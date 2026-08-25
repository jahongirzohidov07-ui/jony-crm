# -*- coding: utf-8 -*-
"""IELTS READING — TABLE COMPLETION (2026-08-25).

Jahongir: "keyin Table Completion qilaylik unda birinchi men senga
mashqlar tashlayman unit 1 paraphrases [famous=well-known,
inhabitants=populations, lifestyle=way of life, don't have so much=
have less, has reputation for=known for, have little=be short of,
don't pay attention to=ignore, excellent=very good, very=extremely,
residents=inhabitants, quality of life=standard of living,
most pleasant=nicest, not many=very few].

Shunaqa paraphraselar topish skillari rivojlanishi kerak, javoblar
tushuntirilganda readingda doim paraphraselarni korsatib
tushuntirish kerak, senga misollar tashladim shunaqa qilib tuzib
ber bundan ozgina osonroqlaridan boshlab buni 10-ga qoyasan va
sekin qiyinlashib boraversin 100ta mashq."

TUZILISHI. 20 ta matn x 5 bo'sh joy = 100 mashq. Daraja 1..20:
  1-9    — Jahongir yuborgan namunadan OSONROQ: qisqa matn, jadval
           iborasi matndagi iboraga juda yaqin;
  10     — "THE WORLD'S FRIENDLIEST CITY" (Jahongirning 1-namunasi,
           aynan o'zi);
  11     — "THE BEST CITIES IN THE WORLD" (2-namunasi);
  12-20  — qiyinlashib boradi: matn uzayadi, ilmiy uslubga o'tadi,
           paraffraz uzoqlashadi va chalg'ituvchi sonlar qo'shiladi.

ENG MUHIMI — IZOH. Har bir javobdan keyin PARAFFRAZ ko'rsatiladi:
    Jadvalda: «have little»  ->  Matnda: «be short of»
Ya'ni bola javobni emas, javobni TOPISH USULINI o'rganadi.
"""

SKILL = "ielts_reading"
KIND = "read_table"
GAP = "______"

# =====================================================================
#  QOIDALAR — mashq boshida o'qitiladi
# =====================================================================
TABLE_TIPS = [
    ("Table Completion nima",
     "Matndagi ma'lumot jadvalga joylashtirilgan, ba'zi kataklar "
     "bo'sh. Bo'shliqqa MATNDAN olingan so'z yoziladi — o'zingizdan "
     "so'z o'ylab topilmaydi va so'z shakli o'zgartirilmaydi.",
     "Jadval: «Has reputation for ______»\n"
     "Matn: «Rio de Janeiro, which is often known for its crime»\n"
     "Javob: crime"),
    ("ASOSIY KO'NIKMA — paraffrazni ko'rish",
     "Jadvaldagi ibora matnda AYNAN takrorlanmaydi — u boshqa so'z "
     "bilan aytiladi. Shuning uchun so'zma-so'z qidirish ishlamaydi. "
     "Avval jadvaldagi iborani MA'NOSIGA ko'chiring, keyin matndan "
     "o'sha ma'noni qidiring.",
     "Jadval: «have little»  ->  Matn: «be short of»\n"
     "Jadval: «don't pay attention to»  ->  Matn: «ignore»\n"
     "Jadval: «don't have so much»  ->  Matn: «have less»"),
    ("Unit 1 — yodlab olinadigan juftliklar",
     "Bular imtihonda eng ko'p uchraydiganlari:\n"
     "famous = well-known · inhabitants = populations · "
     "lifestyle = way of life · don't have so much = have less · "
     "has reputation for = known for · have little = be short of · "
     "don't pay attention to = ignore · excellent = very good · "
     "very = extremely · residents = inhabitants · "
     "quality of life = standard of living · most pleasant = nicest · "
     "not many = very few", ""),
    ("Bo'sh joy ATROFIDAGI so'zlarni o'qing",
     "Bo'shliqdan oldingi va keyingi so'z javobning turini aytadi: "
     "«more ______ lifestyle» — bu yerda SIFAT kerak; "
     "«Has excellent ______ opportunities» — bu yerda OT kerak.",
     "«more ______ lifestyle» -> relaxed (sifat)\n"
     "«a lot of ______» -> traffic (ot)"),
    ("Ustun sarlavhasi — yo'l ko'rsatgich",
     "Qatorni topish uchun chap ustunga (shahar, yil, nom) qarang; "
     "qaysi ma'lumot kerakligini esa TEPADAGI sarlavha aytadi — "
     "«Positive aspects» va «Negative aspects» ikki xil javob "
     "talab qiladi.", ""),
    ("Nechta so'z ruxsat etilgan",
     "«ONE WORD» desa — bitta so'z. «NO MORE THAN TWO WORDS» desa "
     "ikkitagacha. Ortiqcha so'z yozsangiz javob NOTO'G'RI sanaladi, "
     "hatto ma'nosi to'g'ri bo'lsa ham.", ""),
    ("Jadval matn TARTIBI bilan boradi",
     "Jadval kataklari odatda matndagi ketma-ketlikni takrorlaydi. "
     "2-javobni topgan bo'lsangiz, 3-javob matnda undan KEYIN "
     "keladi — orqaga qaytib vaqt yo'qotmang.", ""),
    ("Chalg'ituvchi sonlardan ehtiyot bo'ling",
     "Matnda bir nechta son bo'ladi (53%, 44%, 93%). Jadvaldagi "
     "qator qaysi shaharga tegishli ekanini tekshirmasdan birinchi "
     "ko'ringan sonni yozmang.", ""),
]


