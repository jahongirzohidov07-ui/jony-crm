# -*- coding: utf-8 -*-
"""IMPORTNI BEKOR QILISH (2026-08-28).

Jahongir: "hozir Elena rus tili ... filialdagi guruhga o'quvchi import
qilib 167 ta o'quvchini kirgizvoribman ADASHIB, nima qilsam bo'ladi"

ENG MUHIM TEKSHIRUV: haqiqiy o'quvchi ZARAR KO'RMASLIGI. Bekor
qilish 167 ta yozuvni birdan olib tashlaydi — orasida to'lov qilgan
haqiqiy bola bo'lsa, u yo'qolsa falokat bo'ladi. Shuning uchun
testning yarmi aynan HIMOYAga bag'ishlangan.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_undo/db.sqlite"
os.makedirs("/tmp/verify_undo", exist_ok=True)
if os.path.exists("/tmp/verify_undo/db.sqlite"):
    os.remove("/tmp/verify_undo/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime                 # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import common                                       # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Stretinko")
db.add(b); db.commit()
common.reset_partner_cache()
g = models.Group(name="Elena rus tili", branch_id=b.id, monthly_fee=400_000,
                 subject="Rus tili")
gb = models.Group(name="Boshqa guruh", branch_id=b.id, monthly_fee=400_000)
db.add_all([g, gb]); db.commit()

fo = models.User(username="asoschi_u", password_hash=hash_password("jonyjony"),
                 role=roles.FOUNDER, full_name="Jahongir", is_active=1)
# Filial rahbari — import qila oladigan, lekin ASOSCHI BO'LMAGAN rol.
# Aynan shunday odam adashib import qilishi mumkin.
adm = models.User(username="admin_u", password_hash=hash_password("jonyjony"),
                  role=roles.BRANCH_MANAGER, full_name="Filial rahbari",
                  branch_id=b.id, is_active=1)
db.add_all([fo, adm]); db.commit()
HF = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asoschi_u", "password": "jonyjony"}).json()["access_token"]}
HA = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "admin_u", "password": "jonyjony"}).json()["access_token"]}


# =====================================================================
print("=== 1. XATO IMPORT (167 ta) ===")
# =====================================================================
rows = [{"full_name": f"Xato O'quvchi {i}", "phone": f"+9989{i:08d}"}
        for i in range(1, 168)]
r = c.post("/api/students/import", headers=HF,
           json={"group_id": g.id, "rows": rows}).json()
ck("167 ta kirdi", r["created"], 167)
ck("guruhda 167 ta bo'ldi",
   db.query(models.Student).filter(common.in_group(g.id)).count(), 167)

# JONLI BAZADAGIDEK: tizim har bir yangi o'quvchiga oylik HISOB
# (qarz) yozadi. Xato import shu bilan MOLIYAGA ham tegib ketadi.
for s_ in db.query(models.Student).filter(common.in_group(g.id)).all():
    db.add(models.Payment(student_id=s_.id, amount=-400_000,
                          kind="charge", period="2026-08",
                          created_by="avtomat hisob"))
db.commit()
ck("167 ta soxta qarz paydo bo'ldi",
   db.query(models.Payment).filter(models.Payment.kind == "charge").count(),
   167)

# HAQIQIY o'quvchilar — shu guruhda, lekin TARIXI bor
real = []
for nm, iz in (("Haqiqiy Tolovchi", "payment"),
               ("Haqiqiy Qatnovchi", "attendance"),
               ("Haqiqiy Coinli", "coin")):
    s = models.Student(full_name=nm, group_id=g.id, branch_id=b.id,
                       status="active")
    db.add(s); db.commit()
    real.append(s)
    if iz == "payment":
        db.add(models.Payment(student_id=s.id, amount=400_000,
                              kind="payment", created_by="test"))
    elif iz == "attendance":
        les = models.Lesson(group_id=g.id, date=date.today())
        db.add(les); db.commit()
        db.add(models.Attendance(student_id=s.id, lesson_id=les.id,
                                 present=1))
    else:
        db.add(models.CoinEntry(student_id=s.id, amount=10,
                                source="test", created_by="test"))
    db.commit()
ck("guruhda jami 170 ta", db.query(models.Student)
   .filter(common.in_group(g.id)).count(), 170)


# =====================================================================
print("\n=== 2. RO'YXAT — HECH NARSAGA TEGMAYDI ===")
# =====================================================================
d = c.post("/api/students/import-undo", headers=HF,
           json={"group_id": g.id, "dry_run": True}).json()
ck("dry_run belgisi", d["dry_run"], True)
ck("guruh nomi", d["group"], "Elena rus tili")
ck("jami 170", d["total"], 170)
ck("bekor qilinadi — 167", d["can_undo"], 167)
ck("HIMOYALANGAN — 3", d["protected"], 3)
# ENG MUHIM: avtomat HISOB "tarix" deb hisoblanmasligi kerak.
# Aks holda 167 tasining hammasi himoyalanib, bekor qilish
# umuman ishlamasdi (test aynan shu xatoni tutdi).
ck("avtomat hisob TARIX deb sanalmadi",
   all(not x["activity"] for x in d["rows"]), True)
ck("  lekin nechta hisob borligi ko'rsatiladi", d["charges"], 167)
ck("  soxta qarz summasi aytiladi", d["fake_debt"], -400_000 * 167)
ck("himoyalanganlar kimligi ko'rsatilgan",
   sorted(x["name"] for x in d["protected_rows"]),
   ["Haqiqiy Coinli", "Haqiqiy Qatnovchi", "Haqiqiy Tolovchi"])
ck("  sababi ham yozilgan",
   all(x["activity"] for x in d["protected_rows"]), True)
ck("RO'YXAT SO'RALGANDA hech kim o'chmadi",
   db.query(models.Student).filter(common.in_group(g.id)).count(), 170)


# =====================================================================
print("\n=== 3. ARXIVGA (qaytarib bo'ladi) ===")
# =====================================================================
ten = [x["id"] for x in d["rows"][:10]]
rr = c.post("/api/students/import-undo", headers=HA, json={
    "group_id": g.id, "ids": ten, "mode": "archive",
    "dry_run": False})
if rr.status_code != 200:
    print("  >>> JAVOB:", rr.status_code, rr.json())
r = rr.json()
ck("10 tasi arxivga o'tdi", r.get("done"), 10)
s0 = db.query(models.Student).get(ten[0])
ck("  yozuv O'CHIRILMADI", s0 is not None, True)
ck("  holati arxiv", s0.status, "archived")
ck("  ketgan sanasi qo'yildi", bool(s0.left_date), True)
ck("  guruhdan chiqarildi", s0.group_id, None)
ck("  izohda sabab bor", "Xato import" in (s0.note or ""), True)
ck("  SOXTA QARZI tozalandi",
   db.query(models.Payment).filter(
       models.Payment.student_id == s0.id,
       models.Payment.kind == "charge").count(), 0)
ck("  balansi nol", common.student_balance(db, s0.id), 0.0)
ck("guruhda 160 ta qoldi",
   db.query(models.Student).filter(common.in_group(g.id)).count(), 160)
ck("bazadagi jami yozuv o'zgarmadi",
   db.query(models.Student).count(), 170)


# =====================================================================
print("\n=== 4. HIMOYA: haqiqiy o'quvchiga TEGIB BO'LMAYDI ===")
# =====================================================================
r = c.post("/api/students/import-undo", headers=HF, json={
    "group_id": g.id, "ids": [real[0].id], "mode": "delete",
    "dry_run": False})
ck("to'lov qilgan o'quvchini bekor qilib bo'lmaydi", r.status_code, 400)
ck("  sabab tushuntirilgan", "tarixi bor" in r.json()["detail"], True)
ck("  kimligi aytiladi", "Haqiqiy Tolovchi" in r.json()["detail"], True)
ck("  o'zi joyida", db.query(models.Student).get(real[0].id) is not None, True)

# Aralash ro'yxat — bittasi himoyalangan bo'lsa, HAMMASI to'xtaydi
d2 = c.post("/api/students/import-undo", headers=HF,
            json={"group_id": g.id, "dry_run": True}).json()
aralash = [d2["rows"][0]["id"], real[1].id]
n_before = db.query(models.Student).count()
r = c.post("/api/students/import-undo", headers=HF, json={
    "group_id": g.id, "ids": aralash, "mode": "delete", "dry_run": False})
ck("aralash ro'yxat rad etiladi", r.status_code, 400)
ck("  hech kim o'chmadi", db.query(models.Student).count(), n_before)

# Boshqa guruhdagi o'quvchi ham tegmaydi
sb = models.Student(full_name="Boshqa Guruh Bolasi", group_id=gb.id,
                    branch_id=b.id, status="active")
db.add(sb); db.commit()
r = c.post("/api/students/import-undo", headers=HF, json={
    "group_id": g.id, "ids": [sb.id], "mode": "delete", "dry_run": False})
ck("boshqa guruhdagi o'quvchi rad etiladi", r.status_code, 400)
ck("  o'zi joyida", db.query(models.Student).get(sb.id) is not None, True)


# =====================================================================
print("\n=== 5. HUQUQ ===")
# =====================================================================
d3 = c.post("/api/students/import-undo", headers=HF,
            json={"group_id": g.id, "dry_run": True}).json()
r = c.post("/api/students/import-undo", headers=HA, json={
    "group_id": g.id, "ids": [d3["rows"][0]["id"]], "mode": "delete",
    "dry_run": False})
ck("filial rahbariga BUTUNLAY o'chirish yopiq", r.status_code, 403)
ck("  tushuntirish beriladi",
   "asoschi" in r.json()["detail"].lower(), True)
ck("  arxivga yo'li borligi aytiladi",
   "arxiv" in r.json()["detail"].lower(), True)
ck("loginsiz umuman ishlamaydi",
   c.post("/api/students/import-undo",
          json={"group_id": g.id}).status_code in (401, 403), True)


# =====================================================================
print("\n=== 6. BUTUNLAY O'CHIRISH (asoschi) ===")
# =====================================================================
d4 = c.post("/api/students/import-undo", headers=HF,
            json={"group_id": g.id, "dry_run": True}).json()
hammasi = [x["id"] for x in d4["rows"]]
ck("qolgan bekor qilinadiganlar", len(hammasi), 157)
r = c.post("/api/students/import-undo", headers=HF, json={
    "group_id": g.id, "ids": hammasi, "mode": "delete",
    "dry_run": False}).json()
ck("157 tasi o'chirildi", r["done"], 157)
ck("guruhda FAQAT haqiqiylar qoldi",
   db.query(models.Student).filter(common.in_group(g.id)).count(), 3)
ck("  ular kimligi",
   sorted(x.full_name for x in db.query(models.Student)
          .filter(common.in_group(g.id)).all()),
   ["Haqiqiy Coinli", "Haqiqiy Qatnovchi", "Haqiqiy Tolovchi"])
ck("haqiqiy o'quvchining to'lovi joyida",
   db.query(models.Payment).filter(
       models.Payment.student_id == real[0].id,
       models.Payment.kind == "payment").count(), 1)
ck("SOXTA QARZ butunlay yo'qoldi (bittasi ham qolmadi)",
   db.query(models.Payment).filter(
       models.Payment.kind == "charge").count(), 0)
ck("arxivga o'tganlar o'chmadi (10 ta)",
   db.query(models.Student).filter(
       models.Student.status == "archived").count(), 10)


# =====================================================================
print("\n=== 7. AUDITDA IZ QOLDI ===")
# =====================================================================
au = (db.query(models.AuditLog)
      .filter(models.AuditLog.action == "import_undo").all())
ck("audit yozuvlari bor", len(au) >= 2, True)
ck("  ismlar saqlangan", any("Xato O'quvchi" in (a.note or "")
                             for a in au), True)
ck("  qaysi usul ekani yozilgan",
   any("o'chirildi" in (a.old_value or "") for a in au)
   and any("arxivga" in (a.old_value or "") for a in au), True)

bat = c.get("/api/student-imports", headers=HF).json()
ck("importlar ro'yxati ochiladi", len(bat["rows"]) >= 1, True)
ck("  qaysi guruh va nechta ekani ko'rinadi",
   "Elena rus tili" in (bat["rows"][0]["label"] or ""), True)
# 2026-08-28: guruh RAQAMI ham qaytadi — oyna guruhlar ro'yxatisiz
# ham ishlashi kerak (Jahongir: "tanlab bo'lmayabdi").
ck("  guruh raqami ham beriladi", bat["rows"][0]["group_id"], g.id)
ck("  guruh nomi alohida", bat["rows"][0]["group"], "Elena rus tili")

# ESKI YOZUVLARDA guruh raqami yo'q — nom bo'yicha topilishi kerak
eski = (db.query(models.AuditLog)
        .filter(models.AuditLog.action == "import").first())
eski.entity_id = None
db.commit()
bat2 = c.get("/api/student-imports", headers=HF).json()
ck("eski yozuvda ham guruh nomdan topiladi",
   bat2["rows"][-1]["group_id"], g.id)


print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
