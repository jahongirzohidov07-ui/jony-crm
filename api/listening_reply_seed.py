# -*- coding: utf-8 -*-
"""CEFR LISTENING 1-QISM — CHOOSE THE CORRECT REPLY (2026-08-26).

Jahongir: "CEFR birinchi qismi listening savollari shunaqa bo'ladi
bitta gap aytadi yoki savol shunga mos reply tanlash kerak bo'ladi
bu eng osonlari sekin qiyinlashtirib ketasan shundan keyin iloji
bo'lsa bitta mashqda 8ta bolsin umumiy 100ta."

QANDAY ISHLAYDI. Ekranda FAQAT uchta javob varianti turadi. Aytilgan
gap ko'rinmaydi — u telefonning o'z ovozi bilan o'qiladi va xohlagan
marta qayta eshitiladi (imtihonda ikki marta beriladi).

TUZILISHI. 100 ta savol, 5 bosqich, har bosqichda 20 ta:
  1 (0.7  sekin)        — salomlashuv, oddiy so'rov, yes/no;
  2 (0.8  o'rtacha)     — taklif, ruxsat, maslahat;
  3 (0.85 tezroq)       — question tag, qisqa javob, so/neither;
  4 (0.9  tezroq)       — bilvosita savol, must/needn't, o'tgan zamon;
  5 (1.0  imtihon)      — tabiiy tezlik, idiomatik javoblar.

NOTO'G'RI VARIANTLAR UCH XIL TUZILADI:
  1) MAVZUSI to'g'ri, lekin VAZIFASI boshqa (savolga emas, boshqa
     gapga javob);
  2) grammatikasi buzuq yoki chala ("Yes, I like" — nimani?);
  3) yordamchi fe'li mos emas ("Do you...?" ga "Yes, I am").
Uchalasi ham imtihonda aynan shunday keladi.
"""

SKILL = "ielts_listening"
KIND = "ielts_reply"
LET = ["A", "B", "C"]
STEP_RATE = {1: 0.7, 2: 0.8, 3: 0.85, 4: 0.9, 5: 1.0}
HINT = "Gapni tinglang va mos javobni tanlang"


# =====================================================================
#  QOIDALAR
# =====================================================================
REPLY_TIPS = [
    ("Bu mashq nima",
     "Bitta gap yoki savol eshitiladi. Uchta javobdan mos "
     "kelganini tanlaysiz. Gap ekranda YOZILMAYDI — faqat "
     "eshitiladi, lekin xohlagancha qayta tinglashingiz mumkin.",
     "Eshitasiz: How are you?\n"
     "A I am well.   B Not, fine.   C Yes, good.\nJavob: A"),
    ("BIRINCHI so'zni ushlang",
     "Gapning birinchi so'zi javob turini aytadi:\n"
     "Do / Does / Did -> Yes, I do / No, I didn't\n"
     "Are / Is / Was -> Yes, I am / No, it isn't\n"
     "Can / Could / Will -> Yes, I can / Of course\n"
     "Have / Has -> Yes, I have\n"
     "What / Where / When / Why / How -> Yes yoki No BO'LMAYDI",
     ""),
    ("Wh- savolga Yes/No javob bo'lmaydi",
     "«Where do you live?» savoliga «Yes, I do» javob emas. "
     "Bu eng ko'p uchraydigan qopqon: variant grammatik jihatdan "
     "to'g'ri ko'rinadi, lekin savolga umuman javob bermaydi.", ""),
    ("Yordamchi fe'l MOS kelishi shart",
     "«Do you like tea?» -> «Yes, I do» (Yes, I am EMAS).\n"
     "«Are you tired?» -> «Yes, I am» (Yes, I do EMAS).\n"
     "Ovozda birinchi so'z tez o'tib ketadi — shuni tutish kerak.",
     ""),
    ("Chala javob — noto'g'ri javob",
     "«Would you like some tea?» ga «Yes, I like» javob emas: "
     "like fe'li obyekt talab qiladi (I'd like some / Yes, please). "
     "Imtihonda ataylab shunday chala variant qo'yiladi.",
     "A Yes, I like        <- chala, noto'g'ri\n"
     "B Actually, I won't  <- mavzuga tushmaydi\n"
     "C No, thanks         <- TO'G'RI"),
    ("Taklif va so'rovni ajrating",
     "TAKLIF (Would you like...? / Shall I...?) -> Yes, please / "
     "No, thanks.\nSO'ROV (Can you...? / Could you...?) -> Of "
     "course / Sure / Here you are.\nIkkalasiga ham «Yes, please» "
     "deb javob bermang.", ""),
    ("Must I ...? -> No, you needn't",
     "«Must I learn it by heart?» savoliga «No, you mustn't» "
     "javob EMAS — u «taqiqlanadi» degani. To'g'risi «No, you "
     "needn't» = shart emas.", ""),
    ("So do I / Neither do I",
     "Kimdir «I liked the film» desa, roziligingizni «So did I» "
     "deb bildirasiz. Inkorga esa «Neither did I». Yordamchi fe'l "
     "va zamon aytilgan gapdan olinadi.",
     "I went there last year.  -> So did I.\n"
     "I don't like coffee.     -> Neither do I."),
    ("Gap bo'lsa — savol emas",
     "Ba'zan savol emas, oddiy XABAR eshitiladi ("
     "«I spent the weekend at the seaside»). Unda javob — "
     "qiziqish bildirish yoki savol berish, «Yes/No» emas.", ""),
    ("Ikki marta eshiting, keyin tanlang",
     "Birinchi eshitishda gapning MAQSADINI tuting (so'rayaptimi, "
     "taklif qilyaptimi, xabar beryaptimi). Ikkinchisida yordamchi "
     "fe'l va zamonni tekshiring.", ""),
]


def S(step, items):
    return {"step": step, "items": items}


SETS = []

