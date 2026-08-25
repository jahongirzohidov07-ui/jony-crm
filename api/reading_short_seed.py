# -*- coding: utf-8 -*-
"""IELTS READING — SHORT-ANSWER QUESTIONS (2026-08-25).

Jahongir: "Short answer questions savol turiga misol pastida true
false ham bor uni olmaysan, bitta text shundan aniq savol beriladi
topishga shunaqa qil sen ham bu hozir ozgina qiyin 7-8-mashqqa qilib
qoysang boladi undan oldingilarni osonroq boladi va qiyinlashib
ketaveradi."

Ya'ni namunadagi TRUE/FALSE qismi OLINMADI — faqat to'g'ridan-to'g'ri
savollar (What / Where / How far / Who / Why / How many) va matndan
olingan qisqa javob.

TUZILISHI. 20 ta matn, jami 100 savol, daraja 1..20:
  1-6    — namunadan OSONROQ: qisqa matn, savol matndagi jumlaga
           deyarli aynan mos keladi;
  7      — "READING #9. Sylvia Earle" (Jahongirning namunasi);
  8-20   — qiyinlashib boradi: matn uzayadi, savol bilan javob
           orasidagi paraffraz uzoqlashadi, chalg'ituvchi son va
           sanalar ko'payadi.

BU TURNING O'ZIGA XOSLIGI. Boshqa turlarda bo'shliqni to'ldirasiz —
bu yerda esa SAVOL beriladi. Birinchi ish: savol so'zi javob TURINI
aytadi. "How far" — masofa, "Where" — joy, "Who" — odam, "How many"
— son. Shu aniqlanmasa, matndan noto'g'ri narsa olib chiqiladi.

Javob 2 so'zdan oshmaydi va MATNDAN olinadi — o'zingizdan gap
tuzilmaydi.
"""

SKILL = "ielts_reading"
KIND = "read_short"

# =====================================================================
#  QOIDALAR
# =====================================================================
SHORT_TIPS = [
    ("Short-answer nima",
     "Matn bo'yicha to'g'ridan-to'g'ri savol beriladi, javobni "
     "MATNDAN topib yozasiz. To'liq gap yozilmaydi — faqat kerakli "
     "so'z yoki son.",
     "Savol: How far under water did she go to break a record?\n"
     "Matn: «reaching a record-breaking depth of 381 metres»\n"
     "Javob: 381 metres"),
    ("1-QADAM — savol so'ziga qarang",
     "Savol so'zi javobning TURINI aytadi. Buni aniqlamasdan "
     "matnga kirmang — aks holda birinchi ko'ringan sonni yozib "
     "yuborasiz.",
     "What — narsa/kasb · Where — joy · When — vaqt\n"
     "Who — odam · Why — sabab · How far — masofa\n"
     "How many / How much — son · How long — davomiylik"),
    ("2-QADAM — paraffrazni toping",
     "Savoldagi so'zlar matnda aynan turmaydi. «What was causing "
     "harm to everything living in the sea?» degan savolda matnda "
     "«harm» yo'q — «the damage that pollution was causing to "
     "marine life» bor.",
     "causing harm = causing damage\n"
     "everything living in the sea = marine life\n"
     "career = become an underwater explorer"),
    ("Ikki so'zdan oshmaydi",
     "«NO MORE THAN TWO WORDS AND/OR A NUMBER» — «381 metres», "
     "«fish farms», «underwater explorer». Uchta so'z yozsangiz "
     "javob noto'g'ri sanaladi, ma'nosi to'g'ri bo'lsa ham.", ""),
    ("To'liq gap yozmang",
     "«She went 381 metres deep» — NOTO'G'RI. Faqat «381 metres». "
     "Artikl (a, the) ham odatda shart emas.", ""),
    ("Savollar matn tartibida boradi",
     "1-savol javobi matnning boshida, oxirgisi oxirida. "
     "2-javobni topdingizmi — 3-javob undan keyin. Orqaga "
     "qaytmang.", ""),
    ("O'zingizdan javob o'ylab topmang",
     "Javob matnda BO'LISHI shart. Hayotda to'g'ri bo'lgan javob "
     "matnda yozilmagan bo'lsa — u noto'g'ri.", ""),
    ("Chalg'ituvchi sonlar",
     "Matnda 1935, 16, 6,500, 70, 381, 1970 kabi sonlar ketma-ket "
     "keladi. Savol qaysi birini so'rayotganini savol so'zidan "
     "aniqlang: «How far» — 381 metres, «How many hours» — 6,500.",
     ""),
]


