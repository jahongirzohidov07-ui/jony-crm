"""USTOZ OYLIGI TO'LIQ HISOBOTI: filial -> guruh -> o'quvchi (2026-09-15).

Jahongir: "oqituvchilarga oyligini aynan qaysi oquvchi nechta kelgan
toliq hisoboti oquvchilar kesimida guruhlar kesimida oziniki korinsin
... 2ta filialda ishlasa filiallar kesimida korinsin".

Tekshiriladi:
  1. Ikki filial alohida, har birida guruh va o'quvchilar;
  2. O'quvchi bo'yicha keldi / kelmadi / sanalgan / summa;
  3. Guruhdan chiqqanning dumi sanalmaydi va bu ko'rsatiladi;
  4. Jami _teacher_earned() va ustozning moliya bo'limi bilan AYNAN teng;
  5. Ustoz o'zinikini ko'radi, boshqasinikini emas; rahbar ko'radi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "salary_breakdown_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles, billing                # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
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
PY, PM = (today.year, today.month - 1) if today.month > 1 else (today.year - 1, 12)

db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Bekobod 2")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
u_e = models.User(username="elena", password_hash=hash_password("x"),
                  full_name="Elena", role=roles.TEACHER, branch_id=B1)
u_b = models.User(username="bobur", password_hash=hash_password("x"),
                  full_name="Bobur", role=roles.TEACHER, branch_id=B2)
u_f = models.User(username="asos", password_hash=hash_password("x"),
                  full_name="Asoschi", role=roles.FOUNDER)
db.add_all([u_e, u_b, u_f]); db.commit()
elena = models.Teacher(full_name="Elena", is_active=1, branch_id=B1,
                       grade="middle", user_id=u_e.id)
bobur = models.Teacher(full_name="Bobur", is_active=1, branch_id=B2,
                       grade="middle", user_id=u_b.id)
db.add_all([elena, bobur]); db.commit()
db.add(models.TeacherBranch(teacher_id=elena.id, branch_id=B2)); db.commit()
EID, BID = elena.id, bobur.id


def group(name, br):
    g = models.Group(name=name, branch_id=br, teacher_id=EID,
                     lesson_price=40_000, standard_lessons_per_month=12,
                     monthly_fee=480_000, rate_manual=1,
                     teacher_rate_per_student=120_000)
    db.add(g); db.commit()
    return g


def student(name, g, br, status="active"):
    s = models.Student(full_name=name, branch_id=br, status=status,
                       group_id=g.id, enrolled_date=date(PY, PM, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    db.commit()
    return s


gA = group("Step 2 · ertalab", B1)
gB = group("Step 1 · kechki", B2)
ali = student("Ali", gA, B1)
vali = student("Vali", gA, B1)
sara = student("Sara", gB, B2)
for d in range(1, 13):
    la = models.Lesson(group_id=gA.id, date=date(PY, PM, d), teacher_id=EID, held=1)
    lb = models.Lesson(group_id=gB.id, date=date(PY, PM, d), teacher_id=EID, held=1)
    db.add_all([la, lb]); db.commit()
    db.add(models.Attendance(student_id=ali.id, lesson_id=la.id,
                             present=1 if d != 3 else 0))       # 11 keldi, 1 kelmadi
    # Vali 6-kungacha keldi, keyin kelmadi va guruhdan chiqdi
    db.add(models.Attendance(student_id=vali.id, lesson_id=la.id,
                             present=1 if d <= 6 else 0))
    db.add(models.Attendance(student_id=sara.id, lesson_id=lb.id, present=1))
db.commit()
v = db.query(models.Student).get(vali.id)
v.status = "archived"
db.query(models.StudentGroupLink).filter_by(student_id=vali.id).update({"active": 0})
db.commit()
start, end = billing.month_bounds(PY, PM)
earned = common._teacher_earned(db, EID, since=start, until=end)["amount"]
db.close()

H, TE, TB = tok("asos"), tok("elena"), tok("bobur")
URL = f"/api/teachers/{EID}/salary-breakdown?year={PY}&month={PM}"

print("=== 1. Ustoz o'zi ko'radi: filiallar ===")
r = client.get(URL, headers=TE)
ck("status 200", r.status_code, 200)
d = r.json()
ck("ikki filial", d["multi_branch"], True)
brs = {b["branch"]: b for b in d["branches"]}
ck("filial nomlari", sorted(brs), ["Bekobod 1", "Bekobod 2"])
ck("Bekobod 2 summasi", brs["Bekobod 2"]["amount"], 120_000)

print("\n=== 2. O'quvchilar kesimi ===")
ga = brs["Bekobod 1"]["groups"][0]
st = {s["student"]: s for s in ga["students"]}
ck("Ali: 11 keldi, 1 kelmadi", (st["Ali"]["present"], st["Ali"]["absent"]), (11, 1))
ck("Ali: 12 belgi sanaladi (kelmadi ham)", (st["Ali"]["counted"], st["Ali"]["amount"]), (12, 120_000))
ck("guruh darslari", ga["lessons"], 12)

print("\n=== 3. Chiqqan o'quvchining dumi ===")
ck("Vali: 6 sanalgan, 6 sanalmagan",
   (st["Vali"]["counted"], st["Vali"]["not_counted"]), (6, 6))
ck("Vali summasi 60 000", st["Vali"]["amount"], 60_000)
ck("jami sanalmagan", d["not_counted"], 6)

print("\n=== 4. Oylik bilan aynan teng ===")
ck("jami = _teacher_earned", d["amount"], earned)
ck("jami 300 000", d["amount"], 300_000)
fin = client.get("/api/my/finance", headers=TE).json()
mon = {m["period"]: m for m in fin["months"]}[f"{PY:04d}-{PM:02d}"]
ck("moliya bo'limidagi oy summasi bilan teng", d["amount"], mon["earned"])
ck("o'quvchilar ro'yxati 3 ta", len(d["students"]), 3)
ck("o'quvchilar yig'indisi = jami",
   round(sum(s["amount"] for s in d["students"]), 2), d["amount"])
ck("Sara filiali ko'rsatilgan",
   next(s["branches"] for s in d["students"] if s["student"] == "Sara"), "Bekobod 2")

print("\n=== 5. Ruxsatlar ===")
ck("boshqa ustoz ko'ra olmaydi", client.get(URL, headers=TB).status_code, 403)
ck("asoschi ko'radi", client.get(URL, headers=H).status_code, 200)
ck("yo'q ustoz — 404",
   client.get(f"/api/teachers/99999/salary-breakdown?year={PY}&month={PM}", headers=H).status_code, 404)
ck("noto'g'ri oy — 400",
   client.get(f"/api/teachers/{EID}/salary-breakdown?year={PY}&month=13", headers=H).status_code, 400)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
