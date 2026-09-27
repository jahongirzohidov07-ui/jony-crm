"""MOCK TEST BAZASI (2026-09-26).

Jahongir: "sen xuddi shu pattern va uslubdagi Mock testlar tuzib
berasan haqiqiy IELTS CDI testlari bilan 1x1 kopya bo'lishi kerak ...
va katta mock test bazasini yarat".

Tekshiriladi:
  A. mock_data/ielts/*.json — IELTS formatiga mosligi: Listening 4
     bo'lim × 10 savol va har bo'limda skript, Reading 3 matn ×
     (13,13,14) va matn uzunligi, Writing/Speaking essay (avtomat
     tekshirilmaydi), javob indekslari va matn javoblari joyida;
  B. Yangi savol turlari: multi (Choose TWO letters) faqat hammasi
     to'g'ri bo'lsa ball beradi, essay ballga kirmaydi;
  C. Band jadvali: Listening va Reading chegaralari rasmiy jadvaldek;
  D. Seed: har daraja uchun alohida shablon, ikkinchi seed hech narsa
     qo'shmaydi, bank_max mock uchun band (9) qaytaradi;
  E. mix_parts: bir xil tuzilishdagi variantlar aralashadi, Listening
     va Reading bir-biriga aralashmaydi.
"""
import os
import sys
import random
import tempfile

_DB = os.path.join(tempfile.gettempdir(), "mock_bank_test.db")
os.environ["DATABASE_URL"] = "sqlite:///" + _DB.replace("\\", "/")
if os.path.exists(_DB):
    os.remove(_DB)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import json                                         # noqa: E402
import models                                       # noqa: E402
import exam_online                                  # noqa: E402
import mock_seed                                    # noqa: E402
from database import SessionLocal, engine           # noqa: E402

models.Base.metadata.create_all(bind=engine)
fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


# ----------------------------------------------------------------- A
print("=== A. MOCK FAYLLARI IELTS FORMATIDA ===")
ALL = mock_seed._files()
CEFR = [t for t in ALL if "cefr" in (t.get("levels") or [])]
CH25 = [t for t in ALL if (t.get("key") or "").startswith("challenge25_")]
FILES = [t for t in ALL if t not in CEFR and t not in CH25]
ck("IELTS: 20 fayl (4 bo'lim × 5 variant)", len(FILES), 20)
ck("CEFR: 19 fayl (Speaking 10 variant, qolgani 3 tadan)", len(CEFR), 19)
ck("CEFR Speaking A-J",
   sorted(t["variant"] for t in CEFR if t["section"] == "speaking"),
   list("ABCDEFGHIJ"))
# Rasmiy Multilevel Speaking: 4 qism (Part 1.1 / 1.2 / 2 / 3), reyting
# 0-75 (2026-09-26, DTM spetsifikatsiyasi).
SP = [t for t in CEFR if t["section"] == "speaking"]
ck("Speaking 4 qism, rasmiy nomlar bilan",
   sorted({tuple(p["title"] for p in t["parts"]) for t in SP}),
   [("Part 1.1", "Part 1.2", "Part 2", "Part 3")])
ck("Speaking reytingi 75", sorted({t["paper_max"] for t in SP}), [75])
ck("Speaking kalitlari yangi oilada (eskisi bilan to'qnashmaydi)",
   all(t["key"].startswith("mock_cefr_ml_speaking_") for t in SP), True)
ck("25-day challenge: 17 kun", len(CH25), 17)

by_sec = {}
for t in FILES:
    by_sec.setdefault(t["section"], []).append(t)
ck("har bo'limda 5 variant",
   sorted((k, len(v)) for k, v in by_sec.items()),
   [("listening", 5), ("reading", 5), ("speaking", 5), ("writing", 5)])

