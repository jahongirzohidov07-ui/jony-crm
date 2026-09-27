from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text,
    event, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship, deferred
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

    # HAMKOR FILIAL (2026-08-15, Jahongir: "hamkorlikda ochgan Stech
    # o'quv markazimi ham bor ... uni men umuman boshqarmayman, faqat
    # asoschi sifatida 40% ulushim bor").
    #
    # Hamkor filial JonyOS ichida to'liq ishlaydi, LEKIN uning
    # raqamlari Jony Academy'ning UMUMIY yig'indilariga qo'shilmaydi:
    # bu boshqa biznesning aylanmasi. Ko'rish uchun tepadagi
    # tanlagichdan o'sha filialni tanlash kerak.
    is_partner = Column(Integer, default=0, index=True)
    # SINOV FILIALI (2026-09-25): adminlar mashqi shu filialda
    # kechadi. Mashq paytida yaratilgan o'quvchi, to'lov va guruh
    # haqiqiy filiallarga tushmaydi.
    is_test = Column(Integer, default=0, index=True)
    partner_note = Column(String, nullable=True)   # kim boshqaradi, ulush
    owner_percent = Column(Float, nullable=True)   # bizning ulushimiz (%)

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
    # XODIM TELEGRAMI (2026-08-15). Asoschiga server xatosi
    # ogohlantirishi va kunlik zaxira fayli shu chat orqali boradi.
    # Ulash: xodim profilidagi kodni botga "/start KOD" deb yozadi.
    tg_code = Column(String, nullable=True, index=True)
    telegram_chat_id = Column(String, nullable=True)
    # Ishdan bo'shaganda qanday ajrashildi: yashil / neytral / qizil
    # yo'lak. Qayta ishga olish masalasi shu bilan hal bo'ladi.
    exit_type = Column(String, nullable=True)
    exit_reason = Column(String, nullable=True)
    exit_date = Column(Date, nullable=True)
    # Fiks oylik (so'm). Adminlar (sotuv menejeri) KPI'sida asos bo'ladi:
    # jami ish haqi = fiks + bonuslar. Faqat asoschi o'zgartira oladi.
    fix_salary = Column(Float, nullable=True)
    # Favqulodda tiklash kodi (hash). Asoschi parolni unutsa, shu kod
    # bilan yangi parol o'rnatadi — bazaga qo'l tiqishga hojat yo'q.
    recovery_hash = Column(String, nullable=True)

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

    # Tizimga kirish hisobi. Ism bo'yicha emas, ID bo'yicha bog'lanadi —
    # ustozning ismi keyin o'zgarsa ham aloqa uzilmaydi.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True,
                     index=True)

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


class TeacherGradeRate(Base):
    """DARAJA STAVKASI TARIXI (2026-09-03).

    Jahongir: "men tepadagi 80-160gacha bo'lgan summani 20,000dan
    oshirmoqchiman sentabrdan ustozlarniki".

    Ilgari stavka faqat teacher_grades.rate_per_student ustunida
    turardi — u o'zgartirilsa, O'TGAN OYLARNING oyligi ham yangi
    stavkada qayta hisoblanib ko'rinardi (avgust allaqachon eski
    narxda to'langan bo'lsa ham). Endi har o'zgarish "qaysi oydan"
    sanasi bilan shu yerga yoziladi va oylik hisobi dars sanasida
    amalda bo'lgan stavkani oladi.

    Yozuv o'chirilmaydi — tarix bo'lib qoladi."""
    __tablename__ = "teacher_grade_rates"

    id = Column(Integer, primary_key=True, index=True)
    grade_key = Column(String, index=True, nullable=False)
    rate_per_student = Column(Float, nullable=False)
    # Shu sanadan (oyning 1-kuni) amal qiladi
    effective_from = Column(Date, index=True, nullable=False)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


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

    # QAYSI KURS (2026-08-15). Kurs tanlansa narx va oyiga dars soni
    # kursdan olinadi va kurs narxi o'zgarganda bu guruhga ham
    # ko'chiriladi. price_manual=1 bo'lsa - bu guruhga ataylab boshqa
    # narx qo'yilgan, kurs o'zgarishi unga tegmaydi.
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=True,
                       index=True)
    price_manual = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    teacher = relationship("Teacher", back_populates="groups")
    branch = relationship("Branch", back_populates="groups")
    students = relationship("Student", back_populates="group")
    lessons = relationship(
        "Lesson", back_populates="group", cascade="all, delete-orphan"
    )


class Course(Base):
    """KURS — filialning narx ro'yxati (2026-08-15).

    Jahongir: "sozlamalar ichida kurslar bolimini ochib u yerda
    kurslarni yozadi dars vaqti narxini bitta darsga narxini yozadi,
    shu narxlar hamma joyga ulanadi va shu boyicha hisob kitob
    qilinaveradi bizda ham sentabrdan narxlar oshadi".

    Har filialning O'Z kurslari bo'ladi — hamkor markazda fanlar ham,
    narx ham, dars davomiyligi ham boshqacha.

    NARX QANDAY ISHLAYDI. Kurs narxi guruhga KO'CHIRILADI
    (group.lesson_price). Shu sababli butun hisob-kitob mantig'i
    o'zgarmaydi va o'tgan oylarning hisobi hech qachon qayta
    yozilmaydi — faqat kelgusi hisoblar yangi narxda chiqadi."""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True,
                       index=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=True)        # roles.SUBJECTS yoki erkin
    level = Column(String, nullable=True)
    # Bitta darsning davomiyligi (daqiqa) — jadval tuzishda ishlatiladi
    lesson_minutes = Column(Integer, default=90)
    # Bitta dars narxi va standart oyda nechta dars uchun to'lanadi
    lesson_price = Column(Float, default=0)
    lessons_per_month = Column(Integer, default=12)
    active = Column(Integer, default=1, index=True)
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    branch = relationship("Branch")


