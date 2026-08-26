# -*- coding: utf-8 -*-
"""CEFR LISTENING 3-QISM — MATCHING SPEAKERS (2026-08-26).

Jahongir: "endi qolgan partlarga ham 100tadan tuzib qoy."

FORMAT (kitobdan): "You hear five people talking about X. For
questions 1-5, choose from the list (A-G) what each speaker says."
Yettita variant beriladi, beshtasi ishlatiladi — IKKITASI
ORTIQCHA. Bir variant ikki marta ishlatilmaydi.

MATN MANBASI. Har bir so'zlovchining nutqi Multilevel Master
audioskriptining Part 3 qismidan AYNAN olingan (20 ta mashq,
100 ta so'zlovchi). Mavzu sarlavhasi, yettita variant va
to'g'ri moslik shu yerda tuzildi — kitobning javob kaliti
skanerda bo'lgani uchun ishonchli o'qib bo'lmadi, taxmin
qilish esa noto'g'ri kontent yaratardi.

VARIANT TARTIBI ARALASHTIRILADI. Manbada 1-so'zlovchi A ga,
2-si B ga ... mos keladi. Shundayligicha qoldirilsa, bola
tinglamasdan A B C D E deb 100% olardi. Shuning uchun har
mashqda variantlar 7 modul bo'yicha ko'paytma almashtirish
bilan aralashtiriladi (7 tub son, shuning uchun har qanday
m=2..6 to'liq almashtirish beradi).
"""

SKILL = "ielts_listening"
KIND = "cefr_speaker"
LET = ["A", "B", "C", "D", "E", "F", "G"]
RATE = 0.92


SPEAKER_TIPS = [
    ('Bu mashq nima',
     "Besh kishi bitta mavzuda gapiradi. Yettita fikr beriladi — har so'zlovchiga bittasini moslashtirasiz. IKKI VARIANT ORTIQCHA qoladi va bir variant ikki marta ishlatilmaydi.",
     ''),
    ("Avval VARIANTLARNI o'qing",
     "Audio boshlanmasdan oldin yettita fikrni o'qib chiqing va har birining KALIT SO'ZINI belgilang. Tinglash paytida o'qishga vaqt bo'lmaydi.",
     ''),
    ("So'zlovchining ASOSIY fikrini toping",
     "Har nutqda ko'p tafsilot bo'ladi, lekin faqat BITTASI variantga mos keladi. Qolganlari — chalg'ituvchi. Nutqning umumiy xulosasini tuting, alohida so'zlarni emas.",
     ''),
    ("Bir xil so'z — noto'g'ri yo'l",
     "Variantdagi so'z nutqda aynan eshitilsa, bu ko'pincha QOPQON. To'g'ri variant deyarli har doim parafraz bo'ladi.",
     'Nutq: «I hardly knew anyone» -> Variant: «I wanted to meet people in a new area»'),
    ("Ikki so'zlovchi bir variantga da'vo qilsa",
     "Ikkalasini ham qayta tinglang: biri o'sha fikrni ASOSIY qilib aytadi, ikkinchisi shunchaki o'tib ketadi. Asosiy qilib aytgani to'g'ri javob.",
     ''),
    ("Ortiqcha variantlar bekorga qo'yilmaydi",
     "Ikki ortiqcha variant odatda nutqlarda AYTILGAN, lekin biroz boshqacha ma'noda. Ular sizni sinash uchun turibdi.",
     ''),
    ('Bitta xato — ikkita xato',
     "Noto'g'ri variant tanlansa, u boshqa so'zlovchiga ham yetmaydi. Shuning uchun ishonchsiz bo'lsangiz — o'sha so'zlovchini oxiriga qoldiring.",
     ''),
]


