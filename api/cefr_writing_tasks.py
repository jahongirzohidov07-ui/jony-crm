# -*- coding: utf-8 -*-
"""CEFR WRITING — IMTIHON QATLAMI (2026-08-26).

YANGI FORMAT. Jahongir yuborgan namunada (14.03.2026, 1-smena)
eng muhim narsa shu: PART 1 da bitta xabar keladi va o'quvchi
SHU BITTA vaziyat bo'yicha IKKI xat yozadi —

  1.1  do'stiga        norasmiy   ~50 so'z    7 daqiqa
  1.2  rahbariyatga    rasmiy    120-150 so'z 23 daqiqa

Bu tasodifiy emas: imtihon aynan REGISTER almashtira olishni
tekshiradi. Shuning uchun bu yerda vazifalar ham juftlab tuzilgan
— alohida-alohida emas.

  PART 2  blog / forum / article   C1   180-200 so'z   30 daqiqa

BANDLAR QAMROVI. Har topshiriq bandi uchun "keys" — sinonimlar
to'plami yozilgan. Avtomat tekshirgich shular orqali bandning
javobda YORITILGANINI aniqlaydi. Bu mukammal emas (til jonli
narsa), lekin eng ko'p yo'qotiladigan ballni — "bandni umuman
yozmadim" holatini — ishonchli tutadi.
"""

# =================================================================
#  PART 1 — bitta vaziyat, ikki xat
# =================================================================

# His-tuyg'u BITTA ro'yxatda. Avval har topshiriqda alohida
# yozilgan edi va "furious", "happy" kabi so'zlar tushib qolib,
# to'g'ri javob "band yoritilmagan" deb belgilanardi.
_FEEL = [
    "feel", "felt", "happy", "unhappy", "sad", "annoy", "upset",
    "angry", "furious", "excited", "mind", "glad", "disappoint",
    "shame", "love", "hate", "worri", "stress", "shock", "fair",
    "unfair", "nervous", "keen", "hope", "sorry", "guilt", "awful",
    "embarrass", "grateful", "thank", "lucky", "relie", "impress",
    "frustrat", "terrible", "great", "fine", "pleased", "delight",
    "look forward", "bad", "good", "cross", "fed up", "gutted",
]

