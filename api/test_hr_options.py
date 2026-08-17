"""HR: TIL DARAJASI RO'YXATIGA QO'SHISH + O'QUV RAHBARI (2026-08-16).

Jahongir: "tagidan qo'shadigan qilish kerak til darajasini
nomzodlarda hr bo'limida, ona tili yo boshqa sertifikatlar kiritib
bo'lmayabdi. o'quv bo'lim rahbariga dars baholashni qo'shish kerak
ekan. nomzod o'qituvchi bo'lsa o'quv bo'limi rahbariga ham ko'rinish
kerak. shunda baholay olardi."
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/hropt.db"
if os.path.exists("/tmp/hropt.db"):
    os.remove("/tmp/hropt.db")
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
    print(("OK  " if ok else "MUAMMO ") + n + f": {g}"
          + ("" if ok else f" (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Bekobod 1"); db.add(b); db.commit(); BID = b.id
t = models.Candidate(full_name="Ustoz Nomzod", position="teacher",
                     subject="Ingliz tili", branch_id=BID, stage="applied")
o = models.Candidate(full_name="Farrosh Nomzod", position="cleaner",
                     branch_id=BID, stage="applied")
db.add_all([t, o]); db.commit()
TID, OID = t.id, o.id
db.add_all([
    models.User(username="asos", full_name="Asoschi", role="founder",
                password_hash=hash_password("x"), is_active=1),
    models.User(username="hr", full_name="HR Menejer", role="hr_manager",
                branch_id=BID, password_hash=hash_password("x"),
                is_active=1),
    models.User(username="oquv", full_name="O'quv Rahbari",
                role="academic_head", branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
    models.User(username="sotuv", full_name="Sotuvchi",
                role="sales_manager", branch_id=BID,
                password_hash=hash_password("x"), is_active=1),
])
db.commit(); db.close()


def tok(u_):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u_, "password": "x"})
        .json()["access_token"]}


F, HR, AC, SL = tok("asos"), tok("hr"), tok("oquv"), tok("sotuv")

print("=== 1. Kodda yozilgan ro'yxat joyida ===")
r = c.get(f"/api/candidates/{TID}", headers=HR)
ck("karta ochildi", r.status_code, 200)
levels = r.json()["language_levels"]
ck("boshlang'ich variantlar soni", len(levels), len(roles.LANGUAGE_LEVELS))
ck("B2 bor", any(x["key"] == "b2" for x in levels), True)

print("\n=== 2. Ro'yxatga YANGI variant qo'shiladi ===")
r = c.post("/api/hr/options/language_level", headers=HR,
           json={"label": "TOEFL 90+"})
ck("qo'shildi", r.status_code, 200)
KEY = r.json()["key"]
ck("kalit matndan yasaldi", KEY, "toefl_90")
r = c.post("/api/hr/options/language_level", headers=HR,
           json={"label": "TOEFL 90+"})
ck("dublikat rad etiladi", r.status_code, 400)
r = c.post("/api/hr/options/language_level", headers=HR, json={"label": "  "})
ck("bo'sh nom rad etiladi", r.status_code, 400)
r = c.post("/api/hr/options/language_level", headers=SL,
           json={"label": "Boshqa"})
ck("sotuvchiga ruxsat yo'q", r.status_code, 403)

print("\n=== 3. Yangi variant kartada ko'rinadi va saqlanadi ===")
r = c.get(f"/api/candidates/{TID}", headers=HR)
levels = r.json()["language_levels"]
ck("ro'yxat bittaga o'sdi", len(levels), len(roles.LANGUAGE_LEVELS) + 1)
ck("oxirgisi — qo'shilgani", levels[-1]["label"], "TOEFL 90+")
ck("qo'shilgani belgilangan", levels[-1]["custom"], True)
r = c.put(f"/api/candidates/{TID}", headers=HR,
          json={"language_level": KEY, "native_language": "O'zbek"})
ck("nomzodga yozildi", r.status_code, 200)
r = c.get(f"/api/candidates/{TID}", headers=HR).json()
ck("qiymat saqlandi", r["language_level"], KEY)
ck("nomi to'g'ri chiqdi", r["language_level_label"], "TOEFL 90+")
ck("ona tili saqlandi", r["native_language"], "O'zbek")

print("\n=== 4. Variant yashirilsa ham ESKI yozuv nomi qoladi ===")
db = SessionLocal()
opt = db.query(models.HrOption).filter(models.HrOption.key == KEY).first()
oid = opt.id
db.close()
r = c.delete(f"/api/hr/options/{oid}", headers=HR)
ck("yashirildi", r.status_code, 200)
r = c.get(f"/api/candidates/{TID}", headers=HR).json()
ck("ro'yxatdan chiqdi",
   any(x["key"] == KEY for x in r["language_levels"]), False)
ck("lekin kartada nomi ko'rinadi (yo'qolmadi)",
   r["language_level_label"], KEY)
db = SessionLocal()
ck("baza yozuvi o'chmadi",
   db.query(models.HrOption).filter(models.HrOption.id == oid).count(), 1)
db.close()

print("\n=== 5. O'quv bo'limi rahbari: FAQAT ustoz nomzodlari ===")
r = c.get("/api/candidates", headers=AC)
ck("ro'yxat ochildi", r.status_code, 200)
names = [x["full_name"] for x in r.json()]
ck("ustoz nomzodi bor", "Ustoz Nomzod" in names, True)
ck("farrosh nomzodi ko'rinmaydi", "Farrosh Nomzod" in names, False)
ck("ustoz kartasi ochiladi",
   c.get(f"/api/candidates/{TID}", headers=AC).status_code, 200)
ck("farrosh kartasi yopiq",
   c.get(f"/api/candidates/{OID}", headers=AC).status_code, 403)

print("\n=== 6. O'quv rahbari TAHRIRLAY OLMAYDI, lekin BAHOLAYDI ===")
r = c.put(f"/api/candidates/{TID}", headers=AC, json={"cv": "o'zgartirdim"})
ck("kartani tahrirlash yopiq", r.status_code, 403)
r = c.get(f"/api/observations?candidate_id={TID}", headers=AC)
ck("dars baholash ro'yxati ochiq", r.status_code, 200)
r = c.get("/api/rubrics", headers=AC)
ck("mezonlar ro'yxati ochiq", r.status_code, 200)

print("\n=== 7. Begonaga hammasi yopiq ===")
ck("sotuvchiga nomzodlar yopiq",
   c.get("/api/candidates", headers=SL).status_code, 403)

print("\n=== 8. HR va asoschida hammasi ochiq ===")
ck("HR barcha nomzodni ko'radi",
   len(c.get("/api/candidates", headers=HR).json()), 2)
ck("asoschi ham",
   len(c.get("/api/candidates", headers=F).json()), 2)

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta muammo: {fails}"))
sys.exit(1 if fails else 0)
