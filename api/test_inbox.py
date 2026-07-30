"""Social inbox, SLA, DM'dan lead va kontent atributsiyasi."""
import os, sys
from datetime import date, datetime, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/inbox_test.db"
if os.path.exists("/tmp/inbox_test.db"):
    os.remove("/tmp/inbox_test.db")

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

# Test sutkaning istalgan soatida bir xil natija berishi kerak.
# Shuning uchun markaz vaqt mintaqasi shunday qo'yiladiki, HOZIRGI
# payt mahalliy vaqt bo'yicha kunduz soat 14:00 ga to'g'ri kelsin.
# Bu _is_off_hours ning haqiqiy kodini tekshirishga xalaqit bermaydi.
roles.TIMEZONE_OFFSET_HOURS = (14 - NOW.hour) % 24
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

print("=== 1. KONTENT VA MUROJAAT ===")

r = client.post("/api/content", headers=HS, json={
    "title": "Abdulaziz IELTS 7.0", "platform": "ig_reels",
    "pillar": "results", "goal": "lead", "branch_id": BID,
    "planned_date": (TODAY - timedelta(days=5)).isoformat()})
C1 = r.json()["id"]
client.post(f"/api/content/{C1}/status", headers=HS,
            json={"status": "ready"})
client.post(f"/api/content/{C1}/publish", headers=HS,
            json={"post_url": "https://instagram.com/p/x1"})
client.put(f"/api/content/{C1}/metrics", headers=HS, json={
    "reach": 200000, "views": 180000, "likes": 4000, "comments": 300,
    "saves": 900, "shares": 400, "profile_visits": 3000,
    "link_clicks": 1200, "dms": 430})

d = client.get("/api/inbox", headers=HS).json()
ck("10 ta shablon", len(d["templates"]), 10)
ck("7 ta kanal", len(d["channels"]), 7)
ck("8 ta holat", len(d["statuses"]), 8)
ck("SLA chegarasi", d["sla_alert"], 30)
ck("ish vaqti", d["work_hours"], "09:00–20:00")

print("\n=== 2. MUROJAAT KELDI ===")

r = client.post("/api/inbox", headers=HS, json={
    "channel": "instagram", "kind": "dm",
    "external_id": "ig-1", "author": "Dilnoza",
    "username": "@dilnoza", "text": "IELTS guruhi bormi? Narxi qancha?",
    "content_id": C1, "branch_id": BID, "course": "IELTS",
    "received_at": (NOW - timedelta(minutes=10)).isoformat()})
ck("murojaat qabul qilindi", r.status_code, 200)
M1 = r.json()["id"]
ck("holati yangi", r.json()["status"], "new")
ck("kontentga bog'landi", r.json()["content"], "Abdulaziz IELTS 7.0")
ck("javob kutilmoqda", r.json()["sla_label"], "Javob kutilmoqda")

# Takror kelmaydi
r = client.post("/api/inbox", headers=HS, json={
    "channel": "instagram", "kind": "dm", "external_id": "ig-1",
    "author": "Dilnoza"})
ck("bir xil xabar takrorlanmaydi", r.json()["id"], M1)

print("\n=== 3. JAVOB VA SLA ===")

r = client.post(f"/api/inbox/{M1}/reply", headers=HS, json={
    "text": "Assalomu alaykum! IELTS guruhimiz bor."})
ck("javob berildi", r.json()["status"], "answered")
ck("javob vaqti o'lchandi", r.json()["reply_minutes"] >= 9, True)
ck("SLA yaxshi", r.json()["sla_label"], "Yaxshi")
ck("kim javob berdi", r.json()["replied_by"], "Smm")

# Ikkinchi javob birinchi javob vaqtini o'zgartirmaydi
first = r.json()["first_reply_at"]
r2 = client.post(f"/api/inbox/{M1}/reply", headers=HS,
                 json={"text": "Yana bir gap"})
ck("birinchi javob vaqti o'zgarmadi", r2.json()["first_reply_at"], first)

# Kechikkan javob
r = client.post("/api/inbox", headers=HS, json={
    "channel": "telegram", "kind": "dm", "external_id": "tg-1",
    "author": "Sardor", "text": "Filial qayerda?",
    "received_at": (NOW - timedelta(minutes=75)).isoformat()})
M2 = r.json()["id"]
ck("75 daqiqa kutmoqda", r.json()["waiting_minutes"] >= 74, True)
ck("kechikkan deb belgilandi", r.json()["overdue"], True)

r = client.post(f"/api/inbox/{M2}/reply", headers=HS,
                json={"text": "Zafar shaharchasida"})
ck("kritik SLA", r.json()["sla_label"], "Kritik")

print("\n=== 4. ISH VAQTIDAN TASHQARI ===")

# Mahalliy vaqt bo'yicha 02:00 — aniq ish vaqtidan tashqari
night = NOW - timedelta(hours=12)
r = client.post("/api/inbox", headers=HS, json={
    "channel": "instagram", "kind": "dm", "external_id": "ig-night",
    "author": "Tungi", "text": "Salom",
    "received_at": night.isoformat()})
ck("tunda kelgani belgilandi", r.json()["off_hours"], True)
M3 = r.json()["id"]
client.post(f"/api/inbox/{M3}/reply", headers=HS, json={"text": "Salom"})

d = client.get("/api/inbox", headers=HS).json()
ck("tungi xabar alohida sanaldi", d["off_hours"], 1)
# SLA faqat ish vaqtidagi 2 ta javob bo'yicha: 1 tasi vaqtida
ck("SLA hisobida 2 ta javob", d["answered"], 2)
ck("SLA foizi", d["sla_percent"], 50.0)

