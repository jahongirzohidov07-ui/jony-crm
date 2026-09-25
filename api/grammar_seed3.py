# -*- coding: utf-8 -*-
"""GRAMMAR 3-TO'LQIN (2026-08-24).

Jahongir: "Boshqa tillarni grammatikasi yoq ekan ularni ham qoshib
qoygin iloji boricha maydalab grammatik mavzularga va darajalarga
aylantirib xuddi ingliz tiliga oxshatib qilgin. Keyin ingliz til
grammatika mavzulari B2da tugagan ekan c1 va C2 mavzularni ham
qoyish kerak".

Bu faylda:
  - Ingliz tili C1 va C2 darajalari (zanjir B2 dan keyin davom etadi);
  - Rus, nemis, koreys tillari A1/A2 — xuddi inglizcha kabi mayda
    mavzular, fill/error/order turlari, izohlar o'zbekcha.

Tuzilishi grammar_seed bilan bir xil: (tartib, boss?, mavzu,
savollar). Idempotent — (til, mavzu, prompt) bo'yicha yo'qlari
qo'shiladi, marker grammar_v3.
"""

B = True

# ============================================================
#  INGLIZ TILI — C1
# ============================================================
SEED_EN_C1 = [
(101, not B, "C1 — Inversion (Never have I...)", [
 ("fill", "Never ___ such a beautiful city.",
  ["have I seen", "I have seen", "I saw", "have seen I"],
  "have I seen",
  "Inkor so'z boshda kelsa fe'l egadan OLDIN: Never have I seen."),
 ("fill", "Not only ___ late, but he also forgot the tickets.",
  ["was he", "he was", "was", "he is"], "was he",
  "Not only... boshlasa inversiya: Not only was he late."),
 ("fill", "Hardly ___ the door when the phone rang.",
  ["had I opened", "I had opened", "I opened", "did I opened"],
  "had I opened",
  "Hardly + past perfect inversiyasi: Hardly had I opened."),
 ("fill", "Under no circumstances ___ this door.",
  ["should you open", "you should open", "you open",
   "should open you"], "should you open",
  "Under no circumstances — kuchli inkor, inversiya shart."),
 ("error", "Rarely I have felt so proud.",
  ["Rarely", "I have", "felt", "so proud"], "I have",
  "Rarely have I felt — inversiya kerak edi."),
 ("order", "Kamdan-kam bunday imkoniyat keladi.",
  ["Seldom", "does", "such", "a", "chance", "come"],
  "Seldom does such a chance come",
  "Seldom + does + ega + fe'l."),
]),
(102, not B, "C1 — Mixed conditionals", [
 ("fill", "If I had studied medicine, I ___ a doctor now.",
  ["would be", "would have been", "will be", "were"], "would be",
  "O'tmishdagi shart + HOZIRGI natija: would be now."),
 ("fill", "If she ___ so shy, she would have introduced herself "
  "yesterday.",
  ["weren't", "hadn't been", "isn't", "wouldn't be"], "weren't",
  "Hozirgi doimiy xususiyat + o'tmishdagi natija."),
 ("fill", "If we ___ the map, we wouldn't be lost now.",
  ["had taken", "took", "take", "would take"], "had taken",
  "O'tmishdagi xato + hozirgi natija: if + past perfect."),
 ("fill", "I ___ tired now if I hadn't stayed up all night.",
  ["wouldn't be", "wouldn't have been", "won't be", "am not"],
  "wouldn't be", "Hozirgi natija — wouldn't be now."),
 ("error", "If I would have known, I would have called you.",
  ["If I", "would have known", "I would", "have called"],
  "would have known",
  "If qismida would bo'lmaydi: If I had known."),
 ("order", "Agar o'shanda ketmaganimda, hozir shu yerda ishlardim.",
  ["If", "I", "hadn't", "left,", "I", "would", "work", "here", "now"],
  "If I hadn't left, I would work here now",
  "Aralash shart: past perfect + would + now."),
]),
(103, not B, "C1 — Cleft sentences (It was... that)", [
 ("fill", "___ the manager who made the final decision.",
  ["It was", "There was", "He was", "That was"], "It was",
  "Urg'u berish: It was X who..."),
 ("fill", "What I need most ___ a long holiday.",
  ["is", "are", "было", "be"], "is",
  "What-cleft: What I need most is..."),
 ("fill", "It was only after the meeting ___ I understood the plan.",
  ["that", "when", "which", "what"], "that",
  "It was... that — qat'iy qolip."),
 ("fill", "___ was the noise that kept me awake, not the light.",
  ["It", "There", "That", "What"], "It",
  "It was the noise that... urg'u shovqinda."),
 ("error", "It was him who break the window.",
  ["It was", "him", "who", "break"], "break",
  "who BROKE bo'lishi kerak — o'tgan zamon."),
 ("order", "Menga aynan uning ovozi yoqadi.",
  ["It", "is", "her", "voice", "that", "I", "like"],
  "It is her voice that I like",
  "It is X that... — urg'uli qurilma."),
]),
(104, B, "C1 BOSS — Participle clauses", [
 ("fill", "___ the report, she went home.",
  ["Having finished", "Finishing", "Finished", "To finish"],
  "Having finished",
  "Avval tugatdi, keyin ketdi: Having + V3."),
 ("fill", "___ from above, the town looks tiny.",
  ["Seen", "Seeing", "To see", "Saw"], "Seen",
  "Shahar KO'RILADI (passiv) — Seen from above."),
 ("fill", "Not ___ what to say, he stayed silent.",
  ["knowing", "known", "to know", "knew"], "knowing",
  "Not knowing — sabab: bilmagani uchun."),
 ("fill", "The man ___ by the window is my uncle.",
  ["standing", "stood", "stands", "to stand"], "standing",
  "Aniqlovchi: (who is) standing."),
 ("error", "Walking down the street, the trees looked beautiful.",
  ["Walking", "down the street", "the trees", "looked"],
  "the trees",
  "Dangling participle: yurgan odam daraxt emas — ega mos emas."),
 ("order", "Ishini tugatib, u kompyuterni o'chirdi.",
  ["Having", "finished", "his", "work,", "he", "turned", "off",
   "the", "computer"],
  "Having finished his work, he turned off the computer",
  "Having + V3 bilan ketma-ketlik."),
]),
]

