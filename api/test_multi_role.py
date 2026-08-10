"""KO'P LAVOZIMLI XODIM (2026-08-10).

Jahongir: "bir xodim bir nechta lavozim qo'shsak bo'ladimi, filial
almashtirgandek lavozimini almashtirib kiraverardi. Masalan HR
managerimiz Support managerlik ishini ham qiladi; Go'zal teacher
ham o'quv bo'limi lavozimini bajaradi; Nodir filial rahbari ham,
ustoz ham; Zafar filial rahbari ham, moliyachi ham, xo'jalik
ishlari rahbari ham."

QOIDA (Jahongir tanladi): FAQAT TANLANGAN LAVOZIM huquqi ishlaydi —
lavozimlar birlashmaydi. Shuning uchun xodim bir vaqtda faqat bitta
"rolda" bo'ladi va tasodifan ortiqcha ma'lumot ko'rmaydi.

ENG MUHIM TEKSHIRUV — XAVFSIZLIK: X-Active-Role sarlavhasi mijozdan
keladi, ya'ni uni qo'lda o'zgartirish mumkin. Server unga KO'R-KO'RONA
ISHONMASLIGI kerak: so'ralgan lavozim xodimga HAQIQATAN berilgan
bo'lsagina qabul qilinadi."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/vmr/db.sqlite"
os.makedirs("/tmp/vmr", exist_ok=True)
if os.path.exists("/tmp/vmr/db.sqlite"):
    os.remove("/tmp/vmr/db.sqlite")
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


b = models.Branch(name="Zafar"); db.add(b); db.commit()


def mk(uname, role, extra=()):
    u = models.User(username=uname, full_name=f"X {uname}",
                    password_hash=hash_password("Parol123!"),
                    role=role, branch_id=b.id, is_active=1)
    db.add(u); db.commit()
    for r in extra:
        db.add(models.UserRole(user_id=u.id, role=r))
    db.commit()
    return u


# Go'zal: ustoz + o'quv bo'limi rahbari
gozal = mk("gozal", roles.TEACHER, [roles.ACADEMIC_HEAD])
t = models.Teacher(full_name="X gozal", branch_id=b.id,
                   user_id=gozal.id, is_active=1)
db.add(t); db.commit()
# Oddiy ustoz (qo'shimcha lavozimsiz)
mk("ust", roles.TEACHER)


def tok(u):
    return c.post("/api/auth/login",
                  json={"username": u, "password": "Parol123!"}
                  ).json()["access_token"]


TG = tok("gozal")
TU = tok("ust")


def H(t_, role=None):
    h = {"Authorization": f"Bearer {t_}"}
    if role:
        h["X-Active-Role"] = role
    return h


print("=== /api/me LAVOZIMLAR RO'YXATI ===")
r = c.get("/api/me", headers=H(TG))
d = r.json()
ck("asosiy lavozim ustoz", d["role"], roles.TEACHER)
keys = [x["key"] for x in d.get("roles", [])]
ck("ikkala lavozim qaytadi", keys, [roles.TEACHER, roles.ACADEMIC_HEAD])

r = c.get("/api/me", headers=H(TU))
ck("bitta lavozimli xodimda faqat bitta", len(r.json().get("roles", [])), 1)

print("\n=== LAVOZIM ALMASHTIRISH ISHLAYDI ===")
# O'quv bo'limi rahbari /api/support/teachers ni ko'radi, ustoz — yo'q
r = c.get("/api/support/teachers", headers=H(TG))
ck("USTOZ sifatida support ro'yxati YOPIQ", r.status_code, 403)
r = c.get("/api/support/teachers", headers=H(TG, roles.ACADEMIC_HEAD))
ck("O'QUV BO'LIMI sifatida OCHIQ", r.status_code, 200)

r = c.get("/api/me", headers=H(TG, roles.ACADEMIC_HEAD))
ck("/api/me ham yangi lavozimni ko'rsatadi",
   r.json()["role"], roles.ACADEMIC_HEAD)

print("\n=== XAVFSIZLIK: BERILMAGAN LAVOZIMNI SO'RASH ===")
# Ustozda qo'shimcha lavozim YO'Q — asoschi bo'lib ko'rinmoqchi
r = c.get("/api/me", headers=H(TU, roles.FOUNDER))
ck("berilmagan lavozim QABUL QILINMAYDI (ustozligicha qoladi)",
   r.json()["role"], roles.TEACHER)

# Eng xavflisi: asoschi huquqini o'g'irlashga urinish
r = c.get("/api/users", headers=H(TU, roles.FOUNDER))
ck("soxta asoschi bilan xodimlar ro'yxati OCHILMAYDI",
   r.status_code, 403)

# Go'zalda o'quv bo'limi bor, lekin ASOSCHI yo'q
r = c.get("/api/users", headers=H(TG, roles.FOUNDER))
ck("berilgan lavozimdan tashqarisi ham OCHILMAYDI", r.status_code, 403)

print("\n=== HR + SUPPORT MENEJER (Jahongir aytgan holat) ===")
hr = mk("hr", roles.HR_MANAGER, [roles.HEAD_SUPPORT])
THR = tok("hr")
r = c.get("/api/users", headers=H(THR))
ck("HR sifatida xodimlar ro'yxati ochiladi", r.status_code, 200)
r = c.get("/api/support/teachers", headers=H(THR, roles.HEAD_SUPPORT))
ck("support boshlig'i sifatida support ro'yxati ochiladi",
   r.status_code, 200)

print("\n=== UCH LAVOZIMLI XODIM (Zafar filial rahbari) ===")
zafar = mk("zafar", roles.BRANCH_MANAGER,
           [roles.FINANCE_DIRECTOR, roles.FACILITY_MANAGER])
TZ = tok("zafar")
r = c.get("/api/me", headers=H(TZ))
ck("uchala lavozim qaytadi", len(r.json()["roles"]), 3)
for want in (roles.BRANCH_MANAGER, roles.FINANCE_DIRECTOR,
             roles.FACILITY_MANAGER):
    r = c.get("/api/me", headers=H(TZ, want))
    ck(f"  {roles.UZ_LABELS.get(want, want)} ga o'tadi",
       r.json()["role"], want)

print("\n=== HR QO'SHIMCHA LAVOZIM BERA OLADI ===")
r = c.get("/api/users", headers=H(THR))
row = next(x for x in r.json() if x["username"] == "gozal")
ck("ro'yxatda qo'shimcha lavozim ko'rinadi",
   row.get("extra_roles"), [roles.ACADEMIC_HEAD])

r = c.put(f"/api/users/{gozal.id}", headers=H(THR),
          json={"extra_roles": [roles.ACADEMIC_HEAD, roles.EXAMINER]})
ck("HR lavozim qo'sha oladi", r.status_code, 200)
r = c.get("/api/me", headers=H(TG))
ck("endi uchta lavozim", len(r.json()["roles"]), 3)

r = c.put(f"/api/users/{gozal.id}", headers=H(THR),
          json={"extra_roles": []})
ck("HR lavozimni olib ham tashlaydi", r.status_code, 200)
r = c.get("/api/me", headers=H(TG))
ck("faqat asosiysi qoldi", len(r.json()["roles"]), 1)
r = c.get("/api/support/teachers", headers=H(TG, roles.ACADEMIC_HEAD))
ck("olib tashlangan lavozim endi ISHLAMAYDI", r.status_code, 403)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
