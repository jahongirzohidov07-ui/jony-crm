"""LUG'AT BANKI — asosiy qoidalar testlari (2026-10-16).

Dizayn: vocab/DESIGN.md §2, §3, §5. Ishga tushirish:
  PYTHONIOENCODING=utf-8 python test_wordbank_core.py  (0 = hammasi o'tdi)
"""
import sys
from datetime import date, timedelta

import wordbank_core as W

fails = []


def ck(name, got, want):
    ok = got == want
    print(("OK  " if ok else "XATO ") + f"{name}: {got}" + ("" if ok else f"  (kutilgan {want})"))
    if not ok:
        fails.append(name)


D0 = date(2026, 10, 1)


def d(n):
    return D0 + timedelta(days=n)


print("=== 1. YANGI SO'Z — ENG QISQA YO'L (d0 → d1 → d4, P bilan) ===")
s = W.new_word(d(0))
s = W.apply_answer(s, d(0), "R", True)
ck("d0 R to'g'ri -> 1-pog'ona", s.stage, 1)
s = W.apply_answer(s, d(1), "R", True)
ck("d1 R to'g'ri -> 2-pog'ona", s.stage, 2)
ck("2-pog'ona: hali bilinmaydi", s.known, False)
s = W.apply_answer(s, d(4), "P", True)
ck("d4 P to'g'ri -> tasdiqlangan", s.known, True)
ck("tasdiqlangandan keyin 3-pog'ona", s.stage, 3)

print("\n=== 2. FAQAT TANLASH (R) BILAN BILINMAYDI ===")
s = W.apply_answer(W.apply_answer(W.apply_answer(W.new_word(d(0)), d(0), "R", True), d(1), "R", True), d(4), "R", True)
ck("3 marta R bilan ham tasdiqlanmaydi", s.known, False)
ck("R bilan 2-pog'onada, keyingi kunga", s.due, d(5))

print("\n=== 3. TANISH SO'Z (FAST TRACK) ===")
s = W.fast_track(d(0))
ck("fast track -> 2-pog'ona", s.stage, 2)
ck("fast track due +3 kun", s.due, d(3))
s = W.apply_answer(s, d(3), "P", True)
ck("3-kunda P -> tasdiqlangan", s.known, True)

print("\n=== 4. VAQTIDAN OLDIN VA SHUBHALI JAVOB — HECH NARSA O'ZGARMAYDI ===")
s = W.new_word(d(0))
s2 = W.apply_answer(s, d(0), "R", True)
s3 = W.apply_answer(s2, d(0), "R", True)   # bir kunda ikkinchi marta
ck("bir kunda ikki marta pog'ona o'zgarmaydi", s3.stage, 1)
s4 = W.apply_answer(W.fast_track(d(0)), d(3), "P", True, suspect=True)
ck("shubhali (tez) typed javob tasdiqlamaydi", s4.known, False)
s5 = W.apply_answer(W.fast_track(d(0)), d(1), "P", True)
ck("due dan oldin javob qayd etiladi, pog'ona o'zgarmaydi", s5.stage, 2)

print("\n=== 5. UNUTISH (LAPSE) VA QAYTA TASDIQLASH ===")
known = W.WordState(stage=3, due=d(10), has_prod=True, known=True, last_move=d(3))
lap = W.apply_answer(known, d(10), "R", False)
ck("xato -> 2-pog'ona", lap.stage, 2)
ck("xato -> bilmaydi", lap.known, False)
ck("xato -> lapses +1", lap.lapses, 1)
ck("xato -> has_prod tozalanadi", lap.has_prod, False)
ck("xato -> ertaga", lap.due, d(11))
again = W.apply_answer(lap, d(11), "R", True)
ck("R bilan qaytadi — hali bilinmaydi", again.known, False)
back = W.apply_answer(again, d(12), "P", True)
ck("P bilan qayta tasdiqlanadi", back.known, True)

print("\n=== 6. KATTA POG'ONALAR VA 6-POG'ONA ===")
s6 = W.WordState(stage=5, due=d(0), has_prod=True, known=True)
s6 = W.apply_answer(s6, d(0), "P", True)
ck("5 -> 6 pog'ona", s6.stage, 6)
ck("5 -> 6 da keyingi takror +90 kun (dizayn jadvali)", s6.due, d(90))
ck("6-pog'onada turganda +180 kun", W.apply_answer(s6, d(90), "P", True).due, d(270))
s6b = W.apply_answer(s6, d(180), "P", True)
ck("6-pog'onada qoladi", s6b.stage, 6)

print("\n=== 7. DARAJA TUGASHI VA COIN (HAR DARAJA BIR MARTA) ===")
bands = {1: {1, 2}, 2: {3, 4, 5}}
known_ids = {1: {1, 2}, 2: {3, 4}}
ck("2-daraja to'liq emas — tugamagan", W.bands_completed(known_ids, bands), [1])
known_ids[2] = {3, 4, 5}
ck("hammasi bilingan — ikkala daraja", W.bands_completed(known_ids, bands), [1, 2])
ck("coin: 1-daraja = 1", W.coins_for_band(1), 1)
ck("coin: 20-daraja = 20", W.coins_for_band(20), 20)
ck("yangi coinlar (ikkisi ham)", W.new_band_awards([1, 2], set()), [(1, 1), (2, 2)])
ck("oldin berilgan — qayta berilmaydi", W.new_band_awards([1, 2], {1}), [(2, 2)])
ck("jami coin 1..20 = 210", sum(W.coins_for_band(b) for b in range(1, 21)), 210)
try:
    W.coins_for_band(21)
    ck("21-daraja xato beradi", False, True)
except ValueError:
    ck("21-daraja xato beradi", True, True)

print("\n=== 8. HAJM TESTI — TUZATISH VA TO'XTASH ===")
ck("taxmin: 3 xato 'Bilmayman'siz", round(W.p_hat(4, 3), 2), 0.3)
ck("R=2, W=0 -> 0.2", round(W.p_hat(2, 0), 2), 0.2)
ck("boshlang'ich: 1-darajada 2/10 -> to'xtaydi", W.next_test_band({1: (2, 0)}), None)
ck("1-darajada 5/10 -> 2-daraja", W.next_test_band({1: (5, 0)}), 2)
ck("ketma-ket 2 ta past daraja -> to'xtaydi",
   W.next_test_band({1: (9, 0), 2: (9, 0), 3: (1, 0), 4: (1, 0)}), None)
ck("130 savoldan keyin to'xtaydi",
   W.next_test_band({b: (5, 0) for b in W.TEST_ORDER}), None)

print("\n=== 9. HAJM HISOBI ===")
full = {b: (10, 0) for b in range(1, 21)}
ck("hammasi 100%: 20 000", W.size_estimate(full)["estimate"], 20000)
ck("hammasi 100%: aniqlik noli", W.size_estimate(full)["low"], 20000)
# Dizayn misoli: 1–6 darajalar 100%, qolganlari 0% -> 6 500
ex = {b: (10, 0) for b in range(1, 7)}
ex.update({b: (0, 0) for b in (8, 10, 12, 14, 16, 18, 20)})
ck("misol: 1–6 = 100%, qolgan 0% -> 6 500", W.size_estimate(ex)["estimate"], 6500)
ck("misol: aniqlik oralig'i tor (sinov aniq)",
   W.size_estimate(ex)["high"] - W.size_estimate(ex)["low"] < 200, True)
ck("bo'sh natija -> None", W.size_estimate({}), None)

print("\n" + ("BARCHASI OK" if not fails else f"XATOLAR: {fails}"))
sys.exit(1 if fails else 0)
