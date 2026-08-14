"""Oila a'zosi boshqa filialda (2026-08-14, Jahongir)."""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/fam_branch.db"
if os.path.exists("/tmp/fam_branch.db"): os.remove("/tmp/fam_branch.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient
import main, models
import entry  # noqa
from database import SessionLocal
from auth import hash_password
c = TestClient(main.app); fails=[]
def ck(n,g,w):
    ok=g==w; print(("OK  " if ok else "XATO ")+n+f": {g}"+("" if ok else f"  (kutilgan {w})"))
    if not ok: fails.append(n)

db=SessionLocal()
b1=models.Branch(name="Bekobod 1"); b2=models.Branch(name="Zafar")
db.add_all([b1,b2]); db.commit(); B1,B2=b1.id,b2.id
aka=models.Student(full_name="Xolmatov Aziz", branch_id=B1, status="active")
uka=models.Student(full_name="Xolmatova Nilufar", branch_id=B2, status="active")
ozi=models.Student(full_name="Xolmatov Boshqa", branch_id=B1, status="active")
db.add_all([aka,uka,ozi]); db.commit(); AKA,UKA,OZI=aka.id,uka.id,ozi.id
db.add_all([
  models.User(username="adm", full_name="Administrator", role="administrator",
              branch_id=B1, password_hash=hash_password("x"), is_active=1),
  models.User(username="asos", full_name="Asoschi", role="founder",
              password_hash=hash_password("x"), is_active=1)])
db.commit(); db.close()
def tok(u): return {"Authorization":"Bearer "+c.post("/api/auth/login",
    json={"username":u,"password":"x"}).json()["access_token"]}
A, F = tok("adm"), tok("asos")

print("=== 1. Ptichkasiz: faqat O'Z filialidan ===")
r=c.get(f"/api/family-search?q=Xolmat&exclude={AKA}", headers=A).json()
names=[x["full_name"] for x in r]
ck("o'z filialidagi chiqdi", "Xolmatov Boshqa" in names, True)
ck("boshqa filialdagi chiqmadi", "Xolmatova Nilufar" in names, False)
ck("o'zi chiqmadi", "Xolmatov Aziz" in names, False)

print("\n=== 2. Ptichka bilan: BOSHQA filiallardan ===")
r2=c.get(f"/api/family-search?q=Xolmat&other_branch=1&exclude={AKA}",
         headers=A).json()
n2=[x["full_name"] for x in r2]
ck("boshqa filialdagi chiqdi", "Xolmatova Nilufar" in n2, True)
ck("o'z filialidagi chiqmadi", "Xolmatov Boshqa" in n2, False)
ck("filial nomi ko'rinadi", r2[0]["branch"], "Zafar")

print("\n=== 3. Boshqa filialdagi bilan oila qilib bog'lash ===")
r3=c.post(f"/api/students/{AKA}/family-link", headers=A,
          json={"sibling_id": UKA})
ck("bog'landi (familiya bir xil)", r3.json().get("status"), "linked")
ck("ikkalasiga 10%", r3.json().get("family_percent"), 10.0)
d=c.get(f"/api/students/{UKA}/discounts", headers=F).json()
ck("boshqa filialdagida ham 10%", d["family_percent"], 10.0)

print("\n=== 4. Qidiruv 3 harfdan kam bo'lsa bo'sh ===")
ck("bo'sh", c.get("/api/family-search?q=Xo", headers=A).json(), [])

print()
if fails: print("XATOLAR:", ", ".join(fails)); sys.exit(1)
print("HAMMASI O'TDI")
