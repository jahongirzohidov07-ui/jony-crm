"""SAVOL MAVZULARI (#177, 2026-09-26).

@jonybazabaza test bazasi (Step 1/2/3: 36 unit + 6 mid/end = 1 585
savol) 42 shablonga to'liq mos — javob kalitlari bilan tekshirildi.
Har savolga mavzu belgilandi (exam_topics.json).

Tekshiriladi:
  A. exam_topics.json seed bilan bir xil tuzilishda: 42 shablon, har
     bo'limda savollar soni qancha bo'lsa shuncha mavzu, hammasi
     "Skill · Mavzu" ko'rinishida (Listening/Reading/Vocabulary/Grammar);
  B. Yangi bazada seed: har savolda mavzu bor;
  C. JONLI baza holati: shablon mavzusiz yaratilgan (seed belgisi
     turibdi) + examiner bitta savol matnini o'zgartirgan + ochiq link
     nusxasi ham mavzusiz → fill_topics_from_bank: mos savollarga
     mavzu qo'yiladi, tahrirlangani tegilmaydi, link nusxasi ham
     to'ladi; ikkinchi chaqiriq hech narsa qilmaydi (bir martalik);
  D. O'quvchiga boradigan nusxada mavzu YO'Q; examiner javob varag'ida
     BOR; tahrirda (PUT) mavzu saqlanadi, bo'sh mavzu yozilmaydi;
  E. /api/exam-templates/topics — ro'yxat + sanoq, ustozga yopiq.
"""
import os
import sys
import json
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "exam_topics_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
import exam_online                                  # noqa: E402
import exam_bank_seed                               # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    r = client.post("/api/auth/login", json={"username": u, "password": p})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


SKILLS = ("Listening", "Reading", "Vocabulary", "Grammar")

print("=== A. exam_topics.json TUZILISHI ===")
topics = json.load(open(os.path.join(HERE, "exam_topics.json"), encoding="utf-8"))
ck("42 shablon", len(topics), 42)
bad, total, names = [], 0, set()
for key, tpl in exam_bank_seed.TEMPLATES:
    tp = topics.get(key)
    if tp is None:
        bad.append(f"{key}: yo'q"); continue
    if len(tp) != len(tpl["parts"]):
        bad.append(f"{key}: bo'lim soni {len(tp)} != {len(tpl['parts'])}")
    for p, arr in zip(tpl["parts"], tp):
        if len(arr) != len(p["questions"]):
            bad.append(f"{key}: {p['title'][:20]} {len(arr)} != {len(p['questions'])}")
        for t in arr:
            total += 1
            names.add(t)
            if " · " not in t or t.split(" · ")[0] not in SKILLS:
                bad.append(f"{key}: yomon mavzu {t!r}")
ck("tuzilish xatosi yo'q", bad, [])
ck("jami 1 585 savol", total, 1585)
ck("4 ko'nikma ham bor",
   sorted({n.split(" · ")[0] for n in names}), sorted(SKILLS))
ck("mavzular soni 100+", len(names) >= 100, True)

print("\n=== B. YANGI BAZADA SEED ===")
db = SessionLocal()
exam_online.seed_templates(db)
n_all = n_topic = 0
for t in db.query(models.ExamTemplate).all():
    if (t.variant or "A") != "A":
        continue        # B-E variantlar alohida (test_exam_variants)
    for q in exam_online._questions(exam_online._load(t.parts)):
        n_all += 1
        n_topic += 1 if q.get("topic") else 0
ck("bazada 1 585 savol", n_all, 1585)
ck("hammasida mavzu bor", n_topic, 1585)
t1 = db.query(models.ExamTemplate).filter_by(level="step1", kind="unit",
                                             unit_no=1).first()
p1 = exam_online._load(t1.parts)
ck("Step 1 U1 1-savol: Listening · Short replies",
   p1[0]["questions"][0]["topic"], "Listening · Short replies")
ck("Step 1 U1 Part 2: Vocabulary · Countries and nationalities",
   p1[1]["questions"][0]["topic"], "Vocabulary · Countries and nationalities")
ck("Step 1 U1 Part 5 grammatika",
   p1[4]["questions"][0]["topic"].startswith("Grammar · "), True)

print("\n=== C. JONLI BAZA: MAVZUSIZ SHABLON + TAHRIR + OCHIQ LINK ===")
# Jonli bazadagi holatni yasaymiz: Step 2 Unit 3 mavzusiz (eski seed
# yozgandek), examiner 5-savol matnini o'zgartirgan; link ham ochilgan.
t23 = db.query(models.ExamTemplate).filter_by(level="step2", kind="unit",
                                              unit_no=3).first()
raw = exam_online._load(t23.parts)
for q in exam_online._questions(raw):
    q.pop("topic", None)
raw[0]["questions"][4]["q"] = "EXAMINER O'ZGARTIRGAN SAVOL"
t23.parts = json.dumps(raw, ensure_ascii=False)
# Ochiq link nusxasi (mavzusiz)
b = models.Branch(name="Zafar"); db.add(b); db.commit()
for un, role in [("asos", "founder"), ("exam", "examiner"), ("ustoz", "teacher")]:
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.title(), role=role, branch_id=b.id))
tch = models.Teacher(full_name="Ustoz", branch_id=b.id); db.add(tch); db.commit()
g = models.Group(name="Apex", branch_id=b.id, teacher_id=tch.id,
                 subject="english", level="step2")
