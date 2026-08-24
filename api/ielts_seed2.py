# -*- coding: utf-8 -*-
"""IELTS LISTENING — 2-BLOK: MA'LUMOT ILIB OLISH VA TUZOQLAR
(2026-08-24).

Jahongir: "keyingi listeninglarda hafta kunlari, soat nechidaligi,
qancha vaqt davom etishi, nechi km yurishi, shunga oxshash narsalar
practice bolsin bunda 100ta bolsa yetadi. Keyingisi... multiple
answer trapi uchun alohida qism qilib... bir emas 2-3ta mos javob
aytib chalgitish mashqidan 100ta bolsin".

IKKI MASHQ:

  ielts_detail (4-mashq) — MA'LUMOT ILIB OLISH.
    Qisqa dialog eshittiriladi, bitta aniq narsa so'raladi:
    hafta kuni, soat, davomiylik, masofa, narx, miqdor.
    Yuqori bosqichlarda gapiruvchi o'zini TUZATADI ("sorry, I mean
    Wednesday") — IELTS'da bu doim uchraydi.

  ielts_trap (5-mashq) — CHALG'ITUVCHI JAVOBLAR.
    Jahongir yuborgan misoldagi kabi: audioda BIR XIL turdagi
    2-3 ta qiymat aytiladi (jami 2,020 km, eng qisqasi 206 km,
    eng uzuni 632 km), savol esa faqat BITTASINI so'raydi.
    Talaba "eshitgan birinchi raqamini" yozsa — yiqiladi.
    Shuning uchun har mashqda nima aynan so'ralgani ta'kidlanadi.

TEZLIK VA QIYINLIK. Boshqa bloklardagi kabi step 1..5; tezlik
0.55x dan 1.0x gacha. Bosqich oshgani sari gap uzayadi, tuzatish
va chalg'ituvchilar soni ortadi.

TEKSHIRUV serverda: registr, bo'sh joy, vergul, nuqta va ikki
nuqta e'tiborsiz — "9:30" ham "9.30" ham "930" ham to'g'ri;
"2,020" ham "2020" ham to'g'ri.
"""

SKILL = "ielts_listening"
RATE_BY_STEP = {1: 0.6, 2: 0.7, 3: 0.8, 4: 0.9, 5: 1.0}

# =====================================================================
#  4-MASHQ: MA'LUMOT ILIB OLISH
#  (step, kategoriya, dialog, savol, javob)
# =====================================================================

_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
         "Saturday", "Sunday"]


