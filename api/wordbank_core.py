"""LUG'AT BANKI — asosiy qoidalar (sof mantiq, bazasiz) (2026-10-16).

Dizayn: vocab/DESIGN.md, §2 (bilish holati), §3 (hajm testi), §5 (coin).
Bu modul hech qayerga ulanmagan — jadval, API va ilova keyingi bosqichda.

Qoidalar:
  * "Tasdiqlangan" so'z — turli kunlarda to'g'ri eslab qolingan so'z,
    kamida bir marta P (yozib topish) bilan. Tanlash (R) yolg'iz yetmaydi.
  * Unutilgan so'z (ilgari bilgan, keyin xato) — P bilan qaytadan tasdiqlanadi.
  * Bir kunda so'z holati bir pog'onadan ko'p o'zgarmaydi.
  * Hajm testi — 4 variantli tanlash, taxmin uchun tuzatish (W/(k-1)).
  * Coin — N-darajani tugatsa N coin, har daraja uchun bir marta.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Set, Tuple

BANDS = 20
WORDS_PER_BAND = 1000

# Yangi pog'onaga o'tgandan keyingi takrorlash oralig'i (kun)
NEXT_GAP = {1: 1, 2: 3, 3: 7, 4: 16, 5: 35, 6: 90}
STAY_GAP = 180           # 6-pog'onada qolganda
KNOWN_FROM_STAGE = 3     # shu pog'onadan boshlab "tasdiqlangan"

K_CHOICES = 4            # hajm testi: 4 variant
TEST_N = 10              # har darajada test savoli
TEST_ORDER = [1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 18, 20]
Z95 = 1.96


@dataclass(frozen=True)
class WordState:
    stage: int = 0
    due: Optional[date] = None
    has_prod: bool = False      # stage 2 ga kirgandan beri P muvaffaqiyat bormi
    known: bool = False
    lapses: int = 0
    last_move: Optional[date] = None   # so'nggi pog'ona o'zgargan kun


def fast_track(day: date) -> WordState:
    """Tanish so'z: birinchi to'g'ri javob — to'g'ridan-to'g'ri 2-pog'ona, 3 kundan keyin."""
    return WordState(stage=2, due=day + timedelta(days=3), has_prod=False,
                     known=False, last_move=day)


def new_word(day: date) -> WordState:
    """Yangi so'z: bugun tanishtiriladi (0-pog'ona), darhol takrorlanadi."""
    return WordState(stage=0, due=day, last_move=None)


def apply_answer(state: WordState, day: date, mode: str, correct: bool,
                 suspect: bool = False) -> WordState:
    """Javobdan keyingi holat. mode: 'R' (tanlash) yoki 'P' (yozib topish).

    Qoidalar: faqat 'due' kuni yoki undan keyin pog'ona o'zgaradi; shubhali
    (juda tez yozilgan) javob hech narsani o'zgartirmaydi; bir kunda bir marta.
    """
    if mode not in ("R", "P"):
        raise ValueError("mode R yoki P bo'lishi kerak")
    if suspect:
        return state
    if state.due is not None and day < state.due:
        return state                      # vaqtidan oldin: faqat qayd etiladi
    if state.last_move == day:
        return state                      # bugun allaqachon o'zgargan

    s = state
    if mode == "P" and correct:
        s = replace(s, has_prod=True)

    if correct:
        if s.stage == 0:
            return replace(s, stage=1, due=day + timedelta(days=NEXT_GAP[1]), last_move=day)
        if s.stage == 1:
            return replace(s, stage=2, due=day + timedelta(days=NEXT_GAP[2]), last_move=day)
        if s.stage == 2:
            if s.has_prod:
                return replace(s, stage=3, known=True,
                               due=day + timedelta(days=NEXT_GAP[3]), last_move=day)
            # R bilan keldi — keyingi kuni P bilan tekshiriladi
            return replace(s, due=day + timedelta(days=1), last_move=day)
        if s.stage < 6:
            nxt = s.stage + 1
            return replace(s, stage=nxt, known=nxt >= KNOWN_FROM_STAGE,
                           due=day + timedelta(days=NEXT_GAP[nxt]), last_move=day)
        return replace(s, due=day + timedelta(days=STAY_GAP), last_move=day)

    # Xato javob
    if s.stage >= KNOWN_FROM_STAGE:
        return replace(s, stage=2, known=False, has_prod=False,
                       due=day + timedelta(days=1), lapses=s.lapses + 1, last_move=day)
    if s.stage in (1, 2):
        return replace(s, stage=1, due=day + timedelta(days=1), last_move=day)
    return s                              # 0-pog'ona: bugun qayta chiqadi


def is_known(state: WordState) -> bool:
    return state.known


def known_count(states: Iterable[WordState]) -> int:
    return sum(1 for s in states if s.known)


def bands_completed(known_ids_by_band: Dict[int, Set[int]],
                    band_word_ids: Dict[int, Set[int]]) -> List[int]:
    """Hamma so'zi bilingan darajalar (1..20), o'sish tartibida."""
    done = []
    for band in sorted(band_word_ids):
        ids = band_word_ids[band]
        if ids and ids <= known_ids_by_band.get(band, set()):
            done.append(band)
    return done


def coins_for_band(band: int) -> int:
    if not 1 <= band <= BANDS:
        raise ValueError("daraja 1..20 oralig'ida bo'lishi kerak")
    return band


def new_band_awards(completed: Iterable[int], already_awarded: Set[int]) -> List[Tuple[int, int]]:
    """Yangi beriladigan (daraja, coin) juftliklari — har daraja uchun bir marta."""
    out = []
    for band in sorted(set(completed) - set(already_awarded)):
        out.append((band, coins_for_band(band)))
    return out


# ---------------- Misoldagi bo'shliq (yozib topish) ----------------
#
# 2026-10-16 (review): avval misolda lemma bilan BOSHLANGAN har qanday so'z
# bo'shliqqa aylanardi ((?<![A-Za-z])lemma[A-Za-z]*): "The volt ... measure
# voltage" -> ikki bo'shliq, "so" -> "soup", "an" -> "and". Endi faqat
# lemmaning o'zi va muntazam qo'shimchali shakli (DESIGN §2: "the exact form
# in the gapped example" ham qabul qilinadi). Shu funksiya serverda ham
# (wordbank._gap), so'zlar faylini yig'ishda ham (scripts/wordbank_merge.py
# lint) ishlatiladi — ikkalasi bir xil qoidani tekshiradi.

def gap_regex(lemma: str):
    """Misolda lemma shakllarini topadigan regex (katta-kichik harf farqsiz).

    Qabul qilinadigan qo'shimchalar: s, ing; es (s/x/z/ch/sh/o dan keyin);
    e bilan tugasa — d va e tushib + ing (make -> making); aks holda ed,
    er, est va qo'shaloq undosh (stop -> stopped, big -> bigger); undosh + y
    bilan tugasa — y -> i (worry -> worried, berry -> berries). 1–2 harfli
    lemma faqat o'zi (be -> "bed" emas, an -> "and" emas; go/do -> goes)."""
    low = lemma.lower()
    last = low[-1:]
    esc = re.escape(lemma)
    alts = []
    if len(low) <= 2:
        suf = ["es", "ing"] if last == "o" else []
    else:
        suf = ["s", "ing"]
        if low.endswith(("s", "x", "z", "ch", "sh", "o")):
            suf.append("es")
        if last == "e":
            suf.append("d")
            alts.append(re.escape(lemma[:-1]) + "ing")
        else:
            suf += ["ed", "er", "est"]
            if last.isalpha() and last not in "aeiouwxy":
                suf.append(re.escape(lemma[-1]) + "(?:ed|ing|er|est)")
            if last == "y" and low[-2] not in "aeiou":
                alts.append(re.escape(lemma[:-1]) + "i(?:ed|es|er|est)")
    alts.insert(0, esc + ("(?:" + "|".join(suf) + ")?" if suf else ""))
    return re.compile(r"(?<![A-Za-z])(?:" + "|".join(alts) + r")(?![A-Za-z])",
                      re.I)


