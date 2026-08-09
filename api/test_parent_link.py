"""Ota-ona havolasi: muddat (roles.PARENT_TOKEN_VALIDITY_DAYS) va
/regenerate (2026-08 mustahkamlash).

Oldin: token abadiy amal qilardi, "yangilash" imkoniyati yo'q edi
(parent_link() docstringi va'da bergan bo'lsa ham)."""
import os, sys
from datetime import date, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/parentlink_test.db"
if os.path.exists("/tmp/parentlink_test.db"):
    os.remove("/tmp/parentlink_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
from database import SessionLocal
from auth import hash_password

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
b = models.Branch(name="Zafar")
db.add(b)
db.commit()
BID = b.id

for u, role in [("kassir", "administrator"), ("ustoz1", "teacher")]:
    db.add(models.User(username=u, full_name=u, role=role,
                       branch_id=BID, password_hash=hash_password("x"),
                       is_active=1))
db.commit()

s = models.Student(full_name="Ali Aliyev", branch_id=BID, status="active")
db.add(s)
db.commit()
SID = s.id

H = tok("kassir")
HT = tok("ustoz1")

print("=== 1. RUXSAT ===")
ck("teacher parent-link ololmaydi",
   client.get(f"/api/students/{SID}/parent-link", headers=HT).status_code,
   403)
ck("teacher regenerate ololmaydi",
   client.post(f"/api/students/{SID}/parent-link/regenerate",
               headers=HT).status_code, 403)

print("\n=== 2. BIRINCHI YARATISH ===")
r1 = client.get(f"/api/students/{SID}/parent-link", headers=H).json()
ck("url qaytdi", bool(r1.get("url")), True)
ck("muddat qaytdi", bool(r1.get("expires_at")), True)
db.refresh(s)
TOKEN1 = s.parent_token
ck("token bazaga yozildi", bool(TOKEN1), True)
exp1 = s.parent_token_expires_at
days_left = (exp1 - datetime.utcnow()).days
ck("muddat ~PARENT_TOKEN_VALIDITY_DAYS kun (179-180)",
   days_left in (179, 180), True)

print("\n=== 3. QAYTA SO'RASA - TOKEN O'ZGARMAYDI ===")
r2 = client.get(f"/api/students/{SID}/parent-link", headers=H).json()
db.refresh(s)
ck("ikkinchi GET token'ni o'zgartirmaydi", s.parent_token, TOKEN1)
ck("URL ham bir xil", r2["url"], r1["url"])

print("\n=== 4. ESKI (MUDDATSIZ) TOKEN BACKFILL ===")
s.parent_token_expires_at = None
db.commit()
client.get(f"/api/students/{SID}/parent-link", headers=H)
db.refresh(s)
ck("eski token o'zgarmadi (faqat muddat qo'shildi)",
   s.parent_token, TOKEN1)
ck("endi muddat bor", s.parent_token_expires_at is not None, True)

print("\n=== 5. OCHIQ SAHIFA - AMALDAGI TOKEN ===")
resp = client.get(f"/api/parent/{TOKEN1}")
ck("amaldagi token bilan 200", resp.status_code, 200)
ck("o'quvchi nomi to'g'ri", resp.json().get("name"), "Ali Aliyev")

print("\n=== 6. OCHIQ SAHIFA - MUDDATI TUGAGAN TOKEN ===")
s.parent_token_expires_at = datetime.utcnow() - timedelta(days=1)
db.commit()
resp = client.get(f"/api/parent/{TOKEN1}")
ck("muddati tugagan token 404", resp.status_code, 404)
ck("xabar aniq (muddat so'zi bor)",
   "muddat" in resp.json().get("detail", "").lower(), True)

print("\n=== 7. REGENERATE - ESKI HAVOLA DARHOL O'CHADI ===")
before_logs = db.query(models.AuditLog).count()
r3 = client.post(f"/api/students/{SID}/parent-link/regenerate",
                 headers=H).json()
db.refresh(s)
TOKEN2 = s.parent_token
ck("yangi token eskisidan farq qiladi", TOKEN2 != TOKEN1, True)
ck("javobdagi url yangi tokenga mos", TOKEN2 in r3["url"], True)
days_left2 = (s.parent_token_expires_at - datetime.utcnow()).days
ck("yangi muddat ham ~180 kun", days_left2 in (179, 180), True)

resp_old = client.get(f"/api/parent/{TOKEN1}")
ck("eski token endi umuman topilmaydi", resp_old.status_code, 404)
resp_new = client.get(f"/api/parent/{TOKEN2}")
ck("yangi token ishlaydi", resp_new.status_code, 200)

after_logs = db.query(models.AuditLog).count()
ck("regenerate audit qilindi", after_logs, before_logs + 1)
last_log = db.query(models.AuditLog).order_by(
    models.AuditLog.id.desc()).first()
ck("audit yozuvi shu o'quvchiga tegishli", last_log.entity_id, SID)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
