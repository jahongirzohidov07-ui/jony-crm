"""VAKANSIYALAR ANALITIKASI (2026-09-16).

Jahongir: "HR bitta vakansiyani nechi kunda yopayotganligini
hisobotlarda analitikasi kerak, nechta nomzoddan nechtasi ishga
olinayotganligi ham kerak".

Tekshiriladi:
  1. Har vakansiya: ochilgandan yopilgangacha kun, nomzod, suhbat, olindi;
  2. O'rtacha / mediana muddatga faqat xodim topilib yopilganlar kiradi;
  3. Ochiq vakansiya — necha kundan beri ochiq, muddati o'tganmi;
  4. Konversiya va "har N nomzoddan 1";
  5. Arizasi yo'q eski nomzod ham sanaladi, bir odam ikki marta emas;
  6. Lavozim kesimi va ruxsat.
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "hr_vacancy_report_test")
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


today = roles.local_today()
ago = lambda n: today - timedelta(days=n)   # noqa: E731

db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
db.add_all([
    models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER),
    models.User(username="hr", password_hash=hash_password("x"),
                full_name="HR", role=roles.HR_MANAGER),
    models.User(username="ustoz", password_hash=hash_password("x"),
                full_name="Ustoz", role=roles.TEACHER, branch_id=b.id),
])
db.commit()


def vacancy(title, role, opened, status="open", closed=None, reason=None,
            target=None):
    v = models.Vacancy(title=title, role=role, branch_id=b.id, status=status,
                       opened_on=opened, closed_at=closed, close_reason=reason,
                       target_close=target,
                       created_at=datetime.combine(opened, datetime.min.time()))
    db.add(v); db.commit()
    return v


def cand(v, name, stage, logs=(), app=True, closed=None):
    c = models.Candidate(full_name=name, vacancy_id=v.id, branch_id=b.id,
                         stage={"hired": "hired", "rejected": "rejected"}.get(stage, "interview"))
    db.add(c); db.commit()
    if app:
        a = models.CandidateApplication(candidate_id=c.id, vacancy_id=v.id,
                                        branch_id=b.id, stage=stage,
                                        stage_since=closed or today,
                                        closed_at=closed)
        db.add(a); db.commit()
        for st in ("new",) + tuple(logs):
            db.add(models.ApplicationStageLog(application_id=a.id, to_stage=st))
        db.commit()
    return c


# V1: 30 kun oldin ochildi, 10 kun oldin xodim topilib yopildi -> 20 kun
v1 = vacancy("Ingliz tili ustozi", roles.TEACHER, ago(30), "filled", ago(10), "filled")
cand(v1, "Aziz", "hired", logs=("interview", "demo", "hired"), closed=ago(12))
cand(v1, "Bekzod", "interview", logs=("interview",))
cand(v1, "Dilshod", "rejected", logs=("interview", "rejected"), closed=ago(15))
cand(v1, "Erkin", "rejected", logs=("rejected",), closed=ago(25))
# V2: 50 kun oldin ochildi, bugun yopildi -> 50 kun
v2 = vacancy("Ingliz tili ustozi (2)", roles.TEACHER, ago(50), "closed", today, "filled")
cand(v2, "Farruh", "hired", logs=("interview", "hired"), closed=today)
cand(v2, "G'ani", "new")
# V3: ochiq, 15 kundan beri, reja 5 kun oldin tugagan -> muddati o'tgan
v3 = vacancy("Administrator", roles.ADMINISTRATOR, ago(15), "interviewing",
             target=ago(5))
cand(v3, "Hasan", "screening")
cand(v3, "Ibrohim", "phone")
cand(v3, "Jamshid", "interview", logs=("interview",))
cand(v3, "Kamol (eski)", "interview", app=False)      # arizasi yo'q eski nomzod
# V4: ehtiyoj qolmadi — o'rtacha muddatga kirmaydi
vacancy("Qorovul", None, ago(8), "closed", ago(3), "no_need")
# V5: juda eski (davrdan oldin yopilgan) — ko'rinmaydi
vacancy("Eski vakansiya", None, ago(900), "closed", ago(800), "filled")
db.close()

H, HR, T = tok("asos"), tok("hr"), tok("ustoz")

print("=== 1. Har vakansiya ===")
r = client.get("/api/reports/hr-vacancies?months=12", headers=HR)
ck("HR ochadi", r.status_code, 200)
d = r.json()
rows = {x["title"]: x for x in d["rows"]}
ck("eski vakansiya ko'rinmaydi", "Eski vakansiya" in rows, False)
ck("V1 muddati 20 kun", rows["Ingliz tili ustozi"]["days"], 20)
ck("V1: 4 nomzod, 3 suhbatga yetdi, 1 olindi",
   (rows["Ingliz tili ustozi"]["candidates"], rows["Ingliz tili ustozi"]["interviewed"],
    rows["Ingliz tili ustozi"]["hired"]), (4, 3, 1))
ck("V1 konversiya 25%", rows["Ingliz tili ustozi"]["conversion"], 25.0)
ck("V1: birinchi xodim 18-kuni topildi", rows["Ingliz tili ustozi"]["first_hire_days"], 18)
ck("V2 muddati 50 kun", rows["Ingliz tili ustozi (2)"]["days"], 50)

print("\n=== 2. O'rtacha muddat ===")
s = d["summary"]
ck("xodim topilib yopilgan 2 ta", s["filled"], 2)
ck("o'rtacha 35 kun (qorovul kirmaydi)", s["avg_days_to_close"], 35.0)
ck("mediana 35", s["median_days_to_close"], 35.0)
ck("eng tez / eng uzoq", (s["fastest"], s["slowest"]), (20, 50))
ck("qorovul — yopilgan, lekin to'ldirilmagan",
   (rows["Qorovul"]["closed"], rows["Qorovul"]["filled"]), (True, False))
ck("yopilish sababi ko'rinadi", rows["Qorovul"]["close_reason"], "Ehtiyoj qolmadi")

print("\n=== 3. Ochiq vakansiya ===")
ck("ochiq 1 ta", s["open"], 1)
ck("15 kundan beri ochiq", rows["Administrator"]["days"], 15)
ck("muddati o'tgan", (rows["Administrator"]["overdue"], s["overdue"]), (True, 1))

print("\n=== 4-5. Konversiya ===")
ck("eski nomzod ham sanaldi (V3 = 4)", rows["Administrator"]["candidates"], 4)
ck("jami nomzod 10, olindi 2", (s["candidates"], s["hired"]), (10, 2))
ck("konversiya 20%", s["conversion"], 20.0)
ck("har 5 nomzoddan 1", s["candidates_per_hire"], 5.0)
ck("suhbatga yetgan 6 (V1 3 + V2 1 + V3 2)", s["interviewed"], 6)

print("\n=== 6. Lavozim kesimi va ruxsat ===")
pos = {x["label"]: x for x in d["by_position"]}
ustoz_label = roles.UZ_LABELS.get(roles.TEACHER)
ck("ustoz lavozimi: 2 vakansiya, o'rtacha 35 kun",
   (pos[ustoz_label]["vacancies"], pos[ustoz_label]["avg_days_to_close"]), (2, 35.0))
ck("ustoz lavozimi konversiyasi 2/6", pos[ustoz_label]["conversion"], 33.3)
ck("asoschi ochadi", client.get("/api/reports/hr-vacancies", headers=H).status_code, 200)
ck("ustoz ocholmaydi", client.get("/api/reports/hr-vacancies", headers=T).status_code, 403)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
