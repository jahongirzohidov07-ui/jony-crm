# -*- coding: utf-8 -*-
"""IELTS READING — MATCHING HEADINGS (2026-08-25).

Jahongir: "Bu Paragraph heading savol turi bu misollarni 25-ga qoy
undan oldingilarni osonroq qil bilasanku osondan boshlab qiyinga
qarab ketasan."

TUZILISHI. 29 ta matn, jami 121 xatboshi, daraja 1..28:
  1-8    — 3 xatboshi, qisqa va sodda; sarlavha xatboshining
           birinchi jumlasiga deyarli aynan mos;
  9-16   — 4 xatboshi, sarlavha parafraz bo'lib keladi;
  17-24  — 5 xatboshi, chalg'ituvchi sarlavhalar ko'payadi;
  25     — "READING #12. Traffic Jams" va "READING #13.
           Pedestrians only" (Jahongirning ikki namunasi);
  26-28  — eng qiyini: uzun ilmiy matn, sarlavhalar bir-biriga
           juda yaqin.

BU TURNING O'ZIGA XOSLIGI. Bu yerda bo'shliq to'ldirilmaydi —
xatboshiga MOS SARLAVHA tanlanadi. Ya'ni bitta so'z emas, butun
xatboshining ASOSIY G'OYASI kerak. Eng ko'p xato: xatboshida
uchragan bitta so'z sarlavhada ham borligi uchun tanlab yuborish.

Har matnda ortiqcha sarlavhalar bor — hammasi ishlatilmaydi.
"""

SKILL = "ielts_reading"
KIND = "read_head"
ROMAN = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x"]

# =====================================================================
#  QOIDALAR
# =====================================================================
HEAD_TIPS = [
    ("Matching Headings nima",
     "Matn xatboshilarga bo'lingan (A, B, C...), pastda esa "
     "sarlavhalar ro'yxati (i, ii, iii...). Har xatboshiga MOS "
     "sarlavhani tanlaysiz. Sarlavhalar SONI xatboshilardan ko'p — "
     "ba'zilari ishlatilmaydi.", ""),
    ("ASOSIY G'OYANI toping, so'zni emas",
     "Sarlavha butun xatboshining mazmunini bildiradi. Bitta jumla "
     "yoki bitta so'z bo'yicha tanlash — eng ko'p uchraydigan xato. "
     "Xatboshini o'qib bo'lgach o'zingizga ayting: «bu xatboshi "
     "NIMA HAQIDA?» — keyingina ro'yxatga qarang.",
     "Xatboshi D: «build more roads ... such techniques do not "
     "really keep cars off the road; they only accommodate more of "
     "them»\nAsosiy g'oya: yechim yechim emas\n"
     "Sarlavha: A solution which is no solution"),
    ("BIR XIL SO'Z QOPQONI",
     "Sarlavhada xatboshidagi so'z aynan uchrasa — bu ko'pincha "
     "qopqon. Traffic Jams matnining E xatboshisida «cars» va "
     "«environment» bor, «Making cars more environmentally "
     "friendly» sarlavhasi ham shunday — lekin xatboshi mashina "
     "haqida emas, MABLAG' YETARLI EMASLIGI haqida.", ""),
    ("BIRINCHI va OXIRGI jumlaga alohida qarang",
     "Ko'p xatboshida asosiy fikr birinchi jumlada (topic "
     "sentence) yoki oxirgi jumlada turadi. O'rtadagi misollar va "
     "sonlar — dalil, ular sarlavha emas.", ""),
    ("Ortiqcha sarlavhalar ataylab qo'yilgan",
     "Ikki-uch sarlavha hech qaysi xatboshiga to'g'ri kelmaydi. "
     "Ular odatda matnda uchraydigan so'zlardan yasalgan — shuning "
     "uchun tanish ko'rinadi. «Menga tanish» degani «to'g'ri» "
     "degani emas.", ""),
    ("Oson xatboshidan boshlang",
     "Tartib bilan yurish shart emas. Avval o'zingiz ishonch bilan "
     "topa oladiganini belgilang — shunda qolgan sarlavhalar soni "
     "kamayadi va qiyinlari osonlashadi.", ""),
    ("Sarlavhalarni AVVAL o'qing",
     "Matnga kirishdan oldin sarlavhalar ro'yxatini o'qib chiqing. "
     "Shunda xatboshini o'qiyotganda miya allaqachon nimani "
     "qidirayotganini biladi.", ""),
    ("Misol yoki ro'yxat — sarlavha emas",
     "«Singapore, London and Stockholm have reduced traffic» — bu "
     "MISOL. Xatboshining g'oyasi esa «yo'lga kirish uchun to'lov» "
     "(Paying to get in).", ""),
]


def P(level, title, paras, headings, gaps):
    return {"level": level, "title": title, "paras": paras,
            "headings": headings, "gaps": gaps}


PASSAGES = []

# ================= 1-8 DARAJA: 3 xatboshi, sodda ==================
PASSAGES.append(P(
    1, "OUR SCHOOL DAY",
    [("A", "Lessons begin at eight o'clock and finish at two. "
           "There are six lessons a day, each lasting forty "
           "minutes."),
     ("B", "At eleven there is a long break. Most pupils eat in the "
           "canteen, where a hot meal costs very little."),
     ("C", "After lessons, pupils may join a club. There are clubs "
           "for football, chess, music and drawing.")],
    ["A typical timetable", "Food and rest", "Activities after "
     "school", "Getting to school", "Exam results"],
    [("A", 0, "Lessons begin at eight o'clock and finish at two",
      "Xatboshi butunlay dars vaqti haqida — bu jadval."),
     ("B", 1, "At eleven there is a long break. Most pupils eat in "
      "the canteen", "Tanaffus va ovqat."),
     ("C", 2, "After lessons, pupils may join a club",
      "Darsdan keyingi mashg'ulotlar.")],
))

PASSAGES.append(P(
    2, "A SMALL FARM",
    [("A", "The farm covers twelve hectares. Half of it is used for "
           "wheat and the rest for vegetables."),
     ("B", "Twenty cows live in a barn near the house. They provide "
           "milk which is sold in the village every morning."),
     ("C", "In summer the farmer hires four students to help with "
           "the harvest. They work for six weeks.")],
    ["What is grown", "The animals", "Extra workers", "Selling the "
     "farm", "Machines used"],
    [("A", 0, "Half of it is used for wheat and the rest for "
      "vegetables", "Nima ekiladi."),
     ("B", 1, "Twenty cows live in a barn near the house",
      "Hayvonlar haqida."),
     ("C", 2, "the farmer hires four students to help with the "
      "harvest", "Qo'shimcha ishchilar.")],
))

