"""GRAMMAR A1 DASTURI + A2 QULFI (2026-08-11).

Jahongir bergan 37 mavzulik A1 tartibi, BOSS levellar, va "A1
tugamaguncha A2 umuman ko'rinmasin" qoidasi."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_ga1/db.sqlite"
os.makedirs("/tmp/verify_ga1", exist_ok=True)
if os.path.exists("/tmp/verify_ga1/db.sqlite"):
    os.remove("/tmp/verify_ga1/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
s = models.Student(full_name="Ali Valiyev", branch_id=b.id,
                   status="active", phone="998901112233",
                   public_id="STU-GA-1")
db.add(s); db.commit()
u = models.User(username="998901112233",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112233','password':'jonyjony'}).json()['access_token']}"}

print("=== A1 TUZILISHI ===")
r = c.get("/api/student/grammar/topics", headers=H)
d = r.json()
a1 = d["a1"]
ck("37 mavzu", a1["total"], 37)
ck("1-mavzu TO BE + sifat",
   "TO BE + sifat" in a1["topics"][0]["topic"], True)
ck("tartib saqlangan (7-o'rin BOSS hozirgi zamon)",
   a1["topics"][6]["boss"], True)
bosses = sum(1 for t in a1["topics"] if t["boss"])
ck("8 ta BOSS", bosses, 8)
ck("A1 hali tugamagan", a1["completed"], False)

print("\n=== A2 QULF: MAVZULARI KO'RINMAYDI ===")
ck("a2_locked", d["a2_locked"], True)
ck("A2 mavzulari BO'SH (umuman ko'rinmaydi)",
   d["a2"]["topics"], [])

print("\n=== ESKI MAVZULAR O'CHIRILGAN ===")
old_active = (db.query(models.GrammarQuestion)
              .filter(models.GrammarQuestion.topic == "Present Simple",
                      models.GrammarQuestion.is_active == 1).count())
ck("eski 'Present Simple' faol emas", old_active, 0)

print("\n=== ROUND YANGI MAVZUDA ISHLAYDI ===")
topic = a1["topics"][0]["topic"]
r = c.get("/api/student/grammar/round", params={"topic": topic},
          headers=H)
ck("round 200", r.status_code, 200)
items = r.json()["items"]
ck("javob sirda", any("answer" in it for it in items), False)

q = (db.query(models.GrammarQuestion)
     .filter(models.GrammarQuestion.topic == topic,
             models.GrammarQuestion.kind == "fill").first())
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q.id, "answer": q.answer})
ck("javob qabul + XP", (r.json()["correct"], r.json()["xp"]),
   (True, 1.0))

print("\n=== A1 TUGATILSA A2 OCHILADI ===")
# Hammasini "yechilgan" qilamiz (to'g'ridan-to'g'ri bazaga)
for gq in (db.query(models.GrammarQuestion)
           .filter(models.GrammarQuestion.is_active == 1,
                   models.GrammarQuestion.level == "A1").all()):
    db.add(models.GrammarAttempt(student_id=s.id, question_id=gq.id,
                                 correct=1, date=date.today()))
db.commit()
r = c.get("/api/student/grammar/topics", headers=H)
d = r.json()
ck("A1 completed", d["a1"]["completed"], True)
ck("qulf ochildi", d["a2_locked"], False)
# 2026-08-12: A2 kontenti to'ldirildi (grammar_seed2) - endi A1
# tugagach A2 DARHOL tayyor bo'ladi.
ck("A2 tayyor (kontent to'ldirilgan)",
   d["a2"]["ready"], True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
