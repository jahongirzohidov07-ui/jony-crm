# -*- coding: utf-8 -*-
"""XAVFSIZLIK PAKETI (2026-09-06, "togrla hamma aytganingni").

To'liq check-up auditida topilgan teshiklar:
  1. roles.COIN_ADMIN = FULL_ACCESS bir xil obyekt edi; entry.py unga
     HR ni qo'shardi -> HR bilmagan holda FULL_ACCESS (LC UP pul
     importi, shtat tasdig'i...) ga ega bo'lib qolardi;
  2. GET /api/students va /api/students/{id} faqat "kirgan bo'lsa
     bo'ldi" edi -> o'quvchi o'z tokeni bilan filialidagi barcha
     o'quvchi ismi, telefoni va BALANSINI olardi;
  3. o'quvchiga oid amallarda (to'lov, muzlatish, faollashtirish,
     coin, qarz eslatmasi...) FILIAL tekshiruvi yo'q edi;
  4. standart parol ("jonyjony") almashtirilishi majburiy emasdi;
  5. login urinish chegarasi faqat username bo'yicha edi (IP emas).
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/sec_audit.db"
if os.path.exists("/tmp/sec_audit.db"):
    os.remove("/tmp/sec_audit.db")
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
    r = client.post("/api/auth/login", json={"username": u, "password": p})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


db = SessionLocal()
b1 = models.Branch(name="Zafar")
b2 = models.Branch(name="Bekobod 1")
db.add_all([b1, b2]); db.commit()


def mk(u, role, bid=None, pw="x", fn=None):
    x = models.User(username=u, password_hash=hash_password(pw),
                    full_name=fn or u, role=role, branch_id=bid)
    db.add(x); db.commit(); return x


asos = mk("asos", roles.FOUNDER, None, fn="Asoschi")
adm1 = mk("adm1", roles.SALES_MANAGER, b1.id, fn="Zafar admin")
hr = mk("hr", roles.HR_MANAGER, b1.id, fn="HR menejer")
teacher = mk("ustoz", roles.TEACHER, b1.id, fn="Ustoz")

s1 = models.Student(full_name="Zafar bolasi", branch_id=b1.id,
                    status="active", enrolled_date=date(2026, 6, 1))
s2 = models.Student(full_name="Bekobod bolasi", branch_id=b2.id,
                    status="active", enrolled_date=date(2026, 6, 1))
db.add_all([s1, s2]); db.commit()
# O'quvchi hisobi
su = mk("901112233", roles.STUDENT, b1.id, pw="jonyjony", fn="Zafar bolasi")
s1.user_id = su.id
db.commit()
S1, S2 = s1.id, s2.id

print("=== 1. Rol ro'yxatlari alias emas ===")
ck("COIN_ADMIN va FULL_ACCESS — boshqa obyekt",
   roles.COIN_ADMIN is roles.FULL_ACCESS, False)
ck("HR coin huquqiga ega", roles.HR_MANAGER in roles.COIN_ADMIN, True)
ck("HR FULL_ACCESS ga KIRMAYDI",
   roles.HR_MANAGER in roles.FULL_ACCESS, False)
r = client.post("/api/lcup/balance", json={"rows": []}, headers=tok("hr"))
ck("HR LC UP pul importini ocholmaydi: 403", r.status_code, 403)

print("\n=== 2. O'quvchi/ota-ona ro'yxatni ko'rmaydi ===")
ST = tok("901112233", "jonyjony")
r = client.get("/api/students", headers=ST)
ck("o'quvchi ro'yxatni ko'rmaydi: 403", r.status_code, 403)
r = client.get(f"/api/students/{S2}", headers=ST)
ck("boshqa o'quvchi kartasi: 403", r.status_code, 403)
r = client.get(f"/api/students/{S1}", headers=ST)
ck("o'zinikini ko'radi: 200", r.status_code, 200)
r = client.get("/api/students", headers=tok("adm1"))
ck("admin ro'yxatni ko'radi: 200", r.status_code, 200)

print("\n=== 3. Filial chegarasi (o'quvchi amallari) ===")
A1 = tok("adm1")
ck("o'z filialida to'lov: 200",
   client.post(f"/api/students/{S1}/payments",
               json={"amount": 100000, "kind": "payment"},
               headers=A1).status_code, 200)
ck("boshqa filialda to'lov: 403",
   client.post(f"/api/students/{S2}/payments",
               json={"amount": 100000, "kind": "payment"},
               headers=A1).status_code, 403)
ck("boshqa filialda muzlatish: 403",
   client.post(f"/api/students/{S2}/freeze",
               json={"until": "2026-12-01"}, headers=A1).status_code, 403)
ck("boshqa filialda faollashtirish: 403",
   client.post(f"/api/students/{S2}/activate", json={},
               headers=A1).status_code, 403)
ck("boshqa filialda qarz eslatmasi: 403",
   client.post(f"/api/students/{S2}/notify-debt", json={},
               headers=A1).status_code, 403)
ck("asoschiga chegara yo'q: 200",
   client.post(f"/api/students/{S2}/payments",
               json={"amount": 50000, "kind": "payment"},
               headers=tok("asos")).status_code, 200)

print("\n=== 4. Standart parol — majburiy almashtirish belgisi ===")
mk("bekor", roles.SALES_MANAGER, b1.id, pw=roles.DEFAULT_PASSWORD,
   fn="Standart parolli admin")
r = client.post("/api/auth/login",
                json={"username": "bekor", "password": roles.DEFAULT_PASSWORD})
ck("xodim: must_change_password = True",
   r.json().get("must_change_password"), True)
r = client.post("/api/auth/login", json={"username": "adm1", "password": "x"})
ck("o'z parolini qo'ygan xodimda belgi yo'q",
   r.json().get("must_change_password"), False)
r = client.post("/api/auth/login",
                json={"username": "901112233", "password": "jonyjony"})
ck("o'quvchiga tegishli emas (avtomat hisob)",
   r.json().get("must_change_password"), False)

print("\n=== 5. Login urinishlari: IP bo'yicha ham ===")
ck("IP chegarasi username chegarasidan katta",
   roles.LOGIN_MAX_FAILS_IP > roles.LOGIN_MAX_FAILS, True)
for i in range(roles.LOGIN_MAX_FAILS_IP + 2):
    client.post("/api/auth/login",
                json={"username": f"yoq{i}", "password": "xato"})
r = client.post("/api/auth/login",
                json={"username": "yangi_login", "password": "xato"})
ck("bir IP dan ko'p urinish — bloklandi: 429", r.status_code, 429)

print("\n=== 6. CORS faqat o'z domenlarimiz ===")
ck("* emas", "*" in main._ALLOWED_ORIGINS, False)
ck("jonyos.uz bor", "https://jonyos.uz" in main._ALLOWED_ORIGINS, True)

print()
print("XATOLAR:", fails if fails else "yo'q")
sys.exit(1 if fails else 0)
