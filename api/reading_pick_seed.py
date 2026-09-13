# -*- coding: utf-8 -*-
"""IELTS READING — PICK FROM A LIST (2026-08-26).

Jahongir: "bu picking from the list savol turi, bunda bitta savolga
2ta togri javobni 5ta variant ichidan tanlash kerak bo'ladi. buni
ham osondan qiyinga qil."

TUZILISHI. 22 ta matn, jami 100 savol, daraja 1..22:
  1-8    — 4 savoldan; ikkala javob matnning BITTA jumlasida;
  9-16   — 5 savoldan; javoblar turli xatboshilarda;
  17-22  — eng qiyini. Ichida Jahongirning ikki namunasi:
           18 — "READING #22. On the trail of the honey badger",
           20 — "READING #21. Humpback whale breaks migration
                record" (7 savol, kitobdagi javoblari bilan).

BU TURNING O'ZIGA XOSLIGI. Beshta variantdan IKKITASI to'g'ri, ya'ni
ikkalasini ham topmasa savol hisobga olinmaydi. Uchta noto'g'ri
variant ataylab uch xil qilib tuzilgan:
  1) matnda BOR, lekin boshqa savolga tegishli;
  2) matnda aytilganning TESKARISI;
  3) mantiqan to'g'ri, lekin matnda UMUMAN yo'q.
Uchinchisi eng xavflisi — u o'quvchining dunyo haqidagi bilimiga mos
tushadi va shuning uchun ishonarli ko'rinadi.

JAVOB FORMATI. answer = ikkita variant matni SEP bilan ulangan, harf
tartibida. Server to'plam sifatida solishtiradi — o'quvchi qaysi
birini oldin bosgani ahamiyatsiz.
"""

SKILL = "ielts_reading"
KIND = "read_pick"
LET = ["A", "B", "C", "D", "E"]
SEP = " ||| "


PICK_TIPS = [
    ("Pick from a list nima",
     "Bitta savol, beshta variant (A-E) va ikkitasi to'g'ri. "
     "IKKALASINI ham topish shart: bittasi to'g'ri bo'lsa ham ball "
     "berilmaydi. Shuning uchun birinchi javobni topgach TO'XTAMANG.",
     "What TWO aspects of the whale's journey surprised researchers?\n"
     "A the destination   B the direction   C the distance\n"
     "D the reason        E the season\nJavob: B va C"),
    ("Ikki javob bir joyda bo'lmasligi mumkin",
     "Oson savollarda ikkala javob bitta jumlada turadi. Qiyinlarida "
     "biri matnning boshida, ikkinchisi oxirida bo'ladi. Matnning "
     "faqat bitta joyini o'qib javob bermang.", ""),
    ("Uchta noto'g'ri variant qanday tuziladi",
     "(1) matnda BOR, lekin boshqa savol haqida; (2) matndagi "
     "gapning TESKARISI; (3) mantiqan to'g'ri, lekin matnda "
     "aytilmagan. Uchinchisi eng xavfli — u sizning bilimingizga "
     "to'g'ri keladi, matnga emas.",
     "Which TWO places may the whale have passed?\n"
     "A Antarctica  B Hawaii  C Maine  D New Zealand  E South Africa\n"
     "Hawaii, Maine va New Zealand matnda BOR — lekin ular "
     "olimlarning ish joyi, kitning yo'li emas."),
    ("Savoldagi aniqlovchi so'zga qarang",
     "«near Brazil», «male badgers», «generally migrate», «Kitso "
     "Khama says» — bu so'zlar matnning qaysi qismi kerakligini "
     "aytadi. Ularni sezmasangiz, to'g'ri jumlani topib ham noto'g'ri "
     "javob berasiz.", ""),
    ("Variantlar doim parafraz",
     "Matndagi so'z variantda takrorlanmaydi.",
     "Matn: «photographed its tail fluke and took skin samples»\n"
     "A They took a picture.\n"
     "B They analysed part of the whale's body."),
    ("Ikki variant bir narsani aytsa",
     "Ikkalasi ham to'g'ri bo'la olmaydi — imtihon bir javobni ikki "
     "marta bermaydi. Farqini toping: biri albatta matnga yaqinroq "
     "yoki aniqroq.", ""),
    ("Tartib yo'q",
     "Javoblarni A dan E gacha tartibda yozing, lekin matnda ular "
     "istalgan tartibda uchraydi. A varianti birinchi javob degani "
     "emas.", ""),
    ("Vaqtni to'g'ri sarflang",
     "Bu savol ikki ball beradi, lekin ikki barobar vaqt olmaydi. "
     "Ikkinchi javobni topolmasangiz — belgilab qo'ying, "
     "keyingisiga o'ting va oxirida qayting.", ""),
]


def P(level, title, text, qs):
    return {"level": level, "title": title, "text": text, "qs": qs}


PASSAGES = []

# ================= 1-8: 4 savol, javoblar yaqin ==================
PASSAGES.append(P(
    1, "THE SCHOOL TRIP TO THE FARM",
    "Class 6 visited Oq Tepa farm on Friday. They fed the goats and "
    "collected eggs from the hen house. The farmer showed them how "
    "butter is made, and the children each took a small pot home. "
    "Lunch was bread and soup in the barn. It rained in the "
    "afternoon, so the walk to the river was cancelled and the "
    "children watched a film about bees instead.",
    [("What TWO activities did the children do with animals?",
      ["They fed the goats.", "They rode a horse.",
       "They collected eggs.", "They milked a cow.",
       "They cleaned the barn."], [0, 2],
      "They fed the goats and collected eggs from the hen house",
      "B, D, E fermada bo'lishi mumkin, lekin matnda yo'q."),
     ("What TWO things did the children take or eat?",
      ["Cheese.", "Butter.", "Bread and soup.", "Fruit.", "Honey."],
      [1, 2],
      "each took a small pot home. Lunch was bread and soup",
      "E — QOPQON: asalarilar haqida film bor, asal emas."),
     ("What TWO things happened in the afternoon?",
      ["The walk was cancelled.", "They fed the goats again.",
       "They watched a film.", "They went home early.",
       "They met the farmer."], [0, 2],
      "the walk to the river was cancelled and the children watched "
      "a film about bees instead", "Sababi — yomg'ir."),
     ("What TWO places on the farm are mentioned?",
      ["The hen house.", "The kitchen.", "The barn.", "The office.",
       "The garden."], [0, 2],
      "collected eggs from the hen house ... Lunch was bread and "
      "soup in the barn",
      "Qolgan uch joy matnda aytilmagan.")],
))

PASSAGES.append(P(
    2, "THE NEW BUS ROUTE",
    "Bus 14 began running in April. It connects the railway station "
    "with the hospital and the university, and runs every twenty "
    "minutes. Tickets cost 2,000 so'm, but students and pensioners "
    "travel at half price. The buses are new and have space for "
    "wheelchairs. Passengers have complained that there is no "
    "shelter at three of the stops.",
    [("What TWO places does the bus connect the station with?",
      ["The airport.", "The hospital.", "The market.",
       "The university.", "The stadium."], [1, 3],
      "connects the railway station with the hospital and the "
      "university", "A, C, E aytilmagan."),
     ("What TWO groups pay less?",
      ["Children.", "Students.", "Soldiers.", "Pensioners.",
       "Hospital staff."], [1, 3],
      "students and pensioners travel at half price",
      "A va E mantiqan mumkin, lekin matnda yo'q."),
     ("What TWO good things are said about the buses?",
      ["They are new.", "They are cheap for everyone.",
       "They take wheelchairs.", "They run all night.",
       "They are never full."], [0, 2],
      "The buses are new and have space for wheelchairs",
      "B — QOPQON: hammaga emas, faqat ikki guruhga arzon."),
     ("What TWO facts are given about the timetable?",
      ["It started in April.", "It runs every twenty minutes.",
       "It stops at midnight.", "It changes at weekends.",
       "It has fourteen stops."], [0, 1],
      "began running in April ... runs every twenty minutes",
      "E — QOPQON: 14 avtobus RAQAMI, bekat soni emas.")],
))

