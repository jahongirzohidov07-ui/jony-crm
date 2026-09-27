"""MOCK SHABLONLARI: DUBLIKAT QOIDASI VA TIKLASH (2026-09-27).

Jahongir: "nega bu yerda IELTS da faqat listening turibdi, qolgani qani".

Sabab: exam_online dagi dublikat qoidasi mockni (daraja, tur, unit,
variant) bo'yicha solishtirardi — Listening A, Reading A, Writing A
bitta hisoblanib, Listening'dan boshqasi har startda yashirilardi.
Keyin mock seedi yashirilganlarni "yo'q" deb qayta yozar, qoida esa
yana yashirar edi: production loglarida har startda 69 ta yashirin
nusxa qo'shilayotgani ko'rindi.

Tekshiriladi:
  A. Toza baza — har (daraja, sarlavha) uchun aynan bitta faol shablon;
  B. Production holati (eski qoida + eski seed, uch start) — yangi kod
     hammasini tiklaydi, keyingi startlarda bitta ham yozuv qo'shilmaydi;
  C. Faqat "(dublikat)" nusxalar qolgan guruhda eng yangisi tiklanadi;
  D. Examiner ATAYLAB o'chirgan shablonga tegilmaydi, nusxa ham yozilmaydi;
  E. Parallel startdagi aniq dublikat baribir yashiriladi;
  F. Qayta yoqilgan "(dublikat)" nusxa asl bilan to'qnashsa — bittasi qoladi;
  G. Unit/Mid/End uchun eski qoida o'zgarmagan;
  H. Test bazasi ro'yxati tizim yashirgan nusxalarni sukut bo'yicha
     ko'rsatmaydi, examiner yashirganini ko'rsatadi;
  I. Startdagi audit qatori hamma bo'limlarni ko'rsatadi;
  J. canon_title;
  K. CEFR Speaking tarixi (production): eski 3 qismli C, E-I aynan shu
     nom bilan o'chirilgan — yangi 4 qismlisi yoziladi, 10 variant faol;
  L. Examinerning bitta nomli A/B/C parallel variantlari dublikat emas;
  M. Eski qoida yashirgan examiner mocki tiklanadi, ataylab o'chirgani yo'q;
  N. Guruhdagi yagona faol yozuv "(dublikat)" nomli — loop qaytmaydi;
  O. Unit/Mid/End yashirinlari Test bazasida avvalgidek ko'rinadi;
  P. Variant harfi A-Z (I-Q mock variantlarini saqlash mumkin).
"""
import json
import os
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

DB = os.path.join(tempfile.gettempdir(), "test_mock_dedup_repair.db")
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


FILES = mock_seed._files()
TITLES = {tpl["title"] for tpl in FILES}
PAIRS = {(lv, tpl["title"]) for tpl in FILES
         for lv in (tpl.get("levels") or [None])}


def active_per_pair():
    """Har (daraja, asl sarlavha) uchun nechta faol yozuv."""
    c = defaultdict(int)
    for t in db.query(T).filter(T.kind == "mock", T.is_active == 1).all():
        c[(t.level, mock_seed.canon_title(t.title))] += 1
    return c


def pairs_ok():
    """(yo'q juftliklar soni, ortiqcha faol juftliklar soni)."""
    c = active_per_pair()
    missing = [p for p in PAIRS if c.get(p, 0) == 0]
    extra = [p for p in PAIRS if c.get(p, 0) > 1]
    return len(missing), len(extra)


def total():
    return db.query(T).filter(T.kind == "mock").count()


def old_dedupe():
    """2026-09-27 gacha bo'lgan qoida — production'dagi xatoni takrorlash."""
    seen = {}
    for t in (db.query(T).filter(T.variant.isnot(None), T.is_active == 1)
              .order_by(T.id).all()):
        k = (t.level, t.kind, t.unit_no, t.variant)
        if k in seen:
            t.is_active = 0
            t.title = (t.title or "") + " (dublikat)"
        else:
            seen[k] = t.id
    db.commit()


_CLEAN = {}


