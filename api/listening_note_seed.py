# -*- coding: utf-8 -*-
"""CEFR LISTENING 2-QISM — NOTE COMPLETION (2026-08-26).

Jahongir: "endi qolgan partlarga ham 100tadan tuzib qoy."

FORMAT (kitobdan): "You will hear someone giving a talk. For each
question, fill in the missing information in the numbered space.
Write ONE WORD and/or A NUMBER for each answer."

MATN MANBASI. 17 ta ma'ruza — hammasi Multilevel Master
audioskriptining Part 2 qismidan AYNAN olingan. Qaydnoma
qatorlari va bo'shliqlar shu yerda tuzildi, LEKIN har bir javob
matnda aynan borligi generatorda tekshirilgan (butun so'z
sifatida) — ya'ni o'zimizdan so'z qo'shilmagan.

EKRANDA NIMA TURADI. Butun qaydnoma ko'rinadi, joriy bo'shliq
esa "▶" bilan belgilanadi. Bu imtihondagidek: bola qaydnomani
oldindan o'qib, qayerda nima kelishini taxmin qiladi.

BITTA TEXNIK QOIDA. Javob "hour", "day", "week" kabi so'z
bo'lmasligi kerak: tekshiruvchi _ielts_norm o'lchov so'zlarini
olib tashlaydi va bunday javob BO'SH satrga aylanib, har qanday
narsa to'g'ri sanalardi. Buni test tekshiradi.
"""

SKILL = "ielts_listening"
KIND = "cefr_note"
GAP = "…………"
RATE = 0.92
INSTR = "Write ONE WORD and/or A NUMBER for each answer."


NOTE_TIPS = [
    ('Bu mashq nima',
     "Bitta ma'ruza eshitiladi. Ekrandagi qaydnomada raqamlangan bo'shliqlar bor — har biriga BITTA so'z yoki raqam yoziladi. Ikki so'z yozsangiz nol ball.",
     ''),
    ("Audio boshlanishidan oldin qaydnomani o'qing",
     "Har bo'shliqqa qanday so'z kerakligini oldindan ayting: ot? son? oy nomi? joy nomi? Shunda quloq aynan o'shani kutadi.",
     '«The class has a maximum of ……… students» -> SON kerak.'),
    ('Qaydnoma matn TARTIBIDA boradi',
     "1-bo'shliq ma'ruzaning boshida, oxirgisi oxirida keladi. Bittasini o'tkazib yuborsangiz, keyingisini kutib turing — orqaga qaytmang, aks holda ikkalasini ham yo'qotasiz.",
     ''),
    ("Javob AYNAN eshitilgan so'z bo'ladi",
     "Bu qismda parafraz qilinmaydi: kerakli so'z audioda aynan aytiladi. Qaydnomadagi ATROFDAGI so'zlar esa parafraz bo'ladi — ular sizga qayerda ekanini ko'rsatadi.",
     ''),
    ('Tuzatishga tayyor turing',
     "Ma'ruzachi ko'pincha avval bir narsa aytib, keyin uni o'zgartiradi: «not on 7th July as it says on the website» — to'g'ri javob KEYINGISI.",
     ''),
    ('Imlo muhim',
     'Nomlar va manzillar odatda harflab aytiladi. Eshitganingizni darrov yozing, keyin tekshirasiz.',
     ''),
    ("Bo'sh qoldirmang",
     "Ishonchingiz komil bo'lmasa ham biror narsa yozing — bo'sh javob aniq nol, taxmin esa ba'zan to'g'ri chiqadi.",
     ''),
]


