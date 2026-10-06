"""REJADAN YUBORILGAN TOPSHIRIQ — O'QUVCHIGA HAMMASI YETADI, ADOLATLI
TEKSHIRILADI (2026-10-05, katta ustozlar auditi):
  1) box (so'zlar ro'yxati) o'quvchiga boradi; "C beach" javobida "C" ham,
     "beach" ham to'g'ri — lekin boshqa harf xato;
  2) bandi faqat '1'…'7' bo'lgan summary/jadval matni o'quvchiga boradi;
     "(paper) bookmarks" — "bookmarks" ham, "paper bookmarks" ham to'g'ri;
  3) qavsdagi ixtiyoriy so'zlar va " / " muqobillari;
  4) TRUE/FALSE/NOT GIVEN, YES/NO/NOT GIVEN — tanlanadi, T/F/NG/Y/N ham to'g'ri.

Har kurs (1.0–7.0) har darsi uchun assignable() ro'yxatidagi har qism tuziladi
va tekshiriladi. Ishga tushirish:
    python test_plan_assign_grading.py               # repo JSON
    python test_plan_assign_grading.py --fix [DIR]   # 5.0–7.0 tuzatilgan darslar
                                                     # (DIR/<kurs>/L<NN>.json)
DIR berilmasa PLAN_FIX_DIR yoki ../../fix5/out olinadi."""
import glob
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict

_DIR = os.path.join(tempfile.gettempdir(), "plan_assign_grading_test")
os.makedirs(_DIR, exist_ok=True)
_DB = os.path.join(_DIR, "db.sqlite")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace(chr(92), "/")
if os.path.exists(_DB):
    os.remove(_DB)
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import assignments as A                            # noqa: E402
import liveplay as LP                              # noqa: E402

FIX = "--fix" in sys.argv
FIX_DIR = None
if FIX:
    k = sys.argv.index("--fix")
    FIX_DIR = (sys.argv[k + 1] if len(sys.argv) > k + 1 else None) or os.environ.get("PLAN_FIX_DIR") \
        or os.path.normpath(os.path.join(_HERE, "..", "..", "fix5", "out"))
    if not os.path.isdir(FIX_DIR):
        print("XATO: tuzatilgan darslar papkasi topilmadi:", FIX_DIR)
        sys.exit(1)

fails = []


def bad(msg):
    if len(fails) < 60:
        print("XATO", msg)
    fails.append(msg)


# --- darslar: repo JSON, --fix bo'lsa 5.0–7.0 tuzatilgan nusxasi ustidan
LESSONS = {}
for n in range(1, 8):
    course = f"ielts_{n}_0"
    for L in LP._load_course(course)["lessons"]:
        LESSONS[(course, int(L["no"]))] = L
    if FIX and n >= 5:
        files = sorted(glob.glob(os.path.join(FIX_DIR, course, "L*.json")))
        if not files:
            bad(f"{course}: tuzatilgan darslar yo'q ({FIX_DIR})")
        for p in files:
            with open(p, encoding="utf-8") as f:
                L = json.load(f)
            LESSONS[(course, int(L["no"]))] = L
A._lesson = lambda c, no: LESSONS[(c, int(no))]   # assignable() shu darslarni o'qisin

# --- testning O'Z tahlilchilari (assignments ichki funksiyalariga tayanmaydi)
TFW = {"T": "TRUE", "F": "FALSE", "TRUE": "TRUE", "FALSE": "FALSE", "NG": "NOT GIVEN", "NOT GIVEN": "NOT GIVEN"}
YNW = {"Y": "YES", "N": "NO", "YES": "YES", "NO": "NO", "NG": "NOT GIVEN", "NOT GIVEN": "NOT GIVEN"}
ABBR = {"TRUE": ["T", "true", "True"], "FALSE": ["F", "false"], "NOT GIVEN": ["NG", "ng", "not given", "Not Given"],
        "YES": ["Y", "yes"], "NO": ["N", "no"]}


def strip_no(a, j):
    m = re.match(r"^\s*(\d{1,2})\s*(?:[.)]\s+|[—–-]\s+)(?=\S)", a)
    return a[m.end():].strip() if m and int(m.group(1)) in (j + 1,) else a.strip()


def tf_lead(a):
    s = re.sub(r"^\s*\d{1,2}(?:[.)]\s+|\s*[—–-]\s+)", "", a.strip())
    m = re.match(r"(?i)(not\s+given|true|false|yes|no|ng|t|f|y|n)\.?(?=\s*$|\s*\(|\s*[—–:]|\s+-\s)", s)
    return re.sub(r"\s+", " ", m.group(1)).upper() if m else None


