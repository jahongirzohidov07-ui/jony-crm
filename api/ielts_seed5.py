# -*- coding: utf-8 -*-
"""IELTS LISTENING — 5-BLOK: WORD REORDER VA COMBINATION (2026-08-25).

Jahongir:

  WORD REORDER TRAP — "savolda oxirida kelgan sozlar listening
  boshida kelib qolishi yoki teskarisi bolishi mumkin yani gap
  tartibini o'zgartirish orqali sizni qopqonga tushiradigan trap".

  Rasmdagi misol:
    Savol:  "Has sports ______ and equipment on floors 1-3"
    Audio:  "The FIRST THREE FLOORS have a huge range of SPORTS
             CLOTHING as well as equipment"
  Ya'ni savolda OXIRIDA turgan "floors 1-3" audioda BOSHIDA keladi.
  Savoldagi tartibni kutib o'tirgan talaba javobni o'tkazib
  yuboradi.

  COMBINATION TRAP — "shu paytgacha bolgan barcha traplardan
  kombinatsiya bolib 2-3tasi birdan kelish xolatlari haqiqy
  testlarda kuzatiladi". Ya'ni bitta savolda ikki-uch qopqon
  birga: qarama-qarshilik + tuzatish, inkor + kechikish,
  tartib almashishi + chalg'ituvchi va hokazo. Izohda qaysi
  qopqonlar qo'shilgani sanab beriladi.

Ikkalasida ham javob YOZILADI. Qiyinlik 1..5.
"""

SKILL = "ielts_listening"
RATE_BY_STEP = {1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0}
GAP = "______"

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
        "Saturday", "Sunday"]
TIMES = ["9.30", "10.15", "11.45", "1.20", "2.30", "3.15", "4.45",
         "5.30", "6.20", "7.10"]


def _rot(lst, n):
    return lst[n % len(lst):] + lst[:n % len(lst)]


