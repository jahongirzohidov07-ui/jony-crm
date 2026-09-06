# -*- coding: utf-8 -*-
"""YAXLITLIK VA IZ (2026-09-06, "togrla hamma aytganingni").

Auditda topilganlar:
  1. xodim hisobi bo'shatilsa ustoz kartasi faol qolaverardi
     (va aksincha) — Dostonbek holati aynan shundan;
  2. guruh narxi / ustoz stavkasi tahriri auditga yozilmasdi;
  3. qo'lda coin berish/yechish auditga yozilmasdi;
  4. narx qulfi boshqa narxli guruhga o'tganda ham saqlanib qolardi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/integrity.db"
if os.path.exists("/tmp/integrity.db"):
    os.remove("/tmp/integrity.db")
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
tu = models.User(username="ustoz", password_hash=hash_password("x"),
                 full_name="Ustoz Aka", role=roles.TEACHER, branch_id=b.id)
db.add(tu); db.commit()
t = models.Teacher(full_name="Ustoz Aka", is_active=1, branch_id=b.id,
                   user_id=tu.id)
db.add(t); db.commit()
A = tok("asos")

print("=== 1. Hisob ↔ ustoz kartasi sinxron ===")
r = client.put(f"/api/users/{tu.id}", json={"is_active": False}, headers=A)
ck("bo'shatish 200", r.status_code, 200)
db.expire_all()
ck("ustoz kartasi ham yopildi",
   db.query(models.Teacher).get(t.id).is_active, 0)
ck("ketgan sanasi qo'yildi",
   db.query(models.Teacher).get(t.id).left_date is not None, True)
r = client.put(f"/api/users/{tu.id}", json={"is_active": True}, headers=A)
db.expire_all()
ck("qaytarilsa karta ham ochildi",
   db.query(models.Teacher).get(t.id).is_active, 1)
ck("ketgan sanasi tozalandi",
   db.query(models.Teacher).get(t.id).left_date, None)

print("\n=== 2. Guruh narxi / stavka auditga tushadi ===")
g1 = models.Group(name="Eski narx", branch_id=b.id, teacher_id=t.id,
                  lesson_price=40_000, standard_lessons_per_month=12,
                  monthly_fee=480_000)
g2 = models.Group(name="Yangi narx", branch_id=b.id, teacher_id=t.id,
                  lesson_price=45_000, standard_lessons_per_month=12,
                  monthly_fee=540_000)
db.add_all([g1, g2]); db.commit()
G1, G2 = g1.id, g2.id
before = db.query(models.AuditLog).filter(
    models.AuditLog.entity == "group").count()
r = client.put(f"/api/groups/{G1}",
               json={"lesson_price": 50_000,
                     "teacher_rate_per_student": 130_000}, headers=A)
ck("guruh tahriri 200", r.status_code, 200)
rows = (db.query(models.AuditLog)
        .filter(models.AuditLog.entity == "group",
                models.AuditLog.entity_id == G1).all())
flds = sorted({x.field for x in rows})
ck("narx va stavka auditda", flds, ["lesson_price", "teacher_rate_per_student"])
ck("eski qiymat saqlangan",
   str([x.old_value for x in rows if x.field == "lesson_price"][0]).split(".")[0],
   "40000")

print("\n=== 3. Qo'lda coin auditga tushadi ===")
s = models.Student(full_name="Bola", branch_id=b.id, status="active",
                   group_id=G1, enrolled_date=date(2026, 6, 1))
db.add(s); db.commit()
S = s.id
r = client.post(f"/api/students/{S}/coins",
                json={"amount": 15, "note": "tanlov"}, headers=A)
ck("coin berish 200", r.status_code, 200)
ck("auditda coin yozuvi bor",
   db.query(models.AuditLog).filter(models.AuditLog.field == "coin").count(), 1)

print("\n=== 4. Narx qulfi guruh almashganda qayta ko'riladi ===")
s.locked_lesson_price = 40_000
db.commit()
r = client.post(f"/api/students/{S}/move-group", json={"group_id": G2},
                headers=A)
ck("ko'chirish 200", r.status_code, 200)
db.expire_all()
ck("boshqa narxli guruhga o'tdi — qulf olindi",
   db.query(models.Student).get(S).locked_lesson_price, None)
ck("audit yozuvi bor",
   db.query(models.AuditLog).filter(
       models.AuditLog.field == "locked_lesson_price").count() >= 1, True)
# Bir xil narxli guruhga o'tsa qulf QOLADI
g3 = models.Group(name="Xuddi shu narx", branch_id=b.id, teacher_id=t.id,
                  lesson_price=45_000, standard_lessons_per_month=12,
                  monthly_fee=540_000)
db.add(g3); db.commit()
st = db.query(models.Student).get(S)
st.locked_lesson_price = 45_000
db.commit()
client.post(f"/api/students/{S}/move-group", json={"group_id": g3.id},
            headers=A)
db.expire_all()
ck("bir xil narxda qulf saqlandi",
   db.query(models.Student).get(S).locked_lesson_price, 45_000)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
