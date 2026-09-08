# -*- coding: utf-8 -*-
"""GURUHNI O'CHIRISH — "ichidagi o'quvchini o'chirsam ham ochmayabdi"

2026-09-08, Jahongir: "ichidagi o'quvchini ochirib tashlasayam
ochmayabdi" (ekranda: "Guruhda 10 ta o'quvchi bor. Avval ularni
boshqa guruhga ko'chiring yoki arxivlang").

SABAB: guruhlar ro'yxatidagi qavs ichidagi son FAQAT FAOL
o'quvchilarni sanardi, o'chirish tekshiruvi esa HAMMASINI —
muzlatilgan va arxivdagilarni ham. Guruh "[0]" ko'rinib turib
"10 ta o'quvchi bor" deb rad etardi va ularni ko'rish ham,
chiqarish ham imkonsiz edi. Jonli bazada 5 ta shunday guruh bor
edi (Madrid 15, Успешньй 15, Prime 3, Rangers 3, Yangi 1 —
hammasi muzlatilgan).

Test tekshiradi:
  1. muzlatilgan o'quvchi guruhlar ro'yxatida ALOHIDA ko'rinadi
     (frozen_count);
  2. muzlatilgan o'quvchi bo'lsa — o'chirilmaydi, lekin xabarda
     qaysi holatda nechtaligi aniq yoziladi;
  3. ARXIVdagi o'quvchi to'smaydi: guruh o'chadi, o'quvchi
     O'CHIRILMAYDI — guruhdan uziladi va auditga yoziladi;
  4. imtihon kabi tarix yozuvi bo'lsa — o'chirilmaydi, nima
     to'sib turgani aytiladi (500 emas, tushunarli xabar);
  5. bo'sh guruh avvalgidek o'chadi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/gdel_test.db"
if os.path.exists("/tmp/gdel_test.db"):
    os.remove("/tmp/gdel_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date                            # noqa: E402
from fastapi.testclient import TestClient            # noqa: E402
import main, models, roles                           # noqa: E402
import entry                                         # noqa: E402,F401
from database import SessionLocal                    # noqa: E402
from auth import hash_password                       # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role=roles.FOUNDER))
db.commit()
t = models.Teacher(full_name="Ustoz", is_active=1, branch_id=b.id)
db.add(t); db.commit()


def yangi_guruh(nom):
    g = models.Group(name=nom, branch_id=b.id, teacher_id=t.id,
                     lesson_days="mon,wed,fri", lesson_price=40_000,
                     standard_lessons_per_month=12, monthly_fee=480_000)
    db.add(g); db.commit()
    return g


def bola(nom, g, status):
    s = models.Student(full_name=nom, branch_id=b.id, status=status,
                       group_id=g.id, enrolled_date=date(2026, 8, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    db.commit()
    return s


g_frozen = yangi_guruh("Madrid")
for i in range(3):
    bola(f"Muzlatilgan {i}", g_frozen, "frozen")
g_arch = yangi_guruh("Prime")
arx = [bola(f"Arxiv {i}", g_arch, "archived") for i in range(2)]
g_exam = yangi_guruh("Rangers")
db.add(models.Exam(group_id=g_exam.id, kind="unit", unit_no=1,
                   title="Unit 1", date=date(2026, 8, 10), max_score=100))
db.commit()
g_empty = yangi_guruh("Bo'sh")
GID_FROZEN, GID_ARCH = g_frozen.id, g_arch.id
GID_EXAM, GID_EMPTY = g_exam.id, g_empty.id
ARX_ID = [x.id for x in arx]

H = tok("asos")

print("=== 1. Muzlatilganlar ro'yxatda alohida ko'rinadi ===")
gl = client.get("/api/groups", headers=H).json()
by = {x["name"]: x for x in gl}
ck("Madrid faol soni 0", by["Madrid"]["student_count"], 0)
ck("Madrid muzlatilgan 3", by["Madrid"]["frozen_count"], 3)
ck("Bo'sh guruhda 0", by["Bo'sh"]["frozen_count"], 0)

print()
print("=== 2. Muzlatilgan bo'lsa — o'chirilmaydi, sabab aniq ===")
r = client.delete(f"/api/groups/{GID_FROZEN}", headers=H)
ck("rad etildi", r.status_code, 400)
msg = r.json()["detail"]
ck("xabarda 3 ta deyilgan", "3 ta o'quvchi" in msg, True)
ck("xabarda 'muzlatilgan' bor", "muzlatilgan" in msg, True)
db.expire_all()
ck("guruh joyida", db.query(models.Group).filter_by(id=GID_FROZEN).count(), 1)

print()
print("=== 3. Arxivdagilar to'smaydi — guruh o'chadi, bola qoladi ===")
n_before = db.query(models.Student).count()
r = client.delete(f"/api/groups/{GID_ARCH}", headers=H)
ck("o'chirildi", r.status_code, 200)
db.expire_all()
ck("guruh yo'q", db.query(models.Group).filter_by(id=GID_ARCH).count(), 0)
ck("o'quvchilar soni o'zgarmadi", db.query(models.Student).count(), n_before)
db.expire_all()
ck("guruhdan uzildi",
   [db.query(models.Student).get(i).group_id for i in ARX_ID], [None, None])
ck("bog'lanish ham tozalandi",
   db.query(models.StudentGroupLink).filter_by(group_id=GID_ARCH).count(), 0)
au = (db.query(models.AuditLog)
      .filter(models.AuditLog.action == "group_remove").count())
ck("auditga yozildi (2 ta)", au, 2)

print()
print("=== 4. Imtihon tarixi bo'lsa — tushunarli xabar (500 emas) ===")
r = client.delete(f"/api/groups/{GID_EXAM}", headers=H)
ck("rad etildi", r.status_code, 400)
ck("nima to'sayotgani aytilgan", "imtihon" in r.json()["detail"], True)
db.expire_all()
ck("guruh joyida", db.query(models.Group).filter_by(id=GID_EXAM).count(), 1)

print()
print("=== 5. Bo'sh guruh avvalgidek o'chadi ===")
r = client.delete(f"/api/groups/{GID_EMPTY}", headers=H)
ck("o'chirildi", r.status_code, 200)
db.expire_all()
ck("guruh yo'q", db.query(models.Group).filter_by(id=GID_EMPTY).count(), 0)

print()
print("XULOSA: " + ("HAMMASI O'TDI" if not fails
                    else f"{len(fails)} ta xato: {fails}"))
sys.exit(1 if fails else 0)
