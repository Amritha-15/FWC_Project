from sqlalchemy import Column, Integer, String, Text, Numeric, Date, Time, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)
    google_id = Column(Text, unique=True, nullable=True)
    profile_picture = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    candidate = relationship("Candidate", uselist=False, back_populates="user", cascade="all, delete-orphan")
    employee = relationship("Employee", uselist=False, back_populates="user", cascade="all, delete-orphan")

class Department(Base):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True, index=True)
    department_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    employee_code = Column(String(50), unique=True, nullable=True)
    department_id = Column(Integer, ForeignKey('departments.id'), nullable=True)
    manager_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    designation = Column(String(100), nullable=True)
    salary = Column(Numeric(10, 2), nullable=True)
    joining_date = Column(Date, nullable=True)
    status = Column(String(20), default='active')

    user = relationship("User", back_populates="employee")
    department = relationship("Department", back_populates="employees")

class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=True)
    experience_required = Column(String(50), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'))
    status = Column(String(20), default='Open')
    created_at = Column(DateTime, server_default=func.now())
    department = Column(String(100), nullable=True)
    location = Column(String(100), nullable=True)
    salary_range = Column(String(100), nullable=True)

    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    schedules = relationship("InterviewSchedule", back_populates="job", cascade="all, delete-orphan")

class Candidate(Base):
    __tablename__ = 'candidates'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    phone = Column(String(20), nullable=True)
    education = Column(Text, nullable=True)
    experience = Column(Text, nullable=True)
    resume_url = Column(Text, nullable=True)
    current_status = Column(String(50), default='Applied')
    skills = Column(Text, nullable=True)
    certifications = Column(Text, nullable=True)
    projects = Column(Text, nullable=True)
    resume_parsed_at = Column(DateTime, nullable=True)
    resume_summary = Column(Text, nullable=True)
    resume_quality_score = Column(Numeric(5, 2), nullable=True)
    skill_strength_score = Column(Numeric(5, 2), nullable=True)

    user = relationship("User", back_populates="candidate")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    schedules = relationship("InterviewSchedule", back_populates="candidate", cascade="all, delete-orphan")

class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id', ondelete='CASCADE'))
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    resume_score = Column(Numeric(5, 2), nullable=True)
    interview_score = Column(Numeric(5, 2), nullable=True)
    application_status = Column(String(50), default='Applied')
    applied_at = Column(DateTime, server_default=func.now())
    match_score = Column(Numeric(5, 2), nullable=True)
    ranking_position = Column(Integer, nullable=True)
    hiring_confidence_score = Column(Numeric(5, 2), nullable=True)
    skill_gap = Column(JSON, nullable=True)
    hiring_recommendation = Column(JSON, nullable=True)

    candidate = relationship("Candidate", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    schedules = relationship("InterviewSchedule", back_populates="application", cascade="all, delete-orphan")

class InterviewSchedule(Base):
    __tablename__ = 'interview_schedules'

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id', ondelete='CASCADE'))
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    application_id = Column(Integer, ForeignKey('applications.id', ondelete='CASCADE'))
    interview_date = Column(Date, nullable=False)
    interview_time = Column(Time, nullable=False)
    meeting_link = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    candidate = relationship("Candidate", back_populates="schedules")
    job = relationship("Job", back_populates="schedules")
    application = relationship("Application", back_populates="schedules")

class Attendance(Base):
    __tablename__ = 'attendance'

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'))
    attendance_date = Column(Date, nullable=False)
    check_in = Column(DateTime, nullable=True)
    check_out = Column(DateTime, nullable=True)
    working_hours = Column(Numeric(6,2), nullable=True)
    status = Column(String(50), default='Present')

    employee = relationship('Employee')


class LeaveRequest(Base):
    __tablename__ = 'leave_requests'

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'))
    leave_type = Column(String(50), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(20), default='Pending')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    employee = relationship('Employee')


class PerformanceReview(Base):
    __tablename__ = 'performance_reviews'

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'))
    reviewer_id = Column(Integer, ForeignKey('employees.id'), nullable=True)
    score = Column(Numeric(5,2), nullable=True)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    employee = relationship('Employee', foreign_keys=[employee_id])


class KPI(Base):
    __tablename__ = 'kpis'

    id = Column(Integer, primary_key=True, index=True)
    team = Column(String(100), nullable=False)
    metric = Column(String(100), nullable=False)
    value = Column(Numeric(10,2), nullable=False)
    recorded_at = Column(DateTime, server_default=func.now())


class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = Column(String(200), nullable=False)
    target_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())
    ip_address = Column(String(100), nullable=True)

    admin = relationship('User', foreign_keys=[admin_id])


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    title = Column(String(200), nullable=True)
    message = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship('User', backref='notifications')


class InterviewResult(Base):
    __tablename__ = 'interview_results'

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id', ondelete='CASCADE'))
    job_id = Column(Integer, ForeignKey('jobs.id', ondelete='CASCADE'))
    application_id = Column(Integer, ForeignKey('applications.id'), nullable=True)

    questions = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)

    communication_score = Column(Numeric(5,2), nullable=True)
    technical_score = Column(Numeric(5,2), nullable=True)
    problem_solving_score = Column(Numeric(5,2), nullable=True)
    confidence_score = Column(Numeric(5,2), nullable=True)

    overall_score = Column(Numeric(5,2), nullable=True)

    recommendation = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    answers = Column(JSON, nullable=True)

    created_at = Column(DateTime, server_default=func.now())


class Onboarding(Base):
    __tablename__ = 'onboarding'

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey('candidates.id'))
    employee_id = Column(Integer, ForeignKey('employees.id'))
    offer_letter_status = Column(String(50), default='Pending')
    joining_status = Column(String(50), default='Pending')
    created_at = Column(DateTime, server_default=func.now())