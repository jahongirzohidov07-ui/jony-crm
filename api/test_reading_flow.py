"""IELTS READING — FLOW-CHART COMPLETION (2026-08-25).

Jahongir: "mana Flowchart completion uchun misol senga shunda sal
osonlashtirib buni 5-ga qoyda undan oldingilarni sal osonlashtirib,
umumiy qiyindan osonga qarab ketgizish kerak."

BU TEST NIMANI ISBOTLAYDI:
  * 100 dan ortiq mashq, 20 daraja;
  * Jahongirning namunalari 5, 6 va 7-darajada, javoblari kitobning
    javob kaliti bilan bir xil;
  * 1-4 daraja namunadan OSONROQ (matn qisqaroq);
  * har javob matnda ALOHIDA SO'Z sifatida bor;
  * javob ikki so'zdan oshmaydi (NO MORE THAN TWO WORDS);
  * flow-chart HAR DOIM matn tartibi bilan boradi — bu turning
    ta'rifi, test buni har sxemada tekshiradi;
  * javob/paraffraz mashq boshida yuborilmaydi.
"""
import os, sys, re, collections

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_flow/db.sqlite"
os.makedirs("/tmp/verify_flow", exist_ok=True)
if os.path.exists("/tmp/verify_flow/db.sqlite"):
    os.remove("/tmp/verify_flow/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
import reading_flow_seed as RF

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

K = "read_flow"
rows = RF.build_rows()


def words(t):
    return " " + " ".join(re.findall(r"[a-z0-9]+", t.lower())) + " "


print("=== 1. SONI VA DARAJALAR ===")
ck("100 dan ko'p", len(rows) >= 100, True)
print(f"    jami: {len(rows)} ta")
per = collections.Counter(p[2]["step"] for p in rows)
ck("20 daraja", len(per), 20)
ck("darajalar 1..20", sorted(per), list(range(1, 21)))
ck("20 ta sxema", len(RF.PASSAGES), 20)

print("\n=== 2. NAMUNALAR 5, 6, 7-DARAJADA ===")
byl = {p["level"]: p for p in RF.PASSAGES}
ck("5-daraja — Freya Stark", "FREYA STARK" in byl[5]["title"], True)
ck("6-daraja — Malone Part 1", "PART 1" in byl[6]["title"], True)
ck("7-daraja — Malone Part 2", "PART 2" in byl[7]["title"], True)
ck("Freya javoblari",
   [g[1] for g in byl[5]["gaps"]],
   ["London University", "nurse", "Arabic", "donkey", "Gold Medal",
    "12 years"])
# Kitobning javob kaliti: 1 Britain, 2 Human Geography, 3 teacher,
# 4 1,400 kilometres, 5 remote, 6 expedition
ck("Malone P1 javoblari kalit bilan bir xil",
   [g[1] for g in byl[6]["gaps"]],
   ["Britain", "Human Geography", "teacher", "1,400 kilometres",
    "remote", "expedition"])
# 7 Discovered, 8 Married, 9 three children, 10 twelve months,
# 11 TV series, 12 travel
ck("Malone P2 javoblari kalit bilan bir xil",
   [g[1] for g in byl[7]["gaps"]],
   ["Discovered", "Married", "three children", "twelve months",
    "TV series", "travel"])

print("\n=== 3. 1-4 DARAJA NAMUNADAN OSONROQ ===")
easy = [p for p in RF.PASSAGES if p["level"] <= 4]
a_e = sum(len(p["text"]) for p in easy) / len(easy)
ck("namunadan qisqaroq matn", a_e < len(byl[5]["text"]), True)
print(f"    1-4 ~{int(a_e)} belgi, 5-daraja {len(byl[5]['text'])} belgi")
hard = [p for p in RF.PASSAGES if p["level"] >= 16]
a_h = sum(len(p["text"]) for p in hard) / len(hard)
ck("16-20 osonlaridan uzunroq", a_h > a_e * 1.8, True)
print(f"    16-20 ~{int(a_h)} belgi")

print("\n=== 4. JAVOBLAR MATNDA ALOHIDA SO'Z SIFATIDA ===")
miss = [(p[2]["step"], p[2]["gap_no"], p[3]) for p in rows
        if words(p[3]).strip() not in words(p[2]["passage"])]
ck("hammasi matnda bor", miss, [])
longs = [(p[2]["step"], p[3]) for p in rows if len(p[3].split()) > 2]
ck("ikki so'zdan oshmaydi", longs, [])

print("\n=== 5. TARTIB — BU TURNING TA'RIFI ===")
# Flow-chart ketma-ketlik demak: javoblar matnda ham SHU tartibda.
broken = []
for p in RF.PASSAGES:
    pos = [p["text"].find(g[3][:40]) for g in p["gaps"]]
    if -1 in pos or pos != sorted(pos):
        broken.append(p["level"])
ck("har sxemada javoblar matn tartibida", broken, [])

print("\n=== 6. PARAFFRAZ ===")
ck("juftlik bor",
   all(p[6].get("table") and p[6].get("passage") for p in rows), True)
ck("izohda ikki tomon",
   all("Sxemada:" in p[4] and "Matnda:" in p[4] for p in rows), True)

print("\n=== 7. BO'LIM RO'YXATIDA ===")
r = c.get("/api/student/ielts/reading/parts", headers=H)
parts = {p["title"]: p for p in r.json()["parts"]}
ck("Flow-chart Completion bor", "Flow-chart Completion" in parts, True)
ck("tayyor", parts["Flow-chart Completion"]["ready"], True)
ck("elementlar", parts["Flow-chart Completion"]["total"], len(rows))
ck("endi 13 ta tur ro'yxatda", len(r.json()["parts"]), 13)
ck("6 tasi to'ldirilgan",
   sum(1 for p in r.json()["parts"] if p["ready"]), 6)

print("\n=== 8. QOIDALAR ===")
t = c.get(f"/api/student/ielts/reading/tips?kind={K}",
          headers=H).json()
ck("6+ qoida", len(t["tips"]) >= 6, True)
ck("20 bosqich", len(t["steps"]), 20)
tb = " ".join(x["title"] + x["body"] for x in t["tips"]).lower()
ck("tartib qoidasi o'rgatiladi", "tartib" in tb, True)
ck("ikki so'z qoidasi ham", "ikki so'z" in tb, True)

print("\n=== 9. JAVOB OSHKOR BO'LMAYDI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={K}&count=10",
          headers=H)
items = r.json()["items"]
ck("round 200", r.status_code, 200)
ck("javob yo'q", all("answer" not in i for i in items), True)
ck("paraffraz yo'q", all("paraphrase" not in i for i in items), True)
ck("sxema keladi", all(i.get("flow") for i in items), True)
ck("sxema sarlavhasi", all(i.get("flow_title") for i in items), True)
ck("bosqich o'sadi",
   [i["step"] for i in items] == sorted(i["step"] for i in items), True)
bad = [i["step"] for i in items
       if sum(x.count("______") for x in i["flow"]) != 1]
ck("faqat bitta quti ochiq", bad, [])
ck("ko'rsatmada TWO WORDS bor",
   "TWO WORDS" in items[0]["instruction"], True)

print("\n=== 10. TEKSHIRUV VA MUQOBIL JAVOBLAR ===")
first = items[0]
row = db.query(models.PracticeItem).get(int(first["ref"].split(":")[1]))
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": "zzz"},
           headers=H).json()
