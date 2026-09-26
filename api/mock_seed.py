# -*- coding: utf-8 -*-
"""MOCK TEST BAZASI (2026-09-26).

Jahongir: "sen shularni 1x1 kopya qilmaysan, sen xuddi shu pattern va
uslubdagi Mock testlar tuzib berasan haqiqiy IELTS CDI testlari bilan
1x1 kopya bo'lishi kerak ... va katta mock test bazasini yarat".

Shuning uchun bu yerdagi HAMMA matn — Jony Academy uchun yangidan
yozilgan: Cambridge kitoblaridan birorta gap ham ko'chirilmagan.
Ko'chirilgani faqat FORMAT: bo'limlar soni, savollar soni, savol
turlari, ko'rsatma matnlari va band jadvali.

  mock_data/<imtihon>/*.json — ielts/ va cefr/ papkalari. Har fayl
  bitta bo'lim (Listening / Reading / Writing / Speaking) va bitta
  variant. Fayl ichida:
    key      — seed kaliti (bir marta yoziladi, keyin examiner tahrirlaydi)
    section  — listening | reading | writing | speaking
    variant  — A..E
    levels   — qaysi guruh darajalariga yoziladi
    parts    — exam_online.clean_parts kutadigan ko'rinishda

  Bir daraja + "mock" ichida bir xil TUZILISHdagi variantlar avtomat
  aralashadi (exam_online.mix_parts): Listening A ning 1-qismi, C ning
  2-qismi... — ustoz qaysi savollar tushishini oldindan bilolmaydi.
  IELTS Listening (10,10,10,10), IELTS Reading (13,13,14), CEFR
  Listening (8,6,4,5,6,6), CEFR Reading (6,8,6,9,6), Writing va
  Speaking tuzilishlari boshqa-boshqa, shuning uchun ular o'zaro
  aralashmaydi.

  CEFR Multilevel: darajasi "cefr". Kitoblarda xom balldan CEFR
  darajasiga RASMIY o'tkazish jadvali yo'q (ikkala qo'llanma ham
  mytests.uz ga yo'naltiradi), shuning uchun avtomat band yozilmaydi —
  examiner xom ballni ko'rib darajani o'zi qo'yadi (exam_online.
  _write_result). IELTS Listening/Reading uchun esa rasmiy jadval bor.
"""
import json
import os

from sqlalchemy.orm import Session

import models
from common import _seed_done, _seed_mark

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_data")


def _files() -> list:
    """mock_data ichidagi har papka bitta imtihon turi: ielts, cefr, ..."""
    if not os.path.isdir(DIR):
        return []
    out = []
    for sub in sorted(os.listdir(DIR)):
        d = os.path.join(DIR, sub)
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.endswith(".json"):
                continue
            with open(os.path.join(d, name), encoding="utf-8") as fh:
                tpl = json.load(fh)
            # Har bo'limga "ielts_listening" / "cefr_reading" kabi aniq
            # ko'nikma belgisi qo'yiladi: xom ballni qaysi jadval
            # bo'yicha bandga o'girishni shu hal qiladi. Bo'lim nomiga
            # tayanib bo'lmaydi — IELTS Listening bo'limlari ham
            # shunchaki "Part 1" deb nomlangan.
            skill = f"{sub}_{tpl.get('section') or ''}".strip("_")
            for part in tpl.get("parts") or []:
                part.setdefault("skill", skill)
            out.append(tpl)
    return out


def seed_mocks(db: Session) -> None:
    """Mock shablonlarini bazaga bir marta yozadi. Kalit belgilangach
    qayta yozilmaydi — examinerlar boshlig'i CRM'da o'zi tahrirlaydi."""
    import exam_online as _eo

    # ESKI CEFR SPEAKING (bir martalik, 2026-09-26). Avvalgi Speaking
    # shablonlari IELTS uslubida 3 qismli edi; rasmiy Multilevel
    # formati 4 qismli (Part 1.1 / 1.2 / 2 / 3). Eskilari bazada
    # qolib ketmasin — yashiriladi, o'chirilmaydi (examiner kerak
    # bo'lsa Test bazasidan qaytarib yoqa oladi).
    if not _seed_done(db, "cefr_speaking_old_off_v1"):
        try:
            import exam_online as _eo
            n = 0
            for t in (db.query(models.ExamTemplate)
                      .filter(models.ExamTemplate.kind == "mock",
                              models.ExamTemplate.level == "cefr",
                              models.ExamTemplate.is_active == 1).all()):
                parts = _eo._load(t.parts)
                titles = [str(p.get("title") or "") for p in parts]
                if "Speaking" in (t.title or "") and "Part 1.1" not in titles:
                    t.is_active = 0
                    n += 1
            db.commit()
            if n:
                print(f"[seed] eski CEFR Speaking shablonlari yashirildi: {n}")
            _seed_mark(db, "cefr_speaking_old_off_v1")
        except Exception as e:          # noqa: BLE001
            db.rollback()
            print(f"[seed] eski CEFR Speaking: {e}")

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
