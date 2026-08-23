"""
INTERAKTIV O'RGATUVCHI — "shu yerni bosasan" (2026-08-23).

Jahongir: "yangi xodim kirsa toliq demo yani onboarding qilinsin
avtomat, shu yerga kirsang shunday qilasan deb korsatib tursin
yozuvlar bilan... profil bolimida mening funksiyalarim bolimi
bolsa, shu funksiyalarni qaysini qilishni bilmasa shuni bosadi,
programma avtomat test rejimida... shu yerni bosasan deb strelkalar
turib hammasini korsatib turishi kerak".

NIMA QILADI. Xodim birinchi marta kirganda o'rgatuvchi taklif
qiladi: ekranda strelka chiqadi, kerakli tugmani ko'rsatadi, matn
bilan tushuntiradi va XODIMNING O'ZI bosadi. Har bir dars — bitta
haqiqiy ish (to'lov qabul qilish, yo'qlama qo'yish, muzlatish...).

XAVFSIZLIK. Mashq TEST FILIALIDA ketadi: dars boshlanganda tizim
global filialni test filialiga o'tkazadi, tugagach avvalgisini
qaytaradi. Xodim tugmani haqiqatdan bosadi va natijani ko'radi —
lekin haqiqiy o'quvchi va haqiqiy pulga tegilmaydi.

BU FAYL faqat HOLATNI saqlaydi: qaysi dars tugagan, taklif
ko'rsatilganmi, mashq uchun qaysi filial. Darslarning o'zi (matn,
strelka qayerga tushishi) frontendda — src/lib/guide/lessons.ts.
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Body, Depends
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import Session

import models
import roles
from auth import get_current_user
from common import ensure_tables
from database import Base, get_db

router = APIRouter()

# ---- jadval (create_all faqat yo'q jadvalni yaratadi) ----
if getattr(models, "GuideProgress", None) is None:
    class GuideProgress(Base):
        """Kim qaysi darsni tugatgani. Bitta qator = bitta dars."""

        __tablename__ = "guide_progress"
        __table_args__ = {"extend_existing": True}

        id = Column(Integer, primary_key=True, index=True)
        user_id = Column(Integer, index=True, nullable=False)
        lesson_id = Column(String, index=True, nullable=False)
        # done — tugatdi; skipped — "keyinroq" dedi
        state = Column(String, default="done")
        created_at = Column(DateTime, default=datetime.utcnow)

    models.GuideProgress = GuideProgress
    ensure_tables([GuideProgress.__table__])

_G = models.GuideProgress

# Taklif oynasi ko'rsatilganini belgilaydigan maxsus "dars"
INTRO_KEY = "__intro__"


def _test_branch_id(db: Session) -> int | None:
    """Mashq uchun filial — nomida "test" so'zi bor birinchisi.
    Bo'lmasa None (o'rgatuvchi baribir ishlaydi, faqat filial
    almashtirilmaydi)."""
    for b in db.query(models.Branch).order_by(models.Branch.id).all():
        if "test" in (b.name or "").lower():
            return b.id
    return None


@router.get("/api/guide/state")
def guide_state(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """O'rgatuvchi holati: nima tugagan, taklif ko'rsatilganmi."""
    rows = db.query(_G).filter(_G.user_id == user.id).all()
    done = sorted({r.lesson_id for r in rows
                   if r.state == "done" and r.lesson_id != INTRO_KEY})
    seen_intro = any(r.lesson_id == INTRO_KEY for r in rows)
    return {
        "role": user.role,
        "role_label": roles.UZ_LABELS.get(user.role, user.role),
        "done": done,
        "intro_seen": seen_intro,
        "test_branch_id": _test_branch_id(db),
    }


@router.post("/api/guide/done")
def guide_done(payload: dict = Body(default={}),
               db: Session = Depends(get_db),
               user=Depends(get_current_user)):
    """Dars tugadi (yoki taklif ko'rsatildi) — belgilab qo'yamiz."""
    lid = str(payload.get("lesson_id") or "").strip()[:64]
    if not lid:
        return {"ok": False}
    state = "skipped" if payload.get("skipped") else "done"
    row = (db.query(_G).filter(_G.user_id == user.id,
                               _G.lesson_id == lid).first())
    if row:
        # "keyinroq" degan dars keyin tugallansa — holati yangilanadi
        if row.state != "done":
            row.state = state
    else:
        db.add(_G(user_id=user.id, lesson_id=lid, state=state))
    db.commit()
    return {"ok": True, "lesson_id": lid, "state": state}


@router.delete("/api/guide/done")
def guide_reset(lesson_id: str | None = None,
                db: Session = Depends(get_db),
                user=Depends(get_current_user)):
    """Qaytadan o'rganmoqchi — belgini olib tashlaymiz.
    lesson_id berilmasa — hammasi (o'rgatuvchini boshidan)."""
    q = db.query(_G).filter(_G.user_id == user.id)
    if lesson_id:
        q = q.filter(_G.lesson_id == lesson_id)
    n = q.delete(synchronize_session=False)
    db.commit()
    return {"ok": True, "removed": n}