# =====================================================================
#  MATNLAR
#  P(daraja, sarlavha, matn, ustunlar, qatorlar, bo'shliqlar)
#  Qatorlarda bo'shliq "___1" ko'rinishida yoziladi.
#  Bo'shliq: (raqam, javob, JADVALdagi ibora, MATNdagi ibora, izoh)
# =====================================================================
def P(level, title, text, headers, rows, gaps):
    return {"level": level, "title": title, "text": text,
            "headers": headers, "rows": rows, "gaps": gaps}


PASSAGES = []

# ---------------------------------------------------------------- 1
PASSAGES.append(P(
    1, "TWO SCHOOL CLUBS",
    "The chess club meets on Tuesday in room 12. It costs nothing to "
    "join and it has fourteen members. The drama club meets on Friday "
    "in the main hall. Members pay a small fee of five pounds a term, "
    "and the group is much larger — thirty students take part.",
    ["Club", "Day", "Place", "Cost", "Members"],
    [["Chess", "Tuesday", "Room 12", "___1", "14"],
     ["Drama", "___2", "___3", "5 pounds a term", "___4"]],
    [(1, "nothing", "Cost", "It costs nothing to join",
      "Jadvalda ustun sarlavhasi «Cost», matnda esa «costs "
      "nothing» — narx haqidagi jumla shu."),
     (2, "Friday", "Day", "The drama club meets on Friday",
      "«Day» ustuni — matndagi hafta kunini qidiring."),
     (3, "hall", "Place", "in the main hall",
      "«Place» = joy. Matnda «main hall» deyilgan, bitta so'z "
      "so'ralgani uchun «hall»."),
     (4, "thirty", "Members", "thirty students take part",
      "«Members» = a'zolar. Matnda «students take part» — "
      "boshqa so'z, bir xil ma'no."),
     (5, "larger", "The group is much ______ than the chess club",
      "the group is much larger",
      "Taqqoslash: matnda «much larger» aynan shu ma'noda.")],
))

# ---------------------------------------------------------------- 2
PASSAGES.append(P(
    2, "THE CITY LIBRARY",
    "The city library opens at nine in the morning and closes at "
    "seven in the evening. It holds about 40,000 books. Membership is "
    "free for anyone living in the city. The reading room upstairs is "
    "very quiet, but the ground floor is often noisy because of the "
    "children's area.",
    ["Feature", "Detail"],
    [["Opening time", "___1 o'clock"],
     ["Number of books", "about ___2"],
     ["Membership", "___3 for residents"],
     ["Reading room", "extremely ___4"],
     ["Ground floor", "___5 because of children"]],
    [(1, "nine", "Opening time", "opens at nine in the morning",
      "«Opening time» = ochilish vaqti."),
     (2, "40,000", "Number of books", "It holds about 40,000 books",
      "«Number of books» = kitoblar soni; matnda «holds about»."),
     (3, "free", "Membership", "Membership is free",
      "«for residents» = «for anyone living in the city» — "
      "residents = shu yerda yashovchilar."),
     (4, "quiet", "extremely", "very quiet",
      "PARAFFRAZ: extremely = very. Unit 1 dagi juftlik."),
     (5, "noisy", "because of children", "noisy because of the "
      "children's area",
      "Sabab bir xil, so'z shakli qisqargan.")],
))

# ---------------------------------------------------------------- 3
PASSAGES.append(P(
    3, "A SMALL CAFE",
    "The Blue Cup is a small cafe near the station. It is well-known "
    "for its coffee, which many people say is the best in town. The "
    "cafe is open every day except Monday. There are only twelve "
    "tables, so it fills up quickly at lunchtime.",
    ["Question", "Answer"],
    [["Where is it?", "near the ___1"],
     ["What is it famous for?", "its ___2"],
     ["When is it closed?", "___3"],
     ["How many tables?", "only ___4"],
     ["When is it busy?", "at ___5"]],
    [(1, "station", "Where is it?", "a small cafe near the station",
      "Joy haqidagi jumla."),
     (2, "coffee", "famous for", "It is well-known for its coffee",
      "PARAFFRAZ: famous = well-known. Unit 1 dagi birinchi "
      "juftlik."),
     (3, "Monday", "When is it closed?",
      "open every day except Monday",
      "«closed» — matnda to'g'ridan-to'g'ri emas: «except "
      "Monday» degani dushanba yopiq."),
     (4, "twelve", "How many tables?", "There are only twelve tables",
      "Son so'ralgan."),
     (5, "lunchtime", "When is it busy?",
      "it fills up quickly at lunchtime",
      "PARAFFRAZ: busy = fills up quickly.")],
))

