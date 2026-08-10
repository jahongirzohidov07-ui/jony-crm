"""IMTIHON SO'ROVI: USTOZDAN EXAMINERGA (2026-08-10).

Jahongir: "Qabul qilinishi kerak bo'lgan imtihonlar ko'rinmayapti
deyabdi examinerlar. Ustozlar yuborgan so'rov examinerlarga
keladimi, to'g'rilab ko'r — ulanganmi bular."

TEKSHIRUV NATIJASI: zanjir ULANGAN edi — ustoz so'rov yuborsa, SHU
FILIALDAGI examiner uni ko'radi. LEKIN ikki filialda ishlaydigan
examiner ikkinchi filialdagi so'rovni RO'YXATDA ko'rmasdi, chunki
ro'yxat faqat ASOSIY filialni tekshirardi. Eng chalkashi: qabul
qilish (accept) allaqachon barcha filiallarni hisobga olardi —
ya'ni examiner qabul qila oladigan so'rovni ko'ra olmasdi."""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/veo/db.sqlite"
os.makedirs("/tmp/veo", exist_ok=True)
if os.path.exists("/tmp/veo/db.sqlite"):
    os.remove("/tmp/veo/db.sqlite")
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


bA = models.Branch(name="A"); bB = models.Branch(name="B")
db.add_all([bA, bB]); db.commit()

ut = models.User(username="ust", full_name="Ustoz",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=bA.id, is_active=1)
db.add(ut); db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=bA.id, user_id=ut.id,
                   is_active=1)
db.add(t); db.commit()
g = models.Group(name="G1", subject="english", level="step1",
                 branch_id=bA.id, teacher_id=t.id, lesson_time="09:00",
                 monthly_fee=500000, lesson_days="mon,wed,fri", capacity=15)
db.add(g); db.commit()
for i in range(3):
    db.add(models.Student(full_name=f"S{i}", branch_id=bA.id, group_id=g.id,
                          status="active", enrolled_date=date.today(),
                          public_id=f"ST{i}"))
db.commit()


def mk_ex(uname, branch, extra_branch=None, role=None):
    u = models.User(username=uname, full_name=f"Ex {uname}",
                    password_hash=hash_password("Parol123!"),
                    role=role or roles.EXAMINER,
                    branch_id=branch.id if branch else None, is_active=1)
    db.add(u); db.commit()
    if extra_branch:
        db.add(models.UserBranch(user_id=u.id, branch_id=extra_branch.id))
        db.commit()
    return u


ex_a = mk_ex("ex_a", bA)
ex_b = mk_ex("ex_b", bB)
ex_ab = mk_ex("ex_ab", bB, extra_branch=bA)   # IKKI filialli
head = mk_ex("hx", bA, role=roles.HEAD_EXAMINER)


def H(u):
    return {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':u,'password':'Parol123!'}).json()['access_token']}"}


print("=== USTOZ IMTIHON SO'RAYDI ===")
when = (date.today() + timedelta(days=3)).isoformat()
r = c.post("/api/me/exam-orders", headers=H("ust"),
           json={"group_id": g.id, "date": when, "kind": "unit",
                 "unit_no": 3})
ck("so'rov yuborildi", r.status_code, 200)
o = db.query(models.ExamOrder).first()
ck("so'rov guruh filialiga yozildi", o.branch_id, bA.id)
ck("holati 'new'", o.status, "new")
ck("o'quvchi soni avtomat", o.students_count, 3)

print("\n=== KIM RO'YXATDA KO'RADI ===")
r = c.get("/api/exam-orders", headers=H("ex_a"))
ck("SHU filial examineri ko'radi", len(r.json()["rows"]), 1)
ck("'yangi so'rov' sanog'i to'g'ri", r.json()["new"], 1)

r = c.get("/api/exam-orders", headers=H("ex_ab"))
ck("IKKI FILIALLI examiner ham ko'radi (avval ko'rmasdi)",
   len(r.json()["rows"]), 1)

r = c.get("/api/exam-orders", headers=H("hx"))
ck("examinerlar boshlig'i ko'radi", len(r.json()["rows"]), 1)

r = c.get("/api/exam-orders", headers=H("ex_b"))
ck("BEGONA filial examineri KO'RMAYDI (to'g'ri)",
   len(r.json()["rows"]), 0)

print("\n=== QABUL QILISH ===")
r = c.post(f"/api/exam-orders/{o.id}/accept", headers=H("ex_ab"), json={})
ck("ikki filialli examiner qabul qiladi", r.status_code, 200)
db.refresh(o)
ck("holati 'accepted'", o.status, "accepted")
ck("imtihon avtomat yaratildi", bool(o.exam_id), True)
ex = db.query(models.Exam).get(o.exam_id)
ck("imtihon 'approved' holatida", ex.status, "approved")
ck("ustozga examiner ismi ko'rinadi", ex.approved_by, "Ex ex_ab")

print("\n=== USTOZ O'Z SO'ROVINI KO'RADI ===")
r = c.get("/api/me/exam-orders", headers=H("ust"))
ck("ustoz ro'yxati 200", r.status_code, 200)
rows = r.json().get("rows") or r.json().get("orders") or []
ck("so'rovi ko'rinadi", len(rows) >= 1, True)

print("\n=== TAKROR SO'ROV BLOKLANADI ===")
r = c.post("/api/me/exam-orders", headers=H("ust"),
           json={"group_id": g.id, "date": when, "kind": "unit",
                 "unit_no": 4})
ck("bir kunga ikkinchi so'rov rad etiladi", r.status_code, 400)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
