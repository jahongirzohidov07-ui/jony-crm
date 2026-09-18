"""Boshlang'ich test bazasi (2026-09-18) — Jahongir yuborgan fayllardan.

Har element: (seed kaliti, test). Kalit bir marta yoziladi — keyin
examinerlar boshlig'i testni CRM'da (Audit -> Test bazasi) o'zi
tahrirlaydi, bu fayl uni qayta yozmaydi.

Manba: "Jony Academy exams. Step 1.0 Unit 1.pdf" + "Unit 1 Progress
Test AK.pdf" (javob kaliti)."""


def _c(q, opts, a, image=None):
    d = {"type": "choice", "q": q, "options": opts,
         "answer": "ABCDEFGH".index(a)}
    if image:
        d["image"] = image      # public/exam-img/… dagi rasm
    return d


def _t(q, *answers, image=None):
    d = {"type": "text", "q": q, "answer": list(answers)}
    if image:
        d["image"] = image
    return d


STEP1_UNIT1 = {
    "level": "step1", "kind": "unit", "unit_no": 1,
    "title": "Step 1 · Unit 1 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Hi, my name’s Sophia.", "I’m good.", "And you?"], "A"),
                _c("", ["And you?", "I’m good, thanks.", "Good to meet you, too."], "C"),
                _c("", ["Where’s Carlo?", "Nice to meet you, too.", "Good afternoon."], "C"),
                _c("", ["Hi, I’m Anna.", "Oh, not bad, thanks.", "Where’s Megan?"], "A"),
                _c("", ["And you?", "Nice to meet you.", "I’m fine, thank you."], "B"),
                _c("", ["Good afternoon.", "I’m OK, thanks.", "Good to meet you, too."], "B"),
            ],
        },
        {
            "title": "Part 2 · Countries and nationalities",
            "instructions": "Read the sentences about countries and "
                            "nationalities. What are the missing words? The "
                            "first letter is already there. Write the whole "
                            "word.",
            "questions": [
                _t("My friend Alex is American – he’s from a city in t _ _ U _ _ .",
                   "the USA", "he SA", "USA"),
                _t("Hi, I’m from Beijing in C _ _ _ _ and I’m Chinese.",
                   "China", "hina"),
                _t("This is my friend Lena – she’s from Moscow in R _ _ _ _ _ "
                   "and she’s Russian.", "Russia", "ussia"),
                _t("My friend’s name is Maria and she’s from Brazil – she’s "
                   "B _ _ _ _ _ _ _ _ .", "Brazilian", "razilian"),
                _t("His name is Carlo and he’s from Italy – he’s I _ _ _ _ _ _ .",
                   "Italian", "talian"),
                _t("John is British and he’s from Manchester, a city in "
                   "B _ _ _ _ _ _ .", "Britain", "ritain"),
            ],
        },
        {
            "title": "Part 3 · Countries and nationalities",
            "instructions": "Read the sentences about countries and "
                            "nationalities. What are the missing words? The "
                            "first letter is already there. Write the whole "
                            "word.",
            "questions": [
                _t("My teacher is British – he is from t _ _   U _ .",
                   "the UK", "he K", "UK"),
                _t("Hello, I’m Akira from Tokyo in J _ _ _ _ − I’m Japanese.",
                   "Japan", "apan"),
                _t("Is everyone in your class from Poland – are they all "
                   "P _ _ _ _ _ ?", "Polish", "olish"),
                _t("My name is John – I’m from Toronto in Canada and I’m "
                   "C _ _ _ _ _ _ _ .", "Canadian", "anadian"),
                _t("The receptionist is from Ankara in T _ _ _ _ _ − she’s "
                   "Turkish.", "Turkey", "urkey"),
                _t("This is Megan from Australia – she’s my friend and she’s "
                   "A _ _ _ _ _ _ _ _ _ .", "Australian", "ustralian"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the email from Harumi. Choose the best "
                            "answer (A, B or C) for each space.",
            "passage": (
                "Hi Anna\n\n"
                "How (19) ………… ? And how are your friends, Hannah and Megan? "
                "I'm fine. I'm not in Japan now – I (20) ………… a student in a "
                "small language school in Britain. It’s a good school. "
                "(21) ………… you a student now?\n"
                "My teacher’s name is Darren and he’s nice. He isn’t British – "
                "he’s from Toronto in Canada. (22) ………… your English teacher "
                "from? Is he from the UK?\n"
                "My friends here are students and (23) ………… in my class. Their "
                "names are Laura and Carlo. They (24) ………… from Japan – "
                "they’re from Bologna in Italy and they’re married. We’re good "
                "friends now.\n\nHarumi"),
            "questions": [
                _c("", ["is she", "am I", "are you"], "C"),
                _c("", ["is", "am", "are"], "B"),
                _c("", ["Are", "Is", "Am"], "A"),
                _c("", ["Where’s", "How’s", "What’s"], "A"),
                _c("", ["he’s", "they’re", "I’m"], "B"),
                _c("", ["isn’t", "aren’t", "am not"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about people, countries and "
                            "nationalities. Choose the best answer, A, B or C, "
                            "for each space.",
            "questions": [
                _c("Hello, my name’s Joe and I ............ from London.",
                   ["am", "is", "are"], "A"),
                _c("We aren’t from Australia ............ from Canada.",
                   ["we’re", "he’s", "they’re"], "A"),
                _c("No, you ............ in my class.",
                   ["isn’t", "aren’t", "am not"], "B"),
                _c("Your teacher’s nice - where ............ he from?",
                   ["are", "is", "am"], "B"),
                _c("Hello, ............ your name?",
                   ["who’s", "how’s", "what’s"], "C"),
                _c("Kumiko is Japanese, but she ............ from Tokyo.",
                   ["am not", "aren’t", "isn’t"], "C"),
            ],
        },
    ],
}


NUMBERS_A_G = ["twelve", "thirty", "eleven", "sixty", "fifty", "sixteen",
               "nineteen"]

STEP1_UNIT2 = {
    "level": "step1", "kind": "unit", "unit_no": 2,
    "title": "Step 1 · Unit 2 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Can you spell that?", "Is it a big city?", "Are they British?"], "A"),
                _c("", ["Yes, please.", "Yes, I do.", "Yes, it’s fine."], "B"),
                _c("", ["It’s my number, thanks.", "It’s 12, High Street.", "It’s 07844 012145"], "C"),
                _c("", ["I’m British.", "Nice to meet you.", "It’s Jackson."], "C"),
                _c("", ["15, Station Street.", "sarahbrown@friend.com.", "I’m fine, thank you."], "B"),
                _c("", ["taylor@busy.com.", "T-A-Y-L-O-R.", "07355 687091."], "B"),
            ],
        },
        {
            "title": "Part 2 · People, things and places",
            "instructions": "Read the sentences about people, things and "
                            "places. What are the missing words? The first "
                            "letter is already there. Write the whole word.",
            "questions": [
                _t("Your friend isn’t sad – she’s h _ _ _ _ !", "happy", "appy"),
                _t("This isn’t the right phone number for Jack – it’s the "
                   "w _ _ _ _ number.", "wrong", "rong"),
                _t("Is English an e _ _ _ language or is it difficult?",
                   "easy", "asy"),
                _t("It’s a n _ _ umbrella, not an old one.", "new", "ew"),
                _t("My home is in a big city but your home is in a "
                   "s _ _ _ _ village.", "small", "mall"),
                _t("His newspaper isn’t boring – it’s i _ _ _ _ _ _ _ _ _ _ .",
                   "interesting", "nteresting"),
            ],
        },
        {
            "title": "Part 3 · Numbers",
            "instructions": "Choose the word to match the number.",
            "questions": [
                _c("50", NUMBERS_A_G, "E"),
                _c("16", NUMBERS_A_G, "F"),
                _c("12", NUMBERS_A_G, "A"),
                _c("19", NUMBERS_A_G, "G"),
                _c("30", NUMBERS_A_G, "B"),
                _c("11", NUMBERS_A_G, "C"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the conversation in a student café between "
                            "Luke and Gabi. Choose the correct answer (A, B or "
                            "C) for each space.",
            "passage": """Nice to meet you

Luke: Hello, I'm Luke.
Gabi: Nice to meet you, Luke. I'm Gabi.
Luke: Where are you from?
Gabi: From Italy.
Luke: The (19) ………… in Italy are beautiful.
Gabi: Yes. (20) ………… old and interesting. My home is in Ravello. That's where I live.
Luke: Great! I have an Italian friend at school. He's from Ravello too! (21) ………… name's Marco. What's your address?
Gabi: I have two (22) ………… ! One address is with my parents. (23) ………… house is in a beautiful part of Ravello.
Luke: And do you have an address in the UK?
Gabi: Yes, in Harlow. It's a small town near London.
Luke: Oh, yes. The (24) ………… there are big.
Gabi: Yes. I have four rooms. My friend, Anna, and her two boys have two of the rooms. Where's your home, Luke? Is it in London?
Luke: No, in Harlow!
Gabi: Oh!""",
            "questions": [
                _c("", ["cities", "city", "city’s"], "A"),
                _c("", ["He’s", "They’re", "Are they"], "B"),
                _c("", ["His", "Her", "Our"], "A"),
                _c("", ["address", "addresses", "addresses’"], "B"),
                _c("", ["Her", "His", "Their"], "C"),
                _c("", ["house", "houses", "house’s"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about things and places. "
                            "Choose the best answer, A, B or C, for each "
                            "space.",
            "questions": [
                _c("The old books ............ interesting – they’re boring.",
                   ["isn’t", "aren’t", "are they"], "B"),
                _c("My parents are from Moscow and this is a picture of "
                   "............ flat.", ["his", "your", "their"], "C"),
                _c("............ a new hotel?", ["It is", "Are they", "Is it"], "C"),
                _c("Do you have three ............ for our water?",
                   ["glasses", "glasses’", "glass"], "A"),
                _c("Where are our ............ to Barcelona?",
                   ["ticket", "tickets", "ticket’s"], "B"),
                _c("My friends are from different ............ : Spain, "
                   "Brazil and China.", ["countries", "country’s", "country"], "A"),
            ],
        },
    ],
}


U3_IMG = "/exam-img/step1-u3/"
FOOD_A_G = ["cheese", "an apple", "a potato", "a tomato", "a pizza",
            "a biscuit", "an orange"]

STEP1_UNIT3 = {
    "level": "step1", "kind": "unit", "unit_no": 3,
    "title": "Step 1 · Unit 3 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["No, it’s not.", "Do you like vegetables?", "And ice-cream too?"], "C"),
                _c("", ["That’s £3.50, please.", "No, thank you.", "It’s nice."], "A"),
                _c("", ["A sandwich, please.", "So, two cups of tea.", "How are you?"], "A"),
                _c("", ["A glass of orange juice, please.", "Of course.", "It’s 725129."], "B"),
                _c("", ["Thank you.", "Here you are.", "And something to eat?"], "B"),
                _c("", ["Certainly.", "Yes, please.", "It’s new."], "A"),
            ],
        },
        {
            "title": "Part 2 · Food and drink",
            "instructions": "Look at the pictures. What are the missing "
                            "letters? Some letters are already there. Write "
                            "the whole word.",
            "questions": [
                _t("a f _ _ _", "fish", "ish", image=U3_IMG + "q7.jpg"),
                _t("v _ _ _ _ _ _ _ _ _", "vegetables", "egetables",
                   image=U3_IMG + "q8.jpg"),
                _t("m _ _ _", "meat", "eat", image=U3_IMG + "q9.jpg"),
                _t("r _ _ _", "rice", "ice", image=U3_IMG + "q10.jpg"),
                _t("b _ _ _ _", "bread", "read", image=U3_IMG + "q11.jpg"),
                _t("a glass of c _ _ _", "coke", "oke", "cola", "ola",
                   image=U3_IMG + "q12.jpg"),
            ],
        },
        {
            "title": "Part 3 · Food",
            "instructions": "Choose the word to match the picture.",
            "questions": [
                _c("", FOOD_A_G, "G", image=U3_IMG + "q13.jpg"),
                _c("", FOOD_A_G, "F", image=U3_IMG + "q14.jpg"),
                _c("", FOOD_A_G, "D", image=U3_IMG + "q15.jpg"),
                _c("", FOOD_A_G, "B", image=U3_IMG + "q16.jpg"),
                _c("", FOOD_A_G, "A", image=U3_IMG + "q17.jpg"),
                _c("", FOOD_A_G, "C", image=U3_IMG + "q18.jpg"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the text about food and drink. Choose the "
                            "best answer (A, B or C) for each space.",
            "passage": """Food in my family

My name is Roz. I live in London with my family. Do we all like food? Yes, we do. We eat breakfast at 7.30. For breakfast, we (19) ………… eat eggs, or cereal with milk, but I think toast is the number one breakfast for my family. We (20) ………… a lot of toast! We drink tea or coffee or fruit juice. At 11.00 o'clock, my father likes coffee with biscuits.
At 1.00 o'clock, we eat lunch. We (21) ………… have a sandwich, but not every day. I like cheese sandwiches, and then a piece of cake or an apple.
Dinner is (22) ………… early - at 6.00 o'clock. We don't eat dinner late like people in Spain. We (23) ………… a big dinner with meat or fish, vegetables and potatoes. And I like ice cream, but it isn't very good for me! We never have pizza at home – my mother and father (24) ………… like it, so I eat it in restaurants.""",
            "questions": [
                _c("", ["lots", "never", "sometimes"], "C"),
                _c("", ["eats", "eat", "to eat"], "B"),
                _c("", ["usually", "always", "never"], "A"),
                _c("", ["a lot of", "never", "always"], "C"),
                _c("", ["has", "are", "have"], "C"),
                _c("", ["don’t", "aren’t", "haven’t"], "A"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about what people eat and "
                            "drink. Choose the best answer, A, B or C, for "
                            "each space.",
            "questions": [
                _c("I eat lots of things – I ............ fruit and vegetables every day.",
                   ["have", "likes", "eats"], "A"),
                _c("............ your friends eat a lot of bread?",
                   ["Have", "Are", "Do"], "C"),
                _c("Alice and Ben like fish, but they ............ like meat.",
                   ["isn’t", "don’t", "aren’t"], "B"),
                _c("I ............ eat toast for breakfast but not every day – "
                   "I sometimes have cereal or fruit.",
                   ["usually", "lots", "always"], "A"),
                _c("I ............ eat cheese – I don’t like it.",
                   ["never", "always", "sometimes"], "A"),
                _c("In Jan’s family, they ............ dinner at eight o’clock every night.",
                   ["have usually", "always have", "sometimes has"], "B"),
            ],
        },
    ],
}


U4_IMG = "/exam-img/step1-u4/"
PEOPLE_A_G = ["people", "man", "parents", "boy", "baby", "woman", "girl"]

STEP1_UNIT4 = {
    "level": "step1", "kind": "unit", "unit_no": 4,
    "title": "Step 1 · Unit 4 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Not bad, thanks.", "Nice to meet you.", "It’s really nice."], "C"),
                _c("", ["Yes, please.", "Yes, I do.", "Yes, it’s fine."], "B"),
                _c("", ["Can I help you?", "Can I see them?", "Do you like it?"], "B"),
                _c("", ["It’s my sister, Monica.", "Fine, thank you.", "My name’s Sophia."], "A"),
                _c("", ["See you later!", "What’s your name?", "They’re lovely!"], "C"),
                _c("", ["Yes, I do.", "I like it too.", "I’m good."], "B"),
            ],
        },
        {
            "title": "Part 2 · People",
            "instructions": "Read the sentences about people. What are the "
                            "missing words? The first letter is already "
                            "there. Write the whole word.",
            "questions": [
                _t("Where do you l _ _ _ , in a flat or in a house?", "live", "ive"),
                _t("My daughters s _ _ _ _ Maths at school.", "study", "tudy"),
                _t("Where do you w _ _ _ – in an office or in a supermarket?",
                   "work", "ork"),
                _t("Every day, the friends g _ to work by bus at 8.00 in the "
                   "morning.", "go", "o"),
                _t("The boys usually p _ _ _ football with their friends on "
                   "Saturday afternoons.", "play", "lay"),
                _t("My parents are from Spain - they s _ _ _ _ Spanish, and "
                   "Italian too.", "speak", "peak"),
            ],
        },
        {
            "title": "Part 3 · People",
            "instructions": "Choose the word to match the picture.",
            "questions": [
                _c("", PEOPLE_A_G, "F", image=U4_IMG + "q13.jpg"),
                _c("", PEOPLE_A_G, "G", image=U4_IMG + "q14.jpg"),
                _c("", PEOPLE_A_G, "B", image=U4_IMG + "q15.jpg"),
                _c("", PEOPLE_A_G, "A", image=U4_IMG + "q16.jpg"),
                _c("", PEOPLE_A_G, "D", image=U4_IMG + "q17.jpg"),
                _c("", PEOPLE_A_G, "E", image=U4_IMG + "q18.jpg"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the text about a woman and her sister. "
                            "Choose the best answer (A, B or C) for each "
                            "space.",
            "passage": """My sister, Yoko

This is a photo of my sister, Yoko, and me. Yoko and I are Japanese. I live in Japan, but she lives in Paris, France. Yoko (19) ………… a lovely family. She is married to Pierre, from France. He speaks French and Japanese.
They have two children: their son Pascal is 10 and their daughter Hana is 8. They speak two languages, too. What time (20) ………… go to school? School is at 9.00 every morning. In the afternoons, Pascal plays the guitar and Hana plays football.
Yoko (21) ………… to work five days a week. Where (22) ………… Yoko and Pierre work? Yoko works in a big hotel in the city centre and Pierre (23) ………… maths at the university near their house. What (24) ………… like to do at the weekend? They like to meet friends and go to the cinema. When they are in Japan, I love to see them! And I love this photo, too.""",
            "questions": [
                _c("", ["has", "to have", "have"], "A"),
                _c("", ["they", "do they", "they do"], "B"),
                _c("", ["goes", "go", "going"], "A"),
                _c("", ["does", "do", "do they"], "B"),
                _c("", ["teach", "to teach", "teaches"], "C"),
                _c("", ["do they", "they do", "they"], "A"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about people. Choose the best "
                            "answer, A, B or C, for each space.",
            "questions": [
                _c("Where ............ work?", ["are you", "you do", "do you"], "C"),
                _c("What time ............ lunch every day?",
                   ["do you have", "you have", "you do have"], "A"),
                _c("When ............ at home?", ["they are", "are they", "do they"], "B"),
                _c("Tom’s flat is big – it ............ ten rooms.",
                   ["have", "having", "has"], "C"),
                _c("Franco ............ his friends at the cinema every Saturday.",
                   ["meet", "meets", "do meet"], "B"),
                _c("My daughter ............ French with her Canadian husband.",
                   ["speaks", "speak", "to speak"], "A"),
            ],
        },
    ],
}


U5_IMG = "/exam-img/step1-u5/"
HOME_A_G = ["a TV", "a shower", "a pillow", "a bed", "a towel", "a bath",
            "a blanket"]

STEP1_UNIT5 = {
    "level": "step1", "kind": "unit", "unit_no": 5,
    "title": "Step 1 · Unit 5 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["There isn’t one.", "Yes, there is.", "It’s lovely."], "A"),
                _c("", ["Yes, thank you.", "They’re lovely.", "Yes, of course."], "C"),
                _c("", ["Yes, there are.", "It’s in this street.", "Certainly."], "B"),
                _c("", ["No, sorry, it isn’t.", "Yes, there are – in this street.", "Thank you."], "B"),
                _c("", ["Can you help please?", "Yes, there is.", "It’s in the next street."], "C"),
                _c("", ["Yes, I do.", "Yes, there is.", "Who’s this?"], "B"),
            ],
        },
        {
            "title": "Part 2 · In a hotel room",
            "instructions": "Choose the word to match the picture.",
            "questions": [
                _c("", HOME_A_G, "F", image=U5_IMG + "q7.jpg"),
                _c("", HOME_A_G, "D", image=U5_IMG + "q8.jpg"),
                _c("", HOME_A_G, "B", image=U5_IMG + "q9.jpg"),
                _c("", HOME_A_G, "E", image=U5_IMG + "q10.jpg"),
                _c("", HOME_A_G, "A", image=U5_IMG + "q11.jpg"),
                _c("", HOME_A_G, "C", image=U5_IMG + "q12.jpg"),
            ],
        },
        {
            "title": "Part 3 · Places",
            "instructions": "Look at the pictures of places. What are the "
                            "missing letters? Some letters are already "
                            "there. Write the whole word.",
            "questions": [
                _t("r _ _ _ _ _ _ _ _ _", "restaurant", "estaurant",
                   image=U5_IMG + "q13.jpg"),
                _t("b _ _ _ _", "beach", "each", image=U5_IMG + "q14.jpg"),
                _t("s _ _ _", "shop", "hop", image=U5_IMG + "q15.jpg"),
                _t("c _ _ _ _ _", "cinema", "inema", image=U5_IMG + "q16.jpg"),
                _t("h _ _ _ _ _ _ _", "hospital", "ospital",
                   image=U5_IMG + "q17.jpg"),
                _t("s _ _ _ _ _ _ _   p _ _ _", "swimming pool",
                   "wimming ool", image=U5_IMG + "q18.jpg"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the text about Diana and her town. Choose "
                            "the best answer (A, B or C) for each space.",
            "passage": """Diana’s Town

My name is Diana. I live in Grandford with my family. Grandford is a small town in England. (19) ………… lots of beautiful old houses in Grandford. (20) ………… a lovely hotel – I work there – and lots of good shops and cafés too. (21) ………… a big swimming pool in Grandford and some very good schools but (22) ………… a university. I like my town. Where do you live? (23) ………… a university in your town? (24) ………… any swimming pools in your town?""",
            "questions": [
                _c("", ["They are", "There is", "There are"], "C"),
                _c("", ["There is", "They are", "There are"], "A"),
                _c("", ["It is", "There is", "There are"], "B"),
                _c("", ["there aren’t", "it isn’t", "there isn’t"], "C"),
                _c("", ["Is there", "Is it", "Are there"], "A"),
                _c("", ["Has it", "Are there", "Is there"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about a city. Choose the best "
                            "answer, A, B or C, for each space.",
            "questions": [
                _c("There ............ a nice restaurant in the city.",
                   ["am", "is", "are"], "B"),
                _c("............ are three good hotels in the city.",
                   ["It", "They", "There"], "C"),
                _c("There ............ two banks on Main Street.",
                   ["has", "is", "are"], "C"),
                _c("............ a swimming pool near the hotel?",
                   ["Is there", "Are there", "Is it"], "A"),
                _c("............ many car parks in the centre of the city.",
                   ["They aren’t", "There isn’t", "There aren’t"], "C"),
                _c("............ any good restaurants on Main Street?",
                   ["Is there", "Are there", "Are they"], "B"),
            ],
        },
    ],
}


STEP1_UNIT6 = {
    "level": "step1", "kind": "unit", "unit_no": 6,
    "title": "Step 1 · Unit 6 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["What's your address?", "I'd like a cup of tea, please.", "That's great, thanks."], "C"),
                _c("", ["Here you are.", "Thanks, but I'm fine.", "But it's really nice."], "B"),
                _c("", ["Don't worry, it's OK.", "I'll come with you.", "Would you like a biscuit?"], "A"),
                _c("", ["There isn't a shop near here.", "No, it's OK, thanks.", "It's very expensive."], "B"),
                _c("", ["Don't worry, I'll come with you.", "No, it's OK, thanks.", "That's great, thanks."], "A"),
                _c("", ["No sorry, there isn't.", "Thanks, but I'm fine.", "Would you like one?"], "C"),
            ],
        },
        {
            "title": "Part 2 · Jobs",
            "instructions": "Read the sentences about jobs and daily life. "
                            "Choose the best answer, A, B or C, for each "
                            "space.",
            "questions": [
                _c("Sarah is a ............ for a large hotel - she welcomes people "
                   "and answers the telephone.", ["receptionist", "chef", "student"], "A"),
                _c("Jo is a ............ in a busy restaurant and she loves her job.",
                   ["student", "shop assistant", "waitress"], "C"),
                _c("My uncle knows the names of all the streets in my town because "
                   "he is a ............ .", ["chef", "taxi driver", "teacher"], "B"),
                _c("Does your maths ............ live near the school?",
                   ["doctor", "waiter", "teacher"], "C"),
                _c("Lisa doesn't sit down at work because she's a ............ .",
                   ["shop assistant", "taxi driver", "bank worker"], "A"),
                _c("Carlos is a ............ – he makes cars.",
                   ["business student", "receptionist", "factory worker"], "C"),
            ],
        },
        {
            "title": "Part 3 · Daily life",
            "instructions": "Read the sentences about daily life. What are the "
                            "missing words? The first letter is already "
                            "there. Write the whole words.",
            "questions": [
                _t("My mother doesn’t h _ _ _  d _ _ _ _ _ because she isn't hungry "
                   "– she usually has a big lunch.", "have dinner", "ave inner"),
                _t("Adam and Tom sometimes g _  t _  w _ _ _ together on the bus "
                   "in the morning.", "go to work", "o o ork"),
                _t("After a long day in the shop, Nadia and Ben f _ _ _ _ _ work "
                   "at 6.00 at night.", "finish", "inish"),
                _t("My friends always g _ _  u _ early every morning – at about 6.00.",
                   "get up", "et p"),
                _t("My parents always h _ _ _  c _ _ _ _ _ to drink at 11 o'clock "
                   "in the morning and tea at 3 o'clock.", "have coffee", "ave offee"),
                _t("What time does Tim s _ _ _ _  w _ _ _ in the factory in the "
                   "morning?", "start work", "tart ork"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the conversation between Rob and Zoe. Zoe "
                            "has a sister, Clare. Rob asks about Clare's life. "
                            "Choose the best answer (A, B or C) for each space.",
            "passage": """Rob: What does your sister do?
Zoe: Clare? She's a teacher but she (19) ………… in a school.
Rob: Where does she work?
Zoe: In a university in the USA.
Rob: (20) ………… the university have lots of students?
Zoe: Yes (21) ………… – about 20,000. She (22) ………… every day but she loves it.
Rob: (23) ………… and see her sometimes?
Zoe: Yes, but she doesn't have a lot of holiday. She has another job – she's a waitress in a small restaurant.
Rob: Really? That's interesting.
Zoe: She (24) ………… it, but she needs the money.
Rob: Oh, and where's the university?
Zoe: In Los Angeles.
Rob: Fantastic!""",
            "questions": [
                _c("", ["don’t work", "not work", "doesn’t work"], "C"),
                _c("", ["Does", "Do", "Is"], "A"),
                _c("", ["it can", "it does", "it is"], "B"),
                _c("", ["doesn't teach", "don't teach", "not teach"], "A"),
                _c("", ["Do you go", "Does she go", "When you go"], "A"),
                _c("", ["don’t like", "doesn't like", "not like"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about daily life. Choose the "
                            "best answer, A, B or C, for each space.",
            "questions": [
                _c("Jill ............ her work because it's boring.",
                   ["doesn’t like", "don’t like", "like"], "A"),
                _c("Oh, this is a chocolate ice cream but Gina ............ eat chocolate.",
                   ["not", "don’t", "doesn't"], "C"),
                _c("David is a university student but ............ usually have "
                   "lunch at the university.", ["there isn’t", "he isn’t", "he doesn’t"], "C"),
                _c("Does your father get up early to go to work? ............",
                   ["Yes, he does.", "Yes, he gets up.", "Yes, he is."], "A"),
                _c("When ............ home in the evening?",
                   ["you get", "do you get", "you do get"], "B"),
                _c("Does the film start at 9.00 p.m.? Yes, ............ .",
                   ["it is", "it does", "it starts"], "B"),
            ],
        },
    ],
}


MID_IMG = "/exam-img/step1-mid/"
ABC = ["A", "B", "C"]
A_G = ["A", "B", "C", "D", "E", "F", "G"]

# Mid-course: Listening (1–20) + Reading (21–45) bitta testda. Reading
# faylidagi raqamlar 20 taga surilgan — matndagi bo'sh joylar ham shunga
# mos, o'quvchi raqamlarni adashtirmasin.
STEP1_MID = {
    "level": "step1", "kind": "mid", "unit_no": None,
    "title": "Step 1 · Mid-course Test (Listening + Reading)",
    "paper_max": 0,
    "parts": [
        {
            "title": "Listening · Part 1",
            "instructions": "You will hear five short conversations. For each "
                            "question, choose the correct picture. You will "
                            "hear each conversation twice.",
            "questions": [
                _c("Where does the woman have lunch?", ABC, "C", image=MID_IMG + "l1.jpg"),
                _c("When does the woman usually have breakfast?", ABC, "B", image=MID_IMG + "l2.jpg"),
                _c("What does the man usually have for lunch?", ABC, "C", image=MID_IMG + "l3.jpg"),
                _c("What drink does the woman order?", ABC, "A", image=MID_IMG + "l4.jpg"),
                _c("Who is Steve’s brother?", ABC, "A", image=MID_IMG + "l5.jpg"),
            ],
        },
        {
            "title": "Listening · Part 2",
            "instructions": "Listen to Joe talking to Claire about his family. "
                            "Which job does each person do? Choose a letter "
                            "A – G. You will hear the conversation twice.",
            "image": MID_IMG + "l_jobs.jpg",
            "questions": [
                _c("Jane", A_G, "D"),
                _c("Becky", A_G, "G"),
                _c("Sam", A_G, "E"),
                _c("Daniel", A_G, "C"),
                _c("Mary", A_G, "F"),
            ],
        },
        {
            "title": "Listening · Part 3",
            "instructions": "You will hear an interview with a woman called "
                            "Lisa Galvani talking about going to other "
                            "countries. For each question choose the correct "
                            "answer. You will hear the conversation twice.",
            "questions": [
                _c("What is Lisa’s job?",
                   ["a waitress", "a receptionist", "a shop assistant"], "B"),
                _c("Where does Lisa want to go first?",
                   ["China", "Brazil", "the USA"], "A"),
                _c("Who can go with Lisa?",
                   ["her husband", "her brother", "her father"], "C"),
                _c("What does Lisa take with her when she goes to another country?",
                   ["a book", "a phone", "an umbrella"], "A"),
                _c("When she gets back home, what does Lisa want to do first?",
                   ["teach in a school", "study at university",
                    "work in another country"], "B"),
            ],
        },
        {
            "title": "Listening · Part 4 · Lisa’s hotel",
            "instructions": "You will hear a girl telling her mother about her "
                            "news. For each question, write the correct answer "
                            "in the gap.",
            "questions": [
                _t("The hotel address: 26 ____________ Road", "Station"),
                _t("The hotel doesn’t have: ____________", "Wi-fi", "wifi"),
                _t("The hotel phone number is: ____________", "829774"),
                _t("The receptionist is from: ____________", "Brazil"),
                _t("The best time to phone is: ____________",
                   "7", "7pm", "7 pm", "7.00", "7:00", "at 7.00",
                   "at 7 o’clock", "7 o’clock", "seven o’clock", "seven"),
            ],
        },
        {
            "title": "Reading · Part 1",
            "instructions": "Read the sentences. Which place is it? Choose a "
                            "letter A – G.",
            "image": MID_IMG + "r_places.jpg",
            "questions": [
                _c("I have breakfast here every day before I go to school.", A_G, "F"),
                _c("I want to go shopping, but first I need to get some money.", A_G, "E"),
                _c("People usually sit here and look at the beautiful flowers "
                   "and trees.", A_G, "G"),
                _c("There are a lot of interesting old things to look at.", A_G, "A"),
                _c("We usually go there on Saturday night to watch something.", A_G, "C"),
            ],
        },
        {
            "title": "Reading · Part 2 · Martin’s daily routine",
            "instructions": "Read the sentences about Martin’s daily routine, "
                            "and choose the correct answer for each gap.",
            "questions": [
                _c("Martin ………… quite far away, so he takes the train to work every day.",
                   ["lives", "goes", "studies"], "A"),
                _c("When Martin is on the train, he likes to read a ………… .",
                   ["phone", "Wi-Fi", "newspaper"], "C"),
                _c("Martin ………… work at 5pm.", ["gets up", "goes", "finishes"], "C"),
                _c("After work, Martin usually goes home to have ………… with his mother.",
                   ["breakfast", "dinner", "lunch"], "B"),
                _c("At the weekend, he likes to play football with friends – he "
                   "is ………… then.", ["happy", "right", "easy"], "A"),
            ],
        },
        {
            "title": "Reading · Part 3 · A Teacher’s Life",
            "instructions": "Read the text about Janet, a teacher, and the "
                            "questions below. For each question, choose the "
                            "correct answer.",
            "passage": """A Teacher’s Life

I’m a teacher and I love my job. It's not an easy job – there are always problems, but it's never boring. I usually arrive at school at 7.30, and so I get up at 6.30. There is a lot of work to do before the students arrive at 8.30.
I need to get there early because sometimes parents come to talk to me before school starts. There are 30 children in my class. When they come to school, they sometimes talk to me about why they aren't happy. I feel sad then, but they also talk about good things and sometimes they are very funny.
Lessons begin at 9.00. Sometimes we read books or newspapers for children, but we usually use computers for reading because the children think they are good fun.
Lunch time starts at 11.55. It's a busy time for the teachers. The children eat lunch together but the teachers stay in their classrooms eating and working because we need to think about the afternoon lessons. We don't usually have time to eat a big lunch, just fruit and a sandwich.
In the afternoon, the children are tired and they don't want to work. We play games or we go to the park. They are happy with their friends.
School finishes at 3.15 and the children go home. Teachers stay to work and I never go home before 5.00; usually it's 7.00. At the end of the day I'm tired but happy.""",
            "questions": [
                _c("Janet gets to work at", ["6.30.", "7.30.", "8.30."], "B"),
                _c("Janet is not happy when",
                   ["there are many children in her class.",
                    "the children’s parents talk to her.",
                    "the children have problems."], "C"),
                _c("At lunchtime the teachers",
                   ["don’t have much time.", "don’t work.", "eat a lot of food."], "A"),
                _c("In the afternoon the children",
                   ["don’t want to study.", "go to sleep.",
                    "don’t play with their friends."], "A"),
                _c("Janet’s day usually finishes at",
                   ["a quarter past three.", "five o’clock.", "seven o’clock."], "C"),
            ],
        },
        {
            "title": "Reading · Part 4 · Bristol",
            "instructions": "Read the text about the city of Bristol in the UK "
                            "and choose the correct answer for each gap.",
            "passage": """Bristol

Bristol is a beautiful small city in the UK, and there are many things to see and do there. It has a lot of small shops – they sell local things. The local people (36) ………… want to shop in the big supermarkets because they (37) ………… like to spend money to help (38) ………… local businesses. (39) ………… a very nice city with lots of trees, and the parks and river are nice places to go for a walk. In many places the (40) ………… are also very old and beautiful.""",
            "questions": [
                _c("", ["isn’t", "aren’t", "don’t"], "C"),
                _c("", ["never", "usually", "every day"], "B"),
                _c("", ["their", "his", "our"], "A"),
                _c("", ["He’s", "They’re", "It’s"], "C"),
                _c("", ["house", "houses", "house’s"], "B"),
            ],
        },
        {
            "title": "Reading · Part 5 · Dear Phil",
            "instructions": "Read the text. Think of the word which best fits "
                            "each gap. Write ONE word for each gap.",
            "passage": """Dear Phil,

Hi, how are you? I am at a language school in Italy now. (41) ………… are lots of students in my class – all from different countries. There (42) ………… any other English people – only me. My teacher’s name is Sara. She is very good. The lessons are interesting but they are sometimes difficult. I speak a lot of Italian because she (43) ………… speak English in class with us. I see Sara every day because she lives near my hotel. I like the food here but Italian people usually (44) ………… dinner in restaurants very late, sometimes at 10 o’clock at night! (45) ………… you like Italian food?

Best wishes,
Cathy""",
            "questions": [
                _t("", "There"),
                _t("", "aren’t", "are not"),
                _t("", "doesn’t", "does not", "can’t", "cannot"),
                _t("", "eat", "have"),
                _t("", "Do"),
            ],
        },
    ],
}


U7_IMG = "/exam-img/step1-u7/"
THINGS_A_G = ["clock", "bag", "chair", "lamp", "glass", "cup", "plate"]

STEP1_UNIT7 = {
    "level": "step1", "kind": "unit", "unit_no": 7,
    "title": "Step 1 · Unit 7 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["They’re £2 each.", "No, sorry, they aren’t.", "I’d like four of these cups, please."], "A"),
                _c("", ["Certainly.", "Thank you.", "Don’t worry."], "A"),
                _c("", ["Can I help you?", "Thank you, that’s very kind.", "Of course."], "C"),
                _c("", ["Thank you, that’s very kind.", "Here you are.", "Nice to meet you."], "B"),
                _c("", ["Can I help you?", "That’s great, thanks.", "OK, no problem."], "C"),
                _c("", ["No, I’m sorry. We only have two.", "That’s a good price.", "It’s three pounds for the small ones."], "C"),
            ],
        },
        {
            "title": "Part 2 · Things",
            "instructions": "Choose the word to match the picture.",
            "questions": [
                _c("", THINGS_A_G, "E", image=U7_IMG + "q7.jpg"),
                _c("", THINGS_A_G, "D", image=U7_IMG + "q8.jpg"),
                _c("", THINGS_A_G, "A", image=U7_IMG + "q9.jpg"),
                _c("", THINGS_A_G, "G", image=U7_IMG + "q10.jpg"),
                _c("", THINGS_A_G, "B", image=U7_IMG + "q11.jpg"),
                _c("", THINGS_A_G, "C", image=U7_IMG + "q12.jpg"),
            ],
        },
        {
            "title": "Part 3 · Clothes",
            "instructions": "Look at the pictures of clothes. What are the "
                            "missing letters? Some letters are already "
                            "there. Write the whole words.",
            "questions": [
                _t("t _ _ _ _ _ _ _", "trousers", "rousers", image=U7_IMG + "q13.jpg"),
                _t("a s _ _ _ _", "skirt", "kirt", image=U7_IMG + "q14.jpg"),
                _t("a white d _ _ _ _", "dress", "ress", image=U7_IMG + "q15.jpg"),
                _t("a g _ _ _ _  h _ _", "green hat", "reen at",
                   image=U7_IMG + "q16.jpg"),
                _t("a light b _ _ _  j _ _ _ _ _", "blue jacket", "lue acket",
                   image=U7_IMG + "q17.jpg"),
                _t("d _ _ _  brown s _ _ _ _", "dark shoes", "ark hoes",
                   "dark brown shoes", image=U7_IMG + "q18.jpg"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read about a shop. Choose the best answer, A, B "
                            "or C, for each space.",
            "passage": """Fred the Fashion Man

I like fashion, and on Saturdays I often work in my (19) ………… shop. His name is Fred, and the name of the shop is ‘Fred the Fashion Man’.
(20) ………… is a good name, because the shop sells (21) ………… jeans, trousers, jackets and shirts. The clothes aren’t expensive, and a lot of young people buy them.
The clothes in the shop are interesting and different, but (22) ………… clothes are boring. Fred always wears a black T-shirt and black trousers. Sometimes I see some jeans in the shop and I say to my brother ‘I like (23) ………… red jeans. Why don’t you wear them?’ or ‘I like (24) ………… yellow shirt. Why don’t you wear it?’ But Fred always says ‘No, I like my black T-shirt and jeans.’""",
            "questions": [
                _c("", ["brothers", "brother", "brother’s"], "C"),
                _c("", ["This", "There", "These"], "A"),
                _c("", ["men’s", "man’s", "men"], "A"),
                _c("", ["Freds", "Freds’", "Fred’s"], "C"),
                _c("", ["that", "those", "this"], "B"),
                _c("", ["those", "these", "that"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about clothes. Choose the best "
                            "answer, A, B or C, for each space.",
            "questions": [
                _c("I’d like one of ............ T-shirts.", ["that", "this", "these"], "C"),
                _c("Is ............ a new coat?", ["that", "these", "those"], "A"),
                _c("Look. ............ is my new shirt. Do you like it?",
                   ["These", "Those", "This"], "C"),
                _c("What colour are ............ new shoes?", ["Mark", "Mark’s", "Marks’"], "B"),
                _c("At the school the boys have blue shirts but the ............ "
                   "dresses are green.", ["girls’", "girl", "girl’s"], "A"),
                _c("These new shoes are for ............ party.",
                   ["Tom and Lucy", "Tom’s and Lucy", "Tom and Lucy’s"], "C"),
            ],
        },
    ],
}


U8_IMG = "/exam-img/step1-u8/"
FREE_TIME_A_G = ["play a computer game", "listen to music", "go shopping",
                 "watch a football match", "read a magazine",
                 "play the guitar", "have a drink"]

STEP1_UNIT8 = {
    "level": "step1", "kind": "unit", "unit_no": 8,
    "title": "Step 1 · Unit 8 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Good afternoon.", "Can I help you?", "Yes, that’s a lovely idea."], "C"),
                _c("", ["Yes, OK. Good idea.", "Can I look around?", "It’s really nice."], "A"),
                _c("", ["Thanks, but I’m fine.", "Nice to meet you.", "I’m sorry, I can’t."], "C"),
                _c("", ["It’s really nice.", "No, sorry, there isn’t.", "That’s a great idea."], "C"),
                _c("", ["OK, that’s a nice idea.", "They’re lovely.", "Here you are."], "A"),
                _c("", ["Shall we go to a party?", "OK, that’s a lovely idea.", "I’d like a piece of chocolate cake, please."], "B"),
            ],
        },
        {
            "title": "Part 2 · Free time",
            "instructions": "Choose the words to match the picture.",
            "questions": [
                _c("", FREE_TIME_A_G, "D", image=U8_IMG + "q7.jpg"),
                _c("", FREE_TIME_A_G, "E", image=U8_IMG + "q8.jpg"),
                _c("", FREE_TIME_A_G, "F", image=U8_IMG + "q9.jpg"),
                _c("", FREE_TIME_A_G, "C", image=U8_IMG + "q10.jpg"),
                _c("", FREE_TIME_A_G, "A", image=U8_IMG + "q11.jpg"),
                _c("", FREE_TIME_A_G, "G", image=U8_IMG + "q12.jpg"),
            ],
        },
        {
            "title": "Part 3 · Past time",
            "instructions": "Read the sentences about past events. What are "
                            "the missing words? The first letter is already "
                            "there. Write the whole words.",
            "questions": [
                _t("Sam is at school today but he wasn’t at school "
                   "y _ _ _ _ _ _ _ _ .", "yesterday", "esterday"),
                _t("Lucy went shopping o _  W _ _ _ _ _ _ _ _ .",
                   "on Wednesday", "n ednesday"),
                _t("My family had a holiday in Spain two y _ _ _ _  a _ _ .",
                   "years ago", "ears go"),
                _t("My friends and I played a great computer game "
                   "o _  S _ _ _ _ _ _ _ .", "on Saturday", "n aturday"),
                _t("John is tired now because he played football "
                   "t _ _ _  a _ _ _ _ _ _ _ _ .", "this afternoon", "his fternoon"),
                _t("We went to a good party l _ _ _  n _ _ _ _ .",
                   "last night", "ast ight"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the text about a band on tour. Choose the "
                            "best answer, A, B or C, for each space.",
            "passage": """On tour with my band

I play guitar in a band. Our name’s The Musicmakers. We often go away on tour. Last year we (19) ………… on the road in Spain. We (20) ………… in Madrid first and the band played at concerts in three different Spanish cities in five days: in Madrid and Bilbao on Tuesday, Wednesday and Thursday and then in Barcelona on Friday and Saturday.
I love Spanish food – we (21) ………… to some great restaurants. They (22) ………… very expensive. We (23) ………… some interesting things in the museums. Spain has a lot of good museums – The Prado in Madrid, the Guggenheim Museum in Bilbao, and the Picasso Museum in Barcelona. It (24) ………… fun to travel there with the band.""",
            "questions": [
                _c("", ["be", "are", "were"], "C"),
                _c("", ["arrive", "arrived", "arrives"], "B"),
                _c("", ["go", "went", "goes"], "B"),
                _c("", ["aren’t", "wasn’t", "weren’t"], "C"),
                _c("", ["saw", "see", "sees"], "A"),
                _c("", ["be", "was", "weren’t"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about past events. Choose the "
                            "best answer, A, B or C, for each space.",
            "questions": [
                _c("Where ............ you yesterday?", ["was", "were", "are"], "B"),
                _c("‘Were you at the café last night?’ ‘No, we ............ .’",
                   ["isn’t", "wasn’t", "weren’t"], "C"),
                _c("Laura ............ in the garden, but she isn’t there now.",
                   ["is", "does", "was"], "C"),
                _c("We usually stay at home in the evening, but last Monday we "
                   "............ football.", ["play", "plays", "played"], "C"),
                _c("They ............ a very nice pizza in the restaurant last night.",
                   ["had", "have", "has"], "A"),
                _c("I ............ to Madrid two years ago.", ["went", "go", "was"], "A"),
            ],
        },
    ],
}


U9_IMG = "/exam-img/step1-u9/"

STEP1_UNIT9 = {
    "level": "step1", "kind": "unit", "unit_no": 9,
    "title": "Step 1 · Unit 9 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Of course.", "Don’t worry, it’s OK.", "They’re three pounds each."], "A"),
                _c("", ["I’m sorry, I can’t.", "No, it’s OK, thanks.", "Thanks, but I’m fine."], "A"),
                _c("", ["Here you are.", "Yes, I do.", "Sure, no problem."], "C"),
                _c("", ["OK, no problem.", "Thanks, that’s really kind of you.", "It’s really nice."], "B"),
                _c("", ["No, sorry, there aren’t.", "That’s great, thanks.", "Yes, certainly."], "C"),
                _c("", ["That’s great, thanks.", "No, I can’t.", "Sorry, what’s the spelling?"], "B"),
            ],
        },
        {
            "title": "Part 2 · Transport",
            "instructions": "Look at the transport pictures. What are the "
                            "missing letters? Some letters are already there. "
                            "Write the whole words.",
            "questions": [
                _t("t _ _ _ _", "train", "rain", image=U9_IMG + "q7.jpg"),
                _t("b _ _ _", "bike", "ike", image=U9_IMG + "q8.jpg"),
                _t("g _ _  a  t _ _ _", "get a taxi", "et axi", image=U9_IMG + "q9.jpg"),
                _t("t _ _ _  a  b _ _", "take a bus", "ake us", image=U9_IMG + "q10.jpg"),
                _t("f _ _", "fly", "ly", image=U9_IMG + "q11.jpg"),
                _t("d _ _ _ _", "drive", "rive", image=U9_IMG + "q12.jpg"),
            ],
        },
        {
            "title": "Part 3 · Weather",
            "instructions": "Read the sentences about weather. What are the "
                            "missing words? The first letter is already "
                            "there. Write the whole word.",
            "questions": [
                _t("I wear a big coat when it’s really c _ _ _ .",
                   "cold", "old", "cool", "ool"),
                _t("It’s very grey and c _ _ _ _ _ today. I can’t see the sun.",
                   "cloudy", "loudy"),
                _t("We camped last night but it was really w _ _ _ _ so we "
                   "didn’t sleep well.", "windy", "indy"),
                _t("On our holiday it was hot and s _ _ _ _ so we went to the "
                   "beach every day.", "sunny", "unny"),
                _t("I went to Antarctica last year and there was lots of "
                   "s _ _ _ so everything was white!", "snow", "now"),
                _t("The four seasons are spring, summer, a _ _ _ _ _ and winter.",
                   "autumn", "utumn"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read this interview with Angie about her holiday "
                            "in India. Choose the best answer, A, B or C, for "
                            "each space.",
            "passage": """A holiday in India

Interviewer: Where did you go on holiday last year?
Angie: I went to India for the first time. It was great and I want to go back one day.
Interviewer: Who (19) ………… to India with?
Angie: My husband came with me. We flew from England and it took about 9 hours by plane. In India, (20) ………… but we took buses and trains to travel around. We met lots of friendly people.
Interviewer: Where (21) …………?
Angie: We stayed in hotels, which were all really good.
Interviewer: (22) ………… in spring?
Angie: Yes, so every day was warm and sunny. (23) ………… when we were there.
Interviewer: Did you like the food?
Angie: Yes, we did. We ate in our hotel some nights and other nights we ate in restaurants. (24) ………… time to see everything but it was a great holiday.""",
            "questions": [
                _c("", ["did you travel", "you travelled", "travelled"], "A"),
                _c("", ["we drove", "we didn’t drive", "we did drive"], "B"),
                _c("", ["do you stay", "did you stay", "you stayed"], "B"),
                _c("", ["You didn’t go", "You went", "Did you go"], "C"),
                _c("", ["It didn’t rain", "It rains", "Did it rain"], "A"),
                _c("", ["We haven’t", "Did we have", "We didn’t have"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about travel. Choose the best "
                            "answer, A, B or C, for each space.",
            "questions": [
                _c("They didn’t ............ a bus to the station.", ["took", "take", "takes"], "B"),
                _c("She didn’t ............ to the airport by train.", ["goes", "went", "go"], "C"),
                _c("We ............ stay in a hotel on our summer holiday last year.",
                   ["don’t", "doesn’t", "didn’t"], "C"),
                _c("What ............ on holiday?",
                   ["you saw", "did you see", "you didn’t see"], "B"),
                _c("Did he ............ to the station?", ["drive", "drove", "drives"], "A"),
                _c("Did she travel by plane? No, she ............ .", ["don’t", "didn’t", "did"], "B"),
            ],
        },
    ],
}


U10_IMG = "/exam-img/step1-u10/"
HOUSE_A_G = ["bedroom", "door", "kitchen", "wall", "window", "living room",
             "bathroom"]

STEP1_UNIT10 = {
    "level": "step1", "kind": "unit", "unit_no": 10,
    "title": "Step 1 · Unit 10 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Shall we go on Sunday?", "The bus leaves in three minutes.", "What time’s the next bus to London?"], "C"),
                _c("", ["No, sorry, there isn’t.", "It’s at 8.25.", "You change buses at Oxford."], "B"),
                _c("", ["It’s stop 4, near the ticket office.", "The next bus is at 3.30.", "I can go with you."], "A"),
                _c("", ["It’s platform 6.", "I’ll come with you.", "It leaves in three minutes."], "C"),
                _c("", ["Oh, OK, I’ll do it then.", "No, you change at Manchester.", "Yes, please."], "B"),
                _c("", ["Which platform is it?", "No, sorry, there isn’t.", "Can you spell that?"], "A"),
            ],
        },
        {
            "title": "Part 2 · In the house",
            "instructions": "Choose the word to match the picture.",
            "questions": [
                _c("", HOUSE_A_G, "C", image=U10_IMG + "q7.jpg"),
                _c("", HOUSE_A_G, "G", image=U10_IMG + "q8.jpg"),
                _c("", HOUSE_A_G, "A", image=U10_IMG + "q9.jpg"),
                _c("", HOUSE_A_G, "F", image=U10_IMG + "q10.jpg"),
                _c("", HOUSE_A_G, "B", image=U10_IMG + "q11.jpg"),
                _c("", HOUSE_A_G, "E", image=U10_IMG + "q12.jpg"),
            ],
        },
        {
            "title": "Part 3 · Places",
            "instructions": "Read the sentences about places. Choose the best "
                            "answer, A, B or C, for each space.",
            "questions": [
                _c("I left my phone ............ a train.", ["on", "to", "at"], "A"),
                _c("Let’s meet for lunch ............ a restaurant.", ["in", "to", "on"], "A"),
                _c("Could you meet me ............ the airport, please?", ["on", "at", "to"], "B"),
                _c("Marek’s ............ holiday in Norway.", ["on", "in", "at"], "A"),
                _c("Laura’s ............ work now so please call later.", ["on", "at", "in"], "B"),
                _c("I’m having breakfast in the garden but Paul’s still ............ bed.",
                   ["at", "on", "in"], "C"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the email about a holiday in Colombia. Choose "
                            "the best answer, A, B or C, for each space.",
            "passage": """On holiday in Colombia
From: Anna
To: Mimi

Hi Mimi

Hello from sunny Colombia! How are you? Are you at home today or (19) …………? I hope you’re well. Our holiday here in Colombia is great. Colombia is a beautiful country, and the people are really friendly.
Right now, (20) ………… in a café, drinking a coffee. The weather was cloudy here yesterday, but today it’s warm and sunny, and (21) ………… . That’s good because I don’t like rain! The café is on the beach, so (22) ………… this email and I can see the sea at the same time. There are lots of people on the beach and some people (23) ………… . It’s a great view.
We arrived in this town yesterday. We came by bus, which took four hours. (24) ………… in a hotel because it’s quite expensive, so we’re in a hostel for three nights. It’s lovely.

See you soon.
Anna""",
            "questions": [
                _c("", ["you work", "you’re working", "are you working"], "C"),
                _c("", ["are we sitting", "we’re sitting", "we aren’t sitting"], "B"),
                _c("", ["is it raining", "it isn’t raining", "it’s raining"], "B"),
                _c("", ["I’m not writing", "am I writing", "I’m writing"], "C"),
                _c("", ["swimming", "is swimming", "are swimming"], "C"),
                _c("", ["Are we staying", "We’re not staying", "We are staying"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about here and now. Choose the "
                            "best answer, A, B or C, for each space.",
            "questions": [
                _c("I’ll call you later, we ............ having dinner now.", ["’re", "’s", "’m"], "A"),
                _c("Hurry up, ............ for you at the bus stop.",
                   ["are they waiting", "they aren’t waiting", "they’re waiting"], "C"),
                _c("Sandro ............ cooking dinner at the moment.", ["’m", "’re", "’s"], "C"),
                _c("............ now – why don’t we sit in the garden?",
                   ["It isn’t raining now", "Is it raining", "It’s raining"], "A"),
                _c("Sarah, what ............ at the moment?",
                   ["you are doing", "are you doing", "you aren’t doing"], "B"),
                _c("I ............ today because it’s the weekend.",
                   ["not working", "’m not working", "isn’t working"], "B"),
            ],
        },
    ],
}


U11_IMG = "/exam-img/step1-u11/"
ACTIVITY_A_G = ["ride a bike", "cook dinner", "drive a car", "play tennis",
                "ride a horse", "play cards", "run"]

STEP1_UNIT11 = {
    "level": "step1", "kind": "unit", "unit_no": 11,
    "title": "Step 1 · Unit 11 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Yes, it’s in this street.", "How can I help?", "It’s really nice."], "C"),
                _c("", ["I’m not so sure.", "How are you?", "Yes, please."], "A"),
                _c("", ["Don’t worry, it’s OK.", "Can I look around?", "I don’t think it’s a good idea."], "C"),
                _c("", ["Oh, not bad, thanks.", "Yes, I agree.", "Sure, no problem."], "B"),
                _c("", ["I don’t think so.", "I’m sorry, I can’t.", "No, it’s OK, thanks."], "A"),
                _c("", ["That’s great, thanks.", "I think you’re right.", "Yes, that’s a good idea."], "B"),
            ],
        },
        {
            "title": "Part 2 · Activities",
            "instructions": "Choose the words to match the picture.",
            "questions": [
                _c("", ACTIVITY_A_G, "F", image=U11_IMG + "q7.jpg"),
                _c("", ACTIVITY_A_G, "C", image=U11_IMG + "q8.jpg"),
                _c("", ACTIVITY_A_G, "E", image=U11_IMG + "q9.jpg"),
                _c("", ACTIVITY_A_G, "A", image=U11_IMG + "q10.jpg"),
                _c("", ACTIVITY_A_G, "G", image=U11_IMG + "q11.jpg"),
                _c("", ACTIVITY_A_G, "D", image=U11_IMG + "q12.jpg"),
            ],
        },
        {
            "title": "Part 3 · Life events",
            "instructions": "Look at the pictures of life events. What are the "
                            "missing letters? Some letters are already there. "
                            "Write the whole words.",
            "questions": [
                _t("g _ _  m _ _ _ _ _ _", "get married", "et arried",
                   image=U11_IMG + "q13.jpg"),
                _t("h _ _ _  a  b _ _ _", "have a baby", "ave baby", "ave aby",
                   image=U11_IMG + "q14.jpg"),
                _t("g _  to  s _ _ _ _ _", "go to school", "o chool",
                   image=U11_IMG + "q15.jpg"),
                _t("f _ _ _ _ _  u _ _ _ _ _ _ _ _ _", "finish university",
                   "inish niversity", image=U11_IMG + "q16.jpg"),
                _t("g _ _ _  u _", "grow up", "row p", image=U11_IMG + "q17.jpg"),
                _t("s _ _ _  w _ _ _ _ _ _", "stop working", "top orking",
                   image=U11_IMG + "q18.jpg"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the email from Sally to a friend. Choose the "
                            "best answer, A, B or C, for each space.",
            "passage": """Working in a hotel
From: Sally
To: Philip

Dear Philip

How are you? Did you finish university last month and are you looking for a job now? Well, why don’t you come and work with (19) ………… at the hotel? I love working there! I think there’s a job in the kitchen, but it’s not a good job for you because you (20) ………… cook very well. Sorry, but it’s true!
Do you want to be a receptionist? That’s my job. It’s really interesting. I speak three languages so I (21) ………… talk to people from different countries. What about you? (22) ………… any other languages?
I work with some very friendly people. Do you want to come to the hotel tomorrow night and meet (23) …………? We usually all go out for a meal together – would you like to come with (24) …………? We always have a lot of fun!

See you tomorrow at about 6 o’clock?
Love, Sally""",
            "questions": [
                _c("", ["me", "I", "my"], "A"),
                _c("", ["can", "not", "can’t"], "C"),
                _c("", ["can", "cannot", "do"], "A"),
                _c("", ["You can speak", "Can you speak", "You can’t speak"], "B"),
                _c("", ["them", "it", "they"], "A"),
                _c("", ["we", "her", "us"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about people. Choose the best "
                            "answer, A, B or C, for each space.",
            "questions": [
                _c("Your husband is very nice, where did you meet ............?",
                   ["him", "you", "he"], "A"),
                _c("Mary and Peter go to your school, do you know ............?",
                   ["us", "them", "they"], "B"),
                _c("I love this book, I first read ............ at university.",
                   ["her", "them", "it"], "C"),
                _c("Rodolfo can sing really well but he can’t ............ .",
                   ["dancing", "dance", "to dance"], "B"),
                _c("Sally, ............ play the piano?", ["you can", "can you", "can"], "B"),
                _c("Yes, she ............ speak French very well.", ["can", "can’t", "do"], "A"),
            ],
        },
    ],
}


U12_IMG = "/exam-img/step1-u12/"

STEP1_UNIT12 = {
    "level": "step1", "kind": "unit", "unit_no": 12,
    "title": "Step 1 · Unit 12 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear six short sentences. For each one, "
                            "choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Thank you.", "Maybe you’re right.", "No, sorry, I’m going to a party."], "C"),
                _c("", ["I’d love to come. Thank you.", "I think you’re right.", "Which platform is it?"], "A"),
                _c("", ["Yes, it is.", "Are you free on Friday?", "Great, come on Friday."], "C"),
                _c("", ["I agree.", "Sorry, I’m busy then, but Sunday’s OK.", "It’s very nice."], "B"),
                _c("", ["Yes, please.", "Don’t worry, it’s OK.", "Sure."], "C"),
                _c("", ["Here you are.", "Thanks, but I’m fine.", "Great!"], "C"),
            ],
        },
        {
            "title": "Part 2 · Things to do",
            "instructions": "Look at the pictures. What are the missing "
                            "letters? Some letters are already there. Write "
                            "the whole words.",
            "questions": [
                _t("d _  y _ _ _  h _ _ _ _ _ _ _ _", "do your homework",
                   "o our omework", image=U12_IMG + "q7.jpg"),
                _t("g _  to the  b _ _ _ _", "go to the beach", "o each",
                   "o to the each", image=U12_IMG + "q8.jpg"),
                _t("u _ _  a  c _ _ _ _ _ _ _", "use a computer", "se omputer",
                   "se a omputer", image=U12_IMG + "q9.jpg"),
                _t("d _  the  w _ _ _ _ _ _", "do the washing", "o ashing",
                   "o the ashing", image=U12_IMG + "q10.jpg"),
                _t("v _ _ _ _  a  m _ _ _ _ _", "visit a museum", "isit useum",
                   "isit a useum", image=U12_IMG + "q11.jpg"),
                _t("c _ _ _ _  a  r _ _ _", "clean a room", "lean oom",
                   "lean a oom", image=U12_IMG + "q12.jpg"),
            ],
        },
        {
            "title": "Part 3 · Future plans",
            "instructions": "Read the sentences about future plans. What are "
                            "the missing words? The first letter is already "
                            "there. Write the whole words.",
            "questions": [
                _t("I’m going to go to a New Year party in New York on 31st "
                   "D _ _ _ _ _ _ _ .", "December", "ecember"),
                _t("There are no tickets for Thursday so let’s go "
                   "o _  F _ _ _ _ _ .", "on Friday", "n riday"),
                _t("F _ _ _ _ _ _ _ is going to be a busy month, so I can’t see "
                   "you until March.", "February", "ebruary"),
                _t("I’m having lunch at the moment but you can come and see me "
                   "t _ _ _  a _ _ _ _ _ _ _ _ .", "this afternoon", "his fternoon"),
                _t("Her birthday’s on the fourth of May, but the party’s a day "
                   "later on the f _ _ _ _ .", "fifth", "ifth"),
                _t("My birthday is n _ _ _  S _ _ _ _ _ _ _ but I’m going to "
                   "have my party on Sunday.", "next Saturday", "ext aturday"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read an interview with James Edwards about his "
                            "job. Choose the best answer, A, B or C, for each "
                            "space.",
            "passage": """A holiday in the Sahara

Interviewer: James, you take people on unusual and exciting holidays. Where’s the next one?
James: Well, for the first time, I (19) ………… going to take people to the Sahara desert.
Interviewer: Great! How many people (20) ………… going to be on this trip?
James: About 10 people on holiday and lots of other people to help.
Interviewer: And how (21) ………… going to travel? By car?
James: Oh, no! We’re going to (22) …………!
Interviewer: Oh! And what about sleeping?
James: Well, we (23) ………… going to sleep in hotels! The tourists all sleep in a big tent. There’s water in the Sahara for washing.
Interviewer: And (24) ………… going to enjoy that?
James: Oh yes! People love holidays like this. They think they’re fantastic!""",
            "questions": [
                _c("", ["’s", "’m", "’re"], "B"),
                _c("", ["is", "are", "am"], "B"),
                _c("", ["you’re", "you are", "are you"], "C"),
                _c("", ["walking", "walk", "walks"], "B"),
                _c("", ["aren’t", "can’t", "don’t"], "A"),
                _c("", ["they aren’t", "they are", "are they"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about future plans. Choose the "
                            "best answer, A, B or C, for each space.",
            "questions": [
                _c("We’re going to ............ a party on Saturday.", ["had", "have", "having"], "B"),
                _c("Rebecca ............ going to go out with Peter because he’s too boring.",
                   ["isn’t", "doesn’t", "can’t"], "A"),
                _c("I’m ............ read this book at the weekend.",
                   ["going to", "go to", "going"], "A"),
                _c("Claire, ............ going to meet Chris later?", ["you", "you are", "are you"], "C"),
                _c("............ they going to invite Rashid to the party?", ["Have", "Do", "Are"], "C"),
                _c("Who ............ going to go to London this weekend?", ["am", "is", "are"], "B"),
            ],
        },
    ],
}


END_IMG = "/exam-img/step1-end/"

# End of course: Listening (1–20) + Reading (21–45) bitta testda —
# Mid-course bilan bir xil tartib. Reading raqamlari 20 taga surilgan.
STEP1_END = {
    "level": "step1", "kind": "end", "unit_no": None,
    "title": "Step 1 · End of course Test (Listening + Reading)",
    "paper_max": 0,
    "parts": [
        {
            "title": "Listening · Part 1",
            "instructions": "You will hear five short conversations. For each "
                            "question, choose the correct picture. You will "
                            "hear each conversation twice.",
            "questions": [
                _c("Where’s the man from?", ABC, "B", image=END_IMG + "l1.jpg"),
                _c("How much was the woman’s dress?", ABC, "C", image=END_IMG + "l2.jpg"),
                _c("What job does the woman do now?", ABC, "B", image=END_IMG + "l3.jpg"),
                _c("How did Elena’s parents meet?", ABC, "C", image=END_IMG + "l4.jpg"),
                _c("What’s Dermot going to do first?", ABC, "A", image=END_IMG + "l5.jpg"),
            ],
        },
        {
            "title": "Listening · Part 2",
            "instructions": "You will hear Jasper talking to a friend about the "
                            "presents he bought for people in his family. "
                            "Which present did Jasper buy for each person? "
                            "Choose a letter A – G. You will hear the "
                            "conversation twice.",
            "image": END_IMG + "l_presents.jpg",
            "questions": [
                _c("wife", A_G, "D"),
                _c("mother", A_G, "B"),
                _c("son", A_G, "F"),
                _c("sister", A_G, "A"),
                _c("father", A_G, "G"),
            ],
        },
        {
            "title": "Listening · Part 3",
            "instructions": "You will hear a woman called Megan talking about "
                            "her holiday in Dublin. For each question, choose "
                            "the correct answer. You will hear the "
                            "conversation twice.",
            "questions": [
                _c("When did Megan go to Dublin?",
                   ["two months ago", "two weeks ago", "one week ago"], "A"),
                _c("Megan went to Dublin in", ["spring.", "summer.", "autumn."], "C"),
                _c("Why did Megan stay at the Camilla hotel?",
                   ["It was big.", "It was very cheap.", "It was near the station."], "C"),
                _c("Megan’s favourite meal was", ["breakfast.", "lunch.", "dinner."], "A"),
                _c("What present did Megan buy for her brother?",
                   ["a T-shirt", "a camera", "a book"], "B"),
            ],
        },
        {
            "title": "Listening · Part 4 · Henley Summer School",
            "instructions": "You will hear a man called Andy talking about a "
                            "summer school for teenage students. For each "
                            "question, write the correct answer in the gap. "
                            "You will hear the recording twice.",
            "questions": [
                _t("Students from: Italy, ____________ and Brazil", "Spain"),
                _t("Kilometres from London: ____________",
                   "25", "twenty-five", "twenty five", "25 km",
                   "25 kilometres", "25 kilometre"),
                _t("Month school opens: ____________", "June"),
                _t("Subject of morning class: ____________", "English"),
                _t("Time afternoon classes finish: ____________ o’clock",
                   "4", "four", "4:00", "at 4", "at four", "at 4:00",
                   "4 o’clock", "four o’clock"),
            ],
        },
        {
            "title": "Reading · Part 1",
            "instructions": "Read the sentences. Which picture is it? Choose a "
                            "letter A – G.",
            "image": END_IMG + "r_food.jpg",
            "questions": [
                _c("You go here to buy food.", A_G, "B"),
                _c("You can cook here in your house.", A_G, "E"),
                _c("We are going to cook this meat before we eat it.", A_G, "A"),
                _c("There are lots of nice dishes on the menu here.", A_G, "G"),
                _c("These people are going to cook your meal.", A_G, "D"),
            ],
        },
        {
            "title": "Reading · Part 2 · Carl",
            "instructions": "Read the sentences about Carl, and choose the "
                            "correct answer for each gap.",
            "questions": [
                _c("Carl is a student but he ………… at a hotel every Saturday.",
                   ["works", "arrives", "watches"], "A"),
                _c("Carl ………… up at 6 o’clock every Saturday.", ["has", "goes", "gets"], "C"),
                _c("Carl ………… the cleaning in the hotel.", ["makes", "does", "uses"], "B"),
                _c("In the hotel, it’s very hot in summer and very cold in ………… .",
                   ["spring", "autumn", "winter"], "C"),
                _c("Carl usually has a ………… of coffee with his friends after work.",
                   ["cup", "plate", "spoon"], "A"),
            ],
        },
        {
            "title": "Reading · Part 3 · Three cooks",
            "instructions": "Read the text about three cooks and the questions "
                            "below. For each question, choose the correct "
                            "answer.",
            "passage": """Matt
Cooking was not important to me when I was young. My mum was a good cook but it was boring for me and we didn’t learn cooking at school. When I finished school, I worked on a boat. I went to Italy, Spain and Japan and I learned about different food. I came home, went to college and read all the new cookbooks. Then I got a job in a hotel restaurant. Next month my new restaurant will open in Paris!

Antonio
I love all food – Chinese, Russian, Brazilian! Mum and Dad both cooked great food when I was young and I liked helping them. There were no cooking lessons at my school but I always helped Mum cook dinner on Sundays. Then I found some of her cookbooks. They were over seventy years old and really interesting. Now I have my own school for students of cooking and sometimes I use Mum’s books in my lessons!

James
I didn’t like a lot of subjects at school. They were so boring! But I loved the cooking lessons. The teacher was great and we cooked lots of different things – fish, pizza, biscuits. We never read books! We visited new restaurants in town and ate food from different countries. Now I am a writer! I wrote my first book six years ago. It was about cooking for children, with lots of ideas. My next one is going to be about fish.""",
            "questions": [
                _c("Who learned to cook at home?", ["Matt", "Antonio", "James"], "B"),
                _c("Who travelled to different countries?", ["Matt", "Antonio", "James"], "A"),
                _c("Who is going to have a new restaurant soon?", ["Matt", "Antonio", "James"], "A"),
                _c("Who writes books about cooking?", ["Matt", "Antonio", "James"], "C"),
                _c("Who teaches cooking?", ["Matt", "Antonio", "James"], "B"),
            ],
        },
        {
            "title": "Reading · Part 4 · Holidays with my brother",
            "instructions": "Read the text about a holiday and choose the "
                            "correct answer for each gap.",
            "passage": """Holidays with my brother

Last year, I went to Italy with my brother. We (36) ………… around the country for three weeks. First, we went to the beach. We can swim quite well and we really enjoyed the hot weather. Then we went to the mountains. (37) ………… was no snow but it was cold. We walked to a beautiful village.
Every morning we (38) ………… breakfast in the hotel. Then we bought food at a supermarket and made sandwiches for lunch. Every evening we ate at a different restaurant. Next year, in July, my brother and I (39) ………… drive to Spain on holiday. Holidays with (40) ………… are always great.""",
            "questions": [
                _c("", ["travelling", "travelled", "travels"], "B"),
                _c("", ["There", "That", "They"], "A"),
                _c("", ["having", "has", "had"], "C"),
                _c("", ["are going", "going", "are going to"], "C"),
                _c("", ["him", "he", "his"], "A"),
            ],
        },
        {
            "title": "Reading · Part 5 · Hi Molly!",
            "instructions": "Read the text. Think of the word which best fits "
                            "each gap. Write ONE word for each gap.",
            "passage": """From: Susan
To: Molly

Hi Molly!
How are you? I (41) ………… really enjoying university. My room has big windows. It’s beautiful! Yesterday evening, there was a party at my friend’s house. I met lots of interesting people. I met a nice boy. (42) ………… name is Ralph. He plays the guitar in a band.
I’m very happy because you are (43) ………… to visit me next Friday. When (44) ………… your bus arrive at the bus station? I can meet you in the afternoon on Friday but (45) ………… meet in the morning, because I have classes then.
Let’s go shopping on Saturday!
Email soon.
Susan""",
            "questions": [
                _t("", "am", "’m"),
                _t("", "His"),
                _t("", "going", "coming", "planning"),
                _t("", "does", "will"),
                _t("", "can’t", "cannot"),
            ],
        },
    ],
}


# ------------------------------------------------------------- STEP 2
# Manba: "Step 2.0 Unit N.pdf" + "unit N - IELTS 2.0 keys.pdf"
# (Empower 2nd Edition A2 Unit Progress Test). 40 savol.

STEP2_UNIT1 = {
    "level": "step2", "kind": "unit", "unit_no": 1,
    "title": "Step 2 · Unit 1 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["It’s at 10.30.", "I’d like to do a fitness class.", "You’re welcome."], "B"),
                _c("", ["OK. What’s your name?", "OK. Is it a big group?", "OK. Can I book a place?"], "A"),
                _c("", ["James Park.", "My father isn’t here.", "It’s P-A-R-K."], "C"),
                _c("", ["It’s in Room 108.", "It’s at 9.15.", "It’s 22 Station Road."], "C"),
                _c("", ["You’re welcome.", "Can I help you?", "That’s right."], "A"),
                _c("", ["Can you spell that?", "That’s right.", "No problem."], "B"),
                _c("", ["Yes, it is.", "See you tomorrow.", "In Green Street."], "C"),
                _c("", ["Yes, thank you.", "Yes, it’s at 9.30.", "No, you’re welcome."], "B"),
            ],
        },
        {
            "title": "Part 2 · People and countries",
            "instructions": "Read the sentences about people and countries. "
                            "Choose the missing word (A, B or C) for each "
                            "space.",
            "questions": [
                _c("My mother’s not from Russia – she’s ............ .",
                   ["Polish", "Poland", "Russian"], "A"),
                _c("Thank you for your help today, you are really ………… to me.",
                   ["famous", "busy", "kind"], "C"),
                _c("He says he’s a ............ football player but he’s not very good.",
                   ["quiet", "well-known", "first"], "B"),
                _c("Ahmed’s ............ but he lives in Hamburg in Germany.",
                   ["German", "Australia", "Australian"], "C"),
                _c("My family is from ............ but now we live in the USA.",
                   ["French", "France", "American"], "B"),
                _c("My new computer is Chinese – it’s from ............ .",
                   ["Canadian", "Canada", "China"], "C"),
                _c("Veronica has a big car and a very big house, so I think she "
                   "is ............ .", ["warm", "modern", "rich"], "C"),
                _c("Sam is a nice person, so he’s always very ............ to "
                   "other people.", ["modern", "rich", "pleasant"], "C"),
            ],
        },
        {
            "title": "Part 3 · People",
            "instructions": "Read the sentences about people. What are the "
                            "missing words? The first letter is already "
                            "there. Write the whole word.",
            "questions": [
                _t("Joe is from the USA – he is A _ _ _ _ _ _ _ .", "American", "merican"),
                _t("Rose has lots of friends – she’s very p _ _ _ _ _ _ .", "popular", "opular"),
                _t("Aranya is Thai, she comes from Bangkok in T _ _ _ _ _ _ _ .",
                   "Thailand", "hailand"),
                _t("Claire is from Britain – she is B _ _ _ _ _ _ .", "British", "ritish"),
                _t("I like my job – my colleagues are f _ _ _ _ _ _ _ _ !",
                   "fantastic", "antastic"),
                _t("Maria is Irish; she is from I _ _ _ _ _ _ .", "Ireland", "reland"),
                _t("My sister does not talk much and I am also q _ _ _ _ .", "quiet", "uiet"),
                _t("I like my new class because the teacher is good and the "
                   "students are nice and f _ _ _ _ _ _ _ .", "friendly", "riendly"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read this blog about Robert and Manuel. Choose the "
                            "best answer (A, B or C) for each space.",
            "passage": """Two good friends

My name’s Robert. In this photo I am with my best friend, Manuel. I’m British, but is Manuel British? No, (25) ………… . Manuel’s parents come from Spain but now they live in Britain. I’m not in the same class as Manuel, but we like to have lunch and walk to college together. Manuel (26) ………… very friendly, and popular with all the teachers and students at our college. Some students in our college are British and others (27) ………… . They come from different countries – this is great because we all study together and learn about different places and languages.
Manuel and I love football and like to go to matches when we can. This photo is after a football match in London. Are we happy in this photo? Yes, (28) ………… . At football matches, the weather’s often really cold and the match (29) ………… very good, but for us (30) ………… all great fun. Manuel’s team has great players – really fantastic and well-known. (31) ………… the name of his team? It’s Barcelona! (32) ………… the best players in the world? It’s possible!""",
            "questions": [
                _c("", ["he isn’t", "you aren’t", "I’m not"], "A"),
                _c("", ["am", "are", "is"], "C"),
                _c("", ["isn’t", "aren’t", "are"], "B"),
                _c("", ["he is", "I am", "we are"], "C"),
                _c("", ["am not", "aren’t", "isn’t"], "C"),
                _c("", ["it’s", "he’s", "we’re"], "A"),
                _c("", ["What’s", "What are", "Where’s"], "A"),
                _c("", ["Is he", "Are they", "Are you"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about people. Choose the best "
                            "answer (A, B or C) for each space.",
            "questions": [
                _c("My house ............ here, behind the school.", ["am", "is", "are"], "B"),
                _c("Paulo and Jorge speak Spanish but they ............ from Spain – "
                   "they’re Colombian.", ["are", "is not", "aren’t"], "C"),
                _c("............ our teacher’s name?", ["What are", "What is", "What am"], "B"),
                _c("I play football but ............ good at it.", ["he isn’t", "am I", "I’m not"], "C"),
                _c("Kenji’s a brilliant student – ............ he from?",
                   ["where is", "what is", "where are"], "A"),
                _c("............ quiet? No, I like to talk a lot.", ["Is it", "Are they", "Am I"], "C"),
                _c("Our home town ............ Paris – it’s Calais, a small French city "
                   "by the sea.", ["is not", "am not", "are not"], "A"),
                _c("............ your friend James on holiday in New Zealand?",
                   ["Are", "Be", "Is"], "C"),
            ],
        },
    ],
}


STEP2_UNIT2 = {
    "level": "step2", "kind": "unit", "unit_no": 2,
    "title": "Step 2 · Unit 2 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Sure, no problem.", "I don’t want it.", "It’s at 1:30."], "A"),
                _c("", ["Can I have two coffees, please?", "Sure, no problem.", "What do you want?"], "A"),
                _c("", ["Where do you travel?", "I’m sorry about that.", "Yes, at what time?"], "C"),
                _c("", ["OK, can I phone you this afternoon?", "OK, can I have tea please?", "OK, can I start work?"], "A"),
                _c("", ["Can I have a coffee?", "Certainly. Small or large?", "Please drink it."], "B"),
                _c("", ["Thank you very much.", "OK, no problem.", "You’re welcome."], "B"),
                _c("", ["Can you spell that?", "Certainly, no problem.", "Thanks for your time."], "B"),
                _c("", ["Of course.", "It doesn’t matter.", "How can I help?"], "A"),
            ],
        },
        {
            "title": "Part 2 · Jobs and study",
            "instructions": "Read the sentences about jobs. Choose the missing "
                            "word (A, B or C) for each space.",
            "questions": [
                _c("Chris works as a ............ in a hospital – he looks after "
                   "people when they aren't well.", ["chef", "manager", "nurse"], "C"),
                _c("I study every day because I want to ............ a good mark in "
                   "this exam.", ["get", "pass", "take"], "A"),
                _c("Ben wants to be a ............ because he likes to work with cars "
                   "and machines.", ["mechanic", "secretary", "manager"], "A"),
                _c("I take ............ when I study because they help me to remember "
                   "important information.", ["marks", "notes", "terms"], "B"),
                _c("I'd like to be a ............ one day because I love travel and planes.",
                   ["cleaner", "secretary", "pilot"], "C"),
                _c("Lucy usually gets good ............ in her tests at school.",
                   ["habits", "notes", "marks"], "C"),
                _c("Can you look at the school ............ and tell me when we have "
                   "an English class?", ["teacher", "timetable", "team"], "B"),
                _c("My brother's an amazing ............ and so he works in the "
                   "kitchen of a big hotel.", ["chef", "farmer", "actor"], "A"),
            ],
        },
        {
            "title": "Part 3 · Work and study",
            "instructions": "Read the descriptions of some words about work and "
                            "study. The first letter is already there. Write "
                            "the whole word.",
            "questions": [
                _t("You have this when you stop your studies or your work for a "
                   "short time.   b _ _ _ _", "break", "reak"),
                _t("This person takes you from one place to another by car and you "
                   "pay him money.   t _ _ _  d _ _ _ _ _", "taxi driver", "axi river"),
                _t("This person answers the telephone, writes letters and plans "
                   "meetings in an office.   s _ _ _ _ _ _ _ _", "secretary", "ecretary"),
                _t("If you have a problem with your teeth, you go to this person.   "
                   "d _ _ _ _ _ _", "dentist", "entist"),
                _t("Sometimes you do an e _ _ _ at the end of a course to check "
                   "what you learned.", "exam", "xam"),
                _t("I want to ask the s _ _ _  a _ _ _ _ _ _ _ _ how much this bag is.",
                   "shop assistant", "hop ssistant"),
                _t("People who enjoy their s _ _ _ _ _ _ sometimes get better marks "
                   "in their tests.", "studies", "tudies"),
                _t("The teachers are very good here and the students never "
                   "f _ _ _ their exams.", "fail", "ail"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read Priya's blog about her family and their jobs "
                            "and studies. Choose the best answer (A, B or C) "
                            "for each space.",
            "passage": """Priya's family

I live with my parents and my brother and sister. I work in an office but I (25) ………… want to work there all my life. I'd like to work in another country.
My parents both work in a hospital. My mother is a doctor and my father is a hospital manager. My mother (26) ………… her job is hard but interesting. She (27) ………… much free time. She begins work at 8 o'clock in the morning and finishes at seven o'clock in the evening. My father and I (28) ………… home at 6 o'clock so we cook dinner. When do we eat dinner? After our favourite TV programme!
My sister and brother are students. They want to be doctors like our mother. My sister studies hard but she hates tests. I often say to her, 'Do you (29) ………… good marks?' And she always replies, 'Yes, (30) ………… !' So why (31) ………… she worry? When I ask my brother, 'Do you enjoy your studies?', he always replies, 'No, I (32) ………… . I prefer football!'""",
            "questions": [
                _c("", ["do", "don't", "doesn't"], "B"),
                _c("", ["says", "say", "saying"], "A"),
                _c("", ["not have", "don't have", "doesn't have"], "C"),
                _c("", ["come", "comes", "doesn't come"], "A"),
                _c("", ["get", "gets", "getting"], "A"),
                _c("", ["I don't", "I do", "do I"], "B"),
                _c("", ["don't", "do", "does"], "C"),
                _c("", ["doesn't", "do", "don't"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about everyday life. Choose the "
                            "best answer (A, B or C) for each space.",
            "questions": [
                _c("My brother works in a bank but he ............ enjoy his job.",
                   ["don't", "doesn't", "isn't"], "B"),
                _c("How many hours a week ............ study French?",
                   ["you do", "you don't", "do you"], "C"),
                _c("My friend and I ............ swimming lessons every Friday after work.",
                   ["have", "has", "having"], "A"),
                _c("Larry's a good businessman but does ............ a lot of money?",
                   ["he makes", "he make", "make"], "B"),
                _c("I ............ my car to the office – I go by bus.",
                   ["drive", "don't drive", "doesn't drive"], "B"),
                _c("'Do classes start at 9 o'clock?' 'No, they ............ . They "
                   "start at 8.30.'", ["don't", "do", "doesn’t"], "A"),
                _c("You ............ all the answers so please help me with my homework.",
                   ["knows", "knowing", "know"], "C"),
                _c("'Does Marisa work in a hotel?' 'Yes, she ............ . She's a "
                   "receptionist.'", ["do", "doesn't", "does"], "C"),
            ],
        },
    ],
}


STEP2_UNIT3 = {
    "level": "step2", "kind": "unit", "unit_no": 3,
    "title": "Step 2 · Unit 3 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["How can I help?", "OK, you can come here.", "Yes, that's a good idea."], "C"),
                _c("", ["You're welcome.", "That's a pity.", "I'd love to."], "C"),
                _c("", ["That'd be great.", "You're welcome.", "Yes, I can."], "A"),
                _c("", ["How often do you go there?", "So, what do you think of this idea?", "OK, when are you free?"], "C"),
                _c("", ["How about 3.30?", "Yes, that's fine.", "Why don't you try it?"], "B"),
                _c("", ["Thanks for your help.", "Yes, Friday's fine.", "I'm sorry, I can't."], "C"),
                _c("", ["OK, Monday's fine.", "Let me see.", "Well, sometimes."], "B"),
                _c("", ["I'm fine, thanks.", "That's a pity.", "Mm, possibly."], "C"),
            ],
        },
        {
            "title": "Part 2 · Everyday life",
            "instructions": "Read the sentences about everyday life. Choose the "
                            "missing word (A, B or C) for each space.",
            "questions": [
                _c("In the summer, I like to play football ............ a week.",
                   ["once", "always", "every"], "A"),
                _c("Does the shop in the hotel ............ postcards?", ["sell", "buy", "find"], "A"),
                _c("I can write emails on my ............ when I'm on the train.",
                   ["video", "timetable", "smartphone"], "C"),
                _c("Do you ............ in a hotel when you go on holiday?",
                   ["stay", "prefer", "decide"], "A"),
                _c("Business people need to have a ............ so that they can work "
                   "when they travel.", ["speaker", "text", "laptop"], "C"),
                _c("My brother uses his ............ to check emails when he is not in "
                   "the office.", ["tablet", "keyboard", "speaker"], "A"),
                _c("Can you help me ............ which laptop to buy?",
                   ["meet", "prefer", "decide"], "C"),
                _c("We take a small ............ on holiday with us so we can listen "
                   "to music.", ["camera", "speaker", "keyboard"], "B"),
            ],
        },
        {
            "title": "Part 3 · Daily life",
            "instructions": "Read the sentences about daily life. What are the "
                            "missing words? The first letter is already there. "
                            "Write the whole word.",
            "questions": [
                _t("I go to the cinema three or four t _ _ _ _ a month.", "times", "imes"),
                _t("I need to buy more paper for the p _ _ _ _ _ _ at home.",
                   "printer", "rinter"),
                _t("How much does this computer c _ _ _ please?", "cost", "ost"),
                _t("I don't like using my computer k _ _ _ _ _ _ _ because it's very small.",
                   "keyboard", "eyboard"),
                _t("Which do you p _ _ _ _ _ – tea or coffee?", "prefer", "refer"),
                _t("My brother likes to use h _ _ _ _ _ _ _ _ _ when he listens to music.",
                   "headphones", "eadphones"),
                _t("My grandparents go to the cinema t _ _ _ _ a week – on Tuesdays "
                   "and Saturdays.", "twice", "wice"),
                _t("I wear a s _ _ _ _ _ _ _ _ _ to check the time and do lots of "
                   "other things.", "smartwatch", "martwatch"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the blog about a teacher's life. Choose the "
                            "best answer (A, B or C) for each space.",
            "passage": """A teacher's life

My name is Maria and I teach English in a school in London. I (25) ………… at 7 o'clock. I always go to work by bus because it's too far to walk and I (26) ………… a car. It's a large school in a lovely new building. The school (27) ………… a very nice cafe and so I (28) ………… breakfast there. Lessons start at 9 o'clock. We stop for lunch at half past twelve. In the lunch break (29) ………… the newspaper and talk to the other teachers. Lessons start again at 2 and finish at 4. After school we teachers (30) ………… have a lot of work to do because we're very busy all the time. But when I haven't got work to do, I go to the cinema or visit friends. I (31) ………… a good friend in the next street. She (32) ………… a big garden and we like to sit there in the evenings in summer.""",
            "questions": [
                _c("", ["get up usually", "usually get up", "usually gets up"], "B"),
                _c("", ["hasn't got", "haven't got", "don't get"], "B"),
                _c("", ["have got", "got", "has got"], "C"),
                _c("", ["sometimes have", "have sometimes got", "have sometimes"], "A"),
                _c("", ["usually I read", "I read usually", "I usually read"], "C"),
                _c("", ["always", "never", "sometimes"], "A"),
                _c("", ["get", "has got", "have got"], "C"),
                _c("", ["have got", "do get", "has got"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about everyday life. Choose the "
                            "best answer (A, B or C) for each space.",
            "questions": [
                _c("............ often do you go to the gym every week?", ["How", "What", "When"], "A"),
                _c("Why ............ late?",
                   ["James is always", "is James always", "James always is"], "B"),
                _c("Have both of the children got a laptop? Yes, they ............ .",
                   ["are", "can", "have"], "C"),
                _c("There's no milk again – you ............ remember to buy any!",
                   ["often", "never", "always"], "B"),
                _c("We ............ got a printer at home.", ["aren't", "don't", "haven't"], "C"),
                _c("............ Paul got a new camera?", ["Does", "Has", "Is"], "B"),
                _c("I often leave work at 5.30, but I ............ need to stay in the "
                   "office until 7 pm.", ["always", "usually", "sometimes"], "C"),
                _c("My mother ............ got a great new satnav in her car.",
                   ["have", "is", "has"], "C"),
            ],
        },
    ],
}


STEP2_UNIT4 = {
    "level": "step2", "kind": "unit", "unit_no": 4,
    "title": "Step 2 · Unit 4 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Yes, the name’s Dawson.", "No, wait.", "We’d love to."], "A"),
                _c("", ["Are you ready to order?", "Where would you like to sit?", "Would you like bread with that?"], "C"),
                _c("", ["Yes, thank you.", "This way, please.", "I’m sorry, I can’t."], "B"),
                _c("", ["We have a reservation for two people.", "Maybe not.", "I’ll have the chicken soup."], "C"),
                _c("", ["No problem.", "Yes, please.", "I’m sorry."], "B"),
                _c("", ["No, I prefer tea to coffee.", "No, maybe I’ll have fish.", "No, wait - I’d like water."], "C"),
                _c("", ["And for your main course?", "What is your name, please?", "Can we have a table outside?"], "B"),
                _c("", ["Mm. No, maybe not.", "I’m sorry, I’m not.", "Thank you for your help."], "A"),
            ],
        },
        {
            "title": "Part 2 · Food and cooking",
            "instructions": "Read the sentences about food and cooking. Choose "
                            "the missing word (A, B or C) for each space.",
            "questions": [
                _c("To make ............ eggs, cook them in a little oil for three minutes.",
                   ["boiled", "grilled", "fried"], "C"),
                _c("Can you open this ............ of soup for me, please?", ["bar", "can", "bag"], "B"),
                _c("Can I have a piece of ............ to put in my tea, please?",
                   ["steak", "bean", "lemon"], "C"),
                _c("I want ............ soup for my starter, please.",
                   ["salad", "mushroom", "pear"], "B"),
                _c("This ............ steak is nice and brown on both sides.",
                   ["grilled", "boiled", "baked"], "A"),
                _c("My favourite meat is ............ but I also like chicken.",
                   ["mushroom", "steak", "onion"], "B"),
                _c("Would you like ............ or boiled vegetables with your chicken?",
                   ["cooked", "hot", "roasted"], "C"),
                _c("Would you like a tomato ............ or hot vegetables with your meal?",
                   ["salt", "sugar", "salad"], "C"),
            ],
        },
        {
            "title": "Part 3 · Food and cooking",
            "instructions": "Read the sentences about food and cooking. What "
                            "are the missing words? The first letter is "
                            "already there. Write the whole word.",
            "questions": [
                _t("I think that c _ _ _ _ _ _ are my favourite orange vegetable.",
                   "carrots", "arrots"),
                _t("Put the meat in the oven and r _ _ _ _ it for an hour and a half.",
                   "roast", "oast"),
                _t("We always make our own bread, because we like eating it when it "
                   "is freshly b _ _ _ _ .", "baked", "aked"),
                _t("I’d like to buy a small b _ _ _ _ _ of water, please.", "bottle", "ottle"),
                _t("My favourite vegetable is fried o _ _ _ _ , especially with burgers.",
                   "onion", "nion"),
                _t("I have a bowl of c _ _ _ _ _ with fruit and yoghurt for breakfast "
                   "every morning.", "cereal", "ereal"),
                _t("Put the potatoes in water in a pan and b _ _ _ them for 20 minutes.",
                   "boil", "oil"),
                _t("My favourite meat is roasted c _ _ _ _ _ _ .", "chicken", "hicken"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the email from a wife to her husband. Choose "
                            "the best answer (A, B or C) for each space.",
            "passage": """Supermarket

Hi Tom,
Can you go to the supermarket after work, please? Can you buy (25) ………… fruit? I'd like to make a fruit salad. We've got (26) ………… of bananas but we haven't got (27) ………… grapes or apples. I also want to roast a chicken, so could you get us one, please. We also need (28) ………… butter - we've got a little but not very (29) ………… . Oh, and we've only got (30) ………… potatoes, so please get a bag of those too. Don't get (31) ………… onions or carrots - we've already got a lot of them. One last thing - we haven't got (32) ………… coffee, so please get us a big packet.
Thanks very much.
See you later. Emma""",
            "questions": [
                _c("", ["some", "a", "any"], "A"),
                _c("", ["many", "a lot", "much"], "B"),
                _c("", ["some", "any", "the"], "B"),
                _c("", ["a", "any", "some"], "C"),
                _c("", ["much", "many", "a lot"], "A"),
                _c("", ["not many", "a little", "a few"], "C"),
                _c("", ["any", "an", "some"], "A"),
                _c("", ["a few", "much", "many"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about food and cooking. Choose "
                            "the best answer (A, B or C) for each space.",
            "questions": [
                _c("I need some lamb and ............ onion because I want to make "
                   "curry for dinner.", ["a", "any", "an"], "C"),
                _c("I’d like ............ pasta, please.", ["some", "a", "an"], "A"),
                _c("How ............ milk do the children usually have with their cereal?",
                   ["much", "many", "few"], "A"),
                _c("There are ............ beans in the fridge.", ["any", "a", "some"], "C"),
                _c("How ............ lemons do you want?", ["much", "little", "many"], "C"),
                _c("We haven’t got ............ big onions.", ["some", "a", "any"], "C"),
                _c("We haven’t got ............ ice cream.", ["much", "a lot", "many"], "A"),
                _c("There are only ............ tomatoes in the fridge.",
                   ["a few", "many", "a lot of"], "A"),
            ],
        },
    ],
}


STEP2_UNIT5 = {
    "level": "step2", "kind": "unit", "unit_no": 5,
    "title": "Step 2 · Unit 5 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["A post office? No, there isn't.", "A post office? Turn left at the station.", "A post office? This is the concert hall."], "B"),
                _c("", ["Where's the metro station?", "Are you certain?", "Is there?"], "B"),
                _c("", ["Are you sure?", "That's right – the bank is on the left.", "Yes, go straight on, and turn into Albert Street."], "C"),
                _c("", ["Right into Surrey Street?", "OK, turn left.", "The bank is on the right."], "A"),
                _c("", ["Turn right at the supermarket, then left.", "Is that left into Park Street?", "So, the stadium is straight along here."], "A"),
                _c("", ["Turn right for the supermarket.", "The cinema is on your left.", "Go straight along Black Street."], "C"),
                _c("", ["That's right.", "Are you sure?", "Great, thanks."], "A"),
                _c("", ["I think so.", "Is there a bank near here?", "Go straight on for about 500 metres."], "C"),
            ],
        },
        {
            "title": "Part 2 · City and home",
            "instructions": "Read the sentences about things you can find in "
                            "the city or in your home. Choose the missing word "
                            "(A, B or C) for each space.",
            "questions": [
                _c("People usually only visit a ............ when they have a problem.",
                   ["concert hall", "football stadium", "police station"], "C"),
                _c("Every morning I look in the ............ and think, 'Wow, I look great!'",
                   ["lamp", "mirror", "wardrobe"], "B"),
                _c("This is my favourite ............ where I sit and watch TV.",
                   ["cooker", "armchair", "bookcase"], "B"),
                _c("Every morning, I wash the dishes in the kitchen ............ .",
                   ["washing machine", "sink", "mirror"], "B"),
                _c("I watch football every Saturday at the ............ near my house.",
                   ["concert hall", "stadium", "theatre"], "B"),
                _c("Geraldo lives in a fantastic new ............ opposite the post office.",
                   ["office", "flat", "hospital"], "B"),
                _c("I clean the curtains in the ............ when they are very dirty.",
                   ["cooker", "mirror", "washing machine"], "C"),
                _c("In the centre of my city, there's a beautiful ............ with many "
                   "interesting buildings.", ["square", "café", "flat"], "A"),
            ],
        },
        {
            "title": "Part 3 · City and home",
            "instructions": "Read the descriptions of things you can find in "
                            "the city or in your home. The first letter is "
                            "already there. Write the whole word.",
            "questions": [
                _t("This is a place where you can get some exercise.   "
                   "s _ _ _ _ _  c _ _ _ _ _", "sports centre", "ports entre",
                   "sports center"),
                _t("At night, you can use this to help you see when you want to "
                   "read.   l _ _ _", "lamp", "amp"),
                _t("When you want to send a letter, you go to this place.   "
                   "p _ _ _  o _ _ _ _ _", "post office", "ost ffice"),
                _t("You can find this in the kitchen and use it to make a hot meal.   "
                   "c _ _ _ _ _", "cooker", "ooker"),
                _t("At home, when you want to get something to read, you can find "
                   "something in here.   b _ _ _ _ _ _ _", "bookcase", "ookcase"),
                _t("You can find these at a window.   c _ _ _ _ _ _ _", "curtains", "urtains"),
                _t("There are often apartments and offices inside one of these.   "
                   "b _ _ _ _ _ _ _", "building", "uilding"),
                _t("People walk on this when they go over a river.   b _ _ _ _ _",
                   "bridge", "ridge"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read this text about an unusual house. Choose the "
                            "best answer (A, B or C) for each space.",
            "passage": """An Unusual House

You can visit a very unusual house in Pennsylvania, in the USA. I think it's great. Like other houses, there (25) ………… a normal front door and there are normal windows, but this house is actually very different from a house like yours or (26) ………… . It's a very, very big shoe! In Shoe House, (27) ………… a living room, one bedroom and a bathroom. It's a big shoe outside, but the house is actually very small inside and (28) ………… much furniture.
So, (29) ………… house is this? Carla Farrow and her husband Ron live there now. In the house, you can see a picture of Martin Boston, the first owner. In (30) ………… hands, of course, there is a pair of shoes!
(31) ………… unusual houses near you? Do you live in one? If (32) ………… is unusual, email me some pictures of it.""",
            "questions": [
                _c("", ["is", "are", "has"], "A"),
                _c("", ["mine", "his", "theirs"], "A"),
                _c("", ["there are", "it is", "there's"], "C"),
                _c("", ["there is", "there are", "there isn't"], "C"),
                _c("", ["who", "whose", "who's"], "B"),
                _c("", ["Martin's", "Martin", "Martins"], "A"),
                _c("", ["Is there some", "Isn't there any", "Are there any"], "C"),
                _c("", ["theirs", "yours", "ours"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about things you can find in "
                            "the city or in your home. Choose the best answer "
                            "(A, B or C) for each space.",
            "questions": [
                _c("There ............ three theatres in the town where I live.",
                   ["is", "are", "has"], "B"),
                _c("Why ............ there any milk in the fridge?", ["isn't", "aren't", "hasn’t"], "A"),
                _c("My sister's room is next to ............ .", ["my", "your", "mine"], "C"),
                _c("Go straight along the street and ............ a supermarket on your left.",
                   ["there are", "there's", "this is"], "B"),
                _c("There are ............ good places to listen to classical music in "
                   "your town.", ["lots", "some", "any"], "B"),
                _c("John and Sally live in New York and my apartment is next to ............ .",
                   ["they", "their", "theirs"], "C"),
                _c("My brother lives in London now – it's ............ favourite city.",
                   ["his", "he", "him"], "A"),
                _c("............ bedroom is this?", ["Whose", "Who", "Who's"], "A"),
            ],
        },
    ],
}


STEP2_UNIT6 = {
    "level": "step2", "kind": "unit", "unit_no": 6,
    "title": "Step 2 · Unit 6 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["She's not here just now.", "Can I call you at work?", "Fred’ll be back soon."], "A"),
                _c("", ["Is Carla there?", "You're welcome.", "Sure, no problem."], "C"),
                _c("", ["Can you wait a minute?", "Hi, Lucy, it's Ben.", "Sorry, I have a meeting."], "B"),
                _c("", ["OK, just a minute.", "OK, you can call me at work.", "OK, could he call me back?"], "C"),
                _c("", ["He'll be back soon.", "There is Phil.", "Are you free?"], "A"),
                _c("", ["Thanks for your help.", "Hi, Ben, it's me, Joe.", "Can we chat about it now?"], "B"),
                _c("", ["How can I help?", "I'm not here just now.", "No, it's OK. Can she call me back?"], "C"),
                _c("", ["OK, thanks.", "Is Annie there please?", "She's not there just now."], "A"),
            ],
        },
        {
            "title": "Part 2 · People and families",
            "instructions": "Read the sentences about people and families. "
                            "Choose the missing word (A, B or C) for each "
                            "space.",
            "questions": [
                _c("My grandfather is still alive but my ............ died in 2010 – "
                   "she was 89 years old.", ["grandparents", "grandmother", "granddaughter"], "B"),
                _c("My sister ............ a new computer last week.", ["bought", "spent", "cost"], "A"),
                _c("My little brother was born ............ a Saturday.", ["in", "at", "on"], "C"),
                _c("Sue ............ to London by car yesterday to meet her mother for lunch.",
                   ["brought", "made", "went"], "C"),
                _c("My grandparents moved to their house ............ 1948.", ["in", "at", "on"], "A"),
                _c("My uncle's birthday is ............ May and we always go for a picnic "
                   "that day.", ["on", "at", "in"], "C"),
                _c("Adam and Joe ............ friends when they found out they both like "
                   "football.", ["went", "got", "became"], "C"),
                _c("My sister ............ a big cake for my birthday – she's a very good cook.",
                   ["ate", "made", "cut"], "B"),
            ],
        },
        {
            "title": "Part 3 · People and families",
            "instructions": "Read the sentences about people and families. What "
                            "are the missing words? The first letter is "
                            "already there. Write the whole word.",
            "questions": [
                _t("Susanna's sister has three children and so Susanna is an a _ _ _ .",
                   "aunt", "unt"),
                _t("I s _ _ _ _ all my money on my brother's birthday present, so I've "
                   "got no money now.", "spent", "pent"),
                _t("I saw my c _ _ _ _ _ John and his father, my Uncle Paul, yesterday.",
                   "cousin", "ousin"),
                _t("My parents always wanted g _ _ _ _ _ _ _ _ _ _ _ _ , so they were "
                   "happy when my sons, Tom and Dan were born.",
                   "grandchildren", "randchildren"),
                _t("My sister's new shoes c _ _ _ a lot of money.", "cost", "ost"),
                _t("I f _ _ _ _ this old photograph of my uncle – he moved to "
                   "Australia when he was 19.", "found", "ound"),
                _t("As usual, our whole family a _ _ roast lamb for lunch on Sunday.",
                   "ate", "te"),
                _t("Eva's son, Martin, is a doctor and now Martin's daughter, Eva's "
                   "g _ _ _ _ _ _ _ _ _ _ _ _ , is also a doctor.",
                   "granddaughter", "randdaughter"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read a woman's story about when she was a child. "
                            "Choose the best answer (A, B or C) for each space.",
            "passage": """My early life

When I was a child, I (25) ………… in a small village by the sea. My family had a farm. I loved playing outside in the summer holidays. My older sister (26) ………… at home then but my brothers (27) ………… , and the three of us (28) ………… ourselves. We often played by the sea. We took apples and cola with us and (29) ………… outside all day. There was always lots to do.
But I remember when it rained there was nothing to do. Then I found some books in my parents’ bookcase and the world (30) ………… for me. I took books everywhere with me and read all the time. But my brothers (31) ………… interested in books and thought I wasn't fun anymore! (32) ………… it a good time? Yes, fantastic and I often go back to my old family house where my parents still live.""",
            "questions": [
                _c("", ["lives", "lived", "live"], "B"),
                _c("", ["wasn't", "isn't", "weren't"], "A"),
                _c("", ["weren't", "were", "was"], "B"),
                _c("", ["to enjoy", "enjoy", "enjoyed"], "C"),
                _c("", ["stays", "stayed", "stay"], "B"),
                _c("", ["change", "to change", "changed"], "C"),
                _c("", ["weren't", "were", "wasn't"], "A"),
                _c("", ["Is", "Were", "Was"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about people and families. "
                            "Choose the best answer (A, B or C) for each space.",
            "questions": [
                _c("............ at home when you called?", ["He was", "Was he", "Is he"], "B"),
                _c("Where ............ your older sister born?", ["is", "was", "were"], "B"),
                _c("My brother ............ hard and became a doctor last year.",
                   ["studied", "study", "studies"], "A"),
                _c("I ............ at the same university as my brother.",
                   ["wasn't", "weren't", "aren't"], "A"),
                _c("When my brother was young he ............ sport, and he was really "
                   "good at football.", ["loves", "loved", "love"], "B"),
                _c("When my cousin went to Canada, I ............ writing to her.",
                   ["stops", "stop", "stopped"], "C"),
                _c("'Were all your friends in the same class at school?' 'No, ............ .'",
                   ["they aren't", "weren't they", "they weren't"], "C"),
                _c("My husband usually gets home early but last night he ............ "
                   "home very late.", ["arrived", "arrive", "arrives"], "A"),
            ],
        },
    ],
}


STEP2_UNIT7 = {
    "level": "step2", "kind": "unit", "unit_no": 7,
    "title": "Step 2 · Unit 7 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Great! I love it!", "That’s all right.", "Excuse me, but this is mine."], "B"),
                _c("", ["Really? Why?", "Great! I’m going too.", "I’m sorry, I don’t know."], "A"),
                _c("", ["Great!", "I’d like some help.", "Is it? I’m really sorry."], "C"),
                _c("", ["Don’t worry.", "You’re welcome.", "Excuse me, please."], "A"),
                _c("", ["No problem. They all look the same.", "That’s a pity. I don’t have one.", "Excuse me. It’s raining."], "A"),
                _c("", ["Certainly. What’s the seat number?", "It doesn’t matter. There are lots of other seats.", "Excuse me. It’s my seat."], "B"),
                _c("", ["Great!", "Sure, no problem.", "No, wait."], "A"),
                _c("", ["It doesn’t matter. This is seat 42.", "That’s all right. I’m sitting here.", "I’m sorry. I didn’t see the seat number."], "C"),
            ],
        },
        {
            "title": "Part 2 · Transport",
            "instructions": "Read the sentences about transport. Choose the "
                            "missing word (A, B or C) for each space.",
            "questions": [
                _c("The seats in the bus are small and hard, so they’re not very ............ .",
                   ["dangerous", "comfortable", "empty"], "B"),
                _c("Motorbikes can be very ............ if you don’t ride them carefully.",
                   ["dangerous", "expensive", "comfortable"], "A"),
                _c("I don’t like helicopters because they aren’t very ............ .",
                   ["sure", "safe", "serious"], "B"),
                _c("I don’t travel by plane very often because it’s ............ .",
                   ["fast", "clean", "expensive"], "C"),
                _c("If you want to go to Cambridge, you need to ............ trains in London.",
                   ["miss", "change", "bring"], "B"),
                _c("We can ............ a tram to the beach from here.",
                   ["take", "travel", "carry"], "A"),
                _c("The bus to the station was late, so Jack ............ his train.",
                   ["lost", "failed", "missed"], "C"),
                _c("The bus was very hot and crowded, so I got ............ and walked home.",
                   ["on", "off", "away"], "B"),
            ],
        },
        {
            "title": "Part 3 · Transport",
            "instructions": "Read the descriptions of some words about "
                            "transport. The first letter is already there. "
                            "Write the whole word.",
            "questions": [
                _t("This goes very fast on the water.   s _ _ _ _ _ _ _ _",
                   "speedboat", "peedboat", "speed boat"),
                _t("You need to wash your car when it is this.   d _ _ _ _", "dirty", "irty"),
                _t("A train is this if there are no people on it.   e _ _ _ _", "empty", "mpty"),
                _t("You do this at the start of your train journey.   g _ _  o _",
                   "get on", "et n"),
                _t("A bus ticket is this when it doesn’t cost much money.   c _ _ _ _",
                   "cheap", "heap"),
                _t("This is a very big boat.   s _ _ _", "ship", "hip"),
                _t("The metro is this when there are a lot of people there.   "
                   "c _ _ _ _ _ _", "crowded", "rowded"),
                _t("This has two wheels and it isn’t a bike.   s _ _ _ _ _ _",
                   "scooter", "cooter"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the text about a holiday in Lisbon, in "
                            "Portugal. Choose the best answer (A, B or C) for "
                            "each space.",
            "passage": """A holiday in Lisbon

Last spring I had a holiday in Lisbon, in Portugal. I love walking around city streets, and I like (25) ………… photos too. Lisbon is perfect for that. I (26) ………… stay there very long – only 4 days – but it’s quite a small city, and it’s easy to get around. I usually hate (27) ………… by metro, but I didn’t mind (28) ………… the metro in Lisbon, because it’s clean and never too crowded. I didn’t (29) ………… everything in the city, but I had a great time.
I don’t like (30) ………… in big hotels, because I think they’re boring. So I stayed with a friendly Portuguese family. I ate my breakfast there, but I didn’t (31) ………… my other meals with them because there are so many great restaurants in Lisbon. When my friends ask me ‘Why (32) ………… to Lisbon?’, the answer is easy: ‘It’s my favourite city!’""",
            "questions": [
                _c("", ["taking", "takes", "take"], "A"),
                _c("", ["did", "don’t", "didn’t"], "C"),
                _c("", ["travel", "travels", "travelling"], "C"),
                _c("", ["using", "use", "used"], "A"),
                _c("", ["sees", "see", "seeing"], "B"),
                _c("", ["stay", "staying", "stayed"], "B"),
                _c("", ["have", "had", "having"], "A"),
                _c("", ["did you go", "you went", "you did go"], "A"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about travel. Choose the best "
                            "answer (A, B or C) for each space.",
            "questions": [
                _c("My parents love ............ in the countryside.", ["cycle", "cycling", "cycled"], "B"),
                _c("I ............ travel a lot when I was a student.", ["didn’t", "don’t", "doesn’t"], "A"),
                _c("I hate ............ in the rain.", ["walk", "walked", "walking"], "C"),
                _c("Where ............ get off the bus?", ["you did", "did you", "didn’t you"], "B"),
                _c("‘Did you come by train?’ ‘Yes, I ............ .’", ["didn’t", "did", "do"], "B"),
                _c("I don’t like ............ by metro when it’s busy.",
                   ["travelling", "travel", "travelled"], "A"),
                _c("Did your friend ............ to the USA on holiday?", ["went", "goes", "go"], "C"),
                _c("Maria doesn’t like ............ because it’s so expensive.",
                   ["flies", "fly", "flying"], "C"),
            ],
        },
    ],
}


STEP2_UNIT8 = {
    "level": "step2", "kind": "unit", "unit_no": 8,
    "title": "Step 2 · Unit 8 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["You’re welcome.", "That’s all right.", "Come and sit down."], "C"),
                _c("", ["Poor you.", "Excuse me.", "I’m sorry I can’t."], "A"),
                _c("", ["Oh, you poor thing.", "Yes, I feel a bit sick actually.", "What’s the matter?"], "B"),
                _c("", ["I’ve got toothache.", "I’m not surprised.", "I’m really sorry."], "A"),
                _c("", ["Oh, dear.", "Oh, yes.", "Oh, well."], "A"),
                _c("", ["What’s the matter?", "Can I sit down?", "I’ve got a temperature."], "A"),
                _c("", ["Yes, my back hurts.", "No, I’ve got a really bad cold.", "Oh, you don’t look well."], "B"),
                _c("", ["It doesn’t matter.", "I’m not sure.", "You don’t look well."], "C"),
            ],
        },
        {
            "title": "Part 2 · Health, fitness and appearance",
            "instructions": "Read the sentences about health, fitness and "
                            "appearance. Choose the missing word (A, B or C) "
                            "for each space.",
            "questions": [
                _c("Harry and Joe often ............ sailing together because they both "
                   "love being on the sea.", ["go", "play", "have"], "A"),
                _c("Do you want to ............ badminton with us tomorrow?",
                   ["go", "play", "make"], "B"),
                _c("Tom ate his dinner too quickly, and now his ............ hurts.",
                   ["back", "neck", "stomach"], "C"),
                _c("Did you hurt your ............ when you did that last yoga exercise?",
                   ["position", "neck", "floor"], "B"),
                _c("Jenny was ill and now she looks quite ............ .",
                   ["thin", "straight", "long"], "A"),
                _c("There’s lots of ice on the river this winter, so we can ............ on it.",
                   ["swim", "skate", "ski"], "B"),
                _c("My brother and I both have dark hair, but my sister’s hair is ............ .",
                   ["fair", "brown", "black"], "A"),
                _c("My grandma ............ exercises to keep fit.", ["does", "makes", "plays"], "A"),
            ],
        },
        {
            "title": "Part 3 · Sport, health and the body",
            "instructions": "Read the descriptions of some words about sport, "
                            "health and the body. The first letter is already "
                            "there. Write the whole word.",
            "questions": [
                _t("You have five of these on each hand.   f _ _ _ _ _ _", "fingers", "ingers"),
                _t("You hit a small white ball across grass in this game.   g _ _ _",
                   "golf", "olf"),
                _t("You are this if you do a lot of sport and exercise.   f _ _", "fit", "it"),
                _t("You do this sport on mountains in winter.   s _ _ _ _ _ _ _ _ _ _ _",
                   "snowboarding", "nowboarding"),
                _t("You have five of these on each foot.   t _ _ _", "toes", "oes"),
                _t("You play this ball game in teams on grass.   r _ _ _ _", "rugby", "ugby"),
                _t("In which sport can you also catch some healthy food?   f _ _ _ _ _ _",
                   "fishing", "ishing"),
                _t("This is another word for pretty.   a _ _ _ _ _ _ _ _ _",
                   "attractive", "ttractive"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the text about a British athlete called Mo "
                            "Farah. Choose the best answer (A, B or C) for each "
                            "space.",
            "passage": """Mo Farah

Mo Farah was born in Somalia in East Africa. When he was eight, he moved to London. Life in Britain was hard for Mo because he could only speak a few words of English. He (25) ………… read any English or understand what people said. He (26) ………… to work very hard at school, because the lessons were difficult for him. The only thing that Mo (27) ………… do well was play football, because he could (28) ………… fast. He was good at sports, so he (29) ………… to work hard in sports lessons. Mo became a top runner, and he went to a special sports college where he had to practise very hard. Then in the 2012 Olympics he won gold twice – in the 5,000 and 10,000 metres.
Today life is good for Mo. He (30) ………… speak perfect English and he’s a famous sportsman. He has a lot of money, so he doesn’t (31) ………… to do any work if he doesn’t want to. But he still (32) ………… to go running every day. Why? Because he wants to win gold again!""",
            "questions": [
                _c("", ["couldn’t", "could", "can’t"], "A"),
                _c("", ["has", "had", "have"], "B"),
                _c("", ["could", "can’t", "can"], "A"),
                _c("", ["run", "ran", "running"], "A"),
                _c("", ["don’t have", "didn’t have", "had not"], "B"),
                _c("", ["could", "can", "couldn’t"], "B"),
                _c("", ["have", "has", "had"], "A"),
                _c("", ["hasn’t", "have", "has"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about sport and exercise. "
                            "Choose the best answer (A, B or C) for each space.",
            "questions": [
                _c("............ to wear special shoes to play hockey?",
                   ["You have", "Do you have", "Have you"], "B"),
                _c("To run a marathon, you ............ to be very fit.", ["has", "haven’t", "have"], "C"),
                _c("‘Do you have to play rugby at school?’ ‘No, we ............ .’",
                   ["didn’t", "do", "don’t"], "C"),
                _c("I want to join the beginners’ class because I ............ dance very well.",
                   ["couldn’t", "could", "can’t"], "C"),
                _c("Bill cycles to work, so he ............ have to spend hours in the gym "
                   "every day.", ["can’t", "doesn’t", "hasn’t"], "B"),
                _c("I ............ play volleyball last week because my back hurt.",
                   ["can’t", "could", "couldn’t"], "C"),
                _c("............ ski when you were a child?", ["Can you", "Could you", "You could"], "B"),
                _c("I ............ only swim a few metres when I started school.",
                   ["could", "can", "couldn’t"], "A"),
            ],
        },
    ],
}


STEP2_UNIT9 = {
    "level": "step2", "kind": "unit", "unit_no": 9,
    "title": "Step 2 · Unit 9 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["I’ll take them.", "I’d like some trousers.", "I’m not sure – large?"], "C"),
                _c("", ["Yes please – what colour would you like?", "Yes please – where are the fitting rooms?", "Yes please – large or extra large?"], "B"),
                _c("", ["I’m so sorry.", "Thank you.", "Sure, no problem."], "B"),
                _c("", ["I’d like to try this on, please.", "Size 34, please.", "I’m not sure actually."], "C"),
                _c("", ["Why don’t you try them on?", "What are you looking for?", "What are you wearing?"], "A"),
                _c("", ["Thanks – can I pay by card?", "Thanks – what are you looking for?", "Thanks – how much are they?"], "A"),
                _c("", ["I’d like a watch, please.", "Yes, two please.", "No, I’m fine thanks."], "A"),
                _c("", ["They’re brown.", "They’re size 40.", "They’re £50."], "C"),
            ],
        },
        {
            "title": "Part 2 · Clothes and shopping",
            "instructions": "Read the sentences about clothes and shopping. "
                            "Choose the missing word (A, B or C) for each "
                            "space.",
            "questions": [
                _c("It’s easy to get to the shopping centre because there’s a ............ "
                   "in the city centre.", ["chemist", "bus stop", "cash machine"], "B"),
                _c("It’s wet today, so I really need a ............ .",
                   ["raincoat", "dress", "necklace"], "A"),
                _c("The shops were fantastic and we were in one ............ for three hours!",
                   ["information desk", "entrance", "department store"], "C"),
                _c("In the shoe shop, I bought these ............ because I play tennis a lot.",
                   ["boots", "jeans", "trainers"], "C"),
                _c("My new ............ keeps my neck really warm on cold days.",
                   ["skirt", "jewellery", "scarf"], "C"),
                _c("Ask at the ............ for something for your headache.",
                   ["chemist", "post office", "theatre"], "A"),
                _c("We don’t drive to the shopping centre because the ............ is "
                   "always full.", ["information desk", "car park", "cash machine"], "B"),
                _c("It’s a hot day, so I’m wearing ............ and a T-shirt.",
                   ["gloves", "shorts", "earrings"], "B"),
            ],
        },
        {
            "title": "Part 3 · Clothes and shopping",
            "instructions": "Read the descriptions of some words about clothes "
                            "and shopping. The first letter is already there. "
                            "Write the whole word.",
            "questions": [
                _t("You put these on your hands when it is cold.   g _ _ _ _ _",
                   "gloves", "loves"),
                _t("People often wear these instead of shoes in winter.   b _ _ _ _",
                   "boots", "oots"),
                _t("This is another way to say £.   p _ _ _ _", "pound", "ound"),
                _t("You can buy things to read here.   b _ _ _ _ _ _ _",
                   "bookshop", "ookshop"),
                _t("You can wear this jewellery in your ears.   e _ _ _ _ _ _ _",
                   "earrings", "arrings"),
                _t("These can be long or short and you wear them on your feet.   "
                   "s _ _ _ _", "socks", "ocks"),
                _t("You can use these to go to the car park on top of the shopping "
                   "centre.   s _ _ _ _ _", "stairs", "tairs"),
                _t("When you go into a shopping centre you use this.   e _ _ _ _ _ _ _",
                   "entrance", "ntrance", "elevator", "levator"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the email from Carla to her friends. Choose "
                            "the best word (A, B or C) for each space.",
            "passage": """Carnival in Recife

Hi everyone!
I’m having a wonderful time here in Brazil. Today (25) ………… the last day of the carnival. I (26) ………… in Recife in the north of Brazil. Everybody (27) ………… about the carnival in Rio de Janeiro because it’s the most famous carnival in the world, but we (28) ………… having a big party here in Recife too. Right now lots of people (29) ………… in the street in special clothes. It’s fantastic.
I (30) ………… an orange dress and big gold earrings and a mask. The weather is warm here, so I don’t need to wear a jumper or raincoat!
At the moment (31) ………… walking to the centre of Recife with my friend. We (32) ………… going by bus because they’re all full. But that’s OK. There’s Brazilian music everywhere!""",
            "questions": [
                _c("", ["is being", "is", "be"], "B"),
                _c("", ["stay", "am staying", "stayed"], "B"),
                _c("", ["is knowing", "know", "knows"], "C"),
                _c("", ["are", "is", "be"], "A"),
                _c("", ["dance", "are dancing", "dances"], "B"),
                _c("", ["are wearing", "am wearing", "is wearing"], "B"),
                _c("", ["I", "I’ve", "I’m"], "C"),
                _c("", ["aren’t", "not", "isn’t"], "A"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about clothes and shopping. "
                            "Choose the best answer (A, B or C) for each space.",
            "questions": [
                _c("............ shorts in the summer?",
                   ["Do you wear", "Are you wearing", "You wore"], "A"),
                _c("Tom is not here – he ............ for us outside the bookshop.",
                   ["are waiting", "is waiting", "am waiting"], "B"),
                _c("Why don’t you ............ this jumper on?", ["try", "trying", "are trying"], "A"),
                _c("They often ............ for a coffee at the shopping mall.",
                   ["meet", "meets", "are meeting"], "A"),
                _c("............ these gloves because they’re exactly the right size.",
                   ["I’m not buying", "Am I buying", "I’m buying"], "C"),
                _c("............ for a blue shirt – can you help me?",
                   ["Do you look", "I’m looking", "I look"], "B"),
                _c("He usually ............ for his coffee by card.", ["pay", "is paying", "pays"], "C"),
                _c("Why ............ to the shopping centre now – it closes in thirty minutes?",
                   ["are you going", "you are going", "you aren’t going"], "A"),
            ],
        },
    ],
}


STEP2_UNIT10 = {
    "level": "step2", "kind": "unit", "unit_no": 10,
    "title": "Step 2 · Unit 10 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["You’re welcome.", "Great.", "Yes, of course."], "C"),
                _c("", ["I’m fine, thanks.", "You poor thing.", "No problem."], "C"),
                _c("", ["That looks great.", "Are you free on Friday?", "I’m sorry, I can’t."], "C"),
                _c("", ["Yes, I’d love to.", "Yes. Exactly.", "Yes. It doesn’t matter."], "B"),
                _c("", ["No, not at all.", "It’s right.", "That looks good."], "A"),
                _c("", ["So, first I touch this button?", "It’s right.", "How can I help?"], "A"),
                _c("", ["You’re welcome.", "Not at all.", "That’s right."], "B"),
                _c("", ["It takes me to another screen – like this?", "A light comes on. Are you all right?", "So, that’s the answer. Are you sure?"], "A"),
            ],
        },
        {
            "title": "Part 2 · Listening · Numbers",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the correct answer. You will hear "
                            "each sentence twice.",
            "questions": [
                _c("How many emails did the company receive last week?", ["704", "714", "750"], "B"),
                _c("How much did the man's tablet cost?", ["£390", "£395", "£399"], "C"),
                _c("How many smartphones did the company sell last year?",
                   ["5 million", "15 million", "50 million"], "C"),
                _c("How many kilometres is it from London to Sydney?",
                   ["16,900", "16,908", "16,980"], "C"),
                _c("How many people visited the website yesterday?",
                   ["420,000", "42,000", "4,200"], "A"),
                _c("How many stars can you see in the photo?",
                   ["84,500,000", "85,000,000", "85,000,500"], "A"),
                _c("What was the population of the Maldives in 2012?",
                   ["330,800", "338,000", "380,300"], "B"),
                _c("What is the population of this area?",
                   ["650,000,000", "615,000,000", "660,000,000"], "A"),
            ],
        },
        {
            "title": "Part 3 · Computers",
            "instructions": "Read the sentences about computers. Choose the "
                            "missing word (A, B or C) for each space.",
            "questions": [
                _c("I'm going to ............ all these documents in a file called "
                   "'Holiday plans'.", ["sit", "save", "stay"], "B"),
                _c("It can take a long time to ............ very large documents.",
                   ["click", "download", "log into"], "B"),
                _c("It wastes time if you ............ your emails more than three times a day.",
                   ["choose", "check", "change"], "B"),
                _c("If you ............ on the link in the email, you can see our holiday photos.",
                   ["click", "get", "take"], "A"),
                _c("Why don't you ............ our website to find out more information?",
                   ["go", "visit", "click"], "B"),
                _c("With Skype on my computer, I can ............ calls to my friend in Australia.",
                   ["make", "meet", "mix"], "A"),
                _c("My laptop is very slow – it is taking a long time to ............ this file.",
                   ["download", "click", "charge"], "A"),
                _c("How often do you ............ online to watch videos?", ["log", "make", "go"], "C"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the article about learning a language. "
                            "Choose the best word (A, B or C) for each space.",
            "passage": """How I learned Japanese

I'm American and I learned Japanese online a few years ago. I wanted to learn a different language and Japanese was (25) ………… for my job as a hotel receptionist. I also thought Japanese was (26) ………… than other languages because of the alphabet. Lessons with a private teacher were (27) ………… than lessons at a college. Online lessons were (28) ………… way to learn, so I joined an online course. Online courses are becoming (29) ………… than before for this reason.
The online lessons were easier than I thought. I could log into my computer at any time. I know Japanese is one of (30) ………… languages in the world but I really like it. I could learn anywhere and at any time – on the train to work, in the office at lunchtime, or at night.
Now I can speak (31) ………… Japanese than before. Online lessons are fantastic and I am (32) ………… hotel receptionist I know!""",
            "questions": [
                _c("", ["the most useful", "less useful", "more useful than"], "A"),
                _c("", ["more interesting", "the interesting", "the most interesting"], "A"),
                _c("", ["so expensive", "expensive", "more expensive"], "C"),
                _c("", ["cheaper", "the cheapest", "cheap"], "B"),
                _c("", ["more popular", "popular", "very popular"], "A"),
                _c("", ["harder", "hardest", "the hardest"], "C"),
                _c("", ["better", "best", "good"], "A"),
                _c("", ["happier than", "the happy", "the happiest"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about computers. Choose the "
                            "best answer (A, B or C) for each space.",
            "questions": [
                _c("Most tablets are ............ than a smartphone.", ["big", "bigger", "biggest"], "B"),
                _c("The new smartphones are ............ expensive ones.", ["most", "much", "the most"], "C"),
                _c("It's ............ to read a document on a tablet than on a smartphone.",
                   ["easy", "easier", "easiest"], "B"),
                _c("Many people say the ............ time to check emails is before you go to bed.",
                   ["bad", "worse", "worst"], "C"),
                _c("Tablets are ............ than smartphones because it is easier to watch "
                   "films and read newspapers on them.", ["more useful", "most useful", "useful"], "A"),
                _c("Some people think young people's spelling is ............ now because "
                   "they text too much.", ["bad", "worse", "worst"], "B"),
                _c("My father has ............ phone in our family – he bought it years ago!",
                   ["the old", "the older", "the oldest"], "C"),
                _c("The ............ expensive tablet in the shop costs over £1000!",
                   ["most", "much", "more"], "A"),
            ],
        },
    ],
}


STEP2_UNIT11 = {
    "level": "step2", "kind": "unit", "unit_no": 11,
    "title": "Step 2 · Unit 11 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["I agree.", "Yeah, me too.", "No problem."], "A"),
                _c("", ["I agree.", "No, me neither!", "Yes, it was great!"], "C"),
                _c("", ["Did you?", "Let me see.", "What did you think of it?"], "A"),
                _c("", ["I liked it – how about you?", "I don't really agree.", "Did you think so?"], "A"),
                _c("", ["Yes, maybe.", "Yeah, me too.", "Do you agree?"], "A"),
                _c("", ["No, maybe not.", "No, me neither.", "No, not at all."], "B"),
                _c("", ["Sure, no problem.", "I liked it – how about you?", "Yeah, me too!"], "C"),
                _c("", ["Not at all.", "Me neither.", "I don't really agree."], "C"),
            ],
        },
        {
            "title": "Part 2 · Entertainment",
            "instructions": "Read the sentences about entertainment. Choose the "
                            "missing word (A, B or C) for each space.",
            "questions": [
                _c("Did you hear the ............ concert last night?",
                   ["jazz", "singer", "musician"], "A"),
                _c("That ............ is the best place to hear top musicians from "
                   "around the world.", ["concert hall", "band", "classical music"], "A"),
                _c("The violin player has ............ her arm, so she isn't in the "
                   "orchestra this evening.", ["fallen", "broken", "grown"], "B"),
                _c("Have you ever ............ that musician here before?",
                   ["seen", "forgotten", "read"], "A"),
                _c("I've downloaded all the band's albums, but I've never ............ "
                   "this song before.", ["heard", "written", "caught"], "A"),
                _c("Dan thinks ............ music is better than folk music.",
                   ["rock", "role", "rest"], "A"),
                _c("I've ............ some chocolates for us to share while we watch the film.",
                   ["had", "eaten", "bought"], "C"),
                _c("Do you want to go to the ............ with me?",
                   ["band", "orchestra", "opera"], "C"),
            ],
        },
        {
            "title": "Part 3 · Music",
            "instructions": "Read the sentences about music. What are the "
                            "missing words? The first letter is already there. "
                            "Write the whole words.",
            "questions": [
                _t("Teenagers usually prefer to listen to p _ _  m _ _ _ _ .",
                   "pop music", "op usic"),
                _t("I'm so excited, I've never b _ _ _ to a concert before.", "been", "een"),
                _t("I love listening to d _ _ _ _  m _ _ _ _ when I do exercises.",
                   "dance music", "ance usic"),
                _t("Oh no! I've f _ _ _ _ _ _ _ _ my ticket for the concert!",
                   "forgotten", "orgotten"),
                _t("Peter has w _ _ _ _ _ _ a song for the band to play.", "written", "ritten"),
                _t("I think that s _ _ _ _ _ has a great voice!", "singer", "inger"),
                _t("Some people say c _ _ _ _ _ _ _ _  m _ _ _ _ is too slow and "
                   "boring, but I like it.", "classical music", "lassical usic"),
                _t("Philip has f _ _ _ _ all the way to Australia to see his "
                   "favourite band.", "flown", "lown"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the email from Melanie to her Australian "
                            "friend, Bob. Choose the best word (A, B or C) for "
                            "each space.",
            "passage": """Email to Bob

Hi Bob
How are you? I'm sorry I (25) ………… for a long time! I want to tell you about a great evening I (26) ………… in London last week. I met my brother at the British Library. Have you ever (27) ………… there? It's very modern and my brother likes studying there. When the library closed, we went to a Japanese restaurant. Have you (28) ………… eaten Japanese food? I think it's delicious!
After our meal, we (29) ………… a bus to his house, but walked to a café instead. We met some friends there and listened to some good jazz. You know (30) ………… to Australia – can you hear good music where you live? There have been some Australian films on at my local cinema and I liked the music in those. (31) ………… some interesting Australian musicians on the internet, but I've (32) ………… any Australian bands in London. Now I'm a bit sad because my brother isn't here. He's gone to Italy for three months to study art history.
Come and visit me in England soon!
Melanie""",
            "questions": [
                _c("", ["don't write", "haven't written", "didn't write"], "B"),
                _c("", ["had", "have had", "have"], "A"),
                _c("", ["gone", "been", "went"], "B"),
                _c("", ["never", "once", "ever"], "C"),
                _c("", ["didn't catch", "haven't caught", "don't catch"], "A"),
                _c("", ["I haven't been", "have I been", "I haven't gone"], "A"),
                _c("", ["I've also seen", "I also saw", "I also see"], "A"),
                _c("", ["ever heard", "heard", "never heard"], "C"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about entertainment and having "
                            "fun. Choose the best answer (A, B or C) for each "
                            "space.",
            "questions": [
                _c("Last night ............ a fantastic meal.",
                   ["John cooked", "John has cooked", "John cooks"], "A"),
                _c("I have ............ met a famous actor.", ["ever", "never", "always"], "B"),
                _c("Carolina ............ with us to the cinema yesterday because she's "
                   "already seen the film.", ["didn't come", "hasn't come", "isn't coming"], "A"),
                _c("This film ............ won a lot of prizes.", ["is", "has", "have"], "B"),
                _c("............ the tickets yesterday?",
                   ["Is Harry buying", "Has Harry bought", "Did Harry buy"], "C"),
                _c("I've never seen an opera but my brother ............ one last week.",
                   ["has seen", "saw", "hasn't seen"], "B"),
                _c("I'm surprised that dancer has never ............ over doing that crazy "
                   "jump – it's really difficult!", ["fell", "fallen", "fall"], "B"),
                _c("Have you ............ heard a big band like this before?",
                   ["ever", "once", "still"], "A"),
            ],
        },
    ],
}


STEP2_UNIT12 = {
    "level": "step2", "kind": "unit", "unit_no": 12,
    "title": "Step 2 · Unit 12 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["You're welcome!", "Really?", "I'm sorry, I can't."], "B"),
                _c("", ["Thanks for your help.", "Oh, can you really?", "Yes, how many would you like?"], "C"),
                _c("", ["That's a pity.", "Yes, maybe.", "It doesn't matter."], "B"),
                _c("", ["It's 12 o'clock on the day you leave.", "Your name, please.", "No, not at all."], "B"),
                _c("", ["Let me see.", "That’s great.", "Oh, dear."], "A"),
                _c("", ["No, it costs six pounds.", "It's from 7.15 until 10.15 a.m.", "Is it?"], "A"),
                _c("", ["Are you?", "That looks great.", "No, maybe not."], "A"),
                _c("", ["I'm sorry, I can't.", "Let me see.", "Have you?"], "C"),
            ],
        },
        {
            "title": "Part 2 · Travel",
            "instructions": "Read the sentences about travel. Choose the "
                            "missing word (A, B or C) for each space.",
            "questions": [
                _c("These boats take tourists to the ............ every day.",
                   ["island", "desert", "hill"], "A"),
                _c("I want to sit under a tree in the ............ and read my book today.",
                   ["glacier", "waterfall", "forest"], "C"),
                _c("Why don't we just pack a ............ and take a train somewhere?",
                   ["bag", "hotel", "holiday"], "A"),
                _c("Holidays are too expensive, so I'm going to ............ at home this summer.",
                   ["get", "live", "stay"], "C"),
                _c("I walked across that ............ today and took some photos of an old farm.",
                   ["sea", "lake", "field"], "C"),
                _c("When I was young we didn't ............ on holiday every year.",
                   ["book", "make", "go"], "C"),
                _c("To get to the hotel, turn right at the top of the ............ and go "
                   "straight on.", ["jungle", "hill", "wood"], "B"),
                _c("Can you ............ your plans and catch the earlier train tomorrow?",
                   ["make", "change", "stay"], "B"),
            ],
        },
        {
            "title": "Part 3 · Travel",
            "instructions": "Read the sentences about travel. What are the "
                            "missing words? The first letter is already there. "
                            "Write the whole words.",
            "questions": [
                _t("Klara doesn't want to s _ _ _ in that hotel again because the rooms "
                   "aren't clean.", "stay", "tay"),
                _t("I don't want to visit the d _ _ _ _ _ . It's so hot and there is no "
                   "water anywhere.", "desert", "esert"),
                _t("The trees in that w _ _ _ are very old and beautiful.", "wood", "ood"),
                _t("I want to swim across the l _ _ _ but it's too far.", "lake", "ake"),
                _t("Leo wants to b _ _ _ a hotel near the beach but they're expensive.",
                   "book", "ook"),
                _t("I love being in the c _ _ _ _ _ _ _ _ _ _ because it's quieter "
                   "than the city.", "countryside", "ountryside"),
                _t("I don't want to go b _ _ _  h _ _ _ because I'm really enjoying "
                   "my holiday.", "back home", "ack ome"),
                _t("Do you want to m _ _ _  p _ _ _ _ for the holiday now or can we do "
                   "it later?", "make plans", "ake lans"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the email about a college trip to a "
                            "rainforest. Choose the best word (A, B or C) for "
                            "each space.",
            "passage": """Trip to the rainforest

Here are details of the college trip to the rainforest next week. It's a long trip, starting at 6 a.m., so you should (25) ………… to bed early the night before. When you get there, you (26) ………… to walk through the rainforest to a waterfall. It's a beautiful place to stop for lunch. Lunch is included, but (27) ………… bring lots of water to drink. Remember that you (28) ………… carry too many things because it is very hot.
We're sure you have lots of questions, so here are answers to some of them:
• What time (29) ………… going to return to the hotel? Around 8 p.m.
• How many people (30) ………… going to be on the trip? No more than 12 people.
• (31) ………… bring any money with me? No. You aren't going anywhere you can spend money!
• Am I going to need a camera? Yes, (32) ………… ! The rainforest is a great place to take photos.""",
            "questions": [
                _c("", ["go", "to go", "going"], "A"),
                _c("", ["be going", "are going", "going"], "B"),
                _c("", ["you shouldn’t", "you should", "should you"], "B"),
                _c("", ["has to", "can", "shouldn’t"], "C"),
                _c("", ["are we", "we are", "do we"], "A"),
                _c("", ["is", "are", "be"], "B"),
                _c("", ["Should I", "I should", "I shouldn’t"], "A"),
                _c("", ["are you", "you are", "going to"], "B"),
            ],
        },
        {
            "title": "Part 5 · Grammar",
            "instructions": "Read the sentences about travel. Choose the best "
                            "answer (A, B or C) for each space.",
            "questions": [
                _c("He’s going ............ his friend at the airport.",
                   ["meet", "meeting", "to meet"], "C"),
                _c("To get there quickly, ............ change trains in London.",
                   ["you should", "should you", "shouldn’t you"], "A"),
                _c("We ............ going to take something to eat on the journey.",
                   ["are", "be", "have"], "A"),
                _c("How many bags should I ............ for our holiday?",
                   ["packing", "pack", "to pack"], "B"),
                _c("............ going to come on holiday to Spain with us?",
                   ["Do you", "Are you", "Can you"], "B"),
                _c("You ............ forget to take a sun hat to the beach.",
                   ["have to", "should", "shouldn’t"], "C"),
                _c("We ............ going to take a train to London – it’s too expensive.",
                   ["don’t", "not", "aren’t"], "C"),
                _c("............ buy my train tickets at the station or on the train?",
                   ["I shouldn’t", "Should I", "I should"], "B"),
            ],
        },
    ],
}


S2END_IMG = "/exam-img/step2-end/"
A_H = ["A", "B", "C", "D", "E", "F", "G", "H"]

# Step 2 End of course: Listening 1–15 + Reading 16–40. Listening
# faylida Part 4 (16–20) sahifasi yo'q edi — kelganda qo'shiladi.
# Reading raqamlari 15 taga surilgan.
STEP2_END = {
    "level": "step2", "kind": "end", "unit_no": None,
    "title": "Step 2 · End of course Test (Listening + Reading)",
    "paper_max": 0,
    "parts": [
        {
            "title": "Listening · Part 1",
            "instructions": "You will hear five short recordings. For each "
                            "question, choose the correct picture. You will "
                            "hear each recording twice.",
            "questions": [
                _c("Why has Chris got a headache?", ABC, "A", image=S2END_IMG + "l1.jpg"),
                _c("What would the woman like to have?", ABC, "B", image=S2END_IMG + "l2.jpg"),
                _c("Which man are they looking at?", ABC, "A", image=S2END_IMG + "l3.jpg"),
                _c("What is the man going to buy at the supermarket?", ABC, "A",
                   image=S2END_IMG + "l4.jpg"),
                _c("What does Sally want to buy in town?", ABC, "C", image=S2END_IMG + "l5.jpg"),
            ],
        },
        {
            "title": "Listening · Part 2",
            "instructions": "You will hear a man talking to a friend about the "
                            "transport he used on his holiday. What was the "
                            "problem with each one? You will hear the "
                            "conversation twice.",
            "questions": [
                _c("train", ["crowded", "dangerous", "dirty", "expensive", "late",
                             "noisy", "slow", "uncomfortable"], "D"),
                _c("scooter", ["crowded", "dangerous", "dirty", "expensive", "late",
                               "noisy", "slow", "uncomfortable"], "B"),
                _c("bus", ["crowded", "dangerous", "dirty", "expensive", "late",
                           "noisy", "slow", "uncomfortable"], "G"),
                _c("ferry", ["crowded", "dangerous", "dirty", "expensive", "late",
                             "noisy", "slow", "uncomfortable"], "A"),
                _c("helicopter", ["crowded", "dangerous", "dirty", "expensive", "late",
                                  "noisy", "slow", "uncomfortable"], "F"),
            ],
        },
        {
            "title": "Listening · Part 3",
            "instructions": "You will hear a radio interview with a man called "
                            "Tom, talking about a film he went to see this "
                            "week. For each question choose the correct "
                            "answer. You will hear the conversation twice.",
            "questions": [
                _c("Who did Tom go to the cinema with?",
                   ["his grandfather", "his grandson", "his uncle"], "B"),
                _c("What kind of music was in the film?", ["jazz", "pop", "rock"], "A"),
                _c("What did the main actor want to be at first?",
                   ["a director", "a photographer", "a pilot"], "C"),
                _c("What did the actor do each day to get fit?",
                   ["He went cycling.", "He played rugby.", "He went running."], "C"),
                _c("Tom thinks the film",
                   ["is going to be popular.", "is much too long.",
                    "is really a children's film."], "A"),
            ],
        },
        {
            "title": "Reading · Part 1 · Notices",
            "instructions": "Read the notices. Which notice (A – H) matches "
                            "each sentence?",
            "passage": """A   Wet paint. Please use side door.
B   Turn off all mobiles inside the hospital.
C   UNIVERSITY BOOKSTORE – Coffee Shop on first floor.
D   No food in this shop.
E   A1 Cinema – All tickets half price before 5pm.
F   Watch your head when you come in.
G   “Online Bookstore” – 20% off for all students.
H   Hotel guests. To call an outside line, press “9”.""",
            "questions": [
                _c("You can't eat in here.", A_H, "D"),
                _c("People at university can get things cheaper here.", A_H, "G"),
                _c("You have to go another way into the building.", A_H, "A"),
                _c("Take care here because you can hurt yourself.", A_H, "F"),
                _c("In this place, you can only use your phone outside.", A_H, "B"),
            ],
        },
        {
            "title": "Reading · Part 2 · Albert",
            "instructions": "Read the sentences about a student called Albert, "
                            "and choose the correct answer for each gap.",
            "questions": [
                _c("Albert comes from Germany but he ………… at university in London.",
                   ["is", "has", "does"], "A"),
                _c("Albert loves ………… photographs when he’s not studying.",
                   ["making", "having", "taking"], "C"),
                _c("Albert was happy because he got a good ………… in his exam.",
                   ["test", "mark", "note"], "B"),
                _c("Albert is going to go ………… in the holiday with his brother.",
                   ["golf", "exercises", "fishing"], "C"),
                _c("Albert has ………… lots of interesting places in London.",
                   ["seen", "looked", "watched"], "A"),
            ],
        },
        {
            "title": "Reading · Part 3 · James Cracknell",
            "instructions": "Read the text about James Cracknell and the "
                            "questions below. For each question, choose the "
                            "correct answer.",
            "passage": """James Cracknell

James Cracknell wanted to be a geography teacher, but never became one. Instead, he trained for the Olympic Games and won gold. He still loves sport, but these days he makes TV programmes about his travels.
Last year he and his friend, Ben Fogle, decided to travel across the Arabian desert; a place with almost no food or water. They wanted to make the same trip as another traveller called William Thesiger. Thesiger made the trip eighty years before them.
First, they had to buy some camels. It's a bit like buying a car – you need to check its health and age! But for James and Ben something else mattered more. They needed four camels, so the animals had to like each other. An angry camel is not a good idea in the desert!
A friend, Masalan, who makes similar journeys, gave them good advice. Camels eat most kinds of green food, but there is little in the desert. He said that they really love a local fruit, as much as humans love chocolate, and to take a big bag of them. Masalan also told them to follow a daily routine: Get up at 4.30, feed the camels, make a fire, drink tea but not too much water, leave before 7.00. Ride the camels for 5 hours, walk for 3, and then ride for another 2.""",
            "questions": [
                _c("Why did James go to the Arabian desert?",
                   ["to repeat someone else’s journey", "to meet an old friend who was there",
                    "to try and live on little food and water"], "A"),
                _c("The most important thing about each camel was that it",
                   ["was friendly to the others in the group.", "liked being with both Ben and James.",
                    "was healthy and was not too old."], "A"),
                _c("What did Masalan say to James and Ben about food?",
                   ["Give the camels the same food that you eat.",
                    "Camels can find enough food in the desert.",
                    "Carry lots of the camels’ favourite food."], "C"),
                _c("What advice did Masalan give Ben and James about their routine?",
                   ["Wake up at 7:00.", "Don’t sit on camels all day.",
                    "Have either tea or water at breakfast."], "B"),
                _c("What do we learn about Masalan?",
                   ["He wanted to go with James and Ben.", "He knew about life in the desert.",
                    "He has worked with camels all his life."], "B"),
            ],
        },
        {
            "title": "Reading · Part 4 · The Golf Alexander Hotel",
            "instructions": "Read the text about a hotel and choose the correct "
                            "answer for each gap.",
            "passage": """The Golf Alexander Hotel

Are you looking for a great place to stay? Do you need a relaxing holiday with amazing food and fantastic sports facilities? Then, (31) ………… are you waiting for? Come to the Golf Alexander Hotel. We (32) ………… give you your dream holiday!
Just look at what our guests say about us!
• 'The Golf Alexander Hotel has the (33) ………… comfortable beds I have ever slept on!'
• 'We had a brilliant time and we are going to come back next year.'
• 'The hotel staff were so friendly and (34) ………… happy to answer any of the questions we had.'
• 'My daughter could not swim before we came here (35) ………… now she can and she loves it – thanks to the fantastic pool staff at the Golf Alexander Hotel.'""",
            "questions": [
                _c("", ["why", "where", "what"], "C"),
                _c("", ["can", "want", "need"], "A"),
                _c("", ["much", "most", "more"], "B"),
                _c("", ["never", "always", "still"], "B"),
                _c("", ["but", "because", "so"], "A"),
            ],
        },
        {
            "title": "Reading · Part 5 · Hi everyone!",
            "instructions": "Read the text. Think of the word which best fits "
                            "each gap. Write ONE word for each gap.",
            "passage": """Hi everyone!
I have just bought a new tablet and I (36) ………… like some advice about what apps to get. Could you help me?
I already use my tablet for chatting with my family and friends and listening to music. However, I am (37) ………… to need it for work sometimes. (38) ………… you know a good app for downloading and working on documents?
I also enjoy sport and I go running every week. Which app is (39) ………… best one for planning routes and for keeping an exercise diary? And how (40) ………… does it cost? Or is it free?
Annie""",
            "questions": [
                _t("", "would", "’d"),
                _t("", "going", "sure", "certain", "bound"),
                _t("", "do"),
                _t("", "the"),
                _t("", "much"),
            ],
        },
    ],
}


# ------------------------------------------------------------- STEP 3
# Manba: "Step 3.0 Unit N.pdf" + "Unit N Progress Test Answer Key.pdf"
# (Cambridge English Empower B1 Unit Progress Test). 40 savol.

STEP3_UNIT1 = {
    "level": "step3", "kind": "unit", "unit_no": 1,
    "title": "Step 3 · Unit 1 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Yes, long time no see!", "How about you?", "It was really nice to meet you."], "A"),
                _c("", ["How nice of you.", "That sounds nice too.", "Nice to meet you, too."], "C"),
                _c("", ["About six months ago.", "Not far from here.", "Let’s go."], "B"),
                _c("", ["That’s fine.", "What a lovely surprise!", "Hi – nice to meet you."], "C"),
                _c("", ["How silly.", "We must meet up again soon.", "How are you?"], "B"),
                _c("", ["OK – I’ll give you a call next week.", "OK – how lovely.", "OK – and you?"], "A"),
                _c("", ["Yes, and see you again soon.", "That sounds great.", "Nice to meet him."], "A"),
                _c("", ["I’m John, by the way.", "Nice to meet you too.", "Robert, what a lovely surprise!"], "C"),
            ],
        },
        {
            "title": "Part 2 · Meeting and communicating",
            "instructions": "Read the sentences about meeting and "
                            "communicating with people. Choose the missing "
                            "word A, B or C for each space.",
            "questions": [
                _c("Richard thinks it's alright to finish a relationship by text but I "
                   "think it's ............ .", ["lovely", "awful", "brilliant"], "B"),
                _c("The girl I met yesterday was very nice but unfortunately she was "
                   "wearing an ............ dress.", ["ugly", "excellent", "attractive"], "A"),
                _c("My grandmother gets ............ upset if I don't phone her every week.",
                   ["generally", "mainly", "pretty"], "C"),
                _c("Leila's friends often text her when they're on holiday but they "
                   "............ send her postcards.", ["rarely", "always", "ever"], "A"),
                _c("The weather was ............ when the new students had their picnic "
                   "in the park.", ["delicious", "serious", "perfect"], "C"),
                _c("You should put this photo in your blog because you look ............ "
                   "in your wedding dress.", ["light", "gorgeous", "fair"], "B"),
                _c("My neighbour ............ loves getting letters from her grandchildren.",
                   ["exactly", "particularly", "nearly"], "B"),
                _c("I ............ use Facebook to say 'Happy birthday' to my friends "
                   "because it's the best way.", ["mainly", "fairly", "slowly"], "A"),
            ],
        },
        {
            "title": "Part 3 · Everyday life",
            "instructions": "Read the sentences about everyday life. What are "
                            "the missing words? The first letter is already "
                            "there. Write the whole words.",
            "questions": [
                _t("I don't want to play football in the snow – what a s _ _ _ _ idea!",
                   "silly", "illy"),
                _t("I h _ _ _ _ _  e _ _ _ get birthday cards these days – just messages "
                   "on my Facebook page.", "hardly ever", "ardly ver"),
                _t("Be polite not r _ _ _ when you speak to your boss.", "rude", "ude"),
                _t("If people don't communicate, it can cause s _ _ _ _ _ _ problems "
                   "such as arguments.", "serious", "erious"),
                _t("Tom is planning to cook a really d _ _ _ _ _ _ _ _ meal when his "
                   "girlfriend's parents come to dinner.", "delicious", "elicious"),
                _t("Lena is f _ _ _ _ _ good at writing academic essays - she doesn't "
                   "find it too difficult.", "fairly", "airly"),
                _t("Jack's parents worry about him so he g _ _ _ _ _ _ _ _ calls them "
                   "every weekend.", "generally", "enerally"),
                _t("Our teacher a _ _ _ _ _ _ _ _ _ hates lazy students!",
                   "absolutely", "bsolutely"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the young woman's blog about herself and her "
                            "apartment. Choose the best answer (A, B or C) for "
                            "each space.",
            "passage": """Sharing an apartment

My name's Claudia and I'm from Brazil. I'm living in London for a few months. Five mornings a week I go to a language school and six evenings a week I (25) ………… as a waitress in a Brazilian restaurant. The restaurant cook, Ben, (26) ………… the staff a delicious meal every evening after we (27) ………… work.
I'm renting a nice apartment with two bedrooms but it's too expensive for me to live there by myself. My brother's with me at the moment but he (28) ………… for a long time because he has to go back to Brazil soon. Now I am looking for the right person to share my apartment. Are you interested in sharing the apartment with me? If you think you might be, send me your answers to these questions:
What type of work or study (29) ………… ? When (30) ………… to London? (31) ………… you drive a car?
We need to clean the apartment ourselves. (32) ………… that worry you? If I like your answers, we can meet, get to know each other and talk some more about the apartment.""",
            "questions": [
                _c("", ["works", "work", "working"], "B"),
                _c("", ["is giving", "give", "gives"], "C"),
                _c("", ["finish", "are finishing", "is finishing"], "A"),
                _c("", ["doesn’t stay", "don’t stay", "isn’t staying"], "C"),
                _c("", ["you do", "do you", "do you do"], "C"),
                _c("", ["did you come", "you did come", "you came"], "A"),
                _c("", ["Does", "Are", "Can"], "C"),
                _c("", ["Do", "Does", "Is"], "B"),
            ],
        },
        {
            "title": "Part 5 · Sentence transformation",
            "instructions": "Complete the second sentence so that it means the "
                            "same as the first. Use no more than three words.",
            "questions": [
                _t("I think it's a great party - how about you?\n"
                   "What ………… think of the party? I think it’s great.", "do you"),
                _t("I watch a lot of TV every evening - how about you?\n"
                   "How much TV ………… every evening? - I watch a lot.", "do you watch"),
                _t("Katia hates birthday cake.\n"
                   "Katia really ………… like birthday cake.", "does not", "doesn’t"),
                _t("Is English the only language you speak?\n"
                   "………… any other languages than English?",
                   "Do you speak", "Can you speak"),
                _t("Mum needs help in the kitchen, so Magda and John are there with her.\n"
                   "Magda and John ………… helping Mum in the kitchen.", "are"),
                _t("Do you know how many people Anna invited to her party?\n"
                   "How many people ………… to her party – do you know?",
                   "did Anna invite", "did she invite"),
                _t("Jack's terrible at singing but what about dancing?\n"
                   "Jack can't sing but how well ………… he dance?", "can", "does"),
                _t("Roger's taking photos with his phone, not speaking on it.\n"
                   "Roger ………… speaking on his phone – he's taking photos with it.",
                   "is not", "isn’t"),
            ],
        },
    ],
}


STEP3_UNIT2 = {
    "level": "step3", "kind": "unit", "unit_no": 2,
    "title": "Step 3 · Unit 2 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Every 30 minutes.", "At 15.27.", "There’s a new one over there."], "B"),
                _c("", ["It's just round the corner.", "Actually, there is one more thing.", "It was great to see you again."], "B"),
                _c("", ["Yes, that’s right.", "Yes, of course.", "Yes, I can."], "B"),
                _c("", ["Well, when do you want to travel?", "You can buy one at the ticket office.", "Where can I buy a ticket?"], "A"),
                _c("", ["Yes, sure.", "Yes, you’re right.", "Yes, it is."], "A"),
                _c("", ["From stop number 12.", "It's just over there.", "Every 20 minutes."], "C"),
                _c("", ["Thank you for your help - you're very kind.", "That's great news, really great.", "Where's the bus station, please?"], "C"),
                _c("", ["It's in ten minutes.", "It's one and a half hours.", "This is platform eight."], "A"),
            ],
        },
        {
            "title": "Part 2 · Travel and holidays",
            "instructions": "Read the sentences about travel and holidays. "
                            "Choose the missing word A, B or C for each space.",
            "questions": [
                _c("I want to ............ for two weeks in September, maybe to Thailand.",
                   ["go out", "go away", "go on"], "B"),
                _c("There was snow at the airport so there were long ............ for flights.",
                   ["lifts", "breaks", "delays"], "C"),
                _c("It's always a good idea to ............ your accommodation before you "
                   "go on holiday.", ["order", "book", "ask"], "B"),
                _c("Adam never takes a suitcase on holiday - he just puts some things in "
                   "a small ............ .", ["backpack", "pocket", "luggage"], "A"),
                _c("What a terrible journey - our car ............ twice and we were six "
                   "hours late.", ["took off", "checked in", "broke down"], "C"),
                _c("Flying makes me nervous so I close my eyes when the plane takes off "
                   "or ............ .", ["finishes", "hits", "lands"], "C"),
                _c("Guests who are leaving the hotel must ............ before 10.00.",
                   ["check out", "check into", "check up"], "A"),
                _c("Sorry I’m late – I ............ my train.", ["lost", "missed", "arrived"], "B"),
            ],
        },
        {
            "title": "Part 3 · Travel and holidays",
            "instructions": "Read the sentences about travel and holidays. What "
                            "are the missing words? The first letter is "
                            "already there. Write the whole words.",
            "questions": [
                _t("Passengers at Gate 22 can b _ _ _ _ the plane to Amsterdam in ten "
                   "minutes.", "board", "oard"),
                _t("Jules decided to hitchhike in South America because he wanted to "
                   "have an exciting a _ _ _ _ _ _ _ _ .", "adventure", "dventure"),
                _t("How much money did you e _ _ _ _ _ _ _ at the bank before you went "
                   "to the USA last year?", "exchange", "xchange"),
                _t("Do I need a v _ _ _ or just a passport to visit your country?",
                   "visa", "isa"),
                _t("To remember my holidays, I always buy a s _ _ _ _ _ _ _ , like a "
                   "picture, from everywhere I visit.", "souvenir", "ouvenir"),
                _t("We'll get up early tomorrow so we can s _ _  o _ _ on our journey "
                   "at 7 o'clock.", "set out", "set off", "et ut", "et ff"),
                _t("We often forget to take a map so we g _ _  l _ _ _ when we visit "
                   "new places.", "get lost", "et ost"),
                _t("There was a long t _ _ _ _ _ _  j _ _ on the main road this morning "
                   "because of bad weather.", "traffic jam", "raffic am"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read a young man's story about a journey. Choose "
                            "the best answer (A, B or C) for each space.",
            "passage": """A lesson about luggage

Two years ago, I went from London to Barcelona in Spain by train. I (25) ………… planning to stay in Spain for a year so I (26) ………… two big suitcases and a backpack. Why (27) ………… so much? I don't know.
I changed trains in Paris. I had to go across the city by underground to another station. When I got off the train at my stop, I (28) ………… two suitcases, just one, and my backpack. I saw the second suitcase through the window of the train but the train was already moving. How silly of me!
The journey to Barcelona was at night and I (29) ………… most of the way. Some people (30) ………… a noise but they didn't bother me. (31) ………… at me? Perhaps they were. When I woke up in the morning, my suitcase wasn't there! Now I only had my backpack. But I was lucky – everything I needed was in it. Did I miss my suitcases? No, (32) ………… . This journey taught me a useful lesson – now I never travel with a lot of luggage.""",
            "questions": [
                _c("", ["were", "am", "was"], "C"),
                _c("", ["packed", "pack", "packing"], "A"),
                _c("", ["I took", "did I take", "am I taking"], "B"),
                _c("", ["am not carrying", "wasn’t carrying", "weren’t carrying"], "B"),
                _c("", ["were sleeping", "am sleeping", "slept"], "C"),
                _c("", ["was making", "is making", "were making"], "C"),
                _c("", ["Were they laughing", "They were laughing", "Did they laugh"], "A"),
                _c("", ["didn’t I", "I didn’t", "I did"], "B"),
            ],
        },
        {
            "title": "Part 5 · Sentence transformation",
            "instructions": "Complete the second sentence so that it means the "
                            "same as the first. Use no more than three words.",
            "questions": [
                _t("The weather was dry when the plane took off.\n"
                   "It ………… raining when the plane took off.", "wasn't", "was not"),
                _t("They went to sleep before the train arrived.\n"
                   "They ………… sleeping when the train arrived.", "were"),
                _t("Emma didn't spend a lot of money on holiday but I did.\n"
                   "I ………… a lot of money on holiday but Emma didn't.", "spent"),
                _t("Frank bought twenty postcards yesterday - what about Eva?\n"
                   "How many postcards ………… yesterday? Frank bought twenty.", "did Eva buy"),
                _t("Can you tell me where you went on holiday last year?\n"
                   "Where ………… on holiday last year?", "did you go"),
                _t("The food in our hotel wasn't good.\n"
                   "We ………… like the food in our hotel.", "didn't", "did not"),
                _t("My parents felt ill but they went on the boat trip.\n"
                   "My parents went on the boat trip, although they ………… feeling well.",
                   "weren't", "were not"),
                _t("Tell me what she was doing when she lost her ticket.\n"
                   "What ………… when she lost her ticket - tell me.", "was she doing"),
            ],
        },
    ],
}


STEP3_UNIT3 = {
    "level": "step3", "kind": "unit", "unit_no": 3,
    "title": "Step 3 · Unit 3 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["I don't agree with you.", "I'm looking for a present.", "It's half past twelve."], "B"),
                _c("", ["How would you like to pay?", "When does it leave?", "Where do you want to go?"], "A"),
                _c("", ["I don't mind.", "What about this?", "Thank you very much."], "C"),
                _c("", ["Who's next, please?", "Can you enter your PIN, please?", "Would you like a necklace, perhaps?"], "C"),
                _c("", ["Mm. What about this?", "Would you like to pay later?", "Here's your card."], "A"),
                _c("", ["If you like.", "Something fun.", "That’s all right."], "B"),
                _c("", ["What is it exactly?", "What has she bought?", "What sort of thing does she like?"], "C"),
                _c("", ["It tells you the weather and the time.", "It's ready for your PIN now.", "It's very expensive."], "A"),
            ],
        },
        {
            "title": "Part 2 · Money",
            "instructions": "Read the sentences about money. Choose the missing "
                            "word A, B or C for each space.",
            "questions": [
                _c("James always ............ a joke about owing money, but I don't like it.",
                   ["makes", "does", "gives"], "A"),
                _c("David ............ something really nice for me last week - he lent me £20!",
                   ["made", "gave", "did"], "C"),
                _c("The Bank Manager ............ Ben pay all the money he owed.",
                   ["gave", "got", "made"], "C"),
                _c("Alex got a large ............ from the bank to help him start his business.",
                   ["money", "loan", "account"], "B"),
                _c("I love that coat but I can't ............ to buy it.",
                   ["lend", "afford", "spend"], "B"),
                _c("Please can you ............ me £10 until tomorrow?",
                   ["pay", "borrow", "lend"], "C"),
                _c("Do people usually ............ taxi drivers a tip in your country?",
                   ["do", "give", "make"], "B"),
                _c("How much do I ............ you for the shopping you did for me?",
                   ["save", "buy", "owe"], "C"),
            ],
        },
        {
            "title": "Part 3 · Money",
            "instructions": "Read the sentences about money. What are the "
                            "missing words? The first letter is already there. "
                            "Write the whole word.",
            "questions": [
                _t("I don't have much money in my bank a _ _ _ _ _ _ until they pay me "
                   "next week.", "account", "ccount"),
                _t("Excuse me, please can you give me d _ _ _ _ _ _ _ _ _ to the nearest "
                   "bank?", "directions", "irections"),
                _t("The supermarket has got some very good special o _ _ _ _ _ this week.",
                   "offers", "ffers"),
                _t("He tried to make a j _ _ _ about having no money but nobody laughed.",
                   "joke", "oke"),
                _t("I've just been paid so I can pay you b _ _ _ the money you lent me.",
                   "back", "ack"),
                _t("Jana did very w _ _ _ at maths at school so perhaps she can help you "
                   "save money.", "well", "ell"),
                _t("Jack is hoping to b _ _ _ _ _ some money from his parents to buy a "
                   "new laptop.", "borrow", "orrow"),
                _t("Don't worry about the money, it's no problem – come here – let me "
                   "give you a big h _ _ .", "hug", "ug"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the letter from a girl to her friend. Choose "
                            "the best answer (A, B or C) for each space.",
            "passage": """Dear Zuzana

How are you? I hope you and your family are all well. I (25) ………… a great weekend. It was fantastic. I (26) ………… by train to visit my aunt. She lives in Scotland now. Have you ever been to Scotland? It (27) ………… my first visit and I loved it. My uncle and aunt (28) ………… there two months ago because my uncle got a job in the Bank of Scotland. My aunt's a teacher but she (29) ………… work yet. They have already bought a flat in the centre of Edinburgh, the capital city. They (30) ………… to pay a lot of money for it and it's very nice. I'd love to buy my own flat but I (31) ………… enough money yet. Do write and tell me how things are with you. I know you wanted to learn to drive. (32) ………… to have lessons?

All best wishes
Fiona""",
            "questions": [
                _c("", ["have already had", "have just had", "have still had"], "B"),
                _c("", ["am going", "have gone", "went"], "C"),
                _c("", ["is", "was", "has been"], "B"),
                _c("", ["have moved", "are moving", "moved"], "C"),
                _c("", ["isn’t finding", "hasn’t found", "doesn’t find"], "B"),
                _c("", ["need", "have needed", "needed"], "C"),
                _c("", ["haven’t saved", "am not saving", "don’t save"], "A"),
                _c("", ["Have you already start", "Have you already started", "Are you already starting"], "B"),
            ],
        },
        {
            "title": "Part 5 · Sentence transformation",
            "instructions": "Complete the second sentence so that it means the "
                            "same as the first. Use no more than three words.",
            "questions": [
                _t("It is ten o'clock and Jack is still doing his homework.\n"
                   "It is ten o'clock and Jack ………… finished his homework yet.",
                   "hasn't", "has not"),
                _t("I've been too busy to go shopping so we have no food.\n"
                   "I ………… had time to go shopping so we have no food.",
                   "haven't", "have not"),
                _t("Our visitors are just walking up to our front door.\n"
                   "Our visitors ………… arrived at our front door.",
                   "have just", "have", "just"),
                _t("I have bought so many things that I have no money now.\n"
                   "I ………… all my money.", "have spent", "spent"),
                _t("I love your new shoes - what did you pay for them, Sally?\n"
                   "I love your new shoes - how much ………… cost, Sally?", "did they"),
                _t("My parents are still in Canada.\n"
                   "My parents ………… returned from Canada yet.", "haven't", "have not"),
                _t("My sister often goes to Paris, but she never stays long.\n"
                   "My sister has ………… to Paris many times, but she never stays long.",
                   "been"),
                _t("We're too late - the bank closed two minutes ago.\n"
                   "We're too late - the bank has ………… closed.", "just", "already"),
            ],
        },
    ],
}


STEP3_UNIT4 = {
    "level": "step3", "kind": "unit", "unit_no": 4,
    "title": "Step 3 · Unit 4 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["I know you can.", "Just a moment - I'll ask Tom.", "Nothing, I'm free."], "B"),
                _c("", ["Yes, how about Tuesday?", "What time shall we come round?", "Hang on, I'll just check with Anna."], "C"),
                _c("", ["Sorry, how about Friday?", "Sorry, this week's really busy for me.", "Sorry, I can't do Saturday."], "B"),
                _c("", ["I think I'm next.", "We'll take it.", "I'll just check."], "C"),
                _c("", ["Very good.", "That sounds nice.", "Well, thanks."], "B"),
                _c("", ["What's the time?", "Is that OK for you?", "How about next week?"], "C"),
                _c("", ["I agree with you.", "No, don’t worry.", "Yes, that’s right."], "B"),
                _c("", ["Hang on a minute - let me see.", "I'm not sure - yes, I do.", "Actually, we will."], "A"),
            ],
        },
        {
            "title": "Part 2 · Going out",
            "instructions": "Read the sentences about going out. Choose the "
                            "missing word A, B or C for each space.",
            "questions": [
                _c("Some of the streets in the village are very ............ , so we can't "
                   "drive to the restaurant.", ["high", "low", "narrow"], "C"),
                _c("It's not a good idea to wear ............ because we're going to walk "
                   "to the cinema.", ["long socks", "trainers", "high heels"], "C"),
                _c("I love going to the ............ cinema in the summer because you can "
                   "look at the stars.", ["outdoor", "magnificent", "ordinary"], "A"),
                _c("Our house is really ............ and everybody stops to take photos of "
                   "it on their walks.", ["ordinary", "quiet", "pretty"], "C"),
                _c("David never has time to ............ before going out so he's growing "
                   "a beard.", ["get a new suit", "have a shave", "go to the hairdresser’s"], "B"),
                _c("It's difficult to ............ when you've just walked for an hour in "
                   "the rain.", ["have a new outfit", "look your best", "go to the shop"], "B"),
                _c("We went to a party in a ............ house and there was no space to dance.",
                   ["tiny", "huge", "peaceful"], "A"),
                _c("Take your ............ with you because it might be cold on the beach "
                   "this evening.", ["sweatshirt", "bracelet", "sandals"], "A"),
            ],
        },
        {
            "title": "Part 3 · Clothes and places",
            "instructions": "Read the descriptions of some words about clothes "
                            "and places. The first letter is already there. "
                            "Write the whole word.",
            "questions": [
                _t("This is what you wear under your jeans, sweatshirt or other clothes.   "
                   "u _ _ _ _ _ _ _ _", "underwear", "nderwear"),
                _t("You can wear this when you go jogging.   t _ _ _ _ _ _ _ _",
                   "tracksuit", "racksuit"),
                _t("People often get a new one if they're going to a wedding.   o _ _ _ _ _",
                   "outfit", "utfit"),
                _t("It describes a building that is hundreds of years old.   a _ _ _ _ _ _",
                   "ancient", "ncient"),
                _t("If there's nothing special about a place, you can describe it as "
                   "this.   o _ _ _ _ _ _ _", "ordinary", "rdinary"),
                _t("You wear these on your feet in the summer.   s _ _ _ _ _ _",
                   "sandals", "andals"),
                _t("It describes a building that is not beautiful to look at.   u _ _ _",
                   "ugly", "gly"),
                _t("This word describes a place where there's no noise and you can "
                   "relax.   p _ _ _ _ _ _ _", "peaceful", "eaceful"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the email from a woman to her friend. Choose "
                            "the best answer (A, B or C) for each space.",
            "passage": """To: Daniela
From: Sophie
Subject: This weekend

It's great that (25) ………… coming to visit me this weekend. Have you decided yet which train you are going to catch? Let me know and (26) ………… you at the station. Then perhaps (27) ………… dinner somewhere in the town centre and go to the cinema.
On Saturday evening there (28) ………… be a big concert in a park in the centre of town. Would you like to go? (29) ………… get tickets for us? Oh, and don't forget to bring flat shoes with you. I'd like to go for a long walk by the river on Sunday. It's lovely and peaceful there. But we (30) ………… if it's wet and horrible - we'll go to the gym instead.
(31) ………… to go home on Sunday evening or Monday morning? My brother (32) ………… to do a course in your town next week. Perhaps you can travel back there together?
See you very soon!
Sophie""",
            "questions": [
                _c("", ["you’re", "you’ll", "you’re going to"], "A"),
                _c("", ["I’m meeting", "I’ll meet", "I’m going to meet"], "B"),
                _c("", ["we’re having", "we’re going to have", "we’ll have"], "C"),
                _c("", ["is going to", "are going to", "is going"], "A"),
                _c("", ["Have I", "Am I", "Shall I"], "C"),
                _c("", ["don’t go", "not go", "won’t go"], "C"),
                _c("", ["Will you", "Are you going", "Are you"], "B"),
                _c("", ["is going", "will", "goes"], "A"),
            ],
        },
        {
            "title": "Part 5 · Sentence transformation",
            "instructions": "Complete the second sentence so that it means the "
                            "same as the first. Use no more than three words.",
            "questions": [
                _t("Dan offered to carry my computer for me.\n"
                   "Dan said: '………… carry your computer for you?'",
                   "Shall I", "Can I", "Could I", "May I"),
                _t("I know that John can't come to the meeting on Friday.\n"
                   "I know that John ………… coming to the meeting on Friday.",
                   "isn't", "is not", "won't be", "will not be"),
                _t("Zoe's plan is to study French at university.\n"
                   "Zoe is ………… study French at university.",
                   "going to", "planning to", "intending to"),
                _t("My idea is for us to start the meal with soup - what do you think?\n"
                   "What do you think? - ………… start the meal with soup?", "Shall we"),
                _t("Do you know what your outfit for the wedding on Saturday is going to be?\n"
                   "What are you ………… for the wedding on Saturday?",
                   "going to wear", "planning to wear", "intending to wear", "wearing"),
                _t("We haven't done the shopping yet - what about doing it later?\n"
                   "We haven't done the shopping yet - ………… do it later?",
                   "Shall we", "Could we", "Can we"),
                _t("I'm really tired so I don't want to go to the concert tonight.\n"
                   "I’m ………… to the concert tonight because I'm really tired.",
                   "not going", "not going to go"),
                _t("Thomas offered to take me to the station tomorrow.\n"
                   "'I ………… you to the station tomorrow,' said Thomas.",
                   "’ll take", "will take", "can take", "could take"),
            ],
        },
    ],
}


STEP3_UNIT5 = {
    "level": "step3", "kind": "unit", "unit_no": 5,
    "title": "Step 3 · Unit 5 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Don't worry about it - it's fine!", "Of course, it's no problem.", "Yes, maybe you could."], "A"),
                _c("", ["They'd love to do it.", "You're welcome.", "Yes, that's a good idea."], "C"),
                _c("", ["Yes, I think that’s everything.", "Sure, we’ll take it.", "OK, that would be great."], "C"),
                _c("", ["Do you think that will help me?", "Do you understand it?", "Do you want me to help you?"], "A"),
                _c("", ["There's just one more thing.", "That would really help.", "Yes, I can do that for you."], "B"),
                _c("", ["It's no problem - I'll be all right.", "Yes, that'd be great.", "Okay, it doesn't matter."], "A"),
                _c("", ["That's OK, I'm late too.", "Don't worry about it this time.", "Let's talk about the plan on Friday."], "B"),
                _c("", ["That's OK, if you don't mind.", "Would you like me to prepare the room?", "Will you organise tomorrow's meeting?"], "B"),
            ],
        },
        {
            "title": "Part 2 · Work and jobs",
            "instructions": "Read the sentences about work and jobs. Choose the "
                            "missing word A, B or C for each space.",
            "questions": [
                _c("I wouldn't like to be a ............ because they speak in front of "
                   "lots of people.", ["plumber", "politician", "gardener"], "B"),
                _c("Most electricians complete several years' ............ with a company "
                   "before they can work alone.", ["training", "skills", "homework"], "A"),
                _c("Many actors work ............ because that is when more people can go "
                   "to the theatre.", ["long hours", "at weekends", "every day"], "B"),
                _c("Receptionists do an important job but they don't usually earn a good "
                   "............ .", ["salary", "environment", "money"], "A"),
                _c("We took our cat to the ............ because she had a broken tooth.",
                   ["dentist", "farmer", "vet"], "C"),
                _c("Doctors and nurses make very important ............ about their "
                   "patients' health.", ["problems", "qualifications", "decisions"], "C"),
                _c("Why doesn't the company get a ............ to help with ideas for the "
                   "new reception area?", ["plumber", "waiter", "designer"], "C"),
                _c("The ............ worked hard in good and bad weather to complete our "
                   "new house on time.", ["accountants", "builders", "carers"], "B"),
            ],
        },
        {
            "title": "Part 3 · Work and jobs",
            "instructions": "Read the sentences about work and jobs. What are "
                            "the missing words? The first letter is already "
                            "there. Write the whole words.",
            "questions": [
                _t("To work as an a _ _ _ _ _ _ _ _ and design buildings, you need to "
                   "pass many exams.", "architect", "rchitect"),
                _t("Jude works from 7am to 8pm every day - very l _ _ _  h _ _ _ _ !",
                   "long hours", "ong ours"),
                _t("Some people prefer to work in a t _ _ _ instead of working alone.",
                   "team", "eam"),
                _t("You need good q _ _ _ _ _ _ _ _ _ _ _ _ _ to show that you know how "
                   "to do certain jobs.", "qualifications", "ualifications"),
                _t("A j _ _ _ _ _ _ _ _ _ reports the news, possibly on the radio or TV "
                   "or in newspapers.", "journalist", "ournalist"),
                _t("John plays the violin really well and wants to be a m _ _ _ _ _ _ _ .",
                   "musician", "usician"),
                _t("What time does the p _ _ _ _ _ _ usually bring the letters in the "
                   "morning?", "postman", "ostman"),
                _t("If money is very important to you, then you will want to earn a good "
                   "s _ _ _ _ _ .", "salary", "alary"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the blog about someone's first job as a "
                            "hairdresser. Choose the best answer (A, B or C) "
                            "for each space.",
            "passage": """My first job!

I've just got my first job as a hairdresser! To apply for jobs, you have (25) ………… a qualification - I got mine last month. The job is fun but also tiring. I stand most of the day and (26) ………… only sit down for a few minutes at break times.
Our customers are very important. There's a sign in our staff room: 'EMPLOYEES (27) ………… EVER BE RUDE TO CUSTOMERS.' It's a rule! Another rule is that we need to look nice, but we can choose our own clothes. I'm glad that we (28) ………… wear boring work clothes.
Although this (29) ………… be my perfect job, I'm happy for now. It's a great place to work so I'm confident (30) ………… be a good start to my career. I need this experience, so I've decided that I (31) ………… change jobs for at least a year.
(32) ………… be a safe career for the future? I think so - a computer can't cut your hair ... at least, not yet! But it might be possible in the future!""",
            "questions": [
                _c("", ["get", "to get", "got"], "B"),
                _c("", ["have to", "mustn’t", "can"], "C"),
                _c("", ["don’t have to", "don’t", "must not"], "C"),
                _c("", ["don’t have to", "mustn’t", "can’t"], "A"),
                _c("", ["might not", "do not", "is not"], "A"),
                _c("", ["it is", "it will", "it might"], "B"),
                _c("", ["aren’t", "don’t", "won’t"], "C"),
                _c("", ["This will", "Will this", "Will I"], "B"),
            ],
        },
        {
            "title": "Part 5 · Sentence transformation",
            "instructions": "Complete the second sentence so that it means the "
                            "same as the first. Use no more than three words.",
            "questions": [
                _t("You can choose to start working anytime between 8 and 10am.\n"
                   "You ………… have to start working exactly at 8am.", "don't", "do not"),
                _t("Those musicians are maybe going to start a new orchestra in future.\n"
                   "Those musicians might perhaps ………… a new orchestra in future.",
                   "start", "be starting"),
                _t("Visitors to our company fill in a form with their details - it's a rule.\n"
                   "Visitors to our company ………… fill in a form with their details.",
                   "need to", "have to", "must"),
                _t("Do you think there are definitely going to be postmen in the future?\n"
                   "………… there definitely be postmen in the future - what do you think?",
                   "Will"),
                _t("It is necessary for receptionists to speak clearly on the telephone.\n"
                   "Receptionists ………… to speak clearly on the telephone.", "need", "have"),
                _t("It is possible that Kate will decide to change her job.\n"
                   "Kate ………… decide to change her job.", "might", "may", "could"),
                _t("When are they allowed to take a break at work?\n"
                   "When ………… they take a break at work?", "can", "may"),
                _t("Without experience, Karim is certainly not going to get an interview.\n"
                   "Without experience, Karim certainly ………… not get an interview.", "will"),
            ],
        },
    ],
}


STEP3_UNIT6 = {
    "level": "step3", "kind": "unit", "unit_no": 6,
    "title": "Step 3 · Unit 6 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Yes, we shouldn't do that.", "Yes, do you think I should complain?", "No, that's terrible."], "B"),
                _c("", ["I wouldn't worry about it.", "I suppose so.", "I'm really sorry to hear that."], "A"),
                _c("", ["Yes, I think it is.", "I think it was very good.", "I don't think I should do that."], "C"),
                _c("", ["I'll do it for you.", "I'd use two alarms.", "I hope the classes are OK."], "B"),
                _c("", ["I'm really sorry to hear that.", "I'm really sorry but I can't.", "I'm really sorry about last week."], "A"),
                _c("", ["Yes, you will.", "Can I help you?", "You’re right."], "C"),
                _c("", ["I don't think that's a good idea.", "What do you think she should do?", "I'm sorry I don't think I can."], "A"),
                _c("", ["No, what do you think I should do?", "I don't think I should do that.", "OK, that should be right."], "B"),
            ],
        },
        {
            "title": "Part 2 · Feelings",
            "instructions": "Read the sentences about feelings. Choose the "
                            "missing word A, B or C for each space.",
            "questions": [
                _c("When my brother was a child, he was really ............ of big dogs.",
                   ["annoyed", "surprised", "frightened"], "C"),
                _c("When I ............ all the fun we had together as kids, I feel so happy.",
                   ["forget about", "think of", "deal with"], "B"),
                _c("We were ............ when we heard the terrible news.",
                   ["shocking", "shock", "shocked"], "C"),
                _c("Susan felt very nervous when she arrived ............ the test centre.",
                   ["at", "to", "with"], "A"),
                _c("I was angry when Eva told me how much money she ............ on that car.",
                   ["gave", "paid", "spent"], "C"),
                _c("I love being a lawyer but I have to work long hours - it's a ............ job.",
                   ["relaxing", "disappointing", "tiring"], "C"),
                _c("I felt worried when I ............ my doctor about my health - but I'm fine!",
                   ["asked", "talked", "listened"], "A"),
                _c("Was Lara really ............ when she didn't get that fantastic job?",
                   ["disappointed", "excited", "interested"], "A"),
            ],
        },
        {
            "title": "Part 3 · Feelings",
            "instructions": "Read the sentences about feelings. What are the "
                            "missing words? The first letter is already there. "
                            "Write the whole words.",
            "questions": [
                _t("Our week on holiday was very r _ _ _ _ _ _ _ - we loved having no "
                   "worries and nothing to do!", "relaxing", "elaxing"),
                _t("Please don't worry - we can d _ _ _  w _ _ _ this problem together!",
                   "deal with", "eal ith"),
                _t("I was very excited - I just couldn't think or c _ _ _ _ _ _ _ _ _ _  "
                   "o _ my work.", "concentrate on", "oncentrate n"),
                _t("When the bill came, I didn't have enough money - it was awful; I was "
                   "so e _ _ _ _ _ _ _ _ _ _ !", "embarrassed", "mbarrassed"),
                _t("My boss was angry because I forgot my laptop and had to b _ _ _ _ _ "
                   "one from him.", "borrow", "orrow"),
                _t("I get very a _ _ _ _ _ _ when people talk during a film at the cinema.",
                   "annoyed", "nnoyed"),
                _t("We were very t _ _ _ _ when we arrived so we went to bed early.",
                   "tired", "ired"),
                _t("How do you feel when you l _ _ _  a _ old photographs of yourself?",
                   "look at", "ook t"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read this website page giving advice about "
                            "preparing for job interviews. Choose the best "
                            "answer (A, B or C) for each space.",
            "passage": """Advice for people going to interviews

Before you go to a job interview, it is very important (25) ………… well for it. There are several things you can do, so what (26) ………… do first? They will probably ask you some questions about the company to find out what you know about it, so (27) ………… at the information on their website. Then you need to think about clothes and to decide what (28) ………… because it is important to look good. And don't forget to clean your shoes!
Plan the journey to your interview very carefully because it is important (29) ………… late. You might decide (30) ………… there, but leave early because there might be a traffic jam.
During the interview, you (31) ………… speak clearly and be relaxed. It is good to ask some questions about the job but you (32) ………… ask too many. At the end of the interview you might be surprised to find that you actually enjoyed it!""",
            "questions": [
                _c("", ["prepare", "to prepare", "preparing"], "B"),
                _c("", ["should you", "you should", "you shouldn’t"], "A"),
                _c("", ["look", "looked", "looks"], "A"),
                _c("", ["for wearing", "to wear", "can wear"], "B"),
                _c("", ["not to arrive", "don’t arrive", "not arriving"], "A"),
                _c("", ["drive", "to drive", "driving"], "B"),
                _c("", ["might", "should", "need"], "B"),
                _c("", ["won’t", "didn’t", "shouldn’t"], "C"),
            ],
        },
        {
            "title": "Part 5 · Sentence transformation",
            "instructions": "Complete the second sentence so that it means the "
                            "same as the first. Use no more than three words.",
            "questions": [
                _t("Making a mistake is an easy thing to do, so be careful.\n"
                   "It is easy ………… a mistake, so be careful.", "to make"),
                _t("Is it best for me to do exercise before or after work?\n"
                   "When ………… I do exercise - before or after work?", "should", "shall"),
                _t("I will wait for your advice - I promise.\n"
                   "I promise ………… for your advice.", "to wait", "I will wait", "I’ll wait"),
                _t("It's not really a good idea to drive when you're tired.\n"
                   "You ………… really drive when you're tired.", "should not", "shouldn’t"),
                _t("Is it a good idea to check prices online before going shopping?\n"
                   "Before going shopping, ………… check prices online?",
                   "should I", "should we", "should you", "should one",
                   "shouldn’t I", "shouldn’t we", "shouldn’t you", "shouldn’t one",
                   "shall I", "shall we"),
                _t("Mark gave me advice about going to the airport.\n"
                   "Mark gave me advice on how ………… to the airport.", "to go", "to get"),
                _t("You must be on time for our meeting please.\n"
                   "Please ………… late for our meeting.", "do not be", "don’t be"),
                _t("I need to get some money so I'm going to the bank.\n"
                   "I'm going to the bank ………… some money.", "to get", "to take out"),
            ],
        },
    ],
}


STEP3_UNIT7 = {
    "level": "step3", "kind": "unit", "unit_no": 7,
    "title": "Step 3 · Unit 7 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["What a relief.", "Oh, dear. Really?", "No, I don't think so."], "B"),
                _c("", ["Phew, that's good to hear.", "Yes, I had a broken leg.", "No, I don't think so."], "C"),
                _c("", ["I feel exhausted.", "Are you taking anything for the pain?", "Well, I usually go to the gym after work."], "B"),
                _c("", ["What a relief.", "Yes, I've got a cold.", "Sure, Doctor."], "C"),
                _c("", ["I can't get to sleep.", "Here, in this area.", "I feel sick."], "B"),
                _c("", ["When did this problem start?", "What does it do?", "I've taken some aspirin."], "A"),
                _c("", ["He's gone to the chemist.", "It really hurts when I walk.", "No, I don't think so."], "B"),
                _c("", ["Where does it hurt?", "Do you do any exercise?", "Can I have a look?"], "B"),
            ],
        },
        {
            "title": "Part 2 · Changes",
            "instructions": "Read the sentences about changes. Choose the "
                            "missing word A, B or C for each space.",
            "questions": [
                _c("People often join a gym to ............ weight.", ["fall", "miss", "lose"], "C"),
                _c("An old friend from school got in ............ with me last week.",
                   ["well", "touch", "together"], "B"),
                _c("In her first job, Alice got to ............ some important people.",
                   ["know", "talk", "find"], "A"),
                _c("Tom is a big man and often acts in roles as men who are slightly ............ .",
                   ["great", "full", "overweight"], "C"),
                _c("Don't stay in that job because you will never ............ rich.",
                   ["get", "make", "bring"], "A"),
                _c("People who eat cakes every day often ............ on weight.",
                   ["get", "take", "put"], "C"),
                _c("If you smoke 15 cigarettes a day, I think you're a ............ smoker now.",
                   ["regular", "busy", "general"], "A"),
                _c("They're so proud because their daughter's just got a ............ at "
                   "Oxford University.", ["point", "place", "part"], "B"),
            ],
        },
        {
            "title": "Part 3 · Changes in people's lives",
            "instructions": "Read the descriptions of some changes in people's "
                            "lives. The first letter is already there. Write "
                            "the whole words.",
            "questions": [
                _t("I've lost 5 kilos, but I didn't go on a d _ _ _ — I started running.",
                   "diet", "iet"),
                _t("Do you get p _ _ _ more money now than you used to in your old job?",
                   "paid", "aid"),
                _t("Leo wants to get f _ _ but he doesn't like doing exercise!", "fit", "it"),
                _t("They were unhappily married for 15 years so they got d _ _ _ _ _ _ _ "
                   "last year.", "divorced", "ivorced"),
                _t("Max gets on w _ _ _ with all the other boys in his new school.",
                   "well", "ell"),
                _t("Amanda and Tim got t _ _ _ _ _ _ _ after they met at the tennis club.",
                   "together", "ogether"),
                _t("He's trying to g _ _ _  u _ smoking, but he started 10 years ago when "
                   "he was 18.", "give up", "ive p"),
                _t("It's easy to keep in s _ _ _ _ if you do sport regularly.",
                   "shape", "hape"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the text about Michelle Obama. Choose the "
                            "best answer (A, B or C) for each space.",
            "passage": """Michelle Obama

Michelle LaVaughn Robinson was born in 1964 in Chicago, USA. She had a brother, Craig, who was older (25) ………… her and the family lived in a one-bedroom apartment in Chicago. They were a happy family who got on well together, but they (26) ………… to have a lot of money. However, the Robinson children learned two things from their parents: the first was that you must do the (27) ………… you can in school to get a good education and the second was that it's (28) ………… to work hard than to make a lot of money.
So Michelle used to (29) ………… hard every day and got a place at Princeton University. She trained as a lawyer and used (30) ………… in a Chicago company, where she got to know her future husband, Barack Obama. They got married in 1992. However, after he became US President, she worked less often on her own career in order to support her husband. Michelle (31) ………… to be unknown but she has become one of the (32) ………… women in the world.""",
            "questions": [
                _c("", ["than", "as", "like"], "A"),
                _c("", ["don't use", "not used", "didn't use"], "C"),
                _c("", ["good", "better", "best"], "C"),
                _c("", ["less important", "more important", "most important"], "B"),
                _c("", ["studying", "study", "studied"], "B"),
                _c("", ["work", "to working", "to work"], "C"),
                _c("", ["uses", "used", "using"], "B"),
                _c("", ["famous", "very famous", "most famous"], "C"),
            ],
        },
        {
            "title": "Part 5 · Sentence transformation",
            "instructions": "Complete the second sentence so that it means the "
                            "same as the first. Use no more than three words.",
            "questions": [
                _t("For a healthier life, eating well is more important than anything else.\n"
                   "The ………… thing for a healthy life is eating well.", "most important"),
                _t("My grandfather was a smoker, but he stopped for health reasons.\n"
                   "My grandfather ………… smoke, but he stopped for health reasons.",
                   "used to"),
                _t("Terry's diet was worse ten years ago.\n"
                   "Terry's diet ………… now than it was ten years ago.", "is better"),
                _t("In the 1950s, people thought less about what they ate.\n"
                   "In the 1950s, people didn't ………… to think so much about what they ate.",
                   "use"),
                _t("I've never had such an easy job.\n"
                   "This is ………… job I've had.", "the easiest"),
                _t("Were gyms popular in the 1980s?\n"
                   "Did many people ………… to go to the gym in the 1980s?", "use"),
                _t("I'm 1.80 metres tall now, and my older brother is 1.81 metres.\n"
                   "I'm almost ………… my older brother now.", "as tall as"),
                _t("Aunt Sarah didn't live in New York before but she does now.\n"
                   "Aunt Sarah ………… to live in New York.", "didn't use", "did not use"),
            ],
        },
    ],
}


STEP3_UNIT8 = {
    "level": "step3", "kind": "unit", "unit_no": 8,
    "title": "Step 3 · Unit 8 Progress Test",
    "paper_max": 0,
    "parts": [
        {
            "title": "Part 1 · Listening",
            "instructions": "You will hear eight short sentences. For each "
                            "one, choose the best reply. You will hear each "
                            "sentence twice.",
            "questions": [
                _c("", ["Long time no see!", "How nice.", "It doesn't matter."], "C"),
                _c("", ["I can't do Wednesday.", "Why don't I deal with this?", "I had to work until 10 every night."], "C"),
                _c("", ["Oh, dear. Really?", "No, there's no excuse.", "I'll just check."], "B"),
                _c("", ["That's OK.", "I think you should.", "Are you busy?"], "A"),
                _c("", ["That's good to hear.", "Well, it's not your fault.", "I don't think so."], "B"),
                _c("", ["I don't think that's a good idea.", "Don't worry about it.", "Can I have a look?"], "B"),
                _c("", ["Sorry. I meant to call you.", "I don't think that's a good idea.", "Well, how about Thursday?"], "A"),
                _c("", ["What a relief.", "I suppose so.", "No really, it's fine."], "C"),
            ],
        },
        {
            "title": "Part 2 · Free time and interests",
            "instructions": "Read the sentences about free time activities and "
                            "interests. Choose the missing word A, B or C for "
                            "each space.",
            "questions": [
                _c("I thought that that film was ............ by Robert Redford but I was wrong.",
                   ["decided", "driven", "directed"], "C"),
                _c("Are you watching that TV ............ about art that's on every "
                   "Wednesday evening?", ["stage", "series", "scheme"], "B"),
                _c("In the winter, lots of people go ............ and skiing in the mountains.",
                   ["skateboarding", "windsurfing", "snowboarding"], "C"),
                _c("The hills and mountains here are great for rock ............ .",
                   ["climbing", "diving", "skating"], "A"),
                _c("The new art gallery was ............ by a Scottish architect.",
                   ["imagined", "directed", "designed"], "C"),
                _c("If you like running, jumping and throwing, why not join the "
                   "............ club?", ["athletics", "gymnastics", "ice hockey"], "A"),
                _c("The first concert was ............ at the arts centre in 1979.",
                   ["performed", "played", "passed"], "A"),
                _c("People who go ............ can ride waves up to 20 metres high.",
                   ["scuba diving", "surfing", "ice skating"], "B"),
            ],
        },
        {
            "title": "Part 3 · Free time activities",
            "instructions": "Read the descriptions of some free time "
                            "activities. The first letter is already there. "
                            "Write the whole words.",
            "questions": [
                _t("When I went s _ _ _ _  d _ _ _ _ _ in the Red Sea, I saw lots of "
                   "amazing fish.", "scuba diving", "cuba iving"),
                _t("I'm reading a great n _ _ _ _ set in the future.", "novel", "ovel"),
                _t("Kim and I love running and we go j _ _ _ _ _ _ in the park together "
                   "every weekend.", "jogging", "ogging"),
                _t("My boyfriend's very romantic — he often writes love p _ _ _ _ for me.",
                   "poems", "oems"),
                _t("The sea along the coast here is perfect for sports like "
                   "w _ _ _ _ _ _ _ _ _ _ , sailing and waterskiing.",
                   "windsurfing", "indsurfing"),
                _t("I went i _ _  s _ _ _ _ _ _ on the lake this winter — it was wonderful.",
                   "ice skating", "ce kating"),
                _t("Jon's interested in a _ _ _ _ _ _ _ _ _ _ _ , so he reads a lot about "
                   "both old and modern buildings.", "architecture", "rchitecture"),
                _t("Can I take a p _ _ _ _ _ _ _ _ _ of you with my new camera?",
                   "photograph", "hotograph"),
            ],
        },
        {
            "title": "Part 4 · Reading",
            "instructions": "Read the article about Daniel Johnson, a child "
                            "artist. Choose the best answer (A, B or C) for "
                            "each space.",
            "passage": """The 11-year-old artist

Daniel Johnson is an 11-year-old artist. Recently, one of his paintings (25) ………… sold for £30,000. The painting shows a winter snow scene near his home in Scotland, where the young artist has (26) ………… all his life. Daniel (27) ………… been an artist since he first started painting scenes of nature on a family holiday at the age of 5. His abilities (28) ………… quickly recognised by his parents and when his pictures were (29) ………… to art experts, they agreed the boy had something special.
A local artist gave Daniel lessons and he learned fast, and got a lot of attention from the media. When his paintings go on sale, they (30) ………… bought for very large amounts of money by people from places like the USA and South Africa. Daniel's parents (31) ………… known for a long time that they need to make sure that he has a normal childhood. Daniel has always loved football, and has been a member of the school football team (32) ………… several years.""",
            "questions": [
                _c("", ["have", "were", "was"], "C"),
                _c("", ["live", "lived", "living"], "B"),
                _c("", ["is", "was", "has"], "C"),
                _c("", ["were", "have", "are"], "A"),
                _c("", ["show", "showing", "shown"], "C"),
                _c("", ["are", "have", "was"], "A"),
                _c("", ["have", "were", "are"], "A"),
                _c("", ["since", "for", "during"], "B"),
            ],
        },
        {
            "title": "Part 5 · Sentence transformation",
            "instructions": "Complete the second sentence so that it means the "
                            "same as the first. Use no more than three words.",
            "questions": [
                _t("JK Rowling wrote seven books about Harry Potter.\n"
                   "The seven Harry Potter books ………… JK Rowling.", "were written by"),
                _t("Someone stole the museum's most famous painting in 1931.\n"
                   "The museum's most famous painting ………… in 1931.", "was stolen"),
                _t("Michelangelo didn't paint the Mona Lisa.\n"
                   "The Mona Lisa ………… Michelangelo.",
                   "wasn't painted by", "was not painted by"),
                _t("When did JK Rowling start writing novels?\n"
                   "How ………… JK Rowling been a writer of novels?", "long has"),
                _t("Nigel's love of music started when he was a young child.\n"
                   "Nigel ………… since he was a young child.",
                   "has loved music", "’s loved music"),
                _t("They performed the play for the first time in 1858.\n"
                   "The play ………… for the first time in 1858.", "was performed"),
                _t("Peter became a professional musician in 2003.\n"
                   "Peter's been a professional musician ………… 2003.", "since"),
                _t("Maria was a teenager when she became an actor.\n"
                   "Maria has been an actor ………… a teenager.", "since she was"),
            ],
        },
    ],
}

TEMPLATES = [
    ("exam_tpl_step1_unit1", STEP1_UNIT1),
    ("exam_tpl_step1_unit2", STEP1_UNIT2),
    ("exam_tpl_step1_unit3", STEP1_UNIT3),
    ("exam_tpl_step1_unit4", STEP1_UNIT4),
    ("exam_tpl_step1_unit5", STEP1_UNIT5),
    ("exam_tpl_step1_unit6", STEP1_UNIT6),
    ("exam_tpl_step1_mid", STEP1_MID),
    ("exam_tpl_step1_unit7", STEP1_UNIT7),
    ("exam_tpl_step1_unit8", STEP1_UNIT8),
    ("exam_tpl_step1_unit9", STEP1_UNIT9),
    ("exam_tpl_step1_unit10", STEP1_UNIT10),
    ("exam_tpl_step1_unit11", STEP1_UNIT11),
    ("exam_tpl_step1_unit12", STEP1_UNIT12),
    ("exam_tpl_step1_end", STEP1_END),
    ("exam_tpl_step2_unit1", STEP2_UNIT1),
    ("exam_tpl_step2_unit2", STEP2_UNIT2),
    ("exam_tpl_step2_unit3", STEP2_UNIT3),
    ("exam_tpl_step2_unit4", STEP2_UNIT4),
    ("exam_tpl_step2_unit5", STEP2_UNIT5),
    ("exam_tpl_step2_unit6", STEP2_UNIT6),
    ("exam_tpl_step2_unit7", STEP2_UNIT7),
    ("exam_tpl_step2_unit8", STEP2_UNIT8),
    ("exam_tpl_step2_unit9", STEP2_UNIT9),
    ("exam_tpl_step2_unit10", STEP2_UNIT10),
    ("exam_tpl_step2_unit11", STEP2_UNIT11),
    ("exam_tpl_step2_unit12", STEP2_UNIT12),
    ("exam_tpl_step2_end", STEP2_END),
    ("exam_tpl_step3_unit1", STEP3_UNIT1),
    ("exam_tpl_step3_unit2", STEP3_UNIT2),
    ("exam_tpl_step3_unit3", STEP3_UNIT3),
    ("exam_tpl_step3_unit4", STEP3_UNIT4),
    ("exam_tpl_step3_unit5", STEP3_UNIT5),
    ("exam_tpl_step3_unit6", STEP3_UNIT6),
    ("exam_tpl_step3_unit7", STEP3_UNIT7),
    ("exam_tpl_step3_unit8", STEP3_UNIT8),
]
