"""ADMINISTRATOR: LID O'CHIRISH, O'QUVCHI FAQAT LIDDAN, ARXIVDAN TIKLASH
(2026-09-16).

Jahongir: "lidlarni ochiradigan qilib ber lid ochirib bolmayabdi
ochirganda sabablarni tanlaydigan qilib qoyish kerak, keyin oquvchini
qoshish mumkin bolmasin faqat liddan qoshish mumkin bo'lsin. Arxivdagi
o'quvchilarni qayta tiklashni administratorlarga ochib ber".

Tekshiriladi:
  1. Administrator lidni SABAB bilan o'chiradi; sababsiz — rad;
     boshqa filial lidini o'chira olmaydi;
  2. O'quvchini to'g'ridan-to'g'ri qo'shib bo'lmaydi (asoschidan
     boshqa), liddan aylantirish ishlaydi;
  3. Administrator o'z filiali arxividagi o'quvchini tiklaydi (sinovga),
     boshqa filialnikini — yo'q.
"""
import os
import sys
import tempfile

_DIR = os.path.join(tempfile.gettempdir(), "lead_admin_rules_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402,F401
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u, p="x"):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login", json={"username": u, "password": p}
    ).json()["access_token"]}


db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Bekobod 2")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
db.add_all([
    models.User(username="asos", password_hash=hash_password("x"),
                full_name="Asoschi", role=roles.FOUNDER),
    models.User(username="adm", password_hash=hash_password("x"),
                full_name="Admin B1", role=roles.ADMINISTRATOR, branch_id=B1),
])
l1 = models.Lead(full_name="Adashib kiritilgan", phone="998900000001",
                 source="visit", stage="new", branch_id=B1)
l2 = models.Lead(full_name="Boshqa filial lidi", phone="998900000002",
                 source="visit", stage="new", branch_id=B2)
l3 = models.Lead(full_name="Yangi o'quvchi", phone="998900000003",
                 source="visit", stage="trial_scheduled", branch_id=B1)
a1 = models.Student(full_name="Qaytgan bola", branch_id=B1, status="archived")
a2 = models.Student(full_name="Boshqa filial arxivi", branch_id=B2,
                    status="archived")
db.add_all([l1, l2, l3, a1, a2]); db.commit()
L1, L2, L3, A1, A2 = l1.id, l2.id, l3.id, a1.id, a2.id
db.close()

H, A = tok("asos"), tok("adm")
REASON = next(iter(roles.LEAD_DELETE_LABELS))

print("=== 1. Lid o'chirish ===")
ck("sababsiz — rad", client.delete(f"/api/leads/{L1}", headers=A).status_code, 400)
r = client.delete(f"/api/leads/{L1}?reason={REASON}&note=test", headers=A)
ck("administrator sabab bilan o'chirdi", r.status_code, 200)
s = SessionLocal()
ck("lid arxivga ko'chdi", s.query(models.DeletedLead)
   .filter_by(lead_id=L1).first().reason, REASON)
ck("lidlardan chiqdi", s.query(models.Lead).get(L1), None)
s.close()
ck("boshqa filial lidi — yopiq",
   client.delete(f"/api/leads/{L2}?reason={REASON}", headers=A).status_code, 403)

print("\n=== 2. O'quvchi faqat liddan ===")
r = client.post("/api/students", headers=A, json={
    "full_name": "To'g'ridan-to'g'ri", "branch_id": B1, "status": "active"})
ck("administrator to'g'ridan qo'sha olmaydi", r.status_code, 403)
ck("sababi aytiladi", "Lidlar" in r.json().get("detail", ""), True)
r = client.post(f"/api/leads/{L3}/convert", headers=A, json={})
ck("liddan aylantirish ishlaydi", (r.status_code, r.json().get("status")),
   (200, "trial"))
r = client.post("/api/students", headers=H, json={
    "full_name": "Asoschi qo'shdi", "branch_id": B1, "status": "trial"})
ck("asoschi (favqulodda) qo'sha oladi", r.status_code, 200)

print("\n=== 3. Arxivdan tiklash ===")
r = client.post(f"/api/students/{A1}/restore", headers=A, json={})
ck("administrator tikladi", r.status_code, 200)
ck("sinovga qaytdi", r.json().get("status"), "trial")
ck("boshqa filial arxivi — yopiq",
   client.post(f"/api/students/{A2}/restore", headers=A, json={}).status_code, 403)
ck("qayta tiklab bo'lmaydi (arxivda emas)",
   client.post(f"/api/students/{A1}/restore", headers=A, json={}).status_code, 400)

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
