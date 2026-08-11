"""Coin do'koni xaridlari importi (LC UP "daromadlar" eksporti).

Jahongir: "Coinga narsa olganlar bor shu jadvalda" - o'quvchilar coin
evaziga narsa olgan (33% chegirma, Smartwatch, Jony bakal...), bu
coinlar balansdan YECHILISHI kerak.

MUHIM: xaridlarning katta qismi (225 ta) avvalgi coins_crystal
eksportida allaqachon manfiy "Daromad" yozuvi bo'lib kirgan - ularni
qayta kiritsak ikki marta yechilardi. Shu bois lokalda solishtirilib:
- faqat eski eksportda AKS ETMAGAN 117 ta xarid yangi yozuv bo'ladi
  (source="legacy_shop", ref=Excel qatori, idempotent)
- allaqachon kirganlarining esa mavjud yozuvi izohi boyitiladi
  ("Daromad" -> "Coin do'koni: Smartwatch — ...") - tarix tushunarli

Ism-moslashtirish legacy_coin_seed bilan bir xil: arxivdagilarga ham
yoziladi, topilmagan/ikkilangan ismlar o'tkazib yuboriladi."""

import json
import os
from datetime import datetime

import audit
import models
from sqlalchemy.orm import Session

from legacy_coin_seed import _toks, _subset

_SOURCE = "legacy_shop"


def seed_legacy_shop(db: Session) -> int:
    from common import _seed_done, _seed_mark
    if _seed_done(db, "legacy_shop_v1"):
        return 0
    path = os.path.join(os.path.dirname(__file__), "legacy_shop.json")
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    made = 0

    # ---- 1) Yangi xarid yozuvlari (idempotent, ref bo'yicha)
    done = {rid for (rid,) in db.query(models.CoinEntry.ref_id)
            .filter(models.CoinEntry.source == _SOURCE).all()}
    todo = [r for r in (data.get("new") or []) if r[0] not in done]
    if todo:
        students = db.query(models.Student).all()
        exact, prepared = {}, []
        for s in students:
            tk = _toks(s.full_name or "")
            if not tk:
                continue
            exact.setdefault(tk, []).append(s.id)
            prepared.append((s.id, tk))

        def find(tk):
            hits = exact.get(tk)
            if hits and len(hits) == 1:
                return hits[0]
            if hits:
                return None
            cands = []
            for sid, t in prepared:
                if len(t) < 2 or len(tk) < 2:
                    continue
                if _subset(t, tk) or _subset(tk, t):
                    cands.append(sid)
                    if len(cands) > 1:
                        return None
            return cands[0] if len(cands) == 1 else None

        unmatched = []
        for ref, name, amount, label, ts in todo:
            sid = find(_toks(name))
            if sid is None:
                unmatched.append(name)
                continue
            try:
                when = datetime.strptime(ts, "%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                when = datetime.utcnow()
            db.add(models.CoinEntry(
                student_id=sid, amount=int(amount), source=_SOURCE,
                ref_id=int(ref), note=label[:200],
                created_by="Import (coin do'koni)", created_at=when))
            made += 1
        if made:
            db.commit()
            try:
                audit.log(db, None, entity="student", action="update",
                          entity_label="Coin do'koni importi",
                          note=(f"{made} ta xarid yozuvi kiritildi "
                                f"(coin yechildi). "
                                + (f"Topilmagan {len(unmatched)}: "
                                   + ", ".join(sorted(set(unmatched))[:25])
                                   if unmatched else "Hammasi topildi.")),
                          commit=True)
            except Exception:
                db.rollback()

    # ---- 2) Avvalgi "Daromad" yozuvlari izohini boyitish (bir marta)
    ann = data.get("annotate") or []
    if ann:
        refs = [a[0] for a in ann]
        rows = {e.ref_id: e for e in db.query(models.CoinEntry)
                .filter(models.CoinEntry.source == "legacy_coin",
                        models.CoinEntry.ref_id.in_(refs)).all()}
        changed = 0
        for ref, label in ann:
            e = rows.get(ref)
            # faqat hali boyitilmagan (Daromad...) yozuvlar
            if e is not None and (e.note or "").startswith("Daromad"):
                e.note = label[:200]
                changed += 1
        if changed:
            db.commit()
    _seed_mark(db, "legacy_shop_v1")
    return made
