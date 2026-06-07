import os
import json
try:
  from groq import Groq
except Exception:
  Groq = None
from dotenv import load_dotenv

# Load .env from project root
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../.env'))
load_dotenv(dotenv_path)

client = None
if Groq is not None:
  try:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
  except Exception:
    client = None


def rank_candidates(job_requirements: dict, candidates: list):
    prompt = f"""
    You are a professional AI Candidate Ranking Agent.
    Your task is to rank the candidate profiles against the job requirements.
    
    Job Requirements:
    {json.dumps(job_requirements, indent=2)}

    Candidate Profiles:
    {json.dumps(candidates, indent=2)}

    Instructions:
    1. Calculate a "match_score" (0.0 to 100.0) based on skills fit, experience levels, and educational background.
    2. Determine their "rank_position" (1 for the best candidate, 2 for the second best, etc.).
    3. Generate a "hiring_confidence_score" (0.0 to 100.0) based on candidate resume quality and requirements match.
    4. Provide a brief "ranking_reasoning" explaining their strengths/shortcomings relative to the role.

    You MUST return the output as a valid JSON object only containing a "rankings" key with a list of candidates sorted by their rank_position.
    Expected Format:
    {{
      "rankings": [
        {{
          "candidate_id": 1,
          "application_id": 2,
          "match_score": 92.5,
          "rank_position": 1,
          "hiring_confidence_score": 88.0,
          "ranking_reasoning": "Strong match with Node.js and SQL skills, with 5 years experience matching the requirements perfectly."
        }}
      ]
    }}
    """

    if client is None:
      # Fallback ranking logic
      rankings = []
      for index, candidate in enumerate(candidates):
        rankings.append({
          "candidate_id": candidate.get("candidate_id"),
          "application_id": candidate.get("application_id"),
          "match_score": 70.0,
          "rank_position": index + 1,
          "hiring_confidence_score": 65.0,
          "ranking_reasoning": "Fallback evaluation (no LLM)."
        })
      return {"rankings": rankings}

    try:
      completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
      )
      result = json.loads(completion.choices[0].message.content)
      return result
    except Exception as e:
      print(f"Error in CandidateRankingAgent: {e}")
      rankings = []
      for index, candidate in enumerate(candidates):
        rankings.append({
          "candidate_id": candidate.get("candidate_id"),
          "application_id": candidate.get("application_id"),
          "match_score": 70.0,
          "rank_position": index + 1,
          "hiring_confidence_score": 65.0,
          "ranking_reasoning": "Fallback evaluation due to API error."
        })
      return {"rankings": rankings}