# ============================================================
#  INGLIZ TILI — C2
# ============================================================
SEED_EN_C2 = [
(111, not B, "C2 — Subjunctive & formal structures", [
 ("fill", "The board insisted that he ___ present at the hearing.",
  ["be", "is", "was", "will be"], "be",
  "Insist/demand/suggest + that + BAZA fe'l (subjunctive)."),
 ("fill", "It is essential that every member ___ informed.",
  ["be", "is", "are", "been"], "be",
  "It is essential that... be — rasmiy uslub."),
 ("fill", "___ it not for your help, we would have failed.",
  ["Were", "Was", "If", "Had"], "Were",
  "Were it not for... = If it were not for..."),
 ("fill", "___ the need arise, contact the embassy at once.",
  ["Should", "Would", "Could", "Must"], "Should",
  "Should the need arise = agar ehtiyoj tug'ilsa (rasmiy)."),
 ("error", "I suggest that she goes home early.",
  ["I suggest", "that", "she", "goes"], "goes",
  "Subjunctive: she GO home — s qo'shimchasisiz."),
 ("order", "Qoidalarga rioya qilinishi shart.",
  ["It", "is", "imperative", "that", "the", "rules", "be",
   "observed"],
  "It is imperative that the rules be observed",
  "Imperative that + be — rasmiy talab."),
]),
(112, not B, "C2 — Advanced modality (needn't have...)", [
 ("fill", "You ___ bought bread — we already had plenty.",
  ["needn't have", "mustn't have", "shouldn't", "can't have"],
  "needn't have",
  "Qildi, lekin KERAK EMAS edi: needn't have + V3."),
 ("fill", "She ___ have left — her car is still outside.",
  ["can't", "mustn't", "needn't", "shouldn't"], "can't",
  "Mantiqiy xulosa: bo'lishi MUMKIN EMAS."),
 ("fill", "He ___ have warned us, but he chose not to.",
  ["could", "can", "must", "need"], "could",
  "Imkoni bor edi, qilmadi: could have + V3."),
 ("fill", "By June, I ___ here for ten years.",
  ["will have been working", "will work", "am working",
   "will be worked"], "will have been working",
  "Future perfect continuous."),
 ("error", "You mustn't have watered the plants - I already did.",
  ["You", "mustn't have", "watered", "I already did"],
  "mustn't have",
  "needn't have kerak: 'shart emas edi' ma'nosi."),
 ("order", "Bilet olishing shart emas edi — kirish bepul ekan.",
  ["You", "needn't", "have", "bought", "a", "ticket"],
  "You needn't have bought a ticket",
  "needn't have + V3."),
]),
(113, not B, "C2 — Ellipsis & substitution", [
 ("fill", "— Will they agree? — I hope ___.",
  ["so", "it", "that", "yes"], "so",
  "I hope so — butun gap o'rniga so."),
 ("fill", "She sings better than I ___.",
  ["do", "am", "sing so", "does"], "do",
  "Takror fe'l o'rniga do."),
 ("fill", "I'd like to come, but I'm afraid I ___.",
  ["can't", "can't come to", "don't", "won't to"], "can't",
  "Ellipsis: come tushirib qoldiriladi."),
 ("fill", "My phone is old, so I need a new ___.",
  ["one", "it", "phone one", "ones"], "one",
  "Ot o'rniga one."),
 ("error", "— Is he coming? — I don't think it.",
  ["Is he", "coming", "I don't think", "it"], "it",
  "I don't think SO deyiladi."),
 ("order", "Kelaman dedim va keldim ham.",
  ["I", "said", "I", "would", "come,", "and", "I", "did"],
  "I said I would come, and I did",
  "did — come o'rnini bosadi."),
]),
(114, B, "C2 BOSS — Nominalisation & formal register", [
 ("fill", "The ___ of the bridge took three years.",
  ["construction", "constructing", "construct", "constructed"],
  "construction",
  "Rasmiy uslub: fe'l -> ot (nominalisation)."),
 ("fill", "There has been a sharp ___ in prices.",
  ["rise", "rising", "risen", "rose"], "rise",
  "a sharp rise — ot sifatida."),
 ("fill", "His ___ to compromise surprised everyone.",
  ["willingness", "willing", "will", "willingly"], "willingness",
  "Sifat -> ot: willingness."),
 ("fill", "The committee expressed ___ about the delays.",
  ["concern", "concerning", "concerned", "concernment"], "concern",
  "express concern — rasmiy iboralar."),
 ("error", "The analyze of the data revealed a pattern.",
  ["The", "analyze", "of the data", "revealed"], "analyze",
  "Ot shakli: analysis."),
 ("order", "Qarorning e'lon qilinishi ertaga kutilmoqda.",
  ["The", "announcement", "of", "the", "decision", "is",
   "expected", "tomorrow"],
  "The announcement of the decision is expected tomorrow",
  "Nominalisation + passiv — rasmiy uslub."),
]),
]