def old_seed():
    """ec8a8c57 dagi seed: sarlavhani normallashtirmasdan solishtirardi.
    Mazmuni haqiqiy eski kod kabi to'liq (clean_parts) yoziladi — aks
    holda bo'lim belgisi yo'qolib, jadval "?" ko'rsatadi."""
    have = {(lv, ti) for lv, ti in db.query(T.level, T.title)
            .filter(T.kind == "mock").all()}
    for tpl in FILES:
        for lv in (tpl.get("levels") or [None]):
            if (lv, tpl["title"]) in have:
                continue
            if tpl["key"] not in _CLEAN:
                _CLEAN[tpl["key"]] = json.dumps(eo.clean_parts(tpl["parts"]),
                                                ensure_ascii=False)
            db.add(T(level=lv, kind="mock", unit_no=None, title=tpl["title"],
                     parts=_CLEAN[tpl["key"]],
                     paper_max=float(tpl.get("paper_max") or 0),
                     variant=tpl.get("variant") or "A",
                     subject="english", is_active=1, created_by="JonyOS"))
            have.add((lv, tpl["title"]))
    db.commit()


def new_start():
    """Yangi kod bilan bitta sovuq start: avval dublikat qoidasi
    (exam bank seedi ichida), keyin mock seedi — main.py dagi tartib."""
    eo.dedupe_templates(db)
    mock_seed.seed_mocks(db)


def sections(bank):
    out = eo.mock_banks(db=db, user=None)
    b = next((x for x in out if x["bank"] == bank), None)
    return {s["section"]: len(s["variants"]) for s in b["sections"]} if b else {}


# ----------------------------------------------------------------- J
print("=== J. canon_title ===")
ck("bitta qo'shimcha", mock_seed.canon_title("X — Variant A (dublikat)"),
   "X — Variant A")
ck("ikki marta qo'shilgan", mock_seed.canon_title("X (dublikat) (dublikat)"), "X")
ck("qo'shimchasiz o'zgarmaydi", mock_seed.canon_title("  X  "), "X")
ck("None", mock_seed.canon_title(None), "")

# ----------------------------------------------------------------- A
print("\n=== A. TOZA BAZA ===")
new_start()
n0 = total()
ck("yozuvlar soni fayllardagi juftliklarga teng", n0, len(PAIRS))
ck("har juftlikda aynan bitta faol (yo'q, ortiqcha)", pairs_ok(), (0, 0))
new_start()
ck("ikkinchi start hech narsa qo'shmaydi", total(), n0)

# ----------------------------------------------------------------- B
print("\n=== B. PRODUCTION HOLATI: ESKI QOIDA + ESKI SEED, UCH START ===")
for _ in range(3):
    old_dedupe()
    old_seed()
old_dedupe()                      # oxirgi start eski qoida bilan tugagan
broken = total()
print(f"    eski kod uch startdan keyin: {broken} yozuv "
      f"(+{broken - n0} yashirin nusxa)")
# Qaysi bo'lim "yutishi" yozilish tartibiga bog'liq: production'da
# Listening birinchi yozilgan edi, toza bazada esa Challenge IELTS'dan
# oldin yoziladi. Muhimi — to'rt bo'limdan kami faol.
ck("xato takrorlandi: IELTS'da to'rt bo'limdan kami faol",
   len(sections("ielts")) < 4, True)
new_start()
ck("yangi start: har juftlikda aynan bitta faol", pairs_ok(), (0, 0))
ck("IELTS to'rt bo'lim", sorted(sections("ielts")),
   ["listening", "reading", "speaking", "writing"])
ck("IELTS har bo'limda 5 variant",
   sorted(set(sections("ielts").values())), [5])
ck("CEFR to'rt bo'lim, Speaking 10 variant",
   sections("cefr"), {"listening": 3, "reading": 3, "speaking": 10, "writing": 3})
ck("Challenge 17 to'plam", sections("challenge25"), {"reading": 17})
after = total()
ck("tiklashda yangi yozuv qo'shilmadi (faqat qaytarildi)", after, broken)
new_start()
new_start()
ck("keyingi startlarda ham yozuv qo'shilmaydi (loop to'xtadi)", total(), after)
ck("va hech narsa yashirilmaydi", pairs_ok(), (0, 0))

