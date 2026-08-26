# -*- coding: utf-8 -*-
"""MULTILEVEL SPEAKING — SAVOLLAR BANKI (2026-08-26).

Jahongir: "har bir bo'limga alohida tayyorlanishi sample savollar
ko'p bo'lishi va unga javob berish uchun templatelar, samplelar
bo'lsin."

RASMLAR HAQIDA — OCHIQ AYTAMAN. 1.2 va 2-qismda haqiqiy fotosurat
ko'rsatiladi. Menda rasm chizish imkoni yo'q, shuning uchun har
rasm SO'Z BILAN batafsil tasvirlangan ("scene"). O'quvchi baribir
taqqoslash tilini mashq qila oladi.

Har savolda bo'sh `img` maydoni bor: keyin haqiqiy rasm manzili
yozilsa, ekran o'zi rasmga o'tadi va kod o'zgarmaydi. Ya'ni bugun
ishlaydi, ertaga rasm qo'shilsa yanada yaxshi bo'ladi.
"""

# =================================================================
#  PART 1.1 — A1-A2, uchta shaxsiy savol, har biriga 30 soniya
#  Manba namunasi (speaking_format.pdf, 2-bet):
#    Please tell me about your best friend.
#    Tell me about your country.
#    What do you like to do in your free time?
# =================================================================

