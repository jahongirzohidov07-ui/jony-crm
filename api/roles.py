"""Jony Academy tashkiliy rollari.

Muhim atama farqi: bizning o'quv markazda "Administrator" deganda
SOTUV MENEJERI tushuniladi (lidlar bilan ishlaydigan odam), tizimning
egasi emas. Tizimning to'liq huquqli egasi - ASOSCHI.

Ichki kalitlar (masalan "founder") bazada saqlanadi va hech qachon
o'zgarmasligi kerak; ekranda ko'rinadigan nom UZ_LABELS'da turadi.
"""

FOUNDER = "founder"                     # Asoschi - to'liq huquq
BRANCH_MANAGER = "branch_manager"       # Filial menejeri
SALES_MANAGER = "sales_manager"         # Administrator (sotuv menejeri)
TEACHER = "teacher"                     # O'qituvchi
SUPPORT_TEACHER = "support_teacher"
EXAMINER = "examiner"
HR_MANAGER = "hr_manager"
SMM_MANAGER = "smm_manager"

ALL_ROLES = [
    FOUNDER,
    BRANCH_MANAGER,
    SALES_MANAGER,
    TEACHER,
    SUPPORT_TEACHER,
    EXAMINER,
    HR_MANAGER,
    SMM_MANAGER,
]

UZ_LABELS = {
    FOUNDER: "Asoschi",
    BRANCH_MANAGER: "Filial menejeri",
    SALES_MANAGER: "Administrator (sotuv menejeri)",
    TEACHER: "O'qituvchi",
    SUPPORT_TEACHER: "Support teacher",
    EXAMINER: "Examiner",
    HR_MANAGER: "HR manager",
    SMM_MANAGER: "SMM manager",
}

# ---- Ruxsat guruhlari -------------------------------------------------
# Kundalik operatsion to'liq huquq (talaba/guruh yaratish-o'chirish,
# moliyaviy amallar). Asoschi + filial menejeri.
FULL_ACCESS = [FOUNDER, BRANCH_MANAGER]

# Talaba yozuvlari bilan ishlaydiganlar. Sotuv menejeri ham kiradi -
# lidni o'quvchiga aylantirish uning ishi.
TEACHING_STAFF = FULL_ACCESS + [SALES_MANAGER, TEACHER, SUPPORT_TEACHER, EXAMINER]

# Xodimlar ro'yxatini KO'RA oladiganlar.
STAFF_VIEWERS = FULL_ACCESS + [HR_MANAGER]

# Xodim yaratish va ROL BERISH - faqat asoschi. Bu ataylab eng tor
# guruh: rol berish tizimdagi eng xavfli amal.
USER_ADMIN = [FOUNDER]

# Moliya (to'lov, hisob-kitob, ish haqi).
FINANCE_ACCESS = FULL_ACCESS

# Lidlar (sotuv voronkasi). Administrator/sotuv menejeri bu yerda
# asosiy foydalanuvchi; SMM manager Instagram/Telegram lidlarini
# kiritadi; support teacher qabulda tashrifchilarni yozadi.
LEAD_ACCESS = FULL_ACCESS + [SALES_MANAGER, SMM_MANAGER, SUPPORT_TEACHER]

# Faqat umumiy statistikani ko'radiganlar.
DASHBOARD_ONLY = [SMM_MANAGER]

# Butun tashkilot bo'yicha ko'radigan rollar (filialga bog'lanmagan).
ORG_WIDE_ROLES = [FOUNDER, HR_MANAGER, SMM_MANAGER]

# ---- To'lov usullari --------------------------------------------------
# Cashflow hisoboti shu bo'yicha bo'linadi. Faqat kirim ("payment")
# yozuvlarida ma'noga ega; hisoblangan to'lov va chegirmada bo'sh qoladi.
PAYMENT_METHODS = [
    "cash",      # Naqd
    "card",      # Plastik - Click, Payme, karta o'tkazmasi
    "terminal",  # Terminal - do'kondagi POS apparati
    "other",     # Boshqa
]

PAYMENT_METHOD_LABELS = {
    "cash": "Naqd",
    "card": "Plastik",
    "terminal": "Terminal",
    "other": "Boshqa",
}

# ---- Xarajatlar: guruh (tur) va kategoriya -----------------------------
# Xarajat ikki qavatli: har bir kategoriya bitta GURUHGA tegishli.
# Hisobot va analitika guruh kesimida chiqadi, kiritish esa aniq
# kategoriya bilan - shunda "kommunalga qancha ketdi" ham, "elektrga
# qancha ketdi" ham bir xil ma'lumotdan chiqadi.

EXPENSE_GROUPS = [
    ("rent", "Ijara"),
    ("communal", "Kommunal"),
    ("office", "Ofis xarajatlari"),
    ("admin_salary", "Ma'muriy xodim oyliklari"),
    ("teacher_salary", "Ustozlar oyligi"),   # avtomatik - qo'lda kiritilmaydi
    ("marketing", "Reklama"),
    ("tax", "Soliq"),
    ("other", "Boshqa"),
]
EXPENSE_GROUP_LABELS = dict(EXPENSE_GROUPS)

