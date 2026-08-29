# -*- coding: utf-8 -*-
"""IKKI LAVOZIM: almashtirish ikki tomonga ham ishlashi (2026-08-29).

Jahongir: "Stretinko filial rahbari va ustoz Nodirbek Abdulatipov
bitta odam, lavozim o'zgartirish ishlamayabdi, MENEJERDAN USTOZGA
O'TGANDAN KEYIN ALMASHTIRA OLMAY QOLIBDI. Xuddi shunday Go'zal
Xozidova o'quv bo'limi rahbari va Zafar filialda ustoz."

SABAB. Tahrirlash oynasi qo'shimcha lavozimlar ro'yxatidan ASOSIY
lavozimni chiqarib yuboradi (ikki marta turmasin uchun). Asosiy
lavozim "filial rahbari"dan "ustoz"ga o'zgartirilganda ro'yxatda
faqat "ustoz" qolgan edi -> filtrdan keyin ro'yxat BO'SH bo'ldi ->
odam ustoz kabinetida qamalib qoldi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_dual/db.sqlite"
os.makedirs("/tmp/verify_dual", exist_ok=True)
if os.path.exists("/tmp/verify_dual/db.sqlite"):
    os.remove("/tmp/verify_dual/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

fo = models.User(username="asoschi_d", password_hash=hash_password("jonyjony"),
                 role=roles.FOUNDER, full_name="Jahongir", is_active=1)
nodir = models.User(username="nodir", password_hash=hash_password("jonyjony"),
                    role=roles.BRANCH_MANAGER,
                    full_name="Nodirbek Abdulatipov",
                    branch_id=b.id, is_active=1)
db.add_all([fo, nodir]); db.commit()
db.add(models.UserRole(user_id=nodir.id, role=roles.TEACHER))
db.commit()

HF = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "asoschi_d", "password": "jonyjony"}).json()["access_token"]}
TOK = c.post("/api/auth/login", json={
    "username": "nodir", "password": "jonyjony"}).json()["access_token"]
HN = {"Authorization": "Bearer " + TOK}


def roles_now(extra_hdr=None):
    h = dict(HN)
    if extra_hdr:
        h["X-Active-Role"] = extra_hdr
    r = c.get("/api/me", headers=h)
    if r.status_code != 200:
        return r.status_code
    j = r.json()
    got = j.get("roles") or j.get("all_roles") or []
    return sorted(x["key"] if isinstance(x, dict) else x for x in got)


# =====================================================================
print("=== 1. BOSHLANG'ICH HOLAT ===")
# =====================================================================
ck("asosiy lavozim — filial rahbari", nodir.role, roles.BRANCH_MANAGER)
ck("qo'shimchada ustoz bor",
   [r.role for r in db.query(models.UserRole).filter(
       models.UserRole.user_id == nodir.id).all()], [roles.TEACHER])
ck("ikkala lavozim ham ko'rinadi", roles_now(),
   sorted([roles.BRANCH_MANAGER, roles.TEACHER]))


# =====================================================================
print("\n=== 2. USTOZGA O'TGANDA HAM RO'YXAT TO'LIQ ===")
# =====================================================================
ck("ustoz sifatida ham ikkalasi ko'rinadi", roles_now(roles.TEACHER),
   sorted([roles.BRANCH_MANAGER, roles.TEACHER]))
ck("  qaytib rahbarga o'ta oladi",
   c.get("/api/me",
         headers={**HN, "X-Active-Role": roles.BRANCH_MANAGER}
         ).json().get("role"), roles.BRANCH_MANAGER)


# =====================================================================
print("\n=== 3. ASL XATO: asosiy lavozim ALMASHTIRILGANDA ===")
# =====================================================================
# Brauzer aynan shunday yuboradi: yangi rol "ustoz", qo'shimchalar
# ro'yxatidan esa "ustoz" filtrlanib tashlangan -> BO'SH.
r = c.put(f"/api/users/{nodir.id}", headers=HF, json={
    "role": roles.TEACHER, "extra_roles": []})
ck("saqlandi", r.status_code, 200)
db.expire_all()
nodir = db.query(models.User).get(nodir.id)
ck("asosiy lavozim ustoz bo'ldi", nodir.role, roles.TEACHER)
qosh = [x.role for x in db.query(models.UserRole).filter(
    models.UserRole.user_id == nodir.id).all()]
ck("ESKI LAVOZIM YO'QOLMADI", qosh, [roles.BRANCH_MANAGER])
ck("ro'yxatda ikkalasi ham bor", roles_now(),
   sorted([roles.BRANCH_MANAGER, roles.TEACHER]))
ck("  rahbarga QAYTA OLADI",
   c.get("/api/me",
         headers={**HN, "X-Active-Role": roles.BRANCH_MANAGER}
         ).json().get("role"), roles.BRANCH_MANAGER)


# =====================================================================
print("\n=== 4. TESKARI YO'NALISH ===")
# =====================================================================
r = c.put(f"/api/users/{nodir.id}", headers=HF, json={
    "role": roles.BRANCH_MANAGER, "extra_roles": []})
ck("qayta rahbar qilindi", r.status_code, 200)
db.expire_all()
ck("  ustoz lavozimi saqlanib qoldi",
   [x.role for x in db.query(models.UserRole).filter(
       models.UserRole.user_id == nodir.id).all()], [roles.TEACHER])
ck("  ro'yxat baribir to'liq", roles_now(),
   sorted([roles.BRANCH_MANAGER, roles.TEACHER]))


# =====================================================================
print("\n=== 5. QO'SHIMCHALAR YUBORILMASA HAM ===")
# =====================================================================
# Boshqa oyna (masalan HR kartasi) faqat ismni yuborsa — lavozimlar
# tegilmasligi kerak.
c.put(f"/api/users/{nodir.id}", headers=HF,
      json={"full_name": "Nodirbek Abdulatipov"})
db.expire_all()
ck("qo'shimcha lavozim tegilmadi",
   [x.role for x in db.query(models.UserRole).filter(
       models.UserRole.user_id == nodir.id).all()], [roles.TEACHER])


# =====================================================================
print("\n=== 6. XAVFSIZLIK: yo'q lavozimga o'tib bo'lmaydi ===")
# =====================================================================
r = c.get("/api/me",
          headers={**HN, "X-Active-Role": roles.FOUNDER})
ck("asoschi sarlavhasi qabul qilinmadi", r.json().get("role"),
   roles.BRANCH_MANAGER)
ck("  ya'ni huquq oshirib bo'lmaydi",
   r.json().get("role") != roles.FOUNDER, True)


# =====================================================================
print("\n=== 7. UCHTA LAVOZIMDA HAM ===")
# =====================================================================
c.put(f"/api/users/{nodir.id}", headers=HF, json={
    "role": roles.BRANCH_MANAGER,
    "extra_roles": [roles.TEACHER, roles.HR_MANAGER]})
c.put(f"/api/users/{nodir.id}", headers=HF, json={
    "role": roles.HR_MANAGER, "extra_roles": [roles.TEACHER]})
db.expire_all()
ck("HRga o'tganda rahbar ham saqlandi",
   sorted(x.role for x in db.query(models.UserRole).filter(
       models.UserRole.user_id == nodir.id).all()),
   sorted([roles.BRANCH_MANAGER, roles.TEACHER]))
ck("uchalasi ham ro'yxatda", roles_now(),
   sorted([roles.BRANCH_MANAGER, roles.HR_MANAGER, roles.TEACHER]))


print("\n" + "=" * 60)
if fails:
    print("YIQILGAN TEKSHIRUVLAR:", len(fails))
    for f in fails:
        print("  -", f)
else:
    print("HAMMASI O'TDI")
sys.exit(1 if fails else 0)
