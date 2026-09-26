# -*- coding: utf-8 -*-
"""MOCK TEST BAZASI (2026-09-26).

Jahongir: "sen shularni 1x1 kopya qilmaysan, sen xuddi shu pattern va
uslubdagi Mock testlar tuzib berasan haqiqiy IELTS CDI testlari bilan
1x1 kopya bo'lishi kerak ... va katta mock test bazasini yarat".

Shuning uchun bu yerdagi HAMMA matn — Jony Academy uchun yangidan
yozilgan: Cambridge kitoblaridan birorta gap ham ko'chirilmagan.
Ko'chirilgani faqat FORMAT: bo'limlar soni, savollar soni, savol
turlari, ko'rsatma matnlari va band jadvali.

  mock_data/ielts/*.json — har fayl bitta bo'lim (Listening / Reading /
  Writing / Speaking) va bitta variant (A-E). Fayl ichida:
    key      — seed kaliti (bir marta yoziladi, keyin examiner tahrirlaydi)
    section  — listening | reading | writing | speaking
    variant  — A..E
    levels   — qaysi guruh darajalariga yoziladi
    parts    — exam_online.clean_parts kutadigan ko'rinishda

  Bir daraja + "mock" ichida bir xil TUZILISHdagi variantlar avtomat
  aralashadi (exam_online.mix_parts): Listening A ning 1-qismi, C ning
  2-qismi... — ustoz qaysi savollar tushishini oldindan bilolmaydi.
  Listening (10,10,10,10), Reading (13,13,14), Writing (1,1) va
  Speaking (1,1,1) tuzilishlari boshqa-boshqa, shuning uchun ular
  o'zaro aralashmaydi.
"""
import json
import os

from sqlalchemy.orm import Session

import models
from common import _seed_done, _seed_mark

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "mock_data", "ielts")


def _files() -> list:
    if not os.path.isdir(DIR):
        return []
    out = []
    for name in sorted(os.listdir(DIR)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(DIR, name), encoding="utf-8") as fh:
            out.append(json.load(fh))
    return out


def seed_mocks(db: Session) -> None:
    """Mock shablonlarini bazaga bir marta yozadi. Kalit belgilangach
    qayta yozilmaydi — examinerlar boshlig'i CRM'da o'zi tahrirlaydi."""
    import exam_online as _eo

    for tpl in _files():
        parts = None
        for level in (tpl.get("levels") or [None]):
            key = f"{tpl['key']}_{level or 'all'}"
            if _seed_done(db, key):
                continue
            exists = db.query(models.ExamTemplate).filter(
                models.ExamTemplate.level == level,
                models.ExamTemplate.kind == "mock",
                models.ExamTemplate.title == tpl["title"]).first()
            if not exists:
                if parts is None:
                    parts = _eo.clean_parts(tpl["parts"])
                db.add(models.ExamTemplate(
                    level=level,
                    kind="mock",
                    unit_no=None,
                    title=tpl["title"],
                    parts=json.dumps(parts, ensure_ascii=False),
                    paper_max=float(tpl.get("paper_max") or 0),
                    variant=tpl.get("variant") or "A",
                    subject="english",
                    is_active=1,
                    created_by="JonyOS"))
                db.commit()
            _seed_mark(db, key)
