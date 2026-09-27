"""XODIMLAR MOCK MASHQI + SAVOL XATOLARI — UCHIDAN UCHIGA (2026-09-27).

Jahongir: "faqat guruhda emas, boshqalar ham o'zi kirib ishlaydigan
bo'lsa yaxshi bo'lardi mock testni xodimlargayam koproq ustozlarga
ular ham experience qilib xatolarni aytadida".

Reja 4-bo'limi (1-11):
  1. Katalog: mazmun bo'yicha bitta (3 daraja nusxasi emas), kalit va
     skript yo'q; o'quvchiga 403.
  2. Boshlash / GET (kalitsiz) / skript (TTS) / audio bo'lim 400 /
     boshqaning urinishi 404; test paytida xabar.
  3. Topshirish: ball, IELTS band, CEFR taxminiy daraja, idempotent.
  4. Kalit himoyasi (ustoz: faqat xato belgilanganlarda, <60% da
     umuman yo'q; examinerlar boshlig'i hammasini ko'radi).
  5. Cheklov: 30 kunda bir (boshqa daraja qatori orqali ham), bir
     vaqtda bitta, examinerga cheklov yo'q, muddat o'tsa avtomat yopiladi.
  6. IZOLYATSIYA: Exam / ExamOnline / ExamSubmission / ExamResult /
     coin / XP soni o'zgarmaydi (oxirida tekshiriladi).
  7. Xabarlar: javobda kalit yo'q, qayta xabar birlashadi, 403 lar,
     kuniga 30 ta (12-bo'limda — hisoblagichlarni buzmasin).
  8. Triage: count, guruhlash, nusxalar = 3, signal, shubhali savol,
     ustozga 403, rad etish butun guruhni yopadi.
  9. Shablon tahriri: daraja nusxalariga ko'chirish (farqlisi
     "diverged"), xabar "fixed", eski snapshot "changed".
 10. Shablonni o'chirish: urinish boshqa nusxaga o'tadi, hech biri
     qolmasa 410.
 11. Statik: MockPractice/MockIssue faqat ruxsat etilgan fayllarda,
     roles.ts == roles.py, TEACHER_MENU va support menyusi, ExamBank.
"""
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta

_DB = os.path.join(tempfile.gettempdir(), "mock_practice_test.db")
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
import mock_practice                               # noqa: E402
from cefr_score import lr_approx                   # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []
TODAY = roles.local_today()


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


def bad_keys(o, bad=("answer", "script")) -> set:
    """Javobda (ichma-ich) taqiqlangan kalitlar."""
    found = set()
    if isinstance(o, dict):
        for k, v in o.items():
            if k in bad:
                found.add(k)
            found |= bad_keys(v, bad)
    elif isinstance(o, list):
        for v in o:
            found |= bad_keys(v, bad)
    return found


# ------------------------------------------------------------------ fixture
db = SessionLocal()
mock_seed.seed_mocks(db)            # haqiqiy mock bazasi (3 daraja nusxa)
b = models.Branch(name="Markaz")
db.add(b)
db.commit()
BID = b.id
USERS = [("asos", "founder", "Asoschi"), ("bosh", "head_examiner", "Bosh Examiner"),
         ("exam", "examiner", "Examiner Bir"), ("t1", "teacher", "Ustoz Bir"),
         ("t2", "teacher", "Ustoz Ikki"), ("sup", "support_teacher", "Support Bir"),
         ("stu", "student", "Talaba Bir")]
UID = {}
for un, role, fn in USERS:
    u = models.User(username=un, password_hash=hash_password("x"),
                    full_name=fn, role=role, branch_id=BID, is_active=1)
    db.add(u)
    db.commit()
    UID[un] = u.id
teacher = models.Teacher(full_name="Ustoz Bir", branch_id=BID,
                         user_id=UID["t1"])
db.add(teacher)
db.commit()
g = models.Group(name="IELTS-A", branch_id=BID, teacher_id=teacher.id,
                 subject="english", level="ielts_graduation")
db.add(g)
db.commit()
st = models.Student(full_name="Talaba Bir", branch_id=BID, group_id=g.id,
                    status="active", enrolled_date=TODAY - timedelta(days=60),
                    user_id=UID["stu"])