# ---------------------------------------------------------------- 4
PASSAGES.append(P(
    4, "TWO SPORTS CENTRES",
    "Riverside Sports Centre has a swimming pool and a gym. It is "
    "very popular with families because the staff are helpful. "
    "Hillview Centre has excellent tennis courts, but it is quite "
    "expensive and it has very few parking spaces.",
    ["Centre", "Good points", "Bad points"],
    [["Riverside", "pool, gym, ___1 staff", "—"],
     ["Hillview", "very good ___2 courts", "___3; not many ___4"]],
    [(1, "helpful", "Good points — staff", "the staff are helpful",
      "«Good points» ustuni ijobiy tomonni so'rayapti."),
     (2, "tennis", "very good", "has excellent tennis courts",
      "PARAFFRAZ: very good = excellent. Unit 1 juftligi."),
     (3, "expensive", "Bad points", "it is quite expensive",
      "«Bad points» — salbiy tomon."),
     (4, "parking", "not many", "it has very few parking spaces",
      "PARAFFRAZ: not many = very few. Unit 1 juftligi."),
     (5, "families", "Riverside is popular with ______",
      "very popular with families",
      "Kim bilan mashhur — shuni topish kerak.")],
))

# ---------------------------------------------------------------- 5
PASSAGES.append(P(
    5, "TWO SEASIDE TOWNS",
    "Seaton is a quiet town with a population of only 4,000. Its "
    "inhabitants are mostly older people, and the way of life there "
    "is slow and peaceful. Redcliff, twenty kilometres away, has a "
    "much bigger population of 60,000. It is known for its nightlife "
    "and attracts young visitors every summer.",
    ["Town", "Population", "Character"],
    [["Seaton", "___1", "slow, ___2 lifestyle"],
     ["Redcliff", "___3", "has a reputation for its ___4"]],
    [(1, "4,000", "Population", "a population of only 4,000",
      "«Population» ustuni — aholi soni."),
     (2, "peaceful", "slow, ______ lifestyle",
      "the way of life there is slow and peaceful",
      "PARAFFRAZ: lifestyle = way of life. Jadvaldagi «lifestyle» "
      "sizni matndagi «way of life» ga olib boradi — javob o'sha "
      "jumlada."),
     (3, "60,000", "Population", "a much bigger population of 60,000",
      "Ikkinchi shahar qatoridagi son."),
     (4, "nightlife", "has a reputation for",
      "It is known for its nightlife",
      "PARAFFRAZ: has a reputation for = known for. Unit 1 "
      "juftligi."),
     (5, "young", "Redcliff attracts ______ visitors",
      "attracts young visitors every summer",
      "Bo'shliqdan keyin «visitors» turibdi — sifat kerak.")],
))

# ---------------------------------------------------------------- 6
PASSAGES.append(P(
    6, "BICYCLE HIRE IN THE CITY",
    "The city bicycle scheme started in 2019. There are now 45 "
    "stations and about 600 bicycles. Users pay one pound for the "
    "first thirty minutes; after that the price rises sharply. The "
    "scheme is popular with commuters, although many complain that "
    "the bikes are often short of air in the tyres.",
    ["Item", "Information"],
    [["Year it began", "___1"],
     ["Stations", "___2"],
     ["Price for 30 minutes", "one ___3"],
     ["Main users", "___4"],
     ["Common complaint", "tyres have little ___5"]],
    [(1, "2019", "Year it began", "The city bicycle scheme started "
      "in 2019", "«began» = «started»."),
     (2, "45", "Stations", "There are now 45 stations",
      "Aniq son."),
     (3, "pound", "Price for 30 minutes",
      "pay one pound for the first thirty minutes",
      "«30 minutes» = «thirty minutes» — raqam va so'z bir xil."),
     (4, "commuters", "Main users", "popular with commuters",
      "«Main users» = asosiy foydalanuvchilar."),
     (5, "air", "have little", "the bikes are often short of air",
      "PARAFFRAZ: have little = be short of. Unit 1 juftligi.")],
))

# ---------------------------------------------------------------- 7
PASSAGES.append(P(
    7, "WEEKEND MARKETS",
    "The Old Square market sells fruit and vegetables and opens at "
    "six in the morning. Prices there are low because the farmers "
    "sell directly. The Harbour market opens later, at ten, and "
    "specialises in fish. It is more expensive, but the quality is "
    "the nicest in the region.",
    ["Market", "Opens", "Sells", "Prices", "Note"],
    [["Old Square", "___1", "fruit and ___2", "___3", "farmers sell "
      "directly"],
     ["Harbour", "ten", "___4", "higher", "most pleasant ___5"]],
    [(1, "six", "Opens", "opens at six in the morning",
      "Ochilish vaqti."),
     (2, "vegetables", "Sells", "sells fruit and vegetables",
      "Ro'yxatning ikkinchi qismi."),
     (3, "low", "Prices", "Prices there are low",
      "Narx haqidagi so'z."),
     (4, "fish", "Sells", "specialises in fish",
      "PARAFFRAZ: sells = specialises in."),
     (5, "quality", "most pleasant", "the quality is the nicest",
      "PARAFFRAZ: most pleasant = nicest. Unit 1 juftligi.")],
))