# ============================================================
#  RUS TILI — A1
# ============================================================
SEED_RU_A1 = [
(1, not B, "RU A1 — Jins: он / она / оно", [
 ("fill", "Дом — ___ большой.", ["он", "она", "оно", "они"], "он",
  "Undosh bilan tugagan so'z — mujskoy rod (он)."),
 ("fill", "Книга — ___ интересная.",
  ["она", "он", "оно", "они"], "она",
  "-а/-я bilan tugasa — jenskiy rod (она)."),
 ("fill", "Окно — ___ открыто.", ["оно", "он", "она", "они"], "оно",
  "-о/-е bilan tugasa — sredniy rod (оно)."),
 ("fill", "Мама и папа — ___ дома.",
  ["они", "он", "она", "оно"], "они",
  "Ko'plik — они."),
 ("error", "Стол — она новая.", ["Стол", "она", "новая", "—"],
  "она", "Стол — он (mujskoy rod): он новый."),
 ("order", "Bu mening uyim.", ["Это", "мой", "дом"],
  "Это мой дом", "Это + egalik olmoshi + ot."),
]),
(2, not B, "RU A1 — Shaxs olmoshlari va 'быть'", [
 ("fill", "___ студент.", ["Я", "Ты", "Мы", "Они"], "Я",
  "Men — Я. Hozirgi zamonda 'быть' tushiriladi: Я студент."),
 ("fill", "___ врач? — Да, я врач.",
  ["Ты", "Я", "Оно", "Мы"], "Ты",
  "Savol ikkinchi shaxsga: Ты врач?"),
 ("fill", "Мы ___ из Узбекистана.", ["—", "есть", "быть", "она"],
  "—", "Hozirgi zamonda bog'lama YO'Q: Мы из Узбекистана."),
 ("fill", "Это ___ семья.", ["моя", "мой", "моё", "мои"], "моя",
  "семья — jenskiy rod: моя."),
 ("error", "Я есть учитель.", ["Я", "есть", "учитель", "—"],
  "есть", "Hozirgi zamonda есть ishlatilmaydi: Я учитель."),
 ("order", "Bu mening onam.", ["Это", "моя", "мама"],
  "Это моя мама", "Это + моя + ot."),
]),
(3, not B, "RU A1 — Fe'l hozirgi zamon (-ать)", [
 ("fill", "Я ___ по-русски.",
  ["говорю", "говоришь", "говорит", "говорят"], "говорю",
  "Я + -ю: говорю."),
 ("fill", "Ты ___ дома?", ["работаешь", "работаю", "работает",
  "работаем"], "работаешь", "Ты + -ешь: работаешь."),
 ("fill", "Он ___ книгу.", ["читает", "читаю", "читаешь",
  "читаем"], "читает", "Он/она + -ет: читает."),
 ("fill", "Мы ___ телевизор.", ["смотрим", "смотрю", "смотрит",
  "смотрите"], "смотрим", "Мы + -им/-ем: смотрим."),
 ("error", "Она говорю по-английски.",
  ["Она", "говорю", "по-английски", "—"], "говорю",
  "Она говорИТ — uchinchi shaxs."),
 ("order", "Men rus tilini o'rganaman.",
  ["Я", "учу", "русский", "язык"], "Я учу русский язык",
  "Ega + fe'l + to'ldiruvchi."),
]),
(4, B, "RU A1 BOSS — Ko'plik", [
 ("fill", "стол — ___", ["столы", "стола", "столов", "столи"],
  "столы", "Qattiq undoshdan keyin -ы."),
 ("fill", "книга — ___", ["книги", "книгы", "книг", "книгов"],
  "книги", "г/к/х dan keyin doim -и."),
 ("fill", "окно — ___", ["окна", "окны", "окно", "окон"], "окна",
  "-о tugagan so'z ko'plikda -а."),
 ("fill", "друг — ___", ["друзья", "други", "другы", "другов"],
  "друзья", "Istisno: друг — друзья."),
 ("error", "У меня два книги.", ["У меня", "два", "книги", "—"],
  "два", "книга — jenskiy rod: ДВЕ книги."),
 ("order", "Bizda uchta mushuk bor.", ["У", "нас", "три", "кошки"],
  "У нас три кошки", "У + нас + son + ot."),
]),
]

