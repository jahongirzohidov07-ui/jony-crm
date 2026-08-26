"""READING MASHQLARI BAZASI (2026-08-10).

Qisqa matn + 4 ta tushunish savoli. Darajalar: A1 (juda sodda),
A2 (o'tgan zamon, kundalik voqealar), B1 (fikr va sabab-oqibat).
Mavzular ataylab o'quvchiga tanish muhitdan - maktab, oila,
sport, O'zbekiston."""

# (title, level, body, [(prompt, [4 variant], javob, izoh), ...])
SEED = [
("My Family", "A1",
 "My name is Aziz. I am eleven years old. I live in Bekobod with my "
 "family. My father is a doctor and my mother is a teacher. I have "
 "one sister. Her name is Lola. She is seven. We have a small cat. "
 "Its name is Simba. I love my family very much.",
 [("How old is Aziz?", ["Eleven", "Seven", "Ten", "Twelve"],
   "Eleven", "\"I am eleven years old.\""),
  ("What is his father's job?", ["A doctor", "A teacher", "A driver",
    "A cook"], "A doctor", "\"My father is a doctor.\""),
  ("Who is Lola?", ["His sister", "His mother", "His cat",
    "His friend"], "His sister", "\"I have one sister... Lola.\""),
  ("What pet do they have?", ["A cat", "A dog", "A bird", "A fish"],
   "A cat", "\"We have a small cat.\"")]),
("My School Day", "A1",
 "I get up at seven o'clock. I wash my face and have breakfast. "
 "I go to school at eight. I have five lessons every day. My "
 "favourite lesson is English. After school I do my homework and "
 "play football with my friends. I go to bed at ten o'clock.",
 [("When does he get up?", ["At seven", "At eight", "At ten",
    "At six"], "At seven", "\"I get up at seven o'clock.\""),
  ("How many lessons does he have?", ["Five", "Four", "Six",
    "Seven"], "Five", "\"I have five lessons every day.\""),
  ("What is his favourite lesson?", ["English", "Maths", "Sport",
    "History"], "English", "\"My favourite lesson is English.\""),
  ("What does he do after school?", ["Homework and football",
    "Watches TV", "Sleeps", "Goes to the shop"],
   "Homework and football",
   "\"After school I do my homework and play football.\"")]),
("At the Market", "A1",
 "On Sunday my mother and I go to the market. The market is big "
 "and noisy. We buy apples, bread and rice. The apples are red and "
 "sweet. Bread is fresh and warm. My mother gives money to the "
 "seller. Then we drink tea in a small cafe near the market.",
 [("When do they go to the market?", ["On Sunday", "On Monday",
    "Every day", "On Friday"], "On Sunday",
   "\"On Sunday my mother and I go to the market.\""),
  ("What do they buy?", ["Apples, bread and rice", "Meat and fish",
    "Milk and eggs", "Sweets"], "Apples, bread and rice",
   "\"We buy apples, bread and rice.\""),
  ("What are the apples like?", ["Red and sweet", "Green and sour",
    "Small and old", "Yellow"], "Red and sweet",
   "\"The apples are red and sweet.\""),
  ("What do they do after shopping?", ["Drink tea", "Go home",
    "Buy clothes", "Play games"], "Drink tea",
   "\"we drink tea in a small cafe.\"")]),
("My Best Friend", "A1",
 "My best friend is Timur. He is in my class. Timur is tall and "
 "strong. He likes sport. Every day he runs in the park. Timur "
 "helps me with maths because he is very clever. I help him with "
 "English. We often play chess after lessons. Timur usually wins.",
 [("Who is Timur?", ["His best friend", "His brother",
    "His teacher", "His cousin"], "His best friend",
   "\"My best friend is Timur.\""),
  ("What does Timur do every day?", ["Runs in the park",
    "Plays computer games", "Swims", "Reads books"],
   "Runs in the park", "\"Every day he runs in the park.\""),
  ("Why does Timur help with maths?", ["He is clever",
    "He is tall", "He is fast", "He is funny"], "He is clever",
   "\"because he is very clever.\""),
  ("Who usually wins at chess?", ["Timur", "The author",
    "Nobody", "The teacher"], "Timur", "\"Timur usually wins.\"")]),
("A Trip to Samarkand", "A2",
 "Last month our class went to Samarkand by train. The trip took "
 "two hours. First we visited Registan Square. Our teacher told us "
 "about its history. The old buildings were beautiful and very "
 "tall. Then we ate plov in a national restaurant. In the evening "
 "we bought presents for our families. Everybody was tired but "
 "happy.",
 [("How did they travel?", ["By train", "By bus", "By car",
    "By plane"], "By train", "\"went to Samarkand by train.\""),
  ("How long was the trip?", ["Two hours", "Three hours",
    "One hour", "Five hours"], "Two hours",
   "\"The trip took two hours.\""),
  ("What did they do first?", ["Visited Registan Square",
    "Ate plov", "Bought presents", "Went to a museum"],
   "Visited Registan Square", "\"First we visited Registan Square.\""),
  ("How did everybody feel?", ["Tired but happy", "Sad", "Angry",
    "Bored"], "Tired but happy",
   "\"Everybody was tired but happy.\"")]),
("The Lost Phone", "A2",
 "Yesterday Madina lost her phone at school. She looked for it "
 "everywhere: in her bag, in the classroom and in the sports hall. "
 "She was very sad because it was a present from her father. After "
 "the last lesson, a small boy from the first grade came to her. "
 "He found the phone near the library and gave it back. Madina "
 "thanked him and bought him an ice cream.",
 [("What did Madina lose?", ["Her phone", "Her bag", "Her book",
    "Her keys"], "Her phone", "\"Madina lost her phone.\""),
  ("Why was she sad?", ["It was a present from her father",
    "It was new", "It was expensive", "It had her photos"],
   "It was a present from her father",
   "\"it was a present from her father.\""),
  ("Where was the phone?", ["Near the library",
    "In the sports hall", "In her bag", "In the classroom"],
   "Near the library", "\"He found the phone near the library.\""),
  ("How did Madina thank the boy?", ["She bought him an ice cream",
    "She gave him money", "She said nothing",
    "She helped his homework"], "She bought him an ice cream",
   "\"bought him an ice cream.\"")]),
("Aziza's New Hobby", "A2",
 "Two months ago Aziza started drawing. At first her pictures were "
 "not very good, but she practised every evening. She watched "
 "video lessons and drew animals, trees and houses. Last week her "
 "picture won a school competition. Now Aziza wants to become a "
 "designer. Her parents are proud of her and bought her new "
 "colour pencils.",
 [("When did Aziza start drawing?", ["Two months ago",
    "Last week", "Yesterday", "Two years ago"], "Two months ago",
   "\"Two months ago Aziza started drawing.\""),
  ("How did she get better?", ["She practised every evening",
    "She paid a teacher", "She was born talented",
    "Her friend drew for her"], "She practised every evening",
   "\"she practised every evening.\""),
  ("What happened last week?", ["Her picture won a competition",
    "She stopped drawing", "She sold a picture",
    "She broke her pencils"], "Her picture won a competition",
   "\"her picture won a school competition.\""),
  ("What does Aziza want to become?", ["A designer", "A doctor",
    "A teacher", "A singer"], "A designer",
   "\"Aziza wants to become a designer.\"")]),
("Rain in the Mountains", "A2",
 "Last summer Jasur and his father went camping in the mountains. "
 "On the second day the weather changed and it started to rain "
 "heavily. They quickly put their things into the tent. Jasur's "
 "father made hot tea. They sat in the tent, drank tea and told "
 "funny stories. In the morning the sun came out again. Jasur "
 "says it was the best day of the trip.",
 [("Who went camping?", ["Jasur and his father",
    "Jasur and his class", "Jasur alone", "Two friends"],
   "Jasur and his father", "\"Jasur and his father went camping.\""),
  ("What happened on the second day?", ["It started to rain",
    "It snowed", "It was very hot", "They went home"],
   "It started to rain", "\"it started to rain heavily.\""),
  ("What did they do in the tent?", ["Drank tea and told stories",
    "Slept all day", "Played chess", "Watched films"],
   "Drank tea and told stories",
   "\"drank tea and told funny stories.\""),
  ("What does Jasur think about that day?", ["It was the best day",
    "It was terrible", "It was boring", "It was dangerous"],
   "It was the best day", "\"it was the best day of the trip.\"")]),
("Why Sleep Matters", "B1",
 "Many teenagers think sleep is a waste of time, but scientists "
 "disagree. During sleep the brain sorts the information you "
 "learned during the day and moves important facts into long-term "
 "memory. Students who sleep less than seven hours usually get "
 "lower marks, even if they study a lot. Doctors advise teenagers "
 "to sleep eight or nine hours and to put their phones away an "
 "hour before bed, because the bright screen makes falling asleep "
 "difficult.",
 [("What does the brain do during sleep?",
   ["Moves facts into long-term memory", "Rests completely",
    "Forgets everything", "Grows bigger"],
   "Moves facts into long-term memory",
   "\"moves important facts into long-term memory.\""),
  ("What happens to students who sleep little?",
   ["They get lower marks", "They get higher marks",
    "Nothing changes", "They become taller"],
   "They get lower marks",
   "\"usually get lower marks, even if they study a lot.\""),
  ("How long should teenagers sleep?", ["Eight or nine hours",
    "Five hours", "Six hours", "Twelve hours"],
   "Eight or nine hours", "\"to sleep eight or nine hours.\""),
  ("Why should phones be put away before bed?",
   ["The screen makes falling asleep difficult",
    "Phones are expensive", "Parents say so",
    "To save the battery"],
   "The screen makes falling asleep difficult",
   "\"the bright screen makes falling asleep difficult.\"")]),
("The Power of Small Steps", "B1",
 "People often fail because they want big results immediately. "
 "They start learning a language and expect to speak fluently in "
 "a month. When it does not happen, they give up. Successful "
 "learners work differently: they study a little every day. "
 "Fifteen minutes of daily practice gives better results than "
 "three hours once a week, because the brain remembers things "
 "that it meets often. So if you want to learn English, open your "
 "app every day - even for ten minutes.",
 [("Why do people often fail?",
   ["They want big results immediately", "They study too much",
    "They have bad teachers", "They are lazy"],
   "They want big results immediately",
   "\"they want big results immediately.\""),
  ("How do successful learners work?", ["A little every day",
    "Three hours once a week", "Only at school",
    "Without any plan"], "A little every day",
   "\"they study a little every day.\""),
  ("Why is daily practice better?",
   ["The brain remembers what it meets often",
    "It is easier", "It is cheaper", "Teachers like it"],
   "The brain remembers what it meets often",
   "\"the brain remembers things that it meets often.\""),
  ("What is the author's advice?", ["Open your app every day",
    "Study once a week", "Find a tutor", "Move abroad"],
   "Open your app every day",
   "\"open your app every day - even for ten minutes.\"")]),
("A City Without Cars", "B1",
 "Imagine a city centre where there are no cars at all. In some "
 "European cities this is already real: streets are only for "
 "people, bicycles and small electric buses. The air became "
 "cleaner, and shops earn more money because walking people stop "
 "and look at windows more often than drivers. Of course, not "
 "everybody is happy - some people say it is hard to carry heavy "
 "bags without a car. Still, more and more cities want to try "
 "this idea.",
 [("What is special about these city centres?",
   ["There are no cars", "There are no people",
    "There are no shops", "There are no buses"],
   "There are no cars", "\"where there are no cars at all.\""),
  ("What happened to the air?", ["It became cleaner",
    "It became dirtier", "Nothing changed", "It became warmer"],
   "It became cleaner", "\"The air became cleaner.\""),
  ("Why do shops earn more?",
   ["Walking people look at windows more often",
    "Prices are higher", "Cars bring customers",
    "They work at night"],
   "Walking people look at windows more often",
   "\"walking people stop and look at windows more often.\""),
  ("Why are some people unhappy?",
   ["It is hard to carry heavy bags", "Buses are slow",
    "Bicycles are expensive", "Streets are noisy"],
   "It is hard to carry heavy bags",
   "\"it is hard to carry heavy bags without a car.\"")]),
("The Interview", "B1",
 "When Kamola came to her first job interview, she was very "
 "nervous. The manager asked her about her experience, and she "
 "honestly said she had none, but she showed the projects she had "
 "made at home and explained how she had learned everything "
 "herself. The manager smiled: many people with diplomas could "
 "not answer simple questions, but Kamola showed real skills and "
 "real interest. She got the job. Sometimes what you can do "
 "matters more than what papers you have.",
 [("How did Kamola feel at first?", ["Nervous", "Confident",
    "Angry", "Bored"], "Nervous", "\"she was very nervous.\""),
  ("What did she show the manager?", ["Projects made at home",
    "Her diploma", "A letter", "Her photos"],
   "Projects made at home",
   "\"she showed the projects she had made at home.\""),
  ("Why did the manager smile?",
   ["Kamola showed real skills and interest",
    "The interview was funny", "He knew her father",
    "It was his birthday"],
   "Kamola showed real skills and interest",
   "\"Kamola showed real skills and real interest.\""),
  ("What is the main idea of the text?",
   ["Skills can matter more than papers",
    "Diplomas are useless", "Interviews are easy",
    "Experience is everything"],
   "Skills can matter more than papers",
   "\"what you can do matters more than what papers you have.\"")]),
]