# ---------------------------------------------------------------- 8
PASSAGES.append(P(
    8, "LANGUAGE COURSES",
    "The Morning Course runs for eight weeks and costs 200 pounds. "
    "Classes are small — no more than ten learners. The Evening "
    "Course lasts twelve weeks and is cheaper at 150 pounds, but "
    "groups are extremely large, sometimes with twenty-five students "
    "in one room.",
    ["Course", "Length", "Price", "Group size"],
    [["Morning", "___1 weeks", "200 pounds", "not many — max ___2"],
     ["Evening", "twelve weeks", "___3 pounds", "very ___4 — up to "
      "___5"]],
    [(1, "eight", "Length", "runs for eight weeks",
      "PARAFFRAZ: length = runs for."),
     (2, "ten", "not many — max", "no more than ten learners",
      "PARAFFRAZ: not many = no more than / very few."),
     (3, "150", "Price", "cheaper at 150 pounds",
      "Ikkinchi kurs narxi."),
     (4, "large", "very", "groups are extremely large",
      "PARAFFRAZ: very = extremely. Unit 1 juftligi."),
     (5, "twenty-five", "up to", "sometimes with twenty-five students",
      "«up to» = eng ko'pi bilan.")],
))

# ---------------------------------------------------------------- 9
PASSAGES.append(P(
    9, "CITY TRANSPORT SURVEY",
    "A survey of three cities looked at how people travel to work. In "
    "Bergen, 38 percent cycle, and the residents say the air is "
    "clean. In Turin, buses are used by most people, but passengers "
    "ignore the timetables because they are unreliable. In Porto, the "
    "metro is excellent, though the standard of living is lower than "
    "in the other two cities.",
    ["City", "Main transport", "Positive", "Negative"],
    [["Bergen", "bicycle (___1%)", "___2 air", "—"],
     ["Turin", "___3", "—", "people don't pay attention to ___4"],
     ["Porto", "metro", "very good service", "lower ___5 of life"]],
    [(1, "38", "bicycle (___%)", "38 percent cycle",
      "Foizni to'g'ri shahar qatoriga qo'ying."),
     (2, "clean", "___ air", "the air is clean",
      "«residents say» = «inhabitants say» — Unit 1: residents = "
      "inhabitants."),
     (3, "buses", "Main transport", "buses are used by most people",
      "Eng ko'p ishlatiladigan transport."),
     (4, "timetables", "don't pay attention to",
      "passengers ignore the timetables",
      "PARAFFRAZ: don't pay attention to = ignore. Unit 1 "
      "juftligi."),
     (5, "standard", "___ of life", "the standard of living is lower",
      "PARAFFRAZ: quality of life = standard of living. Unit 1 "
      "juftligi.")],
))

# --------------------------------------------------------------- 10
#  JAHONGIRNING 1-NAMUNASI — aynan o'zi
PASSAGES.append(P(
    10, "THE WORLD'S FRIENDLIEST CITY",
    "A team of social psychologists from California has spent six "
    "years studying the reactions of people in cities around the "
    "world to different situations. The results show that cities "
    "where people have less money generally have friendlier "
    "populations. Rio de Janeiro in Brazil, which is often known for "
    "its crime, comes out top, and the capital of Malawi, Lilongwe, "
    "comes third.\n\n"
    "But what makes one city friendlier than another? The "
    "psychologists from California State University say it has got "
    "more to do with environment than culture or nationality.\n\n"
    "They carried out a study into the way locals treated strangers "
    "in 23 cities around the world. The team conducted their research "
    "through a series of tests, where they dropped pens or pretended "
    "they were blind and needed help crossing the street.\n\n"
    "The study concludes that people are more helpful in cities with "
    "a more relaxed way of life such as Rio. While they were there, "
    "researchers received help in 93 percent of cases, and the "
    "percentage in Lilongwe was only a little lower. However, richer "
    "cities such as Amsterdam and New York are considered the least "
    "friendly. Inhabitants of Amsterdam helped the researchers in 53 "
    "percent of cases and in New York just 44 percent. The "
    "psychologists found that, in these cities, people tend to be "
    "short of time, so they hurry and often ignore strangers.",
    ["City", "Positive aspects", "Negative aspects",
     "% of help received"],
    [["Rio de Janeiro", "friendly inhabitants; more ___1 lifestyle",
      "people don't have so much ___2; has reputation for ___3",
      "93%"],
     ["Amsterdam and New York", "Richer",
      "have little ___4; don't pay attention to ___5",
      "Amsterdam 53% / New York 44%"]],
    [(1, "relaxed", "more ______ lifestyle",
      "cities with a more relaxed way of life",
      "PARAFFRAZ: lifestyle = way of life. Bo'shliqdan keyin ot "
      "turgani uchun SIFAT kerak. Shu qatorda yana bir juftlik "
      "bor: jadvaldagi «friendly inhabitants» matnda «friendlier "
      "populations» — inhabitants = populations."),
     (2, "money", "don't have so much", "cities where people have "
      "less money",
      "PARAFFRAZ: don't have so much = have less."),
     (3, "crime", "has reputation for",
      "Rio de Janeiro, which is often known for its crime",
      "PARAFFRAZ: has reputation for = known for."),
     (4, "time", "have little", "people tend to be short of time",
      "PARAFFRAZ: have little = be short of."),
     (5, "strangers", "don't pay attention to",
      "they hurry and often ignore strangers",
      "PARAFFRAZ: don't pay attention to = ignore.")],
))

