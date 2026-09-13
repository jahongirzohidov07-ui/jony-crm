# -*- coding: utf-8 -*-
"""IELTS READING — SENTENCE COMPLETION (2026-08-26).

Jahongir: "keyingisi sentence completion bu shundan ham 100ta" —
va namuna sifatida "READING #20. The honey badger" (Questions 1-8,
NO MORE THAN TWO WORDS) yubordi.

TUZILISHI. 20 ta matn, jami 100 bo'shliq, daraja 1..20:
  1-6    — qisqa matn, gap matndagi jumlaga deyarli aynan mos;
  7-15   — matn uzayadi, gap bilan matn orasidagi paraffraz
           uzoqlashadi;
  16     — "READING #20. The honey badger" (Jahongirning namunasi,
           8 ta bo'shliq, kitobdagi tartibda);
  17-20  — eng qiyini: javob jumlaning boshida yoki o'rtasida,
           chalg'ituvchi sonlar ko'p.

BU TURNING O'ZIGA XOSLIGI. Summary Completion butun matnning
xulosasini to'ldiradi, Sentence Completion esa ALOHIDA gaplarni —
ular bir-biri bilan bog'lanmagan, lekin MATN TARTIBIDA keladi. Ikki
narsa bir vaqtda to'g'ri bo'lishi kerak:
  1) ma'no — javob matndan olingan bo'lsin;
  2) grammatika — gapga to'g'ri tushsin (birlik/ko'plik, fe'l
     shakli, artikl).
Ko'p o'quvchi ma'nosi to'g'ri, lekin shakli noto'g'ri so'z yozib ball
yo'qotadi.

JAVOB CHEGARASI. Barcha javoblar 2 so'zdan oshmaydi va matnda AYNAN
shu shaklda uchraydi — o'zidan so'z o'ylab topilmaydi.
"""

SKILL = "ielts_reading"
KIND = "read_sentence"
GAP = "………"
INSTR = ("Complete the sentences. Write NO MORE THAN TWO WORDS "
         "from the passage for each answer.")


# =====================================================================
#  QOIDALAR
# =====================================================================
SENTENCE_TIPS = [
    ("Sentence Completion nima",
     "Har gapda bitta bo'shliq bor. Uni MATNDAGI so'z bilan "
     "to'ldirasiz — 2 so'zdan oshmasligi kerak. Gaplar bir-biriga "
     "bog'liq emas, lekin matn tartibida keladi.",
     "Matn: «They are instantly recognisable by grey and white "
     "stripes»\nGap: The pattern and colours on the badger's back "
     "make it ……… .\nJavob: instantly recognisable"),
    ("Avval GRAMMATIKANI aniqlang",
     "Bo'shliqqa qarab, u yerga nima turishi kerakligini oldindan "
     "ayting: ot? sifat? son? fe'l? Ko'plikmi yoki birlik? "
     "«a ………» dan keyin birlik ot keladi, «are ………» dan keyin "
     "sifat yoki ko'plik. Shu bir qadam xatolarning yarmini "
     "yo'q qiladi.", ""),
    ("So'z SHAKLINI o'zgartirmang",
     "Matnda «recognisable» bo'lsa, «recognise» deb yozsangiz "
     "noto'g'ri. Javob matndan KO'CHIRILADI. Agar ko'chirgan "
     "so'zingiz gapga grammatik jihatdan tushmasa — demak javob "
     "noto'g'ri, boshqa joyga qarang.", ""),
    ("So'zlarni sanang",
     "«NO MORE THAN TWO WORDS» — uch so'z yozsangiz, ma'nosi to'g'ri "
     "bo'lsa ham nol ball. Defisli so'z («meat-based») bitta "
     "sanaladi, «sense of smell» esa uchta.", ""),
    ("Gaplar MATN TARTIBIDA",
     "1-gapning javobi 2-gapnikidan oldin turadi. 4-gapni topolmay "
     "qolsangiz, 3 va 5-javoblar orasini qarang — javob o'sha "
     "yerda.", ""),
    ("Bo'shliq atrofidagi so'zlarni belgilang",
     "Bo'shliqning o'zi emas, uning YONIDAGI so'zlar matndan qidirish "
     "kalitidir. Ular esa matnda parafraz bo'lib turadi.",
     "Gap: «Honey badgers will attack ……… if they need to protect "
     "themselves.»\nMatn: «Even humans are not safe from a honey "
     "badger if it thinks the human will attack or harm it.»\n"
     "«protect themselves» = «will attack or harm it» -> humans"),
    ("Bo'shliq gap boshida ham bo'ladi",
     "«……… form the biggest part of the diet» — bunda javob EGA, "
     "ya'ni ko'plik ot kerak. Bo'shliq oxirida bo'lishi shart emas.",
     ""),
    ("Ikki so'zli javoblarga tayyor turing",
     "«small creatures», «working relationship», «special traps» — "
     "sifat + ot juftligi eng ko'p uchraydigan ikki so'zli javob.",
     ""),
]


def P(level, title, text, items):
    return {"level": level, "title": title, "text": text,
            "items": items}


PASSAGES = []

