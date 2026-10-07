"""Build the explicitly authored module 1–14 supplement; never expand contractions.

Each topic has four authored rows: prompt | accepted answers (; separated) | Uzbek
explanation. Constraints in prompts deliberately bound the acceptable responses.
Run with --check to validate the saved JSON without writing it.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'src/data/intensive-exercises-foundation.json'

PACKS = [r"""
@1.1
Otni toping: quickly / hospital / tall. | hospital | Hospital joy nomini bildirgan ot.
Tanlang: There is a ___ outside. (bicycle / beautiful) | bicycle | A artiklidan keyin bu gapda buyum nomi kerak.
Xato tasnifni tuzating: The table is large gapida table sifat deyilgan. To‘g‘ri turkumni tanlang: ot / fe’l. | ot | Table buyum nomi, shuning uchun ot.
Swim fe’lidan shaxs oti yasang: a ___. (swimmer / swimming) | swimmer | Swimmer — suzuvchi shaxs nomi.
@1.2
The old bridge is safe. Yoshni bildiruvchi sifatni yozing. | old | Old ko‘prikning eski ekanini bildiradi.
Tanlang: It is a ___ road. (narrow / narrowly) | narrow | Ot oldida uni tavsiflovchi sifat keladi.
Faqat noto‘g‘ri so‘zni tuzating: The room is beautifully. | beautiful | Be dan keyin xonani tavsiflash uchun sifat kerak.
Care otidan sifat yasang: a ___ driver. (careful / carefully) | careful | Careful haydovchining xususiyatini bildiradi.
@1.3
Birds fly. Harakatni bildiruvchi so‘zni yozing. | fly | Fly — qushlar bajaradigan harakat.
Tanlang: The children ___ in the pool. (swim / happy) | swim | Egadan keyin harakat fe’li kerak.
Tushib qolgan holat fe’lini tanlang: She ___ happy. (is / happiness) | is | Is egani holat bilan bog‘laydigan fe’l.
She is calm. Holatni bog‘lovchi fe’lni yozing. | is | Is egani uning holati bilan bog‘laydi.
@1.4
They carry boxes. Olmoshni yozing. | They | They shaxslar nomi o‘rnida kelgan.
The windows are open. ___ are clean. Ega olmoshini yozing. | They | Ko‘plikdagi buyumlar uchun they ishlatiladi.
Faqat olmoshni tuzating: My mother is a nurse. He works here. | She | Mother ayol kishini bildiradi; she kerak.
The dog is hungry. The dog o‘rniga it qo‘yib gapni qayta yozing. Qisqartirmang. | It is hungry. | Birlikdagi hayvon nomi o‘rnida it kelishi mumkin.
@1.5
He never shouts. Chastota ravishini yozing. | never | Never harakat hech qachon bo‘lmasligini bildiradi.
Tanlang: The baby sleeps ___. (peaceful / peacefully) | peacefully | Ravish uxlash qanday kechishini bildiradi.
Faqat ravishni tuzating: She walks slow. Slowly shaklidan foydalaning. | slowly | Slowly harakatni tavsiflaydi.
Quick sifatidan ravish yasab bo‘shliqni to‘ldiring: He answered ___. | quickly | Quick ga -ly qo‘shilib ravish yasaladi.
@1.6
The picture is above the sofa. Predlogni yozing. | above | Above yuqorida joylashishni bildiradi.
Tanlang: The pencil is ___ the box. (inside / slowly) | inside | Inside buyumning quti ichida ekanini bildiradi.
Ma’noga mos predlogni tuzating: The shoes are above the door. Poyabzal eshik orqasida; above o‘rniga behind yoki between tanlang. | behind | Behind — orqasida.
The school is near the park. near the park birikmasidagi predlogni ajrating. | near | Near ikki joyning yaqinligini bildiradi.
@1.7
I stayed home because I was ill. Bog‘lovchini yozing. | because | Because sababni bildiruvchi gapni bog‘laydi.
Tanlang: Would you like tea ___ coffee? (or / under) | or | Or ikki variant orasidagi tanlovni bildiradi.
Sabab ma’nosiga mos bog‘lovchini yozing: I wore a coat but it was cold. But o‘rniga because yoki and tanlang. | because | Sovuq bo‘lgani palto kiyishning sababi.
And bilan bitta gap qiling: I have a pen. I have a ruler. I have ni bir marta ishlating, narsalar tartibini saqlang. | I have a pen and a ruler. | And ikki to‘ldiruvchini bog‘laydi.
@1.8
Ega olmoshini tanlang: us / we / our. | we | We ega vazifasida ishlatiladi.
My parents are busy. ___ work at a bank. Ega olmoshini yozing. | They | My parents ko‘plikdagi shaxslar.
Faqat ega olmoshini tuzating: Me am a student. | I | Am bilan ega shakli I ishlatiladi.
You and your sister are early. Egani bitta olmoshga almashtiring; gapni qisqartirmang. | You are early. | You birlik va ko‘plik uchun bir xil.
@1.9
Our new teacher speaks English. Egani to‘liq yozing. | Our new teacher | Kim gapiradi? — Our new teacher.
Tanlang: ___ grows vegetables. (My grandfather / In the garden) | My grandfather | Gapga harakat bajaruvchi ega kerak.
Egani ega olmoshi bilan tuzating: Her cooks dinner. Faqat to‘g‘ri olmoshni yozing. | She | Her to‘ldiruvchi, she esa ega shakli.
The red bus stops here. Egani it bilan almashtirib gapni yozing. | It stops here. | The red bus birlikdagi ega; it bilan almashtiriladi.
@1.10
Dad opens the window. To‘ldiruvchini to‘liq yozing. | the window | Nima ochiladi? — The window.
Tanlang: We ___ rice. (eat / hungry) | eat | Eat ega va to‘ldiruvchini bog‘lovchi harakat fe’li.
To‘ldiruvchi olmoshini tuzating: I see they. Faqat to‘g‘ri so‘zni yozing. | them | See dan keyin to‘ldiruvchi shakli them kerak.
Tartiblang: a letter / writes / Sara. | Sara writes a letter. | Tartib: ega, fe’l, to‘ldiruvchi.
@1.11
The sky is grey. Egani tavsiflovchi qismni yozing. | grey | Grey osmonning rangini bildiradi.
Tanlang: My cousin is ___. (a pilot / flies) | a pilot | A pilot egaga kasb tavsifini beradi.
Faqat tavsiflovchi so‘zni tuzating: The test is easily. | easy | Egani tavsiflash uchun easy sifati kerak.
Tartiblang: is / a musician / Her father. | Her father is a musician. | A musician ega haqidagi otli tavsif.
@1.12
Ega + fe’l + to‘ldiruvchi tartibini tanlang: A: Cats chase mice. B: Cats mice chase. Faqat harfni yozing. | A | Chase fe’li ega bilan to‘ldiruvchi orasida keladi.
Tanlang: ___ drinks milk. (The baby / Milk the) | The baby | Darak gap odatda ega bilan boshlanadi.
Tartibni tuzating: My uncle football plays. | My uncle plays football. | Plays egadan keyin, football undan so‘ng keladi.
Tartiblang; vaqtni oxiriga qo‘ying: every morning / We / the shop / open. | We open the shop every morning. | Ega, fe’l, to‘ldiruvchi, vaqt tartibi qo‘llanadi.
@1.13
Holat gapini tanlang: A: We are cold. B: We drink water. Faqat harfni yozing. | A | Are cold harakat emas, holat bildiradi.
Tanlang: The flowers ___ beautiful. (are / grow) | are | Sifatni egaga bog‘lash uchun be kerak.
Ortiqcha so‘zni olib tashlang: They are play tennis. | They play tennis. | Present Simple harakat gapida are kerak emas.
Be ni qo‘shib gapni tuzating: My father busy. Qisqartirmang. | My father is busy. | Busy sifatidan oldin is kerak.
@1.14
To‘g‘ri yozilgan variantni tanlang: A: london is big. B: London is big. Faqat harfni yozing. | B | Joy nomi bosh harf bilan boshlanadi.
Darak gap oxiridagi belgi nomini tanlang: We live here___ (full stop / question mark) | full stop | Darak gap nuqta bilan tugaydi.
To‘g‘ri variantni tanlang: A: Sara and I are friends. B: Sara and i are friends. Faqat harfni yozing. | A | I olmoshi gap ichida ham bosh harfda yoziladi.
She is a doctor. Savolga aylantirilganda oxirgi belgi nomini yozing: full stop / question mark. | question mark | Is she a doctor? so‘roq gap bo‘ladi.
@2.1
Mos juftlikni tanlang: A: I–am. B: I–is. Faqat harfni yozing. | A | I bilan am ishlatiladi.
My shoes ___ wet. (am / is / are) | are | Shoes ko‘plikda; are kerak.
Xatoni tuzating: My name are Dilnoza. | My name is Dilnoza.; My name's Dilnoza. | Name birlikdagi ega.
I am early. I o‘rniga we qo‘ying; qisqartirmang. | We are early. | We bilan am o‘rniga are keladi.
@2.2
Sifatli tasdiq gapni tanlang: A: He is polite. B: He is a waiter. Faqat harfni yozing. | A | Polite shaxsning xususiyatini bildiradi.
The oranges ___ sweet. (is / are) | are | Ko‘plikdagi ega are talab qiladi.
Xatoni tuzating: I is thirsty. | I am thirsty. | I bilan am ishlatiladi.
The room is clean. The room o‘rniga the rooms qo‘ying; qisqartirmang. | The rooms are clean. | Ko‘plikda is o‘rniga are kerak.
@2.3
Inkor sifatli gapni tanlang: A: We are not cold. B: We are cold. Faqat harfni yozing. | A | Not gapni inkor qiladi.
The water ___ not warm. (am / is / are) | is | Water birlik sifatida is bilan keladi.
Tartibni tuzating: They not are afraid. Qisqartirmang. | They are not afraid. | Not be fe’lidan keyin keladi.
Inkor qiling: I am angry. Qisqartirmang. | I am not angry. | Am dan keyin not qo‘shiladi.
@2.4
To‘g‘ri savolni tanlang: A: Is the floor dry? B: Does the floor dry? Sifatli be savoli uchun harfni yozing. | A | Dry sifatini is egaga bog‘laydi.
___ I late? (Am / Is / Are) | Am | I bilan savolda ham am ishlatiladi.
Savol tartibini tuzating: Are tired you? | Are you tired? | Be, ega, sifat tartibi kerak.
Savol qiling: The children are quiet. | Are the children quiet? | Are egadan oldinga chiqadi.
@2.5
Kasbni bildirgan tasdiq gapni tanlang: A: She is a baker. B: She is tired. Faqat harfni yozing. | A | A baker kasb nomidir.
I ___ a musician. (am / is / are) | am | I bilan am ishlatiladi.
Xatoni tuzating: His parents is farmers. | His parents are farmers. | Parents ko‘plikda.
He is a visitor. He o‘rniga they qo‘ying; otni ham ko‘plik qiling. Qisqartirmang. | They are visitors. | Ko‘plikda are va artiklsiz visitors keladi.
@2.6
Otli inkor gapni tanlang: A: I am not a dentist. B: I am not sleepy. Faqat harfni yozing. | A | Dentist ot, sleepy sifat.
She ___ not a manager. (am / is / are) | is | She bilan is not keladi.
Tartibni tuzating: They not are actors. Qisqartirmang. | They are not actors. | Inkor tartibi: ega, be, not, ot.
Inkor qiling: I am a tourist. Qisqartirmang. | I am not a tourist. | Am dan keyin not qo‘yiladi.
@2.7
To‘g‘ri savolni tanlang: A: Is she an architect? B: Does she an architect? Faqat harfni yozing. | A | Otli gap savoli is bilan boshlanadi.
___ I a member? (Am / Is / Are) | Am | I egasiga am mos keladi.
Savolni tuzating: Are he a cook? | Is he a cook? | He birlikda; is kerak.
Savol qiling: These women are scientists. | Are these women scientists? | Are ega oldiga o‘tadi.
@2.8
Tabiiy tartibni tanlang: A: a young farmer. B: a farmer young. Faqat harfni yozing. | A | Sifat otdan oldin keladi.
He is ___ honest man. (a / an) | an | Honest unli tovush bilan boshlanadi.
Tartibni tuzating: She is a teacher patient. | She is a patient teacher.; She's a patient teacher. | Patient sifati teacher dan oldin keladi.
They are artists. Artists oldiga talented qo‘shing; qisqartirmang. | They are talented artists. | Sifat ko‘plikda ham o‘zgarmaydi.
@2.9
To‘g‘ri inkorni tanlang: A: It is not a difficult task. B: It not is a difficult task. Faqat harfni yozing. | A | Not is dan keyin keladi.
We ___ not careless drivers. (is / are) | are | We bilan are ishlatiladi.
Tartibni tuzating: He is not a boy rude. | He is not a rude boy.; He isn't a rude boy.; He's not a rude boy. | Sifat ot oldiga qo‘yiladi.
Inkor qiling: I am a bad player. Qisqartirmang. | I am not a bad player. | Not be dan keyin, ot birikmasidan oldin keladi.
@2.10
To‘g‘ri savolni tanlang: A: Is this an old map? B: Does this an old map? Faqat harfni yozing. | A | Be bilan tuzilgan gapda is oldinga chiqadi.
___ they good singers? (Is / Are) | Are | They bilan are ishlatiladi.
Tartibni tuzating: Is a careful driver he? | Is he a careful driver? | Egadan keyin sifatli ot birikmasi keladi.
Savol qiling: This is a useful tool. | Is this a useful tool? | Is egadan oldin keladi.
@2.11
Joyni bildirgan gapni tanlang: A: He is in the garden. B: He is cheerful. Faqat harfni yozing. | A | In the garden joyni bildiradi.
I ___ at the bus stop. (am / is / are) | am | I bilan am ishlatiladi.
Xatoni tuzating: The keys is on the shelf. | The keys are on the shelf. | Keys ko‘plikda; are kerak.
The nurse is in the ward. The nurse o‘rniga the nurses qo‘ying; qisqartirmang. | The nurses are in the ward. | Ko‘plikdagi ega are bilan keladi.
@2.12
To‘g‘ri inkorni tanlang: A: They are not upstairs. B: They do not upstairs. Faqat harfni yozing. | A | Joy gapida are not ishlatiladi.
My coat ___ not in the car. (is / are) | is | Coat birlikdagi ot.
Tartibni tuzating: I not am at the airport. Qisqartirmang. | I am not at the airport. | Not am dan keyin keladi.
Inkor qiling: The plates are on the table. Qisqartirmang. | The plates are not on the table. | Are dan keyin not qo‘shiladi.
@2.13
To‘g‘ri joy savolini tanlang: A: Are the bags downstairs? B: Do the bags downstairs? Faqat harfni yozing. | A | Joy gapida be savol boshiga chiqadi.
___ I in the right room? (Am / Is / Are) | Am | I bilan am ishlatiladi.
Savolni tuzating: Is your parents in town? | Are your parents in town? | Parents ko‘plikdagi ega.
Savol qiling: The dog is outside. | Is the dog outside? | Is ega oldiga chiqadi.
@2.14
Yoshni so‘raydigan iborani tanlang: ___ is your son? — Six. (How old / Where) | How old | How old yoshni so‘raydi.
___ are you today? — Fine, thanks. (How / Who) | How | How hol-ahvolni so‘raydi.
Tartibni tuzating: Where your shoes are? | Where are your shoes? | Savol so‘zi, be, ega tartibi kerak.
Where bilan joyni so‘rang: The tickets are in my pocket. | Where are the tickets? | Joy birikmasi o‘rnini where egallaydi.
@2.15
Is the lesson easy? Ijobiy qisqa javobni tanlang: A: Yes, it is. B: Yes, it does. Faqat harfni yozing. | A | Is savoliga is bilan javob beriladi.
Are the shops open? — Yes, they ___. | are | They uchun are kerak.
Qisqa javobni tuzating: Am I right? — Yes, you am. Faqat javobni yozing. | Yes, you are. | Savoldagi I javobda you bo‘ladi.
Are you and Malika neighbours? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we are not. | Ikki kishi nomidan we ishlatiladi.
@2.16
She’s clever. She’s ning to‘liq shaklini yozing. | She is | Sifat oldidagi ’s — is qisqartmasi.
We are friends. We are ning qisqartmasini yozing. | We're | We are qisqartmasi we’re bo‘ladi.
Qisqartmani tuzating: You'r welcome. Faqat qisqartmani yozing. | You're | You are qisqartmasida e saqlanadi.
It isn't heavy. Qisqartmani ochib, butun gapni yozing. | It is not heavy. | Isn’t — is not qisqartmasi.
@2.17
To‘g‘ri birikmani tanlang: a actor / an actor. | an actor | Actor unli tovush bilan boshlanadi.
My cousin is ___ nurse. (a / an) | a | Nurse undosh tovush bilan boshlanadi.
Faqat artiklni tuzating: He is an student. | a | Student oldidan a keladi.
She is a pilot. Pilot o‘rniga engineer qo‘ying; artiklni moslang, qisqartirmang. | She is an engineer. | Engineer oldidan an keladi.
@2.18
To‘g‘ri variantni tanlang: A: They are there. B: They are at there. Faqat harfni yozing. | A | There oldidan at qo‘yilmaydi.
The pupils are ___ class. (in / to / on) | in | In class — darsda.
Faqat predlogni tuzating: We are in home. Uyda ma’nosida in o‘rniga at yoki on tanlang. | at | Uyda deganda at home ishlatiladi.
The doctor is at the hospital. At the hospital o‘rniga there qo‘ying; qisqartirmang. | The doctor is there. | There predlogsiz joyni almashtiradi.
@3.1
Birlikdagi otni tanlang: woman / women. | woman | Woman bitta ayolni bildiradi.
One ___ is missing. (button / buttons) | button | One dan keyin birlik kerak.
Faqat otni tuzating: a windows. | window | A birlikdagi ot bilan keladi.
Potatoes ni birlikka aylantiring; faqat otni yozing. | potato | Birlik shaklida -es olib tashlanadi.
@3.2
To‘g‘ri ko‘plikni tanlang: buses / buss. | buses | Bus ga -es qo‘shiladi.
Three ___ are on the desk. (watch; ko‘plik) | watches | -ch bilan tugagan otga -es qo‘shiladi.
Ko‘plikni tuzating: dish → dishs. Faqat to‘g‘ri shaklni yozing. | dishes | -sh dan keyin -es qo‘shiladi.
Cup so‘zini ko‘plikka aylantiring. | cups | Oddiy ko‘plik -s bilan yasaladi.
@3.3
To‘g‘ri ko‘plikni tanlang: toys / toies. | toys | Unli + y bo‘lsa faqat -s qo‘shiladi.
Two ___ are asleep. (baby; ko‘plik) | babies | Undosh + y ko‘plikda -ies bo‘ladi.
Ko‘plikni tuzating: knife → knifes. | knives | Knife ko‘pligida -fe o‘rniga -ves keladi.
Roof so‘zini ko‘plikka aylantiring. | roofs | Roof istisno: -f saqlanib -s qo‘shiladi.
@3.4
To‘g‘ri ko‘plikni tanlang: mice / mouses. | mice | Mouse ning istisno ko‘pligi mice.
Both ___ are wet. (foot; ko‘plik) | feet | Foot ning ko‘pligi feet.
Ko‘plikni tuzating: man → mans. | men | Man ning ko‘pligi men.
Sheep so‘zini ko‘plikka aylantiring. | sheep | Sheep birlik va ko‘plikda bir xil.
@3.5
Sanaladigan otni tanlang: bread / suitcase / rice. | suitcase | Suitcase ni dona bilan sanash mumkin.
We need four ___. (bottle / bottles) | bottles | Four dan keyin ko‘plik kerak.
Faqat otni tuzating: two sandwich. | sandwiches | Ikki dona uchun ko‘plik -es kerak.
A ticket birikmasini three bilan qayta yozing. | three tickets | Son bilan a olib tashlanib ot ko‘plik bo‘ladi.
@3.6
Sanalmaydigan otni tanlang: desk / luggage / coin. | luggage | Luggage umumiy yukni bildiradi.
There ___ some furniture upstairs. (is / are) | is | Furniture sanalmaydi va is bilan keladi.
Faqat otni tuzating: This news is useful, but these advices are not. Advices ning to‘g‘ri shaklini yozing. | advice | Advice odatda ko‘plik -s olmaydi.
Milk ni a glass of bilan sanaladigan birikmaga aylantiring. | a glass of milk | Idish nomi orqali sut miqdori sanaladi.
@3.7
Tovushga mos birikmani tanlang: a European city / an European city. | a European city | European boshida /j/ undosh tovushi bor.
___ umbrella (a / an) | an | Umbrella unli tovush bilan boshlanadi.
Faqat artiklni tuzating: a honest answer. | an | Honest dagi h talaffuz qilinmaydi.
A book birikmasida book o‘rniga old book qo‘ying; artiklni moslang. | an old book | Artikl keyingi old so‘zining tovushiga moslanadi.
@3.8
Noma’lum narsani ilk bor tilga oling: I saw ___ fox. (a / the) | a | Qaysi tulki ekani hali aniqlanmagan.
Yangi, hali aytilmagan narsa: She found ___ envelope. (an / the) | an | Birinchi tilga olishda an ishlatiladi.
Noma’lum narsani ilk bor aytishda artiklni tuzating: I rented the bicycle yesterday. The o‘rniga a yoki an yozing. | a | Bicycle undosh bilan boshlanadi, narsa hali ma’lum emas.
Ikki bo‘shliqni vergul bilan to‘ldiring: I saw ___ dog. ___ dog was brown. (a / the) | a, the | Birinchi aytishda a, takror aytishda the keladi.
@3.9
We bought a lamp. ___ lamp is bright. (A / The) | The | Avval aytilgan lampaga the qo‘yiladi.
Uyimizdagi yagona oshxona: Mum is in ___ kitchen. (a / the) | the | Qaysi oshxona ekani suhbatdoshlarga ma’lum.
Ikkinchi gapdagi artiklni tuzating: I met a sailor. A sailor told me a story. Faqat artiklni yozing. | The | Ikkinchi gapda ayni dengizchi qayta tilga olinmoqda.
Noma’lum a key o‘rniga ikkimiz biladigan aynan o‘sha kalitni ayting; artiklli birikmani yozing. | the key | Ma’lum narsa uchun the ishlatiladi.
@3.10
Umuman hayvonlar haqida to‘g‘ri gapni tanlang: A: Elephants are large. B: An elephants are large. Faqat harfni yozing. | A | Umumiy ko‘plik artiklsiz keladi.
Umuman tillar haqida: ___ languages change. (a / the / 0) | 0 | Umumiy ko‘plik oldidan artikl kerak emas.
Umuman velosipedlar haqida artiklni olib tashlab yozing: The bicycles are useful. | Bicycles are useful. | Barcha velosipedlar umumiy sinf sifatida nazarda tutilgan.
A tiger is an animal. Umumiy ko‘plikka aylantiring. | Tigers are animals. | Ikkala ot ko‘plikda va artiklsiz keladi.
@3.11
Umuman non haqida tanlang: A: Bread is food. B: A bread is food. Faqat harfni yozing. | A | Bread sanalmaydigan ot sifatida artiklsiz keladi.
Umuman bilim haqida: ___ knowledge is valuable. (a / the / 0) | 0 | Umumiy sanalmaydigan ot oldidan artikl kerak emas.
Umuman guruch haqida artiklni olib tashlang: The rice is a common food. | Rice is a common food. | Umumiy rice artiklsiz ishlatiladi.
Gold is expensive. Gold o‘rniga silver qo‘yib yozing. | Silver is expensive. | Umumiy metall nomi artiklsiz keladi.
@3.12
Kasb uchun tanlang: He is ___ electrician. (a / an / 0) | an | Electrician unli tovush bilan boshlanadi.
My sisters are ___ accountants. (a / an / 0) | 0 | Ko‘plikdagi kasb nomi a/an olmaydi.
Yetishmayotgan artiklni qo‘shing: She is journalist. Qisqartirmang. | She is a journalist. | Birlikdagi sanaladigan kasb nomiga a kerak.
He is a vet. He o‘rniga they qo‘ying; kasb nomini moslang, qisqartirmang. | They are vets. | Ko‘plik kasb nomida a olib tashlanadi.
@3.13
Bir bolaning shlyapasi: the boy’s hat / the boys’ hat. To‘g‘ri birikmani yozing. | the boy's hat | Birlikdagi egaga ’s qo‘shiladi.
My ___ bicycle is red. (brother’s / brothers) Bitta akamning velosipedi. | brother's | Egalik uchun ’s kerak.
Egalik belgisini tuzating: my mothers car. Bitta ona nazarda tutilgan. | my mother's car | Mother birlikda; ’s qo‘shiladi.
’s bilan qayta yozing: the office of the doctor. | the doctor's office | Birlikdagi doctor ga ’s qo‘shiladi.
@3.14
Uch qizning xonasi: the girls’ room / the girl’s room. To‘g‘ri birikmani yozing. | the girls' room | -s bilan tugagan ko‘plikdan keyin apostrof keladi.
The ___ coats are blue. (nurses’ / nurse’s) Bir nechta hamshira nazarda tutilgan. | nurses' | Ko‘plik egalikda apostrof -s dan keyin qo‘yiladi.
Bir nechta o‘yinchining sumkalari: the player's bags. Egalikni tuzatib birikmani yozing. | the players' bags | Players ko‘plik, shuning uchun players’.
Egalik bilan qayta yozing: the nests of the birds. | the birds' nests | Birds ko‘plikda va -s bilan tugaydi.
@3.15
Mos birikmani tanlang: a loaf of bread / a loaf of water. | a loaf of bread | Loaf non miqdorini bildiradi.
A ___ of tea. (cup / slice) | cup | Tea uchun cup idish nomi mos.
Bog‘lovchi so‘zni tuzating: a bottle to juice. Birikmani yozing. | a bottle of juice | Miqdor birikmasida of ishlatiladi.
A piece of paper ni two bilan qayta yozing. | two pieces of paper | Miqdor so‘zi piece ko‘plik bo‘ladi, paper o‘zgarmaydi.
@3.16
Tish cho‘tkasi uchun tartibni tanlang: toothbrush / brushtooth. | toothbrush | Inglizchada belgilovchi tooth oldin keladi.
Poyezd bekati: train ___. (station / room) | station | Train station — poyezd bekati.
Tartibni tuzating: a brush hair. | a hairbrush | Hairbrush bir so‘zli qo‘shma ot.
School bag birikmasini ko‘plikka aylantiring. | school bags | Asosiy ot bag ko‘plik bo‘ladi.
""", r"""
@4.1
To‘ldiruvchi olmoshini tanlang: he / him / his. | him | Him fe’l yoki predlogdan keyin to‘ldiruvchi bo‘ladi.
This message is for Tom and me. Please send it to ___. | us | Tom and me o‘rniga us ishlatiladi.
Faqat olmoshni tuzating: Listen to I. | me | To predlogidan keyin me kerak.
I like these songs. These songs o‘rniga olmosh qo‘yib gapni yozing. | I like them. | Ko‘plikdagi to‘ldiruvchi them bilan almashtiriladi.
@4.2
To‘g‘ri gapni tanlang: A: They help us. B: Them help we. Faqat harfni yozing. | A | They ega, us to‘ldiruvchi shakli.
___ can hear ___. (We / Us; he / him) Javoblarni vergul bilan yozing. | We, him | Harakat bajaruvchi we, to‘ldiruvchi him.
Ikki olmoshni tuzatib yozing: Her knows they. | She knows them. | Ega she, to‘ldiruvchi them bo‘ladi.
Tom phones Anna. Tom va Anna o‘rniga olmosh qo‘yib yozing. | He phones her. | He ega, her to‘ldiruvchi vazifasida.
@4.3
Ot oldidan keladigan shaklni tanlang: mine / my. | my | My egalik aniqlovchisi bo‘lib ot oldida keladi.
These boys have a kite. It is ___ kite. | their | Ko‘plikdagi egalar uchun their ishlatiladi.
Faqat egalik so‘zini tuzating: She has a sister. His sister is ten. | Her | She ga mos egalik aniqlovchisi her.
I own this camera. This is ___ camera. | my | I ning egalik aniqlovchisi my.
@4.4
Otsiz mustaqil ishlatiladigan shaklni tanlang: our / ours. | ours | Ours dan keyin ot takrorlanmaydi.
That umbrella belongs to you. It is ___. | yours | You ga mos mustaqil egalik olmoshi yours.
Faqat egalik so‘zini tuzating: The red bicycle is her. | hers | Ot ortidan mustaqil egalik uchun hers kerak.
This is our house. This house is ___ shaklida to‘liq yozing; qisqartirmang. | This house is ours. | Our house o‘rnini ours egallaydi.
@4.5
To‘g‘ri birikmani tanlang: their car / theirs car. | their car | Ot oldidan their keladi.
This is ___ desk; that one is ___. (my / mine; your / yours) Vergul bilan yozing. | my, yours | My ot oldida, yours esa otsiz keladi.
Faqat egalik so‘zini tuzating: Ours team won. | Our | Team oldida our aniqlovchisi kerak.
Those are her gloves. Those gloves are ___ shaklida to‘liq yozing; qisqartirmang. | Those gloves are hers. | Her gloves o‘rnida mustaqil hers ishlatiladi.
@4.6
Qo‘lingizdagi bitta kalit: this key / that key. | this key | Yaqindagi birlik uchun this.
Uzoqdagi bitta qayiq: ___ boat is small. (This / That) | That | Uzoqdagi birlik uchun that.
Faqat ishorani tuzating: These cup is mine. Yaqindagi bitta piyola. | This | Cup birlikda, this kerak.
That is a mountain. Tog‘ endi yoningizda: that o‘rniga this qo‘yib yozing; qisqartirmang. | This is a mountain. | Yaqin birlik narsa this bilan ko‘rsatiladi.
@4.7
Yoningizdagi ikki qalam: these pencils / those pencils. | these pencils | Yaqin ko‘plik uchun these.
Uzoqdagi uylar: ___ houses are new. (These / Those) | Those | Uzoq ko‘plik uchun those.
Faqat ishorani tuzating: This shoes are comfortable. Oyoqingizdagi poyabzal. | These | Ko‘plik shoes bilan these kerak.
That is a star. Ko‘plikka aylantiring; qisqartirmang. | Those are stars. | That → those, is → are, star → stars.
@4.8
Egalik savolini tanlang: A: Whose coat is this? B: Who is this? Faqat harfni yozing. | A | Whose narsa kimga tegishli ekanini so‘raydi.
___ laptop is on the desk? — It is Farida’s. (Who / Whose) | Whose | Farida’s javobi egalikni bildiradi.
Faqat savol so‘zini tuzating: Who's keys are these? | Whose | Whose egalikni, who’s esa who is ni bildiradi.
Whose bilan savol qiling: These are Aziz’s boots. Boots ni savolda saqlang. | Whose boots are these? | Whose dan keyin egalik qilinayotgan ot keladi.
@4.9
Ko‘plikdagi ot o‘rnini tanlang: I like the green ___. (one / ones) Apples nazarda tutilgan. | ones | Ko‘plik ot o‘rniga ones keladi.
This chair is broken. Use that ___. (one / ones) | one | Bitta chair o‘rnini one egallaydi.
Faqat o‘rinbosar so‘zni tuzating: These hats are cheap, but those one are expensive. | ones | Those ko‘plikdagi ones bilan keladi.
I prefer the black jacket. Jacket o‘rniga one qo‘yib yozing. | I prefer the black one. | One takrorlanadigan birlik otni almashtiradi.
@4.10
Shaxsni bildiruvchi so‘zni tanlang: somebody / something. | somebody | Somebody noma’lum shaxsni bildiradi.
I knocked, but ___ answered; the house was empty. (somebody / nobody) | nobody | Hech kim javob bermagan, shuning uchun nobody.
Ikki inkorni tuzating; nobody o‘rniga anybody ishlating: I didn't see nobody. Qisqartmani saqlang. | I didn't see anybody. | Didn't bilan anybody ishlatiladi.
I did not invite anybody. Ma’noni saqlab, nobody bilan qayta yozing. | I invited nobody. | Nobody o‘zi inkor bildiradi; fe’l tasdiq shakliga o‘tadi.
@4.11
Narsani bildirgan so‘zni tanlang: anything / anybody. | anything | Anything narsa yoki ishni bildiradi.
The bag isn't empty: there is ___ inside. (something / nothing) | something | Ichida biror narsa borligi aytilgan.
Ikki inkorni tuzating: We don't need nothing. Nothing o‘rniga anything qo‘ying; qisqartmani saqlang. | We don't need anything. | Don't bilan anything keladi.
There is not anything in the drawer. Nothing bilan qayta yozing; qisqartirmang. | There is nothing in the drawer. | Nothing o‘zi inkor ma’nosini bildiradi.
@4.12
To‘g‘ri birikmani tanlang: every child / every children. | every child | Every dan keyin birlik ot keladi.
Each of these rooms ___ a window. (has / have) | has | Each birlik fe’l bilan ishlatiladi.
Faqat otni tuzating: Every players is ready. | player | Every dan keyin ot birlikda bo‘ladi.
All the buses stop here. Every bilan boshlang; ma’noni saqlang. | Every bus stops here. | Every birlik bus va stops bilan keladi.
@4.13
He made it ___. Yordamsiz bajargan: himself / herself. | himself | He ga mos o‘zlik olmoshi himself.
The children dressed ___. (themselves / ourselves) | themselves | They ga mos o‘zlik olmoshi themselves.
Faqat olmoshni tuzating: I cut yourself while cooking. | myself | I ning o‘zlik shakli myself.
She repaired the radio without help. Without help o‘rniga herself qo‘yib yozing. | She repaired the radio herself. | Herself ishni o‘zi bajarganini ta’kidlaydi.
@4.14
O‘zaro harakatni tanlang: A: They hugged each other. B: They dressed themselves. Faqat harfni yozing. | A | Each other harakatning ikki tomonga yo‘nalganini bildiradi.
Ali helps Vali, and Vali helps Ali. They help ___. (each other / themselves) | each other | Yordam o‘zaro ko‘rsatilmoqda.
O‘zaro ma’noni tiklang: The sisters talk to themselves on the phone. Themselves o‘rniga each other qo‘yib yozing. | The sisters talk to each other on the phone. | Each other ikki opa-singil orasidagi suhbatni bildiradi.
Sara trusts Nina. Nina trusts Sara. The two friends bilan boshlab, each other bilan bir gap qiling. | The two friends trust each other. | Ikki yo‘nalishdagi ishonch each other bilan ifodalanadi.
@5.1
To‘g‘ri gapni tanlang: A: There is a pond here. B: There are a pond here. Faqat harfni yozing. | A | A pond birlikda; there is kerak.
There ___ some sugar in the bowl. (is / are) | is | Sugar sanalmaydigan ot, is bilan keladi.
Faqat fe’lni tuzating: There are a clock above the door. | is | A clock birlikda.
Tartiblang: in the hall / a sofa / There / is. | There is a sofa in the hall. | There is birlikdagi narsaning borligini bildiradi.
@5.2
To‘g‘ri gapni tanlang: A: There are six plates. B: There is six plates. Faqat harfni yozing. | A | Six plates ko‘plikda.
There ___ many stars tonight. (is / are) | are | Ko‘plik uchun are ishlatiladi.
Faqat fe’lni tuzating: There is two entrances. | are | Two entrances ko‘plikdagi ot birikmasi.
There is a tree in the yard. A tree o‘rniga five trees qo‘yib yozing. | There are five trees in the yard. | Ko‘plikka o‘tganda is → are bo‘ladi.
@5.3
To‘g‘ri inkorni tanlang: A: There isn't any juice. B: There aren't any juice. Faqat harfni yozing. | A | Juice sanalmaydi; isn't mos.
There ___ any blankets here. (isn't / aren't) | aren't | Blankets ko‘plikda.
Faqat yordamchini tuzating: There don't any buses on Sundays. Don't o‘rniga aren't yoki isn't yozing. | aren't | Borlik inkori ko‘plikda aren't bilan yasaladi.
Inkor qiling; some o‘rniga any qo‘ying: There is some butter. Qisqartirmang. | There is not any butter. | Sanalmaydigan butter uchun is not any kerak.
@5.4
To‘g‘ri savolni tanlang: A: Are there any lockers? B: Do there any lockers? Faqat harfni yozing. | A | There are savolda are there bo‘ladi.
___ there a bridge over the river? (Is / Are) | Is | A bridge birlikda.
Savol tartibini tuzating: Is a post office there near here? | Is there a post office near here? | Borlik savoli is there bilan boshlanadi.
Yes/no savol qiling: There are two lifts in the building. | Are there two lifts in the building? | Are there ko‘plikdagi borlikni so‘raydi.
@5.5
To‘g‘ri savolni tanlang: A: How many desks are there? B: How many desk is there? Faqat harfni yozing. | A | How many ko‘plik ot va are there bilan keladi.
How many students ___ in your group? (are there / there are) | are there | Savolda are there tartibi kerak.
Faqat otni tuzating: How many chair are there downstairs? | chairs | How many dan keyin ko‘plik kerak.
How many bilan sonni so‘rang: There are eight pages in this booklet. | How many pages are there in this booklet? | Eight o‘rniga how many qo‘yiladi.
@5.6
Is there any water? Ijobiy qisqa javobni tanlang: A: Yes, there is. B: Yes, it is. Faqat harfni yozing. | A | Borlik savolida there javobda saqlanadi.
Are there any trees? — Yes, there ___. | are | Ko‘plik uchun are ishlatiladi.
Qisqa javobni tuzating: Is there a garage? — No, there aren't. Faqat javobni yozing; qisqartirmang. | No, there is not. | Birlik savoliga is not bilan javob beriladi.
Are there any tickets left? Ijobiy qisqa javob yozing. | Yes, there are. | Are there savoliga there are bilan javob beriladi.
@5.7
Yangi narsaning borligini ayting: ___ is a fountain in the square. (There / It) | There | There yangi narsaning mavjudligini bildiradi.
There is a fountain in the square. ___ is very old. (There / It) | It | Oldin aytilgan fountain o‘rnida it keladi.
Faqat birinchi so‘zni tuzating: It is a problem with the lock. Borlik ma’nosida there dan foydalaning. | There | There is muammo borligini bildiradi.
There is a hotel nearby. The hotel is cheap. Ikkinchi gapdagi the hotel o‘rniga it qo‘yib, faqat ikkinchi gapni yozing; qisqartirmang. | It is cheap. | It avval tilga olingan hotel ga ishora qiladi.
@5.8
To‘g‘ri gapni tanlang: A: The school has a gym. B: The school have a gym. Faqat harfni yozing. | A | Birlikdagi school bilan has keladi.
My grandparents ___ a small farm. (have / has) | have | Ko‘plikdagi ega have bilan keladi.
Faqat fe’lni tuzating: I has a question. | have | I bilan have ishlatiladi.
We have a balcony. We o‘rniga she qo‘yib yozing. | She has a balcony. | Uchinchi shaxs birlikda has kerak.
@5.9
To‘g‘ri inkorni tanlang: A: They don't have a map. B: They don't has a map. Faqat harfni yozing. | A | Don't dan keyin have asosiy shakli keladi.
This room ___ have a window. (don't / doesn't) | doesn't | This room birlikda.
Faqat asosiy fe’lni tuzating: She doesn't having a laptop. | have | Doesn't dan keyin have kerak.
Inkor qiling, have got ishlatmang: The twins have a pet. Qisqartirmang. | The twins do not have a pet. | Ko‘plik inkori do not have bilan yasaladi.
@5.10
To‘g‘ri savolni tanlang: A: Does the flat have a lift? B: Does the flat has a lift? Faqat harfni yozing. | A | Does dan keyin have ishlatiladi.
___ we have enough food? (Do / Does) | Do | We bilan do ishlatiladi.
Faqat yordamchini tuzating: Does your friends have bicycles? | Do | Friends ko‘plikda; do kerak.
Have got ishlatmasdan savol qiling: The library has a café. | Does the library have a café? | Has savolda does ... have bo‘ladi.
@5.11
To‘g‘ri gapni tanlang: A: He has got a torch. B: He have got a torch. Faqat harfni yozing. | A | He bilan has got ishlatiladi.
I ___ got a headache. (have / has) | have | I bilan have got keladi.
Faqat yordamchini tuzating: The boys has got new boots. | have | The boys ko‘plikda.
They have a tent. Have got bilan qayta yozing; qisqartirmang. | They have got a tent. | Egalik have got bilan ham ifodalanadi.
@5.12
To‘g‘ri inkorni tanlang: A: We haven't got a ladder. B: We don't got a ladder. Faqat harfni yozing. | A | Have got inkorida haven't ishlatiladi.
The dog ___ got a collar. (haven't / hasn't) | hasn't | Birlikdagi dog bilan hasn't got keladi.
Faqat yordamchini tuzating: You hasn't got my number. | haven't | You bilan haven't kerak.
Inkor qiling: They have got a reservation. Qisqartirmang. | They have not got a reservation. | Not have dan keyin keladi.
@5.13
To‘g‘ri savolni tanlang: A: Has your sister got a car? B: Does your sister got a car? Faqat harfni yozing. | A | Have got savolida has oldinga chiqadi.
___ the children got lunch boxes? (Have / Has) | Have | Children ko‘plikda.
Qisqa javobni tuzating: Have you got a ruler? — Yes, I do. Faqat javobni yozing. | Yes, I have. | Have savoliga have bilan javob beriladi.
Savol qiling: The house has got a cellar. | Has the house got a cellar? | Has ega oldiga o‘tadi, got saqlanadi.
@5.14
Buyruqni tanlang: A: Turn left. B: He turns left. Faqat harfni yozing. | A | Buyruqda ega aytilmaydi va fe’l asosiy shaklda keladi.
___ careful with that glass. (Be / Is) | Be | Holatga oid buyruq be bilan boshlanadi.
Faqat fe’lni tuzating: Opens the gate, please. | Open | Buyruqda -s qo‘shilmaydi.
You must keep quiet. Buyruqqa aylantiring; please qo‘shmang. | Keep quiet. | Buyruq fe’lning asosiy shaklidan boshlanadi.
@5.15
Salbiy buyruqni tanlang: A: Don't park here. B: You don't park here. Faqat harfni yozing. | A | Don't + fe’l taqiqni bildiradi.
Don't ___ afraid. (be / are) | be | Don't dan keyin be asosiy shaklda keladi.
Faqat fe’lni tuzating: Don't opens that box. | open | Don't dan keyin -s ishlatilmaydi.
Inkor buyruq qiling: Feed the animals. Qisqartirmang. | Do not feed the animals. | Do not + fe’l salbiy buyruq yasaydi.
@5.16
Birgalikdagi taklifni tanlang: A: Let's go for a walk. B: Go for a walk. Faqat harfni yozing. | A | Let's so‘zlovchini ham harakatga qo‘shadi.
Let's ___ a taxi. (take / taking) | take | Let's dan keyin asosiy fe’l shakli keladi.
Tartibni tuzating: Let's be not noisy. | Let's not be noisy. | Inkor tartibi let's not + fe’l.
Let's sit outside. Let's not bilan inkor taklif qiling. | Let's not sit outside. | Not let's dan keyin qo‘yiladi.
@6.1
To‘g‘ri shaklni tanlang: We ___ near the river. (live / lives) | live | We bilan fe’lga -s qo‘shilmaydi.
Present Simple: I ___ vegetables in my garden. (grow) | grow | I bilan asosiy fe’l shakli keladi.
Faqat fe’lni tuzating: You speaks clearly. | speak | You bilan speak ishlatiladi.
She works in a bank. She o‘rniga they qo‘yib yozing. | They work in a bank. | Ko‘plikdagi ega bilan -s tushadi.
@6.2
To‘g‘ri shaklni tanlang: My dog ___ a lot. (sleep / sleeps) | sleeps | Uchinchi shaxs birlikda -s kerak.
Present Simple: Sara ___ the piano on Fridays. (play) | plays | She ma’nosidagi Sara bilan plays keladi.
Faqat fe’lni tuzating: The train leave at noon. | leaves | The train birlikdagi ega.
We cook dinner. We o‘rniga he qo‘yib yozing. | He cooks dinner. | He bilan fe’lga -s qo‘shiladi.
@6.3
To‘g‘ri shaklni tanlang: He ___ hard. (trys / tries) | tries | Undosh + y → -ies.
Present Simple: She ___ the ball. (catch) | catches | -ch dan keyin -es qo‘shiladi.
Faqat fe’lni tuzating: He plaies chess. | plays | Unli + y bo‘lsa faqat -s qo‘shiladi.
Fix fe’lini it egasiga mos Present Simple shaklida yozing. | fixes | -x bilan tugagan fe’lga -es qo‘shiladi.
@6.4
To‘g‘ri shaklni tanlang: She ___ two brothers. (haves / has) | has | Have ning uchinchi shaxs shakli has.
Present Simple: The caretaker ___ the cleaning. (do) | does | Do ning birlik shakli does.
Faqat fe’lni tuzating: He gos to bed early. | goes | Go ga -es qo‘shiladi.
I have lunch at one. I o‘rniga she qo‘yib yozing. | She has lunch at one. | Have uchinchi shaxsda has bo‘ladi.
@6.5
To‘g‘ri inkorni tanlang: A: I don't smoke. B: I doesn't smoke. Faqat harfni yozing. | A | I bilan don't ishlatiladi.
We ___ live near the sea. (don't / doesn't) | don't | We bilan don't keladi.
Faqat asosiy fe’lni tuzating: They don't watches TV. | watch | Don't dan keyin fe’l asosiy shaklda keladi.
Inkor qiling: You need a ticket. Qisqartirmang. | You do not need a ticket. | You uchun inkor do not bilan yasaladi.
@6.6
To‘g‘ri inkorni tanlang: A: The baby doesn't walk. B: The baby don't walk. Faqat harfni yozing. | A | Birlikdagi ega doesn't bilan keladi.
It ___ rain much here. (don't / doesn't) | doesn't | It bilan doesn't ishlatiladi.
Faqat asosiy fe’lni tuzating: Omar doesn't studies French. | study | Doesn't dan keyin -ies yo‘q, study kerak.
Inkor qiling: The bus passes our house. Qisqartirmang. | The bus does not pass our house. | Does not dan keyin pass asosiy shaklda keladi.
@6.7
To‘g‘ri savolni tanlang: A: Do the children like soup? B: Does the children like soup? Faqat harfni yozing. | A | Children ko‘plikda; do kerak.
___ I need an umbrella? (Do / Does) | Do | I bilan do ishlatiladi.
Savolni tuzating: Do they lives upstairs? | Do they live upstairs? | Do dan keyin fe’lga -s qo‘shilmaydi.
Yes/no savol qiling: We start at eight. We ni saqlang. | Do we start at eight? | Do ega oldiga qo‘yiladi.
@6.8
To‘g‘ri savolni tanlang: A: Does it cost much? B: Does it costs much? Faqat harfni yozing. | A | Does dan keyin cost asosiy shaklda keladi.
___ your sister teach maths? (Do / Does) | Does | Your sister birlikdagi ega.
Savolni tuzating: Do the museum open on Mondays? | Does the museum open on Mondays? | The museum bilan does kerak.
Yes/no savol qiling: He carries a notebook. | Does he carry a notebook? | Carries savolda carry bo‘ladi.
@6.9
To‘g‘ri savolni tanlang: A: What does she sell? B: What she sells? Faqat harfni yozing. | A | Wh-savolda does ega oldiga qo‘yiladi.
When ___ your lessons end? (do / does) | do | Lessons ko‘plikda.
Savolni tuzating: How does he travels? | How does he travel? | Does dan keyin travel asosiy shakli kerak.
What bilan to‘ldiruvchini so‘rang: They grow tomatoes. | What do they grow? | Tomatoes o‘rniga what keladi, do qo‘shiladi.
@6.10
Does the door close properly? Ijobiy qisqa javobni tanlang: A: Yes, it does. B: Yes, it is. Faqat harfni yozing. | A | Does savoliga does bilan javob beriladi.
Do these shoes fit? — No, they ___. Qisqartma yozing. | don't | Ko‘plikdagi ega uchun don't kerak.
Javobni tuzating: Does she swim? — Yes, she do. Faqat javobni yozing. | Yes, she does. | She bilan does keladi.
Do you and your brother share a room? We bilan ijobiy qisqa javob yozing. | Yes, we do. | Ikki kishi nomidan we do deyiladi.
@6.11
Narsa yoki faoliyatni so‘rang: ___ do you teach? — History. (What / Where / When) | What | What fan yoki narsani so‘raydi.
___ do the birds go in winter? — South. (What / Where / When) | Where | Where yo‘nalish yoki joyni so‘raydi.
Faqat savol so‘zini tuzating: Where do you wake up? — At seven. Where o‘rniga When yoki What yozing. | When | At seven vaqtni bildiradi.
What bilan to‘ldiruvchini so‘rang: She reads magazines. | What does she read? | What to‘ldiruvchi o‘rnini egallaydi.
@6.12
Odatni Present Simpleda ifodalang: He ___ his teeth twice a day. (brush / brushes) | brushes | Takroriy ish va birlik ega uchun brushes.
Present Simple: Every evening, the guards ___ the gates. (lock) | lock | Takroriy ish ko‘plik ega bilan asosiy shaklda keladi.
Odatni Present Simplega tuzating: I am walking to work every day. | I walk to work every day. | Kundalik odat uchun Present Simple ishlatiladi.
We visit the market. Gap oxiriga every Sunday qo‘shib yozing. | We visit the market every Sunday. | Every Sunday ishning takrorlanishini bildiradi.
@6.13
Umumiy xossani tanlang: Metal ___ when heated. (expands / is expanding) | expands | Umumiy qonuniyat Present Simple bilan aytiladi.
Umumiy haqiqat: Plants ___ sunlight to grow. (need; Present Simple) | need | Plants ko‘plikda; need kerak.
Umumiy xossani Present Simplega tuzating: Honey is tasting sweet. | Honey tastes sweet. | Ta’m xossasi bu ma’noda oddiy zamonda aytiladi.
Birds have feathers. Birds o‘rniga a bird qo‘yib yozing. | A bird has feathers. | Umumiy haqiqat birlikda has bilan ifodalanadi.
@6.14
To‘g‘ri tartibni tanlang: A: She is usually cheerful. B: She usually is cheerful. Be dan keyingi odatiy o‘rin uchun harfni yozing. | A | Chastota ravishi odatda be dan keyin keladi.
Always uchun odatiy o‘rinni tanlang: They [A] arrive [B] early. Faqat A yoki B yozing. | A | Chastota ravishi asosiy fe’ldan oldin keladi.
Ravishni asosiy fe’ldan oldinga ko‘chiring: He eats often fish. | He often eats fish. | Often eats fe’lidan oldinda bo‘ladi.
Sometimes ni be dan keyin qo‘ying: I am nervous. Qisqartirmang. | I am sometimes nervous. | Be bilan ravish am dan keyin keladi.
@6.15
Twice a month ma’nosini tanlang: oyiga ikki marta / haftasiga ikki marta. | oyiga ikki marta | Month oy, twice ikki marta degani.
She swims ___ a week: on Monday and Thursday. (once / twice) | twice | Haftada ikki kun — twice a week.
Ibora xatosini tuzating: two time a day. Times shaklidan foydalanib yozing. | two times a day | Two bilan time ko‘plikda times bo‘ladi.
How often bilan chastotani so‘rang: He checks his email every hour. | How often does he check his email? | How often takrorlanish tezligini so‘raydi.
@6.16
___ the children hungry? (Are / Do) | Are | Hungry sifat bo‘lgani uchun be kerak.
___ the children eat here? (Are / Do) | Do | Eat harakat fe’li; savolda do kerak.
Savolni tuzating: Does she a doctor? | Is she a doctor? | Kasbni bildirgan otli gapda is ishlatiladi.
Inkor qiling: We are busy. Qisqartirmang, do ishlatmang. | We are not busy. | Be inkori not qo‘shish bilan yasaladi.
""", r"""
@7.1
To‘g‘ri davomli shaklni tanlang: She ___ a scarf now. (is knitting / knits) | is knitting | Hozir davom etayotgan ish is + -ing bilan ifodalanadi.
Present Continuous: We ___ for the bus. (wait) | are waiting | We bilan are va fe’lning -ing shakli keladi.
Faqat yordamchi fe’lni tuzating: The dog are barking. | is | The dog birlikdagi ega.
They play cards. Hozirgi davomli zamonga aylantiring; qisqartirmang. | They are playing cards. | Present Continuous: are + playing.
@7.2
To‘g‘ri inkorni tanlang: A: I am not joking. B: I do not joking. Faqat harfni yozing. | A | Davomli zamonda am not kerak.
The workers ___ not digging today. (is / are) | are | Workers ko‘plikda.
Tartibni tuzating: He not is reading. Qisqartirmang. | He is not reading. | Not be dan keyin keladi.
Inkor qiling: We are travelling today. Qisqartirmang. | We are not travelling today. | Are dan keyin not qo‘yiladi.
@7.3
To‘g‘ri savolni tanlang: A: Is Dad cooking? B: Does Dad cooking? Faqat harfni yozing. | A | Present Continuous savoli be bilan boshlanadi.
___ I speaking too fast? (Am / Is / Are) | Am | I bilan am ishlatiladi.
Savolni tuzating: Is they leaving now? | Are they leaving now? | They bilan are kerak.
Yes/no savol qiling: The students are taking notes. | Are the students taking notes? | Are ega oldiga chiqadi.
@7.4
To‘g‘ri savolni tanlang: A: Why is the dog barking? B: Why the dog is barking? Faqat harfni yozing. | A | Wh-savolda be ega oldiga chiqadi.
What ___ you carrying? (is / are) | are | You bilan are ishlatiladi.
Savolni tuzating: Where are she going? | Where is she going? | She bilan is kerak.
What bilan to‘ldiruvchini so‘rang: He is washing the dishes. | What is he washing? | The dishes o‘rnini what egallaydi.
@7.5
Are they playing outside? Ijobiy qisqa javobni tanlang: A: Yes, they are. B: Yes, they do. Faqat harfni yozing. | A | Are savoliga are bilan javob beriladi.
Is the printer working? — Yes, it ___. | is | Birlikdagi it uchun is kerak.
Javobni tuzating: Are you listening? — No, I aren't. Faqat javobni yozing; qisqartirmang. | No, I am not. | I bilan inkor am not bo‘ladi.
Are the birds singing? Salbiy qisqa javob yozing; qisqartirmang. | No, they are not. | Birds o‘rniga they ishlatiladi.
@7.6
To‘g‘ri -ing shaklini tanlang: writeing / writing. | writing | Oxirgi talaffuzsiz e tushadi.
Present Continuous: The baby is ___. (smile) | smiling | Smile → smiling.
Fe’l yozilishini tuzating: She is danceing. Faqat fe’lning -ing shaklini yozing. | dancing | Dance ning oxirgi e harfi tushadi.
See fe’lining -ing shaklini yozing. | seeing | -ee bilan tugaganda ikkala e saqlanadi.
@7.7
To‘g‘ri -ing shaklini tanlang: swiming / swimming. | swimming | Qisqa urg‘uli bo‘g‘indagi oxirgi undosh ikki yoziladi.
He is ___ the route. (plan; -ing shakli) | planning | Plan → planning, n ikki yoziladi.
Faqat -ing shaklini tuzating: The flowers are dieing. | dying | -ie o‘rniga y kelib -ing qo‘shiladi.
Lie fe’lining -ing shaklini yozing. | lying | Lie oxiridagi -ie o‘rniga y keladi, so‘ng -ing qo‘shiladi: lying.
@7.8
Ayni damdagi ishni tanlang: Look! The bus ___. (comes / is coming) | is coming | Look hozirgi harakatga e’tibor qaratadi.
Hozir: Listen! Somebody ___ at the door. (knock; Present Continuous) | is knocking | Somebody birlikda; is knocking kerak.
Ayni damdagi ishga tuzating: At this moment, we watch the race. Present Continuous, qisqartirmang. | At this moment, we are watching the race. | Hozir davom etayotgan ish are watching bilan aytiladi.
The chef chops onions. Right now ni oxiriga qo‘shing va Present Continuousga aylantiring; qisqartirmang. | The chef is chopping onions right now. | Chop → chopping; hozirgi jarayon is bilan yasaladi.
@7.9
Vaqtinchalik ish uchun Present Continuousni tanlang: Until her car is fixed, she ___. (is cycling / cycles) | is cycling | Mashina tuzalguncha davom etadigan vaqtinchalik holat.
Vaqtinchalik holat, Present Continuous: I ___ my cousin's room this week. (use) | am using | This week bilan cheklangan vaziyat.
Present Continuousga tuzating: We live in a hotel while our house is repaired. Qisqartirmang. | We are living in a hotel while our house is repaired. | Uy ta’miri davomidagi vaqtinchalik yashash ifodalangan.
He works in Tashkent. This week ni oxiriga qo‘shib, vaqtinchalik ishni Present Continuousda yozing; qisqartirmang. | He is working in Tashkent this week. | Bu hafta bilan cheklangan ish is working bilan aytiladi.
@7.10
O‘zgarish jarayonini tanlang: Prices ___ these days. (are rising / rise) | are rising | Hozirgi tendensiya davomli zamonda aytiladi.
Present Continuous: The nights ___ longer. (get) | are getting | Getting asta-sekin o‘zgarishni bildiradi.
Faqat yordamchini tuzating: Our town are growing quickly. | is | Our town birlikda.
The river becomes wider. Ayni davrdagi o‘zgarishni Present Continuousda yozing; qisqartirmang. | The river is becoming wider. | Is becoming davom etayotgan o‘zgarishni bildiradi.
@7.11
Odatni tanlang: She normally ___ to work. (walks / is walking) | walks | Normally odatni bildiradi.
Ikki shaklni vergul bilan yozing: He usually ___ at home, but today he ___ at a café. (eat; eat) | eats, is eating | Odat — eats, bugungi vaqtinchalik ish — is eating.
Hozirgi ishga tuzating: Look! The cat climbs the curtain. Present Continuous, qisqartirmang. | Look! The cat is climbing the curtain. | Ayni paytdagi harakat is climbing bilan ifodalanadi.
They are playing tennis now. Now o‘rniga every weekend qo‘yib, odatga aylantiring. | They play tennis every weekend. | Muntazam odat uchun Present Simple kerak.
@7.12
Holat fe’lini tanlang: I ___ your address. (know / am knowing) | know | Know bu ma’noda davomli zamonda ishlatilmaydi.
This soup ___ delicious. (tastes / is tasting) | tastes | Ta’m xossasi tastes bilan ifodalanadi.
Xatoni tuzating: She is wanting a new phone. | She wants a new phone. | Want istak holatini bildiradi.
He is having a bicycle. Egalik ma’nosini Present Simple bilan tuzating. | He has a bicycle. | Egalik ma’nosidagi have odatda davomli bo‘lmaydi.
@8.1
Variantlar cheklangan: ___ of the three routes is shorter? (What / Which) | Which | Of the three aniq tanlov doirasini belgilaydi.
Variantlarsiz ochiq savol: ___ is your occupation? (What / Which) | What | Kasb ochiq savol sifatida so‘ralmoqda.
Faqat savol so‘zini tuzating: What of these four cups is yours? | Which | Of these bilan cheklangan tanlov uchun which kerak.
Cheklangan tanlov savoli tuzing: You want the red scarf, not the blue one. Which scarf bilan boshlang. | Which scarf do you want? | Aniq sharflar orasidagi tanlov which bilan so‘raladi.
@8.2
Shaxsni so‘rang: ___ is knocking? — Our neighbour. (Who / Whose) | Who | Who harakatni bajarayotgan shaxsni so‘raydi.
___ glasses are these? — My grandmother's. (Who / Whose) | Whose | Egalik javobi uchun whose kerak.
Faqat savol so‘zini tuzating: Whose teaches you English? — Mr Brown. | Who | O‘qituvchi shaxs so‘ralmoqda, egalik emas.
Whose bilan savol tuzing: This is Mum's handbag. Handbag ni saqlang. | Whose handbag is this? | Whose handbag sumka kimniki ekanini so‘raydi.
@8.3
Sababni so‘rang: ___ are you smiling? — Because I passed. (Why / How) | Why | Because sababga javob beradi.
___ do you open this file? — Click twice. (Why / How) | How | How ishni bajarish usulini so‘raydi.
Faqat savol so‘zini tuzating: How is he absent? — Because he is ill. | Why | Kasallik yo‘qlikning sababi.
How bilan usulni so‘rang: She travels to work by train. | How does she travel to work? | By train usul javobi bo‘lib, how bilan so‘raladi.
@8.4
Masofani so‘rang: ___ is the nearest shop? — Five hundred metres. (How old / How far) | How far | Metrlardagi javob masofani bildiradi.
___ does the journey take? — Three hours. (How long / How old) | How long | How long davomiylikni so‘raydi.
Faqat savol iborasini tuzating: How far is your daughter? — Twelve years old. | How old | Yosh uchun how old ishlatiladi.
How long bilan davomiylikni so‘rang: The lesson lasts forty minutes. | How long does the lesson last? | Davomiylik savolida does va last ishlatiladi.
@8.5
Sanalmaydigan ot uchun tanlang: ___ sugar is in this cake? (How much / How many) | How much | Sugar sanalmaydigan ot.
___ passengers are on the plane? (How much / How many) | How many | Passengers sanaladigan ko‘plik.
Savol iborasini tuzating: How many money do you need? Faqat iborani yozing. | How much | Money sanalmaydi.
How many bilan sonni so‘rang: She has three sisters. Have got ishlatmang. | How many sisters does she have? | Sisters sanaladi; savolda does ... have keladi.
@8.6
Ega savolini tanlang: A: Who broke the cup? B: Who did you call? Faqat harfni yozing. | A | Birinchi savolda who harakat bajaruvchini so‘raydi.
Who ___ in this office? (work / works) | works | Noma’lum ega who bilan odatda birlik fe’l keladi.
Ortiqcha yordamchini olib tashlang: Who did opened the window? | Who opened the window? | Oddiy ega savolida did ishlatilmaydi.
Who bilan egani so‘rang: The mechanic fixed the engine. | Who fixed the engine? | Ega o‘rnini who egallaydi, fe’l o‘zgarmaydi.
@8.7
To‘ldiruvchi savolini tanlang: A: Who does Tom trust? B: Who trusts Tom? Faqat harfni yozing. | A | Birinchi savolda Tom ega, who to‘ldiruvchi.
Who ___ they meet on Fridays? (do / does) | do | They bilan do kerak.
Savolni tuzating: Who did you invited? | Who did you invite? | Did dan keyin asosiy fe’l shakli kerak.
Who bilan to‘ldiruvchini so‘rang: She thanked the nurse. | Who did she thank? | O‘tgan zamondagi to‘ldiruvchi savoli did bilan yasaladi.
@8.8
Idish ichida: The soup is ___ the bowl. (in / on / at) | in | In ichki hajmni bildiradi.
Sirt ustida: The stamp is ___ the envelope. (in / on / at) | on | On yuzaga birikkan narsani bildiradi.
Kelishilgan uchrashuv nuqtasi: Meet me ___ the entrance. (in / on / at) | at | At aniq uchrashuv nuqtasi uchun ishlatiladi.
Faqat predlogni tuzating: The fish are on the aquarium. Ichkarida suzmoqda. | in | Akvariumning ichi in bilan ifodalanadi.
@8.9
Orqasida ma’nosini tanlang: The shed is ___ the house. (behind / between) | behind | Behind — orqasida.
Ikki odam o‘rtasida: I sat ___ Anna and Tim. (under / between) | between | Between ikki chegaraning o‘rtasini bildiradi.
Faqat predlogni tuzating: The lamp hangs below the table. Chiroq stolning tepasida osilgan; above ishlating. | above | Above — tepasida, yuqorisida.
The bank is next to the school. Next to o‘rniga beside qo‘yib gapni yozing; qisqartirmang. | The bank is beside the school. | Beside ham yonida degan ma’noni bildiradi.
@8.10
Ichkaridan tashqariga: The bird flew ___ the cage. (out of / into) | out of | Out of tashqariga harakatni bildiradi.
We are going ___ the station. (to / at) | to | To manzil tomon harakatni bildiradi.
Faqat predlogni tuzating: He jumped at the pool. U hovuz ichiga sakradi; into ishlating. | into | Into ichkariga yo‘nalishni bildiradi.
Yo‘lning narigi tomoniga o‘tishni ifodalang: They walked ___ the road. (across / out of) | across | Across bir tomondan boshqa tomonga o‘tishni bildiradi.
@8.11
Yil bilan tanlang: ___ 2020. (in / on / at) | in | Yillar oldidan in keladi.
We meet ___ noon. (in / on / at) | at | Noon aniq vaqt nuqtasi.
Faqat predlogni tuzating: The test is in Tuesday. | on | Hafta kunlari bilan on ishlatiladi.
Ikki javobni vergul bilan yozing: ___ the morning; ___ Friday morning. (in / on / at) | in, on | Umumiy morning bilan in, aniq kun bilan on keladi.
@8.12
Ketma-ketlik: Dinner is at six. We wash up at seven, ___ dinner. (before / after) | after | Yuvish ovqatdan keyin sodir bo‘ladi.
The shop stays open ___ eight, then closes. (until / before) | until | Until davom etishning oxirgi chegarasini bildiradi.
Ma’noga mos predlogni tanlang: Brush your teeth ___ you go to bed. (before / until) | before | Tish yuvish uxlashdan oldin bajariladi.
The café closes at five. Until bilan qayta yozing: The café is open ___. | until five | Until five ochiq turish chegarasini bildiradi.
@8.13
Muddat uchun tanlang: We waited ___ thirty minutes. (for / during) | for | For vaqt miqdori bilan keladi.
Nobody spoke ___ the exam. (for / during) | during | During voqea yoki davr nomi bilan keladi.
Ikkinchi predlogni tuzating: from Monday until to Friday. Until to o‘rniga bitta to yozib, butun iborani yozing. | from Monday to Friday | From ... to boshlanish va tugashni bildiradi.
The shift starts at six and ends at two. Bo‘shliqni to‘liq yozing: The shift runs ___. From ... to ishlating. | from six to two | From six to two vaqt oralig‘ini ifodalaydi.
@8.14
Harakatni tavsiflovchi shaklni tanlang: Please speak ___. (quiet / quietly) | quietly | Speak fe’li ravish bilan tavsiflanadi.
Easy dan ravish yasang: She solved it ___. | easily | Easy → easily; y o‘rniga i keladi.
Faqat ravishni tuzating: He answered polite. | politely | Polite ga -ly qo‘shiladi.
The driver was careful. He drove ___ shaklida to‘liq gap yozing. | He drove carefully. | Harakatni tavsiflashda careful → carefully.
@8.15
Tanlang: They work very ___. (hard / hardly) Mehnatni astoydil bajarish nazarda tutilgan. | hard | Hard ravish sifatida astoydil degani; hardly boshqa ma’no beradi.
The team played ___. (good / well) | well | Good sifatining ravishi well.
Faqat ravishni tuzating: She arrived lately yesterday. Kech kelgan, late ishlating. | late | Late kech degani; lately yaqinda degani.
He is a fast swimmer. He swims ___ shaklida to‘liq gap yozing. | He swims fast. | Fast ravish bo‘lganda ham o‘zgarmaydi.
@8.16
Ravish → joy → vaqt tartibini tanlang. A: She sang beautifully in the hall last night. B: She sang last night in the hall beautifully. Faqat harfni yozing. | A | Berilgan tartibda ravish, joy, vaqt keladi.
Tartiblang: We danced / at the party / happily / yesterday. Ravish → joy → vaqt. | We danced happily at the party yesterday. | Happily, at the party, yesterday tartibi kerak.
Belgilangan tartibga tuzating: He slept last night peacefully on the sofa. Ravish → joy → vaqt. | He slept peacefully on the sofa last night. | Ravish peacefully oldin, vaqt last night oxirida.
The children played. Quietly, in the garden, this morning ni aynan ravish → joy → vaqt tartibida qo‘shing. | The children played quietly in the garden this morning. | Fe’ldan keyin harakat tarzi, joy va vaqt keladi.
@9.1
O‘tgan zamon be shaklini tanlang: She ___ happy yesterday. (was / is) | was | Yesterday o‘tgan vaqtni bildiradi.
The streets ___ empty last night. (was / were) | were | Streets ko‘plikda.
Faqat fe’lni tuzating: We was at the museum. | were | We bilan were ishlatiladi.
He is ill today. Today o‘rniga yesterday qo‘yib o‘tgan zamonga aylantiring. | He was ill yesterday. | Is o‘tgan zamonda was bo‘ladi.
@9.2
To‘g‘ri inkorni tanlang: A: It wasn't expensive. B: It didn't expensive. Faqat harfni yozing. | A | Sifatli gapning o‘tgan inkori wasn't bilan yasaladi.
The children ___ not asleep at nine. (was / were) | were | Children ko‘plikda.
Faqat yordamchini tuzating: You wasn't alone. Qisqartma yozing. | weren't | You bilan weren't kerak.
Inkor qiling: The weather was fine. Qisqartirmang. | The weather was not fine. | Was dan keyin not keladi.
@9.3
To‘g‘ri savolni tanlang: A: Was the journey long? B: Did the journey long? Faqat harfni yozing. | A | O‘tgan holat savolida was ishlatiladi.
___ I too loud? (Was / Were) | Was | I bilan was kerak.
Savolni tuzating: Was the windows open? | Were the windows open? | Windows ko‘plikda.
Yes/no savol qiling: You were in the audience. | Were you in the audience? | Were ega oldiga chiqadi.
@9.4
To‘g‘ri savolni tanlang: A: Where was your passport? B: Where your passport was? Faqat harfni yozing. | A | Wh-savolda was ega oldiga o‘tadi.
Why ___ the doors locked? (was / were) | were | Doors ko‘plikdagi ega.
Savolni tuzating: When were the meeting? | When was the meeting? | Meeting birlikda.
Where bilan joyni so‘rang: The children were at the zoo. | Where were the children? | At the zoo o‘rniga where keladi.
@9.5
Were the roads icy? Ijobiy qisqa javobni tanlang: A: Yes, they were. B: Yes, they did. Faqat harfni yozing. | A | Were savoliga were bilan javob beriladi.
Was the tea hot? — No, it ___. Qisqartma yozing. | wasn't | It bilan wasn't ishlatiladi.
Javobni tuzating: Were you tired? — Yes, I were. Faqat javobni yozing. | Yes, I was. | Javobda I bilan was keladi.
Was your father at work? Salbiy qisqa javob yozing; qisqartirmang. | No, he was not. | Father o‘rniga he ishlatiladi.
@9.6
To‘g‘ri gapni tanlang: A: There was a delay. B: There were a delay. Faqat harfni yozing. | A | Birlikdagi delay bilan was kerak.
There ___ several mistakes in my essay. (was / were) | were | Several mistakes ko‘plikda.
Faqat fe’lni tuzating: There were snow on the roof. | was | Snow sanalmaydigan ot.
There are ten students here today. Today o‘rniga yesterday qo‘yib o‘tgan zamonga aylantiring. | There were ten students here yesterday. | There are o‘tgan zamonda there were bo‘ladi.
@9.7
To‘g‘ri inkorni tanlang: A: There weren't any clouds. B: There wasn't any clouds. Faqat harfni yozing. | A | Clouds ko‘plikda.
There ___ any traffic at dawn. (wasn't / weren't) | wasn't | Traffic sanalmaydigan ot.
Faqat yordamchini tuzating: There didn't a meeting yesterday. Didn't o‘rniga wasn't yoki weren't yozing. | wasn't | Borlik inkori birlikda wasn't bilan yasaladi.
Inkor qiling; some o‘rniga any qo‘ying: There were some messages. Qisqartirmang. | There were not any messages. | Ko‘plik inkori were not any bilan yasaladi.
@9.8
To‘g‘ri savolni tanlang: A: Was there any damage? B: Did there any damage? Faqat harfni yozing. | A | Sanalmaydigan damage uchun was there kerak.
___ there many visitors yesterday? (Was / Were) | Were | Visitors ko‘plikda.
Savolni tuzating: Was there two exits? | Were there two exits? | Two exits bilan were there ishlatiladi.
Yes/no savol qiling: There was a festival in May. | Was there a festival in May? | Was there o‘tgan borlik savolini yasaydi.
@9.9
O‘tgan zamonni tanlang: Yesterday, they ___ the match. (enjoy / enjoyed) | enjoyed | Muntazam fe’lga -ed qo‘shiladi.
Past Simple: I ___ my aunt last night. (call) | called | Call muntazam fe’l; o‘tgan zamonda -ed qo‘shilib called bo‘ladi.
Faqat fe’lni tuzating: She visit us yesterday. | visited | Yesterday bilan o‘tgan zamon visited kerak.
We watch a film every Friday. Every Friday o‘rniga last Friday qo‘yib o‘tgan zamonga aylantiring. | We watched a film last Friday. | Tugallangan o‘tgan ish watched bilan aytiladi.
@9.10
O‘tgan zamonni tanlang: He ___ the last apple. (ate / eaten) | ate | Eat ning V2 shakli ate.
Past Simple: We ___ the early train. (take) | took | Take ning V2 shakli took.
Faqat fe’lni tuzating: She buyed a coat. | bought | Buy istisno fe’l, o‘tgan shakli bought.
I see him every day. Every day o‘rniga yesterday qo‘yib o‘tgan zamonga aylantiring. | I saw him yesterday. | See ning V2 shakli saw.
@9.11
To‘g‘ri o‘tgan shaklni tanlang: studyed / studied. | studied | Undosh + y o‘rniga -ied keladi.
Stop fe’lining Past Simple shaklini yozing. | stopped | Qisqa urg‘uli bo‘g‘indan keyin p ikki yoziladi.
Worked so‘zidagi -ed tovushini tanlang: /t/ yoki /d/ yoki /ɪd/. | /t/ | Jarangsiz /k/ dan keyin -ed /t/ bo‘ladi.
Played so‘zidagi -ed tovushini tanlang: /t/ yoki /d/ yoki /ɪd/. | /d/ | Unli tovushdan keyin -ed /d/ bo‘ladi.
@9.12
To‘g‘ri inkorni tanlang: A: He didn't call. B: He didn't called. Faqat harfni yozing. | A | Did not dan keyin fe’l asosiy shaklda keladi.
We didn't ___ the answer. (know / knew) | know | Didn't dan keyin V1 kerak.
Faqat fe’lni tuzating: I didn't saw the sign. | see | See ning asosiy shakli ishlatiladi.
Inkor qiling: The train left on time. Qisqartirmang. | The train did not leave on time. | Left inkorda did not leave bo‘ladi.
@9.13
To‘g‘ri savolni tanlang: A: Did she win? B: Did she won? Faqat harfni yozing. | A | Did dan keyin win keladi.
___ the guests stay overnight? (Did / Were) | Did | Stay harakat fe’li savolda did bilan keladi.
Savolni tuzating: Did you slept well? | Did you sleep well? | Slept o‘rniga sleep asosiy shakli kerak.
Yes/no savol qiling: They caught the bus. | Did they catch the bus? | Caught savolda catch bo‘ladi.
@9.14
To‘g‘ri savolni tanlang: A: Where did they sit? B: Where they sat? Faqat harfni yozing. | A | O‘tgan savolda did kerak.
Why ___ he leave early? (did / was) | did | Leave harakat fe’li; did kerak.
Savolni tuzating: What did she wrote? | What did she write? | Did dan keyin write keladi.
Where bilan joyni so‘rang: They stayed in a hostel. | Where did they stay? | In a hostel o‘rnini where egallaydi.
@9.15
Did the dog bark? Ijobiy qisqa javobni tanlang: A: Yes, it did. B: Yes, it was. Faqat harfni yozing. | A | Did savoliga did bilan javob beriladi.
Did Sara pass? — No, she ___. Qisqartma yozing. | didn't | O‘tgan salbiy qisqa javob didn't bilan yasaladi.
Javobni tuzating: Did they agree? — Yes, they do. Faqat javobni yozing. | Yes, they did. | Savol o‘tgan zamonda, javob ham did bilan keladi.
Did you and Ali finish? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we did not. | We ko‘plikdagi javob egasi.
@9.16
O‘tgan vaqt iborasini tanlang: next week / last night. | last night | Last night kecha kechqurunni bildiradi.
She left two minutes ___. (ago / last) | ago | Ago vaqt miqdoridan keyin keladi.
Ortiqcha predlogni olib tashlang: I called her on yesterday. | I called her yesterday. | Yesterday oldidan on qo‘yilmaydi.
Five days before now ma’nosini ago bilan uch so‘zda yozing. | five days ago | Ago hozirdan oldingi muddatni bildiradi.
@9.17
___ your shoes wet after the walk? (Were / Did) | Were | Wet sifat, o‘tgan holat savoli were bilan yasaladi.
___ you lose your umbrella? (Were / Did) | Did | Lose harakat fe’li; did kerak.
Savolni tuzating: Did she angry yesterday? | Was she angry yesterday? | Angry oldidan be ning o‘tgan shakli kerak.
Inkor qiling: They arrived late. Qisqartirmang. | They did not arrive late. | Harakat fe’lining o‘tgan inkori did not + V1.
""", r"""
@10.1
To‘g‘ri davomli shaklni tanlang: At six yesterday, she ___ dinner. (was making / were making) | was making | She bilan was + -ing kerak.
Past Continuous: We ___ the car at ten yesterday. (repair) | were repairing | We bilan were repairing keladi.
Faqat yordamchini tuzating: I were reading at midnight. | was | I bilan was ishlatiladi.
The boys are swimming. O‘tgan davomli zamonga aylantiring; qisqartirmang. | The boys were swimming. | Are o‘rniga were keladi.
@10.2
To‘g‘ri inkorni tanlang: A: I wasn't dreaming. B: I didn't dreaming. Faqat harfni yozing. | A | Past Continuous inkori wasn't + -ing.
The girls ___ not dancing at that moment. (was / were) | were | Girls ko‘plikda.
Faqat yordamchini tuzating: The engine weren't running. Qisqartma yozing. | wasn't | Engine birlikda; wasn't kerak.
Inkor qiling: You were looking at the screen. Qisqartirmang. | You were not looking at the screen. | Were dan keyin not qo‘yiladi.
@10.3
To‘g‘ri savolni tanlang: A: Was it raining? B: Did it raining? Faqat harfni yozing. | A | Davomli savol be bilan boshlanadi.
___ you sleeping at noon? (Was / Were) | Were | You bilan were kerak.
Savolni tuzating: Were the teacher explaining the rule? | Was the teacher explaining the rule? | The teacher birlikdagi ega.
Yes/no savol qiling: The dogs were chasing a ball. | Were the dogs chasing a ball? | Were ega oldiga chiqadi.
@10.4
To‘g‘ri savolni tanlang: A: Why were they laughing? B: Why they were laughing? Faqat harfni yozing. | A | Wh-savolda were ega oldiga chiqadi.
What ___ the chef preparing at seven? (was / were) | was | The chef birlikda.
Savolni tuzating: Where was you sitting? | Where were you sitting? | You bilan were kerak.
What bilan to‘ldiruvchini so‘rang: She was carrying a basket. | What was she carrying? | A basket o‘rnini what egallaydi.
@10.5
Were the children studying? Ijobiy qisqa javobni tanlang: A: Yes, they were. B: Yes, they did. Faqat harfni yozing. | A | Were savoliga were bilan javob beriladi.
Was the sun shining? — No, it ___. Qisqartma yozing. | wasn't | It bilan wasn't keladi.
Javobni tuzating: Was she driving? — Yes, she were. Faqat javobni yozing. | Yes, she was. | She birlikda; was kerak.
Were you and Dad gardening? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we were not. | We uchun were not ishlatiladi.
@10.6
Fon harakatini tanlang: I dropped my glass while I ___. (was washing up / washed up) | was washing up | Davom etayotgan yuvish fon vazifasida.
Ikki fe’lni vergul bilan yozing: We ___ home when it ___ to rain. (walk — Past Continuous; start — Past Simple) | were walking, started | Fon — were walking, yangi voqea — started.
Faqat xato yordamchini tuzating: She were cooking when the alarm rang. | was | She bilan was cooking kerak.
When bilan birlashtiring: I was cycling. I fell. I was cycling bilan boshlang. | I was cycling when I fell. | Davomli ishni qisqa o‘tgan voqea uzadi.
@10.7
Bir paytdagi ikki jarayon: ___ she was sewing, he was ironing. (While / After) | While | While bir vaqtdagi harakatlarni bog‘laydi.
I was opening the gate ___ the dog ran out. (when / while) | when | Qisqa yangi voqea when bilan kiritiladi.
Qisqa voqeaga moslang: We were talking while the phone suddenly rang. While o‘rniga when qo‘yib yozing. | We were talking when the phone suddenly rang. | When kutilmagan qisqa voqeani bog‘laydi.
While bilan birlashtiring: I was cleaning. My sister was cooking. While I bilan boshlang. | While I was cleaning, my sister was cooking. | Ikkala harakat bir vaqtda davom etgan.
@10.8
Eski odatni tanlang: He ___ collect coins, but he doesn't now. (used to / use to) | used to | Tasdiq shakli used to bo‘ladi.
She used to ___ in a village. (live / lived) | live | Used to dan keyin asosiy fe’l keladi.
Faqat xato fe’lni tuzating: I used to played outside. | play | Used to play to‘g‘ri shakl.
We lived by the sea, but we don't now. Used to bilan bitta sodda gap yozing; but qismini yozmang. | We used to live by the sea. | Used to endi o‘zgargan eski holatni bildiradi.
@10.9
To‘g‘ri inkorni tanlang: A: She didn't use to drive. B: She didn't used to drive. Faqat harfni yozing. | A | Did dan keyin use asosiy shakli keladi.
They did not ___ to travel much. (use / used) | use | Did not bilan use to ishlatiladi.
Faqat xato shaklni tuzating: I didn't use to liked olives. | like | Use to dan keyin like asosiy shakli kerak.
Inkor qiling: He used to get up early. Qisqartirmang. | He did not use to get up early. | Inkor did not use to bilan yasaladi.
@10.10
To‘g‘ri savolni tanlang: A: Did they use to live here? B: Did they used to live here? Faqat harfni yozing. | A | Did dan keyin use to ishlatiladi.
___ you use to play the flute? (Did / Were) | Did | Used to savoli did bilan yasaladi.
Savolni tuzating: Did he use to worked at night? | Did he use to work at night? | Use to dan keyin work asosiy shakli kerak.
Yes/no savol qiling: They used to grow grapes. | Did they use to grow grapes? | Used to savolda did ... use to bo‘ladi.
@10.11
Eski takroriy harakat: On winter evenings, Grandma ___ socks for us. (would knit / would knitted) | would knit | Would dan keyin asosiy fe’l keladi.
Every summer as a child, I would ___ in the river. (swim / swam) | swim | Takroriy o‘tgan harakat would + V1 bilan ifodalanadi.
Faqat xato fe’lni tuzating: During those holidays, we would went fishing every morning. | go | Would dan keyin go kerak.
As children, we climbed this tree every weekend. Climbed o‘rniga would climb qo‘yib yozing; qisqartirmang. | As children, we would climb this tree every weekend. | O‘tgan takroriy harakat would bilan aytiladi.
@10.12
Eski holat: This building ___ be a cinema. (used to / would) | used to | Doimiy eski holat uchun used to mos.
Bitta voqea: At three yesterday, she ___ the race. (won / would win) | won | Aniq bir martalik voqea Past Simpleda aytiladi.
Eski holatni tuzating: I would own a horse, but I sold it. Would o‘rniga used to qo‘yib yozing. | I used to own a horse, but I sold it. | Own holat fe’li; eski egalik uchun used to ishlatiladi.
As a child, he visited his aunt every Sunday. Used to bilan qayta yozing; as a child ni boshida saqlang. | As a child, he used to visit his aunt every Sunday. | Used to takroriy eski odatni ham bildiradi.
@11.1
Will bilan to‘g‘ri shaklni tanlang: She ___ soon. (will arrive / will arrives) | will arrive | Will dan keyin asosiy fe’l keladi.
Will bilan to‘ldiring: We ___ you tomorrow. (help; qisqartirmang) | will help | Kelajak tasdiq shakli will + V1.
Faqat asosiy fe’lni tuzating: He will goes first. | go | Will dan keyin go ishlatiladi.
They visit us. Will qo‘shib, kelajak gap qiling; qisqartirmang. | They will visit us. | Will barcha egalar bilan bir xil.
@11.2
To‘g‘ri inkorni tanlang: A: He won't agree. B: He won't agrees. Faqat harfni yozing. | A | Won't dan keyin fe’l asosiy shaklda keladi.
Qisqartirmay to‘ldiring: I will ___ tell anyone. | not | Will dan keyin not keladi.
Ortiqcha to ni olib tashlang: They will not to stop. | They will not stop.; They won't stop.; They'll not stop. | Will not dan keyin to ishlatilmaydi.
Inkor qiling: The shop will open tomorrow. Qisqartirmang. | The shop will not open tomorrow. | Inkor will not bilan yasaladi.
@11.3
To‘g‘ri savolni tanlang: A: Will it snow? B: Does it will snow? Faqat harfni yozing. | A | Will savolda ega oldiga chiqadi.
___ they accept the offer? Will bilan bo‘shliqni to‘ldiring. | Will | Will kelajak savolini boshlaydi.
Savolni tuzating: Will he to wait? | Will he wait? | Will dan keyin to kerak emas.
Yes/no savol qiling: We will need more chairs. We ni saqlang. | Will we need more chairs? | Will ega oldiga o‘tadi.
@11.4
To‘g‘ri savolni tanlang: A: Where will they stay? B: Where they will stay? Faqat harfni yozing. | A | Wh-savolda will ega oldiga chiqadi.
What ___ happen next? (will / does) | will | Kelajak voqeasi will happen bilan so‘raladi.
Savolni tuzating: When will she leaves? | When will she leave? | Will dan keyin leave kerak.
Who bilan to‘ldiruvchini so‘rang: He will invite his cousin. | Who will he invite? | His cousin o‘rnini who egallaydi.
@11.5
Will the bus stop here? Ijobiy qisqa javobni tanlang: A: Yes, it will. B: Yes, it does. Faqat harfni yozing. | A | Will savoliga will bilan javob beriladi.
Will they help? — No, they ___. Qisqartma yozing. | won't | Will not qisqartmasi won't.
Javobni tuzating: Will she come? — Yes, she wills. Faqat javobni yozing. | Yes, she will. | Will ga uchinchi shaxs -s qo‘shilmaydi.
Will you and Anna be ready? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we will not. | We nomidan will not bilan javob beriladi.
@11.6
To‘g‘ri kelajak holatini tanlang: A: He will be tired. B: He will tired. Faqat harfni yozing. | A | Sifatdan oldin be kerak.
My sister will ___ an engineer. | be | Kasb oti oldidan will be keladi.
Yetishmayotgan be ni qo‘shing: I will in the office at ten. Qisqartirmang. | I will be in the office at ten. | Joy birikmasidan oldin be kerak.
They are happy. Will bilan qayta yozing; qisqartirmang. | They will be happy. | Are kelajakda will be bo‘ladi.
@11.7
To‘g‘ri reja shaklini tanlang: A: He is going to study law. B: He going to study law. Faqat harfni yozing. | A | Going to oldidan be kerak.
Going to bilan to‘ldiring: The children ___ a tree. (plant; qisqartirmang) | are going to plant | Ko‘plikda are going to ishlatiladi.
Faqat yordamchini tuzating: I is going to learn Spanish. | am | I bilan am kerak.
She plans to buy a camera. Going to bilan qayta yozing; qisqartirmang. | She is going to buy a camera. | Oldindan reja is going to bilan ifodalanadi.
@11.8
To‘g‘ri inkorni tanlang: A: I am not going to complain. B: I don't going to complain. Faqat harfni yozing. | A | Going to inkori be not bilan yasaladi.
They ___ not going to move. (is / are) | are | They bilan are kerak.
Tartibni tuzating: She not is going to drive. Qisqartirmang. | She is not going to drive. | Not be dan keyin keladi.
Inkor qiling: I am going to borrow his bike. Qisqartirmang. | I am not going to borrow his bike. | Am not going to inkor rejani bildiradi.
@11.9
To‘g‘ri savolni tanlang: A: Is it going to rain? B: Does it going to rain? Faqat harfni yozing. | A | Going to savolida be oldinga chiqadi.
___ we going to eat outside? (Am / Is / Are) | Are | We bilan are kerak.
Savolni tuzating: Are he going to apply? | Is he going to apply? | He bilan is ishlatiladi.
Yes/no savol qiling: The boys are going to build a boat. | Are the boys going to build a boat? | Are ega oldiga chiqadi.
@11.10
To‘g‘ri savolni tanlang: A: When are they going to leave? B: When they are going to leave? Faqat harfni yozing. | A | Savol so‘zidan keyin be keladi.
What ___ she going to wear? (is / are) | is | She bilan is kerak.
Savolni tuzating: Where is you going to stay? | Where are you going to stay? | You bilan are kerak.
What bilan to‘ldiruvchini so‘rang: We are going to sell our car. We ni saqlang. | What are we going to sell? | Our car o‘rnini what egallaydi.
@11.11
Are they going to join? Ijobiy qisqa javobni tanlang: A: Yes, they are. B: Yes, they will. Faqat harfni yozing. | A | Going to savolida be bilan javob beriladi.
Is the shop going to close? — No, it ___. Qisqartma yozing. | isn't | Is savoliga isn't inkori mos.
Javobni tuzating: Are you going to leave? — Yes, I are. Faqat javobni yozing. | Yes, I am. | Javobda I bilan am keladi.
Are you and Tom going to swim? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we are not. | We uchun are not kerak.
@11.12
Kelishilgan reja, Present Continuous: I ___ the manager at two tomorrow. (am meeting / meet) | am meeting | Belgilangan shaxsiy uchrashuv davomli zamonda aytiladi.
Chiptalar olindi. Present Continuous: We ___ on Saturday. (leave; qisqartirmang) | are leaving | Oldindan tashkil etilgan jo‘nash.
Faqat yordamchini tuzating: She are having lunch with the client tomorrow. | is | She bilan is having kerak.
He has an appointment with the doctor tomorrow. See fe’li bilan Present Continuousda qayta yozing; qisqartirmang. | He is seeing the doctor tomorrow. | Belgilangan uchrashuv is seeing bilan ifodalanadi.
@11.13
Jadval, Present Simple: The flight ___ at 8.15 tomorrow. (lands / is landing) | lands | Rasmiy jadval Present Simple bilan aytiladi.
Jadvalni Present Simpleda yozing: The concert ___ at seven tonight. (begin) | begins | Concert birlikda; begins kerak.
Faqat fe’lni tuzating: According to the timetable, the train leave at six. | leaves | The train bilan leaves keladi.
The film will start at nine. Jadval sifatida Present Simplega aylantiring. | The film starts at nine. | Jadval uchun starts ishlatiladi.
@11.14
Hozir qabul qilingan qaror: You're cold? I ___ the window. (will close / am going to close) | will close | Hozirgi qaror will bilan ifodalanadi.
Oldindan reja: We have bought paint. We ___ the bedroom. (are going to paint / paint) | are going to paint | Tayyorlangan reja going to bilan aytiladi.
Dalilga tayangan taxmin uchun going to ni tanlang: Look at those black clouds! It ___. (is going to rain / rains) | is going to rain | Hozirgi ko‘rinadigan dalil going to bilan bog‘langan.
I have decided to learn to drive. I bilan boshlab going to orqali qayta yozing; qisqartirmang. | I am going to learn to drive. | Oldindan qabul qilingan qaror going to bilan ifodalanadi.
@11.15
Vaqt ergash gapini tanlang: I'll wait until she ___. (comes / will come) | comes | Kelajak vaqt ergash gapida Present Simple keladi.
We'll start as soon as everyone ___. (arrive; Present Simple) | arrives | Everyone birlikda; arrives kerak.
Xatoni tuzating: I will call when I will get home. Qisqartirmang. | I will call when I get home. | When dan keyingi kelajak ma’nosi Present Simple bilan beriladi.
As soon as bilan birlashtiring: She arrives. We will eat. As soon as she bilan boshlang; qisqartirmang. | As soon as she arrives, we will eat. | Vaqt gapida arrives, asosiy gapda will eat keladi.
@11.16
Yordam taklifini tanlang: A: Shall I wash the dishes? B: Shall he washes the dishes? Faqat harfni yozing. | A | Shall I yordam taklif qilish uchun ishlatiladi.
Birgalikdagi taklif: ___ we begin? (Shall / Does) | Shall | Shall we birgalikdagi taklifni bildiradi.
Savolni tuzating: Shall we to sit here? | Shall we sit here? | Shall dan keyin to qo‘yilmaydi.
Let's go upstairs. Shall we bilan savol-taklifga aylantiring. | Shall we go upstairs? | Shall we + V1 taklif savolini yasaydi.
""", r"""
@12.1
V3 shaklini tanlang: took / taken. | taken | Take: took — V2, taken — V3.
Present Perfect: I have ___ the letter. (write; V3) | written | Write ning V3 shakli written.
Faqat V3 ni tuzating: She has saw the sea. | seen | See ning V3 shakli seen.
Speak fe’lining V3 shaklini yozing. | spoken | Speak → spoke → spoken.
@12.2
To‘g‘ri shaklni tanlang: We ___ the bridge. (have crossed / has crossed) | have crossed | We bilan have + V3 ishlatiladi.
Present Perfect: They ___ their tickets. (book; qisqartirmang) | have booked | Ko‘plikdagi ega have booked bilan keladi.
Faqat yordamchini tuzating: I has finished the report. | have | I bilan have kerak.
We cleaned the windows. Present Perfectga aylantiring; qisqartirmang. | We have cleaned the windows. | Have + cleaned hozirgi natijani bildiradi.
@12.3
To‘g‘ri shaklni tanlang: She ___ the exam. (has passed / have passed) | has passed | She bilan has kerak.
Present Perfect: The train ___ the station. (leave; qisqartirmang) | has left | Birlik ega bilan has, leave ning V3 shakli left.
Faqat V3 ni tuzating: He has went upstairs. | gone | Go ning V3 shakli gone.
My sister found her ring. Present Perfectga aylantiring; qisqartirmang. | My sister has found her ring. | Birlikdagi ega has found bilan keladi.
@12.4
To‘g‘ri inkorni tanlang: A: We haven't decided. B: We don't decided. Faqat harfni yozing. | A | Present Perfect inkori haven't + V3.
He ___ not answered my message. (have / has) | has | He bilan has not keladi.
Faqat V3 ni tuzating: They haven't wrote back. | written | Have dan keyin written kerak.
Inkor qiling: I have read the instructions. Qisqartirmang. | I have not read the instructions. | Not have dan keyin qo‘yiladi.
@12.5
To‘g‘ri savolni tanlang: A: Has she returned? B: Did she returned? Faqat harfni yozing. | A | Present Perfect savoli has bilan boshlanadi.
___ the children washed their hands? (Have / Has) | Have | Children ko‘plikda.
Savolni tuzating: Have he paid? | Has he paid? | He bilan has kerak.
Yes/no savol qiling: They have reached the village. | Have they reached the village? | Have ega oldiga chiqadi.
@12.6
To‘g‘ri savolni tanlang: A: Why has she left? B: Why she has left? Faqat harfni yozing. | A | Wh-savolda has ega oldiga chiqadi.
How many books ___ you read this month? (have / has) | have | You bilan have ishlatiladi.
Savolni tuzating: What has he did? | What has he done? | Do ning V3 shakli done.
What bilan to‘ldiruvchini so‘rang: They have built a shed. | What have they built? | A shed o‘rnini what egallaydi.
@12.7
Have the guests arrived? Ijobiy qisqa javobni tanlang: A: Yes, they have. B: Yes, they did. Faqat harfni yozing. | A | Have savoliga have bilan javob beriladi.
Has the rain stopped? — No, it ___. Qisqartma yozing. | hasn't | It bilan hasn't kerak.
Javobni tuzating: Have you eaten? — Yes, I has. Faqat javobni yozing. | Yes, I have. | I bilan have keladi.
Have you and Sara met before? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we have not. | We bilan have not ishlatiladi.
@12.8
Tajriba savoli: Have you ___ seen snow? (ever / never) Oddiy, betaraf savol. | ever | Ever shu paytgacha bo‘lgan tajribani so‘raydi.
Men umrimda qilmaganman: I have ___ ridden a horse. (ever / never) | never | Never hech qachon bo‘lmagan tajribani bildiradi.
Ikki inkorni tuzating; not ni olib tashlang: She has not never visited London. Qisqartirmang. | She has never visited London. | Never o‘zi inkor ma’nosini beradi.
You have tried sushi. Ever qo‘shib yes/no tajriba savoli qiling. | Have you ever tried sushi? | Ever yordamchi va V3 orasida keladi.
@12.9
Hozirgina: He has ___ left; his tea is still warm. (just / ever) | just | Just ish juda yaqinda tugaganini bildiradi.
Present Perfect va just: We ___ the room. (just; clean; qisqartirmang) | have just cleaned | Just have bilan V3 orasiga qo‘yiladi.
Just ni has bilan V3 orasiga ko‘chiring: She just has finished. Qisqartirmang. | She has just finished. | Just ning talab qilingan o‘rni has dan keyin.
I have received a letter. Just ni yordamchidan keyin qo‘shing; qisqartirmang. | I have just received a letter. | Just yaqindagina olinganini bildiradi.
@12.10
Allaqachon: Don't buy bread; I have ___ bought some. (already / yet) | already | Already ish kutilganidan oldin bajarilganini bildiradi.
Present Perfect: They ___ the museum. (already; visit; qisqartirmang) | have already visited | Already have va V3 orasida keladi.
Already ni has bilan V3 orasiga ko‘chiring: He already has eaten. Qisqartirmang. | He has already eaten. | Talab qilingan tartib has already eaten.
I have packed my bag. Already ni yordamchidan keyin qo‘shing; qisqartirmang. | I have already packed my bag. | Already ish allaqachon tugaganini bildiradi.
@12.11
Kutilayotgan natija: Have you finished ___? (yet / still) | yet | Yet savol oxirida hali ma’nosini beradi.
He ___ hasn't found his glasses. (yet / still) | still | Still inkor davom etayotganini bildiradi.
Yet ni gap oxiriga ko‘chiring: They yet haven't replied. Qisqartmani saqlang. | They haven't replied yet. | Yet inkor gap oxirida keladi.
She has not arrived. Still ni ega bilan yordamchi orasiga qo‘shing; qisqartirmang. | She still has not arrived. | Still kutilayotgan ish hamon bajarilmaganini bildiradi.
@12.12
Boshlanish nuqtasi: I have known him ___ childhood. (for / since) | since | Childhood boshlanish davrini bildiradi.
We have waited ___ half an hour. (for / since) | for | Half an hour vaqt miqdori.
Faqat predlogni tuzating: She has worked here since five months. | for | Five months davomiylik, shuning uchun for.
Ikki javobni vergul bilan yozing: ___ Monday; ___ three days. (for / since) | since, for | Monday boshlanish nuqtasi, three days muddat.
@12.13
Hali tugamagan yil; Present Perfectni tanlang: This year, we ___ four new classes. (have opened / open) | have opened | Joriy davrdagi natija Present Perfect bilan aytiladi.
Oy hali tugamadi. Present Perfect: She ___ two novels this month. (read; qisqartirmang) | has read | Hozirgacha tugallangan miqdor has read bilan aytiladi.
Faqat yordamchini tuzating: We has received ten orders today, and the shop is still open. | have | We bilan have ishlatiladi.
I wrote three pages. This morning ni oxiriga qo‘shib, hali ertalab ekanida Present Perfectda yozing; qisqartirmang. | I have written three pages this morning. | Davr davom etmoqda, hozirgacha natija aytiladi.
@12.14
U qaytib kelgan: She has ___ to the dentist and is back now. (been / gone) | been | Been borib qaytganlikni bildiradi.
Dad isn't here. He has ___ to the market. (been / gone) | gone | Gone hozir boshqa joyda ekanini bildiradi.
Faqat V3 ni tuzating: Tom has gone to Paris three times and is at home now. | been | Uch marta borib qaytgan tajriba uchun been kerak.
She went to the bank and hasn't returned. She has ___ to the bank shaklida to‘liq yozing; qisqartirmang. | She has gone to the bank. | Hali qaytmaganlik gone bilan ifodalanadi.
@12.15
Aniq tugagan vaqt: We ___ that museum in 2022. (visited / have visited) | visited | Aniq o‘tgan yil Past Simple talab qiladi.
Hayotiy tajriba, Present Perfect: ___ you ever ___ a camel? (ride) Ikki javobni vergul bilan yozing. | Have, ridden | Ever bilan tajriba have + V3 orqali so‘raladi.
Kecha bo‘lgan ishni tuzating: She has bought this coat yesterday. | She bought this coat yesterday. | Yesterday bilan Past Simple ishlatiladi.
I have seen that film. Last night ni oxiriga qo‘shib, zamonni moslang. | I saw that film last night. | Tugagan vaqt kiritilganda saw ishlatiladi.
@12.16
To‘g‘ri davomiylik savolini tanlang: A: How long have you lived here? B: How long do you lived here? Faqat harfni yozing. | A | Hozirgacha davom etgan holat have + V3 bilan so‘raladi.
How long ___ he known the answer? (have / has) | has | He bilan has kerak.
Savolni tuzating: How long have she had this job? | How long has she had this job? | She bilan has had ishlatiladi.
How long bilan davomiylikni so‘rang: They have been married for twenty years. | How long have they been married? | For twenty years o‘rniga how long keladi.
@13.1
To‘g‘ri shaklni tanlang: She ___ all day. (has been studying / has studying) | has been studying | Perfect Continuous: has been + -ing.
Present Perfect Continuous: I ___ for an hour. (run; qisqartirmang) | have been running | I bilan have been running keladi.
Faqat yordamchini tuzating: They has been travelling since June. | have | They bilan have ishlatiladi.
He is learning Turkish. Since January ni oxiriga qo‘shib Present Perfect Continuousda yozing; qisqartirmang. | He has been learning Turkish since January. | O‘tmishdan hozirgacha davom etayotgan jarayon.
@13.2
To‘g‘ri inkorni tanlang: A: She hasn't been eating well. B: She doesn't been eating well. Faqat harfni yozing. | A | Hasn't been + -ing inkor shaklidir.
We ___ not been using the printer. (have / has) | have | We bilan have not been keladi.
Tartibni tuzating: He has been not listening. Qisqartirmang. | He has not been listening. | Not has bilan been orasiga qo‘yiladi.
Inkor qiling: They have been practising every day. Qisqartirmang. | They have not been practising every day. | Not have dan keyin keladi.
@13.3
To‘g‘ri savolni tanlang: A: Has it been snowing? B: Is it been snowing? Faqat harfni yozing. | A | Perfect Continuous savoli has bilan boshlanadi.
___ they been renovating the house? (Have / Has) | Have | They bilan have kerak.
Savolni tuzating: Has you been working hard? | Have you been working hard? | You bilan have ishlatiladi.
Yes/no savol qiling: The dog has been digging in the garden. | Has the dog been digging in the garden? | Has ega oldiga chiqadi.
@13.4
To‘g‘ri savolni tanlang: A: Why have you been crying? B: Why you have been crying? Faqat harfni yozing. | A | Wh-savolda have ega oldiga chiqadi.
How long ___ she been waiting? (have / has) | has | She bilan has kerak.
Savolni tuzating: What have he been reading? | What has he been reading? | He bilan has ishlatiladi.
Where bilan joyni so‘rang: They have been training at the stadium. | Where have they been training? | At the stadium o‘rnini where egallaydi.
@13.5
Has it been raining? Ijobiy qisqa javobni tanlang: A: Yes, it has. B: Yes, it is. Faqat harfni yozing. | A | Qisqa javobda birinchi yordamchi has saqlanadi.
Have they been waiting? — No, they ___. Qisqartma yozing. | haven't | Ko‘plik uchun haven't kerak.
Javobni tuzating: Has he been sleeping? — Yes, he have. Faqat javobni yozing. | Yes, he has. | He bilan has keladi.
Have you and Ali been studying together? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we have not. | Qisqa javobda been studying takrorlanmaydi.
@13.6
Tugallangan sonni tanlang: She ___ all five letters; they are ready to post. (has written / has been writing) | has written | Barcha besh xat tugagan; natija muhim.
Jarayonni Present Perfect Continuousda yozing: We ___ the house all morning and aren't finished. (clean; qisqartirmang) | have been cleaning | Tugamagan davomli faoliyat ta’kidlanadi.
Holat fe’lini tuzating: I have been knowing her for years. Qisqartirmang. | I have known her for years. | Know holat fe’li Perfect Simpleda ishlatiladi.
He has been repairing the bikes. Uchta velosiped tayyor: all three bikes bilan Present Perfect Simplega aylantiring; qisqartirmang. | He has repaired all three bikes. | Tugallangan miqdor Perfect Simple bilan beriladi.
@13.7
To‘g‘ri oldingi o‘tgan shaklni tanlang: The guests ___ before we arrived. (had left / have left) | had left | O‘tgan boshqa voqeadan oldingi ish had + V3.
Past Perfect: She ___ the door before she went out. (lock; qisqartirmang) | had locked | Oldin bajarilgan ish had locked bilan aytiladi.
Faqat V3 ni tuzating: We had saw the film before. | seen | Had dan keyin V3 seen kerak.
I finished my homework before dinner. Finished ni Past Perfectga aylantiring; qisqartirmang. | I had finished my homework before dinner. | Had finished oldingi tugallangan ishni bildiradi.
@13.8
To‘g‘ri inkorni tanlang: A: He hadn't slept before the test. B: He didn't slept before the test. Faqat harfni yozing. | A | Past Perfect inkori hadn't + V3.
Past Perfect inkori: They ___ the tickets before the price rose. (not; buy; qisqartirmang) | had not bought | Had not dan keyin buy ning V3 shakli bought.
Tartibni tuzating: She had finished not when I called. Qisqartirmang. | She had not finished when I called. | Not had bilan V3 orasiga qo‘yiladi.
Inkor qiling: We had visited the island before that trip. Qisqartirmang. | We had not visited the island before that trip. | Past Perfect inkori had not bilan yasaladi.
@13.9
To‘g‘ri savolni tanlang: A: Had he left before noon? B: Did he had left before noon? Faqat harfni yozing. | A | Had ega oldiga chiqadi; did kerak emas.
___ she booked a room before travelling? Past Perfect yordamchisini yozing. | Had | Past Perfect savoli had bilan boshlanadi.
Savolni tuzating: Had you saw him before the meeting? | Had you seen him before the meeting? | Had dan keyin seen kerak.
Yes/no savol qiling: The train had departed before they arrived. | Had the train departed before they arrived? | Had ega oldiga chiqadi.
@13.10
To‘g‘ri savolni tanlang: A: Where had they parked? B: Where they had parked? Faqat harfni yozing. | A | Wh-savolda had ega oldiga chiqadi.
What ___ he promised before leaving? Past Perfect yordamchisini yozing. | had | Past Perfectda had + V3 keladi.
Savolni tuzating: Why had she went home before lunch? | Why had she gone home before lunch? | Go ning V3 shakli gone.
Where bilan joyni so‘rang: He had put the key in a drawer before leaving. | Where had he put the key before leaving? | Joy birikmasi o‘rniga where keladi.
@13.11
Had she finished before lunch? Ijobiy qisqa javobni tanlang: A: Yes, she had. B: Yes, she did. Faqat harfni yozing. | A | Had savoliga had bilan javob beriladi.
Had they met before? — No, they ___. Qisqartma yozing. | hadn't | Had not qisqartmasi hadn't.
Javobni tuzating: Had he paid before leaving? — Yes, he has. Faqat javobni yozing. | Yes, he had. | Savol Past Perfectda, had saqlanadi.
Had you and Tim booked before Friday? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we had not. | We nomidan had not bilan javob beriladi.
@13.12
Oldingi o‘tgan ish: The room was empty because everyone ___. (had left / leaves) | had left | Ketish xonaga qarashdan oldin sodir bo‘lgan.
Yangi keyingi voqea: After she had saved the file, she ___ the computer off. (switched / has switched) | switched | Keyingi tugallangan voqea Past Simpleda keladi.
O‘tgan kontekstga moslang: I was upset because I have lost my ticket. Have o‘rniga had qo‘yib yozing; qisqartirmang. | I was upset because I had lost my ticket. | Yo‘qotish xafa bo‘lishdan oldin sodir bo‘lgan.
Ikki fe’lni vergul bilan yozing: By the time we ___, the shop ___. (arrive — Past Simple; close — Past Perfect) | arrived, had closed | Yetib kelish vaqtiga qadar do‘kon yopilgan edi.
@13.13
To‘g‘ri shaklni tanlang: He was tired because he ___ all day. (had been walking / had walking) | had been walking | Past Perfect Continuous: had been + -ing.
Past Perfect Continuous: We ___ for an hour when help arrived. (wait; qisqartirmang) | had been waiting | O‘tgan nuqtaga qadar davom etgan kutish.
Yetishmayotgan been ni qo‘shing: She had studying all night before the test. Qisqartirmang. | She had been studying all night before the test. | Had bilan -ing orasida been kerak.
It was raining for hours before the match. Past Perfect Continuousga aylantiring; qisqartirmang. | It had been raining for hours before the match. | O‘yindan oldingi davomli jarayon had been raining.
@13.14
To‘g‘ri inkorni tanlang: A: She hadn't been exercising before the race. B: She didn't been exercising before the race. Faqat harfni yozing. | A | Hadn't been + -ing inkor shaklidir.
Past Perfect Continuous inkori: He ___ well before he changed jobs. (not; sleep; qisqartirmang) | had not been sleeping | Inkor tartibi had not been + -ing.
Tartibni tuzating: We had been not listening when the teacher asked us. Qisqartirmang. | We had not been listening when the teacher asked us. | Not had dan keyin keladi.
Inkor qiling: I had been using the car before it broke down. Qisqartirmang. | I had not been using the car before it broke down. | Had not been using oldingi davomli ishni inkor qiladi.
@13.15
To‘g‘ri savolni tanlang: A: Had they been training before the match? B: Did they been training before the match? Faqat harfni yozing. | A | Savolda had oldinga chiqadi.
___ she been travelling before she fell ill? Past Perfect Continuous yordamchisini yozing. | Had | Had birinchi yordamchi fe’l.
Savolni tuzating: Had you been worked before lunch? | Had you been working before lunch? | Been dan keyin -ing shakli kerak.
Yes/no savol qiling: The children had been swimming before the storm. | Had the children been swimming before the storm? | Had ega oldiga o‘tadi.
@13.16
To‘g‘ri savolni tanlang: A: Why had he been shouting? B: Why he had been shouting? Faqat harfni yozing. | A | Wh-savolda had ega oldiga chiqadi.
How long ___ they been living there before they moved? Past Perfect Continuous yordamchisini yozing. | had | Had been living davomiylikni so‘raydi.
Savolni tuzating: What had she been cook before we arrived? | What had she been cooking before we arrived? | Been dan keyin cooking kerak.
Where bilan joyni so‘rang: He had been working in a factory before he retired. | Where had he been working before he retired? | In a factory o‘rnini where egallaydi.
@13.17
Had it been raining before dawn? Ijobiy qisqa javobni tanlang: A: Yes, it had. B: Yes, it was. Faqat harfni yozing. | A | Qisqa javobda had saqlanadi.
Had they been arguing before you arrived? — No, they ___. Qisqartma yozing. | hadn't | Salbiy qisqa javob hadn't bilan yasaladi.
Javobni tuzating: Had he been studying? — Yes, he has. Faqat javobni yozing. | Yes, he had. | O‘tgan perfect savoliga had kerak.
Had you and Anna been running before breakfast? We bilan salbiy qisqa javob yozing; qisqartirmang. | No, we had not. | Qisqa javobda been running takrorlanmaydi.
@13.18
Tugallangan natija: By noon, she ___ all twenty envelopes. (had addressed / had been addressing) | had addressed | Barcha yigirma konvert tugallangan.
Jarayon, Past Perfect Continuous: His clothes were dusty because he ___ the attic for hours. (clean; qisqartirmang) | had been cleaning | Kiyimdagi chang oldingi davomli faoliyat natijasi.
Holat fe’lini tuzating: I had been knowing him for years before we worked together. Qisqartirmang. | I had known him for years before we worked together. | Know davomli shaklda ishlatilmaydi.
She had been painting the chairs. By five ni boshiga qo‘shing; barcha to‘rtta stul tayyor bo‘lganini all four chairs va Past Perfect Simple bilan yozing, qisqartirmang. | By five, she had painted all four chairs. | Tugallangan miqdor Past Perfect Simpleda ifodalanadi.
@14.1
To‘g‘ri qiyosiy shaklni tanlang: bigger / biger. | bigger | Big da oxirgi g ikki yoziladi.
This path is ___ than that one. (short; qiyosiy shakl) | shorter | Qisqa sifatga -er qo‘shiladi.
Faqat sifatni tuzating: This exercise is easyer than the last one. | easier | Undosh + y qiyosiy shaklda -ier bo‘ladi.
Cold sifatini qiyosiy darajaga aylantiring. | colder | Cold ga -er qo‘shiladi.
@14.2
To‘g‘ri qiyosiy shaklni tanlang: more dangerous / dangerouser. | more dangerous | Uzun sifat oldidan more keladi.
The new machine is ___ than the old one. (efficient; qiyosiy shakl) | more efficient | Efficient bilan more ishlatiladi.
Ortiqcha -er ni tuzating: This app is more usefuler than that one. Faqat to‘g‘ri qiyosiy iborani yozing. | more useful | Bir sifatda more va -er birga qo‘yilmaydi.
This task is difficult. Than the first one ni oxiriga qo‘shib qiyosiy gap qiling; qisqartirmang. | This task is more difficult than the first one. | Difficult ning qiyosiy shakli more difficult.
@14.3
To‘g‘ri qiyosiy shaklni tanlang: gooder / better. | better | Good ning istisno qiyosiy shakli better.
The station is ___ away than the school. (far; qiyosiy shakl) | farther; further | Masofa uchun farther ham further ham to‘g‘ri.
Faqat sifatni tuzating: The weather is badder today. | worse | Bad ning qiyosiy shakli worse.
This result is good. Than mine ni oxiriga qo‘shib qiyosiy gap qiling; qisqartirmang. | This result is better than mine. | Good qiyoslashda better bo‘ladi.
@14.4
To‘g‘ri orttirma shaklni tanlang: the tallest / the taller. | the tallest | Guruhdagi eng baland uchun the tallest.
Artikl bilan yozing: This is ___ street in town. (narrow; -est shakli) | the narrowest | Narrow uchun talab qilingan -est shakli narrowest.
Faqat sifatni tuzating: She is the happyest child here. | happiest | Happy → happiest.
Young sifatini orttirma darajaga aylantiring; artiklni qo‘shing. | the youngest | Young ga -est, oldiga the qo‘shiladi.
@14.5
To‘g‘ri orttirma shaklni tanlang: the best / the goodest. | the best | Good ning orttirma shakli the best.
Artikl bilan yozing: This is ___ question in the test. (difficult; orttirma shakl) | the most difficult | Uzun sifat bilan the most ishlatiladi.
Faqat orttirma birikmani tuzating: It was the most bad day of the trip. | the worst | Bad ning orttirma shakli the worst.
Useful sifatini orttirma darajaga aylantiring; artiklni qo‘shing. | the most useful | Useful oldiga the most qo‘yiladi.
@14.6
Tenglikni tanlang: A: This ruler is as long as that one. B: This ruler is longer than that one. Faqat harfni yozing. | A | As ... as tenglikni bildiradi.
This chair is as comfortable ___ that one. | as | As sifat as qolipi kerak.
Faqat ikkinchi bog‘lovchini tuzating: My bike is as fast than yours. | as | Tenglikda than emas, as ishlatiladi.
Anna is taller than Sara. Sara bilan boshlang, not as tall as ishlating; qisqartirmang. | Sara is not as tall as Anna. | Pastroq odam not as tall as bilan ifodalanadi.
@14.7
To‘g‘ri qiyosiy ravishni tanlang: more clearly / clearlier. | more clearly | -ly ravish oldiga more qo‘yiladi.
He runs ___ than I do. (fast; qiyosiy ravish) | faster | Fast ning qiyosiy shakli faster.
Faqat ravish birikmasini tuzating: She drives more careful than her brother. | more carefully | Drives harakati carefully ravishi bilan tavsiflanadi.
Badly ravishini qiyosiy darajaga aylantiring. | worse | Badly ning istisno qiyosiy shakli worse.
@14.8
Katta farq uchun tanlang: This train is ___ faster. (much / very) | much | Much qiyosiy shaklni kuchaytiradi.
Juda katta farq: This route is ___ shorter. (far / a bit) | far | Far katta farqni bildiradi.
Faqat kuchaytiruvchini tuzating: This phone is very cheaper. Very o‘rniga much ishlating. | much | Qiyosiy shakldan oldin much ishlatiladi.
This room is warmer. Ozgina farqni bildirish uchun a bit ni warmer oldiga qo‘shing; qisqartirmang. | This room is a bit warmer. | A bit kichik farqni bildiradi.
@14.9
Tasdiq gap: There are ___ apples in the basket. (some / any) | some | Oddiy tasdiq gapda some mos.
I haven't got ___ stamps. (some / any) | any | Oddiy inkor gapda any ishlatiladi.
Betaraf mavjudlik savolida so‘zni tanlang: Are there ___ buses after midnight? (some / any) | any | Betaraf savolda any ishlatiladi.
Inkor qiling, some o‘rniga any qo‘ying: We have some flour. Have got ishlatmang, qisqartirmang. | We do not have any flour. | Inkor do not have any bilan yasaladi.
@14.10
Taklif uchun darsdagi odatiy shaklni tanlang: Would you like ___ cake? (some / any) | some | Some taklifda odatiy miqdorni bildiradi.
Muloyim iltimos; some ishlating: May I borrow ___ paper, please? | some | Iltimosda some ishlatish mumkin.
Ortiqcha artiklni olib tashlang: Would you like a some soup? | Would you like some soup? | Some oldidan a qo‘yilmaydi.
Some water bilan muloyim iltimos tuzing; Can I have bilan boshlang, please bilan tugating. | Can I have some water, please? | Can I have some ... iltimos qolipi.
@14.11
Sanaladigan ko‘plik: How ___ pencils do you need? (much / many) | many | Pencils sanaladi, shuning uchun many.
We haven't got ___ space. (much / many) | much | Space bu ma’noda sanalmaydi.
Yetishmayotgan of ni qo‘shing: There is a lot traffic today. | There is a lot of traffic today.; There's a lot of traffic today. | Ot oldidan a lot of keladi.
There are many trees here. Many o‘rniga a lot of qo‘yib yozing. | There are a lot of trees here. | A lot of sanaladigan ko‘plik bilan ham keladi.
@14.12
Yetishmaslik: ___ people came, so the hall was almost empty. (Few / A few) | Few | Few juda kam, yetarli emas ma’nosida.
Bir nechta borligi: I have ___ coins, enough for the bus. (few / a few) | a few | A few oz bo‘lsa ham borligini bildiradi.
Faqat miqdor so‘zini tuzating: I have a little questions. A little o‘rniga a few ishlating. | a few | Questions sanaladigan ko‘plik.
We have some friends here. Some o‘rniga a few qo‘yib yozing. | We have a few friends here. | A few bir nechta do‘st borligini bildiradi.
@14.13
Yetishmaslik: There is ___ hope of finding it; it is probably lost forever. (little / a little) | little | Little umid juda kamligini bildiradi.
Ozgina, lekin yetarli: We have ___ money, enough for two tickets. (little / a little) | a little | A little ijobiy oz miqdorni bildiradi.
Faqat miqdor so‘zini tuzating: Add a few salt. A few o‘rniga a little ishlating. | a little | Salt sanalmaydigan ot.
There is some oil left. Some o‘rniga a little qo‘yib yozing. | There is a little oil left.; There's a little oil left. | A little sanalmaydigan oil bilan keladi.
@14.14
Ortiqchalik: The box is ___ heavy for me to lift. (too / enough) | too | Too ehtiyojdan ortiq darajani bildiradi.
We have ___ chairs for everyone. (enough / too) | enough | Enough ot oldidan kelib yetarlilikni bildiradi.
Tartibni tuzating: He is enough tall to reach it. | He is tall enough to reach it.; He's tall enough to reach it. | Enough sifatdan keyin keladi.
The room is too small. Inkor bilan ma’noni saqlang: The room ... big enough. Qisqartirmang. | The room is not big enough. | Juda kichik — yetarlicha katta emas.
@14.15
Ikkalasi ham: ___ twins wear glasses. (Both / Neither) | Both | Both ko‘plikdagi ikkala shaxsni bildiradi.
Ikki variantdan istalgan bittasi: You may choose ___ of these two desserts. (either / both) | either | Either ikki variantdan bittasini tanlashni bildiradi.
Faqat fe’lni tuzating: Both answers is correct. | are | Both ko‘plikdagi fe’lni talab qiladi.
The red key doesn't fit. The blue key doesn't fit. Neither key bilan bitta gap yozing. | Neither key fits. | Neither inkorni o‘zi bildiradi; key birlikda.
@14.16
Guruhning barchasi: ___ of the ten runners finished; nobody dropped out. (All / None) | All | Nobody dropped out hammasi tugatganini ko‘rsatadi.
Faqat bir qismi: ___ of the boxes are empty, but others are full. (Some / None) | Some | Bir qismi bo‘sh, boshqalari to‘la.
Yetishmayotgan of ni qo‘shing: Most the children are asleep. | Most of the children are asleep. | The bilan belgilangan guruh oldidan most of keladi.
No students passed. None of the students bilan qayta yozing. | None of the students passed. | None of guruhdagi hech kimni bildiradi.
"""]


def authored_bank():
    bank = {}
    current = None
    for pack in PACKS:
        for raw in pack.splitlines():
            row = raw.strip()
            if not row:
                continue
            if row.startswith('@'):
                current = row[1:]
                assert current not in bank, f'Duplicate topic: {current}'
                bank[current] = []
                continue
            parts = row.split(' | ')
            assert current and len(parts) == 3, f'Malformed authored row: {row}'
            prompt, answers, explanation = parts
            bank[current].append({
                'prompt': prompt,
                'answers': answers.split('; '),
                'explanation': explanation,
            })
    return bank


def normal(text):
    return re.sub(r'[^\w]+', ' ', text.casefold().replace('’', "'")).strip()


def validate(bank):
    grammar = json.loads((ROOT / 'src/data/intensive-grammar-map.json').read_text(encoding='utf-8'))
    existing = json.loads((ROOT / 'src/data/intensive-topic-exercises.json').read_text(encoding='utf-8'))
    expected = {f'{i}.{j}' for i, module in enumerate(grammar[:14], 1)
                for j in range(1, len(module['items']) + 1)}
    assert set(bank) == expected, f'Topic coverage mismatch: {set(bank) ^ expected}'
    seen = set()
    old_prompts = {normal(q['prompt']) for questions in existing.values() for q in questions}
    variants = 0
    for topic, questions in bank.items():
        assert len(questions) == 4, f'{topic}: expected four additions'
        local = set()
        for q in questions:
            assert set(q) == {'prompt', 'answers', 'explanation'}, (topic, q)
            assert all(isinstance(q[k], str) and q[k].strip() for k in ('prompt', 'explanation'))
            assert len(q['explanation']) > 15, (topic, 'explanation needs a fuller rationale')
            assert isinstance(q['answers'], list) and q['answers']
            assert all(isinstance(a, str) and a.strip() for a in q['answers'])
            assert len(set(map(normal, q['answers']))) == len(q['answers']), (topic, 'duplicate alternatives')
            p = normal(q['prompt'])
            assert p not in old_prompts, (topic, 'existing prompt duplicated', q['prompt'])
            assert p not in seen, (topic, 'new prompt duplicated', q['prompt'])
            seen.add(p)
            signature = (p, tuple(map(normal, q['answers'])))
            assert signature not in local
            local.add(signature)
            assert not re.search(r'placeholder|\bTODO\b|\bTBD\b|\ufffd', json.dumps(q, ensure_ascii=False), re.I)
            if 'Faqat harfni yozing' in q['prompt']:
                assert len(q['answers']) == 1 and q['answers'][0] in {'A', 'B'}
            if 'qisqartirmang' in q['prompt'].casefold():
                assert not any(re.search(r"\b(?:\w+n't|\w+'(?:re|ve|ll|d|m))\b", a) for a in q['answers']), (topic, 'unexpected contraction')
            if 'Qisqartma yozing' in q['prompt']:
                assert all("'" in a for a in q['answers']), (topic, 'missing contraction')
            variants += len(q['answers'])
    return len(bank), sum(map(len, bank.values())), variants


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Validate saved bank and compare with authored source')
    args = parser.parse_args()
    bank = authored_bank()
    topics, exercises, answers = validate(bank)
    if args.check:
        saved = json.loads(TARGET.read_text(encoding='utf-8'))
        assert saved == bank, 'Saved bank differs from the authored source'
        validate(saved)
    else:
        TARGET.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Validated {topics} topics, {exercises} exercises, {answers} accepted answers: {TARGET}')


if __name__ == '__main__':
    main()
