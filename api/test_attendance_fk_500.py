# -*- coding: utf-8 -*-
"""USTOZ YO'QLAMA QO'YA OLMAYAPTI: davomat jadvali 500 berardi (2026-09-07)

Jahongir: "ustoz aytyabdi yoqlama qoyib bolmayabdi deb nega bunaqa
bolyabdi" (ustoz telefonida "Tarmoq bilan bog'lanib bo'lmadi").

Sabab jonli xatolar jurnalidan topildi:
    ForeignKeyViolation ... "xp_transactions_lesson_id_fkey"
    ForeignKeyViolation ... "lesson_reschedules_lesson_id_fkey"
Jadval sinxronlanganda "jadvalga mos kelmaydi" degan BO'SH darsni
o'chirishga urinilardi, lekin darsga XP yozuvi yoki boshqa guruhning
ko'chirish yozuvi bog'langan bo'lsa Postgres rad etardi va butun
/api/groups/{id}/attendance 500 bilan yiqilardi.

Test tekshiradi:
  1. XP yozuvi bog'langan bo'sh dars — jadval 200 qaytaradi, dars
     joyida qoladi (avval 500 edi);
  2. BOSHQA guruhning ko'chirish yozuvi bog'langan dars ham xuddi
     shunday — 500 yo'q, dars o'chirilmaydi;
  3. yo'qlama qo'yish ishlaydi;
  4. hech qanday bog'lanishi yo'q, jadvalga mos kelmaydigan bo'sh
     dars avvalgidek tozalanadi (xatti-harakat o'zgarmagan).
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/attfk_test.db"
if os.path.exists("/tmp/attfk_test.db"):
    os.remove("/tmp/attfk_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                 # noqa: E402
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


TODAY = roles.local_today()
CUR = date(TODAY.year, TODAY.month, 1)

db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
u_f = models.User(username="asos", password_hash=hash_password("x"),
                  full_name="Asoschi", role=roles.FOUNDER)
u_t = models.User(username="umida", password_hash=hash_password("x"),
                  full_name="Umida", role=roles.TEACHER, branch_id=b.id)
db.add_all([u_f, u_t]); db.commit()
t = models.Teacher(full_name="Umida", is_active=1, branch_id=b.id,
                   grade="middle", user_id=u_t.id)
db.add(t); db.commit()
# Jadval: DUSHANBA/CHORSHANBA/JUMA
g = models.Group(name="Texas", branch_id=b.id, teacher_id=t.id,
                 lesson_days="mon,wed,fri", lesson_price=40_000,
                 standard_lessons_per_month=12, monthly_fee=480_000)
g2 = models.Group(name="Boshqa guruh", branch_id=b.id, teacher_id=t.id,
                  lesson_days="mon,wed,fri")
db.add_all([g, g2]); db.commit()
s1 = models.Student(full_name="Bola 1", branch_id=b.id, status="active",
                    group_id=g.id, enrolled_date=CUR)
db.add(s1); db.commit()
db.add(models.StudentGroupLink(student_id=s1.id, group_id=g.id,
                               is_primary=1, active=1))
db.commit()


def _sunday_in_month():
    d = CUR
    while d.weekday() != 6:            # YAKSHANBA — jadvalda yo'q
        d += timedelta(days=1)
    return d


H, HT = tok("asos"), tok("umida")
URL = f"/api/groups/{g.id}/attendance?year={CUR.year}&month={CUR.month}"

print("=== 1. XP yozuvi bog'langan bo'sh dars ===")
d1 = _sunday_in_month()
l1 = models.Lesson(group_id=g.id, date=d1, teacher_id=t.id, held=0)
db.add(l1); db.commit()
db.add(models.XpTransaction(student_id=s1.id, amount=10, lesson_id=l1.id,
                            group_id=g.id, branch_id=b.id))
db.commit()
r = client.get(URL, headers=HT)
ck("jadval ochildi (avval 500 edi)", r.status_code, 200)
db.expire_all()
ck("dars o'chirilmadi",
   db.query(models.Lesson).filter_by(id=l1.id).count(), 1)

print()
print("=== 2. BOSHQA guruhning ko'chirish yozuvi bog'langan dars ===")
d2 = d1 + timedelta(days=7)
l2 = models.Lesson(group_id=g.id, date=d2, teacher_id=t.id, held=0)
db.add(l2); db.commit()
db.add(models.LessonReschedule(group_id=g2.id, lesson_id=l2.id,
                               from_date=d2, to_date=d2 + timedelta(days=1),
                               status="approved"))
db.commit()
r = client.get(URL, headers=HT)
ck("jadval ochildi", r.status_code, 200)
db.expire_all()
ck("dars o'chirilmadi",
   db.query(models.Lesson).filter_by(id=l2.id).count(), 1)

print()
print("=== 3. Yo'qlama qo'yish ishlaydi ===")
today_les = (db.query(models.Lesson)
             .filter(models.Lesson.group_id == g.id,
                     models.Lesson.date == TODAY).first())
if today_les is None:
    today_les = models.Lesson(group_id=g.id, date=TODAY, teacher_id=t.id,
                              held=0)
    db.add(today_les); db.commit()
r = client.put(f"/api/lessons/{today_les.id}/attendance", headers=HT,
               json={"marks": [{"student_id": s1.id, "present": True}]})
ck("yo'qlama saqlandi", r.status_code, 200)
db.expire_all()
ck("yozuv bazada", db.query(models.Attendance)
   .filter_by(lesson_id=today_les.id, student_id=s1.id).count(), 1)

print()
print("=== 4. Bog'lanishi yo'q, mos kelmaydigan bo'sh dars — tozalanadi ===")
d4 = d1 + timedelta(days=14)
l4 = models.Lesson(group_id=g.id, date=d4, teacher_id=t.id, held=0)
db.add(l4); db.commit()
lid4 = l4.id
r = client.get(URL, headers=HT)
ck("jadval ochildi", r.status_code, 200)
db.expire_all()
ck("bo'sh dars tozalandi (eski xatti-harakat)",
   db.query(models.Lesson).filter_by(id=lid4).count(), 0)

print()
print("XULOSA: " + ("HAMMASI O'TDI" if not fails
                    else f"{len(fails)} ta xato: {fails}"))
sys.exit(1 if fails else 0)