# --------------------------------------------------------------- 11
#  JAHONGIRNING 2-NAMUNASI
PASSAGES.append(P(
    11, "THE BEST CITIES IN THE WORLD",
    "In a recent internet survey, tourists and business travellers "
    "were asked to rate 50 cities around the world, from the best to "
    "the worst. Of the top three cities, two were in Europe and one "
    "was in Australia.\n\n"
    "In third place was London, scoring highly mainly because it was "
    "the most famous city on the list of 50 surveyed. It was also "
    "seen as a very good place to do business, and was an important "
    "cultural centre. However, it lost points because people believed "
    "it was an extremely expensive place to live.\n\n"
    "Sydney was also a very popular destination, achieving second "
    "place on the list because people believed it had the friendliest "
    "inhabitants, as well as the best standard of living and the "
    "nicest climate. It failed to make the top spot, however, because "
    "people thought there were very few things to see there.\n\n"
    "At the top of the list was Paris. Despite problems such as the "
    "large amount of traffic, it beat other cities to first place "
    "because people considered it to be the most interesting city, "
    "with more museums, art galleries and places of interest than "
    "anywhere else.",
    ["City", "Position", "Perceived advantages",
     "Perceived disadvantages"],
    [["London", "Third", "more well-known; excellent ___1 "
      "opportunities", "very ___2"],
     ["Sydney", "Second", "residents are the ___3; best quality of "
      "life; most pleasant ___4", "not many things to see"],
     ["Paris", "First", "more interesting", "a lot of ___5"]],
    [(1, "business", "excellent ______ opportunities",
      "seen as a very good place to do business",
      "PARAFFRAZ: excellent = very good."),
     (2, "expensive", "very ______", "an extremely expensive place "
      "to live", "PARAFFRAZ: very = extremely."),
     (3, "friendliest", "residents are the ______",
      "it had the friendliest inhabitants",
      "PARAFFRAZ: residents = inhabitants."),
     (4, "climate", "most pleasant ______", "the nicest climate",
      "PARAFFRAZ: most pleasant = nicest."),
     (5, "traffic", "a lot of ______",
      "the large amount of traffic",
      "PARAFFRAZ: a lot of = large amount of.")],
))

# --------------------------------------------------------------- 12
PASSAGES.append(P(
    12, "WORKING FROM HOME",
    "A study of 2,000 office employees compared three working "
    "patterns. Those who worked entirely from home reported the "
    "greatest satisfaction with their way of life, but nearly half "
    "admitted that they felt isolated. Employees in the office five "
    "days a week were the least content, mainly because commuting "
    "left them short of free time. The hybrid group, who divided "
    "their week between the two, produced the strongest results: "
    "their output rose by 12 percent, although managers complained "
    "that supervision became harder.",
    ["Pattern", "Main benefit", "Main drawback", "Effect on output"],
    [["Fully at home", "best ___1 with lifestyle", "felt ___2", "—"],
     ["Fully in office", "—", "have little ___3", "lowest"],
     ["Hybrid", "—", "___4 became difficult", "up ___5%"]],
    [(1, "satisfaction", "best ______ with lifestyle",
      "reported the greatest satisfaction with their way of life",
      "PARAFFRAZ: best = greatest; lifestyle = way of life."),
     (2, "isolated", "felt ______", "they felt isolated",
      "His-tuyg'u haqidagi so'z."),
     (3, "time", "have little ______",
      "commuting left them short of free time",
      "PARAFFRAZ: have little = be short of."),
     (4, "supervision", "______ became difficult",
      "managers complained that supervision became harder",
      "PARAFFRAZ: difficult = harder."),
     (5, "12", "up ______%", "their output rose by 12 percent",
      "PARAFFRAZ: up = rose by. Chalg'ituvchi son: 2,000 — u "
      "xodimlar soni, natija emas.")],
))

# --------------------------------------------------------------- 13
PASSAGES.append(P(
    13, "THE COFFEE TRADE",
    "Coffee is grown in more than seventy countries, but two of them "
    "dominate. Brazil, whose plantations cover vast areas of the "
    "south-east, produces roughly a third of the world total. Vietnam "
    "comes second; its growers concentrate on the robusta variety, "
    "which is cheaper and is used mainly in instant coffee. Colombia "
    "is famous for the quality of its beans rather than the quantity, "
    "and its farms are usually small, family-run businesses.",
    ["Country", "Position", "Known for", "Farm size"],
    [["Brazil", "first", "about a ___1 of world output",
      "___2 cover very large areas"],
     ["Vietnam", "___3", "___4 variety, used in instant coffee",
      "—"],
     ["Colombia", "—", "well-known for ___5, not quantity",
      "small, family-run"]],
    [(1, "third", "about a ______ of world output",
      "produces roughly a third of the world total",
      "PARAFFRAZ: about = roughly; output = total."),
     (2, "plantations", "______ cover very large areas",
      "whose plantations cover vast areas of the south-east",
      "PARAFFRAZ: very large = vast — shu paraffraz kerakli "
      "jumlaga olib keladi, javob esa o'sha jumlaning egasi."),
     (3, "second", "Position", "Vietnam comes second",
      "O'rin so'ralgan."),
     (4, "robusta", "______ variety",
      "concentrate on the robusta variety",
      "Nav nomi to'g'ridan-to'g'ri berilgan."),
     (5, "quality", "well-known for ______",
      "Colombia is famous for the quality of its beans",
      "PARAFFRAZ: well-known = famous. Unit 1 juftligi.")],
))

