"""IELTS READING: TRUE/FALSE/NOT GIVEN va YES/NO/NOT GIVEN
(2026-08-25).

Jahongir: "mana bu reading uchun TRUE/FALSE/NOT GIVEN savollari va
javoblari, lekin bu yerda osondan qiyinga qarab qoyilmagan va tiplar
ham bor shuni true false ichiga tiplar bilan boshida orgatib
o'rganishga eng zor samarali qilib qoy agar kerak bolsa bundan ham
osonroqlarini tuzib kirish olish uchun boshlanishiga qoygin...
keyin amna oxirida question types hammasini toliq tashladim...
hozircha bo'limlar ochib qo'ysang bo'ladi".

BU TEST NIMANI ISBOTLAYDI:
  * 12 savol turining hammasi bo'lim bo'lib ochilgan;
  * TFNG va YNNG mashqlari OSONDAN QIYINGA saralab beriladi
    (1-bosqich birinchi, real imtihon savollari oxirida);
  * javob mijozga UMUMAN yuborilmaydi — tekshiruv faqat serverda;
  * har element o'z TIP yorlig'i va izohi bilan keladi;
  * kitob javob kaliti bilan mos (nuqtaviy tekshiruv).
"""
import os, sys, json, collections

os.environ["DATABASE_URL"] = "sqlite:////tmp/verify_read/db.sqlite"
os.makedirs("/tmp/verify_read", exist_ok=True)
if os.path.exists("/tmp/verify_read/db.sqlite"):
    os.remove("/tmp/verify_read/db.sqlite")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
import main, models, roles
import entry  # noqa: F401
from database import SessionLocal
from auth import hash_password
import reading_ielts_seed as RS

c = TestClient(main.app)
db = SessionLocal()
fails = []


def ck(n, g, w):
    ok = g == w
    print(("OK  " if ok else "XATO ") + f"{n}: {g}"
          + ("" if ok else f"   (kutilgan {w})"))
    if not ok:
        fails.append(n)


def ck_true(n, cond, extra=""):
    ck(n, bool(cond), True) if cond else ck(n + " " + extra, False, True)


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

TF, YN = "read_tfng", "read_ynng"

print("=== 1. 12 SAVOL TURI HAM BO'LIM BO'LIB OCHILGAN ===")
r = c.get("/api/student/ielts/reading/parts", headers=H)
ck("status 200", r.status_code, 200)
parts = r.json()["parts"]
# 2026-08-25: Flow-chart Completion 13-tur bo'lib qo'shildi
ck("13 ta savol turi", len(parts), 13)
titles = [p["title"] for p in parts]
for want in ("Short answer", "Multiple Choice", "Summary Completion",
             "Matching Sentences", "Sentence Completion",
             "True / False / Not Given", "Yes / No / Not Given",
             "Matching Headings", "Labelling a Diagram",
             "Matching Names",
             "Matching Information to Paragraphs",
             "Table Completion"):
    ck(f"ro'yxatda: {want}", want in titles, True)
ready = [p for p in parts if p["ready"]]
# 2026-08-25: Table + Summary Completion qo'shildi -> to'rtta tayyor
ck("hozircha 5 tasi to'ldirilgan", len(ready), 5)
ck("qolgan 8 tasi 'tez orada'",
   len([p for p in parts if not p["ready"]]), 8)
by_kind = {p["kind"]: p for p in parts if p["kind"]}

print("\n=== 2. MASHQLAR SONI ===")
ck("TFNG 140 dan ko'p", by_kind[TF]["total"] >= 140, True)
ck("YNNG 100 ta", by_kind[YN]["total"], 100)
tot = by_kind[TF]["total"] + by_kind[YN]["total"]
ck("jami 240 dan ko'p", tot >= 240, True)
print(f"    jami: {tot} ta savol")

