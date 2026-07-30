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
    public_id: Optional[str] = None
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
    room_id: Optional[int] = None
    capacity: Optional[int] = None
    teacher_id: Optional[int] = None
    branch_id: Optional[int] = None
    subject: Optional[str] = None
    level: Optional[str] = None
    end_date: Optional[date] = None
    start_date: Optional[date] = None
    lesson_time: Optional[str] = None
    lesson_days: Optional[str] = None
    monthly_fee: float = 0
    lesson_price: float = 40000
    standard_lessons_per_month: int = 12
    teacher_rate_per_student: float = 0


class GroupUpdate(BaseModel):
    """Qisman tahrirlash - faqat yuborilgan maydonlar o'zgaradi.
    Masalan jadvalni o'zgartirish uchun butun guruhni qayta yuborish
    shart emas: {"lesson_days": "mon,wed"} yetadi."""
    name: Optional[str] = None
    room: Optional[str] = None
    room_id: Optional[int] = None
    capacity: Optional[int] = None
    teacher_id: Optional[int] = None
    branch_id: Optional[int] = None
    subject: Optional[str] = None
    level: Optional[str] = None
    end_date: Optional[date] = None
    start_date: Optional[date] = None
    lesson_time: Optional[str] = None
    lesson_days: Optional[str] = None
    monthly_fee: Optional[float] = None
    lesson_price: Optional[float] = None
    standard_lessons_per_month: Optional[int] = None
    teacher_rate_per_student: Optional[float] = None


