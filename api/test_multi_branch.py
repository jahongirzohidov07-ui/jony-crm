"""IKKI FILIALGA biriktirilgan xodim (2026-08-10, Jahongir xabar berdi).

MUAMMO EDI:
  1. Ikki filialda dars beradigan ustoz "Guruhlarim" ro'yxatida ikkala
     filial guruhini KO'RARDI, lekin ikkinchi filialdagisini ochmoqchi
     bo'lsa "Bu guruh boshqa filialga tegishli" (403) chiqardi.
  2. Ikki filialga biriktirilgan examiner ikkinchi filial imtihonini
     qabul qila olmasdi.
  3. Filial tanlagich (BranchPicker) bunday xodimga umuman chiqmasdi.

IKKI SABAB BOR EDI:
  a) Ro'yxat tekshiruvi (scope_to_branch) BARCHA filiallarni hisobga
     olardi, yakka yozuv tekshiruvlari esa faqat user.branch_id ni —
     ya'ni ikkalasi BOSHQA-BOSHQA qoidadan yurardi;
  b) HR ustoz kartasidan ikkinchi filialni belgilaganda faqat
     teacher_branches ga yozilardi, _user_branch_ids esa faqat
     user_branches ni o'qirdi — demak kirish hisobi baribir bitta
     filialda qolardi.

Bu test IKKALA sababni ham qoplaydi: qo'shimcha filial ATAYLAB faqat
USTOZ KARTASIDAN (teacher_branches) beriladi — HR amalda shunday
qiladi."""

import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_multibranch/db.sqlite"
os.makedirs("/tmp/verify_multibranch", exist_ok=True)
if os.path.exists("/tmp/verify_multibranch/db.sqlite"):
    os.remove("/tmp/verify_multibranch/db.sqlite")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

client = TestClient(main.app)
db = SessionLocal()

bA = models.Branch(name="Filial A")
bB = models.Branch(name="Filial B")
db.add_all([bA, bB]); db.commit()

today = roles.local_today()

# --- Ikki filialda dars beradigan ustoz ---
ut = models.User(username="ust2f", full_name="Ustoz Ikki",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=bA.id, is_active=1)
db.add(ut); db.commit()
tt = models.Teacher(full_name="Ustoz Ikki", branch_id=bA.id,
                    user_id=ut.id, is_active=1)
db.add(tt); db.commit()
# Qo'shimcha filial IKKI joyda saqlanishi mumkin — ikkalasini ham qo'yamiz
# HAQIQIY HOLAT: HR faqat USTOZ KARTASIDAN ikkinchi filialni
# belgilaydi (teachers.py:_sync_teacher_branches) — user_branches
# ga hech narsa yozilmaydi. Aynan shu holat ishlashi kerak.
db.add(models.TeacherBranch(teacher_id=tt.id, branch_id=bB.id))
db.commit()

gA = models.Group(name="A-guruh", subject="english", level="B1",
                  branch_id=bA.id, teacher_id=tt.id, lesson_time="09:00",
                  monthly_fee=500000, lesson_days="135", capacity=15)
gB = models.Group(name="B-guruh", subject="english", level="B2",
                  branch_id=bB.id, teacher_id=tt.id, lesson_time="14:00",
                  monthly_fee=500000, lesson_days="246", capacity=15)
db.add_all([gA, gB]); db.commit()

# --- Examiner (Filial A da) ---
ue = models.User(username="exam1", full_name="Examiner Bir",
                 password_hash=hash_password("Parol123!"),
                 role=roles.EXAMINER, branch_id=bA.id, is_active=1)
db.add(ue); db.commit()

# --- Ustozning imtihon so'rovi (A filial guruhiga) ---
o = models.ExamOrder(group_id=gA.id, branch_id=bA.id, kind="unit",
                     unit_no=3, date=today + timedelta(days=3),
                     status="new", requested_by=ut.id,
                     public_id="EXO-0001")
db.add(o); db.commit()