P11: list[dict] = [
    {"topic": "Do'stlar va oila", "q": [
        "Please tell me about your best friend.",
        "Tell me about your family.",
        "What do you usually do together at the weekend?"]},
    {"topic": "Mamlakat va shahar", "q": [
        "Tell me about your country.",
        "What is your home town like?",
        "What would you show a visitor in your city?"]},
    {"topic": "Bo'sh vaqt", "q": [
        "What do you like to do in your free time?",
        "How much free time do you have during the week?",
        "Is there a hobby you would like to try?"]},
    {"topic": "Ish va o'qish", "q": [
        "Are you a student or do you work?",
        "What subject do you find most interesting?",
        "What do you want to do in the future?"]},
    {"topic": "Kundalik tartib", "q": [
        "What time do you usually get up?",
        "Describe a typical weekday for you.",
        "What is your favourite part of the day?"]},
    {"topic": "Ovqat", "q": [
        "What is your favourite food?",
        "Who cooks in your family?",
        "Do you prefer eating at home or in a cafe? Why?"]},
    {"topic": "Sport", "q": [
        "Do you play any sport?",
        "What sport is popular in your country?",
        "How often do you exercise?"]},
    {"topic": "Musiqa", "q": [
        "What kind of music do you like?",
        "When do you usually listen to music?",
        "Have you ever been to a concert?"]},
    {"topic": "Sayohat", "q": [
        "Do you like travelling?",
        "Tell me about a place you have visited.",
        "Where would you like to go next?"]},
    {"topic": "Ob-havo va fasllar", "q": [
        "What is the weather like in your city today?",
        "Which season do you like best? Why?",
        "What do you do on a rainy day?"]},
    {"topic": "Telefon va internet", "q": [
        "How often do you use your phone?",
        "What do you use the internet for?",
        "Do you think you spend too much time online?"]},
    {"topic": "Uy", "q": [
        "Tell me about the place where you live.",
        "What is your favourite room? Why?",
        "Would you like to change anything about your home?"]},
    {"topic": "Do'kon va xarid", "q": [
        "Do you enjoy shopping?",
        "Where do you usually buy your clothes?",
        "Do you prefer shopping online or in shops? Why?"]},
    {"topic": "Kitoblar", "q": [
        "Do you like reading?",
        "What was the last book you read?",
        "Where do you like to read?"]},
    {"topic": "Kino va seriallar", "q": [
        "What kind of films do you enjoy?",
        "Tell me about a film you liked.",
        "Do you prefer watching films at home or at the cinema?"]},
    {"topic": "Bayramlar", "q": [
        "What is your favourite holiday?",
        "How do people celebrate it in your country?",
        "What did you do last Navruz?"]},
    {"topic": "Transport", "q": [
        "How do you usually travel around your city?",
        "Is public transport good where you live?",
        "Can you drive? Would you like to?"]},
    {"topic": "Ranglar va kiyim", "q": [
        "What is your favourite colour?",
        "What kind of clothes do you usually wear?",
        "Do you follow fashion?"]},
    {"topic": "Hayvonlar", "q": [
        "Do you have a pet?",
        "What is your favourite animal? Why?",
        "Do many people keep pets in your country?"]},
    {"topic": "Do'st tanlash", "q": [
        "How did you meet your best friend?",
        "What makes someone a good friend?",
        "Do you prefer a large group of friends or a few close ones?"]},
    {"topic": "Til o'rganish", "q": [
        "How long have you been learning English?",
        "Why is English important for you?",
        "What is the most difficult part of learning a language?"]},
    {"topic": "Maktab xotiralari", "q": [
        "Tell me about your school.",
        "Who was your favourite teacher? Why?",
        "What did you enjoy most at school?"]},
    {"topic": "Texnologiya", "q": [
        "What technology do you use every day?",
        "Which app do you use most often?",
        "Has technology changed the way you study?"]},
    {"topic": "Tabiat", "q": [
        "Do you like spending time outdoors?",
        "Is there a park near your home?",
        "What is the most beautiful place you have seen?"]},
    {"topic": "Uy ishlari", "q": [
        "Do you help with the housework?",
        "Which household job do you dislike most?",
        "Who does most of the cooking in your home?"]},
    {"topic": "Pul", "q": [
        "Do you save money?",
        "What did you last spend money on?",
        "Is it easy to save money for a student?"]},
    {"topic": "Salomatlik", "q": [
        "What do you do to stay healthy?",
        "How many hours do you sleep?",
        "Do you think your diet is healthy?"]},
    {"topic": "Fotosurat", "q": [
        "Do you like taking photographs?",
        "What do you usually take photos of?",
        "Tell me about a photo that is important to you."]},
    {"topic": "Ijtimoiy tarmoq", "q": [
        "Which social network do you use?",
        "What do you usually post?",
        "Do you think social media is useful?"]},
    {"topic": "Qo'shnilar", "q": [
        "Do you know your neighbours?",
        "Is your neighbourhood quiet or noisy?",
        "What do you like about the area where you live?"]},
    {"topic": "Ertalab va kechqurun", "q": [
        "Are you a morning person or an evening person?",
        "What is the first thing you do after waking up?",
        "How do you relax before going to bed?"]},
    {"topic": "Sovg'alar", "q": [
        "Do you like giving presents?",
        "What was the best present you have received?",
        "What present would you buy for your mother?"]},
    {"topic": "Restoran va kafe", "q": [
        "How often do you eat out?",
        "Tell me about a restaurant you like.",
        "What food would you recommend to a foreign visitor?"]},
    {"topic": "Ustozlar va o'qish", "q": [
        "How do you usually study for an exam?",
        "Do you prefer studying alone or with friends?",
        "Where do you study best?"]},
    {"topic": "Shahar hayoti", "q": [
        "What do you like about living in a city?",
        "Is your city changing? How?",
        "Would you prefer to live in a village? Why?"]},
    {"topic": "Ta'til rejalari", "q": [
        "What are you going to do this summer?",
        "Tell me about your last holiday.",
        "Do you prefer the mountains or the sea?"]},
    {"topic": "Ish tajribasi", "q": [
        "Have you ever had a part-time job?",
        "What kind of work would you enjoy?",
        "Is it easy for young people to find a job here?"]},
    {"topic": "Kompyuter o'yinlari", "q": [
        "Do you play computer games?",
        "How much time do you spend on them?",
        "Do you think games can be useful?"]},
    {"topic": "Ovqat pishirish", "q": [
        "Can you cook?",
        "What dish can you make well?",
        "Would you like to learn to cook better?"]},
    {"topic": "Kelajak", "q": [
        "Where do you see yourself in five years?",
        "What skill would you like to learn?",
        "What is your biggest goal at the moment?"]},
]

# =================================================================
#  PART 1.2 — B1, ikki rasm + 3 savol (45 / 30 / 30 soniya)
#  Manba namunasi (3-bet): walking vs driving.
# =================================================================

