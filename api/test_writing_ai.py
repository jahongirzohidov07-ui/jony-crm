"""WRITING AI BAHOSI — UCHIDAN UCHIGA (2026-09-28).

Jahongir: "Writingni ham avtobaholaydigan qilib qoysak yaxshi bo'lardi.
Hech qanday muammolarsiz bo'lishi yaxshi bolardi".

AI chaqiruvi soxta (writing_ai.AI["call"]) — tarmoq yo'q:
  A. Toza funksiyalar: SVG grafik yozuvlari, IELTS (Task 2 ikki
     barobar) va CEFR (0-75) hisobi, bo'sh insho AI'siz 0, buzuq javob,
     kalit yo'q;
  B. Guruh mocki: topshirilgach "pending", o'quvchi brauzeri /ai-grade
     ni chaqiradi -> qog'oz bali = AI bandi (paper_by="ai"); examiner
     o'zgartirsa AI unga tegmaydi; qayta baholash; parallel so'rov
     ikkinchi marta AI chaqirmaydi; e'londan keyin AI jadvalga yozmaydi;
     kalit yo'q -> no_key, ball bo'sh;
  C. Xodim sinovi: /mock-practice/{id}/ai-grade -> band, izoh;
     idempotent;
  D. Mock testlar jadvali: L, R, W, S tartibi, vaqt, Writing "avtomat".
"""
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timedelta