# ============== 1-6: qisqa matn, javob deyarli aynan ==============
PASSAGES.append(P(
    1, "THE CITY LIBRARY",
    "The city library opened in 1962. It has more than 90,000 books "
    "and a special room for children on the ground floor. Members "
    "can borrow six items at a time for three weeks. The library "
    "also runs free computer classes for older people every "
    "Tuesday. Parking is free for the first hour.",
    [("The library began operating in " + GAP + ".", "1962", "",
      "The city library opened in 1962", ""),
     ("The children's room is on the " + GAP + ".", "ground floor",
      "", "a special room for children on the ground floor", ""),
     ("Members are allowed to take out " + GAP + " items at once.",
      "six", "", "Members can borrow six items at a time", ""),
     ("The computer classes are intended for " + GAP + ".",
      "older people", "",
      "free computer classes for older people", ""),
     ("Drivers pay nothing for the first " + GAP + ".", "hour", "",
      "Parking is free for the first hour", "")],
))

PASSAGES.append(P(
    2, "A NEW BAKERY",
    "Nodira opened her bakery in a former shoe shop two years ago. "
    "She bakes bread at four in the morning and sells out by noon "
    "most days. Her best-selling item is a walnut cake made from "
    "her grandmother's recipe. She now employs three people and "
    "plans to open a second shop next spring.",
    [("The building was previously a " + GAP + ".", "shoe shop", "",
      "opened her bakery in a former shoe shop", ""),
     ("Bread is baked at " + GAP + " each morning.", "four", "",
      "She bakes bread at four in the morning", ""),
     ("The most popular product is a " + GAP + ".", "walnut cake",
      "", "Her best-selling item is a walnut cake", ""),
     ("The walnut cake is baked using her " + GAP + ".",
      "grandmother's recipe", "",
      "made from her grandmother's recipe", ""),
     ("Another shop is planned for next " + GAP + ".", "spring", "",
      "plans to open a second shop next spring", "")],
))

PASSAGES.append(P(
    3, "THE MOUNTAIN PATH",
    "The path to Chimyon lake is eleven kilometres long and takes "
    "about four hours to walk. Most of the climb happens in the "
    "first section, so the second half feels much easier. Walkers "
    "should carry two litres of water, because there is no spring "
    "after the forest. The route is closed in winter because of "
    "ice.",
    [("The walk covers a distance of " + GAP + ".",
      "eleven kilometres", "",
      "The path to Chimyon lake is eleven kilometres long", ""),
     ("The whole journey lasts about " + GAP + ".", "four hours", "",
      "takes about four hours to walk", ""),
     ("The steepest part is the " + GAP + " section.", "first", "",
      "Most of the climb happens in the first section", ""),
     ("Walkers are advised to bring " + GAP + " of water.",
      "two litres", "", "should carry two litres of water", ""),
     ("The path is shut during " + GAP + ".", "winter", "",
      "The route is closed in winter", "")],
))

PASSAGES.append(P(
    4, "SCHOOL UNIFORM",
    "Our school changed its uniform in September. The new jumper is "
    "dark green instead of grey, and the tie has been removed "
    "completely. Parents were consulted through an online survey, "
    "and 78 per cent supported the change. The main reason given "
    "was cost: the new uniform is about 30 per cent cheaper. Shoes "
    "must still be black.",
    [("The uniform was changed in " + GAP + ".", "September", "",
      "Our school changed its uniform in September", ""),
     ("The jumper is now " + GAP + ".", "dark green", "",
      "The new jumper is dark green instead of grey", ""),
     ("The " + GAP + " is no longer part of the uniform.", "tie", "",
      "the tie has been removed completely", ""),
     ("Parents gave their opinion in an online " + GAP + ".",
      "survey", "", "Parents were consulted through an online "
      "survey", ""),
     ("The most important reason for the change was " + GAP + ".",
      "cost", "", "The main reason given was cost", "")],
))

PASSAGES.append(P(
    5, "THE OLD BRIDGE",
    "The stone bridge over the Zarafshon was built in 1854 and "
    "carried carts and horses for a hundred years. It was closed to "
    "traffic in 1958, when a wider concrete bridge opened nearby. "
    "The old bridge is now used by pedestrians and cyclists. "
    "Repairs to the eastern arch were finished last autumn.",
    [("The bridge was constructed in " + GAP + ".", "1854", "",
      "The stone bridge over the Zarafshon was built in 1854", ""),
     ("It stopped carrying vehicles in " + GAP + ".", "1958", "",
      "It was closed to traffic in 1958", ""),
     ("It was replaced by a " + GAP + " bridge.", "concrete", "",
      "when a wider concrete bridge opened nearby", ""),
     ("Today it is crossed by walkers and " + GAP + ".", "cyclists",
      "", "now used by pedestrians and cyclists", ""),
     ("The " + GAP + " arch has recently been repaired.", "eastern",
      "", "Repairs to the eastern arch were finished last autumn",
      "")],
))

