import datetime as _dt
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
    # Eslatmalar shu ikki sanaga tayanadi - ro'yxatda ham ko'rinsin
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    hired_date: Optional[date] = None


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str
    branch_id: Optional[int] = None
    fix_salary: Optional[float] = None
    # ---- Xodim kartasi ----
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    position: Optional[str] = None
    manager_id: Optional[int] = None
    hired_date: Optional[date] = None
    photo: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[int] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    fix_salary: Optional[float] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    position: Optional[str] = None
    manager_id: Optional[int] = None
    hired_date: Optional[date] = None
    photo: Optional[str] = None


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
    # Maksimal yuklama. Bo'sh bo'lsa daraja, u ham bo'lmasa tizim
    # standarti ishlatiladi.
    max_groups: Optional[int] = None
    max_lessons_per_day: Optional[int] = None
    # ---- Daraja va karyera ----
    grade: Optional[str] = None
    cert: Optional[str] = None
    cert_score: Optional[float] = None
    qualification: Optional[str] = None
    birth_date: Optional[date] = None
    skill_score: Optional[float] = None
    support_months: Optional[float] = None


class TeacherOut(TeacherCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    branch: Optional[BranchOut] = None
    left_date: Optional[date] = None
    grade_since: Optional[date] = None
    remediation_until: Optional[date] = None
    remediation_reason: Optional[str] = None


# ---------- Ustoz darajasi ----------
class GradeUpdate(BaseModel):
    label: Optional[str] = None
    rate_per_student: Optional[float] = None
    min_months: Optional[int] = None
    min_groups: Optional[int] = None
    max_groups: Optional[int] = None
    cert_label: Optional[str] = None
    cert_min: Optional[float] = None
    promote_pass_rate: Optional[float] = None
    demote_below: Optional[float] = None
    min_results: Optional[int] = None
    result_band: Optional[float] = None
    min_age: Optional[int] = None
    min_skill: Optional[float] = None
    level_pass_percent: Optional[float] = None


class GradeSet(BaseModel):
    """Asoschi darajani qo'lda qo'yadi (yoki avtomat qarorni qaytaradi)."""
    grade: str
    reason: Optional[str] = None


class StudyDone(BaseModel):
    done: bool
    note: Optional[str] = None


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
    # Hozirgi darajasi - guruhga qo'shishda moslik tekshiriladi.
    subject: Optional[str] = None
    level: Optional[str] = None
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
    # ---- Nomzod kartasi ----
    cv: Optional[str] = None
    experience_years: Optional[float] = None
    workplaces: Optional[str] = None
    certificates: Optional[str] = None
    language_level: Optional[str] = None
    expected_salary: Optional[float] = None
    trial_score: Optional[float] = None
    interview_score: Optional[float] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    reference_note: Optional[str] = None
    decision: Optional[str] = None


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


# ---------------------------------------------------- Avtomatik tekshiruv
class ScheduleCheck(BaseModel):
    group_id: Optional[int] = None
    teacher_id: Optional[int] = None
    room_id: Optional[int] = None
    lesson_days: Optional[str] = None
    lesson_time: Optional[str] = None


class EnrolmentCheck(BaseModel):
    student_id: int
    group_id: int


# ---------------------------------------------------------- Chegirmalar
class DiscountCreate(BaseModel):
    student_id: int
    kind: str
    percent: Optional[float] = None
    amount: Optional[float] = None
    reason: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    referrer_student_id: Optional[int] = None
    staff_user_id: Optional[int] = None


class DiscountDecision(BaseModel):
    approve: bool = True
    reason: Optional[str] = None


# ------------------------------------------------------------------- HR
class OnboardingUpdate(BaseModel):
    step: str
    done: bool = True
    note: Optional[str] = None


class StaffEventCreate(BaseModel):
    kind: str
    date: Optional[_dt.date] = None
    end_date: Optional[_dt.date] = None
    title: Optional[str] = None
    note: Optional[str] = None
    score: Optional[float] = None
    amount: Optional[float] = None
    minutes: Optional[int] = None


# -------------------------------------------------------------- Vazifalar
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    watcher_id: Optional[int] = None
    branch_id: Optional[int] = None
    deadline: Optional[date] = None
    priority: str = "normal"
    source: str = "manual"
    meeting: Optional[str] = None
    checklist: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    watcher_id: Optional[int] = None
    branch_id: Optional[int] = None
    deadline: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None
    delay_reason: Optional[str] = None
    meeting: Optional[str] = None
    checklist: Optional[List[dict]] = None
    attachment_id: Optional[int] = None


class MeetingDecision(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    deadline: Optional[date] = None
    priority: Optional[str] = "normal"


class MeetingDecisions(BaseModel):
    meeting: str
    decisions: List[MeetingDecision]
    branch_id: Optional[int] = None
    watcher_id: Optional[int] = None
    deadline: Optional[date] = None


# --------------------------------------------------------- Ombor/aktivlar
class AssetCreate(BaseModel):
    name: str
    kind: str = "other"
    inventory_no: Optional[str] = None
    branch_id: Optional[int] = None
    room_id: Optional[int] = None
    responsible_id: Optional[int] = None
    purchased_on: Optional[date] = None
    price: Optional[float] = None
    condition: str = "good"
    warranty_until: Optional[date] = None
    serial_no: Optional[str] = None
    photo: Optional[str] = None
    note: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    branch_id: Optional[int] = None
    room_id: Optional[int] = None
    responsible_id: Optional[int] = None
    purchased_on: Optional[date] = None
    price: Optional[float] = None
    condition: Optional[str] = None
    warranty_until: Optional[date] = None
    serial_no: Optional[str] = None
    photo: Optional[str] = None
    note: Optional[str] = None


class RepairCreate(BaseModel):
    date: Optional[_dt.date] = None
    cost: Optional[float] = 0
    vendor: Optional[str] = None
    note: Optional[str] = None


class ConsumableCreate(BaseModel):
    name: str
    kind: str = "other"
    branch_id: Optional[int] = None
    qty: float = 0
    min_qty: float = 0
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    note: Optional[str] = None


class ConsumableUpdate(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    branch_id: Optional[int] = None
    min_qty: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None
    note: Optional[str] = None


class StockMoveCreate(BaseModel):
    qty: float
    reason: str = "out"
    note: Optional[str] = None


class PurchaseClose(BaseModel):
    status: str = "done"          # done | ordered | cancelled
    qty: Optional[float] = None


# --------------------------------------------------- Ustoz ish haqi
class TeacherPaymentCreate(BaseModel):
    amount: float
    kind: str = "salary"          # advance | salary | correction
    period: Optional[str] = None  # "YYYY-MM"
    date: Optional[_dt.date] = None
    method: Optional[str] = None
    note: Optional[str] = None


# ------------------------------------------------------- Qarzdorlar
class DebtorContactCreate(BaseModel):
    student_id: int
    result: str = "promised"
    promised_date: Optional[_dt.date] = None
    promised_amount: Optional[float] = None
    note: Optional[str] = None


# ------------------------------------------------------- Ruxsatlar
class PermissionUpdate(BaseModel):
    role: str
    resource: str
    action: str
    allowed: bool


class PermissionReset(BaseModel):
    role: Optional[str] = None


# ---------------------------------------------------- Ketish sababi
class LeaveReasonCreate(BaseModel):
    reason: str
    note: Optional[str] = None


# ----------------------------------------------- Xodimlar davomati
class StaffAttendanceCreate(BaseModel):
    user_id: int
    date: Optional[_dt.date] = None
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    note: Optional[str] = None


# --------------------------------------------------------- NPS
class RatingCreate(BaseModel):
    teacher_id: int
    score: int
    source: str = "student"
    student_id: Optional[int] = None
    comment: Optional[str] = None


# ------------------------------------------------------ Xabarnomalar
class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    channel: Optional[str] = None
    active: Optional[bool] = None
    days_before: Optional[int] = None


class NotifyStatus(BaseModel):
    status: str


class NotifyCreate(BaseModel):
    body: str
    title: Optional[str] = None
    kind: Optional[str] = "new_course"
    channel: str = "telegram"
    course: Optional[str] = None
    student_ids: Optional[List[int]] = None
    segment: Optional[str] = None


# --------------------------------------------------------- Referral
class ReferralCreate(BaseModel):
    student_id: int              # kim keldi (do'sti)
    referrer_student_id: int     # kim olib keldi


# ------------------------------------------------------- Coin do'koni
class RewardDecision(BaseModel):
    give: bool = True
    note: Optional[str] = None


class LinkAccount(BaseModel):
    username: str
    password: str


# ---------- Gamification ----------
class XpAward(BaseModel):
    student_id: int
    event_code: str
    amount: Optional[float] = None
    reason: Optional[str] = None
    lesson_id: Optional[int] = None


class XpBulkAward(BaseModel):
    student_ids: List[int]
    event_code: str
    reason: Optional[str] = None
    lesson_id: Optional[int] = None


class XpReverse(BaseModel):
    reason: str


class XpRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    default_xp: Optional[int] = None
    default_coin: Optional[int] = None
    maximum_per_lesson: Optional[int] = None
    maximum_per_day: Optional[int] = None
    maximum_per_week: Optional[int] = None
    maximum_per_month: Optional[int] = None
    mode: Optional[str] = None
    requires_approval: Optional[bool] = None
    allowed_roles: Optional[str] = None
    is_active: Optional[bool] = None


class LeagueUpdate(BaseModel):
    name: Optional[str] = None
    minimum_xp: Optional[int] = None
    maximum_xp: Optional[int] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    reward_coin: Optional[int] = None
    is_active: Optional[bool] = None


class SeasonCreate(BaseModel):
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    note: Optional[str] = None


class CertAward(BaseModel):
    student_id: int
    kind: str                      # cefr | ielts
    event_code: str
    cert_no: Optional[str] = None
    reason: Optional[str] = None
    mode: Optional[str] = None     # diff | full


class ApprovalDecision(BaseModel):
    approve: bool
    note: Optional[str] = None


class FraudReview(BaseModel):
    status: str
    note: Optional[str] = None


# ---------- Dars baholash ----------
class ScoreItem(BaseModel):
    criterion_id: int
    fact: float = 0
    note: Optional[str] = None


class ObservationCreate(BaseModel):
    rubric_key: str
    target_type: str = "teacher"        # teacher | candidate
    # before = o'z holicha, coached = tushuntirilgandan keyin
    stage: Optional[str] = None
    teacher_id: Optional[int] = None
    candidate_id: Optional[int] = None
    group_id: Optional[int] = None
    date: Optional[_dt.date] = None
    scores: List[ScoreItem] = []
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    note: Optional[str] = None


class CriterionUpdate(BaseModel):
    text: Optional[str] = None
    points: Optional[float] = None
    order_no: Optional[int] = None
    is_active: Optional[bool] = None


class CriterionCreate(BaseModel):
    rubric_key: str
    text: str
    points: float = 1


# ---------- SMM: kontent ----------
class ContentCreate(BaseModel):
    title: str
    platform: Optional[str] = None
    fmt: Optional[str] = None
    pillar: Optional[str] = None
    goal: Optional[str] = None
    funnel: Optional[str] = None
    audience: Optional[str] = None
    branch_id: Optional[int] = None
    course: Optional[str] = None
    campaign_id: Optional[int] = None
    parent_id: Optional[int] = None
    planned_date: Optional[_dt.date] = None
    planned_time: Optional[str] = None
    deadline: Optional[_dt.date] = None
    owner_id: Optional[int] = None
    priority: Optional[str] = None
    needs_consent: Optional[bool] = None
    note: Optional[str] = None


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    platform: Optional[str] = None
    fmt: Optional[str] = None
    pillar: Optional[str] = None
    goal: Optional[str] = None
    funnel: Optional[str] = None
    audience: Optional[str] = None
    branch_id: Optional[int] = None
    course: Optional[str] = None
    campaign_id: Optional[int] = None
    planned_time: Optional[str] = None
    deadline: Optional[_dt.date] = None
    owner_id: Optional[int] = None
    copywriter_id: Optional[int] = None
    designer_id: Optional[int] = None
    videographer_id: Optional[int] = None
    editor_id: Optional[int] = None
    priority: Optional[str] = None
    problem: Optional[str] = None
    message: Optional[str] = None
    hook: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[str] = None
    props: Optional[str] = None
    duration: Optional[str] = None
    music: Optional[str] = None
    design_format: Optional[str] = None
    cta: Optional[str] = None
    references: Optional[str] = None
    script: Optional[str] = None
    caption: Optional[str] = None
    caption_ru: Optional[str] = None
    caption_en: Optional[str] = None
    hashtags: Optional[str] = None
    story_text: Optional[str] = None
    on_video_text: Optional[str] = None
    utm: Optional[str] = None
    short_link: Optional[str] = None
    promo_code: Optional[str] = None
    needs_consent: Optional[bool] = None
    consent_ok: Optional[bool] = None
    note: Optional[str] = None


class ContentStatus(BaseModel):
    status: str
    note: Optional[str] = None


class ContentMoveIn(BaseModel):
    planned_date: _dt.date
    reason: str


class ContentPublish(BaseModel):
    post_url: str
    post_external_id: Optional[str] = None
    screenshot: Optional[str] = None
    published_at: Optional[_dt.datetime] = None


class ApprovalIn(BaseModel):
    decision: str
    comment: Optional[str] = None
    quote: Optional[str] = None


class ShotIn(BaseModel):
    text: str


class ShotState(BaseModel):
    state: str
    note: Optional[str] = None


class IdeaCreate(BaseModel):
    title: str
    description: Optional[str] = None
    pillar: Optional[str] = None
    platform: Optional[str] = None
    fmt: Optional[str] = None
    course: Optional[str] = None
    branch_id: Optional[int] = None
    audience: Optional[str] = None
    reference: Optional[str] = None
    priority: Optional[str] = None


class IdeaStatus(BaseModel):
    status: str
    note: Optional[str] = None


class RequestCreate(BaseModel):
    branch_id: Optional[int] = None
    course: Optional[str] = None
    goal: Optional[str] = None
    offer: Optional[str] = None
    group_time: Optional[str] = None
    teacher_id: Optional[int] = None
    students_needed: Optional[int] = None
    start_date: Optional[_dt.date] = None
    deadline: Optional[_dt.date] = None
    platforms: Optional[str] = None
    approved_price: Optional[float] = None
    cta: Optional[str] = None
    sales_user_id: Optional[int] = None


class RequestDecision(BaseModel):
    status: str
    smm_note: Optional[str] = None


class MetricIn(BaseModel):
    reach: Optional[int] = None
    impressions: Optional[int] = None
    views: Optional[int] = None
    watch_time: Optional[float] = None
    completion: Optional[float] = None
    likes: Optional[int] = None
    comments: Optional[int] = None
    saves: Optional[int] = None
    shares: Optional[int] = None
    profile_visits: Optional[int] = None
    link_clicks: Optional[int] = None
    dms: Optional[int] = None


# ---------- Social inbox ----------
class MessageCreate(BaseModel):
    channel: str = "instagram"
    kind: str = "dm"
    external_id: Optional[str] = None
    author: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None
    text: Optional[str] = None
    content_id: Optional[int] = None
    campaign_id: Optional[int] = None
    branch_id: Optional[int] = None
    course: Optional[str] = None
    received_at: Optional[_dt.datetime] = None


class MessageReply(BaseModel):
    text: str
    status: Optional[str] = None


class MessageStatus(BaseModel):
    status: str
    note: Optional[str] = None


class MessageToLead(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    branch_id: Optional[int] = None
    assigned_user_id: Optional[int] = None
    note: Optional[str] = None


class ReplyTemplate(BaseModel):
    label: Optional[str] = None
    text: Optional[str] = None
    is_active: Optional[bool] = None
