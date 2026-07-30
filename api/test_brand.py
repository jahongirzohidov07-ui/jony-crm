"""Brend kitob, media rozilik, bilimlar bazasi, analitika, KPI, hisobot."""
import os, sys
from datetime import date, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/brand_test.db"
if os.path.exists("/tmp/brand_test.db"):
    os.remove("/tmp/brand_test.db")

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


TODAY = date.today()
NOW = datetime.utcnow()
db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
BID = b.id
for u, role in [("asos", "founder"), ("smm", "smm_manager"),
                ("ustoz", "teacher")]:
    db.add(models.User(username=u, password_hash=hash_password("x"),
                       full_name=u.capitalize(), role=role,
                       branch_id=None if role == "founder" else BID))
db.commit(); db.close()

H = tok("asos")
HS = tok("smm")
HT = tok("ustoz")

print("=== 1. BREND KITOB BRANDBOOKDAN YUKLANDI ===")

d = client.get("/api/brand", headers=HS).json()
ck("manba ko'rsatilgan", d["source"], "Jony Academy brandbook 2023")
ck("asosiy rang", d["primary"], "#1A6FE4")
ck("ikkilamchi rang", d["secondary"], "#4375B9")
ck("brend so'zi", d["word"], "Muhit")

colors = d["sections"]["color"]
ck("ranglar yuklandi", len(colors), 8)
prim = next(c for c in colors if c["value"] == "#1A6FE4")
ck("asosiy ko'k PDFdan", prim["source"], "PDF")
ck("PDFdagi rang to'ldirilgan emas", prim["is_filled"], False)

fill = [c for c in colors if c["is_filled"]]
ck("qo'shimcha ranglar belgilangan", len(fill) >= 5, True)

fonts = d["sections"]["font"]
ck("asosiy shrift", fonts[0]["title"], "HelveticaNeueCyr")
ck("veb uchun zaxira bor",
   any("Inter" in f["title"] for f in fonts), True)

print("\n=== 2. BRANDBOOKDA YO'Q NARSALAR TO'LDIRILDI ===")

ck("kamchiliklar ro'yxati", len(d["gaps"]) >= 8, True)
ck("ovoz qoidalari qo'shildi", len(d["sections"]["tone"]), 10)
ck("logotip taqiqlari qo'shildi", len(d["sections"]["dont"]), 8)
ck("ijtimoiy tarmoq o'lchamlari", len(d["sections"]["spec"]), 6)

logo = d["sections"]["logo"]
ck("xavfsizlik maydoni PDFdan", logo[0]["source"], "PDF")
minsize = next(r for r in logo if "kichik" in r["title"])
ck("eng kichik o'lcham to'ldirildi", minsize["source"], "TO'LDIRILDI")

# Vizitkadagi email xatosi
contacts = d["sections"]["contact"]
mail = next(c for c in contacts if c["title"] == "Email")
ck("email tuzatildi", mail["value"], "jonyacademy@gmail.com")
ck("xato izohlandi", "@ belgisi" in (mail["note"] or ""), True)

print("\n=== 3. TAHRIRLASH VA TASDIQLASH ===")

ck("ustoz brendni o'qiy oladi",
   client.get("/api/brand", headers=HT).status_code, 200)
ck("ustoz brendni tahrirlay olmaydi",
   client.put(f"/api/brand/{minsize['id']}", headers=HT,
              json={"note": "boshqa"}).status_code, 403)

r = client.put(f"/api/brand/{minsize['id']}", headers=H,
               json={"note": "Ekranda 32 px"})
row = next(x for x in r.json() if x["id"] == minsize["id"])
ck("asoschi tahrirladi", row["note"], "Ekranda 32 px")
ck("tasdiqlangan deb belgilandi", row["source"], "Tasdiqlangan")

# Seed qayta yozmaydi
db = SessionLocal(); main._seed_brand(db); db.close()
d2 = client.get("/api/brand", headers=HS).json()
row2 = next(x for x in d2["sections"]["logo"] if x["id"] == minsize["id"])
ck("qayta seed tahrirni buzmadi", row2["note"], "Ekranda 32 px")

print("\n=== 4. MEDIA VA ROZILIK ===")

r = client.post("/api/media", headers=HS, json={
    "name": "Abdulaziz IELTS 7.0 video", "kind": "video",
    "branch_id": BID, "event": "Sertifikat topshirish",
    "taken_on": TODAY.isoformat(), "consent": "social",
    "consent_until": (TODAY + timedelta(days=200)).isoformat()})