_DB = os.path.join(tempfile.gettempdir(), "writing_ai_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402,F401
import entry                                       # noqa: F401,E402
import exam_online                                 # noqa: E402
import cefr_score as C                             # noqa: E402
import mock_marking                                # noqa: E402
import mock_seed                                   # noqa: E402
import writing_ai                                  # noqa: E402
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


# ------------------------------------------------------------ soxta AI
CALLS = []
PLAN = {"ielts": {}, "cefr": {}, "raise": None, "raw": None, "reverse": False}


def fake(system, user_text):
    CALLS.append((system[:40], user_text))
    if PLAN["raise"]:
        raise PLAN["raise"]
    if PLAN["raw"] is not None:
        return PLAN["raw"]
    ids = re.findall(r"\[id=(T\d+)\]", user_text)
    rows = []
    gram = ([{"wrong": "peoples is", "right": "people are", "why": "subject-verb agreement"}]
            + [{"wrong": f"a informations {i}", "right": f"information {i}", "why": "countability"}
               for i in range(14)]
            + [{"wrong": "same", "right": "same", "why": "not an error"}])
    voc = [{"wrong": "make a research", "right": "do research", "why": "collocation",
            "serious": "true"},
           {"wrong": "enviroment", "right": "environment", "why": "spelling"}, "junk",
           {"wrong": "more glasses", "right": "more mirrors", "why": "wrong word",
            "serious": True}]
    if "IELTS" in system:
        for tid in ids:
            c = PLAN["ielts"].get(int(tid[1:]) - 1, [6, 6, 6, 6])
            rows.append({"id": tid, "ta": c[0], "cc": c[1], "lr": c[2],
                         "gra": c[3], "feedback": "The response addresses the task.",
                         "grammar": gram, "vocabulary": voc})
    else:
        for tid in ids:
            rows.append({"id": tid, "mark": PLAN["cefr"].get(int(tid[1:]) - 1, 4),
                         "feedback": "Rasmiy uslub yaxshi."})
    if PLAN["reverse"]:
        rows.reverse()
    return "```json\n" + json.dumps({"tasks": rows}) + "\n```"


writing_ai.AI["call"] = fake
ESSAY = ("Technology has changed the way people communicate and learn. " * 30).strip()


def mocks_of(section):
    return [t for t in db.query(models.ExamTemplate).filter(
        models.ExamTemplate.kind == "mock", models.ExamTemplate.is_active == 1).all()
        if exam_online._mock_section(exam_online._load(t.parts)) == section]


# ============================================================ A
print("=== A. TOZA FUNKSIYALAR ===")
db = SessionLocal()
mock_seed.seed_mocks(db)
wt, ct = mocks_of("ielts_writing"), mocks_of("cefr_writing")
ck("IELTS Writing: 5 variant (3 daraja uchun)", len({t.variant for t in wt}), 5)
ck("CEFR Writing shablonlari 3 ta", len(ct), 3)
ip = exam_online._load(sorted(wt, key=lambda t: t.id)[0].parts)
tasks = writing_ai.tasks_of(ip)
ck("IELTS: 2 topshiriq, 150/250 so'z", [t["min_words"] for t in tasks], [150, 250])
ck("Task 1 grafigi yozuvlari AI'ga matn bo'lib boradi",
   len(tasks[0]["chart"]) > 10 and tasks[1]["chart"] == "", True)
ck("skill_of", (writing_ai.skill_of(ip),
                writing_ai.skill_of(exam_online._load(ct[0].parts))),
   ("ielts_writing", "cefr_writing"))

CALLS.clear()
PLAN["ielts"] = {0: [5, 6, 6, 6], 1: [7, 7, 6, 7]}
ans = {tasks[0]["qid"]: ESSAY, tasks[1]["qid"]: ESSAY}
res = writing_ai.grade(ip, ans)
# (5+14)/3=6.33, (6+14)/3=6.67, (6+12)/3=6, (6+14)/3=6.67 -> o'rtacha 6.42
ck("IELTS: mezonlar (T1 + 2*T2)/3", res["combined"],
   {"ta": 6.33, "cc": 6.67, "lr": 6.0, "gra": 6.67})
ck("IELTS band = kalkulyator (bir marta yaxlitlash)", res["band"],
   mock_marking.ielts_band([19 / 3, 20 / 3, 6.0, 20 / 3])["band"])
ck("bitta AI chaqiruvi", len(CALLS), 1)
ck("o'quvchi javobidan boshqa shaxsiy ma'lumot yo'q", "Talaba" in CALLS[0][1], False)
g0, v0 = res["tasks"][1]["grammar"], res["tasks"][1]["vocabulary"]
ck("grammatika xatolari bittama-bitta, 12 tagacha",
   (len(g0), g0[0]), (12, {"wrong": "peoples is", "right": "people are",
                            "why": "subject-verb agreement", "serious": False}))
ck("lug'at xatolari alohida; buzuq qator tashlanadi",
   [x["right"] for x in v0], ["do research", "environment", "more mirrors"])
ck("ma'noni buzadigan xato belgisi faqat aniq true bo'lsa",
   [x["serious"] for x in v0], [False, False, True])
ck("promptda izoh inglizcha va xatolar ro'yxati so'raladi",
   ("write it in English" in writing_ai.IELTS_SYSTEM,
    '"vocabulary"' in writing_ai.IELTS_SYSTEM), (True, True))
ck("promptlarda band chegaralari (kalibrovka) bor",
   ("HOW TO FIX A BAND" in writing_ai.IELTS_SYSTEM,
    "CLEAR overview" in writing_ai.IELTS_SYSTEM,
    "HOW TO FIX A MARK" in writing_ai.CEFR_SYSTEM), (True, True, True))
_sc = writing_ai._cefr_scale_text()
ck("CEFR shkala matni: 1.2 -> 0-5, Part 2 -> 0-6, inglizcha",
   ("Task 1.2 (target B2, 120-150 words), mark 0-5:" in _sc,
    "Task 2 (target C1, 180-200 words), mark 0-6:" in _sc, "so'z" in _sc),
   (True, True, False))
ck("CEFR shkalasida har ball uchun bitta qator (yuqoridan 0 gacha)",
   [[int(s.split(" ")[0]) for s in writing_ai.CEFR_SCALE[p]]
    for p, *_ in C.WRITING_NEW_PARTS],
   [list(range(mx, -1, -1)) for _p, mx, *_ in C.WRITING_NEW_PARTS])
ck("CEFR_SYSTEM formatlanadi (qavslar buzilmagan)",
   '"mark":<whole number>' in writing_ai.CEFR_SYSTEM.format(scale=_sc), True)

CALLS.clear()
PLAN["reverse"] = True
rr = writing_ai.grade(ip, ans)
PLAN["reverse"] = False
ck("AI qatorlari teskari kelsa ham id bo'yicha to'g'ri bog'lanadi",
   (rr["tasks"][0]["criteria"]["ta"], rr["tasks"][1]["criteria"]["ta"]), (5, 7))

CALLS.clear()
r0 = writing_ai.grade(ip, {tasks[0]["qid"]: "", tasks[1]["qid"]: "  "})
ck("hammasi bo'sh: AI chaqirilmaydi, band 0", (len(CALLS), r0["band"]), (0, 0.0))
CALLS.clear()
r1 = writing_ai.grade(ip, {tasks[0]["qid"]: "too short answer", tasks[1]["qid"]: ESSAY})
ck("<=20 so'zli Task 1: AI'siz, IELTS qoidasi bo'yicha Band 1",
   (len(re.findall(r"\[id=", CALLS[0][1])), r1["tasks"][0]["skipped"],
    r1["tasks"][0]["criteria"]["ta"], r1["tasks"][0]["band"]), (1, True, 1, 1.0))

cp = exam_online._load(sorted(ct, key=lambda t: t.id)[0].parts)
PLAN["cefr"] = {0: 4, 1: 2, 2: 2}
rc = writing_ai.grade(cp, {t["qid"]: ESSAY for t in writing_ai.tasks_of(cp)})
ck("CEFR 4+2+2 = 8 -> 47 B1 (rasmiy jadval, 2025-10-13)",
   (rc["score"], rc["level"], rc["exact"]), (47, "B1", True))
PLAN["cefr"] = {0: 9, 1: 6, 2: 7}
rc2 = writing_ai.grade(cp, {t["qid"]: ESSAY for t in writing_ai.tasks_of(cp)})
ck("CEFR: shkaladan tashqari baho qisiladi (1.1 9->5, 1.2 6->5, 2 7->6)",
   ([t["mark"] for t in rc2["tasks"]], rc2["score"]), ([5, 5, 6], 75))
PLAN["cefr"] = {0: 0, 1: -3, 2: 0}
rc2 = writing_ai.grade(cp, {t["qid"]: ESSAY for t in writing_ai.tasks_of(cp)})
ck("CEFR: 1.1 da yozilgan javob kamida 1, 1.2 va 2 da 0 bo'lishi mumkin",
   [t["mark"] for t in rc2["tasks"]], [1, 0, 0])
# Yakuniy shkaladagi hajm chegaralari
_ct = writing_ai.tasks_of(cp)
_w = lambda n: " ".join(["word"] * n)            # noqa: E731
PLAN["cefr"] = {0: 4, 1: 4, 2: 5}
rc4 = writing_ai.grade(cp, {_ct[0]["qid"]: _w(20), _ct[1]["qid"]: _w(50),
                            _ct[2]["qid"]: _w(30)})
ck("hajm chegarasi: 1.1 20 so'z -> 2, 1.2 50 so'z -> 2, Part 2 30 so'z -> 1",
   [t["mark"] for t in rc4["tasks"]], [2, 2, 1])
ck("chegara qo'llansa izohda aytiladi",
   "too short for a mark above 2" in rc4["tasks"][1]["feedback"], True)
rc5 = writing_ai.grade(cp, {_ct[0]["qid"]: _w(26), _ct[1]["qid"]: _w(61),
                            _ct[2]["qid"]: _w(91)})
ck("chegaradan bir so'z ortiq — cheklanmaydi",
   [t["mark"] for t in rc5["tasks"]], [4, 4, 5])
rc6 = writing_ai.grade(cp, {_ct[0]["qid"]: _w(40), _ct[1]["qid"]: _w(20),
                            _ct[2]["qid"]: _w(60)})
ck("1.2 24 so'zgacha -> 1, Part 2 38-90 so'z -> 2",
   [t["mark"] for t in rc6["tasks"]], [4, 1, 2])
PLAN["cefr"] = {}


def err_code(**plan):
    PLAN.update(plan)
    try:
        writing_ai.grade(ip, ans)
        code = None
    except writing_ai.WritingAIError as e:
        code = e.code
    PLAN.update(raw=None, **{"raise": None})
    return code


ck("buzuq javob -> bad_reply", err_code(raw="kechirasiz, baholay olmayman"), "bad_reply")
ck("kalit yo'q -> no_key", err_code(**{"raise": RuntimeError("no-key")}), "no_key")
ck("kvota -> rate_limit", err_code(**{"raise": TimeoutError("429")}), "rate_limit")
ck("boshqa xato -> ai_error", err_code(**{"raise": LookupError("x")}), "ai_error")
ck("kalit rad etildi (401/403) -> no_key (qayta urinilmaydi)",
   err_code(**{"raise": LookupError("Gemini authentication rejected (403)")}), "no_key")

PLAN["cefr"] = {0: 3, 1: 5, 2: 1}
PLAN["reverse"] = True
rc3 = writing_ai.grade(cp, {t["qid"]: ESSAY for t in writing_ai.tasks_of(cp)})
PLAN["reverse"] = False
PLAN["cefr"] = {}
ck("CEFR: 1.1/1.2/2 baholari id bo'yicha (teskari tartibda ham)",
   [t["mark"] for t in rc3["tasks"]], [3, 5, 1])
svg = "data:image/svg+xml;base64," + __import__("base64").b64encode(
    b"<svg><text>Sales &amp; costs</text><text>54&#37;</text></svg>").decode()
ck("SVG yozuvlaridagi belgilar ochiladi", writing_ai.svg_text(svg), "Sales & costs | 54%")

# ============================================================ B
print("\n=== B. GURUH MOCKI ===")
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
g = models.Group(name="IELTS-A", branch_id=BID, teacher_id=t.id,
                 subject="english", level="ielts_graduation")
db.add(g)
db.commit()
SIDS = []
for i in range(3):
    s = models.Student(full_name=f"Talaba {i}", branch_id=BID, group_id=g.id,
                       status="active", enrolled_date=TODAY - timedelta(days=60))
    db.add(s)
    db.commit()
    SIDS.append(s.id)


def tok(u):
    r = client.post("/api/auth/login", json={"username": u, "password": "x"})
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}