bad = []
for t in FILES:
    parts = exam_online.clean_parts(t["parts"])
    shape = tuple(len(p["questions"]) for p in parts)
    sec, V = t["section"], t["variant"]
    if V not in "ABCDE":
        bad.append(f"{t['key']}: variant {V!r}")
    if sec == "listening":
        if shape != (10, 10, 10, 10):
            bad.append(f"{t['key']}: tuzilish {shape}")
        for p in parts:
            w = len((p.get("script") or "").split())
            if w < 400:
                bad.append(f"{t['key']} {p['title']}: skript {w} so'z")
    elif sec == "reading":
        if shape != (13, 13, 14):
            bad.append(f"{t['key']}: tuzilish {shape}")
        for p in parts:
            w = len((p.get("passage") or "").split())
            if not (600 <= w <= 1200):
                bad.append(f"{t['key']} {p['title']}: matn {w} so'z")
    else:
        if any(q["type"] != "essay" for p in parts for q in p["questions"]):
            bad.append(f"{t['key']}: qo'lda baholanadigan bo'lim essay emas")
        if float(t.get("paper_max") or 0) != 9:
            bad.append(f"{t['key']}: paper_max {t.get('paper_max')}")
    for p in parts:
        for q in p["questions"]:
            if not (q.get("topic") or "").strip():
                bad.append(f"{t['key']} {q['n']}: mavzu yo'q")
            if q["type"] == "choice":
                if not (isinstance(q["answer"], int)
                        and 0 <= q["answer"] < len(q["options"])):
                    bad.append(f"{t['key']} {q['n']}: javob indeksi")
            elif q["type"] == "text":
                if not q["answer"]:
                    bad.append(f"{t['key']} {q['n']}: matn javobi yo'q")
            elif q["type"] == "multi":
                if sorted(q["answer"]) != q["answer"] or len(q["answer"]) < 2:
                    bad.append(f"{t['key']} {q['n']}: multi javobi")
ck("format xatosi yo'q", bad[:6], [])

graded = sum(1 for t in FILES for p in t["parts"] for q in p["questions"]
             if q.get("type") != "essay")
ck("avtomat tekshiriladigan savol 400 ta", graded, 400)

nbad = []
for t in FILES:
    parts = exam_online.clean_parts(t["parts"])
    ns = [q["n"] for p in parts for q in p["questions"]]
    if ns != list(range(1, len(ns) + 1)):
        nbad.append(t["key"])
ck("savollar 1..N raqamlangan", nbad, [])

# ----------------------------------------------------------------- B
print("\n=== B. YANGI SAVOL TURLARI ===")
demo = exam_online.clean_parts([{
    "title": "Reading Passage 1",
    "questions": [
        {"type": "multi", "q": "Choose TWO letters",
         "options": ["a", "b", "c", "d", "e"], "answer": [3, 1]},
        {"type": "essay", "q": "Write at least 250 words", "min_words": 250},
        {"type": "choice", "q": "x",
         "options": ["TRUE", "FALSE", "NOT GIVEN"], "answer": 2},
    ],
}])
qs = demo[0]["questions"]
ck("multi javobi saralanadi, pick chiqadi",
   (qs[0]["answer"], qs[0]["pick"]), ([1, 3], 2))
ck("essay min_words saqlanadi", qs[1]["min_words"], 250)
pub = exam_online.public_parts(demo)[0]["questions"][0]
ck("o'quvchiga pick boradi, javob bormaydi",
   ("answer" not in pub, pub["pick"]), (True, 2))

s, tot, det = exam_online.grade(demo, {"q1": [1, 3], "q2": "insho", "q3": 2})
ck("hammasi to'g'ri: 2/2 (essay ballga kirmaydi)", (s, tot), (2.0, 2.0))
ck("essay 'ok' — None", det[1]["ok"], None)
s, tot, _ = exam_online.grade(demo, {"q1": [1], "q3": 2})
ck("multi yarim to'g'ri — ball yo'q", (s, tot), (1.0, 2.0))
s, tot, _ = exam_online.grade(demo, {"q1": [1, 3, 4], "q3": 2})
ck("ortiqcha belgilangan — ball yo'q", (s, tot), (1.0, 2.0))
sheet = exam_online._answer_sheet(
    exam_online.grade(demo, {"q1": [1, 3]})[2], exam_online._qmap(demo))
ck("javob varag'ida multi harflar bilan",
   (sheet[0]["given_text"], sheet[0]["correct"]),
   ("B) b, D) d", "B) b, D) d"))