PASSAGES.append(P(
    3, "A YOUNG CHESS PLAYER",
    "Kamola learnt chess from her grandfather when she was six. She "
    "won her first regional tournament at nine and joined the "
    "national junior squad two years later. She trains for two hours "
    "every evening and studies old games at weekends. Her coach says "
    "her strongest points are patience and an unusually good memory "
    "for positions. She hopes to become a grandmaster and to study "
    "mathematics at university.",
    [("What TWO things does Kamola do to train?",
      ["She plays online every day.",
       "She practises for two hours each evening.",
       "She studies old games at weekends.",
       "She teaches younger children.",
       "She travels to a tournament every month."], [1, 2],
      "She trains for two hours every evening and studies old games "
      "at weekends", "A, D, E aytilmagan."),
     ("What TWO qualities does her coach mention?",
      ["Speed.", "Patience.", "Courage.", "Memory.",
       "Concentration."], [1, 3],
      "her strongest points are patience and an unusually good "
      "memory for positions",
      "E — QOPQON: diqqat mantiqan mos, lekin matnda yo'q."),
     ("What TWO ambitions does she have?",
      ["To become a coach.", "To become a grandmaster.",
       "To play abroad.", "To study mathematics.",
       "To write a book."], [1, 3],
      "She hopes to become a grandmaster and to study mathematics",
      "Ikkalasi bitta jumlada."),
     ("What TWO facts about her early years are given?",
      ["She learnt from her grandfather.", "She learnt at school.",
       "She won a regional event at nine.",
       "She lost her first game.", "She had a famous teacher."],
      [0, 2],
      "learnt chess from her grandfather when she was six. She won "
      "her first regional tournament at nine", "B — matnga zid.")],
))

PASSAGES.append(P(
    4, "THE COMMUNITY POOL",
    "The pool was built in 1974 and closed in 2019 when the roof "
    "began to leak. A local charity raised 900 million so'm and "
    "reopened it last year. The water is now heated by solar panels, "
    "which cut running costs by about a third. Morning sessions are "
    "reserved for older swimmers and for school classes. The charity "
    "says the main remaining problem is a shortage of qualified "
    "instructors.",
    [("What TWO facts explain why the pool closed?",
      ["It was too old.", "The roof leaked.", "It lost money.",
       "It closed in 2019.", "Nobody used it."], [1, 3],
      "closed in 2019 when the roof began to leak",
      "A va C mumkin, lekin matn sabab sifatida aytmaydi."),
     ("What TWO things did the charity do?",
      ["It raised money.", "It bought the land.",
       "It reopened the pool.", "It trained instructors.",
       "It built a new roof."], [0, 2],
      "A local charity raised 900 million so'm and reopened it",
      "D — QOPQON: instruktor MUAMMO, qilingan ish emas."),
     ("What TWO groups use the morning sessions?",
      ["Older swimmers.", "Competitive teams.", "School classes.",
       "Families.", "Charity staff."], [0, 2],
      "Morning sessions are reserved for older swimmers and for "
      "school classes", "Bitta jumlada."),
     ("What TWO things are said about the solar panels?",
      ["They heat the water.", "They were donated.",
       "They cut costs by about a third.", "They power the lights.",
       "They were installed in 1974."], [0, 2],
      "heated by solar panels, which cut running costs by about a "
      "third", "E — QOPQON: 1974 basseyn qurilgan yil.")],
))

PASSAGES.append(P(
    5, "WORKING AS A VET",
    "Most people imagine a vet spending the day with cats and dogs, "
    "but half of Dilshod's work is with farm animals, and much of "
    "that is done at night. The job is physically demanding: he has "
    "been kicked twice and broke a finger last winter. The part he "
    "finds hardest is not the injuries but explaining to owners that "
    "an animal cannot be saved. He says the training rarely prepares "
    "young vets for that conversation.",
    [("What TWO things surprise people about the job?",
      ["Half the work is with farm animals.", "It is well paid.",
       "Much of it happens at night.",
       "It requires little training.", "Vets work alone."], [0, 2],
      "half of Dilshod's work is with farm animals, and much of that "
      "is done at night", "«but» kutilmagan tomonni bildiradi."),
     ("What TWO injuries are mentioned?",
      ["A broken finger.", "A bite.", "Being kicked.",
       "A back problem.", "An allergy."], [0, 2],
      "he has been kicked twice and broke a finger last winter",
      "B hayvon bilan ishlashda mumkin, lekin matnda yo'q."),
     ("What TWO things does Dilshod say about the hardest part?",
      ["It is the physical danger.",
       "It is telling owners bad news.",
       "Training does not prepare vets for it.",
       "It gets easier with time.", "It happens every day."],
      [1, 2],
      "The part he finds hardest is not the injuries but explaining "
      "to owners that an animal cannot be saved. He says the "
      "training rarely prepares young vets",
      "A — matn aynan rad etadi: «not the injuries»."),
     ("What TWO kinds of animal are mentioned?",
      ["Cats and dogs.", "Horses.", "Farm animals.", "Birds.",
       "Wild animals."], [0, 2],
      "spending the day with cats and dogs, but half of Dilshod's "
      "work is with farm animals", "B, D, E aytilmagan.")],
))

PASSAGES.append(P(
    6, "THE PAPER MILL",
    "The mill opened in 1958 and at its peak employed 1,200 people. "
    "Today it employs 310, although it produces more paper than ever "
    "because most of the work is done by machine. Almost all its raw "
    "material is now recycled waste rather than fresh timber. The "
    "main difficulties it faces are the price of electricity and a "
    "shortage of trained engineers, since the nearest technical "
    "college closed in 2011.",
    [("What TWO changes have taken place at the mill?",
      ["It has fewer workers.", "It produces less.",
       "It produces more.", "It has a new owner.",
       "It has a larger site."], [0, 2],
      "Today it employs 310, although it produces more paper than "
      "ever", "B — matnga zid."),
     ("What TWO reasons explain the changes?",
      ["Machines do most of the work.", "Demand has fallen.",
       "Raw material is now recycled waste.",
       "The site was rebuilt.", "Wages went up."], [0, 2],
      "most of the work is done by machine. Almost all its raw "
      "material is now recycled waste", "Ikki alohida jumla."),
     ("What TWO difficulties does the mill face?",
      ["The cost of electricity.", "Transport problems.",
       "A shortage of engineers.", "Old machinery.",
       "Falling paper prices."], [0, 2],
      "the price of electricity and a shortage of trained engineers",
      "D — QOPQON: mashina ko'p ishlaydi, eski deyilmagan."),
     ("What TWO dates are given in the passage?",
      ["1958.", "1948.", "2011.", "2019.", "1,200."], [0, 2],
      "The mill opened in 1958 ... the nearest technical college "
      "closed in 2011", "E — bu son, sana emas.")],
))

PASSAGES.append(P(
    7, "URBAN PIGEONS",
    "City pigeons are descended from rock doves, birds that nest on "
    "cliffs, which is why window ledges and bridges suit them so "
    "well. They can breed in any month if food is plentiful, and a "
    "pair may raise five broods in a year. Feeding them is banned in "
    "several cities, not because the birds spread disease - the risk "
    "is very low - but because the food attracts rats. Efforts to "
    "reduce numbers by removing eggs have generally failed, since "
    "the birds simply lay again.",
    [("What TWO features of city buildings suit pigeons?",
      ["Window ledges.", "Flat roofs.", "Bridges.",
       "Warm chimneys.", "Tall towers."], [0, 2],
      "which is why window ledges and bridges suit them so well",
      "B, D, E mantiqan mumkin, matnda yo'q."),
     ("What TWO facts about pigeon breeding are given?",
      ["They breed only in spring.", "They can breed in any month.",
       "A pair may raise five broods a year.",
       "They lay one egg at a time.", "They nest in trees."],
      [1, 2],
      "They can breed in any month if food is plentiful, and a pair "
      "may raise five broods in a year", "A — teskarisi."),
     ("What TWO things are said about feeding bans?",
      ["They exist in several cities.",
       "They are because of disease.",
       "They are because food attracts rats.",
       "They are rarely enforced.", "They apply only in parks."],
      [0, 2],
      "Feeding them is banned in several cities, not because the "
      "birds spread disease ... but because the food attracts rats",
      "B — matn aynan rad etadi."),
     ("What TWO things are true about removing eggs?",
      ["It is cheap.", "It has generally failed.",
       "The birds lay again.", "It is illegal.",
       "It works in winter."], [1, 2],
      "Efforts to reduce numbers by removing eggs have generally "
      "failed, since the birds simply lay again",
      "Sabab va oqibat bitta jumlada.")],
))