# ============================================================
#  RUS TILI — A2
# ============================================================
SEED_RU_A2 = [
(11, not B, "RU A2 — O'tgan zamon", [
 ("fill", "Вчера я ___ в школе.", ["был", "была", "было", "были"],
  "был", "Mujskoy rod: был (ayol kishi: была)."),
 ("fill", "Она ___ фильм вечером.",
  ["смотрела", "смотрел", "смотрело", "смотрели"], "смотрела",
  "Она + -ла."),
 ("fill", "Мы ___ в парке.", ["гуляли", "гулял", "гуляла",
  "гуляло"], "гуляли", "Ko'plikda -ли."),
 ("fill", "Он ___ книгу неделю назад.",
  ["читал", "читала", "читали", "читает"], "читал",
  "Он + -л, o'tgan zamon."),
 ("error", "Я вчера смотрю фильм.", ["Я", "вчера", "смотрю",
  "фильм"], "смотрю", "Вчера — o'tgan zamon: смотрел(а)."),
 ("order", "Kecha biz kino ko'rdik.",
  ["Вчера", "мы", "смотрели", "фильм"], "Вчера мы смотрели фильм",
  "Vaqt + ega + fe'l (o'tgan) + to'ldiruvchi."),
]),
(12, not B, "RU A2 — Predloglar: в / на", [
 ("fill", "Я живу ___ Ташкенте.", ["в", "на", "у", "с"], "в",
  "Shahar ichida — в + predlojniy."),
 ("fill", "Книга лежит ___ столе.", ["на", "в", "у", "о"], "на",
  "Yuzada — на столе."),
 ("fill", "Мы идём ___ концерт.", ["на", "в", "к", "у"], "на",
  "Tadbirga — на концерт."),
 ("fill", "Дети ___ школе.", ["в", "на", "у", "от"], "в",
  "Bino ichida — в школе."),
 ("error", "Я работаю на банке.", ["Я", "работаю", "на", "банке"],
  "на", "Tashkilot ichida — В банке."),
 ("order", "Biz maktabda o'qiymiz.", ["Мы", "учимся", "в", "школе"],
  "Мы учимся в школе", "в + joy (predlojniy kelishik)."),
]),
(13, not B, "RU A2 — Vinitelniy kelishik", [
 ("fill", "Я читаю ___ .", ["книгу", "книга", "книге", "книгой"],
  "книгу", "Jenskiy rod -а -> -у: книгу."),
 ("fill", "Она любит ___ .", ["музыку", "музыка", "музыке",
  "музыкой"], "музыку", "-а -> -у."),
 ("fill", "Мы видим ___ .", ["дом", "дома", "доме", "домом"],
  "дом", "Jonsiz mujskoy rod o'zgarmaydi."),
 ("fill", "Он знает ___ .", ["Анну", "Анна", "Анне", "Анной"],
  "Анну", "Jonli ot: Анна -> Анну."),
 ("error", "Я пью чая.", ["Я", "пью", "чая", "—"], "чая",
  "Vinitelniy: пью ЧАЙ."),
 ("order", "Men yangi telefon sotib olaman.",
  ["Я", "покупаю", "новый", "телефон"],
  "Я покупаю новый телефон", "Ega + fe'l + sifat + ot."),
]),
(14, B, "RU A2 BOSS — Kelasi zamon", [
 ("fill", "Завтра я ___ работать.",
  ["буду", "будешь", "будет", "будем"], "буду",
  "Я + буду + infinitiv."),
 ("fill", "Мы ___ отдыхать летом.",
  ["будем", "буду", "будет", "будете"], "будем",
  "Мы + будем."),
 ("fill", "Она ___ учить корейский.",
  ["будет", "буду", "будешь", "будут"], "будет",
  "Она + будет."),
 ("fill", "Что ты ___ делать вечером?",
  ["будешь", "буду", "будет", "будем"], "будешь",
  "Ты + будешь."),
 ("error", "Завтра он буду дома.", ["Завтра", "он", "буду",
  "дома"], "буду", "Он БУДЕТ дома."),
 ("order", "Ertaga men do'stimga qo'ng'iroq qilaman.",
  ["Завтра", "я", "позвоню", "другу"], "Завтра я позвоню другу",
  "Vaqt + ega + fe'l + to'ldiruvchi."),
]),
]