PASSAGES.append(P(
    6, "THE VILLAGE DOCTOR",
    "Dr Aziza has worked in Chorbog' for nineteen years and knows "
    "almost every family. Her clinic opens at seven so that "
    "patients can be seen before work. Because the nearest hospital "
    "is 40 kilometres away, she also deals with emergencies. Her "
    "greatest difficulty is not medicine but paperwork, which takes "
    "up two days of every week.",
    [("Dr Aziza has served the village for " + GAP + ".",
      "nineteen years", "",
      "has worked in Chorbog' for nineteen years", ""),
     ("The clinic starts seeing patients at " + GAP + ".", "seven",
      "", "Her clinic opens at seven", ""),
     ("She treats emergencies herself because the hospital is " +
      GAP + " from the village.", "40 kilometres", "",
      "the nearest hospital is 40 kilometres away", ""),
     ("Her biggest problem is " + GAP + ", not medicine.",
      "paperwork", "",
      "Her greatest difficulty is not medicine but paperwork", ""),
     ("Paperwork occupies " + GAP + " of her working week.",
      "two days", "", "which takes up two days of every week", "")],
))

# ============ 7-15: uzunroq matn, uzoqroq paraffraz =============
PASSAGES.append(P(
    7, "WHY LEAVES CHANGE COLOUR",
    "Green leaves are green because of chlorophyll, the pigment "
    "that captures sunlight. Chlorophyll is unstable and has to be "
    "constantly rebuilt, which a tree can only afford while there "
    "is enough light and warmth. As the days shorten, production "
    "stops and the green fades, revealing yellow and orange "
    "pigments that were present all along.\n\n"
    "Red is different. It is manufactured fresh in autumn, and the "
    "reason is still argued about. One theory is that red pigments "
    "protect the leaf while the tree withdraws nutrients from it. "
    "Cold nights and bright days produce the strongest colours, "
    "which is why the display varies from year to year.",
    [("The green colour is produced by a pigment called " + GAP +
      ".", "chlorophyll", "",
      "Green leaves are green because of chlorophyll", ""),
     ("Chlorophyll is not stable and must be continually " + GAP +
      ".", "rebuilt", "",
      "Chlorophyll is unstable and has to be constantly rebuilt",
      ""),
     ("Yellow and orange pigments had been " + GAP +
      " in the leaf all along.", "present", "",
      "revealing yellow and orange pigments that were present all "
      "along", "Ya'ni ular paydo bo'lmaydi — shunchaki ko'rinadi."),
     ("Red pigments may " + GAP +
      " the leaf while nutrients are taken back.", "protect", "",
      "red pigments protect the leaf while the tree withdraws "
      "nutrients", ""),
     ("The brightest colours appear when the nights are " + GAP +
      ".", "cold", "",
      "Cold nights and bright days produce the strongest colours",
      "")],
))

PASSAGES.append(P(
    8, "THE FIRST PHOTOGRAPH",
    "The oldest surviving photograph was made by Joseph Nicephore "
    "Niepce in about 1826, from an upstairs window of his house in "
    "Burgundy. The exposure lasted at least eight hours, which is "
    "why sunlight appears to fall on both sides of the courtyard "
    "at once.\n\n"
    "Niepce used a polished pewter plate coated with bitumen, a "
    "kind of tar that hardens where light strikes it. The soft "
    "parts were then washed away, leaving the image behind. He "
    "called the process heliography, meaning sun writing. The plate "
    "was lost for decades and rediscovered in a London attic in "
    "1952.",
    [("The picture was taken from an " + GAP + " window.",
      "upstairs", "",
      "from an upstairs window of his house in Burgundy", ""),
     ("The image required an exposure of at least " + GAP + ".",
      "eight hours", "", "The exposure lasted at least eight hours",
      ""),
     ("The plate itself was made of polished " + GAP + ".",
      "pewter", "", "a polished pewter plate coated with bitumen",
      ""),
     ("Bitumen is a form of " + GAP + ".", "tar", "",
      "bitumen, a kind of tar that hardens where light strikes it",
      ""),
     ("The missing plate was found again in " + GAP + ".", "1952",
      "", "rediscovered in a London attic in 1952", "")],
))

PASSAGES.append(P(
    9, "THE HISTORY OF THE UMBRELLA",
    "Umbrellas are far older than raincoats. Carvings from Nineveh "
    "show servants holding one above an Assyrian king almost three "
    "thousand years ago, but there it was a shade against the sun "
    "and a sign of rank, not protection from rain.\n\n"
    "In Europe the object was for a long time thought suitable only "
    "for women. Jonas Hanway, a London merchant, carried one "
    "publicly for thirty years from the 1750s and was mocked in the "
    "street for it; cab drivers were especially hostile, since rain "
    "was good for trade. By the time he died the umbrella had "
    "become ordinary, and Londoners briefly called it a hanway.\n\n"
    "The modern frame dates from 1852, when Samuel Fox replaced "
    "whalebone ribs with steel ones, making the umbrella lighter "
    "and much cheaper. The design has changed remarkably little "
    "since.",
    [("The earliest known umbrellas provided " + GAP +
      " rather than shelter from rain.", "shade", "",
      "there it was a shade against the sun and a sign of rank", ""),
     ("The umbrella also indicated a person's " + GAP + ".", "rank",
      "", "a shade against the sun and a sign of rank", ""),
     ("In Europe umbrellas were originally considered appropriate "
      "for " + GAP + " only.", "women", "",
      "thought suitable only for women", ""),
     ("Hanway was treated with particular hostility by " + GAP +
      ".", "cab drivers", "",
      "cab drivers were especially hostile, since rain was good for "
      "trade", "Sababi: yomg'ir ularga foydali edi."),
     ("Fox made umbrellas lighter by using " + GAP +
      " instead of whalebone.", "steel", "",
      "Samuel Fox replaced whalebone ribs with steel ones", "")],
))