PASSAGES.append(P(
    3, "THE TOWN MUSEUM",
    [("A", "The museum was opened in 1954 in a former courthouse. "
           "The building itself is over two hundred years old."),
     ("B", "Its best-known objects are coins found by a farmer in "
           "1971. There are more than nine hundred of them."),
     ("C", "Entry is free for children and for anyone living in the "
           "town. Others pay a small charge.")],
    ["The building's history", "The most famous collection",
     "Cost of entry", "Opening hours", "Plans for a new wing"],
    [("A", 0, "The museum was opened in 1954 in a former courthouse",
      "Bino tarixi."),
     ("B", 1, "Its best-known objects are coins found by a farmer",
      "Mashhur to'plam."),
     ("C", 2, "Entry is free for children", "Kirish narxi.")],
))

PASSAGES.append(P(
    4, "LEARNING TO DRIVE",
    [("A", "Before taking lessons you must apply for a provisional "
           "licence. This takes about a week to arrive."),
     ("B", "Most learners need around forty hours with an "
           "instructor, plus twenty hours of private practice."),
     ("C", "The test has two parts. The written part comes first, "
           "and only those who pass it may take the practical "
           "test.")],
    ["The first step", "How much practice is needed",
     "How the test works", "Choosing a car", "The cost of insurance"],
    [("A", 0, "you must apply for a provisional licence",
      "Birinchi qadam."),
     ("B", 1, "Most learners need around forty hours with an "
      "instructor", "Qancha mashq kerak."),
     ("C", 2, "The test has two parts", "Imtihon tuzilishi.")],
))

PASSAGES.append(P(
    5, "THE VILLAGE POST OFFICE",
    [("A", "The post office is open from nine until five, but it "
           "closes for an hour at lunchtime."),
     ("B", "As well as letters and parcels, it sells stationery, "
           "newspapers and bus tickets."),
     ("C", "Last year the company planned to shut it, but four "
           "hundred residents signed a letter and the decision was "
           "changed.")],
    ["When you can go", "More than a post office",
     "Saved by the community", "How to send a parcel abroad",
     "The new manager"],
    [("A", 0, "The post office is open from nine until five",
      "Ish vaqti."),
     ("B", 1, "As well as letters and parcels, it sells stationery",
      "Faqat pochta emas."),
     ("C", 2, "four hundred residents signed a letter and the "
      "decision was changed", "Aholi saqlab qoldi.")],
))

PASSAGES.append(P(
    6, "KEEPING BEES",
    [("A", "A beginner needs a hive, a protective suit and a "
           "smoker. Together these cost around three hundred "
           "pounds."),
     ("B", "The best time to start is early spring, when the first "
           "flowers appear and the colony grows quickly."),
     ("C", "A single hive can produce twenty kilograms of honey in "
           "a good year, though a poor summer may give none at "
           "all.")],
    ["What you have to buy", "The right season to begin",
     "How much honey to expect", "Dangers of bee stings",
     "Selling honey at markets"],
    [("A", 0, "A beginner needs a hive, a protective suit and a "
      "smoker", "Xarid ro'yxati."),
     ("B", 1, "The best time to start is early spring",
      "Qachon boshlash kerak."),
     ("C", 2, "A single hive can produce twenty kilograms of honey",
      "Kutilayotgan hosil.")],
))

PASSAGES.append(P(
    7, "THE CITY PARK",
    [("A", "The park was laid out in 1908 on land given to the city "
           "by a wealthy merchant, on condition that it stayed open "
           "to everyone."),
     ("B", "It contains more than sixty kinds of tree, several of "
           "which are not native to the region and were brought "
           "from Asia."),
     ("C", "In recent years the lake has become shallow and weedy, "
           "and the council has set aside money to clean it.")],
    ["A gift with a condition", "An unusual mix of plants",
     "A problem being fixed", "Sports facilities",
     "Rules for dog owners"],
    [("A", 0, "on land given to the city by a wealthy merchant, on "
      "condition that it stayed open to everyone",
      "Sovg'a va uning sharti."),
     ("B", 1, "more than sixty kinds of tree, several of which are "
      "not native", "O'simliklar xilma-xilligi."),
     ("C", 2, "the lake has become shallow and weedy, and the "
      "council has set aside money to clean it",
      "Muammo va uning yechimi.")],
))

PASSAGES.append(P(
    8, "WORKING NIGHT SHIFTS",
    [("A", "About one worker in six now does some night work. "
           "Hospitals, factories and transport all need staff "
           "around the clock."),
     ("B", "Studies show that night workers sleep on average two "
           "hours less than others, and that the sleep they get is "
           "of poorer quality."),
     ("C", "Some employers now allow short naps during the shift. "
           "Where this has been tried, mistakes have fallen "
           "sharply.")],
    ["How common it is", "The effect on rest", "A change that helps",
     "Pay for unsocial hours", "Getting home safely"],
    [("A", 0, "About one worker in six now does some night work",
      "Qanchalik keng tarqalgan."),
     ("B", 1, "night workers sleep on average two hours less",
      "Uyquga ta'siri."),
     ("C", 2, "Some employers now allow short naps ... mistakes have "
      "fallen sharply", "Yordam bergan o'zgarish.")],
))

# ============== 9-16 DARAJA: 4 xatboshi, parafraz ================
PASSAGES.append(P(
    9, "THE RISE OF THE BICYCLE",
    [("A", "When the first pedal bicycles appeared in the 1860s "
           "they were expensive toys for the rich, with iron tyres "
           "that made every stone painful."),
     ("B", "The invention of the air-filled tyre in 1888 changed "
           "everything. Riding became comfortable, and within ten "
           "years ownership had spread to clerks and shop "
           "assistants."),
     ("C", "For women the effect went further. A bicycle allowed "
           "travel without a chaperone, and dress reformers used "
           "the machine as an argument for lighter clothing."),
     ("D", "Cheap cars pushed bicycles aside after 1950, but "
           "crowded cities and rising fuel costs have brought them "
           "back; several capitals now report record numbers of "
           "riders.")],
    ["A toy for the wealthy", "One invention, a wider public",
     "Freedom beyond transport", "Decline and return",
     "How bicycles are made", "Racing and its champions"],
    [("A", 0, "they were expensive toys for the rich",
      "Boylar uchun qimmat o'yinchoq."),
     ("B", 1, "The invention of the air-filled tyre in 1888 changed "
      "everything ... ownership had spread to clerks",
      "Bitta ixtiro — kengroq doira."),
     ("C", 2, "A bicycle allowed travel without a chaperone",
      "Transportdan tashqari erkinlik. Bu xatboshida «women» bor, "
      "lekin g'oya — erkinlik."),
     ("D", 3, "Cheap cars pushed bicycles aside after 1950, but ... "
      "have brought them back", "Tanazzul va qaytish.")],
))

