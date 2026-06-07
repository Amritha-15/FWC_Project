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

def analyze_skill_gap(candidate_skills: str, required_skills: str, transcript: list):
    formatted_transcript = ""
    for idx, qa in enumerate(transcript):
        formatted_transcript += f"Q{idx+1}: {qa.get('question')}\nA{idx+1}: {qa.get('answer')}\n\n"

    prompt = f"""
    You are a professional AI Skill Gap Analysis Agent.
    Your task is to compare the candidate's skills and interview performance against the target role requirements.
    
    Candidate Skills:
    {candidate_skills}

    Required Skills for Job:
    {required_skills}

    Interview Transcript:
    {formatted_transcript}

    Instructions:
    1. Identify "strong_skills": Skills the candidate clearly has or demonstrated command of.
    2. Identify "missing_skills": Required job skills that the candidate either lacks on their resume or struggled to explain in the interview.
    3. Generate "learning_recommendations": Actionable learning courses, certifications, or documentation references to bridge the identified gaps.

    You MUST return the output as a valid JSON object only with the keys below.
    Expected Format:
    {{
      "strong_skills": ["Node.js", "REST APIs"],
      "missing_skills": ["Redis", "SQL Indexing"],
      "learning_recommendations": [
        {{
          "skill": "Redis Caching",
          "recommendation": "Complete the 'Redis University' basic developer course."
        }},
        {{
          "skill": "SQL Query Tuning",
          "recommendation": "Read PostgreSQL documentation on B-Tree Indexes and Execution Plans."
        }}
      ]
    }}
    """

    if client is None:
      # Fallback deterministic response
      return {
        "strong_skills": [],
        "missing_skills": [],
        "learning_recommendations": [
          {
            "skill": "General Technical Focus",
            "recommendation": "Review job specification details to identify improvement areas."
          }
        ]
      }

    try:
      completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"}
      )
      result = json.loads(completion.choices[0].message.content)
      return result
    except Exception as e:
      print(f"Error in SkillGapAnalysisAgent: {e}")
      return {
        "strong_skills": [],
        "missing_skills": [],
        "learning_recommendations": [
          {
            "skill": "General Technical Focus",
            "recommendation": "Review job specification details to identify improvement areas."
          }
        ]
      }
