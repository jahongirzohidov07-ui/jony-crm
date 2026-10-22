# =====================================================================
#  ADAPTIV INGLIZ TILI DIAGNOSTIKASI — SAVOLLAR BANKI
#
#  Cambridge Empower 2nd edition (A1 Starter → C1 Advanced) grammatika
#  syllabusi bo'yicha: har daraja 12 unit, har unitga 5 ta savol.
#  Savol = (daraja, unit, gap matni, [4 variant], to'g'ri indeks).
#  Qiyinlik zinasi: d = daraja_indeksi*12 + (unit-1)  →  0..71.
# =====================================================================
PT_LEVELS = ["A1", "A2", "B1", "B1+", "B2", "C1"]

PT_UNITS = {
    "A1": ["be: I/you, this/that", "be: he/she/they, possessives",
           "present simple: I/you/we/they", "present simple: he/she/it",
           "there is/are, possessive 's", "have got, can/can't",
           "past simple: be, regular verbs", "past simple: irregular, questions",
           "present continuous", "object pronouns, like + -ing",
           "going to, would like", "comparatives, superlatives"],
    "A2": ["question forms, present simple", "past simple",
           "present simple vs continuous, adverbs of frequency",
           "countable/uncountable, quantifiers", "comparatives, superlatives",
           "have to, don't have to", "past continuous",
           "should, imperatives, too/enough", "present perfect",
           "going to vs will", "will, may/might", "first conditional"],
    "B1": ["present simple/continuous, question forms",
           "past simple/continuous, present perfect vs past simple",
           "present perfect with for/since, narrative tenses",
           "present continuous for future, will/going to",
           "must/have to/can, will vs going to", "should, too/enough, imperatives",
           "comparatives, used to", "the passive, -ed/-ing adjectives",
           "present perfect continuous, relative clauses",
           "first and second conditional", "past passive, defining relative clauses",
           "reported speech"],
    "B1+": ["question forms, present tenses",
            "present perfect simple vs continuous",
            "narrative tenses, used to/usually", "modals of obligation, comparatives",
            "future forms, zero/first conditional", "modals of deduction, quantifiers",
            "too/enough, causative have", "reported speech, verb patterns",
            "the passive, relative clauses", "second and third conditional",
            "reported questions, -ed/-ing adjectives", "articles, wishes"],
    "B2": ["tense review, question forms", "narrative tenses, future time clauses",
           "multi-word verbs, present perfect simple/continuous",
           "used to/would, obligation and permission",
           "future probability, future perfect/continuous",
           "gerunds and infinitives, the passive", "too/enough, causative have",
           "conditionals, should have", "relative clauses, reported speech",
           "past modals of deduction, wishes and regrets",
           "passive reporting verbs, articles", "participle clauses, emphasis"],
    "C1": ["adverbs, present tenses", "narrative tenses, future forms",
           "inversion, future in the past", "noun phrases, have/get passive",
           "relative clauses, willingness/obligation",
           "simple vs continuous, participle clauses",
           "speculation and deduction, cleft sentences",
           "gerunds/infinitives, conditionals", "reflexive pronouns, ellipsis",
           "regrets and criticism, passive modals",
           "reported speech, mixed conditionals", "emphasis, inversion, articles"],
}

Q = []


def _a(lvl, unit, text, opts, ans):
    Q.append((lvl, unit, text, opts, ans))