P12: list[dict] = [
    {"topic": "Yurish va mashina",
     "a": "A busy pavement where people of different ages are walking "
          "to work on a bright morning; a few are carrying bags and "
          "one woman is pushing a pram.",
     "b": "A wide road at rush hour, filled with cars moving slowly "
          "bumper to bumper; the drivers are alone in their cars.",
     "q": ["What do you see in these pictures?",
           "What are some advantages of walking over driving?",
           "Why do some people prefer having a car of their own?"]},
    {"topic": "Onlayn va sinfda o'qish",
     "a": "A student sitting alone at a kitchen table with a laptop, "
          "headphones on, following a lesson on the screen.",
     "b": "A classroom where a teacher stands at the board and "
          "fifteen students sit at desks, some raising their hands.",
     "q": ["What do you see in these pictures?",
           "What are the advantages of studying in a classroom?",
           "Why do some people choose online courses instead?"]},
    {"topic": "Uyda va restoranda ovqatlanish",
     "a": "A family of four eating a home-cooked meal around a small "
          "kitchen table, dishes shared in the middle.",
     "b": "A couple in a modern restaurant, a waiter placing plates "
          "in front of them, soft lighting around.",
     "q": ["What do you see in these pictures?",
           "What are the benefits of eating at home?",
           "Why do people enjoy eating in restaurants?"]},
    {"topic": "Shahar va qishloq",
     "a": "A city centre in the evening with tall buildings, bright "
          "signs, crowds of people and heavy traffic.",
     "b": "A quiet village with low houses, a dirt road, fields "
          "behind and an old man walking with a bicycle.",
     "q": ["What do you see in these pictures?",
           "What are the advantages of living in a city?",
           "Why do some people move to the countryside?"]},
    {"topic": "Kitob va telefon",
     "a": "A girl sitting by a window reading a thick paper book, "
          "sunlight falling on the pages.",
     "b": "A young man on a bus scrolling through his phone, several "
          "other passengers doing exactly the same.",
     "q": ["What do you see in these pictures?",
           "Why do some people still prefer paper books?",
           "What are the advantages of reading on a phone?"]},
    {"topic": "Jamoa va yakka sport",
     "a": "A football team celebrating together on a pitch, arms "
          "around each other's shoulders.",
     "b": "A single runner on an empty road at sunrise, wearing a "
          "sports watch.",
     "q": ["What do you see in these pictures?",
           "What can people learn from team sports?",
           "Why do some people prefer to exercise alone?"]},
    {"topic": "Onlayn va do'kondan xarid",
     "a": "A woman choosing fruit at an open market, holding it up "
          "to look at it closely.",
     "b": "A man at home clicking 'buy' on a laptop, several delivery "
          "boxes already stacked by the door.",
     "q": ["What do you see in these pictures?",
           "What are the advantages of shopping in real shops?",
           "Why has online shopping become so popular?"]},
    {"topic": "Ofis va uydan ishlash",
     "a": "An open-plan office where colleagues are discussing "
          "something around a desk with charts on the wall.",
     "b": "A man working from his sofa with a laptop on his knees "
          "while a child plays on the floor nearby.",
     "q": ["What do you see in these pictures?",
           "What are the benefits of working in an office?",
           "Why do many people want to work from home?"]},
    {"topic": "Jamoat transporti va velosiped",
     "a": "A crowded metro carriage where passengers stand close "
          "together holding the rails.",
     "b": "A cyclist riding along a marked cycle lane beside a park, "
          "wearing a helmet.",
     "q": ["What do you see in these pictures?",
           "What are the advantages of cycling in a city?",
           "Why do most people still use public transport?"]},
    {"topic": "Kutubxona va kafe",
     "a": "A silent library reading room with long tables, students "
          "bent over books and laptops.",
     "b": "A busy cafe where a student is studying with headphones "
          "on while others chat around her.",
     "q": ["What do you see in these pictures?",
           "Why do some students prefer studying in a library?",
           "What makes a cafe a good place to work?"]},
    {"topic": "Katta va kichik oila",
     "a": "A large family gathering, three generations sitting "
          "around one long table outdoors.",
     "b": "A young couple with one child having breakfast in a small "
          "bright flat.",
     "q": ["What do you see in these pictures?",
           "What are the advantages of growing up in a big family?",
           "Why do many young couples have fewer children today?"]},
    {"topic": "Qo'lda va texnika bilan mehnat",
     "a": "A craftsman shaping a wooden bowl by hand with simple "
          "tools, wood shavings on the floor.",
     "b": "A modern factory line where robot arms assemble parts and "
          "one worker watches a screen.",
     "q": ["What do you see in these pictures?",
           "Why do people still value handmade products?",
           "What are the advantages of using machines in production?"]},
    {"topic": "Yozgi va qishki dam olish",
     "a": "A crowded sunny beach with umbrellas, families swimming "
          "and children building sandcastles.",
     "b": "A snowy mountain slope with skiers and a wooden lodge "
          "with smoke rising from the chimney.",
     "q": ["What do you see in these pictures?",
           "What do people enjoy about a beach holiday?",
           "Why do some people choose winter holidays instead?"]},
    {"topic": "Yosh va keksa avlod",
     "a": "A grandmother teaching a young girl to make bread, both "
          "with flour on their hands.",
     "b": "A teenager showing an older man how to use a smartphone, "
          "both looking at the screen.",
     "q": ["What do you see in these pictures?",
           "What can young people learn from older generations?",
           "What can older people learn from the young?"]},
    {"topic": "Yolg'iz va guruh sayohati",
     "a": "A backpacker studying a map alone at a train station, "
          "rucksack on the ground.",
     "b": "A tour group following a guide with a raised umbrella "
          "past an old monument.",
     "q": ["What do you see in these pictures?",
           "What are the advantages of travelling alone?",
           "Why do many people book organised tours?"]},
    {"topic": "Ochiq havo va zalda sport",
     "a": "People doing morning exercises in a green park, trees "
          "around them.",
     "b": "A modern gym with running machines, mirrors and people "
          "training with weights.",
     "q": ["What do you see in these pictures?",
           "Why is exercising outdoors good for people?",
           "What are the advantages of going to a gym?"]},
    {"topic": "Naqd pul va karta",
     "a": "A customer handing banknotes to a seller at a small "
          "street stall.",
     "b": "A person paying by tapping a phone on a card reader in a "
          "modern shop.",
     "q": ["What do you see in these pictures?",
           "Why do some people still prefer to pay in cash?",
           "What are the advantages of paying by card or phone?"]},
    {"topic": "Uy hayvonlari va yovvoyi hayvonlar",
     "a": "A boy playing with a dog in a garden, throwing a ball.",
     "b": "A herd of wild horses running across an open steppe.",
     "q": ["What do you see in these pictures?",
           "Why do people keep pets?",
           "Why is it important to protect wild animals?"]},
    {"topic": "Qadimiy va zamonaviy binolar",
     "a": "An ancient madrasah with blue tiles and a carved wooden "
          "door, tourists taking photographs.",
     "b": "A glass office tower reflecting the sky, cars passing at "
          "its base.",
     "q": ["What do you see in these pictures?",
           "Why should old buildings be preserved?",
           "What are the advantages of modern architecture?"]},
    {"topic": "Bir kishilik va ko'p kishilik dars",
     "a": "A private lesson: one teacher and one student sitting "
          "opposite each other with a book between them.",
     "b": "A lecture hall with more than a hundred students facing "
          "a lecturer on a stage.",
     "q": ["What do you see in these pictures?",
           "What are the benefits of one-to-one lessons?",
           "Why do universities still use large lectures?"]},
    {"topic": "Qo'l bilan yozish va terish",
     "a": "A student writing notes by hand in a paper notebook, pen "
          "in hand.",
     "b": "A student typing quickly on a laptop during a lecture.",
     "q": ["What do you see in these pictures?",
           "What are the advantages of writing notes by hand?",
           "Why do many students prefer typing?"]},
    {"topic": "Bozor va supermarket",
     "a": "A colourful farmers' market with piles of fruit and "
          "sellers calling to customers.",
     "b": "A quiet supermarket aisle with packaged goods on long "
          "shelves and a customer with a trolley.",
     "q": ["What do you see in these pictures?",
           "Why do people enjoy shopping at markets?",
           "What are the advantages of supermarkets?"]},
    {"topic": "Erta va kech uxlash",
     "a": "A person waking up at sunrise, opening the curtains to a "
          "quiet street.",
     "b": "A person working at a desk late at night under a lamp, "
          "the rest of the room dark.",
     "q": ["What do you see in these pictures?",
           "What are the benefits of getting up early?",
           "Why do some people work better at night?"]},
    {"topic": "Ko'ngilli ish va maoshli ish",
     "a": "Volunteers in bright vests planting trees together in a "
          "park.",
     "b": "An employee in an office receiving a payslip from a "
          "manager.",
     "q": ["What do you see in these pictures?",
           "Why do people volunteer without being paid?",
           "What do people expect from paid work?"]},
]