PASSAGES.append(P(
    10, "HOW SOAP WORKS",
    "A soap molecule is an unusual shape: one end is attracted to "
    "water, the other is repelled by it and attracted to oil "
    "instead. Dirt sticks to skin mainly because it is held in a "
    "thin film of grease, and grease will not dissolve in water. "
    "This is why rinsing alone achieves so little.\n\n"
    "When soap is added, the oil-loving ends bury themselves in the "
    "grease while the water-loving ends face outwards. The result "
    "is a tiny sphere called a micelle, with the dirt trapped "
    "inside. The outside of the sphere is water-friendly, so the "
    "whole parcel rinses away.\n\n"
    "Against many viruses soap does something more direct. Such "
    "viruses are wrapped in a fatty envelope, and soap pulls that "
    "envelope apart, which destroys the virus completely. This is "
    "why twenty seconds of washing is recommended: the chemistry "
    "needs time, not force.",
    [("One end of a soap molecule is " + GAP + " by water.",
      "repelled", "",
      "the other is repelled by it and attracted to oil instead",
      ""),
     ("Dirt clings to the skin because it sits in a film of " + GAP +
      ".", "grease", "",
      "it is held in a thin film of grease", ""),
     ("The small sphere that forms around the dirt is known as a " +
      GAP + ".", "micelle", "",
      "a tiny sphere called a micelle, with the dirt trapped "
      "inside", ""),
     ("Many viruses are surrounded by a " + GAP + ".",
      "fatty envelope", "",
      "Such viruses are wrapped in a fatty envelope", ""),
     ("Washing is recommended to last " + GAP + ".",
      "twenty seconds", "",
      "This is why twenty seconds of washing is recommended", "")],
))

PASSAGES.append(P(
    11, "THE PENNY BLACK",
    "Before 1840 the cost of a letter in Britain was paid by the "
    "person who received it, and depended on distance and on the "
    "number of sheets. The system was slow, easy to cheat and "
    "expensive to administer, since a clerk had to calculate every "
    "item by hand.\n\n"
    "Rowland Hill argued that the real cost lay in handling, not in "
    "carriage, and proposed a flat charge paid in advance by the "
    "sender. The Penny Black, issued in May 1840, carried no "
    "country name because Britain was the first to use stamps at "
    "all - a privilege the country still keeps.\n\n"
    "The reform worked better than its critics expected. The number "
    "of letters posted doubled within a year. The stamp itself "
    "lasted only until 1841, however, because the red cancellation "
    "mark was hard to see on a black background and could be "
    "removed, allowing stamps to be reused.",
    [("Until 1840 postage was normally paid by the person who " +
      GAP + " the letter.", "received", "",
      "the cost of a letter in Britain was paid by the person who "
      "received it", ""),
     ("Hill claimed that the main expense was " + GAP +
      ", not transport.", "handling", "",
      "the real cost lay in handling, not in carriage", ""),
     ("Hill's plan was that the " + GAP + " should pay in advance.",
      "sender", "",
      "a flat charge paid in advance by the sender", ""),
     ("The number of letters sent " + GAP + " in the first year.",
      "doubled", "",
      "The number of letters posted doubled within a year", ""),
     ("The stamp was withdrawn because the " + GAP +
      " mark did not show up clearly.", "red cancellation", "",
      "the red cancellation mark was hard to see on a black "
      "background", "")],
))

PASSAGES.append(P(
    12, "DESERT ANTS AND NAVIGATION",
    "The Saharan desert ant leaves its nest, wanders in a long "
    "irregular loop that may cover 200 metres, and then "
    "runs almost straight home. It does this on ground with no "
    "landmarks, at surface temperatures that would kill it within "
    "minutes if it got lost.\n\n"
    "Two mechanisms are involved. The ant reads the pattern of "
    "polarised light in the sky, which acts as a compass even when "
    "the sun itself is hidden. It also counts its own steps, and "
    "combines the two into a running estimate of where home lies.\n\n"
    "The step-counting was proved by an experiment that is now "
    "famous. Researchers glued tiny stilts to the legs of some ants "
    "and shortened the legs of others. On the return journey the "
    "long-legged ants overshot the nest and the short-legged ones "
    "stopped short, by almost exactly the predicted amounts.",
    [("The ant's outward journey may extend as far as " + GAP + ".",
      "200 metres", "",
      "a long irregular loop that may cover 200 metres", ""),
     ("The ant navigates using " + GAP + " light in the sky.",
      "polarised", "",
      "The ant reads the pattern of polarised light in the sky", ""),
     ("This works as a " + GAP + " even when the sun is not "
      "visible.", "compass", "",
      "which acts as a compass even when the sun itself is hidden",
      ""),
     ("The ant also keeps a count of its own " + GAP + ".", "steps",
      "", "It also counts its own steps", ""),
     ("Ants given " + GAP + " went past the nest on the way back.",
      "stilts", "",
      "Researchers glued tiny stilts to the legs of some ants", "")],
))

