import os
import json

try:
    import google.generativeai as genai
except Exception:
    genai = None

from dotenv import load_dotenv

# Load .env from project root
dotenv_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../.env")
)
load_dotenv(dotenv_path)

client = None
if genai is not None:
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        client = genai.GenerativeModel("gemini-1.5-flash")
    except Exception:
        client = None


def screen_resume(resume_text: str, job_description: str = ""):
    """
    AI Resume Screening Agent

    Returns:
    {
        skills,
        experience,
        education,
        projects,
        certifications,
        summary,
        quality_score,
        skill_strength_score,
        match_score
    }
    """

    prompt = f"""
You are an expert AI Resume Screening Agent for an HRMS system.

Your job is ONLY to analyze the resume.

DO NOT recommend hiring.
DO NOT recommend rejection.
DO NOT rank candidates.

Resume:
{resume_text}

Job Description:
{job_description}

Analyze and extract:

1. Technical and soft skills
2. Experience
3. Education
4. Projects
5. Certifications
6. Professional summary

Also calculate:

- quality_score (0-100)
  Based on resume structure, experience, achievements and overall quality.

- skill_strength_score (0-100)
  Based on technical depth and demonstrated expertise.

- match_score (0-100)
  Based ONLY on similarity between resume and job description.
  If no job description is provided, estimate match using industry relevance.

Return ONLY valid JSON in the following format.
Do not include markdown, code fences, or any extra text. Return only raw JSON.

{{
    "skills": [],
    "experience": [],
    "education": [],
    "projects": [],
    "certifications": [],
    "summary": "",
    "quality_score": 0,
    "skill_strength_score": 0,
    "match_score": 0
}}
"""

    # Offline fallback
    if client is None:
        return {
            "skills": [],
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "summary": "Resume analyzed using fallback mode.",
            "quality_score": 60.0,
            "skill_strength_score": 60.0,
            "match_score": 60.0,
        }

    try:
        response = client.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown code fences if Gemini wraps the JSON
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        result = json.loads(text)

        return {
            "skills": result.get("skills", []),
            "experience": result.get("experience", []),
            "education": result.get("education", []),
            "projects": result.get("projects", []),
            "certifications": result.get("certifications", []),
            "summary": result.get("summary", ""),
            "quality_score": float(result.get("quality_score", 50.0)),
            "skill_strength_score": float(result.get("skill_strength_score", 50.0)),
            "match_score": float(result.get("match_score", 50.0)),
        }

    except Exception as e:
        print(f"ResumeScreeningAgent Error: {e}")

        return {
            "skills": [],
            "experience": [],
            "education": [],
            "projects": [],
            "certifications": [],
            "summary": "Resume analysis failed.",
            "quality_score": 50.0,
            "skill_strength_score": 50.0,
            "match_score": 50.0,
        }