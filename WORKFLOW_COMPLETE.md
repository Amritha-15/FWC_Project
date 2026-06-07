
# Complete Workflow & API Documentation

## ✅ ADDED FEATURES & FIXES

### 1. Candidate Side Enhancements

#### New Candidate Endpoints:
- `GET /api/candidate/interview-status/:applicationId` — Check if candidate can start interview, view schedule
- `POST /api/candidate/offer/:applicationId/accept` — Accept offer letter 
- `GET /api/candidate/dashboard` — View all applications, pending offers, status summary

#### Enhanced:
- `GET /api/jobs` — Now returns list of Open jobs instead of empty array

---

### 2. HR/Admin Department Management

#### New Department Endpoints:
- `POST /api/hr/departments` — Create new department
- `GET /api/hr/departments` — List all departments
- `GET /api/hr/departments/:id` — Get single department
- `PUT /api/hr/departments/:id` — Update department
- `DELETE /api/hr/departments/:id` — Delete department

---

### 3. Interview Schedule & Retrieval

#### New Endpoints:
- `GET /api/hr/interview/schedule/:applicationId` — HR view candidate's interview schedule
- `GET /api/candidate/interview-status/:applicationId` — Candidate check their interview status & schedule

---

### 4. Offer Letter Management

#### New Endpoints:
- `POST /api/hr/offer/:applicationId/send` — HR sends offer letter to candidate (email + auto status update)
- `GET /api/hr/offer/:applicationId` — HR view offer details
- `POST /api/candidate/offer/:applicationId/accept` — Candidate accepts offer, creates onboarding record

**Flow:**
1. HR marks candidate as "Selected" (triggers email)
2. HR sends formal offer → Creates onboarding record, sends `Offer Letter Generated` email
3. Candidate clicks accept → Application becomes "Hired", onboarding status = "Pending"

---

## Complete Candidate Workflow

### Phase 1: Authentication & Profile
```
1. POST /api/auth/register (name, email, password)
   → Creates candidate user + empty candidate profile
   
2. POST /api/auth/login (email, password)
   → Returns JWT token
   
3. GET /api/candidate/profile
   → View profile with auth token
   
4. PATCH /api/candidate/profile
   → Update personal details, skills, experience, education
```

### Phase 2: Resume Upload & AI Parsing
```
5. POST /api/candidate/upload-resume (file)
   → File stored in /uploads
   → AI parses: education, experience, skills, certifications, projects
   → Automatically saved to candidate profile
```

### Phase 3: Job Search & Application
```
6. GET /api/jobs
   → Browse all Open jobs
   
7. GET /api/jobs/:id
   → View job details
   
8. POST /api/application/apply (jobId)
   → Submit application (status = "Applied")
   → Candidate receives "Application Submitted" email
   
9. GET /api/application/my-applications
   → View all candidate's applications & their status
   
10. GET /api/candidate/dashboard
    → Summary: profile, all apps, status counts, pending offers
```

### Phase 4: AI Screening (HR Triggered)
```
HR Actions:
→ HR reviews application
→ HR triggers: POST /api/hr/agents/resume-screen (candidateId)
  - Python agent analyzes resume vs job
  - Updates: resume_quality_score, skill_strength_score
```

### Phase 5: Shortlist & Interview Approval
```
HR Updates application status:

PUT /api/hr/applications/:id/status (status: "Shortlisted")
→ Candidate receives "Application Shortlisted" email

PUT /api/hr/applications/:id/status (status: "Interview Approved")
→ Candidate receives "Interview Approved" email
→ Candidate can now: GET /api/candidate/interview-status/:appId (can_start_interview = true)
```

### Phase 6: Interview Scheduling
```
HR schedules:
POST /api/hr/interview/schedule
{
  candidateId, jobId, applicationId,
  interviewDate, interviewTime, meetingLink, notes
}
→ Application status → "Interview Scheduled"
→ Candidate receives "Interview Scheduled" email with date/time/link
→ Candidate can view: GET /api/candidate/interview-status/:appId
```

