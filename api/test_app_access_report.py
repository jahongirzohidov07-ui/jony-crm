"""JONY STUDENT APP: KIRISH CHEKLOVI VA HISOBOT (2026-08-25).

Jahongir: "hisobotlar bo'limida Jony Student app hisobotlari kerak
yani nechta o'quvchi akkauntiga kirdi ulandi, nechtasi hali umuman
kirib kormadi, nechtasi har kun kiryabdi nechtasi faol shunaqa
nechtasi qaysi darajaga keldi shunaqa korsatkichlar kerak ... keyin
akkaunti muzlatilsa yoki darsdan chiqib ketsa bu appga kirmay
qolishi kerak".

BU TEST NIMANI ISBOTLAYDI:
  * faol o'quvchi ilovaga kiradi;
  * MUZLATILGAN o'quvchi kira olmaydi va tushunarli sabab oladi;
  * guruhdan CHIQARILGAN (left) va ARXIVDAGI ham kira olmaydi;
  * ESKI TOKEN ham ishlamay qoladi (bola ichkarida qolib ketmaydi);
  * holat qaytsa — kirish O'ZI tiklanadi, hech nima o'chirilmaydi;
  * xodimlar (ustoz/admin) bu cheklovdan ta'sirlanmaydi;
  * hisobotda daraja, kunlik faollik, ko'nikma va liga kesimlari bor.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_acc/db.sqlite"
os.makedirs("/tmp/verify_acc", exist_ok=True)
if os.path.exists("/tmp/verify_acc/db.sqlite"):
    os.remove("/tmp/verify_acc/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta
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


def login(uname, pw="Parol123!"):
    return c.post("/api/auth/login",
                  json={"username": uname, "password": pw})


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()

# Asoschi — hisobot uchun
fu = models.User(username="asos", full_name="Asoschi",
                 password_hash=hash_password("Parol123!"),
                 role=roles.FOUNDER, branch_id=b.id, is_active=1)
db.add(fu); db.commit()
FH = {"Authorization": "Bearer " + login("asos").json()["access_token"]}

# To'rt o'quvchi: faol, muzlatilgan, chiqib ketgan, arxiv
students = {}
for key, status in (("faol", "active"), ("muz", "frozen"),
                    ("ketgan", "left"), ("arxiv", "archived")):
    st = models.Student(full_name=f"O'quvchi {key}", branch_id=b.id,
                        status=status)
    db.add(st); db.commit()
    u = models.User(username=key, full_name=st.full_name,
                    password_hash=hash_password("Parol123!"),
                    role=roles.STUDENT, branch_id=b.id, is_active=1)
    db.add(u); db.commit()
    st.user_id = u.id; db.commit()
    students[key] = st.id

# Ustoz — cheklov unga tegmasligi kerak
t = models.User(username="ustoz", full_name="Ustoz",
                password_hash=hash_password("Parol123!"),
                role=roles.TEACHER, branch_id=b.id, is_active=1)
db.add(t); db.commit()
db.close()

print("=== 1. FAOL O'QUVCHI KIRADI ===")
r = login("faol")
ck("kirish 200", r.status_code, 200)
SH = {"Authorization": "Bearer " + r.json()["access_token"]}
ck("bosh sahifa ochiladi",
   c.get("/api/student/home", headers=SH).status_code, 200)

print("\n=== 2. MUZLATILGAN KIRA OLMAYDI ===")
r = login("muz")
ck("kirish rad etiladi", r.status_code, 403)
ck("sabab muzlatilgani haqida",
   "muzlatilgan" in r.json()["detail"].lower(), True)
ck("qachon ochilishi ham aytiladi",
   "o'zi ochiladi" in r.json()["detail"], True)

print("\n=== 3. CHIQIB KETGAN VA ARXIVDAGI HAM KIRA OLMAYDI ===")
r = login("ketgan")
ck("chiqib ketgan rad", r.status_code, 403)
ck("sababda guruh aytiladi", "guruh" in r.json()["detail"].lower(), True)
r = login("arxiv")
ck("arxivdagi rad", r.status_code, 403)
ck("sababda arxiv aytiladi", "arxiv" in r.json()["detail"].lower(), True)

print("\n=== 4. ESKI TOKEN HAM ISHLAMAY QOLADI ===")
# faol o'quvchi ichkarida turganida muzlatiladi
dbx = SessionLocal()
st = dbx.query(models.Student).get(students["faol"])
st.status = "frozen"; dbx.commit(); dbx.close()
r = c.get("/api/student/home", headers=SH)
ck("eski token bilan ham yopiq", r.status_code, 403)
ck("xabar tushunarli", "muzlatilgan" in r.json()["detail"].lower(), True)
r = c.get("/api/student/skills", headers=SH)
ck("boshqa bo'limlar ham yopiq", r.status_code, 403)

print("\n=== 5. HOLAT QAYTSA — O'ZI OCHILADI ===")
dbx = SessionLocal()
st = dbx.query(models.Student).get(students["faol"])
st.status = "active"; dbx.commit(); dbx.close()
ck("eski token yana ishlaydi",
   c.get("/api/student/home", headers=SH).status_code, 200)
ck("qayta kirish ham ishlaydi", login("faol").status_code, 200)
# Hisob O'CHIRILMAGAN — hech qanday ma'lumot yo'qolmagan
dbx = SessionLocal()
ck("hisob o'chirilmagan (faqat holat tekshiriladi)",
   dbx.query(models.User).filter(
       models.User.username == "muz").first().is_active, 1)
dbx.close()

print("\n=== 6. XODIMLARGA CHEKLOV TEGMAYDI ===")
ck("ustoz kiradi", login("ustoz").status_code, 200)
ck("asoschi kiradi", login("asos").status_code, 200)

print("\n=== 7. HISOBOT: YANGI KO'RSATKICHLAR ===")
# faol o'quvchiga mashq va kirish tarixini beramiz
dbx = SessionLocal()
sid = students["faol"]
for i in range(950):
    dbx.add(models.GrammarAttempt(student_id=sid, question_id=i + 1,
                                  correct=1, date=date.today()))
now = datetime.utcnow()
for k in range(28):        # 28 kun — "deyarli har kuni"
    dbx.add(models.VocabAttempt(student_id=sid, word_id=k + 1,
                                game="en_uz", correct=1,
                                date=date.today(),
                                created_at=now - timedelta(days=k)))
dbx.commit(); dbx.close()

r = c.get("/api/reports/student-app-usage", headers=FH)
ck("hisobot 200", r.status_code, 200)
d = r.json()
for key in ("levels", "skills", "activity", "leagues", "idle_list",
            "idle_count", "blocked", "active_days_avg"):
    ck(f"javobda '{key}' bor", key in d, True)

print("\n--- daraja taqsimoti ---")
ck("7 ta daraja", len(d["levels"]), 7)
ck("daraja yig'indisi = faol o'quvchilar",
   sum(x["students"] for x in d["levels"]), d["total"])
lv = {x["key"]: x["students"] for x in d["levels"]}
ck("950 ball -> Elementary'da 1 ta", lv["elementary"], 1)

print("\n--- kunlik faollik ---")
act = {x["key"]: x["students"] for x in d["activity"]}
ck("faollik yig'indisi = jami", sum(act.values()), d["total"])
ck("28 kun ishlagan -> 'deyarli har kuni'", act["daily"], 1)
ck("o'rtacha faol kun hisoblanadi", d["active_days_avg"] >= 28, True)

print("\n--- ko'nikma kesimi ---")
ck("6 ta ko'nikma", len(d["skills"]), 6)
sk = {x["key"]: x for x in d["skills"]}
ck("grammatikada o'rtacha ball bor", sk["grammar"]["avg_score"] > 0, True)
ck("o'qishga umuman tegilmagan",
   sk["reading"]["untouched"], d["total"])
ck("o'qish o'rtacha bali 0", sk["reading"]["avg_score"], 0.0)

print("\n--- ilovasi yopilganlar ---")
# muzlatilgan + chiqib ketgan = 2 (arxiv OPEN_STATUSES ga kirmaydi)
ck("yopilganlar sanaladi", d["blocked"], 2)

print("\n=== 8. HISOBOT XODIMLARGA YOPIQ ===")
th = {"Authorization": "Bearer " + login("ustoz").json()["access_token"]}
ck("ustozga hisobot yopiq",
   c.get("/api/reports/student-app-usage", headers=th).status_code, 403)

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