class GroupOut(GroupCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    public_id: Optional[str] = None
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
    held: int = 1
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
    public_id: Optional[str] = None
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
    parent_id: Optional[int] = None
    # Yangi o'quvchi darrov "faol" bo'lmaydi - avval sinov darsida turadi.
    # Faollashtirish qo'lda, guruhdagi ro'yxatdan qilinadi.
    status: str = "trial"
    note: Optional[str] = None


class StudentUpdate(StudentCreate):
    full_name: Optional[str] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    public_id: Optional[str] = None
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
    public_id: Optional[str] = None
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
    channel: Optional[str] = None
    method: Optional[str] = "cash"


class ExpenseUpdate(BaseModel):
    date: Optional[date] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    note: Optional[str] = None
    branch_id: Optional[int] = None
    channel: Optional[str] = None
    method: Optional[str] = None


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: date
    category: str
    amount: float
    note: Optional[str] = None
    branch_id: Optional[int] = None
    branch: Optional[BranchOut] = None
    channel: Optional[str] = None
    method: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime


class DashboardStats(BaseModel):
    active_students: int
    trial_students: int
    frozen_students: int
    total_groups: int
    total_teachers: int
    # Shu oy nechta to'lov qabul qilindi va shundan nechtasi yangi mijoz
    month_payment_count: int = 0
    month_new_payment_count: int = 0
    staff_count: int = 0
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
    held: int = 1


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


# ---------- HR ----------
class VacancyCreate(BaseModel):
    title: str
    role: Optional[str] = None
    branch_id: Optional[int] = None
    headcount: int = 1
    status: str = "open"
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    description: Optional[str] = None


class VacancyUpdate(BaseModel):
    title: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[int] = None
    headcount: Optional[int] = None
    status: Optional[str] = None
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    description: Optional[str] = None


class CandidateCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    vacancy_id: Optional[int] = None
    stage: str = "applied"
    source: str = "other"
    branch_id: Optional[int] = None
    note: Optional[str] = None


class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    vacancy_id: Optional[int] = None
    stage: Optional[str] = None
    source: Optional[str] = None
    branch_id: Optional[int] = None
    note: Optional[str] = None
    reject_reason: Optional[str] = None


# ---------- Ijtimoiy tarmoq ----------
class SocialManual(BaseModel):
    platform: str
    followers: int


# ---------- Guruhdagi o'quvchi ustidagi amallar ----------
class StudentGroupMove(BaseModel):
    """Boshqa guruhga o'tkazish. group_id None bo'lsa - guruhdan chiqariladi."""
    group_id: Optional[int] = None


# ---------- Ota-ona ----------
class ParentCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    phone2: Optional[str] = None
    relation: Optional[str] = None
    address: Optional[str] = None
    workplace: Optional[str] = None
    note: Optional[str] = None
    branch_id: Optional[int] = None


class ParentUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    relation: Optional[str] = None
    address: Optional[str] = None
    workplace: Optional[str] = None
    note: Optional[str] = None
    branch_id: Optional[int] = None


# ---------- Shartnoma ----------
class ContractCreate(BaseModel):
    student_id: int
    parent_id: Optional[int] = None
    group_id: Optional[int] = None
    branch_id: Optional[int] = None
    date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    monthly_fee: float = 0
    discount_percent: float = 0
    status: str = "active"
    note: Optional[str] = None


class ContractUpdate(BaseModel):
    parent_id: Optional[int] = None
    group_id: Optional[int] = None
    date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    monthly_fee: Optional[float] = None
    discount_percent: Optional[float] = None
    status: Optional[str] = None
    note: Optional[str] = None


# ---------- Shikoyat ----------
class ComplaintCreate(BaseModel):
    subject: str
    body: Optional[str] = None
    student_id: Optional[int] = None
    group_id: Optional[int] = None
    branch_id: Optional[int] = None
    source: str = "phone"
    severity: str = "normal"
    status: str = "open"
    assigned_user_id: Optional[int] = None


class ComplaintUpdate(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
    student_id: Optional[int] = None
    group_id: Optional[int] = None
    source: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    assigned_user_id: Optional[int] = None


# ---------- O'quv bo'limi ----------
class RoomCreate(BaseModel):
    name: str
    capacity: int = 12
    branch_id: Optional[int] = None
    note: Optional[str] = None
    active: int = 1


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None
    branch_id: Optional[int] = None
    note: Optional[str] = None
    active: Optional[int] = None


class RiskFlagCreate(BaseModel):
    student_id: int
    signal: str
    note: Optional[str] = None


class RiskTaskCreate(BaseModel):
    student_id: int
    title: str
    level: Optional[str] = None
    assigned_user_id: Optional[int] = None
    due_date: Optional[date] = None


class RiskTaskUpdate(BaseModel):
    title: Optional[str] = None
    assigned_user_id: Optional[int] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    result: Optional[str] = None


# ---------- Ota-ona suhbati / sertifikat ----------
class ParentTalkCreate(BaseModel):
    date: Optional[date] = None
    channel: str = "phone"
    topic: str
    summary: Optional[str] = None
    outcome: Optional[str] = None


class CertificateCreate(BaseModel):
    kind: str = "internal"
    level: Optional[str] = None
    score: Optional[float] = None
    date: Optional[date] = None
    note: Optional[str] = None


# ---------- Reklama ko'rsatkichi ----------
class AdStatCreate(BaseModel):
    channel: str
    period: str          # "2026-07"
    impressions: int = 0
    clicks: int = 0
    branch_id: Optional[int] = None
    note: Optional[str] = None


# ---------- Examiner ----------
class ExamStatusUpdate(BaseModel):
    status: str
    note: Optional[str] = None


class RetakeCreate(BaseModel):
    date: Optional[date] = None
    note: Optional[str] = None


# ---------- Support teacher ----------
class SupportAssignmentCreate(BaseModel):
    user_id: int
    group_id: Optional[int] = None
    student_id: Optional[int] = None
    note: Optional[str] = None


class SupportPlanCreate(BaseModel):
    student_id: int
    user_id: Optional[int] = None
    issue: str = "attendance"
    plan: str
    due_date: Optional[date] = None


class SupportPlanUpdate(BaseModel):
    issue: Optional[str] = None
    plan: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[str] = None
    result: Optional[str] = None


# ---------- Fayl ----------
class AttachmentCreate(BaseModel):
    entity: str
    entity_id: int
    kind: str = "document"
    filename: Optional[str] = None
    mime: Optional[str] = None
    note: Optional[str] = None
    data: str          # base64 yoki data URL


# ---------- Xodim ishdan bo'shashi ----------
class ExitTypeUpdate(BaseModel):
    exit_type: str
    exit_reason: Optional[str] = None
