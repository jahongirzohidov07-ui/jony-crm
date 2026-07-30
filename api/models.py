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
    # Reyting og'irliklari (JSON). Bo'sh bo'lsa roles.BRANCH_RATING_DEFAULT.
    # Strategiya o'zgarsa foizlar ham o'zgaradi.
    rating_weights = Column(Text, nullable=True)
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
    # Odam o'qiy oladigan yagona raqam (EMP-000123). Telefon yoki ism
    # o'zgarsa ham bu o'zgarmaydi - tarix shunga bog'lanadi.
    public_id = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="teacher")
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    is_active = Column(Integer, default=1)
    # Ishdan bo'shaganda qanday ajrashildi: yashil / neytral / qizil
    # yo'lak. Qayta ishga olish masalasi shu bilan hal bo'ladi.
    exit_type = Column(String, nullable=True)
    exit_reason = Column(String, nullable=True)
    exit_date = Column(Date, nullable=True)
    # Fiks oylik (so'm). Adminlar (sotuv menejeri) KPI'sida asos bo'ladi:
    # jami ish haqi = fiks + bonuslar. Faqat asoschi o'zgartira oladi.
    fix_salary = Column(Float, nullable=True)

    # ---- Xodim kartasi ----
    phone = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    position = Column(String, nullable=True)     # lavozim nomi (roldan farqli)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    hired_date = Column(Date, nullable=True)
    photo = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", back_populates="users")
    manager = relationship("User", remote_side=[id])


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

    # Maksimal yuklama. Bo'sh bo'lsa DARAJADAN olinadi, u ham bo'lmasa
    # roles.TEACHER_MAX_*. Bundan oshirib guruh biriktirib bo'lmaydi.
    max_groups = Column(Integer, nullable=True)
    max_lessons_per_day = Column(Integer, nullable=True)

    # ---- Daraja va karyera ----
    # junior / middle / senior / expert / head. Bir o'quvchidan qancha
    # olishi ham, nechta guruh olib bora olishi ham shundan chiqadi.
    grade = Column(String, nullable=True)
    grade_since = Column(Date, nullable=True)
    # Sertifikat: "IELTS 7.0", "CEFR B2". cert_score - solishtirish
    # uchun raqam (IELTS balli yoki CEFR foizi).
    cert = Column(String, nullable=True)
    cert_score = Column(Float, nullable=True)
    # Metodika sertifikati: CELTA / TESOL / DELTA. Metodist darajasi
    # uchun shart.
    qualification = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)         # 18+ / 22+ sharti
    # Dars berish mahorati mezonidan olgan bali (0-100)
    skill_score = Column(Float, nullable=True)
    # Ustozlikdan oldingi support/volontyor tajribasi (oy)
    support_months = Column(Float, nullable=True)
    # Natija 50% dan past chiqqanda qo'yiladi: shu sanagacha yangi
    # guruh ochilmaydi, ustoz o'ta olmaganlarni qayta tayyorlaydi.
    remediation_until = Column(Date, nullable=True)
    remediation_reason = Column(String, nullable=True)
    # Oy o'rtasida hamma shart bajarilsa daraja darrov o'zgarmaydi:
    # bu yerga yoziladi va KEYINGI OYNING 1-sanasidan kuchga kiradi.
    # Shunda oy bitta stavkada yopiladi.
    pending_grade = Column(String, nullable=True)
    pending_grade_from = Column(Date, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch", back_populates="teachers")
    groups = relationship("Group", back_populates="teacher")


class TeacherGrade(Base):
    """Daraja jadvali. Hujjatdagi raqamlar bir marta shu yerga tushadi,
    keyin asoschi o'zgartiradi - kod ularga tegmaydi."""
    __tablename__ = "teacher_grades"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=False)
    order_no = Column(Integer, default=0)
    rate_per_student = Column(Float, default=0)
    min_months = Column(Integer, default=0)          # eng kam tajriba
    min_groups = Column(Integer, default=1)
    max_groups = Column(Integer, default=1)
    cert_label = Column(String, nullable=True)
    cert_min = Column(Float, nullable=True)
    # Keyingi darajaga o'tish uchun necha foiz o'quvchi o'tishi kerak
    promote_pass_rate = Column(Float, nullable=True)
    # Oylik test o'rtachasi shundan past bo'lsa - tushiriladi
    demote_below = Column(Float, nullable=True)
    demote_to = Column(String, nullable=True)
    # Metodika sertifikati (CELTA/TESOL/DELTA) shart bo'lgan daraja
    needs_qualification = Column(Integer, default=0)
    # Necha ta yuqori natija talab qilinadi va qaysi balldan
    min_results = Column(Integer, nullable=True)
    result_band = Column(Float, nullable=True)
    min_age = Column(Integer, nullable=True)
    min_skill = Column(Float, nullable=True)
    # O'quvchi "bosqichdan o'tdi" deb hisoblanishi uchun testda kamida
    # necha foiz olishi kerak. Hujjatda alohida aytilmagan - 60% dan
    # boshlanadi, asoschi o'zgartiradi.
    level_pass_percent = Column(Float, default=60.0)
    active = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TeacherGradeEvent(Base):
    """Daraja tarixi. Faqat "kim qachon ko'tarildi" uchun emas: OYLIK
    ham shu tarixdan hisoblanadi. Ustoz bugun ko'tarilsa, o'tgan oyning
    darslari eski stavkada qolishi kerak - aks holda tarix qayta
    yozilib, o'tgan oyning oyligi o'zgarib ketardi."""
    __tablename__ = "teacher_grade_events"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"),
                        nullable=False, index=True)
    from_grade = Column(String, nullable=True)
    to_grade = Column(String, nullable=True)
    kind = Column(String, nullable=False, default="set")   # roles.GRADE_EVENT_KINDS
    # Qaysi sanadan boshlab kuchga kiradi
    effective_from = Column(Date, nullable=False, default=date.today)
    reason = Column(Text, nullable=True)
    pass_rate = Column(Float, nullable=True)
    test_avg = Column(Float, nullable=True)
    rate_before = Column(Float, nullable=True)
    rate_after = Column(Float, nullable=True)
    decided_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher")


