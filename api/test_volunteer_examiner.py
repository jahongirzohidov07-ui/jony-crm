"""VOLONTYOR EXAMINERGA OYLIK HISOBLANMAYDI (2026-09-23).

Jahongir: supportdan keyin "examinerlarga ham".

Support bilan bir xil qoida:
  A. O'z sahifasida ("Oyligim") pul ko'rsatilmaydi, lekin qilgan
     ishi — imtihonlari va ballari — ko'rinib turadi;
  B. Rahbariyat ro'yxatida (Moliya -> Ish haqi) 0, qoldiq ham 0 va
     umumiy summaga qo'shilmaydi;
  C. Junior bo'lsa — o'sha imtihonlardan oylik paydo bo'ladi.
"""
import os
import sys
import tempfile
from datetime import timedelta

_DB = os.path.join(tempfile.gettempdir(), "volunteer_examiner_test.db")
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


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("Parol123!"),
                   role=roles.FOUNDER, branch_id=BID, is_active=1))
ex = models.User(username="exam", full_name="Examiner Diyor",
                 password_hash=hash_password("Parol123!"),
                 role=roles.EXAMINER, branch_id=BID, is_active=1)
ut = models.User(username="ust", full_name="Ustoz Anvar",
                 password_hash=hash_password("Parol123!"),
                 role=roles.TEACHER, branch_id=BID, is_active=1)
db.add_all([ex, ut])
db.commit()
EX_ID = ex.id
t = models.Teacher(full_name="Ustoz Anvar", branch_id=BID, user_id=ut.id,
                   is_active=1)
db.add(t)
db.commit()
g = models.Group(name="Apex", branch_id=BID, teacher_id=t.id, level="B1",
                 subject="english")
db.add(g)
db.commit()
GID = g.id
S = []
for nm in ["Aliyev Ali", "Boboyev Bobur", "Valiyev Valijon"]:
    s = models.Student(full_name=nm, branch_id=BID, group_id=GID,
                       status="active",
                       enrolled_date=TODAY - timedelta(days=60))
    db.add(s)
    db.commit()
    S.append(s.id)
db.close()

H = tok("asos")
HE = tok("exam")

# Imtihonni examiner o'tkazdi — ball shu yerdan hisoblanadi
r = client.post(f"/api/groups/{GID}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 50})
EID = r.json()["id"]
client.put(f"/api/exams/{EID}/results", headers=H, json={
    "marks": [{"student_id": sid, "score": 40} for sid in S]})
db = SessionLocal()
e = db.query(models.Exam).get(EID)
e.examiner_id = EX_ID
e.status = "done"
db.commit()
db.close()


def mine():
    return client.get("/api/me/examiner-salary", headers=HE).json()


def in_payroll():
    d = client.get("/api/examiners/salary", headers=H).json()
    return d, {x["name"]: x for x in d["rows"]}["Examiner Diyor"]


print("\n=== A. VOLONTYOR — O'Z SAHIFASI ===")
d = mine()
ck("volontyor deb belgilandi", d.get("volunteer"), True)
ck("oylik hisoblanmadi", d.get("salary"), 0)
ck("hisob summasi ham 0", d.get("raw"), 0)
ck("imtihoni ko'rinib turadi", d.get("exam_count"), 1)
ck("ballari ham ko'rinadi", d.get("base_points", 0) > 0, True)

print("\n=== B. MOLIYA -> ISH HAQI ===")
all_d, row = in_payroll()
ck("to'lanadigan oylik 0", row["salary"], 0)
ck("qoldiq ham 0", row["left"], 0)
ck("sababi yozilgan", row.get("grade_note"), "Volontyor — oylik berilmaydi")
ck("hisoblangani ko'rinib turadi", row["salary_base"] > 0, True)
ck("umumiy summaga qo'shilmaydi", all_d["total"], 0)

print("\n=== C. JUNIOR BO'LSA — OYLIK PAYDO BO'LADI ===")
ck("daraja ko'tarildi",
   client.put(f"/api/staff-grades/{EX_ID}", headers=H,
              json={"grade": "junior"}).status_code, 200)
d = mine()
ck("endi volontyor emas", d.get("volunteer"), None)
ck("o'ziga oyligi ko'rinadi", d["salary"] >= roles.EXAMINER_PAY_MIN, True)
ck("ish haqida ham", in_payroll()[1]["salary"] >= roles.EXAMINER_PAY_MIN,
   True)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