ck("media qo'shildi", r.status_code, 200)
M1 = r.json()["id"]
ck("joylash mumkin", r.json()["can_publish"], True)
ck("muallif avtomat", r.json()["author"], "Smm")

# Rozilik kutilayotgan
r = client.post("/api/media", headers=HS, json={
    "name": "Sinf fotosi", "kind": "photo", "consent": "pending"})
M2 = r.json()["id"]
ck("rozilik kutilayotgani joylanmaydi", r.json()["can_publish"], False)

# Muddati tugagan
r = client.post("/api/media", headers=HS, json={
    "name": "O'tgan yilgi video", "kind": "video", "consent": "social",
    "consent_until": (TODAY - timedelta(days=5)).isoformat()})
M3 = r.json()["id"]
ck("muddati tugagani taqiqlandi", r.json()["consent"], "forbidden")
ck("joylash to'sildi", r.json()["can_publish"], False)

# Tugash arafasida
r = client.post("/api/media", headers=HS, json={
    "name": "Yaqinda tugaydi", "kind": "photo", "consent": "social",
    "consent_until": (TODAY + timedelta(days=10)).isoformat()})
ck("tugash ogohlantirildi", r.json()["expiring"], True)
ck("necha kun qolgani", r.json()["days_left"], 10)

d = client.get("/api/media", headers=HS).json()
ck("jami media", d["total"], 4)
ck("joylash mumkin bo'lganlar", d["publishable"], 2)
ck("muddati tugaganlar", d["expired"], 1)
ck("tugash arafasidagilar", d["expiring"], 1)

d = client.get("/api/media?publishable=1", headers=HS).json()
ck("faqat ruxsat berilganlar", len(d["rows"]), 2)

ck("ustoz media ko'rmaydi",
   client.get("/api/media", headers=HT).status_code, 403)

# Ota-ona fikrini o'zgartirdi
r = client.put(f"/api/media/{M1}", headers=HS,
               json={"consent": "forbidden"})
ck("rozilik qaytarib olindi", r.json()["can_publish"], False)

print("\n=== 5. BILIMLAR BAZASI ===")

d = client.get("/api/kb", headers=HT).json()
ck("boshlang'ich maqolalar", len(d["rows"]) >= 6, True)
ck("kategoriyalar", len(d["categories"]), 6)
ck("ustoz o'qiy oladi", len(d["rows"]) > 0, True)
ck("ustoz yoza olmaydi", d["can_edit"], False)

a = next(x for x in d["rows"] if "Muhit" in x["title"])
ck("brend so'zi maqolasi bor", a["category"], "brand")

r = client.post(f"/api/kb/{a['id']}/view", headers=HT)
ck("ko'rilgani sanaldi", r.json()["views"], 1)

r = client.post("/api/kb", headers=HS, json={
    "title": "Story uchun qoidalar", "category": "template",
    "body": "Kuniga 3 ta story."})
ck("maqola qo'shildi", r.status_code, 200)
ck("eskirgan emas", r.json()["stale"], False)

ck("ustoz maqola qo'sha olmaydi",
   client.post("/api/kb", headers=HT,
               json={"title": "x"}).status_code, 403)

d = client.get("/api/kb?q=rozilik", headers=HS).json()
ck("qidiruv ishladi", len(d["rows"]) >= 1, True)

# Eskirgan maqola
db = SessionLocal()
old = db.query(models.KbArticle).first()
old.reviewed_at = TODAY - timedelta(days=400)
db.commit(); db.close()
d = client.get("/api/kb", headers=HS).json()
ck("eskirgan aniqlandi", d["stale"], 1)

print("\n=== 6. KONTENT BREND TEKSHIRUVI ===")

r = client.post("/api/content", headers=HS, json={
    "title": "IELTS 7.0 natija", "platform": "ig_reels",
    "pillar": "results", "goal": "lead", "branch_id": BID,
    "planned_date": (TODAY - timedelta(days=3)).isoformat()})
C1 = r.json()["id"]

d = client.get(f"/api/content/{C1}/brand", headers=HS).json()
ck("7 ta tekshiruv", d["total"], 7)
ck("hech biri bajarilmagan", d["done"], 0)
ck("nashr to'sildi", d["can_publish"], False)
ck("nima yetishmayotgani aytildi", len(d["blocked"]), 2)

