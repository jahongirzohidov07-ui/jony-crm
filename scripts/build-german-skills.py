"""Original, locally authored German course skills; no generation services.

Run from any directory: python scripts/build-german-skills.py
The final week's material is original practice, not an official Goethe exam.
"""
import json
from pathlib import Path

ROWS = []

def add(title, reading, rq, listening_title, listening, lq, st, sm, sc, wt, wm, wc):
    no = len(ROWS) + 1
    level = 'A1' if no <= 24 else 'A2' if no <= 48 else 'B1'
    def questions(raw, kind):
        result = []
        for i, line in enumerate(raw.strip().splitlines(), 1):
            prompt, answer, explanation = line.split('|')
            result.append(dict(id=f'{no}-{kind}-{i}', prompt=prompt.strip(),
                               answers=[a.strip() for a in answer.split(' / ')],
                               explanation=explanation.strip()))
        return result
    language = {
        'A1': ['Sodda gaplarda fe’lni to‘g‘ri joylashtiring.', 'So‘zlarni tushunarli ayting va savolga mos javob bering.'],
        'A2': ['Gaplarni weil, dass yoki deshalb bilan mazmunan bog‘lang.', 'Voqea va rejalarni mos zamonlarda tushunarli ifodalang.'],
        'B1': ['Fikrni sabab va aniq misol bilan asoslang.', 'Bog‘lovchilar va mos murojaat shakli bilan izchil nutq tuzing.'],
    }
    writing_language = {
        'A1': ['Bosh harf, nuqta va fe’l shakllarini tekshiring.', 'Qisqa gaplarda kim, nima va qachon ekanini aniq yozing.'],
        'A2': ['Gaplarni bog‘lang va zamonlarni izchil qo‘llang.', 'Salomlashuv va yakunni matn turiga mos tanlang.'],
        'B1': ['Matnni kirish, asosiy qism va yakun bilan tashkil qiling.', 'Uslub, bog‘lovchilar va fe’l o‘rnini tekshiring.'],
    }
    ROWS.append(dict(no=no,
        reading=dict(title=title, text=reading, questions=questions(rq, 'r')),
        listening=dict(title=listening_title + ' — o‘qituvchi o‘qishi yoki sun’iy ovoz bilan mashq uchun matn; audio yozuv emas', text=listening, questions=questions(lq, 'l')),
        speaking=dict(task=st, model=sm, criteria=[sc, *language[level]]),
        writing=dict(task=wt, model=wm, criteria=[wc, *writing_language[level]])))

add('Hallo, ich bin Dilnoza',
'Ich heiße Dilnoza und komme aus Usbekistan. Jetzt wohne ich in Bonn. Ich bin zwanzig Jahre alt und lerne Deutsch. Mein Kurs ist am Montag. Im Kurs sitzt Anna neben mir. Sie kommt aus Polen. Wir sagen: Guten Morgen! Dann schreiben wir unsere Namen.',
'''Wie heißt die Erzählerin?|Dilnoza|„Ich heiße Dilnoza“ — hikoyachining ismi Dilnoza.
Wo wohnt Dilnoza jetzt?|In Bonn|„Jetzt wohne ich in Bonn“ — hozir Bonnda yashaydi.
Woher kommt Anna?|Aus Polen|„Sie kommt aus Polen“ — Anna Polshadan.''',
'Eine neue Stimme im Kurs',
'Guten Tag! Mein Name ist Karim. Ich bin dreiundzwanzig Jahre alt. Ich komme aus Samarkand und wohne jetzt in Berlin. Meine Lehrerin heißt Frau Weber. Wir lernen heute Namen. Mein Nachbar heißt Leo. Er spricht Deutsch und Englisch. Ich spreche Usbekisch und ein bisschen Deutsch.',
'''Wie alt ist Karim?|Dreiundzwanzig Jahre|„Dreiundzwanzig“ — yigirma uch.
Wie heißt die Lehrerin?|Frau Weber|„Meine Lehrerin heißt Frau Weber“ — o‘qituvchining familiyasi Weber.
Woher kommt Karim?|Aus Samarkand|„Ich komme aus Samarkand“ — u Samarqanddan.''',
'O‘zingizni 4–5 sodda gap bilan tanishtiring: ism, yosh, kelib chiqish joyi va hozirgi shahar.',
'Hallo! Ich heiße Aziz. Ich bin neunzehn Jahre alt. Ich komme aus Taschkent. Jetzt wohne ich in Köln. Ich lerne Deutsch.',
'Ism, yosh va ikkita joy haqidagi ma’lumotni ayting.',
'Kursdagi ism kartangiz uchun o‘zingiz haqingizda 4 ta gap yozing.',
'Ich heiße Malika. Ich komme aus Buchara. Ich wohne in Hamburg. Ich spreche Usbekisch und lerne Deutsch.',
'Kartada ism, kelib chiqish joyi, yashash joyi va til bo‘lsin.')

add('Ein Name mit sechs Buchstaben',
'Im Sprachbüro fragt Herr Lang nach meinem Namen. Ich heiße Sabina. Er schreibt zuerst Sabrina. Ich sage langsam: S, A, B, I, N, A. Jetzt ist der Name richtig. Meine Freundin heißt Madina. Ihr Name hat auch sechs Buchstaben. Wir bekommen zwei Karten für den Kurs.',
'''Wie heißt die Erzählerin richtig?|Sabina|To‘g‘ri ism Sabina; Sabrina xato yozilgan variant.
Wie viele Buchstaben hat Madinas Name?|Sechs|„Auch sechs Buchstaben“ — Madina ismida ham olti harf bor.
Was bekommen die Freundinnen?|Zwei Karten|Oxirida ular kurs uchun ikkita karta olishadi.''',
'Die Telefonnummer',
'Hallo, hier ist Emil aus dem Deutschkurs. Ist das deine Tasche? Sie ist blau. Auf der Tasche steht Nora. Bitte ruf mich an. Meine Nummer ist null eins sieben, vier zwei, acht acht, sechs drei. Ich bin heute bis fünf Uhr in der Schule. Bis später!',
'''Welche Farbe hat die Tasche?|Blau|„Sie ist blau“ — sumka ko‘k.
Welcher Name steht auf der Tasche?|Nora|Sumkada Nora ismi yozilgan.
Bis wann ist Emil in der Schule?|Bis fünf Uhr|„Bis fünf Uhr“ — soat beshgacha.''',
'Juftlikda ismingizni ayting, harflab bering va suhbatdoshingizdan ismini so‘rang.',
'A: Wie heißt du? B: Ich heiße Otabek. A: Wie schreibt man das? B: O, T, A, B, E, K. Und wie heißt du?',
'Ismni harflang va qarshi savol bering.',
'Yo‘qolgan sumka haqida 3–4 gaplik xabar yozing: rang, undagi ism va topilgan joy.',
'Hier ist eine Tasche. Sie ist rot. Auf der Tasche steht Lina. Die Tasche ist im Kursraum.',
'Rang, ism va joyni aniq ko‘rsating.')

add('Menschen im Sprachcafé',
'Im Sprachcafé sitzen vier Personen. Omar ist aus Marokko. Er spricht Arabisch und Französisch. Julia kommt aus Spanien und spricht Spanisch. Ich spreche Usbekisch. Unsere gemeinsame Sprache ist heute Deutsch. Wir trinken Tee und fragen: Woher kommst du? Eine Landkarte hängt neben der Tür.',
'''Wie viele Personen sitzen im Sprachcafé?|Vier|„Vier Personen“ — to‘rt kishi.
Woher kommt Julia?|Aus Spanien|Julia Ispaniyadan kelgan.
Welche Sprache sprechen alle heute gemeinsam?|Deutsch|Bugungi umumiy muloqot tili nemis tili.''',
'Am Empfang',
'Mitarbeiterin: Guten Abend. Sprechen Sie Deutsch? Gast: Ja, ein bisschen. Ich heiße Pavel und komme aus Prag. Mitarbeiterin: Willkommen! Ihr Zimmer ist Nummer acht. Gast: Danke. Ist das Café offen? Mitarbeiterin: Ja, das Café ist hier rechts. Gast: Sehr gut. Ich möchte einen Tee.',
'''Woher kommt Pavel?|Aus Prag|Pavel „Ich komme aus Prag“ deydi.
Welche Zimmernummer hat Pavel?|Acht / Nummer acht|Unga sakkizinchi xona beriladi.
Wo ist das Café?|Rechts|„Hier rechts“ — shu yerda o‘ng tomonda.''',
'Mehmonxona xodimi bilan rasmiy salomlashib, ismingiz va biladigan tillaringizni ayting.',
'Guten Abend. Ich heiße Lola Akbarova. Ich spreche Usbekisch und Russisch. Ich spreche auch ein bisschen Deutsch. Sprechen Sie Englisch?',
'Rasmiy Sie shakli va kamida ikkita til nomidan foydalaning.',
'Til almashish guruhi uchun 4–5 gapli tanishtiruv yozing.',
'Hallo zusammen! Ich heiße Rustam. Ich komme aus Usbekistan und wohne in Bremen. Ich spreche Usbekisch und Russisch. Ich lerne jetzt Deutsch.',
'Kelib chiqish joyingizni va o‘rganayotgan tilingizni yozing.')

add('Meine kleine Familie',
'Meine Familie wohnt in Fergana. Mein Vater heißt Anvar und ist Koch. Meine Mutter heißt Saida und ist Lehrerin. Ich habe einen Bruder. Er heißt Ali und ist zwölf. Wir haben keine Schwester. Am Sonntag essen wir zusammen. Unsere Großmutter kommt auch. Sie bringt immer Brot mit.',
'''Was ist Anvars Beruf?|Koch|„Mein Vater ... ist Koch“ — otasi oshpaz.
Wie alt ist Ali?|Zwölf|„Er ... ist zwölf“ — Ali o‘n ikki yoshda.
Wer bringt Brot mit?|Die Großmutter|Buvi har doim non olib keladi.''',
'Ein Familienfoto',
'Das ist mein Foto. Links ist meine Schwester Eva. Sie ist fünfzehn und geht zur Schule. Rechts steht mein Vater. Er heißt Paul. In der Mitte sitzt meine Mutter. Unser Hund liegt vor ihr. Ich bin nicht auf dem Foto. Ich mache das Foto mit meinem Handy.',
'''Wie heißt die Schwester?|Eva|Chapdagi singilning ismi Eva.
Wer sitzt in der Mitte?|Die Mutter|„In der Mitte sitzt meine Mutter“ — o‘rtada onasi o‘tiribdi.
Wer macht das Foto?|Der Erzähler / Die erzählende Person|„Ich mache das Foto“ — gapirayotgan odam suratga olyapti.''',
'Oila a’zolaringizdan ikki kishini tanishtiring; ism, qarindoshlik va yosh yoki kasbini ayting.',
'Das ist meine Mutter. Sie heißt Nargiza und ist Ärztin. Das ist mein Bruder. Er heißt Timur und ist zehn Jahre alt.',
'Ikki odamning qarindoshlik aloqasini tushuntiring.',
'Do‘stingizga oilangiz haqida 4–5 gap yozing; haqiqiy yoki o‘ylab topilgan oila bo‘lishi mumkin.',
'Meine Familie ist klein. Mein Vater heißt Akmal. Meine Mutter heißt Dilorom. Ich habe eine Schwester. Sie ist acht Jahre alt.',
'Kamida uchta oila a’zosini yoki oilaviy holatni tasvirlang.')

add('Besuch bei Tante Leyla',
'Heute besuchen wir meine Tante Leyla. Sie wohnt mit ihrem Mann in einer kleinen Stadt. Ihr Sohn heißt Murad. Er ist mein Cousin. Murad hat ein neues Fahrrad. Wir fahren zusammen zum Park. Meine Eltern bleiben bei Leyla. Am Abend trinken alle im Garten Tee.',
'''Wie heißt die Tante?|Leyla|Matnda xolaning ismi Leyla deb berilgan.
Wer ist Murad für den Erzähler?|Sein Cousin / Der Cousin|„Er ist mein Cousin“ — Murad uning xolavachchasi.
Wohin fahren die Kinder?|Zum Park|Ular birga parkka borishadi.''',
'Wer gehört zur Familie?',
'Mila: Ist Ben dein Bruder? Jonas: Nein, Ben ist mein Cousin. Mein Bruder heißt Max. Mila: Und wer ist die Frau neben Ben? Jonas: Das ist seine Mutter, meine Tante. Sie heißt Rita. Mila: Wohnt sie hier? Jonas: Nein, sie wohnt in Wien. Sie besucht uns heute.',
'''Wie heißt Jonas’ Bruder?|Max|Jonasning akasi yoki ukasi Max, Ben esa amakivachchasi.
Wie heißt Bens Mutter?|Rita|Benning onasi Rita deb ataladi.
Wo wohnt Rita?|In Wien|„Sie wohnt in Wien“ — Rita Venada yashaydi.''',
'Oddiy oila daraxti chizing va undagi qarindoshlikni mein, meine, sein, seine bilan tushuntiring.',
'Das ist mein Onkel. Seine Frau heißt Nadja. Ihr Sohn heißt Bek. Bek ist mein Cousin. Seine Schwester heißt Lola.',
'Egalik so‘zlari bilan kamida ikkita aloqani to‘g‘ri ayting.',
'Qarindoshingizga qisqa tashrif xabari yozing: kim bilan va qachon kelasiz?',
'Hallo Tante Rita! Ich komme am Sonntag. Mein Bruder kommt auch. Wir bringen Brot mit. Bis Sonntag! Liebe Grüße, Jonas',
'Xabarda tashrif kuni va hamrohingiz ko‘rsatilsin.')

add('Ein Geschenk für Papa',
'Mein Vater hat heute Geburtstag. Er wird vierzig. Meine Schwester kauft eine Tasse. Auf der Tasse steht Papa. Ich mache einen Kuchen. Unsere Mutter kauft Blumen. Um sechs kommen zwei Freunde. Wir singen zusammen. Mein Vater freut sich und macht ein Foto von uns und dem Kuchen.',
'''Wie alt wird der Vater?|Vierzig|„Er wird vierzig“ — otasi qirq yoshga kiradi.
Was kauft die Schwester?|Eine Tasse|Opa yoki singil piyola sotib oladi.
Wann kommen die Freunde?|Um sechs|Do‘stlar soat oltida kelishadi.''',
'Die Einladung',
'Hallo Nuri, am Samstag habe ich Geburtstag. Ich werde achtzehn. Meine kleine Feier beginnt um vier Uhr bei mir zu Hause. Meine Adresse ist Gartenstraße neun. Wir essen Pizza und hören Musik. Bring bitte keine Geschenke mit. Ein Spiel ist eine gute Idee. Kommst du? Schreib mir bitte. Deine Lea.',
'''An welchem Tag feiert Lea?|Am Samstag|Lea tug‘ilgan kunini shanba kuni nishonlaydi.
Wann beginnt die Feier?|Um vier Uhr|Bayram soat to‘rtda boshlanadi.
Was essen die Gäste?|Pizza|„Wir essen Pizza“ — mehmonlar pitsa yeyishadi.''',
'Tug‘ilgan kunga og‘zaki taklif qiling va kelish-kelmaslik haqida javob bering.',
'A: Ich habe am Freitag Geburtstag. Kommst du um fünf? B: Ja, gern. Was bringe ich mit? A: Bring bitte ein Spiel mit.',
'Kun, vaqt va taklifga javobni kiriting.',
'Do‘stingizga 4–5 gap bilan tug‘ilgan kun taklifini yozing.',
'Hallo Emma! Am Sonntag habe ich Geburtstag. Die Feier beginnt um drei Uhr bei mir. Wir essen Kuchen. Kommst du? Liebe Grüße, Aziz',
'Taklifda sana yoki kun, boshlanish vaqti va joy bo‘lsin.')

add('Ein früher Kurs',
'Mein Deutschkurs beginnt um acht Uhr. Ich stehe um sechs Uhr auf. Um halb sieben frühstücke ich. Der Bus kommt um Viertel nach sieben. Ich bin um Viertel vor acht in der Schule. Vor dem Unterricht spreche ich mit Tom. Er kommt immer zu Fuß und ist pünktlich.',
'''Wann beginnt der Deutschkurs?|Um acht Uhr|Kurs 8:00 da boshlanadi.
Wann frühstückt die Erzählerin?|Um halb sieben / Um sechs Uhr dreißig|„Halb sieben“ — 6:30, yetti yarim emas.
Wie kommt Tom zur Schule?|Zu Fuß|„Zu Fuß“ — piyoda.''',
'Eine neue Uhrzeit',
'Guten Morgen, hier ist Frau Klein von der Sprachschule. Unser Kurs beginnt morgen nicht um neun, sondern um zehn Uhr. Der Raum bleibt gleich: Raum zwölf im ersten Stock. Bitte bringen Sie Ihr Buch mit. Die Pause ist um halb zwölf. Der Unterricht endet um ein Uhr. Vielen Dank.',
'''Wann beginnt der Kurs morgen?|Um zehn Uhr|Boshlanish vaqti 9:00 dan 10:00 ga o‘zgargan.
In welchem Raum ist der Kurs?|In Raum zwölf|Xona o‘zgarmaydi: 12-xona.
Wann ist die Pause?|Um halb zwölf / Um elf Uhr dreißig|„Halb zwölf“ — 11:30.''',
'Juftlikda uchta faoliyatning vaqtini so‘rang va javob bering; halb va Viertel shakllarini ishlating.',
'A: Wann frühstückst du? B: Um halb acht. A: Wann beginnt dein Kurs? B: Um Viertel nach neun. A: Wann gehst du nach Hause? B: Um zwölf.',
'Uch vaqtni to‘g‘ri ayting, kamida bittasida halb ishlating.',
'Ertalabki rejangizni vaqtlar bilan 4 gapda yozing.',
'Ich stehe um sieben Uhr auf. Um halb acht frühstücke ich. Um acht nehme ich den Bus. Mein Kurs beginnt um halb neun.',
'Vaqtlar ketma-ketligini saqlang.')

add('Meine Woche auf Papier',
'An meiner Wand hängt ein Wochenplan. Am Montag und Mittwoch lerne ich Deutsch. Am Dienstag spiele ich Fußball. Donnerstags arbeite ich im Café. Am Freitag kaufe ich ein. Das Wochenende ist frei. Samstags schlafe ich lange. Am Sonntag besuche ich meine Eltern. Für mich ist der Sonntag besonders schön.',
'''An welchen Tagen lernt die Person Deutsch?|Am Montag und Mittwoch|Rejada nemis tili dushanba va chorshanba kunlari.
Wo arbeitet die Person donnerstags?|Im Café|Payshanba kuni kafeda ishlaydi.
Wen besucht die Person sonntags?|Die Eltern / Ihre Eltern|Yakshanba kuni ota-onasini ko‘radi.''',
'Zeit für einen Kaffee',
'Aylin: Hast du am Dienstag Zeit? Ben: Nein, da arbeite ich. Aylin: Und am Mittwoch? Ben: Da habe ich Deutschkurs. Aber am Donnerstag bin ich frei. Aylin: Gut! Treffen wir uns um drei im Café am Markt? Ben: Gern. Ich komme mit dem Fahrrad. Aylin: Bis Donnerstag!',
'''Wann hat Ben Deutschkurs?|Am Mittwoch|Benning nemis tili kursi chorshanba kuni.
An welchem Tag treffen sich beide?|Am Donnerstag|Ikkalasi payshanbaga kelishishadi.
Wo treffen sie sich?|Im Café am Markt|Uchrashuv bozor yonidagi kafeda.''',
'Bir hafta ichida uchrashuv uchun bo‘sh kun toping; avval bitta taklifni rad etib, boshqa kun ayting.',
'A: Hast du am Montag Zeit? B: Leider nicht. Ich arbeite. Geht es am Freitag? A: Ja. Um vier? B: Das passt gut.',
'Rad etishdan keyin muqobil kun taklif qiling.',
'Do‘stingizga haftadagi ikki band kuningiz va bitta bo‘sh kuningiz haqida yozing.',
'Hallo Sam! Am Montag lerne ich Deutsch. Am Dienstag arbeite ich. Am Mittwoch habe ich Zeit. Treffen wir uns dann? Liebe Grüße, Lena',
'Band va bo‘sh kunlarni ajratib ko‘rsating.')

add('Sonntag ohne Wecker',
'Heute ist Sonntag. Mein Wecker bleibt aus. Ich stehe erst um neun auf und frühstücke mit meiner Schwester. Danach lesen wir. Um zwölf kochen wir Reis und Gemüse. Am Nachmittag gehen wir spazieren. Es regnet nicht. Abends rufe ich meine Eltern an. Um zehn gehe ich ins Bett.',
'''Wann steht die Person auf?|Um neun|Yakshanba kuni to‘qqizda turadi.
Was kochen die Geschwister?|Reis und Gemüse|Ular guruch va sabzavot pishirishadi.
Wen ruft die Person abends an?|Die Eltern / Ihre Eltern|Kechqurun ota-onasiga telefon qiladi.''',
'Eine kurze Pause',
'Hallo, ich bin Sara. Heute arbeite ich von acht bis zwölf. Jetzt ist Mittag. Ich esse ein Brot und trinke Wasser. Meine Kollegin sitzt neben mir. Wir sprechen über das Wochenende. Um eins arbeite ich weiter. Um vier fahre ich nach Hause. Dann habe ich Zeit für meine Katze.',
'''Wann beginnt Sara mit der Arbeit?|Um acht|Sara ishni soat sakkizda boshlaydi.
Was trinkt Sara mittags?|Wasser|Tushlikda suv ichadi.
Welches Tier hat Sara?|Eine Katze|„Meine Katze“ — uning mushugi bor.''',
'Ish kuni va dam olish kuningizni 5–6 gap bilan solishtiring.',
'Am Montag stehe ich um sechs auf. Ich arbeite bis vier. Am Sonntag schlafe ich lange. Ich frühstücke um neun. Danach lese ich. Abends telefoniere ich mit meiner Familie.',
'Ish kuni va dam olish kuni uchun alohida vaqtlar ayting.',
'Dam olish kuningiz haqida avval, keyin va kechqurun tartibida 5 ta gap yozing.',
'Am Samstag stehe ich um acht auf. Zuerst frühstücke ich. Danach kaufe ich ein. Am Nachmittag spiele ich Fußball. Abends sehe ich einen Film.',
'Zuerst va danach bilan ketma-ketlik yarating.')

add('Das Fahrrad wartet',
'Jeden Morgen fährt Deniz mit dem Fahrrad zur Arbeit. Heute ist sein Fahrrad kaputt. Er nimmt den Bus. An der Haltestelle trifft er seine Nachbarin. Sie arbeitet auch im Zentrum. Zusammen fahren sie zwanzig Minuten. Nach der Arbeit repariert Deniz das Fahrrad. Sein Bruder hilft ihm dabei.',
'''Was ist heute kaputt?|Das Fahrrad|Bugun Denizning velosipedi buzilgan.
Wen trifft Deniz an der Haltestelle?|Seine Nachbarin|U bekatda qo‘shni ayolni uchratadi.
Wer hilft bei der Reparatur?|Sein Bruder|Ta’mirlashda uning akasi yoki ukasi yordam beradi.''',
'Morgens zu Hause',
'Ich heiße Julia. Mein Arbeitstag beginnt früh. Um halb sechs klingelt der Wecker. Ich mache das Fenster auf und ziehe mich an. Mein Mann macht Kaffee. Unser Sohn schläft noch. Um sechs verlasse ich das Haus. Ich arbeite in einer Bäckerei. Dort verkaufe ich Brot und Brötchen.',
'''Wann klingelt der Wecker?|Um halb sechs / Um fünf Uhr dreißig|Budilnik 5:30 da jiringlaydi.
Wer macht Kaffee?|Julias Mann / Ihr Mann|Kofeni Juliyaning eri tayyorlaydi.
Wo arbeitet Julia?|In einer Bäckerei|Julia nonvoyxonada ishlaydi.''',
'Ertalab qiladigan ishlaringizni aufstehen, anziehen va verlassen bilan tushuntiring.',
'Ich stehe um halb sieben auf. Dann ziehe ich mich an. Ich esse ein Brötchen und trinke Tee. Um Viertel nach sieben verlasse ich das Haus.',
'Ajraladigan fe’lda old qo‘shimchani gap oxiriga qo‘ying.',
'Uy sherigingizga ertangi erta ketishingiz haqida qisqa izoh yozing.',
'Hallo Jan! Morgen stehe ich um fünf auf. Ich arbeite früh. Um halb sechs verlasse ich die Wohnung. Dein Frühstück steht im Kühlschrank. Bis später!',
'Uyg‘onish va ketish vaqtini hamda bir foydali ma’lumotni yozing.')

add('Nach dem Unterricht',
'Nach dem Deutschkurs geht Farida nicht sofort nach Hause. Sie bleibt in der Bibliothek und lernt neue Wörter. Ihr Freund Leon kommt um drei. Sie machen zusammen Hausaufgaben. Danach spielt Farida im Park Volleyball. Leon spielt nicht mit. Er liest auf einer Bank. Um sechs fahren beide nach Hause.',
'''Wo lernt Farida neue Wörter?|In der Bibliothek|Farida kutubxonada yangi so‘zlarni o‘rganadi.
Wann kommt Leon?|Um drei|Leon soat uchda keladi.
Welchen Sport macht Farida?|Volleyball|U parkda voleybol o‘ynaydi.''',
'Ein freier Abend',
'Murat: Was machst du heute Abend? Nina: Ich höre Musik und zeichne. Und du? Murat: Ich möchte schwimmen. Das Schwimmbad schließt um neun. Kommst du mit? Nina: Heute nicht. Ich bin müde. Aber morgen gehe ich gern mit. Murat: Gut, dann schwimme ich heute allein und morgen mit dir.',
'''Was macht Nina heute neben Musikhören?|Sie zeichnet / Zeichnen|Nina musiqa tinglaydi va rasm chizadi.
Wann schließt das Schwimmbad?|Um neun|Basseyn soat to‘qqizda yopiladi.
Warum kommt Nina heute nicht mit?|Sie ist müde|„Ich bin müde“ — u charchagan.''',
'Uchta sevimli mashg‘ulotingizni ayting va sherigingizni biriga taklif qiling.',
'Ich lese gern und zeichne oft. Am Wochenende schwimme ich. Schwimmst du auch gern? Kommst du am Samstag mit ins Schwimmbad?',
'Gern yoki oft bilan odatni ayting va taklif bering.',
'Bugungi kechki rejangizni do‘stingizga yozing va undan rejalarini so‘rang.',
'Hallo Nina! Heute Abend höre ich Musik. Danach lese ich ein Buch. Um zehn gehe ich schlafen. Was machst du heute? Liebe Grüße, Murat',
'Kamida ikkita faoliyat va bitta savol kiriting.')

add('Ein Tag mit vielen Aufgaben',
'Am Freitag hat Jasur viel zu tun. Er bringt seine Tochter zur Schule. Dann arbeitet er bis Mittag. Um zwei kauft er Lebensmittel. Zu Hause kocht er Suppe und räumt die Küche auf. Seine Tochter deckt den Tisch. Nach dem Essen spielen sie Karten. Die Arbeit ist jetzt fertig.',
'''Wen bringt Jasur zur Schule?|Seine Tochter|Jasur qizini maktabga olib boradi.
Was kocht er?|Suppe|U sho‘rva pishiradi.
Wer deckt den Tisch?|Seine Tochter|Dasturxonni uning qizi tayyorlaydi.''',
'Wer macht was?',
'Oleg: Ich muss heute einkaufen und kochen. Kannst du die Küche aufräumen? Mia: Ja, gern. Ich wasche auch die Tassen. Oleg: Danke. Wir essen um sieben. Mia: Kommt deine Schwester? Oleg: Ja, sie bringt Salat mit. Mia: Gut. Dann brauchen wir nur Brot und etwas Käse.',
'''Wer räumt die Küche auf?|Mia|Mia oshxonani yig‘ishtirishga rozi bo‘ladi.
Wann essen die Personen?|Um sieben|Ular soat yettida ovqatlanishadi.
Was bringt Olegs Schwester mit?|Salat|Olegning opasi yoki singlisi salat olib keladi.''',
'Uy ishlarini sherigingiz bilan bo‘lishing: bir ishni o‘zingiz oling va bittasini undan so‘rang.',
'Ich kaufe heute ein und koche. Kannst du bitte den Tisch decken? Nach dem Essen wasche ich die Teller. Räumst du dann die Küche auf?',
'Vazifalarni kim bajarishini aniq kelishib oling.',
'Uy sherigingiz uchun uchta uy ishi va ovqatlanish vaqti bor xabar yozing.',
'Hallo Mia! Ich kaufe Brot und koche Suppe. Bitte deck den Tisch. Wir essen um sechs. Danach räume ich die Küche auf. Danke! Oleg',
'Ishlar va ovqatlanish vaqtini ko‘rsating.')

add('Unsere neue Wohnung',
'Wir wohnen jetzt in einer Wohnung im zweiten Stock. Sie hat drei Zimmer, eine Küche und ein Bad. Mein Zimmer ist klein, aber hell. Im Wohnzimmer steht ein großer Tisch. Der Balkon ist neben der Küche. Dort stehen zwei Stühle. Am Morgen trinken wir auf dem Balkon Tee.',
'''In welchem Stock liegt die Wohnung?|Im zweiten Stock|Kvartira ikkinchi qavatda joylashgan.
Wie viele Zimmer hat die Wohnung?|Drei|„Drei Zimmer“ — uchta xona.
Wo trinken die Bewohner morgens Tee?|Auf dem Balkon|Ertalab choyni balkonda ichishadi.''',
'Eine Wohnung ansehen',
'Vermieterin: Hier ist das Wohnzimmer. Es ist sehr ruhig. Interessent: Gibt es ein Schlafzimmer? Vermieterin: Ja, links. Das Bad ist rechts. Interessent: Hat die Wohnung einen Balkon? Vermieterin: Nein, aber einen kleinen Garten. Interessent: Schön! Wie hoch ist die Miete? Vermieterin: Sechshundert Euro im Monat, ohne Strom.',
'''Wo ist das Schlafzimmer?|Links|Yotoqxona chap tomonda.
Was hat die Wohnung statt eines Balkons?|Einen kleinen Garten|Balkon o‘rniga kichik bog‘i bor.
Wie hoch ist die monatliche Miete ohne Strom?|Sechshundert Euro / 600 Euro|Elektr to‘lovisiz ijara oyiga 600 yevro.''',
'Uyingizdagi uchta xonani tasvirlang va eng yoqqan xonangizni ayting.',
'Meine Wohnung hat zwei Zimmer. Das Wohnzimmer ist groß. Das Schlafzimmer ist klein und ruhig. Die Küche ist hell. Ich mag die Küche sehr.',
'Uchta xona nomi va kamida ikkita sifat ishlating.',
'Do‘stingizga yangi uyingiz haqida 5 ta gap yozing.',
'Ich wohne jetzt im ersten Stock. Meine Wohnung hat zwei Zimmer. Die Küche ist klein. Das Wohnzimmer ist hell. Es gibt auch einen Balkon.',
'Qavat, xonalar va bitta qulaylikni yozing.')

add('Wo ist der Schlüssel?',
'Nora sucht ihren Schlüssel. Auf dem Tisch liegt nur ein Buch. Unter dem Stuhl steht ihre Tasche. In der Tasche ist der Schlüssel nicht. Ihr Bruder schaut neben das Sofa. Dort liegt ein Ball. Endlich sieht Nora den Schlüssel: Er liegt auf dem Regal, direkt neben der Lampe.',
'''Was sucht Nora?|Ihren Schlüssel / Den Schlüssel|Nora kalitini qidiradi.
Wo steht ihre Tasche?|Unter dem Stuhl|Sumkasi stul ostida turibdi.
Wo liegt der Schlüssel?|Auf dem Regal|Kalit javonning ustida, chiroq yonida.''',
'Das Zimmer einrichten',
'Tom: Wohin stellen wir den Tisch? Eda: Bitte ans Fenster. Dort ist es hell. Tom: Und das Bett? Eda: An die Wand, neben den Schrank. Tom: Der Stuhl steht noch im Flur. Eda: Stell ihn bitte vor den Tisch. Tom: Gut. Jetzt fehlt nur noch eine Lampe.',
'''Wohin soll der Tisch?|Ans Fenster|Stolni deraza yoniga qo‘yish kerak.
Neben welches Möbelstück kommt das Bett?|Neben den Schrank|Karavot shkaf yoniga qo‘yiladi.
Was fehlt am Ende noch?|Eine Lampe|Oxirida hali chiroq yetishmaydi.''',
'Xonadagi uchta buyumning joyini auf, unter va neben bilan ayting.',
'Das Buch liegt auf dem Tisch. Meine Tasche steht unter dem Stuhl. Die Lampe steht neben dem Bett. Der Schlüssel liegt im Regal.',
'Kamida uchta joylashuvni to‘g‘ri tasvirlang.',
'Mehmoningizga kitob, sochiq va kalitni qayerdan topishini yozing.',
'Das Buch liegt auf dem Tisch. Dein Handtuch liegt auf dem Bett. Der Schlüssel ist in der Küche, neben der Tür. Willkommen bei uns!',
'Uch buyum uchun aniq joy ko‘rsating.')

