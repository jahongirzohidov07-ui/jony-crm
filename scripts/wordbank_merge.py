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
    a = ap.parse_args()

    canon = None
    if a.candidates:
        with open(a.candidates, encoding="utf-8") as fh:
            canon = {c["lemma"]: (int(c["rank"]), int(c["band"]))
                     for c in json.load(fh)}
    merged, per_file = load_sources(a.src)
    rows, rep, unknown, fixed, dup = build(merged, canon)

    print("Manbalar:")
    for name, n in per_file:
        print(f"  {name}: {n}")
    print(f"Birlashgan lemma: {len(merged)}")
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
