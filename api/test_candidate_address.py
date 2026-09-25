"""NOMZODNING YASHASH JOYI RO'YXATDA KO'RINADI (2026-09-24).

Jahongir: "hr bo'limi nomzodlar uchun yashash joyi chiqib tursin
karta ochilmasdan turib ham".

Manzil arizada allaqachon so'ralardi va bazada saqlanardi, lekin
faqat nomzod kartasi ochilganda ko'rinardi — HR har birini ochib
chiqishga majbur edi.

Tekshiriladi:
  A. Nomzodlar ro'yxatida manzil bor;
  B. Kanban (ishga olish quvuri) kartochkasida ham bor;
  C. Manzil kiritilmagan nomzodda bo'sh qaytadi, xato bermaydi.
"""
import os
import sys
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "cand_address_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="hr", full_name="HR Nodira",
                   password_hash=hash_password("Parol123!"),
                   role=roles.HR_MANAGER, branch_id=BID, is_active=1))
db.commit()
db.close()

HH = {"Authorization": "Bearer " + client.post(
    "/api/auth/login",
    json={"username": "hr", "password": "Parol123!"}
).json()["access_token"]}

r = client.post("/api/candidates", headers=HH, json={
    "full_name": "Nomzod Aziza", "phone": "901234567",
    "position": "teacher", "subject": "Ingliz tili",
    "address": "Chilonzor 9-kvartal, 12-uy", "branch_id": BID})
ck("nomzod qo'shildi", r.status_code, 200)
r = client.post("/api/candidates", headers=HH, json={
    "full_name": "Nomzod Bekzod", "phone": "901234568",
    "position": "teacher", "branch_id": BID})
ck("manzilsiz nomzod ham qo'shildi", r.status_code, 200)

print("\n=== A. RO'YXATDA MANZIL BOR ===")
rows = client.get("/api/candidates", headers=HH).json()
by = {x["full_name"]: x for x in rows}
ck("manzil qaytdi", by["Nomzod Aziza"]["address"],
   "Chilonzor 9-kvartal, 12-uy")
ck("kartani ochish shart emas", "address" in by["Nomzod Aziza"], True)

print("\n=== B. KANBANDA HAM ===")
p = client.get("/api/ats/pipeline", headers=HH).json()
cards = [r for col in p["columns"] for r in col["rows"]]
byc = {x["candidate"]: x for x in cards}
ck("kartochkada manzil bor", byc["Nomzod Aziza"]["address"],
   "Chilonzor 9-kvartal, 12-uy")

print("\n=== C. MANZILSIZ NOMZOD ===")
ck("bo'sh qaytadi, xato yo'q", by["Nomzod Bekzod"]["address"], None)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
