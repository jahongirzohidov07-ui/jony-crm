"""Oilaviy chegirma: bir marta bog'lash - IKKALASIGA 10% (2026-08).

Jahongir: "bitta oquvchini boshqasiga oila deb boglanganda nargisini
yana bunga qayta yana boglab otirilmasin avtomat ikkalasiga 10%
chegirmani hisoblayversin" va "10% chegirma berganimdan keyin
o'quvchi profilida jami chegirmada 0% turibdi u ham ishlashi kerakku"
(sabab: chegirmaning boshlanish sanasi KELAJAKDA edi - endi buni
ekranda ko'rsatamiz)."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/family_disc_test.db"
if os.path.exists("/tmp/family_disc_test.db"):
    os.remove("/tmp/family_disc_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
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
b = models.Branch(name="Zafar"); db.add(b); db.commit()
BID = b.id
g = models.Group(name="G1", branch_id=BID, monthly_fee=500000.0)
db.add(g); db.commit()
GID = g.id
aka = models.Student(full_name="Abdushukurov Islombek", branch_id=BID,
                     group_id=GID, status="active")
uka = models.Student(full_name="Abdushukurova Ziynat", branch_id=BID,
                     group_id=GID, status="active")
begona = models.Student(full_name="Toshmatov Sardor", branch_id=BID,
                        group_id=GID, status="active")
db.add_all([aka, uka, begona]); db.commit()
AKA, UKA, BEGONA = aka.id, uka.id, begona.id
db.add(models.User(username="asos", full_name="Asoschi", role="founder",
                   password_hash=hash_password("x"), is_active=1))
db.commit()
db.close()

F = tok("asos")

print("=== 1. Bog'lashdan OLDIN chegirma yo'q ===")
d = client.get(f"/api/students/{AKA}/discounts", headers=F).json()
ck("oilaviy chegirma 0%", d["family_percent"], 0)

print("\n=== 2. Bir marta bog'laymiz (aka -> uka) ===")
r = client.post(f"/api/students/{AKA}/family-link", headers=F,
                json={"sibling_id": UKA})
ck("bog'lash muvaffaqiyatli", r.status_code, 200)
ck("oilada 2 ta faol farzand", r.json().get("active_children"), 2)
ck("oilaviy chegirma 10%", r.json().get("family_percent"), 10.0)

print("\n=== 3. TESKARI tomon: ukaga QAYTA bog'lash SHART EMAS ===")
d2 = client.get(f"/api/students/{UKA}/discounts", headers=F).json()
ck("ukada ham oilaviy chegirma 10%", d2["family_percent"], 10.0)
ck("ukada jami chegirma 10%", d2["total_percent"], 10.0)
p2 = client.get(f"/api/students/{UKA}/pricing", headers=F).json()
ck("ukaning to'lovi 10% kam", p2["final_fee"], 450000.0)
ck("aka uning oilasida ko'rinadi",
   [x["id"] for x in p2["siblings"]], [AKA])

print("\n=== 4. Uchinchi bola qo'shilsa ham bitta bog'lash yetadi ===")
r3 = client.post(f"/api/students/{BEGONA}/family-link", headers=F,
                 json={"sibling_id": AKA})
ck("uchinchisi qo'shildi", r3.json().get("active_children"), 3)
d3 = client.get(f"/api/students/{BEGONA}/discounts", headers=F).json()
ck("uchinchisida ham 10%", d3["family_percent"], 10.0)

print("\n=== 5. Biri ketsa chegirma O'ZI yo'qoladi ===")
db = SessionLocal()
for sid in (UKA, BEGONA):
    st = db.query(models.Student).get(sid)
    st.status = "left"
db.commit(); db.close()
d4 = client.get(f"/api/students/{AKA}/discounts", headers=F).json()
ck("bitta faol farzand qoldi - chegirma yo'q", d4["family_percent"], 0)

print("\n=== 6. Kelajakda boshlanadigan chegirma: 0% emas, izohli ===")
soon = (date.today() + timedelta(days=20)).isoformat()
r5 = client.post("/api/discounts", headers=F, json={
    "student_id": AKA, "kind": "grant", "percent": 10,
    "reason": "bilimi uchun", "start_date": soon})
ck("chegirma yaratildi", r5.status_code, 200)
d5 = client.get(f"/api/students/{AKA}/discounts", headers=F).json()
ck("bugungi jami chegirma 0% (hali boshlanmagan)", d5["total_percent"], 0)
ck("kelgusi chegirma 10% deb ko'rsatiladi", d5["upcoming_percent"], 10.0)
ck("boshlanish sanasi ham qaytadi", d5["upcoming_from"], soon)

print("\n=== 7. BUGUNDAN boshlangan chegirma darrov hisobga olinadi ===")
r6 = client.post("/api/discounts", headers=F, json={
    "student_id": BEGONA, "kind": "grant", "percent": 20,
    "reason": "olimpiada"})
ck("yaratildi", r6.status_code, 200)
d6 = client.get(f"/api/students/{BEGONA}/discounts", headers=F).json()
ck("jami chegirma 20%", d6["total_percent"], 20.0)
p6 = client.get(f"/api/students/{BEGONA}/pricing", headers=F).json()
ck("Narx blokida ham 20% ko'rinadi", p6["granted_discount"], 20.0)
ck("to'lanadigan 400 000", p6["final_fee"], 400000.0)

print("\n=== 8. O'zini o'ziga bog'lab bo'lmaydi ===")
r7 = client.post(f"/api/students/{AKA}/family-link", headers=F,
                 json={"sibling_id": AKA})
ck("xato qaytadi", r7.status_code, 400)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