SETS = [
    # ---- audioskript Part 3, EXERCISE 1 ----
    {"no": 1,
     "topic": 'You hear five people talking about a bad habit they have.',
     "options": [
         'I buy things that I have no real use for.',
         'I find it impossible to stop late at night.',
         'I am starting to worry about the harm I may be doing to myself.',
         'I keep watching the same kind of programme.',
         'I can never manage to set off in good time.',
         'I eat far more than I know I should.',
         'I spend too much money on going out.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'It starts as soon as I get home in the early evening. I have a quick snack and then log onto one of my favourite sites. Soon I’ve filled up my basket with all kinds of things – whether I actually need any of them is irrelevant – and then head for the check-out. It’s all so quick and easy. Sometimes I’m watching TV and there’s an ad for a tasty-looking ready meal and I’ll log back on for a minute and order that, too, though when it’s actually delivered it usually turns out to be just junk food and it ends up in the bin.',
         'I first realised something wasn’t quite right when I kept falling asleep at all hours of the day. Getting up around seven isn’t easy when you’ve been up till two the night before, but somehow I never manage to log off until then. There are just so many great sites, particularly news and sports and also shopping, though I rarely end up buying anything. According to a quiz I did, I do seem to have an addiction, though compared to things like overeating I don’t think it’s a particularly harmful one. I mean, I’m quite ft and – unlike some of my colleagues – I always get to the office on time.',
         'I always feel I have to be doing something. I just don’t feel right if I’m not working on my fitness level, and the possible long-term effects of that are beginning to concern me. It also affects my life right now in various ways. For instance, I always go to bed late and get up early. I also need bigger meals than less active people, and although I always choose food that’s good for me, it can be rather expensive and hard to find in the shops. At least, though, the fact that I go everywhere round town on foot means that I’m never held up by traffic!',
         'It was on all the time in my parents’ home and it’s like that here in my own ﬂat. Usually the same channel, too, because to tell the truth I’m totally hooked on the same kinds of series. It’s odd in a way, because most people of my generation spend all their time on the Internet, or, in the case of the fitter ones, doing sport every evening and weekend. I know my own lifestyle isn’t particularly healthy, though at least nowadays I’m up reasonably early, unlike back in my student days when I often had trouble getting out of bed before noon.',
         'It’s always my intention to set off in plenty of time, but somehow there always seems to be something that holds me up. It may be a job that needs finishing off, an email that has to be answered – or even a TV programme that hasn’t quite ended. Then I end up literally running to wherever I’m going, always the last to turn up and also often the most stressed one, too. I’ve tried getting up earlier in the morning so that I have more hours in the day to get everything done, but the lack of sleep just makes me feel tired later on and doesn’t help at all.',
     ]},
    # ---- audioskript Part 3, EXERCISE 2 ----
    {"no": 2,
     "topic": 'You hear five people talking about why they took up a new activity.',
     "options": [
         'I wanted to meet people in a new area.',
         'I needed to solve a money problem.',
         'I wanted to overcome a fear.',
         'I was looking for a complete change from my work.',
         'I began it by chance and found it worthwhile.',
         'I wanted to win a competition.',
         'I was following a family tradition.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'I’ve always been a keen swimmer and that keeps me in good shape, so when I made my mind up to do badminton it was far more about socialising than exercising, especially as I’d only recently moved to this part of town and I hardly knew anyone. I hadn’t realised, though, just how competitive badminton can be – so much so that I’ve now been invited to take part in a local championship. I’ve got no chance of winning it, or even coming close, and to be honest I’m not really bothered about that, but it might be fun so I think I’ll give it a try.',
         'I work part-time in a petrol station, which in some ways is quite a pleasant job but last year I found that I was increasingly getting into financial difficulties. So I began to study the way electronic devices work and how to repair them. I found that fascinating, and eventually I felt confident enough to place an online ad offering my services. I got loads of replies and I’ve now paid off nearly all my debts. I’ve thought of giving up my job at the petrol station, but I think I’d miss meeting different people every day if I worked entirely from home.',
         'For years I’d been so scared of heights that some people used to make fun of me, so one day I decided to do something about it: go rock climbing. Feeling that if I could do that I’d be able to do anything, I joined a local club. On my first day I was surprised to find there were two other people who’d joined for the same reason, and we soon became friends. Together we got fitter and stronger, and encouraged each other to keep going, until by the end of the year we felt unconcerned about tackling the most challenging of climbs.',
         'I never imagined that going horse riding could be such good exercise until I’d spent a weekend trekking in the mountains with friends. That was something of a bonus, really, because what’d initially attracted me to it was that it offered a contrast in every respect to my day job as a cab driver in a noisy, polluted city centre. And although it’s certainly not the cheapest of activities, I find it so relaxing that I always feel it’s worth every penny.',
         'Gardening had always seemed to me as just a way of passing the time, of doing something completely different from office work, or perhaps even – for the really keen – of winning a prize for the largest home- grown vegetable. So it was only by chance that I became interested in it, when the old lady next door asked me to look after her garden while she was away. On her return she was so deligh ted by my efforts that I felt I’d done something really worthwhile, so I then offered to garden for other neighbours in their s and s. They sometimes offered me money, but I always refused to accept it.',
     ]},
    # ---- audioskript Part 3, EXERCISE 3 ----
    {"no": 3,
     "topic": 'You hear five people talking about a difficult situation they faced.',
     "options": [
         'I helped people who were in danger.',
         'I refused to ask anyone for help.',
         'I calmly insisted on being treated fairly.',
         'A local person showed us the right way.',
         'My professional training helped me.',
         'I called the emergency services.',
         'I decided to give up and go home.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'There was a storm blowing as I walked along the cliffs, and down below I noticed a rowing boat being thrown about by the huge waves. I took out my phone to call the rescue services, or the police, but there was no signal. If the boat had hit the rocks it would have been smashed to pi eces, so I ran along the cliff top until I came to a small bay. I ran back and shouted to the crew to row towards it as hard as they could, and eventually they managed it. There the waves pushed their boat into the bay, where they were able to take shelter.',
         'It was my first night out in that city, and when I saw the last bus home disappearing round the corner I knew I had a problem. It was cold and I couldn’t afford a taxi, but I didn’t want to bother my host family by asking them to pick me up so I set off on foot, telling myself it’d only take me an hour or so. Four hours later I was still walking. I was soaked through and my hands were frozen. When I eventually reached the house the family said how worried they’d been, and asked why I hadn’t phoned. By then I wished I had.',
         'I realised straight away I’d been overcharged, but it was only by a small amount and my first thought was to forget about it as I was in a hurry. Then I noticed the assistant glance at me and somehow I knew it had been deliberate. I gently pointed out the error, but he became quite aggressive. Not wanting to get into a row about it, I asked to speak to the manager, and when she came over I explained that I hadn’t been given the correct change. The assistant angrily denied this, but the manager pointed to a security camera right above us. He immediately gave me my money.',
         'Carlos, Alfonso and I had been camping in the mountains, and it was time to leave. Just then a dense mist descended and soon we realised we were completely lost. I was in favour of keeping going along the path, while Carlos suggested heading downhill. Alfonso, though, wanted to phone Mountain Rescue for help. The two of them had just started arguing when a shepherd appeared. I asked him which way we should go and he said we’d taken a wrong turning at the bridge, so we headed back the way we’d come, turned left by the river instead of right, and within twenty minutes we’d reached the village.',
         'I was doing a cross-country run when suddenly I tripped and fell, feeling a sharp pain in my ankle. As I lay there I wondered whether I’d be able to stand on it, maybe even carry on running, but I remembered what I’d been taught as a nurse so I kept it still, checking to see if it was broken. It didn’ t seem to be so I decided against calling an ambulance, but I didn’t want to take any chances so I phoned my sister. She immediately offered to come and collect me, and within fifteen minutes she was able to help me to the car and take me home.',
     ]},
    # ---- audioskript Part 3, EXERCISE 4 ----
    {"no": 4,
     "topic": 'You hear five people talking about a famous city they visited.',
     "options": [
         'It was exactly as I had imagined it.',
         'I went at the wrong time.',
         'It was even better than I had expected.',
         'I found it difficult to find my way around.',
         'I could not understand why people praise it.',
         'It was more expensive than I expected.',
         'The people there were unfriendly.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'The place is always on TV and in films and in magazines, and so you get a mental picture of what it’s like even if you haven’t been there. You have this image of skyscrapers everywhere, streets full of traffic and people, everyone rushing around, talking fast and leading busy lives. You think of it as having a real buzz. And guess what? It was just like that. Everything I’d expected to find was there. In fact, it all seemed so familiar that it was as if I’d actually been there before.',
         'I discovered after I’d been there that you need to be really careful about when you choose to visit the place. There are very busy times and quieter times. Without realizing it, I chose one of the busy times, and wow, was it busy! The place was packed, and of course with the narrow streets it is famed for, that makes movement difficult. I just shuffled along with everyone else, going at their pace, so I didn’t manage to see much. There’s a great atmosphere there, and of course it looks wonderful, but I could have done with a bit more room to move. So I guess I didn’t see it at its best.',
         'Everyone I’ve met who’s been there says what a fantastic place it is, and I was expecting something really special. And I wasn’t disappointed, though I must say the picture I’d had of it in my mind didn’t turn out to be totally accurate. In fact, it not only lived up to my expectations, it exceeded them. People always associate it with its famous buildings, but it was the less well-known places that struck me. In every little street, especially away from the tourist areas, there was something fascinating to see. It’s those little streets that were really memorable for me.',
         'I’d been looking forward to going there for a long time and I finally managed it. I wasn’t quite sure what to expect because people had told me that it wasn’t the same as it used to be. Apparently, it’s become much more touristy recently, but I didn’t see any evidence of that. What did strike me was how confusing it is. Half the time I didn’t know where I was and getting from A to B was always problematic. I normally have a good sense of direction, but I was always getting lost there. Once I did get to where I was trying to go, it was worth it, though.',
         'People always talk about what a marvellous place it is, and so eventually I decided to go and see for myself. It has the reputation of being a place you never forget, and lots of people say it’s their favourite city. But, having been there, I can’t see what all the fuss is about. Sure, the places that you see pictures of all the time, or that you see in films, are impressive enough, but I’ve seen better. It’s a pleasant enough place, and it’s certainly popular with tourists – there were plenty of them there – but I don’t think it really deserves all the praise people give it.',
     ]},
    # ---- audioskript Part 3, EXERCISE 5 ----
    {"no": 5,
     "topic": 'You hear five successful people talking about the reason for their success.',
     "options": [
         'I succeeded simply by being lucky.',
         'A good idea mattered more than business skill.',
         'Natural talent is what counts.',
         'I ignored what other people told me to do.',
         'Hard work mattered more than ability.',
         'My family supported me all the way.',
         'I had excellent training.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'I just fell into my television career really, there was no grand scheme. I guess it was all a case of simply being in the right place at the right time. I got my first job by pure chance and then one job offer followed another. I didn’t set out to get where I am today and I’m sure there are plenty of people who could do the job as well as, if not better than, me. People tell me they like what I do, and that’s great, but I’d probably be just as happy if the whole thing hadn’t happened.',
         'When I started the company, the market was wide open really and hardly anyone was doing what I was doing. Actually, the product I was offering in the early days wasn’t all that good, but there wasn’t much to compare it with, so it did OK. The fact is, it was a good idea and in business there’s no substitute for a good idea. I’m not necessarily a brilliant businessman in terms of strategy and things like that and sometimes I’m not sure what to do next. But I did have that great idea, so I’ve made my own luck.',
         'My personal feeling is that in show business, talent will always get its reward. Even if you have to struggle on for years – which, thankfully I didn’t have to do – if you’ve got what it takes, you’ll make it. Someone will spot you and give you a part if you’re good enough, and that’s exactly what happened to me. I’ve never really had to work at it, it just seems to be something I was born with. I’ve never thought of doing anything else, and fortunately I’ve never had to.',
         'There was no shortage of advice when I started my career as a singer. People told me how I should look, what sort of songs I should sing, all sorts of things. But I ignored them all, and I’m glad I did bec ause I’ve been proved right. I had it all worked out from the very beginning, every detail of what I was going to do and how I was going to do it and it’s all gone very smoothly. I knew what suited me and what would be popular and I’ve followed my instincts on that. I haven’t had to struggle at all, everything’s gone very well.',
         'To get to the top in my sport I’ve had to make the most of what I’ve got. I may not be the most talented player there’s ever been but I’ve put a tremendous amount of effort in to be as good as I can be. All along there have been people making comments about how I’m not good enough, but that’s just made me try even harder. And I’ve exceeded my ambitions really – I only wanted to be a good club player and I never imagined I’d make it into the national side.',
     ]},
    # ---- audioskript Part 3, EXERCISE 6 ----
    {"no": 6,
     "topic": 'You hear five people talking about an autobiography they have read.',
     "options": [
         'The writer says too much about matters he knows little about.',
         'The person is quite different from his public image.',
         'The person admits behaving badly to those who helped him.',
         'The person is the same in private as in public.',
         'The story of rising from poverty to wealth is inspiring.',
         'The book contains far too many personal details.',
         'The book is very badly written.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'What struck me most was just how arrogant the man is! I mean, he’s a fine actor and I really like everything he’s been in – that’s why I bought the book. But that doesn’t mean that his opinions on politics and the world really matter. He seems to think they do, and that because he’s been in a few successful films, people should listen to his views on everything and take them seriously. Actually, he talks a lot of rubbish about all that and that really irritated me. I wanted to read about his early life and struggles, how he got to the top and all that, but he hardly mentions that, or anything about his private life. It’s really put me off him.',
         'I got the book because a friend recommended it, not because I was particularly interested in the man. In fact, from his public image on TV. I thought he was a ghastly person. Self -important, fiercely ambitious and not at all likeable is how he appears to me. So I was very surprised to find that he isn’t actu ally like that at all, that’s just for public consumption. In reality, he’s a decent person who puts family and friendship first and he comes across as the sort of person you could have a pleasant chat with. He’s certainly gone up in my estimation.',
         'His family seem to have played a very important part in his career, and he talks about how much help they gave him in the early days, paying for coaches and taking him to tournaments all over the place. But he admits that after he made it to the top, he didn’t treat them at all well. He talks about how much pressure he was under once he became a champion and how he struggled to deal with all the attention from the media and fans. We always saw him smiling in victory, but he says that he was really horrible to the people who were closest to him. It just shows that appearances can be deceptive.',
         'Of course, people always say that comedians are actually very sad people but that doesn’t seem to be the case here. With him it seems to be very much ‘what you see is what you get’. The book’s full of really funny stories, and he makes fun of everything, from some of the things that happened during his childhood to the big issues in the world today. He seems to have come from a very peculiar family and his descriptions of them are really amusing. You get the impression that there is no difference between his personality on stage and on screen and what he’s like when he’s not performing.',
         'It’s quite an uplifting story, really, a real ‘rags to riches’ one. Of course I knew all about his enormous success as a businessman, but I didn’t know anything about his background. It certainly wasn’t a privileged one, and he seems to have grown up in poverty with a family who didn’t really care about him at all. Th e way he describes his childhood, it’s hard to imagine how it could have been any worse. So the fact that he managed to go from that to such incredible success and wealth makes for a really interesting story. You don’t get much of an idea of the real person, but the story is great.',
     ]},
    # ---- audioskript Part 3, EXERCISE 7 ----
    {"no": 7,
     "topic": 'You hear five people talking about winning an award.',
     "options": [
         'I thought about everyone who had helped me.',
         'It made me rather too pleased with myself.',
         'I mainly felt relief that the pressure was over.',
         'I began to worry about what would come next.',
         'I was too exhausted to enjoy it.',
         'I felt I did not really deserve it.',
         'I was disappointed by the reaction of others.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'When I won the Best Actor award it was an extraordinary moment. There had been so many occasions when I’d thought I might win an award, only to find that someone else got it instead. So when I finally got it I was thrilled. It was a fantastic personal achievement but in fact the main thing in my mind was all the people who had helped me along the way. I thought about all of them and all the help they’d given me. I knew that without them I would never have won it. And I mentioned as many of them as I could in the time available.',
         'I guess that being voted Footballer of the Year went to my head. All I could think about was how well I’d done. Me, the best! I thought back to the early years of my career, which weren’t so great and I felt fantastic. And it was all thanks to my own efforts, not because anyone had handed me anything on a plate. It had been a long, hard journey but I’d finally made it to the very top. I suppose it made me a bit big-headed for a while, but I just felt so good about myself and what I’d managed to achieve.',
         'Everybody was expecting me to win the Writer of the Year award – I don’t know why, there were plenty of other good contenders on the shortlist. Because everyone was predicting I’d win, I felt under pressure, as if it would be some kind of failure if I didn’t win. It was a silly way to feel, I know, but I couldn’t help it. So when my name was announced I was just glad that it was over and I had in fact won it. All the pressure came off me in a moment and I just felt like sitting down quietly rather than celebrating.',
         'These awards mean a lot in the music business and so winning the Best Singer award was a great honour. I’d worked so hard over the years and I’d spent so long getting nowhere that it was amazing to have achieved this recognition. I thought I’d be absolutely overcome with joy, but in fact the reverse happened. As I accented the award, I was wondering if it would be all downhill from there. Would I be able to keep it up and stay at the top? Or would this be the high point, followed by a lot of low points? I couldn’t put those thoughts out of my mind.',
         'I wasn’t totally surprised when I got the Best Student award, because to be honest I felt that I deserved it. In fact, I’d put in so much effort to win it, doing far more work than anyone else, that I was completely worn out. It had been so important to me to win it that I’d dedicated myself completely to the task of winning it. So when I went up to collect it, I’d used up all my energy over the previous couple of weeks and was totally drained. I could barely put a few sentences together for my acceptance speech, though I managed to remember to thank a few people for their help.',
     ]},
    # ---- audioskript Part 3, EXERCISE 8 ----
    {"no": 8,
     "topic": 'You hear five people talking about a holiday they took.',
     "options": [
         'It was easy to travel out of the city.',
         'The room was disappointing but the view was good.',
         'Transport across the water was reliable.',
         'We stayed in several different places.',
         'Local people were very willing to help us.',
         'The food was better than we expected.',
         'The weather spoiled our plans.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'We spent a day exploring the shops and markets in the city, and bought some souvenirs. Then we wanted to see some of the area outside the city, and discovered it was easy to get to loads of places by train, including the mountains, where we were told there were great hostels. You can do bushwalks out there and apparently the scenery is stunning. But it can be dangerous – we were warned to have the right gear and tell other people where we were going. So we decided to give it a miss. Anyway, we weren’t short of things to do in the city! We were spoilt for choice.',
         'We were pretty tired when we first arrived so we were glad just to relax. We’d booked late and I have to say that the room wasn’t the best I’ve stayed in. But we had a view of the lake, which was a real treat – we were really impressed by the forests and mountains around the city. We made good use of the swimming pool, though we were too lazy to go to the famous markets. We didn’t take advantage of all the shows either. Lots of people told us how good they were so that was a pity. And the theatres themselves were supposed to be impressive.',
         'One of my main ambitions was to see inside the big concert hall – and in fact we managed to get in to a concert there, which was pretty special. The acoustics were amazing! The city was divided by a river, and getting round had its problems, especially as we didn’t really understand the city plan. The best way was the ferries – I was really impressed that they were always on time and provided good views in the city. The trams were good too, and the local commuters seemed happy to chat to us and give us ideas for the best things to do and see. We didn’t have time to do everything, though.',
         'Before we went we couldn’t decide where to stay – so many people recommended different places, and there seemed to be loads of different and unusual possibilities, like old traditional farms converted into guest houses – so we decided to move around and try something different every couple of nights. That worked out really well, and they were all excellent. Although we’d been told that getting round on the buses was easy and cheap in the city, we decided to rent a car so that we could get out into the countryside – we didn’t want to miss out on the views driving along by the ocean.',
         'Even though we had a city plan we got lost several times – especially in the old town where the buildings were quite similar – though I know some people say getting lost is the best way to get to know a city! We were never short of help, though – some people were even prepared to walk with us to show us the way. That was something I’ll always remember! Our hotel was all right without being spectacular, and it was a long walk in to the evening shows – we took a taxi most times. There was loads to do every day, though, and we certainly weren’t bored.',
     ]},
    # ---- audioskript Part 3, EXERCISE 9 ----
    {"no": 9,
     "topic": 'You hear five people talking about what happiness means to them.',
     "options": [
         'I am happiest doing a quiet activity on my own.',
         'Leisure is only enjoyable after hard work.',
         'People of every age can be happy.',
         'My family gives me my happiest moments.',
         'People who have had to struggle are happier.',
         'Money is the most important thing of all.',
         'Happiness depends mainly on good health.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'What is happiness? From an early age happiness for me is sitting in a boat in the middle of a lake on a summer’s day and doing some serious fishing … all alone just me and my thoughts. No stress, get away from it all for an hour or so, but maybe not completely aimless – not just lying on a beach somewhere, but having some task to do. Then, when it’s all over, it’s back to normal life and problems and hassle, and having to fight to get what you want. But that brief moment of happiness helps me to reflect and make sense of my life.',
         'I think to be happy, you do obviously need some financial security – not rich … I didn’t say that, ‘cos there’s an important difference. Also I’d say you need humour in your life … that’s kind of obvious too. Having lots of free time to do what you want? Not sure, there. I’d say quite the reverse, actually. For me, you really appreciate your moments of leisure when you’ve done lots of hard work. If it’s all play and no work in your life, then you don’t enjoy it. So for me, it’s all to do with … setting yourself a list of things to get through and then you’ve completed them. Now you can be happy.',
         'I sometimes wonder if being happy is something to do with age. Very young children are happy most of the time; very old people are happy when they think of fond memories, and also they’re happy when they see their grandchildren happy. So happiness is not just specific to one age group. That’s certainly the case with my family. But in my experience happy people get through life more easily – if you take things seriously all the time, that’s when you get stressed or have health issues, maybe. And sometimes life can be a real pain, let’s be honest.',
         'Happiness comes in many shapes and forms. Personally I’m happy when I’m active, doing my sports and feeling all healthy. But maybe that’s a rather self-centred view. I also get moments when I’m just, say, sitting on a train, and suddenly I think of my children’s smiling faces, and realise how lucky I am, how happy they make me – and my husband too, of course. My life could’ve turned out much worse, as it has for many people. Will I still be happy when they’ve all grown up and gone away? I’m sure when that time comes, I’ll find a new form of happiness.',
         'It’s sometimes said that you make your own happiness, and I’ve got some sympathy for that view. But in my experience, it’s something more than that. It might sound strange, but I honestly think it’s all about your life not being too easy. If everything in your life is handed to you on a plate by rich parents then I actually don’t think you’re as happy as someone who’s had to struggle a bit in their life. When you can share your struggles with others and laugh about how you got through them, that’s when you’re truly happy. That’s certainly how it’s worked out for me.',
     ]},
    # ---- audioskript Part 3, EXERCISE 10 ----
    {"no": 10,
     "topic": 'You hear five people talking about how they became interested in classical music.',
     "options": [
         'You have to begin training when you are young.',
         "A pop musician's opinion made me listen.",
         'A relative introduced me to great composers.',
         'I first noticed it in films and advertisements.',
         'At first I only wanted music that was exciting.',
         'I learned about it entirely on my own.',
         'My school choir got me interested.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'Classical music’s often seen as old-fashioned and though there’s people everywhere who go to concerts, and some classical musicians are big-name stars, it doesn’t really excite young people that much; they prefer pop music or more modern stuff. But the truth is, it’s hard to interpret complex music, even with the best teacher in the world, unless you start training early on in life. Luckily for me, I came to this conclusion myself when I was in my early teens, and when I said I wanted to become a classical guitarist, my parents rather reluctantly went along with the idea and bought me some lessons. Since then, I’ve played almost every day.',
         'I bought my first classical recording aged fourteen. It was a violin concerto by a Russian composer. Although my school had a strong arts focus, I’d no particular interest in classical music till one day when I heard a big rock star going on about ‘the most exciting piece of music ever written’. Being a fan of his music, I felt I had to hear it. By the third listening, I was convinced he was right. What’s more, I found I really had an urge to play the violin myself – and found myself a teacher. Despite my dad’s complaints about the noise I produced, I practised every day at home. I’ve never looked back.',
         'At my school, I was made to learn the recorder, and I had to practise every day. The sound I produced was so dreadful that whatever piece of music I was supposed to be playing was hard to recognise, despite all the efforts made by our music teacher, who’d actually been quite a famous musician himself when younger. It took a while, but I recovered from that, and got to know the work of some of the top composers thanks to my uncle. That got me excited enough to beg to have piano lessons when I was about twelve. After that, everything just took off. Now here I am getting quite well-known as a concert pianist.',
         'At school, our music teacher tried to get us into classical music without much success – he just seemed to go for the most unexciting pieces. It was me who noticed classical music turning up in movies, cartoons and stuff. Like, I remember one day hearing a really famous classical piece being played on a commercial trying to attract young kids to some fast food place. You’d think things like that’d be enough to put anyone off classical music, but they had the opposite effect on me – encouraging me to want to learn to play and seek out a good teacher, which is what I did, much to my mum’s amazement, I remember.',
         'Although my dad had taught me to play the flute at an early age, I didn’t get interested in learning to play classical music then. I wasn’t willing to try and understand it and didn’t realise you have to do that in order to enjoy it. As a kid, I wanted something that made me jump and got me going – made me feel happy or enthusiastic, so I resisted the efforts of my teacher to introduce me to classical music. She got there in the end though, by sheer persistence, convincing me that there’s great excitement to be found in the joy of playing something difficult, and doing it well.',
     ]},
    # ---- audioskript Part 3, EXERCISE 11 ----
    {"no": 11,
     "topic": 'You hear five people talking about a radio station they listen to.',
     "options": [
         'There are programmes to suit every age.',
         'You can listen to it over the internet.',
         'It broadcasts no advertisements at all.',
         'The presenter is funny even when you disagree with him.',
         'The station supports good causes.',
         'The news coverage is excellent.',
         'The choice of music is very wide.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'The station I listen to has the right balance of talk, sport and news and a great mixture of presenters but there are far too many advertisements. In the mornings I usually listen to a short news programme and then a show about sports going on both locally and nationally which is presented by a well-known ex sports star. The thing I like about the station is that it has stuff for all age groups. There are a lot of good comedy shows and quizzes, but also stories about people and places in the area and it makes itself accessible to even the youngest members of the community.',
         'It’s a locally operated radio station and it broadcasts some of the top nationally rated talk radio programmes. There are live shows hours a day and you can listen online if you prefer. I’ve enjoyed listening to it for many years now. I especially like one very amusing comedy programme which is on every weekday night and the Science Fantastic programme on Saturday evenings. I prefer this station to some of the national ones and I like the local news stories, although sometimes I’d rather it took more notice of news and other subjects from overseas, rather than just the local area or the country as a whole.',
         'I tend to listen to the radio a lot and I love the arts show – that’s the selling point for this station for me − the presenter is very serious about the arts and his in-depth approach helps me keep up-to-date with all the latest theatre, books and movies. Oh, and they don’t broadcast advertisements so you never get interruptions when you’re enjoying a show. I’ve given up flipping through channels to avoid them now. Another thing is they don’t have news every hour like so many stations. There are some really good quality radio dramas – it’s an excellent way for young writers to get their work broadcast.',
         'Talk radio has grown in popularity in my area and there’s a huge demand for more and more talk-show stars. My favourite station has a show called Viewpoint. It’s presented by a very entertaining guy and sure, there’ll be those out there who may not agree with his opinions, but that doesn’t matter because he makes fun of everything. So, even if you don’t agree with him, you can sit back and enjoy the humour in his approach to local or national news events. I find I’m still one of the few younger listeners to this station though − most of my school friends don’t really go for it.',
         'I even got a chance to go on this radio station myself. It was kind of embarrassing but quite fun because not everyone gets to go on a radio show and meet the presenters. All the shows are really interesting. They also play a lot of fun games − and talk about popular issues. The station’s known for sponsoring charity organisations in this region, so it’s offering more than just entertainment. There’s one programme where they’re training young newsreaders so they picked out about thirty kids from nearby towns and are training them to be newsreaders and they get to do one short show each.',
     ]},
    # ---- audioskript Part 3, EXERCISE 12 ----
    {"no": 12,
     "topic": 'You hear five people talking about what makes a good teacher.',
     "options": [
         'A good teacher pushes students to make more effort.',
         'A good teacher is available outside the classroom.',
         'A good teacher makes the subject itself interesting.',
         'A good teacher sets an example by working hard.',
         'A good teacher tells students exactly how they are doing.',
         'A good teacher keeps strict discipline.',
         'A good teacher treats every student the same.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'I fully accept that everyone’s different, so of course different teachers will suit different types of children and teenagers. Throughout my education, though, the teachers I responded to best were the ones that tried to push me along a bit by getting me to try a little bit harder. Because the problem for me is that I’m naturally quite a lazy person, and I’ve always been more interested in life outside the classroom than inside it. So I’m the kind of person that’s perhaps a bit of a headache for teachers, the sort they’re not really thinking about when they’re studying for their teaching qualifications.',
         'Most of the time a teacher’s just doing his or her job, I guess. I mean, they’ve done their qualification, they’re in the classroom, they’ve got to write your report at the end of term saying how you’ve done, haven’t they? Sometimes, you might want to be able to ask your teacher something before or after class, get some advice or extra information, or tell them about some problem. It’s the teachers who’re there for you in those situations that are special, who take an individual approach. And I don’t think it’s too hard for them to do that, give you a couple of minutes.',
         'Well, I’m a firm believer in the importance of the subject. If a teacher can get the kids absorbed by the subject, be it maths or geography or cookery or whatever, then the job is basically done. The best teachers are the ones who make it look easy, because they make it seem fun. Then the kids are fascinated, even amused, by the subject, so they want to learn, and each and every one of them makes progress. I think this often involves the teacher getting everyone to see the relevance of the subject in the wide world, beyond the confines of the classroom.',
         'Fashions come and go in teaching, just as in everything else. We’re at a stage at the moment where there’s a lot of focus on the individual, and getting every child to take responsibility for their own learning, that kind of thing. But you can’t just tell kids to be better, to study harder, you also have to demonstrate what you mean by this. So the teacher needs to put in the hours, to mark the homework, to prepare lessons carefully. If kids know the teacher’s doing it, then they’ll want to do their part too. I think that’s the way to do it, never mind what’s in fashion.',
         'Perhaps the best thing is for teachers to reflect on how they themselves got to be teachers. How did they achieve success in their qualifications? How did they manage to do well at school? It’s down to a question of each and every student making his or her own way – and they only know if they’re doing well if they’re told by their teacher that they’re doing well… or badly. You need to be told the facts about how well you’re managing with your studies, in class and in your homework. The truth is that learning’s not a game, not just fun, but hard effort.',
     ]},
    # ---- audioskript Part 3, EXERCISE 13 ----
    {"no": 13,
     "topic": 'You hear five people talking about being in a hospital.',
     "options": [
         'I needed an official document for work.',
         'I was surprised to be awake during the procedure.',
         'I was shocked by how a patient looked.',
         'I found a serious safety problem in the building.',
         'I could not find the room I was looking for.',
         'I had to wait a very long time.',
         'The staff were rude to me.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'Well, the last time I went to the hospital was because I needed a medical certificate. I’d just been offered the job in Kuwait and they needed an official piece of paper from any qualified doctor saying that I had healthy lungs, heart, liver and good eyesight. And well, I couldn’t go to my regular doctor because I had already given his name as a reference. And well, I was a bit nervous because if the doctor didn’t declare that I was perfectly healthy, I wouldn’t get the job.',
         'I’d always thought they’d give me something to put me to sleep and when I came round everything would be over and all I would see would be a few stitches. But these days it’s all done with a local anaesthetic so you stay awake through the whole thing and you can see everything they’re doing. Of course, they tell you that you don’t have to look but you can’t really look anywhere else, can you? Of course, you don’t feel anything, but it’s a bit scary.',
         'I didn’t know what to expect. I mean, when somebody has such a big operation nothing really prepares you for… what happens afterwards. It’s not a bit like it is on telly. When at last I managed to find the right room I almost didn’t recognise her. It really was a bit of a shock but the staff all seemed really pleased with her progress and were even talking about… er… going home in just a few days. I don’t know about these things and I believed what they said. If I’d known what was going to happen, I’d have stayed there all night just to be with her, right up to the end.',
         'Well, the call on my answerphone said there was this leaking roof in one of the wards. ‘A drip’ they called it. Well, it hadn’t been raining much so I suppose it didn’t seem too bad to them. But when I got up there, the whole roof was in a shocking state. It’s a good thing I looked at it when I did because one heavy rainstorm and all that lot was going to collapse, and with all the patients in their beds underneath. I mean, I know the ‘National Health’ hasn’t got much cash these days but they should have had the whole roof fixed. So, in the end, I told them to get someone else to do it. And I’ll tell you another thing – I’m going private from now on.',
         'The address on the package says room 4J. Anyway, I’ve been to the hospital loads of times to visit my gran. So I know the layout pretty well. Anyway, I find room 4H in no time – it says ‘check-ups’ on the door so it can’t be the room I want but then there’s no room 4I or 4J and room 4K is the maintenance office and they certainly don’t want a box of surgical knives. So, after I’ve been looking for a good ten minutes, I ask someone and they tell me, as though everyone knows, ‘it’s on the next floor, of course’. How was I to know? Anyway, I take it up there and then there’s nobody there to sign the documents to say they’ve received it. So, I have to come all the way back to…',
     ]},
    # ---- audioskript Part 3, EXERCISE 14 ----
    {"no": 14,
     "topic": 'You hear five people talking at or about a wedding.',
     "options": [
         'I am telling someone who was absent what happened.',
         "I think the groom's life is about to change.",
         'I am explaining how I know the groom.',
         'I want copies of the photographs.',
         'I am comparing it with my own wedding.',
         'I was disappointed by the food.',
         'I did not know anyone there.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'Well, it really was a pity you couldn’t be there. Brian and Julia looked so wonderful and everything went off perfectly. The vicar gave a beautiful address and the reception was gorgeous. Everyone commented on the bridesmaids’ dresses. They wore pale yellow just like you wanted, oh, and I almost forgot, Brian mentioned you in his speech. He said Julia’s got everything a wife could offer, but he still likes your cooking best. I think he meant it, too. Of course, Dad was there with… er… but I don’t suppose you want to hear about that.',
         'Brian’s not going to have an easy time of it. After all, Julia’s not going to coddle him like that mother of his does. And it’s a good thing too if you ask me. It’s about time he learnt to be useful around the house. Seventy years of feminism doesn’t seem to have done much for our family either. Still, when we get married a few little things are going to change. There’ll be no more nights out with the lads – not when I’m in charge – and I’ll tell you another thing, if I were Julia, I’d be keeping a good eye on one of those bridesmaids, too.',
         'So you must have known Brian for quite some time now. Has he always been this handsome?… No, don’t tell me, I can imagine. Well, anyway, I met him a couple of years ago when they moved our unit up to head office and he was already working there as entertainment officer. You know, all the big firms have them these days. He organises surprise parties and hires entertainers and kissagrams and then comes round the office collecting money for them afterwards, but I suppose you know all this already.',
         'Did you take all these pictures yourself? You are clever. And look there’s one of me. I don’t remember you taking that one. Oh, and here’s one of everybody outside the church. Your Auntie Julia would probably like a copy of that one and so would your granny; mind you, it’s a pity it’s got your granddad in with that Marjorie. Oh, could you be a darling and get some copies done? We could send them for Christmas. They always send you something nice.',
         'It was really one of the best weddings I’ve ever been to. The service was short; the bride arrived on time; the groom was sober; the food was excellent; the speakers were funny – not like my wedding at all. They really must have put so much thought into it, and so much preparation. Which must show that they’re serious about each other because so many young people aren’t these days. The only sad thing is that they live so far away. I mean if you hadn’t given me the Friday off, I simply wouldn’t have been able to get there on time.',
     ]},
    # ---- audioskript Part 3, EXERCISE 15 ----
    {"no": 15,
     "topic": 'You hear five people talking about a summer job they did.',
     "options": [
         'The work itself was as dull as I had expected.',
         'It was much harder than I had imagined.',
         'I would be willing to do the job again.',
         'I was given very little responsibility.',
         'I had to deal with problems on my own.',
         'The pay was much lower than promised.',
         'I made a lot of new friends.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'I’m glad I took the job – if nothing else, it’s taught me that I never want to do it again! It was just what I had expected, really, although maybe a bit harder. Packing things into boxes and boxes into crates – it’s never going to be fascinating, is it? But actually, it wasn’t the actual tasks themselves that got to me – because you can just go into a sort of dream world, do it on automatic while thinking about other, nicer things – but the way everyone went for breaks and lunch at exactly the same time every day. The others were OK, you know, I mean, not rude or anything, so I shouldn’t moan.',
         'It wasn’t at all easy, you know, but I’d thought it would be a breeze. I guess the thing with being on the reception desk in a hotel – even a budget hotel… or maybe especially a budget hotel – is you never really know what’s going to happen next. You might find yourself dealing with an incredibly rude guest – tell yourself he’s very stressed – or someone who’s locked out of their room, or anything. Some days were so busy you couldn’t catch your breath, and others dragged by. My manager was great, really positive, but some of the other staff were just, well, dull.',
         'When I first finished the job, I thought I’ll never do that again, no way. But now that I’ve recovered a bit, I think I might well try to do it again next summer. With tips, the money turned out to be quite good, and some of the other waiters were quite funny, so it kept me amused. Every day was pretty similar to the last, and the next, and I found that quite reassuring. It was tiring, being on your feet all the time, and having to smile and be nice and show an interest in everyone and laugh at some pretty terrible jokes – all that was what took the energy … but, yeah, I’d do it again.',
         'Well, I was working in this shop. It sold small craft things, you know, models and little pictures and things, mainly to tourists really. I didn’t exactly have a lot of responsibility – if anything interesting happened, like a delivery, or a customer spending a lot of money – then I had to get the manager to come and deal with it. She was rather a cold person, actually, though very polite. But it wasn’t very good weather and there weren’t very many tourists, so most of the time I just sat about, to be honest, or did a bit of gentle tidying of the stuff on sale.',
         'I didn’t understand what was involved when I got the job. I thought working on a campsite meant helping people put up their tents, stuff like that, but I found I had to do cleaning, and also serving in the little shop they had there. There were a couple of other guys working there, but they kept themselves to themselves and the boss was nowhere to be seen, ever. So problems landed on my plate, and I got shouted at or treated badly by families turning up late and finding we didn’t have any spaces, or that their tent had a hole in it or something – but nothing was my fault so why blame me like that?',
     ]},
    # ---- audioskript Part 3, EXERCISE 16 ----
    {"no": 16,
     "topic": 'You hear five people talking about leaders and bosses.',
     "options": [
         'Leadership is learned, not something you are born with.',
         'A good leader lets others make important decisions.',
         'Employees need regular feedback on their work.',
         'The most important skill is bringing people together.',
         'Some bosses do not work as hard as their staff.',
         'Leaders should always have a management degree.',
         'A leader must be the most knowledgeable person present.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'Some people still think that leaders are born, not made. They say, no matter how hard you study and how many diplomas you collect, at the end of the day, if you’ve got natural skills, such as a strong character, that’s all you’ll need. I think that’s nonsense. Leadership is all about commanding respect. If a boss says to me, for example, ‘Look, your computer skills need upgrading’, I’ll think, ‘Right, this person has a degree in computing, I don’t, so he must be right’. But if it’s the other way round, then you feel, well, maybe I should be boss!',
         'Well, the sort of leaders that I actually admire… are not the… top dogs in suits… with a degree in management and a belief that nobody can do things as well as they can. One thing I’ve learned from all my experience in different jobs is that, to be a really good boss, you have to be good at encouraging the people under you to decide on important issues… creating a situation in which other people can shine. Of course this does not mean the boss’s job is any easier; it’s still a challenge, but so much more rewarding for everyone.',
         'Since I left school, I’ve done a number of short-term office jobs, and I must say I’m beginning to realise how important it is to have the right sort of person directing your work. To develop all my potential, I need to be told when I’m doing something well, and also the areas where I could improve… I think the earlier you get formal and informal feedback, the better. Otherwise you develop bad habits… some of my workmates don’t agree with me, when I say it’s good to meet regularly with your boss, they think I’m trying to be better than them.',
         'Of course we all want bosses who are knowledgeable and who bring energy to the job, and I must say, in my opinion, most people who reach top job positions do possess these qualities. However, what really matters is the ability to bring people together. Leaders often mistakenly encourage people to work on their own, kind of, in isolation, because they are afraid of the strengths of groups, they think maybe they’ll criticise, or even join forces against the leader… Such leaders need to go on management courses, to look at good examples of leadership…',
         'Well, in the organisation where I work, each department has a leader, a boss… and because I’ve worked in six of these departments, I’ve had six different bosses! I must say there’s been very little to complain about… except that we are being asked to do an enormous amount of extra work and some of the bosses don’t seem to be doing long hours, like the rest of us. It is true that after work, they may have to attend special management courses, or meet individual members of staff to discuss performance, but this only happens occasionally…',
     ]},
    # ---- audioskript Part 3, EXERCISE 17 ----
    {"no": 17,
     "topic": 'You hear five students talking about studying at home.',
     "options": [
         'I concentrate best in my own room.',
         'Any noise from other people distracts me.',
         'I need to be physically comfortable.',
         'I plan my work but do not follow the plan.',
         'Other members of my family make it hard to study.',
         'I study best early in the morning.',
         'I need music playing in the background.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'I must say, I’ve never found it easy to study at home. I’ve tried all sorts of places. One of my friends prefers to study outside, lying on a rug in the garden. I try that from time to time and it’s nice and airy, though my concentration tends to wander a bit and I find I’m looking at the trees, or people passing by, rather than at my notes. I think better in my bedroom, where it’s nice and quiet. I’ve got a large desk there to put my computer on, and I set my alarm early and work with a fresh mind before everyone else’s up.',
         'You know how sociable I am normally? Well, it’s strange but I find people talking really puts me off when I’m trying to study, so I hardly ever work with a classmate, although it’s much more fun. You’d think that the faculty library would be the best place for me then – an academic atmosphere and no distractions. You always get a few people whispering and coughing though and that annoys me. What I frequently do instead now is put on my personal stereo and have something blasting away, it doesn’t matter what. That blocks out everything else and I get through the work in no time.',
         'When I do my homework I have to feel right. After sitting on a hard chair all day, I need to stretch out with my head on a pillow. Mum says I cannot possibly concentrate like that, but actually I don’t fall asleep as long as I don’t go on too late and I have the window open to get some fresh air. I’d love to work with music on, a lot of my friends do, and they say it really helps them concentrate. The point is I like music too much – it takes over from whatever I’m supposed to be doing.',
         'I’m hopeless at doing school projects. I make timetables so that I can complete the project well before the deadline, but I don’t stick to them. I’ve tried everything – strong coffee, quiet rooms, fresh air. Even though I’m wide awake and there’s nothing to disturb me, the work still doesn’t get done. I was getting really worried last week, when Mary came round and asked if she could work in my room – hers is too dark and stuffy. I’ve never worked with a friend before and so I said ‘No’, but she was desperate. Eventually, I gave in and it really worked out for us both. I couldn’t believe it!',
         'I really like some of the subjects I’m doing this year, particularly maths and physics. I don’t mind studying them at all, although some of the homework assignments we’re given are quite tricky, so I need to be able to work undisturbed. That’s often a bit difficult in our house, unless I put it off until everyone’s in bed. Did you know that my younger brother, Fred, plays the guitar in a band? I love some of their music, it’s really cool, you’d love it too, but it’s pointless trying to work when he’s playing.',
     ]},
    # ---- audioskript Part 3, EXERCISE 18 ----
    {"no": 18,
     "topic": 'You hear five people talking about a hotel they stayed in with their children.',
     "options": [
         'The room was rather small but it was cheap.',
         'We had more than one room to ourselves.',
         'Younger children stayed and ate at no extra cost.',
         'There was little for the children to do apart from swim.',
         'Part of the hotel was reserved for adults in the evening.',
         'The hotel was the cheapest one we could find.',
         'The staff looked after the children for us.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'We chose this hotel because we knew that the owners had young children of their own. The room could have been a bit bigger, but then it was quite inexpensive. They provided an early supper if you told them in good time, so that the parents could eat in peace later in the cosy dining room. There were hundreds of toys for the children to play with, a huge garden with a playground, ponds and a playhouse. We hardly saw our two all week.',
         'We always have difficulty finding hotels which welcome our children. This one was particularly good because the bedroom had a separate sitting room so we weren’t all squashed together in one room. Although it wasn’t the cheapest around, far from it in fact, it was worth it. Our teenage kids loved the outdoor heated swimming pool and the mountain bikes, which were provided free by the hotel. Apparently, the owners’ kids, who’ve grown up and left home now, had been mad on mountain biking. There was also an all-weather tennis court. Another thing we liked was the separate dining room for people with young families.',
         'We’d had a bad experience the year before at a hotel which didn’t cater for children. But this year we were very impressed by the hospitality of the hotel. The rooms were large enough to accommodate four beds comfortably and there was an adventure playground in the garden for the younger kids. You don’t have to pay for children under ten sharing the room – even meals were free for them, so that was another bonus. There was lots to do including horse riding and tennis. But if you wanted to swim you had to go to the local leisure centre, which the kids loved.',
         'In the hotel we went to, we had a family suite which was very spacious. There was an outdoor heated pool and large grounds so the kids spent most of the time in the pool. So long as your children like swimming you’re alright ’cos there wasn’t much else for them to do. I did think that they could have put in a playground too. Young children under ten aren’t allowed in the dining room but there was an early supper for them. This meant that we could have a quiet dinner for two when they were in bed.',
         'What we liked about our hotel was its size. It was only a small hotel and we were looked after like family. The room had loads of soft toys, wooden toys and books, which the children loved. The guest lounge and conservatory was a child-free zone after seven thirty which suited us fine ’cos there was a special children’s supper at six, which meant that they could go to bed early and get a good night’s sleep. Older children aren’t really catered for and this hotel is probably better for those with younger kids.',
     ]},
    # ---- audioskript Part 3, EXERCISE 19 ----
    {"no": 19,
     "topic": 'You hear five people talking about a cycle race they took part in.',
     "options": [
         'I fell off my bike more than once.',
         'My bike developed a fault during the race.',
         'I gave up because I was not fit enough.',
         'Other road users slowed me down.',
         'My preparation caused me an injury.',
         'I got lost during the race.',
         'The weather made the race very difficult.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'This was my first bike ride across the really difficult ground. When you ride at speed on rough tracks, it’s hard to find an easy riding position, and as a result you get an unpleasant stiffness in your back. You can stand up on the bike, and that sometimes helps. But it didn’t with me I found myself flying over the handle bar a couple of times, landing on soft grass, luckily. If the bike had been damaged I’d have stopped then and there, but it was OK. I carried on to the end but the slight pain in my back didn’t get any better.',
         'We cycled through towns and also through remote areas, and everything was fine until I came to a hilly bit. I knew I had an advantage here, because I’m good at speeding up slopes. No aching muscles for me! But at some point during the climb, I noticed one of the wheels needed adjusting. I’d been told before the start that there’d be a support team, so even if your bike broke down they’d be there to help you immediately. Well, they certainly weren’t capable of running things properly because I had to wait far too long, and so was one of the last competitors to reach the finishing line.',
         'I’d been involved in all the planning stages of the race, and so it seemed a good idea to take part. However, halfway through, I realised my best option was to turn back. I hadn’t done enough training. In a race like that, you need to keep a regular speed, even when you are going up what looks like a mountainside. If you are not fit enough, your leg muscles may seem to refuse to keep on pedalling hard! I saw other riders speeding past me – I couldn’t believe it. Anyway, I thought, this is silly, I may end up with a torn muscle, so that was that.',
         'Well, I think I was just plain unlucky. I came up this village road and there were all these cars moving slowly uphill. There had been an accident or something. Anyway, it was impossible to overtake them, on such a narrow path, so they slowed me down. I’m content with what I’ve achieved, although I didn’t win any of the prizes. Basically, I managed all the difficult bits of the race, and I know that if it hadn’t been for that problem, I would have had a good chance of winning. Also my bike was great, I’d had it repaired recently and wasn’t sure it would stand this test.',
         'I have lots of cycling experience, but I knew this was going to be a long race, and your muscles can get very tired and strained. But I was ready for the challenge, after months of weightlifting to increase my strength. In fact, I could almost say I overdid it, because I developed an elbow problem a couple of months before the race, which fortunately was not serious. But I certainly wasn’t expecting my bike to give me any trouble! But that’s what happened, unfortunately. I had started the race feeling fitter than ever, so it was all the more disappointing that it had to end like this.',
     ]},
    # ---- audioskript Part 3, EXERCISE 20 ----
    {"no": 20,
     "topic": 'You hear five people talking about a trip they took.',
     "options": [
         'A change in our circumstances made the trip possible.',
         'It was a childhood dream that I finally researched.',
         'The level of service was more than I wanted.',
         'The hotel was worse than the pictures suggested.',
         'The history of the place made the greatest impression.',
         'The journey there was very uncomfortable.',
         'We spent far more money than we had planned.',
     ],
     "answers": [0, 1, 2, 3, 4],
     "speakers": [
         'It came as a complete surprise. Right out of the blue she came home and told me she’d been made redundant from work and said why didn’t we just take off for a year and travel around the world.Well, it just all seemed to make sense. I wasn’t enjoying my work at the time and was thinking about doing something else. Her company had given her quite a generous redundancy package and also we could rent out our house for the year; that would give us enough to live on for the year as long as we were careful with our money. And I’m pleased to say that we were, apart from the occasional few luxuries here and there… you know, meals in expensive restaurants for special occasions like birthdays or anniversaries, that kind of thing.',
         'It’s something I’d been looking into for some time. To tell you the truth, it’s something I’ve wanted to do ever since I was a kid. It just never seemed that it would be something I could realistically do, so it just remained a dream. But after somebody told me how cheap it was when you actually got there I started to do some serious research. And really, although actually getting there is very expensive, the price of the hotels, restaurants and travelling around the country is so low compared to places in Europe, it means that in total you’re not paying much more than you would for a cheap holiday on the beach in Greece or Spain. And it’s a lot more interesting than just lying around on a beach somewhere. It was great. I’m going back there next year. I didn’t think I would ever be able to say that.',
         'It’s not every day you go on honeymoon, but if you ask me it was all a bit over the top. We had our own private beach and the staff couldn’t do enough for us: they wouldn’t let us do a thing for ourselves. For example if I tried to pour myself a drink, somebody would suddenly appear and take the bottle out of my hand and finish pouring it. I know it’s all these luxuries that you’re paying for but it’s a bit much for me and wasn’t something I was comfortable with. I suppose you must just get used to it after a while, but all the time I kept thinking that it would have been a better idea if we’d used that money to buy a washing machine and some new furniture instead of going to all that expense.',
         'To tell you the truth, the hotel was a bit of a letdown. The pictures in the brochure were flattering to say the very least. The restaurant was supposed to be five star but I can honestly say I’ve had better food in a motorway service station. It wasn’t all bad though, the area itself was lovely. The beach near the village was lovely and had everything you could ask for… clean white sand, beautiful blue sea, palm trees. And the locals were really friendly and really made a fuss of the kids. I think we’ll go back there soon, but we’ll definitely stay in a different hotel, that one wasn’t good value for money at all.',
         'I’d really been looking forward to going there and I wasn’t disappointed. Not in the least. From the moment you arrive there you feel immersed in its history. It’s the birthplace of civilisation after all, and every street you walk down reminds you of this. I know some people wouldn’t find it much fun, to be going from boring museum to boring museum, but it wasn’t like that. When you see some of the collections they have in the museums, and you see it in context to the city itself, well, it’s an extraordinary feeling. The weather wasn’t great but I don’t think that spoiled it for us at all. It’s not like you go to a place like that just to sit on the beach and get a tan. We had a week there, but really you’d need a month just to see everything.',
     ]},
]



