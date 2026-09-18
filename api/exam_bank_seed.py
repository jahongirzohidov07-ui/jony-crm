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

TEMPLATES = [
    ("exam_tpl_step1_unit1", STEP1_UNIT1),
    ("exam_tpl_step1_unit2", STEP1_UNIT2),
    ("exam_tpl_step1_unit3", STEP1_UNIT3),
]
