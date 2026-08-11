"""LC UP joriy coin balanslari bilan YAKUNIY tenglashtirish.

Jahongir: "qanday qilib LC updagi barcha oquvchilarni coinlarini eng
oson va tez usulda togrlab chiqish" - eng ishonchli usul tarixni yana
qazish emas, YAKUNIY balansni LC UP'dagi haqiqiy raqamga tenglash.

lcup_balance.json - 2026-08-11 kuni LC UP'ning o'zidan (har talaba
profilidan) brauzer orqali yig'ilgan snapshot: Zafar 1722, Bekobod 1
707, Bekobod 2 241, Stretinko 359 = 3029 talaba.

Mantiq: o'quvchining JonyOS'dagi joriy coin yig'indisi LC UP'dagi
tanga soniga teng bo'lmasa, FARQ miqdorida bitta "tenglashtirish"
yozuvi qo'shiladi (+/-). Tarix (imtihonlar, xaridlar, berilganlar)
o'z joyida qoladi - faqat yakuniy raqam to'g'rilanadi.

Ehtiyot choralari:
- MAIN'da barcha coin importlaridan KEYIN ishlaydi (tartib muhim)
- source="lcup_sync" + ref=LC UP talaba IDsi - idempotent, bir marta
- Bir xil ismli ikki JonyOS o'quvchisi -> tavakkal yo'q, o'tkaziladi
- Ikki LC UP yozuvi bitta JonyOS o'quvchisiga mos kelsa -> o'tkaziladi
- Topilmaganlar yozilmaydi, xulosa Auditda"""

import json
import os

import audit
import models
from sqlalchemy import func
from sqlalchemy.orm import Session

from legacy_coin_seed import _toks, _subset

_SOURCE = "lcup_sync"


def seed_lcup_balance(db: Session) -> int:
    path = os.path.join(os.path.dirname(__file__), "lcup_balance.json")
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8") as f:
        rows = json.load(f)["rows"]
    if not rows:
        return 0

    done = {rid for (rid,) in db.query(models.CoinEntry.ref_id)
            .filter(models.CoinEntry.source == _SOURCE).all()}
    todo = [r for r in rows if r[0] not in done]
    if not todo:
        return 0

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

    # LC UP -> JonyOS moslashtirish; bitta studentga ikki yozuv kelsa
    # ikkalasi ham o'tkaziladi (qaysi biri haqiqiy - aniqlab bo'lmaydi)
    m, dupes, unmatched = {}, set(), []
    for r in todo:
        sid = find(_toks(r[1]))
        if sid is None:
            unmatched.append(r[1])
            continue
        if sid in m:
            dupes.add(sid)
            continue
        m[sid] = r
    for sid in dupes:
        unmatched.append(m[sid][1] + " (ikkilangan)")
        del m[sid]
    if not m:
        return 0

    # Joriy balanslar bitta so'rovda
    bal = dict(db.query(models.CoinEntry.student_id,
                        func.coalesce(func.sum(models.CoinEntry.amount), 0))
               .filter(models.CoinEntry.student_id.in_(list(m.keys())))
               .group_by(models.CoinEntry.student_id).all())

    made, plus, minus = 0, 0, 0
    for sid, r in m.items():
        lcup_id, name, tanga, kristal, branch = r
        cur = int(bal.get(sid, 0))
        diff = int(tanga) - cur
        if diff == 0:
            continue
        note = (f"Balans LC UP bilan tenglashtirildi "
                f"(LC UP: {tanga} tanga"
                + (f", {kristal} kristal" if kristal else "")
                + f"; avvalgi hisob: {cur})")
        db.add(models.CoinEntry(
            student_id=sid, amount=diff, source=_SOURCE,
            ref_id=int(lcup_id), note=note[:200],
            created_by="Tenglashtirish (LC UP)"))
        made += 1
        if diff > 0:
            plus += diff
        else:
            minus += diff
    if made:
        db.commit()
        try:
            audit.log(
                db, None, entity="student", action="update",
                entity_label="Coin tenglashtirish (LC UP)",
                note=(f"{made} ta o'quvchi balansi LC UP snapshotiga "
                      f"(2026-08-11) tenglashtirildi: jami +{plus} / "
                      f"{minus}. Mos kelmagan {len(unmatched)} ism "
                      "yozilmadi"
                      + (": " + ", ".join(sorted(set(unmatched))[:30])
                         + "..." if unmatched else ".")),
                commit=True)
        except Exception:
            db.rollback()
    return made