PASSAGES.append(P(
    10, "SLEEP AND MEMORY",
    [("A", "For a long time sleep was regarded as an idle state, a "
           "simple pause in the working of the brain."),
     ("B", "Recordings made in the 1950s showed the opposite. "
           "During certain phases the sleeping brain is almost as "
           "active as it is when awake."),
     ("C", "Volunteers taught a task and then allowed to sleep "
           "perform far better than those kept awake for the same "
           "number of hours, even when both groups are equally "
           "rested at the moment of testing."),
     ("D", "The current explanation is that the brain replays the "
           "day's activity at high speed, strengthening the "
           "connections that matter and discarding the rest.")],
    ["An old and mistaken view", "Evidence that changed minds",
     "What experiments reveal", "The accepted explanation today",
     "Advice for better sleep", "Sleep in other animals"],
    [("A", 0, "sleep was regarded as an idle state",
      "Eski va noto'g'ri qarash."),
     ("B", 1, "Recordings made in the 1950s showed the opposite",
      "Fikrni o'zgartirgan dalil."),
     ("C", 2, "Volunteers taught a task and then allowed to sleep "
      "perform far better", "Tajriba natijasi."),
     ("D", 3, "The current explanation is that the brain replays "
      "the day's activity", "Hozirgi tushuntirish.")],
))

PASSAGES.append(P(
    11, "PAPER RECYCLING",
    [("A", "Waste paper is soaked in warm water and stirred until "
           "the sheets break apart into a soup of loose fibres."),
     ("B", "Staples and plastic windows are separated out by "
           "weight, while ink is lifted from the mixture by air "
           "bubbles that carry it to the surface as foam."),
     ("C", "Fibres shorten a little each time they are used, so "
           "paper cannot be recycled for ever; after about six "
           "cycles fresh material must be added."),
     ("D", "Even so, making a tonne of recycled paper uses roughly "
           "half the energy and a third of the water needed for "
           "new paper.")],
    ["Breaking the paper down", "Removing what is not wanted",
     "A limit to the process", "Why it is still worth doing",
     "Collecting paper from homes", "The cost of new machinery"],
    [("A", 0, "Waste paper is soaked in warm water and stirred until "
      "the sheets break apart", "Birinchi bosqich — parchalash."),
     ("B", 1, "Staples and plastic windows are separated out ... ink "
      "is lifted", "Keraksizni ajratish."),
     ("C", 2, "paper cannot be recycled for ever",
      "Jarayonning chegarasi."),
     ("D", 3, "uses roughly half the energy and a third of the "
      "water", "Nega baribir arziydi.")],
))

PASSAGES.append(P(
    12, "THE ARABIC NUMERALS",
    [("A", "The digits we use today were developed in India, where "
           "a symbol for zero made written calculation possible for "
           "the first time."),
     ("B", "Arab scholars adopted the system and carried it "
           "westwards; the word 'algorithm' comes from the name of "
           "one of them, al-Khwarizmi."),
     ("C", "Europe resisted for three centuries. Merchants "
           "distrusted a symbol that meant nothing, and Florence "
           "banned the digits in 1299 on the grounds that they were "
           "easy to alter."),
     ("D", "Printing settled the argument. Once tables of figures "
           "could be reproduced exactly, the older Roman system "
           "became impossible to defend.")],
    ["Where the system began", "How it travelled", "Years of refusal",
     "What finally decided it", "Teaching arithmetic to children",
     "Counting without writing"],
    [("A", 0, "The digits we use today were developed in India",
      "Kelib chiqishi."),
     ("B", 1, "Arab scholars adopted the system and carried it "
      "westwards", "Qanday tarqalgani."),
     ("C", 2, "Europe resisted for three centuries",
      "Rad etish yillari."),
     ("D", 3, "Printing settled the argument",
      "Bahsni nima hal qilgani.")],
))

PASSAGES.append(P(
    13, "URBAN FOXES",
    [("A", "Foxes first appeared in British suburbs in the 1930s, "
           "when new housing estates with large gardens spread into "
           "the countryside."),
     ("B", "City life suits them. Food is easier to find, winters "
           "are milder, and there are almost no natural enemies."),
     ("C", "Residents are divided. Some enjoy the sight of a wild "
           "animal at the end of the garden; others complain about "
           "noise at night and overturned bins."),
     ("D", "Attempts to remove them have failed everywhere they "
           "have been tried: killing or catching foxes simply "
           "empties a territory that neighbouring animals move "
           "into within weeks.")],
    ["How they arrived", "Why towns suit them", "Two views among "
     "people", "Why control does not work", "Feeding wild animals",
     "Diseases they may carry"],
    [("A", 0, "Foxes first appeared in British suburbs in the 1930s",
      "Qanday paydo bo'lgani."),
     ("B", 1, "City life suits them", "Nega shahar qulay."),
     ("C", 2, "Residents are divided", "Ikki xil qarash."),
     ("D", 3, "Attempts to remove them have failed everywhere",
      "Nazorat nega ishlamaydi.")],
))

PASSAGES.append(P(
    14, "THE HISTORY OF SOAP",
    [("A", "The earliest recipe, written on a Babylonian tablet "
           "around 2800 BC, mixes ash and animal fat — the same two "
           "ingredients used today."),
     ("B", "For most of history soap was used on cloth rather than "
           "skin. Romans cleaned themselves with oil and a metal "
           "scraper, and washing the body with soap only became "
           "usual in Europe in the eighteenth century."),
     ("C", "Its value became clear when a Hungarian doctor, Ignaz "
           "Semmelweis, showed in 1847 that washing hands cut "
           "deaths in a maternity ward from eighteen percent to "
           "two."),
     ("D", "His colleagues rejected the finding, offended by the "
           "suggestion that doctors carried disease, and "
           "Semmelweis died before his idea was accepted.")],
    ["An ancient recipe", "Not always for the body",
     "Proof that it saves lives", "A discovery that was refused",
     "How soap is made in factories", "Modern liquid soaps"],
    [("A", 0, "The earliest recipe, written on a Babylonian tablet "
      "around 2800 BC", "Qadimiy retsept."),
     ("B", 1, "For most of history soap was used on cloth rather "
      "than skin", "Tanaga emas, matoga."),
     ("C", 2, "washing hands cut deaths in a maternity ward from "
      "eighteen percent to two", "Hayot saqlashi isbotlangan."),
     ("D", 3, "His colleagues rejected the finding",
      "Kashfiyot rad etilgan.")],
))

