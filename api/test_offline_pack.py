"""OFFLINE MASHQ TO'PLAMI (2026-10-07).

Jahongir: "ilovada offline rejimda ham mashqlar ishlash mumkin bo'lsin".

Tekshiriladi: to'plam faqat o'quvchiga ochiq, lug'at va grammatika
(faqat fill/error) keladi, javob kalitlari bor (telefonda tekshirish
uchun), lekin XP baribir server tekshiruvidan o'tadi — offline
navbatdagi noto'g'ri javob serverda ham noto'g'ri.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "offline_pack_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
s = models.Student(full_name="Ali Offline", branch_id=b.id, status="active",
                   phone="998907770011", public_id="STU-OFF-1")
db.add(s); db.commit()
u = models.User(username="998907770011", password_hash=hash_password("x"),
                full_name="Ali Offline", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u)
db.add(models.User(username="adm", password_hash=hash_password("x"),
                   full_name="Admin", role=roles.ADMINISTRATOR,
                   branch_id=b.id, is_active=1))
db.commit()
s.user_id = u.id; db.commit()
if db.query(models.VocabWord).filter(models.VocabWord.is_active == 1).count() < 4:
    for i, (w, t) in enumerate([("apple", "olma"), ("book", "kitob"),
                                ("cat", "mushuk"), ("dog", "it"),
                                ("house", "uy")]):
        db.add(models.VocabWord(word=w, translation=t, is_active=1))
    db.commit()
db.close()


def H(un):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": un, "password": "x"}
    ).json()["access_token"]}


hs, ha = H("998907770011"), H("adm")

print("=== Ruxsat ===")
ck("xodimga yopiq", c.get("/api/student/offline/pack", headers=ha).status_code, 403)
ck("loginsiz yopiq", c.get("/api/student/offline/pack").status_code, 401)

print("=== To'plam ===")
r = c.get("/api/student/offline/pack?language=en", headers=hs)
ck("o'quvchiga ochiq", r.status_code, 200)
p = r.json()
ck("lug'at bor", len(p["vocab"]) >= 4, True)
ck("lug'at 300 tadan oshmaydi", len(p["vocab"]) <= 300, True)
ck("so'zda tarjima bor", all(v["word"] and v["translation"] for v in p["vocab"]), True)
ck("grammatika bor", len(p["grammar"]) > 0, True)
ck("grammatika 200 tadan oshmaydi", len(p["grammar"]) <= 200, True)
ck("faqat fill/error", {g["kind"] for g in p["grammar"]} <= {"fill", "error"}, True)
ck("javob kaliti bor", all(g["answer"] for g in p["grammar"]), True)
ck("javob variantlar ichida", all(g["answer"] in g["options"] for g in p["grammar"]), True)
ck("noto'g'ri til -> en", c.get("/api/student/offline/pack?language=xx",
                                 headers=hs).json()["language"], "en")

print("=== Navbatdagi javob server tekshiruvidan o'tadi ===")
g = p["grammar"][0]
wrong = next((o for o in g["options"] if o != g["answer"]), "YOQ")
r = c.post("/api/student/grammar/answer", headers=hs,
           json={"question_id": g["id"], "answer": wrong})
ck("noto'g'ri javob serverda ham noto'g'ri", r.json()["correct"], False)
ck("XP berilmadi", r.json()["xp"], 0.0)
r = c.post("/api/student/grammar/answer", headers=hs,
           json={"question_id": g["id"], "answer": g["answer"]})
ck("to'g'ri javob qabul", r.json()["correct"], True)
v = p["vocab"][0]
r = c.post("/api/student/vocab/answer", headers=hs,
           json={"word_id": v["id"], "game": "en_uz", "answer": v["translation"]})
ck("lug'at javobi qabul", r.json()["correct"], True)

print("\n" + ("HAMMASI OK" if not fails else f"{len(fails)} XATO: {fails}"))
sys.exit(1 if fails else 0)
