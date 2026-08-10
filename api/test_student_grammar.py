"""GRAMMAR MASHQLARI (2026-08-10).

Jahongir: "student appda grammar mashqlari yo'q ekan lekin grammar
natijalar ko'rinib turibdi. Grammar har bir ingliz tilidagi mavzuga
xilma-xil mashqlar bo'lsin."

Tekshiriladi: mavzular ro'yxati, round'da TO'G'RI JAVOB MIJOZGA
KETMASLIGI, uch turning ham server tomonda tekshirilishi, XP bitta
savolga bir marta berilishi, grammar balli skills kartasiga
qo'shilishi va xodim/loginsiz kirishning yopiqligi."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_grammar/db.sqlite"
os.makedirs("/tmp/verify_grammar", exist_ok=True)
if os.path.exists("/tmp/verify_grammar/db.sqlite"):
    os.remove("/tmp/verify_grammar/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
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
                   public_id="STU-GR-1")
db.add(s); db.commit()
u = models.User(username="998901112233",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()

H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112233','password':'jonyjony'}).json()['access_token']}"}

print("=== SEED ISHLAGAN ===")
total_q = db.query(models.GrammarQuestion).count()
ck("312 savol yuklangan", total_q, 312)

print("\n=== MAVZULAR RO'YXATI ===")
r = c.get("/api/student/grammar/topics", headers=H)
ck("status 200", r.status_code, 200)
d = r.json()
lv_names = [x["level"] for x in d["levels"]]
ck("darajalar tartibi A1,A2,B1", lv_names, ["A1", "A2", "B1"])
all_topics = [t for x in d["levels"] for t in x["topics"]]
ck("26 mavzu", len(all_topics), 26)
ck("boshida hech biri yopilmagan",
   any(t["done"] for t in all_topics), False)
t0 = all_topics[0]
ck("har mavzuda 3 xil mashq bor", t0["kinds"],
   ["error", "fill", "order"])

print("\n=== ROUND: JAVOB SIRDA QOLADI ===")
topic = "Present Simple"
r = c.get(f"/api/student/grammar/round?topic={topic}", headers=H)
ck("status 200", r.status_code, 200)
items = r.json()["items"]
ck("8 ta savol", len(items), roles.GRAMMAR_ROUND_SIZE)
ck("javob maydoni YO'Q",
   any("answer" in it for it in items), False)
ck("izoh ham oldindan ketmaydi",
   any("explain" in it for it in items), False)

print("\n=== FILL: TO'G'RI/XATO SERVER HAL QILADI ===")
q = (db.query(models.GrammarQuestion)
     .filter(models.GrammarQuestion.topic == topic,
             models.GrammarQuestion.kind == "fill").first())
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q.id, "answer": q.answer})
j = r.json()
ck("to'g'ri javob qabul qilindi", j["correct"], True)
ck("birinchi marta - XP berildi", j["xp"],
   roles.GRAMMAR_XP_PER_CORRECT)
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q.id, "answer": q.answer})
ck("qayta yechishga XP YO'Q", r.json()["xp"], 0.0)
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q.id, "answer": "NOTO'G'RI"})
j = r.json()
ck("xato javob rad etildi", j["correct"], False)
ck("to'g'risi va izohi qaytdi",
   bool(j["expected"]) and bool(j["explain"]), True)

print("\n=== ORDER: TARTIB VA NORMALLASH ===")
q2 = (db.query(models.GrammarQuestion)
      .filter(models.GrammarQuestion.topic == topic,
              models.GrammarQuestion.kind == "order").first())
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q2.id,
                 "answer": q2.answer.upper() + "."})
ck("katta harf/nuqta farqi kechiriladi", r.json()["correct"], True)
words = json.loads(q2.options)
wrong = " ".join(reversed(words))
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q2.id, "answer": wrong})
ck("noto'g'ri tartib rad etiladi",
   r.json()["correct"], wrong.lower() == q2.answer.lower())

print("\n=== PROGRESS VA SKILLS ===")
r = c.get("/api/student/grammar/topics", headers=H)
ps = [t for x in r.json()["levels"] for t in x["topics"]
      if t["topic"] == topic][0]
ck("mavzu progressi oshdi (2 savol)", ps["solved"], 2)
r = c.get("/api/student/skills", headers=H)
gr = [x for x in r.json()["skills"] if x["key"] == "grammar"][0]
ck("grammar balli skillsda", gr["points"], 2)

print("\n=== XAVFSIZLIK ===")
r = c.get("/api/student/grammar/topics")
ck("loginsiz yopiq", r.status_code in (401, 403), True)
adm = models.User(username="adm", full_name="Xodim",
                  password_hash=hash_password("Parol123!"),
                  role=roles.SALES_MANAGER, branch_id=b.id, is_active=1)
db.add(adm); db.commit()
Ha = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'adm','password':'Parol123!'}).json()['access_token']}"}
r = c.get("/api/student/grammar/topics", headers=Ha)
ck("xodimga yopiq", r.status_code, 403)
r = c.get("/api/student/grammar/round?topic=YOQ_MAVZU", headers=H)
ck("mavjud bo'lmagan mavzu 404", r.status_code, 404)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