PASSAGES.append(P(
    8, "THE NIGHT MARKET",
    "The market opens at seven in the evening and closes at two in "
    "the morning. Around 200 stalls sell food, and a smaller number "
    "sell clothes and phone accessories. Traders pay a nightly fee "
    "rather than rent, which is why many are students or people with "
    "daytime jobs. The city council has twice proposed moving the "
    "market to a car park outside the centre; on both occasions "
    "traders and local residents objected together.",
    [("What TWO things are sold besides food?",
      ["Clothes.", "Books.", "Phone accessories.", "Furniture.",
       "Flowers."], [0, 2],
      "a smaller number sell clothes and phone accessories",
      "B, D, E aytilmagan."),
     ("What TWO kinds of people work as traders?",
      ["Students.", "Retired people.", "People with daytime jobs.",
       "Tourists.", "Council employees."], [0, 2],
      "many are students or people with daytime jobs",
      "Sababi — kunlik to'lov, ijara emas."),
     ("What TWO facts about the council's proposal are given?",
      ["It was made twice.", "It was accepted.",
       "It involved moving to a car park.", "It came from traders.",
       "It was made last year."], [0, 2],
      "The city council has twice proposed moving the market to a "
      "car park", "B va D — matnga zid."),
     ("What TWO groups opposed the move?",
      ["Traders.", "The police.", "Local residents.",
       "Shop owners.", "Students only."], [0, 2],
      "traders and local residents objected together",
      "E — QOPQON: talabalar sotuvchilar ichida, alohida guruh emas.")],
))

# ========== 9-16: 5 savol, javoblar turli xatboshilarda ==========
PASSAGES.append(P(
    9, "THE RETURN OF THE BEAVER",
    "Beavers disappeared from Britain about four hundred years ago, "
    "hunted for their fur and for a substance in their glands that "
    "was used in medicine. In 2009 a small group was released in "
    "Scotland, and further populations have been established since. "
    "The results have surprised even the scientists involved. The "
    "dams the animals build slow rivers down, which reduces flooding "
    "further downstream, and the pools behind them trap sediment and "
    "so improve water quality. Wetland birds and insects have "
    "returned to sites that had been dry for decades.\n\n"
    "Not everyone is pleased. Farmers whose fields lie beside slow "
    "rivers have lost crops to flooding, and some have had mature "
    "trees felled overnight. A compensation scheme now operates in "
    "several regions, and licensed trapping and relocation is "
    "permitted where damage is severe. Conservationists argue that "
    "these costs are small beside the money that would otherwise be "
    "spent on flood defences downstream.",
    [("What TWO reasons are given for the beaver's disappearance?",
      ["Loss of woodland.", "Hunting for fur.", "Disease.",
       "A substance used in medicine.", "River pollution."],
      [1, 3],
      "hunted for their fur and for a substance in their glands that "
      "was used in medicine", "A, C, E mantiqan mumkin, matnda yo'q."),
     ("What TWO benefits of beaver dams are mentioned?",
      ["They create electricity.",
       "They reduce flooding downstream.",
       "They improve water quality.", "They provide timber.",
       "They attract tourists."], [1, 2],
      "slow rivers down, which reduces flooding further downstream, "
      "and the pools behind them trap sediment and so improve water "
      "quality", ""),
     ("What TWO kinds of wildlife have returned?",
      ["Fish.", "Wetland birds.", "Deer.", "Insects.", "Otters."],
      [1, 3],
      "Wetland birds and insects have returned to sites that had "
      "been dry for decades", "A, C, E aytilmagan."),
     ("What TWO complaints do farmers make?",
      ["Their crops are flooded.", "Their fences are damaged.",
       "Their trees are felled.", "Their water is polluted.",
       "Their land has lost value."], [0, 2],
      "have lost crops to flooding, and some have had mature trees "
      "felled overnight", "D — matn suv sifati YAXSHILANADI deydi."),
     ("What TWO responses to the damage are described?",
      ["Beavers are being removed entirely.",
       "Farmers are paid compensation.",
       "Flood defences have been built.",
       "Animals may be trapped and moved.",
       "Farmers have been given new land."], [1, 3],
      "A compensation scheme now operates ... licensed trapping and "
      "relocation is permitted where damage is severe",
      "A — faqat «where damage is severe», hamma joyda emas.")],
))

PASSAGES.append(P(
    10, "THE FOUR-DAY WEEK",
    "In 2022 sixty-one British companies moved their staff to a "
    "four-day week for six months, with no reduction in pay. The "
    "trial was among the largest ever run. At the end of it, "
    "fifty-six of the companies chose to continue, and eighteen made "
    "the change permanent immediately.\n\n"
    "The most consistent finding was not productivity but health: "
    "reported burnout fell sharply, and the number of sick days "
    "taken dropped by around two-thirds. Revenue across the "
    "participating firms was roughly unchanged, rising slightly "
    "overall, though this varied a great deal from company to "
    "company. Staff turnover fell, which several managers described "
    "as the single largest financial benefit, since replacing a "
    "skilled employee is expensive.\n\n"
    "The change was easiest in software and marketing firms, where "
    "output is measured in completed projects. It was hardest in "
    "hospitality and care work, where someone must physically be "
    "present. Researchers also noted that meetings became shorter "
    "and fewer almost everywhere, and several managers admitted this "
    "alone recovered much of the lost day.",
    [("What TWO facts about the trial itself are given?",
      ["It lasted six months.", "It lasted a year.",
       "Pay was not reduced.", "Pay was reduced slightly.",
       "It was run by the government."], [0, 2],
      "for six months, with no reduction in pay", "B va D — matnga zid."),
     ("What TWO health effects were reported?",
      ["Less burnout.", "Better sleep.", "Fewer sick days.",
       "More exercise.", "Lower stress in managers."], [0, 2],
      "reported burnout fell sharply, and the number of sick days "
      "taken dropped by around two-thirds",
      "B, D, E mantiqan mos, lekin matnda yo'q."),
     ("What TWO things are said about money?",
      ["Revenue fell sharply.", "Revenue was roughly unchanged.",
       "Results varied between companies.",
       "Costs rose in every firm.", "Wages were cut."], [1, 2],
      "Revenue ... was roughly unchanged, rising slightly overall, "
      "though this varied a great deal from company to company", ""),
     ("What TWO reasons made the change easier in some firms?",
      ["Output is measured in projects.", "Staff are younger.",
       "Meetings became shorter and fewer.",
       "The firms were smaller.", "Customers were flexible."],
      [0, 2],
      "where output is measured in completed projects ... meetings "
      "became shorter and fewer almost everywhere", ""),
     ("What TWO benefits did managers themselves highlight?",
      ["Lower staff turnover.", "Higher revenue.",
       "Better customer reviews.", "Shorter meetings.",
       "Lower rent."], [0, 3],
      "Staff turnover fell, which several managers described as the "
      "single largest financial benefit ... several managers "
      "admitted this alone recovered much of the lost day",
      "B — daromad deyarli o'zgarmagan.")],
))

PASSAGES.append(P(
    11, "SLEEP AND THE TEENAGE BRAIN",
    "Around the age of thirteen the body clock shifts. The hormone "
    "melatonin, which brings on sleepiness, begins to be released "
    "roughly two hours later than in childhood, and it also clears "
    "from the body later in the morning. A teenager who cannot fall "
    "asleep before midnight is not being difficult; the biology has "
    "changed. Screens make this worse, but they are not the cause, "
    "and the same shift is found in communities with no electricity "
    "at all.\n\n"
    "The consequence is that early school start times take their "
    "hours from the end of the night, which is when most dreaming "
    "sleep occurs. That stage appears to be particularly important "
    "for emotional regulation and for fixing new memories.\n\n"
    "Several American districts have moved the school day later. "
    "Attendance improved, and in one large study the rate of car "
    "crashes among teenage drivers fell noticeably. Grades rose, "
    "though by less than campaigners had predicted. The main "
    "objection has come not from teachers but from parents and "
    "sports coaches, because a later finish disrupts after-school "
    "training and family schedules.",
    [("What TWO changes to melatonin happen at about thirteen?",
      ["It is released later at night.", "Less is produced.",
       "It clears later in the morning.", "More is produced.",
       "It stops being produced."], [0, 2],
      "begins to be released roughly two hours later ... it also "
      "clears from the body later in the morning", ""),
     ("What TWO things does the passage say about screens?",
      ["They make the problem worse.", "They cause the shift.",
       "They are not the cause.", "They delay melatonin by hours.",
       "They have no effect."], [0, 2],
      "Screens make this worse, but they are not the cause",
      "E — matn «make this worse» deydi, ya'ni ta'siri bor."),
     ("What TWO functions of late-night sleep are mentioned?",
      ["Physical growth.", "Emotional regulation.",
       "Fighting infection.", "Fixing new memories.",
       "Muscle repair."], [1, 3],
      "particularly important for emotional regulation and for "
      "fixing new memories",
      "A, C, E uyquning boshqa foydalari, bu matnda aytilmagan."),
     ("What TWO improvements followed a later start?",
      ["Better attendance.", "Fewer teenage car crashes.",
       "Lower costs.", "Less screen use.", "Happier teachers."],
      [0, 1],
      "Attendance improved, and ... the rate of car crashes among "
      "teenage drivers fell noticeably", ""),
     ("What TWO groups objected to the later start?",
      ["Teachers.", "Parents.", "Doctors.", "Sports coaches.",
       "Students."], [1, 3],
      "The main objection has come not from teachers but from "
      "parents and sports coaches", "A — matn aynan rad etadi.")],
))