def P(level, title, text, qs):
    return {"level": level, "title": title, "text": text, "qs": qs}


PASSAGES = []

# ---------------------------------------------------------------- 1
PASSAGES.append(P(
    1, "THE CAFE ON OUR STREET",
    "There is a small cafe at the end of our street. It is called "
    "The Green Door and it opened three years ago. The owner is a "
    "woman named Malika. She makes very good cakes. The cafe is "
    "busiest on Saturday, when families come for breakfast. It "
    "closes at nine in the evening.",
    [("What is the cafe called?", "The Green Door",
      "It is called The Green Door",
      "«called» savolda ham, matnda ham bir xil — eng oson daraja."),
     ("Who owns the cafe?", "Malika",
      "The owner is a woman named Malika",
      "«Who» — odam ismi so'ralyapti."),
     ("What does the owner make well?", "cakes",
      "She makes very good cakes", "PARAFFRAZ: well = very good."),
     ("Which day is the cafe busiest?", "Saturday",
      "The cafe is busiest on Saturday", "Hafta kuni."),
     ("What time does the cafe close?", "nine",
      "It closes at nine in the evening", "Vaqt.")],
))

# ---------------------------------------------------------------- 2
PASSAGES.append(P(
    2, "THE SCHOOL LIBRARY",
    "Our school library is on the second floor. It has about four "
    "thousand books. Students may borrow three books at a time and "
    "keep them for two weeks. The librarian, Mr Karimov, also runs a "
    "reading club on Thursdays. The room is quiet because talking is "
    "not allowed inside.",
    [("Where in the school is the library?", "second floor",
      "Our school library is on the second floor",
      "«Where» — joy so'ralyapti."),
     ("How many books does it have?", "four thousand",
      "It has about four thousand books",
      "«How many» — son. Ikki so'zli javob."),
     ("How long can students keep a book?", "two weeks",
      "keep them for two weeks",
      "«How long» — davomiylik. Chalg'ituvchi: «three» — kitob "
      "soni."),
     ("Who runs the reading club?", "Mr Karimov",
      "The librarian, Mr Karimov, also runs a reading club",
      "«Who» — odam."),
     ("Why is the room quiet?", "talking",
      "The room is quiet because talking is not allowed inside",
      "«Why» — sabab. Javob qisqa: nima taqiqlangan.")],
))

# ---------------------------------------------------------------- 3
PASSAGES.append(P(
    3, "THE CITY BICYCLE RACE",
    "The city bicycle race takes place every spring. Last year more "
    "than five hundred riders took part. The route is forty "
    "kilometres long and passes through the old town. The winner, a "
    "student called Aziz, finished in one hour and ten minutes. The "
    "prize was a new bicycle.",
    [("When does the race take place?", "every spring",
      "The city bicycle race takes place every spring",
      "«When» — vaqt."),
     ("How many riders took part last year?", "five hundred",
      "more than five hundred riders took part",
      "«How many» — son."),
     ("How long is the route?", "forty kilometres",
      "The route is forty kilometres long",
      "«How long» bu yerda MASOFA — chunki yo'l haqida."),
     ("What is the winner's job?", "student",
      "The winner, a student called Aziz",
      "Chalg'ituvchi: ism «Aziz», lekin savol KASBni so'rayapti."),
     ("What did the winner receive?", "a new bicycle",
      "The prize was a new bicycle",
      "PARAFFRAZ: received = the prize was.")],
))

# ---------------------------------------------------------------- 4
PASSAGES.append(P(
    4, "THE OLD BRIDGE",
    "The stone bridge over the river was built in 1892 by a local "
    "engineer. For almost a century it carried carts and later cars. "
    "In 1990 it was closed to traffic because the stone had become "
    "weak. Today only people on foot may cross it. Every summer the "
    "town holds a small festival on the bridge.",
    [("When was the bridge built?", "1892",
      "The stone bridge over the river was built in 1892",
      "«When» — sana. Chalg'ituvchi: 1990."),
     ("Who built it?", "a local engineer",
      "built in 1892 by a local engineer",
      "«Who» — odam yoki kasb."),
     ("Why was it closed to traffic?", "the stone",
      "it was closed to traffic because the stone had become weak",
      "«Why» — sabab; nima zaiflashgan."),
     ("How may people cross the bridge now?", "on foot",
      "Today only people on foot may cross it",
      "PARAFFRAZ: now = today. «How» — usul so'ralyapti."),
     ("What does the town hold on the bridge in summer?", "festival",
      "Every summer the town holds a small festival on the bridge",
      "Voqea nomi.")],
))

