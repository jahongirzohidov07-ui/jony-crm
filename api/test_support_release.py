"""SUPPORT BO'SHATILGANDA GURUHLARI BO'SHASIN (2026-08-10).

Jahongir: "support bo'shatilgandan keyin avtomatik guruhlari bo'sh
qolsin. Masalan Malikani akkauntiga kirmay qolgan edi, boshidan
o'chirib tashlaganman, lekin haliyam support teacher Malika bo'lib
turibdi. Support bo'shatilganda gruppada ham avtomat bo'sh qolsin va
support managerga task kelsin - shu guruhlar supportsiz qoldi deb."

Eng muhim tekshiruv oxirida: FAOL supportning biriktirishlariga
tegilmasligi. Aks holda tozalash kodi ishlayotgan supportlarni ham
guruhlardan uzib yuborishi mumkin edi."""
import os, sys
from datetime import date

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_support_release/db.sqlite"
os.makedirs("/tmp/verify_support_release", exist_ok=True)
if os.path.exists("/tmp/verify_support_release/db.sqlite"):
    os.remove("/tmp/verify_support_release/db.sqlite")
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


b = models.Branch(name="Zafar")
db.add(b); db.commit()


def mk(u, name, role):
    x = models.User(username=u, full_name=name,
                    password_hash=hash_password("Parol123!"),
                    role=role, branch_id=b.id, is_active=1)
    db.add(x); db.commit(); return x


hr = mk("hr", "HR Menejer", roles.HR_MANAGER)
head = mk("hs", "Support Boshlig'i", roles.HEAD_SUPPORT)
malika = mk("malika", "Malika Yusupova", roles.SUPPORT_TEACHER)
ust = mk("ust", "Ustoz", roles.TEACHER)
t = models.Teacher(full_name="Ustoz", branch_id=b.id, user_id=ust.id,
                   is_active=1)
db.add(t); db.commit()

gs = []
for i, nm in enumerate(("IELTS-1", "IELTS-2", "CEFR-1")):
    g = models.Group(name=nm, subject="english", level="step1",
                     branch_id=b.id, teacher_id=t.id,
                     lesson_time=f"0{8+i}:00", monthly_fee=500000,
                     lesson_days="mon,wed,fri", capacity=15)
    db.add(g); db.commit(); gs.append(g)
    db.add(models.SupportAssignment(user_id=malika.id, group_id=g.id))
db.commit()


def H(u):
    r = c.post("/api/auth/login", json={"username": u,
                                        "password": "Parol123!"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


Hhr = H("hr")

print("=== BOSHIDA: MALIKA 3 TA GURUHDA ===")
ck("3 ta biriktirish bor",
   db.query(models.SupportAssignment).filter(
       models.SupportAssignment.user_id == malika.id).count(), 3)
sup = {g["name"]: g.get("support_label")
       for g in c.get("/api/groups", headers=Hhr).json()}
ck("guruhda support ko'rinadi", sup.get("IELTS-1"), "Malika Yusupova")

print("\n=== MALIKA ISHDAN BO'SHATILDI ===")
r = c.put(f"/api/users/{malika.id}", headers=Hhr, json={"is_active": False})
ck("bo'shatildi", r.status_code, 200)
ck("BIRIKTIRISHLAR AVTOMAT O'CHDI",
   db.query(models.SupportAssignment).filter(
       models.SupportAssignment.user_id == malika.id).count(), 0)
sup2 = {g["name"]: g.get("support_label")
        for g in c.get("/api/groups", headers=Hhr).json()}
ck("guruhda support endi bo'sh", sup2.get("IELTS-1") or None, None)

print("\n=== SUPPORT BOSHLIG'IGA VAZIFA KELDI ===")
tasks = db.query(models.Task).filter(
    models.Task.assignee_id == head.id).all()
ck("vazifa yaratildi", len(tasks) >= 1, True)
if tasks:
    tk = tasks[0]
    ck("sarlavhada ismi bor", "Malika" in tk.title, True)
    ck("uchala guruh sanab o'tilgan",
       all(n in (tk.description or "")
           for n in ("IELTS-1", "IELTS-2", "CEFR-1")), True)
    ck("sababi yozilgan", "bo'shatildi" in (tk.description or ""), True)

print("\n=== ROL O'ZGARSA HAM BO'SHAYDI ===")
aziza = mk("aziza", "Aziza Karimova", roles.SUPPORT_TEACHER)
db.add(models.SupportAssignment(user_id=aziza.id, group_id=gs[0].id))
db.commit()
r = c.put(f"/api/users/{aziza.id}", headers=Hhr,
          json={"role": roles.TEACHER})
ck("roli o'zgartirildi", r.status_code, 200)
ck("biriktirish ham o'chdi",
   db.query(models.SupportAssignment).filter(
       models.SupportAssignment.user_id == aziza.id).count(), 0)

print("\n=== FAOL SUPPORTGA TEGILMAYDI ===")
nodira = mk("nodira", "Nodira Soliyeva", roles.SUPPORT_TEACHER)
db.add(models.SupportAssignment(user_id=nodira.id, group_id=gs[1].id))
db.commit()
c.put(f"/api/users/{nodira.id}", headers=Hhr, json={"phone": "998900000000"})
ck("oddiy tahrirlashda biriktirish qoladi",
   db.query(models.SupportAssignment).filter(
       models.SupportAssignment.user_id == nodira.id).count(), 1)
sup3 = {g["name"]: g.get("support_label")
        for g in c.get("/api/groups", headers=Hhr).json()}
ck("faol support guruhda ko'rinadi", sup3.get("IELTS-2"),
   "Nodira Soliyeva")

print("\n=== ESKI (QOLIB KETGAN) YOZUVLARNI TOZALASH ===")
from common import _cleanup_stale_support_assignments
db.add(models.SupportAssignment(user_id=malika.id, group_id=gs[2].id))
db.commit()
n = _cleanup_stale_support_assignments(db)
ck("tozalash eski yozuvni topdi", n >= 1, True)
ck("bo'shatilgan xodim yozuvi qolmadi",
   db.query(models.SupportAssignment).filter(
       models.SupportAssignment.user_id == malika.id).count(), 0)
ck("FAOL supportniki TEGILMADI",
   db.query(models.SupportAssignment).filter(
       models.SupportAssignment.user_id == nodira.id).count(), 1)
ck("tozalanadigan narsa qolmadi",
   _cleanup_stale_support_assignments(db), 0)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
