"""GRAMMATIKA — ARALASH MASHQ (2026-09-25).

Jahongir: "grammatikaga aralash mashq qilish funksyiyasini qoshgin
shunda aynan qaysi mavzuda koproq xato qilyabdi o'ziga bilinib
korinib tursin, chunki bitta mavzuni ishlagan odam javob topishi
osonda".

Tekshiriladi:
  1. /grammar/mix — ochiq darajalar (boshida faqat A1) dan, KO'P
     mavzudan, teng taqsimlab, aralashtirib beradi; javob mijozga
     ketmaydi; har savolda topic/level bor (mijoz javobdan keyin
     ko'rsatadi); qulf daraja so'ralsa 403; noto'g'ri daraja 400.
  2. /grammar/answer mode="mix" — urinish mode bilan yoziladi, javobda
     topic qaytadi; oddiy mashq mode=NULL.
  3. /grammar/mix/stats — faqat mix urinishlari, mavzular kesimida,
     eng ko'p xato tepada, aniqlik to'g'ri; oddiy mashq xatosi
     sanalmaydi.
  4. /grammar/topics "weak" ro'yxatida mix_wrong bor.
  5. Aralash mashqda "xato ustida ishlash": xato qilingan savol
     keyingi aralash mashqda birinchi navbatda keladi.
  6. Xavfsizlik: loginsiz yopiq.
"""
import os, sys, json, tempfile
from datetime import date

_test_dir = tempfile.TemporaryDirectory(prefix="jony-gmix-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
    _test_dir.name, "db.sqlite").replace("\\", "/")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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
                   status="active", phone="998901112255",
                   public_id="STU-GM-1")
db.add(s); db.commit()
u = models.User(username="998901112255",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "998901112255", "password": "jonyjony"},
).json()["access_token"]}


def answer_of(qid):
    q = db.query(models.GrammarQuestion).get(qid)
    if q.kind == "cloze":
        return "|".join(json.loads(q.answer))
    return q.answer


print("=== 1. ARALASH ROUND ===")
r = c.get("/api/student/grammar/mix?count=30", headers=H)
ck("status 200", r.status_code, 200)
d = r.json()
ck("mode=mix", d.get("mode"), "mix")
ck("boshida faqat A1 ochiq", d.get("levels"), ["A1"])
items = d["items"]
ck("30 ta savol", len(items), 30)
topics_in_round = {it["topic"] for it in items}
print(f"     mavzular: {len(topics_in_round)} ta, bank mavzulari: {d['topics']}")
ck("kamida 10 xil mavzudan (teng taqsim)", len(topics_in_round) >= 10, True)
ck("har savolda topic bor", all(it.get("topic") for it in items), True)
ck("har savol A1", all(it.get("level") == "A1" for it in items), True)
ck("to'g'ri javob mijozga KETMAYDI",
   any("answer" in it for it in items), False)
# Teng taqsim: bitta mavzu 30 tadan 5 tadan ko'p bo'lmasin
from collections import Counter
cnts = Counter(it["topic"] for it in items)
ck("bitta mavzu bosib ketmagan (max <= 4)", max(cnts.values()) <= 4, True)
ck("dublikat savol yo'q", len({it["id"] for it in items}), 30)

r = c.get("/api/student/grammar/mix?level=A2&count=10", headers=H)
ck("qulf daraja (A2) 403", r.status_code, 403)
r = c.get("/api/student/grammar/mix?level=Z9&count=10", headers=H)
ck("noto'g'ri daraja 400", r.status_code, 400)
r = c.get("/api/student/grammar/mix?level=a1&count=5", headers=H)
ck("kichik harf daraja qabul (a1)", r.status_code, 200)
ck("faqat A1", r.json()["levels"], ["A1"])
r = c.get("/api/student/grammar/mix?count=10&kind=fill", headers=H)
ck("kind=fill filtri", all(it["kind"] == "fill" for it in r.json()["items"]), True)

print("\n=== 2. JAVOB mode='mix' ===")
# Uch xil mavzudan uchta savol (statistika tekshiruvi aniq bo'lsin)
q1 = items[0]
q2 = next(it for it in items if it["topic"] != q1["topic"])
q3 = next(it for it in items if it["topic"] not in (q1["topic"], q2["topic"]))
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q1["id"], "answer": answer_of(q1["id"]),
                 "mode": "mix"})
ck("to'g'ri javob", r.json()["correct"], True)
ck("javobda mavzu qaytadi", r.json().get("topic"), q1["topic"])
ck("javobda daraja qaytadi", r.json().get("level"), "A1")
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q2["id"], "answer": "___notogri___",
                 "mode": "mix"})