PASSAGES.append(P(
    15, "THE POSTAGE STAMP",
    [("A", "Before 1840 the receiver paid for a letter, and the "
           "charge depended on distance. Many people refused "
           "delivery, and the service lost money."),
     ("B", "Rowland Hill proposed a single low price for anywhere "
           "in the country, paid in advance by the sender with a "
           "small adhesive label."),
     ("C", "The volume of post trebled within two years. Writing "
           "became something ordinary families could afford, and "
           "literacy rates rose with it."),
     ("D", "Almost at once stamps became objects to keep rather "
           "than to use, and by 1860 dealers, catalogues and "
           "forgeries had all appeared.")],
    ["A system that did not work", "A simple new idea",
     "Wider effects on society", "An unexpected hobby",
     "Designing the first stamp", "Post offices around the world"],
    [("A", 0, "the receiver paid for a letter, and the charge depended on "
      "distance. Many people refused delivery", "Ishlamagan tizim."),
     ("B", 1, "Rowland Hill proposed a single low price",
      "Yangi va sodda g'oya."),
     ("C", 2, "The volume of post trebled within two years. Writing became "
      "something ordinary families could afford",
      "Jamiyatga kengroq ta'sir."),
     ("D", 3, "stamps became objects to keep rather than to use",
      "Kutilmagan ermak — kolleksiya.")],
))

PASSAGES.append(P(
    16, "LEFT-HANDEDNESS",
    [("A", "Roughly one person in ten writes with the left hand, "
           "and the figure has been broadly the same in every "
           "society studied, including those where the practice was "
           "punished."),
     ("B", "Cave paintings offer indirect evidence: hands stencilled "
           "on rock walls are overwhelmingly left hands, which is "
           "what one would expect if the paint was blown by the "
           "right."),
     ("C", "In sports where opponents face each other — fencing, "
           "boxing, tennis — left-handers are far more common than "
           "in the population, apparently because their movements "
           "are less familiar to an opponent."),
     ("D", "No single gene has been found. Current models suggest "
           "that many genes each make a small contribution, which "
           "would explain why identical twins are often of "
           "different handedness.")],
    ["A stable proportion everywhere", "Clues from prehistory",
     "An advantage in competition", "The search for a cause",
     "Tools designed for the right hand",
     "Teaching left-handed children"],
    [("A", 0, "Roughly one person in ten writes with the left hand, "
      "and the figure has been broadly the same",
      "Hamma joyda barqaror ulush."),
     ("B", 1, "Cave paintings offer indirect evidence",
      "Tarixdan oldingi dalillar."),
     ("C", 2, "left-handers are far more common than in the "
      "population", "Musobaqadagi ustunlik."),
     ("D", 3, "No single gene has been found",
      "Sabab izlash.")],
))

# ========= 17-24 DARAJA: 5 xatboshi, chalg'ituvchi ko'p ==========
PASSAGES.append(P(
    17, "THE COMMON COLD",
    [("A", "More than two hundred different viruses can produce the "
           "same set of symptoms, which is the main reason a single "
           "cure has never been found."),
     ("B", "The runny nose and sore throat are not caused by the "
           "virus itself but by the body's own defences, which is "
           "why people with stronger immune systems sometimes feel "
           "worse."),
     ("C", "Cold weather does not cause colds. Infections rise in "
           "winter because people gather indoors, where air is dry "
           "and virus particles survive longer."),
     ("D", "Hands matter more than coughing. A virus can live for "
           "hours on a door handle, and most people touch their "
           "face several times an hour without noticing."),
     ("E", "Vitamin C has been tested repeatedly and does not "
           "prevent colds in ordinary people, though it may "
           "shorten them slightly in those under extreme physical "
           "stress.")],
    ["Why no cure exists", "Symptoms come from within",
     "A popular belief corrected", "How it really spreads",
     "A remedy that mostly fails", "Treating a child's cold",
     "How long a cold lasts"],
    [("A", 0, "More than two hundred different viruses can produce "
      "the same set of symptoms", "Nega davo yo'q."),
     ("B", 1, "not caused by the virus itself but by the body's own "
      "defences", "Alomatlar ichkaridan."),
     ("C", 2, "Cold weather does not cause colds",
      "Mashhur ishonch rad etiladi."),
     ("D", 3, "Hands matter more than coughing",
      "Haqiqiy tarqalish yo'li."),
     ("E", 4, "Vitamin C has been tested repeatedly and does not prevent "
      "colds in ordinary people",
      "Ishlamaydigan vosita.")],
))

PASSAGES.append(P(
    18, "THE STORY OF CONCRETE",
    [("A", "Roman builders mixed volcanic ash with lime and "
           "seawater. Their harbour walls are still standing, and "
           "tests show the material has become stronger over two "
           "thousand years."),
     ("B", "The recipe was then lost for more than a millennium, "
           "and medieval Europe built almost entirely in stone and "
           "timber."),
     ("C", "Modern concrete, patented in 1824, sets in hours rather "
           "than months, which made it possible to build quickly on "
           "a large scale."),
     ("D", "Adding steel bars solved its one great weakness: "
           "concrete resists pressure well but pulls apart easily, "
           "while steel does the opposite."),
     ("E", "The industry now produces about eight percent of "
           "global carbon dioxide, most of it released by the "
           "chemistry of making cement rather than by burning "
           "fuel.")],
    ["An ancient material that improved with age",
     "Knowledge that disappeared", "Speed as the modern advantage",
     "Two materials that complete each other",
     "An environmental cost that is hard to avoid",
     "Concrete in modern architecture", "Repairing old buildings"],
    [("A", 0, "Their harbour walls are still standing, and tests "
      "show the material has become stronger",
      "Qadimiy material — vaqt bilan kuchaygan."),
     ("B", 1, "The recipe was then lost for more than a millennium",
      "Bilim yo'qolgan."),
     ("C", 2, "Modern concrete, patented in 1824, sets in hours rather than "
      "months",
      "Zamonaviy ustunlik — tezlik."),
     ("D", 3, "concrete resists pressure well but pulls apart "
      "easily, while steel does the opposite",
      "Ikki material bir-birini to'ldiradi."),
     ("E", 4, "about eight percent of global carbon dioxide",
      "Ekologik narx.")],
))

