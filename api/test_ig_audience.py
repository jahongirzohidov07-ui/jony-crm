# -*- coding: utf-8 -*-
"""Instagram AUDITORIYA statistikasi (2026-09-27).

Jahongir: "jins bo'yicha, yosh guruhi, qayerdan kuzatishlar,
foydalanuvchilar aktiv paytlar ... chiroyli vizual chartlar bilan".

Tarmoqqa chiqilmaydi — soxta Graph API. Tekshiriladi: har ko'rsatkich
to'g'ri o'qiladi; biri rad etilsa qolganlari ishlaydi; kunlar bir kun
oldinga suriladi; soatlar Toshkent vaqtiga o'giriladi; 6 soat kesh;
o'zimizning postlardan tahlil va xulosalar; ruxsat.
"""
import os
import sys
from urllib.parse import urlparse, parse_qs

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_iga/db.sqlite"
os.makedirs("/tmp/verify_iga", exist_ok=True)
if os.path.exists("/tmp/verify_iga/db.sqlite"):
    os.remove("/tmp/verify_iga/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta           # noqa: E402
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: F401,E402
import ig_connect as ig                            # noqa: E402
import ig_audience as ia                           # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

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

print("=== 1. ULANMAGAN / RUXSAT ===")
ck("ustozga yopiq", c.get("/api/smm/instagram/audience", headers=HT)
   .status_code, 403)
r = c.get("/api/smm/instagram/audience", headers=HS)
ck("ulanmagan -> ok False", (r.status_code, r.json().get("ok")), (200, False))

# Ulangan holat
for k, v in ((ig.K_TOKEN, "EAAtest"), (ig.K_USER, "1784"),
             (ig.K_API, "fb")):
    ig._set(db, k, v, "test")
db.commit()

CALLS = []


def bd(results):
    return {"data": [{"total_value": {"breakdowns": [{"results": [
        {"dimension_values": [k], "value": v} for k, v in results]}]}}]}


def fake(url):
    CALLS.append(url)
    u = urlparse(url)
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    if u.path.endswith("/1784"):
        return {"username": "jony_academy", "followers_count": 12500,
                "media_count": 883, "profile_picture_url": "https://x/p.jpg"}
    m = q.get("metric")
    if m == "follower_demographics":
        return {"gender": bd([("F", 700), ("M", 280), ("U", 20)]),
                "age": bd([("18-24", 400), ("25-34", 350), ("13-17", 150)]),
                "city": bd([("Bekobod, Tashkent Region", 600),
                            ("Tashkent, Tashkent", 300)]),
                "country": bd([("UZ", 950), ("RU", 50)])}[q["breakdown"]]
    if m == "online_followers":
        raise RuntimeError("(#100) online_followers is not available")
    if m == "reach":
        return {"data": [{"values": [
            {"value": 1000, "end_time": "2026-09-25T07:00:00+0000"},
            {"value": 3000, "end_time": "2026-09-26T07:00:00+0000"}]}]}
    if m == "follower_count":
        return {"data": [{"values": [
            {"value": 12, "end_time": "2026-09-25T07:00:00+0000"},
            {"value": 40, "end_time": "2026-09-26T07:00:00+0000"}]}]}
    if m and m.startswith("reach,views"):
        return {"data": [{"name": n, "total_value": {"value": v}} for n, v in (
            ("reach", 50000), ("views", 120000), ("accounts_engaged", 3000),
            ("total_interactions", 9000))]}
    if m == "follows_and_unfollows":
        return bd([("FOLLOWER", 380), ("NON_FOLLOWER", 90)])
    raise RuntimeError("? " + url)


ig.HTTP["get"] = fake
# Bazada postlar: 25-sentabr (Toshkent) kuni bitta reels
db.add_all([
    models.IgMedia(ig_id="a", media_type="VIDEO", caption="Nemis tili reels",
                   posted_at=datetime(2026, 9, 25, 14, 0), views=90000,
                   reach=60000, likes=2000, permalink="https://i/a"),
    models.IgMedia(ig_id="b", media_type="IMAGE", caption="Qabul rasm",
                   posted_at=datetime(2026, 9, 20, 5, 0), views=4000,
                   reach=3000, likes=80, follows=7, permalink="https://i/b"),
    models.IgMedia(ig_id="c", media_type="VIDEO", caption="Eski",
                   posted_at=datetime.utcnow() - timedelta(days=400),
                   views=1, reach=1),
])
db.commit()

print("\n=== 2. META'DAN O'QISH ===")
r = c.get("/api/smm/instagram/audience", headers=HS)
d = r.json()
ck("200 + ok", (r.status_code, d.get("ok")), (200, True))
ck("profil", (d["profile"]["username"], d["profile"]["followers_count"]),
   ("jony_academy", 12500))
ck("jins (kattadan kichikka)", [x["key"] for x in d["gender"]], ["F", "M", "U"])
ck("yosh", d["age"][0], {"key": "18-24", "value": 400})
ck("shahar", d["city"][0]["value"], 600)
ck("davlat", d["country"][0]["key"], "UZ")
ck("onlayn rad etildi -> bo'sh, lekin qolganlari ishladi",
   (d["online_hours"], "online" in d["errors"]), ([], True))
ck("kun bir kun oldinga surildi", d["reach_daily"][0],
   {"date": "2026-09-24", "value": 1000})
ck("28 kun jami", (d["totals"]["reach"], d["totals"]["views"]),
   (50000, 120000))
ck("kelgan/ketgan obunachi", (d["follows"], d["unfollows"]), (380, 90))

print("\n=== 3. O'ZIMIZNING POSTLARDAN ===")
L = d["local"]
ck("6 oydan eskisi olinmadi", L["posts_180d"], 2)
ck("reels 1-o'rinda", L["types"][0]["type"], "Reels / video")
ck("top ko'rilgan", L["top_views"][0]["caption"], "Nemis tili reels")
ck("obuna olib kelgan (rasm)", L["top_follows"][0]["follows"], 7)
ck("eng ko'p obunachi kuni + o'sha kungi post",
   (L["best_days"][0]["date"], L["best_days"][0]["new_followers"],
    L["best_days"][0]["posts"][0]["caption"]),
   ("2026-09-25", 40, "Nemis tili reels"))
ck("soat Toshkentda (14 UTC -> 19)",
   [x["hour"] for x in L["post_hours"] if x["posts"]], [10, 19])
tips = " | ".join(x["text"] for x in d["tips"])
ck("xulosa: ayollar 70%", "70% — ayollar" in tips, True)
ck("xulosa: 18-24", "18-24" in tips, True)
ck("xulosa: Bekobod", "Bekobod" in tips, True)
ck("xulosa: sof o'sish", "+290" in tips, True)

print("\n=== 4. KESH (6 soat) ===")
n = len(CALLS)
c.get("/api/smm/instagram/audience", headers=HS)
ck("ikkinchi ochilishda Meta'ga so'rov yo'q", len(CALLS), n)
c.get("/api/smm/instagram/audience?refresh=1", headers=HS)
ck("Yangilash bosilsa qayta so'raydi", len(CALLS) > n, True)


def down(url):
    raise RuntimeError("Meta ishlamayapti")


ig.HTTP["get"] = down
r = c.get("/api/smm/instagram/audience?refresh=1", headers=HS)
ck("Meta yiqilsa eski natija ko'rinadi",
   (r.json().get("ok"), r.json()["profile"]["username"]),
   (True, "jony_academy"))

print("\n=== 5. ONLAYN SOATLAR TOSHKENTGA O'GIRILADI ===")
oh = ia._online({"data": [{"values": [{
    "end_time": "2026-09-20T07:00:00+0000",
    "value": {str(h): (100 if h == 8 else 1) for h in range(24)}}]}]})
ck("PDT 08:00 -> Toshkent 20:00", max(range(24), key=lambda i: oh[i]), 20)
oh2 = ia._online({"data": [{"values": [{
    "end_time": "2026-12-20T08:00:00+0000", "value": {"8": 100, "9": 1}}]}]})
ck("qishda PST 08:00 -> Toshkent 21:00", max(range(24), key=lambda i: oh2[i]), 21)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