# =====================================================================
#  2-TO'LQIN (2026-08-24). Jahongir: "reading listening qismini a1 dan
#  boshlab c2 darajagacha yani beginnerdan boshlab native darajagacha
#  bo'lim chiqib mashqlarni ham kopaytir".
#  Yangi: A1/A2/B1 ga qo'shimcha matnlar + B2/C1/C2 birinchi marta.
# =====================================================================
SEED2 = [
("My Pet Rabbit", "A1",
 "I have a rabbit. His name is Bunny. He is white and very soft. "
 "Bunny lives in a small house in our garden. He eats carrots and "
 "green leaves. Every morning I give him water. Bunny likes to jump. "
 "My little brother laughs when Bunny jumps.",
 [("What colour is Bunny?", ["White", "Black", "Brown", "Grey"],
   "White", "\"He is white and very soft.\""),
  ("Where does Bunny live?", ["In the garden", "In the kitchen",
    "At school", "In a shop"], "In the garden",
   "\"Bunny lives in a small house in our garden.\""),
  ("What does Bunny eat?", ["Carrots and leaves", "Meat", "Bread",
    "Fish"], "Carrots and leaves",
   "\"He eats carrots and green leaves.\""),
  ("Who laughs when Bunny jumps?", ["His little brother",
    "His mother", "His teacher", "Nobody"], "His little brother",
   "\"My little brother laughs.\"")]),
("Rainy Day", "A1",
 "Today it is raining. I cannot play football outside. I stay at "
 "home with my sister. We draw pictures and watch cartoons. Mother "
 "makes hot tea and gives us cookies. I like rainy days at home, "
 "but I want to see the sun tomorrow.",
 [("What is the weather like?", ["Rainy", "Sunny", "Snowy",
    "Windy"], "Rainy", "\"Today it is raining.\""),
  ("Why can't he play football?", ["Because of the rain",
    "He is ill", "He has homework", "It is night"],
   "Because of the rain", "Yomg'ir yog'ayotgani uchun."),
  ("What does mother make?", ["Hot tea", "Soup", "Cake", "Coffee"],
   "Hot tea", "\"Mother makes hot tea.\""),
  ("What does he want tomorrow?", ["To see the sun", "More rain",
    "To sleep", "New toys"], "To see the sun",
   "\"I want to see the sun tomorrow.\"")]),
("A Trip to Bukhara", "A2",
 "Last spring our class went to Bukhara by bus. The trip took six "
 "hours, but nobody was bored because we sang songs and played "
 "games. In Bukhara we saw the old fortress and many beautiful "
 "mosques. Our guide told us stories about ancient traders. I "
 "bought a small souvenir for my grandmother. It was the best "
 "school trip of the year.",
 [("How did the class travel?", ["By bus", "By train", "By plane",
    "By car"], "By bus", "\"went to Bukhara by bus\""),
  ("How long was the trip?", ["Six hours", "Two hours",
    "One day", "Three hours"], "Six hours",
   "\"The trip took six hours.\""),
  ("Who told stories about traders?", ["The guide", "The driver",
    "The teacher", "A student"], "The guide",
   "\"Our guide told us stories.\""),
  ("What did he buy?", ["A souvenir", "A book", "Sweets",
    "A ticket"], "A souvenir",
   "\"I bought a small souvenir.\"")]),
("The New Sports Hall", "A2",
 "Our school built a new sports hall last year. Before that, we "
 "did exercises outside, even in cold weather. Now we play "
 "volleyball and basketball inside. The hall is open until seven "
 "in the evening, so many students stay after lessons. My friends "
 "and I go there every Tuesday and Friday. Our team is preparing "
 "for the city championship in May.",
 [("When was the hall built?", ["Last year", "Two years ago",
    "This month", "In May"], "Last year",
   "\"built a new sports hall last year\""),
  ("Where did they exercise before?", ["Outside", "In the hall",
    "At home", "In another school"], "Outside",
   "\"we did exercises outside\""),
  ("Until what time is the hall open?", ["Seven in the evening",
    "Five o'clock", "Nine o'clock", "All night"],
   "Seven in the evening", "\"open until seven in the evening\""),
  ("What happens in May?", ["The city championship",
    "The hall closes", "Exams start", "A concert"],
   "The city championship",
   "\"preparing for the city championship in May\"")]),
("Why I Stopped Watching TV", "B1",
 "Two months ago I noticed that I was spending almost four hours a "
 "day in front of the TV. My homework was often late and I felt "
 "tired in the mornings. So I made a rule: no TV before finishing "
 "my tasks, and never more than one hour a day. The first week was "
 "difficult, but then something surprising happened. I started "
 "reading books again, my marks improved, and I even joined a "
 "chess club. Now I watch only programmes I really choose, not "
 "whatever is on.",
 [("How much TV did he watch before?", ["About four hours a day",
    "One hour a day", "Only at weekends", "Two hours a week"],
   "About four hours a day",
   "\"almost four hours a day\""),
  ("What was his new rule?", ["No TV before finishing tasks",
    "No TV at all", "TV only in the morning",
    "TV only with friends"], "No TV before finishing tasks",
   "\"no TV before finishing my tasks\""),
  ("What happened after the change?", ["His marks improved",
    "He felt more tired", "He left school", "He sold the TV"],
   "His marks improved", "\"my marks improved\""),
  ("How does he choose programmes now?", ["He picks them himself",
    "He watches whatever is on", "His parents choose",
    "He doesn't watch at all"], "He picks them himself",
   "\"only programmes I really choose\"")]),
("A Part-Time Job", "B1",
 "My cousin Aziza is a university student. Twice a week she works "
 "as a waitress in a small cafe near her dormitory. At first her "
 "parents were against it - they were afraid the job would harm "
 "her studies. However, Aziza planned her time carefully and her "
 "grades did not fall. She says the job taught her more than money "
 "management: she learned to stay calm with difficult customers "
 "and to work in a team. Next summer the cafe owner wants to make "
 "her a shift manager.",
 [("How often does Aziza work?", ["Twice a week", "Every day",
    "Once a month", "Only in summer"], "Twice a week",
   "\"Twice a week she works as a waitress.\""),
  ("Why were her parents against the job?", [
    "They worried about her studies", "The cafe was far",
    "The salary was low", "They disliked the owner"],
   "They worried about her studies",
   "\"afraid the job would harm her studies\""),
  ("What did the job teach her?", [
    "To stay calm and work in a team", "To cook well",
    "To speak English", "To drive"],
   "To stay calm and work in a team",
   "\"stay calm with difficult customers and to work in a team\""),
  ("What may happen next summer?", ["She may become a shift manager",
    "She may quit", "The cafe may close", "She may move abroad"],
   "She may become a shift manager",
   "\"wants to make her a shift manager\"")]),
("The Price of Convenience", "B2",
 "Food delivery apps have transformed the way city dwellers eat. "
 "With a few taps, a hot meal arrives at the door within half an "
 "hour. Yet this convenience has hidden costs. Restaurants pay "
 "the platforms commissions of up to thirty per cent, which "
 "forces many small, family-run places to raise prices or close "
 "their kitchens to walk-in guests entirely. Couriers, meanwhile, "
 "often work without contracts, racing through traffic to meet "
 "algorithm-set deadlines. Some economists argue that unless "
 "regulation catches up, the apps will quietly reshape urban food "
 "culture: fewer independent cafes, more 'ghost kitchens' that "
 "cook only for delivery, and a generation that rarely eats out.",
 [("What problem do small restaurants face?", [
    "High platform commissions", "A lack of couriers",
    "Too many walk-in guests", "Cheap ingredients"],
   "High platform commissions",
   "\"commissions of up to thirty per cent\""),
  ("What is said about couriers?", [
    "They often work without contracts",
    "They earn thirty per cent", "They set their own deadlines",
    "They own the platforms"],
   "They often work without contracts",
   "\"often work without contracts\""),
  ("What is a 'ghost kitchen'?", [
    "A kitchen that cooks only for delivery",
    "A closed restaurant", "An illegal cafe",
    "A kitchen open at night"],
   "A kitchen that cooks only for delivery",
   "\"cook only for delivery\""),
  ("What do some economists call for?", ["Regulation",
    "Higher prices", "More apps", "Free delivery"],
   "Regulation", "\"unless regulation catches up\"")]),
("Sleep and the Teenage Brain", "B2",
 "Ask any teenager why they stay up past midnight and you will "
 "hear about homework, games or endless group chats. Biology, "
 "however, is also to blame. During adolescence the body releases "
 "melatonin - the hormone that signals sleepiness - about two "
 "hours later than in childhood. In other words, a fifteen-year-"
 "old who cannot fall asleep at ten is not simply being stubborn. "
 "The conflict arises because school still starts early. Studies "
 "in several countries have shown that moving the first lesson "
 "just one hour later improves attendance, mood and even exam "
 "results. Critics answer that later starts complicate parents' "
 "work schedules and school transport. The debate continues, but "
 "the science is clear: teenagers are not lazy - their clocks "
 "are different.",
 [("Why do teenagers fall asleep later?", [
    "Melatonin is released later", "They are lazy",
    "They drink coffee", "Schools give no homework"],
   "Melatonin is released later",
   "\"releases melatonin... about two hours later\""),
  ("What did studies show about later school starts?", [
    "Attendance and results improved", "Students slept less",
    "Parents were happier", "Nothing changed"],
   "Attendance and results improved",
   "\"improves attendance, mood and even exam results\""),
  ("What do critics say?", [
    "Later starts complicate schedules and transport",
    "The science is wrong", "Teenagers need less sleep",
    "Exams should be cancelled"],
   "Later starts complicate schedules and transport",
   "\"complicate parents' work schedules and school transport\""),
  ("What is the author's conclusion?", [
    "Teenagers' body clocks are different", "Teenagers are lazy",
    "School should be cancelled", "Melatonin is harmful"],
   "Teenagers' body clocks are different",
   "\"their clocks are different\"")]),
("The Paradox of Choice", "C1",
 "Conventional wisdom holds that the more options we have, the "
 "better off we are. Psychologist Barry Schwartz famously "
 "challenged this assumption, arguing that beyond a certain point "
 "abundance breeds paralysis rather than freedom. In one study, "
 "shoppers offered twenty-four varieties of jam were far less "
 "likely to buy any than those shown just six. The cost of "
 "endless choice is not merely indecision: having finally chosen, "
 "we are haunted by the alternatives we declined, and our "
 "satisfaction shrinks accordingly. Schwartz distinguishes "
 "'maximisers', who exhaustively seek the best, from "
 "'satisficers', who settle for good enough - and finds the "
 "latter consistently happier. The lesson is not to abolish "
 "choice but to recognise that self-imposed limits can be a form "
 "of liberation.",
 [("What did the jam study demonstrate?", [
    "More options led to fewer purchases",
    "Shoppers preferred variety", "Jam sales rose with choice",
    "Six varieties were too few"],
   "More options led to fewer purchases",
   "24 xil murabbo ko'rganlar deyarli sotib olmagan."),
  ("Why does satisfaction shrink after choosing?", [
    "We keep thinking about rejected alternatives",
    "Products are low quality", "Prices rise",
    "We forget our choice"],
   "We keep thinking about rejected alternatives",
   "\"haunted by the alternatives we declined\""),
  ("Who tends to be happier, according to Schwartz?", [
    "Satisficers", "Maximisers", "Shoppers", "Psychologists"],
   "Satisficers", "\"finds the latter consistently happier\""),
  ("What is the author's final message?", [
    "Limiting choice can be liberating",
    "Choice should be abolished", "Buy the best or nothing",
    "Avoid shopping"], "Limiting choice can be liberating",
   "\"self-imposed limits can be a form of liberation\"")]),
("Rewilding: Nature's Second Chance", "C1",
 "Rewilding - the large-scale restoration of ecosystems to the "
 "point where nature can take care of itself - has moved from the "
 "fringes of conservation to its mainstream. Its advocates point "
 "to the reintroduction of wolves in Yellowstone, which triggered "
 "a cascade of recovery: elk herds dispersed, riverbanks "
 "revegetated, and beavers returned. Sceptics, however, caution "
 "against romanticism. Landscapes emptied of predators for "
 "centuries are now home to farms and villages; releasing large "
 "carnivores into them raises legitimate questions about "
 "livestock, livelihoods and liability. The most promising "
 "projects therefore proceed incrementally, pairing ecological "
 "ambition with compensation schemes and genuine local consent. "
 "Rewilding, at its best, is less about turning back the clock "
 "than about giving natural processes room to write the future.",
 [("What happened after wolves returned to Yellowstone?", [
    "Ecosystem recovery followed", "Elk disappeared entirely",
    "Beavers left", "Farms expanded"],
   "Ecosystem recovery followed",
   "\"triggered a cascade of recovery\""),
  ("What do sceptics worry about?", [
    "Livestock, livelihoods and liability",
    "Too many beavers", "Tourism decline", "River flooding"],
   "Livestock, livelihoods and liability",
   "Aynan shu uchlik matnda sanab o'tilgan."),
  ("How do the best projects proceed?", [
    "Gradually, with local consent", "As fast as possible",
    "In secret", "Only in national parks"],
   "Gradually, with local consent",
   "\"incrementally... genuine local consent\""),
  ("What is rewilding 'at its best'?", [
    "Letting natural processes shape the future",
    "Recreating the past exactly", "Removing all people",
    "A tourism strategy"],
   "Letting natural processes shape the future",
   "\"giving natural processes room to write the future\"")]),
("The Cartographer's Dilemma", "C2",
 "Every map is a small act of tyranny. To render a spherical, "
 "seething world legible on a flat rectangle, the cartographer "
 "must decide what merits inclusion and what may be consigned to "
 "oblivion - and each omission quietly legislates reality for the "
 "map's readers. The Mercator projection, contrived for "
 "sixteenth-century navigators, notoriously inflates the poles "
 "until Greenland rivals Africa, a continent fourteen times its "
 "size; generations have thus absorbed a geopolitics of distortion "
 "without ever suspecting it. Nor is the digital age exempt: when "
 "a navigation app shades one district grey and renders another "
 "in inviting detail, it is not describing the city so much as "
 "prescribing our passage through it. The honest cartographer, "
 "then, does not promise objectivity. She discloses her choices, "
 "names her projection, and trusts the reader to remember that "
 "the territory always exceeds the map.",
 [("Why is every map 'an act of tyranny'?", [
    "It imposes choices about what exists for readers",
    "It is drawn by governments", "It is expensive",
    "It shows too much detail"],
   "It imposes choices about what exists for readers",
   "\"each omission quietly legislates reality\""),
  ("What is wrong with the Mercator projection?", [
    "It grossly inflates polar regions",
    "It omits the oceans", "It is upside down",
    "It shows Africa too large"],
   "It grossly inflates polar regions",
   "\"inflates the poles until Greenland rivals Africa\""),
  ("How do navigation apps 'prescribe' movement?", [
    "By rendering areas selectively", "By charging fees",
    "By closing roads", "By tracking users"],
   "By rendering areas selectively",
   "\"shades one district grey... inviting detail\""),
  ("What should an honest cartographer do?", [
    "Disclose choices and name the projection",
    "Promise objectivity", "Avoid making maps",
    "Use only satellites"],
   "Disclose choices and name the projection",
   "\"discloses her choices, names her projection\"")]),
("On the Uses of Boredom", "C2",
 "Boredom has acquired the status of a modern pathology, to be "
 "anaesthetised at the first twinge by the nearest glowing "
 "screen. Yet a growing body of research suggests that this "
 "restless vacancy is not a malfunction of the mind but one of "
 "its indispensable moods. In the idling brain, the so-called "
 "default mode network stitches memory to imagination, rehearsing "
 "futures and auditing the past; it is precisely in these "
 "unclaimed moments that insight tends to ambush us. The "
 "implication is uncomfortable: by reflexively evicting boredom, "
 "we may be foreclosing the very conditions of originality. None "
 "of this romanticises tedium for its own sake - an assembly line "
 "is not a salon. But it does suggest that the capacity to sit "
 "with one's own unfurnished thoughts, once a universal human "
 "competence, is becoming a deliberate discipline, and perhaps a "
 "competitive advantage.",
 [("How is boredom commonly treated today?", [
    "As an illness to be instantly relieved",
    "As a luxury", "As a discipline", "As a skill"],
   "As an illness to be instantly relieved",
   "\"anaesthetised at the first twinge\""),
  ("What does the default mode network do?", [
    "Connects memory with imagination",
    "Blocks distractions", "Causes anxiety",
    "Controls movement"],
   "Connects memory with imagination",
   "\"stitches memory to imagination\""),
  ("What may constant stimulation cost us?", [
    "The conditions for originality", "Better focus",
    "More free time", "Stronger memory"],
   "The conditions for originality",
   "\"foreclosing the very conditions of originality\""),
  ("What is the author's attitude to tedium?", [
    "Valuable, but not romanticised for its own sake",
    "Entirely positive", "Entirely negative",
    "Indifferent"],
   "Valuable, but not romanticised for its own sake",
   "\"None of this romanticises tedium... assembly line is "
   "not a salon\"")]),
]


