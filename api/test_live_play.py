"""JONLI O'YIN (Kahoot uslubi) + DARS REJALARI, 2026-09-18.

Jahongir: "kahoot korinishidagi oyinlar ... hamma togri topgan bilan
kim tez bossa shu oldinga chiqadigan achkoni koproq beradigan bolsin".
Tekshiradi: reja ro'yxati, o'yin ochish, PIN bilan loginsiz kirish,
savol oqimi, tez to'g'ri javob ko'proq ball olishi, reyting.
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
db.add_all([
    models.User(username="ustoz", password_hash=hash_password("x"),
                full_name="Ustoz", role=roles.TEACHER, branch_id=b1.id),
    models.User(username="hr", password_hash=hash_password("x"),
                full_name="HR", role=roles.HR_MANAGER, branch_id=b1.id),
])
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


def game_questions(gid):
    db = SessionLocal()
    qs = json.loads(db.query(models.LiveGame).get(gid).questions)
    db.close()
    return qs


T = tok("ustoz")

# --- Dars rejalari
r = c.get("/api/plans", headers=T)
ck("plans 200", r.status_code, 200)
ck("plans: IELTS 1.0 28 dars", len(r.json()[0]["lessons"]), 28)
r = c.get("/api/plans/ielts_1_0/23", headers=T)
ck("plan 23 conjunctions", "CONJUNCTIONS" in r.json()["title"], True)
ck("plan 23 CORE 20", len(r.json()["vocab"]["core"]), 20)
ck("HR ga reja yopiq", c.get("/api/plans", headers=tok("hr")).status_code, 403)

# --- O'yin ochish
r = c.post("/api/live/games", json={"course": "ielts_1_0", "lesson_no": 23,
                                    "mode": "mixed", "count": 6, "seconds": 20},
           headers=T)
ck("game create 200", r.status_code, 200)
g = r.json()
gid = g["id"]
ck("lobby", g["status"], "lobby")
ck("6 savol", g["total"], 6)
ck("PIN 6 xonali", len(g["code"]), 6)
ck("HR o'yin ocholmaydi", c.post("/api/live/games", json={
    "course": "ielts_1_0", "lesson_no": 1}, headers=tok("hr")).status_code, 403)

# har rejimda savol tuziladi
for mode in ("vocab", "vocab40", "grammar"):
    rr = c.post("/api/live/games", json={"course": "ielts_1_0", "lesson_no": 5,
                                         "mode": mode, "count": 10}, headers=T)
    ck(f"mode {mode} savol bor", rr.status_code == 200 and rr.json()["total"] > 0, True)
    c.post(f"/api/live/games/{rr.json()['id']}/end", headers=T)

# --- Loginsiz kirish
r = c.post("/api/live/join", json={"code": g["code"], "nickname": "Aziz"})
ck("join Aziz", r.status_code, 200)
t1 = r.json()["token"]
r = c.post("/api/live/join", json={"code": g["code"], "nickname": "aziz"})
ck("ism band", r.status_code, 400)
t2 = c.post("/api/live/join", json={"code": g["code"], "nickname": "Bobur"}).json()["token"]
ck("noto'g'ri PIN", c.post("/api/live/join", json={"code": "000000", "nickname": "Xurshid"}).status_code, 404)
ck("lobbyda o'yinchi 2", len(c.get(f"/api/live/games/{gid}/host", headers=T).json()["players"]), 2)
ck("o'quvchi lobby", c.get(f"/api/live/p/{t1}").json()["status"], "lobby")

# --- Boshlash
s = c.post(f"/api/live/games/{gid}/next", headers=T).json()
ck("question 0", (s["status"], s["q_index"]), ("question", 0))
ck("boshlangach kirib bo'lmaydi",
   c.post("/api/live/join", json={"code": g["code"], "nickname": "Kech"}).status_code, 400)
ps = c.get(f"/api/live/p/{t1}").json()
ck("o'quvchiga savol", len(ps["question"]["options"]), 4)
ck("to'g'ri javob o'quvchiga ketmaydi", "correct" in ps["question"], False)

qs = game_questions(gid)
correct0 = qs[0]["correct"]

# Aziz darhol to'g'ri javob beradi, Bobur 10 soniya kechikib to'g'ri
a1 = c.post(f"/api/live/p/{t1}/answer", json={"q_index": 0, "option": correct0}).json()
ck("Aziz to'g'ri", a1["correct"], True)
ck("Aziz ~1000 ball", a1["points"] >= 950, True)
db = SessionLocal()
game = db.query(models.LiveGame).get(gid)
game.q_started_at = datetime.utcnow() - timedelta(seconds=10)
db.commit(); db.close()
a2 = c.post(f"/api/live/p/{t2}/answer", json={"q_index": 0, "option": correct0}).json()
ck("Bobur to'g'ri lekin sekin", a2["correct"] and 700 <= a2["points"] <= 800, True)
ck("Aziz > Bobur", a1["points"] > a2["points"], True)
ck("ikkinchi javob rad", c.post(f"/api/live/p/{t1}/answer", json={"q_index": 0, "option": 0}).status_code, 400)

h = c.get(f"/api/live/games/{gid}/host", headers=T).json()
ck("javob berdi 2", h["answered"], 2)
ck("savol paytida correct yashirin", h["correct"], None)

# --- Natija
s = c.post(f"/api/live/games/{gid}/next", headers=T).json()
ck("reveal", s["status"], "reveal")
ck("reveal correct", s["correct"], correct0)
ck("reyting Aziz 1-o'rin", s["players"][0]["nickname"], "Aziz")
pr = c.get(f"/api/live/p/{t2}").json()
ck("o'quvchi reveal", (pr["status"], pr["reveal"]["is_correct"], pr["rank"]), ("reveal", True, 2))
ck("reveal paytida javob rad", c.post(f"/api/live/p/{t1}/answer", json={"q_index": 0, "option": 0}).status_code, 400)

# 2-savol: Aziz noto'g'ri, Bobur javob bermaydi
s = c.post(f"/api/live/games/{gid}/next", headers=T).json()
ck("question 1", (s["status"], s["q_index"]), ("question", 1))
qs = game_questions(gid)
w = (qs[1]["correct"] + 1) % 4
a = c.post(f"/api/live/p/{t1}/answer", json={"q_index": 1, "option": w}).json()
ck("noto'g'ri 0 ball", (a["correct"], a["points"]), (False, 0))
ck("eski savolga javob rad", c.post(f"/api/live/p/{t2}/answer", json={"q_index": 0, "option": 0}).status_code, 400)

# qolgan savollarni o'tkazib yuborib tugatamiz
for _ in range(20):
    s = c.post(f"/api/live/games/{gid}/next", headers=T).json()
    if s["status"] == "ended":
        break
ck("ended", s["status"], "ended")
pe = c.get(f"/api/live/p/{t1}").json()
ck("yakun: top ro'yxat", len(pe["top"]), 2)
ck("PIN bo'shadi", c.post("/api/live/join", json={"code": g["code"], "nickname": "Yusuf"}).status_code, 404)
ck("mening o'yinlarim", len(c.get("/api/live/games", headers=T).json()) >= 1, True)

print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