PASSAGES.append(P(
    13, "THE MAKING OF A VIOLIN",
    "A violin is built from about seventy separate pieces, and the "
    "two that matter most are the top and the back. The top is "
    "almost always spruce, chosen because it is light and stiff "
    "along the grain; the back is usually maple, which is denser "
    "and reflects sound rather than absorbing it.\n\n"
    "The maker thins the plates by hand, tapping them constantly "
    "and listening. There is no fixed thickness: every piece of "
    "wood behaves differently, and the target is a sound, not a "
    "measurement. Inside, a small rod called the sound post "
    "transmits vibration from the top to the back, and moving it by "
    "a millimetre changes the tone audibly.\n\n"
    "Varnish is the last stage and the most argued about. It "
    "protects the wood, but too thick a coat deadens the "
    "instrument. Claims that the varnish of the old Cremona makers "
    "held a lost secret have not survived chemical analysis; what "
    "the tests keep pointing to instead is the quality of the wood "
    "and the skill of the shaping.",
    [("The front of a violin is nearly always made of " + GAP + ".",
      "spruce", "", "The top is almost always spruce", ""),
     ("Maple is used for the back because it " + GAP + " sound.",
      "reflects", "",
      "which is denser and reflects sound rather than absorbing it",
      ""),
     ("Rather than a set measurement, the maker works towards a "
      "particular " + GAP + ".", "sound", "",
      "the target is a sound, not a measurement", ""),
     ("Vibration passes between the plates through the " + GAP +
      ".", "sound post", "",
      "a small rod called the sound post transmits vibration", ""),
     ("An excessively thick layer of varnish " + GAP +
      " the instrument.", "deadens", "",
      "too thick a coat deadens the instrument", "")],
))

PASSAGES.append(P(
    14, "THE STORY OF CONCRETE",
    "Roman concrete has outlasted almost everything built since. "
    "The harbour walls at Baiae have stood in salt water for two "
    "thousand years, while modern reinforced concrete on the same "
    "coast begins to fail within fifty years.\n\n"
    "Part of the answer is volcanic ash, which the Romans mixed "
    "with lime and seawater. Recent analysis has shown something "
    "stranger: the Roman mix contains lumps of unmixed lime, long "
    "assumed to be careless work. When a crack forms and water "
    "reaches such a lump, it dissolves and recrystallises, sealing "
    "the crack. The material repairs itself.\n\n"
    "Modern concrete fails for a different reason. Its strength "
    "comes from steel bars inside, and steel rusts. Rust occupies "
    "more space than the metal it replaces, so it splits the "
    "concrete from within. The Romans used no steel, which is why "
    "their structures survive - and also why they could not build "
    "anything that had to bend.",
    [("Modern concrete on the Italian coast starts to break down "
      "after about " + GAP + ".", "fifty years", "",
      "modern reinforced concrete on the same coast begins to fail "
      "within fifty years", ""),
     ("The Romans combined lime and seawater with " + GAP + ".",
      "volcanic ash", "",
      "Part of the answer is volcanic ash, which the Romans mixed "
      "with lime and seawater", ""),
     ("The lumps in Roman concrete were previously believed to be "
      "the result of " + GAP + ".", "careless work", "",
      "lumps of unmixed lime, long assumed to be careless work", ""),
     ("Because the lumps seal any crack that opens, the material " +
      GAP + ".", "repairs itself", "",
      "The material repairs itself.", ""),
     ("Modern concrete is weakened from inside because the " + GAP +
      " expands.", "rust", "",
      "Rust occupies more space than the metal it replaces, so it "
      "splits the concrete from within", "")],
))

PASSAGES.append(P(
    15, "WHY WE YAWN",
    "Yawning is one of the most familiar things the human body "
    "does, and one of the least understood. The old explanation, "
    "that a yawn corrects a shortage of oxygen, was tested "
    "directly: volunteers breathing air rich in oxygen yawned just "
    "as often as everyone else. The theory has been abandoned.\n\n"
    "The leading account today is that a yawn cools the brain. The "
    "deep inhalation and the stretching of the jaw both increase "
    "blood flow through the head, and brain temperature does fall "
    "slightly afterwards. In support of this, people yawn less when "
    "a cold pack is held against the forehead, and yawn more in "
    "warm rooms than in cool ones.\n\n"
    "The strangest feature is contagion. Seeing, hearing or even "
    "reading about a yawn is often enough to cause one. Contagious "
    "yawning appears at about the age of four, is stronger between "
    "people who are close, and is largely absent in young children "
    "with autism, which is why some researchers link it to "
    "empathy.",
    [("The traditional explanation was that yawning corrects a lack "
      "of " + GAP + ".", "oxygen", "",
      "that a yawn corrects a shortage of oxygen", ""),
     ("According to the current theory, a yawn " + GAP +
      " the brain.", "cools", "",
      "The leading account today is that a yawn cools the brain",
      ""),
     ("Both the deep breath and the jaw movement raise " + GAP +
      " through the head.", "blood flow", "",
      "both increase blood flow through the head", ""),
     ("People yawn less often when their " + GAP + " is cooled.",
      "forehead", "",
      "people yawn less when a cold pack is held against the "
      "forehead", ""),
     ("Contagious yawning first appears around the age of " + GAP +
      ".", "four", "",
      "Contagious yawning appears at about the age of four", "")],
))

