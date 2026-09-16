"""USTOZ OYLIGI XARAJATLAR RO'YXATIDA (2026-09-16).

Jahongir: "xodimni tanlab ustozni tanlab oylik berganimni kiritsam uni
mamuriy xodimlar oyligi degan katigoriyada ketyabdi bu ustoz oyligi
kategoriyasi ketishi kerak va ustozni ismi korinishi kerak".

Tekshiriladi:
  1. Oylik ro'yxatida ko'p filialli ustoz USTOZ bo'lib chiqadi, akkaunti
     alohida "xodim" bo'lib takrorlanmaydi;
  2. Ustozning akkaunti (staff_user_id) tanlansa ham pul ustoz oyligiga;
  3. Ro'yxatda "Ustoz oyligi" qatori ismi bilan (with_teacher=1),
     xarajat jadvaliga qo'shilmaydi;
  4. Xato "Ma'muriy xodim oyligi" yozuvini tahrirlab ustoz tanlansa —
     ustoz oyligiga ko'chadi, xarajatdan chiqadi;
  5. Ma'muriy xodimga oylik avvalgidek xarajat bo'lib qoladi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "expense_teacher_salary_test")
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


TODAY = date.today()
Y, M = TODAY.year, TODAY.month
db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Bekobod 2")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
f = models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER)
u_s = models.User(username="sardor", password_hash=hash_password("x"),
                  full_name="Sardor Teacher", role=roles.TEACHER, branch_id=B1)
u_i = models.User(username="iroda", password_hash=hash_password("x"),
                  full_name="Iroda Admin", role=roles.ADMINISTRATOR, branch_id=B1)
db.add_all([f, u_s, u_i]); db.commit()
# Sardorning ustoz kartasi asosiy filiali BEKOBOD 2, Bekobod 1 qo'shimcha
t = models.Teacher(full_name="Sardor Teacher", is_active=1, branch_id=B2,
                   user_id=u_s.id)
db.add(t); db.commit()
db.add(models.TeacherBranch(teacher_id=t.id, branch_id=B1)); db.commit()
TID, SUID, IUID = t.id, u_s.id, u_i.id
db.close()

H = tok("asos")


def counts():
    s = SessionLocal()
    out = (s.query(models.Expense).count(),
           s.query(models.TeacherPayment).filter_by(teacher_id=TID).count())
    s.close()
    return out


print("=== 1. Oylik ro'yxati: Bekobod 1 ===")
rows = client.get(f"/api/expenses/staff?branch_id={B1}", headers=H).json()["rows"]
sardor = [r for r in rows if r["name"] == "Sardor Teacher"]
ck("Sardor bitta marta chiqadi", len(sardor), 1)
ck("ustoz sifatida (oylik kartasiga)", (sardor[0]["teacher_id"], sardor[0]["to_salary_card"]),
   (TID, True))
ck("administrator xodim sifatida", any(r["name"] == "Iroda Admin" and not r["teacher_id"]
                                        for r in rows), True)

print("\n=== 2. Ustozning AKKAUNTI tanlansa ham — ustoz oyligi ===")
r = client.post("/api/expenses", headers=H, json={
    "date": TODAY.isoformat(), "category": "admin_salary", "amount": 1_700_000,
    "staff_user_id": SUID, "method": "cash", "branch_id": B1})
ck("qabul qilindi", r.status_code, 200)
ck("turi — ustoz oyligi", r.json()["category"], "teacher_salary")
ck("xarajatga yozilmadi, oylik kartasiga yozildi", counts(), (0, 1))

print("\n=== 3. Ro'yxatda ismi bilan ===")
lst = client.get(f"/api/expenses?year={Y}&month={M}&with_teacher=1", headers=H).json()
tr = [e for e in lst if e["category"] == "teacher_salary"]
ck("bitta ustoz oyligi qatori", len(tr), 1)
ck("ismi ko'rinadi", tr[0]["note"].startswith("Sardor Teacher"), True)
ck("id manfiy (oylik kartasida)", tr[0]["id"] < 0, True)
ck("teacher_id bor", tr[0]["teacher_id"], TID)
plain = client.get(f"/api/expenses?year={Y}&month={M}", headers=H).json()
ck("oddiy so'rovda qo'shilmaydi (boshqa hisobotlar uchun)", len(plain), 0)

print("\n=== 4. Xato kiritilganini ustoz oyligiga ko'chirish ===")
r = client.post("/api/expenses", headers=H, json={
    "date": TODAY.isoformat(), "category": "admin_salary", "amount": 50_000,
    "note": "Sardorcha qarz", "method": "cash", "branch_id": B1})
EID = r.json()["id"]
ck("avval ma'muriy xarajat", counts(), (1, 1))
r = client.put(f"/api/expenses/{EID}", headers=H, json={
    "category": "admin_salary", "amount": 50_000, "teacher_id": TID})
ck("ko'chirildi", (r.status_code, r.json()["category"]), (200, "teacher_salary"))
ck("xarajatdan chiqdi, oylik kartasiga qo'shildi", counts(), (0, 2))
s = SessionLocal()
tp = s.query(models.TeacherPayment).order_by(models.TeacherPayment.id.desc()).first()
ck("summa va eski izoh saqlandi", (tp.amount, tp.note), (50_000, "Sardorcha qarz"))
s.close()
lst = client.get(f"/api/expenses?year={Y}&month={M}&with_teacher=1", headers=H).json()
ck("ro'yxatda endi 2 ta ustoz oyligi",
   sum(1 for e in lst if e["category"] == "teacher_salary"), 2)

print("\n=== 5. Ma'muriy xodim — avvalgidek xarajat ===")
r = client.post("/api/expenses", headers=H, json={
    "date": TODAY.isoformat(), "category": "admin_salary", "amount": 627_000,
    "staff_user_id": IUID, "method": "cash", "branch_id": B1})
ck("xarajat bo'ldi", (r.json()["category"], r.json()["id"] > 0), ("admin_salary", True))
ck("izohda ismi", "Iroda Admin" in (r.json()["note"] or ""), True)
ck("jadvalda 1 xarajat", counts()[0], 1)

print("\n=== 6. Ustoz oyligini ro'yxatdan o'chirish ===")
neg = next(e["id"] for e in lst if e["category"] == "teacher_salary")
ck("o'chirildi", client.delete(f"/api/teacher-payments/{-neg}", headers=H).status_code, 200)
ck("bitta qoldi", counts()[1], 1)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
