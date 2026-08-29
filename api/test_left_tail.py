# -*- coding: utf-8 -*-
"""KETGANNING DUMI: oxirgi kelgan darsdan keyingi yo'qlama (2026-08-29).

Jahongir: "chiqib ketgan kunida oxirida masalan Mahbubahon turibdi
oxirgi 2ta dars kelmagan va chiqib ketgan, shu kelmagan darsini
ayirib tashlash kerak, yo'qlamasi yo'qolishi kerak, chunki u chiqib
ketgan USTOZGA OYLIK YOZILISHI KERAK EMAS, avtomat yo'q bo'lishi
kerak. Admin noto'g'ri kundan chiqarvorgan bo'lsa ham ENG OXIRGI
KELGAN DARSIGACHA pul hisoblanishi, undan keyin 1ta kelmaydimi 2ta
kelmaydimi olib tashlanishi kerak"

ENG MUHIM XAVF: FAOL o'quvchiga ham tegib ketish. Hozir o'qiyotgan
bola oxirgi 2 darsga kelmasa, u BARIBIR to'laydi va ustoz haqini
oladi. Test buni alohida tekshiradi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_tail/db.sqlite"
os.makedirs("/tmp/verify_tail", exist_ok=True)
if os.path.exists("/tmp/verify_tail/db.sqlite"):
    os.remove("/tmp/verify_tail/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date                             # noqa: E402
import billing, models, roles                         # noqa: E402
import common                                         # noqa: E402
from database import SessionLocal, engine             # noqa: E402

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


NARX = 40_000.0
b = models.Branch(name="Bekobod 2")
db.add(b); db.commit()
db.add(models.TeacherGrade(key="middle", label="Middle",
                           rate_per_student=100_000))
db.commit()
t = models.Teacher(full_name="Elena", is_active=1, branch_id=b.id,
                   grade="middle")
db.add(t); db.commit()
g = models.Group(name="Step 1", branch_id=b.id, teacher_id=t.id,
                 lesson_price=NARX, standard_lessons_per_month=12,
                 monthly_fee=NARX * 12)
db.add(g); db.commit()

# 5 ta dars: 12, 13, 15, 18, 20 avgust (skrinshotdagidek)
KUNLAR = [date(2026, 8, d) for d in (12, 13, 15, 18, 20)]
lessons = []
for d in KUNLAR:
    l = models.Lesson(group_id=g.id, date=d, teacher_id=t.id, held=1)
    db.add(l); lessons.append(l)
db.commit()


def bola(nom, status, keldi, link_active=1):
    """keldi — qaysi kunlarda kelgan (indekslar). Qolganida kelmagan."""
    s = models.Student(full_name=nom, group_id=g.id, branch_id=b.id,
                       status=status, enrolled_date=date(2026, 8, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=link_active))
    for i, l in enumerate(lessons):
        db.add(models.Attendance(student_id=s.id, lesson_id=l.id,
                                 present=1 if i in keldi else 0))
    db.commit()
    return s


# Skrinshotdagi holat: 12,13,15 keldi -> 18,20 kelmadi -> CHIQIB KETDI
mahbuba = bola("Yakubova Mahbubahon", "archived", {0, 1, 2})
# Muzlatilgan: 12 kelmadi, 13 keldi -> keyin muzlatildi
kumush = bola("Abdusattarova Kumush", "frozen", {1})
# FAOL o'quvchi — oxirgi 2 darsga kelmagan, lekin O'QIYAPTI
sabrina = bola("Abdurayimova Sabrina", "active", {0, 1, 2})
# Faol va hammasiga kelgan
nozima = bola("Rahmatova Nozima", "active", {0, 1, 2, 3, 4})
db.commit()


# =====================================================================
print("=== 1. CHEGARA SANASI ===")
# =====================================================================
cut = billing.attendance_cutoff(db, [mahbuba.id, kumush.id, sabrina.id,
                                     nozima.id], g.id)
ck("ketgan bolada chegara bor", cut.get(mahbuba.id), date(2026, 8, 15))
ck("  = OXIRGI KELGAN dars", cut.get(mahbuba.id), KUNLAR[2])
ck("muzlatilganda ham chegara bor", cut.get(kumush.id), date(2026, 8, 13))
ck("FAOL o'quvchiga chegara YO'Q", cut.get(sabrina.id), None)
ck("  hammasiga kelganda ham yo'q", cut.get(nozima.id), None)


# =====================================================================
print("\n=== 2. USTOZ OYLIGI: dum sanalmaydi ===")
# =====================================================================
n = billing.countable_attendance(db, lessons, g.id)
ck("12-avg: 4 ta (hammasi)", n[lessons[0].id], 4)
ck("13-avg: 4 ta", n[lessons[1].id], 4)
ck("15-avg: 3 ta (Kumush muzlagan)", n[lessons[2].id], 3)
ck("18-avg: 2 ta (Mahbuba va Kumush chiqdi)", n[lessons[3].id], 2)
ck("  Sabrina KELMAGAN bo'lsa ham sanaldi", n[lessons[3].id] >= 2, True)
ck("20-avg: 2 ta", n[lessons[4].id], 2)

pay = billing.compute_teacher_payroll(db, g, 2026, 8)
ck("ustoz qatori bor", len(pay), 1)
jami = pay[0]["attendances"]
ck("sanaladigan yo'qlama jami 15 ta", jami, 4 + 4 + 3 + 2 + 2)
ck("  20 ta EMAS (5 dars x 4 bola)", jami != 20, True)
ck("stavka noldan katta (pul haqiqatan tekshirilyapti)",
   pay[0]["rate"] > 0, True)
ck("oylik summasi sanalgan yo'qlamaga mos",
   round(pay[0]["amount"]), round(jami * pay[0]["rate"]))
# ENG MUHIM RAQAM: kesilmaganda ustoz 20 ta uchun olardi.
ck("  ustoz 5 ta ORTIQCHA yo'qlama uchun pul OLMADI",
   round(pay[0]["amount"]) < round(20 * pay[0]["rate"]), True)
ck("  farq aynan 5 ta yo'qlama",
   round(20 * pay[0]["rate"] - pay[0]["amount"]),
   round(5 * pay[0]["rate"]))


# =====================================================================
print("\n=== 3. O'QUVCHI HISOBI: dumga pul yozilmaydi ===")
# =====================================================================
ck("Mahbuba 3 darsga to'laydi (5 emas)",
   billing.billable_lessons_for_student(db, mahbuba, g, 2026, 8), 3)
ck("Kumush 2 darsga",
   billing.billable_lessons_for_student(db, kumush, g, 2026, 8), 2)
ck("FAOL Sabrina 5 darsga (kelmasa ham to'laydi)",
   billing.billable_lessons_for_student(db, sabrina, g, 2026, 8), 5)
ck("Nozima 5 darsga",
   billing.billable_lessons_for_student(db, nozima, g, 2026, 8), 5)


# =====================================================================
print("\n=== 4. ADMIN NOTO'G'RI SANA QO'YSA HAM ===")
# =====================================================================
# Jahongir: "admin noto'g'ri kundan chiqarvorgan bo'lsa ham eng
# oxirgi kelgan darsigacha pul hisoblanishi". Ketish sanasi 20-avgust
# qilib qo'yilsa ham, hisob 15-avgustda to'xtaydi.
mahbuba.left_date = date(2026, 8, 20)
db.commit()
ck("ketish sanasi 20-avg qilib qo'yildi", mahbuba.left_date,
   date(2026, 8, 20))
ck("  lekin chegara baribir 15-avg",
   billing.attendance_cutoff(db, [mahbuba.id], g.id)[mahbuba.id],
   date(2026, 8, 15))
ck("  pul ham 3 darsga",
   billing.billable_lessons_for_student(db, mahbuba, g, 2026, 8), 3)

# Teskarisi: sana juda erta qo'yilsa ham FAKT ustun
mahbuba.left_date = date(2026, 8, 1)
db.commit()
ck("sana 1-avg bo'lsa ham 3 dars sanaladi",
   billing.billable_lessons_for_student(db, mahbuba, g, 2026, 8), 3)


# =====================================================================
print("\n=== 5. BOSHQA GURUHGA O'TGAN ===")
# =====================================================================
# Statusi FAOL, lekin shu guruhdan chiqarilgan (link active=0).
g2 = models.Group(name="Step 2", branch_id=b.id, teacher_id=t.id,
                  lesson_price=NARX, standard_lessons_per_month=12)
db.add(g2); db.commit()
otgan = bola("O'tgan Bola", "active", {0, 1}, link_active=0)
otgan.group_id = g2.id
db.commit()
c2 = billing.attendance_cutoff(db, [otgan.id], g.id)
ck("boshqa guruhga o'tganda ham chegara qo'yiladi",
   c2.get(otgan.id), date(2026, 8, 13))
n2 = billing.countable_attendance(db, lessons, g.id)
ck("  15-avg da u sanalmaydi", n2[lessons[2].id], 3)
ck("  12-avg da esa sanaladi", n2[lessons[0].id], 5)


# =====================================================================
print("\n=== 6. UMUMAN KELMAGAN BOLA ===")
# =====================================================================
hech = bola("Hech Kelmagan", "archived", set())
c3 = billing.attendance_cutoff(db, [hech.id], g.id)
ck("chegara eng eski sana", c3.get(hech.id), date(1900, 1, 1))
ck("  pul umuman yozilmaydi",
   billing.billable_lessons_for_student(db, hech, g, 2026, 8), 0)
n3 = billing.countable_attendance(db, lessons, g.id)
ck("  ustozga ham qo'shilmaydi", n3[lessons[0].id], 5)


# =====================================================================
print("\n=== 7. HECH NARSA O'CHIRILMADI ===")
# =====================================================================
ck("yo'qlama yozuvlari joyida",
   db.query(models.Attendance).count(), 5 * 6)
ck("  Mahbubaning 5 tasi ham turibdi",
   db.query(models.Attendance).filter(
       models.Attendance.student_id == mahbuba.id).count(), 5)
ck("o'quvchilar joyida", db.query(models.Student).count(), 6)


print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
