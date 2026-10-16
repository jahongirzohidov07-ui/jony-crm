"""TERMINAL ↔ NAQD O'TKAZMASI (2026-10-16).

Jahongir: terminaldagi pulni bankdan naqd yechish — bank 1% oladi, naqd
kassaga sof summa o'zi tushsin; naqdni terminalga topshirish — to'liq
avtomat. Keyin: o'quv markazda egasiga foyda yechish turi bo'lmaydi —
faqat shu ikki tur.

Tekshiriladi:
  1. O'tkazmasiz holatda qoldiqlar o'zgarmaydi (bloklar 0, satr yo'q).
  2. W: 1 000 000 -> komissiya 10 000 (1%), naqd +990 000, terminal
     −1 000 000, P&L da xarajat 10 000 — BIR MARTA (pnl, oy yopilishi,
     trend, xarajatlar ro'yxati), kirim/tushum o'zgarmaydi.
  3. D: naqd −, terminal +, P&L ga ta'siri yo'q.
  4. Qoldiqdan oshiq summa — aniq o'zbekcha 400; force faqat
     rahbariyat/moliyada.
  5. Tahrirlash/o'chirish — faqat rahbariyat/moliya; komissiya xarajati
     yangilanadi/o'chadi; audit.
  6. Filial chegarasi.
  7. Foiz o'zgarsa — faqat yangi o'tkazmalarga.
  8. Oy boshidagi qoldiq va oylar kesimi.
  9. Bunday yechim turi (egasiga foyda) hech qayerda yo'q.
"""
import os
import re
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "bank_cash_transfer_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

common._ensure_month_charges = lambda db, **kw: None

# Postgres'dagidek tashqi kalitlar (FK) shu yerda ham tekshirilsin:
# o'tkazma (fee_expense_id) va komissiya xarajatini o'chirish tartibi
# jonli bazada xato bermasligi kerak.
from sqlalchemy import event                       # noqa: E402
from database import engine                        # noqa: E402


@event.listens_for(engine, "connect")
def _fk_on(dbapi_con, _rec):
    dbapi_con.execute("PRAGMA foreign_keys=ON")


engine.dispose()

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


T = roles.local_today()
FIRST = T.replace(day=1)
YM = f"year={T.year}&month={T.month}"

db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Bekobod 2")
b3 = models.Branch(name="Bekobod 3"); zf = models.Branch(name="Zafar")
db.add_all([b1, b2, b3, zf]); db.commit()
B1, B2, B3, ZF = b1.id, b2.id, b3.id, zf.id


def mk(login, role, br=None):
    db.add(models.User(username=login, full_name=login.capitalize(),
                       role=role, branch_id=br, is_active=1,
                       password_hash=hash_password("x")))
    db.commit()


mk("asos", roles.FOUNDER)
mk("fin", roles.FINANCE_DIRECTOR)
mk("adm", roles.ADMINISTRATOR, B1)
mk("adm2", roles.ADMINISTRATOR, B2)
mk("rah2", roles.BRANCH_MANAGER, B2)
mk("zadm", roles.ADMINISTRATOR, ZF)
mk("ust", roles.TEACHER, B1)

# Kassa: B1 — terminal 3 000 000, naqd 200 000 (shu oy boshida)
db.add_all([
    models.OtherIncome(date=FIRST, category="other", amount=3_000_000,
                       method="terminal", branch_id=B1, created_by="t"),
    models.OtherIncome(date=FIRST, category="other", amount=200_000,
                       method="cash", branch_id=B1, created_by="t"),
    models.OtherIncome(date=FIRST, category="other", amount=800_000,
                       method="terminal", branch_id=ZF, created_by="t"),
])
db.commit(); db.close()