db.add(st)
db.commit()
db.add(models.Exam(group_id=g.id, kind="unit", unit_no=1, date=TODAY,
                   status="done", max_score=20))
db.commit()


def _ch(qid, text, ans=2):
    return {"id": qid, "type": "choice", "q": text,
            "options": ["red", "blue", "green", "black"], "answer": ans}


SMALL_KEY = "Sinov Mock · Listening — Variant X"
SMALL_PARTS = exam_online.clean_parts([
    {"title": "Part 1", "skill": "ielts_listening", "script": "Script one text.",
     "questions": [_ch("L1", "Colour one?"), _ch("L2", "Colour two?"),
                   {"id": "L3", "type": "text", "q": "Where?",
                    "answer": ["library"]}]},
    {"title": "Part 2", "skill": "ielts_listening", "script": "Script two text.",
     "questions": [_ch("L4", "Four?"), _ch("L5", "Five?"), _ch("L6", "Six?")]},
    {"title": "Part 3", "skill": "ielts_listening", "script": "Script three text.",
     "questions": [_ch("L7", "Seven?"), _ch("L8", "Eight?"), _ch("L9", "Nine?")]},
    {"title": "Part 4", "skill": "ielts_listening", "script": "Script four text.",
     "audio_url": "/exam-audio/p4.mp3",
     "questions": [_ch("L10", "Ten?"), _ch("L11", "Eleven?"), _ch("L12", "Twelve?")]},
])
SMALL_IDS = {}
for lv in ("ielts_intro", "ielts_foundation", "ielts_graduation"):
    t = models.ExamTemplate(level=lv, kind="mock", title=SMALL_KEY,
                            parts=json.dumps(SMALL_PARTS, ensure_ascii=False),
                            variant="X", subject="english", is_active=1,
                            created_by="Examiner")
    db.add(t)
    db.commit()
    SMALL_IDS[lv] = t.id
REP_ID = SMALL_IDS["ielts_intro"]

CEFR_KEY = "Sinov CEFR · Reading — Variant X"
CEFR_PARTS = exam_online.clean_parts([
    {"title": "Part 1", "skill": "cefr_reading", "passage": "Some passage.",
     "questions": [_ch(f"R{i}", f"R question {i}?", 0) for i in range(1, 6)]},
])
db.add(models.ExamTemplate(level="cefr", kind="mock", title=CEFR_KEY,
                           parts=json.dumps(CEFR_PARTS, ensure_ascii=False),
                           variant="X", subject="english", is_active=1,
                           created_by="Examiner"))
db.commit()

H = tok("asos")
HE = tok("bosh")
EX = tok("exam")
T1 = tok("t1")
T2 = tok("t2")
SUP = tok("sup")
STU = tok("stu")

ISO_MODELS = [models.Exam, models.ExamOnline, models.ExamSubmission,
              models.ExamResult, models.CoinEntry, models.XpTransaction]


def iso_counts():
    s = SessionLocal()
    try:
        return {m.__tablename__: s.query(m).count() for m in ISO_MODELS}
    finally:
        s.close()


BEFORE = iso_counts()
r = client.get("/api/examiner/exams", headers=HE)
EXAMINER_BEFORE = (r.status_code, r.json())
r = client.get("/api/me/results", headers=T1)
ME_BEFORE = (r.status_code, r.json())


# ============================================================ 1. KATALOG
print("\n=== 1. KATALOG ===")
r = client.get("/api/mock-practice/catalog", headers=T1)
ck("ustozga katalog 200", r.status_code, 200)
cat = r.json()
items = [v for bk in cat["banks"] for s in bk["sections"] for v in s["variants"]]
keys = [v["content_key"] for v in items]
ck("har mazmun bitta marta", len(keys), len(set(keys)))
ck("kichik test 3 daraja emas, 1 ta", keys.count(SMALL_KEY), 1)
real = next((k for k in keys if k.startswith("IELTS Mock")
             and "Listening" in k and k.endswith("Variant A")), None)
ck("haqiqiy seed: IELTS Listening A katalogda", real is not None, True)
real_rows = [t for t in db.query(models.ExamTemplate)
             .filter(models.ExamTemplate.kind == "mock").all()
             if mock_seed.canon_title(t.title) == real]
