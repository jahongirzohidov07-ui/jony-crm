"""Saytdan kelgan ariza -> JonyOS lidi (2026-08-13).

Jahongir: "Jony Academy.uz saytimizga ariza qoldirsa avtomat JonyOS ga
qaysi filial tanlangan bo'lsa shu filialga lid bolib tushsin va
manbasi website bo'ladigan qil"."""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/web_lead.db"
if os.path.exists("/tmp/web_lead.db"):
    os.remove("/tmp/web_lead.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Zafar")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="adm", full_name="Administrator B1",
                role="administrator", branch_id=B1,
                password_hash=hash_password("x"), is_active=1),
])
db.commit(); db.close()

print("=== 1. Sayt filiallar ro'yxatini oladi (auth siz) ===")
r = c.get("/api/public/branches")
ck("200", r.status_code, 200)
ck("ikkita filial", len(r.json()), 2)

print("\n=== 2. Ariza -> lid (manba website, tanlangan filialga) ===")
r2 = c.post("/api/public/lead", json={
    "full_name": "  Karimov   Doston ", "phone": "+998 90 123 45 67",
    "branch_id": B1, "course": "IELTS", "page": "/kurslar/ielts",
    "utm_source": "instagram_bio"})
ck("qabul qilindi", r2.status_code, 200)
ck("lid yaratildi", bool(r2.json().get("lead_id")), True)
ck("filial qaytdi", r2.json().get("branch"), "Bekobod 1")
db = SessionLocal()
lead = db.query(models.Lead).get(r2.json()["lead_id"])
LEAD_ID = lead.id
ck("manba website", lead.source, "website")
ck("bosqich new", lead.stage, "new")
ck("filial to'g'ri", lead.branch_id, B1)
ck("ism tozalandi", lead.full_name, "Karimov Doston")
ck("LID raqami berildi", (lead.public_id or "").startswith("LID"), True)
ck("izohda yo'nalish bor", "IELTS" in (lead.note or ""), True)
ck("izohda sahifa bor", "/kurslar/ielts" in (lead.note or ""), True)
ck("kim kiritgani: Sayt", lead.created_by, "Sayt")
tasks = [t for t in db.query(models.Task).all()
         if t.title.startswith("Saytdan ariza")]
who = db.query(models.User).get(tasks[0].assignee_id) if tasks else None
db.close()
ck("administratorga vazifa tushdi", bool(tasks), True)
ck("vazifa filial administratoriga", who.username if who else None, "adm")

print("\n=== 3. Ikki marta bosilsa - ikkinchi lid ochilmaydi ===")
r3 = c.post("/api/public/lead", json={
    "full_name": "Karimov Doston", "phone": "998901234567",
    "branch_id": B1})
ck("javob 200", r3.status_code, 200)
ck("takror deb belgilandi", r3.json().get("duplicate"), True)
ck("o'sha lidga ishora qiladi", r3.json().get("lead_id"), LEAD_ID)

print("\n=== 4. Filial tanlanmasa ham ariza yo'qolmaydi ===")
r4 = c.post("/api/public/lead", json={
    "full_name": "Yangi Odam", "phone": "+998 99 000 11 22"})
ck("qabul qilindi", r4.status_code, 200)
db = SessionLocal()
l4 = db.query(models.Lead).get(r4.json()["lead_id"])
ck("filialsiz lid", l4.branch_id, None)
db.close()

print("\n=== 5. Filial NOMI bilan ham yuborsa bo'ladi ===")
r5 = c.post("/api/public/lead", json={
    "full_name": "Zafarlik Bola", "phone": "+998 91 222 33 44",
    "branch": "Zafar"})
db = SessionLocal()
l5 = db.query(models.Lead).get(r5.json()["lead_id"])
ck("Zafar filialiga tushdi", l5.branch_id, B2)
db.close()

print("\n=== 6. Bot (honeypot) - bazaga yozilmaydi ===")
before = None
db = SessionLocal(); before = db.query(models.Lead).count(); db.close()
r6 = c.post("/api/public/lead", json={
    "full_name": "Bot Botov", "phone": "+998 90 000 00 00",
    "hp": "spam"})
db = SessionLocal(); after = db.query(models.Lead).count(); db.close()
ck("javob 200 (bot sezmasin)", r6.status_code, 200)
ck("yangi lid ochilmadi", after, before)

print("\n=== 7. Xato ma'lumot rad etiladi ===")
ck("ismsiz", c.post("/api/public/lead", json={
    "phone": "+998901112233"}).status_code, 400)
ck("telefonsiz", c.post("/api/public/lead", json={
    "full_name": "Ismli Odam"}).status_code, 400)

print("\n=== 8. Lidlar bo'limida ko'rinadi va manbasi 'Sayt' ===")
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login", json={"username": "asos", "password": "x"}
).json()["access_token"]}
rows = c.get("/api/leads", headers=H).json()
web = [x for x in rows if x["source"] == "website"]
ck("ro'yxatda website lidlari bor", len(web) >= 3, True)
ck("manba nomi", roles.LEAD_SOURCE_LABELS["website"],
   "Sayt (jonyacademy.uz)")

print()
if fails:
    print(f"XATOLAR ({len(fails)}): " + ", ".join(fails))
    sys.exit(1)
print("HAMMASI O'TDI")
