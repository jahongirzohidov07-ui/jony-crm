# -*- coding: utf-8 -*-
"""IELTS READING — SUMMARY / NOTE COMPLETION (2026-08-25).

Jahongir: "bu summary completion turi shunga ham 100ta mashq ber.
Butun textdan xulosani textdagi so'zlar bilan to'ldirish."

TABLE COMPLETION'DAN FARQI. Jadvalda ma'lumot kataklarga bo'lingan
va bo'shliqni topish uchun QATOR bilan USTUN kesishmasiga qarash
kifoya. Bu yerda esa xulosa BUTUN MATNNI qamraydi: har bir bo'shliq
matnning boshqa-boshqa joyidan olinadi va xulosa matn tartibi bilan
boradi. Ya'ni bola matnni to'liq o'qishga majbur.

USUL O'ZGARMAYDI — PARAFFRAZ. Xulosadagi ibora matnda hech qachon
aynan takrorlanmaydi:
    Xulosada: «Year started»   ->  Matnda: «Created in 2008»
    Xulosada: «A maximum of»   ->  Matnda: «a total of 50 cities»
Javobdan keyin shu ikki tomon doim ko'rsatiladi.

TUZILISHI. 20 ta matn, jami 100 bo'shliq, daraja 1..20.
  1-9    — Jahongir yuborgan namunadan osonroq;
  10     — "The happiest country in the world" (1-namuna, aynan);
  11     — "A city survey with a difference" (2-namuna, aynan);
  12-20  — qiyinlashib boradi.
"""

SKILL = "ielts_reading"
KIND = "read_summary"
GAP = "______"

# =====================================================================
#  QOIDALAR
# =====================================================================
SUMMARY_TIPS = [
    ("Summary Completion nima",
     "Matnning qisqacha mazmuni (yoki eslatma-qaydnoma) berilgan, "
     "unda bo'sh joylar bor. Bo'shliqqa MATNDAN olingan so'z "
     "yoziladi — o'zingizdan so'z qo'shilmaydi va shakli "
     "o'zgartirilmaydi.",
     "Xulosa: «Year started: ______»\n"
     "Matn: «Created in 2008, the Happy Planet Index...»\n"
     "Javob: 2008"),
    ("Jadvaldan farqi — BUTUN matn kerak",
     "Table Completion'da javob bitta katakka tegishli bo'lardi. "
     "Xulosada esa har bo'shliq matnning boshqa joyidan olinadi. "
     "Shuning uchun avval matnni boshdan-oxir bir marta o'qib "
     "chiqing, keyin xulosaga o'ting.", ""),
    ("PARAFFRAZ — asosiy ko'nikma",
     "Xulosadagi so'z matnda boshqacha aytiladi. So'zma-so'z "
     "qidirish ishlamaydi: avval ma'noni oling, keyin matndan "
     "o'sha ma'noni toping.",
     "started = created · lists = ranks · effect = impact\n"
     "the quantity = how much · uses = consumes\n"
     "population = citizens · maximum = total\n"
     "similar to = like · several = a number of\n"
     "useful = helpful · find work = get a job · regional = local"),
    ("Tartib — foydali, lekin ishonchsiz yo'l ko'rsatgich",
     "Uzluksiz XULOSA (summary) odatda matn tartibi bilan boradi: "
     "3-javobni topdingizmi, 4-javob undan keyin. Ammo "
     "QAYDNOMA (note) turida tartib buzilishi MUMKIN — masalan "
     "Happy Planet Index qaydnomasida «Year started» matnning "
     "uchinchi xatboshisidan, «effect on the environment» esa "
     "birinchisidan olingan. Shuning uchun tartibga ishoning, "
     "lekin topilmasa butun matnni qayta ko'zdan kechiring.",
     "Qaydnoma: «its effect on the ______» -> 1-xatboshi\n"
     "Qaydnoma: «Year started: ______» -> 3-xatboshi"),
    ("So'z TURINI bo'shliq atrofidan aniqlang",
     "Bo'shliqdan oldin artikl yoki sifat bo'lsa — OT kerak; "
     "«to» bo'lsa — FE'L; «the ___ of» bo'lsa — OT.",
     "«a good ______ destination» -> holiday (ot)\n"
     "«decide where to ______» -> live (fe'l)\n"
     "«the ______ of the population» -> health (ot)"),
    ("Son so'ralsa — qaysi son ekanini tekshiring",
     "Matnda bir nechta son bo'ladi (2008, 143, 50, 20, 10,000). "
     "Bo'shliq atrofidagi so'z qaysi biri kerakligini aytadi: "
     "«Year started» — yil, «Number of countries» — davlatlar "
     "soni.", ""),
    ("So'z shaklini O'ZGARTIRMANG",
     "Matnda «consumes» bo'lsa va bo'shliqqa «uses» mos kelsa ham, "
     "matndagi shakl yoziladi. Ko'plik/birlikni ham matndagidek "
     "qoldiring.", ""),
    ("Nechta so'z ruxsat etilgan",
     "«ONE WORD» — bitta so'z. «ONE WORD OR A NUMBER» — bitta so'z "
     "yoki bitta son. Ortiqcha so'z yozilsa javob noto'g'ri "
     "sanaladi.", ""),
]


def P(level, title, text, summary_title, lines, gaps):
    return {"level": level, "title": title, "text": text,
            "summary_title": summary_title, "lines": lines,
            "gaps": gaps}


PASSAGES = []

