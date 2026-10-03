"""HAMKOR MARKAZ (STETCH) — DUBLIKAT TEKSHIRUVI ALOHIDA (2026-10-03).

Jahongir: "ITga keladiganlar umuman boshqa filial, boshqa markaz,
aloqamiz yo'q — bunaqa narsa unga kerak emas" (Stetch lidini o'quvchiga
aylantirganda Bekobod 1 dagi arxivdagi o'quvchi bilan "bazada bor" deb
to'xtatardi).

Tekshiriladi:
  1. Stetch lidi — Jony'dagi bir xil raqamli o'quvchi to'xtatmaydi.
  2. Jony filiali lidi — avvalgidek 409 (Jony ichida dublikat).
  3. Stetch ichida dublikat bo'lsa — 409.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "partner_dup_scope_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

common._ensure_month_charges = lambda db, **kw: None
c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
st = models.Branch(name="Stetch", is_partner=1)
bk = models.Branch(name="Bekobod 1")
za = models.Branch(name="Zafar")
db.add_all([st, bk, za]); db.commit()
ST, BK, ZA = st.id, bk.id, za.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER, is_active=1))
db.add(models.Student(full_name="Mirfozilov Kamron", phone="+998901112233",
                      branch_id=BK, status="archived"))
db.add(models.Student(full_name="IT bola", phone="+998907778899",
                      branch_id=ST, status="active"))
db.commit()


def lead(name, phone, br):
    ld = models.Lead(full_name=name, phone=phone, branch_id=br, stage="new")
    db.add(ld); db.commit()
    return ld.id


L1 = lead("Mirfozilov Kamron", "+998901112233", ST)
L2 = lead("Mirfozilov Kamron", "+998901112233", ZA)
L3 = lead("Boshqa IT bola", "+998907778899", ST)
db.close()
H = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asos", "password": "x"}).json()["access_token"]}


def conv(lid):
    return c.post(f"/api/leads/{lid}/convert", headers=H, json={}).status_code


print("=== Lidni o'quvchiga aylantirish ===")
ck("Stetch lidi — Jony'dagi arxiv to'xtatmaydi", conv(L1), 200)
ck("Zafar lidi — Bekoboddagi arxiv bilan 409", conv(L2), 409)
ck("Stetch ichidagi dublikat — 409", conv(L3), 409)

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
