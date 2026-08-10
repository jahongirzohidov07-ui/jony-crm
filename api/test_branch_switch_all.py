"""IKKI FILIALDA ISHLAYDIGAN HAR QANDAY XODIM (2026-08-10).

Jahongir: "bir vaqtda ikkita filialda ishlaydigan barcha xodim uchun
filial almashtirish imkoniyatini qo'shish kerak. Tepada filial
almashtiradigan joyi."

Tepadagi almashtirgich /api/me dagi "branches" ro'yxatidan chiqadi
(2 va undan ko'p bo'lsa ko'rinadi). Shuning uchun bu test ROLDAN
QAT'I NAZAR har bir xodim uchun o'sha ro'yxat to'g'ri kelishini
va tanlangan filial haqiqatan FILTRLASHINI tekshiradi."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/vbs/db.sqlite"
os.makedirs("/tmp/vbs", exist_ok=True)
if os.path.exists("/tmp/vbs/db.sqlite"):
    os.remove("/tmp/vbs/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}" + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


bA = models.Branch(name="Filial A")
bB = models.Branch(name="Filial B")
db.add_all([bA, bB]); db.commit()


def mk(uname, role, second=True):
    u = models.User(username=uname, full_name=f"X {uname}",
                    password_hash=hash_password("Parol123!"),
                    role=role, branch_id=bA.id, is_active=1)
    db.add(u); db.commit()
    if second:
        db.add(models.UserBranch(user_id=u.id, branch_id=bB.id))
        db.commit()
    return u


def H(u):
    return {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':u,'password':'Parol123!'}).json()['access_token']}"}


# Filialga bog'langan (org-wide BO'LMAGAN) rollar — almashtirgich
# ilgari faqat rahbariyatga chiqardi, bularga umuman yo'q edi.
CASES = [
    ("adm", roles.ADMINISTRATOR, "Administrator"),
    ("sm", roles.SALES_MANAGER, "Sotuv menejeri"),
    ("bm", roles.BRANCH_MANAGER, "Filial rahbari"),
    ("ex", roles.EXAMINER, "Examiner"),
    ("fm", roles.FACILITY_MANAGER, "Xo'jalik menejeri"),
]

print("=== IKKI FILIALLI XODIMLARDA IKKALA FILIAL QAYTADI ===")
for uname, role, label in CASES:
    mk(uname, role)
    r = c.get("/api/me", headers=H(uname))
    brs = sorted(b["name"] for b in (r.json().get("branches") or []))
    ck(f"{label}", brs, ["Filial A", "Filial B"])

print("\n=== BITTA FILIALLI XODIMDA ALMASHTIRGICH CHIQMAYDI ===")
mk("adm1", roles.ADMINISTRATOR, second=False)
r = c.get("/api/me", headers=H("adm1"))
ck("faqat bitta filial", len(r.json().get("branches") or []), 1)

print("\n=== TANLANGAN FILIAL HAQIQATAN FILTRLAYDI ===")
# Har bir filialda bittadan o'quvchi
ut = models.User(username="ust", full_name="Ustoz",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=bA.id, is_active=1)
db.add(ut); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=bA.id, user_id=ut.id,
                   is_active=1)
db.add(t); db.commit()
from datetime import date
for br, nm in ((bA, "A-bola"), (bB, "B-bola")):
    db.add(models.Student(full_name=nm, branch_id=br.id, status="active",
                          enrolled_date=date.today(),
                          public_id=f"STU-{nm}"))
db.commit()

Ha = H("adm")
r = c.get("/api/students", headers=Ha)
names = sorted(s["full_name"] for s in r.json())
ck("filtrsiz IKKALA filial o'quvchisi", names, ["A-bola", "B-bola"])

r = c.get(f"/api/students?branch_id={bA.id}", headers=Ha)
ck("A tanlansa faqat A", [s["full_name"] for s in r.json()], ["A-bola"])
r = c.get(f"/api/students?branch_id={bB.id}", headers=Ha)
ck("B tanlansa faqat B", [s["full_name"] for s in r.json()], ["B-bola"])

print("\n=== XAVFSIZLIK: O'ZINIKI BO'LMAGAN FILIALNI TANLAB BO'LMAYDI ===")
bC = models.Branch(name="Filial C")
db.add(bC); db.commit()
db.add(models.Student(full_name="C-bola", branch_id=bC.id, status="active",
                      enrolled_date=date.today(), public_id="STU-C"))
db.commit()
r = c.get(f"/api/students?branch_id={bC.id}", headers=Ha)
got = [s["full_name"] for s in r.json()]
ck("begona filial tanlansa uning ma'lumoti CHIQMAYDI",
   "C-bola" in got, False)
ck("o'rniga o'z filiallari ko'rinadi", sorted(got), ["A-bola", "B-bola"])

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
