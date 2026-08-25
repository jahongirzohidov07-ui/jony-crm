# -*- coding: utf-8 -*-
"""IELTS READING — MULTIPLE CHOICE, A/B/C/D (2026-08-25).

Jahongir: "mana bular Multiple choice savollari aynan Reading
Part 3 uchun shunaqa boladi butun bir paragraphga savol beradu
shunaqadan osondan boshlab qiyinga qarab ketganingda buni 20-25
orasiga qoyvorasan."

TUZILISHI. 26 ta matn, jami 122 savol, daraja 1..26:
  1-8    — qisqa matn, 4 savoldan; javob bitta jumlada;
  9-16   — 5 savoldan; javob butun XATBOSHIdan chiqadi;
  17-20  — uzunroq, chalg'ituvchi variantlar kuchayadi;
  21     — "READING #16. The ballpoint pen" (namuna);
  22-23  — oraliq;
  24     — "Air conditioning" (Jahongirning ikkinchi namunasi);
  25-26  — eng qiyini: muallif fikri va xulosaga oid savollar.

DIQQAT. Havo sovutgich savollari yuborilgan, lekin MATNI
yuborilmagan edi. Shuning uchun o'sha beshta savolga aynan mos
keladigan matn yozildi — javoblar bir ma'noli bo'lishi uchun.

BU TURNING O'ZIGA XOSLIGI. Boshqa turlarda javob matndan
KO'CHIRILADI. Bu yerda esa to'rt variantning hammasi matndagi
so'zlardan yasalgan — biri to'g'ri, uchtasi ataylab yaqin. Shuning
uchun izohda faqat to'g'ri javob emas, NOTO'G'RI variantlar nega
noto'g'ri ekani ham aytiladi.
"""

SKILL = "ielts_reading"
KIND = "read_mcq"
LET = ["A", "B", "C", "D"]


# =====================================================================
#  QOIDALAR
# =====================================================================
MCQ_TIPS = [
    ("Multiple Choice nima",
     "Savol beriladi va to'rtta variant (A, B, C, D). Bittasi "
     "to'g'ri. Variantlarning hammasi matndagi so'zlardan "
     "yasalgani uchun hammasi tanish ko'rinadi — shu eng katta "
     "qiyinchilik.", ""),
    ("AVVAL SAVOLNI o'qing, variantlarni emas",
     "Variantlarni o'qib bo'lgach ularning hammasi mantiqiy "
     "tuyuladi va miya adashadi. To'g'ri tartib: savolni o'qing -> "
     "matndan javobni o'zingiz toping -> keyingina variantlarga "
     "qarang va o'zingiznikiga mos kelganini tanlang.",
     "Savol: Why was Biro's pen better than earlier models?\n"
     "Matn: «he produced a ballpoint pen that didn't leak when the "
     "pen wasn't being used»\nSizning javobingiz: siyoh oqmasdi\n"
     "Variant: C The ink stayed in the pen until it was needed"),
    ("NOTO'G'RI variantlarni chiqarib tashlang",
     "To'rttadan uchtasi noto'g'ri va odatda uch xil sababdan: "
     "(1) matnda umuman aytilmagan; (2) aytilgan, lekin BOSHQA "
     "narsa haqida; (3) qisman to'g'ri, lekin bitta so'zi noto'g'ri "
     "(«only», «all», «never»).", ""),
    ("Matndagi so'z variantda bo'lsa — ehtiyot bo'ling",
     "«It was designed by a chemist» — matnda «chemist» bor "
     "(Bironing akasi kimyogar edi), lekin savol qalam nega "
     "YAXSHIROQ ekanini so'rayapti, kim yasaganini emas.", ""),
    ("Savol butun XATBOSHIga tegishli bo'lishi mumkin",
     "Part 3 da savol ko'pincha bitta jumlaga emas, butun bo'lakka "
     "tegishli bo'ladi: «What was the purpose of the research?» — "
     "javob bir necha jumlani birga o'qigandagina chiqadi.", ""),
    ("Savollar matn tartibida boradi",
     "1-savol javobi matnning boshida, 5-savolniki oxirida. Agar "
     "javobni topolmasangiz, oldingi javobingizdan keyingi "
     "qismdan qidiring.", ""),
    ("«Most likely» va «suggests» — fikr savollari",
     "Bunday savollarda javob matnda so'zma-so'z yozilmagan "
     "bo'ladi; muallifning ohangi va tanlagan so'zlaridan chiqadi. "
     "Ammo baribir MATNGA tayanish shart — o'zingizdan "
     "o'ylamang.", ""),
    ("Ikki variant juda o'xshash bo'lsa",
     "Ularning FARQINI toping: odatda bitta so'z ajratib turadi "
     "(«all» va «most», «caused» va «contributed to»). O'sha so'z "
     "matnda tasdiqlanganmi — shu hal qiladi.", ""),
]


def P(level, title, text, qs):
    return {"level": level, "title": title, "text": text, "qs": qs}


PASSAGES = []

# ============ 1-8 DARAJA: qisqa matn, 4 savol ====================
PASSAGES.append(P(
    1, "THE NEW LIBRARY",
    "The town's new library opened in March. It cost four million "
    "pounds, most of which came from the regional government. The "
    "old building, which was over a hundred years old, had become "
    "too small and had no lift. The new library has three floors, a "
    "cafe and a room where children can hear stories on Saturday "
    "mornings.",
    [("When did the library open?",
      ["In March.", "In summer.", "A hundred years ago.",
       "On a Saturday."], 0,
      "The town's new library opened in March",
      "B, C va D — matndagi boshqa ma'lumotlar: yoz aytilmagan, "
      "«a hundred years» eski binoga tegishli, shanba esa "
      "ertaklar kuni."),
     ("Who paid for most of the cost?",
      ["The town council.", "The regional government.",
       "Local businesses.", "Visitors to the library."], 1,
      "most of which came from the regional government",
      "A, C, D matnda umuman aytilmagan."),
     ("What was wrong with the old building?",
      ["It was in the wrong place.", "It was too expensive to heat.",
       "It was too small and had no lift.",
       "It had no room for children."], 2,
      "had become too small and had no lift",
      "D chalg'ituvchi: bolalar xonasi YANGI binoda bor."),
     ("What happens on Saturday mornings?",
      ["The cafe is free.", "Children listen to stories.",
       "The library closes early.", "New books arrive."], 1,
      "a room where children can hear stories on Saturday mornings",
      "Qolganlari aytilmagan.")],
))

PASSAGES.append(P(
    2, "A DAY AT THE ZOO",
    "The zoo opens at nine, but the animals are fed at eight, and "
    "visitors who arrive early can watch this through a window. "
    "Tickets cost eight pounds for adults; children under five enter "
    "free. The most popular animals are the penguins, although the "
    "zoo's director says the reptile house is the one that teaches "
    "visitors most.",
    [("Why do some visitors arrive before nine?",
      ["The zoo is cheaper then.", "To watch the animals being fed.",
       "To avoid the crowds.", "The penguins are more active."], 1,
      "the animals are fed at eight, and visitors who arrive early "
      "can watch this through a window",
      "A, C, D matnda yo'q — «erta kelish» sababi faqat "
      "boqish."),
     ("How much does a four-year-old pay?",
      ["Eight pounds.", "Half price.", "Nothing.",
       "The same as an adult."], 2,
      "children under five enter free",
      "A va D kattalar narxi; B umuman aytilmagan."),
     ("Which animals do most visitors like best?",
      ["The reptiles.", "The penguins.", "The birds.",
       "The zoo does not say."], 1,
      "The most popular animals are the penguins",
      "A — QOPQON: reptiliyalar «eng ko'p o'rgatadi», eng "
      "sevimlisi emas."),
     ("What does the director say about the reptile house?",
      ["It is the most expensive part.",
       "It teaches visitors the most.", "It should be made bigger.",
       "Few people visit it."], 1,
      "the reptile house is the one that teaches visitors most",
      "C va D aytilmagan.")],
))

