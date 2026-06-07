import os
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from backend.repositories.interview_repository import InterviewRepository
from python_ai.agents.interview_agent import evaluate_interview

class InterviewService:
    def __init__(self):
        self.repo = InterviewRepository()

    async def transcribe_file(self, file_path: str) -> str:
        # Try to call whisper CLI if available, otherwise fallback
        try:
            # whisper CLI should output txt file; use subprocess if installed
            import subprocess, json
            out = subprocess.check_output(["whisper", file_path, "--model", "small", "--output_format", "txt"], stderr=subprocess.STDOUT)
            # find generated txt file
            txt_path = file_path + ".txt"
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        # fallback: no transcription available
        return ""

    async def evaluate_transcript(self, db: AsyncSession, candidate_id: int, job_id: int, application_id: int, transcript: list):
        # call python_ai agent evaluate_interview
        result = evaluate_interview(transcript)
        payload = {
            'candidate_id': candidate_id,
            'job_id': job_id,
            'application_id': application_id,
            'questions': None,
            'transcript': '\n'.join([qa.get('answer','') for qa in transcript]),
            'communication_score': result.get('communication_score'),
            'technical_score': result.get('technical_score'),
            'problem_solving_score': result.get('problem_solving_score'),
            'confidence_score': result.get('confidence_score'),
            'overall_score': result.get('overall_score'),
            'recommendation': result.get('recommendation'),
            'ai_feedback': result.get('ai_feedback'),
            'answers': transcript,
        }
        return await self.repo.create_result(db, payload)