# ---------------------------------------------------------------- 5
PASSAGES.append(P(
    5, "THE VILLAGE FESTIVAL",
    "Every autumn the village of Chorbog holds a harvest festival. "
    "It has been held since 1978. Around two thousand visitors come "
    "each year, many of them from the capital. The main attraction "
    "is a competition for the largest pumpkin. The money raised goes "
    "to the village school, which used it last year to buy new "
    "computers.",
    [("In which season is the festival held?", "autumn",
      "Every autumn the village of Chorbog holds a harvest festival",
      "Fasl so'ralyapti."),
     ("When was the festival first held?", "1978",
      "It has been held since 1978",
      "PARAFFRAZ: first held = since."),
     ("How many people visit each year?", "two thousand",
      "Around two thousand visitors come each year",
      "PARAFFRAZ: people visit = visitors come."),
     ("What is the main competition about?", "the largest pumpkin",
      "a competition for the largest pumpkin",
      "Musobaqa mavzusi."),
     ("What did the school buy last year?", "new computers",
      "which used it last year to buy new computers",
      "Nima sotib olingan.")],
))

# ---------------------------------------------------------------- 6
PASSAGES.append(P(
    6, "THE MOUNTAIN WEATHER STATION",
    "A weather station stands at 2,400 metres on the slopes of the "
    "Chatkal range. It was set up in 1965 and is staffed by two "
    "people, who stay for a month at a time. Their main task is to "
    "record snow depth, information which is used to warn villages "
    "below about the danger of avalanches. Supplies are brought up "
    "by helicopter once a fortnight.",
    [("How high is the weather station?", "2,400 metres",
      "A weather station stands at 2,400 metres",
      "«How high» — balandlik. Chalg'ituvchi: 1965 — yil."),
     ("How many people work there?", "two",
      "is staffed by two people",
      "PARAFFRAZ: work there = is staffed by."),
     ("What do the staff mainly record?", "snow depth",
      "Their main task is to record snow depth",
      "PARAFFRAZ: mainly = main task."),
     ("What danger are villages warned about?", "avalanches",
      "to warn villages below about the danger of avalanches",
      "Xavf turi."),
     ("How are supplies delivered?", "by helicopter",
      "Supplies are brought up by helicopter",
      "PARAFFRAZ: delivered = brought up.")],
))

# ---------------------------------------------------------------- 7
#  JAHONGIRNING NAMUNASI — READING #9
PASSAGES.append(P(
    7, "READING #9. SYLVIA EARLE, UNDERWATER HERO",
    "She has spent her working life studying the world's oceans. "
    "Sylvia Earle is an underwater explorer and marine biologist who "
    "was born in the USA in 1935. She became interested in the "
    "world's oceans from an early age. As a child, she liked to "
    "stand on the beach for hours and look at the sea, wondering "
    "what it must be like under the surface.\n\n"
    "When she was 16, she finally got a chance to make her first "
    "dive. It was this dive that inspired her to become an "
    "underwater explorer. Since then, she has spent more than 6,500 "
    "hours under water, and has led more than seventy expeditions "
    "worldwide. She has also made the deepest dive ever, reaching a "
    "record-breaking depth of 381 metres.\n\n"
    "In 1970, she became famous around the world when she became the "
    "captain of the first all-female team to live under water. The "
    "team spent two weeks in an underwater 'house'. The research "
    "they carried out showed the damage that pollution was causing "
    "to marine life, and especially to coral reefs. Her team also "
    "studied the problem of over-fishing. Fishing methods meant that "
    "people were catching too many fish, Earle warned, and many "
    "species were in danger of becoming extinct.\n\n"
    "Since then she has written several books and magazine articles "
    "in which she suggests ways of reducing the damage that is being "
    "done to the world's oceans. One way, she believes, is to rely "
    "on fish farms for seafood, and reduce the amount of fishing "
    "that is done out at sea. Although she no longer eats seafood "
    "herself, she realises the importance it plays in our diets. It "
    "would be wrong to tell people they should stop eating fish from "
    "the sea, she says. However, they need to reduce the impact they "
    "are having on the ocean's supplies.",
    [("What career did Sylvia decide to follow after her first dive?",
      "underwater explorer",
      "It was this dive that inspired her to become an underwater "
      "explorer",
      "PARAFFRAZ: career she decided to follow = inspired her to "
      "become. Ikki so'zli javob."),
     ("How far under water did she go in order to break a world "
      "record?", "381 metres",
      "reaching a record-breaking depth of 381 metres",
      "«How far under water» — CHUQURLIK. Chalg'ituvchi: 6,500 "
      "soat, 70 ekspeditsiya, 16 yosh."),
     ("What was causing harm to everything living in the sea?",
      "pollution",
      "the damage that pollution was causing to marine life",
      "PARAFFRAZ: causing harm = causing damage; everything living "
      "in the sea = marine life."),
     ("Where does Sylvia think we should get our fish from?",
      "fish farms",
      "One way, she believes, is to rely on fish farms for seafood",
      "PARAFFRAZ: she thinks = she believes; get our fish from = "
      "rely on ... for seafood.")],
))

