"""USTOZ KARTASI BO'SHATILGANDA HAM SUPPORT GURUHDAN CHIQSIN (2026-09-03).

Jahongir: "NUR guruhida DAN DOSTONNI OLIB TASHLAY OLMAYABMAN. AKKAUNTI
YOQ FAOLDA HAM FAOLMASDA HAM. Akkaunt udalit qilinsa, yoki faol
bo'lmasa guruhdan avtomat chiqsin".

HAQIQIY HOLAT (jonli bazadan): Sulaymonov Dostonbek — akkaunti (users)
FAOL support_teacher, lekin ustoz KARTASI (teachers) 02.09.2026 da
yopilgan. Tanlov ro'yxati kartadan olinadi — u ko'rinmasdi; eski
tozalash esa faqat akkauntga qarab uni "sog'lom" deb o'tkazib
yuborardi. Natijada Nur guruhida osilib qolgan va olib tashlab
bo'lmagan.

Test uch yo'lni tekshiradi:
  1. Karta bo'shatilsa (PUT is_active=0) — biriktirish darrov bo'shaydi;
  2. Karta o'chirilsa (DELETE) — ham bo'shaydi;
  3. Allaqachon shunday qolib ketgan (Dostonbek holati) — tozalash topadi.
Va: FAOL supportga tegilmaydi, kartasi yo'q eski yozuvga tegilmaydi.
"""
import os, sys
from datetime import date, timedelta