PASSAGES.append(P(
    3, "THE BREAD SHOP",
    "Anvar opened his bakery six years ago after losing his job at a "
    "factory. He had never baked professionally, and for the first "
    "year he made very little money. What changed things was a "
    "decision to bake only four kinds of bread instead of twenty. "
    "Today he employs five people and sells to three restaurants.",
    [("Why did Anvar open a bakery?",
      ["He had always wanted to.", "He lost his previous job.",
       "His family asked him to.", "He trained as a baker."], 1,
      "after losing his job at a factory",
      "D — QOPQON: matn aksincha, u kasbiy non yopmagan."),
     ("What was the first year like?",
      ["Very successful.", "He earned almost nothing.",
       "He had too many customers.", "He worked alone by choice."], 1,
      "for the first year he made very little money",
      "A matnga zid; C va D aytilmagan."),
     ("What improved the business?",
      ["Making fewer kinds of bread.", "Moving to a new shop.",
       "Lowering his prices.", "Hiring more staff."], 0,
      "a decision to bake only four kinds of bread instead of twenty",
      "D — natija, sabab emas: xodimlar keyin yollangan."),
     ("How many people work there now?",
      ["Three.", "Four.", "Five.", "Twenty."], 2,
      "he employs five people",
      "Chalg'ituvchi sonlar: uch — restoranlar, to'rt — non "
      "turlari, yigirma — eski soni.")],
))

PASSAGES.append(P(
    4, "A CYCLING HOLIDAY",
    "Last summer Nodira and two friends cycled from the mountains to "
    "the sea, a distance of 340 kilometres. They planned six days "
    "but took eight, mainly because of a puncture that could not be "
    "repaired in a village with no shop. Nodira says the hardest "
    "part was not the hills but the heat in the afternoons.",
    [("How far did they travel?",
      ["340 kilometres.", "Six days.", "Eight kilometres.",
       "From the sea to the mountains."], 0,
      "a distance of 340 kilometres",
      "B — vaqt, masofa emas; D — yo'nalish teskari."),
     ("Why did the trip take longer than planned?",
      ["They were tired.", "The weather was bad.",
       "A tyre problem delayed them.", "They changed the route."], 2,
      "mainly because of a puncture that could not be repaired",
      "B — QOPQON: issiq aytilgan, lekin kechikish sababi emas."),
     ("Why could the puncture not be repaired quickly?",
      ["They had no tools.", "The village had no shop.",
       "It was late at night.", "Nobody knew how."], 1,
      "in a village with no shop", "Qolganlari aytilmagan."),
     ("What did Nodira find most difficult?",
      ["The hills.", "The distance.", "The afternoon heat.",
       "Cycling with friends."], 2,
      "the hardest part was not the hills but the heat in the "
      "afternoons",
      "A — QOPQON: matn aynan «not the hills» deydi.")],
))

PASSAGES.append(P(
    5, "THE SCHOOL GARDEN",
    "Three years ago a teacher at School 42 turned an unused corner "
    "of the yard into a vegetable garden. Pupils grow tomatoes, "
    "beans and herbs, and the produce goes to the school kitchen. "
    "The teacher expected the main benefit to be biology lessons, "
    "but says the real change has been in behaviour: pupils who "
    "worked in the garden argue less at break time.",
    [("What was the corner used for before?",
      ["Sport.", "Parking.", "Nothing.", "Storing rubbish."], 2,
      "an unused corner of the yard",
      "PARAFFRAZ: unused = hech narsaga ishlatilmagan."),
     ("Where does the food go?",
      ["It is sold at a market.", "To the school kitchen.",
       "Pupils take it home.", "It is given to a charity."], 1,
      "the produce goes to the school kitchen", "Qolganlari yo'q."),
     ("What benefit did the teacher expect?",
      ["Better behaviour.", "Cheaper school meals.",
       "Help with biology lessons.", "More parents visiting."], 2,
      "The teacher expected the main benefit to be biology lessons",
      "A — QOPQON: bu KUTILMAGAN natija, kutilgan emas."),
     ("What actually changed most?",
      ["The pupils' marks.", "The pupils' behaviour.",
       "The size of the garden.", "The number of teachers."], 1,
      "the real change has been in behaviour",
      "PARAFFRAZ: actually = real change.")],
))

PASSAGES.append(P(
    6, "THE OLD CINEMA",
    "The Rex cinema closed in 2011 after audiences fell below fifty "
    "a night. A group of residents bought it in 2018 and reopened it "
    "with volunteers running the box office. They kept ticket prices "
    "low deliberately, accepting that the cinema would never make a "
    "profit, and it now shows films four nights a week.",
    [("Why did the cinema close?",
      ["The building was unsafe.", "Too few people came.",
       "The owner retired.", "A new cinema opened nearby."], 1,
      "closed in 2011 after audiences fell below fifty a night",
      "C va D aytilmagan; A ham yo'q."),
     ("Who reopened it?",
      ["The council.", "A film company.", "Local residents.",
       "The original owner."], 2,
      "A group of residents bought it in 2018", "Kim sotib olgani."),
     ("Why are the tickets cheap?",
      ["The building costs little to run.",
       "It was a deliberate choice.", "The films are old.",
       "The council pays part of the cost."], 1,
      "They kept ticket prices low deliberately",
      "PARAFFRAZ: deliberate choice = deliberately."),
     ("What do the owners accept?",
      ["That it will close again.", "That it will not make money.",
       "That volunteers will leave.",
       "That they must show new films."], 1,
      "accepting that the cinema would never make a profit",
      "PARAFFRAZ: not make money = never make a profit.")],
))

PASSAGES.append(P(
    7, "LEARNING A SECOND LANGUAGE AS AN ADULT",
    "It is often said that children learn languages easily and "
    "adults do not. The evidence is more complicated. Adults "
    "actually learn grammar and vocabulary faster in the first "
    "year, because they can use rules and their first language to "
    "help. Children overtake them later, and the one area where "
    "they are clearly better is pronunciation.",
    [("What does the writer say about the common belief?",
      ["It is completely wrong.", "It is too simple.",
       "It applies only to grammar.", "Nobody has tested it."], 1,
      "The evidence is more complicated",
      "A juda kuchli: matn butunlay rad etmaydi, murakkabroq "
      "deydi."),
     ("What do adults do better at first?",
      ["Pronunciation.", "Listening.",
       "Grammar and vocabulary.", "Writing."], 2,
      "Adults actually learn grammar and vocabulary faster in the "
      "first year", "A — QOPQON: bu bolalarning kuchli tomoni."),
     ("Why do adults start faster?",
      ["They study more hours.", "They can use rules and their "
       "first language.", "They have better memories.",
       "They are more motivated."], 1,
      "because they can use rules and their first language to help",
      "C va D aytilmagan."),
     ("Where are children clearly better?",
      ["Vocabulary.", "Speed of progress.", "Pronunciation.",
       "Grammar."], 2,
      "the one area where they are clearly better is pronunciation",
      "«clearly better» — faqat bitta soha.")],
))

PASSAGES.append(P(
    8, "THE RETURN OF THE TRAM",
    "Many European cities removed their trams in the 1950s and "
    "'60s, believing that buses were more flexible and that the "
    "future belonged to the car. Several have since rebuilt them at "
    "far greater cost than removal saved. The argument now made in "
    "their favour is not speed — buses can be as fast — but capacity "
    "and the fact that a fixed route encourages building beside it.",
    [("Why were trams removed?",
      ["They were too slow.", "Buses were thought more flexible.",
       "They were too expensive to run.",
       "Passengers preferred cars."], 1,
      "believing that buses were more flexible",
      "D — QOPQON: mashina aytilgan, lekin sabab sifatida emas."),
     ("What does the writer say about rebuilding them?",
      ["It was cheap.", "It cost more than was saved by removal.",
       "It was paid for by bus companies.",
       "It has not yet happened."], 1,
      "at far greater cost than removal saved", "Taqqoslash."),
     ("What is NOT an argument for trams today?",
      ["Capacity.", "Speed.", "Encouraging building.",
       "Fixed routes."], 1,
      "The argument now made in their favour is not speed",
      "Savol INKOR shaklida — «not» so'ziga diqqat."),
     ("Why does a fixed route matter?",
      ["It is cheaper to maintain.",
       "It encourages building beside it.",
       "It is easier for drivers.", "It reduces accidents."], 1,
      "the fact that a fixed route encourages building beside it",
      "Qolganlari aytilmagan.")],
))

