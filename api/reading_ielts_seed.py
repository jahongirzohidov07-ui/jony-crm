# -*- coding: utf-8 -*-
"""IELTS READING — TRUE/FALSE/NOT GIVEN va YES/NO/NOT GIVEN (2026-08-25).

Jahongir: "mana bu reading uchun TRUE/FALSE/NOT GIVEN savollari va
javoblari, lekin bu yerda osondan qiyinga qarab qoyilmagan va tiplar
ham bor shuni true false ichiga tiplar bilan boshida orgatib
o'rganishga eng zor samarali qilib qoy agar kerak bolsa bundan ham
osonroqlarini tuzib kirish olish uchun boshlanishiga qoygin chunki
bu yerdagi hammasi real examdan olinganlar boshlanishiga qiyinroq
bolishi mumkin."

TUZILISHI. Har bir mashq 5 BOSQICH (step):

  1-bosqich  Kirish — bir gapli matn, TRUE yoki FALSE (NOT GIVEN yo'q)
  2-bosqich  NOT GIVEN nima — "yozilmagan" bilan "noto'g'ri" farqi
  3-bosqich  Sinonim va parafraz — bir xil ma'no, boshqa so'zlar
  4-bosqich  TIP qopqonlari — kitobdagi Tip 15..30 bo'yicha, har
             qoidaga 3 tadan mashq
  5-bosqich  Haqiqiy imtihon savollari (kitobdan, javob kaliti bilan)

Ya'ni o'quvchi darrov real imtihon savoliga urilmaydi: avval qoidani
o'rganadi, keyin o'sha qoidaning qopqoniga tushib ko'radi, undan
keyingina imtihon darajasiga chiqadi.

Har element `tip` yorlig'i bilan belgilangan — javobdan keyingi izohda
"qaysi qoida ishladi" ko'rsatiladi.
"""

SKILL = "ielts_reading"
TF_KIND = "read_tfng"
YN_KIND = "read_ynng"
TF_OPTS = ["TRUE", "FALSE", "NOT GIVEN"]
YN_OPTS = ["YES", "NO", "NOT GIVEN"]

STEP_TITLES = {
    1: "Kirish",
    2: "NOT GIVEN nima",
    3: "Sinonim va parafraz",
    4: "Tip qopqonlari",
    5: "Haqiqiy imtihon",
}

# =====================================================================
#  QOIDALAR (mashq boshida o'rgatiladi)
# =====================================================================
TF_TIPS = [
    ("Uchta javobning ma'nosi",
     "TRUE — matn savolni TASDIQLAYDI. FALSE — matn savolga "
     "QARAMA-QARSHI. NOT GIVEN — matnda bu haqda umuman gap yo'q. "
     "Eng ko'p xato aynan FALSE va NOT GIVEN orasida bo'ladi: "
     "\"noto'g'ri\" degani \"yozilmagan\" degani emas.",
     "Matn: The museum is closed on Mondays.\n"
     "Savol: The museum is open every day. -> FALSE\n"
     "Savol: The museum has a cafe. -> NOT GIVEN"),
    ("Tip 15 — sifatlarga qarang",
     "Otni aniqlab kelayotgan har qanday sifatni tekshiring: huge, "
     "small, cloudy, detailed. Savolda sifat almashtirilgan bo'lsa "
     "javob o'zgaradi.",
     "Matn: a huge collection -> Savol: a large exhibit = TRUE\n"
     "Matn: a small office -> Savol: a large office = FALSE"),
    ("Tip 16 — taqqoslashlar",
     "more than, bigger, the most, as ... as. Kim bilan kim "
     "taqqoslanayotganini aniqlang — ko'pincha savolda BOSHQA narsa "
     "bilan taqqoslanadi va bu NOT GIVEN bo'ladi.",
     "Matn: Train travel is more popular than ten years ago.\n"
     "Savol: Train travel is more popular than air travel. "
     "-> NOT GIVEN"),
    ("Tip 17 — ijobiy so'zlar",
     "agree, help, like, favour, approve, support, accept. Matnda "
     "ijobiy, savolda salbiy (yoki teskarisi) bo'lsa — FALSE.",
     "Matn: Local residents welcomed the new park.\n"
     "Savol: Residents objected to the park. -> FALSE"),
    ("Tip 18 — inkor qo'shimchalari",
     "de-, dis-, in-, il-, ir-, im-, mis-, non-, un-. Va inkor "
     "fe'llar: disagree, refuse, reject, deny. Bitta qo'shimcha "
     "butun gapning ma'nosini teskari qiladi.",
     "Matn: The data proved inadequate.\n"
     "Savol: The data were not sufficient. -> TRUE"),
    ("Tip 19 — o'sish va kamayish",
     "rise, grow, increase, surge / fall, drop, decline, reduce. "
     "Yo'nalish bir xilmi yoki teskarimi — shuni tekshiring.",
     "Matn: the amount has actually decreased\n"
     "Savol: technologies led to a reduction -> TRUE/YES"),
    ("Tip 20 — modal fe'llar",
     "can, could, may, might, must, should, would. \"may\" (mumkin) "
     "\"must\" (shart) emas. Kuchi oshirib yuborilgan bo'lsa — FALSE.",
     "Matn: Students may borrow up to six books.\n"
     "Savol: Students must borrow six books. -> FALSE"),
    ("Tip 21 — sonlar va umumiy/aniq",
     "a solution / a range of solutions, two types / three types. "
     "Aniq son o'zgarganmi yoki umumiy gap aniqqa aylanganmi?",
     "Matn: Two types of earthworms were used.\n"
     "Savol: There were three types. -> FALSE/NO"),
    ("Tip 22 — sabab so'zlari",
     "because, since, as, owing to, due to, thanks to, in view of. "
     "Diqqat: \"after\" (keyin) sabab EMAS — ketma-ketlik.",
     "Matn: The bridge was rebuilt after the flood.\n"
     "Savol: The flood was the reason. -> NOT GIVEN"),
    ("Tip 23 — aktiv va passiv",
     "Kim bajaryapti? Passivda bajaruvchi \"by\" dan keyin keladi. "
     "Savolda subyekt va obyekt joyi almashsa — FALSE.",
     "Matn: The committee was advised by an expert.\n"
     "Savol: The committee advised an expert. -> FALSE"),
    ("Tip 24 — mutlaq so'zlar",
     "all, none, always, never, only, every, best, worst, entirely, "
     "invariably. Bunday \"100%\" so'zlar ko'pincha gapni FALSE "
     "qiladi — matnda odatda most, some, usually turadi.",
     "Matn: The treatment is usually effective.\n"
     "Savol: The treatment is always effective. -> FALSE"),
    ("Tip 25 — bir xil so'z qopqoni",
     "Savolda matndagi so'zlar aynan takrorlangan bo'lsa — bu "
     "ko'pincha qopqon. So'z bir xil, ammo FIKR boshqa.",
     "Matn: Newton believed that for every action there is an equal "
     "and opposite reaction.\n"
     "Savol: Newton believed action and reaction are created by "
     "force. -> NOT GIVEN"),
    ("Tip 26-27 — o'z bilimingiz bilan javob bermang",
     "Gap hayotda to'g'ri bo'lishi mumkin, lekin javob FAQAT matnga "
     "ko'ra beriladi. Va aksincha: so'zma-so'z moslik shart emas — "
     "umumiy ma'no muhim.",
     "\"An electron is negatively charged\" — ilmda to'g'ri, lekin "
     "matnda yozilmagan bo'lsa NOT GIVEN."),
    ("Tip 28-29 — ortiqcha o'ylamang",
     "Uzun mantiqiy zanjir qursangiz — noto'g'ri javobga borasiz. "
     "Ma'lumotni topolmadingizmi? Demak NOT GIVEN. Uni qidirib vaqt "
     "yo'qotmang.", ""),
    ("Tip 30 — and va or",
     "\"and\" ikkalasini ham talab qiladi, \"or\" tanlov beradi. "
     "Savolda biri ikkinchisiga almashtirilgan bo'lsa — FALSE.",
     "Matn: a passport and a bank statement\n"
     "Savol: either a passport or a bank statement -> FALSE"),
    ("Agar umuman bilmasangiz",
     "all/none/only/always kabi mutlaq so'zli gap ko'pincha FALSE. "
     "mostly/often/sometimes/usually li gap ko'pincha TRUE. "
     "TRUE eng ko'p uchraydigan javob, NOT GIVEN eng kam. Lekin bu "
     "faqat vaqt tugaganda ishlatiladigan chora.", ""),
]

YN_TIPS = [
    ("TFNG bilan farqi",
     "TRUE/FALSE — FAKT haqida. YES/NO — MUALLIF FIKRI, da'vosi, "
     "qarashi haqida. Savol: \"muallif shunday deb o'ylaydimi?\" "
     "YES — ha, shunday deydi. NO — muallif teskarisini aytadi. "
     "NOT GIVEN — muallif bu haqda fikr bildirmagan.",
     "Matn: In my view, homework does more harm than good.\n"
     "Savol: The writer thinks homework is harmful. -> YES"),
    ("Fikr bildiruvchi so'zlarni qidiring",
     "I believe, in my view, clearly, sadly, fortunately, "
     "unconvincing, deserve, ought to, it would be a mistake. "
     "Muallif bahosini shu so'zlar ochib beradi.",
     "Matn: It would be a mistake to close the school.\n"
     "Savol: The writer supports closing the school. -> NO"),
    ("Fakt bor, fikr yo'q — NOT GIVEN",
     "Matn voqeani aytishi mumkin, lekin unga BAHO bermasa — "
     "muallif fikri NOT GIVEN. \"Kengash yo'lakni qurdi\" degani "
     "\"muallif buni ma'qulladi\" degani emas.",
     "Matn: The council introduced a cycling scheme last year.\n"
     "Savol: The writer believes it was successful. -> NOT GIVEN"),
    ("Modal fe'l fikrning KUCHINI ko'rsatadi",
     "perhaps / may / might — ehtimol. must / certainly — qat'iy. "
     "Muallif \"balki\" desa, savol \"albatta\" desa — bu NO.",
     "Matn: Cities should perhaps consider limiting car access.\n"
     "Savol: The writer insists cars must be banned. -> NO"),
    ("Yashirin inkor",
     "few would deny, not without its problems, I would hesitate to, "
     "unlikely, little evidence, rarely. Bular ochiq \"not\" siz "
     "inkor yoki tasdiq bildiradi — sekin o'qing.",
     "Matn: Few would deny that the internet has changed education.\n"
     "Savol: The writer accepts this. -> YES"),
    ("Qarama-qarshilik bog'lovchilari",
     "although, though, however, yet, while. Muallifning ASOSIY "
     "fikri odatda \"although\" dan KEYINGI qismda bo'ladi.",
     "Matn: Although the design is attractive, it is impractical.\n"
     "Savol: The writer thinks the design works well. -> NO"),
    ("Boshqalarning fikri muallifniki emas",
     "\"Some people argue...\", \"Critics say...\" — bu boshqalarning "
     "gapi. Muallif rozimi yoki yo'qmi — alohida qaralishi kerak.",
     "Matn: Some researchers have questioned these findings.\n"
     "Savol: The writer agrees with them. -> NOT GIVEN"),
]