class TeacherStudyItem(Base):
    """O'qish rejasi: kitob va podkast. Ustoz o'zi belgilaydi,
    darajaga o'tishda tekshiriladi."""
    __tablename__ = "teacher_study_items"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"),
                        nullable=False, index=True)
    stage = Column(String, nullable=False)        # teacher | head
    kind = Column(String, nullable=False)         # book | podcast
    title = Column(String, nullable=False)
    done = Column(Integer, default=0)
    done_at = Column(Date, nullable=True)
    note = Column(String, nullable=True)
    # Bosqich imtihoni topshirilganmi (kitob+podkastdan keyin)
    created_at = Column(DateTime, default=datetime.utcnow)


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    # Odam o'qiy oladigan yagona raqam (GRP-000123). Telefon yoki ism
    # o'zgarsa ham bu o'zgarmaydi - tarix shunga bog'lanadi.
    public_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    room = Column(String, nullable=True)          # eski matnli xona
    # Xona ro'yxatidan tanlanadi - guruh to'lishi shu xona sig'imiga
    # nisbatan hisoblanadi.
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    # Xona tanlanmagan bo'lsa yoki guruh chekloviga alohida ehtiyoj
    # bo'lsa - o'z sig'imi.
    capacity = Column(Integer, nullable=True)
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
    # Odatda bu USTOZNING DARAJASIDAN olinadi (Junior 80 000, Middle
    # 100 000...). rate_manual=1 bo'lsa - kimdir bu guruhga ataylab
    # boshqa narx qo'ygan, daraja o'zgarganda unga tegilmaydi.
    teacher_rate_per_student = Column(Float, default=0)
    rate_manual = Column(Integer, default=0)

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
    # Odam o'qiy oladigan yagona raqam (STU-000123). Telefon yoki ism
    # o'zgarsa ham bu o'zgarmaydi - tarix shunga bog'lanadi.
    public_id = Column(String, unique=True, index=True)
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
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=True, index=True)
    status = Column(String, default="active")  # active | trial | frozen | archived
    # Hozirgi darajasi. Guruhga qo'shishda mos kelishi tekshiriladi.
    # Guruhga birinchi qo'shilganda avtomat to'ldiriladi, imtihondan
    # o'tganda ko'tariladi.
    subject = Column(String, nullable=True)
    level = Column(String, nullable=True)
    # O'quvchining o'z hisobiga bog'lanish. Bo'lsa — u kirib coin
    # balansini ko'radi va sovg'a so'ray oladi.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
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
    # Odam o'qiy oladigan yagona raqam (PAY-000123). Telefon yoki ism
    # o'zgarsa ham bu o'zgarmaydi - tarix shunga bog'lanadi.
    public_id = Column(String, unique=True, index=True)
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
    # Odam o'qiy oladigan yagona raqam (LID-000123). Telefon yoki ism
    # o'zgarsa ham bu o'zgarmaydi - tarix shunga bog'lanadi.
    public_id = Column(String, unique=True, index=True)
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
    # Tasdiqlash: examiner test tuzadi, keyin tasdiqlaydi, keyin
    # o'tkaziladi. Tasdiqlanmagan testga natija kiritib bo'lmaydi.
    status = Column(String, default="draft")
    approved_by = Column(String, nullable=True)
    approved_at = Column(Date, nullable=True)
    # Qayta imtihon bo'lsa - asl imtihonga bog'lanadi.
    retake_of_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    note = Column(Text, nullable=True)
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
    # Do'konda guruhlab ko'rsatish uchun: merch / tech / sport / special
    category = Column(String, nullable=True)
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
    # O'quvchi o'zi so'rasa "requested" bo'ladi va coin BAND qilinadi;
    # sovg'a qo'lga berilganda "given" bo'ladi. Rad etilsa coin qaytadi.
    status = Column(String, nullable=False, default="given")
    requested_by_student = Column(Integer, default=0)
    given_by = Column(String, nullable=True)
    given_at = Column(DateTime, nullable=True)
    note = Column(String, nullable=True)
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

    # ---- Nomzod kartasi ----
    cv = Column(Text, nullable=True)                 # CV matni yoki havola
    experience_years = Column(Float, nullable=True)  # umumiy tajriba (yil)
    workplaces = Column(Text, nullable=True)         # oldingi ish joylari
    certificates = Column(Text, nullable=True)       # sertifikatlar ro'yxati
    language_level = Column(String, nullable=True)   # roles.LANGUAGE_LEVELS
    expected_salary = Column(Float, nullable=True)
    trial_score = Column(Float, nullable=True)       # probniy dars bahosi (0-10)
    interview_score = Column(Float, nullable=True)   # intervyu bahosi (0-10)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    reference_note = Column(Text, nullable=True)     # tavsiyanoma
    decision = Column(String, nullable=True, default="pending")

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


