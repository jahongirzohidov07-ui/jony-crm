"""Xodimlar ro'yxati: kim ko'radi, kim tahrirlaydi, kim rol beradi.

Bu uch narsa ilgari bitta huquq ostida edi (USER_ADMIN = faqat
asoschi) — natijada HR menejer xodimlar ro'yxatini umuman ocholmasdi.
"""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/staffacc_test.db"
if os.path.exists("/tmp/staffacc_test.db"):
    os.remove("/tmp/staffacc_test.db")

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


db = SessionLocal()
b1 = models.Branch(name="Zafar"); db.add(b1)
b2 = models.Branch(name="Markaz"); db.add(b2)
db.commit()
B1, B2 = b1.id, b2.id

for u, role, br in [("asos", "founder", None), ("hr", "hr_manager", None),
                    ("moliya", "finance_director", None),
                    ("rahbar", "branch_manager", B1),
                    ("sotuv", "sales_manager", B1),
                    ("ustoz", "teacher", B1)]:
    db.add(models.User(username=u, password_hash=hash_password("x"),
                       full_name=u.capitalize(), role=role, branch_id=br,
                       phone="998900000000"))
db.commit()
UID = {u.username: u.id for u in db.query(models.User).all()}
db.close()

H = tok("asos")
HR = tok("hr")
FIN = tok("moliya")
BM = tok("rahbar")
SAL = tok("sotuv")
HT = tok("ustoz")

print("=== 1. RO'YXATNI KIM KO'RADI ===")

r = client.get("/api/users", headers=HR)
ck("HR ro'yxatni ochadi", r.status_code, 200)
ck("HR hamma xodimni ko'radi", len(r.json()), 6)

ck("asoschi ko'radi", len(client.get("/api/users", headers=H).json()), 6)
ck("moliya direktori ko'radi",
   client.get("/api/users", headers=FIN).status_code, 200)

r = client.get("/api/users", headers=BM)
ck("filial rahbari ochadi", r.status_code, 200)
ck("faqat o'z filialini ko'radi",
   {u["branch_id"] for u in r.json()}, {B1})

ck("sotuv menejeri ko'rmaydi",
   client.get("/api/users", headers=SAL).status_code, 403)
ck("ustoz ko'rmaydi",
   client.get("/api/users", headers=HT).status_code, 403)

print("\n=== 2. KARTANI KIM TAHRIRLAYDI ===")

# HR telefon raqamini tuzatadi — bu "rol berish" emas
r = client.put(f"/api/users/{UID['ustoz']}", headers=HR,
               json={"phone": "998901112233"})
ck("HR telefonni tahrirladi", r.status_code, 200)
ck("raqam saqlandi", r.json()["phone"], "998901112233")

r = client.put(f"/api/users/{UID['ustoz']}", headers=HR,
               json={"fix_salary": 3500000})
ck("HR fiks oylikni qo'ydi", r.json()["fix_salary"], 3500000)

r = client.put(f"/api/users/{UID['ustoz']}", headers=HR,
               json={"birth_date": "1998-04-12"})
ck("HR tug'ilgan sanani kiritdi", r.json()["birth_date"], "1998-04-12")

ck("sotuv menejeri tahrirlay olmaydi",
   client.put(f"/api/users/{UID['ustoz']}", headers=SAL,
              json={"phone": "1"}).status_code, 403)

print("\n=== 3. ROL BERISH ALOHIDA HUQUQ ===")

# HR ustozni sotuv menejeriga o'tkaza oladi (ruxsat etilgan ro'yxat)
r = client.put(f"/api/users/{UID['ustoz']}", headers=HR,
               json={"role": "sales_manager"})
ck("HR ruxsat etilgan rolni beradi", r.status_code, 200)
client.put(f"/api/users/{UID['ustoz']}", headers=HR,
           json={"role": "teacher"})

# Lekin filial rahbari roli — yo'q
r = client.put(f"/api/users/{UID['ustoz']}", headers=HR,
               json={"role": "branch_manager"})
ck("HR filial rahbari rolini bera olmaydi", r.status_code, 403)
ck("sabab tushuntirildi", "faqat asoschi" in r.json()["detail"], True)

r = client.put(f"/api/users/{UID['ustoz']}", headers=HR,
               json={"role": "founder"})
ck("HR asoschi rolini bera olmaydi", r.status_code, 403)

r = client.put(f"/api/users/{UID['ustoz']}", headers=H,
               json={"role": "branch_manager"})
ck("asoschi istalgan rolni beradi", r.status_code, 200)
client.put(f"/api/users/{UID['ustoz']}", headers=H,
           json={"role": "teacher"})

print("\n=== 4. ASOSCHI KARTASI HIMOYALANGAN ===")

r = client.put(f"/api/users/{UID['asos']}", headers=HR,
               json={"phone": "000"})
ck("HR asoschi kartasiga tegmaydi", r.status_code, 403)

r = client.put(f"/api/users/{UID['asos']}", headers=HR,
               json={"password": "yangi123"})
