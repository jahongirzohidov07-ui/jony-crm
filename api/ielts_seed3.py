# -*- coding: utf-8 -*-
"""IELTS LISTENING — 3-BLOK: EXACT WORD TRAP (2026-08-24).

Jahongir: "keyingisi exact word trap qopqoni... siz notogri
variantdagi bor so'zlarni audioda eshitib qolasiz lekin u javob
savolga togri kelmaydi, kopincha javob aytilmagan variantda boladi
shunaqa usullardagi qopqonlardan ham 100ta tuzib qoygin."

TUZOQ QANDAY ISHLAYDI (Jahongir yuborgan Sheepmarket misolidagi
kabi):

  Savol:  Eng tez o'sayotgan aholi guruhi kim?
  A young professional people   <- TO'G'RI, lekin audioda bu
                                   so'zlar YO'Q. Faqat ma'nosi bor:
                                   "graduates embarking on careers
                                   in fashion and design are buying
                                   up the new apartments".
  B students from the university <- so'zlari audioda BOR, lekin ular
                                   yashamaydi — kechqurun kelib
                                   ketishadi.
  C employees in the local market<- so'zlari audioda BOR, lekin ular
                                   ILGARI yashagan (used to live).

Ya'ni: NOTO'G'RI variantlarning so'zlari audioda aynan eshitiladi,
TO'G'RI variantniki esa umuman aytilmaydi — faqat boshqacha
ifodalanadi. Eshitgan so'zini belgilagan talaba yiqiladi.

Har element uchta narsani beradi: matn (audio), savol, uchta
variant. Javobdan keyin HAR BIR noto'g'ri variant nega tuzoq
ekani tushuntiriladi — talaba xatosini tushunib olsin.

QIYINLIK 1..5: pastda parafraz yaqin va tuzoq ochiq; yuqorida
parafraz uzoq, tuzoqlar ikkitadan va vaqt ("ilgari / hozir /
kelajakda") bilan aralashadi.
"""

SKILL = "ielts_listening"
RATE_BY_STEP = {1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0}


# =====================================================================
#  QOLIPLAR
#
#  Har qolip TO'G'RI javobni PARAFRAZ bilan beradi, ikki noto'g'ri
#  variantning so'zlarini esa matnga AYNAN joylashtiradi — lekin
#  boshqa rolda (ilgari edi / boshqa maqsadda keladi / rejada bor
#  lekin hali yo'q / boshqa joyda).
#
#  d = (savol, to'g'ri variant yorlig'i, uning PARAFRAZI,
#       1-tuzoq yorlig'i, uning matndagi roli,
#       2-tuzoq yorlig'i, uning matndagi roli, mavzu)
# =====================================================================

def _t_now_vs_past(d):
    """Tuzoq: biri ILGARI edi, biri BOSHQA maqsadda keladi."""
    q, ok, para, w1, r1, w2, r2, topic = d
    say = (f"Welcome to this short talk about {topic}. "
           f"{w1.capitalize()} {r1}, and {w2} {r2}. "
           f"These days, though, the group you will find here most "
           f"of all is {para}.")
    return say, q, ok, [w1, w2]


def _t_plan_vs_real(d):
    """Tuzoq: biri REJADA, biri BEKOR qilingan; to'g'risi hozir bor."""
    q, ok, para, w1, r1, w2, r2, topic = d
    say = (f"A quick update on {topic}. "
           f"{w1.capitalize()} {r1} — that is still only a proposal. "
           f"{w2.capitalize()} {r2}, so that idea was dropped. "
           f"What we actually have now is {para}.")
    return say, q, ok, [w1, w2]


def _t_other_place(d):
    """Tuzoq: ikkalasi ham BOSHQA joyda / boshqa bo'limda."""
    q, ok, para, w1, r1, w2, r2, topic = d
    say = (f"Let me explain how {topic} is organised. "
           f"{w1.capitalize()} {r1}, and {w2} {r2}. "
           f"Here, on the other hand, it is {para}.")
    return say, q, ok, [w1, w2]


