"""ONLINE TEST — LINK ORQALI (2026-09-18).

Tekshiriladi:
  A. Boshlang'ich baza: Step 1 Unit 1 (30 savol) bor;
  B. Link yaratiladi, testning maksimal bali savollar soniga teng;
  C. Ochiq sahifada ro'yxat bor, to'g'ri javoblar YO'Q;
  D. Ro'yxatdan tanlagan — natija o'z qatoriga tushadi (foiz, coin);
  E. Matnli javob: "the usa", "hina" — qabul qilinadi;
  F. Qayta topshirsa — duplicate, natija o'zgarmaydi;
  G. Ro'yxatda yo'q / ism xato — pending, examiner biriktiradi;
  H. Yozilgan ism aynan mos kelsa — o'zi joylashadi;
  I. Rasm yo'q — 400, yopiq link — 410, ustoz link ocholmaydi;
  J. Qog'oz qismi (Writing/Speaking): kiritilguncha natija yo'q,
     kiritilgach jami = online + qog'oz;
  K. Test bazasi: boshliq yaratadi, examiner yarata olmaydi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "exam_online_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
import exam_online                                  # noqa: E402
from database import SessionLocal, engine           # noqa: E402
from sqlalchemy import event                        # noqa: E402


# Saytdagi Postgres kabi bog'lanishlar (FK) tekshirilsin — aks holda
# imtihonni o'chirishdagi 500 xato testda ko'rinmas edi (2026-09-18)
@event.listens_for(engine, "connect")
def _fk_on(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA foreign_keys=ON")
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
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


TODAY = roles.local_today()
PHOTO = "data:image/jpeg;base64," + "A" * 200

db = SessionLocal()
exam_online.seed_templates(db)
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
for un, role in [("asos", "founder"), ("bosh", "head_examiner"),
                 ("exam", "examiner"), ("ustoz", "teacher")]:
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.title(), role=role, branch_id=BID))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID)
db.add(t)
db.commit()
g = models.Group(name="Apex", branch_id=BID, teacher_id=t.id,
                 subject="english", level="step1")
db.add(g)
db.commit()
GID = g.id
S = {}
for nm in ["Aliyev Ali", "Boboyev Bobur", "Valiyev Vali", "Karimova Kamola"]:
    s = models.Student(full_name=nm, branch_id=BID, group_id=GID,
                       status="active",
                       enrolled_date=TODAY - timedelta(days=60))
    db.add(s)
    db.commit()
    S[nm] = s.id
les = models.Lesson(group_id=GID, date=TODAY - timedelta(days=10))
db.add(les)
db.commit()
for sid in S.values():
    db.add(models.Attendance(lesson_id=les.id, student_id=sid, present=1))
db.query(models.ExamCoinRule).delete()
db.add(models.ExamCoinRule(min_percent=90, coins=10))
db.add(models.ExamCoinRule(min_percent=50, coins=5))
db.commit()
db.close()

H = tok("asos")
HB = tok("bosh")
HE = tok("exam")
HT = tok("ustoz")

print("=== A. BOSHLANG'ICH BAZA ===")
r = client.get("/api/exam-templates", headers=HE)
ck("javob 200", r.status_code, 200)
tpl = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 1]
ck("Step 1 Unit 1 bor", len(tpl), 1)
TID = tpl[0]["id"]
ck("30 ta savol", tpl[0]["q_count"], 30)
u2 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 2]
ck("Step 1 Unit 2 bor, 30 savol", [x["q_count"] for x in u2], [30])
u3 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 3]
ck("Step 1 Unit 3 bor, 30 savol", [x["q_count"] for x in u3], [30])
u4 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 4]
ck("Step 1 Unit 4 bor, 30 savol", [x["q_count"] for x in u4], [30])
u5 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 5]
ck("Step 1 Unit 5 bor, 30 savol", [x["q_count"] for x in u5], [30])
u6 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 6]
ck("Step 1 Unit 6 bor, 30 savol", [x["q_count"] for x in u6], [30])
mid = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["kind"] == "mid"]
ck("Step 1 Mid-course bor, 45 savol", [x["q_count"] for x in mid], [45])
u7 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 7]
ck("Step 1 Unit 7 bor, 30 savol", [x["q_count"] for x in u7], [30])
u8 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 8]
ck("Step 1 Unit 8 bor, 30 savol", [x["q_count"] for x in u8], [30])
u9 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 9]
ck("Step 1 Unit 9 bor, 30 savol", [x["q_count"] for x in u9], [30])
u10 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 10]
ck("Step 1 Unit 10 bor, 30 savol", [x["q_count"] for x in u10], [30])
u11 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 11]
ck("Step 1 Unit 11 bor, 30 savol", [x["q_count"] for x in u11], [30])
u12 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["unit_no"] == 12]
ck("Step 1 Unit 12 bor, 30 savol", [x["q_count"] for x in u12], [30])
end = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step1" and x["kind"] == "end"]
ck("Step 1 End of course bor, 45 savol", [x["q_count"] for x in end], [45])
s2 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 1]
ck("Step 2 Unit 1 bor, 40 savol", [x["q_count"] for x in s2], [40])
s22 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 2]
ck("Step 2 Unit 2 bor, 40 savol", [x["q_count"] for x in s22], [40])
s23 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 3]
ck("Step 2 Unit 3 bor, 40 savol", [x["q_count"] for x in s23], [40])
s24 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 4]
ck("Step 2 Unit 4 bor, 40 savol", [x["q_count"] for x in s24], [40])
s25 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 5]
ck("Step 2 Unit 5 bor, 40 savol", [x["q_count"] for x in s25], [40])
s26 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 6]
ck("Step 2 Unit 6 bor, 40 savol", [x["q_count"] for x in s26], [40])
s27 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 7]
ck("Step 2 Unit 7 bor, 40 savol", [x["q_count"] for x in s27], [40])
s28 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 8]
ck("Step 2 Unit 8 bor, 40 savol", [x["q_count"] for x in s28], [40])
s29 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 9]
ck("Step 2 Unit 9 bor, 40 savol", [x["q_count"] for x in s29], [40])
s210 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 10]
ck("Step 2 Unit 10 bor, 40 savol", [x["q_count"] for x in s210], [40])
s211 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 11]
ck("Step 2 Unit 11 bor, 40 savol", [x["q_count"] for x in s211], [40])
s212 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["unit_no"] == 12]
ck("Step 2 Unit 12 bor, 40 savol", [x["q_count"] for x in s212], [40])
s2end = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step2" and x["kind"] == "end"]
ck("Step 2 End of course bor, 40 savol", [x["q_count"] for x in s2end], [40])
s31 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 1]
ck("Step 3 Unit 1 bor, 40 savol", [x["q_count"] for x in s31], [40])
s32 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 2]
ck("Step 3 Unit 2 bor, 40 savol", [x["q_count"] for x in s32], [40])
s33 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 3]
ck("Step 3 Unit 3 bor, 40 savol", [x["q_count"] for x in s33], [40])
s34 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 4]
ck("Step 3 Unit 4 bor, 40 savol", [x["q_count"] for x in s34], [40])
s35 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 5]
ck("Step 3 Unit 5 bor, 40 savol", [x["q_count"] for x in s35], [40])
s36 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 6]
ck("Step 3 Unit 6 bor, 40 savol", [x["q_count"] for x in s36], [40])
s37 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 7]
ck("Step 3 Unit 7 bor, 40 savol", [x["q_count"] for x in s37], [40])
s38 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 8]
ck("Step 3 Unit 8 bor, 40 savol", [x["q_count"] for x in s38], [40])
s39 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 9]
ck("Step 3 Unit 9 bor, 40 savol", [x["q_count"] for x in s39], [40])
s310 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 10]
ck("Step 3 Unit 10 bor, 40 savol", [x["q_count"] for x in s310], [40])
s311 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 11]
ck("Step 3 Unit 11 bor, 40 savol", [x["q_count"] for x in s311], [40])
s312 = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["unit_no"] == 12]
ck("Step 3 Unit 12 bor, 40 savol", [x["q_count"] for x in s312], [40])
s3end = [x for x in r.json() if x.get("variant", "A") == "A" and x["level"] == "step3" and x["kind"] == "end"]
ck("Step 3 End of course bor, 45 savol", [x["q_count"] for x in s3end], [45])
mids = {x["level"]: x["q_count"] for x in r.json() if x["kind"] == "mid" and x.get("variant", "A") == "A"}
ck("Step 2 va Step 3 Mid-course bor, 45 savoldan",
   (mids.get("step2"), mids.get("step3")), (45, 45))
t3 = client.get(f"/api/exam-templates/{u3[0]['id']}", headers=HE).json()
q7 = t3["parts"][1]["questions"][0]
ck("rasmli savol", q7["image"], "/exam-img/step1-u3/q7.jpg")
ck("rasm fayli loyihada bor", os.path.exists(os.path.join(
    os.path.dirname(HERE), "public", "exam-img", "step1-u3", "q7.jpg")), True)
full = client.get(f"/api/exam-templates/{TID}", headers=HE).json()
QS = [q for p in full["parts"] for q in p["questions"]]
ck("7-savol javobi", QS[6]["answer"][0], "the USA")
ck("19-savol javobi C", QS[18]["answer"], 2)


def correct_answers(k=30):
    """Birinchi k ta savolga to'g'ri, qolganiga noto'g'ri javob."""
    out = {}
    for i, q in enumerate(QS):
        if i < k:
            out[q["id"]] = q["answer"] if q["type"] == "choice" else q["answer"][0]
        else:
            out[q["id"]] = (q["answer"] + 1) % len(q["options"]) \
                if q["type"] == "choice" else "xxx"
    return out


r = client.post(f"/api/groups/{GID}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(), "max_score": 50})
assert r.status_code == 200, r.text
EID = r.json()["id"]

print("\n=== A2. MAKSIMAL BALL TEST BAZASIDAN ===")
ck("yangi Unit 1 testi: 50 yozilgan, bazadan 30", r.json()["max_score"], 30)
ck("forma uchun: Unit 2 = 30",
   client.get(f"/api/groups/{GID}/exam-bank-max?kind=unit&unit_no=2", headers=HE)
   .json()["max_score"], 30)
# O'tish va yakuniy test 100 ballik (2026-09-25, Jahongir): savollar
# soni emas, jami ball qaytadi - qolgani Writing/Speaking uchun.
ck("forma uchun: Mid = 100",
   client.get(f"/api/groups/{GID}/exam-bank-max?kind=mid", headers=HE)
   .json()["max_score"], 100)
ck("mock uchun yo'q",
   client.get(f"/api/groups/{GID}/exam-bank-max?kind=mock", headers=HE)
   .json()["max_score"], None)
# Eski imtihonlar: natijasizi yangilanadi, natijalisi o'zgarmaydi
d = SessionLocal()
old_empty = models.Exam(group_id=GID, kind="unit", unit_no=2, date=TODAY,
                        max_score=50, status="approved")
old_done = models.Exam(group_id=GID, kind="unit", unit_no=3, date=TODAY,
                       max_score=50, status="done")
d.add_all([old_empty, old_done])
d.commit()
d.add(models.ExamResult(exam_id=old_done.id, student_id=S["Aliyev Ali"],
                        score=40, percent=80.0, counted=1))
d.commit()
exam_online.fill_exam_max_from_bank(d, key="test_fill_v1")
d.refresh(old_empty)
d.refresh(old_done)
ck("natijasiz eski test 30 bo'ldi", old_empty.max_score, 30)
ck("natijali eski test 50 da qoldi", old_done.max_score, 50)
ck("ikkinchi marta ishlamaydi",
   exam_online.fill_exam_max_from_bank(d, key="test_fill_v1"), 0)
d.close()

print("\n=== B. LINK ===")
r = client.post(f"/api/exams/{EID}/online", headers=HT,
                json={"template_id": TID})
ck("ustoz link ocholmaydi", r.status_code, 403)
r = client.get(f"/api/exams/{EID}/online", headers=HE)
ck("mos test taklif qilinadi", [x["id"] for x in r.json()["templates"]][:1],
   [TID])
r = client.post(f"/api/exams/{EID}/online", headers=HE,
                json={"template_id": TID})
ck("examiner link ochdi", r.status_code, 200)
TOKEN = r.json()["online"]["token"]
ck("yangi link — kutish holati", r.json()["online"]["state"], "waiting")
w = client.get(f"/api/public/exam/{TOKEN}").json()
ck("kutishda savol yo'q, ro'yxat bor", (w["state"], len(w["parts"]), len(w["students"])),
   ("waiting", 0, 4))
ck("ustoz start bosa olmaydi",
   client.post(f"/api/exams/{EID}/online/start", headers=HT,
               json={"minutes": 40}).status_code, 403)
r = client.post(f"/api/exams/{EID}/online/start", headers=HE,
                json={"minutes": 40, "countdown": 0})
ck("examiner start bosdi", r.json()["online"]["state"], "running")
ck("qayta start bo'lmaydi",
   client.post(f"/api/exams/{EID}/online/start", headers=HE,
               json={"minutes": 40}).status_code, 400)
d = client.get(f"/api/exams/{EID}", headers=H).json()
ck("maksimal ball = 30", d["max_score"], 30)

print("\n=== C. OCHIQ SAHIFA ===")
r = client.get(f"/api/public/exam/{TOKEN}")
ck("loginsiz 200", r.status_code, 200)
pub = r.json()
ck("ro'yxatda 4 o'quvchi", len(pub["students"]), 4)
ck("javoblar ko'rinmaydi", any("answer" in q for p in pub["parts"] for q in p["questions"]), False)
ck("30 savol", sum(len(p["questions"]) for p in pub["parts"]), 30)
ck("noto'g'ri token 404", client.get("/api/public/exam/xxxxxxxxxxx").status_code, 404)


def submit(**kw):
    body = {"photo": PHOTO, "answers": correct_answers()}
    body.update(kw)
    return client.post(f"/api/public/exam/{TOKEN}/submit", json=body)


def result(sid):
    d = client.get(f"/api/exams/{EID}", headers=H).json()
    return {x["student_id"]: x for x in d["results"]}.get(sid)


def online_score(sid):
    on = client.get(f"/api/exams/{EID}/online", headers=HE).json()
    for s in on["submissions"]:
        if s["student_id"] == sid and s["status"] == "placed":
            return s["online_score"]


print("\n=== D. RO'YXATDAN TANLAGAN ===")
r = submit(student_id=S["Aliyev Ali"])
ck("qabul qilindi", r.status_code, 200)
ck("o'quvchiga ball ko'rsatilmaydi", "score" in r.json(), False)
ck("examiner ko'radi: 30", online_score(S["Aliyev Ali"]), 30.0)

print("\n=== D2. TASDIQLANGUNCHA YASHIRIN ===")
ck("guruh testiga hali yozilmagan", result(S["Aliyev Ali"]), None)
on_t = client.get(f"/api/exams/{EID}/online", headers=HT).json()
ck("ustozga yashirin", (on_t["hidden"], on_t["submissions"]), (True, []))
ck("examiner tasdiqlashi mumkin",
   client.get(f"/api/exams/{EID}/online", headers=HE).json()["can_publish"], True)
ck("ustoz tasdiqlay olmaydi",
   client.post(f"/api/exams/{EID}/online/publish", headers=HT).status_code, 403)
r = client.post(f"/api/exams/{EID}/online/publish", headers=HE)
ck("examiner tasdiqladi", r.status_code, 200)
ck("tasdiq vaqti bor", bool(r.json()["online"]["published_at"]), True)
ck("qayta tasdiqlab bo'lmaydi",
   client.post(f"/api/exams/{EID}/online/publish", headers=HE).status_code, 400)
rr = result(S["Aliyev Ali"])
ck("endi o'z qatorida 100%", rr and rr["percent"], 100.0)
ck("coin 10", rr and rr["coins"], 10)
on_t = client.get(f"/api/exams/{EID}/online", headers=HT).json()
ck("endi ustozga ko'rinadi", (on_t["hidden"], len(on_t["submissions"])), (False, 1))

print("\n=== E. MATNLI JAVOB (tasdiqdan keyin — darhol yoziladi) ===")
ans = correct_answers(18)
ans[QS[6]["id"]] = "the usa"
ans[QS[7]["id"]] = "hina"
ans[QS[12]["id"]] = "The U.K."
r = submit(student_id=S["Boboyev Bobur"], answers=ans)
ck("18 to'g'ri", online_score(S["Boboyev Bobur"]), 18.0)
ck("Boboyev 60%", result(S["Boboyev Bobur"])["percent"], 60.0)

print("\n=== F. QAYTA TOPSHIRSA ===")
r = submit(student_id=S["Boboyev Bobur"])
ck("qabul qilindi, lekin kutmoqda", r.json()["pending"], True)
ck("natija o'zgarmadi", result(S["Boboyev Bobur"])["percent"], 60.0)

print("\n=== G. ISM XATO ===")
r = submit(name="Valiev Vali", answers=correct_answers(27))
ck("pending", r.json()["pending"], True)
on = client.get(f"/api/exams/{EID}/online", headers=HE).json()
pend = [s for s in on["submissions"] if s["status"] == "pending"]
ck("pastda 1 ta", len(pend), 1)
ck("yozilgan ism", pend[0]["typed_name"], "Valiev Vali")
ck("rasm saqlangan", pend[0]["photo"] == PHOTO, True)
dup = [s for s in on["submissions"] if s["status"] == "duplicate"]
ck("takror 1 ta", len(dup), 1)
r = client.post(f"/api/exam-submissions/{pend[0]['id']}/assign",
                headers=HT, json={"student_id": S["Valiyev Vali"]})
ck("ustoz biriktira olmaydi", r.status_code, 403)
r = client.post(f"/api/exam-submissions/{pend[0]['id']}/assign",
                headers=HE, json={"student_id": S["Valiyev Vali"]})
ck("examiner biriktirdi", r.status_code, 200)
# JAVOB VARAG'I: examiner aynan qaysi savolda xato qilganini ko'radi
v = [x for x in r.json()["submissions"]
     if x["student_id"] == S["Valiyev Vali"]][0]
sheet = {d["n"]: d for d in v["detail"]}
ck("30 qator", len(sheet), 30)
ck("to'g'ri javob belgilangan", sheet[1]["ok"], True)
ck("28-savol xato", sheet[28]["ok"], False)
ck("28-savol matni", "Your teacher" in sheet[28]["q"], True)
ck("28 to'g'risi", sheet[28]["correct"], "B) is")
ck("28 o'quvchi javobi", sheet[28]["given_text"], "C) am")
ck("7-savol yozma to'g'risi", sheet[7]["correct"].startswith("the USA"), True)
ck("bo'lim nomi", sheet[19]["part"], "Part 4 · Reading")

ck("Valiyev 90%", result(S["Valiyev Vali"])["percent"], 90.0)
# Takrorni tanlash: Boboyevning ikkinchi (30/30) natijasi qoldiriladi
r = client.post(f"/api/exam-submissions/{dup[0]['id']}/assign",
                headers=HE, json={"student_id": S["Boboyev Bobur"]})
ck("takror qoldirildi", r.status_code, 200)
ck("Boboyev endi 100%", result(S["Boboyev Bobur"])["percent"], 100.0)
st = {s["id"]: s["status"] for s in r.json()["submissions"]}
ck("eski natija replaced", list(st.values()).count("replaced"), 1)

print("\n=== H. ISM AYNAN MOS ===")
r = submit(name="karimova  kamola", answers=correct_answers(15))
ck("o'zi joylashdi", r.json()["pending"], False)
ck("Karimova 50%", result(S["Karimova Kamola"])["percent"], 50.0)
r = submit(name="Begona Odam")
on = client.get(f"/api/exams/{EID}/online", headers=HE).json()
p2 = [s for s in on["submissions"] if s["status"] == "pending"][0]
r = client.post(f"/api/exam-submissions/{p2['id']}/reject", headers=HE)
ck("rad etildi", r.status_code, 200)

print("\n=== I. HIMOYA ===")
r = client.post(f"/api/public/exam/{TOKEN}/submit",
                json={"student_id": S["Aliyev Ali"], "photo": "",
                      "answers": {}})
ck("rasmsiz 400", r.status_code, 400)
r = submit(student_id=999999)
ck("begona id 400", r.status_code, 400)
client.put(f"/api/exams/{EID}/online", headers=HE, json={"is_open": False})
ck("yopiq link 410", submit(student_id=S["Aliyev Ali"]).status_code, 410)
ck("yopiqda ro'yxat yo'q",
   client.get(f"/api/public/exam/{TOKEN}").json()["students"], [])

print("\n=== J. QOG'OZ QISMI ===")
r = client.post(f"/api/groups/{GID}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(), "max_score": 50})
EID2 = r.json()["id"]
r = client.post(f"/api/exams/{EID2}/online", headers=HE,
                json={"template_id": TID, "paper_max": 20})
TOK2 = r.json()["online"]["token"]
client.post(f"/api/exams/{EID2}/online/start", headers=HE,
            json={"minutes": 40, "countdown": 0})
d = client.get(f"/api/exams/{EID2}", headers=H).json()
ck("maksimal 50 (30+20)", d["max_score"], 50)
r = client.post(f"/api/public/exam/{TOK2}/submit", json={
    "student_id": S["Aliyev Ali"], "photo": PHOTO,
    "answers": correct_answers(30)})
ck("online qabul", r.status_code, 200)
# Tasdiqlashdan oldin qog'oz kiritilsa — faqat saqlanadi, natija yo'q
r = client.put(f"/api/exams/{EID2}/paper", headers=HE, json={
    "marks": [{"student_id": S["Aliyev Ali"], "paper": 10}]})
d = client.get(f"/api/exams/{EID2}", headers=H).json()
ck("tasdiqsiz natija yo'q (qog'oz bo'lsa ham)", len(d["results"]), 0)
r = client.put(f"/api/exams/{EID2}/paper", headers=HE, json={
    "marks": [{"student_id": S["Aliyev Ali"], "paper": None}]})
client.post(f"/api/exams/{EID2}/online/publish", headers=HE)
d = client.get(f"/api/exams/{EID2}", headers=H).json()
# 2026-10-03: umuman kirmaganlar e'londa "kelmadi" bo'ladi — ular
# sanalmaydi; qog'ozi kutilayotgan Alining natijasi hali yo'q
ck("qog'ozsiz natija hali yo'q",
   len([x for x in d["results"] if not x.get("absent")]), 0)
ck("Ali kelmadi deb yozilmadi (topshirgan)",
   S["Aliyev Ali"] in {x["student_id"] for x in d["results"]}, False)
r = client.put(f"/api/exams/{EID2}/paper", headers=HE, json={
    "marks": [{"student_id": S["Aliyev Ali"], "paper": 25}]})
ck("20 dan katta rad", r.status_code, 400)
r = client.put(f"/api/exams/{EID2}/paper", headers=HE, json={
    "marks": [{"student_id": S["Aliyev Ali"], "paper": 15}]})
ck("qog'oz saqlandi", r.status_code, 200)
d = client.get(f"/api/exams/{EID2}", headers=H).json()
rr = {x["student_id"]: x for x in d["results"]}[S["Aliyev Ali"]]
ck("jami 45/50", rr["score"], 45.0)
ck("90% -> 10 coin", (rr["percent"], rr["coins"]), (90.0, 10))

print("\n=== K. TEST BAZASI ===")
body = {"level": "step1", "kind": "unit", "unit_no": 2, "title": "Unit 2",
        "paper_max": 10, "parts": [{"title": "P1", "questions": [
            {"type": "choice", "q": "1+1?", "options": ["1", "2"], "answer": 1},
            {"type": "text", "q": "Capital of UK", "answer": "London / london"},
        ]}]}
ck("examiner yarata olmaydi",
   client.post("/api/exam-templates", headers=HE, json=body).status_code, 403)
r = client.post("/api/exam-templates", headers=HB, json=body)
ck("boshliq yaratdi", r.status_code, 200)
ck("javoblar ajratildi", r.json()["parts"][0]["questions"][1]["answer"],
   ["London", "london"])
ext = dict(body, parts=[{"title": "P", "questions": [
    {"type": "choice", "q": "x", "options": ["a", "b"], "answer": 0,
     "image": "https://begona.sayt/rasm.jpg"}]}])
ck("begona sayt rasmi rad",
   client.post("/api/exam-templates", headers=HB, json=ext).status_code, 400)
up = dict(body, unit_no=5, parts=[{"title": "P", "questions": [
    {"type": "choice", "q": "x", "options": ["a", "b"], "answer": 0,
     "image": "data:image/jpeg;base64,AAAA"}]}])
r = client.post("/api/exam-templates", headers=HB, json=up)
ck("yuklangan rasm saqlandi", r.json()["parts"][0]["questions"][0]["image"],
   "data:image/jpeg;base64,AAAA")
bad = dict(body, parts=[{"title": "P", "questions": [
    {"type": "choice", "q": "x", "options": ["a", "b"]}]}])
ck("to'g'ri javobsiz rad",
   client.post("/api/exam-templates", headers=HB, json=bad).status_code, 400)
ck("ishlatilgan test yashiriladi",
   client.delete(f"/api/exam-templates/{TID}", headers=HB).json()["hidden"], True)

print("\n=== T. VAQTLI TEST: KUTISH, SANOQ, AVTOMATIK TOPSHIRISH ===")
from datetime import datetime as _dt, timedelta as _td  # noqa: E402
r = client.post(f"/api/groups/{GID}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(), "max_score": 30})
EID3 = r.json()["id"]
d = SessionLocal()  # K bo'limida yashirilgan Unit 1 testini qayta faollashtiramiz
d.query(models.ExamTemplate).filter(models.ExamTemplate.id == TID).update(
    {models.ExamTemplate.is_active: 1})
d.commit()
d.close()
r = client.post(f"/api/exams/{EID3}/online", headers=HE, json={"template_id": TID})
TOK3 = r.json()["online"]["token"]


def result3(sid):
    d = client.get(f"/api/exams/{EID3}", headers=H).json()
    return {x["student_id"]: x for x in d["results"]}.get(sid)


b1 = client.post(f"/api/public/exam/{TOK3}/begin", json={
    "student_id": S["Aliyev Ali"], "photo": PHOTO})
ck("kutishda kirish mumkin", b1.status_code, 200)
KEY1 = b1.json()["key"]
b2 = client.post(f"/api/public/exam/{TOK3}/begin", json={
    "student_id": S["Karimova Kamola"], "photo": PHOTO})
KEY2 = b2.json()["key"]
on = client.get(f"/api/exams/{EID3}/online", headers=HE).json()
ck("examiner: 2 kishi kutmoqda", on["online"]["in_progress"], 2)
ck("kutishda saqlab bo'lmaydi",
   client.post(f"/api/public/exam/{TOK3}/save",
               json={"key": KEY1, "answers": {"x": 1}}).json()["ok"], False)
r = client.post(f"/api/exams/{EID3}/online/start", headers=HE,
                json={"minutes": 30, "away_limit": 2})
ck("sanoq boshlandi", r.json()["online"]["state"], "countdown")
w = client.get(f"/api/public/exam/{TOK3}").json()
ck("sanoqda savollar hali yo'q", (w["state"], len(w["parts"])), ("countdown", 0))
ck("tugash vaqti bor", bool(w["ends_at"]) and w["duration_min"] == 30, True)
# Sanoqni o'tkazib yuboramiz
d = SessionLocal()
o3 = d.query(models.ExamOnline).filter(models.ExamOnline.exam_id == EID3).first()
o3.started_at = _dt.utcnow() - _td(seconds=1)
o3.ends_at = _dt.utcnow() + _td(minutes=30)
d.commit()
d.close()
w = client.get(f"/api/public/exam/{TOK3}").json()
ck("test ochildi — 30 savol", (w["state"], sum(len(p["questions"]) for p in w["parts"])),
   ("running", 30))
# Sahifadan chiqish qaydi (skrinshotning o'zi sezilmaydi, lekin
# savolni boshqa ilovaga olib chiqish ko'rinadi)
client.post(f"/api/public/exam/{TOK3}/away", json={"key": KEY1, "seconds": 45})
client.post(f"/api/public/exam/{TOK3}/away", json={"key": KEY1, "seconds": 15})
on = client.get(f"/api/exams/{EID3}/online", headers=HE).json()
live = {x["name"]: x for x in on["online"]["live"]}
ck("examiner jonli ko'radi: 2 marta, 60 soniya",
   (live["Aliyev Ali"]["away_count"], live["Aliyev Ali"]["away_sec"]), (2, 60))
ck("javob saqlandi",
   client.post(f"/api/public/exam/{TOK3}/save",
               json={"key": KEY1, "answers": correct_answers(20)}).json()["ok"], True)
client.post(f"/api/public/exam/{TOK3}/save",
            json={"key": KEY2, "answers": correct_answers(10)})
# CHIQISHLAR CHEGARASI: 2 martagacha uzrli, uchinchisida chetlatiladi
bv = client.post(f"/api/public/exam/{TOK3}/begin", json={
    "student_id": S["Valiyev Vali"], "photo": PHOTO})
KEYV = bv.json()["key"]
client.post(f"/api/public/exam/{TOK3}/save",
            json={"key": KEYV, "answers": correct_answers(30)})
ck("ruxsat qolgani ko'rinadi",
   client.post(f"/api/public/exam/{TOK3}/away",
               json={"key": KEYV, "seconds": 5}).json()["left"], 1)
r = client.post(f"/api/public/exam/{TOK3}/away", json={"key": KEYV, "seconds": 5})
ck("chegarada hali chetlatilmaydi", r.json().get("expelled"), None)
r = client.post(f"/api/public/exam/{TOK3}/away", json={"key": KEYV, "seconds": 5})
ck("chegaradan oshdi — chetlatildi", r.json().get("expelled"), True)
ck("chetlatilganning sahifasi yopiladi",
   client.post(f"/api/public/exam/{TOK3}/save",
               json={"key": KEYV, "answers": correct_answers(30)}).json(),
   {"ok": False, "expelled": True})
ck("chetlatilgan topshira olmaydi",
   client.post(f"/api/public/exam/{TOK3}/submit",
               json={"key": KEYV, "answers": correct_answers(30)}).json()["expelled"],
   True)
on = client.get(f"/api/exams/{EID3}/online", headers=HE).json()
ck("examiner ro'yxatida chetlatilgan",
   [x["name"] for x in on["online"]["expelled"]], ["Valiyev Vali"])
ck("natijasi yozilmadi (30/30 belgilagan bo'lsa ham)",
   result3(S["Valiyev Vali"]), None)
# Karimova o'rniga boshqa o'quvchi kirib, qo'lda chetlatiladi
b3 = client.post(f"/api/public/exam/{TOK3}/begin", json={
    "student_id": S["Boboyev Bobur"], "photo": PHOTO})
KEY3 = b3.json()["key"]
client.post(f"/api/public/exam/{TOK3}/save",
            json={"key": KEY3, "answers": correct_answers(30)})
sid3 = [x["id"] for x in client.get(f"/api/exams/{EID3}/online", headers=HE)
        .json()["online"]["live"] if x["name"] == "Boboyev Bobur"][0]
ck("ustoz chetlata olmaydi",
   client.post(f"/api/exam-submissions/{sid3}/expel", headers=HT).status_code, 403)
r = client.post(f"/api/exam-submissions/{sid3}/expel", headers=HE)
ck("examiner chetlatdi", r.status_code, 200)
ck("uning testi ham yopildi",
   client.post(f"/api/public/exam/{TOK3}/save",
               json={"key": KEY3, "answers": {}}).json()["expelled"], True)
ck("qayta chetlatib bo'lmaydi",
   client.post(f"/api/exam-submissions/{sid3}/expel", headers=HE).status_code, 400)
ck("begona kalit rad",
   client.post(f"/api/public/exam/{TOK3}/save",
               json={"key": "xxxxxxxxxxxxxx", "answers": {}}).status_code, 400)
# Karimova o'zi topshiradi, Aliyevning sahifasi yopilib qoldi
r = client.post(f"/api/public/exam/{TOK3}/submit",
                json={"key": KEY2, "answers": correct_answers(12)})
ck("qo'lda topshirdi", r.json()["ok"], True)
# Examiner muddatidan oldin tugatadi; muhlat ham o'tdi
r = client.post(f"/api/exams/{EID3}/online/stop", headers=HE)
ck("examiner tugatdi", r.json()["online"]["state"], "finished")
d = SessionLocal()
o3 = d.query(models.ExamOnline).filter(models.ExamOnline.exam_id == EID3).first()
o3.ends_at = _dt.utcnow() - _td(seconds=exam_online.GRACE_SEC + 5)
d.commit()
d.close()
on = client.get(f"/api/exams/{EID3}/online", headers=HE).json()
byname = {x["typed_name"]: x for x in on["submissions"]}
ck("topshirmagan avtomatik yakunlandi — saqlangan 20 ta",
   (byname["Aliyev Ali"]["status"], byname["Aliyev Ali"]["online_score"]),
   ("placed", 20.0))
ck("qo'lda topshirgan — 12", byname["Karimova Kamola"]["online_score"], 12.0)
ck("hech kim kutmayapti", on["online"]["in_progress"], 0)
ck("javob varag'ida ham qoladi", byname["Aliyev Ali"]["away_count"], 2)
ck("tugagandan keyin qayd qilinmaydi",
   client.post(f"/api/public/exam/{TOK3}/away",
               json={"key": KEY1, "seconds": 30}).json().get("away_count"), None)
ck("tugagandan keyin kirib bo'lmaydi",
   client.post(f"/api/public/exam/{TOK3}/begin",
               json={"student_id": S["Valiyev Vali"], "photo": PHOTO}).status_code, 410)
ck("tugagandan keyin ro'yxat ham yo'q",
   client.get(f"/api/public/exam/{TOK3}").json()["students"], [])

print("\n=== L. ONLINE TOPSHIRILGAN IMTIHONNI O'CHIRISH ===")
r = client.delete(f"/api/exams/{EID}", headers=HB)
ck("o'chirildi (500 emas)", r.status_code, 200)
d = SessionLocal()
ck("topshiriqlar ham o'chdi", d.query(models.ExamSubmission).filter(
    models.ExamSubmission.exam_id == EID).count(), 0)
ck("link ham o'chdi", d.query(models.ExamOnline).filter(
    models.ExamOnline.exam_id == EID).count(), 0)
d.close()
ck("eski link endi 404",
   client.get(f"/api/public/exam/{TOKEN}").status_code, 404)
ck("ikkinchi test joyida",
   client.get(f"/api/exams/{EID2}", headers=H).status_code, 200)

print()
print("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}")
sys.exit(1 if fails else 0)
