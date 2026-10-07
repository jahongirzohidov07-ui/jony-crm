"""Author prerequisite-safe skills (1–30) and lessonPlan-aligned guidance (1–192).

Only writes the two named JSON files. Run --check for a read-only reproducibility
and content check. Do not run assemble-intensive afterwards: its separate source
packs are outside this change's scope and would overwrite the skills corrections.
"""
import argparse
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'src/data'


def read(name):
    return json.loads((DATA / name).read_text(encoding='utf-8'))


# Each passage has three deliberately constrained, evidence-based questions.
# Question instructions are Uzbek so an untaught English interrogative is not
# itself a prerequisite. English fragments are valid answers in these lessons.
EARLY = [
    (
        'My Teacher', 'Ali: student. Lola: teacher. A kind teacher. A happy student. A new book. A blue bag. Lola: happy. Ali: happy too!',
        [('O‘qituvchining ismi?', 'Lola'), ('Teacher oldidagi sifat?', 'kind'), ('Sumkaning rangi?', 'blue')],
        'The Welcome Badge', 'Mina: Hello! Mina. Student.\nLola: Hello! Lola. Teacher.\nMina: A happy student!\nLola: A kind teacher. A new friend!',
        [('O‘quvchining ismi?', 'Mina'), ('Student oldidagi sifat?', 'happy'), ('Teacher oldidagi sifat?', 'kind')],
        'Ot va sifatni ajratish', 'student / teacher / book — ot; kind / happy / new — sifat',
        'Juftingizga ism kartasini ko‘rsating. Student, teacher, friend kartalaridan ikkitasini, kind va happy sifatlarini ayting. Tayyor “Hello!” qolipi bilan salomlashing; gap tuzish shart emas.',
        'To‘rtta yorliq yozing: ikki ot, ikki sifat. Keyin namunadan ikki sifat + ot birikmasini ko‘chiring.',
        'student; teacher; kind; happy\na kind teacher\na happy student',
        'Ot narsa yoki odam nomi; sifat uning belgisidir. A kind teacher birikmasidagi a hozir tayyor qolip, artikl qoidasi emas.'
    ),
    (
        'The Slow Robot', 'Pip: robot. Sara: student. Pip → it. Sara → she. Action cards: read, walk. Manner cards: slowly, quietly. Pip: walk + slowly. Sara: read + quietly. A quiet robot club!',
        [('Pip o‘rnidagi olmosh?', 'it'), ('Sara o‘rnidagi olmosh?', 'she'), ('Walk yonidagi ravish?', 'slowly')],
        'Robot Radio', 'Robot cards! Ben: he. Mina: she. Robot: it. Read — quietly. Walk — slowly. Be — holat fe’li. A quiet robot, a happy friend!',
        [('Ben o‘rnidagi olmosh?', 'he'), ('Read yonidagi ravish?', 'quietly'), ('Holat fe’li sifatida berilgan so‘z?', 'be')],
        'Fe’l, olmosh va ravishni tanish', 'Pip → it; Sara → she; walk + slowly; read + quietly',
        'Ustoz ko‘rsatgan read/walk harakatini mimika qiling va so‘zni ayting. Pip hamda Sara kartalarini it/she bilan almashtiring; slowly/quietly ni tanlang. Yangi gap yoki -s shakli talab qilinmaydi.',
        'Ikki ism → olmosh juftligi va ikki fe’l + ravish juftligini kartalardan yozing.',
        'Pip → it\nSara → she\nwalk + slowly\nread + quietly',
        'Harakatni ko‘rsating, so‘ng uni qanday bajarishni sekin yoki jim namoyish qiling. Walk va slowly vazifasi boshqa; hozir fe’lni shaxsga moslab tuslamang.'
    ),
    (
        'Lunch Labels', 'Lunch cards: in the classroom; on the table; under the chair. Ali and Mina → they. You and I → we. Bread and cheese. Small but useful. A picnic in the classroom!',
        [('Lunch joyi: in the ...?', 'classroom'), ('Ali and Mina o‘rnidagi olmosh?', 'they'), ('Small va useful orasidagi so‘z?', 'but')],
        'The Picnic Map', 'A picnic map: in the park. A bag: under the tree. A cup: on the table. Lola and Ben: they. You and I: we. Tea and cake. Small but nice!',
        [('Sayr joyi: in the ...?', 'park'), ('Sumka: under the ...?', 'tree'), ('You and I o‘rnidagi olmosh?', 'we')],
        'Joy birikmasi, bog‘lovchi va ega olmoshini tanish', 'in the classroom / on the table; and / but; Ali and Mina → they',
        'Rasmdagi ikki joyni tayyor in/on/under birikmasi bilan ayting. Ikki ismga they kartasini, you and I ga we kartasini qo‘ying. Bread and cheese ni bir butun birikma qilib takrorlang.',
        'Rasmga ikkita joy yorlig‘i, bitta and birikmasi va bitta ism → olmosh juftligi yozing.',
        'on the table\nunder the chair\nbread and cheese\nAli and Mina → they',
        'Predlogni buyumni joyidan siljitib ko‘rsating. And qo‘shadi, but qarama-qarshilikni bog‘laydi. To‘liq gap yoki because bilan mustaqil sabab so‘ramang.'
    ),
    (
        'The Book Doctor', 'Nodir: the book doctor. Model cards: “Nodir repairs books.” Nodir = subject. Repairs = verb. Books = object. “He is kind.” He = subject. Is = verb. Kind = complement. A kind book doctor!',
        [('Birinchi modeldagi ega?', 'Nodir'), ('Birinchi modeldagi to‘ldiruvchi?', 'books'), ('Ikkinchi modeldagi tavsiflovchi qism?', 'kind')],
        'A Picture Helper', 'Two ready-made cards: “Mina draws cats.” Mina: subject. Draws: verb. Cats: object. “She is happy.” She: subject. Is: verb. Happy: complement. A happy picture helper!',
        [('Birinchi modeldagi fe’l?', 'draws'), ('Birinchi modeldagi to‘ldiruvchi?', 'cats'), ('Ikkinchi modeldagi complement?', 'happy')],
        'Tayyor gapda ega, fe’l, to‘ldiruvchi va complementni ajratish', 'Nodir | repairs | books; He | is | kind',
        'Tayyor ikki gapni ustoz ortidan o‘qing. So‘z kartalarini ega, fe’l, to‘ldiruvchi yoki complement deb ko‘rsating. Repairs/draws ni o‘zingiz yasamang.',
        'Namunadagi ikki gapni ko‘chiring va qismlariga ega / fe’l / to‘ldiruvchi / complement belgilarini qo‘ying.',
        'Nodir [ega] repairs [fe’l] books [to‘ldiruvchi].\nHe [ega] is [fe’l] kind [complement].',
        'Repairs books ma’nosini kitobni tuzatish mimikasi bilan bering. Butun gap tayyor tahlil materiali; -s va Present Simple ishlab chiqarish keyingi bosqichga qoladi.'
    ),
    (
        'A Dog with a Badge', 'Kamol and Rex: shop badges. Card A: “I am Kamol.” Card B: “I work.” Card C: “Rex is happy.” Correct order: I | am | Kamol. Capital: I. Full stop: . Rex: a very happy dog!',
        [('A kartadagi ism?', 'Kamol'), ('Harakat fe’li bor karta: A yoki B?', 'B'), ('Gap oxiridagi belgi nomi: full stop yoki comma?', 'full stop')],
        'The Name Card Mix-Up', 'Name cards: “I am Lola.” “I work.” “Ben is kind.” Lola: capital L. I: capital I. Ben: capital B. Ready-made word order: Ben, is, kind. Full stop!',
        [('Birinchi kartadagi ism?', 'Lola'), ('I work dagi harakat fe’li?', 'work'), ('Ben is kind dagi birinchi so‘z?', 'Ben')],
        'So‘z tartibi, be/harakat fe’li va yozuv belgilarini tanish', 'I | am | Kamol. / I | work. / Rex | is | happy.',
        'Berilgan gap kartalarini aynan namunadagi tartibda joylashtirib o‘qing. Be bor kartani va harakat fe’li bor kartani ajrating. I am work ni noto‘g‘ri namuna sifatida taning; yangi ish haqida gap talab qilinmaydi.',
        '“i am kamol”, “rex is happy” va “i work” kartalarini bosh harf va nuqta bilan ko‘chiring. Yangi fe’l qo‘shmang.',
        'I am Kamol.\nRex is happy.\nI work.',
        'So‘z tartibi uchun uchta karta ishlating. I work faqat berilgan butun namuna; unga am qo‘shilmasligini tanish yetarli. Fe’lni almashtirish yoki tuslashni baholamang.'
    ),
    (
        'Our Tiny Museum', 'Museum labels: a red cup; an old book; a happy team. Place: on the table. Ali and Mina → they. Ready-made model: “They read books.” They = subject; read = verb; books = object. Small but special!',
        [('Cup oldidagi sifat?', 'red'), ('Ali and Mina o‘rnidagi olmosh?', 'they'), ('Modeldagi to‘ldiruvchi?', 'books')],
        'A Museum in a Box', 'Box museum: a blue pen; a small hat. Place label: in the box. Ready-made card: “Mina is happy.” Mina: subject. Is: verb. Happy: complement. Blue and red. A tiny museum!',
        [('Pen rangi?', 'blue'), ('Joy yorlig‘i: in the ...?', 'box'), ('Modeldagi complement?', 'happy')],
        '1-hafta: so‘z turkumlari va tayyor gap qismlarini tanish', 'red → sifat; cup → ot; They | read | books; Mina | is | happy',
        'Muzeyga ikkita buyum yorlig‘i va bitta joy birikmasini ayting. Tayyor modeldagi ega va fe’lni ko‘rsating. Tanishingiz yetarli; muzey jamoasining yangi ishini gapda aytish shart emas.',
        'Uchta yorliq yozing; berilgan gapni ko‘chirib ega va fe’lni belgilang. So‘z turkumlari jadvaliga bittadan ot va sifat joylashtiring.',
        'a red cup\nan old book\non the table\nThey [ega] read [fe’l] books [to‘ldiruvchi].',
        'Nazoratda yorliq, so‘z tanlash va tayyor gapni belgilashni ajrating. Mustaqil tanish va ustoz yordami bilan topishni alohida qayd qiling; erkin Present Simple gap so‘ramang.'
    ),
    (
        'Before the Concert', 'I am Daler. I am happy. Mum is calm. Dad is not calm. He is nervous. We are ready. The cat is sleepy. The cat is not ready!',
        [('Kim nervous?', 'Dad'), ('Dalerning holati?', 'happy'), ('Mushukning holati?', 'sleepy')],
        'The Quiet Drum', 'Lola: I am ready.\nBen: I am not ready. I am nervous.\nLola: You are safe. We are together.\nBen: I am happy.\nLola: The drum is quiet. The cat is happy too!',
        [('Dastlab kim nervous?', 'Ben'), ('Drum holati?', 'quiet'), ('Oxirida Benning holati?', 'happy')],
        'Am/is/are bilan holat va inkorni aytish', 'I am happy. He is not calm. We are ready.',
        'Holat kartasini tanlang. O‘zingiz, bir kishi va jamoa haqida uch tasdiq, bitta inkor ayting. Bugun savol tuzish shart emas.',
        'Konsert kartasiga am/is/are bilan to‘rtta qisqa holat gapi yozing; bittasi not bilan bo‘lsin.',
        'I am happy. Lola is calm. We are ready. Ben is not ready.',
        'I bilan am, bitta odam bilan is, we bilan are ni ranglang. Not be dan keyin turadi. Savol shakli keyingi darsda.'
    ),
    (
        'The White Coat', 'Aziza is a doctor. She is not a teacher. Is she happy? Yes. Is Ben a doctor? No. He is a student. He is not sad. The white coat is big!',
        [('Azizaning kasbi?', 'doctor'), ('Ben kim?', 'student'), ('Oq xalat qanday?', 'big')],
        'A Guest with a Cake', 'Mina: Is he a teacher?\nLola: No. He is a cook.\nMina: Is he happy?\nLola: Yes. He is not tired.\nMina: The cake is big!\nLola: He is a happy cook.',
        [('Mehmonning kasbi?', 'cook'), ('U tiredmi? Yes/no.', 'no'), ('Tort qanday?', 'big')],
        'Be bilan kasb, holat va yes/no savollar', 'She is a doctor. She is not a teacher. Is she happy?',
        'Mehmon rolini o‘ynang. Kasb va holat haqida ikkitadan savol-javob qiling. Javobda Yes/No va tasdiq gap yetarli; qisqa yordamchi javob hali shart emas.',
        'Mehmon uchun ikki kasb gapi va bitta savol-javob yozing. A doctor/a teacher ni tayyor kasb qolipi sifatida oling.',
        'She is a doctor. She is not a teacher. Is she happy? Yes. She is happy.',
        'Savolda is ni ega oldiga siljiting. Kasb oldidagi a ni hozir butun birikmada bering. Yes, she is kabi qisqa javobni hali mezon qilmang.'
    ),
    (
        'A Small Hero', 'Bobo is a small dog. He is a brave dog. He is not a big dog. Is he a good friend? Yes. Rano is a kind student. Bobo is a happy hero!',
        [('Qahramon itning ismi?', 'Bobo'), ('Bobo big yoki small?', 'small'), ('Rano qanday student?', 'kind')],
        'The Paper Crown', 'Ben: Is Lola a kind teacher?\nMina: Yes. She is a kind teacher.\nBen: Is the crown a big crown?\nMina: No. It is a small crown.\nBen: A small crown, a happy teacher!',
        [('Kim kind teacher?', 'Lola'), ('Toj big yoki small?', 'small'), ('O‘qituvchining holati?', 'happy')],
        'Be + sifat + ot bilan tavsif va savol', 'He is a brave dog. He is not a big dog. Is he a good friend?',
        'It yoki o‘qituvchi uchun ikki sifat + ot tavsifi ayting. Sherigingiz bitta Is ...? savolini bersin; bitta noto‘g‘ri tavsifni not bilan tuzating.',
        'Qahramon kartasiga uch tavsif va bitta savol yozing. Sifat ot oldida bo‘lsin.',
        'Bobo is a brave dog. He is a good friend. He is not a big dog. Is he a happy dog?',
        'A brave dog bo‘laklarini birga saqlang; sifat ot oldida. Inkor butun tavsifga tegishli. Harakat haqidagi qahramonlik hikoyasi so‘ralmaydi.'
    ),
    (
        'The Wrong Room', 'The club is in room two. Ali is in room three. He is not in room two. Where is Lola? She is in room two. Are they at school? Yes. The sign is wrong!',
        [('Klub qaysi xonada?', 'room two|two|2'), ('Ali qaysi xonada?', 'room three|three|3'), ('Lola qaysi xonada?', 'room two|two|2')],
        'The Garden Classroom', 'Ben: Where are you?\nMina: I am in the garden.\nBen: Are you at school?\nMina: Yes. The class is in the garden.\nBen: The teacher is not in the classroom!\nMina: She is here, under the tree.',
        [('Mina qayerda?', 'in the garden|the garden|garden'), ('O‘qituvchi nima tagida?', 'under the tree|the tree|tree'), ('O‘qituvchi classroom ichidami? Yes/no.', 'no')],
        'Be bilan joy, inkor va where savolini ishlatish', 'The club is in room two. Where is Ali? He is not in room two.',
        'Ikki xona rasmini tanlang. Sherigingizga Where ...? va Are ...? savollarini bering. Bitta noto‘g‘ri joyni not bilan tuzating.',
        'Klubga to‘rtta satr xabar yozing: to‘g‘ri joy, noto‘g‘ri joy, where savoli va javobi.',
        'The club is in room two. It is not in room three. Where is Lola? She is in room two.',
        'Joy birikmasini tayyor bering. Where dan keyin be va ega keladi. Xonalar xaritasida o‘quvchi aytgan joyni ko‘rsatib ma’noni tekshiring.'
    ),
    (
        'An Unusual Desk', 'I’m Sara. I’m a student. Ben’s an English teacher. He’s here. Is he tired? No, he isn’t. We’re in class. A cat is there. Is it a teacher? No, it isn’t!',
        [('Sara kim?', 'student'), ('Benning kasbi?', 'English teacher|teacher'), ('U yerda qaysi hayvon?', 'cat|a cat')],
        'A Tiny Studio', 'Mina: Are you an artist?\nLola: Yes, I am. I’m an artist.\nMina: Is Ben here?\nLola: No, he isn’t. He’s there.\nMina: We’re in a tiny studio!\nLola: Yes, we are.',
        [('Lolaning kasbi?', 'artist|an artist'), ('Ben here yoki there?', 'there'), ('Xona nomi?', 'studio|a tiny studio|tiny studio')],
        'Qisqa javob, qisqartma va a/an ni qo‘llash', 'I’m = I am; an artist / a student; Yes, I am. No, he isn’t.',
        'Ma’lumot stolida ikki be savoli va qisqa javob bering. I’m/he’s bilan tanishtiring; here/there bilan joyni ko‘rsating.',
        'To‘rtta satr studio kartasi yozing: qisqartma, kasb, here/there va qisqa savol-javob.',
        'I’m an artist. Ben is a student. Is he here? No, he isn’t. He’s there.',
        'Yes, I am ni Yes, I’m ga qisqartirmang. An artist da boshlang‘ich unli tovushni eshittiring. He’s bu darsda he is ma’nosida.'
    ),
    (
        'The School Photo', 'We’re at school. Lola is a kind teacher. Ali is not here. Where is he? He’s in the garden. Is he ready? Yes, he is. The cat is ready too. It’s a very serious cat!',
        [('O‘qituvchining ismi?', 'Lola'), ('Ali qayerda?', 'in the garden|garden|the garden'), ('Mushuk qanday?', 'serious|a very serious cat')],
        'A New Neighbour', 'Ben: I’m a new student. Are you a teacher?\nMina: No, I’m not. I’m an artist.\nBen: Are you here for the photo?\nMina: Yes, I am.\nBen: Where is Lola?\nMina: She’s in class. She’s ready!',
        [('Ben kim?', 'student|a new student'), ('Mina kasbi?', 'artist|an artist'), ('Lola qayerda?', 'in class|class')],
        '2-hafta: be bilan kim, qanday va qayerda ekanini aytish', 'Lola is a kind teacher. Ali isn’t here. Where is he? Yes, he is.',
        'Sinf fotosini juftlikda tavsiflang: kim, qanday, qayerda. Bitta inkor va ikki savol-javob qo‘shing. Harakat fe’llari kerak emas.',
        'Foto yoniga beshta qisqa gap yozing; kamida bitta inkor, savol va qisqa javob bo‘lsin.',
        'Lola is a kind teacher. We’re at school. Ali isn’t here. Is he in the garden? Yes, he is.',
        'Holat, kasb va joyni uch ustunga ajrating. Mustaqil be tanlovi va savol tartibini tekshiring; keyingi ot/olmosh qoidalarini nazoratga qo‘shmang.'
    ),
    (
        'Boxes for the Fair', 'A box. Two boxes. A toy. Three toys. A city card. Two city cards. A leaf. Five leaves. The leaves are green. The boxes are blue. The fair is ready!',
        [('Nechta box?', 'two|2'), ('Leaf ning ko‘pligi matnda qanday?', 'leaves'), ('Qutilar rangi?', 'blue')],
        'The Toy Table', 'A tiny fair: one bus, two buses. One baby, two babies. One book, four books. The buses are red. The books are blue. A small table, a big toy city!',
        [('Bus ning ko‘pligi?', 'buses'), ('Baby ning ko‘pligi?', 'babies'), ('Nechta book?', 'four|4')],
        'Birlik va -s/-es/-ies/-ves ko‘pliklarni yasash', 'box → boxes; toy → toys; city → cities; leaf → leaves',
        'Yarmarka kartalarida bir va ko‘p buyumni juft ayting. Boxes, toys, cities, leaves ni ishlating; harakatni tasvirlash shart emas.',
        'To‘rtta birlik → ko‘plik yorlig‘i va ikki rang gapi yozing.',
        'box → boxes\ntoy → toys\ncity → cities\nleaf → leaves\nThe boxes are blue. The leaves are green.',
        'Undosh + y da ies, unli + y da s. Leaf → leaves ni berilgan namuna sifatida oling; barcha f bilan tugagan otlar bir xil emas.'
    ),
    (
        'Water for the Team', 'Two children. Three people. Five apples. Water for the team. The water is cold. The apples are green. The children are happy. A tiny picnic, a happy team!',
        [('Child ning ko‘pligi?', 'children'), ('Sanaladigan oziq-ovqat nomi?', 'apples'), ('Suv qanday?', 'cold')],
        'A Picnic Basket', 'Picnic labels: one person, two people. One child, three children. Four eggs. Bread. Water. The bread is fresh. The eggs are small. The basket is ready!',
        [('Person ning ko‘pligi?', 'people'), ('Nechta egg?', 'four|4'), ('Bread qanday?', 'fresh')],
        'Istisno ko‘plik va sanaladigan/sanalmaydigan otni farqlash', 'child → children; person → people; two apples / water',
        'Sayr uchun children/people kartalarini ayting. Apples/eggs ni sanang; water/bread ni alohida sanalmaydigan ot deb ko‘rsating.',
        'Ikki istisno ko‘plik va to‘rtta oziq-ovqat yorlig‘ini countable/uncountable ustuniga yozing.',
        'child → children\nperson → people\nCountable: apples, eggs\nUncountable: water, bread',
        'Butun olmani sanang, suvni esa ko‘rsatib umumiy nomini ayting. Glass of miqdor birikmasi keyingi darsda; bugun water ga -s qo‘shmaslik yetarli.'
    ),
    (
        'An Umbrella at the University', 'A bag is on the desk. The bag is blue. An umbrella is in the bag. The umbrella is red. A university badge is on the bag. An hour: sixty minutes. A rainy-day kit!',
        [('Bag rangi?', 'blue'), ('Umbrella rangi?', 'red'), ('University oldidan a yoki an?', 'a')],
        'A Surprise Parcel', 'A parcel is here. The parcel is small. An orange is in the parcel. The orange is big. A note: “A happy day!” An orange in a tiny parcel — a bright surprise!',
        [('Posilka qanday?', 'small'), ('Posilkadagi meva?', 'orange|an orange'), ('Ikkinchi orange oldidan a/an/the?', 'the')],
        'A/an ni tovushga, the ni ma’lumlikka qarab tanlash', 'a bag → the bag; an umbrella; a university; an hour',
        'Buyumni a/an bilan tanishtiring, keyin ayni buyumni the bilan tavsiflang. A university/an hour birikmalarini ovoz chiqarib ayting.',
        'Ikki buyum uchun tanishtirish → qayta eslatish juftligini yozing: jami to‘rtta gap.',
        'A bag is here. The bag is blue. An umbrella is in the bag. The umbrella is red.',
        'A/an harfga emas tovushga bog‘liq: university boshida /j/, hour boshida unli. Birinchi marta va ma’lum narsa farqini sumkani ko‘rsatib oching; bought kabi past shakl talab qilinmaydi.'
    ),
    (
        'Jobs at the Garden', 'Lola is an engineer. Ben is a teacher. Water is important. Flowers are beautiful. The garden is green. Lola is happy. Ben is happy too. A garden classroom!',
        [('Lolaning kasbi?', 'engineer|an engineer'), ('Umumiy sanalmaydigan ot?', 'water'), ('Bog‘ning rangi?', 'green')],
        'The Job Fair', 'Mina is an artist. Aziz is a doctor. Books are useful. Music is beautiful. The room is bright. Mina is ready. Aziz is ready. A cheerful job fair!',
        [('Mina kasbi?', 'artist|an artist'), ('Aziz kasbi?', 'doctor|a doctor'), ('Umumiy ko‘plikdagi ot?', 'books')],
        'Umumiy otlarda zero article va kasblarda a/an', 'Flowers are beautiful. Water is important. She is an engineer.',
        'Ikki kishini kasbi bilan tanishtiring. Water va flowers haqida berilgan sifatlar bilan umumiy ikki fikr ayting.',
        'Ikki kasb gapi, umumiy ko‘plik va umumiy sanalmaydigan ot bilan bittadan gap yozing.',
        'Lola is an engineer. Ben is a teacher. Flowers are beautiful. Water is important.',
        'Umumiy flowers/water oldiga the qo‘ymang; aniq rasmda ko‘rsatilgan narsada the mumkin. Kasb birlikdagi sanaladigan ot bo‘lgani uchun a/an saqlanadi.'
    ),
    (
        'The Students’ Tea Table', 'The teacher’s cup is blue. The students’ cups are green. A glass of water is on the table. A piece of cake is on a plate. A coffee cup is empty. The tea table is ready!',
        [('O‘qituvchining piyolasi rangi?', 'blue'), ('O‘quvchilarning piyolalari rangi?', 'green'), ('A glass of dan keyingi ot?', 'water')],
        'The Picnic Note', 'Ali’s bag is red. The girls’ bags are yellow. A bottle of water is in Ali’s bag. A bus stop is nearby. A lunch box is on the bench. A sunny picnic day!',
        [('Alining sumkasi rangi?', 'red'), ('A bottle of dan keyingi ot?', 'water'), ('Qo‘shma ot: lunch ...?', 'box')],
        'Egalik apostrofi, miqdor birikmasi va qo‘shma ot', 'teacher’s cup / students’ cups; a glass of water; coffee cup',
        'Choy stolida bitta kishining va guruhning buyumini ayting. A glass of water va coffee cup ni aniq talaffuz qiling.',
        'To‘rtta yorliq yozing: birlik egaligi, ko‘plik egaligi, miqdor birikmasi va qo‘shma ot.',
        'the teacher’s cup\nthe students’ cups\na glass of water\na coffee cup',
        'Bir egada teacher’s, s bilan tugagan ko‘plik egada students’ ni doskada alohida ko‘rsating. Apostrofni o‘qituvchi qo‘lda tekshiradi: avtomatik tekshiruv tinish belgisini farqlamasligi mumkin.'
    ),
    (
        'The Mini Cafe', 'A cafe is in the classroom. The cafe is small. Two children are ready. Sara is a cook. Ben is an artist. Sara’s cup is red. Water is free. A glass of water and a piece of cake: a tiny menu!',
        [('Kafe qayerda?', 'in the classroom|classroom|the classroom'), ('Sara kasbi?', 'cook|a cook'), ('Saraning piyolasi rangi?', 'red')],
        'The Toy Cafe', 'A toy cafe! Three boxes, two shelves, four cups. The cups are blue. The teacher’s plate is small. Tea is hot. A piece of cake is here. The children are happy.',
        [('Nechta box?', 'three|3'), ('Shelf ning ko‘pligi?', 'shelves'), ('Choy qanday?', 'hot')],
        '3-hafta: son, artikl, egalik va miqdor bilan yorliq tuzish', 'a cafe → the cafe; child → children; Sara’s cup; a glass of water',
        'Mini-kafe kartasini ko‘rsating: ikki ko‘plik, bir kasb, bir egalik va bir miqdor birikmasini ayting. Buyurtma olish uchun yangi fe’l talab qilinmaydi.',
        'Kafe uchun uch menyu yorlig‘i va ikkita be gapi yozing. Artikllar va egalikni tekshiring.',
        'a glass of water\na piece of cake\nSara’s cup\nSara is a cook. The cups are blue.',
        'Nazoratni son, artikl, egalik, miqdor bo‘yicha belgilang. Xato bo‘lsa o‘sha turdan ikki qo‘shimcha yorliq bilan qayta tekshiring; uzun reklama matni shart emas.'
    ),
    (
        'A Letter for Grandpa', 'Grandpa is here. He is happy. A letter for him. Grandma is here too. She is happy. A flower for her. A card for them. A lovely family table!',
        [('Grandpa o‘rnidagi ega olmoshi?', 'he'), ('Grandpa uchun: for ...?', 'him'), ('Grandma uchun: for ...?', 'her')],
        'The Photo Envelope', 'Ali is in the photo. He is a student. An envelope for him. Mina is in the photo too. She is a teacher. A copy for her. Two happy faces!',
        [('Ali o‘rnidagi ega olmoshi?', 'he'), ('Mina kasbi?', 'teacher|a teacher'), ('Mina uchun: for ...?', 'her')],
        'Ega va to‘ldiruvchi olmoshlarini shaxsga bog‘lash', 'Grandpa → he / for him; Grandma → she / for her',
        'Ism kartasini he/she bilan almashtiring. Xatni uzatib “For him”, “For her”, “For them” birikmalarini ayting. Knows/gives kabi fe’l gaplarini mustaqil tuzmang.',
        'Ikki shaxs haqida be gapi va ularga atalgan sovg‘a yorlig‘ini yozing.',
        'Grandpa is here. He is happy. A letter for him. Grandma is here. A flower for her.',
        'He/she ega o‘rnida, for dan keyin him/her keladi. For him tayyor birikmasi orqali object shaklni mashq qiling; harakat fe’li zamoni bu darsning sharti emas.'
    ),
    (
        'The Identical Umbrellas', 'My umbrella is blue. Your umbrella is blue too. The small umbrella is mine. The big umbrella is yours. Our bags are red. The red bags are ours. A blue umbrella puzzle!',
        [('Kichik soyabon: mine yoki yours?', 'mine'), ('Katta soyabon: mine yoki yours?', 'yours'), ('Sumkalar rangi?', 'red')],
        'The Matching Mugs', 'Lola: My mug is green.\nBen: Mine is green too.\nLola: Your mug is big.\nBen: Yes. The big mug is mine. The small mug is yours.\nLola: Our mugs are ready!',
        [('Benning piyolasi big yoki small?', 'big'), ('Ikkala piyolaning rangi?', 'green'), ('My mug o‘rnidagi mustaqil olmosh?', 'mine')],
        'My/your/our va mine/yours/ours ni farqlash', 'my umbrella → mine; your umbrella → yours; our bags → ours',
        'Ikki o‘xshash buyumni ajrating: my bag/mine va your bag/yours juftliklarini be gapida ayting. Sherik egani ko‘rsatsin.',
        'Ikki buyum uchun egalik sifati va mustaqil egalik olmoshi bilan jami to‘rtta gap yozing.',
        'My bag is red. The red bag is mine. Your bag is blue. The blue bag is yours.',
        'My dan keyin ot kerak; mine o‘zi ot birikmasi o‘rnini bosadi. Mine bag emas. Rangli buyumlar egasini almashtirib ma’noni tekshiring.'
    ),
    (
        'The Costume Table', 'This is my hat. That is your crown. These are our masks. Those are Ben’s boots. Whose scarf is this? It is Lola’s. A tiny hat, a giant scarf!',
        [('Uzoqdagi buyum: that is your ...?', 'crown'), ('Benning buyumlari?', 'boots'), ('Sharf kimniki?', 'Lola|Lola’s|Lola\'s')],
        'The Stage Mirror', 'Ben: Whose gloves are these?\nMina: They are mine. Those gloves are yours.\nBen: Is this your hat?\nMina: Yes. That hat is Lola’s.\nBen: These gloves are tiny!',
        [('Yaqindagi qo‘lqop egasi?', 'Mina'), ('Uzoqdagi shlyapa egasi?', 'Lola'), ('These gloves qanday?', 'tiny')],
        'This/that/these/those va whose bilan ishora va egalik', 'this hat / that crown; these masks / those boots; Whose scarf is this?',
        'Yaqin-uzoqdagi bittadan va ko‘p buyumni ko‘rsating. To‘rtta ishora shakli hamda bitta Whose ...? savolini ishlating.',
        'To‘rtta ishora gapi va bitta whose savol-javob yozing.',
        'This is my hat. That is your crown. These are our masks. Those are Ben’s boots. Whose scarf is this? It is Lola’s.',
        'Masofani qo‘l bilan, sonni bitta/ikkita buyum bilan ajrating. These/those bilan are; whose savoliga egani aytish kifoya.'
    ),
    (
        'The Empty Gift Box', 'Two boxes are here. The blue one is small. The red one is big. Something is in the blue one. Nothing is in the red one. Nobody is outside. Somebody is at the door. A surprise!',
        [('Kichik quti rangi?', 'blue'), ('Qizil qutida something yoki nothing?', 'nothing'), ('Eshik oldida somebody yoki nobody?', 'somebody')],
        'The Mystery Pockets', 'Mina: Is anything in the green pocket?\nBen: Nothing. Something is in the yellow one.\nMina: Is anybody outside?\nBen: No. Nobody is outside.\nMina: The small ones are empty!',
        [('Qaysi cho‘ntakda something?', 'yellow|the yellow one'), ('Yashil cho‘ntakda nima?', 'nothing'), ('Tashqarida kim?', 'nobody')],
        'One/ones va noaniq olmoshlarni be bilan ishlatish', 'the blue one; the small ones; Something is here. Nobody is outside.',
        'Ikki qutini one bilan qayta atang. Ichidagini something/nothing, odamni somebody/nobody bilan be gapida ayting. Need/don’t need talab qilinmaydi.',
        'Qutilar haqida to‘rtta qisqa gap yozing: one, ones va ikki noaniq olmosh bo‘lsin.',
        'The blue one is small. The small ones are empty. Something is here. Nobody is outside.',
        'One birlik ot, ones ko‘plik ot o‘rnida. Something/nobody bilan is ni saqlang. Nothing o‘zi inkor ma’noda; not nothing qo‘shmang.'
    ),
    (
        'Our Name Badges', 'Every badge is different. Each badge is bright. Mina: by myself. Ben: by himself. Ready-made card: “We help each other.” Each other = bir-biriga. The badges are ready. A colourful team!',
        [('Har bir nishon qanday: different yoki identical?', 'different'), ('Mina uchun by ...?', 'myself'), ('Bir-biriga ma’nosidagi ikki so‘z?', 'each other')],
        'The Sandwich Cards', 'Every plate is clean. Each sandwich is small. Lola: by herself. The team: by ourselves. Ready-made model: “They help each other.” Each other: bir-biriga. A cheerful picnic!',
        [('Har bir likopcha qanday?', 'clean'), ('Lola uchun by ...?', 'herself'), ('Jamoa uchun by ...?', 'ourselves')],
        'Every/each, o‘zlik va o‘zaro olmosh ma’nosini tanish', 'Every badge is bright. Each badge is different. by myself / each other',
        'Nishonlarni every/each + birlik ot + is bilan tavsiflang. By myself/by herself tayyor birikmasini takrorlang. Berilgan We help each other kartasida each other ni ko‘rsating; yangi harakat hikoyasi kerak emas.',
        'Every/each bilan ikkita be gapi va ikki tayyor o‘zlik birikmasini yozing. Each other ni berilgan modeldan ajratib ko‘chiring.',
        'Every badge is bright. Each badge is different. by myself; by herself; each other',
        'O‘ziga yo‘nalgan strelka va ikki kishi orasidagi strelka bilan myself/each other ni farqlang. Made/help zamonini o‘zgartirmang; o‘zlik shakllari tayyor birikma va tanish darajasida.'
    ),
    (
        'The Borrowed Art Kit', 'This is my art box. The blue pencil is mine. Those brushes are yours. A card for her. Every brush is clean. Nothing is in the small pocket. The big one is full. A ready-made label: by myself.',
        [('Ko‘k qalam egasi: mine yoki yours?', 'mine'), ('Kichik cho‘ntakda nima?', 'nothing'), ('Big one full yoki empty?', 'full')],
        'The Lost Scarf Desk', 'Lola: Whose scarf is this?\nBen: It is mine. Those gloves are hers.\nLola: A bag for him. A card for her.\nBen: Every label is clear.\nLola: Ready-made team card: each other. A friendly desk!',
        [('Sharf egasi?', 'Ben'), ('Qo‘lqoplar: his yoki hers?', 'hers'), ('Har bir yorliq qanday?', 'clear')],
        '4-hafta: ishora, egalik va olmosh ma’nolarini ajratish', 'my box / mine; for her; those brushes; every brush; by myself / each other',
        'Topilmalar stolida whose savolini bering; mine/yours bilan javob bering. For him/her birikmasini ayting. By myself va each other kartalarining ma’nosini rasmdan tanlang.',
        'Buyumlar uchun uchta be gapi va ikki for him/her yorlig‘i yozing. O‘zlik va o‘zaro ma’nosini ikki chizma bilan belgilang.',
        'This is my box. The blue pencil is mine. Those brushes are yours. A card for her. A bag for him.',
        'Ega, object, egalik, ishora va o‘zlikni bir xil vazifa deb bermang. Tanishni talab qiladigan each other kartasini erkin gap tuzish bilan baholamang.'
    ),
    (
        'The Rooftop Reading Corner', 'There is a reading corner on the roof. There are two chairs. There is a small table. There isn’t a sofa. There aren’t any lamps. The sky is blue. A book, a chair, a tiny holiday!',
        [('Nechta stul?', 'two|2'), ('Sofa bormi? Yes/no.', 'no'), ('Osmon rangi?', 'blue')],
        'The Balcony Library', 'There is a shelf on the balcony. There are three books. There is a red cushion. There isn’t a desk. There aren’t any boxes. The cushion is soft. A tiny library!',
        [('Nechta kitob?', 'three|3'), ('Yostiq rangi?', 'red'), ('Desk bormi? Yes/no.', 'no')],
        'There is/are bilan borlik va yo‘qlikni aytish', 'There is a table. There are two chairs. There isn’t a sofa. There aren’t any lamps.',
        'Rasmdagi burchak haqida uch borlik va ikki yo‘qlik gapi ayting. Savol hali talab qilinmaydi.',
        'Rasmga 5–6 qisqa gap yozing: birlik, ko‘plik va ikkita inkor bo‘lsin. Uzun insho kerak emas.',
        'There is a reading corner. There is a table. There are two chairs. There isn’t a sofa. There aren’t any lamps.',
        'Bitta buyum uchun is, ikki buyum uchun are ni rasmda sanab tanlang. Aren’t any ni tayyor inkor qolipi sifatida bering; any ning barcha qo‘llanishlarini ochmang.'
    ),
    (
        'Questions about the Campsite', 'Is there a kitchen? Yes, there is. Are there any tents? Yes, there are. How many tents are there? There are three tents. Is there a shop? No, there isn’t. The campsite is small and quiet.',
        [('Nechta chodir?', 'three|3'), ('Oshxona bormi? Yes/no.', 'yes'), ('Do‘kon bormi? Yes/no.', 'no')],
        'A Room for Chess', 'Ben: Is there a table?\nMina: Yes, there is.\nBen: How many chairs are there?\nMina: There are four chairs.\nBen: Are there any clocks?\nMina: No, there aren’t. A quiet chess room!',
        [('Nechta stul?', 'four|4'), ('Stol bormi? Yes/no.', 'yes'), ('Soatlar bormi? Yes/no.', 'no')],
        'Borlik, son va qisqa javob savollarini ishlatish', 'Is there a kitchen? Are there any tents? How many tents are there?',
        'Lager va klub rasmi bilan ma’lumot almashing: Is there, Are there, How many ... are there savollarini bittadan bering; qisqa javob bilan tekshiring.',
        'Uch savol va uch qisqa javob yozing. Son savoliga rasmga mos raqam kiriting.',
        'Is there a table? Yes, there is. Are there any clocks? No, there aren’t. How many chairs are there? There are four.',
        'Savolda be there oldiga o‘tadi; how many bilan ko‘plik ot keladi. Yes, there is bilan It is ni almashtirmang.'
    ),
    (
        'The Repair Stall', 'There is a repair stall. It is small. There are two lamps. They are bright. Possession cards: “I have a bag.” “She has a box.” “I don’t have a bike.” “He doesn’t have a car.” Bag: yes. Bike: no.',
        [('Ta’mirlash joyi qanday?', 'small'), ('Nechta chiroq?', 'two|2'), ('I don’t have a bike kartasi: bike yes yoki no?', 'no')],
        'The Camera Club', 'There is a camera club. It is friendly. Model cards: “I have a camera.” “Lola has a bag.” “Ben doesn’t have a camera.” Camera for Ben: no. A bag for Lola: yes. A friendly little club!',
        [('Klub qanday?', 'friendly'), ('Lolaning buyumi?', 'bag|a bag'), ('Benda kamera bormi? Yes/no.', 'no')],
        'There/it ni farqlash; have/has egalik kartalarini tanish', 'There is a stall. It is small. Tanish: I have a bag. / He doesn’t have a car.',
        'Bitta joyni There is bilan tanishtiring, It is bilan tavsiflang. Berilgan have/has kartalarini yes/no rasmga moslang va aynan o‘qing; don’t/doesn’t bilan yangi gap yasash shart emas.',
        'There is va It is bilan ikki gap yozing. Berilgan egalik kartalarini bor/yo‘q ustuniga ko‘chiring; fe’lni almashtirmang.',
        'There is a stall. It is small.\nBor: I have a bag.\nYo‘q: I don’t have a bike.',
        'There yangi narsa borligini ochadi, it o‘sha narsaga qaytadi. Have/has va don’t/doesn’t have xaritada bugun bor, lekin hafta 6 gacha faqat ma’noni tanish va aynan takrorlash; umumiy Present Simple qoidasi yoki erkin tuslash yo‘q.'
    ),
    (
        'The Costume Checklist', 'We’ve got a crown. Lola’s got a hat. Ben hasn’t got a mask. I haven’t got boots. The stage is ready. Ready-made question card: “Do you have a hat?” Hat: yes. A tiny crown for a big show!',
        [('Lolaning buyumi?', 'hat|a hat'), ('Benning maskasi bormi? Yes/no.', 'no'), ('Jamoaning buyumi?', 'crown|a crown')],
        'The Travel Bag', 'Mina: I’ve got a ticket.\nBen: I’ve got a bag. I haven’t got a map.\nMina: Lola’s got a map.\nBen: Ready-made question: “Does she have a map?”\nMina: Map: yes. Our little trip kit!',
        [('Mina nimaga ega?', 'ticket|a ticket'), ('Benda yo‘q buyum?', 'map|a map'), ('Xarita kimda?', 'Lola')],
        'Have got egalik qolipi; do/does savolini tanish', 'I’ve got a ticket. I haven’t got a map. Tanish kartasi: Does she have a map?',
        'Tayyor I’ve got/I haven’t got ramkasiga buyum nomini qo‘ying. Do/does savol kartasini rasmga moslang; yangi do/does savolini yasamang.',
        'Got ramkalari bilan to‘rtta qisqa jihoz gapi yozing. Berilgan do/does savolining ma’nosini o‘zbekcha ayting, shaklini o‘zgartirmang.',
        'I’ve got a ticket. I’ve got a bag. I haven’t got a map. Lola’s got a map.',
        'Got egalik qolipini bir butun o‘rgating. Lola’s got dagi ’s = has. Do/does savollari faqat tayyor kartada taniladi; week 6 gacha mustaqil savol ishlab chiqarish mezoni emas.'
    ),
    (
        'The Paper Bridge', 'Have you got paper? Yes, I have. Have you got glue? No, I haven’t. Fold the paper, please. Don’t cut the paper. Put it on two books. Let’s start. Let’s not hurry. A little paper bridge!',
        [('Qaysi jihoz yo‘q?', 'glue'), ('Paper bilan taqiqlangan ish: cut yoki fold?', 'cut'), ('Ko‘prik nechta kitob ustida?', 'two|2')],
        'The Kind Robot', 'Lola: Have you got a pencil?\nBen: Yes, I have.\nLola: Draw a circle, please. Don’t close the book. Let’s colour the circle.\nBen: Have you got a red pencil?\nLola: Yes, I have. A red robot face!',
        [('Chiziladigan shakl?', 'circle|a circle'), ('Yopish taqiqlangan buyum?', 'book|the book'), ('Qalam rangi?', 'red')],
        'Have got savol-javobi, buyruq va let’s taklifi', 'Have you got paper? Yes, I have. Fold it. Don’t cut it. Let’s start.',
        'Qog‘oz ko‘prik uchun Have you got ...? deb jihoz so‘rang. Ikkita buyruq, bitta Don’t va bitta Let’s qolipini ayting; sherik harakat bilan tekshirsin.',
        'Bitta jihoz savol-javobi va to‘rtta qisqa ko‘rsatma yozing. Qadamlarni raqamlang.',
        'Have you got paper? Yes, I have.\n1. Fold the paper.\n2. Don’t cut it.\n3. Put it on two books.\n4. Let’s start.',
        'Buyruqda ega yo‘q: Fold. Inkor buyruq Don’t + asosiy fe’l; bu don’t bilan odat gapini yasash degani emas. Let’s o‘zimizni ham taklifga qo‘shadi.'
    ),
    (
        'A Welcome Box', 'There is a welcome box. It is blue. There are two pencils. There isn’t a map. Have you got a notebook? Yes, I have. Open the box, please. Don’t close it. Let’s start. A new friend, a warm welcome!',
        [('Qutining rangi?', 'blue'), ('Nechta qalam?', 'two|2'), ('Qutida yo‘q buyum?', 'map|a map')],
        'The First Club Kit', 'Ben: Is there a name card?\nLola: Yes, there is. There are two badges too.\nBen: Have you got a pen?\nLola: Yes, I have. Write your name, please. Don’t write on the table. Let’s begin!\nBen: Ready-made possession card: “I have a pen.”',
        [('Nechta nishon?', 'two|2'), ('Qayerga yozish taqiqlangan?', 'table|the table|on the table'), ('Lolada ruchka bormi? Yes/no.', 'yes')],
        '5-hafta: borlik, egalik qolipi va ko‘rsatmani birlashtirish', 'There is a box. It is blue. Have you got a pen? Open it. Let’s start.',
        'Yangi a’zoga qutini tanishtiring: there bilan ikki gap, got bilan bitta savol-javob, bitta buyruq va bitta taklif. Have/has/do/does kartalarida faqat ma’noni taning.',
        'Kutib olish kartasiga 5–7 qisqa gap yoki ko‘rsatma yozing. There, got va buyruq qoliplaridan foydalaning; uzun xat kerak emas.',
        'There is a welcome box. It is blue. There are two pencils. Have you got a pen? Yes, I have. Open the box, please. Let’s start.',
        'Borlik, egalik va buyruqni uch vaziyatda tekshiring. Have/has/do/does kartalarini tanish natijasini mustaqil Present Simple ishlab chiqarish deb hisoblamang; bu week 6 vazifasi.'
    ),
]