# ---------------------------------------------------------------- 1
PASSAGES.append(P(
    1, "A NEW SPORTS CLUB",
    "A new sports club opened in our town last April. It has a large "
    "swimming pool and four tennis courts. Members pay 20 pounds a "
    "month. The club is closed on Sundays. More than 300 people have "
    "already joined.",
    "The town sports club",
    ["Opened: last ___1",
     "Facilities: a big ___2 and four tennis courts",
     "Monthly fee: ___3 pounds",
     "Closed on: ___4",
     "Members so far: over ___5"],
    [(1, "April", "Opened: last ______", "opened in our town last April",
      "«Opened» = «opened» — bu eng oson bosqich, paraffraz hali "
      "yaqin."),
     (2, "swimming", "a big ______", "It has a large swimming pool",
      "PARAFFRAZ: big = large."),
     (3, "20", "Monthly fee: ______ pounds",
      "Members pay 20 pounds a month",
      "PARAFFRAZ: monthly fee = pay ... a month."),
     (4, "Sundays", "Closed on: ______",
      "The club is closed on Sundays", "To'g'ridan-to'g'ri."),
     (5, "300", "Members so far: over ______",
      "More than 300 people have already joined",
      "PARAFFRAZ: over = more than; members = people who joined.")],
))

# ---------------------------------------------------------------- 2
PASSAGES.append(P(
    2, "THE SCHOOL TRIP",
    "Last month our class went to the mountains for three days. We "
    "travelled by bus, which took five hours. The weather was cold "
    "but sunny. We stayed in a small hotel near a lake. Everyone "
    "enjoyed the walk to the waterfall on the second day.",
    "Class trip",
    ["Destination: the ___1",
     "Length: ___2 days",
     "Transport: ___3 (___4 hours)",
     "Accommodation: a small hotel beside a ___5"],
    [(1, "mountains", "Destination: the ______",
      "our class went to the mountains",
      "PARAFFRAZ: destination = the place they went to."),
     (2, "three", "Length: ______ days", "for three days",
      "Davomiylik."),
     (3, "bus", "Transport: ______", "We travelled by bus",
      "PARAFFRAZ: transport = travelled by."),
     (4, "five", "(______ hours)", "which took five hours",
      "Chalg'ituvchi: «three» — kunlar soni, «second» — kun "
      "raqami."),
     (5, "lake", "beside a ______", "in a small hotel near a lake",
      "PARAFFRAZ: beside = near.")],
))

# ---------------------------------------------------------------- 3
PASSAGES.append(P(
    3, "TOM'S PART-TIME JOB",
    "Tom works in a bookshop on Saturdays. He starts at nine and "
    "finishes at five. His main duty is putting new books on the "
    "shelves, but he also helps customers find what they want. He "
    "earns eight pounds an hour and gets a discount on any book he "
    "buys.",
    "Tom's job",
    ["Place of work: a ___1",
     "Day: ___2",
     "Hours: from nine until ___3",
     "Main task: arranging books on the ___4",
     "Extra benefit: a ___5 on books"],
    [(1, "bookshop", "Place of work: a ______",
      "Tom works in a bookshop", "Ish joyi."),
     (2, "Saturdays", "Day: ______", "works in a bookshop on Saturdays",
      "Hafta kuni."),
     (3, "five", "from nine until ______",
      "He starts at nine and finishes at five",
      "PARAFFRAZ: until = finishes at."),
     (4, "shelves", "arranging books on the ______",
      "putting new books on the shelves",
      "PARAFFRAZ: arranging = putting."),
     (5, "discount", "a ______ on books",
      "gets a discount on any book he buys",
      "PARAFFRAZ: extra benefit = gets ... as well as pay.")],
))

# ---------------------------------------------------------------- 4
PASSAGES.append(P(
    4, "THE VILLAGE SHOP",
    "The only shop in Kirby village was going to close in 2019 "
    "because the owner retired. The villagers decided to buy it "
    "themselves. Forty families each paid 100 pounds, and the shop "
    "now belongs to the community. It sells bread, milk and "
    "newspapers, and it is run by volunteers.",
    "Kirby village shop",
    ["Was due to shut in ___1",
     "Reason: the owner ___2",
     "Each family paid: ___3 pounds",
     "Goods sold: bread, ___4 and newspapers",
     "Now staffed by ___5"],
    [(1, "2019", "Was due to shut in ______",
      "was going to close in 2019",
      "PARAFFRAZ: was due to shut = was going to close."),
     (2, "retired", "the owner ______", "because the owner retired",
      "Sabab."),
     (3, "100", "Each family paid: ______ pounds",
      "Forty families each paid 100 pounds",
      "Chalg'ituvchi: «Forty» — oilalar soni, «100» — pul."),
     (4, "milk", "bread, ______ and newspapers",
      "It sells bread, milk and newspapers",
      "Ro'yxatning o'rtasi."),
     (5, "volunteers", "Now staffed by ______",
      "it is run by volunteers",
      "PARAFFRAZ: staffed by = run by.")],
))

