"""Ustozga avtomat akkaunt ochish: login, parol, bog'lanish."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/account_test.db"
if os.path.exists("/tmp/account_test.db"):
    os.remove("/tmp/account_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
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


TODAY = date.today()
db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
BID = b.id
for u, role in [("asos", "founder"), ("hr", "hr_manager"),
                ("sotuv", "sales_manager")]:
    db.add(models.User(username=u, password_hash=hash_password("x"),
                       full_name=u.capitalize(), role=role,
                       branch_id=None if role == "founder" else BID))
db.commit(); db.close()

H = tok("asos")
HR = tok("hr")
HSAL = tok("sotuv")

print("=== 1. LOGIN ISMDAN YASALADI ===")

ck("apostrof tushadi",
   roles.login_from_name("Sevinch To'rayeva"), "sevinch.torayeva")
ck("oddiy ism", roles.login_from_name("Bekzod Nabijonov"),
   "bekzod.nabijonov")
ck("uch so'zli ismda familiya olinadi",
   roles.login_from_name("Abdulaziz Rustam o'g'li Karimov"),
   "abdulaziz.karimov")
ck("kirill o'giriladi", roles.login_from_name("Ирина Тузикова"),
   "irina.tuzikova")
ck("bitta so'z", roles.login_from_name("Mahbuba"), "mahbuba")
ck("bo'sh ism", roles.login_from_name(""), "xodim")
ck("chiziqcha probelga", roles.login_from_name("Anna-Maria Petrova"),
   "anna.petrova")

print("\n=== 2. PAROL XAVFSIZ VA O'QILADIGAN ===")

p1 = roles.make_password()
ck("uzunligi 9 (4+chiziqcha+4)", len(p1), 9)
ck("o'rtasida chiziqcha", p1[4], "-")
bad = set("ilIL10oO")
ck("chalkashtiruvchi belgi yo'q",
   any(c in bad for c in p1.replace("-", "")), False)
ck("har safar boshqacha",
   len({roles.make_password() for _ in range(50)}), 50)

print("\n=== 3. AKKAUNT OCHILADI ===")

r = client.post("/api/teachers", headers=H, json={
    "full_name": "Bekzod Nabijonov", "phone": "998901112233",
    "subject": "Ingliz tili", "branch_id": BID})
T1 = r.json()["id"]

d = client.get(f"/api/teachers/{T1}/account", headers=H).json()
ck("boshida akkaunt yo'q", d["has_account"], False)

r = client.post(f"/api/teachers/{T1}/account", headers=H)
ck("akkaunt ochildi", r.status_code, 200)
acc = r.json()
LOGIN1, PWD1 = acc["login"], acc["password"]
ck("login ismdan", LOGIN1, "bekzod.nabijonov")
ck("parol berildi", len(PWD1), 9)
ck("ogohlantirish bor", "bir marta" in acc["warning"], True)
ck("manzil ko'rsatilgan", acc["url"], "https://jony-crm.vercel.app")
ck("holat yangilandi", acc["has_account"], True)

print("\n=== 4. USTOZ SHU PAROL BILAN KIRADI ===")

r = client.post("/api/auth/login",
                json={"username": LOGIN1, "password": PWD1})
ck("tizimga kirdi", r.status_code, 200)
HT = {"Authorization": "Bearer " + r.json()["access_token"]}

me = client.get("/api/auth/me", headers=HT).json()
ck("roli ustoz", me["role"], "teacher")
ck("ismi to'g'ri", me["full_name"], "Bekzod Nabijonov")
ck("filiali biriktirildi", me["branch_id"], BID)

r = client.post("/api/auth/login",
                json={"username": LOGIN1, "password": "boshqa"})
ck("noto'g'ri parol o'tmaydi", r.status_code, 401)

print("\n=== 5. USTOZ YOZUVI BILAN BOG'LANDI ===")

db = SessionLocal()
t = db.query(models.Teacher).get(T1)
u = db.query(models.User).filter(models.User.username == LOGIN1).first()
ck("ID bo'yicha bog'landi", t.user_id, u.id)
found = main._teacher_of_user(db, u)
ck("o'z yozuvini topdi", found.id, T1)

# Ism o'zgarsa ham aloqa uzilmaydi
t.full_name = "Bekzod Nabijonov-Yusupov"
db.commit()
found = main._teacher_of_user(db, u)
ck("ism o'zgarsa ham topiladi", found.id, T1)
t.full_name = "Bekzod Nabijonov"
db.commit(); db.close()

print("\n=== 6. TAKRORLANISH VA XATOLAR ===")

r = client.post(f"/api/teachers/{T1}/account", headers=H)
ck("ikkinchi marta ochilmaydi", r.status_code, 400)
ck("nima qilish aytilgan", "Yangi parol" in r.json()["detail"], True)

# Bir xil ismli ikkinchi ustoz
r = client.post("/api/teachers", headers=H, json={
    "full_name": "Bekzod Nabijonov", "branch_id": BID})
T2 = r.json()["id"]
r = client.post(f"/api/teachers/{T2}/account", headers=H)
ck("login takrorlanmadi", r.json()["login"], "bekzod.nabijonov2")

# Ishdan ketgan ustoz
r = client.post("/api/teachers", headers=H, json={
    "full_name": "Ketgan Ustoz", "branch_id": BID, "is_active": 0})
T3 = r.json()["id"]
r = client.post(f"/api/teachers/{T3}/account", headers=H)
ck("ishdan ketganga ochilmaydi", r.status_code, 400)

r = client.post("/api/teachers/9999/account", headers=H)
ck("yo'q ustoz", r.status_code, 404)

print("\n=== 7. YANGI PAROL ===")

r = client.post(f"/api/teachers/{T1}/account/reset", headers=H)
ck("yangi parol berildi", r.status_code, 200)
PWD2 = r.json()["password"]
ck("login o'zgarmadi", r.json()["login"], LOGIN1)
ck("parol boshqacha", PWD2 != PWD1, True)

ck("eski parol ishlamaydi",
   client.post("/api/auth/login",
               json={"username": LOGIN1, "password": PWD1}).status_code,
   401)
ck("yangi parol ishlaydi",
   client.post("/api/auth/login",
               json={"username": LOGIN1, "password": PWD2}).status_code,
   200)

r = client.post(f"/api/teachers/{T3}/account/reset", headers=H)
ck("akkauntsizga yangi parol yo'q", r.status_code, 400)

print("\n=== 8. RUXSATLAR ===")

r = client.post("/api/teachers", headers=H, json={
    "full_name": "Yangi Ustoz", "branch_id": BID})
T4 = r.json()["id"]

ck("HR akkaunt ocha oladi",
   client.post(f"/api/teachers/{T4}/account", headers=HR).status_code, 200)
ck("sotuv menejeri ocha olmaydi",
   client.post(f"/api/teachers/{T2}/account/reset",
               headers=HSAL).status_code, 403)
ck("ustozning o'zi ocha olmaydi",
   client.post(f"/api/teachers/{T2}/account/reset",
               headers=HT).status_code, 403)

print("\n=== 9. RO'YXATDA KO'RINADI ===")

rows = client.get("/api/teachers", headers=H).json()
b1 = next(t for t in rows if t["id"] == T1)
ck("login ro'yxatda", b1["login"], LOGIN1)
ck("bog'langan", b1["user_id"] is not None, True)

t3 = next(t for t in rows if t["id"] == T3)
ck("akkauntsizda bo'sh", t3["login"], None)

print("\n=== 10. ESKI YOZUVLARNI BOG'LASH ===")

# Ism bo'yicha yaratilgan eski akkaunt
db = SessionLocal()
old_t = models.Teacher(full_name="Eski Ustoz", branch_id=BID, is_active=1)
db.add(old_t); db.commit()
OLD_T = old_t.id
old_u = models.User(username="eski", password_hash=hash_password("x"),
                    full_name="Eski Ustoz", role="teacher", branch_id=BID)
db.add(old_u); db.commit()
OLD_U = old_u.id
ck("boshida bog'lanmagan",
   db.query(models.Teacher).get(OLD_T).user_id, None)

main._link_teacher_accounts(db)
ck("avtomat bog'landi",
   db.query(models.Teacher).get(OLD_T).user_id, OLD_U)
db.close()

print("\n=== 11. POSTGRES MOSLIGI ===")

# SQLite mantiqiy qiymatni butun sonli ustunga qabul qiladi, Postgres
# esa rad etadi. Ya'ni bunday xato faqat JONLI bazada chiqadi va
# testdan o'tib ketadi. Shuning uchun matnning o'zini tekshiramiz.
import re
_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "models.py")).read()
_int_cols = set(re.findall(r"^\s{4}(\w+)\s*=\s*Column\(Integer",
                           _src, re.M))
_main = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "main.py")).read()
_bad = []
for _m in re.finditer(r"(\w+)\s*=\s*(True|False)\b", _main):
    if _m.group(1) in _int_cols:
        _line = _main[:_m.start()].count("\n") + 1
        # Funksiya argumenti bo'lsa hisobga olinmaydi
        _ctx = _main[max(0, _m.start() - 60):_m.start()]
        if "(" in _ctx.split("\n")[-1]:
            continue
        _bad.append(f"main.py:{_line} {_m.group(1)}")
ck("butun sonli ustunga True berilmagan", _bad, [])

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
