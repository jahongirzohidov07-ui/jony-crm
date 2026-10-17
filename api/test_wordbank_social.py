"""LUG'AT BANKI — "So'z bilish" reytingi, TARIX, ustoz va ota-ona
(2026-10-17, 2–3-bosqich; Jahongir, OWNER_DECISIONS D2–D5).

Tekshiriladi (scratchpad/vocab/PHASE23_CONTRACT.md §2, §4, §5):
  * ismlar yashiriladi ("Bobur A."), o'zingiz — "Siz", familiya javobda yo'q;
  * Jami/Shu hafta — faqat faol va sinovdagilar; yoqilmagan filial yo'q;
  * guruh kesimi: asosiy guruh + ochiq StudentGroupLink (yopiq bog'lanish
    hisobga olinmaydi), 2+ guruh — tanlagich, begona guruh — 403;
  * hafta chegarasi — Toshkent dushanbasi 00:00 (naive UTC 19:00 yakshanba);
  * teng natija: erta erishgan, keyin kichik id;
  * TOP 50 dan tashqaridagi o'z qatori va "keyingi o'ringa N ta so'z";
  * faqat TASDIQLANGAN sertifikat belgisi (kutilayotgan ball hech qayerda);
  * "tekshirilmoqda" — haftalik o'sish yoki shubhali P ulushi (faqat belgi);
  * Tarix: arxiv / ketgan / muzlatilgan (bitirgan / ketgan), butunlay
    o'chirilgan o'quvchi (delete_student) — eng yaxshi natija va daraja
    saqlanadi; import-undo o'chirgani — hidden=1, ko'rinmaydi;
  * o'chirish band awards va sertifikat yuklamalarini qoldiradi, FK xatosiz;
  * birlashtirish: kuchli so'z holati qoladi, daraja takrorsiz, ikki marta
    to'langan coin -N bilan qaytariladi, tarix maksimumlari;
  * refresh_hall eng yaxshi natijani hech qachon pasaytirmaydi;
  * ota-ona: kutilayotgan ball yo'q; ustoz: begona guruh — 403;
  * /me: ranks, best_known, certs (faqat tasdiqlangan), certs_pending (son).
  2026-10-17 (review): import-undo so'z mashqi qilganni himoya qiladi;
  faol guruhsiz o'chirilgan o'quvchi guruh Tarix idan tushmaydi (oxirgi
  yopiq guruhi); qaytib kelib bitirgan — "bitirgan"; ranks_for 0 so'zda
  umumiy hisobni chaqirmaydi.

Ishga tushirish: PYTHONIOENCODING=utf-8 python test_wordbank_social.py
"""
import json
import os
import sys
from datetime import date, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_wordbank_social/db.sqlite"
os.makedirs("/tmp/verify_wordbank_social", exist_ok=True)
if os.path.exists("/tmp/verify_wordbank_social/db.sqlite"):
    os.remove("/tmp/verify_wordbank_social/db.sqlite")
# Startdagi so'z seedi haqiqiy words.json ni yuklamasin
os.environ["WORDBANK_WORDS_FILE"] = "/tmp/verify_wordbank_social/yoq.json"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
import main, models, roles  # noqa: E402,F401
import entry  # noqa: E402,F401 - jonli yo'llar (parent_view) va yamoqlar
import common as _cm  # noqa: E402
import wordbank as WB  # noqa: E402
import wordbank_social as WSOC  # noqa: E402
from database import SessionLocal  # noqa: E402
from auth import hash_password  # noqa: E402

# Login oylik yechimni ishga tushiradi — bu test unga bog'liq emas
_cm._ensure_month_charges = lambda db, **kw: None

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def ckt(name, cond):
    ck(name, bool(cond), True)


# ---- Soxta soat (sys.modules bo'ylab — entry-monkeypatch-pitfall) ----
# 2026-10-14 chorshanba, 07:00 UTC = Toshkent 12:00. Hafta boshi —
# dushanba 2026-10-12 00:00 Toshkent = 2026-10-11 19:00 UTC.
CLOCK = {"t": datetime(2026, 10, 14, 7, 0, 0)}
WS_UTC = datetime(2026, 10, 11, 19, 0, 0)


def _fake_now():
    return CLOCK["t"]


for _m in list(sys.modules.values()):
    _f = getattr(_m, "__file__", "") or ""
    if _f.endswith("wordbank.py"):
        if hasattr(_m, "_now"):
            _m._now = _fake_now
        if hasattr(_m, "BAND_SIZE"):
            _m.BAND_SIZE = 3
    if _f.endswith("wordbank_social.py") and hasattr(_m, "AGG_TTL"):
        _m.AGG_TTL = 0                       # kesh o'chiq (jonli hisob)


def set_social(name, value):
    for _m in list(sys.modules.values()):
        if (getattr(_m, "__file__", "") or "").endswith("wordbank_social.py") \
                and hasattr(_m, name):
            setattr(_m, name, value)


# ------------------------------------------------------------ ma'lumot ---
db = SessionLocal()
bA = models.Branch(name="Zafar")
bB = models.Branch(name="Yunusobod")
bC = models.Branch(name="Yopiq")
db.add_all([bA, bB, bC])
db.commit()
BA_, BB_, BC_ = bA.id, bB.id, bC.id


def mk_user(uname, role, branch_id, full=None):
    u = models.User(username=uname, full_name=full or uname.title(),
                    password_hash=hash_password("Parol123!"), role=role,
                    branch_id=branch_id, is_active=1)
    db.add(u)
    db.commit()
    return u


uT1 = mk_user("wsteach1", roles.TEACHER, BA_, "Ustoz Bir")
uT2 = mk_user("wsteach2", roles.TEACHER, BA_, "Ustoz Ikki")
mk_user("wsboss", roles.FOUNDER, BA_)
T1 = models.Teacher(full_name="Ustoz Bir", branch_id=BA_, user_id=uT1.id)
T2 = models.Teacher(full_name="Ustoz Ikki", branch_id=BA_, user_id=uT2.id)
db.add_all([T1, T2])
db.commit()