def lettered_box(box):
    """{'C': 'beach'} — harflangan box (A, B, C… / i, ii, iii…), aks holda {}."""
    if not isinstance(box, list) or len(box) < 2:
        return {}
    out = {}
    for b in box:
        m = re.match(r"^\s*([A-Za-z]|i{1,3}|iv|v|vi{1,3}|ix|x)(?:[).]\s*|\s+)(?:[—–-]\s+)?(\S.*)$", str(b))
        if not m or m.group(1) in out:
            return {}
        out[m.group(1)] = m.group(2).strip()
    labs = list(out)
    roman = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]
    if labs == roman[:len(labs)] or (all(len(x) == 1 for x in labs)
                                     and all(ord(y) - ord(x) == 1 for x, y in zip(labs, labs[1:]))):
        return out
    return {}


def paren_forms(a):
    """'(paper) bookmarks' -> ('bookmarks', 'paper bookmarks')."""
    drop = re.sub(r"\s+", " ", re.sub(r"\([^()]*\)", " ", a)).strip()
    keep = re.sub(r"\s+", " ", re.sub(r"\(([^()]*)\)", r" \1 ", a)).strip()
    return drop, keep


def ok(q, given):
    return A.is_correct(q["kind"], given, q.get("accept") or q.get("answer"))


def walk_blocks(qs):
    for q in qs:
        for c in q.get("ctx") or []:
            yield c


T = defaultdict(Counter)

