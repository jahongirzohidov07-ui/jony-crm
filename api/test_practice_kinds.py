"""YANGI MASHQ TURLARI (2026-08-11, Jahongir spetsifikatsiyasi)."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_pk/db.sqlite"
os.makedirs("/tmp/verify_pk", exist_ok=True)
if os.path.exists("/tmp/verify_pk/db.sqlite"):
    os.remove("/tmp/verify_pk/db.sqlite")
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
                   public_id="STU-PK-1")
db.add(s); db.commit()
u = models.User(username="998901112233",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112233','password':'jonyjony'}).json()['access_token']}"}

print("=== SEED ===")
ck("91 element", db.query(models.PracticeItem).count(), 91)

def item_of(ref):
    return db.query(models.PracticeItem).get(int(ref.split(":")[1]))

print("\n=== READING: T/F/NG ===")
r = c.get("/api/student/practice/reading/round?kind=read_tfng",
          headers=H)
d = r.json()
ck("matn keladi", bool(d["text"]["body"]), True)
it = d["items"][0]
ck("variantlar T/F/NG", it["options"],
   ["True", "False", "Not Given"])
pi = item_of(it["ref"])
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "reading", "ref": it["ref"],
                 "answer": pi.answer})
ck("to'g'ri qabul + XP", (r.json()["correct"], r.json()["xp"]),
   (True, 1.0))

print("\n=== READING: GAP (ko'p blank) ===")
r = c.get("/api/student/practice/reading/round?kind=read_gap",
          headers=H)
it = r.json()["items"][0]
ck("blank variantlari guruh-guruh",
   isinstance(it["options"][0], list), True)
pi = item_of(it["ref"])
want = json.loads(pi.answer)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "reading", "ref": it["ref"],
                 "answer": "|".join(want)})
ck("to'g'ri to'ldirish", r.json()["correct"], True)
bad = want[:]; bad[0] = "XATO"
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "reading", "ref": it["ref"],
                 "answer": "|".join(bad)})
ck("bitta xato - rad", r.json()["correct"], False)

print("\n=== LISTENING: IMG / QA / ORDER ===")
r = c.get("/api/student/practice/listening/round?kind=listen_img",
          headers=H)
it = r.json()["items"][0]
ck("emoji variantlar", "emoji" in it["options"][0], True)
pi = item_of(it["ref"])
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "listening", "ref": it["ref"],
                 "answer": pi.answer})
ck("img to'g'ri", r.json()["correct"], True)

r = c.get("/api/student/practice/listening/round?kind=listen_qa",
          headers=H)
it = r.json()["items"][0]
ck("savol va audio bor", bool(it["prompt"]) and bool(it["say"]),
   True)

r = c.get("/api/student/practice/listening/round?kind=listen_order",
          headers=H)
it = r.json()["items"][0]
pi = item_of(it["ref"])
steps = json.loads(pi.answer)
ck("qadamlar aralashtirilgan yoki 2+ ta", len(it["options"]) >= 2,
   True)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "listening", "ref": it["ref"],
                 "answer": "|".join(steps)})
ck("to'g'ri tartib qabul", r.json()["correct"], True)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "listening", "ref": it["ref"],
                 "answer": "|".join(reversed(steps))})
ck("teskari tartib rad", r.json()["correct"], False)

print("\n=== WRITING: TRANSFORM (alt javoblar) ===")
r = c.get("/api/student/practice/writing/round?kind=write_transform",
          headers=H)
it = r.json()["items"][0]
pi = item_of(it["ref"])
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "writing", "ref": it["ref"],
                 "answer": pi.answer.upper() + "."})
ck("normallash bilan qabul", r.json()["correct"], True)
alts = json.loads(pi.alt) if pi.alt else []
if alts:
    r = c.post("/api/student/practice/answer", headers=H,
               json={"skill": "writing", "ref": it["ref"],
                     "answer": alts[0]})
    ck("muqobil javob ham qabul", r.json()["correct"], True)

print("\n=== SPEAKING: REPEAT / ANSWER ===")
r = c.get("/api/student/practice/speaking/round?kind=speak_repeat",
          headers=H)
it = r.json()["items"][0]
pi = item_of(it["ref"])
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "speaking", "ref": it["ref"],
                 "answer": pi.answer})
ck("to'liq takror qabul", r.json()["correct"], True)

r = c.get("/api/student/practice/speaking/round?kind=speak_answer",
          headers=H)
it = r.json()["items"][0]
pi = item_of(it["ref"])
pats = json.loads(pi.answer)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "speaking", "ref": it["ref"],
                 "answer": f"Well, {pats[0]} Aziz and something"})
ck("kalit ibora bor - qabul", r.json()["correct"], True)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "speaking", "ref": it["ref"],
                 "answer": "banana banana"})
ck("aloqasiz javob rad", r.json()["correct"], False)

print("\n=== ESKI TURLAR BUZILMAGAN ===")
r = c.get("/api/student/practice/listening/round", headers=H)
ck("eski diktant ishlaydi", r.status_code, 200)
r = c.get("/api/student/practice/reading/round", headers=H)
ck("eski reading MCQ ishlaydi", r.status_code, 200)

print("\n=== SKILLS BALLGA QO'SHILDI ===")
r = c.get("/api/student/skills", headers=H)
sk = {x["key"]: x["points"] for x in r.json()["skills"]}
ck("reading 2+", sk["reading"] >= 2, True)
ck("listening 2+", sk["listening"] >= 2, True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