# =====================================================================
#  Ota-ona, shartnoma, audit log, shikoyat
# =====================================================================
class Parent(Base):
    """Ota-ona alohida shaxs - o'zining ID'si bilan.

    Aka-uka/opa-singil bir ota-onaga bog'lanadi: shunda "bu oila bizga
    qancha to'lagan" degan savolga javob bor, va telefon o'zgarsa bitta
    joyda o'zgaradi."""
    __tablename__ = "parents"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)   # PAR-000123
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True, index=True)
    phone2 = Column(String, nullable=True)
    relation = Column(String, nullable=True)   # ota / ona / vasiy
    address = Column(String, nullable=True)
    workplace = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch")


class Contract(Base):
    """O'quvchi bilan tuzilgan shartnoma."""
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)   # SHT-000123
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("parents.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)

    date = Column(Date, default=date.today)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    monthly_fee = Column(Float, default=0)
    discount_percent = Column(Float, default=0)
    status = Column(String, default="active")   # active | finished | cancelled
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    parent = relationship("Parent")
    group = relationship("Group")
    branch = relationship("Branch")


class AuditLog(Base):
    """Har bir o'zgarish shu yerga yoziladi: kim, qachon, nimani,
    eskisi qanday edi, yangisi qanday bo'ldi.

    Yozuvlar hech qachon o'chirilmaydi va tahrirlanmaydi - shuning
    uchun ular haqiqatning yagona manbai bo'lib qoladi."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    # Kim
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String, nullable=True)
    user_name = Column(String, nullable=True)     # to'liq ism, o'sha paytdagi
    user_role = Column(String, nullable=True)
    # Nima ustida
    entity = Column(String, nullable=False, index=True)   # student, payment...
    entity_id = Column(Integer, nullable=True, index=True)
    entity_label = Column(String, nullable=True)          # "Abdulqodir F."
    action = Column(String, nullable=False, index=True)   # create/update/delete/...
    field = Column(String, nullable=True)                 # qaysi maydon
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    branch = relationship("Branch")


class Complaint(Base):
    """Ota-ona yoki o'quvchi shikoyati. Asoschi panelida ochiq
    shikoyatlar soni ko'rinib turadi."""
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    source = Column(String, default="phone")    # phone/visit/telegram/...
    severity = Column(String, default="normal")  # low | normal | high
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    status = Column(String, default="open")      # open | in_progress | closed
    resolution = Column(Text, nullable=True)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    closed_at = Column(Date, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    student = relationship("Student")
    group = relationship("Group")
    branch = relationship("Branch")
    assigned_user = relationship("User")


# =====================================================================
#  O'quv bo'limi: xonalar, akademik risk
# =====================================================================
class Room(Base):
    """Dars xonasi va uning sig'imi. Guruh to'lishi shu sig'imga
    nisbatan hisoblanadi."""
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    capacity = Column(Integer, default=12)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    note = Column(String, nullable=True)
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch")


class RiskFlag(Base):
    """Qo'lda qo'yiladigan risk signali (ustoz izohi, uy vazifasi va h.k.).

    Avtomat aniqlanadigan signallar (dars qoldirish, to'lov kechikishi,
    shikoyat, guruh almashtirish) bu jadvalga yozilmaydi - ular har safar
    haqiqiy ma'lumotdan hisoblanadi. Bu yerda faqat odam ko'rgan narsa
    turadi."""
    __tablename__ = "risk_flags"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    signal = Column(String, nullable=False)   # roles.RISK_SIGNALS kaliti
    note = Column(Text, nullable=True)
    active = Column(Integer, default=1)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(Date, nullable=True)

    student = relationship("Student")


class RiskTask(Base):
    """Risk uchun mas'ul va vazifa. Har bir xavfdagi o'quvchi bo'yicha
    kimdir nimadir qilishi kerak - shu yerda yoziladi."""
    __tablename__ = "risk_tasks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    level = Column(String, nullable=True)      # yaratilgan paytdagi daraja
    title = Column(String, nullable=False)
    assigned_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(String, default="open")    # open | done | cancelled
    result = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    done_at = Column(Date, nullable=True)

    student = relationship("Student")
    assigned_user = relationship("User")


class ParentTalk(Base):
    """Ota-ona bilan suhbat. O'quvchi kartasidagi tarixga tushadi."""
    __tablename__ = "parent_talks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    date = Column(Date, default=date.today)
    channel = Column(String, default="phone")   # phone | visit | telegram
    topic = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    outcome = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class Certificate(Base):
    """O'quvchi olgan sertifikat. Marketing voronkasining oxirgi
    bosqichi shundan hisoblanadi."""
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    kind = Column(String, default="internal")
    level = Column(String, nullable=True)      # "7.0", "B2" ...
    score = Column(Float, nullable=True)
    date = Column(Date, default=date.today)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class AdStat(Base):
    """Reklama platformasidan olinadigan ko'rsatkich: nechta odam
    ko'rdi va nechtasi bosdi. Oyiga bir marta kanal bo'yicha
    kiritiladi - voronkaning birinchi ikki bosqichi shundan."""
    __tablename__ = "ad_stats"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, nullable=False, index=True)
    period = Column(String, nullable=False, index=True)   # "2026-07"
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch")


# =====================================================================
#  Examiner, support teacher va fayl biriktirish
# =====================================================================
class SupportAssignment(Base):
    """Support teacher qaysi guruh yoki o'quvchiga biriktirilgani."""
    __tablename__ = "support_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    group = relationship("Group")
    student = relationship("Student")


class SupportPlan(Base):
    """O'quvchi bilan ishlash rejasi: qanday muammo, nima qilinadi,
    natija qanday bo'ldi."""
    __tablename__ = "support_plans"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    issue = Column(String, default="attendance")
    plan = Column(Text, nullable=False)
    due_date = Column(Date, nullable=True)
    status = Column(String, default="open")     # open | done | failed
    result = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    done_at = Column(Date, nullable=True)

    student = relationship("Student")
    user = relationship("User")


class Attachment(Base):
    """Fayl (rasm, sertifikat, hujjat). Bazada base64 ko'rinishida
    saqlanadi - alohida fayl xizmati kerak emas."""
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    entity = Column(String, nullable=False, index=True)    # candidate, student...
    entity_id = Column(Integer, nullable=False, index=True)
    kind = Column(String, default="document")
    filename = Column(String, nullable=True)
    mime = Column(String, nullable=True)
    size = Column(Integer, default=0)
    data = Column(Text, nullable=False)        # base64
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Discount(Base):
    """Chegirma. Pul demak - shuning uchun har birida sabab, miqdor,
    muddat va TASDIQLAGAN SHAXS bo'ladi. Tasdiqsiz chegirma ishlamaydi.

    Oila chegirmasini tizim o'zi boshqaradi (kind="family"), qolganini
    odam so'raydi va rahbar tasdiqlaydi."""
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    kind = Column(String, nullable=False, default="individual")  # roles.DISCOUNT_TYPES
    percent = Column(Float, nullable=True)      # foizda
    amount = Column(Float, nullable=True)       # yoki qat'iy summa (so'm)
    reason = Column(Text, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)      # bo'sh = muddatsiz
    status = Column(String, nullable=False, default="pending")

    # Referral: qaysi do'sti olib keldi
    referrer_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    # Xodim farzandi: qaysi xodim. Xodim ketsa chegirma avtomat bekor.
    staff_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    requested_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    cancelled_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", foreign_keys=[student_id])
    referrer = relationship("Student", foreign_keys=[referrer_student_id])
    staff = relationship("User", foreign_keys=[staff_user_id])


class StaffEvent(Base):
    """Xodim kartasidagi voqealar: ta'til, kechikish, trening, baholash,
    intizomiy holat, rag'batlantirish. Hammasi bir jadvalda - karta
    ochilganda butun tarix bir joyda ko'rinadi."""
    __tablename__ = "staff_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    kind = Column(String, nullable=False)       # roles.STAFF_EVENTS
    happened_on = Column(Date, nullable=False, default=date.today)
    end_date = Column(Date, nullable=True)      # ta'til uchun
    title = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    score = Column(Float, nullable=True)        # baholash bali
    amount = Column(Float, nullable=True)       # bonus summasi
    minutes = Column(Integer, nullable=True)    # kechikish daqiqasi
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", foreign_keys=[user_id])


class OnboardingStep(Base):
    """Yangi xodim checklisti. Har bir qadam alohida yozuv - kim va
    qachon bajarganini ko'rsatadi."""
    __tablename__ = "onboarding_steps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    step = Column(String, nullable=False)       # roles.ONBOARDING_STEPS
    done = Column(Integer, default=0)
    done_at = Column(DateTime, nullable=True)
    done_by = Column(String, nullable=True)
    note = Column(String, nullable=True)


class Task(Base):
    """Vazifa. Majlisdagi qaror shu yerga tushmasa - majlis choy
    ichishga aylanadi."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    watcher_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    deadline = Column(Date, nullable=True)
    priority = Column(String, nullable=False, default="normal")
    status = Column(String, nullable=False, default="new")
    source = Column(String, nullable=False, default="manual")
    # Majlis nomi/sanasi - qaror qaysi majlisdan chiqqani
    meeting = Column(String, nullable=True)
    # Checklist JSON: [{"text": "...", "done": true}, ...]
    checklist = Column(Text, nullable=True)
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)
    result = Column(Text, nullable=True)
    delay_reason = Column(Text, nullable=True)
    done_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignee = relationship("User", foreign_keys=[assignee_id])
    watcher = relationship("User", foreign_keys=[watcher_id])
    branch = relationship("Branch")


class Asset(Base):
    """Aktiv: kompyuter, proyektor, konditsioner... Har birida inventar
    raqami va mas'ul xodim bo'ladi - shunda "kim sindirdi" savoli
    javobsiz qolmaydi."""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    inventory_no = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False, default="other")   # roles.ASSET_TYPES
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    purchased_on = Column(Date, nullable=True)
    price = Column(Float, nullable=True)
    condition = Column(String, nullable=False, default="good")
    warranty_until = Column(Date, nullable=True)
    serial_no = Column(String, nullable=True)
    photo = Column(Text, nullable=True)          # base64 data URL
    note = Column(Text, nullable=True)
    written_off_on = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch = relationship("Branch")
    room = relationship("Room")
    responsible = relationship("User", foreign_keys=[responsible_id])
    repairs = relationship(
        "AssetRepair", back_populates="asset", cascade="all, delete-orphan"
    )


class AssetRepair(Base):
    """Ta'mirlash tarixi. Bir jihoz uch marta ta'mirlansa - uni
    almashtirish arzonroq degan xulosa shundan chiqadi."""
    __tablename__ = "asset_repairs"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    happened_on = Column(Date, nullable=False, default=date.today)
    cost = Column(Float, default=0)
    vendor = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", back_populates="repairs")


class Consumable(Base):
    """Sarflanadigan mahsulot: kitob, marker, sertifikat qog'ozi...
    Minimal qoldiqdan pastga tushsa xarid so'rovi avtomat yaratiladi."""
    __tablename__ = "consumables"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=False, default="other")   # roles.CONSUMABLE_TYPES
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    qty = Column(Float, default=0)
    min_qty = Column(Float, default=0)
    unit = Column(String, nullable=True)
    unit_price = Column(Float, nullable=True)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch = relationship("Branch")


