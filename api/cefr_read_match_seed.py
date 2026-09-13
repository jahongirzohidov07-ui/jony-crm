# -*- coding: utf-8 -*-
"""CEFR READING 2-QISM — MATCHING PEOPLE TO TEXTS (2026-08-26).

Jahongir: "ha barcha qismlarni qil."

FORMAT (kitobdan, Multilevel Master Reading, Part 2): sakkizta
qisqa e'lon (kurs, xizmat, ustoz, joy) raqamlangan qutilarda
beriladi. Keyin beshta odam tasvirlanadi va har biriga eng mos
e'lonni tanlash kerak. E'lonlar ORTIQCHA — beshtasi ishlatiladi,
uchtasi qolib ketadi.

BU TURNING O'ZIGA XOSLIGI. Bu tur o'qib tushunishni emas, TEZ
SKANERLASHNI sinaydi. Odam tasvirida odatda 2-3 ta shart bo'ladi
(masalan: kechqurun bo'lsin + boshlang'ich daraja + arzon) va
faqat BITTA e'lon uchalasiga ham javob beradi. Bitta shartga
qarab tanlash — eng ko'p uchraydigan xato.

MANBA. Kitob skaner qilingan, matn qatlami yo'q. E'lonlar va
odamlar shu yerda yozilgan, lekin format kitobdagiga aynan mos.
Har javob DASTUR bilan tekshiriladi: to'g'ri e'lon odamning
BARCHA shartlariga javob berishi, qolganlari esa kamida bittasiga
javob bermasligi shart.
"""

SKILL = "ielts_reading"
KIND = "cefr_match"
LET = ["A", "B", "C", "D", "E", "F", "G", "H"]
INSTR = ("Read the descriptions of five people and the eight "
         "notices. Decide which notice would be the most suitable "
         "for each person.")


CEFR_MATCH_TIPS = [
    ("Bu mashq nima",
     "Sakkizta qisqa e'lon va beshta odam beriladi. Har odamga eng "
     "mos e'lonni tanlaysiz. UCHTA e'lon ortiqcha — ular hech "
     "kimga to'g'ri kelmaydi.", ""),
    ("Avval ODAMNI o'qing, e'lonlarni emas",
     "Odam tasvirida odatda 2-3 ta SHART bo'ladi. Ularni "
     "belgilab oling, keyin e'lonlarni skanerlang. Aks holda "
     "sakkizta e'lonni sakkiz marta qayta o'qishga to'g'ri "
     "keladi.",
     "«He works during the day, has never played before, and "
     "cannot spend much.»\nShartlar: KECHQURUN + BOSHLANG'ICH + "
     "ARZON."),
    ("Hamma shart bajarilishi kerak",
     "Bitta shartga mos kelgan e'lon to'g'ri javob emas. To'g'ri "
     "javob HAMMA shartga javob beradi. Eng ko'p uchraydigan xato "
     "— birinchi mos kelgan so'zni ko'rib to'xtab qolish.", ""),
    ("Bir xil so'z — qopqon",
     "E'londa odam tasviridagi so'z aynan uchrasa, bu ko'pincha "
     "ataylab qo'yilgan. To'g'ri e'lon odatda o'sha fikrni "
     "BOSHQACHA aytadi.", ""),
    ("Ortiqcha e'lonlar bekorga qo'yilmaydi",
     "Uchta ortiqcha e'lon har biri kimningdir bitta shartiga "
     "javob beradi, lekin qolganiga bermaydi. Ular sizni sinash "
     "uchun turibdi.", ""),
    ("Sonlarga, kunlarga va narxga alohida qarang",
     "Ko'pincha farq aynan shu yerda bo'ladi: yosh chegarasi, "
     "hafta kuni, daraja yoki narx. Ikki e'lon deyarli bir xil "
     "bo'lsa, farqni shu ustunlardan qidiring.", ""),
    ("Ishonchsizini oxiriga qoldiring",
     "Oson mosliklarni avval belgilang — qolgan e'lonlar soni "
     "kamayadi va qiyini o'z-o'zidan ochiladi.", ""),
]


def S(level, topic, notices, people):
    """notices: [(sarlavha, matn, {xususiyatlar})] — 8 ta
       people:  [(tasvir, [kerakli xususiyatlar], indeks)] — 5 ta"""
    return {"level": level, "topic": topic,
            "notices": notices, "people": people}


SETS = []

SETS.append(S(1, "Evening classes at the community centre", [
 ("Pottery for Beginners",
  "No experience needed. Tuesdays and Thursdays, 7-9 p.m. "
  "Materials included in the low termly fee.",
  {"evening", "beginner", "cheap", "art"}),
 ("Advanced Spanish Conversation",
  "For speakers who are already fluent and want to discuss "
  "current affairs. Wednesdays, 7.30 p.m.",
  {"evening", "advanced", "language"}),
 ("Gentle Yoga",
  "A slow class for complete beginners and older students. "
  "Mornings only, Monday to Friday.",
  {"morning", "beginner", "fitness"}),
 ("Digital Photography",
  "Saturday and Sunday workshops for people who have just bought "
  "a camera. Equipment hire raises the price.",
  {"weekend", "beginner", "art", "expensive"}),
 ("Business English",
  "Intermediate students preparing for work abroad. Evenings, "
  "small groups, higher fee.",
  {"evening", "intermediate", "language", "expensive"}),
 ("Chess Club",
  "Meets every evening. Beginners welcome and there is no charge "
  "at all.",
  {"evening", "beginner", "free", "games"}),
 ("Cake Decorating",
  "Weekend sessions for absolute beginners. Bring your own cake.",
  {"weekend", "beginner", "cooking"}),
 ("Guitar for Adults",
  "Evening lessons for people who have never held a guitar. "
  "Very reasonable rates.",
  {"evening", "beginner", "music", "cheap"}),
], [
 ("Rustam works in an office all day and has never made anything "
  "with clay. He does not have much money to spend.",
  {"evening", "beginner", "cheap", "art"}, 0),
 ("Nilufar already speaks Spanish well and wants to keep it up "
  "for her job. She is free after work.",
  {"evening", "advanced", "language"}, 1),
 ("Anvar has just retired. His mornings are free and he is "
  "looking for gentle exercise.",
  {"morning", "beginner", "fitness"}, 2),
 ("Dilnoza is busy all week but free at weekends. She has just "
  "bought her first camera.",
  {"weekend", "beginner", "art"}, 3),
 ("Sardor wants something to do in the evenings that costs him "
  "nothing at all.",
  {"evening", "free"}, 5),
]))

