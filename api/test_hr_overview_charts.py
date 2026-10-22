"""HR DASHBOARD GRAFIKLARI (2026-10-22).

Jahongir: "hr dashboard ham professional, statistika va barchartlar
qo'shib ber rangli".

Tekshiriladi: /api/hr/overview avvalgi maydonlarni qaytaradi va
"charts" — lavozim/filial bo'yicha faol xodimlar, 6 oylik kelgan/ketgan
(ketish jarayoni yakunlangan + ustoz kartasidagi ketgan sana, bir odam
ikki marta sanalmaydi), nomzodlar voronkasi va manbalari.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "hr_overview_charts_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b1, b2 = models.Branch(name="Zafar"), models.Branch(name="Chilonzor")
db.add_all([b1, b2]); db.commit()
T = roles.local_today()


def user(login, role, br, active=1, hired=None):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login, role=role, branch_id=br.id,
                    is_active=active, hired_date=hired)
    db.add(u); db.commit()
    return u


user("hr", roles.HR_MANAGER, b1, hired=T)
user("t1", roles.TEACHER, b1, hired=T)
user("t2", roles.TEACHER, b2, hired=date(2020, 1, 1))
gone = user("ketdi", roles.TEACHER, b2, active=0, hired=date(2020, 1, 1))
user("bola", roles.STUDENT, b1)                    # xodim emas
db.add(models.Offboarding(user_id=gone.id, last_day=T, completed=1))
# Shu odamning ustoz kartasi ham ketgan — ikki marta sanalmasin
db.add(models.Teacher(full_name="ketdi", user_id=gone.id, branch_id=b2.id,
                      is_active=0, left_date=T))
db.add_all([models.Candidate(full_name="A", stage="applied",
                             source="instagram"),
            models.Candidate(full_name="B", stage="interview",
                             source="instagram"),
            models.Candidate(full_name="C", stage="hired",
                             source="referral")])
db.commit()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "hr", "password": "x"}
).json()["access_token"]}
r = c.get("/api/hr/overview", headers=H)
ck("200", r.status_code, 200)
d = r.json()
ck("eski kartalar joyida", len(d["cards"]), 8)
ch = d["charts"]
ck("lavozim: ustoz 2 ta (ketgan sanalmaydi)",
   {x["label"]: x["value"] for x in ch["by_role"]}.get(
       roles.UZ_LABELS[roles.TEACHER]), 2)
ck("filial bo'yicha", {x["label"]: x["value"] for x in ch["by_branch"]},
   {"Zafar": 2, "Chilonzor": 1})
ck("6 oy", len(ch["flow"]), 6)
ck("shu oy kelgan 2", ch["flow"][-1]["hired"], 2)
ck("shu oy ketgan 1 (ikki marta emas)", ch["flow"][-1]["left"], 1)
ck("voronka: suhbat 1",
   {x["key"]: x["value"] for x in ch["funnel"]}["interview"], 1)
ck("manba: Instagram 2", ch["sources"][0], {"label": "Instagram", "value": 2})

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
