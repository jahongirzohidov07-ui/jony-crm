"""IELTS READING — SUMMARY / NOTE COMPLETION (2026-08-25).

Jahongir: "bu summary completion turi shunga ham 100ta mashq ber.
Butun textdan xulosani textdagi so'zlar bilan to'ldirish."

BU TEST NIMANI ISBOTLAYDI:
  * 100 dan ortiq mashq, 20 daraja, oson -> qiyin;
  * ikki namuna (READING #3 va #4) 10 va 11-darajada, javoblari
    rasmdagi bilan bir xil;
  * har javob MATNDA haqiqatan bor;
  * xulosa BUTUN matnni qamraydi — bo'shliqlar matnning turli
    joylaridan olingan va matn tartibi bilan boradi;
  * har javobdan keyin PARAFFRAZ ko'rsatiladi;
  * javob/paraffraz mashq boshida mijozga yuborilmaydi;
  * xulosada bir vaqtda faqat bitta bo'shliq ochiq turadi.
"""
import os, sys, json, collections

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_sum/db.sqlite"
os.makedirs("/tmp/verify_sum", exist_ok=True)
if os.path.exists("/tmp/verify_sum/db.sqlite"):
    os.remove("/tmp/verify_sum/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
import reading_summary_seed as RS

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

K = "read_summary"
rows = RS.build_rows()

print("=== 1. SONI VA DARAJALAR ===")
ck("100 dan ko'p mashq", len(rows) >= 100, True)
print(f"    jami: {len(rows)} ta")
per = collections.Counter(p[2]["step"] for p in rows)
ck("20 ta daraja", len(per), 20)
ck("darajalar 1..20", sorted(per), list(range(1, 21)))
ck("har darajada kamida 4 ta",
   all(v >= 4 for v in per.values()), True)
ck("20 ta matn", len(RS.PASSAGES), 20)

print("\n=== 2. NAMUNALAR 10 VA 11-DARAJADA ===")
byl = {p["level"]: p for p in RS.PASSAGES}
ck("10-daraja — happiest country",
   "HAPPIEST COUNTRY" in byl[10]["title"], True)
ck("11-daraja — city survey",
   "CITY SURVEY" in byl[11]["title"], True)
ck("READING #3 javoblari rasmdagidek",
   [g[1] for g in byl[10]["gaps"]],
   ["2008", "143", "environment", "resources", "health", "citizens"])
ck("READING #4 javoblari rasmdagidek",
   [g[1] for g in byl[11]["gaps"]],
   ["products", "year", "50", "categories", "live", "holiday",
    "governments"])

print("\n=== 3. HAR JAVOB MATNDA BOR ===")
miss = []
for _k, _l, pl, ans, _e, _a, _p in rows:
    t = pl["passage"].lower().replace(",", "").replace("-", " ")
    a = ans.lower().replace(",", "").replace("-", " ")
    if a not in t and a.rstrip("s") not in t:
        miss.append((pl["step"], pl["gap_no"], ans))
ck("matnda yo'q javob yo'q", miss, [])

print("\n=== 4. XULOSA BUTUN MATNNI QAMRAYDI ===")
# Har matnda javoblar matn bo'ylab TARQOQ joylashgan bo'lishi kerak
narrow = []
for p in RS.PASSAGES:
    pos = []
    for _n, _a, _c, psg, _note in p["gaps"]:
        pos.append(p["text"].find(psg[:40]))
    span = (max(pos) - min(pos)) / max(1, len(p["text"]))
    if span < 0.45:            # javoblar matnning yarmidan kamiga tiqilgan
        narrow.append((p["level"], round(span, 2)))
ck("javoblar matn bo'ylab tarqoq", narrow, [])
# Har bo'shliqning manba jumlasi matnda TOPILADI
lost = []
for p in RS.PASSAGES:
    for g in p["gaps"]:
        if p["text"].find(g[3][:40]) < 0:
            lost.append((p["level"], g[0]))
ck("har bo'shliqning manba jumlasi matnda topiladi", lost, [])
# Tartib: uzluksiz xulosalar matn ketma-ketligini kuzatadi, lekin
# QAYDNOMA (note) turida tartib buzilishi mumkin — Jahongir yuborgan
# Happy Planet Index qaydnomasi aynan shunday. Shuning uchun
# "ko'pchiligi tartibda" deb tekshiramiz.
pairs_ok = pairs_all = 0
for p in RS.PASSAGES:
    pos = [p["text"].find(g[3][:40]) for g in p["gaps"]]
    for a, bb in zip(pos, pos[1:]):
        pairs_all += 1
        if a <= bb:
            pairs_ok += 1
share = pairs_ok / max(1, pairs_all)
ck(f"bo'shliqlarning ko'pi matn tartibida ({pairs_ok}/{pairs_all})",
   share >= 0.75, True)
# Bitta jumladan ikki javob olinmagan
dup = []
for p in RS.PASSAGES:
    src = [g[3][:40] for g in p["gaps"]]
    if len(set(src)) != len(src):
        dup.append(p["level"])
ck("bir jumladan ikki javob olinmagan", dup, [])

print("\n=== 5. PARAFFRAZ HAR MASHQDA ===")
ck("juftlik bor",
   all(p[6].get("table") and p[6].get("passage") for p in rows), True)
ck("izohda ikkala tomon",
   all("Xulosada:" in p[4] and "Matnda:" in p[4] for p in rows), True)
blob = " ".join(p[4] for p in rows).lower()
for w in ("started = created", "lists = ranks", "effect = impact",
          "maximum = total", "like = similar to",
          "a number of = several", "get a job = find work",
          "local = regional"):
    ck(f"«{w}»", w in blob, True)

print("\n=== 6. QIYINLIK O'SADI ===")
easy = [p for p in RS.PASSAGES if p["level"] <= 5]
hard = [p for p in RS.PASSAGES if p["level"] >= 16]
a_e = sum(len(p["text"]) for p in easy) / len(easy)
a_h = sum(len(p["text"]) for p in hard) / len(hard)
ck("qiyin matnlar 2x uzunroq", a_h > a_e * 2, True)
print(f"    1-5 ~{int(a_e)} belgi, 16-20 ~{int(a_h)} belgi")

print("\n=== 7. BO'LIM OCHIQ ===")
r = c.get("/api/student/ielts/reading/parts", headers=H)
parts = {p["title"]: p for p in r.json()["parts"]}
ck("Summary Completion tayyor",
   parts["Summary Completion"]["ready"], True)
ck("elementlar soni", parts["Summary Completion"]["total"], len(rows))
# 2026-08-25: Flow-chart Completion ham qo'shildi -> beshta
ck("endi 8 ta tur to'ldirilgan",
   sum(1 for p in r.json()["parts"] if p["ready"]), 8)

print("\n=== 8. QOIDALAR ===")
t = c.get(f"/api/student/ielts/reading/tips?kind={K}",
          headers=H).json()
ck("6+ qoida", len(t["tips"]) >= 6, True)
ck("20 bosqich", len(t["steps"]), 20)
tb = " ".join(x["title"] + x["body"] for x in t["tips"]).lower()
ck("paraffraz o'rgatiladi", "paraffraz" in tb, True)
ck("jadvaldan farqi tushuntiriladi", "butun matn" in tb, True)

print("\n=== 9. JAVOB OSHKOR BO'LMAYDI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={K}&count=10",
          headers=H)
items = r.json()["items"]
ck("round 200", r.status_code, 200)
ck("javob yo'q", all("answer" not in i for i in items), True)
ck("paraffraz yo'q", all("paraphrase" not in i for i in items), True)
ck("izoh yo'q", all("explain" not in i for i in items), True)
ck("xulosa keladi", all(i.get("summary") for i in items), True)
ck("xulosa sarlavhasi ham",
   all(i.get("summary_title") for i in items), True)
ck("bosqich o'sib boradi",
   [i["step"] for i in items] == sorted(i["step"] for i in items), True)
bad = [i["step"] for i in items
       if sum(x.count("______") for x in i["summary"]) != 1]
ck("faqat bitta bo'shliq ochiq", bad, [])

print("\n=== 10. TEKSHIRUV SERVERDA ===")
first = items[0]
row = db.query(models.PracticeItem).get(int(first["ref"].split(":")[1]))
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": "zzz"},
           headers=H).json()
