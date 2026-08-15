"""O'QUVCHI FILIALSIZ QOLIB KETMASIN (2026-08-15).

Jahongir: "yoqlamada bor lekin o'quvchilar royxatida o'quvchi
korinmayabdiku".

Sabab ikkita edi:
  1) eski ko'chirishdan qolgan o'quvchilarda filial UMUMAN
     belgilanmagan (branch_id bo'sh) — tepada filial tanlansa
     ular hech qayerda ko'rinmasdi;
  2) guruh ichidagi ro'yxatga ham tepadagi filial filtri
     qo'shilardi — tanlagich boshqa filialda tursa guruh bo'sh
     ko'rinardi.
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/stbranch.db"
if os.path.exists("/tmp/stbranch.db"):
    os.remove("/tmp/stbranch.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models                                # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
import common                                      # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
zafar = models.Branch(name="Zafar")
stech = models.Branch(name="Stetch", is_partner=1)
db.add_all([zafar, stech]); db.commit()
ZID, SID_B = zafar.id, stech.id
common.reset_partner_cache()
g = models.Group(name="Znayka", branch_id=ZID, lesson_price=40000)
db.add(g); db.commit(); GID = g.id
# Eski ko'chirishdan qolgan holat: filial BO'SH
for i in range(14):
    db.add(models.Student(full_name=f"O'quvchi {i:02d}", branch_id=None,
                          status="active", group_id=GID))
# Guruhsiz, filialsiz o'quvchi — unga tegilmasligi kerak
db.add(models.Student(full_name="Guruhsiz Bola", branch_id=None,
                      status="active"))
db.add(models.User(username="a", full_name="Asoschi", role="founder",
                   password_hash=hash_password("x"), is_active=1))
db.commit(); db.close()

H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "a", "password": "x"})
    .json()["access_token"]}

print("=== 1. Filial tanlanmagan bo'lsa hammasi ko'rinadi ===")
r = c.get(f"/api/students?group_id={GID}", headers=H)
ck("14 o'quvchi", len(r.json()), 14)

print("\n=== 2. MUAMMO: boshqa filial tanlansa guruh bo'sh edi ===")
r = c.get(f"/api/students?group_id={GID}&branch_id={SID_B}", headers=H)
ck("boshqa filial so'ralsa 0 (server to'g'ri ishlaydi)",
   len(r.json()), 0)

print("\n=== 3. YECHIM-1: filial to'ldirildi ===")
db = SessionLocal()
# Ilova ishga tushganda allaqachon bir marta yurgan (o'shanda hali
# o'quvchi yo'q edi) — bugungi belgini tozalab qayta chaqiramiz
db.query(models.SeedMark).filter(
    models.SeedMark.key.like("stbranch_%")).delete(
        synchronize_session=False)
db.commit()
common._SEED_KEYS = None
n = common.backfill_student_branches(db)
ck("14 ta o'quvchi biriktirildi", n, 14)
ck("guruh filialiga tushdi",
   db.query(models.Student).filter(
       models.Student.branch_id == ZID).count(), 14)
ck("guruhsiz bolaga TEGILMADI",
   db.query(models.Student).filter(
       models.Student.full_name == "Guruhsiz Bola").first().branch_id,
   None)
n2 = common.backfill_student_branches(db)
ck("ikkinchi marta ishlamaydi", n2, 0)
db.close()

print("\n=== 4. Endi Zafar tanlansa ham ko'rinadi ===")
r = c.get(f"/api/students?branch_id={ZID}", headers=H)
ck("14 ta", len(r.json()), 14)

print("\n=== 5. Mavjud filial HECH QACHON o'zgarmaydi ===")
db = SessionLocal()
st = db.query(models.Student).filter(
    models.Student.full_name == "O'quvchi 00").first()
st.branch_id = SID_B          # ataylab boshqa filialga qo'yamiz
db.commit()
db.query(models.SeedMark).filter(
    models.SeedMark.key.like("stbranch_%")).delete(
        synchronize_session=False)
db.commit()
common._SEED_KEYS = None
common.backfill_student_branches(db)
ck("qo'lda qo'yilgan filial saqlandi",
   db.query(models.Student).filter(
       models.Student.full_name == "O'quvchi 00").first().branch_id,
   SID_B)
db.close()

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
