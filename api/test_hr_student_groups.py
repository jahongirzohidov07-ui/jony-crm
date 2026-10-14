"""HR O'QUVCHINING GURUH TARIXINI KO'RADI (2026-09-24).

Jahongir: "hrga o'quvchilar avval qaysi guruhda bo'lgani xozirda
qaysi guruhda ekani ko'rinsin o'quvchi kartasiga kirganda".

Ilgari HR o'quvchi kartasini ochsa, guruhlar bo'limi ruxsat xatosi
berardi (u TEACHING_ACCESS uchun edi, HR unda yo'q).

Tekshiriladi:
  A. Ilgari HR uchun yopiq bo'lgan yo'l endi ochiq;
  B. Ro'yxatda hozirgi guruh ham, chiqib ketgan guruh ham bor —
     qachondan qachongacha va necha oy o'qigani bilan;
  C. Ustoz va o'quv bo'limi uchun eskicha ishlaydi, mutlaqo begona
     rol (inventar menejeri) ko'ra olmaydi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "hr_groups_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login",
        json={"username": u, "password": "Parol123!"}
    ).json()["access_token"]}


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
for un, nm, role in [("asos", "Asoschi", roles.FOUNDER),
                     ("hr", "HR Nodira", roles.HR_MANAGER),
                     ("ust", "Ustoz Anvar", roles.TEACHER),
                     ("xoj", "Xo'jalik Rustam", roles.FACILITY_MANAGER)]:
    db.add(models.User(username=un, full_name=nm,
                       password_hash=hash_password("Parol123!"),
                       role=role, branch_id=BID, is_active=1))
db.commit()
t = models.Teacher(full_name="Ustoz Anvar", branch_id=BID, is_active=1)
t2 = models.Teacher(full_name="Ustoz Kamola", branch_id=BID, is_active=1)
db.add_all([t, t2])
db.commit()
g1 = models.Group(name="Beginner A", subject="english", level="A1",
                  branch_id=BID, teacher_id=t.id, lesson_time="18:00",
                  monthly_fee=500000, lesson_days="135", capacity=15)
g2 = models.Group(name="Elementary B", subject="english", level="A2",
                  branch_id=BID, teacher_id=t2.id, lesson_time="16:00",
                  monthly_fee=500000, lesson_days="24", capacity=15)
db.add_all([g1, g2])
db.commit()
GID1, GID2 = g1.id, g2.id
s = models.Student(full_name="Aliyev Ali", branch_id=BID, group_id=GID1,
                   status="active", enrolled_date=TODAY - timedelta(days=200))
db.add(s)
db.commit()
SID = s.id
db.close()

H = tok("asos")
HH = tok("hr")
HT = tok("ust")
HX = tok("xoj")

# Eski guruhga biriktirilgan, keyin yangisiga o'tkazilgan
client.get(f"/api/students/{SID}/groups", headers=H)     # bog'lanish yaratiladi
r = client.post(f"/api/students/{SID}/groups", headers=H,
                json={"group_id": GID2})
ck("ikkinchi guruhga qo'shildi", r.status_code, 200)
# 2026-10-14: yangi guruh avval "Sinov" — asosiy guruhni olishdan oldin
# faollashtiriladi (aks holda sinovdagi guruh pulsiz asosiyga aylanardi).
r = client.post(f"/api/students/{SID}/groups/{GID2}/activate", headers=H,
                json={"on": TODAY.isoformat()})
ck("yangi guruh faollashtirildi", r.status_code, 200)
r = client.delete(f"/api/students/{SID}/groups/{GID1}", headers=H)
ck("eski guruhdan chiqarildi", r.status_code, 200)

print("\n=== A. HR UCHUN OCHIQ ===")
r = client.get(f"/api/students/{SID}/groups", headers=HH)
ck("HR ocha oladi", r.status_code, 200)
d = r.json()

print("\n=== B. AVVALGI VA HOZIRGI GURUH ===")
by = {x["group"]: x for x in d["rows"]}
ck("ikkala guruh ham ro'yxatda", sorted(by), ["Beginner A", "Elementary B"])
ck("hozirgisi faol", by["Elementary B"]["active"], True)
ck("avvalgisi yopilgan", by["Beginner A"]["active"], False)
ck("chiqqan sanasi yozilgan",
   by["Beginner A"]["left_date"], TODAY.isoformat())
ck("qo'shilgan sanasi bor", bool(by["Beginner A"]["joined_date"]), True)
ck("necha oy o'qigani hisoblandi",
   by["Beginner A"]["months"] > 6, True)
ck("avvalgi guruhning ustozi ham ko'rinadi",
   by["Beginner A"]["teacher"], "Ustoz Anvar")
ck("hozirgi guruh boshqa ustozda",
   by["Elementary B"]["teacher"], "Ustoz Kamola")
ck("faol guruhlar soni", d["active_count"], 1)

print("\n=== C. BOSHQA ROLLAR ===")
ck("ustoz ko'radi",
   client.get(f"/api/students/{SID}/groups", headers=HT).status_code, 200)
ck("xo'jalik menejeri ko'ra olmaydi",
   client.get(f"/api/students/{SID}/groups", headers=HX).status_code, 403)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
