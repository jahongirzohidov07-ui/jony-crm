"""MATEMATIKA TEST BAZASI (2026-09-26, Jahongir: "endi matematikanini
ozing tuzib qoy baza qildib bo'l tez").

Tekshiriladi:
  A. math_bank: 3 daraja × 14 test × 5 variant = 210 shablon, unit 30 /
     mid-end 45 savol, har savol 4 xil variant, javob indeksi to'g'ri,
     deterministik (qayta qurilganda bir xil), variantlar bir-biridan
     farq qiladi, mavzular "Matematika · …";
  B. Javob kaliti TO'G'RILIGI: generatorlar mustaqil hisob bilan
     tekshiriladi (qo'shish/ayirish, ko'paytirish, chiziqli tenglama,
     foiz, Pifagor, kvadrat tenglama ildizlari, arifmetik progressiya);
  C. Seed: bazaga 210 ta subject="math" shablon; ikkinchi seed hech
     narsa qo'shmaydi; ingliz tili shablonlariga tegmaydi;
  D. Fan bo'yicha ajratish: matematika guruhi linkida faqat matematika
     shablonlari (ingliz tili guruhida matematika chiqmaydi); mid/end
     uchun qog'oz qismi YO'Q (100 ballik qoida faqat ingliz tilida);
     aralash rejim ishlaydi, o'quvchi 30 savol oladi, baholanadi;
  E. Test bazasi: shablon yaratishda "subject" saqlanadi, noto'g'ri 400.
"""
import os
import sys
import re
import json
import random
import tempfile
from datetime import timedelta
from fractions import Fraction

