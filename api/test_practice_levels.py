"""READING/LISTENING DARAJALARI + CEFR/IELTS + SON REGRESSIYALARI
(2026-08-24).

Jahongir: "reading va listeninglarda daraja bo'yicha qilinmagan...
CEFR va IELTS qismini intermediate tugatganda ochiladigan qilgan
edik u yoqolib qolibdi... a1 dan boshlab c2 darajagacha...
mashqlarni ham kopaytir... 5talik paytida ishlaganlarni ham korib
chiq ular kopayganda ishlamagan bolsa ishlashi kerak".
"""
import os, sys, json

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_plv/db.sqlite"
os.makedirs("/tmp/verify_plv", exist_ok=True)
if os.path.exists("/tmp/verify_plv/db.sqlite"):
    os.remove("/tmp/verify_plv/db.sqlite")
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
st.user_id = u.id
db.commit()

tok = c.post("/api/auth/login",
             json={"username": "stud", "password": "Parol123!"}
             ).json()["access_token"]
H = {"Authorization": f"Bearer {tok}"}

print("=== 1. SEEDLAR: B2/C1/C2 KONTENT BAZAGA TUSHDI ===")
for lv in ("B2", "C1", "C2"):
    n_txt = db.query(models.ReadingText).filter(
        models.ReadingText.level == lv).count()
    n_pi = db.query(models.PracticeItem).filter(
        models.PracticeItem.level == lv).count()
    ck(f"{lv}: reading matnlari bor", n_txt > 0, True)
    ck(f"{lv}: practice itemlar bor", n_pi > 0, True)

print("\n=== 2. DARAJA BO'LIMLARI RO'YXATI ===")
r = c.get("/api/student/practice/reading/levels", headers=H)
ck("status 200", r.status_code, 200)
lvs = {x["level"]: x for x in r.json()["levels"]}
ck("6 ta daraja", sorted(lvs), ["A1", "A2", "B1", "B2", "C1", "C2"])
ck("A1 Beginner deb ataladi", lvs["A1"]["label"], "Beginner")
ck("C2 Native deb ataladi", lvs["C2"]["label"], "Native")
ck("har darajada mashq bor",
   all(lvs[k]["total"] > 0 for k in lvs), True)
r = c.get("/api/student/practice/listening/levels", headers=H)
ck("listening ham 200", r.status_code, 200)
llv = {x["level"]: x for x in r.json()["levels"]}
ck("listening C1 da mashq bor", llv["C1"]["total"] > 0, True)
r = c.get("/api/student/practice/writing/levels", headers=H)
ck("writingda daraja bo'limi yo'q (404)", r.status_code, 404)

print("\n=== 3. DARAJA FILTRI ISHLAYDI ===")
r = c.get("/api/student/practice/reading/round?level=C1", headers=H)
ck("C1 matn keladi", r.json()["text"]["level"], "C1")
r = c.get("/api/student/practice/reading/round?level=A1", headers=H)
ck("A1 matn keladi", r.json()["text"]["level"], "A1")
r = c.get("/api/student/practice/reading/round?kind=read_tfng&level=B2",
          headers=H)
ck("tfng B2 to'plami", r.json()["text"]["level"], "B2")
r = c.get("/api/student/practice/listening/round?kind=listen_qa&level=C2",
          headers=H)
ck("listen_qa C2 itemlari", all(
    x["level"] == "C2" for x in r.json()["items"]), True)
# noto'g'ri daraja — e'tiborsiz (hammasi kabi)
r = c.get("/api/student/practice/reading/round?level=X9", headers=H)
ck("noto'g'ri daraja yiqitmaydi", r.status_code, 200)

print("\n=== 4. COUNT — MASHQLAR SONI ===")
r = c.get("/api/student/practice/listening/round?kind=listen_qa&count=30",
          headers=H)
n_all = db.query(models.PracticeItem).filter(
    models.PracticeItem.skill == "listening",
    models.PracticeItem.kind == "listen_qa").count()
ck("bor-yo'g'i qancha bo'lsa shuncha keladi",
   len(r.json()["items"]), min(30, n_all))
r2 = c.get("/api/student/practice/listening/round?kind=listen_qa",
           headers=H)
ck("count bermasa eski 8 talik qoladi",
   len(r2.json()["items"]) <= 8, True)

print("\n=== 5. IELTS QULFI ===")
r = c.get("/api/student/learn", headers=H)
g = r.json().get("ielts") or {}
ck("bo'lim javobda bor", "unlocked" in g, True)
ck("yangi o'quvchiga qulf", g.get("unlocked"), False)
ck("sabab yozilgan", "Intermediate" in (g.get("need_label") or ""), True)
# Intermediate tugatadigan ball beramiz: 4 daraja * ball
need = roles.PRACTICE_POINTS_PER_LEVEL * 4
db.add(models.ExerciseResult(student_id=st.id, skill="reading",
                             correct=need, total=need))
db.commit()
r = c.get("/api/student/learn", headers=H)
ck("intermediate tugagach ochiladi",
   (r.json().get("ielts") or {}).get("unlocked"), True)

print("\n=== 6. '5TALIK DAVRI' REGRESSIYALARI ===")
# 6a. Grammar: count=50 — mavzu banki kichik, boshqa mavzudan to'ladi
topics = [t for (t,) in db.query(
    models.GrammarQuestion.topic).filter(
    models.GrammarQuestion.level == "A1").distinct().all()]
t0 = topics[0]
own = db.query(models.GrammarQuestion).filter(
    models.GrammarQuestion.topic == t0).count()
r = c.get(f"/api/student/grammar/round?topic={t0}&count=50", headers=H)
items = r.json()["items"]
ck("50 so'raganda bankdan ko'p keladi", len(items) > own, True)
ck("50 dan oshmaydi", len(items) <= 50, True)
# boshqa mavzudan kelgan savolga javob berish ham ishlaydi
other_q = next((x for x in items
                if db.query(models.GrammarQuestion).get(x["id"]).topic
                != t0), None)
ck("boshqa mavzu savoli aralashgan", other_q is not None, True)
if other_q:
    qq = db.query(models.GrammarQuestion).get(other_q["id"])
    r = c.post("/api/student/grammar/answer", headers=H,
               json={"question_id": qq.id, "answer": qq.answer})
    ck("unga javob berish ishlaydi", r.status_code, 200)
    ck("to'g'ri deb baholandi", r.json().get("correct"), True)

# 6b. Vocab: "Hammasi" (katta count) pool kichik bo'lsa ham yiqilmaydi
r = c.get("/api/student/vocab/round?game=en_uz&count=500", headers=H)
ck("vocab katta count yiqilmaydi", r.status_code, 200)

# 6c. Daraja tanlamasdan eski yo'l o'zgarmagan
r = c.get("/api/student/practice/reading/round", headers=H)
ck("darajasiz round ishlaydi", r.status_code, 200)
r = c.get("/api/student/practice/listening/round?language=en", headers=H)
ck("diktant round ishlaydi", r.status_code, 200)

# 6d. Diktantda daraja: C1 tanlansa so'zlar aralashmaydi
r = c.get("/api/student/practice/listening/round?level=B1", headers=H)
if r.status_code == 200:
    kinds = {x["kind"] for x in r.json()["items"]}
    ck("B1 diktantida so'z mashqi yo'q (faqat jumla)",
       "listen_type" not in kinds and "listen_choice" not in kinds, True)
else:
    ck("B1 diktanti bo'sh bo'lsa tushunarli xato", r.status_code, 400)

print("\n" + ("HAMMASI O'TDI" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