add('Eine nette Nachbarin',
'Im Haus wohnt Frau Winter neben uns. Sie ist siebzig und lebt allein. Jeden Dienstag bringe ich ihr Milch vom Supermarkt mit. Heute lädt sie mich zum Tee ein. Ihre Katze schläft auf dem Sofa. Frau Winter zeigt mir alte Fotos. Wir sprechen eine Stunde und lachen viel.',
'''Wie alt ist Frau Winter?|Siebzig|Frau Winter yetmish yoshda.
Was bringt die Person ihr dienstags mit?|Milch|Har seshanba unga sut olib keladi.
Was zeigt Frau Winter?|Alte Fotos|U eski suratlarni ko‘rsatadi.''',
'Bitte etwas leiser',
'Nachbar: Guten Abend. Entschuldigung, die Musik ist sehr laut. Bewohnerin: Oh, tut mir leid. Wir feiern meinen Geburtstag. Nachbar: Alles Gute! Ich muss morgen früh arbeiten. Bewohnerin: Ich mache die Musik jetzt leiser. Um zehn ist die Feier zu Ende. Nachbar: Vielen Dank und noch einen schönen Abend.',
'''Was ist zu laut?|Die Musik|Qo‘shni musiqaning balandligidan shikoyat qiladi.
Warum braucht der Nachbar Ruhe?|Er muss morgen früh arbeiten|U ertaga erta ishlashi kerak.
Wann endet die Feier?|Um zehn|Bayram soat o‘nda tugaydi.''',
'Qo‘shningizdan muloyimlik bilan shovqinni kamaytirishni so‘rang; qo‘shni sifatida javob ham bering.',
'A: Entschuldigung, die Musik ist sehr laut. Ich möchte schlafen. B: Tut mir leid. Ich mache sie sofort leiser. A: Vielen Dank. Gute Nacht!',
'Uzr, iltimos va mos javob shakllarini ishlating.',
'Yangi qo‘shningizni shanba kuni choyga taklif qiladigan kichik xat yozing.',
'Liebe Frau Winter, wir sind Ihre neuen Nachbarn. Wir wohnen neben Ihnen. Kommen Sie am Samstag um vier zum Tee? Wir freuen uns. Familie Karimov',
'O‘zingizni tanishtiring va taklif vaqtini yozing.')

add('Auf dem Wochenmarkt',
'Am Samstag geht Malika auf den Markt. Sie braucht zwei Kilo Kartoffeln und ein Kilo Äpfel. Die Äpfel kosten drei Euro pro Kilo. Der Verkäufer gibt ihr einen Apfel zum Probieren. Er ist süß. Malika kauft auch sechs Eier. Alles kommt in ihre große Tasche aus Stoff.',
'''Wie viele Kartoffeln braucht Malika?|Zwei Kilo|Unga ikki kilogramm kartoshka kerak.
Was kostet ein Kilo Äpfel?|Drei Euro|Bir kilogramm olma uch yevro turadi.
Wie viele Eier kauft sie?|Sechs|Malika oltita tuxum sotib oladi.''',
'An der Gemüsetheke',
'Verkäufer: Was möchten Sie? Kunde: Ein Kilo Tomaten bitte. Verkäufer: Sonst noch etwas? Kunde: Ja, zwei Gurken. Haben Sie auch Zitronen? Verkäufer: Ja, hier. Kunde: Dann nehme ich drei. Verkäufer: Das macht zusammen sieben Euro. Kunde: Hier sind zehn Euro. Verkäufer: Danke, drei Euro zurück.',
'''Wie viele Gurken kauft der Kunde?|Zwei|Xaridor ikkita bodring oladi.
Wie viele Zitronen nimmt er?|Drei|U uchta limon oladi.
Wie viel kostet alles zusammen?|Sieben Euro|Jami narx yetti yevro.''',
'Bozorda uchta mahsulotni miqdori bilan so‘rang va umumiy narxni aniqlang.',
'Guten Tag! Ich möchte ein Kilo Äpfel, zwei Gurken und vier Tomaten. Was kostet das zusammen? Gut, ich nehme alles. Vielen Dank!',
'Uch mahsulotning miqdori va narx savoli bo‘lsin.',
'Uy sherigingizga xarid ro‘yxati bilan 4 gapli xabar yozing.',
'Hallo Ben! Wir brauchen ein Kilo Reis und zwei Liter Milch. Kauf bitte auch sechs Eier. Brot haben wir noch. Danke für deine Hilfe!',
'Miqdorlarni yozing va uyda bor mahsulotni ajrating.')

add('Eine Jacke für den Herbst',
'Im Geschäft sucht Elena eine Jacke. Die rote Jacke ist schön, aber zu klein. Eine blaue Jacke passt gut. Sie kostet fünfzig Euro. Elena hat heute nur vierzig Euro dabei. Die Verkäuferin zeigt ihr eine grüne Jacke für fünfunddreißig Euro. Elena probiert sie an und kauft sie.',
'''Warum kauft Elena die rote Jacke nicht?|Sie ist zu klein|Qizil kurtka juda kichik.
Wie viel Geld hat Elena dabei?|Vierzig Euro|Elenaning yonida qirq yevro bor.
Welche Jacke kauft Elena?|Die grüne Jacke|U 35 yevrolik yashil kurtkani sotib oladi.''',
'Schuhe anprobieren',
'Kunde: Ich suche schwarze Schuhe. Verkäuferin: Welche Größe haben Sie? Kunde: Zweiundvierzig. Verkäuferin: Probieren Sie diese bitte. Kunde: Sie sind zu eng. Haben Sie Größe dreiundvierzig? Verkäuferin: Ja. Hier, bitte. Kunde: Diese passen. Was kosten sie? Verkäuferin: Sechzig Euro. Kunde: Gut, ich bezahle mit Karte.',
'''Welche Farbe sollen die Schuhe haben?|Schwarz|Xaridor qora poyabzal qidiradi.
Welche Größe passt am Ende?|Dreiundvierzig / 43|Oxirida 43-o‘lcham mos keladi.
Wie bezahlt der Kunde?|Mit Karte|U karta bilan to‘laydi.''',
'Do‘konda kiyim so‘rang, o‘lchamini ayting va mos kelmasa boshqasini iltimos qiling.',
'Ich suche eine Hose in Größe vierzig. Kann ich sie anprobieren? Sie ist leider zu lang. Haben Sie eine kürzere Hose? Diese passt gut.',
'O‘lcham, kiyib ko‘rish va moslik haqida gapiring.',
'Do‘stingizga sotib olgan kiyimingiz haqida rang, narx va o‘lcham bilan yozing.',
'Hallo Lea! Ich habe eine neue Jacke. Sie ist blau und kostet vierzig Euro. Die Größe ist M. Sie passt sehr gut. Bis bald, Elena',
'Rang, narx va o‘lchamni kiritishni unutmang.')

add('Ein Brot zu viel',
'Nach dem Einkauf sieht Yusuf auf seinen Kassenzettel. Er hat ein Brot gekauft, aber auf dem Zettel stehen zwei. Er geht zur Kasse zurück. Die Kassiererin prüft den Zettel und entschuldigt sich. Yusuf bekommt drei Euro zurück. Dann packt er sein Brot und die Milch ein und geht nach Hause.',
'''Wie viele Brote hat Yusuf gekauft?|Ein Brot|U aslida bitta non olgan.
Wie viele Brote stehen auf dem Kassenzettel?|Zwei|Chekda esa ikkita non yozilgan.
Wie viel Geld bekommt Yusuf zurück?|Drei Euro|Uch yevro qaytariladi.''',
'Die Kasse ist dort',
'Kundin: Entschuldigung, wo kann ich bezahlen? Mitarbeiter: An Kasse zwei, bitte. Kundin: Kann ich mit Karte bezahlen? Mitarbeiter: Ja, natürlich. Brauchen Sie eine Tasche? Kundin: Nein, ich habe einen Rucksack. Mitarbeiter: Möchten Sie den Kassenzettel? Kundin: Ja, bitte. Die Milch ist für meine Nachbarin. Sie braucht den Zettel.',
'''An welcher Kasse soll die Kundin bezahlen?|An Kasse zwei|Xaridor ikkinchi kassaga yo‘naltiriladi.
Was hat sie statt einer Einkaufstasche dabei?|Einen Rucksack|Uning yonida ryukzak bor.
Für wen ist die Milch?|Für ihre Nachbarin|Sut qo‘shni ayol uchun olingan.''',
'Chekdagi xatoni muloyimlik bilan tushuntiring: bitta mahsulot oldingiz, chekda ikkita yozilgan.',
'Entschuldigung, hier stimmt etwas nicht. Ich habe nur einen Saft gekauft. Auf dem Kassenzettel stehen zwei. Können Sie das bitte prüfen? Vielen Dank.',
'Olingan va chekdagi miqdorni aniq qarama-qarshi qo‘ying.',
'Do‘stingizga xarid pulini tushuntiring: nima oldingiz va qancha qaytim qoldi?',
'Hallo Ali! Ich habe Brot für drei Euro und Milch für zwei Euro gekauft. Du hast mir zehn Euro gegeben. Hier sind fünf Euro zurück. Danke!',
'Narxlar va qaytim bir-biriga mos bo‘lsin.')

add('Frühstück am Fenster',
'Zum Frühstück isst Sabina meistens Brot mit Käse. Dazu trinkt sie schwarzen Tee. Ihr Mann mag lieber Joghurt mit Obst. Heute haben sie Besuch. Deshalb stehen auch Eier und Tomaten auf dem Tisch. Der Gast trinkt Kaffee ohne Zucker. Alle frühstücken langsam und sprechen über den neuen Tag.',
'''Was isst Sabina meistens zum Frühstück?|Brot mit Käse|Sabina ko‘pincha pishloqli non yeydi.
Was mag ihr Mann lieber?|Joghurt mit Obst|Uning eri mevali yogurtni afzal ko‘radi.
Wie trinkt der Gast seinen Kaffee?|Ohne Zucker|Mehmon kofeni shakarsiz ichadi.''',
'Im kleinen Café',
'Kellner: Guten Morgen. Was möchten Sie? Gast: Ein Käsebrot und einen Tee bitte. Kellner: Mit Zitrone? Gast: Ja, gern. Mein Freund möchte ein Ei und einen Kaffee. Kellner: Mit Milch? Gast: Nein, schwarz bitte. Kellner: Kommt sofort. Gast: Können wir am Fenster sitzen? Kellner: Natürlich, der Tisch ist frei.',
'''Was bestellt der Gast zu seinem Käsebrot?|Einen Tee|U pishloqli non bilan choy buyurtma qiladi.
Wie möchte der Freund seinen Kaffee?|Schwarz / Ohne Milch|„Schwarz“ — sutsiz qora kofe.
Wo möchten die Gäste sitzen?|Am Fenster|Ular deraza yonida o‘tirishni xohlashadi.''',
'Kafeda o‘zingiz va do‘stingiz uchun nonushta buyurtma qiling.',
'Ich möchte ein Brötchen mit Käse und einen Tee mit Zitrone. Meine Freundin nimmt Joghurt und einen Kaffee mit Milch. Ist der Tisch dort frei?',
'Ikki kishi uchun ovqat va ichimlikni ajrating.',
'Mehmoningizdan nonushta tanlovini so‘rab 4–5 gap yozing.',
'Hallo Nora! Morgen frühstücken wir um acht. Ich habe Brot, Käse und Eier. Trinkst du Tee oder Kaffee? Möchtest du Milch? Bis morgen, Sabina',
'Nonushta vaqti va kamida ikkita tanlov savoli bo‘lsin.')

add('Eine einfache Gemüsesuppe',
'Für unsere Suppe brauchen wir Kartoffeln, Karotten, eine Zwiebel und Wasser. Zuerst waschen wir das Gemüse. Dann schneiden wir alles klein. Die Zwiebel kommt mit etwas Öl in den Topf. Danach geben wir Gemüse und Wasser dazu. Die Suppe kocht zwanzig Minuten. Am Ende kommen Salz und Kräuter hinein.',
'''Welches Gemüse wird zuerst mit Öl erhitzt?|Die Zwiebel|Avval piyoz yog‘ bilan qozonga solinadi.
Wie lange kocht die Suppe?|Zwanzig Minuten|Sho‘rva yigirma daqiqa qaynaydi.
Was kommt am Ende hinein?|Salz und Kräuter|Oxirida tuz va ko‘kat solinadi.''',
'Zusammen kochen',
'Lina: Haben wir alles für den Salat? Aziz: Tomaten und Gurken sind hier. Lina: Gut. Ich schneide die Tomaten. Wasch bitte die Gurken. Aziz: Brauchen wir eine Zwiebel? Lina: Nein, heute nicht. Aber etwas Öl und Salz. Aziz: Das Brot liegt schon auf dem Tisch. Lina: Prima, dann essen wir gleich.',
'''Was schneidet Lina?|Die Tomaten|Pomidorlarni Lina to‘g‘raydi.
Was soll Aziz waschen?|Die Gurken|Aziz bodringlarni yuvishi kerak.
Welche Zutat wollen sie heute nicht benutzen?|Eine Zwiebel / Zwiebel|Bugun salatga piyoz qo‘shishmaydi.''',
'Oddiy salat tayyorlashni zuerst, dann va am Ende bilan og‘zaki tushuntiring.',
'Zuerst wasche ich zwei Tomaten und eine Gurke. Dann schneide ich das Gemüse klein. Ich gebe etwas Öl dazu. Am Ende kommt ein bisschen Salz in den Salat.',
'Tayyorlashning kamida uch bosqichini tartib bilan ayting.',
'Sevimli oddiy taomingiz uchun mahsulotlar va uch bosqichli ko‘rsatma yozing.',
'Wir brauchen Brot, Käse und Tomaten. Zuerst schneiden wir das Brot. Dann legen wir Käse darauf. Am Ende kommen Tomaten auf den Käse. Guten Appetit!',
'Mahsulotlar va bajariladigan amallar bir-biriga mos bo‘lsin.')

add('Mittagessen ohne Fleisch',
'In der Kantine gibt es heute Reis mit Hähnchen oder Nudeln mit Gemüse. Daria isst kein Fleisch. Sie nimmt die Nudeln. Ihr Kollege bestellt das Hähnchen. Beide trinken Wasser. Zum Nachtisch gibt es Äpfel. Daria bezahlt sieben Euro für ihr Essen. Danach gehen die Kollegen kurz im Hof spazieren.',
'''Was nimmt Daria?|Nudeln mit Gemüse|Daria go‘sht yemagani uchun sabzavotli makaron tanlaydi.
Was gibt es zum Nachtisch?|Äpfel|Shirinlik o‘rnida olma bor.
Wie viel bezahlt Daria?|Sieben Euro|U ovqati uchun yetti yevro to‘laydi.''',
'Eine Frage zum Essen',
'Gast: Entschuldigung, ist in der Suppe Fleisch? Kellnerin: Nein, nur Gemüse. Gast: Gut. Ich möchte eine Suppe und einen Salat. Bitte ohne Käse. Kellnerin: Gern. Und was trinken Sie? Gast: Ein Glas Wasser bitte. Kellnerin: Mit oder ohne Kohlensäure? Gast: Ohne, bitte. Können Sie auch etwas Brot bringen?',
'''Was enthält die Suppe?|Nur Gemüse|Sho‘rvada faqat sabzavot bor.
Was soll nicht im Salat sein?|Käse|Mehmon salatni pishloqsiz so‘raydi.
Welches Wasser bestellt der Gast?|Ohne Kohlensäure / Stilles Wasser|U gazsiz suv buyurtma qiladi.''',
'Restoranda taom tarkibini so‘rang va bitta mahsulotsiz buyurtma bering.',
'Ist in diesem Salat Fleisch? Ich esse kein Fleisch. Dann nehme ich den Gemüsesalat, bitte ohne Zwiebeln. Dazu möchte ich Wasser ohne Kohlensäure.',
'Tarkib haqida savol va ohne bilan istak bildiring.',
'Mezboningizga nima yeyishingiz va nimani xohlamasligingiz haqida xabar yozing.',
'Liebe Nina! Danke für die Einladung. Ich esse gern Gemüse und Reis. Fleisch esse ich nicht. Bitte mach dir keine Mühe. Ich bringe einen Salat mit. Liebe Grüße, Daria',
'Ovqat tanlovingizni muloyim ifodalang va bitta taklif qo‘shing.')

add('Ein Weg durch die Stadt',
'Die Bibliothek liegt nicht weit vom Bahnhof. Vom Bahnhof geht man geradeaus bis zur Ampel. Dort geht man nach links in die Parkstraße. Rechts ist eine Apotheke. Die Bibliothek steht neben der Apotheke. Vor dem Eingang gibt es Fahrradplätze. Die Bibliothek öffnet um zehn Uhr und schließt um sechs.',
'''Wo soll man an der Ampel abbiegen?|Nach links|Svetoforda chapga burilish kerak.
Neben welchem Gebäude liegt die Bibliothek?|Neben der Apotheke|Kutubxona dorixona yonida.
Wann öffnet die Bibliothek?|Um zehn Uhr|Kutubxona soat o‘nda ochiladi.''',
'Entschuldigung, wo ist die Post?',
'Tourist: Entschuldigung, ich suche die Post. Frau: Gehen Sie hier geradeaus. An der nächsten Straße gehen Sie nach rechts. Die Post ist gegenüber vom Supermarkt. Tourist: Ist das weit? Frau: Nein, etwa fünf Minuten zu Fuß. Tourist: Vielen Dank. Frau: Gern. Achten Sie auf die Fahrräder an der Ecke.',
'''Was sucht der Tourist?|Die Post|Sayyoh pochta bo‘limini qidiryapti.
Was liegt gegenüber von der Post?|Der Supermarkt|Pochta qarshisida supermarket bor.
Wie lange dauert der Fußweg ungefähr?|Fünf Minuten|Yo‘l piyoda taxminan besh daqiqa.''',
'Bekatdan kutubxonagacha uch bosqichli yo‘l tarifini bering.',
'Gehen Sie vom Bahnhof geradeaus. An der Ampel gehen Sie nach rechts. Dann sehen Sie einen Park. Die Bibliothek ist links neben dem Park.',
'Boshlanish nuqtasi, burilish va mo‘ljalni ayting.',
'Mehmonga bekatdan uyingizgacha qisqa yo‘l ko‘rsatmasi yozing.',
'Geh von der Haltestelle geradeaus. An der Bäckerei gehst du nach links. Mein Haus ist gegenüber vom Park. Die Hausnummer ist zwölf. Bis gleich!',
'Yo‘nalish va uyni aniqlashga yordam beradigan belgi yozing.')

add('Mit der Straßenbahn zum Museum',
'Said möchte das Stadtmuseum besuchen. An der Haltestelle kauft er eine Fahrkarte für drei Euro. Er nimmt die Straßenbahn Nummer vier. Nach sechs Stationen steigt er am Rathaus aus. Von dort geht er zwei Minuten zu Fuß. Das Museum ist heute kostenlos. Said bleibt dort bis zum Nachmittag.',
'''Welche Straßenbahn nimmt Said?|Nummer vier / Die Vier|Said to‘rtinchi tramvayga chiqadi.
Wo steigt er aus?|Am Rathaus|U shahar hokimiyati yonida tushadi.
Wie viel kostet der Museumseintritt heute?|Nichts / Er ist kostenlos|Bugun muzeyga kirish bepul; uch yevro yo‘l chiptasi narxi.''',
'Eine Durchsage im Bus',
'Liebe Fahrgäste, die nächste Haltestelle ist Stadtpark. Dort können Sie in die Linie sieben umsteigen. Dieser Bus fährt heute nur bis zum Krankenhaus. Die Straße zum Bahnhof ist gesperrt. Zum Bahnhof nehmen Sie bitte die Linie sieben ab Stadtpark. Vergessen Sie beim Aussteigen Ihre Taschen nicht. Vielen Dank.',
'''Wie heißt die nächste Haltestelle?|Stadtpark|Keyingi bekat Stadtpark deb e’lon qilindi.
Wo endet dieser Bus heute?|Am Krankenhaus|Bugun bu avtobus kasalxonagacha boradi.
Welche Linie fährt zum Bahnhof?|Linie sieben|Vokzalga yettinchi yo‘nalish bilan borish kerak.''',
'Haydovchidan muzeyga boradigan yo‘nalish va tushish bekatini so‘rang.',
'Entschuldigung, fährt dieser Bus zum Museum? Wo muss ich aussteigen? Muss ich umsteigen? Vielen Dank. Ich brauche bitte eine Fahrkarte.',
'Yo‘nalish, bekat va almashib chiqish haqida so‘rang.',
'Do‘stingizga uchrashuv joyiga qaysi transport bilan kelishni yozing.',
'Hallo Said! Nimm die Straßenbahn vier. Steig am Rathaus aus. Das Café ist direkt neben dem Rathaus. Ich warte dort um drei. Bis später, Emma',
'Transport raqami, tushish joyi va uchrashuv vaqtini kiriting.')

add('Ein gemeinsamer Samstag',
'Unsere Lerngruppe plant einen Samstag in der Stadt. Zuerst treffen wir uns um zehn am Bahnhof. Dann besuchen wir den Markt. Mittags essen wir im Park unsere Brote. Am Nachmittag gehen wir ins Museum. Bei Regen essen wir im Café. Jeder bringt eine Wasserflasche mit. Um fünf fahren wir nach Hause.',
'''Wo trifft sich die Gruppe?|Am Bahnhof|Guruh vokzalda uchrashadi.
Wo isst die Gruppe bei Regen?|Im Café|Yomg‘irda kafeda ovqatlanishadi.
Was bringt jeder mit?|Eine Wasserflasche|Har kim suv idishini olib keladi.''',
'Pläne ändern',
'Hallo Amina, hier ist Paul. Unser Spaziergang beginnt heute später. Es regnet noch. Treffen wir uns um zwei statt um zwölf? Der Treffpunkt bleibt die Brücke am Park. Bring bitte eine Jacke mit. Nach dem Spaziergang können wir bei mir Tee trinken. Ruf mich bitte kurz zurück. Danke!',
'''Um wie viel Uhr soll das Treffen jetzt sein?|Um zwei|Yangi uchrashuv vaqti soat ikki; o‘n ikki eski vaqt.
Wo ist der Treffpunkt?|An der Brücke am Park|Uchrashuv joyi park yonidagi ko‘prik.
Was soll Amina mitbringen?|Eine Jacke|Amina kurtka olib kelishi kerak.''',
'A1 yakuniy mashqi: sherigingiz bilan yarim kunlik sayrni rejalang; vaqt, transport va ovqatni kelishing.',
'A: Treffen wir uns um zehn am Bahnhof? B: Ja. Wir nehmen den Bus zum Park. A: Ich bringe Brot mit. B: Gut, ich bringe Wasser. Bei Regen gehen wir ins Café.',
'Vaqt, transport, ovqat va yomg‘ir uchun yechimni kelishing.',
'Sayr rejangizni kelolmagan do‘stingizga 40 so‘z atrofida yozing.',
'Hallo Mila! Am Samstag treffen wir uns um zehn am Bahnhof. Wir fahren mit dem Bus zum Park. Ich bringe Brot mit, und Ali bringt Wasser. Danach besuchen wir das Museum. Kommst du auch? Liebe Grüße, Amina',
'Uchrashuv tafsilotlari, ikkita faoliyat va taklifni yozing.')

add('Zum ersten Mal am Meer',
'Letzten Sommer ist Kamila mit ihrer Freundin nach Rostock gefahren. Sie haben drei Nächte in einer kleinen Pension geschlafen. Am ersten Tag war es windig, deshalb sind sie nicht schwimmen gegangen. Stattdessen haben sie den Hafen besucht und warme Suppe gegessen. Am nächsten Morgen schien die Sonne. Kamila hat zum ersten Mal das Meer gesehen und viele Fotos gemacht. Die Rückfahrt war lang, aber im Zug haben die Freundinnen Karten gespielt. Beide möchten im nächsten Jahr wieder ans Meer fahren.',
'''Wie lange haben die Freundinnen in der Pension geschlafen?|Drei Nächte|Ular pansionda uch kecha qolishgan.
Warum sind sie am ersten Tag nicht schwimmen gegangen?|Weil es windig war|Birinchi kuni shamol bo‘lgani uchun cho‘milishmagan.
Was haben sie auf der Rückfahrt gespielt?|Karten|Qaytishda poyezdda karta o‘ynashgan.''',
'Eine Nachricht aus dem Urlaub',
'Hallo Jasur, hier ist Nadja. Wir sind gestern in Dresden angekommen. Unser Hotel liegt direkt am Fluss, aber unser Zimmer geht zum ruhigen Hof. Heute haben wir die Altstadt besichtigt. Meine Tochter wollte danach unbedingt mit einem Schiff fahren. Leider waren alle Plätze ausverkauft. Deshalb haben wir Fahrräder gemietet und sind am Wasser entlanggefahren. Morgen besuchen wir ein Museum. Am Freitag kommen wir zurück. Kannst du bitte bis dahin unsere Blumen gießen? Den Schlüssel hat meine Schwester. Vielen Dank für deine Hilfe!',
'''Wohin geht das Hotelzimmer?|Zum ruhigen Hof|Xona daryoga emas, tinch hovliga qaragan.
Warum ist die Familie nicht mit dem Schiff gefahren?|Alle Plätze waren ausverkauft|Kemadagi barcha joylar sotilib bo‘lgan.
Wer hat den Wohnungsschlüssel?|Nadjas Schwester / Ihre Schwester|Uy kaliti Nadjaning opa yoki singlisida.''',
'O‘tgan safaringiz haqida bir daqiqa gapiring: manzil, transport, faoliyat va taassurot. Perfekt ishlating.',
'Letzten Herbst bin ich mit meinem Bruder nach Chiwa gefahren. Wir haben in einem kleinen Hotel übernachtet. Am Morgen haben wir die Altstadt besucht. Das Wetter war warm, und wir sind viel zu Fuß gegangen. Besonders schön fand ich die alten Gebäude. Am Abend haben wir zusammen gegessen.',
'Safardagi kamida uchta o‘tgan voqeani ayting.',
'Do‘stingizga ta’tildan 50–60 so‘zli norasmiy xat yozing: qayerdasiz, nima qildingiz va ertangi reja.',
'Liebe Anna, wir sind seit Montag in Samarkand. Gestern haben wir den Registan besucht und viele Fotos gemacht. Danach haben wir in einem kleinen Restaurant gegessen. Unser Hotel ist einfach, aber sehr ruhig. Morgen fahren wir zu einem Markt. Dort möchte ich ein Geschenk für dich kaufen. Bis bald! Deine Kamila',
'Manzil, o‘tgan voqea va kelajak rejasini ajrating.')

add('Der Zug fährt später',
'Am Bahnhof erfährt Viktor, dass sein Zug dreißig Minuten Verspätung hat. Er muss in Hannover umsteigen und hat dafür normalerweise nur zehn Minuten Zeit. Am Informationsschalter erklärt er sein Problem. Die Mitarbeiterin sucht eine andere Verbindung. Viktor kann einen späteren Zug nehmen und kommt dann eine Stunde später in Bremen an. Für diese Fahrt braucht er keine neue Fahrkarte. Er ruft seinen Freund an, der ihn am Bahnhof abholen möchte. Danach kauft er Wasser und wartet auf Gleis fünf.',
'''Wie viel Verspätung hat Viktors erster Zug?|Dreißig Minuten|Birinchi poyezd o‘ttiz daqiqa kechikmoqda.
Wo muss Viktor umsteigen?|In Hannover|U Hannoverda boshqa poyezdga o‘tishi kerak.
Muss er eine neue Fahrkarte kaufen?|Nein|Xodima yangi chipta kerak emasligini aytadi.''',
'Eine andere Verbindung',
'Mitarbeiter: Guten Tag, wohin möchten Sie fahren? Reisende: Nach Leipzig, möglichst noch heute Nachmittag. Mein Zug ist ausgefallen. Mitarbeiter: Um vierzehn Uhr zehn fährt ein Zug über Halle. Dort müssen Sie einmal umsteigen. Reisende: Wie lange dauert die Fahrt insgesamt? Mitarbeiter: Zwei Stunden und zwanzig Minuten. Sie haben in Halle fünfundzwanzig Minuten zum Umsteigen. Reisende: Gut. Von welchem Gleis fährt der erste Zug? Mitarbeiter: Von Gleis acht. Auf Ihrer Fahrkarte steht noch Gleis drei, aber das hat sich geändert. Reisende: Danke für den Hinweis.',
'''Über welche Stadt fährt die Verbindung?|Über Halle|Yangi yo‘nalish Halle orqali o‘tadi.
Wie lange dauert die gesamte Fahrt?|Zwei Stunden und zwanzig Minuten|Butun yo‘l ikki soat yigirma daqiqa davom etadi.
Von welchem Gleis fährt der erste Zug tatsächlich?|Von Gleis acht|Haqiqiy platforma 8; chiptadagi 3 eskirgan ma’lumot.''',
'Bekor qilingan poyezd o‘rniga boshqa yo‘nalishni so‘rang; ketish vaqti, almashish va platformani aniqlang.',
'Mein Zug ist ausgefallen, und ich muss heute nach Berlin. Gibt es eine andere Verbindung? Wann fährt der nächste Zug? Muss ich umsteigen? Ich habe einen schweren Koffer und brauche etwas Zeit. Von welchem Gleis fährt der Zug ab?',
'Uchta amaliy ma’lumotni savollar orqali aniqlang.',
'Sizni kutayotgan do‘stga kechikish sababi, yangi kelish vaqti va kutish joyi haqida xabar yozing.',
'Hallo Ben, mein Zug hat Verspätung. Deshalb verpasse ich den Anschluss in Hannover. Ich nehme den nächsten Zug und komme erst um achtzehn Uhr in Bremen an. Bitte warte am Haupteingang auf mich. Du musst nicht früher kommen. Ich melde mich noch einmal, wenn ich im Zug sitze. Bis später! Viktor',
'Sabab, yangi vaqt va do‘stingiz bajarishi kerak bo‘lgan ishni ayting.')