class CoursePriceChange(Base):
    """Rejalashtirilgan narx o'zgarishi ("sentabrdan oshadi").

    Sana kelganda kunlik ish narxni kursga va uning guruhlariga
    ko'chiradi. O'tgan oylarga TEGMAYDI."""
    __tablename__ = "course_price_changes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False,
                       index=True)
    from_date = Column(Date, nullable=False, index=True)
    lesson_price = Column(Float, nullable=False)
    lessons_per_month = Column(Integer, nullable=True)
    note = Column(String, nullable=True)
    # ESKI NARX HIMOYASI (2026-08-15): belgilansa, narx oshgan kuni
    # FAOL bo'lgan o'quvchilar eski narxda qolib ketadi. Yangi
    # kelganlar va muzlatib qaytganlar yangi narxda o'qiydi.
    keep_old_for_active = Column(Integer, default=1)
    locked_students = Column(Integer, default=0)   # nechtasi qulflandi
    applied_at = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    course = relationship("Course")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    # Odam o'qiy oladigan yagona raqam (STU-000123). Telefon yoki ism
    # o'zgarsa ham bu o'zgarmaydi - tarix shunga bog'lanadi.
    public_id = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=False)
    # O'quvchi PROFILIDAN kiritiladigan alohida qismlar (2026-08-10,
    # Jahongir: "faqat ism, familiya, otchestva alohida o'zgartirsin").
    # full_name shulardan yig'iladi - xodimlar bazasida ham darhol
    # ko'rinadi. photo - kichraytirilgan avatar (data URL, ~50KB);
    # serverless muhitda fayl diski yo'q, shuning uchun bazada.
    # DEFERRED (2026-08-12): rasm faqat so'ralganda yuklanadi - aks
    # holda har "hamma o'quvchilar" so'rovi yuzlab MB tortib, Neon
    # data-transfer kvotasini yeb qo'ygan edi (sayt yotib qoldi).
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)
    photo = deferred(Column(Text, nullable=True))
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
    # Lid kartasidan ko'chadi — analitika va o'quvchi kartasi uchun
    address = Column(String, nullable=True)
    school = Column(String, nullable=True)
    school_grade = Column(String, nullable=True)
    # Muzlatish: qachon qaytadi va nima uchun
    frozen_until = Column(Date, nullable=True)
    frozen_note = Column(String, nullable=True)
    # MUZLATISH SABABI ro'yxatdan (2026-08-30, Jahongir: "muzlatish
    # sabablari statistikasi ham kerak"). frozen_note erkin izoh
    # bo'lib qoladi — u statistikaga yaramaydi, har kim har xil
    # yozadi. Kod esa roles.FREEZE_REASONS dan.
    frozen_reason = Column(String, nullable=True, index=True)
    # Hozirgi darajasi. Guruhga qo'shishda mos kelishi tekshiriladi.
    # Guruhga birinchi qo'shilganda avtomat to'ldiriladi, imtihondan
    # o'tganda ko'tariladi.
    subject = Column(String, nullable=True)
    level = Column(String, nullable=True)
    # ---- REFERAL (2026-08-28, Jahongir: "o'quvchiga maxsus link
    # beriladi ... do'sti to'lov qilgandan keyin chegirma oladi") ----
    # ref_code — do'stga yuboriladigan havoladagi qisqa kod
    # (jonyos.uz/r/JONY-7KQ2). public_id emas: u ichki raqam va
    # tashqariga chiqmasligi kerak. Kod O'ZGARMAYDI — bola linkni
    # bir marta tarqatib, keyin ham ishlab tursin.
    ref_code = Column(String, unique=True, index=True, nullable=True)
    # Kim taklif qilgan. Lid orqali ham topsa bo'lardi, lekin to'g'ridan
    # to'g'ri ustun bo'lgani ancha ishonchli: lid arxivlansa yoki
    # birlashtirilsa ham bog'lanish yo'qolmaydi.
    referred_by_student_id = Column(Integer, ForeignKey("students.id"),
                                    nullable=True, index=True)
    # O'quvchining o'z hisobiga bog'lanish. Bo'lsa — u kirib coin
    # balansini ko'radi va sovg'a so'ray oladi.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    note = Column(Text, nullable=True)
    # ESKI NARX HIMOYASI (2026-08-15, Jahongir: "bizda o'qib turganlar
    # uchun faol bolib turganlar uchun sentabrdan narx eski narxda
    # qoladi faqat yangilar uchun yoki avgust muzlatib keyin yana
    # kelganlarga narx oshgan bolishi kerak").
    #
    # Narx oshirilganda O'SHA PAYTDA FAOL bo'lgan o'quvchining narxi
    # shu yerga qulflanadi va uning hisobi shu narxda ketaveradi.
    # Muzlatilsa yoki chiqib ketsa qulf OCHILADI - qaytib kelsa
    # o'sha paytdagi (yangi) narxda o'qiydi. Yangi kelganlarda bu
    # maydon bo'sh - ular doim joriy narxda.
    locked_lesson_price = Column(Float, nullable=True)
    locked_price_at = Column(DateTime, nullable=True)
    locked_price_note = Column(String, nullable=True)

    # Telegram: ota-ona botga /start KOD yozganda chat bog'lanadi va
    # "darsga kelmadi", "to'lov qabul qilindi" xabarlari boradi.
    tg_code = Column(String, nullable=True, index=True)
    telegram_chat_id = Column(String, nullable=True)
    # Ota-ona sahifasi: login-siz, taxmin qilib bo'lmaydigan havola.
    parent_token = Column(String, nullable=True, index=True)
    # Havola muddati (roles.PARENT_TOKEN_VALIDITY_DAYS). NULL = eski
    # (muddat tizimidan oldingi) token - hali muddati tugamagan deb
    # hisoblanadi, birinchi murojaatda backfill qilinadi (students.py:
    # parent_link()).
    parent_token_expires_at = Column(DateTime, nullable=True)
    # Oxirgi tahrir vaqti — ikki xodim bir vaqtda tahrirlaganda
    # "oxirgisi yutadi" o'rniga ogohlantirish berish uchun.
    updated_at = Column(DateTime, nullable=True)
    # Guruhdan qarzdorligicha chiqarilgan: qarz to'langach AVTOMAT
    # arxivga o'tadi. Ungacha "guruhsiz" bo'lib ro'yxatda turadi.
    archive_when_paid = Column(Integer, default=0)
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
    # Summa tahrirlangan oxirgi vaqt — parallel tahrirda 409 uchun.
    updated_at = Column(DateTime, nullable=True)
    # DUBL HIMOYASI (2026-08-14, Jahongir: "Tugma ikki marta bosilsa
    # yoki internet uzilib qayta yuborilsa — ikkita to'lov tushadi").
    # Brauzer har bir forma uchun bitta tasodifiy kalit yuboradi.
    # Ayni kalit bilan ikkinchi so'rov kelsa — YANGI yozuv ochilmaydi,
    # birinchisining o'zi qaytariladi. Ya'ni necha marta bosilsa ham
    # natija bitta to'lov (idempotentlik).
    client_key = Column(String, unique=True, index=True, nullable=True)
    # HAQIQATDA qachon kiritilgani (server vaqti). created_at "to'lov
    # sanasi" bo'lib, eski sana bilan kiritilganda orqaga suriladi —
    # shuning uchun rostakam kiritilish vaqti alohida saqlanadi
    # (Jahongir, 2026-08-12: "kim va qaysi soatda kirgizganligi aniq
    # ko'rinib tursin sekundlarigacha").
    entered_at = Column(DateTime, nullable=True)

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
    # BEKOR QILINGAN DARS (2026-08-19, Jahongir: "darsni bekor qilish
    # funsiyasini ham qoshib ber... Dam kunlari darslar bo'lmaydi va bu
    # darslar umuman hisoblanmaydi"). O'chirilmaydi - belgilanadi:
    # rejadan, davomatdan va oylik bo'luvchisidan chiqadi, lekin iz
    # qoladi (kim, qachon, nima sabab).
    cancelled = Column(Integer, default=0)
    cancel_note = Column(String, nullable=True)
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
    # Qaysi kontentdan kelgani. Sotuvgacha bo'lgan yo'l shu orqali
    # kuzatiladi: kontent -> murojaat -> lead -> to'lov.
    content_id = Column(Integer, ForeignKey("contents.id"),
                        nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    # REFERAL: qaysi o'quvchining havolasidan kelgan (2026-08-28).
    # Shu ustun bo'lmasa "kim olib keldi" savoli javobsiz qoladi.
    referrer_student_id = Column(Integer, ForeignKey("students.id"),
                                 nullable=True, index=True)
    social_message_id = Column(Integer, nullable=True)
    converted_student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch = relationship("Branch")
    assigned_user = relationship("User")
    # 2026-08-28: leads -> students ga endi IKKITA yo'l bor
    # (converted_student_id va referrer_student_id), shuning uchun
    # SQLAlchemy'ga qaysi ustun ekanini aniq aytish SHART. Aytilmasa
    # butun model qatlami ishga tushmaydi.
    converted_student = relationship("Student",
                                     foreign_keys=[converted_student_id])
    referrer_student = relationship("Student",
                                    foreign_keys=[referrer_student_id])


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
    # OYLIK: qaysi xodimga berilgani (ustoz bo'lmagan xodimlar uchun —
    # ustoznikilar TeacherPayment jadvalida). Shu bog'lanish tufayli
    # xodim kartasida "oylik berilgan" ko'rinadi (Jahongir,
    # 2026-08-12: "nargi tomonlardagi joylarda ham oylik berilganligi
    # korinsin").
    staff_user_id = Column(Integer, ForeignKey("users.id"), nullable=True,
                           index=True)
    # SONI va qaysi mahsulot: "3 ta Round-up 5" kabi. Kitob/marker
    # olinganda ombor qoldig'i shu orqali oshadi.
    qty = Column(Float, nullable=True)
    consumable_id = Column(Integer, ForeignKey("consumables.id"),
                           nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    branch = relationship("Branch")
    staff = relationship("User", foreign_keys=[staff_user_id])
    consumable = relationship("Consumable")


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
    # Uy vazifasi: null = tekshirilmagan, 0 = bajarmadi, 1 = bajardi,
    # 2 = qisman. Davomat bilan BIR VAQTDA belgilanadi — ustoz alohida
    # oyna ochib yurmasin, aks holda hech qachon to'ldirilmaydi.
    homework = Column(Integer, nullable=True)
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
    # O'TISH BALLI (2026-09-10, Jahongir: "Maksimal ball bor o'tish
    # balli yo'qku"). Foizda. Qiymat test YARATILGANDA sozlamadan
    # (ExamPassRule) ko'chirib olinadi va shu yerda MUHRLANADI —
    # keyinchalik sozlama o'zgarsa, allaqachon o'tkazilgan testlarning
    # "o'tdi/o'tmadi"si va ustoz ko'rsatkichi o'zgarib ketmaydi
    # (narx qulfi bilan bir xil mantiq).
    # NULL = eski testlar: ular avvalgi qotirilgan chegaralarda qoladi.
    pass_percent = Column(Float, nullable=True)
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

    # Kim o'tkazgani — examiner oyligi shu ustunga bog'lanadi.
    # Buyurtmani qabul qilganda yoki natija kiritganda avtomat to'ladi.
    examiner_id = Column(Integer, ForeignKey("users.id"), nullable=True,
                         index=True)
    # Bajarilmagan ish jarimalari (bo'lim boshliqlari belgilaydi):
    # LC UP kiritilmagan, coin berilmagan, jadvaldan necha soat kechikkan.
    penalty_lc_up = Column(Integer, default=0)
    penalty_coin = Column(Integer, default=0)
    penalty_delay_hours = Column(Float, default=0)
    penalty_note = Column(Text, nullable=True)
    penalty_by = Column(String, nullable=True)

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
    # RETAKE (qayta topshirish) - examiner keyin qayta olishi mumkin.
    # Birinchi ball O'ZGARMAYDI va ko'rinib turadi; retake uchun coin
    # umuman berilmaydi, guruh o'rtachasiga ham kirmaydi (Jahongir).
    retake_score = Column(Float, nullable=True)
    retake_band = Column(Float, nullable=True)
    retake_percent = Column(Float, nullable=True)
    retake_at = Column(Date, nullable=True)
    retake_by = Column(String, nullable=True)
    # 0 = umumiy o'rtachaga KIRMAYDI (imtihongacha birorta ham
    # yo'qlamasi bo'lmagan yangi o'quvchi). None/1 = kiradi.
    counted = Column(Integer, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    exam = relationship("Exam", back_populates="results")
    student = relationship("Student")


class ExamPassRule(Base):
    """TEST TURI BO'YICHA O'TISH BALLI (2026-09-10).

    Jahongir: "Maksimal ball bor o'tish balli yo'qku" -> "test turi
    boyivha sozlamalarda bir marta, foizda olchanadi, 65% unit testda
    60% esa mid va end courselarda".

    Bitta tur - bitta qator. Mock uchun qator yo'q: u IELTS band bilan
    baholanadi, o'tish foizi qo'llanmaydi.

    Bu jadval faqat STANDART qiymat beradi: test yaratilganda qiymat
    Exam.pass_percent ga ko'chiriladi va o'sha yerda muhrlanadi.
    Shuning uchun bu yerdagi raqamni o'zgartirish o'tib ketgan
    testlarning natijasini qayta hisoblab yubormaydi."""
    __tablename__ = "exam_pass_rules"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String, unique=True, index=True, nullable=False)
    percent = Column(Float, nullable=False)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


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

    # COINGA CHEGIRMA (2026-08-15, Jahongir: "oquvchilar o'z profilidan
    # kirib Jony Shopda coiniga skidka sotib olsa avtomat balansida shu
    # narsa ozgarsin").
    #   kind="gift"     — oddiy sovg'a, qo'lga beriladi (odatiy);
    #   kind="discount" — o'quv to'loviga chegirma, ODAM ARALASHMAYDI:
    #                     coin yechiladi va balans o'zi to'g'rilanadi.
    kind = Column(String, default="gift", index=True)
    discount_percent = Column(Float, nullable=True)   # oylikdan foiz
    discount_amount = Column(Float, nullable=True)    # yoki qat'iy so'm

    # MAHSULOT RASMI (2026-08-20, Jahongir: "menga shopdagi korinish
    # umuman yoqmadi, o'sha narsani rasmi bo'lishi kerak"). Havola
    # yoki data-URL. Bo'sh bo'lsa ilova nomiga qarab tayyor rasmni
    # o'zi topadi, topolmasa chiroyli ikonka chiqaradi.
    image = Column(Text, nullable=True)

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

    # ---- HR moduli kengaytmasi ----
    public_id = Column(String, unique=True, index=True)     # VAC-000007
    department_id = Column(Integer, ForeignKey("departments.id"),
                           nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"),
                         nullable=True, index=True)
    request_id = Column(Integer, ForeignKey("staff_requests.id"),
                        nullable=True)
    hiring_manager_id = Column(Integer, ForeignKey("users.id"),
                               nullable=True)
    recruiter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employment_type = Column(String, nullable=True)
    work_schedule = Column(String, nullable=True)
    duties = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    experience_years = Column(Float, nullable=True)
    education = Column(String, nullable=True)
    language_level = Column(String, nullable=True)
    certificates = Column(String, nullable=True)
    probation_months = Column(Integer, nullable=True)
    kpi_note = Column(Text, nullable=True)
    priority = Column(String, default="normal", index=True)
    opened_on = Column(Date, nullable=True)
    target_close = Column(Date, nullable=True)
    close_reason = Column(String, nullable=True)
    hired_count = Column(Integer, default=0)

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
    # ONA TILI (2026-08-16, Jahongir: "ona tili yo boshqa sertifikatlar
    # kiritib bo'lmayabdi"). Til darajasi ro'yxati ingliz tiliga
    # mo'ljallangan edi — ona tili va boshqa tillar uchun joy yo'q edi.
    native_language = Column(String, nullable=True)
    expected_salary = Column(Float, nullable=True)
    trial_score = Column(Float, nullable=True)       # probniy dars bahosi (0-10)
    interview_score = Column(Float, nullable=True)   # intervyu bahosi (0-10)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    reference_note = Column(Text, nullable=True)     # tavsiyanoma
    decision = Column(String, nullable=True, default="pending")

    # QAYSI LAVOZIMGA VA QAYSI FANDAN (2026-08-15, Jahongir: "BU
    # ROYXATDA QAYSI VAKANSIYANI TANLAGANI KO'RINIB TURSIN USTOZ
    # TANLASA QAYSI FANLIGI HAM").
    #
    # Ilgari bu ma'lumot faqat onlayn arizaning IZOH matni ichida
    # yotardi ("LAVOZIM: Ustoz", "Qaysi fandan dars beradi: ..."),
    # shuning uchun ro'yxatda "—" ko'rinardi va filtr ham qilib
    # bo'lmasdi. Endi alohida maydonda — ko'rinadi ham, saralanadi ham.
    position = Column(String, nullable=True, index=True)   # roles.APPLY_POSITIONS
    subject = Column(String, nullable=True)                # ustoz uchun fan

    # ARIZA SAVOLLARI (2026-08-15, Jahongir: "yangi nomzod qo'lda
    # ochsam biz link jo'natib so'rovnomadagi savollar chiqmas ekan,
    # qo'lda kiritsa ham shu savollar chiqishi kerak").
    # Ilgari bu javoblar faqat ONLAYN arizada, u ham bo'lsa izoh
    # matni ichida yig'ilardi. Endi alohida maydonlarda — qo'lda
    # kiritilsa ham, havola orqali kelsa ham bir xil joyda turadi
    # va keyin tahrirlash mumkin.
    address = Column(String, nullable=True)          # yashash manzili
    birth_date_text = Column(String, nullable=True)  # tug'ilgan sana (matn)
    education = Column(String, nullable=True)        # ma'lumoti
    marital = Column(String, nullable=True)          # oilaviy holati
    socials = Column(String, nullable=True)          # ijtimoiy tarmoqlar
    work_duration = Column(String, nullable=True)    # qancha ishlamoqchi

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
    # Support darsi QAYSI kun/vaqtda o'tilishi — jadval shunga quriladi.
    # Asosiy dars vaqti EMAS: support o'z vaqtida alohida o'tadi.
    days = Column(String, nullable=True)
    start = Column(String, nullable=True)
    end = Column(String, nullable=True)
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
    # 2026-08-12, Jahongir: "individual ruxsat berilganlarga ko'rinmasin" -
    # yashirin chegirma o'quvchi/ota-ona portalida KO'RSATILMAYDI,
    # faqat xodimlarga ko'rinadi.
    hidden = Column(Integer, default=0)
    # DO'KON CHEGIRMASI (2026-08-15): qaysi OYGA tegishli va balansga
    # allaqachon tushirilganmi. 15-kungacha sotib olinsa shu oy,
    # keyin — keyingi oy (period = "YYYY-MM").
    period = Column(String, nullable=True, index=True)
    applied_at = Column(DateTime, nullable=True)

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
    # QAYSI FILIALDAN berildi (2026-09-16, Jahongir: "2ta filialda
    # ishlaydigan xodimlarni oyligi qaysi filialdan turib kiritsa o'sha
    # filialga tushsin"). Bo'sh bo'lsa (eski yozuv) — ustozning asosiy
    # filiali hisoblanadi.
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True,
                       index=True)
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
    # MAQSAD BALLI (2026-08-18, Jahongir: "o'quvchilar kirganda target
    # ballini kirgizsa uni progressidan kelib chiqib shu ballni olishga
    # qancha vaqt qolganligni korsatib tursin"). O'quvchining o'zi
    # qo'yadi, ilova unga yetish vaqtini hisoblab turadi.
    xp_target = Column(Float, nullable=True)
    # 2026-08-18 (Jahongir: "nechi XP emas IELTS nechi olmoqchiligi
    # bolishi kerak") - maqsad endi IELTS ballida saqlanadi.
    ielts_target = Column(Float, nullable=True)
    study_hours_per_day = Column(Integer, nullable=True)
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
    # Nomzodni sinash bosqichi: before (o'z holicha) -> coached
    # (tushuntirilgandan keyin). Ikkalasi orasidagi FARQ eng muhim
    # signal bo'ladi.
    stage = Column(String, nullable=True, default="before")
    attempt = Column(Integer, default=1)
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


# =====================================================================
#  SMM: KONTENT QUVURI
#
#  Har bir kontent g'oyadan natijagacha bitta yo'ldan o'tadi. Shuning
#  uchun "bugun nima post qilamiz?" degan savol yo'qoladi: tizim
#  vazifani, muddatni va tasdiqlovchini o'zi ko'rsatib turadi.
# =====================================================================
class Content(Base):
    __tablename__ = "contents"

    id = Column(Integer, primary_key=True, index=True)
    # CONTENT-JA-2026-0048 — atributsiya shu raqamga bog'lanadi
    content_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    platform = Column(String, nullable=True)
    fmt = Column(String, nullable=True)              # format
    pillar = Column(String, nullable=True, index=True)
    goal = Column(String, nullable=True)
    funnel = Column(String, nullable=True)
    audience = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True, index=True)
    course = Column(String, nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"),
                         nullable=True, index=True)
    # Bitta asosiy kontentdan boshqa platformalar uchun variant
    parent_id = Column(Integer, ForeignKey("contents.id"), nullable=True)

    status = Column(String, nullable=False, default="idea", index=True)
    planned_date = Column(Date, nullable=True, index=True)
    planned_time = Column(String, nullable=True)
    published_at = Column(DateTime, nullable=True)

    # Mas'ullar
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    copywriter_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    designer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    videographer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # ---- Brief ----
    problem = Column(Text, nullable=True)            # asosiy muammo
    message = Column(Text, nullable=True)            # asosiy xabar
    hook = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    participants = Column(Text, nullable=True)
    props = Column(Text, nullable=True)
    duration = Column(String, nullable=True)
    music = Column(String, nullable=True)
    design_format = Column(String, nullable=True)
    cta = Column(Text, nullable=True)
    references = Column(Text, nullable=True)
    deadline = Column(Date, nullable=True)

    # KONTENT-PLAN USTUNLARI (2026-08-27).
    # Jahongir "idealniy kontent plan" deb Excel yubordi; unda
    # bizda bo'lmagan to'rt ustun bor edi. Ular shu yerda:
    #   proof      — DALIL: fikrni nima tasdiqlaydi (raqam, natija,
    #                sertifikat). Dalilsiz post ishonch bermaydi.
    #   shoot_date — SYOMKA sanasi. Joylash sanasidan boshqa: bir
    #                kunda bir necha post uchun birga suratga olinadi
    #                ("batch №1").
    #   kpi_target — KUTILAYOTGAN natija ("8k ko'rish, 100 ulashish").
    #                Fakt bilan solishtirish uchun.
    #   conclusion — XULOSA: nima ishladi, nima ishlamadi. Keyingi
    #                oyning rejasi shundan tug'iladi.
    proof = Column(Text, nullable=True)
    shoot_date = Column(Date, nullable=True)
    kpi_target = Column(String, nullable=True)
    conclusion = Column(Text, nullable=True)
    # Seriya: "Ustoz-serial №1", "Bekobod hayoti №2" kabi turkumlar
    series = Column(String, nullable=True, index=True)

    # ---- Matn (joriy versiya) ----
    script = Column(Text, nullable=True)
    caption = Column(Text, nullable=True)
    caption_ru = Column(Text, nullable=True)
    caption_en = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    story_text = Column(Text, nullable=True)
    on_video_text = Column(Text, nullable=True)

    # ---- Joylash ----
    post_url = Column(String, nullable=True)
    post_external_id = Column(String, nullable=True)
    utm = Column(String, nullable=True)
    short_link = Column(String, nullable=True)
    promo_code = Column(String, nullable=True)
    screenshot = Column(Text, nullable=True)

    # ---- Rozilik ----
    needs_consent = Column(Integer, default=0)       # o'quvchi rasmi bormi
    consent_ok = Column(Integer, default=0)

    priority = Column(String, default="normal")
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    branch = relationship("Branch")
    versions = relationship("ContentVersion", back_populates="content",
                            cascade="all, delete-orphan")
    shots = relationship("ContentShot", back_populates="content",
                         cascade="all, delete-orphan")
    approvals = relationship("ContentApproval", back_populates="content",
                             cascade="all, delete-orphan")


