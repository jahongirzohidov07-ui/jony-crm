# -*- coding: utf-8 -*-
"""IELTS READING — FLOW-CHART COMPLETION (2026-08-25).

Jahongir: "mana Flowchart completion uchun misol senga shunda sal
osonlashtirib buni 5-ga qoyda undan oldingilarni sal osonlashtirib,
umumiy qiyindan osonga qarab ketgizish kerak."

TUZILISHI. 20 ta sxema, jami 103 bo'shliq, daraja 1..20:
  1-4    — Jahongir yuborgan namunadan OSONROQ (qisqa matn, oddiy
           ketma-ketlik);
  5      — "READING #5. Freya Stark" (namunaning o'zi);
  6      — "READING #7. Patrick Malone (Part 1)";
  7      — "READING #8. Patrick Malone (Part 2)";
  8-20   — qiyinlashib boradi: jarayon sxemalari, ilmiy matnlar,
           ko'p sonli chalg'ituvchi sana va raqamlar.

BU TURNING O'ZIGA XOSLIGI. Flow-chart — bu KETMA-KETLIK: har quti
oldingisidan keyin sodir bo'lgan voqeani bildiradi. Shuning uchun
javob matnda ham SHU TARTIBDA keladi. Jadval va xulosadan farqi
shu — bu yerda tartib qat'iy va u eng kuchli yordamchi.

Javob ikki so'zgacha bo'lishi mumkin (NO MORE THAN TWO WORDS AND/OR
A NUMBER) — jadval va xulosadagi "bitta so'z" qoidasidan farqi shu.

Paraffraz izohi har mashqda saqlanib qoladi.
"""

SKILL = "ielts_reading"
KIND = "read_flow"
GAP = "______"

SEP = "↓"          # pastga strelka

# =====================================================================
#  QOIDALAR
# =====================================================================
FLOW_TIPS = [
    ("Flow-chart nima",
     "Voqealar yoki jarayon bosqichlari yuqoridan pastga qutilar "
     "bilan chiziladi, strelka «keyin nima bo'ldi» degan ma'noni "
     "beradi. Bo'sh qutini MATNDAN olingan so'z bilan "
     "to'ldirasiz.",
     "Born in Paris in 1893\n"
     "  " + SEP + "\nFirst formal education at ______\n"
     "Matn: «She entered London University in 1912»\n"
     "Javob: London University"),
    ("ENG KUCHLI YORDAMCHI — TARTIB",
     "Flow-chart har doim matn ketma-ketligini kuzatadi. 3-javobni "
     "topdingizmi — 4-javob matnda undan KEYIN turadi, oldin emas. "
     "Jadval va xulosada tartib buzilishi mumkin edi, bu yerda "
     "esa yo'q. Shuning uchun topilgan javobingizdan keyin "
     "o'qishda davom eting, boshiga qaytmang.", ""),
    ("Ikki so'zgacha ruxsat",
     "«NO MORE THAN TWO WORDS AND/OR A NUMBER» — javob bitta yoki "
     "ikkita so'z, yoki son bo'lishi mumkin: «London University», "
     "«1,400 kilometres», «Gold Medal», «12 years». Uchta so'z "
     "yozsangiz javob noto'g'ri sanaladi.", ""),
    ("Quti FE'L bilan boshlansa — fe'l kerak",
     "Ba'zi qutilar «______ a tribe that nobody knew existed» "
     "ko'rinishida boshlanadi. Bu yerda FE'L kerak va uni matndagi "
     "shaklga moslash lozim: matnda «The group discovered» bo'lsa, "
     "javob «Discovered».",
     "Quti: «______ someone he met on a trip»\n"
     "Matn: «he married Margaret Logan, an American doctor he had "
     "met while travelling»\nJavob: Married"),
    ("PARAFFRAZ baribir kerak",
     "Qutidagi ibora matnda aynan takrorlanmaydi: «First formal "
     "education at» -> «She entered London University in 1912»; "
     "«on foot» -> «he walked». Avval ma'noni oling, keyin "
     "matndan qidiring.", ""),
    ("Sana va son ko'p bo'ladi",
     "Tarjimai holda 1893, 1912, 1927, 1928, 1934 kabi sanalar "
     "ketma-ket keladi. Quti qaysi bosqichda turganiga qarab "
     "kerakli sonni tanlang — birinchi ko'ringanini yozmang.", ""),
    ("Bo'sh QUTILAR ham yo'l ko'rsatadi",
     "To'ldirilgan qutilar (masalan «Studied at School of Oriental "
     "Studies») matndagi o'rningizni aniqlaydi. Javobingiz "
     "shulardan oldin yoki keyin bo'lishi kerak.", ""),
    ("So'z shaklini o'zgartirmang",
     "Matnda «a distance of over 1,400 kilometres» bo'lsa, javob "
     "«1,400 kilometres» — «1400 km» emas. Ko'plikni ham "
     "matndagidek qoldiring.", ""),
]


def P(level, title, text, flow_title, boxes, gaps):
    return {"level": level, "title": title, "text": text,
            "flow_title": flow_title, "boxes": boxes, "gaps": gaps}


PASSAGES = []

# ---------------------------------------------------------------- 1
PASSAGES.append(P(
    1, "A STUDENT'S MORNING",
    "Dilnoza gets up at half past six. First she washes and gets "
    "dressed. Then she has breakfast with her brother — usually "
    "bread and tea. She leaves the house at ten past seven and walks "
    "to the bus stop. The bus takes her to school, where lessons "
    "begin at eight.",
    "Dilnoza's morning",
    ["Gets up at 6.30",
     "Washes and gets ___1",
     "Has ___2 with her brother",
     "Leaves home at ___3 past seven",
     "Walks to the ___4",
     "Lessons start at ___5"],
    [(1, "dressed", "Washes and gets ______",
      "First she washes and gets dressed", "Ketma-ketlikning "
      "birinchi bosqichi."),
     (2, "breakfast", "Has ______ with her brother",
      "Then she has breakfast with her brother",
      "Strelka «keyin» degani — matnda ham «Then»."),
     (3, "ten", "Leaves home at ______ past seven",
      "She leaves the house at ten past seven",
      "Vaqt matnda so'z bilan yozilgan."),
     (4, "bus stop", "Walks to the ______",
      "walks to the bus stop", "Ikki so'zli javob."),
     (5, "eight", "Lessons start at ______",
      "lessons begin at eight", "PARAFFRAZ: start = begin.")],
))

