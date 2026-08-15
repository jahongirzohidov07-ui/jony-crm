"""NOMZOD QAYSI ISHGA KELGAN + FILTRLAR (2026-08-15).

Jahongir: "BU ROYXATDA QAYSI VAKANSIYANI TANLAGANI KO'RINIB TURSIN
USTOZ TANLASA QAYSI FANLIGI HAM, keyin filtr ham qoyib bersan shu
yerga nomzodlar kopayganda topish osonlashadi".
"""
import os, sys
os.environ["DATABASE_URL"] = "sqlite:////tmp/candpos.db"
if os.path.exists("/tmp/candpos.db"):
    os.remove("/tmp/candpos.db")
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
b1 = models.Branch(name="Bekobod 1"); b2 = models.Branch(name="Yangiyer")
db.add_all([b1, b2]); db.commit()
B1, B2 = b1.id, b2.id
v = models.Vacancy(title="Support teacher", branch_id=B1, status="open")
db.add(v); db.commit(); VID = v.id
# ESKI uslubdagi nomzod: lavozim faqat IZOH matnida
old = models.Candidate(
    full_name="Eski Nomzod", phone="+998901112233", branch_id=B1,
    stage="applied", source="other",
    note=("LAVOZIM: Ustoz\n"
          "Yashash manzili: Bekobod\n"
          "Qaysi fandan dars beradi: Ingliz tili\n"
          "Manba: onlayn ariza"))
db.add(old); db.commit(); OLD_ID = old.id
db.add(models.User(username="hr", full_name="HR", role="hr_manager",
                   password_hash=hash_password("x"), is_active=1))
db.add(models.User(username="asos", full_name="Asoschi", role="founder",
                   password_hash=hash_password("x"), is_active=1))
db.commit(); db.close()


def tok(u):
    return {"Authorization": "Bearer " + c.post(
        "/api/auth/login", json={"username": u, "password": "x"})
        .json()["access_token"]}


F = tok("asos")

print("=== 1. Eski nomzodning lavozimi endi KO'RINADI ===")
r = c.get("/api/candidates", headers=F)
ck("200", r.status_code, 200)
row = [x for x in r.json() if x["id"] == OLD_ID][0]
ck("lavozim izohdan olindi", row["role_label"], "Ustoz")
ck("fan ham olindi", row["subject"], "Ingliz tili")

print("\n=== 2. Ochiq arizadan kelgan nomzod ===")
r = c.post("/api/apply", json={
    "full_name": "Yangi Nomzod Aliyeva",
    "phone": "+998901112244",
    "position": "teacher",
    "subject": "Koreys tili",
    "address": "Bekobod", "education": "Oliy",
    "photo": "data:image/png;base64," + "A" * 200,
    "certificate": "data:application/pdf;base64," + "B" * 200,
})
ck("ariza qabul qilindi", r.status_code, 200)
r = c.get("/api/candidates", headers=F)
new = [x for x in r.json() if x["full_name"].startswith("Yangi")][0]
NEW_ID = new["id"]
ck("lavozim alohida maydonda", new["position"], "teacher")
ck("ro'yxatda 'Ustoz' ko'rinadi", new["role_label"], "Ustoz")
ck("fan saqlandi", new["subject"], "Koreys tili")

print("\n=== 3. Vakansiyaga bog'langan nomzod — vakansiya nomi ===")
r = c.post("/api/candidates", headers=F, json={
    "full_name": "Uchinchi Nomzod", "phone": "930591606",
    "vacancy_id": VID, "branch_id": B2, "source": "alumni",
    "position": "support"})
ck("qo'shildi", r.status_code, 200)
r = c.get("/api/candidates", headers=F)
third = [x for x in r.json() if x["full_name"] == "Uchinchi Nomzod"][0]
ck("vakansiya nomi ustun turadi", third["role_label"], "Support teacher")
ck("fan yo'q (ustoz emas)", third["subject"], None)