class ContentVersion(Base):
    """Matn versiyalari. Kimdir o'zgartirsa eski variant yo'qolmaydi."""
    __tablename__ = "content_versions"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"),
                        nullable=False, index=True)
    field = Column(String, nullable=False)           # script | caption ...
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    changed_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    content = relationship("Content", back_populates="versions")


class ContentShot(Base):
    """Video uchun kadrlar ro'yxati. Videograf har birini belgilaydi."""
    __tablename__ = "content_shots"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"),
                        nullable=False, index=True)
    order_no = Column(Integer, default=0)
    text = Column(Text, nullable=False)
    state = Column(String, default="todo")    # todo | done | retake
    note = Column(String, nullable=True)

    content = relationship("Content", back_populates="shots")


class ContentApproval(Base):
    """Tasdiqlash qadami. Kontent tasdiqsiz chiqib ketmaydi."""
    __tablename__ = "content_approvals"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"),
                        nullable=False, index=True)
    role = Column(String, nullable=True)             # kim tasdiqlashi kerak
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decision = Column(String, nullable=True)         # approved | changes ...
    comment = Column(Text, nullable=True)
    quote = Column(Text, nullable=True)              # matnning belgilangan qismi
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)

    content = relationship("Content", back_populates="approvals")


class ContentMove(Base):
    """Taqvimda sana ko'chirilishi. Sabab yozilmasa ko'chirilmaydi."""
    __tablename__ = "content_moves"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"),
                        nullable=False, index=True)
    from_date = Column(Date, nullable=True)
    to_date = Column(Date, nullable=True)
    reason = Column(Text, nullable=True)
    moved_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContentIdea(Base):
    """G'oyalar bazasi. Har qanday xodim g'oya yubora oladi, lekin
    SMM tasdiqlamaguncha rejaga tushmaydi."""
    __tablename__ = "content_ideas"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    pillar = Column(String, nullable=True)
    platform = Column(String, nullable=True)
    fmt = Column(String, nullable=True)
    course = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    audience = Column(String, nullable=True)
    reference = Column(Text, nullable=True)
    priority = Column(String, default="normal")
    status = Column(String, default="new", index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    author = Column(String, nullable=True)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContentRequest(Base):
    """Boshqa bo'limdan SMMga so'rov. Masalan: "yangi Elementary
    guruhiga 6 ta o'quvchi kerak"."""
    __tablename__ = "content_requests"

    id = Column(Integer, primary_key=True, index=True)
    from_department = Column(String, nullable=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    requester = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    course = Column(String, nullable=True)
    goal = Column(String, nullable=True)
    offer = Column(Text, nullable=True)
    group_time = Column(String, nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    students_needed = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    deadline = Column(Date, nullable=True)
    platforms = Column(String, nullable=True)        # vergul bilan
    approved_price = Column(Float, nullable=True)
    cta = Column(Text, nullable=True)
    sales_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="new", index=True)
    smm_note = Column(Text, nullable=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class Campaign(Base):
    """Bir nechta kontent bitta kampaniya ichida boshqariladi."""
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    goal = Column(String, nullable=True)
    course = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    audience = Column(String, nullable=True)
    offer = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    target_leads = Column(Integer, nullable=True)
    target_sales = Column(Integer, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    conclusion = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContentMetric(Base):
    """Kontentning natijasi. Integratsiya bo'lmasa SMM qo'lda kiritadi."""
    __tablename__ = "content_metrics"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"),
                        unique=True, index=True, nullable=False)
    reach = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    views = Column(Integer, default=0)
    watch_time = Column(Float, default=0)
    completion = Column(Float, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    profile_visits = Column(Integer, default=0)
    link_clicks = Column(Integer, default=0)
    dms = Column(Integer, default=0)
    # AVTOMAT YIG'ISH (2026-08-27). Jahongir: "link orqali avtomat
    # nechta korildi nechta koment like repost bolgani avtomat
    # hisoboti unga korinsin."
    #   source     — "manual" yoki "auto"
    #   fetched_at — oxirgi marta qachon olingani
    #   fetch_note — olinmasa SABABI (masalan TikTok ochiq API
    #                bermaydi). Jim turgan xato eng yomoni.
    source = Column(String, default="manual")
    fetched_at = Column(DateTime, nullable=True)
    fetch_note = Column(String, nullable=True)
    # Instagram insights "follows": shu postdan kelgan obunachilar
    # (2026-09-26, Jahongir: "shu videodan nechta obunachi keldi")
    follows = Column(Integer, default=0)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class MediaAsset(Base):
    """Media kutubxonasi. "O'sha videoni kim olgandi?" degan savol
    yo'qoladi."""
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    kind = Column(String, nullable=True)
    url = Column(Text, nullable=True)
    attachment_id = Column(Integer, ForeignKey("attachments.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    course = Column(String, nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    event = Column(String, nullable=True)
    taken_on = Column(Date, nullable=True)
    author = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    consent = Column(String, default="pending", index=True)
    consent_until = Column(Date, nullable=True)
    can_download = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  SOCIAL INBOX
#
#  DM, izoh, mention va story javoblari bitta oynaga tushadi. Har bir
#  murojaatning javob vaqti o'lchanadi — kim qancha kutgani ko'rinib
#  turadi.
# =====================================================================
class SocialMessage(Base):
    __tablename__ = "social_messages"

    id = Column(Integer, primary_key=True, index=True)
    channel = Column(String, nullable=False, default="instagram", index=True)
    kind = Column(String, nullable=False, default="dm")
    external_id = Column(String, unique=True, index=True, nullable=True)
    author = Column(String, nullable=True)
    username = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    text = Column(Text, nullable=True)
    # Qaysi kontentdan kelgani — atributsiyaning boshlanishi
    content_id = Column(Integer, ForeignKey("contents.id"),
                        nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    course = Column(String, nullable=True)

    status = Column(String, nullable=False, default="new", index=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True)

    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    first_reply_at = Column(DateTime, nullable=True)
    reply_minutes = Column(Float, nullable=True)
    # Ish vaqtidan tashqari kelganmi — SLA'da alohida hisoblanadi
    off_hours = Column(Integer, default=0)
    reply_text = Column(Text, nullable=True)
    replied_by = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    content = relationship("Content")


class InboxReply(Base):
    """Tezkor javob shabloni. SMM tanlaydi, kerak bo'lsa o'zgartiradi."""
    __tablename__ = "inbox_replies"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    is_active = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class BrandRule(Base):
    """Brend kitob yozuvi. Brandbook PDF'dan seed qilinadi, keyin
    asoschi tahrirlashi mumkin — seed qayta yozib yubormaydi."""
    __tablename__ = "brand_rules"

    id = Column(Integer, primary_key=True, index=True)
    section = Column(String, nullable=False, index=True)   # color/font/logo/tone/spec/dont/contact
    key = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    value = Column(String, nullable=True)          # hex, o'lcham va h.k.
    note = Column(Text, nullable=True)
    kind = Column(String, nullable=True)           # primary/neutral/state, do/dont
    source = Column(String, nullable=True)         # "PDF" yoki "TO'LDIRILDI"
    position = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class BrandCheck(Base):
    """Kontent nashrdan oldin brend bo'yicha tekshirilgani."""
    __tablename__ = "brand_checks"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), index=True)
    key = Column(String, nullable=False)
    ok = Column(Integer, default=0)
    note = Column(Text, nullable=True)
    checked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    checked_at = Column(DateTime, default=datetime.utcnow)


class KbArticle(Base):
    """Bilimlar bazasi. Yangi SMM kelganda nolga qaytmaslik uchun."""
    __tablename__ = "kb_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, default="process", index=True)
    body = Column(Text, nullable=True)
    tags = Column(String, nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    views = Column(Integer, default=0)
    is_pinned = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    reviewed_at = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class SmmReport(Base):
    """Yig'ilgan haftalik/oylik hisobot. Raqamlar saqlanadi —
    keyin ma'lumot o'zgarsa ham hisobot o'zgarmaydi."""
    __tablename__ = "smm_reports"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(String, default="month")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    data = Column(Text, nullable=True)          # JSON
    summary = Column(Text, nullable=True)
    kpi_score = Column(Float, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  HR: BO'LIM VA LAVOZIM
# =====================================================================
class Department(Base):
    """Bo'limlar. roles.DEPARTMENTS dan seed qilinadi, keyin asoschi
    tahrirlaydi — seed qayta yozib yubormaydi."""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    head_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    position = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class Position(Base):
    """Lavozimlar. Har bir lavozim tizimdagi rolga bog'lanadi —
    xodim yaratilganda roli shundan olinadi."""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"),
                           nullable=True, index=True)
    system_role = Column(String, nullable=True)
    probation_months = Column(Integer, default=2)
    # Sinov darsi majburiymi (ustoz lavozimlarida)
    trial_required = Column(Integer, default=0)
    salary_from = Column(Float, nullable=True)
    salary_to = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    requirements = Column(Text, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  HR: SHTAT REJASI
# =====================================================================
class WorkforcePlan(Base):
    """Filial × bo'lim × lavozim kesimida nechta odam kerak."""
    __tablename__ = "workforce_plans"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=True)
    quarter = Column(Integer, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True,
                       index=True)
    department_id = Column(Integer, ForeignKey("departments.id"),
                           nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"),
                         nullable=True, index=True)

    approved_headcount = Column(Integer, default=0)
    planned_hires = Column(Integer, default=0)
    expected_leaves = Column(Integer, default=0)
    expected_groups = Column(Integer, default=0)
    budgeted_salary = Column(Float, nullable=True)

    note = Column(Text, nullable=True)
    status = Column(String, default="draft", index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


# =====================================================================
#  HR: YANGI XODIM SO'ROVI
# =====================================================================
class StaffRequest(Base):
    """Filial rahbari yangi xodim so'raydi. Tasdiqlanmagan so'rov
    bo'yicha vakansiya ochilmaydi."""
    __tablename__ = "staff_requests"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)   # REQ-000012
    requested_by = Column(Integer, ForeignKey("users.id"), index=True)
    request_date = Column(Date, default=date.today)

    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True,
                       index=True)
    department_id = Column(Integer, ForeignKey("departments.id"),
                           nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"),
                         nullable=True, index=True)
    headcount = Column(Integer, default=1)
    employment_type = Column(String, default="full")
    work_schedule = Column(String, nullable=True)
    needed_from = Column(Date, nullable=True)

    reason = Column(String, nullable=True)
    replacing_user_id = Column(Integer, ForeignKey("users.id"),
                               nullable=True)
    salary_from = Column(Float, nullable=True)
    salary_to = Column(Float, nullable=True)
    requirements = Column(Text, nullable=True)
    certificates = Column(String, nullable=True)
    experience_years = Column(Float, nullable=True)
    duties = Column(Text, nullable=True)
    kpi_note = Column(Text, nullable=True)
    priority = Column(String, default="normal", index=True)

    status = Column(String, default="draft", index=True)
    reject_reason = Column(Text, nullable=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class RequestApproval(Base):
    """Tasdiqlash zanjirining har bir qadami. O'chirilmaydi —
    kim, qachon, nima uchun qaror qilgani tarixda qoladi."""
    __tablename__ = "request_approvals"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("staff_requests.id"),
                        index=True)
    step = Column(String, nullable=False)        # hr_review, budget_review…
    decision = Column(String, nullable=False)    # approved / rejected
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow)
    note = Column(Text, nullable=True)


# =====================================================================
#  DARS KO'CHIRISH
# =====================================================================
class LessonReschedule(Base):
    """Dars boshqa kunga ko'chirildi. Yozuv O'CHIRILMAYDI — kvota shu
    tarixdan hisoblanadi va "kim qancha surgan" savoli javobsiz
    qolmaydi."""
    __tablename__ = "lesson_reschedules"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False,
                      index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True,
                        index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)

    from_date = Column(Date, nullable=False, index=True)
    to_date = Column(Date, nullable=False)
    from_time = Column(String, nullable=True)
    to_time = Column(String, nullable=True)

    reason = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    # auto | pending | approved | rejected | cancelled
    status = Column(String, default="pending", index=True)
    # Kvota ichida bo'lgani uchun avtomat ruxsat berildimi
    auto_approved = Column(Integer, default=0)
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_note = Column(Text, nullable=True)

    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  O'RINBOSAR USTOZ
# =====================================================================
class Substitution(Base):
    """Bir ustoz boshqasining darsini o'tib beradi. Ish haqi darsni
    HAQIQATDA o'tgan ustozga yoziladi (Lesson.teacher_id)."""
    __tablename__ = "substitutions"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False,
                      index=True)
    lesson_date = Column(Date, nullable=False, index=True)
    lesson_time = Column(String, nullable=True)
    original_teacher_id = Column(Integer, ForeignKey("teachers.id"),
                                 nullable=True, index=True)
    substitute_teacher_id = Column(Integer, ForeignKey("teachers.id"),
                                   nullable=True, index=True)
    reason = Column(String, nullable=True)
    note = Column(Text, nullable=True)
    status = Column(String, default="offered", index=True)
    reschedule_id = Column(Integer, ForeignKey("lesson_reschedules.id"),
                           nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)


# =====================================================================
#  KITOB BUYURTMASI
# =====================================================================
class BookOrder(Base):
    """Ustoz kitob so'raydi. So'rov filial rahbariga vazifa bo'lib
    boradi — og'zaki iltimos yo'qoladi, vazifa yo'qolmaydi."""
    __tablename__ = "book_orders"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)      # BOOK-000042
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True,
                        index=True)
    requested_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True,
                       index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    needed_by = Column(Date, nullable=True)
    urgency = Column(String, default="normal")
    note = Column(Text, nullable=True)
    status = Column(String, default="new", index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_note = Column(Text, nullable=True)
    delivered_at = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class BookOrderItem(Base):
    """Buyurtmadagi bitta kitob: qaysi kitob va nechta."""
    __tablename__ = "book_order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("book_orders.id"), index=True)
    # Omborda bor kitob bo'lsa bog'lanadi, bo'lmasa nomi qo'lda yoziladi
    consumable_id = Column(Integer, ForeignKey("consumables.id"),
                           nullable=True)
    title = Column(String, nullable=False)
    level = Column(String, nullable=True)
    qty = Column(Integer, nullable=False, default=1)
    delivered_qty = Column(Integer, default=0)
    note = Column(String, nullable=True)


class ExamOrder(Base):
    """Ustozning imtihon buyurtmasi.

    Ilgari ustoz imtihonni "qoralama" qilib yaratardi va u examiner
    ro'yxatni ochgunicha kutib turardi. Endi buyurtma alohida yozuv:
    kim so'ragani, qachonga so'ragani, kim qabul qilgani va nima uchun
    rad etilgani — hammasi bir joyda va tarixda qoladi.
    """
    __tablename__ = "exam_orders"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False,
                      index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)

    # So'ralgan vaqt
    date = Column(Date, nullable=False, index=True)
    time = Column(String)                      # "15:30"
    kind = Column(String, default="unit")      # unit | mid | end | mock
    unit_no = Column(Integer)
    # Buyurtma paytidagi o'quvchilar soni — keyin o'zgarsa ham
    # examiner nechta odamga tayyorlanganini biladi
    students_count = Column(Integer, default=0)
    note = Column(Text)

    status = Column(String, default="new", index=True)
    accepted_by = Column(Integer, ForeignKey("users.id"))
    accepted_at = Column(DateTime)
    decision_note = Column(Text)
    reject_reason = Column(String)

    # Qabul qilingach yaratiladigan haqiqiy imtihon
    exam_id = Column(Integer, ForeignKey("exams.id"))

    requested_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  HR FAZA 2B — ATS