ck("haqiqiy seed: bazada 3 daraja qatori", len(real_rows), 3)
ck("haqiqiy seed: katalogda 1 marta", keys.count(real), 1)
ck("katalogda kalit/skript yo'q", bad_keys(cat), set())
small = next(v for v in items if v["content_key"] == SMALL_KEY)
ck("kichik test: 12 savol, 30 daqiqa, skript bor",
   (small["q_count"], small["duration"], small["has_script"]), (12, 30, True))
ck("ustoz cheklangan deb belgilangan", cat["limited"], True)
ck("o'quvchiga 403",
   client.get("/api/mock-practice/catalog", headers=STU).status_code, 403)

# ============================================================ 2. BOSHLASH
print("\n=== 2. BOSHLASH, GET, SKRIPT ===")
r = client.post("/api/mock-practice", headers=T1,
                json={"content_key": SMALL_KEY})
ck("boshlash 200", r.status_code, 200)
P1 = r.json()["id"]
ck("yangi urinish", r.json()["resumed"], False)
g1 = client.get(f"/api/mock-practice/{P1}", headers=T1).json()
ck("GET: kalit va skript yo'q", bad_keys(g1), set())
ck("GET: holat in_progress", g1["status"], "in_progress")
ck("GET: 4 bo'lim", len(g1["parts"]), 4)
ck("GET: skriptli bo'limlar 0,1,2 (3 da audio bor)", g1["script_parts"],
   [0, 1, 2])
ck("GET: vaqt belgilangan", g1["ends_at"] is not None and g1["duration_min"] == 30,
   True)
r = client.post(f"/api/mock-practice/{P1}/script/0", headers=T1)
ck("skript/0 matn qaytaradi", (r.status_code, r.json().get("script")),
   (200, "Script one text."))
db.expire_all()
ck("script_opened == '0'", db.query(models.MockPractice).get(P1).script_opened,
   "0")
r = client.post(f"/api/mock-practice/{P1}/script/3", headers=T1)
ck("audio bor bo'lim skripti 400", r.status_code, 400)
ck("boshqa ustoz urinishni ko'rmaydi (404)",
   client.get(f"/api/mock-practice/{P1}", headers=T2).status_code, 404)
ck("examinerlar boshlig'i ham ko'rmaydi (404)",
   client.get(f"/api/mock-practice/{P1}", headers=HE).status_code, 404)
ck("audit: start yozildi",
   db.query(models.AuditLog).filter(models.AuditLog.entity == "mock_practice",
                                    models.AuditLog.action == "start").count(), 1)

print("\n--- 7a. test paytida xabar ---")
r = client.post("/api/mock-issues", headers=T1,
                json={"practice_id": P1, "qid": "L2", "kind": "answer_key",
                      "comment": "Kalit B bo'lishi kerak", "suggested": "B"})
ck("xabar 200", r.status_code, 200)
ck("javobda faqat id va holat", sorted(r.json().keys()), ["id", "status"])
I_L2 = r.json()["id"]
db.expire_all()
iss = db.query(models.MockIssue).get(I_L2)
ck("during_test = 1", iss.during_test, 1)
ck("snapshot serverda kalit bilan", json.loads(iss.q_snapshot)["answer"], 2)
ck("T2 urinishsiz xabar bera olmaydi (403)",
   client.post("/api/mock-issues", headers=T2,
               json={"content_key": SMALL_KEY, "qid": "L2",
                     "kind": "typo"}).status_code, 403)
ck("T2 T1 ning urinishi bilan ham 403",
   client.post("/api/mock-issues", headers=T2,
               json={"practice_id": P1, "qid": "L2",
                     "kind": "typo"}).status_code, 403)
ck("o'quvchi 403",
   client.post("/api/mock-issues", headers=STU,
               json={"content_key": SMALL_KEY, "qid": "L2",
                     "kind": "typo"}).status_code, 403)
ck("noto'g'ri tur 400",
   client.post("/api/mock-issues", headers=T1,
               json={"practice_id": P1, "qid": "L2",
                     "kind": "zzz"}).status_code, 400)