# ============ 9-16 DARAJA: 5 savol, xatboshi darajasida =========
PASSAGES.append(P(
    9, "THE HISTORY OF THE UMBRELLA",
    "Umbrellas were used in China more than two thousand years ago, "
    "but only for shade and only by people of rank; carrying one was "
    "a mark of status rather than a response to the weather.\n\n"
    "In eighteenth-century Britain they were considered unmanly. "
    "Jonas Hanway, a traveller who carried one openly in London for "
    "thirty years, was laughed at in the street and, more "
    "significantly, opposed by coach drivers, who saw rain as good "
    "for business.\n\n"
    "Attitudes changed slowly. By the 1850s the umbrella had become "
    "ordinary, and the steel-ribbed design patented by Samuel Fox "
    "made it light enough to carry every day. The basic shape has "
    "hardly altered since.",
    [("What was the original purpose of the umbrella?",
      ["To keep off rain.", "To provide shade.",
       "To show wealth only.", "To use in ceremonies."], 1,
      "only for shade and only by people of rank",
      "C qisman to'g'ri (maqom belgisi edi), lekin savol "
      "MAQSADni so'rayapti — soya."),
     ("Why did coach drivers oppose Hanway?",
      ["He blocked the road.", "Rain brought them customers.",
       "He refused to pay.", "They found him ridiculous."], 1,
      "opposed by coach drivers, who saw rain as good for business",
      "D — QOPQON: ko'chadagilar kulgan, aravakashlar esa BOSHQA "
      "sababdan qarshi bo'lgan."),
     ("How long did Hanway carry an umbrella?",
      ["Two thousand years.", "Eighteen years.", "Thirty years.",
       "Until the 1850s."], 2,
      "carried one openly in London for thirty years",
      "Chalg'ituvchi sonlar: 2000 yil — Xitoy, XVIII asr — davr."),
     ("What did Samuel Fox's design achieve?",
      ["It made umbrellas cheaper.",
       "It made them light enough for daily use.",
       "It made them waterproof.", "It made them fashionable."], 1,
      "the steel-ribbed design patented by Samuel Fox made it light "
      "enough to carry every day", "Aynan og'irlik haqida."),
     ("What does the writer say about the modern umbrella?",
      ["It is very different from the Victorian one.",
       "Its shape has changed little.",
       "It is no longer popular.", "It is made of new materials."], 1,
      "The basic shape has hardly altered since",
      "PARAFFRAZ: changed little = hardly altered.")],
))

PASSAGES.append(P(
    10, "WHY WE FORGET NAMES",
    "Most people find names harder to remember than faces or jobs, "
    "and psychologists have a specific explanation for this.\n\n"
    "A face carries meaning: shape, expression, resemblance to "
    "someone else. A job carries meaning too — hearing that a man is "
    "a baker calls up bread, ovens and early mornings. A surname, "
    "however, usually carries none. 'Baker' as a name connects to "
    "nothing at all.\n\n"
    "This was demonstrated in an experiment in which participants "
    "were shown the same word as a name for some faces and as an "
    "occupation for others. The word was remembered far more often "
    "when it was a job, although it was exactly the same word.",
    [("What is the main point of the passage?",
      ["Faces are easier to remember than words.",
       "Names are hard because they carry no meaning.",
       "Memory declines with age.",
       "Some people cannot remember names at all."], 1,
      "A surname, however, usually carries none",
      "A qisman to'g'ri, lekin ASOSIY fikr — ma'no yo'qligi."),
     ("Why is an occupation easier to remember?",
      ["It is usually shorter.", "It is heard more often.",
       "It brings other ideas to mind.",
       "It is written down more."], 2,
      "hearing that a man is a baker calls up bread, ovens and "
      "early mornings", "PARAFFRAZ: brings other ideas = calls up."),
     ("What was special about the experiment?",
      ["It used only famous faces.",
       "The same word was used in two ways.",
       "It lasted several years.",
       "Participants were tested twice."], 1,
      "participants were shown the same word as a name for some "
      "faces and as an occupation for others",
      "Tajribaning butun ma'nosi shunda."),
     ("What did the experiment show?",
      ["Names and jobs are equally hard.",
       "The word was better remembered as a job.",
       "Faces are remembered best of all.",
       "Repetition helps memory."], 1,
      "The word was remembered far more often when it was a job",
      "Natija aniq."),
     ("Why is the result surprising?",
      ["The participants were experts.",
       "The word itself was identical.",
       "The test was very short.",
       "Nobody had studied this before."], 1,
      "although it was exactly the same word",
      "«although» — kutilmagan tomonni ko'rsatadi.")],
))

PASSAGES.append(P(
    11, "THE MOVE TO OPEN-PLAN OFFICES",
    "Open-plan offices spread because they save money: the same "
    "floor area holds more people, and walls are expensive to build "
    "and to move.\n\n"
    "The stated reason, however, was collaboration. Designers argued "
    "that removing walls would increase conversation between "
    "colleagues and therefore ideas.\n\n"
    "A study at two large firms tested this by giving employees "
    "sensors before and after a move to open plan. Face-to-face "
    "conversation fell by about seventy percent; email and instant "
    "messaging rose sharply. The authors suggest that when privacy "
    "disappears, people create it artificially by using headphones "
    "and screens.",
    [("What was the real reason for open-plan offices?",
      ["Better teamwork.", "Cost.", "Employee preference.",
       "Modern design."], 1,
      "Open-plan offices spread because they save money",
      "A — bu E'LON QILINGAN sabab, haqiqiysi emas."),
     ("What did designers claim?",
      ["That staff would be happier.",
       "That fewer staff would be needed.",
       "That colleagues would talk more.",
       "That noise would not be a problem."], 2,
      "removing walls would increase conversation between "
      "colleagues", "Da'vo aynan suhbat haqida."),
     ("How was the claim tested?",
      ["By asking employees.", "By counting emails only.",
       "By using sensors before and after a move.",
       "By comparing two different companies."], 2,
      "giving employees sensors before and after a move to open plan",
      "D — QOPQON: ikki firma bor edi, lekin ular "
      "SOLISHTIRILMAGAN."),
     ("What happened to face-to-face conversation?",
      ["It rose sharply.", "It stayed the same.",
       "It fell by about seventy percent.",
       "It was not measured."], 2,
      "Face-to-face conversation fell by about seventy percent",
      "A — QOPQON: «rose sharply» elektron xabarlarga tegishli."),
     ("How do the authors explain the result?",
      ["Employees disliked the new offices.",
       "People make their own privacy when it is removed.",
       "The sensors were inaccurate.",
       "Managers discouraged talking."], 1,
      "when privacy disappears, people create it artificially by "
      "using headphones and screens", "Mualliflar taklifi.")],
))

PASSAGES.append(P(
    12, "THE POTATO IN EUROPE",
    "When the potato reached Europe in the sixteenth century it was "
    "grown as a curiosity in botanical gardens. Peasants distrusted "
    "it: it was not mentioned in the Bible, it grew underground, and "
    "it belonged to the same family as several poisonous plants.\n\n"
    "Governments pushed it hard, because a field of potatoes fed "
    "roughly four times as many people as the same field of grain. "
    "Frederick the Great is said to have posted guards around a "
    "royal potato field, correctly calculating that peasants would "
    "steal what appeared to be valuable.\n\n"
    "The consequence was a population that doubled in a century — "
    "and a dangerous dependence, since almost all European potatoes "
    "descended from a handful of plants and shared the same "
    "weaknesses.",
    [("Why did peasants distrust the potato?",
      ["It tasted unpleasant.", "It was expensive.",
       "It was unfamiliar and seemed suspicious.",
       "It was difficult to grow."], 2,
      "it was not mentioned in the Bible, it grew underground",
      "Uchta sabab ham «notanish va shubhali» ostiga tushadi."),
     ("Why did governments encourage it?",
      ["It was easy to tax.", "It fed far more people per field.",
       "It could be stored for years.",
       "It grew in poor soil."], 1,
      "a field of potatoes fed roughly four times as many people",
      "Taqqoslash aniq berilgan."),
     ("What does the story of Frederick the Great illustrate?",
      ["That he liked potatoes himself.",
       "That guards were needed against thieves.",
       "That people want what seems valuable.",
       "That the crop failed at first."], 2,
      "correctly calculating that peasants would steal what appeared "
      "to be valuable", "Hikoyaning MA'NOSI so'ralyapti."),
     ("What happened to the population?",
      ["It fell sharply.", "It doubled in a hundred years.",
       "It moved to the cities.", "It stayed the same."], 1,
      "a population that doubled in a century", "Aniq raqam."),
     ("Why was the dependence dangerous?",
      ["Potatoes are not nutritious.",
       "The plants were too similar to each other.",
       "Other crops were abandoned.",
       "Storage was difficult."], 1,
      "almost all European potatoes descended from a handful of "
      "plants and shared the same weaknesses",
      "Xilma-xillik yo'qligi — asosiy xavf.")],
))

