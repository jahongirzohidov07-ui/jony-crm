# -*- coding: utf-8 -*-
"""CEFR MULTILEVEL BAHOLASH — RASMIY SHKALALAR (2026-09-27).

Manba: "Chet tilini bilish darajasini baholash ko'p darajali test
formati uchun baholash mezonlari" — Bilimni baholash agentligi
Ilmiy-metodik kengashi, 2023-yil 16-mart (Jahongir yuborgan
"Multilevel-bm.pdf"), va gapirish bo'limining reyting shkalasi.

MUHIM — TINGLAB TUSHUNISH VA O'QISH ANIQ HISOBLANMAYDI.
Hujjatga ko'ra bu ikki bo'lim RASCH metodi bilan hisoblanadi:

    Z = (theta - mu) / sigma     theta — Rasch qobiliyat bali
    T = Z * 10 + 50              mu — o'rta qiymat, sigma — st. tafovut

ya'ni natija savollarning qiyinlik kalibrovkasiga VA o'sha imtihonni
topshirgan guruh statistikasiga bog'liq. Demak "shuncha to'g'ri javob
= shuncha ball" degan qat'iy jadval YO'Q va uni o'ylab topib bo'lmaydi
(+2.5 va undan yuqori standart ball 75 ga tenglashtiriladi, chunki
C2 darajasidagi topshiriqlar umuman ko'zda tutilmagan).

Hujjatning o'zi faqat TAXMINIY to'g'ri javoblar sonini beradi —
LR_LEVELS shundan olingan va natija doim "taxminiy" deb belgilanadi.

Yozma ish va gapirishda esa shkala ANIQ:
  - Yozma ish: 1-topshiriq 12 ball (33%) + 2-topshiriq 24 ball (67%)
    = 36 xom ball -> WRITING_TABLE bo'yicha 0-75;
  - Gapirish: 21 xom ball -> SPEAKING_TABLE bo'yicha 0-75.

Yakuniy daraja: 4 bo'lim balining o'rtachasi -> LEVELS.
"""
from typing import Optional

# 100 balli shkalada eng yuqori ball 75 (C2 topshiriqlari yo'q)
SCALE_MAX = 75.0

# Umumiy ball -> daraja (hujjatdagi yakuniy shkala)
LEVELS = [
    ("C1", 65, 75),
    ("B2", 51, 64),
    ("B1", 38, 50),
    ("B1 dan quyi", 0, 37),
]

# Tinglab tushunish va o'qish: TAXMINIY to'g'ri javoblar soni (35 tadan).
# Aniq ball Rasch metodi bilan chiqadi — bu faqat mo'ljal.
LR_LEVELS = [
    ("C1", 28, 35),
    ("B2", 18, 27),
    ("B1", 10, 17),
    ("B1 dan quyi", 0, 9),
]

# Yozma ish: ekspert ballari o'rtachasi (0-36) -> yakuniy ball (0-75)
WRITING_TABLE = [
    (35.1, 36.0, 75), (34.1, 35.0, 74), (33.1, 34.0, 73), (32.6, 33.0, 72),
    (32.1, 32.5, 71), (31.6, 32.0, 70), (31.1, 31.5, 69), (30.6, 31.0, 68),
    (30.1, 30.5, 67), (29.1, 30.0, 66), (28.1, 29.0, 65), (27.1, 28.0, 64),
    (26.6, 27.0, 63), (26.1, 26.5, 62), (25.6, 26.0, 61), (25.1, 25.5, 60),
    (24.6, 25.0, 59), (24.1, 24.5, 58), (23.6, 24.0, 57), (23.1, 23.5, 56),
    (22.6, 23.0, 55), (22.1, 22.5, 54), (21.6, 22.0, 53), (21.1, 21.5, 52),
    (20.6, 21.0, 51), (20.1, 20.5, 50), (19.6, 20.0, 49), (19.1, 19.5, 48),
    (18.6, 19.0, 47), (18.1, 18.5, 46), (17.6, 18.0, 45), (17.1, 17.5, 44),
    (16.6, 17.0, 43), (16.1, 16.5, 42), (15.6, 16.0, 41), (15.1, 15.5, 40),
    (14.6, 15.0, 39), (14.1, 14.5, 38), (13.6, 14.0, 37), (13.1, 13.5, 36),
    (12.6, 13.0, 35), (12.1, 12.5, 34), (11.6, 12.0, 33), (11.1, 11.5, 32),
    (10.6, 11.0, 31), (10.1, 10.5, 30), (9.6, 10.0, 29), (9.1, 9.5, 28),
    (8.6, 9.0, 27), (8.1, 8.5, 26), (7.6, 8.0, 25), (7.1, 7.5, 24),
    (6.6, 7.0, 23), (6.1, 6.5, 22), (5.6, 6.0, 21), (5.1, 5.5, 20),
    (4.6, 5.0, 19), (4.1, 4.5, 18), (3.6, 4.0, 17), (3.1, 3.5, 16),
    (2.6, 3.0, 15), (2.1, 2.5, 14), (1.6, 2.0, 13), (1.1, 1.5, 12),
    (0.6, 1.0, 11), (0.1, 0.5, 10),
]
WRITING_RAW_MAX = 36.0