def questions(rows):
    return [dict(prompt=p + ' Qisqa javob yoki berilgan variantni yozing.',
                 answers=a.split('|'), explanation=f'Matndagi dalil: «{a.split("|")[0]}». Javob uchun yangi gap tuzish shart emas.')
            for p, a in rows]


def early_skills(original):
    result = copy.deepcopy(original)
    by_no = {x['lesson']: x for x in result}
    for no, row in enumerate(EARLY, 1):
        rt, reading, rq, lt, listening, lq, aim, board, speaking, writing, model, note = row
        pack = by_no[no]
        pack.update(
            objective=aim + ': berilgan uch tekshiruvdan kamida ikkitasini mustaqil bajaraman.',
            reading=dict(title=rt, text=reading, questions=questions(rq)),
            listening=dict(title=lt, text=listening, questions=questions(lq)),
            speaking=dict(prompt=speaking, success=[aim + ' bo‘yicha berilgan vazifa bajarilgan.',
                'Tayyor karta yoki o‘tilgan qolip to‘g‘ri tanlangan; hali o‘tilmagan zamon talab qilinmagan.',
                'Sherik ko‘rsatilgan shaxs, buyum yoki ma’noni to‘g‘ri aniqlagan.']),
            writing=dict(prompt=writing, model=model, success=[
                'Topshiriqda so‘ralgan yorliq, gap yoki juftliklar to‘liq.',
                aim + ' bo‘yicha kamida ikki to‘g‘ri misol bor.',
                'Imlo va bosh harflar namunaga mos; mustaqil va ko‘chirilgan ish farqlangan.']),
            teacherNote=note + ' Reading: avval sarlavha va rasm/real buyum, keyin uch savolga matndan dalil. '
                'Listening: matnni yashirib ikki marta tabiiy, sekin o‘qing; avval kim/nima, keyin tafsilot. '
                'Savolni o‘zbekcha tushuntiring, bir so‘zli javobni qabul qiling. '
                'Qiynaluvchiga ikki tanlov va ko‘rsatish imkonini bering; tez ishlovchiga shu shaklda boshqa rasm bering.')
    return result