def _t_someone_else_says(d):
    """Tuzoq: noto'g'ri variantlarni BOSHQA odam aytadi."""
    q, ok, para, w1, r1, w2, r2, topic = d
    say = (f"Interviewer: So, about {topic} — people say {w1} {r1}. "
           f"Expert: That is a common belief, yes, and some also "
           f"argue {w2} {r2}. But the research points somewhere "
           f"else entirely: it is {para}.")
    return say, q, ok, [w1, w2]


def _t_correction(d):
    """Tuzoq: gapiruvchi o'zini tuzatadi — birinchi aytgani xato."""
    q, ok, para, w1, r1, w2, r2, topic = d
    say = (f"Right, {topic}. I was going to say {w1} {r1} — no, "
           f"forget that, I am thinking of last year. And {w2} {r2}, "
           f"which is not the same thing at all. The answer you want "
           f"is {para}.")
    return say, q, ok, [w1, w2]


# ---------------------------------------------------------------
#  MA'LUMOT: har qatorda tuzoq tayyor holda
# ---------------------------------------------------------------
D_NOW_PAST = [
    ("Which is the fastest-growing group of residents in the area?",
     "young professional people",
     "graduates starting careers in design who are buying the new "
     "flats",
     "students from the university",
     "come in for the nightlife but live on campus",
     "employees in the local market",
     "used to live in the small houses that were pulled down",
     "the Sheepmarket district"),
    ("What is the building mainly used for now?",
     "a community centre",
     "a place where neighbours meet, run classes and hold parties",
     "a furniture factory",
     "occupied this site until the nineteen-eighties",
     "a car showroom",
     "was here for a few years after that",
     "the old hall on Mill Street"),
    ("Who makes up most of the club's members today?",
     "retired people",
     "members who have finished work and have free mornings",
     "school children",
     "made up the club when it opened",
     "office workers",
     "joined in large numbers ten years ago",
     "the town swimming club"),
    ("What does the shop sell most of?",
     "second-hand books",
     "titles that have already had one owner",
     "greeting cards",
     "were the main product when it opened",
     "children's toys",
     "were added later and then removed",
     "the corner shop on Bridge Road"),
    ("Which subject attracts the most students now?",
     "computer science",
     "programming and data courses",
     "history",
     "was the college's strongest subject for decades",
     "modern languages",
     "brought in most students in the nineties",
     "the city college"),
    ("What is the main use of the river today?",
     "leisure boating",
     "people taking small boats out at weekends for pleasure",
     "transporting coal",
     "was its purpose in the last century",
     "commercial fishing",
     "continued until the nineteen-sixties",
     "the river through the town"),
    ("Who visits the gallery most often?",
     "local families",
     "parents bringing their children at weekends",
     "art students",
     "were the main visitors when it opened",
     "foreign tourists",
     "come only in the summer months",
     "the city gallery"),
    ("What is grown on the farm now?",
     "vegetables",
     "carrots, beans and other crops for the market",
     "wheat",
     "covered these fields for generations",
     "apples",
     "were grown in the orchard that was cut down",
     "Hill Farm"),
    ("What is the hall used for on weekday evenings?",
     "language classes",
     "adults learning Spanish and French",
     "wedding receptions",
     "take place there at weekends",
     "sports training",
     "happens in the building next door",
     "the village hall"),
    ("Which type of housing is being built now?",
     "small flats",
     "one and two bedroom apartments for single people",
     "family houses",
     "were built in the first phase",
     "student halls",
     "were planned but never approved",
     "the new development"),
]