# ---------------------------------------------------------------- 2
PASSAGES.append(P(
    2, "JOINING THE LIBRARY",
    "To become a member of the city library you first fill in a short "
    "form at the desk. You must then show a document with your "
    "address on it, such as a bill. The librarian takes your "
    "photograph, and a card is printed while you wait. Finally you "
    "sign the card and you can borrow up to six books.",
    "How to join the library",
    ["Complete a ___1 at the desk",
     "Show proof of your ___2",
     "Have your ___3 taken",
     "Card is ___4 immediately",
     "Sign it and borrow up to ___5 books"],
    [(1, "form", "Complete a ______ at the desk",
      "you first fill in a short form at the desk",
      "PARAFFRAZ: complete = fill in."),
     (2, "address", "Show proof of your ______",
      "show a document with your address on it",
      "PARAFFRAZ: proof = document."),
     (3, "photograph", "Have your ______ taken",
      "The librarian takes your photograph", "Uchinchi bosqich."),
     (4, "printed", "Card is ______ immediately",
      "a card is printed while you wait",
      "PARAFFRAZ: immediately = while you wait."),
     (5, "six", "borrow up to ______ books",
      "you can borrow up to six books", "Oxirgi bosqich.")],
))

# ---------------------------------------------------------------- 3
PASSAGES.append(P(
    3, "MAKING BREAD",
    "The baker begins by mixing flour, water, salt and yeast in a "
    "large bowl. The dough is then kneaded for about ten minutes "
    "until it is smooth. It is left in a warm place for an hour so "
    "that it can rise. After that it is shaped into loaves and put "
    "into a hot oven for thirty minutes. The bread is cooled on a "
    "wire rack before it is sold.",
    "How bread is made",
    ["Mix flour, water, salt and ___1",
     "Knead for about ___2 minutes",
     "Leave in a ___3 place for an hour",
     "Shape into ___4",
     "Bake for ___5 minutes",
     "Cool on a wire rack"],
    [(1, "yeast", "Mix flour, water, salt and ______",
      "mixing flour, water, salt and yeast", "Ro'yxatning oxiri."),
     (2, "ten", "Knead for about ______ minutes",
      "kneaded for about ten minutes",
      "Chalg'ituvchi: «thirty» — pishirish vaqti."),
     (3, "warm", "Leave in a ______ place",
      "It is left in a warm place for an hour", "Sifat kerak."),
     (4, "loaves", "Shape into ______",
      "it is shaped into loaves", "Ko'plik shaklini saqlang."),
     (5, "thirty", "Bake for ______ minutes",
      "put into a hot oven for thirty minutes",
      "PARAFFRAZ: bake = put into a hot oven.")],
))

# ---------------------------------------------------------------- 4
PASSAGES.append(P(
    4, "SAM'S FOOTBALL CAREER",
    "Sam Coyle was born in Dublin in 1994. He joined a local youth "
    "club at the age of nine and was noticed by a scout four years "
    "later. At sixteen he signed for a professional team in England, "
    "but a knee injury kept him out of the game for a whole season. "
    "He returned in 2015 and became captain three years after that. "
    "He now coaches children in his old club.",
    "Sam Coyle",
    ["Born in Dublin in 1994",
     "Joined a youth club aged ___1",
     "Spotted by a ___2",
     "Signed for an English club at ___3",
     "Missed a season because of a ___4",
     "Became ___5 in 2018",
     "Now works as a coach"],
    [(1, "nine", "Joined a youth club aged ______",
      "He joined a local youth club at the age of nine",
      "PARAFFRAZ: aged = at the age of."),
     (2, "scout", "Spotted by a ______",
      "was noticed by a scout four years later",
      "PARAFFRAZ: spotted = noticed."),
     (3, "sixteen", "Signed for an English club at ______",
      "At sixteen he signed for a professional team in England",
      "Chalg'ituvchi: «four years later» — yosh emas."),
     (4, "knee injury", "Missed a season because of a ______",
      "a knee injury kept him out of the game for a whole season",
      "Ikki so'zli javob."),
     (5, "captain", "Became ______ in 2018",
      "He returned in 2015 and became captain three years after "
      "that", "2015 + 3 = 2018 — sanani hisoblash kerak.")],
))

