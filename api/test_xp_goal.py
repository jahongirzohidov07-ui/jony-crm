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


# 2026-08-25: band endi UMUMIY balldan emas, olti ko'nikmaning
# o'rtachasidan chiqadi. Shu sababli _points_to_band olib tashlandi;
# _band_to_points esa "shu bandga chiqish uchun jami necha ball
# kerak" degan ma'noda qoldi.
print("=== 0. Band -> kerakli ball ===")
import roles as _r
ck("6.0 -> har ko'nikmada 40 ball kerak", _r.score_for_band(6.0), 40)
ck("6.0 -> jami ball", student_app._band_to_points(6.0),
   _r.points_for_score(40) * len(_r.SKILL_KEYS))
ck("9.0 jami ball 6.0 dan katta",
   student_app._band_to_points(9.0) > student_app._band_to_points(6.0), True)

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
ck("band 0 (hali mashq yo'q)", r["band"], 0.0)

# ---------------------------------------------------------------- 2
print("\n=== 2. Maqsad 6.0; mashq yo'q — muddat aytilmaydi ===")
r = c.post("/api/student/goal", headers=H, json={"target": 6.0}).json()
ck("saqlandi", r["target"], 6.0)
ck("muddat yo'q", r["eta"], None)

# ---------------------------------------------------------------- 3
print("\n=== 3. FAQAT GRAMMATIKA ishlagan bola 9.0 ga yaqinlashmaydi ===")
# 2026-08-25, Jahongir: "IELTS 6.5 TURGAN QIZGA 72 kunda IELTS 9.0
# olasan devoryabsan u faqat grammatika va lugat ishlagan bu tomonda
# reading listeninglari yoq". Shuni AYNAN takrorlaymiz.
db = SessionLocal()
for i in range(750):
    db.add(models.GrammarAttempt(student_id=SID, question_id=i + 1,
                                 correct=1, date=date.today()))
now = datetime.utcnow()
for i in range(6):
    db.add(models.XpTransaction(student_id=SID, amount=100,
                                created_at=now - timedelta(days=i * 5)))
db.commit(); db.close()
sk = c.get("/api/student/skills", headers=H).json()
gram = [x for x in sk["ielts"]["skills"] if x["key"] == "grammar"][0]
ck("grammatika bali 30-40", 30 <= gram["score"] <= 40, True)
ck("grammatika bandi 5.5-6.0", gram["band"] in (5.5, 6.0), True)
ck("o'qish bali 0", [x for x in sk["ielts"]["skills"]
                     if x["key"] == "reading"][0]["score"], 0)
r = c.get("/api/student/goal", headers=H).json()
ck("UMUMIY band 1.5 dan past (chunki 5 ko'nikma bo'sh)",
   r["band"] <= 1.5, True)
ck("eng zaif tomon ko'rsatiladi", bool(sk["ielts"]["weakest"]), True)
e = r["eta"]
ck("muddat keldi", e is not None, True)
ck("6.0 gacha 1 yildan ko'p",
   (e["years"] * 365 + e["days"]) > 365 if e else False, True)

# ---------------------------------------------------------------- 4
print("\n=== 4. Hamma ko'nikma ishlansa — band ko'tariladi ===")
db = SessionLocal()
# har ko'nikmaga ~950 ball (B2 darajasi = IELTS 6.0)
for i in range(400):
    db.add(models.GrammarAttempt(student_id=SID, question_id=2000 + i,
                                 correct=1, date=date.today()))
for i in range(950):
    db.add(models.VocabAttempt(student_id=SID, word_id=i + 1,
                               game="en_uz", correct=1,
                               date=date.today()))
for skill in ("reading", "listening", "writing", "speaking"):
    for i in range(950):
        db.add(models.SkillAttempt(student_id=SID, skill=skill,
                                   ref=f"x:{i}", correct=1,
                                   date=date.today()))
db.commit(); db.close()
sk = c.get("/api/student/skills", headers=H).json()
for x in sk["ielts"]["skills"]:
    # grammatikada 3-bosqichdagi 750 ball ustiga qo'shildi -> 6.5
    ck(f"{x['key']} bandi >= 6.0", x["band"] >= 6.0, True)
ck("UMUMIY band 6.0", sk["ielts"]["band"], 6.0)
r = c.post("/api/student/goal", headers=H, json={"target": 6.0}).json()
ck("maqsadga yetildi", r["done"], True)

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