D_PLAN_REAL = [
    ("What does the centre offer at the moment?",
     "a swimming pool",
     "a twenty-five metre pool that opened last spring",
     "a climbing wall",
     "may be added in a later phase",
     "a running track",
     "was too expensive to build",
     "the new sports centre"),
    ("What can visitors do this year?",
     "guided walks",
     "join a member of staff for a tour of the grounds on foot",
     "boat trips",
     "are being considered for next season",
     "cycle hire",
     "was tried once and did not work",
     "the country park"),
    ("What is included in the ticket price?",
     "a hot drink",
     "a cup of tea or coffee at the end",
     "a printed guide",
     "will be introduced when funds allow",
     "car parking",
     "was removed from the package last year",
     "the museum ticket"),
    ("What service is available now?",
     "an evening bus",
     "a service that runs after seven in the evening",
     "a night train",
     "is still under discussion with the operator",
     "a taxi scheme",
     "ran for six months and was withdrawn",
     "transport to the village"),
    ("What does the course include this term?",
     "a work placement",
     "four weeks in a real company",
     "an overseas trip",
     "is planned for a future year",
     "a research project",
     "was moved to the second year",
     "the business course"),
    ("What has the library added recently?",
     "a study area",
     "quiet desks on the first floor for people revising",
     "a coffee shop",
     "is only an idea at this stage",
     "a children's room",
     "was closed when the funding ended",
     "the town library"),
    ("What is provided for guests?",
     "free wifi",
     "internet access at no extra charge",
     "airport transfers",
     "are being looked into for next season",
     "room service",
     "stopped during the refurbishment",
     "the guest house"),
    ("What can members use free of charge?",
     "the gym",
     "the exercise room with weights and machines",
     "the tennis courts",
     "will be free once the resurfacing is finished",
     "the sauna",
     "was closed for safety reasons",
     "the club facilities"),
    ("What is available on Saturdays?",
     "a repair workshop",
     "volunteers who will fix broken items for you",
     "a farmers' market",
     "is hoped for later in the year",
     "a book sale",
     "has moved to the school instead",
     "the community programme"),
    ("What does the app currently do?",
     "show live times",
     "tell you when the next one is actually arriving",
     "sell tickets",
     "is a feature they are still developing",
     "give route maps",
     "was dropped from the design",
     "the transport app"),
]

D_OTHER_PLACE = [
    ("Where should visitors leave their bags?",
     "the cloakroom",
     "the small room by the entrance where staff take your things",
     "the lockers",
     "are for staff only",
     "the reception desk",
     "cannot store anything for visitors",
     "the gallery"),
    ("Which floor has the reading room?",
     "the second floor",
     "two flights up, above the offices",
     "the ground floor",
     "has only the catalogue and the entrance",
     "the basement",
     "holds the archive and is closed to the public",
     "the library building"),
    ("Who should students contact about timetables?",
     "the course office",
     "the small office next to lecture theatre two",
     "the main reception",
     "deals with visitors and post",
     "the student union",
     "handles clubs and societies",
     "the department"),
    ("Where is lunch served?",
     "the garden room",
     "the room that looks out over the lawn",
     "the main hall",
     "is used for lectures during the day",
     "the terrace",
     "is only open in fine weather",
     "the conference centre"),
    ("Where can equipment be borrowed?",
     "the store room",
     "the room behind the changing area",
     "the equipment shop",
     "sells items but does not lend them",
     "the gym",
     "keeps only its own machines",
     "the sports centre"),
    ("Which entrance should deliveries use?",
     "the side gate",
     "the opening on the left of the building",
     "the main entrance",
     "is for visitors on foot",
     "the car park",
     "has no access to the building",
     "the site"),
    ("Where are the workshops held?",
     "the annexe",
     "the separate low building across the yard",
     "the main block",
     "houses the offices",
     "the studio",
     "is booked for exhibitions",
     "the arts centre"),
    ("Where can parents wait?",
     "the cafe",
     "the seating area where drinks are served",
     "the poolside",
     "is not open to spectators during lessons",
     "the car park",
     "has no shelter",
     "the swimming lessons"),
    ("Which room is used for the meeting?",
     "room fourteen",
     "the one at the end of the corridor on the left",
     "room forty",
     "is being decorated",
     "the boardroom",
     "is reserved for directors",
     "the office"),
    ("Where should forms be handed in?",
     "the post box",
     "the metal box on the wall by the door",
     "the front desk",
     "is not staffed after four",
     "the office upstairs",
     "only deals with payments",
     "the application process"),
]

