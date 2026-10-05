"""IMTIHON BUYURTMASI VAZIFALARI O'ZI YOPILADI (2026-10-05).

Jahongir: "examinerga shunaqa narsa chiqyabdi ptichkani bosmaguncha
turibdi shuni test natijalarini kirgizsa o'zi avtomat yo'q boladigan
bolsin".

Ilgari "Imtihon buyurtmasi EXM-… — <examiner>" vazifasi imtihon
o'tib, natija kiritilgandan keyin ham "N kun kechikdi" bo'lib turardi
— faqat qo'lda belgi qo'yilsa yo'qolardi (muddati o'tgani uchun yana
sabab ham so'rardi)."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/eot/db.sqlite"
os.makedirs("/tmp/eot", exist_ok=True)
if os.path.exists("/tmp/eot/db.sqlite"):
    os.remove("/tmp/eot/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
import common
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


bA = models.Branch(name="A"); bB = models.Branch(name="B")
db.add_all([bA, bB]); db.commit()
ut = models.User(username="ust", full_name="Ustoz",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=bA.id, is_active=1)
db.add(ut); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=bA.id, user_id=ut.id,
                   is_active=1)
db.add(t); db.commit()
groups = []
for i in range(4):
    g = models.Group(name=f"G{i}", subject="english", level="step1",
                     branch_id=bA.id, teacher_id=t.id, lesson_time="09:00",
                     monthly_fee=500000, lesson_days="mon,wed,fri",
                     capacity=15)
    db.add(g); db.commit()
    groups.append(g)
studs = []
for i in range(2):
    s = models.Student(full_name=f"S{i}", branch_id=bA.id,
                       group_id=groups[0].id, status="active",
                       enrolled_date=date.today(), public_id=f"ST{i}")
    db.add(s); studs.append(s)
db.commit()


def mk(uname, branch, role=roles.EXAMINER):
    u = models.User(username=uname, full_name=f"Ex {uname}",
                    password_hash=hash_password("Parol123!"), role=role,
                    branch_id=branch.id, is_active=1)
    db.add(u); db.commit()
    return u


ex1 = mk("ex1", bA)
ex2 = mk("ex2", bA)
hx = mk("hx", bA, roles.HEAD_EXAMINER)
exB = mk("exB", bB)


def H(u):
    tok = c.post('/api/auth/login',
                 json={'username': u, 'password': 'Parol123!'}).json()
    return {"Authorization": f"Bearer {tok['access_token']}"}


HT = H("ust")


def order(gi, days=3):
    r = c.post("/api/me/exam-orders", headers=HT,
               json={"group_id": groups[gi].id,
                     "date": (date.today() + timedelta(days=days)).isoformat(),
                     "kind": "unit", "unit_no": 3})
    assert r.status_code == 200, r.text
    db.expire_all()
    return (db.query(models.ExamOrder)
            .filter(models.ExamOrder.group_id == groups[gi].id).first())


def tasks(o):
    db.expire_all()
    return {t.title: t for t in db.query(models.Task)
            .filter(models.Task.title.like(f"%{o.public_id}%")).all()}


def is_open(t):
    return t.status not in roles.TASK_CLOSED


print("=== 1) SO'ROV: HAR EXAMINERGA NUSXA ===")
o1 = order(0)
tt = tasks(o1)
own = {u.id: tt.get(f"Imtihon buyurtmasi {o1.public_id} — {u.full_name}")
       for u in (ex1, ex2, hx, exB)}
ck("ex1, ex2, boshliq — vazifa bor",
   all(own[u.id] is not None for u in (ex1, ex2, hx)), True)
ck("boshqa filial examineri — yo'q", own[exB.id], None)

print("\n=== 2) ex1 QABUL QILDI ===")
r = c.post(f"/api/exam-orders/{o1.id}/accept", headers=H("ex1"), json={})
ck("qabul 200", r.status_code, 200)
tt = tasks(o1)
mine = tt[f"Imtihon buyurtmasi {o1.public_id} — {ex1.full_name}"]
ck("qabul qilganniki OCHIQ (imtihon hali o'tmagan)", is_open(mine), True)
for u in (ex2, hx):
    tk = tt[f"Imtihon buyurtmasi {o1.public_id} — {u.full_name}"]
    ck(f"{u.username} nusxasi yopildi", tk.status, "done")
    ck(f"{u.username}: sabab yozildi",
       (tk.result or "").startswith("Avtomat yopildi"), True)
ck("ustozga 'Imtihon tasdiqlandi' ochiq",
   is_open(tt[f"Imtihon tasdiqlandi {o1.public_id}"]), True)

print("\n=== 3) USTOZ VAQTNI SURDI — MUDDAT HAM SURILADI ===")
new_day = date.today() + timedelta(days=6)
r = c.post(f"/api/me/exam-orders/{o1.id}/change-time", headers=HT,
           json={"date": new_day.isoformat(), "time": "10:00"})
ck("vaqt o'zgardi 200", r.status_code, 200)
tt = tasks(o1)
ck("examiner vazifasi muddati = yangi kun",
   tt[f"Imtihon buyurtmasi {o1.public_id} — {ex1.full_name}"].deadline,
   new_day)
ck("ustoz vazifasi muddati = yangi kun",
   tt[f"Imtihon tasdiqlandi {o1.public_id}"].deadline, new_day)
ck("qabul qilganga xabar ochiq",
   is_open(tt[f"Ustoz imtihon vaqtini o'zgartirdi {o1.public_id}"]), True)

print("\n=== 4) NATIJA KIRITILDI — HAMMASI O'ZI YOPILADI ===")
db.expire_all()
o1 = db.query(models.ExamOrder).get(o1.id)
ex = db.query(models.Exam).get(o1.exam_id)
ex.max_score = 100; db.commit()
r = c.put(f"/api/exams/{ex.id}/results", headers=H("ex1"),
          json={"marks": [{"student_id": studs[0].id, "score": 80},
                          {"student_id": studs[1].id, "absent": True}]})
ck("natija saqlandi", r.status_code, 200)
tt = tasks(o1)
open_left = [k for k, v in tt.items() if is_open(v)]
ck("buyurtmaning ochiq vazifasi qolmadi", open_left, [])
ck("examiner vazifasi sababi",
   tt[f"Imtihon buyurtmasi {o1.public_id} — {ex1.full_name}"].result,
   "Avtomat yopildi: imtihon natijalari kiritildi")
db.expire_all()
ck("buyurtma 'o'tkazildi'",
   db.query(models.ExamOrder).get(o1.id).status, "done")
r = c.get("/api/me/dashboard", headers=H("ex1"))
ck("examiner panelida bu vazifa yo'q",
   [x["title"] for x in r.json()["tasks"]["rows"]
    if o1.public_id in x["title"]], [])

print("\n=== 5) RAD ETILDI ===")
o2 = order(1)
r = c.post(f"/api/exam-orders/{o2.id}/reject", headers=H("ex2"),
           json={"reason": "busy", "note": "Band"})
ck("rad 200", r.status_code, 200)
tt = tasks(o2)
ck("examinerlar nusxalari yopildi",
   [k for k, v in tt.items() if k.startswith("Imtihon buyurtmasi EXM")
    and is_open(v)], [])
ck("ustozga 'rad etildi' xabari OCHIQ qoladi",
   is_open(tt[f"Imtihon buyurtmasi rad etildi {o2.public_id}"]), True)

print("\n=== 6) USTOZ BEKOR QILDI ===")
o3 = order(2)
r = c.post(f"/api/me/exam-orders/{o3.id}/cancel", headers=HT, json={})
ck("bekor 200", r.status_code, 200)
ck("bekor: ochiq vazifa qolmadi",
   [k for k, v in tasks(o3).items() if is_open(v)], [])

print("\n=== 7) ESKI OSILIB QOLGANLAR (deploy/cron supurgisi) ===")
o4 = order(3)
c.post(f"/api/exam-orders/{o4.id}/accept", headers=H("ex2"), json={})
db.expire_all()
o4 = db.query(models.ExamOrder).get(o4.id)
# Eski holat: nusxalar ochiq, imtihon o'tgan (natija yo'lidan emas)
for tk in tasks(o4).values():
    tk.status = "new"; tk.result = None
db.query(models.Exam).get(o4.exam_id).status = "done"
# Begona vazifa — tegilmasligi kerak
db.add(models.Task(title=f"Imtihon buyurtmasi rad etildi {o4.public_id}",
                   assignee_id=ut.id, status="new", created_by="Tizim"))
db.add(models.Task(title="Qo'lda vazifa EXM-999999 haqida",
                   assignee_id=ut.id, status="new", created_by="Tizim"))
db.commit()
n = common.close_stale_exam_order_tasks(db)
ck("supurgi bir nechtasini yopdi", n >= 3, True)
tt = tasks(o4)
ck("eski buyurtma vazifalari yopildi",
   sorted(k for k, v in tt.items() if is_open(v)),
   [f"Imtihon buyurtmasi rad etildi {o4.public_id}"])
db.expire_all()
ck("buyurtma 'o'tkazildi' bo'ldi",
   db.query(models.ExamOrder).get(o4.id).status, "done")
manual = (db.query(models.Task)
          .filter(models.Task.title == "Qo'lda vazifa EXM-999999 haqida")
          .first())
ck("qo'lda yozilgan vazifaga tegilmadi", manual.status, "new")
ck("ikkinchi yurishda ish yo'q", common.close_stale_exam_order_tasks(db), 0)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
