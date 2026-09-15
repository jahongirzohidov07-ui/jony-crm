"""KO'P FILIALLI USTOZ OYLIGI (2026-09-15).

Jahongir: "Elena ustoz 2-3ta filialda ishlaydi lekin men bekobod 2
filialda avgust oyligini korsam yelena chiqmadi lekin dars otgan".

Sabab edi: oylik ro'yxatlari ustozni ASOSIY filiali (Teacher.branch_id)
bo'yicha tanlardi. Endi oylik GURUH filialiga tegishli.

Tekshiriladi (o'tgan oy — muhrlangan oy yo'li ham):
  1. Bekobod 2 tanlansa Elena chiqadi, summasi faqat Bekobod 2 guruhidan;
  2. Bekobod 1 da — faqat Bekobod 1 guruhidan;
  3. Barcha filiallarda — to'liq summa; filiallar yig'indisi = jami;
  4. /api/payroll va o'quvchi kesimi ham xuddi shunday;
  5. Berilgan pul filiallarga ulush bo'yicha bo'linadi (ikki marta emas);
  6. Filial rahbari o'z filialida boshqa filial ustozini ko'radi;
  7. Foyda-zarardagi ish haqi (_payroll_total) bilan bir xil.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "payroll_mb_test")
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

db.add_all([
    models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER),
    models.User(username="rahbar2", password_hash=hash_password("x"),
                full_name="Rahbar 2", role=roles.BRANCH_MANAGER, branch_id=B2),
])
db.commit()
elena = models.Teacher(full_name="Elena", is_active=1, branch_id=B1, grade="middle")
bobur = models.Teacher(full_name="Bobur", is_active=1, branch_id=B2, grade="middle")
db.add_all([elena, bobur]); db.commit()
db.add(models.TeacherBranch(teacher_id=elena.id, branch_id=B2)); db.commit()


def group(name, br, t, n_students):
    g = models.Group(name=name, branch_id=br, teacher_id=t.id,
                     lesson_price=40_000, standard_lessons_per_month=12,
                     monthly_fee=480_000, rate_manual=1,
                     teacher_rate_per_student=120_000)
    db.add(g); db.commit()
    kids = []
    for i in range(n_students):
        s = models.Student(full_name=f"{name} bola {i}", branch_id=br,
                           status="active", group_id=g.id,
                           enrolled_date=date(PY, PM, 1))
        db.add(s); db.commit()
        db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                       is_primary=1, active=1))
        kids.append(s)
    db.commit()
    for d in range(1, 13):
        les = models.Lesson(group_id=g.id, date=date(PY, PM, d),
                            teacher_id=t.id, held=1)
        db.add(les); db.commit()
        for s in kids:
            db.add(models.Attendance(student_id=s.id, lesson_id=les.id, present=1))
    db.commit()
    return g


# 1 yo'qlama = 120 000 / 12 = 10 000
group("E-B1", B1, elena, 2)        # 2 x 12 x 10 000 = 240 000
group("E-B2", B2, elena, 1)        # 1 x 12 x 10 000 = 120 000
group("Bob-B2", B2, bobur, 1)      # 120 000
db.add(models.TeacherPayment(teacher_id=elena.id, amount=90_000, kind="advance",
                             paid_on=date(PY, PM, 20), created_by="Asoschi"))
db.commit()
db.close()

H, BM2 = tok("asos"), tok("rahbar2")
Q = f"year={PY}&month={PM}"


def row(data, key="full_name", name="Elena"):
    return next((r for r in data["rows"] if r.get(key) == name), None)


print("=== 1-3. /api/reports/teacher-payroll ===")
r2 = client.get(f"/api/reports/teacher-payroll?{Q}&branch_id={B2}", headers=H).json()
e2 = row(r2)
ck("Bekobod 2 da Elena chiqadi", e2 is not None, True)
ck("Bekobod 2 summasi faqat shu filial guruhidan", e2 and e2["amount"], 120_000)
ck("faqat Bekobod 2 guruhi", e2 and [g["group"] for g in e2["groups"]], ["E-B2"])
ck("filial yozuvi", e2 and e2["branch"], "Bekobod 2 (asosiy: Bekobod 1)")
ck("Bekobod 2 jami = Elena + Bobur", r2["total"], 240_000)
r1 = client.get(f"/api/reports/teacher-payroll?{Q}&branch_id={B1}", headers=H).json()
ck("Bekobod 1 da Elena summasi", row(r1)["amount"], 240_000)
ck("Bobur Bekobod 1 da yo'q", row(r1, name="Bobur"), None)
ra = client.get(f"/api/reports/teacher-payroll?{Q}", headers=H).json()
ck("barcha filiallarda Elena to'liq", row(ra)["amount"], 360_000)
ck("filiallar yig'indisi = jami", r1["total"] + r2["total"], ra["total"])

print("\n=== 5. To'lov ulush bo'yicha ===")
ck("Bekobod 1 ulushi (2/3)", row(r1)["paid_amount"], 60_000)
ck("Bekobod 2 ulushi (1/3)", e2 and e2["paid_amount"], 30_000)
ck("barchada to'liq", row(ra)["paid_amount"], 90_000)

print("\n=== 4. /api/payroll (muhrlangan o'tgan oy) ===")
p2 = client.get(f"/api/payroll?{Q}&branch_id={B2}", headers=H).json()
ck("oy muhrlangan", p2["sealed"], True)
pe2 = row(p2)
ck("Bekobod 2 da Elena", pe2 is not None, True)
ck("earned = 120 000", pe2 and pe2["earned"], 120_000)
ck("paid ulushi", pe2 and pe2["paid"], 30_000)
pa = client.get(f"/api/payroll?{Q}", headers=H).json()
ck("barchada earned = 360 000", row(pa)["earned"], 360_000)
ck("balans filialga bo'linmaydi (ustoz kartasi)", pe2 and pe2["balance"], row(pa)["balance"])

sd2 = client.get(f"/api/reports/teacher-salary-detail?{Q}&branch_id={B2}", headers=H).json()
se2 = row(sd2, key="teacher")
ck("o'quvchi kesimida Bekobod 2 da Elena", se2 and se2["amount"], 120_000)
ck("o'quvchi kesimi — faqat shu filial bolalari", se2 and len(se2["students"]), 1)

print("\n=== 6. Filial rahbari ===")
rb = client.get(f"/api/reports/teacher-payroll?{Q}", headers=BM2).json()
ck("rahbar o'z filialida Elenani ko'radi", row(rb) and row(rb)["amount"], 120_000)
pb = client.get(f"/api/payroll?{Q}", headers=BM2).json()
ck("rahbar /api/payroll da ham", row(pb) and row(pb)["earned"], 120_000)

print("\n=== 7. Foyda-zarar bilan bir xil ===")
db = SessionLocal()
founder = db.query(models.User).filter_by(username="asos").first()
ck("Bekobod 2: _payroll_total = ro'yxat jami",
   common._payroll_total(db, founder, f"{PY:04d}-{PM:02d}", B2), r2["total"])
db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
