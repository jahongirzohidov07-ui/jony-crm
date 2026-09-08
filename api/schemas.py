import datetime as _dt
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ---------- Branch ----------
class BranchCreate(BaseModel):
    name: str
    address: Optional[str] = None
    # HAMKOR FILIAL (2026-08-15): umumiy yig'indilarga qo'shilmaydi
    is_partner: Optional[bool] = None
    partner_note: Optional[str] = None
    owner_percent: Optional[float] = None


class BranchOut(BranchCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


# ---------- Auth ----------
class LoginRequest(BaseModel):
    username: str
    password: str
    # Eslab qolish: belgi qo'yilsa token 60 kun yashaydi (2026-08-10)
    remember: bool | None = False


class PracticeAnswerIn(BaseModel):
    skill: str
    ref: str
    answer: str


class StudentProfileIn(BaseModel):
    first_name: str
    last_name: str
    middle_name: str | None = None
    birth_date: date | None = None
    address: str | None = None
    school: str | None = None
    school_grade: str | None = None


class StudentPhotoIn(BaseModel):
    photo: str | None = None   # data:image/... yoki None (o'chirish)


class GrammarAnswerIn(BaseModel):
    question_id: int
    answer: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    branch_id: Optional[int] = None
    # Standart parol ("jonyjony") bilan kirgan XODIM — ilova darrov
    # parol almashtirishni so'raydi (2026-09-06 xavfsizlik auditi).
    must_change_password: bool = False


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
    birth_date: Optional[_dt.date] = None
    hired_date: Optional[_dt.date] = None
    # Barcha filiallari ("Markaziy, Bekobod 2") — ro'yxat uchun
    branch_ids: Optional[List[int]] = None
    # Qo'shimcha lavozimlar (2026-08-10): asosiy lavozim
    # `role` da, bu yerda esa xodim bajaradigan boshqa
    # lavozimlar. Tepadagi tanlagichdan almashtiriladi.
    extra_roles: Optional[List[str]] = None
    branches_label: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str
    branch_id: Optional[int] = None
    # Xodim ishlaydigan BARCHA filiallar — birinchisi asosiy
    branch_ids: Optional[List[int]] = None
    # Qo'shimcha lavozimlar (2026-08-10): asosiy lavozim
    # `role` da, bu yerda esa xodim bajaradigan boshqa
    # lavozimlar. Tepadagi tanlagichdan almashtiriladi.
    extra_roles: Optional[List[str]] = None
    fix_salary: Optional[float] = None
    # ---- Xodim kartasi ----
    phone: Optional[str] = None
    birth_date: Optional[_dt.date] = None
    position: Optional[str] = None
    manager_id: Optional[int] = None
    hired_date: Optional[_dt.date] = None
    photo: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    branch_id: Optional[int] = None
    branch_ids: Optional[List[int]] = None
    # Qo'shimcha lavozimlar (2026-08-10): asosiy lavozim
    # `role` da, bu yerda esa xodim bajaradigan boshqa
    # lavozimlar. Tepadagi tanlagichdan almashtiriladi.
    extra_roles: Optional[List[str]] = None
    is_active: Optional[bool] = None
    # Ishdan bo'shatish: qanday ajrashildi va sababi
    exit_type: Optional[str] = None      # green | neutral | red
    exit_reason: Optional[str] = None
    password: Optional[str] = None
    fix_salary: Optional[float] = None
    phone: Optional[str] = None
    birth_date: Optional[_dt.date] = None
    position: Optional[str] = None
    manager_id: Optional[int] = None
    hired_date: Optional[_dt.date] = None
    photo: Optional[str] = None


# ---------- Teacher ----------
class TeacherCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    subject: Optional[str] = None
    branch_id: Optional[int] = None
    # Ishga kirgan sana - retention hisoboti shundan boshlab sanaydi.
    hired_date: Optional[_dt.date] = None
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
    birth_date: Optional[_dt.date] = None
    skill_score: Optional[float] = None
    support_months: Optional[float] = None
    # Ustoz ishlaydigan BARCHA filiallar (2-3 filialda ishlashi mumkin).
    # Berilsa: birinchisi asosiy (branch_id), qolgani teacher_branches da.
    branch_ids: Optional[List[int]] = None


class TeacherOut(TeacherCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    branch: Optional[BranchOut] = None
    left_date: Optional[_dt.date] = None
    grade_since: Optional[date] = None
    remediation_until: Optional[date] = None
    remediation_reason: Optional[str] = None
    # Tizimga kirish hisobi bor-yo'qligi ro'yxatda ko'rinishi uchun
    user_id: Optional[int] = None
    login: Optional[str] = None
    # Barcha filiallari nomlari ("Markaziy, Bekobod 2") — ro'yxat uchun
    branches_label: Optional[str] = None
    # "support" — yordamchi o'qituvchi (bog'langan hisob roli bo'yicha),
    # aks holda "teacher". Ro'yxatda alohida bo'limda ko'rsatiladi.
    kind: Optional[str] = None
    # Support darajasi (Volontyor/Junior/Middle/Senior) — faqat
    # kind="support" bo'lganda to'ldiriladi
    staff_grade: Optional[str] = None
    staff_grade_label: Optional[str] = None


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
    # STAVKA QAYSI OYDAN AMAL QILADI (2026-09-03). Bo'sh bo'lsa —
    # joriy oyning 1-kunidan. O'tgan oylar eski stavkada qoladi.
    effective_from: Optional[_dt.date] = None


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
    end_date: Optional[_dt.date] = None
    start_date: Optional[_dt.date] = None
    lesson_time: Optional[str] = None
    lesson_days: Optional[str] = None
    monthly_fee: float = 0
    lesson_price: float = 40000
    # Qaysi KURS (2026-08-15) — narx shundan olinadi
    course_id: Optional[int] = None
    price_manual: Optional[bool] = None
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
    end_date: Optional[_dt.date] = None
    start_date: Optional[_dt.date] = None
    lesson_time: Optional[str] = None
    lesson_days: Optional[str] = None
    monthly_fee: Optional[float] = None
    lesson_price: Optional[float] = None
    standard_lessons_per_month: Optional[int] = None
    teacher_rate_per_student: Optional[float] = None
    # Qaysi KURS (2026-08-15) — narx shundan olinadi
    course_id: Optional[int] = None
    price_manual: Optional[bool] = None


class MyGroupEdit(BaseModel):
    """USTOZ o'z guruhida o'zgartira oladigan YAGONA maydonlar
    (2026-09-01, Jahongir: "ustozlar o'zlarini guruhlarini edit
    qilishda guruh nomini o'zgartirish darajasini va vaqtini
    o'zgartirish xonasini ozgartirish huquqi bolsin").

    Ro'yxat ATAYLAB tor: narx, ustoz stavkasi, ustozning o'zi, filial,
    dars kunlari va boshqalar bu yerda umuman yo'q. Shuning uchun
    ustoz qo'lda so'rov yasab yuborsa ham, o'sha maydonlar Pydantic
    darajasida tashlab yuboriladi — server ularni ko'rmaydi."""
    name: Optional[str] = None
    level: Optional[str] = None
    lesson_time: Optional[str] = None
    room_id: Optional[int] = None


class GroupOut(GroupCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    public_id: Optional[str] = None
    teacher: Optional[TeacherOut] = None
    branch: Optional[BranchOut] = None
    student_count: int = 0
    # MUZLATILGANLAR (2026-09-08): student_count ga kirmaydi, lekin
    # guruhda turishadi va guruhni o'chirishga to'sqinlik qiladi.
    frozen_count: int = 0
    # 1 — stavka qo'lda kiritilgan (darajadan avtomat emas)
    rate_manual: Optional[int] = None
    # Guruhga biriktirilgan support ustoz(lar) nomi — ro'yxatda ko'rinadi
    support_label: Optional[str] = None


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
    # O'TGAN SANA bilan kiritish (2026-08-12, Jahongir: "asoschiga va
    # moliyachiga eski sana bilan to'lov kirgizish funksiyasi"). Faqat
    # asoschi va moliya direktori uchun; bo'sh bo'lsa - bugungi kun.
    date: Optional[_dt.date] = None
    # DUBL HIMOYASI (2026-08-14). Brauzer forma ochilganda bitta
    # tasodifiy kalit yaratadi va shu kalit bilan yuboradi. Tugma ikki
    # marta bosilsa yoki internet uzilib qayta yuborilsa ham server
    # ikkinchi yozuv OCHMAYDI — birinchisini qaytaradi.
    client_key: Optional[str] = None
    # Bir xil o'quvchiga bir xil summa 2 daqiqa ichida qayta
    # kiritilayotgan bo'lsa server ogohlantiradi. Xodim "ha, bu
    # boshqa to'lov" desa — force=true bilan qayta yuboriladi.
    force: bool = False


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
    updated_at: Optional[datetime] = None
    # Haqiqiy kiritilish vaqti (eski sana bilan kiritilganda
    # created_at dan farq qiladi).
    entered_at: Optional[datetime] = None


# ---------- Student ----------
class StudentCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    parent_phone: Optional[str] = None
    birth_date: Optional[_dt.date] = None
    enrolled_date: Optional[_dt.date] = None
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
    # Parallel tahrir himoyasi: klient o'zi ko'rgan versiya vaqtini
    # yuboradi; serverdagisi boshqa bo'lsa 409 qaytadi.
    expected_updated_at: Optional[str] = None


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # O'quvchi ilovadan o'zi kiritadigan qismlar (2026-08-10)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    photo: Optional[str] = None
    address: Optional[str] = None
    school: Optional[str] = None
    school_grade: Optional[str] = None
    frozen_until: Optional[_dt.date] = None
    frozen_note: Optional[str] = None
    id: int
    public_id: Optional[str] = None
    full_name: str
    phone: Optional[str] = None
    parent_phone: Optional[str] = None
    birth_date: Optional[_dt.date] = None
    enrolled_date: Optional[_dt.date] = None
    left_date: Optional[_dt.date] = None
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
    # Telefon dublikat ogohlantirishidan keyin "baribir qo'shish"
    force: Optional[bool] = False


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
    enrolled_date: Optional[_dt.date] = None
    # Bir xil telefonli o'quvchi bazada bo'lsa server ogohlantiradi.
    # Haqiqatan boshqa odam bo'lsa (aka-uka) shu belgi bilan tasdiqlanadi.
    force: bool = False


class ExpenseCreate(BaseModel):
    date: date
    category: str = "other"
    amount: float
    note: Optional[str] = None
    branch_id: Optional[int] = None
    channel: Optional[str] = None
    method: Optional[str] = "cash"
    # OYLIK yo'li (2026-08-12, Jahongir): xodim tanlanadi. Ustoz
    # bo'lsa teacher_id, ma'muriy xodim bo'lsa staff_user_id.
    teacher_id: Optional[int] = None
    staff_user_id: Optional[int] = None
    period: Optional[str] = None          # "YYYY-MM" — qaysi oy uchun
    # SONI va mahsulot (kitob/marker...): ombor qoldig'i shu bilan
    # to'ldiriladi.
    qty: Optional[float] = None
    consumable_id: Optional[int] = None
    # Ro'yxatda yo'q kitob nomi — yangi mahsulot ochiladi
    new_item_name: Optional[str] = None


class ExpenseUpdate(BaseModel):
    date: Optional[_dt.date] = None
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
    staff_user_id: Optional[int] = None
    qty: Optional[float] = None
    consumable_id: Optional[int] = None


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
    # Kech keldi: present=True bilan birga yuboriladi. Bazada
    # present=2 bo'lib saqlanadi — davomat foizida "kelgan" sanaladi,
    # jadvalda esa alohida (soat belgisi) ko'rinadi.
    late: Optional[bool] = None
    # Belgini butunlay olib tashlash. Olib tashlangan o'quvchi
    # oylikka kirmaydi — "belgilanmagan" holatga qaytadi.
    remove: Optional[bool] = None
    # 0 = bajarmadi, 1 = bajardi, 2 = qisman, None = tekshirilmadi
    homework: Optional[int] = None


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
    # "transferred" satrlar uchun: qayerga/qachon ketgani izohi
    note: Optional[str] = None


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
    # Uy vazifasi: "lessonId:studentId" -> 0/1/2. Davomat bilan bir
    # jadvalda belgilanadi, aks holda hech qachon to'ldirilmaydi.
    homework: dict = {}
    # Dars ko'chirish: kvota, ruxsat va allaqachon ko'chirilganlar.
    # Sana sarlavhasidagi menyu shu ma'lumot bilan chiziladi.
    reschedule: Optional[dict] = None


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
    date: Optional[_dt.date] = None
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
    # Retake (qayta topshirish) - birinchi ball bilan yonma-yon
    retake_score: Optional[float] = None
    retake_band: Optional[float] = None
    retake_percent: Optional[float] = None
    retake_at: Optional[date] = None
    # 0 = umumiy o'rtacha/coinga kirmagan (imtihon kuni yangi kelgan)
    counted: Optional[int] = None


class ExamRetakeIn(BaseModel):
    student_id: int
    score: Optional[float] = None
    band: Optional[float] = None
    remove: bool = False


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
    # Coinga CHEGIRMA (2026-08-15): kind="discount" bo'lsa sovg'a
    # emas, o'quv to'loviga chegirma sotiladi.
    kind: Optional[str] = "gift"
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    image: Optional[str] = None


class RewardUpdate(BaseModel):
    name: Optional[str] = None
    cost: Optional[int] = None
    value_som: Optional[float] = None
    stock: Optional[int] = None
    active: Optional[bool] = None
    branch_id: Optional[int] = None
    kind: Optional[str] = None
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    image: Optional[str] = None


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
    kind: Optional[str] = "gift"
    discount_percent: Optional[float] = None
    discount_amount: Optional[float] = None
    image: Optional[str] = None


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

    ESKI TO'LOV yig'ish bonusi FILIAL ko'rsatkichi bo'yicha — qarz
    yig'ish jamoaviy ish, bir filialdagi ikkala admin ham to'liq
    bonusni oladi.

    YANGI MIJOZ bonusi esa SHAXSIY (2026-08-30): kim birinchi
    to'lovni qabul qilgan bo'lsa — o'shaniki."""
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

    # YANGI MIJOZ — SHAXSIY (2026-08-30, Jahongir: "yangi to'lovlar bu
    # individual KPI bo'ladi ... kim yangi to'lov qildirsa o'ziga
    # hisoblanishi kerak"). Quyidagi ikki maydon FAQAT shu adminning
    # o'zi qabul qilgan yangi mijozlari.
    new_clients: int = 0       # birinchi marta to'lagan o'quvchilar
    new_client_revenue: float = 0
    # Filialda JAMI nechta yangi mijoz bo'lgani — solishtirish uchun.
    # Bonusga ta'sir qilmaydi.
    branch_new_clients: int = 0
    branch_new_revenue: float = 0
    # Hech bir adminga tegishli bo'lmaganlari (asoschi/moliyachi
    # qabul qilgan) — yo'qolib ketmasin, ko'rinib tursin.
    unassigned_new_clients: int = 0
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


class CourseIn(BaseModel):
    """Kurs (2026-08-15): dars davomiyligi va bitta dars narxi."""
    name: Optional[str] = None
    branch_id: Optional[int] = None
    subject: Optional[str] = None
    level: Optional[str] = None
    lesson_minutes: Optional[int] = None
    lesson_price: Optional[float] = None
    lessons_per_month: Optional[int] = None
    active: Optional[bool] = None
    note: Optional[str] = None


class CoursePriceIn(BaseModel):
    """Narxni SANADAN boshlab o'zgartirish (sentabrdan oshirish)."""
    from_date: _dt.date
    lesson_price: float
    lessons_per_month: Optional[int] = None
    note: Optional[str] = None
    # Hozirgi FAOL o'quvchilarga eski narx qolsinmi (2026-08-15)
    keep_old_for_active: Optional[bool] = True


class PriceLockIn(BaseModel):
    """Eski narx qulfi: price berilsa qo'yiladi, bo'sh bo'lsa ochiladi."""
    price: Optional[float] = None
    note: Optional[str] = None


class CoinSetIn(BaseModel):
    """Coin balansini to'g'ri songa keltirish (faqat asoschi)."""
    balance: int
    note: Optional[str] = None


class CandidateCreate(BaseModel):
    full_name: str
    phone: Optional[str] = None
    vacancy_id: Optional[int] = None
    stage: str = "applied"
    source: str = "other"
    branch_id: Optional[int] = None
    note: Optional[str] = None
    # Qaysi ishga kelgani va (ustoz bo'lsa) qaysi fandan — 2026-08-15
    position: Optional[str] = None
    subject: Optional[str] = None
    # Ariza savollari — qo'lda kiritishda ham so'raladi (2026-08-15)
    address: Optional[str] = None
    birth_date: Optional[str] = None
    education: Optional[str] = None
    marital: Optional[str] = None
    socials: Optional[str] = None
    work_duration: Optional[str] = None
    workplaces: Optional[str] = None
    experience_years: Optional[float] = None


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
    # Ona tili (2026-08-16) — til darajasi ro'yxati faqat ingliz
    # tiliga mo'ljallangan edi.
    native_language: Optional[str] = None
    expected_salary: Optional[float] = None
    trial_score: Optional[float] = None
    interview_score: Optional[float] = None
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    reference_note: Optional[str] = None
    decision: Optional[str] = None
    # Qaysi ishga kelgani va (ustoz bo'lsa) qaysi fandan — 2026-08-15
    position: Optional[str] = None
    subject: Optional[str] = None
    address: Optional[str] = None
    birth_date_text: Optional[str] = None
    education: Optional[str] = None
    marital: Optional[str] = None
    socials: Optional[str] = None
    work_duration: Optional[str] = None


# ---------- Ijtimoiy tarmoq ----------
class SocialManual(BaseModel):
    platform: str
    followers: int


# ---------- Guruhdagi o'quvchi ustidagi amallar ----------
class StudentGroupMove(BaseModel):
    """Boshqa guruhga o'tkazish. group_id None bo'lsa - guruhdan chiqariladi."""
    group_id: Optional[int] = None


# ---------- Ota-ona ----------
class FamilyLinkIn(BaseModel):
    """Ikki o'quvchini bir oila deb bog'lash (aka-uka/opa-singil)."""
    sibling_id: int
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None


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
    date: Optional[_dt.date] = None
    start_date: Optional[_dt.date] = None
    end_date: Optional[_dt.date] = None
    monthly_fee: float = 0
    discount_percent: float = 0
    status: str = "active"
    note: Optional[str] = None


class ContractUpdate(BaseModel):
    parent_id: Optional[int] = None
    group_id: Optional[int] = None
    date: Optional[_dt.date] = None
    start_date: Optional[_dt.date] = None
    end_date: Optional[_dt.date] = None
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
    due_date: Optional[_dt.date] = None


class RiskTaskUpdate(BaseModel):
    title: Optional[str] = None
    assigned_user_id: Optional[int] = None
    due_date: Optional[_dt.date] = None
    status: Optional[str] = None
    result: Optional[str] = None


# ---------- Ota-ona suhbati / sertifikat ----------
class ParentTalkCreate(BaseModel):
    date: Optional[_dt.date] = None
    channel: str = "phone"
    topic: str
    summary: Optional[str] = None
    outcome: Optional[str] = None


class CertificateCreate(BaseModel):
    kind: str = "internal"
    level: Optional[str] = None
    score: Optional[float] = None
    date: Optional[_dt.date] = None
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
    date: Optional[_dt.date] = None
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
    due_date: Optional[_dt.date] = None


class SupportPlanUpdate(BaseModel):
    issue: Optional[str] = None
    plan: Optional[str] = None
    due_date: Optional[_dt.date] = None
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
    start_date: Optional[_dt.date] = None
    end_date: Optional[_dt.date] = None
    referrer_student_id: Optional[int] = None
    staff_user_id: Optional[int] = None
    # Individual (yashirin) - o'quvchi/ota-onaga ko'rinmaydi
    hidden: Optional[bool] = False


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
    start_date: Optional[_dt.date] = None
    end_date: Optional[_dt.date] = None
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
    # 2026-08-27: kontent-plan (Excel) ustunlari
    hook: Optional[str] = None
    message: Optional[str] = None
    proof: Optional[str] = None
    cta: Optional[str] = None
    shoot_date: Optional[_dt.date] = None
    kpi_target: Optional[str] = None
    series: Optional[str] = None
    script: Optional[str] = None


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
    # 2026-08-27: kontent-plan ustunlari. Bular sxemada yo'q edi va
    # PUT so'rovi 200 qaytarardi-yu, maydonlarni JIMGINA tashlab
    # yuborardi — test aynan shuni tutdi.
    proof: Optional[str] = None
    shoot_date: Optional[_dt.date] = None
    kpi_target: Optional[str] = None
    conclusion: Optional[str] = None
    series: Optional[str] = None
    planned_date: Optional[_dt.date] = None
    # Havola: SMM post joylagach shu yerga qo'yadi va natija
    # avtomat olinadi.
    post_url: Optional[str] = None


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


# ---- Brend kitob ----
class BrandRuleIn(BaseModel):
    section: str
    key: Optional[str] = None
    title: str
    value: Optional[str] = None
    note: Optional[str] = None
    kind: Optional[str] = None
    position: Optional[int] = 0


class BrandRulePatch(BaseModel):
    title: Optional[str] = None
    value: Optional[str] = None
    note: Optional[str] = None
    kind: Optional[str] = None
    position: Optional[int] = None
    is_active: Optional[int] = None


class BrandCheckIn(BaseModel):
    key: str
    ok: bool
    note: Optional[str] = None


# ---- Bilimlar bazasi ----
class KbIn(BaseModel):
    title: str
    category: Optional[str] = "process"
    body: Optional[str] = None
    tags: Optional[str] = None
    is_pinned: Optional[int] = 0


class KbPatch(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    body: Optional[str] = None
    tags: Optional[str] = None
    is_pinned: Optional[int] = None
    is_active: Optional[int] = None


# ---- Media kutubxona ----
class MediaIn(BaseModel):
    name: str
    kind: Optional[str] = "photo"
    url: Optional[str] = None
    attachment_id: Optional[int] = None
    branch_id: Optional[int] = None
    course: Optional[str] = None
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None
    event: Optional[str] = None
    taken_on: Optional[date] = None
    author: Optional[str] = None
    tags: Optional[str] = None
    consent: Optional[str] = "pending"
    consent_until: Optional[date] = None
    can_download: Optional[int] = 1


class MediaPatch(BaseModel):
    name: Optional[str] = None
    kind: Optional[str] = None
    url: Optional[str] = None
    branch_id: Optional[int] = None
    course: Optional[str] = None
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None
    event: Optional[str] = None
    taken_on: Optional[date] = None
    author: Optional[str] = None
    tags: Optional[str] = None
    consent: Optional[str] = None
    consent_until: Optional[date] = None
    can_download: Optional[int] = None


# ---- Hisobot ----
class ReportIn(BaseModel):
    period: Optional[str] = "month"
    start_date: Optional[_dt.date] = None
    end_date: Optional[_dt.date] = None
    branch_id: Optional[int] = None
    summary: Optional[str] = None


# ---------- HR: bo'lim va lavozim ----------
class DepartmentIn(BaseModel):
    name: str
    key: Optional[str] = None
    description: Optional[str] = None
    head_id: Optional[int] = None
    position: Optional[int] = 0


class DepartmentPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    head_id: Optional[int] = None
    position: Optional[int] = None
    is_active: Optional[int] = None


class PositionIn(BaseModel):
    name: str
    key: Optional[str] = None
    department_id: Optional[int] = None
    system_role: Optional[str] = None
    probation_months: Optional[int] = 2
    trial_required: Optional[int] = 0
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    description: Optional[str] = None
    requirements: Optional[str] = None


class PositionPatch(BaseModel):
    name: Optional[str] = None
    department_id: Optional[int] = None
    system_role: Optional[str] = None
    probation_months: Optional[int] = None
    trial_required: Optional[int] = None
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    is_active: Optional[int] = None


# ---------- HR: shtat rejasi ----------
class PlanIn(BaseModel):
    year: int
    month: Optional[int] = None
    quarter: Optional[int] = None
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    approved_headcount: Optional[int] = 0
    planned_hires: Optional[int] = 0
    expected_leaves: Optional[int] = 0
    expected_groups: Optional[int] = 0
    budgeted_salary: Optional[float] = None
    note: Optional[str] = None


class PlanPatch(BaseModel):
    approved_headcount: Optional[int] = None
    planned_hires: Optional[int] = None
    expected_leaves: Optional[int] = None
    expected_groups: Optional[int] = None
    budgeted_salary: Optional[float] = None
    note: Optional[str] = None
    status: Optional[str] = None


# ---------- HR: xodim so'rovi ----------
class StaffRequestIn(BaseModel):
    branch_id: Optional[int] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    headcount: Optional[int] = 1
    employment_type: Optional[str] = "full"
    work_schedule: Optional[str] = None
    needed_from: Optional[date] = None
    reason: Optional[str] = None
    replacing_user_id: Optional[int] = None
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    requirements: Optional[str] = None
    certificates: Optional[str] = None
    experience_years: Optional[float] = None
    duties: Optional[str] = None
    kpi_note: Optional[str] = None
    priority: Optional[str] = "normal"


class StaffRequestPatch(StaffRequestIn):
    pass


class RequestApprovalIn(BaseModel):
    note: Optional[str] = None


class RequestRejectIn(BaseModel):
    reason: str
    note: Optional[str] = None


# ---------- HR: vakansiya ----------
class VacancyHrIn(BaseModel):
    title: Optional[str] = None
    position_id: Optional[int] = None
    department_id: Optional[int] = None
    branch_id: Optional[int] = None
    headcount: Optional[int] = None
    hiring_manager_id: Optional[int] = None
    recruiter_id: Optional[int] = None
    employment_type: Optional[str] = None
    work_schedule: Optional[str] = None
    salary_from: Optional[float] = None
    salary_to: Optional[float] = None
    description: Optional[str] = None
    duties: Optional[str] = None
    requirements: Optional[str] = None
    experience_years: Optional[float] = None
    education: Optional[str] = None
    language_level: Optional[str] = None
    certificates: Optional[str] = None
    probation_months: Optional[int] = None
    kpi_note: Optional[str] = None
    priority: Optional[str] = None
    target_close: Optional[date] = None


class VacancyStatusIn(BaseModel):
    status: str
    close_reason: Optional[str] = None
    note: Optional[str] = None


# ---------- Dars ko'chirish ----------
class GroupRescheduleIn(BaseModel):
    """Davomat jadvalidan to'g'ridan-to'g'ri ko'chirish."""
    from_date: date
    to_date: date
    reason: Optional[str] = None
    note: Optional[str] = None


class RescheduleIn(BaseModel):
    group_id: int
    from_date: date
    to_date: date
    from_time: Optional[str] = None
    to_time: Optional[str] = None
    reason: Optional[str] = None
    note: Optional[str] = None


class RescheduleDecision(BaseModel):
    decision: str            # approved | rejected
    note: Optional[str] = None


# ---------- O'rinbosar ustoz ----------
class SubstitutionIn(BaseModel):
    group_id: int
    lesson_date: date
    lesson_time: Optional[str] = None
    substitute_teacher_id: Optional[int] = None
    reason: Optional[str] = None
    note: Optional[str] = None


class SubstitutionDecision(BaseModel):
    decision: str            # accepted | declined | cancelled
    note: Optional[str] = None


# ---------- Kitob buyurtmasi ----------
class BookItemIn(BaseModel):
    title: str
    qty: int = 1
    level: Optional[str] = None
    consumable_id: Optional[int] = None
    note: Optional[str] = None


class BookOrderIn(BaseModel):
    items: List[BookItemIn]
    group_id: Optional[int] = None
    needed_by: Optional[date] = None
    urgency: Optional[str] = "normal"
    note: Optional[str] = None


class BookOrderDecision(BaseModel):
    status: str
    note: Optional[str] = None


# ---------- Imtihon buyurtmasi ----------
class ExamOrderIn(BaseModel):
    group_id: int
    date: date
    time: Optional[str] = None
    kind: str = "unit"
    unit_no: Optional[int] = None
    note: Optional[str] = None


class ExamOrderDecision(BaseModel):
    note: Optional[str] = None
    reason: Optional[str] = None


# ---------- HR Faza 2B: ATS ----------
class ApplicationIn(BaseModel):
    """Yangi ariza. Nomzod mavjud bo'lsa candidate_id, yangi bo'lsa
    ismi va telefoni."""
    candidate_id: Optional[int] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    vacancy_id: Optional[int] = None
    branch_id: Optional[int] = None
    source: Optional[str] = None
    note: Optional[str] = None
    # Dublikat topilsa ham baribir ochish
    force: bool = False


class ApplicationMove(BaseModel):
    stage: str
    reason: Optional[str] = None
    note: Optional[str] = None
    pool: Optional[bool] = None


class InterviewIn(BaseModel):
    application_id: int
    kind: str = "hr"
    date: date
    time: Optional[str] = None
    minutes: Optional[int] = None
    place: Optional[str] = None
    room_id: Optional[int] = None
    interviewer_id: Optional[int] = None
    note: Optional[str] = None


class CandidateSchedule(BaseModel):
    """Nomzod bosqichini o'zgartirish + suhbat/sinov darsini
    kalendarga qo'yish — bitta harakatda (2026-08-16)."""
    stage: str                       # interview | demo
    date: date
    time: Optional[str] = None
    kind: Optional[str] = None       # bo'sh bo'lsa bosqichdan olinadi
    minutes: Optional[int] = None
    place: Optional[str] = None
    interviewer_id: Optional[int] = None
    note: Optional[str] = None


class InterviewStatusIn(BaseModel):
    status: str
    note: Optional[str] = None


class ScorecardIn(BaseModel):
    application_id: int
    interview_id: Optional[int] = None
    scores: dict = {}
    recommendation: Optional[str] = None
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    note: Optional[str] = None


class OfferIn(BaseModel):
    application_id: int
    position: Optional[str] = None
    salary: Optional[float] = None
    salary_note: Optional[str] = None
    start_date: Optional[_dt.date] = None
    probation_months: Optional[int] = None
    terms: Optional[str] = None


class OfferAction(BaseModel):
    action: str          # submit | approve | reject | send | accept |
    #                      decline | withdraw
    note: Optional[str] = None


# ---------- HR Faza 3-5 ----------
class DocumentIn(BaseModel):
    user_id: int
    kind: str
    title: Optional[str] = None
    number: Optional[str] = None
    issued_on: Optional[date] = None
    expires_on: Optional[date] = None
    note: Optional[str] = None


class ProbationIn(BaseModel):
    user_id: int
    month_no: int = 1
    decision: str
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    note: Optional[str] = None


class LeaveIn(BaseModel):
    user_id: Optional[int] = None      # bo'sh bo'lsa — o'zi uchun
    kind: str
    date_from: date
    date_to: date
    reason: Optional[str] = None
    replacement_teacher_id: Optional[int] = None
    replacement_note: Optional[str] = None


class LeaveDecision(BaseModel):
    decision: str                      # approved | rejected
    note: Optional[str] = None


class ReviewIn(BaseModel):
    user_id: int
    period: str
    scores: dict = {}
    strengths: Optional[str] = None
    to_improve: Optional[str] = None
    goals: Optional[str] = None
    finalize: bool = False


class OneOnOneIn(BaseModel):
    user_id: int
    date: Optional[_dt.date] = None
    privacy: str = "open"
    notes: Optional[str] = None
    agreements: Optional[str] = None


class PipIn(BaseModel):
    user_id: int
    reason: str
    goals: str
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class PipClose(BaseModel):
    status: str                        # passed | failed
    note: Optional[str] = None


class DisciplineIn(BaseModel):
    user_id: int
    kind: str
    reason: str
    date: Optional[_dt.date] = None


class RecognitionIn(BaseModel):
    user_id: int
    kind: str
    reason: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[_dt.date] = None


class OffboardIn(BaseModel):
    user_id: int
    last_day: Optional[date] = None
    reason: Optional[str] = None


class OffboardUpdate(BaseModel):
    step: Optional[str] = None
    done: Optional[bool] = None
    exit_notes: Optional[str] = None
    would_return: Optional[bool] = None
    reason: Optional[str] = None


# ---------- Support teacher seansi ----------
class SupportSessionIn(BaseModel):
    group_id: int
    # DIQQAT: maydon nomi "date" tur nomi bilan to'qnashib pydantic'da
    # NoneType bo'lib qolardi — shuning uchun _dt.date orqali yoziladi
    date: Optional[_dt.date] = None    # bo'sh bo'lsa — bugun
    start_time: str                    # "14:00"
    # IKKI XIL usul (2026-08-10): support YO tugash vaqtini yozadi,
    # YO qancha soat dars o'tganini o'zi tanlaydi (1 / 1.5 / 2 / 2.5 / 3).
    # Ikkinchisi qulayroq — telefonda hisoblab o'tirmaydi.
    end_time: Optional[str] = None     # "15:30"
    hours: Optional[float] = None      # 1 ... 3
    students_count: int
    note: Optional[str] = None


class ExamPenaltyIn(BaseModel):
    """Imtihonga jarima belgilash — bo'lim boshliqlari uchun."""
    lc_up: bool = False
    coin: bool = False
    delay_hours: float = 0
    note: Optional[str] = None


class ExaminerAdjustIn(BaseModel):
    """Examinerdan qo'lda ball ayirish."""
    user_id: int
    points: float
    reason: str
    date: Optional[_dt.date] = None


class PlanItemIn(BaseModel):
    metric: str
    month: int
    value: float


class PlanSaveIn(BaseModel):
    items: List[PlanItemIn]


class BudgetItemIn(BaseModel):
    month: int
    kind: str                      # income | expense
    category: Optional[str] = None
    branch_id: Optional[int] = None
    amount: float


class BudgetSaveIn(BaseModel):
    items: List[BudgetItemIn]


class PaymentDueIn(BaseModel):
    title: str
    kind: str = "other"
    due_day: Optional[int] = None
    date: Optional[_dt.date] = None
    amount: float
    branch_id: Optional[int] = None
    recurring: bool = True
    note: Optional[str] = None


class FreezeIn(BaseModel):
    until: _dt.date                  # qachon qaytadi — majburiy
    note: Optional[str] = None


class SupportGroupsIn(BaseModel):
    group_ids: List[int]


class HomeworkIn(BaseModel):
    student_id: int
    homework: Optional[int] = None    # 2 a'lo, 1 qisman, 0 qilmadi, None o'chirish


class ReminderIn(BaseModel):
    text: str
    remind_on: Optional[_dt.date] = None


class PaymentEditIn(BaseModel):
    amount: float                     # yangi summa (musbat son kiritiladi)
    note: Optional[str] = None
    # To'lov usulini to'g'rilash (naqd <-> plastik) - faqat kind=payment
    method: Optional[str] = None
    expected_updated_at: Optional[str] = None  # parallel tahrir himoyasi


class PaymentFixIn(BaseModel):
    """To'lovni tuzatish so'rovi (2026-08-15)."""
    kind: str = "amount"              # amount | method | note | delete
    amount: Optional[float] = None    # yangi summa (musbat son)
    method: Optional[str] = None      # yangi to'lov usuli
    note: Optional[str] = None        # yangi izoh
    reason: str                       # nima uchun — MAJBURIY


class PaymentFixDecision(BaseModel):
    note: Optional[str] = None


class ExerciseIn(BaseModel):
    """Mashq natijasi: jami savol va to'g'ri javoblar soni."""
    total: int
    correct: int
    topic: Optional[str] = None


class SupportBusyIn(BaseModel):
    """Support o'zi belgilaydigan band vaqt."""
    days: str          # "mon,wed,fri"
    start: str         # "14:00"
    end: str           # "16:00"
    note: Optional[str] = None


class RefundCreate(BaseModel):
    student_id: int
    amount: float
    reason: str


class RefundDecision(BaseModel):
    note: Optional[str] = None


class SnapshotIn(BaseModel):
    """Tarixiy o'quvchilar soni — bitta yozuv."""
    date: date
    count: int
    note: Optional[str] = None


class SnapshotBulkIn(BaseModel):
    """Ommaviy kiritish: har qatorda "sana son [izoh]"."""
    text: str


class RemoveFromGroupIn(BaseModel):
    """Guruhdan chiqarish — sabab MAJBURIY, ustozlar bilishi uchun.

    2026-08-24 (Jahongir: "ketish sababini majburiy qil"): endi
    KATEGORIYA ham majburiy — roles.LEAVE_REASONS dan biri. Erkin
    matn ("reason") izoh bo'lib qoladi; statistika kategoriyadan
    chiqadi, aks holda hamma narsa "noma'lum" bo'lib ketardi."""
    reason: str
    reason_code: Optional[str] = None
    # QAYSI KUNGACHA (2026-08-20, Jahongir: "guruhdan talabani
    # chiqarishda, sana tanlaydigan bo'lsin va masalan tanlangan
    # sanagacha hisoblanib hisobi o'zgarsin va guruhdan chiqarilsin").
    # Bo'sh bo'lsa bugungi kun.
    on_date: Optional[date] = None


class RecoverySetIn(BaseModel):
    """Asoschi favqulodda tiklash kodini o'rnatadi."""
    current_password: str
    recovery_code: str


class RecoverIn(BaseModel):
    """Parol unutilganda: login + tiklash kodi + yangi parol."""
    username: str
    recovery_code: str
    new_password: str


class TeacherImportRow(BaseModel):
    """Excel'dan (masalan, LC UP eksporti) bitta ustoz qatori."""
    full_name: str
    phone: Optional[str] = None
    birth_date: Optional[str] = None   # "YYYY-MM-DD" yoki bo'sh
    note: Optional[str] = None         # guruhlari kabi qo'shimcha
    per_student_rate: Optional[float] = None


class TeacherImportIn(BaseModel):
    rows: List[TeacherImportRow]
    branch_id: Optional[int] = None


class StudentImportRow(BaseModel):
    """Excel'dan (LC UP eksporti) bitta o'quvchi qatori."""
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    birth_date: Optional[str] = None
    status: Optional[str] = None       # "Aktiv" / "Arxiv" / ...


class StudentImportIn(BaseModel):
    rows: List[StudentImportRow]
    group_id: int


# ---------- Jony Student: lug'at o'yinlari ----------
class VocabAnswerIn(BaseModel):
    """Bitta javob. To'g'riligini SERVER hal qiladi — bu yerda faqat
    o'quvchi nima deganini yuboramiz.

    shown — faqat "To'g'ri/Xato" o'yini uchun: ekranda qaysi tarjima
    ko'rsatilgani. Server shu tarjimani bazadagi haqiqiy tarjima bilan
    solishtirib, javob to'g'ri yoki yo'qligini O'ZI hal qiladi."""
    word_id: int
    game: str
    answer: Optional[str] = None
    shown: Optional[str] = None


class VocabWordIn(BaseModel):
    word: str
    translation: str
    level: Optional[str] = None
    topic: Optional[str] = None
    example: Optional[str] = None


class VocabImportIn(BaseModel):
    words: List[VocabWordIn]
