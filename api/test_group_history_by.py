"""GURUH TARIXIDA KIM QILGANI (2026-09-17).

Jahongir: "bu guruhlarda shularni kim qoygani korinmayapti" — tarixdagi
har voqeada (qo'shildi, muzlatildi, imtihon, daraja o'zgardi, dars
ko'chdi) kim qilgani ko'rinadi.
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "group_history_by_test")
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
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
u = models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi Aka", role=roles.FOUNDER)
db.add(u); db.commit(); UID = u.id
g = models.Group(name="Cambridge", branch_id=BID, lesson_price=50000,
                 standard_lessons_per_month=12)
db.add(g); db.commit(); GID = g.id
s = models.Student(full_name="Malikov Lazizbek", branch_id=BID,
                   status="active", group_id=GID,
                   enrolled_date=date(2026, 9, 1))
db.add(s); db.commit(); SID = s.id
db.add(models.AuditLog(user_id=UID, username="asos",
                       user_name="Admin Iroda", entity="student",
                       entity_id=SID, action="group_move", field="group",
                       new_value="Cambridge"))
db.add(models.AuditLog(user_id=UID, username="asos",
                       user_name="Admin Iroda", entity="group",
                       entity_id=GID, action="update", field="level",
                       new_value="step2"))
db.add(models.Exam(group_id=GID, kind="unit", title="Unit 1",
                   date=date(2026, 9, 7), status="done",
                   created_by="Shirinabonu", approved_by="Asoschi Aka"))
db.add(models.LessonReschedule(group_id=GID, from_date=date(2026, 9, 3),
                               to_date=date(2026, 9, 4), status="approved",
                               requested_by=UID))
db.commit(); db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}

r = c.get(f"/api/groups/{GID}/history", headers=H)
ck("200", r.status_code, 200)
ev = r.json()["events"]
by = {e["kind"]: e.get("by") for e in ev}
txt = {e["kind"]: e["text"] for e in ev}
ck("qo'shganni ko'rsatadi", by.get("join"), "Admin Iroda")
ck("daraja o'zgartirgan", by.get("audit"), "Admin Iroda")
ck("daraja matni tushunarli", txt.get("audit"),
   "Daraja o'zgartirildi: — → step2")
ck("imtihon: kiritgan va tasdiqlagan", by.get("exam"),
   "Shirinabonu, tasdiqladi: Asoschi Aka")
ck("dars ko'chirgan", by.get("move"), "Asoschi Aka")
ck("ko'chirish holati o'zbekcha", "tasdiqlangan" in txt.get("move", ""), True)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
