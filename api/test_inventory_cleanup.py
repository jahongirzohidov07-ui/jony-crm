"""OMBOR TARTIBI (2026-10-14).

Jahongir: "omborda mahsulotlar juda tartibsiz takrorlari ko'p ...
chunarsiz mantiqsizlikni tozalab ber ishlatishga oson qil".

Tekshiriladi:
  1. Minimal 0 = kuzatilmaydi: "kam qolgan" emas, xarid so'rovi
     ochilmaydi; eski keraksiz avtomat so'rovlar o'zi yopiladi.
  2. Shu filialda shu nomli mahsulot ikkinchi marta ochilmaydi (409),
     boshqa filialda ochiladi; xarajatdagi "yangi kitob" bor kitobni
     ishlatadi.
  3. Sanoq: polkadagi sonni yozsa, farq o'zi hisoblanadi.
  4. Takrorlar ro'yxati va birlashtirish: qoldiq qo'shiladi, tarix,
     so'rov, xarajat bog'lanishlari ko'chadi; turli filial — 400.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "inventory_cleanup_test")
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
b1 = models.Branch(name="Zafar"); b2 = models.Branch(name="Chilonzor")
db.add_all([b1, b2]); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER, is_active=1))
db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}

print("=== 1. MINIMAL 0 — KUZATILMAYDI ===")
# Eski xato holat: minimal 0, qoldiq 0 mahsulotga ochilib qolgan so'rov
old = models.Consumable(name="Eski kitob", kind="book", branch_id=b1.id,
                        qty=0, min_qty=0, unit="dona")
db.add(old); db.commit()
db.add(models.PurchaseRequest(consumable_id=old.id, qty=1, auto=1,
                              status="open")); db.commit()
d = c.get(f"/api/consumables?branch_id={b1.id}", headers=H).json()
row = next(r for r in d["rows"] if r["name"] == "Eski kitob")
ck("minimal 0 — kam qolgan emas", row["low"], False)
ck("keraksiz so'rov o'zi yopildi", len(d["requests"]), 0)
db.expire_all()
ck("so'rov bazada cancelled",
   db.query(models.PurchaseRequest).first().status, "cancelled")
r = c.post("/api/consumables", headers=H, json={
    "name": "Marker", "kind": "marker", "branch_id": b1.id,
    "qty": 2, "min_qty": 5})
mk = r.json()
ck("minimal belgilangan — kam qolgan", mk["low"], True)
ck("so'rov ochildi", bool(mk["request_id"]), True)

print("\n=== 2. TAKRORGA QARSHI ===")
r = c.post("/api/consumables", headers=H, json={
    "name": "Step 1", "kind": "book", "branch_id": b1.id})
ck("birinchisi ochildi", r.status_code, 200)
S1 = r.json()["id"]
r = c.post("/api/consumables", headers=H, json={
    "name": "step-1 ", "kind": "book", "branch_id": b1.id})
ck("shu filialda 'step-1' — 409", r.status_code, 409)
ck("xabarda bor mahsulot nomi", "Step 1" in r.json().get("detail", ""), True)
r = c.post("/api/consumables", headers=H, json={
    "name": "Step 1", "kind": "book", "branch_id": b2.id})
ck("boshqa filialda ochiladi", r.status_code, 200)
r = c.post("/api/expenses", headers=H, json={
    "date": date.today().isoformat(), "category": "book",
    "amount": 100000, "branch_id": b1.id, "qty": 4,
    "new_item_name": "STEP 1", "method": "cash"})
ck("xarajat saqlandi", r.status_code, 200)
db.expire_all()
cnt = (db.query(models.Consumable)
       .filter(models.Consumable.branch_id == b1.id,
               models.Consumable.kind == "book").count())
ck("xarajatdagi 'STEP 1' yangi kitob ochmadi", cnt, 2)   # Eski kitob + Step 1
ck("kirim bor kitobga tushdi", db.query(models.Consumable).get(S1).qty, 4)

print("\n=== 3. SANOQ ===")
r = c.post(f"/api/consumables/{S1}/move", headers=H,
           json={"reason": "count", "qty": 3})
ck("sanoqdan keyin qoldiq 3", r.json()["qty"], 3)
mv = c.get(f"/api/consumables/{S1}/moves", headers=H).json()[0]
ck("harakat -1", mv["delta"], -1)
ck("izohda sanoq", mv["note"].startswith("Sanoq: tizimda 4"), True)
r = c.post(f"/api/consumables/{S1}/move", headers=H,
           json={"reason": "count", "qty": -2})
ck("manfiy sanoq — 400", r.status_code, 400)

print("\n=== 4. BIRLASHTIRISH ===")
# Eski ma'lumotdagi takrorlar (API ga qadar yaratilgan)
d1 = models.Consumable(name="step 1", kind="book", branch_id=b1.id,
                       qty=5, min_qty=2, unit="dona", unit_price=45000)
d2 = models.Consumable(name="Step-1", kind="other", branch_id=b1.id,
                       qty=1, min_qty=0, unit="dona")
db.add_all([d1, d2]); db.commit()
D1, D2 = d1.id, d2.id
db.add(models.StockMove(consumable_id=d1.id, delta=5, reason="in"))
exp = db.query(models.Expense).first()
exp.consumable_id = d1.id
db.commit()
dd = c.get("/api/consumables/duplicates", headers=H).json()
ck("1 guruh, 2 ta ortiqcha", (len(dd["groups"]), dd["count"]), (1, 2))
g = dd["groups"][0]
ck("guruh Zafar filialida", g["branch"], "Zafar")
ck("jami qoldiq 3+5+1", g["total_qty"], 9)
ck("tavsiya: tarixi ko'p / eng eski yozuv qoladi", g["keep_id"], S1)
lst = c.get(f"/api/consumables?branch_id={b1.id}", headers=H).json()
ck("ro'yxatda takror soni", lst["duplicates"], 2)
r = c.post("/api/consumables/merge", headers=H, json={
    "keep_id": S1, "merge_ids": [d1.id, d2.id], "name": "Step 1"})
ck("birlashtirildi", r.status_code, 200)
m = r.json()
ck("qoldiqlar qo'shildi", m["qty"], 9)
ck("minimal eng kattasi", m["min_qty"], 2)
ck("qoladigan mahsulot narxi saqlandi (100000/4)", m["unit_price"], 25000)
db.expire_all()
ck("takrorlar o'chdi",
   db.query(models.Consumable).filter(
       models.Consumable.id.in_([D1, D2])).count(), 0)
ck("harakatlar tarixi ko'chdi",
   db.query(models.StockMove).filter(
       models.StockMove.consumable_id == S1).count(), 3)
ck("xarajat bog'lanishi ko'chdi",
   db.query(models.Expense).first().consumable_id, S1)
ck("endi takror yo'q",
   c.get("/api/consumables/duplicates", headers=H).json()["count"], 0)
other = c.get(f"/api/consumables?branch_id={b2.id}", headers=H).json()
b2s1 = next(x for x in other["rows"] if x["name"] == "Step 1")["id"]
r = c.post("/api/consumables/merge", headers=H, json={
    "keep_id": S1, "merge_ids": [b2s1]})
ck("turli filial — 400", r.status_code, 400)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
