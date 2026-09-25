"""LUG'AT UNIT 34–100 + LUG'AT IELTS SHKALASI (2026-09-25).

Jahongir: "JonyStudentAPP da lugat 33ta unit bor shuni ozi bilan lugat
balli 9.0 soz kamku u yerda 9.0 uchun 15000+ soz kerak kamida shuning
uchun ... davomiy unitlarni ham qosh 100tadan soz bolsin va men bergan
34ta unitdan tashqari barcha common sozlarni commonligi boyicha ketma
ket qoyib ketgin ... umumiy 100ta unit bolsin ... shundan kelib chiqib
IELTS ball bersin".

Tekshiriladi:
  1. ma'lumot fayli: 34..100 unit, har birida 100 so'z, dublikat yo'q,
     1–33 unit so'zlari bilan kesishmaydi, tarjima/misol bo'sh emas;
  2. seed: sovuq startda BYUDJET bilan (1200), marker qo'yilmaydi;
     to'liq yuklangach marker; ikkinchi chaqiruv hech narsa qilmaydi;
  3. ma'lumot yo'qotilmaydi: nofaol (eski SAT) so'z yangi unitga
     KO'CHIRILADI, dublikat yaratilmaydi, urinishlari saqlanadi;
  4. shkala: 3200 so'z endi 9.0 EMAS (ilgari edi), 10 000 so'z = 9.0;
     grammatika shkalasi o'zgarmagan;
  5. o'quvchi kartasi va unitlar ro'yxati (100 unit, Unit 100 oxirida,
     unit bo'yicha round ishlaydi).
"""
import os, sys, json, tempfile
from datetime import date

_test_dir = tempfile.TemporaryDirectory(prefix="jony-vx-")
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(
    _test_dir.name, "db.sqlite").replace("\\", "/")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
import vocab_extra_seed as vx
from common import _seed_done, _skills_card
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


HERE = os.path.dirname(os.path.abspath(__file__))

print("=== 1. MA'LUMOT FAYLI ===")
rows = json.load(open(os.path.join(HERE, "vocab_extra_data.json"),
                      encoding="utf-8"))["en"]
base = json.load(open(os.path.join(HERE, "vocab_data.json"),
                      encoding="utf-8"))["en"]
base_words = {w.strip().lower() for w, _, _, _ in base}
units = sorted({u for _, _, u, _ in rows})
ck("unitlar 34..100", units, list(range(34, 101)))
per = {}
for _, _, u, _ in rows:
    per[u] = per.get(u, 0) + 1
ck("har unitda 100 so'z", all(v == 100 for v in per.values()), True)
ck("jami 6700 so'z", len(rows), 6700)
words = [w for w, _, _, _ in rows]
ck("dublikat yo'q", len(set(words)), len(words))
ck("1–33 unit bilan kesishmaydi",
   len(set(words) & base_words), 0)
ck("hammasi kichik lotin harflar",
   all(w.isalpha() and w == w.lower() for w in words), True)
ck("tarjima bo'sh emas", all(t.strip() for _, t, _, _ in rows), True)
ck("misol bo'sh emas", all(e.strip() for _, _, _, e in rows), True)
ck("tarjimada kirill yo'q",
   any(any("Ѐ" <= ch <= "ӿ" for ch in t) for _, t, _, _ in rows),
   False)
# Chastota tartibi: botning 1–33 unitida "the/to/in/you/it" yo'q edi —
# ular 34-unitning boshida bo'lishi kerak (eng ko'p ishlatiladigan).
ck("34-unit eng oddiy so'zlardan boshlanadi ('the' birinchi)",
   words[0], "the")
ck("'you', 'it' ham 34-unitda",
   all(w in words[:100] for w in ("you", "it", "in")), True)

print("\n=== 2. SEED: BYUDJET, DAVOM, MARKER ===")
n_extra = (db.query(models.VocabWord)
           .filter(models.VocabWord.language == "en",
                   models.VocabWord.created_by == "wordfreq").count())