def mk_group(name, branch_id, teacher=None):
    g = models.Group(name=name, branch_id=branch_id,
                     teacher_id=teacher.id if teacher else None,
                     lesson_price=60000, standard_lessons_per_month=8,
                     monthly_fee=480000)
    db.add(g)
    db.commit()
    return g.id


G1 = mk_group("IELTS 6.0", BA_, T1)
G2 = mk_group("Speaking", BA_, T2)
G3 = mk_group("Yunusobod A", BB_)
GU = mk_group("Xato import", BA_, T1)
GC = mk_group("Yopiq guruh", BC_)

SEQ = {"n": 0}


def mk_student(name, branch_id, group_id=None, status="active", login=None,
               phone=None):
    SEQ["n"] += 1
    uid = None
    if login:
        uid = mk_user(login, roles.STUDENT, branch_id, name).id
    s = models.Student(full_name=name, branch_id=branch_id, status=status,
                       group_id=group_id, enrolled_date=date(2026, 9, 1),
                       public_id=f"STU-WS-{SEQ['n']}", user_id=uid,
                       phone=phone)
    db.add(s)
    db.commit()
    if group_id:
        db.add(models.StudentGroupLink(student_id=s.id, group_id=group_id,
                                       is_primary=1, active=1))
        db.commit()
    return s.id


ME = mk_student("Aziz Karimov", BA_, G1, login="wsme")
db.add(models.StudentGroupLink(student_id=ME, group_id=G2, is_primary=0,
                               active=1))
P1 = mk_student("Bobur Aliyev", BA_, G1)
P2 = mk_student("Dilnoza Rahimova", BA_, G1)
P3 = mk_student("Eldor Sobirov", BA_, G1, status="trial")
P11 = mk_student("Nodir Hamidov", BA_, G1)
P12 = mk_student("Olim Tursunov", BA_, G1)
P13 = mk_student("Laylo Saidova", BA_, G1)
P4 = mk_student("Farrux Nazarov", BA_, G1, status="frozen")
P5 = mk_student("Gulnora Tosheva", BA_, G1, status="left")
P9 = mk_student("Jasur Ergashev", BA_, G1, status="archived")
PDEL = mk_student("Kamola Yusupova", BA_, G1, status="archived")
P6 = mk_student("Hasan Usmonov", BA_, G2)
db.add(models.StudentGroupLink(student_id=P6, group_id=G1, is_primary=0,
                               active=0))          # YOPIQ bog'lanish
PUNDO = mk_student("Umid Xatolik", BA_, GU)
P7 = mk_student("Ilhom Qodirov", BB_, G3)
P8 = mk_student("Yopiq Filialdagi", BC_, GC, login="wsoff")
MK = mk_student("Sardor Mirzayev", BB_, phone="+998901112233")
MD = mk_student("Sardor Mirzayev", BB_, phone="+998901112233")
PZ = mk_student("Zarina Guruhsiz", BA_, login="wsz")
FILLERS = [mk_student(f"Filler{i} Test", BB_) for i in range(52)]
db.commit()

# ---- So'zlar: 1- va 2-daraja 3 tadan (to'liq, BAND_SIZE=3), 5-daraja 250
for i in range(3):
    db.add(models.WordbankWord(rank=1 + i, band=1, lemma=f"one{i}",
                               uz_primary=f"bir{i}", uz_alt="[]"))
    db.add(models.WordbankWord(rank=1001 + i, band=2, lemma=f"two{i}",
                               uz_primary=f"ikki{i}", uz_alt="[]"))
for i in range(250):
    db.add(models.WordbankWord(rank=4001 + i, band=5, lemma=f"five{i}",
                               uz_primary=f"besh{i}", uz_alt="[]"))
db.commit()
B1 = [w.id for w in db.query(models.WordbankWord).filter_by(band=1)
      .order_by(models.WordbankWord.rank)]
B2 = [w.id for w in db.query(models.WordbankWord).filter_by(band=2)
      .order_by(models.WordbankWord.rank)]
B5 = [w.id for w in db.query(models.WordbankWord).filter_by(band=5)
      .order_by(models.WordbankWord.rank)]


def give(sid, items, stage=4):
    """items: [(word_id, known_at)] — tasdiqlangan so'zlar."""
    for wid, at in items:
        db.add(models.WordbankStudentWord(
            student_id=sid, word_id=wid, stage=stage, known=1, known_at=at,
            has_prod=1, lapses=0, last_move=at.date(),
            due=at.date() + timedelta(days=30), created_at=at))
    db.commit()


def at(*a):
    return datetime(*a)


# Men (10 ta): hafta ichida 4 tasi — aynan 19:00:00 UTC chegarasi ham
give(ME, [(w, at(2026, 10, 5, 8)) for w in B1]
     + [(B2[0], at(2026, 10, 11, 18, 59, 59)),      # yakshanba 23:59:59
        (B2[1], at(2026, 10, 11, 19, 0, 0)),         # dushanba 00:00:00
        (B2[2], at(2026, 10, 12, 10))]
     + [(B5[0], at(2026, 10, 1)), (B5[1], at(2026, 10, 1)),
        (B5[2], at(2026, 10, 13, 9)), (B5[3], at(2026, 10, 14, 6))])
give(P1, [(w, at(2026, 10, 1, 10)) for w in B5[:25]]
     + [(w, at(2026, 10, 13, 8)) for w in B5[25:30]])
give(P2, [(w, at(2026, 9, 30, 10)) for w in B5[:30]])
for sid in (P3, P11):                 # bir xil son, bir xil vaqt — id hal qiladi
    give(sid, [(w, at(2026, 10, 2, 9)) for w in B5[:17]]
         + [(w, at(2026, 10, 12, 12)) for w in B5[17:20]])
