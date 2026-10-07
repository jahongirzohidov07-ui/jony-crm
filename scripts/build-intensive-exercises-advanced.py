"""Build the hand-authored module 15–27 supplement; never modify source banks.

Rows are prompt | accepted answers separated by ~ | Uzbek explanation.
G = gap, C = correction, T = constrained transformation, M = meaning/choice.
Run with --check to validate the checked-in JSON without writing anything.
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'src/data/intensive-exercises-advanced.json'
BANK = {}
PREFIX = {
    'G': 'Faqat bo‘shliqni to‘ldiring: ',
    'C': 'Ko‘rsatilgan xatoni tuzatib, butun gapni yozing: ',
    'T': '',
    'M': 'Faqat A yoki B ni yozing. ',
}


def add(block):
    topic = None
    for line in block.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('@'):
            topic = line[1:]
            assert topic not in BANK, topic
            BANK[topic] = []
            continue
        kind, body = line[0], line[2:]
        prompt, answers, explanation = (part.strip() for part in body.split('|'))
        assert kind in PREFIX and topic
        BANK[topic].append(dict(prompt=PREFIX[kind] + prompt,
                                answers=answers.split('~'), explanation=explanation))


add(r"""
@26.1
G Ega-fe’l mosligi: The quality of these photos ___ excellent. (is / are) | is | Eganing bosh so‘zi quality birlikda.
C Ega-fe’l mosligi: The keys to the storage room is missing. | The keys to the storage room are missing. | Bosh so‘z keys ko‘plikda, are kerak.
T Present Simple bilan to‘liq yozing: Each of the machines / need / regular maintenance. | Each of the machines needs regular maintenance. | Each birlikdagi fe’lni talab qiladi.
M “A list of repairs is on the desk” gapida fe’lni qaysi ot boshqaradi? A) List. B) Repairs. | A | Of dan keyingi repairs emas, list ega markazidir.
@26.2
G Noaniq olmosh: Nobody ___ where the spare key is. (know / knows) | knows | Nobody grammatik birlikdagi egadir.
C Ega-fe’l mosligi: Everyone have received an invitation. | Everyone has received an invitation. | Everyone bilan has ishlatiladi.
T Everything bilan qayta yozing: All the equipment is ready. | Everything is ready. | Everything birlikdagi is fe’lini oladi.
M “Someone has left their umbrella” gapidagi their: A) Someone ni majburiy ko‘plikka aylantiradi. B) Jinsi noma’lum bir kishiga ishora qilishi mumkin. | B | Singular they mumkin; someone bilan has saqlanadi.
@26.3
G Umumiy tushuncha: ___ education can change lives. The yoki zero yozing. | zero | Umumiy sanalmaydigan education artiklsiz ishlatiladi.
C Muayyan kitob haqida: Information in this booklet is outdated. Boshiga kerakli artiklni qo‘shing. | The information in this booklet is outdated. | Muayyan kitobdagi ma’lumot uchun the kerak.
T Umumiy ma’noda artiklni tuzating: The honesty is important in friendship. | Honesty is important in friendship. | Umumiy honesty artiklsiz keladi.
M Qaysi gap muayyan musiqani bildiradi? A) The music in this film is beautiful. B) Music helps me relax. | A | Aniqlovchi in this film ma’lum musiqani ajratadi.
@26.4
G Geografik nom: They crossed ___ Pacific Ocean. The yoki zero yozing. | the | Okean nomlari odatda the bilan keladi.
C Mamlakat nomi: She grew up in the Japan. | She grew up in Japan. | Japan nomi artiklsiz ishlatiladi.
T Britaniya inglizchasida talaba sifatidagi holatni yozing: My son / is at / university. Kerak bo‘lsa artikl qo‘shing. | My son is at university. | At university talabalik faoliyatini artiklsiz bildiradi.
M “I went to the school to repair a window” gapida the school: A) Maktabda o‘qish holati. B) Muayyan bino. | B | Bino nazarda tutilganda the ishlatiladi.
@26.5
G Go‘sht miqdori, butun qush emas: We need ___ for the soup. (some chicken / a chicken) | some chicken | Chicken go‘sht ma’nosida sanalmaydi; a chicken esa bitta qush.
C Material ma’nosi: This box is made of a paper. A ni olib tashlang. | This box is made of paper. | Paper material sifatida sanalmaydi.
T Ikki piyola choyni qisqa buyurtma qiling: Two cups of tea, please. Cups of ni tushiring. | Two teas, please. | Ichimlik nomi porsiya ma’nosida sanaladigan bo‘ladi.
M “There is a hair in my soup” gapida a hair: A) Bitta soch tolasi. B) Butun soch turmagi. | A | Hair alohida tola ma’nosida sanaladi.
@26.6
G Neytral sifat tartibi: a ___ table. (round wooden / wooden round) | round wooden | Shakl odatda materialdan oldin keladi.
C Neytral sifat tartibi: She bought a silk blue scarf. | She bought a blue silk scarf. | Rang materialdan oldin keladi.
T So‘zlarni odatiy tartibda joylang: a / Italian / beautiful / old / painting. | a beautiful old Italian painting | Fikr → yosh → kelib chiqish → ot odatiy tartibdir.
M Odatiy tartib: A) a small black metal box B) a metal black small box | A | O‘lcham → rang → material tartibi odatiy.
@26.7
G Hisni uyg‘otuvchi narsa: The ending was ___. (shocked / shocking) | shocking | -ing sifat sabab yoki ta’sir manbasini bildiradi.
C Hisni boshdan kechirgan odam: I was exhausting after the climb. | I was exhausted after the climb. | Odamning holati exhausted bilan ifodalanadi.
T Bored bilan yozing: The lecture bored the students. The students were bilan boshlang; by ishlating. | The students were bored by the lecture. | Bored ta’sir olgan kishilarning hissidir.
M “The children are excited” ma’nosi: A) Bolalar boshqalarni hayajonlantiradi. B) Bolalarning o‘zi hayajonda. | B | -ed sifat hisni boshdan kechiruvchini tavsiflaydi.
@26.8
G Kuchli sifat: The view was ___ breathtaking. (absolutely / very) | absolutely | Breathtaking bilan absolutely odatiy kuchaytirgichdir.
C Odatiy birikmani tuzating: The instructions were very impossible to follow. Very o‘rniga absolutely ishlating. | The instructions were absolutely impossible to follow. | Impossible chegaraviy sifat, absolutely bilan keladi.
T Very cold o‘rniga absolutely freezing ishlating: The lake was very cold. | The lake was absolutely freezing. | Freezing o‘zi juda sovuq ma’nosini beradi.
M Odatdagi birikma: A) very useful B) absolutely useful | A | Useful darajalanuvchi sifat; very bilan tabiiy keladi.
@26.9
G Tez-tezlik ravishi: She ___ checks the locks before bed. Always ni qo‘ying. | always | Always asosiy fe’ldan oldin joylashadi.
C Only ni egaga bog‘lang: Diyor only passed the test. Ma’no: faqat Diyor o‘tdi, boshqalar o‘tmadi. | Only Diyor passed the test. | Only egadan oldin tursa faqat shu kishini ajratadi.
T Usually ni is dan keyinga qo‘shing: The receptionist is helpful. | The receptionist is usually helpful. | Odat ravishi be dan keyin keladi.
M “She has nearly finished the course” ma’nosi: A) Kursni tugatganiga ancha bo‘lgan. B) Kurs deyarli tugagan, oz qismi qolgan. | B | Nearly tugallanishga yaqinlikni bildiradi.
@26.10
G Bilvosita ha/yo‘q savol: Could you tell me ___ this seat is taken? If/whether dan foydalaning. | if~whether | Ha/yo‘q savol if yoki whether bilan kiritiladi.
C Ichki so‘z tartibi: Do you know if is the office open on Fridays? | Do you know if the office is open on Fridays? | If dan keyin oddiy ega + fe’l tartibi keladi.
T Do you know whether bilan boshlang: Does this ticket include lunch? | Do you know whether this ticket includes lunch? | Does tushadi, includes ega bilan moslashadi.
M To‘g‘ri savol: A) Could you tell me whether they accept cash? B) Could you tell me whether do they accept cash? | A | Bilvosita qismda do yordamchisi kerak emas.
@26.11
G Bilvosita wh-savol: Do you know where the manager ___? (is / does) | is | Ichki savolda where + ega + is tartibi keladi.
C Bilvosita tartib: Could you explain how does this lock work? | Could you explain how this lock works? | Does tushadi, works asosiy fe’lga aylanadi.
T Can you tell me bilan boshlang: What time does the ferry depart? | Can you tell me what time the ferry departs? | Bilvosita qismda the ferry departs tartibi kerak.
M To‘g‘ri savol: A) Do you know why did he leave? B) Do you know why he left? | B | Ichki wh-savolda did inversiyasi ishlatilmaydi.
@26.12
G Faqat qisqa tag, inkorni qisqartiring: Dilnoza speaks Spanish, ___? | doesn't she | Tasdiq Present Simple uchun inkor does tagi kerak.
C Faqat tagni tuzating: We were on time, didn't we? | We were on time, weren't we? | Were bilan weren’t we mos keladi.
T Qisqa inkor tag qo‘shing, butun gapni yozing: He can ride a horse. | He can ride a horse, can't he? | Tasdiq can bilan inkor can’t he keladi.
M “I'm next, aren't I?” standart suhbat tagimi? A) Ha. B) Yo‘q, amn't I bo‘lishi shart. | A | I am uchun odatiy inkor tag aren’t I.
@26.13
G Faqat tag: Your sister hasn't called, ___? | has she | Inkor has not bilan tasdiq has she keladi.
C Tagni tuzating: We can't leave yet, do we? | We can't leave yet, can we?~We cannot leave yet, can we? | Inkor can bilan tasdiq can we ishlatiladi.
T Tasdiq tag qo‘shing, butun gapni yozing: The lights aren't working. | The lights aren't working, are they?~The lights are not working, are they? | Inkor are bilan tasdiq are they keladi.
M To‘g‘ri tag: A) She never complains, doesn't she? B) She never complains, does she? | B | Never inkor ma’noli; tag tasdiq bo‘ladi.
@26.14
G So bilan qo‘shiling: “I was exhausted.” — “___.” I ishlating. | So was I | Asosiy gapdagi was yordamchisi saqlanadi.
C Qo‘shilish yordamchisi: “I don't eat meat.” — “Neither am I.” Faqat javobni tuzating. | Neither do I | Don’t eat Present Simple; do kerak.
T “I will be there.” gapiga So bilan “Men ham” deb javob bering. | So will I. | So + will + I ijobiy qo‘shilishdir.
M “I couldn't sleep.” gapiga mos javob: A) Neither could I. B) So did I. | A | Inkor fikrga neither va bir xil modal kerak.
@26.15
G Hozirgi faol jarayon: I ___ about changing jobs right now. (think / am thinking) | am thinking | Think about faol o‘ylash jarayoni bo‘lishi mumkin.
C Egalik holati: She is having two brothers. | She has two brothers. | Oila a’zosi borligi holat, Present Simple kerak.
T Hozirgi harakatni Present Continuous bilan yozing: The doctor / see / a patient / now. | The doctor is seeing a patient now. | See bu yerda qabul qilish harakati, davomiy shakl mumkin.
M “This soup tastes salty” gapida taste: A) Holat yoki xususiyatni bildiradi. B) Oshpazning faol tatib ko‘rish jarayonini bildiradi. | A | Soup tastes ta’m xususiyatini, holatni bildiradi.
@27.1
G Future Continuous: At nine on Sunday, I ___ (sail) across the lake. | will be sailing | Kelajakdagi muayyan paytda davom etadigan ish: will be + -ing.
C Davomiy shakl: This time tomorrow, she will be drive through the desert. | This time tomorrow, she will be driving through the desert.~This time tomorrow, she'll be driving through the desert. | Be dan keyin driving kerak.
T Future Continuous qiling: We / rehearse / at seven tomorrow. | We will be rehearsing at seven tomorrow.~We'll be rehearsing at seven tomorrow. | Will be rehearsing o‘sha paytdagi jarayondir.
M “At noon, I'll be interviewing candidates” ma’nosi: A) Tushda suhbat jarayoni ketayotgan bo‘ladi. B) Barcha suhbatlar tongda tugagan bo‘ladi. | A | Future Continuous davom etayotgan kelajak ishini bildiradi.
@27.2
G Future Continuous inkori: At eight tomorrow, he ___ (not sleep). | will not be sleeping~won't be sleeping | Inkor shakli will not be + -ing.
C Inkor davomiy: They won't be wait outside in the rain. | They won't be waiting outside in the rain.~They will not be waiting outside in the rain. | Be dan keyin waiting kerak.
T Inkor qiling: I will be driving at midnight. | I will not be driving at midnight.~I won't be driving at midnight.~I'll not be driving at midnight. | Not will dan keyin keladi.
M “She won't be teaching next Friday morning” ma’nosi: A) U hech qachon dars bermaydi. B) O‘sha tongda dars jarayonida bo‘lmaydi. | B | Kelajakdagi aniq vaqt jarayoni inkor qilinmoqda.
@27.3
G Future Continuous savoli: Will your aunt ___ (travel) with us next week? | be travelling~be traveling | Will + ega + be + -ing kerak.
C Savol tartibi: Will be the team training at six? | Will the team be training at six? | Will dan keyin ega keladi.
T Ha/yo‘q savoliga aylantiring: She will be presenting the awards tonight. | Will she be presenting the awards tonight? | Will egadan oldinga o‘tadi.
M To‘g‘ri savol: A) Will you be using the oven this evening? B) Will you using the oven this evening? | A | Be Future Continuous savolida zarur.
@27.4
G Future Continuous wh-savoli: What will the children ___ (study) at ten tomorrow? | be studying | Will dan keyingi qism be studying.
C Savol tartibi: Where you will be working next month? | Where will you be working next month? | Where + will + ega + be + -ing.
T Who bilan to‘ldiruvchini so‘rang: You will be meeting the director at noon. At noon ni saqlang. | Who will you be meeting at noon?~Whom will you be meeting at noon? | Kim bilan uchrashish rejalanganini wh-savol so‘raydi.
M “What will you be doing at dawn?” nimani so‘raydi? A) Tonggacha tugatilgan ishlar sonini. B) Tong paytida davom etadigan ishni. | B | Be doing kelajakdagi jarayonni so‘raydi.
@27.5
G Future Perfect: By the end of the week, we ___ (paint) all six rooms. | will have painted | Muddatgacha tugallanish: will have + V3.
C V3: By May, he will have wrote three chapters. | By May, he will have written three chapters.~By May, he'll have written three chapters. | Write fe’lining V3 shakli written.
T Future Perfect qiling: She / save / enough money / by December. | She will have saved enough money by December.~She'll have saved enough money by December. | By December muddatiga natija tayyor bo‘ladi.
M “By then, the ice will have melted” ma’nosi: A) O‘sha paytgacha muz erib bo‘ladi. B) O‘sha paytda muzlash boshlanadi. | A | Future Perfect tugallangan kelajak natijasidir.
@27.6
G Future Perfect inkori: By tonight, the team ___ (not finish) the survey. | will not have finished~won't have finished | Will not have + V3 muddatgacha tugamaslikni bildiradi.
C Perfect inkori: I won't have readed all the files by then. | I won't have read all the files by then.~I will not have read all the files by then. | Read fe’lining V3 yozilishi read.
T Inkor qiling: The workers will have repaired the roof by Tuesday. | The workers will not have repaired the roof by Tuesday.~The workers won't have repaired the roof by Tuesday. | Not will dan keyin keladi.
M “We won't have eaten by six” ma’nosi: A) Soat oltida ovqat yeyish taqiqlangan. B) Soat oltigacha ovqatlanib bo‘lmaymiz. | B | Future Perfect inkori muddatgacha yakunlanmaslikdir.
@27.7
G Future Perfect savoli: Will the builders ___ (complete) the extension by July? | have completed | Will + ega + have + V3.
C Savol tartibi: Will have she returned by Monday? | Will she have returned by Monday? | Will dan keyin ega, keyin have keladi.
T Ha/yo‘q savoliga aylantiring: You will have read the proposal by noon. | Will you have read the proposal by noon? | Kelajakdagi yakun savolida will oldinga o‘tadi.
M To‘g‘ri Future Perfect savoli: A) Will the plane have landed by nine? B) Will the plane has landed by nine? | A | Will dan keyin have asosiy shaklda bo‘ladi.
@27.8
G Qisqa ijobiy javob: “Will your mother be helping tonight?” — “Yes, she ___.” | will | Future Continuous qisqa javobida faqat will qoladi.
C Qisqa javob: “Will you be working at noon?” — “Yes, I am.” Faqat javobni tuzating. | Yes, I will. | Will savoliga will bilan javob beriladi.
T “Will Jamshid be travelling tomorrow?” savoliga he bilan qisqa inkor javob bering. | No, he will not.~No, he won't. | No + ega + won’t; be travelling takrorlanmaydi.
M “Will you and Lola be joining us?” Ikkalangiz nomidan: A) Yes, I am. B) Yes, we will. | B | Ko‘plikdagi o‘zimiz uchun we, yordamchi will.
@27.9
G Future Perfect wh-savoli: How much will you ___ (save) by your birthday? | have saved | Wh-so‘zdan keyin will + ega + have + V3.
C Savol tartibi: Which tasks she will have completed by Friday? | Which tasks will she have completed by Friday? | Will ega oldida turishi kerak.
T How many bilan sonni so‘rang: They will have planted fifty trees by April. | How many trees will they have planted by April? | How many trees tugallangan ish miqdorini so‘raydi.
M “What will you have learned by the end?” nimani so‘raydi? A) Yakun muddatigacha erishilgan bilimni. B) Faqat ayni paytdagi darsni. | A | Future Perfect kelajak chegarasidagi natijani so‘raydi.
@27.10
G Qisqa javob: “Will the guests have arrived by then?” — “Yes, they ___.” | will | Future Perfect qisqa javobida will ishlatiladi.
C Qisqa javob: “Will he have finished by six?” — “No, he hasn't.” Faqat javobni tuzating. | No, he won't.~No, he will not. | Savoldagi yordamchi will inkorda won’t bo‘ladi.
T “Will you and your sister have moved by May?” savoliga we bilan qisqa ijobiy javob bering. | Yes, we will. | Qisqa javobda have moved takrorlanmaydi.
M “Will the paint have dried by noon?” savoliga qisqa inkor: A) No, it doesn't. B) No, it won't. | B | Will savoliga won’t mos keladi.
@27.11
G Davom etayotgan kelajak ish: At nine, the flight is still in progress. We ___. (will be flying / will have landed) | will be flying | O‘sha paytdagi jarayon Future Continuous talab qiladi.
C Muddatgacha tugallanish uchun zamonni almashtiring: By dusk, they will be reaching the summit. Will have ishlating. | By dusk, they will have reached the summit.~By dusk, they'll have reached the summit. | Will have reached muddatgacha yakuniy natijadir.
T Tugallangan natijaga aylantiring; at o‘rniga by: At noon, I will be cleaning the kitchen. | By noon, I will have cleaned the kitchen.~By noon, I'll have cleaned the kitchen. | At + jarayon o‘rniga by + tugallangan natija keladi.
M “At five, I'll be packing” va “By five, I'll have packed”: beshgacha ish bitishi qaysida? A) Ikkinchi gapda. B) Birinchi gapda. | A | Have packed ish yakunlangan bo‘lishini bildiradi.
@27.12
G Yakun chegarasi: The repairs will have been completed ___ the time school starts. | by | By the time kelajakdagi chegara vaqtni bildiradi.
C Vaqt qismi: By the time you will wake up, I will have left. | By the time you wake up, I will have left.~By the time you wake up, I'll have left. | Vaqt qismida kelajak ma’nosi Present Simple bilan beriladi.
T By the time bilan birlashtiring: You arrive. We will already have cooked dinner. You arrive qismini boshga qo‘ying. | By the time you arrive, we will already have cooked dinner.~By the time you arrive, we'll already have cooked dinner. | Chegara vaqtgacha ovqat tayyor bo‘ladi.
M “Submit it by Thursday” nimani bildiradi? A) Faqat payshanbadan keyin. B) Eng kechi payshanbagacha. | B | By yakuniy muddatni bildiradi.
@27.13
G O‘tgan reja: We ___ (visit) the castle, but the road was closed. Was/were going to ishlating. | were going to visit | We bilan were going to oldingi rejani bildiradi.
C O‘tmish nuqtasidan kelajak: She knew that she will return one day. | She knew that she would return one day. | Knew dan keyingi kelajak would bilan beriladi.
T Was going to bilan yozing: I planned to bake a cake, but the oven broke. I bilan boshlang, but qismini saqlang. | I was going to bake a cake, but the oven broke. | Was going to amalga oshmagan oldingi rejani bildiradi.
M “In 1999, nobody imagined that she would become famous” gapida would: A) O‘tmishdan qaralgandagi kelajak. B) Hozirgi ruxsat. | A | Would o‘tgan nuqtadan keyingi voqeani bildiradi.
""")

add(r"""
@24.1
G Fe’l qolipi: She admitted ___ the instructions. (ignore) | ignoring~having ignored | Admit dan keyin -ing keladi.
C Enjoy qolipi: My cousins enjoy to camp by the river. | My cousins enjoy camping by the river. | Enjoy + -ing ishlatiladi.
T Finish + -ing bilan birlashtiring: He wrote the report. He finished it at noon. He finished bilan boshlang. | He finished writing the report at noon. | Finish dan keyin writing kerak.
M To‘g‘ri fe’l qolipi: A) We considered moving abroad. B) We considered to move abroad. | A | Consider odatda -ing shaklini oladi.
@24.2
G Infinitiv: They hope ___ the finals. (reach) | to reach | Hope dan keyin to-infinitive keladi.
C Decide qolipi: I decided taking the evening class. | I decided to take the evening class. | Decide + to-infinitive ishlatiladi.
T Plan to bilan qayta yozing: We are planning a visit to the island. We plan bilan boshlang. | We plan to visit the island. | Plan to visit rejalashtirilgan harakatni bildiradi.
M To‘g‘ri gap: A) He refused signing the receipt. B) He refused to sign the receipt. | B | Refuse dan keyin to-infinitive kerak.
@24.3
G Object + infinitive: The tutor encouraged me ___ again. (apply) | to apply | Encourage + shaxs + to-infinitive.
C Want qolipi: I want my brother learn to cook. | I want my brother to learn to cook. | Want dan keyin shaxs va to-infinitive keladi.
T Expect + object + to bilan yozing: I expect that the guests will arrive early. | I expect the guests to arrive early. | The guests infinitiv oldidagi to‘ldiruvchidir.
M “She persuaded him to stay” gapida kim qoladi? A) He. B) She. | A | Him keyingi stay harakatining bajaruvchisidir.
@24.4
G Bare infinitive: The funny ending made everyone ___ (laugh). | laugh | Make + object dan keyin to siz infinitiv keladi.
C Let qolipi: Let the children to choose their books. | Let the children choose their books. | Let + object + asosiy fe’l.
T Make bilan yozing: The loud noise caused the baby to wake up. The loud noise made bilan boshlang. | The loud noise made the baby wake up. | Made the baby dan keyin wake to siz keladi.
M Faol gapdagi to‘g‘ri qolip: A) They made us to wait. B) They made us wait. | B | Faol make dan keyin bare infinitive kerak.
@24.5
G Modaldan keyin: She might ___ us later. (join) | join | Might dan keyin asosiy shakl ishlatiladi.
C Modal qolipi: He should to read the small print. | He should read the small print. | Should dan keyin to qo‘yilmaydi.
T Must bilan qayta yozing: It is essential that she checks every label. She bilan boshlang. | She must check every label. | Must dan keyin checks emas, check keladi.
M To‘g‘ri gap: A) The battery may need replacing. B) The battery may needs replacing. | A | Modal ega bilan o‘zgarmaydigan asosiy fe’lni oladi.
@24.6
G Predlogdan keyin: He apologised for ___ late. (arrive) | arriving | For predlogidan keyin -ing ishlatiladi.
C Predlog + fe’l: We are worried about lose our luggage. | We are worried about losing our luggage. | About dan keyin losing kerak.
T Without + -ing bilan birlashtiring: She left. She did not lock the door. She left bilan boshlang. | She left without locking the door. | Without locking bajarmasdan ketishni bildiradi.
M “I look forward to meeting you” gapidagi to: A) Infinitiv belgisi. B) Predlog. | B | Bu birikmada to predlog, undan keyin meeting keladi.
@24.7
G Maqsad infinitivi: I brought a torch ___ the path. (light) | to light | To light nima maqsadda olib kelinganini bildiradi.
C Maqsad: She went to the post office for send a parcel. To-infinitive ishlating. | She went to the post office to send a parcel. | Maqsad uchun to send kerak.
T To bilan birlashtiring: We opened the windows. We wanted to let in fresh air. | We opened the windows to let in fresh air. | To let in harakat maqsadini beradi.
M “I called to confirm the booking” gapidagi infinitiv: A) Qo‘ng‘iroq maqsadini bildiradi. B) Qo‘ng‘iroq vaqtini bildiradi. | A | To confirm nima uchun qo‘ng‘iroq qilinganini aytadi.
@24.8
G Gerund ega: ___ vegetables at home saves money. (grow) | Growing | Growing harakat nomi bo‘lib ega vazifasida keladi.
C Gerund egaga mos fe’l: Swimming in cold water require practice. | Swimming in cold water requires practice. | Bitta gerund birikma birlikdagi egadir.
T Gerund bilan boshlang: It takes patience to learn a new script. | Learning a new script takes patience. | Learning a new script gap egasiga aylanadi.
M Qaysi gapda cooking ega? A) I enjoy cooking. B) Cooking relaxes me. | B | Cooking relaxes gapida harakat nomi egadir.
@24.9
G Sifat + infinitiv: This label is difficult ___ in dim light. (read) | to read | Difficult dan keyin to-infinitive ishlatiladi.
C Sifat qolipi: I was pleased hearing that you had recovered. To-infinitive ishlating. | I was pleased to hear that you had recovered. | Pleased to hear xursandlik sababini bildiradi.
T It is + sifat + to qolipiga o‘tkazing: Finding this address is hard. | It is hard to find this address.~It's hard to find this address. | Sifatdan keyingi infinitiv baholanayotgan ishni bildiradi.
M To‘g‘ri gap: A) Are you ready to order? B) Are you ready order? | A | Ready dan keyin to order kerak.
@24.10
G Yetarli daraja: The shelf is low ___ for a child to reach. | enough | Sifat + enough + to-infinitive.
C Enough joyi: This bag is enough big to hold the tent. | This bag is big enough to hold the tent. | Enough sifatdan keyin keladi.
T Too…to bilan birlashtiring: The water is very deep. We cannot stand in it. The water bilan boshlang; for us ishlating. | The water is too deep for us to stand in. | Too deep chegaradan ortiq chuqurlikni bildiradi.
M “He is too tired to concentrate” ma’nosi: A) Yetarli dam olgan. B) Charchoq sabab diqqatini jamlay olmaydi. | B | Too…to natijani amalga oshirishga to‘siqni bildiradi.
@24.11
G Odatdan voz kechdi: She stopped ___ fizzy drinks last month. (drinking / to drink) | drinking | Stop doing shu ishni bas qilishdir.
C Maqsad uchun to‘xtadi: We stopped buying petrol on our way home. Ma’no: benzin olish uchun yo‘lda to‘xtadik; to-infinitive ishlating. | We stopped to buy petrol on our way home. | Stop to do boshqa ishni qilish uchun to‘xtashdir.
T Stop + -ing bilan yozing: The baby no longer cried. The baby stopped bilan boshlang. | The baby stopped crying. | Stopped crying yig‘lash tugaganini bildiradi.
M “She stopped to answer her phone” ma’nosi: A) Telefoniga javob berish uchun to‘xtadi. B) Telefoniga javob berishni butunlay bas qildi. | A | To answer to‘xtash maqsadidir.
@24.12
G Bajarilishi kerak ish: Don't forget ___ the door before bed. (locking / to lock) | to lock | Forget to do bajarilishi kerak ishni unutishdir.
C Voqea xotirasi: I remember to meet her at school ten years ago. -ing ishlating. | I remember meeting her at school ten years ago. | Remember doing oldingi voqeani eslashdir.
T Remember to bilan eslatma yozing: You must bring your ID tomorrow. | Remember to bring your ID tomorrow. | Remember to bring kelajakdagi ishni eslatadi.
M “I remembered posting the letter” ma’nosi: A) Xat jo‘natishni endi rejalashtirdim. B) Xatni jo‘natganim xotiramga keldi. | B | Remembered doing oldingi bajarilgan ish xotirasidir.
@24.13
G Tajriba sifatida usul: Try ___ the router closer to the laptop. (moving / to move) | moving | Try doing muammoni yechish uchun usulni sinashdir.
C Qiyin urinish, muvaffaqiyatsiz: He tried reaching the top shelf, but he was too short. To-infinitive ishlating. | He tried to reach the top shelf, but he was too short. | Try to do ishni bajarishga urinishni ta’kidlaydi.
T Try + -ing bilan maslahat bering: Perhaps sleeping with an extra pillow will help. Try bilan boshlang. | Try sleeping with an extra pillow. | Sinov uchun tavsiya try sleeping bilan beriladi.
M “I tried to keep my eyes open, but fell asleep” ma’nosi: A) Uyg‘oq qolishga urindim, ammo uddalay olmadim. B) Uyg‘oq qolish usulini muvaffaqiyatli sinadim. | A | Try to do natijasi kafolatlanmagan urinishdir.
@24.14
G Ko‘nikkanlik: We are used to ___ in a noisy office. (work) | working | Be used to dan keyin -ing keladi.
C Oldingi odat: She used to living above a shop. | She used to live above a shop. | Used to + asosiy fe’l oldingi odatdir.
T Be used to bilan yozing: Speaking in public is familiar and comfortable for him. He bilan boshlang. | He is used to speaking in public.~He's used to speaking in public. | Be used to doing o‘rganib qolganlikni bildiradi.
M “I used to get up at five” ma’nosi: A) Hozir beshda turishga ko‘nikish jarayonidaman. B) Ilgari beshda turardim. | B | Used to oldingi, hozir davom etmasligi mumkin bo‘lgan odatdir.
@24.15
G Ko‘nikish jarayoni: I am getting used to ___ contact lenses. (wear) | wearing | Get used to dan keyin -ing keladi.
C Ko‘nikish qolipi: They soon got used to live in a small town. | They soon got used to living in a small town. | To bu yerda predlog; living kerak.
T Get used to bilan yozing: Gradually, the new timetable became familiar to me. I gradually bilan boshlang, Past Simple. | I gradually got used to the new timetable. | Got used to moslashish tugaganini bildiradi.
M “You will get used to the noise” ma’nosi: A) Shovqinga asta-sekin ko‘nikasiz. B) Ilgari shovqin qilardingiz. | A | Get used to yangi sharoitga moslashishdir.
@24.16
G Ajraladigan fe’l, olmosh: Please pick ___ up before someone trips. (the cable o‘rniga olmosh) | it | Pick up bilan olmosh fe’l va yuklama orasida keladi.
C Ajralmaydigan fe’l: She looks her little brother after. | She looks after her little brother. | Look after ajralmaydi.
T The jacket o‘rniga it ishlating: Take off the jacket. | Take it off. | Ajraladigan take off bilan it o‘rtaga qo‘yiladi.
M To‘g‘ri gap: A) We ran an old friend into. B) We ran into an old friend. | B | Run into bu ma’noda ajralmaydigan birikmadir.
@24.17
G Fe’lga mos predlog: You can rely ___ me. | on | Rely on — ishonib suyanmoq.
C Sifat predlogi: She is good in solving puzzles. | She is good at solving puzzles. | Good at + ot yoki -ing qobiliyatni bildiradi.
T Predlogni qo‘shib to‘liq gap yozing: I / am interested / astronomy. | I am interested in astronomy.~I'm interested in astronomy. | Interested in — biror narsaga qiziqish.
M To‘g‘ri birikma: A) listen to the announcement B) listen the announcement | A | Listen dan keyin to predlogi kerak.
@24.18
G Xizmatni bajartirish: She had her portrait ___ by a local artist. (paint) | painted | Have + object + V3 ishni boshqaga bajartirishdir.
C Xizmat qolipi: I got my watch repair yesterday. | I got my watch repaired yesterday. | Object dan keyin repaired V3 shakli kerak.
T Had bilan yozing: A dentist cleaned my teeth yesterday. I had bilan boshlang; bajaruvchini tushiring. | I had my teeth cleaned yesterday. | I had my teeth cleaned xizmat olganimni bildiradi.
M “We had our roof inspected” gapida odatda kim tekshirgan? A) O‘zimiz. B) Biz yollagan boshqa kishi. | B | Have something done xizmatni boshqa kishi bajarishini bildiradi.
@25.1
G Qarama-qarshilik: I knocked twice, ___ nobody opened the door. (and / but / or) | but | But qarama-qarshi natijani bog‘laydi.
C Tanlovni ifodalang, and o‘rniga mos bog‘lovchi: You can rent a bike and walk; choose one. | You can rent a bike or walk; choose one. | Or muqobil variantlarni bog‘laydi.
T And bilan birlashtiring; ikkinchi he ni tushiring: He washed the cups. He dried them. | He washed the cups and dried them. | And ketma-ket yoki qo‘shimcha ishlarni ulaydi.
M “Hurry, or you will miss the train” gapida or: A) Aks holda degan ogohlantirish. B) Ikkala ish ham bajarilganini. | A | Buyruqdan keyingi or aks holda ma’nosini beradi.
@25.2
G Sabab + gap: We took a taxi ___ the buses had stopped. (because / because of) | because | Because dan keyin ega va fe’lli gap keladi.
C Sabab tuzilmasi: Since of the lift is broken, use the stairs. | Since the lift is broken, use the stairs. | Since sabab gapini to‘g‘ridan-to‘g‘ri kiritadi.
T As bilan boshlang va birlashtiring: The road was flooded. We turned back. | As the road was flooded, we turned back. | As sabab ma’nosida ishlatilgan.
M “Since you're here, help me move this desk” gapida since: A) O‘tgan vaqtdan boshlab. B) Sabab. | B | Since you’re here kelib turganingiz sababini bildiradi.
@25.3
G Ot birikmasi: The event was moved indoors ___ the strong wind. (because / because of) | because of | Because of dan keyin ot birikmasi keladi.
C Due to qolipi: The delay was due the strike. | The delay was due to the strike. | Due to to‘liq birikma bo‘lishi kerak.
T Because of bilan yozing: The path was closed because there was a landslide. The path bilan boshlang. | The path was closed because of a landslide. | Because + gap o‘rniga because of + ot keladi.
M To‘g‘ri birikma: A) due to poor visibility B) due to it was foggy | A | Due to odatda ot yoki ot birikmasini oladi.
@25.4
G Natija: The water supply was cut off, ___ we bought bottled water. (so / because) | so | So sababdan keyin natijani kiritadi.
C Bog‘lanish ma’nosi: The key broke, because we couldn't open the door. Because o‘rniga so ishlating. | The key broke, so we couldn't open the door.~The key broke, so we could not open the door. | Ocholmaslik kalit sinishining natijasidir.
T Therefore bilan ulang, nuqtali vergul ishlating: The evidence was weak. The case was dismissed. | The evidence was weak; therefore, the case was dismissed. | Therefore natija bildiradi; mustaqil gaplar nuqtali vergul bilan ajraladi.
M “The roads froze. As a result, several schools closed.” Yopilish: A) Sabab. B) Natija. | B | As a result oqibatni kiritadi.
@25.5
G Zidlik + gap: ___ she was nervous, she gave a clear presentation. (Although / Despite) | Although | Although dan keyin to‘liq gap keladi.
C Ortiqcha but ni olib tashlang: Although the queue was long, but we waited. | Although the queue was long, we waited. | Although va but bitta juft gapda birga kerak emas.
T Even though bilan boshlang: The tickets cost a lot. We bought them. | Even though the tickets cost a lot, we bought them. | Even though kutilmagan zid natijani kuchliroq ta’kidlaydi.
M “Although he apologised, she remained upset” ma’nosi: A) Uzr so‘ragani uchun xafa bo‘ldi. B) Uzr so‘ragan bo‘lsa ham xafaligi qolgan. | B | Although yon berish va zidlikni bildiradi.
@25.6
G Despite + -ing: Despite ___ (feel) unwell, she attended the briefing. | feeling | Despite dan keyin ot yoki -ing keladi.
C Ortiqcha predlog: Despite of the heat, they kept working. | Despite the heat, they kept working. | Despite dan keyin of ishlatilmaydi.
T In spite of bilan yozing: Although he was tired, he finished the race. Being ishlating. | In spite of being tired, he finished the race. | In spite of dan keyin being tired otlashgan qismdir.
M To‘g‘ri gap: A) Despite the heavy traffic, we arrived early. B) Despite the traffic was heavy, we arrived early. | A | Despite to‘g‘ridan-to‘g‘ri to‘liq gapni olmaydi.
@25.7
G Qarshi fikr: The task looked impossible. ___, they completed it. (Nevertheless / Therefore) | Nevertheless | Nevertheless kutilgan natijaga qarshi fikrni kiritadi.
M Standart tinish belgisi: A) It was costly, however, we agreed. B) It was costly; however, we agreed. | B | However ikki mustaqil gapni faqat vergul bilan bog‘lamaydi.
T But o‘rniga However ishlating; ikkita gap yozing: The room was small, but it was comfortable. | The room was small. However, it was comfortable. | However yangi gapdagi qarshi fikrni kiritadi.
M “He lacked experience. Nevertheless, he succeeded.” ma’nosi: A) Tajribasi kam bo‘lsa ham muvaffaqiyatga erishdi. B) Tajribasi ko‘pligi sabab muvaffaqiyatga erishdi. | A | Nevertheless to‘siqqa qaramay natijani bildiradi.
@25.8
G Taqqoslash: This model is light, ___ the older one is heavy. (whereas / because) | whereas | Whereas ikki modelning farqini ko‘rsatadi.
C Qarama-qarshi taqqoslashda because ni whereas ga almashtiring: I prefer working alone, because she prefers teamwork. | I prefer working alone, whereas she prefers teamwork. | Whereas sabab emas, farqni bildiradi.
T While bilan birlashtiring; The north bilan boshlang: The north gets snow. The south stays warm. | The north gets snow, while the south stays warm. | While bu yerda ikki hududni qarama-qarshi qo‘yadi.
M Qaysi while taqqoslashni bildiradi? A) I fell while I was skiing. B) Ben cycles, while Anna takes the bus. | B | Ikki kishining odati solishtirilmoqda.
@25.9
G Sifat + natija: The instructions were ___ unclear that we called for help. | so | So + sifat + that natijani beradi.
C Ravish kuchaytirgichi: She ran such fast that nobody caught her. | She ran so fast that nobody caught her. | Ravish fast oldidan so keladi.
T So…that bilan birlashtiring: The box was very heavy. We needed a trolley. | The box was so heavy that we needed a trolley. | So heavy daraja sababli natijani bildiradi.
M “He spoke so quietly that I missed his name” gapida I missed his name: A) Natija. B) Maqsad. | A | So…that maqsad emas, daraja natijasidir.
@25.10
G Ot birikmasi: It was ___ a windy day that the ferry stayed in port. | such | Such a + sifat + birlik ot + that.
C Artikl: It was such useful tool that everyone wanted one. | It was such a useful tool that everyone wanted one. | Birlik sanaladigan tool oldidan a kerak.
T Such…that bilan qayta yozing: The music was so loud that we couldn't talk. It was bilan boshlang. | It was such loud music that we couldn't talk.~It was such loud music that we could not talk. | Music sanalmaydi; such loud music, artiklsiz.
M To‘g‘ri gap: A) They were such a friendly people. B) They were such friendly people. | B | Ko‘plik people oldidan a qo‘yilmaydi.
@25.11
G Maqsad: She labelled every box in order ___ confusion. (avoid) | to avoid | In order to + asosiy fe’l maqsad bildiradi.
C Maqsad qolipi: We whispered so as not wake the baby. | We whispered so as not to wake the baby. | Inkor maqsad so as not to + fe’l.
T In order to bilan birlashtiring: I took notes. I wanted to remember the details. | I took notes in order to remember the details. | Infinitiv bir xil eganing maqsadini ko‘rsatadi.
M “They left early so as to avoid the crowds” ma’nosi: A) Gavjumlikdan qochish uchun erta ketishdi. B) Erta ketgani uchun olomon paydo bo‘ldi. | A | So as to maqsadni ifodalaydi.
@25.12
G Maqsad + ega-fe’l: We drew a map ___ visitors could find the hall. | so that | So that dan keyin to‘liq gap keladi.
C Maqsad gapi: She moved aside so that I to see the board. Could ishlating. | She moved aside so that I could see the board. | So that + ega + could + fe’l kerak.
T So that bilan birlashtiring: I enlarged the text. I wanted my grandfather to be able to read it. Could ishlating. | I enlarged the text so that my grandfather could read it. | Ikki xil ega maqsad gapida so that bilan bog‘lanadi.
M “Speak clearly so that everyone can hear” ma’nosi: A) Hamma allaqachon eshitgani uchun. B) Hamma eshita olishi uchun. | B | So that bu gapda maqsadni bildiradi.
@25.13
G Kelajak vaqt qismi: We will begin after everyone ___ (arrive). | arrives | After vaqt qismida kelajak uchun Present Simple keladi.
C Vaqt qismi: I will unlock the door before you will arrive. | I will unlock the door before you arrive.~I'll unlock the door before you arrive. | Before dan keyin oddiy kelajak ma’nosida will kerak emas.
T As soon as bilan boshlang: The lights come on. We will enter immediately. | As soon as the lights come on, we will enter.~As soon as the lights come on, we'll enter. | As soon as darhol keyingi harakatni bildiradi.
M “Stay here until I call” ma’nosi: A) Qo‘ng‘iroq qilgunimcha shu yerda qoling. B) Qo‘ng‘iroq qilganimdan keyin keling. | A | Until harakat davom etadigan chegarani bildiradi.
@25.14
G Oldindan ehtiyot chorasi: Bring a spare shirt ___ this one gets wet. (in case / if) | in case | In case ehtimoliy muammo uchun tayyorgarlikdir.
C Ehtiyot gapidagi zamon: Take some cash in case the card machine will fail. | Take some cash in case the card machine fails. | In case dan keyin kelajak uchun Present Simple kerak.
T In case bilan birlashtiring: I wrote down the address. I was afraid I might forget it. | I wrote down the address in case I forgot it. | Oldingi ehtiyot chorasi uchun in case + past ishlatiladi.
M “Use the spare key if you lose yours” ma’nosi: A) Hozirning o‘zida zaxira kalitni ishlating. B) Faqat kalitingizni yo‘qotsangiz, zaxirasini ishlating. | B | If chorani shart yuz bergandan keyinga bog‘laydi.
@25.15
G Ikkala variant: Both the museum ___ the gallery are free. | and | Both… and ikkisini ham qamrab oladi.
C Juft bog‘lovchi: You can either email us nor call the office. | You can either email us or call the office. | Either bilan or juftlashadi.
T Neither…nor bilan birlashtiring: The printer is not working. The scanner is not working. | Neither the printer nor the scanner is working. | Ikkala birlik ega bilan neither…nor + is ishlatiladi.
M “Either Tuesday or Thursday is fine” ma’nosi: A) Ikki kundan bittasi mos. B) Ikkala kun ham yaroqsiz. | A | Either…or muqobil tanlovni bildiradi.
@25.16
G Juft bog‘lovchi: The guide not only translated ___ also explained the customs. | but | Not only… but also juftligi kerak.
C Parallel fe’llar: She not only designs houses but also building furniture. | She not only designs houses but also builds furniture. | Designs va builds bir xil grammatik shaklda bo‘ladi.
T Not only…but also bilan birlashtiring: The flat is spacious. It is affordable. The flat is bilan boshlang. | The flat is not only spacious but also affordable. | Ikki sifat parallel ulanadi.
M Parallel tuzilma: A) He enjoys not only hiking but also to swim. B) He enjoys not only hiking but also swimming. | B | Hiking va swimming bir xil -ing shaklida keladi.
@25.17
G Misol: Many birds migrate. ___, swallows fly south in autumn. (For example / However) | For example | For example umumiy fikrga misol keltiradi.
C Qo‘shimcha dalil uchun however ni moreover ga almashtiring: The room is large. However, it has a balcony. | The room is large. Moreover, it has a balcony. | Moreover qo‘shimcha ijobiy dalilni ulaydi.
T Ikkinchi gap boshiga For instance qo‘shing: Some hobbies need little equipment. Walking is one example. Ikkala gapni yozing. | Some hobbies need little equipment. For instance, walking is one example. | For instance muayyan misolni tanishtiradi.
M Qaysi birikma qo‘shimcha fikr kiritadi? A) In addition. B) In contrast. | A | In addition qo‘shimcha, in contrast qarama-qarshi fikrdir.
@25.18
M Standart yozuv: A) The path was narrow, nevertheless, we continued. B) The path was narrow; nevertheless, we continued. | B | Mustaqil gaplar orasida nuqtali vergul kerak.
M To‘g‘ri yozuv: A) We had no map. Therefore, we asked for directions. B) We had no map therefore we, asked for directions. | A | Therefore yangi gap boshida vergul bilan ajratiladi.
T However bilan ikkita gap qiling: It was dark, but we found the cabin. | It was dark. However, we found the cabin. | Nuqta ikki mustaqil fikrni ajratadi.
M Qaysi variant oddiy comma splice xatosidan xoli? A) The shop was shut, we went home. B) The shop was shut, so we went home. | B | So bog‘lovchisi ikki gapni vergul orqali to‘g‘ri ulaydi.
""")

add(r"""
@22.1
G Say/tell, Past Simple: The receptionist ___ me that breakfast ended at nine. | told | Tell dan keyin kimga aytilgani to‘ldiruvchi bo‘lib keladi.
C Say qolipi: The guard said us that the gate was locked. Said ni saqlang. | The guard said to us that the gate was locked. | Say bilan shaxsdan oldin to kerak.
T Told o‘rniga said to ishlating: Nargiza told me that she was leaving. | Nargiza said to me that she was leaving. | Told me va said to me bir xabarni yetkazadi.
M To‘g‘ri gap: A) He said that he was ready. B) He told that he was ready. | A | Tell bu qolipda shaxs to‘ldiruvchisini talab qiladi.
@22.2
G Backshift: “I like this design,” she said. → She said that she ___ that design. | liked | Like o‘tgan xabarda liked ga o‘tadi.
C Backshift va egani moslang: Sam said, “I am confident.” → Sam said that he were confident. | Sam said that he was confident. | He bilan was ishlatiladi.
T Backshift qiling; The twins said that bilan boshlang: “We are hungry,” the twins said. | The twins said that they were hungry. | We → they, are → were.
M “Rano said that she needed help” gapida yordam kimga kerak? A) Rano bilan gaplashgan kishiga. B) Ranoning o‘ziga. | B | She xabar egasi Ranoga ishora qiladi.
@22.3
G Backshift: “I cannot find my glasses,” Dad said. → Dad said that he ___ find his glasses. | could not~couldn't | Cannot backshift bilan could not bo‘ladi.
C Backshift: “I don't own a car,” he said. → He said that he didn't owned a car. | He said that he didn't own a car.~He said that he did not own a car. | Didn’t dan keyin asosiy own shakli kerak.
T Backshift qiling; They said that bilan boshlang: “We are not waiting,” they said. | They said that they were not waiting.~They said that they weren't waiting. | Are not waiting → were not waiting.
M “She said she hadn't received the letter” ma’nosi: A) Xatni olmaganini aytdi. B) Xatni olganini aytdi. | A | Not inkor ma’nosini o‘zlashtirma gapda saqlaydi.
@22.4
G Present Continuous ni ortga suring: “I am feeding the birds,” she said. → She said that she ___ the birds. | was feeding | Am feeding → was feeding.
C Backshift talab qilinadi: “We live nearby,” they said. → They said that they live nearby. | They said that they lived nearby. | Present Simple backshift bilan Past Simple ga o‘tadi.
T Backshift qiling; He said that bilan boshlang: “I am learning Korean,” he said. | He said that he was learning Korean. | Hozirgi davomiy zamon o‘tgan davomiyga o‘tadi.
M “I work nights” gapining backshift shakli: A) She said she had worked nights. B) She said she worked nights. | B | Present Simple bir pog‘ona Past Simple ga o‘tadi.
@22.5
G Past Simple ni ortga suring: “I left the keys at home,” he said. → He said that he ___ the keys at home. | had left | Left → had left backshiftidir.
C Perfect backshift: “We have eaten,” they said. → They said that they had ate. | They said that they had eaten. | Had dan keyin V3 eaten kerak.
T Backshift qiling; Malika said that bilan boshlang: “I have lost my receipt,” Malika said. | Malika said that she had lost her receipt. | Have lost → had lost; my → her.
M “He said he had broken the cup” gapida qaysi ish oldin? A) Piyolani sindirish. B) Bu haqda aytish. | A | Past Perfect xabar berishdan oldingi ishni bildiradi.
@22.6
G Backshift: “We will wait outside,” they said. → They said that they ___ wait outside. | would | Will o‘tgan xabarda would bo‘ladi.
C Modal backshift: “I can juggle,” he said. → He said that he could juggled. | He said that he could juggle. | Can → could; keyingi fe’l asosiy shaklda qoladi.
T Backshift qiling; She said that bilan boshlang: “I will send the invoice,” she said. | She said that she would send the invoice. | Will → would o‘tmish nuqtasidan kelajakni bildiradi.
M “I can lift it” gapining modal backshifti: A) He said he must lift it. B) He said he could lift it. | B | Qobiliyat can dan could ga o‘tadi.
@22.7
G Hozirgi xabar, backshift yo‘q: Amir says, “I own two bikes.” → Amir says that he ___ two bikes. | owns | Says hozirgi zamonda; owns saqlanadi.
C Zamonni ortga surmang: “I am ready,” she says. → She says that she were ready. | She says that she is ready. | Hozirgi xabarda is ready keladi.
T Hali to‘g‘ri ilmiy faktni backshiftsiz yozing; The teacher said that bilan boshlang: “Ice floats on water.” | The teacher said that ice floats on water. | Hali dolzarb umumiy haqiqat Present Simple da qolishi mumkin.
M Hali ham to‘g‘ri ma’lumot haqida: A) Backshift qilmaslik mumkin. B) Har doim Past Perfect shart. | A | Dolzarblik saqlansa, zamonni saqlash mumkin.
@22.8
G Qizlar gapirdi: “Our bags are heavy,” the girls said. → The girls said that ___ bags were heavy. | their | Our xabar qiluvchilar nuqtasidan their ga o‘tadi.
C Erkakning o‘z telefoni: Jasur said, “My phone is broken.” → Jasur said that my phone was broken. | Jasur said that his phone was broken. | My Jasurning telefoni bo‘lgani uchun his bo‘ladi.
T Ali menga “I will help you,” dedi. Ali told me that bilan boshlang, backshift qiling. | Ali told me that he would help me. | I → he, you → me; olmoshlar ishtirokchilarga qarab o‘zgaradi.
M “We are ready,” the players said. O‘zlashtirma gapda we o‘rniga: A) I. B) They. | B | Players uchinchi shaxs ko‘plik bo‘lib they ga o‘tadi.
@22.9
G Bir hafta keyin yetkazyapsiz: “I saw her yesterday,” he said. → He said he had seen her ___. The bilan boshlang. | the day before~the previous day | Yesterday boshqa kun nuqtasidan the day before bo‘ladi.
C Boshqa haftada xabar bering: “I'll call next week,” she said. → She said she would call next week. Next week ni the bilan boshlanuvchi iboraga almashtiring. | She said she would call the following week.~She said she would call the next week. | Vaqt nuqtasi o‘zgargani uchun the following week kerak.
T Boshqa kun va joyda yetkazing: “I am here today,” he said. He said that bilan boshlang; here → there, today → that day. | He said that he was there that day. | Joy va vaqt so‘zlari yangi kontekstga moslashadi.
M Bir kunda shu joyning o‘zida xabar berilsa, today va here: A) Kontekstga mos bo‘lsa saqlanishi mumkin. B) Har doim almashtirilishi shart. | A | Vaqt va joy o‘zgarishi kontekstga bog‘liq.
@22.10
G Ha/yo‘q savolini yetkazing: “Are you alone?” → He asked me ___ I was alone. If/whether dan foydalaning. | if~whether | Yes/no o‘zlashtirma savol if yoki whether bilan ulanadi.
C So‘z tartibi: She asked whether could I hear her. | She asked whether I could hear her. | O‘zlashtirma savolda ega yordamchidan oldin keladi.
T If bilan yetkazing; The clerk asked me bilan boshlang, backshift qiling: “Do you need a receipt?” | The clerk asked me if I needed a receipt. | Do tushadi, need → needed; tartib oddiy gapniki.
M To‘g‘ri o‘zlashtirma savol: A) He asked that I was free. B) He asked if I was free. | B | Ha/yo‘q savoliga that emas, if/whether kerak.
@22.11
G Backshift: “Where do you keep the spare key?” → She asked where I ___ the spare key. | kept | Keep → kept; do tushadi.
C Tartibni tuzating, zamonni saqlang: He asked when would the train leave. | He asked when the train would leave. | Wh-so‘zdan keyin ega + fe’l tartibi ishlatiladi.
T Backshift qiling; She asked me bilan boshlang: “Why are you laughing?” | She asked me why I was laughing. | Why saqlanadi, are you → I was.
M “He asked who had called” gapida if kerakmi? A) Yo‘q, who saqlanadi. B) Ha, who o‘rniga if shart. | A | Wh-savol o‘z savol so‘zini saqlaydi.
@22.12
G Buyruq: “Check the lock,” she told me. → She told me ___ the lock. | to check | Told + shaxs + to-infinitive buyruqni yetkazadi.
C Buyruq qolipi: The coach told us stretch before running. | The coach told us to stretch before running. | Told us dan keyin to stretch kerak.
T Buyruqni yetkazing; The teacher told the class bilan boshlang: “Open your notebooks.” | The teacher told the class to open their notebooks. | Your → their, buyruq → to open.
M “He told me to wait by the gate” ma’nosi: A) U darvoza yonida kutayotganini aytdi. B) Menga darvoza yonida kutishni aytdi. | B | Object + to-infinitive boshqaga berilgan ko‘rsatmadir.
@22.13
G Inkor buyruq: “Don't lean out,” she told the child. → She told the child ___ out. | not to lean | Inkor buyruq not to + fe’l bilan beriladi.
C Inkor tartibi: The guide told us to not to cross the rope. | The guide told us not to cross the rope. | Standart qolip told us not to cross.
T Buyruqni yetkazing; The librarian told me bilan boshlang: “Don't write in the book.” | The librarian told me not to write in the book. | Don’t write → not to write.
M “She told him not to switch it off” ma’nosi: A) Uni o‘chirmaslikni aytdi. B) Uni yoqmaslikni aytdi. | A | Not switch off o‘chirishni inkor qiladi.
@22.14
G Iltimos: “Please send me the link,” Sara said to Ali. → Sara asked Ali ___ her the link. | to send | Asked + object + to-infinitive iltimosni yetkazadi.
C Iltimos qolipi: He asked me holding the door. | He asked me to hold the door. | Asked me dan keyin to hold kerak.
T Ask bilan yetkazing; She asked me bilan boshlang: “Please help my sister.” | She asked me to help her sister. | Please alohida takrorlanmaydi; my → her.
M “The neighbour asked us to turn the music down” ma’nosi: A) Musiqa haqida ma’lumot so‘radi. B) Ovozini pasaytirishni iltimos qildi. | B | Ask + shaxs + to-fe’l harakatni iltimos qiladi.
@22.15
G Reporting verb: She refused ___ the agreement. (sign) | to sign | Refuse dan keyin to-infinitive keladi.
C Offer qolipi: He offered carrying my suitcase. | He offered to carry my suitcase. | Offer + to-infinitive yordam taklifidir.
T Promise bilan yetkazing; He promised bilan boshlang: “I will repay the money.” | He promised to repay the money. | Promise to repay va’da berishni ifodalaydi.
M “She offered to drive us home” ma’nosi: A) Olib borishni taklif qildi. B) Olib borishdan bosh tortdi. | A | Offered taklif, refused esa bosh tortishdir.
@22.16
G Reporting verb: The boy denied ___ the window. (break) | breaking~having broken | Deny dan keyin -ing keladi; oldinlik having broken bilan ham beriladi.
C Suggest qolipi: She suggested to postpone the picnic. | She suggested postponing the picnic. | Suggest + -ing; suggest to do emas.
T Admit + -ing bilan yozing: “I copied the answer,” he said. He admitted bilan boshlang. | He admitted copying the answer.~He admitted having copied the answer. | Admit + -ing qilingan ishni tan olishdir.
M “He denied taking the money” ma’nosi: A) Pulni olganini tan oldi. B) Pulni olganini inkor qildi. | B | Denied inkor qilishni bildiradi.
@23.1
G Odamni aniqlang; who/which: The volunteer ___ teaches chess also runs the club. | who | Who odamni aniqlovchi nisbiy olmoshdir.
C Odamga who ishlating: The driver which helped us was very calm. | The driver who helped us was very calm. | Driver shaxs bo‘lgani uchun who mos.
T Who bilan birlashtiring; is my aunt bilan tugating: The woman is my aunt. She owns the bakery. | The woman who owns the bakery is my aunt. | Who owns the bakery qaysi ayol ekanini aniqlaydi.
M “The students who arrive early can choose their seats” kimlarga tegishli? A) Erta keladigan talabalarga. B) Barcha talabalarga, kelishidan qat’i nazar. | A | Defining relative guruhni chegaralaydi.
@23.2
G Buyumni aniqlang; which/that dan foydalaning: The lamp ___ stands by the sofa is solar-powered. | which~that | Buyum uchun defining relative da which yoki that ishlatiladi.
C Olmoshni tuzating, which ishlating: The software who controls the heating has failed. | The software which controls the heating has failed. | Software shaxs emas, shuning uchun which kerak.
T That bilan birlashtiring: The jacket is waterproof. I bought it yesterday. | The jacket that I bought yesterday is waterproof. | That I bought yesterday buyumni aniqlaydi; it tushadi.
M “The key that opens the cellar is rusty” gapida that nimaga ishora qiladi? A) Cellar ga. B) Key ga. | B | Nisbiy qism key otini aniqlaydi.
@23.3
G Egalik: The woman ___ bicycle was stolen called the police. | whose | Whose keyingi otning egasini bildiradi.
C Egalik olmoshi: The singer who's voice we heard is Uzbek. | The singer whose voice we heard is Uzbek. | Whose egalik; who’s esa who is yoki who has.
T Whose bilan birlashtiring: I met a boy. His father repairs clocks. | I met a boy whose father repairs clocks. | His father o‘rniga whose father keladi.
M “The tree whose branches broke is very old” gapida whose buyumga ishlatilishi mumkinmi? A) Ha. B) Yo‘q, faqat odamlarga. | A | Whose odamlar bilan birga buyumlarning egaligini ham ko‘rsatadi.
@23.4
G Joy ravishi, where/which: This is the warehouse ___ we store the spare parts. | where | Where joyda bajariladigan ishni bog‘laydi.
C Takroriy joy predlogini olib tashlang: This is the park where we play in. | This is the park where we play. | Where bu yerda in the park ma’nosini o‘z ichiga oladi.
T Where bilan birlashtiring; is tiny bilan tugating: The village is tiny. My grandparents live there. | The village where my grandparents live is tiny. | There o‘rnini where egallaydi.
M “the shop where I work” qaysi iboraga teng? A) the shop which I work B) the shop in which I work | B | Where bu yerda in which bilan teng.
@23.5
G Vaqt ravishi: I still remember the evening ___ the power failed. (when / where) | when | Evening vaqtni bildiradi; when mos.
C Vaqtga mos ravish: July was the month where we moved house. | July was the month when we moved house. | Month bilan vaqt ravishi when ishlatiladi.
T When bilan birlashtiring: I remember the morning. We found the lost puppy then. | I remember the morning when we found the lost puppy. | Then o‘rnini when egallaydi.
M “the year when I graduated” gapida when nimani bog‘laydi? A) Bitirgan vaqtni. B) Bitirgan joyni. | A | When vaqt nisbiy gapini kiritadi.
@23.6
G Tushirib bo‘lmaydigan ega olmoshi, who/which: The architect ___ designed this library won an award. | who | Who designed qismining egasi; uni tushirib bo‘lmaydi.
C Yetishmayotgan that ni qo‘shing: The bus stops outside our house is always crowded. | The bus that stops outside our house is always crowded. | That stops qismida that ega bo‘lib zarur.
T Takroriy he ni olib tashlang: The man who he delivers our bread is on holiday. | The man who delivers our bread is on holiday. | Who allaqachon ega, yana he kerak emas.
M Qaysi gapda which ni tushirib bo‘lmaydi? A) The camera which I use is old. B) The camera which fell is broken. | B | Which fell da which ega; I use da esa to‘ldiruvchi.
@23.7
G Nisbiy olmosh tushirilgan: The person ___ I hired starts tomorrow. (who / zero) Ikkalasi mumkin bo‘lsa both yozing. | both | Defining gapda to‘ldiruvchi who tushirilishi mumkin.
C Ortiqcha it ni olib tashlang: The song I heard it yesterday is beautiful. | The song I heard yesterday is beautiful. | Song nisbiy qismning to‘ldiruvchisi, it takrorlanmaydi.
T Faqat to‘ldiruvchi olmoshni olib tashlang: The hotel that you suggested has closed. | The hotel you suggested has closed. | You ega bo‘lgani uchun object that tushiriladi.
M “The doctor I saw was helpful” gapida tushirilgan olmoshning vazifasi: A) To‘ldiruvchi. B) Ega. | A | I ega, doctor esa saw fe’lining to‘ldiruvchisidir.
@23.8
G Qo‘shimcha ma’lumot: My laptop, ___ is six years old, still works. (which / that) | which | Non-defining gapda buyum uchun which ishlatiladi.
C That o‘rniga odamga mos olmosh: Mr Lee, that lives upstairs, is a pilot. | Mr Lee, who lives upstairs, is a pilot. | Vergulli qo‘shimcha ma’lumotda who kerak.
T Which bilan qo‘shing; is electric bilan tugating, nisbiy qismni vergullar bilan ajrating: Our car is electric. It was made in Korea. | Our car, which was made in Korea, is electric. | Qo‘shimcha ma’lumot which bilan va ikki vergul orasida keladi.
M Non-defining gapda which ni tushirish mumkinmi? A) Ha, har doim. B) Yo‘q. | B | Qo‘shimcha nisbiy gapning olmoshi saqlanadi.
@23.9
G Qo‘shimcha egalik: Mr Karimov, ___ son won a scholarship, is delighted. | whose | Whose qo‘shimcha qismda ham egalikni bildiradi.
C Joy ravishi: Samarkand, which my cousin lives, attracts many visitors. Where ishlating. | Samarkand, where my cousin lives, attracts many visitors. | Where my cousin lives joydagi holatni bildiradi.
T Whose bilan qo‘shing; is a designer bilan tugating, vergullar qo‘ying: Amina is a designer. Her brother is a chef. | Amina, whose brother is a chef, is a designer. | Her brother → whose brother qo‘shimcha ma’lumotga aylanadi.
M “Oxford, where I studied, is busy in summer” gapida where qismi: A) Qo‘shimcha ma’lumot. B) Qaysi Oxford ekanini zarur ajratish. | A | Vergullar qo‘shimcha ma’lumotni bildiradi.
@23.10
M Faqat ko‘k nishonli ishchilar kirishi mumkin. A) Workers who have blue badges may enter. B) Workers, who have blue badges, may enter. | A | Vergulsiz nisbiy qism kerakli guruhni ajratadi.
M “My sons, who live abroad, visit each summer” nimani anglatadi? A) Faqat ayrim o‘g‘illarim chet elda. B) Gapdagi barcha o‘g‘illarim chet elda. | B | Vergulli qism tilga olingan barcha o‘g‘illarga qo‘shimcha ma’lumot beradi.
T Qo‘shimcha ma’lumotni alohida gap qiling: My sister, who studies medicine, is twenty. Avval yoshini, keyin She bilan o‘qishini ayting. | My sister is twenty. She studies medicine. | Qo‘shimcha nisbiy qismni ajratsak, asosiy ma’no saqlanadi.
M Standart yozuvda qo‘shimcha qismni to‘g‘ri ajrating: A) Our coach, who is very patient, helped us. B) Our coach, who is very patient helped us. | A | Gap o‘rtasidagi qo‘shimcha qism ikki tomondan ajratiladi.
@23.11
G Rasmiy nisbiy gap: The organisation for ___ she works is expanding. | which | Predlogdan keyin buyum/tashkilot uchun which keladi.
C Predlogdan keyingi olmosh: The researcher to that I wrote replied. | The researcher to whom I wrote replied. | Odamga oid predlogdan keyin whom ishlatiladi.
T Rasmiy to whom qolipiga o‘tkazing: The woman I spoke to was the director. | The woman to whom I spoke was the director. | Predlogni boshga ko‘chirganda whom saqlanadi.
M Qaysi shakl odatiy suhbat uslubida? A) the colleague with whom I travelled B) the colleague I travelled with | B | Suhbatda predlog ko‘pincha nisbiy qism oxirida qoladi.
@23.12
G Butun fikrga ishora: Nobody objected, ___ surprised the chairperson. | which | Which oldingi butun voqeaga ishora qiladi.
C Butun gapga ishora: She remembered my birthday, what was thoughtful. | She remembered my birthday, which was thoughtful. | Oldingi fikrga which ishlatiladi, what emas.
T Which bilan birlashtiring: He paid for everyone's lunch. This was generous. | He paid for everyone's lunch, which was generous. | Which uning hamma uchun to‘laganiga ishora qiladi.
M “The lift broke down, which delayed us” gapida which nimaga ishora qiladi? A) Liftning buzilganiga. B) Faqat liftning rangiga. | A | Which oldingi butun holatni bog‘laydi.
@23.13
G Qisqa faol aniqlovchi: Anyone ___ (wish) to join should email us. | wishing | Faol aniqlovchida -ing ishlatiladi.
C Qisqartirilgan faol qism: The girl stand by the window is my cousin. | The girl standing by the window is my cousin. | Girl bajaruvchi; standing bilan aniqlanadi.
T Who are ni tushiring: The people who are queuing outside need tickets. | The people queuing outside need tickets. | Who are queuing → queuing.
M “The train approaching platform two” ma’nosi: A) Ikkinchi yo‘lakka yaqinlashayotgan poyezd. B) Ikkinchi yo‘lakda ta’mirlangan poyezd. | A | Approaching faol jarayonni bildiradi.
@23.14
G Qisqa passiv aniqlovchi: The goods ___ (damage) in transit will be replaced. | damaged | Goods ish ta’sirida; V3 damaged ishlatiladi.
C Qisqa passiv: The messages sending yesterday were confidential. V3 ishlating. | The messages sent yesterday were confidential. | Xabarlar yuborilgan; sent passiv ma’no beradi.
T That was ni tushiring: The bridge that was built in 1880 is still in use. | The bridge built in 1880 is still in use. | That was built → built qisqa passivdir.
M “The forms signed by the manager” ma’nosi: A) Menejerga imzo qo‘ygan blankalar. B) Menejer imzolagan blankalar. | B | Signed V3 blankalarga bajarilgan ishni bildiradi.
""")

add(r"""
@20.1
G “The sculptures were carved by local artists.” Grammatik ega: ___ (the sculptures / local artists). | the sculptures | Passiv gapning egasi ish ta’siridagi buyumdir.
M Qaysi gap passiv? A) A nurse examined the patient. B) The patient was examined by a nurse. | B | Was examined ishning egaga bajarilganini bildiradi.
T Passivga aylantiring, bajaruvchini by bilan saqlang: A technician repaired the scanner. | The scanner was repaired by a technician. | Scanner yangi ega, technician esa by orqali bajaruvchi bo‘ladi.
M “The parcel was damaged during transport” gapida bajaruvchi aytilganmi? A) Yo‘q. B) Ha, transport haydovchisi aniq aytilgan. | A | Passivda bajaruvchi noma’lum bo‘lishi mumkin.
@20.2
G Present Simple Passive: Rice ___ (serve) with every main course here. | is served | Rice sanalmaydigan ot; is + V3 kerak.
C Passiv yordamchisi: The uniforms is checked every Monday. | The uniforms are checked every Monday. | Ko‘plik uniforms bilan are keladi.
T Passivga aylantiring; they ni tushiring: They collect the rubbish twice a week. | The rubbish is collected twice a week. | Odatiy jarayon is collected bilan ifodalanadi.
M “These toys are made locally” nimani bildiradi? A) Hozir ayni paytdagi bir jarayon. B) Odatdagi ishlab chiqarish joyi. | B | Present Simple Passive odatiy holatni bildiradi.
@20.3
G Present Simple Passive inkori: Cash ___ (not accept) at this kiosk. | is not accepted~isn't accepted | Cash bilan is not + V3 ishlatiladi.
C Passiv inkori: These towels don't washed daily. | These towels are not washed daily.~These towels aren't washed daily. | Passiv inkorida do emas, be yordamchisi kerak.
T Inkor qiling: The office doors are locked at noon. | The office doors are not locked at noon.~The office doors aren't locked at noon. | Are dan keyin not qo‘yiladi.
M “Fresh fruit isn't sold here” ma’nosi: A) Bu yerda yangi meva sotilmaydi. B) Meva o‘zini sota olmaydi. | A | Is not sold odatiy passiv inkordir.
@20.4
G Present Simple Passive savoli: How often ___ these filters replaced? | are | Ko‘plik filters bilan are savol boshqaruvchisidir.
C Passiv savol: Does this juice made from fresh oranges? | Is this juice made from fresh oranges? | Is + ega + V3 passiv savolni hosil qiladi.
T Where bilan joyni so‘rang: These carpets are woven in Khiva. | Where are these carpets woven? | Where + are + ega + woven kerak.
M Jarayon haqidagi to‘g‘ri savol: A) Is the water tested regularly? B) Is tested the water regularly? | A | Passiv savolda ega be va V3 orasida keladi.
@20.5
G Past Simple Passive: The medals ___ (award) last night. | were awarded | Ko‘plik ega va o‘tgan vaqt uchun were + V3.
C V3 shakli: The vase was break during the move. | The vase was broken during the move. | Break fe’lining V3 shakli broken.
T Passivga aylantiring; someone ni tushiring: Someone stole my suitcase yesterday. | My suitcase was stolen yesterday. | O‘tgan passivda was stolen ishlatiladi.
M “The tunnel was completed in 2018” nimani bildiradi? A) Tunnel hali qurilyapti. B) Qurilish o‘tmishda yakunlangan. | B | Was completed yakunlangan o‘tgan ishdir.
@20.6
G Past Simple Passive inkori: The damaged goods ___ (not return) last week. | were not returned~weren't returned | Ko‘plik ega bilan were not + V3 kerak.
C Passiv inkori: The application didn't approved yesterday. | The application was not approved yesterday.~The application wasn't approved yesterday. | O‘tgan passiv inkori wasn’t approved bo‘ladi.
T Inkor qiling: The statue was moved in June. | The statue was not moved in June.~The statue wasn't moved in June. | Was dan keyin not qo‘yiladi.
M “The guests weren't informed about the change” ma’nosi: A) Mehmonlarga xabar berilmagan. B) Mehmonlar boshqalarga xabar bergan. | A | Mehmonlar ishning ta’siridagi ega bo‘lib turibdi.
@20.7
G Past Simple Passive savoli: When ___ the missing child found? | was | Birlik ega bilan was + ega + V3 keladi.
C O‘tgan passiv savol: Were the invitations send on time? | Were the invitations sent on time? | Send fe’lining V3 shakli sent.
T Ha/yo‘q savoliga aylantiring: The paintings were insured before the exhibition. | Were the paintings insured before the exhibition? | Were savolda egadan oldinga chiqadi.
M To‘g‘ri o‘tgan passiv savol: A) Did the windows cleaned yesterday? B) Were the windows cleaned yesterday? | B | Past Passive savolida were ishlatiladi.
@20.8
G Present Continuous Passive: A new platform ___ (build) at the station now. | is being built | Ayni jarayondagi passiv: is being + V3.
C Davomiy passiv: The chairs are being paint right now. | The chairs are being painted right now. | Being dan keyin V3 painted kerak.
T Passivga aylantiring; they ni tushiring: They are widening the pavement. | The pavement is being widened. | Hozir bajarilayotgan ish is being widened bilan beriladi.
M “The bridge is being strengthened” ma’nosi: A) Mustahkamlash hozir davom etmoqda. B) Mustahkamlash doim yakshanba bo‘ladi. | A | Be + being + V3 ayni jarayonni bildiradi.
@20.9
G Hozirgi davomiy passiv inkori: The damaged pipes ___ (not replace) today. | are not being replaced~aren't being replaced | Ko‘plikda are not being + V3 kerak.
C Davomiy passiv inkori: The lift isn't repaired right now. Being qo‘shing. | The lift isn't being repaired right now.~The lift is not being repaired right now. | Being ayni paytdagi ta’mirlash jarayonini bildiradi.
T Inkor qiling: The documents are being scanned now. | The documents are not being scanned now.~The documents aren't being scanned now. | Not are dan keyin, being dan oldin turadi.
M “The pool isn't being cleaned at the moment” ma’nosi: A) Hovuz hech qachon tozalanmaydi. B) Hozir tozalash jarayoni ketmayapti. | B | At the moment hozirgi vaqt bilan chegaralaydi.
@20.10
G Davomiy passiv savol: Is the floor ___ (polish) at the moment? | being polished | Is + ega + being + V3 savol qolipidir.
C Savol tartibi: Are being the bags searched now? | Are the bags being searched now? | Are dan keyin ega kelishi kerak.
T Why bilan sababni so‘rang: The traffic is being diverted because of a parade. | Why is the traffic being diverted? | Why + is + ega + being + V3.
M Qaysi savol ayni jarayon haqida? A) Is your passport being checked? B) Is your passport checked on every trip? | A | Being checked ayni bajarilayotgan tekshiruvdir.
@20.11
G Present Perfect Passive: The meeting ___ (postpone). Check the new date. | has been postponed | Hozirgi natija has been + V3 bilan beriladi.
C Perfect Passive: The missing documents have found. Been qo‘shing. | The missing documents have been found. | Passivda have been + V3 kerak.
T Passivga aylantiring; someone ni tushiring: Someone has updated the software. | The software has been updated. | Software bilan has been updated keladi.
M “All the places have been filled” ma’nosi: A) Joylar hozirgina to‘ldirilyapti, hali bo‘sh. B) Joylar band qilingan, bo‘sh joy qolmagan. | B | Present Perfect Passive tugallangan ishning natijasini bildiradi.
@20.12
G Present Perfect Passive inkori: The decision ___ (not make) yet. | has not been made~hasn't been made | Birlik decision bilan has not been + V3.
C Perfect Passive inkori: The rooms haven't been clean yet. | The rooms haven't been cleaned yet.~The rooms have not been cleaned yet. | Been dan keyin cleaned V3 shakli kerak.
T Inkor qiling va yet ni oxirga qo‘ying: The contract has been signed. | The contract has not been signed yet.~The contract hasn't been signed yet. | Yet bilan hali bajarilmagan ish ifodalanadi.
M “The winners haven't been contacted” ma’nosi: A) G‘oliblar bilan hali bog‘lanilmagan. B) G‘oliblar hech kimga murojaat qilmaydi. | A | Ega ish ta’sirini oladi; gap passivdir.
@20.13
G Present Perfect Passive savoli: ___ the password been changed? | Has | Birlik password bilan has savol boshida keladi.
C Savol tartibi: Have been the packages delivered? | Have the packages been delivered? | Have + ega + been + V3 kerak.
T Ha/yo‘q savoliga aylantiring: The injured player has been examined. | Has the injured player been examined? | Has egadan oldinga o‘tadi.
M Tugallangan passiv natijani so‘rang: A) Has the permit been issued? B) Has the permit issued? | A | Passive Perfect savolida been zarur.
@21.1
G Future Passive: The finalists ___ (invite) next week. Will ishlating. | will be invited | Kelajak passivi will be + V3.
C Kelajak passivi: The prize will given at noon. | The prize will be given at noon. | Will va given orasida be kerak.
T Passivga aylantiring; they ni tushiring: They will record the lecture. | The lecture will be recorded. | Lecture ish ta’siridagi ega bo‘ladi.
M “The names will be displayed tomorrow” ma’nosi: A) Ismlar kelajakda ko‘rsatiladi. B) Ismlar hozir ko‘rinib turibdi. | A | Will be displayed kelajakdagi passiv ishdir.
@21.2
G Future Passive inkori: The delivery fee ___ (not refund). Will ishlating. | will not be refunded~won't be refunded | Will not be + V3 salbiy kelajak passivi.
C V3 shakli: These flowers won't be sell tomorrow. | These flowers won't be sold tomorrow.~These flowers will not be sold tomorrow. | Sell fe’lining V3 shakli sold.
T Inkor qiling: The data will be deleted after a week. | The data will not be deleted after a week.~The data won't be deleted after a week. | Not will dan keyin qo‘yiladi.
M “The road won't be reopened tonight” ma’nosi: A) Yo‘l kechasi yopilgan edi. B) Yo‘l bugun kechasi qayta ochilmaydi. | B | Won’t be reopened kelajak inkorini bildiradi.
@21.3
G Future Passive savoli: When will the new timetable ___ (release)? | be released | Will dan keyingi passiv qism be + V3.
C Savol tartibi: Will be the fence repaired next week? | Will the fence be repaired next week? | Will + ega + be + V3 kerak.
T How bilan usulni so‘rang: The results will be sent by email. | How will the results be sent? | How yetkazish usulini so‘raydi.
M To‘g‘ri kelajak passiv savoli: A) Will your expenses be covered? B) Will your expenses covered? | A | Be kelajak passivining zarur qismidir.
@21.4
G Modal Passive: The form must ___ (complete) in black ink. | be completed | Modal + be + V3 passivni hosil qiladi.
C Modal passiv: This stain can removed with soap. | This stain can be removed with soap. | Can dan keyin be removed kerak.
T Passivga aylantiring; you ni tushiring: You should keep the receipt. | The receipt should be kept. | Keep fe’lining V3 shakli kept.
M “The sample must be stored in a fridge” ma’nosi: A) Namuna o‘zi sovutkich saqlaydi. B) Namunani sovutkichda saqlash shart. | B | Must be stored passiv majburiyatdir.
@21.5
G Modal passiv inkori: The seal must not ___ (break). | be broken | Must not be + V3 taqiqni bildiradi.
C Inkor passiv: This password shouldn't be share. | This password shouldn't be shared.~This password should not be shared. | Share o‘rniga V3 shared kerak.
T Passivga aylantiring; you ni tushiring: You cannot export these files. | These files cannot be exported.~These files can't be exported. | Cannot be exported imkon yoki ruxsat yo‘qligini beradi.
M “The safety cover mustn't be removed” ma’nosi: A) Qopqoqni yechish taqiqlangan. B) Qopqoqni yechish ixtiyoriy. | A | Mustn’t be removed passiv taqiqdir.
@21.6
G Modal passiv savol: Could the appointment ___ (move) to Friday? | be moved | Could + ega + be + V3 kerak.
C Savol tartibi: Must be all the fields completed? | Must all the fields be completed? | Modal va be orasida ega turadi.
T Where bilan joyni so‘rang: This voucher can be used at the station. | Where can this voucher be used? | Where + can + ega + be + V3.
M To‘g‘ri passiv savol: A) Can this metal recycle? B) Can this metal be recycled? | B | Metal ishni bajarmaydi, qayta ishlanadi.
@21.7
G Past Continuous Passive: The patients ___ (examine) when the fire alarm rang. | were being examined | Ko‘plik ega bilan were being + V3 kerak.
C O‘tgan davomiy passiv: The fence was being mend at nine. | The fence was being mended at nine. | Being dan keyin mended keladi.
T Passivga aylantiring; they ni tushiring: They were unloading the lorry when I arrived. | The lorry was being unloaded when I arrived. | O‘tmishdagi jarayon was being unloaded bilan beriladi.
M “The stage was being assembled at six” ma’nosi: A) O‘sha vaqtda yig‘ish jarayoni ketayotgan edi. B) Sahna har kuni soat oltida yig‘iladi. | A | Was being + V3 o‘tmishdagi davomiy passivdir.
@21.8
G Past Continuous Passive inkori: The soup ___ (not serve) when we arrived. | was not being served~wasn't being served | O‘sha paytda jarayon bo‘lmaganini bildiradi.
C Inkor passiv shakli: The machines weren't being test at midnight. | The machines weren't being tested at midnight.~The machines were not being tested at midnight. | Being dan keyin V3 tested kerak.
T Inkor qiling: The guests were being photographed at that moment. | The guests were not being photographed at that moment.~The guests weren't being photographed at that moment. | Were dan keyin not qo‘yiladi.
M “The road wasn't being resurfaced when I passed” ma’nosi: A) Yo‘l hech qachon ta’mirlanmagan. B) Men o‘tgan paytda asfalt yotqizilmayotgan edi. | B | Davomiy shakl faqat o‘sha jarayon vaqtini bildiradi.
@21.9
G O‘tgan davomiy passiv savol: ___ the piano being tuned when you called? | Was | Birlik piano bilan was kerak.
C Savol tartibi: Were being the suitcases weighed when you arrived? | Were the suitcases being weighed when you arrived? | Were + ega + being + V3.
T Why bilan sababni so‘rang: The match was being filmed for a documentary. | Why was the match being filmed? | Why ishning sabab yoki maqsadini so‘raydi.
M To‘g‘ri savol: A) Was the engine being tested at noon? B) Was the engine been tested at noon? | A | Davomiy passivda being, perfectda been ishlatiladi.
@21.10
G Past Perfect Passive: The hall ___ (decorate) before the guests arrived. | had been decorated | Oldingi yakunlangan passiv ish had been + V3.
C Perfect Passive: The equipment had checked before departure. | The equipment had been checked before departure. | Had been checked passivni ifodalaydi.
T Passivga aylantiring; someone ni tushiring: Someone had emptied the bins before we arrived. | The bins had been emptied before we arrived. | Tozalash kelishdan oldin tugagan.
M “The parcel had been collected before I called” gapida qaysi ish oldin? A) Qo‘ng‘iroq. B) Posilkani olish. | B | Had been collected avvalgi ishni ko‘rsatadi.
@21.11
G Past Perfect Passive inkori: The route ___ (not plan) before they set off. | had not been planned~hadn't been planned | Had not been + V3 oldingi bajarilmagan ishdir.
C V3: The invoice hadn't been pay when I checked. | The invoice hadn't been paid when I checked.~The invoice had not been paid when I checked. | Pay fe’lining V3 shakli paid.
T Inkor qiling: The warning had been issued before the storm. | The warning had not been issued before the storm.~The warning hadn't been issued before the storm. | Not had dan keyin qo‘yiladi.
M “The room hadn't been aired when we entered” ma’nosi: A) Kirishimizgacha xona shamollatilmagan edi. B) Xona hozir shamollatilyapti. | A | Past Perfect kirishdan oldingi holatni bildiradi.
@21.12
G Past Perfect Passive savoli: Had the seats ___ (allocate) before boarding began? | been allocated | Had + ega + been + V3.
C Savol tartibi: Had been the money transferred before noon? | Had the money been transferred before noon? | Had dan keyin ega keladi.
T Ha/yo‘q savoliga aylantiring: The witness had been interviewed before the trial. | Had the witness been interviewed before the trial? | Had savolda egadan oldinga o‘tadi.
M Avval bajarilgan passiv ishni so‘rang: A) Had the door been locked before you left? B) Had the door locking before you left? | A | Been locked Past Perfect Passive shaklidir.
@21.13
G Bajaruvchi predlogi: The music was composed ___ a former student. | by | By passivdagi bajaruvchini kiritadi.
C Bajaruvchi uchun predlog: The portrait was painted with my aunt. By ishlating. | The portrait was painted by my aunt. | Shaxs bajaruvchi bo‘lsa by ishlatiladi.
T Passivga aylantiring; bajaruvchini saqlang: A local engineer designed the fountain. | The fountain was designed by a local engineer. | Bajaruvchi by a local engineer bilan saqlanadi.
M “The lock was opened by a locksmith with a special tool.” Bajaruvchi kim? A) A special tool. B) A locksmith. | B | By bajaruvchini, with esa asbobni bildiradi.
""")

add(r"""
@15.1
G My grandfather can ___ maps without glasses. (read) | read | Can dan keyin fe’lning asosiy shakli keladi.
C Can dan keyingi fe’l: The baby can claps her hands. | The baby can clap her hands. | Qobiliyatda can + clap; -s qo‘shilmaydi.
T Can bilan qayta yozing: Our neighbour is able to fix radios. | Our neighbour can fix radios. | Hozirgi qobiliyat can bilan ifodalanadi.
M “Lola can solve this puzzle” nimani bildiradi? A) Lola buni yecha oladi. B) Lola buni yechishi shart. | A | Can qobiliyatni bildiradi, majburiyatni emas.
@15.2
G Can ning inkori: I ___ reach the top shelf; it is too high. | cannot~can't | Yetolmaslik cannot yoki can’t bilan ifodalanadi.
C Qobiliyat inkori: The injured bird doesn't can fly. | The injured bird cannot fly.~The injured bird can't fly. | Can bilan do yordamchisi ishlatilmaydi.
T Can bilan inkor gap qiling: My uncle is unable to hear this sound. | My uncle cannot hear this sound.~My uncle can't hear this sound. | Unable to o‘rnida cannot + hear keladi.
M “I can't distinguish these colours” ma’nosi: A) Ranglarni ajratish taqiqlangan. B) Ranglarni farqlay olmayman. | B | Bu kontekstda can’t qobiliyat yo‘qligini bildiradi.
@15.3
G Savolning birinchi so‘zi: ___ your cousin play the violin? (can bilan) | Can | Can savolda egadan oldin keladi.
C Can savolining tartibi: Can solve you this equation? | Can you solve this equation? | Tartib: can + ega + asosiy fe’l.
T Ha/yo‘q savoliga aylantiring: The robot can climb stairs. | Can the robot climb stairs? | Can egadan oldinga o‘tadi.
M Qobiliyatni so‘rang: A) Can your dog catch a ball? B) Does your dog can catch a ball? | A | Can savolida does kerak emas.
@15.4
G Savol so‘zidan keyingi modal: Which instruments ___ you play? (can) | can | Wh-so‘zdan keyin can, keyin ega keladi.
C So‘z tartibi: Where you can recharge this battery? | Where can you recharge this battery? | Where + can + you + recharge tartibi kerak.
T How far bilan masofani so‘rang: She can run ten kilometres. | How far can she run? | How far masofani so‘raydi.
M “Who can repair the clock?” nimani so‘raydi? A) Kim soatni tuzata olishini. B) Kimni tuzatish kerakligini. | A | Who bu yerda ega; ortiqcha ega qo‘shilmaydi.
@15.5
G “Can the twins skate?” — “Yes, they ___.” | can | Qisqa javobda can takrorlanadi.
C Qisqa javob yordamchisi: “Can Aziza draw?” — “Yes, she does.” Faqat javobni tuzating. | Yes, she can. | Can savoliga can bilan javob beriladi.
T “Can your brother dive?” savoliga he bilan qisqa inkor javob yozing. | No, he cannot.~No, he can't. | Inkor qisqa javob: No + ega + can’t.
M “Can you two lift it?” — Ikkalangiz nomidan ijobiy javob: A) Yes, we can. B) Yes, I do. | A | Ikki kishi nomidan we olmoshi kerak.
@15.6
G Oldingi umumiy qobiliyat: At twelve, my mother ___ type very quickly. (can / could) | could | O‘tmishdagi umumiy qobiliyat could bilan beriladi.
C Could dan keyingi fe’l: At school, I could ran faster than anyone. | At school, I could run faster than anyone. | Could dan keyin run keladi, ran emas.
T Could bilan qayta yozing: When we were young, we were able to walk for hours. | When we were young, we could walk for hours. | Takroriy o‘tmish qobiliyati uchun could mos.
M “At four, Aziz could count to a hundred” ma’nosi: A) Hozir sanashi shart. B) To‘rt yoshida sanay olgan. | B | Could oldingi qobiliyatni bildiradi.
@15.7
G Could inkori: As a child, I ___ pronounce this word. | could not~couldn't | Could not o‘tmishdagi qila olmaslikni bildiradi.
C Inkor modal: We didn't could see the mountain through the fog. | We could not see the mountain through the fog.~We couldn't see the mountain through the fog. | Could inkoriga did qo‘shilmaydi.
T Could bilan inkor qiling: At five, she was unable to write her name. | At five, she could not write her name.~At five, she couldn't write her name. | Unable to ning bu o‘tmish shakli couldn’t ga mos.
M “He couldn't speak after the operation” nimani bildiradi? A) Gapira olmagan. B) Gapirishni istamagan. | A | Couldn’t imkon yoki qobiliyat yo‘qligini bildiradi.
@15.8
G O‘tmish qobiliyati savoli: ___ your grandmother drive at twenty? (can / could) | Could | Could + ega + fe’l o‘tmish qobiliyatini so‘raydi.
C Savoldagi fe’l: Could they understood the instructions? | Could they understand the instructions? | Could dan keyin understand asosiy shakli kerak.
T Ha/yo‘q savoliga aylantiring: You could hear the waterfall from the camp. | Could you hear the waterfall from the camp? | Could egadan oldinga o‘tadi.
M Oldingi qobiliyatni so‘rovchi gap: A) Did she could dance at six? B) Could she dance at six? | B | Modal savolida did ishlatilmaydi.
@15.9
G Be able to, Past Simple: After treatment, he ___ walk again. | was able to | He bilan o‘tgan zamonda was able to keladi.
C Ikki modalni tuzating: You will can access the files tomorrow. Will va be able to ishlating. | You will be able to access the files tomorrow. | Will dan keyin can emas, be able to kerak.
T Be able to bilan yozing: I hope I can attend the workshop. I hope to bilan boshlang. | I hope to be able to attend the workshop. | Infinitivda to be able to ishlatiladi.
M “She has been able to eat since Monday” ma’nosi: A) Dushanbadan beri ovqatlana olyapti. B) Faqat kelasi dushanba ovqatlanadi. | A | Has been able to o‘tmishdan hozirgacha imkonni bildiradi.
@15.10
G Bir martalik muvaffaqiyat: Despite the strong current, the swimmer ___ reach the bank. (managed to / could) | managed to | Managed to qiyinchilikdan keyingi aniq muvaffaqiyatni bildiradi.
C Manage qolipi: We managed unlock the safe at last. | We managed to unlock the safe at last. | Manage dan keyin to-infinitive kerak.
T Managed to o‘rniga was able to ishlating: The pilot managed to land safely. | The pilot was able to land safely. | Aniq muvaffaqiyat was able to bilan ham ifodalanadi.
M “After an hour, they managed to restart the engine” ma’nosi: A) Faqat rejalashtirishdi. B) Motorni ishga tushirishga erishishdi. | B | Managed to ish amalga oshganini bildiradi.
@15.11
G Rasmiy ruxsat: ___ I leave my suitcase here? (May / Must) | May | May I ruxsat so‘rashning rasmiy shakli.
C Ruxsat savoli: May I to sit beside you? | May I sit beside you? | May dan keyin to ishlatilmaydi.
T Can I borrow your umbrella? savolini Could I bilan muloyimroq qiling. | Could I borrow your umbrella? | Could I ruxsatni muloyim so‘raydi.
M “Could I open the window?” nimani anglatadi? A) Derazani ochishga ruxsat so‘rayapman. B) O‘tmishdagi qobiliyatimni aytyapman. | A | Could I bu vaziyatda ruxsat so‘rovidir.
@15.12
G Muloyim iltimos: ___ you hold the ladder, please? (Could / Must) | Could | Could you suhbatdoshdan yordam so‘raydi.
C Would dan keyingi fe’l: Would you to pass me the salt? | Would you pass me the salt? | Would you + asosiy fe’l muloyim iltimosdir.
T Buyruqni Would you bilan iltimosga aylantiring, please oxirida: Close the curtains. | Would you close the curtains, please? | Would you buyruqni muloyim iltimosga aylantiradi.
M “Could you spell your surname?” ma’nosi: A) Familiyangizni unutdingizmi? B) Familiyangizni harflab aytib berasizmi? | B | Could you bu yerda iltimos bildiradi.
@15.13
G Ruxsat, Present Simple: A visitor ___ take one leaflet. (be allowed to) | is allowed to | Birlik ega bilan is allowed to keladi.
C Ruxsat qolipi: Students are allowed use calculators. | Students are allowed to use calculators. | Allowed dan keyin to-infinitive kerak.
T Will bilan kelajakka o‘tkazing: We are allowed to enter the archive. Tomorrow ni oxiriga qo‘ying. | We will be allowed to enter the archive tomorrow.~We'll be allowed to enter the archive tomorrow. | Kelajak ruxsati will be allowed to bilan beriladi.
M “We weren't allowed to film inside” ma’nosi: A) Ichkarida tasvirga olishga ruxsat yo‘q edi. B) Kameramiz ishlamas edi. | A | Be allowed to qobiliyat emas, ruxsatga taalluqli.
@15.14
G Would like qolipi: I would like ___ the menu. (see) | to see | Would like dan keyin to-infinitive keladi.
C Taklifdagi fe’l: Would you like trying some soup? | Would you like to try some soup? | Taklifda would like to try ishlatiladi.
T I want a quieter room. gapini would like bilan muloyimroq yozing. | I would like a quieter room.~I'd like a quieter room. | Would like istakni muloyim ifodalaydi.
M “Would you like a lift?” ma’nosi: A) Odatda liftlarni yoqtirasizmi? B) Sizni mashinada olib boraymi? | B | Would you like a lift olib borishni taklif qiladi.
@16.1
G Must bilan: All applicants ___ attach a photograph. | must | Must kuchli talabni bildiradi.
C Majburiyat qolipi: You must to lock the medicine cupboard. | You must lock the medicine cupboard. | Must + asosiy fe’l; to kerak emas.
T Must bilan qayta yozing: It is essential that we protect these records. We bilan boshlang. | We must protect these records. | Must zarur majburiyatni ifodalaydi.
M “Staff must wash their hands” ma’nosi: A) Xodimlar qo‘lini yuvishi shart. B) Yuvish ixtiyoriy. | A | Must bajarilishi shart bo‘lgan talabdir.
@16.2
G Must inkori bilan taqiq: You ___ copy another candidate's answers. | must not~mustn't | Mustn’t taqiqni bildiradi.
C Taqiqdagi fe’l: Visitors mustn't feeds the animals. | Visitors mustn't feed the animals.~Visitors must not feed the animals. | Mustn’t dan keyin feed keladi.
T Must not bilan yozing: Taking photographs in this gallery is forbidden. You bilan boshlang. | You must not take photographs in this gallery.~You mustn't take photographs in this gallery. | Forbidden mazmuni must not bilan beriladi.
M “You mustn't lean on the railing” ma’nosi: A) Suyanish shart emas. B) Suyanish mumkin emas. | B | Mustn’t ruxsat yo‘qligini bildiradi.
@16.3
G Must savoli: ___ every visitor sign this register? | Must | Must savolda egadan oldin keladi.
C Savol tartibi: Must wear we uniforms on Friday? | Must we wear uniforms on Friday? | Must + we + wear tartibi kerak.
T Ha/yo‘q savoliga aylantiring: I must attend the safety briefing. | Must I attend the safety briefing? | Majburiyatni so‘rash uchun must oldinga o‘tadi.
M Majburiyatni so‘rang: A) Must I return both keys? B) Do I must return both keys? | A | Must savoliga do qo‘shilmaydi.
@16.4
G Have to, Present Simple: My daughter ___ wear glasses for reading. | has to | He/she/it bilan has to ishlatiladi.
C Ega bilan moslang: The cleaners has to arrive before seven. | The cleaners have to arrive before seven. | Ko‘plik ega bilan have to kerak.
T Have to bilan yozing: It is necessary for us to change trains. We bilan boshlang. | We have to change trains. | Tashqi zarurat have to bilan ifodalanadi.
M “The nurse has to work tonight” ma’nosi: A) Ishlashni xohlaydi. B) Ishlashiga to‘g‘ri keladi. | B | Has to zaruratni bildiradi.
@16.5
G Have to inkori: The school provides lunch, so pupils ___ bring food. | do not have to~don't have to | Don’t have to ish zarur emasligini bildiradi.
C Inkor shakli: My son doesn't has to wear a tie. | My son doesn't have to wear a tie.~My son does not have to wear a tie. | Doesn’t dan keyin have asosiy shaklda qoladi.
T Don't have to bilan yozing: It is not necessary for you to reply today. You bilan boshlang. | You do not have to reply today.~You don't have to reply today. | Javob berish shart emas, lekin mumkin.
M “You don't have to stay” ma’nosi: A) Qolishingiz shart emas. B) Qolishingiz taqiqlangan. | A | Zarurat yo‘qligi taqiqdan farq qiladi.
@16.6
G Savol boshidagi yordamchi: ___ these students have to attend an interview? | Do | Ko‘plik ega bilan do ishlatiladi.
C Savoldagi fe’l: Does she has to bring a passport? | Does she have to bring a passport? | Does + she + have to standart savol qolipidir.
T Ha/yo‘q savoliga aylantiring: Your brother has to retake the test. | Does your brother have to retake the test? | Does kelganda has o‘rniga have ishlatiladi.
M Zaruratni so‘rovchi to‘g‘ri gap: A) Do we have to queue here? B) Have we queue to here? | A | Have to savoli do yordamchisi bilan tuziladi.
@16.7
G O‘tgan majburiyat: When the printer failed, I ___ write the labels by hand. (have to) | had to | O‘tmishdagi zarurat uchun had to kerak.
C O‘tgan majburiyatdagi fe’l: She had to paid a deposit yesterday. | She had to pay a deposit yesterday. | Had to dan keyin pay asosiy shakli keladi.
T Yesterday ni boshga qo‘yib o‘tmishga o‘tkazing: We have to cancel two lessons. | Yesterday, we had to cancel two lessons. | Have to o‘tgan zamonda had to bo‘ladi.
M “I had to sleep at the airport” ma’nosi: A) Hozir uxlashim mumkin. B) Aeroportda uxlashga majbur bo‘ldim. | B | Had to o‘tgan zaruratni bildiradi.
@16.8
G O‘tgan zarurat savoli: ___ you have to show your ticket again? | Did | Past Simple savolida did + have to keladi.
C Inkor fe’li: We didn't had to replace the battery. | We didn't have to replace the battery.~We did not have to replace the battery. | Didn’t dan keyin have kerak.
T Ha/yo‘q savoliga aylantiring: They had to move the piano upstairs. | Did they have to move the piano upstairs? | Did ishlatilganda had asosiy have ga qaytadi.
M “I didn't have to cook; there was enough food left” ma’nosi: A) Ovqat pishirish zarur emas edi. B) Pishirish taqiqlangan edi. | A | Didn’t have to o‘tmishda zarurat bo‘lmaganini bildiradi.
@16.9
G Will have to bilan: Next year, drivers ___ renew this permit online. | will have to | Kelajakdagi talab will have to bilan beriladi.
C Kelajak majburiyati: We will had to book a larger room. | We will have to book a larger room.~We'll have to book a larger room. | Will dan keyin have asosiy shakli kerak.
T Next month ni oxirga qo‘shib, will bilan yozing: She has to change her password. | She will have to change her password next month.~She'll have to change her password next month. | Kelajak majburiyatida will have to barcha egalarga mos.
M “You'll have to pay when the trial ends” ma’nosi: A) To‘lov hech qachon kerak emas. B) Sinov muddati tugagach to‘lashga to‘g‘ri keladi. | B | Will have to kelajakdagi zaruratni bildiradi.
@16.10
G Ixtiyoriy tashrif: You ___ attend the reception if you are busy. (mustn't / don't have to) | don't have to | Tashrif shart emasligi don’t have to bilan beriladi.
C Taqiqni ifodalash uchun modalni almashtiring: You don't have to reveal this secret. Must not ishlating. | You must not reveal this secret.~You mustn't reveal this secret. | Sirni oshkor qilish taqiqlansa must not ishlatiladi.
T Zarurat yo‘qligini don't have to bilan yozing: Bringing your own laptop is optional. You bilan boshlang. | You don't have to bring your own laptop.~You do not have to bring your own laptop. | Optional majburiy emasligini bildiradi.
M “You mustn't remove the label” va “You don't have to remove the label”: taqiq qaysi? A) Birinchi. B) Ikkinchi. | A | Mustn’t taqiq, don’t have to esa zarurat yo‘qligidir.
@16.11
G Should bilan maslahat: You ___ (back up) your photos regularly. | should back up | Should + asosiy fe’l maslahat beradi.
C Maslahatdagi fe’l: She should to ask for a second opinion. | She should ask for a second opinion. | Should dan keyin to kerak emas.
T Should bilan yozing: It is a good idea for us to compare prices. We bilan boshlang. | We should compare prices. | Yaxshi fikrni should yordamida maslahat sifatida beramiz.
M “You should stretch before running” ma’nosi: A) Yugurishdan oldin cho‘zilish mashqi tavsiya etiladi. B) Cho‘zilish taqiqlangan. | A | Should bu yerda tavsiyadir.
@16.12
G Should inkori: You ___ (share) your account password. | should not share~shouldn't share | Should not salbiy maslahat beradi.
C Fe’l shakli: You shouldn't drove when you are sleepy. | You shouldn't drive when you are sleepy.~You should not drive when you are sleepy. | Shouldn’t dan keyin drive keladi.
T Shouldn't bilan yozing: It is a bad idea to ignore this warning. You bilan boshlang. | You shouldn't ignore this warning.~You should not ignore this warning. | Yomon oqibatli ishga qarshi maslahat shouldn’t bilan beriladi.
M “You shouldn't rush this decision” ma’nosi: A) Shoshilishingiz shart. B) Shoshilmasligingiz ma’qul. | B | Shouldn’t ishni qilmaslikni tavsiya qiladi.
@16.13
G Maslahat savoli: Which platform ___ we use? (should) | should | Wh-so‘zdan keyin should + ega keladi.
C Savol tartibi: Should bring I an extra blanket? | Should I bring an extra blanket? | Should savolda egadan oldin turadi.
T What bilan maslahat so‘rang; so‘zlarni tartiblang: pack / should / we / for the trip / what. | What should we pack for the trip? | What + should + we + pack savol tartibidir.
M To‘g‘ri maslahat savoli: A) Should we check the weather first? B) Do we should check the weather first? | A | Should bilan do yordamchisi kerak emas.
@16.14
G Had better inkori: You had better ___ touch that broken socket. | not | Inkor tartibi had better not + fe’l.
C Ought qolipi: He ought apologise to the customer. | He ought to apologise to the customer.~He ought to apologize to the customer. | Ought dan keyin to-infinitive keladi.
T Had better bilan yozing: We should leave now, or we will miss the ferry. Or qismini saqlang. | We had better leave now, or we will miss the ferry.~We'd better leave now, or we'll miss the ferry.~We'd better leave now, or we will miss the ferry.~We had better leave now, or we'll miss the ferry. | Had better muayyan vaziyatda oqibatli maslahat beradi.
M “You'd better save your work” gapida 'd nimaning qisqartmasi? A) Would. B) Had. | B | Had better birikmasida ’d — had.
@16.15
G Need to, Present Simple: Each trainee ___ complete the form. | needs to | Birlik ega bilan needs to ishlatiladi.
C Needn’t qolipi: You needn't to bring a pen. | You needn't bring a pen.~You need not bring a pen. | Modal needn’t dan keyin to kelmaydi.
T Needn't bilan qayta yozing: We don't need to leave a deposit. | We needn't leave a deposit.~We need not leave a deposit. | Needn’t va don’t need to zarurat yo‘qligini bildiradi.
M “You needn't reply immediately” ma’nosi: A) Darhol javob shart emas. B) Javob berishga ruxsat yo‘q. | A | Needn’t taqiq emas, zarurat yo‘qligidir.
@16.16
G Men ovqat pishirdim, ammo mehmonlar kelmadi: I ___ (cook) so much. Needn't have ishlating. | needn't have cooked~need not have cooked | Needn’t have bajarilgan, ammo keraksiz ishni bildiradi.
C V3 shakli: We needn't have took a taxi; the station was nearby. | We needn't have taken a taxi; the station was nearby.~We need not have taken a taxi; the station was nearby. | Needn’t have dan keyin taken kerak.
T Didn't need to bilan yozing: Buying milk was unnecessary, so I did not buy any. I bilan boshlang; so qismini saqlang. | I didn't need to buy milk, so I did not buy any.~I did not need to buy milk, so I did not buy any.~I didn't need to buy milk, so I didn't buy any.~I did not need to buy milk, so I didn't buy any. | So qismi ish bajarilmaganini aniq ko‘rsatadi.
M “We needn't have booked a hotel” nimani aniq bildiradi? A) Band qilmaganmiz. B) Band qilganmiz, ammo zarur emas ekan. | B | Needn’t have + V3 bajarilgan keraksiz ishdir.
""")

add(r"""
@17.1
G Noaniq ehtimol; may/might/could dan foydalaning: The missing receipt ___ be in my coat. | may~might~could | Uchala modal ham bu yerda ehtimolni bildiradi.
C Modal shakli: That shadow might belongs to a cat. | That shadow might belong to a cat. | Might dan keyin belong asosiy shakli keladi.
T Might bilan yozing: Perhaps the museum is closed today. | The museum might be closed today. | Perhaps mazmuni might be bilan ifodalanadi.
M “The stain could be ink” ma’nosi: A) Dog‘ siyoh bo‘lishi mumkin. B) Dog‘ albatta siyoh. | A | Could taxminni bildiradi, aniqlikni emas.
@17.2
G May bilan ehtimoliy inkor: The instructions ___ apply to older models. | may not | May not bajarilmaslik ehtimolini bildiradi.
C Ehtimoliy inkor tartibi: She not might remember our address. | She might not remember our address. | Not modal fe’ldan keyin keladi.
T Might not bilan yozing: Perhaps the signature is not genuine. | The signature might not be genuine.~The signature mightn't be genuine. | Might not be haqiqiy bo‘lmaslik ehtimolini beradi.
M “He may not agree” ma’nosi: A) U rozi bo‘lishi taqiqlangan. B) Balki u rozi bo‘lmas. | B | Bu gap ehtimoliy inkorni bildiradi.
@17.3
G Dalildan xulosa, must: The oven has been on for hours. It ___ (be) hot. | must be | Kuchli dalilga asoslangan hozirgi xulosa must be bilan beriladi.
C Taxmindagi fe’l: You must are hungry after that long walk. | You must be hungry after that long walk. | Must dan keyin be kerak.
T Must bilan xulosa qiling: I am sure this is the correct entrance. This bilan boshlang. | This must be the correct entrance. | Must kuchli ishonchli taxminni ifodalaydi.
M “That must be the delivery driver; he is carrying our parcel” ma’nosi: A) Dalilga asoslangan taxmin. B) Haydovchiga berilgan majburiyat. | A | Posilka ko‘tarib kelishi taxmin uchun dalildir.
@17.4
G Can't bilan: This painting ___ be an original; the artist died before it was painted. | can't~cannot | Can’t be kuchli inkoriy taxmindir.
C Taxmin qolipi: That cannot is the right price. | That cannot be the right price.~That can't be the right price. | Cannot dan keyin be keladi.
T Can't bilan yozing: I am sure the caller is not my father. The caller bilan boshlang. | The caller can't be my father.~The caller cannot be my father. | Can’t be hozirgi imkonsiz taxminni bildiradi.
M “It can't be midnight; the sun is still up” ma’nosi: A) Yarim tun bo‘lishi taqiqlangan. B) Yarim tun bo‘lishi mumkin emas. | B | Can’t bu yerda dalil asosida imkonni inkor qiladi.
@17.5
G Ehtimol savoli: ___ this message be a scam? (Could / Does) | Could | Could + ega + be ehtimolni so‘raydi.
C Savol tartibi: Could be those footprints a bear's? | Could those footprints be a bear's? | Could dan keyin ega, so‘ng be keladi.
T Could bilan savol tuzing: Perhaps the noise is coming from the cellar. | Could the noise be coming from the cellar? | Could savoli ehtimoliy manbani tekshiradi.
M “Could she be our new tutor?” ma’nosi: A) U yangi ustozimiz bo‘lishi mumkinmi? B) U avval dars bera olarmidi? | A | Could be hozirgi ehtimolni so‘rayapti.
@17.6
G Hozirgi jarayon taxmini: The children may ___ (hide) behind the shed. | be hiding | Modal + be + -ing davom etayotgan ishga ishora qiladi.
C Davomiy taxmin: He must be wait for the train. | He must be waiting for the train. | Be dan keyin waiting kerak.
T Might bilan yozing: Perhaps the mechanic is testing the brakes now. | The mechanic might be testing the brakes now. | Might be testing hozirgi jarayon ehtimolidir.
M “They could be discussing the budget now” ma’nosi: A) Muhokama albatta tugagan. B) Hozir muhokama qilayotgan bo‘lishlari mumkin. | B | Be + -ing jarayonni bildiradi.
@17.7
G Must have bilan: The biscuits have vanished. Someone ___ (eat) them. | must have eaten | O‘tgan kuchli taxmin: must have + V3.
C V3 shakli: She must have took the wrong train. | She must have taken the wrong train. | Take fe’lining V3 shakli taken.
T Must have bilan yozing: I am sure they forgot the appointment. They bilan boshlang. | They must have forgotten the appointment. | Oldingi voqea haqida kuchli xulosa must have bilan beriladi.
M “The dog must have escaped through the gate” ma’nosi: A) It chiqib ketgan, deb kuchli taxmin qilinyapti. B) Itga chiqish buyurilgan. | A | Must have escaped o‘tgan taxmin, majburiyat emas.
@17.8
G Might have bilan: Perhaps the email went into spam. It ___ (go) into spam. | might have gone | Might have + V3 o‘tgan ehtimolni beradi.
C Modal perfect: We may have chose the wrong path. | We may have chosen the wrong path. | Have dan keyin chosen V3 shakli kerak.
T Could have bilan o‘tgan ehtimolni yozing: Perhaps the wind damaged the roof. | The wind could have damaged the roof. | Could have damaged ehtimoliy o‘tgan sababni bildiradi.
M “Mina might have left already” ma’nosi: A) Mina albatta ketgan. B) Mina allaqachon ketgan bo‘lishi mumkin. | B | Might have ishonchsiz o‘tgan taxmindir.
@17.9
G Couldn't have bilan: He was abroad all week. He ___ (attend) yesterday's local meeting. | could not have attended~couldn't have attended | Couldn’t have o‘tgan ishning imkonsizligini bildiradi.
C V3 shakli: You can't have wrote this in two minutes. | You can't have written this in two minutes.~You cannot have written this in two minutes. | Write fe’lining V3 shakli written.
T Can't have bilan yozing: It is impossible that Sara signed the form; she was away. Sara bilan boshlang, nuqtali verguldan keyingi qismni saqlang. | Sara can't have signed the form; she was away.~Sara cannot have signed the form; she was away. | O‘tgan imkonsiz taxmin can’t have + V3 bilan beriladi.
M “They couldn't have known the password” ma’nosi: A) Parolni bilgan bo‘lishlari mumkin emas. B) Parolni bilishlari shart edi. | A | Couldn’t have known o‘tgan imkonni inkor qiladi.
@17.10
G Afsus, should have: I missed the deadline. I ___ (start) sooner. | should have started | Bajarilmagan yaxshi ish should have bilan ifodalanadi.
C V3 shakli: You should have wore gloves. | You should have worn gloves. | Wear fe’lining V3 shakli worn.
T Should have bilan afsus bildiring: We did not check the tyres, and that was a mistake. We bilan boshlang. | We should have checked the tyres. | O‘tmishdagi to‘g‘ri, ammo qilinmagan ish ifodalanadi.
M “I should have thanked her” ma’nosi: A) Rahmat aytishni taqiqlayapman. B) Rahmat aytmaganimdan afsusdaman. | B | Should have bu kontekstda bajarilmagan ishga afsusdir.
@17.11
G Afsus, should not have: I lent him my only key. I ___ (do) that. | should not have done~shouldn't have done | Qilingan noto‘g‘ri ishga shouldn’t have ishlatiladi.
C V3 shakli: We shouldn't have ate those mushrooms. | We shouldn't have eaten those mushrooms.~We should not have eaten those mushrooms. | Eat fe’lining V3 shakli eaten.
T Shouldn't have bilan yozing: It was a mistake to interrupt the speaker. I bilan boshlang. | I shouldn't have interrupted the speaker.~I should not have interrupted the speaker. | Shouldn’t have interrupted qilingan ishga afsusni bildiradi.
M “You shouldn't have posted my photo” ma’nosi: A) Surat joylangan, bu noto‘g‘ri deb baholanyapti. B) Surat joylanmaganiga afsus bildirilmoqda. | A | Shouldn’t have bu yerda bajarilgan ishni tanqid qiladi.
@17.12
G Foydalanilmagan imkon, could have: There were spare seats, but we stood. We ___ (sit) down. | could have sat | Could have sat foydalanilmagan imkonni bildiradi.
C V3 shakli: I could have chose a cheaper model, but I didn't. | I could have chosen a cheaper model, but I didn't.~I could have chosen a cheaper model, but I did not. | Could have dan keyin chosen kerak.
T Could have bilan yozing: She had the chance to study abroad but chose to stay. She bilan boshlang; but chose to stay ni saqlang. | She could have studied abroad but chose to stay. | Imkon bo‘lgan, ammo undan foydalanilmagan.
M “We could have won, but we made too many mistakes” ma’nosi: A) Albatta yutdik. B) Yutish imkoni bor edi, ammo yutmadik. | B | But qismi imkon amalga oshmaganini ko‘rsatadi.
@17.13
G Past ehtimol: With only two players available, the team is ___ win. (likely to / unlikely to) | unlikely to | Unlikely to ehtimol pastligini bildiradi.
C Qolip: The repairs are likely take a week. | The repairs are likely to take a week. | Likely dan keyin to-infinitive kerak.
T Likely to bilan yozing: It is probable that the river will flood. The river bilan boshlang. | The river is likely to flood. | Be likely to yuqori ehtimolni bildiradi.
M “The price is unlikely to fall” ma’nosi: A) Narx pasayishi ehtimoli past. B) Narx pasayishi aniq. | A | Unlikely ehtimolni kamaytiradi, butunlay inkor qilmaydi.
@17.14
G Will va fe’l orasiga ravish: We will ___ need a bigger van. (probably) | probably | Tasdiq gapda probably odatda will dan keyin keladi.
C Ravish joyi: She is tired probably. Probably ni is dan keyinga qo‘ying. | She is probably tired. | Be fe’lidan keyin probably odatiy joylashuvdir.
T Probably ni won't dan oldinga qo‘shing: I won't finish before lunch. | I probably won't finish before lunch.~I probably will not finish before lunch. | Probably odatda inkor yordamchidan oldin turadi.
M Qaysi ravish kuchliroq ishonch bildiradi? A) Probably. B) Definitely. | B | Definitely aniq ishonchni, probably yuqori ehtimolni bildiradi.
@18.1
G Umumiy qoida, Zero Conditional: If metal gets hot, it ___ (expand). | expands | Umumiy qonuniyatda ikkala qism Present Simple bo‘ladi.
C Umumiy qonuniyat uchun will ni olib tashlang: If you mix red and white, you will get pink. | If you mix red and white, you get pink. | Zero Conditional doimiy natijani Present Simple bilan beradi.
T If bilan boshlanadigan qoida qiling: Press this button and the screen lights up. You egasini ishlating. | If you press this button, the screen lights up. | If + Present Simple, Present Simple umumiy qoidadir.
M “If water reaches 100°C at sea level, it boils” ma’nosi: A) Umumiy qonuniyat. B) Faqat ertangi faraz. | A | Zero Conditional takroran amal qiladigan natijani bildiradi.
@18.2
G Umumiy qoida: If this switch is off, the fan ___ (not spin). | does not spin~doesn't spin | Birlik ega inkorida does not + asosiy fe’l kerak.
C Zero Conditional inkori: If you doesn't practise, you lose confidence. | If you don't practise, you lose confidence.~If you do not practise, you lose confidence.~If you don't practice, you lose confidence.~If you do not practice, you lose confidence. | You bilan don’t ishlatiladi.
T Umumiy qoidada natijani inkor qiling: If the lid is loose, the jar stays airtight. | If the lid is loose, the jar does not stay airtight.~If the lid is loose, the jar doesn't stay airtight. | Zero Conditional natija inkori Present Simple da qoladi.
M “If you don't water seedlings, they die” gapida don't water nimani bildiradi? A) O‘tgan afsusni. B) Takroriy salbiy shartni. | B | Shart qismi umumiy holatdagi bajarilmaslikni bildiradi.
@18.3
G Umumiy qoida savoli: What ___ (happen) if you freeze juice? | happens | What ega vazifasida; happens ishlatiladi.
C Savol yordamchisi: Does these seeds grow if the soil is dry? | Do these seeds grow if the soil is dry? | Ko‘plik seeds bilan do kerak.
T Ha/yo‘q savoliga aylantiring: The alarm sounds if the door opens. | Does the alarm sound if the door opens? | Does dan keyin sound asosiy shaklga qaytadi.
M Umumiy ishlash tartibini so‘rang: A) What does the app do if the connection fails? B) What the app does if the connection fails? | A | To‘g‘ri savol tartibi what + does + ega + fe’l.
@18.4
G First Conditional: If the parcel ___ (arrive) today, I will bring it over. | arrives | Kelajak sharti if qismida Present Simple bo‘ladi.
C If qismidagi zamon: If we will find a table, we will stay for dinner. | If we find a table, we will stay for dinner.~If we find a table, we'll stay for dinner. | Oddiy kelajak shartida if dan keyin will kerak emas.
T If bilan birlashtiring, will ishlating: You lend me the tools. I repair the fence. | If you lend me the tools, I will repair the fence.~If you lend me the tools, I'll repair the fence. | Real kelajak sharti: if + present, will + fe’l.
M “If she wins, she'll represent our school” ma’nosi: A) G‘alaba imkonsiz. B) G‘alaba real ehtimol sifatida ko‘rilgan. | B | First Conditional amalga oshishi mumkin bo‘lgan kelajakni bildiradi.
@18.5
G First Conditional: If we ___ (not leave) now, we will be late. | do not leave~don't leave | If qismidagi inkor Present Simple da bo‘ladi.
C Natija inkori: If it snows, they won't drove to the village. | If it snows, they won't drive to the village.~If it snows, they will not drive to the village. | Won’t dan keyin drive asosiy shakli kerak.
T Faqat natijani inkor qiling: If the price rises, I will buy the camera. | If the price rises, I will not buy the camera.~If the price rises, I won't buy the camera. | Kelajak natijasi will not bilan inkor qilinadi.
M “If you don't save the file, you'll lose your changes” ma’nosi: A) Saqlamaslik o‘zgarishlar yo‘qolishiga olib keladi. B) O‘zgarishlar allaqachon yo‘qolgan. | A | Gap kelajakdagi salbiy shart va natijani bildiradi.
@18.6
G Savol boshidagi yordamchi: ___ you visit us if your meeting ends early? (will) | Will | Natija haqidagi savol Will + ega bilan boshlanadi.
C If qismidagi fe’l: Will they refund us if the concert will be cancelled? | Will they refund us if the concert is cancelled? | If qismida kelajak uchun is cancelled ishlatiladi.
T Ha/yo‘q savoliga aylantiring: You will cycle if the roads are dry. | Will you cycle if the roads are dry? | Faqat asosiy qismda will egadan oldinga o‘tadi.
M To‘g‘ri savol: A) Will it work if I replace the battery? B) Will work it if I replace the battery? | A | Will + it + work standart savol tartibidir.
@18.7
G First Conditional savoli: Who will feed the cat if you ___ (go) away? | go | If qismida go Present Simple shakli kerak.
C Savol tartibi: How you will get home if the buses stop? | How will you get home if the buses stop? | How dan keyin will + ega keladi.
T Where bilan joyni so‘rang: They will meet at the library if it rains. | Where will they meet if it rains? | Where natijadagi joy haqida savol beradi.
M “What will you do if the lift breaks?” nimani so‘raydi? A) O‘tgan xatoni. B) Muammo bo‘lsa, kelajakdagi harakatni. | B | Will bilan wh-savol shartli kelajak natijasini so‘raydi.
@18.8
G Buyruq natijasi: If the milk smells sour, ___ (throw) it away. | throw | Buyruq qismida asosiy fe’l ishlatiladi.
C Modal natija: If your work is complete, you can to go home. | If your work is complete, you can go home. | Natijada can + asosiy fe’l keladi.
T If bilan birlashtiring; natijani buyruq qiling: You feel dizzy. Sit down. | If you feel dizzy, sit down. | Shartdan keyin buyruq natija kelishi mumkin.
M “If the path is icy, you should wear boots” natijasi nimani bildiradi? A) Maslahat. B) O‘tgan muvaffaqiyat. | A | Should shart bajarilgandagi maslahatni bildiradi.
@18.9
G Agar to‘lamasangiz: ___ you pay the fee, your application will not be processed. | Unless | Unless if not ma’nosini beradi.
C Unless bilan ortiqcha inkorni olib tashlang: Unless you don't hurry, you will miss the opening. Ma’no: shoshilmasangiz. | Unless you hurry, you will miss the opening. | Unless ichida inkor ma’nosi bor.
T Unless bilan boshlang: If the weather does not improve, we will cancel the hike. | Unless the weather improves, we will cancel the hike.~Unless the weather improves, we'll cancel the hike. | If not o‘rniga unless va tasdiq fe’l keladi.
M “I won't sign unless I understand” ma’nosi: A) Tushunmasam ham imzolayman. B) Faqat tushunsam imzolayman. | B | Unless zarur shartni inkor orqali belgilaydi.
@18.10
G Second Conditional: If I ___ (know) her number, I would call her. | knew | Hozirgi farazning if qismida Past Simple kerak.
C Faraz sharti: If he would have a boat, he would sail every weekend. | If he had a boat, he would sail every weekend.~If he had a boat, he'd sail every weekend. | If qismida would have emas, had ishlatiladi.
T Second Conditional qiling: I do not own a camera, so I do not take wildlife photos. If I owned bilan boshlang, would ishlating. | If I owned a camera, I would take wildlife photos.~If I owned a camera, I'd take wildlife photos. | Hozir yo‘q shartning faraziy natijasi if + past, would + fe’l.
M “If we lived by the sea, we would swim daily” nimani bildiradi? A) Hozirgi faraziy holatni. B) O‘tgan aniq voqeani. | A | Past shakli bu yerda vaqtni emas, farazni bildiradi.
@18.11
G Second Conditional inkori: If petrol were cheaper, we ___ (not spend) so much on travel. | would not spend~wouldn't spend | Faraziy natijaning inkori would not + fe’l.
C If qismidagi inkor: If she doesn't live so far away, we would visit more often. Second Conditional qiling. | If she didn't live so far away, we would visit more often.~If she did not live so far away, we would visit more often.~If she didn't live so far away, we'd visit more often.~If she did not live so far away, we'd visit more often. | Second Conditional shartida didn’t + fe’l keladi.
T Natijani inkor qiling: If I had a garden, I would grow roses. | If I had a garden, I would not grow roses.~If I had a garden, I wouldn't grow roses. | Would not grow faraziy salbiy natijadir.
M “If I didn't trust her, I wouldn't lend her my car” ma’nosi: A) Unga ishonmayman. B) Aslida unga ishonaman. | B | Teskari faraz hozir ishonch borligini anglatadi.
@18.12
G Second Conditional savoli: Would you learn sailing if you ___ (live) near a lake? | lived | Would savolining if qismida Past Simple keladi.
C Savol tartibi: Would accept she the job if it paid more? | Would she accept the job if it paid more? | Would + ega + fe’l kerak.
T Ha/yo‘q savoliga aylantiring: They would buy the flat if it were cheaper. | Would they buy the flat if it were cheaper? | Faraziy natijani so‘rash uchun would oldinga o‘tadi.
M Faraziy savolni tanlang: A) Would you keep a horse if you had enough land? B) Did you keep a horse last year? | A | Would va if + past hozirgi farazni so‘raydi.
@18.13
G Faraziy savol: What would you change if you ___ (run) this school? | ran | Run fe’lining Past Simple shakli ran.
C Wh-savol tartibi: Who you would invite if you had six tickets? | Who would you invite if you had six tickets? | Who bu yerda to‘ldiruvchi; would + you tartibi kerak.
T Which country bilan mamlakatni so‘rang: She would visit Japan if she had a month off. | Which country would she visit if she had a month off? | Which country faraziy tanlovni so‘raydi.
M “How would you travel if money were no problem?” nimani so‘raydi? A) Faraziy sharoitdagi safar usulini. B) Kechagi aniq yo‘lni. | A | How + would faraziy usulni so‘raydi.
@18.14
G Maslahat qolipi: If I were you, I ___ (keep) a copy. Would ishlating. | would keep | If I were you dan keyin would + fe’l keladi.
C An’anaviy qolipni tuzating: If I am you, I would talk to the tutor. | If I were you, I would talk to the tutor.~If I were you, I'd talk to the tutor. | Maslahat qolipi If I were you shaklida bo‘ladi.
T If I were you bilan boshlang: You should not accept that offer. Would ishlating. | If I were you, I would not accept that offer.~If I were you, I wouldn't accept that offer. | Salbiy maslahat would not bilan beriladi.
M “If I were you, I'd check the dates” vazifasi: A) O‘zini tanishtirish. B) Maslahat berish. | B | Bu qolip suhbatdosh o‘rnida qanday yo‘l tutishni aytadi.
@18.15
G Real kelajak: If I get permission, I ___ join you. (will / would) | will | Real kelajak shartida will ishlatiladi.
C Hozir mashinam yo‘q, faraz: If I had a car, I will drive to work. | If I had a car, I would drive to work.~If I had a car, I'd drive to work. | Had bilan faraziy natija would talab qiladi.
T Farazni real kelajak ehtimoliga aylantiring: If she won, she would donate the prize. | If she wins, she will donate the prize.~If she wins, she'll donate the prize. | First Conditional da wins va will donate ishlatiladi.
M Qaysi gap shartni kamroq real deb ko‘rsatadi? A) If I found gold, I would retire. B) If I find gold, I will retire. | A | Second Conditional shartni faraz sifatida uzoqroq ko‘rsatadi.
@18.16
G Natija boshda: I will wait outside ___ the door is locked. (if / so) | if | If qismi asosiy gapdan keyin ham keladi.
M Standart vergul: A) If the train is delayed, we will call. B) If the train is delayed we, will call. | A | Shart boshda bo‘lsa, uning oxiriga vergul qo‘yiladi.
T Shartni oxirga ko‘chiring: If the parcel arrives, I will let you know. | I will let you know if the parcel arrives.~I'll let you know if the parcel arrives. | Oxirdagi if qismidan oldin odatda vergul kerak emas.
T Shartni boshga ko‘chiring: We will eat indoors if it gets windy. | If it gets windy, we will eat indoors.~If it gets windy, we'll eat indoors. | Boshdagi if qismi vergul bilan ajratiladi.
@19.1
G Third Conditional: If we had checked the timetable, we ___ (catch) the train. Would have ishlating. | would have caught | O‘tgan faraz natijasi would have + V3 bilan beriladi.
C If qismidagi shakl: If he has applied sooner, he would have got a place. | If he had applied sooner, he would have got a place.~If he had applied sooner, he would have gotten a place. | O‘tgan amalga oshmagan shart had + V3 bo‘ladi.
T If bilan o‘tgan teskari faraz qiling: I did not wear a coat, so I got cold. Had worn va would have stayed warm ishlating. | If I had worn a coat, I would have stayed warm.~If I'd worn a coat, I would have stayed warm.~If I had worn a coat, I'd have stayed warm.~If I'd worn a coat, I'd have stayed warm. | Third Conditional o‘tgan voqeaning boshqacha natijasini tasavvur qiladi.
M “If she had entered, she would have won” gapida: A) U qatnashmagan. B) U aniq g‘olib bo‘lgan. | A | O‘tgan teskari faraz shart amalga oshmaganini bildiradi.
@19.2
G Third Conditional inkori: If you ___ (not warn) me, I would have fallen. | had not warned~hadn't warned | Salbiy o‘tgan shart had not + V3 bilan beriladi.
C Natija shakli: If I had seen the sign, I wouldn't parked there. | If I had seen the sign, I wouldn't have parked there.~If I had seen the sign, I would not have parked there. | O‘tgan natijaga would not have + V3 kerak.
T Faqat natijani inkor qiling: If we had known the cost, we would have booked the venue. | If we had known the cost, we would not have booked the venue.~If we had known the cost, we wouldn't have booked the venue. | Would have inkorida not would dan keyin keladi.
M “If he hadn't rushed, he wouldn't have dropped the plates” gapida: A) U shoshmagan. B) U shoshgan va likopchalarni tushirib yuborgan. | B | Teskari o‘tgan faraz haqiqiy salbiy natijani ko‘rsatadi.
@19.3
G Third Conditional savoli: Would you have complained if the meal ___ (be) cold? | had been | O‘tgan shart had been bilan ifodalanadi.
C Savol tartibi: Would they accepted have the offer if we had paid more? | Would they have accepted the offer if we had paid more? | Would + ega + have + V3 kerak.
T Ha/yo‘q savoliga aylantiring: She would have stayed if the last bus had gone. | Would she have stayed if the last bus had gone? | Savolda would egadan oldin turadi.
M O‘tgan faraz savoli: A) Would you have called if you had heard the news? B) Will you call if you hear the news? | A | Have + V3 va had + V3 o‘tgan farazni bildiradi.
@19.4
G O‘tgan faraz savoli: How would you ___ (travel) if the airport had closed? | have travelled~have traveled | Would dan keyin have + V3 kerak.
C Wh-savol tartibi: Where you would have gone if the hotel had been full? | Where would you have gone if the hotel had been full? | Where + would + ega + have + V3.
T What bilan narsani so‘rang: He would have bought a bicycle if he had saved enough. | What would he have bought if he had saved enough? | What o‘tgan farazdagi tanlangan narsani so‘raydi.
M “Who would you have asked if I had been away?” nimani so‘raydi? A) Ertangi rejani. B) O‘tgan boshqa sharoitda kimdan so‘rashni. | B | Would have asked amalga oshmagan o‘tgan tanlovdir.
@19.5
G O‘tgan imkon: If the shop had been open, we ___ (buy) batteries. Could have ishlating. | could have bought | Could have natijadagi imkonni ko‘rsatadi.
C V3: If you had explained, I might have understand. | If you had explained, I might have understood. | Might have dan keyin understood kerak.
T Natijani kamroq qat’iy qiling; would o‘rniga might ishlating: If we had trained harder, we would have won. | If we had trained harder, we might have won. | Might have natijani ehtimol sifatida beradi.
M “If I'd taken the course, I could have applied” nimani bildiradi? A) Ariza berish imkoniyati paydo bo‘lardi. B) Ariza albatta qabul qilinardi. | A | Could have imkonni bildiradi, muvaffaqiyatni kafolatlamaydi.
@19.6
G O‘tgan sabab, hozirgi natija: If I had accepted the job, I ___ (live) abroad now. Would bilan davomiy shakl. | would be living | O‘tgan shart hozir davom etayotgan natijaga bog‘langan.
C Hozirgi holatni tuzating: If she had saved the file, she would have been relaxed now. Would be ishlating. | If she had saved the file, she would be relaxed now. | Now bilan hozirgi holat would be shaklida beriladi.
T If bilan yozing: I lost the key yesterday, so I cannot enter now. Had not lost va would be able to ishlating. | If I had not lost the key yesterday, I would be able to enter now.~If I hadn't lost the key yesterday, I would be able to enter now.~If I had not lost the key yesterday, I'd be able to enter now.~If I hadn't lost the key yesterday, I'd be able to enter now. | O‘tgan xato hozirgi imkoniyatga ta’sir qilgan.
M “If he'd taken the medicine, he would feel better now” natijasi qaysi vaqtga tegishli? A) Hozirga. B) Faqat uzoq o‘tmishga. | A | Would feel va now hozirgi natijani ko‘rsatadi.
@19.7
G Doimiy xususiyat, o‘tgan natija: If I ___ (know) Japanese, I would have understood yesterday's speech. | knew | Hozirgi umumiy bilim sharti Past Simple bilan beriladi.
C O‘tgan natija: If she were taller, she would reach the shelf yesterday. | If she were taller, she would have reached the shelf yesterday. | Yesterday natijasi would have + V3 talab qiladi.
T Mixed Conditional qiling: I am afraid of heights, so I did not climb the tower yesterday. If I were not bilan boshlang; would ishlating. | If I were not afraid of heights, I would have climbed the tower yesterday.~If I weren't afraid of heights, I would have climbed the tower yesterday.~If I were not afraid of heights, I'd have climbed the tower yesterday.~If I weren't afraid of heights, I'd have climbed the tower yesterday. | Doimiy qo‘rquv o‘tgan qarorga ta’sir qilgan.
M “If I were a mechanic, I would have fixed it yesterday” sharti nimani bildiradi? A) Faqat kechagi kasbni. B) Hozirgi umumiy kasb holatini. | B | Were a mechanic umumiy hozirgi xususiyatdir.
@19.8
G O‘tgan shart, hozirgi inkor: If we had booked earlier, we ___ (not wait) outside now. Would bilan davomiy shakl. | would not be waiting~wouldn't be waiting | Hozirgi salbiy jarayon would not be + -ing bilan beriladi.
C Savol tartibi: Would be you here now if you hadn't missed the flight? | Would you be here now if you hadn't missed the flight?~Would you be here now if you had not missed the flight? | Would + ega + be; o‘tgan shart had not missed.
T Ha/yo‘q savoliga aylantiring: She would be happier now if she had moved. | Would she be happier now if she had moved? | Savol o‘tgan qarorning hozirgi ta’sirini tekshiradi.
M Qaysi gapda o‘tgan shart va hozirgi natija bor? A) Would you be unemployed now if you hadn't resigned? B) Would you have resigned if they had paid more? | A | Now hozirgi natijani, hadn’t resigned o‘tgan shartni bildiradi.
@19.9
G Hozir uzoqda ishlayman: I wish I ___ (work) closer to home. | worked | Hozirgi istakka wish + Past Simple kerak.
C Hozirgi istak: If only I know the answer! | If only I knew the answer! | Hozir bilmaslikka istak knew bilan ifodalanadi.
T Wish bilan yozing: I do not have a quieter room. I wish bilan boshlang. | I wish I had a quieter room. | Wish + had hozir yo‘q narsani istashdir.
M “I wish I were more patient” ma’nosi: A) Hozir sabrliroq bo‘lishni istayman. B) Kecha sabrli bo‘lganimni aytyapman. | A | Past shakli hozirgi haqiqatga teskari istakni bildiradi.
@19.10
G O‘tgan afsus: I wish I ___ (not sell) my old guitar. | had not sold~hadn't sold | Wish + Past Perfect o‘tgan afsusni bildiradi.
C O‘tgan afsus shakli: If only we have booked earlier! | If only we had booked earlier! | If only dan keyin o‘tgan afsus uchun had + V3 kerak.
T Wish bilan yozing: I did not take your advice, and I regret it. I wish bilan boshlang. | I wish I had taken your advice.~I wish I'd taken your advice. | O‘tgan qilinmagan ishga afsus had taken bilan beriladi.
M “She wishes she hadn't sent the email” gapida: A) Xatni yubormagan. B) Xatni yuborgan va afsuslanmoqda. | B | Hadn’t sent istagi haqiqiy yuborishning teskarisidir.
@19.11
G Odat o‘zgarishini istang: I wish the dog ___ stop barking at night. | would | Wish + would bezovta qiluvchi holat o‘zgarishini istaydi.
C Wish qolipi: I wish people will stop dropping litter here. | I wish people would stop dropping litter here. | Wish bilan bunday o‘zgarishda will emas, would keladi.
T Wouldn't bilan yozing: My colleague keeps interrupting me. I wish my colleague bilan boshlang. | I wish my colleague wouldn't keep interrupting me.~I wish my colleague would not keep interrupting me. | Wouldn’t boshqa kishining takroriy ishidan norozilikni bildiradi.
M “I wish the rain would stop” nimani bildiradi? A) Holat o‘zgarishini istashni. B) O‘tgan yomg‘irni eslashni. | A | Would bu yerda kelajakdagi o‘zgarish istagidir.
@19.12
G Imkon yo‘q: I wish I ___ afford a larger flat. (can / could) | could | Wish + could yetishmayotgan imkonni bildiradi.
C Wish bilan qobiliyat: If only I can play the cello! | If only I could play the cello! | Haqiqatga teskari qobiliyat istagida could keladi.
T I wish bilan yozing: I cannot stay longer. | I wish I could stay longer. | Could qolish imkonini istashni bildiradi.
M “I wish I could hear you clearly” ma’nosi: A) Sizni eshitishim taqiqlangan. B) Yaxshi eshita olishni istayman. | B | Could qobiliyat yoki imkoniyat istagidir.
@19.13
G Haqiqiy kelajak umidi: I ___ the weather improves before our trip. (hope / wish) | hope | Amalga oshishi mumkin bo‘lgan natijaga hope ishlatiladi.
C Hozir vaqtim yo‘q: I hope I had more free time. Wish ishlating. | I wish I had more free time. | Hozirgi haqiqatga teskari istak wish bilan beriladi.
T Hope bilan qayta yozing: Perhaps you will enjoy your new job; that is what I want. I hope you bilan boshlang. | I hope you enjoy your new job.~I hope you will enjoy your new job.~I hope you'll enjoy your new job. | Hope dan keyin present yoki will bilan real umid bildiriladi.
M “I wish I hadn't missed the lecture” nimani bildiradi? A) O‘tmishga afsus. B) Natijasi hali noma’lum kelajak umidi. | A | Wish + Past Perfect o‘tgan afsusdir.
@19.14
G Har qanday holatda: I will support you ___ you lose. (provided / even if) | even if | Even if natija shartga qaramay o‘zgarmasligini bildiradi.
C Shartdagi zamon: You can stay as long as you will keep quiet. | You can stay as long as you keep quiet. | As long as dan keyin oddiy kelajak sharti Present Simple bo‘ladi.
T Provided that bilan if ni almashtiring: You may use the car if you fill the tank afterwards. | You may use the car provided that you fill the tank afterwards. | Provided that aniq shartni ta’kidlaydi.
M “I'll walk even if it snows” ma’nosi: A) Faqat qor yog‘sa yuraman. B) Qor yog‘sa ham yuraman. | B | Even if shart natijani to‘xtatmasligini bildiradi.
""")


def normalize(value):
    value = unicodedata.normalize('NFKC', value).lower()
    value = re.sub('[’‘`]', "'", value)
    return ' '.join(re.sub(r'[.!?,;:]', '', value).split())


def accepted_variants(answers):
    """Add conventional contractions without contracting terminal short answers.

    The app ignores case/punctuation but does not expand contractions. Avoid
    automatically contracting lexical have/had, which need contextual judgement.
    """
    negatives = {
        'cannot': "can't", 'could not': "couldn't", 'must not': "mustn't",
        'should not': "shouldn't", 'will not': "won't", 'would not': "wouldn't",
        'do not': "don't", 'does not': "doesn't", 'did not': "didn't",
        'is not': "isn't", 'are not': "aren't", 'was not': "wasn't",
        'were not': "weren't", 'has not': "hasn't", 'have not': "haven't",
        'had not': "hadn't", 'need not': "needn't",
    }
    suffix = {'will': "'ll", 'would': "'d", 'is': "'s", 'are': "'re"}
    pronoun = re.compile(r'\b(I|[Yy]ou|[Hh]e|[Ss]he|[Ii]t|[Ww]e|[Tt]hey) (will|would|is|are)(?= [A-Za-z])')
    result = list(answers)
    seen = {normalize(a) for a in result}
    for answer in result:
        variants = []
        for full, short in negatives.items():
            for source, replacement in ((full, short), (short, full)):
                variants.append(re.sub(r'\b' + re.escape(source) + r'\b', replacement, answer))
        for match in pronoun.finditer(answer):
            if match[2] in ('will', 'would') and answer[match.end():].startswith(' not'):
                continue
            variants.append(answer[:match.start()] + match[1] + suffix[match[2]] + answer[match.end():])
        for variant in variants:
            key = normalize(variant)
            if key not in seen:
                seen.add(key)
                result.append(variant)
    return result


def validate(bank):
    modules = json.loads((ROOT / 'src/data/intensive-grammar-map.json').read_text(encoding='utf-8'))
    existing = json.loads((ROOT / 'src/data/intensive-topic-exercises.json').read_text(encoding='utf-8'))
    expected = {f'{mi+1}.{ti+1}' for mi in range(14, 27)
                for ti in range(len(modules[mi]['items']))}
    assert set(bank) == expected, (expected - set(bank), set(bank) - expected)
    old_prompts = {normalize(q['prompt']) for rows in existing.values() for q in rows}
    seen = set()
    for topic, rows in bank.items():
        assert len(rows) == 4, (topic, len(rows))
        for q in rows:
            assert set(q) <= {'prompt', 'answers', 'explanation', 'hint'}
            assert all(isinstance(q[k], str) and q[k].strip() for k in ('prompt', 'explanation'))
            assert isinstance(q['answers'], list) and q['answers']
            assert all(isinstance(a, str) and a.strip() for a in q['answers'])
            assert len({normalize(a) for a in q['answers']}) == len(q['answers']), (topic, q)
            prompt = normalize(q['prompt'])
            assert prompt not in old_prompts, (topic, 'existing duplicate', q['prompt'])
            assert prompt not in seen, (topic, 'new duplicate', q['prompt'])
            seen.add(prompt)
            if q['prompt'].startswith(PREFIX['M']):
                assert 'A)' in q['prompt'] and 'B)' in q['prompt']
                assert q['answers'] in (['A'], ['B'])
    return len(bank), sum(map(len, bank.values()))


def main():
    bank = dict(sorted(BANK.items(), key=lambda pair: tuple(map(int, pair[0].split('.')))))
    for rows in bank.values():
        for question in rows:
            question['answers'] = accepted_variants(question['answers'])
    counts = validate(bank)
    if sys.argv[1:] == ['--check']:
        saved = json.loads(DEST.read_text(encoding='utf-8'))
        validate(saved)
        assert saved == bank, 'Saved JSON differs from authored source'
        print(f'PASS: {counts[0]} topics, {counts[1]} exercises; schema, coverage, duplicates, reproducibility')
    elif not sys.argv[1:]:
        DEST.write_text(json.dumps(bank, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'WROTE: {DEST} ({counts[0]} topics, {counts[1]} exercises)')
    else:
        raise SystemExit('Usage: build-intensive-exercises-advanced.py [--check]')


if __name__ == '__main__':
    main()