def seed_reading(db):
    """Idempotent: sarlavha bo'yicha faqat yo'q matnlar qo'shiladi.

    Markerlar:
      reading_v2 (2026-08-24) — SEED + SEED2;
      reading_v3 (2026-08-26) — SEED3. Yangi marker SHART, chunki
        reading_v2 allaqachon qo'yilgan bazalarda seed umuman qayta
        ishlamasdi va SEED3 tushmay qolardi.

    Hech narsa o'chirilmaydi: mavjud sarlavhalar chetlab o'tiladi."""
    from common import _seed_done, _seed_mark
    import json
    import models
    made = 0
    for marker, batch in (("reading_v2", SEED + SEED2),
                          ("reading_v3", SEED3)):
        if _seed_done(db, marker):
            continue
        have = {t for (t,) in db.query(models.ReadingText.title).all()}
        for title, level, body, questions in batch:
            if title in have:
                continue
            tx = models.ReadingText(title=title, level=level,
                                    body=body)
            db.add(tx)
            db.flush()
            for prompt, options, answer, explain in questions:
                db.add(models.ReadingQuestion(
                    text_id=tx.id, prompt=prompt,
                    options=json.dumps(options, ensure_ascii=False),
                    answer=answer, explain=explain))
                made += 1
        if made:
            db.commit()
        _seed_mark(db, marker)
    return made