# =====================================================================
#  10) WORD REORDER TRAP
#      Savoldagi tartib va audiodagi tartib TESKARI.
# =====================================================================
def _reorder_rows():
    rows = []

    def add(step, prompt, say, answer, hint):
        rows.append((step, prompt, say, answer, hint))

    # --- 1) "X on floors N" <-> "floors N have X" (rasmdagi qolip)
    goods = [("clothing", "sports", "1-3", "first three floors"),
             ("footwear", "outdoor", "2-4", "second to fourth floors"),
             ("bedding", "home", "1-2", "first two floors"),
             ("stationery", "office", "3-5", "third to fifth floors"),
             ("cookware", "kitchen", "1-4", "lower four floors"),
             ("luggage", "travel", "2-3", "second and third floors"),
             ("furniture", "garden", "1-5", "first five floors"),
             ("lighting", "indoor", "4-6", "top three floors"),
             ("toolkits", "repair", "2-5", "middle floors"),
             ("uniforms", "school", "1-6", "whole building")]
    for i, (ans, adj, fl, fl_words) in enumerate(goods):
        add(1,
            f"Has {adj} {GAP} and equipment on floors {fl}",
            f"I was invited to a special preview, and I can promise "
            f"you this is the ultimate in retailing. The {fl_words} "
            f"have a huge range of {adj} {ans} as well as equipment, "
            f"and on the top floor there is a cafe.",
            ans,
            "Savolda OXIRIDA turgan 'floors' audioda BOSHIDA keladi")

    # --- 2) "Opens at TIME on DAY" <-> "On DAY ... opens at TIME"
    for i, ans in enumerate(TIMES):
        day = _rot(DAYS, i)[0]
        add(2,
            f"Opens at {GAP} on {day}",
            f"On {day} we work a little differently from the rest of "
            f"the week: the doors are unlocked at {ans}, an hour "
            f"later than usual.",
            ans,
            "Kun savolda oxirida, audioda esa birinchi aytiladi")

    # --- 3) "ROLE responsible for TASK" <-> "TASK handled by ROLE"
    tasks = [("caretaker", "locking the building"),
             ("secretary", "booking the rooms"),
             ("treasurer", "collecting the fees"),
             ("librarian", "ordering the books"),
             ("coordinator", "arranging the transport"),
             ("supervisor", "checking the equipment"),
             ("receptionist", "answering the phone"),
             ("technician", "setting up the sound"),
             ("registrar", "keeping the records"),
             ("steward", "guiding the visitors")]
    for i, (ans, task) in enumerate(tasks):
        add(2,
            f"{GAP} is responsible for {task}",
            f"{task.capitalize()} is looked after by the {ans} — it "
            f"has been that way since the reorganisation.",
            ans,
            "Savolda ega birinchi, audioda esa vazifa birinchi")

    # --- 4) "Bring ITEM to PLACE" <-> "At PLACE you need ITEM"
    kit = [("passport", "the front desk"), ("helmet", "the site"),
           ("receipt", "the returns counter"),
           ("badge", "the main gate"), ("torch", "the cave entrance"),
           ("boots", "the farm visit"), ("gloves", "the workshop"),
           ("towel", "the pool"), ("ticket", "the platform"),
           ("form", "the interview")]
    for i, (ans, place) in enumerate(kit):
        add(3,
            f"Bring your {GAP} to {place}",
            f"When you get to {place}, the one thing they will ask "
            f"you for is your {ans}. Everything else can be sorted "
            f"out later.",
            ans,
            "Savolda buyum birinchi, audioda joy birinchi")

    # --- 5) Passiv <-> aktiv almashinuvi
    made = [("volunteers", "the repairs"),
            ("students", "the survey"),
            ("architects", "the drawings"),
            ("neighbours", "the complaint"),
            ("council", "the decision"),
            ("committee", "the report"),
            ("farmers", "the petition"),
            ("children", "the mural"),
            ("engineers", "the inspection"),
            ("museum", "the donation")]
    for i, (ans, thing) in enumerate(made):
        add(3,
            f"{thing.capitalize()} was carried out by the {GAP}",
            f"It was the {ans}, in the end, who carried out {thing} — "
            f"nobody expected that at the start.",
            ans,
            "Passiv gap savolda, aktiv gap audioda")

    # --- 6) "COST for DURATION" <-> "For DURATION it costs COST"
    costs = [("45", "a month"), ("120", "three months"),
             ("300", "a year"), ("18", "a single session"),
             ("75", "a term"), ("9", "an hour"),
             ("240", "six months"), ("60", "a weekend"),
             ("15", "a day"), ("500", "the full course")]
    for i, (ans, dur) in enumerate(costs):
        add(4,
            f"Costs {GAP} pounds for {dur}",
            f"For {dur} — and this is the part people always get "
            f"wrong — you are looking at {ans} pounds, not the "
            f"figure printed in the old brochure.",
            ans,
            "Muddat savolda oxirida, audioda boshida")

    # --- 7) "MEET at PLACE at TIME" <-> "At TIME, at PLACE"
    for i, ans in enumerate(["gates", "car park", "bridge", "fountain",
                             "clock tower", "bus stop", "ticket hall",
                             "main steps", "boat house", "east door"]):
        t = _rot(TIMES, i + 2)[0]
        add(4,
            f"Meet by the {GAP} at {t}",
            f"At {t} — please be on time, the coach will not wait — "
            f"we all gather by the {ans}.",
            ans,
            "Vaqt savolda oxirida, audioda birinchi")

    # --- 8) Uch bo'lakli tartib almashishi (eng qiyin)
    trio = [("laptop", "Tuesday", "the studio"),
            ("sketchbook", "Friday", "the gallery"),
            ("calculator", "Monday", "the exam hall"),
            ("apron", "Thursday", "the kitchen"),
            ("dictionary", "Wednesday", "the library"),
            ("camera", "Saturday", "the park"),
            ("notebook", "Sunday", "the museum"),
            ("charger", "Monday", "the office"),
            ("swimsuit", "Friday", "the leisure centre"),
            ("racket", "Tuesday", "the courts")]
    for i, (ans, day, place) in enumerate(trio):
        add(5,
            f"Take a {GAP} to {place} on {day}",
            f"On {day}, at {place} — and only on that day, because "
            f"the room is used for something else the rest of the "
            f"week — what you need to have with you is a {ans}.",
            ans,
            "Uchala bo'lak ham teskari tartibda keladi")

    # --- 9) "in PLACE near LANDMARK" <-> "near LANDMARK ... in PLACE"
    near = [("Oakfield", "the station"), ("Millbrook", "the bridge"),
            ("Ashcroft", "the market"), ("Redhill", "the church"),
            ("Longmead", "the school"), ("Fernside", "the park"),
            ("Brackley", "the hospital"), ("Stonegate", "the museum"),
            ("Hartwell", "the harbour"), ("Norbury", "the college")]
    for i, (ans, mark) in enumerate(near):
        add(1,
            f"Situated in {GAP}, near {mark}",
            f"Just by {mark} — you cannot miss it, there is a big "
            f"sign — is the {ans} area, and that is where we are "
            f"based.",
            ans,
            "Mo'ljal savolda oxirida, audioda birinchi aytiladi")

    # --- 10) "Room for N people on FLOOR" <-> "On FLOOR ... seats N"
    seats = [("40", "the ground floor"), ("120", "the first floor"),
             ("25", "the mezzanine"), ("300", "the main hall"),
             ("60", "the annexe"), ("18", "the small room"),
             ("85", "the upper gallery"), ("200", "the theatre"),
             ("12", "the meeting room"), ("500", "the arena")]
    for i, (ans, fl) in enumerate(seats):
        add(5,
            f"Room for {GAP} people on {fl}",
            f"On {fl} — and do check this, because the old leaflet "
            f"gives a different figure and people keep quoting it — "
            f"we can seat {ans}.",
            ans,
            "Joy savolda oxirida, audioda birinchi; oraga chalg'itish "
            "ham qo'shilgan")
    return rows


