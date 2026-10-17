"""LUG'AT BANKI — so'zlar faylini yig'ish (2026-10-16).

NIMA QILADI. Tarjima partiyalari (batch_*.json) va mavjud lug'atdan
olingan qoralama (existing.json) birlashtirilib, server o'qiydigan
yagona fayl yoziladi: api/wordbank_data/words.json. Server uni startda
wordbank.load_words bilan yuklaydi (lemma bo'yicha upsert, hech narsa
o'chirilmaydi; belgi fayl mazmunidan — fayl o'zgarsa qayta yuklanadi).

QOIDALAR.
  * kalit — (rank, band, lemma); tartib: avval existing.json, keyin
    batch_*.json tabiiy tartibda (batch_2 < batch_10). Keyingi manba
    shu lemmaning yozuvini TO'LIQ almashtiradi (qayta qoralama);
  * skip=true yoki uz_primary bo'sh — faylga tushmaydi;
  * --candidates berilsa (vocab/candidates.json, muzlatilgan 20 000):
    rank/band o'sha ro'yxatdan olinadi, ro'yxatda yo'q lemma tashlanadi;
    berilmasa band = (rank-1)//1000 + 1 (har darajada 1000 so'z);
  * bir rank'ga ikki lemma tushsa — birinchisi qoladi (hisobotda).

USTQATLAMLAR (OVERLAYS, 2026-10-17). existing + batch'lardan keyin
<src>/fix papkasidan (yoki --fix) shu tartibda qo'llanadi:
  (a) mature_*.json — yetuk mavzudagi lemmalar (egasi qarori: jinsiy
      mazmun, qon/o'lim tafsiloti, giyohvandlik, haqoratlar, odobsiz
      so'zlar; millat/din sifatlari QOLADI) — qator butunlay tushadi.
      Ko'rinish: ["lemma", ...], {lemma: {"status": "removed"}} yoki
      [{"lemma": ..., "status": "removed"}];
  (b) dups_fix.json, keyin dups_fix_<n>.json — {lemma: {"uz_primary":
      ...}}: bir darajadagi bir xil tarjimalarni ajratish (va noto'g'ri
      ma'noni tuzatish); skip=true — qator tushadi;
  (c) examples_*.json — {lemma: {"example_uz": ...}} (tabiiy tartibda);
      misolsiz qolgan qator uchun "example_en" ham berilishi mumkin.
      (b) va (c) (d)dagi to'ldiruvchi qatorlarga ham qo'llanadi;
  (d) refill_<n>.json — bo'sh qolgan o'rinlarni to'ldiruvchi so'zlar
      (20 000 dan keyingi chastota ro'yxatidan; skip=true — tushadi).
      Har biri BO'SH rank'ga qo'yiladi (DESIGN §9: "refill disabled
      slots"; rank daraja ichida qoladi, 20 000 dan oshmaydi — aks holda
      "rank tartibida" yangi so'z berishda 1-darajadagi to'ldiruvchi
      20-darajadan keyin chiqardi). refill_candidates.json dagi slot_rank
      bo'sh bo'lsa — o'sha o'rin; qolganlari (reserve) — eng quyi
      darajadan boshlab qolgan bo'sh o'rinlarga. O'rinlar (a)–(e) dan
      KEYIN hisoblanadi, shuning uchun (e)da bo'shagan o'rin ham to'ladi;
  (e) BAD_LEMMAS — chastota ro'yxatidagi buzuq lemmalar (re-set,
      over-take ...): to'g'ri shakl shu nomzodning forms ro'yxatida
      bo'lsa — lemma o'sha shaklga almashtiriladi (rank/daraja/tarjima
      saqlanadi), aks holda qator tushadi.
Ustqatlam bazada yo'q lemmaga tegsa — hisobotda ("topilmadi").

LINT (2026-10-16, review; DESIGN §9 "zero errors required"). Xato bo'lsa
fayl YOZILMAYDI (--force bilan yoziladi, --check esa 1 bilan chiqadi):
  * har darajada aniq 1000 so'z (skip / tarjimasiz qator o'rni bo'sh qoladi);
  * example_en bor va unda lemma shakli bor — server bilan BIR XIL qoida
    (api/wordbank_core.gap_forms): aks holda yozib topishda misol chiqmaydi;
  * misolda lemma bilan boshlangan boshqa so'z yo'q (sun/sunglasses,
    volt/voltage) — u javobni ochib qo'yadi;
  * bir darajada bir xil uz_primary yo'q (sense farq qilsa — mumkin):
    aks holda yozib topishda o'zbekcha so'zdan qaysi lemma so'ralgani
    noaniq. Ogohlantirish (yozishni to'xtatmaydi): example_uz bo'sh,
    misolda lemmaning bir nechta shakli.

Ishga tushirish (repo ildizidan):
  python scripts/wordbank_merge.py --src <wbdata papkasi> \
      --candidates <vocab/candidates.json> [--out api/wordbank_data/words.json]
  --fix <papka> — ustqatlamlar papkasi (standart: <src>/fix, bo'lsa);
  --no-fix — ustqatlamlarsiz (eski xatti-harakat).
  --check — faqat hisobot, fayl yozilmaydi (lint xatosi bo'lsa chiqish 1).
  --force — lint xatolari bo'lsa ham yozadi (faqat sinov uchun).
"""
import argparse
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "api", "wordbank_data", "words.json")
BANDS = 20
PER_BAND = 1000

