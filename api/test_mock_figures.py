"""MOCK RASMLARI: XARITA VA GRAFIKLAR (2026-09-27).

Jahongir: "listeningda map debsan qani map", "bar Chartingni rasmi qani".
Listening xarita/plan savollari (IELTS A-E, CEFR A-C) va IELTS Writing
Task 1 (A-E) figuralari ilgari faqat so'z bilan tasvirlangan edi.

Production holati qayta yaratiladi: bazada git HEAD'dagi ESKI fayllardan
yozilgan shablonlar (prefiksli, so'z-tavsifli, rasmsiz). Tekshiriladi:
  A. Yangi fayllar: 13 ta rasm, hammasi xavfsiz SVG data-URI, clean_parts
     ularni qabul qiladi; so'z-tavsif olib tashlangan;
  B. Startup migratsiyasi: rasm qo'shiladi, eski tavsifli matn yangisiga
     almashadi, savol id/javoblari o'zgarmaydi;
  C. Examiner o'zgartirgan matnga tegilmaydi, lekin rasm qo'shiladi;
  D. Ikkinchi start hech narsa o'zgartirmaydi;
  E. O'quvchiga boradigan nusxada rasm bor, javob yo'q.
"""
import base64
import io
import json
import os
import subprocess
import sys
import tempfile
from xml.etree import ElementTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

DB = os.path.join(tempfile.gettempdir(), "test_mock_figures.db")
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
    print(("OK  " if ok else "XATO ") + name + f": {str(got)[:160]}"
          + ("" if ok else f"   (kutilgan {str(want)[:160]})"))
    if not ok:
        fails.append(name)


SPEC = json.load(io.open(mock_seed.FIGURES_SPEC, encoding="utf-8"))
FILES = {tpl["title"]: tpl for tpl in mock_seed._files()}
REL = {}
for sub in ("ielts", "cefr"):
    for name in os.listdir(os.path.join(HERE, "mock_data", sub)):
        t = json.load(io.open(os.path.join(HERE, "mock_data", sub, name),
                              encoding="utf-8"))
        REL[t["title"]] = f"api/mock_data/{sub}/{name}"


def head_version(title):
    raw = subprocess.run(["git", "-C", REPO, "show", f"HEAD:{REL[title]}"],
                         capture_output=True, check=True).stdout
    return json.loads(raw.decode("utf-8"))


def old_db_parts(head_tpl):
    """Eski kod yozgan ko'rinish: clean_parts (o'sha paytda prefikslarni
    tozalamasdi) — shuning uchun savol matni/variantlar HEAD'dan olinadi."""
    parts = eo.clean_parts(head_tpl["parts"])
    for p, hp in zip(parts, head_tpl["parts"]):
        for q, hq in zip(p["questions"], hp["questions"]):
            q["q"] = str(hq.get("q") or "").strip()
            if q.get("options"):
                q["options"] = [str(o).strip() for o in hq.get("options") or []
                                if str(o).strip()]
    return parts


# ----------------------------------------------------------------- A
print("=== A. YANGI FAYLLAR ===")
FIG = [s for s in SPEC
       if FILES[s["title"]]["parts"][s["part"]]["questions"][s["q"]].get("image")]
ck("13 ta figura (5 Writing + 8 Listening)", len(FIG), 13)
ck("Writing ko'rsatmalari (10 qism) takrorlanmaydi — bo'sh",
   sorted({FILES[s["title"]]["parts"][s["part"]]["instructions"]
           for s in SPEC if "Writing" in s["title"]}), [""])
imgs, bad, desc_left = 0, [], []
for s in FIG:
    tpl = FILES[s["title"]]
    q = tpl["parts"][s["part"]]["questions"][s["q"]]
    img = q.get("image") or ""
    if img.startswith("data:image/svg+xml;base64,"):
        imgs += 1
        svg = base64.b64decode(img.split(",", 1)[1]).decode("utf-8")
        root = ElementTree.fromstring(svg)
        tags = {el.tag.split("}")[-1] for el in root.iter()}
        if tags & {"script", "image", "foreignObject"} or "href=\"http" in svg:
            bad.append(s["title"])
    blob = (tpl["parts"][s["part"]].get("instructions") or "") + (q.get("q") or "")
    for marker in ("lettered positions", "DESCRIPTION OF THE TWO MAPS",
                   "(given in words)", "BAR CHART —", "DATA (each pie",
                   "described in full below"):
        if marker in blob:
            desc_left.append((s["title"], marker))
ck("hammasida SVG rasm", imgs, 13)
ck("SVG xavfsiz (script/tashqi havola yo'q)", bad, [])
ck("so'z-tavsif olib tashlangan", desc_left, [])
ck("clean_parts rasmlarni qabul qiladi",
   all(eo.clean_parts(FILES[s["title"]]["parts"])[s["part"]]["questions"][s["q"]]
       .get("image") for s in FIG), True)