ck("xato -> False", r["correct"], False)
ck("to'g'risi ko'rsatiladi", r["expected"], row.answer)
ck("paraffraz keladi", bool(r.get("paraphrase")), True)
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"],
                 "answer": f" {row.answer.upper()} "},
           headers=H).json()
ck("registr e'tiborsiz", r["correct"], True)
it = (db.query(models.PracticeItem)
      .filter(models.PracticeItem.kind == K,
              models.PracticeItem.answer == "three").first())
rr = c.post("/api/student/ielts/reading/answer",
            json={"ref": f"pi:{it.id}", "answer": "3"},
            headers=H).json()
ck("«three» o'rniga «3» ham to'g'ri", rr["correct"], True)

print("\n=== 11. BOSHQA TURLAR BUZILMADI ===")
for k, opt in (("read_tfng", True), ("read_ynng", True),
               ("read_table", False)):
    rr = c.get(f"/api/student/ielts/reading/round?kind={k}&count=5",
               headers=H)
    ck(f"{k} ishlaydi", rr.status_code, 200)
    its = rr.json()["items"]
    ck(f"{k} variantlari",
       all(bool(i.get("options")) == opt for i in its), True)
ck("read_table jadvali joyida",
   all(i.get("rows") for i in c.get(
       "/api/student/ielts/reading/round?kind=read_table&count=3",
       headers=H).json()["items"]), True)

print("\n=== 12. SEED IDEMPOTENT ===")
n1 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
RS.seed_reading_summary(db)
n2 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
ck("dublikat yaratmaydi", n2, n1)
ck("bazada build_rows bilan bir xil", n1, len(rows))

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
