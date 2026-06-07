import json
import os
import asyncio
import traceback
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.candidate_repository import CandidateRepository
from backend.repositories.application_repository import ApplicationRepository
from backend.repositories.job_repository import JobRepository
from backend.repositories.interview_repository import InterviewRepository
from backend.repositories.notification_repository import NotificationRepository
from backend.database.session import async_session_maker

# ── Load .env ──────────────────────────────────────────────────────────────
dotenv_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../.env")
)
load_dotenv(dotenv_path)

# ── Groq client ────────────────────────────────────────────────────────────
_GROQ_API_KEY: Optional[str] = None
try:
    from groq import Groq
    _GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    if not _GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment")
    _groq_available = True
    print("✅ Groq client initialised")
except Exception as _e:
    _groq_available = False
    print(f"⚠️  Groq unavailable: {_e}")

# ── Repositories ───────────────────────────────────────────────────────────
cand_repo     = CandidateRepository()
app_repo      = ApplicationRepository()
job_repo      = JobRepository()
interview_repo = InterviewRepository()
notif_repo    = NotificationRepository()


# ══════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════

def _normalize_score(value: Any) -> Optional[float]:
    """Normalize AI scores to a 0-100 scale."""
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if 0 < score <= 1:
        return round(score * 100, 2)
    return round(score, 2)


import json
import re

def _parse_groq_json(text: str) -> dict:
    """Extract and parse JSON from Groq response."""
    text = text.strip()

    # Remove markdown code fences
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract JSON object if extra text surrounds it
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())

    raise ValueError(f"Could not parse JSON from response:\n{text[:500]}")


def _call_groq(prompt: str) -> dict:
    """Call Groq API with fallback models."""
    if not _groq_available or not _GROQ_API_KEY:
        raise RuntimeError("Groq client not initialised")
    
    from groq import Groq
    client = Groq(api_key=_GROQ_API_KEY)
    
    # Try models in order, fallback if deprecated
    models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant"
    ]
    
    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            return _parse_groq_json(response.choices[0].message.content)
        except Exception as e:
            print(f"Model {model} failed: {e}")
            continue
    
    raise RuntimeError("All Groq models failed")


# ══════════════════════════════════════════════════════════════════════════
#  1. RESUME SCREENING
# ══════════════════════════════════════════════════════════════════════════

def _screen_resume_sync(resume_text: str, job_description: str = "") -> dict:
    resume_text = resume_text[:20000]
    print(f"Resume length sent to Groq: {len(resume_text)}")
    if not resume_text or not resume_text.strip():
        print("⚠️  Resume text is EMPTY — no data to analyze")
        return {
            "skills": [], "experience": [], "education": [],
            "projects": [], "certifications": [],
            "summary": "No resume data provided.",
            "quality_score": 0.0, "skill_strength_score": 0.0, "match_score": 0.0,
        }

    prompt = f"""
You are an expert AI Resume Screening Agent for an HRMS system.
Your job is ONLY to analyse the resume. Do NOT recommend hiring or rejection.

Resume:
{resume_text}

Job Description:
{job_description}

Analyse and extract:
1. Technical and soft skills
2. Experience
3. Education
4. Projects
5. Certifications
6. Professional summary

Also calculate:
- quality_score (0-100): resume structure, experience, achievements.
- skill_strength_score (0-100): technical depth and expertise.
- match_score (0-100): similarity between resume and job description.
  If no job description, estimate using industry relevance.
- hiring_confidence_score (0-100): overall confidence this candidate is a good hire,
  combining quality, skills depth, match, and experience level.

Return ONLY raw JSON — no markdown, no code fences, no extra text.

{{
    "skills": [],
    "experience": [],
    "education": [],
    "projects": [],
    "certifications": [],
    "summary": "",
    "quality_score": 0,
    "skill_strength_score": 0,
    "match_score": 0,
    "hiring_confidence_score": 0
}}
"""
    fallback = {
        "skills": [], "experience": [], "education": [],
        "projects": [], "certifications": [],
        "summary": "Resume analyzed using fallback mode.",
        "quality_score": 60.0, "skill_strength_score": 60.0, "match_score": 60.0,
    }

    if not _groq_available:
        return fallback

    try:
        result = _call_groq(prompt)
        # hiring_confidence_score: use Groq's own field; fall back to skill_strength_score
        groq_confidence = result.get("hiring_confidence_score")
        if groq_confidence is None:
            groq_confidence = result.get("skill_strength_score", 50.0)

        return {
            "skills":                  result.get("skills", []),
            "experience":              result.get("experience", []),
            "education":               result.get("education", []),
            "projects":                result.get("projects", []),
            "certifications":          result.get("certifications", []),
            "summary":                 result.get("summary", ""),
            "quality_score":           float(result.get("quality_score", 50.0)),
            "skill_strength_score":    float(result.get("skill_strength_score", 50.0)),
            "match_score":             float(result.get("match_score", 50.0)),
            "hiring_confidence_score": float(groq_confidence),
        }
    except Exception as e:
        print(f"❌ ResumeScreeningAgent error: {e}")
        traceback.print_exc()
        return {**fallback, "summary": "Resume analysis failed."}


