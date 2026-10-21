"""LISTENING: SAVOL TARTIBI BIR XIL, VARIANTLAR HAR XIL (2026-10-21).

Jahongir: "listening savol ketma ketligi bir xil bo'lsin variantlari
xar xil bo'lsin hammada".

Bazadagi listening bo'limlarining ko'pida audio ham, skript ham yo'q
(audioni examiner sinfda qo'yadi) — ilgari ular oddiy bo'lim deb
savollari aralashtirilardi va o'quvchi audio ketma-ketligini
yo'qotardi. Tekshiriladi (haqiqiy baza shablonlarida, 30 o'quvchi):
  1. Listening bo'limida savollar tartibi HAMMADA bir xil.
  2. Javob variantlari o'quvchilarda har xil; baholash to'g'ri.
  3. Listening bo'lmagan (grammatika) bo'lim avvalgidek aralashadi.
  4. Skriptli (examiner o'qiydigan) listening ham qotib turadi.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import exam_bank_seed                              # noqa: E402
import exam_online as eo                           # noqa: E402

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


def listening_idx(parts):
    return [i for i, p in enumerate(parts)
            if "listening" in str(p.get("title") or "").lower()]


keys = [k for k, tpl in exam_bank_seed.TEMPLATES
        if listening_idx(tpl.get("parts") or [])]
ck("bazada listeningli shablonlar bor", len(keys) > 10, True)

bad_order, opt_differs, other_shuffled, grade_bad = [], 0, 0, []
seeds = [f"talaba-{i}" for i in range(30)]
for key, tpl in exam_bank_seed.TEMPLATES:
    if key not in keys:
        continue
    parts = eo.clean_parts(tpl["parts"])
    pub = eo.public_parts(parts)
    li = listening_idx(parts)
    views = [eo.shuffle_for(pub, parts, s) for s in seeds]
    for i in li:
        base = [q["id"] for q in pub[i]["questions"]]
        if any([q["id"] for q in v[i]["questions"]] != base for v in views):
            bad_order.append(key)
        opts = {tuple(tuple(q.get("options") or []) for q in v[i]["questions"])
                for v in views}
        if len(opts) > 1:
            opt_differs += 1
    for i in range(len(pub)):
        if i in li or pub[i].get("passage") or len(pub[i]["questions"]) < 3:
            continue
        orders = {tuple(q["id"] for q in v[i]["questions"]) for v in views}
        if len(orders) > 1:
            other_shuffled += 1
    # Baholash: har o'quvchi aralash variantda to'g'ri javobni tanlasa —
    # to'liq ball (javob ASL raqamda saqlanadi)
    qmap = {q["id"]: q for q in eo._questions(parts)}
    for v in views[:5]:
        ans = {}
        for p in v:
            for q in p["questions"]:
                orig = qmap[q["id"]]
                if q.get("type") == "choice" and "opt" in q:
                    ans[q["id"]] = q["opt"][q["opt"].index(orig["answer"])]
                elif q.get("type") == "text" and isinstance(
                        orig.get("answer"), list):
                    ans[q["id"]] = orig["answer"][0]
                elif orig.get("answer") is not None:
                    ans[q["id"]] = orig["answer"]
        sc, tot, _ = eo.grade(parts, ans)
        if sc != tot:
            grade_bad.append(key)
            break

ck("1. listening savol tartibi hammada bir xil", sorted(set(bad_order)), [])
ck("2. listening variantlari o'quvchilarda har xil", opt_differs > 10, True)
ck("2. aralash variantda baholash to'g'ri", grade_bad, [])
ck("3. boshqa bo'limlar avvalgidek aralashadi", other_shuffled > 10, True)

print("\n=== 4. SKRIPTLI LISTENING (variant fayli) ===")
p = {"title": "Part 1", "script": "Hello ...", "questions": [
    {"id": f"q{i}", "n": i, "type": "choice", "q": f"Savol {i}",
     "options": ["apple", "banana", "cherry"], "answer": 0}
    for i in range(1, 8)]}
pub = eo.public_parts([p])
orders = {tuple(q["id"] for q in eo.shuffle_for(pub, [p], s)[0]["questions"])
          for s in seeds}
ck("skriptli bo'lim tartibi bir xil", len(orders), 1)

print()
if fails:
    print(f"XATO: {len(fails)} ta tekshiruv o'tmadi")
    for x in fails:
        print("   - " + x)
    sys.exit(1)
print("HAMMASI O'TDI")
sys.exit(0)