ck("yo'q savol 400",
   client.post("/api/mock-issues", headers=T1,
               json={"practice_id": P1, "qid": "L99",
                     "kind": "typo"}).status_code, 400)

# ============================================================ 3. TOPSHIRISH
print("\n=== 3. SAQLASH VA TOPSHIRISH ===")
T1_ANS = {"L1": 2, "L2": 1, "L3": "Library", "L4": 2, "L5": 2, "L6": 1,
          "L7": 2, "L8": 0}
r = client.post(f"/api/mock-practice/{P1}/save", headers=T1,
                json={"answers": T1_ANS})
ck("saqlash ok", r.json(), {"ok": True})
ck("saqlangan javob GET da", client.get(f"/api/mock-practice/{P1}",
                                         headers=T1).json()["answers"]["L3"],
   "Library")
r = client.post(f"/api/mock-practice/{P1}/submit", headers=T1,
                json={"answers": T1_ANS})
ck("topshirish 200", r.status_code, 200)
rv = r.json()
ck("ball 5/12", (rv["score"], rv["max"]), (5.0, 12.0))
ck("IELTS band = mock_band", rv["band"],
   exam_online.mock_band(SMALL_PARTS, 5, 12))
ck("natijada skript yo'q", "script" in bad_keys(rv), False)
r2 = client.post(f"/api/mock-practice/{P1}/submit", headers=T1,
                 json={"answers": {}})
ck("ikkinchi topshirish — o'sha natija (idempotent)",
   (r2.json()["score"], r2.json()["submitted_at"]),
   (rv["score"], rv["submitted_at"]))
ck("topshirilgach skript 400",
   client.post(f"/api/mock-practice/{P1}/script/1", headers=T1).status_code,
   400)

r = client.post("/api/mock-practice", headers=EX,
                json={"content_key": CEFR_KEY})
PE1 = r.json()["id"]
rv_c = client.post(f"/api/mock-practice/{PE1}/submit", headers=EX,
                   json={"answers": {"R1": 0, "R2": 0, "R3": 0, "R4": 1,
                                     "R5": 1}}).json()
ck("CEFR: 3/5", (rv_c["score"], rv_c["max"]), (3.0, 5.0))
ck("CEFR: taxminiy daraja lr_approx", rv_c["cefr"]["level"],
   lr_approx(3, 5)["level"])
ck("CEFR: IELTS band yo'q", rv_c["band"], None)

# ============================================================ 4. KALIT HIMOYASI
print("\n=== 4. KALIT HIMOYASI ===")
det = {d["id"]: d for d in rv["detail"]}
ck("ustoz: xato belgilanganda to'g'ri javob ko'rinadi", det["L2"]["correct"],
   "C) green")
ck("ustoz: belgilanmaganda ko'rinmaydi", det["L9"]["correct"], None)
ck("ustoz: to'g'ri belgilanganda odatiy varaq (frontend yashiradi)",
   (det["L1"]["ok"], det["L1"]["correct"]), (True, "C) green"))
ck("ustoz: 8/12 belgilangan — kalit yopilmagan", rv["key_hidden"], False)

r = client.post("/api/mock-practice", headers=SUP,
                json={"content_key": SMALL_KEY})
PS = r.json()["id"]
rv_s = client.post(f"/api/mock-practice/{PS}/submit", headers=SUP,
                   json={"answers": {}}).json()
ck("bo'sh topshirish: hech bir kalit ko'rinmaydi",
   [d["correct"] for d in rv_s["detail"] if d["correct"] is not None], [])
ck("bo'sh topshirish: key_hidden", rv_s["key_hidden"], True)

r = client.post("/api/mock-practice", headers=HE,
                json={"content_key": SMALL_KEY})
PH = r.json()["id"]
rv_h = client.post(f"/api/mock-practice/{PH}/submit", headers=HE,
                   json={"answers": {}}).json()
ck("examinerlar boshlig'i hamma kalitni ko'radi",
   all(d["correct"] for d in rv_h["detail"]), True)

# ============================================================ 5. CHEKLOV
print("\n=== 5. CHEKLOV ===")
rep = db.query(models.ExamTemplate).get(REP_ID)
rep.is_active = 0
db.commit()
r = client.post("/api/mock-practice", headers=T1,
                json={"content_key": SMALL_KEY})