# =====================================================================
#  11) COMBINATION TRAP
#      Ikki-uch qopqon BIRGA.
# =====================================================================
def _combo_rows():
    rows = []

    def add(step, prompt, say, answer, traps):
        rows.append((step, prompt, say, answer, traps))

    # --- (1) Contrast + Modification (20 ta)
    for i, ans in enumerate(DAYS + DAYS[:3]):
        d1 = _rot(DAYS, i + 2 + (i // 7))[0]
        d2 = _rot(DAYS, i + 4 + (i // 7) * 2)[0]
        add(1, "Day of the visit",
            f"Although {d1} is possible, {d2} would be better. "
            f"Sorry — {d2} is when the hall is booked. Let's fix "
            f"{ans}.",
            ans, ["Contrast", "Modification"])
    for i, ans in enumerate(TIMES):
        d1 = _rot(TIMES, i + 3)[0]
        d2 = _rot(TIMES, i + 6)[0]
        add(2, "Start time",
            f"We could begin at {d1}, but {d2} suits more people. "
            f"Actually, no — {d2} clashes with the delivery. "
            f"{ans} it is.",
            ans, ["Contrast", "Modification"])

    # --- (2) Negation + Delayed (20 ta)
    people = ["administrators", "volunteers", "engineers",
              "researchers", "suppliers", "neighbours", "graduates",
              "technicians", "inspectors", "organisers"]
    for i, ans in enumerate(people):
        d1 = _rot(people, i + 3)[0]
        add(2, "Who will be interviewed",
            f"I don't think we should approach the {d1} — they were "
            f"not involved in this part at all. Let me look at the "
            f"list again. There were several names on it. Right: the "
            f"people we actually need are the {ans}.",
            ans, ["Negation", "Delayed Response"])
    places = ["library", "warehouse", "harbour", "chapel",
              "greenhouse", "workshop", "stadium", "clinic",
              "quarry", "observatory"]
    for i, ans in enumerate(places):
        d1 = _rot(places, i + 4)[0]
        add(3, "Location of the meeting",
            f"It isn't the {d1} any more, whatever the website says. "
            f"Now, where did I write it down... one moment... here. "
            f"It is the {ans}.",
            ans, ["Negation", "Delayed Response"])

    # --- (3) Multiple answers + Negation (20 ta)
    for i, ans in enumerate(TIMES):
        a, b = _rot(TIMES, i + 2)[0], _rot(TIMES, i + 5)[0]
        add(3, "Time the session ENDS",
            f"The building opens at {a} and the first class starts "
            f"at {b}. The session itself does not end at {b}, "
            f"despite what the timetable shows — it finishes at "
            f"{ans}.",
            ans, ["Multiple Answers", "Negation"])
    things = ["helmet", "torch", "notebook", "compass", "blanket",
              "whistle", "passport", "receipt", "badge", "umbrella"]
    for i, ans in enumerate(things):
        a, b = _rot(things, i + 3)[0], _rot(things, i + 6)[0]
        add(4, "Item you must bring YOURSELF",
            f"We provide a {a} and a {b}. You won't need to bring "
            f"either of those. The one item that is not provided is "
            f"a {ans}.",
            ans, ["Multiple Answers", "Negation"])

    # --- (4) Word reorder + Contrast (20 ta)
    for i, ans in enumerate(["clothing", "footwear", "bedding",
                             "stationery", "cookware", "luggage",
                             "furniture", "lighting", "toolkits",
                             "uniforms"]):
        add(4, f"Has sports {GAP} on the lower floors",
            f"The upper floors are given over to the cafe and the "
            f"book section, but it is the lower floors — that is "
            f"where you will find the sports {ans}.",
            ans, ["Word Reorder", "Contrast"])
    for i, ans in enumerate(DAYS + DAYS[:3]):
        d1 = _rot(DAYS, i + 5 + (i // 7) * 2)[0]
        add(4, f"Closed on {GAP}",
            f"Open every day except one. {d1}? No, that is our "
            f"busiest day. It is {ans} when the doors stay shut.",
            ans, ["Word Reorder", "Negation", "Delayed Response"])

    # --- (5) Uchta qopqon birga (20 ta) — eng qiyin
    for i, ans in enumerate(people):
        d1 = _rot(people, i + 2)[0]
        d2 = _rot(people, i + 6)[0]
        add(5, "Group responsible for the report",
            f"Although the {d1} are usually credited, and the {d2} "
            f"certainly helped with the data, I wouldn't say either "
            f"group wrote it. Hang on — I said the {d1} a moment "
            f"ago, forget that. The report was written by the "
            f"{ans}.",
            ans, ["Contrast", "Negation", "Modification"])
    for i, ans in enumerate(places):
        d1 = _rot(places, i + 3)[0]
        d2 = _rot(places, i + 7)[0]
        add(5, "Where the equipment is stored",
            f"Not the {d1} — that was last year. The {d2} was "
            f"suggested, however it turned out to be too damp. I "
            f"keep meaning to update the notice. Everything is now "
            f"kept at the {ans}.",
            ans, ["Negation", "Contrast", "Delayed Response"])
    return rows


def build_rows():
    out = []
    seen = set()

    def push(kind, step, say, prompt, answer, hint, explain, order):
        key = (kind, say, prompt)
        if key in seen:
            return False
        seen.add(key)
        out.append((kind, f"{'R' if kind.endswith('reorder') else 'C'}"
                    f"{step}",
                    {"say": say, "prompt": prompt, "step": step,
                     "rate": RATE_BY_STEP[step], "order": order,
                     "hint": hint},
                    answer, explain))
        return True

    n = 0
    for step, prompt, say, answer, hint in _reorder_rows():
        if push("ielts_reorder", step, say, prompt, answer, hint,
                "WORD REORDER TRAP: savoldagi so'zlar tartibi bilan "
                "audiodagi tartib BOSHQA. Savolda oxirida turgan "
                "bo'lak audioda birinchi kelishi mumkin. Savolni "
                "so'zma-so'z kutib o'tirmang — MA'NOni kuzating.", n):
            n += 1
    n = 0
    for step, prompt, say, answer, traps in _combo_rows():
        if push("ielts_combo", step, say, prompt, answer,
                "Bir nechta qopqon birga: " + " + ".join(traps),
                "COMBINATION TRAP — bu savolda " + str(len(traps)) +
                " ta qopqon birga ishlagan: " + ", ".join(traps) +
                ". Haqiqiy imtihonda aynan shunday bo'ladi: bitta "
                "qopqonni sezib, ikkinchisiga tushib qolasiz.", n):
            n += 1
    return out


def seed_ielts5(db):
    """Idempotent: (kind, say, prompt) bo'yicha yo'qlari qo'shiladi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_listen_v5"):
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
    _seed_mark(db, "ielts_listen_v5")
    return made