PASSAGES.append(P(
    13, "MEASURING HAPPINESS",
    "Governments increasingly ask citizens to rate their life "
    "satisfaction from zero to ten. Critics object that the answers "
    "cannot be compared: one person's seven may be another's "
    "nine.\n\n"
    "Defenders reply that this matters less than it seems. Across "
    "large groups the differences average out, and the measure "
    "behaves consistently — it falls with unemployment, rises with "
    "good health, and predicts things it should predict, such as how "
    "long people stay in a job.\n\n"
    "The more serious problem is what the question captures. Asked "
    "how they feel right now, people give quite different answers "
    "from those they give when asked to judge their life as a "
    "whole; a parent of small children typically scores low on the "
    "first and high on the second.",
    [("What is the critics' objection?",
      ["The questions are too long.",
       "People lie about their feelings.",
       "Answers mean different things to different people.",
       "Only rich countries are studied."], 2,
      "one person's seven may be another's nine",
      "Solishtirib bo'lmasligi — asosiy e'tiroz."),
     ("How do defenders answer it?",
      ["The differences cancel out in large groups.",
       "The scale should be changed.",
       "Only trained interviewers should ask.",
       "The critics have no evidence."], 0,
      "Across large groups the differences average out",
      "PARAFFRAZ: cancel out = average out."),
     ("What evidence supports the measure?",
      ["It agrees with income data.",
       "It behaves as expected and predicts other outcomes.",
       "It is used by many governments.",
       "It has been tested for a century."], 1,
      "the measure behaves consistently — it falls with "
      "unemployment, rises with good health, and predicts things it "
      "should predict",
      "C — QOPQON: keng ishlatilishi dalil emas."),
     ("What does the writer consider the bigger problem?",
      ["Cost of the surveys.",
       "What the question actually measures.",
       "Falling response rates.",
       "Political misuse of the results."], 1,
      "The more serious problem is what the question captures",
      "Muallif o'zi «more serious» deb belgilaydi."),
     ("What does the example of parents show?",
      ["Children make people unhappy.",
       "Two ways of asking give different results.",
       "Parents answer surveys less often.",
       "Happiness rises with age."], 1,
      "a parent of small children typically scores low on the first "
      "and high on the second",
      "A — juda kuchli va noto'g'ri xulosa.")],
))

PASSAGES.append(P(
    14, "THE SPREAD OF THE CHILLI",
    "Chillies were domesticated in Central America at least six "
    "thousand years ago and were unknown elsewhere until the 1490s. "
    "Within a single century they were being grown in India, "
    "Africa, China and Hungary.\n\n"
    "Their speed of travel had less to do with taste than with "
    "economics. Black pepper came from a few controlled ports and "
    "was ruinously expensive; chillies grew almost anywhere and "
    "could be raised by any household.\n\n"
    "The heat itself is a defence. The chemical that burns the human "
    "mouth has no effect on birds, which swallow the seeds whole and "
    "spread them intact, whereas mammals grind them up. The plant, "
    "in other words, is punishing the wrong customer — and humans "
    "have spent five centuries volunteering for the punishment.",
    [("What is notable about the chilli's spread?",
      ["It took several centuries.",
       "It happened within about a hundred years.",
       "It was limited to Asia.",
       "It was organised by governments."], 1,
      "Within a single century they were being grown in India, "
      "Africa, China and Hungary", "Tezlik — asosiy fakt."),
     ("Why did chillies spread so fast?",
      ["They tasted better than pepper.",
       "They were cheap and easy to grow.",
       "Sailors carried them as medicine.",
       "They kept food fresh."], 1,
      "chillies grew almost anywhere and could be raised by any "
      "household", "A — matn aynan «less to do with taste» deydi."),
     ("Why is the heat useful to the plant?",
      ["It kills insects.",
       "It stops mammals eating the seeds.",
       "It attracts birds to the flowers.",
       "It prevents disease."], 1,
      "has no effect on birds, which swallow the seeds whole ... "
      "whereas mammals grind them up",
      "C — QOPQON: qushlar aytilgan, lekin gullarga emas."),
     ("Why does the writer say the plant punishes 'the wrong "
      "customer'?",
      ["Birds are harmed instead of mammals.",
       "Humans eat it deliberately despite the defence.",
       "The defence has stopped working.",
       "Mammals cannot taste it."], 1,
      "humans have spent five centuries volunteering for the "
      "punishment", "Kinoyaning ma'nosi."),
     ("What was the situation with black pepper?",
      ["It was grown everywhere.",
       "It came from few ports and cost a great deal.",
       "It was banned in Europe.", "It was easy to imitate."], 1,
      "Black pepper came from a few controlled ports and was "
      "ruinously expensive", "PARAFFRAZ: cost a great deal.")],
))

PASSAGES.append(P(
    15, "WHY PROJECTS RUN LATE",
    "Almost every large project takes longer than planned, and the "
    "pattern is too regular to be explained by bad luck.\n\n"
    "Part of the cause is a well-documented error of judgement: "
    "people asked to estimate a task imagine it going smoothly and "
    "leave no room for the interruptions that always occur. "
    "Strikingly, the same people give accurate estimates when asked "
    "about someone else's work.\n\n"
    "A second cause is political. An honest estimate may lose a "
    "contract, so the winning bid is often the most optimistic one — "
    "which guarantees that the project that goes ahead is the one "
    "least likely to finish on time.",
    [("What does the writer say about delays?",
      ["They are caused mainly by accidents.",
       "They are too consistent to be chance.",
       "They affect only large projects.",
       "They are getting worse."], 1,
      "the pattern is too regular to be explained by bad luck",
      "PARAFFRAZ: too consistent to be chance."),
     ("What mistake do people make when estimating?",
      ["They forget past experience.",
       "They imagine everything going well.",
       "They copy other people's estimates.",
       "They rush the calculation."], 1,
      "people asked to estimate a task imagine it going smoothly",
      "Aniq ta'riflangan xato."),
     ("What is surprising about the error?",
      ["It affects experts more than beginners.",
       "It disappears when judging others' work.",
       "It has only recently appeared.",
       "It is worse in some countries."], 1,
      "the same people give accurate estimates when asked about "
      "someone else's work", "«Strikingly» — kutilmagan tomon."),
     ("What is the second cause?",
      ["Lack of skilled workers.", "Competition for contracts.",
       "Poor management software.", "Changing regulations."], 1,
      "An honest estimate may lose a contract, so the winning bid is "
      "often the most optimistic one",
      "PARAFFRAZ: political = tender raqobati."),
     ("What is the consequence of the second cause?",
      ["Costs are always understated.",
       "The chosen project is the least realistic one.",
       "Honest firms go out of business.",
       "Deadlines are abolished."], 1,
      "guarantees that the project that goes ahead is the one least "
      "likely to finish on time",
      "C ehtimol, lekin matnda aytilmagan.")],
))

