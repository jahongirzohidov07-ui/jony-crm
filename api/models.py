from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from database import Base


class Branch(Base):
    """Filial. Jony Academy has several physical branches; every
    student/group/teacher belongs to exactly one."""
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teachers = relationship("Teacher", back_populates="branch")
    groups = relationship("Group", back_populates="branch")
    students = relationship("Student", back_populates="branch")
    users = relationship("User", back_populates="branch")


class User(Base):
    """Login accounts. role is one of roles.ALL_ROLES (Jony Academy org
    chart: administrator, branch_manager, teacher, support_teacher,
    examiner, hr_manager, smm_manager).
    branch_id is nullable - administrator/HR/SMM typically see every
    branch, while branch_manager/teacher/support_teacher/examiner are
    scoped to one."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="teacher")
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    is_active = Column(Integer, default=1)
    # Fiks oylik (so'm). Adminlar (sotuv menejeri) KPI'sida asos bo'ladi:
    # jami ish haqi = fiks + bonuslar. Faqat asoschi o'zgartira oladi.
    fix_salary = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", back_populates="users")


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)

    # Retention hisoboti uchun. hired_date - ishga kirgan sana (berilmasa
    # yaratilgan kun), left_date - ishdan ketgan sana. left_date qo'lda
    # kiritilmaydi: ustoz "ishdan ketgan" deb belgilanganda avtomatik
    # qo'yiladi, qaytib kelsa avtomatik tozalanadi.
    hired_date = Column(Date, nullable=True, default=date.today)
    left_date = Column(Date, nullable=True)
    is_active = Column(Integer, default=1)

    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", back_populates="teachers")
    groups = relationship("Group", back_populates="teacher")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    room = Column(String, nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)

    # Qaysi fan va qaysi daraja - ta'lim sifati hisoboti shu kesimda chiqadi.
    subject = Column(String, nullable=True)   # roles.SUBJECTS
    level = Column(String, nullable=True)     # roles.SUBJECT_LEVELS[subject]
    # Guruh qachon boshlangan. Yoqlama shu sanadan oldin qo'yilmaydi.
    start_date = Column(Date, nullable=True)
    # Kurs tugash sanasi - undan keyin dars kunlari avtomat yaratilmaydi.
    end_date = Column(Date, nullable=True)
    # Dars vaqti ("09:00 - 11:00") va kunlari ("mon,wed,fri") - ro'yxatda
    # ko'rinadi, jadval tuzishda qo'l keladi.
    lesson_time = Column(String, nullable=True)
    lesson_days = Column(String, nullable=True)

    monthly_fee = Column(Float, default=0)  # standart oy narxi (= lesson_price * standard_lessons_per_month), asosan ko'rsatish uchun

    # Dars-asosidagi hisoblash: bir dars narxi, standart oyda nechta dars
    # uchun to'lanadi (ortig'i - masalan 13-14-darslar - sovg'a bo'ladi), va
    # ustozning bitta o'quvchidan oyiga (to'liq yoqlama qo'ysa) olishi.
    lesson_price = Column(Float, default=40000)
    standard_lessons_per_month = Column(Integer, default=12)
    teacher_rate_per_student = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="groups")
    branch = relationship("Branch", back_populates="groups")
    students = relationship("Student", back_populates="group")
    lessons = relationship(
        "Lesson", back_populates="group", cascade="all, delete-orphan"
    )


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    parent_phone = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    enrolled_date = Column(Date, default=date.today)
    # O'quv markazni tark etgan sana. LTV ("mijoz qancha vaqt qoladi")
    # hisobotining asosi. Qo'lda kiritilmaydi: status "archived" bo'lganda
    # avtomatik qo'yiladi, o'quvchi qaytsa avtomatik tozalanadi.
    left_date = Column(Date, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    status = Column(String, default="active")  # active | trial | frozen | archived
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="students")
    branch = relationship("Branch", back_populates="students")
    payments = relationship(
        "Payment", back_populates="student", cascade="all, delete-orphan"
    )


class Payment(Base):
    """Ledger row. Positive amount = money paid in. Negative amount = a charge
    (e.g. monthly tuition fee) or a manual debit. Running balance for a
    student is simply the sum of all their Payment.amount values."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    amount = Column(Float, nullable=False)
    kind = Column(String, nullable=False, default="payment")  # payment | charge | discount
    # Pul qaysi kanal orqali kelgani: cash | card | terminal | other.
    # Faqat kind="payment" uchun to'ldiriladi (cashflow hisoboti shunga
    # tayanadi); hisoblangan to'lov va chegirmada bo'sh qoladi.
    method = Column(String, nullable=True)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    # "YYYY-MM" - avtomatik dars-asosidagi hisoblash (billing engine) shu oy
    # uchun yaratgan charge'larni belgilaydi, qo'lda kiritilgan to'lov/charge
    # uchun bo'sh qoladi. Bir talaba bir davr uchun ikki marta hisoblanib
    # qolmasligi (idempotentlik) shu maydon orqali tekshiriladi.
    period = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="payments")