db.add(g); db.commit()
s = models.Student(full_name="Aliyev Ali", branch_id=b.id, group_id=g.id,
                   status="active", enrolled_date=roles.local_today() - timedelta(days=30))
db.add(s); db.commit()
ex = models.Exam(group_id=g.id, kind="unit", unit_no=3, date=roles.local_today(),
                 max_score=40, status="approved")
db.add(ex); db.commit()
o = models.ExamOnline(exam_id=ex.id, template_id=t23.id, token="tokentopic01",
                      is_open=1, parts=json.dumps(raw, ensure_ascii=False),
                      online_max=40, paper_max=0)
db.add(o); db.commit()
# Alohida kalit bilan — go'yo bu deploy birinchi marta ishlayapti
filled = exam_online.fill_topics_from_bank(db, key="exam_topics_test_v1")
db.refresh(t23); db.refresh(o)
pt = exam_online._load(t23.parts)
po = exam_online._load(o.parts)
ck("shablon: 39 ta savolga mavzu qo'yildi, tahrirlangani yo'q",
   (sum(1 for q in exam_online._questions(pt) if q.get("topic")),
    pt[0]["questions"][4].get("topic")), (39, None))
ck("link nusxasi ham to'ldi", sum(1 for q in exam_online._questions(po) if q.get("topic")), 39)
ck("jami qo'yilgan = 78", filled, 78)
ck("ikkinchi marta ishlamaydi (bir martalik)",
   exam_online.fill_topics_from_bank(db, key="exam_topics_test_v1"), 0)
EID, TID, SID = ex.id, t23.id, s.id
db.close()

print("\n=== D. O'QUVCHIGA YO'Q, EXAMINERGA BOR, TAHRIRDA SAQLANADI ===")
H, HE, HT = tok("asos"), tok("exam"), tok("ustoz")
pub = client.get("/api/public/exam/tokentopic01").json()
ck("ochiq sahifa 'topic' yubormaydi",
   any("topic" in q for p in pub["parts"] for q in p["questions"]), False)
r = client.get(f"/api/exam-templates/{TID}", headers=HE)
ck("examiner shablonda mavzuni ko'radi",
   r.json()["parts"][1]["questions"][0].get("topic"), "Vocabulary · Daily life")
# PUT: mavzu saqlanadi, bo'sh mavzu yozilmaydi, yangi mavzu ham qabul qilinadi
body = r.json()
body["parts"][0]["questions"][0]["topic"] = "  "
body["parts"][0]["questions"][1]["topic"] = "Grammar · Yangi mavzu"
r2 = client.put(f"/api/exam-templates/{TID}", headers=H, json={
    "level": body["level"], "kind": body["kind"], "unit_no": body["unit_no"],
    "title": body["title"], "paper_max": body["paper_max"],
    "is_active": True, "parts": body["parts"]})
ck("PUT 200", r2.status_code, 200)
qs = r2.json()["parts"][0]["questions"]
ck("bo'sh mavzu yozilmaydi", "topic" in qs[0], False)
ck("yangi mavzu saqlandi", qs[1].get("topic"), "Grammar · Yangi mavzu")
ck("qolganlari o'z joyida", r2.json()["parts"][1]["questions"][0].get("topic"),
   "Vocabulary · Daily life")
# Examiner javob varag'ida mavzu: o'quvchi topshiradi
PHOTO = "data:image/jpeg;base64," + "A" * 200
client.post(f"/api/exams/{EID}/online/start", headers=HE, json={"minutes": 30, "countdown": 0})
r = client.post("/api/public/exam/tokentopic01/submit",
                json={"photo": PHOTO, "student_id": SID, "answers": {}})
ck("topshirdi", r.status_code, 200)
on = client.get(f"/api/exams/{EID}/online", headers=HE).json()
sheet = on["submissions"][0]["detail"]
ck("javob varag'ida mavzu bor", sheet[8]["topic"], "Vocabulary · Daily life")
ck("tahrirlangan savol mavzusiz (None)", sheet[4]["topic"], None)

print("\n=== E. MAVZULAR RO'YXATI ===")
r = client.get("/api/exam-templates/topics", headers=HE)
ck("200", r.status_code, 200)
rows = {x["topic"]: x["count"] for x in r.json()}
# 264 - 3 (Step 2 U3: tahrirlangan, bo'shatilgan, qayta nomlangan)
# + B–E variantlardagilar (exam_bank_variants.json) — bazadan hisoblanadi
d2 = SessionLocal()
exp_sr = sum(1 for t in d2.query(models.ExamTemplate).all()
             for q in exam_online._questions(exam_online._load(t.parts))
             if q.get("topic") == "Listening · Short replies")
d2.close()
ck("Listening · Short replies soni bazaga teng (>= 261)",
   (rows.get("Listening · Short replies"), exp_sr >= 261), (exp_sr, True))
ck("yangi mavzu ro'yxatda", rows.get("Grammar · Yangi mavzu"), 1)
ck("ustozga yopiq", client.get("/api/exam-templates/topics", headers=HT).status_code, 403)
ck("tartib: ko'nikma bo'yicha",
   [x["topic"].split(" · ")[0] for x in r.json()][:1], ["Grammar"])

print("\n" + ("HAMMASI OK" if not fails else "XATOLAR: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