def _perm(n_opts, e):
    """Variantlarni aralashtirish uchun almashtirish.

    7 tub son bo'lgani uchun i -> (i * m + s) % 7 har qanday
    m = 2..6 da to'liq almashtirish beradi."""
    m = 2 + (e % 5)
    s = e % 7
    return [(i * m + s) % n_opts for i in range(n_opts)]


def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase)."""
    out = []
    for e, st in enumerate(SETS):
        opts = st["options"]
        pos = _perm(len(opts), e)
        new = [None] * len(opts)
        for i, t in enumerate(opts):
            new[pos[i]] = t
        labelled = [f"{LET[k]}. {t}" for k, t in enumerate(new)]
        step = 1 + e // 4          # 1..5
        for si, (say, ai) in enumerate(zip(st["speakers"],
                                           st["answers"]), 1):
            ans = labelled[pos[ai]]
            expl = (f"To'g'ri javob: {ans}  "
                    f"(audioskript Part 3, {st['no']}-mashq, "
                    f"{si}-so'zlovchi).")
            out.append((
                KIND, step,
                {"say": say,
                 "rate": RATE,
                 "options": labelled,
                 "prompt": f"{st['topic']}  —  Speaker {si}",
                 "step": step,
                 "order": st["no"] * 10 + si,
                 "hint": "Beshta so'zlovchi, yettita fikr — "
                         "ikkitasi ortiqcha",
                 # Uzun monolog: ikki marta ketma-ket o'qilsa 3
                 # daqiqa ketadi va javob berishga imkon qolmaydi.
                 # Shuning uchun bir marta o'qiladi, ikkinchisini
                 # o'quvchi "Yana eshitish" bilan o'zi boshlaydi.
                 "plays": 1,
                 "gap_ms": 1500},
                ans, expl, None, None))
    return out


def seed_speaker(db):
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
