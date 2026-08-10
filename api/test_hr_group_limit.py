"""HR MENEJER GURUH CHEGARASI (2026-08-10).

Jahongir: "HR manager ham guruhlarni to'siqlarsiz tahrirlayversin,
chunki ba'zi ustozlarda guruhi limitdan oshsa ham bemalol
saqlayversin."

Ilgari: ustozning guruh soni chegaradan oshsa, ASOSCHIDAN boshqa
hech kim (HR ham) guruhni saqlay olmasdi — 400 "Mumkin emas".
Endi: asoschi va HR menejer 409 OGOHLANTIRISH oladi va
"baribir saqlash" (force=true) bilan saqlaydi. Qolganlarda hamon
400 — qat'iy taqiq.

MUHIM: bu FAQAT guruh SONI chegarasiga tegishli. Vaqt to'qnashuvi
(bir ustoz bir vaqtda ikki guruhda) hamma uchun taqiqligicha
qoladi — u jismonan imkonsiz."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/vhgl/db.sqlite"
os.makedirs("/tmp/vhgl", exist_ok=True)
if os.path.exists("/tmp/vhgl/db.sqlite"):
    os.remove("/tmp/vhgl/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}" + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()


def mk(u, r):
    x = models.User(username=u, full_name=f"X {u}",
                    password_hash=hash_password("Parol123!"),
                    role=r, branch_id=b.id, is_active=1)
    db.add(x); db.commit(); return x


mk("hr", roles.HR_MANAGER)
mk("dir", roles.FOUNDER)
mk("ah", roles.ACADEMIC_HEAD)

ut = mk("ust", roles.TEACHER)
t = models.Teacher(full_name="Ustoz Anvar", branch_id=b.id, user_id=ut.id,
                   is_active=1, max_groups=2)
db.add(t); db.commit()

# Chegara 2 ta — ikkita guruh ochib chegarani to'ldiramiz
# Ikkala guruh HAR XIL KUNDA — vaqt to'qnashuvi bu sinovga
# aralashmasin (biz faqat GURUH SONI chegarasini sinaymiz).
for nm, dys in (("G1", "mon,wed,fri"), ("G2", "tue,thu")):
    db.add(models.Group(name=nm, subject="english", level="step1",
                        branch_id=b.id, teacher_id=t.id,
                        lesson_time="08:00", monthly_fee=500000,
                        lesson_days=dys, capacity=15))
db.commit()
ck("ustozda 2 ta guruh bor (chegara to'ldi)",
   db.query(models.Group).filter(models.Group.teacher_id == t.id).count(), 2)


def H(u):
    return {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':u,'password':'Parol123!'}).json()['access_token']}"}


def new_group(name, time_, days="tue,thu,sat"):
    return {"name": name, "subject": "english", "level": "step1",
            "branch_id": b.id, "teacher_id": t.id, "lesson_time": time_,
            "lesson_days": days, "monthly_fee": 500000, "capacity": 15,
            "start_date": date.today().isoformat()}


print("\n=== 3-CHI GURUH: CHEGARADAN OSHADI ===")
r = c.post("/api/groups", headers=H("hr"), json=new_group("G3", "10:00"))
ck("HR: ogohlantirish (409), qat'iy taqiq EMAS", r.status_code, 409)
d = r.json()["detail"]
ck("'baribir saqlash' mumkin", d.get("can_force"), True)
ck("sabab chegara haqida", "chegara" in d["message"], True)

r = c.post("/api/groups?force=true", headers=H("hr"),
           json=new_group("G3", "10:00", days="sat"))
ck("HR force bilan SAQLAYDI", r.status_code, 200)
ck("guruh haqiqatan yaratildi",
   db.query(models.Group).filter(models.Group.name == "G3").count(), 1)

print("\n=== ASOSCHI ham avvalgidek ishlaydi ===")
r = c.post("/api/groups?force=true", headers=H("dir"),
           json=new_group("G4", "16:00", days="sun"))
ck("asoschi saqlaydi", r.status_code, 200)

print("\n=== BOSHQALARDA HAMON QAT'IY TAQIQ ===")
r = c.post("/api/groups", headers=H("ah"),
           json=new_group("G5", "18:00", days="sun"))
ck("o'quv bo'limi rahbari: 400 taqiq", r.status_code, 400)
ck("xabar 'Mumkin emas' bilan boshlanadi",
   r.json()["detail"]["message"].startswith("Mumkin emas"), True)
r = c.post("/api/groups?force=true", headers=H("ah"),
           json=new_group("G5", "18:00", days="sun"))
ck("force bilan ham o'tolmaydi", r.status_code, 400)

print("\n=== TAHRIRLASH (PUT) ham HR uchun ochiq ===")
g1 = db.query(models.Group).filter(models.Group.name == "G1").first()
r = c.put(f"/api/groups/{g1.id}?force=true", headers=H("hr"),
          json={"teacher_id": t.id, "name": "G1 yangi"})
ck("HR guruhni tahrirlaydi", r.status_code, 200)

print("\n=== VAQT TO'QNASHUVI HAMMAGA TAQIQ (o'zgarmadi) ===")
# G3 soat 10:00, 246 kunlari — xuddi shu vaqtga yana bitta
r = c.post("/api/groups?force=true", headers=H("hr"),
           json=new_group("G6", "10:00", days="sat"))
ck("HR ham bir vaqtda ikki guruh ocha olmaydi", r.status_code, 400)
det = r.json()["detail"]
keys = [p["key"] for p in det["problems"]] if isinstance(det, dict) else []
ck("sabab jadval to'qnashuvi (chegara emas)",
   "teacher_clash" in keys or "room_clash" in keys, True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