add('Eine Reservierung mit Fehler',
'Als Familie Berger im Hotel ankommt, gibt es ein Problem. Sie hat ein Zimmer für zwei Erwachsene und ein Kind gebucht. Im Computer steht jedoch nur ein Doppelzimmer ohne Zusatzbett. Frau Berger zeigt die Bestätigung auf ihrem Handy. Die Rezeptionistin entschuldigt sich und bietet ein größeres Zimmer im dritten Stock an. Es kostet nicht mehr. Die Familie nimmt das Angebot an. Nur das Frühstück ist nicht im Preis enthalten. Deshalb fragt Herr Berger nach einer Bäckerei in der Nähe.',
'''Was fehlt im zuerst vorgesehenen Zimmer?|Ein Zusatzbett|Dastlab belgilangan xonada qo‘shimcha karavot yo‘q.
In welchem Stock liegt das neue Zimmer?|Im dritten Stock|Yangi xona uchinchi qavatda.
Welche Mahlzeit ist nicht im Preis enthalten?|Das Frühstück|Nonushta narxga kiritilmagan.''',
'An der Rezeption',
'Gast: Guten Abend, ich habe auf den Namen Sodiqova reserviert. Rezeptionist: Ja, ein Einzelzimmer für zwei Nächte. Hier ist Ihre Schlüsselkarte. Gast: Danke. Kann ich morgen schon um sechs frühstücken? Rezeptionist: Das Frühstück beginnt erst um sieben. Wir können Ihnen aber ein kleines Frühstückspaket vorbereiten. Gast: Das wäre gut, mein Bus fährt um halb sieben. Rezeptionist: Dann holen Sie das Paket bitte um sechs hier ab. Möchten Sie Kaffee oder Tee dazu? Gast: Tee bitte, und wenn möglich ein Brot ohne Käse.',
'''Für wie viele Nächte hat Frau Sodiqova gebucht?|Für zwei Nächte|Bron ikki kechaga qilingan.
Wann fährt ihr Bus?|Um halb sieben / Um sechs Uhr dreißig|Avtobus 6:30 da ketadi.
Was soll nicht auf ihrem Brot sein?|Käse|U nonini pishloqsiz so‘raydi.''',
'Mehmonxonadagi bron xatosini tushuntiring va mos yechim so‘rang.',
'Guten Abend. Ich habe ein ruhiges Zimmer mit zwei Betten gebucht. In unserem Zimmer gibt es aber nur ein Bett. Hier ist meine Bestätigung. Können wir bitte ein anderes Zimmer bekommen? Wir bleiben drei Nächte und brauchen wirklich zwei Betten.',
'Bron qilingan va berilgan xonani solishtirib, yechim so‘rang.',
'Mehmonxonaga 50–60 so‘zli bron so‘rovi yozing: sana, odamlar, xona va nonushta savoli.',
'Sehr geehrte Damen und Herren, ich möchte vom 12. bis zum 14. Juni ein Zimmer für zwei Erwachsene reservieren. Wir brauchen zwei getrennte Betten und kommen gegen zwanzig Uhr an. Haben Sie noch ein ruhiges Zimmer frei? Bitte teilen Sie mir den Preis mit. Ist das Frühstück dabei? Mit freundlichen Grüßen, Madina Karimova',
'Sanalar, odamlar soni va narx haqidagi savolni kiriting.')

add('Der erste Tag im Büro',
'Aziz beginnt am Montag seine neue Arbeit in einem Reisebüro. Seine Kollegin Paula zeigt ihm zuerst die Räume. Danach erklärt sie das Buchungsprogramm. Aziz schreibt wichtige Schritte in ein kleines Heft, weil er sich nicht alles sofort merken kann. Um zwölf essen beide mit dem Team. Am Nachmittag beantwortet Aziz schon einfache E-Mails. Bei einer schwierigen Frage hilft Paula ihm. Vor Feierabend vereinbaren sie, am nächsten Morgen gemeinsam die offenen Aufgaben zu besprechen. Aziz ist müde, aber zufrieden.',
'''Wo beginnt Aziz seine neue Arbeit?|In einem Reisebüro|Aziz sayohat agentligida ish boshlaydi.
Warum macht Aziz Notizen?|Er kann sich nicht alles sofort merken|U hammasini darhol eslab qola olmagani uchun yozib boradi.
Was beantwortet Aziz am Nachmittag?|Einfache E-Mails|Tushdan keyin sodda elektron xatlarga javob beradi.''',
'Eine Aufgabe für morgen',
'Hallo Farid, hier spricht Frau Neumann. Morgen kommen um neun Uhr sechs Gäste aus unserer Partnerfirma. Bitte bereiten Sie den kleinen Besprechungsraum vor. Wir brauchen Wasser, sechs Gläser und den großen Bildschirm. Die Unterlagen liegen auf meinem Schreibtisch. Bitte kopieren Sie für jeden Gast ein Exemplar. Ich komme erst um Viertel vor neun, weil ich vorher einen Termin habe. Wenn der Bildschirm nicht funktioniert, fragen Sie Herrn Wolf. Er kennt die Technik gut. Vielen Dank, und bis morgen früh.',
'''Wie viele Gäste kommen?|Sechs|Hamkor firmadan olti mehmon keladi.
Wo liegen die Unterlagen?|Auf Frau Neumanns Schreibtisch|Hujjatlar Frau Neumannning yozuv stolida.
Wer hilft bei technischen Problemen?|Herr Wolf|Texnik muammo bo‘lsa Herr Wolfdan so‘rash kerak.''',
'Yangi ish joyida vazifani qayta aniqlashtiring: nima, qachongacha va kim yordam beradi?',
'Ich soll also den Raum für sechs Gäste vorbereiten. Bis wann muss alles fertig sein? Wo finde ich die Unterlagen? Soll ich auch Kaffee machen? Wenn der Bildschirm nicht funktioniert, frage ich Herrn Wolf. Habe ich alles richtig verstanden?',
'Vazifani qayta aytib, kamida ikkita aniqlashtiruvchi savol bering.',
'Rahbaringizga vazifa bajarilgani va bitta muammo haqida 50 so‘z atrofida xat yozing.',
'Guten Tag Frau Neumann, der Besprechungsraum ist fertig. Wasser und Gläser stehen auf dem Tisch, und die Unterlagen sind kopiert. Leider funktioniert der Bildschirm noch nicht. Herr Wolf kommt um halb neun und prüft das Gerät. Ich bleibe bis zum Beginn im Raum. Viele Grüße, Farid',
'Bajarilgan ish, muammo va yechimni alohida ko‘rsating.')

add('Ein Beruf mit Menschen',
'Zarina arbeitet seit einem Jahr in einer Stadtbibliothek. Früher hat sie in einem Laden Kleidung verkauft. Dort musste sie oft bis spät abends arbeiten. Jetzt beginnt ihr Arbeitstag um neun und endet um fünf. Besonders gern hilft sie Kindern, ein passendes Buch zu finden. Manchmal organisiert sie eine Vorlesestunde. Dafür muss sie Bücher auswählen und den Raum vorbereiten. Das Gehalt ist nicht viel höher als früher, aber die Arbeitszeiten passen besser zu ihrer Familie. Deshalb möchte sie in der Bibliothek bleiben.',
'''Wo hat Zarina früher gearbeitet?|In einem Kleidungsgeschäft / In einem Laden|Früher u kiyim do‘konida ishlagan.
Wem hilft sie besonders gern?|Kindern|U ayniqsa bolalarga kitob tanlashda yordam berishni yoqtiradi.
Was passt jetzt besser zu ihrer Familie?|Die Arbeitszeiten|Oilasi uchun yangi ish vaqti qulayroq.''',
'Über einen Wunschberuf sprechen',
'Moderatorin: Heute sprechen wir mit Timo über seine Ausbildung. Timo, warum möchtest du Koch werden? Timo: Ich habe früher oft mit meinem Großvater gekocht. Das hat mir Spaß gemacht. Jetzt lerne ich in einem Restaurant. Moderatorin: Ist die Arbeit anstrengend? Timo: Ja, ich stehe viel und arbeite auch am Wochenende. Aber ich lerne jeden Tag etwas Neues. Moderatorin: Was findest du besonders wichtig? Timo: Man muss gut im Team arbeiten. Wenn viele Gäste kommen, kann niemand alles allein machen. Nach der Ausbildung möchte ich in einer Schulküche arbeiten.',
'''Mit wem hat Timo früher gekocht?|Mit seinem Großvater|Timo ilgari bobosi bilan ovqat pishirgan.
Was ist für Timo besonders wichtig?|Teamarbeit / Gut im Team arbeiten|U jamoada ishlashni ayniqsa muhim deb biladi.
Wo möchte er nach der Ausbildung arbeiten?|In einer Schulküche|O‘qishdan keyin maktab oshxonasida ishlamoqchi.''',
'Qiziqqan kasbingizni tanlang va vazifalari, yaxshi tomoni hamda qiyinchiligini ayting.',
'Ich möchte in einer Bibliothek arbeiten, weil ich Bücher und den Kontakt mit Menschen mag. Dort hilft man Besuchern und ordnet Bücher. Die Arbeit ist manchmal laut, besonders bei Veranstaltungen. Trotzdem finde ich sie interessant. Dafür möchte ich mein Deutsch verbessern und ein Praktikum machen.',
'Kasb tanlovini bir sabab va bir qiyinchilik bilan tushuntiring.',
'Til sherigingizga kelajakdagi kasb rejangiz haqida 50–60 so‘z yozing.',
'Liebe Eva, ich möchte später als Erzieherin arbeiten. Ich verbringe gern Zeit mit Kindern und kann gut erklären. Im Sommer möchte ich zuerst ein Praktikum in einem Kindergarten machen. Dafür brauche ich noch bessere Deutschkenntnisse. Arbeitest du auch gern mit Kindern? Vielleicht können wir am Samstag über unsere Pläne sprechen. Liebe Grüße, Zarina',
'Kasb, sabab va tayyorgarlik uchun keyingi qadamni yozing.')

add('Ein freier Nachmittag gesucht',
'Otabek arbeitet in einem Supermarkt. Nächsten Mittwoch hat seine Tochter ein Schulfest. Er möchte dabei sein, aber sein Dienst endet erst um sechs. Deshalb fragt er seine Kollegin Mira, ob sie tauschen können. Mira kann mittwochs länger arbeiten, wenn Otabek ihren frühen Dienst am Freitag übernimmt. Beide schreiben die neuen Zeiten auf und fragen ihre Teamleiterin. Sie stimmt zu. Otabek ist erleichtert. Er weiß aber auch, dass er am Freitag sehr früh aufstehen muss. Den Wecker stellt er deshalb sofort.',
'''Warum möchte Otabek am Mittwoch früher frei haben?|Wegen des Schulfests seiner Tochter|Qizining maktab bayramiga borishni xohlaydi.
Welchen Dienst übernimmt Otabek dafür?|Miras frühen Dienst am Freitag|Buning evaziga juma kungi ertalabki navbatchilikni oladi.
Wer muss dem Tausch zustimmen?|Die Teamleiterin|Almashishga jamoa rahbari rozilik berishi kerak.''',
'Eine Vertretung organisieren',
'Mira: Otabek, kannst du morgen meine erste Stunde übernehmen? Ich habe um acht einen Termin beim Bürgerbüro. Otabek: Morgen geht es leider nicht, weil ich meinen Sohn zur Schule bringe. Hast du schon Jonas gefragt? Mira: Nein, er hat heute frei. Otabek: Ruf ihn doch an. Vielleicht kann er früher kommen. Ich kann dafür nachmittags eine Stunde länger bleiben. Mira: Das wäre hilfreich. Ich spreche zuerst mit Jonas und sage dann der Teamleiterin Bescheid. Otabek: Gut. Schreib mir bitte, wenn der Plan feststeht.',
'''Wo hat Mira ihren Termin?|Beim Bürgerbüro|Miraning uchrashuvi fuqarolarga xizmat ko‘rsatish idorasida.
Warum kann Otabek morgens nicht helfen?|Er bringt seinen Sohn zur Schule|Otabek o‘g‘lini maktabga olib boradi.
Was bietet Otabek stattdessen an?|Nachmittags eine Stunde länger bleiben|U tushdan keyin bir soat ortiq qolishni taklif qiladi.''',
'Hamkasb bilan ish vaqtini almashtiring; sabab, muqobil taklif va rahbar bilan kelishishni kiriting.',
'A: Kannst du am Dienstag meinen Spätdienst übernehmen? Ich habe einen Elternabend. B: Dienstag geht, wenn du am Samstag für mich arbeitest. A: Das kann ich machen. Fragen wir zuerst unsere Chefin. B: Ja, danach schreiben wir die Zeiten auf.',
'Ikki tomon uchun mos almashinuvni kelishing.',
'Rahbaringizga ish vaqtini almashtirish uchun 50–60 so‘zli muloyim so‘rov yozing.',
'Guten Tag Frau Berg, am Mittwoch möchte ich zum Schulfest meiner Tochter gehen. Deshalb würde ich gern meinen Spätdienst mit Mira tauschen. Sie ist einverstanden. Ich übernehme dafür ihren frühen Dienst am Freitag. Können Sie diesem Tausch zustimmen? Bis zu Ihrer Antwort gilt natürlich unser bisheriger Plan. Vielen Dank! Otabek',
'Sabab, kelishilgan almashinuv va rozilik so‘rovini yozing.')

add('Lernen mit kleinen Karten',
'Nach einigen Wochen im Deutschkurs merkt Lola, dass sie neue Wörter schnell vergisst. Ihre Lehrerin empfiehlt ihr kleine Lernkarten. Auf eine Seite schreibt Lola ein deutsches Wort mit Artikel, auf die andere Seite die usbekische Bedeutung. Bei Verben ergänzt sie einen eigenen Beispielsatz. Jeden Morgen wiederholt sie zehn Karten im Bus. Schwierige Karten legt sie in ein besonderes Fach. Am Sonntag prüft sie, welche Wörter sie schon sicher kennt. Das Lernen dauert nicht lange, aber Lola macht es regelmäßig und fühlt sich dadurch sicherer.',
'''Was schreibt Lola zusammen mit einem deutschen Nomen auf die Karte?|Den Artikel|Ot bilan birga artiklni yozadi.
Wann wiederholt sie zehn Karten?|Jeden Morgen im Bus|Har kuni ertalab avtobusda o‘nta kartani takrorlaydi.
Wohin legt sie schwierige Karten?|In ein besonderes Fach|Qiyin kartalarni alohida bo‘limga qo‘yadi.''',
'Eine Lerngruppe sucht einen Plan',
'Sami: Wir treffen uns jede Woche, aber wir sprechen oft nur über Filme. Eda: Dann brauchen wir einen Plan. Zuerst könnten wir zwanzig Minuten neue Wörter wiederholen. Sami: Gut. Danach möchte ich die Hausaufgaben vergleichen. Eda: Und zum Schluss sprechen wir zehn Minuten frei über ein Thema. Jeder bereitet zwei Fragen vor. Sami: Wer achtet auf die Zeit? Eda: Diese Woche mache ich das. Nächste Woche bist du dran. Sami: Einverstanden. Unsere Handys legen wir während des Lernens in die Tasche, damit wir uns besser konzentrieren.',
'''Wie lange wollen sie zuerst Wörter wiederholen?|Zwanzig Minuten|Avval yigirma daqiqa so‘z takrorlashadi.
Wie viele Fragen bereitet jeder vor?|Zwei|Har kim ikkita savol tayyorlaydi.
Wer achtet diese Woche auf die Zeit?|Eda|Bu hafta vaqtni Eda kuzatadi.''',
'O‘zingizga foydali bo‘lgan ikki o‘rganish usulini tushuntiring va sherigingizga bittasini tavsiya qiling.',
'Ich lerne Wörter mit Karten. Zu jedem Verb schreibe ich einen eigenen Satz, weil ich es dann besser verstehe. Außerdem höre ich kurze Dialoge zweimal. Beim ersten Mal suche ich nur das Thema. Du könntest diese Methode auch versuchen. Zehn Minuten am Tag reichen für den Anfang.',
'Ikki usulning bajarilishi va foydasini ayting.',
'O‘qishda qiynalayotgan do‘stingizga 50–60 so‘zli maslahat xati yozing.',
'Lieber Sam, du musst nicht jeden Abend zwei Stunden lernen. Versuch lieber, jeden Tag zehn Wörter zu wiederholen. Schreib kurze eigene Sätze dazu. Wir können uns am Donnerstag treffen und einen Dialog üben. Bring bitte deine Fragen mit. Fehler sind dabei erlaubt; wir suchen gemeinsam eine bessere Formulierung. Liebe Grüße, Lola',
'Ikkita bajarish mumkin bo‘lgan maslahat va yordam taklifini bering.')

add('Ein Kurs am Abend',
'Akmal möchte besser mit Computern arbeiten. Im Programm der Volkshochschule findet er zwei Kurse. Der erste beginnt um vierzehn Uhr und ist günstig. Zu dieser Zeit arbeitet Akmal jedoch noch. Der zweite findet dienstags und donnerstags um neunzehn Uhr statt. Er kostet mehr, aber die Zeiten passen. Bevor Akmal sich anmeldet, ruft er im Büro an. Er möchte wissen, ob er einen eigenen Laptop braucht. Die Mitarbeiterin erklärt, dass Computer im Kursraum stehen. Akmal muss nur ein Heft und einen Stift mitbringen.',
'''Warum passt der erste Kurs nicht?|Akmal arbeitet zu dieser Zeit|Birinchi kurs vaqtida Akmal ishlayotgan bo‘ladi.
An welchen Tagen findet der Abendkurs statt?|Dienstags und donnerstags|Kechki kurs seshanba va payshanba kunlari.
Braucht Akmal einen eigenen Laptop?|Nein|Xonada kompyuterlar bor, shaxsiy noutbuk kerak emas.''',
'Fragen zur Anmeldung',
'Mitarbeiterin: Guten Tag, Kursbüro West. Anruferin: Ich interessiere mich für den Fotokurs im November. Gibt es noch Plätze? Mitarbeiterin: Ja, drei Plätze sind noch frei. Der Kurs beginnt am fünften November und dauert sechs Wochen. Anruferin: Muss ich schon viel über Fotografie wissen? Mitarbeiterin: Nein, der Kurs ist für Anfänger. Eine einfache Kamera reicht. Anruferin: Kann ich mich telefonisch anmelden? Mitarbeiterin: Bitte füllen Sie das Formular auf unserer Internetseite aus. Wenn Sie dabei Hilfe brauchen, kommen Sie am Montag zwischen zehn und zwölf ins Büro.',
'''Wie lange dauert der Fotokurs?|Sechs Wochen|Fotokurs olti hafta davom etadi.
Für wen ist der Kurs gedacht?|Für Anfänger|Kurs yangi boshlovchilar uchun.
Wie soll sich die Anruferin anmelden?|Mit dem Onlineformular / Über das Formular auf der Internetseite|Internet sahifasidagi shaklni to‘ldirish kerak.''',
'Kurs idorasiga qo‘ng‘iroq qilishni mashq qiling: daraja, jadval, narx va kerakli jihozlarni so‘rang.',
'Guten Tag. Ich interessiere mich für Ihren Computerkurs. Ist er auch für Anfänger geeignet? An welchen Tagen findet er statt, und wie viel kostet er? Brauche ich einen eigenen Laptop? Ich arbeite bis fünf und könnte nur am Abend kommen.',
'Kursni tanlash uchun kamida uchta savol bering.',
'Kurs tashkilotchisiga 50–60 so‘zli ma’lumot so‘rovi yozing.',
'Sehr geehrte Damen und Herren, ich möchte im November an Ihrem Fotokurs teilnehmen. Ich bin Anfängerin und habe nur eine kleine Kamera. Ist das ausreichend? Bitte schicken Sie mir Informationen zu den Kurszeiten und den Gebühren. Außerdem möchte ich wissen, ob am Ende eine Ausstellung geplant ist. Vielen Dank. Mit freundlichen Grüßen, Lola Saidova',
'Qiziqqan kursni, darajangizni va ikkita savolni aniq yozing.')

add('Ein Nachmittag in der Berufsschule',
'Nuri macht eine Ausbildung zum Elektriker. An drei Tagen arbeitet er in einem Betrieb, an zwei Tagen besucht er die Berufsschule. Heute baut seine Gruppe eine einfache Lampe. Bevor die Schüler anfangen, erklärt die Lehrerin die Aufgabe und die Sicherheitsregeln. Nuri liest die Anleitung zweimal, weil einige Wörter neu sind. Sein Mitschüler erklärt sie mit einer Zeichnung. Am Ende funktioniert die Lampe. Die Gruppe beschreibt anschließend schriftlich, welche Schritte nötig waren. Nuri findet diese Aufgabe schwierig, aber hilfreich für seine spätere Arbeit.',
'''An wie vielen Tagen besucht Nuri die Berufsschule?|An zwei Tagen|Nuri haftada ikki kun kasb maktabiga boradi.
Was baut seine Gruppe?|Eine einfache Lampe|Uning guruhi sodda chiroq yasaydi.
Wie erklärt der Mitschüler die neuen Wörter?|Mit einer Zeichnung|Sinfdoshi yangi so‘zlarni chizma orqali tushuntiradi.''',
'Vor einer kleinen Prüfung',
'Lehrerin: Am Freitag schreiben wir einen kurzen Test. Er dauert dreißig Minuten und hat zwei Teile. Zuerst lesen Sie einen Text über einen Arbeitsplatz und beantworten Fragen. Danach schreiben Sie eine Nachricht an einen Kollegen. Wörterbücher dürfen Sie diesmal benutzen, Handys aber nicht. Schülerin: Müssen wir alle neuen Wörter können? Lehrerin: Lernen Sie besonders die Wörter aus den letzten beiden Lektionen. Morgen üben wir noch ein Beispiel gemeinsam. Bitte kommen Sie am Freitag pünktlich, damit wir alle zur gleichen Zeit anfangen können.',
'''Wie lange dauert der Test?|Dreißig Minuten|Test o‘ttiz daqiqa davom etadi.
Was dürfen die Lernenden benutzen?|Wörterbücher|Lug‘atlardan foydalanish mumkin, telefonlardan emas.
Aus welchen Lektionen sollen sie besonders Wörter lernen?|Aus den letzten beiden Lektionen|Asosan oxirgi ikki darsdagi so‘zlarni o‘rganish kerak.''',
'O‘qituvchidan tushunmagan topshiriqni yana tushuntirishni so‘rang va tushunganingizni qayta ayting.',
'Entschuldigung, ich habe den zweiten Schritt noch nicht verstanden. Können Sie ihn bitte an einem Beispiel erklären? Sollen wir zuerst den Text lesen und dann die Fragen beantworten? Danke, jetzt ist es klar. Darf ich unbekannte Wörter im Wörterbuch nachschlagen?',
'Aniq qaysi qism tushunarsizligini ayting va tushunganingizni tekshiring.',
'Darsga kelmagan kursdoshingizga test tartibi haqida 50–60 so‘z yozing.',
'Hallo Nuri, am Freitag schreiben wir einen Test. Er dauert dreißig Minuten. Wir lesen zuerst einen Text und schreiben danach eine kurze Nachricht. Du darfst ein Wörterbuch benutzen, aber kein Handy. Wiederhole besonders die letzten beiden Lektionen. Morgen üben wir zusammen im Kurs. Komm bitte pünktlich. Viele Grüße, Eda',
'Davomiylik, ikki topshiriq va ruxsat etilgan vositani yozing.')

add('Ein Termin in der Praxis',
'Seit Montag hat Emma Halsschmerzen und fühlt sich müde. Sie ruft in einer Arztpraxis an und bekommt einen Termin für den nächsten Morgen. Am Empfang zeigt sie ihre Versicherungskarte. Im Wartezimmer liest sie nicht, weil sie Kopfschmerzen hat. Die Ärztin fragt, seit wann die Beschwerden bestehen und ob Emma Fieber hat. Emma erklärt, dass sie ihre Temperatur noch nicht gemessen hat. Nach dem Gespräch bekommt sie Hinweise für die nächsten Tage. Sie sagt anschließend ihren Abendkurs ab und geht nach Hause.',
'''Seit wann hat Emma Halsschmerzen?|Seit Montag|Tomoq og‘rig‘i dushanbadan boshlangan.
Was zeigt sie am Empfang?|Ihre Versicherungskarte|Qabulda sug‘urta kartasini ko‘rsatadi.
Warum liest sie im Wartezimmer nicht?|Weil sie Kopfschmerzen hat|Boshi og‘rigani sababli o‘qimaydi.''',
'Einen Termin vereinbaren',
'Assistent: Praxis Sommer, guten Morgen. Patient: Guten Morgen, ich möchte einen Termin. Seit gestern tut mein rechtes Knie weh. Assistent: Ist das nach einem Unfall passiert? Patient: Nein. Ich bin am Wochenende viel gelaufen, aber ich weiß nicht, ob das der Grund ist. Assistent: Wir haben heute um fünfzehn Uhr einen Termin frei. Patient: Das passt. Soll ich etwas mitbringen? Assistent: Bitte Ihre Versicherungskarte und, wenn vorhanden, alte Unterlagen zum Knie. Patient: Gut, vielen Dank. Mein Name ist Bek Rustamov. Assistent: Ich habe Sie eingetragen.',
'''Welches Körperteil tut weh?|Das rechte Knie|Bemorning o‘ng tizzasi og‘riyapti.
Wann ist der angebotene Termin?|Heute um fünfzehn Uhr|Taklif qilingan vaqt bugun 15:00.
Welche Karte soll der Patient mitbringen?|Die Versicherungskarte|U sug‘urta kartasini olib kelishi kerak.''',
'Til mashqi sifatida shifokor qabuliga yoziling: alomat, boshlanish vaqti va bo‘sh vaqtni ayting.',
'Guten Morgen, mein Name ist Karimova. Ich möchte einen Termin vereinbaren. Seit gestern habe ich Halsschmerzen. Heute Nachmittag habe ich Zeit. Gibt es noch einen freien Termin? Was soll ich mitbringen? Vielen Dank, dann komme ich um drei.',
'Alomatni tashxis qo‘ymasdan tasvirlang va vaqtni tasdiqlang.',
'Kurs o‘qituvchisiga betobligingiz tufayli darsga kelmasligingiz va vazifani so‘rashingiz haqida yozing.',
'Liebe Frau Weber, leider kann ich heute nicht zum Kurs kommen, weil ich mich krank fühle. Morgen habe ich einen Arzttermin. Können Sie mir bitte die Hausaufgaben schicken? Ich möchte den Stoff nachholen, wenn es mir besser geht. Meiner Lernpartnerin habe ich schon Bescheid gesagt. Vielen Dank für Ihr Verständnis. Freundliche Grüße, Emma',
'Kelmaslik sababi va o‘quv materialini so‘rashni kiriting.')

add('Mehr Bewegung im Alltag',
'Seit Farid im Büro arbeitet, sitzt er fast den ganzen Tag. Abends ist er oft zu müde für Sport. Deshalb möchte er seinen Alltag langsam verändern. Er fährt jetzt zweimal pro Woche mit dem Fahrrad zur Arbeit. In der Mittagspause geht er mit einer Kollegin zehn Minuten spazieren. Am Wochenende spielt er manchmal Tischtennis mit seinem Bruder. Farid hat keinen festen Trainingsplan. Ihm ist wichtig, dass die Bewegung Spaß macht. Nach einem Monat merkt er, dass er sich auf die kurzen Spaziergänge freut.',
'''Wie oft fährt Farid mit dem Fahrrad zur Arbeit?|Zweimal pro Woche|U haftada ikki marta velosipedda ishga boradi.
Wie lange dauert der Spaziergang in der Mittagspause?|Zehn Minuten|Tushlikdagi sayr o‘n daqiqa davom etadi.
Mit wem spielt er Tischtennis?|Mit seinem Bruder|U akasi yoki ukasi bilan stol tennisi o‘ynaydi.''',
'Ein Kurs zum Ausprobieren',
'Trainerin: Willkommen zu unserem Bewegungskurs. Heute lernen wir erst einmal die Gruppe kennen. Sie brauchen keine besonderen Sportgeräte, nur bequeme Kleidung. Wir beginnen mit einfachen Bewegungen im Stehen. Wenn eine Übung für Sie unangenehm ist, sagen Sie bitte Bescheid. Teilnehmer: Ich war lange nicht beim Sport. Kann ich trotzdem mitmachen? Trainerin: Natürlich. Jeder macht in seinem eigenen Tempo mit. Nach zwanzig Minuten machen wir eine Pause. Der Kurs endet um halb sieben. Danach können Sie fragen, ob Sie nächste Woche wieder teilnehmen möchten.',
'''Welche Kleidung brauchen die Teilnehmenden?|Bequeme Kleidung|Qulay kiyim kerak.
Wann macht die Gruppe eine Pause?|Nach zwanzig Minuten|Yigirma daqiqadan so‘ng tanaffus bo‘ladi.
Wann endet der Kurs?|Um halb sieben / Um achtzehn Uhr dreißig|Kurs kechki 18:30 da tugaydi.''',
'Do‘stingiz bilan kundalik hayotga mos yengil faoliyat tanlang; vaqt va qiziqishlaringizni hisobga oling.',
'A: Ich möchte mich mehr bewegen, habe aber abends wenig Zeit. B: Wir könnten in der Mittagspause spazieren gehen. A: Zehn Minuten passen gut. B: Am Samstag können wir auch Tischtennis spielen. A: Gern, das macht mir mehr Spaß als Joggen.',
'Vaqt chekloviga mos ikkita faoliyatni kelishing.',
'Do‘stingizni birgalikdagi sayrga taklif qilib, 50 so‘z atrofida xat yozing.',
'Hallo Murat, ich sitze im Moment viel am Schreibtisch und möchte öfter draußen sein. Hast du Lust, am Samstag mit mir am Fluss spazieren zu gehen? Wir könnten uns um zehn an der Brücke treffen und danach einen Tee trinken. Bei starkem Regen verschieben wir den Spaziergang. Liebe Grüße, Farid',
'Sabab, vaqt, joy va ob-havo uchun muqobilni yozing.')

add('Ein Nachmittag ohne Bildschirm',
'Malika merkt, dass sie nach der Arbeit oft stundenlang am Handy bleibt. Dabei möchte sie eigentlich früher schlafen. Sie beschließt, am Mittwoch einen Nachmittag ohne Bildschirm zu verbringen. Zuerst ist es ungewohnt. Sie sucht automatisch nach ihrem Handy, das in einer Schublade liegt. Dann holt sie ein altes Zeichenheft und setzt sich auf den Balkon. Später kocht sie mit ihrer Mitbewohnerin. Am Abend fühlt sie sich zufrieden. Sie möchte ihr Handy weiterhin nutzen, aber bewusster entscheiden, wann sie es wirklich braucht.',
'''An welchem Tag macht Malika eine Bildschirmpause?|Am Mittwoch|Malika chorshanba kuni ekranlardan tanaffus qiladi.
Wo liegt ihr Handy?|In einer Schublade|Telefon tortmada turadi.
Was holt sie zum Zeichnen?|Ein altes Zeichenheft|U eski rasm daftarini oladi.''',
'Den Abend ruhiger planen',
'Nina: Du siehst heute müde aus. Said: Ich habe gestern bis Mitternacht Videos gesehen. Eigentlich wollte ich nur zehn Minuten schauen. Nina: Das kenne ich. Mir hilft es, vorher eine feste Schlusszeit zu wählen. Said: Vielleicht lege ich das Handy nach dem Abendessen in die Küche. Nina: Und was machst du dann? Said: Ich möchte wieder Gitarre spielen. Früher habe ich das gern gemacht. Nina: Gute Idee. Wir könnten am Sonntag zusammen Musik machen. Said: Ja, aber ohne dass wir dabei ständig neue Nachrichten lesen.',
'''Bis wann hat Said Videos gesehen?|Bis Mitternacht|Said yarim tungacha video ko‘rgan.
Wohin möchte er sein Handy nach dem Essen legen?|In die Küche|Ovqatdan keyin telefonini oshxonaga qo‘ymoqchi.
Welches Instrument möchte er wieder spielen?|Gitarre|U yana gitara chalishni xohlaydi.''',
'Bir kundalik odatingizni o‘zgartirish rejasini ayting: eski odat, sabab va kichik yangi qadam.',
'Abends lese ich oft lange Nachrichten auf meinem Handy. Dann bleibt keine Zeit für mein Buch. Ich möchte deshalb nach neun keine Nachrichten mehr öffnen. Das Handy lege ich in die Küche. Zuerst versuche ich das nur an zwei Abenden. Danach schaue ich, ob es für mich passt.',
'Rejangizni aniq va bajarish mumkin bo‘lgan qadam bilan ifodalang.',
'Do‘stingizga ekranlarsiz bir kecha uchun 50–60 so‘zli taklif yozing.',
'Liebe Nina, am Freitag möchte ich einen Abend ohne Handy verbringen. Hast du Lust mitzumachen? Wir könnten zusammen kochen und danach Karten spielen. Unsere Handys lassen wir währenddessen in den Taschen. Um sieben geht es bei mir los. Bring bitte dein Lieblingsspiel mit. Ich freue mich auf einen ruhigen Abend. Liebe Grüße, Malika',
'Faoliyat, vaqt va telefon bo‘yicha kelishuvni yozing.')

