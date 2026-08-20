"""Onboarding shablonlari + kutubxona ruxsati (2026-08-20).

Jahongir: "onboarding bilan majburiy kitob videolarni qo'lda
o'zgartiradigan qilib bering, hamma xodimga xar xilda onboarding,
kutubxona bo'liimi ham supportlarda ochilmadi".
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/onblib.db"
if os.path.exists("/tmp/onblib.db"):
    os.remove("/tmp/onblib.db")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.testclient import TestClient          # noqa: E402
import main, models, roles                         # noqa: E402
import entry                                       # noqa: E402
from database import SessionLocal                  # noqa: E402
from auth import hash_password                     # noqa: E402

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="hrm", full_name="HR", role="hr_manager",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="sup", full_name="Support",
                role="support_teacher",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="ust", full_name="Ustoz", role="teacher",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="hsup", full_name="Bosh support",
                role="head_support",
                password_hash=hash_password("x"), is_active=1),
])
db.commit()
SUP_ID = db.query(models.User).filter_by(username="sup").first().id
UST_ID = db.query(models.User).filter_by(username="ust").first().id
db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


F, HRM, SUP, UST, HSUP = tok("asos"), tok("hrm"), tok("sup"), tok("ust"), tok("hsup")

print("=== 1. Standart bosqichlar shablonga ko'chadi ===")
r = c.get("/api/onboarding-steps", headers=HRM)
ck("200", r.status_code, 200)
ck("standart soni", len(r.json()["rows"]), len(roles.ONBOARDING_STEPS))
SID0 = r.json()["rows"][0]["id"]

print("\n=== 2. Yangi bosqich - faqat supportlarga ===")
r = c.post("/api/onboarding-steps", headers=HRM,
           json={"label": "Support qo'llanmasi o'qildi",
                 "target_roles": ["support_teacher"]})
ck("qo'shildi", r.status_code, 200)
NEW_ID = r.json()["id"]
NEW_KEY = r.json()["key"]

print("\n=== 3. Bosqichni ustozlardan olib tashlaymiz ===")
r = c.put(f"/api/onboarding-steps/{SID0}", headers=HRM,
          json={"target_roles": ["teacher"]})
ck("o'zgardi", r.status_code, 200)

print("\n=== 4. Rolga qarab checklist HAR XIL ===")
r = c.get(f"/api/staff/{SUP_ID}/onboarding", headers=HRM)
sup_steps = [x["step"] for x in (r.json().get("rows") or r.json().get("onboarding") or r.json())] if r.status_code == 200 else []
r2 = c.get(f"/api/staff/{UST_ID}/onboarding", headers=HRM)
ust_steps = [x["step"] for x in (r2.json().get("rows") or r2.json().get("onboarding") or r2.json())] if r2.status_code == 200 else []
ck("supportda yangi bosqich bor", NEW_KEY in sup_steps, True)
ck("ustozda yangi bosqich yo'q", NEW_KEY in ust_steps, False)
ck("1-bosqich endi faqat ustozda", "docs" in ust_steps and "docs" not in sup_steps, True)

print("\n=== 5. Yangi bosqichni belgilash (dinamik kalit) ===")
r = c.post(f"/api/staff/{SUP_ID}/onboarding", headers=HRM,
           json={"step": NEW_KEY, "done": True})
ck("qabul qilindi", r.status_code, 200)

print("\n=== 6. O'chirish = faolsizlantirish ===")
r = c.delete(f"/api/onboarding-steps/{NEW_ID}", headers=HRM)
ck("200", r.status_code, 200)
r = c.get(f"/api/staff/{SUP_ID}/onboarding", headers=HRM)
sup2 = [x["step"] for x in (r.json().get("rows") or r.json().get("onboarding") or r.json())]
ck("ro'yxatdan chiqdi", NEW_KEY in sup2, False)
db = SessionLocal()
ck("bajarilgan belgi SAQLANDI",
   db.query(models.OnboardingStep).filter_by(
       user_id=SUP_ID, step=NEW_KEY, done=1).count(), 1)
db.close()

print("\n=== 7. Oddiy xodim boshqara olmaydi ===")
r = c.post("/api/onboarding-steps", headers=SUP, json={"label": "x"})
ck("403", r.status_code, 403)

print("\n=== 8. Kutubxona: support O'QIY oladi, bosh support BOSHQARADI ===")
r = c.get("/api/library", headers=SUP)
ck("support 200", r.status_code, 200)
ck("support boshqarmaydi", r.json()["can_manage"], False)
r = c.get("/api/library", headers=HSUP)
ck("bosh support 200", r.status_code, 200)
ck("bosh support boshqaradi", r.json()["can_manage"], True)
r = c.post("/api/library", headers=HSUP,
           json={"title": "Support darsligi", "kind": "book",
                 "url": "https://kitob.uz/x",
                 "target_roles": ["support_teacher"]})
ck("material qo'shdi", r.status_code, 200)
LIB_ID = r.json()["id"]
r = c.put(f"/api/library/{LIB_ID}", headers=HSUP,
          json={"title": "Support darsligi v2", "required": False})
ck("tahrirladi", r.status_code, 200)
ck("nomi o'zgardi", r.json()["title"], "Support darsligi v2")
ck("majburiylik o'zgardi", r.json()["required"], False)
r = c.get("/api/library", headers=SUP)
ck("supportga ko'rindi", any(
    x["title"] == "Support darsligi v2" for x in r.json()["items"]), True)
r = c.get("/api/library", headers=UST)
ck("ustozga ko'rinmadi", any(
    x["title"].startswith("Support darsligi") for x in r.json()["items"]),
   False)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