# ============================================================
#  NEMIS TILI — A1
# ============================================================
SEED_DE_A1 = [
(1, not B, "DE A1 — Artikel: der / die / das", [
 ("fill", "___ Mann ist groß.", ["Der", "Die", "Das", "Den"],
  "Der", "Erkak jins — der Mann."),
 ("fill", "___ Frau kommt aus Berlin.",
  ["Die", "Der", "Das", "Dem"], "Die", "Ayol jins — die Frau."),
 ("fill", "___ Kind spielt im Garten.",
  ["Das", "Der", "Die", "Den"], "Das", "O'rta jins — das Kind."),
 ("fill", "___ Bücher sind neu.", ["Die", "Das", "Der", "Den"],
  "Die", "Ko'plikda doim die."),
 ("error", "Der Auto ist schnell.", ["Der", "Auto", "ist",
  "schnell"], "Der", "das Auto — o'rta jins."),
 ("order", "Bola olma yeyapti.", ["Das", "Kind", "isst", "einen",
  "Apfel"], "Das Kind isst einen Apfel",
  "Artikel + ot + fe'l 2-o'rin."),
]),
(2, not B, "DE A1 — sein va haben", [
 ("fill", "Ich ___ müde.", ["bin", "bist", "ist", "sind"], "bin",
  "ich bin."),
 ("fill", "Du ___ mein Freund.", ["bist", "bin", "ist", "seid"],
  "bist", "du bist."),
 ("fill", "Wir ___ einen Hund.", ["haben", "habe", "hat", "habt"],
  "haben", "wir haben."),
 ("fill", "Sie (u, ayol) ___ zwei Kinder.",
  ["hat", "habe", "hast", "haben"], "hat", "sie hat."),
 ("error", "Er bin Lehrer.", ["Er", "bin", "Lehrer", "—"], "bin",
  "Er IST Lehrer."),
 ("order", "Men talabaman.", ["Ich", "bin", "Student"],
  "Ich bin Student", "Ega + sein + ot."),
]),
(3, not B, "DE A1 — Präsens (fe'l tuslash)", [
 ("fill", "Ich ___ Deutsch.", ["lerne", "lernst", "lernt",
  "lernen"], "lerne", "ich + -e."),
 ("fill", "Du ___ gut Fußball.", ["spielst", "spiele", "spielt",
  "spielen"], "spielst", "du + -st."),
 ("fill", "Er ___ in Taschkent.", ["wohnt", "wohne", "wohnst",
  "wohnen"], "wohnt", "er/sie/es + -t."),
 ("fill", "Wir ___ Tee.", ["trinken", "trinke", "trinkst",
  "trinkt"], "trinken", "wir + -en."),
 ("error", "Sie (ular) lernt Englisch.",
  ["Sie", "lernt", "Englisch", "—"], "lernt",
  "Ko'plik sie + lernEN."),
 ("order", "Biz nemis tilini o'rganamiz.",
  ["Wir", "lernen", "Deutsch"], "Wir lernen Deutsch",
  "Ega + fe'l + til."),
]),
(4, B, "DE A1 BOSS — So'z tartibi (fe'l 2-o'rinda)", [
 ("fill", "Heute ___ ich zu Hause.", ["bleibe", "ich bleibe",
  "bleiben", "bleibst"], "bleibe",
  "Fe'l DOIM 2-o'rinda: Heute bleibe ich..."),
 ("fill", "Morgen ___ wir nach Berlin.",
  ["fahren", "wir fahren", "fährt", "fahre"], "fahren",
  "Morgen fahren wir — inversiya."),
 ("fill", "Am Abend ___ er Musik.", ["hört", "er hört", "hören",
  "hörst"], "hört", "Vaqt boshda — fe'l 2-o'rin, ega 3-o'rin."),
 ("fill", "___ du heute Zeit?", ["Hast", "Habst", "Hat", "Haben"],
  "Hast", "Savolda fe'l 1-o'rin: Hast du...?"),
 ("error", "Heute ich gehe ins Kino.", ["Heute", "ich", "gehe",
  "ins Kino"], "ich", "Heute GEHE ich — fe'l 2-o'rinda."),
 ("order", "Bugun biz kinoga boramiz.",
  ["Heute", "gehen", "wir", "ins", "Kino"],
  "Heute gehen wir ins Kino", "Vaqt + fe'l + ega + joy."),
]),
]