PASSAGES.append(P(
    19, "MEASURING TIME",
    [("A", "The earliest clocks used shadows, and worked only in "
           "sunshine. Water clocks solved that but froze in winter "
           "and ran faster as the vessel emptied."),
     ("B", "Mechanical clocks arrived in the fourteenth century, "
           "and monasteries were among the first buyers: a bell "
           "rung automatically kept prayers to a fixed schedule."),
     ("C", "Until the railways, every town kept its own time, set "
           "by the local noon. Timetables made this impossible, and "
           "a single national time was imposed."),
     ("D", "Accuracy improved from minutes a day to seconds a "
           "century once the swing of a pendulum, and later the "
           "vibration of a quartz crystal, replaced falling "
           "weights."),
     ("E", "Today's atomic clocks are so precise that they must "
           "take account of altitude: time passes measurably faster "
           "at the top of a tall building than at its base.")],
    ["Early attempts and their faults", "An unexpected first market",
     "Transport forces a change", "Sources of greater precision",
     "Precision that reveals physics", "Wristwatches become popular",
     "Time zones around the world"],
    [("A", 0, "The earliest clocks used shadows, and worked only in "
      "sunshine", "Dastlabki urinishlar va kamchiliklari."),
     ("B", 1, "monasteries were among the first buyers",
      "Kutilmagan birinchi xaridor."),
     ("C", 2, "Until the railways, every town kept its own time",
      "Transport o'zgarishga majbur qildi."),
     ("D", 3, "once the swing of a pendulum, and later the "
      "vibration of a quartz crystal, replaced falling weights",
      "Aniqlik manbalari."),
     ("E", 4, "time passes measurably faster at the top of a tall "
      "building", "Aniqlik fizikani ochib beradi.")],
))

PASSAGES.append(P(
    20, "SEEDS AND SURVIVAL",
    [("A", "A seed is a plant in suspended animation, carrying its "
           "own food supply and able to wait until conditions "
           "suit."),
     ("B", "Some wait a very long time. A date palm grown in 2005 "
           "came from a seed two thousand years old, recovered from "
           "a desert fortress."),
     ("C", "Many species will not sprout until something has "
           "happened to them — passing through an animal's gut, "
           "being scorched by fire, or spending months below "
           "freezing."),
     ("D", "This caution is protective. A seed that germinated "
           "after the first warm week of February would meet the "
           "frost that follows."),
     ("E", "Collections now store seeds from thousands of species "
           "at minus twenty degrees, an insurance policy against "
           "loss of habitat and changing climate.")],
    ["What a seed actually is", "Extreme patience",
     "Conditions that must be met first", "Why waiting makes sense",
     "Storing for the future", "How seeds are dispersed by wind",
     "Growing plants from cuttings"],
    [("A", 0, "A seed is a plant in suspended animation",
      "Urug' nima ekani."),
     ("B", 1, "came from a seed two thousand years old",
      "G'oyat uzoq kutish."),
     ("C", 2, "Many species will not sprout until something has "
      "happened to them", "Oldindan bajarilishi kerak bo'lgan "
      "shartlar."),
     ("D", 3, "A seed that germinated after the first warm week of "
      "February would meet the frost", "Nega kutish oqilona."),
     ("E", 4, "Collections now store seeds from thousands of species at "
      "minus twenty degrees", "Kelajak uchun saqlash.")],
))

PASSAGES.append(P(
    21, "THE ORIGINS OF WRITING",
    [("A", "Writing was not invented to record poetry or history. "
           "The oldest tablets from Mesopotamia are lists of grain, "
           "sheep and beer, kept by temple officials."),
     ("B", "Before symbols came tokens: small clay shapes sealed "
           "inside a hollow ball, one for each animal owed. Marking "
           "the outside of the ball made opening it unnecessary — "
           "and the marks became the script."),
     ("C", "For centuries only a small trained group could read. "
           "Scribes guarded the skill, and their schools taught "
           "obedience as much as literacy."),
     ("D", "The alphabet changed the balance. With two dozen "
           "letters instead of hundreds of signs, ordinary traders "
           "could learn to write in weeks."),
     ("E", "Writing has been invented independently at most four "
           "times — in Mesopotamia, China, Egypt and Central "
           "America — which suggests it is far from an obvious "
           "step.")],
    ["An accounting tool, not an art", "From objects to symbols",
     "A skill kept by a few", "The change that opened it up",
     "A rare human achievement", "Materials used for writing",
     "Deciphering lost scripts"],
    [("A", 0, "The oldest tablets from Mesopotamia are lists of "
      "grain, sheep and beer", "San'at emas — hisob vositasi."),
     ("B", 1, "Before symbols came tokens: small clay shapes sealed inside a "
      "hollow ball", "Buyumdan belgiga."),
     ("C", 2, "For centuries only a small trained group could read",
      "Ozchilik qo'lidagi mahorat."),
     ("D", 3, "With two dozen letters instead of hundreds of signs",
      "Uni ochib bergan o'zgarish."),
     ("E", 4, "Writing has been invented independently at most four "
      "times", "Kamdan-kam yutuq.")],
))

PASSAGES.append(P(
    22, "WHY BUILDINGS FALL DOWN",
    [("A", "Structures almost never fail because a material was too "
           "weak. In nearly every investigated collapse the cause "
           "lies in a connection — a joint, a bolt, a weld — rather "
           "than in a beam or column."),
     ("B", "A second pattern is change of use. A floor designed for "
           "offices may be filled with filing cabinets or a "
           "library, doubling the load it was built for."),
     ("C", "Progressive collapse is the most feared mechanism: one "
           "damaged column throws its share of the load onto its "
           "neighbours, which fail in turn, and the building "
           "unzips."),
     ("D", "Modern codes therefore require redundancy — more paths "
           "for the load than are strictly necessary — so that "
           "losing one element does not doom the rest."),
     ("E", "Ironically, the safest buildings tend to be those that "
           "have already been damaged and repaired, because "
           "everything about them has since been examined.")],
    ["Where failure usually begins", "Loads the designer never "
     "expected", "One failure leading to many",
     "Building in spare capacity", "A surprising kind of safety",
     "Earthquake-resistant design", "The role of the inspector"],
    [("A", 0, "In nearly every investigated collapse the cause lies in a "
      "connection", "Buzilish qayerdan boshlanadi."),
     ("B", 1, "A floor designed for offices may be filled with "
      "filing cabinets", "Kutilmagan yuk."),
     ("C", 2, "one damaged column throws its share of the load onto "
      "its neighbours", "Zanjirli qulash."),
     ("D", 3, "Modern codes therefore require redundancy",
      "Zaxira quvvat qo'yish."),
     ("E", 4, "the safest buildings tend to be those that have "
      "already been damaged and repaired",
      "Kutilmagan xavfsizlik turi.")],
))