# ----------------------------------------------------------------- C
print("\n=== C. FAQAT NUSXALAR QOLGAN GURUH — ENG YANGISI TIKLANADI ===")
lv, ti = sorted(p for p in PAIRS if "Reading" in p[1] and p[0])[0]
grp = [t for t in db.query(T).filter(T.kind == "mock", T.level == lv).all()
       if mock_seed.canon_title(t.title) == ti]
for t in grp:
    t.is_active = 0
    if not (t.title or "").endswith("(dublikat)"):
        t.title = t.title + " (dublikat)"
db.commit()
newest = max(t.id for t in grp)
new_start()
act = [t for t in db.query(T).filter(T.kind == "mock", T.level == lv,
                                     T.is_active == 1).all()
       if mock_seed.canon_title(t.title) == ti]
ck("guruhda bitta faol", len(act), 1)
ck("u eng yangi nusxa", act[0].id if act else None, newest)
ck("asl nomi qaytgan", act[0].title if act else None, ti)

# ----------------------------------------------------------------- D
print("\n=== D. EXAMINER ATAYLAB O'CHIRGANI ===")
lv_d, ti_d = sorted(p for p in PAIRS if "Writing" in p[1] and p[0])[1]
row = next(t for t in db.query(T).filter(T.kind == "mock", T.level == lv_d,
                                         T.title == ti_d, T.is_active == 1))
row.is_active = 0                  # nomi o'zgarmaydi — examiner yashirgan
db.commit()
before = total()
new_start()
new_start()
db.refresh(row)
ck("o'chirilgan holicha qoldi", row.is_active, 0)
ck("o'rniga yangi nusxa yozilmadi", total(), before)
ck("audit uni 'ataylab o'chirilgan' deb ko'rsatadi",
   f"@{lv_d}" in mock_seed.audit_off(db, TITLES), True)
row.is_active = 1
db.commit()

# ----------------------------------------------------------------- E
print("\n=== E. PARALLEL STARTDAGI ANIQ DUBLIKAT ===")
src = db.query(T).filter(T.kind == "mock", T.is_active == 1).order_by(T.id).first()
twin = T(level=src.level, kind="mock", unit_no=None, title=src.title,
         parts=src.parts, paper_max=src.paper_max, variant=src.variant,
         subject="english", is_active=1, created_by="JonyOS")
db.add(twin)
db.commit()
new_start()
db.refresh(src)
db.refresh(twin)
ck("eskisi qoladi", src.is_active, 1)
ck("yangisi yashiriladi", (twin.is_active, twin.title.endswith("(dublikat)")),
   (0, True))
ck("hammasi joyida", pairs_ok(), (0, 0))

# ----------------------------------------------------------------- F
print("\n=== F. QAYTA YOQILGAN NUSXA ===")
twin.is_active = 1                 # examiner "yashirin" nusxani yoqdi
db.commit()
new_start()
ck("baribir har juftlikda bitta faol", pairs_ok(), (0, 0))

# ----------------------------------------------------------------- G
print("\n=== G. UNIT/MID/END QOIDASI O'ZGARMAGAN ===")
u1 = T(level="elementary", kind="unit", unit_no=3, title="Unit 3 — A",
       parts="[]", paper_max=0, variant="A", subject="english", is_active=1)
u2 = T(level="elementary", kind="unit", unit_no=3, title="Unit 3 — boshqa nom",
       parts="[]", paper_max=0, variant="A", subject="english", is_active=1)
db.add_all([u1, u2])
db.commit()
eo.dedupe_templates(db)
db.refresh(u1)
db.refresh(u2)
ck("bir xil (daraja, unit, variant) — ikkinchisi yashirildi",
   (u1.is_active, u2.is_active), (1, 0))
m = db.query(T).filter(T.kind == "mock", T.is_active == 1,
                       T.level == "ielts_intro", T.variant == "A").count()
ck("mock: bir daraja + A harfi — bir necha bo'lim faol (to'qnashmaydi)",
   m >= 4, True)