# =============== 1-BOSQICH (sekin) — 20 ta ========================
SETS.append(S(1, [
    ("How are you?", ["I am well.", "Not, fine.", "Yes, good."], 0,
     "«How» savoliga Yes bilan javob berilmaydi (C). B grammatik "
     "jihatdan buzuq."),
    ("What's your name?",
     ["Yes, it is.", "My name is Aziz.", "I am fine, thanks."], 1,
     "A — Wh- savolga Yes bo'lmaydi. C — «How are you?» ning javobi."),
    ("Where do you live?",
     ["Yes, I do.", "I live in Samarkand.", "Since 2019."], 1,
     "C — «How long...?» savolining javobi."),
    ("Nice to meet you.",
     ["Nice to meet you too.", "Yes, I am.", "You are welcome."], 0,
     "C — «Thank you» ga javob."),
    ("Thank you very much.",
     ["Yes, please.", "You're welcome.", "I am sorry."], 1, ""),
    ("How old are you?",
     ["I am nineteen.", "Yes, I am old.", "In 2007."], 0,
     "C — «When were you born?» savolining javobi."),
    ("Do you speak English?",
     ["Yes, I am.", "Yes, a little.", "No, I don't speak."], 1,
     "A — yordamchi fe'l mos emas. C — chala va g'ayritabiiy."),
    ("Can you help me, please?",
     ["Of course.", "Yes, I am.", "No, I can't help."], 0, ""),
    ("What time is it?",
     ["It's half past six.", "Yes, it is.", "On Monday."], 0,
     "C — «When?» savolining javobi."),
    ("Where are you from?",
     ["I am from Bukhara.", "Yes, I am.", "By bus."], 0,
     "C — «How do you get there?» savolining javobi."),
    ("How is the weather today?",
     ["Yes, very good.", "It's sunny and warm.", "I like summer."],
     1, "C — mavzu to'g'ri, lekin savolga javob emas."),
    ("Have a nice weekend!",
     ["Thank you, you too.", "Yes, I have.", "It was nice."], 0,
     "B — «Have you...?» savoliga javob bo'lardi."),
    ("Would you like some tea?",
     ["Yes, I like.", "Yes, please.", "Yes, I would like."], 1,
     "A chala (nimani yoqtirasiz?). C ham chala — «I would like "
     "some» bo'lishi kerak edi."),
    ("Excuse me, is this seat free?",
     ["Yes, of course.", "Yes, I am free.", "No, it is free."], 0,
     "C — o'zini o'zi inkor qilyapti."),
    ("How much is this book?",
     ["It's ten dollars.", "Yes, it is much.", "I have two books."],
     0, ""),
    ("What's the weather like tomorrow?",
     ["I like the weather.", "It will be cold.", "Yes, it is."], 1,
     "A — «like» bu yerda «qanday» degani, «yoqtirmoq» emas."),
    ("See you tomorrow!",
     ["See you!", "Yes, I saw you.", "I am seeing."], 0, ""),
    ("Are you a student?",
     ["Yes, I do.", "Yes, I am.", "Yes, I study English."], 1,
     "A — yordamchi fe'l mos emas."),
    ("How do you go to work?",
     ["At eight o'clock.", "By metro.", "Yes, every day."], 1,
     "A — «When?» savolining javobi."),
    ("Sorry, I am late.",
     ["That's all right.", "Yes, you are.", "Me too, sorry."], 0,
     "B — to'g'ri, lekin qo'pol va tabiiy javob emas."),
]))

# =============== 2-BOSQICH — taklif, ruxsat, maslahat =============
SETS.append(S(2, [
    ("Shall I open the window?",
     ["Yes, please do.", "Yes, I shall.", "No, I don't open it."],
     0, "B va C — taklifga emas, savolga javob shaklida."),
    ("May I use your phone?",
     ["Of course, please.", "No, I forgot.", "Yes, I will."], 0, ""),
    ("Could you tell me the way to the station?",
     ["Here you are.", "Go straight and turn left.",
      "You never go there."], 1,
     "A — narsa uzatilganda aytiladi, yo'l so'ralganda emas."),
    ("Let's go to the cinema tonight.",
     ["Yes, it was good.", "That's a good idea.",
      "I went yesterday."], 1,
     "A va C — o'tgan zamon, taklif esa kelasi haqida."),
    ("Would you mind closing the door?",
     ["Not at all.", "Yes, I mind not.", "Yes, I would."], 0,
     "«Would you mind...?» ga rozilik — «Not at all» yoki «Of "
     "course not». «Yes» bu yerda RAD ETISH degani."),
    ("Can I take this chair?",
     ["Yes, go ahead.", "Yes, I can.", "No, I take it."], 0, ""),
    ("Why don't we meet at six?",
     ["Because I am busy.", "Six is fine for me.", "Yes, we don't."],
     1, "A — «Why don't we...?» sabab so'ramaydi, TAKLIF qiladi."),
    ("I have a terrible headache.",
     ["You should take a rest.", "Yes, you have.",
      "I have one too, thanks."], 0, ""),
    ("Do you mind if I sit here?",
     ["No, please do.", "Yes, sit down.", "Of course I mind not."],
     0, "B ziddiyatli: «Yes» rad etish, keyin «sit down» taklif."),
    ("Help yourself to some cake.",
     ["Thank you, it looks lovely.", "Yes, I helped.",
      "No, help me please."], 0,
     "«Help yourself» = marhamat, oling."),
    ("What about going for a walk?",
     ["I walked this morning.", "Sounds great.", "Yes, it is about."],
     1, ""),
    ("I'm sorry, I broke your cup.",
     ["Never mind.", "Yes, you broke it.", "Thank you very much."],
     0, ""),
    ("Would you like to join us?",
     ["I'd love to.", "Yes, I like.", "I joined already."], 0,
     "B chala. C — hali taklif qilinmoqda, bo'lib bo'lgan emas."),
    ("Shall we take a taxi?",
     ["No, let's walk.", "Yes, we shall take.", "I took a taxi."], 0,
     ""),
    ("Could I speak to Mr Karimov, please?",
     ["Hold on, please.", "Yes, you could.", "He speaks English."],
     0, "Telefonda standart javob."),
    ("You look tired.",
     ["Yes, I didn't sleep well.", "Yes, you look tired too.",
      "No, I look fine."], 0, ""),
    ("Do you want me to help you?",
     ["Yes, if you don't mind.", "Yes, I want.", "No, I help you."],
     0, "B chala — «I want» dan keyin nima kerakligi aytilmagan."),
    ("Make yourself at home.",
     ["Thank you.", "Yes, I am at home.", "No, this is not my home."],
     0, "«Make yourself at home» = o'zingizni erkin tuting."),
    ("Is it all right if I call you later?",
     ["Sure, any time.", "Yes, I call you.", "No, it is all right."],
     0, ""),
    ("I think we should leave now.",
     ["Yes, you are right.", "No, I don't think.",
      "We left an hour ago."], 0, "B chala."),
]))