D_SOMEONE_SAYS = [
    ("What does the expert say is the main cause?",
     "poor sleep",
     "not getting enough rest at night",
     "too much screen time",
     "is to blame",
     "a lack of exercise",
     "is the real problem",
     "tiredness in teenagers"),
    ("What does the researcher say helps most?",
     "regular practice",
     "doing a little every single day",
     "natural talent",
     "matters most",
     "expensive equipment",
     "makes the difference",
     "learning an instrument"),
    ("What does the guide say is the best time to visit?",
     "early morning",
     "just after the gates open, before the coaches arrive",
     "the afternoon",
     "is quietest",
     "the evening",
     "has the best light",
     "the castle"),
    ("What does the scientist say the birds eat mainly?",
     "insects",
     "small creatures they catch in the air",
     "seeds",
     "make up their diet",
     "berries",
     "are what they prefer",
     "the birds on the island"),
    ("What does the manager say attracts customers?",
     "the location",
     "being right beside the station",
     "low prices",
     "bring people in",
     "advertising",
     "is what works",
     "the shop's success"),
    ("What does the teacher say students find hardest?",
     "writing essays",
     "putting an argument down on paper",
     "the exams",
     "are the difficult part",
     "group work",
     "causes the most trouble",
     "the course"),
    ("What does the doctor say is most important?",
     "drinking water",
     "taking in enough fluid through the day",
     "eating vegetables",
     "is the key",
     "taking vitamins",
     "makes the difference",
     "staying healthy in summer"),
    ("What does the architect say the design achieves?",
     "better light",
     "letting far more daylight into every room",
     "lower costs",
     "was the aim",
     "more space",
     "is what people notice",
     "the new school building"),
    ("What does the farmer say has changed most?",
     "the weather",
     "the pattern of rain and temperature through the year",
     "machinery",
     "has transformed the work",
     "prices",
     "are the biggest change",
     "farming today"),
    ("What does the historian say the building was first used for?",
     "storing grain",
     "keeping the harvest dry over the winter",
     "housing soldiers",
     "was its first purpose",
     "holding markets",
     "is what it was built for",
     "the old stone building"),
]

D_CORRECTION = [
    ("How long does the tour last?",
     "ninety minutes",
     "an hour and a half",
     "two hours",
     "is what the leaflet says",
     "forty-five minutes",
     "is the short version we no longer run",
     "the guided tour"),
    ("Which day does the group meet?",
     "Thursday",
     "the day before the weekend starts",
     "Tuesday",
     "was the day last term",
     "Saturday",
     "is when the junior group meets",
     "the walking group"),
    ("What should participants bring?",
     "a packed lunch",
     "your own food for the middle of the day",
     "walking boots",
     "are provided by us",
     "a water bottle",
     "is what the old list said",
     "the day trip"),
    ("Who leads the session?",
     "a volunteer",
     "someone who gives their time without being paid",
     "a qualified coach",
     "runs the advanced group",
     "a member of staff",
     "used to do it",
     "the beginners' session"),
    ("How much does membership cost?",
     "thirty pounds",
     "three tens",
     "fifty pounds",
     "is the family rate",
     "twenty pounds",
     "was last year's price",
     "the club"),
    ("Where does the trip start?",
     "the station",
     "the place where the trains come in",
     "the town hall",
     "was the meeting point before",
     "the car park",
     "is where the coach parks afterwards",
     "the excursion"),
    ("What is the deadline?",
     "the end of the month",
     "the last day in April",
     "next Friday",
     "is when the office closes for repairs",
     "the fifteenth",
     "was the date on the first notice",
     "the applications"),
    ("What age group is the class for?",
     "adults",
     "anyone over eighteen",
     "teenagers",
     "have their own separate class",
     "children",
     "were the original group",
     "the pottery class"),
    ("What is the main topic this week?",
     "recycling",
     "what happens to our waste after it is collected",
     "climate change",
     "is next week's subject",
     "energy saving",
     "was covered last time",
     "the evening talks"),
    ("How do people book?",
     "by phone",
     "by ringing the number on the notice",
     "online",
     "is not working at the moment",
     "in person",
     "was the only way before",
     "the tickets"),
]

