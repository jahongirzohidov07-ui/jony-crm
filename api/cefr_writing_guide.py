# -*- coding: utf-8 -*-
"""CEFR MULTILEVEL WRITING — O'RGANISH QATLAMI (2026-08-26).

Jahongir: "Shu yerda CEFR Multilevel Writing yangi formati
ko'rsatilgan misoli bilan va alohida writing letter yozish bo'yicha
har xil letter turlarni ko'rsatilgan vazifa sen kuchli metodist
ustoz va pro dasturchi sifatida shu narsalarni shunday mukammal
qilib joylashtirginki CEFR writing yozishni o'rganish uchun bu qism
mukammal bo'lsin va skillarni improve qilish eng samarali bo'lsin."

METODIKA. Yozuv ko'nikmasi "yoz va yubor" bilan o'smaydi. Uch
qatlam kerak:
  1) O'RGANISH  — tuzilma, tayyor iboralar, IZOHLANGAN namuna.
  2) MASHQ      — mayda ko'nikmalar (register, ochilish-yopilish,
                  band qamrovi...) — bular AVTOMAT tekshiriladi.
  3) IMTIHON    — vaqt, so'z sanagichi, avtomat tekshiruv + AI
                  ekspert bahosi.
Shu fayl — BIRINCHI qatlam.

NEGA IZOHLANGAN NAMUNA. O'quvchi tayyor xatni o'qiydi-yu, "qaysi
gap nima ish qilyapti" degan savolga javob topolmaydi. Shuning
uchun har abzats yoniga UNING VAZIFASI va NEGA shundayligi
yozilgan. O'quvchi keyin o'z xatini shu qolipga solib ko'radi.

RASMIY FORMAT (Jahongirning jadvalidan):
  Part 1.1  B1  informal email   50 so'z      7 daqiqa
  Part 1.2  B2  formal email     120-150 so'z 23 daqiqa
  Part 2    C1  blog/forum/article 180-200    30 daqiqa

MUHIM. Yangi formatda 1.1 va 1.2 BITTA vaziyatdan kelib chiqadi:
bitta xabar keladi, o'quvchi avval do'stiga yozadi (norasmiy),
keyin rahbarga yozadi (rasmiy). Shuning uchun vazifalar ham
juftlab tuzilgan (cefr_writing_tasks.py).

MANBA. Xat turlari va rasmiy iboralar Doniyor Aslanovning "CEFR
Letter Writing" qo'llanmasidan (6 unit: thank-you, request,
application, complaint, invitation, apology) olindi va CEFR
Multilevel formatiga moslandi.
"""

# ---------------------------------------------------------------
#  QOLIP
#  steps  — abzatslar ketma-ketligi. Har qadamda: nima yoziladi,
#           NEGA kerak va tayyor iboralar.
#  model  — namuna xat. paras = [(vazifa, matn, izoh), ...]
#  must   — bo'lmasa ball tushadigan narsalar (avtomat tekshiriladi)
#  avoid  — eng ko'p uchraydigan xatolar
# ---------------------------------------------------------------