# ------------------------------------------------------------- A1 ----
_a("A1", 1, "Hello! I ___ Anna.", ["am", "is", "are", "be"], 0)
_a("A1", 1, "___ is my friend, Tom.", ["This", "These", "Those", "They"], 0)
_a("A1", 1, "You ___ from Spain.", ["are", "is", "am", "be"], 0)
_a("A1", 1, "What ___ your name?", ["is", "are", "am", "do"], 0)
_a("A1", 1, "I'm not a teacher. I'm ___ student.", ["a", "an", "the", "—"], 0)
_a("A1", 2, "She ___ a doctor.", ["is", "are", "am", "have"], 0)
_a("A1", 2, "They ___ from Tashkent.", ["are", "is", "am", "be"], 0)
_a("A1", 2, "This is Ali. ___ car is red.", ["His", "He", "Her", "Him"], 0)
_a("A1", 2, "Where ___ they from?", ["are", "is", "am", "do"], 0)
_a("A1", 2, "We are students. ___ school is big.", ["Our", "We", "Us", "Ours"], 0)
_a("A1", 3, "I ___ coffee in the morning.", ["drink", "drinks", "drinking", "am drink"], 0)
_a("A1", 3, "___ you like music?", ["Do", "Does", "Are", "Is"], 0)
_a("A1", 3, "We ___ live in London.", ["don't", "doesn't", "aren't", "not"], 0)
_a("A1", 3, "They ___ English at school.", ["study", "studies", "studying", "are study"], 0)
_a("A1", 3, "What time ___ you get up?", ["do", "does", "are", "is"], 0)
_a("A1", 4, "She ___ in a bank.", ["works", "work", "working", "is work"], 0)
_a("A1", 4, "___ he speak French?", ["Does", "Do", "Is", "Are"], 0)
_a("A1", 4, "My brother ___ like fish.", ["doesn't", "don't", "isn't", "not"], 0)
_a("A1", 4, "Maria ___ TV every evening.", ["watches", "watch", "watching", "is watch"], 0)
_a("A1", 4, "Where ___ your father work?", ["does", "do", "is", "are"], 0)
_a("A1", 5, "___ a park near my house.", ["There is", "There are", "It is", "Is there"], 0)
_a("A1", 5, "___ two shops on this street.", ["There are", "There is", "They are", "It is"], 0)
_a("A1", 5, "This is ___ bag.", ["Sara's", "Sara", "of Sara", "Saras"], 0)
_a("A1", 5, "Is there ___ bank here?", ["a", "an", "some", "any"], 0)
_a("A1", 5, "There ___ any chairs in the room.", ["aren't", "isn't", "not", "no"], 0)
_a("A1", 6, "I ___ two sisters.", ["have got", "has got", "am got", "got"], 0)
_a("A1", 6, "She ___ swim very well.", ["can", "cans", "can to", "is can"], 0)
_a("A1", 6, "___ you drive a car?", ["Can", "Do can", "Are", "Have"], 0)
_a("A1", 6, "He ___ got a phone.", ["hasn't", "haven't", "isn't", "don't"], 0)
_a("A1", 6, "I can't ___ Chinese.", ["speak", "to speak", "speaking", "speaks"], 0)
_a("A1", 7, "I ___ at home yesterday.", ["was", "were", "am", "be"], 0)
_a("A1", 7, "They ___ at school last Monday.", ["were", "was", "are", "be"], 0)
_a("A1", 7, "We ___ football on Sunday.", ["played", "play", "playing", "plays"], 0)
_a("A1", 7, "___ you at the party last night?", ["Were", "Was", "Did", "Are"], 0)
_a("A1", 7, "She ___ in Paris in 2019.", ["lived", "lives", "living", "live"], 0)
_a("A1", 8, "I ___ to Samarkand last year.", ["went", "go", "goed", "gone"], 0)
_a("A1", 8, "___ you see the film?", ["Did", "Do", "Were", "Was"], 0)
_a("A1", 8, "He ___ a new phone yesterday.", ["bought", "buyed", "buy", "buys"], 0)
_a("A1", 8, "We ___ eat breakfast this morning.", ["didn't", "don't", "weren't", "not"], 0)
_a("A1", 8, "What ___ you do at the weekend?", ["did", "do", "were", "was"], 0)
_a("A1", 9, "Look! It ___.", ["is raining", "rains", "rain", "raining"], 0)
_a("A1", 9, "What ___ you doing now?", ["are", "do", "is", "did"], 0)
_a("A1", 9, "I ___ a blue jacket today.", ["am wearing", "wear", "wearing", "wears"], 0)
_a("A1", 9, "They ___ TV at the moment.", ["are watching", "watch", "watching", "watches"], 0)
_a("A1", 9, "She ___ working today. It's Sunday.", ["isn't", "doesn't", "not", "aren't"], 0)
_a("A1", 10, "I like Anna. I see ___ every day.", ["her", "she", "hers", "him"], 0)
_a("A1", 10, "Can you help ___?", ["me", "I", "my", "mine"], 0)
_a("A1", 10, "I love ___ to music.", ["listening", "listen", "to listening", "listens"], 0)
_a("A1", 10, "They know ___ very well.", ["us", "we", "our", "ours"], 0)
_a("A1", 10, "He doesn't like ___ early.", ["getting up", "get up", "to getting up", "gets up"], 0)
_a("A1", 11, "I ___ visit my grandmother tomorrow.", ["am going to", "go to", "going to", "will to"], 0)
_a("A1", 11, "I'd ___ a cup of tea, please.", ["like", "likes", "liking", "to like"], 0)
_a("A1", 11, "What ___ you going to do tonight?", ["are", "do", "is", "will"], 0)
_a("A1", 11, "She ___ going to come.", ["isn't", "doesn't", "not", "aren't"], 0)
_a("A1", 11, "___ you like some water?", ["Would", "Do", "Are", "Will"], 0)
_a("A1", 12, "My car is ___ than yours.", ["faster", "more fast", "fast", "fastest"], 0)
_a("A1", 12, "This is the ___ hotel in the city.", ["best", "better", "good", "most good"], 0)
_a("A1", 12, "London is ___ than Tashkent.", ["bigger", "more big", "biggest", "big"], 0)
_a("A1", 12, "It's the ___ day of the year.", ["hottest", "hotter", "most hot", "hot"], 0)
_a("A1", 12, "Chinese is ___ than English.", ["more difficult", "difficulter", "most difficult", "difficult"], 0)