# ══════════════════════════════════════════════════════════════════════════
#  2. RANKING
# ══════════════════════════════════════════════════════════════════════════

def _rank_candidates_sync(
    job_requirements: Dict[str, Any],
    candidates: List[Dict[str, Any]]
) -> dict:
    """Rank candidates by resume_score. Preserve real match/confidence scores from Groq."""
    sorted_candidates = sorted(
        candidates,
        key=lambda c: float(c.get("resume_score") or 0),
        reverse=True
    )
    rankings = []
    for idx, cand in enumerate(sorted_candidates, start=1):
        resume_score = float(cand.get("resume_score") or 0)
        # Use Groq's real match_score if available; never copy resume_score as a fake substitute
        match_score = float(cand.get("match_score") or 0)
        confidence  = float(cand.get("hiring_confidence_score") or 0)
        rankings.append({
            "candidate_id":            cand["candidate_id"],
            "application_id":          cand["application_id"],
            "rank_position":           idx,
            "match_score":             round(match_score, 2),
            "hiring_confidence_score": round(confidence, 2),
        })
    return {"rankings": rankings}


# ══════════════════════════════════════════════════════════════════════════
#  3. HIRING RECOMMENDATION
# ══════════════════════════════════════════════════════════════════════════

def _compile_recommendation_sync(
    resume_score: float,
    candidate_ranking_score: float,
    interview_score: float,
    skill_gap_analysis: dict,
) -> dict:
    prompt = f"""
You are a professional AI Hiring Recommendation Agent.
Synthesise all candidate evaluation scores to formulate a final hiring suggestion.

Scores:
- Resume Quality Score: {resume_score}/100
- Candidate Job Matching Score: {candidate_ranking_score}/100
- Voice Interview Performance Score: {interview_score}/100
- Skill Gap Findings: {json.dumps(skill_gap_analysis, indent=2)}

Instructions:
1. Determine "recommendation": "Strong Hire", "Hire", "Consider", or "Reject".
2. List core "strengths".
3. List core "weaknesses".
4. Write a "reasoning" paragraph.
5. Write a 2-sentence "summary" for the HR dashboard.

Return ONLY raw JSON — no markdown, no code fences, no extra text.

{{
  "recommendation": "Hire",
  "strengths": [],
  "weaknesses": [],
  "reasoning": "",
  "summary": ""
}}
"""
    fallback = {
        "recommendation": "Consider",
        "strengths": [], "weaknesses": [],
        "reasoning": "Fallback: evaluation service unavailable.",
        "summary": "Hiring suggestion compiled under fallback parameters.",
    }

    if not _groq_available:
        return fallback

    try:
        return _call_groq(prompt)
    except Exception as e:
        print(f"❌ HiringRecommendationAgent error: {e}")
        traceback.print_exc()
        return fallback


