"""VOLONTYOR SUPPORTGA OYLIK HISOBLANMAYDI (2026-09-23).

Jahongir: "valantyor supportlar uchun oylik hisoblanmasligi kerak
baribr hisoblanyabdi".

Seanslar baribir yoziladi (tajriba va daraja ko'tarish uchun kerak),
lekin pul hisobi hamma joyda 0 bo'ladi:
  A. Support o'z sahifasida ("Darslarim") oylik ko'rmaydi;
  B. Ustozlar ro'yxatidagi support oyligi 0;
  C. Moliya -> Ish haqi ro'yxatida ham 0 (qoldiq ham 0);
  D. Junior darajasiga ko'tarilsa — o'sha seanslardan oylik paydo
     bo'ladi (ya'ni 0 qilib qo'yilgani daraja sababli, seans yo'qligi
     sababli emas).
"""
import os
import sys
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "volunteer_salary_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login",
        json={"username": u, "password": "Parol123!"}
    ).json()["access_token"]}


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id

db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("Parol123!"),
                   role=roles.FOUNDER, branch_id=BID, is_active=1))
su = models.User(username="sup", full_name="Support Aziza",
                 password_hash=hash_password("Parol123!"),
                 role=roles.SUPPORT_TEACHER, branch_id=BID, is_active=1)
ut = models.User(username="ust", full_name="Ustoz Anvar",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=BID, is_active=1)
db.add_all([su, ut])
db.commit()
SU_ID = su.id
st = models.Teacher(full_name="Support Aziza", branch_id=BID,
                    user_id=su.id, is_active=1)
tt = models.Teacher(full_name="Ustoz Anvar", branch_id=BID,
                    user_id=ut.id, is_active=1)
db.add_all([st, tt])
db.commit()
SUP_TEACHER_ID = st.id
g = models.Group(name="G1", subject="english", level="B1", branch_id=BID,
                 teacher_id=tt.id, lesson_time="18:00", monthly_fee=500000,
                 lesson_days="135", capacity=15)
db.add(g)
db.commit()
db.add(models.SupportAssignment(user_id=su.id, group_id=g.id))
db.commit()
GID = g.id
db.close()

H = tok("asos")
HS = tok("sup")

# Seans yoziladi — oylik shundan hisoblanadi
r = client.post("/api/me/support-sessions", headers=HS,
                json={"group_id": GID, "start_time": "10:00",
                      "hours": 3, "students_count": 12})
ck("seans yozildi", r.status_code, 200)


def mine():
    return client.get("/api/me/support-sessions", headers=HS).json()


def in_list():
    rows = client.get("/api/support-teachers/salaries", headers=H).json()["rows"]
    return {x["teacher_id"]: x for x in rows}[SUP_TEACHER_ID]


def in_payroll():
    rows = client.get("/api/support/salary", headers=H).json()["rows"]
    return {x["name"]: x for x in rows}["Support Aziza"]


print("\n=== A. VOLONTYOR — O'Z SAHIFASI ===")
d = mine()
ck("volontyor deb belgilandi", d.get("volunteer"), True)
ck("oylik hisoblanmadi", d["salary"], 0)
ck("hisob summasi ham 0", d["raw"], 0)
ck("eng kam oylik ogohlantirishi yo'q", d["clamped_min"], False)
ck("seans baribir ko'rinadi", d["session_count"], 1)
ck("soatlari yozilgan", d["hours"], 3)

print("\n=== B. USTOZLAR RO'YXATI ===")
row = in_list()
ck("ro'yxatda 0", row["salary"], 0)
ck("sababi yozilgan", row.get("grade_note"), "Volontyor — oylik berilmaydi")
ck("seanslari ko'rinadi", row["session_count"], 1)

print("\n=== C. MOLIYA -> ISH HAQI ===")
p = in_payroll()
ck("to'lanadigan oylik 0", p["salary"], 0)
ck("qoldiq ham 0", p["left"], 0)
ck("hisoblangani ko'rinib turadi", p["salary_base"] > 0, True)
ck("umumiy summaga qo'shilmaydi",
   client.get("/api/support/salary", headers=H).json()["total"], 0)

print("\n=== D. JUNIOR BO'LSA — OYLIK PAYDO BO'LADI ===")
r = client.put(f"/api/staff-grades/{SU_ID}", headers=H,
               json={"grade": "junior"})
ck("daraja ko'tarildi", r.status_code, 200)
d = mine()
ck("endi volontyor emas", d.get("volunteer"), None)
ck("o'ziga oyligi ko'rinadi", d["salary"] >= roles.SUPPORT_PAY_MIN, True)
ck("ro'yxatda ham summa bor", in_list()["salary"] >= roles.SUPPORT_PAY_MIN,
   True)
ck("ish haqida ham", in_payroll()["salary"] >= roles.SUPPORT_PAY_MIN, True)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
