# -*- coding: utf-8 -*-
"""Kontent-planga qo'shish va o'zgartirish (2026-09-26).

Jahongir: "kontent planni ham qoshimcha qoshish va ozgartirish kerak",
"qoshimcha kontent planni ham smm manager kerakli joylarini ozgartira
olsin".
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_cpe/db.sqlite"
os.makedirs("/tmp/verify_cpe", exist_ok=True)
if os.path.exists("/tmp/verify_cpe/db.sqlite"):
    os.remove("/tmp/verify_cpe/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, got, want):
    ok = got == want
    print(("OK   " if ok else "XATO ") + f"{n}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(n)


br = models.Branch(name="Maktab")
db.add(br)
db.commit()
for un, role in (("marhabo", roles.SMM_MANAGER), ("ustoz", roles.TEACHER),
                 ("dilnoza", roles.SMM_MANAGER)):
    db.add(models.User(username=un, password_hash=hash_password("jonyjony"),
                       role=role, full_name=un.title(), branch_id=br.id,
                       is_active=1))
db.commit()
DIL = db.query(models.User).filter_by(username="dilnoza").first().id


def tok(un):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": un, "password": "jonyjony"}
    ).json()["access_token"]}


HS, HT = tok("marhabo"), tok("ustoz")
d0 = date.today() + timedelta(days=3)

print("=== 1. REJAGA QO'LDA YANGI POST ===")
r = c.post("/api/content", headers=HS, json={
    "title": "Ustozlar bilan tanishuv", "planned_date": d0.isoformat(),
    "planned_time": "18:00", "platform": "instagram", "pillar": "trust",
    "owner_id": DIL, "audience": "Ota-onalar", "branch_id": br.id})
ck("qo'shildi", r.status_code, 200)
CID = r.json()["id"]
plan = c.get("/api/smm/plan", headers=HS).json()
row = next((x for x in plan["rows"] if x["id"] == CID), None)
ck("kontent-planda ko'rinadi", bool(row), True)
ck("  mas'ul va vaqt joyida", (row or {}).get("owner"), "Dilnoza")
ck("mas'ullar ro'yxati (SMM jamoasi) meta'da",
   sorted(u["name"] for u in plan["meta"]["owners"]),
   ["Dilnoza", "Marhabo"])
ck("ustoz qo'sha olmaydi",
   c.post("/api/content", headers=HT, json={"title": "x"}).status_code, 403)

print("\n=== 2. KERAKLI JOYLARINI O'ZGARTIRISH ===")
d1 = d0 + timedelta(days=2)
r = c.put(f"/api/content/{CID}", headers=HS, json={
    "title": "Ustozlar bilan tanishuv (2-qism)",
    "planned_date": d1.isoformat(), "planned_time": "19:30",
    "platform": "telegram", "funnel": "consideration", "owner_id": None,
    "shoot_date": d0.isoformat()})
ck("saqlandi", r.status_code, 200)
db.expire_all()
x = db.query(models.Content).get(CID)
ck("hamma maydon yangilandi",
   (x.title, x.planned_date, x.planned_time, x.platform, x.funnel,
    x.owner_id, x.shoot_date),
   ("Ustozlar bilan tanishuv (2-qism)", d1, "19:30", "telegram",
    "consideration", None, d0))
mv = db.query(models.ContentMove).filter_by(content_id=CID).all()
ck("sana o'zgarishi ko'chish tarixiga yozildi",
   [(m.from_date, m.to_date) for m in mv], [(d0, d1)])
fields = sorted({v.field for v in db.query(models.ContentVersion)
                 .filter_by(content_id=CID).all()})
ck("o'zgargan ustunlar tarixda",
   fields, sorted(["title", "planned_date", "planned_time", "platform",
                   "funnel", "owner_id", "shoot_date"]))
r = c.put(f"/api/content/{CID}", headers=HS, json={"title": "   "})
ck("mavzuni bo'sh qilib bo'lmaydi", r.status_code, 400)
ck("ustoz o'zgartira olmaydi",
   c.put(f"/api/content/{CID}", headers=HT,
         json={"title": "buz"}).status_code, 403)

print("\n=== 3. HOLAT VA BEKOR QILISH (O'CHIRMASDAN) ===")
r = c.post(f"/api/content/{CID}/status", headers=HS,
           json={"status": "cancelled"})
ck("bekor qilindi", r.json().get("status"), "cancelled")
ck("bazada qoldi", db.query(models.Content).get(CID) is not None, True)
same = c.put(f"/api/content/{CID}", headers=HS,
             json={"planned_date": d1.isoformat()})
db.expire_all()
ck("o'zgarmagan sana tarixga qayta yozilmaydi",
   db.query(models.ContentMove).filter_by(content_id=CID).count(), 1)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