GUIDE: list[dict] = [

    # =========================================================
    #  PART 1.1 — B1 — NORASMIY XAT (do'stga)
    # =========================================================
    {
        "key": "informal",
        "part": "1.1",
        "level": "B1",
        "title": "Informal Email — do'stga xat",
        "words": [45, 60],
        "minutes": 7,
        "when": "1.1 qismda DOIM shu tur keladi: sizga xabar keladi "
                "(klub, maktab, ish joyidan), siz shu haqda "
                "do'stingizga yozasiz.",
        "idea": "Bu qismda til sodda bo'lishi KERAK. Rasmiy ibora "
                "ishlatsangiz — ball tushadi. Do'stingizga gapirgandek "
                "yozing, lekin 2 ta savolga aniq javob bering: nima "
                "bo'ldi va siz nima his qilyapsiz.",
        "steps": [
            {
                "name": "Salomlashish",
                "why": "Ismi bilan salomlashish — norasmiylik "
                       "belgisi. \"Dear Sir\" bu yerda XATO.",
                "phrases": ["Hi Aziz,", "Hey Nodira,", "Hi there,",
                            "Hello Bek,"],
            },
            {
                "name": "Ochilish (1 gap)",
                "why": "Do'stona kirish. Bu bir gap — ko'p vaqt "
                       "olmaydi, lekin xat quruq boshlanmaydi.",
                "phrases": ["How are you?", "Hope you're doing well.",
                            "Long time no see!",
                            "I hope everything's OK with you."],
            },
            {
                "name": "Xabar (2-3 gap)",
                "why": "Kelgan xabarni O'Z SO'ZINGIZ bilan aytasiz. "
                       "Ko'chirib yozish ball bermaydi.",
                "phrases": ["Guess what?", "I've just heard that...",
                            "Did you know that...?",
                            "They're going to...",
                            "Apparently, they want to..."],
            },
            {
                "name": "His-tuyg'u (1-2 gap)",
                "why": "Topshiriqda \"tell them how you feel\" deb "
                       "yozilgan — bu ALOHIDA band. Yozmasangiz "
                       "vazifa to'liq bajarilmaydi.",
                "phrases": ["I'm not happy about it.",
                            "To be honest, I think it's a bad idea.",
                            "I'm really excited about it!",
                            "It's a bit annoying, isn't it?",
                            "I don't mind, actually."],
            },
            {
                "name": "Yopilish",
                "why": "Qisqa va do'stona. \"Yours faithfully\" "
                       "bu yerda KULGILI ko'rinadi.",
                "phrases": ["Write back soon!", "Let me know what you think.",
                            "See you soon,", "Take care,", "Best,",
                            "Love,", "Cheers,"],
            },
        ],
        "model": {
            "task": "Your sports club is going to raise the monthly "
                    "fee. Write a short letter to your friend who "
                    "goes to the same club. Explain the situation "
                    "and tell them how you feel about it.",
            "paras": [
                ["Salomlashish", "Hi Kamron,",
                 "Ismi bilan — norasmiy. Vergul qo'yilgan."],
                ["Ochilish", "How are you? Hope you're fine.",
                 "Bir gaplik do'stona kirish."],
                ["Xabar", "Guess what? The club has just told us that "
                          "the monthly fee is going up from next month. "
                          "They say the new gym equipment costs a lot.",
                 "Xabar O'Z SO'ZI bilan aytilgan — nusxa emas. "
                 "Sabab ham qo'shilgan."],
                ["His-tuyg'u", "To be honest, I'm not happy about it. "
                               "It's already expensive for students like us.",
                 "\"how you feel\" bandi — aynan shu joyda bajarildi."],
                ["Yopilish", "What do you think? Write back soon!\nTake care,\nBobur",
                 "Savol bilan tugash — javob kutilayotganini bildiradi."],
            ],
            "words": 58,
        },
        "must": [
            "Ismi bilan salomlashish (Hi / Hey / Hello + ism)",
            "Xabarni o'z so'zingiz bilan aytish",
            "His-tuyg'uni ALOHIDA aytish",
            "Do'stona yopilish (Take care / Best / Cheers)",
        ],
        "avoid": [
            "\"Dear Sir or Madam\" — bu rasmiy xat emas",
            "\"Yours faithfully\" bilan tugatish",
            "Topshiriq matnini ko'chirib yozish",
            "50 so'z o'rniga 150 so'z yozish — vaqt yetmaydi",
        ],
    },

    # =========================================================
    #  PART 1.2 — B2 — RASMIY XAT TURLARI
    # =========================================================
    {
        "key": "request",
        "part": "1.2",
        "level": "B2",
        "title": "Request / Suggestion Letter — so'rov va taklif xati",
        "words": [120, 150],
        "minutes": 23,
        "when": "Biror narsani o'zgartirishni, kechiktirishni yoki "
                "ruxsat berishni so'raysiz. 1.2 da eng ko'p "
                "uchraydigan tur.",
        "idea": "So'rov — bu boshqa odamning vaqtiga da'vo. Shuning "
                "uchun ohang muloyim bo'lishi shart: \"I would like "
                "to suggest\", \"May I suggest\". \"You must change "
                "it\" deb yozsangiz — ball tushadi.",
        "steps": [
            {
                "name": "Salomlashish",
                "why": "Ism berilmagan bo'lsa — Dear Sir or Madam. "
                       "Madam'dan keyin VERGUL qo'yiladi.",
                "phrases": ["Dear Sir or Madam,",
                            "Dear Mr Brown,", "Dear Ms Lee,"],
            },
            {
                "name": "Maqsad (1-2 gap)",
                "why": "O'qiyotgan odam birinchi gapdanoq nima "
                       "istayotganingizni bilishi kerak.",
                "phrases": [
                    "I am writing to request...",
                    "I am writing with regard to...",
                    "I am writing on behalf of the students of Group 5.",
                    "I would like to draw your attention to...",
                ],
            },
            {
                "name": "Sabab (3-4 gap)",
                "why": "So'rov sababsiz bo'lmaydi. Aniq dalil "
                       "keltiring — sana, raqam, holat.",
                "phrases": [
                    "The reason for this is that...",
                    "As you may be aware,...",
                    "This is because...",
                    "The main difficulty is that...",
                    "Considering the fact that...",
                ],
            },
            {
                "name": "So'rov / taklif (2 gap)",
                "why": "Endi to'g'ridan-to'g'ri so'raysiz. Muloyim "
                       "shakl: would / could / I would suggest that.",
                "phrases": [
                    "I would therefore like to suggest that...",
                    "May I suggest that the event be postponed?",
                    "Would it be possible to...?",
                    "I would be grateful if you could...",
                    "My proposal is that...",
                ],
            },
            {
                "name": "Yopilish",
                "why": "Minnatdorchilik + javob kutish. Dear Sir or "
                       "Madam bilan boshlangan bo'lsa — Yours "
                       "faithfully.",
                "phrases": [
                    "Thank you for your time and consideration.",
                    "I look forward to hearing from you.",
                    "Yours faithfully,", "Yours sincerely,",
                ],
            },
        ],
        "model": {
            "task": "The English Department has decided to hold a "
                    "speech contest in late December, but your "
                    "classmates find that it is too near the final "
                    "examination. Write to the Dean to suggest a "
                    "change of the time.",
            "paras": [
                ["Salomlashish", "Dear Sir or Madam,",
                 "Ism berilmagan — shuning uchun Sir or Madam, vergul bilan."],
                ["Maqsad", "I am writing on behalf of the students of "
                           "Group 99-1 regarding the English speech "
                           "contest scheduled for 27th December.",
                 "Kim yozayotgani va nima haqda ekani BIRINCHI gapda."],
                ["Sabab", "We are all delighted that the department is "
                          "organising such an event, and most of us "
                          "would like to take part. However, according "
                          "to the school schedule, our final examinations "
                          "begin on 10th January. Preparing for both at "
                          "the same time would leave us very little time "
                          "for either.",
                 "Avval MAQTOV (muloyimlik), keyin muammo. Aniq "
                 "sanalar — dalil kuchli bo'ladi."],
                ["So'rov", "I would therefore like to suggest that the "
                           "contest be postponed until the first weeks "
                           "of the next term, when students generally "
                           "have more free time and would be able to "
                           "prepare properly. A later date would almost "
                           "certainly increase the number of "
                           "participants as well.",
                 "\"I would like to suggest that... be postponed\" — "
                 "eng muloyim shakl."],
                ["Yopilish", "Thank you for your time and consideration.\n"
                             "Yours faithfully,",
                 "Dear Sir or Madam bilan boshlandi -> Yours faithfully."],
            ],
            "words": 134,
        },
        "must": [
            "Dear Sir or Madam, (vergul bilan)",
            "Birinchi abzatsda maqsad",
            "Kamida bitta ANIQ dalil (sana, raqam, holat)",
            "Muloyim so'rov shakli (would / could / may)",
            "Yours faithfully,",
        ],
        "avoid": [
            "Buyruq ohangi: \"You must\", \"Change it now\"",
            "Qisqartma: don't, can't, I'm — rasmiy xatda TAQIQ",
            "Sababni aytmasdan to'g'ridan-to'g'ri so'rash",
        ],
    },

    {
        "key": "complaint",
        "part": "1.2",
        "level": "B2",
        "title": "Complaint Letter — shikoyat xati",
        "words": [120, 150],
        "minutes": 23,
        "when": "Xizmat, mahsulot yoki holatdan norozisiz va "
                "chora ko'rilishini istaysiz.",
        "idea": "Shikoyat xatining siri — JAHL EMAS, DALIL. Qanchalik "
                "xotirjam yozsangiz, shunchalik jiddiy qabul "
                "qilinasiz. Va oxirida ANIQ nima istayotganingizni "
                "ayting: pul qaytarilsinmi, almashtirilsinmi?",
        "steps": [
            {
                "name": "Salomlashish",
                "why": "Rasmiy.",
                "phrases": ["Dear Sir or Madam,", "Dear Manager,"],
            },
            {
                "name": "Nima haqida (1-2 gap)",
                "why": "Qaysi mahsulot / xizmat, QACHON. Sana va joy "
                       "bo'lmasa shikoyat kuchsiz.",
                "phrases": [
                    "I am writing to express my dissatisfaction with...",
                    "I am writing to complain about...",
                    "I wish to draw your attention to a problem with...",
                    "I purchased ... from your shop on 12th May.",
                ],
            },
            {
                "name": "Muammo (3-4 gap)",
                "why": "Nima noto'g'ri bo'lgani — faktlar bilan. "
                       "Sifatlar emas, dalillar.",
                "phrases": [
                    "Unfortunately, the item was damaged.",
                    "To make matters worse,...",
                    "Despite several attempts to contact you,...",
                    "This is not the first time this has happened.",
                ],
            },
            {
                "name": "Ta'sir (1-2 gap)",
                "why": "Bu sizga qanday zarar keltirdi — shikoyatga "
                       "og'irlik qo'shadi.",
                "phrases": [
                    "As a result, I was unable to...",
                    "This caused me considerable inconvenience.",
                    "Consequently, I had to...",
                ],
            },
            {
                "name": "Talab + yopilish",
                "why": "ANIQ chora so'ralmasa, xat bekor. Va muddat "
                       "bering.",
                "phrases": [
                    "I would therefore request a full refund.",
                    "I would appreciate it if you could replace the item.",
                    "I trust you will look into this matter.",
                    "I look forward to your prompt reply.",
                    "Yours faithfully,",
                ],
            },
        ],
        "model": {
            "task": "You booked a hotel room online for a weekend "
                    "break, but the room did not match the "
                    "description. Write a letter of complaint to "
                    "the hotel manager.",
            "paras": [
                ["Salomlashish", "Dear Sir or Madam,",
                 "Ism berilmagan — Sir or Madam. Madam'dan keyin "
                 "VERGUL qo'yiladi, nuqta emas."],
                ["Nima haqida", "I am writing to express my "
                                "dissatisfaction with the room I "
                                "booked at your hotel for the weekend "
                                "of 14th-15th June, booking reference "
                                "HB2291.",
                 "Sana va bron raqami — shikoyatni tekshirish mumkin "
                 "bo'ladi. Bu eng kuchli detal."],
                ["Muammo", "According to your website, the room had a "
                           "sea view and a private balcony. In reality, "
                           "it overlooked the car park and had no "
                           "balcony at all. To make matters worse, the "
                           "air conditioning did not work throughout "
                           "our stay.",
                 "\"According to your website... In reality...\" — "
                 "va'da va haqiqat solishtirilmoqda."],
                ["Ta'sir", "As a result, what was meant to be a "
                           "relaxing break turned into an "
                           "uncomfortable and disappointing experience.",
                 "Zarar aytildi — lekin haqorat yo'q."],
                ["Talab", "I would therefore request a partial refund "
                          "of the amount paid, together with written "
                          "confirmation that the description on your "
                          "website will be corrected. I have kept the "
                          "booking confirmation and can send it if "
                          "required. I look forward to your prompt "
                          "reply.\nYours faithfully,",
                 "ANIQ talab (qisman qaytarish) + javob kutish."],
            ],
            "words": 131,
        },
        "must": [
            "Sana / raqam / bron kabi ANIQ detal",
            "Muammo faktlar bilan",
            "ANIQ talab (refund / replace / repair)",
            "Yours faithfully,",
        ],
        "avoid": [
            "Haqorat va bo'rttirish: \"terrible\", \"the worst ever\"",
            "Undov belgisi ko'p ishlatish",
            "Nima istayotganini aytmaslik",
        ],
    },

    {
        "key": "application",
        "part": "1.2",
        "level": "B2",
        "title": "Application Letter — ariza xati",
        "words": [120, 150],
        "minutes": 23,
        "when": "Ish o'rni, kurs, stipendiya, ko'ngilli dastur yoki "
                "muddatni uzaytirish uchun ariza.",
        "idea": "Ariza xati — bu \"men kimman\" emas, \"men NEGA "
                "sizga mosman\". Har bir gapingiz e'londagi talabga "
                "javob bo'lsin. Bitta aniq yutuq o'nta sifatdan "
                "kuchliroq.",
        "steps": [
            {
                "name": "Salomlashish + maqsad",
                "why": "Qaysi o'rinni va qayerdan bilganingizni "
                       "birinchi gapda ayting.",
                "phrases": [
                    "I am writing to apply for the position of ... "
                    "advertised on your website.",
                    "I would like to apply for the post of ... as "
                    "advertised in today's newspaper.",
                    "I am writing in response to your advertisement for...",
                ],
            },
            {
                "name": "Hozirgi holat (1-2 gap)",
                "why": "Hozir kimsiz — talaba, o'qituvchi, xodim.",
                "phrases": [
                    "I am currently studying ... at ... University.",
                    "I am a final-year student of...",
                    "I have been working as a ... for the past two years.",
                ],
            },
            {
                "name": "Tajriba va yutuq (3-4 gap)",
                "why": "Eng muhim abzats. ANIQ misol keltiring: "
                       "\"I organised\", \"I trained\", \"our team won\".",
                "phrases": [
                    "During this time, I have gained experience in...",
                    "Last year I organised a ... for over 50 students.",
                    "I am fluent in English and have a B2 certificate.",
                    "In addition to my studies, I have...",
                ],
            },
            {
                "name": "Nega aynan shu joy (1-2 gap)",
                "why": "Bu abzats arizani boshqalardan ajratadi.",
                "phrases": [
                    "I am particularly interested in this position because...",
                    "Your organisation's reputation for ... is what "
                    "attracts me most.",
                ],
            },
            {
                "name": "Yopilish",
                "why": "Hujjat va suhbat haqida ayting.",
                "phrases": [
                    "I have attached my CV for your consideration.",
                    "I would welcome the opportunity to attend an interview.",
                    "I look forward to hearing from you.",
                    "Yours faithfully,",
                ],
            },
        ],
        "model": {
            "task": "You have seen an advertisement for a summer "
                    "volunteer at a local library. Write a letter "
                    "applying for the position.",
            "paras": [
                ["Maqsad", "Dear Sir or Madam,\nI am writing to apply "
                           "for the position of summer volunteer at "
                           "the City Library, which was advertised on "
                           "your website last week.",
                 "Qaysi o'rin va qayerdan ko'rgani — birinchi gapda."],
                ["Hozirgi holat", "I am currently a second-year student "
                                  "of English Philology at the National "
                                  "University.",
                 "Bitta qisqa gap yetarli — bu abzats faqat "
                 "'men kimman' degan savolga javob beradi, "
                 "tafsilot keyingi abzatsda keladi."],
                ["Tajriba", "Last summer I helped to run a reading club "
                            "for children aged seven to ten, where I "
                            "prepared weekly activities for a group of "
                            "fifteen. Through this work I learnt how to "
                            "keep young readers interested and how to "
                            "organise materials efficiently.",
                 "RAQAMLAR: 7-10 yosh, 15 bola. \"I am hardworking\" "
                 "degan quruq sifatdan ancha kuchli."],
                ["Nega shu joy", "I am particularly interested in this "
                                 "position because it would allow me to "
                                 "combine my love of books with practical "
                                 "experience of working with the public.",
                 "Aniq sabab — nusxa ko'chirilgan gap emas."],
                ["Yopilish", "I have attached my CV and would welcome "
                             "the opportunity to attend an interview.\n"
                             "Yours faithfully,",
                 "Hujjat + suhbat + rasmiy yopilish."],
            ],
            "words": 138,
        },
        "must": [
            "Qaysi o'rinni so'rayotganingiz aniq",
            "Kamida bitta ANIQ tajriba misoli (raqam bilan)",
            "Nega aynan shu joy — sabab",
            "Yours faithfully,",
        ],
        "avoid": [
            "Faqat sifatlar sanash: hardworking, responsible, friendly",
            "Yolg'on tajriba — mantiqsiz chiqadi",
            "CV'ni aytmaslik",
        ],
    },

    {
        "key": "thanks",
        "part": "1.2",
        "level": "B2",
        "title": "Thank-you Letter — minnatdorchilik xati",
        "words": [120, 150],
        "minutes": 23,
        "when": "Kimdir sizga yordam bergan, mehmon qilgan yoki "
                "sovg'a bergan — kompaniyaga yoki insonga rasmiy "
                "rahmat.",
        "idea": "Rahmat xatining kuchi — TAFSILOTDA. \"Thank you for "
                "everything\" hech narsa demaydi. \"Thank you for "
                "staying with me until the ambulance arrived\" — "
                "esda qoladi.",
        "steps": [
            {
                "name": "Salomlashish + maqsad",
                "why": "Kimga va nima uchun rahmat aytayotganingiz.",
                "phrases": [
                    "I am writing to express my sincere thanks to...",
                    "I would like to thank you most warmly for...",
                    "I am writing to extend my gratitude to one of "
                    "your employees.",
                ],
            },
            {
                "name": "Nima bo'lgani (3-4 gap)",
                "why": "Voqeani qisqa aytib bering — shundagina rahmat "
                       "haqiqiy ko'rinadi.",
                "phrases": [
                    "Last Friday, while I was...",
                    "On that occasion, your colleague...",
                    "Without his help, I would have...",
                ],
            },
            {
                "name": "Ta'sir (1-2 gap)",
                "why": "Bu siz uchun nima ma'no anglatgani.",
                "phrases": [
                    "His kindness made a great difference to me.",
                    "My family and I are extremely grateful.",
                    "It is rare to meet such professionalism.",
                ],
            },
            {
                "name": "Taklif / tilak",
                "why": "Rahmat bir tomonlama qolmasin — nimadir taklif "
                       "qiling.",
                "phrases": [
                    "I do hope your company will recognise his efforts.",
                    "Please pass on my thanks to him personally.",
                    "If there is any way I can return the favour, "
                    "please let me know.",
                ],
            },
            {
                "name": "Yopilish",
                "why": "Iliq, lekin rasmiy.",
                "phrases": ["Once again, thank you very much.",
                            "Yours faithfully,", "Kind regards,"],
            },
        ],
        "model": {
            "task": "One morning on your way to work you suddenly "
                    "fell ill on the bus. A passenger took you to "
                    "hospital. Write a letter to the company where "
                    "he works to express your gratitude.",
            "paras": [
                ["Maqsad", "Dear Sir or Madam,\nI am writing to express "
                           "my sincere thanks to Mr Baker, one of your "
                           "employees.",
                 "Kimga rahmat — birinchi gapda, ism bilan."],
                ["Voqea", "Last Friday morning I was travelling to work "
                          "on the number 133 bus when I suddenly felt "
                          "dizzy and lost consciousness. When I came "
                          "round, I found myself in St Mary's Hospital. "
                          "The doctor told me that it was Mr Baker who "
                          "had taken me there and informed my wife.",
                 "Sana, avtobus raqami, kasalxona nomi — tafsilot "
                 "rahmatni ishonarli qiladi."],
                ["Ta'sir", "My wife and I are extremely grateful for his "
                           "kindness, especially as he had never met me "
                           "before.",
                 "Nega bu ayniqsa qadrli — bitta gapda."],
                ["Taklif", "I do hope your company will recognise his "
                           "actions, and if he was late for work that "
                           "day because of me, I would be glad to "
                           "explain the circumstances.",
                 "Rahmat bir tomonlama qolmadi — taklif ham bor."],
                ["Yopilish", "Once again, please pass on my heartfelt "
                             "thanks to him.\nYours faithfully,",
                 "Iliq, lekin rasmiy yopilish."],
            ],
            "words": 137,
        },
        "must": [
            "Kimga rahmat — aniq",
            "Voqea tafsiloti (sana / joy / nima bo'lgani)",
            "Bu sizga nima bergani",
            "Yours faithfully, yoki Kind regards,",
        ],
        "avoid": [
            "\"Thank you for everything\" — bo'sh gap",
            "Voqeani aytmasdan faqat rahmat takrorlash",
        ],
    },

    {
        "key": "invitation",
        "part": "1.2",
        "level": "B2",
        "title": "Invitation Letter — taklifnoma",
        "words": [120, 150],
        "minutes": 23,
        "when": "Tadbir, ochilish, konferensiya yoki bayramga rasmiy "
                "taklif.",
        "idea": "Taklifnomada o'quvchi 4 ta savolga javob izlaydi: "
                "NIMA, QACHON, QAYERDA, NEGA MEN. To'rttasi ham "
                "bo'lmasa — taklif ishlamaydi.",
        "steps": [
            {
                "name": "Salomlashish + taklif",
                "why": "To'g'ridan-to'g'ri taklif qiling.",
                "phrases": [
                    "I would like to invite you to...",
                    "It is my pleasure to invite you to...",
                    "On behalf of ..., I am delighted to invite you to...",
                ],
            },
            {
                "name": "Tadbir haqida (2-3 gap)",
                "why": "NIMA / QACHON / QAYERDA — uchalasi ham shu "
                       "yerda.",
                "phrases": [
                    "The event will take place on Saturday, 12th May, "
                    "at the City Hall.",
                    "The programme will begin at 6 p.m. and last "
                    "approximately two hours.",
                    "The celebration marks the tenth anniversary of...",
                ],
            },
            {
                "name": "Nega aynan siz (1-2 gap)",
                "why": "Bu abzats taklifni shaxsiy qiladi — shuning "
                       "uchun rad javobi kamayadi.",
                "phrases": [
                    "As one of our longest-standing members, your "
                    "presence would mean a great deal to us.",
                    "We would be honoured if you could join us.",
                    "Your experience in this field would be of great "
                    "interest to our guests.",
                ],
            },
            {
                "name": "Amaliy ma'lumot",
                "why": "Ovqat, transport, kiyim, javob muddati.",
                "phrases": [
                    "Refreshments will be provided.",
                    "Please let us know by 5th May whether you will "
                    "be able to attend.",
                    "If you require transport, we would be happy to "
                    "arrange it.",
                ],
            },
            {
                "name": "Yopilish",
                "why": "Javob kutayotganingizni bildiring.",
                "phrases": ["We very much hope you will be able to join us.",
                            "I look forward to your reply.",
                            "Yours sincerely,"],
            },
        ],
        "model": {
            "task": "Your college is celebrating its 20th anniversary. "
                    "Write a letter inviting a former teacher to the "
                    "celebration.",
            "paras": [
                ["Taklif", "Dear Mr Karimov,\nOn behalf of the staff and "
                           "students of City College, I am delighted to "
                           "invite you to our twentieth anniversary "
                           "celebration.",
                 "Ism ma'lum — Dear Mr Karimov. Shuning uchun oxirida "
                 "Yours sincerely bo'ladi."],
                ["Tadbir", "The event will take place on Saturday, 12th "
                           "May, in the main hall, beginning at six "
                           "o'clock. The evening will include a short "
                           "concert prepared by our students and a "
                           "dinner afterwards.",
                 "QACHON, QAYERDA, SOAT NECHADA, NIMA bo'ladi — "
                 "hammasi bir abzatsda."],
                ["Nega siz", "As you taught here for more than fifteen "
                             "years, many of your former students have "
                             "asked whether you will be attending. Your "
                             "presence would mean a great deal to them.",
                 "Taklif shaxsiy qilindi — quruq chaqiruv emas."],
                ["Amaliy", "Please let us know by 5th May whether you "
                           "will be able to join us, and do tell us if "
                           "you would like us to arrange transport.",
                 "Javob muddati + transport taklifi."],
                ["Yopilish", "We very much hope to see you there.\n"
                             "Yours sincerely,",
                 "Dear + ism -> Yours sincerely."],
            ],
            "words": 129,
        },
        "must": ["NIMA / QACHON / QAYERDA", "Nega aynan shu odam",
                 "Javob muddati", "Ochilishga MOS yopilish"],
        "avoid": ["Sana yoki joyni tushirib qoldirish",
                  "\"Come if you want\" — sovuq ohang"],
    },

    {
        "key": "apology",
        "part": "1.2",
        "level": "B2",
        "title": "Apology Letter — uzr xati",
        "words": [120, 150],
        "minutes": 23,
        "when": "Kelolmadingiz, kechikdingiz, va'dani bajarmadingiz "
                "yoki xato qildingiz.",
        "idea": "Uzr xatida eng ko'p uchraydigan xato — o'zini "
                "oqlash. To'g'ri tartib: AVVAL uzr, KEYIN sabab "
                "(qisqa), OXIRIDA tuzatish taklifi. Sabab uzrdan "
                "uzunroq bo'lsa — bu uzr emas, bahona.",
        "steps": [
            {
                "name": "Uzr (birinchi gapda!)",
                "why": "Kechirim eng boshida aytilishi kerak.",
                "phrases": [
                    "I am writing to apologise for...",
                    "Please accept my sincere apologies for...",
                    "I would like to apologise for the inconvenience "
                    "caused by...",
                ],
            },
            {
                "name": "Sabab (1-2 gap, QISQA)",
                "why": "Tushuntirish kerak, lekin uzun bo'lmasin.",
                "phrases": [
                    "Unfortunately, I was unable to attend because...",
                    "Due to an unexpected family emergency,...",
                    "This was entirely my own oversight.",
                ],
            },
            {
                "name": "Mas'uliyatni olish (1 gap)",
                "why": "Eng kuchli abzats. Ayb boshqada ekanini "
                       "isbotlamang.",
                "phrases": [
                    "I fully understand the difficulty this must have caused.",
                    "I realise that this was unprofessional.",
                    "There is no excuse for the delay.",
                ],
            },
            {
                "name": "Tuzatish taklifi (2 gap)",
                "why": "Uzr chora bilan tugasa — ishonch qaytadi.",
                "phrases": [
                    "To make up for this, I would like to...",
                    "I would be happy to reschedule at your convenience.",
                    "I assure you that this will not happen again.",
                ],
            },
            {
                "name": "Yopilish",
                "why": "Yana bir bor qisqa uzr.",
                "phrases": ["Once again, I apologise for any inconvenience.",
                            "Thank you for your understanding.",
                            "Yours faithfully,"],
            },
        ],
        "model": {
            "task": "You missed an important meeting with a business "
                    "partner. Write a letter of apology.",
            "paras": [
                ["Uzr", "Dear Mr Aliyev,\nI am writing to apologise "
                        "sincerely for my absence from our meeting on "
                        "Tuesday morning.",
                 "Uzr BIRINCHI gapda. Sana ham bor."],
                ["Sabab", "On the previous evening my daughter was taken "
                          "to hospital, and I was unable to reach a "
                          "telephone until late the following day.",
                 "Sabab bor, lekin ikki gapdan oshmadi."],
                ["Mas'uliyat", "I fully understand that this left you "
                               "and your colleagues waiting without any "
                               "explanation, and I regret the "
                               "inconvenience this caused.",
                 "Bu abzats bo'lmasa xat bahonaga o'xshaydi."],
                ["Tuzatish", "I would be glad to meet at any time that "
                             "suits you next week, and I have already "
                             "prepared the figures we were due to "
                             "discuss so that we can make up for the "
                             "lost time. I have also arranged for a "
                             "colleague to be available should I be "
                             "unable to attend in person again.",
                 "Aniq chora: yangi uchrashuv + hujjat tayyor."],
                ["Yopilish", "Once again, please accept my apologies.\n"
                             "Yours sincerely,",
                 "Dear + ism -> Yours sincerely."],
            ],
            "words": 133,
        },
        "must": ["Uzr birinchi abzatsda", "Sabab QISQA",
                 "Mas'uliyatni olish", "Tuzatish taklifi"],
        "avoid": ["Sabab uzrdan uzun bo'lishi",
                  "Aybni boshqaga ag'darish",
                  "\"It wasn't my fault\""],
    },

    # =========================================================
    #  PART 2 — C1 — 180-200 SO'Z, 30 DAQIQA
    # =========================================================
    {
        "key": "forum",
        "part": "2",
        "level": "C1",
        "title": "Forum Post — onlayn munozarada javob",
        "words": [180, 200],
        "minutes": 30,
        "when": "\"You are participating in an online discussion. "
                "The question is: ...\" — Part 2 da eng ko'p "
                "uchraydigan tur.",
        "idea": "Forum posti — esse EMAS. Sizdan FIKR so'ralyapti, "
                "shuning uchun pozitsiyangiz aniq bo'lishi kerak. "
                "Lekin C1 darajada bir tomonlama fikr yetarli emas: "
                "qarshi tarafni ham tan oling, keyin rad eting. "
                "Shu \"tan olish -> rad etish\" harakati C1 ni B2 "
                "dan ajratadi.",
        "steps": [
            {
                "name": "Pozitsiya (2 gap)",
                "why": "Birinchi abzatsdayoq qaysi tarafda "
                       "ekaningiz bilinsin. \"Bu murakkab masala\" "
                       "deb boshlash — vaqt isrofi.",
                "phrases": [
                    "This is a question that divides opinion, but for "
                    "me the answer is clear:...",
                    "In my view, ... , and I will explain why.",
                    "Having thought about this carefully, I firmly "
                    "believe that...",
                ],
            },
            {
                "name": "1-dalil + misol (3-4 gap)",
                "why": "Har dalil MISOL bilan. Misolsiz dalil C1 "
                       "darajaga chiqmaydi.",
                "phrases": [
                    "The strongest argument in favour of this is that...",
                    "Take, for example, ...",
                    "In my own school, for instance,...",
                    "Research consistently shows that...",
                ],
            },
            {
                "name": "2-dalil + misol (3-4 gap)",
                "why": "Ikkinchi, BOSHQA sohadan dalil — pul, vaqt, "
                       "salomatlik, tenglik.",
                "phrases": [
                    "A second, equally important point is that...",
                    "What is more,...",
                    "This is particularly true for families who...",
                ],
            },
            {
                "name": "Qarshi fikr + rad (2-3 gap)",
                "why": "C1 ning KALITI. Qarshi tarafni tan oling, "
                       "keyin nega baribir o'z fikringiz kuchliroq "
                       "ekanini ayting.",
                "phrases": [
                    "Of course, some people argue that...",
                    "It is true that ... . However,...",
                    "While this concern is understandable, it "
                    "overlooks the fact that...",
                    "Admittedly, ... , but this is a small price to "
                    "pay for...",
                ],
            },
            {
                "name": "Xulosa (2 gap)",
                "why": "Fikringizni takrorlang, lekin BOSHQA so'zlar "
                       "bilan. Va yangi dalil qo'shmang.",
                "phrases": [
                    "All things considered, I remain convinced that...",
                    "On balance, the benefits clearly outweigh the "
                    "drawbacks.",
                    "What matters most, in the end, is...",
                ],
            },
        ],
        "model": {
            "task": "You are participating in an online discussion "
                    "for learners. The question is: Should schools "
                    "provide lunch for students, or should students "
                    "bring their own food from home? Post your "
                    "response, giving reasons and examples.",
            "paras": [
                ["Pozitsiya", "This question comes up in almost every "
                              "parents' meeting I have attended, and my "
                              "answer has not changed: schools should "
                              "provide lunch.",
                 "Pozitsiya BIRINCHI abzatsda. \"Ikkalasining ham "
                 "yaxshi tomoni bor\" degan yuvosh boshlanish emas."],
                ["1-dalil", "The most important reason is equality. When "
                            "every child eats the same meal, no one is "
                            "judged for what is in their lunchbox. In my "
                            "cousin's school, a free lunch scheme was "
                            "introduced two years ago, and teachers "
                            "noticed almost immediately that the "
                            "children who used to sit alone at lunchtime "
                            "began joining the others.",
                 "Dalil (tenglik) + ANIQ misol (amakivachcha maktabi, "
                 "ikki yil, natija). Umumiy gap emas."],
                ["2-dalil", "A second point concerns nutrition. Left to "
                            "themselves, many families rely on crisps "
                            "and biscuits simply because mornings are "
                            "rushed. A school kitchen, by contrast, "
                            "works to a planned menu with vegetables "
                            "and protein in every meal.",
                 "Boshqa SOHADAN dalil — ovqatlanish. Va sabab "
                 "aytilgan (ertalab shoshiladi), ayblov emas."],
                ["Qarshi fikr", "Of course, some parents argue that "
                                "school food is expensive and that "
                                "children should learn independence by "
                                "preparing their own meals. It is a fair "
                                "concern. However, independence can be "
                                "taught in many other ways, and the cost "
                                "of school meals is far lower than the "
                                "long-term cost of poor eating habits.",
                 "C1 KALITI: qarshi fikr tan olindi (\"It is a fair "
                 "concern\"), keyin rad etildi. Shu harakat bahoni "
                 "ko'taradi."],
                ["Xulosa", "On balance, then, I believe the school "
                           "canteen does far more than simply feed "
                           "children: it quietly removes a daily source "
                           "of inequality that no child should have "
                           "to notice at all.",
                 "Xulosa fikrni YANGI so'zlar bilan takrorladi va "
                 "yangi dalil qo'shmadi."],
            ],
            "words": 197,
        },
        "must": [
            "Pozitsiya birinchi abzatsda",
            "Ikkita dalil, HAR BIRIDA misol",
            "Qarshi fikrni tan olish va rad etish",
            "Xulosa (yangi dalilsiz)",
        ],
        "avoid": [
            "\"Firstly, secondly, finally\" bilan quruq ro'yxat",
            "Misolsiz umumiy gaplar",
            "Xulosada yangi fikr ochish",
            "180 so'zdan kam yozish",
        ],
    },

    {
        "key": "blog",
        "part": "2",
        "level": "C1",
        "title": "Blog Post — shaxsiy blog yozuvi",
        "words": [180, 200],
        "minutes": 30,
        "when": "\"You have decided to write a post for your blog "
                "about...\" — shaxsiy tajriba so'raladi.",
        "idea": "Blog — forumdan farqli o'laroq SHAXSIY. \"Men\" "
                "bemalol ishlatiladi, o'quvchiga murojaat qilinadi "
                "(\"Have you ever...?\"). Lekin C1 daraja shundaki: "
                "voqeadan XULOSA chiqarasiz. Faqat hikoya qilsangiz "
                "— B1 bo'lib qoladi.",
        "steps": [
            {
                "name": "Ilgak (2 gap)",
                "why": "Blog o'quvchisi birinchi qatordan keyin "
                       "qoladi yoki ketadi. Savol yoki kutilmagan "
                       "gap bilan boshlang.",
                "phrases": [
                    "Have you ever ...?",
                    "Three months ago I made a decision that most of "
                    "my friends thought was mad.",
                    "I used to believe that ... . I was wrong.",
                ],
            },
            {
                "name": "Kontekst (2-3 gap)",
                "why": "Nima bo'lgani — qisqa, lekin aniq.",
                "phrases": [
                    "It all started when...",
                    "At the time, I was...",
                    "To give you some background,...",
                ],
            },
            {
                "name": "Asosiy qism (4-5 gap)",
                "why": "Bu yerda tafsilot bo'lsin — his, muammo, "
                       "burilish nuqtasi.",
                "phrases": [
                    "The first week was harder than I expected.",
                    "What surprised me most was...",
                    "Little by little, however,...",
                ],
            },
            {
                "name": "Xulosa / saboq (2-3 gap)",
                "why": "C1 ni B1 dan ajratadigan abzats. Voqeadan "
                       "UMUMIY saboq chiqaring.",
                "phrases": [
                    "Looking back, what I learnt was not ... but ...",
                    "If there is one thing I would pass on, it is this:...",
                    "The experience taught me that...",
                ],
            },
            {
                "name": "O'quvchiga murojaat (1-2 gap)",
                "why": "Blog suhbatga chorlaydi — bu janr belgisi.",
                "phrases": [
                    "Have you tried anything similar? Let me know in "
                    "the comments.",
                    "I'd love to hear your thoughts.",
                    "So, would you give it a go?",
                ],
            },
        ],
        "model": {
            "task": "You have decided to write a post for your blog "
                    "about a habit you changed and what you learnt "
                    "from it.",
            "paras": [
                ["Ilgak", "Three months ago I deleted every social "
                          "media app from my phone. My friends were "
                          "convinced I would last a week.",
                 "Kutilmagan gap + kichik ziddiyat — o'quvchi davomini "
                 "bilmoqchi bo'ladi."],
                ["Kontekst", "It started when I checked my screen time "
                             "one Sunday evening and found I had spent "
                             "over five hours scrolling that day alone. "
                             "Five hours. I remember sitting there and "
                             "feeling slightly sick.",
                 "ANIQ raqam (5 soat) + his. \"I used my phone a lot\" "
                 "dan ancha kuchli."],
                ["Asosiy qism", "The first few days were genuinely "
                                "uncomfortable. I kept reaching for a "
                                "phone that had nothing to show me. But "
                                "by the second week something shifted: I "
                                "finished a novel I had been carrying "
                                "around for a year, and I started "
                                "sleeping properly for the first time in "
                                "months.",
                 "Qiyinchilik -> burilish -> natija. Uch bosqich "
                 "hikoyani tirik qiladi."],
                ["Saboq", "Looking back, the lesson was not really about "
                          "social media at all. It was about how easily "
                          "I let a habit make decisions on my behalf "
                          "without ever choosing it. I have reinstalled "
                          "one app since, but now I open it when I "
                          "decide to, rather than the other way round, "
                          "and that small difference has been worth far "
                          "more than three quiet months.",
                 "C1 ABZATSI: voqeadan UMUMIY xulosa. Bu bo'lmasa "
                 "matn oddiy hikoya bo'lib qoladi."],
                ["Murojaat", "Have you ever tried cutting something out "
                             "for a month? I'd genuinely like to know "
                             "how it went.",
                 "Blog janrining belgisi — suhbatga chorlash."],
            ],
            "words": 191,
        },
        "must": ["Ilgak (savol yoki kutilmagan gap)",
                 "Aniq tafsilot va raqamlar",
                 "Voqeadan UMUMIY xulosa",
                 "O'quvchiga murojaat"],
        "avoid": ["Faqat hikoya, xulosasiz",
                  "Rasmiy ohang: \"I am writing to inform you\"",
                  "Umumiy gaplar: \"it was very interesting\""],
    },

    {
        "key": "article",
        "part": "2",
        "level": "C1",
        "title": "Article — jurnal yoki sayt uchun maqola",
        "words": [180, 200],
        "minutes": 30,
        "when": "\"Write an article for your college magazine / "
                "website about...\" — o'quvchi ommaga qaratilgan.",
        "idea": "Maqola blogdan RASMIYROQ, forumdan QIZIQARLIROQ. "
                "Sarlavha qo'yiladi, o'quvchi ko'pchilik deb "
                "qaraladi. Maslahat yoki tavsiya bilan tugasa — "
                "eng kuchli chiqadi.",
        "steps": [
            {
                "name": "Sarlavha",
                "why": "Maqolada sarlavha BO'LISHI kerak — janr "
                       "belgisi. Qisqa va qiziqarli.",
                "phrases": ["Why We Get Studying Wrong",
                            "The Hidden Cost of Cheap Clothes",
                            "Is Your Phone Choosing For You?"],
            },
            {
                "name": "Kirish (2-3 gap)",
                "why": "Muammoni ko'pchilikka tegishli qilib "
                       "ko'rsating.",
                "phrases": [
                    "Ask any student what they find hardest, and the "
                    "answer is usually the same.",
                    "We all know we should ... . So why don't we?",
                    "Every year, thousands of ...",
                ],
            },
            {
                "name": "Tahlil (4-5 gap)",
                "why": "Sabablar. Ikki-uchta sabab, har birida "
                       "izoh.",
                "phrases": [
                    "Part of the problem lies in...",
                    "There are two reasons for this.",
                    "Perhaps the most obvious cause is...",
                    "Less obvious, but just as important, is...",
                ],
            },
            {
                "name": "Yechim / maslahat (3-4 gap)",
                "why": "Maqolaning qiymati shu yerda. Amaliy va "
                       "bajarish mumkin bo'lgan maslahat bering.",
                "phrases": [
                    "The good news is that this is easier to fix "
                    "than it sounds.",
                    "One approach that works is...",
                    "Start small: instead of ..., try ...",
                ],
            },
            {
                "name": "Yakun (1-2 gap)",
                "why": "Esda qoladigan gap bilan tugatish.",
                "phrases": [
                    "In the end, the difference is not talent but habit.",
                    "Small changes, repeated, beat big plans abandoned.",
                ],
            },
        ],
        "model": {
            "task": "Write an article for your college website about "
                    "why so many students struggle to revise "
                    "effectively, and what they can do about it.",
            "paras": [
                ["Sarlavha", "Why Re-reading Your Notes Doesn't Work",
                 "Qisqa, aniq va biroz ziddiyatli sarlavha — o'qishga "
                 "undaydi."],
                ["Kirish", "Ask any student how they revise, and most "
                           "will describe the same routine: open the "
                           "notes, read them through, highlight a few "
                           "lines, repeat. It feels productive. The "
                           "problem is that it rarely is.",
                 "Umumiy odat tasvirlandi, keyin kutilmagan burilish "
                 "(\"The problem is that it rarely is\")."],
                ["Tahlil", "There are two reasons for this. The first is "
                           "that re-reading creates a comfortable sense "
                           "of familiarity, which the brain mistakes for "
                           "knowledge. The second is timing: most "
                           "revision happens in one long session the "
                           "night before, when tired minds absorb very "
                           "little.",
                 "Ikki sabab, har biri izohlangan. \"Firstly, "
                 "secondly\" quruq ro'yxati emas — har biri "
                 "tushuntirilgan."],
                ["Yechim", "The good news is that the fix costs nothing. "
                           "Close the book and try to write down what "
                           "you remember; the gaps you find are exactly "
                           "what you need to study. Then spread the same "
                           "material over three short sessions rather "
                           "than one long one.",
                 "Amaliy va bajarish mumkin: kitobni yop, yozib ko'r, "
                 "uch qismga bo'l."],
                ["Yakun", "None of this requires an app, a paid course or a "
                          "new notebook. It requires only a willingness "
                          "to be wrong in private, several weeks before "
                          "you risk being wrong in an examination hall, "
                          "when it finally counts. "
                          "Revision, in other words, should feel "
                          "slightly difficult. If it feels easy, it "
                          "probably isn't working.",
                 "Qisqa, esda qoladigan yakun."],
            ],
            "words": 186,
        },
        "must": ["Sarlavha", "Muammo ko'pchilikka bog'landi",
                 "Sabablar tahlili", "Amaliy maslahat"],
        "avoid": ["Sarlavhasiz yozish",
                  "Faqat muammo, yechimsiz",
                  "Juda shaxsiy ohang (bu blog emas)"],
    },
]

