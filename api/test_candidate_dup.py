"""TAKRORIY NOMZOD (2026-09-16, taklif #1).

"Bir odam har safar yangi nomzod bo'lib tushyapti. Telefon bo'yicha
'avval ham ariza bergan: 2 marta, oxirgisi rad etilgan (sabab…)' deb
ko'rsatish va nomzodlarni birlashtirish.\""""
import os, sys, tempfile
from datetime import datetime, timedelta

_tmp = tempfile.mkdtemp(prefix="jony_dup_")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
    _tmp, "db.sqlite").replace("\\", "/")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []
PW = "Parol123!"


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g!r}"
          + ("" if ok else f"  (kutilgan {w!r})"))
    if not ok:
        fails.append(n)


b = models.Branch(name="Zafar"); db.add(b); db.commit()
for un, role in (("hr", roles.HR_MANAGER), ("ustoz", roles.TEACHER)):
    db.add(models.User(username=un, full_name=un.title(),
                       password_hash=hash_password(PW), role=role,
                       branch_id=b.id, is_active=1))
db.commit()


def H(un):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": un, "password": PW}
    ).json()["access_token"]}


HR, T = H("hr"), H("ustoz")


def create(name, phone=None, force=False, **kw):
    return c.post("/api/candidates", headers=HR, json={
        "full_name": name, "phone": phone, "position": "teacher",
        "subject": "Ingliz tili", "branch_id": b.id, "force": force, **kw})


def age(cid, days):
    db.query(models.Candidate).filter(models.Candidate.id == cid).update(
        {models.Candidate.created_at: datetime.utcnow() - timedelta(days=days)})
    db.commit()


print("=== QO'LDA KIRITISHDA OGOHLANTIRISH ===")
r = create("Olimova Dilnoza", "+998 90 555 66 77", address="Bekobod")
A = r.json()["id"]
age(A, 40)
app = db.query(models.CandidateApplication).filter_by(candidate_id=A).first()
r = c.post(f"/api/ats/applications/{app.id}/move", headers=HR,
           json={"stage": "rejected", "reason": "weak_demo",
                 "note": "guruhni boshqara olmadi"})
ck("birinchi arizasi rad etildi", r.status_code, 200)

n_before = db.query(models.Candidate).count()
r = create("Dilnoza Olimova", "90-555-66-77")
ck("takror ogohlantirildi", r.json().get("duplicate"), True)
ck("yangi yozuv ochilmadi", db.query(models.Candidate).count(), n_before)
h = r.json()["history"]
ck("tarixda eski ariza", [x["id"] for x in h], [A])
ck("rad etish sababi ko'rinadi", h[0]["reject_reason"],
   "Sinov darsi kuchsiz: guruhni boshqara olmadi")
ck("bosqichi", h[0]["stage_label"], "Rad etildi")
r = create("Dilnoza Olimova", "90-555-66-77", force=True)
B = r.json()["id"]
ck("baribir ochildi", bool(B), True)

C = create("Karimov Aziz", "+998 91 000 00 01").json()["id"]
D = create("Olimova Dilnoza", "+998 93 222 33 44").json().get("id")
ck("ismdosh (boshqa telefon) — ogohlantirishsiz ochildi", bool(D), True)
E = create("olimova  dilnoza", None, force=True).json()["id"]

print("\n=== RO'YXATDA BELGI ===")
lst = {x["id"]: x for x in c.get("/api/candidates", headers=HR).json()}
ck("A: B va telefonsiz E", lst[A]["other_applications"], 2)
ck("B: A va E", lst[B]["other_applications"], 2)
ck("boshqa odam: 0", lst[C]["other_applications"], 0)
ck("ismdosh boshqa telefon: faqat telefonsiz E", lst[D]["other_applications"], 1)
ck("telefonsiz E: hammasi (ism bo'yicha)", lst[E]["other_applications"], 3)

print("\n=== KARTADA TARIX ===")
d = c.get(f"/api/candidates/{B}", headers=HR).json()
ck("B kartasida A va E", sorted(x["id"] for x in d["history"]), sorted([A, E]))
ck("yangisi tepada", d["history"][0]["id"], E)

print("\n=== BIRLASHTIRISH ===")
db.add(models.Attachment(entity="candidate", entity_id=A, kind="photo",
                         filename="a.jpg", mime="image/jpeg", size=3,
                         data="AAA", created_by="t"))
db.add(models.Interview(application_id=app.id, candidate_id=A, kind="hr",
                        date=datetime.utcnow().date(), status="done"))
db.commit()
ck("o'ziga qo'shib bo'lmaydi",
   c.post(f"/api/candidates/{B}/merge", headers=HR,
          json={"source_id": B}).status_code, 400)
ck("ustoz birlashtira olmaydi",
   c.post(f"/api/candidates/{B}/merge", headers=T,
          json={"source_id": A}).status_code, 403)
r = c.post(f"/api/candidates/{B}/merge", headers=HR, json={"source_id": A})
ck("birlashtirildi", r.status_code, 200)
ck("ko'chganlar", r.json()["moved"],
   {"arizalar": 1, "suhbatlar": 1, "fayllar": 1})
ck("bo'sh manzil to'ldirildi", "address" in r.json()["filled"], True)
db.expire_all()
ck("A o'chdi", db.query(models.Candidate).get(A), None)
bb = db.query(models.Candidate).get(B)
ck("B da 2 ta ariza", db.query(models.CandidateApplication)
   .filter_by(candidate_id=B).count(), 2)
ck("fayl B da", db.query(models.Attachment)
   .filter_by(entity="candidate", entity_id=B).count(), 1)
ck("manzil", bb.address, "Bekobod")
ck("izohda birlashtirish yozildi", "Birlashtirildi" in (bb.note or ""), True)
ck("eng eski sana saqlandi", (datetime.utcnow() - bb.created_at).days >= 39,
   True)
d = c.get(f"/api/candidates/{B}", headers=HR).json()
ck("tarixda faqat E qoldi", [x["id"] for x in d["history"]], [E])
ck("auditga yozildi", db.query(models.AuditLog)
   .filter_by(entity="candidate", action="merge").count(), 1)

print("\n=== ONLAYN ARIZA ===")
age(B, 3)
photo = "data:image/jpeg;base64," + "A" * 200
r = c.post("/api/apply", json={"full_name": "Olimova Dilnoza",
                               "phone": "+998905556677",
                               "position": "teacher", "photo": photo,
                               "certificate": photo})
ck("qayta ariza qabul qilindi", r.status_code, 200)
new = (db.query(models.Candidate)
       .order_by(models.Candidate.id.desc()).first())
lst = {x["id"]: x for x in c.get("/api/candidates", headers=HR).json()}
ck("yangi arizada: avval ham kelgan", lst[new.id]["other_applications"] >= 1,
   True)

print()
if fails:
    print("XATOLAR:", fails)
    sys.exit(1)
print("HAMMASI O'TDI")