add('Ein Missverständnis unter Freunden',
'Am Freitag wartet Rano vor dem Kino auf ihre Freundin Klara. Nach zwanzig Minuten wird sie ärgerlich. Sie schreibt eine kurze Nachricht: Wo bleibst du? Klara antwortet sofort, dass sie vor dem Kino am Bahnhof steht. Rano wartet aber vor dem neuen Kino am Markt. Beide hatten nur über den Film gesprochen und den Ort nicht genau vereinbart. Sie müssen lachen. Für die erste Vorstellung ist es nun zu spät. Deshalb treffen sie sich in einem Café und wählen später gemeinsam einen anderen Film.',
'''Wo wartet Klara?|Vor dem Kino am Bahnhof|Klara vokzal yonidagi kinoteatr oldida kutmoqda.
Welche Information hatten die Freundinnen nicht genau vereinbart?|Den Ort / Das Kino|Ular aniq qaysi kinoteatr ekanini kelishmagan.
Wo treffen sie sich nach dem Missverständnis?|In einem Café|Tushunmovchilikdan keyin kafeda uchrashishadi.''',
'Über eine vergessene Einladung sprechen',
'Ben: Ich war traurig, weil du gestern nicht zu meinem Essen gekommen bist. Aziz: Das tut mir leid. Ich hatte den Termin für heute in meinen Kalender geschrieben. Ben: Ich dachte, du hast einfach keine Lust. Aziz: Nein, ich habe mich auf den Abend gefreut. Das war mein Fehler. Kann ich dich am Sonntag zum Mittagessen einladen? Ben: Gern. Aber schreib diesmal bitte den richtigen Tag auf. Aziz: Mache ich. Sonntag um eins bei mir? Ben: Ja, jetzt haben wir es beide klar.',
'''Für welchen Tag hatte Aziz den Termin notiert?|Für heute|Aziz uchrashuvni kecha o‘rniga bugun deb yozgan.
Wie fühlte sich Ben wegen Aziz’ Abwesenheit?|Traurig|Ben do‘sti kelmagani uchun xafa bo‘lgan.
Wann soll das neue Essen stattfinden?|Am Sonntag um eins|Yangi tushlik yakshanba soat birga belgilandi.''',
'Do‘stlar o‘rtasidagi noto‘g‘ri tushunishni rollarda hal qiling: his-tuyg‘u, izoh, uzr va yangi kelishuv.',
'A: Ich habe gestern lange gewartet und war enttäuscht. B: Es tut mir leid. Ich habe die Uhrzeit falsch verstanden. Ich dachte, wir treffen uns um sechs. A: Nächstes Mal schreiben wir alles auf. B: Ja. Kann ich dich morgen auf einen Kaffee einladen?',
'Ayblamasdan his-tuyg‘uni ayting va aniq yechim toping.',
'Unutilgan uchrashuv uchun 50–60 so‘zli uzr xati yozing.',
'Liebe Klara, es tut mir leid, dass ich gestern nicht gekommen bin. Ich hatte den falschen Tag aufgeschrieben. Du hast bestimmt auf mich gewartet, und das ärgert mich sehr. Können wir uns am Samstag um drei im Café am Markt treffen? Diesmal trage ich den Termin sofort richtig ein. Liebe Grüße, Rano',
'Uzr, aniq sabab va yangi taklif kiriting.')

add('Zusammen wohnen lernen',
'Seit zwei Monaten teilen sich drei Studierende eine Wohnung. Anfangs hat jeder geputzt, wenn er Zeit hatte. Bald war die Küche oft schmutzig, und niemand wusste, wer den Müll hinausbringen sollte. Bei einem gemeinsamen Frühstück sprechen sie darüber. Sie erstellen einen Plan: Jede Woche ist eine andere Person für die Küche zuständig. Das Bad reinigen sie abwechselnd am Samstag. Wer verreist, organisiert vorher einen Tausch. Der Plan hängt jetzt am Kühlschrank. Er löst nicht jedes Problem, aber die Gespräche werden freundlicher.',
'''Wie viele Studierende wohnen zusammen?|Drei|Kvartirada uch talaba birga yashaydi.
Wann wird das Bad gereinigt?|Am Samstag|Hammom shanba kuni navbat bilan tozalanadi.
Wo hängt der neue Plan?|Am Kühlschrank|Yangi jadval muzlatkichga osilgan.''',
'Besuch in der Wohngemeinschaft',
'Lena: Mein Bruder möchte am Wochenende bei uns schlafen. Ist das für dich in Ordnung? Murat: Grundsätzlich ja. Wie lange bleibt er? Lena: Von Freitagabend bis Sonntagmittag. Er schläft in meinem Zimmer. Murat: Gut. Ich muss am Samstag früh aufstehen, deshalb brauche ich Freitagabend etwas Ruhe. Lena: Verstehe. Wir gehen abends aus und kommen leise zurück. Murat: Dann passt es. Sag ihm bitte auch, dass wir die Haustür immer abschließen. Lena: Natürlich. Danke, dass wir das so einfach besprechen können. Ich schreibe es noch in unsere Gruppe.',
'''Bis wann bleibt Lenas Bruder?|Bis Sonntagmittag|U yakshanba tushgacha qoladi.
Warum braucht Murat am Freitagabend Ruhe?|Er muss am Samstag früh aufstehen|Murat shanba kuni erta turishi kerak.
Welche Türregel soll der Bruder kennen?|Die Haustür immer abschließen|Asosiy kirish eshigini doim qulflash lozim.''',
'Uy sherigingiz bilan mehmon qabul qilish bo‘yicha kelishing: muddat, joy va tinchlik.',
'A: Meine Schwester möchte zwei Nächte bei uns bleiben. Sie kann in meinem Zimmer schlafen. B: Das ist in Ordnung, aber ich lerne am Sonntag für eine Prüfung. A: Dann gehen wir am Nachmittag spazieren. B: Gut. Bitte sag ihr auch, wo sie ihre Sachen abstellen kann.',
'Mehmonning qolish muddati va sherigingiz ehtiyojini hisobga oling.',
'Uy guruhiga yangi tozalik jadvalini taklif qilib, 50–60 so‘z yozing.',
'Hallo zusammen, unsere Küche ist in letzter Zeit oft schmutzig. Ich schlage vor, dass jede Woche eine andere Person die Küche putzt. Wer nicht da ist, kann vorher mit jemandem tauschen. Können wir den Plan am Sonntag gemeinsam besprechen? Ich möchte, dass die Aufgaben für alle klar und fair sind. Viele Grüße, Murat',
'Muammo, amaliy taklif va birgalikda kelishish vaqtini yozing.')

add('Ein Fest für zwei Familien',
'Als Madina und Jonas zusammenziehen, möchten sie ihre Familien miteinander bekannt machen. Einige Verwandte sprechen nur wenig Deutsch. Deshalb planen sie kein langes gemeinsames Gespräch am Tisch, sondern mehrere kleine Aktivitäten. Jonas bereitet ein Bilderquiz vor. Madina zeigt, wie man einen einfachen Salat macht. Jeder darf etwas über sein Lieblingsessen erzählen. Die Kinder gestalten Namensschilder mit kleinen Zeichnungen. Am Ende tauschen die Gäste Telefonnummern aus. Madina freut sich, weil auch die stillen Gäste mitgemacht haben. Für sie ist das wichtiger als ein perfektes Fest.',
'''Warum planen Madina und Jonas kleine Aktivitäten?|Einige Verwandte sprechen wenig Deutsch|Ba’zi qarindoshlar kam nemischa bilgani uchun faoliyatlar yordam beradi.
Was bereitet Jonas vor?|Ein Bilderquiz|Jonas suratli viktorina tayyorlaydi.
Wer gestaltet die Namensschilder?|Die Kinder|Ism kartalarini bolalar tayyorlaydi.''',
'Ein Gast fragt nach',
'Gast: Vielen Dank für die Einladung. Ich kenne eure Familienfeier noch nicht. Soll ich etwas Besonderes beachten? Gastgeberin: Nein, komm einfach so, wie du dich wohlfühlst. Wir essen um sechs, aber die Gäste kommen ab fünf. Gast: Darf ich meine kleine Tochter mitbringen? Gastgeberin: Natürlich, andere Kinder sind auch da. Gast: Ich würde gern einen Kuchen backen. Gibt es etwas, das jemand nicht essen kann? Gastgeberin: Meine Schwester verträgt keine Nüsse. Wenn du den Kuchen ohne Nüsse machst, können mehr Leute davon essen. Gast: Gut, das mache ich.',
'''Ab wann kommen die Gäste?|Ab fünf|Mehmonlar soat beshdan boshlab kelishadi.
Wen möchte der Gast mitbringen?|Seine kleine Tochter / Die kleine Tochter|Mehmon kichik qizini olib kelmoqchi.
Ohne welche Zutat soll der Kuchen sein?|Ohne Nüsse|Mezbonning singlisi yoki opasi yong‘oqni ko‘tara olmaydi, shu sababli tort yong‘oqsiz bo‘lsin.''',
'Yangi tanishning oilaviy bayramiga borishdan oldin vaqt, kiyim va olib boriladigan narsa haqida so‘rang.',
'Vielen Dank für die Einladung. Wann soll ich kommen? Gibt es eine bestimmte Kleidung für das Fest? Ich möchte gern etwas mitbringen. Passt ein Kuchen, oder braucht ihr eher einen Salat? Ich freue mich darauf, deine Familie kennenzulernen.',
'Odatlarni taxmin qilmay, kamida uchta muloyim savol bering.',
'Mehmonlaringizga oilaviy uchrashuv haqida 50–60 so‘zli xat yozing.',
'Liebe Freunde, am Samstag möchten wir unsere Familien zusammenbringen. Ab fünf könnt ihr zu uns kommen, um sechs essen wir. Kinder sind herzlich willkommen. Wir planen ein kleines Bilderquiz, deshalb braucht niemand perfekt Deutsch zu sprechen. Bringt bitte nur gute Laune mit. Wenn ihr bestimmte Lebensmittel nicht essen könnt, sagt uns vorher Bescheid. Madina und Jonas',
'Vaqt, faoliyat va mehmon ehtiyojlarini so‘rashni kiriting.')

add('Ein Paket beim Nachbarn',
'Amina bestellt ein Regal für ihre Küche. Als das Paket kommt, ist sie bei der Arbeit. Der Lieferdienst gibt es bei ihrem Nachbarn ab und legt eine Karte in ihren Briefkasten. Am Abend klingelt Amina bei ihm. Das Paket ist schwer, deshalb hilft er ihr beim Tragen. Beim Öffnen sehen sie, dass ein Brett beschädigt ist. Amina fotografiert den Schaden und schreibt an den Kundenservice. Sie möchte nur das kaputte Teil ersetzen lassen, weil alle anderen Teile in Ordnung sind.',
'''Wer nimmt das Paket an?|Aminas Nachbar / Ihr Nachbar|Paketni Aminaning qo‘shnisi qabul qiladi.
Welcher Teil ist beschädigt?|Ein Brett|Tokchaning bitta taxtasi shikastlangan.
Was möchte Amina ersetzen lassen?|Nur das kaputte Teil|U faqat buzilgan qismni almashtirmoqchi.''',
'Ein Anruf beim Kundenservice',
'Mitarbeiterin: Guten Tag, wie kann ich helfen? Kunde: Meine Bestellung ist angekommen, aber es fehlt ein Teil. Mitarbeiterin: Was haben Sie bestellt? Kunde: Eine Schreibtischlampe. Der Fuß und die Lampe sind da, aber das Kabel fehlt. Mitarbeiterin: Haben Sie die Bestellnummer? Kunde: Ja, sie lautet vier sieben zwei neun. Mitarbeiterin: Danke. Wir schicken Ihnen das Kabel morgen ohne zusätzliche Kosten. Kunde: Muss ich die Lampe zurücksenden? Mitarbeiterin: Nein, behalten Sie sie bitte. Sie bekommen gleich eine Bestätigung per E-Mail. Kunde: Vielen Dank, das ist eine gute Lösung.',
'''Welches Teil fehlt bei der Lampe?|Das Kabel|Chiroqning kabeli yetishmayapti.
Wann wird das fehlende Teil verschickt?|Morgen|Kabel ertaga jo‘natiladi.
Muss der Kunde die Lampe zurücksenden?|Nein|Chiroqni qaytarib yuborish shart emas.''',
'Mijozlar xizmatiga yetishmayotgan qism haqida xabar bering va jo‘natish muddatini aniqlang.',
'Guten Tag, ich habe gestern mein Regal bekommen. Leider fehlen vier Schrauben. Die Bestellnummer ist 5832. Können Sie mir die Schrauben bitte schicken? Wann kommen sie ungefähr an? Ich möchte das Regal am Wochenende aufbauen. Vielen Dank für Ihre Hilfe.',
'Buyum, muammo va kerakli yechimni aniq ayting.',
'Shikastlangan mahsulot haqida 50–60 so‘zli muloyim shikoyat yozing.',
'Sehr geehrte Damen und Herren, gestern habe ich das bestellte Regal erhalten. Leider ist ein Brett beschädigt. Ein Foto finden Sie im Anhang. Die anderen Teile sind in Ordnung. Bitte schicken Sie mir ein neues Brett und erklären Sie, was ich mit dem beschädigten Teil machen soll. Meine Bestellnummer lautet 5832. Mit freundlichen Grüßen, Amina Saidova',
'Buyurtma raqami, nuqson va almashtirish talabini kiriting.')

add('Der verlorene Rucksack',
'Nach der Busfahrt bemerkt Emil, dass sein Rucksack fehlt. Darin sind ein Sporthemd, eine Wasserflasche und sein Bibliotheksausweis. Zum Glück hat er sein Handy in der Jackentasche. Er ruft beim Fundbüro des Verkehrsunternehmens an. Die Mitarbeiterin fragt nach der Linie, der Uhrzeit und der Farbe des Rucksacks. Emil kann alles genau beschreiben. Am nächsten Tag bekommt er einen Anruf: Der Fahrer hat den Rucksack gefunden. Emil holt ihn nachmittags ab und zeigt dabei seinen Ausweis. Er ist froh, dass nichts fehlt.',
'''Wo war Emils Handy während der Busfahrt?|In der Jackentasche|Telefon ryukzakda emas, kurtka cho‘ntagida bo‘lgan.
Wer hat den Rucksack gefunden?|Der Fahrer|Ryukzakni haydovchi topgan.
Was zeigt Emil bei der Abholung?|Seinen Ausweis|Olib ketishda shaxsini tasdiqlovchi hujjatini ko‘rsatadi.''',
'Eine Beschreibung am Telefon',
'Mitarbeiterin: Fundbüro, guten Tag. Anruferin: Ich habe gestern im Schwimmbad meine Uhr vergessen. Mitarbeiterin: Können Sie sie beschreiben? Anruferin: Sie ist rund und hat ein grünes Band. Auf der Rückseite steht mein Name, Lina. Mitarbeiterin: Einen Moment. Ja, eine solche Uhr liegt hier. Anruferin: Das ist wunderbar. Wann kann ich sie abholen? Mitarbeiterin: Heute bis sechzehn Uhr oder morgen ab neun. Bringen Sie bitte einen Ausweis mit. Anruferin: Heute schaffe ich es nicht. Ich komme morgen gegen zehn. Vielen Dank für Ihre Hilfe.',
'''Welche Farbe hat das Uhrenband?|Grün|Soat tasmasi yashil.
Welcher Name steht auf der Rückseite?|Lina|Orqa tomonida Lina ismi yozilgan.
Wann will Lina die Uhr abholen?|Morgen gegen zehn|Lina ertaga soat o‘n atrofida olmoqchi.''',
'Yo‘qolgan buyumni rangi, hajmi, ichidagi narsalar va yo‘qolgan joyi orqali tasvirlang.',
'Ich habe heute Morgen in der Linie fünf eine kleine blaue Tasche verloren. Darin sind ein Buch und eine rote Wasserflasche. Außen steht mein Name. Ich bin um acht am Markt ausgestiegen. Hat jemand die Tasche gefunden? Wie kann ich Sie später erreichen?',
'Buyumni ajratib turadigan uchta belgi va yo‘l tafsilotini ayting.',
'Topilmalar idorasiga 50–60 so‘zli yo‘qolgan buyum xati yozing.',
'Sehr geehrte Damen und Herren, gestern habe ich gegen vierzehn Uhr in der Linie acht meinen schwarzen Rucksack liegen lassen. Darin sind Sportschuhe und ein gelbes Handtuch. An der Seite hängt ein kleiner roter Schlüsselanhänger. Ich bin am Bahnhof ausgestiegen. Bitte informieren Sie mich, wenn der Rucksack gefunden wird. Vielen Dank. Mit freundlichen Grüßen, Emil Braun',
'Vaqt, joy va tanib olish uchun aniq belgilar kiriting.')

add('Ein Termin beim Bürgerbüro',
'Nach seinem Umzug möchte Bek seine neue Adresse beim Bürgerbüro anmelden. Auf der Internetseite liest er, welche Unterlagen er für seinen Termin mitbringen soll. Er legt alles in eine Mappe und notiert sich seine Fragen. Am Dienstag kommt er zehn Minuten früher an. Im Wartebereich zieht er keine Nummer, weil er bereits einen Termin hat. Eine Mitarbeiterin ruft seinen Namen auf. Während des Gesprächs versteht Bek ein Wort nicht und fragt nach. Die Mitarbeiterin erklärt es langsam. Danach prüft Bek die Angaben auf dem Formular.',
'''Warum geht Bek zum Bürgerbüro?|Er möchte seine neue Adresse anmelden|Bek yangi manzilini ro‘yxatdan o‘tkazmoqchi.
Warum zieht er keine Nummer?|Er hat bereits einen Termin|U oldindan qabulga yozilgan.
Was tut er, wenn er ein Wort nicht versteht?|Er fragt nach|Tushunmagan so‘zini qayta so‘raydi.''',
'Unterlagen vorbereiten',
'Guten Tag Frau Sodiqova, hier spricht Herr Meier vom Kursbüro. Für Ihren Beratungstermin am Donnerstag fehlen uns noch zwei Unterlagen: eine Kopie Ihres Zeugnisses und Ihr ausgefüllter Fragebogen. Sie können beides mitbringen oder vorher per E-Mail schicken. Das Originalzeugnis brauchen wir bei diesem Gespräch nicht. Der Termin bleibt um zehn Uhr in Raum fünf. Falls Sie den Fragebogen nicht finden, melden Sie sich bitte bei uns. Wir schicken ihn dann noch einmal. Die Beratung dauert ungefähr fünfundvierzig Minuten. Vielen Dank und bis Donnerstag.',
'''Welche zwei Unterlagen fehlen?|Eine Zeugniskopie und der ausgefüllte Fragebogen|Attestat yoki diplom nusxasi hamda to‘ldirilgan so‘rovnoma kerak.
In welchem Raum findet der Termin statt?|In Raum fünf|Uchrashuv beshinchi xonada.
Wie lange dauert die Beratung ungefähr?|Fünfundvierzig Minuten|Maslahat taxminan qirq besh daqiqa davom etadi.''',
'Idorada tushunmagan so‘z yoki shakl maydoni haqida muloyim tushuntirish so‘rang.',
'Entschuldigung, was bedeutet dieses Wort hier? Können Sie das bitte einfacher erklären? Soll ich hier meine alte oder meine neue Adresse eintragen? Danke. Ich lese die Angaben noch einmal durch. Ist das Formular jetzt vollständig?',
'Ikki aniqlashtiruvchi savol va yakuniy tekshiruv savolini bering.',
'Maslahat uchrashuvini boshqa kunga ko‘chirish uchun 50 so‘z atrofida rasmiy xat yozing.',
'Sehr geehrter Herr Meier, leider kann ich am Donnerstag um zehn Uhr nicht zu unserem Beratungstermin kommen, weil ich arbeiten muss. Wäre ein Termin am Freitagvormittag möglich? Die Zeugniskopie und den Fragebogen schicke ich Ihnen schon heute per E-Mail. Bitte entschuldigen Sie die Änderung. Vielen Dank für Ihre Hilfe. Mit freundlichen Grüßen, Lola Sodiqova',
'Eski vaqt, sabab va aniq muqobil vaqtni yozing.')

add('Wohnen näher am Arbeitsplatz',
'Seit einem Jahr fährt Dilshod jeden Tag neunzig Minuten zur Arbeit. Nun hat er eine Wohnung in der Nähe seines Büros gefunden. Sie ist kleiner und teurer als seine jetzige Wohnung. Dafür könnte er zu Fuß arbeiten gehen und hätte abends mehr Zeit. Seine Freunde wohnen allerdings im alten Viertel. Dilshod schreibt deshalb eine Liste mit Vor- und Nachteilen. Er entscheidet noch nicht sofort. Zuerst besucht er die neue Gegend am Abend, um zu sehen, wie laut es dort ist und welche Geschäfte geöffnet sind.',
'''Wie lange dauert Dilshods Arbeitsweg bisher?|Neunzig Minuten|Hozir ishga borishiga to‘qson daqiqa ketadi.
Wie ist die neue Wohnung im Vergleich zur alten?|Kleiner und teurer|Yangi kvartira kichikroq va qimmatroq.
Wann besucht er die neue Gegend?|Am Abend|Hududni kechqurun tekshirib ko‘radi.''',
'Zwei Zimmer vergleichen',
'Maklerin: Das erste Zimmer liegt zum Hof und kostet vierhundert Euro. Das zweite hat einen Balkon, liegt aber zur Straße und kostet fünfzig Euro mehr. Interessentin: Ist das Internet bei beiden dabei? Maklerin: Ja. Küche und Bad teilen Sie mit zwei anderen Personen. Interessentin: Ich lerne oft zu Hause und brauche Ruhe. Deshalb gefällt mir das erste Zimmer besser. Kann ich die Mitbewohner kennenlernen? Maklerin: Natürlich. Sie sind heute ab sechs da. Interessentin: Dann komme ich noch einmal. Eine nette Wohngemeinschaft ist mir wichtiger als ein Balkon.',
'''Wie viel kostet das zweite Zimmer?|Vierhundertfünfzig Euro / 450 Euro|400 yevrodan 50 yevro qimmatroq, demak 450 yevro.
Warum bevorzugt die Interessentin das erste Zimmer?|Sie braucht Ruhe|U uyda o‘qigani uchun tinchlikka muhtoj.
Ab wann sind die Mitbewohner zu Hause?|Ab sechs|Uy sheriklari soat oltidan uyda bo‘lishadi.''',
'Ikki kvartirani narx, joy va qulaylik bo‘yicha taqqoslab tanlovingizni ayting.',
'Die erste Wohnung ist günstiger, aber weit von meiner Arbeit entfernt. Die zweite ist kleiner, liegt jedoch direkt im Zentrum. Für mich ist ein kurzer Arbeitsweg sehr wichtig. Deshalb würde ich die zweite Wohnung wählen, wenn sie am Abend ruhig genug ist.',
'Kamida ikki taqqoslash va tanlov sababi bo‘lsin.',
'Do‘stingizga ko‘chish haqidagi ikkilanishingizni tushuntirib, 50–60 so‘zda maslahat so‘rang.',
'Lieber Sam, ich habe eine Wohnung nahe bei meiner Arbeit gefunden. Sie ist kleiner als meine jetzige Wohnung und kostet mehr. Dafür spare ich jeden Tag viel Zeit. Ich würde aber unsere gemeinsamen Abende im Viertel vermissen. Was würdest du an meiner Stelle tun? Am Freitag sehe ich mir die Wohnung noch einmal an. Viele Grüße, Dilshod',
'Bir afzallik, bir kamchilik va aniq maslahat savoli yozing.')

add('Ein Ausflug mit begrenztem Geld',
'Die Lerngruppe möchte am Sonntag einen Ausflug machen. Für jeden dürfen Fahrt und Eintritt zusammen höchstens fünfzehn Euro kosten. Ein Freizeitpark fällt aus, weil allein der Eintritt teurer ist. Ein See ist kostenlos, aber mit dem Bus schwer erreichbar. Schließlich schlägt Eda einen Stadtwald vor. Die Gruppe kann mit einer günstigen Gruppenkarte fahren. Dort gibt es einen Rundweg und einen Platz zum Picknicken. Alle bringen Essen von zu Hause mit. Zwei Personen prüfen vorher den Weg, damit auch ein Teilnehmer mit Kinderwagen gut mitkommen kann.',
'''Wie hoch ist das Budget pro Person für Fahrt und Eintritt?|Höchstens fünfzehn Euro|Yo‘l va kirish uchun har kishiga ko‘pi bilan 15 yevro.
Welches Ziel wählt die Gruppe schließlich?|Den Stadtwald|Oxirida shahar o‘rmoni tanlanadi.
Warum prüfen zwei Personen den Weg vorher?|Wegen eines Teilnehmers mit Kinderwagen|Bolalar aravachasi bilan keladigan ishtirokchi uchun yo‘lni tekshirishadi.''',
'Das Picknick vorbereiten',
'Eda: Für Sonntag fehlen uns noch ein paar Dinge. Wer bringt eine Decke mit? Nuri: Ich habe eine große. Die nehme ich mit. Eda: Super. Wir brauchen auch Wasser. Nuri: Jeder könnte seine eigene Flasche füllen. Dann müssen wir keine schweren Kisten tragen. Eda: Gute Idee. Ich schreibe das in die Gruppe. Und wer kauft die Fahrkarte? Nuri: Das mache ich am Automaten. Gib mir bitte vorher die genaue Personenzahl. Eda: Bis Freitag sagen alle Bescheid. Bei starkem Regen verschieben wir den Ausflug um eine Woche.',
'''Was bringt Nuri mit?|Eine große Decke|Nuri katta to‘shama olib keladi.
Welche Information braucht Nuri für die Fahrkarte?|Die genaue Personenzahl|Chipta olish uchun aniq odamlar soni kerak.
Was passiert bei starkem Regen?|Der Ausflug wird um eine Woche verschoben|Kuchli yomg‘irda sayr bir haftaga suriladi.''',
'Cheklangan byudjet bilan guruh sayrini rejalang: manzil, transport, ovqat va vazifalar.',
'A: Wir können höchstens fünfzehn Euro ausgeben. Wie wäre es mit dem Stadtwald? B: Gut, dort kostet der Eintritt nichts. Ich kümmere mich um die Gruppenkarte. A: Ich frage, wer mitkommt. Jeder bringt etwas zu essen mit. B: Und bei Regen fahren wir eine Woche später.',
'Byudjetga mos qaror va kamida ikkita mas’uliyatni kelishing.',
'Guruhga 50–60 so‘zli sayr e’loni yozing; ro‘yxatdan o‘tish muddati ham bo‘lsin.',
'Hallo zusammen, am Sonntag fahren wir in den Stadtwald. Wir treffen uns um neun am Bahnhof und kaufen eine Gruppenkarte. Bringt bitte Essen, Wasser und feste Schuhe mit. Meldet euch bis Freitag, damit wir die Personenzahl kennen. Bei starkem Regen verschieben wir den Ausflug. Wir freuen uns auf euch! Eda und Nuri',
'Uchrashuv, kerakli buyumlar va javob muddatini kiriting.')

add('Gebraucht statt neu',
'Als ihr Tisch kaputtgeht, möchte Rano nicht sofort einen neuen kaufen. Sie sucht im Internet nach gebrauchten Möbeln in ihrer Nähe. Ein Nachbar bietet einen stabilen Holztisch günstig an. Auf den Fotos sieht er gut aus, hat aber einige Kratzer. Rano fragt nach den Maßen und misst ihre Küche aus. Der Tisch passt. Bei der Abholung prüft sie, ob alle Beine fest sind. Ihre Freundin hilft beim Transport. Gemeinsam reinigen sie den Tisch. Rano freut sich über den niedrigen Preis und darüber, dass der Tisch weiter benutzt wird.',
'''Was fragt Rano vor dem Kauf?|Die Maße / Nach den Maßen|Xariddan oldin stolning o‘lchamlarini so‘raydi.
Welche sichtbaren Spuren hat der Tisch?|Einige Kratzer|Stolda bir nechta tirnalgan joy bor.
Wer hilft beim Transport?|Ihre Freundin|Tashishda dugonasi yordam beradi.''',
'Eine Anzeige besprechen',
'Käufer: Guten Abend. Sie verkaufen ein Fahrrad. Ist es noch da? Verkäuferin: Ja. Es ist fünf Jahre alt, aber ich habe es regelmäßig benutzt und gepflegt. Käufer: Funktionieren Licht und Bremsen? Verkäuferin: Die Bremsen funktionieren. Das vordere Licht muss repariert werden. Deshalb ist der Preis niedrig. Käufer: Kann ich es morgen ansehen und kurz ausprobieren? Verkäuferin: Ja, ab siebzehn Uhr bin ich zu Hause. Käufer: Gut. Ich komme um halb sechs. Bezahlen möchte ich erst, wenn ich das Fahrrad gesehen habe. Verkäuferin: Natürlich, das ist in Ordnung.',
'''Wie alt ist das Fahrrad?|Fünf Jahre|Velosiped besh yillik.
Was muss repariert werden?|Das vordere Licht|Oldingi chiroqni ta’mirlash kerak.
Wann kommt der Käufer?|Um halb sechs / Um siebzehn Uhr dreißig|Xaridor 17:30 da keladi.''',
'Ishlatilgan buyum sotuvchisidan holati, o‘lchami yoki yoshi va ko‘rish vaqtini so‘rang.',
'Guten Tag, ich interessiere mich für Ihren Schreibtisch. Wie breit ist er? Hat er Schäden, die man auf den Fotos nicht sieht? Könnte ich ihn am Samstag ansehen? Wenn er in mein Zimmer passt, würde ich ihn gern mitnehmen. Kann man die Beine für den Transport abschrauben?',
'Xarid uchun muhim uchta aniq savol bering.',
'Sotmoqchi bo‘lgan ishlatilgan buyumingiz haqida 50 so‘z atrofida halol e’lon yozing.',
'Ich verkaufe meinen kleinen Küchentisch aus Holz für dreißig Euro. Er ist achtzig Zentimeter breit und gut für zwei Personen geeignet. Auf der Oberfläche gibt es einige Kratzer, aber der Tisch steht stabil. Abholung ist am Wochenende möglich. Die Beine lassen sich abschrauben. Bei Interesse schreiben Sie mir bitte eine Nachricht.',
'Narx, holat, o‘lcham va olib ketish shartini yozing.')

add('Eine hilfreiche App mit Grenzen',
'Für ihre Wege durch die neue Stadt benutzt Lola eine Fahrplan-App. Sie findet schnell heraus, welcher Bus fährt und wo sie umsteigen muss. Eines Abends zeigt ihr die App jedoch eine Haltestelle an, die wegen Bauarbeiten geschlossen ist. Lola liest das Schild vor Ort und fragt einen Fahrer. Er erklärt ihr den Weg zur Ersatzhaltestelle. Seitdem verlässt sie sich nicht nur auf das Handy. Vor wichtigen Terminen plant sie etwas zusätzliche Zeit ein und schaut auch auf die aktuellen Hinweise an der Haltestelle.',
'''Warum ist die angezeigte Haltestelle geschlossen?|Wegen Bauarbeiten|Bekat qurilish ishlari sabab yopilgan.
Wen fragt Lola nach dem richtigen Weg?|Einen Fahrer|Lola haydovchidan so‘raydi.
Was plant sie vor wichtigen Terminen zusätzlich ein?|Etwas zusätzliche Zeit|Muhim uchrashuvlarga borishda qo‘shimcha vaqt ajratadi.''',
'Hilfe beim Onlineformular',
'Vater: Ich möchte mich für den Kurs anmelden, aber das Formular geht nicht weiter. Tochter: Welches Feld ist rot markiert? Vater: Hier steht Telefonnummer. Ich habe meine Nummer eingetragen. Tochter: Da ist vielleicht ein Leerzeichen zu viel. Versuch es ohne Leerzeichen. Vater: Jetzt klappt es. Soll ich überall ein Häkchen setzen? Tochter: Lies erst, was dort steht. Dieser Punkt ist nur für Werbung. Den musst du nicht auswählen. Vater: Gut, ich möchte keine Werbung. Tochter: Bevor du abschickst, prüfe noch einmal Namen, Kurs und Termin.',
'''Welches Feld ist rot markiert?|Telefonnummer|Qizil belgilangan maydon telefon raqami maydoni.
Was soll der Vater aus der Nummer entfernen?|Das zusätzliche Leerzeichen / Die Leerzeichen|Raqamdagi ortiqcha bo‘shliqni olib tashlash tavsiya qilinadi.
Wofür ist das freiwillige Häkchen?|Für Werbung|Majburiy bo‘lmagan belgi reklama olishga tegishli.''',
'Oddiy onlayn vazifani sherigingizga tushuntiring va ma’lumotni yuborishdan oldin tekshirishni ayting.',
'Öffne zuerst die Kursseite und wähle den passenden Termin. Danach trägst du deinen Namen und deine E-Mail-Adresse ein. Lies die Hinweise unter dem Formular. Du musst Werbung nicht auswählen. Prüfe am Ende alle Angaben. Erst dann klickst du auf Absenden.',
'Amallar tartibi va yakuniy tekshiruvni tushuntiring.',
'Ilovadagi noto‘g‘ri ma’lumot haqida xizmat jamoasiga 50–60 so‘zli xat yozing.',
'Sehr geehrtes Team, Ihre App zeigt die Haltestelle Marktstraße noch als geöffnet an. Heute stand ich dort, aber wegen Bauarbeiten fahren die Busse an einer Ersatzhaltestelle ab. Bitte prüfen Sie diese Information und ergänzen Sie den neuen Standort. Für Menschen, die die Stadt nicht kennen, wäre das sehr hilfreich. Vielen Dank. Mit freundlichen Grüßen, Lola',
'Xato, kuzatilgan holat va so‘ralgan tuzatishni yozing.')

