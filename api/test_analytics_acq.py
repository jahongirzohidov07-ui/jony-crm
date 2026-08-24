"""MANBA VORONKASI, HAYOT DAVRI VA MAJBURIY KETISH SABABI (2026-08-24).

Jahongir: "lid manbasi qayerdan kelayotganligi va ketish sabablari
statistikasi... har bir ustozdan ketish sabablari... biz togridan
togri keldimi yoki avval telegram instagramdan aloqaga chiqib
kursga yozilib keldimi... ketish sababini majburiy qil".
"""
import os, sys
from datetime import date, timedelta, datetime

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_acq/db.sqlite"
os.makedirs("/tmp/verify_acq", exist_ok=True)
if os.path.exists("/tmp/verify_acq/db.sqlite"):
    os.remove("/tmp/verify_acq/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


TODAY = roles.local_today()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
founder = models.User(username="asoschi", full_name="ASOSCHI",
                      password_hash=hash_password("Parol123!"),
                      role=roles.FOUNDER, branch_id=b.id, is_active=1)
admin = models.User(username="admin1", full_name="ADMIN",
                    password_hash=hash_password("Parol123!"),
                    role=roles.ADMINISTRATOR, branch_id=b.id, is_active=1)
db.add_all([founder, admin]); db.commit()
t1 = models.Teacher(full_name="Ustoz Aziz", branch_id=b.id)
t2 = models.Teacher(full_name="Ustoz Malika", branch_id=b.id)
db.add_all([t1, t2]); db.commit()
g1 = models.Group(name="G1", branch_id=b.id, teacher_id=t1.id,
                  lesson_time="10:00", monthly_fee=500000)
g2 = models.Group(name="G2", branch_id=b.id, teacher_id=t2.id,
                  lesson_time="12:00", monthly_fee=500000)
db.add_all([g1, g2]); db.commit()


def H(u):
    tok = c.post("/api/auth/login",
                 json={"username": u, "password": "Parol123!"}
                 ).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


A = H("asoschi")


def mk_student(name, enrolled, group, left=None, status="active"):
    st = models.Student(full_name=name, branch_id=b.id, group_id=group.id,
                        enrolled_date=enrolled, status=status,
                        left_date=left)
    db.add(st); db.commit()
    return st


def mk_lead(name, source, stage, created, student=None):
    l = models.Lead(full_name=name, source=source, stage=stage,
                    branch_id=b.id,
                    created_at=datetime.combine(created, datetime.min.time()),
                    converted_student_id=student.id if student else None)
    db.add(l); db.commit()
    return l


# --- Onlayn (telegram): 4 lid, 2 tasi o'quvchi bo'ldi
s1 = mk_student("Tel Bir", TODAY - timedelta(days=200), g1)
s2 = mk_student("Tel Ikki", TODAY - timedelta(days=100), g1)
mk_lead("Tel Bir", "telegram", "converted", TODAY - timedelta(days=210), s1)
mk_lead("Tel Ikki", "telegram", "converted", TODAY - timedelta(days=110), s2)
mk_lead("Tel Uch", "telegram", "no_show", TODAY - timedelta(days=60))
mk_lead("Tel Tort", "telegram", "contacted", TODAY - timedelta(days=30))
# --- To'g'ridan-to'g'ri (visit): 2 lid, 2 tasi o'quvchi
s3 = mk_student("Vizit Bir", TODAY - timedelta(days=150), g2)
s4 = mk_student("Vizit Ikki", TODAY - timedelta(days=40), g2)
mk_lead("Vizit Bir", "visit", "converted", TODAY - timedelta(days=152), s3)
mk_lead("Vizit Ikki", "visit", "converted", TODAY - timedelta(days=41), s4)
# to'lovlar
for st, amt in ((s1, 1500000), (s2, 500000), (s3, 2000000), (s4, 500000)):
    db.add(models.Payment(student_id=st.id, amount=amt, kind="payment",
                          period=TODAY.strftime("%Y-%m")))
db.commit()
# marketing xarajati (telegram kanali)
db.add(models.Expense(date=TODAY - timedelta(days=20), category="ads",
                      amount=1000000, channel="telegram", branch_id=b.id))
db.commit()

print("=== 1. MANBA VORONKASI ===")
r = c.get("/api/analytics/acquisition?months=12", headers=A)
ck("status 200", r.status_code, 200)
j = r.json()
src = {x["key"]: x for x in j["sources"]}
ck("telegram 4 lid", src["telegram"]["leads"], 4)
ck("telegram 2 o'quvchi", src["telegram"]["converted"], 2)
ck("telegram konversiya 50%", src["telegram"]["conversion"], 50.0)
ck("visit konversiya 100%", src["visit"]["conversion"], 100.0)
ck("telegram daromadi", src["telegram"]["revenue"], 2000000)
ck("telegram xarajati", src["telegram"]["spend"], 1000000)
ck("telegram CAC = 1M/2", src["telegram"]["cac"], 500000)
ck("telegram ROI = +100%", src["telegram"]["roi"], 100.0)
ck("visitda xarajat yo'q -> ROI bo'sh", src["visit"]["roi"], None)
ck("o'rtacha kun hisoblandi", src["visit"]["avg_days"] is not None, True)

print("\n=== 2. TO'G'RIDAN-TO'G'RI / ONLAYN GURUHLARI ===")
grp = {x["key"]: x for x in j["groups"]}
ck("onlayn guruhida 4 lid", grp["online"]["leads"], 4)
ck("to'g'ridan-to'g'ri 2 lid", grp["direct"]["leads"], 2)
ck("onlayn ulushi 66.7%", grp["online"]["share"], 66.7)
ck("to'g'ridan-to'g'ri konversiyasi yuqori",
   grp["direct"]["conversion"] > grp["online"]["conversion"], True)

print("\n=== 3. VORONKA BOSQICHLARI ===")
fn = {x["key"]: x for x in j["funnel"]}
ck("jami 6 lid", fn["leads"]["count"], 6)
ck("o'quvchi bo'lgan 4", fn["converted"]["count"], 4)
ck("bog'lanilgan 5 (converted+contacted)", fn["contacted"]["count"], 5)
ck("tushish ko'rsatilgan", fn["converted"]["drop"] >= 0, True)
lost = {x["key"]: x["count"] for x in j["lost"]}
ck("sinovga kelmagan 1", lost["no_show"], 1)

print("\n=== 4. KETISH SABABI MAJBURIY ===")
r = c.post(f"/api/students/{s1.id}/remove-from-group", headers=A,
           json={"reason": "shunchaki", "on_date": TODAY.isoformat()})
ck("kategoriyasiz rad etildi", r.status_code, 400)
ck("sabab tushuntirildi", "tanlang" in r.json()["detail"], True)
r = c.post(f"/api/students/{s1.id}/remove-from-group", headers=A,
           json={"reason": "Ustozdan norozi — dars yoqmadi",
                 "reason_code": "xxx", "on_date": TODAY.isoformat()})
ck("noto'g'ri kategoriya rad etildi", r.status_code, 400)
r = c.post(f"/api/students/{s1.id}/remove-from-group", headers=A,
           json={"reason": "Ustozdan norozi", "reason_code": "teacher",
                 "on_date": TODAY.isoformat()})
ck("to'g'ri kategoriya bilan o'tdi", r.status_code, 200)
lr = db.query(models.LeaveReason).filter(
    models.LeaveReason.student_id == s1.id).first()
ck("LeaveReason yozildi", lr is not None, True)
ck("sabab kodi to'g'ri", lr.reason, "teacher")
ck("ustoz biriktirildi", lr.teacher_id, t1.id)

print("\n=== 5. USTOZ KESIMIDA SABABLAR ===")
# ikkinchi ketish — boshqa ustoz, boshqa sabab
r = c.post(f"/api/students/{s3.id}/remove-from-group", headers=A,
           json={"reason": "Narx", "reason_code": "price",
                 "on_date": TODAY.isoformat()})
ck("ikkinchi chiqarish ok", r.status_code, 200)
r = c.get("/api/analytics/churn?months=12", headers=A)
ck("churn 200", r.status_code, 200)
byt = {x["label"]: x for x in r.json()["by_teacher"]}
ck("Aziz sabablari ro'yxati", 
   [x["key"] for x in byt["Ustoz Aziz"]["reasons"]], ["teacher"])
ck("Malika sabablari ro'yxati",
   [x["key"] for x in byt["Ustoz Malika"]["reasons"]], ["price"])
ck("sabab nomi ham bor",
   byt["Ustoz Aziz"]["reasons"][0]["label"], "Ustozdan norozi")

print("\n=== 6. HAYOT DAVRI ===")
r = c.get("/api/analytics/lifecycle?months=24", headers=A)
ck("status 200", r.status_code, 200)
lf = r.json()
ck("2 ta ketgan", lf["total_left"], 2)
ck("gistogramma 5 ustun", len(lf["histogram"]), 5)
tot = sum(h["count"] for h in lf["histogram"])
ck("gistogramma yig'indisi to'g'ri", tot, 2)
ck("o'rtacha oy hisoblandi", lf["avg_months"] > 0, True)
srcs = {x["label"]: x for x in lf["by_source"]}
ck("manba kesimi bor", len(srcs) >= 1, True)
tch = {x["label"]: x for x in lf["by_teacher"]}
ck("ustoz kesimi bor", "Ustoz Aziz" in tch, True)

print("\n=== 7. QAYTGANLAR VA UYQUDAGILAR ===")
back = mk_student("Qaytgan", TODAY - timedelta(days=300), g1,
                  left=TODAY - timedelta(days=100), status="active")
frz = models.Student(full_name="Uyquda", branch_id=b.id, group_id=g1.id,
                     enrolled_date=TODAY - timedelta(days=300),
                     status="frozen",
                     frozen_until=TODAY - timedelta(days=90))
db.add(frz); db.commit()
r = c.get("/api/analytics/lifecycle?months=24", headers=A)
lf = r.json()
ck("qaytgan topildi", lf["returned"]["count"] >= 1, True)
ck("uyquda topildi", lf["dormant"]["count"] >= 1, True)
names = [x["student"] for x in lf["dormant"]["rows"]]
ck("uyqudagi ismi ro'yxatda", "Uyquda" in names, True)

print("\n=== 8. XAVFSIZLIK ===")
r = c.get("/api/analytics/acquisition")
ck("loginsiz yopiq", r.status_code in (401, 403), True)
r = c.get("/api/analytics/lifecycle", headers=H("admin1"))
ck("administratorga yopiq", r.status_code, 403)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
