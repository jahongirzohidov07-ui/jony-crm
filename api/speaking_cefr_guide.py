# -*- coding: utf-8 -*-
"""MULTILEVEL SPEAKING — SHABLON, NAMUNA VA AVTOMAT TAHLIL.

Jahongir: "unga javob berish uchun templatelar, samplelar bo'lsin
bergan javobini oxirida tahlili bo'lsin."

VAQT VA SO'Z SONI — ENG MUHIM MASHQ. O'quvchi 30 soniyada nechta
so'z aytish kerakligini bilmaydi: kimdir 12 so'z aytib jim qoladi,
kimdir gapini tugatolmaydi. O'rtacha ravon nutq daqiqasiga 130 ta
so'z. Demak:
    30 soniya  -> 55-75 so'z
    45 soniya  -> 85-110 so'z
    2 daqiqa   -> 230-290 so'z
Shu raqamlar shablonlarga ham, avtomat tahlilga ham asos qilib
olindi.

AVTOMAT TAHLIL NEGA KERAK. AI baho har doim ishlamasligi mumkin
(kalit, tarmoq, limit). Lekin rasmiy RATING SCALE dagi mezonlarning
bir qismini matematik o'lchash MUMKIN:
  - nutq tezligi va uzunligi        -> "frequent pausing" mezoni
  - bog'lovchilar soni              -> "cohesive devices" mezoni
  - murakkab konstruksiyalar        -> "complex structures" mezoni
  - lug'at xilma-xilligi            -> "range of vocabulary" mezoni
  - savol qamrovi                   -> "responses ... are on topic"
  - 3-qismda FOR va AGAINST balansi -> 3 va 4 ball orasidagi FARQ
Shuning uchun AI bo'lmasa ham taxminiy ball chiqadi va o'quvchi
javobsiz qolmaydi. AI ishlaganda esa uning bahosi ustun turadi.
"""
import re as _re
import collections as _c

WPM = 130          # o'rtacha ravon nutq tezligi


def target_words(seconds: int) -> list[int]:
    """Berilgan vaqtga mos so'z soni oralig'i.

    2026-08-26 TUZATISH. Avval ikki xil me'yor bor edi: shablonda
    qo'lda yozilgan raqam (45 soniya -> 85-110) va tahlilchining
    o'z hisobi (45 soniya -> 60-89). Ikkalasi bir-biriga zid edi
    va namunaviy javob "juda uzun" ham, "normal" ham deb
    baholanardi. Endi ikkalasi ham SHU funksiyadan oladi.

    Asos: ravon nutq ~130 so'z/daqiqa. Yaxshi javob shu me'yorning
    85-115% i orasida bo'ladi.
    """
    base = WPM * max(1, int(seconds)) / 60
    return [int(base * 0.85), int(base * 1.15)]

# =================================================================
#  SHABLONLAR VA NAMUNALAR
# =================================================================

