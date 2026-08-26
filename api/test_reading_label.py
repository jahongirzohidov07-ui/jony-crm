"""IELTS READING — LABELLING A DIAGRAM (2026-08-25).

Jahongir: "bu diagram labelling savol turigan bularni samalyotni
15ga, elektric revolutionni 10tga qoysang qolganini osondan qiyinga
qarab ketaveradigan qilasang."

BU TEST NIMANI ISBOTLAYDI:
  * 100 dan ortiq yorliq, 20 daraja;
  * elektromobil AYNAN 10-darajada, Boeing 787 AYNAN 15-darajada;
  * javoblar rasmdagi bilan bir xil;
  * matn uzunligi 1 -> 20 gacha o'sib boradi;
  * har javob matnda alohida so'z sifatida bor, 2 so'zdan oshmaydi;
  * chizmada bir vaqtda faqat bitta yorliq ochiq turadi;
  * javob/paraffraz mashq boshida yuborilmaydi.
"""
import os, sys, re, collections

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_label/db.sqlite"
os.makedirs("/tmp/verify_label", exist_ok=True)
if os.path.exists("/tmp/verify_label/db.sqlite"):
    os.remove("/tmp/verify_label/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
import reading_label_seed as RL

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

K = "read_label"
rows = RL.build_rows()
ART = {"a", "an", "the", "his", "her", "their", "its"}


def core(t):
    return [w for w in re.findall(r"[a-z0-9.,'-]+", t.lower())
            if w not in ART]


def words(t):
    return " " + " ".join(re.findall(r"[a-z0-9]+", t.lower())) + " "


print("=== 1. SONI VA DARAJALAR ===")
ck("100 dan ko'p", len(rows) >= 100, True)
print(f"    jami: {len(rows)} ta yorliq")
per = collections.Counter(p[2]["step"] for p in rows)
ck("20 daraja", len(per), 20)
ck("darajalar 1..20", sorted(per), list(range(1, 21)))
ck("20 ta chizma", len(RL.PASSAGES), 20)

print("\n=== 2. NAMUNALAR AYNAN 10 VA 15-DARAJADA ===")
byl = {p["level"]: p for p in RL.PASSAGES}
ck("10-daraja — electric revolution",
   "ELECTRIC REVOLUTION" in byl[10]["title"], True)
ck("15-daraja — Boeing 787", "BOEING 787" in byl[15]["title"], True)
ck("elektromobil chizmasi nomi", byl[10]["figure"], "An electric car")
ck("elektromobil javoblari",
   [g[1] for g in byl[10]["gaps"]],
   ["electricity grid", "160 km", "work", "price",
    "navigation system", "robot"])
ck("Boeing javoblari",
   [g[1] for g in byl[15]["gaps"]],
   ["lighter", "fuel", "210 passengers", "shorter time", "noise",
    "65 percent", "electric current"])
ck("Boeingda 7 ta yorliq", len(byl[15]["gaps"]), 7)

print("\n=== 3. OSONDAN QIYINGA ===")
grp = {}
for p in RL.PASSAGES:
    band = ("1-9" if p["level"] <= 9 else
            "10-14" if p["level"] <= 14 else "15-20")
    grp.setdefault(band, []).append(len(p["text"]))
avg = {k: int(sum(v) / len(v)) for k, v in grp.items()}
print(f"    o'rtacha uzunlik: {avg}")
ck("10-14 > 1-9", avg["10-14"] > avg["1-9"], True)
ck("15-20 > 10-14", avg["15-20"] > avg["10-14"], True)
ck("eng qiyini eng osonidan 2x uzun",
   avg["15-20"] > avg["1-9"] * 2, True)

print("\n=== 4. JAVOBLAR MATNDA VA QISQA ===")
miss = [(p[2]["step"], p[2]["gap_no"], p[3]) for p in rows
        if words(p[3]).strip() not in words(p[2]["passage"])]
ck("hammasi matnda bor", miss, [])
longs = [(p[2]["step"], p[3]) for p in rows if len(core(p[3])) > 2]
ck("2 so'zdan oshmaydi", longs, [])
lost = []
for p in RL.PASSAGES:
    for g in p["gaps"]:
        if p["text"].find(g[3][:40]) < 0:
            lost.append((p["level"], g[0]))
ck("manba jumlalari matnda topiladi", lost, [])

print("\n=== 5. PARAFFRAZ ===")
ck("juftlik bor",
   all(p[6].get("table") and p[6].get("passage") for p in rows), True)
ck("izohda ikki tomon",
   all("Yorliqda:" in p[4] and "Matnda:" in p[4] for p in rows), True)

print("\n=== 6. BO'LIM RO'YXATIDA ===")
r = c.get("/api/student/ielts/reading/parts", headers=H)
parts = {p["title"]: p for p in r.json()["parts"]}
ck("Labelling a Diagram tayyor",
   parts["Labelling a Diagram"]["ready"], True)
ck("elementlar", parts["Labelling a Diagram"]["total"], len(rows))
ck("11 tur to'ldirilgan",
   sum(1 for p in r.json()["parts"] if p["ready"]), 11)

print("\n=== 7. QOIDALAR ===")
t = c.get(f"/api/student/ielts/reading/tips?kind={K}",
          headers=H).json()
ck("6+ qoida", len(t["tips"]) >= 6, True)
ck("20 bosqich", len(t["steps"]), 20)
tb = " ".join(x["title"] + x["body"] for x in t["tips"]).lower()
ck("«qism» qoidasi bor", "qism" in tb, True)
ck("tartibga ishonmaslik o'rgatiladi",
   "tartibga ishonmang" in tb or "tartib" in tb, True)

print("\n=== 8. JAVOB OSHKOR BO'LMAYDI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={K}&count=10",
          headers=H)
items = r.json()["items"]
ck("round 200", r.status_code, 200)
ck("javob yo'q", all("answer" not in i for i in items), True)
ck("paraffraz yo'q", all("paraphrase" not in i for i in items), True)
ck("chizma nomi keladi", all(i.get("figure") for i in items), True)
ck("yorliqlar keladi", all(i.get("labels") for i in items), True)
ck("bosqich o'sadi",
   [i["step"] for i in items] == sorted(i["step"] for i in items), True)
bad = [i["step"] for i in items
       if sum(x.count("______") for x in i["labels"]) != 1]
ck("faqat bitta yorliq ochiq", bad, [])

print("\n=== 9. TEKSHIRUV VA MUQOBILLAR ===")
first = items[0]
row = db.query(models.PracticeItem).get(int(first["ref"].split(":")[1]))
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": "zzz"},
           headers=H).json()
