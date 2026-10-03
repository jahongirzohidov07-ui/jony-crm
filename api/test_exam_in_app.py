"""IMTIHON JONY STUDENT ILOVASI ICHIDA (2026-09-25).

Jahongir: "cherer Student app qiladigan qilish kerak link ham shu
Student appga keladigan qilaylik" + "baribir ozini tasdiqlashi kerak
rasm bilan chunki birovni nomidan boshqasi ishlashi ham mumkin".

Tekshiriladi:
  A. Ochiq link o'quvchining ilovasida o'zi ko'rinadi: /student/exams,
     bosh sahifa (exam_live) va bildirishnoma (href ilovaga);
     boshqa guruh o'quvchisiga ko'rinmaydi; ko'p-guruh bog'lanishi
     orqali ham ko'rinadi;
  B. Ilovadagi holat sahifasi: "me" login'dan, ro'yxat yo'q, boshqa
     guruh o'quvchisiga 403, loginsiz yopiq, examiner tokeni bilan yopiq;
  C. Kirish: rasmsiz 400; rasm bilan kalit; qayta kirsa O'SHA kalit
     (ikkinchi yozuv ochilmaydi); holatda my.status=in_progress + kalit;
  D. Start → savollar keladi, javoblari yo'q; saqlash/topshirish eski
     public yo'llar orqali (kalit bilan) — natija to'g'ridan-to'g'ri
     o'z qatoriga (pending yo'q);
  E. Topshirgach: qayta kirish 409; ro'yxatdan tushadi, tarixga o'tadi;
     ball examiner e'lon qilguncha ko'rinmaydi, e'londan keyin ko'rinadi;
  F. Chetlatilgan o'quvchi qayta kira olmaydi (403);
  G. Ilovada hisobi yo'q o'quvchi uchun eski (link) tartib ishlayveradi;
  H. Link yopilsa: holat "closed", kirish 410.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "exam_in_app_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry  # noqa: F401,E402
import exam_online                                  # noqa: E402
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


TODAY = roles.local_today()
PHOTO = "data:image/jpeg;base64," + "A" * 200

db = SessionLocal()
exam_online.seed_templates(db)
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
for un, role in [("asos", "founder"), ("exam", "examiner")]:
    db.add(models.User(username=un, password_hash=hash_password("x"),
                       full_name=un.title(), role=role, branch_id=BID))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID)
db.add(t)
db.commit()
gA = models.Group(name="Apex", branch_id=BID, teacher_id=t.id,
                  subject="english", level="step1")
gB = models.Group(name="Beta", branch_id=BID, teacher_id=t.id,
                  subject="english", level="step1")
db.add_all([gA, gB])
db.commit()
GA, GB = gA.id, gB.id


def mk_student(name, gid, phone=None):
    s = models.Student(full_name=name, branch_id=BID, group_id=gid,
                       status="active", phone=phone,
                       enrolled_date=TODAY - timedelta(days=60))
    db.add(s)
    db.commit()
    if phone:
        u = models.User(username=phone, password_hash=hash_password("jonyjony"),
                        full_name=name, role=roles.STUDENT, branch_id=BID,
                        is_active=1)
        db.add(u)
        db.commit()
        s.user_id = u.id
        db.commit()
    return s.id


ALI = mk_student("Aliyev Ali", GA, "998900000001")        # Apex, ilovada
VALI = mk_student("Valiyev Vali", GB, "998900000002")     # Beta, ilovada
KAMOLA = mk_student("Karimova Kamola", GB, "998900000003")  # Beta + Apex link
BOBUR = mk_student("Boboyev Bobur", GA)                   # Apex, ilovasiz
db.add(models.StudentGroupLink(student_id=KAMOLA, group_id=GA,
                               is_primary=0, active=1))
les = models.Lesson(group_id=GA, date=TODAY - timedelta(days=10))
db.add(les)
db.commit()
for sid in (ALI, BOBUR, KAMOLA):
    db.add(models.Attendance(lesson_id=les.id, student_id=sid, present=1))
db.commit()
db.close()

H = tok("asos")
HE = tok("exam")
HA = tok("998900000001", "jonyjony")
HV = tok("998900000002", "jonyjony")
HK = tok("998900000003", "jonyjony")

tpl = [x for x in client.get("/api/exam-templates", headers=HE).json()
       if x["level"] == "step1" and x["unit_no"] == 1]
TID = tpl[0]["id"]
full = client.get(f"/api/exam-templates/{TID}", headers=HE).json()
QS = [q for p in full["parts"] for q in p["questions"]]


def correct_answers(k=30):
    out = {}
    for i, q in enumerate(QS):
        if i < k:
            out[q["id"]] = q["answer"] if q["type"] == "choice" else q["answer"][0]
        else:
            out[q["id"]] = (q["answer"] + 1) % len(q["options"]) \
                if q["type"] == "choice" else "xxx"
    return out


r = client.post(f"/api/groups/{GA}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(), "max_score": 30})
assert r.status_code == 200, r.text
EID = r.json()["id"]

print("=== A0. LINK YO'Q — ILOVADA HAM YO'Q ===")
r = client.get("/api/student/exams/online", headers=HA)
ck("200", r.status_code, 200)
ck("faol imtihon yo'q", r.json()["active"], [])
home = client.get("/api/student/home", headers=HA).json()
ck("bosh sahifada exam_live bo'sh", home.get("exam_live"), [])

r = client.post(f"/api/exams/{EID}/online", headers=HE, json={"template_id": TID})
assert r.status_code == 200, r.text
TOKEN = r.json()["online"]["token"]

print("\n=== A. OCHIQ LINK ILOVADA O'ZI KO'RINADI ===")
r = client.get("/api/student/exams/online", headers=HA)
act = r.json()["active"]
ck("Ali: 1 ta faol", len(act), 1)
ck("token mos", act[0]["token"], TOKEN)
ck("holat kutish, hali kirmagan", (act[0]["state"], act[0]["my_status"]),
   ("waiting", "none"))
ck("30 savol, guruh nomi", (act[0]["q_count"], act[0]["group"]), (30, "Apex"))
ck("Vali (Beta): ko'rinmaydi",
   client.get("/api/student/exams/online", headers=HV).json()["active"], [])
ck("Kamola (ko'p-guruh bog'lanishi orqali Apex): ko'rinadi",
   [x["token"] for x in
    client.get("/api/student/exams/online", headers=HK).json()["active"]], [TOKEN])
home = client.get("/api/student/home", headers=HA).json()
ck("bosh sahifada exam_live 1 ta", [x["token"] for x in home["exam_live"]], [TOKEN])
ck("exam_live holati", (home["exam_live"][0]["state"],
                        home["exam_live"][0]["my_status"]), ("waiting", "none"))
nt = client.get("/api/student/notifications", headers=HA).json()["items"]
ex_n = [n for n in nt if n["id"] == f"exam-live:{TOKEN}"]
ck("bildirishnomada 1 ta", len(ex_n), 1)
ck("bildirishnoma ilovaga olib kiradi", ex_n[0].get("href"),
   f"/student/exam/{TOKEN}")
ck("bildirishnoma turi", ex_n[0]["kind"], "exam")
ntv = client.get("/api/student/notifications", headers=HV).json()["items"]
ck("Valiga bildirishnoma yo'q",
   [n for n in ntv if n["id"].startswith("exam-live:")], [])

print("\n=== B. ILOVADAGI HOLAT SAHIFASI ===")
r = client.get(f"/api/student/exam/{TOKEN}", headers=HA)
ck("Ali 200", r.status_code, 200)
st = r.json()
ck("kim ekani login'dan", st["me"], {"id": ALI, "name": "Aliyev Ali"})
ck("ro'yxat yo'q (tanlash yo'q)", st["students"], [])
ck("hali kirmagan", st["my"], None)
ck("kutishda savol yo'q", (st["state"], st["parts"]), ("waiting", []))
ck("Vali (boshqa guruh) 403",
   client.get(f"/api/student/exam/{TOKEN}", headers=HV).status_code, 403)
ck("loginsiz yopiq",
   client.get(f"/api/student/exam/{TOKEN}").status_code in (401, 403), True)
ck("examiner tokeni bilan yopiq (faqat o'quvchi)",
   client.get(f"/api/student/exam/{TOKEN}", headers=HE).status_code, 403)
ck("examiner /student/exams ham yopiq",
   client.get("/api/student/exams/online", headers=HE).status_code, 403)
ck("noto'g'ri token 404",
   client.get("/api/student/exam/xxxxxxxxxxxx", headers=HA).status_code, 404)

print("\n=== C. KIRISH — RASM BILAN, KALIT BITTA ===")
r = client.post(f"/api/student/exam/{TOKEN}/begin", headers=HA, json={"photo": ""})
ck("rasmsiz 400", r.status_code, 400)
r = client.post(f"/api/student/exam/{TOKEN}/begin", headers=HA,
                json={"photo": "hello"})
ck("rasm emas 400", r.status_code, 400)
r = client.post(f"/api/student/exam/{TOKEN}/begin", headers=HA, json={"photo": PHOTO})
ck("rasm bilan 200", r.status_code, 200)
KEY = r.json()["key"]
ck("kalit bor, yangi", (len(KEY) >= 16, r.json()["resumed"]), (True, False))
ck("ism login'dan", r.json()["name"], "Aliyev Ali")
r = client.post(f"/api/student/exam/{TOKEN}/begin", headers=HA, json={"photo": PHOTO})
ck("qayta kirsa o'sha kalit", (r.json()["key"], r.json()["resumed"]), (KEY, True))
d = SessionLocal()
subs = d.query(models.ExamSubmission).filter_by(exam_id=EID, student_id=ALI).all()
ck("bazada 1 ta yozuv", len(subs), 1)
ck("yozuv: o'quvchi biriktirilgan, rasm saqlangan, davom etmoqda",
   (subs[0].student_id, subs[0].photo == PHOTO, subs[0].status,
    subs[0].typed_name), (ALI, True, "in_progress", "Aliyev Ali"))
d.close()
st = client.get(f"/api/student/exam/{TOKEN}", headers=HA).json()
ck("holat: davom etmoqda + kalit qaytadi",
   (st["my"]["status"], st["my"]["key"]), ("in_progress", KEY))
act = client.get("/api/student/exams/online", headers=HA).json()["active"]
ck("ro'yxatda hali turadi (my_status in_progress)",
   [(x["token"], x["my_status"]) for x in act], [(TOKEN, "in_progress")])
home = client.get("/api/student/home", headers=HA).json()
ck("bosh sahifada ham", home["exam_live"][0]["my_status"], "in_progress")
ck("Vali kira olmaydi (403)",
   client.post(f"/api/student/exam/{TOKEN}/begin", headers=HV,
               json={"photo": PHOTO}).status_code, 403)

print("\n=== D. START → SAVOLLAR, JAVOB, TOPSHIRISH ===")
r = client.post(f"/api/exams/{EID}/online/start", headers=HE,
                json={"minutes": 40, "countdown": 0})
ck("examiner start", r.json()["online"]["state"], "running")
st = client.get(f"/api/student/exam/{TOKEN}", headers=HA).json()
ck("endi savollar keladi", sum(len(p["questions"]) for p in st["parts"]), 30)
ck("javoblar ko'rinmaydi",
   any("answer" in q for p in st["parts"] for q in p["questions"]), False)
ck("vaqt bor", (st["state"], bool(st["ends_at"]), st["duration_min"]),
   ("running", True, 40))
r = client.post(f"/api/public/exam/{TOKEN}/save",
                json={"key": KEY, "answers": correct_answers(5)})
ck("oraliq saqlash (eski yo'l, kalit bilan)", r.json(), {"ok": True})
# BOSHQA TELEFON (2026-10-03): yangi telefon bo'sh {} yuboradi —
# serverdagi 30 ta javob o'chmasligi va holatda qaytishi kerak
r = client.post(f"/api/public/exam/{TOKEN}/save", json={"key": KEY, "answers": {}})
ck("bo'sh saqlash ham 200", r.json(), {"ok": True})
st = client.get(f"/api/student/exam/{TOKEN}", headers=HA).json()
ck("boshqa telefonda javoblar qaytadi (30 ta)", len(st["my"]["answers"] or {}), 30)
r = client.post(f"/api/public/exam/{TOKEN}/away", json={"key": KEY, "seconds": 3})
ck("chiqish qayd qilinadi", r.json().get("away_count"), 1)
r = client.post(f"/api/public/exam/{TOKEN}/submit",
                json={"key": KEY, "answers": correct_answers(27)})
ck("topshirdi", r.status_code, 200)
ck("pending YO'Q — to'g'ridan-to'g'ri o'z qatoriga", r.json()["pending"], False)
ck("ball o'quvchiga qaytmaydi", "score" in r.json(), False)
on = client.get(f"/api/exams/{EID}/online", headers=HE).json()
mine = [s for s in on["submissions"] if s["student_id"] == ALI]
ck("examiner ko'radi: placed, 27 ball, rasm, 1 chiqish",
   (mine[0]["status"], mine[0]["online_score"], mine[0]["photo"] == PHOTO,
    mine[0]["away_count"]), ("placed", 27.0, True, 1))

print("\n=== E. TOPSHIRGACH ===")
ck("qayta kirish 409",
   client.post(f"/api/student/exam/{TOKEN}/begin", headers=HA,
               json={"photo": PHOTO}).status_code, 409)
st = client.get(f"/api/student/exam/{TOKEN}", headers=HA).json()
ck("holat: topshirilgan, kalit yo'q, pending yo'q",
   (st["my"]["status"], st["my"]["key"], st["my"]["pending"]),
   ("placed", None, False))
ex = client.get("/api/student/exams/online", headers=HA).json()
ck("faoldan tushdi", ex["active"], [])
ck("tarixda 1 ta", [(x["token"], x["my_status"]) for x in ex["history"]],
   [(TOKEN, "placed")])
ck("e'lon qilinmagan — ball yo'q",
   (ex["history"][0]["published"], "score" in ex["history"][0]), (False, False))
home = client.get("/api/student/home", headers=HA).json()
ck("bosh sahifadan tushdi", home["exam_live"], [])
nt = client.get("/api/student/notifications", headers=HA).json()["items"]
ck("bildirishnomadan tushdi",
   [n for n in nt if n["id"] == f"exam-live:{TOKEN}"], [])
ck("Kamola (kirmagan) uchun hali turadi",
   [x["my_status"] for x in
    client.get("/api/student/exams/online", headers=HK).json()["active"]], ["none"])
r = client.post(f"/api/exams/{EID}/online/publish", headers=HE)
ck("examiner e'lon qildi", r.status_code, 200)
ex = client.get("/api/student/exams/online", headers=HA).json()
h = ex["history"][0]
ck("e'londan keyin ball: 27/30 = 90%",
   (h["published"], h["score"], h["max_score"], h["percent"]),
   (True, 27, 30, 90))
res = {x["student_id"]: x for x in
       client.get(f"/api/exams/{EID}", headers=H).json()["results"]}
ck("guruh imtihonida o'z qatorida 90%", res[ALI]["percent"], 90.0)
# Avvaldan bor /api/student/exams (tasdiqlangan natijalar tarixi)
# buzilmagan — yangi ro'yxat alohida manzilda (/exams/online)
r = client.get("/api/student/exams", headers=HA)
ck("eski natijalar tarixi ishlaydi", r.status_code, 200)
ck("eski tarixda 90% ko'rinadi",
   [round(x["percent"]) for x in r.json()["rows"]], [90])

print("\n=== F. CHETLATILGAN ===")
r = client.post(f"/api/student/exam/{TOKEN}/begin", headers=HK, json={"photo": PHOTO})
ck("Kamola kirdi", r.status_code, 200)
d = SessionLocal()
o_, exam_ = exam_online._public(d, TOKEN)
sub_k = exam_online._my_sub(d, EID, KAMOLA)
exam_online.expel(d, exam_, sub_k, "test")
d.close()
ck("chetlatilgan — qayta kira olmaydi (403)",
   client.post(f"/api/student/exam/{TOKEN}/begin", headers=HK,
               json={"photo": PHOTO}).status_code, 403)
st = client.get(f"/api/student/exam/{TOKEN}", headers=HK).json()
ck("holatda expelled", st["my"]["status"], "expelled")
ck("faol ro'yxatdan tushdi",
   client.get("/api/student/exams/online", headers=HK).json()["active"], [])

print("\n=== G. ILOVASIZ O'QUVCHI — ESKI LINK TARTIBI ===")
pub = client.get(f"/api/public/exam/{TOKEN}").json()
ck("ochiq sahifada ro'yxat bor (tanlash uchun)",
   BOBUR in [s["id"] for s in pub["students"]], True)
r = client.post(f"/api/public/exam/{TOKEN}/begin",
                json={"student_id": BOBUR, "photo": PHOTO})
ck("ro'yxatdan tanlab kirdi", r.status_code, 200)
KB = r.json()["key"]
r = client.post(f"/api/public/exam/{TOKEN}/submit",
                json={"key": KB, "answers": correct_answers(30)})
ck("topshirdi", (r.status_code, r.json()["pending"]), (200, False))
res = {x["student_id"]: x for x in
       client.get(f"/api/exams/{EID}", headers=H).json()["results"]}
ck("Bobur 100% (e'lon qilingan imtihon — darhol)", res[BOBUR]["percent"], 100.0)

print("\n=== H. LINK YOPILSA ===")
r = client.put(f"/api/exams/{EID}/online", headers=HE, json={"is_open": False})
ck("yopildi", r.status_code, 200)
st = client.get(f"/api/student/exam/{TOKEN}", headers=HK).json()
ck("holat closed", (st["is_open"], st["state"]), (False, "closed"))
# Yangi o'quvchi (hali kirmagan) uchun 410
d = SessionLocal()
d.query(models.ExamSubmission).filter_by(exam_id=EID, student_id=KAMOLA).update(
    {"status": "replaced"})
d.commit()
d.close()
ck("yopiq linkka kirish 410",
   client.post(f"/api/student/exam/{TOKEN}/begin", headers=HK,
               json={"photo": PHOTO}).status_code, 410)
ck("yopiq — faol ro'yxatda yo'q",
   client.get("/api/student/exams/online", headers=HK).json()["active"], [])

print("\n" + ("HAMMASI OK" if not fails else "XATOLAR: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
