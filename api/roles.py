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

# ---- Xarajat turlari --------------------------------------------------
# DIQQAT: ustozlar ish haqi bu ro'yxatda YO'Q - u TeacherPayout
# jadvalidan avtomatik olinadi. Agar uni yana qo'lda kiritsangiz,
# P&L'da ikki marta hisoblanib ketadi. "salary" - ustozlardan boshqa
# xodimlar (administrator, farrosh, qorovul va h.k.) uchun.
EXPENSE_CATEGORIES = [
    "rent",       # Ijara
    "utilities",  # Kommunal (svet, suv, gaz, internet)
    "salary",     # Xodimlar oyligi (ustozlardan tashqari)
    "ads",        # Reklama
    "tax",        # Soliq
    "repair",     # Ta'mir
    "equipment",  # Jihoz / kanstovar
    "other",      # Boshqa
]

EXPENSE_CATEGORY_LABELS = {
    "rent": "Ijara",
    "utilities": "Kommunal",
    "salary": "Xodimlar oyligi",
    "ads": "Reklama",
    "tax": "Soliq",
    "repair": "Ta'mir",
    "equipment": "Jihoz / kanstovar",
    "other": "Boshqa",
}

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
