# HRMS Candidate Module – API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
All protected routes require:
```
Authorization: Bearer <jwt_token>
```

---

## 1. AUTH ENDPOINTS

### POST /api/auth/register
Create a new candidate account.

**Request:**
```json
{
  "name": "Arjun Kumar",
  "email": "arjun@example.com",
  "password": "secret123"
}
```

**Response 201:**
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "name": "Arjun Kumar",
      "email": "arjun@example.com",
      "role": "candidate",
      "created_at": "2024-01-15T10:00:00Z"
    }
  }
}
```

**Errors:**
- 400: Missing fields / password too short
- 409: Email already registered

---

### POST /api/auth/login

**Request:**
```json
{ "email": "arjun@example.com", "password": "secret123" }
```

**Response 200:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "token": "eyJhbGci...",
    "user": { "id": 1, "name": "Arjun Kumar", "email": "arjun@example.com", "role": "candidate" }
  }
}
```

---

### POST /api/auth/google-login

**Request:**
```json
{ "idToken": "<Google ID token from frontend Sign-In>" }
```

**Response 200:**
```json
{
  "success": true,
  "message": "Google login successful",
  "data": {
    "token": "eyJhbGci...",
    "user": {
      "id": 2, "name": "Priya Sharma",
      "email": "priya@gmail.com", "role": "candidate",
      "profile_picture": "https://lh3.googleusercontent.com/..."
    }
  }
}
```

---

### GET /api/auth/me  🔒

**Response 200:**
```json
{
  "success": true,
  "data": {
    "user": { "id": 1, "name": "Arjun Kumar", "email": "arjun@example.com", "role": "candidate" }
  }
}
```

---

## 2. CANDIDATE PROFILE

### GET /api/candidate/profile  🔒

**Response 200:**
```json
{
  "success": true,
  "data": {
    "profile": {
      "user_id": 1,
      "name": "Arjun Kumar",
      "email": "arjun@example.com",
      "candidate_id": 3,
      "phone": "+91-9876543210",
      "education": "B.Tech Computer Science, Anna University, 2022",
      "experience": "2 years as Software Engineer at Zoho Corporation",
      "skills": "Python, React, Node.js, PostgreSQL, Docker",
      "certifications": "AWS Solutions Architect Associate",
      "projects": "E-commerce platform with microservices; AI chatbot using LLM",
      "resume_url": "/uploads/resume_1_1704067200000.pdf",
      "current_status": "Applied",
      "resume_parsed_at": "2024-01-15T10:05:00Z"
    }
  }
}
```

---

### PUT /api/candidate/profile  🔒

**Request:**
```json
{ "phone": "+91-9876543210" }
```

**Response 200:**
```json
{ "success": true, "message": "Profile updated", "data": { "profile": { ... } } }
```

---

### POST /api/candidate/upload-resume  🔒
**Content-Type:** `multipart/form-data`
**Field:** `resume` (PDF or DOCX, max 10 MB)

```bash
curl -X POST http://localhost:5000/api/candidate/upload-resume \
  -H "Authorization: Bearer <token>" \
  -F "resume=@/path/to/resume.pdf"
```

**Response 201:**
```json
{
  "success": true,
  "message": "Resume uploaded. AI parsing in progress – profile will update shortly.",
  "data": {
    "resume_url": "/uploads/resume_1_1704067200000.pdf",
    "message": "..."
  }
}
```

> AI parsing runs in background. Check GET /profile after ~10 seconds to see parsed fields.

---

### POST /api/candidate/parse-resume  🔒
Manually re-trigger AI parsing of uploaded resume.

**Response 200:**
```json
{
  "success": true,
  "message": "Resume parsed successfully",
  "data": {
    "parsed": {
      "education": "B.Tech CS, Anna University, 2022",
      "experience": "2 years – Software Engineer at Zoho",
      "skills": "Python, React, Node.js, Docker, PostgreSQL",
      "certifications": "AWS SAA",
      "projects": "E-commerce microservices; LLM chatbot"
    }
  }
}
```

---

## 3. JOBS