class StockMove(Base):
    """Ombor harakati. Qoldiq qo'lda tuzatilmaydi - faqat harakat
    orqali o'zgaradi, shunda tarix buzilmaydi."""
    __tablename__ = "stock_moves"

    id = Column(Integer, primary_key=True, index=True)
    consumable_id = Column(Integer, ForeignKey("consumables.id"), nullable=False, index=True)
    delta = Column(Float, nullable=False)       # + kirim, - chiqim
    reason = Column(String, nullable=False, default="out")
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consumable = relationship("Consumable")


class PurchaseRequest(Base):
    """Xarid so'rovi. Qoldiq minimaldan pastga tushganda tizim o'zi
    yaratadi - odam esdan chiqarsa ham marker tugab qolmaydi."""
    __tablename__ = "purchase_requests"

    id = Column(Integer, primary_key=True, index=True)
    consumable_id = Column(Integer, ForeignKey("consumables.id"), nullable=False, index=True)
    qty = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="open")  # open | ordered | done | cancelled
    auto = Column(Integer, default=1)
    note = Column(String, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    consumable = relationship("Consumable")


class TeacherPayment(Base):
    """Ustozga HAQIQATDA berilgan pul: avans, oylik yoki tuzatish.

    Ishlab topilgan summa (earned) yoqlamadan avtomat hisoblanadi va
    hech qayerda saqlanmaydi. Bu jadval esa faqat qo'ldan chiqqan pulni
    yozadi. Balans = ishlab topgan - berilgan.

    Shu sababli "o'tgan oyda ko'proq berilgan" holat o'zidan keyingi
    oyga o'tadi: balans manfiy bo'lib qoladi."""
    __tablename__ = "teacher_payments"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    kind = Column(String, nullable=False, default="salary")  # advance|salary|correction
    period = Column(String, nullable=True)      # "YYYY-MM"
    paid_on = Column(Date, nullable=False, default=date.today)
    method = Column(String, nullable=True)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher")


class DebtorContact(Base):
    """Qarzdor bilan bog'lanish yozuvi. Administrator "bog'lanildi"
    tugmasini bosadi va qachon to'layman deganini yozib qo'yadi -
    keyingi kuni kimga qo'ng'iroq qilish kerakligi shundan ko'rinadi."""
    __tablename__ = "debtor_contacts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    contacted_on = Column(Date, nullable=False, default=date.today)
    promised_date = Column(Date, nullable=True)
    promised_amount = Column(Float, nullable=True)
    result = Column(String, nullable=True)   # promised|no_answer|refused|paid
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class RolePermission(Base):
    """Asoschi o'zgartirgan ruxsat. Kod bilan keladigan standart holat
    roles.DEFAULT_MATRIX'da turadi; bu jadval faqat FARQNI saqlaydi.

    Shunday qilingani uchun yangi bo'lim qo'shilganda eski rollarga
    avtomat mos ruxsat beriladi — bazani qo'lda to'ldirish kerak emas."""
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False, index=True)
    resource = Column(String, nullable=False, index=True)
    action = Column(String, nullable=False)
    allowed = Column(Integer, default=0)
    changed_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StaffAttendance(Base):
    """Xodimning kelib-ketish vaqti. Kechikish daqiqasi avtomat
    hisoblanadi — qo'lda yozilmaydi, aks holda hech kim o'zini
    kechikkan deb yozmaydi."""
    __tablename__ = "staff_attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    work_date = Column(Date, nullable=False, default=date.today, index=True)
    check_in = Column(String, nullable=True)     # "09:05"
    check_out = Column(String, nullable=True)    # "18:00"
    late_minutes = Column(Integer, default=0)
    early_minutes = Column(Integer, default=0)   # erta ketgan
    worked_minutes = Column(Integer, default=0)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class TeacherRating(Base):
    """O'quvchi yoki ota-ona ustozga bergan baho (NPS).

    0-10 shkala: 9-10 tarafdor, 7-8 betaraf, 0-6 tanqidchi.
    NPS = tarafdorlar% - tanqidchilar%."""
    __tablename__ = "teacher_ratings"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    source = Column(String, nullable=False, default="student")  # student|parent
    score = Column(Integer, nullable=False)       # 0-10
    comment = Column(Text, nullable=True)
    period = Column(String, nullable=True)        # "YYYY-MM"
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher")
    student = relationship("Student")