add('Eine kleine Ausstellung im Kurs',
'Zum Ende des Semesters organisiert der Deutschkurs eine Ausstellung über Lieblingsorte. Jeder Teilnehmer bringt ein selbst gemachtes Foto mit und schreibt einen kurzen Text dazu. Farid wählt den Hof seiner Großeltern, obwohl er weit weg liegt. Er beschreibt den alten Baum und die gemeinsamen Mahlzeiten im Sommer. Andere zeigen einen Park, einen Sportplatz oder eine Küche. Am Ausstellungstag hängen die Fotos an einer langen Wand. Die Besucher lesen die Texte und stellen Fragen. Farid merkt, dass er länger auf Deutsch erzählen kann als noch vor einigen Monaten.',
'''Was bringt jeder Teilnehmer mit?|Ein selbst gemachtes Foto|Har ishtirokchi o‘zi olgan suratni olib keladi.
Welchen Ort wählt Farid?|Den Hof seiner Großeltern|Farid buvisi va bobosining hovlisini tanlaydi.
Was tun die Besucher außer Lesen?|Sie stellen Fragen|Mehmonlar matnlarni o‘qish bilan birga savollar berishadi.''',
'Die Ausstellung aufbauen',
'Lehrerin: Wir haben noch eine Stunde bis zur Eröffnung. Wer kann die Texte neben die Bilder hängen? Amina: Das mache ich mit Ben. Einige Texte sind aber schwer zu lesen. Lehrerin: Dann drucken wir sie größer aus. Nuri, kannst du dabei helfen? Nuri: Ja, ich gehe zum Computer. Brauchen wir auch Namensschilder? Lehrerin: Nur Vornamen reichen. Amina: Wo stellen wir die Getränke hin? Lehrerin: Auf den Tisch am Fenster, weit genug von den Fotos entfernt. Ben: Und wer begrüßt die Gäste? Lehrerin: Das übernehme ich zusammen mit Farid.',
'''Warum sollen manche Texte neu gedruckt werden?|Sie sind schwer zu lesen|Ba’zi matnlarni o‘qish qiyin, shuning uchun kattaroq chiqariladi.
Welche Namen sollen auf die Schilder?|Nur Vornamen|Kartalarda faqat ismlar bo‘lishi kerak.
Wer begrüßt die Gäste mit der Lehrerin?|Farid|Mehmonlarni o‘qituvchi bilan Farid kutib oladi.''',
'Sevimli joyingiz haqida bir daqiqalik kichik taqdimot qiling: ko‘rinishi, xotira va sabab.',
'Mein Lieblingsort ist der Hof meiner Großeltern. Dort steht ein großer Baum, und im Sommer sitzen wir in seinem Schatten. Als Kind habe ich dort mit meinen Cousins gespielt. Heute besuche ich den Hof seltener. Trotzdem fühle ich mich dort sofort zu Hause, weil viele schöne Erinnerungen mit diesem Ort verbunden sind.',
'Joy tasviri bilan shaxsiy xotirani bog‘lang.',
'Kurs ko‘rgazmasidagi suratingiz uchun 50–60 so‘zli izoh yozing.',
'Auf meinem Foto sieht man einen kleinen Park in meiner Nähe. Ich gehe oft nach dem Deutschkurs dorthin. Besonders gefällt mir die Bank unter dem großen Baum. Dort lese ich oder spreche mit Freunden. Im Winter ist der Park still, im Sommer spielen viele Kinder dort. Für mich ist er ein Ort der Ruhe.',
'Suratdagi aniq belgilar va shaxsiy ahamiyatni yozing.')

add('Ein Wochenende selbst organisieren',
'Vier Freunde wollen nach einem halben Jahr Deutschlernen gemeinsam verreisen. Sie haben unterschiedliche Wünsche: Ben möchte wandern, Amina ein Museum besuchen, und Farid braucht eine günstige Unterkunft. Eda sammelt zuerst alle Vorschläge. Dann findet die Gruppe eine Jugendherberge in einer kleinen Stadt am Wald. Am Samstag planen sie eine kurze Wanderung, am Sonntag einen Museumsbesuch. Sie buchen erst, nachdem alle den Preis bestätigt haben. Jeder übernimmt eine Aufgabe. Die Freunde merken, dass sie auf Deutsch nicht nur Informationen verstehen, sondern auch gemeinsam Entscheidungen treffen können.',
'''Welche Unterkunft findet die Gruppe?|Eine Jugendherberge|Guruh yoshlar yotoqxonasini topadi.
Was planen die Freunde für Sonntag?|Einen Museumsbesuch|Yakshanba kuni muzeyga borishadi.
Wann buchen sie?|Nachdem alle den Preis bestätigt haben|Hamma narxga roziligini bildirgandan keyin bron qilishadi.''',
'Vor der Abfahrt',
'Eda: Sind wir für morgen bereit? Farid: Fast. Die Unterkunft ist bestätigt, und ich habe die Adresse ausgedruckt. Ben: Ich habe den Wanderweg geprüft. Er ist fünf Kilometer lang und nicht schwer. Amina: Die Museumsführung beginnt am Sonntag um elf. Wir sollen zehn Minuten früher da sein. Eda: Gut. Unser Zug fährt morgen um acht Uhr zwanzig. Treffen wir uns um acht vor dem Bahnhof? Farid: Ja. Ich bringe die Fahrkarten mit. Ben: Und falls jemand krank wird? Eda: Dann bitte sofort in der Gruppe Bescheid sagen, damit wir gemeinsam neu planen können.',
'''Wie lang ist der Wanderweg?|Fünf Kilometer|Piyoda yo‘l besh kilometr.
Wann beginnt die Museumsführung?|Am Sonntag um elf|Muzey ekskursiyasi yakshanba soat o‘nda emas, o‘n birda boshlanadi.
Wer bringt die Fahrkarten mit?|Farid|Chiptalarni Farid olib keladi.''',
'A2 yakuniy mashqi: ikki kunlik safarni birga rejalang. Har bir kishi istak bildirsin va bir vazifa olsin.',
'A: Ich würde gern wandern, aber nicht den ganzen Tag. B: Dann machen wir am Samstag einen kurzen Weg und besuchen am Sonntag das Museum. A: Einverstanden. Ich prüfe den Weg. B: Ich suche eine günstige Unterkunft. A: Bevor wir buchen, vergleichen wir die Kosten. B: Ja, und wir treffen uns morgen für die Entscheidung.',
'Istaklar, murosa, narx va vazifalarni kelishing.',
'Safar guruhiga 60 so‘z atrofida yakuniy reja yuboring; vaqt, vazifalar va o‘zgarish holati bo‘lsin.',
'Hallo zusammen, unser Wochenende steht fest. Wir treffen uns am Samstag um acht vor dem Bahnhof. Farid bringt die Fahrkarten mit. Am Nachmittag wandern wir, am Sonntag besuchen wir das Museum. Bitte packt feste Schuhe und eine Wasserflasche ein. Wenn jemand nicht mitkommen kann, sagt sofort Bescheid. Ich freue mich auf unsere gemeinsame Reise! Viele Grüße, Eda',
'Uchrashuv, ikki kunlik dastur va xabar berish qoidasini yozing.')

add('Ein Hof wird grüner',
'Hinter einem großen Wohnhaus liegt ein grauer Hof, der bisher hauptsächlich als Abstellplatz genutzt wurde. Im Frühling schlägt eine Bewohnerin vor, dort gemeinsam Pflanzen anzubauen. Einige Nachbarn sind begeistert, andere befürchten zusätzliche Arbeit und höhere Kosten. Deshalb beginnt die Gruppe mit drei gebrauchten Holzkisten statt mit einer großen Anlage. Die Hausverwaltung erlaubt das Projekt unter der Bedingung, dass der Rettungsweg frei bleibt. Sechs Haushalte teilen sich das Gießen. Eine Liste hängt im Treppenhaus, damit auch neue Bewohner mitmachen können. Nach zwei Monaten wachsen Kräuter und Tomaten. Besonders überraschend ist für die Beteiligten, wie oft sie nun miteinander sprechen. Nicht jede Pflanze überlebt, doch die Gruppe lernt aus den Fehlern. Im nächsten Jahr möchte sie Regenwasser sammeln, bevor sie weitere Kisten aufstellt.',
'''Mit wie vielen Holzkisten beginnt das Projekt?|Mit drei|Loyiha katta inshootdan emas, uchta ishlatilgan yog‘och qutidan boshlanadi.
Welche Bedingung stellt die Hausverwaltung?|Der Rettungsweg muss frei bleiben|Favqulodda chiqish yo‘li to‘silmasligi kerak.
Was möchte die Gruppe vor einer Erweiterung tun?|Regenwasser sammeln|Yangi qutilardan oldin yomg‘ir suvini yig‘ishni yo‘lga qo‘ymoqchi.''',
'Eine Diskussion über den Gemeinschaftsgarten',
'Sprecherin: In unserer Hausversammlung geht es heute um den Garten. Herr Beck, was wünschen Sie sich? Herr Beck: Ich finde das Projekt schön, aber am Wochenende stehen oft Gießkannen auf dem Weg. Mit meinem Rollator komme ich dann schlecht durch. Frau Öz: Danke für den Hinweis. Wir können einen festen Platz für die Geräte markieren. Herr Beck: Das würde helfen. Außerdem weiß ich nicht, wen ich bei Problemen ansprechen soll. Frau Öz: Dann hängen wir die Namen von zwei Ansprechpersonen aus. Sprecherin: Gibt es weitere Vorschläge? Bewohner: Wir sollten einmal im Monat einen gemeinsamen Gartennachmittag anbieten. So können auch Menschen helfen, die nicht regelmäßig gießen können. Frau Öz: Einverstanden. Wir probieren das zunächst im Juni und fragen danach, ob die Zeit für alle passt.',
'''Was behindert Herrn Beck auf dem Weg?|Gießkannen|Yo‘lda qolgan sug‘orish idishlari yurishga xalaqit beradi.
Wie viele Ansprechpersonen sollen genannt werden?|Zwei|Muammo bo‘yicha bog‘lanish uchun ikki kishi ko‘rsatiladi.
Wie oft soll ein gemeinsamer Gartennachmittag stattfinden?|Einmal im Monat|Birgalikdagi bog‘ kuni oyiga bir marta taklif qilinadi.''',
'Mahalladagi umumiy bog‘ loyihasi haqida 1–2 daqiqalik fikr bildiring: foyda, qiyinchilik va yechim.',
'Ein Gemeinschaftsgarten kann unser Haus freundlicher machen. Man baut nicht nur Gemüse an, sondern lernt auch Nachbarn kennen. Allerdings darf die Arbeit nicht immer bei denselben Personen bleiben. Deshalb würde ich klein anfangen und einen einfachen Plan erstellen. Wer wenig Zeit hat, könnte Geräte reparieren oder beim Einkauf helfen. Wichtig ist außerdem, dass alle Wege frei bleiben. Nach zwei Monaten sollten wir gemeinsam prüfen, was gut funktioniert.',
'Bir foyda, bir xavotir va unga mos yechimni asoslang.',
'Uy boshqaruviga umumiy bog‘ uchun 70–90 so‘zli ruxsat so‘rovi yozing: joy, mas’uliyat va yo‘llarni ochiq saqlash.',
'Sehr geehrte Frau Berg, einige Bewohner möchten im Hof einen kleinen Gemeinschaftsgarten anlegen. Für den Anfang planen wir drei Pflanzkisten an der hinteren Wand. Die Wege und der Zugang zum Haus bleiben dabei frei. Sechs Haushalte würden das Gießen und die Pflege übernehmen. Die Kosten für Pflanzen tragen wir selbst. Dürfen wir Ihnen unseren Plan bei der nächsten Hausversammlung vorstellen? Gern prüfen wir gemeinsam, welcher Standort geeignet ist. Über eine Rückmeldung würden wir uns freuen. Mit freundlichen Grüßen, Amina Saidova',
'Aniq loyiha, ish taqsimoti va muloyim ruxsat so‘rovini yozing.')

add('Reparieren als gemeinsames Lernen',
'Ein Jugendzentrum veranstaltet jeden zweiten Samstag ein Reparaturcafé. Besucher bringen kaputte Alltagsgegenstände mit und versuchen gemeinsam mit Freiwilligen, die Fehler zu finden. Eine Reparatur wird nicht versprochen; manchmal fehlen Ersatzteile oder ein Gerät lässt sich nicht sicher öffnen. Trotzdem gehen viele Gäste zufrieden nach Hause, weil sie etwas gelernt haben. Am letzten Termin brachte ein Schüler einen Rucksack mit gerissenem Träger. Eine ältere Besucherin zeigte ihm, wie man die Naht verstärkt. An einem anderen Tisch wurde ein wackeliger Stuhl wieder stabil. Die Organisatoren möchten bewusst keine kostenlose Werkstatt ersetzen. Ihnen geht es um Austausch und einen sorgfältigeren Umgang mit Dingen. Für komplizierte elektrische Geräte verweisen sie an Fachbetriebe. Künftig soll eine Liste zeigen, welche Werkzeuge vorhanden sind, damit niemand unnötig etwas Neues kauft.',
'''Wie oft findet das Reparaturcafé statt?|Jeden zweiten Samstag|Ta’mirlash uchrashuvi har ikkinchi shanba kuni bo‘ladi.
Was war am Rucksack kaputt?|Der Träger / Ein gerissener Träger|Ryukzakning tasmasi yirtilgan edi.
Wohin verweist das Team bei komplizierten elektrischen Geräten?|An Fachbetriebe|Murakkab elektr jihozlari uchun mutaxassis korxonalarga yo‘naltirishadi.''',
'Neu kaufen oder reparieren?',
'Leyla: Mein Wasserkocher funktioniert nicht mehr. Ich wollte heute einen neuen bestellen. Jonas: Hast du schon geprüft, ob sich eine Reparatur lohnt? Leyla: Nein. Ich weiß auch nicht, wer das machen könnte. Jonas: Im Viertel gibt es einen Fachladen. Dort kannst du zunächst nach den Kosten fragen. Leyla: Wenn die Reparatur fast so teuer ist wie ein neues Gerät, würde ich lieber neu kaufen. Jonas: Das verstehe ich. Für mich spielt auch eine Rolle, ob Ersatzteile erhältlich sind. Leyla: Stimmt. Bei einem neuen Gerät sollte ich darauf achten. Jonas: Du könntest dir für ein paar Tage meinen zweiten Wasserkocher leihen. Dann musst du nicht sofort entscheiden. Leyla: Danke, das nimmt den Zeitdruck. Ich frage morgen im Laden nach und vergleiche anschließend die Möglichkeiten.',
'''Welches Gerät ist kaputt?|Der Wasserkocher|Buzilgan jihoz elektr choynak.
Wo soll Leyla nach Reparaturkosten fragen?|In einem Fachladen im Viertel|Mahalladagi ixtisoslashgan do‘konda ta’mir narxini so‘rash tavsiya qilinadi.
Was bietet Jonas vorübergehend an?|Seinen zweiten Wasserkocher|Jonas vaqtincha ikkinchi choynagini berishni taklif qiladi.''',
'Ta’mirlash va yangi sotib olishni taqqoslang; narx, vaqt va ehtiyot qismlar asosida qaror ayting.',
'Ich würde ein kaputtes Gerät nicht sofort wegwerfen. Zuerst möchte ich wissen, was die Reparatur kostet und wie lange sie dauert. Bei einem günstigen, sehr alten Gerät kann ein Neukauf sinnvoll sein. Wenn jedoch nur ein kleines Teil fehlt, finde ich eine Reparatur besser. Wichtig sind für mich auch verfügbare Ersatzteile. Um ohne Zeitdruck zu entscheiden, könnte ich mir vorübergehend ein Gerät leihen.',
'Qarorni kamida uchta mezon bilan tushuntiring.',
'Mahalla forumiga ta’mirlash tadbirini qo‘llab-quvvatlovchi 70–90 so‘zli fikr yozing; cheklovini ham ayting.',
'Ich würde ein Reparaturcafé in unserem Viertel begrüßen. Viele Dinge werden weggeworfen, obwohl nur eine Naht oder eine Schraube kaputt ist. Gemeinsam könnten wir lernen, solche kleinen Probleme selbst zu lösen. Wichtig wäre aber, ehrlich über die Grenzen zu informieren: Nicht jedes Gerät kann repariert werden, und für schwierige elektrische Arbeiten brauchen wir Fachleute. Ein monatlicher Termin im Jugendzentrum wäre ein guter Anfang. Ich könnte bei der Anmeldung helfen und eine Liste der benötigten Werkzeuge führen. Wer hätte ebenfalls Interesse?',
'Afzallik, cheklov va shaxsiy yordam taklifini kiriting.')

add('Weniger Abfall beim Straßenfest',
'Das Organisationsteam eines Straßenfestes möchte in diesem Jahr weniger Einwegverpackungen verwenden. Beim letzten Fest waren die Müllbehälter schon nach zwei Stunden voll. Nun sollen Getränke in wiederverwendbaren Bechern ausgegeben werden. Für jeden Becher zahlen Gäste zwei Euro Pfand, die sie bei der Rückgabe erhalten. Einige Verkaufsstände sorgen sich, dass dadurch lange Schlangen entstehen. Deshalb plant das Team zwei getrennte Rückgabestellen. Außerdem dürfen Besucher eigene saubere Behälter für Essen mitbringen, wenn der jeweilige Stand das anbietet. Die Werbung nennt nicht nur die neuen Regeln, sondern erklärt auch ihren Zweck. Nach dem Fest will das Team die Abfallmenge mit dem Vorjahr vergleichen. Erst dann kann es beurteilen, welche Maßnahmen tatsächlich geholfen haben und was beim nächsten Mal verbessert werden sollte.',
'''Wie hoch ist das Pfand für einen Becher?|Zwei Euro|Har stakan uchun qaytariladigan garov ikki yevro.
Warum sind zwei Rückgabestellen geplant?|Damit keine langen Schlangen entstehen|Uzun navbatlarning oldini olish uchun ikki qaytarish joyi rejalangan.
Womit soll die Abfallmenge verglichen werden?|Mit dem Vorjahr|Chiqindi miqdori o‘tgan yilgi miqdor bilan taqqoslanadi.''',
'Den Einkauf anders organisieren',
'Moderator: In unserer Gesprächsrunde erzählt Rano, wie sie beim Einkaufen Verpackungen vermeiden möchte. Rano: Früher habe ich oft kleine Portionen gekauft, weil das bequem war. Jetzt plane ich zuerst, was wir wirklich essen werden. Moderator: Kaufen Sie alles unverpackt? Rano: Nein, das klappt bei mir nicht. Manche Produkte bekomme ich in der Nähe nur verpackt. Außerdem wäre eine große Packung keine gute Lösung, wenn die Hälfte verdirbt. Moderator: Was hat sich besonders bewährt? Rano: Eine Liste und zwei Stoffbeutel in meinem Rucksack. So kaufe ich weniger spontan. Moderator: Ist Ihr Einkauf dadurch billiger geworden? Rano: Nicht immer. Ich habe die Kosten bisher nicht genau verglichen. Aber ich werfe deutlich weniger Lebensmittel weg. Als Nächstes möchte ich eine Woche lang notieren, welche Reste trotzdem entstehen.',
'''Was plant Rano zuerst?|Was die Familie wirklich essen wird|Avval oilasi amalda nima yeyishini rejalaydi.
Welche zwei Hilfsmittel haben sich bewährt?|Eine Liste und zwei Stoffbeutel|Ro‘yxat va ikkita mato sumka foyda bergan.
Was will sie eine Woche lang notieren?|Welche Reste entstehen|Bir hafta davomida qanday qoldiqlar paydo bo‘lishini yozmoqchi.''',
'Tadbirda chiqindini kamaytirish uchun reja taklif qiling; navbat va qulaylikka oid e’tirozga javob bering.',
'Für unser Fest schlage ich Becher mit Pfand vor. Dadurch könnten wir viele Einwegbecher vermeiden. Ich verstehe aber die Sorge, dass die Rückgabe zu lange dauert. Deshalb brauchen wir zwei gut sichtbare Rückgabestellen und genügend Helfer. Auf den Plakaten sollte einfach erklärt werden, wie das Pfand funktioniert. Nach dem Fest vergleichen wir die Abfallmenge und fragen die Verkaufsstände nach ihren Erfahrungen. Dann entscheiden wir über das nächste Jahr.',
'Taklif, mumkin bo‘lgan e’tiroz va tekshirish usulini ayting.',
'Ko‘cha bayrami jamoasiga 70–90 so‘zli taklif yozing: muammo, ikkita chora va natijani tekshirish.',
'Liebes Organisationsteam, beim letzten Straßenfest waren die Mülleimer sehr schnell voll. Für dieses Jahr schlage ich wiederverwendbare Becher mit Pfand vor. Zusätzlich könnten gut beschriftete Behälter helfen, den übrigen Abfall zu trennen. Damit keine langen Schlangen entstehen, brauchen wir mehrere Rückgabestellen. Ich würde gern zwei Stunden bei der Rücknahme helfen. Nach dem Fest könnten wir die Abfallmenge notieren und mit dem letzten Jahr vergleichen. So sehen wir, ob unsere Ideen wirklich funktionieren. Was halten Sie davon? Viele Grüße, Bek Rustamov',
'Ikki chora, yordam taklifi va o‘lchash usulini yozing.')

add('Eine Nachricht verbreitet sich',
'Am Montag liest Jasur in einer Nachbarschaftsgruppe, dass die Stadtbibliothek angeblich nächsten Monat geschlossen wird. Unter dem Beitrag stehen viele ärgerliche Kommentare, aber kein Link zu einer Quelle. Jasur möchte die Nachricht zuerst weiterleiten. Dann besucht er die Internetseite der Bibliothek. Dort findet er eine aktuelle Mitteilung: Wegen neuer Regale bleibt nur der Kinderbereich drei Tage lang geschlossen. Die übrigen Räume sind normal geöffnet. Jasur stellt den Link in die Gruppe und erklärt ruhig den Unterschied. Die Person, die den ersten Beitrag geteilt hat, bedankt sich und korrigiert ihn. Für Jasur zeigt die Situation, wie leicht eine ungenaue Information Sorgen auslösen kann. Er nimmt sich vor, künftig auf Datum, Quelle und genauen Wortlaut zu achten, bevor er eine überraschende Nachricht weitergibt.',
'''Welcher Bereich wird tatsächlich geschlossen?|Nur der Kinderbereich|Aslida faqat bolalar bo‘limi yopiladi.
Wie lange dauert die tatsächliche Schließung?|Drei Tage|Haqiqiy yopilish muddati uch kun.
Wo findet Jasur die aktuelle Mitteilung?|Auf der Internetseite der Bibliothek|Jasur dolzarb e’lonni kutubxonaning o‘z sahifasidan topadi.''',
'Eine Meldung prüfen',
'Amina: Hast du gehört, dass unser Schwimmbad morgen kostenlos ist? Ben: Woher hast du das? Amina: Jemand hat mir ein Foto von einem Plakat geschickt. Ben: Steht ein Datum darauf? Amina: Moment, unten steht der zwölfte August. Das Jahr kann ich kaum lesen. Ben: Vielleicht ist das Plakat älter. Lass uns auf der Seite des Schwimmbads nachsehen. Amina: Dort steht, dass morgen der normale Preis gilt. Es gibt aber am Sonntag einen Tag der offenen Tür. Ben: Dann war die Nachricht nicht ganz erfunden, aber sie passt nicht zu morgen. Amina: Ich schreibe der Gruppe eine Korrektur und füge den aktuellen Link hinzu. Ben: Gute Idee. Formuliere es freundlich; wahrscheinlich hat die Person das alte Datum einfach übersehen. Amina: Ja, mir wäre das fast auch passiert.',
'''Was hat Amina als Quelle erhalten?|Ein Foto von einem Plakat|Amina manba sifatida plakat suratini olgan.
Welcher Preis gilt morgen laut aktueller Seite?|Der normale Preis|Dolzarb sahifaga ko‘ra ertaga odatdagi narx amal qiladi.
Wann findet der Tag der offenen Tür statt?|Am Sonntag|Ochiq eshiklar kuni yakshanbada bo‘ladi.''',
'Shubhali xabarni tekshirish jarayonini 1–2 daqiqada tushuntiring; misol va hurmatli tuzatish usuli bo‘lsin.',
'Wenn mich eine Nachricht überrascht, suche ich zuerst nach der ursprünglichen Quelle. Dabei prüfe ich das Datum und lese mehr als nur die Überschrift. Ein altes Veranstaltungsplakat kann zum Beispiel heute noch geteilt werden, obwohl der Termin vorbei ist. Wenn ich einen Fehler finde, möchte ich niemanden bloßstellen. Ich würde den aktuellen Link schicken und kurz erklären, welche Information sich unterscheidet. So kann die Gruppe die Korrektur selbst nachvollziehen.',
'Manba, sana va mazmunni tekshirishni aniq misolda ko‘rsating.',
'Guruhdagi noto‘g‘ri kutubxona xabarini 70–90 so‘z bilan xushmuomala tuzating; manba nomini ayting, URL o‘ylab topmang.',
'Hallo zusammen, ich habe wegen der angekündigten Schließung auf der Internetseite unserer Bibliothek nachgesehen. Nach der aktuellen Mitteilung bleibt nicht die ganze Bibliothek geschlossen. Nur der Kinderbereich ist wegen neuer Regale drei Tage lang nicht zugänglich. Die anderen Räume bleiben geöffnet. Vielleicht ist beim Weitergeben ein Teil der Information verloren gegangen. Bitte schaut vor eurem Besuch noch einmal in die Mitteilung der Bibliothek. Es wäre gut, auch den ursprünglichen Beitrag zu ergänzen, damit niemand unnötig auf seinen Besuch verzichtet. Viele Grüße, Jasur',
'Xatoni, to‘g‘ri ma’lumotni va tekshirilgan manbani ayting.')

add('Ein Podcast aus dem Viertel',
'Zwei Schülerinnen starten einen Podcast über Menschen aus ihrem Stadtteil. Statt bekannte Persönlichkeiten einzuladen, sprechen sie mit einer Busfahrerin, einem Bäcker und einer ehrenamtlichen Fußballtrainerin. Vor jedem Gespräch schicken sie ihre Fragen und erklären, wo die Aufnahme veröffentlicht werden soll. Die Gäste entscheiden selbst, welche persönlichen Informationen sie nennen möchten. Die erste Folge ist zu lang und enthält viele Nebengeräusche. Deshalb lernen die Schülerinnen, stärker auszuwählen und in einem ruhigeren Raum aufzunehmen. Ein Gast bittet später darum, eine private Bemerkung zu entfernen. Sie kommen diesem Wunsch nach. Für die zweite Staffel suchen sie nun Themenvorschläge aus der Nachbarschaft. Ihr Ziel ist nicht, möglichst viele Klicks zu bekommen, sondern unterschiedliche Erfahrungen hörbar zu machen und dabei sorgfältig mit den Aussagen ihrer Gäste umzugehen.',
'''Welche drei Personen werden als Gäste genannt?|Eine Busfahrerin, ein Bäcker und eine Fußballtrainerin|Mehmonlar: avtobus haydovchisi, novvoy va ko‘ngilli futbol murabbiyi.
Welche zwei Probleme hat die erste Folge?|Sie ist zu lang und enthält viele Nebengeräusche|Birinchi son juda uzun va unda fon shovqini ko‘p.
Was lassen die Schülerinnen auf Wunsch eines Gastes weg?|Eine private Bemerkung|Mehmon iltimosiga ko‘ra shaxsiy izoh olib tashlanadi.''',
'Ein Interview vorbereiten',
'Sami: Morgen interviewen wir Frau Winter über ihre Arbeit im Theater. Welche Frage soll zuerst kommen? Eda: Vielleicht, wie sie zu diesem Beruf gekommen ist. Das ist persönlicher als eine Liste ihrer Aufgaben. Sami: Gut. Ich möchte auch nach einer schwierigen Situation fragen. Eda: Dann sollten wir ihr erlauben, ein Thema auszulassen, wenn sie darüber nicht sprechen möchte. Sami: Klar. Wie lang soll das Gespräch werden? Eda: Wir planen zwanzig Minuten, veröffentlichen aber nur etwa zehn. Das müssen wir vorher erklären. Sami: Ich prüfe heute das Mikrofon. Eda: Und ich schicke ihr die Fragen. Nach dem Gespräch sollten wir die Namen und Zahlen noch einmal kontrollieren. Sami: Stimmt. Außerdem fragen wir, ob wir ein Foto für die Ankündigung benutzen dürfen. Ohne ihre Zustimmung nehmen wir nur eine Zeichnung.',
'''Über welchen Beruf sprechen sie mit Frau Winter?|Über ihre Arbeit im Theater|Suhbat Frau Winterning teatrdagi ishi haqida.
Wie lang soll die veröffentlichte Fassung ungefähr sein?|Zehn Minuten|E’lon qilinadigan qisqartirilgan versiya taxminan o‘n daqiqa.
Was verwenden sie ohne Zustimmung zu einem Foto?|Eine Zeichnung|Suratga rozilik bo‘lmasa, chizma ishlatishadi.''',
'Mahalla podkasti uchun suhbat rejalang: mehmon, mavzu, uch savol va nashrdan oldingi tekshiruv.',
'Ich würde unsere Busfahrerin einladen, weil sie viele Menschen im Viertel kennt. Zuerst frage ich, warum sie diesen Beruf gewählt hat. Danach interessieren mich schwierige Situationen und schöne Begegnungen. Vor der Aufnahme erkläre ich, wo das Gespräch veröffentlicht wird. Sie darf Fragen ablehnen. Für die fertige Folge prüfen wir Namen und Zahlen und entfernen unwichtige Wiederholungen. Ein Foto verwenden wir nur, wenn sie damit einverstanden ist.',
'Savollar, rozilik va faktlarni tekshirishni rejaga kiriting.',
'Podkast mehmoniga 70–90 so‘zli rasmiy taklif yozing: mavzu, vaqt, e’lon qilinadigan joy va tanlov huquqi.',
'Sehr geehrte Frau Winter, wir gestalten einen kleinen Podcast über Berufe in unserem Viertel und würden gern mit Ihnen über Ihre Arbeit im Theater sprechen. Das Gespräch würde ungefähr zwanzig Minuten dauern. Eine gekürzte Fassung möchten wir auf der Seite unseres Jugendzentrums veröffentlichen. Die Fragen schicken wir Ihnen vorher. Selbstverständlich können Sie einzelne Fragen auslassen. Hätten Sie nächste Woche Zeit und Interesse? Gern richten wir uns nach Ihrem Terminplan und besprechen vorab alle offenen Fragen. Mit freundlichen Grüßen, Sami und Eda',
'Maqsad, davomiylik, nashr joyi va savolni rad etish imkonini yozing.')