# ====== 3-BOSQICH — question tag, qisqa javob, so / neither ========
SETS.append(S(3, [
    ("You are from Tashkent, aren't you?",
     ["Yes, I am.", "Yes, I aren't.", "No, I do."], 0, ""),
    ("You didn't call me yesterday, did you?",
     ["No, I'm sorry, I forgot.", "Yes, I didn't.",
      "No, I did call."], 0,
     "B o'zini inkor qiladi. C ham ziddiyatli."),
    ("I love this song.",
     ["So do I.", "So am I.", "Neither do I."], 0,
     "«love» oddiy fe'l -> do. C — inkorga ishlatiladi."),
    ("I can't swim.",
     ["Neither can I.", "So can I.", "Yes, you can't."], 0, ""),
    ("I went to Bukhara last summer.",
     ["So did I.", "So do I.", "Neither did I."], 0, ""),
    ("I'm not very good at maths.",
     ["Neither am I.", "So am I.", "Yes, you are not."], 0, ""),
    ("It's a lovely day, isn't it?",
     ["Yes, it is.", "Yes, it isn't.", "No, it is lovely."], 0, ""),
    ("She hasn't arrived yet, has she?",
     ["No, not yet.", "Yes, she hasn't.", "No, she has."], 0, ""),
    ("Do you take sugar in your coffee?",
     ["Just one, thanks.", "Yes, I take coffee.", "No, I am."], 0,
     ""),
    ("Have you ever been to London?",
     ["Yes, twice.", "Yes, I did.", "No, I go there."], 0,
     "B — Present Perfect savoliga did mos emas."),
    ("How long have you been waiting?",
     ["About ten minutes.", "Yes, a long time.", "At ten o'clock."],
     0, "C — «What time?» savolining javobi."),
    ("Did you enjoy the concert?",
     ["Yes, it was great.", "Yes, I enjoy.", "No, I am enjoying."],
     0, "B chala va zamon ham noto'g'ri."),
    ("Whose bag is this?",
     ["It's mine.", "Yes, it is.", "It is a bag."], 0, ""),
    ("Which one do you prefer, the blue or the green?",
     ["The blue one.", "Yes, I prefer.", "Both are colours."], 0,
     ""),
    ("I'm afraid I can't come tomorrow.",
     ["That's a pity.", "Yes, you can.", "Thank you very much."], 0,
     ""),
    ("How often do you go to the gym?",
     ["Three times a week.", "Yes, very often.", "For two hours."],
     0, "C — «How long?» savolining javobi."),
    ("What does your brother do?",
     ["He is an engineer.", "He is doing well.", "Yes, he does."], 0,
     "«What does he do?» = kasbi nima. B — «How is he?» ga javob."),
    ("Are you coming with us or staying here?",
     ["I'll come with you.", "Yes, I am.", "No, I don't."], 0,
     "Tanlov savoliga Yes/No javob bo'lmaydi."),
    ("Sorry, I didn't catch your name.",
     ["It's Dilnoza.", "No, you didn't.", "I didn't catch it too."],
     0, "«didn't catch» = eshitmadim."),
    ("Congratulations on your new job!",
     ["Thank you very much.", "Yes, it is new.", "Congratulations!"],
     0, ""),
]))

# ==== 4-BOSQICH — bilvosita savol, must/needn't, o'tgan zamon ======
SETS.append(S(4, [
    ("Must I hand in the report today?",
     ["No, you needn't. Tomorrow is fine.",
      "Yes, you mustn't hand it in.", "No, you don't must."], 0,
     "«mustn't» = TAQIQ, «needn't» = shart emas. C — grammatik "
     "jihatdan mumkin emas."),
    ("Do I have to book a seat in advance?",
     ["No, you don't have to.", "Yes, you haven't.",
      "No, you mustn't book."], 0, ""),
    ("Could you tell me where the nearest bank is?",
     ["It's just around the corner.", "Yes, I could tell you.",
      "No, I don't know the bank."], 0,
     "B savolni so'zma-so'z tushungan — bu bilvosita SO'ROV."),
    ("Do you happen to know when the train leaves?",
     ["At a quarter past nine.", "Yes, I happen.",
      "No, I don't happen to."], 0, ""),
    ("I was wondering if you could give me a hand.",
     ["Sure, what do you need?", "Yes, I was wondering too.",
      "No, my hand is fine."], 0,
     "«give me a hand» = yordam bering."),
    ("Would you mind if I opened the window a little?",
     ["Go ahead, it is stuffy in here.", "Yes, I opened it.",
      "Yes, please open it."], 0,
     "C ziddiyatli: «Yes» rad etish degani."),
    ("How did the interview go?",
     ["Better than I expected.", "I went by taxi.",
      "Yes, I went there."], 0,
     "B — «How did you go?» savolining javobi. Bu yerda «go» = "
     "o'tmoq."),
    ("You should have told me earlier.",
     ["I know, I'm sorry.", "Yes, I should tell you.",
      "No, I told you earlier."], 0,
     "«should have told» = aytishing kerak edi (aytmading)."),
    ("If I were you, I'd take the earlier train.",
     ["That's probably a good idea.", "Yes, you are me.",
      "I took it yesterday."], 0, ""),
    ("I don't suppose you have change for a five, do you?",
     ["Let me check my pocket.", "Yes, I don't suppose.",
      "No, five is not change."], 0,
     "«I don't suppose you...?» — juda muloyim so'rov."),
    ("What was the weather like when you arrived?",
     ["It was pouring with rain.", "I like rainy weather.",
      "Yes, it was like that."], 0, ""),
    ("Have you managed to finish the report?",
     ["Almost, I need another hour.", "Yes, I managed the report.",
      "No, I finish it now."], 0, ""),
    ("Sorry to bother you, but could I ask you something?",
     ["Not at all, go ahead.", "Yes, you bother me.",
      "No, don't ask me."], 0, ""),
    ("I'd rather not talk about it, if you don't mind.",
     ["Of course, I understand.", "Yes, let's talk about it.",
      "No, I don't rather."], 0, "«I'd rather not» = xohlamayman."),
    ("It's a shame you couldn't come to the party.",
     ["I know, I was really sorry to miss it.",
      "Yes, the party was a shame.", "No, I came to the party."], 0,
     "«It's a shame» = afsuski."),
    ("Do you mind waiting a few more minutes?",
     ["No, take your time.", "Yes, I wait a few minutes.",
      "No, I am waiting."], 0, ""),
    ("Whereabouts in Uzbekistan are you from?",
     ["A small town near Andijan.", "Yes, I am from Uzbekistan.",
      "I have been here for years."], 0,
     "«Whereabouts» = aniqroq qayeridan."),
    ("How come you didn't answer my message?",
     ["My phone was switched off.", "Yes, I didn't answer.",
      "I will answer you now."], 0,
     "«How come...?» = nega (sabab so'raladi)."),
    ("You must be exhausted after such a long flight.",
     ["I am, actually.", "Yes, you must be.", "No, I must not."], 0,
     "Bu yerda «must» = taxmin, majburiyat emas."),
    ("Let me know if you need anything else.",
     ["I will, thank you.", "Yes, I let you know now.",
      "No, you need nothing."], 0, ""),
]))

