"""SUPPORT TEACHER BOSHQA FILIALDAGI GURUHI (2026-08-10).

Jahongir: "Supportlarda boshqa filialdagi guruhlari bor, lekin
guruhlarida turibdi. Guruhga kirsa 'guruh boshqa filialda' degan
qizil yozuv chiqayabdi. Supportlarda agar guruhi bir nechta filialda
bo'lsa, filial almashtirish bo'lsin — boshqa xodimlarga o'xshab."

SABAB: supportda ustozdan farqli o'laroq "qo'shimcha filial" degan
alohida sozlama YO'Q — unga shunchaki GURUH biriktiriladi
(SupportAssignment) va o'sha guruh istalgan filialda bo'lishi
mumkin. _user_branch_ids() esa faqat user_branches va
teacher_branches ni o'qirdi, biriktirilgan guruhlarni emas.
Natijada: guruh "Guruhlarim" ro'yxatida KO'RINARDI (u yer
biriktirishga qaraydi), lekin OCHILMASDI (u yer filialga qaraydi).

Endi supportning filiallari biriktirilgan guruhlaridan chiqadi —
shuning uchun ham guruh ochiladi, ham /api/me ikkala filialni
qaytaradi (tepadagi filial almashtirgich shundan chiqadi)."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/vsb/db.sqlite"
os.makedirs("/tmp/vsb", exist_ok=True)
if os.path.exists("/tmp/vsb/db.sqlite"):
    os.remove("/tmp/vsb/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}" + ("" if ok else f"  (kutilgan {w})"))
    if not ok:
        fails.append(n)


bA = models.Branch(name="Filial A")
bB = models.Branch(name="Filial B")
db.add_all([bA, bB]); db.commit()

ut = models.User(username="ust", full_name="Ustoz Anvar",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=bA.id, is_active=1)
db.add(ut); db.commit()
t = models.Teacher(full_name="Ustoz Anvar", branch_id=bA.id,
                   user_id=ut.id, is_active=1)
db.add(t); db.commit()

# SUPPORT: asosiy filiali A, lekin unga B filialidagi guruh ham
# biriktirilgan (haqiqiy hayotdagi holat).
su = models.User(username="sup", full_name="Support Aziza",
                 password_hash=hash_password("Parol123!"),
                 role=roles.SUPPORT_TEACHER, branch_id=bA.id, is_active=1)
db.add(su); db.commit()
st = models.Teacher(full_name="Support Aziza", branch_id=bA.id,
                    user_id=su.id, is_active=1)
db.add(st); db.commit()

gA = models.Group(name="A-guruh", subject="english", level="step1",
                  branch_id=bA.id, teacher_id=t.id, lesson_time="09:00",
                  monthly_fee=500000, lesson_days="mon,wed,fri", capacity=15)
gB = models.Group(name="B-guruh", subject="english", level="step1",
                  branch_id=bB.id, teacher_id=t.id, lesson_time="14:00",
                  monthly_fee=500000, lesson_days="tue,thu", capacity=15)
db.add_all([gA, gB]); db.commit()
db.add(models.SupportAssignment(user_id=su.id, group_id=gA.id))
db.add(models.SupportAssignment(user_id=su.id, group_id=gB.id))
db.commit()

# Boshqa filialdagi, unga BIRIKTIRILMAGAN guruh — ochilmasligi kerak
gC = models.Group(name="C-guruh", subject="english", level="step1",
                  branch_id=bB.id, teacher_id=t.id, lesson_time="18:00",
                  monthly_fee=500000, lesson_days="sat", capacity=15)
db.add(gC); db.commit()


def H(u):
    return {"Authorization": f"Bearer {c.post('/api/auth/login', json={'username':u,'password':'Parol123!'}).json()['access_token']}"}


Hs = H("sup")

print("=== GURUHLARIM RO'YXATI (ilgari ham ishlagan) ===")
r = c.get("/api/me/groups", headers=Hs)
ck("status 200", r.status_code, 200)
names = sorted(g["name"] for g in r.json()["rows"])
ck("ikkala filial guruhi ko'rinadi", names, ["A-guruh", "B-guruh"])

print("\n=== GURUHNI OCHISH (ilgari 403 berardi) ===")
ck("o'z filiali guruhi ochiladi",
   c.get(f"/api/groups/{gA.id}", headers=Hs).status_code, 200)
r = c.get(f"/api/groups/{gB.id}", headers=Hs)
ck("BOSHQA filialdagi biriktirilgan guruh ham ochiladi",
   r.status_code, 200)

print("\n=== DAVOMAT VA SUPPORT DAVOMATI ===")
from datetime import date
today = date.today()
ck("boshqa filial guruhi davomati ochiladi",
   c.get(f"/api/groups/{gB.id}/attendance?year={today.year}"
         f"&month={today.month}", headers=Hs).status_code, 200)

print("\n=== XAVFSIZLIK: BIRIKTIRILMAGAN GURUH ===")
r = c.get(f"/api/groups/{gC.id}", headers=Hs)
ck("biriktirilmagan guruh HAMON ochilmaydi", r.status_code, 403)
ck("sabab 'sizga biriktirilmagan'",
   "biriktirilmagan" in r.json()["detail"], True)

print("\n=== FILIAL ALMASHTIRGICH MA'LUMOTI ===")
r = c.get("/api/me", headers=Hs)
brs = sorted(b["name"] for b in (r.json().get("branches") or []))
ck("ikkala filial qaytadi (tanlagich shundan chiqadi)",
   brs, ["Filial A", "Filial B"])

print("\n=== BITTA FILIALLI SUPPORTDA TANLAGICH CHIQMAYDI ===")
su2 = models.User(username="sup2", full_name="Support Bir",
                  password_hash=hash_password("Parol123!"),
                  role=roles.SUPPORT_TEACHER, branch_id=bA.id, is_active=1)
db.add(su2); db.commit()
db.add(models.SupportAssignment(user_id=su2.id, group_id=gA.id))
db.commit()
r = c.get("/api/me", headers=H("sup2"))
ck("faqat bitta filial qaytadi", len(r.json().get("branches") or []), 1)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
