"""IELTS READING — MULTIPLE CHOICE A/B/C/D (2026-08-25).

Jahongir: "mana bular Multiple choice savollari aynan Reading
Part 3 uchun shunaqa boladi butun bir paragraphga savol beradu
shunaqadan osondan boshlab qiyinga qarab ketganingda buni 20-25
orasiga qoyvorasan."

BU TEST NIMANI ISBOTLAYDI:
  * 122 savol, 26 daraja;
  * ikki namuna 20-25 oralig'ida (ballpoint 21, air conditioning 24)
    va javoblari kitobdagi kalit bilan bir xil;
  * namunalarda variantlar tartibi kitobdagidek QOLDIRILGAN;
  * qolganlarida to'g'ri javob A/B/C/D bo'yicha TENG taqsimlangan —
    "hamma vaqt B" hiylasi ishlamaydi;
  * har savolda aynan 4 ta noyob variant;
  * har javobning matndagi asosi bor;
  * javob mashq boshida yuborilmaydi.
"""
import os, sys, collections

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_mcq/db.sqlite"
os.makedirs("/tmp/verify_mcq", exist_ok=True)
if os.path.exists("/tmp/verify_mcq/db.sqlite"):
    os.remove("/tmp/verify_mcq/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
import reading_mcq_seed as RM

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

K = "read_mcq"
rows = RM.build_rows()


def letter(r):
    return "ABCD"[r[2]["options"].index(r[3])]


print("=== 1. SONI VA DARAJALAR ===")
ck("122 savol", len(rows), 122)
per = collections.Counter(p[2]["step"] for p in rows)
ck("26 daraja", len(per), 26)
ck("darajalar 1..26", sorted(per), list(range(1, 27)))
ck("26 ta matn", len(RM.PASSAGES), 26)
ck("1-8 da 4 savoldan",
   all(len(p["qs"]) == 4 for p in RM.PASSAGES if p["level"] <= 8),
   True)
ck("9+ da 5 savoldan",
   all(len(p["qs"]) == 5 for p in RM.PASSAGES if p["level"] >= 9),
   True)

print("\n=== 2. NAMUNALAR 20-25 ORALIG'IDA ===")
byl = {p["level"]: p for p in RM.PASSAGES}
ck("21-daraja — ballpoint pen",
   "BALLPOINT PEN" in byl[21]["title"], True)
ck("24-daraja — air conditioning",
   "AIR CONDITIONING" in byl[24]["title"], True)
ck("ikkalasi ham 20-25 orasida",
   all(20 <= lv <= 25 for lv in (21, 24)), True)
b21 = [letter(r) for r in rows if r[2]["step"] == 21]
b24 = [letter(r) for r in rows if r[2]["step"] == 24]
ck("ballpoint javoblari kitobdagidek (B D C B A)",
   b21, ["B", "D", "C", "B", "A"])
ck("air conditioning javoblari (D A D C D)",
   b24, ["D", "A", "D", "C", "D"])

print("\n=== 3. «HAMMA VAQT B» HIYLASI ISHLAMAYDI ===")
dist = collections.Counter(letter(r) for r in rows)
print(f"    taqsimot: {dict(sorted(dist.items()))}")
for L in "ABCD":
    ck(f"«{L}» ulushi 20-30%",
       0.20 <= dist[L] / len(rows) <= 0.30, True)

print("\n=== 4. VARIANTLAR TO'G'RI TUZILGAN ===")
bad = []
for k, l, pl, a, e, al, pa in rows:
    if len(pl["options"]) != 4:
        bad.append((pl["step"], "4 ta emas"))
    if len(set(pl["options"])) != 4:
        bad.append((pl["step"], "dublikat variant"))
    if a not in pl["options"]:
        bad.append((pl["step"], "javob variantda yo'q"))
    if not pl["options"][0].startswith("A."):
        bad.append((pl["step"], "harf yo'q"))
ck("variant xatosi yo'q", bad, [])
lost = [(p["level"], q[:30]) for p in RM.PASSAGES
        for q, o, ci, key, note in p["qs"]
        if key[:35] not in p["text"]]
ck("har javobning matnda asosi bor", lost, [])

print("\n=== 5. IZOHDA NOTO'G'RI VARIANTLAR TUSHUNTIRILADI ===")
n_trap = sum(1 for r in rows if "QOPQON" in r[4])
ck("kamida 20 ta izohda qopqon tushuntirilgan", n_trap >= 20, True)
n_wrong = sum(1 for r in rows
              if any(x in r[4] for x in ("QOPQON", "aytilmagan",
                                         "matnga zid", "rad etadi",
                                         "Chalg'ituvchi")))
ck("yarmidan ko'pida noto'g'ri variant tushuntirilgan",
   n_wrong > len(rows) / 2, True)
print(f"    qopqon izohi: {n_trap} ta")
ck("hamma izohda matn asosi bor",
   all("Matnda:" in r[4] for r in rows), True)

print("\n=== 6. QIYINLIK O'SADI ===")
def avg(lo, hi):
    ps = [p for p in RM.PASSAGES if lo <= p["level"] <= hi]
    return int(sum(len(p["text"]) for p in ps) / len(ps))
a1, a2, a3 = avg(1, 8), avg(9, 16), avg(17, 26)
print(f"    1-8 ~{a1}, 9-16 ~{a2}, 17-26 ~{a3} belgi")
ck("9-16 > 1-8", a2 > a1, True)
ck("17-26 > 9-16", a3 > a2, True)

print("\n=== 7. BO'LIM RO'YXATIDA ===")
r = c.get("/api/student/ielts/reading/parts", headers=H)
parts = {p["title"]: p for p in r.json()["parts"]}
ck("Multiple Choice tayyor", parts["Multiple Choice"]["ready"], True)
ck("elementlar", parts["Multiple Choice"]["total"], 122)
ck("10 tur to'ldirilgan",
   sum(1 for p in r.json()["parts"] if p["ready"]), 10)

print("\n=== 8. QOIDALAR ===")
t = c.get(f"/api/student/ielts/reading/tips?kind={K}",
          headers=H).json()
ck("6+ qoida", len(t["tips"]) >= 6, True)
ck("26 bosqich", len(t["steps"]), 26)
tb = " ".join(x["title"] + x["body"] for x in t["tips"]).lower()
ck("«avval savolni o'qing» qoidasi bor",
   "avval savolni" in tb, True)
ck("noto'g'ri variantlarni chiqarish o'rgatiladi",
   "chiqarib tashlang" in tb, True)

print("\n=== 9. JAVOB OSHKOR BO'LMAYDI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={K}&count=10",
          headers=H)
items = r.json()["items"]
ck("round 200", r.status_code, 200)
ck("javob yo'q", all("answer" not in i for i in items), True)
ck("izoh yo'q", all("explain" not in i for i in items), True)
ck("4 ta variant keladi",
   all(len(i["options"]) == 4 for i in items), True)
ck("savol matni keladi", all(i.get("prompt") for i in items), True)
ck("savollar ro'yxati YUBORILMAYDI",
   all(not i.get("questions") for i in items), True)
ck("bosqich o'sadi",
   [i["step"] for i in items] == sorted(i["step"] for i in items), True)
ck("ko'rsatmada A, B, C or D bor",
   "A, B, C or D" in items[0]["instruction"], True)

print("\n=== 10. TEKSHIRUV ===")
first = items[0]
row = db.query(models.PracticeItem).get(int(first["ref"].split(":")[1]))
wrong = [o for o in first["options"] if o != row.answer][0]
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": wrong},
           headers=H).json()
ck("xato -> False", r["correct"], False)
ck("to'g'risi ko'rsatiladi", r["expected"], row.answer)
ck("izoh keladi", bool(r["explain"]), True)
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": row.answer},
           headers=H).json()
ck("to'g'ri javob qabul qilinadi", r["correct"], True)

print("\n=== 11. BOSHQA TURLAR BUZILMADI ===")
for k in ("read_tfng", "read_ynng", "read_table", "read_summary",
          "read_flow", "read_short", "read_label", "read_head"):
    rr = c.get(f"/api/student/ielts/reading/round?kind={k}&count=3",
               headers=H)
    ck(f"{k} ishlaydi", rr.status_code, 200)

print("\n=== 12. SEED IDEMPOTENT ===")
n1 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
RM.seed_reading_mcq(db)
n2 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
ck("dublikat yaratmaydi", n2, n1)
ck("bazada 122 ta", n1, 122)

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