# ---------------------------------------------------------------- 8
PASSAGES.append(P(
    8, "THE PENCIL",
    "The modern pencil began with a discovery in Cumbria, England, in "
    "1564, when a storm uprooted a tree and revealed a large deposit "
    "of graphite. Shepherds first used it to mark sheep. Because pure "
    "graphite is soft and breaks easily, the Italians began wrapping "
    "it in string; later the French chemist Nicolas-Jacques Conte "
    "mixed it with clay and baked it, a method still used today. The "
    "proportion of clay decides the hardness: more clay makes a "
    "harder, lighter line. A single average pencil can draw a line "
    "about fifty-six kilometres long.",
    [("Where was the graphite deposit found?", "Cumbria",
      "began with a discovery in Cumbria, England, in 1564",
      "«Where» — joy nomi."),
     ("What revealed the deposit?", "a storm",
      "when a storm uprooted a tree and revealed a large deposit",
      "Sabab-hodisa."),
     ("Who first used the graphite?", "Shepherds",
      "Shepherds first used it to mark sheep", "«Who» — odamlar."),
     ("What did Conte add to the graphite?", "clay",
      "the French chemist Nicolas-Jacques Conte mixed it with clay",
      "Chalg'ituvchi: «string» — italiyaliklar usuli."),
     ("How long a line can one pencil draw?", "fifty-six kilometres",
      "can draw a line about fifty-six kilometres long",
      "«How long» — masofa. Chalg'ituvchi: 1564.")],
))

# ---------------------------------------------------------------- 9
PASSAGES.append(P(
    9, "JANE GOODALL",
    "Jane Goodall arrived at Gombe in Tanzania in 1960 with no "
    "university degree, sent by the palaeontologist Louis Leakey, who "
    "believed an untrained observer would be free of scientific "
    "prejudice. Within months she had recorded chimpanzees stripping "
    "leaves from twigs to fish termites out of their mounds — the "
    "first proof that animals other than humans make tools. Critics "
    "objected to her habit of giving the animals names rather than "
    "numbers. She later earned a doctorate at Cambridge and now "
    "spends most of the year travelling to speak about conservation.",
    [("Who sent Goodall to Gombe?", "Louis Leakey",
      "sent by the palaeontologist Louis Leakey",
      "«Who» — odam ismi."),
     ("What did Leakey think an untrained observer would avoid?",
      "scientific prejudice",
      "believed an untrained observer would be free of scientific "
      "prejudice", "PARAFFRAZ: avoid = be free of."),
     ("What were the chimpanzees catching?", "termites",
      "to fish termites out of their mounds", "Hasharot nomi."),
     ("What did critics dislike about her method?", "names",
      "Critics objected to her habit of giving the animals names "
      "rather than numbers",
      "PARAFFRAZ: disliked = objected to."),
     ("Where did she gain her doctorate?", "Cambridge",
      "She later earned a doctorate at Cambridge",
      "PARAFFRAZ: gain = earn.")],
))