PASSAGES.append(P(
    23, "THE ECONOMICS OF FREE",
    [("A", "A price of zero does not behave like a very low price. "
           "In one experiment, cutting a chocolate from fifteen "
           "cents to one cent changed little; cutting it from one "
           "cent to nothing changed everything."),
     ("B", "Free removes the possibility of loss. Any purchase "
           "carries the risk of regret, and at zero that risk "
           "disappears, which is why people queue for items they do "
           "not want."),
     ("C", "Businesses exploit this by giving away one thing to "
           "sell another: free delivery above a threshold "
           "reliably increases the size of an order."),
     ("D", "The pattern has limits. Where quality is uncertain, a "
           "free offer can suggest that the product is worth "
           "nothing, and sales fall when the price is removed."),
     ("E", "Attention has become the usual payment online. The "
           "service costs nothing in money, but the user's time and "
           "data are sold on, a bargain many accept without "
           "examining it.")],
    ["Zero is not just a low number", "The fear that vanishes",
     "Using it to sell something else", "When the tactic backfires",
     "Paying without money", "Discount pricing strategies",
     "Consumer protection laws"],
    [("A", 0, "A price of zero does not behave like a very low "
      "price", "Nol — shunchaki past narx emas."),
     ("B", 1, "Free removes the possibility of loss",
      "Yo'qotish qo'rquvi yo'qoladi."),
     ("C", 2, "giving away one thing to sell another",
      "Boshqasini sotish uchun vosita."),
     ("D", 3, "a free offer can suggest that the product is worth "
      "nothing", "Usul teskari ishlaganda."),
     ("E", 4, "the user's time and data are sold on",
      "Pulsiz to'lov.")],
))

PASSAGES.append(P(
    24, "THE PLACEBO EFFECT",
    [("A", "A treatment with no active ingredient can still produce "
           "measurable change — in pain, in nausea, in the symptoms "
           "of Parkinson's disease — and brain scans show real "
           "chemical activity, not imagination."),
     ("B", "The details matter in ways that make little logical "
           "sense. Two dummy tablets work better than one, "
           "injections work better than tablets, and a higher price "
           "increases the effect."),
     ("C", "Remarkably, the effect survives honesty. In several "
           "trials patients told openly that they were receiving an "
           "inactive pill still improved, which undermines the idea "
           "that deception is essential."),
     ("D", "There is a mirror image. Warned of a side effect, "
           "patients on dummy pills report it at rates close to "
           "those on the real drug — an effect strong enough to "
           "make people abandon treatment."),
     ("E", "For researchers this is a nuisance rather than a "
           "curiosity: any new medicine must prove itself better "
           "than an effect that is itself getting stronger, "
           "particularly in American trials.")],
    ["Real effects without a real drug",
     "Illogical details that matter", "It works even when disclosed",
     "The harmful opposite", "A problem for drug testing",
     "The history of medical fraud", "How doctors choose treatments"],
    [("A", 0, "brain scans show real chemical activity, not "
      "imagination", "Dorisiz haqiqiy ta'sir."),
     ("B", 1, "Two dummy tablets work better than one",
      "Mantiqsiz tafsilotlar."),
     ("C", 2, "patients told openly that they were receiving an "
      "inactive pill still improved", "Ochiq aytilganda ham ishlaydi."),
     ("D", 3, "Warned of a side effect, patients on dummy pills "
      "report it", "Zararli teskari ko'rinish."),
     ("E", 4, "any new medicine must prove itself better than an "
      "effect that is itself getting stronger",
      "Dori sinovlari uchun muammo.")],
))

# ============== 25-DARAJA: JAHONGIRNING IKKI NAMUNASI ============
PASSAGES.append(P(
    25, "READING #12. TRAFFIC JAMS — NO END IN SIGHT",
    [("A", "There are no easy answers to the problems of traffic "
           "congestion. Traffic congestion affects people "
           "throughout the world. Traffic jams cause smog in dozens "
           "of cities across both the developed and developing "
           "world. In the U.S., commuters spend an average of a "
           "full work week each year sitting in traffic, according "
           "to the Texas Transportation Institute. While "
           "alternative ways of getting around are available, most "
           "people still choose their cars because they are looking "
           "for convenience, comfort and privacy."),
     ("B", "The most promising technique for reducing city traffic "
           "is called congestion pricing, whereby cities charge a "
           "toll to enter certain parts of town at certain times of "
           "day. In theory, if the toll is high enough, some "
           "drivers will cancel their trips or go by bus or train. "
           "And in practice it seems to work: Singapore, London and "
           "Stockholm have reduced traffic and pollution in city "
           "centers thanks to congestion pricing."),
     ("C", "Another way to reduce rush hour traffic is for "
           "employers to implement flexitime, which lets employees "
           "travel to and from work at off-peak traffic times to "
           "avoid the rush hour. Those who have to travel during "
           "busy times can do their part by sharing cars. Employers "
           "can also allow more staff to telecommute (work from "
           "home) so as to keep more cars off the road altogether."),
     ("D", "Some urban planners still believe that the best way to "
           "ease traffic congestion is to build more roads, "
           "especially roads that can take drivers around or over "
           "crowded city streets. But such techniques do not really "
           "keep cars off the road; they only accommodate more of "
           "them."),
     ("E", "Other, more forward-thinking, planners know that more "
           "and more drivers and cars are taking to the roads every "
           "day, and they are unwilling to encourage more private "
           "automobiles when public transport is so much better "
           "both for people and the environment. For this reason, "
           "the American government has decided to spend some $7 "
           "billion on helping to increase capacity on public "
           "transport systems and upgrade them with more efficient "
           "technologies. But environmentalists complain that such "
           "funding is tiny compared with the $50 billion being "
           "spent on roads and bridges.")],
    ["A solution which is no solution", "Changing working practices",
     "Closing city centres to traffic",
     "Making cars more environmentally friendly", "Not doing enough",
     "Paying to get in", "A global problem"],
    [("A", 6, "Traffic congestion affects people throughout the "
      "world. Traffic jams cause smog in dozens of cities across "
      "both the developed and developing world",
      "Butun xatboshi muammoning KENGLIGI haqida — AQSh shunchaki "
      "misol."),
     ("B", 5, "cities charge a toll to enter certain parts of town",
      "«Paying to get in» = kirish uchun to'lov. Singapur, London, "
      "Stokgolm — misol, sarlavha emas."),
     ("C", 1, "employers to implement flexitime, which lets "
      "employees travel to and from work at off-peak traffic times",
      "Ish tartibini o'zgartirish: flexitime, car sharing, "
      "telecommute."),
     ("D", 0, "such techniques do not really keep cars off the road; "
      "they only accommodate more of them",
      "Yechim taklif qilinadi, lekin u yechim emas — asosiy fikr "
      "OXIRGI jumlada."),
     ("E", 4, "environmentalists complain that such funding is tiny "
      "compared with the $50 billion being spent on roads",
      "QOPQON: xatboshida «cars» va «environment» bor, «Making cars "
      "more environmentally friendly» tanish ko'rinadi. Lekin gap "
      "mablag' YETARLI EMASLIGI haqida.")],
))

