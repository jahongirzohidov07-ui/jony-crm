"""LC UP TO'LOV TARIXINI KO'CHIRISH (2026-08-18).

Jahongir: "LC upda hammasini togrlab qoydim sen uni toliq kochirib ber
JonyOS ga tolovlar tarixini".

Ikki narsa tekshiriladi:

 1) BALANS BUZILMAYDI. Har ko'chirilgan to'lov yoniga o'sha kunning
    "hisoblangani" ham yoziladi — ya'ni tarix ko'rinadi, lekin qarz
    o'zgarmaydi. Bu eng muhim shart: eski tarix bugungi qarzni
    aralashtirib yubormasligi kerak.

 2) KETGAN O'QUVCHI YO'QOLMAYDI. LC UP'da to'lagan, lekin JonyOS'da
    umuman yo'q odam "create_missing" bilan ARXIV o'quvchi bo'lib
    ochiladi va to'lovi o'shanga ilinadi. Faol ro'yxatga aralashmaydi.
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/lcuphist.db"
if os.path.exists("/tmp/lcuphist.db"):
    os.remove("/tmp/lcuphist.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402
from common import student_balance                 # noqa: E402

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
s = models.Student(full_name="Abduvalieva Munisa", phone="998940411480",
                   branch_id=BID, status="active")
db.add(s); db.commit(); SID = s.id
u = models.User(username="asos", full_name="Asoschi",
                password_hash=hash_password("x"), role=roles.FOUNDER,
                branch_id=BID)
db.add(u); db.commit()
db.close()

tok = c.post("/api/auth/login",
             json={"username": "asos", "password": "x"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

ROWS = [
    {"name": "Abduvalieva Munisa", "phone": "+998 94 041 14 80",
     "date": "2026-07-07", "amount": "432000", "method": "Plastik karta"},
    {"name": "Abduvalieva Munisa", "phone": "+998 94 041 14 80",
     "date": "2026-06-05", "amount": "480000", "method": "Naqd"},
    {"name": "Ketgan Odam", "phone": "+998 90 111 22 33",
     "date": "2026-05-04", "amount": "300000", "method": "Naqd"},
]

# ---------------------------------------------------------------- 1
print("\n=== 1. Tekshirish rejimi (hech narsa yozilmaydi) ===")
r = c.post("/api/lcup/payments",
           json={"rows": ROWS, "commit": False, "create_missing": True},
           headers=H)
ck("tekshirish javobi 200", r.status_code, 200)
j = r.json()
ck("3 qator tayyor (2 topildi + 1 ochiladi)", j["ok"], 3)
ck("1 ta arxivga ochiladi", j["created"], 1)
db = SessionLocal()
ck("baza toza qoldi", db.query(models.Payment).count(), 0)
ck("yangi o'quvchi ochilmadi", db.query(models.Student).count(), 1)
db.close()

# ---------------------------------------------------------------- 2
print("\n=== 2. Ko'chirish ===")
r = c.post("/api/lcup/payments",
           json={"rows": ROWS, "commit": True, "create_missing": True},
           headers=H)
ck("ko'chirish javobi 200", r.status_code, 200)
j = r.json()
ck("3 tasi ham ko'chdi", j["ok"], 3)
ck("1 ta arxiv ochildi", j["created"], 1)

db = SessionLocal()
ck("balans o'zgarmadi", student_balance(db, SID), 0)
pays = db.query(models.Payment).filter(
    models.Payment.student_id == SID).all()
ck("Munisada 4 yozuv (2 to'lov + 2 hisob)", len(pays), 4)
ck("to'lovlar yig'indisi", sum(p.amount for p in pays if p.kind == "payment"),
   912000)
ck("hisoblar yig'indisi", sum(p.amount for p in pays if p.kind == "charge"),
   -912000)
ck("sana saqlandi",
   sorted({p.created_at.date().isoformat() for p in pays}),
   ["2026-06-05", "2026-07-07"])
ck("usul o'qildi",
   sorted({p.method for p in pays if p.kind == "payment"}),
   ["card", "cash"])

arх = db.query(models.Student).filter(
    models.Student.full_name == "Ketgan Odam").first()
ck("ketgan odam ochildi", arх is not None, True)
ck("u arxivda", arх.status, "archived")
ck("uning to'lovi bor",
   db.query(models.Payment).filter(
       models.Payment.student_id == arх.id,
       models.Payment.kind == "payment").count(), 1)
ck("uning balansi ham 0", student_balance(db, arх.id), 0)
db.close()

# ---------------------------------------------------------------- 3
print("\n=== 3. Ikkinchi marta bosilsa — takrorlanmaydi ===")
r = c.post("/api/lcup/payments",
           json={"rows": ROWS, "commit": True, "create_missing": True},
           headers=H)
j = r.json()
ck("yangi yozuv yo'q", j["ok"], 0)
ck("takror deb belgilandi", j["duplicate"], 3)
db = SessionLocal()
ck("baza o'smadi", db.query(models.Payment).count(), 6)
ck("o'quvchi soni o'smadi", db.query(models.Student).count(), 2)
db.close()

# ---------------------------------------------------------------- 4
print("\n=== 4. create_missing yo'q bo'lsa — ochilmaydi ===")
r = c.post("/api/lcup/payments",
           json={"rows": [{"name": "Boshqa Ketgan", "date": "2026-04-01",
                           "amount": "100000"}],
                 "commit": True, "create_missing": False}, headers=H)
j = r.json()
ck("topilmadi deb qaytdi", j["not_found"], 1)
ck("hech kim ochilmadi", j["created"], 0)
db = SessionLocal()
ck("o'quvchi soni o'zgarmadi", db.query(models.Student).count(), 2)
db.close()

# ---------------------------------------------------------------- 5
print("\n=== 5. Bekor qilish — hammasi orqaga ===")
r = c.delete("/api/lcup/payments", headers=H)
ck("bekor qilindi", r.status_code, 200)
db = SessionLocal()
ck("LC UP yozuvlari o'chdi", db.query(models.Payment).count(), 0)
ck("balans yana 0", student_balance(db, SID), 0)
db.close()

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
