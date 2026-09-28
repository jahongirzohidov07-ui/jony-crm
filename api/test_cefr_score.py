"""CEFR MULTILEVEL RASMIY SHKALALARI (2026-09-27).

Manba: Bilimni baholash agentligi, 2023-yil 16-mart mezonlari
("Multilevel-bm.pdf") + gapirish reyting shkalasi.

Tekshiriladi:
  A. Daraja chegaralari hujjatdagidek (C1 65-75, B2 51-64, B1 38-50);
  B. Yozma ish 36 xom ball -> 0-75, jadval monoton va chekkalari aniq;
  C. Gapirish 21 xom ball -> 0-75, jadval CHIZIQLI EMAS (past ballarda
     chiziqli formuladan yuqori) va monoton;
  D. Tinglab tushunish / o'qish faqat TAXMINIY daraja beradi —
     hujjatdagi to'g'ri javoblar chegaralari bo'yicha;
  E. Yakuniy daraja 4 bo'lim o'rtachasidan chiqadi;
  F. speaking_cefr_format.to_scale endi rasmiy jadvalni ishlatadi.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import cefr_score as C                            # noqa: E402
import speaking_cefr_format as F                  # noqa: E402

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


# ----------------------------------------------------------------- A
print("=== A. DARAJA CHEGARALARI ===")
ck("C1 65 dan", C.level_of(65), "C1")
ck("C1 75 gacha", C.level_of(75), "C1")
ck("B2 51-64", (C.level_of(51), C.level_of(64)), ("B2", "B2"))
ck("B1 38-50", (C.level_of(38), C.level_of(50)), ("B1", "B1"))
ck("37 — B1 dan quyi", C.level_of(37), "B1 dan quyi")
ck("0 — B1 dan quyi", C.level_of(0), "B1 dan quyi")
ck("chegaralar uzluksiz",
   [C.level_of(x) for x in (37, 38, 50, 51, 64, 65)],
   ["B1 dan quyi", "B1", "B1", "B2", "B2", "C1"])

# ----------------------------------------------------------------- B
print(chr(10) + "=== B1. YOZMA ISH — ESKI FORMAT (0-36 -> 0-75) ===")
ck("36 xom -> 75", C.writing_score_old(36), 75)
ck("0 xom -> 0", C.writing_score_old(0), 0)
ck("2023 hujjatidagi qatorlar",
   (C.writing_score_old(35.5), C.writing_score_old(28.5),
    C.writing_score_old(20.3), C.writing_score_old(12.4),
    C.writing_score_old(0.3)),
   (75, 65, 50, 34, 10))
prev, mono = -1, True
for i in range(0, 361):
    v = C.writing_score_old(i / 10)
    if v < prev:
        mono = False
    prev = v
ck("monoton (0.0 dan 36.0 gacha)", mono, True)
ck("eski format: 12 + 24 = 36", C.WRITING_OLD_RAW_MAX, 36.0)

print(chr(10) + "=== B2. YOZMA ISH — YANGI FORMAT (1.1 + 1.2 + 2 = 16) ===")
ck("uch topshiriq, maksimal 16 (2025-10-13 yakuniy shkala)",
   ([p[1] for p in C.WRITING_NEW_PARTS], C.WRITING_NEW_RAW_MAX),
   ([5, 5, 6], 16))
ck("topshiriq darajalari B1 / B2 / C1",
   [p[2] for p in C.WRITING_NEW_PARTS], ["B1", "B2", "C1"])
# Rasmiy jadval (agentlik, 2025-10-13) — har bir qator
RASMIY_W = {16: 75, 15.5: 72, 15: 69, 14.5: 67, 14: 65, 13.5: 64, 13: 63,
            12.5: 62, 12: 61, 11.5: 59, 11: 57, 10.5: 55, 10: 53, 9.5: 51,
            9: 50, 8.5: 48, 8: 47, 7.5: 45, 7: 43, 6.5: 41, 6: 40,
            5.5: 38, 5: 37, 4.5: 35, 4: 33, 3.5: 31, 3: 28, 2.5: 25,
            2: 21, 1.5: 17, 1: 14, 0.5: 10, 0: 0}
ck("konversiya jadvali 33 qatorda aynan mos",
   [k for k, v in RASMIY_W.items() if C.writing_score_new(k) != v], [])
ck("jadval chegaralari CEFR darajalariga mos (14 C1, 9.5 B2, 5.5 B1)",
   [C.level_of(C.writing_score_new(r)) for r in (14, 13.5, 9.5, 9, 5.5, 5)],
   ["C1", "B2", "B2", "B1", "B1", "B1 dan quyi"])
ck("monoton o'sadi",
   all(C.writing_score_new(a / 2) <= C.writing_score_new(a / 2 + 0.5)
       for a in range(0, 32)), True)
ck("oraliq qiymat eng yaqin 0.5 ga (8.2 -> 8, 8.3 -> 8.5)",
   (C.writing_score_new(8.2), C.writing_score_new(8.3)), (47, 48))
ck("chegaradan tashqari siqiladi (-1 -> 0, 20 -> 75)",
   (C.writing_score_new(-1), C.writing_score_new(20)), (0, 75))
ck("xato kirish — None", C.writing_score_new("abc"), None)
ck("writing_info: har doim aniq",
   (C.writing_info(12)["score"], C.writing_info(12)["exact"],
    C.writing_info(9)["exact"]), (61, True, True))
ck("1.2 shkalasi 0-5 (pilotdagi 6 = C2 yo'q)",
   [b for b, _ in C.WRITING_NEW_BANDS["1.2"]], [5, 4, 3, 2, 1, 0])
ck("eski jadval yangi formatga ishlatilmaydi",
   C.writing_score_old(8) != C.writing_score_new(8), True)
print(chr(10) + "=== B3. YOZMA ISH — RASMIY MEZONLAR (uzbmb.uz) ===")
RASMIY = {1: 1.3, 2: 2.5, 3: 3.8, 4: 5.0, 5: 6.3, 6: 7.5, 7: 8.8, 8: 10.0,
          9: 11.3, 10: 12.5, 11: 13.8, 12: 15.0, 13: 16.3, 14: 17.5,
          15: 18.8, 16: 20.0}
ck("konversiya shkalasi 16 qatorda aynan mos",
   [k for k, v in RASMIY.items() if C.writing_task_convert(k) != v], [])
ck("4 mezon x 4 ball = 16 xom", C.WRITING_TASK_RAW_MAX, 16)
ck("topshiriq maksimali 20", C.WRITING_TASK_MAX, 20.0)
ck("mezonlar to'rttadan",
   (len(C.WRITING_CRITERIA_B2), len(C.WRITING_CRITERIA_C1)), (4, 4))
ck("to'liq ball: [4,4,4,4] -> 20.0",
   C.writing_task_score([4, 4, 4, 4], 160)["score"], 20.0)
# Hajm jarimasi: 135-120 -> 1, 119-105 -> 2, 104-90 -> 3, 89-75 -> 4
ck("hajm jarimasi chegaralari",
   [C.writing_length_penalty(w) for w in (150, 135, 120, 119, 105, 104, 90, 89, 75, 74)],
   [0, 1, 1, 2, 2, 3, 3, 4, 4, 0])
ck("jarima umumiy balldan ayiriladi",
   C.writing_task_score([2, 2, 2, 2], 128)["score"], 9.0)
# 75 so'zdan kam — ish tekshirilmaydi, avtomat minimal ball
ck("75 so'zdan kam -> 0.6 (tekshirilmaydi)",
   (C.writing_task_score([4, 3, 3, 3], 60)["score"],
    C.writing_task_score([4, 3, 3, 3], 60)["too_short"]),
   (0.6, True))
ck("baho 4 dan oshmaydi, 0 dan tushmaydi",
   C.writing_task_score([9, -2, 4, 4], 200)["marks"], [4, 0, 4, 4])

print("\n=== C. GAPIRISH (0-21 -> 0-75) ===")
ck("21 xom -> 75", C.speaking_score(21), 75)
ck("0 xom -> 0", C.speaking_score(0), 0)
ck("hujjatdagi qatorlar",
   (C.speaking_score(18), C.speaking_score(14), C.speaking_score(10),
    C.speaking_score(5), C.speaking_score(0.5)),
   (64, 51, 40, 26, 10))
prev, mono = -1, True
for i in range(0, 43):
    v = C.speaking_score(i / 2)
    if v < prev:
        mono = False
    prev = v
ck("monoton (0 dan 21 gacha, yarim balldan)", mono, True)


def lin(r):
    """Ilgari ishlatilgan chiziqli formula — solishtirish uchun."""
    return int(round(r / 21 * 75))


ck("chiziqli emas: past ballarda yuqoriroq",
   [C.speaking_score(r) > lin(r) for r in (3, 5, 7, 10)],
   [True, True, True, True])
ck("chekkalarda chiziqli bilan mos",
   (C.speaking_score(0), C.speaking_score(21)), (lin(0), lin(21)))

# ----------------------------------------------------------------- D
print("\n=== D. TINGLAB TUSHUNISH / O'QISH — TAXMINIY ===")
r = C.lr_approx(30, 35)
ck("30/35 -> C1", (r["level"], r["score_from"], r["score_to"]), ("C1", 65, 75))
ck("hammasi taxminiy deb belgilanadi", r["approx"], True)
ck("hujjatdagi chegaralar",
   [C.lr_approx(n, 35)["level"] for n in (35, 28, 27, 18, 17, 10, 9, 0)],
   ["C1", "C1", "B2", "B2", "B1", "B1", "B1 dan quyi", "B1 dan quyi"])
ck("boshqa savol sonida 35 talik shkalaga keltiriladi",
   (C.lr_approx(20, 40)["scaled35"], C.lr_approx(20, 40)["level"]),
   (18, "B2"))
ck("savol yo'q — None", C.lr_approx(5, 0), None)

# ----------------------------------------------------------------- E
print("\n=== E. YAKUNIY DARAJA ===")
ck("4 bo'lim o'rtachasi",
   C.overall([70, 68, 66, 65]), {"score": 67.2, "level": "C1", "sections": 4})
ck("B2 o'rtacha", C.overall([55, 52, 60, 51])["level"], "B2")
ck("B1 o'rtacha", C.overall([45, 40, 38, 42])["level"], "B1")
ck("bitta zaif bo'lim darajani tushiradi",
   (C.overall([75, 75, 75, 20])["score"],
    C.overall([75, 75, 75, 20])["level"]), (61.2, "B2"))
ck("bo'sh ro'yxat — None", C.overall([]), None)

# ----------------------------------------------------------------- F
print("\n=== F. GAPIRISH AMALIYOTI RASMIY JADVALGA O'TDI ===")
ck("to_scale = rasmiy jadval",
   [F.to_scale(r) for r in (0, 3, 7, 10, 14, 18, 21)],
   [C.speaking_score(r) for r in (0, 3, 7, 10, 14, 18, 21)])
ck("chekkalar joyida", (F.to_scale(0), F.to_scale(F.RAW_MAX)), (0, 75))

print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
sys.exit(1 if fails else 0)