# ============ 5-BOSQICH — imtihon tezligi, idiomatik ==============
SETS.append(S(5, [
    ("I'm afraid the meeting has been put off until next week.",
     ["Again? That's the second time.", "Yes, I put it off.",
      "No, the meeting is next week."], 0,
     "«put off» = kechiktirmoq. C xabarni takrorlaydi, javob emas."),
    ("Do you fancy grabbing a coffee after work?",
     ["I'd love to, but I've got plans.", "Yes, I fancy coffee.",
      "No, I grabbed one already."], 0,
     "«Do you fancy...?» = xohlaysizmi (norasmiy)."),
    ("It completely slipped my mind, I'm so sorry.",
     ["Don't worry, it happens.", "Yes, your mind slipped.",
      "No, you must remember it."], 0,
     "«slip one's mind» = esdan chiqmoq."),
    ("How's the new job working out?",
     ["So far so good.", "I work out every morning.",
      "Yes, it works."], 0,
     "B — «work out» bu yerda «ketyapti» degani, sport emas."),
    ("I'll give you a ring once I've spoken to her.",
     ["Great, I'll wait to hear from you.",
      "Thank you for the ring.", "Yes, give me a ring now."], 0,
     "«give a ring» = qo'ng'iroq qilmoq (uzuk emas)."),
    ("We're running a bit behind schedule, I'm afraid.",
     ["That's fine, I'm not in a hurry.", "Yes, let's run faster.",
      "No, the schedule is behind."], 0, ""),
    ("Would you mind giving me a hand with these boxes?",
     ["Not at all, where do they go?", "Yes, my hands are free.",
      "Yes, I mind giving a hand."], 0, ""),
    ("I can't make it on Friday after all.",
     ["No problem, shall we say Monday?", "Yes, you can make it.",
      "I made it on Friday too."], 0,
     "«make it» = bora olmoq."),
    ("That's the third time this week the bus has been late.",
     ["Tell me about it.", "Yes, it is three o'clock.",
      "No, the bus is on time."], 0,
     "«Tell me about it» = men ham xuddi shundan azob chekyapman."),
    ("Do you reckon it's worth applying?",
     ["Definitely, you've got nothing to lose.",
      "Yes, it is worth money.", "No, I don't reckon it."], 0,
     "«reckon» = o'ylamoq."),
    ("Sorry, I'm not with you. Could you go over that again?",
     ["Of course, let me explain it differently.",
      "Yes, I am with you.", "No, I will not go over."], 0,
     "«I'm not with you» = tushunmadim; «go over» = qayta "
     "tushuntirmoq."),
    ("I've been meaning to ask you about the deadline.",
     ["Go on, what did you want to know?",
      "Yes, I mean the deadline.", "No, I did not ask you."], 0,
     "«I've been meaning to» = ancha vaqtdan beri so'ramoqchi edim."),
    ("She's bound to say no, isn't she?",
     ["I wouldn't be so sure.", "Yes, she is bound.",
      "No, she says yes."], 0,
     "«bound to» = albatta shunday qiladi."),
    ("Let's call it a day, shall we?",
     ["Good idea, I'm worn out.", "Yes, today is a good day.",
      "No, let's call tomorrow."], 0,
     "«call it a day» = ishni yakunlamoq."),
    ("It's not really my cup of tea, to be honest.",
     ["Fair enough, everyone's different.",
      "Would you like another cup?", "No, I prefer coffee too."], 0,
     "«not my cup of tea» = menga yoqmaydi (choy haqida emas)."),
    ("I'll keep you posted as soon as I hear anything.",
     ["Thanks, I appreciate it.", "Yes, post it to me.",
      "No, I already heard."], 0,
     "«keep you posted» = xabardor qilib turmoq."),
    ("Do you happen to have any idea what went wrong?",
     ["Not the faintest, I'm afraid.", "Yes, nothing went wrong.",
      "No, I have a good idea."], 0,
     "«Not the faintest (idea)» = mutlaqo bilmayman."),
    ("It looks like we'll have to start from scratch.",
     ["After all that work? You must be joking.",
      "Yes, let's scratch it.", "No, we started already."], 0,
     "«from scratch» = noldan boshlamoq."),
    ("Would it be at all possible to move the appointment forward?",
     ["I'll see what I can do.", "Yes, it moved forward.",
      "No, it is not possible to move."], 0,
     "«move forward» = oldinroqqa surmoq."),
    ("I dare say you've heard the news by now.",
     ["Actually, no. What's happened?", "Yes, I dare say it.",
      "No, I did not dare."], 0,
     "«I dare say» = o'ylashimcha."),
]))