# Safe board/check anchors where map examples presuppose later verb grammar.
# Map order and topic allocation remain untouched.
SAFE = {
    '3.6': ('water / advice / information', 'Bitta maslahat uchun an advice to‘g‘rimi?', 'yo‘q', 'Advice va information odatda sanalmaydi; a/an yoki ko‘plik -s qo‘shilmaydi.'),
    '3.9': ('A cat is here. The cat is black.', 'Ikkinchi gapdagi ma’lum mushuk: a cat yoki the cat?', 'the cat', 'Avval tanishtirilgan ayni buyum uchun the; have yoki buy bilan gap yasash shart emas.'),
    '3.10': ('Books are useful. Cats are beautiful.', 'Umuman kitoblar: Books yoki The books?', 'Books', 'Umumiy ko‘plik ot artiklsiz; aniq ko‘rsatilgan kitoblar bo‘lsa the books.'),
    '3.11': ('Water is important. Music is beautiful.', 'Umuman suv haqida Water yoki A water?', 'Water', 'Umumiy sanalmaydigan ot artiklsiz; love/like fe’llarini ishlab chiqarish shart emas.'),
    '4.3': ('my bag / your bag / our bags / its tail', 'Our bags birikmasida our dan keyin ot bormi?', 'ha, bags', 'Egalik sifati ot oldida keladi; its egalik, it’s esa it is/it has qisqartmasi.'),
    '4.4': ('My bag is blue. The blue bag is mine.', 'Mustaqil egalik: The bag is my yoki mine?', 'mine', 'Mine ot birikmasi o‘rnida mustaqil keladi; undan keyin bag qo‘shilmaydi.'),
    '4.5': ('your bag / yours; her scarf / hers', 'Ot oldida your yoki yours? Ot o‘rnida-chi?', 'your bag; yours', 'Ot oldida egalik sifati, ot takrorlanmasa mustaqil egalik olmoshi.'),
    '4.9': ('the blue box → the blue one; small boxes → small ones', 'Bir nechta boxes o‘rniga one yoki ones?', 'ones', 'One birlik, ones ko‘plik sanaladigan ot o‘rnini bosadi; want fe’li shart emas.'),
    '4.10': ('Somebody is here. Is anybody outside? Nobody is outside.', 'Hech kim uchun somebody yoki nobody?', 'nobody', 'Nobody o‘zi inkor ma’noda, yana not kerak emas. Somebody biror kishi, oddiy so‘roqda anybody.'),
    '5.11': ('I’ve got a bag. She’s got a hat. We’ve got chairs.', 'She’s got dagi ’s: is yoki has?', 'has', 'Have got egalik qolipi: I/we have got, she has got; boshqa harakat fe’liga ko‘chirmang.'),
    '5.13': ('Have you got a pen? Yes, I have. Has she got a map? No, she hasn’t.', 'Has she got a map savoliga qisqa inkor javob?', 'No, she hasn’t.', 'Have/has oldinga chiqadi; qisqa javobda got qaytarilmaydi. No, she’s not bu has savoliga mos emas.'),
    '5.14': ('Write your name, please. Sit here.', 'Buyruq uchun Write yoki Writes?', 'Write', 'Buyruq oddiy fe’l bilan boshlanadi; ega va must talab qilinmaydi.'),
    '1.1': ('student / book / school', 'Qaysi so‘z odam nomi: student yoki kind?', 'student', 'Ot odam, buyum yoki joyni nomlaydi.'),
    '1.2': ('kind / happy / useful', 'Happy nommi yoki belgi?', 'belgi, sifat', 'Sifat odam yoki buyumning belgisini bildiradi.'),
    '1.3': ('read / walk / be', 'Read harakatmi, buyum nomimi?', 'harakat', 'Fe’l harakat yoki holatni bildiradi; be ham fe’l.'),
    '1.4': ('Ali → he; the book → it', 'The book o‘rniga he yoki it?', 'it', 'Olmosh oldingi otga ishora qiladi.'),
    '1.5': ('walk + slowly; read + quietly', 'Walk slowly da qanday ma’nosini qaysi so‘z beradi?', 'slowly', 'Ravish harakatning qanday bajarilishini ko‘rsatadi.'),
    '1.6': ('in the room / on the table', 'Stol ustida uchun in yoki on?', 'on', 'Predlog joy munosabatini bildiradi; birikmani rasm bilan bog‘lang.'),
    '1.7': ('tea and cake; small but useful', 'And qo‘shadimi yoki qarama-qarshi qo‘yadimi?', 'qo‘shadi', 'And qo‘shadi, but qarama-qarshi qo‘yadi; because sababni tanitadi, hozir uni tanish yetarli.'),
    '1.8': ('I / you / he / she / it / we / they', 'Ali and Mina o‘rniga we yoki they?', 'they', 'Ega olmoshi kim haqida gap ketayotganini bildiradi.'),
    '1.9': ('My sister | works. [tayyor model]', 'My sister works. Kim? Ega qaysi qism?', 'My sister', 'Ega bir necha so‘zdan iborat bo‘lishi mumkin; works ni yasash shart emas.'),
    '1.10': ('I | read | books. [tayyor model]', 'I read books da fe’l va to‘ldiruvchi qaysi?', 'read — fe’l; books — to‘ldiruvchi', 'Fe’l harakat, object harakat bog‘langan narsani bildiradi; berilgan modelni tahlil qiling.'),
    '1.11': ('She | is | kind. [tayyor model]', 'Kind bu yerda ish bajarilgan buyummi yoki tavsifmi?', 'tavsif, complement', 'Complement egani tavsiflaydi; object bilan bir xil emas.'),
    '1.12': ('We | study | English. [tayyor model]', 'We / English / study kartalarining tayyor modeldagi tartibi?', 'We study English.', 'Ega → fe’l → davom; aynan berilgan modelni yig‘ing, yangi fe’l yasamang.'),
    '1.13': ('I am happy. / I work. [tayyor modellar]', 'I work modeliga am qo‘shiladimi?', 'yo‘q', 'Be holatni bog‘laydi; work harakat fe’li. Hozir farqni tanish yetarli.'),
    '1.14': ('I am Ali. / Are you ready? [tayyor modellar]', 'Ism qanday boshlanadi, savol qaysi belgi bilan tugaydi?', 'bosh harf; savol belgisi', 'Bosh harf va gap oxirini qo‘lda tekshiring; yangi savol tuzish talab qilinmaydi.'),
    '3.8': ('A bag is here. The bag is blue.', 'Birinchi tilga olishda a bag yoki the bag?', 'a bag', 'Yangi bitta buyum a/an bilan kiradi; bought shaklini bu darsda talab qilmang.'),
    '4.1': ('he / for him; she / for her; they / for them', 'For dan keyin he yoki him?', 'him', 'Predlogdan keyin object olmoshi; for him tayyor birikmasi bilan mashq qiling.'),
    '4.2': ('He is here. A card for him.', 'Ega uchun he, for dan keyin qaysi shakl?', 'him', 'Ega va object o‘rnini ajrating; knows kabi harakat fe’lini tuslashni so‘ramang.'),
    '4.11': ('Something is here. Is anything here? Nothing is here.', 'Nothing bor gapga yana not kerakmi?', 'yo‘q', 'Something/anything/nothing biror narsa/so‘roqdagi narsa/hech narsa ma’nolarini be bilan taniting.'),
    '4.12': ('Every badge is bright. Each badge is different.', 'Every/each dan keyin badge yoki badges?', 'badge', 'Every va each birlik ot bilan keladi; every guruhning barchasi, each alohida har biriga urg‘u beradi.'),
    '4.13': ('by myself / by herself / by ourselves [tayyor birikma]', 'Lola: by himself yoki by herself?', 'by herself', 'O‘zlik shaklini shaxsga ulang; by myself — o‘zim/yolg‘iz. Made kabi o‘tgan zamonni o‘zgartirish shart emas.'),
    '4.14': ('We help each other. [faqat tayyor model]; each other = bir-biriga', 'Each other bir o‘ziga qaytadimi yoki ikki tomon orasidami?', 'ikki tomon orasida', 'Ikki odam orasidagi strelkani chizing. Help butun berilgan modelda; o‘quvchi yangi harakat gapini yasamaydi.'),
    '5.8': ('I have a bag. She has a box. [tanish kartalari]', 'She has a box kartasida quti kimda?', 'she — ayol/qizda', 'Have/has egalik ma’nosini tanish va aynan takrorlash; erkin shaxs almashtirish week 6 ga qoladi.'),
    '5.9': ('I don’t have a bike. He doesn’t have a car. [tanish kartalari]', 'He doesn’t have a car: mashina bormi?', 'yo‘q', 'Inkor egalikni rasmga moslang. Do/does tuslashini yoki yangi inkor gapni hali talab qilmang.'),
    '5.10': ('Do you have a pen? Does she have a map? [tanish kartalari]', 'Does she have a map kartasi qaysi buyum haqida?', 'map', 'Tayyor savolni eshitib ma’nosini aniqlash kifoya; mustaqil do/does savoli week 6 da.'),
}


