# -*- coding: utf-8 -*-
"""IELTS LISTENING — 4-BLOK: UCH TUZOQ (2026-08-25).

Jahongir aytgan uchta qopqon, nomlari o'zi bergan atamalar bilan:

  DELAYED RESPONSE TRAP — javob kechiktiriladi.
    "Javobni kechiktiradi va siz javobni o'tkizvordimmikan deb
    xavotirlanishni boshlaysiz shunda javobni aytib ketganda
    yozolmay qolish mumkin."
    Misol (rasmdan): "site workers, visitors or city ___" —
    suhbat uzoq ketadi, javob (administrators) eng oxirida keladi.

  MODIFICATION TRAP — aytilgan javob keyin to'g'rilanadi.
    "bitta javobni aytadi variantlardan yoki javob bolishi mumkin
    narsani lekin keyinchalik uni tog'rlab ketadi."
    Misol (rasmdan): "From a friend? Or did you see an advert?" —
    "No, I read about you in the newspaper."
    Ikki ko'rinishi: (a) SO'ROVCHI noto'g'ri variant taklif qiladi,
    javob beruvchi rad etib to'g'risini aytadi; (b) gapiruvchi
    O'ZI aytib, keyin o'zini tuzatadi ("sorry, I mean...").

  DISTRACTOR TRAP — chalg'ituvchi gap. Ikki turi:
    (1) Contrast/Concession — although / but / however / though:
        "Although Monday is possible, Tuesday would be much better."
        Chalg'ituvchi: Monday. To'g'ri: Tuesday.
    (2) Negation — I don't think / isn't / wouldn't / unlikely /
        not really / hardly:
        "I don't think the meeting is on Friday. It's on Monday."
        O'quvchi inkorni eshitmay Friday deb yozadi.

HAR UCHALASIDA javob YOZILADI (variant tanlanmaydi) — chunki
imtihonda ham bu turlar ko'pincha gap to'ldirish (form/note
completion) bo'lib keladi.

QIYINLIK 1..5: pastda chalg'ituvchi bitta va yaqin turadi;
yuqorida ikkita chalg'ituvchi, uzunroq chalg'itish va inkor bilan
qarama-qarshilik BIRGA keladi.
"""

SKILL = "ielts_listening"
RATE_BY_STEP = {1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0}

# =====================================================================
#  UMUMIY MA'LUMOT POOLLARI
# =====================================================================
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday"]
TIMES = ["9.30", "10.15", "11.45", "1.20", "2.30", "3.15", "4.45",
         "5.30", "6.20", "7.10"]
PEOPLE = ["administrators", "volunteers", "engineers", "researchers",
          "suppliers", "neighbours", "graduates", "technicians",
          "inspectors", "organisers"]
PLACES = ["library", "warehouse", "harbour", "chapel", "greenhouse",
          "workshop", "stadium", "clinic", "quarry", "observatory"]
THINGS = ["helmet", "torch", "notebook", "compass", "blanket",
          "whistle", "passport", "receipt", "badge", "umbrella"]
SOURCES = ["newspaper", "radio", "poster", "website", "leaflet",
           "magazine", "newsletter", "noticeboard", "podcast",
           "billboard"]


def _rot(lst, n):
    return lst[n % len(lst):] + lst[:n % len(lst)]