# =====================================================================
class StudentGroupLink(Base):
    """O'QUVCHI <-> GURUH bog'lanishi (2026-08-17).

    Jahongir: "Abduvaliyeva Munisa degan qiz 2ta gruppaga keladi,
    shuning uchun ham biz ham bazda 2ta gruppa qilishimiz kerak".

    Ilgari o'quvchida BITTA guruh bo'lardi (Student.group_id). Ikki
    fanga qatnaydigan bola ikki marta kiritilardi — natijada faol
    o'quvchilar soni, qarz va hisobotlar ikki barobar ko'rinardi
    (Bekobod 2 da 3 ta shunday yozuv topildi).

    MUHIM — BOSQICHMA-BOSQICH: Student.group_id O'CHIRILMADI. U endi
    "asosiy guruh" bo'lib qoladi va shu jadvaldagi birinchi faol
    bog'lanishga teng turadi. Shu sababli mavjud 27 ta joydagi eski
    so'rovlar (hisob-kitob, yo'qlama, ustoz oyligi) ishlayveradi —
    ular keyingi bosqichlarda bittalab ko'chiriladi.
    """
    __tablename__ = "student_groups"
    __table_args__ = (
        UniqueConstraint("student_id", "group_id",
                         name="uq_student_group"),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"),
                      nullable=False, index=True)
    # Asosiy guruh — Student.group_id shunga teng turadi
    is_primary = Column(Integer, default=0)
    joined_date = Column(Date, nullable=True)
    left_date = Column(Date, nullable=True)
    active = Column(Integer, default=1, index=True)
    # Shu guruh uchun alohida narx (bo'sh = guruh narxi)
    lesson_price = Column(Float, nullable=True)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student")
    group = relationship("Group")


class HrOption(Base):
    """HR ro'yxatlariga QO'LDA qo'shiladigan variantlar (2026-08-16).

    Jahongir: "tagidan qo'shadigan qilish kerak til darajasini
    nomzodlarda hr bo'limida, ona tili yo boshqa sertifikatlar
    kiritib bo'lmayabdi".

    Ilgari til darajasi ro'yxati kodda qattiq yozilgan edi
    (roles.LANGUAGE_LEVELS): A1..C2 va IELTS. TOEFL, CEFR C2
    sertifikati, rus tili darajasi yoki "ona tili" kabi narsalarni
    kiritib bo'lmasdi — har safar dasturchi kerak bo'lardi.

    Endi HR o'zi qo'sha oladi. Kodda yozilganlari JOYIDA QOLADI
    (eski yozuvlar buzilmasin), bu jadval faqat USTIGA qo'shiladi.

    kind — qaysi ro'yxat ("language_level" va kelajakda boshqalar).
    """
    __tablename__ = "hr_options"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String, nullable=False, index=True)
    # key — saqlanadigan qiymat, label — ekranda ko'rinadigani.
    key = Column(String, nullable=False)
    label = Column(String, nullable=False)
    position = Column(Integer, default=0)
    active = Column(Integer, default=1)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateApplication(Base):
    """Bitta odamning bitta vakansiyaga arizasi.

    Bosqich AYNAN SHU YERDA saqlanadi, nomzodning o'zida emas: bir
    odam ustozlikka rad etilib, administratorlikka olinishi mumkin.
    Bosqich odamda tursa, u ikkinchi vakansiyada ham "rad etilgan"
    bo'lib qolardi va yaxshi nomzod behuda yo'qolardi.
    """
    __tablename__ = "candidate_applications"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)

    candidate_id = Column(Integer, ForeignKey("candidates.id"),
                          nullable=False, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)

    stage = Column(String, default="new", index=True)
    # Bosqich qachon o'zgargani — SLA shu bo'yicha hisoblanadi
    stage_since = Column(Date)
    source = Column(String)

    reject_reason = Column(String)
    reject_note = Column(Text)
    # Rad etilgan, lekin sababi nomzodda emas — keyin qaytarish mumkin
    pool = Column(Integer, default=0)
    pool_note = Column(Text)

    owner_id = Column(Integer, ForeignKey("users.id"))
    note = Column(Text)
    closed_at = Column(Date)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class ApplicationStageLog(Base):
    """Bosqich tarixi. Kim, qachon, qayerdan qayerga ko'chirgan.

    Bu voronka analitikasining yagona ishonchli manbai: "suhbatdan
    keyin qancha odam yo'qoladi" degan savolga faqat shu jadval
    javob bera oladi."""
    __tablename__ = "application_stage_logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer,
                            ForeignKey("candidate_applications.id"),
                            nullable=False, index=True)
    from_stage = Column(String)
    to_stage = Column(String, index=True)
    # Oldingi bosqichda necha kun turgan
    days_in_stage = Column(Integer)
    reason = Column(String)
    note = Column(Text)
    by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Interview(Base):
    """Suhbat: qachon, kim bilan, qanday o'tdi."""
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)

    application_id = Column(Integer,
                            ForeignKey("candidate_applications.id"),
                            nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)

    kind = Column(String, default="hr")
    date = Column(Date, index=True)
    time = Column(String)
    minutes = Column(Integer)
    place = Column(String)
    room_id = Column(Integer, ForeignKey("rooms.id"))

    interviewer_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(String, default="planned", index=True)
    note = Column(Text)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Scorecard(Base):
    """Suhbatdan keyingi baholash varaqasi.

    Foiz SERVERDA og'irlikli o'rtacha bilan hisoblanadi — qo'lda
    yozib bo'lmaydi, aks holda har kim o'zicha hisoblab, taqqoslash
    ma'nosini yo'qotardi."""
    __tablename__ = "scorecards"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer,
                            ForeignKey("candidate_applications.id"),
                            nullable=False, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"), index=True)

    author_id = Column(Integer, ForeignKey("users.id"), index=True)
    # {"subject": 4, "method": 5, ...}
    scores = Column(Text)
    percent = Column(Float)
    recommendation = Column(String)
    strengths = Column(Text)
    concerns = Column(Text)
    note = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class Offer(Base):
    """Nomzodga yozma taklif. Har o'zgartirish yangi VERSIYA bo'lib
    saqlanadi — muzokara tarixi hech qachon yo'qolmaydi."""
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)

    application_id = Column(Integer,
                            ForeignKey("candidate_applications.id"),
                            nullable=False, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)

    version = Column(Integer, default=1)
    # Oldingi versiya — zanjir shu orqali o'qiladi
    previous_id = Column(Integer, ForeignKey("offers.id"))

    position = Column(String)
    salary = Column(Float)
    salary_note = Column(String)          # "oyiga, qo'lga tegadi"
    start_date = Column(Date)
    probation_months = Column(Integer)
    terms = Column(Text)

    status = Column(String, default="draft", index=True)
    valid_until = Column(Date)
    decline_reason = Column(Text)

    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    sent_at = Column(DateTime)
    answered_at = Column(DateTime)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  HR FAZA 3 — XODIM HAYOTIY SIKLI
# =====================================================================
class EmployeeDocument(Base):
    """Xodim hujjati. Muddati tugaydiganlari (pasport, sertifikat,
    shartnoma) tugashidan oldin HRga ogohlantirish chiqaradi."""
    __tablename__ = "employee_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    kind = Column(String, nullable=False)
    title = Column(String)
    number = Column(String)
    issued_on = Column(Date)
    expires_on = Column(Date, index=True)
    file = Column(Text)                      # base64 yoki yo'l
    note = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class ProbationCheck(Base):
    """Sinov muddati nazorati: har oy alohida xulosa. Yakuniy qaror
    (passed/failed) qo'yilgach boshqa yozib bo'lmaydi."""
    __tablename__ = "probation_checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    month_no = Column(Integer, default=1)     # sinovning nechanchi oyi
    decision = Column(String, nullable=False)
    strengths = Column(Text)
    concerns = Column(Text)
    note = Column(Text)
    by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class LeaveRequest(Base):
    """Ta'til so'rovi. Ustoz bo'lsa — guruhlariga o'rinbosar
    ko'rsatilishi shart, aks holda darslar egasiz qoladi."""
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)
    kind = Column(String, nullable=False)
    date_from = Column(Date, nullable=False, index=True)
    date_to = Column(Date, nullable=False)
    days = Column(Integer)
    reason = Column(Text)
    # Ustoz uchun: darslarni kim olib turadi
    replacement_teacher_id = Column(Integer, ForeignKey("teachers.id"))
    replacement_note = Column(Text)
    status = Column(String, default="pending", index=True)
    decided_by = Column(Integer, ForeignKey("users.id"))
    decided_at = Column(DateTime)
    decision_note = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  HR FAZA 4 — PERFORMANCE
