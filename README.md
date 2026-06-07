# HRMS Candidate Module – Backend

AI-Powered Human Resource Management System – Candidate Module.

## Features
- JWT + bcrypt authentication
- Google OAuth 2.0 login
- Candidate profile management
- PDF/DOCX resume upload
- AI resume parsing (Groq/OpenAI)
- Browse & apply for jobs
- Application status tracking
- Real-time notifications
- AI Video Interview (question generation + evaluation)

## Quick Start

### 1. Install dependencies
```bash
npm install
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your database credentials, JWT secret, and API keys
```

### 3. Run migrations
Connect to your existing PostgreSQL HRMS database and run:
```sql
\i migrations/additional_tables.sql
```
This adds only the columns/tables not already in your schema (safe to run on existing DB).

### 4. Start the server
```bash
# Development (with auto-reload)
npm run dev

# Production
npm start
```

## Project Structure
```
src/
├── config/
│   ├── db.js              PostgreSQL pool
│   ├── jwt.js             Token sign/verify
│   └── googleAuth.js      Google token verification
├── controllers/
│   ├── authController.js
│   ├── candidateController.js
│   ├── applicationController.js
│   ├── notificationController.js
│   └── interviewController.js
├── routes/
│   ├── authRoutes.js
│   ├── candidateRoutes.js
│   ├── applicationRoutes.js
│   ├── notificationRoutes.js
│   └── interviewRoutes.js
├── middleware/
│   ├── authMiddleware.js  JWT + role guards
│   ├── uploadMiddleware.js Multer config
│   └── errorMiddleware.js  404 + global error
├── models/
│   ├── candidateModel.js
│   ├── applicationModel.js
│   ├── interviewModel.js
│   └── notificationModel.js
├── services/
│   ├── aiClient.js               Groq/OpenAI factory
│   ├── resumeParserService.js    PDF/DOCX parsing + AI extraction
│   ├── interviewQuestionService.js  Question generation
│   ├── interviewEvaluationService.js Scoring + feedback
│   └── notificationService.js    Notification templates
├── utils/
│   └── responseHandler.js       Standardised JSON responses
├── uploads/                     Resume files stored here
├── app.js
└── server.js
```

## AI Provider Setup

### Option A: Groq (Recommended – Free Tier)
1. Sign up at https://console.groq.com
2. Create an API key
3. Set in `.env`:
   ```
   AI_PROVIDER=groq
   GROQ_API_KEY=gsk_...
   ```

### Option B: OpenAI
```
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

## Google OAuth Setup
1. Go to https://console.cloud.google.com
2. Create a project → Credentials → OAuth 2.0 Client ID
3. Set Authorised JavaScript origins (your frontend URL)
4. Copy the Client ID to:
   ```
   GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   ```
5. On the frontend, use Google Sign-In and send the `credential` (idToken) to `POST /api/auth/google-login`

## AI Interview Flow (Frontend Integration)

```
1. Check GET /api/interview/status/:appId
   → If can_start=true, show "Start Interview" button

2. POST /api/interview/start { application_id }
   → Save session_id + first question text

3. Play question via browser TTS:
   speechSynthesis.speak(new SpeechSynthesisUtterance(question.text))

4. Record candidate answer using Web Speech API / MediaRecorder

5. POST /api/interview/answer { session_id, answer_text }
   → If response.data.repeated=true → play question again
   → Else play next_question

6. Repeat until all 3 answered

7. POST /api/interview/complete { session_id }
   → Show "Interview Completed" screen
```

## Repeat Trigger Phrases
The following phrases in an answer will cause the current question to be repeated:
- "repeat"
- "repeat question"
- "can you repeat that"
- "please repeat"
- "say again"

## Deployment Notes
- Set `NODE_ENV=production` in environment
- Use a process manager like PM2: `pm2 start src/server.js`
- Put behind NGINX with HTTPS
- Set `CORS_ORIGIN` to your frontend domain
- Use environment-specific `.env` files (never commit them)