os.environ["DATABASE_URL"] = "sqlite:////tmp/supcard_test.db"
if os.path.exists("/tmp/supcard_test.db"):
    os.remove("/tmp/supcard_test.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
from common import _cleanup_stale_support_assignments

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


def supports_of(gid):
    db = SessionLocal()
    r = sorted(a.user_id for a in db.query(models.SupportAssignment)
               .filter(models.SupportAssignment.group_id == gid).all())
    db.close()
    return r


TODAY = date.today()
db = SessionLocal()
b = models.Branch(name="Bekobod 1")
db.add(b)
db.commit()
BID = b.id
db.add(models.User(username="asos", password_hash=hash_password("x"),
                   full_name="Asoschi", role="founder"))
db.add(models.User(username="hs", password_hash=hash_password("x"),
                   full_name="Support Boshlig'i", role="head_support",
                   branch_id=BID))
db.commit()


def mk_support(uname, name, card_active=1, with_card=True):
    u = models.User(username=uname, password_hash=hash_password("x"),
                    full_name=name, role="support_teacher",
                    branch_id=BID, is_active=1)
    db.add(u)
    db.commit()
    tid = None
    if with_card:
        t = models.Teacher(full_name=name, branch_id=BID, user_id=u.id,
                           is_active=card_active,
                           left_date=None if card_active else TODAY,
                           hired_date=TODAY - timedelta(days=30))
        db.add(t)
        db.commit()
        tid = t.id
    return u.id, tid


DOST_U, DOST_T = mk_support("doston", "Sulaymonov Dostonbek")
SHAX_U, SHAX_T = mk_support("shaxnoza", "Abduhakimova Shaxnoza")
DEL_U, DEL_T = mk_support("ochiriladigan", "Kartasi O'chiriladigan")
# Dostonbek holati: akkaunt faol, karta ALLAQACHON yopiq
OLD_U, OLD_T = mk_support("eski", "Eski Qolib Ketgan", card_active=0)
# Kartasi umuman yo'q eski yozuv — tegilmasligi kerak
NOCARD_U, _ = mk_support("kartasiz", "Kartasiz Support", with_card=False)

ut = models.User(username="ustoz", password_hash=hash_password("x"),
                 full_name="Sardor Mirfozilov", role="teacher",
                 branch_id=BID)
db.add(ut)
db.commit()
t = models.Teacher(full_name="Sardor Mirfozilov", branch_id=BID,
                   user_id=ut.id, is_active=1, grade="middle",
                   hired_date=TODAY - timedelta(days=300))
db.add(t)
db.commit()
g = models.Group(name="Nur", teacher_id=t.id, branch_id=BID,
                 subject="english", lesson_days="mon,wed,fri",
                 lesson_time="16:00", start_date=TODAY - timedelta(days=60),
                 lesson_price=40000, monthly_fee=480000,
                 standard_lessons_per_month=12)
db.add(g)
db.commit()
GID = g.id
for uid in (DOST_U, SHAX_U, DEL_U, OLD_U, NOCARD_U):
    db.add(models.SupportAssignment(user_id=uid, group_id=GID,
                                    days="mon,wed,fri", start="15:00",
                                    end="16:00", created_by="Test"))
db.commit()
db.close()

H = tok("asos")

print("=== 1. BOSHIDA 5 TA SUPPORT BIRIKTIRILGAN ===")
ck("5 ta biriktirish", len(supports_of(GID)), 5)

print("\n=== 2. KARTA BO'SHATILDI (PUT is_active=0) — DOSTONBEK ===")
r = client.put(f"/api/teachers/{DOST_T}", headers=H, json={
    "full_name": "Sulaymonov Dostonbek", "is_active": 0})
ck("karta yopildi", r.status_code, 200)
ck("DOSTONBEK GURUHDAN CHIQDI", DOST_U in supports_of(GID), False)
ck("Shaxnoza joyida", SHAX_U in supports_of(GID), True)
db = SessionLocal()
ck("akkaunti hamon faol (ataylab — tegilmadi)",
   db.query(models.User).get(DOST_U).is_active, True)
ck("support boshlig'iga vazifa tushdi",
   db.query(models.Task).filter(
       models.Task.title.like("Supportsiz qolgan guruhlar: Sulaymonov%")
   ).count(), 1)
db.close()

print("\n=== 3. KARTA O'CHIRILDI (DELETE) ===")
r = client.delete(f"/api/teachers/{DEL_T}", headers=H)
ck("karta o'chirildi", r.status_code, 200)
ck("BIRIKTIRISH HAM BO'SHADI", DEL_U in supports_of(GID), False)

print("\n=== 4. ALLAQACHON QOLIB KETGAN (Dostonbek holati) — TOZALASH ===")
ck("tozalashdan oldin eski yozuv turibdi", OLD_U in supports_of(GID), True)
db = SessionLocal()
n = _cleanup_stale_support_assignments(db)
db.close()
ck("tozalash topdi", n >= 1, True)
ck("ESKI YOPIQ KARTALI SUPPORT GURUHDAN CHIQDI",
   OLD_U in supports_of(GID), False)

print("\n=== 5. TEGILMASLIGI KERAK BO'LGANLAR ===")
ck("FAOL support (Shaxnoza) joyida", SHAX_U in supports_of(GID), True)
ck("kartasi yo'q eski yozuvga TEGILMADI",
   NOCARD_U in supports_of(GID), True)

print("\n=== 6. TOZALASH IDEMPOTENT ===")
db = SessionLocal()
ck("ikkinchi marta 0", _cleanup_stale_support_assignments(db), 0)
db.close()

print("\n=== 7. GURUH RO'YXATIDA ENDI KO'RINMAYDI ===")
sup = client.get(f"/api/groups/{GID}/supports", headers=H).json()
ids = [a["user_id"] for a in sup["assigned"]]
ck("Dostonbek yo'q", DOST_U in ids, False)
ck("Shaxnoza bor", SHAX_U in ids, True)
gl = client.get("/api/groups", headers=H).json()
nur = [x for x in gl if x["id"] == GID][0]
ck("guruh yozuvida Dostonbek nomi yo'q",
   "Dostonbek" in (nur.get("support_label") or ""), False)
ck("Shaxnoza nomi bor",
   "Shaxnoza" in (nur.get("support_label") or ""), True)

print("\n=== 8. ODDIY TAHRIR (ism) BIRIKTIRISHGA TEGMAYDI ===")
r = client.put(f"/api/teachers/{SHAX_T}", headers=H, json={
    "full_name": "Abduhakimova Shaxnoza Abduaziz qizi", "is_active": 1})
ck("tahrir 200", r.status_code, 200)
ck("Shaxnoza hamon guruhda", SHAX_U in supports_of(GID), True)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