H, HE = tok("asos"), tok("bosh")
r = client.post(f"/api/groups/{g.id}/exams", headers=H, json={
    "kind": "mock", "date": TODAY.isoformat(), "max_score": None})
EID = r.json()["id"]
client.put(f"/api/exams/{EID}", headers=H, json={"status": "approved"})
tid = sorted(t.id for t in wt)[0]
# paper_max 0 yuborilsa ham Writing mockiga shablon shkalasi (9) qo'yiladi
r = client.post(f"/api/exams/{EID}/online", headers=HE, json={
    "template_id": tid, "paper_max": 0, "mode": "single"})
ck("link ochildi", r.status_code, 200)
ck("paper_max 0 emas, 9 (band 0 xavfi yo'q)", r.json()["online"]["paper_max"], 9.0)
ck("ai_writing belgisi", r.json()["online"]["ai_writing"], True)
client.post(f"/api/exams/{EID}/online/start", headers=HE,
            json={"minutes": 60, "countdown": 0})
TOKEN = client.get(f"/api/exams/{EID}/online", headers=HE).json()["online"]["token"]
WQ = [q for p in exam_online._load(db.query(models.ExamOnline)
                                   .filter_by(exam_id=EID).first().parts)
      for q in p["questions"]]


def begin_submit(sid, answers):
    r = client.post(f"/api/public/exam/{TOKEN}/begin",
                    json={"photo": PHOTO, "student_id": sid})
    assert r.status_code == 200, r.text
    key = r.json()["key"]
    r = client.post(f"/api/public/exam/{TOKEN}/submit",
                    json={"key": key, "answers": answers})
    assert r.status_code == 200, r.text
    return key


