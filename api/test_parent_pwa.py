"""Ota-ona portali PWA: shaxsiy manifest + muddat tekshiruvining
HAQIQIY (entry.py orqali) ishlashi.

MUHIM: bu fayl `import entry` qiladi, chunki /api/parent/{token} ni
entry.py to'liq mustaqil qayta yozadi (parents.py'nikini chaqirmaydi).
create_user_v2'da topilgan xuddi shu naqsh: agar shu yerda faqat
`import main` qilinsa, parents.py'ning (HAQIQATDA ishlamaydigan)
nusxasi tekshirilib, natija noto'g'ri "yashil" chiqadi."""
import os, sys
from datetime import datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/parent_pwa_test.db"
if os.path.exists("/tmp/parent_pwa_test.db"):
    os.remove("/tmp/parent_pwa_test.db")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models
import entry  # noqa: F401 - haqiqiy /api/parent/{token} shu yerda
from database import SessionLocal

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


db = SessionLocal()
b = models.Branch(name="Zafar")
db.add(b)
db.commit()

s_ok = models.Student(full_name="Amira Yusupova", branch_id=b.id,
                      status="active", parent_token="tok_amira_valid_1",
                      parent_token_expires_at=datetime.utcnow()
                      + timedelta(days=30))
s_expired = models.Student(full_name="Bekzod Rustamov", branch_id=b.id,
                           status="active",
                           parent_token="tok_bekzod_expired_1",
                           parent_token_expires_at=datetime.utcnow()
                           - timedelta(days=1))
s_legacy = models.Student(full_name="Sherzod Nazarov", branch_id=b.id,
                          status="active", parent_token="tok_legacy_null_1",
                          parent_token_expires_at=None)
db.add_all([s_ok, s_expired, s_legacy])
db.commit()

print("=== 1. Amal qiluvchi token: sahifa ochiladi ===")
r = client.get(f"/api/parent/{s_ok.parent_token}")
ck("status 200", r.status_code, 200)
ck("ism to'g'ri", r.json().get("name"), "Amira Yusupova")
ck("practice maydoni bor (mashqlar)", "practice" in r.json(), True)

print("\n=== 2. Muddati o'tgan token: RAD ETILADI (asosiy topilma) ===")
r2 = client.get(f"/api/parent/{s_expired.parent_token}")
ck("status 404", r2.status_code, 404)
ck("sabab tushunarli", "muddati tugagan" in r2.json().get("detail", ""), True)

print("\n=== 3. Eski (muddatsiz/NULL) token hali ishlaydi ===")
r3 = client.get(f"/api/parent/{s_legacy.parent_token}")
ck("status 200 (NULL = eski, hali amal qiladi)", r3.status_code, 200)

print("\n=== 4. Shaxsiy PWA manifest — amal qiluvchi token ===")
r4 = client.get(f"/api/parent/{s_ok.parent_token}/manifest.webmanifest")
ck("status 200", r4.status_code, 200)
ck("content-type to'g'ri",
   r4.headers.get("content-type", "").startswith("application/manifest+json"),
   True)
mf = r4.json()
ck("nomi farzand ismini o'z ichiga oladi", "Amira Yusupova" in mf.get("name", ""), True)
ck("start_url shu tokenga bog'langan",
   mf.get("start_url", "").startswith(f"/parent/{s_ok.parent_token}"), True)
ck("scope shu tokenga bog'langan", mf.get("scope"), f"/parent/{s_ok.parent_token}")
ck("4 ta belgi (icon) bor", len(mf.get("icons", [])), 4)
ck("maskable belgi bor",
   any(i.get("purpose") == "maskable" for i in mf["icons"]), True)

print("\n=== 5. Manifest ham muddat/mavjudlikni hurmat qiladi ===")
r5 = client.get(f"/api/parent/{s_expired.parent_token}/manifest.webmanifest")
ck("muddati o'tgan token uchun ham manifest beriladi "
   "(sahifaning o'zi keyin 404 qiladi)", r5.status_code, 200)
r6 = client.get("/api/parent/notoqrisiktoken000/manifest.webmanifest")
ck("umuman mavjud bo'lmagan token uchun 404", r6.status_code, 404)

db.close()

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
