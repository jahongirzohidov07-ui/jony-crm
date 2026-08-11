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


def seed_reading(db):
    """Idempotent: sarlavha bo'yicha faqat yo'q matnlar qo'shiladi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "reading_v1"):
        return None
    import json
    import models
    have = {t for (t,) in db.query(models.ReadingText.title).all()}
    made = 0
    for title, level, body, questions in SEED:
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
    _seed_mark(db, "reading_v1")
    return made
