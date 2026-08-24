"""O'RGANISH TIZIMI YANGILANISHLARI (2026-08-24).

Jahongir: "bitta sozni 6ta togri qilgan bo'lsa, xato qilganlarni
korsatsin qayta qayta... Writingni ham darajalanmagan... Boshqa
tillarni grammatikasi yoq ekan... c1 va C2 mavzularni ham...
mashqlar soni 20ta... qiynalgan mavzulardan yana takrorlaydigan
joyi ham bo'lsin".
"""
import os, sys, json

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_lu/db.sqlite"
os.makedirs("/tmp/verify_lu", exist_ok=True)
if os.path.exists("/tmp/verify_lu/db.sqlite"):
    os.remove("/tmp/verify_lu/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
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


b = models.Branch(name="Zafar"); db.add(b); db.commit()
st = models.Student(full_name="Test O'quvchi", branch_id=b.id,
                    status="active")
db.add(st); db.commit()
u = models.User(username="stud", full_name="Test O'quvchi",
                password_hash=hash_password("Parol123!"),
                role=roles.STUDENT, branch_id=b.id, is_active=1)
db.add(u); db.commit()
st.user_id = u.id; db.commit()
tok = c.post("/api/auth/login",
             json={"username": "stud", "password": "Parol123!"}
             ).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

print("=== 1. GRAMMAR ROUND ENDI 20 TALIK ===")
ck("konstanta 20", roles.GRAMMAR_ROUND_SIZE, 20)
topic = db.query(models.GrammarQuestion).filter(
    models.GrammarQuestion.level == "A1",
    models.GrammarQuestion.language.is_(None)).first().topic
r = c.get("/api/student/grammar/round", params={"topic": topic},
          headers=H)
ck("count bermasa 20 ta keladi", len(r.json()["items"]), 20)

print("\n=== 2. C1/C2 INGLIZ GRAMMATIKASI ===")
for lv in ("C1", "C2"):
    n = db.query(models.GrammarQuestion).filter(
        models.GrammarQuestion.level == lv,
        models.GrammarQuestion.language == "en").count()
    ck(f"{lv} savollari bazada ({n})", n >= 20, True)
j = c.get("/api/student/grammar/topics", headers=H).json()
ck("javobda c1/c2 kalitlari bor", "c1" in j and "c2" in j, True)
ck("c1 hali qulf (B2 tugamagan)", j["c1_locked"], True)
ck("available C2 gacha", j["available"][-1], "C2")

print("\n=== 3. RU/DE/KO GRAMMATIKASI ===")
for lang in ("ru", "de", "ko"):
    n1 = db.query(models.GrammarQuestion).filter(
        models.GrammarQuestion.language == lang,
        models.GrammarQuestion.level == "A1").count()
    n2 = db.query(models.GrammarQuestion).filter(
        models.GrammarQuestion.language == lang,
        models.GrammarQuestion.level == "A2").count()
    ck(f"{lang}: A1={n1} A2={n2} bor", n1 >= 20 and n2 >= 20, True)
    j = c.get(f"/api/student/grammar/topics?language={lang}",
              headers=H).json()
    ck(f"{lang}: 4 ta A1 mavzu", len(j["a1"]["topics"]), 4)
    ck(f"{lang}: available faqat A1/A2", j["available"], ["A1", "A2"])
    ck(f"{lang}: A2 qulf", j["a2_locked"], True)
jen = c.get("/api/student/grammar/topics?language=en", headers=H).json()
ru_topic = c.get("/api/student/grammar/topics?language=ru",
                 headers=H).json()["a1"]["topics"][0]["topic"]
ck("ruscha mavzu inglizchada YO'Q",
   any(t["topic"] == ru_topic for t in jen["a1"]["topics"]), False)
r = c.get("/api/student/grammar/round",
          params={"topic": ru_topic, "language": "ru"}, headers=H)
ck("ruscha round ochiladi", r.status_code, 200)
qid = r.json()["items"][0]["id"]
qq = db.query(models.GrammarQuestion).get(qid)
ck("savol chindan ruscha", qq.language, "ru")
r = c.post("/api/student/grammar/answer", headers=H,
           json={"question_id": qid, "answer": qq.answer})
ck("ruscha javob tekshiriladi", r.json().get("correct"), True)

print("\n=== 4. XATO USTIDA ISHLASH — LUG'AT ===")
words = db.query(models.VocabWord).filter(
    models.VocabWord.language == "en").limit(30).all()
if len(words) < 12:
    # test bazasida so'z bo'lmasa o'zimiz qo'shamiz
    unit = None
    for i in range(30):
        db.add(models.VocabWord(word=f"testword{i}",
                                translation=f"tarjima{i}",
                                language="en", is_active=1))
    db.commit()
    words = db.query(models.VocabWord).filter(
        models.VocabWord.language == "en").limit(30).all()
W = words[:12]
# 0-2: KO'P XATO qilingan; 3-5: 6+ marta to'g'ri (o'zlashtirilgan)
for w in W[:3]:
    for _ in range(4):
        db.add(models.VocabAttempt(student_id=st.id, word_id=w.id,
                                   game="en_uz", correct=0))
for w in W[3:6]:
    for _ in range(6):
        db.add(models.VocabAttempt(student_id=st.id, word_id=w.id,
                                   game="en_uz", correct=1))
db.commit()
from student_app import _pick_vocab_words
pool = words
picked = _pick_vocab_words(db, st.id, pool, 10)
ids = [w.id for w in picked]
ck("xato so'zlar birinchi uchlikda",
   set(x.id for x in W[:3]) <= set(ids[:3]), True)
mastered = {x.id for x in W[3:6]}
ck("6+ to'g'ri so'zlar tushmadi",
   mastered & set(ids), set())
# pool kichik bo'lsa mastered to'ldiruvchi bo'ladi
small = W[:3] + W[3:6]
picked2 = _pick_vocab_words(db, st.id, small, 6)
ck("boshqa so'z qolmasa mastered to'ldiradi", len(picked2), 6)

print("\n=== 5. GRAMMAR: XATO SAVOL BIRINCHI ===")
qs = db.query(models.GrammarQuestion).filter(
    models.GrammarQuestion.topic == topic).all()
bad_q = qs[3]
for _ in range(4):
    db.add(models.GrammarAttempt(student_id=st.id,
                                 question_id=bad_q.id, correct=0))
db.commit()
r = c.get("/api/student/grammar/round",
          params={"topic": topic, "count": 5}, headers=H)
ck("ko'p xato qilingan savol roundda bor",
   any(x["id"] == bad_q.id for x in r.json()["items"]), True)

print("\n=== 6. QIYNALGAN MAVZULAR ===")
j = c.get("/api/student/grammar/topics", headers=H).json()
ck("weak ro'yxati bor", isinstance(j.get("weak"), list), True)
ck("qiynalgan mavzu ichida", any(
    w["topic"] == topic for w in j["weak"]), True)

print("\n=== 7. WRITING DARAJALARI ===")
r = c.get("/api/student/practice/writing/levels", headers=H)
ck("writing levels 200", r.status_code, 200)
lvs = {x["level"]: x for x in r.json()["levels"]}
ck("A1 da yozish mashqi bor", lvs["A1"]["total"] > 0, True)
r = c.get("/api/student/practice/writing/round?level=A1&count=15",
          headers=H)
ck("A1 writing round", r.status_code, 200)
ck("15 tagacha keladi", len(r.json()["items"]) <= 15, True)
refs = [x["ref"] for x in r.json()["items"]]
lv_ok = all(
    (db.query(models.GrammarQuestion).get(int(x.split(":")[1])).level
     or "A1") == "A1" for x in refs)
ck("hammasi A1 jumlalari", lv_ok, True)

print("\n=== 8. RU LISTENING JUMLALARI ===")
r = c.get("/api/student/practice/listening/round?language=ru",
          headers=H)
if r.status_code == 200:
    kinds = {x["kind"] for x in r.json()["items"]}
    ck("ruscha diktantda jumla bor", "listen_dictation" in kinds, True)
    gr = [x for x in r.json()["items"] if x["kind"] == "listen_dictation"]
    qid2 = int(gr[0]["ref"].split(":")[1])
    ck("jumla ruscha bazadan",
       db.query(models.GrammarQuestion).get(qid2).language, "ru")
else:
    ck("ru diktant ishlashi kerak edi", r.status_code, 200)

print("\n=== 9. ESKI YO'L BUZILMADI ===")
r = c.get("/api/student/grammar/topics", headers=H)
ck("en topics eski kalitlar bilan",
   all(k in r.json() for k in ("a1", "a2", "b1", "b2")), True)
r = c.get("/api/student/practice/reading/round", headers=H)
ck("reading round ishlaydi", r.status_code, 200)
r = c.get("/api/student/vocab/round?game=en_uz", headers=H)
ck("vocab round ishlaydi", r.status_code, 200)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
