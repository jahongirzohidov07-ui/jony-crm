"""QO'SHIMCHA LAVOZIM "SUPPORT" (2026-09-30).

Jahongir: "adminga support qo'shimcha lavozim biriktirsam guruhda support
biriktirishda chiqmay qoldi".

Ilgari hamma joyda faqat asosiy lavozim (User.role) tekshirilardi.
Tekshiriladi:
  1. Guruhga support biriktirish ro'yxatida qo'shimcha lavozimli
     administrator bor; oddiy administrator (supportsiz) yo'q.
  2. Saqlash o'tadi; supportsiz administrator — 400.
  3. Tozalovchi (_cleanup_stale_support_assignments) biriktirishni
     O'CHIRMAYDI.
  4. Supportlar jadvalida, /api/support/teachers da ko'rinadi.
  5. Ustoz kartasi avtomat ochiladi va "support" turida.
  6. Administrator lavozimini "Support"ga almashtirsa, o'z panelida
     guruhni ko'radi.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "support_extra_role_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
import common                                      # noqa: E402
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
b = models.Branch(name="Zafar"); db.add(b); db.commit()


def user(login, name, role, extra=()):
    u = models.User(username=login, password_hash=hash_password("x"),
                    full_name=name, role=role, branch_id=b.id, is_active=1)
    db.add(u); db.commit()
    for r in extra:
        db.add(models.UserRole(user_id=u.id, role=r))
    db.commit()
    return u


founder = user("asos", "Asoschi", roles.FOUNDER)
adm_sup = user("adm1", "Admin Support", roles.ADMINISTRATOR,
               extra=[roles.SUPPORT_TEACHER])
adm = user("adm2", "Oddiy Admin", roles.ADMINISTRATOR)
sup = user("sup1", "Asl Support", roles.SUPPORT_TEACHER)
t = models.Teacher(full_name="Ustoz", branch_id=b.id, is_active=1)
db.add(t); db.commit()
g = models.Group(name="G1", branch_id=b.id, teacher_id=t.id,
                 lesson_price=40_000, monthly_fee=480_000)
db.add(g); db.commit()
GID, ADM_SUP, ADM, SUP = g.id, adm_sup.id, adm.id, sup.id


def tok(u):
    r = c.post("/api/auth/login", json={"username": u, "password": "x"})
    return r.json()["access_token"]


def H(t_, role=None):
    h = {"Authorization": f"Bearer {t_}"}
    if role:
        h["X-Active-Role"] = role
    return h


TF, TA = tok("asos"), tok("adm1")

print("=== 1. BIRIKTIRISH RO'YXATI ===")
r = c.get(f"/api/groups/{GID}/supports", headers=H(TF))
ck("status", r.status_code, 200)
opts = {o["user_id"] for o in r.json()["options"]}
ck("qo'shimcha lavozimli admin bor", ADM_SUP in opts, True)
ck("asl support bor", SUP in opts, True)
ck("supportsiz admin yo'q", ADM in opts, False)

print("\n=== 2. SAQLASH ===")
r = c.put(f"/api/groups/{GID}/supports?force=true", headers=H(TF),
          json={"items": [{"user_id": ADM_SUP, "days": "mon,wed",
                           "start": "15:00", "end": "16:00"}]})
ck("admin-support biriktirildi", r.status_code, 200)
r = c.put(f"/api/groups/{GID}/supports?force=true", headers=H(TF),
          json={"items": [{"user_id": ADM, "days": "mon",
                           "start": "15:00", "end": "16:00"}]})
ck("supportsiz admin — 400", r.status_code, 400)
# Qayta admin-supportni qo'yamiz (400 dan keyin o'zgarmagan bo'lishi kerak)
db.expire_all()
ck("biriktirish joyida", [a.user_id for a in db.query(
    models.SupportAssignment).filter(
    models.SupportAssignment.group_id == GID).all()], [ADM_SUP])

print("\n=== 3. TOZALOVCHI O'CHIRMAYDI ===")
common._cleanup_stale_support_assignments(db)
db.expire_all()
ck("tozalovchidan keyin ham bor", db.query(models.SupportAssignment).filter(
    models.SupportAssignment.user_id == ADM_SUP).count(), 1)

print("\n=== 4. JADVAL VA RO'YXAT ===")
r = c.get("/api/support-timetable?day=mon", headers=H(TF))
row = [x for x in r.json()["rows"] if x["name"] == "Admin Support"]
ck("supportlar jadvalida bor", len(row), 1)
ck("dushanba 15:00-16:00 G1",
   [(bl["label"], bl["time"]) for bl in row[0]["blocks"]] if row else None,
   [("G1", "15:00-16:00")])
r = c.get("/api/support/teachers", headers=H(TF))
ck("/support/teachers da bor",
   ADM_SUP in [x["id"] for x in r.json()], True)

print("\n=== 5. USTOZ KARTASI ===")
db.expire_all()
card = db.query(models.Teacher).filter(
    models.Teacher.user_id == ADM_SUP).first()
ck("karta ochildi", card is not None, True)
r = c.get("/api/teachers", headers=H(TF))
kinds = {x["full_name"]: x.get("kind") for x in r.json()}
ck("kartasi support turida", kinds.get("Admin Support"), "support")
ck("supportsiz adminga karta yo'q",
   db.query(models.Teacher).filter(models.Teacher.user_id == ADM).count(), 0)

print("\n=== 6. LAVOZIMNI ALMASHTIRGANDA O'Z PANELI ===")
r = c.get("/api/support/panel", headers=H(TA, roles.SUPPORT_TEACHER))
ck("panel status", r.status_code, 200)
txt = str(r.json())
ck("panelda G1 bor", "G1" in txt, True)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