SETS.append(S(2, "Places to stay for a short trip", [
 ("Lakeside Cabins",
  "Simple wooden cabins by the water. Dogs welcome. No wifi and "
  "no restaurant.",
  {"quiet", "pets", "cheap", "nature"}),
 ("City Central Hotel",
  "Two minutes from the station, in the middle of the shops and "
  "theatres. Rooms are small and the street is noisy.",
  {"central", "transport", "shops"}),
 ("Riverbank Family Rooms",
  "Large rooms sleeping five, with a playground and an early "
  "children's supper.",
  {"family", "children", "large"}),
 ("The Old Rectory",
  "A very quiet country house for adults only. Excellent "
  "restaurant. Expensive.",
  {"quiet", "adults", "expensive", "food"}),
 ("Airport Lodge",
  "Free shuttle every twenty minutes, twenty-four-hour reception, "
  "rooms cleaned quickly between guests.",
  {"transport", "airport", "late"}),
 ("Hillside Hostel",
  "Shared rooms at the lowest price in the area. Kitchen for "
  "guests. No private rooms.",
  {"cheap", "shared", "nature"}),
 ("Harbour Apartments",
  "Self-catering flats with a full kitchen, sleeping four. "
  "Weekly bookings only.",
  {"family", "kitchen", "large", "weekly"}),
 ("Station Guest House",
  "Bed and breakfast opposite the station. Adults only, quiet "
  "after ten.",
  {"central", "transport", "adults", "quiet"}),
], [
 ("Bekzod is travelling with his dog and wants somewhere quiet "
  "and inexpensive in the countryside.",
  {"quiet", "pets", "cheap"}, 0),
 ("The Karimovs have three young children and want a big room "
  "and somewhere for the children to play.",
  {"family", "children", "large"}, 2),
 ("Malika and her husband want a peaceful weekend without "
  "children and are happy to pay for good food.",
  {"quiet", "adults", "expensive", "food"}, 3),
 ("Timur arrives on a late flight and needs a room near the "
  "airport with transport provided.",
  {"transport", "airport", "late"}, 4),
 ("Aziza wants the cheapest possible bed and does not mind "
  "sharing a room.",
  {"cheap", "shared"}, 5),
]))

SETS.append(S(3, "Part-time jobs for students", [
 ("Weekend Cafe Assistant",
  "Saturday and Sunday shifts only. No experience needed, "
  "training given. Tips shared.",
  {"weekend", "no_exp", "training"}),
 ("Night Shelf Stacker",
  "Ten p.m. to six a.m., Monday to Thursday. Higher rate for "
  "night work.",
  {"night", "weekday", "well_paid"}),
 ("Private Maths Tutor",
  "Must have a strong maths background. Hours arranged with the "
  "family. Excellent pay.",
  {"qualified", "flexible", "well_paid", "teaching"}),
 ("Dog Walker",
  "Two hours every weekday afternoon. Must like animals. Outdoor "
  "work in all weather.",
  {"weekday", "outdoor", "animals", "no_exp"}),
 ("Library Assistant",
  "Quiet indoor work shelving books. Weekday mornings. Suits "
  "someone who likes reading.",
  {"weekday", "indoor", "quiet", "no_exp"}),
 ("Festival Steward",
  "Three days in July only. Free entry to all concerts. Long "
  "hours on your feet.",
  {"summer", "outdoor", "short_term", "no_exp"}),
 ("Online English Helper",
  "Work from home at any hour. You need a good level of English "
  "and a quiet room.",
  {"home", "flexible", "teaching", "qualified"}),
 ("Hotel Breakfast Waiter",
  "Six a.m. to ten a.m., seven days a week. Uniform provided.",
  {"early", "daily", "no_exp"}),
], [
 ("Kamron studies all week and can only work at weekends. He has "
  "never had a job before.",
  {"weekend", "no_exp"}, 0),
 ("Sevara is very good at maths and wants the best pay she can "
  "get. She can choose her own hours.",
  {"qualified", "flexible", "well_paid"}, 2),
 ("Jasur wants to be outdoors every afternoon and loves animals. "
  "He has no work experience.",
  {"weekday", "outdoor", "animals", "no_exp"}, 3),
 ("Zilola prefers quiet indoor work and is free on weekday "
  "mornings.",
  {"weekday", "indoor", "quiet"}, 4),
 ("Otabek wants to work from home whenever he likes and has an "
  "excellent level of English.",
  {"home", "flexible", "qualified"}, 6),
]))

SETS.append(S(4, "Weekend day trips", [
 ("Mountain Walk",
  "A six-hour hike with a steep climb. Good boots essential. Not "
  "suitable for children.",
  {"active", "outdoor", "adults", "long"}),
 ("City Museum Tour",
  "Two hours indoors with a guide. Wheelchair access throughout. "
  "Free for students.",
  {"indoor", "short", "accessible", "free_students", "history"}),
 ("Farm Visit",
  "Children can feed the animals and ride the tractor. Picnic "
  "area. Half a day.",
  {"children", "outdoor", "animals", "short"}),
 ("Cave Expedition",
  "Underground, narrow passages, helmets provided. Minimum age "
  "sixteen. Full day.",
  {"active", "adults", "long", "adventure"}),
 ("River Cruise",
  "Three hours on the water with lunch served on board. Suitable "
  "for all ages. Not cheap.",
  {"relaxed", "family", "food", "expensive"}),
 ("Old Town Photo Walk",
  "A slow two-hour walk with a photographer. Bring any camera. "
  "Small groups.",
  {"outdoor", "short", "art", "relaxed"}),
 ("Castle and Gardens",
  "Indoor rooms and large gardens. Cafe on site. Free entry for "
  "students with a card.",
  {"indoor", "outdoor", "history", "free_students", "food"}),
 ("Cycling Route",
  "Forty kilometres on flat paths. Bikes for hire. Children over "
  "ten welcome.",
  {"active", "outdoor", "children", "long"}),
], [
 ("Farrukh wants a hard day outdoors without children and is a "
  "strong walker.",
  {"active", "outdoor", "adults", "long"}, 0),
 ("Gulnora has a wheelchair and only two hours free. She is a "
  "student and would like to pay nothing.",
  {"indoor", "short", "accessible", "free_students"}, 1),
 ("The Yusupovs have two small children who love animals and want "
  "a short trip outdoors.",
  {"children", "outdoor", "animals", "short"}, 2),
 ("Nodira wants a relaxed day with her family and lunch included, "
  "and does not mind the cost.",
  {"relaxed", "family", "food", "expensive"}, 4),
 ("Shahzod likes taking pictures and wants a short, gentle walk "
  "outdoors.",
  {"outdoor", "short", "art", "relaxed"}, 5),
]))