# =====================================================================
#  TRUE / FALSE / NOT GIVEN
#  Har element: (matn, savol, javob, izoh, tip yorlig'i)
# =====================================================================

# --- 1-bosqich: kirish. Faqat TRUE va FALSE, bir gapli matn --------
TF1 = [
 ("The library opens at nine o'clock every morning.",
  "The library opens at nine in the morning.", "TRUE",
  "Matn aynan shuni aytyapti — vaqt bir xil.", "To'g'ridan-to'g'ri moslik"),
 ("The museum is closed on Mondays.",
  "The museum is open every day of the week.", "FALSE",
  "Dushanba yopiq — demak \"har kuni ochiq\" qarama-qarshi.",
  "Qarama-qarshilik"),
 ("Tea is the most popular drink in Britain.",
  "Tea is Britain's most popular drink.", "TRUE",
  "So'zlar tartibi o'zgargan, ma'no bir xil.", "So'z tartibi"),
 ("The school has 400 students.",
  "There are 400 students at the school.", "TRUE",
  "Son bir xil, gap qurilishi boshqacha.", "Son mos"),
 ("The bus takes twenty minutes to reach the city centre.",
  "The journey to the city centre takes half an hour.", "FALSE",
  "20 daqiqa — yarim soat (30 daqiqa) emas.", "Son mos emas"),
 ("Anna works as a nurse in a small hospital.",
  "Anna is a nurse.", "TRUE",
  "Matnda kasbi aniq aytilgan.", "To'g'ridan-to'g'ri moslik"),
 ("The park is free for everyone.",
  "Visitors must pay to enter the park.", "FALSE",
  "\"free\" — bepul. To'lash kerak degani teskari.", "Qarama-qarshilik"),
 ("The hotel has a swimming pool and a gym.",
  "The hotel has a gym.", "TRUE",
  "Ro'yxatning bir qismi so'ralgan — u bor.", "Ro'yxatdan bir qism"),
 ("The festival takes place in July every year.",
  "The festival is held annually.", "TRUE",
  "\"every year\" = \"annually\".", "Sinonim"),
 ("Only members can use the tennis courts.",
  "Anyone can use the tennis courts.", "FALSE",
  "\"only members\" — hamma emas.", "Mutlaq so'z"),
 ("The train leaves from platform three.",
  "The train departs from platform three.", "TRUE",
  "leave va depart — bir xil ma'noli fe'llar; platforma raqami "
  "ham bir xil.", "Sinonim"),
 ("The book was written in 1998.",
  "The book was written in the 1980s.", "FALSE",
  "1998 — 1990-yillar, 1980-yillar emas.", "Son mos emas"),
 ("The company employs 50 people in Manchester.",
  "The company has 50 employees in Manchester.", "TRUE",
  "employ (fe'l) = have employees.", "Sinonim"),
 ("The exhibition will run until the end of March.",
  "The exhibition finishes in March.", "TRUE",
  "\"until the end of March\" — martda tugaydi.", "Parafraz"),
 ("Photography is not allowed inside the gallery.",
  "Visitors may take photographs in the gallery.", "FALSE",
  "Ta'qiqlangan — ruxsat bor degani teskari.", "Inkor"),
 ("The course lasts six weeks and costs 120 pounds.",
  "The course costs 120 pounds.", "TRUE",
  "Matnda ikki ma'lumot bor (muddat va narx) — savol faqat "
  "narxni so'rayapti, u aynan mos.", "To'g'ridan-to'g'ri moslik"),
 ("Children under five travel free.",
  "Children under five must buy a ticket.", "FALSE",
  "Bepul — chipta sotib olish shart emas.", "Qarama-qarshilik"),
 ("The restaurant serves breakfast from seven to eleven.",
  "Breakfast is served in the morning.", "TRUE",
  "7:00-11:00 — ertalabki vaqt.", "Umumlashtirish"),
 ("All rooms have air conditioning.",
  "Every room is air conditioned.", "TRUE",
  "all rooms = every room — ikkalasi ham istisnosiz hamma xonani "
  "bildiradi.", "Sinonim"),
 ("The shop closes early on Sundays.",
  "The shop stays open late on Sundays.", "FALSE",
  "Erta yopiladi — kech ochiq turmaydi.", "Qarama-qarshilik"),
]

# --- 2-bosqich: NOT GIVEN tushunchasi -----------------------------
TF2 = [
 ("The museum has a large collection of Roman coins.",
  "The museum charges an entrance fee.", "NOT GIVEN",
  "Matnda tanga to'plami haqida. Kirish haqi haqida BIR OG'IZ ham "
  "gap yo'q — demak NOT GIVEN.", "Mavzu umuman aytilmagan"),
 ("Sara moved to London in 2015 to study medicine.",
  "Sara moved to London in 2015.", "TRUE",
  "Sana aynan mos. Matndagi qo'shimcha ma'lumot (tibbiyot "
  "o'qishi) javobga xalaqit bermaydi.", "To'g'ridan-to'g'ri moslik"),
 ("Sara moved to London in 2015 to study medicine.",
  "Sara enjoyed living in London.", "NOT GIVEN",
  "Yoqdi-yoqmadi — matnda his-tuyg'u haqida hech narsa yo'q.",
  "His-tuyg'u aytilmagan"),
 ("The hotel has 60 rooms and a small restaurant.",
  "The hotel restaurant is popular with local people.", "NOT GIVEN",
  "Restoran bor, ammo mashhurligi haqida gap yo'q.",
  "Qo'shimcha baho aytilmagan"),
 ("The city built a new bridge in 2019.",
  "The bridge was the most expensive project of the year.",
  "NOT GIVEN",
  "Narx yoki taqqoslash haqida hech nima yozilmagan.",
  "Taqqoslash aytilmagan"),
 ("The report was published in June and runs to 200 pages.",
  "The report is 200 pages long.", "TRUE",
  "Sahifa soni aynan berilgan.", "To'g'ridan-to'g'ri moslik"),
 ("Many students take a part-time job during their studies.",
  "Part-time work improves students' grades.", "NOT GIVEN",
  "Ish bor — lekin bahoga ta'siri haqida gap yo'q.",
  "Sabab-oqibat aytilmagan"),
 ("The factory produces 2,000 bicycles a month.",
  "The factory exports bicycles to Europe.", "NOT GIVEN",
  "Ishlab chiqarish aytilgan, eksport aytilmagan.",
  "Mavzu umuman aytilmagan"),
 ("Coffee was first grown in Ethiopia.",
  "Coffee was first grown in Brazil.", "FALSE",
  "Matn boshqa mamlakatni aytadi — qarama-qarshi.",
  "Qarama-qarshilik"),
 ("Coffee was first grown in Ethiopia.",
  "Coffee is Ethiopia's main export.", "NOT GIVEN",
  "Efiopiya aytilgan, lekin eksport haqida gap yo'q. Bir so'z "
  "uchraganiga aldanmang.", "Bir xil so'z qopqoni"),
 ("The team won the championship three times.",
  "The team has never won the championship.", "FALSE",
  "Uch marta yutgan — hech qachon yutmagan degani teskari.",
  "Qarama-qarshilik"),
 ("The team won the championship three times.",
  "The team's coach was replaced last season.", "NOT GIVEN",
  "Murabbiy haqida umuman gap yo'q.", "Mavzu umuman aytilmagan"),
 ("Rain is common in this region in autumn.",
  "It rains often in this region in autumn.", "TRUE",
  "common (odatiy) va often (tez-tez) — bu kontekstda bir xil "
  "ma'noni beradi.", "Sinonim"),
 ("Rain is common in this region in autumn.",
  "Farmers welcome the autumn rain.", "NOT GIVEN",
  "Dehqonlar haqida hech narsa yozilmagan.",
  "Mavzu umuman aytilmagan"),
 ("The novel was translated into twelve languages.",
  "The novel appeared in more than ten languages.", "TRUE",
  "12 > 10 — matn tasdiqlaydi.", "Son mantiqi"),
 ("The novel was translated into twelve languages.",
  "The novel was made into a film.", "NOT GIVEN",
  "Kino haqida gap yo'q.", "Mavzu umuman aytilmagan"),
 ("The conference will be held in Vienna.",
  "The conference will be held in Vienna for the first time.",
  "NOT GIVEN",
  "Joy to'g'ri, lekin \"birinchi marta\"ligi aytilmagan. Qo'shimcha "
  "ma'lumot — qo'shimcha tekshiruv.", "Qo'shimcha shart"),
 ("Electric cars are becoming cheaper.",
  "Electric cars are becoming more expensive.", "FALSE",
  "Yo'nalish teskari.", "O'sish/kamayish"),
 ("Electric cars are becoming cheaper.",
  "Most drivers now prefer electric cars.", "NOT GIVEN",
  "Haydovchilar tanlovi haqida gap yo'q.",
  "Mavzu umuman aytilmagan"),
 ("The building was designed by a Spanish architect.",
  "The architect who designed the building was from Spain.", "TRUE",
  "Passivdan aktivga aylantirilgan, ma'no bir xil.",
  "Aktiv/passiv"),
]