ck("sovuq startda faqat byudjetcha yozildi", n_extra, vx.WORD_BUDGET)
ck("marker HALI qo'yilmagan", _seed_done(db, vx._seed_key()), False)
# 2-start: yana byudjetcha
r2 = vx.seed_vocab_extra(db)
ck("2-startda davom etdi", r2["made"], vx.WORD_BUDGET)
ck("2-startdan keyin ham marker yo'q", _seed_done(db, vx._seed_key()), False)
# qolganini bir yo'la
r3 = vx.seed_vocab_extra(db, budget=None)
ck("qolgani yozildi", r3["finished"], True)
n_extra = (db.query(models.VocabWord)
           .filter(models.VocabWord.language == "en",
                   models.VocabWord.created_by == "wordfreq").count())
ck("jami 6700 so'z bazada", n_extra, 6700)
ck("marker qo'yildi", _seed_done(db, vx._seed_key()), True)
ck("idempotent: qayta chaqirilsa None", vx.seed_vocab_extra(db), None)
n_all_en = (db.query(models.VocabWord)
            .filter(models.VocabWord.language == "en",
                    models.VocabWord.is_active == 1).count())
print(f"     faol inglizcha so'zlar: {n_all_en}")
# (ko/de lug'atida ham "Unit 34" bor — faqat inglizchasini olamiz)
ck("Unit 34 = B2, Unit 50 = C1, Unit 80 = C2",
   [db.query(models.VocabWord).filter(models.VocabWord.topic == t,
                                      models.VocabWord.language == "en")
    .first().level for t in ("Unit 34", "Unit 50", "Unit 80")],
   ["B2", "C1", "C2"])

print("\n=== 3. MA'LUMOT YO'QOTILMAYDI: nofaol so'z ko'chiriladi ===")
# Yangi bazada takrorlaymiz: eski SAT so'zi (is_active=0, urinishi
# bor) + ro'yxatdagi so'z — seed uni o'chirmasdan yangi unitga oladi.
target = [r for r in rows if r[2] == 90][0]
db2 = SessionLocal()
# markerni olib tashlab, seedni qayta ishlatamiz (yangi so'z sifatida
# emas — ko'chirish yo'lini tekshirish uchun bazadagi nusxani nofaol
# qilamiz va unitini eskisiga qaytaramiz)
w90 = (db2.query(models.VocabWord)
       .filter(models.VocabWord.word == target[0]).first())
w90.is_active = 0
w90.topic = "Unit 44 (SAT)"
db2.add(models.VocabAttempt(student_id=1, word_id=w90.id, game="en_uz",
                            correct=1, date=date.today()))
mark = db2.query(models.SeedMark).get(vx._seed_key())
db2.delete(mark)
db2.commit()
import common as _common
_common._SEED_KEYS = None          # keshni tozalash
res = vx.seed_vocab_extra(db2, budget=None)
ck("seed nofaol so'zni TIKLADI (revived=1)", res["revived"], 1)
ck("yangi so'z qo'shilmadi (dublikat yo'q)", res["made"], 0)
db2.expire_all()
same = (db2.query(models.VocabWord)
        .filter(models.VocabWord.word == target[0]).all())
ck("bitta qator qoldi", len(same), 1)
ck("faol va Unit 90 da", (same[0].is_active, same[0].topic),
   (1, "Unit 90"))
ck("urinishi saqlandi",
   db2.query(models.VocabAttempt)
   .filter(models.VocabAttempt.word_id == w90.id).count(), 1)
db2.close()

print("\n=== 4. SHKALA ===")
ck("3200 so'z endi 9.0 EMAS (ilgari 95 ball edi)",
   roles.score_for_skill("vocabulary", 3200) < 95, True)
ck("3200 so'z ~6.0 (B2)",
   roles.ielts_band(roles.score_for_skill("vocabulary", 3200)), 6.0)
ck("10 000 so'z = 95 ball = 9.0",
   (roles.vocab_score(10000),
    roles.ielts_band(roles.vocab_score(10000))), (95, 9.0))
