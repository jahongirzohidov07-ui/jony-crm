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

TEMPLATES = [
    ("exam_tpl_step1_unit1", STEP1_UNIT1),
    ("exam_tpl_step1_unit2", STEP1_UNIT2),
    ("exam_tpl_step1_unit3", STEP1_UNIT3),
    ("exam_tpl_step1_unit4", STEP1_UNIT4),
    ("exam_tpl_step1_unit5", STEP1_UNIT5),
    ("exam_tpl_step1_unit6", STEP1_UNIT6),
    ("exam_tpl_step1_mid", STEP1_MID),
]