# --------------------------------------------------------------- 14
PASSAGES.append(P(
    14, "SLEEP AND STUDENT PERFORMANCE",
    "Researchers followed 800 university students for one term. "
    "Students sleeping under six hours a night scored, on average, "
    "nine percent lower in examinations, and their concentration in "
    "lectures was noticeably poorer. Those sleeping seven to eight "
    "hours performed best and reported the greatest well-being. "
    "Interestingly, students who slept more than nine hours did not "
    "do any better; the researchers suggest that excessive sleep is "
    "often a sign of an underlying illness rather than a cause of "
    "weak results.",
    ["Hours of sleep", "Exam result", "Other findings"],
    [["Under six", "___1% lower", "worse ___2 in lectures"],
     ["Seven to eight", "___3", "highest ___4"],
     ["Over nine", "no improvement", "may indicate an ___5"]],
    [(1, "nine", "______% lower", "scored, on average, nine percent "
      "lower", "Chalg'ituvchi: 800 — talabalar soni; «six», "
      "«seven», «nine» — soatlar. Faqat FOIZ kerak."),
     (2, "concentration", "worse ______ in lectures",
      "their concentration in lectures was noticeably poorer",
      "PARAFFRAZ: worse = poorer."),
     (3, "best", "Exam result", "Those sleeping seven to eight hours "
      "performed best", "Eng yaxshi natija."),
     (4, "well-being", "highest ______",
      "reported the greatest well-being",
      "PARAFFRAZ: highest = greatest."),
     (5, "illness", "may indicate an ______",
      "often a sign of an underlying illness",
      "PARAFFRAZ: indicate = be a sign of.")],
))

# --------------------------------------------------------------- 15
PASSAGES.append(P(
    15, "PLASTIC RECYCLING IN THREE COUNTRIES",
    "Germany recycles about 56 percent of its plastic packaging, the "
    "highest figure in Europe, largely thanks to a deposit scheme "
    "introduced in 2003. Consumers pay a small sum on each bottle and "
    "get it back on return. In Spain the rate is close to 37 percent; "
    "campaigners argue that the collection points are too scattered. "
    "Turkey has expanded quickly from a very low base, but much of "
    "the material is exported for processing rather than treated at "
    "home.",
    ["Country", "Rate", "Reason / obstacle"],
    [["Germany", "___1%", "deposit scheme started in ___2"],
     ["Spain", "about ___3%", "collection points are too ___4"],
     ["Turkey", "rising fast", "waste is ___5 for processing"]],
    [(1, "56", "Rate", "recycles about 56 percent",
      "Har qatorga O'Z foizini qo'ying."),
     (2, "2003", "started in ______",
      "a deposit scheme introduced in 2003",
      "PARAFFRAZ: started = introduced."),
     (3, "37", "about ______%", "the rate is close to 37 percent",
      "PARAFFRAZ: about = close to."),
     (4, "scattered", "too ______",
      "the collection points are too scattered",
      "Bo'shliqdan oldin «too» — SIFAT kerak."),
     (5, "exported", "waste is ______ for processing",
      "much of the material is exported for processing rather "
      "than treated at home",
      "«chetga yuboriladi» ma'nosidagi so'z — matnda «exported».")],
))

# --------------------------------------------------------------- 16
PASSAGES.append(P(
    16, "URBAN FARMING",
    "Rooftop farms have appeared in many cities over the past decade. "
    "In Singapore, where land is extremely scarce, such farms now "
    "supply about four percent of the country's vegetables. In "
    "Detroit, by contrast, the driving force has been the abundance "
    "of empty land left after factories closed; community gardens "
    "there are run by residents themselves. Critics point out that "
    "the yields remain modest and that the labour costs are far "
    "higher than on conventional farms.",
    ["Place", "Main driver", "Who runs them", "Share of supply"],
    [["Singapore", "very little ___1", "commercial companies",
      "about ___2%"],
     ["Detroit", "plenty of ___3 land", "the ___4 themselves", "—"]],
    [(1, "land", "very little ______", "where land is extremely "
      "scarce",
      "PARAFFRAZ: very little = extremely scarce."),
     (2, "four", "about ______%",
      "supply about four percent of the country's vegetables",
      "Foiz so'ralgan."),
     (3, "empty", "plenty of ______ land",
      "the abundance of empty land",
      "PARAFFRAZ: plenty of = abundance of."),
     (4, "residents", "the ______ themselves",
      "community gardens there are run by residents themselves",
      "PARAFFRAZ: residents = inhabitants. Unit 1 juftligi."),
     (5, "labour", "Critics say ______ costs are too high",
      "the labour costs are far higher",
      "PARAFFRAZ: too high = far higher.")],
))

