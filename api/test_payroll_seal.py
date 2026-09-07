# -*- coding: utf-8 -*-
"""OYLIK MUHRI — o'tgan oy raqami muhrlanadi (2026-09-07)

Jahongir: "taklifing menga maqul otgan oy muhransin".

Ilgari oylik hech qayerda saqlanmasdi — sahifa har ochilganda
yo'qlamalardan qayta hisoblanardi. Shuning uchun oy yopilgandan
KEYINGI har qanday o'zgarish (muzlatish, guruhdan chiqarish, dars
yozuvi qo'shilishi) O'TGAN oyning raqamini ham o'zgartirardi.

Endi: tugab bo'lgan oy birinchi ochilishida MUHRLANADI (PayrollSeal)
va shundan keyin o'zgarmaydi. Muhr o'chirilmaydi — faqat asoschi
"qayta hisobla" desa yangilanadi, eski qiymati auditda qoladi.

Test tekshiradi:
  1. tugagan oy ochilganda muhrlanadi;
  2. muhrdan keyin ma'lumot o'zgarsa ham oylik raqami o'zgarmaydi;
  3. ustozning Moliya bo'limi ham muhrlangan raqamni ko'rsatadi;
  4. JORIY oy muhrlanmaydi — u hali davom etyapti;
  5. asoschi qayta hisoblaganda raqam yangilanadi va eski qiymat
     auditga yoziladi; muhr yozuvi o'chirilmaydi (revision oshadi);
  6. asoschidan boshqasi qayta hisoblay olmaydi;
  7. guruh DARS KUNLARI o'zgarishi endi auditga tushadi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/seal_test.db"
if os.path.exists("/tmp/seal_test.db"):
    os.remove("/tmp/seal_test.db")
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
PREV = (CUR - timedelta(days=1)).replace(day=1)
PY, PM = PREV.year, PREV.month
PER = f"{PY:04d}-{PM:02d}"

db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
u_f = models.User(username="asos", password_hash=hash_password("x"),
                  full_name="Asoschi", role=roles.FOUNDER)
u_t = models.User(username="bek", password_hash=hash_password("x"),
                  full_name="Bekzod", role=roles.TEACHER, branch_id=b.id)
db.add_all([u_f, u_t]); db.commit()
t = models.Teacher(full_name="Bekzod", is_active=1, branch_id=b.id,
                   grade="middle", user_id=u_t.id)
db.add(t); db.commit()
g = models.Group(name="IELTS intro", branch_id=b.id, teacher_id=t.id,
                 lesson_days="mon,wed,fri", lesson_price=40_000,
                 standard_lessons_per_month=12, monthly_fee=480_000,
                 rate_manual=1, teacher_rate_per_student=120_000)
db.add(g); db.commit()
S = []
for i in range(5):
    s = models.Student(full_name=f"Bola {i}", branch_id=b.id, status="active",
                       group_id=g.id, enrolled_date=PREV)
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    S.append(s)
db.commit()

# O'tgan oyda 12 dars, hammasi o'tilgan: 12 x 5 x (120000/12) = 600 000
LES = []
d = PREV
while len(LES) < 12:
    if d.weekday() in (0, 2, 4):
        l = models.Lesson(group_id=g.id, date=d, teacher_id=t.id, held=1)
        db.add(l); db.commit()
        for s in S:
            db.add(models.Attendance(student_id=s.id, lesson_id=l.id,
                                     present=1))
        LES.append(l)
    d += timedelta(days=1)
db.commit()

H, HT = tok("asos"), tok("bek")

print("=== 1. Tugagan oy ochilganda MUHRLANADI ===")
ck("muhr hali yo'q", db.query(models.PayrollSeal).count(), 0)
p1 = client.get(f"/api/payroll?year={PY}&month={PM}", headers=H).json()
row1 = [r for r in p1["rows"] if r["teacher_id"] == t.id][0]
ck("oylik 600 000", round(row1["earned"]), 600_000)
ck("muhrlangan deb belgilandi", row1["sealed"], True)
ck("javobda muhr bor", p1["sealed"], True)
db.expire_all()
sl = db.query(models.PayrollSeal).filter_by(period=PER,
                                            teacher_id=t.id).first()
ck("muhr yozuvi yaratildi", sl is not None, True)
ck("muhrdagi summa", round(sl.amount), 600_000)

print()
print("=== 2. Muhrdan keyin ma'lumot o'zgarsa ham raqam o'zgarmaydi ===")
# O'quvchini o'tgan oyning oxirgi 3 darsidan "yo'qotamiz" — ilgari
# oylik shu zahoti kamayardi
for l in LES[-3:]:
    a = db.query(models.Attendance).filter_by(student_id=S[0].id,
                                              lesson_id=l.id).first()
    db.delete(a)
db.commit()
p2 = client.get(f"/api/payroll?year={PY}&month={PM}", headers=H).json()
row2 = [r for r in p2["rows"] if r["teacher_id"] == t.id][0]
ck("oylik O'ZGARMADI", round(row2["earned"]), 600_000)

print()
print("=== 3. Ustozning Moliya bo'limi ham muhrni ko'rsatadi ===")
fin = client.get("/api/my/finance", headers=HT).json()
mm = {x["period"]: x for x in fin["months"]}
ck("o'tgan oy muhrlangan", mm[PER]["sealed"], True)
ck("o'tgan oy summasi muhrdagidek", round(mm[PER]["earned"]), 600_000)

print()
print("=== 4. JORIY oy muhrlanmaydi ===")
pc = client.get(f"/api/payroll?year={CUR.year}&month={CUR.month}",
                headers=H).json()
ck("joriy oy muhrsiz", pc["sealed"], False)
ck("joriy oyda muhr yozuvi yo'q",
   db.query(models.PayrollSeal).filter_by(
       period=f"{CUR.year:04d}-{CUR.month:02d}").count(), 0)

print()
print("=== 5. Asoschi qayta hisoblasa — yangilanadi, eskisi auditda ===")
n_before = db.query(models.PayrollSeal).count()
r = client.post(f"/api/payroll/reseal?year={PY}&month={PM}", headers=H)
ck("qayta hisoblandi", r.status_code, 200)
db.expire_all()
sl2 = db.query(models.PayrollSeal).filter_by(period=PER,
                                             teacher_id=t.id).first()
# 3 ta yo'qlama o'chgan edi: 57 x 10 000 = 570 000
ck("yangi summa", round(sl2.amount), 570_000)
ck("muhr yozuvi o'chirilmadi", db.query(models.PayrollSeal).count(),
   n_before)
ck("revision oshdi", sl2.revision, 2)
au = (db.query(models.AuditLog)
      .filter(models.AuditLog.field == f"oylik muhri {PER}").first())
ck("auditga yozildi", au is not None, True)
ck("eski qiymat auditda", round(float(au.old_value)), 600_000)
ck("yangi qiymat auditda", round(float(au.new_value)), 570_000)

print()
print("=== 6. Asoschidan boshqasi qayta hisoblay olmaydi ===")
r = client.post(f"/api/payroll/reseal?year={PY}&month={PM}", headers=HT)
ck("ustozga yopiq", r.status_code, 403)
r = client.post(f"/api/payroll/reseal?year={CUR.year}&month={CUR.month}",
                headers=H)
ck("joriy oyni muhrlab bo'lmaydi", r.status_code, 400)

print()
print("=== 7. Guruh DARS KUNLARI o'zgarishi auditga tushadi ===")
r = client.put(f"/api/groups/{g.id}", headers=H,
               json={"lesson_days": "tue,thu,sat"})
ck("saqlandi", r.status_code, 200)
au2 = (db.query(models.AuditLog)
       .filter(models.AuditLog.entity == "group",
               models.AuditLog.field == "lesson_days").first())
ck("audit yozuvi bor", au2 is not None, True)
ck("eskisi", au2.old_value, "mon,wed,fri")
ck("yangisi", au2.new_value, "tue,thu,sat")

print()
print("XULOSA: " + ("HAMMASI O'TDI" if not fails
                    else f"{len(fails)} ta xato: {fails}"))
sys.exit(1 if fails else 0)
