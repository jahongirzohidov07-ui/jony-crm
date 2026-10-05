"""GURUHGA QAYTARISH + GURUHSIZ FAOLLASHTIRISH TAQIQI (2026-10-05).

Jahongir: "Gayratova Nargiza, Rahmonova Diyora, Maqsudova Durdona shu
o'quvchi o'zidan o'zi arxivga o'tib qolibdi, nega va guruh arxivida
turgan o'quvchini ism familya yonida guruhga qaytarish tugmasi tursin
guruhga qaytarganda avtomat oylik tanlagan kundan boshlab oy oxirigacha
hisoblanishi kerak".

Sabab: sinovda 2 marta kelmagan o'quvchi guruhdan avtomat chiqarildi;
admin uni arxivdan GURUHSIZ faol qildi; "guruhsiz faol bo'lmaydi" va
"guruhsiz + qarzsiz -> arxiv" qoidalari uni bir daqiqada arxivga
qaytardi.

Tekshiriladi:
  1. Guruhsiz faollashtirish — 400 va tushunarli xabar, holat o'zgarmaydi.
  2. "Guruhdan o'chirilganlar" ro'yxatida turadi.
  3. Qaytarish: faol, shu guruhda, bog'lanish ochiq, tanlangan kundan
     oy oxirigacha darslar uchun hisob yozildi.
  4. Avtomat tozalashlar endi uni arxivga qaytarmaydi.
  5. Takror qaytarish — 400; ustozga — 403; administratorga ruxsat.
  6. Faollashtirishda group_id berilsa — guruhga qo'shib faol qiladi.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "return_group_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
import common                                      # noqa: E402
import students as stu                             # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


TODAY = roles.local_today()
NOW = f"{TODAY.year:04d}-{TODAY.month:02d}"
PRICE = 40_000
_next = date(TODAY.year + (TODAY.month == 12), TODAY.month % 12 + 1, 1)
LAST = (_next - timedelta(days=1)).day
BACK = TODAY.replace(day=max(2, TODAY.day - 2)) if TODAY.day >= 3 else TODAY

db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit()
BID = b.id
db.add_all([
    models.User(username="mudir", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER),
    models.User(username="adm", password_hash=hash_password("x"),
                full_name="Mashxura", role=roles.ADMINISTRATOR,
                branch_id=BID),
    models.User(username="ustoz", password_hash=hash_password("x"),
                full_name="Sardor", role=roles.TEACHER, branch_id=BID),
])
t = models.Teacher(full_name="Sardor Mirfozilov", is_active=1,
                   branch_id=BID)
db.add(t); db.commit()
TID = t.id
g = models.Group(name="Top students", branch_id=BID, teacher_id=t.id,
                 lesson_price=PRICE, standard_lessons_per_month=12,
                 monthly_fee=480_000, lesson_days="")
db.add(g); db.commit()
GID = g.id
for d in range(1, LAST + 1, 2):
    db.add(models.Lesson(group_id=GID, teacher_id=t.id,
                         date=date(TODAY.year, TODAY.month, d)))
db.commit()


def dropped(name):
    """Sinovda 2 marta kelmay guruhdan chiqarilgan holat."""
    s = models.Student(full_name=name, branch_id=BID, status="trial",
                       group_id=GID, enrolled_date=TODAY - timedelta(days=6))
    db.add(s); db.commit()
    common.attach_group(db, s, GID, joined=s.enrolled_date)
    common.detach_group(db, s, GID)
    s.status = "archived"
    s.group_id = None
    db.commit()
    return s.id


N = dropped("Gayratova Nargiza")
D = dropped("Maqsudova Durdona")
R = dropped("Rahmonova Diyora")
db.close()


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": "x"}
    ).json()["access_token"]}


HM, HA, HT = tok("mudir"), tok("adm"), tok("ustoz")


def status(sid):
    s = SessionLocal()
    st = s.get(models.Student, sid)
    out = (st.status, st.group_id)
    s.close()
    return out


def lessons_from(d):
    return min(len([x for x in range(d.day, LAST + 1) if x % 2 == 1]), 12)


print("=== 1. Guruhsiz faollashtirish taqiqlangan ===")
r = client.post(f"/api/students/{N}/activate", headers=HM,
                json={"on": TODAY.isoformat()})
ck("400 qaytadi", r.status_code, 400)
ck("xabarda sabab bor", "guruhda emas" in r.text, True)
ck("holat o'zgarmadi", status(N), ("archived", None))

print("=== 2. Guruhdan o'chirilganlar ro'yxatida ===")
r = client.get(f"/api/students?group_id={GID}&left=1", headers=HM)
ids = {x["id"] for x in r.json()}
ck("uchalasi ro'yxatda", {N, D, R} <= ids, True)

print("=== 3. Qaytarish ===")
r = client.post(f"/api/groups/{GID}/students/{N}/return", headers=HA,
                json={"on": BACK.isoformat()})
ck("administratorga ruxsat, 200", r.status_code, 200)
res = r.json()
ck("faol va shu guruhda", status(N), ("active", GID))
want_n = lessons_from(BACK)
ck("hisob darslari tanlangan kundan", (res.get("charge") or {}).get(
    "lessons"), want_n)
s = SessionLocal()
ch = [round(-p.amount) for p in s.query(models.Payment).filter(
    models.Payment.student_id == N, models.Payment.kind == "charge",
    models.Payment.period == NOW).all()]
lk = s.query(models.StudentGroupLink).filter_by(
    student_id=N, group_id=GID).first()
s.close()
ck("hisob summasi", ch, [want_n * PRICE])
ck("bog'lanish ochiq", lk.active, 1)
r = client.get(f"/api/students?group_id={GID}", headers=HM)
ck("asosiy ro'yxatda ko'rinadi", N in {x["id"] for x in r.json()}, True)

print("=== 4. Avtomat tozalashlar arxivga qaytarmaydi ===")
s = SessionLocal()
try:
    stu.sweep_left_to_archive(s)
except Exception as e:
    print("sweep xato:", e)
s.close()
client.get("/api/students", headers=HM)     # ro'yxat ochilishi tozalaydi
ck("hali ham faol", status(N), ("active", GID))

print("=== 5. Takror / ruxsatlar ===")
r = client.post(f"/api/groups/{GID}/students/{N}/return", headers=HA,
                json={"on": TODAY.isoformat()})
ck("takror — 400", r.status_code, 400)
r = client.post(f"/api/groups/{GID}/students/{D}/return", headers=HT,
                json={"on": TODAY.isoformat()})
ck("ustozga 403", r.status_code, 403)
ck("Durdona tegilmadi", status(D), ("archived", None))
r = client.post(f"/api/groups/{GID}/students/{D}/return", headers=HM,
                json={"on": (TODAY + timedelta(days=3)).isoformat()})
ck("kelajak sanasi — 400", r.status_code, 400)

print("=== 6. Faollashtirishda guruh tanlash ===")
r = client.post(f"/api/students/{R}/activate", headers=HM,
                json={"on": TODAY.isoformat(), "group_id": GID})
ck("200", r.status_code, 200)
ck("faol va guruhda", status(R), ("active", GID))

print("=== 7. Guruhsiz faol o'quvchiga guruh qo'shish — oylik yoziladi ===")
db = SessionLocal()
sx = models.Student(full_name="Rahmanova Diyora 2", branch_id=BID,
                    status="active", group_id=None,
                    enrolled_date=TODAY - timedelta(days=40))
db.add(sx); db.commit(); X = sx.id
g2 = models.Group(name="Ikkinchi guruh", branch_id=BID, teacher_id=TID,
                  lesson_price=PRICE, standard_lessons_per_month=12,
                  monthly_fee=480_000, lesson_days="")
db.add(g2); db.commit(); G2 = g2.id
db.close()
r = client.post(f"/api/students/{X}/groups", headers=HM,
                json={"group_id": GID, "joined_date": BACK.isoformat()})
ck("200", r.status_code, 200)
ck("hisob qaytdi", bool(r.json().get("charge")), True)
s = SessionLocal()
chx = [round(-p.amount) for p in s.query(models.Payment).filter(
    models.Payment.student_id == X, models.Payment.kind == "charge",
    models.Payment.period == NOW).all()]
s.close()
ck("qo'shilgan kundan oy oxirigacha", chx, [lessons_from(BACK) * PRICE])
r = client.post(f"/api/students/{X}/groups", headers=HM,
                json={"group_id": G2})
ck("ikkinchi guruh — 200", r.status_code, 200)
ck("ikkinchi guruhga qo'shimcha hisob yo'q", r.json().get("charge"), None)
s = SessionLocal()
n_ch = s.query(models.Payment).filter(
    models.Payment.student_id == X, models.Payment.kind == "charge").count()
s.close()
ck("jami bitta hisob", n_ch, 1)

print("\nNATIJA:", "HAMMASI OK" if not fails else f"{len(fails)} XATO: {fails}")
sys.exit(1 if fails else 0)
