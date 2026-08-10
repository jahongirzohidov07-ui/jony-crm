"""4 KO'NIKMA YANGI MASHQ TURLARI BAZASI (2026-08-11).

Jahongir bergan spetsifikatsiya bo'yicha. Har element:
(skill, kind, level, payload dict, answer, alt, explain).
Idempotent: (skill, kind, payload) bo'yicha faqat yo'qlari qo'shiladi.
"""

# ============================ READING ============================
# T/F/NG: payload {text, statement}; answer True/False/Not Given
_R_TFNG = [
("A1", "My name is Aziz. I am eleven. I live in Bekobod with my "
 "family. My father is a doctor. We have a small cat.",
 [("Aziz is eleven years old.", "True",
   "\"I am eleven\" - matnda aniq aytilgan."),
  ("Aziz lives in Tashkent.", "False",
   "Matnda Bekobod deyilgan."),
  ("His father is a doctor.", "True", "Aniq aytilgan."),
  ("Aziz has a sister.", "Not Given",
   "Matnda opa-singil haqida HECH NARSA yo'q."),
  ("They have a dog.", "False", "Matnda mushuk (cat) deyilgan.")]),
("A1", "Lola gets up at seven. She goes to school at eight. Her "
 "favourite lesson is English. After school she plays tennis.",
 [("Lola gets up at seven.", "True", "Aniq aytilgan."),
  ("She goes to school by bus.", "Not Given",
   "Qanday borishi aytilmagan."),
  ("Her favourite lesson is Maths.", "False",
   "English deyilgan."),
  ("She plays tennis after school.", "True", "Aniq aytilgan.")]),
("A2", "Dear Tim, I am writing from Samarkand. We arrived two days "
 "ago by train. Yesterday we visited Registan Square - the old "
 "buildings are amazing! Tomorrow we are going to a big market. "
 "See you next week. Malika.",
 [("Malika travelled to Samarkand by plane.", "False",
   "by train deyilgan - sinonim emas, boshqa transport."),
  ("She has already seen Registan Square.", "True",
   "\"Yesterday we visited\" = allaqachon ko'rgan."),
  ("The weather in Samarkand is hot.", "Not Given",
   "Ob-havo haqida gap yo'q."),
  ("She will return next week.", "True",
   "\"See you next week\" shuni bildiradi."),
  ("Malika is travelling alone.", "Not Given",
   "\"We\" deyilgan, lekin kim bilanligi noma'lum.")]),
("A2", "Last month our school opened a new library. It has more "
 "than five thousand books and a quiet reading room. Students can "
 "borrow three books for two weeks. The library is closed on "
 "Sundays.",
 [("The library opened last month.", "True", "Aniq aytilgan."),
  ("It has about five hundred books.", "False",
   "Besh MING (five thousand) deyilgan."),
  ("Students can keep books for a month.", "False",
   "Ikki hafta (two weeks) deyilgan."),
  ("The library has free Wi-Fi.", "Not Given",
   "Wi-Fi haqida ma'lumot yo'q."),
  ("It does not work on Sundays.", "True",
   "closed on Sundays = ishlamaydi.")]),
("B1", "Many people think that learning a language is only about "
 "memorising words. However, researchers say that regular short "
 "practice is more important than long rare sessions. Fifteen "
 "minutes every day gives better results than three hours once a "
 "week, because the brain needs repetition to move information "
 "into long-term memory.",
 [("The author agrees that language learning is only about "
   "memorising words.", "False",
   "\"However...\" - muallif bu fikrga QO'SHILMAYDI."),
  ("Short daily practice is better than rare long sessions.",
   "True", "Matnning asosiy g'oyasi."),
  ("The brain needs repetition to remember for a long time.",
   "True", "\"needs repetition to move into long-term memory\"."),
  ("The research was done at Oxford University.", "Not Given",
   "Qayerda o'tkazilgani aytilmagan."),
  ("Three hours once a week is the best way to learn.", "False",
   "Aksincha deyilgan.")]),
("B1", "Our city plans to make the central street car-free from "
 "next spring. Shop owners first protested, fearing they would "
 "lose customers. But a study of ten similar projects in other "
 "cities showed that sales usually grow, because people walking "
 "slowly notice shops more often than drivers do.",
 [("The central street is already car-free.", "False",
   "\"plans to... from next spring\" - hali emas."),
  ("At first, shop owners supported the plan.", "False",
   "protested = qarshi chiqishgan."),
  ("Similar projects usually increase sales.", "True",
   "\"sales usually grow\"."),
  ("The study looked at ten projects.", "True", "Aniq raqam bor."),
  ("Taxi drivers are against the plan.", "Not Given",
   "Taksichilar haqida gap yo'q.")]),
]

