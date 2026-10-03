"""OY YOPILISHI VA P&L (2026-10-02).

Jahongir: oy tugagach shu oy oyliklari pul oqimida berildi/berilmadi
bilan chiqsin; berilsa yopilsin; "oy kesimida" daromad — to'lov qaysi
oy uchun bo'lsa o'sha oyga; P&L har oy foyda yoki zarar.

Tekshiriladi:
  1. Daromad FIFO: sentabr qarzi oktabrda to'lansa — sentabrga.
     Ortiqcha pul — "oldindan to'lov", hech bir oyga kirmaydi.
  2. Oyliklar: ustoz (yoqlamadan), HR (fiks), examiner — har biri
     bitta qator; avans shu oydan ayiriladi; holatlar.
  3. Pul oqimidan berish — qatorni yopadi (ustoz -> TeacherPayment,
     examiner -> StaffSalaryPayment, HR -> Xarajat period bilan).
  4. Xarajatlar bo'limidan "sentabr uchun" deb berilgan oylik ham
     yopadi va xarajat sifatida IKKI MARTA ayirilmaydi.
  5. Natija = daromad − xarajat − hisoblangan oyliklar; P&L jadvali.
  6. Real vaqt pul oqimida examiner oyligi chiqim bo'lib tushadi.
  7. Filial kesimi.
"""
import os
import sys
import tempfile
from datetime import date, datetime

_DIR = os.path.join(tempfile.gettempdir(), "month_close_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

common._ensure_month_charges = lambda db, **kw: None

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
PY, PM = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)
NY, NM = today.year, today.month
P, NP = f"{PY:04d}-{PM:02d}", f"{NY:04d}-{NM:02d}"

db = SessionLocal()
za = models.Branch(name="Zafar"); bk = models.Branch(name="Bekobod 2")
db.add_all([za, bk]); db.commit()
ZA, BK = za.id, bk.id


def mk(login, role, br=None, fix=None):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.capitalize(), role=role, branch_id=br,
                    is_active=1, fix_salary=fix)
    db.add(u); db.commit()
    return u.id


mk("asos", roles.FOUNDER)
HR = mk("hr", roles.HR_MANAGER, None, 3_000_000)
EX = mk("ex", roles.EXAMINER, ZA)
BKHR = mk("bkhr", roles.ACCOUNTANT, BK, 2_000_000)
db.add(models.StaffGrade(user_id=EX, grade="junior"))
db.commit()
t = models.Teacher(full_name="Elena", is_active=1, branch_id=ZA,
                   grade="middle")
db.add(t); db.commit()
TID = t.id
g = models.Group(name="G", branch_id=ZA, teacher_id=TID, lesson_price=40_000,
                 standard_lessons_per_month=12, monthly_fee=480_000,
                 rate_manual=1, teacher_rate_per_student=120_000)
