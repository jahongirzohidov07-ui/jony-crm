"""CHECKLIST — HR uchun bitta katta jadval (2026-09-26).

Jahongir: "checklist bo'limini ochib ber hr uchun, supportlarga ko'rgan
videolari va o'qigan kitobini o'tdi o'tmadi qilib bitta katta jadvalda
ko'rib tura olay".

Jadval: qatorda xodim (sukut bo'yicha supportlar), ustunda
  1) "Shaxsiy rivojlanish" videolari (pd_videos) — pleyer har 5 soniyada
     yozadi, "ko'rdi" belgisini SERVER qo'yadi (oxiriga tashlab yuborish
     foizni oshirmaydi). HR bu belgini qo'lda qo'ymaydi;
  2) HR kutubxonasi (library_items: video, kitob, fayl, havola) — xodim
     foizini o'zi yozadi, "o'tdi"ni HR qo'yadi. Jadvaldagi katakni bosish
     mavjud PUT /api/library/{id}/people/{user_id} ga boradi.

Yangi jadval yoki yangi pul mantiqi YO'Q — faqat mavjud ikki manbani
bitta ko'rinishga yig'adi. Ustun faqat shu lavozimga tegishli (target
roles) va faol yozuvlardan tuziladi.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import roles
from auth import require_role
from database import get_db

router = APIRouter()

# Kim ko'radi: asoschi/direktorlar, HR va support boshlig'i (o'z
# supportlarini kuzatadi). Katakni belgilash huquqi kutubxonaning
# o'zida (_LIB_MANAGE) — bu ro'yxat o'shaning ichida.
CHECKLIST_VIEW = list(dict.fromkeys(
    list(roles.FULL_ACCESS) + [roles.HR_MANAGER, roles.HEAD_SUPPORT]))
# CHECKLISTDAN TAHRIRLASH (2026-09-26, Jahongir: "shu yerni o'zidan
# o'zgartirib qo'sha olay"). Alohida endpoint yo'q — sahifa mavjud
# /api/library va /api/pd/videos ga yozadi, huquq ham o'shalarniki:
# kutubxona — HR, support boshlig'i va rahbarlar; avtomat kuzatiladigan
# video — faqat asoschi va HR (entry._PD_MANAGE).
PD_EDIT = [roles.FOUNDER, roles.HR_MANAGER]


def _targets(raw) -> list:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def _for_role(item, role: str) -> bool:
    t = _targets(getattr(item, "target_roles", None))
    return (not t) or (role in t)


def _people(db: Session, role: str, user, branch_id: Optional[int]) -> list:
    """Shu lavozimdagi faol xodimlar: asosiy lavozimi yoki QO'SHIMCHA
    lavozimi (user_roles) shu bo'lganlar."""
    extra = {uid for (uid,) in db.query(models.UserRole.user_id)
             .filter(models.UserRole.role == role).all()}
    q = db.query(models.User).filter(models.User.is_active == 1)
    us = [u for u in q.order_by(models.User.full_name).all()
          if u.role == role or u.id in extra]
    # Filial: tashkilot bo'yicha ishlaydiganlar hammasini, qolganlar
    # faqat o'z filialini ko'radi (kutubxona ro'yxati bilan bir xil).
    if user.role not in tuple(roles.ORG_WIDE_ROLES) and user.branch_id:
        us = [u for u in us if u.branch_id == user.branch_id]
    elif branch_id:
        us = [u for u in us if u.branch_id == branch_id]
    return us


