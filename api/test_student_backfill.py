"""ESKI O'QUVCHILARGA BIR YO'LA AKKAUNT (2026-08-10).

Jahongir: "hop endi o'quvchilarga avtomat login parol qo'yib ber,
loginga nomeri parolga jonyjony."

Tekshiriladi: akkaunti yo'q eski o'quvchilarga ochilishi, telefon
raqami login bo'lishi, jonyjony bilan kirib /student ochilishi,
telefonsizlar ro'yxati asoschiga vazifa bo'lib tushishi, band raqam
va arxivdagilar o'tkazib yuborilishi, ikkinchi chaqiruv hech nima
qilmasligi (idempotent)."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_backfill/db.sqlite"
os.makedirs("/tmp/verify_backfill", exist_ok=True)
if os.path.exists("/tmp/verify_backfill/db.sqlite"):
    os.remove("/tmp/verify_backfill/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
from common import _backfill_student_accounts

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
founder = models.User(username="boss", full_name="Jahongir",
                      password_hash=hash_password("Parol123!"),
                      role=roles.FOUNDER, branch_id=b.id, is_active=1)
db.add(founder); db.commit()


def mk_student(name, tag, phone=None, parent=None, status="active"):
    s = models.Student(full_name=name, branch_id=b.id, status=status,
                       phone=phone, parent_phone=parent,
                       public_id=f"STU-BF-{tag}")
    db.add(s); db.commit(); return s


ali = mk_student("Ali Valiyev", 1, phone="+998 90 123 45 67")
vali = mk_student("Vali Aliyev", 2, parent="998911112233")  # ota raqami
gani = mk_student("G'ani Toshev", 3)                        # telefonsiz
muz = mk_student("Muzlagan Bola", 4, phone="998922223344",
                 status="frozen")
arx = mk_student("Arxiv Bola", 5, phone="998933334455",
                 status="archived")
band = mk_student("Band Raqam", 6, phone="998900000001")
db.add(models.User(username="998900000001", full_name="Kimdir",
                   password_hash=hash_password("x"),
                   role=roles.TEACHER, branch_id=b.id, is_active=1))
db.commit()

print("=== BACKFILL ISHGA TUSHADI ===")
n = _backfill_student_accounts(db)
ck("3 ta akkaunt ochildi (Ali, Vali, Muzlagan)", n, 3)

db.refresh(ali); db.refresh(vali); db.refresh(muz)
db.refresh(gani); db.refresh(arx); db.refresh(band)
ua = db.query(models.User).get(ali.user_id) if ali.user_id else None
ck("Ali logini = raqamlari", ua.username if ua else None, "998901234567")
ck("Ali roli o'quvchi", ua.role if ua else None, roles.STUDENT)
uv = db.query(models.User).get(vali.user_id) if vali.user_id else None
ck("Vali logini = ota raqami", uv.username if uv else None,
   "998911112233")
ck("muzlatilganga ham ochildi", bool(muz.user_id), True)
ck("telefonsizga ochilmadi", gani.user_id, None)
ck("arxivdagiga ochilmadi", arx.user_id, None)
ck("band raqamli o'tkazildi", band.user_id, None)

print("\n=== JONYJONY BILAN KIRISH ===")
r = c.post("/api/auth/login", json={"username": "998901234567",
                                    "password": "jonyjony"})
ck("login 200", r.status_code, 200)
tok = r.json().get("access_token")
H = {"Authorization": f"Bearer {tok}"}
r = c.get("/api/me", headers=H)
ck("roli student", r.json().get("role"), "student")
r = c.get("/api/student/home", headers=H)
ck("Jony Student ochiladi", r.status_code, 200)

print("\n=== TELEFONSIZLAR VAZIFASI ===")
tk = (db.query(models.Task)
      .filter(models.Task.assignee_id == founder.id).first())
ck("asoschiga vazifa tushdi", tk is not None, True)
if tk:
    ck("G'ani ro'yxatda", "G'ani Toshev" in (tk.description or ""), True)
    ck("arxivdagi ro'yxatda YO'Q",
       "Arxiv Bola" in (tk.description or ""), False)

print("\n=== IKKINCHI CHAQIRUV HECH NIMA QILMAYDI ===")
ck("0 ta yangi", _backfill_student_accounts(db), 0)
ck("foydalanuvchilar soni o'zgarmadi",
   db.query(models.User).filter(
       models.User.role == roles.STUDENT).count(), 3)

print("\n=== YANGI O'QUVCHIGA ESKI YO'L ISHLAYVERADI ===")
Hb = {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':'boss','password':'Parol123!'}).json()['access_token']}"}
r = c.post("/api/students", headers=Hb,
           json={"full_name": "Yangi Bola", "branch_id": b.id,
                 "phone": "998944445566", "status": "active"})
ck("o'quvchi qo'shildi", r.status_code in (200, 201), True)
r = c.post("/api/auth/login", json={"username": "998944445566",
                                    "password": "jonyjony"})
ck("yangi o'quvchi darhol kira oladi", r.status_code, 200)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