# ------------------------------------------------------------- A2 ----
_a("A2", 1, "___ does she live?", ["Where", "What", "Who", "Which"], 0)
_a("A2", 1, "How ___ brothers have you got?", ["many", "much", "long", "often"], 0)
_a("A2", 1, "Who ___ you usually go out with?", ["do", "does", "are", "is"], 0)
_a("A2", 1, "___ often do you play tennis?", ["How", "What", "When", "Why"], 0)
_a("A2", 1, "What ___ your sister do?", ["does", "do", "is", "did"], 0)
_a("A2", 2, "I ___ my keys yesterday.", ["lost", "losed", "lose", "have lost"], 0)
_a("A2", 2, "When ___ you start this job?", ["did", "do", "were", "have"], 0)
_a("A2", 2, "They ___ get married in 2015.", ["didn't", "don't", "weren't", "haven't"], 0)
_a("A2", 2, "She ___ the exam two weeks ago.", ["took", "taked", "takes", "has taken"], 0)
_a("A2", 2, "He ___ up late and missed the bus.", ["got", "get", "gets", "getting"], 0)
_a("A2", 3, "I ___ to work by bus, but today I ___ a taxi.", ["usually go / am taking", "am usually going / take", "usually go / take", "am going / am taking"], 0)
_a("A2", 3, "She ___ late for work.", ["is never", "never is", "is not never", "never"], 0)
_a("A2", 3, "Be quiet! The baby ___.", ["is sleeping", "sleeps", "sleep", "slept"], 0)
_a("A2", 3, "We ___ pizza on Fridays.", ["often eat", "are often eating", "eat often", "often eating"], 0)
_a("A2", 3, "___ at the moment?", ["Are you working", "Do you work", "Work you", "You are working"], 0)
_a("A2", 4, "How ___ milk do we need?", ["much", "many", "lot", "a few"], 0)
_a("A2", 4, "There are ___ apples in the bag.", ["a few", "a little", "much", "any"], 0)
_a("A2", 4, "We haven't got ___ sugar.", ["any", "some", "a", "many"], 0)
_a("A2", 4, "Would you like ___ rice?", ["some", "any", "a", "many"], 0)
_a("A2", 4, "I don't eat ___ meat.", ["much", "many", "a few", "few"], 0)
_a("A2", 5, "This exercise is ___ than the last one.", ["easier", "more easy", "easiest", "easy"], 0)
_a("A2", 5, "She is the ___ person I know.", ["most intelligent", "more intelligent", "intelligentest", "intelligent"], 0)
_a("A2", 5, "My flat is ___ expensive ___ yours.", ["as / as", "so / as", "as / than", "more / as"], 0)
_a("A2", 5, "Today is ___ than yesterday.", ["worse", "badder", "more bad", "worst"], 0)
_a("A2", 5, "It's the ___ restaurant in town.", ["cheapest", "cheaper", "most cheap", "cheap"], 0)
_a("A2", 6, "I ___ wear a uniform at work.", ["have to", "must to", "has to", "have"], 0)
_a("A2", 6, "You ___ pay. It's free.", ["don't have to", "mustn't", "haven't to", "don't must"], 0)
_a("A2", 6, "___ she work on Saturdays?", ["Does / have to", "Has / to", "Must / to", "Do / has to"], 0)
_a("A2", 6, "He ___ get up early tomorrow.", ["has to", "have to", "has", "must to"], 0)
_a("A2", 6, "We ___ finish this today. There's no hurry.", ["don't have to", "mustn't", "haven't", "don't need"], 0)
_a("A2", 7, "I ___ TV when the phone rang.", ["was watching", "watched", "am watching", "watch"], 0)
_a("A2", 7, "What ___ you doing at 8 o'clock last night?", ["were", "was", "did", "are"], 0)
_a("A2", 7, "They ___ football when it started to rain.", ["were playing", "played", "play", "are playing"], 0)
_a("A2", 7, "While she ___, he was cooking.", ["was reading", "read", "reads", "is reading"], 0)
_a("A2", 7, "It ___ when I left the house.", ["wasn't raining", "didn't rain", "isn't raining", "not rained"], 0)
_a("A2", 8, "You ___ see a doctor.", ["should", "should to", "ought", "must to"], 0)
_a("A2", 8, "This tea is ___ hot to drink.", ["too", "enough", "very much", "so much"], 0)
_a("A2", 8, "He isn't old ___ to drive.", ["enough", "too", "very", "so"], 0)
_a("A2", 8, "___ smoke in here!", ["Don't", "Not", "No", "Doesn't"], 0)
_a("A2", 8, "You ___ eat so much sugar.", ["shouldn't", "don't should", "should not to", "not should"], 0)
_a("A2", 9, "I ___ never ___ to Japan.", ["have / been", "has / been", "did / go", "have / went"], 0)
_a("A2", 9, "___ you ever eaten sushi?", ["Have", "Did", "Do", "Are"], 0)
_a("A2", 9, "She ___ just ___ her homework.", ["has / finished", "have / finished", "has / finish", "is / finished"], 0)
_a("A2", 9, "We ___ seen that film yet.", ["haven't", "didn't", "hasn't", "don't"], 0)
_a("A2", 9, "He has ___ his keys. He can't get in.", ["lost", "losed", "lose", "losing"], 0)
_a("A2", 10, "Look at those clouds! It ___ rain.", ["is going to", "will", "is", "going to"], 0)
_a("A2", 10, "I'm tired. I think I ___ go to bed.", ["will", "am going to", "going to", "would"], 0)
_a("A2", 10, "We ___ a new car next month. We've decided.", ["are going to buy", "will buy", "buy", "buying"], 0)
_a("A2", 10, "The phone's ringing. I ___ answer it.", ["'ll", "'m going to", "going to", "would"], 0)
_a("A2", 10, "What ___ you going to do this summer?", ["are", "will", "do", "is"], 0)
_a("A2", 11, "I think it ___ be sunny tomorrow.", ["will", "is", "going to", "would"], 0)
_a("A2", 11, "She ___ come to the party. She isn't sure.", ["might", "will", "is", "must"], 0)
_a("A2", 11, "___ you help me with this?", ["Will", "Might", "Are", "May be"], 0)
_a("A2", 11, "It ___ rain later, so take an umbrella.", ["may", "will may", "is", "would"], 0)
_a("A2", 11, "People ___ live on Mars one day.", ["might", "are", "may be", "will be"], 0)
_a("A2", 12, "If it ___, we'll stay at home.", ["rains", "will rain", "rain", "rained"], 0)
_a("A2", 12, "If you study hard, you ___ the exam.", ["will pass", "pass", "passed", "would pass"], 0)
_a("A2", 12, "I'll call you if I ___ time.", ["have", "will have", "had", "would have"], 0)
_a("A2", 12, "If she ___ come, we'll start without her.", ["doesn't", "won't", "didn't", "not"], 0)
_a("A2", 12, "What ___ you do if you win the money?", ["will", "do", "did", "would"], 0)

