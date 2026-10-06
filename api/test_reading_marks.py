"""READING MATNIDAGI _JAVOB JOYI_ BELGISI O'QUVCHIGA BORMAYDI (2026-10-05,
audit: 5.0 L11 "Air conditioning", "The ballpoint pen" — paraphrase / javob
joylari "_..._" bilan belgilangan; bu ustoz uchun yordam, o'quvchi
topshirig'ida esa javobni ko'rsatib qo'yardi):
  1) strip_marks: belgi olinadi, "___" bo'sh joy va "a_b" tegilmaydi;
  2) har kurs (1.0–7.0, tuzatilgan 5.0–7.0 ham) har reading qismi —
     build_from_plan matnida, savol/kontekstida belgi qolmaydi, so'zlar
     yo'qolmaydi;
  3) API: rejadan yuborilgan reading va tuzatishdan OLDIN bazaga xom matn
     bilan saqlangan topshiriq — o'quvchi ham, ustoz ham belgisiz oladi.
Ishga tushirish: python test_reading_marks.py"""
import glob
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "reading_marks_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
import assignments as A                            # noqa: E402
import liveplay as LP                              # noqa: E402

c = TestClient(main.app)
fails = []
# testning O'Z belgi qidiruvi: yakka "_" bilan o'ralgan ibora ("___" emas)
MARK = re.compile(r"(?<![\w])_(?!_)[^_\n]*?[^_\s]_(?![\w])")


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}" + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


# --- 1) sof funksiya
ck("belgi olinadi", A.strip_marks("people _have less_ time (_since 1990_)."), "people have less time (since 1990).")
ck("ro'yxat va None", (A.strip_marks(["_a_ b", None]), A.strip_marks(None)), (["a b", None], None))
ck("'___' bo'sh joy tegilmaydi", A.strip_marks("My mother ___ a kind nurse. (___)"), "My mother ___ a kind nurse. (___)")
ck("yakka chiziq (email, a_b) tegilmaydi", A.strip_marks("It's clarice_willard@... and x_y"), "It's clarice_willard@... and x_y")

# --- 2) har kurs, har reading qismi (repo JSON + tuzatilgan 5.0–7.0 bo'lsa)
FIX_DIR = os.environ.get("PLAN_FIX_DIR") or os.path.normpath(os.path.join(_HERE, "..", "..", "fix5", "out"))
lessons = []
for n in range(1, 8):
    course = f"ielts_{n}_0"
    lessons += [(course, L, "repo") for L in LP._load_course(course)["lessons"]]
    for p in sorted(glob.glob(os.path.join(FIX_DIR, course, "L*.json"))) if n >= 5 else []:
        with open(p, encoding="utf-8") as f:
            lessons.append((course, json.load(f), "fix"))


def strings(o):
    """O'quvchiga boradigan matnlar (javob, accept, explain — yashirin)."""
    if isinstance(o, str):
        yield o
    elif isinstance(o, list):
        for x in o:
            yield from strings(x)
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in ("answer", "accept", "explain"):
                yield from strings(v)


marked = parts = leaks = lost = 0
for course, L, src in lessons:
    for i, R in enumerate(A._readings(L)):
        b = A.build_from_plan(L, "reading" if i == 0 else f"reading:{i}", course)
        if not b:
            continue
        parts += 1
        raw = R.get("text") or []
        marked += any(MARK.search(t) for t in raw)
        for s in strings({"text": b.get("text"), "questions": b["questions"]}):
            if MARK.search(s):
                leaks += 1
                if leaks <= 10:
                    print("XATO belgi qoldi:", course, L["no"], src, R.get("title"), "|", MARK.search(s).group(0))
        # so'zlar yo'qolmasin: faqat belgi ostidagi "_" olinadi
        if [re.sub(r"_([^_]+)_", r"\1", t) for t in raw] != (b.get("text") or []):
            lost += 1
            if lost <= 5:
                print("XATO matn o'zgardi:", course, L["no"], src, R.get("title"))
ck("belgili reading matnlari bor (test bo'sh emas)", marked > 20, True)
ck("reading qismlarida belgi qolmadi", leaks, 0)
ck("matnda faqat belgi olindi", lost, 0)
print(f"   ({parts} reading qismi, {marked} tasida belgi bor edi)")

