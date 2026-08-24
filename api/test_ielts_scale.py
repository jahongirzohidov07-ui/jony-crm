"""IELTS BALI VA DARAJA ZINASI (2026-08-25).

Jahongir: "har bir darajalar orasi 500XP bu juda oson bolib
qolyabdi IELTS 6.5 TURGAN QIZGA 72 kunda IELTS 9.0 olasan
devoryabsan u faqat grammatika va lugat ishlagan bu tomonda reading
listeninglari yoq bolsa kel shuni bunday qilaylik ... har bir skill
boyicha 9.0 ballga teng bolsa 95-100 orasida qilsa bitta skilldan
9.0 degani endi hamma skillarni qoshib ortachasini chiqarganda uni
IELTS balli kelib chiqsin. lekin hozir u B2gacha grammatika ishlagan
xolos bu degani hozir grammatika IELTS 6.0."

Va: "ligalarga kotarish bor unga coin beryabsan lekin biror joyda
ligalar royxati va u yerda qaysi ligaga chiqqanligini korsatadigan
joy yoq ekan".

BU TEST NIMANI ISBOTLAYDI:
  * B2 gacha grammatika ishlagan bola AYNAN 6.0 oladi;
  * 95-100 ball = 9.0, 85-94 = 8.5 (Jahongir bergan ikki tayanch);
  * umumiy band — oltita ko'nikmaning o'rtachasi, ya'ni bitta
    ko'nikma bo'sh tursa ball ko'tarilmaydi;
  * daraja zinasi endi chiziqli emas va sezilarli qiyin;
  * bitta so'zni qayta-qayta o'ynab ball yig'ib bo'lmaydi;
  * ligalar ro'yxati o'quvchiga to'liq ko'rinadi.
"""
import os, sys

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_scale/db.sqlite"
os.makedirs("/tmp/verify_scale", exist_ok=True)
if os.path.exists("/tmp/verify_scale/db.sqlite"):
    os.remove("/tmp/verify_scale/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date
from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password

c = TestClient(main.app)
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


db = SessionLocal()
b = models.Branch(name="Zafar"); db.add(b); db.commit()
st = models.Student(full_name="Hadicha Test", branch_id=b.id,
                    status="active")
db.add(st); db.commit()
SID = st.id
u = models.User(username="hadicha", full_name="Hadicha Test",
                password_hash=hash_password("Parol123!"),
                role=roles.STUDENT, branch_id=b.id, is_active=1)
db.add(u); db.commit()
st.user_id = u.id; db.commit(); db.close()
tok = c.post("/api/auth/login",
             json={"username": "hadicha", "password": "Parol123!"}
             ).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

print("=== 1. JAHONGIR BERGAN IKKI TAYANCH NUQTA ===")
ck("95 ball -> 9.0", roles.ielts_band(95), 9.0)
ck("100 ball -> 9.0", roles.ielts_band(100), 9.0)
ck("85 ball -> 8.5", roles.ielts_band(85), 8.5)
ck("94 ball -> 8.5", roles.ielts_band(94), 8.5)
ck("95 ball CEFR C2", roles.score_cefr(95), "C2")

print("\n=== 2. B2 GACHA GRAMMATIKA = IELTS 6.0 ===")
# Bazadagi ingliz grammatikasining A1+A2+B1+B2 savollari
dbx = SessionLocal()
b2_total = (dbx.query(models.GrammarQuestion)
            .filter(models.GrammarQuestion.language.is_(None),
                    models.GrammarQuestion.level.in_(
                        ("A1", "A2", "B1", "B2"))).count())
dbx.close()
print(f"    bazada A1-B2 grammatika savollari: {b2_total} ta")
sc = roles.skill_score(b2_total)
ck("B2 tugatgan bolaning bali 38-46", 38 <= sc <= 46, True)
ck("B2 tugatgan bolaning bandi 6.0", roles.ielts_band(sc), 6.0)
ck("C1 tugasa 7.5", roles.ielts_band(roles.skill_score(1800)), 7.5)
ck("C2 tugasa 9.0", roles.ielts_band(roles.skill_score(3200)), 9.0)

print("\n=== 3. ZINA MONOTON VA CHIZIQLI EMAS ===")
prev = -1
mono = True
for p in range(0, 4500, 25):
    v = roles.skill_score(p)
    if v < prev:
        mono = False
    prev = v
ck("ball hech qachon kamaymaydi", mono, True)
ck("0 ball -> 0", roles.skill_score(0), 0)
ck("chegaradan yuqori -> 100", roles.skill_score(99999), 100)
# 1-yarim (0->50 ball) 2-yarimdan (50->100) ARZONROQ bo'lishi kerak
half1 = roles.points_for_score(50)
half2 = roles.points_for_score(100) - half1
ck("ikkinchi yarmi qimmatroq", half2 > half1, True)
print(f"    0->50 ball: {half1} ta, 50->100 ball: {half2} ta")

print("\n=== 4. DARAJA ZINASI SEZILARLI QIYINLASHDI ===")
ck("zina o'sib boradi",
   roles.ENG_LEVEL_POINTS == sorted(roles.ENG_LEVEL_POINTS), True)
steps = [roles.ENG_LEVEL_POINTS[i + 1] - roles.ENG_LEVEL_POINTS[i]
         for i in range(len(roles.ENG_LEVEL_POINTS) - 1)]
ck("har qadam oldingisidan katta",
   all(steps[i + 1] > steps[i] for i in range(len(steps) - 1)), True)
ck("Native uchun 20 000 ball", roles.ENG_LEVEL_POINTS[-1], 20000)
# Eski tizimda 2206 ball = Upper-Intermediate edi
ck("2206 ball endi Upper-Intermediate EMAS",
   roles.ENG_LEVELS[roles.level_index_for(2206)]["key"]
   != "upper_intermediate", True)
ck("2206 ball -> Pre-Intermediate",
   roles.ENG_LEVELS[roles.level_index_for(2206)]["key"],
   "pre_intermediate")

print("\n=== 5. FAQAT GRAMMATIKA -> UMUMIY BAND PAST ===")
dbx = SessionLocal()
for i in range(950):
    dbx.add(models.GrammarAttempt(student_id=SID, question_id=i + 1,
                                  correct=1, date=date.today()))
dbx.commit(); dbx.close()
r = c.get("/api/student/skills", headers=H)
ck("skills 200", r.status_code, 200)
d = r.json()
sk = {x["key"]: x for x in d["ielts"]["skills"]}
ck("grammatika bandi 6.0", sk["grammar"]["band"], 6.0)
ck("o'qish bandi 0", sk["reading"]["band"], 0.0)
ck("tinglash bandi 0", sk["listening"]["band"], 0.0)
ck("UMUMIY band 1.0 (6.0 / 6 ko'nikma)", d["ielts"]["band"], 1.0)
ck("ya'ni 9.0 dan JUDA uzoq", d["ielts"]["band"] < 2.0, True)

print("\n=== 6. BITTA SO'ZNI TAKROR O'YNAB BALL YIG'IB BO'LMAYDI ===")
dbx = SessionLocal()
for i in range(300):        # AYNAN bitta so'z, 300 marta
    dbx.add(models.VocabAttempt(student_id=SID, word_id=7,
                                game="en_uz", correct=1,
                                date=date.today()))
dbx.commit(); dbx.close()
d = c.get("/api/student/skills", headers=H).json()
voc = [x for x in d["skills"] if x["key"] == "vocabulary"][0]
ck("300 ta takror urinish = 1 ball", voc["points"], 1)
ck("lug'at bali hali 0", voc["score"], 0)
dbx = SessionLocal()
for i in range(950):        # endi 950 ta ALOHIDA so'z
    dbx.add(models.VocabAttempt(student_id=SID, word_id=1000 + i,
                                game="en_uz", correct=1,
                                date=date.today()))
dbx.commit(); dbx.close()
d = c.get("/api/student/skills", headers=H).json()
voc = [x for x in d["skills"] if x["key"] == "vocabulary"][0]
ck("951 ta alohida so'z -> 6.0", voc["band"], 6.0)

print("\n=== 7. HAR KO'NIKMADA MASHQ ZAXIRASI KO'RINADI ===")
d = c.get("/api/student/skills", headers=H).json()
for x in d["skills"]:
    ck(f"{x['key']}: zaxira soni bor", x["available"] > 0, True)
ck("qamrov foizi hisoblanadi",
   all(0 <= x["coverage"] <= 100 for x in d["skills"]), True)

print("\n=== 8. PROFIL VA YO'L XARITASIDA IELTS KARTASI ===")
r = c.get("/api/student/profile", headers=H)
ck("profil 200", r.status_code, 200)
pf = r.json()
ck("profilda ielts bloki bor", "ielts" in pf, True)
ck("radar bali endi CEFR zinasidan",
   all("band" in x and "cefr" in x for x in pf["radar"]), True)
ck("radar izohida 44/70/95 bor", "44" in pf["radar_note"], True)
ck("profilda liga ko'rinadi", "league" in pf, True)

print("\n=== 9. LIGALAR RO'YXATI O'QUVCHIGA OCHIQ ===")
r = c.get("/api/student/leagues", headers=H)
ck("leagues 200", r.status_code, 200)
lg = r.json()
ck("14 ta liga", len(lg["leagues"]), 14)
ck("bittasi 'current'",
   sum(1 for x in lg["leagues"] if x["state"] == "current"), 1)
ck("ro'yxat rank bo'yicha tartibda",
   [x["rank"] for x in lg["leagues"]]
   == sorted(x["rank"] for x in lg["leagues"]), True)
ck("har ligada mukofot coin maydoni bor",
   all("coin" in x for x in lg["leagues"]), True)
ck("mukofot coin yig'indisi 136",
   sum(x["coin"] for x in lg["leagues"]), 136)
ck("XP chegaralari o'sib boradi",
   [x["min_xp"] for x in lg["leagues"]]
   == sorted(x["min_xp"] for x in lg["leagues"]), True)
ck("qulflanganlarda 'yana X XP' bor",
   all(x["xp_left"] > 0 for x in lg["leagues"]
       if x["state"] == "locked"), True)
ck("izoh matni bor", bool(lg["note"]), True)

print("\n=== 10. REYTINGDA HAM LIGA KO'RINADI ===")
r = c.get("/api/student/leaderboard?scope=all&period=all", headers=H)
ck("leaderboard 200", r.status_code, 200)
ck("javobda liga bor", "league" in r.json(), True)

print("\n=== 11. IELTS YAXLITLASH QOIDASI ===")
ck("6.25 -> 6.5", roles.ielts_round(6.25), 6.5)
ck("6.24 -> 6.0", roles.ielts_round(6.24), 6.0)
ck("6.75 -> 7.0", roles.ielts_round(6.75), 7.0)
ck("o'rtacha 9.0 dan oshmaydi",
   roles.ielts_overall([9.0] * 6), 9.0)

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