ck("boshqa daraja qatori orqali ham 30 kunda bir (429)", r.status_code, 429)
ck("xabar matni", "30 kunda bir marta" in r.json().get("detail", ""), True)
rep.is_active = 1
db.commit()

r = client.post("/api/mock-practice", headers=T2,
                json={"content_key": SMALL_KEY})
PT2 = r.json()["id"]
r = client.post("/api/mock-practice", headers=T2,
                json={"content_key": CEFR_KEY})
ck("bir vaqtda bitta: boshlangani qaytadi",
   (r.json()["id"], r.json()["resumed"]), (PT2, True))
client.post(f"/api/mock-practice/{PT2}/save", headers=T2,
            json={"answers": {"L2": 1, "L6": 1}})

r = client.post("/api/mock-practice", headers=EX,
                json={"content_key": CEFR_KEY})
ck("examinerga cheklov yo'q (qayta boshlaydi)",
   (r.status_code, r.json()["id"] != PE1), (200, True))
PE2 = r.json()["id"]
client.post(f"/api/mock-practice/{PE2}/submit", headers=EX,
            json={"answers": {}})

p = db.query(models.MockPractice).get(PT2)
p.ends_at = datetime.utcnow() - timedelta(seconds=exam_online.GRACE_SEC + 60)
db.commit()
r = client.post(f"/api/mock-practice/{PT2}/save", headers=T2,
                json={"answers": {"L1": 2}})
ck("muddat o'tgach saqlanmaydi", r.json(), {"ok": False, "expired": True})
g2 = client.get(f"/api/mock-practice/{PT2}", headers=T2).json()
ck("muddat o'tgach GET avtomat yopadi", g2["status"], "submitted")
ck("saqlangan javoblar bilan baholandi (0/12)", (g2["score"], g2["max"]),
   (0.0, 12.0))
ck("2/12 belgilangan ustozga kalit umuman ko'rinmaydi",
   (g2["key_hidden"], [d["correct"] for d in g2["detail"]
                       if d["correct"] is not None]), (True, []))

r = client.post("/api/mock-practice", headers=EX,
                json={"content_key": SMALL_KEY})
PE3 = r.json()["id"]
client.post(f"/api/mock-practice/{PE3}/submit", headers=EX,
            json={"answers": {"L2": 1, "L6": 1}})

mine = client.get("/api/mock-practice/mine", headers=T1).json()
ck("mening urinishlarim: 1 ta, ochiq xabar 1",
   (len(mine), mine[0]["issues"]["open"]), (1, 1))
cat2 = client.get("/api/mock-practice/catalog", headers=T1).json()
sm2 = next(v for bk in cat2["banks"] for s in bk["sections"]
           for v in s["variants"] if v["content_key"] == SMALL_KEY)
ck("katalog: my_last va qulf", (sm2["my_last"]["score"],
                                 sm2["locked_until"] is not None), (5.0, True))
lg = client.get("/api/mock-practice/log", headers=HE)
ck("ochilganlar jurnali: 200, ball yo'q",
   (lg.status_code, bad_keys(lg.json(), ("score", "band", "max"))),
   (200, set()))
ck("jurnal ustozga 403",
   client.get("/api/mock-practice/log", headers=T1).status_code, 403)

# ============================================================ 7b. BIRLASHISH
print("\n=== 7. XABAR BIRLASHADI ===")
r = client.post("/api/mock-issues", headers=T1,
                json={"practice_id": P1, "qid": "L2", "kind": "two_answers",
                      "comment": "B ham, C ham to'g'ri"})
ck("qayta xabar — o'sha yozuv", r.json()["id"], I_L2)
ck("baribir bitta qator",
   db.query(models.MockIssue).filter(
       models.MockIssue.reporter_id == UID["t1"],
       models.MockIssue.qid == "L2").count(), 1)
db.expire_all()
ck("xabarchining javobi yozilgan",
   db.query(models.MockIssue).get(I_L2).given, "B) blue")

# ============================================================ 8. TRIAGE
print("\n=== 8. TRIAGE ===")
ck("count = 1", client.get("/api/mock-issues/count", headers=HE).json(),
   {"open": 1})