# read_gap: payload {text (raqamli bo'shliqlar), options[[...]]};
# answer - JSON ro'yxat
_R_GAP = [
("A1", "Aziz is my best (1)___. He is eleven years (2)___. Every "
 "morning he (3)___ to school by bus. After lessons he plays "
 "(4)___ with his brother.",
 [["friend", "teacher", "book"], ["old", "tall", "new"],
  ["goes", "eats", "sleeps"], ["football", "kitchen", "water"]],
 ["friend", "old", "goes", "football"],
 "Ma'no bo'yicha: do'st, yosh, boradi, futbol."),
("A1", "I have a small (1)___. Its name is Simba. It likes to "
 "(2)___ milk. At night it (3)___ on my bed.",
 [["cat", "car", "chair"], ["drink", "read", "write"],
  ["sleeps", "cooks", "opens"]],
 ["cat", "drink", "sleeps"],
 "Mushuk sut ichadi va uxlaydi."),
("A2", "Yesterday we went (1)___ the mountains. We arrived early "
 "(2)___ the morning. The weather was sunny, (3)___ in the "
 "evening it started to rain. We came home tired (4)___ happy.",
 [["to", "on", "at"], ["in", "on", "at"], ["but", "and", "so"],
  ["but", "or", "if"]],
 ["to", "in", "but", "but"],
 "go TO, IN the morning; qarama-qarshilik - but."),
("A2", "Kamola is the (1)___ student in our class. She always "
 "does her homework (2)___ and never comes late. Teachers say "
 "she is very (3)___ and works (4)___ than anyone.",
 [["best", "good", "well"], ["carefully", "careful", "care"],
  ["clever", "cleverly", "cleverness"], ["harder", "hard", "hardest"]],
 ["best", "carefully", "clever", "harder"],
 "the best; ravish carefully; sifat clever; taqqoslash harder."),
("B1", "Sleep is not wasted time. (1)___ During the night the "
 "brain sorts everything you learned. (2)___ That is why students "
 "who sleep well usually get higher marks. (3)___",
 [["Scientists explain why.", "Nobody knows why.",
   "It is just a habit."],
  ["Important facts move into long-term memory.",
   "The body stops working completely.",
   "Dreams have no meaning."],
  ["So a good night's sleep is real preparation for exams.",
   "So it is better to study all night.",
   "So marks do not depend on sleep."]],
 ["Scientists explain why.",
  "Important facts move into long-term memory.",
  "So a good night's sleep is real preparation for exams."],
 "B1: butun GAPLARNI matn mantig'iga qarab joylash."),
]