# ----------------------------------------------------------------- B
print("\n=== B. PRODUCTION'DAGI ESKI SHABLONLAR MIGRATSIYASI ===")
ROWS = {}
for title in dict.fromkeys(s["title"] for s in SPEC):
    head = head_version(title)
    for lv in head.get("levels") or [None]:
        r = T(level=lv, kind="mock", title=title,
              parts=json.dumps(old_db_parts(head), ensure_ascii=False),
              variant=head.get("variant") or "A", subject="english",
              is_active=1, created_by="JonyOS")
        db.add(r)
        db.commit()
        ROWS.setdefault(title, []).append(r.id)

# Examiner tahrirlagan qator: IELTS Listening A, bitta daraja
edited_title = "IELTS Mock · Listening — Variant A"
edited = db.query(T).get(ROWS[edited_title][0])
ep = eo._load(edited.parts)
ep[1]["instructions"] = ep[1]["instructions"] + "\n(examiner izohi)"
edited.parts = json.dumps(ep, ensure_ascii=False)
db.commit()
before_ids = {rid: [(q["id"], q["n"], q["type"], q.get("answer"))
                    for p in eo._load(db.query(T).get(rid).parts)
                    for q in p["questions"]]
              for ids in ROWS.values() for rid in ids}

mock_seed.seed_mocks(db)
db.expire_all()

no_img, text_diff = [], []
for s in SPEC:
    src = eo.clean_parts(FILES[s["title"]]["parts"])
    for rid in ROWS[s["title"]]:
        parts = eo._load(db.query(T).get(rid).parts)
        q = parts[s["part"]]["questions"][s["q"]]
        if q.get("image") != src[s["part"]]["questions"][s["q"]].get("image"):
            no_img.append((s["title"], rid))
        if rid == edited.id:
            continue
        if "instructions" in s["old"]:
            if parts[s["part"]]["instructions"] != src[s["part"]]["instructions"]:
                text_diff.append((s["title"], "instructions"))
        if "q" in s["old"] and q["q"] != src[s["part"]]["questions"][s["q"]]["q"]:
            text_diff.append((s["title"], "q"))
ck("har qatorda rasm (fayldagi bilan bir xil)", no_img, [])
ck("eski tavsifli matn yangisiga almashdi", text_diff, [])
after_ids = {rid: [(q["id"], q["n"], q["type"], q.get("answer"))
                   for p in eo._load(db.query(T).get(rid).parts)
                   for q in p["questions"]]
             for ids in ROWS.values() for rid in ids}
ck("savol id, n, tur va javoblar o'zgarmadi", after_ids == before_ids, True)
n_rows = sum(len(v) for v in ROWS.values())
ck("yangi nusxa yozilmadi (daraja+sarlavha bor edi)",
   db.query(T).filter(T.title.in_(list(ROWS)), T.is_active == 1).count(), n_rows)

# ----------------------------------------------------------------- C
print("\n=== C. EXAMINER TAHRIRI ===")
ep2 = eo._load(db.query(T).get(edited.id).parts)
ck("tahrirlangan matnga tegilmadi",
   ep2[1]["instructions"].endswith("(examiner izohi)"), True)
ck("lekin rasm qo'shildi", bool(ep2[1]["questions"][6].get("image")), True)

# ----------------------------------------------------------------- D
print("\n=== D. IKKINCHI START ===")
snap = {r.id: r.parts for r in db.query(T).filter(T.title.in_(list(ROWS))).all()}
mock_seed.seed_mocks(db)
db.expire_all()
ck("hech narsa o'zgarmadi",
   {r.id: r.parts for r in db.query(T).filter(T.title.in_(list(ROWS))).all()} == snap,
   True)

# ----------------------------------------------------------------- E
print("\n=== E. O'QUVCHI NUSXASI ===")
rid = ROWS["IELTS Mock · Writing — Variant A"][0]
pub = eo.public_parts(eo._load(db.query(T).get(rid).parts))
ck("Writing Task 1 rasmi o'quvchiga boradi",
   (pub[0]["questions"][0].get("image") or "")[:26], "data:image/svg+xml;base64,")
ck("Writing matni toza (raqamsiz, tavsifsiz)",
   pub[0]["questions"][0]["q"].splitlines()[0], "WRITING TASK 1")
rid = ROWS["IELTS Mock · Listening — Variant C"][0]
pub = eo.public_parts(eo._load(db.query(T).get(rid).parts))
ck("Listening xaritasi o'quvchiga boradi",
   bool(pub[1]["questions"][6].get("image")), True)
ck("javob kaliti yo'q", any("answer" in q for p in pub for q in p["questions"]),
   False)

print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
db.close()
sys.exit(1 if fails else 0)