ck("ustozga ro'yxat 403",
   client.get("/api/mock-issues", headers=T1).status_code, 403)
ck("ustozga count 403",
   client.get("/api/mock-issues/count", headers=T1).status_code, 403)
lst = client.get("/api/mock-issues", headers=HE).json()
ck("bitta guruh", len(lst["groups"]), 1)
grp = lst["groups"][0]
ck("guruh (mazmun, savol)", (grp["content_key"], grp["qid"]),
   (SMALL_KEY, "L2"))
ck("nusxalar = 3", grp["copies"], 3)
ck("faol vakil", grp["template_id"], REP_ID)
ck("signal: 3 urinish, 100% xato", (grp["signal"]["n_attempts"],
                                    grp["signal"]["wrong_pct"]), (3, 100))
ck("signal: ko'p xato javob va kalit",
   (grp["signal"]["top_wrong"], grp["signal"]["key"]),
   ("B) blue", "C) green"))
ck("hali o'zgarmagan", grp["changed"], False)
sus = {(s["content_key"], s["qid"]): s for s in lst["suspect"]}
ck("xabarsiz L6 shubhali ro'yxatda", (SMALL_KEY, "L6") in sus, True)
ck("xabar berilgan L2 shubhalida yo'q", (SMALL_KEY, "L2") in sus, False)
ck("L6 signali 100%", sus.get((SMALL_KEY, "L6"), {}).get("wrong_pct"), 100)

ck("ustoz rad eta olmaydi (403)",
   client.put(f"/api/mock-issues/{I_L2}", headers=T1,
              json={"status": "rejected"}).status_code, 403)
r = client.put(f"/api/mock-issues/{I_L2}", headers=HE,
               json={"status": "rejected", "note": "Kalit to'g'ri: C"})
ck("rad etish 200", (r.status_code, r.json()["closed"]), (200, 1))
ck("count = 0", client.get("/api/mock-issues/count", headers=HE).json(),
   {"open": 0})
myi = client.get("/api/mock-issues/mine", headers=T1).json()
ck("T1 o'z xabarida rad etilgan va izoh",
   (myi[0]["status"], myi[0]["resolution_note"]),
   ("rejected", "Kalit to'g'ri: C"))
ck("mening xabarlarimda kalit yo'q", "answer" in bad_keys(myi), False)

# ============================================================ 9. TUZATISH
print("\n=== 9. SHABLON TAHRIRI + NUSXALAR ===")
r = client.post("/api/mock-issues", headers=T1,
                json={"practice_id": P1, "qid": "L1", "kind": "typo",
                      "comment": "Savolda imlo xato"})
I_L1 = r.json()["id"]
# Bitta daraja qatori oldindan boshqacha tahrirlangan
grad = db.query(models.ExamTemplate).get(SMALL_IDS["ielts_graduation"])
gp = json.loads(grad.parts)
gp[2]["questions"][0]["q"] = "Seven (graduation o'zi)?"
grad.parts = json.dumps(gp, ensure_ascii=False)
# Yashirin "(dublikat)" nusxa ham sinxronlanadi
dup = models.ExamTemplate(level="ielts_graduation", kind="mock",
                          title=SMALL_KEY + " (dublikat)",
                          parts=json.dumps(SMALL_PARTS, ensure_ascii=False),
                          variant="X", subject="english", is_active=0,
                          created_by="Examiner")
db.add(dup)
db.commit()
DUP_ID = dup.id
GRAD_PARTS_BEFORE = grad.parts

tpl = client.get(f"/api/exam-templates/{REP_ID}", headers=HE).json()
parts = tpl["parts"]
parts[0]["questions"][0]["q"] = "Colour one (tuzatildi)?"
body = {"level": tpl["level"], "kind": "mock", "title": tpl["title"],
        "parts": parts, "paper_max": tpl["paper_max"], "is_active": True,
        "variant": tpl["variant"], "subject": tpl["subject"],
        "sync_siblings": True, "resolve_issue_ids": [I_L1]}
ck("ustoz shablonni o'zgartira olmaydi (403)",
   client.put(f"/api/exam-templates/{REP_ID}", headers=T1,
              json=body).status_code, 403)
