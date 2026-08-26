# -*- coding: utf-8 -*-
"""MULTILEVEL SPEAKING — FORMAT VA BAHOLASH (2026-08-26).

Jahongir: "Multilevel Speakingni ham yangi formati va savollardan
namunalar tashlab qo'ydim, buni ham shunday joylashtirginki
multilevelga tayyorlashi uchun eng zor platforma bo'lsin va
Multilevel Free Mock olsayam bo'lsin bahosini chiqarib bersin
masalan speaking 0-75 ballgacha 65-75 C1 ga teng 51-64 bu B2ga
teng 30-50 B1 ga teng qolgani A1-A2 darajada."

MANBA. Ikkala hujjat ham foydalanuvchi yuborgan rasmiy fayllardan:
  speaking_format.pdf   — qismlar, savollar soni, vaqt taqsimoti
  yangi_format_eng.pdf  — RATING SCALE (baholash mezonlari)

=================================================================
 IMTIHON TUZILMASI (speaking_format.pdf, 1-bet)
=================================================================
  Qism  Daraja  Savol  Javob vaqti          Tayyorgarlik
  1.1   A1-A2     3    30 soniya (har biri)     yo'q
  1.2   B1        3    4-savol 45 s;            yo'q
                       5-6-savol 30 s
  2     B2        3    2 daqiqa (uchalasi)      1 daqiqa
  3     C1        1    2 daqiqa                 1 daqiqa

=================================================================
 BALL (yangi_format_eng.pdf)
=================================================================
Rasmiy shkala savollarni TO'RT BLOKKA bo'lib baholaydi:
  Q1-3  -> 0-5   (5 = A2 dan yuqori, 4 = Higher A2, ...)
  Q4-6  -> 0-5   (5 = B1 dan yuqori, 4 = Higher B1, ...)
  Q7    -> 0-5   (5 = B2 dan yuqori, 4 = Higher B2, ...)
  Q8    -> 0-6   (6 = C1 dan yuqori, 5 = C1, 4 = Higher B2, ...)
Xom ball eng ko'pi: 5 + 5 + 5 + 6 = 21.

Jahongir 0-75 shkalasini so'radi. Shuning uchun xom ball chiziqli
ravishda 75 ga keltiriladi: ball = round(xom / 21 * 75).

TEKSHIRUV — bu almashtirish Jahongir bergan chegaralarga tabiiy
tushadimi?
  21 -> 75  C1     (hamma blok maksimal)
  19 -> 68  C1     (5+5+5+4)
  18 -> 64  B2     (chegara aynan shu yerda)
  16 -> 57  B2     (4+4+4+4 — barqaror B2)
  14 -> 50  B1     (chegara)
  11 -> 39  B1     (3+3+3+2)
   8 -> 29  A2
Ya'ni C1 olish uchun deyarli hamma blokda eng yuqori baho kerak —
haqiqiy imtihondagidek. Chegaralar sun'iy emas.
"""

# =================================================================
#  QISMLAR
# =================================================================