def H(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


ha, hf, hb, hb2, hr2, hz, hu = (H("asos"), H("fin"), H("adm"), H("adm2"),
                                H("rah2"), H("zadm"), H("ust"))
LED = f"/api/reports/cashflow-ledger?{YM}&branch_id={B1}"


def led(h=ha, q=LED):
    return c.get(q, headers=h).json()


def pnl():
    return c.get(f"/api/reports/pnl?{YM}&branch_id={B1}", headers=ha).json()


def fee_rows():
    s = SessionLocal()
    try:
        return [(e.id, e.amount, e.method, e.branch_id) for e in
                s.query(models.Expense)
                .filter(models.Expense.category == "bank_fee").all()]
    finally:
        s.close()


def snap():
    L = led()
    P = pnl()
    return (L["opening"], L["kirim"], L["chiqim"], L["kassa"],
            P["expenses_total"], P["profit"], len(L["rows"]))


print("=== 1. O'tkazmasiz — qoldiqlar o'zgarmaydi ===")
L0 = led()
ck("o'tkazma bloki jami 0", L0["otkazma"]["total"], 0)
ck("o'tkazma bloki naqd 0", L0["otkazma"]["cash"], 0)
ck("kassa terminal = kirim", L0["kassa"]["terminal"], 3_000_000)
ck("kassa naqd = kirim", L0["kassa"]["cash"], 200_000)
ck("transfer satri yo'q",
   len([r for r in L0["rows"] if r["direction"] == "transfer"]), 0)
day0 = c.get(f"/api/reports/cash-day?day={T.isoformat()}&branch_id={B1}",
             headers=ha).json()
ck("kun kassasida o'tkazma yo'q", day0["transfer_rows"], [])
ck("kun kassasida ta'sir yo'q", day0["transfer_effect"], [])
S0 = snap()
P0 = pnl()
ck("P&L xarajat 0", P0["expenses_total"], 0)
TREND0 = c.get("/api/reports/cashflow?months=1", headers=ha).json()["totals"]

print("=== 9. Faqat ikki tur (egasiga foyda yechish yo'q) ===")
ck("turlar", [k for k, _ in roles.BANK_TRANSFER_KINDS],
   ["withdraw", "deposit"])
r = c.post("/api/bank-transfers", headers=ha, json={
    "kind": "dividend", "amount": 100_000, "branch_id": B1})
ck("noma'lum tur — 400", r.status_code, 400)
r = c.post("/api/bank-transfers", headers=ha, json={
    "kind": "owner_withdraw", "amount": 100_000, "branch_id": B1})
ck("egasiga yechish — 400", r.status_code, 400)
lst = c.get(f"/api/bank-transfers?{YM}&branch_id={B1}", headers=ha).json()
ck("ro'yxatdagi turlar", [k["key"] for k in lst["kinds"]],
   ["withdraw", "deposit"])
pat = re.compile(r"dividend|divident", re.I)
hits = []
for root in (_HERE, os.path.join(os.path.dirname(_HERE), "src")):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ("node_modules", "__pycache__")]
        for f in fn:
            if f.startswith("test_") or not f.endswith((".py", ".ts", ".tsx")):
                continue
            p = os.path.join(dp, f)
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            if pat.search(txt):
                hits.append(os.path.relpath(p, os.path.dirname(_HERE)))
ck("kodda bunday tur/yozuv yo'q (api + src)", hits, [])
ck("xarajat turlarida ham yo'q",
   [k for k in roles.EXPENSE_CATEGORIES if pat.search(k)], [])

print("=== Huquq: ustoz ===")
ck("ustoz ro'yxatni ko'rmaydi",
   c.get("/api/bank-transfers", headers=hu).status_code, 403)
ck("ustoz kirita olmaydi", c.post("/api/bank-transfers", headers=hu, json={
    "kind": "withdraw", "amount": 1000}).status_code, 403)

print("=== 2. W: terminaldan naqd yechish ===")
r = c.post("/api/bank-transfers", headers=hb, json={
    "kind": "withdraw", "amount": 1_000_000, "date": T.isoformat(),
    "note": "Bank kassasi"})
ck("administrator kiritadi", r.status_code, 200)
W = r.json()
W1 = W.get("id")
ck("o'z filialiga", W.get("branch_id"), B1)
ck("foiz 1%", W.get("fee_rate"), 1.0)
ck("komissiya 10 000", W.get("fee"), 10_000)
ck("sof 990 000", W.get("net"), 990_000)
ck("terminaldan", W.get("from_method"), "terminal")
ck("naqdga", W.get("to_method"), "cash")
ck("yozuv matni", W.get("title"),
   "Terminaldan naqdga: 1 000 000 (komissiya 1% — 10 000) → naqd +990 000")
FR = fee_rows()
ck("komissiya xarajati BITTA", len(FR), 1)
ck("komissiya summasi", FR[0][1] if FR else None, 10_000)
ck("komissiya terminaldan", FR[0][2] if FR else None, "terminal")
ck("komissiya filiali", FR[0][3] if FR else None, B1)
FEE_ID = FR[0][0] if FR else None
ck("o'tkazmaga bog'langan", W.get("fee_expense_id"), FEE_ID)

L = led()
ck("kirim naqd o'zgarmadi", L["kirim"]["cash"], 200_000)
ck("kirim terminal o'zgarmadi", L["kirim"]["terminal"], 3_000_000)
ck("kirim jami o'zgarmadi", L["kirim"]["total"], 3_200_000)
ck("chiqim = faqat komissiya", L["chiqim"]["total"], 10_000)
ck("chiqim terminaldan", L["chiqim"]["terminal"], 10_000)
ck("o'tkazma naqd +990 000", L["otkazma"]["cash"], 990_000)
ck("o'tkazma terminal −990 000", L["otkazma"]["terminal"], -990_000)
ck("o'tkazma jami 0", L["otkazma"]["total"], 0)
ck("kassa terminal −1 000 000", L["kassa"]["terminal"], 2_000_000)
ck("kassa naqd +990 000", L["kassa"]["cash"], 1_190_000)
ck("kassa jami −komissiya", L["kassa"]["total"], 3_190_000)
tr = [x for x in L["rows"] if x["direction"] == "transfer"]
ck("daftarda o'tkazma satri", len(tr), 1)
ck("satr matni", tr[0]["title"] if tr else None, W.get("title"))
fr = [x for x in L["rows"] if x.get("category") == "bank_fee"]
ck("daftarda komissiya satri bitta", len(fr), 1)
ck("komissiya — chiqim", fr[0]["direction"] if fr else None, "out")