# =====================================================================
#  KITOBDAN OLINGAN QISM (2026-08-26)
#
#  Jahongir "AUDIOSCRIPT_MultilevelMaster_Listening.pdf" ni yubordi.
#  Part 1'da 50 ta mashq, 383 ta gap bor. Quyida 1-13 mashqlardagi
#  gaplar AYNAN o'sha kitobdan olingan — ya'ni o'quvchi haqiqiy
#  imtihon gaplarini eshitadi.
#
#  VARIANTLAR HAQIDA. Kitobning o'zi skaner qilingan, javob kaliti
#  yo'q. 1-mashq va 2-mashqning boshidagi variantlar Jahongir
#  yuborgan rasmdan aynan olindi. Qolganlariga variantlar shu yerda
#  yozildi — chunki kalitsiz variantni taxmin qilish noto'g'ri
#  kontent yaratardi. Gap KITOBNIKI, variant BIZNIKI.
#
#  BITTA TUZATISH. Kitobda "Turn the left and go straight" deb
#  yozilgan — bu grammatik xato. O'quv materialida xato ingliz tili
#  qolmasligi kerak, shuning uchun "Turn left and go straight" deb
#  to'g'rilandi.
# =====================================================================
BOOK_SETS = []

# ---- 1-4 mashqlar -> 2-bosqich --------------------------------
BOOK_SETS.append(S(2, [
    ("How are you?", ["I am well.", "Not, fine.", "Yes, good."], 0,
     "«How» savoliga Yes bilan javob berilmaydi."),
    ("Did you do your homework?",
     ["Of course, please.", "No, I forgot.", "Yes, I will."], 1,
     "«Did» — o'tgan zamon, C esa kelasi zamon."),
    ("How can I go to the train station?",
     ["Here you are.", "Turn left and go straight.",
      "You never go there."], 1,
     "A — narsa uzatilganda aytiladi."),
    ("Would you like a cup of tea?",
     ["Yes, I like", "Actually, I won't", "No, thanks"], 2,
     "A chala: «like» obyekt talab qiladi. Taklifga javob — "
     "«Yes, please» yoki «No, thanks»."),
    ("What is the time now?",
     ["Yes, this is", "Sorry, I don't have a watch",
      "No, it is not."], 1, "Wh- savolga Yes/No javob bo'lmaydi."),
    ("Shall I retell the text?",
     ["Yes, you will. You can only translate it.",
      "Do, please. You can only translate it.",
      "No, you needn't. You can only translate it."], 2,
     "«faqat tarjima qilasan» deyilyapti — demak qayta so'zlab "
     "berish SHART EMAS: needn't."),
    ("What did you think of the film?",
     ["It was OK.", "Let's go tomorrow.", "So did I."], 0,
     "«What did you think of...?» = fikringiz qanday. C — "
     "«I liked it» kabi gapga javob bo'lardi."),
    ("We went to Berlin last weekend.",
     ["How did you get there?", "Yes, last weekend was rainy.",
      "And, what about you?"], 0,
     "Bu XABAR, savol emas — javob qiziqish bildirish."),
]))

BOOK_SETS.append(S(2, [
    ("Is 'copying someone's homework' cheating?",
     ["Sure, you can copy in the exam.", "No, it isn't an exam.",
      "Yes, definitely."], 2, ""),
    ("Why, Ann! Are you reading without light? "
     "Turn on the lamp, please.",
     ["Oh, yes, it's far from here.", "Oh, no, I am too hungry.",
      "Oh, yes, it's getting dark."], 2, ""),
    ("Look, Gill, the rain has stopped.",
     ["Let's go out then.", "Yes, I stopped it.",
      "No, it will rain."], 0, ""),
    ("I was told an interesting story yesterday.",
     ["Really? Tell me about it.", "Yes, I told you.",
      "No, it wasn't interesting."], 0,
     "B — kim aytganini almashtirib yuborgan."),
    ("How many times have you been in South Africa?",
     ["Only once.", "Yes, many times I have.", "For two weeks."], 0,
     "C — «How long?» savolining javobi."),
    ("Will you cook sumalak this year?",
     ["Of course I will.", "Yes, I cooked.", "No, I am cooking."],
     0, "Savol KELASI zamonda."),
    ("Mary is out now.",
     ["Shall I call back later?", "Yes, she is in.",
      "No, I am out too."], 0, "Telefon suhbati."),
    ("I think Nick will let us go to the park.",
     ["I hope so.", "Yes, he let us.", "No, I don't let you."], 0,
     ""),
]))

BOOK_SETS.append(S(2, [
    ("May I watch what you are doing?",
     ["Yes, of course.", "Yes, I watch.", "No, I am watching."], 0,
     ""),
    ("Oh, I must water the plants.",
     ["Don't worry, I've already done it.", "Yes, water is there.",
      "No, you mustn't."], 0,
     "C — «mustn't» taqiq degani, bu yerda mos emas."),
    ("I'm sorry for keeping you waiting for such a long time.",
     ["That's all right.", "Yes, you kept me.",
      "Thank you very much."], 0, ""),
    ("Where is the smoking room?",
     ["It's on the first floor.", "Yes, you can smoke.",
      "I don't smoke."], 0,
     "C — mavzuga tegishli, lekin savolga javob emas."),
    ("Have you got any books by Furqat?",
     ["I'm afraid we haven't.", "Yes, I did.", "No, I don't got."],
     0, "«Have you got...?» -> «I have» / «I haven't»."),
    ("Bread is not taken with fork, is it?",
     ["No, it isn't.", "Yes, it is not.", "No, it is."], 0,
     "Inkor question tag: rozilik — «No, it isn't»."),
    ("Who had an exam last week?",
     ["The third-year students.", "Yes, they had.",
      "It was on Monday."], 0,
     "«Who?» — odam so'raladi. C — «When?» javobi."),
    ("Where did you stay when you went to the Fergana?",
     ["At my uncle's house.", "By train.", "For five days."], 0,
     "B — «How?», C — «How long?» javoblari."),
]))

