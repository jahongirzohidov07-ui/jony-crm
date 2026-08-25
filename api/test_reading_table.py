"""IELTS READING — TABLE COMPLETION (2026-08-25).

Jahongir: "keyin Table Completion qilaylik unda birinchi men senga
mashqlar tashlayman unit 1 paraphrases ... Shunaqa paraphraselar
topish skillari rivojlanishi kerak, javoblar tushuntirilganda
readingda doim paraphraselarni korsatib tushuntirish kerak, senga
misollar tashladim shunaqa qilib tuzib ber bundan ozgina
osonroqlaridan boshlab buni 10-ga qoyasan va sekin qiyinlashib
boraversin 100ta mashq."

BU TEST NIMANI ISBOTLAYDI:
  * 100 ta mashq, 20 daraja, har darajada 5 tadan;
  * Jahongirning ikki namunasi AYNAN 10 va 11-darajada;
  * har javob MATNDA haqiqatan bor (ONE WORD from the passage);
  * har javobdan keyin PARAFFRAZ ko'rsatiladi;
  * Unit 1 dagi 13 juftlikning hammasi qamrab olingan;
  * javob va paraffraz mashq boshida mijozga YUBORILMAYDI;
  * javob registr va tinish belgisiga qarab rad etilmaydi;
  * matn darajaga qarab uzayadi (oson -> qiyin).
"""
import os, sys, json, collections, re

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_tbl/db.sqlite"
os.makedirs("/tmp/verify_tbl", exist_ok=True)
if os.path.exists("/tmp/verify_tbl/db.sqlite"):
    os.remove("/tmp/verify_tbl/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
import reading_table_seed as RT

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
H = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "stud", "password": "Parol123!"}
).json()["access_token"]}

K = "read_table"
rows = RT.build_rows()

print("=== 1. SONI VA DARAJALAR ===")
ck("100 ta mashq", len(rows), 100)
per = collections.Counter(p[2]["step"] for p in rows)
ck("20 ta daraja", len(per), 20)
ck("har darajada 5 tadan",
   all(v == 5 for v in per.values()), True)
ck("darajalar 1..20", sorted(per), list(range(1, 21)))
ck("20 ta matn", len(RT.PASSAGES), 20)

print("\n=== 2. JAHONGIRNING NAMUNALARI 10 VA 11-DARAJADA ===")
byl = {p["level"]: p for p in RT.PASSAGES}
ck("10-daraja = THE WORLD'S FRIENDLIEST CITY",
   byl[10]["title"], "THE WORLD'S FRIENDLIEST CITY")
ck("11-daraja = THE BEST CITIES IN THE WORLD",
   byl[11]["title"], "THE BEST CITIES IN THE WORLD")
# 10-darajadagi besh javob rasmdagi bilan bir xil
ck("10-darajaning javoblari",
   [g[1] for g in byl[10]["gaps"]],
   ["relaxed", "money", "crime", "time", "strangers"])
ck("11-darajaning javoblari",
   [g[1] for g in byl[11]["gaps"]],
   ["business", "expensive", "friendliest", "climate", "traffic"])

print("\n=== 3. HAR JAVOB MATNDA HAQIQATAN BOR ===")
miss = []
for _k, _l, pl, ans, _e, _a, _p in rows:
    t = pl["passage"].lower().replace(",", "").replace("-", " ")
    a = ans.lower().replace(",", "").replace("-", " ")
    if a not in t and a.rstrip("s") not in t:
        miss.append((pl["step"], pl["gap_no"], ans))
ck("matnda yo'q javob yo'q", miss, [])
ck("har savolda bo'shliq belgisi bor",
   all(RT.GAP in p[2]["prompt"] for p in rows), True)

print("\n=== 4. PARAFFRAZ HAR MASHQDA BOR ===")
ck("hammasida paraffraz juftligi bor",
   all(p[6].get("table") and p[6].get("passage") for p in rows), True)
ck("izohda ikkala tomon ham ko'rinadi",
   all("Jadvalda:" in p[4] and "Matnda:" in p[4] for p in rows), True)
ck("izoh bo'sh emas",
   all(len(p[4]) > 40 for p in rows), True)

print("\n=== 5. UNIT 1 JUFTLIKLARI QAMRAB OLINGAN ===")
UNIT1 = ["famous", "well-known", "inhabitants", "populations",
         "lifestyle", "way of life", "have less", "known for",
         "have little", "be short of", "ignore", "excellent",
         "very good", "extremely", "residents",
         "standard of living", "nicest", "very few"]
blob = " ".join((p[4] + " " + p[6]["table"] + " " + p[6]["passage"])
                for p in rows).lower()
for w in UNIT1:
    ck(f"«{w}» ishlatilgan", w.lower() in blob, True)

print("\n=== 6. QIYINLIK HAQIQATAN O'SADI ===")
easy = [p for p in RT.PASSAGES if p["level"] <= 5]
hard = [p for p in RT.PASSAGES if p["level"] >= 16]
a_easy = sum(len(p["text"]) for p in easy) / len(easy)
a_hard = sum(len(p["text"]) for p in hard) / len(hard)
ck("qiyin matnlar 2x uzunroq", a_hard > a_easy * 2, True)
print(f"    1-5 daraja ~{int(a_easy)} belgi, 16-20 ~{int(a_hard)} belgi")
ck("namunadan oldingilar undan qisqa",
   sum(len(p["text"]) for p in easy) / len(easy)
   < len(byl[10]["text"]), True)