P = pnl()
ck("P&L xarajat = komissiya", P["expenses_total"], 10_000)
ck("P&L da bank_fee bir marta",
   [(x["category"], x["amount"]) for x in P["expense_lines"]],
   [("bank_fee", 10_000)])
ck("P&L daromad o'zgarmadi", P["income"], P0["income"])
ck("P&L foyda −komissiya", P["profit"], P0["profit"] - 10_000)

mc = c.get(f"/api/month-close?{YM}&branch_id={B1}", headers=ha).json()
ck("oy yopilishi: xarajat 10 000", mc["expenses"]["total"], 10_000)
ck("oy yopilishi: yorliq",
   [(x["category"], x["label"]) for x in mc["expenses"]["lines"]],
   [("bank_fee", "Bank komissiyasi (1%)")])
yr = T.year if T.month >= 9 else T.year - 1
pt = c.get(f"/api/pnl?year={yr}&branch_id={B1}", headers=ha).json()
row = [x for x in pt["rows"] if x["period"] == f"{T.year:04d}-{T.month:02d}"]
ck("P&L jadvali: xarajat 10 000", row[0]["expenses"] if row else None,
   10_000)
TR = c.get("/api/reports/cashflow?months=1", headers=ha).json()["totals"]
ck("trend: xarajat +10 000", TR["expenses"] - TREND0["expenses"], 10_000)
ck("trend: tushum o'zgarmadi", TR["income"], TREND0["income"])

day = c.get(f"/api/reports/cash-day?day={T.isoformat()}&branch_id={B1}",
            headers=ha).json()
ck("kun kassasi: o'tkazma bitta", len(day["transfer_rows"]), 1)
eff = {x["method"]: x["amount"] for x in day["transfer_effect"]}
ck("kun kassasi: terminal −1 000 000", eff.get("terminal"), -1_000_000)
ck("kun kassasi: naqd +990 000", eff.get("cash"), 990_000)
ck("kun kassasi: tushum o'zgarmadi", day["total"], day0["total"])
ck("kun kassasi: komissiya", day["transfer_fee_total"], 10_000)

print("=== Komissiya xarajatini Xarajatlardan o'zgartirib bo'lmaydi ===")
ck("qo'lda bank_fee kiritib bo'lmaydi", c.post("/api/expenses", headers=ha,
   json={"date": T.isoformat(), "category": "bank_fee", "amount": 5000,
         "branch_id": B1}).status_code, 400)
ck("komissiyani tahrirlab bo'lmaydi", c.put(f"/api/expenses/{FEE_ID}",
   headers=ha, json={"amount": 1}).status_code, 400)
ck("komissiyani o'chirib bo'lmaydi",
   c.delete(f"/api/expenses/{FEE_ID}", headers=ha).status_code, 400)
ck("hali ham bitta komissiya", len(fee_rows()), 1)

print("=== 3. D: naqdni terminalga topshirish ===")
r = c.post("/api/bank-transfers", headers=hb, json={
    "kind": "deposit", "amount": 500_000, "date": T.isoformat()})
ck("administrator kiritadi", r.status_code, 200)
DP = r.json()
D1 = DP.get("id")
ck("komissiyasiz", DP.get("fee"), 0)
ck("sof = summa", DP.get("net"), 500_000)
ck("naqddan terminalga", (DP.get("from_method"), DP.get("to_method")),
   ("cash", "terminal"))
ck("yozuv matni", DP.get("title"), "Naqd → terminalga: 500 000")
ck("yangi xarajat yo'q", len(fee_rows()), 1)
L = led()
ck("kassa naqd −500 000", L["kassa"]["cash"], 690_000)
ck("kassa terminal +500 000", L["kassa"]["terminal"], 2_500_000)
ck("chiqim o'zgarmadi", L["chiqim"]["total"], 10_000)
ck("kirim o'zgarmadi", L["kirim"]["total"], 3_200_000)
ck("P&L o'zgarmadi", pnl()["expenses_total"], 10_000)

print("=== 4. Qoldiqdan oshiq — ogohlantirish va force ===")
r = c.post("/api/bank-transfers", headers=hb, json={
    "kind": "withdraw", "amount": 5_000_000, "date": T.isoformat()})
ck("terminaldan ortiq — 400", r.status_code, 400)
det = r.json().get("detail") or {}
ck("aniq xabar", "Terminalda" in str(det.get("message"))
   and "2 500 000" in str(det.get("message"))
   and "yechib bo'lmaydi" in str(det.get("message")), True)
ck("administratorga force yo'q", det.get("can_force"), False)
ck("administrator force — 403", c.post("/api/bank-transfers", headers=hb,
   json={"kind": "withdraw", "amount": 5_000_000, "force": True}
   ).status_code, 403)
r = c.post("/api/bank-transfers", headers=hb, json={
    "kind": "deposit", "amount": 1_000_000})
ck("naqddan ortiq — 400", r.status_code, 400)
ck("naqd xabari", "Naqd kassada" in str(
    (r.json().get("detail") or {}).get("message")), True)
r = c.post("/api/bank-transfers", headers=ha, json={
    "kind": "withdraw", "amount": 5_000_000, "branch_id": B1})
