"""XODIM FARZANDI CHEGIRMASI — XODIMLAR RO'YXATI (2026-10-22).

Jahongir: "xodimlarga va qarindoshlariga chegirma bo'lganda hamma
xodimlar ham chiqmayabdi admin ro'yxatida".

Ilgari forma /api/users ni ishlatardi: admin va sotuv menejeri uni
olmasdi (403), filial rahbari faqat o'z filialini ko'rardi.
Tekshiriladi:
  1. Admin, sotuv menejeri, filial rahbari — BARCHA filiallarning faol
     xodimlarini ko'radi (filial nomi bilan).
  2. Ishdan ketgan xodim, o'quvchi, ota-ona va kuzatuvchi chiqmaydi.
  3. Ustoz (o'qituvchi) — chegirma so'rash huquqi yo'q, 403.
  4. Boshqa filial xodimining farzandiga chegirma so'rovi yuboriladi.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "discount_staff_opts_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b1, b2 = models.Branch(name="Zafar"), models.Branch(name="Chilonzor")
db.add_all([b1, b2]); db.commit()


def user(login, role, br, active=1):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=login.capitalize(), role=role,
                    branch_id=br.id if br else None, is_active=active)
    db.add(u); db.commit()
    return u


ADM = user("admin1", roles.ADMINISTRATOR, b1)
SM = user("sotuv1", roles.SALES_MANAGER, b1)
BM = user("rahbar1", roles.BRANCH_MANAGER, b1)
T2 = user("ustoz2", roles.TEACHER, b2)          # boshqa filial ustozi
HR = user("hr0", roles.HR_MANAGER, None)        # filialsiz
GONE = user("ketgan", roles.TEACHER, b1, active=0)
user("bola", roles.STUDENT, b1)
user("ona", roles.PARENT, b1)
user("kuzat", roles.OBSERVER, None)
st = models.Student(full_name="Xodim Bolasi", branch_id=b1.id,
                    status="active")
db.add(st); db.commit()


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return {"Authorization": "Bearer " + r.json()["access_token"]}


want = sorted(["Admin1", "Sotuv1", "Rahbar1", "Ustoz2", "Hr0"])
for login in ("admin1", "sotuv1", "rahbar1"):
    print(f"=== 1-2. {login} ===")
    r = c.get("/api/discounts/staff-options", headers=tok(login))
    ck(f"{login}: 200", r.status_code, 200)
    rows = r.json() if r.status_code == 200 else []
    ck(f"{login}: barcha faol xodimlar", sorted(x["full_name"] for x in rows),
       want)
    ck(f"{login}: boshqa filial ustozi filiali bilan",
       next((x["branch"] for x in rows if x["id"] == T2.id), None),
       "Chilonzor")

print("\n=== 3. USTOZ ===")
r = c.get("/api/discounts/staff-options", headers=tok("ustoz2"))
ck("ustozga yopiq", r.status_code, 403)

print("\n=== 4. BOSHQA FILIAL XODIMI FARZANDIGA CHEGIRMA ===")
r = c.post("/api/discounts", headers=tok("admin1"), json={
    "student_id": st.id, "kind": "staff_child", "percent": 20,
    "reason": "Chilonzor ustozining o'g'li", "staff_user_id": T2.id})
ck("so'rov qabul qilindi", r.status_code, 200)
db.expire_all()
d = db.query(models.Discount).filter(
    models.Discount.student_id == st.id).first()
ck("chegirmada xodim to'g'ri", d.staff_user_id if d else None, T2.id)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