add('Erreichbar, aber nicht immer',
'In einer Lerngruppe werden täglich viele Nachrichten verschickt. Neben Hausaufgaben erscheinen Witze, Fotos und spontane Fragen. Einige Mitglieder freuen sich über den Austausch, andere fühlen sich unter Druck, sofort zu antworten. Besonders schwierig ist es für Menschen, die im Schichtdienst arbeiten. Bei einem Treffen spricht die Gruppe offen darüber. Sie beschließt, wichtige Informationen in einer einzigen Wochenübersicht zu sammeln. Dringende Änderungen sollen mit dem Wort Termin beginnen. Niemand muss am späten Abend reagieren. Wer länger nicht erreichbar ist, kann freiwillig kurz Bescheid sagen. Nach vier Wochen prüfen die Mitglieder, ob die Regeln helfen. Die Nachrichten werden nicht völlig verschwinden, und das ist auch nicht das Ziel. Die Gruppe möchte freundlich verbunden bleiben, ohne dass das Handy den ganzen Tag bestimmt.',
'''Wo werden wichtige Informationen künftig gesammelt?|In einer Wochenübersicht|Muhim ma’lumotlar bitta haftalik sharhda jamlanadi.
Mit welchem Wort sollen dringende Änderungen beginnen?|Termin|Shoshilinch o‘zgarish xabarlari „Termin“ so‘zi bilan boshlanadi.
Wann prüft die Gruppe die neuen Regeln?|Nach vier Wochen|To‘rt haftadan keyin qoidalar foydasini baholashadi.''',
'Grenzen freundlich erklären',
'Kollege: Ich habe dir gestern Abend geschrieben, aber du hast nicht geantwortet. Kollegin: Ja, ich habe die Nachricht erst heute Morgen gelesen. Nach acht lege ich mein Diensthandy weg. Kollege: Ich wollte nur wissen, wo die Unterlagen liegen. Kollegin: Das verstehe ich. Für solche Fälle könnten wir einen gemeinsamen Ordner besser beschriften. Dann musst du nicht auf meine Antwort warten. Kollege: Gute Idee. Manchmal denke ich, eine kurze Nachricht stört doch niemanden. Kollegin: Das Schreiben ist nicht unbedingt das Problem. Schwierig wird es, wenn eine sofortige Antwort erwartet wird. Kollege: Dann schreibe ich künftig dazu, wenn es bis morgen Zeit hat. Kollegin: Das hilft. Und für echte dringende Fälle sollten wir im Team einen klaren Kontaktweg vereinbaren, damit nicht alle ständig erreichbar sein müssen.',
'''Ab wann legt die Kollegin ihr Diensthandy weg?|Nach acht|U ish telefonini soat sakkizdan keyin chetga qo‘yadi.
Was wollte der Kollege wissen?|Wo die Unterlagen liegen|Hamkasb hujjatlarning qayerdaligini bilmoqchi bo‘lgan.
Welche praktische Verbesserung schlägt die Kollegin vor?|Den gemeinsamen Ordner besser beschriften|Umumiy papkadagi nomlarni aniqroq qilishni taklif etadi.''',
'Doim javob berish kutiladigan guruhda o‘z chegarangizni muloyim tushuntiring va umumiy qoida taklif qiling.',
'Ich lese unsere Gruppe gern, kann aber während der Arbeit nicht sofort antworten. Wenn eine Frage dringend ist, sollte das am Anfang stehen. Für normale Aufgaben würde ich eine Antwort bis zum nächsten Abend vorschlagen. Außerdem könnten wir wichtige Termine in einer Übersicht sammeln. So finden alle die Informationen leichter. Mir geht es nicht darum, weniger Kontakt zu haben, sondern unsere unterschiedlichen Tagesabläufe zu respektieren.',
'Shaxsiy ehtiyoj, boshqalarga hurmat va amaliy qoida bo‘lsin.',
'Kurs guruhiga xabar almashish qoidalari haqida 70–90 so‘zli taklif yozing; muvozanatli ohangni saqlang.',
'Hallo zusammen, ich freue mich über den Austausch in unserer Gruppe. Manchmal gehen wichtige Termine aber zwischen vielen Nachrichten verloren. Deshalb schlage ich eine kurze Wochenübersicht vor. Außerdem sollte niemand erwarten, dass wir spätabends sofort antworten. Für dringende Änderungen könnten wir ein einheitliches Stichwort benutzen. Das würde besonders denjenigen helfen, die zu unterschiedlichen Zeiten arbeiten. Lasst uns diese Regeln vier Wochen ausprobieren und danach gemeinsam besprechen, was gut funktioniert. Natürlich sollen persönliche Gespräche und freundliche Nachrichten weiterhin Platz haben. Viele Grüße, Amina',
'Muammo, ikkita qoida va sinov muddatini yozing.')

add('Eine Ausbildung oder sofort arbeiten?',
'Nach einem Praktikum bekommt Timur ein Angebot für eine feste Stelle in einem Lager. Gleichzeitig könnte er im Herbst eine Ausbildung beginnen. Die feste Stelle würde ihm sofort mehr Geld bringen. Eine Ausbildung dauert länger und bedeutet zunächst ein kleineres Einkommen, könnte aber neue berufliche Möglichkeiten eröffnen. Timur spricht mit seiner Familie und einer Berufsberaterin. Sie nimmt ihm die Entscheidung nicht ab, sondern hilft ihm, Fragen zu ordnen. Welche Arbeit interessiert ihn? Welche Kosten muss er jeden Monat bezahlen? Gibt es Unterstützung während der Ausbildung? Timur besucht außerdem einen Betrieb, in dem Auszubildende von ihrem Alltag erzählen. Erst danach entscheidet er sich für die Ausbildung. Er weiß, dass dieser Weg anstrengend wird, hat aber nun einen konkreten Plan für die ersten Monate.',
'''Welche Möglichkeit bringt Timur sofort mehr Geld?|Die feste Stelle im Lager|Ombordagi doimiy ish darhol ko‘proq daromad beradi.
Wer hilft ihm, seine Fragen zu ordnen?|Eine Berufsberaterin|Kasb maslahatchisi savollarini tartibga solishga yordam beradi.
Wofür entscheidet er sich am Ende?|Für die Ausbildung|Oxirida kasbiy ta’limni tanlaydi.''',
'Eine Entscheidung nicht zu schnell treffen',
'Lea: Ich habe eine Zusage für einen Kurs in einer anderen Stadt. Jetzt soll ich innerhalb von drei Tagen antworten. Murat: Freust du dich darüber? Lea: Ja, aber ich müsste umziehen. Ich kenne dort niemanden und weiß noch nicht, wie teuer ein Zimmer ist. Murat: Dann fehlen dir wichtige Informationen. Kannst du um etwas mehr Zeit bitten? Lea: Vielleicht. Ich habe Angst, dass der Platz dann weg ist. Murat: Du könntest heute anrufen und gleichzeitig nach Wohnmöglichkeiten fragen. Lea: Stimmt. Außerdem möchte ich mit jemandem sprechen, der den Kurs schon besucht. Murat: Gute Idee. Was wäre für dich entscheidend? Lea: Ob die Inhalte wirklich zu meinem Berufsziel passen und ob ich die Kosten tragen kann. Murat: Dann prüfe diese beiden Punkte zuerst, statt nur auf den Zeitdruck zu reagieren.',
'''Innerhalb welcher Frist soll Lea antworten?|Innerhalb von drei Tagen|Lea uch kun ichida javob berishi kerak.
Welche Wohninformation fehlt ihr?|Wie teuer ein Zimmer ist|U xonaning narxini hali bilmaydi.
Welche zwei Punkte sind für ihre Entscheidung entscheidend?|Passende Kursinhalte und tragbare Kosten|Kurs kasb maqsadiga mosligi va xarajatlarni ko‘tara olish muhim.''',
'Ikki ta’lim yoki ish imkoniyatini taqqoslang; daromad, qiziqish va kelajak bo‘yicha asoslangan tanlov qiling.',
'Eine feste Stelle wäre für mich attraktiv, weil ich sofort Geld verdienen könnte. Trotzdem würde ich auch die Ausbildung prüfen. Entscheidend ist, ob mich der Beruf langfristig interessiert und ob ich während der Ausbildung meine Ausgaben bezahlen kann. Ich würde mit Auszubildenden sprechen und einen Monatsplan für die Kosten erstellen. Erst danach möchte ich entscheiden. Ein höheres Einkommen heute ist wichtig, aber für mich nicht das einzige Kriterium.',
'Ikki variant, uchta mezon va ma’lumot yig‘ish qadamini ayting.',
'Kurs tashkilotchisiga qaror muddati va turar joy haqida 70–90 so‘zli rasmiy xat yozing.',
'Sehr geehrte Frau Kern, vielen Dank für die Zusage zu Ihrem Kurs. Ich freue mich sehr über den angebotenen Platz. Da ich dafür umziehen müsste, möchte ich vorher die Wohnkosten prüfen. Wäre es möglich, meine Antwortfrist um eine Woche zu verlängern? Außerdem wäre ich Ihnen dankbar, wenn Sie mir Hinweise zu günstigen Zimmern geben könnten. Gern würde ich auch kurz mit einer Person sprechen, die den Kurs bereits besucht hat. Vielen Dank für Ihre Unterstützung. Mit freundlichen Grüßen, Lea Sommer',
'Qiziqish, muddatni uzaytirish sababi va ikkita aniq so‘rov bo‘lsin.')

add('Ein Arbeitsweg mit Folgen',
'Mira erhält ein Stellenangebot von einer Firma außerhalb der Stadt. Die Aufgaben passen genau zu ihrer Erfahrung, und das Gehalt ist höher als bisher. Allerdings würde sie täglich fast zwei Stunden unterwegs sein. Ihr jetziger Arbeitsplatz ist mit dem Fahrrad erreichbar, bietet aber kaum Möglichkeiten, neue Aufgaben zu übernehmen. Mira möchte weder nur nach dem Geld entscheiden noch die neue Stelle sofort ablehnen. Im zweiten Gespräch fragt sie, ob sie nach der Einarbeitung an zwei Tagen von zu Hause arbeiten könnte. Die Firma ist bereit, ein solches Modell zunächst drei Monate zu testen. Mira spricht daraufhin mit ihrer Familie über die veränderten Zeiten. Sie nimmt das Angebot schließlich an, vereinbart aber ein Gespräch am Ende der Testphase. Dann sollen beide Seiten prüfen, ob die Lösung im Alltag funktioniert.',
'''Wie lang wäre Miras tägliche Fahrtzeit bei der neuen Stelle?|Fast zwei Stunden|Yangi ishga qatnash har kuni deyarli ikki soat oladi.
An wie vielen Tagen möchte sie zu Hause arbeiten?|An zwei Tagen|Haftada ikki kun uyda ishlashni xohlaydi.
Wie lange soll das Modell zunächst getestet werden?|Drei Monate|Model avval uch oy sinab ko‘riladi.''',
'Im Bewerbungsgespräch nachfragen',
'Arbeitgeber: Haben Sie noch Fragen zu der Stelle? Bewerber: Ja, mich interessiert, wie die Einarbeitung organisiert ist. Arbeitgeber: In den ersten vier Wochen begleitet Sie eine Kollegin. Danach übernehmen Sie schrittweise eigene Projekte. Bewerber: Das klingt gut. In der Anzeige stand auch flexible Arbeitszeit. Was bedeutet das konkret? Arbeitgeber: Zwischen neun und fünfzehn Uhr sollten Sie erreichbar sein. Die übrigen Stunden können Sie nach Absprache verteilen. Bewerber: Gibt es regelmäßige Wochenenddienste? Arbeitgeber: Normalerweise nicht. Bei größeren Veranstaltungen kommt das etwa viermal im Jahr vor. Diese Termine werden früh angekündigt. Bewerber: Danke. Mir ist wichtig, Arbeit und Familie zuverlässig planen zu können. Arbeitgeber: Das verstehen wir. Wenn Sie möchten, lernen Sie beim nächsten Termin das Team kennen und können weitere Fragen zum Arbeitsalltag stellen.',
'''Wie lange begleitet eine Kollegin den Bewerber zu Beginn?|Vier Wochen|Dastlab hamkasb to‘rt hafta yordam beradi.
Zwischen welchen Uhrzeiten soll er erreichbar sein?|Zwischen neun und fünfzehn Uhr|9:00 dan 15:00 gacha aloqada bo‘lish talab qilinadi.
Wie oft gibt es ungefähr Wochenenddienste?|Etwa viermal im Jahr|Dam olish kunidagi navbatchilik yiliga taxminan to‘rt marta.''',
'Ish suhbatida ishning sizga mosligini bilish uchun mazmunli savollar bering; oilaviy rejalashtirish ehtiyojini ayting.',
'Die Aufgaben interessieren mich sehr, besonders die Zusammenarbeit mit Kunden. Bevor ich entscheide, möchte ich den Arbeitsalltag besser verstehen. Wie läuft die Einarbeitung ab? Welche Zeiten sind fest, und wie früh werden besondere Dienste angekündigt? Ich kann gelegentlich am Wochenende arbeiten, brauche dafür aber eine verlässliche Planung. Außerdem würde ich gern wissen, welche Entwicklungsmöglichkeiten es nach dem ersten Jahr gibt.',
'Vazifalar, ish vaqti va rivojlanish imkoniyati haqida so‘rang.',
'Ish suhbatidan keyin 70–90 so‘zli rasmiy xat yozing: minnatdorchilik, qiziqish va qolgan bir savol.',
'Sehr geehrte Frau Neumann, vielen Dank für das freundliche Gespräch und die ausführlichen Informationen zur Stelle. Besonders die geplanten Projekte und die Zusammenarbeit im Team haben mein Interesse verstärkt. Eine Frage zur Einarbeitung ist noch offen: Wäre in den ersten Wochen ein fester Ansprechpartner für organisatorische Fragen vorgesehen? Das würde mir helfen, mich schnell in die Abläufe einzuarbeiten. Über die Möglichkeit, beim nächsten Termin das Team kennenzulernen, würde ich mich freuen. Ich danke Ihnen für Ihre Zeit. Mit freundlichen Grüßen, Mira Weber',
'Suhbatga aniq murojaat qiling va bitta asosli savol bering.')

add('Ein Fehler als Ausgangspunkt',
'Bei einer Präsentation im Sprachkurs verliert Bek plötzlich den Faden. Er sucht lange nach einem Wort und beendet seinen Vortrag früher als geplant. Zu Hause denkt er zunächst, dass alle anderen besser sprechen. Seine Lernpartnerin erinnert ihn jedoch daran, dass die Zuhörer seine Hauptidee verstanden und interessiert nachgefragt haben. Gemeinsam hören sie eine Aufnahme an, die Bek mit Zustimmung der Gruppe gemacht hat. Sie entdecken, dass er viele richtige Sätze bildet, aber kaum Pausen plant. Für den nächsten Vortrag schreibt Bek deshalb nur fünf Stichwörter auf und übt Übergänge zwischen den Teilen. Außerdem bereitet er einen Satz vor, mit dem er um einen Moment Bedenkzeit bitten kann. Beim nächsten Versuch spricht er nicht fehlerfrei, bleibt aber ruhiger und erklärt sein Beispiel bis zum Ende.',
'''Was haben die Zuhörer trotz Beks Unsicherheit verstanden?|Seine Hauptidee|Tinglovchilar Bekning asosiy fikrini tushungan.
Wie viele Stichwörter schreibt er für den nächsten Vortrag auf?|Fünf|Keyingi chiqish uchun beshta tayanch so‘z yozadi.
Was plant er beim ersten Vortrag zu wenig?|Pausen|Birinchi chiqishda tanaffuslar yetarlicha rejalashtirilmagan.''',
'Rückmeldung nach einer Präsentation',
'Lehrerin: Wie hast du dich während deiner Präsentation gefühlt, Amina? Amina: Am Anfang war ich nervös. Später ging es besser, aber ich habe bestimmt viele Fehler gemacht. Lehrerin: Einige Formen waren noch unsicher. Trotzdem war dein Aufbau klar, und dein Beispiel hat die Gruppe interessiert. Amina: Was sollte ich zuerst verbessern? Lehrerin: Du hast am Ende sehr schnell gesprochen. Übe, vor deinem Fazit eine kurze Pause zu machen. Amina: Soll ich den ganzen Text auswendig lernen? Lehrerin: Das würde ich nicht empfehlen. Arbeite lieber mit Stichwörtern, damit du auf Fragen reagieren kannst. Amina: Dann übe ich morgen mit meiner Partnerin. Lehrerin: Gute Idee. Bitte sie, dir eine unerwartete Frage zu stellen. So trainierst du auch, ruhig zu bleiben, wenn das Gespräch anders läuft als geplant.',
'''Was lobt die Lehrerin neben dem Beispiel?|Den klaren Aufbau|O‘qituvchi tuzilmaning ravshanligini maqtaydi.
Wann soll Amina eine kurze Pause machen?|Vor ihrem Fazit|Xulosadan oldin qisqa to‘xtash tavsiya qilinadi.
Was soll die Lernpartnerin beim Üben stellen?|Eine unerwartete Frage|Mashqda sherigi kutilmagan savol berishi kerak.''',
'Qiyin o‘quv tajribangiz va undan olgan saboq haqida 1–2 daqiqalik taqdimot qiling; oxirida savolga javob bering.',
'Als ich zum ersten Mal auf Deutsch präsentiert habe, wollte ich jeden Satz perfekt sagen. Dadurch habe ich oft den Faden verloren. Meine Partnerin hat mir gezeigt, dass die Hauptidee trotzdem verständlich war. Jetzt bereite ich Stichwörter vor und übe kurze Pausen. Das hilft mir mehr als ein auswendig gelernter Text. Wenn mir ein Wort fehlt, beschreibe ich es anders. Mein Ziel ist, verständlich weiterzusprechen und aus jeder Rückmeldung einen konkreten nächsten Schritt zu machen.',
'Muammo, qayta baholash va keyingi amaliy qadamni bog‘lang.',
'Omadsiz chiqishdan keyin do‘stingizni qo‘llab-quvvatlovchi 70–90 so‘zli xat yozing; ikki aniq maslahat bering.',
'Lieber Bek, ich verstehe, dass du nach der Präsentation enttäuscht bist. Trotzdem fand ich deine Hauptidee klar, und dein Beispiel war interessant. Du musst nicht alles auf einmal verbessern. Vielleicht übst du zuerst die Übergänge mit fünf Stichwörtern. Außerdem könntest du vor dem Schluss eine kurze Pause einplanen. Wenn du möchtest, höre ich dir am Donnerstag zu und stelle anschließend zwei Fragen. So üben wir eine echte Gesprächssituation. Ein schwieriger Versuch bedeutet nicht, dass du keine Fortschritte machst. Liebe Grüße, Amina',
'Aniq ijobiy kuzatuv, ikkita maslahat va yordam taklifini yozing.')

add('Eine Bibliothek verändert sich',
'Die Stadtbibliothek möchte mehr Platz zum gemeinsamen Lernen schaffen. Dafür sollen einige selten ausgeliehene Bücher ins Magazin gebracht werden. Eine Gruppe älterer Besucher befürchtet, dass dadurch der Charakter der Bibliothek verloren geht. Studierende begrüßen dagegen die Idee, weil sie zu Hause oft keinen ruhigen Arbeitsplatz haben. Die Leitung lädt beide Gruppen zu einem Gespräch ein. Dabei wird deutlich, dass Ruhe und Zusammenarbeit unterschiedliche Räume brauchen. Der neue Plan sieht deshalb einen stillen Lesebereich und zwei kleine Gruppenräume vor. Bücher aus dem Magazin können weiterhin bestellt werden. Zunächst wird nur ein Teil des Gebäudes verändert. Nach sechs Monaten sollen Besucher ihre Erfahrungen mitteilen. Die Leitung möchte die Nutzung beobachten, bevor sie weitere Regale entfernt. So bleibt die Entscheidung überprüfbar und kann bei Bedarf angepasst werden.',
'''Wohin kommen selten ausgeliehene Bücher?|Ins Magazin|Kam olinadigan kitoblar saqlash bo‘limiga o‘tkaziladi.
Wie viele Gruppenräume sieht der neue Plan vor?|Zwei|Yangi rejada ikkita guruh xonasi bor.
Nach welcher Zeit sollen Besucher Rückmeldung geben?|Nach sechs Monaten|Olti oydan keyin tashrif buyuruvchilar fikri olinadi.''',
'Was braucht unser Lernraum?',
'Moderatorin: Heute sammeln wir Wünsche für den neuen Lernraum. Samira: Ich brauche vor allem einen ruhigen Platz mit Steckdose. Zu Hause teilen sich meine Geschwister und ich ein Zimmer. Leon: Für unsere Lerngruppe wären große Tische wichtig. Wir müssen dabei aber miteinander sprechen dürfen. Samira: Genau das könnte mich beim Lesen stören. Moderatorin: Wie könnten wir beide Bedürfnisse berücksichtigen? Leon: Vielleicht teilen wir den Raum mit einer beweglichen Wand. Samira: Wenn sie Geräusche ausreichend dämpft, wäre das eine Möglichkeit. Sonst brauchen wir verschiedene Zeiten. Moderatorin: Wir können beides testen. Am Vormittag bleibt es still, am Nachmittag erlauben wir Gruppengespräche hinter der Trennwand. Leon: Dann sollte der Zeitplan am Eingang stehen. Samira: Und nach einem Monat fragen wir die Nutzer, ob sie sich konzentrieren konnten. Moderatorin: Das halten wir so fest.',
'''Warum braucht Samira einen Lernplatz außerhalb ihrer Wohnung?|Sie teilt zu Hause ein Zimmer mit ihren Geschwistern|Uyda opa-uka yoki aka-singillari bilan bir xonani bo‘lishadi.
Wann soll es im Raum still bleiben?|Am Vormittag|Ertalabki vaqtda xona sokin bo‘lishi kerak.
Wo soll der Zeitplan stehen?|Am Eingang|Jadval kirish joyida ko‘rsatiladi.''',
'Kutubxonaning jim o‘qish va guruhda ishlash ehtiyojlari bo‘yicha murosa taklif qiling.',
'Ich verstehe beide Seiten. Wer allein liest, braucht Ruhe. Eine Lerngruppe muss dagegen miteinander sprechen können. Deshalb würde ich nicht überall dieselben Regeln einführen. Wenn möglich, richten wir getrennte Bereiche ein. Falls nur ein Raum vorhanden ist, könnten feste Zeiten helfen. Wichtig ist, die Regeln am Eingang verständlich zu zeigen. Nach einem Monat sollten wir nachfragen, ob die Lösung funktioniert, statt sofort den ganzen Raum dauerhaft umzubauen.',
'Ikki ehtiyojni tan oling va tekshiriladigan murosa ayting.',
'Kutubxona rahbariyatiga 70–90 so‘zli fikr yozing; o‘qish joylari va kitoblarga kirishni birga hisobga oling.',
'Sehr geehrte Bibliotheksleitung, ich begrüße Ihren Plan, zusätzliche Lernplätze einzurichten. Viele Kursteilnehmer haben zu Hause keinen ruhigen Arbeitsplatz. Gleichzeitig sollten Bücher weiterhin leicht zugänglich bleiben. Deshalb finde ich einen kleinen Probelauf mit getrennten Bereichen sinnvoll. Bitte erklären Sie deutlich, wie Bücher aus dem Magazin bestellt werden können. Nach einigen Monaten könnten Besucher einen kurzen Fragebogen ausfüllen. Auf diese Weise würden nicht nur die lautesten Stimmen gehört. Ich würde gern an einem Gespräch über die Gestaltung teilnehmen. Mit freundlichen Grüßen, Samira Karimova',
'Qo‘llab-quvvatlash, ehtiyot sharti va baholash usulini yozing.')

add('Ein Ehrenamt mit klaren Grenzen',
'Nach ihrem Umzug möchte Dilnoza neue Menschen kennenlernen und etwas für ihr Viertel tun. Sie meldet sich bei einer Initiative, die ältere Menschen beim Einkaufen unterstützt. Zunächst bietet sie jeden freien Nachmittag an. Schon nach zwei Wochen merkt sie jedoch, dass Arbeit, Deutschkurs und Ehrenamt zusammen zu viel werden. Statt einfach nicht mehr zu kommen, spricht sie mit der Koordinatorin. Gemeinsam vereinbaren sie einen festen Termin am Samstag und eine Vertretung für Urlaubszeiten. Dilnoza begleitet nun regelmäßig dieselbe Nachbarin. Dadurch entsteht Vertrauen, und beide können besser planen. Die Initiative fragt neue Freiwillige inzwischen genauer nach ihren Möglichkeiten. Hilfsbereitschaft soll nicht dazu führen, dass jemand sich dauerhaft überfordert. Dilnoza bleibt gern dabei, gerade weil ihre Aufgabe jetzt überschaubar ist und sie ohne schlechtes Gewissen auch Nein sagen kann.',
'''Wobei hilft die Initiative älteren Menschen?|Beim Einkaufen|Tashabbus keksa odamlarga xarid qilishda yordam beradi.
Welchen festen Termin vereinbart Dilnoza?|Am Samstag|Dilnoza shanba kuni doimiy yordam berishga kelishadi.
Mit wem bespricht sie ihre Überlastung?|Mit der Koordinatorin|Ortiqcha yuklamani muvofiqlashtiruvchi bilan muhokama qiladi.''',
'Freiwillige für ein Lesecafé',
'Koordinator: Danke, dass Sie sich für unser Lesecafé interessieren. Welche Aufgaben würden Sie gern übernehmen? Bewerberin: Ich könnte mit Kindern lesen. Ich habe aber noch keine Erfahrung mit großen Gruppen. Koordinator: Sie wären nicht allein. Am Anfang arbeiten Sie mit einer erfahrenen Freiwilligen zusammen. Bewerberin: Das beruhigt mich. Wie viel Zeit sollte ich einplanen? Koordinator: Ein Nachmittag alle zwei Wochen wäre ideal. Dazu kommt eine kurze Besprechung im Monat. Bewerberin: Das passt besser als jede Woche. Was mache ich, wenn ich krank bin? Koordinator: Bitte melden Sie sich möglichst früh bei mir. Wir organisieren dann eine Vertretung. Bewerberin: Kann ich erst einmal zuschauen? Koordinator: Natürlich. Kommen Sie nächsten Dienstag. Danach entscheiden Sie in Ruhe, ob Sie regelmäßig mitmachen möchten. Uns ist eine verlässliche kleine Zusage lieber als ein zu großes Versprechen.',
'''Mit wem arbeitet die Bewerberin am Anfang zusammen?|Mit einer erfahrenen Freiwilligen|Avval tajribali ko‘ngilli bilan birga ishlaydi.
Wie oft soll sie idealerweise einen Nachmittag helfen?|Alle zwei Wochen|Ideal holda ikki haftada bir tushdan keyin yordam beradi.
Wann darf sie zunächst zuschauen?|Nächsten Dienstag|Kelasi seshanba avval kuzatib ko‘rishi mumkin.''',
'Ko‘ngillilik rolini tanlash bo‘yicha suhbat qiling: ko‘nikmangiz, vaqtingiz, yordam va sinab ko‘rish.',
'Ich würde gern im Lesecafé helfen, weil ich Freude an Büchern habe. Mit großen Kindergruppen habe ich allerdings wenig Erfahrung. Deshalb möchte ich zunächst einer erfahrenen Person zuschauen. Zeit hätte ich jeden zweiten Dienstag. Eine wöchentliche Aufgabe könnte ich im Moment nicht zuverlässig übernehmen. Wenn dieser Umfang für Sie passt, würde ich gern einen Probetermin vereinbaren und danach gemeinsam besprechen, welche Aufgabe am besten zu mir passt.',
'Qila oladigan ish va vaqt chegarasini halol ayting.',
'Ko‘ngillilar muvofiqlashtiruvchisiga 70–90 so‘zli ishtirok so‘rovi yozing; imkoniyat va cheklovingizni kiriting.',
'Sehr geehrter Herr Wolf, ich habe von Ihrem Lesecafé gehört und möchte mich gern freiwillig engagieren. Ich lese gern und habe früher meiner kleinen Schwester bei den Hausaufgaben geholfen. Eine große Kindergruppe habe ich jedoch noch nicht betreut. Deshalb würde ich zunächst gern bei einem Termin zuschauen. Zeit habe ich jeden zweiten Dienstagnachmittag. Wäre das für Ihre Planung ausreichend? Über Informationen zu den Aufgaben und zur Begleitung neuer Freiwilliger würde ich mich freuen. Vielen Dank für Ihre Rückmeldung. Mit freundlichen Grüßen, Dilnoza Saidova',
'Tajriba, mavjud vaqt va boshlash uchun aniq so‘rov bo‘lsin.')

add('Ein Tauschregal verbindet Nachbarn',
'Im Eingangsbereich eines Nachbarschaftshauses steht seit Kurzem ein Tauschregal. Dort können Menschen gut erhaltene Bücher, Spiele und kleine Haushaltsgegenstände abgeben oder mitnehmen. Geld spielt keine Rolle, und niemand muss zuerst etwas bringen, um etwas nehmen zu dürfen. Anfangs werden jedoch auch kaputte Geräte und große Säcke mit unsortierten Dingen abgestellt. Das Team merkt, dass eine freundliche Idee klare Regeln braucht. Es hängt Bilder geeigneter Gegenstände auf und bietet feste Annahmezeiten an. Eine Woche lang erklären Freiwillige den Besuchern persönlich, wie das Regal funktioniert. Danach wird es übersichtlicher. Besonders beliebt sind Kinderbücher, weil sie oft nur für eine bestimmte Altersphase gebraucht werden. Das Team plant nun eine kleine Ecke, in der Menschen erzählen können, welche Geschichte hinter einem Gegenstand steckt, ohne ihre privaten Daten öffentlich zu hinterlassen.',
'''Muss man zuerst etwas abgeben, um etwas mitnehmen zu dürfen?|Nein|Biror narsa olishdan oldin albatta narsa topshirish shart emas.
Welche Gegenstände sind besonders beliebt?|Kinderbücher|Bolalar kitoblari ayniqsa mashhur.
Welche Zeiten führt das Team ein?|Feste Annahmezeiten|Buyumlarni qabul qilish uchun aniq vaqtlar belgilanadi.''',
'Ein Nachbarschaftsprojekt organisieren',
'Sprecher: Unser Tauschregal braucht nächste Woche Betreuung. Wer kann am Montag die neuen Sachen prüfen? Leyla: Ich kann von vier bis fünf kommen. Aber ich möchte nicht allein entscheiden, was wir ablehnen. Sprecher: Verständlich. Wir machen eine kurze Liste: sauber, vollständig und ungefähr so groß, dass es in ein Fach passt. Karim: Was passiert mit Dingen, die niemand mitnimmt? Sprecher: Nach vier Wochen prüfen wir sie gemeinsam und suchen gegebenenfalls eine andere Abgabestelle. Leyla: Wie erkennen wir, wie lange etwas schon da ist? Karim: Wir könnten kleine Zettel mit dem Abgabedatum benutzen, ohne Namen. Sprecher: Gute Idee. Außerdem brauchen wir eine Erklärung für Menschen, die wenig Deutsch lesen. Leyla: Dann ergänzen wir Bilder. Ich kann welche zeichnen und sie am Montag mitbringen. Karim: Ich übersetze die wichtigsten drei Sätze ins Usbekische.',
'''Wann kann Leyla am Montag helfen?|Von vier bis fünf|Leyla dushanba soat to‘rtdan beshgacha yordam bera oladi.
Nach welcher Zeit werden liegen gebliebene Dinge geprüft?|Nach vier Wochen|Olinmagan narsalar to‘rt haftadan keyin ko‘rib chiqiladi.
Welche Information soll auf kleinen Zetteln stehen?|Das Abgabedatum|Kichik yorliqda topshirilgan sana yoziladi, ism emas.''',
'Qo‘shnilar almashish javonini birga rejalang: qoidalar, navbatchilik va hamma tushunadigan belgilash.',
'A: Unser Regal sollte auch für Menschen mit wenig Deutsch verständlich sein. B: Dann brauchen wir Bilder und kurze Sätze. Welche Dinge nehmen wir an? A: Nur saubere und vollständige Sachen, die in ein Fach passen. B: Ich kann montags helfen. Wer entscheidet bei Zweifeln? A: Das machen wir zu zweit. Außerdem schreiben wir das Abgabedatum auf einen Zettel. B: Gut, nach vier Wochen prüfen wir, was noch da ist.',
'Qabul mezonlari, vazifalar va tushunarli axborotni kelishing.',
'Yangi almashish javoni haqida 70–90 so‘zli e’lon yozing: qanday ishlashi, qoidalari va yordam imkoniyati.',
'Liebe Nachbarinnen und Nachbarn, im Nachbarschaftshaus gibt es jetzt ein Tauschregal. Sie können dort Bücher, Spiele und kleine Haushaltsgegenstände kostenlos mitnehmen. Es ist nicht nötig, vorher selbst etwas abzugeben. Wenn Sie etwas bringen möchten, achten Sie bitte darauf, dass es sauber, vollständig und nicht größer als ein Regalfach ist. Neue Dinge nehmen wir montags von vier bis fünf an. Wir suchen außerdem Freiwillige, die beim Sortieren helfen. Fragen beantworten wir gern vor Ort. Machen Sie mit und geben Sie Dingen ein zweites Zuhause!',
'Almashish sharti, qabul vaqti va buyum mezonlarini yozing.')