_DB = os.path.join(tempfile.gettempdir(), "exam_math_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
import exam_online                                  # noqa: E402
import math_bank as mb                              # noqa: E402
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


print("=== A. GENERATOR TUZILISHI ===")
bad, n, tpls = [], 0, 0
for level, kind, u in mb.all_keys():
    for v in mb.VARIANTS:
        t = mb.build(level, kind, u, v)
        tpls += 1
        want = (5, 6) if kind == "unit" else (9, 5)
        if len(t["parts"]) != want[0]:
            bad.append(f"{level} {kind} {u} {v}: bo'lim")
        for p in t["parts"]:
            if len(p["questions"]) != want[1]:
                bad.append(f"{level} {kind} {u} {v}: savol soni")
            for q in p["questions"]:
                n += 1
                o = q["options"]
                if len(o) != 4 or len(set(o)) != 4 or not (0 <= q["answer"] < 4):
                    bad.append(f"{level} {kind} {u} {v}: {q['q'][:40]} {o}")
                if not q["topic"].startswith("Matematika · "):
                    bad.append(f"{level} {kind} {u} {v}: mavzu {q['topic']}")
        if mb.build(level, kind, u, v) != t:
            bad.append(f"{level} {kind} {u} {v}: deterministik emas")
ck("210 shablon, 6 750 savol", (tpls, n), (210, 6750))
ck("tuzilish xatosi yo'q", bad[:5], [])
a, b = mb.build("basic", "unit", 1, "A"), mb.build("basic", "unit", 1, "B")
qa = [q["q"] for p in a["parts"] for q in p["questions"]]
qb = [q["q"] for p in b["parts"] for q in p["questions"]]
ck("A va B variant savollari farq qiladi", len(set(qa) & set(qb)) < 5, True)
ck("sarlavha", (a["title"].startswith("Matematika Boshlang'ich · Unit 1"), b["title"].endswith("— B varianti")),
   (True, True))

print("\n=== B. JAVOB KALITI TO'G'RILIGI (mustaqil hisob) ===")
rng = random.Random(1)


def norm(s):
    """Matematik matnni Python ifodasiga: − → -, × → *, x² → x**2, 3x → 3*x."""
    s = s.replace("−", "-").replace("×", "*").replace("x²", "x**2").replace(" ", "")
    s = re.sub(r"(\d+)x", r"\1*x", s)          # 3x -> 3*x
    s = re.sub(r"(?<![\d*\w])x", "1*x", s)     # +x / -x / boshida x -> 1*x
    return s


def ev(s, x=0):
    return eval(norm(s), {"__builtins__": {}}, {"x": x})


ok_all = True
for _ in range(60):
    q = mb.g_add_sub(rng)
    expr = q["q"].replace("Hisoblang: ", "")
    ok_all &= int(q["options"][q["answer"]]) == ev(expr)
ck("qo'shish/ayirish 60 ta to'g'ri", ok_all, True)
ok_all = True
for _ in range(60):
    q = mb.g_mul_div(rng)
    expr = q["q"].replace("Hisoblang: ", "").replace(":", "//")
    ok_all &= int(q["options"][q["answer"]]) == ev(expr)
ck("ko'paytirish/bo'lish 60 ta to'g'ri", ok_all, True)
ok_all = True
for _ in range(60):
    q = mb.g_linear_eq(rng)
    x = int(q["options"][q["answer"]])
    lhs, rhs = q["q"].replace("Tenglamani yeching: ", "").split(" = ")
    ok_all &= ev(lhs, x) == ev(rhs, x)
ck("chiziqli tenglama 60 ta to'g'ri", ok_all, True)
ok_all = True
for _ in range(60):
    q = mb.g_percent(rng)
    ans = int(q["options"][q["answer"]])
    m = re.match(r"(\d+) ning (\d+)% ini toping", q["q"])
    if m:
        ok_all &= ans == int(m.group(1)) * int(m.group(2)) // 100
    m = re.match(r"(\d+) soni (\d+) ning necha foizi", q["q"])
    if m:
        ok_all &= int(m.group(1)) * 100 == ans * int(m.group(2))
ck("foizlar 60 ta to'g'ri", ok_all, True)
ok_all = True
for _ in range(40):
    q = mb.g_pythagoras(rng)
    ans = int(q["options"][q["answer"]])
    m = re.match(r".*katetlari (\d+) va (\d+)\.", q["q"])
    if m:
        ok_all &= ans * ans == int(m.group(1)) ** 2 + int(m.group(2)) ** 2
ck("Pifagor 40 ta to'g'ri", ok_all, True)
ok_all = True
for _ in range(60):
    q = mb.g_quadratic(rng)
    if not q["q"].startswith("Tenglamaning ildizlari"):
        continue
    eq = q["q"].replace("Tenglamaning ildizlari: ", "").replace(" = 0", "")
    r1, r2 = [int(v) for v in q["options"][q["answer"]].split("; ")]
    ok_all &= ev(eq, r1) == 0 and ev(eq, r2) == 0 and r1 != r2
ck("kvadrat tenglama ildizlari to'g'ri", ok_all, True)
ok_all = True
for _ in range(40):
    q = mb.g_arith_prog(rng)
    m = re.match(r"Arifmetik progressiyada a1 = (-?\d+), d = (-?\d+)\. Dastlabki (\d+) ta", q["q"])
    if m:
        a1, d, k = int(m.group(1)), int(m.group(2)), int(m.group(3))
        ok_all &= int(q["options"][q["answer"]]) == sum(a1 + i * d for i in range(k))
ck("arifmetik progressiya yig'indisi to'g'ri", ok_all, True)

print("\n=== C. SEED ===")
db = SessionLocal()
rounds, prev = 0, -1
while rounds < 10:                       # 8 soniyalik byudjet: keyingi startda davom etadi
    exam_online.seed_templates(db)
    rounds += 1
    cnt = db.query(models.ExamTemplate).filter_by(subject="math").count()
    if cnt == prev:
        break
    prev = cnt
print(f"    seed {rounds} startda tugadi")
mt = db.query(models.ExamTemplate).filter_by(subject="math").all()
ck("210 ta matematika shabloni", len(mt), 210)
ck("ingliz tili shablonlari joyida (subject NULL)",
   db.query(models.ExamTemplate).filter(models.ExamTemplate.subject.is_(None)).count() >= 42, True)
by = {(t.level, t.kind, t.unit_no, t.variant) for t in mt}
ck("basic unit 1 A..E, advanced end A..E bor",
   all((("basic", "unit", 1, v) in by) and (("advanced", "end", None, v) in by) for v in "ABCDE"), True)
t0 = db.query(models.ExamTemplate).filter_by(subject="math", level="basic", kind="unit", unit_no=1, variant="A").first()
ck("30 savol, mavzular, qog'oz 0",
   (sum(1 for _ in exam_online._questions(exam_online._load(t0.parts))),
    all(q.get("topic", "").startswith("Matematika") for q in exam_online._questions(exam_online._load(t0.parts))),
    t0.paper_max), (30, True, 0))
n_before = db.query(models.ExamTemplate).count()
exam_online.seed_templates(db)
ck("ikkinchi seed qo'shmaydi", db.query(models.ExamTemplate).count(), n_before)

print("\n=== D. FAN BO'YICHA LINK ===")
b = models.Branch(name="Zafar"); db.add(b); db.commit()
for un, role in [("asos", "founder"), ("exam", "examiner")]:
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.title(), role=role, branch_id=b.id))
tch = models.Teacher(full_name="Ustoz", branch_id=b.id); db.add(tch); db.commit()
gm = models.Group(name="Math-1", branch_id=b.id, teacher_id=tch.id, subject="math", level="basic")
ge = models.Group(name="Apex", branch_id=b.id, teacher_id=tch.id, subject="english", level="step1")
db.add_all([gm, ge]); db.commit()
s = models.Student(full_name="Aliyev Ali", branch_id=b.id, group_id=gm.id, status="active",
                   enrolled_date=roles.local_today() - timedelta(days=30))
