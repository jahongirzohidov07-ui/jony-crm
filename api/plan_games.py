# -*- coding: utf-8 -*-
"""DARS O'YINLARI — chop etib o'ynaladigan o'yinlar (2026-09-28).

Jahongir: "ielts 1.0-4.0 gacha bo'lgan dars rejalari ichiga xar xil
oyinli activitylar qoshib ber mavzuga doir. Keyin uni pdf qilib
yuklab chiqarib oynash mumkin bo'lsin".

Har dars uchun:
  - MUALLIFLIK o'yinlari — plans_data/games/<course>.json da,
    {"lessons": {"<no>": [o'yin, ...]}}. Dars JSON'iga qo'shilmaydi:
    rejalar DSL generatordan qayta yaratilsa qo'shimcha kalitlar
    yo'qoladi (kahoot bilan shunday bo'lgan) va ielts_1_0.json siqilgan
    bir qatorli fayl.
  - AVTOMAT o'yinlar — Bingo va Memory, darsning 20/40/60 lug'atidan
    shu yerda tuziladi (tasodif urug'i kurs+dars, PDF har safar bir xil).

GET /api/plans/{course}/{no}/games      — o'yinlar ro'yxati (web)
GET /api/plans/{course}/{no}/games.pdf  — ?id=<o'yin> bittasi, id'siz
                                          hammasi bitta PDF'da

PDF: 1-sahifa "USTOZ UCHUN" (maqsad, kerakli narsalar, qoidalar,
javoblar kaliti), keyin qaychi bilan qirqiladigan materiallar
(kartalar, taxta, varaq). Brend vocab_pdf bilan bir xil.

Muallif uchun tekshiruv:  python api/plan_games.py check <fayl.json>
  <fayl.json> = {"course": "ielts_1_0", "lessons": {"3": [...]}}
  sxema xatolari va har o'yinning PDF'i quriladimi — hammasi chiqadi.
"""
import copy
import io
import json
import os
import random
import re
import sys
from functools import lru_cache
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

import roles
from auth import require_role
from database import get_db
from liveplay import _PLANS_DIR, _english_only, _head, _lesson
from vocab_pdf import _ASSETS, BRAND, CONTACT, _fonts

router = APIRouter()

GAMES_DIR = os.path.join(_PLANS_DIR, "games")
# 1.0-4.0 (2026-09-28) va 5.0-7.0 skill darslari (2026-09-29) — hamma daraja
COURSES = ("ielts_1_0", "ielts_2_0", "ielts_3_0", "ielts_4_0",
           "ielts_5_0", "ielts_6_0", "ielts_7_0")

# ------------------------------------------------------------ turlar
# name — inglizcha nomi, uz — o'zbekcha, skill — nimani mashq qiladi,
# kit — PDF'da avtomat yoziladigan "kerakli narsalar".
TYPES = {
    "auction": {"name": "Grammar Auction", "uz": "Grammatika auksioni", "skill": "grammar",
                "kit": ["Har jamoaga bittadan auksion varag'i (PDF'dagi varaq)",
                        "Doska va marker — gaplar bittadan yoziladi"]},
    "board": {"name": "Board Game", "uz": "Stol o'yini (zar bilan)", "skill": "grammar",
              "kit": ["O'yin taxtasi — har 3–4 o'quvchiga bittadan (A4 albom)",
                      "Zar (kub) va har o'yinchiga fishka (tanga, qalpoqcha)"]},
    "dominoes": {"name": "Dominoes", "uz": "Domino", "skill": "grammar",
                 "kit": ["Domino toshlari — har jamoaga bir to'plam (qaychi bilan qirqiladi)",
                         "Konvert yoki qisqich — to'plamlar aralashib ketmasin"]},
    "taboo": {"name": "Taboo", "uz": "Taboo kartalari", "skill": "vocab",
              "kit": ["Taboo kartalari — qirqib, teskari qilib dasta qilinadi",
                      "Soat yoki telefon taymeri (har navbat 60 soniya)"]},
    "find_someone": {"name": "Find Someone Who", "uz": "Kim …? (so'rovnoma)", "skill": "speaking",
                     "kit": ["Har o'quvchiga bittadan so'rovnoma varag'i", "Ruchka"]},
    "speaking_cards": {"name": "Speaking Cards", "uz": "Gapirish kartalari", "skill": "speaking",
                       "kit": ["Savol kartalari — juftlik yoki guruhga bir to'plam",
                               "Taymer (har javob 30–60 soniya)"]},
    "scramble": {"name": "Sentence Race", "uz": "Gap yig'ish poygasi", "skill": "grammar",
                 "kit": ["So'z kartochkalari — har jamoaga bir to'plam (qirqib, aralashtiriladi)",
                         "Konvert — har jamoaga bittadan"]},
    "quiz_board": {"name": "Quiz Board", "uz": "Viktorina taxtasi (Jeopardy)", "skill": "mixed",
                   "kit": ["Viktorina taxtasi — doskaga chizing yoki proyektorga qo'ying",
                           "Doska — jamoalar hisobi uchun"]},
    "memory": {"name": "Memory Pairs", "uz": "Juftini top (Memory)", "skill": "vocab",
               "kit": ["Kartalar — har 3–4 o'quvchiga bir to'plam (qirqib, teskari qo'yiladi)"]},
    "bingo": {"name": "Vocabulary Bingo", "uz": "Lug'at Bingo", "skill": "vocab",
              "kit": ["Bingo kartalari — har o'quvchiga bittadan (16 xil karta)",
                      "Ruchka yoki qalam — topilgan so'zni belgilash uchun"]},
}
AUTHORED = ("auction", "board", "dominoes", "taboo", "find_someone",
            "speaking_cards", "scramble", "quiz_board", "memory")
# Har darsda bo'lishi shart bo'lgan turlar (memory — ixtiyoriy, lug'at
# jufti avtomat qo'shiladi)
CORE_TYPES = AUTHORED[:-1]
SKILL_UZ = {"grammar": "Grammatika", "vocab": "Lug'at", "speaking": "Gapirish", "mixed": "Aralash"}