# --- 3-bosqich: sinonim va parafraz -------------------------------
TF3 = [
 ("Almost all of the workers arrive by bicycle.",
  "Nearly every employee cycles to work.", "TRUE",
  "almost all = nearly every, workers = employees, arrive by bicycle "
  "= cycle.", "Parafraz"),
 ("The plan was rejected by the council.",
  "The council turned down the plan.", "TRUE",
  "reject = turn down; passivdan aktivga.", "Parafraz"),
 ("The illness spreads quickly in crowded places.",
  "The disease is transmitted rapidly where many people gather.",
  "TRUE", "illness=disease, spreads=transmitted, quickly=rapidly.",
  "Parafraz"),
 ("Fewer people are reading printed newspapers.",
  "The number of printed newspaper readers is falling.", "TRUE",
  "fewer = falling number.", "O'sish/kamayish"),
 ("The scheme was abandoned after two years.",
  "The scheme continued for more than a decade.", "FALSE",
  "2 yil — 10 yildan ko'p emas.", "Son mos emas"),
 ("Scientists remain uncertain about the cause.",
  "Scientists have identified the cause.", "FALSE",
  "uncertain — hali aniqlanmagan.", "Qarama-qarshilik"),
 ("The technique was invented by a Japanese engineer.",
  "A Japanese engineer developed the technique.", "TRUE",
  "invent = develop; passiv -> aktiv.", "Aktiv/passiv"),
 ("Sales fell slightly in the first quarter.",
  "Sales dropped a little at the start of the year.", "TRUE",
  "fell=dropped, slightly=a little, first quarter=start of year.",
  "Parafraz"),
 ("Attendance has doubled since the museum was renovated.",
  "Twice as many people visit the museum as before the renovation.",
  "TRUE", "doubled = twice as many.", "Son mantiqi"),
 ("The medicine relieves the symptoms but does not cure the illness.",
  "The medicine cures the illness.", "FALSE",
  "\"does not cure\" aniq yozilgan.", "Inkor"),
 ("The species is found only on two small islands.",
  "The species lives on just two small islands.", "TRUE",
  "only = just, found = lives.", "Parafraz"),
 ("The tower is one of the tallest structures in the country.",
  "The tower is the tallest structure in the country.", "NOT GIVEN",
  "\"eng balandlaridan biri\" — \"eng balandi\" degani emas. "
  "Umumiy gapni aniq gapga aylantirib bo'lmaydi.",
  "Umumiy/aniq"),
 ("The programme is aimed at children aged 6 to 12.",
  "The programme is designed for young children.", "TRUE",
  "6-12 yosh — yosh bolalar.", "Umumlashtirish"),
 ("Very few students dropped out of the course.",
  "Hardly any students left the course before it ended.", "TRUE",
  "very few = hardly any.", "Parafraz"),
 ("The report criticises the government's housing policy.",
  "The report praises the government's housing policy.", "FALSE",
  "criticise va praise — teskari.", "Ijobiy/salbiy"),
 ("The material is light but extremely strong.",
  "Despite its low weight, the material is very strong.", "TRUE",
  "but = despite; light = low weight.", "Parafraz"),
 ("Prices are expected to remain stable next year.",
  "Prices are expected to rise sharply next year.", "FALSE",
  "stable — o'zgarmaydi, ko'tarilmaydi.", "O'sish/kamayish"),
 ("The library is used mainly by postgraduate students.",
  "Postgraduate students are the library's main users.", "TRUE",
  "Bir gapning ikki xil qurilishi.", "So'z tartibi"),
 ("Most of the equipment was donated by local businesses.",
  "Local businesses gave most of the equipment.", "TRUE",
  "donate = give; passiv -> aktiv.", "Aktiv/passiv"),
 ("The road was closed for repairs for three days.",
  "Repairs to the road took less than a week.", "TRUE",
  "Yo'l 3 kun yopilgan, bir hafta esa 7 kun — demak bir haftadan "
  "kam.", "Son mantiqi"),
]

# --- 4-bosqich: TIP qopqonlari (har qoidaga 3 tadan) --------------
TF4 = [
 # Tip 15 — sifatlar
 ("The company opened a small office in Berlin.",
  "The company opened a large office in Berlin.", "FALSE",
  "TIP 15. Sifat almashtirilgan: small -> large. Ot bir xil bo'lsa "
  "ham javob teskari.", "Tip 15 — sifat"),
 ("Researchers made a surprising discovery about ancient bees.",
  "Researchers made a discovery about ancient bees.", "TRUE",
  "TIP 15. Bu yerda sifat (surprising) faqat QO'SHIMCHA — u tushib "
  "qolsa ham ma'no buzilmaydi.", "Tip 15 — sifat"),
 ("The team produced a detailed map of the seabed.",
  "The team produced a rough sketch of the seabed.", "FALSE",
  "TIP 15. detailed map va rough sketch — bir-biriga zid ta'rif.",
  "Tip 15 — sifat"),
 # Tip 16 — taqqoslash
 ("Wind power is cheaper than nuclear power in this region.",
  "Nuclear power costs more than wind power in this region.", "TRUE",
  "TIP 16. Taqqoslash teskari qilib yozilgan, lekin ma'no aynan bir "
  "xil.", "Tip 16 — taqqoslash"),
 ("The southern branch is busier than the northern one.",
  "The northern branch is the busiest of the two.", "FALSE",
  "TIP 16. Matnda janubiy bandroq — savol teskarisini aytyapti.",
  "Tip 16 — taqqoslash"),
 ("Train travel is more popular than it was ten years ago.",
  "Train travel is more popular than air travel.", "NOT GIVEN",
  "TIP 16. Matn poyezdni O'TMISHDAGI o'zi bilan taqqoslaydi, "
  "samolyot bilan emas. Boshqa taqqoslash — NOT GIVEN.",
  "Tip 16 — taqqoslash"),
 # Tip 17 — ijobiy so'zlar
 ("The council approved the plan without discussion.",
  "The council supported the plan.", "TRUE",
  "TIP 17. approve — ijobiy so'z, support bilan bir ma'noda.",
  "Tip 17 — ijobiy so'z"),
 ("Local residents welcomed the new park.",
  "Local residents objected to the new park.", "FALSE",
  "TIP 17. welcome (ijobiy) va object (salbiy) — teskari.",
  "Tip 17 — ijobiy so'z"),
 ("The critics found the film watchable but forgettable.",
  "The critics thought the film was outstanding.", "FALSE",
  "TIP 17. \"watchable but forgettable\" — kuchsiz baho, "
  "\"outstanding\" esa yuqori maqtov.", "Tip 17 — ijobiy so'z"),
 # Tip 18 — inkor qo'shimchalari
 ("The data proved inadequate for a firm conclusion.",
  "The data were not sufficient for a firm conclusion.", "TRUE",
  "TIP 18. in- qo'shimchasi: inadequate = not sufficient.",
  "Tip 18 — inkor qo'shimcha"),
 ("The author denies that the letters are genuine.",
  "The author believes the letters are genuine.", "FALSE",
  "TIP 18. deny — inkor qiluvchi fe'l, believe bilan teskari.",
  "Tip 18 — inkor qo'shimcha"),
 ("The results were irregular and hard to interpret.",
  "The results followed a regular pattern.", "FALSE",
  "TIP 18. ir- qo'shimchasi: irregular = regular emas.",
  "Tip 18 — inkor qo'shimcha"),
 # Tip 19 — o'sish/kamayish
 ("Since 2010 the number of visitors has fallen steadily.",
  "Visitor numbers have declined since 2010.", "TRUE",
  "TIP 19. fallen = declined — yo'nalish bir xil.",
  "Tip 19 — o'sish/kamayish"),
 ("Output rose sharply after the new machines were installed.",
  "Production dropped after the new machines were installed.",
  "FALSE", "TIP 19. rose va dropped — teskari yo'nalish.",
  "Tip 19 — o'sish/kamayish"),
 ("The population of the town has remained unchanged for a decade.",
  "The town's population has grown over the last ten years.",
  "FALSE", "TIP 19. unchanged — o'smagan ham, kamaymagan ham.",
  "Tip 19 — o'sish/kamayish"),
 # Tip 20 — modal fe'llar
 ("Students may borrow up to six books at a time.",
  "Students must borrow six books at a time.", "FALSE",
  "TIP 20. may (ruxsat) va must (majburiyat) — boshqa kuch. "
  "Ustiga \"up to six\" ham \"exactly six\" emas.",
  "Tip 20 — modal fe'l"),
 ("Heavy rain could delay the harvest.",
  "Heavy rain will certainly delay the harvest.", "FALSE",
  "TIP 20. could (ehtimol) — will certainly (aniq) emas.",
  "Tip 20 — modal fe'l"),
 ("Visitors should book a place in advance.",
  "Visitors are advised to book in advance.", "TRUE",
  "TIP 20. should = tavsiya = are advised.", "Tip 20 — modal fe'l"),
 # Tip 21 — sonlar, umumiy/aniq
 ("The researchers tested a range of solutions.",
  "The researchers tested a single solution.", "FALSE",
  "TIP 21. \"a range of\" — bir nechta; \"a single\" — bitta.",
  "Tip 21 — son/umumiy"),
 ("Three of the five machines were replaced.",
  "All the machines were replaced.", "FALSE",
  "TIP 21. 5 tadan 3 tasi — hammasi emas.", "Tip 21 — son/umumiy"),
 ("The survey covered more than 2,000 households.",
  "Over two thousand households took part in the survey.", "TRUE",
  "TIP 21. more than 2,000 = over two thousand.",
  "Tip 21 — son/umumiy"),
 # Tip 22 — sabab so'zlari
 ("Owing to the storm, the ferry service was suspended.",
  "The ferry service stopped because of the storm.", "TRUE",
  "TIP 22. owing to = because of — sabab bir xil.",
  "Tip 22 — sabab"),
 ("The shop closed, although trade had been good.",
  "The shop closed because trade was poor.", "FALSE",
  "TIP 22. although — savdo YAXSHI edi. Savol sababni teskari "
  "qilib qo'ygan.", "Tip 22 — sabab"),
 ("The bridge was rebuilt after the flood.",
  "The flood was the reason the bridge was rebuilt.", "NOT GIVEN",
  "TIP 22. \"after\" — vaqt ketma-ketligi, SABAB emas. Sabab "
  "yozilmagan.", "Tip 22 — sabab"),
 # Tip 23 — aktiv/passiv
 ("The vaccine was developed by a team in Oxford.",
  "A team in Oxford developed the vaccine.", "TRUE",
  "TIP 23. Passivdan aktivga — bajaruvchi o'sha-o'sha.",
  "Tip 23 — aktiv/passiv"),
 ("The letters were destroyed by the family.",
  "The family destroyed the letters.", "TRUE",
  "TIP 23. by + bajaruvchi = aktivdagi ega.",
  "Tip 23 — aktiv/passiv"),
 ("The committee was advised by an outside expert.",
  "The committee advised an outside expert.", "FALSE",
  "TIP 23. Ega va to'ldiruvchi joyi almashib ketgan — kim kimga "
  "maslahat berdi?", "Tip 23 — aktiv/passiv"),
 # Tip 24 — mutlaq so'zlar
 ("Many birds in the area migrate in winter.",
  "Every bird in the area migrates in winter.", "FALSE",
  "TIP 24. many (ko'p) — every (hammasi) emas.",
  "Tip 24 — mutlaq so'z"),
 ("The treatment is usually effective.",
  "The treatment is always effective.", "FALSE",
  "TIP 24. usually — always emas. \"100%\" so'zdan ehtiyot bo'ling.",
  "Tip 24 — mutlaq so'z"),
 ("Some of the caves have never been explored.",
  "None of the caves has been explored.", "FALSE",
  "TIP 24. ba'zilari o'rganilmagan — demak boshqalari o'rganilgan.",
  "Tip 24 — mutlaq so'z"),
 # Tip 25 — bir xil so'z qopqoni
 ("The museum keeps its oldest manuscripts in a locked room.",
  "The museum's oldest manuscripts are the most valuable items it "
  "owns.", "NOT GIVEN",
  "TIP 25. \"oldest manuscripts\" aynan takrorlangan — shu sizni "
  "aldaydi. Qimmatbaholigi haqida gap yo'q.",
  "Tip 25 — bir xil so'z"),
 ("The factory uses solar panels to heat its water.",
  "The factory sells solar panels.", "NOT GIVEN",
  "TIP 25. \"solar panels\" bor, lekin sotish haqida emas — "
  "ishlatish haqida.", "Tip 25 — bir xil so'z"),
 ("The report mentions climate change several times.",
  "The report concludes that climate change is the main cause.",
  "NOT GIVEN",
  "TIP 25. Eslatib o'tish (mention) — xulosa chiqarish emas.",
  "Tip 25 — bir xil so'z"),
 # Tip 30 — and / or
 ("Applicants must provide a passport and a bank statement.",
  "Applicants must provide either a passport or a bank statement.",
  "FALSE", "TIP 30. and — ikkalasi ham shart; or — tanlov.",
  "Tip 30 — and/or"),
 ("Tickets can be bought online or at the door.",
  "Tickets can be bought at the door.", "TRUE",
  "TIP 30. or — ikki yo'lning ikkisi ham mumkin.",
  "Tip 30 — and/or"),
 ("The room includes a desk and a wardrobe.",
  "The room includes a desk.", "TRUE",
  "TIP 30. and bilan berilgan ro'yxatning bir qismi — bor.",
  "Tip 30 — and/or"),
]

