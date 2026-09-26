# -*- coding: utf-8 -*-
"""Instagram ulash (2026-09-26).

Jahongir: "instagramni ulaylik unda avtomat ko'rinishi kerak ... Shuni
ulab ber o'zing to'liq. Har bir videodan nechta odam murojaat qildi,
nechta sotuv boldi aniq avtomat hisoblash".

Tarmoqqa chiqilmaydi: ig_connect.HTTP["get"] soxta Graph API bilan
almashtiriladi. Tekshiriladi:
  - token faqat ruxsatli rolga, javobda to'liq ko'rinmaydi;
  - akkaunt raqami avtomat topiladi;
  - har post: havola bo'yicha / shu kungi reja bo'yicha bog'lanadi,
    rejada yo'q bo'lsa avtomat qo'shiladi;
  - raqamlar ContentMetric'ga tushadi (0 kelsa qo'lda yozilgani qoladi);
  - qayta sinxron dublikat yaratmaydi; uzish hech narsani o'chirmaydi.
"""
import os
import sys
from urllib.parse import urlparse, parse_qs

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_ig/db.sqlite"
os.makedirs("/tmp/verify_ig", exist_ok=True)
if os.path.exists("/tmp/verify_ig/db.sqlite"):
    os.remove("/tmp/verify_ig/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, datetime, timedelta      # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import ig_connect as ig                             # noqa: E402
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
for un, role in (("boss", roles.FOUNDER), ("marhabo", roles.SMM_MANAGER),
                 ("ustoz", roles.TEACHER)):
    db.add(models.User(username=un, password_hash=hash_password("jonyjony"),
                       role=role, full_name=un.title(), branch_id=br.id,
                       is_active=1))
db.commit()


def tok(un):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": un, "password": "jonyjony"}
    ).json()["access_token"]}


HB, HS, HT = tok("boss"), tok("marhabo"), tok("ustoz")

today = date.today()
d1, d2, d3 = (today - timedelta(days=1), today - timedelta(days=2),
              today - timedelta(days=3))
TOKEN = "EAAtest" + "x" * 40 + "WXYZ"
MEDIA = [
    {"id": "m1", "caption": "Olimpiada g'oliblari\nbatafsil",
     "media_type": "VIDEO", "permalink": "https://www.instagram.com/reel/AAA111/",
     "timestamp": f"{d1}T10:00:00+0000", "like_count": 120,
     "comments_count": 7},
    {"id": "m2", "caption": "Ustozlar bilan tanishing",
     "media_type": "VIDEO", "permalink": "https://www.instagram.com/reel/BBB222/",
     "timestamp": f"{d2}T09:00:00+0000", "like_count": 80,
     "comments_count": 3},
    {"id": "m3", "caption": "Rejada yo'q post", "media_type": "IMAGE",
     "permalink": "https://www.instagram.com/p/CCC333/",
     "timestamp": f"{d3}T08:00:00+0000", "like_count": 40,
     "comments_count": 0},
    {"id": "old", "caption": "Juda eski", "media_type": "IMAGE",
     "permalink": "https://www.instagram.com/p/OLD999/",
     "timestamp": f"{today - timedelta(days=200)}T08:00:00+0000",
     "like_count": 1, "comments_count": 0},
]
INS = {"m1": {"reach": 5000, "saved": 40, "shares": 25, "views": 9000,
              "follows": 18, "profile_visits": 210},
       "m2": {"reach": 3000, "saved": 0, "shares": 10, "views": 4000,
              "follows": 5, "profile_visits": 90},
       "m3": {"reach": 800, "saved": 2, "shares": 1, "views": 0,
              "follows": 1, "profile_visits": 12}}
CALLS = []


def fake_get(url):
    CALLS.append(url)
    u = urlparse(url)
    q = parse_qs(u.query)
    if q.get("access_token", [""])[0] != TOKEN:
        raise RuntimeError("Invalid OAuth access token")
    p = u.path
    if p.endswith("/me/accounts"):
        return {"data": [{"name": "Jony Academy", "instagram_business_account":
                          {"id": "1784", "username": "jonyacademy",
                           "followers_count": 12500}}]}
    if p.endswith("/1784/media"):
        return {"data": MEDIA}
    if p.endswith("/insights"):
        mid = p.split("/")[-2]
        return {"data": [{"name": k, "values": [{"value": v}]}
                         for k, v in INS.get(mid, {}).items()]}
    if p.endswith("/1784"):
        return {"followers_count": 12500}
    raise RuntimeError("kutilmagan so'rov " + p)


ig.HTTP["get"] = fake_get

# Kontent-plan: m1 havolasi bilan, m2 shu kunga havolasiz rejalangan
c1 = models.Content(title="Olimpiada reels", platform="instagram",
                    planned_date=d1, status="published", branch_id=br.id,
                    post_url="https://instagram.com/reel/AAA111/?igsh=abc")
c2 = models.Content(title="Ustozlar reels", platform="instagram",
                    planned_date=d2, status="ready", branch_id=br.id)
db.add_all([c1, c2])
db.commit()
db.add(models.ContentMetric(content_id=c2.id, saves=33, source="manual"))
db.commit()
n_before = db.query(models.Content).count()