# ---------------------------------------------------------------- 5
#  JAHONGIRNING NAMUNASI — READING #5
PASSAGES.append(P(
    5, "READING #5. FREYA STARK, EXPLORER AND WRITER",
    "Freya Stark was an explorer who lived during a time when "
    "explorers were regarded as heroes. She travelled to distant "
    "areas of the Middle East, where few Europeans - especially "
    "women - had travelled before. She also travelled extensively in "
    "Turkey, Greece, Italy, Nepal and Afghanistan.\n\n"
    "Stark was born in Paris in 1893. Although she had no formal "
    "education as a child, she moved about with her artist parents "
    "and learned French, German and Italian. She entered London "
    "University in 1912, but at the start of World War I, she joined "
    "the nurse corps and was sent to Italy. After the war, she "
    "returned to London and attended the School of Oriental Studies. "
    "Her studies there led to extensive travel in the Middle East, "
    "enabling her to eventually become fluent in Persian, Russian "
    "and Turkish.\n\n"
    "Stark became well known as a traveler and explorer in the "
    "Middle East. She travelled to the Lebanon in 1927 at the age of "
    "33 when she had saved enough money, and while there, she "
    "studied Arabic.\n\n"
    "In 1928, she travelled by donkey to the Jebel Druze, a "
    "mountainous area in Syria. During another trip, she went to a "
    "distant region of the Elburz, a mountain range in Iran, where "
    "she made a map. She was searching for information about an "
    "ancient Muslim sect known as the Assassins, which she wrote "
    "about in Valley of the Assassins (1934), a classic for which "
    "she was awarded a Gold Medal by the Royal Geographic Society. "
    "For the next 12 years, she continued her career as a traveler "
    "and writer, establishing a style which combined an account of "
    "her journeys with personal commentary on the people, customs, "
    "history and politics of the Middle East.",
    "Freya Stark",
    ["Born in Paris in 1893",
     "First formal education at ___1",
     "Worked as a ___2 in Italy",
     "Studied at School of Oriental Studies",
     "Travelled to the Lebanon, where she learned ___3",
     "Made a journey to the Syrian mountains on a ___4",
     "In 1934, won a ___5 for a book",
     "Spent a further ___6 in the Middle East"],
    [(1, "London University", "First formal education at ______",
      "She entered London University in 1912",
      "PARAFFRAZ: «no formal education as a child» deyilgan, "
      "demak BIRINCHI rasmiy ta'lim — universitet."),
     (2, "nurse", "Worked as a ______ in Italy",
      "she joined the nurse corps and was sent to Italy",
      "PARAFFRAZ: worked as = joined the ... corps."),
     (3, "Arabic", "where she learned ______",
      "she had saved enough money, and while there, she studied "
      "Arabic", "PARAFFRAZ: learned = studied."),
     (4, "donkey", "on a ______",
      "In 1928, she travelled by donkey to the Jebel Druze, a "
      "mountainous area in Syria",
      "PARAFFRAZ: Syrian mountains = a mountainous area in Syria."),
     (5, "Gold Medal", "won a ______ for a book",
      "a classic for which she was awarded a Gold Medal by the "
      "Royal Geographic Society",
      "PARAFFRAZ: won = was awarded. Ikki so'zli javob."),
     (6, "12 years", "Spent a further ______",
      "For the next 12 years, she continued her career",
      "PARAFFRAZ: a further = the next.")],
))

# ---------------------------------------------------------------- 6
#  JAHONGIRNING NAMUNASI — READING #7
PASSAGES.append(P(
    6, "READING #7. PATRICK MALONE (PART 1)",
    "Patrick Malone is a traveller, writer and broadcaster. He was "
    "born in 1968 in Basel, Switzerland, where his British parents "
    "were working for a pharmaceutical company. His family left "
    "Switzerland when he was twelve, and returned to their home in "
    "Britain. For the next six years, Malone attended the local "
    "secondary school. He then went to Leeds University to do a "
    "course in Human Geography. He wanted to become a town planner. "
    "However, the only work he could find was as a teacher at a "
    "local school.\n\n"
    "During his holidays and free time, he went walking, often "
    "covering very long distances very quickly. On one occasion he "
    "walked the entire length of Britain, a distance of over 1,400 "
    "kilometres, in less than a month. He enjoyed the experience and "
    "the challenge so much that he started walking in different "
    "parts of the world, usually in fairly remote areas away from "
    "major population centres. The people he met and the experiences "
    "he had on these trips provided him with some excellent material "
    "for his classes.\n\n"
    "It was during one trip that he met his old university tutor, "
    "Don Perkins. At the time, Perkins was putting together a team "
    "of geographers and biologists for a research trip to the "
    "Amazon, and asked Malone if he would like to go with them. The "
    "expedition was for a whole year, and so he had to give up his "
    "job at the school, but Malone did not hesitate to accept "
    "Perkins' offer. He sold his car to make some money, bought an "
    "airline ticket for Brazil and set off.",
    "Patrick Malone",
    ["Born in Switzerland in 1968",
     "Moved to ___1 when he was twelve",
     "Studied ___2 at university",
     "Got a job as a ___3",
     "Once travelled more than ___4 on foot on a single trip",
     "Often went walking in places that were quite ___5",
     "Joined an ___6 to the Amazon"],
    [(1, "Britain", "Moved to ______ when he was twelve",
      "His family left Switzerland when he was twelve, and "
      "returned to their home in Britain",
      "PARAFFRAZ: moved to = returned to."),
     (2, "Human Geography", "Studied ______ at university",
      "He then went to Leeds University to do a course in Human "
      "Geography", "PARAFFRAZ: studied = do a course in."),
     (3, "teacher", "Got a job as a ______",
      "the only work he could find was as a teacher at a local "
      "school", "PARAFFRAZ: got a job = the only work he could "
      "find. Chalg'ituvchi: «town planner» — u BO'LMOQCHI edi."),
     (4, "1,400 kilometres", "travelled more than ______ on foot",
      "he walked the entire length of Britain, a distance of over "
      "1,400 kilometres",
      "PARAFFRAZ: on foot = walked; more than = over."),
     (5, "remote", "places that were quite ______",
      "usually in fairly remote areas away from major population "
      "centres", "PARAFFRAZ: quite = fairly."),
     (6, "expedition", "Joined an ______ to the Amazon",
      "The expedition was for a whole year",
      "PARAFFRAZ: joined = accepted the offer to go with them.")],
))

