from .agents.resume_agent import screen_resume as _screen_resume
from .agents.skill_gap_agent import analyze_skill_gap as _analyze_skill_gap
from .agents.ranking_agent import rank_candidates as _rank_candidates
from .agents.recommendation_agent import compile_recommendation as _compile_recommendation
from .agents.interview_agent import evaluate_interview as _evaluate_interview

# Lightweight orchestrator functions. Import these from backend.ai in services.

def screen_resume(resume_text: str):
    return _screen_resume(resume_text)


def analyze_skill_gap(candidate_skills: str, required_skills: str, transcript: list):
    return _analyze_skill_gap(candidate_skills, required_skills, transcript)


def rank_candidates(job_requirements: dict, candidates: list):
    return _rank_candidates(job_requirements, candidates)


def compile_recommendation(resume_score: float, candidate_ranking_score: float, interview_score: float, skill_gap_analysis: dict):
    return _compile_recommendation(resume_score, candidate_ranking_score, interview_score, skill_gap_analysis)


def evaluate_interview(transcript: list):
    return _evaluate_interview(transcript)