SETS.append(S(5, "Books for a reading group", [
 ("Winter Road",
  "A long historical novel of nine hundred pages, set in the "
  "nineteenth century.",
  {"long", "history", "novel", "serious"}),
 ("Small Hours",
  "A short collection of funny stories, each about ten pages. "
  "Easy to read in one sitting.",
  {"short", "funny", "stories", "easy"}),
 ("The Glass Coast",
  "A modern novel about a family holiday that goes wrong. Two "
  "hundred pages, simple language.",
  {"short", "novel", "easy", "modern"}),
 ("Ways of Seeing Water",
  "Poetry about rivers and the sea. Difficult but rewarding. "
  "Sixty pages.",
  {"short", "poetry", "difficult"}),
 ("The Long Silence",
  "A true account of a scientific expedition, with maps and "
  "photographs. Six hundred pages.",
  {"long", "true", "science", "serious"}),
 ("Nine Kitchens",
  "Recipes and memories from nine countries. Beautifully "
  "illustrated. Can be read in any order.",
  {"food", "true", "illustrated", "easy"}),
 ("The Iron Bridge",
  "A detective story set in a small town. Three hundred pages, "
  "very fast moving.",
  {"novel", "crime", "modern", "easy"}),
 ("Letters Home",
  "Real letters written by soldiers, with historical notes. "
  "Serious and often sad.",
  {"true", "history", "serious", "short"}),
], [
 ("Umid has plenty of time and enjoys serious historical "
  "fiction.",
  {"long", "history", "novel", "serious"}, 0),
 ("Kamola is very busy and wants something short and funny that "
  "she can finish quickly.",
  {"short", "funny", "easy"}, 1),
 ("Sherzod likes a challenge and prefers poetry to prose.",
  {"poetry", "difficult"}, 3),
 ("Feruza prefers true stories about science and does not mind a "
  "long book.",
  {"long", "true", "science"}, 4),
 ("Aziz wants a modern crime novel that moves quickly and is not "
  "hard work.",
  {"novel", "crime", "modern", "easy"}, 6),
]))

SETS.append(S(6, "Language courses abroad", [
 ("Summer in Valencia",
  "Four weeks in July for beginners. Host family included. Very "
  "affordable.",
  {"summer", "beginner", "family_stay", "cheap", "spanish"}),
 ("Business German, Berlin",
  "Two weeks for advanced speakers preparing for work. Hotel "
  "accommodation. High fee.",
  {"advanced", "hotel", "expensive", "german", "business"}),
 ("Online French Intensive",
  "Study from home, three hours a day for a month. Any level. "
  "Low cost.",
  {"online", "any_level", "cheap", "french"}),
 ("Japanese in Kyoto",
  "Twelve weeks for serious learners, all levels. Shared student "
  "flat. Payment in instalments.",
  {"long", "any_level", "shared", "japanese", "instalments"}),
 ("Weekend Italian, Rome",
  "Three days for complete beginners who want the basics before a "
  "holiday. Hotel not included.",
  {"short", "beginner", "italian"}),
 ("Arabic for Travellers",
  "Evening classes in your own city, once a week for ten weeks. "
  "Beginners only.",
  {"home_city", "beginner", "evening", "arabic"}),
 ("Advanced English, Dublin",
  "Six weeks for students preparing for university. Host family "
  "or residence. Exam included.",
  {"advanced", "family_stay", "english", "exam", "long"}),
 ("Chinese Culture and Language",
  "Two weeks combining lessons with cooking and calligraphy. "
  "Beginners welcome. Hotel included.",
  {"short", "beginner", "hotel", "chinese", "culture"}),
], [
 ("Muhammad wants a cheap summer course in Spanish for beginners "
  "and would like to live with a family.",
  {"summer", "beginner", "family_stay", "cheap", "spanish"}, 0),
 ("Laylo already speaks German well and needs it for work. Her "
  "company will pay.",
  {"advanced", "expensive", "german", "business"}, 1),
 ("Behruz cannot travel and wants a cheap French course he can do "
  "from home.",
  {"online", "cheap", "french"}, 2),
 ("Madina wants a long course in Japan and cannot pay everything "
  "at once.",
  {"long", "japanese", "instalments"}, 3),
 ("Doston is preparing for university in English and needs a "
  "course that ends with an exam.",
  {"advanced", "english", "exam"}, 6),
]))

SETS.append(S(7, "Sports clubs in the town", [
 ("Dawn Swimmers",
  "Meets at the outdoor pool at six a.m. every day. Cold water, "
  "experienced swimmers only.",
  {"early", "daily", "outdoor", "experienced", "swim"}),
 ("Family Badminton",
  "Sunday afternoons in the sports hall. Rackets provided. All "
  "ages and levels.",
  {"weekend", "indoor", "family", "beginner", "racket"}),
 ("Town Running Club",
  "Two evening runs a week plus a long run on Saturday. Suits "
  "people training for a race.",
  {"evening", "weekend", "outdoor", "experienced", "run"}),
 ("Walking Football",
  "Slow-paced football for players over fifty. Wednesday "
  "mornings, indoor.",
  {"morning", "indoor", "older", "gentle", "football"}),
 ("Climbing Wall",
  "Open every evening. Instructors on hand for complete "
  "beginners. Membership required.",
  {"evening", "indoor", "beginner", "climb", "membership"}),
 ("Table Tennis Social",
  "Thursday evenings, free to attend, no coaching. Bring your own "
  "bat if you have one.",
  {"evening", "indoor", "free", "racket", "social"}),
 ("Junior Athletics",
  "Saturday mornings for children aged eight to fourteen. "
  "Qualified coaches.",
  {"weekend", "morning", "children", "outdoor", "run"}),
 ("Aqua Fitness",
  "Gentle exercise in warm water. Tuesday and Friday mornings. "
  "Popular with older members.",
  {"morning", "indoor", "older", "gentle", "swim"}),
], [
 ("Ravshan is a strong swimmer who likes cold water and gets up "
  "very early every day.",
  {"early", "daily", "outdoor", "experienced", "swim"}, 0),
 ("The Ergashevs want an indoor activity they can all do together "
  "at the weekend, including the children.",
  {"weekend", "indoor", "family", "beginner"}, 1),
 ("Iroda is training for a race and can run on weekday evenings "
  "and Saturdays.",
  {"evening", "weekend", "outdoor", "experienced", "run"}, 2),
 ("Bahodir is sixty-two and wants gentle indoor exercise in the "
  "morning, but he does not swim.",
  {"morning", "indoor", "older", "gentle", "football"}, 3),
 ("Nigora wants to try climbing in the evenings and has never "
  "done it before.",
  {"evening", "beginner", "climb"}, 4),
]))

