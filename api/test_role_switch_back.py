"""IKKI LAVOZIMLI XODIM: USTOZGA O'TGACH QAYTA OLADIMI (2026-08-25).

Jahongir: "qara 2ta lavozimi borlar ustoz va manager yoki ustoz va
o'quv bolimi rahbari yoki filial rahbari lavozim lamashtirish
funksiyasi bor edi lekin ustoz lavozimiga otsa manager lavozimi
yoqolib qolibdi kira olmayabdi ekan".

XATO NIMADA EDI. /api/me lavozimlar ro'yxatini _user_roles() dan
oladi, u esa ro'yxatni user.role dan boshlardi. Lavozim
almashtirilganda auth.py so'rov davomida user.role ni TANLANGAN
lavozimga o'zgartiradi — natijada ustozga o'tgan zahoti asosiy
lavozim ro'yxatdan tushib qolardi, ekrandagi tanlagich yo'qolardi
va xodim ustoz kabinetida qamalib qolardi.

BU TEST NIMANI ISBOTLAYDI:
  * asosiy lavozimda ikkala lavozim ham ko'rinadi;
  * USTOZGA o'tgach ham ikkalasi ro'yxatda QOLADI (asosiy xato);
  * ustozga o'tganda huquqlar haqiqatan ustoznikiga tushadi;
  * asosiy lavozimga QAYTIB kelib bo'ladi va huquqlar tiklanadi;
  * uchta juftlik ham ishlaydi: ustoz+filial rahbari,
    ustoz+o'quv bo'limi rahbari, ustoz+sotuv menejeri;
  * begona lavozimni sarlavha bilan qo'lda yozib huquq oshirib
    bo'lmaydi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_role/db.sqlite"
os.makedirs("/tmp/verify_role", exist_ok=True)
if os.path.exists("/tmp/verify_role/db.sqlite"):
    os.remove("/tmp/verify_role/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
BID = b.id

# Uch xil juftlik — Jahongir sanab o'tgan uchtasi
PAIRS = [
    ("nodir", roles.BRANCH_MANAGER, roles.TEACHER, "filial rahbari"),
    ("gozal", roles.ACADEMIC_HEAD, roles.TEACHER, "o'quv bo'limi rahbari"),
    ("aziz", roles.SALES_MANAGER, roles.TEACHER, "sotuv menejeri"),
]
for uname, main_role, extra, _lbl in PAIRS:
    u = models.User(username=uname, full_name=uname.title(),
                    password_hash=hash_password("Parol123!"),
                    role=main_role, branch_id=BID, is_active=1)
    db.add(u); db.commit()
    db.add(models.UserRole(user_id=u.id, role=extra)); db.commit()
db.close()


def tok(uname):
    return c.post("/api/auth/login",
                  json={"username": uname, "password": "Parol123!"}
                  ).json()["access_token"]


for uname, main_role, extra, lbl in PAIRS:
    print(f"\n=== {uname.title()} — {lbl} + ustoz ===")
    T = tok(uname)
    H = {"Authorization": f"Bearer {T}"}
    HT = dict(H); HT["X-Active-Role"] = roles.TEACHER

    # 1) asosiy lavozimda
    me = c.get("/api/me", headers=H).json()
    keys = [r["key"] for r in me["roles"]]
    ck("asosiy lavozimda 2 ta lavozim ko'rinadi", len(keys), 2)
    ck("asosiy lavozim birinchi", keys[0], main_role)
    ck("ustoz ham ro'yxatda", roles.TEACHER in keys, True)

    # 2) USTOZGA O'TGANDA — aynan shu joyda xato bor edi
    me2 = c.get("/api/me", headers=HT).json()
    keys2 = [r["key"] for r in me2["roles"]]
    ck("USTOZDA HAM 2 ta lavozim qoladi", len(keys2), 2)
    ck(f"{lbl} ro'yxatdan YO'QOLMAYDI", main_role in keys2, True)
    ck("joriy lavozim ustoz", me2["role"], roles.TEACHER)
    ck("lavozim yorlig'i ham to'g'ri",
       me2["role_label"], roles.UZ_LABELS[roles.TEACHER])

    # 3) huquqlar haqiqatan almashadi (menyu shu ro'yxatdan quriladi)
    p_main = c.get("/api/me/permissions", headers=H).json()
    p_teach = c.get("/api/me/permissions", headers=HT).json()
    ck("ruxsatlar asosiy lavozimniki", p_main["role"], main_role)
    ck("ustozga o'tgach ruxsatlar ustozniki", p_teach["role"],
       roles.TEACHER)
    ck("ruxsatlar to'plami haqiqatan boshqacha",
       p_main["perms"] != p_teach["perms"], True)

    # 4) QAYTIB KELISH (sarlavhani olib tashlash = asosiyga qaytish)
    me3 = c.get("/api/me", headers=H).json()
    ck("asosiy lavozimga qaytdi", me3["role"], main_role)
    ck("qaytgach ham 2 ta lavozim", len(me3["roles"]), 2)
    ck("huquqlar tiklandi",
       c.get("/api/me/permissions", headers=H).json()["role"], main_role)

    # 5) sarlavhani ochiq tanlab qaytish ham ishlaydi
    HM = dict(H); HM["X-Active-Role"] = main_role
    ck("sarlavha bilan ham qaytadi",
       c.get("/api/me", headers=HM).json()["role"], main_role)

print("\n=== XAVFSIZLIK: begona lavozim qabul qilinmaydi ===")
H = {"Authorization": f"Bearer {tok('nodir')}"}
HF = dict(H); HF["X-Active-Role"] = roles.FOUNDER
me = c.get("/api/me", headers=HF).json()
ck("asoschi bo'lib ololmaydi", me["role"], roles.BRANCH_MANAGER)
ck("ro'yxatga ham qo'shilmaydi",
   roles.FOUNDER in [r["key"] for r in me["roles"]], False)
HX = dict(H); HX["X-Active-Role"] = "yolq_lavozim"
ck("mavjud bo'lmagan lavozim ham rad etiladi",
   c.get("/api/me", headers=HX).json()["role"], roles.BRANCH_MANAGER)

print("\n=== BITTA LAVOZIMLI XODIMGA TA'SIR YO'Q ===")
db = SessionLocal()
u = models.User(username="oddiy", full_name="Oddiy",
                password_hash=hash_password("Parol123!"),
                role=roles.TEACHER, branch_id=BID, is_active=1)
db.add(u); db.commit(); db.close()
me = c.get("/api/me",
           headers={"Authorization": f"Bearer {tok('oddiy')}"}).json()
ck("bitta lavozim ko'rinadi", len(me["roles"]), 1)
ck("o'sha ustoz", me["roles"][0]["key"], roles.TEACHER)

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