PASSAGES.append(P(
    25, "READING #13. PEDESTRIANS ONLY",
    [("A", "The concept of traffic-free shopping areas goes back a "
           "long time. During the Middle Ages, traffic-free "
           "shopping areas known as souks were built in Middle "
           "Eastern countries to allow people to shop in comfort "
           "and, more importantly, safety. As far back as 2,000 "
           "years ago, road traffic was banned from central Rome "
           "during the day to allow for the free movement of "
           "pedestrians, and was only allowed in at night when "
           "shops and markets had closed for the day."),
     ("B", "The modern, traffic-free shopping street was born in "
           "Europe in the 1960s, when both city populations and car "
           "ownership increased rapidly. Dirty exhaust fumes from "
           "cars and the risks involved in crossing the road were "
           "beginning to make shopping an unpleasant and dangerous "
           "experience. Many believed the time was right for "
           "experimenting with car-free streets, and shopping areas "
           "seemed the best place to start."),
     ("C", "At first, there was resistance from shopkeepers. They "
           "believed that such a move would be bad for business. "
           "They argued that people would avoid streets if they "
           "were unable to get to them in their cars. When the "
           "first streets in Europe were closed to traffic, there "
           "were even noisy demonstrations, as many shopkeepers "
           "predicted they would lose customers."),
     ("D", "However, research carried out afterwards in several "
           "European cities revealed some unexpected statistics. In "
           "Munich, Cologne and Hamburg, visitors to shopping areas "
           "increased by 50 percent. On Copenhagen's main shopping "
           "street, shopkeepers reported sales increases of 25-40 "
           "percent. Shopkeepers in Minneapolis, USA, were so "
           "impressed when they learnt this that they even offered "
           "to pay for the construction and maintenance costs of "
           "their own traffic-free streets."),
     ("E", "With the arrival of the traffic-free shopping street, "
           "many shops, especially those selling things like "
           "clothes, food and smaller luxury items, prospered. "
           "Unfortunately, it wasn't good news for everyone, as "
           "shops selling furniture and larger electrical "
           "appliances actually saw their sales drop. Many of these "
           "were forced to move elsewhere, away from the city "
           "centre.")],
    ["Facing local opposition", "Some reasons for success",
     "Winners and losers", "A need for change",
     "An experiment that went wrong", "An idea from ancient history",
     "North America learns from Europe"],
    [("A", 5, "As far back as 2,000 years ago, road traffic was "
      "banned from central Rome",
      "O'rta asrlar va Rim — g'oya qadimdan kelgan."),
     ("B", 3, "Dirty exhaust fumes from cars and the risks involved "
      "in crossing the road were beginning to make shopping an "
      "unpleasant and dangerous experience",
      "Nega o'zgarish kerak bo'lgani."),
     ("C", 0, "At first, there was resistance from shopkeepers ... "
      "there were even noisy demonstrations",
      "Mahalliy qarshilik."),
     ("D", 1, "research carried out afterwards in several European cities "
      "revealed some unexpected statistics",
      "QOPQON: oxirgi jumlada Minneapolis bor, «North America "
      "learns from Europe» tanish ko'rinadi. Lekin xatboshining "
      "g'oyasi — muvaffaqiyat dalillari."),
     ("E", 2, "Unfortunately, it wasn't good news for everyone, as shops "
      "selling furniture and larger electrical appliances actually "
      "saw their sales drop",
      "Ba'zilar yutdi, ba'zilar yutqazdi.")],
))

# ============== 26-28 DARAJA: eng qiyini =========================
PASSAGES.append(P(
    26, "THE VALUE OF BOREDOM",
    [("A", "Boredom is usually treated as a fault to be corrected, "
           "yet it appears in every culture that has been studied "
           "and has no obvious evolutionary cost, which suggests it "
           "serves a purpose."),
     ("B", "One argument is that it functions as a signal, in the "
           "way that hunger does. It does not tell us what to do; "
           "it tells us that what we are currently doing is not "
           "worth continuing."),
     ("C", "Laboratory work supports this. Participants asked to "
           "carry out a dull sorting task afterwards produced more "
           "unusual uses for an everyday object than a control "
           "group, and the effect grew with the dullness of the "
           "task."),
     ("D", "The modern difficulty is not that life has become more "
           "boring but that the gap is instantly filled. A queue, a "
           "lift, a wait at a crossing — each is now occupied by a "
           "screen, and the signal never has time to do its work."),
     ("E", "Some researchers therefore argue for deliberate "
           "under-stimulation, though they concede that prescribing "
           "boredom is a contradiction: an activity chosen in order "
           "to be dull is no longer entirely dull.")],
    ["An emotion that must have a use", "What the feeling is for",
     "Evidence from experiments", "Why it has become rarer",
     "A recommendation that defeats itself",
     "Boredom in children at school", "Treating chronic boredom"],
    [("A", 0, "it appears in every culture that has been studied "
      "and has no obvious evolutionary cost",
      "Demak, foydasi bo'lishi kerak."),
     ("B", 1, "it functions as a signal, in the way that hunger does",
      "His nima uchun kerak."),
     ("C", 2, "Participants asked to carry out a dull sorting task "
      "afterwards produced more unusual uses", "Tajriba dalili."),
     ("D", 3, "The modern difficulty is not that life has become more boring "
      "but that the gap is instantly filled", "Nega kamayib ketdi."),
     ("E", 4, "prescribing boredom is a contradiction",
      "O'zini o'zi inkor qiladigan tavsiya.")],
))

