"""STRETINKO 420 000 + QOPLONBEK (2026-09-19).

Jahongir: "Qoplonbek Stretinko filialining ham barcha ishlarini menejerga
ochib ber va stretinkoda narxlar 420 bolgani bilan 10% skidka 480mingdan
hisoblanyabdi ekan shunaqami togrla".
"""
import os
import sys
import tempfile
from datetime import date

_DIR = os.path.join(tempfile.gettempdir(), "stretinko_420_test")
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
from courses import fix_stretinko_420, grant_qoplonbek_stretinko  # noqa: E402
from common import _user_branch_ids                # noqa: E402

c = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
main_b = models.Branch(name="Bekobod 1")
st_b = models.Branch(name="Stretinko")
db.add_all([main_b, st_b]); db.commit()

g_st = models.Group(name="Stretinko A", branch_id=st_b.id, lesson_price=40000,
                    monthly_fee=480000, standard_lessons_per_month=12)
g_main = models.Group(name="Asosiy A", branch_id=main_b.id, lesson_price=40000,
                      monthly_fee=480000, standard_lessons_per_month=12)
db.add_all([g_st, g_main]); db.commit()

def stud(name, g, b, locked=None):
    s = models.Student(full_name=name, branch_id=b.id, group_id=g.id,
                       status="active", enrolled_date=date(2026, 8, 1),
                       locked_lesson_price=locked)
    db.add(s); db.commit()
    return s

s_disc = stud("Chegirmali Stretinko", g_st, st_b)
s_lock = stud("Qulfli Stretinko", g_st, st_b, locked=40000)
s_man = stud("Qo'lda o'zgargan", g_st, st_b)
s_main = stud("Asosiy filial", g_main, main_b)
for s in (s_disc, s_man, s_main):
    db.add(models.Discount(student_id=s.id, kind="individual", percent=10,
                           reason="test", status="active"))
db.commit()

def charge(s, amt):
    p = models.Payment(student_id=s.id, amount=-amt, kind="charge",
                       period="2026-09", created_by="Tizim")
    db.add(p); db.commit()
    return p

p_disc = charge(s_disc, 432000)       # 480 000 - 10% — XATO
p_lock = charge(s_lock, 480000)       # qulf 40 000 — XATO
p_man = charge(s_man, 400000)         # boshqa sabab — tegilmaydi
p_main = charge(s_main, 432000)       # asosiy filial — tegilmaydi
aug = models.Payment(student_id=s_disc.id, amount=-432000, kind="charge",
                     period="2026-08", created_by="Tizim")
db.add(aug); db.commit()

dry = fix_stretinko_420(db, apply=False)
ck("sinov rejimi: 2 hisob topildi", dry["charges"], 2)
db.expire_all()
ck("sinov rejimi hech narsani o'zgartirmaydi",
   db.query(models.Payment).get(p_disc.id).amount, -432000)

r = fix_stretinko_420(db)
db.expire_all()
ck("guruh narxi 35 000", db.query(models.Group).get(g_st.id).lesson_price, 35000)
ck("guruh oylik 420 000", db.query(models.Group).get(g_st.id).monthly_fee, 420000)
ck("asosiy filial guruhiga tegilmadi", db.query(models.Group).get(g_main.id).lesson_price, 40000)
ck("40 000 qulf olindi", db.query(models.Student).get(s_lock.id).locked_lesson_price, None)
ck("chegirmali: 432 000 -> 378 000", db.query(models.Payment).get(p_disc.id).amount, -378000)
ck("qulfli: 480 000 -> 420 000", db.query(models.Payment).get(p_lock.id).amount, -420000)
ck("qo'lda o'zgargan hisobga tegilmadi", db.query(models.Payment).get(p_man.id).amount, -400000)
ck("asosiy filial hisobiga tegilmadi", db.query(models.Payment).get(p_main.id).amount, -432000)
ck("avgust hisobiga tegilmadi", db.query(models.Payment).get(aug.id).amount, -432000)
ck("qaytgan summa", r["back_sum"], 54000 + 60000)
ck("ikkinchi marta — o'zgarish yo'q", fix_stretinko_420(db)["charges"], 0)

# --- Yangi guruh: Stretinko'da kurssiz 40 000 bilan ochilmaydi
u_f = models.User(username="boss", password_hash=hash_password("x"),
                  full_name="Asoschi", role=roles.FOUNDER, branch_id=main_b.id)
db.add(u_f); db.commit()
T = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "boss", "password": "x"}).json()["access_token"]}
rg = c.post("/api/groups", headers=T, json={"name": "Stretinko yangi", "branch_id": st_b.id})
ck("yangi Stretinko guruhi 200", rg.status_code, 200)
ck("yangi Stretinko guruhi 35 000", rg.json().get("lesson_price"), 35000)
rg2 = c.post("/api/groups", headers=T, json={"name": "Asosiy yangi", "branch_id": main_b.id})
ck("asosiy filial yangi guruhi o'zgarmaydi", rg2.json().get("lesson_price"), 40000)

# --- Qoplonbek
from courses import undo_student_qoplonbek                 # noqa: E402
u_s = models.User(username="qoplonbek_st", password_hash=hash_password("x"),
                  full_name="Qoplonbek", role=roles.STUDENT, branch_id=main_b.id)
db.add(u_s); db.commit()
db.add(models.UserBranch(user_id=u_s.id, branch_id=st_b.id)); db.commit()
ck("o'quvchi Qoplonbek hisobga olinmaydi", grant_qoplonbek_stretinko(db).get("found"), 0)
ck("o'quvchidagi xato filial olib tashlandi", undo_student_qoplonbek(db), [u_s.id])
u_q = models.User(username="qoplonbek", password_hash=hash_password("x"),
                  full_name="Qoplonbek Karimov", role=roles.SALES_MANAGER,
                  branch_id=main_b.id)
db.add(u_q); db.commit()
q = grant_qoplonbek_stretinko(db)
ck("Qoplonbek topildi va Stretinko qo'shildi", q.get("added"), [st_b.id])
u_q = db.query(models.User).get(u_q.id)
ck("Qoplonbek filiallari", sorted(_user_branch_ids(db, u_q)), sorted([main_b.id, st_b.id]))
ck("qayta chaqirilsa takrorlanmaydi", grant_qoplonbek_stretinko(db).get("added"), [])
TQ = {"Authorization": "Bearer " + c.post("/api/auth/login", json={
    "username": "qoplonbek", "password": "x"}).json()["access_token"]}
rs = c.get(f"/api/students?branch_id={st_b.id}", headers=TQ)
ck("Qoplonbek Stretinko o'quvchilarini ko'radi", rs.status_code, 200)

db.close()
print("\nJAMI XATO:", len(fails), fails)
sys.exit(1 if fails else 0)
