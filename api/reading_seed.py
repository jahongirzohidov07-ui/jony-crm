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

    Marker reading_v2 (2026-08-24): SEED2 dagi yangi darajali matnlar
    jonli bazaga ham tushishi uchun."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "reading_v2"):
        return None
    import json
    import models
    have = {t for (t,) in db.query(models.ReadingText.title).all()}
    made = 0
    for title, level, body, questions in SEED + SEED2:
        if title in have:
            continue
        tx = models.ReadingText(title=title, level=level, body=body)
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
    _seed_mark(db, "reading_v2")
    return made
