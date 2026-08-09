"""Audit-log qamrovi: ilgari umuman yozilmagan 4 ta yuqori xavfli
harakat (2026-08 mustahkamlash):
  - o'z parolini almashtirish (auth_users.py: change_own_password)
  - yangi foydalanuvchi yaratish (auth_users.py: create_user)
  - xodim darajasi koeffitsiyentini o'zgartirish (entry.py:
    staff_grade_rates_set)
  - ustoz to'lovini "to'landi" deb belgilash (finance.py:
    update_payout)
"""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/auditgaps_test.db"
if os.path.exists("/tmp/auditgaps_test.db"):
    os.remove("/tmp/auditgaps_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401 - staff_grade_rates_set shu yerda ro'yxatdan
              # o'tadi (entry.py main.app'ga qo'shimcha route qo'shadi -
              # test_staff_access.py va boshqalar buni import qilmagani
              # uchun domen fayllarini izolyatsiyada sinaydi, lekin BU
              # aynan entry.py'da yashaydigan endpointni sinaydi).
from database import SessionLocal
from auth import hash_password

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


def last_log():
    return db.query(models.AuditLog).order_by(
        models.AuditLog.id.desc()).first()


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id

db.add(models.User(username="asos", full_name="Asoschi", role="founder",
                   branch_id=BID, password_hash=hash_password("x"),
                   is_active=1))
db.add(models.User(username="moliya", full_name="Moliyachi",
                   role="finance_director", branch_id=BID,
                   password_hash=hash_password("x"), is_active=1))
db.commit()

FOUNDER = tok("asos")
FIN = tok("moliya")

print("=== 1. O'Z PAROLINI ALMASHTIRISH ===")
before = db.query(models.AuditLog).count()
r = client.put("/api/auth/me/password", headers=FIN,
               json={"current_password": "x", "new_password": "yangi123"})
ck("parol almashtirildi", r.status_code, 200)
after = db.query(models.AuditLog).count()
ck("audit yozildi", after, before + 1)
lg = last_log()
ck("action to'g'ri", lg.action, "password_change")
ck("kim o'zgartirgani to'g'ri qayd etildi", lg.username, "moliya")
# Parolni asl holiga qaytaramiz - keyingi loginlar buzilmasin
u = db.query(models.User).filter(models.User.username == "moliya").first()
u.password_hash = hash_password("x")
db.commit()

print("\n=== 2. YANGI FOYDALANUVCHI YARATISH ===")
before = db.query(models.AuditLog).count()
r = client.post("/api/users", headers=FOUNDER, json={
    "phone": "+998901234567", "password": "parol123",
    "full_name": "Yangi Xodim", "role": "teacher", "branch_id": BID,
})
ck("foydalanuvchi yaratildi", r.status_code, 200)
new_uid = r.json()["id"]
after = db.query(models.AuditLog).count()
ck("audit yozildi", after, before + 1)
lg = last_log()
ck("action to'g'ri", lg.action, "create")
ck("entity to'g'ri", lg.entity, "user")
ck("entity_id yangi xodimga mos", lg.entity_id, new_uid)

print("\n=== 3. XODIM DARAJASI KOEFFITSIYENTI ===")
# Birinchi GET/PUT chaqiruvi _grade_rates() orqali jadvalni urug'laydi
before = db.query(models.AuditLog).count()
r = client.put("/api/staff-grades", headers=FOUNDER,
               json={"rates": [{"key": "middle", "coef": 1.5}]})
ck("koeffitsiyent yangilandi", r.status_code, 200)
after = db.query(models.AuditLog).count()
ck("haqiqiy o'zgarish audit qilindi", after, before + 1)
lg = last_log()
ck("entity to'g'ri", lg.entity, "staff_grade_rate")
ck("eski qiymat qayd etildi", float(lg.old_value), 1.15)
ck("yangi qiymat qayd etildi", float(lg.new_value), 1.5)

before2 = db.query(models.AuditLog).count()
r2 = client.put("/api/staff-grades", headers=FOUNDER,
                json={"rates": [{"key": "middle", "coef": 1.5}]})
after2 = db.query(models.AuditLog).count()
ck("no-op (o'zgarishsiz) qayta yuborish audit YOZMAYDI", after2, before2)

print("\n=== 4. USTOZ TO'LOVI ===")
t = models.Teacher(full_name="Bekzod Ustoz", branch_id=BID, is_active=1)
db.add(t)
g = models.Group(name="G-Test", branch_id=BID, teacher_id=None)
db.add(g)
db.commit()
payout = models.TeacherPayout(teacher_id=t.id, group_id=g.id,
                              period="2026-08", amount=350000, paid=0)
db.add(payout)
db.commit()
PID = payout.id

before = db.query(models.AuditLog).count()
r = client.put(f"/api/payouts/{PID}", headers=FIN, json={"paid": True})
ck("to'lov belgilandi", r.status_code, 200)
after = db.query(models.AuditLog).count()
ck("haqiqiy o'zgarish audit qilindi", after, before + 1)
lg = last_log()
ck("entity to'g'ri", lg.entity, "teacher_payout")
ck("entity_label ustoz + davrni o'z ichiga oladi",
   "Bekzod Ustoz" in lg.entity_label and "2026-08" in lg.entity_label, True)
ck("eski/yangi qiymat mantiqiy (audit._fmt bool'ni ha/yo'q qiladi)",
   (lg.old_value, lg.new_value), ("yo'q", "ha"))

before2 = db.query(models.AuditLog).count()
r2 = client.put(f"/api/payouts/{PID}", headers=FIN, json={"paid": True})
after2 = db.query(models.AuditLog).count()
ck("no-op (allaqachon to'langan) qayta yuborish audit YOZMAYDI",
   after2, before2)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