GUIDE: dict[str, dict] = {

    # ---------------------------------------------------------
    "p11": {
        "title": "Part 1.1 — shaxsiy savollar",
        "idea": "Bu qismda hech qanday chuqur fikr talab "
                "qilinmaydi. Xato — jim qolish yoki bir og'iz "
                "javob berish. 30 soniya uzoq: to'g'ridan-to'g'ri "
                "javob bering, keyin IKKI tafsilot qo'shing va "
                "bitta sabab bilan yakunlang.",
        "seconds": 30,
        "template": [
            {"t": "0-5 soniya", "name": "To'g'ridan-to'g'ri javob",
             "how": "Savolni takrorlamang. Darrov javob bering.",
             "eg": "My best friend is called Sardor."},
            {"t": "5-20 soniya", "name": "Ikki tafsilot",
             "how": "Kim / qachon / qayerda / qanday. Aniq bo'lsin.",
             "eg": "We met at school about ten years ago, and now "
                   "we study at the same university."},
            {"t": "20-30 soniya", "name": "Sabab yoki his",
             "how": "'because' yoki 'what I like about...' bilan "
                    "bitta sabab qo'shing — bu sizni A2 dan B1 ga "
                    "ko'taradi.",
             "eg": "What I really like about him is that he always "
                   "tells me the truth, even when it is not "
                   "pleasant."},
        ],
        "phrases": {
            "Boshlash": ["Well, ...", "Actually, ...",
                         "To be honest, ...", "I'd say ..."],
            "Tafsilot qo'shish": ["We usually ...", "For example, ...",
                                  "Most of the time, ...",
                                  "What's more, ..."],
            "Sabab": ["because ...", "The reason is that ...",
                      "That's why ...", "What I like about it is ..."],
            "Vaqt yetmasa": ["... but the main thing is ...",
                             "In short, ..."],
        },
        "sample_q": "Please tell me about your best friend.",
        "sample": "My best friend is called Sardor. We met at school "
                  "when we were eight, and we still see each other "
                  "every week. He studies "
                  "engineering, and for example last month he helped me "
                  "repair my laptop. At the "
                  "weekend we play football together, although he is "
                  "much better than me. What I like most is that he "
                  "always tells me the "
                  "truth, because a friend who only agrees with you "
                  "is not really helping.",
        "notes": [
            "Savol takrorlanmadi — birinchi gapdanoq javob.",
            "Aniq tafsilot: sakkiz yosh, har hafta, muhandislik, "
            "futbol. Umumiy gap emas.",
            "Oxirgi gap SABAB — aynan shu B1 belgisi.",
        ],
        "avoid": ["Bir og'iz javob: 'My best friend is Sardor.' "
                  "va jimlik",
                  "Savolni takrorlash: 'You asked me about my best "
                  "friend, so my best friend is...' — vaqt ketadi",
                  "Yodlangan matn o'qish — bu 0 ball degani"],
    },

    # ---------------------------------------------------------
    "p12": {
        "title": "Part 1.2 — ikki rasmni taqqoslash",
        "idea": "4-savolda (45 soniya) IKKALA rasm ham tilga "
                "olinishi SHART. Faqat bittasini tasvirlash — eng "
                "ko'p uchraydigan xato. 5 va 6-savollarda (30 "
                "soniyadan) fikr + sabab + misol.",
        "seconds": 45,
        "template": [
            {"t": "4-savol, 0-10 s", "name": "Umumiy bog'lanish",
             "how": "Ikkala rasmni bitta jumlada bog'lang.",
             "eg": "Both pictures show different ways of getting "
                   "around a city."},
            {"t": "4-savol, 10-25 s", "name": "Birinchi rasm",
             "how": "In the first picture ... — kim, nima qilyapti, "
                    "qanday ko'rinyapti.",
             "eg": "In the first picture, a group of people are "
                   "walking along a pavement on a sunny morning."},
            {"t": "4-savol, 25-40 s", "name": "Ikkinchi rasm",
             "how": "In the second picture ... + solishtirish "
                    "so'zi (whereas, while, on the other hand).",
             "eg": "In the second one, however, the road is full of "
                   "cars in a traffic jam, and most drivers seem to "
                   "be alone."},
            {"t": "4-savol, 40-45 s", "name": "Asosiy farq",
             "how": "The main difference is ...",
             "eg": "The main difference is that one looks relaxed "
                   "and the other looks stressful."},
            {"t": "5-6-savol, 30 s", "name": "Fikr + sabab + misol",
             "how": "I think ... because ... For example, ...",
             "eg": "I think walking is healthier because you move "
                   "your whole body. For example, my father walks to "
                   "work every day and he is fitter than me."},
        ],
        "phrases": {
            "Ikkalasini bog'lash": ["Both pictures show ...",
                                    "These two photos are connected "
                                    "by ...",
                                    "What they have in common is ..."],
            "Rasmni tasvirlash": ["In the first picture, ...",
                                  "In the second one, ...",
                                  "It looks like ...",
                                  "I can see ... in the background."],
            "Solishtirish": ["whereas", "while", "on the other hand",
                             "unlike the first picture",
                             "The main difference is that ..."],
            "Taxmin": ["They seem to be ...", "It's probably ...",
                       "I'd guess that ..."],
            "Fikr va sabab": ["I think ... because ...",
                              "One clear advantage is that ...",
                              "For example, ...",
                              "In my experience, ..."],
        },
        "sample_q": "What do you see in these pictures?",
        "sample": "Both pictures show different ways of moving around "
                  "a city. In the first picture, a group of people "
                  "are walking along a pavement on a bright morning; "
                  "they look relaxed and one woman is pushing a pram. "
                  "In the second one, however, the road is completely "
                  "full of cars in a traffic jam, and most of the "
                  "drivers seem to be sitting alone. The main "
                  "difference for me is the atmosphere: the first "
                  "looks calm and social, whereas the second looks "
                  "slow and rather frustrating. In addition, the "
                  "walkers are clearly in no hurry, whereas the "
                  "drivers, who are probably late for work, feel "
                  "that the same journey is stressful.",
        "notes": [
            "Birinchi gap ikkala rasmni BOG'LADI — shundan keyin "
            "tasvirlash boshlandi.",
            "'however' va 'whereas' — solishtirish bog'lovchilari. "
            "Rasmiy mezonda aynan shular sanaladi.",
            "Oxirida ASOSIY FARQ aytildi — javob tugallangan "
            "ko'rinadi.",
        ],
        "avoid": ["Faqat bitta rasmni tasvirlash",
                  "Ro'yxat qilib sanash: 'I see a man. I see a car. "
                  "I see a tree.'",
                  "Rasmda yo'q narsani o'ylab topish"],
    },

    # ---------------------------------------------------------
    "p2": {
        "title": "Part 2 — rasm va uchta savol",
        "idea": "Eng ko'p ball shu yerda yo'qoladi: o'quvchi "
                "birinchi savolga uzoq javob berib, qolgan "
                "ikkitasiga vaqt qoldirmaydi. Rasmiy mezon aniq "
                "aytadi — UCHALA savolga javob berilsa 4-5 ball, "
                "ikkitasiga 3 ball, bittasiga 1 ball. Shuning "
                "uchun vaqtni uchga bo'ling: taxminan 40 soniyadan.",
        "seconds": 120,
        "template": [
            {"t": "Tayyorgarlik 60 s", "name": "Uchta so'z yozing",
             "how": "Har savol uchun BITTA kalit so'z o'ylang. "
                    "To'liq javob yozishga urinmang — ulgurmaysiz.",
             "eg": "1) university  2) independence  3) family+money"},
            {"t": "0-40 s", "name": "1-savol: shaxsiy voqea",
             "how": "Aniq voqea ayting: qachon, qayerda, nima. "
                    "Umumiy gap ball bermaydi.",
             "eg": "The most important decision I've made was "
                   "choosing to study in another city..."},
            {"t": "40-80 s", "name": "2-savol: ta'siri",
             "how": "'As a result...', 'It has changed...' — "
                    "natijani ayting.",
             "eg": "As a result, I had to learn to manage my own "
                   "money and time..."},
            {"t": "80-120 s", "name": "3-savol: umumiy fikr",
             "how": "Endi shaxsiydan UMUMIYga o'ting. Ikki omil "
                    "ayting va bittasini misol bilan asoslang.",
             "eg": "In general, I think two things affect people's "
                   "decisions most: money and the opinion of their "
                   "family..."},
        ],
        "phrases": {
            "Savoldan savolga o'tish": ["As for the second question, ...",
                                        "Moving on to how it affected "
                                        "me, ...",
                                        "And in more general terms, ..."],
            "Shaxsiy voqea": ["The most important ... I've made was ...",
                              "This happened when I was ...",
                              "At that time, I had to choose between "
                              "... and ..."],
            "Natija": ["As a result, ...", "Because of that decision, ...",
                       "It completely changed the way I ...",
                       "Looking back, it taught me that ..."],
            "Umumiy fikr": ["Generally speaking, ...",
                            "In most cases, people are influenced "
                            "by ...",
                            "I'd say the biggest factor is ...",
                            "It largely depends on ..."],
            "Vaqt tugayotganda": ["To sum up, ...",
                                  "So overall, ..."],
        },
        "sample_q": "Tell me about a critical decision you have made. "
                    "How has this decision influenced you and your "
                    "life? What factors have the highest impact on "
                    "the decisions people make?",
        "sample": "The most important decision I have ever made was "
                  "leaving my home town to study in the capital. I "
                  "was seventeen, I had a place at a local college, "
                  "and my parents were fairly clear that they wanted "
                  "me to stay. I chose to go anyway.\n\n"
                  "As for how it has influenced me, the effect was "
                  "much bigger than I expected. Within a few months "
                  "I had to manage my own money, cook for myself and "
                  "solve problems that my mother used to solve in "
                  "five minutes. I became far more independent, "
                  "although I also felt lonely for the first year. "
                  "Looking back, it taught me that discomfort and "
                  "growth usually arrive together.\n\n"
                  "In more general terms, I would say two factors "
                  "influence people's decisions most strongly. The "
                  "first is money, because it quietly removes some "
                  "options before you even consider them. The second, "
                  "and in our culture probably the stronger one, is "
                  "the opinion of the family. Many of my friends "
                  "chose their university not because of the "
                  "programme, but because their parents felt "
                  "comfortable with the city. In my own case, "
                  "if my parents had insisted a little more "
                  "firmly, I would probably have stayed at home, "
                  "and my life today would look completely "
                  "different. That is why I think young people "
                  "should be encouraged to weigh these pressures "
                  "consciously rather than simply follow them, "
                  "because a decision you have thought about "
                  "yourself is far easier to live with "
                  "afterwards, even when it turns out to be the "
                  "wrong one.",
        "notes": [
            "Uch abzats — uch savol. Vaqt teng taqsimlangan.",
            "Har o'tishda ochiq belgi bor: 'As for how it has "
            "influenced me', 'In more general terms'. Imtihonchi "
            "qaysi savolga javob berilayotganini adashtirmaydi.",
            "3-savolda IKKI omil aytildi va har biri "
            "asoslandi — B2 ning 'analyse and justify' talabi.",
            "'although', 'because', 'while' — murakkab tuzilmalar.",
        ],
        "avoid": ["Birinchi savolga 90 soniya sarflash",
                  "Rasmni tasvirlash — bu TALAB QILINMAYDI",
                  "Uchinchi savolni ham shaxsiy misol bilan "
                  "tugatish (u UMUMIY savol)"],
    },

    # ---------------------------------------------------------
    "p3": {
        "title": "Part 3 — tarafdor va qarshi dalillar",
        "idea": "Rasmiy mezonda 3 va 4 ball orasidagi farq ANIQ "
                "yozilgan: faqat BITTA ro'yxatdan gapirsangiz — 3 "
                "ball (Lower B2), IKKALA ro'yxatdan gapirsangiz — 4 "
                "ball va undan yuqori. Ya'ni muvozanat — bu uslub "
                "emas, ball. Har ro'yxatdan IKKITA band tanlang.",
        "seconds": 120,
        "template": [
            {"t": "Tayyorgarlik 60 s", "name": "2+2 band belgilang",
             "how": "FOR dan ikkita, AGAINST dan ikkita band "
                    "tanlang — o'zingizga eng oson asoslanadiganini. "
                    "Hammasini qamrashga urinmang.",
             "eg": "FOR: 1 va 3 · AGAINST: 2 va 3"},
            {"t": "0-15 s", "name": "Mavzuni ochish",
             "how": "Mavzuni O'Z so'zingiz bilan qayta ayting va "
                    "ikki tomon borligini bildiring.",
             "eg": "The question of whether ordinary citizens should "
                   "be allowed to carry guns divides opinion sharply."},
            {"t": "15-60 s", "name": "TARAFDOR — 2 band",
             "how": "Har band uchun: dalil + NEGA. Faqat o'qib "
                    "chiqish 1 ball degani.",
             "eg": "Those in favour argue, first of all, that ... "
                   "Secondly, they point out that ..."},
            {"t": "60-105 s", "name": "QARSHI — 2 band",
             "how": "'On the other hand' bilan aniq o'ting.",
             "eg": "On the other hand, opponents make two strong "
                   "points..."},
            {"t": "105-120 s", "name": "Muvozanatli xulosa",
             "how": "Ikki tomonni tortib, o'z pozitsiyangizni "
                    "ayting. Yangi dalil qo'shmang.",
             "eg": "On balance, I find the second set of arguments "
                   "more convincing, because ..."},
        ],
        "phrases": {
            "Ochish": ["This is a topic that divides opinion.",
                       "There are strong arguments on both sides of "
                       "this question.",
                       "Let me look at each side in turn."],
            "Tarafdor": ["Those in favour argue that ...",
                         "The strongest argument for this is ...",
                         "Supporters would point out that ...",
                         "It is certainly true that ..."],
            "O'tish": ["On the other hand, ...",
                       "Having said that, ...",
                       "The opposite view is equally strong.",
                       "However, critics raise two serious concerns."],
            "Qarshi": ["Opponents argue that ...",
                       "The main objection is that ...",
                       "A serious counter-argument is that ...",
                       "This overlooks the fact that ..."],
            "Xulosa": ["On balance, ...", "Weighing both sides, ...",
                       "All things considered, I would argue that ...",
                       "While both views have merit, ..."],
        },
        "sample_q": "Citizens should be allowed to carry personal "
                    "guns. (FOR: protection, prevents burglary, "
                    "hunting · AGAINST: used in crime, fewer guns "
                    "lower murder rate, military guns useless for "
                    "hunting)",
        "sample": "The question of whether ordinary citizens should "
                  "be allowed to carry guns divides opinion very "
                  "sharply, and I can see the logic on both "
                  "sides.\n\n"
                  "Those in favour argue, first of all, that a "
                  "weapon allows people to protect themselves. In "
                  "areas where the police may take twenty minutes to "
                  "arrive, that argument is difficult to dismiss "
                  "completely. Their second point is that armed "
                  "households deter burglary, because a criminal has "
                  "no way of knowing which home is armed and "
                  "therefore avoids the risk altogether.\n\n"
                  "On the other hand, opponents raise two objections "
                  "that I find considerably stronger. The first is "
                  "simply that guns are designed to kill, and the "
                  "more of them there are in circulation, the more "
                  "often they end up being used in ordinary "
                  "arguments rather than in self-defence. The second "
                  "is that countries which have reduced the number "
                  "of privately owned weapons have generally seen "
                  "their murder rates fall, which suggests that "
                  "availability itself is part of the problem.\n\n"
                  "On balance, then, while I accept that the wish to "
                  "protect one's family is entirely reasonable, I "
                  "would argue that the risk to society as a whole "
                  "clearly outweighs the benefit to the "
                  "individual. A household may feel safer with a "
                  "weapon in the drawer, but the same weapon is "
                  "available during a family argument, and it is "
                  "available to a child who finds it. For that "
                  "reason I would support strict licensing rather "
                  "than a general right to carry, since that "
                  "approach keeps guns available to hunters and "
                  "sportspeople while removing them from ordinary "
                  "streets.",
        "notes": [
            "IKKALA ro'yxatdan ikkitadan band olindi — 4 ball va "
            "undan yuqori uchun shart aynan shu.",
            "Bandlar O'QILMADI, qayta ifodalandi va har biriga "
            "SABAB qo'shildi.",
            "'first of all', 'their second point', 'on the other "
            "hand', 'on balance' — boy bog'lovchilar (C1 mezoni).",
            "Xulosada qarshi tomon tan olindi ('while I accept "
            "that...') — bu C1 ning belgisi.",
        ],
        "avoid": ["Faqat bir tomondan gapirish — 3 balldan "
                  "oshmaydi",
                  "Ekrandagi bandlarni o'qib chiqish — 1 ball",
                  "To'rttala banddan ko'p olishga urinish — "
                  "hech biri asoslanmay qoladi"],
    },
}