PARTS: list[dict] = [
    {
        "key": "p11",
        "part": "1.1",
        "level": "A1-A2",
        "title": "Shaxsiy savollar",
        "focus": "Shaxsiy ma'lumot almashish",
        "questions": 3,
        "seconds": [30, 30, 30],
        "prep": 0,
        "block": "q1_3",
        "intro": "Part one. In this part, I'm going to ask you three "
                 "short questions about yourself and your interests. "
                 "You will have 30 seconds to reply to each question. "
                 "Begin speaking when you hear this sound.",
        "uz": "Tanish mavzuda (uy, oila, do'stlar, qiziqishlar) uchta "
              "savol ketma-ket beriladi. Har biriga 30 soniya. "
              "Tayyorgarlik vaqti YO'Q.",
    },
    {
        "key": "p12",
        "part": "1.2",
        "level": "B1",
        "title": "Ikki rasmni taqqoslash",
        "focus": "Tasvirlash, fikr bildirish va asoslash",
        "questions": 3,
        "seconds": [45, 30, 30],
        "prep": 0,
        "block": "q4_6",
        "intro": "Now, I'm going to ask you to compare two pictures "
                 "and I will ask you two questions about them.",
        "uz": "Bir mavzuga oid ikkita rasm ko'rsatiladi. 4-savol — "
              "rasmlarni taqqoslash (45 soniya), 5 va 6-savollar — "
              "fikr va sabab (30 soniyadan). Tayyorgarlik YO'Q.",
    },
    {
        "key": "p2",
        "part": "2",
        "level": "B2",
        "title": "Rasm va uchta savol",
        "focus": "Abstrakt mavzuda fikr yuritish, afzallik va "
                 "kamchiliklarni tahlil qilish",
        "questions": 3,
        "seconds": [120],
        "prep": 60,
        "block": "q7",
        "intro": "Part two. In this part, I'm going to show you a "
                 "picture and ask you three questions. You will have "
                 "one minute to think about your answers before you "
                 "start speaking. You will have two minutes to answer "
                 "all three questions.",
        "uz": "Rasm va uchta savol BIRDANIGA beriladi. 1 daqiqa "
              "o'ylash, keyin 2 daqiqada UCHALA savolga javob. "
              "Rasmni tasvirlab berish TALAB QILINMAYDI — u faqat "
              "mavzuni bildiradi.",
    },
    {
        "key": "p3",
        "part": "3",
        "level": "C1",
        "title": "Tarafdor va qarshi dalillar",
        "focus": "Argumentning har ikki tomonini tahlil qilish",
        "questions": 1,
        "seconds": [120],
        "prep": 60,
        "block": "q8",
        "intro": "Part three. In this part, you are going to speak on "
                 "a topic for two minutes. You can see the topic on "
                 "the screen and two lists of points - for and against. "
                 "Choose two items from each list and give a balanced "
                 "argument to represent both sides of the topic.",
        "uz": "Mavzu va ikki ro'yxat (FOR / AGAINST) beriladi. Har "
              "ro'yxatdan IKKITADAN band tanlab, muvozanatli dalil "
              "quriladi. 1 daqiqa tayyorgarlik, 2 daqiqa nutq.",
    },
]

PART_BY_KEY = {p["key"]: p for p in PARTS}

# =================================================================
#  BAHOLASH MEZONLARI (yangi_format_eng.pdf dan qisqartirilgan)
#  Har blokda: ball -> (daraja yorlig'i, o'zbekcha izoh)
# =================================================================

BANDS: dict[str, dict] = {
    "q1_3": {
        "max": 5,
        "title": "1-3 savollar (Part 1.1)",
        "scale": {
            5: ("A2 dan yuqori",
                "Uchala javob ham mavzuda va A2 darajadan baland."),
            4: ("Higher A2",
                "Uchala javob mavzuda. Oddiy grammatika to'g'ri "
                "ishlatiladi, lekin asosiy xatolar tizimli takrorlanadi. "
                "Lug'at yetarli, lekin noo'rin so'z tanlash seziladi."),
            3: ("Lower A2",
                "Ikki javob mavzuda. Qolgan belgilar Higher A2 bilan "
                "bir xil."),
            2: ("Higher A1",
                "Kamida ikki javob mavzuda, lekin grammatika so'z va "
                "iboralar darajasida; talaffuz asosan tushunarsiz."),
            1: ("Lower A1",
                "Faqat bitta javob mavzuda."),
            0: ("Ball yo'q",
                "Mazmunli nutq yo'q yoki javoblar mavzudan tashqari "
                "(yodlangan matn, taxmin)."),
        },
    },
    "q4_6": {
        "max": 5,
        "title": "4-6 savollar (Part 1.2)",
        "scale": {
            5: ("B1 dan yuqori",
                "Uchala javob ham mavzuda va B1 darajadan baland."),
            4: ("Higher B1",
                "Uchala javob mavzuda. Oddiy tuzilmalar to'g'ri; xato "
                "murakkab tuzilmaga urinilganda chiqadi. Bog'lovchilar "
                "sodda."),
            3: ("Lower B1", "Ikki javob mavzuda."),
            2: ("Higher A2",
                "Kamida ikki javob mavzuda, lekin fikrlar ro'yxatga "
                "o'xshaydi, bog'lanish kuchsiz."),
            1: ("Lower A2", "Faqat bitta javob mavzuda."),
            0: ("Ball yo'q", "A2 dan past yoki mazmunli nutq yo'q."),
        },
    },
    "q7": {
        "max": 5,
        "title": "7-savol (Part 2)",
        "scale": {
            5: ("B2 dan yuqori",
                "Uchala savolga ham mavzuda javob berilgan va B2 dan "
                "baland."),
            4: ("Higher B2",
                "Ba'zi murakkab konstruksiyalar aniq ishlatilgan. "
                "Lug'at mavzuni muhokama qilishga yetarli. Talaffuz "
                "tushunarli."),
            3: ("Lower B2", "Ikki savolga javob berilgan."),
            2: ("Higher B1",
                "Kamida ikki savol yoritilgan, lekin lug'at cheklovi "
                "vazifani to'liq bajarishga xalaqit beradi."),
            1: ("Lower B1", "Faqat bitta savolga javob berilgan."),
            0: ("Ball yo'q", "B1 dan past yoki mazmunli nutq yo'q."),
        },
    },
    "q8": {
        "max": 6,
        "title": "8-savol (Part 3)",
        "scale": {
            6: ("C1 dan yuqori", "C1 darajadan baland nutq."),
            5: ("C1",
                "Nutq aniq, har ikki ro'yxatdan bandlar yoritilgan. "
                "Tarafdor va qarshi dalillar asoslangan. Murakkab "
                "grammatika xilma-xil va aniq. Bog'lovchilar boy."),
            4: ("Higher B2",
                "Har ikki ro'yxatdagi bandlar yoritilgan; ba'zi "
                "murakkab konstruksiyalar aniq."),
            3: ("Lower B2",
                "Faqat BITTA ro'yxatdagi bandlar yoritilgan — ya'ni "
                "muvozanat yo'q."),
            2: ("Higher B1",
                "Yaxlit nutq qura olmaydi, ekrandagi bandlarga qattiq "
                "bog'lanib qoladi."),
            1: ("Lower B1",
                "Ekrandagi bandlarni to'g'ridan-to'g'ri o'qiydi."),
            0: ("Ball yo'q", "Mazmunli nutq yo'q."),
        },
    },
}

