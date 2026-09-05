# -*- coding: utf-8 -*-
"""HR XODIMGA FILIAL BIRIKTIRA OLSIN (2026-09-05).

Jahongir: "HR bo'limi rahbari xodimlarga filial biriktira olasin".

Topilgan sabablar:
  1. Tahrirlash oynasi is_active ni HAR DOIM yuborardi — HR filial
     rahbarining kartasini ochib "Saqlash" bossa, o'zgarmagan faollik
     ham "faollikni boshqarish" deb 403 berardi.
  2. Rol o'zgarmasa ham filial o'zgarsa "rol berish" tekshiruvi
     ishlardi — HR filial rahbariga filial bera olmasdi.
  3. Tahrirlashda brauzer faqat birinchi filialni yuborardi
     (branch_ids yo'q) — 2-3 filial belgilansa yo'qolardi.

Bu test 1 va 2 ni (server) tekshiradi; 3 — brauzer tomonida.
Xavfsizlik chegarasi o'zgarmadi: HR filial rahbari/asoschining
parolini, faolligini o'zgartira olmaydi, rol bera olmaydi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/hr_branch_test.db"
if os.path.exists("/tmp/hr_branch_test.db"):
    os.remove("/tmp/hr_branch_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: E402,F401
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

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
b1 = models.Branch(name="Zafar")
b2 = models.Branch(name="Bekobod 1")
b3 = models.Branch(name="Yangiyo'l")
db.add_all([b1, b2, b3]); db.commit()


def mk(u, role, bid=None, fn=None):
    x = models.User(username=u, password_hash=hash_password("x"),
                    full_name=fn or u, role=role, branch_id=bid)
    db.add(x); db.commit(); return x


asos = mk("asos", roles.FOUNDER, None, "Asoschi")
hr = mk("hr", roles.HR_MANAGER, b1.id, "HR menejer")
ustoz = mk("ustoz", roles.TEACHER, b1.id, "Ustoz")
adm = mk("admin1", roles.SALES_MANAGER, b1.id, "Admin")
bm = mk("bm", roles.BRANCH_MANAGER, b1.id, "Filial rahbari")
bm2 = mk("bm2", roles.BRANCH_MANAGER, b2.id, "Bekobod rahbari")
H = tok("hr")


def branches_of(uid):
    u = [x for x in client.get("/api/users", headers=tok("asos")).json()
         if x["id"] == uid][0]
    return sorted(u.get("branch_ids")
                  or ([u["branch_id"]] if u.get("branch_id") else []))


print("=== 1. HR oddiy xodimga filial biriktiradi ===")
r = client.put(f"/api/users/{ustoz.id}",
               json={"full_name": "Ustoz", "role": "teacher",
                     "branch_id": b2.id, "branch_ids": [b2.id, b3.id],
                     "is_active": True}, headers=H)
ck("ustoz → Bekobod + Yangiyo'l: 200", r.status_code, 200)
ck("  ikkala filial saqlandi", branches_of(ustoz.id), sorted([b2.id, b3.id]))
ck("  asosiy filial Bekobod", r.json()["branch_id"], b2.id)

r = client.put(f"/api/users/{adm.id}",
               json={"role": "sales_manager", "branch_id": b3.id,
                     "branch_ids": [b3.id], "is_active": True}, headers=H)
ck("admin → Yangiyo'l: 200", r.status_code, 200)

print("\n=== 2. HR filial rahbariga ham filial biriktiradi ===")
# Brauzer is_active ni o'zgarmagan holda yuboradi — bu 403 bo'lmasin
r = client.put(f"/api/users/{bm.id}",
               json={"full_name": "Filial rahbari", "role": "branch_manager",
                     "branch_id": b3.id, "branch_ids": [b3.id],
                     "is_active": True, "phone": "+998901112233"},
               headers=H)
ck("filial rahbari → Yangiyo'l (is_active o'zgarmagan): 200",
   r.status_code, 200)
ck("  filiali Yangiyo'l", r.json()["branch_id"], b3.id)
ck("  telefon ham saqlandi", r.json().get("phone"), "+998901112233")

print("\n=== 3. Xavfsizlik chegarasi O'ZGARMADI ===")
r = client.put(f"/api/users/{bm.id}", json={"is_active": False}, headers=H)
ck("HR filial rahbarini bo'shata olmaydi: 403", r.status_code, 403)
r = client.put(f"/api/users/{bm.id}", json={"password": "Yangi12345"},
               headers=H)
ck("HR filial rahbari parolini almashtira olmaydi: 403", r.status_code, 403)
r = client.put(f"/api/users/{ustoz.id}",
               json={"role": "branch_manager", "branch_id": b2.id}, headers=H)
ck("HR ustozni filial rahbari qila olmaydi: 403", r.status_code, 403)
r = client.put(f"/api/users/{asos.id}", json={"branch_id": b2.id}, headers=H)
ck("HR asoschi kartasiga tegolmaydi: 403", r.status_code, 403)
r = client.put(f"/api/users/{ustoz.id}", json={"is_active": False}, headers=H)
ck("HR oddiy xodimni bo'shata oladi (avvalgidek): 200", r.status_code, 200)
client.put(f"/api/users/{ustoz.id}", json={"is_active": True}, headers=H)

print("\n=== 4. Filial rahbari uchun eski qoida qoladi ===")
B2 = tok("bm2")
r = client.put(f"/api/users/{adm.id}",
               json={"role": "sales_manager", "branch_id": b2.id}, headers=B2)
ck("Bekobod rahbari boshqa filial xodimini o'ziga o'tkaza olmaydi: 403",
   r.status_code, 403)

print("\n=== 5. Asoschi hammasini qila oladi ===")
r = client.put(f"/api/users/{bm.id}",
               json={"role": "branch_manager", "branch_id": b1.id,
                     "branch_ids": [b1.id, b2.id], "is_active": True},
               headers=tok("asos"))
ck("asoschi filial rahbariga 2 filial: 200", r.status_code, 200)
ck("  ikkalasi saqlandi", branches_of(bm.id), sorted([b1.id, b2.id]))

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