class Lesson(Base):
    """Bitta guruh uchun bitta kunlik dars yozuvi - "yoqlama qo'yish". Qator
    mavjudligi shu dars o'tilgani (held)ni bildiradi; xato kiritilgan bo'lsa
    o'chirib tashlanadi. teacher_id - shu darsni haqiqatda kim o'tgani
    (odatda guruhning o'z ustozi, lekin almashtiruvchi ustoz bo'lishi ham
    mumkin) - bu ustoz ish haqini hisoblashda ishlatiladi."""
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    date = Column(Date, nullable=False, default=date.today)
    # 1 - dars HAQIQATDA o'tilgan (yoqlama qo'yilgan), 0 - jadval bo'yicha
    # REJALASHTIRILGAN. Guruh dars kunlari ("mon,wed,fri") bo'yicha butun
    # oyning darslari avtomat yaratiladi, lekin ular held=0 turadi:
    # o'quvchidan pul ham, ustozga ish haqi ham faqat held=1 darslar uchun
    # hisoblanadi. Yoqlama yoki baho qo'yilishi bilan held=1 bo'ladi.
    held = Column(Integer, default=1)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="lessons")
    teacher = relationship("Teacher")


class Lead(Base):
    """Hali o'quvchiga aylanmagan potensial mijoz (lid).

    "stage" - sotuv voronkasidagi bosqich, "source" - qayerdan kelgani.
    Manba boshlang'ich bosqichni ham belgilaydi: o'zi kirib kelgan odam
    "unga qo'ng'iroq qilish kerak" bosqichini allaqachon o'tgan bo'ladi."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    source = Column(String, nullable=False, default="other")
    stage = Column(String, nullable=False, default="new")

    # Qayerdan kelgani (mahalla/tuman), hozir o'qiyotgan maktabi va sinfi.
    # Uchalasi ham ixtiyoriy - lid birinchi qo'ng'iroqda to'liq bo'lmasligi mumkin.
    address = Column(String, nullable=True)
    school = Column(String, nullable=True)
    grade = Column(String, nullable=True)

    note = Column(Text, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    converted_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch = relationship("Branch")
    assigned_user = relationship("User")
    converted_student = relationship("Student")


class Expense(Base):
    """Markaz xarajati - ijara, kommunal, reklama, soliq va h.k.

    Ustozlar ish haqi bu yerga YOZILMAYDI: u TeacherPayout jadvalidan
    avtomatik olinadi. Aks holda P&L'da ikki marta hisoblanadi."""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, default=date.today)
    category = Column(String, nullable=False, default="other")
    amount = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    created_by = Column(String, nullable=True)
    # Reklama xarajati bo'lsa - qaysi kanal (instagram/telegram/...).
    # CAC shu ustun orqali kanal kesimida hisoblanadi.
    channel = Column(String, nullable=True)
    # Qaysi usulda to'landi - naqd/click/terminal. Kassa qoldig'i usul
    # kesimida to'g'ri chiqishi uchun kerak.
    method = Column(String, nullable=True, default="cash")
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch")