# ------------------------------------------------------------- B1 ----
_a("B1", 1, "___ do you think of the new teacher?", ["What", "How", "Which", "Who"], 0)
_a("B1", 1, "Who ___ this cake? It's delicious.", ["made", "did make", "does make", "making"], 0)
_a("B1", 1, "I ___ this book. It's really good.", ["'m enjoying", "enjoy", "enjoying", "am enjoy"], 0)
_a("B1", 1, "She ___ two languages fluently.", ["speaks", "is speaking", "speak", "speaking"], 0)
_a("B1", 1, "What ___ you ___ about?", ["are / talking", "do / talk", "are / talk", "is / talking"], 0)
_a("B1", 2, "I ___ my leg while I ___ football.", ["broke / was playing", "was breaking / played", "broke / played", "was breaking / was playing"], 0)
_a("B1", 2, "I ___ Rome three times.", ["have visited", "visited", "have visit", "was visiting"], 0)
_a("B1", 2, "She ___ to Paris in 2018.", ["went", "has gone", "has been", "was going"], 0)
_a("B1", 2, "___ you ever ___ a famous person?", ["Have / met", "Did / meet", "Have / meet", "Did / met"], 0)
_a("B1", 2, "When I arrived, they ___ dinner.", ["were having", "had", "have had", "are having"], 0)
_a("B1", 3, "I've lived here ___ 2010.", ["since", "for", "from", "during"], 0)
_a("B1", 3, "We've known each other ___ ten years.", ["for", "since", "during", "ago"], 0)
_a("B1", 3, "How long ___ you had this car?", ["have", "did", "do", "are"], 0)
_a("B1", 3, "By the time we arrived, the film ___.", ["had started", "started", "has started", "was starting"], 0)
_a("B1", 3, "She ___ her phone, so she couldn't call.", ["had lost", "lost", "has lost", "was losing"], 0)
_a("B1", 4, "I ___ my dentist at 3 tomorrow.", ["'m seeing", "see", "will seeing", "am see"], 0)
_a("B1", 4, "Don't worry, I ___ help you.", ["'ll", "'m going to", "going to", "am"], 0)
_a("B1", 4, "We ___ to Turkey in July. We've booked the tickets.", ["'re going", "'ll go", "go", "would go"], 0)
_a("B1", 4, "What time ___ the train leave?", ["does", "will", "is", "are"], 0)
_a("B1", 4, "I promise I ___ be late.", ["won't", "'m not going to", "don't", "not"], 0)
_a("B1", 5, "You ___ be quiet in the library.", ["must", "have", "should to", "can"], 0)
_a("B1", 5, "You ___ park here. It's not allowed.", ["can't", "don't have to", "mustn't to", "haven't to"], 0)
_a("B1", 5, "I ___ work tomorrow. It's a holiday.", ["don't have to", "mustn't", "can't", "haven't"], 0)
_a("B1", 5, "Look, the bus is coming. We ___ make it!", ["'re going to", "will", "must", "have to"], 0)
_a("B1", 5, "You ___ smoke in hospitals.", ["mustn't", "don't have to", "haven't to", "not must"], 0)
_a("B1", 6, "It's ___ cold to go swimming.", ["too", "enough", "very", "so"], 0)
_a("B1", 6, "There aren't ___ chairs for everyone.", ["enough", "too", "too many", "very"], 0)
_a("B1", 6, "You ___ talk to her about it.", ["should", "should to", "ought", "had"], 0)
_a("B1", 6, "___ forget to lock the door.", ["Don't", "Not", "No", "Didn't"], 0)
_a("B1", 6, "The room is big ___ for ten people.", ["enough", "too", "so", "very"], 0)
_a("B1", 7, "I ___ play the piano, but I stopped.", ["used to", "use to", "was used to", "am used to"], 0)
_a("B1", 7, "Life is ___ than it used to be.", ["much easier", "more easier", "much more easy", "easyer"], 0)
_a("B1", 7, "The ___ you practise, the better you get.", ["more", "most", "much", "many"], 0)
_a("B1", 7, "Did you ___ live in the countryside?", ["use to", "used to", "using to", "be used to"], 0)
_a("B1", 7, "This phone is ___ as expensive as that one.", ["not", "no", "less", "much"], 0)
_a("B1", 8, "The Mona Lisa ___ by Leonardo da Vinci.", ["was painted", "painted", "is painting", "has painted"], 0)
_a("B1", 8, "Coffee ___ in Brazil.", ["is grown", "grows", "is growing", "grown"], 0)
_a("B1", 8, "I was really ___ by the film.", ["bored", "boring", "bore", "boredom"], 0)
_a("B1", 8, "The lesson was very ___.", ["interesting", "interested", "interest", "interestingly"], 0)
_a("B1", 8, "These cars ___ in Germany.", ["are made", "make", "are making", "made"], 0)
_a("B1", 9, "I ___ for two hours. I'm exhausted.", ["'ve been running", "'m running", "run", "was running"], 0)
_a("B1", 9, "That's the man ___ lives next door.", ["who", "which", "whose", "what"], 0)
_a("B1", 9, "This is the book ___ I told you about.", ["which", "who", "whose", "where"], 0)
_a("B1", 9, "How long ___ you been learning English?", ["have", "are", "do", "did"], 0)
_a("B1", 9, "She's the girl ___ brother is a singer.", ["whose", "who", "which", "that"], 0)
_a("B1", 10, "If I ___ rich, I'd travel the world.", ["were", "am", "will be", "would be"], 0)
_a("B1", 10, "If it rains, we ___ inside.", ["'ll stay", "'d stay", "stay", "stayed"], 0)
_a("B1", 10, "What would you do if you ___ a wallet?", ["found", "find", "will find", "would find"], 0)
_a("B1", 10, "I ___ you if I had your number.", ["would call", "will call", "call", "called"], 0)
_a("B1", 10, "If you ___ now, you'll catch the bus.", ["leave", "left", "would leave", "will leave"], 0)
_a("B1", 11, "The telephone ___ in 1876.", ["was invented", "invented", "is invented", "has invented"], 0)
_a("B1", 11, "A dictionary is a book ___ explains words.", ["that", "who", "what", "whose"], 0)
_a("B1", 11, "The bridge ___ last year.", ["was built", "built", "has built", "is built"], 0)
_a("B1", 11, "That's the café ___ we first met.", ["where", "which", "that", "who"], 0)
_a("B1", 11, "The letters ___ yesterday.", ["were sent", "sent", "are sent", "have sent"], 0)
_a("B1", 12, "He said he ___ tired.", ["was", "is", "were", "be"], 0)
_a("B1", 12, "She told me she ___ come the next day.", ["would", "will", "can", "is"], 0)
_a("B1", 12, "They said they ___ the film before.", ["had seen", "have seen", "saw", "see"], 0)
_a("B1", 12, "He ___ me that he was busy.", ["told", "said", "say", "tell"], 0)
_a("B1", 12, "'I live in Rome.' → She said she ___ in Rome.", ["lived", "lives", "living", "is living"], 0)