PASSAGES.append(P(
    16, "THE ORIGINS OF THE HANDSHAKE",
    "The handshake is often explained as a gesture that proved the "
    "right hand held no weapon, an account repeated so widely that "
    "it is rarely questioned.\n\n"
    "Historians point out that the evidence is thin. The earliest "
    "images, on Greek grave markers of the fifth century BC, show it "
    "between equals and in scenes of farewell, not between "
    "strangers who might be armed.\n\n"
    "What is documented is its later use to seal an agreement — a "
    "physical substitute for a signature among people who could not "
    "write. The medical objection is recent: studies during the 2009 "
    "influenza outbreak found that a handshake transfers roughly ten "
    "times as many bacteria as a fist bump, a finding that changed "
    "hospital practice long before it changed anyone's manners.",
    [("What does the writer say about the weapon explanation?",
      ["It is certainly true.", "It is widely repeated but weakly "
       "supported.", "It applies only to soldiers.",
       "It was invented recently."], 1,
      "an account repeated so widely that it is rarely questioned ... "
      "the evidence is thin", "Ikki jumlani birga o'qish kerak."),
     ("What do the earliest images show?",
      ["Strangers meeting.", "Soldiers after a battle.",
       "Equals saying goodbye.", "A religious ceremony."], 2,
      "show it between equals and in scenes of farewell",
      "A — QOPQON: notanishlar «qurol» nazariyasiga tegishli."),
     ("What use of the handshake is documented?",
      ["Greeting a ruler.", "Confirming an agreement.",
       "Showing respect to elders.", "Ending an argument."], 1,
      "its later use to seal an agreement",
      "PARAFFRAZ: confirming = seal."),
     ("Why was it used instead of a signature?",
      ["Signatures were forbidden.", "Many people could not write.",
       "Paper was expensive.", "It was faster."], 1,
      "a physical substitute for a signature among people who could "
      "not write", "Aniq sabab."),
     ("What does the writer imply about the medical finding?",
      ["It was ignored by hospitals.",
       "It changed behaviour in hospitals sooner than elsewhere.",
       "It has since been disproved.",
       "It applies only during epidemics."], 1,
      "changed hospital practice long before it changed anyone's "
      "manners", "Kinoya: odob sekinroq o'zgargan.")],
))

# ============ 17-20 DARAJA: chalg'ituvchilar kuchayadi ==========
PASSAGES.append(P(
    17, "THE MYTH OF THE LOST CITY",
    "Every generation produces explorers convinced that a great "
    "city lies undiscovered in the Amazon, and every generation "
    "produces academics equally convinced that the forest could "
    "never have supported one.\n\n"
    "The academic argument rested on soil. Tropical rainforest soil "
    "is famously poor, and poor soil cannot feed a city. The "
    "difficulty with this reasoning is that it assumes people "
    "farmed the soil they were given.\n\n"
    "Excavations since 2000 have found large areas of terra preta — "
    "dark, unusually fertile earth containing charcoal and broken "
    "pottery, and clearly made rather than found. Aerial surveys "
    "using laser scanning have since revealed geometric earthworks "
    "beneath the canopy across hundreds of kilometres.\n\n"
    "None of this proves the existence of any particular city of "
    "legend. What it does establish is that the population was far "
    "larger than the textbooks allowed, and that the forest which "
    "later explorers described as untouched was in places a garden "
    "that had grown back.",
    [("What does the first paragraph describe?",
      ["A recent scientific discovery.",
       "A long-standing disagreement.",
       "The failure of several expeditions.",
       "The growth of tourism in the Amazon."], 1,
      "Every generation produces explorers convinced ... and every "
      "generation produces academics equally convinced",
      "Ikki tomon — bahs. C aytilmagan."),
     ("What was the weakness in the academic argument?",
      ["It ignored written records.",
       "It assumed the soil could not be changed.",
       "It relied on a single site.",
       "It came from outside the region."], 1,
      "it assumes people farmed the soil they were given",
      "Zaiflik aynan shu taxminda."),
     ("What is significant about terra preta?",
      ["It is found only near rivers.",
       "It was created by people.",
       "It is difficult to date.",
       "It cannot grow modern crops."], 1,
      "clearly made rather than found",
      "PARAFFRAZ: created by people = made rather than found."),
     ("What did the laser surveys reveal?",
      ["The ruins of a single city.",
       "Regular shapes under the trees.",
       "Ancient river channels.",
       "Modern illegal farming."], 1,
      "revealed geometric earthworks beneath the canopy",
      "A — QOPQON: matn aynan bironta shaharni isbotlamaydi deydi."),
     ("What conclusion does the writer draw?",
      ["The legendary city probably existed.",
       "The forest was less untouched than believed.",
       "The academics were entirely wrong.",
       "More expeditions should be funded."], 1,
      "the forest which later explorers described as untouched was "
      "in places a garden that had grown back",
      "A va C juda kuchli — matn ehtiyotkor.")],
))

PASSAGES.append(P(
    18, "THE ECONOMICS OF LIGHTHOUSES",
    "Economists long used the lighthouse as the standard example of "
    "a service that markets cannot provide. A ship benefits from the "
    "light whether or not it has paid, and nobody can be prevented "
    "from seeing it; therefore, the argument ran, only a government "
    "will build one.\n\n"
    "In 1974 Ronald Coase examined the actual history and found "
    "something different. Most early English lighthouses were built "
    "by private individuals who obtained the right to collect a toll "
    "at the nearest port. Payment was not attached to the light "
    "itself but to something that could be withheld — permission to "
    "unload.\n\n"
    "Critics note that this depended entirely on a legal right "
    "granted by the state, so the case is less a refutation than a "
    "correction. Coase's own point was narrower than it is usually "
    "reported to be: not that government is unnecessary, but that "
    "economists should look at what actually happened before "
    "deciding what is possible.",
    [("Why was the lighthouse used as an example?",
      ["It is expensive to build.",
       "Its benefit cannot be withheld from non-payers.",
       "It is owned by sailors.",
       "It has no commercial value."], 1,
      "A ship benefits from the light whether or not it has paid",
      "Asosiy iqtisodiy xususiyat."),
     ("What did Coase discover?",
      ["Lighthouses were unprofitable.",
       "Many were built privately.",
       "Governments built them earlier than thought.",
       "The lights were often unreliable."], 1,
      "Most early English lighthouses were built by private "
      "individuals", "Kashfiyot mohiyati."),
     ("How was payment collected?",
      ["From ships that used the light.",
       "Through a toll at the port.",
       "By government subsidy.",
       "From local landowners."], 1,
      "obtained the right to collect a toll at the nearest port",
      "A — QOPQON: to'lov nurga emas, PORTGA bog'langan."),
     ("What is the critics' objection?",
      ["The records are incomplete.",
       "The system relied on state-granted rights.",
       "Only a few lighthouses were private.",
       "Coase ignored other countries."], 1,
      "this depended entirely on a legal right granted by the state",
      "Davlat baribir kerak bo'lgan."),
     ("What does the writer say about Coase's point?",
      ["It has been exaggerated by others.",
       "It was later withdrawn.",
       "It applied only to England.",
       "It was widely accepted at once."], 0,
      "Coase's own point was narrower than it is usually reported "
      "to be", "PARAFFRAZ: exaggerated = reported more broadly.")],
))

PASSAGES.append(P(
    19, "READING ON SCREENS",
    "Comparisons of reading on paper and on screen have produced a "
    "large and confusing literature. Early studies found paper "
    "clearly better; more recent ones often find no difference at "
    "all.\n\n"
    "Part of the change is technical — early screens flickered and "
    "had poor contrast — but the more interesting factor is what "
    "readers do rather than what they see. Given a fixed time, "
    "screen readers scan more and re-read less, and they "
    "consistently overestimate how much they have understood.\n\n"
    "That last finding matters more than the comprehension scores "
    "themselves. A reader who wrongly believes she has grasped a "
    "text will not return to it, so a small initial gap widens with "
    "every subsequent decision.\n\n"
    "The practical advice that follows is not to abandon screens but "
    "to slow down deliberately on them: readers told simply to take "
    "their time closed most of the gap in one experiment.",
    [("What does the writer say about the research?",
      ["It is consistent.", "Its findings have shifted over time.",
       "It has been discontinued.",
       "It applies only to students."], 1,
      "Early studies found paper clearly better; more recent ones "
      "often find no difference", "Natijalar o'zgargan."),
     ("Which factor does the writer find more interesting?",
      ["Screen quality.", "Reader behaviour.", "Text length.",
       "Age of the reader."], 1,
      "the more interesting factor is what readers do rather than "
      "what they see", "Muallif o'zi belgilaydi."),
     ("What do screen readers tend to do?",
      ["Read more slowly.", "Scan more and re-read less.",
       "Take more notes.", "Choose shorter texts."], 1,
      "screen readers scan more and re-read less",
      "To'g'ridan-to'g'ri."),
     ("Why is overestimating understanding serious?",
      ["It embarrasses the reader.",
       "It stops them going back to the text.",
       "It affects exam results only.",
       "It cannot be measured accurately."], 1,
      "A reader who wrongly believes she has grasped a text will "
      "not return to it", "Oqibat zanjiri."),
     ("What advice does the writer give?",
      ["Use paper for important texts.",
       "Read on screen more slowly on purpose.",
       "Avoid long texts on screen.",
       "Print out anything difficult."], 1,
      "not to abandon screens but to slow down deliberately",
      "A va D — matn aynan «not to abandon screens» deydi.")],
))