# ---------------------------------------------------------------- 5
PASSAGES.append(P(
    5, "A MUSIC FESTIVAL",
    "The Riverside Music Festival takes place every July. It began in "
    "1998 with just two stages; today there are eight. Around 25,000 "
    "visitors attend, and tickets usually sell out within a week. "
    "Local businesses say the festival brings useful income, although "
    "some residents complain about the noise at night.",
    "Riverside Music Festival",
    ["Held: every ___1",
     "First held: ___2",
     "Stages now: ___3",
     "Audience: about ___4 people",
     "Complaint from ___5: night-time noise"],
    [(1, "July", "Held: every ______", "takes place every July",
      "PARAFFRAZ: held = takes place."),
     (2, "1998", "First held: ______", "It began in 1998",
      "PARAFFRAZ: first held = began."),
     (3, "eight", "Stages now: ______",
      "with just two stages; today there are eight",
      "Chalg'ituvchi: «two» — o'shandagi soni, «eight» — hozirgi."),
     (4, "25,000", "Audience: about ______ people",
      "Around 25,000 visitors attend",
      "PARAFFRAZ: about = around; audience = visitors."),
     (5, "residents", "Complaint from ______",
      "some residents complain about the noise",
      "PARAFFRAZ: residents = inhabitants (Unit 1 juftligi).")],
))

# ---------------------------------------------------------------- 6
PASSAGES.append(P(
    6, "LEARNING TO SWIM",
    "The council offers free swimming lessons to children under "
    "twelve. Classes last thirty minutes and are held on Wednesday "
    "afternoons at the leisure centre. Each group has a maximum of "
    "six children so that the teacher can give individual attention. "
    "Parents must fill in a form before the first lesson.",
    "Free swimming lessons",
    ["Cost: ___1",
     "For children aged under ___2",
     "Length of class: ___3 minutes",
     "Day: ___4 afternoons",
     "Group size: no more than ___5"],
    [(1, "free", "Cost: ______",
      "The council offers free swimming lessons",
      "Narx haqidagi so'z."),
     (2, "twelve", "aged under ______",
      "free swimming lessons to children under twelve", "Yosh."),
     (3, "thirty", "Length of class: ______ minutes",
      "Classes last thirty minutes", "PARAFFRAZ: length = last."),
     (4, "Wednesday", "Day: ______ afternoons",
      "held on Wednesday afternoons", "Hafta kuni."),
     (5, "six", "no more than ______",
      "Each group has a maximum of six children",
      "PARAFFRAZ: no more than = a maximum of.")],
))

# ---------------------------------------------------------------- 7
PASSAGES.append(P(
    7, "THE NIGHT BUS",
    "A night bus service started in the city three years ago. It runs "
    "from midnight until four in the morning on Fridays and "
    "Saturdays. The fare is double the daytime price. Passenger "
    "numbers have grown steadily, and the transport authority is now "
    "considering extending the service to Thursdays.",
    "City night bus",
    ["Introduced: ___1 years ago",
     "Operates: from ___2 to four a.m.",
     "Nights: Fridays and ___3",
     "Price: ___4 the daytime fare",
     "Possible change: also running on ___5"],
    [(1, "three", "Introduced: ______ years ago",
      "started in the city three years ago",
      "PARAFFRAZ: introduced = started."),
     (2, "midnight", "from ______ to four a.m.",
      "It runs from midnight until four in the morning",
      "PARAFFRAZ: a.m. = in the morning."),
     (3, "Saturdays", "Fridays and ______",
      "on Fridays and Saturdays", "Ro'yxatning ikkinchi qismi."),
     (4, "double", "______ the daytime fare",
      "The fare is double the daytime price",
      "PARAFFRAZ: fare = price."),
     (5, "Thursdays", "also running on ______",
      "considering extending the service to Thursdays",
      "PARAFFRAZ: possible change = considering.")],
))

# ---------------------------------------------------------------- 8
PASSAGES.append(P(
    8, "THE COMMUNITY GARDEN",
    "An area of waste ground behind the station has been turned into "
    "a community garden. Volunteers cleared the rubbish in 2021 and "
    "planted fruit trees and vegetables. The produce is shared among "
    "the helpers, and anything left over is given to a local charity. "
    "The main problem has been a shortage of water in summer.",
    "The community garden",
    ["Former use: ___1 ground",
     "Location: behind the ___2",
     "Cleared in: ___3",
     "Surplus food goes to a ___4",
     "Main difficulty: not enough ___5 in summer"],
    [(1, "waste", "______ ground", "An area of waste ground",
      "PARAFFRAZ: former use = what it was before."),
     (2, "station", "behind the ______",
      "waste ground behind the station", "Joy."),
     (3, "2021", "Cleared in: ______",
      "Volunteers cleared the rubbish in 2021", "Yil."),
     (4, "charity", "Surplus food goes to a ______",
      "anything left over is given to a local charity",
      "PARAFFRAZ: surplus = left over."),
     (5, "water", "not enough ______ in summer",
      "a shortage of water in summer",
      "PARAFFRAZ: not enough = a shortage of.")],
))

# ---------------------------------------------------------------- 9
PASSAGES.append(P(
    9, "A PHOTOGRAPHY COURSE",
    "The evening photography course is aimed at complete beginners. "
    "It consists of ten sessions and covers the basics of light, "
    "composition and editing. Students need their own camera, "
    "although a few can be borrowed from the college. The tutor, "
    "Maria Blake, has worked as a press photographer for over twenty "
    "years. Places are limited and the course is often fully booked "
    "by September.",
    "Evening photography course",
    ["Suitable for: total ___1",
     "Number of sessions: ___2",
     "Topics: light, ___3 and editing",
     "Equipment: students should bring their own ___4",
     "Tutor's background: ___5 photographer"],
    [(1, "beginners", "total ______",
      "aimed at complete beginners",
      "PARAFFRAZ: total = complete."),
     (2, "ten", "Number of sessions: ______",
      "It consists of ten sessions",
      "Chalg'ituvchi: «twenty» — tutorning ish staji."),
     (3, "composition", "light, ______ and editing",
      "covers the basics of light, composition and editing",
      "Ro'yxatning o'rtasi."),
     (4, "camera", "bring their own ______",
      "Students need their own camera",
      "PARAFFRAZ: should bring = need."),
     (5, "press", "______ photographer",
      "has worked as a press photographer",
      "Kasb turi.")],
))

