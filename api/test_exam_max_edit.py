"""MAKSIMAL BALLNI TO'G'RILASH MUMKIN (2026-09-25).

Jahongir: "imtixon qo'shsa qizil yozuv chiqib qolyabdi 0-40 orasida
bo'lishi kerak ball deb".

SABAB: test bazasidagi savollar soni (masalan 40) imtihonning
maksimal balliga AVTOMAT qo'yilardi va maydon QULFLANARDI. Haqiqiy
test 45 savoldan iborat bo'lsa, 41-45 ball kiritib bo'lmasdi va
chiqish yo'li ham yo'q edi.

Tekshiriladi:
  A. Maksimal ball tahrirlanadi va undan keyin katta ball kiritiladi;
  B. Xato matni sababini aytadi (qayerdan 40 kelgani va nima qilish);
  C. Allaqachon qo'yilgan balldan past qilib bo'lmaydi;
  D. Online havola ulangan bo'lsa, online qismidan past qilib
     bo'lmaydi — aks holda natija 100% dan oshib ketardi.
"""
import os
import sys
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "exam_max_edit_test.db")
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


TODAY = roles.local_today()

db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="asos", full_name="Asoschi",
                   password_hash=hash_password("Parol123!"),
                   role=roles.FOUNDER, branch_id=BID, is_active=1))
db.commit()
t = models.Teacher(full_name="Ustoz", branch_id=BID, is_active=1)
db.add(t)
db.commit()
g = models.Group(name="Apex", subject="english", level="B1", branch_id=BID,
                 teacher_id=t.id, lesson_time="18:00", monthly_fee=1,
                 lesson_days="135", capacity=15)
db.add(g)
db.commit()
GID = g.id
S = {}
for nm in ["Aliyev Ali", "Boboyev Bobur"]:
    s = models.Student(full_name=nm, branch_id=BID, group_id=GID,
                       status="active", enrolled_date=TODAY)
    db.add(s)
    db.commit()
    S[nm] = s.id
db.close()

H = {"Authorization": "Bearer " + client.post(
    "/api/auth/login", json={"username": "asos", "password": "Parol123!"}
).json()["access_token"]}

EID = client.post(f"/api/groups/{GID}/exams", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 40}).json()["id"]

print("\n=== B. XATO MATNI SABABINI AYTADI ===")
r = client.put(f"/api/exams/{EID}/results", headers=H, json={
    "marks": [{"student_id": S["Aliyev Ali"], "score": 43}]})
ck("43 ball rad etildi", r.status_code, 400)
msg = r.json()["detail"]
ck("chegarasi aytilgan", "0 va 40" in msg, True)
ck("nima qilish kerakligi aytilgan", "tahrirlab" in msg, True)

print("\n=== A. MAKSIMAL BALL TO'G'RILANADI ===")
r = client.put(f"/api/exams/{EID}", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 45})
ck("45 ga o'zgartirildi", r.status_code, 200)
r = client.put(f"/api/exams/{EID}/results", headers=H, json={
    "marks": [{"student_id": S["Aliyev Ali"], "score": 43}]})
ck("endi 43 ball qabul qilindi", r.status_code, 200)
res = {x["student_id"]: x for x in
       client.get(f"/api/exams/{EID}", headers=H).json()["results"]}
ck("foiz 45 dan hisoblandi", res[S["Aliyev Ali"]]["percent"], 95.6)

print("\n=== C. QO'YILGAN BALLDAN PAST QILIB BO'LMAYDI ===")
r = client.put(f"/api/exams/{EID}", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 40})
ck("40 ga tushirib bo'lmadi", r.status_code, 400)

print("\n=== D. ONLINE HAVOLA ULANGAN BO'LSA ===")
d = SessionLocal()
tpl = models.ExamTemplate(level="B1", kind="unit", unit_no=1,
                          title="Unit 1", parts="[]", paper_max=0,
                          is_active=1)
d.add(tpl)
d.commit()
d.add(models.ExamOnline(exam_id=EID, template_id=tpl.id, token="tok123",
                        is_open=1, parts="[]", online_max=45, paper_max=0))
d.commit()
d.close()
# Natijani olib tashlaymiz — endi faqat online chegarasi sinaladi
client.put(f"/api/exams/{EID}/results", headers=H, json={
    "marks": [{"student_id": S["Aliyev Ali"], "absent": True}]})
r = client.put(f"/api/exams/{EID}", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 30})
ck("online qismidan past qilib bo'lmadi", r.status_code, 400)
ck("sababi online ekani aytilgan", "online" in r.json()["detail"].lower(),
   True)
r = client.put(f"/api/exams/{EID}", headers=H, json={
    "kind": "unit", "unit_no": 1, "date": TODAY.isoformat(),
    "max_score": 50})
ck("kattaroq qilish mumkin (qog'oz qismi qo'shiladi)", r.status_code, 200)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
