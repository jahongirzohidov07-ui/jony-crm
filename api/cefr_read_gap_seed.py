# -*- coding: utf-8 -*-
"""CEFR READING 1-QISM — WORD FROM THE TEXT (2026-08-26).

Jahongir: "bu esa CEFR reading barcha qismlar savoli qaysilari
50ta bo'lsa 100ta qilasan o'zin qo'shib."

FORMAT (kitobdan, Multilevel Master Reading, Part 1):
"Read the text. Fill in each gap with ONE word. You must use a
word which is somewhere in the rest of the text."

BU TURNING O'ZIGA XOSLIGI. Bo'shliqqa yoziladigan so'z SHU
MATNNING boshqa joyida albatta bor. Ya'ni bola so'zni o'ylab
topmaydi — matn ichidan qidirib topadi. Shuning uchun eng muhim
ko'nikma: bo'shliq atrofidagi gapni o'qib, qaysi TURDAGI so'z
kerakligini aniqlash (ot? fe'l? sifat?) va keyin matnni shu so'z
uchun skanerlash.

MATN MANBASI. Kitob skaner qilingan (442 bet, matn qatlami yo'q),
shuning uchun matnlar shu yerda yozildi — lekin format kitobdagiga
aynan mos. Har javob shu matnning boshqa joyida borligi
generatorda tekshiriladi.
"""

SKILL = "ielts_reading"
KIND = "cefr_word"
GAP = "__________"
INSTR = ("Fill in each gap with ONE word. You must use a word "
         "which is somewhere in the rest of the text.")


CEFR_WORD_TIPS = [
    ("Bu mashq nima",
     "Matnda bo'shliqlar bor. Har biriga BITTA so'z yoziladi va u "
     "so'z SHU MATNNING boshqa joyida albatta uchraydi. O'zingizdan "
     "so'z o'ylab topmaysiz — matndan topasiz.", ""),
    ("Avval SO'Z TURINI aniqlang",
     "Bo'shliqdan oldin va keyin turgan so'zga qarang:\n"
     "«the ……… of» -> ot;\n«are ………» -> sifat yoki ko'plik ot;\n"
     "«to ………» -> fe'lning asosiy shakli;\n«have ………» -> 3-shakl.\n"
     "Bu bir qadam qidiruvni bir necha barobar qisqartiradi.", ""),
    ("Butun matnni skanerlang, faqat atrofni emas",
     "Kerakli so'z bo'shliqdan OLDIN ham, KEYIN ham bo'lishi mumkin. "
     "Ko'p o'quvchi faqat oldingi gaplarni qaraydi va topolmaydi.",
     ""),
    ("Takrorlanadigan so'zlarni belgilang",
     "Matnni birinchi o'qishda tez-tez qaytadigan so'zlarni "
     "belgilab qo'ying — javoblar odatda ana o'shalar orasida "
     "bo'ladi.", ""),
    ("Shakl mos kelishi shart",
     "Matnda «planet» bo'lsa, bo'shliqqa «planets» kerak bo'lishi "
     "mumkin. Ma'no to'g'ri, shakl noto'g'ri bo'lsa ball "
     "berilmaydi — gapga qarab qo'shimchani moslang.", ""),
    ("Bir so'z ikki marta javob bo'lmaydi",
     "Har bo'shliqning javobi boshqa. Bitta so'zni ikki joyga "
     "yozsangiz, ikkalasi ham xato bo'lishi mumkin.", ""),
    ("Oxirida qayta o'qing",
     "Bo'shliqlarni to'ldirib bo'lgach, matnni boshdan oxirigacha "
     "bir marta o'qib chiqing: gap mantiqan va grammatik jihatdan "
     "butun bo'lishi kerak.", ""),
]