# ---------------------------------------------------------------- 7
#  JAHONGIRNING NAMUNASI — READING #8
PASSAGES.append(P(
    7, "READING #8. PATRICK MALONE (PART 2)",
    "The Amazon expedition, which took six months and covered a "
    "distance of almost 2,500 kilometres, was a great success. The "
    "group discovered some new plant and insect species, as well as "
    "a forest tribe which people had never heard of. Malone enjoyed "
    "the trip so much that he decided to become a full-time "
    "explorer. He earned money by writing travel articles for "
    "magazines and newspapers, which he illustrated with his own "
    "photographs.\n\n"
    "In 1996, he married Margaret Logan, an American doctor he had "
    "met while travelling around Africa. In 1998 they had Adam, the "
    "first of three children (twins Amelia and Jennifer were born a "
    "year later). Many families at this stage would settle down, but "
    "Margaret and Patrick decided to keep travelling, spending two "
    "years walking around India and another twelve months exploring "
    "the islands of Indonesia.\n\n"
    "When they returned home, they wrote a magazine article about "
    "travelling with small children. It was so popular that they "
    "were asked to write several more articles on the same subject. "
    "This was followed by an offer from a television company to "
    "present a TV series about travelling with children. The series "
    "ran for 12 years, and won several television awards. Today they "
    "still make the most of every opportunity to travel, and have "
    "recently returned from the South Pacific.",
    "Patrick Malone (continued)",
    ["Travelled 2,500 kilometres through the Amazon",
     "___1 a tribe that nobody knew existed",
     "___2 someone he met on a trip",
     "They had ___3: Adam, Amelia and Jennifer",
     "Explored the Indonesian islands for ___4",
     "Made a successful ___5",
     "Still likes to ___6 whenever possible"],
    [(1, "Discovered", "______ a tribe that nobody knew existed",
      "The group discovered some new plant and insect species, as "
      "well as a forest tribe which people had never heard of",
      "PARAFFRAZ: nobody knew existed = people had never heard of. "
      "Quti fe'l bilan boshlanadi."),
     (2, "Married", "______ someone he met on a trip",
      "he married Margaret Logan, an American doctor he had met "
      "while travelling around Africa", "Fe'l kerak."),
     (3, "three children", "They had ______",
      "In 1998 they had Adam, the first of three children",
      "Ikki so'zli javob; «3 children» ham qabul qilinadi."),
     (4, "twelve months", "Explored the Indonesian islands for "
      "______",
      "another twelve months exploring the islands of Indonesia",
      "Chalg'ituvchi: «two years» — Hindiston uchun."),
     (5, "TV series", "Made a successful ______",
      "an offer from a television company to present a TV series "
      "about travelling with children",
      "«television series» ham to'g'ri."),
     (6, "travel", "Still likes to ______ whenever possible",
      "Today they still make the most of every opportunity to "
      "travel", "PARAFFRAZ: whenever possible = every "
      "opportunity.")],
))

# ---------------------------------------------------------------- 8
PASSAGES.append(P(
    8, "HOW GLASS IS RECYCLED",
    "Used bottles and jars are collected from household bins and "
    "taken to a processing plant. There they are sorted by colour, "
    "since mixing colours lowers the value of the material. Metal "
    "lids are removed by a magnet and paper labels are burned off. "
    "The clean glass is then crushed into small pieces called "
    "cullet. Cullet melts at a lower temperature than raw sand, "
    "which saves fuel. Finally the molten glass is poured into "
    "moulds to form new containers.",
    "Glass recycling",
    ["Bottles collected from household bins",
     "Taken to a ___1",
     "Separated according to ___2",
     "Lids taken off with a ___3; labels burned",
     "Crushed into pieces known as ___4",
     "Melted — uses less ___5 than raw sand",
     "Poured into moulds"],
    [(1, "processing plant", "Taken to a ______",
      "taken to a processing plant", "Ikki so'zli javob."),
     (2, "colour", "Separated according to ______",
      "they are sorted by colour",
      "PARAFFRAZ: separated according to = sorted by."),
     (3, "magnet", "Lids taken off with a ______",
      "Metal lids are removed by a magnet",
      "PARAFFRAZ: taken off = removed."),
     (4, "cullet", "pieces known as ______",
      "crushed into small pieces called cullet",
      "PARAFFRAZ: known as = called."),
     (5, "fuel", "uses less ______ than raw sand",
      "Cullet melts at a lower temperature than raw sand, which "
      "saves fuel", "PARAFFRAZ: uses less = saves.")],
))

# ---------------------------------------------------------------- 9
PASSAGES.append(P(
    9, "MARIE CURIE",
    "Maria Sklodowska was born in Warsaw in 1867. Women could not "
    "enter Polish universities, so she worked for several years as a "
    "governess to pay for her sister's studies in Paris. In 1891 she "
    "followed her there and enrolled at the Sorbonne, living in an "
    "unheated attic. She married Pierre Curie in 1895. Working in a "
    "converted shed, the couple isolated two new elements, polonium "
    "and radium, and shared the Nobel Prize for Physics in 1903. "
    "After Pierre's death in a street accident she took over his "
    "professorship, becoming the first woman to teach at the "
    "Sorbonne, and won a second Nobel Prize, this time for "
    "Chemistry, in 1911.",
    "Marie Curie",
    ["Born in Warsaw in 1867",
     "Worked as a ___1 to fund her sister",
     "Moved to Paris and studied at the ___2",
     "Married Pierre Curie in ___3",
     "Isolated polonium and ___4",
     "Won her first Nobel Prize in 1903",
     "Became the first woman to ___5 at the Sorbonne",
     "Won a second prize for ___6 in 1911"],
    [(1, "governess", "Worked as a ______ to fund her sister",
      "she worked for several years as a governess to pay for her "
      "sister's studies", "PARAFFRAZ: fund = pay for."),
     (2, "Sorbonne", "studied at the ______",
      "she followed her there and enrolled at the Sorbonne",
      "PARAFFRAZ: studied at = enrolled at."),
     (3, "1895", "Married Pierre Curie in ______",
      "She married Pierre Curie in 1895",
      "Chalg'ituvchi: 1891, 1903, 1911."),
     (4, "radium", "Isolated polonium and ______",
      "the couple isolated two new elements, polonium and radium",
      "Ro'yxatning ikkinchisi."),
     (5, "teach", "the first woman to ______ at the Sorbonne",
      "becoming the first woman to teach at the Sorbonne",
      "Fe'l kerak."),
     (6, "Chemistry", "a second prize for ______ in 1911",
      "won a second Nobel Prize, this time for Chemistry, in 1911",
      "Chalg'ituvchi: birinchisi Fizika edi.")],
))