give(P12, [(w, at(2026, 10, 1)) for w in B5[:2]])
give(P13, [(B5[0], at(2026, 10, 1))])
give(P4, [(w, at(2026, 10, 1)) for w in B5[:100]])
give(P5, [(w, at(2026, 9, 1)) for w in B5[:80]])
give(P9, [(w, at(2026, 9, 1)) for w in B5[:50]])
give(PDEL, [(w, at(2026, 9, 20)) for w in B5[:70]])
give(P6, [(w, at(2026, 10, 1)) for w in B5[:12]])
give(PUNDO, [(w, at(2026, 10, 1)) for w in B5[:40]])
give(P7, [(w, at(2026, 10, 1)) for w in B5[:200]])
give(P8, [(w, at(2026, 10, 1)) for w in B5[:240]])
for i, sid in enumerate(FILLERS):
    give(sid, [(w, at(2026, 10, 1) + timedelta(minutes=i)) for w in B5[:11]])

# Ketish sabablari: Gulnora — bitirdi; Jasur — avval "finished", keyin
# "price" (oxirgisi hisob); Kamola — bitirdi
LR = models.LeaveReason
db.add_all([
    LR(student_id=P5, reason="finished", created_at=at(2026, 9, 10)),
    LR(student_id=P9, reason="finished", created_at=at(2026, 9, 1)),
    LR(student_id=P9, reason="price", created_at=at(2026, 9, 20)),
    LR(student_id=PDEL, reason="finished", created_at=at(2026, 9, 25)),
])
# Kamolaning 1-darajasi (eng birinchi tugatgan) va tasdiqlangan sertifikati
db.add(models.WordbankBandAward(student_id=PDEL, band=1, coins=1,
                                awarded_at=at(2026, 10, 2, 5)))
CU = models.WordbankCertUpload
db.add_all([
    CU(student_id=P1, exam_type="ielts", result_label="IELTS 7.0",
       score=7.0, status="confirmed", test_date=date(2026, 5, 1),
       reviewed_at=at(2026, 6, 1), created_at=at(2026, 5, 20)),
    CU(student_id=P1, exam_type="ielts", result_label="IELTS 8.5",
       score=8.5, status="pending", test_date=date(2026, 9, 1),
       created_at=at(2026, 10, 10)),
    CU(student_id=P2, exam_type="ielts", result_label="IELTS 8.0",
       score=8.0, status="rejected", test_date=date(2026, 9, 1),
       created_at=at(2026, 10, 10)),
    CU(student_id=ME, exam_type="ielts", result_label="IELTS 6.5",
       score=6.5, status="pending", test_date=date(2026, 9, 15),
       created_at=at(2026, 10, 12)),
    CU(student_id=ME, exam_type="sat", result_label="SAT 1350",
       score=1350, status="confirmed", test_date=date(2026, 3, 1),
       reviewed_at=at(2026, 4, 1), created_at=at(2026, 3, 20)),
    CU(student_id=PDEL, exam_type="duolingo", result_label="Duolingo 125",
       score=125, status="confirmed", test_date=date(2026, 6, 1),
       reviewed_at=at(2026, 6, 5), created_at=at(2026, 6, 2)),
])
# Hajm testi (men): oxirgisi — 4200
db.add_all([
    models.WordbankSizeTest(student_id=ME, estimate=3000, low=2600,
                            high=3400, created_at=at(2026, 10, 1)),
    models.WordbankSizeTest(student_id=ME, estimate=4200, low=3800,
                            high=4600, created_at=at(2026, 10, 10)),
])
db.commit()


def p_answers(sid, n, suspect):
    sess = models.WordbankSession(student_id=sid, kind="practice",
                                  created_at=at(2026, 10, 13, 8))
    db.add(sess)
    db.flush()
    for i in range(n):
        db.add(models.WordbankSessionItem(
            session_id=sess.id, student_id=sid, word_id=B5[i], seq=i,
            band=5, mode="P", expected="x", given="y", correct=0,
            suspect=1 if i < suspect else 0, asked_at=at(2026, 10, 13, 8),
            answered_at=at(2026, 10, 13, 8, 1)))
    db.commit()


p_answers(P12, 25, 10)     # 40% shubhali, 25 ta — "tekshirilmoqda"
p_answers(P13, 10, 5)      # 50%, lekin atigi 10 ta — belgi yo'q

st_me = db.query(models.Student).get(ME)
st_me.parent_token = "parent-token-me-0001"
db.query(models.Student).get(P8).parent_token = "parent-token-off-0001"
db.commit()


def set_flag(value):
    d = SessionLocal()
    row = d.query(models.IntegrationSetting).get("wordbank_branches")
    if row is None:
        row = models.IntegrationSetting(key="wordbank_branches")
        d.add(row)
    row.value = value
    d.commit()
    d.close()