SETS.append(S(8, "Volunteer opportunities", [
 ("Hospital Visitor",
  "Sit and talk with patients who have no family nearby. Two "
  "hours a week. Training and a check required.",
  {"people", "weekly", "training", "check", "indoor"}),
 ("Beach Clean",
  "One Saturday a month. Gloves and bags provided. No commitment "
  "beyond the day.",
  {"outdoor", "monthly", "no_commit", "environment"}),
 ("Reading Buddy",
  "Listen to a child read for thirty minutes after school, twice "
  "a week. Check required.",
  {"children", "weekly", "check", "indoor", "teaching"}),
 ("Charity Shop Sorting",
  "Sort donated clothes in the back room. Any weekday, as many "
  "hours as you like. No contact with customers.",
  {"indoor", "flexible", "alone", "no_commit"}),
 ("Community Garden",
  "Dig, plant and water. Tuesday and Thursday mornings. Tools "
  "provided, no experience needed.",
  {"outdoor", "morning", "environment", "no_exp"}),
 ("Telephone Befriender",
  "Call an older person from your own home once a week. Training "
  "given, no travel.",
  {"home", "people", "weekly", "training", "older"}),
 ("Museum Guide",
  "Show visitors round at weekends. You must learn the script and "
  "commit for a year.",
  {"weekend", "people", "commit", "history"}),
 ("Food Bank Driver",
  "Collect and deliver on Friday afternoons. Own car and clean "
  "licence essential.",
  {"driving", "weekly", "car", "outdoor"}),
], [
 ("Zafar wants to help people face to face, can give two hours a "
  "week, and is willing to be checked and trained.",
  {"people", "weekly", "training", "check"}, 0),
 ("Guzal can only help once a month, outdoors, and does not want "
  "to promise anything long-term.",
  {"outdoor", "monthly", "no_commit"}, 1),
 ("Shohrux wants to work quietly on his own, indoors, whenever he "
  "has time.",
  {"indoor", "flexible", "alone"}, 3),
 ("Dilorom cannot leave the house but would like to help older "
  "people once a week.",
  {"home", "people", "weekly", "older"}, 5),
 ("Alisher has a car and a clean licence and is free on Friday "
  "afternoons.",
  {"driving", "car", "weekly"}, 7),
]))

SETS.append(S(9, "Music lessons", [
 ("Violin, Classical",
  "One-to-one lessons for children aged six and over. Exams "
  "prepared. Instrument hire available.",
  {"children", "one_to_one", "classical", "exam", "hire"}),
 ("Adult Piano, Beginners",
  "Evening lessons for adults who have never played. No exams, "
  "just enjoyment.",
  {"adults", "evening", "beginner", "no_exam", "piano"}),
 ("Rock Band Workshop",
  "Play in a group from the first week. Teenagers only. Saturday "
  "afternoons.",
  {"teens", "group", "weekend", "modern"}),
 ("Singing for Everyone",
  "A large choir that anyone can join. No audition, no reading "
  "music. Thursday evenings.",
  {"adults", "group", "evening", "beginner", "no_audition"}),
 ("Jazz Guitar, Advanced",
  "For players who can already read chord charts. Weekday "
  "afternoons, high fee.",
  {"advanced", "modern", "expensive", "afternoon"}),
 ("Drum Lessons",
  "Half-hour lessons after school for children of any level. "
  "Sticks provided, drums at the studio.",
  {"children", "one_to_one", "afternoon", "modern", "hire"}),
 ("Music Theory Online",
  "Study grades one to five from home at your own pace. Suits "
  "students preparing for exams.",
  {"online", "exam", "flexible", "theory"}),
 ("Family Ukulele",
  "Parents and children learn together on Sunday mornings. "
  "Instruments lent free.",
  {"family", "group", "weekend", "beginner", "hire"}),
], [
 ("Sanjar's daughter is seven and he wants private classical "
  "lessons with exams. He does not own a violin.",
  {"children", "one_to_one", "classical", "exam", "hire"}, 0),
 ("Nasiba is forty and has never played the piano. She wants to "
  "learn in the evenings without taking exams.",
  {"adults", "evening", "beginner", "no_exam", "piano"}, 1),
 ("Jahongir is fifteen and wants to play modern music in a group "
  "at the weekend.",
  {"teens", "group", "weekend", "modern"}, 2),
 ("Oybek can already read chord charts and wants advanced jazz "
  "lessons. Cost is not a problem.",
  {"advanced", "modern", "expensive"}, 4),
 ("Zebo is preparing for a theory exam and needs to study from "
  "home at her own speed.",
  {"online", "exam", "flexible"}, 6),
]))

SETS.append(S(10, "Restaurants in the old town", [
 ("The Green Table",
  "Entirely vegetarian menu. Small dining room, booking "
  "essential. Moderate prices.",
  {"vegetarian", "small", "booking", "moderate"}),
 ("Harbour Grill",
  "Fresh fish landed the same morning. Large terrace over the "
  "water. Expensive.",
  {"fish", "terrace", "expensive", "large"}),
 ("Nur Kebab",
  "Open until three in the morning. Takeaway or eat in. Cheapest "
  "in the district.",
  {"late", "cheap", "takeaway", "meat"}),
 ("Casa Nonna",
  "Family-run Italian with a children's menu, high chairs and a "
  "play corner. Good value.",
  {"family", "children", "moderate", "italian"}),
 ("The Reading Room",
  "Quiet cafe with newspapers and free wifi. Light lunches only, "
  "no evening service.",
  {"quiet", "wifi", "light", "day_only"}),
 ("Silk Road Buffet",
  "Eat as much as you like for one price. Vegetarian and meat "
  "dishes. Very busy and noisy.",
  {"buffet", "vegetarian", "meat", "cheap", "noisy"}),
 ("Chez Marc",
  "Set menu of five courses, one sitting at eight o'clock. Adults "
  "only. Very expensive.",
  {"set_menu", "adults", "expensive", "evening"}),
 ("Corner Bakery",
  "Bread, pastries and coffee from six in the morning. Nowhere to "
  "sit down.",
  {"early", "takeaway", "cheap", "light"}),
], [
 ("Sabina eats no meat and wants a quiet dinner at a fair price. "
  "She is happy to book ahead.",
  {"vegetarian", "small", "booking", "moderate"}, 0),
 ("Rustam wants the best fresh fish and a table outside, and does "
  "not mind paying.",
  {"fish", "terrace", "expensive"}, 1),
 ("Aziz finishes work at two in the morning and wants something "
  "cheap to take away.",
  {"late", "cheap", "takeaway"}, 2),
 ("The Nazarovs have two small children and need somewhere with "
  "a children's menu that is not expensive.",
  {"family", "children", "moderate"}, 3),
 ("Kamola wants a quiet place to work in the daytime with free "
  "internet and a light meal.",
  {"quiet", "wifi", "light", "day_only"}, 4),
]))

