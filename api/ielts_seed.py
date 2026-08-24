# -*- coding: utf-8 -*-
"""IELTS LISTENING — 1-BLOK: SPELLING VA RAQAMLAR (2026-08-24).

Jahongir: "IELTS ochilganda listening, reading, writing, speaking
bo'limi bo'ladi. Listening bo'limda birinchi spelling names bo'lsin,
har xil britaniya shaxarlari kochalar nomlari, british odamlarni
ismlarini yozish bo'lsin spelling mashqlar 50ta kamida, keyin 50ta
number practice bolsin... tel raqam, carta raqam... va hammasi
sekinidan boshlab qiyinlashib borsin va tezlashib borsin asta
sekinlik bilan, 3-mashq spelling mixed koproq postcodelar harf va
son aralash ham 50ta".

UCH MASHQ:
  ielts_spell  — ism/shahar/ko'cha nomi harflab aytiladi, yoziladi;
  ielts_number — telefon, karta, sana, narx kabi raqamlar;
  ielts_mixed  — postcode va kod (harf + raqam aralash).

QIYINLIK VA TEZLIK. Har mashqda elementlar step (1..5) bo'yicha
saralangan: 1 — qisqa va tanish, 5 — uzun va chalg'ituvchi. Tezlik
step'dan kelib chiqadi (0.55x dan 1.0x gacha) — bola sekin
boshlab, sezdirmasdan imtihon tezligiga chiqadi. Tezlik
serverdan keladi, mijoz o'zi o'ylab topmaydi.

SAQLANISHI. PracticeItem jadvali, skill="ielts_listening".
payload: {say, step, rate, hint}; answer — kutilgan matn.
Tekshiruv serverda, bo'sh joy/defis/registr e'tiborsiz.
"""

# ---- 1-MASHQ: SPELLING NAMES ------------------------------------
# (matn, step) — step 1..5 qiyinlik
SPELL = [
    # step 1 — qisqa, tanish shaharlar
    ("YORK", 1), ("BATH", 1), ("HULL", 1), ("DEAL", 1),
    ("ELY", 1), ("RYE", 1), ("WARE", 1), ("DISS", 1),
    ("LEEDS", 1), ("DERBY", 1),
    # step 2 — o'rtacha shaharlar
    ("BOLTON", 2), ("EXETER", 2), ("NORWICH", 2), ("IPSWICH", 2),
    ("DUNDEE", 2), ("NEWPORT", 2), ("SWANSEA", 2), ("CARDIFF", 2),
    ("BRISTOL", 2), ("OXFORD", 2),
    # step 3 — ko'cha nomlari
    ("HIGH STREET", 3), ("BAKER STREET", 3), ("QUEENS ROAD", 3),
    ("MILL LANE", 3), ("CHURCH ROAD", 3), ("PARK AVENUE", 3),
    ("VICTORIA ROAD", 3), ("STATION ROAD", 3),
    ("KINGS CRESCENT", 3), ("ALBERT DRIVE", 3),
    # step 4 — britaniyacha familiyalar (qiyin yozilishi)
    ("SMITH", 4), ("BROWN", 4), ("TAYLOR", 4), ("WILSON", 4),
    ("THOMPSON", 4), ("HUGHES", 4), ("MORGAN", 4), ("KNIGHT", 4),
    ("WRIGHT", 4), ("GRAHAM", 4), ("MURPHY", 4), ("O'BRIEN", 4),
    ("MACLEOD", 4), ("FLETCHER", 4), ("HARGREAVES", 4),
    # step 5 — eng qiyin: uzun va aldamchi
    ("WORCESTER", 5), ("GLOUCESTER", 5), ("LEICESTER", 5),
    ("EDINBURGH", 5), ("PETERBOROUGH", 5), ("LOUGHBOROUGH", 5),
    ("KIRKCALDY", 5), ("BEACONSFIELD", 5), ("FEATHERSTONE", 5),
    ("WYTHENSHAWE", 5), ("CHOLMONDELEY", 5), ("BEAULIEU", 5),
]

