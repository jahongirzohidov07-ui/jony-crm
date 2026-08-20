"""BI panel + Biznes maslahatchi + so'rov-vazifa yopilishi (2026-08-20).

Jahongir: "menga shu narsa vazifalar bolimiga kelsin va vazifalardan
tasdiqlansan vazifa avtomat bajarilgan bo'lsin ... menga asoschi
uchun Biznes maslahatchi AI qoshib ber ... analitik bo'limini eng
zor BI texnologiyalari bilan".
"""
import os, sys
from datetime import date, datetime
os.environ["DATABASE_URL"] = "sqlite:////tmp/advbi.db"
if os.path.exists("/tmp/advbi.db"):
    os.remove("/tmp/advbi.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import student_app                                 # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


today = roles.local_today()
this_m = f"{today.year:04d}-{today.month:02d}"
db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
g = models.Group(name="G1", branch_id=BID, monthly_fee=400000,
                 lesson_price=50000, standard_lessons_per_month=12)
db.add(g); db.commit(); GID = g.id
s1 = models.Student(full_name="Faol Bola", branch_id=BID, status="active",
                    group_id=GID, enrolled_date=today.replace(day=1))
s2 = models.Student(full_name="Qarzdor Bola", branch_id=BID,
                    status="active", group_id=GID,
                    enrolled_date=today.replace(day=1))
db.add_all([s1, s2]); db.commit()
db.add_all([
    models.Payment(student_id=s1.id, amount=-400000, kind="charge",
                   period=this_m, created_by="avtomat"),
    models.Payment(student_id=s1.id, amount=400000, kind="payment",
                   method="cash", created_by="Admin",
                   created_at=datetime.utcnow()),
    models.Payment(student_id=s2.id, amount=-400000, kind="charge",
                   period=this_m, created_by="avtomat"),
    models.Expense(date=today, category="rent", amount=150000,
                   branch_id=BID, created_by="Admin"),
])
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="mol", full_name="Moliyachi",
                role="finance_director",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Admin", role="administrator",
                branch_id=BID, password_hash=hash_password("x"),
                is_active=1),
])
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


F, M, A = tok("asos"), tok("mol"), tok("adm")

print("=== 1. BI panel ===")
r = c.get("/api/analytics/bi", headers=F)
ck("200", r.status_code, 200)
d = r.json()
ck("faol 2 ta", d["kpi"]["active"], 2)
ck("tushum 400k", d["kpi"]["rev_this"], 400000)
ck("qarz 400k", d["kpi"]["debt_total"], 400000)
ck("foyda 250k", d["kpi"]["profit_this"], 250000)
ck("12 oy", len(d["revenue_by_month"]), 12)
ck("usul cash", d["method_split"][0]["value"], 400000)
ck("filial tushumi", d["branch_revenue"][0]["name"], "Bekobod 1")
ck("top guruh", d["top_groups"][0]["students"], 2)
r = c.get("/api/analytics/bi", headers=A)
ck("adminга yopiq", r.status_code, 403)

print("\n=== 2. Maslahatchi (asoschi) ===")
_calls = {}
def _fake(system, messages):
    _calls["system"] = system
    _calls["messages"] = messages
    return "Tushum 400 000 so'm — yaxshi start."
student_app._ai_reply = _fake
r = c.post("/api/founder/advisor", headers=F,
           json={"text": "Biznes qanday?", "history": []})
ck("200", r.status_code, 200)
ck("javob keldi", "400 000" in r.json()["reply"], True)
ck("kontekstda faol soni bor", '"active": 2' in _calls["system"], True)
ck("kontekstda tushum bor", '"rev_this": 400000' in _calls["system"], True)
r = c.post("/api/founder/advisor", headers=M, json={"text": "salom"})
ck("moliyachiga yopiq", r.status_code, 403)

print("\n=== 3. To'lov tuzatish so'rovi -> vazifa avtomat yopiladi ===")
db = SessionLocal()
pay = (db.query(models.Payment)
       .filter(models.Payment.kind == "payment").first())
PID = pay.id; db.close()
r = c.post(f"/api/payments/{PID}/fix-request", headers=A,
           json={"kind": "amount", "amount": 350000,
                 "reason": "summa noto'g'ri kiritildi"})
ck("so'rov ketdi", r.status_code, 200)
RID = r.json()["id"] if "id" in r.json() else r.json().get("request_id")
db = SessionLocal()
open_tasks = (db.query(models.Task)
              .filter(models.Task.title.like("To'lovni tuzatish%"),
                      models.Task.status == "new").count())
ck("tasdiqlovchilarga vazifa tushdi (2 ta)", open_tasks, 2)
db.close()
r = c.post(f"/api/payments/fix-requests/{RID}/approve", headers=F, json={})
ck("tasdiqlandi", r.status_code, 200)
db = SessionLocal()
left = (db.query(models.Task)
        .filter(models.Task.title.like("To'lovni tuzatish%"),
                ~models.Task.status.in_(("done", "cancelled")))).count()
ck("BARCHA vazifalar yopildi", left, 0)
t = (db.query(models.Task)
     .filter(models.Task.title.like("To'lovni tuzatish%")).first())
ck("natija yozildi", "Tasdiqlandi" in (t.result or ""), True)
pay = db.query(models.Payment).get(PID)
ck("summa o'zgardi", abs(pay.amount), 350000)
db.close()

print("\n=== 4. Chegirma so'rovi -> vazifalar yopiladi ===")
db = SessionLocal(); sid = db.query(models.Student).first().id; db.close()
r = c.post("/api/discounts", headers=A,
           json={"student_id": sid, "kind": "grant", "percent": 20,
                 "reason": "natijasi uchun"})
ck("so'rov ketdi", r.status_code, 200)
DID = r.json()["id"]
db = SessionLocal()
n_open = (db.query(models.Task)
          .filter(models.Task.title.like(f"Chegirma so'rovi #{DID}%"),
                  models.Task.status == "new").count())
ck("vazifalar bor", n_open >= 1, True)
db.close()
r = c.post(f"/api/discounts/{DID}/approve", headers=F,
           json={"approve": True})
ck("tasdiqlandi", r.status_code, 200)
db = SessionLocal()
left = (db.query(models.Task)
        .filter(models.Task.title.like(f"Chegirma so'rovi #{DID}%"),
                ~models.Task.status.in_(("done", "cancelled")))).count()
ck("chegirma vazifalari ham yopildi", left, 0)
db.close()

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
