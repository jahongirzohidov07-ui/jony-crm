"""JONLI O'YIN (Kahoot uslubi) + DARS REJALARI, 2026-09-18.

Jahongir: "kahoot korinishidagi oyinlar ... hamma togri topgan bilan
kim tez bossa shu oldinga chiqadigan achkoni koproq beradigan bolsin";
"savollar soni kamida 20ta ... ustozlar qaysi guruhga jonatayotgnaini
tanlasin ... o'quvchilar royxatidagi ism familyalardan birini
tanlashsin ... Kahoot natijalari esa exam bo'limida qolishi kerak. Coin
avtomat berilsin, 100% ishlagan hammaga 3 coin ... 1-o'ringa 3 coin,
2-oringa 2 coin 3-oringa 1 coin".
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "live_play_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b1 = models.Branch(name="Bekobod 1")
db.add(b1); db.commit()
u_t = models.User(username="ustoz", password_hash=hash_password("x"),
                  full_name="Ustoz", role=roles.TEACHER, branch_id=b1.id)
u_o = models.User(username="ustoz2", password_hash=hash_password("x"),
                  full_name="Boshqa Ustoz", role=roles.TEACHER, branch_id=b1.id)
u_r = models.User(username="rus", password_hash=hash_password("x"),
                  full_name="Rus Ustoz", role=roles.TEACHER, branch_id=b1.id)
db.add_all([u_t, u_o, u_r,
            models.User(username="hr", password_hash=hash_password("x"),
                        full_name="HR", role=roles.HR_MANAGER, branch_id=b1.id),
            models.User(username="sup", password_hash=hash_password("x"),
                        full_name="Support", role=roles.SUPPORT_TEACHER, branch_id=b1.id),
            models.User(username="exam", password_hash=hash_password("x"),
                        full_name="Examiner", role=roles.EXAMINER, branch_id=b1.id),
            models.User(username="adm", password_hash=hash_password("x"),
                        full_name="Admin", role=roles.ADMINISTRATOR, branch_id=b1.id)])
db.commit()
t1 = models.Teacher(full_name="Ustoz", user_id=u_t.id, branch_id=b1.id, subject="english")
t2 = models.Teacher(full_name="Boshqa Ustoz", user_id=u_o.id, branch_id=b1.id, subject="english")
t3 = models.Teacher(full_name="Rus Ustoz", user_id=u_r.id, branch_id=b1.id, subject="russian")
db.add_all([t1, t2, t3]); db.commit()
g1 = models.Group(name="IELTS A1", branch_id=b1.id, teacher_id=t1.id, lesson_price=50000,
                  standard_lessons_per_month=12, monthly_fee=600000)
g2 = models.Group(name="Boshqa guruh", branch_id=b1.id, teacher_id=t2.id, lesson_price=50000,
                  standard_lessons_per_month=12, monthly_fee=600000)
db.add_all([g1, g2]); db.commit()
studs = [models.Student(full_name=n, branch_id=b1.id, status="active", group_id=g1.id)
         for n in ("Aziz Karimov", "Bobur Aliyev", "Dilnoza Rahimova", "Erkin Yusupov")]
db.add_all(studs); db.commit()
SID = {s.full_name.split()[0]: s.id for s in studs}
G1, G2 = g1.id, g2.id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


def game_questions(gid):
    db = SessionLocal()
    qs = json.loads(db.query(models.LiveGame).get(gid).questions)
    db.close()
    return qs


def set_started(gid, seconds_ago):
    db = SessionLocal()
    game = db.query(models.LiveGame).get(gid)
    game.q_started_at = datetime.utcnow() - timedelta(seconds=seconds_ago)
    db.commit(); db.close()


T = tok("ustoz")

# --- Dars rejalari
r = c.get("/api/plans", headers=T)
ck("plans 200", r.status_code, 200)
ck("plans: 7 daraja", [x["title"] for x in r.json()][::6], ["IELTS 1.0", "IELTS 7.0 - IELTS GRADUATION"])
ck("plans: IELTS 1.0 28 dars", (r.json()[0]["cefr"], len(r.json()[0]["lessons"]), r.json()[0]["ready"]), ("A1", 28, True))
ck("plans: IELTS 2.0 25 dars tayyor", (len(r.json()[1]["lessons"]), r.json()[1]["ready"]), (25, True))
ck("plans: IELTS 3.0 26 dars tayyor", (len(r.json()[2]["lessons"]), r.json()[2]["ready"]), (26, True))
ck("plans: IELTS 4.0 25 dars tayyor", (len(r.json()[3]["lessons"]), r.json()[3]["ready"]), (25, True))
ck("tayyor dars 200 (2.0 1-dars)", c.get("/api/plans/ielts_2_0/1", headers=T).status_code, 200)
ck("5.0 1-dars ochiladi", c.get("/api/plans/ielts_5_0/1", headers=T).status_code, 200)
ck("5.0 tayyor bo'lmagan dars 404", c.get("/api/plans/ielts_5_0/48", headers=T).status_code, 404)
ck("plans: IELTS 5.0 48 mavzu (Introduction 1-35 + Writing 36-48)", (len(r.json()[4]["lessons"]), r.json()[4]["lessons"][0]["title"]), (48, "Reading: Paraphrases"))
ck("plans: IELTS 5.0 darslar tayyorlanmoqda", r.json()[4]["ready_count"] >= 1, True)
r = c.get("/api/plans/ielts_1_0/18", headers=T)
ck("plan 18 conjunctions (yangi tartib)", "CONJUNCTIONS" in r.json()["title"], True)
ck("HR ga reja yopiq", c.get("/api/plans", headers=tok("hr")).status_code, 403)
for tier, mn in (("20", 20), ("40", 40), ("60", 60)):
    rp = c.get(f"/api/plans/ielts_1_0/23/vocab.pdf?tier={tier}", headers=T)
    ck(f"lug'at PDF {tier}", (rp.status_code, rp.headers.get("content-type"), rp.content[:4] == b"%PDF",
                             len(rp.content) > 20000), (200, "application/pdf", True, True))
ck("lug'at PDF HR ga yopiq", c.get("/api/plans/ielts_1_0/23/vocab.pdf", headers=tok("hr")).status_code, 403)
# Faqat ingliz tili ustozlariga (Jahongir: "barcha ingliz til ustozlariga
# chiqsin boshqa ustozlarga chiqmasin")
ck("rus tili ustoziga ham reja ochiq (2026-09-18)", c.get("/api/plans", headers=tok("rus")).status_code, 200)
_m = c.get("/api/plan-media/ielts5_01_friendliest_city.jpg", headers=T)
ck("5.0 material rasmi ustozga ochiladi", (_m.status_code, _m.headers.get("content-type")), (200, "image/jpeg"))
ck("material rasmi tokensiz yopiq", c.get("/api/plan-media/ielts5_01_friendliest_city.jpg").status_code in (401, 403), True)
ck("material nomi tekshiriladi", c.get("/api/plan-media/..%2Fielts_1_0.json", headers=T).status_code, 404)
ck("supportga material yopiq", c.get("/api/plan-media/ielts5_01_friendliest_city.jpg", headers=tok("sup")).status_code, 403)
for _u in ("sup", "exam", "adm"):
    ck(f"{_u}: dars rejalari yopiq", c.get("/api/plans", headers=tok(_u)).status_code, 403)
ck("me: ingliz ustozi bayrog'i", c.get("/api/me", headers=T).json().get("english_teacher"), True)
ck("me: rus ustozi bayrog'i", c.get("/api/me", headers=tok("rus")).json().get("english_teacher"), False)

# --- Guruhlar: ustoz faqat o'zinikini ko'radi
gr = c.get("/api/live/groups", headers=T).json()
ck("ustoz guruhlari", [g["name"] for g in gr], ["IELTS A1"])
ck("guruh o'quvchilari 4", len(gr[0]["students"]), 4)

# --- O'yin ochish: guruh majburiy, kamida 20 savol
ck("guruhsiz ochilmaydi", c.post("/api/live/games", json={
    "course": "ielts_1_0", "lesson_no": 23}, headers=T).status_code, 400)
ck("boshqa ustoz guruhi bilan ochilmaydi", c.post("/api/live/games", json={
    "course": "ielts_1_0", "lesson_no": 23, "group_id": G2}, headers=T).status_code, 403)
r = c.post("/api/live/games", json={"course": "ielts_1_0", "lesson_no": 23, "group_id": G1,
                                    "mode": "mixed", "count": 5, "seconds": 20}, headers=T)
ck("game create 200", r.status_code, 200)
g = r.json()
gid = g["id"]
ck("lobby", g["status"], "lobby")
ck("5 so'ralsa ham kamida 20 savol", g["total"], 20)
ck("guruh nomi", g["group"], "IELTS A1")
for mode, n in (("vocab", 20), ("vocab40", 40), ("grammar", 25)):
    rr = c.post("/api/live/games", json={"course": "ielts_1_0", "lesson_no": 5, "group_id": G1,
                                         "mode": mode, "count": n}, headers=T)
    ck(f"mode {mode}: {n} savol", (rr.status_code, rr.json().get("total")), (200, n))
    c.post(f"/api/live/games/{rr.json()['id']}/end", headers=T)

# --- Loginsiz kirish: ro'yxatdan tanlash yoki boshqa ism
lob = c.get(f"/api/live/lobby/{g['code']}").json()
ck("lobby ro'yxati", ([s["name"] for s in lob["students"]][:2], lob["group"]),
   (["Aziz Karimov", "Bobur Aliyev"], "IELTS A1"))
ta = c.post("/api/live/join", json={"code": g["code"], "student_id": SID["Aziz"]}).json()
ck("Aziz ro'yxatdan", ta["nickname"], "Aziz Karimov")
ck("Aziz ikkinchi marta yo'q", c.post("/api/live/join", json={"code": g["code"], "student_id": SID["Aziz"]}).status_code, 400)
ck("lobbyda Aziz band", [s["taken"] for s in c.get(f"/api/live/lobby/{g['code']}").json()["students"]][0], True)
tb = c.post("/api/live/join", json={"code": g["code"], "student_id": SID["Bobur"]}).json()["token"]
td = c.post("/api/live/join", json={"code": g["code"], "student_id": SID["Dilnoza"]}).json()["token"]
tm = c.post("/api/live/join", json={"code": g["code"], "nickname": "Mehmon"}).json()["token"]
ck("begona o'quvchi id", c.post("/api/live/join", json={"code": g["code"], "student_id": 99999}).status_code, 400)
ck("noto'g'ri PIN", c.post("/api/live/join", json={"code": "000000", "nickname": "Xurshid"}).status_code, 404)
ta = ta["token"]

# --- O'yin: Aziz hammasini to'g'ri va tez; Bobur hammasini to'g'ri, sekin;
#     Dilnoza yarmini; Mehmon hammasini to'g'ri (coin yo'q)
qs = game_questions(gid)
s = c.post(f"/api/live/games/{gid}/next", headers=T).json()
ck("question 0", (s["status"], s["q_index"]), ("question", 0))
ck("boshlangach kirib bo'lmaydi", c.post("/api/live/join", json={"code": g["code"], "student_id": SID["Erkin"]}).status_code, 400)
ps = c.get(f"/api/live/p/{ta}").json()
ck("to'g'ri javob o'quvchiga ketmaydi", "correct" in ps["question"], False)
# Chiqib ketib qayta kirish (Jahongir): Dilnoza 0-savol paytida qayta
# kiradi -> yangi token, 0-savol avtomat XATO, javob berolmaydi.
rj = c.post("/api/live/join", json={"code": g["code"], "student_id": SID["Dilnoza"]})
ck("qayta kirish 200 + reconnected", (rj.status_code, rj.json().get("reconnected")), (200, True))
td_old, td = td, rj.json()["token"]
ck("eski token o'ldi", c.get(f"/api/live/p/{td_old}").status_code, 404)
ck("joriy savol avtomat xato", c.post(f"/api/live/p/{td}/answer", json={"q_index": 0, "option": qs[0]["correct"]}).status_code, 400)
ck("qayta kirganda answered=-1", c.get(f"/api/live/p/{td}").json()["answered"], -1)
for i, q in enumerate(qs):
    if i:
        s = c.post(f"/api/live/games/{gid}/next", headers=T).json()   # reveal -> question i
        assert s["status"] == "question" and s["q_index"] == i, s
    a1 = c.post(f"/api/live/p/{ta}/answer", json={"q_index": i, "option": q["correct"]}).json()
    set_started(gid, 10)
    a2 = c.post(f"/api/live/p/{tb}/answer", json={"q_index": i, "option": q["correct"]}).json()
    c.post(f"/api/live/p/{tm}/answer", json={"q_index": i, "option": q["correct"]})
    c.post(f"/api/live/p/{td}/answer", json={"q_index": i, "option": q["correct"] if i % 2 else (q["correct"] + 1) % 4})
    if i == 0:
        ck("Aziz ~1000 ball", a1["points"] >= 950, True)
        ck("Bobur sekin 700–800", 700 <= a2["points"] <= 800, True)
        ck("ikkinchi javob rad", c.post(f"/api/live/p/{ta}/answer", json={"q_index": 0, "option": 0}).status_code, 400)
    s = c.post(f"/api/live/games/{gid}/next", headers=T).json()   # -> reveal
    assert s["status"] == "reveal", s
    if i == 0:
        ck("reveal correct", s["correct"], qs[0]["correct"])
        ck("reveal paytida javob rad", c.post(f"/api/live/p/{ta}/answer", json={"q_index": 0, "option": 0}).status_code, 400)
s = c.post(f"/api/live/games/{gid}/next", headers=T).json()   # oxirgi reveal -> ended
ck("ended", s["status"], "ended")
ck("reyting: Aziz 1-o'rin", s["players"][0]["nickname"], "Aziz Karimov")
ck("exam yaratildi", bool(s["exam_id"]), True)

# --- Coin: 100% -> 3; 1-o'rin +3, 2-o'rin +2, 3-o'rin +1; mehmonga yo'q
by = {p["nickname"]: p for p in s["players"]}
PL = {1: 3, 2: 2, 3: 1}
ck("Aziz: 100% + 1-o'rin = 6 coin", (by["Aziz Karimov"]["correct"], by["Aziz Karimov"]["coins"]), (20, 6))
ck("Bobur 100% + o'rin bonusi", by["Bobur Aliyev"]["coins"], 3 + PL.get(by["Bobur Aliyev"]["rank"], 0))
ck("Mehmonga coin yo'q", by["Mehmon"]["coins"], 0)
ck("Dilnoza 50%: faqat o'rin bonusi", (by["Dilnoza Rahimova"]["correct"], by["Dilnoza Rahimova"]["coins"]),
   (10, PL.get(by["Dilnoza Rahimova"]["rank"], 0)))
pe = c.get(f"/api/live/p/{ta}").json()
ck("o'quvchi yakuni: coin", (pe["status"], pe["coins"], pe["linked"], pe["correct"]), ("ended", 6, True, 20))
ck("mehmon yakuni: linked=False", c.get(f"/api/live/p/{tm}").json()["linked"], False)

db = SessionLocal()
exam = db.query(models.Exam).get(s["exam_id"])
ck("exam kind/guruh/status", (exam.kind, exam.group_id, exam.status, exam.max_score), ("kahoot", G1, "done", 20.0))
res = {r.student_id: r for r in db.query(models.ExamResult).filter(models.ExamResult.exam_id == exam.id).all()}
ck("exam natijalari 3 o'quvchi (mehmon yo'q)", len(res), 3)
ck("Aziz natijasi", (res[SID["Aziz"]].score, res[SID["Aziz"]].percent, res[SID["Aziz"]].coins), (20.0, 100.0, 6))
coins = {e.student_id: e.amount for e in db.query(models.CoinEntry).filter(models.CoinEntry.source == "kahoot").all()}
ck("coin yozuvlari", (coins.get(SID["Aziz"]), coins.get(SID["Bobur"]) == by["Bobur Aliyev"]["coins"], SID["Erkin"] in coins), (6, True, False))
n_coin_rows = len(coins)
db.close()
ck("guruh imtihonlarida ko'rinadi", any(e["kind"] == "kahoot" for e in c.get(f"/api/groups/{G1}/exams", headers=T).json()), True)
# ikkinchi marta tugatilsa — coin takrorlanmaydi
c.post(f"/api/live/games/{gid}/end", headers=T)
db = SessionLocal()
ck("coin bir marta", db.query(models.CoinEntry).filter(models.CoinEntry.source == "kahoot").count(), n_coin_rows)
db.close()
ck("PIN bo'shadi", c.post("/api/live/join", json={"code": g["code"], "nickname": "Yusuf"}).status_code, 404)

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