SETS.append(S(11, "Evening entertainment", [
 ("Open Mic Night",
  "Anyone can perform for five minutes. Free entry. Tuesdays from "
  "eight.",
  {"free", "participate", "weekday", "music"}),
 ("Symphony Concert",
  "Full orchestra, formal dress usual. Saturday at seven thirty. "
  "Tickets from thirty pounds.",
  {"weekend", "classical", "expensive", "formal"}),
 ("Comedy Cellar",
  "Four comedians a night, strong language. Over eighteens only. "
  "Friday and Saturday.",
  {"weekend", "adults", "funny", "moderate"}),
 ("Outdoor Film",
  "A classic film shown on the wall of the castle. Bring a "
  "blanket. Cancelled if wet. Free.",
  {"free", "outdoor", "film", "weather"}),
 ("Quiz Night",
  "Teams of up to six. Two pounds each, prize for the winners. "
  "Wednesdays.",
  {"cheap", "participate", "weekday", "team"}),
 ("Ballet",
  "A touring company performs for three nights only. Children "
  "welcome from age five. Tickets are not cheap.",
  {"classical", "children", "expensive", "dance"}),
 ("Board Game Cafe",
  "Two hundred games to borrow. Open every evening. Small charge "
  "per table, food available.",
  {"cheap", "participate", "daily", "food", "games"}),
 ("Jazz in the Cellar",
  "Live trio every Thursday. No entry charge but drinks are "
  "expensive. Small room, arrive early.",
  {"free", "music", "weekday", "small"}),
], [
 ("Farhod plays the guitar and wants to perform in front of an "
  "audience on a weekday without paying.",
  {"free", "participate", "weekday", "music"}, 0),
 ("Nargiza loves orchestral music and is happy to dress up and "
  "pay for a good seat at the weekend.",
  {"weekend", "classical", "expensive", "formal"}, 1),
 ("Sardor and his friends want to laugh at the weekend and are "
  "all over twenty.",
  {"weekend", "adults", "funny"}, 2),
 ("Malika wants a free evening out in the open air and does not "
  "mind if it is cancelled.",
  {"free", "outdoor", "weather"}, 3),
 ("Six colleagues want a cheap midweek activity they can do as a "
  "team.",
  {"cheap", "participate", "weekday", "team"}, 4),
]))

SETS.append(S(12, "Flats to rent", [
 ("Studio, Central",
  "One room with a kitchen corner. Above a busy road. Bills "
  "included. Available now.",
  {"small", "central", "bills", "now", "noisy"}),
 ("Two-Bed Garden Flat",
  "Ground floor with a private garden. Pets allowed. Twelve-month "
  "contract.",
  {"large", "garden", "pets", "long_let"}),
 ("Room in Shared House",
  "One room in a house with four students. Cheapest option. "
  "Kitchen shared.",
  {"small", "shared", "cheap", "students"}),
 ("Furnished One-Bed",
  "Everything provided down to the plates. Six-month contract. "
  "No pets, no smoking.",
  {"furnished", "short_let", "no_pets"}),
 ("Family House, Suburbs",
  "Three bedrooms, garden, near two schools. Long contract "
  "preferred. Car needed.",
  {"large", "garden", "schools", "long_let", "car"}),
 ("Loft Apartment",
  "Open plan, top floor, wonderful views. No lift and eighty "
  "stairs. Expensive.",
  {"large", "expensive", "stairs", "central"}),
 ("Quiet Bedsit",
  "One room at the back of a house on a residential street. "
  "Bills extra. Available in three months.",
  {"small", "quiet", "later"}),
 ("Riverside Two-Bed",
  "Fully furnished with a balcony over the water. Short lets "
  "welcome. Pets by arrangement.",
  {"furnished", "large", "short_let", "pets", "expensive"}),
], [
 ("Otabek needs somewhere immediately, wants to pay one price "
  "including bills, and does not mind traffic noise.",
  {"central", "bills", "now"}, 0),
 ("The Sultonovs have a dog and want a garden. They are happy to "
  "sign for a year.",
  {"garden", "pets", "long_let"}, 1),
 ("Zarina is a student looking for the cheapest room and does not "
  "mind sharing a kitchen.",
  {"shared", "cheap", "students"}, 2),
 ("Ulugbek is here for six months only and does not want to buy "
  "any furniture. He has no pets.",
  {"furnished", "short_let", "no_pets"}, 3),
 ("The Rahimovs have three children, a car, and want to be near "
  "schools with a garden.",
  {"garden", "schools", "car"}, 4),
]))