# read_match: payload {paragraphs:[...], headings:[...]};
# answer - har abzas uchun sarlavha (JSON ro'yxat)
_R_MATCH = [
("A1",
 ["My name is Timur. I am from Bekobod. I am twelve years old.",
  "I get up at seven, go to school and do my homework in the "
  "evening.",
  "I like football and chess. On Sundays I play with my friends."],
 ["About me", "My day", "My hobbies"],
 ["About me", "My day", "My hobbies"],
 "Har abzasning asosiy mavzusi."),
("A2",
 ["Our school canteen started serving fresh fruit every day. "
  "Students can take an apple or a banana for free.",
  "The sports hall got new equipment: balls, mats and a climbing "
  "wall. PE lessons are now much more interesting.",
  "From next month the library will work until 7 pm, so students "
  "can do homework there after lessons."],
 ["Healthy food at school", "Better sport lessons",
  "Longer library hours"],
 ["Healthy food at school", "Better sport lessons",
  "Longer library hours"],
 "Har abzas bitta yangilik haqida."),
("B1",
 ["People often buy things they do not need just because of a "
  "discount. Shops know this and use big red labels on purpose.",
  "A simple rule helps: wait 24 hours before buying anything that "
  "is not on your list. Most of the time the wish disappears.",
  "Saving even small amounts regularly gives surprising results: "
  "ten thousand som a day becomes more than three million a year."],
 ["Why we buy too much", "A trick to stop impulse buying",
  "The power of small savings"],
 ["Why we buy too much", "A trick to stop impulse buying",
  "The power of small savings"],
 "Bosh g'oya (main idea) ni aniqlash."),
]

# ============================ LISTENING ============================
# listen_img: payload {say, options:[{emoji,label}]}; answer - label
_L_IMG = [
("A1", "He is wearing a red hat.",
 [("🎩", "black hat"), ("🧢", "red cap"), ("👒", "red hat"),
  ("🧣", "red scarf")], "red hat",
 "red hat - qizil shlyapa."),
("A1", "She is eating an apple.",
 [("🍎", "apple"), ("🍌", "banana"), ("🍞", "bread"),
  ("🥛", "milk")], "apple", "apple - olma."),
("A1", "It is raining.",
 [("☀️", "sunny"), ("🌧️", "raining"), ("❄️", "snowing"),
  ("🌪️", "windy")], "raining", "rain - yomg'ir."),
("A1", "The boy is riding a bicycle.",
 [("🚲", "bicycle"), ("🚗", "car"), ("🚌", "bus"),
  ("✈️", "plane")], "bicycle", "bicycle - velosiped."),
("A1", "There are three books on the table.",
 [("📚", "books"), ("🖊️", "pens"), ("🎒", "bags"),
  ("💻", "laptops")], "books", "books - kitoblar."),
("A2", "Turn left at the bank, and the library is next to the "
 "park.",
 [("🏦", "bank"), ("📚", "library"), ("🏫", "school"),
  ("🏥", "hospital")], "library",
 "Qayerga yetib borish aytilyapti - kutubxona."),
("A2", "The man is cooking dinner in the kitchen.",
 [("🍳", "cooking"), ("🧹", "cleaning"), ("📖", "reading"),
  ("😴", "sleeping")], "cooking", "cook - ovqat pishirish."),
("A2", "She bought a ticket and got on the train.",
 [("🚆", "train"), ("🚕", "taxi"), ("🚢", "ship"),
  ("🚁", "helicopter")], "train", "train - poyezd."),
("B1", "After hearing the good news, she couldn't stop smiling "
 "all day.",
 [("😊", "happy"), ("😢", "sad"), ("😡", "angry"),
  ("😱", "scared")], "happy",
 "couldn't stop smiling - xursandlik belgisi."),
("B1", "Everyone was quiet and nervous before the exam results "
 "appeared.",
 [("😬", "nervous"), ("🥳", "celebrating"), ("😴", "bored"),
  ("😎", "relaxed")], "nervous",
 "quiet and nervous - hayajon."),
]