# ---- 2-MASHQ: NUMBER PRACTICE -----------------------------------
# (aytiladigan raqam, tur, step)
NUMBER = [
    # step 1 — qisqa sonlar
    ("14", "son", 1), ("40", "son", 1), ("13", "son", 1),
    ("30", "son", 1), ("17", "son", 1), ("70", "son", 1),
    ("19", "son", 1), ("90", "son", 1), ("15", "son", 1),
    ("50", "son", 1),
    # step 2 — 3-4 xonali
    ("245", "son", 2), ("806", "son", 2), ("1990", "yil", 2),
    ("2014", "yil", 2), ("3500", "son", 2), ("7250", "son", 2),
    ("1066", "yil", 2), ("1815", "yil", 2), ("4080", "son", 2),
    ("6015", "son", 2),
    # step 3 — narx va o'lchov
    ("19.99", "narx", 3), ("249.50", "narx", 3),
    ("7.45", "narx", 3), ("130.75", "narx", 3),
    ("2.5", "son", 3), ("12.8", "son", 3),
    ("85.20", "narx", 3), ("999.99", "narx", 3),
    ("0.75", "son", 3), ("64.30", "narx", 3),
    # step 4 — telefon raqamlar
    ("07700 900123", "telefon", 4), ("0161 496 0345", "telefon", 4),
    ("020 7946 0812", "telefon", 4), ("0113 496 0221", "telefon", 4),
    ("07911 123456", "telefon", 4), ("0141 496 0709", "telefon", 4),
    ("01865 240 517", "telefon", 4), ("029 2018 0934", "telefon", 4),
    ("07543 887 210", "telefon", 4), ("0191 498 0166", "telefon", 4),
    # step 5 — karta va hisob raqamlari
    ("4532 8891 0276 3345", "karta", 5),
    ("5412 7700 6621 9083", "karta", 5),
    ("4024 0071 5590 1284", "karta", 5),
    ("6011 3390 8874 2201", "karta", 5),
    ("3782 822463 10005", "karta", 5),
    ("60-16-13 31926819", "hisob", 5),
    ("20-45-45 40118293", "hisob", 5),
    ("09-01-28 55779923", "hisob", 5),
    ("40-47-84 66203417", "hisob", 5),
    ("77-22-19 80345561", "hisob", 5),
    ("1 800 555 0199", "telefon", 5),
    ("+44 7911 654321", "telefon", 5),
]

# ---- 3-MASHQ: SPELLING MIXED (postcode va kodlar) ---------------
MIXED = [
    # step 1 — qisqa postcodelar
    ("M1 1AE", 1), ("B1 1HQ", 1), ("L1 8JQ", 1), ("S1 2HE", 1),
    ("G1 1XW", 1), ("W1 3PA", 1), ("E1 6AN", 1), ("N1 9GU", 1),
    ("Y1 4RT", 1), ("D1 2KL", 1),
    # step 2 — standart postcodelar
    ("SW1A 2AA", 2), ("EC1V 9HX", 2), ("NW3 5QT", 2),
    ("SE10 8XJ", 2), ("CV34 6RG", 2), ("BS8 1TH", 2),
    ("LS29 8JZ", 2), ("OX14 3DB", 2), ("PE28 9AF", 2),
    ("TN23 6LN", 2),
    # step 3 — qiyinroq postcodelar
    ("EH12 5EZ", 3), ("AB25 1XS", 3), ("IV63 6TU", 3),
    ("KY16 9AJ", 3), ("PH33 6EJ", 3), ("HD9 7XW", 3),
    ("WF17 6QB", 3), ("DN22 0AD", 3), ("TR11 4RH", 3),
    ("ZE1 0PW", 3),
    # step 4 — buyurtma va bron kodlari
    ("BK7734Z", 4), ("RX90188Q", 4), ("TQ4471MB", 4),
    ("JX2205LP", 4), ("VN8830CR", 4), ("HY6612KD", 4),
    ("QZ0457WF", 4), ("LM7729TG", 4), ("DP3364XN", 4),
    ("CS9081RV", 4),
    # step 5 — uzun aralash kodlar
    ("GB29 NWBK 6016 1331 9268 19", 5),
    ("AB12 3CD4 5EF6 7890", 5),
    ("XK-4471-QP-2208", 5),
    ("MN7/2245/BX", 5),
    ("ZQ88-1174-KLM-30", 5),
    ("PL2019 TY44 88Z", 5),
    ("RJ4488 WQ12 07", 5),
    ("TT-9021-VBX-556", 5),
    ("NC1174 JJ90 22K", 5),
    ("SW1A 1AA / EC2R 8AH", 5),
]