SETS.append(S(13, "Computer courses", [
 ("Spreadsheets for Work",
  "Two days on formulas and charts. You must already use a "
  "computer confidently. Employer discount.",
  {"short", "intermediate", "office", "work"}),
 ("First Steps Online",
  "For people who have never used the internet. Very slow pace, "
  "one afternoon a week for ten weeks.",
  {"beginner", "afternoon", "slow", "internet"}),
 ("Python for Absolute Beginners",
  "Twelve evening sessions. No previous coding. Laptop provided "
  "in class.",
  {"beginner", "evening", "coding", "equipment"}),
 ("Photo Editing Weekend",
  "Saturday and Sunday. Bring your own laptop and photographs. "
  "Some experience assumed.",
  {"weekend", "intermediate", "design", "own_kit"}),
 ("Data Analysis, Advanced",
  "For programmers who already know Python. Four weeks, evenings, "
  "high fee.",
  {"advanced", "evening", "coding", "expensive"}),
 ("Online Safety for Parents",
  "One free evening session on keeping children safe online. No "
  "technical knowledge needed.",
  {"beginner", "evening", "free", "internet", "parents"}),
 ("Touch Typing",
  "Learn to type without looking. Practise at home at any time, "
  "twenty minutes a day.",
  {"home", "flexible", "beginner", "typing"}),
 ("Web Design Basics",
  "Six Saturday mornings building your own site. Beginners "
  "welcome, computers provided.",
  {"weekend", "beginner", "design", "equipment"}),
], [
 ("Nodir uses a computer every day at work and needs two days of "
  "spreadsheet training for his job.",
  {"short", "intermediate", "office", "work"}, 0),
 ("Halima has never been online and wants a very slow course in "
  "the afternoons.",
  {"beginner", "afternoon", "slow", "internet"}, 1),
 ("Aslon wants to learn to code in the evenings but has no laptop "
  "of his own.",
  {"beginner", "evening", "coding", "equipment"}, 2),
 ("Dilshod already programmes in Python and wants an advanced "
  "evening course. His firm will pay.",
  {"advanced", "evening", "coding", "expensive"}, 4),
 ("Munisa wants to learn to type properly at home whenever she "
  "has a spare moment.",
  {"home", "flexible", "beginner"}, 6),
]))

SETS.append(S(14, "Holiday activities for children", [
 ("Football Camp",
  "Full days for ages eight to twelve. Outdoor pitches. Lunch not "
  "provided.",
  {"full_day", "older_kids", "outdoor", "sport"}),
 ("Little Explorers",
  "Mornings only, ages three to five, parent must stay. Indoor "
  "play and songs.",
  {"morning", "young_kids", "parent", "indoor", "age3_5"}),
 ("Art Week",
  "Five afternoons of painting and printing for ages seven to "
  "eleven. All materials included.",
  {"afternoon", "older_kids", "indoor", "art", "materials"}),
 ("Swim Intensive",
  "Half an hour every morning for a week. Non-swimmers aged five "
  "and over. Small groups.",
  {"morning", "older_kids", "swim", "beginner"}),
 ("Forest School",
  "Whole days outdoors in all weather, ages six to ten. Hot lunch "
  "included. Waterproofs essential.",
  {"full_day", "older_kids", "outdoor", "lunch", "nature"}),
 ("Toddler Music",
  "Forty minutes of songs and instruments for under-threes with a "
  "parent. Tuesday mornings.",
  {"morning", "young_kids", "parent", "music", "indoor"}),
 ("Coding Club",
  "Ages nine to fourteen, afternoons, computers provided. No "
  "experience needed.",
  {"afternoon", "older_kids", "indoor", "coding", "materials"}),
 ("Drama Workshop",
  "A week of rehearsals ending in a performance for families. "
  "Ages ten to sixteen, full days.",
  {"full_day", "teens", "indoor", "drama"}),
], [
 ("Sherzod's son is ten, loves football and needs somewhere to be "
  "all day outdoors.",
  {"full_day", "older_kids", "outdoor", "sport"}, 0),
 ("Nilufar's daughter is four. Nilufar wants a morning activity "
  "indoors that she can attend with her.",
  {"morning", "young_kids", "parent", "indoor", "age3_5"}, 1),
 ("Kamron's daughter is nine and loves painting. Afternoons suit "
  "the family and they do not want to buy materials.",
  {"afternoon", "older_kids", "indoor", "art", "materials"}, 2),
 ("Aziza's son is six, cannot swim, and mornings are free.",
  {"morning", "older_kids", "swim", "beginner"}, 3),
 ("The Toshevs want their eight-year-old outdoors all day with a "
  "hot lunch provided.",
  {"full_day", "older_kids", "outdoor", "lunch"}, 4),
]))

SETS.append(S(15, "Getting to the airport", [
 ("Express Train",
  "Every fifteen minutes, journey of twenty-two minutes. Most "
  "expensive option. No luggage limit.",
  {"fast", "frequent", "expensive", "luggage"}),
 ("Night Bus",
  "Runs once an hour through the night when nothing else "
  "operates. Slow but very cheap.",
  {"night", "cheap", "slow"}),
 ("Shared Minibus",
  "Picks you up at your door. Must be booked a day ahead. "
  "Moderate price, seats six.",
  {"door", "booking", "moderate", "group"}),
 ("Taxi",
  "Available at any hour without booking. Most expensive per "
  "person if travelling alone.",
  {"door", "anytime", "expensive", "no_booking"}),
 ("Underground",
  "Cheap and frequent but involves two changes and many stairs. "
  "Not suitable with heavy bags.",
  {"cheap", "frequent", "stairs", "changes"}),
 ("Long-stay Car Park",
  "Drive yourself and leave the car. Free bus to the terminal "
  "every ten minutes. Cheaper the longer you stay.",
  {"car", "self", "long_trip"}),
 ("Coach",
  "Direct from the city centre, once an hour, luggage included in "
  "the fare. Takes fifty minutes.",
  {"slow", "cheap", "luggage", "direct"}),
 ("Bicycle Route",
  "A traffic-free path all the way, secure storage at the "
  "terminal. Free but forty minutes of effort.",
  {"free", "active", "slow", "direct"}),
], [
 ("Bekzod is late and needs the fastest way, whatever it costs. "
  "He has two large suitcases.",
  {"fast", "expensive", "luggage"}, 0),
 ("Sitora's flight leaves at four in the morning and she has very "
  "little money.",
  {"night", "cheap"}, 1),
 ("The Yuldashevs are six people who want to be collected from "
  "their house and can book in advance.",
  {"door", "booking", "group"}, 2),
 ("Farrukh is driving and will be away for two weeks.",
  {"car", "self", "long_trip"}, 5),
 ("Gulchehra wants a cheap direct journey with her luggage "
  "included and does not mind if it is slow.",
  {"slow", "cheap", "luggage", "direct"}, 6),
]))