# --- 3) API: yuborish va o'quvchi ko'rinishi
db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); db.add(b1); db.commit()
u_t = models.User(username="ustoz", password_hash=hash_password("x"), full_name="Ustoz", role=roles.TEACHER, branch_id=b1.id)
u_s = models.User(username="aziz", password_hash=hash_password("x"), full_name="Aziz Karimov", role=roles.STUDENT, branch_id=b1.id)
db.add_all([u_t, u_s]); db.commit()
t1 = models.Teacher(full_name="Ustoz", user_id=u_t.id, branch_id=b1.id, subject="english"); db.add(t1); db.commit()
g1 = models.Group(name="IELTS 5.0", branch_id=b1.id, teacher_id=t1.id, lesson_price=50000,
                  standard_lessons_per_month=12, monthly_fee=600000)
db.add(g1); db.commit()
s1 = models.Student(full_name="Aziz Karimov", branch_id=b1.id, status="active", group_id=g1.id, user_id=u_s.id)
db.add(s1); db.commit()
db.add(models.GroupPlan(group_id=g1.id, course="ielts_5_0", next_lesson_no=11, carry="[]")); db.commit()
G1, S1 = g1.id, s1.id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post("/api/auth/login", json={"username": u, "password": "x"}).json()["access_token"]}


T, S = tok("ustoz"), tok("aziz")
L11 = LP._lesson("ielts_5_0", 11)
ck("5.0 L11 matnida belgi bor (Air conditioning, The ballpoint pen)",
   [any(MARK.search(t) for t in R["text"]) for R in A._readings(L11)[:2]], [True, True])
r = c.post(f"/api/groups/{G1}/assignments/from-plan",
           json={"course": "ielts_5_0", "lesson_no": 11, "parts": ["reading", "reading:1"], "due_days": 2}, headers=T)
CR = r.json()["created"]
ck("ikkala reading yuborildi", (r.status_code, len(CR)), (200, 2))
for a in CR:
    d = c.get(f"/api/student/assignments/{a['id']}", headers=S).json()
    txt = (d.get("text") or {}).get("text") or []
    ck(f"o'quvchi: {d['title']} — matn bor, belgisiz",
       (len(txt) > 0, sum(1 for t in txt if MARK.search(t)), sum(1 for s in strings(d["questions"]) if MARK.search(s))),
       (True, 0, 0))
db = SessionLocal()
ck("bazada ham belgisiz saqlandi",
   [bool(MARK.search(db.query(models.Assignment).get(a["id"]).text)) for a in CR], [False, False])
# tuzatishdan oldin yuborilgan: bazada xom matn
raw = A._readings(L11)[0]
old = models.Assignment(group_id=G1, course="ielts_5_0", lesson_no=11, kind="reading", skill="reading",
                        title="11-dars — Reading (eski)", instr=None,
                        text=json.dumps({"text": raw["text"], "glossary": raw.get("glossary")}, ensure_ascii=False),
                        questions=json.dumps([{"kind": "gap", "prompt": "x", "answer": "y"}]), auto=1,
                        max_score=1.0, due_at=datetime.utcnow() + timedelta(days=2), sent_at=datetime.utcnow(),
                        status="sent", created_by="Ustoz", targets=json.dumps([S1]))
db.add(old); db.commit()
OLD = old.id
db.close()
d = c.get(f"/api/student/assignments/{OLD}", headers=S).json()
ck("eski topshiriq: o'quvchiga belgisiz", sum(1 for t in d["text"]["text"] if MARK.search(t)), 0)
ck("eski topshiriq: so'zlar joyida", d["text"]["text"] == [re.sub(r"_([^_]+)_", r"\1", t) for t in raw["text"]], True)
lst = c.get("/api/student/assignments", headers=S).json()["items"]
ck("ro'yxatda ham belgisiz",
   sum(1 for i in lst for t in ((i.get("text") or {}).get("text") or []) if MARK.search(t)), 0)
d = c.get(f"/api/assignments/{OLD}", headers=T).json()
ck("ustoz topshiriq ko'rinishi ham belgisiz (o'quvchi ko'rgan matn)",
   (len(d["text"]["text"]), sum(1 for t in d["text"]["text"] if MARK.search(t))), (len(raw["text"]), 0))

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