PASSAGES.append(P(
    12, "SAVING THE SEED",
    "On a mountainside in the Arctic, a tunnel runs 120 metres into "
    "the rock. Inside it is the Svalbard Global Seed Vault, which "
    "holds duplicate samples of seeds kept in gene banks around the "
    "world. It is not a bank in the ordinary sense: depositors "
    "retain ownership, and only the country that made a deposit may "
    "withdraw it.\n\n"
    "The location was chosen for two practical reasons. The "
    "surrounding permafrost keeps the chambers cold even if the "
    "refrigeration fails, and the site sits well above any "
    "conceivable sea level. Norway pays the running costs, and "
    "deposits are free, which is why banks in poorer countries make "
    "up a large share of the collection.\n\n"
    "The vault has been opened for withdrawal only once. In 2015 "
    "researchers who had fled the war in Syria requested seeds to "
    "rebuild a collection they had left behind in Aleppo. They grew "
    "the seeds in Lebanon and Morocco and returned fresh samples to "
    "Svalbard within a few years. The episode is often described as "
    "the vault working exactly as intended, though it also revealed "
    "that the greatest threat to seed collections is not climate but "
    "conflict.",
    [("What TWO rules govern the vault?",
      ["Depositors keep ownership.", "Norway owns the seeds.",
       "Only the depositor may withdraw.", "Anyone may withdraw.",
       "Seeds must be replaced yearly."], [0, 2],
      "depositors retain ownership, and only the country that made a "
      "deposit may withdraw it", "B va D — matnga zid."),
     ("What TWO reasons explain the choice of location?",
      ["The permafrost keeps it cold.", "The land was cheap.",
       "It is high above sea level.", "It is easy to reach.",
       "It is politically neutral."], [0, 2],
      "The surrounding permafrost keeps the chambers cold ... the "
      "site sits well above any conceivable sea level",
      "D — Arktikaga borish oson emas."),
     ("What TWO facts about cost are given?",
      ["Norway pays the running costs.", "Depositors pay a fee.",
       "Deposits are free.", "The vault is funded by the UN.",
       "Withdrawals are charged."], [0, 2],
      "Norway pays the running costs, and deposits are free",
      "B va E — matnga zid."),
     ("What TWO things did the Syrian researchers do?",
      ["They requested seeds.", "They visited Svalbard.",
       "They grew the seeds elsewhere.", "They closed the vault.",
       "They paid for the samples."], [0, 2],
      "requested seeds ... They grew the seeds in Lebanon and "
      "Morocco", ""),
     ("What TWO conclusions are drawn from the 2015 episode?",
      ["The vault worked as intended.", "The vault is too small.",
       "Conflict is the greatest threat.",
       "Climate is the greatest threat.",
       "Withdrawals should be easier."], [0, 2],
      "often described as the vault working exactly as intended, "
      "though it also revealed that the greatest threat ... is not "
      "climate but conflict", "D — matn aynan rad etadi.")],
))

PASSAGES.append(P(
    13, "THE LANGUAGE OF BEES",
    "A returning honeybee that has found food performs a movement "
    "inside the hive which other bees can read. Karl von Frisch, who "
    "first decoded it in the 1940s, showed that the angle of the "
    "dance relative to vertical gives the direction of the food "
    "relative to the sun, and that the length of the central run "
    "encodes the distance. He received a Nobel Prize for the work.\n\n"
    "For years the discovery was doubted. Critics pointed out that "
    "the hive is dark and noisy and argued that the followers might "
    "simply be tracking the scent the dancer carried. The argument "
    "was settled in 2005, when a team fitted individual bees with "
    "tiny radar transponders and tracked their flights. Bees that "
    "had watched a dance flew directly to the indicated spot, even "
    "when the food itself had been removed.\n\n"
    "Two further findings came out of that work. Bees do not follow "
    "the instruction blindly: an experienced forager who knows a "
    "better site will ignore the dance. And distance is measured not "
    "in metres but in how much the landscape appears to move past "
    "the eye during the flight, which is why a bee flown through a "
    "narrow patterned tunnel reports a journey far longer than it "
    "really was.",
    [("What TWO things does the dance communicate?",
      ["The direction of the food.", "The type of flower.",
       "The distance to the food.", "The quality of the food.",
       "The time of day."], [0, 2],
      "the angle of the dance ... gives the direction ... the length "
      "of the central run encodes the distance",
      "B, D, E mantiqan foydali, lekin matnda yo'q."),
     ("What TWO objections did critics raise?",
      ["The hive is dark.", "Bees cannot see colour.",
       "Bees might follow scent instead.", "The dance is too short.",
       "Von Frisch used too few bees."], [0, 2],
      "the hive is dark and noisy and argued that the followers "
      "might simply be tracking the scent", ""),
     ("What TWO things did the 2005 study do?",
      ["It fitted bees with transponders.",
       "It filmed the dance in infrared.", "It tracked flights.",
       "It removed the dancers.",
       "It repeated von Frisch's route."], [0, 2],
      "fitted individual bees with tiny radar transponders and "
      "tracked their flights", ""),
     ("What TWO later findings are described?",
      ["Bees may ignore the dance.", "Only young bees dance.",
       "Distance is judged visually.", "Bees dance at night.",
       "Bees count landmarks."], [0, 2],
      "an experienced forager who knows a better site will ignore "
      "the dance ... distance is measured ... in how much the "
      "landscape appears to move past the eye",
      "E — QOPQON: manzara harakati sanash bilan bir xil emas."),
     ("What TWO things are true of a bee flown through a patterned "
      "tunnel?",
      ["It reports a longer journey.", "It refuses to dance.",
       "Its report is inaccurate.", "It flies more slowly.",
       "It loses its way home."], [0, 2],
      "reports a journey far longer than it really was", "")],
))

PASSAGES.append(P(
    14, "THE COST OF FAST FASHION",
    "A garment made today is worn, on average, about half as many "
    "times as one made fifteen years ago, while the number of "
    "garments produced each year has roughly doubled. The two "
    "figures together explain most of the industry's growing "
    "environmental cost.\n\n"
    "Cotton is the usual target of criticism, and it is certainly "
    "thirsty: a single shirt may take 2,700 litres of water to "
    "produce. But synthetic fibres now make up around two-thirds of "
    "textiles, and their problem is different. Every wash releases "
    "microscopic plastic fibres, which pass through treatment plants "
    "and reach rivers and, eventually, the sea.\n\n"
    "Recycling is often presented as the answer. In practice less "
    "than one per cent of clothing is turned back into clothing, "
    "chiefly because most garments are blends, and separating cotton "
    "from polyester at scale remains unsolved. Much of what is "
    "collected for recycling is in fact exported; a proportion is "
    "resold and worn, but a large share is dumped.\n\n"
    "The measures that researchers consider genuinely effective are "
    "unglamorous. Wearing a garment twice as long roughly halves its "
    "footprint, and washing at lower temperatures cuts both energy "
    "use and fibre shedding.",
    [("What TWO trends explain the rising environmental cost?",
      ["Garments are worn fewer times.", "Clothes cost more.",
       "Production has roughly doubled.", "Cotton is scarcer.",
       "Shops have closed."], [0, 2],
      "worn, on average, about half as many times ... the number of "
      "garments produced each year has roughly doubled", ""),
     ("What TWO problems with synthetic fibres are described?",
      ["They use more water than cotton.",
       "They release plastic fibres when washed.",
       "They pass through treatment plants.",
       "They are hard to dye.", "They wear out quickly."], [1, 2],
      "Every wash releases microscopic plastic fibres, which pass "
      "through treatment plants",
      "A — QOPQON: suv muammosi paxtaga tegishli."),
     ("What TWO reasons are given for the failure of recycling?",
      ["Most garments are blends.",
       "Separating fibres is unsolved.", "It is too expensive.",
       "People do not donate clothes.",
       "There are too few plants."], [0, 1],
      "most garments are blends, and separating cotton from "
      "polyester at scale remains unsolved", ""),
     ("What TWO things happen to clothing collected for recycling?",
      ["It is turned back into clothing.", "It is exported.",
       "It is burned for energy.", "Some of it is dumped.",
       "It is stored for later use."], [1, 3],
      "Much of what is collected for recycling is in fact exported; "
      "... a large share is dumped",
      "A — bir foizdan kam, ya'ni asosiy taqdiri emas."),
     ("What TWO measures do researchers consider effective?",
      ["Buying organic cotton.", "Wearing garments longer.",
       "Washing at lower temperatures.", "Recycling more.",
       "Banning synthetics."], [1, 2],
      "Wearing a garment twice as long roughly halves its footprint, "
      "and washing at lower temperatures cuts both energy use and "
      "fibre shedding",
      "D — matn qayta ishlash ishlamayotganini ko'rsatadi.")],
))

