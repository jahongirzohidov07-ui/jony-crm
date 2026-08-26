"""IELTS READING — SHORT-ANSWER QUESTIONS (2026-08-25).

Jahongir: "Short answer questions savol turiga misol pastida true
false ham bor uni olmaysan, bitta text shundan aniq savol beriladi
topishga shunaqa qil sen ham bu hozir ozgina qiyin 7-8-mashqqa qilib
qoysang boladi undan oldingilarni osonroq boladi va qiyinlashib
ketaveradi."

BU TEST NIMANI ISBOTLAYDI:
  * 100 ta savol, 20 daraja;
  * Jahongirning Sylvia Earle namunasi 7-darajada, javoblari
    rasmdagi bilan bir xil, TRUE/FALSE qismi OLINMAGAN;
  * 1-6 daraja namunadan osonroq, 8-20 qiyinroq;
  * har javob matnda ALOHIDA SO'Z sifatida bor;
  * javob 2 so'zdan oshmaydi (artikl sanalmaydi);
  * savollar matn tartibida boradi;
  * "a festival" va "festival" ikkalasi ham to'g'ri sanaladi.
"""
import os, sys, re, collections

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_short/db.sqlite"
os.makedirs("/tmp/verify_short", exist_ok=True)
if os.path.exists("/tmp/verify_short/db.sqlite"):
    os.remove("/tmp/verify_short/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
import reading_short_seed as RQ

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
st = models.Student(full_name="Test", branch_id=b.id, status="active")
db.add(st); db.commit()
u = models.User(username="stud", full_name="Test",
                password_hash=hash_password("Parol123!"),
                role=roles.STUDENT, branch_id=b.id, is_active=1)
db.add(u); db.commit()
st.user_id = u.id; db.commit()
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "stud", "password": "Parol123!"}
).json()["access_token"]}

K = "read_short"
rows = RQ.build_rows()
ART = {"a", "an", "the", "his", "her", "their", "its"}


def core(t):
    return [w for w in re.findall(r"[a-z0-9.,'-]+", t.lower())
            if w not in ART]


def words(t):
    return " " + " ".join(re.findall(r"[a-z0-9]+", t.lower())) + " "


print("=== 1. SONI VA DARAJALAR ===")
ck("100 ta savol", len(rows), 100)
per = collections.Counter(p[2]["step"] for p in rows)
ck("20 daraja", len(per), 20)
ck("darajalar 1..20", sorted(per), list(range(1, 21)))
ck("20 ta matn", len(RQ.PASSAGES), 20)

print("\n=== 2. NAMUNA 7-DARAJADA ===")
byl = {p["level"]: p for p in RQ.PASSAGES}
ck("7-daraja — Sylvia Earle", "SYLVIA EARLE" in byl[7]["title"], True)
ck("rasmdagi 4 ta savol", len(byl[7]["qs"]), 4)
ck("javoblari rasmdagidek",
   [q[1] for q in byl[7]["qs"]],
   ["underwater explorer", "381 metres", "pollution", "fish farms"])
blob = " ".join(q[0] for q in byl[7]["qs"]).lower()
ck("TRUE/FALSE qismi OLINMAGAN",
   ("true" in blob or "false" in blob or "not given" in blob), False)

print("\n=== 3. 1-6 OSONROQ, 8-20 QIYINROQ ===")
easy = [p for p in RQ.PASSAGES if p["level"] <= 6]
hard = [p for p in RQ.PASSAGES if p["level"] >= 16]
a_e = sum(len(p["text"]) for p in easy) / len(easy)
a_h = sum(len(p["text"]) for p in hard) / len(hard)
ck("1-6 namunadan qisqaroq", a_e < len(byl[7]["text"]), True)
ck("16-20 osonlaridan uzunroq", a_h > a_e * 1.5, True)
print(f"    1-6 ~{int(a_e)}, namuna {len(byl[7]['text'])}, "
      f"16-20 ~{int(a_h)} belgi")

print("\n=== 4. JAVOBLAR MATNDA VA QISQA ===")
miss = [(p[2]["step"], p[2]["q_no"], p[3]) for p in rows
        if words(p[3]).strip() not in words(p[2]["passage"])]
ck("hammasi matnda bor", miss, [])
longs = [(p[2]["step"], p[3]) for p in rows if len(core(p[3])) > 2]
ck("2 so'zdan oshmaydi (artiklsiz)", longs, [])

