import sys, os
# Ensure project root is on import path for direct script execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import random
import json
from datetime import date, datetime, timedelta

import asyncpg

from backend.core.config import settings
from backend.core.security import get_password_hash


PASSWORD = "Password123"


def mk_email(name, idx):
    return f"{name.lower().replace(' ', '.')}{idx}@example.com"


async def run():
    dsn = settings.DATABASE_URL
    conn = await asyncpg.connect(dsn=dsn)

    try:
        # Truncate tables to start fresh
        await conn.execute("TRUNCATE TABLE users, employees, candidates, jobs, applications, interview_questions, interview_results, attendance, leave_requests, performance_reviews, notifications, onboarding, kpis RESTART IDENTITY CASCADE;")
        async with conn.transaction():
            # Departments (7)
            departments = [
                'Engineering', 'Product', 'Design', 'Sales', 'Marketing', 'Human Resources', 'Finance'
            ]
            dept_ids = []
            for name in departments:
                row = await conn.fetchrow("INSERT INTO departments (department_name, description) VALUES ($1, $2) RETURNING id", name, f"{name} department")
                dept_ids.append(row['id'])

            # Create 25 users
            first_names = ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Jamie', 'Avery', 'Drew', 'Quinn', 'Sam', 'Cameron', 'Reese', 'Charlie', 'Parker', 'Rowan', 'Skyler', 'Bailey', 'Harper', 'Finley', 'Elliot', 'Hayden', 'Kai', 'Logan', 'Noah']
            users = []
            for i in range(25):
                name = first_names[i % len(first_names)] + (f" {i//len(first_names)+1}" if i >= len(first_names) else "")
                email = mk_email(first_names[i % len(first_names)], i+1)
                pw = get_password_hash(PASSWORD)
                role = 'employee'
                # We'll set HR and managers among employees later
                row = await conn.fetchrow("""INSERT INTO users (name, email, password_hash, role) VALUES ($1,$2,$3,$4)
                   ON CONFLICT (email) DO UPDATE SET role=EXCLUDED.role
                   RETURNING id""",
                   name, email, pw, role)
                users.append({'id': row['id'], 'name': name, 'email': email})

            # Assign employee users: first 15 users are employees (including 2 HR and 3 managers)
            employee_user_ids = [u['id'] for u in users[:15]]
            hr_user_ids = employee_user_ids[:2]
            manager_user_ids = employee_user_ids[2:5]

            # Update HR roles
            for uid in hr_user_ids:
                await conn.execute("UPDATE users SET role='hr' WHERE id=$1", uid)

            # Update manager roles
            for uid in manager_user_ids:
                await conn.execute("UPDATE users SET role='manager' WHERE id=$1", uid)

            # Create employees rows
            employee_rows = {}
            # First create manager employee rows so we have employee ids to reference
            for uid in manager_user_ids:
                dept = random.choice(dept_ids)
                code = f"EMP{1000+uid}"
                row = await conn.fetchrow(
                    "INSERT INTO employees (user_id, employee_code, department_id, manager_id, designation, salary, joining_date, status) VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id",
                    uid, code, dept, None, random.choice(['Engineering Manager','Senior Manager','Team Lead']), random.randint(80000,140000), date.today() - timedelta(days=random.randint(365,2000)), 'active'
                )
                employee_rows[uid] = row['id']

            # Create remaining employee rows and assign manager_id as an employee.id
            manager_emp_ids = list(employee_rows.values())
            for uid in employee_user_ids:
                if uid in employee_rows:
                    continue
                dept = random.choice(dept_ids)
                mgr_emp_id = random.choice(manager_emp_ids)
                code = f"EMP{1000+uid}"
                row = await conn.fetchrow(
                    "INSERT INTO employees (user_id, employee_code, department_id, manager_id, designation, salary, joining_date, status) VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id",
                    uid, code, dept, mgr_emp_id, random.choice(['Engineer','Senior Engineer','Product Manager','Designer','Sales Rep']), random.randint(40000,120000), date.today() - timedelta(days=random.randint(30,1000)), 'active'
                )
                employee_rows[uid] = row['id']

            # Candidates: next 10 users are candidates
            candidate_user_ids = [u['id'] for u in users[15:25]]
            candidate_rows = {}
            for uid in candidate_user_ids:
                phone = f"+1555{random.randint(1000000,9999999)}"
                row = await conn.fetchrow("INSERT INTO candidates (user_id, phone, education, experience, resume_url, current_status, skills) VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING id",
                                        uid, phone, random.choice(['BSc Computer Science','MSc Computer Science','BCom','BA']), f"{random.randint(0,10)} years", None, 'Applied', 'Python,SQL')
                candidate_rows[uid] = row['id']

            # Jobs (10)
            job_titles = ['Backend Engineer','Frontend Engineer','Data Scientist','Product Manager','UX Designer','Sales Associate','Marketing Manager','HR Generalist','Finance Analyst','Support Engineer']
            job_ids = []
            for t in job_titles:
                row = await conn.fetchrow(
                    "INSERT INTO jobs (title, description, required_skills, created_by, status, department, location, salary_range) VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id",
                    t, f"Hiring for {t}", 'Python,SQL', users[0]['id'], 'Open', random.choice(departments), random.choice(['Remote','NYC','SF','London']), '$40k-$120k'
                )
                job_ids.append(row['id'])

            # KPIs (team, metric, value)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS kpis (
                    id SERIAL PRIMARY KEY,
                    team VARCHAR(100) NOT NULL,
                    metric VARCHAR(100) NOT NULL,
                    value NUMERIC(10,2) NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            team_names = ['Engineering', 'Product', 'Design', 'Sales', 'Marketing', 'HR', 'Finance']
            metrics = ['velocity', 'quarterly_revenue', 'employee_satisfaction', 'lead_conversion', 'budget_utilization']
            for _ in range(10):
                team = random.choice(team_names)
                metric = random.choice(metrics)
                value = round(random.uniform(50, 1000), 2)
                await conn.execute("INSERT INTO kpis (team, metric, value) VALUES ($1, $2, $3)", team, metric, value)

            # Applications (20)
            application_ids = []
            statuses = ['Applied','Shortlisted','Interview Scheduled','Selected','Rejected']
            for _ in range(20):
                cand_uid = random.choice(candidate_user_ids)
                cand_id = candidate_rows[cand_uid]
                job_id = random.choice(job_ids)
                status = random.choice(statuses[:4])
                row = await conn.fetchrow("INSERT INTO applications (candidate_id, job_id, resume_score, interview_score, application_status, match_score) VALUES ($1,$2,$3,$4,$5,$6) RETURNING id",
                                        cand_id, job_id, round(random.uniform(50,90),2), None, status, round(random.uniform(0,1),2))
                application_ids.append(row['id'])

            # Interview questions table (create if not exists) and populate
            await conn.execute("CREATE TABLE IF NOT EXISTS interview_questions (id SERIAL PRIMARY KEY, question TEXT)")
            iq_ids = []
            sample_qs = [
                'Tell me about yourself.', 'Describe a challenging technical problem you solved.', 'How do you test your code?', 'Explain a past project you led.', 'Why do you want to join us?'
            ]
            for q in sample_qs:
                r = await conn.fetchrow("INSERT INTO interview_questions (question) VALUES ($1) RETURNING id", q)
                iq_ids.append(r['id'])

            # Interview results (10)
            ir_ids = []
            for i in range(10):
                app_id = random.choice(application_ids)
                # fetch candidate_id and job_id for this application
                rec = await conn.fetchrow('SELECT candidate_id, job_id FROM applications WHERE id=$1', app_id)
                comm = round(random.uniform(2,5),2)
                tech = round(random.uniform(2,5),2)
                prob = round(random.uniform(2,5),2)
                conf = round(random.uniform(2,5),2)
                overall = round((comm+tech+prob+conf)/4,2)
                answers = [{'question': random.choice(sample_qs), 'answer': 'Sample answer'} for _ in range(3)]
                row = await conn.fetchrow(
                    "INSERT INTO interview_results (candidate_id, job_id, application_id, questions, transcript, communication_score, technical_score, problem_solving_score, confidence_score, overall_score, recommendation, ai_feedback, answers, video_url) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14) RETURNING id",
                    rec['candidate_id'], rec['job_id'], app_id, '\n'.join([a['question'] for a in answers]), 'Transcript text', comm, tech, prob, conf, overall, random.choice(['Hire','Maybe','Reject']), 'AI says looks good', json.dumps(answers), None
                )
                ir_ids.append(row['id'])

            # Attendance (60) for employee ids
            attendance_status = ['Present', 'Absent', 'Late', 'Half Day']
            emp_ids = list(employee_rows.values())
            for _ in range(60):
                emp = random.choice(emp_ids)
                at_date = date.today() - timedelta(days=random.randint(1,60))
                status = random.choice(attendance_status)
                working_hours = 8 if status == 'Present' else (4 if status == 'Half Day' else 0)
                # adapt to actual attendance schema: (employee_id, attendance_date, check_in, check_out, working_hours, status)
                await conn.execute("INSERT INTO attendance (employee_id, attendance_date, check_in, check_out, working_hours, status) VALUES ($1,$2,$3,$4,$5,$6)", emp, at_date, None, None, working_hours, status)

            # Leave requests (15)
            for _ in range(15):
                emp = random.choice(emp_ids)
                start = date.today() - timedelta(days=random.randint(1,90))
                end = start + timedelta(days=random.randint(1,7))
                await conn.execute("INSERT INTO leave_requests (employee_id, start_date, end_date, reason, status) VALUES ($1,$2,$3,$4,$5)", emp, start, end, 'Personal', random.choice(['Pending','Approved','Rejected']))

            # Performance reviews (20) - adapt to existing schema (manager_id, rating, review_date)
            for _ in range(20):
                emp = random.choice(emp_ids)
                manager = random.choice(emp_ids)
                rating = random.randint(2,5)
                review_date = date.today() - timedelta(days=random.randint(1,365))
                await conn.execute(
                    "INSERT INTO performance_reviews (employee_id, manager_id, rating, feedback, review_date) VALUES ($1, $2, $3, $4, $5)",
                    emp, manager, rating, f"Performance rating {rating}", review_date
                )

            # Notifications (30)
            for _ in range(30):
                user = random.choice([u['id'] for u in users])
                await conn.execute("INSERT INTO notifications (user_id, title, message, is_read) VALUES ($1,$2,$3,$4)", user, 'Notice', 'This is a demo notification', random.choice([True, False]))

            # Onboarding (5) - pick some interview_results and create employee rows for candidate users
            onboard_created = 0
            for ir in ir_ids[:5]:
                rec = await conn.fetchrow('SELECT candidate_id FROM interview_results WHERE id=$1', ir)
                # find user id for candidate
                cand = await conn.fetchrow('SELECT user_id FROM candidates WHERE id=$1', rec['candidate_id'])
                # create employee row for this candidate's user if not exists
                existing = await conn.fetchrow('SELECT id FROM employees WHERE user_id=$1', cand['user_id'])
                if existing:
                    emp_id = existing['id']
                else:
                    row = await conn.fetchrow("INSERT INTO employees (user_id, employee_code, department_id, manager_id, designation, salary, joining_date, status) VALUES ($1,$2,$3,$4,$5,$6,$7,$8) RETURNING id",
                                            cand['user_id'], f"EMP{2000+cand['user_id']}", random.choice(dept_ids), random.choice(list(employee_rows.values())), 'New Hire', random.randint(40000,90000), date.today(), 'onboarding')
                    emp_id = row['id']
                await conn.execute('INSERT INTO onboarding (candidate_id, employee_id, offer_letter_status, joining_status) VALUES ($1,$2,$3,$4)', rec['candidate_id'], row['id'], 'Sent', 'Pending')
                onboard_created += 1

            print('Seeding complete')
    finally:
        await conn.close()


if __name__ == '__main__':
    asyncio.run(run())