print("\n=== 7. BO'LIM RO'YXATIDA OCHIQ ===")
r = c.get("/api/student/ielts/reading/parts", headers=H)
ck("parts 200", r.status_code, 200)
parts = {p["title"]: p for p in r.json()["parts"]}
ck("Table Completion tayyor", parts["Table Completion"]["ready"], True)
ck("100 ta element", parts["Table Completion"]["total"], 100)
# 2026-08-25: Summary Completion ham qo'shildi -> to'rtta tayyor
ck("endi 4 ta tur to'ldirilgan",
   sum(1 for p in r.json()["parts"] if p["ready"]), 4)

print("\n=== 8. QOIDALAR PARAFFRAZNI O'RGATADI ===")
r = c.get(f"/api/student/ielts/reading/tips?kind={K}", headers=H)
ck("tips 200", r.status_code, 200)
t = r.json()
ck("6+ qoida", len(t["tips"]) >= 6, True)
ck("20 bosqich", len(t["steps"]), 20)
tips_blob = " ".join(x["title"] + x["body"] for x in t["tips"]).lower()
ck("qoidalarda paraffraz o'rgatiladi", "paraffraz" in tips_blob, True)
ck("Unit 1 juftliklari qoidada ham bor",
   "be short of" in tips_blob, True)

print("\n=== 9. JAVOB MASHQ BOSHIDA YUBORILMAYDI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={K}&count=10",
          headers=H)
ck("round 200", r.status_code, 200)
items = r.json()["items"]
raw = json.dumps(items, ensure_ascii=False)
ck("javob maydoni yo'q", all("answer" not in i for i in items), True)
ck("paraffraz ham yuborilmaydi",
   all("paraphrase" not in i for i in items), True)
ck("izoh ham yuborilmaydi",
   all("explain" not in i for i in items), True)
ck("variant yo'q (yozma tur)",
   all(not i.get("options") for i in items), True)
ck("jadval keladi", all(i.get("headers") and i.get("rows")
                        for i in items), True)
ck("bosqichlar o'sib boradi",
   [i["step"] for i in items] == sorted(i["step"] for i in items), True)
ck("birinchisi 1-daraja", items[0]["step"], 1)
ck("ko'rsatma bor", bool(items[0].get("instruction")), True)

print("\n=== 10. JADVALDA FAQAT BITTA BO'SHLIQ OCHIQ ===")
bad = []
for i in items:
    flat = " | ".join(" ".join(r) for r in i["rows"])
    if i.get("in_table") and flat.count(RT.GAP) != 1:
        bad.append((i["step"], i["gap_no"], flat.count(RT.GAP)))
ck("boshqa javoblar yopilgan", bad, [])

print("\n=== 11. TEKSHIRUV SERVERDA VA KECHIRIMLI ===")
first = items[0]
row = db.query(models.PracticeItem).get(int(first["ref"].split(":")[1]))
right = row.answer
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": "qwerty"},
           headers=H).json()
ck("xato javob -> False", r["correct"], False)
ck("to'g'risi ko'rsatiladi", r["expected"], right)
ck("PARAFFRAZ javob bilan keladi", bool(r.get("paraphrase")), True)
ck("paraffrazda jadval tomoni bor",
   bool(r["paraphrase"].get("table")), True)
ck("paraffrazda matn tomoni bor",
   bool(r["paraphrase"].get("passage")), True)
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"],
                 "answer": f"  {right.upper()} . "}, headers=H).json()
ck("katta harf va nuqta ham qabul qilinadi", r["correct"], True)

print("\n=== 12. RAQAM SO'Z BILAN HAM, RAQAM BILAN HAM ===")
# 40,000 kabi javoblarda vergul e'tiborsiz
tgt = [p for p in rows if p[3] == "40,000"]
ck("40,000 li mashq bor", len(tgt), 1)
it = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.skill == RT.SKILL,
              models.PracticeItem.answer == "40,000").first())
rr = c.post("/api/student/ielts/reading/answer",
            json={"ref": f"pi:{it.id}", "answer": "40000"},
            headers=H).json()
ck("vergulsiz yozilsa ham to'g'ri", rr["correct"], True)
it2 = (db.query(models.PracticeItem)
       .filter(models.PracticeItem.skill == RT.SKILL,
               models.PracticeItem.answer == "nine").first())
rr = c.post("/api/student/ielts/reading/answer",
            json={"ref": f"pi:{it2.id}", "answer": "9"},
            headers=H).json()
ck("«nine» o'rniga «9» ham to'g'ri", rr["correct"], True)

print("\n=== 13. TFNG/YNNG BUZILMADI ===")
for k in ("read_tfng", "read_ynng"):
    rr = c.get(f"/api/student/ielts/reading/round?kind={k}&count=5",
               headers=H)
    ck(f"{k} ishlaydi", rr.status_code, 200)
    ck(f"{k} da variantlar bor",
       all(len(i["options"]) == 3 for i in rr.json()["items"]), True)

print("\n=== 14. SEED IDEMPOTENT ===")
n1 = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.kind == K).count())
RT.seed_reading_table(db)
n2 = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.kind == K).count())
ck("qayta seed dublikat yaratmaydi", n2, n1)
ck("bazada 100 ta", n1, 100)

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