# --------------------------------------------------------------- 10
PASSAGES.append(P(
    10, "APPLYING FOR A PASSPORT",
    "Applicants download the form from the government website or "
    "collect a paper copy from a post office. The completed form must "
    "be signed by a referee who has known the applicant for at least "
    "two years and who is not a relative. Two identical photographs "
    "are required; these must have been taken within the last month. "
    "The application, the fee of 82 pounds and the applicant's birth "
    "certificate are then posted to the processing centre. Standard "
    "applications take about three weeks, although an urgent service "
    "delivers within one week for an extra charge.",
    "Passport application",
    ["Obtain the form online or from a ___1",
     "Form signed by a ___2 who is not a family member",
     "Provide two matching ___3, taken in the past month",
     "Post the form, the ___4 of 82 pounds and a birth certificate",
     "Normal processing takes about ___5"],
    [(1, "post office", "online or from a ______",
      "collect a paper copy from a post office", "Ikki so'z."),
     (2, "referee", "signed by a ______",
      "must be signed by a referee who has known the applicant for "
      "at least two years and who is not a relative",
      "PARAFFRAZ: family member = relative."),
     (3, "photographs", "two matching ______",
      "Two identical photographs are required",
      "PARAFFRAZ: matching = identical."),
     (4, "fee", "the ______ of 82 pounds",
      "the fee of 82 pounds", "To'lov nomi."),
     (5, "three weeks", "takes about ______",
      "Standard applications take about three weeks",
      "Chalg'ituvchi: «one week» — shoshilinch xizmat.")],
))

# --------------------------------------------------------------- 11
PASSAGES.append(P(
    11, "FROM BEAN TO CUP",
    "Coffee cherries are picked by hand when they turn deep red. The "
    "outer fruit is stripped away in a pulping machine, leaving the "
    "beans covered in a sticky layer. This is broken down by soaking "
    "the beans in tanks of water for up to two days, a stage known as "
    "fermentation. The beans are then dried in the sun until their "
    "moisture content falls to about eleven percent. Once dry, they "
    "are graded by size and exported green, because roasted beans "
    "lose their flavour quickly. Roasting takes place close to the "
    "consumer, often only days before sale.",
    "Coffee production",
    ["Cherries picked by hand when deep ___1",
     "Fruit removed in a ___2",
     "Beans soaked in water — a stage called ___3",
     "Dried until moisture reaches about ___4 percent",
     "Sorted by ___5 and shipped green",
     "Roasted near the ___6"],
    [(1, "red", "when deep ______",
      "picked by hand when they turn deep red", "Rang."),
     (2, "pulping machine", "Fruit removed in a ______",
      "The outer fruit is stripped away in a pulping machine",
      "PARAFFRAZ: removed = stripped away. Ikki so'z."),
     (3, "fermentation", "a stage called ______",
      "a stage known as fermentation",
      "PARAFFRAZ: called = known as."),
     (4, "eleven", "moisture reaches about ______ percent",
      "until their moisture content falls to about eleven percent",
      "PARAFFRAZ: reaches = falls to. Chalg'ituvchi: «two days»."),
     (5, "size", "Sorted by ______",
      "they are graded by size and exported green",
      "PARAFFRAZ: sorted = graded."),
     (6, "consumer", "Roasted near the ______",
      "Roasting takes place close to the consumer",
      "PARAFFRAZ: near = close to.")],
))

# --------------------------------------------------------------- 12
PASSAGES.append(P(
    12, "THE LIFE OF A SALMON",
    "Salmon eggs are laid in gravel on the bed of a fast-flowing "
    "river. The young fish that hatch, known as alevins, live off a "
    "yolk sac for several weeks before they begin to feed. As they "
    "grow they develop dark markings which act as camouflage. After "
    "one to three years in fresh water, their bodies change so that "
    "they can survive in salt water; at this point they are called "
    "smolts and they swim downstream to the ocean. They spend up to "
    "four years at sea, feeding and growing, before navigating back "
    "to the exact river where they hatched, guided largely by smell.",
    "The salmon's life cycle",
    ["Eggs laid in ___1 on the river bed",
     "Newly hatched fish, called ___2, feed on a yolk sac",
     "Dark markings develop, providing ___3",
     "Bodies adapt to ___4 water; fish now called smolts",
     "Up to ___5 years spent in the ocean",
     "Return to birth river, mainly using ___6"],
    [(1, "gravel", "Eggs laid in ______",
      "Salmon eggs are laid in gravel on the bed of a "
      "fast-flowing river", "Joy."),
     (2, "alevins", "called ______",
      "The young fish that hatch, known as alevins",
      "PARAFFRAZ: called = known as."),
     (3, "camouflage", "providing ______",
      "they develop dark markings which act as camouflage",
      "PARAFFRAZ: providing = act as."),
     (4, "salt", "Bodies adapt to ______ water",
      "their bodies change so that they can survive in salt water",
      "PARAFFRAZ: adapt = change."),
     (5, "four", "Up to ______ years spent in the ocean",
      "They spend up to four years at sea",
      "Chalg'ituvchi: «one to three years» — chuchuk suvda."),
     (6, "smell", "mainly using ______",
      "navigating back to the exact river where they hatched, "
      "guided largely by smell",
      "PARAFFRAZ: mainly = largely.")],
))

