# -*- coding: utf-8 -*-
"""Instagram: "Facebook orqali ulash" (token ko'chirmasdan) — 2026-09-26.

Jahongir: "instagramni qilib ber qanday qilaman ozing qilib ber hammasini".
Tarmoqqa chiqilmaydi: ig_connect.HTTP["get"] soxta Graph API.
"""
import os
import sys
from urllib.parse import urlparse, parse_qs

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_igo/db.sqlite"
os.makedirs("/tmp/verify_igo", exist_ok=True)
if os.path.exists("/tmp/verify_igo/db.sqlite"):
    os.remove("/tmp/verify_igo/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import ig_connect as ig                             # noqa: E402
from database import SessionLocal                   # noqa: E402
from auth import hash_password                      # noqa: E402

c = TestClient(main.app, follow_redirects=False)
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
for un, role in (("boss", roles.FOUNDER), ("ustoz", roles.TEACHER)):
    db.add(models.User(username=un, password_hash=hash_password("jonyjony"),
                       role=role, full_name=un.title(), branch_id=br.id,
                       is_active=1))
db.commit()


def tok(un):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": un, "password": "jonyjony"}
    ).json()["access_token"]}


HB, HT = tok("boss"), tok("ustoz")
APP_ID, SECRET = "1234567890123456", "a" * 32
PAGE_TOKEN = "EAApage" + "p" * 40
SEEN = []


def fake_get(url):
    SEEN.append(url)
    u = urlparse(url)
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    if u.path.endswith("/oauth/access_token"):
        assert q["client_secret"] == SECRET
        if q.get("code") == "GOOD":
            return {"access_token": "SHORT"}
        if q.get("grant_type") == "fb_exchange_token":
            return {"access_token": "LONG"}
        raise RuntimeError("bad code")
    if u.path.endswith("/me/accounts"):
        assert q["access_token"] == "LONG"
        return {"data": [
            {"name": "Boshqa sahifa", "access_token": "x" * 30},
            {"name": "Jony Academy", "access_token": PAGE_TOKEN,
             "instagram_business_account": {"id": "1784",
                                            "username": "jony_academy"}}]}
    if u.path.endswith("/1784/media"):
        return {"data": []}
    if u.path.endswith("/1784"):
        return {"followers_count": 12000}
    raise RuntimeError("kutilmagan " + u.path)


ig.HTTP["get"] = fake_get

print("=== 1. ILOVA SOZLANMAGAN ===")
s = c.get("/api/smm/instagram", headers=HB).json()
ck("app yo'q", (s["app_id"], s["has_secret"]), (None, False))
ck("qaytish manzili ko'rsatiladi",
   s["redirect_uri"].endswith("/api/smm/instagram/oauth/callback"), True)
ck("ilovasiz start rad",
   c.post("/api/smm/instagram/oauth/start", headers=HB).status_code, 400)

print("\n=== 2. APP ID / SECRET SAQLASH ===")
ck("noto'g'ri secret rad",
   c.post("/api/smm/instagram/app", headers=HB,
          json={"app_id": APP_ID, "app_secret": "qisqa"}).status_code, 400)
ck("ustoz sozlay olmaydi",
   c.post("/api/smm/instagram/app", headers=HT,
          json={"app_id": APP_ID, "app_secret": SECRET}).status_code, 403)
r = c.post("/api/smm/instagram/app", headers=HB,
           json={"app_id": APP_ID, "app_secret": SECRET})
ck("saqlandi", r.status_code, 200)
s = c.get("/api/smm/instagram", headers=HB)
ck("status: app bor, secret javobda YO'Q",
   (s.json()["app_id"], s.json()["has_secret"], SECRET in s.text),
   (APP_ID, True, False))

print("\n=== 3. FACEBOOK DIALOGI ===")
url = c.post("/api/smm/instagram/oauth/start", headers=HB).json()["url"]
q = {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}
ck("facebook dialogiga", urlparse(url).netloc, "www.facebook.com")
ck("kerakli ruxsatlar so'raladi",
   "instagram_manage_insights" in q["scope"], True)
ck("secret havolada YO'Q", SECRET in url, False)
STATE = q["state"]

print("\n=== 4. QAYTIB KELISH ===")
r = c.get(ig.CALLBACK_PATH, params={"code": "GOOD", "state": "soxta"})
ck("soxta state rad (token saqlanmaydi)",
   ("ig_error" in r.headers["location"], ig._s(db, ig.K_TOKEN)), (True, ""))
r = c.get(ig.CALLBACK_PATH, params={"error": "access_denied",
                                     "error_description": "User denied"})
ck("rad etilsa xabar bilan qaytadi", "ig_error=User" in r.headers["location"],
   True)
r = c.get(ig.CALLBACK_PATH, params={"code": "GOOD", "state": STATE})
ck("muvaffaqiyat -> SMM Instagram oynasi",
   r.headers["location"].endswith("/smm?tab=instagram&ig=ok"), True)
db.expire_all()
ck("SAHIFA tokeni saqlandi (muddatsiz)", ig._s(db, ig.K_TOKEN), PAGE_TOKEN)
ck("to'g'ri Instagram akkaunt", (ig._s(db, ig.K_USER), ig._s(db, ig.K_NAME)),
   ("1784", "jony_academy"))
ck("darrov sinxron qilindi",
   any("/1784/media" in u for u in SEEN), True)
s = c.get("/api/smm/instagram", headers=HB)
ck("status: ulangan, token javobda yo'q",
   (s.json()["connected"], PAGE_TOKEN in s.text), (True, False))
ck("auditda secret ham, token ham yo'q",
   any(x in (a.note or "") for a in db.query(models.AuditLog).all()
       for x in (SECRET, PAGE_TOKEN)), False)

print("\n=== 5. FACEBOOK LOGIN FOR BUSINESS (config_id) ===")
ck("config yo'q -> scope bilan (config_id yo'q)",
   ("config_id" in q, s.json().get("config_id")), (False, None))
c.post("/api/smm/instagram/app", headers=HB,
       json={"app_id": "1614151326992230"})
u2 = c.post("/api/smm/instagram/oauth/start", headers=HB).json()["url"]
q2 = {k: v[0] for k, v in parse_qs(urlparse(u2).query).items()}
ck("JonyOS ilovasi -> config_id 1127900133139057, scope yuborilmaydi",
   (q2.get("config_id"), "scope" in q2), ("1127900133139057", False))
ck("secret saqlanib qoldi (App ID yangilanganda)",
   c.get("/api/smm/instagram", headers=HB).json()["has_secret"], True)
c.post("/api/smm/instagram/app", headers=HB,
       json={"app_id": "1614151326992230", "config_id": "99887766554433"})
u3 = c.post("/api/smm/instagram/oauth/start", headers=HB).json()["url"]
q3 = {k: v[0] for k, v in parse_qs(urlparse(u3).query).items()}
ck("qo'lda kiritilgan config_id ustun", q3.get("config_id"), "99887766554433")
ck("status config_id ko'rsatadi",
   c.get("/api/smm/instagram", headers=HB).json()["config_id"],
   "99887766554433")

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