PASSAGES.append(P(
    15, "THE MAN WHO MAPPED CHOLERA",
    "When cholera struck Soho in 1854, the accepted explanation was "
    "miasma - bad air rising from waste. John Snow, a London "
    "anaesthetist, did not believe it. He suspected water, and set "
    "out to prove it in a way that had not been tried before: he "
    "drew a map.\n\n"
    "On it he marked every death as a bar at the address where it "
    "occurred. The bars clustered tightly around a single public "
    "pump in Broad Street. Two apparent exceptions turned out to "
    "strengthen his case rather than weaken it. The workhouse, with "
    "hundreds of residents in the middle of the outbreak, had almost "
    "no deaths - and its own well. The nearby brewery had none at "
    "all; its workers drank beer.\n\n"
    "Snow persuaded the parish to remove the pump handle, and the "
    "outbreak subsided, though it was already declining as residents "
    "fled the district. His committee accepted the practical measure "
    "but rejected his theory, and the handle was later replaced. "
    "Snow died in 1858 without seeing his explanation adopted; the "
    "germ theory that vindicated him arrived a generation later.",
    [("What TWO things does the passage say about the miasma theory?",
      ["It blamed bad air from waste.", "Snow rejected it.",
       "It had been disproved by 1854.", "It was new in 1854.",
       "It was supported by the brewery."], [0, 1],
      "the accepted explanation was miasma - bad air rising from "
      "waste. John Snow ... did not believe it",
      "C — teskarisi: u hali qabul qilingan nazariya edi."),
     ("What TWO things did Snow do to test his idea?",
      ["He drew a map.", "He tested water samples.",
       "He marked each death at its address.",
       "He interviewed doctors.", "He closed the brewery."],
      [0, 2],
      "he drew a map. On it he marked every death as a bar at the "
      "address where it occurred",
      "B — QOPQON: u suvni GUMON qildi, lekin tahlil qilmadi."),
     ("What TWO places had unusually few deaths?",
      ["Broad Street.", "The workhouse.", "The parish office.",
       "The brewery.", "Snow's own street."], [1, 3],
      "The workhouse ... had almost no deaths ... The nearby brewery "
      "had none at all", ""),
     ("What TWO explanations are given for those exceptions?",
      ["The buildings were cleaner.",
       "The workhouse had its own well.",
       "The residents had left.", "Brewery workers drank beer.",
       "They were further from the pump."], [1, 3],
      "and its own well ... its workers drank beer",
      "E — QOPQON: pivo zavodi YAQIN edi («nearby»)."),
     ("What TWO things happened after the pump handle was removed?",
      ["The outbreak subsided.", "Snow's theory was accepted.",
       "The handle was later replaced.", "The pump was destroyed.",
       "Snow was given an award."], [0, 2],
      "the outbreak subsided ... the handle was later replaced",
      "B — qo'mita amaliy chorani qabul qildi, nazariyani emas.")],
))

PASSAGES.append(P(
    16, "WHY BUILDINGS FALL DOWN",
    "Structural engineers observe that buildings rarely collapse "
    "because a single member was too weak. Almost always the cause "
    "is a connection, a change made during construction, or an "
    "assumption that nobody checked.\n\n"
    "The Hyatt Regency walkway in Kansas City is the case every "
    "student learns. The original design hung two walkways from a "
    "single set of long rods. The fabricator, finding those rods "
    "impossible to thread over their full length, proposed hanging "
    "the lower walkway from the upper one instead. The change looked "
    "trivial on the drawing. In fact it doubled the load on the "
    "upper connection, which failed in 1981 and killed 114 people.\n\n"
    "Two lessons are usually drawn. The first is that load paths "
    "must be traced by hand after any change, however small it "
    "appears. The second is about communication: the revision was "
    "approved by telephone, and no one produced a fresh calculation. "
    "Modern codes require written approval and an independent check "
    "for exactly this reason.\n\n"
    "Engineers add a caution. Redundancy - designing so that if one "
    "element fails another carries the load - is valuable, but it "
    "can hide damage until several elements have gone. Inspection "
    "matters as much as spare capacity.",
    [("What TWO causes of collapse does the passage identify?",
      ["A weak single member.", "A faulty connection.",
       "Poor materials.", "An unchecked assumption.",
       "Earthquake damage."], [1, 3],
      "Almost always the cause is a connection, a change made during "
      "construction, or an assumption that nobody checked",
      "A — matn aynan rad etadi: «rarely ... a single member»."),
     ("What TWO facts about the original Hyatt design are given?",
      ["Two walkways hung from one set of rods.",
       "The rods were too short.",
       "The rods could not be threaded fully.",
       "The walkways were made of concrete.",
       "The design was never approved."], [0, 2],
      "hung two walkways from a single set of long rods. The "
      "fabricator, finding those rods impossible to thread over "
      "their full length", ""),
     ("What TWO things are said about the change that was made?",
      ["It looked trivial.", "It saved money.",
       "It doubled the load on a connection.",
       "It was rejected by the engineer.",
       "It delayed the project."], [0, 2],
      "The change looked trivial on the drawing. In fact it doubled "
      "the load on the upper connection", ""),
     ("What TWO lessons are usually drawn from the case?",
      ["Load paths must be traced by hand.",
       "Fabricators should not propose changes.",
       "Approval must not be verbal.",
       "Walkways should be avoided.", "Rods must be shorter."],
      [0, 2],
      "load paths must be traced by hand after any change ... the "
      "revision was approved by telephone, and no one produced a "
      "fresh calculation", ""),
     ("What TWO points do engineers make about redundancy?",
      ["It is valuable.", "It is too expensive.",
       "It can hide damage.", "It replaces inspection.",
       "It is required by modern codes."], [0, 2],
      "Redundancy ... is valuable, but it can hide damage until "
      "several elements have gone",
      "D — matn teskarisini aytadi: tekshiruv baribir kerak.")],
))

# ============ 17-22: eng qiyin. 18 va 20 — Jahongirning ==========
# ============ namunalari, javoblari kitob kaliti bilan  ==========
PASSAGES.append(P(
    17, "THE PROBLEM WITH RECYCLING SYMBOLS",
    "The three chasing arrows stamped on plastic packaging are among "
    "the most recognised symbols in the world, and among the most "
    "misunderstood. The number inside the triangle is a resin "
    "identification code. It was introduced by the plastics industry "
    "in 1988 to tell sorting machinery what a container is made of. "
    "It was never a promise that the item would be recycled, and it "
    "carries no information about whether any local facility accepts "
    "it.\n\n"
    "The consequences are measurable. Surveys in several countries "
    "find that a majority of householders believe the symbol means "
    "the item is recyclable, and this belief predicts a specific "
    "behaviour: people place doubtful items in the recycling bin "
    "rather than the general waste, on the assumption that sorting "
    "staff will decide. The industry term is wish-cycling. A load "
    "contaminated by the wrong plastics, or by food residue, may be "
    "downgraded or sent to landfill entirely, so the well-meaning "
    "act makes the outcome worse rather than better.\n\n"
    "Reform is under discussion but is slower than campaigners "
    "expected, and for a reason that is rarely stated plainly. "
    "Labelling is set nationally while collection is arranged "
    "locally, so a symbol that is accurate in one district is "
    "misleading twenty kilometres away. Some countries have moved "
    "to instructions printed in words, and early evaluations "
    "suggest these reduce contamination, though they take up more "
    "space on the packaging and cost more to change when a council "
    "alters its rules.",
    [("What TWO facts about the resin code are given?",
      ["It was introduced in 1988.",
       "It was introduced by governments.",
       "It identifies the material.",
       "It guarantees recycling.",
       "It is required by law worldwide."], [0, 2],
      "It was introduced by the plastics industry in 1988 to tell "
      "sorting machinery what a container is made of",
      "B va D — matn aynan rad etadi."),
     ("What TWO things does the passage say about wish-cycling?",
      ["It is deliberate cheating.",
       "It comes from a mistaken belief.",
       "Doubtful items go in the recycling bin.",
       "It is encouraged by councils.",
       "It only happens with food packaging."], [1, 2],
      "a majority of householders believe the symbol means the item "
      "is recyclable, and this belief predicts a specific "
      "behaviour: people place doubtful items in the recycling bin",
      "A — QOPQON: matn «well-meaning» deydi, ya'ni niyat yaxshi."),
     ("What TWO things can ruin a whole load?",
      ["The wrong plastics.", "Too much paper.", "Food residue.",
       "Heavy items.", "Wet weather."], [0, 2],
      "A load contaminated by the wrong plastics, or by food "
      "residue, may be downgraded or sent to landfill", ""),
     ("What TWO reasons are given for slow reform?",
      ["Labelling is set nationally.",
       "The industry opposes change.",
       "Collection is arranged locally.",
       "Printers cannot produce the labels.",
       "Householders prefer symbols."], [0, 2],
      "Labelling is set nationally while collection is arranged "
      "locally, so a symbol that is accurate in one district is "
      "misleading twenty kilometres away",
      "B — sanoat qarshiligi mantiqan mumkin, matnda aytilmagan.")],
))