# (kalit, nomi, guruh)
EXPENSE_CATEGORY_DEFS = [
    ("rent", "Ijara", "rent"),

    ("electricity", "Elektr toki", "communal"),
    ("gas", "Gaz", "communal"),
    ("water_main", "Vodoprovod suv", "communal"),
    ("internet", "Internet / aloqa", "communal"),
    # Eski yozuvlar shu kalitda edi - yo'qotmaslik uchun qoldiramiz.
    ("utilities", "Kommunal (umumiy)", "communal"),

    ("cooler_water", "Kuler suvi", "office"),
    ("printer_refill", "Printer zapravka", "office"),
    ("paper", "List qog'oz", "office"),
    ("marker", "Marker / doska", "office"),
    ("stationery", "Boshqa kanstovar", "office"),
    ("equipment", "Jihoz", "office"),

    ("admin_salary", "Ma'muriy xodim oyligi", "admin_salary"),
    ("support_salary", "Farrosh / qorovul", "admin_salary"),
    # Eski "salary" kaliti ham ma'muriy xodimlarni bildirgan.
    ("salary", "Xodimlar oyligi (eski)", "admin_salary"),

    ("ads", "Reklama", "marketing"),
    ("tax", "Soliq", "tax"),
    ("repair", "Ta'mir", "other"),
    ("other", "Boshqa", "other"),
]

EXPENSE_CATEGORIES = [c for c, _, _ in EXPENSE_CATEGORY_DEFS]
EXPENSE_CATEGORY_LABELS = {c: lbl for c, lbl, _ in EXPENSE_CATEGORY_DEFS}
EXPENSE_CATEGORY_GROUP = {c: g for c, _, g in EXPENSE_CATEGORY_DEFS}

# DIQQAT: ustozlar ish haqi bu ro'yxatda YO'Q - u TeacherPayout
# jadvalidan avtomatik olinadi. Agar uni qo'lda ham kiritsangiz,
# P&L'da ikki marta hisoblanib ketadi.

# ---- Lid voronkasi ----------------------------------------------------
LEAD_STAGES = [
    "new",              # Yangi (so'rov keldi, hali bog'lanilmagan)
    "contacted",        # Bog'lanildi
    "trial_scheduled",  # Sinov darsiga yozildi
    "trial_attended",   # Sinovga keldi
    "converted",        # O'quvchiga aylandi  (yutuq)
    "rejected",         # Rad etdi            (yo'qotish)
]

LEAD_SOURCES = [
    "visit",      # Tashrif - o'zi kirib kelgan
    "phone",      # Telefon - o'zi qo'ng'iroq qilgan
    "instagram",
    "telegram",
    "referral",   # Tanish orqali
    "ads",        # Reklama
    "other",      # Boshqa
]

# Manba lidni voronkaning qaysi nuqtasiga qo'yishini belgilaydi.
LEAD_SOURCE_DEFAULT_STAGE = {
    "visit": "trial_scheduled",
    "phone": "contacted",
    "instagram": "new",
    "telegram": "new",
    "referral": "new",
    "ads": "new",
    "other": "new",
}

# ---- Imtihonlar -------------------------------------------------------
# Bizda asosan unit testlar (12 ta unit), ularga qo'shimcha kurs o'rtasi,
# kurs oxiri va mock testlar bor.
EXAM_KINDS = ["unit", "mid", "end", "mock"]
EXAM_KIND_LABELS = {
    "unit": "Unit test",
    "mid": "Mid-course",
    "end": "End of course",
    "mock": "Mock test",
}
UNIT_COUNT = 12

# Mock IELTS band'ni foizga o'tkazish uchun eng yuqori band. Coin qoidasi
# hamma test turi uchun foizda ishlashi kerak, shuning uchun band -> foiz:
# 7.0 band => 7/9*100 = 77.8%.
MOCK_MAX_BAND = 9.0

# ---- Coin (gamification) ---------------------------------------------
# Coin qayerdan kelgani. Balans - shu yozuvlar yig'indisi, alohida
# "balans" ustuni yo'q: shunda hech qachon haqiqatdan uzilib qolmaydi.
COIN_SOURCES = ["daily", "exam", "manual", "reward"]
COIN_SOURCE_LABELS = {
    "daily": "Kunlik baho",
    "exam": "Imtihon",
    "manual": "Qo'lda",
    "reward": "Sovg'a",
}

# Kunlik baho shkalasi: ustoz har dars uchun 1-5 qo'yadi va o'sha ball
# aynan shuncha coinga teng (foydalanuvchi qoidasi).
DAILY_GRADE_MIN = 1
DAILY_GRADE_MAX = 5

# Imtihon natijasidan coin: foiz shu qiymatdan katta yoki teng bo'lsa,
# eng yuqori mos qator ishlaydi. Bu faqat BOSHLANG'ICH jadval - asoschi
# uni Gamification bo'limidan o'zgartira oladi.
DEFAULT_EXAM_COIN_RULES = [
    (90.0, 50),
    (80.0, 30),
    (70.0, 15),
    (60.0, 5),
]