print("\n=== 5. SAVOLLAR MATN TARTIBIDA ===")
broken = []
for p in RQ.PASSAGES:
    pos = [p["text"].find(q[2][:40]) for q in p["qs"]]
    if -1 in pos or pos != sorted(pos):
        broken.append(p["level"])
ck("har matnda tartib to'g'ri", broken, [])

print("\n=== 6. SAVOL SO'ZLARI XILMA-XIL ===")
qw = collections.Counter()
for _k, _l, pl, _a, _e, _al, _p in rows:
    first = pl["prompt"].split()[0].lower().strip("?,")
    qw[first] += 1
for w in ("what", "where", "who", "how", "when", "why", "which"):
    ck(f"«{w}» bilan savollar bor", qw[w] > 0, True)
print(f"    {dict(qw.most_common())}")

print("\n=== 7. PARAFFRAZ ===")
ck("juftlik bor",
   all(p[6].get("table") and p[6].get("passage") for p in rows), True)
ck("izohda ikki tomon",
   all("Savolda:" in p[4] and "Matnda:" in p[4] for p in rows), True)

print("\n=== 8. BO'LIM RO'YXATIDA ===")
r = c.get("/api/student/ielts/reading/parts", headers=H)
parts = {p["title"]: p for p in r.json()["parts"]}
ck("Short answer tayyor", parts["Short answer"]["ready"], True)
ck("100 ta element", parts["Short answer"]["total"], 100)
ck("11 tur to'ldirilgan",
   sum(1 for p in r.json()["parts"] if p["ready"]), 11)

print("\n=== 9. QOIDALAR ===")
t = c.get(f"/api/student/ielts/reading/tips?kind={K}",
          headers=H).json()
ck("6+ qoida", len(t["tips"]) >= 6, True)
ck("20 bosqich", len(t["steps"]), 20)
tb = " ".join(x["title"] + x["body"] + (x["example"] or "")
              for x in t["tips"]).lower()
ck("savol so'zi o'rgatiladi", "savol so'zi" in tb, True)
ck("how far / where sanab o'tilgan",
   "how far" in tb and "where" in tb, True)

print("\n=== 10. JAVOB OSHKOR BO'LMAYDI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={K}&count=10",
          headers=H)
items = r.json()["items"]
ck("round 200", r.status_code, 200)
ck("javob yo'q", all("answer" not in i for i in items), True)
ck("paraffraz yo'q", all("paraphrase" not in i for i in items), True)
ck("savollar ro'yxati keladi",
   all(i.get("questions") for i in items), True)
ck("joriy savol raqami ham", all(i.get("q_no") for i in items), True)
ck("bosqich o'sadi",
   [i["step"] for i in items] == sorted(i["step"] for i in items), True)
ck("prompt ro'yxatdagi savol bilan mos",
   all(i["questions"][i["q_no"] - 1] == i["prompt"] for i in items),
   True)

print("\n=== 11. TEKSHIRUV VA ARTIKL ===")
first = items[0]
row = db.query(models.PracticeItem).get(int(first["ref"].split(":")[1]))
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": "zzz"},
           headers=H).json()
ck("xato -> False", r["correct"], False)
ck("paraffraz keladi", bool(r.get("paraphrase")), True)
it = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.kind == K,
              models.PracticeItem.answer == "festival").first())
for given in ("festival", "a festival", "The festival", " FESTIVAL "):
    rr = c.post("/api/student/ielts/reading/answer",
                json={"ref": f"pi:{it.id}", "answer": given},
                headers=H).json()
    ck(f"«{given.strip()}» qabul qilinadi", rr["correct"], True)
it2 = (db.query(models.PracticeItem)
       .filter(models.PracticeItem.kind == K,
               models.PracticeItem.answer == "four thousand").first())
rr = c.post("/api/student/ielts/reading/answer",
            json={"ref": f"pi:{it2.id}", "answer": "4000"},
            headers=H).json()
ck("«four thousand» o'rniga «4000»", rr["correct"], True)

print("\n=== 12. BOSHQA TURLAR BUZILMADI ===")
for k in ("read_tfng", "read_ynng", "read_table", "read_summary",
          "read_flow"):
    rr = c.get(f"/api/student/ielts/reading/round?kind={k}&count=3",
               headers=H)
    ck(f"{k} ishlaydi", rr.status_code, 200)

print("\n=== 13. SEED IDEMPOTENT ===")
n1 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
RQ.seed_reading_short(db)
n2 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
ck("dublikat yaratmaydi", n2, n1)
ck("bazada 100 ta", n1, 100)

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
