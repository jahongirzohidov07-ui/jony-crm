"""Eski sana bilan to'lov: faqat asoschi va moliya direktori."""
import os, sys
from datetime import date, timedelta
os.environ["DATABASE_URL"] = "sqlite:////tmp/backdate.db"
if os.path.exists("/tmp/backdate.db"): os.remove("/tmp/backdate.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient
import main, models
import entry  # noqa
from database import SessionLocal
from auth import hash_password
c = TestClient(main.app); fails=[]
def ck(n,g,w):
    ok = g==w
    print(("OK  " if ok else "XATO ")+n+f": {g}"+("" if ok else f" (kutilgan {w})"))
    if not ok: fails.append(n)
db = SessionLocal()
b = models.Branch(name="B"); db.add(b); db.commit()
st = models.Student(full_name="Test O", branch_id=b.id, status="active")
db.add(st); db.commit(); SID = st.id
db.add_all([
 models.User(username="asos", full_name="Asoschi", role="founder",
             password_hash=hash_password("x"), is_active=1),
 models.User(username="mol", full_name="Moliyachi", role="finance_director",
             branch_id=b.id, password_hash=hash_password("x"), is_active=1),
 models.User(username="adm", full_name="Admin", role="administrator",
             branch_id=b.id, password_hash=hash_password("x"), is_active=1)])
db.commit(); db.close()
def tok(u):
    return {"Authorization":"Bearer "+c.post("/api/auth/login",
            json={"username":u,"password":"x"}).json()["access_token"]}
F, M, A = tok("asos"), tok("mol"), tok("adm")
past = (date.today()-timedelta(days=45)).isoformat()

print("=== 1. Asoschi eski sana bilan kiritadi ===")
r = c.post(f"/api/students/{SID}/payments", headers=F,
           json={"amount":300000,"kind":"payment","method":"cash","date":past})
ck("qabul qilindi", r.status_code, 200)
ck("sana o'sha kunga yozildi", r.json()["created_at"][:10], past)

print("\n=== 2. Moliyachi ham kirita oladi ===")
r2 = c.post(f"/api/students/{SID}/payments", headers=M,
            json={"amount":100000,"kind":"payment","method":"cash","date":past})
ck("qabul qilindi", r2.status_code, 200)

print("\n=== 3. Administratorga RUXSAT YO'Q ===")
r3 = c.post(f"/api/students/{SID}/payments", headers=A,
            json={"amount":50000,"kind":"payment","method":"cash","date":past})
ck("403 qaytadi", r3.status_code, 403)

print("\n=== 4. Sanasiz kiritsa - hamma qila oladi, bugungi kun ===")
r4 = c.post(f"/api/students/{SID}/payments", headers=A,
            json={"amount":50000,"kind":"payment","method":"cash"})
ck("qabul qilindi", r4.status_code, 200)
# created_at server soati (UTC) bilan yoziladi — mahalliy kun
# bilan farq qilishi mumkin, shuning uchun ikkalasi ham to'g'ri.
_ok_days = {date.today().isoformat(),
            (date.today()+timedelta(days=1)).isoformat(),
            (date.today()-timedelta(days=1)).isoformat()}
ck("bugungi sana", r4.json()["created_at"][:10] in _ok_days, True)

print("\n=== 5. Kelajak sanasi bilan bo'lmaydi ===")
fut = (date.today()+timedelta(days=3)).isoformat()
r5 = c.post(f"/api/students/{SID}/payments", headers=F,
            json={"amount":10000,"kind":"payment","method":"cash","date":fut})
ck("400 qaytadi", r5.status_code, 400)

print("\n=== 6. Ro'yxat tartibi: bugungi tepada, eskisi pastda ===")
rows = c.get(f"/api/students/{SID}", headers=F).json()["payments"]
ck("birinchi qator bugungi", rows[0]["created_at"][:10] in _ok_days, True)
ck("oxirgi qator eski sana", rows[-1]["created_at"][:10], past)

print("\n=== 7. Auditda iz qoladi ===")
db = SessionLocal()
al = [a for a in db.query(models.AuditLog).all()
      if a.note and "ESKI SANA" in a.note]
db.close()
ck("audit yozuvi bor", len(al) >= 2, True)
print()
if fails: print("XATOLAR:", ", ".join(fails)); sys.exit(1)
print("HAMMASI O'TDI")
