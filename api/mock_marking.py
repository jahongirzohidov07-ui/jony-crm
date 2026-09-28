# -*- coding: utf-8 -*-
"""MOCK BAHOLASH KALKULYATORI (2026-09-27).

Jahongir: "Examinerga iloji boricha kam ish qoldir."

Examiner faqat MEZONLAR bo'yicha baho qo'yadi, yakuniy ballni tizim
rasmiy jadvallar bo'yicha o'zi chiqaradi:

  ielts_writing   4 mezon x 0-9  -> o'rtacha, IELTS yaxlitlash qoidasi
  ielts_speaking  4 mezon x 0-9  -> o'rtacha, IELTS yaxlitlash qoidasi
  cefr_writing    2 topshiriq x (4 mezon x 1-4) -> har biri x1.25 = 0-20,
                  hajm jarimasi bilan
  cefr_speaking   8 element (1-3, 4-6, 7 -> 0-5; 8 -> 0-6) = 0-21
                  -> rasmiy jadval bo'yicha 0-75 va CEFR darajasi

Manbalar: uzbmb.uz "B2/C1 Baholash mezoni (yozma ish)" va gapirish
reyting shkalasi; IELTS uchun to'rt mezon o'rtachasi (roles.ielts_round).
"""
from typing import Optional

import cefr_score as C
import roles

IELTS_WRITING_CRITERIA = [
    "Task Achievement / Response",
    "Coherence and Cohesion",
    "Lexical Resource",
    "Grammatical Range and Accuracy",
]
IELTS_SPEAKING_CRITERIA = [
    "Fluency and Coherence",
    "Lexical Resource",
    "Grammatical Range and Accuracy",
    "Pronunciation",
]
IELTS_BAND_MAX = 9.0

CEFR_SPEAKING_ITEMS = [
    ("1-3 savol (Part 1.1)", 5),
    ("4-6 savol (Part 1.2)", 5),
    ("7-savol (Part 2)", 5),
    ("8-savol (Part 3)", 6),
]
CEFR_WRITING_TASKS = ["1-topshiriq", "2-topshiriq"]


def ielts_band(marks: list) -> Optional[dict]:
    """To'rt mezon bahosidan (har biri 0-9) IELTS bandi.

    Yaxlitlash roles.ielts_round bilan — tizimda allaqachon shu
    qoida ishlatiladi, ikkinchi variantini yasamaymiz."""
    vals = []
    for m in marks or []:
        try:
            vals.append(max(0.0, min(IELTS_BAND_MAX, float(m))))
        except (TypeError, ValueError):
            pass
    if len(vals) != 4:
        return None
    return {
        "marks": vals,
        "mean": round(sum(vals) / 4, 2),
        "band": roles.ielts_overall(vals),
        "max": IELTS_BAND_MAX,
    }


def cefr_writing(tasks: list) -> Optional[dict]:
    """Ikki topshiriq; har biri {"marks": [4 ta 1-4], "words": N}."""
    out, total = [], 0.0
    for t in tasks or []:
        r = C.writing_task_score((t or {}).get("marks") or [],
                                 (t or {}).get("words"))
        out.append(r)
        total += r["score"]
    if not out:
        return None
    return {
        "tasks": out,
        "total": round(total, 1),
        "of": round(C.WRITING_TASK_MAX * len(out), 1),
        # 75 ballik yakuniy shkalaga o'tkazish jadvali rasmiy manbada
        # topilmadi — shuning uchun taxminiy raqam berilmaydi.
        "note": ("Har topshiriq 0-20 ball (4 mezon x 1-4, konversiya "
                 "x1.25, hajm jarimasi ayiriladi). Yakuniy 75 ballik "
                 "shkalaga o'tkazish jadvali rasmiy manbada yo'q — "
                 "ballni examiner kiritadi."),
    }


def cefr_speaking(items: list) -> Optional[dict]:
    """8 element bahosi -> xom ball (0-21) -> rasmiy jadval bo'yicha
    0-75 ball va CEFR darajasi."""
    vals = []
    for (_label, mx), m in zip(CEFR_SPEAKING_ITEMS, items or []):
        try:
            vals.append(max(0, min(mx, int(m))))
        except (TypeError, ValueError):
            vals.append(0)
    if len(vals) != len(CEFR_SPEAKING_ITEMS):
        return None
    raw = sum(vals)
    score = C.speaking_score(raw)
    return {
        "items": vals,
        "raw": raw,
        "raw_max": int(C.SPEAKING_RAW_MAX),
        "score": score,
        "score_max": int(C.SCALE_MAX),
        "level": C.level_of(score),
    }


