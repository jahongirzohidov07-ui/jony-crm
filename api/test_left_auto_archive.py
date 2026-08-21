"""GURUHSIZ VA QARZSIZ "Chiqib ketgan"lar avtomat arxivga (2026-08-22).

Jahongir: "guruhi yoq, qarzi yoq bo'lsa arxivga tushsin chiqib ketgan
joyi kerak emasda bizga".

Tekshiriladi: guruhsiz + qarzsiz "left" arxivga o'tadi; qarzdor,
guruhi bor va faol/muzlatilgan o'quvchilarga TEGILMAYDI; ro'yxat
ochilganda o'zi ishlaydi; auditda iz qoladi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_swp/db.sqlite"
os.makedirs("/tmp/verify_swp", exist_ok=True)
if os.path.exists("/tmp/verify_swp/db.sqlite"):
    os.remove("/tmp/verify_swp/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
import students as students_mod
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
u = models.User(username="asos", full_name="Asoschi",
                password_hash=hash_password("Parol123!"),
                role=roles.FOUNDER, branch_id=b.id, is_active=1)
db.add(u); db.commit()
g = models.Group(name="IELTS 1.0", branch_id=b.id); db.add(g); db.commit()


def mk(name, status, group_id=None, bal=0):
    s = models.Student(full_name=name, branch_id=b.id, status=status,
                       group_id=group_id, enrolled_date=date(2026, 1, 1))
    db.add(s); db.commit()
    if bal:
        db.add(models.Payment(student_id=s.id, amount=bal,
                              kind="payment" if bal > 0 else "charge"))
        db.commit()
    return s


# 1. guruhsiz + qarzsiz "chiqib ketgan" — ARXIVGA
a1 = mk("Toza Ketgan", roles.STUDENT_LEFT)
# 2. guruhsiz + BALANSI ORTIQCHA "chiqib ketgan" — ham arxivga
a2 = mk("Ortiqcha Ketgan", roles.STUDENT_LEFT, bal=50000)
# 3. guruhsiz + QARZDOR — tegilmaydi
d1 = mk("Qarzdor Ketgan", roles.STUDENT_LEFT, bal=-480000)
# 4. GURUHI BOR "chiqib ketgan" — tegilmaydi
d2 = mk("Guruhli Ketgan", roles.STUDENT_LEFT, group_id=g.id)
# 5. faol va muzlatilgan guruhsiz — tegilmaydi
d3 = mk("Faol Bola", "active")
d4 = mk("Muzlatilgan Bola", "frozen")
# 6. guruhsiz "left", lekin ko'p guruh bog'lanishi ochiq — tegilmaydi
d5 = mk("Bogliqligi Bor", roles.STUDENT_LEFT)
db.add(models.StudentGroupLink(student_id=d5.id, group_id=g.id, active=1))
db.commit()

ids = {x.full_name: x.id for x in (a1, a2, d1, d2, d3, d4, d5)}

print("=== RO'YXAT OCHILGANDA O'ZI ISHLAYDI ===")
tok = c.post("/api/auth/login",
             json={"username": "asos", "password": "Parol123!"}
             ).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}
r = c.get("/api/students", headers=H)
ck("status 200", r.status_code, 200)

db.expire_all()


def st(name):
    return db.query(models.Student).get(ids[name]).status


print("\n=== ARXIVGA O'TDI ===")
ck("guruhsiz+qarzsiz arxivda", st("Toza Ketgan"), "archived")
ck("guruhsiz+ortiqcha balans arxivda", st("Ortiqcha Ketgan"), "archived")
ck("ketgan sanasi qo'yildi",
   db.query(models.Student).get(ids["Toza Ketgan"]).left_date is not None, True)

print("\n=== TEGILMADI ===")
ck("qarzdor joyida", st("Qarzdor Ketgan"), roles.STUDENT_LEFT)
ck("guruhi bori joyida", st("Guruhli Ketgan"), roles.STUDENT_LEFT)
ck("faol joyida", st("Faol Bola"), "active")
ck("muzlatilgan joyida", st("Muzlatilgan Bola"), "frozen")
ck("ochiq bog'lanishi bori joyida", st("Bogliqligi Bor"), roles.STUDENT_LEFT)

print("\n=== AUDITDA IZ ===")
a = (db.query(models.AuditLog)
     .filter(models.AuditLog.action == "auto_archive").all())
ck("2 ta yozuv", len(a), 2)
ck("sababi yozilgan",
   "Guruhsiz va qarzsiz" in (a[0].note or "") if a else False, True)

print("\n=== QARZ YOPILSA KEYINGI OCHILISHDA O'TADI ===")
db.add(models.Payment(student_id=ids["Qarzdor Ketgan"], amount=480000,
                      kind="payment"))
db.commit()
moved = students_mod.sweep_left_to_archive(db)
ck("bitta ko'chdi", moved, 1)
db.expire_all()
ck("endi arxivda", st("Qarzdor Ketgan"), "archived")

print("\n=== TAKROR ISHLASA HECH NARSA O'ZGARMAYDI ===")
ck("ikkinchi yugurish bo'sh", students_mod.sweep_left_to_archive(db), 0)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
