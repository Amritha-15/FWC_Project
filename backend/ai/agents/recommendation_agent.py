import os
import json
try:
    import google.generativeai as genai
except Exception:
    genai = None

from dotenv import load_dotenv

# Load .env from project root
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.env'))
load_dotenv(dotenv_path)

client = None
if genai is not None:
    try:
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        client = genai.GenerativeModel("gemini-1.5-flash")
    except Exception:
        client = None


def compile_recommendation(resume_score: float, candidate_ranking_score: float, interview_score: float, skill_gap_analysis: dict):
    prompt = f"""
    You are a professional AI Hiring Recommendation Agent.
    Synthesize all candidate evaluation scores to formulate a final hiring suggestion.
    
    Scores Context:
    - Resume Quality Score: {resume_score}/100.0
    - Candidate Job Matching Score: {candidate_ranking_score}/100.0
    - Voice Interview Performance Score: {interview_score}/100.0
    - Skill Gap Findings: {json.dumps(skill_gap_analysis, indent=2)}

    Instructions:
    1. Determine the "recommendation" category: "Strong Hire", "Hire", "Consider", or "Reject".
    2. Extract a list of core "strengths".
    3. Extract a list of core "weaknesses" or improvement opportunities.
    4. Write a detailed "reasoning" paragraph explaining the decision logic based on the scores and gaps.
    5. Write a concise 2-sentence "summary" suitable for the HR dashboard.

    You MUST return the output as a valid JSON object only with the keys below.
    Do not include markdown, code fences, or any extra text. Return only raw JSON.
    Expected Format:
    {{
      "recommendation": "Hire",
      "strengths": ["Excellent Node.js and SQL skills", "Strong communication clarity during voice interview"],
      "weaknesses": ["Lacks experience in Redis cache invalidation techniques"],
      "reasoning": "Detailed reasoning paragraph...",
      "summary": "Dashboard summary sentence."
    }}
    """

    if client is None:
        return {
            "recommendation": "Consider",
            "strengths": [],
            "weaknesses": [],
            "reasoning": "Fallback suggestion generated due to evaluation service unavailability.",
            "summary": "Hiring suggestion compiled under fallback parameters."
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
        return result
    except Exception as e:
        print(f"Error in HiringRecommendationAgent: {e}")
        return {
            "recommendation": "Consider",
            "strengths": [],
            "weaknesses": [],
            "reasoning": "Fallback suggestion generated due to evaluation service unavailability.",
            "summary": "Hiring suggestion compiled under fallback parameters."
        }