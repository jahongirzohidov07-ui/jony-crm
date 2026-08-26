# -*- coding: utf-8 -*-
"""CEFR LISTENING 5-QISM — THREE EXTRACTS (2026-08-26).

Jahongir: "endi qolgan partlarga ham 100tadan tuzib qoy."

FORMAT (kitobdan): "You will hear three extracts. Choose the
correct answer (A, B or C) for each question (1-6). There are
TWO questions for each extract."

MATN MANBASI. 17 ta mashq, 51 ta parcha — hammasi Multilevel
Master audioskriptining Part 5 qismidan AYNAN olingan
(o'rtacha 1090 belgi). Savollar va uchta variant shu yerda
tuzildi: kitobning javob kaliti skanerda, ishonchli o'qib
bo'lmadi, taxmin qilish esa noto'g'ri kontent yaratardi.

BU QISM NIMANI SINAYDI. Boshqa qismlarda ma'lumot ilib
olinadi; bu yerda esa MUNOSABAT va FIKR so'raladi: "How does
he feel...", "What do they agree about...", "What surprised
her...". Javob deyarli hech qachon bitta jumlada turmaydi —
butun parchadan xulosa chiqariladi.
"""

SKILL = "ielts_listening"
KIND = "cefr_extract"
LET = ["A", "B", "C"]
RATE = 0.95


EXTRACT_TIPS = [
    ('Bu mashq nima',
     "Uchta suhbat yoki intervyu eshitiladi, har biriga IKKITA savol beriladi. Javob A, B yoki C. Bu CEFR'ning eng qiyin qismi.",
     ''),
    ("Avval SAVOLNI o'qing, variantni emas",
     "Savol nimani so'rayotganini aniqlang: fikrmi, his-tuyg'umi, sabab-mi, kelishuvmi. Uch variantni oldindan o'qisangiz, hammasi eshitilganday tuyuladi.",
     ''),
    ("Javob bitta jumlada bo'lmaydi",
     "Boshqa qismlarda bitta so'zni ilib olasiz. Bu yerda esa so'zlovchining butun aytganidan XULOSA chiqarasiz. Bitta jumlaga tayanib javob bermang.",
     ''),
    ('«Ikkalasi nima haqida kelishadi?» savoli',
     "Bunda IKKALA so'zlovchi ham aytgan fikrni qidiring. Bittasi aytib, ikkinchisi rad etgan narsa — noto'g'ri javob.",
     "Ayol: «they've probably overpaid» / Erkak: «they were overcharged for him» -> ikkalasi ham qimmat deb hisoblaydi."),
    ('Birinchi eshitilgan narsa javob emas',
     "Ko'pincha so'zlovchi avval bir fikrni aytadi, keyin «but», «actually», «mind you» bilan uni o'zgartiradi. To'g'ri javob OXIRGI holatda bo'ladi.",
     ''),
    ('Suhbatdoshning gapiga aldanmang',
     "Savol ko'pincha bitta odam haqida bo'ladi. Ikkinchi odam aytgan narsa juda ishonarli variant bo'lib qo'yiladi.",
     "Do'sti: «I expect he was hungry» — lekin savol AYOLNING fikrini so'rayapti."),
    ("Ikki savolni birga o'qing",
     "Parcha bir marta o'qiladi va ikkala savolga javob kerak. Boshlashdan oldin ikkalasini ham ko'zdan kechiring — aks holda birinchisiga javob izlab, ikkinchisini o'tkazib yuborasiz.",
     ''),
]