@router.get("/api/hr/checklist")
def hr_checklist(role: str = roles.SUPPORT_TEACHER,
                 branch_id: Optional[int] = None,
                 db: Session = Depends(get_db),
                 user=Depends(require_role(*CHECKLIST_VIEW))):
    if role not in tuple(roles.STAFF_ROLES):
        raise HTTPException(400, "Noto'g'ri lavozim")
    PdV = getattr(models, "PdVideo", None)
    PdW = getattr(models, "PdWatch", None)
    LI = getattr(models, "LibraryItem", None)
    LP = getattr(models, "LibraryProgress", None)

    cols = []
    if PdV is not None:
        for v in (db.query(PdV).order_by(PdV.order_no, PdV.id).all()):
            if v.active and _for_role(v, role):
                cols.append({"key": f"pd:{v.id}", "source": "pd",
                             "id": v.id, "title": v.title,
                             "kind": "video", "kind_label": "Video",
                             "topic": v.topic or "",
                             "required": bool(v.required),
                             "targets": _targets(v.target_roles),
                             "url": (f"https://youtu.be/{v.yt_id}"
                                     if v.yt_id else None),
                             # 2026-10-10: HR qo'lda ham belgilay oladi
                             "can_mark": True})
    if LI is not None:
        labels = {"video": "Video", "book": "Kitob", "file": "Fayl",
                  "link": "Havola"}
        for it in (db.query(LI).order_by(LI.order_no, LI.id).all()):
            if it.active and _for_role(it, role):
                cols.append({"key": f"lib:{it.id}", "source": "lib",
                             "id": it.id, "title": it.title,
                             "kind": it.kind or "video",
                             "kind_label": labels.get(it.kind, it.kind),
                             "topic": "Kutubxona",
                             "required": bool(it.required),
                             "targets": _targets(it.target_roles),
                             "url": it.url,
                             "can_mark": True})

    people = _people(db, role, user, branch_id)
    ids = [u.id for u in people]
    pd_ids = [c["id"] for c in cols if c["source"] == "pd"]
    lib_ids = [c["id"] for c in cols if c["source"] == "lib"]
    pdw = {}
    if PdW is not None and ids and pd_ids:
        for w in (db.query(PdW).filter(PdW.user_id.in_(ids),
                                       PdW.video_id.in_(pd_ids)).all()):
            pdw[(w.user_id, w.video_id)] = w
    lpr = {}
    if LP is not None and ids and lib_ids:
        for p in (db.query(LP).filter(LP.user_id.in_(ids),
                                      LP.item_id.in_(lib_ids)).all()):
            lpr[(p.user_id, p.item_id)] = p

    branches = {b.id: b.name for b in db.query(models.Branch).all()}
    rows = []
    for u in people:
        cells = {}
        need = passed = 0
        for c in cols:
            if c["source"] == "pd":
                w = pdw.get((u.id, c["id"]))
                ok = bool(w is not None and w.done)
                pct = int(getattr(w, "percent", 0) or 0)
                at = (w.done_at.strftime("%d.%m.%Y")
                      if ok and getattr(w, "done_at", None) else None)
                by = getattr(w, "marked_by", None) if ok else None
            else:
                p = lpr.get((u.id, c["id"]))
                ok = bool(p is not None and p.passed)
                pct = int(getattr(p, "percent", 0) or 0)
                at = (p.passed_at.strftime("%d.%m.%Y")
                      if ok and getattr(p, "passed_at", None) else None)
                by = getattr(p, "passed_by", None) if ok else None
            if c["source"] == "pd":
                # Video: haqiqiy ko'rish foizi saqlanadi (qo'lda "o'tdi"
                # qilinsa ham necha foiz ko'rgani ko'rinib tursin)
                cells[c["key"]] = {"passed": ok, "percent": pct,
                                   "at": at, "by": by}
            else:
                cells[c["key"]] = {"passed": ok, "percent": 100 if ok else pct,
                               "at": at, "by": by}
            if c["required"]:
                need += 1
                passed += 1 if ok else 0
        rows.append({
            "user_id": u.id, "name": u.full_name or u.username,
            "role": roles.UZ_LABELS.get(u.role, u.role),
            "branch": branches.get(u.branch_id),
            "cells": cells, "required": need, "passed": passed,
            "percent": round(passed * 100 / need) if need else 0,
        })
    # O'tganlar TEPADA (2026-10-10, Jahongir: "o'tganlar pastda emas
    # yuqoriga chiqsin"): ko'p o'tgan birinchi, teng bo'lsa ism bo'yicha
    rows.sort(key=lambda r: (-r["percent"], -r["passed"], r["name"]))
    return {
        "role": role, "role_label": roles.UZ_LABELS.get(role, role),
        "columns": cols, "rows": rows,
        "roles": [{"key": r, "label": roles.UZ_LABELS.get(r, r)}
                  for r in roles.STAFF_ROLES],
        "summary": {
            "people": len(rows),
            "complete": len([r for r in rows
                             if r["required"] and r["passed"] == r["required"]]),
            "avg_percent": (round(sum(r["percent"] for r in rows) / len(rows))
                            if rows else 0),
        },
        "can_mark": user.role in tuple(CHECKLIST_VIEW),
        "can_edit_lib": user.role in tuple(CHECKLIST_VIEW),
        "can_edit_pd": user.role in tuple(PD_EDIT),
    }