def H(uname):
    r = client.post("/api/auth/login",
                    json={"username": uname, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


HME, HZ, HOFF = H("wsme"), H("wsz"), H("wsoff")
HT1, HT2, HF = H("wsteach1"), H("wsteach2"), H("wsboss")
LB = "/api/wordbank/leaderboard"


def board(params, h=HME):
    r = client.get(LB, params=params, headers=h)
    return r


SURNAMES = ["Karimov", "Aliyev", "Rahimova", "Sobirov", "Hamidov",
            "Tursunov", "Saidova", "Nazarov", "Tosheva", "Ergashev",
            "Yusupova", "Usmonov", "Xatolik", "Qodirov", "Filialdagi",
            "Mirzayev", "Guruhsiz"]


def no_surnames(name, payload):
    blob = json.dumps(payload, ensure_ascii=False)
    hit = [x for x in SURNAMES if x in blob]
    ck(f"{name}: to'liq familiya yo'q", hit, [])
    ck(f"{name}: rasm maydoni yo'q", '"photo"' in blob, False)


print("\n=== 1. DARVOZA ===")
ck("bayroq o'chiq: 404", board({}).status_code, 404)
set_flag(json.dumps([BA_, BB_]))
ck("yoqilmagan filial o'quvchisi: 404", board({}, HOFF).status_code, 404)
ck("noto'g'ri scope: 400", board({"scope": "class"}).status_code, 400)
ck("noto'g'ri period: 400", board({"period": "month"}).status_code, 400)
ck("begona guruh: 403", board({"group_id": G3}).status_code, 403)
ck("group_id matn: 400", board({"group_id": "abc"}).status_code, 400)
ck("ortiqcha branch_id parametri e'tiborsiz: 200",
   board({"branch_id": BB_}).status_code, 200)

print("\n=== 2. /me: DARAJA COINI TARIXGA YOZILADI, RANKS, SERTIFIKATLAR ===")
r = client.get("/api/wordbank/me", headers=HME)
ck("/me 200", r.status_code, 200)
me = r.json()
ck("/me known", me["known"], 10)
ck("/me: 1- va 2-daraja tugadi (o'z-o'zini tiklash)",
   [b["done"] for b in me["bands"][:2]], [True, True])
ck("/me ranks (guruh 5, filial 7, markaz 60)", me["ranks"],
   {"group": 5, "branch": 7, "school": 60})
ck("/me best_known", me["best_known"], 10)
ck("/me certs — faqat tasdiqlangan",
   [c["label"] for c in me["certs"]], ["SAT 1350"])
ck("/me certs_pending — faqat son", me["certs_pending"], 1)
ck("/me: kutilayotgan ball (6.5) yo'q", "6.5" in json.dumps(me), False)
h = db.query(models.WordbankHall).filter_by(student_ref=ME).first()
ckt("tarix qatori yaratildi (daraja coini paytida)", h is not None)
ck("tarix: best 10, bands 2 (mask 0b11), badge, guruh",
   (h.best_known, h.bands_done, h.bands_mask, h.cert_badge, h.group_id,
    h.status_snap, h.hidden),
   (10, 2, 3, "SAT 1350", G1, "active", 0))

print("\n=== 3. JAMI — GURUH: NIQOB, HOLAT, TENGLIK, BELGILAR ===")
r = board({"scope": "group", "period": "total"})
d = r.json()
ck("guruh: 200", r.status_code, 200)
ck("guruh tanlagichi (asosiy birinchi)",
   [g["id"] for g in d["groups"]], [G1, G2])
ck("guruh_id", d["group_id"], G1)
ck("hafta boshi — Toshkent dushanbasi", d["week_start"], "2026-10-12")
ck("qatorlar: ism, son (teng: erta erishgan, keyin kichik id)",
   [(x["rank"], x["name"], x["known"]) for x in d["rows"]],
   [(1, "Dilnoza R.", 30), (2, "Bobur A.", 30), (3, "Eldor S.", 20),
    (4, "Nodir H.", 20), (5, "Siz", 10), (6, "Olim T.", 2),
    (7, "Laylo S.", 1)])
ck("muzlatilgan / ketgan / arxiv yo'q (faqat active, trial)",
   {x["name"] for x in d["rows"]} & {"Farrux N.", "Gulnora T.", "Jasur E.",
                                    "Kamola Y."}, set())
ck("yopiq bog'lanish (Hasan) guruhda yo'q",
   "Hasan U." in [x["name"] for x in d["rows"]], False)
ck("bosh harflar", d["rows"][0]["initials"], "DR")
ck("guruh va filial nomi", (d["rows"][0]["group"], d["rows"][0]["branch"]),
   ("IELTS 6.0", "Zafar"))
ck("faqat tasdiqlangan belgi (Bobur: IELTS 7.0, 8.5 emas)",
   d["rows"][1]["cert_badge"], "IELTS 7.0")
ck("rad etilgan belgi yo'q (Dilnoza)", d["rows"][0]["cert_badge"], None)
ck("o'z qatori: Siz, SAT 1350, is_me",
   (d["me"]["name"], d["me"]["rank"], d["me"]["cert_badge"],
    d["me"]["is_me"], d["me"]["bands_done"]),
   ("Siz", 5, "SAT 1350", True, 2))
ck("keyingi o'ringa (20 - 10 + 1)", d["gap_to_next"], 11)
ck("jami reytingda", d["total"], 7)
ck("tekshirilmoqda: 25 P dan 40% shubhali — Olim",
   [x["name"] for x in d["rows"] if x["flagged"]], ["Olim T."])
ck("label va first_finishers jami da yo'q",
   ({x["label"] for x in d["rows"]}, d["first_finishers"]), ({None}, []))
blob = json.dumps(d)
ck("kutilayotgan ball (8.5, 6.5) reytingda yo'q",
   ("8.5" in blob, "6.5" in blob), (False, False))
no_surnames("guruh reytingi", d)

print("\n=== 4. 2-GURUH (ochiq bog'lanish), FILIAL, MARKAZ ===")
d = board({"scope": "group", "group_id": G2}).json()
ck("Speaking: Hasan + men (bog'lanish orqali)",
   [(x["rank"], x["name"], x["known"]) for x in d["rows"]],
   [(1, "Hasan U.", 12), (2, "Siz", 10)])
d = board({"scope": "branch"}).json()
ck("filial: o'rnim 7, jami 9", (d["me"]["rank"], d["total"]),
   (7, 9))
ckt("filial: boshqa filialdagilar yo'q",
    all(x["branch"] == "Zafar" for x in d["rows"]))
d = board({"scope": "school"}).json()
ck("markaz: TOP 50 qator", len(d["rows"]), 50)
ck("markaz: o'z qatori TOP 50 dan tashqarida — o'rin 60",
   (d["me"]["rank"], d["me"]["name"], d["me"]["known"]), (60, "Siz", 10))
ck("markaz: o'zim ro'yxat ichida emas",
   any(x["is_me"] for x in d["rows"]), False)
ck("markaz: keyingi o'ringa (11 - 10 + 1)", d["gap_to_next"], 2)
ck("markaz: yopiq filial (240 so'z) yo'q",
   d["rows"][0]["known"], 200)
ck("markaz: jami (o'zimdan keyin Olim va Laylo)", d["total"], 62)
no_surnames("markaz reytingi", d)

print("\n=== 5. SHU HAFTA — CHEGARA VA TENGLIK ===")
d = board({"scope": "group", "period": "week"}).json()
ck("hafta: (o'rin, ism, o'sish)",
   [(x["rank"], x["name"], x["week_gain"]) for x in d["rows"]],
   [(1, "Bobur A.", 5), (2, "Siz", 4), (3, "Eldor S.", 3),
    (4, "Nodir H.", 3)])
ck("hafta: dushanba 00:00 kiradi, yakshanba 23:59:59 kirmaydi",
   d["me"]["week_gain"], 4)
ck("hafta: Siz — umumiy son ham ko'rinadi", d["me"]["known"], 10)
ck("hafta: keyingi o'ringa (5 - 4 + 1)", d["gap_to_next"], 2)
set_social("FLAG_WEEK_GAIN", 4)
d = board({"scope": "group", "period": "week"}).json()
ck("hafta o'sishi chegaradan katta — belgi (faqat ko'rsatish)",
   [x["name"] for x in d["rows"] if x["flagged"]], ["Bobur A."])
set_social("FLAG_WEEK_GAIN", 550)
CLOCK["t"] = datetime(2026, 10, 11, 18, 0, 0)     # yakshanba 23:00 Toshkent
d = board({"scope": "group", "period": "week"}).json()
ck("o'tgan hafta: boshqa hafta boshi", d["week_start"], "2026-10-05")
CLOCK["t"] = datetime(2026, 10, 14, 7, 0, 0)

print("\n=== 6. GURUHSIZ O'QUVCHI ===")
d = board({"scope": "group"}, HZ).json()
ck("guruhsiz: bo'sh ro'yxat va izoh",
   (d["rows"], d["hint"], d["me"]["name"], d["groups"]),
   ([], "Siz hali guruhga biriktirilmagansiz.", "Siz", []))

print("\n=== 7. KESH: o'z qatori jonli ===")
set_social("AGG_TTL", 60)
WSOC.clear_cache()
d1 = board({"scope": "school"}).json()
give(P7, [(B5[200], at(2026, 10, 14, 6, 30))])
give(ME, [(B5[4], at(2026, 10, 14, 6, 31))])
d2 = board({"scope": "school"}).json()
ck("keshda boshqalar eski (60 s)", d2["rows"][0]["known"], 200)
ck("o'z qatori darhol yangilandi", d2["me"]["known"], 11)
set_social("AGG_TTL", 0)
WSOC.clear_cache()
ck("kesh o'chgach jonli", board({"scope": "school"}).json()["rows"][0]
   ["known"], 201)
db.query(models.WordbankStudentWord).filter_by(
    student_id=ME, word_id=B5[4]).delete()
db.query(models.WordbankStudentWord).filter_by(
    student_id=P7, word_id=B5[200]).delete()
db.commit()

print("\n=== 8. refresh_hall HECH QACHON PASAYTIRMAYDI ===")
for wid in B5[:2]:
    sw = (db.query(models.WordbankStudentWord)
          .filter_by(student_id=ME, word_id=wid).first())
    sw.known, sw.known_at = 0, None
db.commit()
WSOC.refresh_hall(db, ME)
db.commit()
db.expire_all()
h = db.query(models.WordbankHall).filter_by(student_ref=ME).first()
ck("jonli 8, tarix 10 qoladi", h.best_known, 10)
d = client.get("/api/wordbank/me", headers=HME).json()
ck("/me: known 8, best_known 10", (d["known"], d["best_known"]), (8, 10))
for wid in B5[:2]:
    sw = (db.query(models.WordbankStudentWord)
          .filter_by(student_id=ME, word_id=wid).first())
    sw.known, sw.known_at = 1, at(2026, 10, 1)
db.commit()
# Bekor qilish (sertifikatlar moduli shunday chaqiradi): holat hali
# flush qilinmagan — refresh_hall o'zi flush qiladi (autoflush=False)
u_sat = db.query(CU).filter_by(student_id=ME, exam_type="sat").first()
u_sat.status = "revoked"
h = WSOC.refresh_hall(db, ME)
ck("bekor qilingan sertifikat tarix belgisidan tushadi", h.cert_badge, None)
db.rollback()                       # tajriba — hech narsa saqlanmaydi
db.expire_all()
ck("rollback: belgi joyida",
   db.query(models.WordbankHall).filter_by(student_ref=ME).first()
   .cert_badge, "SAT 1350")

print("\n=== 9. OTA-ONA: FAQAT TASDIQLANGAN ===")
r = client.get("/api/parent/parent-token-me-0001")
ck("ota-ona 200", r.status_code, 200)
pw = r.json().get("wordbank")
ck("ota-ona: wordbank",
   pw and (pw["known"], pw["best"], pw["bands_done"], pw["rank_group"],
           pw["rank_branch"], [c["label"] for c in pw["certs"]]),
   (10, 10, 2, 5, 7, ["SAT 1350"]))
# (sahifaning boshqa qismida "~6.0-6.5" daraja jadvali bor — shuning
# uchun butun matnda yorliq, wordbank bo'limida esa son ham tekshiriladi)
ck("ota-ona: kutilayotgan natija yo'q",
   ("IELTS 6.5" in r.text, "6.5" in json.dumps(pw)), (False, False))
r = client.get("/api/parent/parent-token-off-0001")
ck("ota-ona: yopiq filial — wordbank null",
   (r.status_code, r.json().get("wordbank")), (200, None))

print("\n=== 10. USTOZ RO'YXATI ===")
TS = "/api/wordbank/teacher/students"
r = client.get(TS, params={"group_id": G2}, headers=HT1)
ck("boshqa ustozning guruhi: 403", r.status_code, 403)
ck("o'quvchi: 403",
   client.get(TS, params={"group_id": G1}, headers=HME).status_code, 403)
r = client.get(TS, params={"group_id": G1}, headers=HT1)
ck("o'z guruhi: 200", r.status_code, 200)
t = r.json()
ck("ustoz: faqat active/trial, son bo'yicha",
   [(x["name"], x["known"]) for x in t["students"]],
   [("Bobur Aliyev", 30), ("Dilnoza Rahimova", 30), ("Eldor Sobirov", 20),
    ("Nodir Hamidov", 20), ("Aziz Karimov", 10), ("Olim Tursunov", 2),
    ("Laylo Saidova", 1)])
mine = next(x for x in t["students"] if x["id"] == ME)
ck("ustoz: men — best, hafta, daraja, hajm testi, sertifikat",
   (mine["best"], mine["week_gain"], mine["bands_done"],
    mine["size_test"]["estimate"], mine["size_test"]["date"],
    [c["label"] for c in mine["certs"]]),
   (10, 4, 2, 4200, "2026-10-10", ["SAT 1350"]))
ck("ustoz: Olim — tekshirilmoqda",
   [x["name"] for x in t["students"] if x["flagged"]], ["Olim Tursunov"])
ck("ustoz: kutilayotgan ball yo'q", ("8.5" in r.text, "6.5" in r.text),
   (False, False))
ck("asoschi: yopiq filial guruhi — enabled false",
   (lambda j: (j["enabled"], j["students"]))(
       client.get(TS, params={"group_id": GC}, headers=HF).json()),
   (False, []))
set_flag("")
ck("bayroq o'chiq: ustoz 404",
   client.get(TS, params={"group_id": G1}, headers=HT1).status_code, 404)
set_flag(json.dumps([BA_, BB_]))

print("\n=== 11. TARIX (oldin): arxiv / ketgan / muzlatilgan ===")
d = board({"scope": "group", "period": "history"}).json()
top = [(x["rank"], x["name"], x["known"], x["label"]) for x in d["rows"]]
ck("tarix: eng yaxshi bo'yicha, yorliqlar", top[:5],
   [(1, "Farrux N.", 100, "ketgan"), (2, "Gulnora T.", 80, "bitirgan"),
    (3, "Kamola Y.", 70, "bitirgan"), (4, "Jasur E.", 50, "ketgan"),
    (5, "Dilnoza R.", 30, None)])
ckt("tarix: yopiq bog'lanish ham kiradi (Hasan)",
    "Hasan U." in [x["name"] for x in d["rows"]])
ck("tarix: hafta va belgi yo'q",
   ({x["week_gain"] for x in d["rows"]}, {x["flagged"] for x in d["rows"]}),
   ({0}, {False}))

print("\n=== 12. BUTUNLAY O'CHIRISH: TARIX QOLADI, FK XATOSIZ ===")
r = client.delete(f"/api/students/{PDEL}", headers=HF)
ck("asoschi o'chirdi", r.status_code, 200)
db.expire_all()
ck("o'quvchi yo'q", db.query(models.Student).get(PDEL), None)
h = db.query(models.WordbankHall).filter_by(student_ref=PDEL).first()
ck("tarix qatori: ism, best, daraja, belgi, holat",
   h and (h.name_snap, h.best_known, h.bands_done, h.cert_badge,
          h.status_snap, h.group_id, h.branch_name, h.hidden),
   ("Kamola Yusupova", 70, 1, "Duolingo 125", "finished", G1, "Zafar", 0))
ck("daraja yozuvi qoldi",
   db.query(models.WordbankBandAward).filter_by(student_id=PDEL).count(), 1)
ck("sertifikat yuklamasi qoldi",
   db.query(models.WordbankCertUpload).filter_by(student_id=PDEL).count(), 1)
ck("so'z holatlari tozalandi",
   db.query(models.WordbankStudentWord).filter_by(student_id=PDEL).count(),
   0)
bad = []
for t_ in ("wordbank_student_words", "wordbank_sessions",
           "wordbank_session_items", "wordbank_size_tests",
           "wordbank_hall", "wordbank_band_awards", "wordbank_cert_uploads"):
    bad += list(db.execute(text(f"PRAGMA foreign_key_check({t_})")))
ck("FK buzilishi yo'q", bad, [])

print("\n=== 13. IMPORT-UNDO: so'z mashqi — himoya; bo'sh import — hidden=1 ===")
# 2026-10-17 (review): so'z mashqi qilgan o'quvchi haqiqiy odam — import
# bekor qilinganda o'chirilmaydi (ilgari "tarixsiz" deb o'chirilib,
# natijasi butunlay yashirilardi)
r = client.post("/api/students/import-undo", headers=HF, json={
    "group_id": GU, "mode": "delete", "dry_run": True})
prot = {x["id"]: x["activity"] for x in r.json().get("protected_rows", [])}
ck("dry-run: so'z mashqi qilgan — himoyalangan", prot.get(PUNDO),
   ["so'z mashqi: 40"])
r = client.post("/api/students/import-undo", headers=HF, json={
    "group_id": GU, "ids": [PUNDO], "mode": "delete", "dry_run": False})
ck("himoyalanganni o'chirib bo'lmaydi — 400", r.status_code, 400)
db.expire_all()
ckt("o'quvchi joyida", db.query(models.Student).get(PUNDO) is not None)

# Tarix guruhi (ketgan o'quvchi, faol bog'lanishsiz) va qayta bitirish —
# yangi o'quvchilar PU2 dan OLDIN yaratiladi (SQLite eng katta rowid ni
# qayta ishlatadi — o'chirilgan PU2 ning tarixi ularga o'tib ketmasin)
PGF = mk_student("Gavhar Fayzullayeva", BA_, status="archived")
db.add(models.StudentGroupLink(student_id=PGF, group_id=G2, is_primary=0,
                               active=0, left_date=date(2026, 9, 30)))
db.add(LR(student_id=PGF, reason="finished", group_id=G2,
          created_at=at(2026, 9, 30)))
db.commit()
give(PGF, [(w, at(2026, 9, 15)) for w in B5[:3]])
PLR = mk_student("Lola Qaytganova", BA_, G2)
db.add(LR(student_id=PLR, reason="price", group_id=G2,
          left_date=date(2025, 5, 1), created_at=at(2025, 5, 1)))
db.commit()
give(PLR, [(w, at(2026, 10, 1)) for w in B5[:2]])

# Haqiqiy bo'sh import: so'z mashqi yo'q, lekin eski tarix qatori bor
PU2 = mk_student("Ulugbek Xatoyev", BA_, GU)
db.add(models.WordbankHall(student_ref=PU2, name_snap="Ulugbek Xatoyev",
                           branch_id=BA_, group_id=GU, best_known=7,
                           bands_mask=0, bands_done=0, hidden=0))
db.commit()
r = client.post("/api/students/import-undo", headers=HF, json={
    "group_id": GU, "ids": [PU2], "mode": "delete", "dry_run": False})
ck("bo'sh import o'chirildi", r.status_code, 200)
db.expire_all()
h = db.query(models.WordbankHall).filter_by(student_ref=PU2).first()
ck("tarix qatori bor, lekin yashirin",
   h and (h.best_known, h.hidden), (7, 1))

print("\n=== 14. BIRLASHTIRISH ===")
SWM = models.WordbankStudentWord
X, Y, Z = B5[100], B5[101], B5[102]
db.add_all([
    SWM(student_id=MK, word_id=X, stage=1, known=0, lapses=1,
        last_move=date(2026, 10, 9)),
    SWM(student_id=MD, word_id=X, stage=3, known=1, lapses=2,
        known_at=at(2026, 10, 8), last_move=date(2026, 10, 8)),
    SWM(student_id=MK, word_id=Y, stage=4, known=1, lapses=0,
        known_at=at(2026, 10, 1), last_move=date(2026, 10, 1)),
    SWM(student_id=MD, word_id=Y, stage=2, known=1, lapses=1,
        known_at=at(2026, 10, 2), last_move=date(2026, 10, 9)),
    SWM(student_id=MD, word_id=Z, stage=4, known=1, lapses=0,
        known_at=at(2026, 10, 3), last_move=date(2026, 10, 3)),
])
sess = models.WordbankSession(student_id=MD, kind="practice",
                              created_at=at(2026, 10, 3))
db.add(sess)
db.flush()
db.add(models.WordbankSessionItem(session_id=sess.id, student_id=MD,
                                  word_id=Z, seq=0, band=5, mode="R",
                                  expected="0"))
db.add(models.WordbankSizeTest(student_id=MD, estimate=900, low=700,
                               high=1100, created_at=at(2026, 10, 3)))
CEm = models.CoinEntry
aw_k = models.WordbankBandAward(student_id=MK, band=1, coins=1,
                                awarded_at=at(2026, 10, 5))
aw_d1 = models.WordbankBandAward(student_id=MD, band=1, coins=1,
                                 awarded_at=at(2026, 10, 3))
aw_d2 = models.WordbankBandAward(student_id=MD, band=2, coins=2,
                                 awarded_at=at(2026, 10, 4))
db.add_all([aw_k, aw_d1, aw_d2,
            CEm(student_id=MK, amount=1, source="vocab_band", ref_id=1,
                note="So'z bilish: Common 1000", created_by="Tizim"),
            CEm(student_id=MD, amount=1, source="vocab_band", ref_id=1,
                note="So'z bilish: Common 1000", created_by="Tizim"),
            CEm(student_id=MD, amount=2, source="vocab_band", ref_id=2,
                note="So'z bilish: Common 2000", created_by="Tizim"),
            CU(student_id=MD, exam_type="toefl", result_label="TOEFL 90",
               score=90, status="pending", test_date=date(2026, 9, 1),
               created_at=at(2026, 10, 1)),
            models.WordbankHall(student_ref=MK, best_known=5, bands_mask=1,
                                bands_done=1, hidden=0),
            models.WordbankHall(student_ref=MD, best_known=50, bands_mask=3,
                                bands_done=2, hidden=0,
                                best_at=at(2026, 10, 4))])
db.commit()
AWD1 = aw_d1.id
r = client.post(f"/api/students/{MK}/merge/{MD}", headers=HF)
ck("birlashtirish 200", r.status_code, 200)
moved = r.json().get("moved", {})
ck("moved: so'z holati / birlashdi / coin takror",
   (moved.get("So'z holati"), moved.get("So'z holati (birlashdi)"),
    moved.get("Daraja coini (takror)")), (1, 2, 1))
db.expire_all()
rows = {w.word_id: w for w in db.query(SWM).filter_by(student_id=MK)}
ck("X: kuchlisi (drop) qoldi, lapses yig'indi",
   (rows[X].known, rows[X].stage, rows[X].lapses,
    rows[X].known_at), (1, 3, 3, at(2026, 10, 8)))
ck("Y: kuchlisi (keep, stage 4) qoldi, lapses yig'indi",
   (rows[Y].stage, rows[Y].lapses, rows[Y].last_move),
   (4, 1, date(2026, 10, 1)))
ck("Z: ko'chdi", Z in rows, True)
ck("drop da so'z holati qolmadi",
   db.query(SWM).filter_by(student_id=MD).count(), 0)
aws = {a.band: a for a in
       db.query(models.WordbankBandAward).filter_by(student_id=MK)}
ck("darajalar takrorsiz: 1 (erta — drop qatori), 2",
   (sorted(aws), aws[1].id, aws[1].awarded_at),
   ([1, 2], AWD1, at(2026, 10, 3)))
ck("drop da daraja qolmadi",
   db.query(models.WordbankBandAward).filter_by(student_id=MD).count(), 0)
ce = db.query(CEm).filter_by(student_id=MK, source="vocab_band").all()
ck("coin: jami 1+2 = 3 (takror -1 bilan)", sum(c.amount for c in ce), 3)
ckt("coin: -1 [merge] izohi bilan",
    any(c.amount == -1 and "[merge]" in (c.note or "") for c in ce))
ck("audit: vocab_band [merge] yozuvi",
   db.query(models.AuditLog).filter(
       models.AuditLog.field == "vocab_band",
       models.AuditLog.note.like("[merge]%")).count(), 1)
ck("sessiya, savol, hajm testi ko'chdi",
   (db.query(models.WordbankSession).filter_by(student_id=MK).count(),
    db.query(models.WordbankSessionItem).filter_by(student_id=MK).count(),
    db.query(models.WordbankSizeTest).filter_by(student_id=MK).count()),
   (1, 1, 1))
ck("sertifikat yuklamasi ko'chdi",
   (db.query(CU).filter_by(student_id=MK).count(),
    db.query(CU).filter_by(student_id=MD).count()), (1, 0))
hk = db.query(models.WordbankHall).filter_by(student_ref=MK).all()
ck("tarix: bitta qator, maksimumlar",
   [(x.best_known, x.bands_mask, x.bands_done) for x in hk], [(50, 3, 2)])
ck("tarix: drop qatori yo'q",
   db.query(models.WordbankHall).filter_by(student_ref=MD).count(), 0)
bad = []
for t_ in ("wordbank_student_words", "wordbank_sessions",
           "wordbank_session_items", "wordbank_size_tests",
           "coin_entries"):
    bad += list(db.execute(text(f"PRAGMA foreign_key_check({t_})")))
ck("birlashtirishdan keyin FK buzilishi yo'q", bad, [])

print("\n=== 15. TARIX (keyin): o'chirilgan qoladi, yashirin yo'q ===")
d = board({"scope": "group", "period": "history"}).json()
top = [(x["rank"], x["name"], x["known"], x["label"], x["bands_done"],
        x["cert_badge"]) for x in d["rows"]]
ck("tarix: o'chirilgan Kamola — best 70, 1 daraja, bitirgan, belgi",
   top[2], (3, "Kamola Y.", 70, "bitirgan", 1, "Duolingo 125"))
ck("tarix: o'chirilgan guruh/filial nomi",
   (d["rows"][2]["group"], d["rows"][2]["branch"]), ("IELTS 6.0", "Zafar"))
ck("tarix: o'z qatori", (d["me"]["name"], d["me"]["known"],
                         d["me"]["label"]), ("Siz", 10, None))
ck("birinchi bo'lib tugatganlar",
   [(f["band"], f["name"], f["at"], f["is_me"])
    for f in d["first_finishers"]],
   [(1, "Kamola Y.", "2026-10-02", False), (2, "Siz", "2026-10-14", True)])
d = board({"scope": "school", "period": "history"}).json()
names = [x["name"] for x in d["rows"]]
ck("markaz tarixi: import-undo (yashirin) yo'q",
   "Ulugbek X." in names, False)
ckt("markaz tarixi: himoyalangan (so'z mashqi) o'quvchi bor",
    "Umid X." in names)
ckt("markaz tarixi: o'chirilgan Kamola bor", "Kamola Y." in names)
ck("markaz tarixi: yopiq filial yo'q", "Yopiq F." in names, False)
ck("markaz tarixi: 1-daraja birinchisi — Kamola (02.10)",
   d["first_finishers"][0]["name"], "Kamola Y.")
no_surnames("tarix", d)
d = board({"scope": "branch", "period": "history"}).json()
ckt("filial tarixi: o'chirilgan Kamola (hall.branch_id)",
    "Kamola Y." in [x["name"] for x in d["rows"]])
# Kamola (arxiv) o'chirilgani o'rinni o'zgartirmaydi; Umid (40 so'z) endi
# import-undo dan himoyalangan — oldimda qoladi (2026-10-17, review)
ck("/me ranks (o'chirishdan keyin: filial 7)",
   client.get("/api/wordbank/me", headers=HME).json()["ranks"]["branch"], 7)

print("\n=== 16. TARIX: OXIRGI GURUH VA QAYTA BITIRISH (review) ===")
# Arxivlangan (faol bog'lanishsiz) o'quvchi /me ga kirmagan — tarix
# qatori birinchi marta o'chirish oldidan yoziladi: oxirgi (yopiq) guruhi
r = client.delete(f"/api/students/{PGF}", headers=HF)
ck("ketgan (faol guruhsiz) o'quvchi o'chirildi", r.status_code, 200)
db.expire_all()
h = db.query(models.WordbankHall).filter_by(student_ref=PGF).first()
ck("tarix: oxirgi (yopiq) guruhi yozildi",
   h and (h.best_known, h.group_id, h.group_name, h.status_snap),
   (3, G2, "Speaking", "finished"))
d = board({"scope": "group", "group_id": G2, "period": "history"}).json()
ck("guruh tarixida o'chirilgan o'quvchi — bitirgan",
   [(x["name"], x["label"]) for x in d["rows"] if x["name"] == "Gavhar F."],
   [("Gavhar F.", "bitirgan")])
# Ilgari "narx" sababi bilan ketib, qaytgan o'quvchi endi bitirdi
r = client.post(f"/api/students/{PLR}/remove-from-group", headers=HF,
                json={"reason": "Kursni to'liq tugatdi",
                      "reason_code": "finished"})
ck("qaytgan o'quvchi guruhdan bitirib chiqdi", r.status_code, 200)
db.expire_all()
# Ketish sababi analitikasi o'zgarmaydi: bir o'quvchiga bitta (birinchi)
# yozuv qoladi — eski ketish churn hisobotidan yo'qolmasin (2026-10-17).
ck("ketish sababi yozuvi o'zgarmadi (bitta qator)",
   [x.reason for x in db.query(LR).filter_by(student_id=PLR)], ["price"])
d = board({"scope": "group", "group_id": G2, "period": "history"}).json()
ck("guruh tarixi: o'quvchi tarixda qoladi",
   [x["label"] for x in d["rows"] if x["name"] == "Lola Q."], ["ketgan"])

print("\n=== 17. ranks_for: 0 so'z — umumiy hisobsiz (review, tezlik) ===")
_orig_rows = WSOC._known_rows


def _no_agg(*a, **k):
    raise AssertionError("umumiy hisob chaqirilmasligi kerak")


WSOC._known_rows = _no_agg
try:
    got = WSOC.ranks_for(db, db.query(models.Student).get(PZ), known=0)
except AssertionError as e:
    got = str(e)
WSOC._known_rows = _orig_rows
ck("0 so'z: o'rinlar bo'sh, umumiy hisob yo'q", got,
   {"group": None, "branch": None, "school": None})
ck("ranks_for(known=...) — /me bilan bir xil",
   WSOC.ranks_for(db, db.query(models.Student).get(ME), known=10),
   client.get("/api/wordbank/me", headers=HME).json()["ranks"])

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {len(fails)}"))
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
