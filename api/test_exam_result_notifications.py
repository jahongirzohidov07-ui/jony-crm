"""Test natijasi chiqqanda ota-onaga Telegram xabarnomasi (2026-08-09,
Jahongir so'radi: "test natijalari chiqqanda test natijalari chiqdi
deb ham bildirishnoma kelsin"). notify.enabled()/send() mock qilinadi
(haqiqiy tarmoq so'rovi yo'q), lekin haqiqiy jonli yo'lga
(PUT /api/exams/{id}/results, exams.py) so'rov yuboriladi."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_exam_notif/db.sqlite"
os.makedirs("/tmp/verify_exam_notif", exist_ok=True)
if os.path.exists("/tmp/verify_exam_notif/db.sqlite"):
    os.remove("/tmp/verify_exam_notif/db.sqlite")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, notify
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


sent = []
notify.enabled = lambda: True
notify.send = lambda chat_id, text: sent.append((chat_id, text)) or True

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()

user_t = models.User(username="ust3", full_name="Ustoz Dilnoza",
                     password_hash=hash_password("x"), role="teacher",
                     branch_id=b.id, is_active=1)
db.add(user_t)
db.commit()
teacher = models.Teacher(full_name="Ustoz Dilnoza", branch_id=b.id,
                         user_id=user_t.id, is_active=1)
db.add(teacher)
db.commit()

g = models.Group(name="B1-Weekend", subject="english", level="B1",
                 branch_id=b.id, teacher_id=teacher.id,
                 lesson_time="09:00", monthly_fee=450000,
                 lesson_days="16", capacity=10)
db.add(g)
db.commit()

today = date.today()


def mk_student(name, tag):
    s = models.Student(full_name=name, branch_id=b.id, group_id=g.id,
                       status="active", enrolled_date=today,
                       parent_token=f"tok-{tag}-" + "y" * 12,
                       public_id=f"STU-EX-{tag}",
                       telegram_chat_id=f"chat-ex-{tag}")
    db.add(s)
    db.commit()
    return s


s1 = mk_student("Dilshod Rasulov", "1")
s2 = mk_student("Nigora Fayzullayeva", "2")  # kelmagan bo'ladi

ex = models.Exam(group_id=g.id, kind="unit", unit_no=7, date=today,
                 status="approved", max_score=20)
db.add(ex)
db.commit()


def login():
    r = client.post("/api/auth/login",
                    json={"username": "ust3", "password": "x"})
    return r.json()["access_token"]


H = {"Authorization": f"Bearer {login()}"}

print("=== BIRINCHI NATIJA KIRITISH (2 ta xabar: kelmagan hisobga olinmaydi) ===")
r = client.put(
    f"/api/exams/{ex.id}/results",
    headers=H,
    json={"marks": [
        {"student_id": s1.id, "score": 18, "absent": False},
        {"student_id": s2.id, "absent": True},
    ]},
)
ck("status 200", r.status_code, 200)
ck("faqat kelgan (Dilshod) uchun xabar", len(sent), 1)
ck("xabar Dilshodning chatiga", sent[0][0] if sent else None, "chat-ex-1")
ck("xabarda 'Test natijasi chiqdi' bor",
   "Test natijasi chiqdi" in sent[0][1] if sent else False, True)
ck("xabarda ball toza ko'rinishda (18/20, 18.0 emas)",
   "18/20" in sent[0][1] if sent else False, True)

db.refresh(ex)
ck("exam.status endi 'done'", ex.status, "done")

print("\n=== BALLNI TUZATISH (status allaqachon 'done' — qayta xabar YO'Q) ===")
sent.clear()
r2 = client.put(
    f"/api/exams/{ex.id}/results",
    headers=H,
    json={"marks": [
        {"student_id": s1.id, "score": 19, "absent": False},
    ]},
)
ck("status 200 (tuzatish)", r2.status_code, 200)
ck("tuzatishda qayta xabar ketmaydi", len(sent), 0)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