ck("asoschiga ham avval ogohlantirish", r.status_code, 400)
ck("asoschiga force mumkin", (r.json().get("detail") or {}).get("can_force"),
   True)
r = c.post("/api/bank-transfers", headers=ha, json={
    "kind": "withdraw", "amount": 5_000_000, "branch_id": B1,
    "force": True})
ck("asoschi force bilan saqlaydi", r.status_code, 200)
ck("forced belgisi", r.json().get("forced"), True)
FX = r.json().get("id")
ck("asoschi o'chiradi", c.delete(f"/api/bank-transfers/{FX}",
                                 headers=ha).status_code, 200)
ck("forced komissiyasi ham o'chdi", len(fee_rows()), 1)
ck("summa 0 — 400", c.post("/api/bank-transfers", headers=hb, json={
    "kind": "withdraw", "amount": 0}).status_code, 400)
ck("kelajak sana — 400", c.post("/api/bank-transfers", headers=hb, json={
    "kind": "deposit", "amount": 1000,
    "date": (T + timedelta(days=2)).isoformat()}).status_code, 400)
ck("asoschi filialsiz — 400", c.post("/api/bank-transfers", headers=ha,
   json={"kind": "deposit", "amount": 1000}).status_code, 400)

print("=== 6. Filial chegarasi ===")
ck("boshqa filial admini kirita olmaydi", c.post(
    "/api/bank-transfers", headers=hb2, json={
        "kind": "deposit", "amount": 1000, "branch_id": B1}).status_code, 403)
ck("boshqa filial admini ko'rmaydi", len(c.get(
    f"/api/bank-transfers?{YM}", headers=hb2).json()["rows"]), 0)
ck("o'z admini ko'radi", len(c.get(
    f"/api/bank-transfers?{YM}", headers=hb).json()["rows"]), 2)
ck("asoschi B2 tanlasa — 0", len(c.get(
    f"/api/bank-transfers?{YM}&branch_id={B2}", headers=ha).json()["rows"]), 0)
L2 = led(hb2, f"/api/reports/cashflow-ledger?{YM}")
ck("B2 daftarida o'tkazma yo'q",
   len([x for x in L2["rows"] if x["direction"] == "transfer"]), 0)
ck("B2 daftarida komissiya yo'q", L2["chiqim"]["total"], 0)
ck("B2 filial rahbari B1 ni tahrirlay olmaydi", c.put(
    f"/api/bank-transfers/{W1}", headers=hr2,
    json={"amount": 2_000_000}).status_code, 403)
ck("B2 filial rahbari B1 ni o'chira olmaydi", c.delete(
    f"/api/bank-transfers/{W1}", headers=hr2).status_code, 403)
ck("boshqa filial qoldig'i yopiq", c.get(
    f"/api/bank-transfers/balance?branch_id={B1}", headers=hb2).status_code,
   403)
bal = c.get(f"/api/bank-transfers/balance?branch_id={B1}", headers=hb).json()
ck("o'z qoldig'i: terminal", bal.get("terminal"), 2_500_000)
ck("o'z qoldig'i: naqd", bal.get("cash"), 690_000)

print("=== Cheklangan filial (Zafar) ===")
ck("Zafar admini — o'tgan sana 400", c.post(
    "/api/bank-transfers", headers=hz, json={
        "kind": "withdraw", "amount": 100_000,
        "date": (T - timedelta(days=1)).isoformat()}).status_code, 400)
r = c.post("/api/bank-transfers", headers=hz, json={
    "kind": "withdraw", "amount": 100_000})
ck("Zafar admini bugun kiritadi", r.status_code, 200)
r = c.post("/api/bank-transfers", headers=hz, json={
    "kind": "withdraw", "amount": 9_000_000})
ck("Zafar: ortiq — 400", r.status_code, 400)
ck("Zafar: qoldiq ko'rsatilmaydi",
   (r.json().get("detail") or {}).get("available"), None)
ck("Zafar: qoldiq so'rovi yopiq",
   c.get("/api/bank-transfers/balance", headers=hz).status_code, 403)
zd = c.get("/api/reports/cash-day", headers=hz).json()
ck("Zafar: kun kassasida ko'rinadi", len(zd["transfer_rows"]), 1)

print("=== 5. Tahrirlash / o'chirish ===")
ck("administrator tahrirlay olmaydi", c.put(
    f"/api/bank-transfers/{W1}", headers=hb,
    json={"amount": 2_000_000}).status_code, 403)
ck("administrator o'chira olmaydi",
   c.delete(f"/api/bank-transfers/{W1}", headers=hb).status_code, 403)
r = c.put(f"/api/bank-transfers/{W1}", headers=ha,
          json={"amount": 2_000_000, "note": "tuzatildi"})
ck("asoschi tahrirlaydi", r.status_code, 200)
ck("yangi komissiya 20 000", r.json().get("fee"), 20_000)
ck("yangi sof", r.json().get("net"), 1_980_000)
FR = [x for x in fee_rows() if x[3] == B1]
ck("komissiya o'sha yozuvda yangilandi", FR, [(FEE_ID, 20_000, "terminal",
                                               B1)])
