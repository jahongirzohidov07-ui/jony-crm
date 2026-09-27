"""MOCK BAHOLASH KALKULYATORI (2026-09-27).

Jahongir: "Examinerga iloji boricha kam ish qoldir."

Tekshiriladi:
  A. IELTS Writing/Speaking — 4 mezon o'rtachasi IELTS qoidasi
     bo'yicha yaxlitlanadi (.25 -> .5, .75 -> keyingi butun);
  B. CEFR Speaking — 8 element (5+5+5+6=21) rasmiy jadval bo'yicha
     0-75 ball va daraja;
  C. CEFR Writing — har topshiriq 4 mezon x 1-4 = 0-16, konversiya
     x1.25, hajm jarimasi ayiriladi;
  D. Sxemalar ro'yxati examiner formasi uchun to'g'ri shaklda;
  E. Noto'g'ri kirish ma'lumotida None (xato raqam berilmaydi).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mock_marking as M                          # noqa: E402
import cefr_score as C                            # noqa: E402

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + name + f": {got}"
          + ("" if ok else f"   (kutilgan {want})"))
    if not ok:
        fails.append(name)


# ----------------------------------------------------------------- A
print("=== A. IELTS WRITING / SPEAKING (4 mezon -> band) ===")
ck("o'rtacha aniq band", M.ielts_band([7, 7, 7, 7])["band"], 7.0)
ck(".25 yuqoriga (7.25 -> 7.5)", M.ielts_band([8, 7, 7, 7])["band"], 7.5)
ck(".75 keyingi butunga (7.75 -> 8.0)",
   M.ielts_band([8, 8, 8, 7])["band"], 8.0)
ck("kichik qoldiq pastga (7.125 -> 7.0)",
   M.ielts_band([7, 7, 7, 7.5])["band"], 7.0)
ck("yarim ballar qabul qilinadi",
   M.ielts_band([6.5, 6.5, 6, 6])["band"], 6.5)
ck("9 dan oshmaydi", M.ielts_band([9, 9, 9, 9])["band"], 9.0)
ck("4 ta mezon shart — 3 ta bo'lsa None", M.ielts_band([7, 7, 7]), None)
ck("mezon nomlari to'rttadan",
   (len(M.IELTS_WRITING_CRITERIA), len(M.IELTS_SPEAKING_CRITERIA)), (4, 4))

# ----------------------------------------------------------------- B
print("\n=== B. CEFR SPEAKING (8 element -> 0-75) ===")
ck("elementlar 5+5+5+6 = 21",
   sum(m for _, m in M.CEFR_SPEAKING_ITEMS), 21)
r = M.cefr_speaking([5, 5, 5, 6])
ck("to'liq ball -> 75, C1", (r["raw"], r["score"], r["level"]), (21, 75, "C1"))
ck("15/21 -> 54, B2",
   (M.cefr_speaking([4, 4, 3, 4])["score"],
    M.cefr_speaking([4, 4, 3, 4])["level"]), (54, "B2"))
ck("0 -> 0", M.cefr_speaking([0, 0, 0, 0])["score"], 0)
ck("maksimaldan oshgan baho kesiladi",
   M.cefr_speaking([9, 9, 9, 9])["items"], [5, 5, 5, 6])
ck("jadval bilan bir xil",
   M.cefr_speaking([3, 3, 3, 3])["score"], C.speaking_score(12))

# ----------------------------------------------------------------- C
print("\n=== C. CEFR WRITING (2 topshiriq) ===")
w = M.cefr_writing([{"marks": [4, 4, 4, 4], "words": 160},
                    {"marks": [4, 4, 4, 4], "words": 260}])
ck("ikkala topshiriq to'liq -> 40", (w["total"], w["of"]), (40.0, 40.0))
w2 = M.cefr_writing([{"marks": [4, 4, 3, 3], "words": 160},
                     {"marks": [3, 3, 3, 2], "words": 240}])
ck("xom 14 -> 17.5 va xom 11 -> 13.8",
   [t["converted"] for t in w2["tasks"]], [17.5, 13.8])
ck("jami 31.3", w2["total"], 31.3)
w3 = M.cefr_writing([{"marks": [3, 3, 3, 3], "words": 128}])
ck("hajm jarimasi ayiriladi (128 so'z -> -1)",
   (w3["tasks"][0]["converted"], w3["tasks"][0]["penalty"],
    w3["tasks"][0]["score"]), (15.0, 1, 14.0))
w4 = M.cefr_writing([{"marks": [4, 4, 4, 4], "words": 60}])
ck("75 so'zdan kam -> 0.6", w4["tasks"][0]["score"], 0.6)
ck("yakuniy 75 ballik jadval yo'qligi aytiladi",
   "rasmiy manbada yo'q" in w2["note"], True)

# ----------------------------------------------------------------- D
print("\n=== D. SXEMALAR (examiner formasi uchun) ===")
ck("beshta sxema", sorted(M.SCHEMES),
   ["cefr_speaking", "cefr_writing", "cefr_writing_old",
    "ielts_speaking", "ielts_writing"])
bad = [k for k, sch in M.SCHEMES.items()
       if not sch.get("criteria") or not sch.get("label")]
ck("har sxemada mezonlar va nom bor", bad, [])
ck("IELTS mezonlari 9 balldan, yarim qadam",
   [(c["max"], c["step"]) for c in M.SCHEMES["ielts_writing"]["criteria"]],
   [(9, 0.5)] * 4)
ck("CEFR yozma (yangi) mezonlari 5 / 6 / 6",
   [c["max"] for c in M.SCHEMES["cefr_writing"]["criteria"]], [5, 6, 6])
ck("har mezonda baho izohlari bor (examiner ko'rsin)",
   [len(c["bands"]) for c in M.SCHEMES["cefr_writing"]["criteria"]],
   [6, 7, 7])
ck("eski format mezonlari 4 balldan",
   [c["max"] for c in M.SCHEMES["cefr_writing_old"]["criteria"]],
   [4, 4, 4, 4])

# ----------------------------------------------------------------- E
print("\n=== E. NOTO'G'RI KIRISHDA XATO RAQAM BERILMAYDI ===")
ck("noma'lum sxema — None", M.compute("boshqa", {"marks": [7, 7, 7, 7]}), None)
ck("bo'sh ballar — None", M.compute("ielts_writing", {"marks": []}), None)
ck("bo'sh topshiriq — None",
   M.compute("cefr_writing_old", {"tasks": []}), None)
ck("yangi formatda ballar yetishmasa — None",
   M.compute("cefr_writing", {"marks": [4, 2]}), None)
ck("compute IELTS uchun ishlaydi",
   M.compute("ielts_speaking", {"marks": [6, 6, 7, 7]})["band"], 6.5)
ck("compute CEFR speaking uchun ishlaydi",
   M.compute("cefr_speaking", {"marks": [5, 5, 5, 6]})["score"], 75)

print(f"\nJAMI XATO: {len(fails)} {fails[:8]}")
sys.exit(1 if fails else 0)
