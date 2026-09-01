"""USTOZ O'Z GURUHINI TAHRIRLAYDI (2026-09-01).

Jahongir: "ustozlar o'zlarini guruhlarini edit qilishda guruh nomini
o'zgartirish darajasini va vaqtini o'zgartirish xonasini ozgartirish
huquqi bolsin".

Bu test IKKI TOMONNI ham isbotlaydi:
  1. RUXSAT — ustoz o'z guruhining nomi, darajasi, dars vaqti va
     xonasini o'zgartira oladi;
  2. CHEGARA — narx, ustoz stavkasi, ustozning o'zi, filial va dars
     kunlari O'ZGARMAYDI, begona guruhga umuman tegib bo'lmaydi,
     xona to'qnashuvi esa force bilan ham o'tmaydi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/tge_test.db"
if os.path.exists("/tmp/tge_test.db"):
    os.remove("/tmp/tge_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401 — jonli saytda entry.py ham yuklanadi
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
db = SessionLocal()
b = models.Branch(name="Zafar")
b2 = models.Branch(name="Bekobod 1")
db.add_all([b, b2])
db.commit()
BID, BID2 = b.id, b2.id

db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.commit()

R = {}
for nm, br, cap in [("101-xona", BID, 20), ("102-xona", BID, 20),
                    ("Begona xona", BID2, 20)]:
    r = models.Room(name=nm, branch_id=br, capacity=cap)
    db.add(r)
    db.commit()
    R[nm] = r.id

T = {}
for name in ["Mening Ustoz", "Boshqa Ustoz"]:
    t = models.Teacher(full_name=name, branch_id=BID, is_active=1,
                       grade="senior",
                       hired_date=TODAY - timedelta(days=800))
    db.add(t)
    db.commit()
    u = models.User(username=roles.login_from_name(name),
                    password_hash=hash_password("x"), full_name=name,
                    role="teacher", branch_id=BID)
    db.add(u)
    db.commit()
    t.user_id = u.id
    db.commit()
    T[name] = t.id
    T[name + "_login"] = u.username

# Support ustoz — u ham SELF_STATS rolida, lekin guruh EGASI emas
su = models.User(username="support1", password_hash=hash_password("x"),
                 full_name="Support Ustoz", role="support_teacher",
                 branch_id=BID)
db.add(su)
db.commit()
st = models.Teacher(full_name="Support Ustoz", branch_id=BID, is_active=1,
                    user_id=su.id, hired_date=TODAY - timedelta(days=100))
db.add(st)
db.commit()

G = {}
for nm, tid, tm in [("Mening guruh", T["Mening Ustoz"], "15:00"),
                    ("Begona guruh", T["Boshqa Ustoz"], "17:00")]:
    g = models.Group(name=nm, teacher_id=tid, branch_id=BID,
                     subject="english", level="step1",
                     lesson_days="mon,wed", lesson_time=tm,
                     room_id=R["101-xona"], room="101-xona",
                     lesson_price=40000, monthly_fee=480000,
                     standard_lessons_per_month=12,
                     teacher_rate_per_student=25000)
    db.add(g)
    db.commit()
    G[nm] = g.id

# Boshqa ustozning guruhi 102-xonada du/chor 09:00 — to'qnashuv uchun
gb = models.Group(name="Band xona guruhi", teacher_id=T["Boshqa Ustoz"],
                  branch_id=BID, subject="english", lesson_days="mon,wed",
                  lesson_time="09:00", room_id=R["102-xona"])
db.add(gb)
db.commit()
db.close()

H = tok("asos")
ME = tok(T["Mening Ustoz_login"])
SUP = tok("support1")
GID = G["Mening guruh"]
FOREIGN = G["Begona guruh"]

print("=== 1. TAHRIR OYNASI UCHUN RO'YXATLAR ===")
r = client.get(f"/api/me/groups/{GID}/edit-options", headers=ME)
ck("edit-options 200", r.status_code, 200)
d = r.json()
ck("hozirgi nom", d["current"]["name"], "Mening guruh")
ck("darajalar ro'yxati bo'sh emas", len(d["levels"]) > 0, True)
ck("dars vaqtlari bor", len(d["lesson_times"]) > 0, True)
room_ids = [x["id"] for x in d["rooms"]]
ck("o'z filialining xonalari bor", R["101-xona"] in room_ids, True)
ck("BOSHQA filial xonasi ro'yxatda YO'Q",
   R["Begona xona"] in room_ids, False)

print("\n=== 2. BEGONA GURUHGA TEGIB BO'LMAYDI ===")
r = client.put(f"/api/me/groups/{FOREIGN}", headers=ME,
               json={"name": "O'g'irlangan nom"})
ck("begona guruh 403", r.status_code, 403)
r = client.get(f"/api/me/groups/{FOREIGN}/edit-options", headers=ME)
ck("begona guruh ro'yxati ham 403", r.status_code, 403)
db = SessionLocal()
ck("begona guruh nomi o'zgarmagan",
   db.query(models.Group).get(FOREIGN).name, "Begona guruh")
db.close()

print("\n=== 3. SUPPORT USTOZ GURUH EGASI EMAS ===")
r = client.put(f"/api/me/groups/{GID}", headers=SUP,
               json={"name": "Support qo'ydi"})
ck("support 403", r.status_code, 403)

print("\n=== 4. TO'RT MAYDON O'ZGARADI ===")
r = client.put(f"/api/me/groups/{GID}", headers=ME, json={
    "name": "Mening guruh — 2-oqim",
    "level": "step3",
    "lesson_time": "18:00",
    "room_id": R["102-xona"],
})
ck("saqlash 200", r.status_code, 200)
j = r.json()
ck("nom o'zgardi", j["name"], "Mening guruh — 2-oqim")
ck("daraja o'zgardi", j["level"], "step3")
ck("vaqt o'zgardi", j["lesson_time"], "18:00")
ck("xona o'zgardi", j["room_id"], R["102-xona"])
ck("xona nomi ham yangilandi", j["room"], "102-xona")

db = SessionLocal()
g = db.query(models.Group).get(GID)
ck("bazada nom", g.name, "Mening guruh — 2-oqim")
ck("bazada daraja", g.level, "step3")
ck("bazada vaqt", g.lesson_time, "18:00")
ck("bazada xona", g.room_id, R["102-xona"])

print("\n=== 5. QOLGAN HAMMA NARSA TEGILMAGAN ===")
ck("narx o'sha-o'sha", g.lesson_price, 40000)
ck("oylik to'lov o'sha-o'sha", g.monthly_fee, 480000)
ck("ustoz stavkasi o'sha-o'sha", g.teacher_rate_per_student, 25000)
ck("ustoz o'zgarmagan", g.teacher_id, T["Mening Ustoz"])
ck("filial o'zgarmagan", g.branch_id, BID)
ck("dars kunlari o'zgarmagan", g.lesson_days, "mon,wed")
ck("standart dars soni o'sha-o'sha", g.standard_lessons_per_month, 12)
db.close()

print("\n=== 6. TAQIQLANGAN MAYDONLAR YUBORILSA — E'TIBORSIZ ===")
r = client.put(f"/api/me/groups/{GID}", headers=ME, json={
    "name": "Nom uchinchi marta",
    "lesson_price": 1,
    "monthly_fee": 1,
    "teacher_rate_per_student": 999999,
    "teacher_id": T["Boshqa Ustoz"],
    "branch_id": BID2,
    "lesson_days": "sat",
    "standard_lessons_per_month": 1,
})
ck("saqlash 200", r.status_code, 200)
db = SessionLocal()
g = db.query(models.Group).get(GID)
ck("nom o'zgardi", g.name, "Nom uchinchi marta")
ck("NARX baribir o'zgarmadi", g.lesson_price, 40000)
ck("OYLIK TO'LOV o'zgarmadi", g.monthly_fee, 480000)
ck("STAVKA o'zgarmadi", g.teacher_rate_per_student, 25000)
ck("USTOZ o'zgarmadi", g.teacher_id, T["Mening Ustoz"])
ck("FILIAL o'zgarmadi", g.branch_id, BID)
ck("KUNLAR o'zgarmadi", g.lesson_days, "mon,wed")
ck("DARS SONI o'zgarmadi", g.standard_lessons_per_month, 12)
db.close()

print("\n=== 7. XONA BANDLIGI — FORCE BILAN HAM O'TMAYDI ===")
r = client.put(f"/api/me/groups/{GID}", headers=ME,
               json={"lesson_time": "09:00", "room_id": R["102-xona"]})
ck("to'qnashuv 400", r.status_code, 400)
r = client.put(f"/api/me/groups/{GID}?force=true", headers=ME,
               json={"lesson_time": "09:00", "room_id": R["102-xona"]})
ck("force bilan ham 400", r.status_code, 400)
db = SessionLocal()
ck("vaqt o'zgarmay qoldi",
   db.query(models.Group).get(GID).lesson_time, "18:00")
db.close()

print("\n=== 8. NOTO'G'RI QIYMATLAR ===")
r = client.put(f"/api/me/groups/{GID}", headers=ME, json={"name": "   "})
ck("bo'sh nom 400", r.status_code, 400)
r = client.put(f"/api/me/groups/{GID}", headers=ME,
               json={"level": "a1"})
ck("ingliz guruhiga rus darajasi (a1) 400", r.status_code, 400)
r = client.put(f"/api/me/groups/{GID}", headers=ME,
               json={"lesson_time": "kechqurun"})
ck("noto'g'ri vaqt 400", r.status_code, 400)
r = client.put(f"/api/me/groups/{GID}", headers=ME,
               json={"room_id": R["Begona xona"]})
ck("boshqa filial xonasi 400", r.status_code, 400)
r = client.put(f"/api/me/groups/{GID}", headers=ME, json={})
ck("bo'sh so'rov 400", r.status_code, 400)

print("\n=== 9. AUDITGA YOZILDI ===")
db = SessionLocal()
rows = db.query(models.AuditLog).filter(
    models.AuditLog.entity == "group",
    models.AuditLog.entity_id == GID).all()
ck("audit yozuvlari bor", len(rows) > 0, True)
flds = {x.field for x in rows}
ck("nom o'zgarishi auditda", "name" in flds, True)
ck("vaqt o'zgarishi auditda", "lesson_time" in flds, True)
ck("xona o'zgarishi auditda", "room_id" in flds, True)
ck("kim qilgani yozilgan", rows[0].user_name, "Mening Ustoz")
db.close()

print("\n=== 10. GURUHLARIM RO'YXATI YANGI QIYMATNI KO'RSATADI ===")
d = client.get("/api/me/groups", headers=ME).json()
row = [x for x in d["rows"] if x["id"] == GID][0]
ck("ro'yxatda yangi nom", row["name"], "Nom uchinchi marta")
ck("ro'yxatda yangi vaqt", row["time"], "18:00")
ck("ro'yxatda yangi xona", row["room"], "102-xona")

print("\n=== 11. RAHBARIYAT YO'LI BUZILMAGAN ===")
r = client.put(f"/api/groups/{GID}", headers=H,
               json={"lesson_price": 50000})
ck("asoschi narxni o'zgartira oladi", r.status_code, 200)
db = SessionLocal()
ck("narx haqiqatda o'zgardi",
   db.query(models.Group).get(GID).lesson_price, 50000)
db.close()

print("\n=== 12. QALAMCHA KIMGA KO'RINADI (my-access.own_group) ===")
# Guruh sahifasidagi qalamcha shu bayroqqa qarab chiqadi.
d = client.get(f"/api/groups/{GID}/my-access", headers=ME).json()
ck("o'z guruhida own_group=True", d.get("own_group"), True)
d = client.get(f"/api/groups/{FOREIGN}/my-access", headers=ME).json()
ck("begona guruhda own_group=False", d.get("own_group"), False)
d = client.get(f"/api/groups/{GID}/my-access", headers=H).json()
ck("asoschida own_group=False (u to'liq forma bilan tahrirlaydi)",
   d.get("own_group"), False)
ck("eski maydonlar joyida", sorted(d.keys()),
   ["can_mark", "group_id", "locked", "own_group", "reason"])

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