L = led()
ck("kassa terminal −2 000 000 +500 000", L["kassa"]["terminal"], 1_500_000)
ck("kassa naqd", L["kassa"]["cash"], 200_000 + 1_980_000 - 500_000)
ck("P&L komissiya 20 000", pnl()["expenses_total"], 20_000)
r = c.put(f"/api/bank-transfers/{W1}", headers=ha,
          json={"amount": 5_000_000})
ck("tahrirda ham qoldiq tekshiruvi — 400", r.status_code, 400)
ck("tahrir xabarida qaytgan qoldiq",
   "3 500 000" in str((r.json().get("detail") or {}).get("message")), True)
r = c.put(f"/api/bank-transfers/{W1}", headers=hf,
          json={"amount": 1_000_000})
ck("moliya direktori qaytaradi", r.status_code, 200)
ck("komissiya 10 000 ga qaytdi",
   [x[1] for x in fee_rows() if x[0] == FEE_ID], [10_000])
ck("turini o'zgartirib bo'lmaydi", c.put(
    f"/api/bank-transfers/{W1}", headers=ha,
    json={"kind": "deposit"}).status_code, 400)
s = SessionLocal()
au = [(a.action, a.field) for a in s.query(models.AuditLog)
      .filter(models.AuditLog.entity == "bank_transfer",
              models.AuditLog.entity_id == W1).all()]
s.close()
ck("audit: yaratildi", ("create", "withdraw") in au, True)
ck("audit: summa o'zgardi", ("update", "amount") in au, True)
ck("audit: izoh o'zgardi", ("update", "note") in au, True)

print("=== 7. Foiz sozlamasi ===")
ck("administrator foizni o'zgartira olmaydi", c.put(
    "/api/bank-transfers/settings", headers=hb,
    json={"fee_percent": 2}).status_code, 403)
ck("filial rahbari ham o'zgartira olmaydi", c.put(
    "/api/bank-transfers/settings", headers=hr2,
    json={"fee_percent": 2}).status_code, 403)
ck("manfiy foiz — 400", c.put("/api/bank-transfers/settings", headers=hf,
   json={"fee_percent": -1}).status_code, 400)
ck("juda katta foiz — 400", c.put("/api/bank-transfers/settings", headers=hf,
   json={"fee_percent": 50}).status_code, 400)
r = c.put("/api/bank-transfers/settings", headers=hf,
          json={"fee_percent": 1.5})
ck("moliya direktori 1.5% qo'yadi", r.status_code, 200)
ck("sozlama 1.5", c.get("/api/bank-transfers/settings",
                        headers=hb).json()["fee_percent"], 1.5)
r = c.post("/api/bank-transfers", headers=hb, json={
    "kind": "withdraw", "amount": 1_000_000})
ck("yangi W 1.5% bilan", (r.json().get("fee_rate"), r.json().get("fee"),
                         r.json().get("net")), (1.5, 15_000, 985_000))
W2 = r.json().get("id")
s = SessionLocal()
w1 = s.query(models.BankCashTransfer).get(W1)
ck("eski o'tkazma foizi o'zgarmadi", (w1.fee_rate, w1.fee), (1.0, 10_000))
s.close()
r = c.put(f"/api/bank-transfers/{W1}", headers=ha,
          json={"amount": 1_200_000})
ck("eskisini tahrirlash — o'z 1% i bilan", r.json().get("fee"), 12_000)
c.put(f"/api/bank-transfers/{W1}", headers=ha, json={"amount": 1_000_000})
s = SessionLocal()
ck("audit: foiz o'zgarishi", s.query(models.AuditLog).filter(
    models.AuditLog.entity == "settings",
    models.AuditLog.field == "Bank komissiyasi foizi").count(), 1)
s.close()
P = pnl()
ck("P&L: ikki komissiya (10 000 + 15 000)", P["expenses_total"], 25_000)
ck("P&L: bitta qator", [x["category"] for x in P["expense_lines"]],
   ["bank_fee"])
c.put("/api/bank-transfers/settings", headers=ha, json={"fee_percent": 1})

print("=== O'chirish — komissiya ham o'chadi ===")
for tid in (W2, D1, W1):
    ck(f"asoschi o'chiradi #{tid}", c.delete(
        f"/api/bank-transfers/{tid}", headers=ha).status_code, 200)
ck("B1 da komissiya qolmadi",
   [x for x in fee_rows() if x[3] == B1], [])
s = SessionLocal()
ck("komissiya xarajati bazadan o'chdi",
   s.query(models.Expense).get(FEE_ID) is None, True)
ck("o'tkazma bazadan o'chdi",
   s.query(models.BankCashTransfer).get(W1) is None, True)
ck("audit: o'tkazma o'chirildi", s.query(models.AuditLog).filter(
    models.AuditLog.entity == "bank_transfer",
    models.AuditLog.action == "delete",
    models.AuditLog.entity_id == W1).count(), 1)
ck("audit: komissiya xarajati o'chirildi", s.query(models.AuditLog).filter(
    models.AuditLog.entity == "expense",
    models.AuditLog.action == "delete",
    models.AuditLog.entity_id == FEE_ID).count(), 1)
