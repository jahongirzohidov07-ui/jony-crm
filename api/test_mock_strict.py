"""MOCK — QAT'IY TARTIB (2026-09-27).

Jahongir: "test boshlanganda bunaqa google translate boshqa boshqa
narsalari ishlamasligi kerak mock test faqat kompyuterda ishlanadi bizda
telda mumkinmas, boshqa joyga ham chiqshi mumkinmas qatiy tizim bo'lishi
kerak. Mock testda telefon ruxsat berilmaydi mumkinmas rasmga olish ham".

Server tomoni (sahifadagi to'liq ekran / kengaytma / tugmalar —
src/components/StrictExam.tsx):
  A. Mock: GET da strict=true va chegara 2; telefon / planshet UA bilan
     /begin 403, kompyuter UA bilan 200; kalitsiz eski /submit ham 403;
  B. Mock: examiner chegara qo'ymagan — 2 marta chiqish mumkin, 3-chisida
     chetlatiladi; izohda chetlatishga olib kelgan SABAB turadi;
  C. Mock: examiner o'zi 4 qo'ygan — 5-chisida chetlatiladi;
  D. Mock: bazada chegara umuman yo'q (Start'siz) — baribir 2;
  E. Unit test — avvalgidek: telefondan kirish mumkin, strict yo'q,
     Start'da 5, chegara yo'q bo'lsa chetlatilmaydi;
  F. Ilovadagi (Jony Student) mock: strict=true, telefondan /begin 403;
  G. Xodim mock sinovi: POST /api/mock-practice telefondan 403.
  H. Mock: chetlatilgan o'quvchi maxfiy oyna / boshqa brauzerda ismini
     qayta tanlab kira olmaydi (403), boshlagani bo'lsa 409; unit — avvalgidek;
  I. /away: eid bilan takror yuborish sanalmaydi; extend — faqat soniya;
     flag=nofs — sanalmaydi, examiner jonli ro'yxatda ko'radi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "mock_strict_test.db")
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

IPHONE = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 "
                        "Mobile/15E148 Safari/604.1"}
ANDROID = {"User-Agent": "Mozilla/5.0 (Linux; Android 14; SM-A546B) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/126.0.0.0 Mobile Safari/537.36"}
DESKTOP = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/126.0.0.0 Safari/537.36"}


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
exam_online.seed_templates(db)
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
gi = models.Group(name="IELTS-A", branch_id=BID, teacher_id=t.id,
                  subject="english", level="ielts_graduation")
gs = models.Group(name="Step-A", branch_id=BID, teacher_id=t.id,
                  subject="english", level="step1")
db.add_all([gi, gs])
db.commit()
GI, GS = gi.id, gs.id
s = models.Student(full_name="Aliyev Ali", branch_id=BID, group_id=GI,
                   status="active", phone="998900000011",
                   enrolled_date=TODAY - timedelta(days=60))
db.add(s)
db.commit()
u = models.User(username="998900000011", password_hash=hash_password("jonyjony"),
                full_name="Aliyev Ali", role=roles.STUDENT, branch_id=BID,
                is_active=1)
db.add(u)
db.commit()
s.user_id = u.id
db.commit()
SID = s.id
sv = models.Student(full_name="Valiyev Vali", branch_id=BID, group_id=GS,
                    status="active", phone="998900000012",
                    enrolled_date=TODAY - timedelta(days=60))
db.add(sv)
db.commit()
SVID = sv.id

H = tok("asos")
HE = tok("bosh")
HS = tok("998900000011", "jonyjony")


def make_exam(gid, kind, **extra):
    r = client.post(f"/api/groups/{gid}/exams", headers=H, json={
        "kind": kind, "date": TODAY.isoformat(), "max_score": None, **extra})
    assert r.status_code == 200, r.text
    eid = r.json()["id"]
    client.put(f"/api/exams/{eid}", headers=H, json={"status": "approved"})
    return eid


def open_link(eid, tpl_id, **start):
    r = client.post(f"/api/exams/{eid}/online", headers=HE,
                    json={"template_id": tpl_id})
    assert r.status_code == 200, r.text
    r2 = client.post(f"/api/exams/{eid}/online/start", headers=HE,
                     json={"minutes": 60, "countdown": 0, **start})
    assert r2.status_code == 200, r2.text
    return client.get(f"/api/exams/{eid}/online", headers=HE).json()["online"]


def begin(token, name, headers=DESKTOP):
    return client.post(f"/api/public/exam/{token}/begin", headers=headers,
                       json={"name": name, "photo": PHOTO})


def away(token, key, reason=None, seconds=3):
    body = {"key": key, "seconds": seconds}
    if reason:
        body["reason"] = reason
    return client.post(f"/api/public/exam/{token}/away", json=body).json()


def sub_of(key):
    d = SessionLocal()
    try:
        x = d.query(models.ExamSubmission).filter_by(sub_key=key).first()
        return (x.status, x.note or "", x.away_count or 0)
    finally:
        d.close()


def sec_of(key):
    d = SessionLocal()
    try:
        return d.query(models.ExamSubmission).filter_by(sub_key=key).first().away_sec or 0
    finally:
        d.close()


def begin_id(token, sid, headers=DESKTOP):
    return client.post(f"/api/public/exam/{token}/begin", headers=headers,
                       json={"student_id": sid, "photo": PHOTO})


def away2(token, key, **body):
    return client.post(f"/api/public/exam/{token}/away",
                       json={"key": key, **body}).json()


tpls = [x for x in client.get("/api/exam-templates", headers=HE).json()
        if x["kind"] == "mock" and x["level"] == "ielts_graduation"
        and "Listening" in x["title"]]
MOCK_TPL = sorted(tpls, key=lambda x: x["id"])[0]["id"]
UNIT_TPL = [x for x in client.get("/api/exam-templates", headers=HE).json()
            if x["level"] == "step1" and x["unit_no"] == 1][0]["id"]

# ------------------------------------------------------------------ A
print("=== A. MOCK: FAQAT KOMPYUTERDA ===")
MEID = make_exam(GI, "mock")
on = open_link(MEID, MOCK_TPL)
MTOK = on["token"]
ck("examiner oynasida chegara 2 (belgilanmagan mock)", on["away_limit"], 2)
pub = client.get(f"/api/public/exam/{MTOK}").json()
ck("GET: strict=true", pub.get("strict"), True)
ck("GET: away_limit=2", pub.get("away_limit"), 2)
r = begin(MTOK, "Mehmon Birinchi", IPHONE)
ck("iPhone: /begin 403", r.status_code, 403)
ck("iPhone: xabar", r.json().get("detail"), "Mock test faqat kompyuterda ishlanadi")
ck("Android: /begin 403", begin(MTOK, "Mehmon Birinchi", ANDROID).status_code, 403)
r = client.post(f"/api/public/exam/{MTOK}/submit", headers=IPHONE, json={
    "photo": PHOTO, "name": "Mehmon Eski", "answers": {}})
ck("iPhone: kalitsiz eski /submit ham 403", r.status_code, 403)
r = begin(MTOK, "Mehmon Birinchi", DESKTOP)
ck("kompyuter: /begin 200", r.status_code, 200)
K1 = r.json()["key"]

# ------------------------------------------------------------------ B
print("\n=== B. MOCK: 2 MARTA MUMKIN, 3-CHISIDA CHETLATILADI ===")
j = away(MTOK, K1, "tab")
ck("1-chiqish: chetlatilmadi, yana 1", (j.get("expelled"), j.get("left")), (None, 1))
j = away(MTOK, K1, "blur")
ck("2-chiqish: chetlatilmadi, yana 0", (j.get("expelled"), j.get("left")), (None, 0))
j = away(MTOK, K1, "fullscreen")
ck("3-chiqish: chetlatildi", j.get("expelled"), True)
st, note, cnt = sub_of(K1)
ck("holat expelled, 3 marta", (st, cnt), ("expelled", 3))
ck("izohda sabab: to'liq ekrandan chiqdi", "to'liq ekrandan chiqdi" in note, True)
ck("izohda chegara", "(ruxsat: 2)" in note, True)
r = client.post(f"/api/public/exam/{MTOK}/save", json={"key": K1, "answers": {}})
ck("chetlatilgan: save expelled", r.json().get("expelled"), True)
# Noma'lum sabab izohga tushmaydi, xato ham bermaydi
K1b = begin(MTOK, "Mehmon Ikkinchi").json()["key"]
for _ in range(2):
    away(MTOK, K1b, "nimadir")
j = away(MTOK, K1b, "nimadir")
st, note, _c = sub_of(K1b)
ck("noma'lum sabab: chetlatildi, izohda 'oxirgisi' yo'q",
   (j.get("expelled"), "oxirgisi" in note), (True, False))

# ------------------------------------------------------------------ C
print("\n=== C. MOCK: EXAMINER CHEGARASI HURMAT QILINADI ===")
MEID2 = make_exam(GI, "mock")
on2 = open_link(MEID2, MOCK_TPL, away_limit=4)
ck("examiner 4 qo'ydi", on2["away_limit"], 4)
K2 = begin(on2["token"], "Mehmon Uchinchi").json()["key"]
res = [away(on2["token"], K2, "tab").get("expelled") for _ in range(4)]
ck("4 marta chiqdi — chetlatilmadi", res, [None] * 4)
ck("5-chisida chetlatildi", away(on2["token"], K2, "extension").get("expelled"), True)
ck("izohda: kengaytma", "brauzer kengaytmasi" in sub_of(K2)[1], True)

# ------------------------------------------------------------------ D
print("\n=== D. MOCK: BAZADA CHEGARA YO'Q — SERVER BARIBIR 2 ===")
d = SessionLocal()
o = d.query(models.ExamOnline).filter_by(exam_id=MEID2).first()
o.away_limit = None
d.commit()
d.close()
ck("examiner oynasida 2",
   client.get(f"/api/exams/{MEID2}/online", headers=HE).json()["online"]["away_limit"], 2)
K3 = begin(on2["token"], "Mehmon To'rtinchi").json()["key"]
res = [away(on2["token"], K3, "blur").get("expelled") for _ in range(3)]
ck("3-chisida chetlatildi", res, [None, None, True])

# ------------------------------------------------------------------ E
print("\n=== E. UNIT TEST — AVVALGIDEK ===")
UEID = make_exam(GS, "unit", unit_no=1)
uon = open_link(UEID, UNIT_TPL)
UTOK = uon["token"]
ck("unit: Start'da chegara 5 (bugungi)", uon["away_limit"], 5)
upub = client.get(f"/api/public/exam/{UTOK}").json()
ck("unit: strict yo'q", bool(upub.get("strict")), False)
ck("unit: away_limit ochiq sahifada yo'q", upub.get("away_limit"), None)
r = begin(UTOK, "Mehmon Telefon", IPHONE)
ck("unit: iPhone bilan /begin 200", r.status_code, 200)
KU = r.json()["key"]
res = [away(UTOK, KU).get("expelled") for _ in range(5)]
ck("unit: 5 marta — chetlatilmadi", res, [None] * 5)
ck("unit: 6-chisida chetlatildi", away(UTOK, KU).get("expelled"), True)
ck("unit: izoh o'zgarmagan", sub_of(KU)[1], "Sahifadan 6 marta chiqdi (ruxsat: 5)")
d = SessionLocal()
o = d.query(models.ExamOnline).filter_by(exam_id=UEID).first()
o.away_limit = None
d.commit()
d.close()
KU2 = begin(UTOK, "Mehmon Android", ANDROID).json()["key"]
res = [away(UTOK, KU2, "tab").get("expelled") for _ in range(8)]
ck("unit: chegara yo'q — 8 marta ham chetlatilmaydi", res, [None] * 8)
j = away(UTOK, KU2)
ck("unit: chegara yo'q — left None", (j.get("away_limit"), j.get("left")), (None, None))
r = client.post(f"/api/public/exam/{UTOK}/submit", headers=IPHONE, json={
    "photo": PHOTO, "name": "Mehmon Eski", "answers": {}})
ck("unit: kalitsiz eski /submit telefondan ham 200", r.status_code, 200)

# ------------------------------------------------------------------ F
print("\n=== F. JONY STUDENT ILOVASIDA MOCK ===")
st = client.get(f"/api/student/exam/{MTOK}", headers=HS).json()
ck("ilova: strict=true, chegara 2", (st.get("strict"), st.get("away_limit")), (True, 2))
r = client.post(f"/api/student/exam/{MTOK}/begin", headers={**HS, **IPHONE},
                json={"photo": PHOTO})
ck("ilova: iPhone /begin 403", r.status_code, 403)
r = client.post(f"/api/student/exam/{MTOK}/begin", headers={**HS, **DESKTOP},
                json={"photo": PHOTO})
ck("ilova: kompyuter /begin 200", r.status_code, 200)
# Unit test ilovada — strict yo'q (o'quvchi Step guruhida emas, shuning
# uchun faqat ochiq sahifa tekshirildi, E ga qarang)

# ------------------------------------------------------------------ G
print("\n=== G. XODIM MOCK SINOVI ===")
cat = client.get("/api/mock-practice/catalog", headers=H).json()
CK = [v["content_key"] for bk in cat["banks"] for sct in bk["sections"]
      for v in sct["variants"]][0]
r = client.post("/api/mock-practice", headers={**H, **IPHONE},
                json={"content_key": CK})
ck("iPhone: POST /api/mock-practice 403", r.status_code, 403)
ck("iPhone: xabar", r.json().get("detail"), "Mock test faqat kompyuterda ishlanadi")
r = client.post("/api/mock-practice", headers={**H, **ANDROID},
                json={"content_key": CK})
ck("Android: 403", r.status_code, 403)
r = client.post("/api/mock-practice", headers={**H, **DESKTOP},
                json={"content_key": CK})
ck("kompyuter: 200", r.status_code, 200)

# ------------------------------------------------------------------ H
print("\n=== H. MOCK: CHETLATILGAN QAYTA KIRA OLMAYDI (maxfiy oyna) ===")
MEID3 = make_exam(GI, "mock")
T3 = open_link(MEID3, MOCK_TPL)["token"]
r = begin_id(T3, SID)
ck("ro'yxatdan tanladi: /begin 200", r.status_code, 200)
KA = r.json()["key"]
r = begin_id(T3, SID)
ck("ikkinchi brauzerda o'sha ism: 409, kalit berilmaydi",
   (r.status_code, "key" in r.json()), (409, False))
res = [away(T3, KA, "blur").get("expelled") for _ in range(3)]
ck("3-chisida chetlatildi", res, [None, None, True])
r = begin_id(T3, SID)
ck("chetlatilgandan keyin /begin 403", r.status_code, 403)
ck("xabar", r.json().get("detail"), "Siz bu testdan chetlatilgansiz")
r = begin(T3, "aliyev  ali")
ck("ismini yozib ham (ro'yxatga mos) 403", r.status_code, 403)
r = client.post(f"/api/public/exam/{T3}/submit", headers=DESKTOP, json={
    "photo": PHOTO, "student_id": SID, "answers": {}})
ck("kalitsiz eski /submit ham 403", r.status_code, 403)
subs = client.get(f"/api/exams/{MEID3}/online", headers=HE).json()["submissions"]
ck("natija yozilmadi — faqat bitta (expelled) yozuv",
   sorted(x["status"] for x in subs if x["student_id"] == SID or
          x["typed_name"] == "Aliyev Ali"), ["expelled"])
r = begin(T3, "Mehmon Yangi")
ck("ro'yxatda yo'q ism — avvalgidek kiradi", r.status_code, 200)
# Examiner eski yozuvni rad etsa — qayta kira oladi (kompyuter buzilgan)
KB = begin_id(on2["token"], SID).json()["key"]
sub_b = [x for x in client.get(f"/api/exams/{MEID2}/online", headers=HE)
         .json()["submissions"] if x["student_id"] == SID]
client.post(f"/api/exam-submissions/{sub_b[0]['id']}/reject", headers=HE)
ck("rad etilgandan keyin qayta kira oladi", begin_id(on2["token"], SID).status_code, 200)
# Unit test — avvalgidek: ikkinchi marta kirish mumkin
UEID2 = make_exam(GS, "unit", unit_no=1)
UT2 = open_link(UEID2, UNIT_TPL)["token"]
ck("unit: 1-kirish 200", begin_id(UT2, SVID).status_code, 200)
ck("unit: 2-kirish ham 200 (bugungidek)", begin_id(UT2, SVID).status_code, 200)

# ------------------------------------------------------------------ I
print("\n=== I. TAKROR YUBORISH, DAVOMI, TO'LIQ EKRAN BELGISI ===")
K4 = begin(on2["token"], "Mehmon Beshinchi").json()["key"]
j = away2(on2["token"], K4, reason="blur", seconds=10, eid="ab-1")
ck("1-chiqish (eid): yana 1", (j.get("away_count"), j.get("left")), (1, 1))
j = away2(on2["token"], K4, reason="blur", seconds=10, eid="ab-1")
ck("o'sha eid qayta: sanalmadi",
   (j.get("away_count"), j.get("duplicate"), j.get("expelled")), (1, True, None))
j = away2(on2["token"], K4, reason="blur", seconds=890, eid="ab-1+", extend=True)
ck("davomi (extend): soni o'zgarmadi", (j.get("away_count"), j.get("left")), (1, 1))
ck("davomi: away_sec 900", sec_of(K4), 900)
away2(on2["token"], K4, reason="blur", seconds=890, eid="ab-1+", extend=True)
ck("davomi qayta yuborildi: away_sec baribir 900", sec_of(K4), 900)
j = away2(on2["token"], K4, reason="fullscreen", eid="nofs-x", flag="nofs")
ck("to'liq ekran belgisi: sanalmadi", j.get("away_count"), 1)
live = [x for x in client.get(f"/api/exams/{MEID2}/online", headers=HE)
        .json()["online"]["live"] if x["name"] == "Mehmon Beshinchi"]
ck("examiner jonli ro'yxatda ko'radi", live[0].get("note"),
   exam_online.NOFS_NOTE)
j = away2(on2["token"], K4, reason="tab", seconds=2, eid="ab-2")
ck("2-chiqish: yana 0", j.get("left"), 0)
j = away2(on2["token"], K4, reason="printscreen", seconds=1, eid="ab-3")
ck("3-chiqish: chetlatildi", j.get("expelled"), True)
ck("izohda oxirgi sabab", "ekran rasmini" in sub_of(K4)[1], True)

db.close()
print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
