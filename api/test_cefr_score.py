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
print("\n=== B. YOZMA ISH (0-36 -> 0-75) ===")
ck("36 xom -> 75", C.writing_score(36), 75)
ck("0 xom -> 0", C.writing_score(0), 0)
ck("hujjatdagi qatorlar",
   (C.writing_score(35.5), C.writing_score(28.5), C.writing_score(20.3),
    C.writing_score(12.4), C.writing_score(0.3)),
   (75, 65, 50, 34, 10))
prev, mono = -1, True
for i in range(0, 361):
    v = C.writing_score(i / 10)
    if v < prev:
        mono = False
    prev = v
ck("monoton (0.0 dan 36.0 gacha)", mono, True)
ck("1-topshiriq 12 + 2-topshiriq 24 = 36", C.WRITING_RAW_MAX, 36.0)

# ----------------------------------------------------------------- C
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