ck("xato -> False", r["correct"], False)
ck("paraffraz keladi", bool(r.get("paraphrase")), True)
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"],
                 "answer": f" THE {row.answer.upper()} "},
           headers=H).json()
ck("artikl va registr e'tiborsiz", r["correct"], True)
for ans, alt in (("160 km", "160 kilometres"),
                 ("recovery device", "energy recovery device"),
                 ("ten minutes", "10 minutes")):
    it = (db.query(models.PracticeItem)
          .filter(models.PracticeItem.kind == K,
                  models.PracticeItem.answer == ans).first())
    rr = c.post("/api/student/ielts/reading/answer",
                json={"ref": f"pi:{it.id}", "answer": alt},
                headers=H).json()
    ck(f"«{ans}» o'rniga «{alt}»", rr["correct"], True)

print("\n=== 10. BOSHQA TURLAR BUZILMADI ===")
for k in ("read_tfng", "read_ynng", "read_table", "read_summary",
          "read_flow", "read_short"):
    rr = c.get(f"/api/student/ielts/reading/round?kind={k}&count=3",
               headers=H)
    ck(f"{k} ishlaydi", rr.status_code, 200)

print("\n=== 11. SEED IDEMPOTENT ===")
n1 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
RL.seed_reading_label(db)
n2 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
ck("dublikat yaratmaydi", n2, n1)
ck("bazada build_rows bilan bir xil", n1, len(rows))

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