sys.path.insert(0, os.path.join(ROOT, "api"))
import wordbank_core as WC  # noqa: E402 — bo'shliq qoidasi serverdagi bilan bir xil


def _natural(path):
    name = os.path.basename(path)
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name)]


def _entries(data):
    """{"words": [...]}, {"items": [...]}, [...] yoki {lemma: {...}}."""
    if isinstance(data, dict):
        for k in ("words", "items", "entries"):
            if isinstance(data.get(k), list):
                return data[k]
        out = []
        for lemma, e in data.items():
            if isinstance(e, dict):
                e = dict(e)
                e.setdefault("lemma", lemma)
                out.append(e)
        return out
    return data if isinstance(data, list) else []


def _txt(v):
    if isinstance(v, (list, tuple)):
        v = next((x for x in v if isinstance(x, str) and x.strip()), None)
    if v is None or isinstance(v, (dict, bool)):
        return ""
    return str(v).strip()


def _int(v):
    if isinstance(v, bool):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _alts(v):
    if isinstance(v, str):
        v = [v]
    if not isinstance(v, list):
        return []
    out = []
    for a in v:
        a = a.strip() if isinstance(a, str) else ""
        if a and a not in out:
            out.append(a)
    return out


def load_sources(src):
    files = []
    ex = os.path.join(src, "existing.json")
    if os.path.exists(ex):
        files.append(ex)
    files += sorted(glob.glob(os.path.join(src, "batch_*.json")), key=_natural)
    if not files:
        sys.exit(f"Manba topilmadi: {src} (existing.json / batch_*.json)")
    merged, per_file = {}, []
    for f in files:
        with open(f, encoding="utf-8-sig") as fh:
            items = _entries(json.load(fh))
        n = 0
        for e in items:
            if not isinstance(e, dict):
                continue
            lemma = _txt(e.get("lemma"))
            if not lemma:
                continue
            prev = merged.get(lemma)
            e = dict(e)
            # partiya rank/band yozmagan bo'lsa — oldingi manbadan
            for k in ("rank", "band"):
                if _int(e.get(k)) is None and prev is not None:
                    e[k] = prev.get(k)
            e["_src"] = os.path.basename(f)
            merged[lemma] = e
            n += 1
        per_file.append((os.path.basename(f), n))
    return merged, per_file


# --------------------------------------------------- ustqatlamlar ---
# 2026-10-17: chastota ro'yxatidagi buzuq lemmalar -> to'g'ri shakl.
# Tarjima va misol to'g'ri shakl uchun yozilgan ("Reset your password",
# "won first prize"), lemma esa wordfreq/lemmatizator buzgani — shuning
# uchun yozib topishda misol chiqmasdi. To'g'ri shakl nomzodning forms
# ro'yxatida bo'lsa — almashtiriladi, aks holda (school-child: forms da
# faqat "schoolchildren") qator tushadi.
BAD_LEMMAS = {"prise": "prize", "re-set": "reset", "over-take": "overtake",
              "over-ride": "override", "school-child": "schoolchild",
              "mini-bus": "minibus"}