class TeacherPayout(Base):
    """Bir ustozning bir guruhdagi bir oy ("period" = YYYY-MM) uchun
    hisoblangan ish haqi - billing.py'dagi payroll formulasi natijasi.
    Qayta hisoblanganda mavjud qator yangilanadi (upsert); "paid" faqat
    qo'lda, administrator/moliya tomonidan belgilanadi."""
    __tablename__ = "teacher_payouts"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    period = Column(String, nullable=False)
    student_count = Column(Integer, default=0)
    held_lessons = Column(Integer, default=0)
    taught_lessons = Column(Integer, default=0)
    amount = Column(Float, default=0)
    paid = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    teacher = relationship("Teacher")
    group = relationship("Group")


class Attendance(Base):
    """Bitta o'quvchining bitta darsdagi davomati.

    Diqqat: hisob-kitob (billing) bundan EMAS, guruh darajasidagi Lesson
    yozuvlaridan hisoblanadi - o'quvchi kelmagan darsi ham to'lanadi.
    Bu jadval faqat davomat ko'rsatkichi uchun."""
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    present = Column(Integer, default=1)  # 1 = keldi, 0 = kelmadi
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lesson = relationship("Lesson")
    student = relationship("Student")


class DailyGrade(Base):
    """Ustozning bir dars uchun o'quvchiga qo'ygan bahosi (1-5).

    Ball aynan shuncha coinga teng: 5 baho = 5 coin. Coin qo'lda
    qo'shilmaydi - baho saqlanishi bilan CoinEntry avtomat yaratiladi,
    baho o'zgarsa coin ham o'zgaradi, baho o'chirilsa coin qaytariladi."""
    __tablename__ = "daily_grades"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    score = Column(Integer, nullable=False)  # 1..5
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lesson = relationship("Lesson")
    student = relationship("Student")


