# -*- coding: utf-8 -*-
"""Har videodan murojaat va sotuv (2026-09-26).

Jahongir: "Har bir videodan nechta odam murojaat qildi, nechta sotuv
boldi aniq avtomat hisoblashni yo'lga qoyish kerak".

Avval: LeadCreate/LeadUpdate content_id ni QABUL QILMASDI (jimgina
tashlab yuborardi), saytdan kelgan ariza ham postga bog'lanmasdi —
shuning uchun har post bo'yicha lid/sotuv doim 0 edi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_attr/db.sqlite"
os.makedirs("/tmp/verify_attr", exist_ok=True)
if os.path.exists("/tmp/verify_attr/db.sqlite"):
    os.remove("/tmp/verify_attr/db.sqlite")
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
for un, role in (("boss", roles.FOUNDER), ("marhabo", roles.SMM_MANAGER)):
    db.add(models.User(username=un, password_hash=hash_password("jonyjony"),
                       role=role, full_name=un.title(), branch_id=br.id,
                       is_active=1))
db.commit()


def tok(un):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": un, "password": "jonyjony"}
    ).json()["access_token"]}


HB, HS = tok("boss"), tok("marhabo")
today = date.today()
A = models.Content(title="Olimpiada reels", platform="instagram",
                   planned_date=today - timedelta(days=3),
                   status="published", branch_id=br.id)
B = models.Content(title="Ustozlar reels", platform="instagram",
                   planned_date=today - timedelta(days=5),
                   status="published", branch_id=br.id, promo_code="USTOZ10")
IDEA = models.Content(title="Hali g'oya", platform="instagram",
                      planned_date=today + timedelta(days=2), status="idea",
                      branch_id=br.id)
OLD = models.Content(title="Eski post", platform="instagram",
                     planned_date=today - timedelta(days=200),
                     status="published", branch_id=br.id)
db.add_all([A, B, IDEA, OLD])
db.commit()
for x in (A, B, IDEA, OLD):
    x.content_id = f"CONTENT-JA-{x.planned_date.year}-{x.id:04d}"
db.add(models.ContentMetric(content_id=A.id, views=9000, reach=5000,
                            follows=18, source="auto"))
db.commit()

print("=== 1. LID FORMASI: 'QAYSI VIDEODAN?' ===")
opts = c.get("/api/leads/content-options", headers=HB).json()["rows"]
ids = [o["id"] for o in opts]
ck("joylangan postlar ro'yxatda", A.id in ids and B.id in ids, True)
ck("g'oya va 200 kunlik eski post yo'q",
   IDEA.id in ids or OLD.id in ids, False)
EXTRA = {"address": "Zafar", "school": "12-maktab", "grade": "9"}
r = c.post("/api/leads", json={"full_name": "Aliyev Vali",
                               "phone": "+998901110011", "source": "instagram",
                               "content_id": A.id, **EXTRA}, headers=HB)
if r.status_code != 200:
    print("   javob:", r.text[:300])
ck("lid ochildi", r.status_code, 200)
ck("  content_id saqlandi", r.json().get("content_id"), A.id)
L1 = r.json()["id"]
r = c.post("/api/leads", json={"full_name": "Soliyev Ali",
                               "phone": "+998901110022", "source": "instagram",
                               "content_id": 999999, **EXTRA}, headers=HB)
ck("yo'q post berilsa lid baribir ochiladi, bog'lanmaydi",
   (r.status_code, r.json().get("content_id")), (200, None))
L2 = r.json()["id"]
r = c.put(f"/api/leads/{L2}", json={"content_id": 999999}, headers=HB)
ck("tahrirda yo'q post rad etiladi", r.status_code, 400)
r = c.put(f"/api/leads/{L2}", json={"content_id": A.id}, headers=HB)
ck("tahrirda postga bog'landi", r.json().get("content_id"), A.id)

print("\n=== 2. SAYTDAN ARIZA: AVTOMAT BOG'LANISH ===")
r = c.post("/api/public/lead", json={
    "full_name": "Sayt Bir", "phone": "+998 93 000 00 01",
    "utm_content": B.content_id})
l = db.query(models.Lead).get(r.json()["lead_id"])
ck("utm_content=CONTENT-JA-... -> B", l.content_id, B.id)
r = c.post("/api/public/lead", json={
    "full_name": "Sayt Ikki", "phone": "+998 93 000 00 02",
    "page": f"https://jonyacademy.uz/ielts?c={A.id}&utm_source=instagram"})
l = db.query(models.Lead).get(r.json()["lead_id"])
ck("sahifa havolasidagi ?c= -> A", l.content_id, A.id)
r = c.post("/api/public/lead", json={
    "full_name": "Sayt Uch", "phone": "+998 93 000 00 03",
    "promo": "ustoz10"})
l = db.query(models.Lead).get(r.json()["lead_id"])
ck("promo-kod (katta-kichik harf farqsiz) -> B", l.content_id, B.id)
r = c.post("/api/public/lead", json={
    "full_name": "Sayt Tort", "phone": "+998 93 000 00 04"})
l = db.query(models.Lead).get(r.json()["lead_id"])
ck("belgisiz ariza — bog'lanmaydi", l.content_id, None)

print("\n=== 3. SOTUV VA TUSHUM ===")
st = models.Student(full_name="Aliyev Vali", phone="+998901110011",
                    branch_id=br.id, status="active")
db.add(st)
db.commit()
lead = db.query(models.Lead).get(L1)
lead.converted_student_id = st.id
lead.stage = "converted"
db.add_all([
    models.Payment(student_id=st.id, amount=540000, kind="payment"),
    models.Payment(student_id=st.id, amount=540000, kind="payment"),
    models.Payment(student_id=st.id, amount=-540000, kind="charge"),
])
db.commit()

pp = c.get("/api/smm/per-post?months=1", headers=HS).json()
rows = {x["id"]: x for x in pp["rows"]}
ra = rows[A.id]
ck("A: 3 ta lid (qo'lda 2 + saytdan 1)", ra["leads"], 3)
ck("A: 1 ta sotuv", ra["sales"], 1)
ck("A: tushum faqat to'lovlar (hisoblash emas)", ra["revenue"], 1080000.0)
ck("A: ko'rish va obuna ham yonida", (ra["views"], ra["follows"]),
   (9000, 18))
rb = rows[B.id]
ck("B: 2 ta lid, sotuv 0", (rb["leads"], rb["sales"]), (2, 0))
ck("g'oya holatidagi post jadvalda yo'q", IDEA.id in rows, False)
ck("jami lid", pp["totals"]["leads"], 5)
ck("jami tushum", pp["totals"]["revenue"], 1080000.0)

# Eski yagona post ekrani ham xuddi shu sonni ko'rsatadi
one = c.get(f"/api/content/{A.id}/attribution", headers=HB).json()
ck("post kartasidagi voronka bilan bir xil (lid)", one.get("leads"), 3)
ck("post kartasidagi voronka bilan bir xil (sotuv)", one.get("sales"), 1)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