# --------------------------------------------------------------- 10
#  JAHONGIRNING 1-NAMUNASI
PASSAGES.append(P(
    10, "READING #3. THE HAPPIEST COUNTRY IN THE WORLD",
    "Children growing up in Costa Rica are surrounded by some of the "
    "most beautiful and diverse landscapes in the world. Preserving "
    "tropical rainforests isn't Costa Rica's only success, because "
    "the government also makes sure everyone has access to "
    "health-care and education. So when the New Economics Foundation "
    "released its second Happy Planet Index, Costa Rica came out "
    "number one. The index is a ranking of countries based on their "
    "impact on the environment and the health and happiness of their "
    "citizens.\n\n"
    "According to Mariano Rojas, a Costa Rican economics professor, "
    "Costa Rica is a mid-income country where citizens have plenty of "
    "time for themselves and for their relationships with others. 'A "
    "mid-income level allows most citizens to satisfy their basic "
    "needs. The government makes sure that all Costa Ricans have "
    "access to education, health and nutrition services.' Costa "
    "Ricans, he believes, are not interested in status or spending "
    "money to show how successful they are.\n\n"
    "Created in 2008, the Happy Planet Index examines happiness on a "
    "national level and ranks 143 countries according to three "
    "measurements: their citizens' happiness, how long they live "
    "(which reflects their health), and how much of the planet's "
    "resources each country consumes. According to researcher Saamah "
    "Abdallah, the Index also measures the outcomes that are most "
    "important, and those are happy, healthy lives for everyone.",
    "The happy planet index",
    ["Year started: ___1",
     "Number of countries in lists: ___2",
     "Measures each country's happiness according to:",
     "• its effect on the ___3 (i.e. the quantity of the Earth's "
     "___4 that it uses)",
     "• the ___5 of the population (i.e. how long people live)",
     "• how happy its ___6 are"],
    [(1, "2008", "Year started", "Created in 2008, the Happy Planet "
      "Index", "PARAFFRAZ: started = created."),
     (2, "143", "Number of countries in lists",
      "ranks 143 countries according to three measurements",
      "PARAFFRAZ: lists = ranks. Chalg'ituvchi: «2008» — yil, "
      "«three» — o'lchov soni."),
     (3, "environment", "its effect on the ______",
      "a ranking of countries based on their impact on the "
      "environment", "PARAFFRAZ: effect = impact."),
     (4, "resources", "the quantity of the Earth's ______ that it "
      "uses",
      "how much of the planet's resources each country consumes",
      "PARAFFRAZ: the quantity = how much; uses = consumes; "
      "Earth = planet."),
     (5, "health", "the ______ of the population",
      "how long they live (which reflects their health)",
      "PARAFFRAZ: population = citizens. Qavs ichidagi izoh "
      "«how long people live» sizni to'g'ri jumlaga olib boradi."),
     (6, "citizens", "how happy its ______ are",
      "their citizens' happiness",
      "PARAFFRAZ: population = citizens.")],
))

# --------------------------------------------------------------- 11
#  JAHONGIRNING 2-NAMUNASI
PASSAGES.append(P(
    11, "READING #4. A CITY SURVEY WITH A DIFFERENCE",
    "There are many websites on the Internet which provide lists of "
    "the world's best cities to visit, live or work in. These lists "
    "usually grade the cities in order, from 'best' to 'worst', and "
    "are based on facts and figures provided by local or national "
    "organisations.\n\n"
    "The City Brands Index (CBI) also provides a list of best and "
    "worst cities. However, unlike other surveys, it is based on the "
    "idea that cities are similar to products in shops. It asks "
    "ordinary people in other countries to grade cities in the same "
    "way that they would grade a product, like a soft drink or a car. "
    "What is particularly different about the CBI is that the people "
    "who take part in the survey may have never visited the cities. "
    "Instead, they are asked to say what they think the cities are "
    "like, basing their opinions on things like news stories, "
    "magazine articles or television programmes they have heard or "
    "seen.\n\n"
    "Each year, about 10,000 people in 20 countries take part in the "
    "CBI survey, and they grade a total of 50 cities. They do this by "
    "filling in an online questionnaire. There are several categories "
    "in the survey. These include things like the economy, education, "
    "the environment, local culture, climate and what the city's "
    "residents are like.\n\n"
    "The CBI list is useful because it helps people choose a good "
    "place to live, find work or take a holiday. It also helps "
    "regional governments to understand why people and businesses "
    "are, or are not, coming to their cities, and so shows them areas "
    "which they could develop or improve.",
    "The City Brands Index",
    ["The CBI believes that cities are like ___1 which people can "
     "buy when they go shopping.",
     "Surveys take place every ___2. A maximum of ___3 cities are "
     "included in the survey.",
     "A number of different ___4 are included in the survey.",
     "The CBI list is helpful for:",
     "• people who are trying to decide where to ___5 or get a job",
     "• people who are looking for a good ___6 destination",
     "• local ___7 who want to make their city a better place"],
    [(1, "products", "cities are like ______",
      "it is based on the idea that cities are similar to products "
      "in shops", "PARAFFRAZ: like = similar to."),
     (2, "year", "Surveys take place every ______",
      "Each year, about 10,000 people in 20 countries take part",
      "PARAFFRAZ: every = each."),
     (3, "50", "A maximum of ______ cities",
      "they grade a total of 50 cities",
      "PARAFFRAZ: maximum = total. Chalg'ituvchi: 10,000 — "
      "odamlar, 20 — davlatlar."),
     (4, "categories", "A number of different ______",
      "There are several categories in the survey",
      "PARAFFRAZ: a number of = several."),
     (5, "live", "decide where to ______ or get a job",
      "it helps people choose a good place to live, find work",
      "PARAFFRAZ: get a job = find work."),
     (6, "holiday", "a good ______ destination",
      "find work or take a holiday",
      "PARAFFRAZ: destination = place to take a holiday."),
     (7, "governments", "local ______",
      "It also helps regional governments to understand",
      "PARAFFRAZ: local = regional.")],
))