# Matn chegaralari — karta/katakka sig'ishi uchun (belgilar soni)
LIM = {
    "title": 70, "stage": 140, "players": 60, "goal": 240, "rule": 240, "material": 120,
    "auction_s": 110, "auction_fix": 110, "auction_why": 110,
    "board_t": 90, "board_a": 100,
    "domino": 55, "taboo_word": 28, "taboo_ban": 22,
    "find_t": 75, "find_q": 85, "speak": 130, "scramble": 100,
    "quiz_cat": 24, "quiz_q": 120, "quiz_a": 70, "memory": 45,
}
NW = 28.35                # "№" ustuni kengligi (1 sm) — 2 xonali son bo'linmasin
BOARD_TASKS = 24
# Taxtadagi maxsus kataklar (1 = START, 30 = FINISH)
BOARD_SPECIAL = {7: "+2 katak oldinga!", 13: "3 katak orqaga", 18: "Yana bir marta zar tashla!",
                 24: "Bir navbat o'tkazib yuborasan"}


# ------------------------------------------------------------ yuklash
@lru_cache(maxsize=8)
def _load_games(course: str) -> dict:
    if not re.fullmatch(r"[a-z0-9_]+", course or ""):
        return {}
    path = os.path.join(GAMES_DIR, course + ".json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return d.get("lessons") or {}


def _vocab_pairs(L: dict, tiers=("core", "strong")) -> list:
    """[(inglizcha, o'zbekcha)] — takrorlarsiz, tartib saqlanadi."""
    out, seen = [], set()
    V = L.get("vocab") or {}
    for t in tiers:
        for e in V.get(t) or []:
            if len(e) < 2:
                continue
            en, uz = _head(str(e[0])).strip(), str(e[1]).strip()
            if en and uz and en.lower() not in seen:
                seen.add(en.lower())
                out.append((en, uz))
    return out


def _auto_games(course: str, L: dict) -> list:
    """Lug'atdan avtomat Bingo va Memory."""
    out = []
    pool = _vocab_pairs(L)
    # Bingo uchun uchala daraja: 6.0/7.0 da lug'at 10/6/4 bo'lib, CORE+STRONG
    # atigi 16 so'z (2026-09-29). 1.0-4.0 da birinchi 24 so'z o'zgarmaydi.
    pool_all = _vocab_pairs(L, ("core", "strong", "super"))
    topic = L.get("vocab_topic") or ""
    if len(pool_all) >= 20:
        words = pool_all[:24]
        out.append({
            "id": "bingo", "type": "bingo", "auto": True,
            "title": f"Vocabulary Bingo — {topic}"[:LIM["title"]],
            "stage": "Lug'at bosqichidan keyin yoki dars oxirida takror",
            "minutes": 10, "players": "Butun sinf, har kim o'zi",
            "goal": "Darsning yangi so'zlarini tarjimasidan tanib olish va tez topish.",
            "rules": [
                "Har o'quvchiga bittadan Bingo kartasi bering (16 xil karta bor — yonidagi bilan bir xil emas).",
                "Ustoz 'Ustoz ro'yxati'dan so'zning O'ZBEKCHA tarjimasini o'qiydi (tartib aralash).",
                "O'quvchi kartasida shu so'zning inglizchasini topsa, katakni belgilaydi.",
                "Bir qator (gorizontal, vertikal yoki diagonal) to'lsa — 'BINGO!' deb qichqiradi.",
                "G'olib belgilagan so'zlarini inglizcha o'qib beradi va har biri bilan qisqa gap tuzadi; xato bo'lsa o'yin davom etadi.",
                "Kuchli guruhda o'zbekchasi o'rniga inglizcha ta'rif yoki misol gapni bo'sh joy bilan o'qing.",
            ],
            "data": {"words": [list(w) for w in words]},
        })
    if len(pool) >= 12:
        rnd = random.Random(f"{course}:{L['no']}:memory")
        pairs = rnd.sample(pool[:20], 12) if len(pool) >= 20 else pool[:12]
        out.append({
            "id": "memory_vocab", "type": "memory", "auto": True,
            "title": f"Memory Pairs — {topic}"[:LIM["title"]],
            "stage": "Lug'at bosqichida mustahkamlash (so'zlar tushuntirilgandan keyin)",
            "minutes": 12, "players": "3–4 kishilik guruhlar",
            "goal": "So'z va tarjimasini juftlab eslab qolish; talaffuz bilan birga takrorlash.",
            "rules": [
                "Kartalarni qirqib, aralashtiring va stolga yuzini pastga qaratib qator-qator qo'ying.",
                "Navbati kelgan o'quvchi 2 ta kartani ochadi va inglizcha so'zni baland ovozda aytadi.",
                "Inglizcha so'z va uning tarjimasi chiqsa — juftlik unga; yana bir marta ochadi.",
                "Juft chiqmasa — kartalar yana yopiladi, navbat keyingisiga o'tadi.",
                "Hamma juftlar topilgach, eng ko'p juft yig'gan g'olib. Bonus: har jufti bilan bitta gap tuzsa +1.",
            ],
            "data": {"pairs": [list(p) for p in pairs]},
        })
    return out


def games_count(course: str, L: dict) -> int:
    """Darslar ro'yxati uchun tez hisob (nusxa ko'chirmasdan)."""
    if course not in COURSES:
        return 0
    pool = len(_vocab_pairs(L))
    pool_all = len(_vocab_pairs(L, ("core", "strong", "super")))
    return len(_load_games(course).get(str(L["no"])) or []) + (pool_all >= 20) + (pool >= 12)


def lesson_games(course: str, L: dict) -> list:
    """Dars o'yinlari: mualliflik + avtomat, web va PDF uchun bir xil."""
    out = []
    for g in _load_games(course).get(str(L["no"])) or []:
        g = copy.deepcopy(g)
        g["auto"] = False
        out.append(g)
    out.extend(_auto_games(course, L))
    for g in out:
        t = TYPES.get(g.get("type"), {})
        g["type_name"] = t.get("name", g.get("type"))
        g["type_uz"] = t.get("uz", "")
        g.setdefault("skill", t.get("skill", "mixed"))
        g["kit"] = list(t.get("kit", [])) + list(g.get("materials") or [])
    return out


# ------------------------------------------------------------ tekshiruv
def _s(v) -> str:
    return v if isinstance(v, str) else ""


def check_game(g) -> list:
    """Bitta mualliflik o'yinining xatolari (bo'sh ro'yxat — joyida)."""
    e = []
    if not isinstance(g, dict):
        return ["o'yin obyekt emas"]
    gid = _s(g.get("id"))
    tag = gid or "?"

    def err(msg):
        e.append(f"[{tag}] {msg}")

    def txt(key, v, lim, need=True):
        if not isinstance(v, str) or (need and not v.strip()):
            err(f"{key} bo'sh yoki matn emas")
        elif len(v) > lim:
            err(f"{key} juda uzun ({len(v)} > {lim}): {v[:40]}…")

    if not re.fullmatch(r"[a-z0-9_]{2,30}", gid):
        err("id faqat a-z, 0-9, _ (2-30 belgi)")
    t = g.get("type")
    if t not in AUTHORED:
        err(f"type noma'lum: {t!r} (ruxsat: {', '.join(AUTHORED)})")
        return e
    txt("title", g.get("title"), LIM["title"])
    txt("stage", g.get("stage"), LIM["stage"])
    txt("players", g.get("players"), LIM["players"])
    txt("goal", g.get("goal"), LIM["goal"])
    m = g.get("minutes")
    if not isinstance(m, int) or isinstance(m, bool) or not 5 <= m <= 30:
        err("minutes 5..30 butun son bo'lsin")
    rules = g.get("rules")
    if not isinstance(rules, list) or not 3 <= len(rules) <= 8:
        err("rules 3..8 ta qadam bo'lsin")
    else:
        for i, r in enumerate(rules):
            txt(f"rules[{i}]", r, LIM["rule"])
    mats = g.get("materials", [])
    if not isinstance(mats, list) or len(mats) > 3:
        err("materials — ko'pi bilan 3 ta qator (ro'yxat)")
    else:
        for i, r in enumerate(mats):
            txt(f"materials[{i}]", r, LIM["material"])
    if g.get("skill") not in (None, "grammar", "vocab", "speaking", "mixed"):
        err("skill: grammar | vocab | speaking | mixed")
    d = g.get("data")
    if not isinstance(d, dict):
        err("data obyekt bo'lsin")
        return e

    if t == "auction":
        items = d.get("items")
        if not isinstance(items, list) or not 10 <= len(items) <= 12:
            err("auction: items 10..12 ta")
            return e
        bad = 0
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                err(f"items[{i}] obyekt emas")
                continue
            txt(f"items[{i}].s", it.get("s"), LIM["auction_s"])
            if not isinstance(it.get("ok"), bool):
                err(f"items[{i}].ok true/false bo'lsin")
            elif not it["ok"]:
                bad += 1
                txt(f"items[{i}].fix", it.get("fix"), LIM["auction_fix"])
                if _s(it.get("fix")).strip() == _s(it.get("s")).strip():
                    err(f"items[{i}].fix xato gap bilan bir xil")
            txt(f"items[{i}].why", it.get("why"), LIM["auction_why"])
        if not 0.4 <= bad / len(items) <= 0.6:
            err(f"auction: xato gaplar ulushi 40–60% bo'lsin (hozir {bad}/{len(items)})")
        mo = d.get("money", 1000)
        if not isinstance(mo, int) or not 100 <= mo <= 10000:
            err("auction: money 100..10000")
    elif t == "board":
        sq = d.get("squares")
        if not isinstance(sq, list) or len(sq) != BOARD_TASKS:
            err(f"board: squares aynan {BOARD_TASKS} ta")
            return e
        for i, it in enumerate(sq):
            if not isinstance(it, dict):
                err(f"squares[{i}] obyekt emas")
                continue
            txt(f"squares[{i}].t", it.get("t"), LIM["board_t"])
            txt(f"squares[{i}].a", it.get("a"), LIM["board_a"])
    elif t == "dominoes":
        pairs = d.get("pairs")
        if not isinstance(pairs, list) or not 12 <= len(pairs) <= 16:
            err("dominoes: pairs 12..16 ta")
            return e
        for i, p in enumerate(pairs):
            if not (isinstance(p, list) and len(p) == 2):
                err(f"pairs[{i}] [chap, o'ng] bo'lsin")
                continue
            txt(f"pairs[{i}][0]", p[0], LIM["domino"])
            txt(f"pairs[{i}][1]", p[1], LIM["domino"])
        lefts = [_s(p[0]).strip().lower() for p in pairs if isinstance(p, list) and len(p) == 2]
        rights = [_s(p[1]).strip().lower() for p in pairs if isinstance(p, list) and len(p) == 2]
        if len(set(lefts)) != len(lefts) or len(set(rights)) != len(rights):
            err("dominoes: chap va o'ng qismlar takrorlanmasin")
    elif t == "taboo":
        cards = d.get("cards")
        if not isinstance(cards, list) or not 12 <= len(cards) <= 16:
            err("taboo: cards 12..16 ta")
            return e
        seen = set()
        for i, c in enumerate(cards):
            if not isinstance(c, dict):
                err(f"cards[{i}] obyekt emas")
                continue
            txt(f"cards[{i}].word", c.get("word"), LIM["taboo_word"])
            w = _s(c.get("word")).strip().lower()
            if w in seen:
                err(f"taboo: '{w}' takrorlandi")
            seen.add(w)
            ban = c.get("taboo")
            if not isinstance(ban, list) or len(ban) != 3:
                err(f"cards[{i}].taboo aynan 3 ta so'z")
            else:
                for j, b in enumerate(ban):
                    txt(f"cards[{i}].taboo[{j}]", b, LIM["taboo_ban"])
    elif t == "find_someone":
        items = d.get("items")
        if not isinstance(items, list) or not 10 <= len(items) <= 12:
            err("find_someone: items 10..12 ta")
            return e
        for i, it in enumerate(items):
            if not isinstance(it, dict):
                err(f"items[{i}] obyekt emas")
                continue
            txt(f"items[{i}].t", it.get("t"), LIM["find_t"])
            txt(f"items[{i}].q", it.get("q"), LIM["find_q"])
    elif t == "speaking_cards":
        cards = d.get("cards")
        if not isinstance(cards, list) or not 12 <= len(cards) <= 16:
            err("speaking_cards: cards 12..16 ta")
            return e
        for i, c in enumerate(cards):
            txt(f"cards[{i}]", c, LIM["speak"])
    elif t == "scramble":
        ss = d.get("sentences")
        if not isinstance(ss, list) or not 8 <= len(ss) <= 10:
            err("scramble: sentences 8..10 ta")
            return e
        for i, s in enumerate(ss):
            txt(f"sentences[{i}]", s, LIM["scramble"])
            n = len(_s(s).split())
            if not 4 <= n <= 14:
                err(f"sentences[{i}] 4..14 so'z bo'lsin (hozir {n})")
    elif t == "quiz_board":
        cats = d.get("categories")
        if not isinstance(cats, list) or len(cats) != 4:
            err("quiz_board: categories aynan 4 ta")
            return e
        for i, c in enumerate(cats):
            if not isinstance(c, dict):
                err(f"categories[{i}] obyekt emas")
                continue
            txt(f"categories[{i}].name", c.get("name"), LIM["quiz_cat"])
            qs = c.get("qs")
            if not isinstance(qs, list) or len(qs) != 5:
                err(f"categories[{i}].qs aynan 5 ta (100..500)")
                continue
            for j, q in enumerate(qs):
                if not isinstance(q, dict):
                    err(f"categories[{i}].qs[{j}] obyekt emas")
                    continue
                txt(f"categories[{i}].qs[{j}].q", q.get("q"), LIM["quiz_q"])
                txt(f"categories[{i}].qs[{j}].a", q.get("a"), LIM["quiz_a"])
    elif t == "memory":
        pairs = d.get("pairs")
        if not isinstance(pairs, list) or not 12 <= len(pairs) <= 16:
            err("memory: pairs 12..16 ta")
            return e
        for i, p in enumerate(pairs):
            if not (isinstance(p, list) and len(p) == 2):
                err(f"pairs[{i}] [a, b] bo'lsin")
                continue
            txt(f"pairs[{i}][0]", p[0], LIM["memory"])
            txt(f"pairs[{i}][1]", p[1], LIM["memory"])
    return e


def check_lesson(games) -> list:
    """Bitta darsning mualliflik o'yinlari: 8 ta asosiy turning HAMMASI
    (2026-09-28, Jahongir: "dars rejasiga qosh hamma pdf li oyinlarni har
    bir darsga") + ixtiyoriy memory; turlar takrorlanmaydi."""
    if not isinstance(games, list):
        return ["dars o'yinlari ro'yxat bo'lsin"]
    e = []
    for g in games:
        e.extend(check_game(g))
    ids = [g.get("id") for g in games if isinstance(g, dict)]
    types = [g.get("type") for g in games if isinstance(g, dict)]
    missing = [t for t in CORE_TYPES if t not in types]
    if missing:
        e.append(f"darsda har turdan bittadan o'yin bo'lsin — yetishmaydi: {', '.join(missing)}")
    if len(set(ids)) != len(ids):
        e.append("id lar takrorlanmasin")
    if len(set(types)) != len(types):
        e.append("bitta darsda bir xil turdagi o'yin ikki marta bo'lmasin")
    if ("bingo" in ids) or ("memory_vocab" in ids):
        e.append("'bingo' va 'memory_vocab' id lari avtomat o'yinlarga band")
    return e


# ------------------------------------------------------------ PDF
_ST = {}


def _styles() -> dict:
    if _ST:
        return _ST
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    _fonts()
    ink = colors.HexColor("#0F172A")
    _ST.update(
        h=ParagraphStyle("gh", fontName="DV-B", fontSize=15, leading=19, textColor=ink),
        kind=ParagraphStyle("gk", fontName="DV-B", fontSize=9, leading=12,
                            textColor=colors.HexColor("#1A6FE4")),
        meta=ParagraphStyle("gm", fontName="DV", fontSize=8.8, leading=12,
                            textColor=colors.HexColor("#475569")),
        sec=ParagraphStyle("gs", fontName="DV-B", fontSize=10.5, leading=14, textColor=ink,
                           spaceBefore=8, spaceAfter=3),
        body=ParagraphStyle("gb", fontName="DV", fontSize=9.3, leading=12.6, textColor=ink),
        cell=ParagraphStyle("gc", fontName="DV", fontSize=8.4, leading=10.6, textColor=ink),
        head=ParagraphStyle("gth", fontName="DV-B", fontSize=8.4, leading=10.6, textColor=ink),
        mat=ParagraphStyle("gmt", fontName="DV-B", fontSize=12, leading=15, textColor=ink),
        hint=ParagraphStyle("ghi", fontName="DV", fontSize=8, leading=10.5,
                            textColor=colors.HexColor("#64748B")),
    )
    return _ST


def _x(s) -> str:
    return escape(str(s or ""))


def _fit(text: str, w: float, h: float, size: float = 11, bold: bool = False,
         align: int = 1, color: str = "#0F172A", min_size: float = 5.5):
    """Matnni katakka sig'diradi — sig'maguncha shriftni kichraytiradi.
    Eng uzun so'z ham kenglikka sig'ishi shart: aks holda reportlab uni
    harflab bo'lib yuboradi ("handsom-e")."""
    import html as _html
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.platypus import Paragraph
    plain = _html.unescape(re.sub(r"<[^>]+>", " ", text))
    # "rosy-cheeked" defis joyida bo'linishi mumkin (embeddedHyphenation)
    parts = [p for wd in plain.split() for p in re.split(r"(?<=-)", wd) if p]
    longest = max((stringWidth(p, "DV-B", 1) for p in parts), default=0)
    s = size
    while True:
        st = ParagraphStyle("fit", fontName="DV-B" if bold else "DV", fontSize=s,
                            leading=s * 1.2, alignment=align, textColor=colors.HexColor(color),
                            embeddedHyphenation=1)
        p = Paragraph(text, st)
        _, ph = p.wrap(w, h)
        if (ph <= h and longest * s <= w) or s <= min_size:
            return p
        s -= 0.5


def _cut_grid(data, col_w, row_h, bg=None, pad=4):
    """Qirqiladigan kartalar jadvali: shtrix chiziq — qaychi yo'li."""
    from reportlab.lib import colors
    from reportlab.platypus import Table, TableStyle
    t = Table(data, colWidths=col_w, rowHeights=row_h)
    st = [("GRID", (0, 0), (-1, -1), 0.7, colors.HexColor("#94A3B8"), None, (4, 3)),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER"),
          ("LEFTPADDING", (0, 0), (-1, -1), pad), ("RIGHTPADDING", (0, 0), (-1, -1), pad),
          ("TOPPADDING", (0, 0), (-1, -1), pad), ("BOTTOMPADDING", (0, 0), (-1, -1), pad)]
    st.extend(bg or [])
    t.setStyle(TableStyle(st))
    return t


def _key_table(head, rows, widths):
    from reportlab.lib import colors
    from reportlab.platypus import Paragraph, Table, TableStyle
    S = _styles()
    data = [[Paragraph(_x(h), S["head"]) for h in head]]
    for r in rows:
        data.append([Paragraph(c, S["cell"]) if isinstance(c, str) else c for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9E2F3")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B8C4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FD")]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))
    return t