# ----------------------------------------------------------------- H
print("\n=== H. TEST BAZASI RO'YXATI ===")
row.is_active = 0
db.commit()
lst = eo.list_templates(level=None, kind="mock", hidden=False, db=db, user=None)
ck("sukut bo'yicha tizim yashirgan nusxa ko'rinmaydi",
   sum(1 for x in lst if (x["title"] or "").endswith("(dublikat)")), 0)
ck("examiner yashirgani ko'rinadi", any(x["id"] == row.id for x in lst), True)
lst_all = eo.list_templates(level=None, kind="mock", hidden=True, db=db, user=None)
ck("hidden=True — hammasi", len(lst_all), total())
row.is_active = 1
db.commit()

# ----------------------------------------------------------------- I
print("\n=== I. AUDIT QATORI ===")
line = mock_seed.audit(db)
print("    " + line)
for sk in ("ielts_listening", "ielts_reading", "ielts_writing", "ielts_speaking",
           "cefr_listening", "cefr_reading", "cefr_writing", "cefr_speaking",
           "challenge25_reading"):
    ck(f"auditda {sk}", sk + "=" in line, True)

# ----------------------------------------------------------------- K
print("\n=== K. CEFR SPEAKING TARIXI (production'dagi holat) ===")
SPK = {tpl["variant"]: tpl for tpl in FILES
       if tpl["key"].startswith("mock_cefr_ml_speaking_")}
OLD3 = json.dumps([{"title": f"Part {i}", "instructions": "", "passage": "",
                    "questions": []} for i in (1, 2, 3)])


def old_title(v):
    return f"CEFR Multilevel Mock - Speaking - Variant {v}"


# E-I: 4 qismlisi production'da HECH QACHON yozilmagan
for v in "EFGHI":
    for t in db.query(T).filter(T.kind == "mock", T.level == "cefr",
                                T.variant == v).all():
        if mock_seed.canon_title(t.title) == SPK[v]["title"]:
            db.delete(t)
db.commit()
# Eski 3 qismlilar — ENG ESKI yozuvlar (manfiy id), migratsiya o'chirgan
nid = -1
for v in "ABCDEFGHIJ":
    # A, B, C ni eski dublikat qoidasi migratsiyadan oldin yashirgan
    ti = old_title(v) + (" (dublikat)" if v in "ABC" else "")
    db.add(T(id=nid, level="cefr", kind="mock", unit_no=None, title=ti,
             parts=OLD3, paper_max=75, variant=v, subject="english",
             is_active=0, created_by="JonyOS"))
    nid -= 1
db.commit()
# C ning 4 qismlisi oxirgi startda eski qoida bilan yashirilgan
for t in db.query(T).filter(T.kind == "mock", T.level == "cefr",
                            T.variant == "C", T.is_active == 1).all():
    if "Speaking" in (t.title or ""):
        t.is_active = 0
        t.title = t.title + " (dublikat)"
db.commit()


def spk_active():
    return [t for t in db.query(T).filter(T.kind == "mock", T.level == "cefr",
                                          T.is_active == 1).all()
            if "Speaking" in (t.title or "")]


ck("xato takrorlandi: faol CEFR Speaking — A, B, D, J",
   "".join(sorted(t.variant for t in spk_active())), "ABDJ")
new_start()
act = spk_active()
ck("CEFR Speaking — 10 variant faol",
   "".join(sorted(t.variant for t in act)), "ABCDEFGHIJ")
ck("hammasi yangi 4 qismli format (Part 1.1 bor)",
   all("Part 1.1" in [p.get("title") for p in eo._load(t.parts)] for t in act),
   True)
ck("eski 3 qismlilar nomi '(eski format)' — 10 ta",
   sum(1 for t in db.query(T).filter(T.kind == "mock", T.level == "cefr").all()
       if (t.title or "").endswith("(eski format)")), 10)
ck("eski 3 qismli birortasi ham faol emas",
   sum(1 for t in act if len(eo._load(t.parts)) == 3), 0)
ck("jadvalda Speaking 10", sections("cefr").get("speaking"), 10)
before_k = total()
new_start()
ck("keyingi start hech narsa qo'shmaydi", total(), before_k)