# --------------------------------------------------------------- 13
PASSAGES.append(P(
    13, "AMELIA EARHART",
    "Amelia Earhart saw her first aeroplane at a state fair in 1908 "
    "and was unimpressed. Her interest began only after a ten-minute "
    "flight over Los Angeles in 1920, which she later said settled "
    "her future. She took lessons from Neta Snook, a pioneering "
    "female instructor, paying for them by working as a photographer "
    "and a truck driver. In 1928 she crossed the Atlantic as a "
    "passenger, an experience she dismissed as being 'like a sack of "
    "potatoes'. Four years later she repeated the flight alone, "
    "becoming the first woman to do so. Her attempt to circle the "
    "globe ended in 1937 when her aircraft disappeared over the "
    "Pacific.",
    "Amelia Earhart",
    ["Saw her first aeroplane in 1908 — she was ___1",
     "A short flight in ___2 changed her mind",
     "Learned to fly with ___3",
     "Paid for lessons by working as a photographer and a ___4",
     "Crossed the Atlantic as a ___5 in 1928",
     "Flew the same route ___6 in 1932",
     "Disappeared over the Pacific in 1937"],
    [(1, "unimpressed", "she was ______",
      "saw her first aeroplane at a state fair in 1908 and was "
      "unimpressed",
      "Matndagi so'z aynan olinadi — «un-» inkor qo'shimchasi "
      "bilan."),
     (2, "1920", "A short flight in ______",
      "after a ten-minute flight over Los Angeles in 1920",
      "PARAFFRAZ: short = ten-minute. Chalg'ituvchi: 1908."),
     (3, "Neta Snook", "Learned to fly with ______",
      "She took lessons from Neta Snook, a pioneering female "
      "instructor", "PARAFFRAZ: learned to fly with = took lessons "
      "from. Ikki so'z."),
     (4, "truck driver", "a photographer and a ______",
      "paying for them by working as a photographer and a truck "
      "driver", "Ikki so'z."),
     (5, "passenger", "Crossed the Atlantic as a ______ in 1928",
      "In 1928 she crossed the Atlantic as a passenger",
      "To'g'ridan-to'g'ri."),
     (6, "alone", "Flew the same route ______ in 1932",
      "Four years later she repeated the flight alone",
      "1928 + 4 = 1932; PARAFFRAZ: the same route = repeated the "
      "flight.")],
))

# --------------------------------------------------------------- 14
PASSAGES.append(P(
    14, "HOW A VACCINE IS DEVELOPED",
    "Researchers first identify a part of the pathogen, called an "
    "antigen, which the immune system can recognise. Candidate "
    "vaccines are then tested on cells and animals in what is termed "
    "the pre-clinical stage. Phase one trials involve a few dozen "
    "healthy volunteers and check only for safety. Phase two, with "
    "several hundred participants, establishes the correct dose. "
    "Phase three compares the vaccine with a placebo in thousands of "
    "people and provides the evidence regulators require. Even after "
    "approval, monitoring continues, because very rare side effects "
    "appear only when millions have been treated.",
    "Vaccine development",
    ["Identify a part of the pathogen, known as an ___1",
     "Test on cells and animals — the ___2 stage",
     "Phase 1: a few dozen volunteers, checks ___3 only",
     "Phase 2: several hundred people, finds the right ___4",
     "Phase 3: compared with a ___5 in thousands of people",
     "After approval, ___6 continues"],
    [(1, "antigen", "known as an ______",
      "a part of the pathogen, called an antigen",
      "PARAFFRAZ: known as = called."),
     (2, "pre-clinical", "the ______ stage",
      "tested on cells and animals in what is termed the "
      "pre-clinical stage", "PARAFFRAZ: known as = termed."),
     (3, "safety", "checks ______ only",
      "Phase one trials involve a few dozen healthy volunteers and "
      "check only for safety", "Nima tekshiriladi."),
     (4, "dose", "finds the right ______",
      "Phase two, with several hundred participants, establishes "
      "the correct dose",
      "PARAFFRAZ: finds the right = establishes the correct."),
     (5, "placebo", "compared with a ______",
      "Phase three compares the vaccine with a placebo",
      "To'g'ridan-to'g'ri."),
     (6, "monitoring", "______ continues",
      "Even after approval, monitoring continues",
      "Oxirgi bosqich.")],
))

# --------------------------------------------------------------- 15
PASSAGES.append(P(
    15, "PRODUCING A DAILY NEWSPAPER",
    "The day begins with a conference at which editors propose "
    "stories and the front page is provisionally agreed. Reporters "
    "then gather material, and every factual claim must be verified "
    "by a second source before it is used. Sub-editors cut the copy "
    "to fit the space available and write the headlines, a task that "
    "requires great compression. Pages are laid out on screen and "
    "sent electronically to printing plants around the country, "
    "usually before ten at night. Lorries distribute the copies "
    "overnight so that they reach shops by six in the morning.",
    "Making a newspaper",
    ["Morning ___1 — editors suggest stories",
     "Reporters collect material; every fact checked against a "
     "second ___2",
     "___3 shorten the text and write headlines",
     "Pages sent to ___4 by about ten p.m.",
     "___5 deliver copies during the night",
     "In shops by ___6 a.m."],
    [(1, "conference", "Morning ______",
      "The day begins with a conference at which editors propose "
      "stories", "PARAFFRAZ: suggest = propose."),
     (2, "source", "checked against a second ______",
      "every factual claim must be verified by a second source",
      "PARAFFRAZ: checked = verified."),
     (3, "Sub-editors", "______ shorten the text",
      "Sub-editors cut the copy to fit the space available",
      "PARAFFRAZ: shorten = cut."),
     (4, "printing plants", "Pages sent to ______",
      "sent electronically to printing plants around the country",
      "Ikki so'z."),
     (5, "Lorries", "______ deliver copies during the night",
      "Lorries distribute the copies overnight",
      "PARAFFRAZ: deliver = distribute; during the night = "
      "overnight."),
     (6, "six", "In shops by ______ a.m.",
      "so that they reach shops by six in the morning",
      "PARAFFRAZ: a.m. = in the morning.")],
))