print("\n=== 3. QOIDALAR (tips) MASHQDAN OLDIN BERILADI ===")
for kind, least in ((TF, 12), (YN, 6)):
    r = c.get(f"/api/student/ielts/reading/tips?kind={kind}",
              headers=H)
    ck(f"{kind} tips 200", r.status_code, 200)
    t = r.json()
    ck(f"{kind}: {least}+ qoida", len(t["tips"]) >= least, True)
    ck(f"{kind}: har qoidada matn bor",
       all(x["title"] and x["body"] for x in t["tips"]), True)
    ck(f"{kind}: 5 bosqich xaritasi", len(t["steps"]), 5)
    ck(f"{kind}: bosqichlar 1..5",
       [s["step"] for s in t["steps"]], [1, 2, 3, 4, 5])
r = c.get("/api/student/ielts/reading/tips?kind=yolq", headers=H)
ck("noma'lum tur -> 404", r.status_code, 404)

print("\n=== 4. OSONDAN QIYINGA (1-bosqich birinchi keladi) ===")
for kind in (TF, YN):
    r = c.get(
        f"/api/student/ielts/reading/round?kind={kind}&count=40",
        headers=H)
    ck(f"{kind} round 200", r.status_code, 200)
    items = r.json()["items"]
    steps = [i["step"] for i in items]
    ck(f"{kind}: bosqichlar o'sib boradi", steps == sorted(steps), True)
    ck(f"{kind}: birinchisi 1-bosqich", steps[0], 1)
    ck(f"{kind}: real imtihon oxirida", max(steps) <= 5, True)

print("\n=== 5. JAVOB MIJOZGA YUBORILMAYDI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={TF}&count=10",
          headers=H)
items = r.json()["items"]
raw = json.dumps(items, ensure_ascii=False)
ck("javobda 'answer' maydoni yo'q",
   all("answer" not in i for i in items), True)
ck("izoh (explain) ham yuborilmaydi",
   all("explain" not in i for i in items), True)
ck("har elementda matn bor",
   all(i["passage"] and i["prompt"] for i in items), True)
ck("har elementda 3 ta variant",
   all(len(i["options"]) == 3 for i in items), True)
ck("TFNG variantlari to'g'ri",
   items[0]["options"], ["TRUE", "FALSE", "NOT GIVEN"])
ck("bosqich nomi ham keladi",
   all(i.get("step_title") for i in items), True)

print("\n=== 6. TEKSHIRUV SERVERDA ===")
first = items[0]
row = db.query(models.PracticeItem).get(int(first["ref"].split(":")[1]))
right = row.answer
wrong = [o for o in first["options"] if o != right][0]
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": wrong}, headers=H)
ck("xato javob -> correct False", r.json()["correct"], False)
ck("to'g'risi ko'rsatiladi", r.json()["expected"], right)
ck("izoh qaytadi", bool(r.json()["explain"]), True)
ck("qaysi qoida ishlagani aytiladi", bool(r.json()["tip"]), True)
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": right.lower()},
           headers=H)
ck("kichik harf ham qabul qilinadi", r.json()["correct"], True)
ck("birinchi marta -> XP", r.json()["first_time"], True)
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": first["ref"], "answer": right}, headers=H)
ck("ikkinchi marta XP takrorlanmaydi", r.json()["first_time"], False)
r = c.post("/api/student/ielts/reading/answer",
           json={"ref": "pi:999999", "answer": "TRUE"}, headers=H)
ck("yo'q element -> 404", r.status_code, 404)

print("\n=== 7. YECHILGANI OXIRGA SURILADI ===")
r = c.get(f"/api/student/ielts/reading/round?kind={TF}&count=10",
          headers=H)
refs = [i["ref"] for i in r.json()["items"]]
ck("yechilgan savol qayta birinchi bo'lmaydi",
   first["ref"] not in refs[:1], True)

print("\n=== 8. KONTENT: BOSQICHLAR TO'LIQ ===")
rows = RS.build_rows()
per = collections.defaultdict(collections.Counter)
for kind, _lvl, pl, ans, why in rows:
    per[kind][pl["step"]] += 1