# ---------------------------------------------------------------
#  NAMUNA SO'Z SONINI QO'LDA EMAS, HISOBLAB QO'YAMIZ.
#
#  2026-08-26 TUZATISH. Avval har namunaga so'z soni qo'lda
#  yozilgan edi va sakkiztasi noto'g'ri chiqdi (masalan "134" deb
#  yozilgan xat aslida 107 so'z edi). O'quvchi shu raqamga qarab
#  "demak 134 so'z shunday ko'rinar ekan" deb xulosa chiqaradi —
#  ya'ni noto'g'ri raqam noto'g'ri o'rgatadi. Endi raqam matndan
#  hisoblanadi, xato bo'lishi mumkin emas.
# ---------------------------------------------------------------
import re as _re


def _count(text: str) -> int:
    return len(_re.findall(r"[A-Za-z][A-Za-z'\u2019-]*", text))


for _g in GUIDE:
    _g["model"]["words"] = sum(_count(p[1]) for p in _g["model"]["paras"])

GUIDE_BY_KEY = {g["key"]: g for g in GUIDE}


def parts_summary() -> list[dict]:
    """Ekran uchun qisqa ro'yxat (matn tanasisiz — trafik tejaladi)."""
    out = []
    for g in GUIDE:
        out.append({
            "key": g["key"], "title": g["title"], "part": g["part"],
            "level": g["level"], "words": g["words"],
            "minutes": g["minutes"], "when": g["when"],
            "steps": len(g["steps"]),
        })
    return out