print("\n=== 4. Ustoz bo'lmasa fan saqlanmaydi ===")
r = c.post("/api/candidates", headers=F, json={
    "full_name": "Farrosh Nomzod", "position": "cleaner",
    "subject": "Ingliz tili", "branch_id": B1})
ck("qo'shildi", r.status_code, 200)
r = c.get("/api/candidates?position=cleaner", headers=F)
ck("faqat farrosh chiqdi", len(r.json()), 1)

print("\n=== 5. FILTRLAR ===")
r = c.get("/api/candidates?position=teacher", headers=F)
ck("lavozim bo'yicha: 1 ta (yangi ariza)", len(r.json()), 1)
r = c.get("/api/candidates?subject=Koreys", headers=F)
ck("fan bo'yicha (qismiy moslik)", len(r.json()), 1)
r = c.get("/api/candidates?source=alumni", headers=F)
ck("manba bo'yicha", len(r.json()), 1)
r = c.get(f"/api/candidates?branch_id={B2}", headers=F)
ck("filial bo'yicha", len(r.json()), 1)
r = c.get("/api/candidates?q=Aliyeva", headers=F)
ck("ism bo'yicha qidiruv", len(r.json()), 1)
r = c.get("/api/candidates?q=930591606", headers=F)
ck("telefon bo'yicha qidiruv", len(r.json()), 1)
r = c.get("/api/candidates?q=1112233", headers=F)
ck("telefon qismi bilan ham", len(r.json()), 1)
r = c.get("/api/candidates?position=teacher&subject=Ingliz", headers=F)
ck("ikki filtr birga (VA mantig'i)", len(r.json()), 0)
r = c.get("/api/candidates?stage=applied", headers=F)
ck("bosqich filtri ishlayapti", len(r.json()) >= 1, True)

print("\n=== 6. Filtr ro'yxatlari ===")
r = c.get("/api/candidates/filters", headers=F)
ck("200", r.status_code, 200)
d = r.json()
ck("lavozimlar ro'yxati", len(d["positions"]), 6)
ck("fanlar bazadan yig'ildi",
   sorted(d["subjects"]), ["Ingliz tili", "Koreys tili"])
ck("manbalar ro'yxati bor", len(d["sources"]) > 3, True)

print("\n=== 7. Eski yozuvlar bir marta to'ldiriladi ===")
from hr_ats import backfill_candidate_positions   # noqa: E402
import common                                     # noqa: E402
db = SessionLocal()
db.query(models.SeedMark).filter(
    models.SeedMark.key == "cand_answers_v1").delete()
db.commit()
common._SEED_KEYS = None
n = backfill_candidate_positions(db)
ck("eski nomzod to'ldirildi", n >= 1, True)
row = db.query(models.Candidate).get(OLD_ID)
ck("lavozim maydoni yozildi", row.position, "teacher")
ck("fan maydoni yozildi", row.subject, "Ingliz tili")
n2 = backfill_candidate_positions(db)
ck("ikkinchi marta ishlamaydi", n2, 0)
db.close()

print("\n=== 8. Endi eski nomzod ham filtrga tushadi ===")
r = c.get("/api/candidates?position=teacher", headers=F)
ck("ikkita ustoz", len(r.json()), 2)
r = c.get("/api/candidates?subject=Ingliz tili", headers=F)
ck("Ingliz tili bo'yicha 1 ta", len(r.json()), 1)

print("\n=== 9. Ro'yxat N+1 qilmaydi ===")
from sqlalchemy import event                       # noqa: E402
from sqlalchemy.engine import Engine               # noqa: E402
cnt = [0]


@event.listens_for(Engine, "before_cursor_execute")
def _c(conn, cur, st, p, ctx, many):
    cnt[0] += 1


cnt[0] = 0
c.get("/api/candidates", headers=F)
ck("15 tadan kam so'rov", cnt[0] < 15, True)