# --- 5-bosqich: HAQIQIY IMTIHON savollari (kitob + javob kaliti) ---
#     Oxirgi element — qiyinlik (1 oson ... 3 qiyin), shu bo'yicha
#     saralanadi.
TF5 = [
 ("The majority of consumers prefer imported cars.",
  "Foreign cars are preferred by most customers.", "TRUE",
  "imported = foreign, majority = most, consumers = customers. "
  "Aktivdan passivga o'tgan, ma'no bir xil.",
  "Tip 23 — aktiv/passiv", 1),
 ("Niagara Falls is viewed by thousands of tourists every year.",
  "Each year, thousands of people visit Niagara Falls.", "TRUE",
  "Passivdan aktivga; view = visit, every year = each year.",
  "Tip 23 — aktiv/passiv", 1),
 ("The museum has a huge collection of African art.",
  "There is a large exhibit of African art at the museum.", "TRUE",
  "huge = large, collection = exhibit.", "Tip 15 — sifat", 1),
 ("She angered me with her inappropriate comments, rumor-spreading, "
  "and disrespectfulness at the formal dinner table.",
  "Her impoliteness, gossiping, and general lack of respect at "
  "dinner infuriated me.", "TRUE",
  "Uchta so'z ham parafraz: inappropriate comments = impoliteness, "
  "rumor-spreading = gossiping, disrespectfulness = lack of "
  "respect, angered = infuriated.", "Parafraz", 1),
 ("Physical exercise helps control insulin levels, while ingesting "
  "fat combined with sugars and starches can cause surges in "
  "insulin levels.",
  "Insulin levels rise sharply when foods with high levels of "
  "starch, sugar and fat are eaten.", "TRUE",
  "surge = rise sharply.", "Tip 19 — o'sish/kamayish", 1),
 ("Most websites are intended to amuse visitors with quality "
  "information.",
  "All website are designed to be entertaining.", "FALSE",
  "TIP 24. Most -> All. Mutlaq so'z gapni noto'g'ri qiladi.",
  "Tip 24 — mutlaq so'z", 1),
 ("Acupuncture is a good way to manage many pain conditions "
  "related to arthritis, joints and tendinitis.",
  "Acupuncture is used to alleviate pain and to treat all various "
  "physical conditions.", "FALSE",
  "TIP 24. many -> all. Matn faqat ba'zi holatlarni aytadi.",
  "Tip 24 — mutlaq so'z", 1),
 ("The middle of a glacier moves faster than the sides and bottom "
  "because there is no rock to cause friction.",
  "All parts of the glacier move at the same speed.", "FALSE",
  "TIP 16 + 24. O'rtasi tezroq — demak tezlik bir xil emas.",
  "Tip 16 — taqqoslash", 1),
 ("Australians believe that life should have a balance between "
  "work and leisure time. As a consequence, some students may be "
  "critical of others who they perceive as doing nothing but study.",
  "Students who study all the time may receive positive comments "
  "from their colleagues.", "FALSE",
  "TIP 17. critical (salbiy) -> positive comments (ijobiy) — "
  "teskari.", "Tip 17 — ijobiy so'z", 2),
 ("Habitation in outer space in huge stations is no longer just a "
  "dream, but a reality; the development of space hotels is not "
  "far-off.",
  "The concept of the habitation of outer space by mankind is "
  "unimaginable.", "FALSE",
  "TIP 18. Matn \"reallik\" deydi, savol \"tasavvur qilib "
  "bo'lmaydi\" deydi.", "Tip 18 — inkor qo'shimcha", 2),
 ("Australian notions of privacy mean that areas such as financial "
  "matters, appearance and relationships are only discussed with "
  "close friends. While people may volunteer such information, "
  "they may resent someone actually asking them unless the "
  "friendship is firmly established. Even then, it is considered "
  "very impolite to ask someone what they earn.",
  "It is acceptable to discuss financial issues with people you do "
  "not know well.", "FALSE",
  "TIP 17 + 24. only with close friends; very impolite — demak "
  "notanish odam bilan maqbul emas.", "Tip 24 — mutlaq so'z", 2),
 ("But most modern humour theorists have settled on some version "
  "of Aristotle's belief that jokes are based on a reaction to or "
  "resolution of incongruity.",
  "Current thinking on humour has largely ignored Aristotle's view "
  "on the subject.", "FALSE",
  "\"settled on Aristotle's belief\" — e'tibordan chetda "
  "qoldirilmagan, aksincha qabul qilingan.", "Qarama-qarshilik", 2),
 ("More than most other hobbies, collecting can be totally "
  "engrossing, and can give a strong sense of personal fulfilment.",
  "Collecting gives a feeling that other hobbies are unlikely to "
  "inspire.", "TRUE",
  "TIP 16. \"More than most other hobbies\" — boshqa mashg'ulotlar "
  "bunday tuyg'u bermaydi.", "Tip 16 — taqqoslash", 2),
 ("Massive floods, long droughts, hurricanes and severe monsoons "
  "take their toll each year, destroying millions of tons of "
  "valuable crops.",
  "Some damage to food crops is caused by climate change.", "TRUE",
  "Sanab o'tilgan ofatlar — iqlim hodisalari; ular hosilni "
  "yo'q qiladi.", "Umumlashtirish", 2),
 ("Because of problems of definition, which directly affect "
  "statistical measurement, it is not possible with any degree of "
  "certainty to provide precise, valid or reliable data about the "
  "extent of world-wide tourism participation or its economic "
  "impact.",
  "It is easy to show statistically how tourism affects individual "
  "economies.", "FALSE",
  "\"not possible ... precise data\" — oson emas, aksincha "
  "imkonsiz.", "Tip 18 — inkor qo'shimcha", 2),
 ("We may disagree with the 'general', for we doubt if all "
  "musicians of genius could have become scientists of genius or "
  "vice versa.",
  "A true genius has general powers capable of excellence in any "
  "area.", "FALSE",
  "Muallif aynan shu fikrga qo'shilmasligini aytyapti (disagree, "
  "doubt).", "Tip 18 — inkor qo'shimcha", 2),
 ("Understanding how consumers make decisions, and the crucial "
  "role of packaging in this process, has been a neglected area of "
  "research so far.",
  "Little research has been done on the link between packaging and "
  "consumers choosing a product.", "TRUE",
  "neglected area of research = little research.", "Parafraz", 2),
 ("Home-schooling is a controversial issue surrounded by "
  "misgivings, with supporters emphasizing its benefits and "
  "detractors pointing to its limitations and risks.",
  "There is much disagreement about the merits of home-schooling.",
  "TRUE",
  "controversial + supporters/detractors = katta kelishmovchilik.",
  "Parafraz", 2),
 ("Inside an igloo, the temperature may range from minus 7 degrees "
  "Celsius to 16 degrees Celsius when warmed by body heat alone.",
  "Although relatively warm, the temperature inside an igloo in "
  "winter Arctic conditions will never rise above freezing.",
  "FALSE",
  "TIP 24. 16 daraja — muzlash nuqtasidan ancha yuqori, demak "
  "\"never rise above freezing\" noto'g'ri.",
  "Tip 24 — mutlaq so'z", 2),
 ("City problems thought to be caused mostly by weak and "
  "unrepresentative city governments.",
  "Problems in very large cities are mostly due to poor "
  "administration.", "TRUE",
  "weak governments = poor administration; mostly ikkalasida ham "
  "bor.", "Tip 22 — sabab", 2),
 ("The extra work required to cultivate Cripps Pink trees is "
  "offset by its advantages, which include: vigorous trees; fruit "
  "that has tolerance to sunburn; a thin skin that does not crack.",
  "One advantage of Cripps Pink trees is that they grow well.",
  "TRUE", "\"vigorous trees\" — kuchli o'sadi, ro'yxatdagi "
  "afzallik.", "Ro'yxatdan bir qism", 2),
 ("A fingerprint is the arrangement of skin ridges and furrows on "
  "the tips of the fingers. This ridged skin develops fully during "
  "foetal development, as the skin cells grow in the mother's womb.",
  "The ridges and patterns that make up fingerprints develop "
  "before birth.", "TRUE",
  "foetal development / in the womb = tug'ilishdan oldin.",
  "Parafraz", 2),
 ("Indeed, while there are an estimated 400 million bicycles in "
  "China, where it has long been the preferred form of transport, "
  "rapid economic growth has fuelled an explosive expansion in car "
  "ownership.",
  "In China, latest economic recession has enabled many people to "
  "own a car.", "FALSE",
  "TIP 19. Matnda O'SISH (growth), savolda TANAZZUL (recession).",
  "Tip 19 — o'sish/kamayish", 2),
 ("'The escalating cost of higher education is causing many to "
  "question the value of continuing education beyond high school'.",
  "The cost of a college education has remained steady for several "
  "years.", "FALSE",
  "TIP 19. escalating — ko'tarilyapti, barqaror emas.",
  "Tip 19 — o'sish/kamayish", 2),
 ("The bark of the cork oak has a particular cellular structure - "
  "with about 40 million cells per cubic centimetre - that "
  "technology has never succeeded in replicating.",
  "Scientists have developed a synthetic cork with the same "
  "cellular structure as natural cork.", "FALSE",
  "\"never succeeded\" — sun'iy nusxa yaratilmagan.",
  "Tip 18 — inkor qo'shimcha", 2),
 ("Recent discoveries offer some evidence that black holes have a "
  "dramatic influence on things around them, emitting powerful "
  "gamma ray bursts, absorbing nearby stars, and both stimulating "
  "and hindering the growth of new stars.",
  "Black holes can actually help the creation of new stars.",
  "TRUE", "\"stimulating ... the growth of new stars\" = yordam "
  "beradi. \"both ... and\" ikkalasini ham bildiradi.",
  "Tip 30 — and/or", 2),
 ("Cork harvesting is a very specialised profession. No mechanical "
  "means of stripping cork bark has been invented, so the job is "
  "done by teams of highly skilled workers.",
  "The only way to remove the bark from cork oak trees is by hand.",
  "TRUE", "Mexanik usul yo'q + ishni ishchilar qiladi = yagona yo'l "
  "qo'lda.", "Tip 22 — sabab", 2),
 ("Kant and Freud felt that joke-telling relies on building up a "
  "psychic tension which is safely punctured by the ludicrousness "
  "of the punchline.",
  "Kant believed that a successful joke involves the controlled "
  "release of nervous energy.", "TRUE",
  "psychic tension safely punctured = asabiy kuchlanishning "
  "nazorat ostida chiqishi.", "Parafraz", 2),
 ("Graeme Ritchie, a computational linguist in Edinburgh, studies "
  "the linguistic structure of jokes in order to understand not "
  "only humour but language understanding and reasoning in "
  "machines.",
  "Graeme Ritchie's work links jokes to artificial intelligence.",
  "TRUE", "\"reasoning in machines\" = sun'iy intellekt.",
  "Parafraz", 2),
 ("Play is a crucial part of development in most young mammals. "
  "Rats produce ultrasonic squeaks to prevent their scuffles "
  "turning nasty. Chimpanzees have a 'play-face' - a gaping "
  "expression accompanied by a panting 'ah, ah' noise.",
  "Chimpanzees make particular noises when they are playing.",
  "TRUE", "panting 'ah, ah' noise = maxsus tovush.", "Parafraz", 2),
 ("The pyramid builders could have used kites to lift massive "
  "stones into place.",
  "The team decided that it was possible to use kites to raise very "
  "heavy stones.", "TRUE",
  "TIP 20. could have used = mumkin edi = imkoniyat bor.",
  "Tip 20 — modal fe'l", 2),
 ("If the bark is stripped on a day when it's too cold - or when "
  "the air is damp - the tree will be damaged.",
  "Cork bark should be stripped in dry atmospheric conditions.",
  "TRUE", "Nam havo zarar qiladi — demak quruq havo kerak.",
  "Tip 18 — inkor qo'shimcha", 2),
 ("The pyramids of Egypt were built more than three thousand years "
  "ago, and no one knows how. The conventional picture is that "
  "tens of thousands of slaves dragged stones on sledges.",
  "It is generally believed that large numbers of people were "
  "needed to build the pyramids.", "TRUE",
  "conventional picture = umumiy qabul qilingan qarash; tens of "
  "thousands = ko'p odam.", "Parafraz", 2),
 ("Despite popular belief that sleep is one long event, research "
  "shows that, in an average night, there are five stages of sleep "
  "and four cycles, during which the sequence of stages is "
  "repeated.",
  "The various stages of sleep occur more than once a night.",
  "TRUE", "To'rt tsikl — bosqichlar takrorlanadi.",
  "Tip 21 — son/umumiy", 2),
 ("As president, he organised the purchase of a vast tract of land "
  "from the French, who were embattled in Europe and strapped for "
  "cash. This land, called the Louisiana Territory, doubled the "
  "size of America.",
  "During Jefferson's presidency, the French bought some American "
  "land, greatly reducing the size of the country.", "FALSE",
  "TIP 23. Kim kimdan sotib oldi? Amerika fransuzlardan sotib "
  "olgan va hudud IKKI BARAVAR OSHGAN.",
  "Tip 23 — aktiv/passiv", 2),
 ("It's highly likely that you'll see one of the major soft drink "
  "companies represented.",
  "Certain brands of soft drinks can be seen in many movies.",
  "TRUE", "highly likely = ko'p uchraydi.", "Tip 20 — modal fe'l",
  2),
 ("As less energy is needed to melt recycled glass than to melt "
  "down raw materials, this also saves fuel and production costs.",
  "It is more expensive to produce recycled glass than to "
  "manufacture new glass.", "FALSE",
  "TIP 16. Matn arzonroq deydi — savol qimmatroq deydi.",
  "Tip 16 — taqqoslash", 2),
 ("In a normal electrical system, customers are supplied with a "
  "steady electrical current. This steady electrical supply is "
  "subject to minimal variations - variations that are "
  "imperceptible to the consumer and do not normally harm "
  "electrical devices.",
  "All variations in electrical voltage are potentially damaging, "
  "and must be prevented.", "FALSE",
  "TIP 24. Kichik o'zgarishlar zarar qilmaydi — \"all\" noto'g'ri.",
  "Tip 24 — mutlaq so'z", 2),
 ("Newton believed that for every action there is an equal and "
  "opposite reaction.",
  "Newton believed that action and reaction are created by force.",
  "NOT GIVEN",
  "TIP 25. So'zlar (action, reaction, believed) aynan bir xil — "
  "shu aldaydi. \"Kuch ularni YARATADI\" degan fikr matnda yo'q.",
  "Tip 25 — bir xil so'z", 3),
 ("The ancestors of the Inuit people of Greenland are thought to "
  "have lived in Siberia until 7,000 or 8,000 years ago. There is "
  "evidence that they then travelled by boat into Alaska. From "
  "there, some migrated to Greenland around 5,000 years ago, and "
  "evidence has been found of their existence around the northern "
  "tip of the island.",
  "The north of Greenland was the most attractive area of the "
  "island for the earliest settlers.", "NOT GIVEN",
  "TIP 25. Shimolda yashagani aytilgan, ammo \"eng jozibali joy\" "
  "degan BAHO yo'q.", "Tip 25 — bir xil so'z", 3),
 ("Tourism has a profound impact both on the world economy, and "
  "because of the educative effect of travel and the effects on "
  "employment, on society itself.",
  "Tourism has a social impact because it promotes recreation.",
  "NOT GIVEN",
  "TIP 22. Ijtimoiy ta'sir bor, lekin SABAB boshqa (ta'lim va "
  "bandlik). \"Dam olishni rag'batlantiradi\" deyilmagan.",
  "Tip 22 — sabab", 3),
 ("Laughter has always struck people as deeply mysterious, perhaps "
  "pointless. The writer Arthur Koestler dubbed it the luxury "
  "reflex: 'unique in that it serves no apparent biological "
  "purpose'.",
  "Arthur Koestler considered laughter biologically important in "
  "several ways.", "FALSE",
  "\"no apparent biological purpose\" — aynan teskari.",
  "Tip 18 — inkor qo'shimcha", 3),
 ("Plato expressed the idea that humour is simply a delighted "
  "feeling of superiority over others.",
  "Plato believed humour to be a sign of above-average "
  "intelligence.", "NOT GIVEN",
  "TIP 25. superiority (ustunlik hissi) — intellekt haqida emas.",
  "Tip 25 — bir xil so'z", 3),
 ("A comedian will present a situation followed by an unexpected "
  "interpretation that is also apt.",
  "Most comedians use personal situations as a source of humour.",
  "NOT GIVEN",
  "TIP 25. \"situation\" so'zi bor, lekin SHAXSIY vaziyat haqida "
  "gap yo'q.", "Tip 25 — bir xil so'z", 3),
 ("Cork - the thick bark of the cork oak tree (Quercus suber) - is "
  "a remarkable material. It is tough, elastic, buoyant, and "
  "fire-resistant, and suitable for a wide range of purposes.",
  "The cork oak has the thickest bark of any living tree.",
  "NOT GIVEN",
  "TIP 16 + 25. \"thick\" bor, lekin BOSHQA daraxtlar bilan "
  "taqqoslanmagan.", "Tip 16 — taqqoslash", 3),
 ("Sometimes, a gift of the product isn't an appropriate form of "
  "compensation, so money powers the deal. Someone from a "
  "manufacture's marketing team hears about a movie project, and "
  "approaches the set dresser with a financially attractive "
  "proposal.",
  "Film makers would rather be paid than receive goods.",
  "NOT GIVEN",
  "TIP 16. Ba'zan pul ishlatiladi deyilgan, lekin kinochilar "
  "qaysinisini AFZAL ko'rishi aytilmagan.",
  "Tip 16 — taqqoslash", 3),
 ("Global warming is the gradual heating of Earth's surface, "
  "oceans and atmosphere. Earth's average temperature has risen by "
  "1.4 degrees Fahrenheit over the past century, according to the "
  "Environmental Protection Agency (EPA).",
  "The consumption of fossil fuels in last few decades has "
  "contributed much to the degradation of our environment.",
  "NOT GIVEN",
  "TIP 26. Bu hayotda to'g'ri bo'lishi mumkin, ammo matnda "
  "yoqilg'i haqida bir og'iz ham gap yo'q. O'z bilimingiz bilan "
  "javob bermang.", "Tip 26 — o'z bilimi", 3),
 ("Recently, some people have become richer both in developed "
  "countries and developing countries because of the economic "
  "growth.",
  "People are concerned that economic problems may increase the "
  "gap between developed and developing countries.", "NOT GIVEN",
  "TIP 25. Bir xil so'zlar (developed/developing) bor, lekin "
  "\"tashvish\" va \"tafovut\" haqida gap yo'q.",
  "Tip 25 — bir xil so'z", 3),
]