# ----------------------------------------------------------------- L
print("\n=== L. EXAMINERNING BITTA NOMLI PARALLEL VARIANTLARI ===")
exv = []
for v in "ABC":
    r = T(level="ielts_intro", kind="mock", unit_no=None,
          title="Jony Reading Mock", parts="[]", paper_max=0, variant=v,
          subject="english", is_active=1, created_by="examiner1")
    db.add(r)
    exv.append(r)
db.commit()
# Dublikat qoidasining O'ZI tekshiriladi: to'liq startda tiklash ularni
# qayta yoqib yuborib, noto'g'ri kalitni yashirib qo'yardi (har startda
# "yashir -> tikla" aylanishi).
hid = eo.dedupe_templates(db)
for r in exv:
    db.refresh(r)
ck("dublikat qoidasi ularga tegmaydi", [r.is_active for r in exv], [1, 1, 1])
ck("bu startda hech narsa yashirilmadi", hid, 0)
new_start()
for r in exv:
    db.refresh(r)
ck("to'liq startdan keyin ham A, B, C faol", [r.is_active for r in exv],
   [1, 1, 1])
ck("nomlari o'zgarmadi", {r.title for r in exv}, {"Jony Reading Mock"})

# ----------------------------------------------------------------- M
print("\n=== M. ESKI QOIDA YASHIRGAN EXAMINER MOCKI ===")
victim = T(level="ielts_intro", kind="mock", unit_no=None,
           title="Examiner Speaking Mock (dublikat)", parts="[]", paper_max=9,
           variant="D", subject="english", is_active=0, created_by="examiner1")
off = T(level="ielts_intro", kind="mock", unit_no=None,
        title="Examiner Old Mock", parts="[]", paper_max=9,
        variant="A", subject="english", is_active=0, created_by="examiner1")
db.add_all([victim, off])
db.commit()
new_start()
db.refresh(victim)
db.refresh(off)
ck("noto'g'ri yashirilgani tiklandi",
   (victim.is_active, victim.title), (1, "Examiner Speaking Mock"))
ck("examiner ataylab o'chirgani o'chiq qoldi", off.is_active, 0)

# ----------------------------------------------------------------- N
print("\n=== N. YAGONA FAOL YOZUV '(dublikat)' NOMLI ===")
lv_n, ti_n = sorted(p for p in PAIRS if "Reading" in p[1]
                    and "IELTS" in p[1] and p[0])[3]
grp = [t for t in db.query(T).filter(T.kind == "mock", T.level == lv_n,
                                     T.is_active == 1).all()
       if mock_seed.canon_title(t.title) == ti_n]
ck("guruhda bitta faol", len(grp), 1)
grp[0].title = ti_n + " (dublikat)"      # masalan ?hidden=true dan qayta yoqilgan
db.commit()
before_n = total()
for _ in range(3):
    new_start()
ck("uch startda bitta ham yozuv qo'shilmadi", total(), before_n)
ck("guruhda hamon bitta faol",
   sum(1 for t in db.query(T).filter(T.kind == "mock", T.level == lv_n,
                                     T.is_active == 1).all()
       if mock_seed.canon_title(t.title) == ti_n), 1)

# ----------------------------------------------------------------- O
print("\n=== O. UNIT/MID/END YASHIRINLARI KO'RINADI ===")
lst_u = eo.list_templates(level="elementary", kind="unit", hidden=False,
                          db=db, user=None)
ck("unit '(dublikat)' yozuvi sukut bo'yicha ham ro'yxatda",
   any(x["id"] == u2.id for x in lst_u), True)

# ----------------------------------------------------------------- P
print("\n=== P. VARIANT HARFI A-Z ===")
ck("I va Q qabul qilinadi",
   (eo._clean_variant("i"), eo._clean_variant("Q")), ("I", "Q"))
try:
    eo._clean_variant("1")
    ck("raqam rad etiladi", False, True)
except eo.HTTPException:
    ck("raqam rad etiladi", True, True)

print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
db.close()
sys.exit(1 if fails else 0)