SKILL = "ielts_listening"
# Tezlik step bo'yicha — sekindan imtihon tezligigacha
RATE_BY_STEP = {1: 0.55, 2: 0.65, 3: 0.75, 4: 0.88, 5: 1.0}

_NUM_HINT = {
    "son": "Oddiy son",
    "yil": "Yil",
    "narx": "Narx (funt sterling)",
    "telefon": "Telefon raqami",
    "karta": "Bank kartasi raqami",
    "hisob": "Sort code va hisob raqami",
}


def _say_letters(text: str) -> str:
    """Harflab aytish uchun: 'YORK' -> 'Y, O, R, K'.

    Nuqta-vergul bilan ajratamiz — ovoz sintezatori har harfni
    ALOHIDA o'qiydi, aks holda so'z bo'lib ketadi. Bo'sh joy
    'space' deb aytiladi (IELTS'da aynan shunday eshitiladi),
    apostrof esa 'apostrophe'.
    """
    out = []
    for ch in text:
        if ch == " ":
            out.append("space")
        elif ch == "'":
            out.append("apostrophe")
        elif ch == "-":
            out.append("dash")
        elif ch == "/":
            out.append("slash")
        else:
            out.append(ch)
    return ", ".join(out)


def _say_digits(text: str) -> str:
    """Raqamlarni bittalab: '245' -> '2, 4, 5'. Nuqta 'point',
    bo'sh joy kichik pauza. IELTS'da raqamlar aynan shunday
    diktovka qilinadi."""
    out = []
    for ch in text:
        if ch == " ":
            out.append("...")
        elif ch == ".":
            out.append("point")
        elif ch == "-":
            out.append("dash")
        elif ch == "+":
            out.append("plus")
        else:
            out.append(ch)
    return ", ".join(out)


def build_rows():
    """(kind, level, payload, answer, explain) ro'yxati."""
    rows = []

    for i, (text, step) in enumerate(SPELL):
        rows.append((
            "ielts_spell", f"S{step}",
            {"say": _say_letters(text), "step": step,
             "rate": RATE_BY_STEP[step], "order": i,
             "hint": "Ism / shahar / ko'cha nomi"},
            text,
            "Harflab aytiladi. Bo'sh joy — 'space', apostrof — "
            "'apostrophe' deb eshitiladi."))

    for i, (text, kind, step) in enumerate(NUMBER):
        rows.append((
            "ielts_number", f"N{step}",
            {"say": _say_digits(text), "step": step,
             "rate": RATE_BY_STEP[step], "order": i,
             "hint": _NUM_HINT.get(kind, "Raqam")},
            text,
            "Raqamlar bittalab aytiladi. Nuqta — 'point'. "
            "IELTS'da 0 ko'pincha 'oh' deb o'qiladi."))

    for i, (text, step) in enumerate(MIXED):
        rows.append((
            "ielts_mixed", f"M{step}",
            {"say": _say_letters(text), "step": step,
             "rate": RATE_BY_STEP[step], "order": i,
             "hint": "Postcode yoki kod (harf + raqam)"},
            text,
            "Postcodeda harf va raqam aralash keladi. Bo'sh joyni "
            "ham qo'yib yozing — tekshiruvda muhim emas, lekin "
            "imtihonda toza yozgan yaxshi."))

    return rows


def seed_ielts(db):
    """Idempotent: (skill, kind, answer) bo'yicha yo'qlari qo'shiladi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_listen_v1"):
        return None
    import json
    import models

    have = {(k, a) for (k, a) in
            db.query(models.PracticeItem.kind, models.PracticeItem.answer)
            .filter(models.PracticeItem.skill == SKILL).all()}
    made = 0
    for kind, level, payload, answer, explain in build_rows():
        if (kind, answer) in have:
            continue
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, explain=explain))
        have.add((kind, answer))
        made += 1
    if made:
        db.commit()
    _seed_mark(db, "ielts_listen_v1")
    return made