# =====================================================================
#  YES / NO / NOT GIVEN — muallif fikri
# =====================================================================

# --- 1-bosqich: muallif fikri bormi -------------------------------
YN1 = [
 ("In my view, homework does more harm than good.",
  "The writer thinks homework is harmful.", "YES",
  "\"In my view\" — muallif ochiq fikr bildiryapti.",
  "Fikr so'zi"),
 ("I believe that public transport should be free.",
  "The writer opposes free public transport.", "NO",
  "Muallif tarafdor — savol teskarisini aytyapti.", "Fikr so'zi"),
 ("It is clear that the policy has failed.",
  "The writer considers the policy a failure.", "YES",
  "\"It is clear that\" — muallifning qat'iy bahosi.",
  "Fikr so'zi"),
 ("Personally, I find modern architecture cold and unwelcoming.",
  "The writer admires modern architecture.", "NO",
  "cold, unwelcoming — salbiy baho.", "Ijobiy/salbiy"),
 ("There is no doubt that reading aloud helps young learners.",
  "The writer is convinced that reading aloud benefits young "
  "learners.", "YES",
  "no doubt = ishonch.", "Fikr kuchi"),
 ("Sadly, too few schools teach children how to cook.",
  "The writer would like more schools to teach cooking.", "YES",
  "\"Sadly, too few\" — muallif afsuslanyapti, demak ko'proq "
  "bo'lishini xohlaydi.", "Yashirin fikr"),
 ("The argument that zoos protect wildlife is unconvincing.",
  "The writer accepts that zoos protect wildlife.", "NO",
  "unconvincing — muallif ishonmaydi.", "Tip 18 — inkor"),
 ("Governments would be wise to invest in flood defences now.",
  "The writer recommends investing in flood defences.", "YES",
  "\"would be wise to\" — tavsiya.", "Fikr kuchi"),
 ("Claims that the new law will reduce crime are exaggerated.",
  "The writer doubts the new law will reduce crime.", "YES",
  "exaggerated — muallif shubhalanyapti.", "Yashirin fikr"),
 ("It would be a mistake to close the village school.",
  "The writer supports closing the village school.", "NO",
  "\"a mistake\" — qarshi.", "Ijobiy/salbiy"),
 ("Fortunately, the tradition has survived.",
  "The writer is pleased the tradition continues.", "YES",
  "Fortunately — mamnunlik.", "Yashirin fikr"),
 ("I am not persuaded by the evidence presented.",
  "The writer finds the evidence convincing.", "NO",
  "not persuaded = ishonmadi.", "Tip 18 — inkor"),
 ("Teachers deserve far better pay than they currently receive.",
  "The writer thinks teachers are underpaid.", "YES",
  "deserve better pay = hozir kam olishadi.", "Yashirin fikr"),
 ("The scheme is, in my opinion, a waste of public money.",
  "The writer approves of the scheme.", "NO",
  "waste of money — qarshi.", "Ijobiy/salbiy"),
 ("Such a change is long overdue.",
  "The writer welcomes the change.", "YES",
  "long overdue — allaqachon bo'lishi kerak edi, ya'ni ma'qullaydi.",
  "Yashirin fikr"),
]