BOOK_SETS.append(S(2, [
    ("Who fell ill?", ["My younger brother.", "Yes, he fell.",
                       "Last Tuesday."], 0, ""),
    ("My parents want to speak to you.",
     ["When would it be convenient?", "Yes, I spoke to them.",
      "No, they don't want."], 0, ""),
    ("Excuse me, sir.", ["Yes, how can I help you?",
                         "No, I am not sir.", "You are excused."], 0,
     ""),
    ("Could you pass me the salt, please?",
     ["Here you are.", "Yes, I could.", "No, I don't pass."], 0,
     "B savolni so'zma-so'z tushungan — bu SO'ROV."),
    ("Coffee, sir?", ["Yes, please.", "Yes, it is coffee.",
                      "No, I am sir."], 0, ""),
    ("How long has she been with you?",
     ["About three years.", "Yes, a long time.", "She is very tall."],
     0, "C — «How tall?» bilan adashtirgan."),
    ("You go in for sports, don't you?",
     ["Yes, I play tennis.", "Yes, I don't.", "No, I go."], 0,
     "«go in for sports» = sport bilan shug'ullanmoq."),
    ("Can I borrow your map of Khiva?",
     ["Sure, take it.", "Yes, I borrowed it.", "No, I can."], 0,
     ""),
]))

# ---- 5-8 mashqlar -> 3-bosqich --------------------------------
BOOK_SETS.append(S(3, [
    ("Do you think we'll have good weather?",
     ["I hope so.", "Yes, I think.", "No, it was good."], 0,
     "B chala — «I think so» bo'lishi kerak edi."),
    ("Who is a sailor?", ["My cousin Bekzod.", "Yes, he is.",
                          "On a big ship."], 0, ""),
    ("It's time for lunch.", ["I'm coming.", "Yes, it is time.",
                              "What time is it?"], 0,
     "C — vaqtni so'rayapti, lekin vaqt allaqachon aytildi."),
    ("Would you like a drink?", ["Just water, thanks.",
                                 "Yes, I drink.", "No, I would."], 0,
     ""),
    ("How much was your new shirt?",
     ["Only fifteen pounds.", "Yes, it was much.",
      "It's dark blue."], 0, "C — «What colour?» javobi."),
    ("I'm very sorry.", ["Never mind.", "Yes, you are.",
                         "Thank you."], 0, ""),
    ("Do you speak English?", ["A little, yes.", "Yes, I am.",
                               "No, I speak."], 0,
     "B — yordamchi fe'l mos emas."),
    ("John's broken this plate.",
     ["Has he? What a pity.", "Yes, he break it.",
      "No, the plate is fine."], 0, ""),
]))

BOOK_SETS.append(S(3, [
    ("Is this your watch?", ["No, it's my brother's.",
                             "Yes, I watch.", "It's ten o'clock."],
     0, "C — «watch» so'zini soat deb tushungan qopqon."),
    ("Can I have a sandwich?", ["Certainly, which one?",
                               "Yes, I can.", "No, I have one."], 0,
     ""),
    ("How many people were in the cafe?",
     ["About twenty.", "Yes, a lot.", "It was very noisy."], 0, ""),
    ("We're from London.", ["Oh, which part?", "Yes, you are.",
                            "No, I am not."], 0, ""),
    ("Who's that man with the green sweater?",
     ["He's our new teacher.", "Yes, that's him.",
      "The sweater is nice."], 0, ""),
    ("Where's Amanda gone?", ["To the library, I think.",
                              "Yes, she has gone.", "An hour ago."],
     0, "C — «When?» javobi."),
    ("I hate shopping.", ["So do I.", "So am I.",
                          "Neither do I hate."], 0,
     "«hate» oddiy fe'l -> do."),
    ("How long did the journey take?",
     ["Nearly four hours.", "Yes, it was long.", "By plane."], 0,
     ""),
]))

BOOK_SETS.append(S(3, [
    ("The room costs $55 a night.",
     ["That's more than I expected.", "Yes, it costs.",
      "No, I have $55."], 0, ""),
    ("Are you sure the match starts at two?",
     ["Yes, I checked the ticket.", "Yes, I sure.",
      "No, it is a match."], 0, ""),
    ("I saw the new Spielberg film last night.",
     ["Was it any good?", "Yes, I see it.",
      "No, I will see it last night."], 0, ""),
    ("How did the accident happen?",
     ["A car ran into a bus.", "Yes, it happened.",
      "Near the market."], 0, "C — «Where?» javobi."),
    ("Hello, I'd like to speak to Mr Green, please.",
     ["I'll put you through.", "Yes, he speaks.",
      "No, I am Mr Green."], 0,
     "«put you through» = ulab qo'yaman."),
    ("May I leave now?", ["Yes, you may.", "Yes, I leave.",
                          "No, you needn't leave."], 0,
     "C — ruxsat so'ralyapti, «needn't» esa majburiyat haqida."),
    ("Let's listen to this new CD.",
     ["Good idea.", "Yes, I listened.", "No, I am listening."], 0,
     ""),
    ("I'd like two tickets for tonight.",
     ["I'm afraid we're sold out.", "Yes, you would.",
      "No, tonight is fine."], 0, ""),
]))

