-- =============================================================
-- FULL DATABASE SCHEMA (Base Tables + Additional Tables)
-- =============================================================

-- USERS
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (
        role IN ('admin','hr','manager','employee','candidate')
    ),
    google_id TEXT UNIQUE,
    profile_picture TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- DEPARTMENTS
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    description TEXT
);

-- EMPLOYEES
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    employee_code VARCHAR(50) UNIQUE,
    department_id INT REFERENCES departments(id),
    manager_id INT REFERENCES employees(id),
    designation VARCHAR(100),
    salary NUMERIC(10,2),
    joining_date DATE,
    status VARCHAR(20) DEFAULT 'active'
);

-- ATTENDANCE
CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id) ON DELETE CASCADE,
    attendance_date DATE NOT NULL,
    check_in TIMESTAMP,
    check_out TIMESTAMP,
    working_hours NUMERIC(5,2),
    status VARCHAR(20)
);

-- LEAVE REQUESTS
CREATE TABLE IF NOT EXISTS leave_requests (
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id) ON DELETE CASCADE,
    leave_type VARCHAR(50),
    start_date DATE,
    end_date DATE,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'Pending',
    approved_by INT REFERENCES employees(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PERFORMANCE REVIEWS
CREATE TABLE IF NOT EXISTS performance_reviews (
    id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employees(id) ON DELETE CASCADE,
    manager_id INT REFERENCES employees(id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    feedback TEXT,
    review_date DATE DEFAULT CURRENT_DATE
);

-- JOBS
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description TEXT,
    required_skills TEXT,
    experience_required VARCHAR(50),
    created_by INT REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'Open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CANDIDATES
CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    phone VARCHAR(20),
    education TEXT,
    experience TEXT,
    resume_url TEXT,
    current_status VARCHAR(50) DEFAULT 'Applied',
    skills TEXT,
    certifications TEXT,
    projects TEXT,
    resume_parsed_at TIMESTAMP
);

-- APPLICATIONS
CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    candidate_id INT REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INT REFERENCES jobs(id) ON DELETE CASCADE,
    resume_score NUMERIC(5,2),
    interview_score NUMERIC(5,2),
    application_status VARCHAR(50) DEFAULT 'Applied',
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INTERVIEW RESULTS
CREATE TABLE IF NOT EXISTS interview_results (
    id SERIAL PRIMARY KEY,
    candidate_id INT REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INT REFERENCES jobs(id) ON DELETE CASCADE,
    application_id INT REFERENCES applications(id),

    questions TEXT,
    transcript TEXT,

    communication_score NUMERIC(5,2),
    technical_score NUMERIC(5,2),
    problem_solving_score NUMERIC(5,2),
    confidence_score NUMERIC(5,2),

    overall_score NUMERIC(5,2),

    recommendation VARCHAR(50),
    ai_feedback TEXT,

    video_url TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    answers JSONB
);

-- NOTIFICATIONS
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200),
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ONBOARDING
CREATE TABLE IF NOT EXISTS onboarding (
    id SERIAL PRIMARY KEY,

    candidate_id INT REFERENCES candidates(id),
    employee_id INT REFERENCES employees(id),

    offer_letter_status VARCHAR(50) DEFAULT 'Pending',
    joining_status VARCHAR(50) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INTERVIEW QUESTIONS
CREATE TABLE IF NOT EXISTS interview_questions (
    id SERIAL PRIMARY KEY,
    candidate_id INT REFERENCES candidates(id) ON DELETE CASCADE,
    job_id INT REFERENCES jobs(id) ON DELETE CASCADE,
    application_id INT REFERENCES applications(id),
    question TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INTERVIEW SESSIONS
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

-- INTERVIEW ANSWERS
CREATE TABLE IF NOT EXISTS interview_answers (
  id              SERIAL PRIMARY KEY,
  session_id      INT REFERENCES interview_sessions(id) ON DELETE CASCADE,
  question_id     INT REFERENCES interview_questions(id) ON DELETE CASCADE,
  question_text   TEXT NOT NULL,
  answer_text     TEXT,
  question_score  NUMERIC(5,2),
  recorded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_applications_candidate ON applications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_applications_job       ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user     ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_sessions_app ON interview_sessions(application_id);