# listen_qa: payload {say (dialog/monolog), prompt, options}; answer
_L_QA = [
("A1", "The bus leaves at nine o'clock in the morning.",
 "What time does the bus leave?",
 ["At nine", "At ten", "At seven", "At noon"], "At nine",
 "nine o'clock deyilgan."),
("A1", "Hello! My name is Karim. I am from Bekobod. I have two "
 "brothers.",
 "How many brothers does Karim have?",
 ["Two", "Three", "One", "None"], "Two", "two brothers."),
("A1", "Mum: Dinner is ready! Son: What is it? Mum: Your "
 "favourite - plov!",
 "What did mum cook?",
 ["Plov", "Soup", "Pizza", "Salad"], "Plov",
 "Your favourite - plov."),
("A2", "Woman: Excuse me, how much is this bag? Seller: It is "
 "ninety thousand som. Woman: That's expensive. Can you make it "
 "seventy? Seller: OK, eighty and it is yours.",
 "How much will the woman probably pay?",
 ["Eighty thousand", "Ninety thousand", "Seventy thousand",
  "Fifty thousand"], "Eighty thousand",
 "Savdolashuv 80 mingda to'xtadi."),
("A2", "Man: Two tickets to Samarkand, please. Clerk: For today? "
 "Man: No, for tomorrow morning. Clerk: The 8 am train has free "
 "seats. Man: Perfect.",
 "When will the man travel?",
 ["Tomorrow morning", "Today", "Tonight", "Next week"],
 "Tomorrow morning", "for tomorrow morning dedi."),
("A2", "Girl: Let's meet at four near the cinema. Boy: I have an "
 "English lesson until four thirty. Girl: OK, five o'clock then.",
 "What time will they meet?",
 ["At five", "At four", "At four thirty", "At six"], "At five",
 "Oxirgi kelishuv - five o'clock."),
("B1", "Woman: How was the new restaurant? Man: Well, the food "
 "arrived quickly and looked beautiful... but honestly, my dish "
 "was almost cold, and for that price I expected much more.",
 "What does the man really think about the restaurant?",
 ["He was disappointed", "He loved everything",
  "He liked the price", "He will go again tomorrow"],
 "He was disappointed",
 "\"...I expected much more\" - norozilik (yashirin ma'no)."),
("B1", "Teacher: Aziz, your essay is well written, and your "
 "grammar has clearly improved. Next time, try to add your own "
 "examples instead of general phrases - that will make it "
 "excellent.",
 "What is the teacher's main advice?",
 ["Add his own examples", "Improve his grammar",
  "Write more pages", "Copy general phrases"],
 "Add his own examples",
 "Asosiy maslahat - o'z misollarini qo'shish."),
("B1", "Announcement: Due to heavy snow, all morning flights are "
 "delayed. Passengers for Tashkent should go to gate 5, where "
 "staff will give new boarding times.",
 "What should Tashkent passengers do?",
 ["Go to gate 5", "Go home", "Board immediately",
  "Buy new tickets"], "Go to gate 5",
 "should go to gate 5 deyilgan."),
]

# listen_order: payload {say, steps (TO'G'RI tartibda)}; answer JSON
_L_ORDER = [
("A1", "Every morning I get up at seven. Then I wash my face. "
 "After that I have breakfast. Finally I go to school.",
 ["I get up", "I wash my face", "I have breakfast",
  "I go to school"],
 "Kunlik tartib: turish - yuvinish - nonushta - maktab."),
("A1", "First the cat sees a bird. Then it runs to the tree. But "
 "the bird flies away. So the cat sleeps under the tree.",
 ["The cat sees a bird", "It runs to the tree",
  "The bird flies away", "The cat sleeps"],
 "Voqealar ketma-ketligi."),
("A2", "To make tea, first boil some water. Then put a tea bag "
 "into the cup. After that pour the hot water. Finally add sugar "
 "and enjoy.",
 ["Boil water", "Put a tea bag in the cup", "Pour the hot water",
  "Add sugar"],
 "Retsept bosqichlari."),
("A2", "To use the washing machine, first put the clothes inside. "
 "Then add the powder. Next choose the programme. At the end "
 "press the start button.",
 ["Put the clothes inside", "Add the powder",
  "Choose the programme", "Press start"],
 "Yo'riqnoma tartibi."),
("B1", "Last summer we travelled to Khiva. We left Tashkent by "
 "night train. In the morning we checked into a small hotel near "
 "the old city. During the day we walked along the ancient walls, "
 "and in the evening we watched the sunset from a tower.",
 ["They left Tashkent by train", "They checked into a hotel",
  "They walked along the walls", "They watched the sunset"],
 "Sayohat voqealari rivoji."),
("B1", "The interview did not start well: I arrived late because "
 "of traffic. However, I apologised and explained my projects "
 "calmly. The manager asked several difficult questions. In the "
 "end, she smiled and offered me the job.",
 ["He arrived late", "He explained his projects",
  "The manager asked questions", "She offered him the job"],
 "Hikoya ketma-ketligi."),
]