# =====================================================================
#  1) DELAYED RESPONSE TRAP
#     Javob OXIRIDA keladi; oldin uzoq chalg'itish ketadi.
# =====================================================================
def _delayed_rows():
    rows = []

    def add(step, say, prompt, answer, hint):
        rows.append((step, say, prompt, answer, hint))

    # --- step 1-2: qisqa chalg'itish (40 ta) ---
    for i, ans in enumerate(PEOPLE):
        d1, d2 = _rot(PEOPLE, i + 3)[0], _rot(PEOPLE, i + 6)[0]
        add(1,
            f"A: So who should we interview — the {d1}, or perhaps "
            f"the {d2}? "
            f"B: Both of those did cross my mind, yes. "
            f"Hmm. Let me think about it properly. "
            f"The group we really need to speak to is the {ans}.",
            "Who do they finally decide to interview?", ans,
            "Javob eng OXIRIDA aytiladi — oldingilari shunchaki "
            "o'ylangan variantlar")
    for i, ans in enumerate(PLACES):
        d1, d2 = _rot(PLACES, i + 4)[0], _rot(PLACES, i + 7)[0]
        add(1,
            f"A: Where shall we hold it — in the {d1}? Or the {d2}? "
            f"B: Possibly. I'd have to check both. "
            f"Actually, now I think about it, we have already booked "
            f"the {ans}.",
            "Where will it be held?", ans,
            "Oxirgi jumlaga qadar kuting")
    for i, ans in enumerate(THINGS):
        d1, d2 = _rot(THINGS, i + 2)[0], _rot(THINGS, i + 5)[0]
        add(2,
            f"A: What do I need to bring — a {d1}? A {d2}? "
            f"B: You won't need either of those, they're provided. "
            f"There's a list somewhere... where did I put it... "
            f"right, here it is. The one thing to bring is a {ans}.",
            "What must you bring?", ans,
            "Ro'yxat izlanadi, javob shundan keyin keladi")
    for i, ans in enumerate(SOURCES):
        d1, d2 = _rot(SOURCES, i + 3)[0], _rot(SOURCES, i + 8)[0]
        add(2,
            f"A: How did you hear about us — from the {d1}? Or maybe "
            f"the {d2}? "
            f"B: Neither, actually. I'd have to think back. "
            f"It was a while ago now. It was the {ans}, I'm sure of "
            f"it.",
            "How did they hear about the company?", ans,
            "Ikkala taklif ham rad etiladi, javob keyin keladi")

    # --- step 3-4: uzunroq chalg'itish (40 ta) ---
    for i, ans in enumerate(DAYS + DAYS[:3]):
        d1 = _rot(DAYS, i + 2 + (i // 7))[0]
        d2 = _rot(DAYS, i + 4 + (i // 7) * 2)[0]
        add(3,
            f"A: Which day works for the visit — {d1}? "
            f"B: {d1}... I think there's something else on. "
            f"A: What about {d2}, then? "
            f"B: Let me look at the calendar. Hold on. There's a "
            f"delivery that morning, and the manager is away. "
            f"So the only day that really works is {ans}.",
            "Which day is finally agreed?", ans,
            "Ikki kun muhokama qilinib rad etiladi")
    for i, ans in enumerate(TIMES):
        d1 = _rot(TIMES, i + 3)[0]
        add(3,
            f"A: Shall we say {d1}? "
            f"B: Mmm. That's when the group from the college arrives, "
            f"so the room would be busy. And the caretaker locks up "
            f"over lunch. Let's make it {ans} instead.",
            "What time do they agree on?", ans,
            "Birinchi taklif band, javob keyin")
    for i, ans in enumerate(PLACES):
        d1 = _rot(PLACES, i + 5)[0]
        add(4,
            f"A: I've put the meeting in the {d1} — is that right? "
            f"B: You'd think so, wouldn't you. That's where it used "
            f"to be. And the sign on the door still says so, which "
            f"confuses everybody. But since the refurbishment it has "
            f"been in the {ans}.",
            "Where does the meeting take place now?", ans,
            "Eski joy uzoq muhokama qilinadi, javob oxirida")
    for i, ans in enumerate(PEOPLE):
        d1 = _rot(PEOPLE, i + 4)[0]
        add(4,
            f"A: Who signs the form — the {d1}? "
            f"B: That's the usual assumption, and honestly it would "
            f"make more sense. But the rules were rewritten last "
            f"year and now it has to go to the {ans}.",
            "Who signs the form?", ans,
            "Mantiqiy ko'ringan variant rad etiladi")

    # --- step 5: eng uzun, ikki chalg'ituvchi (20 ta) ---
    for i, ans in enumerate(THINGS):
        d1 = _rot(THINGS, i + 3)[0]
        d2 = _rot(THINGS, i + 6)[0]
        add(5,
            f"A: The kit list mentions a {d1} and a {d2}, doesn't it? "
            f"B: It does, but that list is three years old. The {d1} "
            f"is supplied on site now, and nobody has used a {d2} "
            f"since the route changed. Sorry, I'm going on a bit. "
            f"The item you actually have to bring yourself is a "
            f"{ans}.",
            "What must you bring yourself?", ans,
            "Ikki chalg'ituvchi uzoq muhokama qilinadi")
    for i, ans in enumerate(SOURCES):
        d1 = _rot(SOURCES, i + 2)[0]
        d2 = _rot(SOURCES, i + 7)[0]
        add(5,
            f"A: Most of our enquiries come from the {d1}, and a few "
            f"from the {d2}. "
            f"B: That was true last year, certainly. The {d1} "
            f"campaign finished in March, though, and the {d2} was "
            f"never very effective. This year almost everyone found "
            f"us through the {ans}.",
            "Where do most enquiries come from THIS year?", ans,
            "Eski ma'lumot uzoq aytiladi, yangisi oxirida")
    return rows


# =====================================================================
#  2) MODIFICATION TRAP
#     Aytilgan javob keyin TO'G'RILANADI.
# =====================================================================
def _modification_rows():
    rows = []

    def add(step, say, prompt, answer, hint):
        rows.append((step, say, prompt, answer, hint))

    # (a) So'rovchi noto'g'ri variant taklif qiladi (40 ta)
    for i, ans in enumerate(SOURCES):
        d1, d2 = _rot(SOURCES, i + 4)[0], _rot(SOURCES, i + 6)[0]
        add(1,
            f"A: Can I ask where you heard about us? From the {d1}? "
            f"Or perhaps the {d2}? "
            f"B: No, I read about you in the {ans}.",
            "How did they hear about the company?", ans,
            "So'rovchining ikki taklifi ham NOTO'G'RI")
    for i, ans in enumerate(DAYS + DAYS[:3]):
        d1 = _rot(DAYS, i + 3 + (i // 7) * 2)[0]
        add(1,
            f"A: So you'll come on {d1}? "
            f"B: Not {d1}, no — {ans} suits me better.",
            "Which day will they come?", ans,
            "Taklif rad etiladi")
    for i, ans in enumerate(PLACES):
        d1 = _rot(PLACES, i + 2)[0]
        add(2,
            f"A: We'll meet at the {d1}, then? "
            f"B: Actually, could we make it the {ans}? The {d1} is "
            f"being used for something else.",
            "Where will they meet?", ans, "Joy o'zgartiriladi")
    for i, ans in enumerate(TIMES):
        d1 = _rot(TIMES, i + 5)[0]
        add(2,
            f"A: Is {d1} all right for you? "
            f"B: Could we say {ans}? I finish work later than I used "
            f"to.",
            "What time do they agree on?", ans,
            "Vaqt o'zgartiriladi")

    # (b) Gapiruvchi O'ZINI tuzatadi (40 ta)
    for i, ans in enumerate(PEOPLE):
        d1 = _rot(PEOPLE, i + 5)[0]
        add(3,
            f"The form goes to the {d1} — sorry, I mean the {ans}. "
            f"The {d1} deal with something completely different.",
            "Who does the form go to?", ans,
            "Gapiruvchi o'zini tuzatadi: 'sorry, I mean'")
    for i, ans in enumerate(THINGS):
        d1 = _rot(THINGS, i + 4)[0]
        add(3,
            f"Don't forget your {d1}. Oh — no, that was the winter "
            f"trip. For this one you need your {ans}.",
            "What do you need for this trip?", ans,
            "Birinchi aytilgani boshqa safarga tegishli")
    for i, ans in enumerate(TIMES):
        d1 = _rot(TIMES, i + 2)[0]
        add(4,
            f"The coach leaves at {d1}. Hang on, that's the return "
            f"time. Going out, it leaves at {ans}.",
            "What time does the coach leave on the way OUT?", ans,
            "Birinchi vaqt QAYTISH vaqti edi")
    for i, ans in enumerate(PLACES):
        d1 = _rot(PLACES, i + 6)[0]
        add(4,
            f"Registration is at the {d1}. Sorry, I've said that "
            f"wrong — the {d1} is where you collect your badge "
            f"afterwards. Registration itself is at the {ans}.",
            "Where does registration take place?", ans,
            "Birinchi joy boshqa maqsad uchun")

    # (c) Ikki marta o'zgaradi — eng qiyin (20 ta)
    for i, ans in enumerate(DAYS + DAYS[:3]):
        d1 = _rot(DAYS, i + 1 + (i // 7))[0]
        d2 = _rot(DAYS, i + 5 + (i // 7) * 2)[0]
        add(5,
            f"Let's meet on {d1}. Actually, {d2} would be better — "
            f"no, wait, {d2} is the holiday. {ans}, then. Let's fix "
            f"{ans}.",
            "Which day is finally fixed?", ans,
            "Ikki marta o'zgaradi — OXIRGISI to'g'ri")
    for i, ans in enumerate(TIMES[:10]):
        d1 = _rot(TIMES, i + 3)[0]
        d2 = _rot(TIMES, i + 7)[0]
        add(5,
            f"We open at {d1} — well, {d2} on this day of the week. "
            f"Although in the school holidays, which is now, it is "
            f"{ans}.",
            "What time does it open NOW?", ans,
            "Uch vaqt aytiladi, oxirgisi hozirgi holat")
    return rows


# =====================================================================
#  3) DISTRACTOR TRAP
#     (1) Contrast/Concession   (2) Negation
# =====================================================================
def _distractor_rows():
    rows = []

    def add(step, say, prompt, answer, hint, sub):
        rows.append((step, say, prompt, answer, hint, sub))

    C_HINT = ("Qarama-qarshilik: although / but / however — "
              "birinchi aytilgani CHALG'ITUVCHI")
    N_HINT = ("Inkor: don't / isn't / wouldn't / unlikely — "
              "eshitgan so'zingiz INKOR qilingan bo'lishi mumkin")

    # --- Contrast / Concession (50 ta) ---
    for i, ans in enumerate(DAYS + DAYS[:3]):
        d1 = _rot(DAYS, i + 2 + (i // 7) * 3)[0]
        add(1, f"Although {d1} is possible, {ans} would be much "
            f"better.", "Which day is better?", ans, C_HINT,
            "contrast")
    for i, ans in enumerate(TIMES):
        d1 = _rot(TIMES, i + 4)[0]
        add(2, f"We could start at {d1}, but {ans} would suit "
            f"everyone more.", "What time do they prefer?", ans,
            C_HINT, "contrast")
    for i, ans in enumerate(PLACES):
        d1 = _rot(PLACES, i + 3)[0]
        add(3, f"The {d1} is closer, however the {ans} has much "
            f"better facilities, so we'll use that.",
            "Which place will they use?", ans, C_HINT, "contrast")
    for i, ans in enumerate(THINGS):
        d1 = _rot(THINGS, i + 5)[0]
        add(4, f"Even though a {d1} is on the list, what you really "
            f"need is a {ans} — that's the one thing people forget.",
            "What do you really need?", ans, C_HINT, "contrast")
    for i, ans in enumerate(PEOPLE):
        d1 = _rot(PEOPLE, i + 6)[0]
        add(5, f"While the {d1} were consulted at the start, and "
            f"their comments are in the report, the decision itself "
            f"rests with the {ans}.",
            "Who makes the decision?", ans, C_HINT, "contrast")

    # --- Negation (50 ta) ---
    for i, ans in enumerate(DAYS + DAYS[:3]):
        d1 = _rot(DAYS, i + 3 + (i // 7) * 2)[0]
        add(1, f"I don't think the meeting is on {d1}. It's on "
            f"{ans}.", "Which day is the meeting?", ans, N_HINT,
            "negation")
    for i, ans in enumerate(TIMES):
        d1 = _rot(TIMES, i + 2)[0]
        add(2, f"It isn't at {d1} any more — it's at {ans} now.",
            "What time is it now?", ans, N_HINT, "negation")
    for i, ans in enumerate(PLACES):
        d1 = _rot(PLACES, i + 4)[0]
        add(3, f"We wouldn't use the {d1} for that; the {ans} is far "
            f"more suitable.", "Which place is suitable?", ans,
            N_HINT, "negation")
    for i, ans in enumerate(SOURCES):
        d1 = _rot(SOURCES, i + 5)[0]
        add(4, f"It's unlikely anyone saw the {d1} — hardly anybody "
            f"reads it. Most people found us through the {ans}.",
            "How did most people find them?", ans, N_HINT,
            "negation")
    for i, ans in enumerate(PEOPLE):
        d1 = _rot(PEOPLE, i + 2)[0]
        add(5, f"Not really the {d1}, no. I wouldn't say they were "
            f"involved at all, whatever the notes suggest. The work "
            f"was done by the {ans}.",
            "Who did the work?", ans, N_HINT, "negation")
    return rows


# =====================================================================
def build_rows():
    """(kind, level, payload, answer, explain) ro'yxati."""
    out = []
    seen = set()

    def push(kind, step, say, prompt, answer, hint, explain, order):
        key = (kind, say, prompt)
        if key in seen:
            return False
        seen.add(key)
        out.append((kind, f"{kind[-1].upper()}{step}",
                    {"say": say, "prompt": prompt, "step": step,
                     "rate": RATE_BY_STEP[step], "order": order,
                     "hint": hint},
                    answer, explain))
        return True

    n = 0
    for step, say, prompt, answer, hint in _delayed_rows():
        if push("ielts_delayed", step, say, prompt, answer, hint,
                "DELAYED RESPONSE TRAP: javob suhbatning OXIRIDA "
                "keladi. Boshida aytilganlar — shunchaki o'ylangan "
                "yoki rad etilgan variantlar. Oxirigacha kutmasdan "
                "yozgan odam yiqiladi.", n):
            n += 1
    n = 0
    for step, say, prompt, answer, hint in _modification_rows():
        if push("ielts_modif", step, say, prompt, answer, hint,
                "MODIFICATION TRAP: birinchi aytilgan javob keyin "
                "TO'G'RILANADI. Har doim oxirgi tasdiqlangan "
                "qiymatni oling — 'sorry, I mean', 'actually', "
                "'no, wait' kabi so'zlar signal beradi.", n):
            n += 1
    n = 0
    for step, say, prompt, answer, hint, sub in _distractor_rows():
        expl = ("DISTRACTOR TRAP — Contrast/Concession: "
                "although / but / however / even though / while "
                "so'zidan OLDIN aytilgani chalg'ituvchi, KEYIN "
                "aytilgani to'g'ri javob."
                if sub == "contrast" else
                "DISTRACTOR TRAP — Negation: don't / isn't / "
                "wouldn't / unlikely / not really / hardly. "
                "Eshitilgan qiymat INKOR qilinyapti — uni yozmang.")
        if push("ielts_distract", step, say, prompt, answer, hint,
                expl, n):
            n += 1
    return out


def seed_ielts4(db):
    """Idempotent: (kind, say, prompt) bo'yicha yo'qlari qo'shiladi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_listen_v4"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            pl = json.loads(p)
            have.add((k, pl.get("say"), pl.get("prompt")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain in build_rows():
        key = (kind, payload.get("say"), payload.get("prompt"))
        if key in have:
            continue
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, explain=explain))
        have.add(key)
        made += 1
    if made:
        db.commit()
    _seed_mark(db, "ielts_listen_v4")
    return made