TALKS = [
    # ---- audioskript Part 2, EXERCISE 1 ----
    {"no": 1,
     "title": 'SKY JAM — a new video game',
     "say": 'Hi everyone. I’m going to tell you about a new video game that I’ve played a lot recently, called Sky Jam. It’s produced by the same company that made Road Jam a few years ago, which was set in a city of course. Instead of streets and huge buildings, though, you’ll find yourself living in a rainforest in this game. It’s an unusual game because you have to answer questions in order to make progress, as well as by moving through the environment. You’ll be asked all sorts of things regarding insects, which you have to learn on the way from the many helpful creatures you meet, such as butterflies and bats. There are 30 levels in the whole game, which are supposed to become more and more challenging as you go on. I found the one called ‘the money’ almost impossible, even though it comes well before the last level, called ‘the frog’, which didn’t seem so difficult. There are lots of things to love about this game. The story you learn about as you continue through the game is fantastic, second only to the characters you can play, who are lovely, and extremely interesting too. Learning to play the game is easy and fun, too. Unfortunately, unlike the eight players who could play against each other in Road Jam, six people at the most can join in this game at any one time. I found this to be a few too many, though, and preferred playing in a group of four. You can find out more about the game online. If you’re interested, visit the company’s website www.lombardio.com. I’ll spell that for you: it’s L-O-M-B-A-R-D-I-O. Thank you for listening.',
     "items": [
         ('The game is set in a %s.', 'rainforest'),
         ('To make progress you answer questions about %s.', 'insects'),
         ('You learn from creatures such as butterflies and %s.', 'bats'),
         ("The hardest level is called 'the %s'.", 'money'),
         ('After the characters, the best thing is the %s.', 'story'),
         ('The speaker preferred to play in a group of %s.', 'four'),
     ]},
    # ---- audioskript Part 2, EXERCISE 2 ----
    {"no": 2,
     "title": 'SCHOOL PHOTOGRAPHY COMPETITION',
     "say": 'Listen, everyone! I’ve got some information about this year’s school photography competition. As you’ll probably remember, last year’s competition asked you to focus on the topic of travel, but photos should have something to do with the environment this time. As in previous years, there are certain things that we want the photographs to include. We want all the pictures to have wildlife in them, so we’re not looking for photos that only show landscapes or people. The head teacher has decided to ask someone from outside the school to judge the competition this year. She was hoping that local artist Sally Graves would be able to judge the entries, but she’s actually away at that time. Writer James McKay has agreed to help us instead. I’m sure many of you have heard of him, as he’s quite famous and was born not far away from here, too. It was felt that most keen photographers already have the photography books or equipment they need, so the organisers have decided that the winner will receive a photography course run by Central College instead. The College was also hoping to have a small photography exhibition for winners of all the school photography competitions in the area, but their gallery’s too busy putting on other shows, I’m afraid. The winner of the competition will be announced on 11th March. If you wish to enter, please make sure we receive your photos by 15th February, as the judging will take place on 19th February. So if you’re interested, send your entry to the school secretary, Mrs Mitchell, not to me or the head teacher. I’ll give you her email address – it’s k dot Mitchell, that’s spelt M-I-T-C-H-E-double-L at school dot com. Good luck!',
     "items": [
         ('This year the topic is the %s.', 'environment'),
         ('Every photograph must include %s.', 'wildlife'),
         ('The judge will be the writer James %s.', 'McKay'),
         ('The prize is a photography %s.', 'course'),
         ('Entries must arrive in %s.', 'February'),
         ('The winner is announced in %s.', 'March'),
     ]},
    # ---- audioskript Part 2, EXERCISE 3 ----
    {"no": 3,
     "title": 'ACTING CLUB',
     "say": "Hello everyone. I'd like to tell you about this wonderful acting club I joined recently. The best thing about it is the teacher. We're really lucky to have someone who's actually quite famous. Her name's Alice Fisher and she's appearing in a play at the big theatre in town at the moment. She plays a policewoman in that, but you'll probably know her better as the farmer in the series Green Valley that was on last year. She's worked as a professional theatre actor for about 10 years, as well as having 3 years experience of appearing in serious drama. She's also spent 7 years working in comedy productions, so she has lots of different talents. The sess ions are always fun and are split into two sections. In the first section, Alice will be playing a character who's a member of a club. In the first part, rather than practising anything to do with movement of the body, we focus instead on improving how to control the voice as an actor. In the second part, we practise our performance skills. If you're interested in coming to the drama club, you'll need to know where to come, of course. The club actually hires a room from the university to run the classes. It's much cheaper to do it there than at the college or the acting school. The sessions are on Wednesdays. At the moment, we're practising for a play which will be on at the town theatre soon. Its name is The Passenger, and we're hoping that this latest one will be as popular as the last production the club did, which was called Reality. It was a big success, apparently. We've got our last practice for the new play on the 13th of July, with audiences able to come and see it from the 20th of July for one week. Thanks for listening.",
     "items": [
         ('In the play at the theatre the teacher is a %s.', 'policewoman'),
         ('In Green Valley she played a %s.', 'farmer'),
         ('The first part of the session is about the %s.', 'voice'),
         ('The club hires a room from the %s.', 'university'),
         ('Sessions take place on %s.', 'Wednesdays'),
         ('The play they are preparing is called The %s.', 'Passenger'),
     ]},
    # ---- audioskript Part 2, EXERCISE 4 ----
    {"no": 4,
     "title": 'VISIT TO THE SCIENCE MUSEUM',
     "say": "Hi everyone. I'm going to tell you about my trip to the new science museum last week. I went with my family and we looked around the whole museum. There are loads of different rooms and each one contains displays about a particular topic. We spent ages looking around the room that was all about space. And even longer in the one with loads of stuff on energy, which I thought was the best bit. The museum's free, but there are also two special exhibitions that you have to pay for. You can't go into the one on health yet because it doesn't open for another couple of weeks. I'd like to go back and see that. The other exhibition on computers was good though. As well as the display of the science museum, there's also the museum's exhibition on the computer. There are lots of things you can actually do there too. My brother made this fantastic car that went quite fast using only power from the sun, while I created a rocket that used gas to fly. It went really high! As well as the in teresting things to see and do, there's a nice shop. My mum and dad let me get something because it was my birthday. As I said, not all sets to choose from, it took me ages to decide which one I wanted. They have the usual toys and games – and a few nice books there too. You can also take a tour of the museum with a guide. When we arrived, they said we'd have to wait at least sixty minutes for the 80-minute tour because it's so popular, so we decided against it. If you want to go, the entrance is on Lockhart Road. I'll spell it for you. I was soon told it was an open-air museum. And out for you. It's L-O-C-K-H-A-R-T Road. Thanks for listening.",
     "items": [
         ("The speaker's favourite room was about %s.", 'energy'),
         ('The exhibition on %s has not opened yet.', 'health'),
         ("His brother's car was powered by the %s.", 'sun'),
         ("The speaker's rocket flew using %s.", 'gas'),
         ('The shop sells toys, games and a few %s.', 'books'),
         ('The entrance is on %s Road.', 'Lockhart'),
     ]},
    # ---- audioskript Part 2, EXERCISE 5 ----
    {"no": 5,
     "title": 'SCHOOL TRIP TO THE FARM',
     "say": 'Good morning everyone. I’m going to tell you about the school trip to the farm tomorrow. As I told you last week, you need to wait for the bus by the school gate, so don’t go to the bus stop or come straight into the playground like you usually do. The farm is providing us all with a nice packed lunch, so there’s no need to bring one yourself. It’d be great if you could make sure you’ve got a drink, though, as it can get quite hot on the bus. There are lots of different animals on the farm. You’re all going to have a go at brushing the horses just after we arrive there at about 9 a.m. Shortly after this, you’ll learn what farmers give lambs to eat, and you’ll be able to give them their breakfast, too. As well as the animals, the farm has lots of activities students can take part in. We’re going to do some climbing on the special wall they have there after lunch, and maybe next time we can try one of the other activities like fishing or playing baseball. We’ll be setting off back to school at about 3.30 p.m., and will be back here at 4.15, so 45 minutes after the usual school finish time of 3.30. Please could you let your parents know, especially if they usually come to the school to pick you up. If you or your parents want to find out more about the farm before we go, you can visit their website and there’s loads of information about it on there. I’ll give you the website address: it’s www dot caffertys dot farm dot com. I’ll spell that for you: it’s C-A-double F-E-R-T-Y-S dot farm dot com. OK, see you all tomorrow.',
     "items": [
         ('Wait for the bus by the school %s.', 'gate'),
         ('Lunch is provided, but bring a %s.', 'drink'),
         ('On arrival students will brush the %s.', 'horses'),
         ('Shortly after that they will feed the %s.', 'lambs'),
         ('After lunch there will be %s on a special wall.', 'climbing'),
         ("The farm's website is www.%s.farm.com", 'caffertys'),
     ]},
    # ---- audioskript Part 2, EXERCISE 6 ----
    {"no": 6,
     "title": 'SATURDAY MORNING MUSIC CLASSES',
     "say": 'Listen, everyone. I know some of you are interested in learning to play a musical instrument so I have some information about Saturday morning music classes that are starting this week. There are many classes to choose from for a range of different instruments. You can learn anything from the drums to the guitar. The violin teacher the school usually uses can’t make it on Saturdays, but why not have a go at the flute if you prefer classical music. When you arrive at the school, you’ll need to collect your instruments. You probably know that these are normally kept in the large cupboard next to the technology room but we’ll make sure they’re all ready for you in the drama room so go straight there, please. You’ll need to tell your parents about the cost, of course. They can pay in two different ways: if they decide to pay for each individual class, it’ll be £7.75, or they can pay per term, in which case it works out a little cheaper at £72. There’ll be an end of term concert for all students, which will take place on 24th June, and not on 7th July as it says on the school website. You’ll be able to play solo, that’s by yourself, or with others. Last year, there were several students who joined together in a band and they played together at the concert. This year, though, we’d like to include more people and have an orchestra that students can play in. Family and friends are welcome to come and listen. If you or your parents want more information, you’ll need to email Mr Driscoll, the music teacher on driscoll at school dot net. I’ll spell that for you: it’s D-R-I-S-C-O-double-L at school dot net.',
     "items": [
         ('The %s teacher cannot come on Saturdays.', 'violin'),
         ('For classical music, try the %s instead.', 'flute'),
         ('Instruments will be waiting in the %s room.', 'drama'),
         ('Paying by term costs %s pounds.', '72'),
         ('The concert is on the 24th of %s.', 'June'),
         ('This year they want to form an %s.', 'orchestra'),
     ]},
    # ---- audioskript Part 2, EXERCISE 7 ----
    {"no": 7,
     "title": 'HELPING THE ENVIRONMENT',
     "say": 'This morning we’re continuing to look at environmental problems to see what we can do to help. And we can make a difference if we try. We often forget that as people who go shopping, we have a lot of power. If one company does something we don’t like we can always shop somewhere else. Then there’s the amount of plastic that comes with the goods we buy. Try buying things that aren’t wrapped in it. And if you’re offered a bag and you don’t need one, just say ‘no thanks’. And any plastic bags you have at home, don’t throw them away. Put them away somewhere until your next shopping trip and use them then. On the subject of throwing stuff away, I try to keep things that other people might be able to use. There are always charity shops which are very happy to help you recycle your old clothes or things in the house. Knowing that someone else is getting pleasure from something you no longer need is a lovely feeling. Pollution is of course a big problem, and we often feel that as individuals we have no power to make any difference. But that’s not true. Find out what some of the local environmental problems are and see how you can help. Get together with friends and help to clear the rubbish from local rivers or collect litter from the streets around your home to keep the area looking tidy. Finally, let’s turn to energy. Cars are here to stay for the moment, and it would be difficult to ask people not to use them at all. But we should all try to avoid making unnecessary car journeys. Go by bike or public transport sometimes or, if you work in the same area as your neighbour, try car-sharing. Take it in turns to drive to work.',
     "items": [
         ('Buy things that are not wrapped in %s.', 'plastic'),
         ('Keep old bags until your next shopping %s.', 'trip'),
         ('Old clothes can go to %s shops.', 'charity'),
         ('With friends, clear rubbish from local %s.', 'rivers'),
         ('Avoid unnecessary car %s.', 'journeys'),
         ('If a neighbour works nearby, try car-%s.', 'sharing'),
     ]},
    # ---- audioskript Part 2, EXERCISE 8 ----
    {"no": 8,
     "title": 'THIS WEEK ON THE RADIO',
     "say": "Before tonight's news, let me tell you about some of the shows we have for you this week, so you can make a note of them in your diary. There are a few changes to our regular programmes, so listen carefully to make sure you don't miss any of your favourites. Tonight at 8.30, John Seymour will present this week's wildlife documentary. John entertained us all previously with hi s trip to the safari park when he went along to meet the elephants. This time, John will be telling us about how we can recognise the wildflowers in our gardens. Then, our first change of schedule. Apologies to listeners. Looking forward to Writer's World and our interview with Frances Sellhurst on how to get ideas for your next novel. We've had to rearrange this interview for next week as Frances is attending a conference. Instead, we'll be talking with an expert about how you can make use of the internet to get your next book published. On Thursday at 8, we have Sports Night. Sports Night, as usual, with a look at next weekend's football. Most of the games from last Saturday were cancelled due to the terrible weather, so there are no reports on those match es. But our experts will be looking forward to seeing some action this Saturday and will be trying to predict results, as usual. Join our team at 8. And finally, our reporters. Reporter Sally Williams will be in town next Friday morning. She'll be interviewing people for our weekly programme, Money Matters, starting from 10, not the usual 9. If you'd like the chance to speak to her and share your views of your experiences and any problems you may have, meet Sally at the main door of the library, not the normal meeting place at the town hall. Which is closed due to building work.",
     "items": [
         ('Tonight John Seymour talks about %s in gardens.', 'wildflowers'),
         ('Last time he went to a safari park to meet the %s.', 'elephants'),
         ('Frances Sellhurst cannot come because of a %s.', 'conference'),
         ('Instead there is a talk on publishing using the %s.', 'internet'),
         ("Saturday's games were cancelled because of the %s.", 'weather'),
         ('Sally Williams will be at the main door of the %s.', 'library'),
     ]},
    # ---- audioskript Part 2, EXERCISE 9 ----
    {"no": 9,
     "title": 'TRAINING DAY',
     "say": 'Can I just say something about the training day next week. You should all receive your programme by email shortly. We’ve had to make changes to rooms and even now some of the training sessions may have to be held in a different building. But we’ll let you know if this happens. Some of you have asked about changing to a different session than the one you signed up for. We’ve tried to do this when it’s been possible but as some training sessions are full it will sometimes not be possible. We will let you know by email on 13 September the full list of names of people going to each session. The trainers will email you the materials they’ll be using during the sessions for you to have a look at before the training day. There are some tasks for you to complete in preparation for your session. Please make sure you print out these materials and complete the exercises before you attend. At the end of the training day you will all be given a questionnaire for your comments on each of the sessions you attended. Could you please make sure you complete this and give it to the training manager? We are using a new company for this event and are keen to see how well the day goes. Because staff in the company restaurant will also be attending training sessions, the restaurant will not be open. We are arranging cold food, teas and coffee for everyone. Could you email the restaurant manager before the end of this week and let him know if you have any special dietary requirements. Finally, can I remind you to check the noticeboard outside room 134 for any last-minute changes. Yes, we’ll email you all important information but several of you have complained that you haven’t received our messages, so to be absolutely sure you’re up to date, check the noticeboard.',
     "items": [
         ('The programme will arrive by %s.', 'email'),
         ('The list of names will be sent on 13 %s.', 'September'),
         ('Trainers will send %s to look at beforehand.', 'materials'),
         ('At the end everyone gets a %s.', 'questionnaire'),
         ('The company %s will be closed that day.', 'restaurant'),
         ('Check the noticeboard outside room %s.', '134'),
     ]},
    # ---- audioskript Part 2, EXERCISE 10 ----
    {"no": 10,
     "title": "THE SPEAKERS' CLUB",
     "say": 'Russell: And finally, news of an interesting club that started recently and meets here every week. The Speakers· Club is aimed at anyone who needs to develop their public speaking skills. Perhaps you have to give talks to colleagues at work or need to practise a presentation you have prepared for a job interview. The Speakers· Club offers a weekly meeting in the main hall, where members can learn from each other as well as through talks given by highly experienced speakers from the world of business or entertainment. We look at everything from body language and eye contact to storytelling and delivery. A typical session starts at 7.00 with tea, coffee and biscuits before we listen to the speaker and start looking at a particular topic. Members are then given the chance to change a presentation they’ve prepared before the session so that it includes the ideas presented by the speaker. We also invite you to enter one of our speech competitions each year. We understand that clubs like ours might not suit everyone and we like to give you the chance to see for yourself how we operate before you join. So, we invite anyone to attend their first session for free. However, in order for us to manage the numbers of people attending, please make sure you reserve a place first or you may not be able to attend. If you do decide to join us, annual membership is £170 per year. Arrangements can be made to pay the membership fee once a month. Membership allows you to attend all sessions during the year and gives you access to private areas of the website and the chance to take part in our social events.',
     "items": [
         ('Meetings are held in the main %s.', 'hall'),
         ('Sessions begin at 7.00 with tea, coffee and %s.', 'biscuits'),
         ('Members may change a %s they have prepared.', 'presentation'),
         ('Each year the club holds speech %s.', 'competitions'),
         ('Your first session is %s.', 'free'),
         ('Annual membership costs %s pounds.', '170'),
     ]},
    # ---- audioskript Part 2, EXERCISE 11 ----
    {"no": 11,
     "title": 'PHOTOGRAPHING PEOPLE — course tips',
     "say": 'William: I had a great time away on holiday and one of the things I did was go on a two-day photography course about taking photos of people. It was for beginners and I was given quite a few tips, some of which I think are really useful. For example, getting your position correct is really important. They said a common mistake is to stand too far away from the person. You get a much better result if you get close to them as they take up more of the photo. It’s also important to make sure the camera is at the same height as the person, especially if you’re taking one of a child. A really useful tip was to pay attention to the background. The person will stand out much more if the background is as plain as possible. This will help you to focus on the subject of your photo. Although most smartphones come with a flash to provide extra light, they suggested we try to make as much use as possible of daylight. Doing this will make the colours more accurate and the photo will appear more natural. We’re all used to asking someone to ‘say cheese’ when we’re about to take their photo. To get a more interesting picture, they recommended taking a photo of the person when they don’t know you’re about to do it. Perhaps they’re reading or looking out of the window. Finally, they told us to take plenty of photos so we can practise our skills. They said we should aim to take at least three photos of people every day. These can be of friends and family or even strangers, if you ask their permission.',
     "items": [
         ('The course lasted %s days.', 'two'),
         ('A common mistake is standing too far %s.', 'away'),
         ('Keep the camera at the same %s as the person.', 'height'),
         ('The background should be as %s as possible.', 'plain'),
         ('Use as much %s as you can.', 'daylight'),
         ('Take at least %s photos of people every day.', 'three'),
     ]},
    # ---- audioskript Part 2, EXERCISE 12 ----
    {"no": 12,
     "title": "WHAT'S ON THIS SUMMER",
     "say": 'Ellen: If you’re looking for things to do over the summer, there’s lots going on in the area. I’ll give you an idea of what you can do now, but for a full programme of events text 1576 and we’ll send you a link to all the information you need. To give you a taste of what’s on offer, the Activity Centre is running a wide range of activities for all the family. There’s climbing for beginners. This is indoors and will be led by experienced teachers. The centre has also organised a walk along the coast path for a look at some of the creatures you can find there. The centre is open seven days a week, with a special open day on the thirteenth of June to give you an idea of what else is on offer. As you know, our town has a very long history, and those with an interest in the past can sign up for one of the guided walks the History Group has organised. Find out where a very well-known celebrity was born and learn about local industry in the past. You can find out more at the History Centre, which is located in the central library. For film lovers, the Arts Centre has a full programme of films running throughout the summer months. And the Book Festival, which starts on the fourteenth of August, has several speakers on its programme and book readings by some well-known authors. This year they’ll be organising a question and answer session for anyone interested in writing poetry. The Arts Centre expects this to be quite popular, so you should call them first to book a place.',
     "items": [
         ('For the full programme, text %s.', '1576'),
         ('Climbing for beginners takes place %s.', 'indoors'),
         ('The coast path walk looks at %s.', 'creatures'),
         ('The History Centre is in the central %s.', 'library'),
         ('The Book Festival starts on the %s of August.', 'fourteenth'),
         ('There will be a session on writing %s.', 'poetry'),
     ]},
    # ---- audioskript Part 2, EXERCISE 13 ----
    {"no": 13,
     "title": "MILBURN'S STORE — announcements",
     "say": 'Woman: Welcome to Milburn’s. If you’re looking for a sale or for something unusual, don’t forget our Thursday ‘Special Buy’ day where you’ll find some great offers. These change every week and are removed from the shelves at the end of the day. This Thursday you’ll be able to buy a special gift for your pet with lots of items at low. low prices. Come early and don’t miss our offers. Are you interested in a career with Milburn’s? we’re looking for new staff in various areas of the business. There are now opportunities to join our trainee manager programme and several jobs for cleaners. We are proud of our staff and like to think they’re proud to be part of the Milburn family. Why not speak to our manager today if you’re interested in joining us? Or pick up our magazine at the exit for details about how to apply. As the New Year approaches we know you’ll need to get your shopping done ready for all the celebrations. We’ll be opening until 10.30 on Friday evening to give you time to get ready for the big day. Don’t forget we’ll be closed on the first but open again on the second, when we return to normal opening hours. We value our local community and are always looking for the chance to help out where we can. This month we’re supporting the local Arts Project and the Children’s Theatre Group. When you pay for your shopping you’ll be given a ticket. To show your support, choose which of the organisations you would like to give this to by putting it in the box by the exit. We’ll turn these into cash when they are counted up at the end of the month.',
     "items": [
         ("'Special Buy' day is every %s.", 'Thursday'),
         ('This week there are gifts for your %s.', 'pet'),
         ('There are jobs for trainee managers and %s.', 'cleaners'),
         ('Details of how to apply are in the %s.', 'magazine'),
         ('On Friday the store stays open until %s.', '10.30'),
         ('Put your ticket in the box by the %s.', 'exit'),
     ]},
    # ---- audioskript Part 2, EXERCISE 14 ----
    {"no": 14,
     "title": 'STARTING UNIVERSITY',
     "say": "This will be a very exciting time for you. You've got the grades you needed and you're off to university. For many of you, this will be the first time away from home. Write a list of things you should take with you, for example, your passport, if you're planning to go travelling. You'll certainly need all the documentation the university has sent you about your course or accommodation. Don't bring too many household items with you. You'll be able to buy a lot of things at university. When you arrive and go to your room, check that everything is as it should be and engaged. Report anything that looks damaged. You don't want to be blamed for this and be asked to pay any costs involved. This is also the time to get to meet new people. Don't lock yourself away in your room, but go to the kitchen, as this is always the first place to introduce yourself to other students. During your first week, you can enjoy Freshers' Week. This is the time to find out what you need to do. 18. Learn about all the clubs and societies you can join at university. These are great ways to get to know students doing different subjects. These people will help you forget about your studies when you need to relax and not talk about work. It's sensible to limit yourself to signing up to a maximum of five groups, or you'll be receiving emails for weeks to come. Don't forget the important things you need to do. Things like registering with the local doctor as soon as you can. And think about your weekly shopping list. Don't spend too much, but at the same time, make sure you don't go hungry. And remember to put your name on your food. A shared fridge sometimes leads to arguments.",
     "items": [
         ('Take your %s if you plan to travel.', 'passport'),
         ('Do not bring too many %s items.', 'household'),
         ('Report anything that looks %s.', 'damaged'),
         ('The best place to meet other students is the %s.', 'kitchen'),
         ('Join no more than %s groups.', 'five'),
         ('Register with the local %s straight away.', 'doctor'),
     ]},
    # ---- audioskript Part 2, EXERCISE 15 ----
    {"no": 15,
     "title": 'FRENCH CLASS — changes',
     "say": "Hello everybody and welcome to the class. I'm pleased to see so many of you here today. But don't worry, there won't be any more of you. There's always a maximum of 15 in the class and a minimum of 8. Before we start, I'd like to tell you about the course. Some of the information you'll probably know already, but some of it has changed. Your class will still be on Tuesday evenings, but it won't start at 7 o'clock. It will start at the later time of 7.30 and will end at 9.30, not 9 o'clock. I hope that change is OK for everyone. Unfortunately, I can't be here any earlier than that. Another change is the room. Next week we need to move to the second floor, to the room on the right. Opposite the art room. That's room 26. Today is the only time we'll be here in room 12. The course book will be the same as before, that is, starting French. I see some of you have already bought it. That's good. However, if you want to buy it from us, it costs £8. You can order it today, but it takes two weeks, so you won't have it until the 1st of October. One more thing. During the last week of term, there is an international evening at the college. There will be traditional dancing from different countries, and every class is asked to provide some food. I thought we could take some French cheese, but any other suggestions are welcome. And finally, let me remind you that most of your lessons will be completely in French, so let's begin now, shall we?",
     "items": [
         ('The class has a maximum of %s students.', '15'),
         ('Lessons will now start at %s.', '7.30'),
         ('From next week the room is on the %s floor.', 'second'),
         ('The new room is opposite the %s room.', 'art'),
         ('The course book costs %s pounds.', '8'),
         ('The class will take French %s to the international evening.', 'cheese'),
     ]},
    # ---- audioskript Part 2, EXERCISE 16 ----
    {"no": 16,
     "title": 'THREE HOLIDAYS TO RECOMMEND',
     "say": 'Woman: I love being a travel writer, and I love talking about my trips, so thank you for inviting me into the studio today! Right, I’m going to tell you about three different holidays that I can recommend to everyone. The first is a good, year-round sun destination: The Canary Islands. These islands are known for their big busy seaside hotels in Tenerife and Lanzarote, but there are less well-known islands, like La Gomera. If you want a quieter experience, you can stay in traditional villages there and try out the excellent walking routes in the hills. Johnson’s Travel currently has two-week holidays in La Gomera from as little as £600 per person, or £900 with an extra week. Another island you might like to try is Sardinia, in the Mediterranean. And if you and your family want a little more adventure, then a water sports holiday could be the one for you. Water skiing and sailing are always popular, and you could even try for a diving qualification while you’re there on one of the specially organized activity weeks offered by SunWorld! SunWorld designs fantastic holidays, and the peak season for families begins in July. It’s important to remember, however, that the month of June is reserved for adults only. Finally, if you’re not interested in lying on the beach, why not try something completely different? On a trip to Iceland, you and your family could first visit all the main attractions of Reykjavik on a special guided bus tour. Then take a traditional Icelandic trip on the back of a horse to the Blue Lagoon, before flying off to the lovely snow-covered mountains of the Askja region. A week with Travel the World costs £1,200 per adult for accommodation and return flights to Reykjavik and on to Askja. Rates for children are lower.',
     "items": [
         ('A quieter Canary island is La %s.', 'Gomera'),
         ('Two weeks there start at %s pounds.', '600'),
         ('Another island worth trying is %s.', 'Sardinia'),
         ('On an activity week you can qualify in %s.', 'diving'),
         ('The month of %s is for adults only.', 'June'),
         ('In Iceland you ride a %s to the Blue Lagoon.', 'horse'),
     ]},
    # ---- audioskript Part 2, EXERCISE 17 ----
    {"no": 17,
     "title": 'SEMINAR ON THE TOY INDUSTRY',
     "say": 'Woman: Good morning and welcome to our seminar on the toy industry. I’d like to start by saying a few words about what you can expect from this seminar, since some of the details on the original plan have changed. After the introduction by Sally Connor, Kenji Nakamura will give a talk. That’s from 10 a.m. to 11 a.m. He will tell you about the most recent developments in the toy industry in Japan and will show a short film. This will be followed by half an hour of questions. Then at 12.00, we’ll have a break for lunch. This will be a buffet meal, served in Victoria Hall, which is on the opposite side of the building, next to the library. After lunch, we’ll return here for Toys in Britain: Success and Failure. This talk will be given by Robert Price who, as you know, is the owner of a chain of over 200 toy shops in the UK. The next talk What’s Next for Toys? will take place immediately after this, at 3.30. This will be given by Sarah Smith, who is, of course, our Sales Manager. Sarah’s talk will finish at 5 p.m. After that, tea and juice will be served in the Green Room, which is on the first floor. Please join us there as will be a chance for everyone to chat and …',
     "items": [
         ("Kenji Nakamura's talk begins at %s a.m.", '10'),
         ('His talk includes a short %s.', 'film'),
         ('Lunch will be served in %s Hall.', 'Victoria'),
         ('The lunch hall is next to the %s.', 'library'),
         ('Robert Price owns over 200 toy %s.', 'shops'),
         ('Tea and juice will be in the %s Room.', 'Green'),
     ]},
]