# ------------------------------------------------------------- B1+ ---
_a("B1+", 1, "___ you ___ for someone?", ["Are / waiting", "Do / wait", "Are / wait", "Do / waiting"], 0)
_a("B1+", 1, "Who ___ you sit next to at school?", ["did", "were", "have", "do you"], 0)
_a("B1+", 1, "I ___ what you mean.", ["don't understand", "'m not understanding", "not understand", "don't understanding"], 0)
_a("B1+", 1, "___ was the meeting like?", ["What", "How", "Which", "Who"], 0)
_a("B1+", 1, "She ___ to Spain twice this year.", ["has been", "was", "has gone", "went"], 0)
_a("B1+", 2, "I ___ this essay all morning and I'm still not finished.", ["'ve been writing", "'ve written", "wrote", "'m writing"], 0)
_a("B1+", 2, "She ___ three emails so far today.", ["has written", "has been writing", "wrote", "is writing"], 0)
_a("B1+", 2, "Your eyes are red. ___?", ["Have you been crying", "Have you cried", "Did you cry", "Do you cry"], 0)
_a("B1+", 2, "How many times ___ you ___ him?", ["have / called", "have / been calling", "did / calling", "are / calling"], 0)
_a("B1+", 2, "We ___ each other since we were children.", ["'ve known", "'ve been knowing", "know", "knew"], 0)
_a("B1+", 3, "When I got home, someone ___ the window.", ["had broken", "broke", "has broken", "was breaking"], 0)
_a("B1+", 3, "I ___ hate vegetables, but now I love them.", ["used to", "would", "use to", "was used to"], 0)
_a("B1+", 3, "She ___ along the road when she saw the accident.", ["was walking", "walked", "had walked", "has walked"], 0)
_a("B1+", 3, "Every summer we ___ go to the seaside.", ["would", "used", "were", "had"], 0)
_a("B1+", 3, "By the time the police arrived, the thief ___.", ["had escaped", "escaped", "has escaped", "was escaping"], 0)
_a("B1+", 4, "You ___ to wear a helmet on a motorbike.", ["have", "must", "should", "ought"], 0)
_a("B1+", 4, "You ___ bring food. There'll be plenty.", ["needn't", "mustn't", "can't", "shouldn't"], 0)
_a("B1+", 4, "She's ___ more confident than her sister.", ["far", "very", "too", "much more"], 0)
_a("B1+", 4, "It's ___ the hardest exam I've taken.", ["by far", "far", "much", "very"], 0)
_a("B1+", 4, "We ___ leave early yesterday because of the storm.", ["had to", "must", "should", "have to"], 0)
_a("B1+", 5, "I'll call you as soon as I ___.", ["arrive", "will arrive", "arrived", "would arrive"], 0)
_a("B1+", 5, "If you heat ice, it ___.", ["melts", "will melt", "would melt", "melted"], 0)
_a("B1+", 5, "This time next week I ___ on a beach.", ["'ll be lying", "'ll lie", "'m lying", "lie"], 0)
_a("B1+", 5, "Unless it ___, we'll go for a walk.", ["rains", "will rain", "doesn't rain", "rained"], 0)
_a("B1+", 5, "The train ___ at 6.45 tomorrow morning.", ["leaves", "will leaving", "is leave", "would leave"], 0)
_a("B1+", 6, "The lights are off. They ___ be at home.", ["can't", "mustn't", "shouldn't", "needn't"], 0)
_a("B1+", 6, "He's got a huge house. He ___ be rich.", ["must", "can", "might not", "should"], 0)
_a("B1+", 6, "___ of my friends speak Russian.", ["Most", "Most of", "The most", "Almost"], 0)
_a("B1+", 6, "There's ___ traffic today than usual.", ["less", "fewer", "few", "little"], 0)
_a("B1+", 6, "She ___ be at work — it's Sunday.", ["might not", "can't to", "mustn't", "needn't"], 0)
_a("B1+", 7, "I had my car ___ yesterday.", ["repaired", "repair", "to repair", "repairing"], 0)
_a("B1+", 7, "The flat isn't big ___ for a family.", ["enough", "too", "so", "very"], 0)
_a("B1+", 7, "We're having the kitchen ___ next month.", ["painted", "paint", "painting", "to paint"], 0)
_a("B1+", 7, "There's ___ much noise to work here.", ["too", "enough", "so", "very"], 0)
_a("B1+", 7, "Where do you get your hair ___?", ["cut", "cutting", "to cut", "cuts"], 0)
_a("B1+", 8, "She asked me ___ I was from.", ["where", "that where", "where was", "from where that"], 0)
_a("B1+", 8, "He promised ___ me.", ["to help", "helping", "help", "that help"], 0)
_a("B1+", 8, "They suggested ___ a taxi.", ["taking", "to take", "take", "that take"], 0)
_a("B1+", 8, "She told me ___ the door.", ["to lock", "lock", "locking", "that lock"], 0)
_a("B1+", 8, "I can't stand ___ in queues.", ["waiting", "to wait", "wait", "for waiting"], 0)
_a("B1+", 9, "The new stadium ___ next year.", ["will be opened", "will open by", "is opening by", "opens by"], 0)
_a("B1+", 9, "My uncle, ___ lives in Canada, is visiting us.", ["who", "that", "which", "whom he"], 0)
_a("B1+", 9, "The report ___ at the moment.", ["is being written", "is writing", "is written", "writes"], 0)
_a("B1+", 9, "The car, ___ was very old, broke down.", ["which", "that", "what", "whose"], 0)
_a("B1+", 9, "He ___ to the hospital after the accident.", ["was taken", "took", "has taken", "taken"], 0)
_a("B1+", 10, "If I ___ harder, I would have passed.", ["had studied", "studied", "have studied", "would study"], 0)
_a("B1+", 10, "If I were you, I ___ that job.", ["'d take", "'ll take", "take", "took"], 0)
_a("B1+", 10, "She ___ the flight if she had left earlier.", ["wouldn't have missed", "wouldn't miss", "didn't miss", "hadn't missed"], 0)
_a("B1+", 10, "If we ___ a car, we could drive there.", ["had", "have", "would have", "will have"], 0)
_a("B1+", 10, "I wish I ___ speak Chinese.", ["could", "can", "will", "would can"], 0)
_a("B1+", 11, "He asked me ___ I liked football.", ["if", "that", "what", "do"], 0)
_a("B1+", 11, "She wanted to know what time the shop ___.", ["closed", "does close", "closes it", "did it close"], 0)
_a("B1+", 11, "I was ___ by the news.", ["shocked", "shocking", "shock", "shockingly"], 0)
_a("B1+", 11, "The journey was really ___.", ["tiring", "tired", "tire", "tiredness"], 0)
_a("B1+", 11, "They asked us where we ___.", ["had been", "have been", "were been", "are"], 0)
_a("B1+", 12, "I wish I ___ so much money last night.", ["hadn't spent", "didn't spend", "haven't spent", "wouldn't spend"], 0)
_a("B1+", 12, "___ life in the city is very fast.", ["—", "The", "A", "An"], 0)
_a("B1+", 12, "He plays ___ guitar in a band.", ["the", "a", "—", "an"], 0)
_a("B1+", 12, "If only I ___ taller.", ["were", "am", "would be", "will be"], 0)
_a("B1+", 12, "She is ___ honest person.", ["an", "a", "the", "—"], 0)

