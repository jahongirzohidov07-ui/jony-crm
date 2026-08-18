"""LID -> O'QUVCHI: DUBLIKAT, AUDIT, HISOB VA GURUH (2026-08-18).

Jahongir: "shu boymirzayev Bekzod degan o'quvchi yoqolib qolib bir paydo
bolib qolyabdi, keyi yana men qoshib qoydim deyabdi admin".

Tekshirganda ma'lum bo'ldiki karta QO'LDA emas, lid o'quvchiga
aylantirilganda ochilgan. Bu yo'lda:
  - dublikat tekshiruvi YO'Q edi,
  - auditga hech narsa yozilmasdi (shuning uchun "qayerdan paydo
    bo'ldi" degan savolga javob yo'q edi),
  - o'quvchiga hisob ochilmasdi,
  - guruh bog'lanish jadvaliga yozilmasdi.

Shu to'rttasi tekshiriladi.
"""
import os, sys
from datetime import date
os.environ["DATABASE_URL"] = "sqlite:////tmp/leadconv.db"
if os.path.exists("/tmp/leadconv.db"):
    os.remove("/tmp/leadconv.db")
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
b1 = models.Branch(name="Zafar"); b2 = models.Branch(name="Bekobod 2")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
t = models.Teacher(full_name="Sardor", branch_id=B2); db.add(t); db.commit()
g = models.Group(name="New", branch_id=B2, teacher_id=t.id,
                 lesson_price=40000, standard_lessons_per_month=12,
                 monthly_fee=480000)
db.add(g); db.commit(); GID = g.id
# Boshqa filialda MUZLATILGAN o'quvchi — aynan Bekzodning holati
old = models.Student(full_name="Boymirzaev Bekzodbek Ravshan o'g'li",
                     phone="+(998) 90-119-36-89", branch_id=B1,
                     status="frozen")
db.add(old); db.commit(); OLD = old.id
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("x"),
                   role=roles.FOUNDER, branch_id=B2))
db.commit(); db.close()

tok = c.post("/api/auth/login",
             json={"username": "asos", "password": "x"}).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}


def new_lead(name, phone):
    r = c.post("/api/leads", headers=H, json={
        "full_name": name, "phone": phone, "branch_id": B2,
        "address": "14 mkr", "school": "8-maktab", "grade": "7",
        "force": True})
    return r.json()["id"]


# ---------------------------------------------------------------- 1
print("\n=== 1. Bir xil raqamli lid — ogohlantiradi ===")
lid = new_lead("Boymirzaev Bekzod", "901193689")
r = c.post(f"/api/leads/{lid}/convert", headers=H,
           json={"group_id": GID, "enrolled_date": date.today().isoformat()})
ck("to'sildi (409)", r.status_code, 409)
msg = r.json().get("detail", "")
ck("eski karta ko'rsatildi", f"#{OLD}" in msg, True)
ck("MUZLATILGAN deyildi", "MUZLATILGAN" in msg, True)
ck("filiali aytildi", "Zafar" in msg, True)
db = SessionLocal()
ck("yangi o'quvchi ochilmadi", db.query(models.Student).count(), 1)
db.close()

# ---------------------------------------------------------------- 2
print("\n=== 2. Tasdiqlansa — o'tadi va HAMMASI yoziladi ===")
r = c.post(f"/api/leads/{lid}/convert", headers=H,
           json={"group_id": GID, "force": True,
                 "enrolled_date": date.today().isoformat()})
ck("o'tdi", r.status_code, 200)
sid = r.json()["id"]

db = SessionLocal()
st = db.query(models.Student).get(sid)
ck("o'quvchi ochildi", st.full_name, "Boymirzaev Bekzod")
ck("filial lidnikidan olindi", st.branch_id, B2)
ck("izohda manzil/maktab saqlandi",
   "8-maktab" in (st.note or ""), True)

# 1) AUDIT
a = (db.query(models.AuditLog)
     .filter(models.AuditLog.entity == "student",
             models.AuditLog.entity_id == sid).all())
ck("auditga yozildi", len(a), 1)
ck("kim qilgani yozildi", a[0].user_name, "Asoschi")
ck("lid raqami izohda", f"Lid #{lid}" in (a[0].note or ""), True)

# 2) HISOB
ck("o'quvchiga hisob ochildi", bool(st.user_id), True)
if st.user_id:
    ck("login telefon raqami",
       db.query(models.User).get(st.user_id).username, "901193689")

# 3) GURUH BOG'LANISHI
links = (db.query(models.StudentGroupLink)
         .filter(models.StudentGroupLink.student_id == sid).all())
ck("guruh bog'lanishi yozildi", len(links), 1)
ck("to'g'ri guruh", links[0].group_id if links else None, GID)
ck("asosiy guruh belgilandi", st.group_id, GID)
db.close()

# ---------------------------------------------------------------- 3
print("\n=== 3. Ikkinchi marta aylantirib bo'lmaydi ===")
r = c.post(f"/api/leads/{lid}/convert", headers=H, json={"force": True})
ck("to'sildi", r.status_code, 400)

# ---------------------------------------------------------------- 4
print("\n=== 4. Yangi odam — ogohlantirishsiz o'tadi ===")
lid2 = new_lead("Butunlay Yangi", "998935550022")
r = c.post(f"/api/leads/{lid2}/convert", headers=H, json={"group_id": GID})
ck("darrov o'tdi", r.status_code, 200)
db = SessionLocal()
ck("bazada 3 ta o'quvchi", db.query(models.Student).count(), 3)
db.close()

print("\n" + ("HAMMASI JOYIDA" if not fails
              else f"MUAMMO: {len(fails)} ta -> {fails}"))
sys.exit(1 if fails else 0)