# =====================================================================
#  SEED3 (2026-08-26) — Jahongir: "10ta tanlasa 10ta bo'lsinda, 20ta
#  tanlasa 20ta bo'lsin".
#
#  Sonni tuzatgandan keyin ma'lum bo'ldiki, kontentning o'zi
#  yetmaydi: B2, C1 va C2 darajalarda atigi 2 tadan matn, ya'ni 8
#  tadan savol bor edi. 20 yoki 30 ta so'ralsa ham shuncha chiqardi.
#  Quyida har daraja kamida 10 ta matnga (40 savolga) yetkaziladi.
# =====================================================================
SEED3 = [
# ----------------------------- A1 -----------------------------
("At the Bus Stop", "A1",
 "Every morning Dilnoza waits at the bus stop near her house. The "
 "bus comes at half past seven. It is always yellow. Dilnoza sits "
 "near the window and reads a book. The bus stops at her school at "
 "eight o'clock. Her friend Kamron gets on at the second stop.",
 [("What time does the bus come?", ["Half past seven", "Eight o'clock",
   "Seven o'clock", "Half past eight"], "Half past seven",
   "\"The bus comes at half past seven.\""),
  ("What colour is the bus?", ["Yellow", "Blue", "Green", "White"],
   "Yellow", "\"It is always yellow.\""),
  ("What does Dilnoza do on the bus?", ["She reads a book",
   "She sleeps", "She eats", "She talks"], "She reads a book",
   "\"Dilnoza sits near the window and reads a book.\""),
  ("Where does Kamron get on?", ["At the second stop",
   "At the school", "At the first stop", "Near his house"],
   "At the second stop",
   "\"Her friend Kamron gets on at the second stop.\"")]),
("My Dog Bobo", "A1",
 "I have a dog. His name is Bobo. He is brown and very small. Bobo "
 "is three years old. He likes bread and milk. Every evening we go "
 "to the park. Bobo runs fast. He sleeps under my bed at night.",
 [("What colour is Bobo?", ["Brown", "Black", "White", "Grey"],
   "Brown", "\"He is brown and very small.\""),
  ("How old is Bobo?", ["Three", "Two", "Five", "One"], "Three",
   "\"Bobo is three years old.\""),
  ("What does Bobo like?", ["Bread and milk", "Meat and rice",
   "Fruit", "Fish"], "Bread and milk", "\"He likes bread and milk.\""),
  ("Where does Bobo sleep?", ["Under the bed", "In the park",
   "On the sofa", "In the kitchen"], "Under the bed",
   "\"He sleeps under my bed at night.\"")]),
("The Small Shop", "A1",
 "There is a small shop next to my house. It opens at eight in the "
 "morning and closes at nine in the evening. The shop sells bread, "
 "milk, eggs and fruit. The woman in the shop is called Nigora. She "
 "is very kind. On Sunday the shop is closed.",
 [("When does the shop open?", ["At eight", "At nine", "At seven",
   "At ten"], "At eight",
   "\"It opens at eight in the morning\""),
  ("What does the shop sell?", ["Bread and milk", "Books",
   "Clothes", "Toys"], "Bread and milk",
   "\"The shop sells bread, milk, eggs and fruit.\""),
  ("Who works in the shop?", ["Nigora", "Lola", "Aziz", "Kamron"],
   "Nigora", "\"The woman in the shop is called Nigora.\""),
  ("When is the shop closed?", ["On Sunday", "On Monday",
   "On Saturday", "Every evening"], "On Sunday",
   "\"On Sunday the shop is closed.\"")]),
("A Rainy Day", "A1",
 "Today it is raining. I cannot play football. My brother and I "
 "stay at home. We watch a film about animals. Then my mother makes "
 "hot tea. In the afternoon the rain stops and the sun comes out. "
 "We go outside and ride our bikes.",
 [("Why can the writer not play football?", ["It is raining",
   "He is ill", "It is late", "He has no ball"], "It is raining",
   "\"Today it is raining. I cannot play football.\""),
  ("What is the film about?", ["Animals", "Cars", "Sport",
   "School"], "Animals", "\"We watch a film about animals.\""),
  ("What does the mother make?", ["Hot tea", "Bread", "Soup",
   "Cake"], "Hot tea", "\"Then my mother makes hot tea.\""),
  ("What do they do in the afternoon?", ["They ride bikes",
   "They watch another film", "They sleep", "They go to school"],
   "They ride bikes", "\"We go outside and ride our bikes.\"")]),
# ----------------------------- A2 -----------------------------
("The School Library", "A2",
 "Our school library moved to a bigger room last September. Before "
 "that, it was next to the kitchen and it was always noisy. Now it "
 "is on the second floor and it is much quieter. Students can "
 "borrow three books for two weeks. Last year they could only take "
 "one. The librarian, Mr Tosh, started a reading club that meets "
 "every Thursday after lessons.",
 [("Where was the library before?", ["Next to the kitchen",
   "On the second floor", "In the hall", "Near the office"],
   "Next to the kitchen",
   "\"Before that, it was next to the kitchen\""),
  ("How many books can a student borrow now?", ["Three", "One",
   "Two", "Five"], "Three",
   "\"Students can borrow three books for two weeks.\""),
  ("What changed compared with last year?", ["Students can take "
   "more books", "The library closed", "The librarian left",
   "Books became expensive"], "Students can take more books",
   "\"Last year they could only take one.\""),
  ("When does the reading club meet?", ["Every Thursday",
   "Every Monday", "At weekends", "Before lessons"],
   "Every Thursday",
   "\"a reading club that meets every Thursday after lessons\"")]),
("A Trip to the Mountains", "A2",
 "Last summer my family drove to the mountains. The journey took "
 "four hours because the road was bad in places. We stayed in a "
 "small guest house with only six rooms. In the morning we walked "
 "to a waterfall. It was cold, so nobody swam. My father took a "
 "hundred photographs. On the last day it rained and we came home "
 "early.",
 [("How long did the journey take?", ["Four hours", "Two hours",
   "Six hours", "One day"], "Four hours",
   "\"The journey took four hours\""),
  ("Why did nobody swim?", ["The water was cold", "It was raining",
   "There was no time", "It was dangerous"], "The water was cold",
   "\"It was cold, so nobody swam.\""),
  ("How many rooms did the guest house have?", ["Six", "Four",
   "Ten", "Two"], "Six",
   "\"a small guest house with only six rooms\""),
  ("Why did they come home early?", ["Because of the rain",
   "Because they were tired", "Because of the road",
   "Because the guest house closed"], "Because of the rain",
   "\"On the last day it rained and we came home early.\"")]),
("Learning to Cook", "A2",
 "When Malika went to university she could not cook at all. In her "
 "first week she ate bread and cheese every day. Then her flatmate "
 "showed her how to make soup. It was easier than she expected. "
 "Now she cooks three or four times a week and she says it saves a "
 "lot of money. Her favourite dish is still the soup she learnt "
 "first.",
 [("What did Malika eat in her first week?", ["Bread and cheese",
   "Soup", "Rice", "Nothing"], "Bread and cheese",
   "\"In her first week she ate bread and cheese every day.\""),
  ("Who taught her to cook?", ["Her flatmate", "Her mother",
   "A teacher", "Her brother"], "Her flatmate",
   "\"Then her flatmate showed her how to make soup.\""),
  ("What did she think of cooking soup?", ["Easier than she "
   "expected", "Very difficult", "Boring", "Expensive"],
   "Easier than she expected",
   "\"It was easier than she expected.\""),
  ("Why is cooking useful for her?", ["It saves money",
   "It saves time", "It is a hobby", "Her friends like it"],
   "It saves money", "\"she says it saves a lot of money\"")]),
("The Phone on the Metro", "A2",
 "Botir lost his phone on the metro on Friday evening. He went "
 "back to the station on Saturday morning, but the office was "
 "closed. On Monday he returned and a woman gave him a form to "
 "fill in. Two days later somebody called his home number: a "
 "student had found the phone and taken it to a police station. "
 "Botir gave the student a box of chocolates.",
 [("Where did Botir lose his phone?", ["On the metro",
   "At the police station", "At home", "In the office"],
   "On the metro",
   "\"Botir lost his phone on the metro on Friday evening.\""),
  ("Why could he do nothing on Saturday?", ["The office was closed",
   "He had no time", "He forgot", "The station was shut"],
   "The office was closed",
   "\"the office was closed\""),
  ("Who found the phone?", ["A student", "A police officer",
   "A woman in the office", "A driver"], "A student",
   "\"a student had found the phone\""),
  ("How did Botir thank the finder?", ["He gave chocolates",
   "He gave money", "He wrote a letter", "He said nothing"],
   "He gave chocolates",
   "\"Botir gave the student a box of chocolates.\"")]),
# ----------------------------- B1 -----------------------------
("Why Cities Are Getting Greener", "B1",
 "Twenty years ago, a car park in the centre of Sheffield was one "
 "of the ugliest places in the city. Today the same space is a "
 "small park with 40 trees and a pond. The change was not made for "
 "beauty alone. Trees lower the temperature of a street by several "
 "degrees in summer, which matters more each year, and their roots "
 "absorb rainwater that would otherwise flood the drains. The "
 "council admits the park costs more to maintain than the car park "
 "did, but says the money saved on drainage repairs more than "
 "covers it.",
 [("What was the space used for before?", ["A car park", "A pond",
   "A market", "A school"], "A car park",
   "\"a car park in the centre of Sheffield\""),
  ("What is the main reason given for planting trees?",
   ["They cool the street and absorb rainwater",
    "They look beautiful", "They are cheap",
    "They attract tourists"],
   "They cool the street and absorb rainwater",
   "\"Trees lower the temperature... their roots absorb rainwater\""),
  ("What does the council admit?",
   ["The park costs more to maintain", "The park is too small",
    "Nobody uses the park", "The trees are dying"],
   "The park costs more to maintain",
   "\"the park costs more to maintain than the car park did\""),
  ("Why is the extra cost acceptable?",
   ["Drainage repairs cost less now", "The council received a grant",
    "Visitors pay to enter", "The trees were donated"],
   "Drainage repairs cost less now",
   "\"the money saved on drainage repairs more than covers it\"")]),
("The Night Shift", "B1",
 "Working at night pays about fifteen per cent more than the same "
 "job during the day, and for that reason it attracts people who "
 "need money quickly. What is less often discussed is the cost. "
 "The human body expects to sleep in darkness, and night workers "
 "rarely get the same quality of rest even when they sleep the "
 "same number of hours. Studies of hospital staff have found that "
 "mistakes are most likely between three and five in the morning, "
 "which is exactly when the body is least alert. Most night "
 "workers say the hardest part is not the work itself but the "
 "effect on family life.",
 [("Why do people choose night work?", ["It pays more",
   "It is easier", "It is safer", "The hours are shorter"],
   "It pays more",
   "\"Working at night pays about fifteen per cent more\""),
  ("What does the passage say about sleep?",
   ["Quality is worse even if the hours are the same",
    "Night workers sleep longer", "Night workers need less sleep",
    "Sleep is not affected"],
   "Quality is worse even if the hours are the same",
   "\"rarely get the same quality of rest even when they sleep the "
   "same number of hours\""),
  ("When do most mistakes happen?", ["Between three and five a.m.",
   "At midnight", "At the end of the shift", "In the evening"],
   "Between three and five a.m.",
   "\"mistakes are most likely between three and five in the "
   "morning\""),
  ("What do night workers find hardest?",
   ["The effect on family life", "The work itself", "The pay",
    "The travel"], "The effect on family life",
   "\"the hardest part is not the work itself but the effect on "
   "family life\"")]),
("Second-hand Clothes", "B1",
 "The second-hand clothes market has grown faster than the new "
 "clothing market for six years running. Sellers usually explain "
 "this by pointing to the environment, and that is part of the "
 "story, but surveys give a different first answer: price. Nearly "
 "seventy per cent of buyers say cost is their main reason, with "
 "the environment second. There is also a quality argument. A coat "
 "made in 1990 was often built to last a decade, while many new "
 "coats are designed for two seasons. The main complaint from "
 "buyers is not condition but sizing, since older labels rarely "
 "match modern measurements.",
 [("What is buyers' main reason for choosing second-hand?",
   ["Price", "The environment", "Fashion", "Quality"], "Price",
   "\"Nearly seventy per cent of buyers say cost is their main "
   "reason\""),
  ("What is said about older coats?",
   ["They were made to last longer", "They were cheaper",
    "They were warmer", "They were rare"],
   "They were made to last longer",
   "\"A coat made in 1990 was often built to last a decade\""),
  ("What do buyers complain about most?", ["Sizing", "Condition",
   "Price", "Delivery"], "Sizing",
   "\"The main complaint from buyers is not condition but sizing\""),
  ("How long has the market grown faster than new clothing?",
   ["Six years", "Two years", "Ten years", "One year"],
   "Six years",
   "\"has grown faster than the new clothing market for six years "
   "running\"")]),
("The Return of the Tram", "B1",
 "Many European cities removed their tram lines in the 1950s and "
 "60s to make room for cars. A surprising number are now putting "
 "them back. A tram carries far more people per metre of street "
 "than a bus lane, and because the route is fixed, shops and "
 "housing are built along it with confidence. The disadvantage is "
 "the cost of construction, which is roughly ten times that of a "
 "bus route, and the disruption while the rails are laid. Cities "
 "that have done it say the first two years are painful and the "
 "next twenty are not.",
 [("Why were tram lines removed?", ["To make room for cars",
   "Because they were unpopular", "Because of cost",
   "Because of accidents"], "To make room for cars",
   "\"removed their tram lines in the 1950s and 60s to make room "
   "for cars\""),
  ("Why do developers build along tram routes?",
   ["The route does not change", "The land is cheap",
    "There is more parking", "The council pays them"],
   "The route does not change",
   "\"because the route is fixed, shops and housing are built "
   "along it with confidence\""),
  ("What is the main disadvantage?", ["The cost of construction",
   "Low capacity", "Noise", "Slow speed"],
   "The cost of construction",
   "\"The disadvantage is the cost of construction\""),
  ("What do cities say about the experience?",
   ["The first two years are difficult", "It was a mistake",
    "It was cheaper than expected", "Nothing changed"],
   "The first two years are difficult",
   "\"the first two years are painful and the next twenty are "
   "not\"")]),
# ----------------------------- B2 -----------------------------
("The Cost of Convenience", "B2",
 "Home delivery is usually presented as an environmental win: one "
 "van replaces twenty car journeys. The arithmetic holds only when "
 "the van is full and the customer is at home. In practice, "
 "roughly one delivery in eight fails on the first attempt, and "
 "each retry cancels the saving entirely. Retailers know this, "
 "which is why the industry has invested so heavily in lockers and "
 "pick-up points rather than in faster vans. The irony is that the "
 "greenest option is the one customers were originally trying to "
 "avoid: collecting the parcel themselves.",
 [("When is the environmental argument valid?",
   ["When the van is full and the customer is in",
    "When the van is electric", "When the parcel is small",
    "When delivery is free"],
   "When the van is full and the customer is in",
   "\"The arithmetic holds only when the van is full and the "
   "customer is at home.\""),
  ("What happens to the saving after a failed delivery?",
   ["It disappears completely", "It is halved",
    "It stays the same", "It doubles"],
   "It disappears completely",
   "\"each retry cancels the saving entirely\""),
  ("Why has the industry invested in lockers?",
   ["To avoid failed deliveries", "To reduce staff costs",
    "To speed up delivery", "Because of new laws"],
   "To avoid failed deliveries",
   "\"Retailers know this, which is why the industry has invested "
   "so heavily in lockers\""),
  ("What does the writer find ironic?",
   ["Collecting the parcel yourself is greenest",
    "Vans are getting bigger", "Delivery is now expensive",
    "Customers prefer shops"],
   "Collecting the parcel yourself is greenest",
   "\"the greenest option is the one customers were originally "
   "trying to avoid\"")]),
("Why Meetings Multiply", "B2",
 "Ask any office worker what wastes most of their week and the "
 "answer is rarely the work itself. Meetings expand because they "
 "are cheap for the person calling them and expensive for everyone "
 "else: the organiser spends one hour, the eight attendees spend "
 "eight. Since that cost never appears on any budget, there is no "
 "pressure to control it. The organisations that have solved the "
 "problem did not ban meetings; they made the cost visible, "
 "usually by displaying the total staff hours next to the invite.",
 [("Why do meetings multiply?",
   ["The cost falls on other people", "Managers enjoy them",
    "Work is complicated", "There are no rules"],
   "The cost falls on other people",
   "\"they are cheap for the person calling them and expensive for "
   "everyone else\""),
  ("Why is there no pressure to control meetings?",
   ["The cost is not recorded anywhere",
    "Nobody complains", "They are short",
    "They are required by law"],
   "The cost is not recorded anywhere",
   "\"that cost never appears on any budget\""),
  ("What did successful organisations do?",
   ["They made the cost visible", "They banned meetings",
    "They shortened meetings", "They reduced staff"],
   "They made the cost visible",
   "\"they made the cost visible\""),
  ("What is the writer's attitude to banning meetings?",
   ["It is not the solution he describes",
    "He strongly recommends it", "He says it is illegal",
    "He says it saves the most time"],
   "It is not the solution he describes",
   "\"did not ban meetings; they made the cost visible\"")]),
("The Language of Menus", "B2",
 "Restaurant menus are written with unusual care, and almost none "
 "of it is about accuracy. Removing the currency symbol from "
 "prices reliably increases spending, because the symbol reminds "
 "diners that they are parting with money. Long descriptions work "
 "in the same direction: a dish described in twelve words is "
 "chosen more often than the same dish described in three. What "
 "does not work, and this surprises restaurateurs, is placing the "
 "most profitable dish first. Diners tend to remember the second "
 "and third items in a list, which is where experienced designers "
 "put the food they most want to sell.",
 [("Why is the currency symbol removed?",
   ["It reminds diners about money", "It looks untidy",
    "It confuses tourists", "It takes space"],
   "It reminds diners about money",
   "\"the symbol reminds diners that they are parting with money\""),
  ("What effect do long descriptions have?",
   ["The dish is chosen more often", "The dish seems expensive",
    "Diners take longer to order", "Diners order less"],
   "The dish is chosen more often",
   "\"a dish described in twelve words is chosen more often\""),
  ("What surprises restaurateurs?",
   ["Putting the best dish first does not work",
    "Prices should be higher", "Menus should be shorter",
    "Photographs reduce sales"],
   "Putting the best dish first does not work",
   "\"What does not work, and this surprises restaurateurs, is "
   "placing the most profitable dish first.\""),
  ("Where do designers place the dishes they want to sell?",
   ["Second and third in the list", "At the top",
    "At the bottom", "In a separate box"],
   "Second and third in the list",
   "\"Diners tend to remember the second and third items in a "
   "list, which is where experienced designers put the food\"")]),
("Reading the Weather Without Instruments", "B2",
 "Long before satellites, sailors predicted weather with a "
 "reliability that modern forecasters find respectable for the "
 "following twelve hours, though useless beyond that. Their rules "
 "were observations rather than theories. A halo round the moon "
 "indicates high cloud, which often precedes a warm front. Smoke "
 "that rises straight up suggests high pressure and settled "
 "conditions; smoke that hangs low suggests the opposite. The "
 "limitation is obvious: every one of these signs describes what "
 "the atmosphere is doing now, and none of them can see a system "
 "that has not yet arrived.",
 [("How good were sailors' predictions?",
   ["Reliable for about twelve hours", "Better than satellites",
    "Reliable for a week", "Almost never right"],
   "Reliable for about twelve hours",
   "\"a reliability that modern forecasters find respectable for "
   "the following twelve hours\""),
  ("What does a halo round the moon indicate?",
   ["High cloud", "Rain within an hour", "High pressure",
    "Fog"], "High cloud",
   "\"A halo round the moon indicates high cloud\""),
  ("What does rising smoke suggest?",
   ["Settled conditions", "A coming storm", "Falling pressure",
    "Strong wind"], "Settled conditions",
   "\"Smoke that rises straight up suggests high pressure and "
   "settled conditions\""),
  ("What is the main limitation of these signs?",
   ["They only describe the present", "They need instruments",
    "They only work at sea", "They are difficult to learn"],
   "They only describe the present",
   "\"every one of these signs describes what the atmosphere is "
   "doing now\"")]),
("The Museum That Gave Things Back", "B2",
 "In 2019 a small European museum returned a collection of carved "
 "figures to the community they had been taken from a century "
 "earlier. The decision was less controversial inside the museum "
 "than outside it. Curators had known for years that the objects "
 "were acquired under conditions no modern institution would "
 "accept. What made the case unusual was the outcome: rather than "
 "disappearing from public view, the figures are now displayed in "
 "a new building funded partly by the museum, and visitor numbers "
 "at the original museum rose in the year that followed.",
 [("Who found the decision least controversial?",
   ["The museum's own curators", "The public",
    "The government", "Other museums"],
   "The museum's own curators",
   "\"The decision was less controversial inside the museum than "
   "outside it.\""),
  ("Why did curators support the return?",
   ["The objects were acquired unacceptably",
    "The objects were damaged", "There was no space",
    "The objects were fakes"],
   "The objects were acquired unacceptably",
   "\"the objects were acquired under conditions no modern "
   "institution would accept\""),
  ("What happened to the figures afterwards?",
   ["They went on display in a new building",
    "They were put into storage", "They were sold",
    "They were copied"],
   "They went on display in a new building",
   "\"the figures are now displayed in a new building\""),
  ("What happened to the museum's visitor numbers?",
   ["They rose", "They fell sharply", "They stayed the same",
    "They were not counted"], "They rose",
   "\"visitor numbers at the original museum rose in the year that "
   "followed\"")]),
("The Trouble with Averages", "B2",
 "In the 1950s the American air force redesigned cockpits around "
 "the average pilot and accident rates refused to fall. A young "
 "researcher measured four thousand pilots on ten dimensions and "
 "found that not one of them was average on all ten; fewer than "
 "four per cent were average on even three. The conclusion was "
 "not that the measurements were wrong but that the average pilot "
 "did not exist. The response, adjustable seats and pedals, is now "
 "so ordinary that its origin has been forgotten.",
 [("What problem did the redesign fail to solve?",
   ["Accident rates", "Fuel costs", "Pilot training time",
   "Cockpit weight"], "Accident rates",
   "\"redesigned cockpits around the average pilot and accident "
   "rates refused to fall\""),
  ("How many pilots were average on all ten dimensions?",
   ["None", "Four per cent", "Half", "Most"], "None",
   "\"not one of them was average on all ten\""),
  ("What was the conclusion?",
   ["The average pilot does not exist",
    "The measurements were wrong", "Pilots were too tall",
    "More training was needed"],
   "The average pilot does not exist",
   "\"the average pilot did not exist\""),
  ("What was the practical response?",
   ["Adjustable seats and pedals", "Smaller cockpits",
    "Stricter selection", "Longer training"],
   "Adjustable seats and pedals",
   "\"The response, adjustable seats and pedals\"")]),
("Why Some Bridges Sing", "B2",
 "When wind passes a cable, it sheds small swirls of air "
 "alternately from each side, and each swirl gives the cable a "
 "tiny push. If the rhythm of those pushes happens to match the "
 "cable's own natural frequency, the movement grows instead of "
 "dying away. On most bridges the effect is audible rather than "
 "dangerous, which is why some structures hum in a steady wind. "
 "Engineers rarely try to stop the swirls; it is easier to change "
 "the cable so that its natural frequency no longer matches, "
 "usually by adding a small weight or a spiral of plastic.",
 [("What causes the pushes on a cable?",
   ["Swirls of air shed from each side", "Rain", "Traffic",
    "Temperature change"], "Swirls of air shed from each side",
   "\"it sheds small swirls of air alternately from each side\""),
  ("When does the movement grow?",
   ["When the rhythm matches the cable's natural frequency",
    "When the wind is very strong", "At night",
    "When the bridge is new"],
   "When the rhythm matches the cable's natural frequency",
   "\"If the rhythm of those pushes happens to match the cable's "
   "own natural frequency, the movement grows\""),
  ("On most bridges the effect is:",
   ["Audible but not dangerous", "Extremely dangerous",
    "Invisible", "Seasonal"], "Audible but not dangerous",
   "\"the effect is audible rather than dangerous\""),
  ("What do engineers usually do?",
   ["Change the cable's frequency", "Stop the swirls",
    "Close the bridge in wind", "Replace the cable"],
   "Change the cable's frequency",
   "\"it is easier to change the cable so that its natural "
   "frequency no longer matches\"")]),
("The Slowest Experiment", "B2",
 "In 1927 a professor in Australia heated a lump of pitch, poured "
 "it into a funnel and let it settle for three years before "
 "cutting the stem. The point was to show students that a "
 "substance which shatters like glass when struck is in fact a "
 "liquid. Nine drops have fallen since. No one has ever seen one "
 "fall: the professor missed the first, a camera failed on another "
 "occasion, and a technician stepped out for a cup of tea before "
 "the eighth. The experiment is still running, in a cabinet, "
 "watched now by a webcam.",
 [("What was the experiment designed to show?",
   ["That pitch is a liquid", "That pitch is a solid",
    "How glass is made", "How funnels work"],
   "That pitch is a liquid",
   "\"a substance which shatters like glass when struck is in fact "
   "a liquid\""),
  ("How long did the pitch settle before the stem was cut?",
   ["Three years", "One year", "Nine years", "Ten years"],
   "Three years",
   "\"let it settle for three years before cutting the stem\""),
  ("What is true of all nine drops?",
   ["Nobody saw them fall", "They fell at night",
    "They were filmed", "They fell in the same year"],
   "Nobody saw them fall",
   "\"No one has ever seen one fall\""),
  ("Why was the eighth drop missed?",
   ["The technician went for tea", "The camera failed",
    "The lab was closed", "It fell too fast"],
   "The technician went for tea",
   "\"a technician stepped out for a cup of tea before the "
   "eighth\"")]),
# ----------------------------- C1 -----------------------------
("The Economics of Repair", "C1",
 "For most of the twentieth century, mending a broken appliance "
 "was cheaper than replacing it, and an entire trade existed to do "
 "so. The reversal was not caused by greed alone. Manufacturing "
 "costs fell faster than wages rose, so the hour of skilled labour "
 "needed to diagnose a fault came to cost more than the machine "
 "itself. Legislation now moving through several parliaments "
 "attacks the problem from an unexpected direction: rather than "
 "subsidising repair, it obliges manufacturers to publish "
 "schematics and to keep spare parts available for a fixed period. "
 "The intention is to make repair possible, not to make it "
 "cheap — a distinction that campaigners have not always drawn "
 "clearly, and one that will determine whether the laws are judged "
 "a success.",
 [("Why did repair become uneconomic?",
   ["Labour costs overtook manufacturing costs",
    "Companies stopped making parts",
    "Appliances became more reliable",
    "Repairers retired"],
   "Labour costs overtook manufacturing costs",
   "\"the hour of skilled labour... came to cost more than the "
   "machine itself\""),
  ("What do the new laws require?",
   ["Publishing schematics and stocking parts",
    "Subsidising repair shops", "Longer warranties",
    "Lower prices"],
   "Publishing schematics and stocking parts",
   "\"it obliges manufacturers to publish schematics and to keep "
   "spare parts available\""),
  ("What distinction does the writer emphasise?",
   ["Between making repair possible and making it cheap",
    "Between old and new appliances",
    "Between labour and materials",
    "Between laws and campaigns"],
   "Between making repair possible and making it cheap",
   "\"The intention is to make repair possible, not to make it "
   "cheap\""),
  ("What is the writer's view of campaigners?",
   ["They have blurred an important distinction",
    "They have been entirely wrong",
    "They caused the legislation",
    "They oppose the laws"],
   "They have blurred an important distinction",
   "\"a distinction that campaigners have not always drawn clearly\"")]),
("Silence in Architecture", "C1",
 "Acoustic design is usually discussed in terms of what a building "
 "should let you hear. The harder problem is what it should let "
 "you not hear. An open-plan office is quiet by any meter — the "
 "measured sound level is often lower than in a library — yet "
 "workers report far greater disturbance, because intelligible "
 "speech captures attention in a way that undifferentiated noise "
 "does not. The counter-intuitive remedy, now common in call "
 "centres, is to add sound rather than remove it: a low background "
 "hiss makes neighbouring conversations unintelligible and "
 "therefore ignorable. Architects resisted the idea for years, "
 "largely because it conflicts with the instinct that silence is "
 "the goal.",
 [("What is the harder acoustic problem?",
   ["What a building lets you not hear",
    "What a building lets you hear", "How loud a room is",
    "How sound travels"],
   "What a building lets you not hear",
   "\"The harder problem is what it should let you not hear.\""),
  ("Why is an open-plan office disturbing?",
   ["Speech can be understood", "It is very loud",
    "It has hard surfaces", "It is too quiet"],
   "Speech can be understood",
   "\"intelligible speech captures attention in a way that "
   "undifferentiated noise does not\""),
  ("What is the remedy described?",
   ["Adding background sound", "Removing all sound",
    "Building partitions", "Reducing staff numbers"],
   "Adding background sound",
   "\"The counter-intuitive remedy, now common in call centres, is "
   "to add sound rather than remove it\""),
  ("Why did architects resist?",
   ["It contradicts the instinct that silence is the goal",
    "It was expensive", "It was untested",
    "Clients refused it"],
   "It contradicts the instinct that silence is the goal",
   "\"it conflicts with the instinct that silence is the goal\"")]),
("The Map Before the Territory", "C1",
 "Explorers are remembered for reaching places; cartographers are "
 "remembered, if at all, for drawing them. Yet the sequence is "
 "frequently the reverse of what we assume. Coastlines were "
 "commonly mapped from a distance, by triangulation from a ship, "
 "decades before anyone landed, and interiors were sketched from "
 "the reports of traders who had no interest in accuracy and every "
 "interest in exaggeration. The result was a class of features "
 "that existed on paper and nowhere else: mountains that turned "
 "out to be cloud, islands that had been the same island seen "
 "twice. Some survived on official charts for a century, being "
 "copied from one edition to the next by cartographers who assumed "
 "that whoever drew them first must have had a reason.",
 [("What assumption does the writer question?",
   ["That places are visited before they are mapped",
    "That maps are accurate", "That explorers were brave",
    "That cartographers were skilled"],
   "That places are visited before they are mapped",
   "\"the sequence is frequently the reverse of what we assume\""),
  ("What was the problem with traders' reports?",
   ["They had reasons to exaggerate", "They were too brief",
    "They were written in code", "They were secret"],
   "They had reasons to exaggerate",
   "\"traders who had no interest in accuracy and every interest "
   "in exaggeration\""),
  ("What is given as an example of a false feature?",
   ["Mountains that were actually cloud",
    "Rivers that dried up", "Cities that were destroyed",
    "Coasts that eroded"],
   "Mountains that were actually cloud",
   "\"mountains that turned out to be cloud\""),
  ("Why did such errors survive so long?",
   ["Cartographers trusted earlier maps",
    "Nobody looked at the charts", "Printing was expensive",
    "Ships avoided the areas"],
   "Cartographers trusted earlier maps",
   "\"copied from one edition to the next by cartographers who "
   "assumed that whoever drew them first must have had a reason\"")]),
("The Placebo That Works Anyway", "C1",
 "The standard account of the placebo effect assumes deception: "
 "the patient must believe the tablet is active. A series of "
 "trials has undermined that assumption. Patients told explicitly "
 "that they were receiving an inert tablet, and told why such "
 "tablets sometimes help, still reported improvement in conditions "
 "such as back pain and irritable bowel syndrome. The effect is "
 "smaller than in concealed trials but it is not zero, which "
 "matters because it removes the ethical objection that has kept "
 "placebos out of ordinary practice. What it does not do is settle "
 "the mechanism. The leading explanation is that the ritual of "
 "treatment — the consultation, the routine, the expectation of "
 "attention — does work that the tablet was being credited with.",
 [("What did the standard account assume?",
   ["That the patient must be deceived",
    "That placebos never work", "That the dose matters",
    "That doctors must believe too"],
   "That the patient must be deceived",
   "\"The standard account of the placebo effect assumes "
   "deception\""),
  ("What happened when patients were told the truth?",
   ["They still improved, but less", "Nothing changed at all",
    "They got worse", "They refused treatment"],
   "They still improved, but less",
   "\"still reported improvement... The effect is smaller than in "
   "concealed trials but it is not zero\""),
  ("Why does this matter practically?",
   ["It removes an ethical objection",
    "It proves tablets are useless", "It reduces costs",
    "It speeds up trials"],
   "It removes an ethical objection",
   "\"it removes the ethical objection that has kept placebos out "
   "of ordinary practice\""),
  ("What remains unresolved?",
   ["How the effect works", "Whether the effect exists",
    "Which conditions respond", "Who should prescribe it"],
   "How the effect works",
   "\"What it does not do is settle the mechanism.\"")]),
("Writing Systems and Memory", "C1",
 "It is often said that writing was invented to record poetry or "
 "law. The earliest surviving tablets suggest something more "
 "prosaic: they are almost entirely accounts, listing quantities "
 "of grain and numbers of workers. Literature appears roughly "
 "seven centuries later. The implication is not that early "
 "societies lacked stories but that they had a perfectly adequate "
 "technology for stories already, namely memory, and no adequate "
 "technology for arithmetic performed on other people's property. "
 "Where memory served, writing was unnecessary; where it failed, "
 "writing was invented. This also explains a pattern that puzzled "
 "scholars for a long time — that the earliest scripts are poor at "
 "representing sound and excellent at representing amounts.",
 [("What do the earliest tablets contain?",
   ["Accounts", "Poetry", "Laws", "Letters"], "Accounts",
   "\"they are almost entirely accounts\""),
  ("How much later does literature appear?",
   ["About seven centuries", "About seventy years",
    "Immediately", "About two centuries"],
   "About seven centuries",
   "\"Literature appears roughly seven centuries later.\""),
  ("Why did early societies not write down stories?",
   ["Memory was already adequate for them",
    "They had no stories", "Writing was forbidden",
    "Tablets were scarce"],
   "Memory was already adequate for them",
   "\"they had a perfectly adequate technology for stories "
   "already, namely memory\""),
  ("What pattern does this explain?",
   ["Early scripts record amounts better than sounds",
    "Scripts spread slowly", "Scribes were rare",
    "Tablets were reused"],
   "Early scripts record amounts better than sounds",
   "\"the earliest scripts are poor at representing sound and "
   "excellent at representing amounts\"")]),
("The Limits of Expertise", "C1",
 "Chess masters, firefighters and nurses in intensive care develop "
 "genuine intuition: they reach correct conclusions faster than "
 "they can explain them. Stock pickers and political forecasters, "
 "who feel equally certain, do not. The difference is not "
 "intelligence or effort but the environment in which the skill is "
 "learned. Intuition requires a world regular enough to contain "
 "patterns, and feedback rapid enough to correct errors before the "
 "wrong lesson sets. A chess position is judged within moves; a "
 "market prediction may take years, by which time the forecaster "
 "has forgotten the reasoning and remembers only the outcome. "
 "Confidence, it turns out, is produced by the coherence of one's "
 "own story, and coherence is available in any environment at all.",
 [("What do chess masters and nurses have in common?",
   ["Their intuition is genuine", "They are highly intelligent",
    "They work under pressure", "They train for years"],
   "Their intuition is genuine",
   "\"Chess masters, firefighters and nurses in intensive care "
   "develop genuine intuition\""),
  ("What two conditions does intuition require?",
   ["Regular patterns and quick feedback",
    "Talent and training", "Experience and confidence",
    "Rules and supervision"],
   "Regular patterns and quick feedback",
   "\"Intuition requires a world regular enough to contain "
   "patterns, and feedback rapid enough\""),
  ("Why does forecasting fail this test?",
   ["Feedback arrives too late",
    "Forecasters are careless", "The data is poor",
    "The rules change"], "Feedback arrives too late",
   "\"a market prediction may take years, by which time the "
   "forecaster has forgotten the reasoning\""),
  ("What produces confidence, according to the writer?",
   ["A coherent personal story", "Accurate prediction",
    "Long experience", "Peer agreement"],
   "A coherent personal story",
   "\"Confidence... is produced by the coherence of one's own "
   "story\"")]),
("Weeds and Definitions", "C1",
 "A weed has no botanical definition. It is simply a plant growing "
 "where somebody does not want it, which makes weeding an act of "
 "taste as much as agriculture. The category shifts: several "
 "species now sold in garden centres were removed as weeds within "
 "living memory, and the poppy that farmers spend money to "
 "eliminate is protected on roadside verges a few metres away. "
 "This is more than a curiosity of language. Herbicide policy, "
 "conservation funding and even planning law rest on a distinction "
 "that turns out to be a preference, and the plants themselves are "
 "indifferent to which side of it they fall.",
 [("What is a weed, according to the passage?",
   ["A plant somebody does not want",
    "A fast-growing plant", "A poisonous plant",
    "A non-native plant"], "A plant somebody does not want",
   "\"a plant growing where somebody does not want it\""),
  ("What example shows the category shifting?",
   ["Plants once removed are now sold in garden centres",
    "Weeds have become rarer", "Farmers have stopped weeding",
    "New species have arrived"],
   "Plants once removed are now sold in garden centres",
   "\"several species now sold in garden centres were removed as "
   "weeds within living memory\""),
  ("What is odd about the poppy?",
   ["It is destroyed in fields but protected nearby",
    "It is poisonous", "It is imported",
    "It is very rare"],
   "It is destroyed in fields but protected nearby",
   "\"the poppy that farmers spend money to eliminate is protected "
   "on roadside verges a few metres away\""),
  ("Why does the writer say this matters?",
   ["Policy and funding depend on the distinction",
    "Weeds are increasing", "Gardens are changing",
    "Language is imprecise"],
   "Policy and funding depend on the distinction",
   "\"Herbicide policy, conservation funding and even planning law "
   "rest on a distinction that turns out to be a preference\"")]),
("The Second-Best Route", "C1",
 "Adding a road to a congested network can make every journey "
 "slower. The result, demonstrated mathematically in 1968 and "
 "since observed in several cities, follows from the fact that "
 "drivers choose selfishly rather than collectively: each takes "
 "the route that is fastest for them given everyone else's "
 "choices, and the equilibrium they settle into need not be the "
 "arrangement that minimises total travel time. Closing a road can "
 "therefore improve flow, as Seoul and New York both found when "
 "they removed urban motorways and traffic did not simply move "
 "elsewhere. The uncomfortable implication for transport planning "
 "is that intuition about capacity is unreliable, and that "
 "modelling is not an optional refinement but the only defence "
 "against confident error.",
 [("What can adding a road do?",
   ["Make every journey slower", "Always reduce congestion",
    "Reduce accidents", "Increase road tax"],
   "Make every journey slower",
   "\"Adding a road to a congested network can make every journey "
   "slower.\""),
  ("Why does this happen?",
   ["Drivers choose selfishly, not collectively",
    "Roads are badly built", "There are too many cars",
    "Traffic lights fail"],
   "Drivers choose selfishly, not collectively",
   "\"drivers choose selfishly rather than collectively\""),
  ("What did Seoul and New York discover?",
   ["Removing motorways improved flow",
    "Traffic moved to other roads", "Congestion doubled",
    "Costs increased"], "Removing motorways improved flow",
   "\"they removed urban motorways and traffic did not simply move "
   "elsewhere\""),
  ("What is the implication for planners?",
   ["Modelling is essential, not optional",
    "Roads should never be built", "Intuition is reliable",
    "Cities should expand"],
   "Modelling is essential, not optional",
   "\"modelling is not an optional refinement but the only defence "
   "against confident error\"")]),
# ----------------------------- C2 -----------------------------
("The Tyranny of the Measurable", "C2",
 "Every institution that adopts a metric discovers, sooner or "
 "later, that the metric has begun to adopt it. The mechanism is "
 "not corruption but substitution: because the number is legible "
 "and the underlying goal is not, effort migrates towards the "
 "number with no dishonest intention on anyone's part. Hospitals "
 "judged on waiting times became fast; whether they became better "
 "is a separate question that the data was never designed to "
 "answer. What makes the problem intractable is that the obvious "
 "correction — measure more things — reproduces the pathology at "
 "greater expense, since a basket of proxies is still a basket of "
 "proxies. The institutions that have escaped tend to share an "
 "unfashionable feature: somebody senior retains the authority to "
 "override the figures, and is expected to justify doing so in "
 "words.",
 [("What does the writer identify as the mechanism?",
   ["Substitution of the measurable for the goal",
    "Deliberate corruption", "Poor data collection",
    "Lack of training"],
   "Substitution of the measurable for the goal",
   "\"The mechanism is not corruption but substitution\""),
  ("What does the hospital example illustrate?",
   ["Speed improved but quality was not measured",
    "Metrics always fail", "Waiting times are unimportant",
    "Data was falsified"],
   "Speed improved but quality was not measured",
   "\"Hospitals judged on waiting times became fast; whether they "
   "became better is a separate question\""),
  ("Why does measuring more things not help?",
   ["More proxies are still proxies",
    "It costs too little", "Staff resist it",
    "The data conflicts"], "More proxies are still proxies",
   "\"a basket of proxies is still a basket of proxies\""),
  ("What do successful institutions share?",
   ["Someone senior may override the figures",
    "They use no metrics", "They publish everything",
    "They employ statisticians"],
   "Someone senior may override the figures",
   "\"somebody senior retains the authority to override the "
   "figures\"")]),
("On Not Finishing Books", "C2",
 "The moral weight attached to finishing a book is a recent and "
 "largely commercial invention. For most of the history of "
 "reading, texts were consulted rather than consumed; the "
 "commonplace book, in which readers copied passages that struck "
 "them, treats a volume as a quarry rather than a journey. The "
 "shift towards the novel, and towards the expectation of a single "
 "sustained arc, made abandonment feel like failure — and the "
 "publishing industry, whose interests are served by completion "
 "and by the purchase of the next volume, had no reason to correct "
 "the impression. There is a case for guilt, but it is a narrower "
 "one than usually made: not that unfinished books are wasted, but "
 "that the habit of abandonment can become indistinguishable from "
 "the inability to concentrate, and only the reader can tell which "
 "is which.",
 [("How does the writer describe the duty to finish books?",
   ["Recent and commercially convenient",
    "Ancient and universal", "Purely academic",
    "Imposed by teachers"],
   "Recent and commercially convenient",
   "\"a recent and largely commercial invention\""),
  ("What does the commonplace book show?",
   ["Books were treated as a quarry",
    "Readers finished everything", "Books were rare",
    "Copying was forbidden"],
   "Books were treated as a quarry",
   "\"treats a volume as a quarry rather than a journey\""),
  ("What made abandonment feel like failure?",
   ["The rise of the novel and its single arc",
    "Cheaper printing", "Compulsory education",
    "Public libraries"],
   "The rise of the novel and its single arc",
   "\"The shift towards the novel, and towards the expectation of "
   "a single sustained arc, made abandonment feel like failure\""),
  ("What narrower case for guilt does the writer accept?",
   ["Abandonment may mask an inability to concentrate",
    "Unfinished books waste money",
    "Readers insult authors", "Libraries lose out"],
   "Abandonment may mask an inability to concentrate",
   "\"the habit of abandonment can become indistinguishable from "
   "the inability to concentrate\"")]),
("The Archive and the Fire", "C2",
 "Archivists have long accepted a proposition that unsettles "
 "everyone else: that total preservation is neither possible nor "
 "desirable. Selection is not a regrettable consequence of limited "
 "shelving but the discipline's central intellectual act, and the "
 "criteria are necessarily those of the present, applied to "
 "material whose future usefulness cannot be known. The digital "
 "turn was expected to dissolve the problem, storage having become "
 "effectively free. It has instead sharpened it, because the "
 "constraint has moved from space to attention: an archive that "
 "keeps everything and describes nothing is functionally "
 "identical to one that burned. Cataloguing, not capacity, is now "
 "the binding limit, and cataloguing requires exactly the "
 "judgements that abundance was supposed to make unnecessary.",
 [("What proposition do archivists accept?",
   ["Total preservation is neither possible nor desirable",
    "Everything should be kept", "Digital copies are enough",
    "Selection should be automatic"],
   "Total preservation is neither possible nor desirable",
   "\"total preservation is neither possible nor desirable\""),
  ("How does the writer characterise selection?",
   ["The central intellectual act of the discipline",
    "A regrettable necessity", "A technical problem",
    "A political choice"],
   "The central intellectual act of the discipline",
   "\"Selection is not a regrettable consequence of limited "
   "shelving but the discipline's central intellectual act\""),
  ("What did the digital turn do to the problem?",
   ["Sharpened it", "Solved it", "Postponed it",
    "Made it irrelevant"], "Sharpened it",
   "\"It has instead sharpened it\""),
  ("What is now the binding limit?",
   ["Cataloguing", "Storage space", "Funding",
    "Copyright"], "Cataloguing",
   "\"Cataloguing, not capacity, is now the binding limit\"")]),
("Translating What Is Not Said", "C2",
 "The hardest sentences to translate are rarely the ornate ones. "
 "Ornament can be approximated; implication cannot. A Japanese "
 "sentence may leave the subject unstated because the "
 "relationship between speaker and listener makes it obvious, and "
 "English will not permit the omission, so the translator must "
 "decide something the original declined to decide. Every "
 "resolution of such an ambiguity is an addition, and the "
 "cumulative effect of a thousand small additions is a text that "
 "is clearer than the original and, in exactly that respect, "
 "wrong. The best translators are therefore recognisable less by "
 "their fluency than by their willingness to leave a sentence "
 "slightly awkward where awkwardness is the only honest "
 "equivalent.",
 [("What is hardest to translate?",
   ["Implication", "Ornament", "Idiom", "Humour"],
   "Implication",
   "\"Ornament can be approximated; implication cannot.\""),
  ("Why must the translator decide something extra?",
   ["English does not allow the omission",
    "The original is unclear", "Editors demand it",
    "Readers expect it"],
   "English does not allow the omission",
   "\"English will not permit the omission, so the translator must "
   "decide something the original declined to decide\""),
  ("What is the cumulative effect of such decisions?",
   ["A text clearer than the original and therefore wrong",
    "A shorter text", "A more beautiful text",
    "An unreadable text"],
   "A text clearer than the original and therefore wrong",
   "\"a text that is clearer than the original and, in exactly "
   "that respect, wrong\""),
  ("How are the best translators recognised?",
   ["By tolerating necessary awkwardness",
    "By their fluency", "By their speed",
    "By their footnotes"],
   "By tolerating necessary awkwardness",
   "\"their willingness to leave a sentence slightly awkward where "
   "awkwardness is the only honest equivalent\"")]),
("The Uses of Boredom", "C2",
 "Boredom has been treated for a century as a deficiency — of "
 "stimulation, of imagination, of moral fibre — and only recently "
 "as a signal. The reframing matters because the two accounts "
 "recommend opposite responses. If boredom is a deficit, the cure "
 "is input, and the device in the pocket supplies it "
 "inexhaustibly. If it is a signal that current activity is not "
 "worth continuing, then suppressing it removes the very "
 "discomfort that would have prompted a change. Experimental work "
 "is suggestive rather than conclusive: bored subjects generate "
 "more unusual uses for everyday objects than entertained ones, "
 "which is a narrow finding often reported as though it "
 "established that boredom causes creativity. It establishes "
 "something more modest and more useful — that the mind, left "
 "without instruction, does not idle.",
 [("How was boredom traditionally understood?",
   ["As a deficiency", "As a signal", "As an illness",
    "As a choice"], "As a deficiency",
   "\"Boredom has been treated for a century as a deficiency\""),
  ("Why does the reframing matter?",
   ["The two accounts recommend opposite responses",
    "It changes the definition", "It affects diagnosis",
    "It is more scientific"],
   "The two accounts recommend opposite responses",
   "\"the two accounts recommend opposite responses\""),
  ("What is the risk of suppressing boredom?",
   ["It removes the prompt to change",
    "It causes anxiety", "It wastes time",
    "It reduces attention"], "It removes the prompt to change",
   "\"suppressing it removes the very discomfort that would have "
   "prompted a change\""),
  ("What does the writer say the experiments establish?",
   ["The mind does not idle when unoccupied",
    "Boredom causes creativity",
    "Entertainment reduces intelligence",
    "Nothing at all"], "The mind does not idle when unoccupied",
   "\"the mind, left without instruction, does not idle\"")]),
("The Invention of the Teenager", "C2",
 "Adolescence is a biological fact; the teenager is a marketing "
 "category, and the two are separated by about a century. Before "
 "the 1940s, the years between childhood and adult work were "
 "short, unnamed and spent largely in the company of adults. What "
 "created the teenager was not rebellion but the coincidence of "
 "three duller developments: compulsory schooling extended past "
 "puberty, which grouped the age cohort together for the first "
 "time; disposable income among the young; and a media industry "
 "that discovered it could sell to them directly rather than "
 "through their parents. The rebellion came afterwards and was "
 "sold back to them, which is why every subsequent youth movement "
 "has had a shop.",
 [("How does the writer distinguish adolescence and the teenager?",
   ["One is biological, the other commercial",
    "One is older than the other", "They are the same",
    "One is legal, the other social"],
   "One is biological, the other commercial",
   "\"Adolescence is a biological fact; the teenager is a "
   "marketing category\""),
  ("What did compulsory schooling do?",
   ["Grouped the age cohort together",
    "Reduced child labour", "Raised literacy",
    "Delayed marriage"], "Grouped the age cohort together",
   "\"compulsory schooling extended past puberty, which grouped "
   "the age cohort together for the first time\""),
  ("What does the writer say about rebellion?",
   ["It came after the category and was sold back",
    "It created the category", "It was invented by parents",
    "It never existed"],
   "It came after the category and was sold back",
   "\"The rebellion came afterwards and was sold back to them\""),
  ("What does the final clause explain?",
   ["Why youth movements have shops",
    "Why schooling was extended", "Why incomes rose",
    "Why parents objected"],
   "Why youth movements have shops",
   "\"which is why every subsequent youth movement has had a "
   "shop\"")]),
("Certainty and the Weather Forecast", "C2",
 "A forecast that says 'seventy per cent chance of rain' is "
 "routinely judged wrong when the day turns out dry, which "
 "reveals more about the audience than the forecaster. "
 "Probabilistic statements are unfalsifiable one day at a time; "
 "they can only be assessed across many days, by asking whether it "
 "rained on about seventy per cent of the occasions the phrase was "
 "used. By that standard, national forecasters are strikingly well "
 "calibrated, better than doctors estimating survival and far "
 "better than economists. The persistent complaint arises because "
 "listeners want a decision — umbrella or no umbrella — and a "
 "probability declines to supply one. Broadcasters who have tried "
 "to meet that demand by rounding to certainty are more popular "
 "and measurably less accurate.",
 [("Why is a single forecast not falsifiable?",
   ["Probabilities can only be judged over many days",
    "Forecasters change their minds", "Weather is chaotic",
    "The wording is vague"],
   "Probabilities can only be judged over many days",
   "\"they can only be assessed across many days\""),
  ("How do national forecasters compare with doctors?",
   ["Forecasters are better calibrated",
    "Doctors are better calibrated", "They are equal",
    "The comparison is not made"],
   "Forecasters are better calibrated",
   "\"better than doctors estimating survival\""),
  ("Why do listeners complain?",
   ["They want a decision, not a probability",
    "Forecasts are too long", "The language is technical",
    "Forecasts are often wrong"],
   "They want a decision, not a probability",
   "\"listeners want a decision — umbrella or no umbrella — and a "
   "probability declines to supply one\""),
  ("What happens to broadcasters who round to certainty?",
   ["They are more popular but less accurate",
    "They lose their audience", "They are more accurate",
    "They are prosecuted"],
   "They are more popular but less accurate",
   "\"are more popular and measurably less accurate\"")]),
("What Cities Remember", "C2",
 "A street name is the cheapest form of monument and the hardest "
 "to remove, which is why the politics of renaming are so much "
 "fiercer than the politics of statues. A statue can be relocated "
 "to a museum, where context can be supplied; a street name lives "
 "in deeds, utility bills and the habits of the people who use it, "
 "and no plaque accompanies it. The consequence is that cities "
 "carry commitments they never consciously renewed — honouring "
 "figures nobody now defends, and doing so in the only civic "
 "language that residents encounter daily without noticing. "
 "Proposals to rename are therefore rarely arguments about the "
 "past; they are arguments about how much friction a society is "
 "willing to accept in order to stop saying something it no longer "
 "means.",
 [("Why is renaming fiercer than removing statues?",
   ["A street name cannot be given context elsewhere",
    "Street names are older", "Statues are cheaper",
    "Nobody notices statues"],
   "A street name cannot be given context elsewhere",
   "\"A statue can be relocated to a museum, where context can be "
   "supplied; a street name lives in deeds... and no plaque "
   "accompanies it\""),
  ("What do cities end up carrying?",
   ["Commitments they never consciously renewed",
    "Debts from the past", "Legal obligations",
    "Tourist attractions"],
   "Commitments they never consciously renewed",
   "\"cities carry commitments they never consciously renewed\""),
  ("How do residents encounter these names?",
   ["Daily, without noticing", "Only in documents",
    "Through the media", "On special occasions"],
   "Daily, without noticing",
   "\"the only civic language that residents encounter daily "
   "without noticing\""),
  ("What are renaming proposals really about?",
   ["How much friction a society will accept",
    "Historical accuracy", "The cost of new signs",
    "Tourism revenue"],
   "How much friction a society will accept",
   "\"they are arguments about how much friction a society is "
   "willing to accept\"")]),
]