def _detail_rows():
    rows = []

    def add(step, cat, say, prompt, answer, hint):
        rows.append((step, cat, say, prompt, answer, hint))

    # ---------- STEP 1: bitta aniq qiymat (20 ta) ----------
    times = ["9 a.m.", "10.30 a.m.", "2 p.m.", "4.15 p.m.", "6 p.m."]
    for t, day in zip(times, _WEEK):
        add(1, "time",
            f"The reception desk opens at {t} on {day}s.",
            f"What time does the reception desk open on {day}s?",
            t.replace(" a.m.", "").replace(" p.m.", ""),
            "Soat (faqat raqam, masalan 9 yoki 10.30)")
    classes = ["swimming", "guitar", "drawing", "chess", "yoga"]
    for cls, day in zip(classes, _WEEK[:5]):
        add(1, "weekday",
            f"The {cls} class takes place on {day}.",
            f"On which day is the {cls} class?", day, "Hafta kuni")
    vids = ["introduction", "safety", "welcome", "training", "history"]
    for v, n in zip(vids, ["45", "90", "20", "75", "30"]):
        add(1, "duration",
            f"The {v} video lasts {n} minutes.",
            f"How long does the {v} video last? (minutes)", n,
            "Daqiqa (faqat raqam)")
    trails = ["nature", "coastal", "forest", "river", "hill"]
    for tr, n in zip(trails, ["12", "35", "8", "60", "25"]):
        add(1, "distance",
            f"The {tr} trail is {n} kilometres long.",
            f"How long is the {tr} trail? (km)", n,
            "Kilometr (faqat raqam)")

    # ---------- STEP 2: qo'shimcha ma'lumot ichida (20 ta) ----------
    add(2, "time", "The museum opens at 10 in the morning, and the "
        "guided tour starts half an hour later.",
        "What time does the guided tour start?", "10.30",
        "Soat — yarim soat KEYIN")
    add(2, "time", "Check-in begins at 2 p.m., but you can leave your "
        "luggage from 11 a.m.",
        "From what time can you leave luggage?", "11",
        "Soat")
    add(2, "weekday", "The office is closed on Sunday, and on Saturday "
        "it only works until midday.",
        "On which day is the office completely closed?", "Sunday",
        "Hafta kuni")
    add(2, "duration", "The flight is three hours, and there is a "
        "one-hour wait at the airport before it.",
        "How long is the flight? (hours)", "3", "Soat")
    add(2, "distance", "From the hotel to the beach it is two "
        "kilometres, and the station is five kilometres away.",
        "How far is the beach from the hotel? (km)", "2", "Kilometr")
    add(2, "price", "Entry costs fifteen pounds, and the audio guide "
        "is an extra four pounds.",
        "How much does entry cost? (pounds)", "15", "Funt")
    add(2, "quantity", "There are twenty-four rooms in the building, "
        "six of them on the ground floor.",
        "How many rooms are there in total?", "24", "Son")
    add(2, "time", "Lessons finish at 4.45 and the bus leaves at five.",
        "What time do lessons finish?", "4.45", "Soat")
    add(2, "weekday", "We meet every Thursday, except in August when "
        "we move to Tuesday.",
        "Which day is the usual meeting?", "Thursday", "Hafta kuni")
    add(2, "duration", "The workshop runs for six weeks, with a break "
        "of two weeks in the middle.",
        "How many weeks does the workshop run? (number)", "6", "Hafta")
    add(2, "distance", "The cycle route is forty kilometres, though "
        "most people only do the first fifteen.",
        "How long is the whole cycle route? (km)", "40", "Kilometr")
    add(2, "price", "Membership is ninety pounds a year, or ten "
        "pounds a month.",
        "How much is membership per year? (pounds)", "90", "Funt")
    add(2, "quantity", "The minibus takes sixteen passengers plus the "
        "driver.",
        "How many passengers can the minibus take?", "16", "Son")
    add(2, "time", "Breakfast is served from seven until half past "
        "nine.",
        "What time does breakfast end?", "9.30", "Soat")
    add(2, "weekday", "The library stays open late on Wednesday and "
        "Friday.",
        "Which is the FIRST late day mentioned?", "Wednesday",
        "Hafta kuni")
    add(2, "duration", "Each session is fifty minutes, with a ten "
        "minute break after it.",
        "How long is each session? (minutes)", "50", "Daqiqa")
    add(2, "distance", "The walk to the waterfall is three "
        "kilometres each way.",
        "How far is it to the waterfall one way? (km)", "3",
        "Kilometr")
    add(2, "price", "A single ticket is two pounds fifty; a day pass "
        "is six pounds.",
        "How much is a day pass? (pounds)", "6", "Funt")
    add(2, "quantity", "We need eight volunteers on the day and four "
        "for the preparation.",
        "How many volunteers are needed on the day?", "8", "Son")
    add(2, "time", "The last train leaves at 11.20 at night.",
        "What time does the last train leave?", "11.20", "Soat")

    # ---------- STEP 3: ikki ma'lumot, bittasi so'raladi (20) ------
    pairs = [
        ("time", "The morning session is at 9.15 and the afternoon "
         "session is at 2.30.", "What time is the afternoon session?",
         "2.30", "Soat"),
        ("time", "The doors open at 6.45 and the concert itself "
         "begins at 7.30.", "What time does the concert begin?",
         "7.30", "Soat"),
        ("weekday", "The theory test is on Monday and the practical "
         "test is on Friday.", "Which day is the practical test?",
         "Friday", "Hafta kuni"),
        ("weekday", "Deliveries arrive on Tuesday, but the shop "
         "restocks the shelves on Wednesday.",
         "On which day are the shelves restocked?", "Wednesday",
         "Hafta kuni"),
        ("duration", "The written exam lasts ninety minutes and the "
         "interview twenty minutes.",
         "How long is the interview? (minutes)", "20", "Daqiqa"),
        ("duration", "The coach journey takes four hours; the return "
         "by train takes only two.",
         "How long does the train take? (hours)", "2", "Soat"),
        ("distance", "The first stage is eighteen kilometres and the "
         "second stage twenty-six.",
         "How long is the second stage? (km)", "26", "Kilometr"),
        ("distance", "The hotel is nine hundred metres from the "
         "station and two kilometres from the beach.",
         "How far is the hotel from the beach? (km)", "2",
         "Kilometr"),
        ("price", "Adults pay twelve pounds and children pay seven.",
         "How much do children pay? (pounds)", "7", "Funt"),
        ("price", "The deposit is fifty pounds and the full price is "
         "three hundred and twenty.",
         "What is the full price? (pounds)", "320", "Funt"),
        ("quantity", "There were sixty applicants and only fifteen "
         "places.", "How many places were there?", "15", "Son"),
        ("quantity", "The hall seats four hundred, but we expect "
         "about two hundred and fifty guests.",
         "How many guests are expected?", "250", "Son"),
        ("time", "Registration closes at 5 p.m. and the results come "
         "out at 9 the next morning.",
         "What time do the results come out?", "9", "Soat"),
        ("weekday", "The gym is busiest on Monday and quietest on "
         "Sunday.", "Which day is the gym quietest?", "Sunday",
         "Hafta kuni"),
        ("duration", "Part one takes twenty-five minutes and part two "
         "takes forty.", "How long is part two? (minutes)", "40",
         "Daqiqa"),
        ("distance", "The old road is fifty-two kilometres; the new "
         "motorway cuts it to thirty-eight.",
         "How long is the new motorway route? (km)", "38",
         "Kilometr"),
        ("price", "The course fee is four hundred and fifty pounds, "
         "and materials cost another thirty-five.",
         "How much do the materials cost? (pounds)", "35", "Funt"),
        ("quantity", "We ordered thirty chairs and twelve tables.",
         "How many tables were ordered?", "12", "Son"),
        ("time", "The ferry leaves at 8.05 and arrives at 11.40.",
         "What time does the ferry arrive?", "11.40", "Soat"),
        ("weekday", "Payment is due on Thursday, and the goods arrive "
         "the following Monday.",
         "On which day do the goods arrive?", "Monday", "Hafta kuni"),
    ]
    for cat, say, q, a, h in pairs:
        add(3, cat, say, q, a, h)

    # ---------- STEP 4: gapiruvchi O'ZINI TUZATADI (20 ta) --------
    fixes = [
        ("weekday", "The class is on Tuesday — sorry, no, I'm looking "
         "at last term's list. It's on Wednesday now.",
         "On which day is the class?", "Wednesday", "Hafta kuni"),
        ("time", "We start at nine... actually, from this month it's "
         "half past eight.", "What time do they start now?", "8.30",
         "Soat"),
        ("distance", "It's about forty kilometres — no, wait, that's "
         "the return trip. One way it's twenty.",
         "How far is it ONE WAY? (km)", "20", "Kilometr"),
        ("price", "That'll be sixty pounds. Oh, you're a student — so "
         "it's forty-five.",
         "How much does the student pay? (pounds)", "45", "Funt"),
        ("duration", "The tour is two hours. Hmm, with the museum "
         "visit it's actually three.",
         "How long is the tour WITH the museum? (hours)", "3",
         "Soat"),
        ("time", "The meeting was at four, but it's been moved "
         "forward an hour.", "What time is the meeting now?", "3",
         "Soat"),
        ("weekday", "Rubbish collection is Friday. Sorry — over the "
         "holiday week it moves to Saturday.",
         "Which day is collection during the holiday week?",
         "Saturday", "Hafta kuni"),
        ("quantity", "Put down twelve people. No — add the two "
         "guides, so fourteen.",
         "How many people in total?", "14", "Son"),
        ("price", "It's ninety-nine pounds... let me check... yes, "
         "but there's a five pound booking fee, so a hundred and "
         "four.", "How much will you pay in total? (pounds)", "104",
         "Funt"),
        ("distance", "The race is ten kilometres. Sorry, the junior "
         "race — the adult one is twenty-one.",
         "How long is the ADULT race? (km)", "21", "Kilometr"),
        ("time", "Doors at seven. Actually the email says six forty-"
         "five.", "What time do the doors open?", "6.45", "Soat"),
        ("duration", "The contract is for six months — no, they "
         "extended it, it's twelve now.",
         "How long is the contract now? (months)", "12", "Oy"),
        ("weekday", "I'll come Monday. Ah, Monday's a bank holiday — "
         "make it Tuesday.", "Which day will he come?", "Tuesday",
         "Hafta kuni"),
        ("price", "Twenty pounds each. For a group of ten it drops "
         "to sixteen.",
         "How much each for a group of ten? (pounds)", "16", "Funt"),
        ("quantity", "There are three bedrooms. Well, four if you "
         "count the small one upstairs.",
         "How many bedrooms are there in total?", "4", "Son"),
        ("time", "Lunch is at half twelve. Sorry — half past one on "
         "Fridays.", "What time is lunch on Fridays?", "1.30",
         "Soat"),
        ("distance", "It's five kilometres by road but only three if "
         "you walk across the park.",
         "How far is it if you WALK? (km)", "3", "Kilometr"),
        ("duration", "The film's ninety minutes. With the adverts, "
         "closer to a hundred and ten.",
         "How long with the adverts? (minutes)", "110", "Daqiqa"),
        ("weekday", "Results go out on Wednesday. Hold on — this "
         "year it's Thursday.",
         "Which day do results go out this year?", "Thursday",
         "Hafta kuni"),
        ("price", "The room is eighty a night. Breakfast adds twelve, "
         "so ninety-two.",
         "How much per night with breakfast? (pounds)", "92", "Funt"),
    ]
    for cat, say, q, a, h in fixes:
        add(4, cat, say, q, a, h)

    # ---------- STEP 5: uzun, tez, tuzatishli (20 ta) -------------
    hard = [
        ("time", "Right, so the coach picks you up at a quarter to "
         "seven — that's from the hotel, not the airport; the airport "
         "pick-up is forty minutes later.",
         "What time is the AIRPORT pick-up?", "7.25", "Soat"),
        ("distance", "The whole route is a hundred and forty "
         "kilometres, split into two days: eighty on the first day "
         "and the rest on the second.",
         "How many kilometres on the SECOND day?", "60", "Kilometr"),
        ("duration", "Allow three hours for the visit — an hour in "
         "the gallery, forty minutes for lunch and the rest in the "
         "gardens.",
         "How many minutes are spent in the gardens?", "80",
         "Daqiqa"),
        ("price", "The package is two hundred and forty pounds per "
         "person, but there's a ten per cent discount for groups.",
         "What does one person in a group pay? (pounds)", "216",
         "Funt"),
        ("weekday", "The centre runs sessions on Monday, Wednesday "
         "and Friday; the beginners' one is always the middle day.",
         "Which day is the beginners' session?", "Wednesday",
         "Hafta kuni"),
        ("quantity", "We had thirty-two bookings, four cancelled and "
         "two more joined on the day.",
         "How many people came in the end?", "30", "Son"),
        ("time", "It leaves at ten past eight and the journey takes "
         "an hour and a half.",
         "What time does it arrive?", "9.40", "Soat"),
        ("distance", "Day one is twelve kilometres, day two is "
         "eighteen and day three is the same as day one.",
         "What is the TOTAL distance? (km)", "42", "Kilometr"),
        ("duration", "The programme is four weeks full-time, or eight "
         "weeks if you study in the evenings.",
         "How many weeks for the EVENING option?", "8", "Hafta"),
        ("price", "Tickets are eighteen pounds, but under-sixteens "
         "pay half.",
         "How much does a fourteen-year-old pay? (pounds)", "9",
         "Funt"),
        ("weekday", "The deadline is the Friday before the holiday, "
         "and the holiday starts on Monday the tenth.",
         "On which DAY of the week is the deadline?", "Friday",
         "Hafta kuni"),
        ("quantity", "Each box holds twenty-four bottles and we "
         "ordered five boxes.",
         "How many bottles altogether?", "120", "Son"),
        ("time", "Registration is open from nine until four, but on "
         "the last day it closes two hours early.",
         "What time does it close on the LAST day?", "2", "Soat"),
        ("distance", "It's seven hundred and fifty metres to the "
         "car park and one and a half kilometres to the entrance.",
         "How far is the entrance in metres?", "1500", "Metr"),
        ("duration", "Interviews are twenty minutes each with a "
         "ten-minute gap, and there are four candidates.",
         "How many minutes from the first start to the last end?",
         "110", "Daqiqa"),
        ("price", "It's forty pounds a month for twelve months, paid "
         "in one go.", "How much is paid in total? (pounds)", "480",
         "Funt"),
        ("weekday", "The market runs at the weekend — Saturday for "
         "food and the other day for crafts.",
         "Which day is the CRAFTS market?", "Sunday", "Hafta kuni"),
        ("quantity", "Of the ninety students, a third chose the "
         "science option.",
         "How many chose science?", "30", "Son"),
        ("time", "The alarm is set for five thirty, but he never gets "
         "up before six fifteen.",
         "What time does he actually get up?", "6.15", "Soat"),
        ("duration", "The warranty is two years, extendable by a "
         "further eighteen months.",
         "What is the MAXIMUM cover in months?", "42", "Oy"),
    ]
    for cat, say, q, a, h in hard:
        add(5, cat, say, q, a, h)

    return rows