# ---- Ruxsatlar --------------------------------------------------------
# Davomat, baho va imtihon - o'quv jarayoni, ustozlar ishlaydi.
TEACHING_ACCESS = FULL_ACCESS + [TEACHER, SUPPORT_TEACHER, EXAMINER]
# Sovg'a ro'yxati, coin qoidasi va qo'lda coin berish - faqat rahbariyat.
COIN_ADMIN = FULL_ACCESS

# ---- Adminlar (sotuv menejeri) KPI ------------------------------------
# Admin ish haqi = fiks oylik + eski to'lovlarni yig'ish bonusi +
# yangi mijoz bonusi. Ikkala bonus ham FILIAL ko'rsatkichi bo'yicha
# hisoblanadi: bir filialda ikkita admin bo'lsa, ikkalasi ham to'liq
# bonusni oladi.

# Eski to'lov = ilgari kamida bir marta to'lagan o'quvchining keyingi
# to'lovi. Yangi to'lov = o'quvchining eng birinchi to'lovi.

# Yig'ish foizi SUMMA bo'yicha: shu oyda eski o'quvchilarga hisoblangan
# summadan qanchasi kassaga tushgani.

# (min_students, max_students yoki None, min_percent, bonus)
DEFAULT_KPI_COLLECTION_RULES = [
    (51, 100, 95.0, 500_000),
    (101, 150, 95.0, 1_000_000),
    (101, 150, 90.0, 500_000),
    (151, None, 98.0, 2_000_000),
    (151, None, 90.0, 1_000_000),
    (151, None, 80.0, 500_000),
]
# 50 tagacha o'quvchida bonus yo'q - shuning uchun jadvalda qator ham yo'q.

# (yangi mijozlar soni, bonus)
DEFAULT_KPI_NEW_CLIENT_RULES = [
    (10, 50_000),
    (20, 120_000),
    (30, 300_000),
    (40, 500_000),
    (50, 750_000),
    (60, 1_200_000),
    (70, 1_800_000),
    (80, 2_400_000),
    (90, 3_150_000),
    (100, 4_000_000),
]

# KPI'ni ko'rish - rahbariyat; qoidalar va fiks oylikni o'zgartirish -
# faqat asoschi.
KPI_VIEW = FULL_ACCESS
KPI_ADMIN = [FOUNDER]

# ---- Fanlar va darajalar ----------------------------------------------
# Guruh ochilganda fan va daraja tanlanadi. Ta'lim sifati hisoboti ham
# shu kesimda chiqadi.

SUBJECTS = [
    ("english", "Ingliz tili"),
    ("russian", "Rus tili"),
    ("korean", "Koreys tili"),
    ("turkish", "Turk tili"),
    ("german", "Nemis tili"),
]
SUBJECT_LABELS = dict(SUBJECTS)

# Ingliz tilida o'z bosqichlarimiz bor; qolgan tillarda xalqaro
# CEFR shkalasi (A1-B2) ishlatiladi.
CEFR_LEVELS = [
    ("a1", "A1"),
    ("a2", "A2"),
    ("b1", "B1"),
    ("b2", "B2"),
]

ENGLISH_LEVELS = [
    ("step1", "Step 1"),
    ("step2", "Step 2"),
    ("step3", "Step 3"),
    ("step4", "Step 4"),
    ("ielts_intro", "IELTS Introduction"),
    ("ielts_foundation", "IELTS Foundation"),
    ("ielts_graduation", "IELTS Graduation"),
    ("cefr", "CEFR"),
]

SUBJECT_LEVELS = {
    "english": ENGLISH_LEVELS,
    "russian": CEFR_LEVELS,
    "korean": CEFR_LEVELS,
    "turkish": CEFR_LEVELS,
    "german": CEFR_LEVELS,
}

# Barcha daraja kalitlari - tekshirish uchun
ALL_LEVELS = {k for levels in SUBJECT_LEVELS.values() for k, _ in levels}
LEVEL_LABELS = {k: lbl for levels in SUBJECT_LEVELS.values() for k, lbl in levels}


def level_valid(subject: str, level: str) -> bool:
    """Daraja tanlangan fanga tegishlimi. Masalan rus tilida "Step 1"
    bo'lishi mumkin emas."""
    if not level:
        return True
    return level in {k for k, _ in SUBJECT_LEVELS.get(subject, [])}


# ---- Dars kunlari -----------------------------------------------------
WEEKDAYS = [
    ("mon", "Dushanba", "Du"),
    ("tue", "Seshanba", "Se"),
    ("wed", "Chorshanba", "Ch"),
    ("thu", "Payshanba", "Pa"),
    ("fri", "Juma", "Ju"),
    ("sat", "Shanba", "Sha"),
    ("sun", "Yakshanba", "Ya"),
]
WEEKDAY_KEYS = [k for k, _, _ in WEEKDAYS]
WEEKDAY_LABELS = {k: lbl for k, lbl, _ in WEEKDAYS}
