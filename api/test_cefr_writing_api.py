# -*- coding: utf-8 -*-
"""CEFR Writing — HTTP darajasida uchidan-uchiga tekshiruv.

test_cefr_writing.py KONTENTni tekshiradi. Bu esa boshqa savolga
javob beradi: o'quvchi ilovada tugmani bosganda ROSTDAN ishlaydimi?

Tekshiriladi:
  - bosh ekran ma'lumot qaytaradimi
  - qo'llanma ochiladimi
  - mashq keladimi, to'g'ri javob qabul qilinadimi, XP berilyaptimi
  - bir mashqni ikki marta yechib XP ikki marta olinmasligi
  - vazifa berilganda NAMUNA JAVOB SIZIB CHIQMASLIGI
  - yozuv topshirilganda baho va namuna qaytishi
  - AI kaliti yo'q bo'lganda ham javob to'liq bo'lishi
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_cw/db.sqlite"
os.makedirs("/tmp/verify_cw", exist_ok=True)
if os.path.exists("/tmp/verify_cw/db.sqlite"):
    os.remove("/tmp/verify_cw/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: F401,E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
import cefr_writing_drills as D                    # noqa: E402
import cefr_writing_tasks as T                     # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar")
db.add(b)
db.commit()
s = models.Student(full_name="Writing Test", branch_id=b.id,
                   status="active", phone="998901110099",
                   public_id="STU-CW-1")
db.add(s)
db.commit()
u = models.User(username="998901110099",
                password_hash=hash_password("jonyjony"),
                role="student", full_name="Writing Test",
                branch_id=b.id)
db.add(u)
db.commit()
s.user_id = u.id
db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "998901110099", "password": "jonyjony"}
).json()["access_token"]}

print("=== BOSH EKRAN ===")
d = c.get("/api/student/cefr/writing/home", headers=H).json()
ck("10 xat turi", len(d["guide"]), 10)
ck("7 mashq turi", len(d["drills"]), 7)
ck("uch qismli format", len(d["format"]), 3)
ck("Part 1 vazifalari", d["tasks"]["part1"] >= 10, True)
ck("boshida hech narsa yechilmagan",
   sum(x["solved"] for x in d["drills"]), 0)

print("\n=== QO'LLANMA ===")
g = c.get("/api/student/cefr/writing/guide/request", headers=H).json()
ck("qadamlar bor", len(g["steps"]) >= 5, True)
ck("izohlangan namuna", len(g["model"]["paras"]) >= 5, True)
ck("har abzatsda izoh",
   all(len(p[2]) > 20 for p in g["model"]["paras"]), True)
ck("yo'q turga 404",
   c.get("/api/student/cefr/writing/guide/yoq", headers=H).status_code,
   404)

print("\n=== MASHQ: variant tanlash ===")
r = c.get("/api/student/cefr/writing/drill?kind=w_close&count=5",
          headers=H).json()
ck("5 ta mashq keldi", len(r["items"]), 5)
q = r["items"][0]
ck("variantlar bor", len(q["options"]) >= 3, True)
src = next(x for x in D.items("w_close") if x["idx"] == q["idx"])
a = c.post("/api/student/cefr/writing/drill/answer", headers=H,
           json={"kind": "w_close", "idx": q["idx"],
                 "answer": src["answer"]}).json()
ck("to'g'ri javob qabul qilindi", a["correct"], True)
ck("XP berildi", a["xp"] > 0, True)
ck("izoh keldi", bool(a["explain"]), True)
a2 = c.post("/api/student/cefr/writing/drill/answer", headers=H,
            json={"kind": "w_close", "idx": q["idx"],
                  "answer": src["answer"]}).json()
ck("ikkinchi marta XP YO'Q", a2["xp"], 0.0)
wrong = (src["answer"] + 1) % len(src["options"])
a3 = c.post("/api/student/cefr/writing/drill/answer", headers=H,
            json={"kind": "w_close", "idx": q["idx"], "answer": wrong}).json()
ck("xato javob xato deb belgilandi", a3["correct"], False)
ck("to'g'ri javob ko'rsatildi",
   a3["expected"], src["options"][src["answer"]])

print("\n=== MASHQ: yozib kiritish ===")
r = c.get("/api/student/cefr/writing/drill?kind=w_phrase&count=3",
          headers=H).json()
q = r["items"][0]
src = next(x for x in D.items("w_phrase") if x["idx"] == q["idx"])
ck("javob savolda ko'rinmaydi",
   src["answer"].lower() in q["prompt"].lower(), False)
a = c.post("/api/student/cefr/writing/drill/answer", headers=H,
           json={"kind": "w_phrase", "idx": q["idx"],
                 "answer": src["answer"].upper()}).json()
ck("katta harf ham qabul qilinadi", a["correct"], True)

print("\n=== MASHQ: abzats tartibi ===")
r = c.get("/api/student/cefr/writing/drill?kind=w_order&count=2",
          headers=H).json()
q = r["items"][0]
src = next(x for x in D.items("w_order") if x["idx"] == q["idx"])
ck("bo'laklar keldi", len(q["pieces"]) >= 5, True)
a = c.post("/api/student/cefr/writing/drill/answer", headers=H,
           json={"kind": "w_order", "idx": q["idx"],
                 "answer": src["answer"]}).json()
ck("to'g'ri tartib qabul qilindi", a["correct"], True)
a = c.post("/api/student/cefr/writing/drill/answer", headers=H,
           json={"kind": "w_order", "idx": q["idx"],
                 "answer": list(reversed(src["answer"]))}).json()
ck("teskari tartib rad etildi", a["correct"], False)

print("\n=== ISHLANMAGANLAR BIRINCHI ===")
# Yuqorida w_close ning 0-mashqi TO'G'RI yechilgan edi.
# Endi u ro'yxat OXIRIGA surilishi kerak — o'quvchi ishlamagan
# mashqlarni birinchi ko'rsin.
r = c.get("/api/student/cefr/writing/drill?kind=w_close&count=15",
          headers=H).json()
yechilgan = 0
tartib = [x["idx"] for x in r["items"]]
ck("yechilgan mashq oxiriga surildi", tartib[-1], yechilgan)
ck("boshida ishlanmagani turibdi", tartib[0] != yechilgan, True)
ck("hisob yangilandi", r["solved"] >= 1, True)

print("\n=== VAZIFA: namuna sizib chiqmaydi ===")
t = c.get("/api/student/cefr/writing/task/p1_cinema", headers=H).json()
raw = str(t)
ck("kontekst bor", bool(t["context"]), True)
ck("ikki topshiriq", bool(t["t11"] and t["t12"]), True)
ck("NAMUNA JAVOB YO'Q", "Yours faithfully" in raw, False)
ck("bandlar ko'rinadi", len(t["t12"]["bullets"]), 3)

print("\n=== TOPSHIRISH ===")
model = next(x for x in T.PART1 if x["id"] == "p1_cinema")["model12"]
r = c.post("/api/student/cefr/writing/submit", headers=H,
           json={"task_id": "p1_cinema", "part": "1.2",
                 "text": model}).json()
ck("namunaviy javob 100 ball", r["score"], 100)
ck("endi namuna ochildi", bool(r["model"]), True)
ck("tekshiruvlar ro'yxati", len(r["checks"]) >= 5, True)
ck("XP berildi", r["xp"] > 0, True)

yomon = ("hey, they're changing the time and it's mad. i don't like "
         "it. bye")
r = c.post("/api/student/cefr/writing/submit", headers=H,
           json={"task_id": "p1_cinema", "part": "1.2",
                 "text": yomon}).json()
ck("yomon matn past ball", r["score"] < 55, True)
xato = {x["label"] for x in r["checks"] if x["ok"] is False}
ck("so'z soni tutildi", "So'z soni" in xato, True)
ck("ochilish tutildi", "Ochilish" in xato, True)
ck("uslub tutildi", "Uslub" in xato, True)

print("\n=== AI ISHLAMASA HAM ===")
ck("AI kalitsiz ham baho keldi", r["score"] >= 0, True)
ck("javob to'liq", set(["score", "checks", "model", "ai"]) <= set(r), True)

print("\n=== PART 2 ===")
p2 = next(x for x in T.PART2 if x.get("model"))
r = c.post("/api/student/cefr/writing/submit", headers=H,
           json={"task_id": p2["id"], "part": "2",
                 "text": p2["model"]}).json()
ck("Part 2 namunasi 100 ball", r["score"], 100)

print("\n=== YOZUVLAR SAQLANDI ===")
n = (db.query(models.SkillAttempt)
     .filter(models.SkillAttempt.skill == "writing",
             models.SkillAttempt.ref.like("cwrite:%")).count())
ck("topshirilgan yozuvlar bazada", n >= 3, True)
d = c.get("/api/student/cefr/writing/home", headers=H).json()
ck("bosh ekranda hisob o'sdi", d["tasks"]["written"] >= 2, True)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
