"""IMTIHON BUYURTMASI: VAQTNI KO'CHIRISH VA RAD ETISH SABABLARI (2026-10-02).

Jahongir: "Test qabul qilishda rad etish bilan vaqtni ko'chirishni
qo'shish kerak. Ko'chirishni tanlab o'ziga mos kun vaqtni examiner
tanlasa keyin ustozga notification boradi keyin ustozgayam qulay bo'lsa
accept qilinadi. Rad qilishga sabablar qo'shib qo'yish kerak: Shaxsiy
sababga ko'ra, Xatolik tufayli, Examiner yo'q va h.k."

Tekshiriladi:
  1. Rad etish sabablari ro'yxatida yangi sabablar bor.
  2. Examiner yangi buyurtmaga ko'chirish taklif qiladi -> holat
     "reschedule", ustozga vazifa, sababsiz/o'tgan kunga — 400.
  3. Ustoz qabul qiladi -> sana/vaqt yangilanadi, buyurtma shu examiner
     nomiga qabul qilinadi, imtihon yangi sanada; examinerga vazifa.
  4. Qabul qilingan buyurtmani ko'chirish, ustoz rad etadi -> eski
     vaqtida "qabul qilingan" bo'lib qoladi, imtihon sanasi o'zgarmaydi.
  5. Boshqa ustoz javob bera olmaydi; taklif kutilayotganda qayta
     taklif yoki rad etish — 400.
"""
import os
import sys
import tempfile
from datetime import date, timedelta

_DIR = os.path.join(tempfile.gettempdir(), "exam_order_resched_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common as _cm_stub                          # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

_cm_stub._ensure_month_charges = lambda db, **kw: None

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="A"); db.add(b); db.commit()
BID = b.id


def mkuser(login, role):
    u = models.User(username=login, full_name=login.upper(),
                    password_hash=hash_password("Parol123!"), role=role,
                    branch_id=BID, is_active=1)
    db.add(u); db.commit()
    return u.id


UT = mkuser("ust", roles.TEACHER)
UT2 = mkuser("ust2", roles.TEACHER)
EX = mkuser("ex", roles.EXAMINER)
t = models.Teacher(full_name="Ustoz", branch_id=BID, user_id=UT, is_active=1)
t2 = models.Teacher(full_name="Ustoz2", branch_id=BID, user_id=UT2,
                    is_active=1)
db.add_all([t, t2]); db.commit()
g = models.Group(name="G1", subject="english", level="step1", branch_id=BID,
                 teacher_id=t.id, lesson_time="09:00", monthly_fee=500000,
                 lesson_days="mon,wed,fri", capacity=15)
db.add(g); db.commit()
GID = g.id
db.close()


def H(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "Parol123!"}
    ).json()["access_token"]}


HT, HT2, HE = H("ust"), H("ust2"), H("ex")
D1 = date.today() + timedelta(days=3)
D2 = date.today() + timedelta(days=5)
D3 = date.today() + timedelta(days=8)


def order(day):
    r = c.post("/api/me/exam-orders", headers=HT,
               json={"group_id": GID, "date": day.isoformat(),
                     "kind": "unit", "unit_no": 2})
    return r.json()["id"]


def get(oid):
    s = SessionLocal()
    o = s.query(models.ExamOrder).get(oid)
    ex = s.query(models.Exam).get(o.exam_id) if o.exam_id else None
    res = (o.status, o.date, o.time, o.accepted_by,
           ex.date if ex else None)
    s.close()
    return res


def tasks_for(uid, word):
    s = SessionLocal()
    n = sum(1 for x in s.query(models.Task).all()
            if word in (x.title or "") and uid in
            {getattr(x, "assignee_id", None), getattr(x, "assigned_to", None),
             getattr(x, "user_id", None)})
    s.close()
    return n


print("=== 1. Rad etish sabablari ===")
q = c.get("/api/exam-orders", headers=HE).json()
keys = {r["key"] for r in q["reject_reasons"]}
ck("yangi sabablar bor", {"personal", "mistake", "no_examiner"} <= keys, True)
ck("ko'chirish sabablari ham bor", len(q["reschedule_reasons"]) >= 4, True)