client.post(f"/api/content/{C1}/brand", headers=HS,
            json={"key": "claim", "ok": True})
r = client.post(f"/api/content/{C1}/brand", headers=HS,
                json={"key": "consent", "ok": True,
                      "note": "Ota-onadan yozma rozilik bor"})
ck("majburiylar bajarildi", r.json()["can_publish"], True)
ck("bajarilganlar sanaldi", r.json()["done"], 2)

r = client.post(f"/api/content/{C1}/brand", headers=HS,
                json={"key": "yolgon", "ok": True})
ck("noma'lum tekshiruv rad etildi", r.status_code, 400)

print("\n=== 7. ANALITIKA KESIMLARI ===")

client.post(f"/api/content/{C1}/status", headers=HS,
            json={"status": "ready"})
client.post(f"/api/content/{C1}/publish", headers=HS,
            json={"post_url": "https://instagram.com/p/a"})
client.put(f"/api/content/{C1}/metrics", headers=HS, json={
    "reach": 50000, "likes": 1000, "comments": 100, "saves": 200,
    "shares": 50, "dms": 40, "profile_visits": 800, "link_clicks": 300})

# Ko'p ko'rilgan, lekin natijasiz kontent
r = client.post("/api/content", headers=HS, json={
    "title": "Kulgili video", "platform": "ig_reels", "pillar": "fun",
    "goal": "reach", "branch_id": BID,
    "planned_date": (TODAY - timedelta(days=2)).isoformat()})
C2 = r.json()["id"]
client.post(f"/api/content/{C2}/status", headers=HS,
            json={"status": "ready"})
client.post(f"/api/content/{C2}/publish", headers=HS,
            json={"post_url": "https://instagram.com/p/b"})
client.put(f"/api/content/{C2}/metrics", headers=HS,
           json={"reach": 400000, "likes": 9000})

# Birinchi kontentdan lead va sotuv
db = SessionLocal()
s = models.Student(full_name="Dilnoza", branch_id=BID, status="active",
                   enrolled_date=TODAY - timedelta(days=2))
db.add(s); db.commit()
msg = models.SocialMessage(
    channel="instagram", kind="dm", author="Dilnoza", content_id=C1,
    received_at=NOW - timedelta(minutes=10),
    first_reply_at=NOW - timedelta(minutes=2), status="lead")
db.add(msg); db.commit()
lead = models.Lead(full_name="Dilnoza", source="instagram",
                   content_id=C1, social_message_id=msg.id,
                   stage="won", converted_student_id=s.id,
                   branch_id=BID, created_at=NOW - timedelta(days=2))
db.add(lead); db.commit()
msg.lead_id = lead.id
db.add(models.Payment(student_id=s.id, amount=480000, kind="payment",
                      created_at=TODAY - timedelta(days=1)))
db.commit(); db.close()

d = client.get("/api/smm/analytics?dim=pillar", headers=HS).json()
ck("kesim nomi", d["dim_label"], "Yo'nalish")
ck("8 ta kesim tanlovi", len(d["dims"]), 8)
ck("ikkita yo'nalish", len(d["rows"]), 2)
ck("tushum bo'yicha birinchi", d["rows"][0]["revenue"], 480000)
ck("eng yaxshisi natijalar", d["best"]["label"], "Student Results")

ck("qamrov tuzog'i topildi", d["trap"] is not None, True)
ck("tuzoq: ko'p ko'rilgan", d["trap"]["reach"], 400000)
ck("tuzoq: pul yo'q", d["trap"]["revenue"], 0)
ck("tuzoq: yaxshirog'i", d["trap"]["better"], "Student Results")

d = client.get("/api/smm/analytics?dim=format", headers=HS).json()
ck("format kesimi ishladi", d["rows"][0]["label"], "Reels / qisqa video")

d = client.get("/api/smm/analytics?dim=weekday", headers=HS).json()
ck("hafta kuni kesimi", len(d["rows"]) >= 1, True)

ck("noto'g'ri kesim rad etildi",
   client.get("/api/smm/analytics?dim=xyz", headers=HS).status_code, 400)
ck("ustoz analitikani ko'rmaydi",
   client.get("/api/smm/analytics", headers=HT).status_code, 403)

print("\n=== 8. SMM KPI ===")

