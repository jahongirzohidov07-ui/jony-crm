# -*- coding: utf-8 -*-
# =====================================================================
#  PLACEMENT TEST — LISTENING BANKI
#
#  Ovoz brauzerning o'z ovoz sintezi bilan chiqadi (Jony Student
#  appdagi listening mashqlari ham shunday ishlaydi). Audio fayl
#  kerak emas, telefon brauzerida ham ishlaydi, xarajat yo'q.
#
#  Qoida: matn EKRANDA KO'RSATILMAYDI — faqat eshittiriladi.
#  Eng ko'pi bilan 2 marta tinglash mumkin.
#
#  Agar brauzerda ovoz ishlamasa, lid "Ovoz chiqmayapti" tugmasini
#  bosadi — bo'lim o'tkazib yuboriladi va natijada "tekshirilmadi"
#  deb yoziladi. Jazo yo'q: bu lidning aybi emas.
#
#  Tezlik daraja bilan oshadi: A1 sekin (0.80), C1 tabiiy (1.0).
# =====================================================================

LISTEN_ITEMS = [
    # ---------------- A1 ----------------
    {"id": 3001, "level": "A1", "rate": 0.80,
     "script": "Hello. My name is Anna. I am from Poland. I am a teacher.",
     "q": "What is Anna's job?",
     "opts": ["A teacher", "A doctor", "A driver", "A student"], "a": 0},
    {"id": 3002, "level": "A1", "rate": 0.80,
     "script": "The train leaves at seven o'clock. Please be at the "
               "station at half past six.",
     "q": "When does the train leave?",
     "opts": ["At half past six", "At seven o'clock",
              "At half past seven", "At eight o'clock"], "a": 1},
    {"id": 3003, "level": "A1", "rate": 0.80,
     "script": "I have two brothers and one sister. My sister is ten "
               "years old.",
     "q": "How old is the sister?",
     "opts": ["Two", "Ten", "One", "Twelve"], "a": 1},
    {"id": 3004, "level": "A1", "rate": 0.80,
     "script": "It is raining today, so we will stay at home and watch a "
               "film.",
     "q": "Why will they stay at home?",
     "opts": ["It is raining", "It is very hot", "They are tired",
              "The film is long"], "a": 0},
    {"id": 3005, "level": "A1", "rate": 0.80,
     "script": "The coffee is three dollars and the cake is five dollars.",
     "q": "How much is the cake?",
     "opts": ["Three dollars", "Five dollars", "Eight dollars",
              "Two dollars"], "a": 1},

    # ---------------- A2 ----------------
    {"id": 3101, "level": "A2", "rate": 0.85,
     "script": "Good morning. This is a message for Mr Davies. Your "
               "appointment on Thursday has been moved to Friday at "
               "eleven. Please call the clinic if that time does not suit "
               "you.",
     "q": "What has changed?",
     "opts": ["The day of the appointment", "The doctor",
              "The address of the clinic", "The price"], "a": 0},
    {"id": 3102, "level": "A2", "rate": 0.85,
     "script": "We are sorry to announce that flight BA209 to Rome is "
               "delayed by two hours because of bad weather. Passengers "
               "may collect a free drink voucher at the information desk.",
     "q": "Why is the flight delayed?",
     "opts": ["A technical problem", "Bad weather", "Late passengers",
              "A strike"], "a": 1},
    {"id": 3103, "level": "A2", "rate": 0.85,
     "script": "I usually cycle to work, but last week my bike was stolen "
               "from outside the office, so now I take the bus. It is "
               "slower, but at least I can read.",
     "q": "How does the speaker travel now?",
     "opts": ["By bike", "On foot", "By bus", "By car"], "a": 2},
    {"id": 3104, "level": "A2", "rate": 0.85,
     "script": "The museum is free on the first Sunday of every month. On "
               "other days, tickets cost eight pounds for adults, and "
               "children under twelve go free.",
     "q": "When is the museum free for everyone?",
     "opts": ["Every Sunday", "The first Sunday of the month",
              "Every day", "Never"], "a": 1},
    {"id": 3105, "level": "A2", "rate": 0.85,
     "script": "Could you tell Sara that I will be about twenty minutes "
               "late? The meeting I am in has overrun. Start without me "
               "and I will join when I arrive.",
     "q": "What does the speaker want Sara to do?",
     "opts": ["Wait for him", "Cancel the meeting", "Begin without him",
              "Call him back"], "a": 2},

    # ---------------- B1 ----------------
    {"id": 3201, "level": "B1", "rate": 0.92,
     "script": "When I started running, I made the classic mistake of "
               "going too fast. I would finish exhausted after two "
               "kilometres and then skip the next three days. What finally "
               "worked was slowing down to a pace where I could hold a "
               "conversation. It felt almost embarrassing, but I have run "
               "four times a week ever since.",
     "q": "What solved the speaker's problem?",
     "opts": ["Running longer distances", "Running more slowly",
              "Running with a group", "Buying better shoes"], "a": 1},
    {"id": 3202, "level": "B1", "rate": 0.92,
     "script": "Attention, shoppers. The lift in the east wing is out of "
               "order this afternoon while engineers carry out repairs. "
               "Customers who need step-free access should use the lift "
               "near the main entrance, which is operating normally.",
     "q": "What should customers needing step-free access do?",
     "opts": ["Use the stairs", "Come back tomorrow",
              "Use the lift by the main entrance",
              "Ask a member of staff for help"], "a": 2},
    {"id": 3203, "level": "B1", "rate": 0.92,
     "script": "I had booked the hotel because the photos showed a sea "
               "view. When we arrived, the room looked onto a car park. To "
               "be fair, the manager apologised immediately and moved us "
               "the next morning without charging anything extra.",
     "q": "How does the speaker feel about the hotel?",
     "opts": ["Completely satisfied",
              "Angry and unwilling to return",
              "Critical, but fair about the response",
              "Completely indifferent"], "a": 2},
    {"id": 3204, "level": "B1", "rate": 0.92,
     "script": "The course runs for eight weeks, with classes on Tuesday "
               "and Thursday evenings. There is no exam, but you will need "
               "to complete a short project by the final week. Places are "
               "limited to fifteen, so please confirm by Friday.",
     "q": "What must students do to complete the course?",
     "opts": ["Take an exam", "Complete a project",
              "Attend every single class", "Give a presentation"], "a": 1},
    {"id": 3205, "level": "B1", "rate": 0.92,
     "script": "We looked at four suppliers. The cheapest could not "
               "guarantee delivery dates, and the fastest was almost "
               "double the price. In the end we chose the second one, "
               "which was slightly more expensive than the cheapest but "
               "far more reliable.",
     "q": "Why did they choose that supplier?",
     "opts": ["It was the cheapest", "It was the fastest",
              "It balanced price and reliability",
              "It was recommended to them"], "a": 2},

    # ---------------- B1+ ----------------
    {"id": 3301, "level": "B1+", "rate": 0.95,
     "script": "The thing nobody tells you about working from home is that "
               "the problem is not distraction, it is that the day never "
               "ends. In an office you get up and leave. At home, the "
               "laptop is still there at nine in the evening, and "
               "answering one more email feels harmless. I now put mine in "
               "a cupboard at six.",
     "q": "What does the speaker identify as the main difficulty?",
     "opts": ["Too many distractions",
              "No clear end to the working day",
              "A poor internet connection", "Feeling lonely"], "a": 1},
    {"id": 3302, "level": "B1+", "rate": 0.95,
     "script": "I want to be clear that the delay is ours, not the "
               "supplier's. We changed the specification twice after the "
               "order was placed, and each change reset their production "
               "schedule. I would rather we acknowledged that now than "
               "discovered it in the review next month.",
     "q": "What is the speaker doing?",
     "opts": ["Blaming the supplier", "Accepting responsibility",
              "Requesting a discount", "Cancelling the order"], "a": 1},
    {"id": 3303, "level": "B1+", "rate": 0.95,
     "script": "Reviews of the restaurant are oddly divided. People who "
               "booked a table describe attentive service and excellent "
               "food; people who walked in report waiting forty minutes to "
               "be seated. It seems less a question of quality than of "
               "capacity - they simply cannot handle more than they have "
               "planned for.",
     "q": "What explains the divided reviews?",
     "opts": ["The food quality varies from day to day",
              "Staff are rude to certain customers",
              "The restaurant cannot handle unplanned demand",
              "The prices changed recently"], "a": 2},
    {"id": 3304, "level": "B1+", "rate": 0.95,
     "script": "We trialled the four-day week for six months. Output held "
               "steady, which surprised most of us. What did not hold "
               "steady was communication: with everyone off on different "
               "days, decisions that used to take an afternoon started "
               "taking a week. We have kept the four days but fixed the "
               "day off for everyone.",
     "q": "What problem did the trial reveal?",
     "opts": ["Output fell noticeably", "Staff became unhappy",
              "Decisions became much slower", "Costs increased"], "a": 2},
    {"id": 3305, "level": "B1+", "rate": 0.95,
     "script": "My advice to anyone learning an instrument as an adult is "
               "to stop comparing yourself to children. They are not "
               "faster learners; they simply practise daily without "
               "negotiating with themselves about it. Adults lose most of "
               "their time to the decision, not the practice.",
     "q": "What does the speaker say about adults?",
     "opts": ["They learn more slowly than children",
              "They waste time deciding whether to practise",
              "They should not start learning instruments",
              "They practise far too much"], "a": 1},

    # ---------------- B2 ----------------
    {"id": 3401, "level": "B2", "rate": 1.0,
     "script": "I would push back gently on the framing of the question. "
               "We keep asking whether remote work is more or less "
               "productive, as though productivity were a single quantity. "
               "For routine, well-specified tasks the evidence is fairly "
               "consistent and mildly positive. For work that depends on "
               "noticing that a colleague is struggling, or on the "
               "half-formed idea someone mentions in passing, we have "
               "almost no evidence at all. Averaging those together "
               "produces a number that describes nobody.",
     "q": "What is the speaker's main criticism?",
     "opts": ["Remote work clearly reduces productivity",
              "The question treats productivity as one single thing",
              "There is too much evidence to interpret",
              "Colleagues cannot be relied upon"], "a": 1},
    {"id": 3402, "level": "B2", "rate": 1.0,
     "script": "The grant was refused, and I think the reason is worth "
               "stating plainly. Our proposal was methodologically sound "
               "but it answered a question nobody outside the field is "
               "asking. That is a failure of framing, not of science. If "
               "we resubmit it unchanged with a better introduction, we "
               "will probably succeed, and I am slightly uncomfortable "
               "about what that tells us.",
     "q": "What makes the speaker uncomfortable?",
     "opts": ["The methodology was weak",
              "Presentation may matter more than substance",
              "The field is too small to matter",
              "The grant was far too large"], "a": 1},
    {"id": 3403, "level": "B2", "rate": 1.0,
     "script": "Historians are often asked when the war became inevitable, "
               "and the honest answer is that the question smuggles in its "
               "own conclusion. Contemporaries did not experience the "
               "period as a slope; they experienced it as a series of "
               "choices, most of which could have been made differently "
               "and several of which nearly were. Inevitability is "
               "something we add afterwards.",
     "q": "What does the speaker say about inevitability?",
     "opts": ["It was obvious to people at the time",
              "It is imposed later, looking back",
              "It applies only to wars",
              "All historians now agree about it"], "a": 1},
    {"id": 3404, "level": "B2", "rate": 1.0,
     "script": "There is a persistent belief that regulation slows "
               "innovation, and in some sectors it clearly has. But the "
               "pharmaceutical industry is a poor example to cite, because "
               "the approval process also creates the thing that makes "
               "investment possible: a credible signal that a drug works. "
               "Remove it and you do not get faster innovation, you get a "
               "market in which no serious investor can distinguish a "
               "breakthrough from a claim.",
     "q": "What point is the speaker making about regulation?",
     "opts": ["It always slows innovation down",
              "In this sector it is what makes investment possible",
              "It should be removed as soon as possible",
              "It is currently far too weak"], "a": 1},
    {"id": 3405, "level": "B2", "rate": 1.0,
     "script": "I have reviewed the complaints and I do not think we have "
               "a training problem. The staff know the policy; they can "
               "recite it. What they do not have is the authority to "
               "deviate from it, so when a customer presents a situation "
               "the policy did not anticipate, the only available answer "
               "is no. Sending everyone on another course will not change "
               "that.",
     "q": "What does the speaker identify as the real issue?",
     "opts": ["Staff lack knowledge of the policy",
              "Staff lack the authority to use judgement",
              "Customers are being unreasonable",
              "The policy has never been written down"], "a": 1},

    # ---------------- C1 ----------------
    {"id": 3501, "level": "C1", "rate": 1.0,
     "script": "What interests me is not that the forecasts were wrong - "
               "forecasts usually are - but that they were wrong in a "
               "correlated way. Nearly everyone erred in the same "
               "direction, which rules out random error and points instead "
               "to a shared assumption that nobody stated because nobody "
               "noticed holding it. That is the characteristic failure "
               "mode of a professional consensus: not stupidity, but an "
               "unexamined premise that the training reliably installs.",
     "q": "What does the correlation of the errors suggest to the "
          "speaker?",
     "opts": ["The forecasters were simply incompetent",
              "A shared, unexamined assumption",
              "The underlying data were falsified",
              "Ordinary random variation"], "a": 1},
    {"id": 3502, "level": "C1", "rate": 1.0,
     "script": "I am sceptical of the claim that the policy failed, though "
               "I accept it did not achieve its stated aim. Stated aims "
               "are frequently the least reliable guide to what a policy "
               "is for. This one was introduced in the middle of a crisis, "
               "it allowed the government to be seen acting, and it "
               "foreclosed a more radical proposal that was gathering "
               "support. Judged against those functions, it succeeded "
               "comfortably.",
     "q": "Why does the speaker resist calling the policy a failure?",
     "opts": ["It did achieve its stated aim",
              "It served purposes other than its stated aim",
              "The evidence is still incomplete",
              "It was never actually implemented"], "a": 1},
    {"id": 3503, "level": "C1", "rate": 1.0,
     "script": "There is a tension in the way we teach the subject that we "
               "have never resolved. We tell students that the canonical "
               "experiments are foundational, and we reproduce them in the "
               "first year, but several of them would not survive "
               "contemporary scrutiny - small samples, no pre-"
               "registration, effects that have not replicated. We are, in "
               "effect, using as an introduction to rigour a body of work "
               "that fails the standard we are introducing.",
     "q": "What contradiction does the speaker describe?",
     "opts": ["Students dislike the classic experiments",
              "Foundational studies fail the standards they teach",
              "The subject has become too difficult",
              "Replication is no longer considered necessary"], "a": 1},
    {"id": 3504, "level": "C1", "rate": 1.0,
     "script": "The difficulty with measuring teaching quality by student "
               "outcomes is not that the measure is noisy, though it is. "
               "It is that it is legible enough to be gamed and "
               "prestigious enough to be worth gaming, which is a worse "
               "combination than simply being inaccurate. An obviously "
               "crude measure gets ignored. A measure that is nearly good "
               "reorganises everyone's behaviour around it, and the "
               "resulting distortion is invisible precisely because the "
               "number keeps improving.",
     "q": "What is the speaker's central concern?",
     "opts": ["The measure is too crude to be used at all",
              "A nearly-good measure distorts behaviour while appearing "
              "to work",
              "Teaching quality cannot be assessed in any way",
              "Students are unreliable judges of teaching"], "a": 1},
    {"id": 3505, "level": "C1", "rate": 1.0,
     "script": "I would distinguish between two objections that are "
               "usually run together. One is that the translation is "
               "inaccurate, which is checkable and, in this case, mostly "
               "unfounded. The other is that it is accurate to the "
               "sentences and unfaithful to the book - that the register "
               "has been flattened, so that a prose which was strange in "
               "the original reads as merely competent in English. The "
               "second objection is the serious one.",
     "q": "What is the serious objection, according to the speaker?",
     "opts": ["Individual words have been mistranslated",
              "The style and register of the original have been lost",
              "The book is far too long",
              "The dictionary used was out of date"], "a": 1},
]

LISTEN_BY_LEVEL = {}
for _l in LISTEN_ITEMS:
    LISTEN_BY_LEVEL.setdefault(_l["level"], []).append(_l)
LISTEN_BY_ID = {x["id"]: x for x in LISTEN_ITEMS}