TEMPLATES = [
    (1, _t_now_vs_past, D_NOW_PAST),
    (2, _t_plan_vs_real, D_PLAN_REAL),
    (3, _t_other_place, D_OTHER_PLACE),
    (4, _t_someone_else_says, D_SOMEONE_SAYS),
    (5, _t_correction, D_CORRECTION),
]

# Ikkinchi to'lqin: bir xil qoliplarni BOSHQA mavzularda takrorlaymiz
# (jami 100 ta bo'lishi uchun). Mavzular boshqacha, tuzoq mantig'i
# o'sha — talaba qolipni tanib olsin, bu foydali.
D2_NOW_PAST = [
    ("Who uses the car park most?",
     "hospital visitors",
     "people coming to see patients",
     "shop customers",
     "filled it before the supermarket opened its own",
     "office workers",
     "used it until the offices moved out",
     "the car park on King Street"),
    ("What is the room used for now?",
     "storage",
     "keeping boxes and spare furniture",
     "a classroom",
     "was its use for many years",
     "a staff room",
     "was tried briefly",
     "the room at the back"),
    ("Which language is taught most?",
     "Spanish",
     "the language spoken across South America",
     "French",
     "had the most classes for a long time",
     "German",
     "was popular in the past",
     "the language school"),
    ("What is the main product now?",
     "furniture",
     "tables and chairs made from local wood",
     "shoes",
     "were made here for a century",
     "textiles",
     "took over for a short period",
     "the workshop"),
    ("Who attends the morning session?",
     "parents with babies",
     "mothers and fathers bringing very young children",
     "pensioners",
     "came in the mornings years ago",
     "school groups",
     "visit in the afternoons",
     "the swimming pool"),
    ("What does the field produce now?",
     "solar power",
     "electricity generated from panels",
     "sheep",
     "grazed here for generations",
     "barley",
     "was the crop until recently",
     "the field on the hill"),
    ("Which group borrows the most?",
     "teenagers",
     "readers between thirteen and eighteen",
     "young children",
     "borrowed most when the library opened",
     "older readers",
     "were the biggest group ten years ago",
     "the library's borrowers"),
    ("What is the pier used for today?",
     "fishing",
     "people sitting with rods along the edge",
     "steamer trips",
     "left from here in Victorian times",
     "concerts",
     "were held in the pavilion that burned down",
     "the old pier"),
    ("Who works in the building now?",
     "designers",
     "people creating graphics and websites",
     "printers",
     "occupied it for eighty years",
     "journalists",
     "were based here until the paper closed",
     "the old print works"),
    ("What is the lake used for now?",
     "wildlife watching",
     "people coming to look at birds and other animals",
     "water supply",
     "was its purpose when it was dug",
     "sailing",
     "was allowed until the club moved",
     "the lake in the park"),
]

