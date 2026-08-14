"""Global qidiruv: arxiv + telefon raqami; lid dublikati arxivni ham
ko'radi (2026-08-13, Jahongir)."""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/search_arch.db"
if os.path.exists("/tmp/search_arch.db"):
    os.remove("/tmp/search_arch.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient
import main, models
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app); fails = []
def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}" + ("" if ok else f"   (kutilgan {w})"))
    if not ok: fails.append(n)

db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
BID = b.id
faol = models.Student(full_name="Karimov Sardor", branch_id=BID,
                      status="active", phone="+(998) 90-404-47-48")
arx = models.Student(full_name="Ergashev Bobur", branch_id=BID,
                     status="archived", phone="+(998) 91-222-33-44")
db.add_all([faol, arx]); db.commit()
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Administrator", role="administrator",
                branch_id=BID, password_hash=hash_password("x"), is_active=1),
])
db.commit(); db.close()
def tok(u):
    return {"Authorization": "Bearer " + c.post("/api/auth/login",
            json={"username": u, "password": "x"}).json()["access_token"]}
F, A = tok("asos"), tok("adm")

print("=== 1. Arxivdagi o'quvchi ham qidiruvda chiqadi ===")
r = c.get("/api/search/students?q=Ergash", headers=F).json()
names = [x["name"] for x in r["students"]]
ck("arxivdagi topildi", "Ergashev Bobur" in names, True)
ck("arxiv deb belgilangan",
   next(x["archived"] for x in r["students"] if x["name"] == "Ergashev Bobur"), True)
ck("holati yozilgan",
   next(x["status_label"] for x in r["students"] if x["name"] == "Ergashev Bobur"),
   "arxivda")

print("\n=== 2. Telefon raqami bo'yicha qidiruv ===")
for q in ("904044748", "90 404 47 48", "4044748", "+998904044748"):
    rr = c.get(f"/api/search/students?q={q}", headers=F).json()
    ck(f"'{q}' -> Karimov topildi",
       any(x["name"] == "Karimov Sardor" for x in rr["students"]), True)

print("\n=== 3. Administrator ham arxivni ko'radi ===")
ra = c.get("/api/search/students?q=Ergash", headers=A).json()
ck("administratorda ham chiqdi",
   any(x["name"] == "Ergashev Bobur" for x in ra["students"]), True)
ck("arxiv ro'yxati ochiladi",
   c.get("/api/archive/students", headers=A).status_code, 200)

print("\n=== 4. Lid: ARXIVDAGI o'quvchi raqami kiritilsa ogohlantiradi ===")
r4 = c.post("/api/leads", headers=A, json={
    "full_name": "Yangi Odam", "phone": "+998 91 222 33 44",
    "source": "phone", "address": "Zafar", "school": "12-maktab",
    "grade": "5"})
ck("409 qaytadi", r4.status_code, 409)
ck("arxivdagi deb aytadi", "ARXIVDAGI" in str(r4.json().get("detail")), True)
ck("ismi ham aytiladi", "Ergashev Bobur" in str(r4.json().get("detail")), True)

print("\n=== 5. Lid: ISM bir xil bo'lsa ham ogohlantiradi ===")
r5 = c.post("/api/leads", headers=A, json={
    "full_name": "Karimov Sardor", "phone": "+998 99 111 22 33",
    "source": "phone", "address": "Zafar", "school": "12-maktab",
    "grade": "5"})
ck("409 qaytadi", r5.status_code, 409)
ck("mavjud o'quvchi deb aytadi",
   "Karimov Sardor" in str(r5.json().get("detail")), True)

print("\n=== 6. Tasdiqlansa (force) baribir yoziladi ===")
r6 = c.post("/api/leads?force=true", headers=A, json={
    "full_name": "Karimov Sardor", "phone": "+998 99 111 22 33",
    "source": "phone", "force": True, "address": "Zafar",
    "school": "12-maktab", "grade": "5"})
ck("qabul qilindi", r6.status_code, 200)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails)); sys.exit(1)
print("HAMMASI O'TDI")