# --------------------------------------------------------------- 10
PASSAGES.append(P(
    10, "THE GREAT BARRIER REEF",
    "Stretching for 2,300 kilometres along the coast of Queensland, "
    "the Great Barrier Reef is the largest structure on Earth built "
    "by living organisms. It is composed of nearly three thousand "
    "individual reefs and supports some 1,500 species of fish. The "
    "reef generates about six billion Australian dollars a year, "
    "mostly from tourism. Its greatest threat is warming water, "
    "which causes corals to expel the algae that give them both "
    "their colour and most of their food; the whitened coral can "
    "recover if temperatures fall quickly enough.",
    [("How long is the reef?", "2,300 kilometres",
      "Stretching for 2,300 kilometres along the coast",
      "«How long» — masofa."),
     ("Which Australian state lies beside it?", "Queensland",
      "along the coast of Queensland", "Joy nomi."),
     ("How many fish species live there?", "1,500",
      "supports some 1,500 species of fish",
      "Chalg'ituvchi: «three thousand» — riflar soni."),
     ("What earns most of the reef's income?", "tourism",
      "generates about six billion Australian dollars a year, "
      "mostly from tourism", "PARAFFRAZ: most = mostly."),
     ("What do corals lose when the water warms?", "algae",
      "causes corals to expel the algae",
      "PARAFFRAZ: lose = expel.")],
))

# --------------------------------------------------------------- 11
PASSAGES.append(P(
    11, "HOW BEES MAKE HONEY",
    "A worker bee visits up to a hundred flowers on a single trip, "
    "storing nectar in a special stomach. Back at the hive she passes "
    "it to a house bee, who chews it for about half an hour, adding "
    "enzymes that break the complex sugars down. The mixture is then "
    "spread in the wax cells, where bees fan it with their wings "
    "until the water content drops below twenty percent, low enough "
    "to prevent fermentation. The cell is finally sealed with a wax "
    "cap. A single bee produces around a twelfth of a teaspoon of "
    "honey in her whole life.",
    [("How many flowers does a bee visit on one trip?", "a hundred",
      "visits up to a hundred flowers on a single trip",
      "«How many» — son."),
     ("Where does the bee store the nectar?", "a special stomach",
      "storing nectar in a special stomach",
      "«Where» — joy, tanadagi organ."),
     ("What does the house bee add?", "enzymes",
      "adding enzymes that break the complex sugars down",
      "Nima qo'shiladi."),
     ("What do bees use to dry the mixture?", "their wings",
      "bees fan it with their wings",
      "PARAFFRAZ: dry = fan; chalg'ituvchi: «wax cells» — joy."),
     ("What seals the cell at the end?", "a wax cap",
      "The cell is finally sealed with a wax cap",
      "PARAFFRAZ: at the end = finally.")],
))

# --------------------------------------------------------------- 12
PASSAGES.append(P(
    12, "THE WRIGHT BROTHERS",
    "Wilbur and Orville Wright ran a bicycle shop in Dayton, Ohio, "
    "and used its profits to fund their experiments. Unlike rivals "
    "who concentrated on engine power, they were convinced that the "
    "unsolved problem was control, and they studied the way buzzards "
    "twisted their wingtips to stay balanced. To test their designs "
    "cheaply they built a wind tunnel in 1901 and measured more than "
    "two hundred wing shapes. Their first powered flight, at Kitty "
    "Hawk in December 1903, lasted just twelve seconds and covered "
    "thirty-seven metres.",
    [("What business did the brothers run?", "a bicycle shop",
      "ran a bicycle shop in Dayton, Ohio", "Biznes turi."),
     ("What did they believe was the unsolved problem?", "control",
      "they were convinced that the unsolved problem was control",
      "PARAFFRAZ: believed = were convinced."),
     ("Which birds did they study?", "buzzards",
      "they studied the way buzzards twisted their wingtips",
      "Qush nomi."),
     ("What did they build to test designs cheaply?", "a wind tunnel",
      "To test their designs cheaply they built a wind tunnel",
      "Qurilma nomi."),
     ("How long did the first powered flight last?", "twelve seconds",
      "lasted just twelve seconds",
      "«How long» — vaqt. Chalg'ituvchi: 37 metr — masofa.")],
))

# --------------------------------------------------------------- 13
PASSAGES.append(P(
    13, "RICE",
    "Rice feeds more people than any other crop, providing over a "
    "fifth of the calories consumed worldwide. It was domesticated in "
    "the Yangtze valley of China at least nine thousand years ago. "
    "Unlike wheat, rice tolerates flooded fields, and farmers use "
    "standing water chiefly to suppress weeds rather than to feed the "
    "plant. This method has a cost: flooded paddies are a major "
    "source of methane, a gas about thirty times more powerful than "
    "carbon dioxide at trapping heat. Newer techniques drain the "
    "fields periodically, cutting emissions by roughly half.",
    [("What share of the world's calories does rice provide?",
      "a fifth", "providing over a fifth of the calories consumed",
      "PARAFFRAZ: share = fifth."),
     ("Where was rice first domesticated?", "Yangtze valley",
      "It was domesticated in the Yangtze valley of China",
      "«Where» — joy. Ikki so'z."),
     ("Why do farmers flood the fields?", "weeds",
      "farmers use standing water chiefly to suppress weeds",
      "«Why» — sabab; nimani bostirish uchun."),
     ("What gas do paddies release?", "methane",
      "flooded paddies are a major source of methane",
      "PARAFFRAZ: release = are a source of."),
     ("By how much do new methods cut emissions?", "half",
      "cutting emissions by roughly half",
      "Chalg'ituvchi: «thirty times» — metan kuchi.")],
))

