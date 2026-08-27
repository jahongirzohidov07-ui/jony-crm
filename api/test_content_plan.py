# -*- coding: utf-8 -*-
"""SMM KONTENT-PLAN (2026-08-27).

Jahongir "idealniy kontent plan" deb Excel yubordi: "sen ham SMMdagi
kontent planni shunaqa qism bo'limilarni bo'lishi kerak va ichiga
ssearniysi scriptini yozadigan ham bo'lishi kerak SMM manager kirib
shuni kopya qilishga oson bo'lsin, ozgartirishga oson bo'lsin va shu
video joylangangandan keyin linkini joylashi kerak link orqali
avtomat nechta korildi nechta koment like repost bolgani avtomat
hisoboti unga korinsin kuchli tahlil qilsa ob'ladi."

Tekshiriladi:
  1. Oylik jadval Excel ustunlarini to'liq qaytarishi
  2. Ssenariy yozilishi va saqlanishi
  3. NUSXA olish (seriyali kontent uchun) va nusxaga havola/natija
     KO'CHMASLIGI — u boshqa postniki
  4. Havoladan avtomat natija: platforma tanilishi, olinmasa
     SABABI aytilishi
  5. Avtomat 0 qaytarsa qo'lda kiritilgan raqam O'CHMASLIGI
  6. Tahlil: o'rtacha bo'yicha taqqoslash va tavsiya berish
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_cplan/db.sqlite"
os.makedirs("/tmp/verify_cplan", exist_ok=True)
if os.path.exists("/tmp/verify_cplan/db.sqlite"):
    os.remove("/tmp/verify_cplan/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import content as content_mod                       # noqa: E402
import content_fetch                                # noqa: E402
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


b = models.Branch(name="Zafar")
db.add(b)
db.commit()
u = models.User(username="marhabo", password_hash=hash_password("jonyjony"),
                role=roles.SMM_MANAGER, full_name="Marhabo",
                branch_id=b.id, is_active=1)
db.add(u)
db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "marhabo", "password": "jonyjony"}
).json()["access_token"]}

today = date.today()
d1 = today.replace(day=3).isoformat()

print("=== KONTENT YARATISH (Excel ustunlari) ===")
r = c.post("/api/content", headers=H, json={
    "title": "Ustoz-serial №1: Bekzod aka",
    "platform": "IG + TG", "fmt": "reels", "pillar": "teacher",
    "goal": "trust", "funnel": "mofu", "audience": "Ota-onalar",
    "planned_date": d1, "planned_time": "19:00",
    "branch_id": b.id, "owner_id": u.id,
    "hook": "30 bolalik guruhni oxirigacha diqqatda ushlab turish",
    "message": "Kuchli ustoz to'la guruhda ham har bolani ko'radi",
    "cta": "Guruhida joy bormi? DM'da so'rang",
})
ck("kontent yaratildi", r.status_code, 200)
cid = r.json()["id"]

# Excel ustunlari: dalil, syomka sanasi, kutilgan KPI, seriya
r = c.put(f"/api/content/{cid}", headers=H, json={
    "proof": "Guruh natijalari, dars lavhalari",
    "shoot_date": today.replace(day=1).isoformat(),
    "kpi_target": "10k ko'rish, 10 DM",
    "series": "Ustoz-serial",
    "script": "[0-3 s] HOOK\n30 bolalik guruh...",
})
ck("Excel ustunlari saqlandi", r.status_code, 200)

print("\n=== OYLIK JADVAL ===")
p = c.get(f"/api/smm/plan?year={today.year}&month={today.month}",
          headers=H).json()
ck("qator keldi", len(p["rows"]), 1)
row = p["rows"][0]
for k, nom in (("date", "Sana"), ("weekday", "Kun"), ("time", "Vaqt"),
               ("platform", "Platforma"), ("audience", "Auditoriya"),
               ("pillar_label", "Kontent ustuni"),
               ("funnel_label", "Voronka"), ("goal_label", "Maqsad"),
               ("title", "Mavzu"), ("hook", "Hook"),
               ("message", "Asosiy fikr"), ("proof", "Dalil"),
               ("fmt_label", "Format"), ("cta", "CTA"),
               ("owner", "Mas'ul"), ("shoot_date", "Syomka sanasi"),
               ("status_label", "Holati"), ("kpi_target", "Kutilgan KPI")):
    ck(f"  {nom}", bool(row.get(k)), True)
ck("  voronka nomi o'zbekcha", row["funnel_label"], "Ishonch")
ck("  ssenariy bor", "HOOK" in (row["script"] or ""), True)

print("\n=== NUSXA OLISH ===")
r = c.post(f"/api/content/{cid}/copy", headers=H,
           json={"title": "Ustoz-serial №2: Sarvar aka",
                 "planned_date": today.replace(day=14).isoformat()})
ck("nusxa olindi", r.status_code, 200)
n = r.json()
ck("  ssenariy ko'chdi", "HOOK" in (n["script"] or ""), True)
ck("  seriya ko'chdi", n["series"], "Ustoz-serial")
ck("  dalil ko'chdi", n["proof"], "Guruh natijalari, dars lavhalari")
ck("  holati G'oyaga qaytdi", n["status"], "idea")
ck("  HAVOLA ko'chmadi", n["post_url"], None)
ck("  NATIJA ko'chmadi", n["metrics"], None)
ck("  yangi sana", n["date"], today.replace(day=14).isoformat())

print("\n=== HAVOLADAN AVTOMAT NATIJA ===")
r = c.post(f"/api/content/{cid}/fetch", headers=H)
ck("havolasiz rad etiladi", r.status_code, 400)

c.put(f"/api/content/{cid}", headers=H,
      json={"post_url": "https://www.tiktok.com/@jony/video/7"})
r = c.post(f"/api/content/{cid}/fetch", headers=H).json()
ck("TikTok platformasi tanildi", r["platform"], "tiktok")
ck("  olinmadi", r["ok"], False)
ck("  SABABI aytildi", "qo'lda" in (r["note"] or ""), True)

print("\n=== QO'LDA KIRITILGAN RAQAM O'CHMAYDI ===")
c.put(f"/api/content/{cid}/metrics", headers=H,
      json={"views": 9000, "likes": 120, "comments": 15,
            "shares": 8, "reach": 10000})
r = c.post(f"/api/content/{cid}/fetch", headers=H).json()
ck("avtomat 0 qaytardi, eskisi qoldi", r["metrics"]["views"], 9000)
ck("  like ham joyida", r["metrics"]["likes"], 120)

print("\n=== PLATFORMA ANIQLASH ===")
for url, want in (("https://t.me/JonyAcademy/128", "telegram"),
                  ("https://youtu.be/abc12345", "youtube"),
                  ("https://www.instagram.com/reel/Cx1/", "instagram"),
                  ("https://vk.com/x", "other")):
    ck(f"  {want}", content_fetch.platform_of(url), want)

print("\n=== TAHLIL ===")
# Ikkita ustundan uchtadan post — taqqoslash uchun
mk = []
for i, (pil, fmt, views) in enumerate([
        ("teacher", "reels", 12000), ("teacher", "reels", 14000),
        ("teacher", "reels", 10000), ("culture", "static", 2000),
        ("culture", "static", 1500), ("culture", "static", 2500)]):
    rr = c.post("/api/content", headers=H, json={
        "title": f"Post {i}", "platform": "IG", "fmt": fmt,
        "pillar": pil, "goal": "trust", "funnel": "tofu",
        "planned_date": (today - timedelta(days=10 + i)).isoformat(),
        "planned_time": "19:00", "branch_id": b.id}).json()
    mk.append(rr["id"])
    x = db.query(models.Content).get(rr["id"])
    x.status = "published"
    db.commit()
    c.put(f"/api/content/{rr['id']}/metrics", headers=H,
          json={"views": views, "reach": views, "likes": views // 100,
                "comments": views // 500, "shares": views // 800})

a = c.get("/api/smm/content-analytics?months=3", headers=H).json()
ck("postlar sanaldi", a["count"] >= 6, True)
best = a["by_pillar"][0]
ck("eng yaxshi ustun — Teacher Branding",
   best["key"], "teacher")
ck("  o'rtacha ko'rish (jami emas)", best["avg_views"], 12000)
ck("  post soni", best["count"], 3)
ck("tavsiya berildi", len(a["tips"]) >= 1, True)
ck("  tavsiyada yo'nalish nomi bor",
   any("Teacher" in t["text"] for t in a["tips"]), True)
ck("hafta kuni kesimi bor", len(a["by_weekday"]) >= 1, True)
ck("eng yaxshi 5 post", len(a["top"]) <= 5, True)

print("\n=== SSENARIY SHABLONI ===")
t = roles.script_template("reels", hook="Sinov", message="Fikr",
                          proof="114 natija", cta="DM")
ck("shablonda vaqt bo'linishi", "[0-3 s]" in t, True)
ck("  hook o'z joyiga qo'yildi", "Sinov" in t, True)
ck("  dalil o'z joyiga", "114 natija" in t, True)
ck("noma'lum format uchun ham beriladi",
   bool(roles.script_template("noma'lum")), True)

print("\n" + ("HAMMASI O'TDI" if not fails else "XATO: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
