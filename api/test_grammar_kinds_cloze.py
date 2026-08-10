"""GRAMMAR MASHQ TURLARI + CLOZE + SO'Z LUG'ATI (2026-08-11)."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_gkc/db.sqlite"
os.makedirs("/tmp/verify_gkc", exist_ok=True)
if os.path.exists("/tmp/verify_gkc/db.sqlite"):
    os.remove("/tmp/verify_gkc/db.sqlite")
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
                   public_id="STU-KC-1")
db.add(s); db.commit()
u = models.User(username="998901112233",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112233','password':'jonyjony'}).json()['access_token']}"}

print("=== CLOZE YUKLANGAN ===")
n = (db.query(models.GrammarQuestion)
     .filter(models.GrammarQuestion.kind == "cloze",
             models.GrammarQuestion.is_active == 1).count())
ck("10 ta cloze", n, 10)

print("\n=== MAVZUDA TURLAR KO'RINADI ===")
r = c.get("/api/student/grammar/topics", headers=H)
t0 = r.json()["a1"]["topics"][0]
ck("Level 1 da cloze bor", "cloze" in t0["kinds"], True)
ck("4 tur ham bor", sorted(t0["kinds"]),
   ["cloze", "error", "fill", "order"])

print("\n=== TUR FILTRI ===")
topic = t0["topic"]
r = c.get("/api/student/grammar/round",
          params={"topic": topic, "kind": "fill"}, headers=H)
ck("faqat fill", {it["kind"] for it in r.json()["items"]}, {"fill"})
r = c.get("/api/student/grammar/round",
          params={"topic": topic, "kind": "cloze"}, headers=H)
items = r.json()["items"]
ck("cloze round", {it["kind"] for it in items}, {"cloze"})
cz = items[0]
ck("variantlar guruh-guruh", isinstance(cz["options"][0], list), True)
ck("javob sirda", "answer" in cz, False)

print("\n=== CLOZE TEKSHIRUVI ===")
q = db.query(models.GrammarQuestion).get(cz["id"])
answers = json.loads(q.answer)
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q.id, "answer": "|".join(answers)})
ck("to'g'ri to'ldirish qabul", r.json()["correct"], True)
wrong = answers[:]
wrong[0] = "XATO"
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q.id, "answer": "|".join(wrong)})
ck("bitta xato - rad", r.json()["correct"], False)
ck("to'g'ri javoblar qaytadi", "|" in r.json()["expected"], True)

print("\n=== SO'Z LUG'ATI (reading pop-up) ===")
r = c.get("/api/student/word-lookup?w=Businessman.", headers=H)
ck("topildi", r.json()["found"], True)
ck("tarjimasi bor", bool(r.json()["translation"]), True)
r = c.get("/api/student/word-lookup?w=qwertyzzz", headers=H)
ck("yo'q so'z - found False", r.json()["found"], False)
r = c.get("/api/student/word-lookup?w=apples", headers=H)
ck("ko'plik (-s) ham topiladi", r.json()["found"], True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