ck("xato -> False", r["correct"], False)
ck("paraffraz keladi", bool(r.get("paraphrase")), True)
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"],
                 "answer": f" {row.answer.upper()} "},
           headers=H).json()
ck("registr e'tiborsiz", r["correct"], True)
for ans, alt in (("three children", "3 children"),
                 ("twelve months", "12 months"),
                 ("TV series", "television series"),
                 ("12 years", "twelve years")):
    it = (db.query(models.PracticeItem)
          .filter(models.PracticeItem.kind == K,
                  models.PracticeItem.answer == ans).first())
    rr = c.post("/api/student/ielts/reading/answer",
                json={"ref": f"pi:{it.id}", "answer": alt},
                headers=H).json()
    ck(f"«{ans}» o'rniga «{alt}»", rr["correct"], True)
# vergul e'tiborsiz
it = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.kind == K,
              models.PracticeItem.answer == "1,400 kilometres").first())
rr = c.post("/api/student/ielts/reading/answer",
            json={"ref": f"pi:{it.id}", "answer": "1400 kilometres"},
            headers=H).json()
ck("vergulsiz ham to'g'ri", rr["correct"], True)

print("\n=== 11. BOSHQA TURLAR BUZILMADI ===")
for k in ("read_tfng", "read_ynng", "read_table", "read_summary"):
    rr = c.get(f"/api/student/ielts/reading/round?kind={k}&count=3",
               headers=H)
    ck(f"{k} ishlaydi", rr.status_code, 200)

print("\n=== 12. SEED IDEMPOTENT ===")
n1 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
RF.seed_reading_flow(db)
n2 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
ck("dublikat yaratmaydi", n2, n1)
ck("bazada build_rows bilan bir xil", n1, len(rows))

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
