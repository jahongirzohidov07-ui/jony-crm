"""JONY TEACHER ilovasi: bugungi darslar, yo'qlama ekrani va
xavfsizlik (2026-08-10).

Eng muhim tekshiruv: ustoz FAQAT O'Z guruhining darsini ochishi va
belgilashi mumkin. Boshqa ustozning darsini ochishga urinsa 403.
Shuningdek yo'qlama YOZISH mavjud yo'l orqali ketishi (ya'ni
ikkinchi nusxa yozilmagani) ham tasdiqlanadi."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_teacher_app/db.sqlite"
os.makedirs("/tmp/verify_teacher_app", exist_ok=True)
if os.path.exists("/tmp/verify_teacher_app/db.sqlite"):
    os.remove("/tmp/verify_teacher_app/db.sqlite")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def ckt(name, cond):
    ck(name, bool(cond), True)


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()

today = roles.local_today()


def mk_teacher(uname, name):
    u = models.User(username=uname, full_name=name,
                    password_hash=hash_password("Parol123!"),
                    role=roles.TEACHER, branch_id=b.id, is_active=1)
    db.add(u)
    db.commit()
    t = models.Teacher(full_name=name, branch_id=b.id, user_id=u.id,
                       is_active=1)
    db.add(t)
    db.commit()
    return u, t


u1, t1 = mk_teacher("ustA", "Ustoz Anvar")
u2, t2 = mk_teacher("ustB", "Ustoz Bobur")


def mk_group(name, teacher, time_):
    g = models.Group(name=name, subject="english", level="B1",
                     branch_id=b.id, teacher_id=teacher.id,
                     lesson_time=time_, monthly_fee=500000,
                     lesson_days="135", capacity=15)
    db.add(g)
    db.commit()
    return g


gA = mk_group("IELTS-A", t1, "09:00")
gB = mk_group("IELTS-B", t2, "11:00")


def mk_student(name, g, tag, status="active"):
    s = models.Student(full_name=name, branch_id=b.id, group_id=g.id,
                       status=status, enrolled_date=today,
                       public_id=f"STU-T-{tag}")
    db.add(s)
    db.commit()
    return s


sA1 = mk_student("Aziz Karimov", gA, "1")
sA2 = mk_student("Bahora Yulduz", gA, "2")
sA3 = mk_student("Muzlagan Bola", gA, "3", status="frozen")
sB1 = mk_student("Begona Bola", gB, "9")

lsA = models.Lesson(group_id=gA.id, date=today, teacher_id=u1.id, held=0)
lsB = models.Lesson(group_id=gB.id, date=today, teacher_id=u2.id, held=0)
db.add_all([lsA, lsB])
db.commit()

# Bir hafta oldingi, yo'qlamasiz dars — "unutilgan" ro'yxatida chiqishi kerak
old_ls = models.Lesson(group_id=gA.id, date=today - timedelta(days=3),
                       teacher_id=u1.id, held=0)
db.add(old_ls)
db.commit()


def H(uname):
    r = client.post("/api/auth/login",
                    json={"username": uname, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


H1, H2 = H("ustA"), H("ustB")

print("=== BOSH EKRAN ===")
r = client.get("/api/teacher/home", headers=H1)
ck("status 200", r.status_code, 200)
d = r.json()
ck("o'z ismi", d["teacher"], "Ustoz Anvar")
ck("1 ta guruhi bor", d["groups"], 1)
ck("faol o'quvchilar sanaladi (muzlagan emas)", d["students"], 2)
ck("bugun 1 ta dars", len(d["today"]), 1)
ck("dars hali belgilanmagan", d["pending"], 1)

print("\n=== BUGUN + UNUTILGAN DARSLAR ===")
r = client.get("/api/teacher/today", headers=H1)
ck("status 200", r.status_code, 200)
t = r.json()
ck("bugungi dars 1 ta", len(t["lessons"]), 1)
ck("unutilgan dars ko'rinadi", len(t["missed"]), 1)
ck("unutilgan dars sanasi to'g'ri", t["missed"][0]["date"],
   (today - timedelta(days=3)).isoformat())

print("\n=== YO'QLAMA EKRANI ===")
r = client.get(f"/api/teacher/lesson/{lsA.id}", headers=H1)
ck("status 200", r.status_code, 200)
L = r.json()
ck("guruh nomi", L["group"], "IELTS-A")
ck("muzlatilgan o'quvchi ro'yxatda YO'Q", len(L["students"]), 2)
ck("bugungi dars tahrirlanadi", L["editable"], True)
ck("boshida hech kim belgilanmagan",
   [s["present"] for s in L["students"]], [None, None])

print("\n=== XAVFSIZLIK: BOSHQA USTOZNING DARSI ===")
r = client.get(f"/api/teacher/lesson/{lsB.id}", headers=H1)
ck("boshqa ustozning darsi ochilmaydi", r.status_code, 403)
r = client.get(f"/api/teacher/lesson/{lsA.id}", headers=H2)
ck("teskarisi ham bloklanadi", r.status_code, 403)

print("\n=== YO'QLAMA SAQLASH (mavjud yo'l orqali) ===")
r = client.put(f"/api/lessons/{lsA.id}/attendance", headers=H1,
               json={"marks": [
                   {"student_id": sA1.id, "present": True, "late": False,
                    "homework": 2},
                   {"student_id": sA2.id, "present": True, "late": True},
               ]})
ck("saqlash 200", r.status_code, 200)

r = client.get(f"/api/teacher/lesson/{lsA.id}", headers=H1)
L2 = r.json()
by = {s["full_name"]: s for s in L2["students"]}
ck("Aziz keldi (1)", by["Aziz Karimov"]["present"], 1)
ck("Aziz uy vazifasi bajardi (2)", by["Aziz Karimov"]["homework"], 2)
ck("Bahora kech keldi (2)", by["Bahora Yulduz"]["present"], 2)

r = client.get("/api/teacher/home", headers=H1)
ck("endi kutayotgan dars yo'q", r.json()["pending"], 0)

print("\n=== BAHO QO'YISH ===")
r = client.put(f"/api/lessons/{lsA.id}/grades", headers=H1,
               json={"marks": [{"student_id": sA1.id, "score": 5}]})
ck("baho saqlandi", r.status_code, 200)
r = client.get(f"/api/teacher/lesson/{lsA.id}", headers=H1)
by = {s["full_name"]: s for s in r.json()["students"]}
ck("baho ekranda ko'rinadi", by["Aziz Karimov"]["grade"], 5)

print("\n=== HAFTALIK JADVAL ===")
r = client.get("/api/teacher/week", headers=H1)
ck("status 200", r.status_code, 200)
w = r.json()
ck("7 kun qaytadi", len(w["days"]), 7)
ckt("bugun belgilangan", any(x["is_today"] for x in w["days"]))
all_lessons = [l for day in w["days"] for l in day["lessons"]]
ckt("faqat o'z guruhining darslari",
    all(l["group"] == "IELTS-A" for l in all_lessons))

print("\n=== KELAJAKDAGI DARS BELGILANMAYDI ===")
fut = models.Lesson(group_id=gA.id, date=today + timedelta(days=2),
                    teacher_id=u1.id, held=0)
db.add(fut)
db.commit()
r = client.get(f"/api/teacher/lesson/{fut.id}", headers=H1)
ck("kelajakdagi dars ochiladi (ko'rish uchun)", r.status_code, 200)
ck("lekin tahrirlanmaydi", r.json()["editable"], False)
ckt("sababi tushuntirilgan", bool(r.json()["readonly_reason"]))

print("\n=== ROL TEKSHIRUVI ===")
adm = models.User(username="admin1", full_name="Administrator",
                  password_hash=hash_password("Parol123!"),
                  role=roles.SALES_MANAGER, branch_id=b.id, is_active=1)
db.add(adm)
db.commit()
Ha = H("admin1")
r = client.get("/api/teacher/home", headers=Ha)
ck("ustoz bo'lmagan xodim kira olmaydi", r.status_code, 403)
r = client.get("/api/teacher/home")
ckt("loginsiz kirish yopiq", r.status_code in (401, 403))

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