# =====================================================================
class PerformanceReview(Base):
    """Davriy baholash. YAKUNLANGACH QULFLANADI — tarix qayta
    yozilmaydi, aks holda baholashning qadri qolmaydi."""
    __tablename__ = "performance_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    period = Column(String, index=True)       # "2026-H1"
    scores = Column(Text)                     # {"results": 4, ...}
    percent = Column(Float)
    strengths = Column(Text)
    to_improve = Column(Text)
    goals = Column(Text)
    status = Column(String, default="draft")  # draft | final
    finalized_at = Column(DateTime)
    by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class OneOnOne(Base):
    """1:1 suhbat. Maxfiy bo'lsa — faqat ikkala ishtirokchi o'qiydi,
    HR ham ko'rmaydi. Ishonch shu bilan quriladi."""
    __tablename__ = "one_on_ones"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    manager_id = Column(Integer, ForeignKey("users.id"), index=True)
    date = Column(Date)
    privacy = Column(String, default="open")  # open | private
    notes = Column(Text)
    agreements = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Pip(Base):
    """Natijani yaxshilash rejasi. Jazo emas — oxirgi imkoniyat:
    aniq maqsad, aniq muddat, aniq yakun."""
    __tablename__ = "pips"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    reason = Column(Text)
    goals = Column(Text)
    date_from = Column(Date)
    date_to = Column(Date)
    status = Column(String, default="active")
    outcome_note = Column(Text)
    by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  HR FAZA 5 — MUNOSABATLAR VA KETISH
# =====================================================================
class DisciplinaryCase(Base):
    __tablename__ = "disciplinary_cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    kind = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    date = Column(Date)
    by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Recognition(Base):
    __tablename__ = "recognitions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    kind = Column(String, nullable=False)
    reason = Column(Text)
    amount = Column(Float)
    date = Column(Date)
    by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Offboarding(Base):
    """Ketish jarayoni: bandlar ro'yxati + chiqish suhbati.

    Chiqish suhbatining maqsadi — TIZIMNI tuzatish: sabab "bizga
    bog'liq" bo'lsa (ish haqi, rahbariyat, yuk) bu ustidan ishlash
    mumkin bo'lgan signal."""
    __tablename__ = "offboardings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)
    last_day = Column(Date)
    reason = Column(String)
    steps = Column(Text)                      # {"notice": 1, ...}
    exit_notes = Column(Text)                 # chiqish suhbati
    would_return = Column(Integer)            # 1/0 — qaytarmidi
    completed = Column(Integer, default=0)
    by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class SupportSession(Base):
    """Support teacherning bitta darsi: qaysi guruh, qachondan
    qachongacha, nechta o'quvchi. Oylik shu yozuvlardan AVTOMAT
    hisoblanadi — oy oxirida hech kim qo'lda sanamaydi."""
    __tablename__ = "support_sessions"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"),
                        nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)

    # Yakka dars bo'lsa - kimga (2026-09-23). Guruh darsida bo'sh.
    student_id = Column(Integer, ForeignKey("students.id"), index=True)

    date = Column(Date, nullable=False, index=True)
    start_time = Column(String, nullable=False)   # "14:00"
    end_time = Column(String, nullable=False)     # "15:30"
    minutes = Column(Integer, nullable=False)     # serverda hisoblanadi
    students_count = Column(Integer, nullable=False)
    note = Column(Text)

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class ExaminerAdjustment(Base):
    """Examinerdan qo'lda ball ayirish (ESLATMA qoidasi).

    Bo'lim boshliqlari (Exam, HR, O'quv bo'limi) kamchilik aniqlasa,
    holatga ko'ra munosib ball ayirib tashlashi mumkin. Sabab majburiy —
    oylik hujjatida "nega kam" degan savol qolmasligi kerak."""
    __tablename__ = "examiner_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    date = Column(Date, nullable=False, default=date.today, index=True)
    points = Column(Float, nullable=False)      # ayiriladigan ball (musbat)
    reason = Column(Text, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SupportAdjustment(Base):
    """Support teacherdan jarima ball ayirish — ExaminerAdjustment ning
    egizagi (2026-09-16). HR kamchilik aniqlasa, ball oylikka
    aylantirilishidan oldin ayiriladi. Sabab majburiy."""
    __tablename__ = "support_adjustments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    date = Column(Date, nullable=False, default=date.today, index=True)
    points = Column(Float, nullable=False)      # ayiriladigan ball (musbat)
    reason = Column(Text, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConductViolation(Base):
    """Na'munali xodim: bitta qoidabuzarlik yozuvi (2026-09-16).

    Ayiriladigan ball SAQLANMAYDI — u oy ichidagi tartib raqamidan
    (1-marta, 2-marta ...) hisoblanadi, Excel'dagi kabi. Shunda eski
    yozuv o'chirilsa, keyingilarining bali o'zi to'g'rilanadi.
    Faqat "xayfsan" turida ball qo'lda yoziladi (points)."""
    __tablename__ = "conduct_violations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False,
                     index=True)
    date = Column(Date, nullable=False, index=True)
    kind = Column(String, nullable=False)
    points = Column(Float, nullable=True)       # faqat xayfsan uchun
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class HrBlacklist(Base):
    """HR qora ro'yxati (2026-09-16). Bu yerdagi odam ishga olinmaydi.

    Odam telefon (phone_key — oxirgi 9 raqam) va ism (name_key) bo'yicha
    tanib olinadi. Yozuv O'CHIRILMAYDI: ro'yxatdan chiqarilganda
    is_active=0 bo'ladi va kim, qachon, nega chiqargani saqlanadi."""
    __tablename__ = "hr_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    phone_key = Column(String, nullable=True, index=True)
    name_key = Column(String, nullable=True, index=True)
    category = Column(String, nullable=False, default="other")
    reason = Column(Text, nullable=False)
    candidate_id = Column(Integer, nullable=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    is_active = Column(Integer, nullable=False, default=1, index=True)
    added_by = Column(String, nullable=True)
    added_by_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    removed_by = Column(String, nullable=True)
    removed_at = Column(DateTime, nullable=True)
    remove_reason = Column(Text, nullable=True)


class PlanTarget(Base):
    """Yillik reja — bitta ko'rsatkichning bitta oydagi Reja qiymati.

    year — o'quv yili BOSHLANGAN kalendar yil (sentabr). Fakt saqlanmaydi:
    u har safar tirik ma'lumotdan hisoblanadi, shuning uchun hech qachon
    eskirmaydi."""
    __tablename__ = "plan_targets"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    metric = Column(String, nullable=False, index=True)
    month = Column(Integer, nullable=False)      # 1..12
    value = Column(Float, nullable=False, default=0)
    # 2026-08-11 (Jahongir): "har bir filial uchun alohida reja va
    # fakt bo'ladi" - reja endi filial kesimida. NULL qolmasligi uchun
    # eski yozuvlar bir martalik migratsiyada Bekobod 1 ga biriktiriladi
    # (ular o'sha filial uchun tuzilgan edi).
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class BudgetLine(Base):
    """Budjet qatori: yil-oy-kategoriya kesimida rejalashtirilgan summa.

    kind="income" — daromad rejasi, kind="expense" — xarajat rejasi
    (kategoriya bilan). branch_id bo'sh — butun kompaniya."""
    __tablename__ = "budget_lines"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)   # o'quv yili boshi
    month = Column(Integer, nullable=False)              # 1..12
    kind = Column(String, nullable=False, default="expense")
    category = Column(String, nullable=True)             # xarajat kategoriyasi
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    amount = Column(Float, nullable=False, default=0)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class SmmSalesPlan(Base):
    """Marketolog uchun OYLIK SOTUV REJASI - filial kesimida (so'm).

    Jahongir (2026-08-11): sotuv rejasi bajarilishiga qarab marketolog
    bonusi aniq jadval bo'yicha chiqadi (80% dan 1 mln ... 150%+ da
    8 mln). Reja shu jadvalga kiritiladi, fakt (shu oy tushumi) va
    foiz avtomat hisoblanadi."""
    __tablename__ = "smm_sales_plans"

    id = Column(Integer, primary_key=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False, default=0)
    created_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class NpsResponse(Base):
    """NPS so'rovi javobi (2026-08-12): chorakda bir marta, o'quvchi
    va ota-onadan alohida. teacher_id - javob paytidagi guruh ustozi
    (sifat o'lchovi ustoz kesimida chiqishi uchun)."""
    __tablename__ = "nps_responses"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    who = Column(String, nullable=False, default="student")  # student/parent
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    quarter = Column(String, nullable=False, index=True)      # 2026-Q3
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SeedMark(Base):
    """Bir martalik import/seed bajarilganini belgilaydi.

    Sabab (2026-08-11, Jahongir: "tezroq ishlaydigan qil"): har
    server uyg'onishida katta JSON fayllar (lug'at 733KB, coin tarixi
    647KB...) qayta o'qilib, minglab yozuvlar qayta solishtirilardi -
    sovuq start sekinlashardi. Endi to'liq bajarilgan seed shu yerga
    belgi qo'yadi va keyingi startlarda BITTA yengil so'rov bilan
    o'tkazib yuboriladi. Hech qanday ma'lumot o'chirilmaydi - bu
    faqat "qayta tekshirish shart emas" belgisi. Yangi ma'lumot
    qo'shilsa kod yangi kalit (masalan _v2) bilan keladi."""
    __tablename__ = "seed_marks"

    key = Column(String, primary_key=True)
    done_at = Column(DateTime, default=datetime.utcnow)


class LegacyCollectionMonth(Base):
    """Eski yillardagi oylik to'lov yig'ilishi (reja/fakt) - Google
    Sheets arxividan import. Joriy billing hisobiga aralashmaydi,
    faqat tarixiy ko'rsatkich sifatida Moliya bo'limida ko'rinadi."""
    __tablename__ = "legacy_collection_months"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False)
    # Filialga ID bilan emas, nom bilan bog'lanadi - tarixiy jamlanma
    # filiallar keyin o'zgarsa ham buzilmasin
    branch_label = Column(String, nullable=False, default="Markaz umumiy")
    plan = Column(Float, default=0)   # qancha tushishi kerak edi
    fact = Column(Float, default=0)   # qancha tushdi


class PaymentDue(Base):
    """To'lov kalendari: qachon maosh, ijara, soliq, reklama va
    yetkazib beruvchiga to'lov. recurring=1 — har oy shu kuni."""
    __tablename__ = "payment_dues"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    kind = Column(String, nullable=False, default="other")
    due_day = Column(Integer, nullable=True)     # har oyning kuni (1-31)
    date = Column(Date, nullable=True)           # bir martalik sana
    amount = Column(Float, nullable=False, default=0)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    recurring = Column(Integer, default=1)
    active = Column(Integer, default=1)
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)



class StudentReminder(Base):
    """O'quvchi bo'yicha eslatma. remind_on to'lsa — o'sha kuni
    adminlarga vazifa tushadi (masalan: 'to'lovni so'rang')."""
    __tablename__ = "student_reminders"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    text = Column(Text, nullable=False)
    remind_on = Column(Date, nullable=True, index=True)
    done = Column(Integer, default=0)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class LoginAttempt(Base):
    """Kirish urinishlari — brute-force himoyasi. 15 daqiqada 5 marta
    xato parol tersa, o'sha login vaqtincha bloklanadi."""
    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False, index=True)
    ip = Column(String, nullable=True)
    success = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DeletedPayment(Base):
    """O'CHIRILGAN TO'LOV ARXIVI (2026-08-15).

    Jahongir'ning asosiy qoidasi: "hech narsa o'chmasin". Ilgari xato
    yozuv butunlay o'chib ketardi - faqat audit izohi qolardi, summani
    qaytarib bo'lmasdi. Endi yozuv payments'dan olinadi va SHU YERGA
    ko'chiriladi: kim o'chirdi, qachon, nima sababdan. Kerak bo'lsa
    asoschi bir bosishda qaytaradi.

    Nega alohida jadval, nega "o'chirilgan" bayrog'i emas: balans va
    barcha hisobotlar payments jadvalining yig'indisidan chiqadi.
    Bayroq qo'yilsa, uni FILTRLASHNI unutgan bitta so'rov ham
    hisobotni buzardi. Arxivga ko'chirilganda esa hech qanday hisobot
    o'zgarmaydi - xato qilish imkoniyati yo'q."""
    __tablename__ = "payments_deleted"

    id = Column(Integer, primary_key=True, index=True)
    # payments.id - qaysi yozuv edi (tiklashda o'sha raqam qaytadi)
    payment_id = Column(Integer, index=True, nullable=False)
    public_id = Column(String, nullable=True)
    student_id = Column(Integer, index=True, nullable=True)
    student_name = Column(String, nullable=True)
    branch_id = Column(Integer, nullable=True)
    amount = Column(Float, nullable=False)
    kind = Column(String, nullable=True)
    method = Column(String, nullable=True)
    note = Column(String, nullable=True)
    period = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    entered_at = Column(DateTime, nullable=True)
    client_key = Column(String, nullable=True)
    # --- o'chirish tafsiloti ---
    deleted_by = Column(String, nullable=True)
    deleted_at = Column(DateTime, default=datetime.utcnow, index=True)
    reason = Column(String, nullable=True)
    # Qaytarilgan bo'lsa - qachon va kim
    restored_at = Column(DateTime, nullable=True)
    restored_by = Column(String, nullable=True)


class DeletedLead(Base):
    """O'CHIRILGAN LID ARXIVI (2026-08-30).

    Jahongir: "lidni o'chirishni ham sabablar qo'shib qo'y, ichida
    adashib kiritilib yuborilibdi bo'lsin".

    Ilgari lid BUTUNLAY o'chib ketardi — na yozuvi, na sababi
    qolardi. Endi DeletedPayment bilan bir xil yo'l: yozuv leads
    jadvalidan olinadi va shu yerga ko'chiriladi.

    Nega alohida jadval, nega "o'chirilgan" bayrog'i emas: voronka,
    konversiya va marketing hisobotlari leads jadvalining o'zidan
    chiqadi. Bayroq qo'yilsa, uni filtrlashni unutgan BITTA so'rov
    ham butun statistikani buzardi (adashib kiritilgan lid
    voronkada turib qolardi). Arxivga ko'chirilganda esa hech
    qanday hisobot o'zgarmaydi — xato qilish imkoniyati yo'q."""
    __tablename__ = "leads_deleted"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, index=True, nullable=False)
    public_id = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    source = Column(String, nullable=True)
    stage = Column(String, nullable=True)
    branch_id = Column(Integer, nullable=True, index=True)
    assigned_user_id = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    # --- o'chirish tafsiloti ---
    reason = Column(String, nullable=True, index=True)   # roles.LEAD_DELETE_REASONS
    reason_note = Column(String, nullable=True)          # erkin izoh
    deleted_by = Column(String, nullable=True)
    deleted_at = Column(DateTime, default=datetime.utcnow, index=True)
    restored_at = Column(DateTime, nullable=True)
    restored_by = Column(String, nullable=True)


