"""IKKI "ADMINISTRATOR" ROLI BITTAGA BIRLASHDI (2026-09-03).

Jahongir: "unda shu 2ta administratorni bitta qil, sales managerga
birlashtir, hozirgi bor xodimlar hammasi shu admin turiga o'tsin,
kimdur administrator (qabul) turgan bo'lsa nargi turiga o'tsin".

Tizimda ikkita alohida rol bor edi va IKKALASI HAM ekranda
"Administrator" bo'lib ko'rinardi:
  sales_manager  — "Administrator"
  administrator  — "Administrator (qabul)"
Huquqlari esa bir xil emasdi: masalan muzlatilgan o'quvchini
faollashtirishni faqat birinchisi qila olardi.

Test tekshiradi:
  1. Tanlov ro'yxatlarida endi bitta variant qoladi;
  2. Mavjud xodimlar (asosiy rol VA qo'shimcha rollar) ko'chadi;
  3. Ko'chgan xodim muzlatish/faollashtirishni qila oladi;
  4. Qolib ketgan yozuv bo'lsa ham huquqi bir xil;
  5. Ko'chirish idempotent va boshqa rollarga tegmaydi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/admmerge_test.db"
if os.path.exists("/tmp/admmerge_test.db"):
    os.remove("/tmp/admmerge_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry
from database import SessionLocal
from auth import hash_password

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


print("=== 1. TANLOVDA BITTA \"ADMINISTRATOR\" QOLDI ===")
ck("ALL_ROLES da yo'q", roles.ADMINISTRATOR in roles.ALL_ROLES, False)
ck("xodim yaratishda yo'q",
   roles.ADMINISTRATOR in roles.STAFF_ASSIGNABLE_ROLES, False)
ck("HR ro'yxatida yo'q",
   roles.ADMINISTRATOR in roles.HR_ASSIGNABLE_ROLES, False)
ck("filialga biriktirishda yo'q",
   roles.ADMINISTRATOR in roles.BRANCH_ASSIGNABLE_ROLES, False)
ck("sales_manager o'z joyida",
   roles.SALES_MANAGER in roles.STAFF_ASSIGNABLE_ROLES, True)
adm_labels = [r for r in roles.STAFF_ASSIGNABLE_ROLES
              if roles.UZ_LABELS.get(r) == "Administrator"]
ck("ro'yxatda \"Administrator\" nomi BIR MARTA", len(adm_labels), 1)

print("\n=== 2. RUXSAT RO'YXATLARIGA TEGILMADI ===")
# STAFF_ROLES — tanlov emas, RUXSAT ro'yxati; IDEA_SUBMIT va
# SALARY_SELF_VIEW aynan o'sha obyekt.
ck("STAFF_ROLES da administrator saqlandi",
   roles.ADMINISTRATOR in roles.STAFF_ROLES, True)
ck("g'oya yuborish huquqi saqlandi",
   roles.ADMINISTRATOR in roles.IDEA_SUBMIT, True)
ck("o'z oyligini ko'rish saqlandi",
   roles.ADMINISTRATOR in roles.SALARY_SELF_VIEW, True)

print("\n=== 3. HUQUQLAR TENGLASHDI ===")
farq = [nm for nm in dir(roles)
        if nm.isupper() and isinstance(getattr(roles, nm), (list, tuple))
        and roles.SALES_MANAGER in getattr(roles, nm)
        and roles.ADMINISTRATOR not in getattr(roles, nm)]
ck("farq faqat TANLOV ro'yxatlarida qoldi", sorted(farq),
   sorted(["ALL_ROLES", "BRANCH_ASSIGNABLE_ROLES",
           "HR_ASSIGNABLE_ROLES", "STAFF_ASSIGNABLE_ROLES"]))
ck("muzlatish/faollashtirish huquqi bir xil",
   roles.ADMINISTRATOR in roles.FREEZE_ROLES, True)

print("\n=== 4. MAVJUD XODIMLAR KO'CHADI ===")
db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
# Eski turdagi administrator
u1 = models.User(username="qabul1", password_hash=hash_password("x"),
                 full_name="Qabul Xodimi", role="administrator",
                 branch_id=BID)
# Ikki lavozimli: asosiysi ustoz, qo'shimchasi eski administrator
u2 = models.User(username="ikki", password_hash=hash_password("x"),
                 full_name="Ikki Lavozim", role="teacher", branch_id=BID)
# Ikkalasi ham bor: sales_manager + eski administrator (dubl bo'lmasin)
u3 = models.User(username="uch", password_hash=hash_password("x"),
                 full_name="Uch Lavozim", role="sales_manager",
                 branch_id=BID)
db.add_all([u1, u2, u3])
db.commit()
U1, U2, U3 = u1.id, u2.id, u3.id
db.add(models.UserRole(user_id=U2, role="administrator"))
db.add(models.UserRole(user_id=U3, role="sales_manager"))
db.add(models.UserRole(user_id=U3, role="administrator"))
db.commit()
db.close()

entry._merge_admin_roles()

db = SessionLocal()
ck("asosiy rol ko'chdi",
   db.query(models.User).get(U1).role, "sales_manager")
r2 = [x.role for x in db.query(models.UserRole).filter(
    models.UserRole.user_id == U2).all()]
ck("qo'shimcha rol ko'chdi", r2, ["sales_manager"])
ck("ustozligi saqlandi",
   db.query(models.User).get(U2).role, "teacher")
r3 = sorted(x.role for x in db.query(models.UserRole).filter(
    models.UserRole.user_id == U3).all())
ck("dubl yaratilmadi", r3, ["sales_manager"])
ck("bazada administrator qolmadi",
   db.query(models.User).filter(
       models.User.role == "administrator").count(), 0)
ck("qo'shimcha rollarda ham qolmadi",
   db.query(models.UserRole).filter(
       models.UserRole.role == "administrator").count(), 0)
db.close()

print("\n=== 5. KO'CHGAN XODIM MUZLATA VA FAOLLASHTIRA OLADI ===")
db = SessionLocal()
t = models.Teacher(full_name="Ustoz", branch_id=BID, is_active=1,
                   grade="senior",
                   hired_date=date.today() - timedelta(days=400))
db.add(t)
db.commit()
g = models.Group(name="Kids", teacher_id=t.id, branch_id=BID,
                 subject="english", lesson_days="mon,wed,fri",
                 lesson_time="09:00",
                 start_date=date.today() - timedelta(days=60),
                 lesson_price=40000, monthly_fee=480000,
                 standard_lessons_per_month=12)
db.add(g)
db.commit()
st = models.Student(full_name="Bola", branch_id=BID, group_id=g.id,
                    status="active",
                    enrolled_date=date.today() - timedelta(days=60))
db.add(st)
db.commit()
SID = st.id
db.close()

QB = tok("qabul1")
until = (date.today() + timedelta(days=20)).isoformat()
r = client.post(f"/api/students/{SID}/freeze", headers=QB,
                json={"until": until, "reason": "travel"})
ck("muzlatdi", r.status_code, 200)
db = SessionLocal()
ck("holati muzlatilgan",
   db.query(models.Student).get(SID).status, "frozen")
db.close()

r = client.post(f"/api/students/{SID}/activate", headers=QB, json={})
ck("MUZLATISHDAN CHIQARDI", r.status_code, 200)
db = SessionLocal()
ck("holati faol", db.query(models.Student).get(SID).status, "active")
db.close()

print("\n=== 6. IDEMPOTENT VA BOSHQALARGA TEGMAYDI ===")
db = SessionLocal()
before = sorted((u.username, u.role) for u in
                db.query(models.User).all())
db.close()
entry._merge_admin_roles()
entry._merge_admin_roles()
db = SessionLocal()
after = sorted((u.username, u.role) for u in
               db.query(models.User).all())
db.close()
ck("qayta chaqirilsa hech nima o'zgarmaydi", after, before)
ck("asoschi o'z rolida", [r for u, r in after if u == "asos"],
   ["founder"])
ck("ustoz o'z rolida", [r for u, r in after if u == "ikki"],
   ["teacher"])

print("\n=== 7. YANGI XODIMGA ESKI ROL BERIB BO'LMAYDI ===")
H = tok("asos")
r = client.post("/api/users", headers=H, json={
    "username": "yangi.qabul", "password": "Parol1234",
    "full_name": "Yangi Qabul", "role": "administrator",
    "branch_id": BID})
ck("rad etiladi", r.status_code in (400, 422), True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