# ══════════════════════════════════════════════════════════════════════════
#  4. INTERVIEW EVALUATION
# ══════════════════════════════════════════════════════════════════════════

def _evaluate_interview_sync(transcript: List[Dict[str, str]]) -> dict:
    transcript_text = "\n".join(
        f"{t.get('role', 'user').upper()}: {t.get('content', '')}"
        for t in transcript
    )
    prompt = f"""
You are an expert AI Interview Evaluation Agent.

Evaluate this interview transcript and return scores.

Transcript:
{transcript_text}

Return ONLY raw JSON — no markdown, no code fences, no extra text.

{{
  "communication_score": 0,
  "technical_score": 0,
  "problem_solving_score": 0,
  "confidence_score": 0,
  "overall_score": 0,
  "recommendation": "",
  "ai_feedback": ""
}}
"""
    fallback = {
        "communication_score": 50.0, "technical_score": 50.0,
        "problem_solving_score": 50.0, "confidence_score": 50.0,
        "overall_score": 50.0,
        "recommendation": "Consider",
        "ai_feedback": "Evaluation unavailable.",
    }

    if not _groq_available:
        return fallback

    try:
        result = _call_groq(prompt)
        return {
            "communication_score":   float(result.get("communication_score", 50)),
            "technical_score":       float(result.get("technical_score", 50)),
            "problem_solving_score": float(result.get("problem_solving_score", 50)),
            "confidence_score":      float(result.get("confidence_score", 50)),
            "overall_score":         float(result.get("overall_score", 50)),
            "recommendation":        result.get("recommendation", ""),
            "ai_feedback":           result.get("ai_feedback", ""),
        }
    except Exception as e:
        print(f"❌ InterviewEvaluationAgent error: {e}")
        return fallback


# ══════════════════════════════════════════════════════════════════════════
#  PUBLIC ASYNC API
# ══════════════════════════════════════════════════════════════════════════