# --------------------------------------------------------------- 14
PASSAGES.append(P(
    14, "THE SAHARA",
    "The Sahara covers roughly nine million square kilometres, an "
    "area comparable to that of China. Its reputation for endless "
    "sand is misleading: dunes occupy only about a quarter of the "
    "surface, the rest being gravel plains, rock and mountains, the "
    "highest of which rises to 3,415 metres. Rock paintings show "
    "hippopotamuses and cattle, evidence that as recently as six "
    "thousand years ago the region held lakes and grassland. The "
    "change is attributed to a slow shift in the Earth's orbit, which "
    "weakened the summer monsoon.",
    [("How large is the Sahara?", "nine million",
      "covers roughly nine million square kilometres",
      "«How large» — maydon."),
     ("What proportion of it is dunes?", "a quarter",
      "dunes occupy only about a quarter of the surface",
      "PARAFFRAZ: proportion = about a quarter."),
     ("How high is the tallest mountain?", "3,415 metres",
      "the highest of which rises to 3,415 metres",
      "«How high» — balandlik."),
     ("What animals appear in the rock paintings?", "hippopotamuses",
      "Rock paintings show hippopotamuses and cattle",
      "Hayvon nomi."),
     ("What weakened as the orbit shifted?", "the summer monsoon",
      "a slow shift in the Earth's orbit, which weakened the "
      "summer monsoon", "Nima zaiflashgan.")],
))

# --------------------------------------------------------------- 15
PASSAGES.append(P(
    15, "LIVING IN ANTARCTICA",
    "About four thousand people work in Antarctica during the "
    "southern summer, a figure that falls to around one thousand when "
    "the darkness sets in. The largest base, McMurdo, resembles a "
    "small mining town and has its own fire station. Winter staff "
    "cannot be evacuated for medical reasons between March and "
    "August, so every team includes a doctor who has been trained to "
    "operate on herself if necessary. A famous case occurred in 1961, "
    "when a Soviet physician removed his own appendix using a mirror.",
    [("How many people work there in summer?", "four thousand",
      "About four thousand people work in Antarctica during the "
      "southern summer", "«How many» — son."),
     ("What is the biggest base called?", "McMurdo",
      "The largest base, McMurdo",
      "PARAFFRAZ: biggest = largest."),
     ("What facility does that base have?", "fire station",
      "has its own fire station", "Ob'yekt nomi."),
     ("Why must the doctor be specially trained?", "evacuated",
      "Winter staff cannot be evacuated for medical reasons",
      "«Why» — sabab: evakuatsiya qilib bo'lmaydi."),
     ("What did the Soviet doctor use in 1961?", "a mirror",
      "a Soviet physician removed his own appendix using a mirror",
      "Asbob.")],
))

# --------------------------------------------------------------- 16
PASSAGES.append(P(
    16, "THE TELEPHONE",
    "Alexander Graham Bell filed his patent on 14 February 1876, only "
    "hours before a rival, Elisha Gray, filed a similar document; the "
    "dispute occupied the courts for years. Bell's interest in sound "
    "was personal — both his mother and his wife were deaf, and he "
    "spent much of his career teaching speech to deaf children, work "
    "he regarded as more important than the telephone. He refused to "
    "keep an instrument in his study, complaining that it interrupted "
    "his thinking. By 1886 more than 150,000 Americans owned one.",
    [("When did Bell file his patent?", "14 February",
      "filed his patent on 14 February 1876",
      "«When» — sana. Chalg'ituvchi: 1886."),
     ("Who filed a similar document that day?", "Elisha Gray",
      "only hours before a rival, Elisha Gray, filed a similar "
      "document", "«Who» — odam."),
     ("Besides his wife, which relative of Bell was deaf?",
      "mother", "both his mother and his wife were deaf",
      "Chalg'ituvchi: «wife» savolda aytib qo'yilgan."),
     ("What work did Bell value most?", "teaching speech",
      "he spent much of his career teaching speech to deaf "
      "children, work he regarded as more important",
      "PARAFFRAZ: valued most = regarded as more important."),
     ("Why did he keep no telephone in his study?", "interrupted",
      "complaining that it interrupted his thinking",
      "«Why» — sabab.")],
))