SETS.append(S(16, "Gifts for different people", [
 ("Star Map",
  "A printed chart of the night sky on any chosen date. Framed. "
  "Delivered in three days.",
  {"personal", "keepsake", "quick", "moderate"}),
 ("Cookery Class Voucher",
  "A day learning to make bread. Valid for a year. Not cheap but "
  "unforgettable.",
  {"experience", "food", "expensive", "long_valid"}),
 ("Plant Subscription",
  "A new houseplant every month for six months. Care notes "
  "included.",
  {"repeat", "plants", "moderate", "practical"}),
 ("Handmade Notebook",
  "Leather cover, blank pages. Can be stamped with initials. "
  "Ready the same day.",
  {"personal", "keepsake", "quick", "cheap", "writing"}),
 ("Concert Tickets",
  "Two seats at a live performance next month. Choose from twenty "
  "shows. Expensive.",
  {"experience", "music", "expensive", "pair"}),
 ("Wool Blanket",
  "Warm, heavy and made locally. Delivery takes four weeks "
  "because each one is woven to order.",
  {"keepsake", "practical", "slow", "expensive"}),
 ("Coffee of the Month",
  "Fresh beans posted every four weeks for a year. Different "
  "country each time.",
  {"repeat", "food", "long_valid", "moderate"}),
 ("Photo Calendar",
  "Your own pictures printed for the coming year. Cheap and made "
  "in two days.",
  {"personal", "quick", "cheap", "practical"}),
], [
 ("Sardor wants something personal and lasting for his wife's "
  "birthday next week, at a fair price.",
  {"personal", "keepsake", "quick", "moderate"}, 0),
 ("Zilola wants to give her brother an experience with food "
  "rather than an object, and is happy to spend a lot.",
  {"experience", "food", "expensive"}, 1),
 ("Aziz wants a present that keeps arriving for months and is "
  "useful around the house.",
  {"repeat", "plants", "practical"}, 2),
 ("Malika needs something personal today and cannot spend much. "
  "Her friend loves writing.",
  {"personal", "quick", "cheap", "writing"}, 3),
 ("Bekzod wants two tickets to live music and money is no "
  "object.",
  {"experience", "music", "expensive", "pair"}, 4),
]))

SETS.append(S(17, "Local newspapers and magazines", [
 ("The Valley Weekly",
  "Local news, sport and council reports. Delivered free to every "
  "house on Thursdays.",
  {"free", "weekly", "local_news", "paper"}),
 ("Green Living",
  "Monthly magazine on gardening and the environment. Subscription "
  "only, no advertising.",
  {"monthly", "environment", "no_ads", "subscription"}),
 ("City Business Daily",
  "Company news and share prices every weekday morning. Digital "
  "only. Expensive.",
  {"daily", "business", "digital", "expensive"}),
 ("What's On",
  "A listings paper of concerts, films and markets. Picked up "
  "free in cafes each fortnight.",
  {"free", "listings", "paper", "fortnightly"}),
 ("Young Voices",
  "Written by teenagers for teenagers. Term-time only, sold in "
  "schools for a small sum.",
  {"teens", "cheap", "termly", "paper"}),
 ("The Long Read",
  "One serious article a week, sent by email. Free, no "
  "advertising, takes an hour to read.",
  {"free", "weekly", "digital", "no_ads", "serious"}),
 ("Country Homes",
  "Glossy monthly about houses and interiors. Sold in shops, full "
  "of advertising.",
  {"monthly", "design", "shops", "ads"}),
 ("Sport Extra",
  "Match reports and results every Monday. Digital or paper. "
  "Moderate price.",
  {"weekly", "sport", "digital", "paper", "moderate"}),
], [
 ("Ravshan wants free local news delivered to his door once a "
  "week on paper.",
  {"free", "weekly", "local_news", "paper"}, 0),
 ("Nargiza gardens and hates advertising. She is happy to pay "
  "monthly.",
  {"monthly", "environment", "no_ads", "subscription"}, 1),
 ("Otabek follows share prices and needs something every working "
  "day on his phone.",
  {"daily", "business", "digital"}, 2),
 ("Dilnoza wants to know what is on locally and does not want to "
  "pay anything.",
  {"free", "listings", "paper"}, 3),
 ("Jasur wants one serious free article a week by email with no "
  "advertising.",
  {"free", "weekly", "digital", "no_ads", "serious"}, 5),
]))

SETS.append(S(18, "Ways to learn to drive", [
 ("Intensive Week",
  "Thirty hours in five days, test booked at the end. Suits "
  "people in a hurry. Large payment in advance.",
  {"fast", "test", "expensive", "upfront"}),
 ("Weekly Lessons",
  "One hour every Saturday with the same instructor. Pay as you "
  "go. Takes several months.",
  {"slow", "weekend", "pay_as_go", "same_teacher"}),
 ("Automatic Only",
  "For learners who do not want to use gears. Weekday afternoons. "
  "Test in an automatic car.",
  {"automatic", "afternoon", "test"}),
 ("Motorway Confidence",
  "For drivers who already hold a licence but avoid fast roads. "
  "Two sessions.",
  {"licensed", "short", "confidence", "motorway"}),
 ("Theory Only",
  "Online lessons for the written test. Study at any hour. Very "
  "low cost.",
  {"online", "flexible", "cheap", "theory"}),
 ("Female Instructor",
  "Lessons with a woman instructor, weekday mornings, in a small "
  "car. Pay by the lesson.",
  {"morning", "pay_as_go", "female", "small_car"}),
 ("Refresher Course",
  "For people who passed years ago and have not driven since. "
  "Three evening sessions.",
  {"licensed", "evening", "confidence", "short"}),
 ("Village Lessons",
  "Quiet country roads for very nervous beginners. Any day, any "
  "time, at your own pace.",
  {"flexible", "nervous", "quiet_roads", "pay_as_go"}),
], [
 ("Anvar starts a job in a month and needs to pass quickly. He "
  "can pay the whole amount now.",
  {"fast", "test", "expensive", "upfront"}, 0),
 ("Kamola can only learn on Saturdays and wants the same "
  "instructor each time, paying week by week.",
  {"slow", "weekend", "pay_as_go", "same_teacher"}, 1),
 ("Sherzod does not want to bother with gears and is free on "
  "weekday afternoons.",
  {"automatic", "afternoon"}, 2),
 ("Zebo already has a licence but is frightened of motorways.",
  {"licensed", "short", "confidence", "motorway"}, 3),
 ("Timur wants to study only for the written test, online, as "
  "cheaply as possible.",
  {"online", "flexible", "cheap", "theory"}, 4),
]))