EXTRACTS = [
    # --- audioskript Part 5, EXERCISE 1, Extract 1 ---
    {"no": 1, "idx": 1,
     "say": 'Interviewer: So, Fiona, can you tell me about how you started in fashion retailing? Fiona: Yes, of course. After I finished university, I took a job with a big high street chain – I was an assistant manager. Every week you would see the sales figures for your product and then act on that by placing repeat orders or putting a new style in. It was a good grounding. However, most of the staff had been there years and I think I did make mistakes in my dealings with them – I blush now to think of my time there. I then moved on, after five years, to my present job. Interviewer: And now you’re thinking of moving up the ladder. How do you see yourself in ten years’ time? Fiona: I would eventually like to be in senior management. Interviewer: Well, before you rush off to see your line manager, I think you need to work out skills you can offer emphasising your selling points, showing them what you can do. Also have you been going the extra mile to get things done or doing more than what is asked of you, recently?',
     "qs": [
         ('What does Fiona regret about her first job?',
          ['the long hours she had to work', 'the way she dealt with the other staff', 'the stock decisions she made'],
          1),
         ('What does the interviewer advise Fiona to do?',
          ['speak to her line manager at once', 'work out what she can offer an employer', 'apply to a different company'],
          1),
     ]},
    # --- audioskript Part 5, EXERCISE 1, Extract 2 ---
    {"no": 1, "idx": 2,
     "say": 'Friend: So, what happened last weekend? Woman: Well, we were taking our boat along the river, when we passed a pair of swans, with a nest nearby. One swan just carried on feeding, but the other one – the male I think – decided to come and investigate. Friend: Oh, fantastic. I’ve never seen a swan’s nest close up. I expect he was hungry. Woman: Well, actually it was immediately obvious from his body language that he had other things on his mind. He was flapping his wings really hard, and approaching at incredible speed. And I guess we’d gone too close to the nest. I’d never have done that if I’d known what would happen. Friend: Gosh, amazing. I’ve never heard of swans behaving like that before. So what did you do? Row like mad? Woman: Well, we got out onto the bank, but he followed us up, and then stood between us and the boat for about an hour! We just couldn’t frighten him away. Friend: No, I suppose not. Still, I’m sure he wouldn’t have hurt you. Woman: Are you kidding? You should have seen the way he moved – swans can be really aggressive at nesting times. Friend: Hmm.',
     "qs": [
         ('What does the woman say about the swan?',
          ['She realised at once that it was angry.', 'She thought it was looking for food.', 'She had expected it because of the season.'],
          0),
         ('How did the incident end?',
          ['They managed to frighten the bird away.', 'They were kept away from their boat for a long time.', 'They rowed off as fast as they could.'],
          1),
     ]},
    # --- audioskript Part 5, EXERCISE 1, Extract 3 ---
    {"no": 1, "idx": 3,
     "say": 'Interviewer: Bruce, at school, you discovered you had a natural talent for art. Bruce: Yes, I inherited my dad’s gift for drawing. I wanted to do representational art; paint portraits. But every college I went to – and there were three who accepted me – all the college tutors said, ‘Forget representational art, get a single lens reflex -millimetre camera, hit the shutter, crash, there’s your picture. Not even Rembrandt could get that accuracy, so it’s not worth it.’ Interviewer: And you believed them? Bruce: I did. That was my biggest mistake. I haven’t picked up a paintbrush since. Interviewer: How did your father react, when you told him you weren’t going to art college? Bruce: His face was white with rage. He said, ‘Right, that’s it. You could have made something of going to college. You won’t get another chance. Now I’ve got a perfectly good job for you on the factory floor. You start this week – take it or leave it.’ I said, ‘No, I’m going to start a business next.’ He said, ‘Well, at your own expense, then.’ Interviewer: He refused to support you any more? Bruce: That’s it, and so…',
     "qs": [
         ('What does Bruce consider his biggest mistake?',
          ['applying to three different colleges', 'choosing representational art', 'accepting what his tutors told him'],
          2),
         ("How did Bruce's father react to his decision?",
          ['He offered to pay for a business.', 'He was furious and withdrew his support.', 'He agreed that the college was wrong.'],
          1),
     ]},
    # --- audioskript Part 5, EXERCISE 2, Extract 1 ---
    {"no": 2, "idx": 1,
     "say": 'John: So, Diane, have you finally decided to come to Hong Kong with us for a holiday? Your flight’s reserved, we need to confirm by Wednesday. Diane: Well, John, I’ve given it some thought and it’s pretty tempting, but it’s not that long since I last had a break. I don’t know – I still haven’t come to any definite decision. John: Oh, come on, what’s the problem? I know it may seem extravagant, but you told me you’d just been given promotion and a rise, so that can’t be an issue, surely. Diane: Well, it’s not so much that as my work situation. Taking another break so soon after my promotion might send out the wrong message to my team, although I think my line manager would understand. John: Of course – she knows you’re a good worker. Diane: Hmm. Well, I guess I could empty my in-tray in time – my workload’s not too heavy just now. It’s just that I haven’t had much time to get the office organised, and to be honest, one of my colleagues would probably be only too glad to use my absence to further his own position. John: Hmm, sounds pretty nasty to me. Are you sure you want to carry on working there?',
     "qs": [
         ('Why is Diane hesitating about the holiday?',
          ['She cannot really afford it.', 'She is worried about how it would look at work.', 'Her manager has refused to allow it.'],
          1),
         ('What does Diane say about one of her colleagues?',
          ['He might use her absence to his own advantage.', 'He would have to do all her work.', 'He has just had a holiday himself.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 2, Extract 2 ---
    {"no": 2, "idx": 2,
     "say": 'Man: I hear Joe Schultz’s new film The System isn’t going to be given the ‘ ’ certificate he wanted. Woman: So youngsters can’t see it? I’m not surprised. The reviewers say that watching the first few minutes is pretty unpleasant – there’s a lot of aggression. Man: That didn’t seem to worry the authorities. Nor did the strong language, although there’s quite a bit of that, but they couldn’t take the little bursts of rather tense music – makes your hair stand on end, apparently! Woman: Interesting. Anyway, I don’t think the storyline’s really suitable for young children – too much delving into people’s thoughts and motives. Man: True. You’ve read the book? Woman: Oh yeah. A great page-turner. I had no idea what the final outcome would be. Man: Oh, I guessed. I loved the way the author uses dialect all the way through – a bit out of the ordinary. Woman: Takes some getting used to, but it’s decidedly different. You can’t really believe the Prince is based on a real person from the past, though, can you? Man: I thought he did come over well, considering how little we know about people from that era. Woman: We’ll go and see the film, won’t we? Man: Definitely.',
     "qs": [
         ('According to the man, why was the film refused the certificate?',
          ['because of the violence in it', 'because of the language used', 'because of the music'],
          2),
         ('What do the man and woman disagree about?',
          ['whether the ending of the book was predictable', 'whether the dialect was effective', 'whether they will go and see the film'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 2, Extract 3 ---
    {"no": 2, "idx": 3,
     "say": 'Interviewer: Ingrid Chapman, tell us about this new office block. Ingrid: It has enormous glass walls, because transparency was paramount in the brief I received from my clients – that gives it an airy, spacious feel inside. The three floors all open onto a cavernous central hall, and this is what’s crucial for me – there are so many reasons for people to meet there: have a coffee, gossip, discuss formal matters in an informal setting. I force them to do these things by locating most of the services they need in this area – toilets, photocopying, cafe, etc. Interviewer: Forgive me, but there’ll be company executives listening who are saying, ‘That’s all very well if you’re able to design a brand new building from scratch.’ What would you say to them? Ingrid: Commission me to come up with a scheme for a replacement, for example? No, seriously, it doesn’t require much, a little creativity, that’s all. Under-used areas can be refurbished, art hung on the walls, that sort of thing. And a questionnaire can be sent to all personnel to get their reactions to any changes you’ve made. Good morale facilitates productivity.',
     "qs": [
         ('What does Ingrid say matters most in her design?',
          ['the amount of natural light', 'the central space where people meet', 'the number of floors'],
          1),
         ('What does Ingrid say to companies in older buildings?',
          ['They should commission a new building.', 'Small, inexpensive changes are enough.', 'They should let staff redesign the space.'],
          1),
     ]},
    # --- audioskript Part 5, EXERCISE 3, Extract 1 ---
    {"no": 3, "idx": 1,
     "say": 'Eva: So the thing is, you aren’t getting on with our new boss then, Colin? Colin: She’s just so different from her predecessor. I mean, John used to get us all involved in the decision-making process. Eva: No chance of that with Sandra, you think? Colin: No way! OK, I grant you, she’s got some good ideas – she moved pretty fast to get us all to agree to individual job descriptions and a proper timetable, none of which we’ve had before and we should have had. And she’s done her homework on the staff profile, our qualifications and past experience and so on… Eva: As you’d expect. Colin: Yes. But she doesn’t seem aware of the atmosphere here – it’s the way we’ve always done things. I just don’t feel I can work with her. Eva: I’d say she’s just finding her feet in a new job, and she’ll soon get the hang of what we’re all about. Let’s focus on how much she’s already achieved. I wouldn’t let anybody tell you it’s a trivial issue, though. If she doesn’t settle in soon, and you still have issues with her, I think you should approach her direct. Colin: OK, thanks, Eva.',
     "qs": [
         ("What is Colin's main complaint about the new boss?",
          ['She does not understand how things are done there.', 'She has introduced no new ideas at all.', "She knows nothing about the staff's background."],
          0),
         ('What does Eva advise Colin to do?',
          ['treat the problem as unimportant', 'complain to someone more senior', 'speak to the boss himself if things do not improve'],
          2),
     ]},
    # --- audioskript Part 5, EXERCISE 3, Extract 2 ---
    {"no": 3, "idx": 2,
     "say": 'Interviewer: Show me how you do it. I see you’ve got trays and trays of pieces here. Expert: Yes, you have to find the bits that match, so I’ve put all these tiny pieces into colour groups – red here, blue over there. It’s a bit like doing a jigsaw, really. But at least there are no stains to remove. All we have to be aware of is the enamel on the surface; that we have to lift all the dirt and grease off. If you don’t, the pieces won’t go back together again, it’ll fall apart. If the cracks are going to show, they’ve got to be really clean, otherwise they’ll look messy. Interviewer: You want the cracks to show? Some people would say that’s terrible, for such a valuable vase. Expert: Well, yes, they probably would, but something that’s broken so extensively as this, if you cover all the cracks up you’re really making a fake. Being broken is something that’s happened to it in its lifetime, which should be recorded, and as long as you can restore it so that aesthetically it still works, it shouldn’t matter that the cracks show…',
     "qs": [
         ('What does the expert say must be done before the pieces are joined?',
          ['sorting them into colour groups', 'removing all the dirt and grease', 'taking out the stains'],
          1),
         ('Why does the expert think the cracks should be visible?',
          ["They are part of the object's history.", 'They make the repair cheaper.', 'They cannot be hidden completely.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 3, Extract 3 ---
    {"no": 3, "idx": 3,
     "say": 'Woman: This is such an unusual place because there’s no public transport to the island – I came here in your fishing boat. The result is a paradise – rich marine life, unspoilt countryside. Yet you want to let the world in – you’ve campaigned to start up a ferry service from the mainland. Why? Man: There isn’t enough work to support our population. If visitors come to the island – and we have a lot to offer them – catering for them would create employment. Also our young people would be able to commute to jobs on the mainland. Woman: Don’t you think it’s risky? These beaches could be covered with holiday houses and hotels; your visitors will complain because there are only a few shops. And a ferry service won’t be enough. People will want to fly here, and you’ll have to build an airport. No more paradise! Man: We can build a small airport without impacting on our quality of life here, and it makes economic sense. Our shops can cope with more people on the island – it’ll be seasonal anyway. And why would we build on the beaches? It’d be crazy. Woman: I hope you’re right.',
     "qs": [
         ('Why does the man want a ferry service?',
          ['to create work and let young people commute', 'to bring more shops to the island', 'to protect the marine life'],
          0),
         ("How does the man respond to the woman's warnings?",
          ['He admits an airport would ruin the island.', 'He believes the island can grow without damage.', 'He agrees the shops could not cope.'],
          1),
     ]},
    # --- audioskript Part 5, EXERCISE 4, Extract 1 ---
    {"no": 4, "idx": 1,
     "say": 'Woman: So is John Elliott a player you like to watch? I’m guessing he is. Man: Yes, he’s excellent, very technical, clever with the ball; he’s good at passing the ball to the team’s top goal scorers and setting them up to shoot. When he sees that final pass coming as he approaches the goal area, you get a lot of players who get there but then freeze and get erratic, but he’s not one of them. So if you can get him backing up the strikers, he can be the key player. Woman: And what about their new man, Danny Martinez? Seven million they paid for him, they’ve probably overpaid. Not very cautious given that they’ve paid out this kind of cash before and it all went wrong, didn’t it? They’ll want to hang on to him come what may, at that price… Man: Yes, well, it hasn’t broken the bank, but they were overcharged for him. They probably thought he was a good investment – he’s young, they can sell him on if things go wrong, for more money. They got their fingers burnt once over a similar deal, and they won’t want it to happen again.',
     "qs": [
         ('What does the man admire about John Elliott?',
          ['He scores a great many goals himself.', 'He stays calm near the goal area.', 'He is the most experienced player.'],
          1),
         ('What do the speakers agree about Danny Martinez?',
          ['The club paid too much for him.', 'The club will sell him quickly.', 'He is too young for the team.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 4, Extract 2 ---
    {"no": 4, "idx": 2,
     "say": 'Interviewer: Congratulations, Deanna! Deanna: Thanks very much. Interviewer: Were you surprised to win? Deanna: Completely! Interviewer: Now you’re trying to save a wildlife habitat that stretches 3, kilometres along the coast of South America. Aren’t you daunted by that? Deanna: It’s a huge task but we’re basically getting the message out: the local fish population – mainly anchovies – are being forced into colder water because the sea’s warming up. Of those left, per cent are being scooped up by industrial fishing trawlers so predators like seals, penguins and dolphins – and local fishermen – are left with very little. Now this is the richest ecosystem in the world. If it’s starting to be affected, you know there must be a tremendous impact on other less robust systems. Interviewer: So what’s your relationship like with local fishermen? Deanna: They used to regard me as an enemy because I used to work for seals, and as you know, fishermen and seals compete for the same fish – but now they see me as an ally trying to control industrial fishing. Interviewer: What – stopping them scooping up anchovies? Deanna: Not stopping them, but getting them to catch less; which means the local fishermen can catch more of the large fish that feed on the anchovies.',
     "qs": [
         ('What does Deanna say about the anchovies?',
          ['They are moving because the sea is warming.', 'They are no longer eaten by predators.', 'They are now protected by law.'],
          0),
         ("How has the local fishermen's attitude to Deanna changed?",
          ['They now see her as being on their side.', 'They now compete with her for fish.', 'They now want industrial fishing stopped completely.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 4, Extract 3 ---
    {"no": 4, "idx": 3,
     "say": 'Neil: Today we’re talking about books that have inspired us, books that have made a difference to our lives. Each of my studio guests has chosen what for them was an important book and first off we’re going to hear about Monica Naim’s choice. Monica. Monica: Thanks, Neil. Well the thing about this book is that when I first discovered it in my late teens – it was a birthday present, if I remember correctly – I’d never really read anything like it before. I’d heard about it from a friend, and I’d got the idea it was something special and so I asked for it specifically. I think I was about , so I was a fairly late developer as a reader. I hadn’t been particularly interested up till then, but it suddenly sort of took a grip. I think it was the strangeness of that book; I mean it’s the one I’d take with me to a desert island because it’s just got everything in it and it just opened me up to what pleasures there are in description, in narrative, you know, in ideas. Neil: Well, we’ll discover exactly which book my next guest has chosen…',
     "qs": [
         ('How did Monica get the book?',
          ['She was given it as a present.', 'She borrowed it from a friend.', 'She came across it by chance.'],
          0),
         ('What does Monica say about herself as a young reader?',
          ['She had read many similar books before.', 'She came to reading fairly late.', 'She preferred description to narrative.'],
          1),
     ]},
    # --- audioskript Part 5, EXERCISE 5, Extract 1 ---
    {"no": 5, "idx": 1,
     "say": 'Gordon: Annabelle, you saw A Secret Place the other day, didn’t you? Annabelle: I did. Interesting, but the action’s very patchy – it falls apart here and there. Gordon: There isn’t a thread you can follow all the way through , is there? I can see what the director… Annabelle: Yoshiki Muto. Gordon: Yeah. I can see what he’s trying to do – it’s a complex layering of detail, but it just doesn’t come off. Annabelle: Well, it’s a brave attempt. It works for me. Although I have to say, I still really prefer the original novel with its very delicate touch. Gordon: I think, though, the film version taps into our emotions more. But what about the ending? Annabelle: I’d have enjoyed it more if it hadn’t been for that powerful, pounding rock music, which was obviously supposed to emphasise what was happening on screen. But I did like the way I was on the verge of laughing, then almost crying, for that final two or three minutes. Very well done . Gordon: Not that it really appeared to sort anything out for our hero. Annabelle: Presumably he’ll turn up in a sequel soon, with the same old dilemma! Gordon: Look forward to that then!',
     "qs": [
         ('What do Gordon and Annabelle agree about the film?',
          ['The story is hard to follow all the way through.', 'It is better than the original novel.', "The director's approach was successful."],
          0),
         ('What did Annabelle dislike about the ending?',
          ['the music', 'the acting', 'the length'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 5, Extract 2 ---
    {"no": 5, "idx": 2,
     "say": 'Interviewer: So, Alan, what’s the best way to get good public architecture? Alan: Well, people don’t want to be challenged by architecture, that’s understandable in a way; I’m not one for saying necessarily that public buildings are an appropriate area where people should have a vote to say that this building should go ahead or not. Many of our greatest and most glorious buildings wouldn’t exist if that happened. Take St Paul’s Cathedral in London – at the time, people were very antagonistic and hated its horrid foreign style. Now everyone adores it; it’s a landmark, a sort of emblem of the city, that wouldn’t have existed if public opinion had had its way. Interviewer: Do other countries do better than us – either in terms of imagination, or in terms of the kind of decision-making we’ve been talking about? Alan: Yes they do – in recent history anyway. The Netherlands is a prime example. A number of the world’s leading architects happen to come from there, but the important thing is that the people are very knowledgeable; they learn about architecture in school. They do have a good record for town- planning as well, but that’s hardly the point.',
     "qs": [
         ("What is Alan's view on letting the public vote on buildings?",
          ['It would prevent great buildings from being built.', 'It is the fairest way to decide.', 'It should be used only for landmarks.'],
          0),
         ('What does Alan say about the Netherlands?',
          ['It does better than his own country.', 'Its architects mostly work abroad.', 'Its public is never consulted.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 5, Extract 3 ---
    {"no": 5, "idx": 3,
     "say": 'Interviewer: Why did you decide to publicise climate change in this way? Lorna: Well, I was really upset about some countries’ failure to sign up to pollution agreements; it felt like the science wasn’t getting through to the politicians, so I decided to look into what I personally could do. That led me to dream up a cartoon character called Mr Carbon – we all know somebody like him – he’s climate-ignorant and makes no effort to save energy. Factories are the obvious villains, of course, but I couldn’t do much about them. Interviewer: So are we going to see him in scenes like we get in disaster movies? Lorna: That’s pretty unlikely – you need a lot of alarmist nonsense to make a box office success. But the reality certainly gives cause for concern. Interviewer: So you came up with the idea of another cartoon character, Mrs Green. Lorna: Yes – now she pays attention to little things, uses low-energy light bulbs, doesn’t leave the TV on standby, goes in for recycling. And, can you believe it, as well as making a huge difference to her climate impact, she’ll save one hundred and fifty thousand dollars over her lifetime. Interviewer: That’s incredible!',
     "qs": [
         ('Why did Lorna create the character Mr Carbon?',
          ['Politicians were not listening to the science.', 'Factories refused to change their practices.', 'A film company asked her to.'],
          0),
         ('What does Lorna say about disaster-film scenes?',
          ['She is unlikely to use them.', 'They are the best way to shock people.', 'They would be too expensive to draw.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 6, Extract 1 ---
    {"no": 6, "idx": 1,
     "say": 'Woman: Sorry to be late. This club’s a bit off the beaten track, isn’t it? Thought I’d never find it! Secretary: You don’t have an in-car satellite navigation system, then? Woman: A sat-nav? No I don’t, though I suppose I should invest in one. I often have this sort of trouble – getting to a town’s a piece of cake, but after that… well. It’s not so much the cost – my friends all have them and tell me the price is going down all the time. But electronic gadgets aren’t my favourite things. Fine when they work; nightmare when they don’t. A little black box could hardly have been less useful than my map today, though! Secretary: I wouldn’t be without mine now. I won’t try and blind you with science, but I do know quite a bit about satellites. The technology’s amazing – position can be pinpointed to within a metre. Of course, accuracy’s down to the mapping companies who do the updating work, but new models come out all the time. It’s entirely up to you of course, but imagine never having to ask for directions again! Woman: That’d be good – I’ll certainly give it some thought!',
     "qs": [
         ('Why does the woman not own a sat-nav?',
          ['She dislikes electronic gadgets.', 'She thinks they cost too much.', 'She never has trouble finding places.'],
          0),
         ('What does the secretary emphasise about the technology?',
          ['how accurate it is', 'how cheap it has become', 'how often it goes wrong'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 6, Extract 2 ---
    {"no": 6, "idx": 2,
     "say": 'Paula: We both grew up in a fairly rough part of the city, Mike, so I’m assuming you used comedy to keep yourself safe – and popular in the long run! Mike: Well, in school, as you know, if you could run fast or make people laugh, you had a very good chance of surviving and emerging unscathed. I wasn’t a fast runner, so I exploited comedy to avoid unwelcome attention. It seemed to come easy, and it worked. Paula: Your type of comedy is less spontaneous than reflective. You see things from your own point of view, don’t you, and create a world for other people to see. Whereas I explore the world that’s already there, which most people don’t see. Mike: Don’t you think that the key to achieving what you want in life is the realisation that it’s going to be tough, and the sheer persistence that gets you there in the end? Paula: What you have to have is massive self-confidence. With that you can do anything. Mike: And being specific about what it is you want to do. Paula: Ah well, that goes without saying.',
     "qs": [
         ('Why did Mike use comedy at school?',
          ['to protect himself', 'to become popular with the teachers', 'because it was expected of him'],
          0),
         ('What do Mike and Paula disagree about?',
          ['what matters most in achieving your goals', 'whether comedy can be taught', 'where they grew up'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 6, Extract 3 ---
    {"no": 6, "idx": 3,
     "say": 'Woman: If you’re English, a nice sad nineteenth-century romance is very useful if you’re on holiday and you get attacked by homesickness because it conjures up dripping English autumn days perfectly. Man: I always take something by this chap who’s written a number of books about the criminal underworld of Boston, Massachusetts, which is hardly culturally or geographically a place that I know, but I find it fascinating. There’s no doubt about it if you compile, as I do, dictionaries of slang for a living, one is drawn inevitably not alas to the great classics, who are on the whole rather light on slang, but to someone like this fellow who has this amazing ability, far beyond quoting, of writing or pages of dialogue in almost incomprehensible slang, which I have the most wonderful time going through. I find it very alluring.',
     "qs": [
         ('Why does the woman take a nineteenth-century romance on holiday?',
          ['It reminds her of home.', 'It is easy to read on a beach.', 'It is set in the place she visits.'],
          0),
         ('What attracts the man to the books he takes?',
          ['the slang used in the dialogue', 'the crime stories themselves', 'his knowledge of Boston'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 7, Extract 1 ---
    {"no": 7, "idx": 1,
     "say": 'Woman: So, did you go to that play in the end? Man: I did, and it was an interesting experience. Woman: Really? Why’s that? Man: Well, for a start, the theatre was in Pelham Street. Now I’ve walked up and down that street many times, but I never realised there was a theatre there. Woman: No, nor had I. Has it always been there? Man: Apparently. Anyway, it took a bit of finding; you go through a doorway, down a passage – you know the sort of place. And when you do get inside, it’s really surprisingly intimate – I shouldn’t think it holds more than about forty people. Woman: And the play? Man: Well, the show was a big success up in London last year – huge audiences – but unfortunately only a handful of people turned up for last night’s performance. I’m not surprised though – it was rather amateurish. They could have done with using at least a bit of make-up and learning their parts better. They just about managed to cover up their mistakes by really throwing themselves into their characters. Woman: Yes, I know what you mean.',
     "qs": [
         ('What surprised the man about the theatre?',
          ['He had never noticed it before.', 'It was much larger than he expected.', 'It was hard to get a ticket for it.'],
          0),
         ('What did the man think of the performance?',
          ['It was rather amateurish.', 'The audience was far too large.', 'The make-up was very good.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 7, Extract 2 ---
    {"no": 7, "idx": 2,
     "say": 'Reporter: Excuse me, sir, could you spare a couple of minutes before the conference to answer some questions? Man: Well, if you could make it really brief. Reporter: You’re always identified with ‘responsible’ tourism – how do you feel it’s different from normal tourism? Man: Our trips have unique themes including culinary, spa, angling, indigenous peoples – plus those specially designed for groups with special needs. But it’s the tour organisation that really differentiates them from others. Take the Himalayas: several of our outdoor staff work only six months of the season but are well paid all year round. Then we always use solar powered equipment and make our environmental commitment known to every tourist… Reporter: Do you believe people are willing to pay more for your kind of tourism? Man: Not in the main, but I think they will be once their thinking is revolutionised: they just become aware of the global consequences of the choices they make. Then I think they’ll see that the future of the world depends on justice in commerce and industry and they’ll dig deep in their pockets – I must rush now, but come to my session!',
     "qs": [
         ('What does the man say makes his trips different?',
          ['the unusual themes they have', 'the way the tours are organised', 'the price he charges'],
          1),
         ('What does he think about people paying more?',
          ['They will once they understand the consequences.', 'Most of them are already willing to.', 'They will never accept higher prices.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 7, Extract 3 ---
    {"no": 7, "idx": 3,
     "say": 'Laura: So, Steve, what about next week’s all-important match in Melbourne – Australia versus Wales? The teams are pretty evenly matched, aren’t they? Steve: Australia are certainly the favourites, but whether they’ll pull it off and by what margin is anybody’s guess. Laura: A real cliff-hanger probably. And there’s huge interest in this match, but I understand the Welsh supporters haven’t been allowed enough tickets. Steve: As usual, the authorities have given priority to the home fans, but that seems eminently reasonable to me. Laura: There’s concern, isn’t there, about two of the Welsh players who are currently recovering from injuries? Steve: Yes, and there’s still doubt about whether they’ll play, but even if they don’t, I reckon it’ll be a gripping match to watch. And to anybody listening who’s lucky enough to have tickets, Melbourne’s filling up with school groups and junior teams because the Australians are very keen to encourage their youngsters to take up rugby, so better make sure you book somewhere to stay right now. And, of course, you could consider becoming a member of the Welsh team’s fan club, although it’s a bit late to take advantage of their cheap flight deals. Laura: Well, thanks for that, Steve.',
     "qs": [
         ('What does Steve say about the result of the match?',
          ['The winning margin is impossible to predict.', 'Australia will certainly lose.', 'The teams are not evenly matched.'],
          0),
         ("What is Steve's opinion about the ticket allocation?",
          ['He thinks it is reasonable.', 'He thinks Welsh fans were treated badly.', 'He thinks too many went to schools.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 8, Extract 1 ---
    {"no": 8, "idx": 1,
     "say": 'Interviewer: Why did you decide to include a painting by a famous politician? Man: I wanted to remind viewers that amateur painting has its own purpose, that scores and scores of people paint for themselves as that politician did. And I liked his daughter’s explanation that it helped to give him some respite from the pressures of public life. I thought that was important to focus on, so that we weren’t just talking about painters as professionals who had really cracked it and who taught us things about their technique. Interviewer: You draw yourself, don’t you? Man: Yes, I’ve always liked it though I’m afraid my attempts aren’t very good, so I keep them purely for my own amusement. The intensity of drawing is always a great thrill, i can’t say it’s a relief, which it obviously is for some people. You have to use your eyes to look more carefully at a scene than you would if you were just out for a walk, or even if you were taking a photograph as an amateur. There’s something about drawing that forces you to see things and think about them',
     "qs": [
         ("Why did the man include the politician's painting?",
          ['to show that people paint for their own sake', 'because the politician was a fine painter', "because the politician's daughter asked him to"],
          0),
         ('How does the man describe his own drawing?',
          ['It excites him rather than relaxing him.', 'It is good enough to exhibit.', 'He prefers photography to it.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 8, Extract 2 ---
    {"no": 8, "idx": 2,
     "say": 'Interviewer: I’ve only ever been up in a plane once where the pilot turned the plane over in an aerobatic display and I’ve never been more scared or felt sicker. Do you get that sinking feeling too, Gina? Gina: I’m very fortunate in that I don’t. This came as a pleasant surprise to me because I do get terribly seasick. I find that what is routine and what I’m used to doing isn’t frightening. Learning some of the new manoeuvres, though, can be quite daunting because this is a single-seater plane. So, the first time I do anything new, I’m on my own except for the guidance of my coach, who’s on the ground. Interviewer: What’s the real thrill for you of performing these difficult manoeuvres in competitions? Gina: It’s exciting of course, but ultimately the reward comes from knowing that you’ve done it with precision. It involves an unusual combination of mental preparation, physical preparation and skill. It’s not as difficult as you might first think to fly the sequences of movements. What is difficult is doing it to a high enough standard to avoid the faults the judges are looking out for.',
     "qs": [
         ('What surprised Gina about flying?',
          ['that it does not make her feel ill', 'that the plane has only one seat', 'that her coach stays on the ground'],
          0),
         ('What gives Gina most satisfaction?',
          ['doing the movements precisely', 'winning competitions', 'the physical preparation'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 8, Extract 3 ---
    {"no": 8, "idx": 3,
     "say": 'Fran: I’m exhausted. It took an hour to drive five kilometres! George: You should do what I do and use a motorbike. Fran: Is it much quicker? George: It is a bit, because you avoid some queues. The great thing is, when I put on my helmet, I’m shut away, you know, in my own little world and that means I arrive feeling quite calm. I started riding a motorbike where I grew up in the country because there weren’t any buses. Fran: So is that your most prized possession? I was asked recently what my favourite thing at home was. As a chef I imagine yours is something in the kitchen, your cooker perhaps. George: The one at the restaurant is fantastic because it was specially designed for me. It’s hard to say here. My family love the kitchen table, where they chat for hours. Given the late hours I work, I hardly participate in that. No, my workplace is so hot and sticky that what I long for is a shower when I get home. I feel the stresses of the day disappear with the water. Odd thing to choose, isn’t it?',
     "qs": [
         ('Why does George like riding a motorbike?',
          ['It lets him arrive feeling calm.', 'It is much faster than driving.', 'It costs far less than a car.'],
          0),
         ('What does George choose as his favourite thing at home?',
          ['the kitchen table', 'the cooker', 'the shower'],
          2),
     ]},
    # --- audioskript Part 5, EXERCISE 9, Extract 1 ---
    {"no": 9, "idx": 1,
     "say": 'Man: As a kid, I was always messing around on computers, so ended up doing a degree in computer science. Though strictly speaking it isn’t necessary for this job, it did mean I could walk straight into it. What companies want is people who can come up with ideas. I get a buzz from that side of it , even when it’s hard. It’s a fluid working environment, so hours aren’t fixed and can be long in relation to the salary. I generally like to work on my own, but a web designer can’t produce stuff in a vacuum, because by its very nature it’s a collaborative effort. Woman: I didn’t go the university route but worked part-time with different companies and made loads of contacts who’ve come in handy – got my foot in the door so to speak – then I got a full time job offer that got me on the ladder. It wasn’t easy, and considering what you put in the job’s not the big earner that people assume it is – at least not at the beginning! I supplement it by writing reviews of other people’s sites, but I enjoy the flexibility. I like working with other people, and that’s key.',
     "qs": [
         ('What does the man say about his degree?',
          ['It was not strictly necessary but it helped him start.', 'It taught him everything he needed.', 'He now regrets choosing it.'],
          0),
         ('What do the two speakers agree about the job?',
          ['The pay is lower than people assume.', 'It is best done alone.', 'A university degree is essential.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 9, Extract 2 ---
    {"no": 9, "idx": 2,
     "say": 'Woman: How long have you been cycling then? Man: I started road cycling when I was six, and got hooked immediately. I’d practise sprinting between two streetlights over and over. I’ve always been competitive, and I work harder than anyone else. If I don’t win I need to know why. I copy the person who beat me. I won’t stop till I’m better than them. The stiff competition in the cycling world is what drives me. You’ve been to the velodrome, haven’t you? Woman: Yeah. The track itself is amazing – such a steep angle and the bikes have no brakes. If you stop pedalling it stops! Although I’m not such an experienced cyclist as you, I jumped at the chance to try it and, wow! From the position of the start line that steep slope looks like a mountain! I was told the faster you go the safer you are, so I pedalled like mad, and managed one lap. I kept going and started to enjoy it; so much so I forgot to pedal, and immediately fell off! Man: So you’ll go be going back? Woman: You try stopping me!',
     "qs": [
         ('What drives the man to succeed?',
          ['the strong competition', 'the money he can earn', "his coach's encouragement"],
          0),
         ('How did the woman feel at the velodrome?',
          ['She enjoyed it and wants to go back.', 'She was too frightened to finish a lap.', 'She found the bikes easy to control.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 9, Extract 3 ---
    {"no": 9, "idx": 3,
     "say": 'Interviewer: So, Roy, what do you want to talk about on the programme today? Roy: I want to talk about bees. Bees are a vital part of our ecosystem, they’re friendly creatures and they’re declining in numbers. For what it’s worth, my own experience is much like that of other callers who’ve reported near normal numbers of bumble bees but virtually no honey bees. I think there’s a distinct lack of wasps, too. I’m at a loss to know why, though I’ve read interesting articles about the domestication of bees and poor practices of modern beekeepers, but it seems clear that we can’t discount what others see as the number one culprit – the overuse of chemicals by gardeners. Interviewer: So what do you suggest gardeners do, Roy? Roy: Well, the best thing anyone lucky enough to have a garden can do is provide a ‘bee friendly’ area. And the good news is bees prefer ‘lazy’ gardeners, which I suspect is most of us. A wild garden providing a natural habitat is the way forward. Choose what you plant carefully. It doesn’t have to be hard work but it could make a big difference! And buy your honey from local suppliers you know and trust.',
     "qs": [
         ('What has Roy noticed about bees?',
          ['Honey bees have almost disappeared.', 'Bumble bees have declined sharply.', 'Wasps have increased in number.'],
          0),
         ('What does Roy advise gardeners to do?',
          ['leave part of the garden wild', 'keep their own bees', 'use different chemicals'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 10, Extract 1 ---
    {"no": 10, "idx": 1,
     "say": 'Girl: Hi Tom, so what d’you think of the concert? Tom: Well, I’m not complaining because at the end of the day, I had a pretty good night out. But it’s just as well that we got a hefty student discount on the tickets. I went with high hopes of seeing something really spectacular from the headline band, and it just didn’t happen. I reckon I was taken in by all the hype; you know, the big build-up in the media and everything. I should know better than to take any notice of it, but you just get swept up by it, don’t you? Girl: Well, you may but I don’t. I hadn’t actually read or heard much about the gig at all, so I didn’t go with any preconceptions. If you ask me, you’re being rather hard on the main band. I mean, they were way better than the support act. If the idea was to get us in the mood for what was coming later, then I think they should’ve been presenting us with something a bit more exciting. Tom: Well, who knows? Perhaps they were chosen because they wouldn’t upstage the stars.',
     "qs": [
         ('Why was Tom disappointed by the concert?',
          ['He had believed the publicity.', 'The tickets were too expensive.', 'The support act played for too long.'],
          0),
         ('What does the girl think about the support act?',
          ['It should have been more exciting.', 'It was better than the headline band.', 'It was very well chosen.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 10, Extract 2 ---
    {"no": 10, "idx": 2,
     "say": 'Gary: There’s been lots of speculation in the press this week surrounding the fate of United manager Tony Benson, with some people calling for his resignation after a run of poor results. Talking to people at the club this week, I sense that there may actually be little substance to stories that his job’s on the line. Indeed, a number of people I spoke to were keen to defend his record, feeling that he was focussing the players on a more stylish, entertaining brand of football. They thought it would only be a matter of time before we begin to see this reflected in the results. What’s your take on all this, Suzie? Suzie: Well Gary, the club’s invested in promising players. The potential’s there, it’s just a question of whether Benson’s the man to pull it all together and make it work; and time’s running out for him. I’ve been talking to some of the players and I’d say there was a groundswell of support in the dressing room for Benson’s general approach. But I think the results speak for themselves and, these days, if a top- flight football team isn’t getting points, then something’s got to change and that comes back to the manager because that’s his responsibility – getting the results.',
     "qs": [
         ('What has Gary concluded from talking to people at the club?',
          ["Benson's job is probably not in danger.", 'The players want a new manager.', 'The results will not improve.'],
          0),
         ("What is Suzie's view?",
          ['The results matter more than the support he has.', 'Benson has no support in the dressing room.', 'The club has not invested enough.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 10, Extract 3 ---
    {"no": 10, "idx": 3,
     "say": 'Man: So what did you think of it? Woman: I could stand and look at his work all day long. I know it’s a strange thing to say about sculpture, but it really makes you think, you know, about more than just the art – about aspects of life itself . Man: But this was a strange exhibition. They seemed to have gone for quite an eclectic selection . Was it meant to be representative of something? I never read the notes they hand out because I prefer to come to my own interpretation. Woman: Yes, so do I. Actually, I think the unifying theme was the material. I mean, all these pieces were made out of the same three raw materials – wire, glass and straw. Not all his work is, of course, but I guess it’s a phase he went through; part of his development as an artist. I’d have been happy to have seen some of his other stuff actually. Man: Yeah, more of a range. Well you can’t fault the museum, can you? I mean, any exhibition they put on is worth going to. It’s such a brilliant space and you never know how things are going to look because the presentation’s so imaginative, isn’t it? Woman: There’s nowhere quite like it really.',
     "qs": [
         ("What did the woman like about the sculptor's work?",
          ['It made her think about life itself.', 'It used very unusual materials.', 'It was arranged very clearly.'],
          0),
         ('What do the two speakers agree about?',
          ['They prefer to interpret the work themselves.', 'The selection was far too narrow.', 'The museum building is badly designed.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 11, Extract 1 ---
    {"no": 11, "idx": 1,
     "say": 'Interviewer: Charles, you’re retired now, but you actually designed some household products, and all of them as an employee of a company. Did it ever frustrate you that you were making products without your name on? Charles: It was standard practice. Besides, I needed a weekly pay check before I needed recognition. Nowadays, you can find designers’ names on products, but it tends to be high-profile people seeking attention. And then there’s celebrity endorsement and all that. People think that if they buy a soccer ball that has the name of some famous player on it, they’re going to score wonderful goals… a ploy to get you to buy products. Interviewer: What advice do you have for young designers? Charles: What they do will affect so many people during the lifetime of that product. That’s serious stuff. So the product should do what it’s supposed to do and be pleasing to have in your environment. I tried to make things appear as if they just belong. They don’t need to scream. I don’t think a nutcracker needs to look like an elephant.',
     "qs": [
         ('How did Charles feel about not having his name on products?',
          ['He accepted it as normal practice.', 'It frustrated him for years.', 'He asked the company to change it.'],
          0),
         ('What does Charles say about celebrity names on products?',
          ['They are used to persuade people to buy.', 'They guarantee better quality.', 'They help young designers.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 11, Extract 2 ---
    {"no": 11, "idx": 2,
     "say": 'Man: Well, what a one-sided interview that was – and with one of my favourite actresses. She hardly got a look-in! Noone would’ve learned anything new about her, especially as it was the usual, tired stuff being put to her. When she did try to steer things in a different direction, the interviewer just ignored her and kept going on about himself. Woman: There aren’t many really good interviewers, are there? The best ones really take on board what’s being said and follow it up. This guy showed no imagination at all, just covering old ground, and targeting obvious stuff. No wonder he couldn’t get interesting responses. Man: And Celia could’ve told a few stories… she’s had a fascinating life. I know some film actors are perhaps a bit tricky – some seem afraid to be themselves, like they’re desperate to keep up their public image at all costs. And of course many actors are interviewed just after their last film’s been released, and are understandably keen to publicise it, but interviewers often concentrate on other superficial stuff. I love it when actors are challenged a bit, and the interviewer dares to deviate from the set script, putting them on the spot!',
     "qs": [
         ('What do both speakers criticise about the interviewer?',
          ['He asked nothing new.', 'He interrupted far too often.', 'He knew nothing about films.'],
          0),
         ('What does the man say about some film actors?',
          ['They are anxious to protect their public image.', 'They refuse to give interviews.', 'They talk only about their latest film.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 11, Extract 3 ---
    {"no": 11, "idx": 3,
     "say": 'Man: Hmm, I must get down to some work. Woman: Is getting started tricky for you? Man: Well, it can take me a while to enter into a creative state, but once I’m there, I lose awareness of absolutely anything but the ideas flowing – don’t even perceive my fingers typing. Woman: Really? Man: Hm, and I’m then extremely resistant to interruption, so I’ll shout at anyone who knocks at my study door. My defensive reactions are subconscious, though, and usually I don’t even recall them. The family’s used to it and I’m certainly not upholding it as a model of good behaviour, but sometimes it’s necessary. Woman: Yeah, once I’m immersed in creating something, I usually maintain that state until I complete the work. And I don’t even feel as if I am working. But if I look at the task ahead of me, all I tend to see is the effort involved! Man: Right. And what about stuff you wrote ages back? Do you return to it for inspiration? Woman: Well, I find I can’t always recreate the mindset I had during its creation, because inevitably I’ve since broadened my perspective on it. I can see why I used the inspiration I did, but obviously experience changes you. Man: Yes… absolutely.',
     "qs": [
         ('What does the man admit about his working habits?',
          ['He reacts badly to being interrupted.', 'He finds it impossible to start.', 'He works better with company.'],
          0),
         ('What does the woman say about her own work?',
          ['She keeps going until it is finished.', 'She takes frequent breaks.', 'She always enjoys planning it.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 12, Extract 1 ---
    {"no": 12, "idx": 1,
     "say": 'Man: You know, I think privacy as we used to understand it is a thing of the past. Woman: Why do you say that? Not another scare story in the papers? They’re always full of fanciful tales of doom and gloom… Man: You may laugh, but after what happened yesterday… Woman: What did happen? Man: I was discussing the whole issue with an uncle of mine, who’s just turned . He proudly informed me there couldn’t be any data relating to him on the internet because he’d never used a computer. Woman: Well fair enough, surely? Man: Well, I only spent a couple of minutes searching and was still able to come up with quite a bit of stuff about him Woman: Really? That’s a bit worrying. I bet he was taken aback, wasn’t he? Man: He was stunned… speechless – asked me to remove it all from ‘cyberspace’. But it doesn’t work like that, of course. What’s there, is there. Woman: That does seem an erosion of privacy. Mind you, come to think of it, I suppose there’s also been some information available on us all for a while, way before the days of the internet. Man: But it wasn’t so easy to get at. And the situation’s not going to improve. Woman: No… I guess not. Quite the opposite.',
     "qs": [
         ("What surprised the man's uncle?",
          ['how much about him was online', 'how easy computers are to use', 'how quickly data can be removed'],
          0),
         ('What does the man say about removing the information?',
          ['It cannot really be done.', 'It takes a very long time.', 'It has to be paid for.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 12, Extract 2 ---
    {"no": 12, "idx": 2,
     "say": 'Woman: Did you know that over seven million tonnes of food is thrown away every year in the UK? Man: Really? That’s one big garbage mountain. Woman: Yeah – and it costs huge amounts to collect, not to mention clogging landfills and producing vast amounts of C emissions. Man: There’s not much we can do about it though, is there? Woman: Well actually, restaurants are some of the worst offenders. That’s why we adopted responsible practices in our kitchen a while back. We’ve only got one garbage bin now despite having seats, but two compost machines for food waste. Man: Oh come on! We’ve got four or five bins and only seats at our place. Woman: Look, anything is possible. Our place is unrecognisable from what it was like last year, as is my boss – can’t think what’s got into him! Thinking ahead for a change! Man: Hmmm. OK – maybe I’d better talk to my head chef. Might be fighting an uphill battle though. Woman: There’re other things you can do too – my chef’s obsessive about portion control, keeping an eye on how much food customers leave, and altering dishes accordingly. Man: Don’t you get complaints about small servings? Woman: Granted, we don’t do enormous portions – but if occasionally someone wants a little bit more, we’ll give it to them. It works – honest! Man: Don’t suppose we’d go far down that road.',
     "qs": [
         ("What has the woman's restaurant done?",
          ['reduced its bins and added composting', 'reduced the number of seats', 'stopped serving certain dishes'],
          0),
         ('How does the man react?',
          ['He will discuss it with his chef.', 'He thinks it is impossible.', 'He has already done the same.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 12, Extract 3 ---
    {"no": 12, "idx": 3,
     "say": 'Man: Do you know anything about that experiment the lecturer was referring to? Woman: I’ve looked it up – it involved this Frenchman spending two months in a cave under a glacier – in 2 I think it was. He was m below ground, and because he had nothing to track the time – no clock obviously, no sun either – he got disorientated. When he came back up, he thought he’d been down there for just days. Very revealing for the researchers, who’d anticipated it would go the other way. Various stuntmen and entertainers have done similar things to push themselves to extremes – but then of course they’ve always got an eye on the headlines they’ll create. Man: That’s fascinating. Woman: Yes, it’s all about temporal landmarks – they’re really important. If you build more of them into your life, you’ll experience time differently. Days and years won’t be one undifferentiated mush. Temporal landmarks help stop the feeling that time’s whizzing by. I bet, for example, you retain memories of events that happen near the beginning or end of term – they’re kind of landmarks – better than those that happened somewhere in between. Man: So? Woman: So establish a few landmarks – remember to mark special events like birthdays properly with some sort of celebration. Man: That advice I’m happy to follow.',
     "qs": [
         ('What surprised the researchers?',
          ['The man underestimated the time he had spent.', 'He stayed longer than he had planned.', 'He kept an accurate record of the days.'],
          0),
         ('What does the woman say about temporal landmarks?',
          ['They change how we experience time.', 'They are only useful to scientists.', 'They make the days seem shorter.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 13, Extract 1 ---
    {"no": 13, "idx": 1,
     "say": 'Man: How are you finding the teaching course, Susanna? You seem to have been making good progress so far. Woman: Yeah, I’m feeling more confident in front of my students. But I worry about whether they’re inspired by the activities I do with them sometimes. I guess this is a wake-up call for me – that it’s just too much to expect them to be as excited about Maths as I am. Man: I think when a teacher’s motivated, that can’t fail to make an impression. You can’t expect your students to love a subject unless they can see you love it yourself. Sure, your students will think you’re crazy if you talk about Maths as if it were a spectator sport, but in the end your attitude will rub off on them. Woman: I was reading about some techniques I could try in the classroom to keep their interest levels up. I’ve been trying to get some more hands-on stuff into my classes – you know trying things out in a practical sense rather than sticking to boring theory. Man: Sounds like an excellent idea. Students always appreciate a teacher who goes the extra mile for them.',
     "qs": [
         ('What is Susanna worried about?',
          ['whether her students find her lessons inspiring', 'whether she knows enough maths', 'whether she can control the class'],
          0),
         ("What does the man say about a teacher's attitude?",
          ['It rubs off on the students.', 'It matters less than the material.', 'It should be hidden from students.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 13, Extract 2 ---
    {"no": 13, "idx": 2,
     "say": 'Sam: So you decided against the concert then? Ella: I thought about it, but I don’t really think it’s possible to get caught up in the atmosphere when all you see is someone pressing buttons on a computer and tinkling the keys on a synthesiser. That’s all this electronic music amounts to. Sam: Admittedly the performer was dressed all in black and she looked like a scene shifter. And the visuals were limited – there was a screen, but just with some sober animations on it – trees, castles, rippling water – that sort of thing. Ella: That says it all. Sam: But does that matter, if the music’s brilliant? And it certainly was. But that’s just my opinion. Ella: Tell me something about her then. Sam: Well – she’s a student – studying comparative literature I think. That seems to give a bit of substance to her music, make it thoughtful and rigorous. Ella: Sounds overly serious! Sam: Well, it all paid off. When the audience got more lively towards the end, she kept it steady and didn’t change pace to build excitement. And she didn’t seem to need the pyrotechnics and lasers that so many techies rely on.',
     "qs": [
         ('Why did Ella decide not to go to the concert?',
          ['She thought there would be no atmosphere.', 'The tickets were far too expensive.', 'She dislikes the performer.'],
          0),
         ('What does Sam say about the performer?',
          ['Her studies give her music substance.', 'Her clothes spoiled the show.', 'The visuals were the best part.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 13, Extract 3 ---
    {"no": 13, "idx": 3,
     "say": 'Man: I heard that people from your office were planting trees last week. What’s going on? Woman: Sustainability’s the new watchword these days. Last year we concentrated on cutting down on our use of paper, and providing raw material for more also seemed a good thing to do. Man: And easier too – your office is next door to a big forest, isn’t it? Woman: Yes – very convenient. We’re really keen on the idea that the company should be seen to identify with a certain set of values – and I think we were doing just that out there in the woods. So much internal conflict seemed forgotten too – which may not last, of course! Man: What else have you done? Woman: It’s not just the trees of course – we’ve cut down our carbon footprint and reduced staff travel by encouraging remote working and flexible home working, so people have been understandably pleased about that. And word seems to have got round because the last bunch of job applicants were a very noticeably higher calibre than previously- and I’m pretty sure that wasn’t just a coincidence, though it wasn’t part of our original thinking. There are certainly plenty of happy clients, but they’ve always been keen on the idea of supporting community projects through our efforts!',
     "qs": [
         ('Why did the office plant trees?',
          ['to provide raw material for the paper they use', 'because the forest needed help', 'because a customer asked them to'],
          0),
         ('What extra benefit has the woman noticed?',
          ['better job applicants', 'lower rent', 'shorter working hours'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 14, Extract 1 ---
    {"no": 14, "idx": 1,
     "say": 'Woman: You’ve read this new book on competitiveness. Is it all about striving for success, or a defence of the Olympic ideal? You know – taking part is more important than winning. Man: Well, yes, that’s a view often ridiculed certainly, as some sort of excuse for underachievement. I mean if you run a race, surely it’s because you want to win, and we’ve all got used to the belief that competition is a necessary force for good in the modern world. It’s a deeply ingrained idea. It was a bit of a shock to read that competition impoverishes people rather than enriching them. There’s the mind- boggling range of convincing examples you’d expect in support of this theory, and the whole thing is so engagingly written that the most hostile opponents would have trouble refuting it. Woman: Well my experience of competition in the business world is nothing but negative. I’d say that if you put competition at the heart of your strategy, far from achieving the desired outcome of boosting efficiency by pitting staff against each other, the effect is rather to encourage people to focus exclusively on immediate success… not on sustained growth . Let’s face it, the best businesses are the ones that look ahead instead of limiting their perspective in this way.',
     "qs": [
         ('What surprised the man about the book?',
          ['its claim that competition harms people', 'how badly written it is', 'how few examples it gives'],
          0),
         ("What is the woman's view of competition in business?",
          ['It is entirely negative.', 'It is necessary but limited.', 'It is useful only for large firms.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 14, Extract 2 ---
    {"no": 14, "idx": 2,
     "say": 'Woman: You know how colours affect us, like red and yellow are often used in fast food restaurants… in the decor I mean. Man: Yeah, yeah – they say they excite the brain, which tells you you’re hungry – that was in the papers years back. Woman: Well, OK, but now there’s a suggestion colours may help us memorise better. Man: Oh, come on. Influence appetites and emotions, maybe, but… Woman: No, really – this teenager did some research. Man: Teenager? Woman: Yeah I know- but it does seem sound. She took a page of words and printed them in so-called ‘warm colours’… Man: How do you mean? Woman: Well, reds, oranges, yellows, etc. – and gave people two minutes to memorise the words. She followed that with pretty complicated maths equations to stop them reciting the words in their head. Man: Hmm… OK, sounds good so far… Woman: And they were given a minute to record how many words they could remember. And then the same procedure with words printed in cool colours like green and blue. Man: And? Woman: Overall warm colours were memorised better and cool colours worse. Man: She’s followed a thorough process, then. But is there any existing published data that backs up or contradicts these claims? Woman: Well, not as such, I grant you. Though it sounds like she’s onto something to me. But only time will tell.',
     "qs": [
         ("What was the man's first reaction to the idea?",
          ['He did not believe it.', 'He had read about it before.', 'He thought it was obvious.'],
          0),
         ('Why did the researcher use maths equations?',
          ['to stop people repeating the words in their head', 'to test how intelligent they were', 'to give them a short rest'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 14, Extract 3 ---
    {"no": 14, "idx": 3,
     "say": 'Woman: I watched ‘How Musical are you?’ on TV last night – they were saying how listening to music is a really complicated process. The scientists were really going to town on it! Man: I thought so-called musicality meant being able to play a musical instrument, but that seemed to be just one aspect of the whole programme. It’s odd, people who’ve never set foot inside a music classroom might still have a musical ‘ear’ without realising it! Woman: You mean, everyone has an innate ability to make sense of music? I’m not sure but it brings an enormous amount of pleasure.I really don’t know how, but it changes my mood when I’m down – which never ceases to amaze me! But they missed a trick in not clarifying why some people are avid listeners to music and others not. Man: They seemed more interested in the possible effect of music on musicians’ brains. I didn’t know that people who’ve had music training in childhood find long-term positive effects on their verbal memory- who’d have thought it. Woman: I don’t remember words whatever I do! You know that online quiz they mentioned – that might be worth a go. It’s about how engaged you are with music, you know, whether it’s part of your identity or not. Man: So you might be more musical than you think!',
     "qs": [
         ('What did the man learn from the programme?',
          ['Playing an instrument is only part of musicality.', 'Anyone can learn to play an instrument.', 'Musicians have larger brains.'],
          0),
         ('What did the woman think was missing?',
          ['an explanation of why some people love music and others do not', 'examples from famous musicians', 'advice on learning an instrument'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 15, Extract 1 ---
    {"no": 15, "idx": 1,
     "say": 'Woman: I dread the experience. It’s the anticipation that gets me. Once I start I’m usually OK but beforehand I panic. I think that my mind will go blank and everyone will stare at me. This happened once. I was trying to speak and listen to my own voice at the same time but all I could hear was silence. I seemed to have forgotten how to speak and I felt my face go red. I fumbled for my notes and simply read out the rest of the speech. Man: Well, fear of public speaking, or what is called ‘representational anxiety’, is normal. If you think about it, public speaking is not a natural thing to do. You don’t want to humiliate yourself in front of people. But with preparation and practice, even the most stressed public speakers can conquer their fears. There are very few people who are quick, intelligent and extrovert enough to just get up and deliver something spontaneously. If you’re giving a speech, you must carefully plan what you’re going to say. Woman: I find it also helps not to think of yourself the whole time. Once you shift the focus on to the people you are speaking to, you feel the pressure lift.',
     "qs": [
         ('What happened to the woman on one occasion?',
          ['She forgot how to speak and read out her notes.', 'She fainted in front of the audience.', 'She refused to go on stage at all.'],
          0),
         ('What does the man say about most speakers?',
          ['Very few can speak well without preparing.', 'Most people never overcome the fear.', 'Practice makes very little difference.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 15, Extract 2 ---
    {"no": 15, "idx": 2,
     "say": 'Man: As part of a huge publicity drive in the 0s and 0s, London Transport launched a poster campaign to persuade people to move into the suburbs and make use of the rapidly expanding Underground network. Tell us about that, Zoe. Woman: Well, the posters were used to encourage people to live in and enjoy the quiet and domestic life of the suburbs and travel into London for work and leisure. They helped to shape people’s perceptions and expectations of London and what it meant to live there in a period of great change. As well as persuading people to move out to the suburbs, there was a drive for people to make use of the city at a time when the leisure industry was expanding. Man: What kind of things did these posters show? Woman: Well, despite the fact that many women worked in the 0s and 0s, the posters depicted a domestic ideal, with pictures of women playing with their children in the park and preparing meals for their husbands’ return. More and more people were becoming middle class and part of this ideal was that the husband would go to work and the wife would stay at home, even though this was not the case for many families.',
     "qs": [
         ('What was the purpose of the posters?',
          ['to persuade people to move to the suburbs', 'to advertise new Underground stations', 'to reduce traffic in the city centre'],
          0),
         ('What does the woman say about the women in the posters?',
          ['They were shown at home although many worked.', 'They were shown travelling to work.', 'They were hardly shown at all.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 15, Extract 3 ---
    {"no": 15, "idx": 3,
     "say": 'Man: Of course, the cliche is ‘don’t believe everything you read in the papers’, and I guess there’s some truth in that. But in many ways that’s not backed up by the evidence. Look at all the times when stories would never have come out if it hadn’t been for the much maligned news media. Woman: I don’t know about that. Personally I’m always pretty sceptical when it comes to all these revelations. I mean, look at medical stories. It sometimes seems as if every day brings some new health scare – you mustn’t eat that, you should drink that – and most of these things you never hear about again. I think it’d be really interesting to find out how many of these stories actually turn out to be true. I reckon they just write these things to create a stir. I mean, lots of them are in the entertainment industry really, aren’t they? ‘Don’t let the facts get in the way of a good story’ is the joke in the trade isn’t it? I think lots of them live by that. Man: I don’t think that’s really fair. There are lots of investigative journalists who’ve done the public a great service by exposing things they otherwise would never have known about.',
     "qs": [
         ("What is the man's view of the news media?",
          ['Some stories would never appear without them.', 'They cannot be trusted at all.', 'They should be controlled more strictly.'],
          0),
         ('What does the woman say about health stories?',
          ['Most of them are never mentioned again.', 'They are usually proved correct.', 'They are written by doctors.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 16, Extract 1 ---
    {"no": 16, "idx": 1,
     "say": 'Jane: Well that was certainly original. I’ve seen quite a few of his plays and that one was completely different to the others. Bill: Yes, it was quite dark, wasn’t it? Maybe it’s because he’d become aware of his own mortality when he wrote it. Jane: That’s right. He’d been seriously ill, hadn’t he? Bill: Apparently it was touch and go for a while. Jane: Mind you, the main character was hilarious, in a sick kind of way. I think that kind of humour would go right over most people’s heads. Bill: Well, I don’t know how he’ll follow up that story. He really seems to be a different character to when he first started to write.',
     "qs": [
         ('What do the speakers say about this play?',
          ["It is different from the writer's other work.", 'It is his funniest play so far.', 'It repeats his earlier themes.'],
          0),
         ('What does Jane say about the humour?',
          ['Most people would not understand it.', 'It was the weakest part of the play.', 'It made the play far too light.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 16, Extract 2 ---
    {"no": 16, "idx": 2,
     "say": 'Interviewer: The old mantra about the three most important factors for a shop’s success – location, location, location – has been borne out by a new mathematical model. It could help retailers pinpoint lucrative sites for their stores. Physicist Pablo Jenson is here with us today. Good morning Pablo. Pablo: Good morning. We have analysed location records for more than 0 retail outlets in Lyon, France. We found that the shops formed clusters, with shops such as butchers and delicatessens in one group, for example, and laundromats and bookstores in another. Stores of the same group seemed to attract each other, while stores from different groups repelled each other. Interviewer: You’ve created a theory haven’t you? Pablo: Yes, that’s right. It’s a theory of magnetism to calculate a number, ‘Q’ for shops, based on the proximity of attractive and repellent businesses in the area. ‘Q’ represents the suitability of a site for a particular type of shop: the higher the number, the better the site. We tested this theory with all of the bakeries in Lyon between 3 and 5. During that period, bakeries shut down and their average ‘Q’ was lower than the average for all bakeries. Actually, the Lyon Chamber of Commerce is using the model to help entrepreneurs identify promising new premises',
     "qs": [
         ("What did Pablo's team find?",
          ['Similar shops group together.', 'Shops do best when they stand alone.', 'Location matters less than price.'],
          0),
         ("What is the number 'Q' used for?",
          ['judging how suitable a site is', "measuring a shop's profits", 'counting the customers'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 16, Extract 3 ---
    {"no": 16, "idx": 3,
     "say": 'Speaker: For a beautiful alternative to the bigger Spanish coasts, try the Costa de la Cruz, ‘the coast of light’. The government of Andalucia is taking care to protect this little known region, which has earned the nickname, ‘the Spanish Algarve’ thanks to its charm and proximity to the Portuguese border. A property in the area represents a sound investment because homes are cheaper than their Portuguese equivalents, and land laws mean that it will never become so built up that it is spoiled. National parks, farmland and beautiful beaches all abound, and Chris Mercer of spanishproperty.co.uk says that more homes will be built soon. ‘More land will have to be made available for development soon because demand is quite simply starting to outstrip supply’, he says. ‘The government is being careful to preserve the natural beauty and character though, so your investment should stay strong.’',
     "qs": [
         ('Why is property there described as a good investment?',
          ['It is cheaper than in Portugal.', 'The government pays for building.', 'There is very little demand yet.'],
          0),
         ('What does Chris Mercer expect?',
          ['More land will be released for building.', 'Prices will soon start to fall.', 'The area will become overbuilt.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 17, Extract 1 ---
    {"no": 17, "idx": 1,
     "say": 'Man: One of my colleagues is always complaining about his job, or moaning about our boss, or the company’s management. It’s making other team members dissatisfied because some of his complaints are true and it’s created a very negative atmosphere. I’ve tried to speak to him about it, but now he just thinks I’m trying to be the boss’ favourite. Woman: Well, I’m not trying to question your analysis of the problem or your motives for trying to sort it out, but I do suspect you’ve gone about trying to solve it in a way that casts you, however unjustly, as a bit of a self-important bore. Why don’t two or three of you put your complaints to your boss in a fair and constructive way? And, it might be a good idea to involve your unhappy colleague in that.',
     "qs": [
         ("What is the man's problem?",
          ["A colleague's complaints are affecting the team.", 'His boss has criticised him unfairly.', 'He has been given far too much work.'],
          0),
         ('What does the woman advise him to do?',
          ['complain as a group, including the colleague', 'ignore the colleague completely', 'ask to be moved to another team'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 17, Extract 2 ---
    {"no": 17, "idx": 2,
     "say": 'Janet: I’m glad you persuaded me to go to the recruitment fair. It was nothing like I thought it would be. Paul: Yes, it was really interesting. Janet: I was quite sure that I would become a translator before I went to the fair because I was just about to finish my degree in modern languages. I wandered up to a stall that was promoting careers in Public Relations, just to have a nose really. I was blown away. It seemed perfect to suit my skills and interests. Paul: Well, I’d been looking for a job in the papers and in employment agencies and I didn’t find anything at the fair, but one of the employees I spoke to there passed on my CV to the marketing and business development manager and a week later I was invited for an interview. I couldn’t believe my luck when they offered me the position.',
     "qs": [
         ('What happened to Janet at the fair?',
          ['She changed her mind about her career.', 'She was offered a job as a translator.', 'She decided to finish her degree first.'],
          0),
         ('How did Paul get his job?',
          ['Someone at the fair passed on his CV.', 'He answered a newspaper advertisement.', 'He applied through an employment agency.'],
          0),
     ]},
    # --- audioskript Part 5, EXERCISE 17, Extract 3 ---
    {"no": 17, "idx": 3,
     "say": 'Man: It’s not just a job for men you know and it’s a career where you can achieve promotion very quickly. Woman: What’s the salary like? Man: Typically, graduates who join can expect to earn? , within a year and achieve two promotions within the first two years. Of course, you can join up straight from school but it will take you longer to get to a higher position such as management. Woman: To be honest, I didn’t think I could ever do your job. You’ve got to be out of your mind to want to work with dangerous people like that, plus I wouldn’t have the courage to face violent criminals. You never know what they are going to do next. Man: Well, I just wanted to be sure of a career where I could do well without having to wait until I was a lot older.',
     "qs": [
         ('What does the man say about promotion?',
          ['It comes faster for graduates.', 'It depends mainly on your age.', 'It is very rare in the first two years.'],
          0),
         ('Why would the woman not want his job?',
          ['She would be too frightened.', 'The salary is too low.', 'It takes too long to be promoted.'],
          0),
     ]},
]


def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase).

    JAVOB O'RNI AYLANTIRILADI — manbada to'g'ri javob deyarli
    hamma joyda birinchi turadi (yozishga qulay bo'lsin uchun).
    Shundayligicha qoldirilsa, bola tinglamasdan A deb 100%
    olardi."""
    out = []
    n = 0
    for e, x in enumerate(EXTRACTS):
        step = 1 + e // 11          # 1..5
        for qi, (q, opts, ci) in enumerate(x["qs"], 1):
            shift = (n % 3 - ci) % 3
            n += 1
            new = [None] * 3
            for k, t in enumerate(opts):
                new[(k + shift) % 3] = t
            ci2 = (ci + shift) % 3
            labelled = [f"{LET[k]}. {t}" for k, t in enumerate(new)]
            expl = (f"To'g'ri javob: {labelled[ci2]}  "
                    f"(audioskript Part 5, {x['no']}-mashq, "
                    f"{x['idx']}-parcha, {qi}-savol).")
            out.append((
                KIND, step,
                {"say": x["say"],
                 "rate": RATE,
                 "options": labelled,
                 "prompt": f"Extract {x['idx']} — {q}",
                 "step": step,
                 "order": x["no"] * 100 + x["idx"] * 10 + qi,
                 "hint": "Uchta parcha, har biriga ikkita savol",
                 # Parcha uzun — ketma-ket ikki marta o'qilsa
                 # javob berishga vaqt qolmaydi. Ikkinchi marta
                 # eshitishni o'quvchi o'zi boshlaydi.
                 "plays": 1,
                 "gap_ms": 1500},
                labelled[ci2], expl, None, None))
    return out


def seed_extract(db):
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