# ----------------------------------------------------------------- C
print("\n=== C. XOM BALL -> IELTS BAND ===")
L = [{"title": "Listening · Part 1"}]
R = [{"title": "Reading Passage 1"}]
ck("Listening 30/40 -> 7.0", exam_online.mock_band(L, 30, 40), 7.0)
ck("Listening 23/40 -> 6.0", exam_online.mock_band(L, 23, 40), 6.0)
ck("Reading 30/40 -> 7.0", exam_online.mock_band(R, 30, 40), 7.0)
ck("Reading 23/40 -> 6.0", exam_online.mock_band(R, 23, 40), 6.0)
ck("Reading 26/40 -> 6.0, Listening 26/40 -> 6.5",
   (exam_online.mock_band(R, 26, 40), exam_online.mock_band(L, 26, 40)),
   (6.0, 6.5))
ck("40/40 -> 9.0", exam_online.mock_band(L, 40, 40), 9.0)
ck("0/40 -> 1.0", exam_online.mock_band(L, 0, 40), 1.0)
ck("Writing bo'limida band yo'q",
   exam_online.mock_band([{"title": "Writing Task 1"}], 1, 1), None)
ck("savol yo'q — None", exam_online.mock_band(L, 0, 0), None)

# ----------------------------------------------------------------- D
print("\n=== D. SEED ===")
db = SessionLocal()
mock_seed.seed_mocks(db)
rows = db.query(models.ExamTemplate).filter_by(kind="mock").all()
LEVELS = ["ielts_foundation", "ielts_graduation", "ielts_intro"]
ck("IELTS 20×3 + CEFR 19×1 + challenge 17×3 = 130 shablon", len(rows), 130)
ck("darajalar to'g'ri", sorted({r.level for r in rows}), ["cefr"] + LEVELS)
ck("variantlar A-Q", sorted({r.variant for r in rows}), list("ABCDEFGHIJKLMNOPQ"))
ck("CEFR shablonlari 19 ta, variant A-J",
   (sum(1 for r in rows if r.level == "cefr"),
    sorted({r.variant for r in rows if r.level == "cefr"})),
   (19, list("ABCDEFGHIJ")))
ck("hammasi english, unit_no yo'q",
   ({r.subject for r in rows}, {r.unit_no for r in rows}),
   ({"english"}, {None}))
n_before = len(rows)
mock_seed.seed_mocks(db)
ck("ikkinchi seed hech narsa qo'shmaydi",
   db.query(models.ExamTemplate).filter_by(kind="mock").count(), n_before)

print(chr(10) + "=== D2. CEFR MULTILEVEL FORMATI ===")
cbad = []
for t in CEFR:
    parts = exam_online.clean_parts(t["parts"])
    shape = tuple(len(p["questions"]) for p in parts)
    want = {"listening": (8, 6, 4, 5, 6, 6), "reading": (6, 8, 6, 9, 6)}.get(t["section"])
    if want and shape != want:
        cbad.append(f"{t['key']}: {shape}")
    # Bo'lim nomlarida "Listening"/"Reading" bo'lmasin — bo'lmasa
    # mock_band IELTS jadvalini xato qo'llab yubormaydi.
    for p in parts:
        low = p["title"].lower()
        if "listening" in low or "reading" in low:
            cbad.append(f"{t['key']}: bo'lim nomi {p['title']!r}")
ck("CEFR tuzilishi kitobdagidek (35 savol)", cbad, [])
ck("CEFR Listening/Reading 35 savol",
   sorted({sum(len(p["questions"]) for p in t["parts"])
           for t in CEFR if t["section"] in ("listening", "reading")}), [35])
ck("CEFR'da IELTS band jadvali qo'llanmaydi",
   {exam_online.mock_band(t["parts"], 30, 35) for t in CEFR
    if t["section"] in ("listening", "reading")}, {None})


class _G:
    level = "ielts_graduation"
    subject = "english"


ck("bank_max mock uchun band (9)",
   exam_online.bank_max(db, _G(), "mock"), 9.0)

# ----------------------------------------------------------------- E
print("\n=== E. VARIANTLAR ARALASHADI ===")
base = (db.query(models.ExamTemplate)
        .filter_by(kind="mock", level="ielts_graduation", variant="A")
        .filter(models.ExamTemplate.title.like("IELTS Mock%Listening%")).first())