# --------------------------------------------------------------- 12
PASSAGES.append(P(
    12, "THE RETURN OF REMOTE WORK",
    "When offices closed in 2020, remote working was treated as a "
    "temporary emergency measure. Five years later it has become a "
    "permanent feature of the labour market in most wealthy "
    "economies. A survey of 34,000 workers in twenty-seven countries "
    "found that employees now spend an average of 1.4 days a week at "
    "home. The figure is highest in English-speaking countries and "
    "lowest in Asia, where homes are typically smaller and commuting "
    "distances shorter. Employers report that the main advantage is a "
    "wider pool of candidates, since geography no longer limits "
    "recruitment. The most frequently mentioned drawback is the "
    "difficulty of training junior staff, who learn a great deal by "
    "overhearing more experienced colleagues.",
    "Remote working today",
    ["Began as a short-term response in ___1.",
     "Survey covered ___2 employees across twenty-seven countries.",
     "Workers are at home for an average of ___3 days each week.",
     "Rates are lowest in ___4, partly because journeys to work are "
     "shorter.",
     "Chief benefit for employers: a larger ___5 of applicants.",
     "Chief drawback: it is harder to ___6 new employees."],
    [(1, "2020", "short-term response in ______",
      "When offices closed in 2020, remote working was treated as a "
      "temporary emergency measure",
      "PARAFFRAZ: short-term = temporary."),
     (2, "34,000", "Survey covered ______ employees",
      "A survey of 34,000 workers in twenty-seven countries",
      "PARAFFRAZ: employees = workers. Chalg'ituvchi: 2020, 1.4, "
      "twenty-seven."),
     (3, "1.4", "average of ______ days each week",
      "employees now spend an average of 1.4 days a week at home",
      "PARAFFRAZ: each week = a week."),
     (4, "Asia", "Rates are lowest in ______",
      "lowest in Asia, where homes are typically smaller and "
      "commuting distances shorter",
      "PARAFFRAZ: journeys to work = commuting distances."),
     (5, "pool", "a larger ______ of applicants",
      "the main advantage is a wider pool of candidates",
      "PARAFFRAZ: larger = wider; applicants = candidates."),
     (6, "train", "harder to ______ new employees",
      "the difficulty of training junior staff",
      "PARAFFRAZ: harder = difficulty; new employees = junior "
      "staff. Bo'shliqdan oldin «to» — FE'L kerak.")],
))

# --------------------------------------------------------------- 13
PASSAGES.append(P(
    13, "THE STORY OF TEA",
    "Tea was first drunk in China, where legend attributes its "
    "discovery to the emperor Shen Nong. For centuries it remained an "
    "Asian beverage. Portuguese traders brought it to Europe in the "
    "sixteenth century, but it was the Dutch who established a "
    "regular trade. In Britain tea was at first a luxury; a pound of "
    "it cost more than a labourer earned in a month. Heavy taxation "
    "encouraged widespread smuggling, and only when the duty was cut "
    "sharply in 1784 did tea become an everyday drink. Today the "
    "largest producer is China, while the biggest consumers per "
    "person are the Turks.",
    "Tea: a short history",
    ["Origin: ___1, according to legend discovered by an emperor.",
     "First carried to Europe by ___2 merchants.",
     "Regular trade was set up by the ___3.",
     "In Britain it began as a ___4 — a pound cost more than a "
     "month's wages.",
     "High taxes led to ___5 until the duty fell in 1784."],
    [(1, "China", "Origin: ______", "Tea was first drunk in China",
      "PARAFFRAZ: origin = first drunk in."),
     (2, "Portuguese", "carried to Europe by ______ merchants",
      "Portuguese traders brought it to Europe",
      "PARAFFRAZ: merchants = traders; carried = brought."),
     (3, "Dutch", "trade was set up by the ______",
      "it was the Dutch who established a regular trade",
      "PARAFFRAZ: set up = established."),
     (4, "luxury", "began as a ______",
      "In Britain tea was at first a luxury",
      "PARAFFRAZ: began as = was at first."),
     (5, "smuggling", "High taxes led to ______",
      "Heavy taxation encouraged widespread smuggling",
      "PARAFFRAZ: high taxes = heavy taxation; led to = "
      "encouraged.")],
))

