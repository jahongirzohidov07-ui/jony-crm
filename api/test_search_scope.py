"""GLOBAL QIDIRUV: FILIAL DOIRASI VA XODIMLAR (2026-08-18).

Jahongir: "kimdur qidirsa o'z filialidagi o'quvchilarni chiqarginda
faqat asoschi barcha filiallarda turganda yoki boshqa xodim barcha
filiallarda turganda qidiruv qilsa barcha filiallardagi oquvchilari
chiqarsin va qidiruvda xodimlar chiqmasin".

Bu shunchaki qulaylik emas — aynan shu chalkashlik Boymirzaev Bekzod
voqeasini keltirib chiqargan: Bekobod 2 da qidirilganda Zafar
filialidagi boshqa bola chiqib, "shu bola muzlab qolibdi" degan
noto'g'ri xulosa chiqarilgan.
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/searchscope.db"
if os.path.exists("/tmp/searchscope.db"):
    os.remove("/tmp/searchscope.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
z = models.Branch(name="Zafar"); b2 = models.Branch(name="Bekobod 2")
db.add_all([z, b2]); db.commit()
Z, B2 = z.id, b2.id
db.add_all([
    models.Student(full_name="Boymirzaev Bekzodbek Ravshan o'g'li",
                   phone="+(998) 90-119-36-89", branch_id=Z,
                   status="frozen"),
    models.Student(full_name="Boymirzaev Bekzod", phone="901193689",
                   branch_id=B2, status="active"),
])
# Xodim — ismi ham "Boymirzaev", qidiruvda CHIQMASLIGI kerak
db.add(models.User(username="boymirza_xodim",
                   full_name="Boymirzaev Xodim",
                   password_hash=hash_password("x"),
                   role=roles.ADMINISTRATOR, branch_id=B2))
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("x"),
                   role=roles.FOUNDER, branch_id=B2))
db.add(models.User(username="admin2", full_name="Bekobod Admin",
                   password_hash=hash_password("x"),
                   role=roles.ADMINISTRATOR, branch_id=B2))
db.commit(); db.close()


def tok(u):
    return c.post("/api/auth/login",
                  json={"username": u, "password": "x"}).json()["access_token"]


ASOS = {"Authorization": f"Bearer {tok('asos')}"}
ADM = {"Authorization": f"Bearer {tok('admin2')}"}


def find(H, branch=None):
    url = "/api/search/students?q=Boymirza"
    if branch:
        url += f"&branch_id={branch}"
    r = c.get(url, headers=H).json()
    return r


# ---------------------------------------------------------------- 1
print("\n=== 1. Asoschi 'Barcha filiallar'da — hammasi chiqadi ===")
r = find(ASOS)
ck("2 ta o'quvchi", len(r["students"]), 2)
ck("ikkala filial ham", sorted(s["name"][:20] for s in r["students"]),
   ["Boymirzaev Bekzod", "Boymirzaev Bekzodbek"])

# ---------------------------------------------------------------- 2
print("\n=== 2. Asoschi 'Bekobod 2'da — faqat o'sha filial ===")
r = find(ASOS, B2)
ck("1 ta o'quvchi", len(r["students"]), 1)
ck("aynan Bekobod 2 niki", r["students"][0]["name"], "Boymirzaev Bekzod")

print("\n=== 2b. Asoschi 'Zafar'da — faqat Zafar ===")
r = find(ASOS, Z)
ck("1 ta o'quvchi", len(r["students"]), 1)
ck("aynan Zafarniki",
   r["students"][0]["name"], "Boymirzaev Bekzodbek Ravshan o'g'li")

# ---------------------------------------------------------------- 3
print("\n=== 3. Bekobod 2 admini — boshqa filialni ko'rmaydi ===")
r = find(ADM)
ck("faqat 1 ta", len(r["students"]), 1)
ck("o'z filiali", r["students"][0]["name"], "Boymirzaev Bekzod")

print("\n=== 3b. Admin Zafarni so'rasa ham — o'ziniki qaytadi ===")
r = find(ADM, Z)
ck("chetga chiqmadi", len(r["students"]), 1)
ck("baribir o'ziniki", r["students"][0]["name"], "Boymirzaev Bekzod")

# ---------------------------------------------------------------- 4
print("\n=== 4. Xodimlar qidiruvda chiqmaydi ===")
for nm, H in (("asoschi", ASOS), ("admin", ADM)):
    r = find(H)
    ck(f"{nm}: xodim ro'yxati bo'sh", len(r.get("staff") or []), 0)
    ck(f"{nm}: xodim ismi natijada yo'q",
       any("Xodim" in s["name"] for s in r["students"]), False)

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