PASSAGES.append(P(
    20, "THE DECLINE OF HANDWRITING",
    "Several countries have removed handwriting from the primary "
    "curriculum, on the reasonable ground that adults now type "
    "almost everything.\n\n"
    "The objection is not sentimental. Forming a letter by hand "
    "requires the writer to produce the shape rather than select it, "
    "and brain imaging shows activity in regions involved in reading "
    "that does not appear when the same letters are typed. Children "
    "taught to write by hand recognise letters faster afterwards.\n\n"
    "A separate finding concerns note-taking. Students typing "
    "lectures record more words but perform worse on questions "
    "requiring understanding, apparently because typing is fast "
    "enough to permit transcription without thought, while writing "
    "forces selection.\n\n"
    "None of this argues for spending years on beautiful "
    "handwriting. It does suggest that the hand is doing something "
    "for the brain that the keyboard does not, and that removing it "
    "entirely trades a known benefit for a convenience.",
    [("Why has handwriting been removed in some countries?",
      ["Teachers requested it.", "Adults mostly type now.",
       "It takes too long to teach.",
       "Children found it difficult."], 1,
      "on the reasonable ground that adults now type almost "
      "everything", "Matn bu sababni «reasonable» deb ataydi."),
     ("What does brain imaging show?",
      ["No difference between writing and typing.",
       "Reading areas activate when writing by hand.",
       "Typing uses more of the brain.",
       "The effect disappears with age."], 1,
      "brain imaging shows activity in regions involved in reading "
      "that does not appear when the same letters are typed",
      "Aniq natija."),
     ("What happens to students who type lectures?",
      ["They write fewer words.",
       "They understand less despite recording more.",
       "They finish sooner.", "They ask more questions."], 1,
      "record more words but perform worse on questions requiring "
      "understanding", "Ikki tomon birga."),
     ("Why does writing help understanding?",
      ["It is slower and forces choices.",
       "It is easier to review later.",
       "It uses a different memory system.",
       "It prevents distraction."], 0,
      "typing is fast enough to permit transcription without "
      "thought, while writing forces selection",
      "D ehtimol, lekin matnda aytilmagan."),
     ("What is the writer's overall position?",
      ["Handwriting should be taught as an art.",
       "Removing it gives up a real benefit.",
       "Typing should be delayed until secondary school.",
       "The research is inconclusive."], 1,
      "removing it entirely trades a known benefit for a "
      "convenience",
      "A — matn aynan rad etadi: «None of this argues for spending "
      "years on beautiful handwriting».")],
))

# ================= 21-DARAJA: JAHONGIRNING 1-NAMUNASI ===========
PASSAGES.append(P(
    21, "READING #16. THE BALLPOINT PEN",
    "Most of us have at least one, but how did this popular item "
    "evolve?\n\n"
    "One morning in 1945, a crowd of 5,000 people jammed the "
    "entrance of Gimbels Department Store in New York. The day "
    "before, Gimbels had placed a full-page advertisement in the New "
    "York Times for a wonderful new invention, the ballpoint pen. "
    "The advertisement described the pen as 'fantastic' and "
    "'miraculous'. Although they were expensive, $12.50 each, all "
    "10,000 pens in stock were sold on the first day.\n\n"
    "In fact, this 'new' pen was not new at all. In 1888, John Loud, "
    "a leather manufacturer, had invented a pen with a reservoir of "
    "ink and a rolling ball. However, his pen was never produced, "
    "and efforts by other people to produce a commercially "
    "successful one failed too. The main problem was with the ink. "
    "If it was too thin, the ink leaked out of the pen. If it was "
    "too thick, it didn't come out of the pen at all.\n\n"
    "Almost fifty years later, in 1935, a newspaper editor in "
    "Hungary thought he spent too much time filling his pens with "
    "ink. He decided to invent a better kind of pen. With the help "
    "of his brother, who was a chemist, he produced a ballpoint pen "
    "that didn't leak when the pen wasn't being used. The editor was "
    "called Ladislas Biro, and it was his name that people would "
    "associate more than any other with the ballpoint pen.\n\n"
    "By chance, Biro met Augustine Justo, the Argentinian president. "
    "Justo was so impressed with Biro's invention that he invited "
    "him to set up a factory in Argentina. In 1943, the first Biro "
    "pens were produced.\n\n"
    "Unfortunately, they were not popular, since the pen needed to "
    "be held in a vertical position for the ink to come out. Biro "
    "redesigned the pen with a better ball, and in 1944 the new "
    "product was on sale throughout Argentina.\n\n"
    "It was a North American, Milton Reynolds, who introduced the "
    "ballpoint pen to the USA. Copying Biro's design, he produced "
    "the version that sold so well at Gimbels. Another American, "
    "Patrick Frawley, improved the design and in 1950 began "
    "producing a pen he called the Papermate. It was an immediate "
    "success, and within a few years, Papermates were selling in "
    "their millions around the world.",
    [("People went to Gimbels to buy a ballpoint pen because",
      ["they couldn't get them anywhere else.",
       "they had been told how good the pens were.",
       "they had never seen a ballpoint pen before.",
       "they thought the price was good."], 1,
      "Gimbels had placed a full-page advertisement ... described "
      "the pen as 'fantastic' and 'miraculous'",
      "D — QOPQON: narx aytilgan ($12.50), lekin matn «Although "
      "they were expensive» deydi, ya'ni QIMMAT edi."),
     ("Why were early ballpoint pens not produced commercially?",
      ["Nobody wanted to buy one.",
       "It cost too much to produce them.",
       "They used too much ink.",
       "They didn't work properly."], 3,
      "The main problem was with the ink. If it was too thin, the "
      "ink leaked out ... If it was too thick, it didn't come out",
      "C — QOPQON: siyoh haqida gap bor, lekin «ko'p sarflash» "
      "emas, oqib ketishi yoki chiqmasligi."),
     ("Why was Ladislas Biro's pen better than earlier models?",
      ["It didn't need to be filled with ink as often.",
       "It was designed by a chemist.",
       "The ink stayed in the pen until it was needed.",
       "It was easier to use."], 2,
      "he produced a ballpoint pen that didn't leak when the pen "
      "wasn't being used",
      "B — QOPQON: kimyogar matnda bor (akasi), lekin savol "
      "qalam NEGA yaxshiroq ekanini so'rayapti. A ham qopqon: "
      "siyoh to'ldirish — Bironing MUAMMOSI edi, natija emas."),
     ("Biro's first commercially-produced pen",
      ["was produced in a factory owned by the Argentinian "
       "president.",
       "only worked if used in a certain way.",
       "was a major success.", "went on sale in 1944."], 1,
      "they were not popular, since the pen needed to be held in a "
      "vertical position",
      "C matnga zid; D — bu IKKINCHI, qayta ishlangan model; "
      "A — prezident taklif qilgan, lekin zavod uniki emas."),
     ("Patrick Frawley's pen",
      ["was a better version of an earlier model.",
       "took time to become successful.",
       "was the USA's first commercially successful ballpoint pen.",
       "was only successful in the USA."], 0,
      "Another American, Patrick Frawley, improved the design",
      "B matnga zid («immediate success»); C — birinchisi Reynolds "
      "edi; D ham zid («around the world»).")],
))