# ============================================================
#  NEMIS TILI — A2
# ============================================================
SEED_DE_A2 = [
(11, not B, "DE A2 — Perfekt (haben + Partizip II)", [
 ("fill", "Ich ___ Pizza gegessen.", ["habe", "bin", "hat",
  "hast"], "habe", "Ko'pchilik fe'llar haben bilan."),
 ("fill", "Wir ___ nach Samarkand gefahren.",
  ["sind", "haben", "ist", "habt"], "sind",
  "Harakat fe'llari sein bilan: sind gefahren."),
 ("fill", "Er hat das Buch ___ .", ["gelesen", "lesen", "liest",
  "gelest"], "gelesen", "lesen -> gelesen."),
 ("fill", "Sie ist früh ___ .", ["aufgestanden", "aufstehen",
  "aufgestehen", "gestanden auf"], "aufgestanden",
  "aufstehen -> ist aufgestanden."),
 ("error", "Ich bin Deutsch gelernt.", ["Ich", "bin", "Deutsch",
  "gelernt"], "bin", "lernen — haben bilan: Ich HABE gelernt."),
 ("order", "Men kecha futbol o'ynadim.",
  ["Ich", "habe", "gestern", "Fußball", "gespielt"],
  "Ich habe gestern Fußball gespielt",
  "haben 2-o'rin, Partizip oxirida."),
]),
(12, not B, "DE A2 — Akkusativ (den / einen)", [
 ("fill", "Ich sehe ___ Mann.", ["den", "der", "dem", "das"],
  "den", "Mujskoy rod Akkusativda: der -> den."),
 ("fill", "Sie kauft ___ Apfel.", ["einen", "ein", "eine",
  "einem"], "einen", "ein -> einen (erkak jins)."),
 ("fill", "Wir besuchen ___ Schule.", ["die", "der", "das",
  "den"], "die", "Ayol jins o'zgarmaydi: die."),
 ("fill", "Er trinkt ___ Wasser.", ["das", "den", "der", "dem"],
  "das", "O'rta jins o'zgarmaydi: das."),
 ("error", "Ich habe ein Bruder.", ["Ich", "habe", "ein",
  "Bruder"], "ein", "der Bruder -> einEN Bruder (Akkusativ)."),
 ("order", "Men bir it ko'ryapman.", ["Ich", "sehe", "einen",
  "Hund"], "Ich sehe einen Hund", "Akkusativ: einen Hund."),
]),
(13, not B, "DE A2 — Modalverben", [
 ("fill", "Ich ___ gut schwimmen.", ["kann", "kannst", "können",
  "könnt"], "kann", "ich kann."),
 ("fill", "Du ___ deine Hausaufgaben machen.",
  ["musst", "muss", "müssen", "musste"], "musst", "du musst."),
 ("fill", "___ ich das Fenster öffnen?",
  ["Darf", "Darfst", "Dürfen", "Durfte"], "Darf",
  "Ruxsat so'rash: Darf ich...?"),
 ("fill", "Wir ___ heute nicht kommen.",
  ["können", "kann", "kannst", "könnt"], "können", "wir können."),
 ("error", "Er kann gut kochen machen.",
  ["Er", "kann", "gut kochen", "machen"], "machen",
  "Modal + bitta infinitiv: Er kann gut kochen."),
 ("order", "Men nemischa gapira olaman.",
  ["Ich", "kann", "Deutsch", "sprechen"],
  "Ich kann Deutsch sprechen",
  "Modal 2-o'rin, infinitiv oxirida."),
]),
(14, B, "DE A2 BOSS — trennbare Verben", [
 ("fill", "Ich stehe um sieben Uhr ___ .",
  ["auf", "an", "aus", "ab"], "auf",
  "aufstehen: prefiks gap oxiriga."),
 ("fill", "Der Zug kommt um acht ___ .",
  ["an", "auf", "ein", "mit"], "an", "ankommen -> kommt... an."),
 ("fill", "Machst du das Licht ___ ?", ["an", "auf", "zu", "ab"],
  "an", "anmachen — yoqish."),
 ("fill", "Wir kaufen im Supermarkt ___ .",
  ["ein", "an", "auf", "aus"], "ein", "einkaufen -> kaufen... ein."),
 ("error", "Ich aufstehe um sechs.", ["Ich", "aufstehe", "um",
  "sechs"], "aufstehe", "Ajraladi: Ich stehe um sechs AUF."),
 ("order", "Men do'stimni chaqiraman (telefon).",
  ["Ich", "rufe", "meinen", "Freund", "an"],
  "Ich rufe meinen Freund an",
  "anrufen: rufe... an."),
]),
]

# ============================================================
#  KOREYS TILI — A1
# ============================================================
SEED_KO_A1 = [
(1, not B, "KO A1 — 은/는 (mavzu qo'shimchasi)", [
 ("fill", "저___ 학생입니다.", ["는", "은", "이", "가"], "는",
  "Unli bilan tugagan so'z + 는 (저는)."),
 ("fill", "선생님___ 친절합니다.", ["은", "는", "가", "를"], "은",
  "Undosh bilan tugagan so'z + 은 (선생님은)."),
 ("fill", "이것___ 책입니다.", ["은", "는", "이", "를"], "은",
  "이것 undosh bilan tugaydi: 이것은."),
 ("fill", "저는 우즈베키스탄 사람___.",
  ["입니다", "습니다", "합니다", "있습니다"], "입니다",
  "Ot + 입니다 = ...man/dir."),
 ("error", "저은 요리사입니다.", ["저은", "요리사", "입니다", "—"],
  "저은", "저 unli bilan tugaydi: 저는."),
 ("order", "Men o'qituvchiman.", ["저는", "선생님", "입니다"],
  "저는 선생님 입니다", "Mavzu + ot + 입니다."),
]),
(2, not B, "KO A1 — 이/가 (ega qo'shimchasi)", [
 ("fill", "책___ 있습니다.", ["이", "가", "은", "를"], "이",
  "Undoshdan keyin 이 (책이)."),
 ("fill", "사과___ 맛있습니다.", ["가", "이", "는", "을"], "가",
  "Unlidan keyin 가 (사과가)."),
 ("fill", "시간___ 없습니다.", ["이", "가", "은", "에"], "이",
  "시간 undosh bilan tugaydi: 시간이."),
 ("fill", "누구___ 왔습니까?", ["가", "이", "는", "를"], "가",
  "누구 + 가 = kim keldi?"),
 ("error", "물가 없습니다.", ["물가", "없습니다", "—", "—"],
  "물가", "물 undosh bilan tugaydi: 물이 없습니다."),
 ("order", "Do'stim bor.", ["친구가", "있습니다"], "친구가 있습니다",
  "Ega + 있습니다 (bor)."),
]),
(3, not B, "KO A1 — 있다 / 없다 (bor / yo'q)", [
 ("fill", "고양이가 ___ .", ["있습니다", "없습니다", "입니다",
  "합니다"], "있습니다", "Bor — 있습니다."),
 ("fill", "돈이 ___ . (pul yo'q)", ["없습니다", "있습니다",
  "입니다", "갑니다"], "없습니다", "Yo'q — 없습니다."),
 ("fill", "가방 안에 책이 ___ .", ["있습니다", "없습니다",
  "입니다", "옵니다"], "있습니다", "Sumka ichida kitob BOR."),
 ("fill", "학교에 학생이 많이 ___ .", ["있습니다", "없습니다",
  "입니다", "봅니다"], "있습니다", "Ko'p o'quvchi bor."),
 ("error", "저는 형이 입니다. (akam bor demoqchi)",
  ["저는", "형이", "입니다", "—"], "입니다",
  "Bor — 있습니다: 형이 있습니다."),
 ("order", "Menda savol bor.", ["질문이", "있습니다"],
  "질문이 있습니다", "Ot + 이/가 + 있습니다."),
]),
(4, B, "KO A1 BOSS — 을/를 va fe'l", [
 ("fill", "밥___ 먹습니다.", ["을", "를", "이", "은"], "을",
  "Undoshdan keyin 을 (밥을)."),
 ("fill", "커피___ 마십니다.", ["를", "을", "가", "는"], "를",
  "Unlidan keyin 를 (커피를)."),
 ("fill", "책___ 읽습니다.", ["을", "를", "이", "에"], "을",
  "책 undosh bilan tugaydi: 책을."),
 ("fill", "한국어___ 공부합니다.", ["를", "을", "가", "은"], "를",
  "한국어 unli bilan tugaydi: 한국어를."),
 ("error", "저는 물를 마십니다.", ["저는", "물를", "마십니다",
  "—"], "물를", "물 undosh bilan tugaydi: 물을."),
 ("order", "Men kitob o'qiyman.", ["저는", "책을", "읽습니다"],
  "저는 책을 읽습니다", "Ega + to'ldiruvchi + fe'l (SOV)."),
]),
]