print("\n=== 10. QO'LDA kiritishda ariza savollari saqlanadi ===")
r = c.post("/api/candidates", headers=F, json={
    "full_name": "Qo'lda Nomzod",
    "phone": "+998901119999",
    "position": "teacher",
    "subject": "Rus tili",
    "experience_years": 3.5,
    "address": "Bekobod, Navoiy 12",
    "birth_date": "2000-05-14",
    "education": "TDPU, ingliz tili",
    "marital": "married",
    "socials": "@nomzod",
    "workplaces": "Maktab 5 — 2 yil",
    "work_duration": "2 yildan ko'p (uzoq muddat)",
    "note": "Tanish tavsiya qildi",
    "branch_id": B1,
})
ck("qo'shildi", r.status_code, 200)
MID = r.json()["id"]
r = c.get(f"/api/candidates/{MID}", headers=F)
d = r.json()
ck("manzil saqlandi", d["address"], "Bekobod, Navoiy 12")
ck("tug'ilgan sana", d["birth_date_text"], "2000-05-14")
ck("ma'lumoti", d["education"], "TDPU, ingliz tili")
ck("oilaviy holati", d["marital_label"], "Oilali")
ck("ijtimoiy tarmoq", d["socials"], "@nomzod")
ck("qancha ishlamoqchi", d["work_duration"],
   "2 yildan ko'p (uzoq muddat)")
ck("ish joylari", d["workplaces"], "Maktab 5 — 2 yil")
ck("tajriba", d["experience_years"], 3.5)
ck("fan", d["subject"], "Rus tili")

print("\n=== 11. Izoh ONLAYN ARIZADAGIDEK yig'iladi ===")
note = d["note"] or ""
for need in ("LAVOZIM: Ustoz", "Yashash manzili: Bekobod",
             "Oilaviy holati: Oilali",
             "Qaysi fandan dars beradi: Rus tili"):
    ck(f"izohda '{need[:22]}…'", need in note, True)
ck("kim kiritgani yozilgan", "qo'lda kiritildi" in note, True)
ck("erkin izoh ham saqlandi", "Tanish tavsiya qildi" in note, True)

print("\n=== 12. Onlayn ariza ham AYNI maydonlarni to'ldiradi ===")
r = c.post("/api/apply", json={
    "full_name": "Onlayn Nomzod Test",
    "phone": "+998901118888",
    "position": "sales",
    "address": "Yangiyer",
    "birth_date": "1999-01-02",
    "education": "Maktab 3",
    "marital": "single",
    "socials": "@onlayn",
    "work_duration": "1-2 yil",
    "workplaces": "Do'kon — 1 yil",
    "photo": "data:image/png;base64," + "A" * 200,
})
ck("ariza qabul qilindi", r.status_code, 200)
r = c.get("/api/candidates?q=Onlayn Nomzod", headers=F)
OID = r.json()[0]["id"]
d2 = c.get(f"/api/candidates/{OID}", headers=F).json()
ck("manzil", d2["address"], "Yangiyer")
ck("ma'lumoti", d2["education"], "Maktab 3")
ck("oilaviy holati", d2["marital_label"], "Turmush qurmagan")
ck("ijtimoiy tarmoq", d2["socials"], "@onlayn")
ck("ikkala yo'l bir xil maydonlarni to'ldiradi",
   sorted(k for k in ("address", "education", "marital", "socials",
                      "work_duration") if d2.get(k)),
   ["address", "education", "marital", "socials", "work_duration"])

print("\n=== 13. Eski nomzodning javoblari izohdan ko'chdi ===")
db = SessionLocal()
db.query(models.SeedMark).filter(
    models.SeedMark.key.in_(["cand_position_v1",
                             "cand_answers_v1"])).delete(
    synchronize_session=False)
db.commit()
common._SEED_KEYS = None
backfill_candidate_positions(db)
row = db.query(models.Candidate).get(OLD_ID)
ck("manzil izohdan olindi", row.address, "Bekobod")
db.close()

print("\n" + ("HAMMASI OK" if not fails
              else f"{len(fails)} ta XATO: {fails}"))
sys.exit(1 if fails else 0)