class PaymentFixRequest(Base):
    """TO'LOVNI TUZATISH SO'ROVI (2026-08-15).

    Jahongir: "masalan sotuv manager tolovni notogri urvordi, shuni
    ozgartirish qilib sorov yuborsa filial rahbari yoki moliyachiga
    borsa yoki asoschiga tasdiqlavorsa ozgarsin, chunki shunaqa holat
    boldi u menga aloqaga chiqadi men uni topaman ozgartiraman vaqt
    ketadi".

    Ilgari to'lovni faqat asoschi/moliya direktori/filial rahbari
    tahrirlay olardi. Sotuv menejeri xato kiritsa — telefon qilib,
    odam qidirib, vaqt ketardi. Endi u SO'ROV yuboradi: so'rov uchala
    tasdiqlovchiga vazifa bo'lib tushadi va kim birinchi bo'lib
    tasdiqlasa — o'zgarish o'zi qo'llanadi.

    Nima o'zgarishi mumkin: summa, to'lov usuli, izoh yoki butunlay
    o'chirish (o'chirilsa arxivga tushadi, yo'qolmaydi)."""
    __tablename__ = "payment_fix_requests"

    id = Column(Integer, primary_key=True, index=True)
    public_id = Column(String, unique=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"),
                        nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)

    # amount | method | note | delete
    kind = Column(String, nullable=False, default="amount")
    old_amount = Column(Float, nullable=True)
    new_amount = Column(Float, nullable=True)
    old_method = Column(String, nullable=True)
    new_method = Column(String, nullable=True)
    new_note = Column(String, nullable=True)
    reason = Column(Text, nullable=False)

    status = Column(String, nullable=False, default="pending", index=True)
    requested_by = Column(String, nullable=True)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    decided_by = Column(String, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    decision_note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    student = relationship("Student")


class ErrorLog(Base):
    """Kutilmagan server xatolari. Foydalanuvchi aytishini kutmasdan
    asoschi o'zi ko'rib turadi (Audit -> Tizim xatolari)."""
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=True)
    method = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ExerciseResult(Base):
    """O'quvchi bajargan mashq natijasi: nechta savol, nechtasi to'g'ri.
    Har to'g'ri javob 1 ball — ball yig'ilib daraja ko'tariladi
    (roles.ENG_LEVELS zinasi)."""
    __tablename__ = "exercise_results"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    date = Column(Date, default=date.today)
    total = Column(Integer, nullable=False)
    correct = Column(Integer, nullable=False)
    topic = Column(String, nullable=True)
    # Qaysi ko'nikma (roles.SKILL_KEYS). NULL = eski yozuv, faqat
    # umumiy darajaga sanaladi.
    skill = Column(String, nullable=True, index=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SupportBusy(Base):
    """Support teacherning O'ZI belgilagan band vaqti: "seshanba-payshanba
    14:00-16:00 — repetitorlik". Shu oraliqqa guruh biriktirilmoqchi
    bo'lsa, support manager ogohlantirish oladi."""
    __tablename__ = "support_busy"
    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"),
                        nullable=False, index=True)
    days = Column(String, nullable=False)   # "mon,wed,fri"
    start = Column(String, nullable=False)  # "14:00"
    end = Column(String, nullable=False)    # "16:00"
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChargeSkip(Base):
    """Asoschi avtomatik oylik yechimini O'CHIRGAN (student, oy) juftligi.
    Cron yoki "qayta hisoblash" shu oyni shu o'quvchiga QAYTA yozmaydi —
    aks holda o'chirilgan yechim ertasiga qaytib kelardi."""
    __tablename__ = "charge_skips"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    period = Column(String, nullable=False, index=True)  # "2026-08"
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RefundRequest(Base):
    """Pul qaytarish so'rovi. Sotuv menejeri so'raydi, filial rahbari
    yoki moliyachi tasdiqlaydi — shundagina pul qaytadi. To'g'ridan
    to'g'ri refund yo'q: to'rt ko'z qoidasi."""
    __tablename__ = "refund_requests"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    amount = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending/approved/rejected
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    requested_by = Column(String, nullable=True)
    decided_by = Column(String, nullable=True)
    decided_note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)

    student = relationship("Student")


class StudentCountSnapshot(Base):
    """Tarixiy statistika: ma'lum sanadagi o'quvchilar soni.

    Tizim kiritilishidan OLDINGI yillar uchun asoschi qo'lda kiritadi
    (masalan oyiga 2 marta yozib borilgan raqamlar). Grafikda jonli
    ma'lumotlar bilan bitta chiziqda ko'rinadi."""
    __tablename__ = "student_count_snapshots"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    count = Column(Integer, nullable=False)
    # Izoh: "Bekobod 2 ochildi", "yangi o'quv yili" kabi belgilar
    note = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SchemaMigration(Base):
    """Qo'llangan sxema o'zgarishlari ro'yxati. Har bir versiya bir
    marta ishlaydi — 'except: pass' o'rniga tartibli migratsiya."""
    __tablename__ = "schema_migrations"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, nullable=False)
    applied_at = Column(DateTime, default=datetime.utcnow)


class TeacherBranch(Base):
    """Ustoz ishlaydigan QO'SHIMCHA filiallar. Ba'zi ustozlar 2-3
    filialda dars beradi — asosiysi Teacher.branch_id da, qolganlari
    shu yerda. Filial rahbari ro'yxatida ikkalasi ham hisobga olinadi."""
    __tablename__ = "teacher_branches"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"),
                        nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"),
                       nullable=False, index=True)


class UserBranch(Base):
    """Xodim ishlaydigan QO'SHIMCHA filiallar. Ba'zi xodimlar (masalan,
    administrator) 2-3 filialda ishlaydi — asosiysi User.branch_id da,
    qolganlari shu yerda. Filialga bog'liq ko'rinishlar barcha
    filiallarini hisobga oladi."""
    __tablename__ = "user_branches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"),
                       nullable=False, index=True)


class VocabWord(Base):
    """Lug'at bazasi — Jony Student ilovasidagi so'z o'yinlari shu
    yerdan savol tuzadi.

    Ataylab SODDA: bitta so'z + tarjima + daraja + mavzu. Murakkab
    struktura (misol gaplar, audio va h.k.) keyin qo'shilishi mumkin,
    lekin o'yinlar ishlashi uchun shu yetarli. Import orqali
    (POST /api/vocab/import) katta ro'yxatni bir zumda yuklash mumkin —
    kod o'zgartirmasdan."""
    __tablename__ = "vocab_words"

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False, index=True)      # inglizcha
    translation = Column(String, nullable=False)           # o'zbekcha
    level = Column(String, nullable=True, index=True)      # A1..C1 (CEFR)
    topic = Column(String, nullable=True, index=True)      # ixtiyoriy mavzu
    example = Column(Text, nullable=True)                  # misol gap
    # Qaysi til lug'ati: en | ru | de | ko (2026-08-11, bayroq
    # almashtirish uchun). Eski yozuvlarda NULL = en deb o'qiladi.
    language = Column(String, default="en", index=True)
    is_active = Column(Integer, default=1, index=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PracticeItem(Base):
    """4 ko'nikma uchun universal mashq elementi (2026-08-11).

    Jahongir bergan spetsifikatsiyadagi yangi turlar shu jadvalda:
      reading:  read_tfng (T/F/Not Given), read_gap (matnda bo'sh
                joy), read_match (sarlavha moslash)
      listening: listen_img (emoji-rasm tanlash), listen_qa (dialog
                bo'yicha savol), listen_order (tartiblash)
      writing:  write_transform (qayta tuzish/kengaytirish)
      speaking: speak_repeat (eshitib takrorlash), speak_answer
                (savolga og'zaki javob - kalit iboralar bo'yicha)

    payload - JSON (har tur o'z tuzilishida), answer - JSON yoki
    matn, alt - qo'shimcha to'g'ri javoblar (JSON ro'yxat)."""
    __tablename__ = "practice_items"

    id = Column(Integer, primary_key=True, index=True)
    skill = Column(String, nullable=False, index=True)
    kind = Column(String, nullable=False, index=True)
    level = Column(String, default="A1")
    payload = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    alt = Column(Text)
    explain = Column(Text)
    is_active = Column(Integer, default=1)


class ReadingText(Base):
    """Reading mashqi uchun qisqa matn (2026-08-10)."""
    __tablename__ = "reading_texts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    level = Column(String, default="A1")       # A1 | A2 | B1
    body = Column(Text, nullable=False)
    is_active = Column(Integer, default=1)


class ReadingQuestion(Base):
    """Matnga tegishli tushunish savoli (4 variantli)."""
    __tablename__ = "reading_questions"

    id = Column(Integer, primary_key=True, index=True)
    text_id = Column(Integer, ForeignKey("reading_texts.id"),
                     nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    options = Column(Text, nullable=False)     # JSON list
    answer = Column(Text, nullable=False)
    explain = Column(Text)


class SkillAttempt(Base):
    """Listening/Reading/Writing/Speaking mashqlaridagi javoblar.

    ref - manba kaliti: "word:12" (lug'atdan), "gram:45" (grammar
    jumlasidan), "read:7" (reading savolidan). Ball har ko'nikmada
    distinct to'g'ri ref bo'yicha - bitta mashqni qayta yechib ball
    yig'ib bo'lmaydi."""
    __tablename__ = "skill_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    skill = Column(String, nullable=False, index=True)
    ref = Column(String, nullable=False, index=True)
    correct = Column(Integer, default=0)
    answer = Column(String)
    date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)


class GrammarQuestion(Base):
    """Grammar mashqlari bazasi (2026-08-10, Jahongir: "Grammar har
    bir ingliz tilidagi mavzuga xilma-xil mashqlar bo'lsin").

    Uch tur: fill (bo'sh joy), error (xatoni top), order (jumla
    yig'ish). options JSON ro'yxat; order turida options TO'G'RI
    tartibdagi so'zlar - server round tuzayotganda aralashtiradi,
    shuning uchun to'g'ri javob mijozga hech qachon ketmaydi."""
    __tablename__ = "grammar_questions"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False, index=True)
    topic_order = Column(Integer, default=0)   # mavzular tartibi
    is_boss = Column(Integer, default=0)       # BOSS LEVEL belgisi
    level = Column(String, default="A1")       # A1 | A2 | B1
    # Qaysi til grammatikasi (2026-08-24, Jahongir: "boshqa tillarni
    # grammatikasi yoq ekan ularni ham qoshib qoygin"). NULL = en
    # (eski yozuvlar ingliz tili).
    language = Column(String, nullable=True, index=True)
    kind = Column(String, nullable=False)      # fill | error | order
    prompt = Column(Text, nullable=False)
    options = Column(Text, nullable=False)     # JSON list
    answer = Column(Text, nullable=False)
    explain = Column(Text)
    is_active = Column(Integer, default=1)


class GrammarAttempt(Base):
    """O'quvchining grammar mashqidagi har bir javobi. Ball va
    mavzu progressi shu yerdan chiqadi; bitta savol uchun ball bir
    marta beriladi (distinct hisob)."""
    __tablename__ = "grammar_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("grammar_questions.id"),
                         nullable=False, index=True)
    correct = Column(Integer, default=0)
    answer = Column(String)
    date = Column(Date, default=date.today)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Qaysi rejimda yechildi (2026-09-25, Jahongir: "grammatikaga
    # aralash mashq qilish funksiyasini qoshgin shunda aynan qaysi
    # mavzuda koproq xato qilyabdi o'ziga bilinib korinib tursin").
    # NULL = mavzu ichida (eski yozuvlar), "mix" = aralash mashq —
    # mavzu ko'rsatilmagan holdagi xato haqiqiy bo'shliqni ko'rsatadi.
    mode = Column(String, nullable=True, index=True)


class VocabUnitPass(Base):
    """USTOZ tasdig'i: o'quvchi unitni topshirdi (2026-08-11).

    Jahongir: "ustoz 1-unitni topshirdi degan tick qo'ysa birinchi
    unit avtomat 100% bo'lishi kerak" - practice bilan maksimum 99%
    yig'iladi, 100% faqat shu tasdiq bilan."""
    __tablename__ = "vocab_unit_passes"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    unit = Column(String, nullable=False, index=True)   # "Unit 1"
    language = Column(String, default="en")
    passed_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class VocabAttempt(Base):
    """O'quvchining lug'at o'yinidagi HAR BIR javobi.

    Nega har bir javob alohida yoziladi: (1) reyting va statistika shu
    yerdan chiqadi; (2) qaysi so'z qiyin kelayotganini bilish mumkin
    (kelajakda "xatolar ustida ishlash" rejimi uchun); (3) XP takror
    berilmasligini nazorat qilish oson."""
    __tablename__ = "vocab_attempts"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"),
                        nullable=False, index=True)
    word_id = Column(Integer, ForeignKey("vocab_words.id"),
                     nullable=True, index=True)
    game = Column(String, nullable=False, index=True)   # roles.VOCAB_GAMES
    correct = Column(Integer, default=0, index=True)    # 1 / 0
    answer = Column(String, nullable=True)              # o'quvchi javobi
    date = Column(Date, default=date.today, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserRole(Base):
    """Xodimning QO'SHIMCHA lavozimlari (2026-08-10).

    Jahongir: "bir xodim bir nechta lavozim qo'shsak bo'ladimi,
    filial almashtirgandek lavozimini almashtirib kiraverardi.
    Masalan HR managerimiz Support managerlik ishini ham qiladi;
    Nodir filial rahbari ham, ustoz ham; Zafar filial rahbari ham,
    moliyachi ham, xo'jalik ishlari rahbari ham."

    ASOSIY lavozim User.role da qoladi (butun tizim shuni o'qiydi),
    qo'shimchalari shu jadvalda. Xodim tepadagi tanlagichdan
    lavozimni almashtirsa, so'rov sarlavhasida (X-Active-Role) qaysi
    lavozimda ishlayotgani keladi va o'sha so'rov davomida user.role
    SHU lavozimga almashtiriladi.

    NEGA SHUNDAY: tizimda yuzlab joyda user.role tekshiriladi. Agar
    "barcha lavozimlar birlashsin" desak, har bir tekshiruvni qayta
    yozish kerak bo'lardi — bu esa xavfsizlik teshiklari uchun eng
    qulay yo'l. Almashtirish esa mavjud tekshiruvlarning HAMMASI
    o'zgarishsiz to'g'ri ishlashini kafolatlaydi."""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False, index=True)
    role = Column(String, nullable=False, index=True)