# --- 2-bosqich: fikr aytilmagan bo'lsa NOT GIVEN ------------------
YN2 = [
 ("The council introduced a cycling scheme last year.",
  "The writer believes the cycling scheme was successful.",
  "NOT GIVEN",
  "Fakt bor, BAHO yo'q. Muallif hech qanday fikr bildirmagan.",
  "Fakt bor, fikr yo'q"),
 ("In my view, the report is too long.",
  "The writer thinks the report is too long.", "YES",
  "Aynan shu fikr aytilgan.", "Fikr so'zi"),
 ("In my view, the report is too long.",
  "The writer thinks the report is inaccurate.", "NOT GIVEN",
  "Uzunligi haqida fikr bor, ANIQLIGI haqida yo'q.",
  "Boshqa jihat"),
 ("Many parents now choose to home-school their children.",
  "The writer approves of home-schooling.", "NOT GIVEN",
  "Faqat holat bayon qilingan.", "Fakt bor, fikr yo'q"),
 ("The museum's new wing cost 4 million pounds.",
  "The writer thinks the new wing was too expensive.", "NOT GIVEN",
  "Raqam berilgan, baho berilmagan.", "Fakt bor, fikr yo'q"),
 ("I have always found grammar rules easier to learn than "
  "vocabulary.",
  "The writer finds vocabulary harder than grammar.", "YES",
  "Taqqoslash teskari yozilgan, ma'no bir xil.",
  "Tip 16 — taqqoslash"),
 ("I have always found grammar rules easier to learn than "
  "vocabulary.",
  "The writer thinks grammar should be taught first.", "NOT GIVEN",
  "Qiyinlik haqida fikr bor, O'QITISH TARTIBI haqida yo'q.",
  "Boshqa jihat"),
 ("Online shopping continues to grow rapidly.",
  "The writer regrets the growth of online shopping.", "NOT GIVEN",
  "O'sish aytilgan, munosabat aytilmagan.", "Fakt bor, fikr yo'q"),
 ("Frankly, the film's ending ruins an otherwise fine story.",
  "The writer dislikes the film's ending.", "YES",
  "ruins — salbiy baho.", "Ijobiy/salbiy"),
 ("Frankly, the film's ending ruins an otherwise fine story.",
  "The writer thinks the acting is poor.", "NOT GIVEN",
  "Yakun haqida fikr bor, AKTYORLIK haqida yo'q.",
  "Boshqa jihat"),
 ("The company has moved its headquarters to Dublin.",
  "The writer thinks the move to Dublin was sensible.", "NOT GIVEN",
  "Voqea aytilgan, baho yo'q.", "Fakt bor, fikr yo'q"),
 ("It is hard to defend a system that so clearly favours the rich.",
  "The writer criticises the system.", "YES",
  "\"hard to defend\" — tanqid.", "Yashirin fikr"),
 ("Some researchers have questioned these findings.",
  "The writer agrees with the researchers who question the "
  "findings.", "NOT GIVEN",
  "Bu BOSHQALARNING fikri. Muallif rozimi — aytilmagan.",
  "Boshqaning fikri"),
 ("I would happily see exams replaced by coursework.",
  "The writer supports replacing exams with coursework.", "YES",
  "happily — ma'qullaydi.", "Fikr so'zi"),
 ("The government published the figures in March.",
  "The writer believes the figures are unreliable.", "NOT GIVEN",
  "Nashr qilingani aytilgan, ishonchliligi haqida gap yo'q.",
  "Fakt bor, fikr yo'q"),
]

# --- 3-bosqich: modal fe'l va yumshatuvchi so'zlar ----------------
YN3 = [
 ("Cities should perhaps consider limiting car access to the "
  "centre.",
  "The writer insists that cars must be banned from city centres.",
  "NO",
  "TIP 20. \"should perhaps consider\" — juda yumshoq taklif. "
  "\"insists ... must be banned\" esa qat'iy talab.",
  "Tip 20 — modal fe'l"),
 ("Solar power may well become the cheapest source of energy.",
  "The writer thinks solar power could become the cheapest energy "
  "source.", "YES",
  "may well = could — kuch bir xil.", "Tip 20 — modal fe'l"),
 ("It is unlikely that the deadline will be met.",
  "The writer expects the deadline to be met.", "NO",
  "unlikely — kutmaydi.", "Tip 18 — inkor"),
 ("Employers ought to offer more flexible hours.",
  "The writer believes employers should be more flexible about "
  "hours.", "YES", "ought to = should.", "Tip 20 — modal fe'l"),
 ("The results must be treated with caution.",
  "The writer thinks the results can be fully trusted.", "NO",
  "with caution — to'liq ishonib bo'lmaydi.", "Ijobiy/salbiy"),
 ("Such projects can occasionally succeed.",
  "The writer believes such projects always succeed.", "NO",
  "TIP 24. occasionally — always emas.", "Tip 24 — mutlaq so'z"),
 ("Few would deny that the internet has changed education.",
  "The writer accepts that the internet has changed education.",
  "YES",
  "\"Few would deny\" — deyarli hamma rozi, ya'ni TASDIQ. Ikki "
  "inkor bir-birini yo'qqa chiqaradi.", "Yashirin inkor"),
 ("There is little evidence that the method works.",
  "The writer is confident the method works.", "NO",
  "little evidence — dalil kam, ishonch yo'q.", "Yashirin inkor"),
 ("It might be worth trying the scheme in one district first.",
  "The writer suggests testing the scheme on a small scale.",
  "YES", "one district = kichik miqyos.", "Parafraz"),
 ("Almost certainly, prices will rise again.",
  "The writer expects prices to rise.", "YES",
  "almost certainly — kutyapti.", "Tip 20 — modal fe'l"),
 ("The plan is not without its problems.",
  "The writer thinks the plan has some problems.", "YES",
  "\"not without\" = bor. Ikki inkor — tasdiq.",
  "Yashirin inkor"),
 ("I would hesitate to call the experiment a breakthrough.",
  "The writer regards the experiment as a breakthrough.", "NO",
  "hesitate to call — demoqchi emas.", "Yashirin inkor"),
 ("Rarely has a policy been so badly explained.",
  "The writer thinks the policy was poorly explained.", "YES",
  "\"Rarely ... so badly\" — juda yomon tushuntirilgan degani.",
  "Yashirin inkor"),
 ("The benefits, if any, are small.",
  "The writer is sure the benefits are large.", "NO",
  "\"if any\" + small — foyda deyarli yo'q.", "Yashirin inkor"),
 ("Arguably, the museum is the finest in the country.",
  "The writer states as a fact that the museum is the best in the "
  "country.", "NO",
  "Arguably — bahsli, FAKT sifatida aytilmagan.",
  "Tip 20 — modal fe'l"),
]

