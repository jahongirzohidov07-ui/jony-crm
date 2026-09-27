"""TAKRORLANGAN SAVOL RAQAMI VA VARIANT HARFI (2026-09-27).

Jahongir skrinshoti: "11. 11 The land now occupied ..." va
"A  A a reservoir." — mock matnlarida raqam va harf matnning ichida
yozilgan edi, ekran esa ularni o'zi qo'shadi.

Tekshiriladi:
  A. strip_q_prefix / strip_opt_prefixes chekka holatlari (oddiy matnga
     tegilmaydi);
  B. api/mock_data dagi hech bir savol/variantda prefiks qolmagan;
  C. clean_parts yangi saqlangan shablonni tozalaydi, javob indekslari
     o'zgarmaydi;
  D. Bazadagi ESKI (prefiksli) faol shablon bir martalik migratsiyada
     tozalanadi — savol id'lari, javoblar va tur o'zgarmaydi; yashirin
     nusxaga tegilmaydi; ikkinchi start hech narsa qilmaydi;
  E. Tuzatishdan OLDIN ochilgan link nusxasi (ExamOnline.parts) ham
     o'quvchiga toza chiqadi (public_parts) va javoblar varag'i toza.
"""
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DB = os.path.join(tempfile.gettempdir(), "test_mock_prefixes.db")
if os.path.exists(DB):
    os.remove(DB)
os.environ["DATABASE_URL"] = "sqlite:///" + DB.replace("\\", "/")

import database                                   # noqa: E402
import models                                     # noqa: E402
import mock_seed                                  # noqa: E402
import exam_online as eo                          # noqa: E402

models.Base.metadata.create_all(bind=database.engine)
db = database.SessionLocal()
T = models.ExamTemplate
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


L = "ABCDEFGHIJKLMNOP"

# ----------------------------------------------------------------- A
print("=== A. CHEKKA HOLATLAR ===")
ck("raqam + ikki bo'shliq", eo.strip_q_prefix("11  The land"), "The land")
ck("oraliq", eo.strip_q_prefix("38-40  Choose THREE"), "Choose THREE")
ck("'and' oraliq", eo.strip_q_prefix("24 and 25  Choose TWO"), "Choose TWO")
ck("nuqta", eo.strip_q_prefix("3. What is it?"), "What is it?")
ck("yil bilan boshlangan matn", eo.strip_q_prefix("1998 was dry"), "1998 was dry")
ck("o'nlik son", eo.strip_q_prefix("3.5 million people"), "3.5 million people")
ck("bitta bo'shliqli raqam", eo.strip_q_prefix("7 days later"), "7 days later")
ck("faqat raqam bo'lsa — o'zgarmaydi", eo.strip_q_prefix("12  "), "12  ")
ck("gap o'rtasidagi 'and'", eo.strip_q_prefix("39  and may not feel"),
   "and may not feel")
ck("harf + ikki bo'shliq",
   eo.strip_opt_prefixes(["A  a reservoir.", "B  a quarry.", "C  farmland."]),
   ["a reservoir.", "a quarry.", "farmland."])
ck("harf + qavs", eo.strip_opt_prefixes(["A) red", "B) blue"]), ["red", "blue"])
ck("xarita harflari o'zgarmaydi", eo.strip_opt_prefixes(list("ABCDEFGH")),
   list("ABCDEFGH"))
ck("ketma-ket bo'lmasa tegilmaydi",
   eo.strip_opt_prefixes(["A lot", "Quite a few"]), ["A lot", "Quite a few"])
ck("TFNG o'zgarmaydi", eo.strip_opt_prefixes(["TRUE", "FALSE", "NOT GIVEN"]),
   ["TRUE", "FALSE", "NOT GIVEN"])

# ----------------------------------------------------------------- B
print("\n=== B. MOCK_DATA FAYLLARI TOZA ===")
left_q, left_o, total = [], [], 0
root = os.path.join(HERE, "mock_data")
for sub in sorted(os.listdir(root)):
    d = os.path.join(root, sub)
    if not os.path.isdir(d):
        continue
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json"):
            continue
        t = json.load(io.open(os.path.join(d, name), encoding="utf-8"))
        for p in t["parts"]:
            for q in p.get("questions") or []:
                total += 1
                if eo.strip_q_prefix(q.get("q")) != q.get("q"):
                    left_q.append(f"{name}: {q['q'][:30]}")
                o = q.get("options") or []
                if o and eo.strip_opt_prefixes(o) != o:
                    left_o.append(f"{name}: {o[:2]}")
ck(f"{total} savolda raqam prefiksi qolmagan", left_q[:5], [])
ck("variantlarda harf prefiksi qolmagan", left_o[:5], [])

