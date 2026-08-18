"""MAQSAD BALLI (2026-08-18).

Jahongir: "o'quvchilar kirganda target ballini kirgizsa uni
progressidan kelib chiqib shu ballni olishga qancha vaqt qolganligni
korsatib tursin, shuncha yil, shuncha kun va shuncha soatdan keyin
olasan deb".
"""
import os, sys
from datetime import datetime, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/xpgoal.db"
if os.path.exists("/tmp/xpgoal.db"):
    os.remove("/tmp/xpgoal.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
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


db = SessionLocal()
b = models.Branch(name="B"); db.add(b); db.commit()
s = models.Student(full_name="Munisa", phone="998940411480",
                   branch_id=b.id, status="active")
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
print("\n=== 1. Boshida maqsad yo'q ===")
r = c.get("/api/student/goal", headers=H).json()
ck("target bo'sh", r["target"], None)

# ---------------------------------------------------------------- 2
print("\n=== 2. Maqsad qo'yish; hali XP yo'q — muddat aytilmaydi ===")
r = c.post("/api/student/goal", headers=H, json={"target": 3000}).json()
ck("saqlandi", r["target"], 3000)
ck("muddat yo'q (tezlik 0)", r["eta"], None)
ck("foiz 0", r["percent"], 0)

# ---------------------------------------------------------------- 3
print("\n=== 3. 30 kunlik tezlikdan muddat ===")
db = SessionLocal()
gam = (db.query(models.StudentGamification)
       .filter(models.StudentGamification.student_id == SID).first())
gam.lifetime_xp = 600
now = datetime.utcnow()
# Oxirgi 30 kunda 600 XP -> kuniga 20 XP. Qolgan 2400 XP -> 120 kun.
for i in range(6):
    db.add(models.XpTransaction(student_id=SID, amount=100,
                                created_at=now - timedelta(days=i * 5)))
db.commit(); db.close()
r = c.get("/api/student/goal", headers=H).json()
ck("foiz 20", r["percent"], 20)
ck("kunlik tezlik 20", r["per_day"], 20.0)
e = r["eta"]
ck("yil 0", e["years"], 0)
ck("kunlar ~120", 118 <= e["days"] <= 120, True)

# ---------------------------------------------------------------- 4
print("\n=== 4. Juda katta maqsad — yillarga o'tadi ===")
c.post("/api/student/goal", headers=H, json={"target": 300000})
e = c.get("/api/student/goal", headers=H).json()["eta"]
# (300000-600)/20 = 14970 kun ≈ 41 yil
ck("yillar hisoblandi", e["years"] >= 40, True)

# ---------------------------------------------------------------- 5
print("\n=== 5. Yetib bo'lingan maqsad ===")
r = c.post("/api/student/goal", headers=H, json={"target": 500}).json()
ck("done", r["done"], True)
ck("muddat kerak emas", r["eta"], None)

# ---------------------------------------------------------------- 6
print("\n=== 6. Chegara va olib tashlash ===")
r = c.post("/api/student/goal", headers=H, json={"target": 2000000})
ck("million chegarasi", r.status_code, 400)
r = c.post("/api/student/goal", headers=H, json={"target": 0}).json()
ck("0 = olib tashlandi", r["target"], None)
r = c.post("/api/student/goal", headers=H, json={"target": "abc"})
ck("harf qabul qilinmaydi", r.status_code, 400)

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