# =================================================================
#  PART 2 — B2, bitta rasm + uchta savol, 1 daq tayyorgarlik,
#  2 daqiqa javob. Manba namunasi (4-bet): critical decision.
# =================================================================

P2: list[dict] = [
    {"topic": "Muhim qaror",
     "scene": "A person standing at a fork in a road, looking at two "
              "signposts pointing in different directions.",
     "q": ["Tell me about a critical decision you have made.",
           "How has this decision influenced you and your life?",
           "What factors have the highest impact on the decisions "
           "people make?"]},
    {"topic": "Muvaffaqiyat",
     "scene": "A young woman on a small stage receiving a certificate "
              "while an audience applauds.",
     "q": ["Tell me about an achievement you are proud of.",
           "What did you have to give up to achieve it?",
           "How do people in your country define success?"]},
    {"topic": "Xato va saboq",
     "scene": "A student looking at a test paper covered in red "
              "corrections.",
     "q": ["Tell me about a mistake that taught you something.",
           "How did you feel at the time and how do you feel now?",
           "Why are people often afraid of making mistakes?"]},
    {"topic": "O'zgarish",
     "scene": "A family carrying boxes into an empty flat, one child "
              "looking out of the window.",
     "q": ["Tell me about a big change in your life.",
           "How did you adapt to it?",
           "Why do some people find change more difficult than "
           "others?"]},
    {"topic": "Ta'sir ko'rsatgan inson",
     "scene": "An older teacher explaining something to a student, "
              "both leaning over an open book.",
     "q": ["Tell me about a person who has influenced you.",
           "What exactly did you learn from them?",
           "What qualities make someone a good role model?"]},
    {"topic": "Texnologiya va hayot",
     "scene": "Five people sitting on a bench, each looking at their "
              "own phone.",
     "q": ["How has technology changed your daily life?",
           "What do you think people have lost because of it?",
           "Will technology make people closer or more distant in "
           "the future?"]},
    {"topic": "Ish va shaxsiy hayot",
     "scene": "A man at a desk late in the evening, a photograph of "
              "his family beside the computer.",
     "q": ["How do you balance work or study with your personal "
           "life?",
           "What happens when this balance is lost?",
           "Should companies be responsible for their employees' "
           "free time?"]},
    {"topic": "Pul va baxt",
     "scene": "A simple wooden house next to a large modern villa in "
              "the same street.",
     "q": ["Does money make people happier?",
           "What do you think people value more than money?",
           "How has attitude to money changed in your country?"]},
    {"topic": "Ta'lim",
     "scene": "A classroom where half the desks are empty and the "
              "board is full of formulas.",
     "q": ["What is the purpose of education in your opinion?",
           "What would you change about the education system here?",
           "Should schools teach practical skills such as managing "
           "money?"]},
    {"topic": "Atrof-muhit",
     "scene": "A river bank covered in plastic bottles with a factory "
              "in the background.",
     "q": ["What environmental problems are most serious in your "
           "country?",
           "What can an ordinary person realistically do?",
           "Who should be mainly responsible — governments or "
           "individuals?"]},
    {"topic": "Ijtimoiy tarmoqlar",
     "scene": "A teenager photographing a plate of food in a cafe "
              "before eating it.",
     "q": ["Why do people share so much of their life online?",
           "What are the dangers of social media for young people?",
           "How could social media be used more usefully?"]},
    {"topic": "Sog'liq",
     "scene": "A hospital corridor with a long queue of people "
              "waiting on chairs.",
     "q": ["How do people look after their health in your country?",
           "What stops people from living more healthily?",
           "Should healthcare be free for everyone?"]},
    {"topic": "Shahar rivoji",
     "scene": "An old low neighbourhood with new tower blocks rising "
              "directly behind it.",
     "q": ["How has your city changed in the last ten years?",
           "What has been gained and what has been lost?",
           "How should cities grow in the future?"]},
    {"topic": "Ish tanlash",
     "scene": "A young person looking at a wall covered with job "
              "advertisements.",
     "q": ["What kind of work would you like to do?",
           "What matters more — a high salary or job satisfaction?",
           "Why do many young people change careers today?"]},
    {"topic": "An'ana va zamonaviylik",
     "scene": "A wedding where some guests wear traditional dress and "
              "others wear modern suits.",
     "q": ["Which traditions are important in your country?",
           "Are young people losing interest in traditions?",
           "Can a society be modern and traditional at the same "
           "time?"]},
    {"topic": "Sayohat va madaniyat",
     "scene": "A traveller sitting with a local family, sharing a "
              "meal and laughing.",
     "q": ["What do people gain from travelling to other countries?",
           "Tell me about something that surprised you about another "
           "culture.",
           "Does tourism help or harm local communities?"]},
    {"topic": "Ommaviy axborot",
     "scene": "A person reading news on a phone with several "
              "contradicting headlines visible.",
     "q": ["Where do you usually get your news?",
           "How can people tell whether news is reliable?",
           "What responsibility do the media have to society?"]},
    {"topic": "Jamoada ishlash",
     "scene": "Four colleagues around a table covered with sticky "
              "notes, one person writing on a whiteboard.",
     "q": ["Do you prefer working in a team or alone?",
           "What makes a team work well together?",
           "How should disagreements in a team be handled?"]},
    {"topic": "Vaqtni boshqarish",
     "scene": "A desk with a clock, a full diary and a long "
              "handwritten list of tasks.",
     "q": ["How do you organise your time?",
           "What usually stops you finishing what you planned?",
           "Why do so many people feel short of time today?"]},
    {"topic": "Sport va jamiyat",
     "scene": "A packed stadium where fans of both teams are "
              "cheering.",
     "q": ["Why is sport so important to many people?",
           "Should governments spend money on professional sport?",
           "How can sport bring communities together?"]},
    {"topic": "San'at",
     "scene": "A large colourful mural painted on the side of a grey "
              "apartment block.",
     "q": ["What role does art play in people's lives?",
           "Should art be taught in every school?",
           "Is street art a form of art or a problem?"]},
    {"topic": "Ko'ngillilik",
     "scene": "Volunteers handing out warm food from a van on a cold "
              "evening.",
     "q": ["Have you ever helped someone you did not know?",
           "Why do people give their time to help others?",
           "How could more young people be encouraged to volunteer?"]},
    {"topic": "Uy va joy tanlash",
     "scene": "Two doors side by side: one opening on to a busy "
              "street, the other on to a quiet garden.",
     "q": ["What makes a place a good place to live?",
           "Would you rather live near your work or in a quieter "
           "area?",
           "How do people's housing needs change with age?"]},
    {"topic": "Kelajak kasblari",
     "scene": "A robot working beside a human at the same counter.",
     "q": ["Which jobs do you think will disappear in the future?",
           "What skills will still be needed?",
           "How should young people prepare for this?"]},
]