# So'z me'yori QO'LDA yozilmaydi — vaqtdan hisoblanadi. Shunda
# shablon va tahlilchi hech qachon bir-biriga zid bo'lolmaydi.
for _g in GUIDE.values():
    _g["words"] = target_words(_g["seconds"])


# =================================================================
#  AVTOMAT TAHLIL
# =================================================================

LINKERS = [
    "because", "although", "however", "therefore", "moreover",
    "furthermore", "on the other hand", "for example", "for instance",
    "in addition", "as a result", "whereas", "while", "besides",
    "in contrast", "firstly", "first of all", "secondly", "finally",
    "on balance", "in my opinion", "that is why", "such as",
    "in fact", "actually", "so that", "even though", "despite",
    "nevertheless", "to sum up", "overall", "in short", "since",
    "unlike", "similarly", "having said that", "what is more",
]

COMPLEX = [
    r"\bif\s+\w+\s+(would|had|were)\b", r"\bwould have\b",
    r"\bhad\s+\w+ed\b", r"\bwhich\b", r"\bwho\b", r"\bwhose\b",
    r"\bwhereas\b", r"\balthough\b", r"\beven though\b",
    r"\bhave\s+\w+ed\b", r"\bhas\s+\w+ed\b", r"\bbeen\s+\w+ing\b",
    r"\bnot only\b", r"\brather than\b", r"\bin order to\b",
    r"\bthe more\b", r"\bused to\b", r"\bwould rather\b",
]