# --------------------------------------------------------------- 17
PASSAGES.append(P(
    17, "THE ARCTIC TERN",
    "The Arctic tern makes the longest migration of any animal, "
    "flying from its Arctic breeding grounds to Antarctica and back "
    "each year. Tracking devices weighing only 1.4 grams have shown "
    "that the route is not direct: birds follow winding paths that "
    "exploit prevailing winds, so the annual distance reaches about "
    "seventy thousand kilometres. Because the bird lives for some "
    "thirty years, its lifetime travel is roughly equal to three "
    "return journeys to the Moon. It sees more daylight than any "
    "other creature.",
    [("Which animal migrates furthest?", "the Arctic tern",
      "The Arctic tern makes the longest migration of any animal",
      "PARAFFRAZ: furthest = longest."),
     ("How heavy are the tracking devices?", "1.4 grams",
      "Tracking devices weighing only 1.4 grams",
      "«How heavy» — og'irlik."),
     ("What do the winding routes make use of?", "prevailing winds",
      "birds follow winding paths that exploit prevailing winds",
      "PARAFFRAZ: make use of = exploit."),
     ("How far does the tern fly each year?", "seventy thousand",
      "the annual distance reaches about seventy thousand "
      "kilometres", "«How far» — masofa."),
     ("How long does the bird live?", "thirty years",
      "Because the bird lives for some thirty years",
      "«How long» — umr davomiyligi.")],
))

# --------------------------------------------------------------- 18
PASSAGES.append(P(
    18, "THE SILK ROAD",
    "The name Silk Road was invented in 1877 by the German geographer "
    "Ferdinand von Richthofen; the merchants themselves never used "
    "it. Nor was it a single road, but a shifting network of routes "
    "across Central Asia. Few traders travelled its whole length: "
    "goods passed from hand to hand, so that silk reaching Rome might "
    "have changed owner a dozen times. Ideas moved with the cargo — "
    "Buddhism spread from India into China along these paths — and so "
    "did disease, most notoriously the plague that reached Europe in "
    "the fourteenth century.",
    [("Who invented the name?", "von Richthofen",
      "invented in 1877 by the German geographer Ferdinand von "
      "Richthofen", "«Who» — odam. Familiya yetarli."),
     ("What was it in reality, instead of a single road?",
      "network",
      "Nor was it a single road, but a shifting network of routes",
      "PARAFFRAZ: in reality = but."),
     ("How many times might silk change owner before reaching "
      "Rome?", "a dozen",
      "silk reaching Rome might have changed owner a dozen times",
      "«How many times» — necha marta."),
     ("Which religion spread from India to China?", "Buddhism",
      "Buddhism spread from India into China along these paths",
      "Din nomi."),
     ("What disease reached Europe along it?", "the plague",
      "most notoriously the plague that reached Europe",
      "Kasallik nomi.")],
))

# --------------------------------------------------------------- 19
PASSAGES.append(P(
    19, "CORAL BLEACHING",
    "Corals owe their colour, and up to ninety percent of their "
    "energy, to microscopic algae living inside their tissue. When "
    "the water is even one degree above the usual summer maximum for "
    "several weeks, the relationship breaks down and the algae are "
    "expelled, leaving the white skeleton visible through the "
    "transparent flesh. Bleached coral is not dead and can regain its "
    "partners if conditions improve within about six weeks. The "
    "Australian reef suffered mass bleaching in 1998, 2002, 2016, "
    "2017 and 2020; before 1998 no such event had been recorded.",
    [("How much of the coral's energy comes from algae?",
      "ninety percent",
      "Corals owe their colour, and up to ninety percent of their "
      "energy, to microscopic algae",
      "PARAFFRAZ: how much = up to."),
     ("In which part of the coral do the algae live?", "tissue",
      "microscopic algae living inside their tissue",
      "«Which part» — tana qismi."),
     ("What becomes visible when the algae go?", "the white skeleton",
      "leaving the white skeleton visible",
      "Nima ko'rinadi."),
     ("How long does coral have to recover?", "six weeks",
      "can regain its partners if conditions improve within about "
      "six weeks", "«How long» — muddat."),
     ("When was the first mass bleaching recorded?", "1998",
      "before 1998 no such event had been recorded",
      "Chalg'ituvchi: 2002, 2016, 2017, 2020 ham bor.")],
))