def _mat_title(text, hint=""):
    from reportlab.platypus import Paragraph, Spacer
    S = _styles()
    out = [Paragraph(_x(text), S["mat"])]
    if hint:
        out.append(Paragraph(_x(hint), S["hint"]))
    out.append(Spacer(1, 6))
    return out


def _board_cells(d: dict) -> dict:
    """Taxta katagi raqami -> (yorliq, rang, matn, javob)."""
    tasks = list(d.get("squares") or [])
    cells, k = {}, 0
    for n in range(1, 31):
        if n == 1:
            cells[n] = ("START", "#DCFCE7", "Boshlanish", "")
        elif n == 30:
            cells[n] = ("FINISH", "#FDE68A", "Marra — g'olib!", "")
        elif n in BOARD_SPECIAL:
            cells[n] = (str(n), "#FCE7F3", BOARD_SPECIAL[n], "")
        else:
            sq = tasks[k] if k < len(tasks) else {}
            cells[n] = (str(n), "#FFFFFF" if n % 2 else "#EFF6FF", sq.get("t", ""), sq.get("a", ""))
            k += 1
    return cells


# --- javoblar kaliti (ustoz sahifasi)
def _key(g, W):
    from reportlab.lib.units import cm
    t, d = g["type"], g.get("data") or {}
    if t == "auction":
        rows = []
        for i, it in enumerate(d.get("items") or [], 1):
            ok = it.get("ok")
            rows.append([str(i), _x(it.get("s")), "✓ To'g'ri" if ok else "✗ Xato",
                         "—" if ok else f"<b>{_x(it.get('fix'))}</b>", _x(it.get("why"))])
        return _key_table(["№", "Gap", "Javob", "To'g'risi", "Nega"], rows,
                          [NW, W * 0.33, 1.8 * cm, W * 0.27, W * 0.4 - 1.8 * cm - NW])
    if t == "board":
        cells = _board_cells(d)
        rows = [[str(n), _x(cells[n][2]), f"<b>{_x(cells[n][3])}</b>"]
                for n in range(2, 30) if n not in BOARD_SPECIAL]
        return _key_table(["Katak", "Topshiriq", "Javob"], rows, [1.5 * cm, W * 0.55, W * 0.45 - 1.5 * cm])
    if t == "dominoes":
        rows = [[str(i), _x(a), f"<b>{_x(b)}</b>"] for i, (a, b) in enumerate(d.get("pairs") or [], 1)]
        return _key_table(["№", "Birinchi qism", "Ulanadigan qism"], rows, [NW, W * 0.47, W * 0.53 - NW])
    if t == "find_someone":
        rows = [[str(i), _x(it.get("t")), f"<b>{_x(it.get('q'))}</b>"]
                for i, it in enumerate(d.get("items") or [], 1)]
        return _key_table(["№", "Find someone who…", "To'g'ri savol"], rows, [NW, W * 0.47, W * 0.53 - NW])
    if t == "scramble":
        rows = [[str(i), f"<b>{_x(s)}</b>"] for i, s in enumerate(d.get("sentences") or [], 1)]
        return _key_table(["№", "To'g'ri gap"], rows, [NW, W - NW])
    if t == "quiz_board":
        rows = []
        for c in d.get("categories") or []:
            for j, q in enumerate(c.get("qs") or []):
                rows.append([_x(c.get("name")) if j == 0 else "", str((j + 1) * 100),
                             _x(q.get("q")), f"<b>{_x(q.get('a'))}</b>"])
        return _key_table(["Bo'lim", "Ball", "Savol", "Javob"], rows,
                          [W * 0.16, 1.2 * cm, W * 0.5, W * 0.34 - 1.2 * cm])
    if t == "bingo":
        # chaqiruv ro'yxati ikki ustunda — ustoz sahifasiga sig'sin
        rnd = random.Random(f"{g.get('_seed')}:call")
        words = list(d.get("words") or [])
        rnd.shuffle(words)
        cells = [["☐ " + str(i), _x(uz), f"<b>{_x(en)}</b>"] for i, (en, uz) in enumerate(words, 1)]
        half = (len(cells) + 1) // 2
        rows = [cells[k] + (cells[k + half] if k + half < len(cells) else ["", "", ""])
                for k in range(half)]
        cw = (W - 2 * 1.2 * cm) / 2
        return _key_table(["", "O'qiladi", "So'z", "", "O'qiladi", "So'z"], rows,
                          [1.2 * cm, cw * 0.55, cw * 0.45] * 2)
    if t == "memory":
        rows = [[str(i), f"<b>{_x(a)}</b>", _x(b)] for i, (a, b) in enumerate(d.get("pairs") or [], 1)]
        return _key_table(["№", "A karta", "B karta (jufti)"], rows, [NW, W * 0.47, W * 0.53 - NW])
    return None                          # taboo, speaking_cards — kalit shart emas