s.close()
ck("hammasi o'chgach — qoldiqlar boshlang'ich holatda", snap(), S0)
ck("o'chirilgan — 404", c.delete(f"/api/bank-transfers/{W1}",
                                 headers=ha).status_code, 404)

print("=== 8. Oy boshidagi qoldiq va oylar kesimi ===")
PREV_LAST = FIRST - timedelta(days=1)
PREV_FIRST = PREV_LAST.replace(day=1)
if PREV_FIRST >= date(2026, 9, 2) or PREV_FIRST.month == 9 and \
        PREV_FIRST.year == 2026:
    s = SessionLocal()
    s.add(models.OtherIncome(date=PREV_FIRST, category="other",
                             amount=2_000_000, method="terminal",
                             branch_id=B3, created_by="t"))
    s.commit(); s.close()
    mid = PREV_FIRST + timedelta(days=9)
    r = c.post("/api/bank-transfers", headers=ha, json={
        "kind": "withdraw", "amount": 1_000_000, "branch_id": B3,
        "date": mid.isoformat()})
    ck("o'tgan oyga W", r.status_code, 200)
    r = c.post("/api/bank-transfers", headers=ha, json={
        "kind": "deposit", "amount": 300_000, "branch_id": B3,
        "date": mid.isoformat()})
    ck("o'tgan oyga D", r.status_code, 200)
    L3 = led(ha, f"/api/reports/cashflow-ledger?{YM}&branch_id={B3}")
    ck("oy boshi: terminal 2M −1M +0.3M", L3["opening"]["terminal"],
       1_300_000)
    ck("oy boshi: naqd +990 000 −300 000", L3["opening"]["cash"], 690_000)
    ck("oy boshi jami −komissiya", L3["opening"]["total"], 1_990_000)
    rng = (f"/api/reports/cashflow-ledger?year={PREV_FIRST.year}"
           f"&month={PREV_FIRST.month}&to_year={T.year}&to_month={T.month}"
           f"&branch_id={B3}")
    LR = led(ha, rng)
    ck("oraliq: kassa terminal", LR["kassa"]["terminal"], 1_300_000)
    ck("oraliq: kassa naqd", LR["kassa"]["cash"], 690_000)
    ck("oraliq: o'tgan oy kassasi", LR["months"][0]["kassa"], 1_990_000)
    ck("oraliq: o'tkazma bloki", (LR["otkazma"]["cash"],
                                  LR["otkazma"]["terminal"]),
       (690_000, -690_000))
    # O'tgan oydagi kunga — o'sha kun qoldig'i bilan tekshiriladi
    r = c.post("/api/bank-transfers", headers=ha, json={
        "kind": "withdraw", "amount": 1_500_000, "branch_id": B3,
        "date": mid.isoformat()})
    ck("o'tgan kun qoldig'idan ortiq — 400", r.status_code, 400)
else:
    print("(o'tgan oy qoldiq yuritilmagan davrda — o'tkazildi)")