# --------------------------------------------------------------- 17
PASSAGES.append(P(
    17, "THE DECLINE OF THE HONEYBEE",
    "Beekeepers in North America have reported losing close to a "
    "third of their colonies each winter since 2006. Three "
    "explanations dominate the debate. The varroa mite, a parasite "
    "that feeds on bees, is regarded by most specialists as the "
    "principal culprit. A second factor is the shortage of wild "
    "flowers: modern farming leaves bees short of the varied diet "
    "they need. Pesticides form the third strand; although evidence "
    "of direct killing is limited, several studies show that exposed "
    "bees lose their sense of direction and fail to return to the "
    "hive.",
    ["Cause", "Status", "Effect on bees"],
    [["Varroa mite", "seen as the main ___1", "feeds on bees"],
     ["Loss of wild flowers", "second factor",
      "bees have little ___2"],
     ["Pesticides", "___3 evidence of killing",
      "bees lose their sense of ___4 and cannot find the ___5"]],
    [(1, "culprit", "the main ______",
      "regarded by most specialists as the principal culprit",
      "PARAFFRAZ: main = principal."),
     (2, "diet", "have little ______",
      "modern farming leaves bees short of the varied diet they need",
      "PARAFFRAZ: have little = be short of. Unit 1 juftligi."),
     (3, "limited", "______ evidence",
      "evidence of direct killing is limited",
      "Dalil darajasi haqidagi so'z."),
     (4, "direction", "sense of ______",
      "exposed bees lose their sense of direction",
      "To'g'ridan-to'g'ri ibora."),
     (5, "hive", "cannot find the ______",
      "fail to return to the hive",
      "PARAFFRAZ: cannot = fail to.")],
))

# --------------------------------------------------------------- 18
PASSAGES.append(P(
    18, "NOISE POLLUTION IN EUROPEAN CITIES",
    "More than one hundred million Europeans are exposed to traffic "
    "noise above the level the World Health Organization considers "
    "safe. The consequences are not merely irritating. Long-term "
    "exposure raises blood pressure and is associated with an "
    "estimated 12,000 premature deaths a year across the continent. "
    "Children living near busy roads show delayed reading "
    "development. Some cities have responded: Paris has reduced "
    "speed limits to 30 kilometres an hour on most streets, while "
    "Zurich has invested in quieter road surfaces, which cut noise by "
    "roughly three decibels.",
    ["Aspect", "Detail"],
    [["People affected", "over ___1 million"],
     ["Health effect", "higher ___2 pressure"],
     ["Deaths per year", "about ___3"],
     ["Effect on children", "slower ___4 development"],
     ["Zurich's solution", "quieter road ___5"]],
    [(1, "one hundred", "over ______ million",
      "More than one hundred million Europeans",
      "PARAFFRAZ: over = more than."),
     (2, "blood", "higher ______ pressure",
      "raises blood pressure",
      "PARAFFRAZ: higher = raises."),
     (3, "12,000", "Deaths per year",
      "an estimated 12,000 premature deaths a year",
      "PARAFFRAZ: about = estimated; per year = a year. "
      "Chalg'ituvchi: 30 va 3 — boshqa narsalar."),
     (4, "reading", "slower ______ development",
      "show delayed reading development",
      "PARAFFRAZ: slower = delayed."),
     (5, "surfaces", "quieter road ______",
      "invested in quieter road surfaces",
      "Ibora aynan matndan olinadi.")],
))

# --------------------------------------------------------------- 19
PASSAGES.append(P(
    19, "THE FOUR-DAY WEEK",
    "Between 2022 and 2023, sixty-one British companies took part in "
    "the largest trial of a shorter week yet attempted. Staff worked "
    "four days for the same salary. Revenue at the participating "
    "firms was broadly unchanged, rising by 1.4 percent on average, "
    "while the number of employees resigning fell by 57 percent. "
    "Fifteen percent of workers said no amount of money would "
    "persuade them to return to five days. Critics note, however, "
    "that the trial relied on firms that volunteered, and that "
    "manufacturing was barely represented — a sector where output is "
    "tied directly to hours worked.",
    ["Measure", "Result", "Note"],
    [["Companies involved", "___1", "all took part voluntarily"],
     ["Pay", "___2", "—"],
     ["Revenue", "up ___3%", "essentially flat"],
     ["Staff leaving", "down ___4%", "—"],
     ["Weak point of study", "few firms from ___5",
      "output depends on hours"]],
    [(1, "sixty-one", "Companies involved",
      "sixty-one British companies took part",
      "Chalg'ituvchi sonlar ko'p: 2022, 2023, 1.4, 57, 15. "
      "Faqat KOMPANIYALAR soni kerak."),
     (2, "unchanged", "Pay", "Staff worked four days for the same "
      "salary",
      "PARAFFRAZ: unchanged = the same. «Pay» = «salary»."),
     (3, "1.4", "up ______%", "rising by 1.4 percent on average",
      "PARAFFRAZ: up = rising by."),
     (4, "57", "down ______%",
      "the number of employees resigning fell by 57 percent",
      "PARAFFRAZ: down = fell by; staff leaving = employees "
      "resigning."),
     (5, "manufacturing", "few firms from ______",
      "manufacturing was barely represented",
      "PARAFFRAZ: few = barely represented.")],
))