# ============================================================
#  KOREYS TILI — A2
# ============================================================
SEED_KO_A2 = [
(11, not B, "KO A2 — 아요/어요 (hozirgi zamon)", [
 ("fill", "저는 학교에 ___ . (bormoq)", ["가요", "가어요", "갑요",
  "가아요"], "가요", "가다 -> 가요 (ㅏ dan keyin 아요 qo'shilib qisqaradi)."),
 ("fill", "저는 밥을 ___ . (yemoq)", ["먹어요", "먹아요", "먹요",
  "먹러요"], "먹어요", "ㅓ/boshqa unli -> 어요: 먹어요."),
 ("fill", "친구가 책을 ___ . (o'qimoq)", ["읽어요", "읽아요",
  "읽요", "읽러요"], "읽어요", "읽다 -> 읽어요."),
 ("fill", "저는 한국어를 ___ . (o'rganmoq)", ["공부해요",
  "공부하요", "공부어요", "공부아요"], "공부해요",
  "하다 -> 해요."),
 ("error", "저는 물을 마셔어요.", ["저는", "물을", "마셔어요",
  "—"], "마셔어요", "마시다 -> 마셔요 (bitta 어)."),
 ("order", "Men koreys tilini o'rganaman.",
  ["저는", "한국어를", "공부해요"], "저는 한국어를 공부해요",
  "SOV tartibi + 해요."),
]),
(12, not B, "KO A2 — 았/었어요 (o'tgan zamon)", [
 ("fill", "어제 학교에 ___ .", ["갔어요", "가았어요", "갔아요",
  "가요"], "갔어요", "가다 -> 갔어요."),
 ("fill", "아침에 빵을 ___ .", ["먹었어요", "먹았어요", "먹었요",
  "먹어요"], "먹었어요", "먹다 -> 먹었어요."),
 ("fill", "주말에 영화를 ___ .", ["봤어요", "보았요", "봤아요",
  "봐요"], "봤어요", "보다 -> 봤어요."),
 ("fill", "어제 한국어를 ___ .", ["공부했어요", "공부하았어요",
  "공부했아요", "공부해요"], "공부했어요", "하다 -> 했어요."),
 ("error", "어제 친구를 만나요.", ["어제", "친구를", "만나요",
  "—"], "만나요", "어제 — o'tgan zamon: 만났어요."),
 ("order", "Kecha men kitob o'qidim.",
  ["어제", "저는", "책을", "읽었어요"], "어제 저는 책을 읽었어요",
  "Vaqt + ega + to'ldiruvchi + o'tgan zamon fe'l."),
]),
(13, not B, "KO A2 — 에 / 에서 (joy qo'shimchalari)", [
 ("fill", "학교___ 가요. (maktabGA)", ["에", "에서", "를", "이"],
  "에", "Yo'nalish — 에."),
 ("fill", "도서관___ 공부해요. (kutubxonaDA harakat)",
  ["에서", "에", "을", "는"], "에서",
  "Harakat sodir bo'lgan joy — 에서."),
 ("fill", "집___ 있어요. (uyDA turibman)", ["에", "에서", "를",
  "가"], "에", "있다/없다 bilan joy — 에."),
 ("fill", "식당___ 밥을 먹어요.", ["에서", "에", "이", "은"],
  "에서", "Ovqatlanish — harakat: 에서."),
 ("error", "저는 학교에 공부해요.", ["저는", "학교에", "공부해요",
  "—"], "학교에", "Harakat joyi — 학교에서."),
 ("order", "Men kafeda kofe ichaman.",
  ["저는", "카페에서", "커피를", "마셔요"],
  "저는 카페에서 커피를 마셔요", "Ega + joy(에서) + obyekt + fe'l."),
]),
(14, B, "KO A2 BOSS — 안 / 지 않다 (inkor)", [
 ("fill", "저는 커피를 ___ 마셔요.", ["안", "못", "지", "는"],
  "안", "Oddiy inkor: 안 + fe'l."),
 ("fill", "밥을 먹___ 않아요.", ["지", "어", "게", "고"], "지",
  "Fe'l o'zagi + 지 않다."),
 ("fill", "주말에 일을 ___ 해요.", ["안", "못", "는", "이"], "안",
  "안 해요 — qilmayman."),
 ("fill", "그 영화를 보___ 않았어요.", ["지", "게", "어", "고"],
  "지", "보지 않았어요 — ko'rmadim."),
 ("error", "저는 고기를 먹 안 어요.", ["저는", "고기를", "먹 안 어요",
  "—"], "먹 안 어요", "안 fe'ldan OLDIN: 안 먹어요."),
 ("order", "Men televizor ko'rmayman.",
  ["저는", "텔레비전을", "안", "봐요"], "저는 텔레비전을 안 봐요",
  "안 fe'ldan oldin."),
]),
]