def sub_of(sid):
    return [s for s in client.get(f"/api/exams/{EID}/online", headers=HE)
            .json()["submissions"] if s["student_id"] == sid][0]


PLAN["ielts"] = {0: [6, 6, 6, 6], 1: [7, 7, 7, 7]}
K0 = begin_submit(SIDS[0], {q["id"]: ESSAY for q in WQ})
s0 = sub_of(SIDS[0])
ck("topshirilgach: pending, ball yo'q", (s0["ai_status"], s0["paper_score"]),
   ("pending", None))
CALLS.clear()
r = client.post(f"/api/public/exam/{TOKEN}/ai-grade", json={"key": K0})
ck("o'quvchi brauzeri baholatadi (natija ko'rsatilmaydi)",
   (r.status_code, r.json()), (200, {"ok": True, "status": "done"}))
s0 = sub_of(SIDS[0])
# (6+14)/3 = 6.67 -> 6.5 har mezonda -> band 6.5
ck("qog'oz bali = AI bandi, paper_by=ai",
   (s0["ai_status"], s0["ai_score"], s0["paper_score"], s0["paper_by"]),
   ("done", 6.5, 6.5, "ai"))
ck("examiner mezon va izohni ko'radi",
   (len(s0["ai_review"]["tasks"]), s0["ai_review"]["tasks"][1]["criteria"]["ta"],
    bool(s0["ai_review"]["tasks"][0]["feedback"])), (2, 7, True))
r = client.post(f"/api/public/exam/{TOKEN}/ai-grade", json={"key": K0})
ck("qayta chaqirilsa AI qayta chaqirilmaydi", (r.json()["status"], len(CALLS)),
   ("done", 1))
r = client.post(f"/api/public/exam/{TOKEN}/ai-grade", json={"key": "notarealkey123"})
ck("noto'g'ri kalit rad etiladi", r.status_code, 400)

