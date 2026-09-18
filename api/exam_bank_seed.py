"""Boshlang'ich test bazasi (2026-09-18) — Jahongir yuborgan fayllardan.

Har element: (seed kaliti, test). Kalit bir marta yoziladi — keyin
examinerlar boshlig'i testni CRM'da (Audit -> Test bazasi) o'zi
tahrirlaydi, bu fayl uni qayta yozmaydi.

Manba: "Jony Academy exams. Step 1.0 Unit 1.pdf" + "Unit 1 Progress
Test AK.pdf" (javob kaliti)."""


def _c(q, opts, a):
    return {"type": "choice", "q": q, "options": opts, "answer": "ABC".index(a)}


def _t(q, *answers):
    return {"type": "text", "q": q, "answer": list(answers)}


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

TEMPLATES = [
    ("exam_tpl_step1_unit1", STEP1_UNIT1),
]