ck("HR asoschi parolini almashtira olmaydi", r.status_code, 403)

r = client.put(f"/api/users/{UID['asos']}", headers=HR,
               json={"is_active": False})
ck("HR asoschini o'chira olmaydi", r.status_code, 403)

r = client.put(f"/api/users/{UID['asos']}", headers=H,
               json={"phone": "998901234567"})
ck("asoschi o'z kartasini tahrirlaydi", r.status_code, 200)

print("\n=== 5. XODIM OCHISH ===")

r = client.post("/api/users", headers=HR, json={
    "username": "yangi.ustoz", "password": "parol123",
    "full_name": "Yangi Ustoz", "role": "teacher", "branch_id": B1,
    "fix_salary": 2000000})
ck("HR ustoz ochdi", r.status_code, 200)
ck("fiks oylik yozildi", r.json()["fix_salary"], 2000000)

r = client.post("/api/users", headers=HR, json={
    "username": "yangi.rahbar", "password": "parol123",
    "full_name": "Yangi Rahbar", "role": "branch_manager"})
ck("HR filial rahbari ocha olmaydi", r.status_code, 403)

r = client.post("/api/users", headers=BM, json={
    "username": "filial.ustoz", "password": "parol123",
    "full_name": "Filial Ustoz", "role": "teacher", "branch_id": B1})
ck("filial rahbari o'z filialiga ochdi", r.status_code, 200)

r = client.post("/api/users", headers=BM, json={
    "username": "boshqa.filial", "password": "parol123",
    "full_name": "Boshqa Filial", "role": "teacher", "branch_id": B2})
ck("boshqa filialga ocholmaydi", r.status_code, 403)

ck("sotuv menejeri xodim ocholmaydi",
   client.post("/api/users", headers=SAL, json={
       "username": "x", "password": "y", "full_name": "Z",
       "role": "teacher"}).status_code, 403)

print("\n=== 6. MAOSH ALOHIDA HUQUQ ===")

# Filial rahbari kartani tahrirlaydi, lekin oylik raqamiga tegmaydi
r = client.put(f"/api/users/{UID['ustoz']}", headers=BM,
               json={"fix_salary": 99000000})
ck("filial rahbari maoshni o'zgartira olmaydi", r.status_code, 403)
ck("sabab aytildi", "Fiks oylik" in r.json()["detail"], True)

r = client.put(f"/api/users/{UID['ustoz']}", headers=HR,
               json={"fix_salary": 4000000})
ck("HR maoshni o'zgartiradi", r.json()["fix_salary"], 4000000)

r = client.put(f"/api/users/{UID['ustoz']}", headers=FIN,
               json={"fix_salary": 4200000})
ck("moliya direktori ham o'zgartiradi", r.json()["fix_salary"], 4200000)

print("\n=== 7. FILIAL RAHBARI CHEGARASI ===")

r = client.put(f"/api/users/{UID['hr']}", headers=BM, json={"phone": "1"})
ck("boshqa filial xodimini tahrirlay olmaydi", r.status_code, 403)

r = client.put(f"/api/users/{UID['ustoz']}", headers=BM,
               json={"phone": "998911112233"})
ck("o'z filiali xodimini tahrirlaydi", r.status_code, 200)

print("\n=== 8. FRONTEND VA BACKEND BIR XIL ===")

# roles.ts dagi ro'yxat bilan roles.py bir xil bo'lishi shart, aks
# holda tugma ko'rinadi-yu, bosilganda 403 chiqadi
import re
ts = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "..", "frontend", "src", "lib", "roles.ts")).read()
m = re.search(r"HR_ASSIGNABLE_ROLES = \[(.*?)\]", ts, re.S)
ts_names = [x.strip() for x in m.group(1).replace("\n", " ").split(",")
            if x.strip()]
ts_keys = set()
for name in ts_names:
    mm = re.search(rf'export const {name}\s*=\s*"([^"]+)"', ts)
    if mm:
        ts_keys.add(mm.group(1))
ck("HR ro'yxati ikki tomonda bir xil",
   ts_keys, set(roles.HR_ASSIGNABLE_ROLES))

m2 = re.search(r"if \(myRole === BRANCH_MANAGER\)\s*return \[(.*?)\];",
               ts, re.S)
bm_names = [x.strip() for x in m2.group(1).replace("\n", " ").split(",")
            if x.strip()]
bm_keys = set()
for name in bm_names:
    mm = re.search(rf'export const {name}\s*=\s*"([^"]+)"', ts)
    if mm:
        bm_keys.add(mm.group(1))
ck("filial rahbari ro'yxati bir xil",
   bm_keys, set(roles.BRANCH_ASSIGNABLE_ROLES))

print("\n=== 9. AUDIT ===")

db = SessionLocal()
logs = db.query(models.AuditLog).filter(
    models.AuditLog.entity == "user").all()
ck("o'zgarishlar yozildi", len(logs) >= 3, True)
who = {l.user_role for l in logs}
ck("HR o'zgarishlari ham yozildi", "hr_manager" in who, True)
db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
