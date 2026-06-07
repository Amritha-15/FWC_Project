-- ============================================================
-- hrms_hr_migration.sql
-- Run this ONCE to migrate your database for the HR Module
-- ============================================================

-- 1. Extend candidates table with Resume Screening Agent fields
ALTER TABLE candidates
  ADD COLUMN IF NOT EXISTS resume_summary TEXT,
  ADD COLUMN IF NOT EXISTS resume_quality_score NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS skill_strength_score NUMERIC(5,2);

-- 2. Extend applications table with Candidate Ranking and Analysis fields
ALTER TABLE applications
  ADD COLUMN IF NOT EXISTS match_score NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS ranking_position INT,
  ADD COLUMN IF NOT EXISTS hiring_confidence_score NUMERIC(5,2),
  ADD COLUMN IF NOT EXISTS skill_gap JSONB,
  ADD COLUMN IF NOT EXISTS hiring_recommendation JSONB;

-- 3. Create interview_schedules table
CREATE TABLE IF NOT EXISTS interview_schedules (
  id              SERIAL PRIMARY KEY,
  candidate_id    INT REFERENCES candidates(id) ON DELETE CASCADE,
  job_id          INT REFERENCES jobs(id) ON DELETE CASCADE,
  application_id  INT REFERENCES applications(id) ON DELETE CASCADE,
  interview_date  DATE NOT NULL,
  interview_time  TIME NOT NULL,
  meeting_link    TEXT,
  notes           TEXT,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Extend jobs table with new HR fields
ALTER TABLE jobs
  ADD COLUMN IF NOT EXISTS department VARCHAR(100),
  ADD COLUMN IF NOT EXISTS location VARCHAR(100),
  ADD COLUMN IF NOT EXISTS salary_range VARCHAR(100);

-- 5. Extend users table with Admin fields
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