D2_PLAN_REAL = [
    ("What can people do at the centre now?",
     "borrow tools",
     "take home a drill or a ladder for a few days",
     "attend repair classes",
     "are planned for the autumn",
     "hire a workshop space",
     "proved too expensive to run",
     "the community centre"),
    ("What is open to the public this summer?",
     "the walled garden",
     "the enclosed garden behind the house",
     "the tower",
     "will open when the stairs are repaired",
     "the chapel",
     "was closed after the roof was damaged",
     "the estate"),
    ("What is provided on the course?",
     "online materials",
     "notes and videos you can use from home",
     "printed handouts",
     "are being phased in again",
     "a textbook",
     "was dropped to keep costs down",
     "the evening course"),
    ("What does the ticket allow?",
     "unlimited travel",
     "as many journeys as you like in one day",
     "seat reservations",
     "will be added to the system later",
     "a refund",
     "is no longer offered",
     "the day ticket"),
    ("What is available at the surgery?",
     "online booking",
     "making an appointment through the website",
     "a walk-in clinic",
     "is under review",
     "home visits",
     "were stopped last winter",
     "the doctor's surgery"),
    ("What can members do this year?",
     "vote on projects",
     "choose which schemes get the money",
     "attend the annual dinner",
     "is being organised for next year",
     "use the members' room",
     "closed when the lease ended",
     "the society"),
    ("What is offered to new staff?",
     "a mentor",
     "an experienced colleague who supports you",
     "a training week",
     "is still being designed",
     "a relocation payment",
     "was withdrawn in the last budget",
     "the induction"),
    ("What does the museum lend to schools?",
     "object boxes",
     "cases of real items teachers can use in class",
     "a mobile exhibition",
     "is hoped for next year",
     "a visiting speaker",
     "had to stop when the post was cut",
     "the museum's outreach"),
    ("What is included in the rent?",
     "heating",
     "the cost of keeping the flat warm",
     "electricity",
     "may be included in future contracts",
     "internet",
     "was taken out of the agreement",
     "the flat"),
    ("What can visitors join today?",
     "a craft session",
     "making something with your hands with a tutor",
     "a guided tour",
     "starts again in April",
     "a talk",
     "was cancelled this morning",
     "today's programme"),
]

# Ikkinchi to'lqinda qoliplar BOSHQA ma'lumot bilan kesishtiriladi —
# shunda bir xil savol boshqa audio bilan keladi va talaba qolipni
# emas, MA'NONI tinglashni o'rganadi.
TEMPLATES2 = [
    (2, _t_now_vs_past, D2_NOW_PAST),
    (3, _t_plan_vs_real, D2_PLAN_REAL),
    (4, _t_correction, D_OTHER_PLACE),
    (4, _t_someone_else_says, D_PLAN_REAL),
    (5, _t_other_place, D_NOW_PAST),
]


def build_rows():
    """(kind, level, payload, answer, explain) ro'yxati."""
    out = []
    seen = set()
    order = 0
    for group in (TEMPLATES, TEMPLATES2):
        for step, fn, data in group:
            for d in data:
                say, q, ok, wrongs = fn(d)
                key = (q, say)
                if key in seen:
                    continue
                seen.add(key)
                # Variantlar tartibi barqaror, lekin A doim to'g'ri
                # bo'lib qolmasin: navbat bilan aylantiramiz.
                opts = [ok, wrongs[0], wrongs[1]]
                shift = order % 3
                opts = opts[-shift:] + opts[:-shift] if shift else opts
                out.append((
                    "ielts_exact", f"E{step}",
                    {"say": say, "prompt": q, "options": opts,
                     "step": step, "rate": RATE_BY_STEP[step],
                     "order": order,
                     "hint": "Eshitgan so'zingizni emas — MA'NOSINI "
                             "tanlang"},
                    ok,
                    "TUZOQ: «" + wrongs[0] + "» va «" + wrongs[1] +
                    "» so'zlari audioda AYNAN eshitiladi, lekin ular "
                    "savolga javob emas. To'g'ri javob esa audioda "
                    "boshqacha aytilgan — shuning uchun uning "
                    "so'zlarini eshitmaysiz."))
                order += 1
    return out


def seed_ielts3(db):
    """Idempotent: (kind, prompt+say) bo'yicha yo'qlari qo'shiladi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_listen_v3"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            pl = json.loads(p)
            have.add((k, pl.get("prompt"), pl.get("say")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain in build_rows():
        key = (kind, payload.get("prompt"), payload.get("say"))
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
    _seed_mark(db, "ielts_listen_v3")
    return made