# --------------------------------------------------------------- 20
PASSAGES.append(P(
    20, "DEEP-SEA MINING",
    "The seabed of the Clarion-Clipperton Zone, an area of the "
    "Pacific roughly the size of Europe, is scattered with "
    "potato-sized nodules rich in cobalt and nickel — metals central "
    "to battery manufacture. Mining companies argue that extracting "
    "them would be less damaging than opening new mines on land, "
    "where forests are cleared and communities displaced. Marine "
    "biologists are unconvinced. The nodules take millions of years "
    "to form, so any habitat destroyed is effectively lost for ever, "
    "and the sediment plumes stirred up by collectors may travel "
    "hundreds of kilometres, smothering filter-feeding animals far "
    "from the mining site itself. A moratorium is supported by "
    "twenty-four states, though the industry insists that a ban "
    "would leave the world short of the materials it needs.",
    ["Point", "Argument for mining", "Argument against"],
    [["Compared with land mines", "causes ___1 damage",
      "habitat is ___2 for ever"],
     ["Speed of recovery", "—", "nodules need ___3 of years"],
     ["Sediment", "—", "plumes may travel ___4 of kilometres"],
     ["Ban", "world would have little ___5",
      "supported by 24 states"]],
    [(1, "less", "causes ______ damage",
      "would be less damaging than opening new mines on land",
      "Taqqoslash: kon qazishga QARSHI emas, TARAFDOR dalil."),
     (2, "lost", "habitat is ______ for ever",
      "any habitat destroyed is effectively lost for ever",
      "PARAFFRAZ: destroyed = lost."),
     (3, "millions", "need ______ of years",
      "The nodules take millions of years to form",
      "PARAFFRAZ: need = take."),
     (4, "hundreds", "may travel ______ of kilometres",
      "may travel hundreds of kilometres",
      "Chalg'ituvchi: «twenty-four» — davlatlar soni."),
     (5, "materials", "have little ______",
      "would leave the world short of the materials it needs",
      "PARAFFRAZ: have little = be short of. Unit 1 juftligi — "
      "eng qiyin matnda ham xuddi o'sha qoida ishlaydi.")],
))


# =====================================================================
#  YIG'ISH
# =====================================================================
# Raqam so'z bilan yozilgan javoblarda raqamli shakl ham qabul
# qilinadi — mashqda maqsad PARAFFRAZNI topish, imlo emas.
NUM_ALT = {
    "four": "4", "six": "6", "eight": "8", "nine": "9", "ten": "10",
    "twelve": "12", "thirty": "30", "sixty-one": "61",
    "twenty-five": "25", "one hundred": "100", "third": "3rd",
    "millions": "million",
    "hundreds": "hundred",
}


def _prompt_for(rows, n, table_phrase):
    """Bo'shliq jadval katagida bo'lsa — o'sha katak matni, bo'lmasa
    (jadvaldan tashqari savol) — berilgan ibora."""
    mark = f"___{n}"
    for r in rows:
        for cell in r:
            if mark in str(cell):
                return str(cell).replace(mark, GAP), True
    return str(table_phrase).replace("______", GAP), False


def build_rows():
    out = []
    for p in PASSAGES:
        for i, (n, ans, tbl, psg, note) in enumerate(p["gaps"]):
            prompt, in_table = _prompt_for(p["rows"], n, tbl)
            payload = {
                "title": p["title"],
                "passage": p["text"],
                "headers": p["headers"],
                # Jadvalda FAQAT shu bo'shliq ochiq turadi, qolganlari
                # "…" bilan yopiladi — javob boshqa katakdan
                # ko'chirib olinmasin.
                "rows": [[_mask(c, n) for c in r] for r in p["rows"]],
                "gap_no": n,
                "in_table": in_table,
                "prompt": prompt,
                "step": p["level"],
                "order": i,
                "step_title": f"{p['level']}-daraja",
                "tip": "Paraffrazni toping",
                "instruction": "Choose ONE WORD from the passage.",
            }
            explain = (f"Jadvalda: «{tbl}»  ->  Matnda: «{psg}». {note}")
            alt = NUM_ALT.get(ans.lower(), "")
            out.append((KIND, _cefr(p["level"]), payload, ans,
                        explain, alt, {"table": tbl, "passage": psg}))
    return out


def _mask(cell, keep):
    """Boshqa bo'shliqlarni yopadi, kerakligini ochiq qoldiradi."""
    s = str(cell)
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


def seed_reading_table(db):
    """Idempotent: (kind, passage, prompt, gap_no) bo'yicha."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_read_table_v1"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            pl = json.loads(p)
            have.add((k, pl.get("passage"), pl.get("prompt"),
                      pl.get("gap_no")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain, alt, para in build_rows():
        key = (kind, payload["passage"], payload["prompt"],
               payload["gap_no"])
        if key in have:
            continue
        payload = dict(payload)
        payload["paraphrase"] = para   # javobdan KEYIN ko'rsatiladi
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt or None, explain=explain))
        have.add(key)
        made += 1
    if made:
        db.commit()
    _seed_mark(db, "ielts_read_table_v1")
    return made