# --------------------------------------------------------------- 20
PASSAGES.append(P(
    20, "THE JAMES WEBB TELESCOPE",
    "Unlike Hubble, which orbits the Earth, the James Webb telescope "
    "was placed 1.5 million kilometres away at a gravitational "
    "balance point, far beyond any possibility of repair. Its mirror, "
    "6.5 metres across, was too large for any rocket and had to be "
    "folded; unfolding it after launch required 344 separate "
    "mechanisms, each of which had to work first time. A five-layer "
    "sunshield the size of a tennis court keeps the instruments at "
    "minus 233 degrees, cold enough to detect the faint infrared "
    "light of galaxies formed shortly after the Big Bang. The project "
    "took twenty-five years and cost about ten billion dollars.",
    [("How far from Earth is the telescope?", "1.5 million",
      "was placed 1.5 million kilometres away",
      "«How far» — masofa."),
     ("How wide is the mirror?", "6.5 metres",
      "Its mirror, 6.5 metres across",
      "«How wide» — kenglik. Chalg'ituvchi: 344, 233, 25."),
     ("How many mechanisms unfolded it?", "344",
      "unfolding it after launch required 344 separate mechanisms",
      "«How many» — son."),
     ("What is the sunshield compared to in size?",
      "a tennis court",
      "A five-layer sunshield the size of a tennis court",
      "Taqqoslash ob'yekti."),
     ("What kind of light does the telescope detect?", "infrared",
      "cold enough to detect the faint infrared light",
      "Nur turi."),
     ("How long did the project take?", "twenty-five years",
      "The project took twenty-five years",
      "«How long» — davomiylik. Chalg'ituvchi: «ten billion» — "
      "narx.")],
))


# =====================================================================
#  YIG'ISH
# =====================================================================
ALT = {
    "a hundred": "one hundred", "four thousand": "4000",
    "two thousand": "2000", "five hundred": "500",
    "nine million": "9 million", "seventy thousand": "70,000",
    "twelve seconds": "12 seconds", "thirty years": "30 years",
    "twenty-five years": "25 years", "two weeks": "2 weeks",
    "six weeks": "6 weeks", "fifty-six kilometres": "56 kilometres",
    "forty kilometres": "40 kilometres", "a quarter": "one quarter",
    "a fifth": "one fifth", "ninety percent": "90 percent",
    "von Richthofen": "Ferdinand von Richthofen",
    "1.5 million": "1,500,000",
}


def _cefr(level):
    if level <= 4:
        return "A2"
    if level <= 9:
        return "B1"
    if level <= 14:
        return "B2"
    return "C1"


def build_rows():
    out = []
    for p in PASSAGES:
        qs = [q[0] for q in p["qs"]]
        for i, (q, ans, psg, note) in enumerate(p["qs"], 1):
            payload = {
                "title": p["title"],
                "passage": p["text"],
                # Butun savollar ro'yxati ko'rinadi (joriy savol
                # ajratiladi) — "savollar matn tartibida" qoidasi
                # amalda ishlashi uchun.
                "questions": qs,
                "q_no": i,
                "prompt": q,
                "step": p["level"],
                "order": i - 1,
                "step_title": f"{p['level']}-daraja",
                "tip": "Savol so'ziga qarang",
                "instruction": ("Answer the question. Choose NO MORE "
                                "THAN TWO WORDS AND/OR A NUMBER from "
                                "the passage."),
            }
            explain = f"Savolda: «{q}»  ->  Matnda: «{psg}». {note}"
            out.append((KIND, _cefr(p["level"]), payload, ans,
                        explain, ALT.get(ans, ""),
                        {"table": q, "passage": psg}))
    return out


def seed_reading_short(db):
    """Idempotent: (kind, passage, q_no) bo'yicha."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_read_short_v1"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            pl = json.loads(p)
            have.add((k, pl.get("passage"), pl.get("q_no")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain, alt, para in build_rows():
        key = (kind, payload["passage"], payload["q_no"])
        if key in have:
            continue
        payload = dict(payload)
        payload["paraphrase"] = para
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt or None, explain=explain))
        have.add(key)
        made += 1
    if made:
        db.commit()
    _seed_mark(db, "ielts_read_short_v1")
    return made