def _read_json(path):
    with open(path, encoding="utf-8-sig") as fh:
        return json.load(fh)


def _removed(data):
    """mature_*.json -> lemmalar. status berilgan bo'lsa — faqat removed."""
    if isinstance(data, dict):
        data = [dict(v, lemma=k) if isinstance(v, dict) else {"lemma": k}
                for k, v in data.items()]
    out = []
    for x in data if isinstance(data, list) else []:
        if isinstance(x, str):
            x = {"lemma": x}
        if not isinstance(x, dict):
            continue
        lem = _txt(x.get("lemma"))
        if lem and _txt(x.get("status")).lower() in ("", "removed"):
            out.append(lem)
    return out


def _patches(data):
    """{lemma: {...}} yoki [{"lemma": ..., ...}] -> {lemma: patch}."""
    out = {}
    for e in _entries(data):
        if isinstance(e, dict) and _txt(e.get("lemma")):
            out[_txt(e.get("lemma"))] = e
    return out


def load_overlays(fix):
    ov = {"mature": [], "dups": {}, "examples": {}, "refill": {},
          "slots": {}, "files": []}

    def files(pat, rx=None):
        out = sorted(glob.glob(os.path.join(fix, pat)), key=_natural)
        return [f for f in out
                if rx is None or re.fullmatch(rx, os.path.basename(f))]

    for f in files("mature_*.json"):
        got = _removed(_read_json(f))
        ov["mature"] += [x for x in got if x not in ov["mature"]]
        ov["files"].append((os.path.basename(f), len(got)))
    # dups_fix.json, keyin dups_fix_<n>.json (tabiiy tartibda; keyingisi
    # shu lemmaning oldingi tuzatishini almashtiradi)
    for f in files("dups_fix*.json", r"dups_fix(_\d+)?\.json"):
        got = _patches(_read_json(f))
        ov["dups"].update(got)
        ov["files"].append((os.path.basename(f), len(got)))
    for f in files("examples_*.json"):
        got = _patches(_read_json(f))
        ov["examples"].update(got)
        ov["files"].append((os.path.basename(f), len(got)))
    # refill_candidates.json / refill_excluded.json — qator emas
    for f in files("refill_*.json", r"refill_\d+\.json"):
        got = _patches(_read_json(f))
        ov["refill"].update(got)
        ov["files"].append((os.path.basename(f), len(got)))
    p = os.path.join(fix, "refill_candidates.json")
    if os.path.exists(p):
        ov["slots"] = _patches(_read_json(p))
    return ov


def _example_patch(e, p):
    """examples_*.json yozuvidan o'zgaradigan maydonlar: example_uz va
    (bor bo'lsa) example_en — misolsiz qolgan qatorlar uchun ikkalasi."""
    out = {}
    for k in ("example_en", "example_uz"):
        v = _txt(p.get(k))
        if v and v != _txt(e.get(k)):
            out[k] = v
    return out


