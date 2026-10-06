"""KETGAN XODIMNI QAYTARISH (2026-10-06).

Jahongir: "arxivdagi ketgan xodimlarni akkauntlarini tiklash
qaytarishni ham qo'shib ber hrga".

Tekshiriladi:
  1. HR qaytaradi: akkaunt faol, ketish belgisi tozalanadi, ustoz kartasi
     ham qaytadi, yana kira oladi; audit.
  2. Parolni tiklash: standart parol bilan kiradi va almashtirish so'raladi.
  3. Qizil yo'lak — 409, force bilan qaytadi.
  4. Qora ro'yxat — 403. Filial rahbari hisobini HR qaytara olmaydi.
  5. Akkauntsiz ustoz kartasi qaytadi. Ustoz (ruxsatsiz) — 403.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "staff_restore_test")
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
b = models.Branch(name="Zafar"); db.add(b); db.commit()
PW = "Parol123!"


def user(login, name, role, active=1, exit_type=None, phone=None):
    u = models.User(username=login, password_hash=hash_password(PW),
                    full_name=name, role=role, branch_id=b.id,
                    is_active=active, phone=phone)
    if not active:
        u.exit_type = exit_type or "neutral"
        u.exit_date = date(2026, 9, 1)
        u.exit_reason = "o'qishga ketdi"
    db.add(u); db.commit()
    return u


user("hr", "HR", roles.HR_MANAGER)
user("ust", "Ustoz Faol", roles.TEACHER)
sup = user("sup", "Ketgan Support", roles.SUPPORT_TEACHER, active=0)
red = user("red", "Qizil Odam", roles.ADMINISTRATOR, active=0, exit_type="red")
bm = user("bm", "Ketgan Rahbar", roles.BRANCH_MANAGER, active=0)
bl = user("bl", "Qora Odam", roles.ADMINISTRATOR, active=0, phone="998901112233")
tc = models.Teacher(full_name="Ketgan Support", branch_id=b.id,
                    user_id=sup.id, is_active=0, left_date=date(2026, 9, 1))
card = models.Teacher(full_name="Eski Karta", branch_id=b.id, is_active=0)
db.add_all([tc, card]); db.commit()
db.add(models.HrBlacklist(
    full_name="Qora Odam", phone="998901112233",
    phone_key=roles.blacklist_phone_key("998901112233"),
    name_key=roles.blacklist_name_key("Qora Odam"),
    category="other", reason="o'g'irlik", is_active=1))
db.commit()
SUP, RED, BM, BL, CARD = sup.id, red.id, bm.id, bl.id, card.id


def login(u, pw=PW):
    return c.post("/api/auth/login", json={"username": u, "password": pw})


H = {"Authorization": "Bearer " + login("hr").json()["access_token"]}
HU = {"Authorization": "Bearer " + login("ust").json()["access_token"]}

print("=== 1. ODDIY QAYTARISH ===")
ck("ketgan kira olmaydi", login("sup").status_code, 401)
r = c.post(f"/api/staff/{SUP}/restore", headers=H, json={"note": "qaytdi"})
ck("qaytarildi", r.status_code, 200)
db.expire_all()
u = db.query(models.User).get(SUP)
ck("faol, ketish belgisi yo'q",
   (u.is_active, u.exit_type, u.exit_date, u.exit_reason), (1, None, None, None))
t = db.query(models.Teacher).filter(models.Teacher.user_id == SUP).one()
ck("karta ham qaytdi", (t.is_active, t.left_date), (1, None))
ck("eski paroli bilan kiradi", login("sup").status_code, 200)
ck("ikkinchi marta — 400",
   c.post(f"/api/staff/{SUP}/restore", headers=H, json={}).status_code, 400)

print("\n=== 2. PAROLNI TIKLASH / QIZIL YO'LAK ===")
r = c.post(f"/api/staff/{RED}/restore", headers=H, json={})
ck("qizil yo'lak — 409", r.status_code, 409)
r = c.post(f"/api/staff/{RED}/restore", headers=H,
           json={"force": True, "reset_password": True})
ck("tasdiq bilan qaytdi", r.status_code, 200)
r = login("red", roles.DEFAULT_PASSWORD)
ck("standart parol bilan kiradi", r.status_code, 200)
ck("parolni almashtirish so'raladi", r.json().get("must_change_password"), True)

print("\n=== 3. TAQIQLAR ===")
ck("filial rahbarini HR qaytarmaydi",
   c.post(f"/api/staff/{BM}/restore", headers=H, json={}).status_code, 403)
if True:
    ck("qora ro'yxat — 403",
       c.post(f"/api/staff/{BL}/restore", headers=H, json={}).status_code, 403)
ck("ustoz — 403",
   c.post(f"/api/staff/{BM}/restore", headers=HU, json={}).status_code, 403)

print("\n=== 4. AKKAUNTSIZ KARTA ===")
r = c.post(f"/api/staff/teacher-card/{CARD}/restore", headers=H)
ck("karta qaytdi", r.status_code, 200)
db.expire_all()
ck("faol", db.query(models.Teacher).get(CARD).is_active, 1)

print("\n=== 5. AUDIT ===")
n = (db.query(models.AuditLog)
     .filter(models.AuditLog.action == "restore",
             models.AuditLog.entity == "user").count())
ck("2 ta qaytarish yozildi", n, 2)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