# Gapirish: 8 baholanadigan element (1-3, 4-6, 7 -> 0-5 dan; 8 -> 0-6)
# = 21 xom ball. Jadval CHIZIQLI EMAS, shuning uchun aynan shu
# qiymatlar ishlatiladi.
SPEAKING_TABLE = [
    (21, 75), (20.5, 73), (20, 71), (19.5, 69), (19, 67), (18.5, 65),
    (18, 64), (17.5, 63), (17, 61), (16.5, 59), (16, 57), (15.5, 56),
    (15, 54), (14.5, 52), (14, 51), (13.5, 50), (13, 49), (12.5, 47),
    (12, 46), (11.5, 45), (11, 43), (10.5, 42), (10, 40), (9.5, 39),
    (9, 38), (8.5, 37), (8, 35), (7.5, 33), (7, 32), (6.5, 30),
    (6, 29), (5.5, 27), (5, 26), (4.5, 24), (4, 23), (3.5, 21),
    (3, 19), (2.5, 17), (2, 15), (1.5, 13), (1, 11), (0.5, 10), (0, 0),
]
SPEAKING_RAW_MAX = 21.0


def level_of(score) -> Optional[str]:
    """0-75 balldan CEFR darajasi."""
    try:
        s = float(score)
    except (TypeError, ValueError):
        return None
    for name, lo, hi in LEVELS:
        if lo <= s <= hi:
            return name
    return LEVELS[0][0] if s > 0 else LEVELS[-1][0]


def writing_score(raw) -> Optional[int]:
    """Yozma ish: ekspert ballari o'rtachasi (0-36) -> 0-75."""
    try:
        r = float(raw)
    except (TypeError, ValueError):
        return None
    if r <= 0:
        return 0
    if r > WRITING_RAW_MAX:
        return 75
    for lo, hi, sc in WRITING_TABLE:
        if lo <= r <= hi:
            return sc
    return 0


def speaking_score(raw) -> Optional[int]:
    """Gapirish: xom ball (0-21) -> 0-75 (rasmiy jadval)."""
    try:
        r = float(raw)
    except (TypeError, ValueError):
        return None
    if r > SPEAKING_RAW_MAX:
        r = SPEAKING_RAW_MAX
    for lo, sc in SPEAKING_TABLE:
        if r >= lo:
            return sc
    return 0


def lr_approx(correct, total: int = 35) -> Optional[dict]:
    """Tinglab tushunish / o'qish: to'g'ri javoblar sonidan TAXMINIY
    daraja. Aniq ball Rasch metodi bilan chiqadi (modul izohiga
    qarang), shuning uchun bu yerda faqat mo'ljal beriladi."""
    try:
        c = float(correct)
        t = float(total or 0)
    except (TypeError, ValueError):
        return None
    if t <= 0:
        return None
    # Savollar soni 35 dan farq qilsa, 35 talik shkalaga keltiriladi
    n = max(0, min(35, int(round(c / t * 35))))
    for name, lo, hi in LR_LEVELS:
        if lo <= n <= hi:
            band = next((b for b in LEVELS if b[0] == name), None)
            return {
                "correct": int(round(c)),
                "of": int(round(t)),
                "scaled35": n,
                "level": name,
                "score_from": band[1] if band else None,
                "score_to": band[2] if band else None,
                "approx": True,
            }
    return None


def overall(scores: list) -> Optional[dict]:
    """4 bo'lim balining o'rtachasidan yakuniy daraja."""
    vals = []
    for s in scores or []:
        try:
            vals.append(float(s))
        except (TypeError, ValueError):
            continue
    if not vals:
        return None
    avg = round(sum(vals) / len(vals), 1)
    return {"score": avg, "level": level_of(avg), "sections": len(vals)}
