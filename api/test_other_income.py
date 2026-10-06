"""QO'SHIMCHA DAROMAD (2026-10-06).

Jahongir: "qo'shimcha daromadlar bo'limini qo'shib ber administratorlar
qila oladigan bo'lsin, pul oqimida ko'rinishi kerak u ham".

Tekshiriladi: administrator kiritadi/tuzatadi, o'chira olmaydi (faqat
moliya — arxivga, bazadan o'chmaydi), filial chegarasi, pul oqimidagi
kirim, kun kassasi, oy boshidagi qoldiq va trend.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "other_income_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
z = models.Branch(name="Zafar"); bk = models.Branch(name="Bekobod 1")
db.add_all([z, bk]); db.commit()
ZID, BID = z.id, bk.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="badm", full_name="Baxriniso",
                role=roles.ADMINISTRATOR, branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="zadm", full_name="Mashxura",
                role=roles.ADMINISTRATOR, branch_id=ZID,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="ust", full_name="Ustoz",
                role=roles.TEACHER, branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
])
db.commit(); db.close()


def H(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


T = roles.local_today()
LED = f"/api/reports/cashflow-ledger?year={T.year}&month={T.month}"
hb, hz, ha, hu = H("badm"), H("zadm"), H("asos"), H("ust")

print("=== Kiritish ===")
r = c.post("/api/other-incomes", headers=hb, json={
    "category": "book_sale", "amount": 50000, "method": "cash",
    "date": T.isoformat(), "note": "Round-up 3"})
ck("administrator kiritadi", r.status_code, 200)
OID = r.json().get("id")
ck("o'z filialiga yozildi", r.json().get("branch_id"), BID)
ck("ustoz kirita olmaydi", c.post("/api/other-incomes", headers=hu, json={
    "category": "other", "amount": 1000}).status_code, 403)
ck("boshqa filialga kirita olmaydi", c.post("/api/other-incomes", headers=hb,
   json={"category": "other", "amount": 1000,
         "branch_id": ZID}).status_code, 403)
ck("summa 0 — rad", c.post("/api/other-incomes", headers=hb, json={
    "category": "other", "amount": 0}).status_code, 400)
ck("noto'g'ri tur — rad", c.post("/api/other-incomes", headers=hb, json={
    "category": "kristal", "amount": 100}).status_code, 400)
ck("kelajak sana — rad", c.post("/api/other-incomes", headers=hb, json={
    "category": "other", "amount": 100,
    "date": (T + timedelta(days=3)).isoformat()}).status_code, 400)
r = c.post("/api/other-incomes", headers=hz, json={
    "category": "mock_exam", "amount": 30000, "method": "card"})
ck("Zafar admini o'z filialiga", r.status_code, 200)

print("=== Ro'yxat va filial chegarasi ===")
lst = c.get(f"/api/other-incomes?year={T.year}&month={T.month}",
            headers=hb).json()
ck("Bekobod admini faqat o'zinikini ko'radi", len(lst["rows"]), 1)
ck("jami", lst["total"], 50000)
ck("admin arxivlay olmaydi (belgi)", lst["can_archive"], False)
lst = c.get(f"/api/other-incomes?year={T.year}&month={T.month}",
            headers=ha).json()
ck("asoschi hammasini ko'radi", len(lst["rows"]), 2)

print("=== Tahrirlash ===")
r = c.put(f"/api/other-incomes/{OID}", headers=hb, json={"amount": 60000})
ck("administrator tuzatadi", r.status_code, 200)
ck("yangi summa", r.json().get("amount"), 60000)
ck("Zafar admini Bekobodnikini tuzata olmaydi",
   c.put(f"/api/other-incomes/{OID}", headers=hz,
         json={"amount": 1}).status_code, 403)

print("=== Pul oqimi (kassa daftari) ===")
led = c.get(LED, headers=hb).json()
oi = [x for x in led["rows"] if x["category"] == "other_income"]
ck("kirim qatori bor", len(oi), 1)
ck("yo'nalish — kirim", oi[0]["direction"] if oi else None, "in")
ck("naqd kirimga qo'shildi", led["kirim"]["cash"], 60000)
ck("other_income jami", led["other_income"], 60000)
ck("kassaga ham tushdi", led["kassa"]["cash"], 60000)

print("=== Kun kassasi ===")
day = c.get("/api/reports/cash-day", headers=hb).json()
ck("bugungi qo'shimcha daromad", day["other_total"], 60000)
ck("kassaga jami = to'lov + qo'shimcha", day["grand_total"],
   day["total"] + 60000)
day = c.get("/api/reports/cash-day", headers=hz).json()
ck("Zafar (faqat bugun) ham ko'radi", day["other_total"], 30000)
ck("Zafar — Click", day["other_rows"][0]["method"] if day["other_rows"]
   else None, "card")

print("=== Oylik trend ===")
tr = c.get("/api/reports/cashflow?months=1", headers=ha).json()
ck("trendda qo'shimcha daromad", tr["totals"]["other_income"], 90000)

print("=== Oy boshidagi qoldiq ===")
if T >= date(2026, 10, 2):
    db = SessionLocal()
    first = T.replace(day=1)
    db.add(models.OtherIncome(date=first - timedelta(days=5),
                              category="rent", amount=20000,
                              method="terminal", branch_id=BID,
                              created_by="test"))
    db.commit(); db.close()
    led = c.get(LED, headers=hb).json()
    ck("o'tgan oy daromadi qoldiqqa o'tdi", led["opening"]["terminal"],
       20000)

print("=== Arxivlash (o'chirmasdan) ===")
ck("administrator o'chira olmaydi",
   c.delete(f"/api/other-incomes/{OID}", headers=hb).status_code, 403)
ck("asoschi arxivlaydi",
   c.delete(f"/api/other-incomes/{OID}", headers=ha).status_code, 200)
db = SessionLocal()
o = db.query(models.OtherIncome).get(OID)
ck("bazada qoldi", o is not None, True)
ck("archived_at qo'yildi", o.archived_at is not None if o else None, True)
db.close()
led = c.get(LED, headers=hb).json()
ck("arxivdagi pul oqimidan chiqdi",
   len([x for x in led["rows"] if x["category"] == "other_income"]), 0)
ck("ro'yxatdan ham chiqdi", len(c.get(
    f"/api/other-incomes?year={T.year}&month={T.month}",
    headers=hb).json()["rows"]), 0)

print("\n" + ("HAMMASI OK" if not fails else f"{len(fails)} XATO: {fails}"))
sys.exit(1 if fails else 0)