def plan(no, modules):
    week = (no - 1) // 6 + 1
    day = (no - 1) % 6 + 1
    module_ids = [week - 1] if week <= 27 else [list(range(0, 8)), list(range(8, 13)),
        list(range(13, 19)), list(range(19, 24)), list(range(24, 27))][week - 28]
    all_topics = [(f'{mi + 1}.{ti + 1}', title, example, mi)
                  for mi in module_ids for ti, (title, example) in enumerate(modules[mi]['items'])]
    assigned = all_topics if day == 6 else all_topics[(day - 1) * len(all_topics) // 5:day * len(all_topics) // 5]
    return week, day, module_ids, assigned


def worked(q):
    return f'{q["prompt"]} → {" / ".join(q["answers"])}. {q["explanation"]}'


def topic_card(topic, exercises, early):
    tid, title, example, mi = topic
    if early and tid in SAFE:
        board, question, answer, reason = SAFE[tid]
        return (f'{tid} · {title}: {board}', f'{question} [Javob: {answer}. {reason}]', reason,
                f'{question} → {answer}. {reason}')
    first, second = exercises[tid][:2]
    return (f'{tid} · {title}: {example}',
            f'{first["prompt"]} [Javob: {" / ".join(first["answers"])}. {first["explanation"]}]',
            first['explanation'], worked(second))


def make_guidance(skills, modules, exercises, notes):
    result = []
    for pack in skills:
        no = pack['lesson']
        week, day, mids, assigned = plan(no, modules)
        cards = [topic_card(t, exercises, no <= 30) for t in assigned]
        names = '; '.join(t[1] for t in assigned)
        # Every assigned topic is available; review/spiral sessions explicitly
        # diagnose first and select only 3–5 weak topics, never reteach all cards.
        review = day == 6 or week > 27
        route = ('Avval shu mavzulardan 5 qisqa topshiriqni yordamsiz bajartiring; xatolar bo‘yicha '
                 '3–5 mavzuni tanlang. Quyidagi doska bankidan faqat tanlangan kartalarni oching. '
                 'Bir xil xato qilgan juftlarni birlashtiring, so‘ng yangi parallel misol bilan qayta tekshiring. '
                 if review else 'Har bir doska modelini vaziyat yoki buyum bilan oching. Avval o‘zingiz namuna '
                 'qiling, keyin juftlikda, oxirida yordamsiz tekshiring. ')
        boundary = ('1-haftada faqat turkum, tayyor gap tahlili, yorliq va yodlangan birikmalar; '
                    'erkin gap yoki fe’l tuslashni so‘ramang. ' if no <= 6 else
                    'Faqat bugungacha o‘tilgan be shakllari; keyingi kun savol/qisqartmasini oldindan talab qilmang. ' if no <= 12 else
                    'Ot va artiklni o‘tilgan be bilan ishlating; yangi harakat zamoni shart emas. ' if no <= 18 else
                    'Olmoshni be yoki tayyor birikmada ishlating. O‘zlik/o‘zaro kartalarda yangi harakat gapini talab qilmang. ' if no <= 24 else
                    'There va o‘tilgan got/buyruq qoliplari ishlab chiqariladi. Have/has/do/does faqat tayyor kartani tanish; '
                    'Present Simple mustaqil ishlab chiqarish 31-darsdan boshlanadi. ' if no <= 30 else '')
        reading = pack['reading']
        listening = pack['listening']
        explain = route + boundary + ' '.join(f'{t[0]}: {c[2]}' for t, c in zip(assigned, cards))
        explain += (f' O‘qish — «{reading["title"]}»: avval mazmunni ayttiring, so‘ng har javob yonida matndagi dalilni belgilang. '
                    f'Tinglash — «{listening["title"]}»: transkriptni yashiring; birinchi o‘qishda vaziyat, ikkinchisida uch tafsilot. '
                    'Javobdan keyingina transkriptni oching. ' + pack['teacherNote'] +
                    ' Gapirish vazifasi: ' + pack['speaking']['prompt'] + ' Yozish vazifasi: ' + pack['writing']['prompt'] +
                    ' Tayyor yozuv namunasini dastlabki urinishdan keyin ko‘rsating; nusxa ko‘chirishni mustaqil natija deb baholamang.')
        skill_checks = []
        for label, block in [('Reading', reading), ('Listening', listening)]:
            q = block['questions'][0]
            skill_checks.append(f'{label} · {block["title"]}: {q["prompt"]} '
                                f'[Javob: {" / ".join(q["answers"])}. {q["explanation"]}]')
        production = ('Vazifadagi yorliq yoki belgilashni namunasiz qaytaring; kamida ikki to‘g‘ri tanlovni tekshiring.'
                      if no <= 6 else 'Gapirish va yozishda tekshiring: ' + pack['speaking']['success'][0] + ' ' + pack['writing']['success'][1])
        objective = (f'{no}-dars — ' + pack['objective'] + ' Grammatik fokus: ' + names +
                     (' Diagnostikadan tanlangan 3–5 mavzudan kamida 4/5 to‘g‘ri javob va bitta tuzatilgan ish namunasi.' if review else
                      ' Har tayinlangan mavzudan kamida bitta to‘g‘ri javob; chiqishdagi besh banddan kamida to‘rttasi mustaqil.') +
                     ' ' + production)
        # Use the exact topic-specific explanation as an anticipated correction,
        # plus the module's authored common pitfall; do not invent incorrect forms.
        mistake = ('Chegara xatosi: tayyor kartani tanish o‘rniga hali o‘tilmagan fe’lni yasatish. ' + boundary
                   if no <= 30 else '')
        mistake += ' '.join(dict.fromkeys(notes[mi][2] for mi in mids))
        mistake += ' Bugungi tuzatish namunasi: ' + cards[0][3]
        vocab_start = (week - 1) * 125 + (0 if day == 6 else (day - 1) * 25) + 1
        vocab_end = week * 125 if day == 6 else vocab_start + 24
        exits = [
            '1. Grammatik tekshiruv: ' + cards[0][1],
            '2. Boshqa maqsadli tekshiruv: ' + cards[-1][1],
            '3. Mazmunni dalil bilan tekshirish: ' + skill_checks[0],
            f'4. Bugungi {vocab_start}–{vocab_end} lug‘at oralig‘idan o‘qituvchi tanlagan uch so‘zni tarjimasiz taning yoki ayting; kamida 2/3 to‘g‘ri bo‘lsin.',
            '5. ' + production + ' Yordam ishlatilsa alohida qayd qiling. 4/5 dan past bo‘lsa, keyingi dars boshida aynan xato turini ikki yangi misolda tekshiring.',
        ]
        homework = [
            (f'Grammatika: bugungi kartalar — {", ".join(t[0] for t in assigned)}. '
             + ('Diagnostikada xato chiqqan uch kartani tanlang. ' if review else '')
             + ('Tayyor namunalardagi so‘zlarni turkum yoki gap qismiga ajrating; yangi gap yasamang.' if no <= 6 else
                'Har kartani o‘qib ma’nosini rasmga moslang. Bugungi writing topshirig‘idagi shakllardan foydalaning; keyingi dars shaklini qo‘shmang. Faqat tanish deb belgilangan kartani aynan o‘qing, yangi fe’l yoki zamon yasamang.' if no <= 30 else
                'Har tanlangan shakldan ikki yangi misol yozing; bitta xatoni to‘g‘rilab sababini ayting.')),
            f'Lug‘at: {vocab_start}–{vocab_end} oralig‘idagi so‘zlarni yopib eslang; qiyin beshtasini rasm yoki ma’no bilan qayta tekshiring.',
            f'Reading «{reading["title"]}»: uch savolga qisqa javob va matndan dalil yozing. Listening «{listening["title"]}»: audio bo‘lsa matnsiz qayta tinglang; bo‘lmasa ikki qatorni ko‘rib o‘qing, yoping va eslang — buni tinglash nazorati deb hisoblamang.',
            'Speaking: ' + pack['speaking']['prompt'] + ' Yakunda tekshiring: ' + pack['speaking']['success'][0],
            'Writing: ' + pack['writing']['prompt'] + ' So‘ng namuna bilan solishtiring va bitta tuzatishni boshqa rangda belgilang.',
        ]
        result.append(dict(lesson=no, objective=objective,
            board=[c[0] for c in cards] + [f'Vaziyat: {reading["title"]} ↔ {listening["title"]}'],
            explain=explain, checkQuestions=[c[1] for c in cards] + skill_checks,
            commonMistake=mistake,
            differentiation=(f'Tayanch: «{reading["title"]}» savollarini bittadan bering, ikkita javob variantidan tanlating; '
                f'doskadagi «{cards[0][0]}» modelini ko‘rinadigan qoldiring. '
                + ('Rasmga ko‘rsatish yoki tayyor birikmani aytish yetarli; yangi zamon bilan murakkablashtirmang. '
                   if no <= 30 else 'Gapni boshlash va dalil joyini topish uchun juftlik yordami bering. ')
                + f'Kengaytirish: «{listening["title"]}»dagi javobni matndan dalil bilan izohlatsin; '
                + ('shu so‘z/shaklni boshqa rasm yoki kartada yordamsiz tanisin.' if no <= 6 else
                   'bugun o‘tilgan shaklda bitta yangi buyum yoki shaxs bilan misol keltirsin; faqat tanish deb belgilangan kartani tuslamasin.' if no <= 30 else
                   f'«{assigned[-1][1]}» bo‘yicha ikkinchi vaziyat yaratsin va ma’no yoki shakl tanlovini asoslasin.')),
            exitTicket=exits, homework=homework))
    return result


def validate(skills, guidance, original, modules):
    required = {'lesson', 'objective', 'board', 'explain', 'checkQuestions', 'commonMistake',
                'differentiation', 'exitTicket', 'homework'}
    def nonempty(value):
        if isinstance(value, str):
            assert value.strip(), 'Empty string'
        elif isinstance(value, list):
            assert value, 'Empty list'
            for child in value:
                nonempty(child)
        elif isinstance(value, dict):
            assert value, 'Empty object'
            for child in value.values():
                nonempty(child)
    for records in [skills, guidance]:
        assert len(records) == 192
        assert [x['lesson'] for x in records] == list(range(1, 193))
        nonempty(records)
    assert skills[30:] == original[30:], 'Out-of-scope later skill lessons changed'
    for pack, old in zip(skills, original):
        assert set(pack) == set(old), 'Skill schema changed'
        for mode in ['reading', 'listening']:
            assert len(pack[mode]['questions']) == 3
            assert len(pack[mode]['text']) >= 100
        assert len(pack['writing']['model']) > 30, pack['lesson']
        for mode in ['reading', 'listening', 'speaking', 'writing']:
            assert set(pack[mode]) == set(old[mode]), 'Nested schema changed'
    for mode in ['reading', 'listening']:
        assert len({x[mode]['text'] for x in skills}) == 192, 'Repeated passage'
        for pack in skills[:30]:
            for q in pack[mode]['questions']:
                # Canonical answer must be present, except explicitly semantic
                # yes/no and classification questions.
                answer = q['answers'][0].lower()
                assert answer in pack[mode]['text'].lower() or answer in {'yes', 'no', 'b'}, (pack['lesson'], q)
    for entry in guidance:
        assert set(entry) == required
        for field in ['board', 'checkQuestions', 'exitTicket', 'homework']:
            assert isinstance(entry[field], list) and all(isinstance(v, str) for v in entry[field])
        for field in ['objective', 'explain', 'commonMistake', 'differentiation']:
            assert isinstance(entry[field], str)
        assigned = plan(entry['lesson'], modules)[3]
        for tid, title, _, _ in assigned:
            assert any(v.startswith(tid + ' · ' + title + ':') for v in entry['board']), (entry['lesson'], tid)
        assert len(entry['checkQuestions']) == len(assigned) + 2
        assert len(entry['exitTicket']) == 5
    for field in ['objective', 'board', 'checkQuestions', 'explain', 'exitTicket', 'homework']:
        assert len({json.dumps(x[field], ensure_ascii=False) for x in guidance}) == 192, ('Repeated guidance', field)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate without writing any files')
    args = parser.parse_args()
    original = read('intensive-skills.json')
    modules = read('intensive-grammar-map.json')
    exercises = read('intensive-topic-exercises.json')
    notes = read('intensive-teacher-notes.json')
    skills = early_skills(original)
    guidance = make_guidance(skills, modules, exercises, notes)
    validate(skills, guidance, original, modules)
    for name, content in [('intensive-skills.json', skills), ('intensive-lesson-guidance.json', guidance)]:
        if args.check:
            assert read(name) == content, f'{name} needs regeneration'
        else:
            (DATA / name).write_text(json.dumps(content, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('PASS: 192 unique complete skill packs; 192 unique complete guidance entries; all assigned topics covered; '
          'distinct passages; 180 early comprehension answer keys; later skills preserved; outputs reproducible.')


if __name__ == '__main__':
    main()