# ------------------------------------------------------------- B2 ----
_a("B2", 1, "Nobody ___ what to do, did they?", ["knew", "knows", "known", "has known"], 0)
_a("B2", 1, "___ did you learn to play so well?", ["How", "What", "Which", "Where"], 0)
_a("B2", 1, "It's the first time I ___ this dish.", ["'ve tried", "try", "tried", "'m trying"], 0)
_a("B2", 1, "___ do you know who lives in Berlin?", ["Who", "Whom", "Which", "What"], 0)
_a("B2", 1, "She ___ constantly ___ about the weather.", ["is / complaining", "does / complain", "has / complained", "was / complain"], 0)
_a("B2", 2, "As soon as we ___ the results, we'll let you know.", ["have", "will have", "had", "would have"], 0)
_a("B2", 2, "He ___ for hours before anyone noticed he was missing.", ["had been walking", "walked", "was walking", "has walked"], 0)
_a("B2", 2, "I'll text you once the plane ___.", ["has landed", "will land", "landed", "would land"], 0)
_a("B2", 2, "By the time help arrived, they ___ out of water.", ["had run", "ran", "have run", "were running"], 0)
_a("B2", 2, "We won't leave until everyone ___ ready.", ["is", "will be", "was", "would be"], 0)
_a("B2", 3, "I've ___ a cold. I can't stop sneezing.", ["come down with", "come up with", "put up with", "got over"], 0)
_a("B2", 3, "She ___ the piano since she was five.", ["has been playing", "has played since", "plays", "played"], 0)
_a("B2", 3, "I'll ___ you ___ at the station at six.", ["pick / up", "take / off", "put / up", "get / on"], 0)
_a("B2", 3, "How many books ___ this year?", ["have you read", "have you been reading", "did you read", "do you read"], 0)
_a("B2", 3, "Could you ___ the music? It's too loud.", ["turn down", "turn up", "put off", "take off"], 0)
_a("B2", 4, "When we were kids, we ___ climb that tree every day.", ["would", "used", "were used to", "use to"], 0)
_a("B2", 4, "I ___ like coffee, but now I drink it every day.", ["didn't use to", "wouldn't", "didn't used to", "usedn't"], 0)
_a("B2", 4, "You ___ to be 18 to vote.", ["are required", "are allowed", "are let", "are made"], 0)
_a("B2", 4, "We ___ leave the building during the exam.", ["weren't allowed to", "didn't allow", "weren't let", "couldn't to"], 0)
_a("B2", 4, "My parents ___ me stay out late.", ["let", "allowed", "made to", "permitted"], 0)
_a("B2", 5, "By 2030, scientists ___ a cure, I hope.", ["will have found", "will find", "find", "are finding"], 0)
_a("B2", 5, "This time tomorrow we ___ over the Atlantic.", ["'ll be flying", "fly", "'ll fly", "flew"], 0)
_a("B2", 5, "It's ___ that the price will rise.", ["likely", "probably", "definitely", "surely"], 0)
_a("B2", 5, "There's a good ___ he'll be late.", ["chance", "likely", "sure", "possible"], 0)
_a("B2", 5, "She ___ to be promoted next year.", ["is bound", "bounds", "is likely that", "must"], 0)
_a("B2", 6, "I regret ___ him the truth.", ["not telling", "not to tell", "to not tell", "don't tell"], 0)
_a("B2", 6, "Remember ___ the lights when you leave.", ["to switch off", "switching off", "switch off", "to switching off"], 0)
_a("B2", 6, "The suspect is thought ___ abroad.", ["to have fled", "that fled", "fleeing", "to flee has"], 0)
_a("B2", 6, "It's no use ___ about it now.", ["worrying", "to worry", "worry", "worried"], 0)
_a("B2", 6, "The package should ___ by Friday.", ["have been delivered", "deliver", "be delivering", "have delivered"], 0)
_a("B2", 7, "There aren't ___ parks in this city.", ["nearly enough", "too enough", "enough of", "so many enough"], 0)
_a("B2", 7, "We ___ our roof repaired after the storm.", ["had", "made", "got to", "did"], 0)
_a("B2", 7, "The rent is ___ high for most people.", ["far too", "much enough", "too much", "very too"], 0)
_a("B2", 7, "I need to ___ my eyes tested.", ["get", "make", "do", "let"], 0)
_a("B2", 7, "She ___ her phone stolen on the metro.", ["had", "got to", "made", "was"], 0)
_a("B2", 8, "You ___ told me earlier! I could have helped.", ["should have", "must have", "would have", "ought have"], 0)
_a("B2", 8, "If I hadn't missed the bus, I ___ late.", ["wouldn't have been", "wouldn't be", "wasn't", "hadn't been"], 0)
_a("B2", 8, "I ___ so much. I feel sick now.", ["shouldn't have eaten", "mustn't have eaten", "couldn't eat", "shouldn't eat"], 0)
_a("B2", 8, "If you ___ me, I'd have come.", ["had called", "called", "would call", "have called"], 0)
_a("B2", 8, "___ I known, I would have waited.", ["Had", "If", "Would", "Should"], 0)
_a("B2", 9, "The hotel ___ we stayed was fantastic.", ["where", "which", "that", "what"], 0)
_a("B2", 9, "He denied ___ the money.", ["taking", "to take", "that take", "take"], 0)
_a("B2", 9, "She apologised ___ late.", ["for being", "to be", "being", "for be"], 0)
_a("B2", 9, "The people ___ I work are very friendly.", ["with whom", "who with", "which", "whose"], 0)
_a("B2", 9, "He accused me ___ lying.", ["of", "for", "about", "to"], 0)
_a("B2", 10, "She's not answering. She ___ her phone at home.", ["must have left", "must leave", "should leave", "can't have left"], 0)
_a("B2", 10, "He ___ the meeting — he was on holiday.", ["can't have attended", "mustn't have attended", "shouldn't attend", "wouldn't attend"], 0)
_a("B2", 10, "I wish I ___ so rude to her yesterday.", ["hadn't been", "wasn't", "weren't", "haven't been"], 0)
_a("B2", 10, "If only it ___ stop raining!", ["would", "will", "had", "does"], 0)
_a("B2", 10, "They ___ got lost; they don't know the area.", ["might have", "must to have", "should have", "can have"], 0)
_a("B2", 11, "It ___ that the company is in trouble.", ["is believed", "believes", "is believing", "believed"], 0)
_a("B2", 11, "He ___ to be the richest man in the country.", ["is said", "says", "is saying", "said"], 0)
_a("B2", 11, "___ unemployment is rising in many countries.", ["—", "The", "An", "A"], 0)
_a("B2", 11, "She works as ___ engineer at ___ company in Madrid.", ["an / a", "a / an", "the / the", "— / a"], 0)
_a("B2", 11, "The painting is reported ___ stolen last night.", ["to have been", "to be", "that it was", "being"], 0)
_a("B2", 12, "___ by the news, she burst into tears.", ["Shocked", "Shocking", "Having shock", "To shock"], 0)
_a("B2", 12, "It was John ___ broke the window, not me.", ["who", "which", "whom", "what"], 0)
_a("B2", 12, "___ finished the report, he went home.", ["Having", "Being", "Had", "To have"], 0)
_a("B2", 12, "What I need ___ a holiday.", ["is", "are", "it is", "be"], 0)
_a("B2", 12, "I ___ like your new haircut!", ["do", "am", "very", "so"], 0)