# ---------------------------------------------------------------
# 18-DARAJA — Jahongir yuborgan namuna:
#   "READING #22. On the trail of the honey badger"
# Javoblar kitob kalitiga mos: 1-2 B,D | 2 A,B | 3 C,D | 4 B,D | 5 A,E
# ---------------------------------------------------------------
PASSAGES.append(P(
    18, "ON THE TRAIL OF THE HONEY BADGER",
    "Researchers learn more about this fearless African predator\n\n"
    "On a recent field trip to the Kalahari Desert, a team of "
    "researchers learnt a lot more about honey badgers. They were "
    "rewarded with a detailed insight into how these fascinating "
    "creatures live and hunt.\n\n"
    "The team employed a local wildlife expert, Kitso Khama, to help "
    "them locate and follow the badgers across the desert. Their "
    "main aim was to study the badgers' movements and behaviour as "
    "discreetly as possible, without frightening them away or "
    "causing them to change their natural behaviour. They also "
    "planned to trap a few and study them close up before releasing "
    "them. In view of the animal's reputation, this was something "
    "that even Khama was reluctant to do.\n\n"
    "'The problem with honey badgers is they are naturally curious "
    "animals, especially when they see something new,' he says. "
    "'That, combined with their unpredictable nature, can be a "
    "dangerous mixture. If they sense you have food, for example, "
    "they won't be shy about coming right up to you for something to "
    "eat. They're actually quite sociable creatures around humans, "
    "but as soon as they feel they might be in danger, they can "
    "become extremely vicious. Fortunately this is rare, but it does "
    "happen.'\n\n"
    "The research confirmed many things that were already known. As "
    "expected, honey badgers ate any creatures they could catch and "
    "kill. Even poisonous snakes, feared and avoided by most other "
    "animals, were not safe from them. The researchers were "
    "surprised, however, by the animal's fondness for local melons, "
    "probably because of their high water content. Previously "
    "researchers thought that the animal got all of its liquid "
    "requirements from its prey. The team also learnt that, contrary "
    "to previous research findings, the badgers occasionally formed "
    "loose family groups. They were also able to confirm certain "
    "results from previous research, including the fact that female "
    "badgers never socialised with each other.\n\n"
    "Following some of the male badgers was a challenge, since they "
    "can cover large distances in a short space of time. Some "
    "hunting territories cover more than 500 square kilometres. "
    "Although they seem happy to share these territories with other "
    "males, there are occasional fights over an important food "
    "source, and male badgers can be as aggressive towards each "
    "other as they are towards other species.\n\n"
    "As the badgers became accustomed to the presence of people, it "
    "gave the team the chance to get up close to them without being "
    "the subject of the animals' curiosity - or their sudden "
    "aggression. The badgers' eating patterns, which had been "
    "disrupted, returned to normal. It also allowed the team to "
    "observe more closely some of the other creatures that form "
    "working associations with the honey badger, as these seemed to "
    "adopt the badgers' relaxed attitude when near humans.",
    [("Why did the wildlife experts visit the Kalahari desert? "
      "Choose TWO reasons.",
      ["To find where honey badgers live.",
       "To observe how honey badgers behave.",
       "To try to change the way honey badgers behave.",
       "To temporarily catch some honey badgers.",
       "To find out why honey badgers have such a bad reputation."],
      [1, 3],
      "Their main aim was to study the badgers' movements and "
      "behaviour ... They also planned to trap a few and study them "
      "close up before releasing them",
      "C — matn teskarisini aytadi: «without ... causing them to "
      "change their natural behaviour»."),
     ("What TWO things does Kitso Khama say about honey badgers?",
      ["They show interest in things they are not familiar with.",
       "It's hard to tell how they will behave.",
       "They are always looking for food.",
       "They do not enjoy human company.",
       "It is common for them to attack people."], [0, 1],
      "they are naturally curious animals, especially when they see "
      "something new ... combined with their unpredictable nature",
      "D — «quite sociable creatures around humans», ya'ni "
      "teskarisi. E — «Fortunately this is rare»."),
     ("What TWO things did the team find out about honey badgers?",
      ["There are some creatures they will not eat.",
       "They were afraid of poisonous creatures.",
       "They may get some of the water they need from fruit.",
       "They do not always live alone.",
       "Female badgers do not mix with male badgers."], [2, 3],
      "the animal's fondness for local melons, probably because of "
      "their high water content ... contrary to previous research "
      "findings, the badgers occasionally formed loose family groups",
      "E — QOPQON: urg'ochilari BIR-BIRI bilan aralashmaydi, "
      "erkaklari bilan emas."),
     ("According to the passage, which TWO features are typical of "
      "male badgers?",
      ["They don't run very quickly.",
       "They hunt over a very large area.",
       "They defend their territory from other badgers.",
       "They sometimes fight each other.",
       "They are more aggressive than females."], [1, 3],
      "Some hunting territories cover more than 500 square "
      "kilometres ... there are occasional fights over an important "
      "food source",
      "C — matn teskarisini aytadi: «happy to share these "
      "territories with other males»."),
     ("What TWO things happened when the honey badgers got used to "
      "humans being around them?",
      ["The badgers lost interest in people.",
       "The badgers became less aggressive towards other creatures.",
       "The badgers started eating more.",
       "Other animals started working with the badgers.",
       "Other animals near them became more relaxed."], [0, 4],
      "without being the subject of the animals' curiosity ... these "
      "seemed to adopt the badgers' relaxed attitude when near humans",
      "C — QOPQON: ovqatlanish «returned to normal», ya'ni "
      "TIKLANDI, ko'paymadi. D — hamkorlik allaqachon bor edi.")],
))

PASSAGES.append(P(
    19, "THE ECONOMICS OF THE COFFEE CUP",
    "Of the price paid for a cup of coffee in a European city, the "
    "grower typically receives between one and three per cent. The "
    "figure is often quoted as evidence of exploitation, and the "
    "conclusion may well be right, but the arithmetic behind it is "
    "more complicated than the headline suggests. Most of what the "
    "customer pays covers rent, wages and the milk, none of which "
    "the farmer supplies.\n\n"
    "A more revealing comparison is what happens to the beans "
    "themselves. Roasting adds far more to the value of a batch than "
    "growing it does, and almost all roasting takes place in "
    "consuming countries rather than producing ones. The reason is "
    "partly technical - roasted beans stale within weeks, while "
    "green beans keep for a year - but it is also political. Import "
    "tariffs in several large markets rise sharply once a bean has "
    "been roasted, which discourages producing countries from doing "
    "the profitable step at home.\n\n"
    "Certification schemes were designed to close the gap. Their "
    "record is mixed. Studies find that certified farmers do earn "
    "more per kilo, but they also pay the certification fee, and the "
    "gain is often absorbed by the cooperative rather than reaching "
    "the household. Where the schemes have worked best is not price "
    "at all: they have improved access to credit and to training, "
    "which raises yields, and yield is what actually determines a "
    "smallholder's income.",
    [("What TWO things does the passage say about the grower's "
      "share?",
      ["It is between one and three per cent.",
       "It is falling every year.",
       "It is often used as evidence of exploitation.",
       "It excludes the cost of milk.",
       "It has been calculated wrongly."], [0, 2],
      "the grower typically receives between one and three per cent. "
      "The figure is often quoted as evidence of exploitation",
      "E — matn hisobni «murakkabroq» deydi, xato demaydi."),
     ("What TWO reasons explain why roasting happens in consuming "
      "countries?",
      ["Roasted beans stale quickly.",
       "Producing countries lack machinery.",
       "Tariffs rise once beans are roasted.",
       "Consumers prefer local roasting.",
       "Green beans are cheaper to grow."], [0, 2],
      "roasted beans stale within weeks ... Import tariffs in "
      "several large markets rise sharply once a bean has been "
      "roasted",
      "B — QOPQON: sabab siyosiy va texnik, uskuna emas."),
     ("What TWO criticisms of certification schemes are made?",
      ["Farmers pay a fee.",
       "The gain may stay with the cooperative.",
       "Certified coffee tastes worse.",
       "Prices per kilo fall.",
       "Few farmers qualify."], [0, 1],
      "they also pay the certification fee, and the gain is often "
      "absorbed by the cooperative rather than reaching the "
      "household", "D — matnga zid: ular ko'proq oladi."),
     ("What TWO benefits of certification does the passage accept?",
      ["Better access to credit.", "Higher prices for consumers.",
       "Access to training.", "Larger farms.",
       "Guaranteed buyers."], [0, 2],
      "they have improved access to credit and to training, which "
      "raises yields", "")],
))

