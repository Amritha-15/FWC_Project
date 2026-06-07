-- ============================================================
-- migrations/additional_tables.sql
-- Run this ONCE on your existing HRMS database.
-- Only adds columns/tables that don't already exist.
-- ============================================================

-- 1. Add google_id to users (for Google OAuth)
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS google_id TEXT UNIQUE,
  ADD COLUMN IF NOT EXISTS profile_picture TEXT;

-- 2. Extend candidates table with parsed resume fields
ALTER TABLE candidates
  ADD COLUMN IF NOT EXISTS skills TEXT,
  ADD COLUMN IF NOT EXISTS certifications TEXT,
  ADD COLUMN IF NOT EXISTS projects TEXT,
  ADD COLUMN IF NOT EXISTS resume_parsed_at TIMESTAMP;

-- 3. Extend interview_results with per-question data
ALTER TABLE interview_results
  ADD COLUMN IF NOT EXISTS answers JSONB,
  ADD COLUMN IF NOT EXISTS ai_feedback TEXT,
  ADD COLUMN IF NOT EXISTS application_id INT REFERENCES applications(id);

-- 4. Add application_id FK to interview_questions
ALTER TABLE interview_questions
  ADD COLUMN IF NOT EXISTS application_id INT REFERENCES applications(id);

-- 5. Interview sessions table (tracks live session state)
CREATE TABLE IF NOT EXISTS interview_sessions (
  id              SERIAL PRIMARY KEY,
  candidate_id    INT REFERENCES candidates(id) ON DELETE CASCADE,
  application_id  INT REFERENCES applications(id) ON DELETE CASCADE,
  job_id          INT REFERENCES jobs(id) ON DELETE CASCADE,
  status          VARCHAR(30) DEFAULT 'in_progress'
                    CHECK (status IN ('in_progress','completed','abandoned')),
  current_question_index INT DEFAULT 0,
  started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at    TIMESTAMP
);

-- 6. Interview answers table (one row per question/answer)
CREATE TABLE IF NOT EXISTS interview_answers (
  id              SERIAL PRIMARY KEY,
  session_id      INT REFERENCES interview_sessions(id) ON DELETE CASCADE,
  question_id     INT REFERENCES interview_questions(id) ON DELETE CASCADE,
  question_text   TEXT NOT NULL,
  answer_text     TEXT,
  question_score  NUMERIC(5,2),
  recorded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_applications_candidate ON applications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_applications_job       ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user     ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_app ON interview_sessions(application_id);