# ---------------------------------------------------------------
# 16-DARAJA — Jahongir yuborgan namuna:
#   "READING #20. The honey badger", Questions 1-8,
#   "Write NO MORE THAN TWO WORDS from the passage for each answer."
# Matn kitobdagidek, savollar kitobdagi tartibda.
# ---------------------------------------------------------------
PASSAGES.append(P(
    16, "THE HONEY BADGER",
    "It looks harmless and vulnerable. But the honey badger is "
    "afraid of nothing... and will attack and eat almost anything\n\n"
    "The honey badger (Melivora capensis) is an African and "
    "south-Asian mammal that has a reputation for being one of the "
    "world's most fearless animals, despite its small size. And in "
    "spite of its gentle-sounding name, it is also one of the most "
    "aggressive. Honey badgers have been known to attack lions, "
    "buffalo, and snakes three times their size. Even humans are "
    "not safe from a honey badger if it thinks the human will "
    "attack or harm it. They are also extremely tough creatures, "
    "and can recover quickly from injuries that would kill most "
    "other animals.\n\n"
    "At first glance, honey badgers look like the common European "
    "badger. They are usually between 75cm and 1 metre long, "
    "although males are about twice the size of females. They are "
    "instantly recognisable by grey and white stripes that extend "
    "from the top of the head to the tail. Closer inspection, which "
    "is probably not a wise thing to do, reveals pointed teeth, and "
    "sharp front claws which can be four centimetres in length.\n\n"
    "Honey badgers are meat-eating animals with an extremely varied "
    "diet. They mainly eat a range of small creatures like beetles, "
    "lizards and birds, but will also catch larger reptiles like "
    "snakes and small crocodiles. Some mammals, such as foxes, "
    "antelope and wild cats also form part of their diet.\n\n"
    "The badgers locate their prey mainly using their excellent "
    "sense of smell, and catch most of their prey through digging. "
    "During a 24-hour period, they may dig as many as fifty holes, "
    "and travel more than 40 kilometres. They are also good "
    "climbers, and can easily climb very tall trees to steal eggs "
    "from birds' nests, or catch other tree-dwelling creatures.\n\n"
    "As their name suggests, honey badgers have always been "
    "associated with honey, although they do not actually eat it. "
    "It is the highly nutritious bee eggs (called 'brood') that "
    "they prefer, and they will do anything to find it. They "
    "usually cause a lot of damage to the hive in the process, and "
    "for this reason, humans are one of their main predators. "
    "Bee-keepers will often set special traps for honey badgers, to "
    "protect their hives.\n\n"
    "One of the most fascinating aspects of the honey badger is its "
    "working relationship with a bird called the greater honeyguide "
    "(Indicator indicator). This bird deliberately guides the "
    "badger to beehives, then waits while the badger breaks into "
    "the hive and extracts the brood. The two creatures, bird and "
    "mammal, then share the brood between them.",
    [("Although they are not big animals, honey badgers are "
      "fearless, " + GAP + " and tough.", "aggressive", "",
      "in spite of its gentle-sounding name, it is also one of the "
      "most aggressive",
      "Gapdagi «fearless» va «tough» matnning boshi va oxiridan "
      "olingan — javob ularning ORASIDA."),
     ("Honey badgers will attack " + GAP +
      " if they need to protect themselves.", "humans", "",
      "Even humans are not safe from a honey badger if it thinks "
      "the human will attack or harm it",
      "«protect themselves» = «if it thinks the human will attack "
      "or harm it»."),
     ("The pattern and colours on the honey badger's back make it " +
      GAP + ".", "instantly recognisable", "recognisable",
      "They are instantly recognisable by grey and white stripes "
      "that extend from the top of the head to the tail",
      "«pattern and colours» = «grey and white stripes»."),
     ("The food they eat is meat-based and " + GAP + ".",
      "extremely varied", "varied",
      "Honey badgers are meat-eating animals with an extremely "
      "varied diet", "«meat-based» = «meat-eating»."),
     (GAP + " form the biggest part of a honey badger's diet.",
      "small creatures", "",
      "They mainly eat a range of small creatures like beetles, "
      "lizards and birds",
      "Bo'shliq gap BOSHIDA — ya'ni ega kerak, ko'plik ot. "
      "«biggest part» = «mainly eat»."),
     ("Honey badgers find the creatures they eat by their " + GAP +
      ".", "smell", "sense of smell",
      "The badgers locate their prey mainly using their excellent "
      "sense of smell",
      "DIQQAT — SO'Z SANASH: «sense of smell» UCH so'z, chegara "
      "esa ikkita. Haqiqiy imtihonda uch so'z yozsangiz nol ball "
      "olardingiz. Bu yerda ikkalasi ham qabul qilinadi, lekin "
      "odat qilmang: doim chegarani sanang."),
     (GAP + " are often used to catch honey badgers which attack "
      "beehives.", "special traps", "traps",
      "Bee-keepers will often set special traps for honey badgers, "
      "to protect their hives.", ""),
     ("For one particular type of food, the honey badger has a " +
      GAP + " with another creature.", "working relationship", "",
      "its working relationship with a bird called the greater "
      "honeyguide",
      "«another creature» = «a bird»; «one particular type of "
      "food» = brood (asalari tuxumi).")],
))