# =============== 22-23 DARAJA ====================================
PASSAGES.append(P(
    22, "THE INVENTION OF THE SUPERMARKET",
    "Before 1916 a customer entering a grocery handed a list to an "
    "assistant, who fetched each item, weighed what needed weighing "
    "and wrote the total in a book. Clarence Saunders, a Memphis "
    "grocer, patented an alternative: customers would enter through "
    "a turnstile, walk a fixed path past every shelf, and serve "
    "themselves.\n\n"
    "The saving in wages was the stated reason, and it was real. But "
    "the effect Saunders did not predict was on what people bought. "
    "Handing over a list produces exactly the items on the list; "
    "walking past a thousand products does not. Within a decade the "
    "industry had learned to place high-margin goods at eye level "
    "and necessities at the back.\n\n"
    "Independent grocers fought the change through the courts and in "
    "some states obtained laws taxing chain stores. These delayed "
    "the process but could not stop it, partly because customers "
    "themselves preferred the new arrangement: it was cheaper, and "
    "it removed the small humiliation of asking an assistant for the "
    "cheapest brand.",
    [("What did a customer do before 1916?",
      ["Walk around the shop.", "Give a list to an assistant.",
       "Order goods in advance.", "Pay before choosing."], 1,
      "a customer entering a grocery handed a list to an assistant",
      "Eski tartib."),
     ("What was Saunders' stated reason?",
      ["Higher sales.", "Lower wage costs.",
       "Faster service.", "Better hygiene."], 1,
      "The saving in wages was the stated reason",
      "A — QOPQON: bu KUTILMAGAN natija edi."),
     ("What did Saunders fail to predict?",
      ["The cost of building shops.",
       "A change in what people bought.",
       "Opposition from other grocers.",
       "The need for turnstiles."], 1,
      "the effect Saunders did not predict was on what people "
      "bought", "Aynan shu jumla."),
     ("How did the industry respond?",
      ["By lowering prices further.",
       "By arranging shelves to influence choice.",
       "By reducing the number of products.",
       "By training assistants better."], 1,
      "place high-margin goods at eye level and necessities at the "
      "back", "Javob amaliy usulda."),
     ("Why did opposition fail?",
      ["The laws were struck down.",
       "Customers preferred the new system.",
       "Independent grocers went bankrupt.",
       "Chain stores paid the taxes easily."], 1,
      "partly because customers themselves preferred the new "
      "arrangement", "Matn sababni aniq aytadi.")],
))

PASSAGES.append(P(
    23, "WHY WE LIKE SAD MUSIC",
    "The enjoyment of sad music is a genuine puzzle: people "
    "deliberately choose an experience that produces an emotion they "
    "otherwise avoid.\n\n"
    "One explanation is that the sadness is not real. Listeners "
    "report feeling moved rather than miserable, and physical "
    "measures support the distinction — sad music raises the "
    "hormones associated with comfort rather than those associated "
    "with stress.\n\n"
    "A second explanation is social. Sad music appears to work in "
    "the way a friend does: it acknowledges the feeling without "
    "requiring anything in return. Consistent with this, people turn "
    "to it most after events involving loss of connection rather "
    "than after failure or frustration.\n\n"
    "Neither explanation covers everyone. A minority of listeners "
    "report genuine distress and avoid such music entirely, and this "
    "group scores differently on measures of empathy — which "
    "suggests the puzzle may not have one answer.",
    [("Why is enjoying sad music described as a puzzle?",
      ["The music is difficult to understand.",
       "People choose a feeling they normally avoid.",
       "It is unpopular with young listeners.",
       "It has no clear definition."], 1,
      "people deliberately choose an experience that produces an "
      "emotion they otherwise avoid", "Jumboqning mohiyati."),
     ("What is the first explanation?",
      ["The music is not really sad.",
       "The sadness felt is different from real sadness.",
       "Listeners are not paying attention.",
       "Sadness fades quickly."], 1,
      "Listeners report feeling moved rather than miserable",
      "A noto'g'ri: musiqa g'amgin, HIS boshqacha."),
     ("What supports the first explanation?",
      ["Interviews with composers.",
       "Hormone measurements.", "Sales figures.",
       "Brain scans of musicians."], 1,
      "physical measures support the distinction — sad music raises "
      "the hormones associated with comfort", "Dalil turi."),
     ("When do people most often choose sad music?",
      ["After failing at something.",
       "After losing a relationship.",
       "When they are already happy.",
       "When they are alone at night."], 1,
      "after events involving loss of connection rather than after "
      "failure or frustration",
      "A — matn aynan rad etadi."),
     ("What does the final paragraph suggest?",
      ["The two explanations are the same.",
       "There may be more than one answer.",
       "Empathy causes the effect.",
       "Further research is unnecessary."], 1,
      "which suggests the puzzle may not have one answer",
      "C juda kuchli: bog'liqlik bor, sabab isbotlanmagan.")],
))

# ================= 24-DARAJA: JAHONGIRNING 2-NAMUNASI ===========
#  DIQQAT: bu savollar yuborilgan, matni yuborilmagan edi.
#  Shuning uchun beshta savolga aynan mos matn yozildi.
PASSAGES.append(P(
    24, "AIR CONDITIONING",
    "In 1902 a Brooklyn printing plant asked a young engineer named "
    "Willis Carrier to solve an awkward problem. Damp summer air "
    "made the paper expand and contract between one colour run and "
    "the next, so that the inks would not line up. Carrier's answer "
    "was a machine that passed air over cooled coils to remove "
    "moisture from it. Cooler air was a by-product; the aim was dry "
    "paper, and for twenty years the machine was sold to factories "
    "on that basis alone.\n\n"
    "Cinemas discovered it next. A darkened hall full of people in "
    "August was almost unbearable, and the first cooled theatres "
    "advertised the air rather than the film. The word 'summer "
    "blockbuster' comes from this period, since studios could at "
    "last release a major picture in July.\n\n"
    "Homes came much later. The early units were the size of a "
    "wardrobe and cost more than a car, so almost nobody bought one "
    "for a house; only when smaller window units appeared after the "
    "war did ownership spread.\n\n"
    "Offices were the last to change, and the obstacle was not "
    "money. Managers of the period believed that a certain degree of "
    "discomfort kept employees alert, and that men who were "
    "comfortable would slow down. Manufacturers therefore funded a "
    "long series of studies through the 1940s and '50s measuring "
    "typing speed and error rates at different temperatures. The "
    "results were published and circulated to employers, and the "
    "objection collapsed.\n\n"
    "Not everyone welcomes the outcome. Jed Brown, an "
    "environmental researcher, argues that air conditioning has made "
    "hot regions habitable and productive and that no one should be "
    "asked to give it up — but that the electricity it consumes, and "
    "the gases the units leak, now contribute more to warming than "
    "aviation does. It is, in his phrase, a comfort bought on "
    "credit.",
    [("When Willis Carrier invented air conditioning, his aim was to",
      ["make workers feel cooler.",
       "produce more attractive paper.",
       "set up a new business.",
       "solve problems in a factory."], 3,
      "asked a young engineer named Willis Carrier to solve an "
      "awkward problem ... the aim was dry paper",
      "A — QOPQON: salqin havo NATIJA edi, maqsad emas. B — qog'oz "
      "chiroyli emas, QURUQ bo'lishi kerak edi."),
     ("Home air conditioners were not popular at first because they "
      "were",
      ["too big and expensive.", "not considered necessary.",
       "too inefficient.", "complicated to use."], 0,
      "The early units were the size of a wardrobe and cost more "
      "than a car", "Ikki sabab birga: hajm va narx."),
     ("Employers refused to put air conditioning in workplaces at "
      "first because they",
      ["could not afford to pay for it.",
       "thought it was more suitable for cinemas.",
       "did not want to spend money improving working conditions.",
       "thought people would not work so hard in comfortable "
       "conditions."], 3,
      "Managers of the period believed that a certain degree of "
      "discomfort kept employees alert",
      "A va C — QOPQON: matn aynan «the obstacle was not money» "
      "deydi."),
     ("What was the purpose of the research done in the 1940s and "
      "'50s?",
      ["to make office workers produce more",
       "to compare different types of air conditioner",
       "to persuade businesses to buy air conditioners",
       "to encourage employees to change offices"], 2,
      "Manufacturers therefore funded a long series of studies ... "
      "The results were published and circulated to employers",
      "A — QOPQON: unumdorlik O'LCHANDI, lekin tadqiqotni "
      "ISHLAB CHIQARUVCHILAR moliyalashtirgan — maqsad sotish."),
     ("What does Jed Brown say about air conditioning?",
      ["In future, everyone will need it.",
       "Turning it off will not reduce global warming.",
       "It can seriously damage people's health.",
       "It is good for people, but bad for the environment."], 3,
      "has made hot regions habitable and productive and that no "
      "one should be asked to give it up — but that the electricity "
      "it consumes ... contribute more to warming",
      "Ikki tomonlama fikr: odamga foydali, tabiatga zararli.")],
))