print("=== 10. Orqa sana: keyingi kunlar qoldig'i ham tekshiriladi ===")
# 2026-10-16 ko'rik: o'tgan sanani tanlab ogohlantirishni aylanib o'tib
# bo'lmasin — summa `on` kunidan BUGUNgacha har kun oxiridagi eng kam
# qoldiq bilan solishtiriladi (keyin kiritilgan chiqimlar ham).
A0 = T - timedelta(days=6)
if A0 >= date(2026, 9, 1):
    s = SessionLocal()
    b4 = models.Branch(name="Bekobod 4"); s.add(b4); s.commit(); B4 = b4.id
    Y1 = T - timedelta(days=1)
    s.add_all([
        models.OtherIncome(date=A0, category="other", amount=1_000_000,
                           method="terminal", branch_id=B4, created_by="t"),
        models.OtherIncome(date=A0, category="other", amount=500_000,
                           method="cash", branch_id=B4, created_by="t"),
        models.Expense(date=Y1, category="rent", amount=800_000,
                       method="terminal", branch_id=B4, created_by="t"),
        models.Expense(date=Y1, category="rent", amount=400_000,
                       method="cash", branch_id=B4, created_by="t"),
    ])
    s.commit(); s.close()
    mk("adm4", roles.ADMINISTRATOR, B4)
    h4 = H("adm4")
    D4 = (T - timedelta(days=4)).isoformat()
    LOW = Y1.strftime("%d.%m.%Y")
    # 4 kun oldin terminalda 1 000 000 bor, lekin kecha 800 000 ijara
    r = c.post("/api/bank-transfers", headers=h4, json={
        "kind": "withdraw", "amount": 1_000_000, "date": D4})
    ck("orqa sana: keyingi kun minusga tushadi — 400", r.status_code, 400)
    det = r.json().get("detail") or {}
    ck("xabarda eng kam qoldiq kuni va summasi",
       LOW in str(det.get("message")) and "200 000" in str(
           det.get("message")), True)
    ck("orqa sana: administratorga force yo'q", det.get("can_force"), False)
    r = c.post("/api/bank-transfers", headers=h4, json={
        "kind": "deposit", "amount": 300_000, "date": D4})
    ck("orqa sana: naqd ham — 400", r.status_code, 400)
    ck("naqd xabari — eng kam qoldiq",
       "Naqd kassada" in str((r.json().get("detail") or {}).get("message"))
       and "100 000" in str((r.json().get("detail") or {}).get("message")),
       True)
    r = c.post("/api/bank-transfers", headers=h4, json={
        "kind": "deposit", "amount": 50_000, "date": D4})
    ck("orqa sana: yetarli bo'lsa o'tadi", r.status_code, 200)
    ck("orqa sana: forced emas", r.json().get("forced"), False)
    c.delete(f"/api/bank-transfers/{r.json().get('id')}", headers=ha)
    r = c.post("/api/bank-transfers", headers=h4, json={
        "kind": "withdraw", "amount": 150_000, "date": D4})
    ck("orqa sana: 150 000 o'tadi", r.status_code, 200)
    WB = r.json().get("id")
    # Tahrir: eski summa o'z sanasidan boshlab qaytariladi
    r = c.put(f"/api/bank-transfers/{WB}", headers=ha,
              json={"amount": 200_000})
    ck("tahrir: kechagi eng kam qoldiqqacha — 200", r.status_code, 200)
    r = c.put(f"/api/bank-transfers/{WB}", headers=ha,
              json={"amount": 250_000})
    ck("tahrir: keyingi kun minus — 400", r.status_code, 400)
    msg = str((r.json().get("detail") or {}).get("message"))
    ck("tahrir xabari", LOW in msg and "200 000" in msg, True)
    r = c.put(f"/api/bank-transfers/{WB}", headers=ha,
              json={"date": (T - timedelta(days=2)).isoformat()})
    ck("tahrir: sanani keyinga surish — 200", r.status_code, 200)
    # Bugun terminal 0 — o'tgan sanaga yechish ham bo'lmaydi
    bal4 = c.get(f"/api/bank-transfers/balance?branch_id={B4}",
                 headers=h4).json()
    ck("bugun terminal 0", bal4.get("terminal"), 0)
    r = c.post("/api/bank-transfers", headers=h4, json={
        "kind": "withdraw", "amount": 10_000,
        "date": (T - timedelta(days=3)).isoformat()})
    ck("bugun 0 — o'tgan sanaga ham 400", r.status_code, 400)
    r = c.post("/api/bank-transfers", headers=ha, json={
        "kind": "withdraw", "amount": 10_000, "branch_id": B4,
        "date": (T - timedelta(days=3)).isoformat(), "force": True})
    ck("asoschi force bilan — forced", (r.status_code,
                                         r.json().get("forced")), (200, True))
    c.delete(f"/api/bank-transfers/{r.json().get('id')}", headers=ha)

    # Kunlik harakat (_cf_day_moves) — oy boshidagi qoldiq (_cf_opening)
    # bilan bir xil manbalar: har kun oxiridagi qoldiq mos tushadi.
    # Tunda (Toshkent 01:00) qilingan to'lov o'z kuniga tushadi.
    import dashboard as DSH
    from bank_transfer import _BranchViewer
    from datetime import datetime as _dtm
    s = SessionLocal()
    st4 = models.Student(full_name="Tun To'lovchi", branch_id=B4)
    te4 = models.Teacher(full_name="Ustoz To'rt", branch_id=B4)
    s.add_all([st4, te4]); s.commit()
    off = timedelta(hours=roles.TIMEZONE_OFFSET_HOURS)
    s.add_all([
        models.Payment(student_id=st4.id, amount=70_000, kind="payment",
                       method="cash", created_at=_dtm.combine(
                           T - timedelta(days=3), _dtm.min.time())
                       + timedelta(hours=1) - off),
        models.TeacherPayment(teacher_id=te4.id, amount=30_000,
                              paid_on=T - timedelta(days=2),
                              method="terminal"),
    ])
    u4 = s.query(models.User).filter(models.User.username == "adm4").first()
    SSP = getattr(models, "StaffSalaryPayment", None)
    if SSP is not None:
        s.add(SSP(user_id=u4.id, amount=20_000, paid_on=T - timedelta(days=5),
                  method="cash"))
    s.commit()
    for bid in (B1, B3, B4):
        v = _BranchViewer(bid)
        mv = DSH._cf_day_moves(s, v, bid, DSH.CF_OPENING_FROM, T)
        run = {m: 0.0 for m in roles.PAYMENT_METHODS}
        bad = []
        dd = DSH.CF_OPENING_FROM
        while dd <= T:
            for k, val in mv.get(dd, {}).items():
                run[k] += val
            want = DSH._cf_opening(s, v, bid, dd + timedelta(days=1))
            if any(abs(run[k] - want[k]) > 0.01 for k in run):
                bad.append(dd.isoformat())
            dd += timedelta(days=1)
        ck(f"kunlik harakat = qoldiq hisobi (filial {bid})", bad, [])
    ck("tungi to'lov o'z kunida",
       DSH._cf_day_moves(s, _BranchViewer(B4), B4, T - timedelta(days=3),
                         T - timedelta(days=3))
       .get(T - timedelta(days=3), {}).get("cash"), 70_000)
    s.close()
    c.delete(f"/api/bank-transfers/{WB}", headers=ha)