RAW_MAX = sum(b["max"] for b in BANDS.values())      # 21
SCALE_MAX = 75

# Jahongir bergan chegaralar (0-75)
LEVELS = [
    (65, 75, "C1", "Mustaqil, murakkab mavzuda erkin gapiradi."),
    (51, 64, "B2", "Abstrakt mavzuda dalil keltira oladi."),
    (30, 50, "B1", "Tanish mavzuda bog'langan nutq qura oladi."),
    (15, 29, "A2", "Oddiy, kundalik mavzularda gapiradi."),
    (0, 14, "A1", "Alohida so'z va qisqa iboralar darajasida."),
]


def to_scale(raw: float) -> int:
    """Xom ballni (0-21) 0-75 shkalasiga keltiradi."""
    raw = max(0.0, min(float(raw), float(RAW_MAX)))
    return int(round(raw / RAW_MAX * SCALE_MAX))


def level_of(score: int) -> tuple[str, str]:
    """0-75 balldan CEFR darajasini beradi."""
    for lo, hi, name, desc in LEVELS:
        if lo <= score <= hi:
            return name, desc
    return "A1", LEVELS[-1][3]


def next_level_gap(score: int) -> tuple[str, int]:
    """Keyingi darajagacha necha ball qolgani.

    O'quvchiga "yana 6 ball to'plasangiz B2 bo'lasiz" deyish —
    quruq bahodan ancha foydali.
    """
    for lo, _hi, name, _d in reversed(LEVELS):
        if score < lo:
            return name, lo - score
    return "", 0


def band_label(block: str, point: int) -> tuple[str, str]:
    b = BANDS[block]["scale"]
    p = max(0, min(int(point), BANDS[block]["max"]))
    return b[p]


def build_result(points: dict) -> dict:
    """Blok ballaridan to'liq natija.

    points = {"q1_3": 4, "q4_6": 3, "q7": 3, "q8": 4}
    """
    rows = []
    raw = 0.0
    for block, meta in BANDS.items():
        p = max(0, min(int(points.get(block, 0)), meta["max"]))
        raw += p
        lab, why = band_label(block, p)
        rows.append({"block": block, "title": meta["title"],
                     "point": p, "max": meta["max"],
                     "label": lab, "why": why})
    score = to_scale(raw)
    name, desc = level_of(score)
    nx, gap = next_level_gap(score)
    return {"raw": int(raw), "raw_max": RAW_MAX, "score": score,
            "score_max": SCALE_MAX, "level": name, "level_desc": desc,
            "next_level": nx, "next_gap": gap, "blocks": rows}