# =====================================================================
#  MATNLAR
#
#  DIQQAT — BO'SHLIQLAR QO'LDA QO'YILMAYDI. Avval qo'lda yozib
#  ko'rildi va tekshiruv 14 ta xatoni topdi: javob matnda umuman
#  yo'q edi yoki bitta so'z ikki bo'shliqqa javob bo'lib qolgan edi.
#
#  Shuning uchun matn TOZA yoziladi, bo'shliqni esa dastur tanlaydi:
#  matnda kamida IKKI MARTA uchraydigan mazmunli so'zlar topiladi va
#  ularning KEYINGI uchrashi bo'shliqqa aylantiriladi. Shunda
#  "javob matnning boshqa joyida bor" degan qoida qurilish
#  darajasida kafolatlanadi — xato qilishning iloji yo'q.
# =====================================================================
STOP = set("""a an the and or but if of to in on at by for with from
as is are was were be been being it its this that these those they
them their he she his her him we us our you your i my me not no so
than then there here when where which who whom whose what how why
all any each every some most many much more less few little other
another same such only just also very too can could will would
shall should may might must do does did done have has had having
about after again against because before between both down during
into over under up out off through while until upon per one two
three four five six seven eight nine ten first second third new old
""".split())


def T(level, title, text):
    return {"level": level, "title": title, "text": text}


