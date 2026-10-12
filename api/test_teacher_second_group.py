"""USTOZ QO'SHIMCHA GURUHDAGI O'QUVCHISINI KO'RADI (2026-10-12).

Jahongir: "ustoz nega mirzoulug'bek degan o'quvchim chap tomonda
chiqmayapti". Bola asosiy guruhi boshqa ustozda (Telc), Result
Makers'ga qo'shimcha bog'lanish bilan qatnaydi. Davomat jadvalida bor,
lekin ustozning o'quvchilar ro'yxatida, qidiruvda va profilida yo'q
edi — ustoz filtri faqat Student.group_id ga qarardi.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "teacher_second_group_test")
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


TODAY = date.today()
db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
BID = b.id
db.add(models.User(username="asos", full_name="Asoschi", role=roles.FOUNDER,
                   password_hash=hash_password("x"), is_active=1))
db.commit()

T = {}
for name in ["Shirinabonu Ustoz", "Asadbek Ustoz", "Begona Ustoz"]:
    t = models.Teacher(full_name=name, branch_id=BID, is_active=1,
                       grade="senior", hired_date=TODAY - timedelta(days=400))
    db.add(t); db.commit()
    u = models.User(username=roles.login_from_name(name),
                    password_hash=hash_password("x"), full_name=name,
                    role=roles.TEACHER, branch_id=BID, is_active=1)
    db.add(u); db.commit()
    t.user_id = u.id; db.commit()
    T[name] = t.id
    T[name + "_login"] = u.username

G = {}
for gname, tname in [("Result Makers", "Shirinabonu Ustoz"),
                     ("Telc", "Asadbek Ustoz"),
                     ("Begona", "Begona Ustoz")]:
    g = models.Group(name=gname, teacher_id=T[tname], branch_id=BID,
                     subject="english", lesson_days="tue,thu,sat",
                     lesson_time="16:00")
    db.add(g); db.commit()
    G[gname] = g.id

# Oddiy bola — asosiy guruhi Result Makers
own = models.Student(full_name="Atayev Ibrohim", branch_id=BID,
                     group_id=G["Result Makers"], status="active",
                     enrolled_date=TODAY - timedelta(days=60))
# Ikki guruhli bola — asosiysi Telc, qo'shimchasi Result Makers
two = models.Student(full_name="Boymuxamatov Mirzoulugbek", branch_id=BID,
                     group_id=G["Telc"], status="active",
                     enrolled_date=TODAY - timedelta(days=60))
# Begona bola — ustozga ko'rinmasligi kerak
alien = models.Student(full_name="Begona Bola", branch_id=BID,
                       group_id=G["Begona"], status="active",
                       enrolled_date=TODAY - timedelta(days=60))
db.add_all([own, two, alien]); db.commit()
db.add_all([
    models.StudentGroupLink(student_id=own.id, group_id=G["Result Makers"],
                            is_primary=1, active=1),
    models.StudentGroupLink(student_id=two.id, group_id=G["Telc"],
                            is_primary=1, active=1),
    models.StudentGroupLink(student_id=two.id, group_id=G["Result Makers"],
                            is_primary=0, active=1),
    models.StudentGroupLink(student_id=alien.id, group_id=G["Begona"],
                            is_primary=1, active=1),
])
db.commit()
OWN, TWO, ALIEN = own.id, two.id, alien.id
db.close()


def H(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


hs = H(T["Shirinabonu Ustoz_login"])
ha = H(T["Asadbek Ustoz_login"])
hf = H("asos")

print("=== Guruh ro'yxati (chap panel) ===")
r = c.get(f"/api/students?group_id={G['Result Makers']}", headers=hs)
ck("ustoz: status", r.status_code, 200)
names = sorted(s["full_name"] for s in r.json())
ck("ustoz: Result Makers'da ikkala bola",
   names, ["Atayev Ibrohim", "Boymuxamatov Mirzoulugbek"])
r = c.get(f"/api/students?group_id={G['Result Makers']}", headers=hf)
ck("asoschi: o'sha 2 bola",
   sorted(s["full_name"] for s in r.json()),
   ["Atayev Ibrohim", "Boymuxamatov Mirzoulugbek"])

print("=== Ustozning barcha o'quvchilari ===")
ids = {s["id"] for s in c.get("/api/students", headers=hs).json()}
ck("ikki guruhli bola ko'rinadi", TWO in ids, True)
ck("begona bola ko'rinmaydi", ALIEN in ids, False)
ids_a = {s["id"] for s in c.get("/api/students", headers=ha).json()}
ck("asosiy guruh ustozi ham ko'radi", TWO in ids_a, True)
ck("asosiy guruh ustoziga Atayev ko'rinmaydi", OWN in ids_a, False)

print("=== Profil ===")
ck("qo'shimcha guruh ustozi profilni ochadi",
   c.get(f"/api/students/{TWO}", headers=hs).status_code, 200)
ck("asosiy guruh ustozi profilni ochadi",
   c.get(f"/api/students/{TWO}", headers=ha).status_code, 200)
ck("begona bola profili yopiq",
   c.get(f"/api/students/{ALIEN}", headers=hs).status_code, 403)
ck("ustozga balans ko'rinmaydi",
   c.get(f"/api/students/{TWO}", headers=hs).json().get("balance"), 0.0)

print("=== Qidiruv ===")
r = c.get("/api/search/students?q=Boymux", headers=hs)
ck("qidiruv status", r.status_code, 200)
ck("qidiruvda topiladi", "Boymuxamatov" in r.text, True)
r = c.get("/api/search/students?q=Begona", headers=hs)
ck("begona bola qidiruvda chiqmaydi", "Begona Bola" in r.text, False)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
