# -*- coding: utf-8 -*-
"""NEGA O'TGAN OYNING OYLIGI KAMAYIB QOLDI? (2026-09-07)

Jahongir: "31-avgust men oyliklarni screenshot qilib oldim va oyliklarni
tolagani moliyachiga berdim, lekin bugun kirib qarasam avgust oyliklari
kamayib qolgan masalan bekzod akaniki 2mlncha, shirinabonuniki 1,5 mln
atrofida kamaygan nega bunday bo'ldi".

Oylik hech qayerda saqlanmaydi — har safar yo'qlamadan qaytadan
hisoblanadi. Test uchta kamaytiruvchi sababni SINTETIK ma'lumotda
qaytadan yaratadi va /api/payroll/diag ularni to'g'ri raqamlashini
tekshiradi:

  1. KETGANNING DUMI  — o'quvchi keyin arxivga o'tsa, oxirgi kelgan
     darsidan keyingi yo'qlamalari hisobdan chiqadi;
  2. O'CHIRILGAN YO'QLAMA — avtomuzlatish oxirgi 3 ta "kelmadi"
     yozuvini bazadan o'chiradi (teshik qoladi);
  3. OY BO'LUVCHISI — oyga 13-dars qo'shilsa bitta yo'qlama narxi
     12 dan 13 ga bo'linadi.

Yana: diagnostika HECH NARSANI o'zgartirmaydi (yo'qlama, dars va
o'quvchi soni chaqiruvdan oldin va keyin bir xil) va /api/payroll
raqami diagnostikadagi amount_now bilan aynan bir xil.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/pdiag_test.db"
if os.path.exists("/tmp/pdiag_test.db"):
    os.remove("/tmp/pdiag_test.db")
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


def reseal():
    """Avgust — YOPILGAN oy, ya'ni MUHRLANGAN (2026-09-07). Test
    ma'lumotni o'zgartirgandan keyin muhrni ataylab yangilaydi —
    aks holda /api/payroll eski muhrni qaytaradi (aynan shu himoya
    uchun qilingan)."""
    client.post("/api/payroll/reseal?year=2026&month=8", headers=H)


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
# Stavka qo'lda — daraja jadvali tarixiga bog'liq bo'lmasin
g = models.Group(name="IELTS intro", branch_id=b.id, teacher_id=t.id,
                 lesson_price=40_000, standard_lessons_per_month=12,
                 monthly_fee=480_000, rate_manual=1,
                 teacher_rate_per_student=120_000)
db.add(g); db.commit()

# 6 ta o'quvchi, avgustda 12 dars (bo'luvchi = 12, yo'qlama narxi 10 000)
S = []
for i in range(6):
    s = models.Student(full_name=f"Bola {i}", branch_id=b.id, status="active",
                       group_id=g.id, enrolled_date=date(2026, 7, 1))
    db.add(s); db.commit()
    db.add(models.StudentGroupLink(student_id=s.id, group_id=g.id,
                                   is_primary=1, active=1))
    S.append(s)
db.commit()

LES = []
for d in range(1, 13):
    l = models.Lesson(group_id=g.id, date=date(2026, 8, d), teacher_id=t.id,
                      held=1)
    db.add(l); db.commit()
    LES.append(l)
    for s in S:
        db.add(models.Attendance(student_id=s.id, lesson_id=l.id, present=1))
db.commit()

H = tok("asos")
print("=== 0. Boshlang'ich holat: 12 dars x 6 bola x 10 000 = 720 000 ===")
p0 = client.get("/api/payroll?year=2026&month=8", headers=H).json()
row0 = [r for r in p0["rows"] if r["teacher_id"] == t.id][0]
ck("avgust oyligi 720 000", row0["earned"], 720_000)

d0 = client.get("/api/payroll/diag?year=2026&month=8", headers=H).json()
tr0 = [r for r in d0["teachers"] if r["teacher_id"] == t.id][0]
ck("diag amount_now = payroll earned", tr0["amount_now"], row0["earned"])
ck("hech qanday yo'qotish yo'q",
   [tr0["lost_cutoff"], tr0["lost_deleted"], tr0["lost_divisor"]],
   [0, 0, 0])

print()
print("=== 1. KETGANNING DUMI: Bola 0 sentabrda arxivga o'tdi ===")
# oxirgi 3 darsda kelmadi (yozuv turibdi), keyin arxivga o'tkazildi
for l in LES[-3:]:
    a = db.query(models.Attendance).filter_by(student_id=S[0].id,
                                              lesson_id=l.id).first()
    a.present = 0
db.commit()
S[0].status = "archived"
db.query(models.StudentGroupLink).filter_by(student_id=S[0].id).update(
    {"active": 0})
db.commit()

reseal()
p1 = client.get("/api/payroll?year=2026&month=8", headers=H).json()
row1 = [r for r in p1["rows"] if r["teacher_id"] == t.id][0]
ck("oylik 30 000 ga kamaydi (3 yo'qlama x 10 000)",
   row1["earned"], 690_000)
d1 = client.get("/api/payroll/diag?year=2026&month=8", headers=H).json()
tr1 = [r for r in d1["teachers"] if r["teacher_id"] == t.id][0]
ck("diag: ketganning dumi 30 000", tr1["lost_cutoff"], 30_000)
ck("diag: oldin qancha bo'lgan bo'lardi", tr1["would_be_before"], 720_000)
cs = tr1["groups"][0]["cut_students"]
ck("kesilgan o'quvchi ko'rsatilgan", [c["name"] for c in cs], ["Bola 0"])
ck("nechta yo'qlama kesilgan", cs[0]["excluded"], 3)

print()
print("=== 2. O'CHIRILGAN YO'QLAMA: Bola 1 avtomuzlatildi ===")
# avtomuzlatish oxirgi 3 ta "kelmadi" yozuvini BAZADAN o'chiradi
for l in LES[-3:]:
    a = db.query(models.Attendance).filter_by(student_id=S[1].id,
                                              lesson_id=l.id).first()
    db.delete(a)
S[1].status = "frozen"
db.commit()

reseal()
p2 = client.get("/api/payroll?year=2026&month=8", headers=H).json()
row2 = [r for r in p2["rows"] if r["teacher_id"] == t.id][0]
ck("oylik yana 30 000 ga kamaydi", row2["earned"], 660_000)
d2 = client.get("/api/payroll/diag?year=2026&month=8", headers=H).json()
tr2 = [r for r in d2["teachers"] if r["teacher_id"] == t.id][0]
ck("diag: o'chirilgan yo'qlama 30 000", tr2["lost_deleted"], 30_000)
hs = tr2["groups"][0]["hole_students"]
ck("teshikli o'quvchi ko'rsatilgan", [h["name"] for h in hs], ["Bola 1"])
ck("oxirgi belgidan keyin 3 ta teshik", hs[0]["missing_after_last"], 3)
ck("ichkarida teshik yo'q", hs[0]["missing_inside"], 0)
ck("umumiy: oldin 720 000 bo'lgan", tr2["would_be_before"], 720_000)

print()
print("=== 3. OY BO'LUVCHISI: avgustga 13-dars qo'shildi ===")
l13 = models.Lesson(group_id=g.id, date=date(2026, 8, 13), teacher_id=t.id,
                    held=1)
db.add(l13); db.commit()
for s in S[2:]:
    db.add(models.Attendance(student_id=s.id, lesson_id=l13.id, present=1))
db.commit()
# O'TILGAN dars qo'shildi — u sanaladi, bo'luvchi 13 bo'ladi:
# yo'qlama narxi 120 000/13 = 9230.77
reseal()
d3 = client.get("/api/payroll/diag?year=2026&month=8", headers=H).json()
tr3 = [r for r in d3["teachers"] if r["teacher_id"] == t.id][0]
gg = tr3["groups"][0]
ck("bo'luvchi 13 bo'ldi", gg["divisor"], 13)
ck("yo'qlama narxi 9230.77", gg["rate"], 9230.77)
ck("standart bo'yicha bo'lsa 10 000", gg["rate_if_standard"], 10_000.0)
ck("bo'luvchidan yo'qotish 0 dan katta", tr3["lost_divisor"] > 0, True)

print()
print("=== 3b. BO'SH dars yozuvi bo'luvchiga KIRMAYDI ===")
# 2026-09-07, Jahongir: "bosh yoqlama sanalmaydi". Yopilgan oyga
# qo'shilgan bo'sh (yo'qlamasiz) dars oylikni kamaytirmasligi shart.
reseal()
before = client.get("/api/payroll?year=2026&month=8", headers=H).json()
amt_before = [r for r in before["rows"] if r["teacher_id"] == t.id][0]["earned"]
for dd in (14, 15, 16):
    db.add(models.Lesson(group_id=g.id, date=date(2026, 8, dd),
                         teacher_id=t.id, held=0, created_by="avtomat"))
db.commit()
after = client.get("/api/payroll?year=2026&month=8", headers=H).json()
amt_after = [r for r in after["rows"] if r["teacher_id"] == t.id][0]["earned"]
ck("oylik o'zgarmadi", amt_after, amt_before)
d3b = client.get("/api/payroll/diag?year=2026&month=8&teacher_id=%d" % t.id,
                 headers=H).json()
g3b = d3b["teachers"][0]["groups"][0]
ck("bo'sh yozuvlar sanaldi", g3b["empty_lesson_rows"], 3)
ck("bo'luvchi hamon 13", g3b["divisor"], 13)
ck("tuzatiladigan narsa qolmadi", d3b["teachers"][0]["gain_if_fixed"], 0)

print()
print("=== 4. Diagnostika HECH NARSANI o'zgartirmaydi ===")
before = (db.query(models.Attendance).count(),
          db.query(models.Lesson).count(),
          db.query(models.Student).count(),
          db.query(models.AuditLog).count())
client.get("/api/payroll/diag?year=2026&month=8", headers=H)
client.get("/api/payroll/diag?year=2026&month=8&teacher_id=%d" % t.id,
           headers=H)
db.expire_all()
after = (db.query(models.Attendance).count(),
         db.query(models.Lesson).count(),
         db.query(models.Student).count(),
         db.query(models.AuditLog).count())
ck("yo'qlama/dars/o'quvchi/audit soni o'zgarmadi", after, before)

print()
print("=== 5. Faqat asoschi ko'radi ===")
r = client.get("/api/payroll/diag?year=2026&month=8", headers=tok("bek"))
ck("ustozga yopiq", r.status_code, 403)

print()
print("=== 6. amount_now hamisha /api/payroll bilan bir xil ===")
reseal()
p4 = client.get("/api/payroll?year=2026&month=8", headers=H).json()
row4 = [r for r in p4["rows"] if r["teacher_id"] == t.id][0]
d4 = client.get("/api/payroll/diag?year=2026&month=8&teacher_id=%d" % t.id,
                headers=H).json()
ck("bir xil", d4["teachers"][0]["amount_now"], row4["earned"])

print()
print("=== 7. Daraja oy o'rtasida ko'tarilsa ham /api/payroll bilan mos ===")
# Ustoz 5-avgustdan boshqa darajaga o'tdi: 5-avgustgacha darslar eski
# narxda, keyingilari yangi narxda. Diagnostika ham SHU tartibda
# hisoblashi shart (ilgari butun oyga bitta narx olinardi).
g.rate_manual = 0
db.commit()
db.add(models.TeacherGradeEvent(teacher_id=t.id, to_grade="junior",
                                effective_from=date(2026, 1, 1)))
db.add(models.TeacherGradeEvent(teacher_id=t.id, to_grade="expert",
                                effective_from=date(2026, 8, 5)))
db.commit()
reseal()
p7 = client.get("/api/payroll?year=2026&month=8", headers=H).json()
row7 = [r for r in p7["rows"] if r["teacher_id"] == t.id][0]
d7 = client.get("/api/payroll/diag?year=2026&month=8&teacher_id=%d" % t.id,
                headers=H).json()
ck("oy ichida narx o'zgarsa ham amount_now bir xil",
   d7["teachers"][0]["amount_now"], row7["earned"])
ck("guruh summasi ham bir xil",
   d7["teachers"][0]["groups"][0]["amount_now"],
   round(row7["groups"][0]["amount"], 2))

print()
print("=== 8. Bir kunda ikkita dars yozuvi bo'lsa — ko'rsatiladi ===")
dbl = models.Lesson(group_id=g.id, date=date(2026, 8, 13), teacher_id=t.id,
                    held=0)
db.add(dbl); db.commit()
d8 = client.get("/api/payroll/diag?year=2026&month=8&teacher_id=%d" % t.id,
                headers=H).json()
ck("dublikat dars yozuvi topildi",
   d8["teachers"][0]["groups"][0]["duplicate_lesson_rows"], 1)
# Dublikat BO'SH (yo'qlamasiz) — yopilgan oyda bo'luvchiga kirmaydi
ck("bo'sh dublikat bo'luvchini oshirmadi",
   d8["teachers"][0]["groups"][0]["divisor"], 13)

print()
print("XULOSA: " + ("HAMMASI O'TDI" if not fails
                    else f"{len(fails)} ta xato: {fails}"))
sys.exit(1 if fails else 0)