TEXTS = [
T(1, "The Village Shop",
  "Every village used to have a small shop. Today many of these "
  "shops have closed, because people prefer to drive to a "
  "supermarket in the nearest town. In one village in Wales, "
  "however, the people decided to buy the shop themselves. Forty "
  "families each paid a small amount, and the shop now belongs to "
  "the whole village. It is open six days a week and is run by "
  "volunteers. The people who work there are not paid, but they "
  "say the work is worth it. The nearest supermarket is fourteen "
  "miles away, which is a long drive for an elderly person without "
  "a car, so the village keeps its own shop alive."),
T(2, "Learning to Ride",
  "Most children learn to ride a bicycle at about six. The usual "
  "method is to remove the pedals so that the child can push the "
  "bicycle along with both feet and learn to balance. Once the "
  "child can balance for a few seconds, the pedals go back on. "
  "This method works far better than the old method, in which an "
  "adult ran behind holding the bicycle and let go without "
  "warning. Children taught that way often fell. Teachers now say "
  "the pedals should be the last thing added, and that no adult "
  "should ever let go without telling the child."),
T(3, "Salt on the Roads",
  "Every winter, councils spread salt on the roads to stop ice "
  "forming. Salt lowers the temperature at which water freezes, so "
  "a road surface treated with salt stays clear until about minus "
  "eight degrees. Below that the salt stops working and the water "
  "freezes anyway. There are costs. Salt damages the metal under "
  "cars, it harms plants beside the roads, and it washes into "
  "rivers. Some councils now mix the salt with beet juice, which "
  "makes it stick to the surface instead of bouncing off. That "
  "means less salt is needed for the same result, and less of it "
  "reaches the rivers."),
T(4, "The Weekly Market",
  "The market in the square has been held on the same day every "
  "week for six hundred years. Traders arrive before dawn and set "
  "up their stalls in the dark. By eight o'clock the square is "
  "full of people. Most of the vegetables come from farms within "
  "thirty miles, so the vegetables were picked the day before. "
  "Supermarkets cannot match that freshness, although they can "
  "match the price. Younger shoppers say they come for the "
  "freshness, not for the price. The council once tried to move "
  "the market to a car park outside the town, but the traders "
  "refused and the plan was dropped. The stalls are still set up "
  "in the square before dawn every week."),
T(5, "Why Bread Rises",
  "Bread rises because yeast, a living thing, feeds on the sugar "
  "in flour and produces gas. The gas is trapped by gluten, a "
  "stretchy network that forms when flour is mixed with water and "
  "kneaded. Without gluten the gas simply escapes and the loaf "
  "stays flat. Without yeast there is no gas at all. Warmth speeds "
  "the process up, which is why bakers leave the dough in a warm "
  "place, and cold slows it down, which is why some bakers put the "
  "dough in a fridge overnight for a better flavour. Too much heat "
  "kills the yeast, so an oven that is too hot will stop the loaf "
  "rising before the gluten has set."),
T(6, "The First Photograph of a Person",
  "The oldest photograph showing a human being was taken in Paris "
  "in 1838. The photograph shows a busy boulevard that appears "
  "completely empty, because the exposure lasted several minutes "
  "and moving traffic left no trace. Only one figure is visible: a "
  "man having his boots polished, who stood still long enough to "
  "register. The bootblack kneeling in front of the man is "
  "fainter, because he was moving slightly. Every other figure on "
  "that boulevard that morning has disappeared. The photographer "
  "did not plan the picture; the picture was an accident of the "
  "long exposure. Today the same boulevard would need an exposure "
  "of a fraction of a second."),
T(7, "Sleeping Twice",
  "Before artificial light, people in Europe often slept in two "
  "blocks. They went to bed at dusk, woke around midnight for an "
  "hour or two, then slept again until dawn. Diaries and court "
  "records treat this pattern as completely ordinary: during that "
  "middle hour people prayed, talked, visited neighbours or simply "
  "lay thinking. The practice disappeared within a generation of "
  "cheap light, which pushed bedtime later and squeezed the two "
  "blocks into one. Some researchers argue that people who wake at "
  "midnight today are not ill but following the older pattern, and "
  "that calling the practice a disorder makes it worse."),
T(8, "The Cost of a Free App",
  "An application that costs nothing to install is rarely free in "
  "any other sense. The developer must be paid, and if the user "
  "does not pay, someone else does. Usually that someone is an "
  "advertiser, and what the advertiser buys is attention and "
  "information about the user. Some apps sell a paid version "
  "without advertising, which is the honest form of the bargain: "
  "either you pay with money or you pay with attention. The "
  "trouble is that the second price is invisible. A user can "
  "compare two prices in pounds, but cannot compare how much "
  "information each app collects. Regulators have therefore begun "
  "to require that every app states plainly what information it "
  "takes."),
T(9, "Rebuilding a Cathedral",
  "When fire destroyed the roof of a medieval cathedral, the first "
  "argument was not about money but about time. One group wanted "
  "the roof rebuilt exactly as it had been, using oak beams cut by "
  "hand, which would take a decade. Another group wanted a modern "
  "structure of steel and glass, which would take three years. The "
  "traditional design won, partly because the old design had stood "
  "for eight hundred years and nobody could promise the same of "
  "steel. Finding the oak proved harder than expected: an oak of "
  "the right size takes two centuries to grow. In the end a "
  "thousand trees were given by private owners, which is why the "
  "roof cost less than the modern structure would have done."),
T(10, "The Shipping Container",
  "Before 1956, loading a ship was slow, expensive and dangerous. "
  "Goods arrived in barrels, sacks and crates of every shape, and "
  "dockers moved the goods by hand. A ship could spend longer in "
  "port than at sea. The invention that changed this was not a new "
  "engine but a steel box of a fixed size, the shipping container. "
  "Because every container was identical, cranes could be built to "
  "handle it, lorries could carry it and ships could stack it. The "
  "cost of moving goods fell so far that it stopped mattering "
  "where a factory was built. That single invention did more for "
  "world trade than most treaties. It also destroyed the work of "
  "the dockers, whose skill was no longer needed once every box "
  "was the same size."),
T(11, "Left-handed in a Right-handed World",
  "About one person in ten is left-handed, and the proportion has "
  "been steady for as long as anyone has measured it. Almost every "
  "tool is designed for the other hand: scissors, tin openers, "
  "even the direction in which a page turns. Most left-handed "
  "people therefore learn to use the weaker hand for many tasks, "
  "which is why they often appear more skilful with both. There is "
  "no evidence that being left-handed makes anyone cleverer, "
  "though the claim is repeated often. What is true is that a "
  "left-handed child taught by a right-handed teacher may copy a "
  "grip that suits the teacher and not the child. A good teacher "
  "shows the child a grip that suits the child's own hand."),
T(12, "The Quiet Carriage",
  "Many trains now have one carriage in which phone calls and loud "
  "conversation are forbidden. The rule is popular but almost "
  "never enforced, because staff have no power to remove a "
  "passenger for talking. In practice the rule works only if the "
  "passengers enforce it themselves, and most people are unwilling "
  "to speak to a stranger. Researchers who studied this found that "
  "a single sign is ignored, while a sign plus an announcement is "
  "obeyed far more often. The announcement matters because it "
  "tells everyone that everyone else has heard the rule too. "
  "Shared knowledge, not the rule itself, is what keeps the "
  "carriage quiet, which is why some companies repeat the "
  "announcement at every stop."),
T(13, "Counting Trees",
  "Nobody knew how many trees there were on Earth until 2015. The "
  "first serious attempt combined satellite images with more than "
  "four hundred thousand measurements taken on the ground, because "
  "a satellite can see the top of a forest but cannot count the "
  "trunks beneath it. The answer, about three trillion trees, was "
  "seven times higher than the previous estimate. That did not "
  "mean there were suddenly more trees; it meant the old estimate "
  "had been wrong. Counting from the ground is slow, so the "
  "researchers used the satellite images to spread the ground "
  "measurements across areas nobody had visited. Without the "
  "ground work the images would have been useless, and without the "
  "images the ground work would have covered too little land."),
T(14, "The Rules of the Road",
  "Countries drive on the left or the right for historical rather "
  "than practical reasons. Before cars, a rider on horseback kept "
  "to the left so that the sword arm faced an approaching "
  "stranger. Wagons drawn by teams of horses changed that, because "
  "the driver sat on the rear left animal and wanted to see the "
  "edge of the road, which meant driving on the right. Countries "
  "that used heavy wagons therefore moved to the right, while "
  "countries that did not kept to the left. Sweden changed sides "
  "in 1967, in a single morning, and accidents fell for two years "
  "because every driver was concentrating. Accidents rose again "
  "once the new rule became habit, which suggests that attention, "
  "not the side of the road, is what keeps people safe."),
T(15, "Museums Without Objects",
  "A growing number of museums own almost nothing. Instead of "
  "collecting objects, they borrow them, or display copies, or "
  "tell a story with film and sound. Supporters say that a museum "
  "exists to explain, not to hoard, and that a good story can "
  "teach more than a case of unlabelled objects. Critics reply "
  "that a copy is not the same as the real object, and that people "
  "travel a long way to stand in front of a genuine object. Both "
  "sides agree on one point: a museum that borrows must plan years "
  "ahead, because the object it wants may be promised elsewhere. "
  "The cost of insurance for a borrowed object can be higher than "
  "the cost of making a copy."),
T(16, "The Longest Running Experiment",
  "In a laboratory in Australia, a funnel of pitch has been "
  "dripping since 1927. Pitch looks like a solid and shatters when "
  "struck, but it is a liquid, and the experiment was set up to "
  "prove it. Nine drops have fallen in almost a century. Nobody "
  "has ever seen a drop fall: the first drop was missed, a camera "
  "failed on another occasion, and a technician stepped out for "
  "tea before the eighth. The funnel is now watched by a webcam so "
  "that the next drop can be recorded, and the laboratory keeps "
  "that webcam running day and night. The professor who began the "
  "experiment died in the same laboratory long before the third "
  "drop fell."),
T(17, "Why Ice Floats",
  "Almost every substance becomes denser as it cools, so the solid "
  "form sinks in the liquid form. Water is the great exception. As "
  "water cools towards freezing its molecules arrange themselves "
  "into a rigid pattern with gaps in it, so ice takes up more "
  "space than the same mass of water and therefore floats. The "
  "consequence is enormous. Because ice floats, a lake freezes "
  "from the top down, and the layer of ice insulates the water "
  "beneath it. If ice sank, a lake would freeze from the bottom "
  "up, and every fish in that lake would die each winter. Life in "
  "cold water depends on this single strange property of water."),
T(18, "The Pencil",
  "A pencil contains no lead. The dark material is graphite, mixed "
  "with clay and baked. The proportion of clay decides how hard "
  "the pencil is: more clay makes a harder pencil that leaves a "
  "fainter line, less clay makes a softer pencil that leaves a "
  "darker line. The name lead survives from a mistake made in the "
  "sixteenth century, when a large deposit of graphite was found "
  "in England and everyone assumed the black material was a form "
  "of lead. The mistake stayed in the language long after the "
  "graphite was correctly identified, which is why a pencil is "
  "still said to contain lead."),
T(19, "The Empty Middle Seat",
  "Airlines have known for years that the middle seat is the least "
  "popular, and several have tried to solve the problem. One "
  "airline charged less for the middle seat, which worked but "
  "reduced income. Another designed a middle seat slightly wider "
  "than the others, set a few centimetres back so that shoulders "
  "do not touch. That design costs nothing to fly and has been "
  "adopted by several airlines. The simplest answer, leaving the "
  "middle seat empty, is the only one no airline will accept, "
  "because an empty seat earns nothing and the whole economics of "
  "a modern airline depends on filling every seat."),
T(20, "Reading Aloud",
  "For most of history, reading meant reading aloud. Ancient texts "
  "were written without spaces between words, which makes silent "
  "reading almost impossible, so a reader sounded out the letters "
  "to find where each word ended. Spaces were introduced by Irish "
  "monks in the seventh century, and silent reading spread slowly "
  "afterwards. Augustine records his astonishment at seeing a man "
  "read without moving his lips, which shows how unusual silent "
  "reading still was. Today reading aloud survives mainly for "
  "children, but teachers point out that a child who can read "
  "aloud fluently has already solved the hardest part of "
  "reading."),
]