for kind, mins in ((RS.TF_KIND, (20, 20, 20, 30, 45)),
                   (RS.YN_KIND, (15, 15, 15, 15, 35))):
    for i, m in enumerate(mins, 1):
        ck(f"{kind} {i}-bosqich >= {m}", per[kind][i] >= m, True)

print("\n=== 9. KONTENT: HAR ELEMENT TO'LIQ VA NOYOB ===")
ck("hammasida izoh bor",
   all(w and len(w) > 15 for _k, _l, _p, _a, w in rows), True)
ck("hammasida tip yorlig'i bor",
   all(p.get("tip") for _k, _l, p, _a, _w in rows), True)
ck("javob doim variantlar ichida",
   all(a in p["options"] for _k, _l, p, a, _w in rows), True)
keys = [(k, p["passage"], p["prompt"]) for k, _l, p, _a, _w in rows]
ck("dublikat yo'q", len(keys), len(set(keys)))
ck("savol matni bo'sh emas",
   all(len(p["prompt"]) > 10 for _k, _l, p, _a, _w in rows), True)

print("\n=== 10. JAVOBLARNI TAXMIN QILIB BO'LMAYDI ===")
for kind, opts in ((RS.TF_KIND, RS.TF_OPTS), (RS.YN_KIND, RS.YN_OPTS)):
    cnt = collections.Counter(a for k, _l, _p, a, _w in rows
                              if k == kind)
    n = sum(cnt.values())
    print(f"    {kind}: {dict(cnt)}")
    for o in opts:
        share = cnt[o] / n
        ck(f"{kind}: '{o}' ulushi 10-60%",
           0.10 <= share <= 0.60, True)

print("\n=== 11. KIRISH BOSQICHI HAQIQATAN OSON ===")
# 1-bosqichda NOT GIVEN yo'q (avval TRUE/FALSE o'rgatiladi) va
# matn bir gapdan iborat.
for kind in (RS.TF_KIND, RS.YN_KIND):
    s1 = [(p, a) for k, _l, p, a, _w in rows
          if k == kind and p["step"] == 1]
    ck(f"{kind} 1-bosqichda NOT GIVEN yo'q",
       all(a != "NOT GIVEN" for _p, a in s1), True)
    ck(f"{kind} 1-bosqich matni qisqa (<160 belgi)",
       max(len(p["passage"]) for p, _a in s1) < 160, True)
# 5-bosqich (real imtihon) matnlari sezilarli uzunroq
for kind in (RS.TF_KIND, RS.YN_KIND):
    s1 = [p for k, _l, p, _a, _w in rows
          if k == kind and p["step"] == 1]
    s5 = [p for k, _l, p, _a, _w in rows
          if k == kind and p["step"] == 5]
    a1 = sum(len(p["passage"]) for p in s1) / len(s1)
    a5 = sum(len(p["passage"]) for p in s5) / len(s5)
    ck(f"{kind}: real imtihon matni 2x uzunroq", a5 > a1 * 2, True)
    print(f"    {kind}: 1-bosqich ~{int(a1)} belgi, "
          f"5-bosqich ~{int(a5)} belgi")

print("\n=== 12. 2-BOSQICH NOT GIVEN'NI HAQIQATAN O'RGATADI ===")
for kind in (RS.TF_KIND, RS.YN_KIND):
    s2 = [a for k, _l, p, a, _w in rows
          if k == kind and p["step"] == 2]
    ng = sum(1 for a in s2 if a == "NOT GIVEN")
    ck(f"{kind} 2-bosqichda NOT GIVEN ko'p (>=40%)",
       ng / len(s2) >= 0.40, True)
    ck(f"{kind} 2-bosqichda boshqa javoblar ham bor",
       ng < len(s2), True)

print("\n=== 13. 4-BOSQICH: TIP QOPQONLARI QAMROVI ===")
tf4 = [p["tip"] for k, _l, p, _a, _w in rows
       if k == RS.TF_KIND and p["step"] == 4]