# --------------------------------------------------------------- 14
PASSAGES.append(P(
    14, "SCHOOL START TIMES",
    "Adolescents' body clocks shift later during puberty, so that a "
    "typical teenager does not feel sleepy until around eleven at "
    "night. Most secondary schools, however, begin before half past "
    "eight. In 2016 a district in Seattle moved the start of the "
    "school day back by nearly an hour. Researchers fitted students "
    "with wrist monitors and found that they gained thirty-four "
    "minutes of sleep each night. Attendance improved and grades rose "
    "by 4.5 percent. Opponents point out that later finishing times "
    "clash with after-school jobs and sports, and that the change "
    "creates difficulties for parents who leave for work early.",
    "Later school start times",
    ["Cause: during puberty the body ___1 moves later.",
     "Teenagers are not tired before about ___2 at night.",
     "Seattle delayed the start by almost an ___3 in 2016.",
     "Students slept an extra ___4 minutes.",
     "Marks improved by ___5 percent.",
     "Objection: clashes with sports and after-school ___6."],
    [(1, "clocks", "the body ______ moves later",
      "Adolescents' body clocks shift later during puberty",
      "PARAFFRAZ: moves = shift."),
     (2, "eleven", "not tired before about ______ at night",
      "does not feel sleepy until around eleven at night",
      "PARAFFRAZ: tired = sleepy; about = around."),
     (3, "hour", "delayed the start by almost an ______",
      "moved the start of the school day back by nearly an hour",
      "PARAFFRAZ: delayed = moved back; almost = nearly."),
     (4, "thirty-four", "an extra ______ minutes",
      "they gained thirty-four minutes of sleep each night",
      "PARAFFRAZ: extra = gained."),
     (5, "4.5", "Marks improved by ______ percent",
      "grades rose by 4.5 percent",
      "PARAFFRAZ: marks = grades; improved = rose."),
     (6, "jobs", "sports and after-school ______",
      "clash with after-school jobs and sports",
      "Ro'yxat tartibi almashgan — diqqat.")],
))

# --------------------------------------------------------------- 15
PASSAGES.append(P(
    15, "VERTICAL FORESTS",
    "The Bosco Verticale in Milan, completed in 2014, consists of two "
    "residential towers carrying around 900 trees and more than "
    "twenty thousand smaller plants. The architect, Stefano Boeri, "
    "calculated that the greenery absorbs roughly thirty tonnes of "
    "carbon dioxide a year and filters dust from the surrounding "
    "streets. Maintenance is unusual: a team of gardeners descends "
    "the facade on ropes three times a year. Critics argue that the "
    "buildings are expensive to construct and that planting the same "
    "number of trees at ground level would cost a fraction of the "
    "price.",
    "Bosco Verticale, Milan",
    ["Finished in ___1.",
     "Two ___2 blocks covered with plants.",
     "Approximately ___3 trees in total.",
     "Absorbs about thirty ___4 of carbon dioxide annually.",
     "Gardeners work from ___5, visiting three times a year.",
     "Criticism: the towers are ___6 to build."],
    [(1, "2014", "Finished in ______",
      "completed in 2014", "PARAFFRAZ: finished = completed."),
     (2, "residential", "Two ______ blocks",
      "consists of two residential towers",
      "PARAFFRAZ: blocks = towers."),
     (3, "900", "Approximately ______ trees",
      "carrying around 900 trees",
      "PARAFFRAZ: approximately = around. Chalg'ituvchi: «twenty "
      "thousand» — kichik o'simliklar."),
     (4, "tonnes", "about thirty ______ of carbon dioxide",
      "absorbs roughly thirty tonnes of carbon dioxide a year",
      "PARAFFRAZ: about = roughly; annually = a year."),
     (5, "ropes", "Gardeners work from ______",
      "a team of gardeners descends the facade on ropes",
      "Usul: arqonda tushadi."),
     (6, "expensive", "the towers are ______ to build",
      "Critics argue that the buildings are expensive to construct",
      "PARAFFRAZ: towers = buildings; to build = to construct. "
      "Matnning davomi «a fraction of the price» — yerga ekish "
      "ancha arzon degani.")],
))

# --------------------------------------------------------------- 16
PASSAGES.append(P(
    16, "THE RETURN OF THE WOLF",
    "Wolves were exterminated across most of western Europe by the "
    "early twentieth century. Legal protection introduced in the "
    "1970s, together with the abandonment of remote farmland, has "
    "allowed them to spread back. Germany, which had no resident "
    "wolves in 2000, now has more than two hundred packs. The animals "
    "have travelled remarkable distances: one collared male crossed "
    "1,500 kilometres of Poland and Germany in five months. Farmers' "
    "organisations demand compensation for livestock losses, which "
    "several governments now pay. Ecologists reply that wolves keep "
    "deer numbers down, which in turn allows young trees to survive.",
    "Wolves in western Europe",
    ["Almost wiped out by the early ___1 century.",
     "Recovery helped by ___2 protection from the 1970s.",
     "Also helped by the ___3 of distant farmland.",
     "Germany now has over ___4 packs.",
     "One tracked animal covered ___5 kilometres.",
     "Ecologists' argument: fewer ___6 means more young trees "
     "survive."],
    [(1, "twentieth", "the early ______ century",
      "by the early twentieth century",
      "PARAFFRAZ: almost wiped out = exterminated."),
     (2, "legal", "______ protection from the 1970s",
      "Legal protection introduced in the 1970s", "Himoya turi."),
     (3, "abandonment", "the ______ of distant farmland",
      "the abandonment of remote farmland",
      "PARAFFRAZ: distant = remote."),
     (4, "two hundred", "over ______ packs",
      "now has more than two hundred packs",
      "PARAFFRAZ: over = more than. Chalg'ituvchi: 2000 — yil, "
      "1,500 — masofa."),
     (5, "1,500", "covered ______ kilometres",
      "one collared male crossed 1,500 kilometres",
      "PARAFFRAZ: tracked = collared; covered = crossed."),
     (6, "deer", "fewer ______ means more young trees survive",
      "wolves keep deer numbers down, which in turn allows young "
      "trees to survive",
      "PARAFFRAZ: fewer = keep numbers down.")],
))