else:
    print("(qoldiq yuritilmagan davr — o'tkazildi)")

print("=== 11. Hamkor (Stech) va test filiali chegarasi ===")
# 2026-10-16 ko'rik: hamkor markaz qoldig'i moliya direktori/buxgalterga
# yopiq (scope_to_branch bilan bir xil); asoschi esa hamkor yoki test
# filialini TANLASA o'z kiritgan o'tkazmasini ro'yxat, daftar va kun
# kassasida ko'radi (tahrirlab/o'chira oladi).
s = SessionLocal()
stc = models.Branch(name="Stech", is_partner=1)
tst = models.Branch(name="Test filial", is_test=1)
s.add_all([stc, tst]); s.commit()
ST, TS = stc.id, tst.id
s.add_all([
    models.OtherIncome(date=T, category="other", amount=5_000_000,
                       method="terminal", branch_id=ST, created_by="t"),
    models.OtherIncome(date=T, category="other", amount=700_000,
                       method="cash", branch_id=ST, created_by="t"),
    models.OtherIncome(date=T, category="other", amount=400_000,
                       method="cash", branch_id=TS, created_by="t"),
])
s.commit(); s.close()
common.reset_partner_cache()
mk("sadm", roles.ADMINISTRATOR, ST)
hs = H("sadm")
ck("moliya direktori: hamkor qoldig'i yopiq", c.get(
    f"/api/bank-transfers/balance?branch_id={ST}", headers=hf).status_code,
   403)
r = c.post("/api/bank-transfers", headers=hf, json={
    "kind": "withdraw", "amount": 99_000_000, "branch_id": ST})
ck("moliya direktori: katta summa — 403 (qoldiq oshkor emas)",
   r.status_code, 403)
ck("xabarda qoldiq yo'q", "5 000 000" in r.text, False)
ck("moliya direktori: hamkorga kirita olmaydi", c.post(
    "/api/bank-transfers", headers=hf, json={
        "kind": "withdraw", "amount": 100_000, "branch_id": ST}
).status_code, 403)
bal_s = c.get(f"/api/bank-transfers/balance?branch_id={ST}",
              headers=ha).json()
ck("asoschi hamkor qoldig'ini ko'radi",
   (bal_s.get("terminal"), bal_s.get("cash")), (5_000_000, 700_000))
r = c.post("/api/bank-transfers", headers=ha, json={
    "kind": "deposit", "amount": 50_000, "branch_id": ST})
ck("asoschi hamkorga kiritadi", r.status_code, 200)
SD = r.json().get("id")
ck("asoschi Stech tanlasa ro'yxatda", [x["id"] for x in c.get(
    f"/api/bank-transfers?{YM}&branch_id={ST}", headers=ha).json()["rows"]],
   [SD])
LS = led(ha, f"/api/reports/cashflow-ledger?{YM}&branch_id={ST}")
ck("asoschi Stech daftarida o'tkazma",
   [x["transfer_id"] for x in LS["rows"] if x["direction"] == "transfer"],
   [SD])
ck("asoschi Stech kun kassasida", [x["id"] for x in c.get(
    f"/api/reports/cash-day?branch_id={ST}", headers=ha).json()
    ["transfer_rows"]], [SD])
ck("barcha filiallar yig'indisida Stech yo'q", SD in [x["id"] for x in c.get(
    f"/api/bank-transfers?{YM}", headers=ha).json()["rows"]], False)
ck("Stech administratori o'zinikini ko'radi", [x["id"] for x in c.get(
    f"/api/bank-transfers?{YM}", headers=hs).json()["rows"]], [SD])
ck("moliya direktori Stech ro'yxatini ko'rmaydi", c.get(
    f"/api/bank-transfers?{YM}&branch_id={ST}", headers=hf).json()["rows"],
   [])
ck("moliya direktori tahrirlay olmaydi", c.put(
    f"/api/bank-transfers/{SD}", headers=hf,
    json={"amount": 60_000}).status_code, 403)
ck("moliya direktori o'chira olmaydi", c.delete(
    f"/api/bank-transfers/{SD}", headers=hf).status_code, 403)
ck("asoschi o'chiradi", c.delete(f"/api/bank-transfers/{SD}",
                                 headers=ha).status_code, 200)
r = c.post("/api/bank-transfers", headers=ha, json={
    "kind": "deposit", "amount": 40_000, "branch_id": TS})
ck("asoschi test filialiga kiritadi", r.status_code, 200)
TD = r.json().get("id")
ck("asoschi test filialini tanlasa ko'radi", [x["id"] for x in c.get(
    f"/api/bank-transfers?{YM}&branch_id={TS}", headers=ha).json()["rows"]],
   [TD])
ck("asoschi test o'tkazmasini o'chiradi", c.delete(
    f"/api/bank-transfers/{TD}", headers=ha).status_code, 200)

print("\n" + ("HAMMASI OK" if not fails else f"{len(fails)} XATO: {fails}"))
sys.exit(1 if fails else 0)
