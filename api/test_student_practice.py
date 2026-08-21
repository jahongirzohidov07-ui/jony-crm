"""4 KO'NIKMA MASHQLARI (2026-08-10).

Jahongir: "listening, reading, writing, speaking mashqlari ham
qo'shaylik." Tekshiriladi: har roundning tuzilishi, serverdagi
tekshiruv (shu jumladan speaking'dagi so'z mosligi), XP bir
martaligi va ballarning skills kartasiga tushishi."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_practice/db.sqlite"
os.makedirs("/tmp/verify_practice", exist_ok=True)
if os.path.exists("/tmp/verify_practice/db.sqlite"):
    os.remove("/tmp/verify_practice/db.sqlite")
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
                   public_id="STU-PC-1")
db.add(s); db.commit()
u = models.User(username="998901112233",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'998901112233','password':'jonyjony'}).json()['access_token']}"}

print("=== SEEDLAR ===")
ck("reading matnlari yuklangan",
   db.query(models.ReadingText).count(), 12)
ck("reading savollari", db.query(models.ReadingQuestion).count(), 48)

print("\n=== READING ===")
r = c.get("/api/student/practice/reading/round", headers=H)
ck("status 200", r.status_code, 200)
d = r.json()
ck("matn keladi", bool(d["text"]["body"]), True)
ck("savollarda javob YO'Q",
   any("answer" in it for it in d["items"]), False)
ref = d["items"][0]["ref"]
qid = int(ref.split(":")[1])
q = db.query(models.ReadingQuestion).get(qid)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "reading", "ref": ref, "answer": q.answer})
ck("to'g'ri javob + XP", (r.json()["correct"], r.json()["xp"]),
   (True, 1.0))
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "reading", "ref": ref, "answer": q.answer})
ck("qayta XP yo'q", r.json()["xp"], 0.0)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "reading", "ref": ref, "answer": "xxx"})
ck("xato rad + izoh bor",
   (r.json()["correct"], bool(r.json()["expected"])), (False, True))

print("\n=== WRITING (uz -> en) ===")
r = c.get("/api/student/practice/writing/round", headers=H)
d = r.json()
ck("8 ta mashq", len(d["items"]), 8)
it = d["items"][0]
gq = db.query(models.GrammarQuestion).get(int(it["ref"].split(":")[1]))
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "writing", "ref": it["ref"],
                 "answer": gq.answer.upper() + "!"})
ck("normallash bilan qabul", r.json()["correct"], True)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "writing", "ref": it["ref"],
                 "answer": "totally wrong sentence"})
ck("xato rad", r.json()["correct"], False)

print("\n=== SPEAKING (so'z mosligi) ===")
r = c.get("/api/student/practice/speaking/round", headers=H)
it = r.json()["items"][0]
gq = db.query(models.GrammarQuestion).get(int(it["ref"].split(":")[1]))
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "speaking", "ref": it["ref"],
                 "answer": gq.answer})
ck("to'liq o'qilgan - qabul", r.json()["correct"], True)
words = gq.answer.split()
partial = " ".join(words[:max(1, len(words) // 3)])
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "speaking", "ref": it["ref"],
                 "answer": partial})
ck("chala o'qilgan - rad", r.json()["correct"], False)

print("\n=== LISTENING ===")
r = c.get("/api/student/practice/listening/round", headers=H)
d = r.json()
ck("8 ta mashq", len(d["items"]), 8)
kinds = {it["kind"] for it in d["items"]}
ck("aralash turlar bor", len(kinds) >= 2, True)
wit = next(it for it in d["items"] if it["ref"].startswith("word:"))
w = db.query(models.VocabWord).get(int(wit["ref"].split(":")[1]))
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "listening", "ref": wit["ref"],
                 "answer": w.word})
ck("so'z diktanti qabul", r.json()["correct"], True)

# Til filtri (2026-08-21, Jahongir: "listeninglar ham boshqa tillarni
# mashqlarini bervoryabdi aralashtirib... inglizcha chiqsin faqat")
r = c.get("/api/student/practice/listening/round?language=en", headers=H)
en_ids = [int(it["ref"].split(":")[1]) for it in r.json()["items"]
          if it["ref"].startswith("word:")]
langs = {w.language for w in
         db.query(models.VocabWord)
         .filter(models.VocabWord.id.in_(en_ids)).all()}
ck("EN roundda faqat en/None so'zlar", langs <= {"en", None}, True)

# Koreyscha so'z qo'shib, ko tilida round so'raymiz — faqat o'sha til
db.add(models.VocabWord(word="사과", translation="olma",
                        level="A1", language="ko"))
db.commit()
r = c.get("/api/student/practice/listening/round?language=ko", headers=H)
ko_items = r.json()["items"]
ck("KO roundda jumla diktanti yo'q (inglizcha aralashmaydi)",
   any(it["ref"].startswith("gram:") for it in ko_items), False)
ko_ids = [int(it["ref"].split(":")[1]) for it in ko_items]
ko_langs = {w.language for w in
            db.query(models.VocabWord)
            .filter(models.VocabWord.id.in_(ko_ids)).all()}
ck("KO roundda faqat koreys so'zlari", ko_langs, {"ko"})

print("\n=== SKILLS KARTASIGA TUSHDI ===")
r = c.get("/api/student/skills", headers=H)
sk = {x["key"]: x["points"] for x in r.json()["skills"]}
ck("reading balli", sk["reading"] >= 1, True)
ck("writing balli", sk["writing"] >= 1, True)
ck("speaking balli", sk["speaking"] >= 1, True)
ck("listening balli", sk["listening"] >= 1, True)

print("\n=== XAVFSIZLIK ===")
r = c.get("/api/student/practice/reading/round")
ck("loginsiz yopiq", r.status_code in (401, 403), True)
r = c.get("/api/student/practice/hacking/round", headers=H)
ck("mavjud bo'lmagan ko'nikma 404", r.status_code, 404)
r = c.post("/api/student/practice/answer", headers=H,
           json={"skill": "reading", "ref": "read:abc", "answer": "x"})
ck("buzuq ref 400", r.status_code, 400)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