# --- o'quvchilar uchun chop etiladigan materiallar
def _mat_board(g, d, WL, HL):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle
    out = _mat_title(g["title"], "Zar tashlang, katakdagi topshiriqni bajaring. Xato bo'lsa — oldingi joyingizga qayting.")
    cols, rows_n = 6, 5
    cw, rh = WL / cols, (HL - 1.6 * cm) / rows_n
    cells = _board_cells(d)
    data, bg = [], []
    for r in range(rows_n):
        level = rows_n - 1 - r                        # pastdan yuqoriga
        nums = [level * cols + c + 1 for c in range(cols)]
        if level % 2 == 1:
            nums.reverse()                            # ilon yo'li
        row = []
        for c, n in enumerate(nums):
            lab, col, body, _a = cells[n]
            row.append(_fit(f"<font size=12><b>{_x(lab)}</b></font><br/>{_x(body)}", cw - 8, rh - 8, size=8.6))
            bg.append(("BACKGROUND", (c, r), (c, r), colors.HexColor(col)))
        data.append(row)
    t = Table(data, colWidths=[cw] * cols, rowHeights=[rh] * rows_n)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1.1, colors.HexColor("#1A6FE4")),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")] + bg))
    return out + [t]


def _mat_quiz(g, d, WL, HL):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle
    cats = d.get("categories") or []
    out = _mat_title(g["title"], "Jamoa bo'lim va ballni tanlaydi; to'g'ri javob — ball, xato — savol boshqa jamoaga o'tadi.")
    cw, rh = WL / 4, (HL - 1.8 * cm) / 6
    data = [[_fit(f"<b>{_x(c.get('name'))}</b>", cw - 10, rh - 10, size=15, bold=True, color="#FFFFFF")
             for c in cats]]
    for j in range(5):
        data.append([_fit(f"<b>{(j + 1) * 100}</b>", cw - 10, rh - 10, size=30, bold=True, color="#1A6FE4")
                     for _c in cats])
    t = Table(data, colWidths=[cw] * 4, rowHeights=[rh] * 6)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1.5, colors.white),
                           ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A6FE4")),
                           ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#EFF6FF")),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return out + [t]