# =====================================================================
#  ESKI NARX QULFI O'ZI OCHILADI (2026-08-15)
#
#  Jahongir: "avgust muzlatib keyin yana kelganlarga narx oshgan
#  bolishi kerak".
#
#  O'quvchi FAOL bo'lmay qolsa (muzlatildi, arxivlandi, ketdi) eski
#  narx himoyasi bekor bo'ladi — qaytib kelsa o'sha paytdagi joriy
#  narxda o'qiydi.
#
#  Buni bitta joyda hal qilamiz: status maydoni QAYERDA o'zgartirilsa
#  ham shu ilgak ishlaydi. Aks holda muzlatish, arxivlash, guruhdan
#  chiqarish — har birini alohida tuzatish kerak bo'lardi va bittasi
#  esdan chiqsa xato jimgina qolib ketardi.
# =====================================================================
@event.listens_for(Student.status, "set")
def _release_price_lock_on_status(target, value, oldvalue, initiator):
    if value != "active" and getattr(target, "locked_lesson_price", None):
        target.locked_lesson_price = None
        target.locked_price_at = None
        target.locked_price_note = None


class Holiday(Base):
    """DAM KUNI (2026-08-19, Jahongir: "bizda dam kunlari degan narsa
    bor buni sozlamalarga qoshib qoysang ham bo'ladi. Dam kunlari
    darslar bo'lmaydi va bu darslar umuman hisoblanmaydi").

    Belgilanganda o'sha kundagi barcha rejadagi darslar bekor
    qilinadi. Har bir guruhda oyda kamida 12 dars qolishi tekshiriladi
    - kamaysa dam kuni qo'yilmaydi."""
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =====================================================================
#  OYLIK MUHRI (2026-09-07)
#
#  Jahongir: "taklifing menga maqul otgan oy muhransin".
#
#  Ustoz oyligi hech qayerda saqlanmasdi — sahifa har ochilganda
#  yo'qlamalardan qayta hisoblanardi. Shuning uchun oy yopilgandan
#  KEYIN bo'lgan har qanday o'zgarish (o'quvchi muzlashi, guruhdan
#  chiqishi, dars yozuvi qo'shilishi) O'TGAN oyning raqamini ham
#  o'zgartirardi — 31-avgustdagi skrinshot bilan bugungi raqam mos
#  kelmay qolgan edi.
#
#  Endi: oy tugagach raqam BIR MARTA muhrlanadi va o'zgarmaydi.
#  Muhr o'chirilmaydi — faqat asoschi ataylab "qayta hisobla" desa
#  yangilanadi va eski qiymati auditda qoladi.
# =====================================================================
class PayrollSeal(Base):
    """Bir ustozning bir oylik muhrlangan oyligi."""
    __tablename__ = "payroll_seals"

    id = Column(Integer, primary_key=True, index=True)
    period = Column(String, nullable=False, index=True)      # "YYYY-MM"
    teacher_id = Column(Integer, ForeignKey("teachers.id"),
                        nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    amount = Column(Float, nullable=False, default=0)
    attendances = Column(Integer, default=0)
    lessons = Column(Integer, default=0)
    groups_json = Column(Text, nullable=True)
    sealed_at = Column(DateTime, default=datetime.utcnow)
    sealed_by = Column(String, nullable=True)
    # Qayta hisoblangan bo'lsa — nechanchi marta va qachon
    revision = Column(Integer, default=1)
    note = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("period", "teacher_id", name="uq_seal_period_teacher"),
    )


class Event(Base):
    """TADBIR (2026-09-14): bayram, tanlov, ekskursiya, bitiruv va h.k.

    Event menejer rejalashtiradi va holatini yuritadi. Filialsiz
    tadbir — butun markazniki (masalan, umumiy bayram)."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    kind = Column(String, default="other")            # roles.EVENT_KINDS
    event_date = Column(Date, nullable=False, index=True)
    start_time = Column(String, nullable=True)         # "17:00"
    place = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True,
                       index=True)
    audience = Column(String, nullable=True)           # kimlar uchun
    budget = Column(Float, nullable=True)
    status = Column(String, default="planned", index=True)  # roles.EVENT_STATUSES
    responsible_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    note = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    branch = relationship("Branch")
    responsible = relationship("User", foreign_keys=[responsible_id])


class Comment(Base):
    """Izohlar tarixi: o'quvchi yoki lid kartasidagi har bir izoh alohida
    qator (2026-09-15). O'chirilmaydi va tahrirlanmaydi — LC UP'dagidek
    oldingilari saqlanib, raqamlangan ro'yxatda turadi."""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    entity = Column(String, nullable=False, index=True)      # student | lead
    entity_id = Column(Integer, nullable=False, index=True)
    text = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    author_name = Column(String, nullable=True)              # o'sha paytdagi ism
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ---------------------------------------------------------------
#  JONLI O'YIN — Kahoot uslubidagi viktorina (2026-09-18, Jahongir:
#  "kahoot korinishidagi oyinlar ... har bir unitda"). Ustoz dars
#  rejasidan o'yin ochadi, o'quvchilar PIN/QR bilan loginsiz kiradi.
# ---------------------------------------------------------------
class LiveGame(Base):
    __tablename__ = "live_games"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, index=True)        # 6 xonali PIN
    course = Column(String, nullable=False)                  # ielts_1_0
    lesson_no = Column(Integer, nullable=False)
    mode = Column(String, default="mixed")                   # vocab|vocab40|grammar|mixed
    title = Column(String, nullable=True)
    questions = Column(Text, nullable=False)                 # JSON ro'yxat
    question_seconds = Column(Integer, default=20)
    status = Column(String, default="lobby", index=True)     # lobby|question|reveal|ended
    q_index = Column(Integer, default=-1)
    q_started_at = Column(DateTime, nullable=True)
    host_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    # Qaysi guruh uchun (coin va imtihon natijasi shu guruhga yoziladi)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True, index=True)
    # Tugagach yaratilgan imtihon yozuvi (kind="kahoot") — bir marta
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)


class LivePlayer(Base):
    __tablename__ = "live_players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("live_games.id"), nullable=False, index=True)
    nickname = Column(String, nullable=False)
    # Ro'yxatdan tanlangan o'quvchi (coin shu yerga boradi); NULL = mehmon
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    token = Column(String, nullable=False, index=True)       # telefon sessiyasi
    score = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)               # yakunda hisoblanadi
    coins = Column(Integer, default=0)                       # yakunda berilgan coin
    joined_at = Column(DateTime, default=datetime.utcnow)


class LiveAnswer(Base):
    __tablename__ = "live_answers"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("live_games.id"), nullable=False, index=True)
    player_id = Column(Integer, ForeignKey("live_players.id"), nullable=False, index=True)
    q_index = Column(Integer, nullable=False)
    option_index = Column(Integer, nullable=False)
    correct = Column(Integer, default=0)
    ms = Column(Integer, default=0)                          # savol boshidan o'tgan ms
    points = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------
#  DARS BOSHQARUVI (2026-09-18, Jahongir): guruh ↔ reja va dars rejimi
# ---------------------------------------------------------------
class GroupPlan(Base):
    """Guruh qaysi daraja rejasida va qaysi darsda turibdi."""
    __tablename__ = "group_plans"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, unique=True, index=True)
    course = Column(String, nullable=False)                  # ielts_1_0
    next_lesson_no = Column(Integer, default=1)              # keyingi o'tiladigan dars
    carry = Column(Text, default="[]")                       # ko'chgan bosqichlar (JSON)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)


class LessonRun(Base):
    """Bitta darsning o'tkazilish jarayoni: bosqichlar, taymer, izohlar."""
    __tablename__ = "lesson_runs"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    course = Column(String, nullable=False)
    lesson_no = Column(Integer, nullable=False)
    stages = Column(Text, nullable=False)                    # JSON [{title,min,desc,done,carried}]
    current = Column(Integer, default=0)
    stage_started_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)                      # ustozning maxfiy izohi
    status = Column(String, default="running", index=True)  # running | finished
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)


# ---------------------------------------------------------------
#  TOPSHIRIQLAR VA TEKSHIRISH (2026-09-18, Jahongir, 4- va 6-bandlar)
# ---------------------------------------------------------------
class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)   # shaxsiy bo'lsa
    course = Column(String, nullable=False)
    lesson_no = Column(Integer, nullable=False)
    kind = Column(String, nullable=False)        # vocab_test|grammar_test|homework|reading|writing|speaking|free
    skill = Column(String, nullable=True)        # vocab|grammar|reading|listening|writing|speaking
    title = Column(String, nullable=False)
    instr = Column(Text, nullable=True)
    text = Column(Text, nullable=True)           # reading matni (JSON)
    questions = Column(Text, nullable=False)     # JSON [{kind,prompt,options,answer,explain}]
    auto = Column(Integer, default=1)            # 1 — avtomat tekshiriladi
    rubric = Column(Text, nullable=True)         # JSON [[mezon, ball], ...]
    max_score = Column(Float, nullable=True)
    targets = Column(Text, nullable=True)        # JSON [student_id, ...]
    due_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="sent", index=True)   # sent | closed
    created_by = Column(String, nullable=True)


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    attempt = Column(Integer, default=1)
    answers = Column(Text, nullable=True)        # JSON {"0": ..., "1": ...}
    text = Column(Text, nullable=True)           # writing
    transcript = Column(Text, nullable=True)     # speaking matni
    media_id = Column(Integer, nullable=True)    # audio (assignment_media)
    auto_score = Column(Float, nullable=True)
    auto_max = Column(Float, nullable=True)
    result = Column(Text, nullable=True)         # JSON avtomat natija (har savol)
    status = Column(String, default="submitted", index=True)   # started|submitted|graded|returned
    teacher_score = Column(Float, nullable=True)
    rubric_scores = Column(Text, nullable=True)  # JSON {mezon: ball}
    comment = Column(Text, nullable=True)
    voice_media_id = Column(Integer, nullable=True)
    ai_review = Column(Text, nullable=True)      # JSON
    coins = Column(Integer, default=0)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    graded_at = Column(DateTime, nullable=True)
    graded_by = Column(String, nullable=True)


class AssignmentMedia(Base):
    """Audio (speaking javobi, ustozning ovozli izohi). 30 kundan keyin o'chiriladi."""
    __tablename__ = "assignment_media"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=True, index=True)
    submission_id = Column(Integer, nullable=True, index=True)
    kind = Column(String, default="audio")
    mime = Column(String, default="audio/webm")
    data = deferred(Column(Text, nullable=False))    # base64 data URL
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


# ------------------------------------------------------ ONLINE TEST (link)
# 2026-09-18, Jahongir: "guruhga test biriktirganda unit midterm yoki end
# of course link paydo bo'lsin shu linkni examiner telegramdan tashlab
# bersa o'quvchilar kirib baholay olsin natijalar to'g'ridan to'g'ri
# guruhga biriktirilgan exam natijalarga tushaversin". Writing va
# Speaking qog'ozda qoladi — examiner ularni qo'lda qo'shadi.