def gap_forms(lemma: str, example: str) -> List[str]:
    """Misolda topilgan lemma shakllari (yozilishi bo'yicha, takrorsiz,
    kichik harfda). Bo'sh ro'yxat — misolni yozib topishda ko'rsatib
    bo'lmaydi; bittadan ko'p — misolda turli shakllar (lint ogohlantiradi)."""
    if not lemma or not example:
        return []
    out: List[str] = []
    for m in gap_regex(lemma).finditer(example):
        f = m.group(0).lower()
        if f not in out:
            out.append(f)
    return out


# ---------------- Hajm testi ----------------

def p_hat(right: int, wrong: int, n: int = TEST_N, k: int = K_CHOICES) -> float:
    """Taxmin uchun tuzatilgan ulush. 'Bilmayman' va vaqt tugashi — na R, na W."""
    return max(0.0, (right - wrong / (k - 1)) / n)


def next_test_band(results: Dict[int, Tuple[int, int]]) -> Optional[int]:
    """Keyingi darajani tanlaydi yoki testni to'xtatadi (None).

    results: {daraja: (R, W)}. To'xtash: ketma-ket ikki sinalgan daraja
    p < 0.15; yoki 1-daraja p < 0.30 (boshlang'ich); yoki 130 savol.
    """
    if len(results) * TEST_N >= 130:
        return None
    if 1 in results:
        r1, w1 = results[1]
        if p_hat(r1, w1) < 0.30:
            return None
    tested = [b for b in TEST_ORDER if b in results]
    if len(tested) >= 2:
        last, prev = tested[-1], tested[-2]
        if p_hat(*results[last]) < 0.15 and p_hat(*results[prev]) < 0.15:
            return None
    for b in TEST_ORDER:
        if b not in results:
            return b
    return None