def _mat_auction(g, d, W):
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, Spacer, TableStyle
    S = _styles()
    items = d.get("items") or []
    out = _mat_title(f"Auksion varag'i — {g['title']}",
                     f"Jamoa nomi: ____________________     Boshlang'ich pul: {d.get('money', 1000)}     "
                     "Qolgan pul: __________")
    rows = [[str(i), _x(it.get("s")), "", "", ""] for i, it in enumerate(items, 1)]
    tb = _key_table(["№", "Gap", "To'g'ri / Xato?", "Tikildi", "Natija (+/−)"], rows,
                    [NW, W - 7.0 * cm - NW, 2.4 * cm, 2.2 * cm, 2.4 * cm])
    tb.setStyle(TableStyle([("TOPPADDING", (0, 1), (-1, -1), 7), ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
                            ("VALIGN", (0, 1), (-1, -1), "MIDDLE")]))
    return out + [tb, Spacer(1, 8), Paragraph("Yutib olingan to'g'ri gaplar: ______     Oxirgi pul: ______", S["body"])]


def _mat_find(g, d, W):
    from reportlab.lib.units import cm
    from reportlab.platypus import TableStyle
    items = d.get("items") or []
    out = _mat_title("Find someone who… — so'rovnoma",
                     "Sinfda yuring va savolni o'zingiz tuzib bering. 'Yes' degan odamning ismini yozing va yana bitta savol bering.")
    rows = [[str(i), _x(it.get("t")), "", "", ""] for i, it in enumerate(items, 1)]
    tb = _key_table(["№", "Find someone who…", "Mening savolim", "Ism", "Qo'shimcha ma'lumot"], rows,
                    [NW, W * 0.36, W * 0.3, W * 0.13, W * 0.21 - NW])
    tb.setStyle(TableStyle([("TOPPADDING", (0, 1), (-1, -1), 9), ("BOTTOMPADDING", (0, 1), (-1, -1), 9),
                            ("VALIGN", (0, 1), (-1, -1), "MIDDLE")]))
    return out + [tb]