### GET /api/jobs  (public)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "count": 2,
    "jobs": [
      {
        "id": 10,
        "title": "Full Stack Developer",
        "description": "Build web applications using React and Node.js...",
        "required_skills": "React, Node.js, PostgreSQL",
        "experience_required": "2-4 years",
        "status": "Open",
        "posted_by": "HR Team",
        "created_at": "2024-01-10T09:00:00Z"
      }
    ]
  }
}
```

---

### GET /api/jobs/:id  (public)

**Response 200:**
```json
{ "success": true, "data": { "job": { "id": 10, "title": "Full Stack Developer", ... } } }
```

---

## 4. APPLICATIONS

### POST /api/applications  🔒

**Request:**
```json
{ "job_id": 10 }
```

**Response 201:**
```json
{
  "success": true,
  "message": "Application submitted successfully",
  "data": {
    "application": {
      "id": 55,
      "candidate_id": 3,
      "job_id": 10,
      "application_status": "Applied",
      "applied_at": "2024-01-15T10:30:00Z"
    }
  }
}
```

**Errors:**
- 409: Already applied

---

### GET /api/applications  🔒

**Response 200:**
```json
{
  "success": true,
  "data": {
    "count": 1,
    "applications": [
      {
        "id": 55,
        "application_status": "Interview Approved",
        "applied_at": "2024-01-15T10:30:00Z",
        "job_id": 10,
        "title": "Full Stack Developer",
        "resume_score": null,
        "interview_score": null
      }
    ]
  }
}
```

**Application Status Values:**
`Applied` → `Screening` → `Shortlisted` → `Interview Approved` → `Interview Completed` → `Selected` / `Rejected` → `Hired`

---

### GET /api/applications/:id  🔒

**Response 200:**
```json
{ "success": true, "data": { "application": { "id": 55, "application_status": "Shortlisted", ... } } }
```

---

## 5. NOTIFICATIONS

### GET /api/notifications  🔒

**Response 200:**
```json
{
  "success": true,
  "data": {
    "unread_count": 2,
    "notifications": [
      {
        "id": 1,
        "title": "📹 Interview Approved",
        "message": "Your AI video interview for \"Full Stack Developer\" is now ready.",
        "is_read": false,
        "created_at": "2024-01-16T09:00:00Z"
      },
      {
        "id": 2,
        "title": "✅ Application Submitted",
        "message": "Your application for \"Full Stack Developer\" has been received.",
        "is_read": true,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

### PUT /api/notifications/:id/read  🔒

**Response 200:**
```json
{ "success": true, "message": "Notification marked as read" }
```

---

### PUT /api/notifications/read-all  🔒

**Response 200:**
```json
{ "success": true, "message": "All notifications marked as read" }
```

---

## 6. AI VIDEO INTERVIEW

> ⚠️ Interview can only be started when `application_status = "Interview Approved"`

### GET /api/interview/status/:applicationId  🔒

**Response 200:**
```json
{
  "success": true,
  "data": {
    "application_id": 55,
    "interview_status": "Interview Pending",
    "can_start": true
  }
}
```

---

### POST /api/interview/start  🔒
Validates eligibility, generates 3 AI questions, creates session.

**Request:**
```json
{ "application_id": 55 }
```

**Response 200:**
```json
{
  "success": true,
  "message": "Interview started. Camera and microphone access required.",
  "data": {
    "session_id": 7,
    "total_questions": 3,
    "current_index": 0,
    "current_question": {
      "id": 101,
      "text": "You mentioned using PostgreSQL in your projects. Can you walk me through how you optimised a slow query in a production system?",
      "number": 1
    }
  }
}
```

**Errors:**
- 400: Resume not uploaded
- 403: Status is not "Interview Approved"

---

### GET /api/interview/question?session_id=7  🔒
Get current question (useful for TTS playback).

**Response 200:**
```json
{
  "success": true,
  "data": {
    "question": {
      "id": 101,
      "text": "You mentioned using PostgreSQL...",
      "number": 1,
      "total": 3
    }
  }
}
```

---

### POST /api/interview/answer  🔒
Submit speech-to-text transcript for current question.

**Request:**
```json
{
  "session_id": 7,
  "answer_text": "In my last project I had a slow JOIN query on the orders table. I added a composite index on customer_id and created_at which reduced the query time from 2 seconds to 80ms."
}
```

**Response (next question):**
```json
{
  "success": true,
  "message": "Answer saved",
  "data": {
    "completed": false,
    "next_question": {
      "id": 102,
      "text": "Tell me about a time you led a feature end-to-end from design to deployment.",
      "number": 2,
      "total": 3
    }
  }
}
```

**Repeat trigger – request:**
```json
{ "session_id": 7, "answer_text": "Can you repeat that?" }
```

**Repeat trigger – response:**
```json
{
  "success": true,
  "message": "Repeating question",
  "data": {
    "repeated": true,
    "question": { "id": 101, "text": "You mentioned using PostgreSQL...", "number": 1, "total": 3 }
  }
}
```

---

### POST /api/interview/complete  🔒
Triggers AI evaluation after all 3 answers.

**Request:**
```json
{ "session_id": 7 }
```

**Response 200:**
```json
{
  "success": true,
  "message": "Interview completed successfully",
  "data": {
    "message": "Interview completed and evaluated.",
    "overall_score": 7.8,
    "status": "Interview Completed"
  }
}
```

---

### GET /api/interview/result/:applicationId  🔒 (HR/Admin only)

**Response 200:**
```json
{
  "success": true,
  "data": {
    "result": {
      "id": 5,
      "candidate_name": "Arjun Kumar",
      "candidate_email": "arjun@example.com",
      "resume_url": "/uploads/resume_1_1704067200000.pdf",
      "job_title": "Full Stack Developer",
      "technical_score": 8.0,
      "communication_score": 7.5,
      "problem_solving_score": 7.0,
      "confidence_score": 8.0,
      "overall_score": 7.6,
      "recommendation": "Shortlist",
      "ai_feedback": "Arjun demonstrated strong technical depth, particularly in database optimisation. Communication was clear and structured. Would benefit from more concrete examples on team collaboration.",
      "transcript": "Q1: You mentioned using PostgreSQL...\nA: In my last project...",
      "created_at": "2024-01-16T11:30:00Z"
    }
  }
}
```

---

## Error Response Format
All errors follow this structure:
```json
{
  "success": false,
  "message": "Descriptive error message"
}
```

## HTTP Status Codes Used
| Code | Meaning |
|------|---------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request / Validation error |
| 401  | Unauthenticated |
| 403  | Forbidden (wrong role or status) |
| 404  | Not Found |
| 409  | Conflict (duplicate) |
| 500  | Internal Server Error |