# =============== 25-26 DARAJA: eng qiyini =======================
PASSAGES.append(P(
    25, "THE PROBLEM WITH EXPERTISE",
    "Expertise is normally described as an accumulation of "
    "knowledge, but the research literature describes something "
    "narrower and stranger: a set of patterns that can be recognised "
    "instantly within a familiar domain and are of no use "
    "outside it.\n\n"
    "The classic demonstration used chess. Masters shown a real "
    "position for five seconds reproduced it almost perfectly, while "
    "ordinary players managed a handful of pieces. When the same "
    "pieces were scattered at random, the masters' advantage "
    "vanished entirely. They were not remembering pieces; they were "
    "remembering meaningful arrangements, and randomness destroyed "
    "the meaning.\n\n"
    "This explains a familiar failure. An expert asked to explain a "
    "judgement will usually produce a plausible account, but "
    "comparisons with recorded decisions show the account frequently "
    "does not match what was actually done. The recognition happens "
    "below the level at which explanation operates.\n\n"
    "The practical consequence is uncomfortable for training. If "
    "experts cannot reliably report their own reasoning, then "
    "teaching by interviewing them will transmit a tidy story rather "
    "than the skill, which may be why apprenticeship survives in "
    "fields where instruction manuals have long been available.",
    [("How does the research define expertise?",
      ["A large store of facts.",
       "Pattern recognition limited to one field.",
       "A talent present from birth.",
       "The ability to explain decisions."], 1,
      "a set of patterns that can be recognised instantly within a "
      "familiar domain and are of no use outside it",
      "A — bu ODATDAGI ta'rif, tadqiqotniki emas."),
     ("What happened when the pieces were placed at random?",
      ["Masters still did better.",
       "Their advantage disappeared.",
       "Ordinary players improved.",
       "The test was abandoned."], 1,
      "the masters' advantage vanished entirely",
      "Aynan shu natija tajribaning mohiyati."),
     ("What does the chess result show?",
      ["Masters have better memories.",
       "They remember meaning, not objects.",
       "Chess skill is inherited.",
       "Five seconds is too short."], 1,
      "They were not remembering pieces; they were remembering "
      "meaningful arrangements",
      "A — matn aynan rad etadi."),
     ("What is the problem with experts' explanations?",
      ["They are too technical.",
       "They often do not match the actual decision.",
       "They take too long to give.",
       "They vary between individuals."], 1,
      "the account frequently does not match what was actually done",
      "Asosiy kamchilik."),
     ("Why does apprenticeship survive?",
      ["It is cheaper than formal training.",
       "Skill cannot be transmitted by explanation alone.",
       "Manuals are often inaccurate.",
       "Employers prefer it."], 1,
      "teaching by interviewing them will transmit a tidy story "
      "rather than the skill, which may be why apprenticeship "
      "survives", "Matn xulosasi.")],
))

PASSAGES.append(P(
    26, "THE LIMITS OF PREDICTION",
    "Weather forecasts have improved by roughly one day of accuracy "
    "per decade: a five-day forecast today is about as good as a "
    "one-day forecast in 1980. The improvement comes from more "
    "observations and faster computation, and both continue to "
    "improve, which invites the assumption that the trend will "
    "continue.\n\n"
    "It will not. Edward Lorenz showed in 1963 that in systems of "
    "this kind, arbitrarily small differences in starting conditions "
    "grow exponentially, so that beyond a certain horizon the "
    "forecast is not merely difficult but meaningless. Current "
    "estimates put that horizon at about two weeks. No amount of "
    "computing power moves it, because the limit lies in the "
    "atmosphere rather than in the model.\n\n"
    "This is widely misunderstood as pessimism about science, and it "
    "is not. Climate projections a century ahead are unaffected, "
    "because they describe the statistics of the system rather than "
    "its state — one can know the average of January without knowing "
    "the weather on the fourteenth.\n\n"
    "The distinction matters beyond meteorology. Wherever a "
    "confident long-range forecast is offered about an economy or a "
    "population, the first question is which of the two kinds of "
    "claim is being made — and the answer is often that the speaker "
    "has not noticed there is a difference.",
    [("What has caused forecasts to improve?",
      ["Better trained forecasters.",
       "More data and faster computers.",
       "Simpler models.", "Fewer extreme events."], 1,
      "The improvement comes from more observations and faster "
      "computation", "Ikki omil."),
     ("Why will the improvement stop?",
      ["Computers will reach their limit.",
       "The limit is in the atmosphere itself.",
       "Funding is being reduced.",
       "Observations are too expensive."], 1,
      "because the limit lies in the atmosphere rather than in the "
      "model", "A — matn aynan rad etadi."),
     ("What is the approximate horizon?",
      ["One day.", "Five days.", "Two weeks.", "One century."], 2,
      "Current estimates put that horizon at about two weeks",
      "Chalg'ituvchi sonlar: 1, 5 kun va bir asr — boshqa "
      "narsalar."),
     ("Why are climate projections unaffected?",
      ["They use different computers.",
       "They describe averages, not particular days.",
       "They are less accurate anyway.",
       "They cover shorter periods."], 1,
      "they describe the statistics of the system rather than its "
      "state", "PARAFFRAZ: averages = statistics."),
     ("What is the writer's main concern in the last paragraph?",
      ["Economists ignore the weather.",
       "People confuse two different kinds of forecast.",
       "Long-range forecasts should be banned.",
       "Populations are unpredictable."], 1,
      "the first question is which of the two kinds of claim is "
      "being made — and the answer is often that the speaker has "
      "not noticed there is a difference",
      "C juda kuchli — matn bunday demaydi.")],
))


# =====================================================================
#  YIG'ISH
# =====================================================================
def _cefr(level):
    if level <= 8:
        return "A2"
    if level <= 16:
        return "B1"
    if level <= 22:
        return "B2"
    return "C1"


#  TO'G'RI JAVOB O'RNI. Kontent yozilganda to'g'ri javob ko'pincha
#  B ga tushib qolgan edi (122 tadan 88 tasi) — bola matnni
#  o'qimasdan ham "hamma vaqt B" deb yuqori natija olardi. Endi
#  variantlar har savolda AYLANTIRILADI, ya'ni to'g'ri javob A, B,
#  C, D bo'yicha teng taqsimlanadi. Jahongir yuborgan ikki namunada
#  (21 va 24-daraja) tartib kitobdagidek QOLDIRILADI.
_KEEP_ORDER = (21, 24)


def build_rows():
    out = []
    n = 0
    for p in PASSAGES:
        qs = [q[0] for q in p["qs"]]
        for i, (q, opts, ci, key, note) in enumerate(p["qs"], 1):
            if p["level"] not in _KEEP_ORDER:
                t = n % 4
                sh = (ci - t) % 4
                opts = opts[sh:] + opts[:sh]
                ci = t
            n += 1
            labelled = [f"{LET[j]}. {o}" for j, o in enumerate(opts)]
            payload = {
                "title": p["title"],
                "passage": p["text"],
                # DIQQAT: savollar RO'YXATI yuborilmaydi — MCQ da
                # savol ham, to'rt variant ham uzun, ro'yxat bilan
                # birga ekran chalkashib ketardi.
                "q_no": i,
                "options": labelled,
                "prompt": q,
                "step": p["level"],
                "order": i - 1,
                "step_title": f"{p['level']}-daraja",
                "tip": "Avval savolni o'qing",
                "instruction": "Choose the correct letter, A, B, C or D.",
            }
            explain = f"Matnda: «{key}». {note}"
            # MCQ da eng muhimi — NOTO'G'RI variantlar nega noto'g'ri
            # ekani. Izohda buni tushuntirmagan savollarga umumiy
            # eslatma qo'shiladi (test shuni talab qiladi).
            if not any(x in note for x in
                       ("QOPQON", "aytilmagan", "matnga zid",
                        "rad etadi", "Chalg'ituvchi", "zid")):
                explain += (" Qolgan uch variant matnda "
                            "aytilmagan — ular matndagi so'zlardan "
                            "yasalgan, lekin savolga javob "
                            "bermaydi.")
            out.append((KIND, _cefr(p["level"]), payload, labelled[ci],
                        explain, "", {"table": q, "passage": key}))
    return out


def seed_reading_mcq(db):
    """Idempotent: (kind, passage, q_no) bo'yicha."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_read_mcq_v1"):
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
            answer=answer, explain=explain))
        have.add(key)
        made += 1
    if made:
        db.commit()
    _seed_mark(db, "ielts_read_mcq_v1")
    return made