def _mat_dominoes(g, d, W, H, rnd):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import Table, TableStyle
    pairs = list(d.get("pairs") or [])
    out = _mat_title(f"Domino — {g['title']}",
                     "✂ Shtrix chiziq bo'ylab qirqing. START toshidan boshlab, o'ng tomondagi matnga mos davomni toping.")
    # tosh = (oldingi juftning 2-qismi | keyingi juftning 1-qismi)
    tiles = [("START", pairs[0][0])]
    for i in range(len(pairs)):
        tiles.append((pairs[i][1], pairs[i + 1][0] if i + 1 < len(pairs) else "FINISH"))
    rest = tiles[1:]
    rnd.shuffle(rest)
    tiles = [tiles[0]] + rest
    tw = W / 2
    th = min(2.6 * cm, (H - 2.4 * cm) / ((len(tiles) + 1) // 2))
    cells = []
    for a, b in tiles:
        inner = Table([[_fit(_x(a), tw / 2 - 14, th - 14, size=10, bold=a in ("START", "FINISH")),
                        _fit(_x(b), tw / 2 - 14, th - 14, size=10, bold=b in ("START", "FINISH"))]],
                      colWidths=[tw / 2 - 5, tw / 2 - 5], rowHeights=[th - 8])
        inner.setStyle(TableStyle([("LINEAFTER", (0, 0), (0, 0), 1.4, colors.HexColor("#1A6FE4")),
                                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                   ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC"))]))
        cells.append(inner)
    if len(cells) % 2:
        cells.append("")
    data = [cells[i:i + 2] for i in range(0, len(cells), 2)]
    return out + [_cut_grid(data, [tw, tw], [th] * len(data), pad=3)]


def _mat_cards(title, hint, texts, W, H, cols, rows_n, size, bgs=None):
    """Umumiy qirqiladigan kartalar (taboo, speaking, memory)."""
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import PageBreak
    out = []
    per = cols * rows_n
    cw, rh = W / cols, (H - 2.0 * cm) / rows_n
    for p in range(0, len(texts), per):
        if p:
            out.append(PageBreak())
        out += _mat_title(title, hint)
        cells, bg = [], []
        for k, txt in enumerate(texts[p:p + per]):
            cells.append(_fit(txt, cw - 16, rh - 14, size=size))
            if bgs:
                bg.append(("BACKGROUND", (k % cols, k // cols), (k % cols, k // cols),
                           colors.HexColor(bgs[p + k])))
        while len(cells) % cols:
            cells.append("")
        data = [cells[i:i + cols] for i in range(0, len(cells), cols)]
        out.append(_cut_grid(data, [cw] * cols, [rh] * len(data), bg=bg, pad=7))
    return out


def _mat_scramble(g, d, W, rnd):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.pdfbase.pdfmetrics import stringWidth
    from reportlab.platypus import Spacer
    out = _mat_title(f"Sentence race — {g['title']}",
                     "✂ So'zlarni qirqib, har gapni alohida konvertga soling. Jamoa so'zlarni to'g'ri tartibda teradi — kim tez?")
    for i, s in enumerate(d.get("sentences") or [], 1):
        words = s.split()
        rnd.shuffle(words)
        line, lines, w_line = [], [], 0.0
        for w in words:
            ww = min(W, max(1.6 * cm, stringWidth(w, "DV-B", 11) + 22))
            if line and w_line + ww > W:
                lines.append(line)
                line, w_line = [], 0.0
            line.append((w, ww))
            w_line += ww
        if line:
            lines.append(line)
        for ln in lines:
            row = [_fit(f"<font size=6 color='#94A3B8'>{i}</font> <b>{_x(w)}</b>", ww - 8, 1.0 * cm, size=11)
                   for w, ww in ln]
            out.append(_cut_grid([row], [ww for _w, ww in ln], [1.15 * cm], pad=3,
                                 bg=[("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC"))]))
        out.append(Spacer(1, 7))
    return out


def _mat_bingo(g, d, W, H, rnd):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import PageBreak, Paragraph, Table, TableStyle
    S = _styles()
    words = [tuple(w) for w in d.get("words") or []]
    n_cards = 16
    cw, ch = W / 2, (H - 1.6 * cm) / 2
    cell = min((cw - 1.2 * cm) / 4, (ch - 2.4 * cm) / 4)
    cards = []
    for k in range(n_cards):
        pick = rnd.sample(words, 16)
        grid = [[_fit(f"<b>{_x(en)}</b>", cell - 6, cell - 6, size=10, bold=True)
                 for en, _uz in pick[r * 4:(r + 1) * 4]] for r in range(4)]
        gt = Table(grid, colWidths=[cell] * 4, rowHeights=[cell] * 4)
        gt.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#1A6FE4")),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 2), ("RIGHTPADDING", (0, 0), (-1, -1), 2)]))
        head = _fit(f"<font color='#1A6FE4'><b>B I N G O</b></font>  <font size=8 color='#94A3B8'>karta {k + 1}</font>",
                    cw - 1 * cm, 0.9 * cm, size=17, bold=True)
        box = Table([[head], [gt], [Paragraph("Ism: ______________________", S["hint"])]],
                    rowHeights=[1.0 * cm, cell * 4 + 0.2 * cm, 0.6 * cm])
        box.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
        cards.append(box)
    out = []
    for p in range(0, n_cards, 4):
        if p:
            out.append(PageBreak())
        out += _mat_title(f"Bingo kartalari ({p + 1}–{p + 4})", "✂ Qirqing — har o'quvchiga bittadan.")
        chunk = cards[p:p + 4]
        out.append(_cut_grid([chunk[0:2], chunk[2:4]], [cw, cw], [ch] * 2, pad=4))
    return out


def _materials(g, W, H, WL, HL):
    """(albommi?, flowables) — o'quvchilar uchun chop etiladigan qism."""
    t, d = g["type"], g.get("data") or {}
    rnd = random.Random(f"{g.get('_seed')}:mat")
    if t == "board":
        return True, _mat_board(g, d, WL, HL)
    if t == "quiz_board":
        return True, _mat_quiz(g, d, WL, HL)
    if t == "auction":
        return False, _mat_auction(g, d, W)
    if t == "find_someone":
        return False, _mat_find(g, d, W)
    if t == "dominoes":
        return False, _mat_dominoes(g, d, W, H, rnd)
    if t == "scramble":
        return False, _mat_scramble(g, d, W, rnd)
    if t == "bingo":
        return False, _mat_bingo(g, d, W, H, rnd)
    if t == "taboo":
        texts = []
        for c in d.get("cards") or []:
            ban = "<br/>".join(f"• {_x(b)}" for b in c.get("taboo") or [])
            texts.append(f"<font size=17 color='#1A6FE4'><b>{_x(str(c.get('word', '')).upper())}</b></font><br/><br/>"
                         f"<font size=8 color='#B91C1C'><b>AYTISH MUMKIN EMAS:</b></font><br/>{ban}")
        return False, _mat_cards(f"Taboo — {g['title']}",
                                 "✂ Qirqing. So'zni tushuntiring, lekin uning o'zini va pastdagi 3 so'zni aytmang!",
                                 texts, W, H, 2, 4, 11)
    if t == "speaking_cards":
        texts = [f"<font size=8 color='#94A3B8'><b>{i}</b></font><br/>{_x(c)}"
                 for i, c in enumerate(d.get("cards") or [], 1)]
        return False, _mat_cards(f"Speaking cards — {g['title']}",
                                 "✂ Qirqing, dasta qilib teskari qo'ying. Kartani oling, savolni o'qing va javob bering.",
                                 texts, W, H, 2, 5, 12.5)
    if t == "memory":
        cards = [(a, "#EFF6FF") for a, _b in d.get("pairs") or []] + \
                [(b, "#FEF9C3") for _a, b in d.get("pairs") or []]
        rnd.shuffle(cards)
        return False, _mat_cards(f"Memory — {g['title']}",
                                 "✂ Qirqing, aralashtiring va yuzini pastga qaratib qo'ying. Ko'k karta — A, sariq karta — uning jufti.",
                                 [f"<b>{_x(c)}</b>" for c, _col in cards], W, H, 4, 6, 12,
                                 bgs=[col for _c, col in cards])
    return False, []


def build_games_pdf(course: str, L: dict, games: list) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.platypus import (BaseDocTemplate, Frame, NextPageTemplate, PageBreak,
                                    PageTemplate, Paragraph, Spacer, Table, TableStyle)
    S = _styles()
    if not games:
        raise HTTPException(404, "Bu darsda o'yin yo'q")
    buf = io.BytesIO()
    lm, tm, bm = 1.2 * cm, 1.9 * cm, 1.6 * cm
    pw, ph = A4
    lw, lh = landscape(A4)
    blue, grey = colors.HexColor("#1A6FE4"), colors.HexColor("#7F7F7F")
    logo = os.path.join(_ASSETS, "brand-icon.png")

    def deco(canvas, doc):
        w, h = canvas._pagesize
        canvas.saveState()
        canvas.setFont("DV-B", 54)
        canvas.setFillColor(colors.Color(0.72, 0.8, 0.92, alpha=0.10))
        canvas.translate(w / 2, h / 2)
        canvas.rotate(28)
        canvas.drawCentredString(0, 0, BRAND)
        canvas.restoreState()
        canvas.saveState()
        y = h - 1.25 * cm
        if os.path.exists(logo):
            canvas.drawImage(logo, lm, y - 0.15 * cm, width=0.62 * cm, height=0.62 * cm, mask="auto")
        canvas.setFont("DV-B", 10.5)
        canvas.setFillColor(blue)
        canvas.drawString(lm + 0.8 * cm, y, BRAND)
        canvas.setFont("DV", 7.5)
        canvas.setFillColor(grey)
        canvas.drawRightString(w - lm, y, f"Dars {L['no']} · {L.get('title', '')}"[:90])
        canvas.setStrokeColor(colors.HexColor("#D9E2F3"))
        canvas.line(lm, y - 0.35 * cm, w - lm, y - 0.35 * cm)
        canvas.setFont("DV", 7.2)
        canvas.drawCentredString(w / 2, 0.6 * cm, f"© Jony Academy · {CONTACT} · sahifa {doc.page}")
        canvas.restoreState()

    doc = BaseDocTemplate(buf, pagesize=A4, title=f"Dars {L['no']} — o'yinlar", author=BRAND,
                          leftMargin=lm, rightMargin=lm, topMargin=tm, bottomMargin=bm)
    W, H = pw - 2 * lm, ph - tm - bm
    WL, HL = lw - 2 * lm, lh - tm - bm
    doc.addPageTemplates([
        PageTemplate(id="P", pagesize=A4, onPage=deco,
                     frames=[Frame(lm, bm, W, H, id="fp", leftPadding=0, rightPadding=0,
                                   topPadding=0, bottomPadding=0)]),
        PageTemplate(id="L", pagesize=landscape(A4), onPage=deco,
                     frames=[Frame(lm, bm, WL, HL, id="fl", leftPadding=0, rightPadding=0,
                                   topPadding=0, bottomPadding=0)]),
    ])
    story = []
    for gi, g in enumerate(games):
        g = dict(g)
        g["_seed"] = f"{course}:{L['no']}:{g.get('id')}"
        if gi:
            story += [NextPageTemplate("P"), PageBreak()]
        # --- USTOZ UCHUN
        tinfo = TYPES.get(g["type"], {})
        story.append(Paragraph(f"USTOZ UCHUN · {_x(tinfo.get('uz', ''))} · {_x(tinfo.get('name', ''))}", S["kind"]))
        story.append(Paragraph(_x(g.get("title")), S["h"]))
        meta = (f"{g.get('minutes', '')} daqiqa · {_x(g.get('players'))} · "
                f"{SKILL_UZ.get(g.get('skill') or tinfo.get('skill'), '')} · Bosqich: {_x(g.get('stage'))}")
        story += [Paragraph(meta, S["meta"]), Spacer(1, 4)]
        box = Table([[Paragraph(f"<b>Maqsad:</b> {_x(g.get('goal'))}", S["body"])]], colWidths=[W])
        box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
                                 ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BFDBFE")),
                                 ("LEFTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 5),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        story.append(box)
        story.append(Paragraph("Kerakli narsalar", S["sec"]))
        story += [Paragraph(f"• {_x(k)}", S["body"])
                  for k in list(tinfo.get("kit", [])) + list(g.get("materials") or [])]
        story.append(Paragraph("Qanday o'ynaladi", S["sec"]))
        story += [Paragraph(f"<b>{i}.</b> {_x(r)}", S["body"]) for i, r in enumerate(g.get("rules") or [], 1)]
        key = _key(g, W)
        if key is not None:
            story.append(Paragraph("Javoblar kaliti (faqat ustoz uchun)", S["sec"]))
            story.append(key)
        # --- MATERIALLAR
        land, mats = _materials(g, W, H, WL, HL)
        if mats:
            story += [NextPageTemplate("L" if land else "P"), PageBreak()] + mats
    doc.build(story)
    return buf.getvalue()


# ------------------------------------------------------------ API
def _course_ok(course: str):
    if course not in COURSES:
        raise HTTPException(404, "Bu daraja uchun o'yinlar hali yo'q")


@router.get("/api/plans/{course}/{no}/games")
def list_games(course: str, no: int, db: Session = Depends(get_db),
               user=Depends(require_role(*roles.PLANS_ACCESS))):
    _english_only(db, user)
    _course_ok(course)
    L = _lesson(course, no)
    return {"course": course, "no": L["no"], "games": lesson_games(course, L)}


@router.get("/api/plans/{course}/{no}/games.pdf")
def games_pdf(course: str, no: int, id: str = "", db: Session = Depends(get_db),
              user=Depends(require_role(*roles.PLANS_ACCESS))):
    _english_only(db, user)
    _course_ok(course)
    L = _lesson(course, no)
    games = lesson_games(course, L)
    if id:
        games = [g for g in games if g.get("id") == id]
        if not games:
            raise HTTPException(404, "O'yin topilmadi")
    pdf = build_games_pdf(course, L, games)
    part = games[0]["id"] if id else "oyinlar"
    fname = f"Dars {L['no']} - {part}.pdf"
    return Response(pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


# ------------------------------------------------------------ CLI
def _cli_check(path: str) -> int:
    """Muallif fayli: sxema + har o'yin PDF'i quriladimi."""
    from liveplay import _load_course
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    course = d.get("course")
    full = _load_course(course) or {"lessons": []}
    by_no = {str(L["no"]): L for L in full["lessons"]}
    bad = 0
    for no, games in sorted((d.get("lessons") or {}).items(), key=lambda kv: int(kv[0])):
        L = by_no.get(str(no))
        errs = [] if L else [f"{course} da {no}-dars yo'q"]
        errs += check_lesson(games)
        if L and not errs:
            for g in games:
                try:
                    build_games_pdf(course, L, [dict(copy.deepcopy(g), auto=False)])
                except Exception as ex:                   # noqa: BLE001
                    errs.append(f"[{g.get('id')}] PDF qurilmadi: {type(ex).__name__}: {ex}")
        print(f"{course} {no}-dars: " + ("OK" if not errs else f"{len(errs)} xato"))
        for x in errs:
            print("   -", x)
        bad += len(errs)
    print(f"JAMI XATO: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "check":
        sys.exit(_cli_check(sys.argv[2]))
    print(__doc__)