def size_estimate(results: Dict[int, Tuple[int, int]]) -> Optional[Dict[str, float]]:
    """Taxminiy lug'at hajmi E va 95% oraliq, 100 ga yaxlitlangan.

    Sinalmagan darajalar ikki qo'shni sinalgan darajaning o'rtachasi bilan
    to'ldiriladi; oxirgi sinalgandan yuqori darajalar 0. Har sinalgan daraja
    o'z va yarim ulushini oladi: w_b = 1 + ½·(to'ldirilgan qo'shnilar soni).
    """
    if not results:
        return None
    tested = sorted(results)
    last = tested[-1]
    p = {b: p_hat(*results[b]) for b in tested}
    filled: Dict[int, float] = {}
    for b in range(1, BANDS + 1):
        if b in p:
            continue
        if b > last:
            filled[b] = 0.0
            continue
        below = [t for t in tested if t < b]
        above = [t for t in tested if t > b]
        if below and above:
            filled[b] = (p[max(below)] + p[min(above)]) / 2.0
        elif above:
            filled[b] = p[min(above)]
        else:
            filled[b] = p[max(below)]

    w: Dict[int, float] = {}
    for b in tested:
        extra = 0
        for nb in (b - 1, b + 1):
            if nb in filled and nb <= last:
                extra += 1
        w[b] = 1 + 0.5 * extra

    E = 1000.0 * sum(w[b] * p[b] for b in tested)
    var = sum((w[b] ** 2) * p[b] * (1 - p[b]) / TEST_N for b in tested)
    se = 1000.0 * (K_CHOICES / (K_CHOICES - 1)) * math.sqrt(var)
    return {
        "estimate": round(E / 100) * 100,
        "low": max(0, round(max(0.0, E - Z95 * se) / 100) * 100),
        "high": round((E + Z95 * se) / 100) * 100,
        "bands_checked": float(len(tested)),
    }