# --------------------------------------------------------------- 16
PASSAGES.append(P(
    16, "ALAN TURING",
    "Turing published his paper on computable numbers in 1936, while "
    "still in his twenties; it set out the idea of a universal "
    "machine that could in principle perform any calculation. During "
    "the war he worked at Bletchley Park, where he designed an "
    "electromechanical device known as the Bombe, which reduced the "
    "time needed to break German naval codes from weeks to hours. "
    "After 1945 he moved to the National Physical Laboratory and "
    "drew up a detailed plan for a stored-programme computer. In "
    "1950 he proposed a test of machine intelligence based on "
    "whether a human interrogator could tell a computer from a "
    "person. He died in 1954.",
    "Alan Turing",
    ["1936: paper describing a ___1 machine",
     "Wartime work at ___2",
     "Designed a device called the ___3",
     "Code-breaking time cut from weeks to ___4",
     "After 1945: designed a ___5 computer at the NPL",
     "1950: suggested a test of machine ___6"],
    [(1, "universal", "a ______ machine",
      "it set out the idea of a universal machine that could in "
      "principle perform any calculation", "Sifat."),
     (2, "Bletchley Park", "Wartime work at ______",
      "During the war he worked at Bletchley Park",
      "PARAFFRAZ: wartime = during the war. Ikki so'z."),
     (3, "Bombe", "a device called the ______",
      "an electromechanical device known as the Bombe",
      "PARAFFRAZ: called = known as."),
     (4, "hours", "cut from weeks to ______",
      "reduced the time needed to break German naval codes from "
      "weeks to hours", "PARAFFRAZ: cut = reduced."),
     (5, "stored-programme", "designed a ______ computer",
      "drew up a detailed plan for a stored-programme computer",
      "PARAFFRAZ: designed = drew up a plan for."),
     (6, "intelligence", "a test of machine ______",
      "he proposed a test of machine intelligence",
      "PARAFFRAZ: suggested = proposed.")],
))

# --------------------------------------------------------------- 17
PASSAGES.append(P(
    17, "FROM FLEECE TO CLOTH",
    "The fleece is removed from the sheep in a single piece by "
    "shearers, who can handle a hundred animals in a day. It is then "
    "washed in warm water and detergent to remove grease and dirt, a "
    "process called scouring. The clean fibres are passed between "
    "rollers covered in fine wire teeth, which disentangle them and "
    "lay them parallel; this is carding. The resulting soft rope is "
    "drawn out and twisted into yarn, which gives it strength. "
    "Finally the yarn is woven on a loom, and the finished cloth is "
    "often treated with steam to stop it shrinking later.",
    "Wool processing",
    ["Fleece removed by ___1 in one piece",
     "Washed to remove grease — known as ___2",
     "Fibres straightened between rollers with wire ___3 (carding)",
     "Soft rope twisted into ___4 for strength",
     "Woven on a ___5",
     "Treated with ___6 to prevent shrinking"],
    [(1, "shearers", "Fleece removed by ______",
      "The fleece is removed from the sheep in a single piece by "
      "shearers", "Kim bajaradi."),
     (2, "scouring", "known as ______",
      "to remove grease and dirt, a process called scouring",
      "PARAFFRAZ: known as = called."),
     (3, "teeth", "rollers with wire ______",
      "passed between rollers covered in fine wire teeth",
      "To'g'ridan-to'g'ri."),
     (4, "yarn", "twisted into ______ for strength",
      "drawn out and twisted into yarn, which gives it strength",
      "PARAFFRAZ: for strength = which gives it strength."),
     (5, "loom", "Woven on a ______",
      "the yarn is woven on a loom", "Uskuna nomi."),
     (6, "steam", "Treated with ______ to prevent shrinking",
      "often treated with steam to stop it shrinking later",
      "PARAFFRAZ: prevent = stop.")],
))

# --------------------------------------------------------------- 18
PASSAGES.append(P(
    18, "ZAHA HADID",
    "Hadid studied mathematics in Beirut before moving to London in "
    "1972 to attend the Architectural Association. She opened her own "
    "practice in 1980, but for more than a decade her designs "
    "remained on paper: clients considered them unbuildable, and one "
    "competition victory in Cardiff was overturned by the local "
    "authority. Her first completed building, a fire station in "
    "Germany, opened in 1993. Advances in computer modelling "
    "gradually made her curved forms practical, and commissions "
    "multiplied. In 2004 she became the first woman to receive the "
    "Pritzker Prize, architecture's highest honour, and by her death "
    "in 2016 her office employed some four hundred people.",
    "Zaha Hadid",
    ["Studied ___1 in Beirut",
     "Moved to London in 1972 to attend the ___2",
     "Set up her own ___3 in 1980",
     "Designs thought to be ___4 by clients",
     "First finished building: a ___5 in Germany, 1993",
     "___6 modelling made her curved forms possible",
     "First woman to win the Pritzker Prize in 2004"],
    [(1, "mathematics", "Studied ______ in Beirut",
      "Hadid studied mathematics in Beirut", "Fan nomi."),
     (2, "Architectural Association", "to attend the ______",
      "moving to London in 1972 to attend the Architectural "
      "Association",
      "Maktab nomi — ikki so'zli javob."),
     (3, "practice", "Set up her own ______ in 1980",
      "She opened her own practice in 1980",
      "PARAFFRAZ: set up = opened."),
     (4, "unbuildable", "thought to be ______ by clients",
      "clients considered them unbuildable",
      "PARAFFRAZ: thought to be = considered."),
     (5, "fire station", "a ______ in Germany, 1993",
      "Her first completed building, a fire station in Germany, "
      "opened in 1993", "Ikki so'z."),
     (6, "Computer", "______ modelling made her curved forms "
      "possible",
      "Advances in computer modelling gradually made her curved "
      "forms practical",
      "PARAFFRAZ: possible = practical.")],
))