print("=== 1. ULANMAGAN HOLAT ===")
s = c.get("/api/smm/instagram", headers=HS).json()
ck("ulanmagan", s["connected"], False)
ck("SMM token joylay oladi", s["can_set_token"], True)
ck("cron token yo'q bo'lsa jim o'tadi", ig.cron_sync(db)["ok"], False)
ck("ustoz ko'ra olmaydi",
   c.get("/api/smm/instagram", headers=HT).status_code, 403)

print("\n=== 2. TOKEN JOYLASH ===")
ck("qisqa token rad",
   c.post("/api/smm/instagram/token", json={"token": "abc"},
          headers=HB).status_code, 400)
r = c.post("/api/smm/instagram/token", json={"token": "EAA" + "y" * 40},
           headers=HB)
ck("ishlamaydigan token rad (saqlanmaydi)", r.status_code, 400)
ck("  bazaga yozilmadi", ig._s(db, ig.K_TOKEN), "")
ck("ustoz joylay olmaydi",
   c.post("/api/smm/instagram/token", json={"token": TOKEN},
          headers=HT).status_code, 403)
r = c.post("/api/smm/instagram/token", json={"token": TOKEN}, headers=HB)
j = r.json()
ck("ulandi", (r.status_code, j.get("username")), (200, "jonyacademy"))
ck("akkaunt raqami avtomat topildi", j.get("account_id"), "1784")
ck("javobda token YO'Q", TOKEN in r.text, False)
s = c.get("/api/smm/instagram", headers=HS).json()
ck("status: ulangan", s["connected"], True)
ck("status: token yashirin", s["token"], "•••• WXYZ")
ck("status javobida ham token yo'q",
   TOKEN in c.get("/api/smm/instagram", headers=HS).text, False)

print("\n=== 3. SINXRON NATIJASI (token joylanganda o'zi ishladi) ===")
sy = j["sync"]
ck("3 ta yangi post o'qildi (200 kunlik eski olinmadi)", sy["seen"], 3)
ck("2 tasi rejaga bog'landi", sy["linked"], 2)
ck("1 tasi rejaga avtomat qo'shildi", sy["created"], 1)
db.expire_all()
media = {m.ig_id: m for m in db.query(models.IgMedia).all()}
ck("ig_media: 3 ta", sorted(media), ["m1", "m2", "m3"])
ck("m1 -> havola bo'yicha c1", media["m1"].content_id, c1.id)
ck("m2 -> shu kungi reja c2", media["m2"].content_id, c2.id)
c2r = db.query(models.Content).get(c2.id)
ck("  c2 ga havola yozildi", c2r.post_url, MEDIA[1]["permalink"])
ck("  c2 holati 'joylandi'", c2r.status, "published")
new = db.query(models.Content).get(media["m3"].content_id)
ck("m3 -> yangi qator", (new.title, new.status, new.planned_date),
   ("Rejada yo'q post", "published", d3))
m1 = (db.query(models.ContentMetric)
      .filter(models.ContentMetric.content_id == c1.id).first())
ck("c1 raqamlari", (m1.views, m1.reach, m1.likes, m1.comments, m1.saves,
                    m1.shares, m1.follows, m1.profile_visits, m1.source),
   (9000, 5000, 120, 7, 40, 25, 18, 210, "auto"))
m2 = (db.query(models.ContentMetric)
      .filter(models.ContentMetric.content_id == c2.id).first())
ck("c2: saqlash 0 keldi -> qo'lda yozilgan 33 qoldi", m2.saves, 33)
ck("c2: obunachi", m2.follows, 5)
last = (db.query(models.SocialStat)
        .filter(models.SocialStat.platform == "instagram").first())
ck("obunachilar soni ham yozildi", last.followers if last else None, 12500)

print("\n=== 4. QAYTA SINXRON — DUBLIKAT YO'Q ===")
r = c.post("/api/smm/instagram/sync", headers=HS).json()
ck("yana 3 ta o'qildi", r["seen"], 3)
ck("yangi qator qo'shilmadi", r["created"], 0)
db.expire_all()
ck("ig_media hali 3 ta", db.query(models.IgMedia).count(), 3)
ck("kontentlar: faqat 1 ta qo'shilgan",
   db.query(models.Content).count(), n_before + 1)

print("\n=== 5. QO'LDA QAYTA BOG'LASH ===")
r = c.post("/api/smm/instagram/link",
           json={"media_id": media["m3"].id, "content_id": c2.id},
           headers=HS)
ck("qo'lda bog'landi", r.status_code, 200)

print("\n=== 6. UZISH — HECH NARSA O'CHMAYDI ===")
ck("SMM uza oladi",
   c.post("/api/smm/instagram/disconnect", headers=HS).status_code, 200)
db.expire_all()
ck("token bo'shadi", ig._s(db, ig.K_TOKEN), "")
ck("postlar joyida", db.query(models.IgMedia).count(), 3)
ck("raqamlar joyida",
   db.query(models.ContentMetric)
   .filter(models.ContentMetric.content_id == c1.id).first().views, 9000)
ck("auditda ulash/uzish yozilgan",
   db.query(models.AuditLog)
   .filter(models.AuditLog.entity == "integration").count(), 2)
ck("audit yozuvida ham token yo'q",
   any(TOKEN in (a.note or "") for a in db.query(models.AuditLog).all()),
   False)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
