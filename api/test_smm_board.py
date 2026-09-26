# -*- coding: utf-8 -*-
"""SMM: holat doskasi, avgust test rejasini yopish, favqulodda o'zgarish
(2026-09-26).

Jahongir:
  "xuddi LID bolimidagiga oxshab har bir kontentni holatni o'tkizadigan
   qilib qoyish kerak qaysi holatga kelganini qo'lda surib o'tkizib
   qoya oladigan bo'lsa yaxshi bo'ladi"
  "avgust oyidagi kontent plandagi kechikkanlarni olib tashla uni men
   shunchaki tekshirish uchun qilganman"
  "SMM manager ozi ham kontent planga ozgarishlar favqulotta
   ozgarishlar qosha olsin"

QOIDA: hech narsa o'chirilmaydi — faqat holat o'zgaradi, tarix qoladi.
"""
import os
import sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_smm_board/db.sqlite"
os.makedirs("/tmp/verify_smm_board", exist_ok=True)
if os.path.exists("/tmp/verify_smm_board/db.sqlite"):
    os.remove("/tmp/verify_smm_board/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date, timedelta                # noqa: E402
from fastapi.testclient import TestClient           # noqa: E402
import main, models, roles                          # noqa: E402
import entry                                        # noqa: F401,E402
import common                                       # noqa: E402
import content as content_mod                       # noqa: E402
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
for un, role in (("marhabo", roles.SMM_MANAGER), ("ustoz", roles.TEACHER)):
    db.add(models.User(username=un, password_hash=hash_password("jonyjony"),
                       role=role, full_name=un.title(), branch_id=br.id,
                       is_active=1))
db.commit()


def tok(un):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": un, "password": "jonyjony"}
    ).json()["access_token"]}


H = tok("marhabo")
HT = tok("ustoz")


def mk(title, d, status, **kw):
    x = models.Content(title=title, planned_date=d, status=status,
                       platform="instagram", branch_id=br.id, **kw)
    db.add(x)
    db.commit()
    return x.id


A1 = mk("Avg test 1", date(2026, 8, 5), "idea")
A2 = mk("Avg test 2", date(2026, 8, 20), "editing")
A3 = mk("Avg chiqqan", date(2026, 8, 12), "published",
        post_url="https://www.instagram.com/reel/ABC123/")
A4 = mk("Avg bekor", date(2026, 8, 25), "cancelled")
S1 = mk("Sentabr post", date(2026, 9, 10), "idea")
FUT = mk("Kelajak post", date.today() + timedelta(days=3), "idea")
CONS = mk("Rozilik kerak", date.today() + timedelta(days=2), "review",
          needs_consent=1, consent_ok=0)
total_before = db.query(models.Content).count()

print("=== 1. AVGUST TEST REJASI: OLDIN (qizil holat) ===")
rows = c.get("/api/content?date_from=2026-08-01&date_to=2026-08-31",
             headers=H).json()["rows"]
late_before = [r["id"] for r in rows
               if any(w["key"] == "late" for w in r["warnings"])]
ck("avgustda 2 ta kechikkan bor edi", sorted(late_before), sorted([A1, A2]))

print("\n=== 2. AVGUST TEST REJASI: YOPISH ===")
# Ilova ishga tushganda bo'sh bazada belgi qo'yilgan — test uchun olamiz
db.query(models.SeedMark).filter(
    models.SeedMark.key == content_mod._AUG_TEST_KEY).delete()
db.commit()
common._SEED_KEYS = None
n = content_mod.cancel_aug_test_content(db)
ck("2 ta post bekor qilindi", n, 2)
db.expire_all()
st = {x.id: x.status for x in db.query(models.Content).all()}
ck("ochiq avgust postlari -> cancelled", (st[A1], st[A2]),
   ("cancelled", "cancelled"))
ck("chiqqan avgust postiga TEGILMADI", st[A3], "published")
ck("sentabr postiga TEGILMADI", st[S1], "idea")
ck("HECH NARSA O'CHIRILMADI", db.query(models.Content).count(), total_before)
vers = (db.query(models.ContentVersion)
        .filter(models.ContentVersion.field == "status",
                models.ContentVersion.content_id.in_([A1, A2])).all())