PASSAGES.append(P(
    27, "THE DISAPPEARANCE OF NIGHT",
    [("A", "Two thirds of Europeans and nearly eighty percent of "
           "North Americans can no longer see the Milky Way from "
           "where they live, a change that has happened within a "
           "single lifetime."),
     ("B", "The cause is not the quantity of light so much as its "
           "direction and colour. Fixtures that throw light "
           "sideways or upwards waste most of it, and the white "
           "LEDs that replaced orange sodium lamps scatter far more "
           "strongly in the atmosphere."),
     ("C", "The biological consequences are widest among animals "
           "that navigate by the sky. Newly hatched turtles crawl "
           "towards the brightest horizon, which for millions of "
           "years meant the sea; hundreds of thousands now die on "
           "roads instead."),
     ("D", "For humans the effect is subtler. Light in the blue "
           "part of the spectrum suppresses melatonin most "
           "strongly, and shift workers exposed to it show measured "
           "differences in sleep and metabolism."),
     ("E", "Unlike most pollution, this one is reversible in an "
           "instant and often pays for itself: cities that have "
           "shielded their lamps and lowered their colour "
           "temperature report both darker skies and smaller "
           "electricity bills.")],
    ["A loss within one generation", "Not simply too much light",
     "Animals that are misled", "A quieter effect on people",
     "Pollution that can be undone", "Astronomy and observatories",
     "Street lighting and crime"],
    [("A", 0, "can no longer see the Milky Way from where they live, a "
      "change that has happened within a single lifetime", "Bir avlod ichidagi yo'qotish."),
     ("B", 1, "The cause is not the quantity of light so much as "
      "its direction and colour", "Miqdor emas, yo'nalish va rang."),
     ("C", 2, "Newly hatched turtles crawl towards the brightest "
      "horizon", "Adashtirilgan hayvonlar."),
     ("D", 3, "Light in the blue part of the spectrum suppresses "
      "melatonin", "Odamga sekinroq ta'sir."),
     ("E", 4, "this one is reversible in an instant and often pays "
      "for itself", "Qaytarib bo'ladigan ifloslanish.")],
))

PASSAGES.append(P(
    28, "THE ECONOMICS OF QUEUES",
    [("A", "A queue is a price paid in time rather than money, and "
           "like any price it sorts people — but it sorts them by "
           "who has time to spare, which is not the same as who "
           "values the goods most."),
     ("B", "Operators discovered long ago that the perception "
           "matters more than the duration. An airport that moved "
           "its arrival gates further from the baggage hall cut "
           "complaints to almost nothing, although the total wait "
           "was unchanged: walking feels like progress, standing "
           "does not."),
     ("C", "Unexplained waits feel roughly twice as long as "
           "explained ones, and unfair waits feel longer still, "
           "which is why a single queue feeding several counters "
           "produces higher satisfaction than separate lines even "
           "when it is slower."),
     ("D", "Selling a way past the queue raises a different "
           "difficulty. Fast-track lanes increase revenue, but "
           "studies of theme parks find that ordinary visitors "
           "report lower satisfaction after watching others "
           "overtake them, even when their own wait has not "
           "lengthened."),
     ("E", "The uncomfortable conclusion is that queue design is "
           "largely a matter of managing feelings rather than "
           "minutes, and that an operator who optimises only the "
           "clock will make customers less happy while making the "
           "system faster.")],
    ["A price paid in time", "Feeling shorter without being shorter",
     "Fairness and explanation", "The cost of letting people pay to "
     "skip", "Managing perception, not speed",
     "Software that predicts demand", "Queues in health services"],
    [("A", 0, "A queue is a price paid in time rather than money",
      "Vaqt bilan to'lanadigan narx."),
     ("B", 1, "the perception matters more than the duration ... "
      "although the total wait was unchanged",
      "Qisqarmasdan qisqa tuyulishi."),
     ("C", 2, "Unexplained waits feel roughly twice as long as "
      "explained ones, and unfair waits feel longer still",
      "Adolat va tushuntirish."),
     ("D", 3, "Fast-track lanes increase revenue, but ... ordinary "
      "visitors report lower satisfaction",
      "Navbatni pulga o'tkazishning narxi."),
     ("E", 4, "queue design is largely a matter of managing "
      "feelings rather than minutes",
      "Tezlikni emas, idrokni boshqarish.")],
))


# =====================================================================
#  YIG'ISH
# =====================================================================
def _cefr(level):
    if level <= 8:
        return "A2"
    if level <= 16:
        return "B1"
    if level <= 24:
        return "B2"
    return "C1"


def build_rows():
    out = []
    for p in PASSAGES:
        opts = [f"{ROMAN[i]}. {h}" for i, h in enumerate(p["headings"])]
        full = "\n\n".join(f"{L}. {t}" for L, t in p["paras"])
        for i, (letter, hi, key, note) in enumerate(p["gaps"]):
            payload = {
                "title": p["title"],
                "passage": full,
                "paragraphs": [{"letter": L, "text": t}
                               for L, t in p["paras"]],
                "para": letter,
                "options": opts,
                "prompt": f"Paragraph {letter}",
                "step": p["level"],
                "order": i,
                "step_title": f"{p['level']}-daraja",
                "tip": "Asosiy g'oyani toping",
                "instruction": ("Choose the correct heading for each "
                                "paragraph. There are more headings "
                                "than paragraphs."),
            }
            explain = (f"Xatboshi {letter} ning asosiy fikri: "
                       f"«{key}». {note}")
            out.append((KIND, _cefr(p["level"]), payload, opts[hi],
                        explain, "",
                        {"table": f"Paragraph {letter}",
                         "passage": key}))
    return out


def seed_reading_head(db):
    """Idempotent: (kind, passage, para) bo'yicha."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_read_head_v1"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            pl = json.loads(p)
            have.add((k, pl.get("passage"), pl.get("para")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain, alt, para in build_rows():
        key = (kind, payload["passage"], payload["para"])
        if key in have:
            continue
        payload = dict(payload)
        payload["paraphrase"] = para
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, explain=explain))
        have.add(key)
        made += 1
    if made:
        db.commit()
    _seed_mark(db, "ielts_read_head_v1")
    return made