ck("3500 so'z = 44 = 6.0", roles.vocab_score(3500), 44)
ck("6500 so'z = 70 = 7.5",
   (roles.vocab_score(6500), roles.ielts_band(70)), (70, 7.5))
ck("300 so'z = 8 = A1", (roles.vocab_score(300),
                          roles.score_cefr(8)), (8, "A1"))
ck("0 so'z = 0", roles.vocab_score(0), 0)
ck("monoton o'sadi",
   all(roles.vocab_score(i) <= roles.vocab_score(i + 50)
       for i in range(0, 11000, 50)), True)
ck("grammatika shkalasi O'ZGARMAGAN (3200 = 95)",
   roles.score_for_skill("grammar", 3200), 95)

print("\n=== 5. O'QUVCHI KARTASI VA UNITLAR ===")
b = models.Branch(name="Zafar"); db.add(b); db.commit()
s = models.Student(full_name="Ali Valiyev", branch_id=b.id,
                   status="active", phone="998901112255",
                   public_id="STU-VX-1")
db.add(s); db.commit()
u = models.User(username="998901112255",
                password_hash=hash_password("jonyjony"),
                full_name="Ali Valiyev", role=roles.STUDENT,
                branch_id=b.id, is_active=1)
db.add(u); db.commit()
s.user_id = u.id; db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "998901112255", "password": "jonyjony"},
).json()["access_token"]}

ids = [i for (i,) in db.query(models.VocabWord.id)
       .filter(models.VocabWord.language == "en",
               models.VocabWord.is_active == 1)
       .order_by(models.VocabWord.id).all()]
print(f"     faol so'zlar: {len(ids)}")
ck("100 unit uchun 10 000 dan ko'p so'z bor", len(ids) >= 10000, True)
db.bulk_save_objects([
    models.VocabAttempt(student_id=s.id, word_id=wid, game="en_uz",
                        correct=1, date=date.today())
    for wid in ids[:3200]])
db.commit()
card = _skills_card(db, s.id)
voc = [x for x in card["skills"] if x["key"] == "vocabulary"][0]
ck("3200 so'z bilgan bola lug'atda 9.0 EMAS", voc["band"] < 9.0, True)
ck("3200 so'z = 6.0", voc["band"], 6.0)
db.bulk_save_objects([
    models.VocabAttempt(student_id=s.id, word_id=wid, game="en_uz",
                        correct=1, date=date.today())
    for wid in ids[3200:10000]])
db.commit()
card = _skills_card(db, s.id)
voc = [x for x in card["skills"] if x["key"] == "vocabulary"][0]
ck("10 000 so'z bilgan bola lug'atda 9.0", voc["band"], 9.0)
ck("/api/student/skills ham shuni beradi",
   [x for x in c.get("/api/student/skills", headers=H).json()["skills"]
    if x["key"] == "vocabulary"][0]["band"], 9.0)

r = c.get("/api/student/vocab/units?language=en", headers=H)
ck("unitlar status", r.status_code, 200)
ul = r.json()["units"]
keys = [x["key"] for x in ul]
ck("100 unit", len(ul), 100)
ck("oxirgisi Unit 100", keys[-1], "Unit 100")
ck("tartib raqam bo'yicha (Unit 9, 10, ..., 99, 100)",
   keys, [f"Unit {i}" for i in range(1, 101)])
ck("Unit 34..100 har birida 100 so'z",
   all(x["n"] == 100 for x in ul if int(x["key"].split()[-1]) >= 34), True)
r = c.get("/api/student/vocab/round?game=en_uz&language=en&unit=Unit 100",
          headers=H)
ck("Unit 100 bilan round", r.status_code, 200)
ck("Unit 100 savollari keldi", len(r.json().get("items") or []) > 0, True)
r = c.get("/api/student/vocab/round?game=en_uz&language=en&unit=Unit 34",
          headers=H)
ck("Unit 34 bilan round", r.status_code, 200)

print()
db.close()
try:
    from database import engine as _eng
    _eng.dispose()
except Exception:
    pass
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