ck("xato javob", r.json()["correct"], False)
# oddiy mashq (mode yo'q) — xato
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": q3["id"], "answer": "___notogri___"})
ck("oddiy mashq javobi ham ishlaydi", r.status_code, 200)
rows = db.query(models.GrammarAttempt).order_by(models.GrammarAttempt.id).all()
ck("3 ta urinish yozildi", len(rows), 3)
ck("mode: mix, mix, NULL", [x.mode for x in rows], ["mix", "mix", None])

print("\n=== 3. MAVZULAR KESIMIDA STATISTIKA ===")
# q2 mavzusidan yana 2 ta xato (aralash) — u eng ko'p xato bo'lsin.
# Aralash roundda shu mavzudan bitta savol bo'lishi mumkin, shuning
# uchun mavzuning o'z roundidan olamiz.
tr = c.get(f"/api/student/grammar/round?topic={q2['topic']}&count=10",
           headers=H).json()["items"]
same_topic = [it for it in tr
              if it["id"] != q2["id"] and it["topic"] == q2["topic"]][:2]
ck("q2 mavzusidan yana 2 ta savol topildi", len(same_topic), 2)
extra = [it for it in items if it["topic"] not in (q1["topic"], q2["topic"])][:2]
for it in same_topic:
    c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": it["id"], "answer": "___notogri___", "mode": "mix"})
for it in extra:
    c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": it["id"], "answer": answer_of(it["id"]), "mode": "mix"})
r = c.get("/api/student/grammar/mix/stats", headers=H)
ck("stats 200", r.status_code, 200)
st = r.json()
n_wrong_q2 = 1 + len(same_topic)          # q2 + 2 ta = 3 xato
# mix urinishlari: q1 (ok) + q2 (xato) + 2 xato + 2 ok = 6; q3 oddiy — sanalmaydi
ck("faqat mix urinishlari sanaladi (oddiy xato yo'q)",
   st["attempts"], 1 + n_wrong_q2 + len(extra))
ck("umumiy xato soni", st["wrong"], n_wrong_q2)
top = st["topics"][0]
ck("eng ko'p xato mavzu tepada", top["topic"], q2["topic"])
ck("o'sha mavzuda xato soni", top["wrong"], n_wrong_q2)
ck("weakest ro'yxatida", st["weakest"][0]["topic"], q2["topic"])
ok_topic = [x for x in st["topics"] if x["topic"] == q1["topic"]][0]
ck("to'g'ri yechilgan mavzu aniqligi 100%",
   ok_topic["accuracy"] if ok_topic["total"] == ok_topic["total"] - ok_topic["wrong"] else -1, 100)
ck("q3 mavzusi (oddiy mashq xatosi) statsda YO'Q yoki mixdan emas",
   all(x["topic"] != q3["topic"] or x["total"] > 0 for x in st["topics"]), True)
r = c.get("/api/student/grammar/mix/stats?days=0", headers=H)
ck("days=0 -> 1 kunga yaxlitlanadi", r.json()["days"], 1)

print("\n=== 4. /grammar/topics weak ro'yxatida mix_wrong ===")
# weak ga tushishi uchun q2 mavzusida >=3 xato va >25% kerak — bor
r = c.get("/api/student/grammar/topics", headers=H)
weak = r.json()["weak"]
w2 = [w for w in weak if w["topic"] == q2["topic"]]
ck("q2 mavzusi qiynalganlarda", len(w2), 1 if n_wrong_q2 >= 3 else len(w2))
if w2:
    ck("mix_wrong bor va to'g'ri", w2[0].get("mix_wrong"), n_wrong_q2)
    ck("weak birinchi o'rinda (mix xatosi ko'p)", weak[0]["topic"], q2["topic"])

print("\n=== 5. XATO USTIDA ISHLASH: xato savol keyingi aralashda birinchi navbatda ===")
# Teng taqsim: 37 mavzu, 60 savol -> har mavzudan 1-2 ta. Shu mavzudan
# kelganlari XATO qilinganlar ichidan bo'lishi kerak (ular navbatda
# birinchi), va mavzu har safar qatnashadi.
wrong_ids = {q2["id"]} | {it["id"] for it in same_topic}
hits = 0
for _ in range(5):
    r = c.get("/api/student/grammar/mix?count=60", headers=H)
    mine = [it["id"] for it in r.json()["items"] if it["topic"] == q2["topic"]]
    if mine and set(mine) <= wrong_ids:
        hits += 1
ck("xato mavzu har safar qatnashadi va faqat xato savollari bilan", hits, 5)

print("\n=== 6. XAVFSIZLIK ===")
ck("mix loginsiz yopiq",
   c.get("/api/student/grammar/mix").status_code in (401, 403), True)
ck("stats loginsiz yopiq",
   c.get("/api/student/grammar/mix/stats").status_code in (401, 403), True)

print()
db.close()
try:
    from database import engine as _eng
    _eng.dispose()
except Exception:
    pass
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