for tip in ("Tip 15", "Tip 16", "Tip 17", "Tip 18", "Tip 19",
            "Tip 20", "Tip 21", "Tip 22", "Tip 23", "Tip 24",
            "Tip 25", "Tip 30"):
    n = sum(1 for t in tf4 if t.startswith(tip))
    ck(f"{tip} bo'yicha 3 ta mashq", n, 3)

print("\n=== 14. KITOB JAVOB KALITI BILAN MOS ===")
# Kitobning 253-betidagi javob kalitidan nuqtaviy tekshiruv.
KEY = [
    ("read_tfng", "Newton believed that action and reaction",
     "NOT GIVEN"),
    ("read_tfng", "All website are designed to be entertaining",
     "FALSE"),
    ("read_tfng", "Foreign cars are preferred by most customers",
     "TRUE"),
    ("read_tfng", "The cork oak has the thickest bark", "NOT GIVEN"),
    ("read_tfng", "All parts of the glacier move at the same speed",
     "FALSE"),
    ("read_tfng", "The ridges and patterns that make up fingerprints",
     "TRUE"),
    ("read_ynng", "There were three types of worm", "NO"),
    ("read_ynng", "Modern technologies have led to a reduction",
     "YES"),
    ("read_ynng", "Teams work best when their members", "NOT GIVEN"),
    ("read_ynng", "Beethoven would probably have accepted", "NO"),
    ("read_ynng", "The study shows elephants work together", "YES"),
    ("read_ynng", "The classic networker is physically strong",
     "NOT GIVEN"),
]
for kind, frag, want in KEY:
    got = [a for k, _l, p, a, _w in rows
           if k == kind and frag in p["prompt"]]
    ck(f"kalit: {frag[:40]}…", got[0] if got else "TOPILMADI", want)

print("\n=== 15. HAQIQIY IMTIHON SAVOLLARI OXIRIDA VA "
      "OSONDAN QIYINGA ===")
# 5-bosqich ichida ham tartib bor: NOT GIVEN (eng qiyin tur)
# ro'yxatning oxirgi yarmiga to'plangan bo'lishi kerak.
for kind in (RS.TF_KIND, RS.YN_KIND):
    s5 = [(p["order"], a) for k, _l, p, a, _w in rows
          if k == kind and p["step"] == 5]
    s5.sort()
    half = len(s5) // 2
    ng_late = sum(1 for o, a in s5[half:] if a == "NOT GIVEN")
    ng_all = sum(1 for _o, a in s5 if a == "NOT GIVEN")
    ck(f"{kind}: NOT GIVEN savollari oxirgi yarmida "
       f"({ng_late}/{ng_all})", ng_late >= ng_all * 0.7, True)

print("\n=== 16. SEED IDEMPOTENT ===")
n1 = db.query(models.PracticeItem).filter(
    models.PracticeItem.skill == RS.SKILL).count()
RS.seed_reading_ielts(db)
n2 = db.query(models.PracticeItem).filter(
    models.PracticeItem.skill == RS.SKILL).count()
ck("qayta seed dublikat yaratmaydi", n2, n1)
# Bazada Table Completion mashqlari ham bor — TFNG/YNNG qismini
# alohida sanaymiz (2026-08-25).
n_tf_yn = db.query(models.PracticeItem).filter(
    models.PracticeItem.skill == RS.SKILL,
    models.PracticeItem.kind.in_((RS.TF_KIND, RS.YN_KIND))).count()
ck("bazada build_rows bilan bir xil", n_tf_yn, len(rows))

print("\n=== 17. ESKI MASHQLAR BUZILMAGAN ===")
r = c.get("/api/student/ielts/listening/parts", headers=H)
ck("listening parts hali ishlaydi", r.status_code, 200)
ck("listening 11 mashq", len(r.json()["parts"]), 11)
r = c.get("/api/student/practice/reading/levels", headers=H)
ck("daraja bo'limlari ishlaydi", r.status_code, 200)

print()
if fails:
    print(f"XATO: {len(fails)} ta -> {fails}")
    sys.exit(1)
print("HAMMASI O'TDI")
