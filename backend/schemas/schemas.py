from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time

# ==========================================
# 1. Authentication & Token Schemas
# ==========================================

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# ==========================================
# 2. User Schemas
# ==========================================

class UserCreate(BaseModel):
    name: str = Field(..., max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field("employee", description="Role of the user (admin, hr, employee, manager, candidate)")

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class RoleUpdateRequest(BaseModel):
    role: str = Field(..., description="New role for the user")

# ==========================================
# 3. Department Schemas
# ==========================================

class DepartmentCreate(BaseModel):
    department_name: str = Field(..., max_length=100)
    description: Optional[str] = None

class DepartmentResponse(BaseModel):
    id: int
    department_name: str
    description: Optional[str]

    class Config:
        from_attributes = True

# ==========================================
# 4. Dashboard Summary Response
# ==========================================

class DashboardSummaryResponse(BaseModel):
    total_users: int
    total_candidates: int
    total_jobs: int
    total_applications: int
    total_departments: int

# ==========================================
# 5. Analytics Response Schemas
# ==========================================

class JobApplicationsMetric(BaseModel):
    job_title: str
    applications_count: int

class CandidateStatusMetric(BaseModel):
    status: str
    count: int

class DepartmentEmployeesMetric(BaseModel):
    department_name: str
    count: int

class RecruitmentStatusMetric(BaseModel):
    status: str
    count: int

class AnalyticsDashboardResponse(BaseModel):
    applications_per_job: List[JobApplicationsMetric]
    candidate_status_breakdown: List[CandidateStatusMetric]
    employees_per_department: List[DepartmentEmployeesMetric]
    recruitment_summary: List[RecruitmentStatusMetric]


class AttendanceRecord(BaseModel):
    id: int
    employee_id: int
    attendance_date: date
    check_in: Optional[datetime]
    check_out: Optional[datetime]
    working_hours: Optional[float]
    status: Optional[str]


class LeaveRequestResponse(BaseModel):
    id: int
    employee_id: int
    leave_type: Optional[str]
    start_date: date
    end_date: date
    reason: Optional[str]
    status: str
    approved_by: Optional[int]
    created_at: Optional[datetime]


class PerformanceReviewRequest(BaseModel):
    employee_id: int
    score: float
    feedback: Optional[str]


class LeaveApplicationRequest(BaseModel):
    leave_type: Optional[str] = 'General'
    start_date: date
    end_date: date
    reason: Optional[str]


class KPIRecord(BaseModel):
    id: int
    team: str
    metric: str
    value: float
    recorded_at: datetime


class TeamAttendanceMetric(BaseModel):
    date: date
    present: int


class SeniorManagerDashboardResponse(BaseModel):
    pending_leaves: int
    team_attendance: Optional[List[TeamAttendanceMetric]] = None
    kpis: Optional[List[KPIRecord]] = None


class UpdateProfileRequest(BaseModel):
    name: Optional[str]
    profile_picture: Optional[str]


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class NotificationResponse(BaseModel):
    id: int
    title: Optional[str]
    message: Optional[str]
    is_read: bool
    created_at: Optional[datetime]