SETS.append(S(19, "Courses for people returning to study", [
 ("Access to Nursing",
  "One year full time, leads directly to a degree place. Free for "
  "those on benefits.",
  {"full_time", "year", "degree", "free_some", "health"}),
 ("Evening Accountancy",
  "Two evenings a week for two years while you keep working. Fees "
  "paid monthly.",
  {"evening", "part_time", "long", "monthly_pay", "business"}),
 ("Distance Learning History",
  "Study entirely from home with a tutor by email. Start any "
  "month. Assignments every six weeks.",
  {"home", "flexible", "start_any", "humanities"}),
 ("Return to Maths",
  "A ten-week refresher for adults who left school without a "
  "qualification. Free. Daytime.",
  {"short", "free", "daytime", "refresher", "maths"}),
 ("Weekend Law Certificate",
  "Ten Saturdays. Suits people in full-time work. High fee, paid "
  "in one instalment.",
  {"weekend", "short", "expensive", "upfront", "law"}),
 ("Childcare Level 2",
  "Daytime classes with a work placement in a nursery. Childcare "
  "provided for your own children.",
  {"daytime", "placement", "creche", "care"}),
 ("Open Degree",
  "Build your own degree over up to ten years. Study online, take "
  "breaks whenever you need.",
  {"home", "flexible", "degree", "breaks", "long"}),
 ("Summer Access Course",
  "Six weeks in July and August, full days, to prepare for "
  "university in September.",
  {"summer", "full_time", "short", "degree"}),
], [
 ("Rustam wants to become a nurse, can study full time for a "
  "year, and is on benefits.",
  {"full_time", "year", "degree", "free_some", "health"}, 0),
 ("Nilufar works all day and can only study two evenings a week. "
  "She wants to pay monthly.",
  {"evening", "part_time", "monthly_pay"}, 1),
 ("Aziz cannot attend anywhere and wants to start whenever he is "
  "ready, studying from home.",
  {"home", "flexible", "start_any"}, 2),
 ("Malika left school without maths and wants a free short "
  "daytime course.",
  {"short", "free", "daytime", "refresher"}, 3),
 ("Dilnoza has a small child and needs daytime classes with "
  "childcare and practical experience.",
  {"daytime", "placement", "creche"}, 5),
]))

SETS.append(S(20, "Second-hand items for sale", [
 ("Upright Piano",
  "Needs tuning but plays. Free to anyone who can collect it. "
  "Very heavy.",
  {"free", "collect", "heavy", "music"}),
 ("Child's Bicycle",
  "Suitable for ages five to eight. Small amount of rust. Cheap "
  "and easy to carry.",
  {"cheap", "children", "light", "sport"}),
 ("Dining Table and Six Chairs",
  "Solid oak, twenty years old, in good order. Delivery within "
  "the city can be arranged.",
  {"delivery", "large", "furniture", "moderate"}),
 ("Camping Set",
  "Tent, two sleeping bags and a stove. Used twice. Everything "
  "packs into one bag.",
  {"outdoor", "light", "moderate", "complete"}),
 ("Office Chair",
  "Adjustable, on wheels, one arm broken. Free if you take it "
  "away today.",
  {"free", "collect", "furniture", "damaged"}),
 ("Sewing Machine",
  "Electric, with instructions and spare needles. Works "
  "perfectly. Priced to sell.",
  {"cheap", "working", "craft", "light"}),
 ("Garden Shed",
  "Wooden, four metres by three. You must take it apart "
  "yourself. Free.",
  {"free", "collect", "heavy", "garden"}),
 ("Double Bed",
  "Frame and mattress, three years old. Delivery included in the "
  "price. No marks.",
  {"delivery", "large", "furniture", "expensive"}),
], [
 ("Sardor has a van and wants something musical for nothing, even "
  "if it is difficult to move.",
  {"free", "collect", "heavy", "music"}, 0),
 ("Zilola needs a cheap bicycle for her six-year-old and has only "
  "a small car.",
  {"cheap", "children", "light"}, 1),
 ("The Umarovs want a large solid table and need it delivered.",
  {"delivery", "large", "furniture", "moderate"}, 2),
 ("Bekzod wants everything he needs for camping in one light "
  "package and can pay a fair price.",
  {"outdoor", "light", "moderate", "complete"}, 3),
 ("Gulnora wants a cheap machine for sewing that works and is "
  "easy to carry home.",
  {"cheap", "working", "craft", "light"}, 5),
]))


def build_rows():
    """(kind, level, payload, answer, explain, alt, paraphrase)."""
    out = []
    for st in SETS:
        board = "\n\n".join(
            f"{LET[i]}. {t}\n{txt}"
            for i, (t, txt, _g) in enumerate(st["notices"]))
        for qi, (desc, need, idx) in enumerate(st["people"], 1):
            let = LET[idx]
            title = st["notices"][idx][0]
            expl = (f"To'g'ri javob: {let} — «{title}». Bu e'lon "
                    f"odamning HAMMA shartiga javob beradi; "
                    f"qolganlari kamida bittasiga javob bermaydi.")
            out.append((
                KIND, st["level"],
                {"title": st["topic"],
                 "passage": st["topic"] + "\n\n" + board,
                 "prompt": f"{qi}. {desc}",
                 "options": [f"{LET[i]}. {t}"
                             for i, (t, _x, _g) in
                             enumerate(st["notices"])],
                 "instruction": INSTR,
                 "step": st["level"],
                 "step_title": f"{st['level']}-daraja",
                 "order": qi},
                f"{let}. {title}", expl, None, None))
    return out


def seed_cefr_match(db):
    """Idempotent: bor bo'lsa qayta yozmaydi (hech narsa o'chmaydi)."""
    import json
    import models
    # 2026-09-13: TEKSHIRUV ISHLAMAGAN EDI. r.level bazada MATN ("1"),
    # build_rows() esa SON (1) beradi — ("1", 1) != (1, 1), shuning
    # uchun har sovuq startda 100 ta nusxa qayta yozilardi. Jonli bazada
    # shu 4 turdan 1,3 mln qator (2 GB) to'plangan edi. Ikkala tomon
    # ham matnga keltiriladi; bazadan faqat kerakli ustunlar o'qiladi.
    have = {
        (str(lv), json.loads(pl).get("order"))
        for lv, pl in db.query(models.PracticeItem.level,
                               models.PracticeItem.payload)
        .filter(models.PracticeItem.skill == SKILL,
                models.PracticeItem.kind == KIND).all()}
    n = 0
    for kind, level, payload, answer, explain, alt, para in build_rows():
        if (str(level), payload["order"]) in have:
            continue
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, alt=alt, explain=explain, is_active=1))
        n += 1
    if n:
        db.commit()
    return n