# =====================================================================
#  5-MASHQ: CHALG'ITUVCHI JAVOBLAR (multiple answers trap)
#  Audioda bir xil turdagi 2-3 qiymat, savol bittasini so'raydi.
# =====================================================================

def _trap_rows():
    rows = []

    def add(step, say, prompt, answer, others, hint):
        rows.append((step, say, prompt, answer, others, hint))

    # ---------- STEP 1: ikki qiymat, savol aniq (20 ta) ----------
    s1 = [
        ("The morning tour is 40 kilometres and the afternoon tour is "
         "25 kilometres.", "How long is the AFTERNOON tour? (km)",
         "25", "40"),
        ("The pool opens at 6 a.m. and closes at 9 p.m.",
         "What time does the pool CLOSE?", "9", "6"),
        ("Adults pay 14 pounds, children pay 8 pounds.",
         "How much do CHILDREN pay? (pounds)", "8", "14"),
        ("The lecture is on Monday; the seminar is on Thursday.",
         "Which day is the SEMINAR?", "Thursday", "Monday"),
        ("Part one lasts 30 minutes and part two lasts 45 minutes.",
         "How long is PART TWO? (minutes)", "45", "30"),
        ("The bus takes 50 minutes; the train takes 20 minutes.",
         "How long does the TRAIN take? (minutes)", "20", "50"),
        ("There are 18 rooms in the old wing and 32 in the new one.",
         "How many rooms in the NEW wing?", "32", "18"),
        ("The deposit is 100 pounds and the balance is 350 pounds.",
         "How much is the BALANCE? (pounds)", "350", "100"),
        ("Registration closes on Friday; the course starts on Monday.",
         "Which day does the COURSE START?", "Monday", "Friday"),
        ("The short walk is 3 kilometres, the long walk is 11.",
         "How long is the SHORT walk? (km)", "3", "11"),
        ("Breakfast is at 7.30 and dinner is at 7.30 in the evening; "
         "lunch is at 12.15.", "What time is LUNCH?", "12.15", "7.30"),
        ("The library shuts at 8 on weekdays and at 5 at weekends.",
         "What time does it shut at WEEKENDS?", "5", "8"),
        ("A single room is 60 pounds; a double is 85.",
         "How much is a DOUBLE room? (pounds)", "85", "60"),
        ("The maths exam is on Wednesday and the results come on "
         "Friday.", "Which day is the MATHS EXAM?", "Wednesday",
         "Friday"),
        ("The first session runs 90 minutes, the second only 60.",
         "How long is the SECOND session? (minutes)", "60", "90"),
        ("It's 5 kilometres to the village and 12 to the town.",
         "How far is the TOWN? (km)", "12", "5"),
        ("There are 25 seats downstairs and 40 upstairs.",
         "How many seats UPSTAIRS?", "40", "25"),
        ("The early flight is at 6.10, the later one at 11.55.",
         "What time is the LATER flight?", "11.55", "6.10"),
        ("Standard delivery is 4 days, express is 1 day.",
         "How many days for STANDARD delivery?", "4", "1"),
        ("The gym costs 30 a month or 300 a year.",
         "How much per MONTH? (pounds)", "30", "300"),
    ]
    for say, q, a, o in s1:
        add(1, say, q, a, [o], "Ikkita qiymat aytiladi — SO'RALGANINI oling")

    # ---------- STEP 2-3: uch qiymat (40 ta) ----------
    s3 = [
        (2, "The self-drive tour covers 2,020 kilometres in total. "
         "The shortest day's drive is 206 kilometres and the longest "
         "is 632 kilometres.",
         "What is the TOTAL distance of the trip? (km)", "2020",
         ["206", "632"]),
        (2, "The museum opens at 9.30, the cafe at 10 and the shop "
         "at 11.", "What time does the SHOP open?", "11",
         ["9.30", "10"]),
        (2, "Classes run on Monday, Wednesday and Saturday. The exam "
         "is always on the Saturday.",
         "Which day is the EXAM?", "Saturday", ["Monday", "Wednesday"]),
        (2, "Adults are 20 pounds, students 12 and children under "
         "five are free.",
         "How much do STUDENTS pay? (pounds)", "12", ["20", "free"]),
        (2, "The whole walk is 14 kilometres: 6 before lunch and 8 "
         "after.", "How far is the walk BEFORE lunch? (km)", "6",
         ["14", "8"]),
        (2, "The talk is 45 minutes, questions are 15 minutes and the "
         "break is 20.", "How long are the QUESTIONS? (minutes)",
         "15", ["45", "20"]),
        (2, "We have 3 rooms free in June, 8 in July and none in "
         "August.", "How many rooms are free in JULY?", "8",
         ["3", "none"]),
        (2, "The train leaves at 7.40, arrives at 10.15, and the "
         "connection departs at 10.50.",
         "What time does the CONNECTION depart?", "10.50",
         ["7.40", "10.15"]),
        (3, "Last year we had 240 members, this year 315, and we hope "
         "for 400 next year.",
         "How many members are there THIS year?", "315",
         ["240", "400"]),
        (3, "The course is 8 weeks; the placement is 4 weeks and the "
         "project takes another 6.",
         "How long is the PROJECT? (weeks)", "6", ["8", "4"]),
        (3, "Option A is 250 pounds, option B is 380 and option C is "
         "610.", "How much is OPTION B? (pounds)", "380",
         ["250", "610"]),
        (3, "The first flight is 2 hours, the stopover is 4 hours and "
         "the second flight is 3 hours.",
         "How long is the STOPOVER? (hours)", "4", ["2", "3"]),
        (3, "Deliveries are Tuesday and Thursday; the office is "
         "closed on Wednesday.",
         "Which day is the office CLOSED?", "Wednesday",
         ["Tuesday", "Thursday"]),
        (3, "The lift takes 12 people, the stairs are 84 steps and "
         "the building has 7 floors.",
         "How many FLOORS does the building have?", "7",
         ["12", "84"]),
        (3, "Booking opens on the 3rd, closes on the 17th and the "
         "event is on the 24th.",
         "On which date does booking CLOSE?", "17", ["3", "24"]),
        (3, "The room rate is 95 pounds, breakfast is 14 and parking "
         "is 9.", "How much is PARKING? (pounds)", "9", ["95", "14"]),
        (3, "There are 6 sessions in the morning, 4 in the afternoon "
         "and 2 in the evening.",
         "How many sessions in the AFTERNOON?", "4", ["6", "2"]),
        (3, "It's 18 kilometres to the airport, 7 to the station and "
         "2 to the centre.",
         "How far is the STATION? (km)", "7", ["18", "2"]),
        (3, "The warranty is 12 months, extendable to 24, and repairs "
         "are covered for 6.",
         "How many months are REPAIRS covered?", "6", ["12", "24"]),
        (3, "Lessons are 9 to 12 in the morning and 2 to 4 in the "
         "afternoon.", "What time do AFTERNOON lessons end?", "4",
         ["12", "2"]),
    ] * 1
    s3b = [
        (2, "The gallery is open 10 to 5, the shop 10 to 6 and the "
         "cafe 9 to 4.", "What time does the CAFE close?", "4",
         ["5", "6"]),
        (2, "Beginners meet on Monday, intermediate on Wednesday and "
         "advanced on Friday.",
         "Which day do INTERMEDIATE learners meet?", "Wednesday",
         ["Monday", "Friday"]),
        (2, "The bike hire is 8 pounds an hour, 25 for half a day and "
         "40 for a full day.",
         "How much for HALF a day? (pounds)", "25", ["8", "40"]),
        (2, "Route one is 9 kilometres, route two 16 and route three "
         "22.", "How long is ROUTE TWO? (km)", "16", ["9", "22"]),
        (2, "The talk lasts 30 minutes, the film 55 and the "
         "discussion 25.", "How long is the FILM? (minutes)", "55",
         ["30", "25"]),
        (2, "We have 5 single rooms, 9 doubles and 2 family rooms.",
         "How many DOUBLE rooms are there?", "9", ["5", "2"]),
        (2, "The first bus is at 6.45, the next at 7.20 and then "
         "every half hour.",
         "What time is the SECOND bus?", "7.20", ["6.45", "8"]),
        (2, "Postage is 3 pounds in the UK, 9 in Europe and 15 "
         "worldwide.",
         "How much is postage to EUROPE? (pounds)", "9", ["3", "15"]),
        (2, "The pool is cleaned on Tuesday, the gym on Thursday and "
         "the courts on Sunday.",
         "Which day is the GYM cleaned?", "Thursday",
         ["Tuesday", "Sunday"]),
        (2, "Level one takes 10 weeks, level two 12 and level three "
         "16.", "How many weeks is LEVEL THREE?", "16", ["10", "12"]),
        (2, "There are 14 places on the morning trip, 20 on the "
         "afternoon one and 6 in the evening.",
         "How many places on the AFTERNOON trip?", "20", ["14", "6"]),
        (2, "The station is 400 metres away, the market 900 and the "
         "park 1,200.",
         "How far is the MARKET? (metres)", "900", ["400", "1200"]),
        (2, "Doors open 7, the show starts 7.45 and the interval is "
         "at 8.50.", "What time is the INTERVAL?", "8.50",
         ["7", "7.45"]),
        (2, "A day ticket is 11 pounds, a week 45 and a month 150.",
         "How much for a WEEK? (pounds)", "45", ["11", "150"]),
        (2, "The report is due Monday, the presentation Wednesday and "
         "the feedback Friday.",
         "Which day is the PRESENTATION?", "Wednesday",
         ["Monday", "Friday"]),
        (2, "Group sizes are 6 for cooking, 12 for language and 20 "
         "for the lecture.",
         "How many in the LANGUAGE group?", "12", ["6", "20"]),
        (2, "It takes 25 minutes on foot, 10 by bike and 6 by car.",
         "How many minutes BY BIKE?", "10", ["25", "6"]),
        (2, "Rooms are cleaned at 9, beds changed at 11 and towels "
         "at 3.", "What time are BEDS changed?", "11", ["9", "3"]),
        (2, "The trial is 14 days, the basic plan 1 month and the "
         "annual plan 12 months.",
         "How many DAYS is the trial?", "14", ["1", "12"]),
        (2, "Platform 2 for the local train, platform 5 for the "
         "express and platform 9 for the airport service.",
         "Which platform for the AIRPORT service?", "9", ["2", "5"]),
    ]
    for step, say, q, a, others in s3 + s3b:
        add(step, say, q, a, others,
            "Uch qiymat aytiladi — savol qaysinisini so'rayotganiga "
            "diqqat qiling")

    # ---------- STEP 4: chalg'ituvchi + tuzatish (20 ta) --------
    s4 = [
        ("The trip is 320 kilometres. Sorry — that's the round trip. "
         "One way it's 160, and the detour adds another 25.",
         "How far is it ONE WAY? (km)", "160", ["320", "25"]),
        ("We open at 8. Well, the doors open at 8 but the desk opens "
         "at 8.30 and the first tour is at 9.",
         "What time does the DESK open?", "8.30", ["8", "9"]),
        ("It's on Tuesday. Hang on — Tuesday is the staff meeting. "
         "The public session is Thursday, and Friday is cleaning.",
         "Which day is the PUBLIC session?", "Thursday",
         ["Tuesday", "Friday"]),
        ("Two hundred pounds. Actually that was last year; it's two "
         "hundred and thirty now, plus a twenty pound deposit.",
         "What is the price NOW, without the deposit? (pounds)",
         "230", ["200", "20"]),
        ("The session is an hour. With the practical it's an hour and "
         "a half, and the assessment adds thirty minutes.",
         "How long is the session WITH the practical? (minutes)",
         "90", ["60", "30"]),
        ("There are 40 places. No — 40 applied; there are 25 places "
         "and 15 on the waiting list.",
         "How many PLACES are there?", "25", ["40", "15"]),
        ("The bus is at 6.20, but that's the early one. The one you "
         "want is 7.05, and the last is 9.30.",
         "What time is the bus you WANT?", "7.05", ["6.20", "9.30"]),
        ("It's 3 kilometres. Sorry, 3 miles — that's about 5 "
         "kilometres, and the shortcut is 4.",
         "How far is it in kilometres by the MAIN route?", "5",
         ["3", "4"]),
        ("Monday and Wednesday for beginners. Sorry, Monday is now "
         "full, so beginners are Wednesday and Saturday.",
         "Which TWO days are for beginners now? (answer the later "
         "one)", "Saturday", ["Monday", "Wednesday"]),
        ("Fifty pounds each. For members it's thirty-five, and "
         "children go free.",
         "How much do MEMBERS pay? (pounds)", "35", ["50", "free"]),
        ("The report is due in 2 weeks. Well, the draft is in 2 "
         "weeks; the final version is in 5.",
         "In how many weeks is the FINAL version due?", "5",
         ["2", "5"]),
        ("Room 12. Sorry, room 12 is the office — the class is in "
         "room 21, next to room 20.",
         "Which room is the CLASS in?", "21", ["12", "20"]),
        ("It lasts 4 days. That includes travel; the actual "
         "programme is 3 days and there's 1 free day.",
         "How many days is the actual PROGRAMME?", "3", ["4", "1"]),
        ("We need 12 chairs. Make it 12 tables and 30 chairs.",
         "How many CHAIRS are needed?", "30", ["12", "30"]),
        ("Departure is 14th July. Sorry — booking closes on the "
         "14th; departure is the 21st and return the 28th.",
         "On which date is DEPARTURE?", "21", ["14", "28"]),
        ("The fee is 75. Plus VAT that's 90, and there's a 15 pound "
         "registration charge.",
         "What is the fee INCLUDING VAT but without registration? "
         "(pounds)", "90", ["75", "15"]),
        ("Nine in the morning. Actually she said nine THIRTY, and the "
         "second group is at eleven.",
         "What time is the FIRST group?", "9.30", ["9", "11"]),
        ("It's 200 metres. Sorry, 200 metres to the car park; the "
         "entrance is 600 metres and the cafe is 350.",
         "How far is the ENTRANCE? (metres)", "600", ["200", "350"]),
        ("Six people. Six confirmed, four maybe — so plan for ten.",
         "How many should we PLAN for?", "10", ["6", "4"]),
        ("Thursday at 5. No — Thursday at 5 is the rehearsal; the "
         "performance is Friday at 7.",
         "What time is the PERFORMANCE?", "7", ["5", "7"]),
    ]
    for say, q, a, others in s4:
        add(4, say, q, a, others,
            "Tuzatish bor: gapiruvchi o'zini to'g'irlaydi — OXIRGI "
            "to'g'ri qiymatni oling")

    # ---------- STEP 5: eng qiyin (20 ta) ----------
    s5 = [
        ("The full circuit is 2,020 kilometres over twelve days. The "
         "shortest single day is 206 and the longest is 632, but "
         "most days average around 170.",
         "What is the TOTAL distance? (km)", "2020",
         ["206", "632", "170"]),
        ("The centre is open 8 till 8 on weekdays, 9 till 5 on "
         "Saturday and 10 till 4 on Sunday. The pool, though, closes "
         "an hour before the centre every day.",
         "What time does the POOL close on SUNDAY?", "3",
         ["4", "5", "8"]),
        ("Standard is 45 pounds, concession 30, family 110 and there "
         "is a 5 pound booking fee on all of them.",
         "What does a FAMILY pay in total, with the fee? (pounds)",
         "115", ["110", "45", "30"]),
        ("Group A meets Monday and Thursday, group B Tuesday and "
         "Friday, and the joint session is on the Wednesday.",
         "Which day does GROUP B meet FIRST in the week?", "Tuesday",
         ["Monday", "Wednesday", "Friday"]),
        ("The flight is 7 hours, there's a 3 hour stopover and then "
         "another 2 hours. Add an hour for check-in at the start.",
         "How many hours from CHECK-IN to arrival?", "13",
         ["7", "3", "2"]),
        ("We sold 340 tickets, but 40 were refunded and 25 were "
         "complimentary, so paid attendance was lower.",
         "How many PAID tickets were actually used?", "275",
         ["340", "40", "25"]),
        ("The old site is 12 kilometres away, the new one 30, and "
         "the depot sits halfway between the two.",
         "How far is the DEPOT? (km)", "21", ["12", "30", "15"]),
        ("Doors 6.30, support act 7.15, main act 8.45, and it all "
         "finishes by 11.",
         "What time does the MAIN act start?", "8.45",
         ["6.30", "7.15", "11"]),
        ("The lease is 3 years with a 6 month break clause and a 12 "
         "month notice period after that.",
         "How many MONTHS is the notice period?", "12",
         ["3", "6", "36"]),
        ("Prices went from 80 to 95 last year and to 120 this year; "
         "next year they plan 135.",
         "What is the price THIS year? (pounds)", "120",
         ["80", "95", "135"]),
        ("Session one is 9 to 10.30, session two 11 to 12, and after "
         "lunch there's a 90 minute workshop starting at 2.",
         "What time does the WORKSHOP finish?", "3.30",
         ["10.30", "12", "2"]),
        ("There are 4 teachers, 2 assistants and 28 students; each "
         "teacher takes an equal share of the students.",
         "How many students per TEACHER?", "7", ["4", "2", "28"]),
        ("The deadline was the 5th, extended to the 12th, and late "
         "entries are accepted until the 19th with a penalty.",
         "Until which date are LATE entries accepted?", "19",
         ["5", "12"]),
        ("Monday is closed, Tuesday to Friday it's 10 to 6, and at "
         "the weekend 11 to 4.",
         "What time does it OPEN on Saturday?", "11", ["10", "6", "4"]),
        ("Course fees are 600, the exam is 150 and the textbook 45. "
         "Members get 10 per cent off the course fee only.",
         "What does a MEMBER pay for the course? (pounds)", "540",
         ["600", "150", "45"]),
        ("The van does 8 kilometres per litre, the tank holds 60 "
         "litres and the journey is 400 kilometres.",
         "How many LITRES are needed for the journey?", "50",
         ["8", "60", "400"]),
        ("She starts at 8.15, has 40 minutes for lunch and leaves at "
         "5.15.", "How many hours does she actually WORK?", "8.20",
         ["9", "8.15", "5.15"]),
        ("Tickets: 25 on the door, 20 in advance, 18 for groups over "
         "ten. Our group has nine people.",
         "How much does each of OUR group pay? (pounds)", "20",
         ["25", "18"]),
        ("The building has 9 floors above ground and 2 below; the "
         "office is on the fourth floor from the top.",
         "Which floor is the OFFICE on?", "6", ["9", "2", "4"]),
        ("Term one is 14 weeks, term two 11 and term three 9, with "
         "2 weeks holiday between each.",
         "How many weeks in TOTAL, including holidays?", "38",
         ["14", "11", "9"]),
    ]
    for say, q, a, others in s5:
        add(5, say, q, a, others,
            "Bir nechta qiymat va hisob-kitob — savolni oxirigacha "
            "o'qing")

    return rows


