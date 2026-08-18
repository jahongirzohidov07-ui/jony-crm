"""MAQSAD: IELTS BALLI (2026-08-18).

Jahongir: "target ballini kirgizsa uni progressidan kelib chiqib shu
ballni olishga qancha vaqt qolganligni korsatib tursin" + aniqlashtirdi:
"nechi XP emas IELTS nechi olmoqchiligi bolishi kerak".
"""
import os, sys
from datetime import date, datetime, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/ieltsgoal.db"
if os.path.exists("/tmp/ieltsgoal.db"):
    os.remove("/tmp/ieltsgoal.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import student_app                                 # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


# Zinaning o'zi to'g'riligini avval sinaymiz
print("=== 0. Ball <-> IELTS aylantirish ===")
ck("0 ball -> 2.0", student_app._points_to_band(0), 2.0)
ck("500 ball -> 3.0", student_app._points_to_band(500), 3.0)
ck("750 ball -> 3.5", student_app._points_to_band(750), 3.5)
ck("2000 ball -> 6.0", student_app._points_to_band(2000), 6.0)
ck("juda katta -> 9.0", student_app._points_to_band(99999), 9.0)
ck("6.0 -> 2000 ball", student_app._band_to_points(6.0), 2000.0)
ck("7.0 -> 2500 ball", student_app._band_to_points(7.0), 2500.0)

db = SessionLocal()
b = models.Branch(name="B"); db.add(b); db.commit()
s = models.Student(full_name="Munisa", branch_id=b.id, status="active")
db.add(s); db.commit(); SID = s.id
u = models.User(username="stu", full_name="Munisa",
                password_hash=hash_password("x"), role=roles.STUDENT,
                branch_id=b.id)
db.add(u); db.commit()
s.user_id = u.id
db.commit(); db.close()
tok = c.post("/api/auth/login",
             json={"username": "stu", "password": "x"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

# ---------------------------------------------------------------- 1
print("\n=== 1. Boshida: maqsad yo'q, daraja ko'rinadi ===")
r = c.get("/api/student/goal", headers=H).json()
ck("target bo'sh", r["target"], None)
ck("band 2.0 (yangi o'quvchi)", r["band"], 2.0)

# ---------------------------------------------------------------- 2
print("\n=== 2. Maqsad 6.0; mashq yo'q — muddat aytilmaydi ===")
r = c.post("/api/student/goal", headers=H, json={"target": 6.0}).json()
ck("saqlandi", r["target"], 6.0)
ck("muddat yo'q", r["eta"], None)

# ---------------------------------------------------------------- 3
print("\n=== 3. 750 mashq balli (~3.5) + kuniga 20 XP tezlik ===")
db = SessionLocal()
# 750 to'g'ri javob — grammatikadan (eng soddasi: 750 ta alohida savol)
for i in range(750):
    db.add(models.GrammarAttempt(student_id=SID, question_id=i + 1,
                                 correct=1, date=date.today()))
now = datetime.utcnow()
for i in range(6):
    db.add(models.XpTransaction(student_id=SID, amount=100,
                                created_at=now - timedelta(days=i * 5)))
db.commit(); db.close()
r = c.get("/api/student/goal", headers=H).json()
ck("hozirgi band 3.5", r["band"], 3.5)
# 6.0 uchun 2000 ball kerak, bor 750, kuniga 20 -> 62.5 kun
e = r["eta"]
ck("muddat keldi", e is not None, True)
ck("kunlar ~62", 61 <= e["days"] <= 63, True)
ck("foiz 37-38", r["percent"] in (37, 38), True)

# ---------------------------------------------------------------- 4
print("\n=== 4. Maqsadga yetilgan bo'lsa ===")
r = c.post("/api/student/goal", headers=H, json={"target": 3.5}).json()
ck("done", r["done"], True)

# ---------------------------------------------------------------- 5
print("\n=== 5. Chegaralar ===")
ck("9.5 rad", c.post("/api/student/goal", headers=H,
                     json={"target": 9.5}).status_code, 400)
ck("6.3 rad (0.5 qadam emas)", c.post("/api/student/goal", headers=H,
                                      json={"target": 6.3}).status_code, 400)
ck("2.0 rad (past)", c.post("/api/student/goal", headers=H,
                            json={"target": 2.0}).status_code, 400)
r = c.post("/api/student/goal", headers=H, json={"target": 0}).json()
ck("0 = olib tashlash", r["target"], None)

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