# ---------------------------------------------------------------
# 20-DARAJA — Jahongir yuborgan namuna:
#   "READING #21. Humpback whale breaks migration record"
# 7 savol, kitob kaliti: B,C | C,E | A,E | A,E | B,D | A,D | B,E
# ---------------------------------------------------------------
PASSAGES.append(P(
    20, "HUMPBACK WHALE BREAKS MIGRATION RECORD",
    "A whale surprises researchers with her journey.\n\n"
    "A lone humpback whale travelled more than 9,800 kilometres from "
    "breeding areas in Brazil to those in Madagascar, setting a "
    "record for the longest mammal migration ever documented.\n\n"
    "Humpback whales (Megaptera novaeangliae) are known to have some "
    "of the longest migration distances of all mammals, and this "
    "huge journey is about 400 kilometres farther than the previous "
    "humpback record. The finding was made by Peter Stevick, a "
    "biologist at the College of the Atlantic in Bar Harbor, "
    "Maine.\n\n"
    "The whale's journey was unusual not only for its length, but "
    "also because it travelled across almost 90 degrees of longitude "
    "from west to east. Typically, humpbacks move in a north-south "
    "direction between cold feeding areas and warm breeding grounds "
    "- and the longest journeys which have been recorded until now "
    "have been between breeding and feeding sites.\n\n"
    "The whale, a female, was first spotted off the coast of Brazil, "
    "where researchers photographed its tail fluke and took skin "
    "samples for chromosome testing to determine the animal's sex. "
    "Two years later, a tourist on a whale-watching boat snapped a "
    "photo of the humpback near Madagascar.\n\n"
    "To match the two sightings, Stevick's team used an extensive "
    "international catalogue of photographs of the undersides of "
    "tail flukes, which have distinctive markings. Researchers "
    "routinely compare the markings in each new photograph to those "
    "in the archive.\n\n"
    "The scientists then estimated the animal's shortest possible "
    "route: an arc skirting the southern tip of South Africa and "
    "heading north-east towards Madagascar. The minimum distance is "
    "9,800 kilometres, says Stevick, but this is likely to be an "
    "underestimate, because the whale probably took a detour to feed "
    "on krill in the Southern Ocean near Antarctica before reaching "
    "its destination.\n\n"
    "Most humpback-whale researchers focus their efforts on the "
    "Northern Hemisphere because the Southern Ocean near the "
    "Antarctic is a hostile environment and it is hard to get to, "
    "explains Rochelle Constantine, who studies the ecology of "
    "humpback whales at the University of Auckland in New Zealand. "
    "But, for whales, oceans in the Southern Hemisphere are wider "
    "and easier to travel across, says Constantine. Scientists will "
    "probably observe more long-distance migrations in the Southern "
    "Hemisphere as satellite tracking becomes increasingly common, "
    "she adds.\n\n"
    "Daniel Palacios, an oceanographer at the University of Hawaii "
    "at Manoa, says that the record-breaking journey could indicate "
    "that migration patterns are shifting as populations begin to "
    "recover from near-extinction and the population increases. But "
    "the reasons why the whale did not follow the usual migration "
    "routes remain a mystery. She could have been exploring new "
    "habitats, or simply have lost her way. 'We generally think of "
    "humpback whales as very well studied, but then they surprise us "
    "with things like this,' Palacios says. 'Undoubtedly there are a "
    "lot of things we still don't know about whale migration.'",
    [("What TWO aspects of the whale's journey surprised "
      "researchers?",
      ["the destination", "the direction", "the distance",
       "the reason", "the season"], [1, 2],
      "The whale's journey was unusual not only for its length, but "
      "also because it travelled across almost 90 degrees of "
      "longitude from west to east",
      "«length» = distance (C), «west to east» = direction (B)."),
     ("The passage mentions reasons why whales generally migrate. "
      "What TWO reasons are given?",
      ["to avoid humans", "to be safe", "to eat", "to keep warm",
       "to produce young"], [2, 4],
      "humpbacks move in a north-south direction between cold "
      "feeding areas and warm breeding grounds",
      "D — QOPQON: «warm» joyning TA'RIFI, sabab emas. Sabab — "
      "breeding."),
     ("What TWO methods did researchers use to record the identity "
      "of the whale near Brazil?",
      ["They analysed part of the whale's body.",
       "They marked its tail.",
       "They made notes of its behaviour.",
       "They recorded the sounds it made.",
       "They took a picture."], [0, 4],
      "researchers photographed its tail fluke and took skin samples "
      "for chromosome testing",
      "B — QOPQON: dumini SURATGA oldi, belgi qo'ymadi."),
     ("The passage mentions places the whale may have passed close "
      "to on its journey. Which TWO places may the whale have "
      "passed?",
      ["Antarctica", "Hawaii", "Maine", "New Zealand",
       "South Africa"], [0, 4],
      "an arc skirting the southern tip of South Africa ... took a "
      "detour to feed on krill in the Southern Ocean near Antarctica",
      "Hawaii, Maine va New Zealand matnda BOR — lekin ular "
      "olimlarning ish joyi, kitning yo'li emas. Bu turdagi eng "
      "klassik qopqon."),
     ("The passage says that more research is done in the Northern "
      "Hemisphere. Which TWO reasons are given for this?",
      ["It contains more whales.", "It has friendlier surroundings.",
       "There are more samples available.", "It is easier to reach.",
       "It contains smaller whales."], [1, 3],
      "the Southern Ocean near the Antarctic is a hostile "
      "environment and it is hard to get to",
      "Janub haqidagi gap SHIMOL foydasiga o'giriladi: hostile -> "
      "friendlier, hard to get to -> easier to reach."),
     ("The passage suggests why the whale made a different journey "
      "from usual. Which TWO reasons does it suggest?",
      ["She did not know where she was going.",
       "She did not want to breed.",
       "She wanted to escape a danger.",
       "She was looking for a new place to live.",
       "She was recovering from an illness."], [0, 3],
      "She could have been exploring new habitats, or simply have "
      "lost her way",
      "«lost her way» = A, «exploring new habitats» = D."),
     ("Which TWO methods of finding out where whales migrate are "
      "mentioned in the passage?",
      ["attaching radio transmitters",
       "comparing pictures taken in different places",
       "following them in boats", "placing cameras in key positions",
       "following their movements from space"], [1, 4],
      "Researchers routinely compare the markings in each new "
      "photograph to those in the archive ... as satellite tracking "
      "becomes increasingly common",
      "«satellite tracking» = kosmosdan kuzatish (E).")],
))

PASSAGES.append(P(
    21, "THE MYTH OF THE LONE INVENTOR",
    "The story of invention is usually told through individuals, and "
    "the telling is almost always misleading. Historians of "
    "technology have long noticed a pattern they call simultaneous "
    "invention: the telephone, the telegraph, the jet engine and the "
    "theory of natural selection were each arrived at independently "
    "by two or more people within a few years, and sometimes within "
    "weeks. The pattern is too regular to be coincidence.\n\n"
    "The usual explanation is that an invention becomes possible "
    "only when the components it depends on already exist, and once "
    "they exist it becomes almost inevitable. Nobody could build a "
    "practical aeroplane before lightweight engines were available; "
    "once they were, several teams were close. What the individual "
    "supplies, on this account, is timing and persistence rather "
    "than the idea itself.\n\n"
    "The patent system sits awkwardly with all of this. It awards a "
    "monopoly to whoever files first, which assumes exactly the "
    "model of the lone originator that historians question. Bell "
    "and Gray filed on the same day. The system also creates an "
    "incentive to file early and broadly, which can block the very "
    "follow-on work that turns an idea into a product.\n\n"
    "Some economists therefore argue for shorter patent terms in "
    "fast-moving fields. Others reply that without the prospect of "
    "exclusivity the expensive final stage - turning a working "
    "prototype into something manufacturable - would not be funded "
    "at all, and point to pharmaceuticals, where that stage costs "
    "more than the discovery itself.",
    [("What TWO things are said about simultaneous invention?",
      ["It has been noticed by historians.",
       "It happens only in engineering.",
       "It is too regular to be chance.",
       "It was first described by Bell.",
       "It applies to natural selection."], [0, 2],
      "Historians of technology have long noticed a pattern they "
      "call simultaneous invention ... The pattern is too regular to "
      "be coincidence",
      "E — tabiiy tanlanish MISOL, «what is said about the "
      "pattern» emas."),
     ("According to the usual explanation, what TWO things does the "
      "individual inventor contribute?",
      ["The original idea.", "Timing.", "Funding.", "Persistence.",
       "The components."], [1, 3],
      "What the individual supplies, on this account, is timing and "
      "persistence rather than the idea itself",
      "A — matn aynan rad etadi."),
     ("What TWO criticisms of the patent system are made?",
      ["It assumes a lone originator.",
       "It is too slow to grant patents.",
       "It can block follow-on work.",
       "It is too expensive for individuals.",
       "It ignores foreign inventors."], [0, 2],
      "It awards a monopoly to whoever files first, which assumes "
      "exactly the model of the lone originator ... which can block "
      "the very follow-on work",
      "D — mantiqan to'g'ri tanqid, lekin matnda yo'q."),
     ("What TWO arguments are made in defence of patents?",
      ["They reward the true inventor.",
       "The final stage would not be funded without them.",
       "They shorten development time.",
       "Pharmaceuticals show the final stage is costly.",
       "They encourage simultaneous invention."], [1, 3],
      "without the prospect of exclusivity the expensive final "
      "stage ... would not be funded at all, and point to "
      "pharmaceuticals, where that stage costs more than the "
      "discovery itself", "")],
))