FILLERS = ["um", "uh", "erm", "like like", "you know", "i mean",
           "how to say", "how you say"]

STOP = {"the", "a", "an", "and", "or", "but", "is", "are", "was",
        "were", "be", "been", "being", "to", "of", "in", "on", "at",
        "for", "with", "i", "you", "he", "she", "it", "we", "they",
        "my", "your", "his", "her", "its", "our", "their", "this",
        "that", "these", "those", "have", "has", "had", "do", "does",
        "did", "will", "would", "can", "could", "should", "so",
        "very", "just", "also", "there", "them", "then", "as", "if",
        "not", "no", "yes", "me", "him", "us", "what", "which"}


def words_of(t: str) -> list[str]:
    return _re.findall(r"[A-Za-z][A-Za-z'’-]*", t or "")


def _content(ws):
    return [w.lower() for w in ws if w.lower() not in STOP and len(w) > 2]


def _covered(text: str, question: str) -> bool:
    """Javob shu savolga tegishlimi — kalit so'zlar kesishuvi."""
    q = set(_content(words_of(question)))
    a = set(_content(words_of(text)))
    if not q:
        return True
    hit = len(q & a)
    return hit >= max(1, min(2, len(q) // 4))


def _stem(w: str) -> str:
    """Sodda o'zak: birinchi 5 harf.

    'reduce' va 'reduced', 'rate' va 'rates', 'crime' va 'crimes'
    bir xil deb qaraladi. To'liq morfologiya emas, lekin bandni
    o'z so'zi bilan qayta aytgan o'quvchini tanish uchun yetarli.
    """
    return w[:5]


def _side_hits(items: list, other: list, text: str) -> int:
    """Ro'yxatdagi nechta band NUTQDA ishlatilgan.

    2026-08-26 TUZATISH. Avval bandning HAR QANDAY so'zi hisobga
    olinardi va "guns" so'zi ikkala ro'yxatda ham borligi uchun
    faqat tarafdor gapirgan o'quvchi ham "qarshi tomonni yoritdi"
    deb belgilanardi. Test shu xatoni tutdi.

    Endi ikki qoida:
      1) Ikkala ro'yxatda YOKI mavzuda uchraydigan so'zlar
         hisobga olinmaydi — faqat shu bandga XOS so'zlar.
      2) Band "ishlatilgan" deyish uchun kamida IKKI xos so'z
         kerak. Bitta tasodifiy so'z yetarli emas.
    """
    other_w = {_stem(w) for it in other for w in _content(words_of(it))}
    said = {_stem(w) for w in _content(words_of(text))}
    used = 0
    for it in items:
        own = {_stem(w) for w in _content(words_of(it))} - other_w
        if len(own & said) >= 2:
            used += 1
    return used


def analyse(text: str, seconds: int, questions: list[str] | None = None,
            for_list: list[str] | None = None,
            against_list: list[str] | None = None) -> dict:
    """Transkriptni rasmiy mezonlarga yaqin ko'rsatkichlarga aylantiradi."""
    text = (text or "").strip()
    ws = words_of(text)
    n = len(ws)
    low = " " + text.lower() + " "
    secs = max(1, int(seconds or 30))
    target_lo, target_hi = target_words(secs)
    wpm = round(n / (secs / 60)) if n else 0

    links = sorted({l for l in LINKERS if l in low})
    cx = sorted({p for p in COMPLEX if _re.search(p, low)})
    fill = [f for f in FILLERS if f in low]
    cw = _content(ws)
    variety = round(len(set(cw)) / len(cw), 2) if cw else 0.0
    rep = ""
    if cw:
        c = _c.Counter(cw).most_common(1)[0]
        if c[1] >= max(4, n // 25):
            rep = f"{c[0]} ({c[1]} marta)"

    covered, missed = [], []
    for q in (questions or []):
        (covered if _covered(text, q) else missed).append(q)

    bal = None
    if for_list is not None and against_list is not None:
        bal = {"for": _side_hits(for_list, against_list, text),
               "against": _side_hits(against_list, for_list, text)}

    return {"words": n, "seconds": secs, "wpm": wpm,
            "target": [target_lo, target_hi],
            "linkers": links, "linker_count": len(links),
            "complex": len(cx), "fillers": fill,
            "variety": variety, "repeat": rep,
            "covered": len(covered), "missed": missed,
            "asked": len(questions or []), "balance": bal}


def estimate_point(block: str, a: dict) -> int:
    """AI ishlamaganda taxminiy ball.

    2026-08-26 TUZATISH. Avval hamma blokka BIR XIL talab
    qo'yilgan edi ("kamida 3 bog'lovchi va 3 murakkab tuzilma"),
    natijada namunaviy B1 javobi 3 ball olib qolgan edi. Bu
    metodik jihatdan xato: rasmiy mezonda Higher B1 (4 ball)
    uchun murakkab tuzilma TALAB QILINMAYDI — u yerda aynan
    "Simple grammatical structures are used correctly" deb
    yozilgan. Endi har blok o'z darajasining talabiga qarab
    baholanadi:
        q1_3 (A2)  -> savol qamrovi + hajm
        q4_6 (B1)  -> + kamida 2 bog'lovchi
        q7   (B2)  -> + 3 bog'lovchi va 2 murakkab tuzilma
        q8   (C1)  -> + FOR/AGAINST muvozanati

    Ataylab EHTIYOTKOR: eng yuqori ball (5 yoki 6 — "daraja o'zidan
    ham baland") avtomat qo'yilmaydi, chunki buni faqat inson yoki
    AI ayta oladi. Maqsad — o'quvchi hech qachon bahosiz
    qolmasligi.
    """
    n = a["words"]
    lo = a["target"][0]
    if not n:
        return 0
    enough = n >= lo * 0.7
    ok_len = n >= lo
    L, C = a["linker_count"], a["complex"]

    # ---- 3-qism: muvozanat hal qiladi ----
    if block == "q8" and a.get("balance") is not None:
        b = a["balance"]
        both = b["for"] >= 1 and b["against"] >= 1
        if both and ok_len and L >= 4 and C >= 3:
            return 5
        if both and enough:
            return 4
        if (b["for"] + b["against"]) >= 1 and enough:
            return 3
        if enough:
            return 2
        return 1

    asked = max(1, a["asked"] or 1)
    cov = a["covered"]
    full = cov >= asked

    if block == "q1_3":
        need4 = ok_len
    elif block == "q4_6":
        need4 = ok_len and L >= 2
    else:                                   # q7 va balanssiz q8
        need4 = ok_len and L >= 3 and C >= 2

    if full and need4:
        return 4
    if full and enough:
        return 3
    if cov >= max(1, asked - 1) and enough:
        return 3 if asked > 1 else 2
    if cov >= 1 and enough:
        return 2
    return 1


def tips(a: dict, block: str) -> list[dict]:
    """O'quvchiga tushunarli, aniq maslahatlar."""
    out = []
    lo, hi = a["target"]
    if a["words"] == 0:
        return [{"ok": False, "label": "Nutq",
                 "detail": "Matn topilmadi. Mikrofonga yaqinroq va "
                           "balandroq gapiring."}]
    if a["words"] < lo:
        out.append({"ok": False, "label": "Nutq hajmi",
                    "detail": f"{a['words']} so'z aytdingiz, "
                              f"{a['seconds']} soniyada {lo}-{hi} so'z "
                              f"kutiladi. Vaqt qolganda jim qolish — "
                              f"'frequent pausing' mezoni bo'yicha "
                              f"ball tushiradi."})
    elif a["words"] > hi * 1.15:
        out.append({"ok": None, "label": "Nutq hajmi",
                    "detail": f"{a['words']} so'z — juda tez "
                              f"gapiryapsiz ({a['wpm']} so'z/daq). "
                              f"Sekinroq gapirsangiz talaffuz "
                              f"aniqroq bo'ladi."})
    else:
        out.append({"ok": True, "label": "Nutq hajmi",
                    "detail": f"{a['words']} so'z ({a['wpm']} "
                              f"so'z/daqiqa) — vaqtga mos."})

    if a["missed"]:
        out.append({"ok": False, "label": "Savol qamrovi",
                    "detail": "Bu savol(lar)ga javob topilmadi: "
                              + "; ".join(q[:60] for q in a["missed"])
                              + ". Rasmiy mezonda ball aynan nechta "
                                "savol yoritilganiga qarab qo'yiladi."})
    elif a["asked"]:
        out.append({"ok": True, "label": "Savol qamrovi",
                    "detail": f"Hamma {a['asked']} savol yoritilgan."})

    if a["balance"] is not None:
        b = a["balance"]
        if b["for"] and b["against"]:
            out.append({"ok": True, "label": "Muvozanat",
                        "detail": f"FOR dan {b['for']} ta, AGAINST dan "
                                  f"{b['against']} ta band ishlatilgan "
                                  f"— 4 ball va undan yuqori uchun "
                                  f"shart bajarildi."})
        else:
            yoq = "AGAINST" if b["for"] else "FOR"
            out.append({"ok": False, "label": "Muvozanat",
                        "detail": f"{yoq} ro'yxatidan hech qanday band "
                                  f"ishlatilmagan. Rasmiy mezon aniq: "
                                  f"faqat bitta ro'yxat = 3 ball "
                                  f"(Lower B2). Ikkalasi = 4 ball."})

    if a["linker_count"] >= 4:
        out.append({"ok": True, "label": "Bog'lovchilar",
                    "detail": f"{a['linker_count']} xil bog'lovchi: "
                              + ", ".join(a["linkers"][:6])})
    else:
        out.append({"ok": False, "label": "Bog'lovchilar",
                    "detail": f"Faqat {a['linker_count']} xil "
                              f"bog'lovchi. Rasmiy mezonda 'cohesive "
                              f"devices' alohida sanaladi. Qo'shing: "
                              f"however, although, as a result, for "
                              f"example, on the other hand."})

    if a["complex"] >= 3:
        out.append({"ok": True, "label": "Murakkab tuzilmalar",
                    "detail": f"{a['complex']} xil murakkab "
                              f"konstruksiya ishlatilgan."})
    else:
        out.append({"ok": False, "label": "Murakkab tuzilmalar",
                    "detail": "Gaplar asosan sodda. B2 va C1 uchun "
                              "murakkab tuzilma kerak: which/who "
                              "ergash gaplari, Present Perfect, "
                              "shart gaplar, 'not only ... but also'."})

    if a["variety"] and a["variety"] < 0.55:
        out.append({"ok": None, "label": "Lug'at xilma-xilligi",
                    "detail": f"Mazmunli so'zlarning {int(a['variety']*100)}%"
                              f" i noyob. Sinonim ishlating."})
    if a["repeat"]:
        out.append({"ok": None, "label": "Takrorlanish",
                    "detail": f"Eng ko'p takrorlangan so'z: "
                              f"{a['repeat']}."})
    if a["fillers"]:
        out.append({"ok": None, "label": "To'ldiruvchi so'zlar",
                    "detail": "Eshitildi: " + ", ".join(a["fillers"])
                              + ". Ularning o'rniga bir soniya jim "
                                "turing — bu tabiiyroq eshitiladi."})
    return out