def apply_overlays(merged, ov, canon=None, forms=None):
    """(a)–(e) ni merged ga qo'llaydi (joyida). canon (nusxa) ham joyida
    yangilanadi (almashtirilgan lemma). Qaytaradi: (to'ldiruvchilar
    [(lemma, yozuv)], hisobot {tur: [namuna]})."""
    rep = defaultdict(list)
    gone = set(ov["mature"])
    refill = ov["refill"]
    for lem in ov["mature"]:                                    # (a)
        if merged.pop(lem, None) is not None:
            rep["(a) mature: olib tashlandi"].append(lem)
        elif lem not in refill:
            rep["(a) mature: bazada yo'q"].append(lem)
    for lem, p in ov["dups"].items():                           # (b)
        e = merged.get(lem)
        if e is None:
            if lem not in gone and lem not in refill:
                rep["(b) dups_fix: topilmadi"].append(lem)
            continue
        if p.get("skip"):
            del merged[lem]
            rep["(b) dups_fix: skip (tushdi)"].append(lem)
            continue
        uz = _txt(p.get("uz_primary"))
        if uz and uz != _txt(e.get("uz_primary")):
            merged[lem] = dict(e, uz_primary=uz)
            rep["(b) dups_fix: uz_primary"].append(lem)
    for lem, p in ov["examples"].items():                       # (c)
        e = merged.get(lem)
        if e is None:
            if lem not in gone and lem not in ov["dups"] \
                    and lem not in refill:
                rep["(c) examples: topilmadi"].append(lem)
            continue
        new = _example_patch(e, p)
        if new:
            merged[lem] = dict(e, **new)
            for k in new:
                rep[f"(c) examples: {k}"].append(lem)
    pool = []                                                   # (d)
    for lem, p in refill.items():
        # (b)/(c) to'ldiruvchi qatorga ham tegadi (bir darajadagi bir xil
        # tarjima ko'pincha to'ldiruvchi bilan mavjud so'z orasida chiqadi)
        d = ov["dups"].get(lem)
        if d is not None:
            if d.get("skip"):
                p = dict(p, skip=True)
                rep["(b) dups_fix: to'ldiruvchi skip"].append(lem)
            elif _txt(d.get("uz_primary")) and \
                    _txt(d.get("uz_primary")) != _txt(p.get("uz_primary")):
                p = dict(p, uz_primary=_txt(d.get("uz_primary")))
                rep["(b) dups_fix: to'ldiruvchi uz_primary"].append(lem)
        x = ov["examples"].get(lem)
        if x is not None:
            new = _example_patch(p, x)
            if new:
                p = dict(p, **new)
                rep["(c) examples: to'ldiruvchi"].append(lem)
        if p.get("skip") or not _txt(p.get("uz_primary")):
            rep["(d) refill: skip"].append(lem)
        elif lem in gone:
            rep["(d) refill: mature (tushdi)"].append(lem)
        elif lem in merged or lem in BAD_LEMMAS.values():
            rep["(d) refill: lemma allaqachon bor"].append(lem)
        else:
            s = ov["slots"].get(lem) or {}
            slot = _int(s.get("slot_rank"))
            e = dict(p, lemma=lem, _src="refill", _slot=slot,
                     _reserve=bool(s.get("reserve")) or slot is None,
                     _orig=_int(p.get("rank")) or 10 ** 9)
            pool.append((lem, e))
    for bad, good in BAD_LEMMAS.items():                        # (e)
        e = merged.pop(bad, None)
        if e is None:
            continue
        if forms is not None and good in forms.get(bad, ()) \
                and good not in merged:
            merged[good] = dict(e, lemma=good)
            if canon is not None and bad in canon:
                canon[good] = canon[bad]
            rep["(e) buzuq lemma: tuzatildi"].append(f"{bad} -> {good}")
        else:
            rep["(e) buzuq lemma: tushdi"].append(bad)
    return pool, rep


def place_refill(merged, canon, pool, rep):
    """To'ldiruvchilarni BO'SH rank'larga qo'yadi (merged/canon joyida).
    Avval refill_candidates dagi slot_rank (bo'sh bo'lsa), keyin o'z
    darajasidagi bo'sh o'rin (zaxira emaslar), qolganlari — eng quyi
    darajadan boshlab. O'rin qolmasa — qo'yilmaydi (hisobotda)."""
    rows = build(merged, canon)[0]
    rank_band = ({rk: bd for rk, bd in canon.values()} if canon is not None
                 else {})

    def band_of(rk):
        return rank_band.get(rk) or (rk - 1) // PER_BAND + 1

    free = sorted(set(range(1, BANDS * PER_BAND + 1))
                  - {r["rank"] for r in rows})
    free_set = set(free)
    pool = sorted(pool, key=lambda kv: (kv[1]["_reserve"], kv[1]["_orig"]))
    placed = {}

    def put(lem, e, rk):
        free_set.discard(rk)
        bd = band_of(rk)
        merged[lem] = dict(e, rank=rk, band=bd)
        if canon is not None:
            canon[lem] = (rk, bd)
        placed[lem] = rk
        rep["(d) refill: bo'sh o'ringa qo'yildi"].append(f"{lem}@{rk}")

    for lem, e in pool:                       # 1) o'zining slot_rank'i
        if e["_slot"] in free_set:
            put(lem, e, e["_slot"])
    for lem, e in pool:                       # 2) o'z darajasida bo'sh o'rin
        if lem in placed or e["_reserve"]:
            continue
        want = _int(e.get("band"))
        rk = next((r for r in free if r in free_set and band_of(r) == want),
                  None)
        if rk is not None:
            put(lem, e, rk)
    for lem, e in pool:                       # 3) qolgan bo'sh o'rinlar
        if lem in placed:
            continue
        rk = next((r for r in free if r in free_set), None)
        if rk is None:
            rep["(d) refill: o'rin qolmadi (zaxirada)"].append(lem)
            continue
        put(lem, e, rk)
    return placed