fam = exam_online._family(db, base)
# Oila endi ko'nikma bo'yicha ham ajratiladi: Listening faqat
# Listening bilan. Aks holda tashqi to'plam akademiya bazasiga
# aralashib ketishi mumkin edi (2026-09-26).
ck("oila = faqat Listening variantlari", len(fam), 5)
rnd = random.Random(7)
seen, mixbad = set(), []
for _ in range(25):
    parts, chosen = exam_online.mix_parts(base, fam, rnd)
    seen.add(chosen)
    if tuple(len(p["questions"]) for p in parts) != (10, 10, 10, 10):
        mixbad.append("tuzilish")
    if len(chosen.split(",")) != 4:
        mixbad.append("bo'lim soni")
ck("Listening faqat Listening bilan aralashdi (tuzilish saqlandi)",
   mixbad, [])
ck("kombinatsiyalar xilma-xil (>=10)", len(seen) >= 10, True)

rbase = (db.query(models.ExamTemplate)
         .filter_by(kind="mock", level="ielts_graduation", variant="A")
         .filter(models.ExamTemplate.title.like("IELTS Mock%Reading%")).first())
rparts, _rc = exam_online.mix_parts(
    rbase, exam_online._family(db, rbase), rnd)
ck("Reading aralashmasi (13,13,14)",
   tuple(len(p["questions"]) for p in rparts), (13, 13, 14))

print(chr(10) + "=== F. TASHQI TO'PLAM ALOHIDA TURADI ===")
ck("challenge25 savollari 644 ta",
   sum(sum(len(p["questions"]) for p in t["parts"]) for t in CH25), 644)
ck("hammasi reading va o'z belgisi bilan",
   (sorted({t["section"] for t in CH25}),
    sorted({p.get("skill") for t in CH25 for p in t["parts"]})),
   (["reading"], ["challenge25_reading"]))
chrow = (db.query(models.ExamTemplate)
         .filter_by(kind="mock", level="ielts_graduation", variant="A")
         .filter(models.ExamTemplate.title.like("%Challenge%")).first())
chfam = exam_online._family(db, chrow)
ck("challenge oilasi = faqat challenge (17 kun)", len(chfam), 17)
ck("akademiya Reading bazasi bilan aralashmaydi",
   any("Challenge" in (x.title or "") for x in exam_online._family(db, rbase)),
   False)
ck("challenge uchun avtomat band yo'q (savol soni har xil)",
   exam_online.mock_band(exam_online._load(chrow.parts), 30, 40), None)


print(chr(10) + "=== G. ESKI SHABLONLARGA KO'NIKMA BELGISI ===")
# Ko'nikma belgisi 2026-09-26 da qo'shilgan; undan oldin yozilgan
# shablonlarda u yo'q va "Mock testlar" jadvali noto'g'ri guruhlanardi
# (CEFR bo'limlari yo'qolib, IELTS "?" bo'lib chiqardi).
ck("sarlavhadan ko'nikma aniqlanadi",
   [mock_seed.skill_from_template(lv, t) for lv, t in [
       ("ielts_graduation", "IELTS Mock - Listening - Variant A"),
       ("cefr", "CEFR Multilevel Mock - Reading - Variant B"),
       ("ielts_intro", "Reading Challenge - Day 3 (3 matn)"),
       ("cefr", "CEFR Multilevel Mock - Speaking - Variant J"),
   ]],
   ["ielts_listening", "cefr_reading", "challenge25_reading", "cefr_speaking"])

_rows = db.query(models.ExamTemplate).filter_by(kind="mock").all()
for _t in _rows[:6]:
    _p = exam_online._load(_t.parts)
    for _x in _p:
        _x.pop("skill", None)
    _t.parts = json.dumps(_p, ensure_ascii=False)
db.commit()
ck("belgisiz shablon guruhlanmaydi",
   exam_online._mock_section(exam_online._load(
       db.query(models.ExamTemplate).filter_by(kind="mock").first().parts)) or "?",
   "?")
ck("migratsiya belgini tiklaydi", mock_seed.backfill_skills(db) >= 1, True)
ck("tiklangach guruhlash to'g'ri",
   sorted({s["section"] for b in exam_online.mock_banks(db, _G())
           for s in b["sections"]}),
   ["listening", "reading", "speaking", "writing"])
db.close()
print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
sys.exit(1 if fails else 0)