BOOK_SETS.append(S(3, [
    ("What time did the meeting end?",
     ["At half past five.", "Yes, it ended.", "It lasted two hours."],
     0, "C — «How long?» javobi."),
    ("I can't do this maths problem.",
     ["Shall I help you?", "Yes, you can't.", "No, I can do it."], 0,
     ""),
    ("Do you like Jane's new flat?",
     ["Yes, it's lovely.", "Yes, I like.", "No, she likes it."], 0,
     "B chala."),
    ("How did you go to Madrid?", ["We flew.", "Yes, we went.",
                                   "For a week."], 0, ""),
    ("I really must go now!", ["See you soon then.",
                               "Yes, you mustn't.", "No, you go."], 0,
     ""),
    ("Is Mike still doing this homework?",
     ["Yes, he hasn't finished.", "Yes, he did.",
      "No, he is doing it."], 0, "C o'zini inkor qiladi."),
    ("I can't understand this letter.",
     ["Let me have a look.", "Yes, I understand.",
      "No, the letter is fine."], 0, ""),
    ("Are you sure the film starts at 10?",
     ["Actually, it's half past ten.", "Yes, I am sure film.",
      "No, I saw the film."], 0, ""),
]))

# ---- 9-11 mashqlar -> 4-bosqich -------------------------------
BOOK_SETS.append(S(4, [
    ("I don't think I can come to the concert.",
     ["Oh, that's a shame.", "Yes, you can come.",
      "Neither can I come."], 0, ""),
    ("Let's have supper now.", ["I'm not hungry yet.",
                                "Yes, I had supper.",
                                "No, we don't have."], 0, ""),
    ("Have you shut the windows?", ["Yes, all of them.",
                                    "Yes, I shut them tomorrow.",
                                    "No, I do."], 0, ""),
    ("My street is too noisy.", ["Why don't you move?",
                                 "Yes, it is a street.",
                                 "No, my street is quiet."], 0, ""),
    ("Can I speak to John, please?", ["Speaking.", "Yes, I can.",
                                      "No, John speaks."], 0,
     "«Speaking» = men o'zim gapiryapman."),
    ("$500 is too expensive.", ["I'll give you a discount.",
                                "Yes, it is $500.",
                                "No, it is cheap for me."], 0, ""),
    ("I've got an appointment with my doctor today.",
     ["I hope it's nothing serious.", "Yes, you have got.",
      "No, the doctor is today."], 0, ""),
    ("Would you like anything else?", ["No, that's all, thanks.",
                                       "Yes, I would like.",
                                       "No, I like anything."], 0,
     "B chala."),
]))

BOOK_SETS.append(S(4, [
    ("When is your mother's birthday?", ["On the fifth of May.",
                                         "Yes, it is her birthday.",
                                         "She is fifty."], 0, ""),
    ("Shall we go to the shops now?", ["Let's wait until it stops "
                                       "raining.", "Yes, we shall go "
                                       "shops.", "No, I went."], 0,
     ""),
    ("It's my sister's birthday tomorrow!",
     ["What are you going to buy her?", "Yes, it was yesterday.",
      "No, my birthday is tomorrow."], 0, ""),
    ("Mary will help the teacher.", ["That's very kind of her.",
                                     "Yes, she helped.",
                                     "No, the teacher helps Mary."],
     0, ""),
    ("I would like to see the doctor.", ["Do you have an "
                                         "appointment?",
                                         "Yes, you would.",
                                         "No, the doctor sees you."],
     0, ""),
    ("Shall we leave now?", ["In five minutes, if that's all right.",
                             "Yes, we left.", "No, I leave you."], 0,
     ""),
    ("Anything else?", ["That's everything, thank you.",
                        "Yes, anything.", "No, something else."], 0,
     ""),
    ("When will lunch be ready?", ["In about ten minutes.",
                                   "Yes, it will.",
                                   "In the kitchen."], 0,
     "C — «Where?» javobi."),
]))

BOOK_SETS.append(S(4, [
    ("It's very hot in here.", ["Shall I open a window?",
                                "Yes, it is here.",
                                "No, it is cold outside."], 0, ""),
    ("Have you met Henry before?", ["No, I don't think we have.",
                                    "Yes, I meet him.",
                                    "No, I will meet him before."],
     0, ""),
    ("Do you like visiting museums?", ["Not really, I find them "
                                       "boring.", "Yes, I visit.",
                                       "No, I liked it."], 0, ""),
    ("I've broken my glasses.", ["Can they be repaired?",
                                 "Yes, I broke them.",
                                 "No, the glasses are fine."], 0,
     ""),
    ("John's going to London.", ["When does he leave?",
                                 "Yes, he went.",
                                 "No, London is far."], 0,
     "«is going» — kelasi zamon, B esa o'tgan."),
    ("When do you study?", ["Usually in the evening.",
                            "Yes, I study.", "At the university."],
     0, "C — «Where?» javobi."),
    ("Do you like my new shoes?", ["They really suit you.",
                                   "Yes, I like.", "No, they are "
                                   "my shoes."], 0, ""),
    ("Be careful.", ["Don't worry, I will.", "Yes, I am careful "
                     "yesterday.", "No, you be careful."], 0, ""),
]))

# ---- 12-13 mashqlar -> 5-bosqich ------------------------------
BOOK_SETS.append(S(5, [
    ("I hate basketball.", ["Neither do I.", "So do I.",
                            "Yes, I hate you."], 1,
     "Inkor MA'NOLI gap, lekin shakli TASDIQ («I hate») — shuning "
     "uchun «So do I». «Neither» faqat «don't/can't» kabi inkor "
     "shakldan keyin keladi."),
    ("Can you give me some money?", ["How much do you need?",
                                     "Yes, I can money.",
                                     "No, you give me."], 0, ""),
    ("Let's walk to the park.", ["It's too far, let's take a bus.",
                                 "Yes, I walked.",
                                 "No, the park walks."], 0, ""),
    ("When did you arrive?", ["Only ten minutes ago.",
                              "Yes, I arrived.", "By taxi."], 0, ""),
    ("Shall I open the door?", ["Yes, please do.", "Yes, I shall.",
                                "No, I opened it tomorrow."], 0, ""),
    ("I got a letter from Paul this morning.", ["What did he say?",
                                                "Yes, I got it.",
                                                "No, Paul got a "
                                                "letter."], 0, ""),
    ("How's your sister?", ["Much better, thanks.",
                            "She is my sister.",
                            "Yes, she is."], 0,
     "«How is...?» = ahvoli qanday."),
    ("How far is it to Manchester?", ["About sixty miles.",
                                      "Yes, it is far.",
                                      "Two hours by train."], 0,
     "C — vaqt, savol esa MASOFA so'rayapti. Ikkalasi ham ishonarli "
     "ko'rinadi — «How far» va «How long» ni ajratish shart."),
]))