# ----------------------------------------------------------------- C
print("\n=== C. CLEAN_PARTS YANGI SAQLASHDA TOZALAYDI ===")
cp = eo.clean_parts([{"title": "Part 1", "questions": [
    {"type": "choice", "q": "11  The land was", "answer": 1,
     "options": ["A  a reservoir.", "B  a quarry.", "C  farmland."]},
    {"type": "multi", "q": "14-15  Choose TWO", "answer": [0, 2],
     "options": ["A  one", "B  two", "C  three", "D  four"]},
    {"type": "text", "q": "16  Surname: ....", "answer": ["Smith"]},
]}])
qs = cp[0]["questions"]
ck("matnlar", [q["q"] for q in qs], ["The land was", "Choose TWO", "Surname: ...."])
ck("variantlar", (qs[0]["options"], qs[1]["options"]),
   (["a reservoir.", "a quarry.", "farmland."], ["one", "two", "three", "four"]))
ck("javob indekslari o'zgarmadi", (qs[0]["answer"], qs[1]["answer"]), (1, [0, 2]))
ck("raqamlash o'z joyida", [q["n"] for q in qs], [1, 2, 3])

# ----------------------------------------------------------------- D
print("\n=== D. BAZADAGI ESKI SHABLON MIGRATSIYASI ===")
tpl_file = json.load(io.open(os.path.join(root, "ielts", "ielts_listening_a.json"),
                             encoding="utf-8"))
clean = eo.clean_parts(tpl_file["parts"])


def dirty(parts):
    """Tuzatishdan oldingi ko'rinish: raqam va harf matn ichida."""
    out = json.loads(json.dumps(parts))
    for p in out:
        for q in p["questions"]:
            q["q"] = f"{q['n']}  {q['q']}"
            if q.get("options") and q["options"] != list(L[:len(q["options"])]):
                q["options"] = [f"{L[i]}  {o}" for i, o in enumerate(q["options"])]
    return out


old = dirty(clean)
active = T(level="ielts_intro", kind="mock", title=tpl_file["title"],
           parts=json.dumps(old, ensure_ascii=False), variant="A",
           subject="english", is_active=1, created_by="JonyOS")
hidden = T(level="ielts_intro", kind="mock", title=tpl_file["title"] + " (dublikat)",
           parts=json.dumps(old, ensure_ascii=False), variant="A",
           subject="english", is_active=0, created_by="JonyOS")
db.add_all([active, hidden])
db.commit()
ck("oldin: '11. 11 ...' holati takrorlandi",
   eo._load(active.parts)[1]["questions"][0]["q"].startswith("11  "), True)
mock_seed.seed_mocks(db)
db.refresh(active)
db.refresh(hidden)
new = eo._load(active.parts)
q11 = new[1]["questions"][0]
ck("11-savol matni toza", q11["q"], clean[1]["questions"][0]["q"])
ck("11-savol variantlari toza", q11.get("options"), clean[1]["questions"][0].get("options"))
ck("savol id, n, tur va javoblar o'zgarmadi",
   [(q["id"], q["n"], q["type"], q.get("answer")) for p in new for q in p["questions"]],
   [(q["id"], q["n"], q["type"], q.get("answer")) for p in clean for q in p["questions"]])
def diff_paths(a, b, path=""):
    """Ikki JSON orasidagi farqli yo'llar (qisqa hisobot uchun)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(f"{path}.{k} ({'yangi' if k in a else 'yo`q'})")
            else:
                out += diff_paths(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path} (uzunlik {len(a)} != {len(b)})"]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff_paths(x, y, f"{path}[{i}]")
        return out
    return [] if a == b else [path]


# "skill" belgisini backfill_skills qo'shadi — bu kutilgan
ck("butun shablon fayl bilan bir xil (skill belgisidan tashqari)",
   [d for d in diff_paths(new, clean) if ".skill" not in d], [])
ck("skill belgisi to'ldirildi", {p.get("skill") for p in new}, {"ielts_listening"})
ck("yashirin nusxaga tegilmadi", eo._load(hidden.parts), old)
before = active.parts
mock_seed.seed_mocks(db)
db.refresh(active)
ck("ikkinchi start hech narsa o'zgartirmaydi", active.parts, before)

# ----------------------------------------------------------------- E
print("\n=== E. ESKI LINK NUSXASI ===")
pub = eo.public_parts(old)
ck("o'quvchiga toza savol", pub[1]["questions"][0]["q"], clean[1]["questions"][0]["q"])
ck("o'quvchiga toza variantlar", pub[1]["questions"][0].get("options"),
   clean[1]["questions"][0].get("options"))
ck("o'quvchi nusxasida javob yo'q",
   any("answer" in q for p in pub for q in p["questions"]), False)
qm = eo._qmap(old)
qid = clean[1]["questions"][0]["id"]
ck("javoblar varag'i uchun toza matn", qm[qid]["q"], clean[1]["questions"][0]["q"])
ck("javoblar varag'i uchun toza variantlar", qm[qid].get("options"),
   clean[1]["questions"][0].get("options"))

print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
db.close()
sys.exit(1 if fails else 0)