def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase)."""
    out = []
    for e, t in enumerate(TALKS):
        step = 1 + e // 4          # 1..5
        for gi, (line, ans) in enumerate(t["items"], 1):
            lines = []
            for j, (l2, _a2) in enumerate(t["items"], 1):
                mark = "▶ " if j == gi else "   "
                lines.append(f"{mark}({j}) " + (l2 % GAP))
            block = t["title"] + "\n\n" + "\n".join(lines)
            expl = (f"{gi}-bo'shliq javobi: {ans}. "
                    f"(audioskript Part 2, {t['no']}-mashq.)")
            out.append((
                KIND, step,
                {"say": t["say"],
                 "rate": RATE,
                 "prompt": block,
                 "gap_no": gi,
                 "title": t["title"],
                 "instruction": INSTR,
                 "step": step,
                 "order": t["no"] * 10 + gi,
                 "hint": "Bitta so'z yoki raqam yozing",
                 # Ma'ruza uzun — ikkinchi marta eshitishni o'quvchi
                 # o'zi boshlaydi.
                 "plays": 1,
                 "gap_ms": 1500},
                ans, expl, None, None))
    return out


def seed_note(db):
    """Idempotent: bor bo'lsa qayta yozmaydi (hech narsa o'chmaydi)."""
    import json as _json
    import models
    have = {
        (_json.loads(r.payload).get("step"),
         _json.loads(r.payload).get("order"))
        for r in db.query(models.PracticeItem)
        .filter(models.PracticeItem.skill == SKILL,
                models.PracticeItem.kind == KIND).all()}
    n = 0
    for kind, step, payload, answer, explain, alt, para in build_rows():
        if (payload["step"], payload["order"]) in have:
            continue
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=step,
            payload=_json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt, explain=explain, is_active=1))
        n += 1
    if n:
        db.commit()
    return n