# Seed to'plamlari: (ma'lumot, daraja, til). Pastdagi _missing_sets
# shu ro'yxatni bazadagi holat bilan solishtiradi.
def _all_sets():
    return [
        (SEED_EN_C1, "C1", "en"),
        (SEED_EN_C2, "C2", "en"),
        (SEED_RU_A1, "A1", "ru"),
        (SEED_RU_A2, "A2", "ru"),
        (SEED_DE_A1, "A1", "de"),
        (SEED_DE_A2, "A2", "de"),
        (SEED_KO_A1, "A1", "ko"),
        (SEED_KO_A2, "A2", "ko"),
    ]


def _missing_sets(db):
    """Qaysi (til, daraja) juftligi bazada YO'Q — bitta so'rov bilan.

    NEGA MARKER YETMAYDI (2026-09-25, Jahongir: "programmada
    JonyStudentappda muammo koreys tiliga o'tmayabdi ekan").

    Ilgari bu seed "grammar_v3" markeri bilan bir marta ishlab,
    keyin QAYTA KIRMASDI. Faylga keyinchalik ru/de/ko qo'shilganda
    jonli bazaga tushmadi — marker allaqachon yozilgan edi. Yangi
    bazada (test) hammasi ishlaydi, jonli bazada esa koreys
    grammatikasi bo'sh qoladi. Aynan shu hol kuzatilgan.

    Endi marker emas, KONTENT tekshiriladi. Yangi til yoki daraja
    qo'shilsa o'zi tushadi; hammasi joyida bo'lsa bitta arzon
    so'rovdan keyin chiqib ketadi."""
    import models
    from sqlalchemy import func
    rows = (db.query(models.GrammarQuestion.language,
                     models.GrammarQuestion.level,
                     func.count(models.GrammarQuestion.id))
            .group_by(models.GrammarQuestion.language,
                      models.GrammarQuestion.level).all())
    have = {(lang, lvl) for lang, lvl, n in rows if n}
    return [s for s in _all_sets() if (s[2], s[1]) not in have]


def _seed_key() -> str:
    """Marker kaliti KONTENTDAN chiqadi.

    Shunda yangi til yoki daraja qo'shilsa kalit o'zi o'zgaradi va
    seed bir marta qayta ishlaydi. Hammasi joyida bo'lsa esa hech
    qanday so'rov yo'q — kalit xotiradagi ro'yxatdan tekshiriladi.
    Sxema barmoq izi bilan bir xil mantiq."""
    parts = sorted(f"{lang}-{level}" for _, level, lang in _all_sets())
    return "grammar_v3:" + ",".join(parts)


def seed_grammar_extra(db):
    """C1/C2 (en) + ru/de/ko A1/A2. Idempotent.

    Eski "grammar_v3" markeri kontentga bog'lanmagan edi: faylga
    yangi til qo'shilganda ham qulf ochilmasdi. Endi kalit
    kontentdan chiqadi, ustiga esa kontent tekshiruvi qo'yilgan."""
    from common import _seed_done, _seed_mark
    key = _seed_key()
    if _seed_done(db, key):
        return None
    todo = _missing_sets(db)
    if not todo:
        _seed_mark(db, key)
        return None
    import json
    import models

    have = {(t, p) for (t, p) in
            db.query(models.GrammarQuestion.topic,
                     models.GrammarQuestion.prompt).all()}
    made = 0

    def _add(seed, level, language):
        nonlocal made
        for order, is_boss, topic, questions in seed:
            for kind, prompt, options, answer, explain in questions:
                if (topic, prompt) in have:
                    continue
                db.add(models.GrammarQuestion(
                    topic=topic, level=level, language=language,
                    topic_order=order, is_boss=1 if is_boss else 0,
                    kind=kind, prompt=prompt,
                    options=json.dumps(options, ensure_ascii=False),
                    answer=answer, explain=explain))
                have.add((topic, prompt))
                made += 1

    # Faqat YETISHMAYOTGANI qo'shiladi — borini qayta yozmaydi
    for seed, level, language in todo:
        _add(seed, level, language)
        print(f"[grammar] {language} {level}: kontent qo'shildi")

    if made:
        db.commit()
    _seed_mark(db, key)
    return made
