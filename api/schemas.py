from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ---------- Branch ----------
class BranchCreate(BaseModel):
    name: str
    address: Optional[str] = None


class BranchOut(BranchCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    branch_id: Optional[int] = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    role: str
    branch_id: Optional[int] = None
    branch: Optional[BranchOut] = None
    is_active: bool = True


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str
    branch_id: Optional[int] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


# ---------- Teacher ----------
class TeacherCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    subject: Optional[str] = None
    branch_id: Optional[int] = None


class TeacherOut(TeacherCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    branch: Optional[BranchOut] = None


# ---------- Group ----------
class GroupCreate(BaseModel):
    name: str
    room: Optional[str] = None
    teacher_id: Optional[int] = None
    branch_id: Optional[int] = None
    monthly_fee: float = 0
    lesson_price: float = 40000
    standard_lessons_per_month: int = 12
    teacher_rate_per_student: float = 0


class GroupOut(GroupCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    teacher: Optional[TeacherOut] = None
    branch: Optional[BranchOut] = None
    student_count: int = 0


# ---------- Lesson ("yoqlama") ----------
class LessonCreate(BaseModel):
    date: date
    teacher_id: Optional[int] = None
    note: Optional[str] = None


class LessonOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int
    teacher_id: Optional[int] = None
    teacher: Optional[TeacherOut] = None
    date: date
    note: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime


# ---------- Billing / payroll ----------
class StudentChargeResult(BaseModel):
    student_id: int
    student_name: str
    billable_lessons: int
    amount: float
    already_charged: bool
    created: bool = False


class BillingRunResult(BaseModel):
    period: str
    held_lessons: int
    committed: bool
    results: List[StudentChargeResult]


class TeacherPayoutOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: Optional[int] = None
    teacher_id: int
    teacher: Optional[TeacherOut] = None
    group_id: int
    period: str
    student_count: int
    held_lessons: int
    taught_lessons: int
    amount: float
    paid: bool = False


class PayrollRunResult(BaseModel):
    period: str
    committed: bool
    results: List[TeacherPayoutOut]


class PayoutUpdate(BaseModel):
    paid: bool


# ---------- Payment ----------
class PaymentCreate(BaseModel):
    amount: float
    kind: str = "payment"  # payment | charge | discount
    note: Optional[str] = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: float
    kind: str
    note: Optional[str] = None
    created_by: Optional[str] = None
    period: Optional[str] = None
    created_at: datetime


# ---------- Student ----------
class StudentCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    parent_phone: Optional[str] = None
    birth_date: Optional[date] = None
    enrolled_date: Optional[date] = None
    group_id: Optional[int] = None
    branch_id: Optional[int] = None
    status: str = "active"
    note: Optional[str] = None


class StudentUpdate(StudentCreate):
    full_name: Optional[str] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone: Optional[str] = None
    parent_phone: Optional[str] = None
    birth_date: Optional[date] = None
    enrolled_date: Optional[date] = None
    status: str
    note: Optional[str] = None
    group: Optional[GroupOut] = None
    branch: Optional[BranchOut] = None
    balance: float = 0


class StudentDetail(StudentOut):
    payments: List[PaymentOut] = []


class StaffOption(BaseModel):
    """Lidga mas'ul xodim tanlash uchun qisqartirilgan foydalanuvchi ma'lumoti
    - to'liq UserOut'ni ochmaydi (u faqat HR/adminlar uchun)."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    role: str


class LeadCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    source: str = "other"
    # Berilmasa, manbaga qarab avtomatik tanlanadi.
    stage: Optional[str] = None
    note: Optional[str] = None
    branch_id: Optional[int] = None
    assigned_user_id: Optional[int] = None


class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    stage: Optional[str] = None
    note: Optional[str] = None
    branch_id: Optional[int] = None
    assigned_user_id: Optional[int] = None


class LeadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    phone: Optional[str] = None
    source: str
    stage: str
    note: Optional[str] = None
    branch_id: Optional[int] = None
    branch: Optional[BranchOut] = None
    assigned_user_id: Optional[int] = None
    assigned_user: Optional[StaffOption] = None
    converted_student_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class LeadConvertRequest(BaseModel):
    """Lidni o'quvchiga aylantirish - ixtiyoriy ravishda darrov guruhga
    biriktirish va qo'shilgan sanani belgilash mumkin."""
    group_id: Optional[int] = None
    enrolled_date: Optional[date] = None


class DashboardStats(BaseModel):
    active_students: int
    trial_students: int
    frozen_students: int
    total_groups: int
    total_teachers: int
    month_income: float
    total_debt: float
    debtor_count: int