r = client.put(f"/api/exam-templates/{REP_ID}", headers=HE, json=body)
ck("saqlash 200", r.status_code, 200)
res = r.json()
ck("ikki bir xil nusxa yangilandi",
   sorted(res["synced"]), sorted([SMALL_IDS["ielts_foundation"], DUP_ID]))
ck("oldindan tahrirlangani diverged", res["diverged"],
   [SMALL_IDS["ielts_graduation"]])
ck("1 xabar yopildi", res["resolved"], 1)
db.expire_all()
fnd = db.query(models.ExamTemplate).get(SMALL_IDS["ielts_foundation"])
ck("foundation yangi matnda",
   json.loads(fnd.parts)[0]["questions"][0]["q"], "Colour one (tuzatildi)?")
ck("graduation tegilmagan",
   db.query(models.ExamTemplate).get(SMALL_IDS["ielts_graduation"]).parts
   == GRAD_PARTS_BEFORE, True)
ck("xabar fixed", db.query(models.MockIssue).get(I_L1).status, "fixed")
myi = {i["id"]: i for i in
       client.get("/api/mock-issues/mine", headers=T1).json()}
ck("T1 fixed ni ko'radi", myi[I_L1]["status"], "fixed")
fx = client.get("/api/mock-issues?status=fixed", headers=HE).json()
g_l1 = next((x for x in fx["groups"] if x["qid"] == "L1"), {})
ck("eski snapshot: changed = True", g_l1.get("changed"), True)
rj = client.get("/api/mock-issues?status=rejected", headers=HE).json()
ck("tegilmagan savol: changed = False",
   next((x for x in rj["groups"] if x["qid"] == "L2"), {}).get("changed"),
   False)
r = client.put(f"/api/exam-templates/{REP_ID}", headers=HE,
               json={**body, "sync_siblings": False, "resolve_issue_ids": None})
ck("oddiy saqlash (bayroqsiz) avvalgidek", (r.status_code, r.json()["synced"],
                                           r.json()["resolved"]), (200, [], 0))

# ============================================================ 10. O'CHIRISH
print("\n=== 10. SHABLONNI O'CHIRISH ===")
r = client.delete(f"/api/exam-templates/{REP_ID}", headers=HE)
ck("ishlatilmagan shablon o'chadi", (r.status_code, r.json()["hidden"]),
   (200, False))
db.expire_all()
ck("qator yo'q", db.query(models.ExamTemplate).get(REP_ID), None)
g3 = client.get(f"/api/mock-practice/{P1}", headers=T1)
ck("urinish boshqa nusxaga o'tadi", (g3.status_code, g3.json()["score"]),
   (200, 5.0))
ck("shablon almashgani belgilanadi", g3.json()["tpl_changed"], True)
for tid in (SMALL_IDS["ielts_foundation"], SMALL_IDS["ielts_graduation"],
            DUP_ID):
    client.delete(f"/api/exam-templates/{tid}", headers=HE)
ck("hech nusxa qolmasa 410",
   client.get(f"/api/mock-practice/{P1}", headers=T1).status_code, 410)
ck("o'chgan testni boshlab bo'lmaydi (410)",
   client.post("/api/mock-practice", headers=HE,
               json={"content_key": SMALL_KEY}).status_code, 410)

# ============================================================ 12. KUNLIK CHEK
print("\n=== 7c. KUNIGA 30 TA XABAR ===")
real_rep = min(t.id for t in real_rows if t.is_active == 1)
qids = [q["id"] for q in exam_online._questions(
    client.get(f"/api/exam-templates/{real_rep}", headers=HE).json()["parts"])]
codes = [client.post("/api/mock-issues", headers=EX,
                     json={"content_key": real, "qid": qid,
                           "kind": "unclear"}).status_code
         for qid in qids[:30]]
ck("examiner urinishsiz 30 ta xabar beradi", set(codes), {200})
ck("31-xabar 429",
   client.post("/api/mock-issues", headers=EX,
               json={"content_key": real, "qid": qids[30],
                     "kind": "unclear"}).status_code, 429)
ck("mavjud xabarni to'ldirish chekka urilmaydi",
   client.post("/api/mock-issues", headers=EX,
               json={"content_key": real, "qid": qids[0], "kind": "typo",
                     "comment": "yana"}).status_code, 200)

