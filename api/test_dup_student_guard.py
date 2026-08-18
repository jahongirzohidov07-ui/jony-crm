"""DUBLIKAT O'QUVCHI QO'SHILISHINING OLDINI OLISH (2026-08-18).

Jahongir: "qara shu boymirzayev Bekzod degan o'quvchi yoqolib qolib bir
paydo bolib qolyabdi, keyi yana men qoshib qoydim deyabdi admin".

Sabab: o'quvchi 3 darsga ketma-ket kelmagani uchun AVTOMUZLATILGAN
bo'lgan. Muzlatilgan o'quvchi faol ro'yxatda ko'rinmaydi — admin uni
topolmay yangi karta ochib yuborgan. Bitta bolaga ikkita yozuv.

Test aynan shu holatni takrorlaydi va tizim endi to'sishini tekshiradi.
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/dupguard.db"
if os.path.exists("/tmp/dupguard.db"):
    os.remove("/tmp/dupguard.db")
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
b = models.Branch(name="Bekobod 2"); db.add(b); db.commit(); BID = b.id
# Muzlatilgan o'quvchi — aynan Bekzodning holati
frozen = models.Student(full_name="Boymirzaev Bekzodbek Ravshan o'g'li",
                        phone="+(998) 90-119-36-89", branch_id=BID,
                        status="frozen")
arch = models.Student(full_name="Ketgan Bola", phone="998901112233",
                      branch_id=BID, status="archived")
db.add_all([frozen, arch]); db.commit()
FID = frozen.id
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("x"),
                   role=roles.FOUNDER, branch_id=BID))
db.commit(); db.close()

tok = c.post("/api/auth/login",
             json={"username": "asos", "password": "x"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}


def add(name, phone, force=False, parent=None):
    body = {"full_name": name, "phone": phone, "branch_id": BID}
    if parent:
        body["parent_phone"] = parent
    url = "/api/students" + ("?force=true" if force else "")
    return c.post(url, json=body, headers=H)


# ---------------------------------------------------------------- 1
print("\n=== 1. Muzlatilgan o'quvchi, ismi boshqacha yozilgan ===")
r = add("Boymirzaev Bekzod", "901193689")
ck("to'sildi (409)", r.status_code, 409)
msg = r.json().get("detail", "")
ck("telefon bo'yicha topilgani aytildi", "TELEFON RAQAM" in msg, True)
ck("eski karta raqami ko'rsatildi", f"#{FID}" in msg, True)
ck("MUZLATILGAN deb ogohlantirildi", "MUZLATILGAN" in msg, True)
ck("tiklashga yo'naltirildi", "TIKLANG" in msg, True)
db = SessionLocal()
ck("bazaga yangi yozuv tushmadi",
   db.query(models.Student).count(), 2)
db.close()

# ---------------------------------------------------------------- 2
print("\n=== 2. Arxivdagi o'quvchi ham ushlanadi ===")
r = add("Boshqa Ism", "+998 90 111 22 33")
ck("to'sildi", r.status_code, 409)
ck("ARXIVDA deyildi", "ARXIVDA" in r.json().get("detail", ""), True)

# ---------------------------------------------------------------- 3
print("\n=== 3. Ota-ona raqami ham hisobga olinadi ===")
r = add("Yana Boshqa", "998905550001", parent="998901193689")
# ota-ona raqami bir xil bo'lsa ham ogohlantiradi
ck("to'sildi", r.status_code, 409)
ck("dublikat deb ushlandi", "allaqachon bor" in r.json().get("detail",""), True)

# ---------------------------------------------------------------- 4
print("\n=== 4. Haqiqatan yangi odam — bemalol kiradi ===")
r = add("Yangi Bola", "998935550022")
ck("qo'shildi", r.status_code, 200)
db = SessionLocal()
ck("bazada 3 ta bo'ldi", db.query(models.Student).count(), 3)
db.close()

# ---------------------------------------------------------------- 5
print("\n=== 5. Tasdiqlansa (force) — baribir kiritiladi ===")
r = add("Boymirzaev Bekzod", "901193689", force=True)
ck("tasdiq bilan o'tdi", r.status_code, 200)
db = SessionLocal()
ck("bazada 4 ta", db.query(models.Student).count(), 4)
ck("eski yozuv o'z holicha", db.query(models.Student).get(FID).status,
   "frozen")
db.close()

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