def build(merged, canon=None):
    rep = Counter()
    unknown, fixed = [], []
    rows = []
    for lemma, e in merged.items():
        if e.get("skip"):
            rep["skip"] += 1
            continue
        uz = _txt(e.get("uz_primary"))
        if not uz:
            rep["empty_uz"] += 1
            continue
        rank, band = _int(e.get("rank")), _int(e.get("band"))
        if canon is not None:
            c = canon.get(lemma)
            if c is None:
                unknown.append(lemma)
                continue
            if (rank, band) != c:
                fixed.append((lemma, rank, band, c))
                rank, band = c
        else:
            if rank is None or rank <= 0:
                unknown.append(lemma)
                continue
            want = (rank - 1) // PER_BAND + 1
            if band != want:
                fixed.append((lemma, rank, band, (rank, want)))
                band = want
        if not 1 <= band <= BANDS:
            unknown.append(lemma)
            continue
        rows.append({
            "rank": rank, "band": band, "lemma": lemma,
            "pos": _txt(e.get("pos")) or None,
            "uz_primary": uz,
            "uz_alt": [a for a in _alts(e.get("uz_alt")) if a != uz],
            "example_en": _txt(e.get("example_en")) or None,
            "example_uz": _txt(e.get("example_uz")) or None,
        })
    rows.sort(key=lambda r: (r["rank"], r["lemma"]))
    out, seen, dup = [], {}, []
    for r in rows:
        if r["rank"] in seen:
            dup.append((r["rank"], seen[r["rank"]], r["lemma"]))
            continue
        seen[r["rank"]] = r["lemma"]
        out.append(r)
    return out, rep, unknown, fixed, dup


def _uz_key(s):
    s = (s or "").replace("’", "'").replace("‘", "'") \
        .replace("`", "'").lower()
    return re.sub(r"\s+", " ", s).strip(" .,;:!?\"'")


def lint(rows, merged):
    """2026-10-16 (review): DESIGN §9 lint. (xatolar, ogohlantirishlar) —
    ikkalasi ham {tur: [namuna, ...]}."""
    err, warn = defaultdict(list), defaultdict(list)
    same_uz = defaultdict(list)
    for r in rows:
        lem, en = r["lemma"], r["example_en"] or ""
        if not en:
            err["example_en yo'q"].append(lem)
        else:
            forms = WC.gap_forms(lem, en)
            if not forms:
                err["misolda lemma shakli yo'q (yozib topishda misol "
                    "chiqmaydi)"].append(f"{lem}: {en}")
            elif len(forms) > 1:
                warn["misolda lemmaning bir nechta shakli"].append(
                    f"{lem}: {forms}")
            longer = sorted({m.group(0) for m in re.finditer(
                r"(?<![A-Za-z])" + re.escape(lem) + r"[A-Za-z]+", en, re.I)
                if m.group(0).lower() not in forms})
            if longer:
                err["misolda javobni ochadigan uzun so'z"].append(
                    f"{lem}: {longer}")
        if not r["example_uz"]:
            warn["example_uz bo'sh"].append(lem)
        sense = _txt((merged.get(lem) or {}).get("sense"))
        same_uz[(r["band"], _uz_key(r["uz_primary"]), sense)].append(lem)
    for (band, uz, _s), lems in sorted(same_uz.items(),
                                       key=lambda kv: (kv[0][0], kv[0][1])):
        if len(lems) > 1:
            err["bir darajada bir xil uz_primary (sense yo'q)"].append(
                f"{band}: {uz} = {'/'.join(lems)}")
    per_band = Counter(r["band"] for r in rows)
    for b in range(1, BANDS + 1):
        if per_band.get(b, 0) != PER_BAND:
            err[f"darajada {PER_BAND} so'z emas"].append(
                f"{b}: {per_band.get(b, 0)}")
    return err, warn