PASSAGES.append(P(
    22, "MEASURING WHAT MATTERS IN SCHOOLS",
    "For thirty years the dominant instrument of school "
    "accountability has been the published league table. Its "
    "defenders make a straightforward case: parents are entitled to "
    "comparable information, and schools that were quietly failing "
    "for decades were exposed by it. Both claims are supported by "
    "evidence.\n\n"
    "The objections are equally evidenced, and they are not mainly "
    "about fairness to schools. A raw table measures the intake as "
    "much as the teaching; a school in a wealthy district will rank "
    "highly whatever its staff do. Value-added measures, which "
    "compare a pupil's result to what pupils with the same starting "
    "point achieved elsewhere, correct for this and are now used in "
    "several systems. They are harder to explain to parents, and "
    "they are noisy for small schools, where a single cohort can "
    "swing the figure.\n\n"
    "The deeper problem is behavioural. Once a number carries "
    "consequences, effort moves towards the number. Schools have "
    "concentrated resources on pupils sitting just below a grade "
    "boundary, because moving those pupils changes the published "
    "figure while helping the weakest does not. Subjects that are "
    "not counted lose teaching time. None of this requires "
    "dishonesty; it is the predictable response of rational people "
    "to what is being measured.\n\n"
    "The responses now being tried are partial. Some systems publish "
    "several measures at once, including destinations after school "
    "and pupil wellbeing surveys, on the theory that a basket is "
    "harder to distort than a single figure. Others have moved to "
    "inspection judgements that a school cannot predict in advance. "
    "Both approaches reduce gaming, and both are more expensive and "
    "slower than printing a table.",
    [("What TWO arguments do defenders of league tables make?",
      ["Parents are entitled to comparable information.",
       "Tables improve teaching directly.",
       "Failing schools were exposed.",
       "Tables are cheap to produce.",
       "Tables are fair to all schools."], [0, 2],
      "parents are entitled to comparable information, and schools "
      "that were quietly failing for decades were exposed by it",
      "D — arzonligi oxirgi xatboshida, himoya dalili sifatida "
      "emas."),
     ("What TWO problems with value-added measures are given?",
      ["They ignore the intake.",
       "They are hard to explain to parents.",
       "They are unfair to wealthy schools.",
       "They are unreliable for small schools.",
       "They are not yet used anywhere."], [1, 3],
      "They are harder to explain to parents, and they are noisy for "
      "small schools",
      "A va E — matnga zid: ular aynan intake'ni hisobga oladi va "
      "allaqachon qo'llanilyapti."),
     ("What TWO behaviours does the passage describe as responses "
      "to measurement?",
      ["Falsifying results.",
       "Focusing on pupils near a grade boundary.",
       "Reducing time for uncounted subjects.",
       "Excluding weak pupils from school.",
       "Hiring more teachers."], [1, 2],
      "Schools have concentrated resources on pupils sitting just "
      "below a grade boundary ... Subjects that are not counted lose "
      "teaching time",
      "A — matn aynan rad etadi: «None of this requires dishonesty»."),
     ("What TWO drawbacks of the newer approaches are mentioned?",
      ["They are more expensive.",
       "They do not reduce gaming.",
       "They are slower.",
       "Parents ignore them.",
       "They are easier to distort."], [0, 2],
      "Both approaches reduce gaming, and both are more expensive "
      "and slower than printing a table",
      "B va E — matnga zid.")],
))


# =====================================================================
#  QURISH
# =====================================================================
# Kitobdagi tartib SAQLANADIGAN darajalar — Jahongirning
# namunalari. Ularda javob harflari kitob kaliti bilan bir xil
# qolishi shart, shuning uchun aylantirilmaydi.
_KEEP_ORDER = (18, 20)


def _rotate(opts, ci, counter):
    """Javob juftligini aylantirib, harflar bo'ylab tekis tarqatadi.

    NEGA KERAK. Birinchi variantda to'g'ri javoblar A 65 / C 68 ga
    to'planib, E atigi 5 marta javob bo'lgan edi (200 dan). Ya'ni
    o'quvchi E ni umuman o'qimasa ham deyarli hech narsa
    yo'qotmasdi — bu mashqni buzadi.

    Beshta variantni aylantirsak, juftlik orasidagi MASOFA
    o'zgarmaydi (AB -> BC -> CD ...), shuning uchun juftliklar ikki
    guruhga bo'linadi: masofa 1 (AB, BC, CD, DE, AE) va masofa 2
    (AC, BD, CE, AD, BE). Har guruh ichida boshlanish harfini
    navbatma-navbat surib chiqsak, beshala harf ham bir xil
    chastotada javob bo'ladi.

    Qaytaradi: (yangi_variantlar, yangi_javob_indekslari, surish)."""
    i, j = ci
    d1 = j - i
    d2 = 5 - d1
    start, gap = (i, d1) if d1 <= d2 else (j, d2)
    shift = (counter % 5 - start) % 5
    new_opts = [None] * 5
    for k, t in enumerate(opts):
        new_opts[(k + shift) % 5] = t
    new_ci = sorted(((i + shift) % 5, (j + shift) % 5))
    return new_opts, new_ci, shift, gap


def _remap_note(note, shift):
    """Izohdagi «B, D, E aytilmagan» kabi harflarni yangi
    joylashuvga moslaydi. Bir vaqtda almashtiriladi — ketma-ket
    qilinsa zanjir hosil bo'lardi (A->B->C)."""
    if not note or not shift:
        return note
    import re as _re
    return _re.sub(
        r"(?<![\w'’])([A-E])(?![\w'’])",
        lambda m: LET[(LET.index(m.group(1)) + shift) % 5],
        note)


def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase)."""
    out = []
    turn = {1: 0, 2: 0}
    for p in PASSAGES:
        lvl = p["level"]
        for i, q in enumerate(p["qs"], 1):
            prompt, opts, ci, quote, note = q
            assert len(opts) == 5, (lvl, i, "5 ta variant kerak")
            assert len(ci) == 2, (lvl, i, "2 ta to'g'ri javob kerak")
            assert ci[0] < ci[1], (lvl, i, "tartib")
            if lvl not in _KEEP_ORDER:
                _g = min(ci[1] - ci[0], 5 - (ci[1] - ci[0]))
                opts, ci, sh, _g = _rotate(opts, ci, turn[_g])
                turn[_g] += 1
                note = _remap_note(note, sh)
            labelled = [f"{LET[k]}. {t}" for k, t in enumerate(opts)]
            answer = SEP.join(labelled[k] for k in ci)
            expl = (f"To'g'ri javob: {LET[ci[0]]} va {LET[ci[1]]}. "
                    f"Matnda: «{quote}».")
            if note:
                expl += " " + note
            out.append((
                KIND, lvl,
                {"passage": f"{p['title']}\n\n{p['text']}",
                 "prompt": prompt,
                 "options": labelled,
                 "pick": 2,
                 "instruction": "Choose TWO letters, A-E.",
                 "step": lvl, "step_title": f"{lvl}-daraja",
                 "order": i,
                 "tip": PICK_TIPS[(lvl + i) % len(PICK_TIPS)][0]},
                answer, expl, None, None))
    return out


def seed_pick(db):
    """Idempotent: bor bo'lsa qayta yozmaydi (hech narsa o'chmaydi)."""
    import json
    import models
    rows = build_rows()
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
    for kind, level, payload, answer, explain, alt, para in rows:
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