class LeaveReason(Base):
    """O'quvchi nega ketdi. Churn tahlilining asosi — sababsiz raqam
    hech narsani o'zgartirmaydi."""
    __tablename__ = "leave_reasons"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    reason = Column(String, nullable=False)      # roles.LEAVE_REASONS
    note = Column(Text, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    left_date = Column(Date, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class Notification(Base):
    """Yuboriladigan xabar. Tug'ilgan kun, to'lov eslatmasi, yangi kurs.

    Tizim xabarni O'ZI yaratadi va navbatga qo'yadi; yuborish esa
    Telegram bot tokeni yoki SMS xizmati ulanganda ishlaydi."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String, nullable=False)         # roles.NOTIFY_KINDS
    channel = Column(String, nullable=False, default="telegram")  # telegram|sms
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    phone = Column(String, nullable=True)
    title = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="queued")  # queued|sent|failed|cancelled
    scheduled_for = Column(Date, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True)
    error = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class NotifyTemplate(Base):
    """Xabar shabloni. {ism}, {summa}, {sana} kabi o'rinbosarlar
    matn ichida turadi."""
    __tablename__ = "notify_templates"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String, nullable=False, unique=True)
    title = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    channel = Column(String, nullable=False, default="telegram")
    active = Column(Integer, default=1)
    days_before = Column(Integer, default=0)   # to'lov eslatmasi uchun
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =====================================================================
#  GAMIFICATION: XP, LIGA, SEASON
#
#  XP balansi bitta ustunni o'zgartirish orqali yuritilmaydi. Asosiy
#  manba — append-only tranzaksiya jurnali. Summary jadvali faqat
#  tezlik uchun: uni har doim jurnaldan qayta hisoblash mumkin.
# =====================================================================
class XpLeague(Base):
    """Liga. Chegara, rang va mukofot admin panelidan boshqariladi —
    kodda qattiq yozilmagan."""
    __tablename__ = "xp_leagues"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    rank = Column(Integer, nullable=False, default=1)
    minimum_xp = Column(Integer, nullable=False, default=0)
    maximum_xp = Column(Integer, nullable=True)      # None = cheklanmagan
    color = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    background_image = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    reward_coin = Column(Integer, default=0)
    reward_badge_id = Column(Integer, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class XpSeason(Base):
    """Mavsum. Season XP yangi mavsumda 0 dan boshlanadi, Lifetime XP
    esa hech qachon reset qilinmaydi."""
    __tablename__ = "xp_seasons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False, default=date.today)
    end_date = Column(Date, nullable=True)
    is_active = Column(Integer, default=1)
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class XpRule(Base):
    """XP berish qoidasi. Qiymati o'zgarsa ESKI tranzaksiyalar
    o'zgarmaydi — ular o'sha paytdagi qiymat bilan yozilgan."""
    __tablename__ = "xp_rules"

    id = Column(Integer, primary_key=True, index=True)
    event_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False, default="academic")
    default_xp = Column(Integer, default=0)
    default_coin = Column(Integer, default=0)
    maximum_per_lesson = Column(Integer, nullable=True)
    maximum_per_day = Column(Integer, nullable=True)
    maximum_per_week = Column(Integer, nullable=True)
    maximum_per_month = Column(Integer, nullable=True)
    mode = Column(String, default="automatic")       # automatic | manual
    requires_approval = Column(Integer, default=0)
    allowed_roles = Column(Text, nullable=True)      # vergul bilan
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class XpTransaction(Base):
    """Append-only XP jurnali. Yozuv O'CHIRILMAYDI — xato bo'lsa
    manfiy reversal yoziladi. Shunda to'liq tarix saqlanadi."""
    __tablename__ = "xp_transactions"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    amount = Column(Float, nullable=False, default=0)   # musbat yoki manfiy
    category = Column(String, nullable=True, index=True)
    event_code = Column(String, nullable=True, index=True)
    xp_rule_id = Column(Integer, ForeignKey("xp_rules.id"), nullable=True)
    source_type = Column(String, nullable=True)
    source_id = Column(Integer, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    season_id = Column(Integer, ForeignKey("xp_seasons.id"),
                       nullable=True, index=True)
    awarded_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    meta = Column(Text, nullable=True)                 # JSON
    # Takror yozuvni to'xtatadi: bir xil kalit bilan ikkinchi marta
    # yozib bo'lmaydi (masalan bitta darsga ikki marta XP).
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    reversed_transaction_id = Column(Integer,
                                     ForeignKey("xp_transactions.id"),
                                     nullable=True)
    is_reversal = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    student = relationship("Student")


class StudentGamification(Base):
    """Tezlik uchun jamlanma. Har doim jurnaldan qayta hisoblanishi
    mumkin — haqiqat manbai jurnalda."""
    __tablename__ = "student_gamification"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        unique=True, index=True, nullable=False)
    lifetime_xp = Column(Float, default=0, index=True)
    season_xp = Column(Float, default=0, index=True)
    season_id = Column(Integer, ForeignKey("xp_seasons.id"), nullable=True)
    current_league_id = Column(Integer, ForeignKey("xp_leagues.id"),
                               nullable=True, index=True)
    current_level = Column(Integer, default=1)
    # Kategoriya kesimidagi XP (JSON)
    by_category = Column(Text, nullable=True)
    last_xp_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    student = relationship("Student")


class StudentLeagueHistory(Base):
    """Ligaga ko'tarilish tarixi. Liga tushmaydi — Lifetime XP
    kamaymaydi."""
    __tablename__ = "student_league_history"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    from_league_id = Column(Integer, ForeignKey("xp_leagues.id"), nullable=True)
    to_league_id = Column(Integer, ForeignKey("xp_leagues.id"), nullable=True)
    xp_at_promotion = Column(Float, default=0)
    reward_coin = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class XpStreak(Base):
    """O'quvchining ketma-ketligi: davomat, homework, test."""
    __tablename__ = "xp_streaks"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    kind = Column(String, nullable=False)          # attendance|homework|test
    current = Column(Integer, default=0)
    longest = Column(Integer, default=0)
    last_event_date = Column(Date, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class XpStreakMilestone(Base):
    """Bosqich bonusi bir marta beriladi: 10 ga yetganda 5 lik bonus
    qaytadan berilmaydi."""
    __tablename__ = "xp_streak_milestones"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    kind = Column(String, nullable=False)
    milestone = Column(Integer, nullable=False)
    awarded_at = Column(DateTime, default=datetime.utcnow)


class GamificationAchievement(Base):
    """Yutuq turi (badge)."""
    __tablename__ = "gamification_achievements"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    tone = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class StudentAchievement(Base):
    __tablename__ = "student_achievements"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    achievement_id = Column(Integer,
                            ForeignKey("gamification_achievements.id"),
                            nullable=False)
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class XpApprovalRequest(Base):
    """Katta qo'lda XP tasdiqdan o'tadi."""
    __tablename__ = "xp_approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    event_code = Column(String, nullable=True)
    amount = Column(Float, default=0)
    reason = Column(Text, nullable=True)
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="pending")     # pending|approved|rejected
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")


class XpFraudAlert(Base):
    """Shubhali XP harakati."""
    __tablename__ = "xp_fraud_alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="LOW")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    transaction_id = Column(Integer, ForeignKey("xp_transactions.id"),
                            nullable=True)
    description = Column(Text, nullable=True)
    meta = Column(Text, nullable=True)
    status = Column(String, default="open")
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime, nullable=True)


