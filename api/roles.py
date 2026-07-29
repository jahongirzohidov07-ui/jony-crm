"""Jony Academy org-chart roles (not the Jony School kurator model - separate context).

Internal keys are plain ASCII for safe DB/string comparisons; UZ_LABELS gives
the human-readable Uzbek label for each, used by the frontend.
"""

ADMINISTRATOR = "administrator"
BRANCH_MANAGER = "branch_manager"       # Filial menejeri
TEACHER = "teacher"                     # O'qituvchi
SUPPORT_TEACHER = "support_teacher"
EXAMINER = "examiner"
HR_MANAGER = "hr_manager"
SMM_MANAGER = "smm_manager"

ALL_ROLES = [
    ADMINISTRATOR,
    BRANCH_MANAGER,
    TEACHER,
    SUPPORT_TEACHER,
    EXAMINER,
    HR_MANAGER,
    SMM_MANAGER,
]

UZ_LABELS = {
    ADMINISTRATOR: "Administrator",
    BRANCH_MANAGER: "Filial menejeri",
    TEACHER: "O'qituvchi",
    SUPPORT_TEACHER: "Support teacher",
    EXAMINER: "Examiner",
    HR_MANAGER: "HR manager",
    SMM_MANAGER: "SMM manager",
}

# ---- Permission groups -----------------------------------------------
# Full operational control (create/edit/delete students, groups, payments,
# manage branches).
FULL_ACCESS = [ADMINISTRATOR, BRANCH_MANAGER]

# Can view/edit students & groups day-to-day, but not touch finance or delete.
TEACHING_STAFF = FULL_ACCESS + [TEACHER, SUPPORT_TEACHER, EXAMINER]

# Can manage teacher/staff records (HR's actual job) plus everything
# TEACHING_STAFF can already do.
STAFF_MANAGERS = FULL_ACCESS + [HR_MANAGER]

# Finance (payments, balances, discounts) - kept to the smallest group since
# mistakes here cost real money.
FINANCE_ACCESS = FULL_ACCESS

# SMM manager gets read-only access to aggregate stats (for content
# planning) but no access to individual student records or money.
DASHBOARD_ONLY = [SMM_MANAGER]

# Lidlar (sales funnel). SMM manager is included on purpose - the Instagram
# and Telegram leads are theirs, so they need to log and follow them up.
# Support teacher handles walk-ins at reception.
LEAD_ACCESS = FULL_ACCESS + [SMM_MANAGER, SUPPORT_TEACHER]

# ---- Lead funnel -----------------------------------------------------
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

# Manba lidni voronkaning qaysi nuqtasiga qo'yishini belgilaydi: o'zi kirib
# kelgan odam bilan allaqachon yuzma-yuz gaplashilgan, o'zi qo'ng'iroq
# qilgani esa "bog'lanildi" bosqichida. Onlayn so'rov qoldirganlar esa
# hali kutmoqda - ularga qo'ng'iroq qilish kerak.
LEAD_SOURCE_DEFAULT_STAGE = {
    "visit": "trial_scheduled",
    "phone": "contacted",
    "instagram": "new",
    "telegram": "new",
    "referral": "new",
    "ads": "new",
    "other": "new",
}
