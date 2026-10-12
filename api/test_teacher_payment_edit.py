"""USTOZ OYLIGI YOZUVINI TAHRIRLASH (2026-10-12).

Jahongir: "shu rayxonani to'g'rilayman desam xato ketib qolibdi"
(Kassa daftaridagi qalamcha "Xatolik: 422" berdi). PUT
/api/teacher-payments/{id}: summa/usul/izoh o'zgaradi, yozuv
o'chmaydi, eski qiymat auditda; huquqi yo'q xodim tahrirlay olmaydi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "teacher_payment_edit_test")
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
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit()
t = models.Teacher(full_name="Rayxona Abdujalilova", branch_id=b.id,
                   is_active=1)
db.add(t); db.commit()
p = models.TeacherPayment(teacher_id=t.id, amount=8_410_000, kind="salary",
                          period="2026-09", paid_on=date(2026, 10, 12),
                          method="card", branch_id=b.id)
db.add(p)
db.add_all([
    models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Admin", role=roles.ADMINISTRATOR,
                branch_id=b.id, password_hash=hash_password("x"),
                is_active=1),
])
db.commit()
PID, TID = p.id, t.id
db.close()


def H(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


ha, hd = H("asos"), H("adm")
ck("administrator tahrirlay olmaydi",
   c.put(f"/api/teacher-payments/{PID}", headers=hd,
         json={"amount": 841000}).status_code, 403)
r = c.put(f"/api/teacher-payments/{PID}", headers=ha,
          json={"amount": 841000, "method": "card", "note": None})
ck("asoschi: 200", r.status_code, 200)
ck("summa yangilandi", r.json().get("amount"), 841000.0)
ck("0 summa — 400", c.put(f"/api/teacher-payments/{PID}", headers=ha,
                          json={"amount": 0}).status_code, 400)
ck("yo'q yozuv — 404", c.put("/api/teacher-payments/999999", headers=ha,
                             json={"amount": 1}).status_code, 404)

db = SessionLocal()
row = db.query(models.TeacherPayment).get(PID)
ck("yozuv o'chmadi, oyi o'zgarmadi", (row is not None, row.period),
   (True, "2026-09"))
logs = db.query(models.AuditLog).filter(
    models.AuditLog.entity == "teacher",
    models.AuditLog.entity_id == TID).all()
ck("auditda eski summa", any("8 410 000" in (l.old_value or "")
                             for l in logs), True)
db.close()

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