d = client.get("/api/smm/kpi?months=1", headers=HS).json()
ck("7 ta mezon", len(d["parts"]), 7)
ck("jami og'irlik 100",
   sum(w["weight"] for w in d["weights"]), 100)
ck("ball 0-100 oralig'ida", 0 <= d["score"] <= 100, True)
ck("baho berildi", d["label"] in
   ["Ajoyib", "Yaxshi", "Qoniqarli", "Past"], True)
ck("2 ta kontent joylandi", d["published"], 2)

brand = next(p for p in d["parts"] if p["key"] == "brand")
# 2 kontent × 2 majburiy tekshiruv = 4, bajarilgani 2 → 50%
ck("brend mezoni hisoblandi", brand["percent"], 50)

inbox = next(p for p in d["parts"] if p["key"] == "inbox")
ck("SLA to'liq", d["sla_percent"], 100.0)
ck("inbox ballari to'liq", inbox["score"], 10.0)

leads = next(p for p in d["parts"] if p["key"] == "leads")
ck("lead mezonida izoh bor", "mo'ljal" in leads["note"], True)

print("\n=== 9. HISOBOT YIG'UVCHI ===")

d = client.get("/api/smm/report?period=month"
               f"&start={(TODAY - timedelta(days=7)).isoformat()}"
               f"&end={TODAY.isoformat()}", headers=HS).json()
ck("9 ta bo'lim", len(d["sections"]), 9)
ck("joylangan kontentlar", d["published"], 2)
ck("qamrov qo'shildi", d["totals"]["reach"], 450000)
ck("tushum", d["totals"]["revenue"], 480000)
ck("voronka bor", len(d["funnel"]), 10)
ck("eng yaxshilari", d["top"][0]["title"], "IELTS 7.0 natija")
ck("ishlamagani ajratildi", d["weak"][0]["title"], "Kulgili video")
ck("kesimlar", len(d["dims"]), 3)
ck("xulosa matni yozildi", "kontent joylandi" in d["summary"], True)
ck("KPI kiritildi", d["kpi"]["score"] == d["kpi"]["score"], True)
ck("tavsiya berildi", len(d["tips"]) >= 1, True)

r = client.post("/api/smm/report", headers=HS, json={
    "period": "month",
    "start_date": (TODAY - timedelta(days=7)).isoformat(),
    "end_date": TODAY.isoformat()})
ck("hisobot saqlandi", r.status_code, 200)
RID = r.json()["id"]
saved_reach = r.json()["totals"]["reach"]

# Ma'lumot o'zgardi — saqlangan hisobot o'zgarmaydi
client.put(f"/api/content/{C2}/metrics", headers=HS,
           json={"reach": 999999})
d = client.get(f"/api/smm/report/{RID}", headers=HS).json()
ck("saqlangan hisobot muzlatilgan", d["totals"]["reach"], saved_reach)
ck("muzlatilgani belgilandi", d["frozen"], True)

d = client.get("/api/smm/report", headers=HS).json()
ck("saqlanganlar ro'yxati", len(d["saved"]) >= 1, True)

ck("ustoz hisobotni ko'rmaydi",
   client.get("/api/smm/report", headers=HT).status_code, 403)

print("\n=== 10. DAVR HISOBI ===")

s1, e1 = main._period_range("month", date(2026, 7, 15))
ck("o'tgan oy boshi", s1.isoformat(), "2026-06-01")
ck("o'tgan oy oxiri", e1.isoformat(), "2026-06-30")

s2, e2 = main._period_range("week", date(2026, 7, 15))   # chorshanba
ck("o'tgan hafta dushanba", s2.isoformat(), "2026-07-06")
ck("o'tgan hafta yakshanba", e2.isoformat(), "2026-07-12")

s3, e3 = main._period_range("quarter", date(2026, 7, 15))
ck("o'tgan chorak boshi", s3.isoformat(), "2026-04-01")
ck("o'tgan chorak oxiri", e3.isoformat(), "2026-06-30")

ck("KPI bahosi: 95", roles.kpi_band(95)[0], "Ajoyib")
ck("KPI bahosi: 80", roles.kpi_band(80)[0], "Yaxshi")
ck("KPI bahosi: 65", roles.kpi_band(65)[0], "Qoniqarli")
ck("KPI bahosi: 40", roles.kpi_band(40)[0], "Past")

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
