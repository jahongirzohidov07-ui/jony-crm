"""TELEFON RAQAMLARI BITTA FORMATDA (2026-09-16, taklif #30).

O'zbekiston raqami bazada 9 raqam bo'lib turadi ("901234567"), qaysi
yo'l bilan kiritilganidan qat'i nazar. Chet el raqami va tushunarsiz
qiymat o'zgarmaydi. Loginlarga tegilmaydi."""
import os, sys, tempfile

_tmp = tempfile.mkdtemp(prefix="jony_ph_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
    _tmp, "db.sqlite").replace("\\", "/")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from fastapi.testclient import TestClient
import main, models, roles, phones
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []
PW = "Parol123!"


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g!r}"
          + ("" if ok else f"  (kutilgan {w!r})"))
    if not ok:
        fails.append(n)


print("=== QOIDA ===")
for raw, want in [
    ("+998 90 123-45-67", "901234567"),
    ("998901234567", "901234567"),
    ("(90) 123 45 67", "901234567"),
    ("901234567", "901234567"),
    ("+7 916 123 45 67", "+7 916 123 45 67"),
    ("+123456789", "+123456789"),
    ("12345", "12345"),
    ("   ", None),
    (None, None),
]:
    ck(f"{raw!r}", roles.normalize_phone(raw), want)

b = models.Branch(name="Zafar"); db.add(b); db.commit()
hr = models.User(username="hr", full_name="Hr", password_hash=hash_password(PW),
                 role=roles.HR_MANAGER, branch_id=b.id, is_active=1)
db.add(hr); db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "hr", "password": PW}
).json()["access_token"]}

print("\n=== YOZISHDA AVTOMAT ===")
u = models.User(username="998911112233", full_name="Xodim Bir",
                password_hash=hash_password(PW), role=roles.TEACHER,
                branch_id=b.id, is_active=1, phone="+998 91 111-22-33")
db.add(u); db.commit(); db.refresh(u)
ck("xodim telefoni", u.phone, "911112233")
ck("login o'zgarmadi", u.username, "998911112233")
st = models.Student(full_name="O'quvchi Bir", branch_id=b.id,
                    phone="998 93 000 11 22", parent_phone="+7 999 000 00 00")
db.add(st); db.commit(); db.refresh(st)
ck("o'quvchi telefoni", st.phone, "930001122")
ck("chet el raqami o'zgarmadi", st.parent_phone, "+7 999 000 00 00")
st.phone = "+998 (93) 777 66 55"; db.commit(); db.refresh(st)
ck("tahrirlashda ham", st.phone, "937776655")
st.phone = ""; db.commit(); db.refresh(st)
ck("bo'sh qiymat -> None", st.phone, None)

r = c.post("/api/candidates", headers=H, json={
    "full_name": "Nomzod Bir", "phone": "+998 99 555 44 33",
    "position": "sales"})
cid = r.json()["id"]
ck("nomzod (API)", c.get(f"/api/candidates/{cid}", headers=H).json()["phone"],
   "995554433")
ck("login bo'lganda ham kiradi (12 xonali)",
   c.post("/api/auth/login", json={"username": "998911112233",
                                   "password": PW}).status_code, 200)
ck("login bo'lganda ham kiradi (9 xonali yozilsa)",
   c.post("/api/auth/login", json={"username": "91 111 22 33",
                                   "password": PW}).status_code, 200)

print("\n=== ONLAYN ARIZA TAKRORI ===")
photo = "data:image/jpeg;base64," + "A" * 200
body = {"full_name": "Takror Nomzod Aka", "position": "sales", "photo": photo}
r1 = c.post("/api/apply", json={**body, "phone": "+998 90 999 88 77"})
r2 = c.post("/api/apply", json={**body, "phone": "90-999-88-77"})
ck("birinchisi qabul", r1.json().get("already"), None)
ck("boshqa yozilishdagi takror aniqlandi", r2.json().get("already"), True)

print("\n=== OTA-ONA QIDIRUVI ===")
p = models.Parent(full_name="Ota Ona", phone="+998 97 123 45 67",
                  branch_id=b.id)
db.add(p); db.commit()
F = models.User(username="asoschi", full_name="Asoschi",
                password_hash=hash_password(PW), role=roles.FOUNDER,
                is_active=1)
db.add(F); db.commit()
HF = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asoschi", "password": PW}
).json()["access_token"]}
names = [x["full_name"] for x in c.get(
    "/api/parents?q=97 123 45", headers=HF).json()]
ck("probel bilan yozilgan raqam topildi", "Ota Ona" in names, True)

print("\n=== ESKI YOZUVLARNI TOZALASH ===")
# ORM'ni chetlab eski ko'rinishda yozamiz (hodisa ishlamaydi)
db.execute(text("UPDATE users SET phone='+998 (91) 111-22-33' "
                "WHERE id=:i"), {"i": u.id})
db.execute(text("UPDATE students SET phone='998930001122', "
                "parent_phone='+7 999 000 00 00' WHERE id=:i"), {"i": st.id})
db.execute(text("UPDATE leads_deleted SET phone=phone"))
db.commit()
# oldingi startda belgi qo'yilgan bo'lishi mumkin — sinov uchun olib tashlaymiz
db.execute(text("DELETE FROM seed_marks WHERE key LIKE 'phone_norm_v1%'"))
db.commit()
import common
if common._SEED_KEYS is not None:
    common._SEED_KEYS = {k for k in common._SEED_KEYS
                         if not k.startswith("phone_norm_v1")}
res = phones.normalize_existing(db, budget_s=30)
ck("tugadi", res["done"], True)
ck("xodimlar: 1 ta o'zgardi", res["changed"].get("users.phone"), 1)
ck("o'quvchilar: 1 ta o'zgardi", res["changed"].get("students.phone"), 1)
ck("chet el raqamiga tegilmadi", res["changed"].get("students.parent_phone"), 0)
db.expire_all()
ck("xodim", db.query(models.User).get(u.id).phone, "911112233")
ck("login joyida", db.query(models.User).get(u.id).username, "998911112233")
res2 = phones.normalize_existing(db, budget_s=30)
ck("qayta ishga tushsa hech narsa qilmaydi", res2, {"done": True, "changed": {}})

print("\n=== QORA RO'YXAT BUZILMADI ===")
r = c.post("/api/hr/blacklist", headers=H, json={
    "full_name": "Nomzod Bir", "phone": "995554433", "category": "other",
    "reason": "Test uchun sabab"})
ck("qo'shildi", r.status_code, 200)
d = c.get(f"/api/candidates/{cid}", headers=H).json()
ck("nomzod tanildi", d["blacklist"] is not None, True)

print()
if fails:
    print("XATOLAR:", fails)
    sys.exit(1)
print("HAMMASI O'TDI")
