"""ADMIN MASHQI (2026-09-25).

Jahongir: "test filial yaratganmiz shu filialga kirib mashq degan
bo'lim ochiladi faqat adminlarga start bossa vazifa bersin
vazifalarni bajarib keyingi bosqichga o'taversin".

Tekshiriladi:
  A. Mashq faqat SINOV filialida boshlanadi;
  B. Start bosilsa birinchi vazifa va sekundomer beriladi;
  C. Vazifa BAJARILMASDAN "Bajardim" bosilsa — yopilmaydi;
  D. Haqiqatda bajarilsa (yangi yozuv yoki auditdagi amal) —
     yopiladi va keyingi vazifa beriladi;
  E. Vaqtdan oshsa ham o'tiladi, lekin "vaqtida emas" deb belgilanadi;
  F. Ustoz va support mashqqa kira olmaydi; HR topshirmaydi, lekin
     soniyalarni o'zgartira oladi;
  G. HR soniyani o'zgartirsa, keyingi urinishda o'sha vaqt amal qiladi.
"""
import os
import sys
import tempfile
import time

_DB = os.path.join(tempfile.gettempdir(), "drill_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry  # noqa: F401,E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

client = TestClient(main.app)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def tok(u):
    return {"Authorization": "Bearer " + client.post(
        "/api/auth/login",
        json={"username": u, "password": "Parol123!"}
    ).json()["access_token"]}


TODAY = roles.local_today()

db = SessionLocal()
real = models.Branch(name="Zafar")
test = models.Branch(name="Sinov filiali")
db.add_all([real, test])
db.commit()
BID, TBID = real.id, test.id
for un, nm, role, bid in [("asos", "Asoschi", roles.FOUNDER, BID),
                          ("hr", "HR Nodira", roles.HR_MANAGER, BID),
                          ("admin", "Admin Aziza", roles.ADMINISTRATOR, TBID),
                          ("admin2", "Admin Bek", roles.ADMINISTRATOR, BID),
                          ("ust", "Ustoz Anvar", roles.TEACHER, BID)]:
    db.add(models.User(username=un, full_name=nm,
                       password_hash=hash_password("Parol123!"),
                       role=role, branch_id=bid, is_active=1))
db.commit()
db.close()

H = tok("asos")
HH = tok("hr")
HA = tok("admin")
HA2 = tok("admin2")
HT = tok("ust")

print("\n=== A. FAQAT SINOV FILIALIDA ===")
r = client.put("/api/drill/branches/%d" % TBID, headers=HH,
               json={"is_test": True})
ck("HR filialni sinov deb belgiladi", r.status_code, 200)
ck("haqiqiy filialdagi admin boshlay olmaydi",
   client.post("/api/drill/start", headers=HA2).status_code, 400)
_msg = client.post("/api/drill/start", headers=HA2).json()["detail"]
ck("sababi aytilgan", "sinov filialida" in _msg, True)
ck("qaysi filial sinov ekani aytilgan", "Sinov filiali" in _msg, True)
ck("hozir qayerdaligi aytilgan", "Zafar" in _msg, True)

print("\n=== A2. FILIALI BOSHQA BO'LGAN ASOSCHI ===")
# Asoschi butun tashkilot bo'yicha ishlaydi. "Boshlash" POST bo'lgani
# uchun tepadagi filial tanlagichi unga qo'shilmaydi — yagona sinov
# filiali bo'lsa, server o'zi tanlashi kerak.
r = client.post("/api/drill/start", headers=H)
ck("asoschi boshlay oldi", r.status_code, 200)
ck("sinov filialida", r.json()["branch"], "Sinov filiali")
ck("filial id qaytdi", r.json()["branch_id"], TBID)
client.post("/api/drill/stop", headers=H)

print("\n=== F. KIM KIRA OLADI ===")
ck("ustoz kira olmaydi",
   client.get("/api/drill/state", headers=HT).status_code, 403)
_m = client.get("/api/drill/state", headers=HT).json()["detail"]
ck("xato matni lavozimni aytadi", "O'qituvchi" in _m, True)
ck("kimga ruxsat borligini aytadi", "Administrator" in _m, True)
# 2026-09-25: ofis lavozimlari (HR ham) topshira oladi — ilgari
# ro'yxat faqat administrator edi va amalda hech kim kira olmadi
ck("HR ham topshira oladi",
   client.get("/api/drill/state", headers=HH).status_code, 200)
ck("HR sozlamani ko'radi",
   client.get("/api/drill/admin", headers=HH).status_code, 200)
ck("admin sozlamani ko'ra olmaydi",
   client.get("/api/drill/admin", headers=HA).status_code, 403)

print("\n=== B. START: BIRINCHI VAZIFA ===")
r = client.post("/api/drill/start", headers=HA)
ck("boshlandi", r.status_code, 200)
d = r.json()
ck("vazifa berildi", bool(d["current"]), True)
ck("birinchi band", d["current"]["order_no"], 1)
ck("sekundomer bor", d["left"] is not None, True)
ck("ro'yxatda 27 ta band", len(d["tasks"]), 27)
# Sekundomerdagi sanoq JAMI vazifa soni bo'yicha bo'lishi kerak
ck("sanoq 27 dan ketadi", d["attempt"]["total"], 27)
ck("ochilgan bandlar alohida", d["attempt"]["opened"], 1)

# Birinchi bandlar "view" — o'zi tasdiqlaydi
while d.get("current") and d["current"]["verify_kind"] == "view":
    d = client.post("/api/drill/done", headers=HA, json={}).json()
ck("ko'rish bandlari yopildi", d["current"]["verify_kind"] in ("row", "audit"),
   True)
cur = d["current"]
print(f"     (endi: {cur['title']} — {cur['verify_kind']})")

print("\n=== C. BAJARMASDAN YOPIB BO'LMAYDI ===")
r = client.post("/api/drill/done", headers=HA, json={}).json()
ck("yopilmadi", r["ok"], False)
ck("tushuntirish berildi", "bajarilgani ko'rinmadi" in r["message"], True)
ck("o'sha vazifa turibdi", r["current"]["title"], cur["title"])

print("\n=== D. HAQIQATDA BAJARILSA ===")
# Lid qo'shish bandi: sinov filialida haqiqiy lid yaratamiz
r = client.post("/api/leads", headers=HA, json={
    "full_name": "Sinov Lid Birinchi", "phone": "901112233",
    "source": "instagram", "branch_id": TBID,
    "address": "Chilonzor", "school": "12-maktab", "grade": "7"})
ck("lid qo'shildi", r.status_code, 200)
r = client.post("/api/drill/done", headers=HA, json={}).json()
ck("endi yopildi", r["ok"], True)
ck("keyingi vazifaga o'tdi", r["current"]["order_no"], cur["order_no"] + 1)
done = [x for x in r["attempt"]["steps"] if x["ok"]]
ck("bajarilganlar sanaldi", len(done), cur["order_no"])
ck("sarflangan vaqt yozildi", done[-1]["spent"] is not None, True)

print("\n=== E. VAQTDAN OSHSA ===")
dd = SessionLocal()
t1 = (dd.query(models.DrillTask)
      .filter(models.DrillTask.key == "student_add").first())
T1_ID, T1_TITLE = t1.id, t1.title
t1.seconds = 5
dd.commit()
dd.close()
guard = 0
while r.get("current") and r["current"]["title"] != T1_TITLE and guard < 40:
    r = client.post("/api/drill/done", headers=HA, json={"skip": True}).json()
    guard += 1
ck("kerakli bandga yetdik", r["current"]["title"], T1_TITLE)
time.sleep(6)
lead_id = client.get("/api/leads", headers=HA).json()[0]["id"]
r2 = client.post(f"/api/leads/{lead_id}/convert", headers=HA, json={})
ck("lid o'quvchiga aylandi", r2.status_code, 200)
r = client.post("/api/drill/done", headers=HA, json={}).json()
ck("bajarildi deb yopildi", r["ok"], True)
step = [x for x in r["attempt"]["steps"] if x["title"] == T1_TITLE][0]
ck("bajarildi", step["ok"], True)
ck("lekin vaqtida emas", step["in_time"], False)

print("\n=== G. HR SONIYANI O'ZGARTIRADI ===")
r = client.put(f"/api/drill/tasks/{T1_ID}", headers=HH,
               json={"seconds": 90})
ck("o'zgartirildi", r.json()["seconds"], 90)
ck("juda kichik son rad etiladi",
   client.put(f"/api/drill/tasks/{T1_ID}", headers=HH,
              json={"seconds": 2}).status_code, 400)
ck("admin o'zgartira olmaydi",
   client.put(f"/api/drill/tasks/{T1_ID}", headers=HA,
              json={"seconds": 300}).status_code, 403)
adm = client.get("/api/drill/admin", headers=HH).json()
ck("HR urinishlarni ko'radi", len(adm["attempts"]) >= 1, True)
ck("kim topshirgani ko'rinadi", adm["attempts"][0]["user"], "Admin Aziza")

print("\n=== H. O'TISH FOIZI (60%) ===")
st = client.get("/api/drill/state", headers=HA).json()
ck("standart o'tish foizi", st["pass_percent"], 60)

# Toza urinish: hamma vazifa "o'tkazib yuborildi" — natija 0%
client.post("/api/drill/stop", headers=HA)
client.post("/api/drill/start", headers=HA)
guard = 0
while guard < 40:
    r = client.post("/api/drill/done", headers=HA, json={"skip": True}).json()
    guard += 1
    if not r.get("current"):
        break
last = client.get("/api/drill/state", headers=HA).json()["history"][0]
ck("hammasi o'tkazib yuborilsa 0%", last["percent"], 0)
ck("o'tmadi", last["passed"], False)
ck("xulosa yozilgan", "hali tayyor emas" in (last["verdict"] or ""), True)
ck("qancha kerakligi aytilgan", "60%" in (last["verdict"] or ""), True)

print("\n=== I. HR FOIZNI O'ZGARTIRADI ===")
r = client.put("/api/drill/settings", headers=HH, json={"pass_percent": 40})
ck("o'zgartirildi", r.json()["pass_percent"], 40)
ck("chegaradan tashqari rad etiladi",
   client.put("/api/drill/settings", headers=HH,
              json={"pass_percent": 5}).status_code, 400)
ck("admin o'zgartira olmaydi",
   client.put("/api/drill/settings", headers=HA,
              json={"pass_percent": 90}).status_code, 403)
adm = client.get("/api/drill/admin", headers=HH).json()
ck("HR panelida ko'rinadi", adm["pass_percent"], 40)
ck("urinishda natija foizi bor", "percent" in adm["attempts"][0], True)

print()
if fails:
    print("XATOLAR:", ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