# =====================================================================
#  BO'SHLIQLARNI DASTUR TANLAYDI
# =====================================================================
def _pick_gaps(text, n=5):
    """Matndan n ta bo'shliq tanlaydi.

    Qoida: so'z matnda kamida IKKI marta uchrasin va bo'shliq uning
    IKKINCHI uchrashiga qo'yilsin. Shunda javob har doim matnning
    boshqa (oldingi) joyida turadi — kitobdagi "you must use a word
    which is somewhere in the rest of the text" qoidasi qurilish
    darajasida bajariladi.

    Qaytaradi: [(boshlanish, tugash, so'z), ...] joylashuv bo'yicha."""
    import re as _re
    import collections as _c
    toks = [(m.start(), m.end(), m.group(0))
            for m in _re.finditer(r"[A-Za-z]+", text)]
    low = _c.defaultdict(list)
    for a, b, w in toks:
        lw = w.lower()
        if lw in STOP or len(lw) < 4:
            continue
        low[lw].append((a, b))
    # ikkinchi uchrashi bor so'zlar
    cands = [(pos[1][0], pos[1][1], w)
             for w, pos in low.items() if len(pos) >= 2]
    cands.sort()
    if len(cands) < n:
        return []
    # matn bo'ylab teng tarqatib tanlaymiz
    step = len(cands) / n
    picked = [cands[int(i * step)] for i in range(n)]
    # bir xil so'z ikki marta tushmasin
    seen, out = set(), []
    i = 0
    for a, b, w in picked:
        if w in seen:
            continue
        seen.add(w)
        out.append((a, b, w))
    for a, b, w in cands:
        if len(out) >= n:
            break
        if w not in seen:
            seen.add(w)
            out.append((a, b, w))
    out.sort()
    return out[:n]