def _show(title, groups, n=8):
    if not groups:
        return
    print(title)
    for kind, items in groups.items():
        print(f"  {kind}: {len(items)}")
        for x in items[:n]:
            print(f"      {x}")


def write(rows, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write('{"lexicon": "en-v1", "count": %d, "words": [\n' % len(rows))
        for i, r in enumerate(rows):
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")))
            f.write(",\n" if i + 1 < len(rows) else "\n")
        f.write("]}\n")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--src", required=True,
                    help="existing.json va batch_*.json papkasi")
    ap.add_argument("--candidates", help="vocab/candidates.json (20 000)")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--check", action="store_true",
                    help="faqat hisobot, fayl yozilmaydi")
    ap.add_argument("--force", action="store_true",
                    help="lint xatolari bo'lsa ham yozish (faqat sinov)")
    ap.add_argument("--fix", help="ustqatlamlar papkasi (standart: <src>/fix)")
    ap.add_argument("--no-fix", action="store_true",
                    help="ustqatlamlarsiz (faqat existing + batch)")
    a = ap.parse_args()

    canon = forms = None
    if a.candidates:
        with open(a.candidates, encoding="utf-8") as fh:
            cands = json.load(fh)
        canon = {c["lemma"]: (int(c["rank"]), int(c["band"]))
                 for c in cands}
        forms = {c["lemma"]: {str(f).lower() for f in c.get("forms") or []}
                 for c in cands}
    merged, per_file = load_sources(a.src)
    n_src = len(merged)
    fix = None if a.no_fix else (a.fix or os.path.join(a.src, "fix"))
    if fix and not os.path.isdir(fix):
        if a.fix:
            sys.exit(f"--fix papkasi topilmadi: {fix}")
        fix = None
    orep, placed = {}, {}
    if fix:
        ov = load_overlays(fix)
        per_file += ov["files"]
        pool, orep = apply_overlays(merged, ov, canon, forms)
        placed = place_refill(merged, canon, pool, orep)
    rows, rep, unknown, fixed, dup = build(merged, canon)

    print("Manbalar:")
    for name, n in per_file:
        print(f"  {name}: {n}")
    print(f"Birlashgan lemma: {n_src}" + (
        f" -> ustqatlamlardan keyin {len(merged)}" if fix else ""))
    if fix:
        print(f"Ustqatlamlar ({fix}):")
        for kind, items in orep.items():
            print(f"  {kind}: {len(items)}  {items[:6]}")
        pb = Counter((rk - 1) // PER_BAND + 1 for rk in placed.values())
        print("  to'ldiruvchilar darajalar bo'yicha: " + "  ".join(
            f"{b}:{pb[b]}" for b in range(1, BANDS + 1) if pb[b]))
    print(f"Faylga: {len(rows)}  | skip: {rep['skip']}  | tarjimasiz: "
          f"{rep['empty_uz']}  | ro'yxatda yo'q/yaroqsiz: {len(unknown)}  "
          f"| rank/band tuzatildi: {len(fixed)}  | rank dublikati: {len(dup)}")
    if unknown:
        print("  ro'yxatda yo'q (namuna):", unknown[:10])
    if fixed:
        print("  tuzatilgan (namuna):", fixed[:5])
    if dup:
        print("  dublikat rank (namuna):", dup[:5])
    per_band = Counter(r["band"] for r in rows)
    print("Darajalar (so'z / 1000):")
    print("  " + "  ".join(f"{b}:{per_band.get(b, 0)}"
                           for b in range(1, BANDS + 1)))
    err, warn = lint(rows, merged)
    _show("Lint ogohlantirishlari:", warn)
    _show("Lint XATOLARI (DESIGN §9 — nol bo'lishi shart):", err)
    if a.check:
        print("--check: fayl yozilmadi")
        sys.exit(1 if err else 0)
    if err and not a.force:
        sys.exit("Lint xatolari bor — fayl YOZILMADI (sinov uchun: --force). "
                 "Server to'liq bo'lmagan darajani baribir ochmaydi.")
    write(rows, a.out)
    print(f"Yozildi: {a.out} ({os.path.getsize(a.out) // 1024} KB)")


if __name__ == "__main__":
    main()
