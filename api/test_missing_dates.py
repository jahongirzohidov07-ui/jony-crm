"""TADBIRLAR: SANASI KIRITILMAGANLAR (2026-10-06).

Jahongir: "tadbirlarga bitta click bilan tug'ilgan kuni yoki ishga
kirgan sanasi kiritilmaganlar degan knopka qo'shib ber, xodim ismiga
bosib akkauntiga tug'ilgan kun biriktirib qo'ya olay".

Tekshiriladi:
  1. Ro'yxat: sanasi to'liq xodim yo'q; o'quvchi/ota-ona hisobi xodim
     emas; arxivdagi o'quvchi yo'q.
  2. Event menejer sana kiritadi — kartaga yoziladi, ro'yxatdan chiqadi,
     tug'ilgan kunlar ro'yxatiga tushadi; audit.
  3. Noto'g'ri sanalar — 400; asoschi kartasi — 403.
  4. SMM ko'radi, lekin o'zgartira olmaydi (403).
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "missing_dates_test")
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
b = models.Branch(name="Zafar"); db.add(b); db.commit()
today = date.today()


def user(login, name, role, **kw):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=name, role=role, branch_id=b.id,
                    is_active=1, **kw)
    db.add(u); db.commit()
    return u


founder = user("asos", "Asoschi", roles.FOUNDER,
               birth_date=date(1990, 1, 1), hired_date=date(2020, 1, 1))
user("ev", "Event Menejer", roles.EVENT_MANAGER,
     birth_date=date(1995, 5, 5), hired_date=date(2025, 1, 1))
user("smm", "SMM", roles.SMM_MANAGER,
     birth_date=date(1996, 6, 6), hired_date=date(2025, 1, 1))
nob = user("x1", "Sanasiz Xodim", roles.TEACHER)
noh = user("x2", "Yarim Xodim", roles.ADMINISTRATOR, birth_date=date(1998, 3, 3))
user("stu", "O'quvchi Hisob", roles.STUDENT)
st = models.Student(full_name="Sanasiz Bola", branch_id=b.id, status="active")
gone = models.Student(full_name="Arxiv Bola", branch_id=b.id, status="archived")
db.add_all([st, gone]); db.commit()
NOB, NOH, ST, FOUNDER_ID = nob.id, noh.id, st.id, founder.id


def H(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


HE, HS = H("ev"), H("smm")

print("=== 1. RO'YXAT ===")
d = c.get("/api/events/missing-dates", headers=HE).json()
ck("xodimlar", sorted(r["full_name"] for r in d["staff"]),
   ["Sanasiz Xodim", "Yarim Xodim"])
ck("o'quvchilar", [r["full_name"] for r in d["students"]], ["Sanasiz Bola"])
ck("sanoq", (d["no_birth_staff"], d["no_hired_staff"]), (1, 2))
ck("event menejer tahrirlaydi", d["can_edit"], True)

print("\n=== 2. KIRITISH ===")
bd = today.replace(year=today.year - 30)
r = c.put(f"/api/events/dates/staff/{NOB}", headers=HE,
          json={"birth_date": bd.isoformat(), "hired_date": "2024-09-01"})
ck("xodim saqlandi", (r.status_code, r.json().get("changed")), (200, 2))
r = c.put(f"/api/events/dates/student/{ST}", headers=HE,
          json={"birth_date": (today - timedelta(days=12 * 365)).isoformat()})
ck("o'quvchi saqlandi", r.status_code, 200)
db.expire_all()
u = db.query(models.User).get(NOB)
ck("kartaga yozildi", (u.birth_date, u.hired_date), (bd, date(2024, 9, 1)))
d = c.get("/api/events/missing-dates", headers=HE).json()
ck("ro'yxatdan chiqdi", [r["full_name"] for r in d["staff"]], ["Yarim Xodim"])
ck("o'quvchi ham chiqdi", d["students"], [])
bdays = c.get("/api/events/birthdays?days=1", headers=HE).json()["rows"]
ck("bugungi tug'ilgan kunda bor",
   any(x["full_name"] == "Sanasiz Xodim" and x["today"] for x in bdays), True)
n = (db.query(models.AuditLog)
     .filter(models.AuditLog.entity_id == NOB,
             models.AuditLog.note == "Tadbirlar: sanasi kiritilmaganlar")
     .count())
ck("audit 2 ta", n, 2)

print("\n=== 3. TEKSHIRUVLAR ===")
for name, body in [
    ("kelajak tug'ilgan sana", {"birth_date": (today + timedelta(days=3)).isoformat()}),
    ("200 yil oldin", {"birth_date": "1820-01-01"}),
    ("kelajak ishga kirish", {"hired_date": (today + timedelta(days=5)).isoformat()}),
    ("noto'g'ri format", {"birth_date": "31-12-1999"}),
]:
    ck(name + " — 400", c.put(f"/api/events/dates/staff/{NOH}", headers=HE,
                              json=body).status_code, 400)
ck("asoschi kartasi — 403",
   c.put(f"/api/events/dates/staff/{FOUNDER_ID}", headers=HE,
         json={"birth_date": "1990-02-02"}).status_code, 403)

print("\n=== 4. SMM ===")
d = c.get("/api/events/missing-dates", headers=HS).json()
ck("SMM ko'radi, tahrirlay olmaydi", d["can_edit"], False)
ck("SMM o'zgartira olmaydi",
   c.put(f"/api/events/dates/staff/{NOH}", headers=HS,
         json={"hired_date": "2024-01-01"}).status_code, 403)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
