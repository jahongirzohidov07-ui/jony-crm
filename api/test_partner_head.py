"""HAMKOR MARKAZ (STECH) RAHBARI (2026-09-17).

Jahongir: "stech filial rahbariga markaz bo'yicha barcha funksiyalarni
ochib qoy, qolgan filial rahbarlariga emas" + "Stetchga doir barcha
narsa va funksiyalar moliyaviy hammasi ochiladigan bolsin".

Tekshiriladi: Stech rahbari moliyaviy (asoschi darajasidagi) amallarni
O'Z markazida bajaradi; Jony Academy ma'lumoti unga yopiq; oddiy
filial rahbarida hech narsa o'zgarmaydi.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "partner_head_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
jb = models.Branch(name="Bekobod 1")
sb = models.Branch(name="Stech", is_partner=1)
db.add_all([jb, sb]); db.commit()
JB, SB = jb.id, sb.id
db.add_all([
    models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER),
    models.User(username="stech", password_hash=hash_password("x"),
                full_name="Stech rahbari", role=roles.BRANCH_MANAGER,
                branch_id=SB),
    models.User(username="jony", password_hash=hash_password("x"),
                full_name="Jony filial rahbari",
                role=roles.BRANCH_MANAGER, branch_id=JB),
])
sst = models.Student(full_name="Stech bola", branch_id=SB, status="active")
jst = models.Student(full_name="Jony bola", branch_id=JB, status="active")
db.add_all([sst, jst]); db.commit()
SST, JST = sst.id, jst.id
sp = models.Payment(student_id=SST, amount=100000, kind="payment",
                    method="cash", created_by="x")
jp = models.Payment(student_id=JST, amount=200000, kind="payment",
                    method="cash", created_by="x")
db.add_all([sp, jp,
            models.Payment(student_id=JST, amount=-70000, kind="discount",
                           created_by="x")])
db.commit()
SP, JP = sp.id, jp.id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


S, J, F = tok("stech"), tok("jony"), tok("asos")

print("=== 1. Belgi ===")
ck("Stech rahbari partner_head", c.get("/api/me", headers=S).json()
   .get("partner_head"), True)
ck("oddiy filial rahbari emas", c.get("/api/me", headers=J).json()
   .get("partner_head"), False)

print("\n=== 2. Moliya bosh sahifasi ===")
ck("Stech: ochiq", c.get("/api/finance/overview", headers=S).status_code, 200)
ck("oddiy rahbar: yopiq",
   c.get("/api/finance/overview", headers=J).status_code, 403)
ck("asoschi: ochiq", c.get("/api/finance/overview", headers=F).status_code,
   200)

print("\n=== 3. Reja (faqat o'z markazi) ===")
body = {"items": [{"metric": "leads", "month": 10, "value": 50}]}
ck("Stech o'z rejasini kiritadi",
   c.put(f"/api/plan/2026?branch_id={SB}", headers=S, json=body)
   .status_code, 200)
ck("Jony rejasiga yozolmaydi",
   c.put(f"/api/plan/2026?branch_id={JB}", headers=S, json=body)
   .status_code, 403)
ck("oddiy rahbar reja kiritolmaydi",
   c.put(f"/api/plan/2026?branch_id={JB}", headers=J, json=body)
   .status_code, 403)
r = c.get(f"/api/plan?year=2026&branch_id={JB}", headers=S).json()
ck("Jony rejasini ochsa ham o'zinikiga qaytadi", r.get("branch_id"), SB)
ck("tahrirlash mumkin", r.get("can_edit"), True)
ck("filial tanlagichi yo'q", r.get("branches"), [])

print("\n=== 4. Budjet (faqat o'z markazi) ===")
r = c.put("/api/finance/budget/2026", headers=S, json={"items": [
    {"month": 10, "kind": "expense", "category": "rent",
     "branch_id": JB, "amount": 999}]})
ck("budjet saqlandi", r.status_code, 200)
db = SessionLocal()
ck("qator Stech'ga yozildi (Jony'ga emas)",
   [x.branch_id for x in db.query(models.BudgetLine).all()], [SB])
db.close()
ck("oddiy rahbar budjet yozolmaydi",
   c.put("/api/finance/budget/2026", headers=J, json={"items": []})
   .status_code, 403)
b = c.get("/api/finance/budget?year=2026&month=10", headers=S).json()
ck("budjetda faqat Stech filiali", [x["branch"] for x in b["branches"]],
   ["Stech"])
ck("budjet tahrirlanadi", b["can_edit"], True)

print("\n=== 5. Refund (faqat o'z o'quvchisi) ===")
rb = {"amount": 10000, "reason": "test"}
ck("Stech o'quvchisiga refund",
   c.post("/api/refunds", headers=S, json={**rb, "student_id": SST})
   .status_code, 200)
ck("Jony o'quvchisiga yo'q",
   c.post("/api/refunds", headers=S, json={**rb, "student_id": JST})
   .status_code, 403)

print("\n=== 6. To'lov yozuvini o'chirish ===")
ck("oddiy rahbar pul kirimini o'chira olmaydi",
   c.delete(f"/api/payments/{SP}?reason=xato", headers=J).status_code, 403)
ck("Jony to'lovi Stech rahbariga yopiq",
   c.delete(f"/api/payments/{JP}?reason=xato", headers=S).status_code, 403)
ck("Stech o'z to'lovini o'chiradi",
   c.delete(f"/api/payments/{SP}?reason=xato", headers=S).status_code, 200)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
