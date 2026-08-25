"""IELTS READING — MATCHING HEADINGS (2026-08-25).

Jahongir: "Bu Paragraph heading savol turi bu misollarni 25-ga qoy
undan oldingilarni osonroq qil bilasanku osondan boshlab qiyinga
qarab ketasan."

BU TEST NIMANI ISBOTLAYDI:
  * 120 dan ortiq xatboshi, 28 daraja;
  * Traffic Jams va Pedestrians only AYNAN 25-darajada, javoblari
    kitobdagi kalit bilan bir xil;
  * 1-24 daraja namunadan osonroq, 26-28 qiyinroq;
  * har matnda ORTIQCHA sarlavha bor (hammasi ishlatilmaydi);
  * bitta sarlavha ikki xatboshiga berilmaydi;
  * javob variantlar ichida, javobning o'zi mijozga yuborilmaydi.
"""
import os, sys, collections

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_head/db.sqlite"
os.makedirs("/tmp/verify_head", exist_ok=True)
if os.path.exists("/tmp/verify_head/db.sqlite"):
    os.remove("/tmp/verify_head/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
import reading_head_seed as RH

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
tb = models.Branch(name="Test filial"); db.add(tb); db.commit()
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

K = "read_head"
rows = RH.build_rows()

print("=== 1. SONI VA DARAJALAR ===")
ck("120 dan ko'p", len(rows) >= 120, True)
print(f"    jami: {len(rows)} ta xatboshi, {len(RH.PASSAGES)} ta matn")
per = collections.Counter(p[2]["step"] for p in rows)
ck("28 daraja", len(per), 28)
ck("darajalar 1..28", sorted(per), list(range(1, 29)))

print("\n=== 2. NAMUNALAR AYNAN 25-DARAJADA ===")
p25 = [p for p in RH.PASSAGES if p["level"] == 25]
ck("25-darajada ikki matn", len(p25), 2)
titles = " | ".join(p["title"] for p in p25)
ck("Traffic Jams bor", "TRAFFIC JAMS" in titles, True)
ck("Pedestrians only bor", "PEDESTRIANS ONLY" in titles, True)
tj = [p for p in p25 if "TRAFFIC" in p["title"]][0]
po = [p for p in p25 if "PEDESTRIANS" in p["title"]][0]
ck("Traffic Jams javoblari (A-E)",
   [tj["headings"][g[1]] for g in tj["gaps"]],
   ["A global problem", "Paying to get in",
    "Changing working practices", "A solution which is no solution",
    "Not doing enough"])
ck("Pedestrians javoblari (A-E)",
   [po["headings"][g[1]] for g in po["gaps"]],
   ["An idea from ancient history", "A need for change",
    "Facing local opposition", "Some reasons for success",
    "Winners and losers"])
ck("Traffic Jamsda 2 sarlavha ortiqcha",
   len(tj["headings"]) - len(tj["gaps"]), 2)
ck("Pedestriansda ham 2 ta ortiqcha",
   len(po["headings"]) - len(po["gaps"]), 2)

print("\n=== 3. OSONDAN QIYINGA ===")
def avg(lo, hi):
    ps = [p for p in RH.PASSAGES if lo <= p["level"] <= hi]
    return int(sum(len(" ".join(t for _l, t in p["paras"]))
                   for p in ps) / len(ps))
a1, a2, a3, a4 = avg(1, 8), avg(9, 16), avg(17, 24), avg(26, 28)
print(f"    1-8 ~{a1}, 9-16 ~{a2}, 17-24 ~{a3}, 26-28 ~{a4} belgi")
ck("9-16 > 1-8", a2 > a1, True)
ck("17-24 > 9-16", a3 > a2, True)
ck("26-28 eng uzun", a4 > a3, True)
ck("1-8 da 3 tadan xatboshi",
   all(len(p["gaps"]) == 3 for p in RH.PASSAGES if p["level"] <= 8),
   True)
ck("17+ da 5 tadan xatboshi",
   all(len(p["gaps"]) == 5 for p in RH.PASSAGES
       if p["level"] >= 17), True)

print("\n=== 4. SARLAVHALAR TO'G'RI TUZILGAN ===")
bad = []
for p in RH.PASSAGES:
    used = [g[1] for g in p["gaps"]]
    if len(set(used)) != len(used):
        bad.append((p["level"], "bitta sarlavha ikki marta"))
    if len(p["headings"]) <= len(p["gaps"]):
        bad.append((p["level"], "ortiqcha sarlavha yo'q"))
    letters = [g[0] for g in p["gaps"]]
    if letters != sorted(letters):
        bad.append((p["level"], "xatboshi tartibi"))
ck("tuzilish xatosi yo'q", bad, [])
ck("kalit jumla har xatboshida bor",
   [(p["level"], g[0]) for p in RH.PASSAGES for g in p["gaps"]
    if g[2][:35] not in dict(p["paras"])[g[0]]], [])
ck("javob doim variantlar ichida",
   all(p[3] in p[2]["options"] for p in rows), True)

print("\n=== 5. BO'LIM RO'YXATIDA ===")
r = c.get("/api/student/ielts/reading/parts", headers=H)
parts = {p["title"]: p for p in r.json()["parts"]}
ck("Matching Headings tayyor",
   parts["Matching Headings"]["ready"], True)
ck("elementlar", parts["Matching Headings"]["total"], len(rows))
ck("9 tur to'ldirilgan",
   sum(1 for p in r.json()["parts"] if p["ready"]), 9)

print("\n=== 6. QOIDALAR ===")
t = c.get(f"/api/student/ielts/reading/tips?kind={K}",
          headers=H).json()
ck("6+ qoida", len(t["tips"]) >= 6, True)
ck("28 bosqich", len(t["steps"]), 28)
tb_ = " ".join(x["title"] + x["body"] for x in t["tips"]).lower()
ck("asosiy g'oya qoidasi bor", "asosiy g'oya" in tb_, True)
ck("bir xil so'z qopqoni o'rgatiladi", "qopqon" in tb_, True)

print("\n=== 7. JAVOB OSHKOR BO'LMAYDI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={K}&count=10",
          headers=H)
items = r.json()["items"]
ck("round 200", r.status_code, 200)
ck("javob yo'q", all("answer" not in i for i in items), True)
ck("izoh yo'q", all("explain" not in i for i in items), True)
ck("xatboshilar keladi",
   all(i.get("paragraphs") for i in items), True)
ck("qaysi xatboshi so'ralayotgani ham",
   all(i.get("para") for i in items), True)
ck("sarlavhalar variant sifatida",
   all(len(i["options"]) >= 5 for i in items), True)
ck("prompt xatboshi harfini ko'rsatadi",
   all(i["prompt"] == f"Paragraph {i['para']}" for i in items), True)
ck("bosqich o'sadi",
   [i["step"] for i in items] == sorted(i["step"] for i in items), True)

print("\n=== 8. TEKSHIRUV ===")
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

print("\n=== 9. TEST FILIALIDA IELTS BO'LIMI OCHIQ ===")
# Jahongir iPhone'dan tekshirishi uchun (yangi ball shkalasida
# hech kim Upper-Intermediate emas)
db2 = SessionLocal()
st2 = models.Student(full_name="Sinov", branch_id=tb.id,
                     status="active")
db2.add(st2); db2.commit()
u2 = models.User(username="sinov", full_name="Sinov",
                 password_hash=hash_password("Parol123!"),
                 role=roles.STUDENT, branch_id=tb.id, is_active=1)
db2.add(u2); db2.commit()
st2.user_id = u2.id; db2.commit(); db2.close()
H2 = {"Authorization": "Bearer " + c.post(
    "/api/auth/login",
    json={"username": "sinov", "password": "Parol123!"}
).json()["access_token"]}
g1 = (c.get("/api/student/learn", headers=H).json() or {}).get("ielts")
g2 = (c.get("/api/student/learn", headers=H2).json() or {}).get("ielts")
ck("oddiy filialda hali qulflangan", g1["unlocked"], False)
ck("TEST filialida ochiq", g2["unlocked"], True)
ck("test filial belgisi qaytadi", g2["test_branch"], True)

print("\n=== 10. BOSHQA TURLAR BUZILMADI ===")
for k in ("read_tfng", "read_ynng", "read_table", "read_summary",
          "read_flow", "read_short", "read_label"):
    rr = c.get(f"/api/student/ielts/reading/round?kind={k}&count=3",
               headers=H)
    ck(f"{k} ishlaydi", rr.status_code, 200)

print("\n=== 11. SEED IDEMPOTENT ===")
n1 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
RH.seed_reading_head(db)
n2 = db.query(models.PracticeItem).filter(
    models.PracticeItem.kind == K).count()
ck("dublikat yaratmaydi", n2, n1)
ck("bazada build_rows bilan bir xil", n1, len(rows))

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