for (course, no), L in sorted(LESSONS.items()):
    T[course]["darslar"] += 1
    try:
        parts = [p["part"] for p in A.assignable(course, no, None)]
    except Exception as e:                       # noqa: BLE001
        bad(f"{course} L{no}: assignable() yiqildi: {e!r}")
        continue
    for part in parts:
        b = A.build_from_plan(L, part, course)
        if not b or not b.get("questions"):
            bad(f"{course} L{no} {part}: ro'yxatda bor, lekin tuzilmadi")
            continue
        T[course]["qismlar"] += 1
        qs = b["questions"]
        where = f"{course} L{no} {part}"
        for i, q in enumerate(qs):
            T[course]["savollar"] += 1
            if q["kind"] not in A.AUTO_KINDS:
                continue
            T[course]["avtomat"] += 1
            if not str(q.get("prompt") or "").strip():
                bad(f"{where} #{i}: bo'sh savol matni")
            pub = A._public_q(q)
            if any(k in pub for k in ("answer", "accept", "explain")):
                bad(f"{where} #{i}: javob o'quvchiga ochiq: {sorted(pub)}")
            if q["kind"] == "mcq":
                n = len(q["options"])
                if not (A.is_correct("mcq", q["answer"], q["answer"])
                        and (n < 2 or not A.is_correct("mcq", (q["answer"] + 1) % n, q["answer"]))):
                    bad(f"{where} #{i}: mcq kaliti")
                continue
            if not ok(q, q["answer"]):
                bad(f"{where} #{i}: rasmiy javob xato chiqdi: {q['answer']!r}")
            if ok(q, "zzqx qwv"):
                bad(f"{where} #{i}: bema'ni javob to'g'ri chiqdi")
            for x in q.get("accept") or []:
                if not ok(q, x):
                    bad(f"{where} #{i}: accept dagi {x!r} xato chiqdi")
            if q["kind"] == "tf":
                T[course]["tfng"] += 1
                opts = q.get("options") or []
                if q["answer"] not in opts:
                    bad(f"{where} #{i}: TF javobi variantlarda yo'q: {q['answer']!r} {opts}")
                for o in opts:
                    if ok(q, o) != (o == q["answer"]):
                        bad(f"{where} #{i}: TF variant {o!r} noto'g'ri baholandi (kalit {q['answer']!r})")
                for ab in ABBR.get(q["answer"], []):
                    if not ok(q, ab):
                        bad(f"{where} #{i}: qisqartma {ab!r} ({q['answer']}) qabul qilinmadi")
                continue
            opts = q.get("options") or []
            if opts:
                T[course]["tanlanadigan"] += 1
                good = [o for o in opts if ok(q, o)]
                lettered = bool(lettered_box(opts)) or all(re.match(r"^[A-E]\)\s", o) for o in opts)
                if not good or (lettered and len(good) != 1) or (len(opts) > 1 and len(good) == len(opts)):
                    bad(f"{where} #{i}: variantlardan to'g'risi {len(good)} ta: {q['answer']!r} {good[:3]}")

        # --- manba mashqlari bilan solishtirish
        if part.startswith("hw:"):
            exs = [L["homework"][int(part[3:])]]
        elif part.startswith("reading"):
            exs = A._readings(L)[int(part.split(":")[1]) if ":" in part else 0].get("tasks", [])
        else:
            exs = []
        blocks = list(walk_blocks(qs))
        for ex in exs:
            if isinstance(ex.get("box"), list) and ex["box"]:
                T[course]["box_mashq"] += 1
                if not any(c.get("box") == [str(x) for x in ex["box"]] for c in blocks):
                    bad(f"{where}: box o'quvchiga yetmadi ({ex.get('title')})")
            if isinstance(ex.get("rows"), list) and ex["rows"]:
                T[course]["jadval_mashq"] += 1
                if not any(c.get("rows") for c in blocks
                           if json.dumps(c.get("rows"), ensure_ascii=False) == json.dumps(
                               [[str(x) for x in r] if isinstance(r, list) else [str(r)] for r in ex["rows"]],
                               ensure_ascii=False)):
                    bad(f"{where}: summary/jadval o'quvchiga yetmadi ({ex.get('title')})")
        if b["kind"] in ("writing", "speaking"):
            continue
        for ex in exs:
            items, answers = ex.get("items"), ex.get("answers")
            if not (isinstance(items, list) and isinstance(answers, list) and len(items) == len(answers)
                    and items and all(isinstance(x, str) for x in answers)):
                continue
            eq = A._ex_to_questions(ex, head=part.startswith("reading"))
            if len(eq) != len(items):
                bad(f"{where}: {ex.get('title')}: {len(items)} band, {len(eq)} savol")
                continue
            if part.startswith("reading") and ex.get("title") and not any(
                    c.get("title") == ex["title"].strip() for c in eq[0].get("ctx") or []):
                bad(f"{where}: vazifa sarlavhasi yo'q ({ex['title']})")
            # IELTS raqami: hamma bandlar ketma-ket raqamli bo'lsa — saqlanadi
            nums = [re.match(r"^\s*(\d{1,2})(?:[.)]\s*|\s+|\s*$)", str(it)) for it in items]
            if all(nums) and all(int(b2.group(1)) == int(a2.group(1)) + 1 for a2, b2 in zip(nums, nums[1:])):
                for j, q in enumerate(eq):
                    if str(q.get("no") or "") != nums[j].group(1):
                        bad(f"{where}: {j}-band raqami yo'qoldi: {items[j][:30]!r} -> {q.get('no')!r}")
                    if q["kind"] in A.AUTO_KINDS and re.fullmatch(r"\s*\d+\s*", items[j]) and ex.get("rows") \
                            and f"({nums[j].group(1)})" not in q["prompt"]:
                        bad(f"{where}: '{items[j]}' bandiga jadval/summary qatori berilmadi: {q['prompt']!r}")
            bm = lettered_box(ex.get("box"))
            leads = [tf_lead(a) for a in answers]
            for j, (it, a, q) in enumerate(zip(items, answers, eq)):
                if q["kind"] not in A.AUTO_KINDS:
                    continue
                if not ok(q, a.strip()):
                    bad(f"{where}: manbadagi rasmiy javob xato chiqdi: {a!r} (savol {q.get('answer')!r})")
                if q["kind"] == "tf" and leads[j] not in TFW and leads[j] not in YNW:
                    bad(f"{where}: T/F emas javob T/F savol bo'ldi: {a!r}")
                if leads[j] in ("TRUE", "FALSE", "NOT GIVEN") and q["kind"] != "tf":
                    bad(f"{where}: {a!r} — tanlanadigan TRUE/FALSE/NOT GIVEN emas")
                if q["kind"] != "gap":
                    continue
                core = strip_no(a, j)
                pm = re.fullmatch(r"(?:Paragraph\s+)?([A-H])", re.sub(r"^\s*\d{1,2}[.)]?\s+", "", it).strip())
                m2 = re.match(r"^([A-H])\s*[—–-]\s*(\S.*)$", core) if pm else None
                if m2 and m2.group(1) == pm.group(1):
                    core = m2.group(2).strip()
                # 1) box: harf, so'z, ikkalasi — to'g'ri; boshqa harf — xato
                m = re.match(r"^([A-Za-z]{1,4})[).]?(?:\s+[—–-])?(?:\s+(.*))?$", core)
                if bm and m and m.group(1) in bm and (not m.group(2) or m.group(2).startswith("(")
                                                      or A.norm(m.group(2)) == A.norm(bm[m.group(1)])):
                    T[course]["box_javob"] += 1
                    lab, word = m.group(1), bm[m.group(1)]
                    for g in (lab, word, f"{lab} {word}", lab.lower() if len(lab) == 1 else lab):
                        if not ok(q, g):
                            bad(f"{where}: box javobi {g!r} ({a!r}) qabul qilinmadi")
                    for other in bm:
                        if other != lab and A.norm(bm[other]) != A.norm(word) and ok(q, other):
                            bad(f"{where}: boshqa box harfi {other!r} ({a!r}) to'g'ri chiqdi")
                elif re.match(r"^[A-Z]\s+\w", core) and not re.match(r"^[A-E]\s*(?:,|and)", core):
                    # box yo'q: "I am tired." — yolg'iz "I" to'g'ri bo'lmasligi kerak
                    if ok(q, core[0]):
                        bad(f"{where}: yolg'iz harf {core[0]!r} ({a!r}) to'g'ri chiqdi")
                # 3) qavsdagi ixtiyoriy so'zlar
                if "(" in core and core.count("(") == core.count(")") <= 3 and not m2 and not (
                        bm and m and m.group(1) in bm):
                    T[course]["qavs"] += 1
                    for g in paren_forms(core):
                        if g and not ok(q, g):
                            bad(f"{where}: qavsli javob {g!r} ({a!r}) qabul qilinmadi")