add('Sicher mit dem Fahrrad zur Schule',
'Vor einer Schule gibt es morgens häufig Gedränge. Autos halten kurz vor dem Eingang, während Kinder mit Fahrrädern zwischen ihnen hindurchfahren. Eine Elterninitiative schlägt deshalb vor, eine entfernte Haltezone einzurichten und den letzten Abschnitt gemeinsam zu Fuß zu gehen. Einige Eltern finden den zusätzlichen Weg unpraktisch, besonders bei Regen. Die Initiative lädt sie zu einem Rundgang ein. Dabei zeigt sich, dass eine nahe Kreuzung schlecht einsehbar ist und eine sichere Querung fehlt. Die Gruppe sammelt ihre Beobachtungen und bittet die Stadt um eine Prüfung. Sie behauptet nicht, das ganze Verkehrsproblem allein lösen zu können. Parallel organisiert sie an zwei Tagen eine begleitete Fahrradgruppe. Nach einem Monat werden Teilnahme und Schwierigkeiten dokumentiert. So entsteht aus einer allgemeinen Beschwerde ein konkreter Vorschlag, über den Schule, Eltern und Verwaltung gemeinsam sprechen können.',
'''Wo soll die neue Haltezone liegen?|Weiter vom Schuleingang entfernt|Yangi tushirish hududi maktab kirishidan uzoqroqda bo‘lishi kerak.
Welches Problem zeigt sich an der Kreuzung?|Sie ist schlecht einsehbar und eine sichere Querung fehlt|Chorrahada ko‘rish cheklangan va xavfsiz kesib o‘tish joyi yo‘q.
An wie vielen Tagen wird eine Fahrradgruppe organisiert?|An zwei Tagen|Velosiped guruhi ikki kunga tashkil qilinadi.''',
'Über den Schulweg sprechen',
'Moderatorin: Wir suchen eine Lösung für den morgendlichen Verkehr. Vater: Ich bringe meinen Sohn mit dem Auto, weil ich danach direkt zur Arbeit fahre. Ein Umweg kostet mich Zeit. Mutter: Das verstehe ich. Aber direkt vor dem Tor ist es für die Kinder unübersichtlich. Könnten Sie an der Sporthalle halten? Vater: Von dort müsste mein Sohn noch fünf Minuten laufen. Mutter: Wir könnten dort eine Begleitung organisieren, zumindest für die jüngeren Kinder. Moderatorin: Bevor wir das festlegen, müssen wir prüfen, ob der Weg geeignet ist. Vater: Wenn die Strecke sicher ist und jemand mitgeht, würde ich es ausprobieren. Mutter: Dann machen wir nächste Woche gemeinsam einen Rundgang. Moderatorin: Gut. Wir laden auch die Schule ein und notieren offene Fragen, statt heute schon eine endgültige Lösung zu versprechen.',
'''Warum nutzt der Vater morgens das Auto?|Er fährt danach direkt zur Arbeit|Ota keyin to‘g‘ri ishga boradi.
Wo soll er alternativ halten?|An der Sporthalle|Muqobil to‘xtash joyi sport zali yonida.
Was vereinbaren die Beteiligten für nächste Woche?|Einen gemeinsamen Rundgang|Keyingi hafta yo‘lni birgalikda ko‘zdan kechirishga kelishishadi.''',
'Maktabga borishdagi muammo haqida muhokama qiling: ota-onaning va bolaning ehtiyojini aytib, sinov yechimi taklif qiling.',
'Eltern brauchen morgens eine Lösung, die in ihren Arbeitsweg passt. Gleichzeitig müssen Kinder den Eingang sicher erreichen können. Ich würde deshalb eine Haltezone an der Sporthalle prüfen. Von dort könnte eine kleine Gruppe begleitet zur Schule gehen. Bevor wir das testen, sollten Eltern und Schule den Weg gemeinsam ansehen. Nach vier Wochen fragen wir, ob weniger Gedränge entsteht und welche Probleme bleiben. So berücksichtigen wir Sicherheit und Alltag, ohne sofort eine perfekte Lösung zu behaupten.',
'Ikki tomon ehtiyoji, oldindan tekshirish va sinov muddatini ayting.',
'Shahar idorasiga maktab yo‘li bo‘yicha 70–90 so‘zli murojaat yozing; kuzatuvni taxmindan ajrating.',
'Sehr geehrte Damen und Herren, vor unserer Schule halten morgens viele Autos direkt am Eingang. Dabei haben wir mehrfach beobachtet, dass Kinder zwischen parkenden Fahrzeugen hindurchgehen müssen. Besonders unübersichtlich ist die Kreuzung an der Sporthalle. Wir bitten Sie, die Situation vor Ort zu prüfen. Unsere Elterninitiative würde gern an einem gemeinsamen Rundgang teilnehmen und ihre Beobachtungen erläutern. Eine weiter entfernte Haltezone könnte eine Möglichkeit sein, müsste aber fachlich geprüft werden. Über einen Gesprächstermin mit Schule und Eltern würden wir uns freuen. Mit freundlichen Grüßen, Leyla Karimova',
'Aniq kuzatuv, joy va tekshirish so‘rovini kiriting.')

add('Tourismus und Alltag im Viertel',
'Ein historisches Viertel zieht immer mehr Besucher an. Cafés und kleine Geschäfte profitieren davon, doch Bewohner beklagen Lärm und volle Gehwege. Besonders am Wochenende stehen Reisegruppen lange vor Hauseingängen. Eine Ladenbesitzerin schlägt vor, gemeinsam mit Stadtführern Regeln für die Gruppen zu entwickeln. Die Führungen sollen an breiteren Plätzen halten und am Abend auf Lautsprecher verzichten. Gleichzeitig wünschen sich die Bewohner Informationen darüber, wie sie Probleme melden können. Bei einer Gesprächsrunde wird deutlich, dass nicht alle Touristen gleich handeln und auch nicht alle Anwohner dieselben Interessen haben. Einige vermieten Zimmer oder arbeiten selbst im Tourismus. Deshalb sucht die Gruppe keine einfache Einteilung in Gewinner und Verlierer. Sie will zunächst zwei besonders belastete Straßen beobachten und die vorgeschlagenen Regeln dort während der Sommermonate ausprobieren.',
'''Wo sollen Stadtführungen künftig halten?|An breiteren Plätzen|Ekskursiya guruhlari kengroq maydonlarda to‘xtashi kerak.
Worauf sollen Führungen am Abend verzichten?|Auf Lautsprecher|Kechqurun ovoz kuchaytirgich ishlatilmasligi taklif qilinadi.
Wie viele besonders belastete Straßen werden zunächst beobachtet?|Zwei|Avval yuklama yuqori bo‘lgan ikkita ko‘cha kuzatiladi.''',
'Eine Reise rücksichtsvoll planen',
'Nora: Für unseren Wochenendausflug habe ich ein Zimmer mitten in der Altstadt gefunden. Es ist günstig, aber die Bewertungen erwähnen viel Lärm. Sami: Dann sollten wir überlegen, was uns wichtiger ist: kurze Wege oder Ruhe. Nora: Vielleicht nehmen wir eine Unterkunft am Rand und fahren mit dem Bus hinein. Sami: Das wäre für mich in Ordnung. Außerdem möchte ich nicht nur die bekannten Fotoplätze sehen. Nora: Wir könnten eine Führung in einer kleinen Gruppe buchen. Sami: Ja, und vorher prüfen, ob sie Rücksicht auf die Bewohner nimmt. Nora: Was meinst du genau? Sami: Zum Beispiel nicht vor privaten Türen stehen bleiben und keine Menschen ohne zu fragen fotografieren. Nora: Gute Punkte. Ich suche nach einer Führung, die auch über den Alltag im Viertel erzählt, nicht nur über berühmte Gebäude.',
'''Welches Problem nennen die Bewertungen der Unterkunft?|Viel Lärm|Turar joy sharhlarida shovqin ko‘pligi aytiladi.
Wo könnte die Gruppe stattdessen übernachten?|Am Rand der Altstadt|Muqobil turar joy eski shahar chetida bo‘lishi mumkin.
Was soll die Führung außer berühmten Gebäuden zeigen?|Den Alltag im Viertel|Ekskursiya mashhur binolardan tashqari mahalla hayotini tushuntirsin.''',
'Sayyohlikning mahalla hayotiga foyda va qiyinchiliklarini ayting; ikki amaliy qoida taklif qiling.',
'Tourismus kann Arbeitsplätze schaffen und kleine Geschäfte unterstützen. Gleichzeitig brauchen Bewohner Ruhe und freie Eingänge. Deshalb halte ich kleine Gruppen für sinnvoller als sehr große Führungen. Sie sollten an geeigneten Plätzen stehen bleiben und am Abend keine Lautsprecher benutzen. Auch Besucher können Rücksicht nehmen, zum Beispiel vor Fotos um Erlaubnis fragen. Wichtig ist ein Gespräch mit verschiedenen Bewohnern, denn manche arbeiten selbst im Tourismus und haben andere Bedürfnisse als ihre Nachbarn.',
'Bir foyda, bir qiyinchilik va ikkita qoida bilan muvozanatli fikr bildiring.',
'Mahalla forumiga sayyohlik qoidalari bo‘yicha 70–90 so‘zli fikr yozing.',
'Ich freue mich, dass Besucher unser Viertel interessant finden. Die Cafés und Geschäfte profitieren davon. Trotzdem sind blockierte Hauseingänge und laute Führungen für Bewohner belastend. Ich schlage vor, feste Haltepunkte für Gruppen zu vereinbaren und abends auf Lautsprecher zu verzichten. Ein Kontakt für Beschwerden wäre ebenfalls hilfreich. Wir sollten diese Regeln gemeinsam mit Stadtführern und Bewohnern entwickeln und zunächst im Sommer testen. Ein vollständiger Ausschluss von Besuchern wäre für mich keine gute Lösung, weil das Viertel von Begegnungen lebt. Viele Grüße, Nora',
'Ikki qarashni hisobga olib, aniq sinov taklifini yozing.')

add('Eine Stadt auch bei Hitze nutzen',
'Während warmer Sommertage meiden viele Menschen den zentralen Platz einer Kleinstadt. Dort gibt es wenig Schatten, obwohl sich mehrere Bushaltestellen und Geschäfte befinden. Der Seniorenbeirat und eine Jugendgruppe sammeln gemeinsam Vorschläge. Ältere Teilnehmer wünschen sich Bänke im Schatten, Jugendliche einen frei zugänglichen Trinkwasserpunkt. Die Stadt erklärt, dass neue Bäume Zeit zum Wachsen brauchen und Leitungen im Boden berücksichtigt werden müssen. Deshalb diskutiert die Gruppe auch kurzfristige Möglichkeiten, etwa mobile Schattendächer für den Sommer. Eine Geschäftsfrau bietet an, ihren kühlen Innenhof während der Öffnungszeiten zugänglich zu machen. Die Gruppe veröffentlicht anschließend eine Karte vorhandener Schattenplätze, ohne daraus eine medizinische Empfehlung zu machen. Langfristig soll der Platz umgestaltet werden. Dafür werden zuerst die Wege verschiedener Nutzer beobachtet, damit neue Sitzplätze weder Buszugänge noch Durchgänge versperren.',
'''Was wünschen sich ältere Teilnehmer?|Bänke im Schatten|Keksa ishtirokchilar soyadagi o‘rindiqlarni xohlashadi.
Welche kurzfristige Schattenlösung wird genannt?|Mobile Schattendächer|Qisqa muddatli chora sifatida ko‘chma soyabon inshootlari aytiladi.
Was bietet eine Geschäftsfrau an?|Zugang zu ihrem kühlen Innenhof|Tadbirkor ayol salqin ichki hovlisiga kirishga ruxsat berishni taklif qiladi.''',
'Ein Treffen an einem anderen Ort',
'Organisatorin: Unser Nachbarschaftstreffen ist für Samstag auf dem Marktplatz geplant. Dort gibt es am Nachmittag kaum Schatten. Karim: Dann wäre ein anderer Ort besser. Im Park stehen viele Bäume. Organisatorin: Stimmt, aber der Weg ist für einige Gäste weit. Außerdem gibt es dort keine Toiletten. Leyla: Was ist mit dem Innenhof des Kulturhauses? Der ist von der Haltestelle aus gut erreichbar. Karim: Wir müssten fragen, ob wir ihn nutzen dürfen. Organisatorin: Ich rufe heute dort an. Wenn der Hof frei ist, ändern wir den Treffpunkt. Leyla: Dann müssen wir auch Menschen erreichen, die unsere Onlinegruppe nicht lesen. Karim: Ich hänge einen Hinweis am alten Treffpunkt aus und rufe Frau Winter an. Organisatorin: Gut. Die Anfangszeit bleibt gleich, damit die Änderung möglichst einfach zu verstehen ist.',
'''Warum ist der Park nicht für alle geeignet?|Der Weg ist weit und es gibt keine Toiletten|Park uzoqroq va unda hojatxona yo‘q.
Wer fragt beim Kulturhaus nach?|Die Organisatorin|Madaniyat uyiga tashkilotchi qo‘ng‘iroq qiladi.
Welche Angabe bleibt bei der Änderung gleich?|Die Anfangszeit|Uchrashuvning boshlanish vaqti o‘zgarmaydi.''',
'Tashqi tadbir joyini qulaylik, soya va yetib borish asosida tanlang; internetdan foydalanmaydigan mehmonlarni ham hisobga oling.',
'A: Der Marktplatz ist gut erreichbar, hat aber wenig Schatten. B: Im Park wäre es angenehmer, doch einige Gäste können nicht weit laufen. A: Dann fragen wir nach dem Innenhof des Kulturhauses. Dort gibt es auch Toiletten. B: Ich prüfe, ob der Eingang ohne Stufen erreichbar ist. A: Sobald wir eine Zusage haben, informieren wir alle. B: Zusätzlich hängen wir einen Hinweis am alten Treffpunkt aus und rufen die Gäste ohne Onlinezugang an.',
'Joy mezonlari, ruxsat va hammani xabardor qilishni kelishing.',
'Uchrashuv joyi o‘zgarganini 70–90 so‘zli e’londa tushuntiring; eski-yangi joy va o‘zgarmagan vaqtni aniq ayting.',
'Liebe Nachbarinnen und Nachbarn, unser Treffen am Samstag findet nicht auf dem Marktplatz, sondern im Innenhof des Kulturhauses statt. Auf dem Marktplatz gibt es am Nachmittag kaum Schatten. Der neue Ort liegt direkt neben der Haltestelle und verfügt über Sitzplätze und Toiletten. Wir beginnen wie geplant um fünfzehn Uhr. Bitte informieren Sie auch Bekannte, die unsere Onlinegruppe nicht nutzen. Am bisherigen Treffpunkt hängen wir einen Hinweis aus. Wer Unterstützung beim Finden des Eingangs braucht, kann sich vorher bei uns melden. Ihr Organisationsteam',
'Yangi joy, sabab, saqlangan vaqt va xabar yetkazishni yozing.')

add('Soll der Schultag später beginnen?',
'In einer Schülerzeitung wird diskutiert, ob der Unterricht morgens eine halbe Stunde später beginnen sollte. Einige Jugendliche berichten, dass sie in der ersten Stunde kaum aufmerksam sind. Lehrkräfte weisen dagegen darauf hin, dass ein späterer Beginn auch ein späteres Ende bedeutet. Das könnte Busverbindungen, Sportvereine und die Betreuung jüngerer Geschwister beeinflussen. Die Schulleitung möchte deshalb nicht allein nach einer schnellen Abstimmung entscheiden. Zunächst sollen Schülerinnen, Eltern und Beschäftigte zwei Wochen lang ihre tatsächlichen Wege und Zeiten notieren. Anschließend wird geprüft, für welche Gruppen eine Änderung hilfreich oder schwierig wäre. Ein Schüler schlägt außerdem vor, zuerst einzelne Tage zu testen. Der Artikel kommt zu keinem endgültigen Ergebnis. Er zeigt vielmehr, dass eine scheinbar einfache Zeitänderung viele Folgen haben kann und gute Entscheidungen verlässliche Informationen über den Alltag der Beteiligten brauchen.',
'''Um wie viel später soll der Unterricht beginnen?|Um eine halbe Stunde|Darsni yarim soat kechroq boshlash taklif etilgan.
Wie lange sollen die Beteiligten Wege und Zeiten notieren?|Zwei Wochen|Yo‘l va vaqt ma’lumotlari ikki hafta yoziladi.
Welchen begrenzten Versuch schlägt ein Schüler vor?|Zuerst einzelne Tage testen|Avval ayrim kunlarda sinab ko‘rishni taklif qiladi.''',
'Eine Meinung mit Gegenargument',
'Moderator: Sollte unsere Schule später anfangen? Amina: Ich wäre dafür. Mein Bus kommt sehr früh, und in der ersten Stunde bin ich oft noch müde. Ben: Bei mir wäre das schwierig. Nachmittags hole ich meinen kleinen Bruder ab. Wenn der Unterricht später endet, passt das nicht mehr. Amina: Daran hatte ich nicht gedacht. Könnte die Schule nur an zwei Tagen später beginnen? Ben: Vielleicht, aber dann müssten wir jede Woche unterschiedliche Zeiten beachten. Moderator: Welche Informationen fehlen uns noch? Amina: Wir wissen nicht, wie viele Schüler wirklich betroffen sind. Ben: Und wir kennen die Möglichkeiten der Busunternehmen nicht. Moderator: Dann wäre eine Befragung sinnvoll, bevor wir eine Empfehlung schreiben. Amina: Ja. Ich bleibe für einen späteren Beginn, möchte aber eine Lösung, die nicht einfach neue Probleme für andere schafft.',
'''Warum findet Ben ein späteres Unterrichtsende schwierig?|Er holt nachmittags seinen kleinen Bruder ab|Ben tushdan keyin kichik ukasini olib ketishi kerak.
Welche Änderung schlägt Amina als Kompromiss vor?|Nur an zwei Tagen später beginnen|Faqat ikki kunda kechroq boshlashni taklif qiladi.
Was soll vor einer Empfehlung stattfinden?|Eine Befragung|Tavsiya yozishdan avval so‘rov o‘tkazish kerak.''',
'Darsni kechroq boshlash haqida pozitsiya bildiring; qarshi dalilni tan olib, qanday ma’lumot yetishmasligini ayting.',
'Ich könnte mir einen späteren Unterrichtsbeginn vorstellen, weil ich morgens oft sehr früh unterwegs bin. Allerdings verstehe ich, dass ein späteres Ende für Familien schwierig sein kann. Wer Geschwister abholt oder einen festen Bus braucht, hätte vielleicht neue Probleme. Deshalb würde ich zuerst nach den tatsächlichen Tagesabläufen fragen. Danach könnte die Schule einen begrenzten Versuch planen. Meine Meinung hängt also nicht nur von meinem eigenen Wunsch ab, sondern auch davon, ob eine faire Lösung möglich ist.',
'Pozitsiya, qarshi dalil va qaror uchun zarur ma’lumotni ayting.',
'Maktab gazetasi uchun 70–90 so‘zli fikr yozing: tezis, misol, qarshi dalil va taklif.',
'Ein späterer Unterrichtsbeginn könnte vielen Jugendlichen helfen, morgens aufmerksamer zu sein. Ich selbst fahre sehr früh los und brauche in der ersten Stunde oft etwas Zeit. Trotzdem sollten wir nicht nur an diesen Vorteil denken. Ein späteres Ende kann Sportkurse oder die Betreuung kleinerer Geschwister erschweren. Deshalb schlage ich vor, zuerst Schüler, Eltern und Lehrkräfte nach ihren Tagesabläufen zu fragen. Anschließend könnten wir einzelne Tage testen. Eine gute Lösung sollte möglichst viele Bedürfnisse berücksichtigen und nach dem Versuch noch verändert werden können.',
'Bir taraflama xulosa qilmay, dalil va muqobilni bog‘lang.')

add('Homeoffice im kleinen Team',
'Ein kleines Übersetzungsbüro führt zwei Tage Arbeit von zu Hause ein. Anfangs freuen sich alle über weniger Fahrzeit und mehr Ruhe. Nach einigen Wochen zeigt sich jedoch, dass kurze Rückfragen länger dauern, weil nicht klar ist, wer gerade erreichbar ist. Neue Mitarbeitende fühlen sich besonders unsicher. Das Team möchte das Modell deshalb verbessern, statt es sofort abzuschaffen. Es vereinbart ein kurzes Treffen am Morgen und einen gemeinsamen Zeitraum für Rückfragen. Komplizierte Themen sollen nicht in langen Nachrichtenketten geklärt werden, sondern in einem Gespräch. Gleichzeitig bleiben ruhige Arbeitsphasen geschützt. Am Freitag sammeln die Beschäftigten offene Punkte für die nächste Woche. Nach drei Monaten wird erneut besprochen, ob diese Regeln hilfreich sind. Dabei zählen nicht nur erledigte Aufgaben, sondern auch Zusammenarbeit, Einarbeitung und das Gefühl, ausreichend Unterstützung zu bekommen.',
'''Wie viele Tage pro Woche arbeitet das Team zu Hause?|Zwei Tage|Jamoa haftada ikki kun uyda ishlaydi.
Wer fühlt sich besonders unsicher?|Neue Mitarbeitende|Yangi xodimlar ayniqsa o‘zini ishonchsiz his qiladi.
Wie sollen komplizierte Themen geklärt werden?|In einem Gespräch|Murakkab masalalar uzun yozishmalar emas, suhbat orqali hal qilinadi.''',
'Gemeinsame Regeln aushandeln',
'Teamleiterin: Was brauchen wir, damit die Arbeit zu Hause besser funktioniert? Aziz: Ich brauche längere Zeiten ohne Unterbrechung. Im Moment kommen ständig kurze Fragen. Mira: Für mich sind schnelle Antworten wichtig, weil ich noch neu bin. Wenn ich warte, komme ich nicht weiter. Aziz: Das verstehe ich. Vielleicht können wir feste Fragezeiten einführen. Teamleiterin: Wie wäre es mit einer halben Stunde am Vormittag und einer am Nachmittag? Mira: Das würde bei vielen Fragen reichen. Für dringende Probleme brauche ich aber einen klaren Kontakt. Teamleiterin: Dann übernimmt jeden Tag eine erfahrene Person diese Rolle. Aziz: Einverstanden, solange die Aufgabe wechselt. Mira: Außerdem hätte ich gern eine kurze Sammlung häufiger Fragen. Teamleiterin: Gute Idee. Wir beginnen klein und ergänzen sie nach Bedarf. In vier Wochen schauen wir, ob die Regeln uns tatsächlich entlasten.',
'''Was braucht Aziz besonders?|Längere Zeiten ohne Unterbrechung|Azizga uzluksiz ishlash uchun uzoqroq vaqt kerak.
Wie lang soll jede feste Fragezeit sein?|Eine halbe Stunde|Har bir savol vaqti yarim soat bo‘lishi taklif etiladi.
Wann wird die Wirkung der Regeln überprüft?|In vier Wochen|Qoidalarning ta’siri to‘rt haftadan keyin tekshiriladi.''',
'Masofadan ishlashning afzallik va kamchiliklari haqida qisqa taqdimot qiling; yangi xodimlar ehtiyojini ham hisobga oling.',
'Arbeit von zu Hause spart Wege und kann konzentriertes Arbeiten erleichtern. Ich sehe aber auch Schwierigkeiten, besonders für neue Kollegen. Eine kleine Frage kann lange offenbleiben, wenn niemand erreichbar ist. Deshalb brauchen wir klare Kontaktzeiten und wechselnde Ansprechpersonen für dringende Probleme. Gleichzeitig sollte nicht jede Nachricht sofort eine Unterbrechung auslösen. Für mich ist ein gemischtes Modell sinnvoll: einige Tage zu Hause, andere gemeinsam im Büro. Entscheidend ist, ob Zusammenarbeit und Unterstützung im Alltag funktionieren.',
'Afzallik, muammo va jamoaga mos ikkita chora ayting.',
'Jamoa rahbariga 70–90 so‘zli yaxshilash taklifi yozing: kuzatilgan muammo va sinov qoidalari.',
'Liebe Frau Neumann, die Arbeit von zu Hause hilft mir, längere Aufgaben konzentriert zu erledigen. Gleichzeitig habe ich bemerkt, dass Rückfragen neuer Kollegen manchmal lange offenbleiben. Ich schlage deshalb zwei kurze Fragezeiten pro Tag vor. Für dringende Probleme könnte eine täglich wechselnde Ansprechperson zuständig sein. Eine kleine Übersicht häufiger Fragen würde zusätzlich helfen. Können wir diese Regeln vier Wochen ausprobieren und anschließend gemeinsam auswerten? So könnten wir ruhige Arbeitsphasen erhalten und trotzdem genügend Unterstützung anbieten. Gern helfe ich beim Aufbau der Übersicht. Viele Grüße, Aziz',
'Muammo, ikki amaliy qoida va sinovdan keyingi baholashni yozing.')

add('Ein Freizeitangebot für alle',
'Ein Sportverein möchte neue Mitglieder gewinnen und wirbt mit dem Satz Sport für alle. Bei einem offenen Gespräch erzählen Interessierte jedoch von Hindernissen. Eine Mutter findet keine Betreuung für ihr Kind, ein Schichtarbeiter kann keine feste wöchentliche Zeit zusagen, und ein älterer Mann versteht das Onlineformular nicht. Der Verein erkennt, dass ein niedriger Beitrag allein noch keinen einfachen Zugang schafft. Er bietet deshalb zunächst einen monatlichen offenen Nachmittag ohne langfristige Anmeldung an. Freiwillige helfen vor Ort beim Formular, und die Zeiten wechseln zwischen Samstag und Sonntag. Für die Kinder wird parallel ein betreutes Spielangebot geplant. Noch sind nicht alle Fragen gelöst, besonders die Finanzierung. Der Vorstand möchte nach drei Terminen prüfen, wer tatsächlich teilgenommen hat und welche Menschen weiterhin fehlen. Das Motto soll an konkreten Erfahrungen gemessen werden.',
'''Welches Problem hat der ältere Mann?|Er versteht das Onlineformular nicht|Keksa odam onlayn shaklni tushunmaydi.
Wie oft soll der offene Nachmittag stattfinden?|Einmal im Monat|Ochiq sport kuni oyiga bir marta bo‘ladi.
Nach wie vielen Terminen will der Vorstand die Teilnahme prüfen?|Nach drei Terminen|Rahbariyat uch uchrashuvdan keyin qatnashishni tekshiradi.''',
'Einen offenen Sporttag planen',
'Trainerin: Unser Sporttag soll auch Menschen ansprechen, die lange keinen Sport gemacht haben. Wie können wir den Einstieg leichter machen? Freiwilliger: Wir sollten deutlich sagen, dass niemand besondere Kenntnisse braucht. Teilnehmerin: Und bitte keine Pflicht, sich sofort für ein ganzes Jahr anzumelden. Trainerin: Einverstanden. Man kann erst einmal ausprobieren. Freiwilliger: Was machen wir mit den Informationen? Nur eine Ankündigung im Internet reicht wahrscheinlich nicht. Teilnehmerin: Hängt auch Plakate in der Bibliothek und im Nachbarschaftshaus auf. Trainerin: Gut. Wir brauchen außerdem jemanden am Eingang, der Fragen beantwortet. Freiwilliger: Das übernehme ich. Teilnehmerin: Können die Leute zwischen mehreren Aktivitäten wählen? Trainerin: Ja, wir bieten leichte Bewegung, Ballspiele und einen Spaziergang an. Jeder entscheidet selbst, was passt. Nach dem Tag fragen wir kurz nach, was den Einstieg erleichtert oder erschwert hat.',
'''Welche langfristige Verpflichtung möchte die Teilnehmerin vermeiden?|Eine Anmeldung für ein ganzes Jahr|U darhol bir yilga a’zo bo‘lish majburiyatini xohlamaydi.
Wo sollen außer im Internet Informationen hängen?|In der Bibliothek und im Nachbarschaftshaus|E’lonlar kutubxona va mahalla uyida ham bo‘lishi kerak.
Wer beantwortet Fragen am Eingang?|Der Freiwillige|Kirishda savollarga ko‘ngilli javob beradi.''',
'Hamma uchun qulay tadbirni rejalang: yangi kelganlar, vaqt cheklovi va ro‘yxatdan o‘tishdagi qiyinchiliklarni hisobga oling.',
'A: Wir möchten neue Leute erreichen, aber eine Onlineanmeldung ist für manche schwierig. B: Dann bieten wir auch Hilfe vor Ort an. A: Außerdem sollte niemand sofort Mitglied werden müssen. B: Richtig, ein offener Nachmittag wäre ein guter Anfang. Wir brauchen verschiedene Aktivitäten und klare Informationen. A: Ich kümmere mich um Plakate in der Bibliothek. B: Ich begrüße die Gäste am Eingang. Nach drei Terminen prüfen wir, wen wir erreicht haben und welche Hindernisse bleiben.',
'Kamida ikki to‘siqni kamaytiradigan choralar va vazifalarni kelishing.',
'Sport klubiga 70–90 so‘zli mulohaza yozing: shaxsiy to‘siq, mos taklif va tajriba natijasini bilish usuli.',
'Sehr geehrter Vorstand, Ihr offener Sporttag interessiert mich sehr. Wegen meiner wechselnden Arbeitszeiten kann ich jedoch nicht jede Woche zur gleichen Zeit kommen. Ein monatliches Angebot mit wechselnden Terminen wäre für mich leichter nutzbar. Hilfreich fände ich außerdem, zunächst ohne Jahresmitgliedschaft teilnehmen zu können. Bitte veröffentlichen Sie Informationen auch in der Bibliothek, damit mehr Menschen davon erfahren. Nach den ersten Terminen könnten Sie kurz nachfragen, welche Zeiten und Aktivitäten passen. Ich würde gern teilnehmen und meine Erfahrungen mitteilen. Mit freundlichen Grüßen, Karim Rustamov',
'Shaxsiy ehtiyoj, taklif va fikr yig‘ish usulini kiriting.')