# --------------------------------------------------------------- 19
PASSAGES.append(P(
    19, "EARLY WARNING FOR EARTHQUAKES",
    "An earthquake releases two kinds of wave. The faster primary "
    "wave causes little damage; the slower secondary wave does most "
    "of the destruction. Sensors buried near known faults detect the "
    "primary wave and transmit the reading to a central computer, "
    "which estimates the magnitude within a few seconds. If the "
    "estimate exceeds a set threshold, an alert is broadcast to "
    "phones, trains and factories. Because radio signals travel far "
    "faster than seismic waves, distant cities may receive up to "
    "sixty seconds of notice, enough to halt trains and shut gas "
    "valves, though areas directly above the epicentre get almost no "
    "warning at all.",
    "Earthquake warning system",
    ["Faster ___1 wave arrives first, causing little damage",
     "___2 near faults detect it",
     "Reading sent to a central ___3",
     "___4 estimated within seconds",
     "If above a set ___5, an alert goes out",
     "Distant cities gain up to ___6 seconds"],
    [(1, "primary", "Faster ______ wave",
      "The faster primary wave causes little damage",
      "To'g'ridan-to'g'ri."),
     (2, "Sensors", "______ near faults detect it",
      "Sensors buried near known faults detect the primary wave",
      "Qurilma nomi."),
     (3, "computer", "sent to a central ______",
      "transmit the reading to a central computer",
      "PARAFFRAZ: sent = transmit."),
     (4, "Magnitude", "______ estimated within seconds",
      "which estimates the magnitude within a few seconds",
      "Nima baholanadi."),
     (5, "threshold", "If above a set ______",
      "If the estimate exceeds a set threshold",
      "PARAFFRAZ: above = exceeds."),
     (6, "sixty", "gain up to ______ seconds",
      "distant cities may receive up to sixty seconds of notice",
      "PARAFFRAZ: gain = receive.")],
))

# --------------------------------------------------------------- 20
PASSAGES.append(P(
    20, "THE PANAMA CANAL",
    "A French company under Ferdinand de Lesseps, fresh from success "
    "at Suez, began cutting a sea-level channel across Panama in "
    "1881. Disease proved decisive: an estimated twenty-two thousand "
    "workers died, most of them from yellow fever and malaria, and "
    "the enterprise collapsed in bankruptcy. The United States "
    "acquired the rights in 1904, but its first act was medical "
    "rather than engineering — a campaign led by William Gorgas "
    "eliminated the mosquito that carried the fever. American "
    "engineers also abandoned the sea-level plan in favour of a "
    "system of locks that lifts ships twenty-six metres to an "
    "artificial lake. The canal opened in 1914, cutting the voyage "
    "from New York to San Francisco by some thirteen thousand "
    "kilometres.",
    "The Panama Canal",
    ["1881: French begin a ___1 channel",
     "About ___2 workers die, mainly of yellow fever and malaria",
     "Project ends in ___3",
     "1904: the ___4 takes over the rights",
     "First step is medical — the ___5 carrying the fever is wiped "
     "out",
     "Sea-level plan replaced by a system of ___6",
     "Opened in 1914"],
    [(1, "sea-level", "begin a ______ channel",
      "began cutting a sea-level channel across Panama in 1881",
      "Loyiha turi."),
     (2, "twenty-two thousand", "About ______ workers die",
      "an estimated twenty-two thousand workers died",
      "PARAFFRAZ: about = an estimated. Ikki-uch so'zli son — "
      "«22,000» ham qabul qilinadi."),
     (3, "bankruptcy", "Project ends in ______",
      "the enterprise collapsed in bankruptcy",
      "PARAFFRAZ: ends = collapsed."),
     (4, "United States", "the ______ takes over the rights",
      "The United States acquired the rights in 1904",
      "PARAFFRAZ: takes over = acquired. Ikki so'z."),
     (5, "mosquito", "the ______ carrying the fever",
      "a campaign led by William Gorgas eliminated the mosquito "
      "that carried the fever", "PARAFFRAZ: wiped out = "
      "eliminated."),
     (6, "locks", "replaced by a system of ______",
      "abandoned the sea-level plan in favour of a system of locks",
      "PARAFFRAZ: replaced by = in favour of.")],
))


# =====================================================================
#  YIG'ISH
# =====================================================================
ALT = {
    "12 years": "twelve years",
    "three children": "3 children",
    "twelve months": "12 months",
    "TV series": "television series",
    "twenty-two thousand": "22,000",
    "1,400 kilometres": "1400 kilometers",
    "six": "6", "ten": "10", "nine": "9", "eleven": "11",
    "sixteen": "16", "thirty": "30", "four": "4", "sixty": "60",
    "eight": "8", "three weeks": "3 weeks",
}


def _mask(box, keep):
    s = str(box)
    for k in range(1, 12):
        s = s.replace(f"___{k}", GAP if k == keep else "…")
    return s


def _cefr(level):
    if level <= 4:
        return "A2"
    if level <= 9:
        return "B1"
    if level <= 14:
        return "B2"
    return "C1"


def _prompt_for(boxes, n, cue):
    mark = f"___{n}"
    for b in boxes:
        if mark in b:
            return _mask(b, n)
    return str(cue).replace("______", GAP)


def build_rows():
    out = []
    for p in PASSAGES:
        for i, (n, ans, cue, psg, note) in enumerate(p["gaps"]):
            payload = {
                "title": p["title"],
                "passage": p["text"],
                "flow_title": p["flow_title"],
                "flow": [_mask(b, n) for b in p["boxes"]],
                "gap_no": n,
                "in_table": False,
                "prompt": _prompt_for(p["boxes"], n, cue),
                "step": p["level"],
                "order": i,
                "step_title": f"{p['level']}-daraja",
                "tip": "Tartibga qarang",
                "instruction": ("Complete the flow-chart. Choose NO "
                                "MORE THAN TWO WORDS AND/OR A NUMBER "
                                "from the passage."),
            }
            explain = f"Sxemada: «{cue}»  ->  Matnda: «{psg}». {note}"
            out.append((KIND, _cefr(p["level"]), payload, ans,
                        explain, ALT.get(ans, ""),
                        {"table": cue, "passage": psg}))
    return out


def seed_reading_flow(db):
    """Idempotent: (kind, passage, gap_no) bo'yicha."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_read_flow_v1"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            pl = json.loads(p)
            have.add((k, pl.get("passage"), pl.get("gap_no")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain, alt, para in build_rows():
        key = (kind, payload["passage"], payload["gap_no"])
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
    _seed_mark(db, "ielts_read_flow_v1")
    return made
