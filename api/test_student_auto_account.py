"""O'QUVCHI HISOBI AVTOMAT OCHILISHI + OTA-ONA/O'QUVCHI ROLLARI
XODIM RO'YXATIDAN OLIB TASHLANISHI (2026-08-10).

Jahongir: "ota-ona yoki o'quvchi degan rol ochib o'tirilmasin,
o'quvchi kiritildimi avtomat unga o'quvchi maqomi va akkaunti
ochilsin, nomeri login paroli esa jonyjony bo'lsin. Xuddi shunday
ota-ona roli ham avtomat ochilsin, faqat unga maxsus link bilan
kiriladigan bo'lishi kerak ... bu yerda ota-ona o'quvchi degan
rollar keremas, olib tashla."

Ota-onaga HISOB umuman ochilmaydi — u maxsus havola (parent_token)
orqali kiradi, u ham o'quvchi kartasi bilan birga avtomat
yaratiladi."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/vsa/db.sqlite"
os.makedirs("/tmp/vsa", exist_ok=True)
if os.path.exists("/tmp/vsa/db.sqlite"):
    os.remove("/tmp/vsa/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password, verify_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}" + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
adm = models.User(username="dir", full_name="Asoschi",
                  password_hash=hash_password("Parol123!"),
                  role=roles.FOUNDER, branch_id=b.id, is_active=1)
db.add(adm); db.commit()
H = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'dir','password':'Parol123!'}).json()['access_token']}"}

print("=== ROLLAR RO'YXATIDA OTA-ONA/O'QUVCHI YO'Q ===")
ck("HR ro'yxatida ota-ona yo'q", roles.PARENT in roles.HR_ASSIGNABLE_ROLES, False)
ck("HR ro'yxatida o'quvchi yo'q", roles.STUDENT in roles.HR_ASSIGNABLE_ROLES, False)
ck("xodim ro'yxatida ota-ona yo'q",
   roles.PARENT in roles.STAFF_ASSIGNABLE_ROLES, False)
ck("xodim ro'yxatida o'quvchi yo'q",
   roles.STUDENT in roles.STAFF_ASSIGNABLE_ROLES, False)
# Rollar TIZIMDA qoladi (o'quvchi hisobi shu rol bilan ochiladi)
ck("lekin tizimda rol o'zi bor", roles.STUDENT in roles.ALL_ROLES, True)

print("\n=== O'QUVCHI KIRITILDI -> HISOB AVTOMAT ===")
r = c.post("/api/students", headers=H, json={
    "full_name": "Aziz Karimov", "branch_id": b.id,
    "phone": "+998 90 123 45 67", "status": "active",
    "enrolled_date": date.today().isoformat()})
ck("o'quvchi yaratildi", r.status_code, 200)
sid = r.json()["id"]
s = db.query(models.Student).get(sid)
db.refresh(s)
ck("hisob bog'landi", bool(s.user_id), True)

u = db.query(models.User).get(s.user_id)
ck("login = telefon raqami (faqat raqamlar)", u.username, "998901234567")
ck("roli o'quvchi", u.role, roles.STUDENT)
ck("ismi bir xil", u.full_name, "Aziz Karimov")
ck("filiali bir xil", u.branch_id, b.id)
ck("paroli jonyjony", verify_password("jonyjony", u.password_hash), True)

print("\n=== O'QUVCHI HAQIQATAN KIRA OLADI ===")
r = c.post("/api/auth/login",
           json={"username": "998901234567", "password": "jonyjony"})
ck("login muvaffaqiyatli", r.status_code, 200)
ck("roli o'quvchi", r.json()["role"], roles.STUDENT)
Hs = {"Authorization": f"Bearer {r.json()['access_token']}"}
r = c.get("/api/student/home", headers=Hs)
ck("Jony Student ilovasi ochiladi", r.status_code, 200)
ck("o'z ismini ko'radi", r.json()["name"], "Aziz Karimov")

print("\n=== OTA-ONA HAVOLASI AVTOMAT (hisob YO'Q) ===")
r = c.post(f"/api/students/{sid}/parent-link", headers=H, json={})
if r.status_code != 200:
    r = c.get(f"/api/students/{sid}/parent-link", headers=H)
db.refresh(s)
ck("ota-ona havolasi (token) bor", bool(s.parent_token), True)
r = c.get(f"/api/parent/{s.parent_token}")
ck("havola bilan ota-ona sahifasi ochiladi", r.status_code, 200)
ck("farzand ismi ko'rinadi", r.json()["name"], "Aziz Karimov")
n_parent = db.query(models.User).filter(
    models.User.role == roles.PARENT).count()
ck("ota-onaga HISOB ochilmagan (kerak emas)", n_parent, 0)

print("\n=== TELEFONSIZ O'QUVCHI: KARTA OCHILADI, HISOB KEYIN ===")
r = c.post("/api/students", headers=H, json={
    "full_name": "Bahora Yulduz", "branch_id": b.id, "status": "active",
    "enrolled_date": date.today().isoformat()})
ck("telefonsiz ham o'quvchi yaratiladi", r.status_code, 200)
sid2 = r.json()["id"]
s2 = db.query(models.Student).get(sid2)
ck("hozircha hisobsiz", s2.user_id, None)

r = c.put(f"/api/students/{sid2}", headers=H,
          json={"phone": "998911112233"})
ck("telefon qo'shildi", r.status_code, 200)
db.refresh(s2)
ck("endi hisob AVTOMAT ochildi", bool(s2.user_id), True)
ck("login yangi telefon",
   db.query(models.User).get(s2.user_id).username, "998911112233")

print("\n=== TAKROR OCHILMAYDI ===")
before = db.query(models.User).count()
c.put(f"/api/students/{sid}", headers=H, json={"note": "test"})
ck("mavjud hisob ikkinchi marta ochilmaydi",
   db.query(models.User).count(), before)

print("\n=== BAND LOGIN: KARTA BARIBIR YARATILADI ===")
# 2026-08-18: endi bir xil telefon dublikat deb ogohlantiriladi
# (Boymirzaev Bekzod holati). Bu yerda ataylab boshqa odam kiritilyapti
# — shuning uchun force=true bilan tasdiqlanadi. Test maqsadi
# o'zgarmadi: login band bo'lsa ham KARTA yaratilishi kerak.
r = c.post("/api/students?force=true", headers=H, json={
    "full_name": "Uchinchi Bola", "branch_id": b.id,
    "phone": "998901234567",  # Azizniki bilan bir xil
    "status": "active", "enrolled_date": date.today().isoformat()})
ck("band raqam bo'lsa ham o'quvchi yaratiladi", r.status_code, 200)
s3 = db.query(models.Student).get(r.json()["id"])
ck("lekin hisob ochilmadi (login band)", s3.user_id, None)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