print("\n=== 2. Ko'chirish taklifi ===")
O1 = order(D1)
ck("sababsiz — 400", c.post(f"/api/exam-orders/{O1}/reschedule", headers=HE,
                            json={"date": D2.isoformat()}).status_code, 400)
ck("o'tgan kunga — 400", c.post(
    f"/api/exam-orders/{O1}/reschedule", headers=HE,
    json={"date": (date.today() - timedelta(days=1)).isoformat(),
          "reason": "personal"}).status_code, 400)
r = c.post(f"/api/exam-orders/{O1}/reschedule", headers=HE,
           json={"date": D2.isoformat(), "time": "15:30",
                 "reason": "personal", "note": "Ertalab darsim bor"})
ck("taklif yuborildi", r.status_code, 200)
ck("javobda taklif", (r.json()["status"], r.json()["proposal"]["date"],
                      r.json()["proposal"]["time"],
                      r.json()["proposal"]["reason_label"]),
   ("reschedule", D2.isoformat(), "15:30", "Shaxsiy sababga ko'ra"))
ck("ustozga xabar ketdi", tasks_for(UT, "ko'chirish taklifi") >= 1, True)
ck("examiner navbatida ko'rinadi", any(
    x["id"] == O1 for x in c.get("/api/exam-orders", headers=HE)
    .json()["rows"]), True)
ck("qayta taklif — 400", c.post(
    f"/api/exam-orders/{O1}/reschedule", headers=HE,
    json={"date": D3.isoformat(), "reason": "busy"}).status_code, 400)
ck("kutilayotganda rad etish — 400", c.post(
    f"/api/exam-orders/{O1}/reject", headers=HE,
    json={"reason": "busy", "note": "x"}).status_code, 400)

print("\n=== 3. Ustoz qabul qiladi ===")
ck("boshqa ustoz javob bera olmaydi", c.post(
    f"/api/me/exam-orders/{O1}/reschedule-answer", headers=HT2,
    json={"accept": True}).status_code, 403)
r = c.post(f"/api/me/exam-orders/{O1}/reschedule-answer", headers=HT,
           json={"accept": True})
ck("qabul qilindi", r.status_code, 200)
ck("yangi vaqt, examiner nomiga, imtihon yangi sanada", get(O1),
   ("accepted", D2, "15:30", EX, D2))
ck("examinerga xabar", tasks_for(EX, "ko'chirishni qabul qildi") >= 1, True)
ck("taklif tozalandi", r.json()["proposal"], None)

print("\n=== 4. Qabul qilingan buyurtma, ustoz rad etadi ===")
O2 = order(D1 + timedelta(days=1))
ck("examiner qabul qildi", c.post(f"/api/exam-orders/{O2}/accept",
                                  headers=HE, json={}).status_code, 200)
before = get(O2)
r = c.post(f"/api/exam-orders/{O2}/reschedule", headers=HE,
           json={"date": D3.isoformat(), "reason": "no_examiner"})
ck("taklif", r.status_code, 200)
r = c.post(f"/api/me/exam-orders/{O2}/reschedule-answer", headers=HT,
           json={"accept": False, "note": "O'quvchilar o'sha kuni yo'q"})
ck("rad etildi", r.status_code, 200)
ck("eski vaqtida qabul qilingan bo'lib qoldi", get(O2), before)
ck("examinerga xabar", tasks_for(EX, "rozi emas") >= 1, True)
ck("javob yo'q taklifga — 400", c.post(
    f"/api/me/exam-orders/{O2}/reschedule-answer", headers=HT,
    json={"accept": True}).status_code, 400)

print("\n=== 5. Yangi sabab bilan rad etish ===")
O3 = order(D3 + timedelta(days=2))
r = c.post(f"/api/exam-orders/{O3}/reject", headers=HE,
           json={"reason": "no_examiner", "note": "Shu kuni hamma band"})
ck("rad etildi", (r.status_code, r.json().get("reject_reason_label")),
   (200, "Examiner yo'q"))

print()
if fails:
    print(f"{len(fails)} ta XATO: {fails}")
    sys.exit(1)
print("HAMMASI OK")