db.add(s); db.commit()
exm = models.Exam(group_id=gm.id, kind="unit", unit_no=3, date=roles.local_today(), max_score=30, status="approved")
exe = models.Exam(group_id=ge.id, kind="unit", unit_no=3, date=roles.local_today(), max_score=30, status="approved")
exmid = models.Exam(group_id=gm.id, kind="mid", unit_no=None, date=roles.local_today(), max_score=45, status="approved")
db.add_all([exm, exe, exmid]); db.commit()
EM, EE, EMID, GM, SID = exm.id, exe.id, exmid.id, gm.id, s.id
db.close()
H, HE = tok("asos"), tok("exam")
r = client.get(f"/api/exams/{EM}/online", headers=HE).json()
ck("matematika guruhi: faqat matematika shablonlari (3 daraja × 5 variant), o'z darajasi birinchi",
   ({t["subject"] for t in r["templates"]}, len(r["templates"]),
    [t["level"] for t in r["templates"][:5]]), ({"math"}, 15, ["basic"] * 5))
r2 = client.get(f"/api/exams/{EE}/online", headers=HE).json()
ck("ingliz guruhi: matematika chiqmaydi", "math" in {t["subject"] for t in r2["templates"]}, False)
ck("exam-bank-max: matematika unit 30",
   client.get(f"/api/groups/{GM}/exam-bank-max?kind=unit&unit_no=3", headers=H).json()["max_score"], 30)
ck("exam-bank-max: matematika mid 45 (100 emas)",
   client.get(f"/api/groups/{GM}/exam-bank-max?kind=mid", headers=H).json()["max_score"], 45)
base = [t for t in r["templates"] if t["variant"] == "A"][0]
r = client.post(f"/api/exams/{EM}/online", headers=HE, json={"template_id": base["id"]})
ck("aralash link 200, 30 savol, qog'oz 0",
   (r.status_code, r.json()["online"]["online_max"], r.json()["online"]["paper_max"]), (200, 30.0, 0.0))
ck("variantlar aralash", len(r.json()["online"]["variants"].split(",")), 5)
TOKEN = r.json()["online"]["token"]
client.post(f"/api/exams/{EM}/online/start", headers=HE, json={"minutes": 30, "countdown": 0})
pub = client.get(f"/api/public/exam/{TOKEN}").json()
ck("o'quvchi: 5 bo'lim, 30 savol, 4 variantli, javob yo'q",
   (len(pub["parts"]), sum(len(p["questions"]) for p in pub["parts"]),
    all(len(q["options"]) == 4 for p in pub["parts"] for q in p["questions"]),
    any("answer" in q for p in pub["parts"] for q in p["questions"])), (5, 30, True, False))
d = SessionLocal()
o = d.query(models.ExamOnline).filter_by(exam_id=EM).first()
answers = {q["id"]: q["answer"] for q in exam_online._questions(exam_online._load(o.parts))}
d.close()
PHOTO = "data:image/jpeg;base64," + "A" * 200
r = client.post(f"/api/public/exam/{TOKEN}/submit", json={"photo": PHOTO, "student_id": SID, "answers": answers})
subs = client.get(f"/api/exams/{EM}/online", headers=HE).json()["submissions"]
ck("30/30 baholandi, mavzu javob varag'ida", (subs[0]["online_score"], subs[0]["detail"][0]["topic"].startswith("Matematika")),
   (30.0, True))
rm = client.get(f"/api/exams/{EMID}/online", headers=HE).json()
midA = [t for t in rm["templates"] if t["variant"] == "A"][0]
r = client.post(f"/api/exams/{EMID}/online", headers=HE, json={"template_id": midA["id"]})
ck("mid-course: 45 online + qog'oz 0 (matematika)",
   (r.json()["online"]["online_max"], r.json()["online"]["paper_max"]), (45.0, 0.0))

print("\n=== E. TEST BAZASI: FAN MAYDONI ===")
body = client.get(f"/api/exam-templates/{base['id']}", headers=HE).json()
ck("GET subject=math", body["subject"], "math")
r = client.post("/api/exam-templates", headers=H, json={
    "level": "basic", "kind": "unit", "unit_no": 12, "title": "Yangi", "paper_max": 0,
    "is_active": True, "variant": "F", "subject": "math", "parts": body["parts"]})
ck("yangi matematika shabloni", (r.status_code, r.json().get("subject")), (200, "math"))
r = client.post("/api/exam-templates", headers=H, json={
    "level": "basic", "kind": "unit", "unit_no": 12, "title": "Yangi", "paper_max": 0,
    "is_active": True, "subject": "fizika", "parts": body["parts"]})
ck("noma'lum fan 400", r.status_code, 400)
ck("ro'yxatda subject bor",
   {t["subject"] for t in client.get("/api/exam-templates", headers=HE).json()} >= {"english", "math"}, True)

print("\n" + ("HAMMASI OK" if not fails else "XATOLAR: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