# --- eski (yuborilgan, bazada saqlangan) savol shakllari baholanishi buzilmasin
old = [{"kind": "tf", "prompt": "x", "answer": "T", "explain": "T"},
       {"kind": "tf", "prompt": "x", "answer": "F", "explain": "F (alarm)"},
       {"kind": "gap", "prompt": "x", "answer": "C beach", "explain": None},
       {"kind": "gap", "prompt": "x", "answer": "(paper) bookmarks", "explain": None},
       {"kind": "gap", "prompt": "x", "answer": "am / is", "explain": None},
       {"kind": "mcq", "prompt": "x", "options": ["a", "b"], "answer": 1},
       {"kind": "text", "prompt": "x", "answer": "Namuna"}]
r = A.auto_grade(old, {"0": "true", "1": "F", "2": "c beach ", "3": "paper bookmarks", "4": "is", "5": 1})
if (r["score"], r["max"]) != (6, 6):
    bad(f"eski shakllar: {r['score']}/{r['max']} {r['items']}")
r = A.auto_grade(old, {"0": "F", "1": "To'g'ri", "2": "beach", "3": "paper", "4": "are", "5": 0})
if r["score"] != 0:
    bad(f"eski shakllar: xato javoblar to'g'ri chiqdi {[x for x in r['items'] if x['ok']]}")
for given, exp, want in [("T", "T", True), ("To'g'ri", "T", True), ("NO", "N", True), ("ng", "NOT GIVEN", True),
                         ("N", "NOT GIVEN", False), ("n", "FALSE", False), ("Y", "YES", True), ("NG", "NO", False)]:
    if A.is_correct("tf", given, exp) != want:
        bad(f"tf {given!r} / {exp!r} -> {not want}")
for given, exp, want in [("bookmarks", "(paper) bookmarks", True), ("paper bookmarks", "(paper) bookmarks", True),
                         ("initial enthusiasm", "(initial) enthusiasm", True), ("enthusiasm", "(initial) enthusiasm", True),
                         ("a cultural clash", "(a) cultural clash", True), ("cultural clash", "(a) cultural clash", True),
                         ("paper", "(paper) bookmarks", False), ("C", "C beach", False), ("I", "I am tired.", False),
                         ("so", "so / and", True), ("are", "are (ko'plik)", True)]:
    if A.is_correct("gap", given, exp) != want:
        bad(f"gap {given!r} / {exp!r} -> {not want}")

print(f"\nManba: {'repo JSON + tuzatilgan 5.0–7.0 (' + FIX_DIR + ')' if FIX else 'repo JSON'}")
for course in sorted(T):
    t = T[course]
    print(f"{course}: {t['darslar']} dars, {t['qismlar']} qism, {t['savollar']} savol ({t['avtomat']} avtomat), "
          f"TF/YN {t['tfng']}, tanlanadigan {t['tanlanadigan']}, box javob {t['box_javob']}, "
          f"qavsli {t['qavs']}, box mashq {t['box_mashq']}, jadval/summary {t['jadval_mashq']}")
print("\nJAMI XATO:", len(fails))
sys.exit(1 if fails else 0)