PART1: list[dict] = [
    {
        "id": "p1_cinema",
        "topic": "Kino klub",
        "type": "request",
        "context_from": "your cinema club manager",
        "context": "Dear Member,\nThe cinema club management is "
                   "considering moving weekly movie time from Friday "
                   "evenings to Tuesday mornings to reduce the "
                   "theatre rental costs. They are also planning to "
                   "stop showing international movies with subtitles "
                   "and instead focus only on high-budget Hollywood "
                   "films.\nThe Club Manager",
        "t11": {
            "prompt": "Write a short letter to your friend who also "
                      "attends this cinema club with you. Explain the "
                      "situation about the possible changes and tell "
                      "them how you feel about it.",
            "bullets": [
                {"label": "explain the changes",
                 "keys": [["chang", "move", "moving", "tuesday",
                           "morning", "friday"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the cinema club manager.",
            "bullets": [
                {"label": "give your opinion about moving the movie "
                          "time to Tuesday mornings",
                 "keys": [["tuesday", "morning", "time", "schedul"]]},
                {"label": "explain what you think about focusing only "
                          "on Hollywood movies",
                 "keys": [["hollywood", "international", "subtitle",
                           "foreign", "film", "movie"]]},
                {"label": "suggest what the club should do instead",
                 "keys": [["suggest", "propose", "instead", "could",
                           "recommend", "alternativ", "perhaps"]]},
            ],
        },
        "model11": "Hi Sardor,\n\nHow are you? Guess what — the club "
                   "wants to move our film night from Friday evening to "
                   "Tuesday morning to save money, and to show only "
                   "Hollywood films from now on.\n\n"
                   "To be honest, I'm really disappointed. Tuesday "
                   "morning is impossible for me, and the subtitled "
                   "films were the best part.\n\nWhat do you think? "
                   "Write back soon!\n\nTake care,\nJavohir",
        "model12": "Dear Sir or Madam,\n\nI am writing on behalf of "
                   "several members regarding the changes announced in "
                   "your recent message.\n\nWhile I understand that "
                   "rental costs must be reduced, moving the screening "
                   "to Tuesday morning would exclude almost every "
                   "working member and student. Friday evening is the "
                   "one time most of us are free.\n\nI am also "
                   "concerned about showing only Hollywood films. Many "
                   "of us joined precisely because of the subtitled "
                   "international programme, which is difficult to "
                   "find elsewhere in the city.\n\nI would therefore "
                   "suggest keeping Friday evenings but reducing the "
                   "number of screenings to two a month, and "
                   "alternating between international and popular "
                   "films. This would cut costs without losing the "
                   "audience.\n\nThank you for your consideration.\n\n"
                   "Yours faithfully,",
    },
    {
        "id": "p1_gym",
        "topic": "Sport zali",
        "type": "complaint",
        "context_from": "the manager of your fitness centre",
        "context": "Dear Member,\nFrom next month the monthly "
                   "membership fee will increase by 30%. The swimming "
                   "pool will also be closed on weekdays so that it "
                   "can be rented to a private school.\nFitness "
                   "Centre Management",
        "t11": {
            "prompt": "Write a short letter to your friend who trains "
                      "at the same centre. Explain what is changing "
                      "and tell them how you feel about it.",
            "bullets": [
                {"label": "explain the changes",
                 "keys": [["fee", "price", "expensive", "increase",
                           "pool", "30", "cost", "swim"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the fitness centre manager.",
            "bullets": [
                {"label": "say how long you have been a member",
                 "keys": [["member", "year", "month", "since", "been"]]},
                {"label": "explain why the changes are a problem for you",
                 "keys": [["problem", "difficult", "afford", "unable",
                           "cannot", "student", "work", "weekday"]]},
                {"label": "say what you would like the centre to do",
                 "keys": [["would like", "request", "suggest", "ask",
                           "hope", "propose", "discount", "keep"]]},
            ],
        },
        "model11": "Hi Dilnoza,\n\nHope you're well! Did you see the "
                   "message from the gym? They're putting the fee up "
                   "by 30% next month, and the pool will be closed on "
                   "weekdays because they're renting it to a school.\n\n"
                   "I'm pretty annoyed, to be honest. We only go on "
                   "weekdays, so we're paying more for less.\n\n"
                   "Shall we look for another place? Let me know!\n\n"
                   "See you soon,\nMalika",
        "model12": "Dear Sir or Madam,\n\nI am writing regarding the "
                   "changes to membership announced this week. I have "
                   "been a member of your centre for three years and "
                   "have always been satisfied with the service.\n\n"
                   "However, the two changes together create a real "
                   "difficulty. A 30% increase is a considerable sum "
                   "for a student, and closing the pool on weekdays "
                   "removes the only time I am able to swim. In "
                   "effect, members like me would pay significantly "
                   "more for noticeably less.\n\nI would be grateful "
                   "if you could consider a reduced rate for members "
                   "who use the centre only on weekdays, or keep two "
                   "weekday evenings free for those members who have been with "
                   "the centre for more than a year.\n\nI "
                   "look forward to hearing from you.\n\nYours "
                   "faithfully,",
    },
    {
        "id": "p1_library",
        "topic": "Kutubxona",
        "type": "request",
        "context_from": "your university library",
        "context": "Dear Student,\nDue to building work, the library "
                   "will close at 5 p.m. instead of 10 p.m. for the "
                   "next three months. The group study rooms will not "
                   "be available during this period.\nLibrary "
                   "Services",
        "t11": {
            "prompt": "Write a short letter to your classmate. Explain "
                      "the situation and tell them how you feel.",
            "bullets": [
                {"label": "explain the changes",
                 "keys": [["clos", "5", "five", "early", "study room",
                           "building", "hour"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the head of library services.",
            "bullets": [
                {"label": "explain how you use the library",
                 "keys": [["use", "study", "evening", "after", "work",
                           "class", "revis"]]},
                {"label": "explain why the new hours are a problem",
                 "keys": [["problem", "difficult", "exam", "evening",
                           "unable", "cannot", "job", "late"]]},
                {"label": "suggest a solution",
                 "keys": [["suggest", "propose", "could", "perhaps",
                           "alternativ", "another", "room", "recommend"]]},
            ],
        },
        "model11": "Hi Ozoda,\n\nHow's it going? Bad news — the "
                   "library is closing at five instead of ten for the "
                   "next three months because of building work, and "
                   "the group rooms are shut too.\n\nI'm really "
                   "worried about it. Exams are in six weeks and I "
                   "always revise there in the evenings.\n\nWhere are "
                   "you going to study? Let me know.\n\nBest,\nSarvar",
        "model12": "Dear Sir or Madam,\n\nI am writing with regard to "
                   "the reduced opening hours announced for the next "
                   "three months.\n\nLike many students on my course, "
                   "I work part-time during the day and rely on the "
                   "library between six and nine in the evening. The "
                   "new closing time removes that possibility "
                   "entirely, and it does so during the revision "
                   "period before the winter examinations.\n\nI "
                   "understand that building work cannot be avoided. "
                   "However, I would like to suggest that the reading "
                   "room on the ground floor, which is not affected by "
                   "the work, remain open until nine, even without "
                   "staff at the desk. A card-entry system would make "
                   "this possible at little cost.\n\nThank you for "
                   "considering this request.\n\nYours faithfully,",
    },
    {
        "id": "p1_bus",
        "topic": "Avtobus yo'nalishi",
        "type": "request",
        "context_from": "the city transport company",
        "context": "Dear Passenger,\nFrom 1st September the number 12 "
                   "bus will no longer stop at Green Park. Passengers "
                   "should use the number 30 bus, which stops 1.5 km "
                   "away. The service will also be reduced to one bus "
                   "per hour.\nCity Transport",
        "t11": {
            "prompt": "Write a short letter to a friend who travels on "
                      "the same route. Explain the change and say how "
                      "you feel.",
            "bullets": [
                {"label": "explain the change",
                 "keys": [["bus", "12", "stop", "green park", "30",
                           "hour", "chang", "walk"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the city transport company.",
            "bullets": [
                {"label": "say how you use the service",
                 "keys": [["every day", "daily", "work", "school",
                           "travel", "use", "commut", "morning"]]},
                {"label": "explain the problems the change will cause",
                 "keys": [["problem", "walk", "elder", "children",
                           "winter", "late", "difficult", "far",
                           "distance"]]},
                {"label": "ask them to reconsider",
                 "keys": [["reconsider", "review", "request", "ask",
                           "urge", "hope", "would like", "please"]]},
            ],
        },
        "model11": "Hi Kamola,\n\nHave you heard? From September the "
                   "number 12 won't stop at Green Park any more. "
                   "We'll have to use the 30 and walk about a "
                   "kilometre and a half, and there'll only be one "
                   "bus an hour.\n\nHonestly, I'm furious. That's an "
                   "extra half hour each way, in winter too.\n\nAre "
                   "you going to complain as well?\n\nTake care,\nAziza",
        "model12": "Dear Sir or Madam,\n\nI am writing regarding the "
                   "planned changes to the number 12 service from 1st "
                   "September.\n\nI travel on this route every "
                   "weekday morning, together with a large number of "
                   "residents from the Green Park area. Removing the "
                   "stop would mean a walk of one and a half "
                   "kilometres in each direction, which is a serious "
                   "difficulty for elderly passengers and for parents "
                   "taking small children to school, particularly "
                   "during the winter months. Reducing the service to "
                   "one bus an hour would make the journey "
                   "unreliable as well as longer.\n\nI would "
                   "therefore urge you to reconsider, or at least to "
                   "keep the Green Park stop during morning and evening peak "
                   "hours, when demand is at its highest.\n\nI look "
                   "forward to your reply.\n\nYours faithfully,",
    },
    {
        "id": "p1_course",
        "topic": "Til kursi",
        "type": "complaint",
        "context_from": "the language school you attend",
        "context": "Dear Student,\nYour evening English group will be "
                   "merged with another class from next week. The new "
                   "group will have 28 students and will be taught by "
                   "a different teacher. Lessons will move from "
                   "Tuesday and Thursday to Saturday morning.\nAcademic "
                   "Office",
        "t11": {
            "prompt": "Write a short letter to a friend from the same "
                      "group. Explain what is happening and how you "
                      "feel.",
            "bullets": [
                {"label": "explain the changes",
                 "keys": [["merg", "join", "28", "big", "teacher",
                           "saturday", "chang", "class"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the academic office.",
            "bullets": [
                {"label": "say which group you are in and why you chose it",
                 "keys": [["group", "class", "chose", "enrol", "join",
                           "evening", "because"]]},
                {"label": "explain why the changes are unsuitable",
                 "keys": [["problem", "large", "28", "saturday",
                           "work", "unable", "difficult", "attention"]]},
                {"label": "say what you would like to happen",
                 "keys": [["would like", "request", "refund", "keep",
                           "transfer", "suggest", "ask", "hope"]]},
            ],
        },
        "model11": "Hi Rustam,\n\nHow are you? Did you get the email "
                   "from the school? They're merging our group with "
                   "another one — 28 students in one class! — and "
                   "we're getting a new teacher. Lessons are moving "
                   "to Saturday morning as well.\n\nI'm really not "
                   "happy about it. I chose the evening class "
                   "because I work on Saturdays.\n\nAre you going to "
                   "stay? Let me know what you think.\n\nBest,\nNilufar",
        "model12": "Dear Sir or Madam,\n\nI am writing about the "
                   "changes to Evening Group B4, which I joined in "
                   "September.\n\nI chose this course specifically "
                   "because it was a small evening group of twelve "
                   "students, which allowed each of us regular "
                   "speaking practice. A class of twenty-eight cannot "
                   "offer the same, and moving the lessons to "
                   "Saturday morning makes attendance impossible for "
                   "those of us who work at weekends. Neither change "
                   "was mentioned when I paid for the full course.\n\n"
                   "I would therefore like to request a transfer to "
                   "another evening group, or, if that is not "
                   "possible, a refund of the fees for the remaining lessons. "
                   "I would be glad to discuss either option in "
                   "person.\n\n"
                   "Thank you for your attention to this matter.\n\n"
                   "Yours faithfully,",
    },
    {
        "id": "p1_dorm",
        "topic": "Yotoqxona",
        "type": "request",
        "context_from": "the student accommodation office",
        "context": "Dear Resident,\nThe student kitchen on the third "
                   "floor will be closed for renovation for six "
                   "weeks. Residents should use the kitchen on the "
                   "ground floor, which is shared by 60 students. "
                   "Rent will not be reduced during this period.\n"
                   "Accommodation Office",
        "t11": {
            "prompt": "Write a short letter to a friend in another "
                      "dormitory. Explain the situation and how you "
                      "feel.",
            "bullets": [
                {"label": "explain the situation",
                 "keys": [["kitchen", "clos", "renovat", "six", "week",
                           "ground", "60", "shar"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the accommodation office.",
            "bullets": [
                {"label": "explain the practical problem",
                 "keys": [["queue", "wait", "crowd", "60", "sixty",
                           "problem", "difficult", "cook", "time"]]},
                {"label": "mention the rent",
                 "keys": [["rent", "pay", "fee", "cost", "money",
                           "reduc", "charg"]]},
                {"label": "suggest what could be done",
                 "keys": [["suggest", "propose", "could", "perhaps",
                           "microwave", "temporary", "schedul",
                           "recommend", "alternativ"]]},
            ],
        },
        "model11": "Hi Jasur,\n\nHope you're doing well. Our kitchen "
                   "is closing for six weeks for renovation, so all "
                   "of us have to use the ground-floor one — that's "
                   "sixty people sharing four cookers. And they're "
                   "not reducing the rent.\n\nI think it's completely "
                   "unfair, honestly. I waited forty minutes to cook "
                   "last night.\n\nHow are things in your block?\n\n"
                   "Take care,\nOtabek",
        "model12": "Dear Sir or Madam,\n\nI am writing about the "
                   "closure of the third-floor kitchen announced last "
                   "week.\n\nI understand that renovation is "
                   "necessary. In practice, however, sixty residents "
                   "are now sharing a kitchen designed for twenty, "
                   "and waiting times of thirty to forty minutes in "
                   "the evening have become normal. For students with "
                   "early lectures this is a genuine difficulty.\n\n"
                   "I was also surprised that the rent remains "
                   "unchanged, although one of the facilities we pay "
                   "for is unavailable for six weeks.\n\nI would like "
                   "to suggest two measures: placing two additional "
                   "microwaves in the ground-floor kitchen, and "
                   "offering a small reduction in rent for the "
                   "affected floor for as long as the work continues.\n\n"
                   "Thank you for your "
                   "consideration.\n\nYours faithfully,",
    },
    {
        "id": "p1_job",
        "topic": "Ish o'rni",
        "type": "application",
        "context_from": "a notice on your college website",
        "context": "SUMMER STAFF WANTED\nThe City Museum is looking "
                   "for student guides for July and August. Duties "
                   "include leading short tours in English and helping "
                   "visitors. Applicants should have good "
                   "communication skills and an interest in history. "
                   "Write to the Education Manager.",
        "t11": {
            "prompt": "Write a short letter to a friend telling them "
                      "about this opportunity and how you feel about "
                      "applying.",
            "bullets": [
                {"label": "explain the opportunity",
                 "keys": [["museum", "guid", "job", "summer", "july",
                           "august", "tour", "work"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the Education Manager of the "
                      "museum.",
            "bullets": [
                {"label": "say which position you are applying for",
                 "keys": [["apply", "position", "post", "guide",
                           "summer", "advertis"]]},
                {"label": "describe your relevant experience and skills",
                 "keys": [["experience", "worked", "helped", "led",
                           "organis", "english", "skill", "volunteer",
                           "last year", "school"]]},
                {"label": "say when you are available",
                 "keys": [["available", "free", "july", "august",
                           "from", "start", "any time"]]},
            ],
        },
        "model11": "Hi Shahzod,\n\nHow are you? I've just seen "
                   "something on the college website — the City "
                   "Museum wants student guides for July and August, "
                   "giving short tours in English.\n\nI'm quite "
                   "excited about it, although I'm a bit nervous "
                   "about speaking in front of groups.\n\nWhy don't "
                   "you apply too? We could do it together!\n\n"
                   "Cheers,\nAzamat",
        "model12": "Dear Sir or Madam,\n\nI am writing to apply for "
                   "the position of student guide advertised on the "
                   "City College website.\n\nI am a second-year "
                   "student of History and English at City College. "
                   "Last summer I volunteered at the regional archive, "
                   "where I prepared short presentations about local "
                   "monuments for visiting school groups of up to "
                   "twenty children. Through this work I learnt how "
                   "to explain historical material simply and how to "
                   "keep a group's attention. My English is at B2 "
                   "level and I have taken part in two public "
                   "speaking competitions.\n\nI am available "
                   "throughout July and August, including weekends, "
                   "including weekends, and I could begin as early as the first "
                   "week of July. I have attached my CV and a "
                   "reference from the archive.\n\nI would welcome the "
                   "opportunity to attend an interview.\n\nYours "
                   "faithfully,",
    },
    {
        "id": "p1_delivery",
        "topic": "Onlayn buyurtma",
        "type": "complaint",
        "context_from": "an online shop",
        "context": "Dear Customer,\nYour order #7734 (one laptop bag, "
                   "black) was delivered on 4th May. We hope you are "
                   "satisfied. Please note that returns are accepted "
                   "within 14 days.\nCustomer Service",
        "t11": {
            "prompt": "The bag that arrived was the wrong colour and "
                      "the zip was broken. Write a short letter to "
                      "your friend explaining what happened and how "
                      "you feel.",
            "bullets": [
                {"label": "explain what happened",
                 "keys": [["bag", "wrong", "colour", "color", "zip",
                           "broken", "order", "arriv", "deliver"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the customer service "
                      "department.",
            "bullets": [
                {"label": "give your order details",
                 "keys": [["7734", "order", "4th may", "may",
                           "reference", "number"]]},
                {"label": "describe exactly what is wrong",
                 "keys": [["wrong", "colour", "color", "brown",
                           "grey", "zip", "broken", "damaged",
                           "instead"]]},
                {"label": "say what you want them to do",
                 "keys": [["replace", "refund", "return", "exchang",
                           "request", "would like", "collect"]]},
            ],
        },
        "model11": "Hi Laylo,\n\nHow are you? Remember that laptop "
                   "bag I ordered? It finally came yesterday — but "
                   "it's brown instead of black, and the zip is "
                   "broken.\n\nI'm so annoyed. I waited three weeks "
                   "for it and now I have to send it back.\n\nHave "
                   "you ever ordered from them? Let me know!\n\n"
                   "Take care,\nMadina",
        "model12": "Dear Sir or Madam,\n\nI am writing about order "
                   "number 7734, a black laptop bag, which was "
                   "delivered on 4th May.\n\nUnfortunately the item I "
                   "received does not match my order in two respects. "
                   "The bag is brown rather than black, and the main "
                   "zip is broken and cannot be closed. I have kept "
                   "the original packaging and can send photographs "
                   "if that would be helpful.\n\nAs the fault is not "
                   "mine, I would be grateful if you could send the "
                   "correct item and arrange collection of the "
                   "incorrect one at no cost to me. If the black "
                   "version is no longer in stock, I would prefer a "
                   "full refund rather than an alternative colour. I should add "
                   "that the fourteen-day return period began only "
                   "when the item reached me.\n\nI look forward to your prompt "
                   "reply.\n\nYours faithfully,",
    },
    {
        "id": "p1_wedding",
        "topic": "Tadbir",
        "type": "invitation",
        "close12": "sincere",
        "context_from": "your college students' union",
        "context": "Dear Student Representative,\nThe college is "
                   "holding its 20th anniversary evening on Saturday "
                   "12th May at 6 p.m. in the main hall. Each group "
                   "may invite one former teacher. Please write to "
                   "your chosen guest this week.\nStudents' Union",
        "t11": {
            "prompt": "Write a short letter to a classmate telling "
                      "them about the event and how you feel about it.",
            "bullets": [
                {"label": "explain the event",
                 "keys": [["anniversary", "20", "twent", "may",
                           "evening", "hall", "celebrat", "invit"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter inviting your former teacher to "
                      "the celebration.",
            "bullets": [
                {"label": "invite them and say what the event is",
                 "keys": [["invit", "anniversary", "celebrat",
                           "delighted", "pleasure", "event"]]},
                {"label": "give the date, time and place",
                 "keys": [["12", "may", "saturday", "six", "6 p",
                           "hall", "evening"]]},
                {"label": "say why you have chosen them",
                 "keys": [["because", "taught", "remember", "student",
                           "mean", "influence", "inspir", "years"]]},
            ],
        },
        "model11": "Hi Zilola,\n\nHope you're well! Did you hear "
                   "about the anniversary evening? It's on Saturday "
                   "12th May at six in the main hall — twenty years "
                   "of the college — and each group can invite one "
                   "old teacher.\n\nI'm really excited. I'm going to "
                   "write to Mr Karimov.\n\nWho will you invite? "
                   "Write back!\n\nBest,\nGulnora",
        "model12": "Dear Mr Karimov,\n\nOn behalf of Group 3B, I am "
                   "delighted to invite you to City College's "
                   "twentieth anniversary celebration.\n\nThe evening "
                   "will take place on Saturday 12th May at six "
                   "o'clock in the main hall. The programme includes "
                   "a short concert prepared by current students, a "
                   "photograph exhibition covering the college's "
                   "history, and dinner afterwards.\n\nWe have chosen "
                   "to invite you because you taught our group for "
                   "three years and many of us decided to continue "
                   "studying literature because of your lessons. "
                   "Several former students have already asked "
                   "whether you will be there.\n\nCould you let us "
                   "know by 5th May whether you are able to come? We "
                   "would be happy to arrange transport if "
                   "needed.\n\nWe very much hope to see you.\n\n"
                   "Yours sincerely,",
    },
    {
        "id": "p1_late",
        "topic": "Uzr",
        "type": "apology",
        # Ism ma'lum (Dr Nazarova) -> Yours sincerely.
        "close12": "sincere",
        "context_from": "your project supervisor",
        "context": "Dear Student,\nYou did not attend the project "
                   "review meeting on Tuesday and did not submit your "
                   "progress report. Both were required. Please "
                   "explain in writing before Friday.\nProject "
                   "Supervisor",
        "t11": {
            "prompt": "Write a short letter to your project partner "
                      "explaining what happened and how you feel.",
            "bullets": [
                {"label": "explain what happened",
                 "keys": [["miss", "meeting", "tuesday", "report",
                           "forgot", "ill", "could not", "couldn"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to your project supervisor.",
            "bullets": [
                {"label": "apologise",
                 "keys": [["apolog", "sorry", "regret"]]},
                {"label": "explain briefly what happened",
                 "keys": [["because", "ill", "hospital", "family",
                           "emergency", "unable", "reason", "due to"]]},
                {"label": "say what you will do now",
                 "keys": [["will", "submit", "attach", "friday",
                           "meet", "complete", "assure", "make up"]]},
            ],
        },
        "model11": "Hi Bekzod,\n\nI'm so sorry about Tuesday. My "
                   "little brother was taken to hospital on Monday "
                   "night and I was there until the next evening — I "
                   "completely forgot to message anyone about the "
                   "meeting or the report.\n\nI feel awful about "
                   "leaving you to explain everything on your own.\n\n"
                   "I'll finish my part tonight and send it over. Sorry "
                   "again!\n\nTake care,\n"
                   "Bekhzod",
        "model12": "Dear Dr Nazarova,\n\nI am writing to apologise "
                   "sincerely for missing Tuesday's project review "
                   "and for failing to submit my progress report.\n\n"
                   "On Monday evening my younger brother was taken to "
                   "hospital, and I remained with my family until "
                   "late on Tuesday. I should have sent a message "
                   "before the meeting, and I fully accept that not "
                   "doing so left both you and my project partner "
                   "without an explanation.\n\nI have now completed "
                   "the report and have attached it to this letter. "
                   "I would also be grateful for the opportunity to "
                   "present my section at your convenience this week, "
                   "and I can assure you that I will inform you "
                   "immediately should any similar situation "
                   "arise.\n\nThank you for your understanding.\n\n"
                   "Yours sincerely,",
    },
    {
        "id": "p1_nurse",
        "topic": "Minnatdorchilik",
        "type": "thanks",
        "context_from": "the city hospital",
        "context": "Dear Patient,\nWe hope you have recovered well "
                   "after your recent stay in Ward 6. If you would "
                   "like to comment on the care you received, please "
                   "write to the Hospital Director.\nPatient "
                   "Services",
        "t11": {
            "prompt": "Write a short letter to a friend about the care "
                      "you received and how you feel about it.",
            "bullets": [
                {"label": "explain what happened",
                 "keys": [["hospital", "ward", "nurse", "operat",
                           "ill", "stay", "care", "week"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the Hospital Director.",
            "bullets": [
                {"label": "say who you are thanking and why",
                 "keys": [["thank", "grateful", "nurse", "staff",
                           "doctor", "ward", "express"]]},
                {"label": "describe what happened",
                 "keys": [["when", "night", "day", "operation",
                           "stayed", "helped", "admitted", "after"]]},
                {"label": "suggest how the hospital could recognise them",
                 "keys": [["recognis", "recogniz", "reward", "pass on",
                           "award", "mention", "hope", "team"]]},
            ],
        },
        "model11": "Hi Farrux,\n\nI'm finally home! I spent five days "
                   "in Ward 6 after the operation and honestly the "
                   "nurses there were incredible — one of them stayed "
                   "with me half the night when I couldn't sleep.\n\n"
                   "I feel so lucky. I was really frightened going "
                   "in.\n\nI'll call you at the weekend!\n\nTake "
                   "care,\nShohruh",
        "model12": "Dear Sir or Madam,\n\nI am writing to express my "
                   "sincere thanks to the nursing team of Ward 6, and "
                   "in particular to Nurse Ergasheva.\n\nI was "
                   "admitted for surgery on 3rd April and stayed for "
                   "five days. On my first night I was in "
                   "considerable pain and, being far from my family, "
                   "very frightened. Nurse Ergasheva sat with me for "
                   "almost an hour after her shift had ended, "
                   "explained clearly what would happen the following "
                   "morning, and checked on me twice more before she "
                   "left.\n\nIt is rare to meet such kindness "
                   "combined with such professionalism, and it made a "
                   "real difference to my recovery.\n\nI do hope the "
                   "hospital will find a way to recognise her work, "
                   "and I would be grateful if you could pass on my "
                   "thanks to the whole team.\n\nYours faithfully,",
    },
    {
        "id": "p1_flat",
        "topic": "Ijara",
        "type": "complaint",
        "context_from": "your landlord",
        "context": "Dear Tenant,\nFrom next month the rent will "
                   "increase by 20%. Please also note that the "
                   "heating repair you requested in November has been "
                   "postponed until the spring.\nProperty "
                   "Management",
        "t11": {
            "prompt": "Write a short letter to a friend explaining the "
                      "situation and how you feel about it.",
            "bullets": [
                {"label": "explain the situation",
                 "keys": [["rent", "20", "increase", "heating",
                           "repair", "postpon", "spring", "cold"]]},
                {"label": "say how you feel",
                 "keys": [_FEEL]},
            ],
        },
        "t12": {
            "prompt": "Write a letter to the property management "
                      "company.",
            "bullets": [
                {"label": "refer to their letter and your tenancy",
                 "keys": [["letter", "tenant", "flat", "rent", "since",
                           "year", "living", "contract"]]},
                {"label": "explain why the two decisions together are "
                          "unacceptable",
                 "keys": [["heating", "cold", "winter", "repair",
                           "increase", "unaccept", "unfair", "same "
                           "time", "while"]]},
                {"label": "state what action you expect",
                 "keys": [["expect", "request", "repair", "fix",
                           "before", "postpone", "reduce", "would like"]]},
            ],
        },
        "model11": "Hi Doniyor,\n\nYou won't believe this. The "
                   "landlord is putting the rent up by 20% from next "
                   "month, and in the same letter he says the heating "
                   "repair I asked for in November is postponed until "
                   "spring.\n\nI'm furious, honestly. It's been ten "
                   "degrees in my room all winter.\n\nDo you know "
                   "anyone who deals with tenants' rights?\n\nBest,\n"
                   "Ulugbek",
        "model12": "Dear Sir or Madam,\n\nI am writing in response to "
                   "your letter of 3rd February concerning the flat "
                   "at 14 Bog'ishamol Street, which I have rented for "
                   "two years.\n\nI find it difficult to accept the "
                   "two decisions in the same letter. I reported the "
                   "faulty heating in November, and the temperature "
                   "in the bedroom has not risen above twelve degrees "
                   "since then. To postpone that repair until the "
                   "spring, when the cold weather will have passed, "
                   "while at the same time raising the rent by twenty "
                   "per cent, does not seem reasonable.\n\nI would "
                   "therefore ask you to carry out the heating repair "
                   "within the next two weeks, and to delay any "
                   "increase until the property is in full working "
                   "order.\n\nI look forward to your reply.\n\nYours "
                   "faithfully,",
    },
]

# =================================================================
#  PART 2 — C1, 180-200 so'z, 30 daqiqa
# =================================================================

PART2: list[dict] = [
    {
        "id": "p2_lunch", "type": "forum",
        "prompt": "You are participating in an online discussion for "
                  "learners. The question is: Should schools provide "
                  "lunch for students, or should students bring their "
                  "own food from home? Post your response, giving "
                  "reasons and examples.",
        "model": "This question comes up in almost every parents' "
                 "meeting I have attended, and my answer has not "
                 "changed: schools should provide lunch.\n\nThe most "
                 "important reason is equality. When every child eats "
                 "the same meal, no one is judged for what is in "
                 "their lunchbox. In my cousin's school a free lunch "
                 "scheme was introduced two years ago, and teachers "
                 "noticed almost immediately that children who used "
                 "to sit alone at lunchtime began joining the "
                 "others.\n\nA second point concerns nutrition. Left "
                 "to themselves, many families rely on crisps and "
                 "biscuits simply because mornings are rushed. A "
                 "school kitchen, by contrast, works to a planned "
                 "menu.\n\nOf course, some parents argue that school "
                 "food is expensive and that children should learn "
                 "independence by preparing their own meals. It is a "
                 "fair concern. However, independence can be taught "
                 "in many other ways, and the cost of school meals is "
                 "far lower than the long-term cost of poor eating "
                 "habits.\n\nOn balance, the school canteen does more "
                 "than feed children: it quietly removes a daily "
                 "source of inequality that no child should ever have to "
                 "notice in the first place.",
    },
    {
        "id": "p2_homework", "type": "forum",
        "prompt": "You are taking part in an online discussion. The "
                  "question is: Some people believe homework should be "
                  "abolished in primary schools, while others say it "
                  "builds discipline. What is your view? Give reasons "
                  "and examples.",
    },
    {
        "id": "p2_remote", "type": "forum",
        "prompt": "You are participating in an online discussion for "
                  "young professionals. The question is: Is working "
                  "from home better for employees than working in an "
                  "office? Give reasons and examples.",
    },
    {
        "id": "p2_uniform", "type": "forum",
        "prompt": "An online forum is discussing school uniforms. The "
                  "question is: Should schools require students to "
                  "wear a uniform? Post your response with reasons and "
                  "examples.",
    },
    {
        "id": "p2_phones", "type": "forum",
        "prompt": "You are taking part in an online discussion. The "
                  "question is: Should mobile phones be banned in "
                  "schools completely, or should students be taught "
                  "to use them responsibly? Give reasons and examples.",
    },
    {
        "id": "p2_free_transport", "type": "forum",
        "prompt": "An online discussion asks: Should public transport "
                  "be free for everyone in large cities? Post your "
                  "response, giving reasons and examples.",
    },
    {
        "id": "p2_habit", "type": "blog",
        "prompt": "You have decided to write a post for your blog "
                  "about a habit you changed and what you learnt from "
                  "it. Write your blog post.",
        "model": "Three months ago I deleted every social media app "
                 "from my phone. My friends were convinced I would "
                 "last a week.\n\nIt started when I checked my screen "
                 "time one Sunday evening and found I had spent over "
                 "five hours scrolling that day alone. Five hours. I "
                 "remember sitting there and feeling slightly "
                 "sick.\n\nThe first few days were genuinely "
                 "uncomfortable. I kept reaching for a phone that had "
                 "nothing to show me. But by the second week "
                 "something shifted: I finished a novel I had been "
                 "carrying around for a year, and I started sleeping "
                 "properly for the first time in months.\n\nLooking "
                 "back, the lesson was not really about social media "
                 "at all. It was about how easily I let a habit make "
                 "decisions on my behalf without ever choosing "
                 "it.\n\nHave you ever tried cutting something out "
                 "for a month? I'd genuinely like to know how it "
                 "went.\n\nI am not going to pretend it was easy, or that I "
                 "have never reinstalled a single app since. But I "
                 "decide when I open it now, rather than the other "
                 "way round, and that small difference has been "
                 "worth far more than three quiet months.",
    },
    {
        "id": "p2_travel", "type": "blog",
        "prompt": "Write a post for your blog about a journey that "
                  "did not go as planned, and what you learnt from it.",
    },
    {
        "id": "p2_firstjob", "type": "blog",
        "prompt": "Write a blog post about your first day at a new "
                  "job or school, and the advice you would give "
                  "someone in the same situation.",
    },
    {
        "id": "p2_failure", "type": "blog",
        "prompt": "Write a post for your blog about a time you failed "
                  "at something and what the experience taught you.",
    },
    {
        "id": "p2_hometown", "type": "blog",
        "prompt": "Write a blog post about a change in your home town "
                  "over the last ten years and how you feel about it.",
    },
    {
        "id": "p2_revision", "type": "article",
        "prompt": "Write an article for your college website about "
                  "why so many students struggle to revise "
                  "effectively, and what they can do about it.",
        "model": "Why Re-reading Your Notes Doesn't Work\n\nAsk any "
                 "student how they revise, and most will describe the "
                 "same routine: open the notes, read them through, "
                 "highlight a few lines, repeat. It feels productive. "
                 "The problem is that it rarely is.\n\nThere are two "
                 "reasons for this. The first is that re-reading "
                 "creates a comfortable sense of familiarity, which "
                 "the brain mistakes for knowledge. The second is "
                 "timing: most revision happens in one long session "
                 "the night before, when tired minds absorb very "
                 "little.\n\nThe good news is that the fix costs "
                 "nothing. Close the book and try to write down what "
                 "you remember; the gaps you find are exactly what "
                 "you need to study. Then spread the same material "
                 "over three short sessions rather than one long "
                 "one.\n\nRevision, in other words, should feel "
                 "slightly difficult. If it feels easy, it probably "
                 "isn't working.\n\nNone of this needs an app, a course or a "
                 "new notebook. It needs only a willingness to be "
                 "wrong in private, several weeks before you risk "
                 "being wrong in an examination hall, when it finally "
                 "counts.",
    },
    {
        "id": "p2_volunteer", "type": "article",
        "prompt": "Write an article for a student magazine about why "
                  "young people should volunteer, and how they can "
                  "start.",
    },
    {
        "id": "p2_sleep", "type": "article",
        "prompt": "Write an article for your college website about "
                  "why students do not get enough sleep and what can "
                  "be done about it.",
    },
    {
        "id": "p2_money", "type": "article",
        "prompt": "Write an article for a student website about the "
                  "money mistakes students make and how to avoid them.",
    },
    {
        "id": "p2_reading", "type": "article",
        "prompt": "Write an article for your college magazine about "
                  "why fewer young people read books, and what might "
                  "change that.",
    },
    {
        "id": "p2_ai", "type": "forum",
        "prompt": "An online forum is discussing technology in "
                  "education. The question is: Do translation and "
                  "writing tools help language learners, or do they "
                  "slow them down? Give reasons and examples.",
    },
    {
        "id": "p2_city", "type": "forum",
        "prompt": "You are taking part in an online discussion. The "
                  "question is: Is it better to grow up in a large "
                  "city or in a small town? Give reasons and examples.",
    },
]


# =================================================================
#  AVTOMAT TEKSHIRGICH
#
#  NEGA KERAK. AI baho har doim ham ishlamaydi (kalit, tarmoq,
#  limit). Lekin o'quvchi javob YOZGANDA darrov aniq javob olishi
#  shart, aks holda mashq ma'nosini yo'qotadi.
#
#  Shuning uchun bu yerda AI'siz, sof qoida asosida ishlaydigan
#  tekshiruv bor. U eng ko'p ball yo'qotiladigan narsalarni
#  tutadi:
#    - so'z soni oralig'i
#    - topshiriq bandlaridan birortasi umuman yozilmagani
#    - noto'g'ri ochilish/yopilish juftligi
#    - rasmiy xatda qisqartma va so'zlashuv so'zlari
#    - abzatslarga bo'linmagan bir bo'lak matn
#
#  Bu inson o'rnini bosmaydi, lekin "yozdim va hech kim ko'rmadi"
#  holatini yo'q qiladi.
# =================================================================
import re as _re

_CONTRACTIONS = [
    "i'm", "i've", "i'd", "i'll", "don't", "doesn't", "didn't",
    "can't", "won't", "wouldn't", "couldn't", "shouldn't", "isn't",
    "aren't", "wasn't", "weren't", "it's", "that's", "there's",
    "we're", "they're", "you're", "haven't", "hasn't", "hadn't",
    "let's", "we've", "you've", "we'll", "you'll", "they'll",
]

_SLANG = [
    "guys", "kids", "stuff", "loads of", "a lot of", "mad", "cool",
    "awesome", "gonna", "wanna", "kinda", "mate", "fancy", "huge",
    "thanks a million", "no way", "big time", "hi there", "yeah",
    "ok,", "okay,", "super ", "pretty much",
]

_TOO_FORMAL = [
    "yours faithfully", "yours sincerely", "dear sir", "dear madam",
    "i am writing to inform", "i would be grateful if you could",
    "please find enclosed", "with regard to", "i look forward to "
    "hearing from you", "i wish to apply", "to whom it may concern",
    "please accept my sincere apologies", "should you require",
]

_INFORMAL_CLOSE = [
    "take care", "best wishes", "best,", "see you", "cheers",
    "love,", "all the best", "talk soon", "write back", "bye",
    "lots of love", "speak soon",
]


def words_of(text: str) -> list[str]:
    return _re.findall(r"[A-Za-z][A-Za-z'’-]*", text or "")


def paragraphs_of(text: str) -> list[str]:
    parts = [p.strip() for p in _re.split(r"\n\s*\n", text or "")]
    if len(parts) < 2:
        parts = [p.strip() for p in (text or "").split("\n")]
    return [p for p in parts if p]


def _sentences(text: str) -> list[str]:
    s = [x.strip() for x in _re.split(r"[.!?]+", text or "")]
    return [x for x in s if len(x.split()) > 1]


def _has(low: str, needle: str) -> bool:
    """So'z chegarasi bilan qidirish.

    2026-08-26 TUZATISH. Avval oddiy `in` ishlatilgan edi va u
    "Dear Sir or MADam" ichidan "mad" ni, "estiMATEd" ichidan
    "mate" ni topib, namunaviy rasmiy xatlarni ham "so'zlashuv
    uslubi" deb belgilab qo'ygan edi. Test shu xatoni tutdi.
    """
    if not needle.strip():
        return False
    pat = r"(?<![A-Za-z])" + _re.escape(needle) + r"(?![A-Za-z])"
    return _re.search(pat, low) is not None


def check(text: str, spec: dict) -> dict:
    """Matnni topshiriq talablariga solishtiradi.

    Qaytaradi: {"score": 0-100, "words": n, "checks": [...]}
    Har check: {"ok": True/False/None, "label": ..., "detail": ...}
    ok=None — ogohlantirish (ball tushirmaydi, lekin maslahat).
    """
    text = (text or "").strip()
    low = text.lower()
    ws = words_of(text)
    n = len(ws)
    paras = paragraphs_of(text)
    checks: list[dict] = []
    got = 0.0
    total = 0.0

    # --- 1. So'z soni ---------------------------------------
    lo, hi = spec.get("words", [120, 150])
    total += 25
    if n == 0:
        checks.append({"ok": False, "label": "So'z soni",
                       "detail": "Matn bo'sh."})
    elif lo <= n <= hi:
        got += 25
        checks.append({"ok": True, "label": "So'z soni",
                       "detail": f"{n} ta — talab {lo}-{hi}. To'g'ri."})
    elif n < lo:
        share = max(0.0, n / lo)
        got += 25 * share * 0.7
        checks.append({
            "ok": False, "label": "So'z soni",
            "detail": f"{n} ta — kamida {lo} ta kerak. Yetishmayapti: "
                      f"{lo - n} so'z. Kam yozish CEFRda eng ko'p ball "
                      f"yo'qotadigan xato."})
    else:
        over = n - hi
        got += 25 * (0.75 if over <= hi * 0.25 else 0.5)
        checks.append({
            "ok": None, "label": "So'z soni",
            "detail": f"{n} ta — chegara {hi}. {over} so'z ortiqcha. "
                      f"Imtihonda vaqt yetmay qolishi mumkin; "
                      f"ortiqcha so'z ball qo'shmaydi."})

    # --- 2. Topshiriq bandlari ------------------------------
    bl = spec.get("bullets") or []
    if bl:
        total += 30
        miss = []
        for b in bl:
            hit = any(any(k in low for k in grp) for grp in b["keys"])
            if not hit:
                miss.append(b["label"])
        cov = (len(bl) - len(miss)) / len(bl)
        got += 30 * cov
        if not miss:
            checks.append({"ok": True, "label": "Topshiriq bandlari",
                           "detail": f"Hamma {len(bl)} band yoritilgan."})
        else:
            checks.append({
                "ok": False, "label": "Topshiriq bandlari",
                "detail": "Yoritilmagan band: "
                          + "; ".join(miss)
                          + ". Har band alohida baholanadi — biri "
                            "tushib qolsa ball darrov tushadi."})

    # --- 3. Ochilish ----------------------------------------
    reg = spec.get("register", "formal")
    total += 10
    first = (paras[0] if paras else "").lower()
    if reg == "formal":
        if first.startswith("dear "):
            got += 10
            checks.append({"ok": True, "label": "Ochilish",
                           "detail": "Rasmiy salomlashish bor."})
        else:
            checks.append({
                "ok": False, "label": "Ochilish",
                "detail": "Rasmiy xat 'Dear Sir or Madam,' yoki "
                          "'Dear Mr/Ms + familiya,' bilan boshlanadi."})
    else:
        greet = _re.match(r"(hi|hey|hello|dear)\b", first)
        bad = first.startswith("dear sir") or first.startswith("dear madam")
        if greet and not bad:
            got += 10
            checks.append({"ok": True, "label": "Ochilish",
                           "detail": "Do'stona salomlashish bor."})
        else:
            checks.append({
                "ok": False, "label": "Ochilish",
                "detail": "Do'stga xat 'Hi + ism,' bilan boshlanadi. "
                          "'Dear Sir or Madam' bu yerda xato."})

    # --- 4. Yopilish ----------------------------------------
    total += 10
    want = spec.get("close", "any")
    has_f = "yours faithfully" in low
    has_s = "yours sincerely" in low
    has_i = any(c in low for c in _INFORMAL_CLOSE)
    if reg == "formal":
        if want == "faithful" and has_f:
            got += 10
            ok, det = True, "Dear Sir or Madam -> Yours faithfully. To'g'ri."
        elif want == "sincere" and has_s:
            got += 10
            ok, det = True, "Dear + ism -> Yours sincerely. To'g'ri."
        elif has_f or has_s or "kind regards" in low or "regards" in low:
            got += 6
            ok, det = None, (
                "Yopilish bor, lekin ochilishga MOS emas. Qoida: ism "
                "noma'lum -> Yours faithfully; ism ma'lum -> Yours "
                "sincerely.")
        else:
            ok, det = False, ("Rasmiy yopilish yo'q. 'Yours faithfully,' "
                              "yoki 'Yours sincerely,' yozilishi kerak.")
    else:
        if has_i and not (has_f or has_s):
            got += 10
            ok, det = True, "Do'stona yopilish bor."
        elif has_f or has_s:
            ok, det = False, ("Do'stga yozilgan xatda 'Yours faithfully' "
                              "ishlatilmaydi. 'Take care,' / 'Best,' / "
                              "'See you soon,' yozing.")
        else:
            ok, det = False, ("Yopilish yo'q. Do'stona xat 'Take care,' "
                              "kabi ibora bilan tugaydi.")
    checks.append({"ok": ok, "label": "Yopilish", "detail": det})

    # --- 5. Abzatslar ---------------------------------------
    need_p = spec.get("min_paras", 3)
    total += 10
    if len(paras) >= need_p:
        got += 10
        checks.append({"ok": True, "label": "Abzatslar",
                       "detail": f"{len(paras)} ta abzats — yaxshi "
                                 f"tuzilma."})
    else:
        got += 10 * (len(paras) / max(1, need_p))
        checks.append({
            "ok": False, "label": "Abzatslar",
            "detail": f"{len(paras)} ta abzats — kamida {need_p} ta "
                      f"kerak. Bir bo'lak matn o'qishga qiyin va "
                      f"'tuzilma' mezonidan ball tushiradi."})

    # --- 6. Uslub -------------------------------------------
    total += 15
    if reg == "formal":
        bad = [c for c in _CONTRACTIONS if _has(low, c)]
        bad += [s for s in _SLANG if _has(low, s.rstrip(", "))]
        if not bad:
            got += 15
            checks.append({"ok": True, "label": "Uslub",
                           "detail": "Rasmiy uslub saqlangan."})
        else:
            got += max(0.0, 15 - 4 * len(bad))
            checks.append({
                "ok": False, "label": "Uslub",
                "detail": "Rasmiy xatga mos kelmaydigan so'zlar: "
                          + ", ".join(sorted(set(bad))[:6])
                          + ". Qisqartma o'rniga to'liq shakl yozing "
                            "(I'm -> I am, don't -> do not)."})
    else:
        bad = [s for s in _TOO_FORMAL if _has(low, s)]
        if not bad:
            got += 15
            checks.append({"ok": True, "label": "Uslub",
                           "detail": "Do'stona uslub saqlangan."})
        else:
            got += max(0.0, 15 - 5 * len(bad))
            checks.append({
                "ok": False, "label": "Uslub",
                "detail": "Do'stga xatda juda rasmiy iboralar bor: "
                          + ", ".join(sorted(set(bad))[:4])
                          + ". Oddiyroq yozing."})

    # --- Maslahatlar (ball tushirmaydi) ---------------------
    if n >= 40:
        cw = [w.lower() for w in ws if len(w) > 4]
        if cw:
            top = max(set(cw), key=cw.count)
            if cw.count(top) >= 5:
                checks.append({
                    "ok": None, "label": "Takrorlanish",
                    "detail": f"'{top}' so'zi {cw.count(top)} marta "
                              f"takrorlangan. Sinonim ishlating — "
                              f"lug'at boyligi alohida baholanadi."})
        sents = _sentences(text)
        if len(sents) >= 4:
            lens = [len(s.split()) for s in sents]
            if max(lens) - min(lens) < 5:
                checks.append({
                    "ok": None, "label": "Gap tuzilishi",
                    "detail": "Gaplaringiz bir xil uzunlikda. Qisqa va "
                              "uzun gaplarni almashtirib yozing — bu "
                              "grammatika bahosini ko'taradi."})
            if sum(lens) / len(lens) > 28:
                checks.append({
                    "ok": None, "label": "Gap tuzilishi",
                    "detail": "Gaplar juda uzun (o'rtacha "
                              f"{sum(lens)//len(lens)} so'z). Uzun gapda "
                              "grammatik xato ehtimoli oshadi."})

    score = int(round(100 * got / total)) if total else 0
    return {"score": score, "words": n, "paras": len(paras),
            "checks": checks}


def spec_for(part: str, task: dict) -> dict:
    """Topshiriqdan tekshiruv talablarini yig'adi."""
    if part == "1.1":
        return {"words": [45, 70], "register": "informal",
                "close": "informal", "min_paras": 3,
                "bullets": task["t11"]["bullets"]}
    if part == "1.2":
        # Yopilish TOPSHIRIQDA belgilanadi: ism berilgan bo'lsa
        # sincere, aks holda faithful. Avval bu tur bo'yicha
        # taxmin qilinardi va "Dear Dr Nazarova" li uzr xati
        # noto'g'ri baholangan edi — test tutdi.
        close = task.get("close12", "faithful")
        return {"words": [120, 150], "register": "formal",
                "close": close, "min_paras": 4,
                "bullets": task["t12"]["bullets"]}
    return {"words": [180, 200], "register": "essay",
            "close": "any", "min_paras": 4, "bullets": []}


def check_part2(text: str, kind: str = "forum") -> dict:
    """Part 2 — xat emas, shuning uchun boshqa mezonlar.

    2026-08-26 TUZATISH. Avval uchala turga ham BIR XIL mezon
    qo'llanilgan edi va namunaviy blog hamda maqola "qarshi fikr
    yo'q" deb past baholangan edi. Test shu xatoni tutdi.

    Aslida uchala janrning C1 belgisi HAR XIL:
      forum   -> qarshi fikrni tan olib, rad etish
      blog    -> voqeadan UMUMIY xulosa + o'quvchiga murojaat
      article -> sabab tahlili + amaliy yechim
    Endi har biri o'z mezoni bilan tekshiriladi.
    """
    text = (text or "").strip()
    low = text.lower()
    ws = words_of(text)
    n = len(ws)
    paras = paragraphs_of(text)
    checks, got, total = [], 0.0, 0.0

    # --- so'z soni (hamma turga bir xil) ---------------------
    total += 30
    if 180 <= n <= 200:
        got += 30
        checks.append({"ok": True, "label": "So'z soni",
                       "detail": f"{n} ta — talab 180-200. To'g'ri."})
    elif n < 180:
        got += 30 * max(0.0, n / 180) * 0.7
        checks.append({"ok": False, "label": "So'z soni",
                       "detail": f"{n} ta — kamida 180 kerak "
                                 f"({180 - n} so'z yetishmayapti)."})
    else:
        got += 30 * 0.75
        checks.append({"ok": None, "label": "So'z soni",
                       "detail": f"{n} ta — 200 dan {n - 200} ta ortiq. "
                                 f"Vaqtingizni yeydi."})

    # --- janrga xos ASOSIY mezon ----------------------------
    if kind == "blog":
        total += 25
        lesson = ["looking back", "i learnt", "i learned", "taught me",
                  "the lesson", "i realised", "i realized", "what i "
                  "would", "if there is one thing", "now i know",
                  "in the end", "since then", "changed the way"]
        if any(l in low for l in lesson):
            got += 25
            checks.append({"ok": True, "label": "Xulosa",
                           "detail": "Voqeadan umumiy xulosa chiqarilgan "
                                     "— blogni C1 darajaga ko'taradigan "
                                     "asosiy narsa."})
        else:
            checks.append({
                "ok": False, "label": "Xulosa",
                "detail": "Faqat hikoya qilingan. C1 uchun voqeadan "
                          "UMUMIY saboq chiqarish shart: 'Looking back, "
                          "what I learnt was...'"})
        total += 25
        reader = ["have you", "let me know", "what about you", "would you",
                  "i'd love to hear", "i would love to hear", "comment",
                  "do you", "tell me", "?"]
        if any(r in low for r in reader):
            got += 25
            checks.append({"ok": True, "label": "O'quvchiga murojaat",
                           "detail": "O'quvchiga savol berilgan — blog "
                                     "janrining belgisi."})
        else:
            checks.append({
                "ok": False, "label": "O'quvchiga murojaat",
                "detail": "Blogda o'quvchiga murojaat bo'lishi kerak: "
                          "'Have you ever tried...?'"})
    elif kind == "article":
        total += 25
        cause = ["the reason", "reasons for", "part of the problem",
                 "this happens because", "the first is", "one cause",
                 "why this", "because", "the problem is"]
        if any(c in low for c in cause):
            got += 25
            checks.append({"ok": True, "label": "Sabab tahlili",
                           "detail": "Muammoning sababi tahlil qilingan."})
        else:
            checks.append({
                "ok": False, "label": "Sabab tahlili",
                "detail": "Maqolada muammo NEGA yuz berayotgani "
                          "tushuntirilishi kerak."})
        total += 25
        fix = ["the good news", "try ", "start ", "one approach",
               "instead of", "should", "could", "solution", "advice",
               "tip", "what you can do", "the fix", "it helps to"]
        if any(f in low for f in fix):
            got += 25
            checks.append({"ok": True, "label": "Amaliy yechim",
                           "detail": "Amaliy maslahat berilgan — "
                                     "maqolaning qiymati shunda."})
        else:
            checks.append({
                "ok": False, "label": "Amaliy yechim",
                "detail": "Faqat muammo aytilgan, yechim yo'q. Maqola "
                          "o'quvchiga nima qilishni aytishi kerak."})
    else:  # forum
        total += 25
        counter = ["however", "although", "some people argue", "it is true",
                   "admittedly", "on the other hand", "of course, some",
                   "critics", "opponents", "while this", "nevertheless",
                   "even so", "granted", "that said"]
        if any(c in low for c in counter):
            got += 25
            checks.append({"ok": True, "label": "Qarshi fikr",
                           "detail": "Qarshi fikr tan olingan — bu C1 "
                                     "darajaning asosiy belgisi."})
        else:
            checks.append({
                "ok": False, "label": "Qarshi fikr",
                "detail": "Qarshi fikr yo'q. C1 da faqat o'z fikringizni "
                          "aytish yetarli emas: qarshi tarafni tan olib "
                          "('Of course, some people argue that...'), keyin "
                          "rad eting ('However,...')."})
        total += 25
        example = ["for example", "for instance", "such as", "in my own",
                   "take, for", "last year", "in my school", "i remember",
                   "a friend of mine", "research shows", "studies",
                   "recently", "when i", "in my cousin", "i have seen",
                   "i once"]
        if any(e in low for e in example):
            got += 25
            checks.append({"ok": True, "label": "Misol",
                           "detail": "Aniq misol keltirilgan."})
        else:
            checks.append({
                "ok": False, "label": "Misol",
                "detail": "Misol yo'q. Topshiriqda 'giving reasons and "
                          "examples' deb yozilgan — misolsiz dalil "
                          "baholanmaydi."})

    # --- tuzilma --------------------------------------------
    total += 20
    if len(paras) >= 4:
        got += 20
        checks.append({"ok": True, "label": "Tuzilma",
                       "detail": f"{len(paras)} ta abzats."})
    else:
        got += 20 * (len(paras) / 4)
        checks.append({"ok": False, "label": "Tuzilma",
                       "detail": f"{len(paras)} ta abzats — kamida 4 ta "
                                 f"kerak."})

    if n >= 60:
        cw = [w.lower() for w in ws if len(w) > 4]
        if cw:
            top = max(set(cw), key=cw.count)
            if cw.count(top) >= 6:
                checks.append({
                    "ok": None, "label": "Takrorlanish",
                    "detail": f"'{top}' {cw.count(top)} marta "
                              f"takrorlangan — sinonim qidiring."})

    return {"score": int(round(100 * got / total)), "words": n,
            "paras": len(paras), "checks": checks}
