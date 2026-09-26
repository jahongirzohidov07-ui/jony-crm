"""MOCK TESTNI LINK ORQALI OLISH — UCHIDAN UCHIGA (2026-09-26).

Jahongir: "haqiqiy IELTS CDI testlari bilan 1x1 kopya bo'lishi kerak
... va katta mock test bazasini yarat".

Mock ilgari online oqimdan butunlay chetda edi (shablon ham, link ham
rad etilardi). Shu yerda butun yo'l tekshiriladi:

  A. IELTS guruhiga mock testi yaratiladi, bazadan maksimal ball = 9
     (band), Listening shabloniga link ochiladi;
  B. O'quvchiga savollar to'g'ri javobsiz boradi, listening SKRIPTI
     ham bormaydi (examiner o'qib beradi);
  C. 30/40 topshirgan o'quvchi — natija 7.0 BAND bo'lib guruh testiga
     tushadi (ball emas: exams._apply_exam_marks mock uchun band
     talab qiladi);
  D. CEFR Multilevel mockida rasmiy o'tkazish jadvali yo'q — avtomat
     band YOZILMAYDI, xom ball examinerda qoladi;
  E. Writing mockida avtomat tekshiriladigan savol yo'q: natija
     examiner qog'oz balini (bandni) kiritgandagina yoziladi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "mock_online_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402,F401
import entry                                       # noqa: F401,E402
import exam_online                                 # noqa: E402
import mock_seed                                   # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []
TODAY = roles.local_today()
PHOTO = "data:image/jpeg;base64," + "A" * 200


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


db = SessionLocal()
mock_seed.seed_mocks(db)
b = models.Branch(name="Markaz")
db.add(b)
db.commit()
BID = b.id
for un, role in [("asos", "founder"), ("bosh", "head_examiner")]:
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.title(), role=role, branch_id=BID))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID)
db.add(t)
db.commit()
GRP = {}
for name, level in [("IELTS-A", "ielts_graduation"), ("CEFR-A", "cefr")]:
    g = models.Group(name=name, branch_id=BID, teacher_id=t.id,
                     subject="english", level=level)
    db.add(g)
    db.commit()
    GRP[level] = g.id
STU = {}
for level, gid in GRP.items():
    s = models.Student(full_name=f"Talaba {level}", branch_id=BID,
                       group_id=gid, status="active",
                       enrolled_date=TODAY - timedelta(days=60))
    db.add(s)
    db.commit()
    STU[level] = s.id
db.commit()
H = tok("asos")
HE = tok("bosh")


def tpl_rows(level, like):
    return [t for t in client.get("/api/exam-templates", headers=HE).json()
            if t["kind"] == "mock" and t["level"] == level
            and like in t["title"]]


def make_exam(gid):
    r = client.post(f"/api/groups/{gid}/exams", headers=H, json={
        "kind": "mock", "date": TODAY.isoformat(), "max_score": None})
    assert r.status_code == 200, r.text
    eid = r.json()["id"]
    client.put(f"/api/exams/{eid}", headers=H, json={"status": "approved"})
    return eid


def open_link(eid, tpl_id, paper=0, mode="single"):
    r = client.post(f"/api/exams/{eid}/online", headers=HE, json={
        "template_id": tpl_id, "paper_max": paper, "mode": mode})
    assert r.status_code == 200, r.text
    r2 = client.post(f"/api/exams/{eid}/online/start", headers=HE,
                     json={"minutes": 60, "countdown": 0})
    assert r2.status_code == 200, r2.text
    return client.get(f"/api/exams/{eid}/online", headers=HE).json()


def band(eid, student_id):
    d = client.get(f"/api/exams/{eid}", headers=H).json()
    row = {x["student_id"]: x for x in d["results"]}.get(student_id)
    return None if not row else (row.get("band"), row.get("score"))


def link_parts(eid):
    return exam_online._load(
        db.query(models.ExamOnline).filter_by(exam_id=eid).first().parts)


# ------------------------------------------------------------------ A
print("=== A. IELTS MOCK LINKI OCHILADI ===")
ck("bazadan mock maksimal bali = band (9)",
   client.get(f"/api/groups/{GRP['ielts_graduation']}/exam-bank-max?kind=mock",
              headers=HE).json()["max_score"], 9.0)
lst = tpl_rows("ielts_graduation", "Listening")
ck("Listening shablonlari 5 variant", len(lst), 5)
EID = make_exam(GRP["ielts_graduation"])
data = open_link(EID, sorted(lst, key=lambda x: x["id"])[0]["id"])
TOKEN = data["online"]["token"]
ck("online maksimal = 40 savol", data["online"]["online_max"], 40)

# ------------------------------------------------------------------ B
print("\n=== B. O'QUVCHIGA KETADIGAN NUSXA ===")
pub = client.get(f"/api/public/exam/{TOKEN}").json()
QS = [q for p in pub["parts"] for q in p["questions"]]
ck("40 savol", len(QS), 40)
ck("to'g'ri javob yo'q", any("answer" in q for q in QS), False)
ck("listening skripti o'quvchiga ketmaydi",
   any("script" in p for p in pub["parts"]), False)
ck("4 bo'lim", len(pub["parts"]), 4)

# ------------------------------------------------------------------ C
print("\n=== C. 30/40 -> BAND 7.0 ===")
KEY = [q for p in link_parts(EID) for q in p["questions"]]


def answers(n_right):
    out = {}
    for i, q in enumerate(KEY):
        right = i < n_right
        if q["type"] == "choice":
            out[q["id"]] = q["answer"] if right \
                else (q["answer"] + 1) % len(q["options"])
        elif q["type"] == "multi":
            out[q["id"]] = q["answer"] if right else [q["answer"][0]]
        else:
            out[q["id"]] = q["answer"][0] if right else "zzz"
    return out


sid = STU["ielts_graduation"]
r = client.post(f"/api/public/exam/{TOKEN}/submit", json={
    "photo": PHOTO, "student_id": sid, "answers": answers(30)})
ck("topshirildi", r.status_code, 200)
sub = [s for s in client.get(f"/api/exams/{EID}/online", headers=HE)
       .json()["submissions"] if s["student_id"] == sid]
ck("xom ball 30/40",
   (sub[0]["online_score"], sub[0]["online_max"]), (30.0, 40.0))
ck("tasdiqlanmaguncha natija yo'q", band(EID, sid), None)
ck("tasdiqlandi",
   client.post(f"/api/exams/{EID}/online/publish", headers=HE).status_code, 200)
ck("natija BAND 7.0, ball yo'q", band(EID, sid), (7.0, None))

# ------------------------------------------------------------------ D
print("\n=== D. CEFR MULTILEVEL — AVTOMAT BAND YOZILMAYDI ===")
ctpl = tpl_rows("cefr", "Listening")
ck("CEFR Listening 3 variant", len(ctpl), 3)
CEID = make_exam(GRP["cefr"])
cdata = open_link(CEID, sorted(ctpl, key=lambda x: x["id"])[0]["id"])
ck("CEFR online maksimal = 35 savol", cdata["online"]["online_max"], 35)
csid = STU["cefr"]
cans = {}
for q in [q for p in link_parts(CEID) for q in p["questions"]]:
    cans[q["id"]] = q["answer"] if q["type"] in ("choice", "multi") \
        else q["answer"][0]
r = client.post(f"/api/public/exam/{cdata['online']['token']}/submit", json={
    "photo": PHOTO, "student_id": csid, "answers": cans})
ck("topshirildi", r.status_code, 200)
csub = [s for s in client.get(f"/api/exams/{CEID}/online", headers=HE)
        .json()["submissions"] if s["student_id"] == csid]
ck("xom ball 35/35",
   (csub[0]["online_score"], csub[0]["online_max"]), (35.0, 35.0))
client.post(f"/api/exams/{CEID}/online/publish", headers=HE)
ck("taxminiy band yozilmadi — examiner o'zi qo'yadi",
   band(CEID, csid), None)

# ------------------------------------------------------------------ E
print("\n=== E. WRITING MOCKI — QOG'OZ BALI ===")
wtpl = tpl_rows("ielts_graduation", "Writing")
ck("Writing 5 variant, 2 vazifa", (len(wtpl), wtpl[0]["q_count"]), (5, 2))
WEID = make_exam(GRP["ielts_graduation"])
wdata = open_link(WEID, sorted(wtpl, key=lambda x: x["id"])[0]["id"], paper=9)
WKEY = [q for p in link_parts(WEID) for q in p["questions"]]
ck("ikkala vazifa ham essay", sorted({q["type"] for q in WKEY}), ["essay"])
ck("so'z chegarasi 150 va 250",
   sorted(q["min_words"] for q in WKEY), [150, 250])
r = client.post(f"/api/public/exam/{wdata['online']['token']}/submit", json={
    "photo": PHOTO, "student_id": sid,
    "answers": {q["id"]: "Bu mening javobim. " * 30 for q in WKEY}})
ck("topshirildi", r.status_code, 200)
wsub = [s for s in client.get(f"/api/exams/{WEID}/online", headers=HE)
        .json()["submissions"] if s["student_id"] == sid]
ck("avtomat ball 0/0 (essay hisobga kirmaydi)",
   (wsub[0]["online_score"], wsub[0]["online_max"]), (0.0, 0.0))
ck("examiner insho matnini ko'radi",
   len(wsub[0]["detail"][0]["given_text"] or "") > 100, True)
client.post(f"/api/exams/{WEID}/online/publish", headers=HE)
ck("qog'oz bali kiritilmagan — natija yo'q", band(WEID, sid), None)
r = client.put(f"/api/exams/{WEID}/paper", headers=HE, json={
    "marks": [{"student_id": sid, "paper": 6.5}]})
ck("qog'oz bali kiritildi", r.status_code, 200)
ck("natija = examiner qo'ygan band", band(WEID, sid), (6.5, None))

db.close()
print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
sys.exit(1 if fails else 0)
