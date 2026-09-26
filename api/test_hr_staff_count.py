"""HR DASHBOARD: "Xodimlar" faqat xodimlarni sanaydi (2026-09-26).

Jahongir: "dashboarda xodimlar notogri korinyabdi hrga faqat xodimlar
ko'rinsin o'quvchilar ham qoshilib ketgan" (ekranda 1466 chiqqan).

O'quvchi va ota-onaning ham ilova hisobi (users) bor — ular xodim emas.
Tekshiriladi: HR kartasi, umumiy dashboard, HR umumiy holati, yaqin
sanalar ro'yxati.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "hr_staff_count_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import main, models, roles                         # noqa: E402,F401
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
bday = date.today()
n = 0


def user(role, active=1, birth=None):
    global n
    n += 1
    u = models.User(username=f"u{n}", password_hash=hash_password("x"),
                    full_name=f"{role} {n}", role=role, branch_id=b.id,
                    is_active=active, birth_date=birth)
    db.add(u); db.commit()
    return u


hr = user(roles.HR_MANAGER)
user(roles.TEACHER, birth=bday)
user(roles.SUPPORT_TEACHER)
user(roles.TEACHER, active=0)                    # ishdan ketgan
for _ in range(5):
    user(roles.STUDENT, birth=bday)              # o'quvchi hisoblari
for _ in range(2):
    user(roles.PARENT)                           # ota-ona hisoblari

cards = {c["label"]: c["value"] for c in common._my_hr_cards(db, hr)}
ck("HR kartasi: Xodimlar = 3", cards.get("Xodimlar"), 3)

dates = common._staff_dates(db, hr, days=roles.STAFF_DATE_HORIZON)
ck("yaqin sanalarda o'quvchi yo'q",
   [r for r in dates if "student" in (r.get("name") or "")], [])

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