# Eski sahifadan "Saqlash" (bo'sh katak) AI balini o'chirmaydi
r = client.put(f"/api/exams/{EID}/paper", headers=HE, json={
    "marks": [{"student_id": SIDS[0], "paper": None}]})
s0 = sub_of(SIDS[0])
ck("bo'sh katak AI balini o'chirmaydi", (s0["paper_score"], s0["paper_by"]), (6.5, "ai"))

# Examiner o'zgartiradi -> AI endi tegmaydi
r = client.put(f"/api/exams/{EID}/paper", headers=HE, json={
    "marks": [{"student_id": SIDS[0], "paper": 7.0}]})
s0 = sub_of(SIDS[0])
ck("examiner bahosi", (s0["paper_score"], s0["paper_by"]), (7.0, "Bosh"))
PLAN["ielts"] = {0: [4, 4, 4, 4], 1: [4, 4, 4, 4]}
r = client.post(f"/api/exam-submissions/{s0['id']}/ai-grade?force=true", headers=HE)
ck("qayta baholash: AI yangilanadi, examiner bahosi qoladi",
   (r.json()["ai_score"], r.json()["paper_score"], r.json()["paper_by"]),
   (4.0, 7.0, "Bosh"))
PLAN["raise"] = LookupError("down")
r = client.post(f"/api/exam-submissions/{s0['id']}/ai-grade?force=true", headers=HE)
ck("qayta baholash xato bo'lsa — eski AI natijasi qoladi",
   (r.json()["status"], r.json()["ai_status"], r.json()["ai_score"]),
   ("error", "done", 4.0))
PLAN["raise"] = None

# Parallel so'rov: "running" yangi bo'lsa AI chaqirilmaydi
PLAN["ielts"] = {0: [5, 5, 5, 5], 1: [5, 5, 5, 5]}
K1 = begin_submit(SIDS[1], {q["id"]: ESSAY for q in WQ})
s1 = db.query(models.ExamSubmission).filter_by(exam_id=EID, student_id=SIDS[1]).first()
s1.ai_status = "running"
s1.ai_review = json.dumps({"tries": 0, "started": datetime.utcnow()
                           .isoformat(timespec="seconds")})
db.commit()
CALLS.clear()
r = client.post(f"/api/public/exam/{TOKEN}/ai-grade", json={"key": K1})
ck("band qilingan (running) — ikkinchi AI chaqiruvi yo'q",
   (r.json()["status"], len(CALLS)), ("running", 0))
s1.ai_review = json.dumps({"tries": 0, "started": "2020-01-01T00:00:00"})
db.commit()
r = client.post(f"/api/public/exam/{TOKEN}/ai-grade", json={"key": K1})
ck("osilib qolgan (eski running) qayta baholanadi", r.json()["status"], "done")

# E'lon -> AI bandlari jadvalga tushadi
r = client.post(f"/api/exams/{EID}/online/publish", headers=HE)
ck("e'lon qilindi", r.status_code, 200)
res = {x["student_id"]: x for x in client.get(f"/api/exams/{EID}", headers=H)
       .json()["results"]}
ck("jadvalda: examiner bahosi 7.0 va AI bandi 5.0",
   (res[SIDS[0]]["band"], res[SIDS[1]]["band"]), (7.0, 5.0))

# E'londan keyin kelgan AI bahosi jadvalga o'zi yozilmaydi
s2 = models.ExamSubmission(exam_id=EID, student_id=SIDS[2], typed_name="Talaba 2",
                           status="placed",
                           answers=json.dumps({q["id"]: ESSAY for q in WQ}),
                           ai_status="pending", sub_key="k" * 16)
db.add(s2)
db.commit()
r = client.post(f"/api/exam-submissions/{s2.id}/ai-grade", headers=HE)
db.refresh(s2)
ck("e'londan keyin: AI bahosi bor, qog'oz bali bo'sh (examiner saqlaydi)",
   (s2.ai_status, s2.ai_score, s2.paper_score), ("done", 5.0, None))
res = {x["student_id"]: x for x in client.get(f"/api/exams/{EID}", headers=H)
       .json()["results"]}
ck("jadvalga yozilmadi", (res.get(SIDS[2]) or {}).get("band"), None)

# Kalit yo'q
PLAN["raise"] = RuntimeError("no-key")
s3 = models.ExamSubmission(exam_id=EID, student_id=None, typed_name="Mehmon",
                           status="pending",
                           answers=json.dumps({q["id"]: ESSAY for q in WQ}),
                           ai_status="pending", sub_key="z" * 16)