# --- 4-bosqich: tip qopqonlari ------------------------------------
YN4 = [
 ("The scheme failed, not because of poor planning, but because of "
  "a lack of funds.",
  "The writer blames poor planning for the failure.", "NO",
  "TIP 22. \"not because of X, but because of Y\" — sabab boshqa.",
  "Tip 22 — sabab"),
 ("Although the design is attractive, it is impractical.",
  "The writer thinks the design works well in practice.", "NO",
  "although dan KEYINGI qism — asosiy fikr: impractical.",
  "Qarama-qarshilik"),
 ("Every single one of these claims deserves scrutiny.",
  "The writer thinks some of the claims should be examined.",
  "YES", "TIP 24. \"hammasi\" ichida \"ba'zilari\" ham bor.",
  "Tip 24 — mutlaq so'z"),
 ("Neither the students nor the teachers were consulted.",
  "The writer says the teachers were consulted.", "NO",
  "neither ... nor — ikkalasi ham emas.", "Tip 18 — inkor"),
 ("The results were welcomed by the ministry.",
  "The ministry welcomed the results.", "YES",
  "TIP 23. Passivdan aktivga.", "Tip 23 — aktiv/passiv"),
 ("Money alone will not solve the problem.",
  "The writer believes funding is the complete answer.", "NO",
  "\"alone will not\" — pulning o'zi yetmaydi.",
  "Tip 18 — inkor"),
 ("The word 'reform' appears throughout the document.",
  "The writer believes the document proposes genuine reform.",
  "NOT GIVEN",
  "TIP 25. \"reform\" so'zi bor — lekin muallif uni HAQIQIY deb "
  "baholaganmi, aytilmagan.", "Tip 25 — bir xil so'z"),
 ("Students learn faster in small groups than in large lectures.",
  "The writer thinks large lectures are the best way to learn.",
  "NO", "TIP 16. Taqqoslash teskari.", "Tip 16 — taqqoslash"),
 ("Progress has been slower than expected, though it has not "
  "stopped.",
  "The writer says progress has halted.", "NO",
  "\"has not stopped\" — to'xtamagan.", "Tip 18 — inkor"),
 ("Only in exceptional cases should the rule be waived.",
  "The writer thinks the rule should usually be applied.", "YES",
  "TIP 24. Faqat istisno hollarda bekor qilinadi — demak odatda "
  "qo'llanadi.", "Tip 24 — mutlaq so'z"),
 ("The invention is often credited to Edison, wrongly in my view.",
  "The writer doubts that Edison was the inventor.", "YES",
  "\"wrongly in my view\" — muallif rozi emas.", "Fikr so'zi"),
 ("The city needs more housing and better transport.",
  "The writer says the city needs either more housing or better "
  "transport.", "NO",
  "TIP 30. and — ikkalasi ham kerak, or — tanlov.",
  "Tip 30 — and/or"),
 ("Since the law changed, accidents have decreased.",
  "The writer links the fall in accidents to the change in the "
  "law.", "YES",
  "TIP 22. \"Since\" bu yerda sabab bog'lovchisi.",
  "Tip 22 — sabab"),
 ("The book is long, repetitive and, at times, dull.",
  "The writer enjoyed the book.", "NO",
  "Uchta salbiy sifat.", "Ijobiy/salbiy"),
 ("The critics were unimpressed; readers, however, were delighted.",
  "The writer says readers disliked the book.", "NO",
  "however — o'quvchilar aksincha, mamnun bo'lishgan. Kim haqida "
  "gapirilayotganini adashtirmang.", "Qarama-qarshilik"),
]