def cefr_writing_new(marks: list) -> Optional[dict]:
    """CEFR Multilevel YOZMA ISH — yangi 3 topshiriqli format.

    Examiner har topshiriqqa BITTA holistik baho qo'yadi (1.1 -> 0-5,
    1.2 -> 0-5, 2 -> 0-6; jami 16). Xom ball rasmiy konversiya
    jadvali (C.WRITING_NEW_TABLE, 2025-10-13) bo'yicha 0-75 ga
    o'tadi — ball doim aniq, taxmin yo'q.
    """
    vals, tasks = [], []
    for (name, mx, _lv, _len), m in zip(C.WRITING_NEW_PARTS, marks or []):
        try:
            v = max(0, min(mx, int(m)))
        except (TypeError, ValueError):
            return None
        vals.append(v)
        tasks.append({"part": name, "mark": v, "max": mx,
                      "level": C.writing_new_band_level(name, v)})
    if len(vals) != len(C.WRITING_NEW_PARTS):
        return None
    raw = sum(vals)
    info = C.writing_info(raw)
    score = info.get("score")
    return {
        "tasks": tasks,
        "raw": raw,
        "raw_max": C.WRITING_NEW_RAW_MAX,
        "score": score,
        "score_max": int(C.SCALE_MAX),
        "level": C.level_of(score) if score is not None else None,
        "exact": bool(info.get("exact")),
        "note": info.get("note"),
    }


SCHEMES = {
    "ielts_writing": {
        "label": "IELTS Writing",
        "kind": "criteria",
        "criteria": [{"name": n, "max": 9, "step": 0.5}
                     for n in IELTS_WRITING_CRITERIA],
        "result": "band",
        "note": "To'rt mezon o'rtachasi IELTS qoidasi bo'yicha yaxlitlanadi.",
    },
    "ielts_speaking": {
        "label": "IELTS Speaking",
        "kind": "criteria",
        "criteria": [{"name": n, "max": 9, "step": 0.5}
                     for n in IELTS_SPEAKING_CRITERIA],
        "result": "band",
        "note": "To'rt mezon o'rtachasi IELTS qoidasi bo'yicha yaxlitlanadi.",
    },
    "cefr_speaking": {
        "label": "CEFR Multilevel Speaking",
        "kind": "items",
        "criteria": [{"name": n, "max": m, "step": 1}
                     for n, m in CEFR_SPEAKING_ITEMS],
        "result": "score75",
        "note": "8 element = 0-21 xom ball, rasmiy jadval bo'yicha 0-75.",
    },
    "cefr_writing": {
        "label": "CEFR Multilevel Writing (yangi, 3 topshiriq)",
        "kind": "criteria",
        "criteria": [{"name": f"Part {n} ({ln})", "max": mx, "step": 1,
                      "bands": [{"mark": b, "level": lb}
                                for b, lb in C.WRITING_NEW_BANDS[n]]}
                     for n, mx, _lv, ln in C.WRITING_NEW_PARTS],
        "result": "score75",
        "note": ("Har topshiriqqa bitta baho (1.1 va 1.2 -> 0-5, 2 -> "
                 "0-6). Jami 16 xom ball, rasmiy konversiya jadvali "
                 "bo'yicha 0-75 (2025-10-13)."),
    },
    "cefr_writing_old": {
        "label": "CEFR Writing (eski, 2 topshiriqli format)",
        "kind": "tasks",
        "criteria": [{"name": n, "max": 4, "step": 1}
                     for n in C.WRITING_CRITERIA_B2],
        "tasks": CEFR_WRITING_TASKS,
        "result": "score20",
        "note": ("Har topshiriq 4 mezon x 1-4 = 0-16, konversiya x1.25 "
                 "-> 0-20. Hajm jarimasi avtomat ayiriladi."),
    },
}


def compute(skill: str, payload: dict) -> Optional[dict]:
    """Kalkulyatorning yagona kirish nuqtasi."""
    s = (skill or "").strip().lower()
    if s in ("ielts_writing", "ielts_speaking"):
        return ielts_band((payload or {}).get("marks"))
    if s == "cefr_speaking":
        return cefr_speaking((payload or {}).get("marks"))
    if s == "cefr_writing":
        return cefr_writing_new((payload or {}).get("marks"))
    if s == "cefr_writing_old":
        return cefr_writing((payload or {}).get("tasks"))
    return None