db.add(s3)
db.commit()
r = client.post(f"/api/public/exam/{TOKEN}/ai-grade", json={"key": "z" * 16})
db.refresh(s3)
ck("kalit yo'q -> no_key, ball bo'sh, xato matni saqlanmaydi",
   (r.json()["status"], s3.paper_score, json.loads(s3.ai_review)["error"]),
   ("no_key", None, "no_key"))
PLAN["raise"] = None

# Buzilgan javoblar (eski 20 000 belgi kesimi) — 0 qo'yilmaydi
s4 = models.ExamSubmission(exam_id=EID, student_id=None, typed_name="Buzuq",
                           status="pending", answers='{"q1": "abc',
                           ai_status="pending", sub_key="y" * 16)
db.add(s4)
db.commit()
CALLS.clear()
r = client.post(f"/api/public/exam/{TOKEN}/ai-grade", json={"key": "y" * 16})
db.refresh(s4)
ck("buzuq javoblar: error, ball yo'q, AI chaqirilmadi",
   (r.json()["status"], s4.paper_score, len(CALLS)), ("error", None, 0))

# Uzun insho endi JSON'ni buzmaydi
long_ans = {"a": "w " * 9000, "b": "x " * 9000}
ck("uzun javoblar JSON sifatida saqlanadi",
   isinstance(json.loads(exam_online._answers_json(long_ans)), dict), True)

ck("Listening mocki AI emas",
   exam_online._is_ai_writing(exam_online._load(mocks_of("ielts_listening")[0].parts)),
   False)

# ============================================================ C
print("\n=== C. XODIM SINOVI ===")
cat = client.get("/api/mock-practice/catalog", headers=H).json()
ielts = [bk for bk in cat["banks"] if bk["bank"] == "ielts"][0]
ck("sinov katalogi: L, R, W, S tartibi",
   [s["section"] for s in ielts["sections"]],
   ["listening", "reading", "writing", "speaking"])
wsec = [s for s in ielts["sections"] if s["section"] == "writing"][0]
ckey = wsec["variants"][0]["content_key"]
r = client.post("/api/mock-practice", headers=H,
                json={"content_key": ckey, "timed": False})
ck("sinov boshlandi", r.status_code, 200)
PID = r.json()["id"]
att = client.get(f"/api/mock-practice/{PID}", headers=H).json()
pq = [q for p in att["parts"] for q in p["questions"]]
PLAN["ielts"] = {0: [6, 6, 6, 6], 1: [6, 6, 6, 6]}
rv = client.post(f"/api/mock-practice/{PID}/submit", headers=H,
                 json={"answers": {q["id"]: ESSAY for q in pq}}).json()
ck("topshirildi: ai_writing, hali baholanmagan", (rv["ai_writing"], rv["ai"]),
   (True, None))
CALLS.clear()
rv = client.post(f"/api/mock-practice/{PID}/ai-grade", headers=H).json()
ck("AI bahosi: band 6.0", (rv["ai"]["status"], rv["ai"]["band"], rv["band"]),
   ("done", 6.0, 6.0))
rv = client.post(f"/api/mock-practice/{PID}/ai-grade", headers=H).json()
ck("idempotent: qayta AI chaqirilmaydi", len(CALLS), 1)
r = client.post(f"/api/mock-practice/{PID}/ai-grade", headers=HE)
ck("boshqa xodimning urinishi — 404", r.status_code, 404)

# ============================================================ D
print("\n=== D. MOCK TESTLAR JADVALI ===")
mb = client.get("/api/mock-banks", headers=HE).json()
ib = [x for x in mb if x["bank"] == "ielts"][0]
ck("tartib: Listening, Reading, Writing, Speaking",
   [s["section"] for s in ib["sections"]],
   ["listening", "reading", "writing", "speaking"])
ck("vaqt ko'rsatiladi", [s["time"] for s in ib["sections"]],
   ["30 daqiqa", "60 daqiqa", "60 daqiqa", "11–14 daqiqa"])
ck("Writing avtomat, Speaking examiner",
   [(s["section"], s["auto"]) for s in ib["sections"]][2:],
   [("writing", True), ("speaking", False)])
ck("xom ball matnlari yo'q",
   any("xom" in (s["grading"] or "").lower() for x in mb for s in x["sections"]),
   False)
ck("Writing: 2 topshiriq", [s["tasks"] for s in ib["sections"]][2], 2)

db.close()
print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
sys.exit(1 if fails else 0)