def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase)."""
    out = []
    for t in TEXTS:
        gaps = _pick_gaps(t["text"], 5)
        assert len(gaps) == 5, (t["title"], len(gaps))
        # bo'shliqli matnni yasaymiz
        body, last = [], 0
        for i, (a, b, w) in enumerate(gaps, 1):
            body.append(t["text"][last:a])
            body.append(f"({i}) {GAP}")
            last = b
        body.append(t["text"][last:])
        gapped = "".join(body)
        for i, (a, b, w) in enumerate(gaps, 1):
            expl = (f"{i}-bo'shliq javobi: {w}. Bu so'z matnning "
                    f"boshqa joyida ham bor — shuning uchun uni "
                    f"o'ylab topish emas, TOPISH kerak edi.")
            out.append((
                KIND, t["level"],
                {"title": t["title"],
                 "passage": t["title"] + "\n\n" + gapped,
                 "prompt": f"({i}) bo'shlig'iga qaysi so'z tushadi?",
                 "gap_no": i,
                 "instruction": INSTR,
                 "step": t["level"],
                 "step_title": f"{t['level']}-daraja",
                 "order": i},
                w, expl, None, None))
    return out


def seed_cefr_word(db):
    """Idempotent: bor bo'lsa qayta yozmaydi (hech narsa o'chmaydi)."""
    import json
    import models
    have = {
        (r.level, json.loads(r.payload).get("order"))
        for r in db.query(models.PracticeItem)
        .filter(models.PracticeItem.skill == SKILL,
                models.PracticeItem.kind == KIND).all()}
    n = 0
    for kind, level, payload, answer, explain, alt, para in build_rows():
        if (level, payload["order"]) in have:
            continue
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt, explain=explain, is_active=1))
        n += 1
    if n:
        db.commit()
    return n