async def process_resume(
    db: AsyncSession,
    candidate_id: int,
    application_id: Optional[int] = None,
    resume_text: Optional[str] = "",
    job_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Screen a resume with Groq and persist scores to DB."""

    job_description = ""
    if job_id:
        job = await job_repo.get(db, job_id)
        if job:
            parts = []
            if getattr(job, "description", None):
                parts.append(str(job.description))
            if getattr(job, "required_skills", None):
                parts.append("Required skills: " + str(job.required_skills))
            job_description = "\n".join(parts)

    result = await asyncio.to_thread(_screen_resume_sync, resume_text, job_description)

    candidate = await cand_repo.get(db, candidate_id)
    if candidate:
        extracted_skills = result.get("skills", [])
        # Always build skills string — even empty list produces "" which is a valid update
        skills_str = ", ".join(s for s in extracted_skills if s.strip()) if extracted_skills else None

        update_payload: Dict[str, Any] = {}
        if result.get("summary"):
            update_payload["resume_summary"] = result["summary"]
        if result.get("quality_score") is not None:
            update_payload["resume_quality_score"] = result["quality_score"]
        if result.get("skill_strength_score") is not None:
            update_payload["skill_strength_score"] = result["skill_strength_score"]
        if skills_str:
            update_payload["skills"] = skills_str

        if update_payload:
            await cand_repo.update(db, db_obj=candidate, obj_in=update_payload)
            print(f"  💾 Candidate updated: skills={skills_str!r}, summary_len={len(result.get('summary',''))}")

    if application_id:
        application = await app_repo.get(db, application_id)
        if application:
            app_update: Dict[str, Any] = {
                "resume_score": float(result.get("quality_score", 0.0)),
            }
            # Save Groq's real match_score immediately
            raw_match = result.get("match_score")
            if raw_match is not None:
                app_update["match_score"] = _normalize_score(float(raw_match))
            # hiring_confidence_score: use dedicated field from Groq (Bug 3 fix)
            raw_confidence = result.get("hiring_confidence_score")
            if raw_confidence is None:
                raw_confidence = result.get("skill_strength_score")  # graceful fallback
            if raw_confidence is not None:
                app_update["hiring_confidence_score"] = _normalize_score(float(raw_confidence))
            print(f"  💾 Application scores — resume={app_update.get('resume_score')}, "
                  f"match={app_update.get('match_score')}, confidence={app_update.get('hiring_confidence_score')}")
            await app_repo.update(db, db_obj=application, obj_in=app_update)

    return result


async def evaluate_and_store_interview(
    db: AsyncSession,
    application_id: int,
    transcript: List[Dict[str, str]],
) -> Dict[str, Any]:
    # Run LLM evaluation first (doesn't need DB)
    result = await asyncio.to_thread(_evaluate_interview_sync, transcript)

    # ── BUG FIX: fetch application and hard-fail if not found ──────────────
    # Without candidate_id + job_id the InterviewResult row gets NULL FKs,
    # which causes the hr.py list_interview_results JOIN to silently drop it.
    application = await app_repo.get(db, application_id)
    if not application:
        print(f"❌ evaluate_and_store_interview: Application {application_id} not found — aborting DB write")
        return {"error": f"Application {application_id} not found", "interview": result, "db_id": None}

    candidate_id: int = application.candidate_id   # guaranteed non-None
    job_id: int       = application.job_id         # guaranteed non-None

    payload = {
        "application_id":        application_id,
        "candidate_id":          candidate_id,
        "job_id":                job_id,
        "questions":             None,
        "transcript":            str(transcript),
        "communication_score":   result.get("communication_score"),
        "technical_score":       result.get("technical_score"),
        "problem_solving_score": result.get("problem_solving_score"),
        "confidence_score":      result.get("confidence_score"),
        "overall_score":         result.get("overall_score"),
        "recommendation":        result.get("recommendation"),
        "ai_feedback":           result.get("ai_feedback"),
    }

    # Truncate recommendation to 50 chars so VARCHAR(50) never overflows
    # (also run: ALTER TABLE interview_results ALTER COLUMN recommendation TYPE TEXT)
    if payload.get("recommendation"):
        payload["recommendation"] = str(payload["recommendation"])[:50]

    interview_obj = None
    db_error = None
    try:
        interview_obj = await interview_repo.create_result(db, payload)
        if application and result.get("overall_score") is not None:
            await app_repo.update(
                db, db_obj=application,
                obj_in={"interview_score": float(result.get("overall_score"))}
            )
        await db.commit()
    except Exception as e:
        db_error = e
        print(f"❌ evaluate_and_store_interview DB error: {e}")
        traceback.print_exc()
        try:
            await db.rollback()
        except Exception:
            pass

    # If the insert failed, try updating the score in a brand-new session
    if db_error is not None and result.get("overall_score") is not None:
        try:
            async with async_session_maker() as fresh_db:
                fresh_app = await app_repo.get(fresh_db, application_id)
                if fresh_app:
                    await app_repo.update(
                        fresh_db, db_obj=fresh_app,
                        obj_in={"interview_score": float(result.get("overall_score"))}
                    )
                    await fresh_db.commit()
                    print("✅ interview_score saved via fallback session")
        except Exception as e2:
            print(f"❌ fallback interview_score update failed: {e2}")

    return {"interview": result, "db_id": getattr(interview_obj, "id", None)}


async def run_skill_gap(
    candidate_skills: str,
    required_skills: str,
    transcript: List[Dict[str, str]],
):
    """Skill gap is simple set difference."""
    cand_set = {s.strip().lower() for s in candidate_skills.split(",") if s.strip()}
    req_set  = {s.strip().lower() for s in required_skills.split(",") if s.strip()}
    missing  = sorted(req_set - cand_set)
    matched  = sorted(cand_set & req_set)
    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "gap_score": round(len(matched) / max(len(req_set), 1) * 100, 2),
    }


async def run_ranking(
    job_requirements: Dict[str, Any],
    candidates: List[Dict[str, Any]],
):
    return await asyncio.to_thread(_rank_candidates_sync, job_requirements, candidates)


async def run_recommendation(
    resume_score: float,
    candidate_ranking_score: float,
    interview_score: float,
    skill_gap_analysis: Dict[str, Any],
):
    return await asyncio.to_thread(
        _compile_recommendation_sync,
        resume_score, candidate_ranking_score, interview_score, skill_gap_analysis
    )


# ══════════════════════════════════════════════════════════════════════════
#  5. GENERATE INTERVIEW QUESTIONS
# ══════════════════════════════════════════════════════════════════════════

def _generate_questions_sync(resume_text: str, job_title: str, job_description: str) -> list:
    prompt = f"""
You are an expert technical interviewer at a top company.

Candidate Resume:
{resume_text}

Job Title: {job_title}
Job Description:
{job_description}

Generate exactly 3 personalised interview questions tailored to this candidate's background
and the requirements of the role. Mix question types: at least one behavioural, one technical,
and one problem-solving question.

Return ONLY a raw JSON array of 3 strings — no markdown, no code fences, no extra text.

["Question 1", "Question 2", "Question 3"]
"""
    fallback = [
        "Tell me about yourself and your relevant experience for this role.",
        "Describe a challenging technical problem you solved and how you approached it.",
        "How do you prioritise tasks when working under tight deadlines?",
    ]

    if not _groq_available:
        return fallback

    try:
        from groq import Groq
        client = Groq(api_key=_GROQ_API_KEY)
        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma-7b-it"]
        for model in models:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                )
                text = response.choices[0].message.content.strip()
                if text.startswith("```"):
                    parts = text.split("```")
                    text = parts[1]
                    if text.startswith("json"):
                        text = text[4:]
                    text = text.strip()
                questions = json.loads(text)
                if isinstance(questions, list) and len(questions) == 3:
                    return questions
                return fallback
            except Exception as e:
                print(f"Model {model} failed for question generation: {e}")
                continue
        return fallback
    except Exception as e:
        print(f"❌ GenerateQuestionsAgent error: {e}")
        traceback.print_exc()
        return fallback


async def generate_interview_questions(
    db: AsyncSession,
    application_id: int,
) -> Dict[str, Any]:
    """Fetch candidate + job for the application and return 3 AI-generated questions."""

    application = await app_repo.get(db, application_id)
    if not application:
        return {"error": f"Application {application_id} not found"}

    candidate = await cand_repo.get(db, application.candidate_id)
    if not candidate:
        return {"error": f"Candidate not found for application {application_id}"}

    job = await job_repo.get(db, application.job_id)

    # Build resume text from available fields
    resume_text = ""
    if getattr(candidate, "resume_summary", None):
        resume_text = candidate.resume_summary
    if not resume_text:
        parts = []
        if getattr(candidate, "experience", None):
            parts.append(str(candidate.experience))
        if getattr(candidate, "skills", None):
            parts.append("Skills: " + str(candidate.skills))
        resume_text = "\n".join(parts)
    if not resume_text:
        resume_text = f"Candidate name: {getattr(candidate, 'full_name', 'Unknown')}"

    job_title = getattr(job, "title", "the role") if job else "the role"
    job_description = ""
    if job:
        parts = []
        if getattr(job, "description", None):
            parts.append(str(job.description))
        if getattr(job, "required_skills", None):
            parts.append("Required skills: " + str(job.required_skills))
        job_description = "\n".join(parts)

    questions = await asyncio.to_thread(
        _generate_questions_sync, resume_text, job_title, job_description
    )
    return {"questions": questions}


# ══════════════════════════════════════════════════════════════════════════
#  6. TRANSCRIBE AUDIO  (Groq Whisper)
# ══════════════════════════════════════════════════════════════════════════

async def transcribe_audio(tmp_path: str) -> Dict[str, Any]:
    """Send an audio file to Groq Whisper and return the transcript."""

    if not _groq_available or not _GROQ_API_KEY:
        return {"transcript": "", "error": "Groq not available"}

    def _do_transcribe():
        from groq import Groq
        client = Groq(api_key=_GROQ_API_KEY)
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
                response_format="text",
            )
        # response_format="text" returns a plain string, not an object
        return result if isinstance(result, str) else getattr(result, "text", "")

    try:
        transcript = await asyncio.to_thread(_do_transcribe)
        return {"transcript": transcript}
    except Exception as e:
        print(f"❌ Whisper transcription error: {e}")
        traceback.print_exc()
        return {"transcript": "", "error": str(e)}


# ══════════════════════════════════════════════════════════════════════════
#  SCREEN JOB
# ══════════════════════════════════════════════════════════════════════════

async def screen_job(
    db: AsyncSession,
    job_id: int,
    concurrency: int = 4,
) -> Dict[str, Any]:

    print(f"🚀 Started screening Job ID: {job_id}")

    job = await job_repo.get(db, job_id)
    if not job:
        print("❌ Job not found")
        return {"error": "job_not_found"}

    applications = await app_repo.list_for_job(db, job_id)
    all_applications = applications
    applications = [a for a in all_applications if getattr(a, "application_status", "Applied") == "Applied"]
    print(f"📄 Applications found: {len(all_applications)} total, {len(applications)} with 'Applied' status")

    if not applications:
        print("ℹ️  No 'Applied' candidates to screen for this job")
        return {"job_id": job_id, "screening_results": {}, "ranking": [], "scheduled": []}

    async def _screen_app(application):
        print(f"  📋 Screening Application {application.id}")
        try:
            from backend.database.session import async_session_maker as maker
            async with maker() as session:
                candidate = await cand_repo.get(session, application.candidate_id)
                if not candidate:
                    print(f"  ❌ Candidate not found for app {application.id}")
                    return {
                        "application_id": application.id,
                        "candidate_id":   application.candidate_id,
                        "result":         {"error": "candidate_not_found"},
                    }

                resume_text = ""

                # Priority 1: try to extract text from the uploaded resume file/URL
                resume_url = getattr(candidate, "resume_url", None)
                if resume_url:
                    try:
                        if os.path.exists(resume_url):

                            if resume_url.lower().endswith(".pdf"):
                                try:
                                    from pypdf import PdfReader

                                    reader = PdfReader(resume_url)

                                    pages = []
                                    for page in reader.pages:
                                        text = page.extract_text()
                                    if text:
                                        pages.append(text)

                                    resume_text = "\n".join(pages)

                                    print(
                                        f"📄 Resume extracted from local PDF "
                                        f"({len(resume_text)} chars)"
                                    )

                                except Exception as pdf_err:
                                    print(f"PDF extraction failed: {pdf_err}")

                            else:
                                with open(
                                    resume_url,
                                    "r",
                                    encoding="utf-8",
                                    errors="ignore"
                                ) as f:
                                    resume_text = f.read()

                                    print(
                                        f"📄 Resume read from text file "
                                        f"({len(resume_text)} chars)"
                                    )
                        elif resume_url.startswith("http://") or resume_url.startswith("https://"):
                            # Cloud/remote URL — fetch via HTTP
                            import urllib.request
                            with urllib.request.urlopen(resume_url, timeout=10) as resp:
                                raw = resp.read()
                            # Try to decode as text; if it's a PDF extract text with pdfminer
                            if resume_url.lower().endswith(".pdf") or raw[:4] == b"%PDF":
                                try:
                                    import io
                                    from pdfminer.high_level import extract_text as pdf_extract
                                    resume_text = pdf_extract(io.BytesIO(raw))
                                    print(f"  📄 Resume extracted from remote PDF ({len(resume_text)} chars)")
                                except Exception as pdf_err:
                                    print(f"  PDF extract failed, using raw decode: {pdf_err}")
                                    resume_text = raw.decode("utf-8", errors="ignore")
                            else:
                                resume_text = raw.decode("utf-8", errors="ignore")
                                print(f"  📄 Resume fetched from URL ({len(resume_text)} chars)")
                    except Exception as e:
                        print(f"  ⚠️  Resume URL read failed: {e}")

                # Priority 2: use already-stored summary (may be stale, but better than nothing)
                if not resume_text and getattr(candidate, "resume_summary", None):
                    resume_text = candidate.resume_summary
                    print(f"  📝 Using stored resume_summary as fallback ({len(resume_text)} chars)")

                # Priority 3: build from structured fields
                if not resume_text:
                    parts = []
                    if getattr(candidate, "experience", None):
                        parts.append("Experience:\n" + str(candidate.experience))
                    if getattr(candidate, "skills", None):
                        parts.append("Skills: " + str(candidate.skills))
                    if getattr(candidate, "education", None):
                        parts.append("Education: " + str(candidate.education))
                    resume_text = "\n\n".join(parts)
                    if resume_text:
                        print(f"  📝 Resume built from structured fields ({len(resume_text)} chars)")

                if not resume_text:
                    print(f"  ⚠️  No resume content found for candidate {candidate.id} — Groq will return zeros")

                result = await process_resume(
                    session, candidate.id, application.id, resume_text, job_id
                )
                print(f"  ✅ Resume processed for App {application.id} — quality={result.get('quality_score')}")
                return {
                    "application_id": application.id,
                    "candidate_id":   application.candidate_id,
                    "result":         result,
                }

        except Exception as e:
            print(f"  ❌ Error screening app {application.id}: {e}")
            traceback.print_exc()
            return {
                "application_id": application.id,
                "candidate_id":   application.candidate_id,
                "result":         {"error": str(e)},
            }

    semaphore = asyncio.Semaphore(concurrency)

    async def _bounded(application):
        async with semaphore:
            return await _screen_app(application)

    results = await asyncio.gather(*[_bounded(app) for app in applications])
    print("✅ Resume screening complete")

    candidates_for_ranking = []
    for result in results:
        app_id = result["application_id"]
        application = await app_repo.get(db, app_id)
        await db.refresh(application)
        candidates_for_ranking.append({
            "candidate_id":            result["candidate_id"],
            "application_id":          app_id,
            "resume_score":            float(application.resume_score or 0),
            # Carry real Groq scores so _rank_candidates_sync doesn't have to fake them
            "match_score":             float(application.match_score or 0),
            "hiring_confidence_score": float(application.hiring_confidence_score or 0),
        })

    job_requirements = {
        "title":           job.title,
        "required_skills": getattr(job, "required_skills", ""),
        "description":     getattr(job, "description", ""),
    }
    ranking  = await run_ranking(job_requirements, candidates_for_ranking)
    rankings = ranking.get("rankings", [])
    print(f"🏆 Rankings generated: {len(rankings)}")

    from backend.models.models import Application

    for entry in rankings:
        app_id = entry.get("application_id")
        if not app_id:
            continue

        application  = await app_repo.get(db, app_id)
        resume_score = float(application.resume_score or 0)
        match_score  = float(application.match_score or 0)   # already saved from Groq

        rec_result = await run_recommendation(resume_score, match_score, 0, {})
        rec_json   = json.dumps(rec_result) if isinstance(rec_result, dict) else rec_result

        await db.execute(
            Application.__table__.update()
            .where(Application.__table__.c.id == app_id)
            .values(
                ranking_position=entry.get("rank_position"),
                # Do NOT overwrite match_score or hiring_confidence_score here —
                # they were set from real Groq output in process_resume()
                hiring_recommendation=rec_json,
            )
        )

    await db.commit()
    print("✅ Ranking saved")

    mapping = {r["application_id"]: r["result"] for r in results}
    return {
        "job_id":            job_id,
        "screening_results": mapping,
        "ranking":           rankings,
        "scheduled":         [],
    }