# ============================ WRITING ============================
# write_transform: payload {instruction, given}; answer + alt
_W_TRANSFORM = [
("A1", "Ikki gapni AND bilan birlashtirib yozing:",
 "I like tea. I like coffee.",
 "I like tea and coffee", ["I like coffee and tea"],
 "Bir xil fe'l takrorlanmaydi: and bilan birlashadi."),
("A1", "Ikki gapni BUT bilan birlashtirib yozing:",
 "She is small. She is strong.",
 "She is small but strong", [],
 "Qarama-qarshi sifatlar but bilan."),
("A1", "Gapni INKOR shaklga o'tkazing:",
 "I like cold tea.",
 "I don't like cold tea", ["I do not like cold tea"],
 "Present Simple inkori: don't + fe'l."),
("A1", "Gapni SAVOL shaklga o'tkazing:",
 "You speak English.",
 "Do you speak English", ["Do you speak English?"],
 "Savol: Do + ega + fe'l."),
("A2", "Gapga YESTERDAY qo'shib, o'tgan zamonda yozing:",
 "I watch an interesting film.",
 "I watched an interesting film yesterday",
 ["Yesterday I watched an interesting film"],
 "watch - watched, yesterday qo'shiladi."),
("A2", "Gapga IN THE LIBRARY qo'shib qayta yozing:",
 "She reads books.",
 "She reads books in the library", [],
 "Joy ko'rsatkichi gap oxirida."),
("A2", "Gapni KELASI zamonga o'tkazing (will):",
 "He plays football.",
 "He will play football", [],
 "will + fe'l o'z holicha."),
("A2", "Ikki gapni BECAUSE bilan birlashtirib yozing:",
 "I stayed home. I was ill.",
 "I stayed home because I was ill", [],
 "Sabab because bilan."),
("B1", "Gapni PASSIV nisbatga o'tkazing:",
 "They built this school in 2010.",
 "This school was built in 2010", [],
 "was/were + V3; ega tushib qoladi."),
("B1", "Gapni PASSIV nisbatga o'tkazing:",
 "People speak English all over the world.",
 "English is spoken all over the world", [],
 "Present passiv: is + V3."),
("B1", "Gapni 2-shart (Second Conditional) shakliga o'tkazing:",
 "I am not rich, so I will not buy a car.",
 "If I were rich I would buy a car",
 ["If I were rich, I would buy a car"],
 "Xayoliy shart: If + Past, would + fe'l."),
("B1", "Gapni RASMIYROQ uslubda yozing (Could you...):",
 "Open the window!",
 "Could you open the window please",
 ["Could you open the window, please?",
  "Could you please open the window",
  "Could you open the window"],
 "Buyruq -> muloyim iltimos."),
]

# ============================ SPEAKING ============================
# speak_repeat: payload {say}; answer = say (takrorlash)
_S_REPEAT = [
("A1", "Good morning"), ("A1", "I like apples"),
("A1", "My name is important to me"), ("A1", "Nice to meet you"),
("A2", "Where is the nearest bus station"),
("A2", "I usually get up at seven o'clock"),
("A2", "Could you help me with my homework"),
("B1", "If it rains tomorrow we will stay at home"),
("B1", "I have been learning English for two years"),
("B1", "Learning a language takes time but it is worth it"),
]

