"""ZAFAR FILIALI ADMINISTRATORIGA FAQAT BUGUNGI TUSHUM (2026-10-06).

Jahongir: "shu cashflow adminlarga ko'rinmasin, Zafar filialidagilarga.
Ularga faqat bugun urilgan pullar va umumiy hisobi ko'rinsin. Qolgan
filial turaversin".
"""
import os
import sys
import tempfile
from datetime import timedelta

_DIR = os.path.join(tempfile.gettempdir(), "cashflow_limited_test")
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
db.add_all([
    models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="zadm", full_name="Mashxura",
                role=roles.ADMINISTRATOR, branch_id=z.id,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="zsm", full_name="Zafar SM",
                role=roles.SALES_MANAGER, branch_id=z.id,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="badm", full_name="Baxriniso",
                role=roles.ADMINISTRATOR, branch_id=bk.id,
                password_hash=hash_password("x"), is_active=1),
])
db.commit(); db.close()


def H(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


T = roles.local_today()
Y = T - timedelta(days=1)
LED = f"/api/reports/cashflow-ledger?year={T.year}&month={T.month}"

print("=== Zafar administratori ===")
for u in ("zadm", "zsm"):
    h = H(u)
    ck(f"{u}: kassa daftari yopiq", c.get(LED, headers=h).status_code, 403)
    ck(f"{u}: oylik trend yopiq",
       c.get("/api/reports/cashflow?months=6", headers=h).status_code, 403)
    r = c.get(f"/api/reports/cash-day?day={Y.isoformat()}", headers=h)
    ck(f"{u}: bugungi tushum ochiq", r.status_code, 200)
    ck(f"{u}: kechani so'rasa ham bugun", r.json()["date"], T.isoformat())
    ck(f"{u}: today_only belgisi", r.json()["today_only"], True)

print("=== Boshqa filial administratori — o'zgarmadi ===")
h = H("badm")
ck("kassa daftari ochiq", c.get(LED, headers=h).status_code, 200)
r = c.get(f"/api/reports/cash-day?day={Y.isoformat()}", headers=h)
ck("kechagi kunni ko'ra oladi", r.json()["date"], Y.isoformat())
ck("today_only yo'q", r.json()["today_only"], False)

print("=== Asoschi ===")
h = H("asos")
ck("kassa daftari ochiq", c.get(LED, headers=h).status_code, 200)
ck("trend ochiq",
   c.get("/api/reports/cashflow?months=6", headers=h).status_code, 200)

print("\n" + ("HAMMASI OK" if not fails else f"{len(fails)} XATO: {fails}"))
sys.exit(1 if fails else 0)
