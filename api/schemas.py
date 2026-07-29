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
    fix_salary: Optional[float] = None


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str
    branch_id: Optional[int] = None
    fix_salary: Optional[float] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    fix_salary: Optional[float] = None


# ---------- Teacher ----------
class TeacherCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    subject: Optional[str] = None
    branch_id: Optional[int] = None
    # Ishga kirgan sana - retention hisoboti shundan boshlab sanaydi.
    hired_date: Optional[date] = None
    # 1 = hozir ishlayapti, 0 = ishdan ketgan. left_date qo'lda emas,
    # shu bayroqdan avtomatik chiqadi.
    is_active: Optional[int] = 1


class TeacherOut(TeacherCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    branch: Optional[BranchOut] = None
    left_date: Optional[date] = None


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
    # cash | card | terminal | other - faqat kind="payment" uchun
    method: Optional[str] = None
    note: Optional[str] = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: float
    kind: str
    method: Optional[str] = None
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
    left_date: Optional[date] = None
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
    address: Optional[str] = None
    school: Optional[str] = None
    grade: Optional[str] = None
    note: Optional[str] = None
    branch_id: Optional[int] = None
    assigned_user_id: Optional[int] = None


class LeadUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None
    stage: Optional[str] = None
    address: Optional[str] = None
    school: Optional[str] = None
    grade: Optional[str] = None
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
    address: Optional[str] = None
    school: Optional[str] = None
    grade: Optional[str] = None
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


class ExpenseCreate(BaseModel):
    date: date
    category: str = "other"
    amount: float
    note: Optional[str] = None
    branch_id: Optional[int] = None


class ExpenseUpdate(BaseModel):
    date: Optional[date] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None
    branch_id: Optional[int] = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    category: str
    amount: float
    note: Optional[str] = None
    branch_id: Optional[int] = None
    branch: Optional[BranchOut] = None
    created_by: Optional[str] = None
    created_at: datetime


class DashboardStats(BaseModel):
    active_students: int
    trial_students: int
    frozen_students: int
    total_groups: int
    total_teachers: int
    month_income: float
    total_debt: float
    debtor_count: int


# ---------- Davomat va kunlik baho ----------
class AttendanceMark(BaseModel):
    """Bitta o'quvchining bitta darsdagi holati."""
    student_id: int
    present: bool


class AttendanceBulk(BaseModel):
    """Butun ustunni bir so'rovda saqlash - jadvalda bitta dars kuni
    to'liq belgilanadi."""
    marks: List[AttendanceMark]


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lesson_id: int
    student_id: int
    present: bool
    note: Optional[str] = None


class GradeMark(BaseModel):
    student_id: int
    # None = bahoni olib tashlash (coin ham qaytariladi)
    score: Optional[int] = None


class GradeBulk(BaseModel):
    marks: List[GradeMark]


class DailyGradeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    lesson_id: int
    student_id: int
    score: int
    note: Optional[str] = None


class GridStudent(BaseModel):
    id: int
    full_name: str
    status: str


class GridLesson(BaseModel):
    id: int
    date: date


class AttendanceGrid(BaseModel):
    """Davomat/Baholash jadvali: chapda o'quvchilar, tepada dars kunlari.
    marks - "lessonId:studentId" -> qiymat."""
    students: List[GridStudent]
    lessons: List[GridLesson]
    marks: dict


# ---------- Imtihonlar ----------
class ExamCreate(BaseModel):
    kind: str = "unit"
    unit_no: Optional[int] = None
    title: Optional[str] = None
    date: date
    max_score: Optional[float] = None


class ExamUpdate(BaseModel):
    kind: Optional[str] = None
    unit_no: Optional[int] = None
    title: Optional[str] = None
    date: Optional[date] = None
    max_score: Optional[float] = None


class ExamResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    exam_id: int
    student_id: int
    score: Optional[float] = None
    band: Optional[float] = None
    percent: Optional[float] = None
    coins: int = 0
    absent: bool = False
    note: Optional[str] = None


class ExamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    group_id: int
    kind: str
    unit_no: Optional[int] = None
    title: Optional[str] = None
    date: date
    max_score: Optional[float] = None
    created_by: Optional[str] = None
    created_at: datetime
    # Ro'yxatda ko'rsatish uchun qisqa xulosa
    result_count: int = 0
    avg_percent: Optional[float] = None


class ExamDetail(ExamOut):
    results: List[ExamResultOut] = []
    students: List[GridStudent] = []


class ExamScoreMark(BaseModel):
    student_id: int
    score: Optional[float] = None
    band: Optional[float] = None
    absent: bool = False
    note: Optional[str] = None


class ExamScoreBulk(BaseModel):
    marks: List[ExamScoreMark]


# ---------- Coin / gamification ----------
class CoinEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    amount: int
    source: str
    ref_id: Optional[int] = None
    note: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime


class CoinManual(BaseModel):
    amount: int
    note: Optional[str] = None


class CoinBalance(BaseModel):
    student_id: int
    full_name: str
    group: Optional[str] = None
    branch: Optional[str] = None
    balance: int
    earned: int
    spent: int


class ExamCoinRuleIn(BaseModel):
    min_percent: float
    coins: int
    kind: Optional[str] = None


class ExamCoinRuleOut(ExamCoinRuleIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RewardCreate(BaseModel):
    name: str
    cost: int
    value_som: Optional[float] = None
    stock: Optional[int] = None
    active: Optional[bool] = True
    branch_id: Optional[int] = None


class RewardUpdate(BaseModel):
    name: Optional[str] = None
    cost: Optional[int] = None
    value_som: Optional[float] = None
    stock: Optional[int] = None
    active: Optional[bool] = None
    branch_id: Optional[int] = None


class RewardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    cost: int
    value_som: Optional[float] = None
    stock: Optional[int] = None
    active: bool = True
    branch_id: Optional[int] = None
    branch: Optional[BranchOut] = None


class RedeemRequest(BaseModel):
    student_id: int
    reward_id: int


class RedemptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    reward_id: int
    coins: int
    created_by: Optional[str] = None
    created_at: datetime
    student: Optional[GridStudent] = None
    reward: Optional[RewardOut] = None


# ---------- Adminlar KPI ----------
class KpiCollectionRuleIn(BaseModel):
    min_students: int
    max_students: Optional[int] = None
    min_percent: float
    bonus: float


class KpiCollectionRuleOut(KpiCollectionRuleIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class KpiNewClientRuleIn(BaseModel):
    min_clients: int
    bonus: float


class KpiNewClientRuleOut(KpiNewClientRuleIn):
    model_config = ConfigDict(from_attributes=True)
    id: int


class KpiRules(BaseModel):
    collection: List[KpiCollectionRuleOut] = []
    new_clients: List[KpiNewClientRuleOut] = []


class KpiRulesIn(BaseModel):
    collection: List[KpiCollectionRuleIn] = []
    new_clients: List[KpiNewClientRuleIn] = []


class AdminKpi(BaseModel):
    """Bitta adminning bir oylik ish haqi hisobi.

    Bonuslar FILIAL ko'rsatkichi bo'yicha - bir filialda ikkita admin
    bo'lsa, ikkalasi ham to'liq bonusni oladi."""
    user_id: int
    full_name: str
    branch_id: Optional[int] = None
    branch: Optional[str] = None

    fix_salary: float = 0

    # Filial ko'rsatkichlari
    active_students: int = 0
    expected: float = 0        # eski o'quvchilarga hisoblangan summa
    collected: float = 0       # ulardan tushgan summa
    collection_percent: float = 0
    collection_bonus: float = 0

    new_clients: int = 0       # birinchi marta to'lagan o'quvchilar
    new_client_revenue: float = 0
    new_client_bonus: float = 0

    total: float = 0


class AdminKpiResult(BaseModel):
    period: str
    rows: List[AdminKpi] = []
