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

def evaluate_interview(transcript: list):
    formatted_transcript = ""
    for idx, qa in enumerate(transcript):
        formatted_transcript += f"Q{idx+1}: {qa.get('question')}\nA{idx+1}: {qa.get('answer')}\n\n"

    prompt = f"""
    You are a professional AI Interview Evaluation Agent.
    Evaluate the following interview transcript and grade the candidate.
    
    Interview Transcript:
    {formatted_transcript}

    Instructions:
    1. Score the following dimensions out of 10.0:
       - "technical_score": Assessment of technical accuracy and knowledge.
       - "communication_score": Evaluation of clarity, brevity, and structure.
       - "confidence_score": Candidate's presence, tone, and certainty.
       - "problem_solving_score": Ability to break down problems and explain reasoning.
    2. Compute the "overall_score" (0.0 to 100.0).
    3. State a "recommendation": "Strong Hire", "Hire", "Consider", or "Reject".
    4. Compile detailed "ai_feedback" summarizing strengths, flaws, and overall quality.

    You MUST return the output as a valid JSON object only with the keys below.
    Expected Format:
    {{
      "technical_score": 8.5,
      "communication_score": 7.0,
      "confidence_score": 8.0,
      "problem_solving_score": 7.5, 
      "overall_score": 78.0,
      "recommendation": "Hire",
      "ai_feedback": "Detailed feedback text..."
    }}
    """

    if client is None:
        return {
            "technical_score": 7.5,
            "communication_score": 7.0,
            "confidence_score": 7.0,
            "problem_solving_score": 7.0,
            "overall_score": 73.5,
            "recommendation": "Consider",
            "ai_feedback": "Fallback evaluation used (no LLM available)."
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
        print(f"Error in InterviewEvaluationAgent: {e}")
        return {
            "technical_score": 6.0,
            "communication_score": 6.0,
            "confidence_score": 6.0,
            "problem_solving_score": 6.0,
            "overall_score": 60.0,
            "recommendation": "Consider",
            "ai_feedback": "Interview evaluation completed with fallback scores due to system error."
        }