print("\n=== 5. MUROJAATDAN LEAD ===")

r = client.post(f"/api/inbox/{M1}/lead", headers=HS, json={
    "phone": "+998901112233", "course": "IELTS", "branch_id": BID})
ck("lead yaratildi", r.status_code, 200)
LID = r.json()["lead_id"]
ck("lead raqami berildi", r.json()["public_id"].startswith("LID-"), True)

d = client.get("/api/inbox", headers=HS).json()
m1 = next(m for m in d["rows"] if m["id"] == M1)
ck("murojaat holati o'zgardi", m1["status"], "lead")
ck("leadga bog'landi", m1["lead_id"], LID)

db = SessionLocal()
lead = db.query(models.Lead).get(LID)
ck("ism ko'chdi", lead.full_name, "Dilnoza")
ck("telefon yozildi", lead.phone, "+998901112233")
ck("kontent ko'chdi", lead.content_id, C1)
ck("manba instagram", lead.source, "instagram")
db.close()

r = client.post(f"/api/inbox/{M1}/lead", headers=HS, json={})
ck("ikki marta leadga aylantirilmaydi", r.status_code, 400)

print("\n=== 6. ATRIBUTSIYA: KONTENTDAN SOTUVGACHA ===")

# Leadni o'quvchiga aylantiramiz va to'lov qo'shamiz
db = SessionLocal()
s = models.Student(full_name="Dilnoza", branch_id=BID, status="active",
                   enrolled_date=TODAY - timedelta(days=45))
db.add(s); db.commit()
lead = db.query(models.Lead).get(LID)
lead.converted_student_id = s.id
lead.stage = "won"
db.commit()
db.add(models.Payment(student_id=s.id, amount=480000, kind="payment",
                      created_at=TODAY - timedelta(days=40)))
db.add(models.Payment(student_id=s.id, amount=480000, kind="payment",
                      created_at=TODAY - timedelta(days=10)))
db.commit(); db.close()

a = client.get(f"/api/content/{C1}/attribution", headers=HS).json()
ck("reach", a["reach"], 200000)
ck("murojaatlar", a["messages"], 1)
ck("leadlar", a["leads"], 1)
ck("sifatli leadlar", a["qualified"], 1)
ck("sotuvlar", a["sales"], 1)
ck("tushum", a["revenue"], 960000)
ck("birinchi to'lov", a["first_revenue"], 480000)
ck("30 kun qoldi", a["retained_30"], 1)
ck("90 kun hali yo'q", a["retained_90"], 0)
ck("voronka 10 bosqich", len(a["funnel"]), 10)
ck("hikoya matni tuzildi", "sotuv" in a["story"], True)
ck("maqsad ko'rsatilgan", a["goal_label"], "Lead yig'ish")

# Sifatli engagement: 4000*1 + 300*2 + 900*3 + 400*4 + 430*5
ck("sifatli engagement", a["engagement"],
   4000 + 600 + 2700 + 1600 + 2150)

print("\n=== 7. UMUMIY ATRIBUTSIYA ===")

d = client.get("/api/smm/attribution", headers=HS).json()
ck("kontent ro'yxatda", len(d["rows"]) >= 1, True)
ck("tushum bo'yicha saralangan", d["rows"][0]["revenue"], 960000)
ck("yo'nalish kesimi bor", len(d["by_pillar"]) >= 1, True)
ck("umumiy tushum", d["total"]["revenue"], 960000)
ck("eng yaxshilari ajratilgan", len(d["best"]) >= 1, True)

print("\n=== 8. KAMPANIYA VORONKASI ===")

db = SessionLocal()
camp = models.Campaign(name="IELTS kampaniyasi", goal="lead",
                       course="IELTS", branch_id=BID,
                       start_date=TODAY - timedelta(days=10),
                       target_leads=10, is_active=1)
db.add(camp); db.commit()
CID = camp.id
db.query(models.Content).get(C1).campaign_id = CID
db.commit(); db.close()

d = client.get("/api/campaigns", headers=HS).json()
c = d["rows"][0]
ck("kampaniya ko'rinadi", c["name"], "IELTS kampaniyasi")
ck("kontentlar soni", c["contents"], 1)
ck("leadlar", c["leads"], 1)
ck("sotuvlar", c["sales"], 1)
ck("reja bajarilishi", c["lead_plan_percent"], 10.0)
ck("voronka bor", len(c["funnel"]), 10)

print("\n=== 9. HOLATLAR VA RUXSAT ===")

r = client.post(f"/api/inbox/{M2}/status", headers=HS,
                json={"status": "complaint"})
ck("shikoyat deb belgilandi", r.json()["status"], "complaint")
ck("rangi qizil", r.json()["status_tone"], "red")

ck("ustoz inboxni ko'rmaydi",
   client.get("/api/inbox", headers=HT).status_code, 403)
ck("ustoz atributsiyani ko'rmaydi",
   client.get("/api/smm/attribution", headers=HT).status_code, 403)

r = client.post("/api/inbox", headers=HS, json={
    "channel": "instagram", "kind": "comment", "author": "",
    "text": "Zo'r!"})
MX = r.json()["id"]
r = client.post(f"/api/inbox/{MX}/lead", headers=HS, json={})
ck("ismsiz lead yaratilmaydi", r.status_code, 400)

print("\n=== 10. SLA HISOBI ===")

ck("15 daqiqa yaxshi", roles.sla_band(15)[1], "Yaxshi")
ck("25 daqiqa qoniqarli", roles.sla_band(25)[1], "Qoniqarli")
ck("45 daqiqa kechikish", roles.sla_band(45)[1], "Kechikish")
ck("90 daqiqa kritik", roles.sla_band(90)[1], "Kritik")

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