def build_rows():
    """(kind, level, payload, answer, explain) ro'yxati."""
    out = []
    for i, (step, cat, say, prompt, answer, hint) in enumerate(
            _detail_rows()):
        out.append((
            "ielts_detail", f"D{step}",
            {"say": say, "prompt": prompt, "step": step,
             "rate": RATE_BY_STEP[step], "order": i, "hint": hint,
             "cat": cat},
            answer,
            "Savolda AYNAN nima so'ralganiga qarang: soatmi, "
            "kunmi, davomiylikmi. Gapiruvchi o'zini tuzatsa — "
            "oxirgi aytilgani to'g'ri."))

    for i, (step, say, prompt, answer, others, hint) in enumerate(
            _trap_rows()):
        out.append((
            "ielts_trap", f"T{step}",
            {"say": say, "prompt": prompt, "step": step,
             "rate": RATE_BY_STEP[step], "order": i, "hint": hint,
             "others": others},
            answer,
            "Audioda bir xil turdagi bir nechta qiymat aytiladi. "
            "Chalg'ituvchilar: " + ", ".join(others) + ". "
            "Savol qaysinisini so'rayotganini aniqlab oling."))
    return out


def seed_ielts2(db):
    """Idempotent: (kind, answer, prompt) bo'yicha yo'qlari qo'shiladi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_listen_v2"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            have.add((k, json.loads(p).get("prompt")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain in build_rows():
        key = (kind, payload.get("prompt"))
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
    _seed_mark(db, "ielts_listen_v2")
    return made