# ============================================================ 6. IZOLYATSIYA
print("\n=== 6. IZOLYATSIYA ===")
ck("Exam/Online/Submission/Result/Coin/XP soni o'zgarmadi", iso_counts(),
   BEFORE)
r = client.get("/api/examiner/exams", headers=HE)
ck("/api/examiner/exams o'zgarmadi", (r.status_code, r.json()),
   EXAMINER_BEFORE)
r = client.get("/api/me/results", headers=T1)
ck("T1 /api/me/results o'zgarmadi", (r.status_code, r.json()), ME_BEFORE)

# ============================================================ 11. STATIK
print("\n=== 11. STATIK TEKSHIRUV ===")
ALLOWED = {"models.py", "mock_practice.py", "exam_online.py"}
leak = []
for name in sorted(os.listdir(HERE)):
    if not name.endswith(".py") or name.startswith("test_"):
        continue
    src = open(os.path.join(HERE, name), encoding="utf-8").read()
    if name == "exam_online.py":
        if "MockPractice" in src:
            leak.append(name + ":MockPractice")
        continue
    if name in ALLOWED:
        continue
    if re.search(r"\bMock(Practice|Issue)\b", src):
        leak.append(name)
ck("MockPractice/MockIssue faqat ruxsat etilgan fayllarda", leak, [])

ROOT = os.path.dirname(HERE)


def _read(*p):
    try:
        return open(os.path.join(ROOT, *p), encoding="utf-8").read()
    except OSError:
        return ""


TS = _read("src", "lib", "roles.ts")


def ts_list(name, depth=0):
    """roles.ts dagi ro'yxatni rol qiymatlariga yoyadi (...spread ham)."""
    m = re.search(rf"export const {name}\s*=\s*(\[.*?\]|[^;\n]+);", TS, re.S)
    if not m or depth > 5:
        return None
    out = []
    for spread, ident in re.findall(r"(\.\.\.)?\b([A-Z][A-Z0-9_]+)\b",
                                    m.group(1)):
        mm = re.search(rf'export const {ident}\s*=\s*"([^"]+)"', TS)
        if mm and not spread:
            out.append(mm.group(1))
        else:
            sub = ts_list(ident, depth + 1)
            out += sub or []
    return out


for name in ("MOCK_PRACTICE", "MOCK_LIMITED", "MOCK_ISSUE_VIEW",
             "MOCK_ISSUE_TRIAGE"):
    got = ts_list(name)
    ck(f"roles.ts {name} == roles.py",
       set(got) if got is not None else None, set(getattr(roles, name)))

m = re.search(r"export const TEACHER_MENU\s*=\s*\[(.*?)\]", TS, re.S)
ck("TEACHER_MENU da /mock-practice",
   bool(m) and '"/mock-practice"' in m.group(1), True)
# Menyu 2026-09-27 dan src/components/navItems.ts da (xodim paneli va
# /app xodim ilovasi uchun bitta ro'yxat). Band `mockItem` o'zgaruvchisi
# orqali qo'shiladi — ta'rifi "/mock-practice" ga olib borishi shart.
NAV = _read("src", "components", "navItems.ts")
ck("navItems.ts: mockItem /mock-practice ga olib boradi",
   bool(re.search(r'const mockItem\s*=\s*\{\s*to:\s*"/mock-practice"', NAV)),
   True)


def _nav_block(head):
    i = NAV.find(head)
    return NAV[i:NAV.find("\n  }\n", i)] if i >= 0 else ""


ck("navItems.ts support teacher menyusida mock",
   "mockItem" in _nav_block("if (user?.role === SUPPORT_TEACHER) {"), True)
ck("navItems.ts ustoz menyusida mock (TEACHER_MENU kesishidan oldin)",
   "mockItem" in _nav_block("if (user?.role === TEACHER) {"), True)
BANK = _read("src", "components", "ExamBank.tsx")
ck("ExamBank tur tanlagichi mockda ONLINE_KINDS ishlatmaydi",
   bool(BANK) and not re.search(r"\{\s*ONLINE_KINDS\.map\(", BANK), True)

db.close()
print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