class SeasonRankSnapshot(Base):
    """Leaderboarddagi o'rin o'zgarishini ko'rsatish uchun."""
    __tablename__ = "season_rank_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    scope = Column(String, nullable=False)          # lifetime|season|week|month
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    xp = Column(Float, default=0)
    taken_on = Column(Date, nullable=False, default=date.today, index=True)


# =====================================================================
#  DARS BAHOLASH (observation)
#
#  Nomzod ishga olinayotganda ham, ishlayotgan ustoz tekshirilganda ham
#  bir xil mezon ishlatiladi. Natija ustozning skill_score'iga tushadi —
#  ya'ni karyera darajasiga ta'sir qiladi.
# =====================================================================
class LessonRubric(Base):
    """Baholash jadvali: birinchi dars yoki asosiy dars."""
    __tablename__ = "lesson_rubrics"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class RubricCriterion(Base):
    """Bitta mezon va uning bali."""
    __tablename__ = "rubric_criteria"

    id = Column(Integer, primary_key=True, index=True)
    rubric_key = Column(String, nullable=False, index=True)
    order_no = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    points = Column(Float, default=0)
    is_active = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class LessonObservation(Base):
    """Bitta baholash: kim, qachon, qaysi jadval bo'yicha, necha ball."""
    __tablename__ = "lesson_observations"

    id = Column(Integer, primary_key=True, index=True)
    rubric_key = Column(String, nullable=False, index=True)
    target_type = Column(String, nullable=False, default="teacher")
    teacher_id = Column(Integer, ForeignKey("teachers.id"),
                        nullable=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"),
                          nullable=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    date = Column(Date, nullable=False, default=date.today)
    # Jami avtomat hisoblanadi — qo'lda yozilmaydi
    total = Column(Float, default=0)
    max_total = Column(Float, default=0)
    percent = Column(Float, default=0)
    band = Column(String, nullable=True)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    note = Column(Text, nullable=True)
    observer = Column(String, nullable=True)
    observer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher")
    scores = relationship("ObservationScore", back_populates="observation",
                          cascade="all, delete-orphan")


class ObservationScore(Base):
    """Bitta mezon bo'yicha qo'yilgan fakt bali."""
    __tablename__ = "observation_scores"

    id = Column(Integer, primary_key=True, index=True)
    observation_id = Column(Integer, ForeignKey("lesson_observations.id"),
                            nullable=False, index=True)
    criterion_id = Column(Integer, ForeignKey("rubric_criteria.id"),
                          nullable=False)
    fact = Column(Float, default=0)
    note = Column(String, nullable=True)

    observation = relationship("LessonObservation", back_populates="scores")