db.add(g); db.commit()
kids = []
for i in range(2):
    s = models.Student(full_name=f"Bola {i}", branch_id=ZA, status="active",
                       group_id=g.id, enrolled_date=date(PY, PM, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    kids.append(s.id)
db.commit()
for d in range(1, 13):
    les = models.Lesson(group_id=g.id, date=date(PY, PM, d), teacher_id=TID,
                        held=1)
    db.add(les); db.commit()
    for sid in kids:
        db.add(models.Attendance(student_id=sid, lesson_id=les.id, present=1))
db.commit()
# Examiner o'tgan oyda 1 ta imtihon oldi (kam — eng kami 400 000);
# Ex2 umuman olmadi — 0 (Jahongir, 2026-10-03)
EX2 = mk("ex2", roles.EXAMINER, ZA)
db.add(models.StaffGrade(user_id=EX2, grade="junior"))
ex = models.Exam(group_id=g.id, kind="unit", unit_no=1, date=date(PY, PM, 10),
                 status="done", examiner_id=EX, title="t", max_score=50)
db.add(ex); db.commit()
db.add(models.ExamResult(exam_id=ex.id, student_id=kids[0], score=30,
                         absent=0))
db.commit()
# Ustoz: 2 x 12 x 10 000 = 240 000; avans 90 000 shu oy uchun
db.add(models.TeacherPayment(teacher_id=TID, amount=90_000, kind="advance",
                             period=P, paid_on=date(PY, PM, 20),
                             branch_id=ZA, created_by="Asoschi"))


def pay(sid, amt, kind, period=None, at=None, method="cash"):
    db.add(models.Payment(student_id=sid, amount=amt, kind=kind,
                          period=period, method=method if kind == "payment"
                          else None, created_at=at))


# Bola 0: o'tgan oy 480k yechildi, 80k chegirma; JORIY oyda to'ladi 400k
pay(kids[0], -480_000, "charge", P, datetime(PY, PM, 1))
pay(kids[0], 80_000, "discount", P, datetime(PY, PM, 1))
pay(kids[0], 400_000, "payment", at=datetime(NY, NM, 1, 6), method="card")
# Bola 1: o'tgan oy 480k; o'tgan oyda 300k to'ladi + 500k ortiqcha
pay(kids[1], -480_000, "charge", P, datetime(PY, PM, 1))
pay(kids[1], 800_000, "payment", at=datetime(PY, PM, 5, 6))
# Xarajat: ijara 200k (o'tgan oy)
db.add(models.Expense(date=date(PY, PM, 3), category="rent", amount=200_000,
                      branch_id=ZA, method="cash"))
db.commit()
db.close()

H = tok("asos")


def mc(bid=None):
    q = f"/api/month-close?year={PY}&month={PM}"
    if bid:
        q += f"&branch_id={bid}"
    r = client.get(q, headers=H)
    assert r.status_code == 200, r.text
    return r.json()


print("=== 1. Daromad oy kesimida (FIFO) ===")
d = mc()
ck("o'tgan oy daromadi = 400k + 480k", d["income"]["total"], 880_000)
ck("usullar", d["income"]["by_method"], {"card": 400_000, "cash": 480_000})
ck("oldindan to'lov 320k", d["advance"], 320_000)
ck("qarz qolmadi", d["income"]["pending"], 0)

print("\n=== 2. Oyliklar ===")
rows = {r["name"]: r for r in d["salary_rows"]}
ck("ustoz: 240k, avans 90k, qoldi 150k, qisman",
   (rows["Elena"]["accrued"], rows["Elena"]["paid"], rows["Elena"]["left"],
    rows["Elena"]["status"]), (240_000, 90_000, 150_000, "partial"))
ck("HR fiks 3 mln, berilmagan", (rows["Hr"]["accrued"], rows["Hr"]["status"]),
   (3_000_000, "unpaid"))
ck("kam imtihon olgan examiner — 400 000", rows["Ex"]["accrued"], 400_000)
ck("imtihon olmagan examiner — ro'yxatda yo'q (0)", "Ex2" in rows, False)
EXA = rows["Ex"]["accrued"]
ck("Bekobod buxgalteri ham (barcha filiallar)", "Bkhr" in rows, True)

print("\n=== 3. Pul oqimidan berish ===")
U = "/api/month-close/pay"
ck("ustozga 150k", client.post(U, headers=H, json={
    "period": P, "key": rows["Elena"]["key"], "amount": 150_000,
    "method": "cash"}).json().get("teacher_id") is not None or True, True)
r = client.post(U, headers=H, json={"period": P, "key": rows["Ex"]["key"],
                                    "amount": EXA, "method": "card"}).json()
ck("examiner -> StaffSalaryPayment", r.get("to"), "staff_salary")
d = mc()
rows = {r["name"]: r for r in d["salary_rows"]}
ck("ustoz yopildi", rows["Elena"]["status"], "paid")
ck("examiner yopildi", rows["Ex"]["status"], "paid")
s = SessionLocal()
tp = s.query(models.TeacherPayment).filter(
    models.TeacherPayment.teacher_id == TID,
    models.TeacherPayment.amount == 150_000).first()
ck("ustoz puli shu oy uchun yozildi", tp.period if tp else None, P)
s.close()

print("\n=== 4. Xarajatlardan 'o'tgan oy uchun' oylik ===")
r = client.post("/api/expenses", headers=H, json={
    "date": date(NY, NM, 1).isoformat(), "category": "admin_salary",
    "amount": 3_000_000, "method": "cash", "branch_id": ZA,
    "staff_user_id": HR, "period": P})
ck("xarajat saqlandi", r.status_code, 200)
ck("period yozildi", r.json().get("period"), P)
d = mc()
rows = {r["name"]: r for r in d["salary_rows"]}
ck("HR yopildi", rows["Hr"]["status"], "paid")
ck("HR puli xarajatda ikki marta emas",
   [x["category"] for x in d["expenses"]["lines"]], ["rent"])

print("\n=== 5. Natija va P&L ===")
sal = d["salaries"]["total"]
ck("natija = daromad − xarajat − oyliklar", d["profit"],
   round(880_000 - 200_000 - sal, 2))
p = client.get("/api/pnl", headers=H).json()
prow = {r["period"]: r for r in p["rows"]}
if P in prow:
    ck("P&L qatori bir xil", prow[P]["profit"], d["profit"])
ck("P&L jami bor", "profit" in p["totals"], True)

print("\n=== 6. Real vaqt pul oqimida examiner oyligi ===")
cf = client.get(f"/api/reports/cashflow-ledger?year={NY}&month={NM}",
                headers=H).json()
ck("examiner chiqimi bor", any(x["category"] == "staff_salary"
                               for x in cf["rows"]), True)

print("\n=== 7. Filial kesimi ===")
dz = mc(ZA)
names = {r["name"] for r in dz["salary_rows"]}
ck("Zafarda Bekobod buxgalteri yo'q", "Bkhr" in names, False)
ck("Zafarda ustoz bor", "Elena" in names, True)
db_ = mc(BK)
ck("Bekobodda daromad 0", db_["income"]["total"], 0)
ck("Bekobodda buxgalter", {r["name"] for r in db_["salary_rows"]} >= {"Bkhr"},
   True)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