# ================= 17-20: eng qiyin daraja =====================
PASSAGES.append(P(
    17, "THE DISCOVERY OF PENICILLIN",
    "The story is usually told as an accident, and the accident is "
    "real enough. Returning from holiday in September 1928, "
    "Alexander Fleming found that a culture plate of staphylococcus "
    "had been contaminated by a mould, and that the bacteria around "
    "the mould had dissolved. What is less often said is how "
    "improbable the sequence was: the mould spore is thought to "
    "have drifted up from a laboratory on the floor below, and an "
    "unusually cool spell had allowed it to grow before the "
    "bacteria took over the plate.\n\n"
    "Fleming published his observation in 1929 and then largely set "
    "it aside. He could not purify the substance in useful "
    "quantities, and he was not a chemist. For almost a decade the "
    "paper was read by few and acted on by nobody.\n\n"
    "The work that mattered was done in Oxford from 1938 by Howard "
    "Florey and Ernst Chain, who solved the extraction problem and "
    "showed in 1940 that infected mice survived when treated. Even "
    "then the yield was so small that the team recovered the drug "
    "from patients' urine and used it again. Mass production "
    "required American factories and a strain of mould found, "
    "famously, on a melon in a Peoria market.\n\n"
    "Fleming, Florey and Chain shared the Nobel Prize in 1945. In "
    "his acceptance lecture Fleming warned that bacteria exposed to "
    "too little of the drug would become resistant to it - a "
    "prediction that took less than twenty years to come true.",
    [("The mould is believed to have come from a laboratory on the "
      + GAP + ".", "floor below", "",
      "the mould spore is thought to have drifted up from a "
      "laboratory on the floor below", ""),
     ("An unusually " + GAP +
      " period of weather let the mould grow first.", "cool", "",
      "an unusually cool spell had allowed it to grow before the "
      "bacteria took over the plate", ""),
     ("Fleming abandoned the work partly because he was not a " +
      GAP + ".", "chemist", "",
      "He could not purify the substance in useful quantities, and "
      "he was not a chemist", ""),
     ("Because so little could be made, the drug was collected "
      "again from the " + GAP + " of patients.", "urine", "",
      "the team recovered the drug from patients' urine and used it "
      "again", ""),
     ("Fleming predicted that bacteria given too small a dose would "
      "become " + GAP + ".", "resistant", "",
      "bacteria exposed to too little of the drug would become "
      "resistant to it", "")],
))

PASSAGES.append(P(
    18, "TIDAL POWER",
    "Of all renewable sources, tidal energy has the one quality the "
    "others lack: it is predictable. The wind may or may not blow "
    "next Tuesday, but the tide next Tuesday can be calculated "
    "years ahead, because it is driven by the positions of the moon "
    "and the sun rather than by weather.\n\n"
    "The oldest approach is the barrage, a dam across an estuary "
    "with turbines set into it. The scheme at La Rance in France "
    "has run since 1966 and still produces power at a competitive "
    "price, the capital cost having been paid off long ago. But a "
    "barrage changes the estuary permanently: mudflats that feed "
    "migrating birds are lost, and sediment builds up behind the "
    "wall. Few countries have been willing to accept that trade "
    "since.\n\n"
    "Attention has therefore shifted to underwater turbines, which "
    "sit on the seabed in a fast current and work rather like wind "
    "turbines in a much denser fluid. Because water is some eight "
    "hundred times denser than air, a small rotor gathers a great "
    "deal of energy. The difficulty is maintenance: salt water "
    "attacks everything, and a machine on the seabed cannot be "
    "reached in a hurry.",
    [("Unlike other renewable sources, tidal power is " + GAP + ".",
      "predictable", "",
      "tidal energy has the one quality the others lack: it is "
      "predictable", ""),
     ("The tide depends on the positions of the sun and the " + GAP +
      " rather than on the weather.", "moon", "",
      "it is driven by the positions of the moon and the sun rather "
      "than by weather", ""),
     ("A barrage destroys the " + GAP +
      " on which migrating birds feed.", "mudflats", "",
      "mudflats that feed migrating birds are lost", ""),
     ("The main problem with underwater turbines is " + GAP + ".",
      "maintenance", "",
      "The difficulty is maintenance: salt water attacks "
      "everything", "")],
))

PASSAGES.append(P(
    19, "THE ART OF THE MAP",
    "Every map is a lie, and a useful map is a lie told carefully. "
    "A curved surface cannot be laid flat without distortion "
    "somewhere, so the cartographer must decide what to sacrifice. "
    "The Mercator projection, drawn in 1569, preserves angles, "
    "which is why a ship steering a constant compass bearing "
    "follows a straight line on it. The price is area: Greenland "
    "appears roughly the size of Africa, though Africa is fourteen "
    "times larger.\n\n"
    "Projections that keep areas true, such as the Gall-Peters, "
    "distort shape instead, and were promoted in the 1970s on "
    "political grounds. Cartographers were mostly unimpressed - not "
    "because the politics were wrong but because the projection "
    "itself was neither new nor particularly good.\n\n"
    "Digital mapping has quietly settled the argument in an "
    "unexpected way. Online maps use a variant of Mercator, chosen "
    "for a technical reason rather than a political one: it keeps "
    "small shapes correct at every zoom level, which matters when a "
    "user is looking at a street corner. The old debate about "
    "world maps continues, but almost nobody now looks at a world "
    "map.",
    [("Because a curved surface cannot be flattened, every map "
      "contains " + GAP + ".", "distortion", "",
      "A curved surface cannot be laid flat without distortion "
      "somewhere", ""),
     ("The Mercator projection keeps " + GAP + " accurate.",
      "angles", "",
      "The Mercator projection, drawn in 1569, preserves angles",
      ""),
     ("On Mercator maps, Africa is shown far smaller than its real "
      + GAP + ".", "area", "",
      "The price is area: Greenland appears roughly the size of "
      "Africa", ""),
     ("Online maps use a form of Mercator because small shapes stay "
      "correct at every " + GAP + ".", "zoom level", "",
      "it keeps small shapes correct at every zoom level", "")],
))