# ------------------------------------------------------------- C1 ----
_a("C1", 1, "She ___ speaks about her past.", ["rarely", "rare", "rarity", "rarest"], 0)
_a("C1", 1, "I ___ been meaning to call you for weeks.", ["'ve", "'m", "had", "was"], 0)
_a("C1", 1, "He ___ works late, which annoys his wife.", ["frequently", "frequent", "frequency", "most frequent"], 0)
_a("C1", 1, "You're ___ making the same mistake.", ["forever", "ever", "always be", "forever be"], 0)
_a("C1", 1, "___ speaking, the project has been a success.", ["Broadly", "Broad", "Broadness", "Broaden"], 0)
_a("C1", 2, "I ___ just about to leave when the phone rang.", ["was", "am", "had", "have been"], 0)
_a("C1", 2, "By next June, we ___ here for a decade.", ["will have been living", "will live", "are living", "live"], 0)
_a("C1", 2, "The train ___ to depart at 9.15 but it was delayed.", ["was due", "is due", "dues", "had due"], 0)
_a("C1", 2, "The plane ___ leave, so hurry up!", ["is about to", "is due", "about to", "will about"], 0)
_a("C1", 2, "They ___ been arguing for an hour when I walked in.", ["had", "have", "were", "are"], 0)
_a("C1", 3, "___ had I sat down than the doorbell rang.", ["No sooner", "Hardly", "Scarcely", "Not until"], 0)
_a("C1", 3, "___ did she realise how dangerous it was.", ["Only later", "Later only", "Only she later", "Later did"], 0)
_a("C1", 3, "We were told the ferry ___ at noon.", ["would be leaving", "will leave", "leaves", "is leaving"], 0)
_a("C1", 3, "Not only ___ the exam, but she got the top mark.", ["did she pass", "she passed", "she did pass", "passed she"], 0)
_a("C1", 3, "Under no circumstances ___ leave the building.", ["should you", "you should", "you shouldn't", "should not you"], 0)
_a("C1", 4, "The ___ of the situation surprised everyone.", ["complexity", "complex", "complexly", "complicate"], 0)
_a("C1", 4, "We ___ our house broken into last night.", ["had", "got to", "were", "made"], 0)
_a("C1", 4, "There has been a ___ in demand for electric cars.", ["surge", "surging", "surged", "surgeon"], 0)
_a("C1", 4, "I ___ my passport renewed last week.", ["got", "made", "did", "was"], 0)
_a("C1", 4, "The ___ growth of the city has caused problems.", ["rapid", "rapidly", "rapidity", "rapids"], 0)
_a("C1", 5, "The extent ___ he was involved is unclear.", ["to which", "which", "that", "of whom"], 0)
_a("C1", 5, "Employees ___ to follow the safety rules.", ["are obliged", "oblige", "are willing", "obliging"], 0)
_a("C1", 5, "She refused ___ to their demands.", ["to give in", "giving in", "give in", "that give in"], 0)
_a("C1", 5, "The people, ___ of whom were elderly, waited patiently.", ["most", "the most", "mostly", "almost"], 0)
_a("C1", 5, "I'm ___ prepared to help, but not today.", ["perfectly", "perfect", "perfection", "perfectly to"], 0)
_a("C1", 6, "I ___ you're right, but I'm not sure.", ["suppose", "am supposing", "supposed", "have supposing"], 0)
_a("C1", 6, "___ from a distance, the building looks small.", ["Seen", "Seeing", "To see", "Saw"], 0)
_a("C1", 6, "The house ___ to Mr Jones.", ["belongs", "is belonging", "belong", "has belonging"], 0)
_a("C1", 6, "___ no one at home, I left a note.", ["There being", "There was", "Being there", "As being"], 0)
_a("C1", 6, "He ___ always ___ his keys.", ["is / losing", "does / lose", "has / lose", "was / lose"], 0)
_a("C1", 7, "It ___ have been Tom you saw; he's abroad.", ["can't", "mustn't", "shouldn't", "needn't"], 0)
_a("C1", 7, "___ I don't understand is why she left.", ["What", "That", "Which", "Why"], 0)
_a("C1", 7, "It was only after the storm ___ we saw the damage.", ["that", "when", "which", "so"], 0)
_a("C1", 7, "She ___ well have forgotten about it.", ["may", "can", "will", "shall"], 0)
_a("C1", 7, "The reason ___ he resigned was never explained.", ["why", "which", "for", "what"], 0)
_a("C1", 8, "I'd rather you ___ smoke in here.", ["didn't", "don't", "wouldn't", "not"], 0)
_a("C1", 8, "Were it not for your help, I ___ failed.", ["would have", "will have", "had", "have"], 0)
_a("C1", 8, "She can't help ___ at his jokes.", ["laughing", "to laugh", "laugh", "but laughing"], 0)
_a("C1", 8, "___ you need anything, just ask.", ["Should", "If should", "Would", "Had"], 0)
_a("C1", 8, "It's high time we ___.", ["left", "leave", "have left", "will leave"], 0)
_a("C1", 9, "The manager ___ signed the letter.", ["herself", "her own", "by herself", "herselves"], 0)
_a("C1", 9, "They looked at ___ in silence.", ["each other", "themselves", "each", "one other"], 0)
_a("C1", 9, "A: Are you coming? B: I ___ if I can.", ["will", "come", "do", "'m"], 0)
_a("C1", 9, "I didn't like the film, but my sister ___.", ["did", "liked", "was", "does"], 0)
_a("C1", 9, "Help ___ to some cake.", ["yourself", "you", "yourselves you", "your own"], 0)
_a("C1", 10, "You ___ have told me — now it's too late.", ["might", "can", "may", "would"], 0)
_a("C1", 10, "I regret ___ the opportunity.", ["not having taken", "not to take", "to not have taken", "not take"], 0)
_a("C1", 10, "The suspect ___ questioned for hours.", ["must have been", "must be being", "should being", "has to been"], 0)
_a("C1", 10, "It ___ have been done differently.", ["could", "could to", "was could", "can to"], 0)
_a("C1", 10, "If only I ___ listened to your advice.", ["had", "have", "would", "did"], 0)
_a("C1", 11, "She ___ that she had never seen the man.", ["insisted", "insisted me", "said me", "told"], 0)
_a("C1", 11, "If I ___ more careful, I wouldn't be in hospital now.", ["had been", "was", "were", "have been"], 0)
_a("C1", 11, "He asked whether I ___ the report by Friday.", ["would have finished", "will finish", "finish", "am finishing"], 0)
_a("C1", 11, "If she weren't so stubborn, she ___ the job last year.", ["would have got", "would get", "got", "will get"], 0)
_a("C1", 11, "They ___ us to stay for dinner.", ["urged", "said", "insisted", "suggested"], 0)
_a("C1", 12, "___ is the beauty of the place that visitors return every year.", ["Such", "So", "Very", "Much"], 0)
_a("C1", 12, "Little ___ that his life was about to change.", ["did he know", "he knew", "knew he", "he did know"], 0)
_a("C1", 12, "___ Himalayas are the highest mountains on Earth.", ["The", "—", "A", "An"], 0)
_a("C1", 12, "It was ___ because of the rain that we stayed in.", ["precisely", "precise", "precision", "precisely that"], 0)
_a("C1", 12, "Rarely ___ such a talented musician.", ["have I heard", "I have heard", "I heard", "heard I"], 0)

PT_BANK = [{"id": i + 1, "level": lv, "unit": u, "q": t, "opts": o, "a": a}
           for i, (lv, u, t, o, a) in enumerate(Q)]

# 2026-10-22 — 5 ta variant (taxminan bosishga qarshi). Yuqoridagi 4 ta
# variant asl manba; placement_options_v2.json bor bo'lsa, har savolning
# variantlari va to'g'ri indeksi shu fayldan olinadi ("grammar", kalit —
# str(id)). To'g'ri javob matni o'zgarmagan, faqat 88 bitta bo'shliqqa
# moslangan. PLACEMENT_V2_OFF=1 — asl 4 variant (merge_v2.py shuni o'qiydi).
import json as _json  # noqa: E402
import os as _os  # noqa: E402
_V2 = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                    "placement_options_v2.json")
if _os.path.exists(_V2) and not _os.environ.get("PLACEMENT_V2_OFF"):
    with open(_V2, encoding="utf-8") as _f:
        _ov = _json.load(_f).get("grammar") or {}
    for _q in PT_BANK:
        _o = _ov.get(str(_q["id"]))
        if _o:
            _q["opts"], _q["a"] = list(_o["opts"]), int(_o["a"])
