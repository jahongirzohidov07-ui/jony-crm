# -*- coding: utf-8 -*-
"""YOPILGAN OYGA YANGI DARS YARATILMASIN (2026-09-07)

Jahongir: "31-avgust men oyliklarni screenshot qilib oldim va oyliklarni
tolagani moliyachiga berdim, lekin bugun kirib qarasam avgust oyliklari
kamayib qolgan masalan bekzod akaniki 2mlncha, shirinabonuniki 1,5 mln
atrofida kamaygan nega bunday bo'ldi".

SABAB: davomat jadvali ochilganda _sync_scheduled_lessons() guruhning
lesson_days'i bo'yicha O'SHA OYNING yetishmayotgan kunlarini yaratardi —
o'tgan oy uchun ham. Bo'sh dars pulga kirmaydi, lekin OYLIK
BO'LUVCHISIGA kiradi (billing.month_divisor bekor qilinmagan barcha
dars yozuvlarini sanaydi). Ya'ni sentabrda avgust jadvalini ochish
avgust oyligini kamaytirardi:
    160 000 / 13 = 12 308  ->  160 000 / 25 = 6 400

Test tekshiradi:
  1. TUGAB BO'LGAN oyning jadvalini ochish yangi dars YARATMAYDI —
     dars soni ham, oylik ham o'zgarmaydi (asosiy tuzatish);
  2. JORIY oyda jadval avvalgidek ishlaydi (yangi kunlar yaratiladi);
  3. mavjud bo'sh yozuvlar (tuzatishdan oldin paydo bo'lganlari)
     hech qayerga yo'qolmaydi, lekin diagnostika ularni sanab
     ko'rsatadi: empty_lesson_rows, divisor_if_real, gain_if_fixed.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/pastles_test.db"
if os.path.exists("/tmp/pastles_test.db"):
    os.remove("/tmp/pastles_test.db")
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
PREV = (CUR - timedelta(days=1)).replace(day=1)      # tugab bo'lgan oy

db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
u_f = models.User(username="asos", password_hash=hash_password("x"),
                  full_name="Asoschi", role=roles.FOUNDER)
db.add(u_f); db.commit()
t = models.Teacher(full_name="Bekzod", is_active=1, branch_id=b.id,
                   grade="middle")
db.add(t); db.commit()
# Jadval: du/chor/juma. Lekin o'tgan oyda darslar SE/PA/SHA da o'tilgan
# (jadval keyin o'zgargan) — aynan shu holat avgustda bo'lgan.
g = models.Group(name="IELTS 1.0", branch_id=b.id, teacher_id=t.id,
                 lesson_days="mon,wed,fri", lesson_price=40_000,
                 standard_lessons_per_month=12, monthly_fee=480_000,
                 rate_manual=1, teacher_rate_per_student=160_000)
db.add(g); db.commit()
S = []
for i in range(10):
    s = models.Student(full_name=f"Bola {i}", branch_id=b.id, status="active",
                       group_id=g.id, enrolled_date=PREV)
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    S.append(s)
db.commit()

# O'tgan oyda 13 ta dars — SESHANBA/PAYSHANBA/SHANBA kunlari
d = PREV
held_dates = []
while d.month == PREV.month and len(held_dates) < 13:
    if d.weekday() in (1, 3, 5):
        held_dates.append(d)
    d += timedelta(days=1)
for dd in held_dates:
    l = models.Lesson(group_id=g.id, date=dd, teacher_id=t.id, held=1)
    db.add(l); db.commit()
    for s in S:
        db.add(models.Attendance(student_id=s.id, lesson_id=l.id, present=1))
db.commit()

H = tok("asos")
PY, PM = PREV.year, PREV.month


def les_count(month_start):
    y, m = month_start.year, month_start.month
    nxt = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return (db.query(models.Lesson)
            .filter(models.Lesson.group_id == g.id,
                    models.Lesson.date >= month_start,
                    models.Lesson.date < nxt).count())


print("=== 1. Tugab bo'lgan oy: 13 dars, oylik to'liq ===")
ck("o'tgan oyda 13 ta dars", les_count(PREV), 13)
p0 = client.get(f"/api/payroll?year={PY}&month={PM}", headers=H).json()
row0 = [r for r in p0["rows"] if r["teacher_id"] == t.id][0]
# 13 dars x 10 bola x (160000/13) = 1 600 000
ck("oylik 1 600 000", round(row0["earned"]), 1_600_000)

print()
print("=== 2. O'tgan oy jadvalini OCHISH oylikni o'zgartirmaydi ===")
r = client.get(f"/api/groups/{g.id}/attendance?year={PY}&month={PM}",
               headers=H)
ck("jadval ochildi", r.status_code, 200)
db.expire_all()
ck("yangi dars YARATILMADI (13 ta qoldi)", les_count(PREV), 13)
p1 = client.get(f"/api/payroll?year={PY}&month={PM}", headers=H).json()
row1 = [r2 for r2 in p1["rows"] if r2["teacher_id"] == t.id][0]
ck("oylik o'zgarmadi", round(row1["earned"]), 1_600_000)
ck("bo'luvchi hamon 13", row1["groups"][0]["rate"], 160_000 / 13)

print()
print("=== 3. Joriy oyda jadval avvalgidek ishlaydi ===")
before = les_count(CUR)
r = client.get(f"/api/groups/{g.id}/attendance"
               f"?year={CUR.year}&month={CUR.month}", headers=H)
ck("jadval ochildi", r.status_code, 200)
db.expire_all()
ck("joriy oyga darslar yaratildi", les_count(CUR) > before, True)

print()
print("=== 4. Eski (tuzatishdan oldingi) bo'sh yozuvlar: diagnostika ===")
# Tuzatishdan OLDIN yaratilgan bo'sh darslarni qo'lda qo'yamiz —
# ular o'chirilmaydi, lekin diagnostika ularni ko'rsatishi shart.
d = PREV
ghost = 0
while d.month == PREV.month:
    if d.weekday() in (0, 2, 4):
        db.add(models.Lesson(group_id=g.id, date=d, teacher_id=t.id,
                             held=0, created_by="avtomat"))
        ghost += 1
    d += timedelta(days=1)
db.commit()
ck("bo'sh yozuvlar qo'shildi (eski holat)", ghost > 10, True)

p2 = client.get(f"/api/payroll?year={PY}&month={PM}", headers=H).json()
row2 = [r2 for r2 in p2["rows"] if r2["teacher_id"] == t.id][0]
# 2026-09-07, Jahongir: "bosh yoqlama sanalmaydi" — bo'sh dars
# yozuvlari yopilgan oyning bo'luvchisiga KIRMAYDI, shuning uchun
# oylik o'zgarmaydi.
ck("oylik KAMAYMADI", round(row2["earned"]), 1_600_000)

d2 = client.get(f"/api/payroll/diag?year={PY}&month={PM}"
                f"&teacher_id={t.id}", headers=H).json()
tt = d2["teachers"][0]
gg = tt["groups"][0]
ck("bo'sh dars yozuvlari sanaldi", gg["empty_lesson_rows"], ghost)
ck("bo'luvchi o'tilgan darslar soni", gg["divisor"], 13)
ck("haqiqiy bo'luvchi bilan bir xil", gg["divisor_if_real"], 13)
ck("tuzatiladigan narsa qolmadi", tt["gain_if_fixed"], 0)

print()
print("=== 5. Bo'sh yozuvlar HECH QAYERGA yo'qolmadi ===")
db.expire_all()
ck("dars yozuvlari joyida", les_count(PREV), 13 + ghost)
client.get(f"/api/groups/{g.id}/attendance?year={PY}&month={PM}", headers=H)
db.expire_all()
ck("jadval ochilgandan keyin ham joyida", les_count(PREV), 13 + ghost)

print()
print("XULOSA: " + ("HAMMASI O'TDI" if not fails
                    else f"{len(fails)} ta xato: {fails}"))
sys.exit(1 if fails else 0)
