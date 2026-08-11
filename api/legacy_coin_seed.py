"""Eski (Crystal) tizimdagi coin tarixini import qilish.

Jahongir: "Coinlarni qoshish kerak, menda polniy tarixi bor" va
"topilmagan o'quvchilarga qoyilmasin, agar shu oquvchi arxivda bo'lsa
arxivdagi o'quvchiga qoshish kerak".

legacy_coins.json - Excel eksportidan tayyorlangan (faqat "coins"
turi; "crystal" qatorlari coinsning hosilasi bo'lgani uchun ataylab
olinmadi - ikki marta hisoblanib qolardi). Har yozuv o'z sanasi va
sababi bilan CoinEntry bo'lib yoziladi, balans avtomat to'g'ri
chiqadi (balans = yozuvlar yig'indisi).

Qoidalar:
- O'quvchi ISM bo'yicha topiladi (faylda telefon yo'q). Yozilish
  farqlariga chidamli: apostroflar, x/h, katta-kichik, "o'g'li/qizi"
  suffikslari, token tartibi. Bitta aniq nomzod bo'lsagina yoziladi -
  ikki xil o'quvchiga birdek mos kelsa xato yozmasdan o'tkaziladi.
- ARXIVDAGI o'quvchiga ham yoziladi (status filtri yo'q).
- Topilmaganlar shunchaki o'tkazib yuboriladi (vazifa YO'Q -
  Jahongir shunday so'radi), xulosa auditga yoziladi.
- source="legacy_coin" + ref_id=Excel T/R - idempotent, takror
  yozilmaydi."""

import json
import os
from datetime import datetime

import audit
import models
from sqlalchemy.orm import Session

_SOURCE = "legacy_coin"
_SUFFIX = {"ogli", "qizi", "qiz", "ugli", "kizi"}
_APOS = "ʻ‘’'`"


def _norm(tok: str) -> str:
    t = tok.lower()
    for ch in _APOS:
        t = t.replace(ch, "")
    t = t.replace("x", "h").replace("dj", "j").replace("o", "a")
    out = []
    for ch in t:
        if not out or out[-1] != ch:
            out.append(ch)
    return "".join(c for c in out if c.isalpha())


def _toks(name: str) -> tuple:
    out = []
    for raw in (name or "").split():
        t = _norm(raw)
        if t and t not in _SUFFIX:
            out.append(t)
    return tuple(sorted(out))


def _tok_match(a: str, b: str) -> bool:
    if a == b:
        return True
    if len(a) >= 4 and len(b) >= 4 and (a.startswith(b) or b.startswith(a)):
        return True
    return False


def _subset(small: tuple, big: tuple) -> bool:
    """small'ning har tokeni big'da o'z juftini topadimi."""
    used = set()
    for a in small:
        hit = None
        for i, b in enumerate(big):
            if i in used:
                continue
            if _tok_match(a, b):
                hit = i
                break
        if hit is None:
            return False
        used.add(hit)
    return True


def seed_legacy_coins(db: Session) -> int:
    path = os.path.join(os.path.dirname(__file__), "legacy_coins.json")
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["rows"]
    if not rows:
        return 0

    done = {rid for (rid,) in db.query(models.CoinEntry.ref_id)
            .filter(models.CoinEntry.source == _SOURCE).all()}
    todo = [r for r in rows if r[0] not in done]
    if not todo:
        return 0

    # O'quvchilar indeksi - ARXIV ham kiradi (Jahongir talabi)
    students = db.query(models.Student).all()
    exact = {}
    prepared = []
    for s in students:
        tk = _toks(s.full_name or "")
        if not tk:
            continue
        exact.setdefault(tk, []).append(s.id)
        prepared.append((s.id, tk))

    def find(name_toks):
        if not name_toks:
            return None
        hits = exact.get(name_toks)
        if hits and len(hits) == 1:
            return hits[0]
        if hits and len(hits) > 1:
            return None  # bir xil ismli ikki o'quvchi - tavakkal yo'q
        cands = []
        for sid, tk in prepared:
            if len(tk) < 2 or len(name_toks) < 2:
                continue
            if _subset(tk, name_toks) or _subset(name_toks, tk):
                cands.append(sid)
                if len(cands) > 1:
                    return None
        return cands[0] if len(cands) == 1 else None

    resolved = {}
    unmatched = set()
    for ix, nm in enumerate(data["names"]):
        sid = find(_toks(nm))
        if sid is None:
            unmatched.add(ix)
        else:
            resolved[ix] = sid

    notes = data["notes"]
    payload = []
    skipped = 0
    touched = set()
    for tr, ni, amount, ci, ts in todo:
        sid = resolved.get(ni)
        if sid is None:
            skipped += 1
            continue
        try:
            when = datetime.strptime(ts, "%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            when = datetime.utcnow()
        payload.append({
            "student_id": sid,
            "amount": int(amount),
            "source": _SOURCE,
            "ref_id": int(tr),
            "note": (notes[ci][:200] if notes[ci] else None),
            "created_by": "Import (eski tizim)",
            "created_at": when,
        })
        touched.add(sid)

    if payload:
        db.bulk_insert_mappings(models.CoinEntry, payload)
        db.commit()
        try:
            miss = [data["names"][i] for i in sorted(unmatched)]
            audit.log(
                db, None, entity="student", action="update",
                entity_label="Coin importi (eski tizim)",
                note=(f"{len(payload)} ta coin yozuvi "
                      f"{len(touched)} ta o'quvchiga kiritildi. "
                      + (f"Topilmagan {len(miss)} ism (yozilmadi): "
                         + ", ".join(miss[:40])
                         + ("..." if len(miss) > 40 else "")
                         if miss else "Barcha ismlar topildi.")),
                commit=True)
        except Exception:
            db.rollback()
    return len(payload)