class Exam(Base):
    """Bir guruh uchun o'tkazilgan test: unit (1-12), mid-course,
    end of course yoki mock."""
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    kind = Column(String, nullable=False, default="unit")
    unit_no = Column(Integer, nullable=True)   # faqat kind="unit" uchun 1..12
    title = Column(String, nullable=True)
    date = Column(Date, nullable=False, default=date.today)
    # Unit/mid/end uchun maksimal ball. Mock uchun band ishlatiladi.
    max_score = Column(Float, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group")
    results = relationship(
        "ExamResult", back_populates="exam", cascade="all, delete-orphan"
    )


class ExamResult(Base):
    """Bitta o'quvchining bitta testdagi natijasi.

    Ustoz faqat ball (yoki mock uchun band) kiritadi - foiz avtomat
    hisoblanadi, coin ham avtomat beriladi."""
    __tablename__ = "exam_results"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    score = Column(Float, nullable=True)    # olgan bali
    band = Column(Float, nullable=True)     # mock IELTS band (0-9)
    percent = Column(Float, nullable=True)  # avtomat
    coins = Column(Integer, default=0)      # avtomat
    absent = Column(Integer, default=0)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exam = relationship("Exam", back_populates="results")
    student = relationship("Student")


class ExamCoinRule(Base):
    """Imtihon foizidan coinga o'tkazish qoidasi: foiz min_percent'dan
    katta yoki teng bo'lsa, eng yuqori mos qatorning coini beriladi.
    Asoschi bu jadvalni o'zgartirsa, keyingi natijalar yangi qoida
    bo'yicha hisoblanadi."""
    __tablename__ = "exam_coin_rules"

    id = Column(Integer, primary_key=True, index=True)
    min_percent = Column(Float, nullable=False)
    coins = Column(Integer, nullable=False)
    # null = hamma test turlari uchun; aks holda faqat shu tur uchun.
    kind = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CoinEntry(Base):
    """Coin harakati. O'quvchining balansi - shu jadvaldagi amountlar
    yig'indisi (alohida "balans" ustuni yo'q, shuning uchun u hech qachon
    haqiqatdan uzilib qolmaydi).

    source + ref_id juftligi avtomatik yozuvlarni bir marta yaratilishini
    ta'minlaydi: baho yoki natija o'zgarsa, o'sha yozuv yangilanadi."""
    __tablename__ = "coin_entries"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # + berildi, - yechildi
    source = Column(String, nullable=False, default="manual")
    ref_id = Column(Integer, nullable=True)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class Reward(Base):
    """Coinga almashtiriladigan sovg'a."""
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cost = Column(Integer, nullable=False)          # necha coin
    value_som = Column(Float, nullable=True)        # taxminiy so'mdagi qiymati
    stock = Column(Integer, nullable=True)          # null = cheklanmagan
    active = Column(Integer, default=1)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch")


class RewardRedemption(Base):
    """Sovg'a berilgani. coins - o'sha paytdagi narx: keyin sovg'a narxi
    o'zgarsa ham tarix buzilmaydi."""
    __tablename__ = "reward_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    reward_id = Column(Integer, ForeignKey("rewards.id"), nullable=False)
    coins = Column(Integer, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    reward = relationship("Reward")


class KpiCollectionRule(Base):
    """Eski to'lovlarni yig'ish bonusi.

    Filialdagi o'quvchi soni min_students..max_students oralig'ida bo'lsa
    va yig'ish foizi min_percent'dan katta yoki teng bo'lsa - bonus
    beriladi. Bir nechta qator to'g'ri kelsa, eng kattasi olinadi."""
    __tablename__ = "kpi_collection_rules"

    id = Column(Integer, primary_key=True, index=True)
    min_students = Column(Integer, nullable=False, default=0)
    max_students = Column(Integer, nullable=True)   # None = cheklanmagan
    min_percent = Column(Float, nullable=False)
    bonus = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class KpiNewClientRule(Base):
    """Yangi mijoz (birinchi marta to'lagan o'quvchi) soniga qarab bonus."""
    __tablename__ = "kpi_new_client_rules"

    id = Column(Integer, primary_key=True, index=True)
    min_clients = Column(Integer, nullable=False)
    bonus = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  HR - ishga olish voronkasi
# =====================================================================
class Vacancy(Base):
    """Ochiq ish o'rni. HR voronkasi shu bo'yicha bo'linadi."""
    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    role = Column(String, nullable=True)        # tizimdagi rol kaliti
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    headcount = Column(Integer, default=1)      # nechta odam kerak
    status = Column(String, default="open")
    salary_from = Column(Float, nullable=True)
    salary_to = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(Date, nullable=True)

    branch = relationship("Branch")


class Candidate(Base):
    """Ishga nomzod. Lidga o'xshab bosqichma-bosqich yuradi."""
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=True, index=True)
    stage = Column(String, nullable=False, default="applied")
    source = Column(String, nullable=False, default="other")
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    note = Column(Text, nullable=True)
    reject_reason = Column(String, nullable=True)
    # Ishga olingan sana - "qancha kunda yopdik" shundan hisoblanadi.
    hired_date = Column(Date, nullable=True)
    closed_date = Column(Date, nullable=True)   # hired yoki rejected sanasi
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy = relationship("Vacancy")
    branch = relationship("Branch")


class SocialStat(Base):
    """Instagram / Telegram obunachilar soni. Har o'lchov alohida qator -
    shunda o'sish grafigi ham chiqadi."""
    __tablename__ = "social_stats"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False, index=True)
    followers = Column(Integer, nullable=False)
    source = Column(String, default="auto")     # auto | manual
    date = Column(Date, default=date.today, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
