"""TIZIM TEKSHIRUVI (2026-08-15).

Jahongir: "men test deb bitta filial ochganman shunda qilib ko'rsa
bo'ladi hamma testlarni" + "platformani biror joyini buzib qoyib
enasini korsatma".

Shu ikkinchi jumla shu faylning asosiy mavzusi: tekshiruv HAQIQIY
FILIALGA TEGMASLIGI va o'zidan keyin BIRORTA IZ QOLDIRMASLIGI kerak.
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/selftest_t.db"
if os.path.exists("/tmp/selftest_t.db"):
    os.remove("/tmp/selftest_t.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
real = models.Branch(name="Bekobod 1"); db.add(real)
tb = models.Branch(name="Test filial"); db.add(tb)
db.commit()
RID, TID = real.id, tb.id
# Haqiqiy filialga ma'lumot: tekshiruvdan keyin BIR ZARRA
# o'zgarmaganini isbotlaymiz.
g0 = models.Group(name="Haqiqiy guruh", branch_id=RID,
                  monthly_fee=400000, lesson_price=50000)
db.add(g0); db.commit()
s0 = models.Student(full_name="Haqiqiy O'quvchi", branch_id=RID,
                    status="active", group_id=g0.id)
db.add(s0); db.commit()
db.add(models.Payment(student_id=s0.id, amount=500000, kind="payment",
                      method="cash", created_by="Admin"))
db.commit()
SID0 = s0.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="mol", full_name="Moliyachi",
                role="finance_director", branch_id=RID,
                password_hash=hash_password("x"), is_active=1),
])
db.commit()


def snapshot():
    d = SessionLocal()
    out = {}
    for name, model in (("students", models.Student),
                        ("groups", models.Group),
                        ("leads", models.Lead),
                        ("payments", models.Payment),
                        ("lessons", models.Lesson),
                        ("attendance", models.Attendance),
                        ("discounts", models.Discount),
                        ("deleted_payments", models.DeletedPayment)):
        try:
            out[name] = d.query(model).count()
        except Exception:
            out[name] = -1
    out["real_balance"] = sum(
        p.amount for p in d.query(models.Payment).filter(
            models.Payment.student_id == SID0).all())
    d.close()
    return out


before = snapshot()
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


F, M = tok("asos"), tok("mol")

print("=== 1. Faqat asoschi ishga tushira oladi ===")
r = c.post(f"/api/selftest?branch_id={TID}", headers=M)
ck("moliyachiga 403", r.status_code, 403)

print("\n=== 2. HAQIQIY FILIALDA ISHLAMAYDI (asosiy himoya) ===")
r = c.post(f"/api/selftest?branch_id={RID}", headers=F)
ck("400 - rad etildi", r.status_code, 400)
ck("sabab tushuntirilgan", "test" in str(r.json().get("detail", "")), True)
mid = snapshot()
ck("haqiqiy filialda hech narsa o'zgarmadi", mid, before)

print("\n=== 3. Filiallar ro'yxati faqat test filialini beradi ===")
r = c.get("/api/selftest/branches", headers=F)
ck("200", r.status_code, 200)
names = [b["name"] for b in r.json()["branches"]]
ck("faqat test filiali", names, ["Test filial"])

print("\n=== 4. Test filialida to'liq zanjir ishlaydi ===")
r = c.post(f"/api/selftest?branch_id={TID}", headers=F)
ck("200", r.status_code, 200)
d = r.json()
print(f"    ({d['passed']}/{d['total']} tekshiruv, {d['seconds']} s)")
for chk in d["checks"]:
    print(("      + " if chk["ok"] else "      - ") + chk["name"]
          + (f"  [{chk['detail']}]" if chk["detail"] else ""))
ck("hammasi yashil", d["all_ok"], True)
ck("kamida 12 ta tekshiruv", d["total"] >= 12, True)
ck("yiqilmadi", d["crash"], None)

print("\n=== 5. ENG MUHIMI: o'zidan keyin IZ QOLMADI ===")
after = snapshot()
for k in before:
    ck(f"{k} o'zgarmadi", after[k], before[k])
ck("tozalash hisoboti bo'sh qoldiqsiz", d["cleanup"]["stuck"], [])
ck("nechta yozuv o'chirildi", d["cleanup"]["removed"] > 5, True)

print("\n=== 6. Qoldiq tekshirgichi toza deydi ===")
r = c.get("/api/selftest/leftovers", headers=F)
ck("toza", r.json()["clean"], True)

print("\n=== 7. Ikki marta ketma-ket ishlatsa ham toza ===")
c.post(f"/api/selftest?branch_id={TID}", headers=F)
r = c.post(f"/api/selftest?branch_id={TID}", headers=F)
ck("yana yashil", r.json()["all_ok"], True)
again = snapshot()
ck("baza yana o'zgarmagan", again, before)

print("\n=== 8. Manzil xaritasi: yashirin dubl ko'paymasin ===")
r = c.get("/api/system/route-map", headers=F)
ck("200", r.status_code, 200)
d2 = r.json()
ck("manzillar sanaldi", d2["total"] > 500, True)
# Kodda 52 ta manzil bir necha faylda e'lon qilingan, LEKIN entry.py
# eskisini _drop_route bilan olib tashlaydi. Shuning uchun JONLI
# dubl atigi 2 ta (LC UP importi). Bu son OSHMASLIGI kerak - oshsa,
# demak kimdir _drop_route'ni unutgan va qaysi nusxa ishlashi
# noaniq bo'lib qolgan.
print("    jonli dubllar:", d2["duplicate_paths"])
ck("jonli dubl 2 tadan oshmadi", d2["duplicates"] <= 2, True)
ck("dubllar aynan LC UP importi",
   all("lcup" in p for p in d2["duplicate_paths"]), True)

print("\n=== 9. O'lik kod qaytib kelmasin ===")
ck("main_original.py yo'q",
   os.path.exists(os.path.join(
       os.path.dirname(os.path.abspath(__file__)),
       "main_original.py")), False)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