PASSAGES.append(P(
    20, "MEMORY AND THE WITNESS",
    "The law has long treated an eyewitness as the strongest kind "
    "of evidence, and psychology has spent fifty years showing why "
    "that confidence is misplaced. Memory is not a recording. Each "
    "time an event is recalled it is reassembled, and anything "
    "encountered since can be built into it.\n\n"
    "Elizabeth Loftus demonstrated the effect with a question. "
    "Volunteers watched a film of a car crash; those asked how fast "
    "the cars were going when they smashed into each other gave "
    "higher speeds than those asked about cars that hit each other, "
    "and were later more likely to report broken glass that had "
    "never been in the film at all.\n\n"
    "The practical danger lies in the identification parade. If the "
    "real offender is absent, a witness who assumes the guilty "
    "party must be present tends to choose whoever looks closest. "
    "Any encouragement afterwards raises the witness's confidence "
    "without improving accuracy, and by the time of the trial the "
    "hesitant choice has become a certain memory.\n\n"
    "The remedies now recommended are procedural rather than "
    "technological. The officer running the parade should not know "
    "which person is the suspect; the witness should be told the "
    "offender may not be there; and the level of confidence should "
    "be recorded immediately, before anyone can comment on it.",
    [("Rather than a recording, a memory is " + GAP +
      " each time it is recalled.", "reassembled", "",
      "Each time an event is recalled it is reassembled", ""),
     ("Witnesses asked about cars that " + GAP +
      " estimated greater speeds.", "smashed", "",
      "those asked how fast the cars were going when they smashed "
      "into each other gave higher speeds", ""),
     ("Encouragement increases a witness's " + GAP +
      " but not their accuracy.", "confidence", "",
      "Any encouragement afterwards raises the witness's confidence "
      "without improving accuracy", ""),
     ("The witness should be warned that the offender " + GAP +
      " be present.", "may not", "",
      "the witness should be told the offender may not be there",
      "")],
))


# =====================================================================
#  QURISH
# =====================================================================
def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase)."""
    out = []
    for p in PASSAGES:
        sents = [it[0] for it in p["items"]]
        for i, (sent, ans, alt, quote, note) in enumerate(
                p["items"], 1):
            assert sent.count(GAP) == 1, (p["level"], i, "1 bo'shliq")
            expl = (f"Gapda: «{sent}»  ->  Matnda: «{quote}». "
                    f"Javob: {ans}.")
            if note:
                expl += " " + note
            out.append((
                KIND, p["level"],
                {"title": p["title"],
                 "passage": p["text"],
                 # Butun to'plam ko'rinadi (joriysi ajratiladi) —
                 # "gaplar matn tartibida" qoidasi amalda ishlashi
                 # uchun.
                 "questions": sents,
                 "q_no": i,
                 "prompt": sent,
                 "step": p["level"],
                 "step_title": f"{p['level']}-daraja",
                 "order": i - 1,
                 "instruction": INSTR,
                 "tip": SENTENCE_TIPS[
                     (p["level"] + i) % len(SENTENCE_TIPS)][0]},
                ans, expl, alt or None,
                {"table": sent, "passage": quote}))
    return out


def seed_sentence(db):
    """Idempotent: bor bo'lsa qayta yozmaydi (hech narsa o'chmaydi)."""
    import json
    import models
    # 2026-09-13: TEKSHIRUV ISHLAMAGAN EDI. r.level bazada MATN ("1"),
    # build_rows() esa SON (1) beradi — ("1", 1) != (1, 1), shuning
    # uchun har sovuq startda 100 ta nusxa qayta yozilardi. Jonli bazada
    # shu 4 turdan 1,3 mln qator (2 GB) to'plangan edi. Ikkala tomon
    # ham matnga keltiriladi; bazadan faqat kerakli ustunlar o'qiladi.
    have = {
        (str(lv), json.loads(pl).get("order"))
        for lv, pl in db.query(models.PracticeItem.level,
                               models.PracticeItem.payload)
        .filter(models.PracticeItem.skill == SKILL,
                models.PracticeItem.kind == KIND).all()}
    n = 0
    for kind, level, payload, answer, explain, alt, para in \
            build_rows():
        if (str(level), payload["order"]) in have:
            continue
        if para:
            payload["paraphrase"] = para
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt, explain=explain, is_active=1))
        n += 1
    if n:
        db.commit()
    return n