ck("eski holat tarixda saqlandi",
   sorted(v.old_value for v in vers), ["editing", "idea"])
ck("ikkinchi marta ishlamaydi", content_mod.cancel_aug_test_content(db), 0)
rows = c.get("/api/content?date_from=2026-08-01&date_to=2026-08-31",
             headers=H).json()["rows"]
ck("avgustda kechikkan ogohlantirish qolmadi",
   [r["id"] for r in rows if any(w["key"] == "late" for w in r["warnings"])],
   [])

print("\n=== 3. HOLAT DOSKASI: SURIB O'TKAZISH ===")
r = c.post(f"/api/content/{FUT}/status", json={"status": "shooting"},
           headers=H)
ck("g'oya -> syomka", (r.status_code, r.json().get("status")),
   (200, "shooting"))
r = c.post(f"/api/content/{FUT}/status", json={"status": "idea"}, headers=H)
ck("orqaga ham suriladi", r.json().get("status"), "idea")
r = c.post(f"/api/content/{CONS}/status", json={"status": "ready"},
           headers=H)
ck("roziliksiz 'tayyor'ga o'tmaydi", r.status_code, 400)
r = c.post(f"/api/content/{A1}/status", json={"status": "idea"}, headers=H)
ck("bekor qilingan postni qaytarish mumkin", r.json().get("status"), "idea")
r = c.post(f"/api/content/{FUT}/status", json={"status": "yoq"}, headers=H)
ck("noma'lum holat rad etiladi", r.status_code, 400)
r = c.post(f"/api/content/{FUT}/status", json={"status": "editing"},
           headers=HT)
ck("ustoz sura olmaydi", r.status_code, 403)
meta = c.get("/api/content-meta", headers=H).json()
ck("doska ustunlari = holatlar ro'yxati",
   [s["key"] for s in meta["statuses"]],
   [k for k, _, _ in roles.CONTENT_STATUSES])

print("\n=== 4. FAVQULODDA O'ZGARISH ===")
r = c.post("/api/smm/urgent", json={"action": "add", "title": "Tezkor"},
           headers=H)
ck("sababsiz qabul qilinmaydi", r.status_code, 400)
r = c.post("/api/smm/urgent", json={"action": "add", "title": "Tezkor post",
                                    "reason": "Olimpiada g'olibi e'loni"},
           headers=H)
j = r.json()
ck("yangi post qo'shildi", r.status_code, 200)
ck("  bugungi sana", j.get("planned_date"), roles.local_today().isoformat())
ck("  shoshilinch belgisi", j.get("priority"), "urgent")
NEW = j["id"]
r = c.post("/api/smm/urgent", json={"action": "move", "content_id": S1,
                                    "planned_date": "2026-09-30",
                                    "reason": "Syomka qoldirildi"},
           headers=H)
ck("ko'chirildi", r.json().get("planned_date"), "2026-09-30")
mv = (db.query(models.ContentMove)
      .filter(models.ContentMove.content_id == S1).all())
ck("  ko'chish tarixi yozildi (eski sana saqlandi)",
   [(str(m.from_date), str(m.to_date)) for m in mv],
   [("2026-09-10", "2026-09-30")])
r = c.post("/api/smm/urgent", json={"action": "cancel", "content_id": NEW,
                                    "reason": "Rahbar to'xtatdi"},
           headers=H)
ck("bekor qilindi", r.json().get("status"), "cancelled")
db.expire_all()
ck("  bazada qoldi (o'chirilmadi)",
   db.query(models.Content).get(NEW) is not None, True)
ck("  tarix: 3 ta favqulodda yozuv",
   db.query(models.ContentVersion)
   .filter(models.ContentVersion.field == "urgent").count(), 3)
ck("  auditda bor",
   db.query(models.AuditLog)
   .filter(models.AuditLog.entity == "content",
           models.AuditLog.action == "urgent").count(), 3)
r = c.post("/api/smm/urgent", json={"action": "add", "title": "x",
                                    "reason": "sabab bor"}, headers=HT)
ck("ustozga ruxsat yo'q", r.status_code, 403)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