# --------------------------------------------------------------- 17
PASSAGES.append(P(
    17, "FOOD WASTE",
    "About a third of all food produced for human consumption is "
    "never eaten. In poorer countries most of the loss happens early "
    "— crops rot before they reach a market because storage and "
    "roads are inadequate. In richer countries the waste occurs at "
    "the end of the chain, in shops and above all in households, "
    "which throw away food that has passed a date printed on the "
    "packet. Researchers stress that these dates usually indicate "
    "quality rather than safety. If food waste were a country, its "
    "greenhouse gas emissions would rank third, behind only China and "
    "the United States.",
    "Food waste worldwide",
    ["Share never eaten: about one ___1.",
     "In poor countries loss happens ___2 in the chain.",
     "Main causes there: poor ___3 and roads.",
     "In rich countries most waste comes from ___4.",
     "Printed dates usually refer to ___5, not safety."],
    [(1, "third", "about one ______",
      "About a third of all food produced for human consumption "
      "is never eaten", "Ulush."),
     (2, "early", "loss happens ______ in the chain",
      "most of the loss happens early", "Vaqt nuqtasi."),
     (3, "storage", "poor ______ and roads",
      "because storage and roads are inadequate",
      "PARAFFRAZ: poor = inadequate."),
     (4, "households", "most waste comes from ______",
      "in shops and above all in households",
      "PARAFFRAZ: most = above all."),
     (5, "quality", "dates usually refer to ______",
      "these dates usually indicate quality rather than safety",
      "PARAFFRAZ: refer to = indicate.")],
))

# --------------------------------------------------------------- 18
PASSAGES.append(P(
    18, "THE SAND SHORTAGE",
    "Sand is the second most heavily used natural resource after "
    "water, and the world consumes roughly fifty billion tonnes a "
    "year, chiefly for concrete. Desert sand is useless for building "
    "because wind erosion makes the grains too round to bind "
    "together. The material must therefore come from riverbeds, "
    "beaches and the sea floor, where dredging destroys habitats and "
    "undermines riverbanks. In some regions organised gangs now "
    "control extraction, and journalists investigating the trade have "
    "been attacked. Engineers are testing substitutes made from "
    "crushed rock and recycled glass, but neither is yet cheap enough "
    "to replace natural sand.",
    "The sand crisis",
    ["Only ___1 is used more heavily.",
     "Annual consumption: about ___2 billion tonnes.",
     "Main use: making ___3.",
     "Desert sand fails because the grains are too ___4.",
     "Extraction from rivers damages ___5 and weakens riverbanks.",
     "Possible replacements: crushed rock and recycled ___6."],
    [(1, "water", "Only ______ is used more heavily",
      "the second most heavily used natural resource after water",
      "PARAFFRAZ: only X is used more = second after X."),
     (2, "fifty", "about ______ billion tonnes",
      "the world consumes roughly fifty billion tonnes a year",
      "PARAFFRAZ: about = roughly."),
     (3, "concrete", "Main use: making ______",
      "chiefly for concrete", "PARAFFRAZ: main = chiefly."),
     (4, "round", "grains are too ______",
      "wind erosion makes the grains too round to bind together",
      "To'g'ridan-to'g'ri sifat."),
     (5, "habitats", "damages ______ and weakens riverbanks",
      "dredging destroys habitats and undermines riverbanks",
      "PARAFFRAZ: damages = destroys; weakens = undermines."),
     (6, "glass", "crushed rock and recycled ______",
      "substitutes made from crushed rock and recycled glass",
      "PARAFFRAZ: replacements = substitutes.")],
))

# --------------------------------------------------------------- 19
PASSAGES.append(P(
    19, "WHY VISITORS LEAVE MUSEUMS",
    "A study tracked 2,400 visitors through four national museums "
    "using anonymous sensors. The average stay was fifty-one minutes, "
    "far shorter than curators assume, and attention declined sharply "
    "after the first twenty exhibits — a phenomenon the authors call "
    "museum fatigue. Visitors who sat down at least once stayed "
    "nineteen minutes longer than those who did not, yet seating was "
    "scarce in three of the four buildings. Labels longer than fifty "
    "words were read in full by fewer than one visitor in ten. The "
    "researchers recommend shorter texts, more benches and clearer "
    "routes rather than additional objects.",
    "Museum visitor study",
    ["Number of visitors monitored: ___1.",
     "Average visit length: ___2 minutes.",
     "Concentration falls after roughly ___3 exhibits.",
     "Those who ___4 stayed nineteen minutes longer.",
     "Labels over ___5 words are rarely read completely.",
     "Advice: shorter texts, more ___6 and clearer routes."],
    [(1, "2,400", "Number of visitors monitored: ______",
      "A study tracked 2,400 visitors through four national museums",
      "PARAFFRAZ: monitored = tracked. Chalg'ituvchi: four, "
      "fifty-one, twenty, nineteen, fifty, ten."),
     (2, "fifty-one", "Average visit length: ______ minutes",
      "The average stay was fifty-one minutes",
      "PARAFFRAZ: visit length = stay."),
     (3, "twenty", "falls after roughly ______ exhibits",
      "attention declined sharply after the first twenty exhibits",
      "PARAFFRAZ: concentration = attention; falls = declined."),
     (4, "sat", "Those who ______ stayed nineteen minutes longer",
      "Visitors who sat down at least once stayed nineteen minutes "
      "longer", "Bo'shliqqa FE'L kerak."),
     (5, "fifty", "Labels over ______ words",
      "Labels longer than fifty words were read in full by fewer "
      "than one visitor in ten",
      "PARAFFRAZ: over = longer than; rarely read completely = "
      "read in full by fewer than one in ten."),
     (6, "benches", "shorter texts, more ______ and clearer routes",
      "recommend shorter texts, more benches and clearer routes",
      "PARAFFRAZ: advice = recommend.")],
))