BOOK_SETS.append(S(5, [
    ("Could you give me the butter?", ["Here you are.",
                                       "Yes, I could.",
                                       "No, the butter is here."], 0,
     ""),
    ("John hates shopping.", ["So does my brother.",
                             "So do my brother.",
                             "Neither does he."], 0,
     "B — «does» kerak, «do» emas. Uchinchi shaxs birlik."),
    ("I've already done my homework.", ["That was quick!",
                                        "Yes, you have done.",
                                        "No, do it now."], 0, ""),
    ("What's the date today?", ["The twelfth of March.",
                                "It's Tuesday.", "Yes, it is today."],
     0, "B — «What day?» javobi. Date va day ni ajrating."),
    ("Nick, have you got anything special for tonight?",
     ["Nothing at all, why?", "Yes, tonight is special.",
      "No, I got it."], 0, ""),
    ("Shall we have a snack lunch in a pub for a change?",
     ["Why not? I'm tired of the canteen.",
      "Yes, we had lunch there.", "No, I don't have change."], 0,
     "«for a change» = xilma-xillik uchun; C uni «mayda pul» deb "
     "tushungan."),
    ("Would you like a cup of tea?", ["I'd love one, thanks.",
                                      "Yes, I like tea.",
                                      "No, I would."], 0,
     "B — savol TAKLIF, «tea yoqadimi» degani emas."),
    ("Do you mind if I turn the television off?",
     ["Not at all, nobody is watching.", "Yes, turn it off.",
      "No, I mind."], 0, ""),
]))


# =====================================================================
#  QURISH
# =====================================================================
def _remap(note, shift):
    """Izohdagi «B — ...» kabi harflarni yangi joylashuvga moslaydi.
    Bir vaqtda almashtiriladi, aks holda zanjir hosil bo'lardi."""
    if not note or not shift:
        return note
    import re
    return re.sub(
        r"(?<![\w'’])([A-C])(?![\w'’])",
        lambda m: LET[(LET.index(m.group(1)) + shift) % 3],
        note)


def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase).

    JAVOB O'RNI AYLANTIRILADI. Manba ro'yxatida to'g'ri javob doim
    birinchi turadi — o'qish oson bo'lsin uchun. Agar shundayligicha
    qoldirilsa, o'quvchi tinglamasdan «hamma vaqt A» deb 100%
    olardi. Shuning uchun har savolda variantlar aylantiriladi va
    to'g'ri javob A/B/C bo'ylab teng tarqaladi."""
    out = []
    n = 0
    # SETS — o'zimiz tuzgan, sof bosqichma-bosqich mashqlar.
    # BOOK_SETS — Multilevel Master audioscriptidan olingan HAQIQIY
    # imtihon gaplari. Ular bir xil bosqich ichida o'zimiznikidan
    # KEYIN keladi (order 100 dan boshlanadi), ya'ni bola avval
    # tayyorlanadi, keyin haqiqiy imtihon gapini eshitadi.
    for src, base, book in ((SETS, 0, False), (BOOK_SETS, 100, True)):
      for si, st in enumerate(src):
        step = st["step"]
        for i, (say, opts, ci, note) in enumerate(st["items"], 1):
            assert len(opts) == 3, (step, i)
            shift = (n % 3 - ci) % 3
            n += 1
            new = [None] * 3
            for k, t in enumerate(opts):
                new[(k + shift) % 3] = t
            ci2 = (ci + shift) % 3
            note2 = _remap(note, shift)
            labelled = [f"{LET[k]}. {t}" for k, t in enumerate(new)]
            expl = f"To'g'ri javob: {LET[ci2]}. Eshitilgan gap: «{say}»."
            if note2:
                expl += " " + note2
            if book:
                expl += (" (Gap Multilevel Master audioskriptidan "
                         "olingan — haqiqiy imtihon materiali.)")
            out.append((
                KIND, step,
                {"say": say,
                 "rate": STEP_RATE[step],
                 # 2026-08-26, Jahongir: "2 marta aytiladi CEFRdagi
                 # barcha listeninglar". Yuborgan audiosini o'lchab
                 # ko'rdim: har gap ikki marta o'qiladi, orasida
                 # ~3.7 soniya jimlik, javob uchun yana ~5-6 soniya.
                 # Telefonda 3.7 soniya jimlik "buzilib qoldi"
                 # taassurotini beradi, shuning uchun orasi 2
                 # soniya qilindi — takror soni esa aynan 2 ta.
                 "plays": 2,
                 "gap_ms": 2000,
                 "options": labelled,
                 "step": step,
                 "order": base + si * 10 + i,
                 "book": book,
                 "hint": HINT,
                 # DIQQAT: "prompt" YUBORILMAYDI — aytilgan gap
                 # ekranda ko'rinmasligi kerak, aks holda tinglash
                 # mashqi o'qish mashqiga aylanadi.
                 },
                labelled[ci2], expl, None, None))
    return out


def seed_reply(db):
    """Idempotent: bor bo'lsa qayta yozmaydi (hech narsa o'chmaydi)."""
    import json
    import models
    have = {
        (json.loads(r.payload).get("step"),
         json.loads(r.payload).get("order"))
        for r in db.query(models.PracticeItem)
        .filter(models.PracticeItem.skill == SKILL,
                models.PracticeItem.kind == KIND).all()}
    cnt = 0
    for kind, step, payload, answer, explain, alt, para in build_rows():
        if (payload["step"], payload["order"]) in have:
            continue
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=step,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt, explain=explain, is_active=1))
        cnt += 1
    if cnt:
        db.commit()
    return cnt