class ExamTemplate(Base):
    """Test bazasi: bitta daraja + tur + unit uchun savollar to'plami.

    parts — JSON: [{title, instructions, passage, audio_url,
    questions: [{id, n, type: "choice"|"text", q, options, answer}]}].
    choice: answer = to'g'ri variant indeksi; text: answer = qabul
    qilinadigan javoblar ro'yxati. Har savol 1 ball."""
    __tablename__ = "exam_templates"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, nullable=True, index=True)   # Group.level (step1…)
    kind = Column(String, nullable=False, default="unit")
    unit_no = Column(Integer, nullable=True)
    title = Column(String, nullable=False)
    parts = Column(Text, nullable=False, default="[]")
    # Writing + Speaking (qog'ozda) maksimal bali; 0 = yo'q
    paper_max = Column(Float, nullable=False, default=0)
    # VARIANT (2026-09-26, Jahongir: "shu savollarni 4-5 xil variantini
    # tayyorlab qoyish kerak chunki ustozlar aynan testga tayyorlash
    # holatlari kuzatilyabdi"). Bir daraja+tur+unit uchun A (asl),
    # B, C, D, E — bir xil tuzilish, boshqa savollar. Link ochilganda
    # har bo'lim tasodifiy variantdan olinadi. NULL = A (eski yozuvlar).
    variant = Column(String, nullable=True, index=True)
    # FAN (2026-09-26, matematika bazasi): Group.subject bilan mos
    # (english, math, …). NULL = english (eski yozuvlar). Link ochilganda
    # faqat guruh faniga mos shablonlar taklif qilinadi.
    subject = Column(String, nullable=True, index=True)
    is_active = Column(Integer, nullable=False, default=1)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ExamOnline(Base):
    """Guruh testining online linki. Bitta testga bitta link."""
    __tablename__ = "exam_online"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False,
                     unique=True, index=True)
    template_id = Column(Integer, ForeignKey("exam_templates.id"), nullable=False)
    token = Column(String, nullable=False, unique=True, index=True)
    is_open = Column(Integer, nullable=False, default=1)
    # Link ochilgan paytdagi savollar nusxasi — bazadagi test keyin
    # tahrirlansa ham shu testni yechganlar bir xil savol oladi.
    parts = Column(Text, nullable=False, default="[]")
    online_max = Column(Float, nullable=False, default=0)
    paper_max = Column(Float, nullable=False, default=0)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Examiner natijalarni TASDIQLAGAN payt (2026-09-18, Jahongir: "testni
    # examiner tasdiqlaganidan keyin o'quvchilar va ustozlarga ko'rinadigan
    # qilib ber"). NULL — natijalar hali guruh testiga yozilmagan.
    published_at = Column(DateTime, nullable=True)
    published_by = Column(String, nullable=True)
    # VAQTLI TEST (2026-09-18, Jahongir: "examiner vaqt belgilab start
    # bosganda sekund teskari sanab test ochilsin ... vaqt tugagach
    # avtomatik topshirilsin"). started_at — savollar ochiladigan payt
    # (sanoqdan keyin), ends_at — tugash payti. NULL — hali kutish.
    duration_min = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    # Sahifadan necha marta chiqishga ruxsat (2026-09-23, Jahongir:
    # "5tami nechtadir son ... shundan oshsa testdan chiqarib yuborsin").
    # Shu songacha uzrli (internet uzilishi va h.k.).
    away_limit = Column(Integer, nullable=True)
    # Qaysi variantlardan yig'ilgani, bo'limlar tartibida: "B,A,D,C,E"
    # (2026-09-26). NULL — eski link / bitta shablon.
    variants = Column(String, nullable=True)


class ExamSubmission(Base):
    """O'quvchining link orqali topshirgan javobi.

    status: placed — guruhdagi o'quvchiga biriktirilgan (natijasi o'z
    qatorida); pending — ro'yxatda yo'q / ism xato (qizil chiziqdan
    pastda, examiner biriktiradi); duplicate — shu o'quvchi avval ham
    topshirgan; replaced — o'rniga boshqasi qoldirilgan; rejected."""
    __tablename__ = "exam_submissions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    typed_name = Column(String, nullable=True)
    photo = deferred(Column(Text, nullable=True))   # data:image/jpeg;base64,…
    answers = Column(Text, nullable=True)           # JSON {qid: javob}
    detail = Column(Text, nullable=True)            # JSON [{id, n, ok, given}]
    online_score = Column(Float, nullable=False, default=0)
    online_max = Column(Float, nullable=False, default=0)
    paper_score = Column(Float, nullable=True)      # Writing + Speaking
    status = Column(String, nullable=False, default="pending")
    # in_progress — o'quvchi kirgan, test hali topshirilmagan; sub_key —
    # uning brauzeridagi kalit (javoblarni oraliqda saqlash uchun)
    sub_key = Column(String, nullable=True, index=True)
    # SAHIFADAN CHIQISH (2026-09-23, Jahongir): o'quvchi test paytida
    # boshqa ilovaga o'tsa — necha marta va jami necha soniya.
    away_count = Column(Integer, nullable=False, default=0)
    away_sec = Column(Integer, nullable=False, default=0)
    # MOCK QAT'IY TARTIBI (2026-09-27): sahifa qoidabuzarlikni internet
    # uzilsa ham qayta-qayta yuboradi — bir hodisa ikki marta
    # sanalmasin, oxirgi ~40 ta hodisa kodi (JSON ro'yxat)
    away_eids = Column(Text, nullable=True)
    # Chetlatish sababi (chegaradan oshdi yoki examiner chetlatdi)
    note = Column(String, nullable=True)
    ip = Column(String, nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    placed_by = Column(String, nullable=True)
    placed_at = Column(DateTime, nullable=True)


# ------------------------------------------------ XODIMLAR MOCK MASHQI
# 2026-09-27, Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib
# ishlaydigan bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq
# ustozlarga ular ham experience qilib xatolarni aytadida".
#
# Ikki jadval ATAYLAB alohida: xodim urinishi Exam / ExamOnline /
# ExamSubmission / ExamResult ga HECH QACHON yozilmaydi — natija,
# coin, XP, examiner maoshi va mavzu tahlili bunga tegmaydi.
# template_id — FK EMAS: delete_template shablonni butunlay o'chiradi,
# urinish esa content_key (canon_title) orqali boshqa nusxaga o'tadi.

class MockPractice(Base):
    """Xodimning mock testni o'zi yechib ko'rishi (natija faqat o'ziga)."""
    __tablename__ = "mock_practice"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user_name = Column(String, nullable=True)            # nusxa
    template_id = Column(Integer, nullable=False, index=True)   # FK yo'q
    content_key = Column(String, nullable=False, index=True)    # canon_title
    skill = Column(String(40), nullable=True)            # ielts_listening …
    variant = Column(String(4), nullable=True)
    # Urinish paytida shablon tahrirlansa — sahifada izoh chiqadi
    tpl_updated_at = Column(DateTime, nullable=True)
    answers = Column(Text, default="{}")                 # JSON {qid: javob}
    detail = Column(Text, nullable=True)                 # grade() natijasi
    score = Column(Float, nullable=True)
    max_score = Column(Float, nullable=True)
    band = Column(Float, nullable=True)                  # IELTS L/R
    cefr = Column(Text, nullable=True)                   # JSON lr_approx (taxminiy)
    script_opened = Column(String, nullable=True)        # "0,2" — TTS skriptlar
    # in_progress | submitted
    status = Column(String, nullable=False, default="in_progress", index=True)
    duration_min = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_mock_practice_user_key",
                            "user_id", "content_key", "created_at"),)


class MockIssue(Base):
    """Savoldagi xato haqida xabar: kalit xato, ikki javob, imlo …
    Examinerlar boshlig'i ko'rib "tuzatildi / rad etildi" qiladi."""
    __tablename__ = "mock_issue"

    id = Column(Integer, primary_key=True)
    content_key = Column(String, nullable=False, index=True)
    template_id = Column(Integer, nullable=True, index=True)   # FK yo'q
    skill = Column(String(40), nullable=True)
    variant = Column(String(4), nullable=True)
    qid = Column(String, nullable=True)                  # NULL = butun bo'lim
    q_n = Column(Integer, nullable=True)
    part_title = Column(String, nullable=True)
    # Xabar paytidagi savol {q, options, answer, type} — FAQAT serverda
    q_snapshot = Column(Text, nullable=True)
    q_hash = Column(String(16), nullable=True)           # "o'zgargan" belgisi
    # answer_key | two_answers | typo | unclear | script_audio | other
    kind = Column(String, nullable=False)
    comment = Column(Text, nullable=True)                # <= 1000
    suggested = Column(String(300), nullable=True)
    given = Column(String(200), nullable=True)           # xabarchining javobi
    during_test = Column(Integer, default=0)
    practice_id = Column(Integer, nullable=True, index=True)   # FK yo'q
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reporter_name = Column(String, nullable=True)
    # open | fixed | rejected | duplicate
    status = Column(String, nullable=False, default="open", index=True)
    resolution_note = Column(String, nullable=True)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_mock_issue_status_key",
                            "status", "content_key", "qid"),)


class DrillTask(Base):
    """MASHQ BANDI (2026-09-25). Admin qanday vazifani necha soniyada
    bajarishi kerakligi. HR bo'limidan tahrirlanadi."""
    __tablename__ = "drill_tasks"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    order_no = Column(Integer, default=0, index=True)
    title = Column(String, nullable=False)
    hint = Column(String, nullable=True)
    seconds = Column(Integer, default=30)
    # row = jadvalda yangi yozuv; audit = tarixdagi amal; view = ko'rish
    verify_kind = Column(String, default="view")
    verify_table = Column(String, nullable=True)
    verify_entity = Column(String, nullable=True)
    verify_action = Column(String, nullable=True)
    verify_field = Column(String, nullable=True)
    is_active = Column(Integer, default=1)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class DrillAttempt(Base):
    """Bitta urinish: kim, qachon, qaysi filialda."""
    __tablename__ = "drill_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True,
                     nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.id"), index=True)
    status = Column(String, default="running", index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class DrillStep(Base):
    """Urinishdagi bitta band: qachon boshlandi, qancha vaqt ketdi,
    tekshiruvdan o'tdimi."""
    __tablename__ = "drill_steps"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("drill_attempts.id"),
                        index=True, nullable=False)
    task_id = Column(Integer, ForeignKey("drill_tasks.id"), nullable=False)
    order_no = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    done_at = Column(DateTime, nullable=True)
    spent = Column(Integer, nullable=True)      # soniya
    ok = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    # "row" tekshiruvi uchun: band boshlanganda jadvaldagi eng katta id
    snapshot_id = Column(Integer, nullable=True)


class DrillSetting(Base):
    """MASHQ SOZLAMASI — bitta qator (id=1).

    2026-09-25, Jahongir: "60% foiz o'tsa xodimni ishga olsa bo'ladi".
    O'tish foizi kodda qotib qolmasin: HR uni o'zgartira oladi."""
    __tablename__ = "drill_settings"

    id = Column(Integer, primary_key=True)
    pass_percent = Column(Integer, default=60)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


# =====================================================================
#  BARABAN — lidlar testi oxiridagi sovg'a g'ildiragi (2026-09-25)
# =====================================================================
#
#  Jahongir: "yangi lidlar ishlaydigan test bor shu testni bajargan
#  oquvchiga oxirida baraban chiqishi kerak va barabanda xar xil
#  sovgalar skidkalar 10-100%gacha coinlar 10-100gacha bo'lishi
#  kerak aylantirganda bittasiga tushsa shu sovga avtomat unga
#  otishi kerak".
#
#  Ikki jadval:
#    wheel_prizes — g'ildirakdagi bo'laklar va EHTIMOLLIKLARI.
#                   Asoschi Sozlamalardan o'zgartiradi. Kodda
#                   qotmaydi. Hech qachon o'chirilmaydi — is_active=0.
#    wheel_spins  — har aylantirish. SERVER tanlaydi va shu yerga
#                   yozadi, telefon faqat animatsiya qiladi. Bir lidga
#                   BITTA aylantirish. Sovg'a o'quvchiga qanday
#                   qo'llangani ham shu qatorda: qaysi chegirma /
#                   qaysi tanga yozuvi, qachon, kimga.

class WheelPrize(Base):
    __tablename__ = "wheel_prizes"

    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String, nullable=False)          # coin | discount
    value = Column(Integer, nullable=False)        # tanga soni / foiz
    weight = Column(Float, nullable=False, default=1.0)  # ehtimol og'irligi
    label = Column(String, nullable=True)          # "10% chegirma"
    order_no = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class WheelSpin(Base):
    __tablename__ = "wheel_spins"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=True,
                     index=True)
    session_token = Column(String, nullable=True, index=True)
    phone = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)
    prize_id = Column(Integer, ForeignKey("wheel_prizes.id"), nullable=True)
    prize_kind = Column(String, nullable=False)    # coin | discount
    prize_value = Column(Integer, nullable=False)
    prize_label = Column(String, nullable=True)
    spun_at = Column(DateTime, default=datetime.utcnow)
    # Qo'llanish izi (hech narsa o'chirilmaydi)
    applied_student_id = Column(Integer, ForeignKey("students.id"),
                                nullable=True, index=True)
    coin_entry_id = Column(Integer, nullable=True)
    discount_id = Column(Integer, nullable=True)
    applied_at = Column(DateTime, nullable=True)
    notified_at = Column(DateTime, nullable=True)  # asoschiga xabar
    note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class IntegrationSetting(Base):
    """Tashqi xizmat sozlamalari (kalit -> qiymat). Birinchi foydalanish:
    Instagram tokeni (2026-09-26). Tokenni ASOSCHI O'ZI joylaydi;
    API javobida hech qachon to'liq ko'rsatilmaydi (faqat oxirgi 4 belgi).
    O'chirilmaydi — "uzish" qiymatni bo'shatadi, izi auditda qoladi."""
    __tablename__ = "integration_settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=True)
    updated_by = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class IgMedia(Base):
    """Instagram akkauntimizdagi har bir post/reels (avtomat sinxron).
    Kontent-plandagi postga bog'lansa (content_id) raqamlari
    ContentMetric'ga ham yoziladi."""
    __tablename__ = "ig_media"

    id = Column(Integer, primary_key=True, index=True)
    ig_id = Column(String, unique=True, index=True, nullable=False)
    shortcode = Column(String, index=True, nullable=True)
    permalink = Column(String, nullable=True)
    caption = Column(Text, nullable=True)
    media_type = Column(String, nullable=True)
    posted_at = Column(DateTime, nullable=True)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    views = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    follows = Column(Integer, default=0)
    profile_visits = Column(Integer, default=0)
    content_id = Column(Integer, ForeignKey("contents.id"), nullable=True,
                        index=True)
    link_note = Column(String, nullable=True)
    fetched_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class VideoCheck(Base):
    """Video yuklanganda avtomat tekshiruv natijasi (2026-09-26).
    Jahongir: "videoni yuklaganda tahlil qiladigan funksiya ... oxirida
    tel raqam qoyilmagan, oxirida logo animation qoshilmagan".
    Video faylning o'zi SAQLANMAYDI — faqat natija (JSON)."""
    __tablename__ = "video_checks"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id"), index=True,
                        nullable=True)
    file_name = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    ok = Column(Integer, default=0)
    result = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