# =================================================================
#  PART 3 — C1, mavzu + FOR/AGAINST ro'yxati, 2 daqiqa
#  Manba namunasi (5-bet): personal guns.
# =================================================================

P3: list[dict] = [
    {"topic": "Citizens should be allowed to carry personal guns.",
     "for": ["Guns can help people protect themselves",
             "They prevent people from becoming victims of crimes "
             "like burglary",
             "Necessary for hunting or target sports"],
     "against": ["Guns are weapons that are used to commit a crime",
                 "Fewer guns will reduce the murder rate",
                 "Small or military guns are not useful for "
                 "activities like hunting"]},
    {"topic": "University education should be free for everyone.",
     "for": ["Talented students are not stopped by family income",
             "A better educated workforce helps the whole economy",
             "Graduates start life without heavy debt"],
     "against": ["Someone has to pay — usually through higher taxes",
                 "Students may value a course less if it costs "
                 "nothing",
                 "Money might be better spent on primary schools"]},
    {"topic": "Mobile phones should be banned in schools.",
     "for": ["Students concentrate better without notifications",
             "It reduces cyberbullying during the school day",
             "Children talk to each other more at break time"],
     "against": ["Phones are useful learning tools in class",
                 "Parents need to contact their children",
                 "Students must learn to use technology responsibly"]},
    {"topic": "Working from home is better than working in an office.",
     "for": ["No time or money is wasted on commuting",
             "People can organise their day around their family",
             "Companies save money on office space"],
     "against": ["Teamwork and new ideas suffer without face-to-face "
                 "contact",
                 "The line between work and rest disappears",
                 "New employees learn much more slowly"]},
    {"topic": "Public transport should be free in large cities.",
     "for": ["Fewer cars means cleaner air and less traffic",
             "It helps people on low incomes reach work",
             "Ticket systems and inspectors cost money to run"],
     "against": ["The cost falls on taxpayers, including non-users",
                 "Crowding may make the service worse",
                 "Without income the system cannot be modernised"]},
    {"topic": "Social media does more harm than good.",
     "for": ["It damages the mental health of young people",
             "False information spreads faster than facts",
             "People compare their lives with unrealistic images"],
     "against": ["It keeps families and friends connected across "
                 "distance",
                 "Small businesses reach customers cheaply",
                 "It gives a voice to people who are usually "
                 "ignored"]},
    {"topic": "Zoos should be closed.",
     "for": ["Animals suffer in small artificial spaces",
             "Wild behaviour cannot develop in captivity",
             "Documentaries can teach the same lessons"],
     "against": ["Zoos protect species that are almost extinct",
                 "They fund research and conservation projects",
                 "Seeing a real animal changes how children think"]},
    {"topic": "Homework should be abolished in primary school.",
     "for": ["Young children need time to play and rest",
             "It creates stress and family arguments",
             "Research shows little effect at this age"],
     "against": ["It builds the habit of independent study",
                 "Parents can see what their child is learning",
                 "Practice at home strengthens new skills"]},
    {"topic": "Tourists should pay more to visit historical sites.",
     "for": ["The money pays for repair and protection",
             "Fewer visitors means less damage to old buildings",
             "Local people should not carry the cost alone"],
     "against": ["High prices exclude ordinary travellers",
                 "Tourism income supports local families",
                 "Heritage should belong to everyone, not only the "
                 "rich"]},
    {"topic": "Everyone should be required to learn a second "
              "language at school.",
     "for": ["It opens study and career opportunities",
             "Learning a language improves memory and thinking",
             "It builds understanding between cultures"],
     "against": ["Not every student needs it for their future work",
                 "Time could go to maths, science or practical "
                 "skills",
                 "Translation technology is becoming very good"]},
    {"topic": "Fast food should be taxed more heavily.",
     "for": ["Higher prices reduce consumption and obesity",
             "The tax money can fund health services",
             "It pushes companies to make healthier products"],
     "against": ["It hits poorer families hardest",
                 "People should be free to choose what they eat",
                 "Education works better than punishment"]},
    {"topic": "Companies should be allowed to advertise to children.",
     "for": ["Advertising funds free content and programmes",
             "Children learn to recognise persuasion early",
             "Parents make the final purchasing decision"],
     "against": ["Children cannot judge advertising critically",
                 "It creates pressure inside families",
                 "It encourages unhealthy food and unnecessary "
                 "spending"]},
    {"topic": "Living in a big city is better than living in the "
              "countryside.",
     "for": ["More jobs, universities and hospitals",
             "Cultural life — theatres, museums, events",
             "Better transport and services"],
     "against": ["Pollution, noise and constant crowds",
                 "Housing costs are far higher",
                 "Neighbours often do not know each other"]},
    {"topic": "Exams are the best way to measure a student's "
              "ability.",
     "for": ["Everyone is assessed by the same standard",
             "They are difficult to cheat when well organised",
             "They prepare students for pressure in real life"],
     "against": ["One bad day can ruin months of work",
                 "They reward memory rather than understanding",
                 "Creative and practical skills are ignored"]},
    {"topic": "Governments should invest more in space exploration.",
     "for": ["It produces technology used in daily life",
             "It inspires young people to study science",
             "Understanding space may protect the planet"],
     "against": ["The money is needed for hospitals and schools",
                 "Results take decades to appear",
                 "Private companies can fund it instead"]},
    {"topic": "Parents should limit how much time children spend "
              "online.",
     "for": ["Too much screen time affects sleep and eyesight",
             "Children need physical activity and real play",
             "It protects them from unsuitable content"],
     "against": ["Children learn a great deal online",
                 "Strict rules often push children to hide things",
                 "Self-control is a better long-term lesson"]},
    {"topic": "Traditional shops will disappear because of online "
              "shopping.",
     "for": ["Online prices are lower and choice is wider",
             "Delivery is faster and more convenient every year",
             "Shops carry high rent and staff costs"],
     "against": ["People want to see and try products first",
                 "Shopping is also a social activity",
                 "Local shops keep town centres alive"]},
    {"topic": "Employees should have a four-day working week.",
     "for": ["Rested workers make fewer mistakes",
             "It improves family life and mental health",
             "Trials show output often stays the same"],
     "against": ["Some services must run every day",
                 "Costs may rise for small businesses",
                 "The same work may simply be squeezed into fewer "
                 "days"]},
    {"topic": "Museums should be free to enter.",
     "for": ["Culture becomes available to every family",
             "Schools can visit more often",
             "More visitors bring money to the area"],
     "against": ["Museums need income to maintain collections",
                 "Free entry can lead to overcrowding",
                 "Taxes then support people who never visit"]},
    {"topic": "It is better to be self-employed than to work for a "
              "company.",
     "for": ["You control your own time and decisions",
             "Income is not limited by a fixed salary",
             "You can work on projects you believe in"],
     "against": ["Income is unstable, especially at the start",
                 "There is no paid holiday or sick leave",
                 "You must do accounting, sales and the work "
                 "itself"]},
    {"topic": "Renewable energy should replace all fossil fuels "
              "within twenty years.",
     "for": ["It reduces air pollution and health problems",
             "Costs of solar and wind are falling quickly",
             "It reduces dependence on imported fuel"],
     "against": ["Storage technology is not ready for all needs",
                 "Whole industries and regions depend on old fuels",
                 "The change requires enormous investment"]},
    {"topic": "Children should start school at the age of four.",
     "for": ["Early years are the best time for language learning",
             "It helps working parents",
             "Children from difficult homes get support sooner"],
     "against": ["Very young children learn best through play",
                 "It puts pressure on them too early",
                 "Family time in early years is valuable"]},
    {"topic": "Advertising should be banned on television.",
     "for": ["It interrupts programmes and wastes viewers' time",
             "It encourages unnecessary spending",
             "Children are influenced without understanding"],
     "against": ["Advertising pays for free channels",
                 "It informs people about useful products",
                 "It supports jobs in a whole industry"]},
    {"topic": "Every citizen should be required to vote.",
     "for": ["Results represent the whole population",
             "It encourages people to follow public issues",
             "It reduces the influence of small extreme groups"],
     "against": ["Freedom includes the freedom not to vote",
                 "Uninformed votes do not improve decisions",
                 "Fines punish the poorest most"]},
    {"topic": "Foreign films should always be dubbed rather than "
              "subtitled.",
     "for": ["Viewers can watch the images instead of reading",
             "It helps children and older viewers",
             "It makes cinema available to people who read slowly"],
     "against": ["The original acting and emotion are lost",
                 "Subtitles help people learn languages",
                 "Dubbing is expensive and often poorly done"]},
    {"topic": "Cities should ban private cars from the centre.",
     "for": ["Cleaner air and far less noise",
             "Streets become safer for children and cyclists",
             "Space can be used for parks and cafes"],
     "against": ["Shops in the centre may lose customers",
                 "Elderly and disabled people need door-to-door "
                 "transport",
                 "Public transport must be excellent first"]},
    {"topic": "Talented athletes deserve their very high salaries.",
     "for": ["Their careers are short and injuries end them",
             "They generate enormous income for clubs and sponsors",
             "Only a tiny number ever reach that level"],
     "against": ["Nurses and teachers do more valuable work",
                 "It gives young people the wrong priorities",
                 "The money comes from ordinary fans"]},
    {"topic": "Students should choose their subjects freely from the "
              "age of fourteen.",
     "for": ["Motivation rises when students study what interests "
             "them",
             "They can specialise earlier and go deeper",
             "It reduces the number who leave school early"],
     "against": ["Fourteen-year-olds may not know their future needs",
                 "A broad base of knowledge keeps options open",
                 "Choices may follow friends rather than ability"]},
    {"topic": "Artificial intelligence should be used to mark "
              "students' work.",
     "for": ["Feedback arrives immediately, not in two weeks",
             "The same standard is applied to everyone",
             "Teachers gain time for actual teaching"],
     "against": ["It cannot judge originality or genuine thought",
                 "Students may learn to write for the machine",
                 "Mistakes in the system affect thousands at once"]},
    {"topic": "People should be encouraged to eat less meat.",
     "for": ["Meat production uses huge amounts of water and land",
             "A plant-rich diet lowers heart disease",
             "It would reduce greenhouse gas emissions"],
     "against": ["Meat is part of national cuisine and tradition",
                 "Whole farming communities depend on it",
                 "Diet is a personal choice, not a public matter"]},
]