# --- 5-bosqich: HAQIQIY IMTIHON (kitob, YES/NO/NOT GIVEN) ---------
YN5 = [
 ("But since 1980, the amount of water consumed per person has "
  "actually decreased, thanks to a range of new technologies that "
  "help to conserve water in homes and industry.",
  "Modern technologies have led to a reduction in domestic water "
  "consumption.", "YES",
  "TIP 19. decreased = reduction; thanks to = sabab.",
  "Tip 19 — o'sish/kamayish", 1),
 ("Two types of earthworms were used to create a soil structure.",
  "There were three types of worm used in creating a soil "
  "structure.", "NO",
  "TIP 21. Ikki tur — uch emas.", "Tip 21 — son/umumiy", 1),
 ("The laboratory studies similarly show less mental stimulation, "
  "as measured by brain-wave production, during viewing than "
  "during reading.",
  "People's brains show less activity while watching television "
  "than when reading.", "YES",
  "TIP 16. Taqqoslash aynan bir xil yo'nalishda.",
  "Tip 16 — taqqoslash", 1),
 ("In the end the fact remains that pharmaceutical companies have "
  "every right to make a profit and will continue to find new ways "
  "to increase sales.",
  "It is legitimate for drug companies to make money.", "YES",
  "\"have every right\" = legitimate.", "Parafraz", 1),
 ("Besides the physical and biological damage, technology can also "
  "have serious mental implications for children. It can be the "
  "cause of severe, addictive behaviour.",
  "It is possible to become obsessed with technology.", "YES",
  "addictive behaviour = obsession.", "Parafraz", 1),
 ("Calls can be made and received on mobiles from anywhere and the "
  "internet can be accessed without the need for cables. The "
  "advantages are enormous, bringing ease and convenience to our "
  "lives.",
  "There are considerable benefits to our wireless world.", "YES",
  "advantages are enormous = considerable benefits.", "Parafraz",
  1),
 ("The free, accessible nature of free-running means it has the "
  "potential to engage groups of young people who are typically "
  "unmoved by traditional sports. Basically anyone can practise, "
  "anywhere - all you need is a decent pair of trainers, so the "
  "financial outlay is negligible. There are no joining fees.",
  "Free-running is an expensive activity for participants.", "NO",
  "negligible outlay + no fees = qimmat emas.",
  "Ijobiy/salbiy", 1),
 ("Those findings suggest that caloric restriction could delay "
  "aging and increase longevity in humans, too.",
  "There is scientific evidence that eating fewer calories may "
  "extend human life.", "YES",
  "TIP 20. could / may — kuch bir xil, ikkalasi ham ehtimol.",
  "Tip 20 — modal fe'l", 1),
 ("As researchers on aging noted recently, no treatment on the "
  "market today has been proved to slow human aging.",
  "Studies show drugs available today can delay the process of "
  "growing old.", "NO",
  "\"no treatment ... proved\" — aynan teskari.",
  "Tip 18 — inkor", 1),
 ("In the security industry today, there are two clear divisions "
  "and one of these is decidedly more glamorous than the other. "
  "The glamorous part deals with digital security, which includes "
  "everything from fighting computer viruses and tackling "
  "malicious computer hackers.",
  "Designing ways to protect computers from hackers represents the "
  "boring side of the security industry.", "NO",
  "TIP 16. Raqamli xavfsizlik — aynan JOZIBALI tomoni deyilgan.",
  "Tip 16 — taqqoslash", 2),
 ("While reading a certain amount of writing is as crucial as it "
  "has ever been in industrial societies, it is doubtful whether a "
  "fully extended grasp of either is as necessary as it was 30 or "
  "40 years ago.",
  "Our literacy skills need to be as highly developed as they were "
  "in the past.", "NO",
  "\"it is doubtful whether ... as necessary\" — muallif "
  "shubhalanadi.", "Yashirin inkor", 2),
 ("The very infinity of choice enjoyed by the novelist is a source "
  "of anxiety and difficulty. But the novelist does retain "
  "absolute control over his text until it is published. He may be "
  "advised by his editor to revise his text, but if the writer "
  "refused to meet this condition no one would be surprised.",
  "Novelists must agree to the demands of their editors.", "NO",
  "TIP 20. \"may be advised\" va rad etish mumkin — \"must\" emas.",
  "Tip 20 — modal fe'l", 2),
 ("Such road pricing however, can be controversial. When the local "
  "government in Cambridge England considered introducing "
  "Singaporean techniques, it faced vocal and ultimately "
  "successful opposition.",
  "Charging drivers for entering certain parts of the city has "
  "been successfully done in Cambridge England.", "NO",
  "Muvaffaqiyatli bo'lgani — QARSHILIK. Ya'ni tizim joriy "
  "etilmagan. \"successful\" so'zi sizni aldaydi.",
  "Tip 25 — bir xil so'z", 2),
 ("Some people have argued that human-induced global warming is "
  "beneficial because it averts the next ice age.",
  "Global warming is universally believed to be a bad thing for "
  "the Earth.", "NO",
  "TIP 24. \"universally\" — hamma. Ammo ba'zilar foydali deb "
  "hisoblaydi.", "Tip 24 — mutlaq so'z", 2),
 ("Food production has kept pace with soaring populations mainly "
  "because of the expansion of artificial irrigation systems that "
  "make possible the growth of 40% of the world's food.",
  "Feeding increasing populations is possible due primarily to "
  "improved irrigation systems.", "YES",
  "TIP 22. mainly because of = due primarily to.",
  "Tip 22 — sabab", 2),
 ("But it is worth trying, for to understand the initial shock of "
  "those images is to understand the extraordinary power and magic "
  "of cinema, the unique, hypnotic quality that has made film the "
  "most dynamic, effective art form of the 20th century.",
  "It is important to understand how the first audiences reacted "
  "to the cinema.", "YES",
  "\"it is worth trying ... to understand the initial shock\" — "
  "muallif buni muhim deb biladi.", "Yashirin fikr", 2),
 ("When an organisation is shrinking, the best and most mobile "
  "workers are prone to leave voluntarily. Unfortunately, they are "
  "the ones the organisation can least afford to lose - those with "
  "the highest skills and experience. The minor employees remain.",
  "A shrinking organisation tends to lose its less skilled "
  "employees rather than its more skilled employees.", "NO",
  "TIP 16. Aynan teskari: eng malakalilari ketadi.",
  "Tip 16 — taqqoslash", 2),
 ("As an illustration of the health risks, in the case of a "
  "married couple where one partner is a smoker and one a "
  "non-smoker, the latter is believed to have a 30 per cent higher "
  "risk of death from heart disease because of passive smoking.",
  "If one partner in a marriage smokes, the other is likely to "
  "take up smoking.", "NOT GIVEN",
  "TIP 25. Matn SALOMATLIK xavfi haqida; ikkinchisi chekishni "
  "boshlaydimi — aytilmagan.", "Tip 25 — bir xil so'z", 3),
 ("A cardinal mistake is to think qualifications make a good "
  "teacher. When you're faced with 30 truculent children after "
  "lunch on a Friday afternoon, they don't count for much.",
  "More difficult behaviour is often seen in pupils towards the "
  "end of the school day.", "NOT GIVEN",
  "TIP 25. Juma tushdan keyin misol qilib keltirilgan, lekin "
  "\"kun oxirida qiyinlashadi\" degan umumiy fikr yo'q.",
  "Tip 25 — bir xil so'z", 3),
 ("It's been scientifically proven that three people will be "
  "better than one at solving problems, even if that one person is "
  "the smartest person in the field.",
  "Teams work best when their members are of equally matched "
  "intelligence.", "NOT GIVEN",
  "TIP 25. Guruh yaxshiroq deyilgan, lekin a'zolar intellekti TENG "
  "bo'lishi haqida gap yo'q.", "Tip 25 — bir xil so'z", 3),
 ("We predict that preschoolers will both continue and "
  "increasingly begin to adopt video games for personal enjoyment.",
  "The proportion of preschool children using video games is "
  "likely to rise.", "YES",
  "TIP 19. \"increasingly begin to adopt\" = o'sish.",
  "Tip 19 — o'sish/kamayish", 2),
 ("Transport systems including roads within and between cities "
  "need to be constructed or upgraded; green fields are turned "
  "into airports; virgin forest is stripped to provide food and "
  "firewood. In poorer regions, this newly exposed land becomes "
  "desert, completing the cycle of destruction.",
  "The destruction of land for food and firewood is linked to "
  "desertification.", "YES",
  "TIP 22. \"becomes desert\" — bevosita bog'liqlik ko'rsatilgan.",
  "Tip 22 — sabab", 2),
 ("The community that focuses its efforts on the exploration of "
  "space has largely been different from the community focused on "
  "the study and protection of the Earth's environment, despite "
  "the fact that both fields of interest involve what might be "
  "referred to as 'scientific exploration'.",
  "Activities related to environmental protection and space "
  "exploration have a common theme.", "YES",
  "\"both ... involve scientific exploration\" = umumiy jihat.",
  "Qarama-qarshilik", 2),
 ("In order to know what kind of lies work best, successful liars "
  "need to accurately assess other people's emotional states.",
  "To be a good liar, one has to understand other people's "
  "emotions.", "YES",
  "assess emotional states = tushunish.", "Parafraz", 2),
 ("Experience shows that for nations, as for individuals, it is "
  "critical to address problems sooner rather than later. Waiting "
  "significantly increases the costs and difficulties of "
  "addressing these challenges.",
  "It would be better to wait a while to see how the situation "
  "develops, as fast decisions could create problems in the "
  "future.", "NO",
  "Muallif aynan teskarisini aytadi: kutish qimmatga tushadi.",
  "Qarama-qarshilik", 2),
 ("In our Experience Sampling Method (ESM) studies the longer "
  "people sat in front of the set, the less satisfaction they said "
  "they obtained from it.",
  "Pleasure increases in proportion to the length of time spent "
  "watching TV.", "NO",
  "TIP 19. Matnda teskari bog'liqlik: uzoq — kam qoniqish.",
  "Tip 19 — o'sish/kamayish", 2),
 ("Drawn from the world of business, and in particular of "
  "marketing, branding would have been an alien concept to "
  "Leonardo da Vinci or Beethoven, or most other self-respecting "
  "artists and musicians, and one that the vast majority would "
  "have rejected.",
  "Beethoven would probably have accepted the idea of branding.",
  "NO",
  "\"would have rejected\" — rad etardi.", "Tip 18 — inkor", 2),
 ("It is also the case that ever-increasing numbers of people make "
  "their living out of writing, which is better rewarded than ever "
  "before.",
  "Professional writers earn relatively more than they used to.",
  "YES",
  "TIP 16. better rewarded than ever before = avvalgidan ko'proq.",
  "Tip 16 — taqqoslash", 2),
 ("In fact, climate science needs professional help to rebuild its "
  "reputation.",
  "Climate scientists should take professional advice on regaining "
  "public confidence.", "YES",
  "needs professional help = should take professional advice.",
  "Parafraz", 2),
 ("Increasing productivity that results in decreasing costs for "
  "such goods has been responsible for the greatest gains in the "
  "standard of living, and there is every reason to believe that "
  "this will continue.",
  "As manufactured goods get cheaper, people will benefit more "
  "from them.", "YES",
  "TIP 19. Ikki yo'nalish: xarajat kamayadi -> turmush darajasi "
  "o'sadi; muallif davom etishiga ishonadi.",
  "Tip 19 — o'sish/kamayish", 2),
 ("What is the Tupperware story? The special plastic used in it "
  "was invented in 1938 by an American called Earl Tupper. The "
  "famous seals, which keep the air out and freshness in, came "
  "later.",
  "Keeping food fresh is something Tupperware does well.", "YES",
  "\"keep the air out and freshness in\" — muallif buni ijobiy "
  "bayon qilyapti.", "Yashirin fikr", 2),
 ("Bright or creative children are often physically very active at "
  "the same time, and so may receive more parental attention. This "
  "can sometimes cause problems with other siblings who may feel "
  "jealous even though they themselves may be bright. Their "
  "creative talents may be undervalued and so never come to "
  "fruition.",
  "The brother or sister of a gifted older child may fail to "
  "fulfil their own potential.", "YES",
  "\"never come to fruition\" = imkoniyati ochilmay qoladi.",
  "Parafraz", 2),
 ("The computer has re-established a central place for the written "
  "word on the screen, which used to be entirely devoted to the "
  "image. There is even anecdotal evidence that children are "
  "mastering reading and writing in order to get on to the "
  "Internet.",
  "Computers are having a negative impact on literacy in schools.",
  "NO",
  "Muallif ijobiy ta'sir haqida yozyapti.", "Ijobiy/salbiy", 2),
 ("Mozart himself simply wanted to create the finest music ever "
  "written but did not necessarily view himself as a genius - he "
  "could write sublime music at will, and so often preferred to "
  "lead a hedonistic lifestyle.",
  "Mozart was acutely aware of his own remarkable talent.", "NO",
  "\"did not necessarily view himself as a genius\" — teskari.",
  "Tip 18 — inkor", 2),
 ("Albert Einstein and Bill Gates are two more examples of people "
  "whose talents have blossomed by virtue of the times they were "
  "living in.",
  "Einstein and Gates would have achieved success in any era.",
  "NO",
  "TIP 22. \"by virtue of the times\" — aynan o'z davri tufayli. "
  "Demak istalgan davrda emas.", "Tip 22 — sabab", 3),
 ("The researchers thought they saw evidence of 'conversation' "
  "between the elephants; when the signal to move was given, "
  "elephants stood side by side and 'discussed' which route to "
  "take. When this long exchange ended, the elephants moved all "
  "together in one direction.",
  "The study shows elephants work together in order to make a "
  "decision.", "YES",
  "Muhokama + birgalikda harakat = jamoaviy qaror.",
  "Parafraz", 3),
 ("The classic net worker is someone who is strong enough within "
  "themselves to connect different people including close friends "
  "with each other.",
  "The classic networker is physically strong and generally in "
  "good health.", "NOT GIVEN",
  "TIP 25. \"strong\" so'zi bor, ammo u YETUK SHAXS ma'nosida — "
  "jismoniy kuch haqida emas.", "Tip 25 — bir xil so'z", 3),
 ("The danger is that this commercialisation of our private world "
  "breeds cynicism and emotional attachment: happiness is reduced "
  "to no more than having the latest mobile phone.",
  "The general public is becoming concerned about the increase in "
  "cynicism.", "NOT GIVEN",
  "TIP 25. Muallif tashvishlanyapti — lekin JAMOATCHILIK "
  "tashvishlanayotgani aytilmagan. Kim tashvishda — shuni "
  "farqlang.", "Tip 25 — bir xil so'z", 3),
 ("Although video games were first developed for adults, they are "
  "no longer exclusively reserved for the grown ups in the home. "
  "In 2006, Rideout and Hamel reported that as many as 29 percent "
  "of preschool children in the United States had played console "
  "video games.",
  "Video game use amongst preschool children is higher in the US "
  "than in other countries.", "NOT GIVEN",
  "TIP 16. AQSH raqami bor, lekin BOSHQA davlatlar bilan "
  "taqqoslash yo'q.", "Tip 16 — taqqoslash", 3),
 ("At the Ottawa Conference in 1986, a charter was developed which "
  "outlined new directions for health promotion based on the "
  "socio-ecological view of health. This charter, known as the "
  "Ottawa Charter for Health Promotion, remains as the backbone of "
  "health action today.", 
  "The principles of the Ottawa Charter are considered to be out "
  "of date in the 1990s.", "NO",
  "\"remains as the backbone ... today\" — hali ham asosiy hujjat.",
  "Qarama-qarshilik", 3),
]


# =====================================================================
#  YIG'ISH
# =====================================================================
def _rows(kind, opts, groups):
    """groups: {step: [(passage, q, ans, why, tip[, d]), ...]}"""
    out = []
    for step in sorted(groups):
        items = groups[step]
        # 5-bosqichda qiyinlik (oxirgi element) bo'yicha saralaymiz:
        # oson imtihon savoli oldin, qiyini keyin.
        if items and len(items[0]) == 6:
            items = sorted(enumerate(items),
                           key=lambda p: (p[1][5], p[0]))
            items = [x[1] for x in items]
        for i, it in enumerate(items):
            passage, prompt, ans, why, tip = it[:5]
            payload = {
                "passage": passage, "prompt": prompt,
                "options": list(opts), "step": step, "order": i,
                "tip": tip, "step_title": STEP_TITLES[step],
            }
            level = "B1" if step <= 2 else ("B2" if step <= 4 else "C1")
            out.append((kind, level, payload, ans, why))
    return out


def build_rows():
    rows = _rows(TF_KIND, TF_OPTS,
                 {1: TF1, 2: TF2, 3: TF3, 4: TF4, 5: TF5})
    rows += _rows(YN_KIND, YN_OPTS,
                  {1: YN1, 2: YN2, 3: YN3, 4: YN4, 5: YN5})
    return rows


def seed_reading_ielts(db):
    """Idempotent: (kind, passage, prompt) bo'yicha yo'qlari qo'shiladi."""
    from common import _seed_done, _seed_mark
    if _seed_done(db, "ielts_read_v1"):
        return None
    import json
    import models

    have = set()
    for k, p in db.query(models.PracticeItem.kind,
                         models.PracticeItem.payload).filter(
            models.PracticeItem.skill == SKILL).all():
        try:
            pl = json.loads(p)
            have.add((k, pl.get("passage"), pl.get("prompt")))
        except Exception:
            pass
    made = 0
    for kind, level, payload, answer, explain in build_rows():
        key = (kind, payload.get("passage"), payload.get("prompt"))
        if key in have:
            continue
        db.add(models.PracticeItem(
            skill=SKILL, kind=kind, level=level,
            payload=json.dumps(payload, ensure_ascii=False),
            answer=answer, explain=explain))
        have.add(key)
        made += 1
    if made:
        db.commit()
    _seed_mark(db, "ielts_read_v1")
    return made