### Phase 7: AI Voice Interview (Candidate Takes)
```
Candidate:
1. Checks GET /api/candidate/interview-status/:appId (can_start_interview = true)
2. POST /api/interview/start (applicationId)
   → Creates interview_sessions record
   → Generates first question dynamically
   
3. Play question via browser TTS
   → Record answer (voice or text)
   
4. POST /api/interview/answer (sessionId, questionId, answerText)
   OR POST /api/interview/answer-voice (sessionId, questionId, audio_file)
   → Saves answer
   → Checks for "repeat" phrases
   → If yes, repeats question
   → If no, generates follow-up question
   
5. Repeat for 3 total questions
   → On 3rd answer completion:
   - Auto-evaluates all 3 Q&A
   - Saves evaluation (scores + recommendation)
   - Status → "Interview Completed"
   - Candidate receives "Interview Completed" email
```

### Phase 8: AI Analysis & Ranking (HR Triggered)
```
After interview:

HR triggers ranking:
POST /api/hr/agents/rank-candidates (jobId)
→ Python agent ranks all candidates for job
→ Updates: match_score, rank_position, hiring_confidence_score

HR triggers skill gap:
POST /api/hr/agents/skill-gap (applicationId)
→ Analyzes required vs candidate skills
→ Provides gap analysis

HR triggers recommendation:
POST /api/hr/agents/recommend (applicationId)
→ Final hiring recommendation based on all scores
```

### Phase 9: Selection & Offer
```
HR marks Selected:
PUT /api/hr/applications/:id/status (status: "Selected")
→ Candidate receives "Congratulations - Selected" email
→ Candidate receives "Offer Letter Generated" email

HR sends formal offer:
POST /api/hr/offer/:applicationId/send
{
  salary, joining_date, department_id
}
→ Creates onboarding record (offer_letter_status = 'Sent')
→ Sends "Official Offer Letter" email

Candidate accepts offer:
POST /api/candidate/offer/:applicationId/accept
→ Application status → "Hired"
→ Onboarding status → "Accepted", joining_status → "Pending"
```

### Phase 10: Onboarding (Post-Hire)
```
Candidate can view onboarding details (once hired)
→ Joining date, department assignment, next steps
```

---

## HR/Admin Workflow

### Dashboard Overview
```
GET /api/hr/dashboard
→ Total jobs posted, applications, shortlisted, hired
→ Interview completion rate, avg scores
→ Recent activity
```

### Multi-Agent Capabilities
```
Available agents:
1. Resume Screen Agent — Resume matching, quality scoring
2. Candidate Ranking Agent — Compare candidates for same job
3. Interview Evaluation Agent — Auto-evaluate Q&A
4. Skill Gap Analysis Agent — Identify skill gaps
5. Hiring Recommendation Agent — Final decision support
```

---

## Email Templates Sent Automatically

| Trigger | Email Template |
|---------|---------------|
| Application submitted | "Application Received" |
| HR shortlists | "Application Shortlisted" |
| HR approves interview | "Interview Approved" |
| HR schedules interview | "Interview Scheduled" |
| Any status update | Status notification |
| Interview completed | "Interview Completed" |
| HR selects candidate | "Congratulations - Selected" |
| HR sends offer | "Official Offer Letter" |
| Candidate rejected | "Application Update" |

---

## Database Tables

### New Features Use:
- `departments` — For department management
- `interview_sessions` — Tracks live interview state
- `interview_answers` — Stores Q&A from each session
- `onboarding` — Tracks offer acceptance, joining status

---

## Testing the Complete Flow

```bash
# 1. Candidate registers
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"John","email":"john@test.com","password":"pass123"}'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@test.com","password":"pass123"}'

# 3. View jobs
curl -X GET http://localhost:5000/api/jobs \
  -H "Authorization: Bearer TOKEN"

# 4. Apply for job
curl -X POST http://localhost:5000/api/application/apply \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jobId": 1}'

# ... (HR operations) ...

# Check interview status
curl -X GET "http://localhost:5000/api/candidate/interview-status/1" \
  -H "Authorization: Bearer TOKEN"

# Start interview
curl -X POST http://localhost:5000/api/interview/start \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"applicationId": 1}'
```

---

## Summary of Gaps Resolved

✅ Fixed candidate job list (was returning empty)
✅ Added department management (full CRUD)
✅ Added candidate dashboard with summary
✅ Added interview status check for candidates
✅ Added offer letter sending & acceptance flow  
✅ Added onboarding tracking
✅ Ensured all automated emails are sent at right triggers
✅ Added comprehensive status tracking throughout workflow

**No webcam assessment** — Project uses **AI Voice Interview** instead, which is better for remote hiring (no webcam/device dependency).