# --------------------------------------------------------------- 20
PASSAGES.append(P(
    20, "ANTIBIOTIC RESISTANCE",
    "Alexander Fleming warned in his Nobel lecture of 1945 that "
    "careless use of penicillin would breed resistant bacteria. His "
    "prediction has been fulfilled: an estimated 1.3 million deaths "
    "are now directly attributable to resistant infections each year, "
    "a toll comparable to malaria. Two forces drive the problem. The "
    "first is over-prescription — a large share of the antibiotics "
    "given for sore throats treat viral illnesses against which the "
    "drugs are powerless. The second, and quantitatively greater, is "
    "agriculture, where antibiotics are added routinely to animal "
    "feed to accelerate growth. Developing a new class of antibiotic "
    "takes over a decade and rarely repays the investment, so most "
    "large pharmaceutical firms abandoned the field years ago.",
    "Antibiotic resistance",
    ["Fleming's warning came in his ___1 lecture in 1945.",
     "Deaths caused directly each year: about ___2 million.",
     "First cause: doctors prescribe them for ___3 illnesses they "
     "cannot cure.",
     "Second and larger cause: use in ___4, mainly to speed up "
     "animal ___5.",
     "New antibiotics take more than a ___6 to develop.",
     "Result: most big ___7 companies have left this area."],
    [(1, "Nobel", "his ______ lecture in 1945",
      "Alexander Fleming warned in his Nobel lecture of 1945",
      "Ma'ruza turi."),
     (2, "1.3", "about ______ million",
      "an estimated 1.3 million deaths",
      "PARAFFRAZ: about = an estimated. Chalg'ituvchi: 1945 — yil."),
     (3, "viral", "prescribe them for ______ illnesses",
      "a large share of the antibiotics given for sore throats "
      "treat viral illnesses against which the drugs are powerless",
      "PARAFFRAZ: cannot cure = the drugs are powerless."),
     (4, "agriculture", "use in ______",
      "The second, and quantitatively greater, is agriculture",
      "PARAFFRAZ: larger = quantitatively greater."),
     (5, "growth", "to speed up animal ______",
      "added routinely to animal feed to accelerate growth",
      "PARAFFRAZ: speed up = accelerate."),
     (6, "decade", "more than a ______ to develop",
      "Developing a new class of antibiotic takes over a decade",
      "PARAFFRAZ: more than = over."),
     (7, "pharmaceutical", "most big ______ companies",
      "most large pharmaceutical firms abandoned the field",
      "PARAFFRAZ: big = large; companies = firms.")],
))


# =====================================================================
#  YIG'ISH
# =====================================================================
NUM_ALT = {
    "three": "3", "five": "5", "ten": "10", "six": "6",
    "twelve": "12", "thirty": "30", "eight": "8", "eleven": "11",
    "forty": "40", "fifty": "50", "twentieth": "20th",
    "thirty-four": "34", "fifty-one": "51", "twenty": "20",
    "two hundred": "200", "third": "1/3",
}


def _mask(line, keep):
    s = str(line)
    for k in range(1, 12):
        s = s.replace(f"___{k}", GAP if k == keep else "…")
    return s


def _cefr(level):
    if level <= 5:
        return "A2"
    if level <= 9:
        return "B1"
    if level <= 14:
        return "B2"
    return "C1"


def _prompt_for(lines, n, fallback):
    mark = f"___{n}"
    for ln in lines:
        if mark in ln:
            return _mask(ln, n).lstrip("• ").strip()
    return str(fallback).replace("______", GAP)


def build_rows():
    out = []
    for p in PASSAGES:
        for i, (n, ans, cue, psg, note) in enumerate(p["gaps"]):
            payload = {
                "title": p["title"],
                "passage": p["text"],
                "summary_title": p["summary_title"],
                # Xulosada FAQAT shu bo'shliq ochiq, qolganlari "…"
                "summary": [_mask(ln, n) for ln in p["lines"]],
                "gap_no": n,
                "in_table": False,
                "prompt": _prompt_for(p["lines"], n, cue),
                "step": p["level"],
                "order": i,
                "step_title": f"{p['level']}-daraja",
                "tip": "Paraffrazni toping",
                "instruction": ("Complete the summary. Choose ONE "
                                "WORD OR A NUMBER from the passage."),
            }
            explain = f"Xulosada: «{cue}»  ->  Matnda: «{psg}». {note}"
            alt = NUM_ALT.get(ans.lower(), "")
            out.append((KIND, _cefr(p["level"]), payload, ans,
                        explain, alt, {"table": cue, "passage": psg}))
    return out


def seed_reading_summary(db):
    """Idempotent: (kind, passage, gap_no) bo'yicha."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_read_summary_v1"):
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
    _seed_mark(db, "ielts_read_summary_v1")
    return made