add('Eine Ausstellung mit vielen Perspektiven',
'Ein Stadtmuseum plant eine Ausstellung über das Ankommen in einer neuen Umgebung. Die Kuratorin möchte nicht nur Dokumente zeigen, sondern auch persönliche Gegenstände und Erinnerungen. Sie lädt Menschen aus verschiedenen Generationen ein. Ein Mann bringt seinen ersten Wohnungsschlüssel mit, eine Frau ein Rezeptheft ihrer Mutter. Eine junge Teilnehmerin möchte ihre Geschichte erzählen, aber ihren vollständigen Namen nicht veröffentlichen. Das Museum akzeptiert diesen Wunsch. In den Gesprächen zeigt sich, dass Erfahrungen sehr unterschiedlich sind: Manche erinnern sich zuerst an Einsamkeit, andere an Unterstützung oder berufliche Chancen. Deshalb verzichtet das Team auf eine einzige große Erfolgsgeschichte. Zu jedem Gegenstand erscheint ein kurzer Text in einfacher Sprache. Besucher können eigene Gedanken auf Karten schreiben. Diese werden regelmäßig geprüft, damit die Ausstellung ein respektvoller Ort bleibt und persönliche Erfahrungen nicht durch verletzende Kommentare abgewertet werden.',
'''Welchen Gegenstand bringt der Mann mit?|Seinen ersten Wohnungsschlüssel|Erkak ilk kvartirasining kalitini olib keladi.
Was möchte die junge Teilnehmerin nicht veröffentlichen?|Ihren vollständigen Namen|Yosh ishtirokchi to‘liq ismini e’lon qilishni xohlamaydi.
Wie können Besucher eigene Gedanken beitragen?|Auf Karten schreiben|Mehmonlar fikrlarini kartalarga yozishlari mumkin.''',
'Über einen persönlichen Gegenstand sprechen',
'Interviewer: Welchen Gegenstand haben Sie heute mitgebracht? Gast: Eine kleine Teedose. Sie ist nicht wertvoll, aber ich habe sie von meiner Großmutter bekommen. Interviewer: Was verbinden Sie damit? Gast: Als ich in meine erste eigene Wohnung gezogen bin, war vieles fremd. Der Geruch aus der Dose erinnerte mich an gemeinsame Nachmittage bei ihr. Interviewer: Benutzen Sie die Dose noch? Gast: Ja, inzwischen bewahre ich darin kleine Zettel mit neuen deutschen Wörtern auf. Dadurch verbindet sie für mich Vergangenheit und Gegenwart. Interviewer: Dürfen wir Ihre Geschichte mit Ihrem Namen ausstellen? Gast: Meinen Vornamen können Sie nennen, aber bitte nicht meinen Wohnort. Interviewer: Natürlich. Sie bekommen den Text vor der Veröffentlichung zum Lesen. Gast: Danke. Mir ist wichtig, dass die Geschichte einfach erzählt wird und nicht so klingt, als wäre die Dose für alle Menschen dasselbe Symbol.',
'''Von wem hat der Gast die Teedose bekommen?|Von seiner Großmutter|Choy qutisini buvisidan olgan.
Was bewahrt der Gast heute darin auf?|Zettel mit neuen deutschen Wörtern|Hozir qutida yangi nemischa so‘zlar yozilgan qog‘ozlar saqlanadi.
Welche Ortsangabe soll nicht veröffentlicht werden?|Der Wohnort|Yashash joyi e’lon qilinmasligi kerak.''',
'Siz uchun ahamiyatli buyum haqida ikki daqiqalik taqdimot qiling: kelib chiqishi, xotira va hozirgi roli.',
'Ich möchte ein altes Notizbuch vorstellen, das ich von meiner Schwester bekommen habe. Als ich mit Deutsch angefangen habe, schrieb ich darin meine ersten Sätze. Heute sehe ich viele Fehler, aber auch meinen Fortschritt. Das Buch erinnert mich daran, dass Lernen Zeit braucht. Besonders wichtig ist mir eine Seite mit Fragen für mein erstes Gespräch im Kurs. Ich benutze das Heft nicht mehr täglich, bewahre es aber auf, weil es einen persönlichen Anfang sichtbar macht.',
'Buyumni tasvirlang, bitta aniq xotira va shaxsiy ma’noni bog‘lang.',
'Muzey uchun buyumingiz haqida 70–90 so‘zli izoh yozing; bir xotira va nashr uchun afzal ko‘rgan nomingizni ayting.',
'Dieses Notizbuch hat mir meine Schwester geschenkt, als ich meinen ersten Deutschkurs begonnen habe. Darin stehen neue Wörter, kurze Dialoge und viele Verbesserungen in verschiedenen Farben. Besonders erinnere ich mich an die Vorbereitung auf mein erstes Telefonat auf Deutsch. Damals brauchte ich für drei Sätze fast eine ganze Seite. Heute hilft mir das Buch, meinen Fortschritt zu sehen und geduldiger mit mir zu sein. Für die Ausstellung möchte ich nur mit meinem Vornamen, Dilnoza, genannt werden. Meinen Wohnort möchte ich nicht veröffentlichen.',
'Aniq buyum, xotira va nashrga oid istagingizni yozing.')

add('Ein Streit um den gemeinsamen Raum',
'In einem Kulturhaus nutzen ein Chor und eine Theatergruppe denselben großen Raum. Seit einigen Wochen findet der Chor nach seiner Probe die Stühle anders angeordnet vor. Die Theatergruppe wiederum ärgert sich über Notenständer, die ihre Bewegungen behindern. Zunächst beschweren sich beide Gruppen nur untereinander. Als eine Probe verspätet beginnt, lädt die Hausleitung zu einem Gespräch ein. Jede Seite beschreibt zuerst, was sie konkret braucht, ohne der anderen Absicht zu unterstellen. Es zeigt sich, dass die Zeiten im Buchungskalender keine Aufräumphase enthalten. Gemeinsam vereinbaren sie nun fünfzehn Minuten zum Umbauen und markieren einen festen Platz für Material. Fotos zeigen die gewünschte Grundordnung. Nach einem Monat wollen sie prüfen, ob die Absprachen eingehalten werden. Der Konflikt verschwindet nicht durch eine Entschuldigung allein, sondern durch veränderte Abläufe, die für beide Seiten nachvollziehbar sind.',
'''Welche zwei Gruppen nutzen den Raum?|Ein Chor und eine Theatergruppe|Xonadan xor va teatr guruhi foydalanadi.
Was fehlt bisher im Buchungskalender?|Eine Aufräumphase|Bron jadvalida yig‘ishtirish uchun vaqt yo‘q.
Wie viel Zeit wird zum Umbauen vereinbart?|Fünfzehn Minuten|Xonani qayta tartiblashga o‘n besh daqiqa belgilanadi.''',
'Im Konflikt beim Thema bleiben',
'Chorleiter: Wenn wir kommen, stehen die Stühle oft im Kreis. Wir brauchen Reihen und verlieren dadurch Probenzeit. Theaterleiterin: Für unsere Übungen brauchen wir den Kreis. Ich dachte, jede Gruppe baut selbst um. Chorleiter: Das war für uns nicht klar. Hausleiterin: Dann fehlt offenbar eine gemeinsame Regel. Wie viel Zeit brauchen Sie jeweils? Theaterleiterin: Zehn Minuten reichen meistens, wenn alle mithelfen. Chorleiter: Bei uns ähnlich. Hausleiterin: Wir könnten fünfzehn Minuten zwischen den Buchungen frei lassen. Theaterleiterin: Gut, aber wohin mit den Notenständern? Chorleiter: In die hintere Ecke, wenn wir dort einen festen Platz bekommen. Hausleiterin: Ich markiere den Bereich morgen. Außerdem machen wir Fotos von der Grundordnung. Theaterleiterin: Damit kann ich arbeiten. Chorleiter: Ich auch. Wichtig ist mir, dass wir Probleme künftig direkt ansprechen, bevor sich wieder Ärger ansammelt.',
'''Welche Stuhlanordnung braucht der Chor?|Reihen|Xor uchun stullar qator qilib qo‘yilishi kerak.
Wohin sollen die Notenständer kommen?|In die hintere Ecke|Nota stendlari orqa burchakka qo‘yiladi.
Wer markiert den Materialbereich?|Die Hausleiterin|Jihozlar joyini madaniyat uyi rahbari belgilaydi.''',
'Umumiy joy yuzasidan kelishmovchilikni rollarda hal qiling: kuzatuv, ehtiyoj va tekshiriladigan kelishuv.',
'A: Wenn ich den Raum benutze, liegen oft Materialien auf dem Tisch. Dadurch kann ich nicht sofort anfangen. B: Ich brauche die Sachen für meinen Kurs, wusste aber nicht, dass sie stören. A: Können wir einen festen Platz dafür finden? B: Ja, das Regal neben der Tür wäre geeignet. A: Dann räumt jede Gruppe vor dem Ende ihre Sachen dorthin. B: Einverstanden. Nach zwei Wochen sprechen wir noch einmal darüber, ob der Platz ausreicht.',
'Ayblovsiz kuzatuv ayting va kim nima qilishini kelishing.',
'Ikki guruhga kelishilgan xona qoidalarini 70–90 so‘zli xatda tasdiqlang.',
'Liebe Mitglieder beider Gruppen, vielen Dank für das sachliche Gespräch. Zwischen den Buchungen bleiben künftig fünfzehn Minuten zum Umbauen frei. Jede Gruppe stellt ihre Materialien vor dem Verlassen an den markierten Platz in der hinteren Ecke. Die Fotos an der Tür zeigen die vereinbarte Grundordnung der Stühle. Falls etwas nicht funktioniert, sprechen die Gruppenleitungen direkt miteinander. Nach einem Monat prüfen wir gemeinsam, ob die Zeiten ausreichen. Bitte erklären Sie die Absprachen auch neuen Mitgliedern, damit alle dieselben Informationen haben. Freundliche Grüße, Ihre Hausleitung',
'Vaqt, material joyi, aloqa yo‘li va qayta tekshiruvni yozing.')

add('Nach dem Kurs weiterlernen',
'Kurz vor dem Ende ihres Deutschkurses erstellt Malika einen Plan für die nächsten drei Monate. Sie möchte nicht einfach dieselben Übungen wiederholen, sondern Deutsch stärker in ihren Alltag einbauen. Montags liest sie einen kurzen Artikel und fasst ihn mündlich zusammen. Mittwochs trifft sie eine Sprachpartnerin, mit der sie abwechselnd Themen auswählt. Einmal im Monat besucht sie eine öffentliche Veranstaltung und notiert danach neue Ausdrücke. Gleichzeitig behält sie ein kleines Fehlerheft, in dem nur häufige Schwierigkeiten stehen. Ihre Lehrerin rät ihr, Fortschritte nicht ausschließlich an fehlerfreien Sätzen zu messen. Auch eine erklärte Meinung oder ein selbstständig geführtes Telefonat zählt. Malika vereinbart deshalb mit sich selbst eine monatliche Rückschau. Wenn ein Plan zu aufwendig ist, möchte sie ihn anpassen, statt das Lernen ganz aufzugeben. Ihr Ziel bleibt regelmäßiger Kontakt mit der Sprache.',
'''Für welchen Zeitraum macht Malika ihren Plan?|Für die nächsten drei Monate|Malika kelgusi uch oy uchun reja tuzadi.
Was macht sie mittwochs?|Sie trifft eine Sprachpartnerin|Chorshanba kunlari til sherigi bilan uchrashadi.
Wie oft plant sie eine Rückschau?|Einmal im Monat / Monatlich|Oyiga bir marta natijalarni ko‘rib chiqadi.''',
'Ziele realistisch formulieren',
'Berater: Was möchten Sie nach diesem Kurs auf Deutsch besser können? Teilnehmer: Ich möchte im Beruf sicherer telefonieren und bei Besprechungen meine Meinung sagen. Berater: Das sind zwei konkrete Bereiche. Wie könnten Sie sie üben? Teilnehmer: Ich könnte jede Woche ein Telefongespräch mit einem Kollegen nachspielen. Für Besprechungen würde ich vorher zwei Sätze zu einem Thema vorbereiten. Berater: Gut. Woran erkennen Sie einen Fortschritt? Teilnehmer: Wenn ich nicht mehr jeden Satz übersetzen muss und eine Rückfrage selbst beantworten kann. Berater: Das klingt überprüfbar. Planen Sie auch Schwierigkeiten ein? Teilnehmer: In arbeitsreichen Wochen schaffe ich vielleicht nur eine Übung. Dann mache ich weniger, aber höre nicht ganz auf. Berater: Genau. Nach einem Monat können Sie prüfen, welche Methode geholfen hat. Teilnehmer: Ich möchte außerdem meinen Kollegen fragen, ob meine Aussagen klarer geworden sind, statt nur selbst darüber zu urteilen.',
'''Welche zwei beruflichen Situationen möchte der Teilnehmer verbessern?|Telefonate und Besprechungen|Ishtirokchi telefon suhbatlari va yig‘ilishdagi fikr bildirishni yaxshilamoqchi.
Wie oft möchte er ein Telefongespräch üben?|Jede Woche|Telefon suhbatini har hafta mashq qilmoqchi.
Wen will er zusätzlich um Rückmeldung bitten?|Seinen Kollegen|Qo‘shimcha fikr uchun hamkasbiga murojaat qiladi.''',
'Kursdan keyingi uch oylik o‘quv rejangizni taqdim qiling: ikki maqsad, odatlar va natijani bilish mezoni.',
'In den nächsten drei Monaten möchte ich vor allem besser telefonieren und längere Texte verstehen. Dafür übe ich einmal pro Woche ein Gespräch mit meiner Lernpartnerin. Außerdem lese ich montags einen kurzen Artikel und fasse die Hauptidee zusammen. Fortschritt bedeutet für mich, dass ich Rückfragen ohne vorbereiteten Text beantworten kann. Am Monatsende höre ich eine eigene Aufnahme an und vergleiche sie mit der vorherigen. In stressigen Wochen verkürze ich die Übungen, statt sie ganz zu streichen.',
'Ikki o‘lchanadigan maqsad va moslashuvchan jadval ayting.',
'Til sherigingizga 70–90 so‘zli davomiy mashq rejasini taklif qiling; vazifa almashish va baholashni kiriting.',
'Liebe Amina, auch nach dem Kurs würde ich gern regelmäßig mit dir Deutsch üben. Wir könnten uns jeden Mittwoch für eine halbe Stunde treffen. Eine Woche wählen wir ein Alltagsthema, in der nächsten üben wir ein Gespräch aus dem Beruf. Die Vorbereitung teilen wir abwechselnd auf. Am Ende geben wir uns jeweils eine positive Rückmeldung und einen konkreten Verbesserungsvorschlag. Nach einem Monat prüfen wir, ob Zeit und Aufgaben passen. Wenn du einmal wenig Zeit hast, können wir stattdessen kurze Sprachnachrichten austauschen. Liebe Grüße, Malika',
'Muntazam vaqt, navbat, fikr bildirish va muqobil formatni yozing.')

add('Eigene B1-Übung: Ein Projekttag mit Änderungen',
'Ein Sprachkurs plant einen öffentlichen Projekttag über nachhaltigen Alltag. Drei Gruppen bereiten eine Tauschstation, eine kleine Ausstellung und Gespräche über Mobilität vor. Zwei Tage vor dem Termin fällt der große Raum wegen eines Wasserschadens aus. Die Kursleitung bietet zwei kleinere Räume an, die jedoch auf unterschiedlichen Stockwerken liegen. Ein Teilnehmer weist darauf hin, dass nicht alle Gäste Treppen benutzen können. Deshalb wird die Gesprächsrunde in den gut zugänglichen Raum im Erdgeschoss verlegt. Die Ausstellung findet oben statt; ihre wichtigsten Texte werden zusätzlich unten ausgelegt. Die Tauschstation zieht in den überdachten Hof. Alle Ankündigungen werden aktualisiert, und am Eingang steht eine Person für Fragen bereit. Der Projekttag wird kleiner als geplant, kann aber stattfinden. Anschließend hält die Gruppe fest, welche Informationen bei der Änderung gefehlt haben und was sie künftig früher prüfen möchte.',
'''Warum fällt der große Raum aus?|Wegen eines Wasserschadens|Katta xona suvdan zarar ko‘rgani sabab ishlatilmaydi.
Wo findet die Gesprächsrunde statt?|Im Erdgeschoss|Suhbat zinadan foydalana olmaydigan mehmonlar uchun pastki qavatga o‘tkaziladi.
Wo wird die Tauschstation aufgebaut?|Im überdachten Hof|Almashish joyi usti yopiq hovliga ko‘chiriladi.''',
'Eigene B1-Übung: Die letzten Absprachen',
'Leiterin: Unser Projekttag beginnt morgen um elf. Wegen der Raumänderung brauchen wir besonders klare Hinweise. Farid: Ich kann um zehn kommen und die Schilder aufhängen. Amina: Ich begrüße die Gäste am Eingang. Was sage ich zur Ausstellung im oberen Stockwerk? Leiterin: Erkläre bitte, dass eine Auswahl der Texte auch unten liegt. Wer Fragen zu den Bildern hat, kann sich an mich wenden. Bek: Für die Tauschstation fehlen noch zwei Tische. Farid: Die können wir aus Raum vier holen, aber erst nach dem Morgenkurs. Leiterin: Gut, macht das bitte zu zweit. Amina: Und wenn es im Hof zu windig ist? Leiterin: Dann befestigen wir die Schilder mit Klammern und stellen leichte Dinge näher an die Wand. Bek: Nach der Veranstaltung sollten wir kurz sammeln, was trotz der Änderungen funktioniert hat. Leiterin: Ja, dafür reservieren wir zwanzig Minuten.',
'''Wann kommt Farid zum Aufhängen der Schilder?|Um zehn|Farid belgilarni osish uchun soat o‘nda keladi.
Wann dürfen die Tische aus Raum vier geholt werden?|Nach dem Morgenkurs|Stollarni ertalabki kurs tugagandan keyin olish mumkin.
Wie viel Zeit ist für die Auswertung reserviert?|Zwanzig Minuten|Yakuniy tahlil uchun yigirma daqiqa ajratiladi.''',
'Mualliflik B1 mashqi, rasmiy to‘liq imtihon emas: sherik bilan o‘zgargan tadbir rejasini 3 daqiqada kelishing. Joy, kirish imkoniyati, vazifa va muqobilni muhokama qiling.',
'A: Der große Raum ist nicht verfügbar. Wir müssen das Programm aufteilen. B: Dann sollte die Gesprächsrunde unten stattfinden, damit alle teilnehmen können. A: Einverstanden. Ich aktualisiere die Ankündigung und drucke Hinweise aus. B: Ich organisiere zwei Personen am Eingang. Was machen wir mit der Ausstellung? A: Sie bleibt oben, aber die wichtigsten Texte legen wir zusätzlich unten aus. B: Gut. Nach dem Projekttag sammeln wir Rückmeldungen, damit wir beim nächsten Mal früher an solche Fragen denken.',
'To‘rtta reja bandi, sherik taklifiga javob va yakuniy kelishuv bo‘lsin.',
'Mualliflik B1 mashqi: mehmonlarga tadbirdagi o‘zgarishlarni 70–90 so‘zli rasmiy xatda bildiring. Sabab, yangi joylashuv va yordamni ayting.',
'Sehr geehrte Gäste, wegen eines Wasserschadens steht unser großer Veranstaltungsraum morgen leider nicht zur Verfügung. Der Projekttag beginnt trotzdem wie geplant um elf Uhr. Die Gesprächsrunde findet im Erdgeschoss statt, die Tauschstation im überdachten Hof. Die Ausstellung liegt im ersten Stock; eine Auswahl der Texte können Sie auch unten lesen. Am Eingang helfen Ihnen unsere Kursmitglieder bei der Orientierung. Bitte informieren Sie weitere angemeldete Personen über die Änderung. Vielen Dank für Ihr Verständnis. Wir freuen uns auf Ihren Besuch. Mit freundlichen Grüßen, das Kursteam',
'O‘zgarish sababi, uch joy va mehmonlarga yordamni aniq yozing.')

add('Eigene B1-Übung: Ein Kurs wird bewertet',
'Nach einem sechsmonatigen Abendkurs bittet das Bildungszentrum die Teilnehmenden um Rückmeldung. Viele loben die praktischen Gespräche und die regelmäßige Zusammenarbeit in Paaren. Gleichzeitig wünschen sich einige mehr Zeit für längere Texte. Andere erklären, dass zusätzliche Hausaufgaben wegen ihrer Arbeitszeiten kaum möglich wären. Die Kursleiterin fasst die unterschiedlichen Stimmen zusammen, ohne nur die häufigste Meinung zu übernehmen. Sie schlägt vor, im nächsten Kurs einen Teil der Aufgaben wählbar zu machen: Ein kurzer Pflichtteil sichert die gemeinsame Grundlage, freiwillige Vertiefungen bieten mehr Übung. Auch die Raumplanung soll verbessert werden, weil ein Wechsel mehrfach erst kurz vor Unterrichtsbeginn mitgeteilt wurde. Das Zentrum veröffentlicht anschließend eine kurze Antwort auf die Rückmeldungen. Darin steht, welche Änderungen sofort möglich sind und welche noch geprüft werden. Die Teilnehmenden sehen so, dass ihre Erfahrungen konkrete Folgen haben können.',
'''Wofür wünschen sich einige Teilnehmende mehr Zeit?|Für längere Texte|Ba’zi ishtirokchilar uzunroq matnlar uchun ko‘proq vaqt xohlashadi.
Warum sind zusätzliche Hausaufgaben für andere schwierig?|Wegen ihrer Arbeitszeiten|Boshqalarning ish vaqti qo‘shimcha uy vazifasiga imkon bermaydi.
Welche organisatorische Information kam mehrfach zu spät?|Ein Raumwechsel|Xona almashgani haqidagi xabar bir necha marta kech berilgan.''',
'Eigene B1-Übung: Eine Präsentation besprechen',
'Moderatorin: Heute hören wir eine kurze Meinung zum Thema Lernen in Gruppen. Nuri: Für mich ist Gruppenlernen besonders hilfreich, wenn wir ein klares Ziel haben. Im Deutschkurs haben wir einmal eine Reise geplant. Jeder musste einen Vorschlag erklären und auf Fragen reagieren. Dadurch habe ich mehr gesprochen als bei einer stillen Übung. Allerdings klappt Gruppenarbeit nicht automatisch. Wenn immer dieselbe Person redet, lernen die anderen wenig. Deshalb sollten Aufgaben und Redezeit verteilt werden. Moderatorin: Würdest du also nie allein lernen? Nuri: Doch, neue Wörter wiederhole ich gern allein, weil ich mein Tempo selbst bestimmen kann. Ich würde beide Formen verbinden. Moderatorin: Was empfiehlst du einer neuen Lerngruppe? Nuri: Mit einer kleinen Aufgabe beginnen und am Ende prüfen, ob alle mitgemacht haben. Danach kann man die Aufgaben schrittweise erweitern, statt sofort einen komplizierten Wochenplan zu erstellen.',
'''Welche gemeinsame Aufgabe nennt Nuri als Beispiel?|Eine Reise planen|Nuri misol sifatida safarni rejalashni aytadi.
Was wiederholt er lieber allein?|Neue Wörter|Yangi so‘zlarni yolg‘iz takrorlashni afzal ko‘radi.
Was soll eine neue Gruppe am Ende prüfen?|Ob alle mitgemacht haben|Mashq oxirida hamma qatnashganini tekshirish kerak.''',
'Mualliflik B1 mashqi: „Yolg‘iz yoki guruhda o‘qish?“ mavzusida 2 daqiqa gapiring, so‘ng sherik savoliga javob bering. Tajriba, afzallik, kamchilik va xulosani kiriting.',
'Ich lerne sowohl allein als auch mit anderen. Allein kann ich schwierige Wörter in meinem Tempo wiederholen. In einer Gruppe übe ich dagegen, spontan zu reagieren. Bei einer gemeinsamen Reiseplanung musste ich meine Vorschläge erklären, und das war sehr hilfreich. Ein Nachteil ist, dass manchmal nur eine Person spricht. Deshalb brauchen wir klare Aufgaben. Ich würde beide Lernformen verbinden. Auf die Frage nach meiner Lieblingsform würde ich antworten: Für Gespräche wähle ich die Gruppe, für die erste Wiederholung oft die Einzelarbeit.',
'Tuzilgan taqdimot, aniq tajriba va savolga mazmunli javob bo‘lsin.',
'Mualliflik B1 mashqi: kurs haqida 70–90 so‘zli rasmiy fikr yozing; ijobiy tajriba, bitta muammo va bajariladigan taklifni kiriting.',
'Sehr geehrte Frau Weber, vielen Dank für den abwechslungsreichen Kurs. Besonders die Gespräche in Paaren haben mir geholfen, freier zu sprechen. Schwieriger fand ich die kurzfristigen Raumwechsel, weil ich nach der Arbeit oft direkt zum Unterricht komme. Bitte teilen Sie solche Änderungen künftig möglichst früh mit. Für den nächsten Kurs wünsche ich mir außerdem freiwillige Übungen zu längeren Texten. So könnten Interessierte mehr lesen, ohne dass alle zusätzliche Pflichtaufgaben bekommen. Insgesamt habe ich viel gelernt und würde den Kurs weiterempfehlen. Mit freundlichen Grüßen, Amina Saidova',
'Ijobiy jihat, aniq muammo va real taklifni hurmatli uslubda yozing.')

add('Eigene B1-Übung: Ein neuer Anfang nach 24 Wochen',
'Am letzten Kurstag legt die Gruppe keine Liste perfekter Ergebnisse vor. Stattdessen bringt jeder ein Beispiel dafür mit, was heute selbstständiger gelingt. Rano zeigt eine beantwortete Anfrage an ein Kursbüro. Bek erzählt von einem Gespräch mit seinem Vermieter, bei dem er ruhig nach einer Erklärung gefragt hat. Andere berichten von Büchern, Freundschaften oder schwierigen Telefonaten. Die Lehrerin betont, dass solche Erfahrungen eine standardisierte Prüfung nicht ersetzen, aber persönliche Fortschritte sichtbar machen. Für die nächste Lernphase formuliert jeder ein konkretes Ziel und einen ersten Schritt. Die Gruppe möchte sich einmal im Monat treffen und abwechselnd ein Thema vorbereiten. Niemand verspricht, nach sechs Monaten jede Situation mühelos zu verstehen. Trotzdem ist deutlich geworden, dass die Teilnehmenden Fragen stellen, Meinungen begründen und gemeinsam Lösungen entwickeln können. Diese Fähigkeiten sollen nun weiter wachsen.',
'''Welches schriftliche Beispiel bringt Rano mit?|Eine beantwortete Anfrage an ein Kursbüro|Rano kurs idorasiga yuborgan va javob olingan so‘rovini ko‘rsatadi.
Mit wem hat Bek ein Gespräch geführt?|Mit seinem Vermieter|Bek uy egasi bilan gaplashgan.
Wie oft möchte sich die Gruppe weiterhin treffen?|Einmal im Monat|Guruh bundan keyin oyiga bir marta uchrashmoqchi.''',
'Eigene B1-Übung: Gemeinsam weitermachen',
'Amina: Unser Kurs endet, aber ich möchte den Kontakt nicht verlieren. Sollen wir weiter zusammen üben? Farid: Gern. Wöchentlich wäre mir zu viel, weil mein neuer Arbeitsplan noch nicht feststeht. Amina: Dann treffen wir uns einmal im Monat. Dazwischen kann jeder freiwillig eine kurze Nachricht zu unserem Thema schicken. Farid: Das klingt machbar. Wo treffen wir uns? Amina: Ich frage in der Bibliothek nach einem Gruppenraum. Falls keiner frei ist, könnten wir online sprechen. Farid: Wer bereitet das erste Thema vor? Amina: Das übernehme ich. Wir sprechen über eine Entscheidung, die unseren Alltag verändert hat. Farid: Gut. Ich kümmere mich um die Terminabfrage. Amina: Lass uns nach drei Treffen prüfen, ob das Format passt. Farid: Einverstanden. Wichtig ist, dass wir weiterlernen, ohne aus unserem Treffen eine zusätzliche Belastung zu machen.',
'''Warum möchte Farid sich nicht wöchentlich treffen?|Sein neuer Arbeitsplan steht noch nicht fest|Faridning yangi ish jadvali hali aniqlanmagan.
Was ist die Alternative, wenn kein Gruppenraum frei ist?|Online sprechen / Ein Onlinetreffen|Guruh xonasi bo‘lmasa onlayn gaplashishadi.
Wer organisiert die Terminabfrage?|Farid|Uchrashuv vaqti bo‘yicha so‘rovni Farid tashkil qiladi.''',
'Yakuniy mualliflik B1 mashqi, rasmiy to‘liq Goethe testi emas: sherigingiz bilan kursdan keyingi guruhni rejalang, keyin o‘sishingiz haqida 1 daqiqa gapiring va bitta savolga javob bering.',
'A: Ich möchte monatliche Treffen vorschlagen. So bleiben wir in Kontakt, ohne zu viel zu planen. B: Gut. Ich frage nach einem Raum, und du sammelst passende Termine. A: Falls kein Raum frei ist, treffen wir uns online. Nach drei Monaten prüfen wir den Plan. Mein persönlicher Fortschritt ist, dass ich heute selbst nachfragen kann. Früher blieb ich bei unbekannten Wörtern still. Als Nächstes möchte ich längere Gespräche führen. Dabei helfen mir Themen, zu denen ich wirklich etwas sagen möchte.',
'Reja, shaxsiy aniq misol va keyingi maqsadni mustaqil ifodalang.',
'Yakuniy mualliflik B1 mashqi: do‘stingizga 70–90 so‘zli xat yozing. Olti oydagi aniq o‘sish, qolgan qiyinchilik va keyingi rejangizni ayting; uni mashqqa taklif qiling.',
'Liebe Malika, unser Deutschkurs ist nun zu Ende. Vor sechs Monaten konnte ich mich nur kurz vorstellen. Heute habe ich selbst bei einem Kursbüro angerufen und meine Fragen geklärt. Lange Gespräche mit mehreren Personen finde ich allerdings noch schwierig. Deshalb möchte ich weiterhin regelmäßig sprechen und kurze Artikel zusammenfassen. Unsere Gruppe plant ein Treffen pro Monat. Hättest du Lust, beim ersten Mal dabei zu sein? Wir wollen über wichtige Entscheidungen im Alltag sprechen. Den genauen Termin schicke ich dir, sobald alle geantwortet haben. Liebe Grüße, Rano',
'Aniq o‘sish dalili, qiyinchilik, amaliy reja va taklif yozing.')

def validate(rows):
    assert len(rows) == 72, f'Expected 72 rows, got {len(rows)}'
    assert [r['no'] for r in rows] == list(range(1, 73))
    ids, texts = set(), set()
    lengths = {'A1': [], 'A2': [], 'B1': []}
    issues = []
    for row in rows:
        no = row['no']
        assert set(row) == {'no', 'reading', 'listening', 'speaking', 'writing'}
        level = 'A1' if no <= 24 else 'A2' if no <= 48 else 'B1'
        lo, hi = {'A1': (35, 65), 'A2': (70, 100), 'B1': (110, 150)}[level]
        for kind in ('reading', 'listening'):
            section = row[kind]
            assert set(section) == {'title', 'text', 'questions'}
            assert section['title'].strip() and section['text'].strip()
            normalized = ' '.join(section['text'].casefold().split())
            assert normalized not in texts, f'Duplicate text: {no} {kind}'
            texts.add(normalized)
            count = len(section['text'].split())
            lengths[level].append(count)
            if not lo <= count <= hi:
                issues.append(f'{no} {kind}: {count} words (target {lo}-{hi})')
            assert len(section['questions']) == 3
            for q in section['questions']:
                assert set(q) == {'id', 'prompt', 'answers', 'explanation'}
                assert q['id'] not in ids, f'Duplicate question ID: {q["id"]}'
                ids.add(q['id'])
                assert all(isinstance(q[k], str) and q[k].strip() for k in ('id', 'prompt', 'explanation'))
                assert isinstance(q['answers'], list) and q['answers']
                assert all(isinstance(a, str) and a.strip() for a in q['answers'])
            if kind == 'listening':
                assert 'audio yozuv emas' in section['title']
        for kind in ('speaking', 'writing'):
            section = row[kind]
            assert set(section) == {'task', 'model', 'criteria'}
            assert section['task'].strip() and section['model'].strip()
            assert len(section['criteria']) == 3 and all(c.strip() for c in section['criteria'])
    assert len(ids) == 432 and len(texts) == 144
    if issues:
        raise ValueError('Length review needed:\n' + '\n'.join(issues))
    return ids, texts, lengths

if __name__ == '__main__':
    ids, texts, lengths = validate(ROWS)
    output = Path(__file__).resolve().parents[1] / 'src/data/german/skills.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(ROWS, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert json.loads(output.read_text(encoding='utf-8')) == ROWS
    print(f'PASS: {len(ROWS)} lessons; 24 A1 + 24 A2 + 24 B1; no=1..72')
    print(f'PASS: {len(texts)} unique reading/listening texts; {len(ids)} globally unique question IDs')
    print('PASS: 72 speaking + 72 writing models; 432 Uzbek production criteria; 432 Uzbek explanations')
    print('PASS: 72 listening texts explicitly labeled teacher-read/synthetic practice, not recorded audio')
    for level, counts in lengths.items():
        print(f'{level}: {len(counts)} texts; words min={min(counts)}, max={max(counts)}, mean={sum(counts)/len(counts):.1f}')
    print(f'JSON: {output}')
    print(f'SOURCE: {Path(__file__).resolve()}')