def H(u):
    r = client.post("/api/auth/login",
                    json={"username": u, "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


Ht, He = H("ust2f"), H("exam1")


fails = []


def show(name, r, want=200):
    """Kutilgan holat kodini ham tekshiradi."""
    body = ""
    try:
        j = r.json()
        body = j.get("detail") if isinstance(j, dict) else ""
    except Exception:
        pass
    ok = r.status_code == want
    if not ok:
        fails.append(name)
    print(("OK  " if ok else "XATO ") + f"{name}: {r.status_code}"
          + (f"  {body}" if r.status_code >= 400 else "")
          + ("" if ok else f"   (kutilgan {want})"))
    return r


print("=========== 1. IKKI FILIALLI USTOZ ===========")
r = show("GET /me/groups (ikkala filial guruhi ko'rinadimi)",
         client.get("/api/me/groups", headers=Ht))
if r.status_code == 200:
    names = [g["name"] for g in r.json()["rows"]]
    print("     ko'rinayotgan guruhlar:", names)

show(f"GET /groups/{gA.id} (O'Z filiali)",
     client.get(f"/api/groups/{gA.id}", headers=Ht))
show(f"GET /groups/{gB.id} (BOSHQA filial — shu yerda xato bo'lishi kerak)",
     client.get(f"/api/groups/{gB.id}", headers=Ht))
show(f"GET /groups/{gB.id}/attendance (boshqa filial davomati)",
     client.get(f"/api/groups/{gB.id}/attendance?year={today.year}"
                f"&month={today.month}", headers=Ht))

print("\n     _user_branch_ids natijasi:")
from common import _user_branch_ids
fresh = db.query(models.User).get(ut.id)
print("     ->", _user_branch_ids(db, fresh))

print("\n=========== 2. EXAMINER IMTIHON QABUL QILISHI ===========")
show("GET /exam-orders (navbat ro'yxati)",
     client.get("/api/exam-orders", headers=He))
show(f"POST /exam-orders/{o.id}/accept (QABUL QILISH)",
     client.post(f"/api/exam-orders/{o.id}/accept", headers=He, json={}))

db.refresh(o)
print("     buyurtma holati:", o.status, "| exam_id:", o.exam_id)

if o.exam_id:
    show(f"GET /exams/{o.exam_id} (yaratilgan imtihonni ochish)",
         client.get(f"/api/exams/{o.exam_id}", headers=He))
    ex = db.query(models.Exam).get(o.exam_id)
    show(f"PUT /exams/{o.exam_id}/results (natija kiritish)",
         client.put(f"/api/exams/{o.exam_id}/results", headers=He,
                    json={"marks": []}))
    show(f"POST /exam-orders/{o.id}/done (imtihon o'tkazildi)",
         client.post(f"/api/exam-orders/{o.id}/done", headers=He, json={}))

print("\n=========== 3. BOSHQA FILIALDAGI IMTIHON ===========")
o2 = models.ExamOrder(group_id=gB.id, branch_id=bB.id, kind="unit",
                      unit_no=4, date=today + timedelta(days=3),
                      status="new", requested_by=ut.id,
                      public_id="EXO-0002")
db.add(o2); db.commit()
# Bu examiner FAQAT A filialida — B filial imtihonini qabul qila
# OLMASLIGI kerak. Ya'ni tuzatish "hammaga ochib yuborish" emas.
show("BIR filialli examiner boshqa filialga KIRA OLMAYDI",
     client.post(f"/api/exam-orders/{o2.id}/accept", headers=He, json={}),
     want=403)

print("\n=========== 4. IKKI FILIALLI EXAMINER ===========")
db.add(models.UserBranch(user_id=ue.id, branch_id=bB.id))
db.commit()
o3 = models.ExamOrder(group_id=gB.id, branch_id=bB.id, kind="unit",
                      unit_no=5, date=today + timedelta(days=4),
                      status="new", requested_by=ut.id,
                      public_id="EXO-0003")
db.add(o3); db.commit()
He2 = H("exam1")  # yangi token — kesh tozalansin
show(f"POST /exam-orders/{o3.id}/accept (endi ikkinchi filialga ham)",
     client.post(f"/api/exam-orders/{o3.id}/accept", headers=He2, json={}))
db.refresh(o3)
print("     holati:", o3.status)
r = client.get("/api/me", headers=He2)
print("     /api/me branches:", r.json().get("branches"))

print("\n=========== 5. TANLAGICH MA'LUMOTI ===========")
r = client.get("/api/me", headers=Ht)
brs = r.json().get("branches") or []
ok = len(brs) == 2
print(("OK  " if ok else "XATO ") + f"ustozga 2 ta filial qaytadi: {[b['name'] for b in brs]}")
if not ok:
    fails.append("ustoz filiallari")

r = client.get("/api/me", headers=H("exam1"))
brs2 = r.json().get("branches") or []
ok2 = len(brs2) == 2
print(("OK  " if ok2 else "XATO ") + f"examinerga 2 ta filial qaytadi: {[b['name'] for b in brs2]}")
if not ok2:
    fails.append("examiner filiallari")

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