# speak_answer: payload {say (savol), hint}; answer - kalit iboralar
_S_ANSWER = [
("A1", "What is your name?", "My name is ...",
 ["my name is", "i am", "i'm"],
 "Javob \"My name is ...\" bilan boshlansin."),
("A1", "How old are you?", "I am ... years old",
 ["i am", "i'm", "years old"],
 "\"I am ... (years old)\" deb javob bering."),
("A1", "Where are you from?", "I am from ...",
 ["i am from", "i'm from", "from"],
 "\"I am from ...\" deb javob bering."),
("A2", "What did you do yesterday?", "Yesterday I ...",
 ["yesterday i", "i went", "i played", "i watched", "i studied",
  "i visited", "i was"],
 "O'tgan zamonda javob bering: Yesterday I ..."),
("A2", "What is your favourite food?", "My favourite food is ...",
 ["my favourite food is", "my favorite food is", "i like",
  "i love"],
 "\"My favourite food is ...\" yoki \"I like ...\"."),
("B1", "Why do you want to learn English?", "I want to learn "
 "English because ...",
 ["because", "i want", "i need"],
 "Sababini ayting: ... because ..."),
("B1", "What will you do after you finish school?",
 "After school I will ...",
 ["i will", "i want to", "i am going to", "i'm going to"],
 "Kelasi zamonda reja ayting."),
]


def seed_practice(db):
    """Idempotent: (skill, kind, payload) bo'yicha yo'qlari qo'shiladi."""
    import json
    import models

    rows = []
    for lvl, text, sts in _R_TFNG:
        for stmt, ans, expl in sts:
            rows.append(("reading", "read_tfng", lvl,
                         {"text": text, "statement": stmt},
                         ans, None, expl))
    for lvl, text, opts, ans, expl in _R_GAP:
        rows.append(("reading", "read_gap", lvl,
                     {"text": text, "options": opts},
                     json.dumps(ans, ensure_ascii=False), None, expl))
    for lvl, paras, heads, ans, expl in _R_MATCH:
        rows.append(("reading", "read_match", lvl,
                     {"paragraphs": paras, "headings": heads},
                     json.dumps(ans, ensure_ascii=False), None, expl))
    for lvl, say, opts, ans, expl in _L_IMG:
        rows.append(("listening", "listen_img", lvl,
                     {"say": say,
                      "options": [{"emoji": e, "label": l}
                                  for e, l in opts]},
                     ans, None, expl))
    for lvl, say, prompt, opts, ans, expl in _L_QA:
        rows.append(("listening", "listen_qa", lvl,
                     {"say": say, "prompt": prompt, "options": opts},
                     ans, None, expl))
    for lvl, say, steps, expl in _L_ORDER:
        rows.append(("listening", "listen_order", lvl,
                     {"say": say, "steps": steps},
                     json.dumps(steps, ensure_ascii=False), None, expl))
    for lvl, instr, given, ans, alt, expl in _W_TRANSFORM:
        rows.append(("writing", "write_transform", lvl,
                     {"instruction": instr, "given": given},
                     ans, json.dumps(alt, ensure_ascii=False), expl))
    for lvl, say in _S_REPEAT:
        rows.append(("speaking", "speak_repeat", lvl,
                     {"say": say}, say, None,
                     "Eshitganingizni aynan takrorlang."))
    for lvl, say, hint, pats, expl in _S_ANSWER:
        rows.append(("speaking", "speak_answer", lvl,
                     {"say": say, "hint": hint},
                     json.dumps(pats, ensure_ascii=False), None, expl))

    have = {(r.skill, r.kind, r.payload) for r in
            db.query(models.PracticeItem).all()}
    made = 0
    for skill, kind, lvl, payload, ans, alt, expl in rows:
        pj = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if (skill, kind, pj) in have:
            continue
        db.add(models.PracticeItem(
            skill=skill, kind=kind, level=lvl, payload=pj,
            answer=ans, alt=alt, explain=expl))
        made += 1
    if made:
        db.commit()
    return made
