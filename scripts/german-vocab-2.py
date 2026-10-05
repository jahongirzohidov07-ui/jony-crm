"""Original German A2 vocabulary with Uzbek explanations, weeks 9-16."""
import json
from pathlib import Path

WEEKS = {}

WEEKS[9] = r"""
die Rundreise|ˈʁʊntˌʁaɪ̯zə|bir necha joyni qamragan sayohat|Unsere Rundreise führt durch drei Länder.|Sayohatimiz uch mamlakatni qamrab oladi.|die Rundreisen
die Abfahrt|ˈapˌfaːɐ̯t|jo‘nab ketish|Vor der Abfahrt kaufe ich eine Zeitung.|Jo‘nab ketishdan oldin gazeta sotib olaman.|die Abfahrten
die Ankunft|ˈanˌkʊnft|yetib kelish|Bei unserer Ankunft scheint die Sonne.|Biz yetib kelganimizda quyosh charaqlaydi.|die Ankünfte
die Strecke|ˈʃtʁɛkə|yo‘l masofasi; yo‘nalish|Diese Strecke fahre ich zum ersten Mal.|Bu yo‘nalishda birinchi marta ketyapman.|die Strecken
die Tageskarte|ˈtaːɡəsˌkaʁtə|bir kunlik chipta|Mit einer Tageskarte kann ich beliebig oft fahren.|Bir kunlik chipta bilan xohlagancha qatnay olaman.|die Tageskarten
der Fahrschein|ˈfaːɐ̯ˌʃaɪ̯n|yo‘l chiptasi|Zeigen Sie bitte Ihren Fahrschein.|Iltimos, yo‘l chiptangizni ko‘rsating.|die Fahrscheine
der Wagen|ˈvaːɡn̩|vagon; avtomobil|Unser Sitzplatz ist im letzten Wagen.|O‘rindig‘imiz oxirgi vagonda.|die Wagen
das Abteil|ˈapˌtaɪ̯l|kupe|Wir teilen das Abteil mit zwei Wanderern.|Kupeda ikki sayohatchi bilan birga ketyapmiz.|die Abteile
der Anschluss|ˈanˌʃlʊs|keyingi ulanish reysi|In Köln haben wir Anschluss nach Bonn.|Kyolnda Bonnga ketadigan keyingi transportga ulguramiz.|die Anschlüsse
der Ausfall|ˈaʊ̯sˌfal|qatnovning bekor bo‘lishi; uzilish|Wegen eines Zugausfalls nehmen wir den Bus.|Poyezd qatnovi bekor bo‘lgani uchun avtobusga chiqamiz.|die Ausfälle
die Verbindung|fɛɐ̯ˈbɪndʊŋ|transport aloqasi|Gibt es eine direkte Verbindung nach Dresden?|Drezdenga to‘g‘ridan to‘g‘ri qatnov bormi?|die Verbindungen
der Umstieg|ˈʊmˌʃtiːk|boshqa transportga o‘tish|Für den Umstieg bleiben uns acht Minuten.|Boshqa transportga o‘tishimiz uchun sakkiz daqiqa qoladi.|die Umstiege
der Sitzplatz|ˈzɪtsˌplats|o‘rindiq|Mein Sitzplatz ist am Fenster.|Mening o‘rindig‘im deraza yonida.|die Sitzplätze
die Buchung|ˈbuːxʊŋ|band qilish|Meine Buchung enthält zwei Übernachtungen.|Band qilgan xizmatim ikki kecha tunashni o‘z ichiga oladi.|die Buchungen
der Schaffner|ˈʃafnɐ|vagon kuzatuvchisi|Der Schaffner hilft mir mit dem Koffer.|Vagon kuzatuvchisi chamadonimni ko‘tarishga yordam beradi.|die Schaffner
die Durchsage|ˈdʊʁçˌzaːɡə|ovozli e’lon|Wegen der lauten Musik höre ich die Durchsage nicht.|Baland musiqa sababli ovozli e’lonni eshitmayapman.|die Durchsagen
der Notausgang|ˈnoːtˌʔaʊ̯sɡaŋ|favqulodda chiqish joyi|Vor dem Notausgang dürfen keine Koffer stehen.|Favqulodda chiqish joyi oldida chamadonlar turmasligi kerak.|die Notausgänge
die Anzeigetafel|ˈantsaɪ̯ɡəˌtaːfl̩|axborot tablosi|Auf der Anzeigetafel steht plötzlich ein anderes Gleis.|Axborot tablosida birdan boshqa yo‘l raqami chiqadi.|die Anzeigetafeln
das Terminal|ˈtɛʁmɪnl̩|aeroport terminali|Ein kostenloser Bus verbindet die beiden Terminals.|Bepul avtobus ikki terminal orasida qatnaydi.|die Terminals
der Flug|fluːk|parvoz|Unser Flug dauert fast sechs Stunden.|Parvozimiz deyarli olti soat davom etadi.|die Flüge
die Fluggesellschaft|ˈfluːkɡəˌzɛlʃaft|aviakompaniya|Diese Fluggesellschaft erlaubt einen kleinen Rucksack.|Bu aviakompaniya kichik ryukzak olib kirishga ruxsat beradi.|die Fluggesellschaften
die Bordkarte|ˈbɔʁtˌkaʁtə|bortga chiqish taloni|Die Bordkarte ist auf meinem Handy.|Bortga chiqish taloni telefonimda.|die Bordkarten
das Handgepäck|ˈhantɡəˌpɛk|qo‘l yuki|Die Kamera bleibt im Handgepäck.|Fotoapparat qo‘l yukida qoladi.|kein Plural
die Gepäckausgabe|ɡəˈpɛkˌʔaʊ̯sɡaːbə|yuk olish joyi|An der Gepäckausgabe warten alle auf ihre Koffer.|Yuk olish joyida hamma chamadonlarini kutyapti.|die Gepäckausgaben
der Kofferraum|ˈkɔfɐˌʁaʊ̯m|mashina yukxonasi|In den Kofferraum passt noch eine Tasche.|Mashina yukxonasiga yana bitta sumka sig‘adi.|die Kofferräume
die Reisetasche|ˈʁaɪ̯zəˌtaʃə|safar sumkasi|Meine Reisetasche ist kleiner als dein Koffer.|Safar sumkam sening chamadoningdan kichikroq.|die Reisetaschen
die Sicherheitskontrolle|ˈzɪçɐhaɪ̯tsˌkɔntʁɔlə|xavfsizlik tekshiruvi|An der Sicherheitskontrolle ziehe ich meine Jacke aus.|Xavfsizlik tekshiruvida kurtkamni yechaman.|die Sicherheitskontrollen
der Reisepass|ˈʁaɪ̯zəˌpas|xorijga chiqish pasporti|Mein Reisepass ist noch drei Jahre gültig.|Xorijga chiqish pasportim yana uch yil amal qiladi.|die Reisepässe
das Visum|ˈviːzʊm|viza|Für diese Reise brauche ich ein Visum.|Bu sayohat uchun menga viza kerak.|die Visa
die Grenze|ˈɡʁɛntsə|chegara|An der Grenze kontrolliert man unsere Pässe.|Chegarada pasportlarimiz tekshiriladi.|die Grenzen
der Zoll|tsɔl|bojxona|Beim Zoll öffnet sie ihren Koffer.|U bojxonada chamadonini ochadi.|kein Plural in dieser Bedeutung
das Reiseziel|ˈʁaɪ̯zəˌtsiːl|sayohat manzili|Unser nächstes Reiseziel ist Samarkand.|Keyingi sayohat manzilimiz Samarqand.|die Reiseziele
die Unterkunft|ˈʊntɐˌkʊnft|turar joy|Wir suchen eine Unterkunft in der Altstadt.|Eski shahardan turar joy qidiryapmiz.|die Unterkünfte
die Jugendherberge|ˈjuːɡn̩tˌhɛʁbɛʁɡə|yoshlar yotoqxonasi|Die Jugendherberge hat eine gemeinsame Küche.|Yoshlar yotoqxonasida umumiy oshxona bor.|die Jugendherbergen
die Pension|pɛnˈzi̯oːn|kichik mehmonxona|Die kleine Pension liegt direkt am See.|Kichik mehmonxona ko‘lning qoq yonida joylashgan.|die Pensionen
die Ferienwohnung|ˈfeːʁi̯ənˌvoːnʊŋ|ta’til uchun ijaradagi uy|Unsere Ferienwohnung hat einen Balkon.|Ta’til uchun ijaraga olgan uyimizning balkoni bor.|die Ferienwohnungen
das Gästezimmer|ˈɡɛstəˌtsɪmɐ|mehmon xonasi|Im Gästezimmer steht ein zusätzliches Bett.|Mehmon xonasida qo‘shimcha karavot bor.|die Gästezimmer
das Mehrbettzimmer|ˈmeːɐ̯bɛtˌtsɪmɐ|ko‘p kishilik xona|Ein Bett im Mehrbettzimmer ist günstiger.|Ko‘p kishilik xonadagi joy arzonroq.|die Mehrbettzimmer
die Lobby|ˈlɔbi|mehmonxona foyesi|Wir warten in der Lobby auf unser Taxi.|Mehmonxona foyesida taksimizni kutamiz.|die Lobbys
der Zimmerschlüssel|ˈtsɪmɐˌʃlʏsl̩|xona kaliti|Der Zimmerschlüssel passt nicht ins Schloss.|Xona kaliti qulfga tushmayapti.|die Zimmerschlüssel
die Übernachtung|yːbɐˈnaxtʊŋ|tunash|Eine Übernachtung mit Frühstück kostet achtzig Euro.|Nonushta bilan bir kecha tunash sakson yevro turadi.|die Übernachtungen
die Halbpension|ˈhalpˌpɛnzi̯oːn|nonushta va kechki ovqatli xizmat|Bei Halbpension ist das Mittagessen nicht dabei.|Nonushta va kechki ovqatli xizmatga tushlik kirmaydi.|kein Plural
die Vollpension|ˈfɔlˌpɛnzi̯oːn|uch mahal ovqatli xizmat|Mit Vollpension essen wir dreimal täglich im Hotel.|Uch mahal ovqatli xizmat bilan mehmonxonada kuniga uch marta ovqatlanamiz.|kein Plural
die Bettwäsche|ˈbɛtˌvɛʃə|choyshab va yostiq jildi|Frische Bettwäsche liegt im Schrank.|Toza choyshab va yostiq jildi shkafda turibdi.|kein Plural
der Bademantel|ˈbaːdəˌmantl̩|cho‘milish xalati|Der Bademantel im Hotel ist mir viel zu groß.|Mehmonxonadagi cho‘milish xalati menga juda katta.|die Bademäntel
die Klimaanlage|ˈkliːmaˌʔanlaːɡə|konditsioner|Die Klimaanlage ist nachts zu laut.|Konditsioner tunda juda shovqinli.|die Klimaanlagen
die Heizung|ˈhaɪ̯tsʊŋ|isitish tizimi|Die Heizung wird erst am Abend warm.|Isitish tizimi faqat kechqurun isiydi.|die Heizungen
die Aussicht|ˈaʊ̯sˌzɪçt|manzara|Vom Balkon genießen wir die Aussicht auf die Berge.|Balkondan tog‘lar manzarasidan zavqlanamiz.|die Aussichten
der Aufenthalt|ˈaʊ̯fʔɛntˌhalt|bir joyda turish muddati|Wir verlängern unseren Aufenthalt um zwei Tage.|Bu yerda turish muddatimizni ikki kunga uzaytiramiz.|die Aufenthalte
die Anzahlung|ˈanˌtsaːlʊŋ|oldindan qisman to‘lov|Bei der Buchung leisten wir eine kleine Anzahlung.|Band qilishda ozgina oldindan to‘lov qilamiz.|die Anzahlungen
verreisen|fɛɐ̯ˈʁaɪ̯zn̩|safarga ketmoq|Im Oktober verreise ich für eine Woche.|Oktabrda bir haftaga safarga ketaman.|
vorauszahlen|foːˈʁaʊ̯sˌtsaːlən|oldindan to‘lamoq|Für die Ferienwohnung müssen wir die Hälfte vorauszahlen.|Ta’til uyining yarim haqini oldindan to‘lashimiz kerak.|
stornieren|ʃtɔʁˈniːʁən|bekor qilmoq|Wegen der Krankheit müssen wir den Flug stornieren.|Kasallik sababli parvozni bekor qilishimiz kerak.|
umbuchen|ˈʊmˌbuːxn̩|band qilingan sana yoki reysni o‘zgartirmoq|Ich möchte meinen Flug auf Montag umbuchen.|Parvozimni dushanbaga o‘zgartirmoqchiman.|
einchecken|ˈaɪ̯nˌtʃɛkn̩|kelishni ro‘yxatdan o‘tkazmoq|Wir checken schon zu Hause online ein.|Biz uydayoq internet orqali parvozga ro‘yxatdan o‘tamiz.|
auschecken|ˈaʊ̯sˌtʃɛkn̩|mehmonxonadan chiqishni rasmiylashtirmoq|Am Sonntag checken wir vor elf Uhr aus.|Yakshanba kuni soat o‘n birdan oldin mehmonxonadan chiqishni rasmiylashtiramiz.|
losfahren|ˈloːsˌfaːʁən|yo‘lga chiqmoq|Wenn alle bereit sind, fahren wir los.|Hamma tayyor bo‘lgach, yo‘lga chiqamiz.|fährt los; fuhr los; ist losgefahren
eintreffen|ˈaɪ̯nˌtʁɛfn̩|yetib kelmoq|Die Reisegruppe trifft am Nachmittag ein.|Sayyohlar guruhi tushdan keyin yetib keladi.|trifft ein; traf ein; ist eingetroffen
weiterfahren|ˈvaɪ̯tɐˌfaːʁən|yo‘lni davom ettirmoq|Nach einer kurzen Pause fahren wir weiter.|Qisqa tanaffusdan keyin yo‘lni davom ettiramiz.|fährt weiter; fuhr weiter; ist weitergefahren
zusteigen|ˈtsuːˌʃtaɪ̯ɡn̩|yo‘ldagi bekatda transportga chiqmoq|In Bremen steigen noch zwanzig Gäste zu.|Bremenda yana yigirma mehmon avtobusga chiqadi.|steigt zu; stieg zu; ist zugestiegen
ausweichen|ˈaʊ̯sˌvaɪ̯çn̩|chetga chiqib yo‘l bermoq; chetlab o‘tmoq|Der Radfahrer weicht einer Pfütze aus.|Velosipedchi ko‘lmakni chetlab o‘tadi.|weicht aus; wich aus; ist ausgewichen
verpassen|fɛɐ̯ˈpasn̩|o‘tkazib yubormoq|Fast verpasse ich den Zug wegen eines Fotos.|Bir surat deb poyezdni sal bo‘lmasa o‘tkazib yuboraman.|
erreichen|ɛɐ̯ˈʁaɪ̯çn̩|yetib bormoq|Zu Fuß erreichen Sie das Hotel in zehn Minuten.|Mehmonxonaga piyoda o‘n daqiqada yetib borasiz.|
landen|ˈlandn̩|qo‘nmoq|Das Flugzeug landet trotz des Regens pünktlich.|Samolyot yomg‘irga qaramay vaqtida qo‘nadi.|
starten|ˈʃtaʁtn̩|uchib ketmoq; boshlamoq|Unser Flugzeug startet mit einer Stunde Verspätung.|Samolyotimiz bir soat kechikib uchib ketadi.|
einpacken|ˈaɪ̯nˌpakn̩|o‘ramoq; yuk ichiga solmoq|Ich packe das zerbrechliche Souvenir in ein Tuch ein.|Mo‘rt esdalik buyumini matoga o‘rayman.|
auspacken|ˈaʊ̯sˌpakn̩|yukni ochib joylashtirmoq|Im Hotel packe ich zuerst die nassen Schuhe aus.|Mehmonxonada avval ho‘l poyabzalimni yukdan chiqaraman.|
transportieren|tʁanspɔʁˈtiːʁən|tashimoq|Der kleine Bus transportiert auch unsere Fahrräder.|Kichik avtobus velosipedlarimizni ham tashiydi.|
zurückkehren|tsuˈʁʏkˌkeːʁən|qaytib kelmoq|Nach einer Woche kehren wir nach Hause zurück.|Bir haftadan keyin uyga qaytamiz.|
campen|ˈkɛmpn̩|chodirda dam olmoq|Im Sommer campen wir gern am See.|Yozda ko‘l bo‘yida chodirda dam olishni yoqtiramiz.|
unterwegs|ʊntɐˈveːks|yo‘lda|Unterwegs machen wir eine kurze Pause.|Yo‘lda qisqa tanaffus qilamiz.|
planmäßig|ˈplaːnˌmɛːsɪç|jadval bo‘yicha|Der Zug verlässt den Bahnhof planmäßig.|Poyezd vokzaldan jadval bo‘yicha jo‘naydi.|
direkt|diˈʁɛkt|to‘g‘ridan to‘g‘ri|Dieser Bus fährt direkt zum Museum.|Bu avtobus to‘g‘ridan to‘g‘ri muzeyga boradi.|
gültig|ˈɡʏltɪç|amal qiladigan|Das Ticket ist bis morgen gültig.|Chipta ertagacha amal qiladi.|
besetzt|bəˈzɛtst|band|Ist der Platz neben Ihnen besetzt?|Yoningizdagi joy bandmi?|
verfügbar|fɛɐ̯ˈfyːkbaːɐ̯|mavjud; foydalanish mumkin|Für Samstag sind noch Zimmer verfügbar.|Shanba uchun hali bo‘sh xonalar bor.|
ausgebucht|ˈaʊ̯sɡəˌbuːxt|barcha joylari band|Während der Messe ist das Hotel ausgebucht.|Ko‘rgazma vaqtida mehmonxonaning barcha xonalari band.|
inklusive|ɪnkluˈziːvə|ichiga kiritilgan|Das Frühstück ist bei diesem Zimmerpreis inklusive.|Bu xona narxiga nonushta ham kiradi.|
geräumig|ɡəˈʁɔɪ̯mɪç|keng; sig‘imli|Das Zimmer ist geräumig genug für unser ganzes Gepäck.|Xona barcha yukimiz uchun yetarlicha keng.|
unbequem|ˈʊnbəkveːm|noqulay|Mit diesem großen Rucksack ist der Sitz unbequem.|Bu katta ryukzak bilan o‘rindiqda o‘tirish noqulay.|
die Rückfahrt|ˈʁʏkˌfaːɐ̯t|qaytish safari|Für die Rückfahrt nehmen wir einen früheren Zug.|Qaytish uchun ertaroq poyezdni tanlaymiz.|die Rückfahrten
die Hinfahrt|ˈhɪnˌfaːɐ̯t|borish safari|Auf der Hinfahrt lesen wir denselben Krimi.|Borishda ikkalamiz bir xil detektiv asarni o‘qiymiz.|die Hinfahrten
der Mietwagen|ˈmiːtˌvaːɡn̩|ijara mashinasi|Unser Mietwagen steht auf Parkplatz zwölf.|Ijara mashinamiz o‘n ikkinchi to‘xtash joyida turibdi.|die Mietwagen
die Tankstelle|ˈtaŋkˌʃtɛlə|yoqilg‘i quyish shoxobchasi|Die nächste Tankstelle ist zwanzig Kilometer entfernt.|Keyingi yoqilg‘i quyish shoxobchasi yigirma kilometr uzoqda.|die Tankstellen
die Autobahn|ˈaʊ̯toˌbaːn|avtomagistral|Auf der Autobahn gibt es heute viel Verkehr.|Bugun avtomagistralda transport ko‘p.|die Autobahnen
die Baustelle|ˈbaʊ̯ˌʃtɛlə|qurilish maydoni|Wegen der Baustelle ist die Straße gesperrt.|Qurilish sababli ko‘cha yopilgan.|die Baustellen
die Umleitung|ˈʊmˌlaɪ̯tʊŋ|aylanma yo‘l|Wegen der Baustelle folgen wir einer Umleitung.|Qurilish tufayli aylanma yo‘ldan yuramiz.|die Umleitungen
die Fähre|ˈfɛːʁə|parom|Die Fähre bringt uns auf die Insel.|Parom bizni orolga olib boradi.|die Fähren
der Hafen|ˈhaːfn̩|bandargoh|Im Hafen liegen viele kleine Boote.|Bandargohda ko‘p kichik qayiq turibdi.|die Häfen
die Kabine|kaˈbiːnə|kayuta; alohida bo‘lma|Unsere Kabine auf dem Schiff hat kein Fenster.|Kemadagi kayutamizning derazasi yo‘q.|die Kabinen
die Altstadt|ˈaltˌʃtat|shaharning eski qismi|Die Altstadt erkunden wir lieber zu Fuß.|Shaharning eski qismini piyoda aylanib ko‘rishni afzal bilamiz.|die Altstädte
die Sehenswürdigkeit|ˈzeːənsˌvʏʁdɪçkaɪ̯t|diqqatga sazovor joy|Diese Brücke ist die bekannteste Sehenswürdigkeit der Stadt.|Bu ko‘prik shaharning eng mashhur diqqatga sazovor joyidir.|die Sehenswürdigkeiten
die Führung|ˈfyːʁʊŋ|gidli ekskursiya|Die Führung durch das Schloss beginnt um elf.|Saroy bo‘ylab gidli ekskursiya soat o‘n birda boshlanadi.|die Führungen
der Reiseführer|ˈʁaɪ̯zəˌfyːʁɐ|sayohat qo‘llanmasi; gid|In meinem Reiseführer fehlt diese schöne Gasse.|Sayohat qo‘llanmamda bu chiroyli tor ko‘cha yo‘q.|die Reiseführer
das Souvenir|zuːvəˈniːɐ̯|esdalik buyumi|Als Souvenir kaufe ich eine kleine Keramikschale.|Esdalik uchun kichik sopol kosa sotib olaman.|die Souvenirs
die Postkarte|ˈpɔstˌkaʁtə|pochta otkritkasi|Meine Postkarte kommt später an als ich.|Otkritkam mendan kechroq yetib boradi.|die Postkarten
besichtigen|bəˈzɪçtɪɡn̩|borib tomosha qilmoq|Morgen besichtigen wir eine alte Burg.|Ertaga qadimiy qal’ani tomosha qilamiz.|
entdecken|ɛntˈdɛkn̩|kashf qilmoq; topmoq|In einer Seitenstraße entdecken wir ein ruhiges Café.|Yon ko‘chada sokin qahvaxona topamiz.|
sich orientieren|zɪç oʁi̯ɛnˈtiːʁən|mo‘ljal olmoq|Mit dem Stadtplan kann ich mich besser orientieren.|Shahar xaritasi bilan yaxshiroq mo‘ljal olaman.|
verlängern|fɛɐ̯ˈlɛŋɐn|uzaytirmoq|Wir verlängern den Urlaub um einen Tag.|Ta’tilni bir kunga uzaytiramiz.|
"""

WEEKS[10] = r"""
die Auskunft|ˈaʊ̯sˌkʊnft|ma’lumot berish; ma’lumot|Bei der Auskunft erfahren wir die Öffnungszeiten.|Ma’lumot bo‘limidan ish vaqtlarini bilib olamiz.|die Auskünfte
die Sprechstunde|ˈʃpʁɛçˌʃtʊndə|qabul vaqti|Die Sprechstunde beginnt erst um neun.|Qabul vaqti faqat soat to‘qqizda boshlanadi.|die Sprechstunden
die Anmeldung|ˈanˌmɛldʊŋ|ro‘yxatdan o‘tish|Für den Kurs ist eine Anmeldung nötig.|Kurs uchun ro‘yxatdan o‘tish zarur.|die Anmeldungen
die Abmeldung|ˈapˌmɛldʊŋ|ro‘yxatdan chiqish|Die Abmeldung vom Kurs ist bis Freitag möglich.|Jumagacha kursdan chiqishni rasmiylashtirish mumkin.|die Abmeldungen
die Bestätigung|bəˈʃtɛːtɪɡʊŋ|tasdiq|Die Bestätigung kommt per E-Mail.|Tasdiq elektron pochta orqali keladi.|die Bestätigungen
die Absage|ˈapˌzaːɡə|bekor qilish xabari; rad javobi|Die Absage kam eine Stunde vor dem Treffen.|Bekor qilish xabari uchrashuvdan bir soat oldin keldi.|die Absagen
die Wartezeit|ˈvaʁtəˌtsaɪ̯t|kutish vaqti|Mit einem Termin ist die Wartezeit kürzer.|Oldindan vaqt olinsa, kutish vaqti qisqaroq bo‘ladi.|die Wartezeiten
das Wartezimmer|ˈvaʁtəˌtsɪmɐ|kutish xonasi|Im Wartezimmer lese ich eine alte Zeitschrift.|Kutish xonasida eski jurnal o‘qiyman.|die Wartezimmer
die Behandlung|bəˈhandlʊŋ|davolash|Nach der Behandlung vereinbaren wir einen Kontrolltermin.|Davolashdan keyin qayta tekshiruv vaqtini belgilaymiz.|die Behandlungen
die Untersuchung|ʊntɐˈzuːxʊŋ|tekshiruv|Die Untersuchung dauert nur zehn Minuten.|Tekshiruv atigi o‘n daqiqa davom etadi.|die Untersuchungen
die Verordnung|fɛɐ̯ˈʔɔʁdnʊŋ|shifokor buyurtmasi; rasmiy ko‘rsatma|Für die Physiotherapie brauche ich eine ärztliche Verordnung.|Fizioterapiya uchun menga shifokor yo‘llanmasi kerak.|die Verordnungen
der Notdienst|ˈnoːtˌdiːnst|navbatchi shoshilinch xizmat|Welche Apotheke hat heute Notdienst?|Bugun qaysi dorixona navbatchilik qiladi?|die Notdienste
die Versicherung|fɛɐ̯ˈzɪçəʁʊŋ|sug‘urta|Meine Versicherung bezahlt die Reparatur.|Ta’mir haqini sug‘urtam to‘laydi.|die Versicherungen
die Krankenkasse|ˈkʁaŋkn̩ˌkasə|tibbiy sug‘urta kassasi|Ich schicke das Formular an meine Krankenkasse.|Blankani tibbiy sug‘urta kassamga yuboraman.|die Krankenkassen
die Versichertenkarte|fɛɐ̯ˈzɪçɐtn̩ˌkaʁtə|tibbiy sug‘urta kartasi|Bitte bringen Sie Ihre Versichertenkarte mit.|Iltimos, tibbiy sug‘urta kartangizni olib keling.|die Versichertenkarten
das Formular|fɔʁmuˈlaːɐ̯|blanka|Auf dem Formular fehlt Ihre Unterschrift.|Blankada imzoingiz yo‘q.|die Formulare
die Unterschrift|ˈʊntɐˌʃʁɪft|imzo|Seine Unterschrift kann niemand lesen.|Uning imzosini hech kim o‘qiy olmaydi.|die Unterschriften
der Antrag|ˈanˌtʁaːk|ariza|Den Antrag können Sie online stellen.|Arizani internet orqali topshirishingiz mumkin.|die Anträge
die Bescheinigung|bəˈʃaɪ̯nɪɡʊŋ|ma’lumotnoma|Für den Arbeitgeber brauche ich eine Bescheinigung.|Ish beruvchiga taqdim etish uchun ma’lumotnoma kerak.|die Bescheinigungen
der Aufenthaltstitel|ˈaʊ̯fʔɛnthaltstiːtl̩|yashash huquqini tasdiqlovchi hujjat|Meinen Aufenthaltstitel bewahre ich sicher auf.|Yashash huquqini tasdiqlovchi hujjatimni xavfsiz saqlayman.|die Aufenthaltstitel
die Behörde|bəˈhøːɐ̯də|davlat idorasi|Diese Behörde ist nur vormittags geöffnet.|Bu davlat idorasi faqat tushgacha ochiq.|die Behörden
das Bürgeramt|ˈbʏʁɡɐˌʔamt|fuqarolarga xizmat ko‘rsatish idorasi|Beim Bürgeramt melden wir unsere neue Adresse an.|Fuqarolarga xizmat ko‘rsatish idorasida yangi manzilimizni ro‘yxatdan o‘tkazamiz.|die Bürgerämter
der Schalter|ˈʃaltɐ|xizmat darchasi|Am dritten Schalter bekommen Sie die Unterlagen.|Hujjatlarni uchinchi darchadan olasiz.|die Schalter
die Gebühr|ɡəˈbyːɐ̯|xizmat haqi|Für eine neue Karte zahlen Sie eine Gebühr.|Yangi karta uchun xizmat haqi to‘laysiz.|die Gebühren
die Frist|fʁɪst|oxirgi muddat|Die Frist endet am letzten Tag des Monats.|Oxirgi muddat oyning oxirgi kuni tugaydi.|die Fristen
die Öffnungszeit|ˈœfnʊŋsˌtsaɪ̯t|ish vaqti|Die Öffnungszeiten stehen an der Glastür.|Ish vaqtlari oynali eshikda yozilgan.|die Öffnungszeiten
die Warteschlange|ˈvaʁtəˌʃlaŋə|navbat|In der Warteschlange lerne ich neue Wörter.|Navbatda yangi so‘zlarni o‘rganaman.|die Warteschlangen
die Nummernanzeige|ˈnʊmɐnˌʔantsaɪ̯ɡə|navbat raqami ekrani|Auf der Nummernanzeige erscheint endlich meine Nummer.|Navbat ekranida nihoyat mening raqamim chiqadi.|die Nummernanzeigen
die Postfiliale|ˈpɔstfili̯aːlə|pochta bo‘limi|Die Postfiliale schließt heute früher.|Pochta bo‘limi bugun ertaroq yopiladi.|die Postfilialen
das Paket|paˈkeːt|pochta jo‘natmasi|Das Paket ist schwerer als erwartet.|Jo‘natma kutilganidan og‘irroq.|die Pakete
das Päckchen|ˈpɛkçən|kichik pochta jo‘natmasi|In dem Päckchen steckt ein Schal.|Kichik pochta jo‘natmasida sharf bor.|die Päckchen
der Briefumschlag|ˈbʁiːfʔʊmˌʃlaːk|konvert|Die Adresse passt kaum auf den Briefumschlag.|Manzil konvertga zo‘rg‘a sig‘adi.|die Briefumschläge
die Sendung|ˈzɛndʊŋ|pochta jo‘natmasi; eshittirish|Den Weg meiner Sendung verfolge ich online.|Jo‘natmamning yo‘lini internet orqali kuzataman.|die Sendungen
das Porto|ˈpɔʁto|pochta jo‘natish haqi|Wie hoch ist das Porto nach Usbekistan?|O‘zbekistonga jo‘natish haqi qancha?|kein Plural
der Empfänger|ɛmˈpfɛŋɐ|qabul qiluvchi|Der Empfänger wohnt nicht mehr hier.|Qabul qiluvchi endi bu yerda yashamaydi.|die Empfänger
der Absender|ˈapˌzɛndɐ|jo‘natuvchi|Auf dem Brief fehlt der Absender.|Xatda jo‘natuvchi ko‘rsatilmagan.|die Absender
die Lieferung|ˈliːfəʁʊŋ|yetkazib berish|Die Lieferung kommt zwischen acht und zwölf.|Buyurtma sakkizdan o‘n ikkigacha yetkaziladi.|die Lieferungen
der Kundendienst|ˈkʊndn̩ˌdiːnst|mijozlarga xizmat bo‘limi|Der Kundendienst antwortet auch am Samstag.|Mijozlarga xizmat bo‘limi shanba kuni ham javob beradi.|die Kundendienste
die Reparatur|ʁepaʁaˈtuːɐ̯|ta’mir|Die Reparatur kostet mehr als ein neues Gerät.|Ta’mir yangi uskunadan ham qimmatga tushadi.|die Reparaturen
die Werkstatt|ˈvɛʁkˌʃtat|ustaxona|Mein Fahrrad steht noch in der Werkstatt.|Velosipedim hali ustaxonada.|die Werkstätten
der Friseursalon|fʁiˈzøːɐ̯zaˌlɔŋ|sartaroshxona|Der Friseursalon nimmt auch Kunden ohne Termin an.|Sartaroshxona oldindan yozilmagan mijozlarni ham qabul qiladi.|die Friseursalons
die Reinigung|ˈʁaɪ̯nɪɡʊŋ|kimyoviy tozalash xizmati|Ich bringe meinen Mantel in die Reinigung.|Paltomni kimyoviy tozalashga topshiraman.|die Reinigungen
der Waschsalon|ˈvaʃzaˌlɔŋ|kir yuvish shoxobchasi|Im Waschsalon fehlt mir eine Münze.|Kir yuvish shoxobchasida bitta tanga yetmayapti.|die Waschsalons
die Quittung|ˈkvɪtʊŋ|to‘lov kvitansiyasi|Bewahren Sie die Quittung bitte auf.|Iltimos, to‘lov kvitansiyasini saqlab qo‘ying.|die Quittungen
die Garantie|ɡaʁanˈtiː|kafolat|Auf den Drucker gibt es zwei Jahre Garantie.|Printerga ikki yil kafolat beriladi.|die Garantien
der Umtausch|ˈʊmˌtaʊ̯ʃ|tovarni almashtirish|Ein Umtausch ist nur mit Kassenbon möglich.|Tovarni faqat kassa cheki bilan almashtirish mumkin.|kein Plural
die Rückgabe|ˈʁʏkˌɡaːbə|qaytarib berish|Die Rückgabe der Bücher ist auch am Automaten möglich.|Kitoblarni avtomat orqali ham qaytarish mumkin.|die Rückgaben
die Beschwerde|bəˈʃveːɐ̯də|shikoyat|Meine Beschwerde betrifft die lange Wartezeit.|Shikoyatim uzoq kutish vaqti haqida.|die Beschwerden
die Beratung|bəˈʁaːtʊŋ|maslahat xizmati|Die erste Beratung ist kostenlos.|Birinchi maslahat bepul.|die Beratungen
der Kostenvoranschlag|ˈkɔstn̩foːɐ̯ʔanˌʃlaːk|dastlabki xarajat hisob-kitobi|Vor der Reparatur möchte ich einen Kostenvoranschlag.|Ta’mirdan oldin dastlabki xarajat hisob-kitobini olishni istayman.|die Kostenvoranschläge
vereinbaren|fɛɐ̯ˈʔaɪ̯nbaːʁən|kelishib belgilamoq|Wir vereinbaren einen Termin für Donnerstag.|Payshanbaga uchrashuv belgilaymiz.|
verschieben|fɛɐ̯ˈʃiːbn̩|boshqa vaqtga ko‘chirmoq|Können wir den Termin auf morgen verschieben?|Uchrashuvni ertaga ko‘chirsak bo‘ladimi?|verschiebt; verschob; hat verschoben
absagen|ˈapˌzaːɡn̩|bekor qilmoq|Leider muss ich unseren Termin absagen.|Afsuski, uchrashuvimizni bekor qilishim kerak.|
bestätigen|bəˈʃtɛːtɪɡn̩|tasdiqlamoq|Bitte bestätigen Sie den Termin schriftlich.|Iltimos, uchrashuv vaqtini yozma tasdiqlang.|
anmelden|ˈanˌmɛldn̩|ro‘yxatdan o‘tkazmoq|Ich melde mich für den Abendkurs an.|Kechki kursga yozilaman.|
abmelden|ˈapˌmɛldn̩|ro‘yxatdan chiqarmoq|Nach dem Umzug melde ich mein altes Auto ab.|Ko‘chganimdan keyin eski mashinamni ro‘yxatdan chiqaraman.|
ausfüllen|ˈaʊ̯sˌfʏlən|to‘ldirmoq|Füllen Sie das Formular bitte leserlich aus.|Iltimos, blankani o‘qishga qulay qilib to‘ldiring.|
unterschreiben|ʊntɐˈʃʁaɪ̯bn̩|imzo qo‘ymoq|Lesen Sie alles, bevor Sie unterschreiben.|Imzo qo‘yishdan oldin hammasini o‘qing.|unterschreibt; unterschrieb; hat unterschrieben
beantragen|bəˈʔantʁaːɡn̩|ariza bilan so‘ramoq|Sie beantragt einen neuen Reisepass.|U yangi xorijga chiqish pasporti uchun ariza beradi.|
einreichen|ˈaɪ̯nˌʁaɪ̯çn̩|topshirmoq|Sie müssen die Unterlagen bis Freitag einreichen.|Hujjatlarni jumagacha topshirishingiz kerak.|
entgegennehmen|ɛntˈɡeːɡənˌneːmən|qabul qilib olmoq|Kannst du morgen mein Paket entgegennehmen?|Ertaga jo‘natmamni qabul qilib ola olasanmi?|nimmt entgegen; nahm entgegen; hat entgegengenommen
abgeben|ˈapˌɡeːbn̩|topshirmoq; berib qo‘ymoq|Geben Sie den Schlüssel an der Rezeption ab.|Kalitni qabulxonaga topshiring.|gibt ab; gab ab; hat abgegeben
vorlegen|ˈfoːɐ̯ˌleːɡn̩|taqdim etmoq|Am Schalter lege ich meinen Ausweis vor.|Darchada shaxsni tasdiqlovchi hujjatimni taqdim etaman.|
nachreichen|ˈnaːxˌʁaɪ̯çn̩|keyinroq qo‘shimcha topshirmoq|Das fehlende Foto kann ich morgen nachreichen.|Yetishmayotgan suratni ertaga topshirsam bo‘ladi.|
bearbeiten|bəˈʔaʁbaɪ̯tn̩|ko‘rib chiqmoq; ishlov bermoq|Die Behörde bearbeitet meinen Antrag.|Davlat idorasi arizamni ko‘rib chiqyapti.|
erledigen|ɛɐ̯ˈleːdɪɡn̩|bajarib bitirmoq|Heute erledige ich alle wichtigen Termine.|Bugun barcha muhim uchrashuv va ishlarimni bitiraman.|
beraten|bəˈʁaːtn̩|maslahat bermoq|Eine Mitarbeiterin berät mich zur Versicherung.|Bir xodima menga sug‘urta bo‘yicha maslahat beradi.|berät; beriet; hat beraten
reparieren|ʁepaˈʁiːʁən|ta’mirlamoq|Kann man diese Uhr noch reparieren?|Bu soatni hali ta’mirlasa bo‘ladimi?|
erstatten|ɛɐ̯ˈʃtatn̩|xarajat yoki pulni qaytarmoq|Der Händler erstattet mir den vollen Kaufpreis.|Sotuvchi xarid pulini menga to‘liq qaytaradi.|
widerrufen|viːdɐˈʁuːfn̩|bekor qilishini bildirmoq|Ich möchte meine Bestellung schriftlich widerrufen.|Buyurtmamni yozma ravishda bekor qilmoqchiman.|widerruft; widerrief; hat widerrufen
reklamieren|ʁeklaˈmiːʁən|nuqson yuzasidan e’tiroz bildirmoq|Wir reklamieren den beschädigten Tisch.|Shikastlangan stol yuzasidan e’tiroz bildiramiz.|
sich beschweren|zɪç bəˈʃveːʁən|shikoyat qilmoq|Ich beschwere mich über die kalte Dusche.|Sovuq dush haqida shikoyat qilaman.|
überweisen|yːbɐˈvaɪ̯zn̩|pul o‘tkazmoq|Ich überweise die Gebühr noch heute.|Xizmat haqini bugunoq o‘tkazaman.|überweist; überwies; hat überwiesen
einzahlen|ˈaɪ̯nˌtsaːlən|hisobga pul qo‘ymoq|Am Automaten zahle ich Bargeld ein.|Avtomatda hisobimga naqd pul qo‘yaman.|
abheben|ˈapˌheːbn̩|hisobdan naqd pul olmoq|Ich hebe nur fünfzig Euro ab.|Men faqat ellik yevro naqd pul olaman.|hebt ab; hob ab; hat abgehoben
versenden|fɛɐ̯ˈzɛndn̩|jo‘natmoq|Der Laden versendet die Ware am Montag.|Do‘kon tovarni dushanba kuni jo‘natadi.|versendet; versandte; hat versandt
zustellen|ˈtsuːˌʃtɛlən|yetkazib bermoq|Der Bote stellt das Paket am Nachmittag zu.|Kuryer jo‘natmani tushdan keyin yetkazadi.|
wiegen|ˈviːɡn̩|vaznini o‘lchamoq; vaznga ega bo‘lmoq|Die Mitarbeiterin wiegt mein Paket.|Xodima jo‘natmamning vaznini o‘lchaydi.|wiegt; wog; hat gewogen
frankieren|fʁaŋˈkiːʁən|pochta haqini markalamoq|Ich frankiere den Brief am Automaten.|Xatning pochta haqini avtomatda markalayman.|
aufbewahren|ˈaʊ̯fbəˌvaːʁən|saqlab qo‘ymoq|Ich bewahre alle Quittungen in einer Mappe auf.|Barcha kvitansiyalarni bitta jildda saqlayman.|
dringend|ˈdʁɪŋənt|shoshilinch|Ich brauche dringend einen neuen Termin.|Menga zudlik bilan yangi qabul vaqti kerak.|
zuständig|ˈtsuːˌʃtɛndɪç|mas’ul; vakolatli|Welche Abteilung ist für meinen Antrag zuständig?|Arizamga qaysi bo‘lim mas’ul?|
persönlich|pɛʁˈzøːnlɪç|shaxsan; shaxsiy|Sie müssen den Ausweis persönlich abholen.|Hujjatni shaxsan olib ketishingiz kerak.|
schriftlich|ˈʃʁɪftlɪç|yozma|Bitte schicken Sie uns Ihre Frage schriftlich.|Iltimos, savolingizni bizga yozma yuboring.|
mündlich|ˈmʏntlɪç|og‘zaki|Die Mitarbeiterin erklärt mir die Regeln mündlich.|Xodima qoidalarni menga og‘zaki tushuntiradi.|
erforderlich|ɛɐ̯ˈfɔʁdɐlɪç|talab qilinadigan; zarur|Für diesen Antrag ist ein Foto erforderlich.|Bu ariza uchun surat talab qilinadi.|
vollständig|ˈfɔlˌʃtɛndɪç|to‘liq|Sind meine Unterlagen jetzt vollständig?|Hujjatlarim endi to‘liqmi?|
unleserlich|ˈʊnˌleːzɐlɪç|o‘qib bo‘lmaydigan|Die Adresse auf dem Paket ist unleserlich.|Jo‘natmadagi manzilni o‘qib bo‘lmaydi.|
rechtzeitig|ˈʁɛçtˌtsaɪ̯tɪç|o‘z vaqtida; ulgurib|Reichen Sie den Antrag rechtzeitig ein.|Arizani o‘z vaqtida topshiring.|
beschädigt|bəˈʃɛːdɪçt|shikastlangan|Der Karton ist außen beschädigt.|Quti tashqi tomondan shikastlangan.|
die Bankfiliale|ˈbaŋkfili̯aːlə|bank filiali|Meine Bankfiliale zieht in die Nachbarstraße.|Bank filialim qo‘shni ko‘chaga ko‘chyapti.|die Bankfilialen
das Konto|ˈkɔnto|bank hisobi|Auf meinem Konto fehlt noch die Erstattung.|Hisobimga qaytarilishi kerak bo‘lgan pul hali tushmadi.|die Konten
der Kontostand|ˈkɔntoˌʃtant|hisobdagi qoldiq|Meinen Kontostand prüfe ich einmal pro Woche.|Hisobimdagi qoldiqni haftasiga bir marta tekshiraman.|die Kontostände
die Überweisung|yːbɐˈvaɪ̯zʊŋ|pul o‘tkazmasi|Die Überweisung ist heute angekommen.|Pul o‘tkazmasi bugun kelib tushdi.|die Überweisungen
der Dauerauftrag|ˈdaʊ̯ɐˌʔaʊ̯ftʁaːk|muntazam avtomatik to‘lov topshirig‘i|Für die Miete richte ich einen Dauerauftrag ein.|Ijara haqi uchun muntazam avtomatik to‘lov o‘rnataman.|die Daueraufträge
die Erstattung|ɛɐ̯ˈʃtatʊŋ|pulni qaytarish|Nach der Rückgabe warte ich auf die Erstattung.|Tovarni qaytarganimdan so‘ng pulning qaytarilishini kutaman.|die Erstattungen
der Beleg|bəˈleːk|tasdiqlovchi chek|Den Beleg lege ich zu meinen Unterlagen.|Chekni hujjatlarim yoniga qo‘yaman.|die Belege
die Kopie|koˈpiː|nusxa|Bitte machen Sie eine Kopie von diesem Blatt.|Iltimos, bu varaqdan nusxa oling.|die Kopien
der Stempel|ˈʃtɛmpl̩|muhr|Auf der Bescheinigung fehlt der Stempel.|Ma’lumotnomada muhr yo‘q.|die Stempel
die Vollmacht|ˈfɔlˌmaxt|ishonchnoma|Mit einer Vollmacht holt mein Nachbar das Paket ab.|Qo‘shnim ishonchnoma bilan jo‘natmani olib keladi.|die Vollmachten
"""

WEEKS[11] = r"""
die Ausbildung|ˈaʊ̯sˌbɪldʊŋ|kasbiy ta’lim|Meine Ausbildung dauert drei Jahre.|Kasbiy ta’limim uch yil davom etadi.|die Ausbildungen
das Studium|ˈʃtuːdi̯ʊm|oliy ta’lim|Nach dem Studium möchte sie in Buchara arbeiten.|Oliy ta’limdan keyin u Buxoroda ishlamoqchi.|die Studien
die Hochschule|ˈhoːxˌʃuːlə|oliy o‘quv yurti|Die Hochschule bietet einen neuen Sprachkurs an.|Oliy o‘quv yurti yangi til kursini taklif qilyapti.|die Hochschulen
die Universität|univɛʁziˈtɛːt|universitet|An dieser Universität studieren Menschen aus vielen Ländern.|Bu universitetda ko‘p mamlakatlardan kelgan odamlar o‘qiydi.|die Universitäten
die Berufsschule|bəˈʁuːfsˌʃuːlə|kasb-hunar maktabi|Zweimal pro Woche besucht er die Berufsschule.|U haftasiga ikki marta kasb-hunar maktabiga boradi.|die Berufsschulen
die Volkshochschule|ˈfɔlksˌhoːxʃuːlə|kattalar ta’lim markazi|In der Volkshochschule lernt meine Nachbarin Deutsch.|Qo‘shnim kattalar ta’lim markazida nemis tilini o‘rganadi.|die Volkshochschulen
der Lernstoff|ˈlɛʁnˌʃtɔf|o‘quv materiali|Den Lernstoff teile ich in kleine Portionen ein.|O‘quv materialini kichik qismlarga bo‘laman.|kein Plural
die Unterrichtsstunde|ˈʊntɐʁɪçtsˌʃtʊndə|dars soati|Eine Unterrichtsstunde dauert hier fünfundvierzig Minuten.|Bu yerda bir dars soati qirq besh daqiqa davom etadi.|die Unterrichtsstunden
der Stundenplan|ˈʃtʊndn̩ˌplaːn|dars jadvali|Mein Stundenplan hängt über dem Schreibtisch.|Dars jadvalim yozuv stoli tepasida osilgan.|die Stundenpläne
das Fach|fax|o‘quv fani|Geschichte war früher mein Lieblingsfach.|Ilgari tarix eng sevimli fanim edi.|die Fächer
die Vorlesung|ˈfoːɐ̯ˌleːzʊŋ|ma’ruza darsi|Die Vorlesung beginnt heute eine halbe Stunde später.|Ma’ruza bugun yarim soat kechroq boshlanadi.|die Vorlesungen
das Seminar|zemiˈnaːɐ̯|seminar|Im Seminar diskutieren wir in kleinen Gruppen.|Seminarda kichik guruhlarda muhokama qilamiz.|die Seminare
der Vortrag|ˈfoːɐ̯ˌtʁaːk|ma’ruza; chiqish|Ihr Vortrag über Taschkent dauert zehn Minuten.|Uning Toshkent haqidagi chiqishi o‘n daqiqa davom etadi.|die Vorträge
die Präsentation|pʁɛzɛntaˈtsi̯oːn|taqdimot|Für die Präsentation brauche ich drei Bilder.|Taqdimot uchun menga uchta rasm kerak.|die Präsentationen
die Leistung|ˈlaɪ̯stʊŋ|natija; ko‘rsatkich|Mit ihrer mündlichen Leistung ist sie sehr zufrieden.|U og‘zaki javobidagi natijadan juda mamnun.|die Leistungen
die Abschlussprüfung|ˈapʃlʊsˌpʁyːfʊŋ|yakuniy imtihon|Im Juni schreibe ich meine Abschlussprüfung.|Iyun oyida yakuniy yozma imtihonimni topshiraman.|die Abschlussprüfungen
das Zeugnis|ˈtsɔɪ̯knɪs|baholar hujjati; shahodatnoma|Auf dem Zeugnis stehen meine letzten Noten.|Shahodatnomada oxirgi baholarim yozilgan.|die Zeugnisse
das Zertifikat|tsɛʁtifiˈkaːt|sertifikat|Nach dem Kurs bekomme ich ein Zertifikat.|Kursdan keyin sertifikat olaman.|die Zertifikate
die Note|ˈnoːtə|baho|Über diese gute Note freut sie sich sehr.|U bu yaxshi bahodan juda xursand.|die Noten
das Ergebnis|ɛɐ̯ˈɡeːpnɪs|natija|Das Ergebnis erfahren wir am Freitag.|Natijani juma kuni bilamiz.|die Ergebnisse
der Irrtum|ˈʔɪʁtuːm|yanglishish|Entschuldigung, das war ein Irrtum meinerseits.|Kechirasiz, bu mening yanglishishim bo‘ldi.|die Irrtümer
die Korrektur|kɔʁɛkˈtuːɐ̯|tuzatish; tekshirish|Nach der Korrektur verstehe ich meinen Fehler.|Tuzatishdan keyin xatomni tushunaman.|die Korrekturen
die Herausforderung|hɛˈʁaʊ̯sˌfɔʁdəʁʊŋ|murakkab vazifa; sinov|Ein ganzes Buch auf Deutsch ist noch eine Herausforderung.|Nemischa butun kitobni o‘qish hali men uchun qiyin vazifa.|die Herausforderungen
die Methode|meˈtoːdə|usul|Diese Methode hilft mir beim Lernen neuer Wörter.|Bu usul yangi so‘zlarni o‘rganishimga yordam beradi.|die Methoden
die Vorbereitung|ˈfoːɐ̯bəˌʁaɪ̯tʊŋ|tayyorgarlik|Gute Vorbereitung macht die Prüfung weniger stressig.|Yaxshi tayyorgarlik imtihonni kamroq asabiy qiladi.|die Vorbereitungen
die Lösung|ˈløːzʊŋ|yechim; javob|Zu diesem Rätsel gibt es zwei Lösungen.|Bu topishmoqning ikkita javobi bor.|die Lösungen
die Erklärung|ɛɐ̯ˈklɛːʁʊŋ|tushuntirish|Nach Ihrer Erklärung ist die Regel klar.|Tushuntirishingizdan keyin qoida ravshan bo‘ldi.|die Erklärungen
das Beispiel|ˈbaɪ̯ʃpiːl|misol|Ein lustiges Beispiel hilft mir beim Lernen.|Kulgili misol o‘rganishimga yordam beradi.|die Beispiele
die Regel|ˈʁeːɡl̩|qoida|Diese Regel gilt nicht für alle Verben.|Bu qoida barcha fe’llarga tegishli emas.|die Regeln
die Ausnahme|ˈaʊ̯sˌnaːmə|istisno|Zu fast jeder Regel finde ich eine Ausnahme.|Deyarli har bir qoidadan istisno topaman.|die Ausnahmen
die Grammatik|ɡʁaˈmatɪk|grammatika|Grammatik üben wir heute mit einem Spiel.|Bugun grammatikani o‘yin orqali mashq qilamiz.|die Grammatiken
der Wortschatz|ˈvɔʁtˌʃats|so‘z boyligi|Durch kurze Geschichten wächst mein Wortschatz.|Qisqa hikoyalar orqali so‘z boyligim oshadi.|kein Plural
die Aussprache|ˈaʊ̯sˌʃpʁaːxə|talaffuz|Ich übe die Aussprache vor dem Spiegel.|Talaffuzni ko‘zgu oldida mashq qilaman.|kein Plural in dieser Bedeutung
die Betonung|bəˈtoːnʊŋ|urg‘u|Bei diesem Wort liegt die Betonung am Anfang.|Bu so‘zda urg‘u boshida keladi.|die Betonungen
die Silbe|ˈzɪlbə|bo‘g‘in|Wir klatschen bei jeder Silbe einmal.|Har bir bo‘g‘inda bir marta chapak chalamiz.|die Silben
der Laut|laʊ̯t|tovush|Diesen Laut gibt es in meiner Sprache nicht.|Bu tovush mening tilimda yo‘q.|die Laute
der Satzbau|ˈzatsˌbaʊ̯|gap tuzilishi|Beim Satzbau helfen mir farbige Karten.|Gap tuzilishini o‘rganishda rangli kartochkalar yordam beradi.|kein Plural
der Nebensatz|ˈneːbn̩ˌzats|ergash gap|Im Nebensatz steht das Verb oft am Ende.|Ergash gapda fe’l ko‘pincha oxirida turadi.|die Nebensätze
die Vergangenheit|fɛɐ̯ˈɡaŋənhaɪ̯t|o‘tgan zamon; o‘tmish|Heute erzählen wir in der Vergangenheit.|Bugun o‘tgan zamonda hikoya qilamiz.|kein Plural
die Zukunft|ˈtsuːkʊnft|kelajak|Für die Zukunft hat er viele Pläne.|Uning kelajak uchun ko‘p rejalari bor.|kein Plural im üblichen Gebrauch
die Übersetzung|yːbɐˈzɛtsʊŋ|tarjima|Die Übersetzung klingt auf Usbekisch natürlich.|Tarjima o‘zbekchada tabiiy eshitiladi.|die Übersetzungen
das Nachschlagewerk|ˈnaːxʃlaːɡəˌvɛʁk|ma’lumotnoma kitobi|Dieses Nachschlagewerk erklärt schwierige Begriffe.|Bu ma’lumotnoma kitobi qiyin tushunchalarni izohlaydi.|die Nachschlagewerke
das Lehrbuch|ˈleːɐ̯ˌbuːx|darslik|Unser Lehrbuch hat viele kurze Dialoge.|Darsligimizda ko‘p qisqa suhbatlar bor.|die Lehrbücher
das Arbeitsblatt|ˈaʁbaɪ̯tsˌblat|mashq varag‘i|Auf dem Arbeitsblatt fehlt die zweite Aufgabe.|Mashq varag‘ida ikkinchi topshiriq yo‘q.|die Arbeitsblätter
der Beamer|ˈbiːmɐ|proyektor|Der Beamer zeigt das Bild leider kopfüber.|Proyektor, afsuski, rasmni teskari ko‘rsatyapti.|die Beamer
die Mitschrift|ˈmɪtˌʃʁɪft|dars davomida yozilgan qaydlar|Deine Mitschrift hilft mir nach dem verpassten Unterricht.|Qoldirgan darsimdan keyin sening qaydlaring menga yordam beradi.|die Mitschriften
der Ordner|ˈɔʁdnɐ|hujjatlar jildi|Alle Arbeitsblätter sind im blauen Ordner.|Barcha mashq varaqlari ko‘k jildda.|die Ordner
die Notiz|noˈtiːts|qayd|Meine Notizen sind kurz, aber nützlich.|Qaydlarim qisqa, ammo foydali.|die Notizen
die Zusammenfassung|tsuˈzamənˌfasʊŋ|qisqacha mazmun|Am Ende schreiben wir eine Zusammenfassung.|Oxirida qisqacha mazmunini yozamiz.|die Zusammenfassungen
die Lerngruppe|ˈlɛʁnˌɡʁʊpə|o‘quv guruhi|Unsere Lerngruppe trifft sich in der Bibliothek.|O‘quv guruhimiz kutubxonada uchrashadi.|die Lerngruppen
der Teilnehmer|ˈtaɪ̯lˌneːmɐ|ishtirokchi|Jeder Teilnehmer stellt eine Frage.|Har bir ishtirokchi bitta savol beradi.|die Teilnehmer
die Voraussetzung|ˈfoːʁaʊ̯sˌzɛtsʊŋ|zarur shart|Grundkenntnisse sind eine Voraussetzung für diesen Kurs.|Boshlang‘ich bilim bu kurs uchun zarur shartdir.|die Voraussetzungen
der Dozent|doˈtsɛnt|oliy ta’lim o‘qituvchisi|Der Dozent bringt heute alte Fotos mit.|O‘qituvchi bugun eski suratlarni olib keladi.|die Dozenten
die Anwesenheit|ˈanveːzn̩haɪ̯t|hozir bo‘lish; qatnashish|Die Lehrerin prüft zu Beginn die Anwesenheit.|O‘qituvchi boshida kim qatnashayotganini tekshiradi.|kein Plural
das Stipendium|ʃtiˈpɛndi̯ʊm|stipendiya|Mit dem Stipendium kann sie im Ausland studieren.|Stipendiya bilan u chet elda o‘qiy oladi.|die Stipendien
die Weiterbildung|ˈvaɪ̯tɐˌbɪldʊŋ|malaka oshirish|Die Firma bezahlt meine Weiterbildung.|Firma malaka oshirishim uchun haq to‘laydi.|die Weiterbildungen
der Abschluss|ˈapˌʃlʊs|ta’limni tugatganlik darajasi|Für diese Stelle braucht man einen beruflichen Abschluss.|Bu lavozim uchun kasbiy ta’limni tugatganlik darajasi kerak.|die Abschlüsse
das Semester|zeˈmɛstɐ|semestr|Im nächsten Semester lerne ich zusätzlich Französisch.|Keyingi semestrda qo‘shimcha ravishda fransuz tilini o‘rganaman.|die Semester
die Ausleihe|ˈaʊ̯sˌlaɪ̯ə|vaqtincha foydalanishga berish bo‘limi|An der Ausleihe verlängere ich die Leihfrist.|Kitob berish bo‘limida foydalanish muddatini uzaytiraman.|die Ausleihen
der Lesesaal|ˈleːzəˌzaːl|o‘quv zali|Im Lesesaal darf mein Handy nicht klingeln.|O‘quv zalida telefonim jiringlamasligi kerak.|die Lesesäle
sich einprägen|zɪç ˈaɪ̯nˌpʁɛːɡn̩|xotirasiga singdirmoq|Mit einem lustigen Bild präge ich mir das Wort ein.|Kulgili rasm bilan so‘zni xotiramga singdiraman.|
lösen|ˈløːzn̩|yechmoq; hal qilmoq|Diese Aufgabe lösen wir Schritt für Schritt.|Bu topshiriqni qadamma-qadam yechamiz.|
erläutern|ɛɐ̯ˈlɔɪ̯tɐn|izohlab tushuntirmoq|Die Lehrerin erläutert den Unterschied mit zwei Beispielen.|O‘qituvchi farqni ikkita misol bilan tushuntiradi.|
übersetzen|yːbɐˈzɛtsn̩|tarjima qilmoq|Wir übersetzen den Text ins Usbekische.|Matnni o‘zbek tiliga tarjima qilamiz.|
korrigieren|kɔʁiˈɡiːʁən|tuzatmoq|Bitte korrigiere nur meine wichtigsten Fehler.|Iltimos, faqat eng muhim xatolarimni tuzat.|
markieren|maʁˈkiːʁən|belgilamoq|Ich markiere alle neuen Verben gelb.|Barcha yangi fe’llarni sariq rang bilan belgilayman.|
unterstreichen|ʊntɐˈʃtʁaɪ̯çn̩|tagiga chizmoq|Unterstreichen Sie die richtige Antwort.|To‘g‘ri javobning tagiga chizing.|unterstreicht; unterstrich; hat unterstrichen
notieren|noˈtiːʁən|yozib olmoq|Ich notiere neue Wörter sofort.|Yangi so‘zlarni darhol yozib olaman.|
zusammenfassen|tsuˈzamənˌfasn̩|qisqacha bayon qilmoq|Fasse den Text in drei Sätzen zusammen.|Matn mazmunini uchta gapda bayon qil.|
vergleichen|fɛɐ̯ˈɡlaɪ̯çn̩|solishtirmoq|Wir vergleichen unsere Antworten zu zweit.|Javoblarimizni juft bo‘lib solishtiramiz.|vergleicht; verglich; hat verglichen
zuordnen|ˈtsuːˌʔɔʁdnən|moslashtirmoq|Ordnen Sie die Überschriften den Texten zu.|Sarlavhalarni matnlarga moslashtiring.|
ergänzen|ɛɐ̯ˈɡɛntsn̩|to‘ldirmoq|Ergänzen Sie die fehlenden Endungen.|Yetishmayotgan qo‘shimchalarni yozib to‘ldiring.|
ankreuzen|ˈanˌkʁɔɪ̯tsn̩|xoch belgisi bilan belgilamoq|Kreuzen Sie nur eine Antwort an.|Faqat bitta javobni xoch belgisi bilan belgilang.|
bestehen|bəˈʃteːən|imtihondan o‘tmoq|Mit regelmäßiger Übung bestehe ich die Prüfung.|Muntazam mashq bilan imtihondan o‘taman.|besteht; bestand; hat bestanden
durchfallen|ˈdʊʁçˌfalən|imtihondan yiqilmoq|Er ist durchgefallen und versucht es noch einmal.|U imtihondan yiqildi va yana bir marta urinadi.|fällt durch; fiel durch; ist durchgefallen
teilnehmen|ˈtaɪ̯lˌneːmən|qatnashmoq|Am Samstag nehme ich an einem Sprachworkshop teil.|Shanba kuni til bo‘yicha amaliy mashg‘ulotda qatnashaman.|nimmt teil; nahm teil; hat teilgenommen
sich vorbereiten|zɪç ˈfoːɐ̯bəˌʁaɪ̯tn̩|tayyorlanmoq|Ich bereite mich jeden Tag auf die Prüfung vor.|Har kuni imtihonga tayyorlanaman.|
sich konzentrieren|zɪç kɔntsɛnˈtʁiːʁən|diqqatni jamlamoq|Mit leiser Musik kann ich mich gut konzentrieren.|Past ovozdagi musiqa bilan diqqatimni yaxshi jamlay olaman.|
sich merken|zɪç ˈmɛʁkn̩|eslab qolmoq|Ich merke mir das Wort mit einem Bild.|So‘zni rasm yordamida eslab qolaman.|
nachschlagen|ˈnaːxˌʃlaːɡn̩|lug‘atdan qaramoq|Unbekannte Wörter schlage ich im Wörterbuch nach.|Notanish so‘zlarni lug‘atdan qarayman.|schlägt nach; schlug nach; hat nachgeschlagen
vorlesen|ˈfoːɐ̯ˌleːzn̩|ovoz chiqarib o‘qimoq|Lies bitte den ersten Absatz vor.|Iltimos, birinchi xatboshini ovoz chiqarib o‘qi.|liest vor; las vor; hat vorgelesen
abschreiben|ˈapˌʃʁaɪ̯bn̩|ko‘chirib yozmoq|Ich schreibe das Beispiel von der Tafel ab.|Misolni doskadan ko‘chirib yozaman.|schreibt ab; schrieb ab; hat abgeschrieben
aussprechen|ˈaʊ̯sˌʃpʁɛçn̩|talaffuz qilmoq|Wie spricht man diesen Ortsnamen aus?|Bu joy nomi qanday talaffuz qilinadi?|spricht aus; sprach aus; hat ausgesprochen
auswendig|ˈaʊ̯sˌvɛndɪç|yoddan|Dieses kurze Gedicht kann ich schon auswendig.|Bu qisqa she’rni allaqachon yoddan bilaman.|
selbstständig|ˈzɛlpstˌʃtɛndɪç|mustaqil|Die nächste Aufgabe lösen Sie selbstständig.|Keyingi topshiriqni mustaqil bajarasiz.|
fleißig|ˈflaɪ̯sɪç|tirishqoq|Sie lernt fleißig, macht aber auch Pausen.|U tirishib o‘qiydi, lekin dam ham oladi.|
aufmerksam|ˈaʊ̯fˌmɛʁkzaːm|diqqatli|Die Gruppe hört der Geschichte aufmerksam zu.|Guruh hikoyani diqqat bilan tinglaydi.|
mühelos|ˈmyːəˌloːs|qiynalmasdan|Nach viel Übung liest er den Text mühelos.|Ko‘p mashqdan keyin u matnni qiynalmasdan o‘qiydi.|
verständlich|fɛɐ̯ˈʃtɛntlɪç|tushunarli|Die Erklärung ist kurz und verständlich.|Tushuntirish qisqa va tushunarli.|
unverständlich|ˈʊnfɛɐ̯ʃtɛntlɪç|tushunarsiz|Ohne Beispiel bleibt die Regel unverständlich.|Misolsiz qoida tushunarsiz bo‘lib qoladi.|
ausleihen|ˈaʊ̯sˌlaɪ̯ən|vaqtincha foydalanishga olmoq yoki bermoq|In der Bibliothek leihe ich ein Hörbuch aus.|Kutubxonadan audiokitobni vaqtincha foydalanishga olaman.|leiht aus; lieh aus; hat ausgeliehen
der Lernplan|ˈlɛʁnˌplaːn|o‘qish rejasi|In meinem Lernplan stehen auch freie Abende.|O‘qish rejamda bo‘sh oqshomlar ham bor.|die Lernpläne
das Lernziel|ˈlɛʁnˌtsiːl|o‘quv maqsadi|Mein Lernziel ist ein Gespräch ohne lange Pausen.|O‘quv maqsadim — uzoq tanaffuslarsiz suhbatlashish.|die Lernziele
der Fortschritt|ˈfɔʁtˌʃʁɪt|o‘sish; ilgarilash|Beim Hören merke ich meinen Fortschritt besonders.|Tinglashda o‘sishimni ayniqsa sezaman.|die Fortschritte
das Niveau|niˈvoː|daraja|Dieser Text passt zu unserem Niveau.|Bu matn darajamizga mos.|die Niveaus
die Muttersprache|ˈmʊtɐˌʃpʁaːxə|ona tili|Meine Muttersprache hilft mir beim Vergleichen.|Solishtirishda ona tilim menga yordam beradi.|die Muttersprachen
die Fremdsprache|ˈfʁɛmtˌʃpʁaːxə|chet tili|Eine Fremdsprache öffnet Türen zu neuen Gesprächen.|Chet tili yangi suhbatlarga yo‘l ochadi.|die Fremdsprachen
die Partnerarbeit|ˈpaʁtnɐˌʔaʁbaɪ̯t|juftlikda ishlash|Bei der Partnerarbeit sprechen beide gleich viel.|Juftlikda ishlaganda ikkalasi teng miqdorda gapiradi.|kein Plural
die Gruppenarbeit|ˈɡʁʊpn̩ˌʔaʁbaɪ̯t|guruhda ishlash|Die Gruppenarbeit endet mit einem kleinen Plakat.|Guruhdagi ish kichik plakat tayyorlash bilan tugaydi.|die Gruppenarbeiten
die Wiederholung|viːdɐˈhoːlʊŋ|takrorlash|Eine kurze Wiederholung gehört zu jeder Stunde.|Har bir darsda qisqa takrorlash bo‘ladi.|die Wiederholungen
"""

WEEKS[12] = r"""
der Arbeitsplatz|ˈaʁbaɪ̯tsˌplats|ish joyi|Mein Arbeitsplatz liegt direkt am Fenster.|Ish joyim derazaning qoq yonida.|die Arbeitsplätze
der Arbeitgeber|ˈaʁbaɪ̯tsˌɡeːbɐ|ish beruvchi|Mein Arbeitgeber bezahlt den Deutschkurs.|Ish beruvchim nemis tili kursi haqini to‘laydi.|die Arbeitgeber
der Arbeitnehmer|ˈaʁbaɪ̯tsˌneːmɐ|yollanma xodim|Jeder Arbeitnehmer bekommt eine Kopie des Vertrags.|Har bir xodim shartnoma nusxasini oladi.|die Arbeitnehmer
die Mitarbeiterin|ˈmɪtʔaʁbaɪ̯təʁɪn|xodima|Die neue Mitarbeiterin kennt schon alle Namen.|Yangi xodima allaqachon hammaning ismini biladi.|die Mitarbeiterinnen
die Belegschaft|bəˈleːkʃaft|korxona xodimlari jamoasi|Die ganze Belegschaft kommt zum Sommerfest.|Butun xodimlar jamoasi yozgi bayramga keladi.|die Belegschaften
der Bereich|bəˈʁaɪ̯ç|soha; yo‘nalish|Ich suche eine Stelle im technischen Bereich.|Texnik yo‘nalishda ish qidiryapman.|die Bereiche
die Abteilung|ˈapˌtaɪ̯lʊŋ|bo‘lim|Unsere Abteilung zieht in den zweiten Stock.|Bo‘limimiz ikkinchi yuqori qavatga ko‘chyapti.|die Abteilungen
das Unternehmen|ʊntɐˈneːmən|korxona|Das Unternehmen stellt dieses Jahr neue Leute ein.|Korxona bu yil yangi xodimlarni ishga oladi.|die Unternehmen
der Betrieb|bəˈtʁiːp|ishlab chiqarish yoki xizmat korxonasi|In unserem Betrieb arbeiten vierzig Personen.|Korxonamizda qirq kishi ishlaydi.|die Betriebe
die Branche|ˈbʁaŋʃə|soha; tarmoq|In welcher Branche möchten Sie arbeiten?|Qaysi sohada ishlamoqchisiz?|die Branchen
die Stelle|ˈʃtɛlə|ish o‘rni|Die freie Stelle passt gut zu meiner Erfahrung.|Bo‘sh ish o‘rni tajribamga juda mos.|die Stellen
die Stellenanzeige|ˈʃtɛlənˌʔantsaɪ̯ɡə|ish e’loni|Diese Stellenanzeige nennt leider kein Gehalt.|Bu ish e’lonida, afsuski, maosh ko‘rsatilmagan.|die Stellenanzeigen
die Bewerbung|bəˈvɛʁbʊŋ|ishga kirish uchun ariza|Meine Bewerbung schicke ich heute ab.|Ishga kirish arizamni bugun yuboraman.|die Bewerbungen
der Lebenslauf|ˈleːbn̩sˌlaʊ̯f|tarjimayi hol|Mein Lebenslauf passt auf zwei Seiten.|Tarjimayi holim ikki betga sig‘adi.|die Lebensläufe
das Anschreiben|ˈanˌʃʁaɪ̯bn̩|arizaga ilova xati|Im Anschreiben erkläre ich mein Interesse an der Stelle.|Ilova xatida shu ishga qiziqishimni tushuntiraman.|die Anschreiben
das Vorstellungsgespräch|ˈfoːɐ̯ʃtɛlʊŋsɡəˌʃpʁɛːç|ishga qabul suhbati|Beim Vorstellungsgespräch darf ich auch Fragen stellen.|Ishga qabul suhbatida men ham savol berishim mumkin.|die Vorstellungsgespräche
die Berufserfahrung|bəˈʁuːfsʔɛɐ̯ˌfaːʁʊŋ|kasbiy tajriba|Sie hat fünf Jahre Berufserfahrung im Verkauf.|U savdo sohasida besh yillik tajribaga ega.|kein Plural im üblichen Gebrauch
die Qualifikation|kvalifikaˈtsi̯oːn|malaka|Für diese Tätigkeit fehlt mir noch eine Qualifikation.|Bu faoliyat uchun menga hali bitta malaka yetishmaydi.|die Qualifikationen
die Fähigkeit|ˈfɛːɪçkaɪ̯t|qobiliyat; ko‘nikma|Im Praktikum entdecke ich neue Fähigkeiten.|Amaliyotda yangi qobiliyatlarimni kashf etaman.|die Fähigkeiten
die Stärke|ˈʃtɛʁkə|kuchli jihat|Geduld ist eine meiner Stärken.|Sabr mening kuchli jihatlarimdan biri.|die Stärken
die Schwäche|ˈʃvɛçə|zaif jihat|Über meine Schwächen spreche ich ehrlich.|Zaif jihatlarim haqida rost gapiraman.|die Schwächen
das Praktikum|ˈpʁaktikʊm|amaliyot|Während des Praktikums lerne ich den Alltag im Büro kennen.|Amaliyot vaqtida ofisdagi kundalik ish bilan tanishaman.|die Praktika
der Praktikant|pʁaktiˈkant|amaliyotchi erkak|Der Praktikant begleitet uns zum Kundentermin.|Amaliyotchi mijoz bilan uchrashuvga biz bilan boradi.|die Praktikanten
die Aushilfe|ˈaʊ̯sˌhɪlfə|vaqtinchalik yordamchi xodim|Samstags arbeite ich als Aushilfe in einem Laden.|Shanba kunlari do‘konda vaqtinchalik yordamchi bo‘lib ishlayman.|die Aushilfen
der Arbeitsvertrag|ˈaʁbaɪ̯tsfɛɐ̯ˌtʁaːk|mehnat shartnomasi|Im Arbeitsvertrag stehen meine Arbeitszeiten.|Mehnat shartnomasida ish vaqtlarim yozilgan.|die Arbeitsverträge
die Probezeit|ˈpʁoːbəˌtsaɪ̯t|sinov muddati|Während der Probezeit lerne ich alle Abläufe.|Sinov muddati davomida barcha ish tartiblarini o‘rganaman.|die Probezeiten
die Kündigung|ˈkʏndɪɡʊŋ|shartnomani bekor qilish xabari|Die Kündigung muss schriftlich erfolgen.|Shartnomani bekor qilish xabari yozma bo‘lishi kerak.|die Kündigungen
das Gehalt|ɡəˈhalt|oylik maosh|Mein Gehalt kommt am Monatsende.|Maoshim oy oxirida tushadi.|die Gehälter
der Lohn|loːn|ish haqi|Der Lohn wird nach Stunden berechnet.|Ish haqi soatlar bo‘yicha hisoblanadi.|die Löhne
die Arbeitszeit|ˈaʁbaɪ̯tsˌtsaɪ̯t|ish vaqti|Meine Arbeitszeit beginnt um halb acht.|Ish vaqtim soat yetti yarimda boshlanadi.|die Arbeitszeiten
die Teilzeit|ˈtaɪ̯lˌtsaɪ̯t|to‘liqsiz ish vaqti|Während des Studiums arbeitet sie in Teilzeit.|O‘qish davrida u to‘liqsiz ish vaqtida ishlaydi.|kein Plural
die Vollzeit|ˈfɔlˌtsaɪ̯t|to‘liq ish vaqti|Ab September möchte er wieder in Vollzeit arbeiten.|Sentabrdan u yana to‘liq ish vaqtida ishlamoqchi.|kein Plural
die Schicht|ʃɪçt|smena|Meine Schicht endet um zehn Uhr abends.|Smenam kechki soat o‘nda tugaydi.|die Schichten
die Nachtschicht|ˈnaxtˌʃɪçt|tungi smena|Nach der Nachtschicht brauche ich absolute Ruhe.|Tungi smenadan keyin menga to‘liq tinchlik kerak.|die Nachtschichten
die Überstunde|ˈyːbɐˌʃtʊndə|qo‘shimcha ish soati|Diesen Monat habe ich keine Überstunden gemacht.|Bu oy qo‘shimcha ish soatlari ishlamadim.|die Überstunden
der Feierabend|ˈfaɪ̯ɐˌʔaːbn̩t|ishdan keyingi bo‘sh vaqt|Nach Feierabend lasse ich den Laptop geschlossen.|Ishdan keyin noutbukni ochmayman.|die Feierabende
der Urlaubstag|ˈʔuːɐ̯laʊ̯psˌtaːk|ta’til kuni|Für den Umzug nehme ich einen Urlaubstag.|Ko‘chish uchun bir kun ta’til olaman.|die Urlaubstage
die Krankmeldung|ˈkʁaŋkˌmɛldʊŋ|kasallik haqida ishga xabar|Die Krankmeldung schicke ich gleich am Morgen.|Kasallik haqidagi xabarni ertalaboq yuboraman.|die Krankmeldungen
die Besprechung|bəˈʃpʁɛçʊŋ|ish yig‘ilishi|Unsere Besprechung dauert heute nur zwanzig Minuten.|Bugungi ish yig‘ilishimiz atigi yigirma daqiqa davom etadi.|die Besprechungen
das Protokoll|pʁotoˈkɔl|bayonnoma|Im Protokoll stehen die nächsten Schritte.|Bayonnomada keyingi qadamlar yozilgan.|die Protokolle
die Tagesordnung|ˈtaːɡəsˌʔɔʁdnʊŋ|kun tartibi|Die Tagesordnung hat nur drei Punkte.|Kun tartibida atigi uchta masala bor.|die Tagesordnungen
das Projekt|pʁoˈjɛkt|loyiha|An diesem Projekt arbeiten zwei Abteilungen.|Bu loyiha ustida ikki bo‘lim ishlaydi.|die Projekte
der Auftrag|ˈaʊ̯fˌtʁaːk|buyurtma; topshiriq|Der neue Auftrag muss bis Freitag fertig sein.|Yangi buyurtma jumagacha tayyor bo‘lishi kerak.|die Aufträge
die Kundschaft|ˈkʊntʃaft|mijozlar jamoasi|Unsere Kundschaft kommt aus der ganzen Region.|Mijozlarimiz butun hududdan keladi.|kein Plural
die Dienstleistung|ˈdiːnstˌlaɪ̯stʊŋ|xizmat|Diese Dienstleistung können Sie auch online buchen.|Bu xizmatni internet orqali ham buyurtma qilishingiz mumkin.|die Dienstleistungen
die Verantwortung|fɛɐ̯ˈʔantvɔʁtʊŋ|mas’uliyat|Für diese Aufgabe trage ich die Verantwortung.|Bu vazifa uchun men mas’ulman.|kein Plural im üblichen Gebrauch
die Zusammenarbeit|tsuˈzamənˌʔaʁbaɪ̯t|hamkorlik|Gute Zusammenarbeit spart Zeit und Nerven.|Yaxshi hamkorlik vaqtni ham, asabni ham tejaydi.|kein Plural
das Team|tiːm|jamoa|Unser Team löst Probleme gemeinsam.|Jamoamiz muammolarni birgalikda hal qiladi.|die Teams
die Fragerunde|ˈfʁaːɡəˌʁʊndə|savol-javob qismi|Nach dem Vortrag gibt es eine kurze Fragerunde.|Ma’ruzadan keyin qisqa savol-javob bo‘ladi.|die Fragerunden
die Vertretung|fɛɐ̯ˈtʁeːtʊŋ|vaqtincha o‘rinbosarlik|Während meines Urlaubs übernimmt Ali die Vertretung.|Ta’tilim davomida Ali o‘rnimda ishlaydi.|die Vertretungen
sich bewerben|zɪç bəˈvɛʁbn̩|ishga ariza bermoq|Ich bewerbe mich um eine Stelle im Hotel.|Mehmonxonadagi ish o‘rniga ariza beraman.|bewirbt sich; bewarb sich; hat sich beworben
einstellen|ˈaɪ̯nˌʃtɛlən|ishga olmoq|Die Firma stellt zwei Techniker ein.|Firma ikki texnikni ishga olyapti.|
kündigen|ˈkʏndɪɡn̩|mehnat shartnomasini bekor qilmoq|Sie kündigt, weil sie in eine andere Stadt zieht.|U boshqa shaharga ko‘chayotgani uchun ishdan bo‘shaydi.|
verdienen|fɛɐ̯ˈdiːnən|pul ishlab topmoq|Im neuen Job verdiene ich etwas mehr.|Yangi ishimda biroz ko‘proq pul topaman.|
übernehmen|yːbɐˈneːmən|zimmasiga olmoq|Ich übernehme heute den Empfang.|Bugun qabulxonadagi ishni zimmamga olaman.|übernimmt; übernahm; hat übernommen
erstellen|ɛɐ̯ˈʃtɛlən|tuzmoq; yaratmoq|Für die Besprechung erstelle ich eine Liste.|Yig‘ilish uchun ro‘yxat tuzaman.|
koordinieren|koʔɔʁdiˈniːʁən|muvofiqlashtirmoq|Ich koordiniere die Termine für unser Team.|Jamoamizning uchrashuv vaqtlarini muvofiqlashtiraman.|
organisieren|ɔʁɡaniˈziːʁən|tashkil qilmoq|Meine Kollegin organisiert die Schulung.|Hamkasbim o‘quv mashg‘ulotini tashkil qiladi.|
besprechen|bəˈʃpʁɛçn̩|muhokama qilmoq|Wir besprechen das Angebot nach der Pause.|Taklifni tanaffusdan keyin muhokama qilamiz.|bespricht; besprach; hat besprochen
berichten|bəˈʁɪçtn̩|xabar bermoq; hisobot bermoq|Am Montag berichte ich über meinen Besuch beim Kunden.|Dushanba kuni mijoz huzuridagi tashrifim haqida aytib beraman.|
vertreten|fɛɐ̯ˈtʁeːtn̩|o‘rnida ishlamoq; vakillik qilmoq|Morgen vertrete ich meine Kollegin am Empfang.|Ertaga qabulxonada hamkasbim o‘rnida ishlayman.|vertritt; vertrat; hat vertreten
zusammenarbeiten|tsuˈzamənˌʔaʁbaɪ̯tn̩|birga ishlamoq|Wir arbeiten eng mit der Werkstatt zusammen.|Ustaxona bilan yaqindan hamkorlik qilamiz.|
prüfen|ˈpʁyːfn̩|tekshirmoq|Vor dem Versand prüfe ich die Adresse.|Jo‘natishdan oldin manzilni tekshiraman.|
erwarten|ɛɐ̯ˈvaʁtn̩|kutmoq; umid qilmoq|Der Kunde erwartet eine Antwort bis morgen.|Mijoz ertagacha javob kutyapti.|
anbieten|ˈanˌbiːtn̩|taklif qilmoq|Die Firma bietet flexible Arbeitszeiten an.|Firma moslashuvchan ish vaqtini taklif qiladi.|bietet an; bot an; hat angeboten
ausbilden|ˈaʊ̯sˌbɪldn̩|kasbga o‘rgatmoq|Unser Betrieb bildet junge Elektriker aus.|Korxonamiz yosh elektriklarni kasbga o‘rgatadi.|
einarbeiten|ˈaɪ̯nˌʔaʁbaɪ̯tn̩|ishga moslashtirib o‘rgatmoq|Eine erfahrene Kollegin arbeitet mich ein.|Tajribali hamkasbim menga ishni o‘rgatadi.|
verhandeln|fɛɐ̯ˈhandl̩n|muzokara qilmoq|Wir verhandeln über einen neuen Liefertermin.|Yangi yetkazish sanasi haqida muzokara qilamiz.|
ablehnen|ˈapˌleːnən|rad etmoq|Ich lehne das Angebot höflich ab.|Taklifni muloyimlik bilan rad etaman.|
zusagen|ˈtsuːˌzaːɡn̩|rozilik bildirmoq|Für das Gespräch am Freitag habe ich zugesagt.|Juma kungi suhbatga rozilik bildirdim.|
zuverlässig|ˈtsuːfɛɐ̯ˌlɛsɪç|ishonchli|Eine zuverlässige Kollegin hält ihre Zusagen ein.|Ishonchli hamkasb va’dalarida turadi.|
flexibel|flɛˈksiːbl̩|moslashuvchan|Bei den Arbeitszeiten bin ich flexibel.|Ish vaqtlariga moslasha olaman.|
befristet|bəˈfʁɪstət|muddatli|Mein Vertrag ist auf ein Jahr befristet.|Shartnomam bir yilga tuzilgan.|
unbefristet|ˈʊnbəˌfʁɪstət|muddatsiz|Nach der Probezeit bekomme ich einen unbefristeten Vertrag.|Sinov muddatidan keyin muddatsiz shartnoma olaman.|
berufstätig|bəˈʁuːfsˌtɛːtɪç|ishlaydigan|Viele Teilnehmer sind berufstätig und lernen abends.|Ko‘p ishtirokchilar ishlaydi va kechqurun o‘qiydi.|
arbeitslos|ˈaʁbaɪ̯tsˌloːs|ishsiz|Seit März ist er arbeitslos und sucht eine neue Stelle.|Martdan beri u ishsiz va yangi ish qidiryapti.|
erfahren|ɛɐ̯ˈfaːʁən|tajribali|Bei schwierigen Fragen hilft ein erfahrener Kollege.|Qiyin savollarda tajribali hamkasb yordam beradi.|
geeignet|ɡəˈʔaɪ̯ɡnət|mos; munosib|Diese Stelle ist auch für Anfänger geeignet.|Bu ish o‘rni yangi boshlovchilar uchun ham mos.|
verantwortlich|fɛɐ̯ˈʔantvɔʁtlɪç|mas’ul|Wer ist für die Bestellung verantwortlich?|Buyurtma uchun kim mas’ul?|
beschäftigt|bəˈʃɛftɪçt|band|Ich bin gerade beschäftigt und rufe später zurück.|Hozir bandman, keyinroq qayta qo‘ng‘iroq qilaman.|
die Arbeitskleidung|ˈaʁbaɪ̯tsˌklaɪ̯dʊŋ|ish kiyimi|Saubere Arbeitskleidung liegt im Schrank bereit.|Toza ish kiyimi shkafda tayyor turibdi.|kein Plural
der Schutzhelm|ˈʃʊtsˌhɛlm|himoya kaskasi|Auf der Baustelle tragen alle einen Schutzhelm.|Qurilish maydonida hamma himoya kaskasi kiyadi.|die Schutzhelme
das Werkzeug|ˈvɛʁkˌtsɔɪ̯k|asbob|Nach der Arbeit räumen wir das Werkzeug weg.|Ishdan keyin asboblarni yig‘ishtiramiz.|die Werkzeuge
die Maschine|maˈʃiːnə|mashina; uskuna|Diese Maschine schneidet das Papier genau.|Bu uskuna qog‘ozni aniq kesadi.|die Maschinen
das Lager|ˈlaːɡɐ|ombor|Im Lager fehlt Platz für die neue Lieferung.|Omborda yangi tovar uchun joy yetishmaydi.|die Lager
die Kantine|kanˈtiːnə|korxona oshxonasi|In der Kantine sitzen Kollegen aus allen Abteilungen.|Korxona oshxonasida barcha bo‘limlardan hamkasblar o‘tirishadi.|die Kantinen
der Empfang|ɛmˈpfaŋ|qabul bo‘limi|Am Empfang bekommen Besucher einen Ausweis.|Tashrifchilar qabul bo‘limida kirish kartasini olishadi.|kein Plural in dieser Bedeutung
der Besprechungsraum|bəˈʃpʁɛçʊŋsˌʁaʊ̯m|yig‘ilish xonasi|Der Besprechungsraum ist bis Mittag belegt.|Yig‘ilish xonasi tushgacha band.|die Besprechungsräume
die Dienstreise|ˈdiːnstˌʁaɪ̯zə|xizmat safari|Auf meiner ersten Dienstreise fahre ich nach Leipzig.|Birinchi xizmat safarimda Leypsigga boraman.|die Dienstreisen
die Reisekosten|ˈʁaɪ̯zəˌkɔstn̩|safar xarajatlari|Die Firma übernimmt die Reisekosten.|Safar xarajatlarini firma qoplaydi.|nur Plural
die Personalabteilung|pɛʁzoˈnaːlʔapˌtaɪ̯lʊŋ|kadrlar bo‘limi|Fragen zum Vertrag beantwortet die Personalabteilung.|Shartnomaga oid savollarga kadrlar bo‘limi javob beradi.|die Personalabteilungen
die Bewerbungsfrist|bəˈvɛʁbʊŋsˌfʁɪst|ariza topshirish muddati|Die Bewerbungsfrist endet nächste Woche.|Ariza topshirish muddati keyingi hafta tugaydi.|die Bewerbungsfristen
die Rückmeldung|ˈʁʏkˌmɛldʊŋ|javob; fikr bildirish|Auf meine Bewerbung habe ich noch keine Rückmeldung.|Arizamga hali javob olmadim.|die Rückmeldungen
die Zusage|ˈtsuːˌzaːɡə|ijobiy javob; rozilik|Über die Zusage freue ich mich sehr.|Ijobiy javobdan juda xursandman.|die Zusagen
der Vorgesetzte|ˈfoːɐ̯ɡəˌzɛtstə|rahbar erkak|Mein Vorgesetzter hört sich meinen Vorschlag an.|Rahbarim taklifimni tinglaydi.|die Vorgesetzten; ein Vorgesetzter
der Bewerber|bəˈvɛʁbɐ|ishga da’vogar|Für die Stelle gibt es zehn Bewerber.|Bu ish o‘rniga o‘nta da’vogar bor.|die Bewerber
die Tätigkeit|ˈtɛːtɪçkaɪ̯t|ish faoliyati|Zu meiner Tätigkeit gehört der Kontakt mit Kunden.|Ish faoliyatimga mijozlar bilan aloqa qilish kiradi.|die Tätigkeiten
die Erfahrung|ɛɐ̯ˈfaːʁʊŋ|tajriba|Diese Erfahrung hilft mir bei der nächsten Bewerbung.|Bu tajriba keyingi ish arizamda menga yordam beradi.|die Erfahrungen
die Einarbeitung|ˈaɪ̯nʔaʁbaɪ̯tʊŋ|ishga o‘rgatish davri|Für die Einarbeitung sind zwei Wochen geplant.|Ishga o‘rgatish uchun ikki hafta rejalashtirilgan.|die Einarbeitungen
die Schulung|ˈʃuːlʊŋ|o‘quv mashg‘uloti|Die Schulung findet während der Arbeitszeit statt.|O‘quv mashg‘uloti ish vaqtida o‘tkaziladi.|die Schulungen
"""

WEEKS[13] = r"""
das Gespräch|ɡəˈʃpʁɛːç|suhbat|Unser Gespräch dauert länger als geplant.|Suhbatimiz rejalashtirilganidan uzoqroq davom etadi.|die Gespräche
der Hinweis|ˈhɪnˌvaɪ̯s|ko‘rsatma; eslatma|Danke für den Hinweis auf den falschen Link.|Noto‘g‘ri havolani ko‘rsatganingiz uchun rahmat.|die Hinweise
die Mitteilung|ˈmɪtˌtaɪ̯lʊŋ|bildirish; xabarnoma|Auf der Webseite steht eine wichtige Mitteilung.|Veb-saytda muhim xabarnoma bor.|die Mitteilungen
die Einladung|ˈaɪ̯nˌlaːdʊŋ|taklifnoma|Danke für die Einladung zu deinem Fest.|Bayramingga taklif qilganing uchun rahmat.|die Einladungen
die Anfrage|ˈanˌfʁaːɡə|so‘rov|Ihre Anfrage beantworten wir morgen.|So‘rovingizga ertaga javob beramiz.|die Anfragen
die Stellungnahme|ˈʃtɛlʊŋsˌnaːmə|yozma fikr; munosabat|Zu meiner Beschwerde erhalte ich eine schriftliche Stellungnahme.|Shikoyatimga yozma munosabat olaman.|die Stellungnahmen
die Bitte|ˈbɪtə|iltimos|Ich habe eine kleine Bitte an dich.|Senga kichik iltimosim bor.|die Bitten
der Vorschlag|ˈfoːɐ̯ˌʃlaːk|taklif|Dein Vorschlag spart uns eine lange Fahrt.|Taklifing bizni uzoq yo‘ldan qutqaradi.|die Vorschläge
die Meinung|ˈmaɪ̯nʊŋ|fikr|Zu diesem Film möchte ich deine Meinung hören.|Bu film haqida fikringni eshitmoqchiman.|die Meinungen
das Missverständnis|ˈmɪsfɛɐ̯ˌʃtɛntnɪs|tushunmovchilik|Ein falsches Datum hat das Missverständnis verursacht.|Noto‘g‘ri sana tushunmovchilikka sabab bo‘ldi.|die Missverständnisse
die Entschuldigung|ɛntˈʃʊldɪɡʊŋ|uzr|Sie nimmt meine Entschuldigung an.|U uzrimni qabul qiladi.|die Entschuldigungen
die Anrede|ˈanˌʁeːdə|murojaat shakli|Bei einem offiziellen Brief ist die Anrede wichtig.|Rasmiy xatda murojaat shakli muhim.|die Anreden
die Grußformel|ˈɡʁuːsˌfɔʁml̩|xat yakunidagi salomlashuv iborasi|Am Ende der E-Mail fehlt die Grußformel.|Elektron xat oxirida xayrlashuv iborasi yo‘q.|die Grußformeln
der Betreff|bəˈtʁɛf|xat mavzusi satri|Im Betreff steht nur das Wort Anfrage.|Mavzu satrida faqat «So‘rov» so‘zi yozilgan.|die Betreffe
der Anhang|ˈanˌhaŋ|ilova fayli|Die Rechnung finden Sie im Anhang.|Hisobni ilova faylidan topasiz.|die Anhänge
die E-Mail-Adresse|ˈiːmeːlʔaˌdʁɛsə|elektron pochta manzili|In deiner E-Mail-Adresse fehlt ein Buchstabe.|Elektron pochta manzilingda bitta harf yetishmayapti.|die E-Mail-Adressen
das Postfach|ˈpɔstˌfax|elektron pochta qutisi|Mein Postfach ist fast voll.|Elektron pochta qutim deyarli to‘lgan.|die Postfächer
der Anruf|ˈanˌʁuːf|telefon qo‘ng‘irog‘i|Dein Anruf kam genau in der Pause.|Qo‘ng‘irog‘ing aynan tanaffusga to‘g‘ri keldi.|die Anrufe
der Rückruf|ˈʁʏkˌʁuːf|qayta qo‘ng‘iroq|Ich warte noch auf einen Rückruf der Werkstatt.|Ustaxonadan qayta qo‘ng‘iroq bo‘lishini hali kutyapman.|die Rückrufe
der Anrufbeantworter|ˈanʁuːfbəˌʔantvɔʁtɐ|avtojavob qurilmasi|Auf dem Anrufbeantworter ist eine Nachricht für dich.|Avtojavob qurilmasida sen uchun xabar bor.|die Anrufbeantworter
die Vorwahl|ˈfoːɐ̯ˌvaːl|telefon hudud kodi|Für einen Anruf ins Ausland brauche ich die Vorwahl.|Chet elga qo‘ng‘iroq qilish uchun telefon kodi kerak.|die Vorwahlen
das Festnetz|ˈfɛstˌnɛts|statsionar telefon tarmog‘i|Auf dem Land telefoniere ich oft über das Festnetz.|Qishloqda ko‘pincha statsionar tarmoq orqali qo‘ng‘iroq qilaman.|die Festnetze
der Mobilfunk|moˈbiːlˌfʊŋk|uyali aloqa|In diesem Tal funktioniert der Mobilfunk schlecht.|Bu vodiyda uyali aloqa yomon ishlaydi.|kein Plural
das Netz|nɛts|tarmoq|Im Tunnel habe ich kein Netz.|Tunnelda telefonim tarmoqni tutmaydi.|die Netze
der Bildschirm|ˈbɪltˌʃɪʁm|ekran|Auf dem Bildschirm erscheint eine Fehlermeldung.|Ekranda xato xabari paydo bo‘ladi.|die Bildschirme
die Tastatur|tastaˈtuːɐ̯|klaviatura|Auf dieser Tastatur finde ich das Ü nicht.|Bu klaviaturadan Ü harfini topa olmayapman.|die Tastaturen
die Maus|maʊ̯s|kompyuter sichqonchasi|Meine Maus funktioniert auf diesem Tisch nicht.|Sichqoncham bu stolda ishlamayapti.|die Mäuse
der Drucker|ˈdʁʊkɐ|printer|Der Drucker hat schon wieder kein Papier.|Printerda yana qog‘oz tugabdi.|die Drucker
der Scanner|ˈskɛnɐ|skaner|Mit dem Scanner mache ich eine digitale Kopie.|Skaner yordamida raqamli nusxa olaman.|die Scanner
der Laptop|ˈlɛptɔp|noutbuk|Mein Laptop passt genau in die Tasche.|Noutbukim sumkaga aynan sig‘adi.|die Laptops
das Tablet|ˈtɛblət|planshet|Auf dem Tablet lese ich unterwegs Zeitschriften.|Yo‘lda planshetdan jurnallar o‘qiyman.|die Tablets
das Ladegerät|ˈlaːdəɡəˌʁɛːt|quvvatlagich|Mein Ladegerät liegt noch im Hotel.|Quvvatlagichim hali mehmonxonada qolibdi.|die Ladegeräte
der Akku|ˈʔaku|akkumulyator|Der Akku hält nur noch zwei Stunden.|Akkumulyator quvvati yana atigi ikki soatga yetadi.|die Akkus
die Steckdose|ˈʃtɛkˌdoːzə|rozetka|Unter dem Tisch gibt es eine freie Steckdose.|Stol tagida bo‘sh rozetka bor.|die Steckdosen
das Kabel|ˈkaːbl̩|kabel|Dieses Kabel ist für den Drucker zu kurz.|Bu kabel printer uchun juda qisqa.|die Kabel
der Kopfhörer|ˈkɔpfˌhøːʁɐ|quloqchin|Mit Kopfhörern störe ich niemanden beim Lernen.|Quloqchin bilan o‘qiyotganimda hech kimga xalaqit bermayman.|die Kopfhörer
das Mikrofon|mikʁoˈfoːn|mikrofon|Bitte schalten Sie Ihr Mikrofon wieder ein.|Iltimos, mikrofoningizni yana yoqing.|die Mikrofone
die Datei|daˈtaɪ̯|fayl|Die Datei ist zu groß für eine E-Mail.|Fayl elektron xat uchun juda katta.|die Dateien
das Dokument|dokuˈmɛnt|hujjat|Speichere das Dokument bitte als PDF.|Iltimos, hujjatni PDF shaklida saqla.|die Dokumente
das Passwort|ˈpasˌvɔʁt|parol|Mein Passwort verrate ich niemandem.|Parolimni hech kimga aytmayman.|die Passwörter
der Benutzername|bəˈnʊtsɐˌnaːmə|foydalanuvchi nomi|Mein Benutzername enthält keine Leerzeichen.|Foydalanuvchi nomimda bo‘sh joylar yo‘q.|die Benutzernamen
das Benutzerkonto|bəˈnʊtsɐˌkɔnto|foydalanuvchi hisobi|Für den Kurs brauche ich ein Benutzerkonto.|Kurs uchun menga foydalanuvchi hisobi kerak.|die Benutzerkonten
die Webseite|ˈvɛpˌzaɪ̯tə|veb-sahifa|Auf dieser Webseite übe ich das Hörverstehen.|Bu veb-sahifada tinglab tushunishni mashq qilaman.|die Webseiten
der Link|lɪŋk|havola|Der Link führt direkt zum Anmeldeformular.|Havola to‘g‘ridan to‘g‘ri ro‘yxatdan o‘tish blankasiga olib boradi.|die Links
die Suchmaschine|ˈzuːxmaˌʃiːnə|qidiruv tizimi|Die Suchmaschine zeigt mir mehrere Wörterbücher.|Qidiruv tizimi menga bir nechta lug‘atni ko‘rsatadi.|die Suchmaschinen
die App|ɛp|ilova|Diese App erinnert mich ans Vokabellernen.|Bu ilova so‘z o‘rganishni eslatadi.|die Apps
das Programm|pʁoˈɡʁam|dastur|Das Programm startet nach dem Update schneller.|Yangilanishdan keyin dastur tezroq ishga tushadi.|die Programme
die Einstellung|ˈaɪ̯nˌʃtɛlʊŋ|sozlama|In den Einstellungen ändere ich die Sprache.|Sozlamalarda tilni o‘zgartiraman.|die Einstellungen
die Fehlermeldung|ˈfeːlɐˌmɛldʊŋ|xato haqidagi xabar|Die Fehlermeldung verschwindet nach dem Neustart.|Qayta ishga tushirgandan keyin xato xabari yo‘qoladi.|die Fehlermeldungen
die Sicherungskopie|ˈzɪçəʁʊŋskoˌpiː|zaxira nusxa|Eine Sicherungskopie liegt auf einem anderen Gerät.|Zaxira nusxa boshqa qurilmada saqlanadi.|die Sicherungskopien
sich unterhalten|zɪç ʊntɐˈhaltn̩|suhbatlashmoq|Wir unterhalten uns über unsere Reisepläne.|Sayohat rejalarimiz haqida suhbatlashamiz.|unterhält sich; unterhielt sich; hat sich unterhalten
nachfragen|ˈnaːxˌfʁaːɡn̩|aniqlashtirib so‘ramoq|Wenn ich etwas nicht verstehe, frage ich nach.|Biror narsani tushunmasam, qayta so‘rayman.|
unterbrechen|ʊntɐˈbʁɛçn̩|gapini bo‘lmoq; to‘xtatmoq|Entschuldigung, darf ich Sie kurz unterbrechen?|Kechirasiz, gapingizni qisqa vaqtga bo‘lsam maylimi?|unterbricht; unterbrach; hat unterbrochen
vorschlagen|ˈfoːɐ̯ˌʃlaːɡn̩|taklif qilmoq|Ich schlage ein Treffen am Samstag vor.|Shanba kuni uchrashishni taklif qilaman.|schlägt vor; schlug vor; hat vorgeschlagen
zustimmen|ˈtsuːˌʃtɪmən|qo‘shilmoq; rozi bo‘lmoq|Bei diesem Punkt stimme ich dir zu.|Bu masalada fikringga qo‘shilaman.|
widersprechen|viːdɐˈʃpʁɛçn̩|qarshi fikr bildirmoq|Ich widerspreche dir, aber ich verstehe deinen Grund.|Fikringga qarshiman, lekin sababingni tushunaman.|widerspricht; widersprach; hat widersprochen
begründen|bəˈɡʁʏndn̩|asoslab bermoq|Bitte begründen Sie Ihre Meinung mit einem Beispiel.|Iltimos, fikringizni misol bilan asoslang.|
mitteilen|ˈmɪtˌtaɪ̯lən|xabar qilmoq|Teilen Sie uns bitte Ihre neue Adresse mit.|Iltimos, yangi manzilingizni bizga xabar qiling.|
weiterleiten|ˈvaɪ̯tɐˌlaɪ̯tn̩|boshqaga yo‘naltirmoq|Ich leite Ihre E-Mail an die richtige Abteilung weiter.|Xatingizni tegishli bo‘limga yo‘naltiraman.|
reagieren|ʁeaˈɡiːʁən|munosabat bildirmoq; javob bermoq|Auf meine erste E-Mail hat niemand reagiert.|Birinchi elektron xatimga hech kim javob bermadi.|
zurückrufen|tsuˈʁʏkˌʁuːfn̩|qayta qo‘ng‘iroq qilmoq|Rufst du mich nach der Besprechung zurück?|Yig‘ilishdan keyin menga qayta qo‘ng‘iroq qilasanmi?|ruft zurück; rief zurück; hat zurückgerufen
auflegen|ˈaʊ̯fˌleːɡn̩|telefon suhbatini tugatmoq|Bitte legen Sie noch nicht auf.|Iltimos, hali go‘shakni qo‘ymang.|
wählen|ˈvɛːlən|tanlamoq; raqam termoq|Ich habe leider die falsche Nummer gewählt.|Afsuski, noto‘g‘ri raqam teribman.|
verbinden|fɛɐ̯ˈbɪndn̩|ulamoq|Können Sie mich mit der Buchhaltung verbinden?|Meni buxgalteriya bilan ulay olasizmi?|verbindet; verband; hat verbunden
speichern|ˈʃpaɪ̯çɐn|saqlamoq|Ich speichere den Text nach jedem Absatz.|Har bir xatboshidan keyin matnni saqlayman.|
löschen|ˈlœʃn̩|o‘chirmoq|Lösch bitte nicht das einzige gute Foto.|Iltimos, yagona yaxshi suratni o‘chirma.|
herunterladen|hɛˈʁʊntɐˌlaːdn̩|yuklab olmoq|Zu Hause lade ich die Hörtexte herunter.|Uyda audio matnlarni yuklab olaman.|lädt herunter; lud herunter; hat heruntergeladen
hochladen|ˈhoːxˌlaːdn̩|internetga yuklamoq|Ich lade meine Hausaufgabe auf die Lernplattform hoch.|Uy vazifamni o‘quv platformasiga yuklayman.|lädt hoch; lud hoch; hat hochgeladen
installieren|ɪnstaˈliːʁən|o‘rnatmoq|Für den Kurs installiere ich eine kostenlose App.|Kurs uchun bepul ilova o‘rnataman.|
aktualisieren|aktualiˈziːʁən|yangilamoq|Bitte aktualisiere deine Kontaktdaten.|Iltimos, aloqa ma’lumotlaringni yangila.|
ausdrucken|ˈaʊ̯sˌdʁʊkn̩|printerdan chiqarmoq|Ich drucke nur die erste Seite aus.|Men faqat birinchi betni printerdan chiqaraman.|
einscannen|ˈaɪ̯nˌskɛnən|skanerdan o‘tkazmoq|Kannst du dieses Zeugnis einscannen?|Bu shahodatnomani skanerdan o‘tkaza olasanmi?|
anklicken|ˈanˌklɪkn̩|sichqoncha bilan bosmoq|Klicken Sie das grüne Feld an.|Yashil maydonni bosing.|
eingeben|ˈaɪ̯nˌɡeːbn̩|kiritmoq|Geben Sie hier Ihre E-Mail-Adresse ein.|Bu yerga elektron pochta manzilingizni kiriting.|gibt ein; gab ein; hat eingegeben
bedienen|bəˈdiːnən|boshqarmoq; xizmat ko‘rsatmoq|Den neuen Drucker kann ich schon allein bedienen.|Yangi printerni endi o‘zim boshqara olaman.|
abbrechen|ˈapˌbʁɛçn̩|to‘xtatib qo‘ymoq; bekor qilmoq|Wegen der schlechten Verbindung brechen wir das Gespräch ab.|Aloqa yomonligi sababli suhbatni to‘xtatamiz.|bricht ab; brach ab; hat abgebrochen
aufladen|ˈaʊ̯fˌlaːdn̩|quvvatlamoq|Im Zug kann ich mein Handy aufladen.|Poyezdda telefonimni quvvatlay olaman.|lädt auf; lud auf; hat aufgeladen
neu starten|ˈnɔɪ̯ ˌʃtaʁtn̩|qayta ishga tushirmoq|Nach der Installation müssen Sie den Computer neu starten.|O‘rnatishdan keyin kompyuterni qayta ishga tushirishingiz kerak.|
kopieren|koˈpiːʁən|nusxa olmoq|Ich kopiere die Adresse in meine Notizen.|Manzilni qaydlarimga nusxalab qo‘yaman.|
einfügen|ˈaɪ̯nˌfyːɡn̩|joylashtirmoq; qo‘shib qo‘ymoq|Füge das Bild bitte unter dem Titel ein.|Iltimos, rasmni sarlavha ostiga joylashtir.|
digital|diɡiˈtaːl|raqamli|Die digitale Fahrkarte ist auf meinem Handy.|Raqamli chipta telefonimda.|
kabellos|ˈkaːbl̩ˌloːs|simsiz|Meine Kopfhörer sind kabellos und sehr leicht.|Quloqchinlarim simsiz va juda yengil.|
online|ˈɔnlaɪ̯n|internet orqali; tarmoqda|Den Termin kann ich online buchen.|Qabul vaqtini internet orqali band qila olaman.|
offline|ˈɔflaɪ̯n|internetsiz; tarmoqdan tashqarida|Die Wörterliste ist auch offline verfügbar.|So‘zlar ro‘yxatidan internetsiz ham foydalanish mumkin.|
erreichbar|ɛɐ̯ˈʁaɪ̯çbaːɐ̯|bog‘lanish mumkin bo‘lgan|Nach sechs bin ich telefonisch erreichbar.|Oltidan keyin men bilan telefon orqali bog‘lanish mumkin.|
höflich|ˈhøːflɪç|odobli; muloyim|Auch eine kurze Antwort kann höflich sein.|Qisqa javob ham muloyim bo‘lishi mumkin.|
unhöflich|ˈʊnˌhøːflɪç|odobsiz; qo‘pol|Lautes Telefonieren im Kino finde ich unhöflich.|Kinoda baland ovozda telefonlashishni odobsizlik deb bilaman.|
deutlich|ˈdɔɪ̯tlɪç|aniq; ravshan|Bitte sprechen Sie etwas deutlicher.|Iltimos, biroz aniqroq gapiring.|
undeutlich|ˈʊnˌdɔɪ̯tlɪç|noaniq|Durch das alte Mikrofon klingt seine Stimme undeutlich.|Eski mikrofon sababli uning ovozi noaniq eshitiladi.|
öffentlich|ˈœfn̩tlɪç|ommaviy; hammaga ochiq|Dieses Profil ist öffentlich sichtbar.|Bu profil hammaga ko‘rinadi.|
privat|pʁiˈvaːt|shaxsiy|Meine private Telefonnummer steht nicht auf der Webseite.|Shaxsiy telefon raqamim veb-saytda ko‘rsatilmagan.|
vertraulich|fɛɐ̯ˈtʁaʊ̯lɪç|maxfiy|Diese Nachricht ist vertraulich.|Bu xabar maxfiy.|
die Sprachnachricht|ˈʃpʁaːxˌnaːxʁɪçt|ovozli xabar|Deine Sprachnachricht höre ich später mit Kopfhörern.|Ovozli xabaringni keyinroq quloqchin bilan eshitaman.|die Sprachnachrichten
die Videokonferenz|ˈviːdeoˌkɔnfeʁɛnts|videoyig‘ilish|In der Videokonferenz ist plötzlich eine Katze zu sehen.|Videoyig‘ilishda to‘satdan mushuk ko‘rinib qoladi.|die Videokonferenzen
der Datenschutz|ˈdaːtn̩ˌʃʊts|shaxsiy ma’lumotlar himoyasi|Bei dieser App ist mir der Datenschutz wichtig.|Bu ilovada men uchun ma’lumotlar himoyasi muhim.|kein Plural
die Benachrichtigung|bəˈnaːxʁɪçtɪɡʊŋ|bildirishnoma|Während des Unterrichts schalte ich Benachrichtigungen aus.|Dars vaqtida bildirishnomalarni o‘chiraman.|die Benachrichtigungen
die Internetverbindung|ˈɪntɐnɛtfɛɐ̯ˌbɪndʊŋ|internet aloqasi|Die Internetverbindung wird am Abend langsamer.|Kechqurun internet aloqasi sekinlashadi.|die Internetverbindungen
die Lautstärke|ˈlaʊ̯tˌʃtɛʁkə|ovoz balandligi|Kannst du die Lautstärke etwas reduzieren?|Ovozini biroz pasaytira olasanmi?|die Lautstärken
der Speicherplatz|ˈʃpaɪ̯çɐˌplats|xotiradagi joy|Für das Video brauche ich mehr Speicherplatz.|Video uchun menga xotirada ko‘proq joy kerak.|kein Plural in dieser Bedeutung
die Fernbedienung|ˈfɛʁnbəˌdiːnʊŋ|masofadan boshqarish pulti|Die Fernbedienung liegt natürlich unter dem Kissen.|Pult, albatta, yostiq tagida yotibdi.|die Fernbedienungen
"""

WEEKS[14] = r"""
die Beziehung|bəˈtsiːʊŋ|munosabat|Eine gute Beziehung braucht Zeit und Vertrauen.|Yaxshi munosabat vaqt va ishonch talab qiladi.|die Beziehungen
die Freundschaft|ˈfʁɔɪ̯ntʃaft|do‘stlik|Unsere Freundschaft hat im Sprachkurs begonnen.|Do‘stligimiz til kursida boshlangan.|die Freundschaften
die Bekanntschaft|bəˈkantʃaft|tanishlik|Auf der Reise habe ich nette Bekanntschaften gemacht.|Sayohatda yoqimli tanishlar orttirdim.|die Bekanntschaften
der Bekannte|bəˈkantə|tanish erkak|Ein Bekannter hat mir diese Wohnung empfohlen.|Bir tanishim menga bu kvartirani tavsiya qilgan.|die Bekannten; ein Bekannter
der Kontakt|kɔnˈtakt|aloqa|Mit alten Freunden halte ich regelmäßig Kontakt.|Eski do‘stlarim bilan muntazam aloqada bo‘laman.|die Kontakte
die Nachbarschaft|ˈnaːxbaːɐ̯ʃaft|qo‘shnichilik; mahalla|In unserer Nachbarschaft helfen wir einander.|Mahallamizda bir-birimizga yordam beramiz.|die Nachbarschaften
der Mitbewohner|ˈmɪtbəˌvoːnɐ|birga yashovchi erkak|Mein Mitbewohner gießt die Pflanzen während meiner Reise.|Safarim davomida birga yashovchi sherigim gullarni sug‘oradi.|die Mitbewohner
die Gemeinschaft|ɡəˈmaɪ̯nʃaft|jamoa; hamjamiyat|In dieser Gemeinschaft fühlt sich niemand ausgeschlossen.|Bu jamoada hech kim o‘zini chetda his qilmaydi.|die Gemeinschaften
die Wohngemeinschaft|ˈvoːnɡəˌmaɪ̯nʃaft|birga ijarada yashaydiganlar uyi|In unserer Wohngemeinschaft gibt es einen Putzplan.|Birga ijarada yashaydigan uyimizda tozalash jadvali bor.|die Wohngemeinschaften
das Zusammenleben|tsuˈzamənˌleːbn̩|birga yashash|Offene Gespräche machen das Zusammenleben leichter.|Ochiq suhbatlar birga yashashni yengillashtiradi.|kein Plural
das Treffen|ˈtʁɛfn̩|uchrashuv|Unser nächstes Treffen findet im Park statt.|Keyingi uchrashuvimiz bog‘da bo‘ladi.|die Treffen
die Verabredung|fɛɐ̯ˈʔapʁeːdʊŋ|kelishilgan uchrashuv|Heute Abend habe ich eine Verabredung mit Freunden.|Bugun kechqurun do‘stlarim bilan uchrashishga kelishganman.|die Verabredungen
der Besuch|bəˈzuːx|tashrif; mehmon|Am Wochenende bekommen wir Besuch aus Berlin.|Dam olish kunlari Berlindan mehmonlarimiz keladi.|die Besuche
der Gastgeber|ˈɡastˌɡeːbɐ|mezbon erkak|Der Gastgeber zeigt uns zuerst den Garten.|Mezbon avval bizga bog‘ni ko‘rsatadi.|die Gastgeber
die Höflichkeit|ˈhøːflɪçkaɪ̯t|xushmuomalalik|Aus Höflichkeit höre ich bis zum Ende zu.|Xushmuomalalik yuzasidan oxirigacha tinglayman.|kein Plural in dieser Bedeutung
der Gast|ɡast|mehmon|Der letzte Gast hilft beim Aufräumen.|Oxirgi mehmon yig‘ishtirishga yordam beradi.|die Gäste
die Überraschung|yːbɐˈʁaʃʊŋ|kutilmagan sovg‘a yoki voqea|Dein Besuch ist eine schöne Überraschung.|Tashrifing yoqimli kutilmagan voqea bo‘ldi.|die Überraschungen
das Geschenk|ɡəˈʃɛŋk|sovg‘a|Dieses Geschenk erinnert mich an unsere Reise.|Bu sovg‘a sayohatimizni eslatadi.|die Geschenke
der Gefallen|ɡəˈfalən|yaxshilik; yordam|Kannst du mir einen kleinen Gefallen tun?|Menga kichik bir yaxshilik qila olasanmi?|die Gefallen
die Unterstützung|ʊntɐˈʃtʏtsʊŋ|ko‘mak|Ohne deine Unterstützung wäre der Umzug schwerer.|Sening ko‘magingsiz ko‘chish qiyinroq bo‘lardi.|die Unterstützungen
das Vertrauen|fɛɐ̯ˈtʁaʊ̯ən|ishonch|Vertrauen entsteht nicht an einem einzigen Tag.|Ishonch bir kundayoq paydo bo‘lmaydi.|kein Plural
der Respekt|ʁeˈspɛkt|hurmat|Auch bei Streit ist Respekt wichtig.|Janjalda ham hurmat muhim.|kein Plural in dieser Bedeutung
der Streit|ʃtʁaɪ̯t|janjal; tortishuv|Der Streit begann wegen eines schmutzigen Tellers.|Janjal bitta kir likopcha sababli boshlandi.|die Streite; meist Singular
der Konflikt|kɔnˈflɪkt|ziddiyat|Wir lösen den Konflikt in einem ruhigen Gespräch.|Ziddiyatni xotirjam suhbat orqali hal qilamiz.|die Konflikte
der Kompromiss|kɔmpʁoˈmɪs|murosa|Unser Kompromiss ist einfach: heute Kino, morgen Museum.|Murosamiz oddiy: bugun kino, ertaga muzey.|die Kompromisse
die Versöhnung|fɛɐ̯ˈzøːnʊŋ|yarashish|Nach der Versöhnung lachen wir über den Streit.|Yarashgandan keyin janjalimiz ustidan kulamiz.|die Versöhnungen
die Trennung|ˈtʁɛnʊŋ|ayriliq; ajralish|Nach der Trennung zieht er in eine kleinere Wohnung.|Ajralishdan keyin u kichikroq uyga ko‘chadi.|die Trennungen
das Gefühl|ɡəˈfyːl|his-tuyg‘u|Dieses Gefühl kann ich schwer beschreiben.|Bu hisni tasvirlashim qiyin.|die Gefühle
die Freude|ˈfʁɔɪ̯də|quvonch|Die Freude über die Zusage ist groß.|Ijobiy javobdan quvonchimiz katta.|die Freuden
die Traurigkeit|ˈtʁaʊ̯ʁɪçkaɪ̯t|g‘amginlik|Ein Spaziergang hilft mir gegen die Traurigkeit.|Sayr qilish g‘amginligimni kamaytiradi.|kein Plural
die Angst|aŋst|qo‘rquv|Vor dem ersten Arbeitstag hatte ich etwas Angst.|Birinchi ish kunidan oldin biroz qo‘rqdim.|die Ängste
die Sorge|ˈzɔʁɡə|tashvish|Ihre größte Sorge ist die Wohnungssuche.|Uning eng katta tashvishi uy qidirish.|die Sorgen
die Wut|vuːt|g‘azab|Aus Wut schreibt er eine Nachricht, schickt sie aber nicht ab.|G‘azab bilan xabar yozadi, lekin yubormaydi.|kein Plural
die Enttäuschung|ɛntˈtɔɪ̯ʃʊŋ|hafsalasi pir bo‘lish|Nach der Absage war die Enttäuschung groß.|Rad javobidan keyin hafsalasi juda pir bo‘ldi.|die Enttäuschungen
die Hoffnung|ˈhɔfnʊŋ|umid|Trotz der Schwierigkeiten verliert sie die Hoffnung nicht.|Qiyinchiliklarga qaramay u umidini yo‘qotmaydi.|die Hoffnungen
die Geduld|ɡəˈdʊlt|sabr|Beim Sprachenlernen brauche ich Geduld mit mir selbst.|Til o‘rganishda o‘zimga nisbatan sabrli bo‘lishim kerak.|kein Plural
der Mut|muːt|jasorat|Für das erste Gespräch brauche ich etwas Mut.|Birinchi suhbat uchun biroz jasorat kerak.|kein Plural
die Neugier|ˈnɔɪ̯ˌɡiːɐ̯|qiziquvchanlik|Aus Neugier besuche ich den Tanzkurs.|Qiziqqanim uchun raqs kursiga boraman.|kein Plural
die Einsamkeit|ˈaɪ̯nzaːmkaɪ̯t|yolg‘izlik|Ein regelmäßiger Treffpunkt hilft gegen Einsamkeit.|Muntazam uchrashadigan joy yolg‘izlikni yengishga yordam beradi.|kein Plural
das Heimweh|ˈhaɪ̯mˌveː|yurtni yoki uyni sog‘inish|Gegen Heimweh höre ich Musik aus meiner Heimat.|Yurtimni sog‘inganimda vatanim musiqasini tinglayman.|kein Plural
der Stress|ʃtʁɛs|ruhiy zo‘riqish|Vor der Reise habe ich viel Stress.|Safar oldidan juda band va asabiyman.|kein Plural
die Stimmung|ˈʃtɪmʊŋ|kayfiyat; muhit|Die Musik verbessert sofort die Stimmung.|Musiqa darhol kayfiyatni ko‘taradi.|die Stimmungen
das Lächeln|ˈlɛçl̩n|tabassum|Ihr Lächeln macht den Raum freundlicher.|Uning tabassumi xonaga iliqlik beradi.|kein Plural
die Träne|ˈtʁɛːnə|ko‘z yoshi|Vor Freude laufen ihr Tränen über das Gesicht.|Quvonchdan yuziga ko‘z yoshlari oqadi.|die Tränen
das Geheimnis|ɡəˈhaɪ̯mnɪs|sir|Dein Geheimnis bleibt bei mir.|Siringni hech kimga aytmayman.|die Geheimnisse
sich verabreden|zɪç fɛɐ̯ˈʔapʁeːdn̩|uchrashishga kelishmoq|Wir verabreden uns für Sonntag im Park.|Yakshanba kuni bog‘da uchrashishga kelishamiz.|
gratulieren|ɡʁatuˈliːʁən|tabriklamoq|Ich gratuliere dir zur bestandenen Prüfung.|Imtihondan o‘tganing bilan tabriklayman.|
kennenlernen|ˈkɛnənˌlɛʁnən|tanishmoq|Im Verein lerne ich neue Menschen kennen.|Klubda yangi odamlar bilan tanishaman.|
begrüßen|bəˈɡʁyːsn̩|salomlashib kutib olmoq|Wir begrüßen den neuen Kollegen gemeinsam.|Yangi hamkasbni birgalikda kutib olamiz.|
sich verabschieden|zɪç fɛɐ̯ˈʔapʃiːdn̩|xayrlashmoq|Am Bahnhof verabschieden wir uns voneinander.|Vokzalda bir-birimiz bilan xayrlashamiz.|
begleiten|bəˈɡlaɪ̯tn̩|hamrohlik qilmoq|Begleitest du mich zum Bürgeramt?|Fuqarolarga xizmat ko‘rsatish idorasiga men bilan borasanmi?|
unterstützen|ʊntɐˈʃtʏtsn̩|qo‘llab-quvvatlamoq|Meine Freunde unterstützen mich bei der Jobsuche.|Do‘stlarim ish qidirishimda meni qo‘llab-quvvatlaydi.|
vertrauen|fɛɐ̯ˈtʁaʊ̯ən|ishonmoq|Ich vertraue dir, deshalb erzähle ich dir alles.|Senga ishonaman, shuning uchun hammasini aytaman.|
versprechen|fɛɐ̯ˈʃpʁɛçn̩|va’da bermoq|Ich verspreche dir, pünktlich zu kommen.|Vaqtida kelishga va’da beraman.|verspricht; versprach; hat versprochen
sich entschuldigen|zɪç ɛntˈʃʊldɪɡn̩|uzr so‘ramoq|Ich entschuldige mich für meine späte Antwort.|Kech javob berganim uchun uzr so‘rayman.|
verzeihen|fɛɐ̯ˈtsaɪ̯ən|kechirmoq|Kannst du mir diesen Fehler verzeihen?|Bu xatoyimni kechira olasanmi?|verzeiht; verzieh; hat verziehen
sich streiten|zɪç ˈʃtʁaɪ̯tn̩|janjallashmoq|Wir streiten uns selten über wichtige Dinge.|Muhim narsalar ustida kamdan kam tortishamiz.|streitet sich; stritt sich; hat sich gestritten
sich versöhnen|zɪç fɛɐ̯ˈzøːnən|yarashmoq|Nach dem Streit versöhnen wir uns schnell.|Janjaldan keyin tez yarashamiz.|
sich trennen|zɪç ˈtʁɛnən|ajralmoq|Nach vielen Gesprächen haben sie sich getrennt.|Ko‘p suhbatlardan keyin ular ajralishdi.|
vermissen|fɛɐ̯ˈmɪsn̩|sog‘inmoq|Im Ausland vermisse ich unsere langen Spaziergänge.|Chet elda uzoq sayrlarimizni sog‘inaman.|
bewundern|bəˈvʊndɐn|qoyil qolmoq|Ich bewundere deine Geduld mit diesem schwierigen Projekt.|Bu qiyin loyihadagi sabringga qoyil qolaman.|
sich ärgern|zɪç ˈʔɛʁɡɐn|jahli chiqmoq|Ich ärgere mich über den verpassten Bus.|Avtobusni o‘tkazib yuborganimdan jahlim chiqyapti.|
sich beruhigen|zɪç bəˈʁuːɪɡn̩|tinchlanmoq|Nach einem kurzen Spaziergang beruhige ich mich.|Qisqa sayrdan keyin tinchlanaman.|
sich sorgen|zɪç ˈzɔʁɡn̩|xavotir olmoq|Sie sorgt sich um ihren Freund im Krankenhaus.|U shifoxonadagi do‘sti uchun xavotir oladi.|
sich sehnen|zɪç ˈzeːnən|qo‘msamoq; intizor bo‘lmoq|Nach der langen Reise sehne ich mich nach meinem Zuhause.|Uzoq sayohatdan keyin uyimni qo‘msayman.|
lächeln|ˈlɛçl̩n|tabassum qilmoq|Die Nachbarin lächelt mir freundlich zu.|Qo‘shni ayol menga iliq tabassum qiladi.|
scherzen|ˈʃɛʁtsn̩|hazillashmoq|Wir scherzen oft über unsere kleinen Sprachfehler.|Kichik til xatolarimiz ustidan tez-tez hazillashamiz.|
weinen|ˈvaɪ̯nən|yig‘lamoq|Am Ende des Films weinen sogar meine Freunde.|Film oxirida hatto do‘stlarim ham yig‘laydi.|
trösten|ˈtʁøːstn̩|ovutmoq; taskin bermoq|Nach der schlechten Nachricht tröstet sie mich.|Yomon xabardan keyin u menga taskin beradi.|
umarmen|ʊmˈʔaʁmən|quchoqlamoq|Zur Begrüßung umarmen sich die beiden Freunde.|Ikki do‘st ko‘rishganda quchoqlashadi.|
zufrieden|tsuˈfʁiːdn̩|mamnun|Mit meinem Fortschritt bin ich zufrieden.|O‘sishimdan mamnunman.|
unzufrieden|ˈʊntsuˌfʁiːdn̩|norozi|Mit dem lauten Zimmer sind wir unzufrieden.|Shovqinli xonadan norozimiz.|
erleichtert|ɛɐ̯ˈlaɪ̯çtɐt|yengil tortgan|Nach dem schwierigen Gespräch bin ich erleichtert.|Qiyin suhbatdan keyin yengil tortdim.|
unglücklich|ˈʊnˌɡlʏklɪç|baxtsiz; xafa|Ohne Kontakt zu anderen wird er unglücklich.|Boshqalar bilan aloqasiz u xafa bo‘lib qoladi.|
bedrückt|bəˈdʁʏkt|dilgir; ko‘ngli siqilgan|Seit der schlechten Nachricht wirkt er bedrückt.|Yomon xabardan beri u dilgir ko‘rinadi.|
fröhlich|ˈfʁøːlɪç|xushchaqchaq|Unsere fröhliche Nachbarin singt beim Putzen.|Xushchaqchaq qo‘shnimiz tozalayotganda qo‘shiq aytadi.|
wütend|ˈvyːtn̩t|g‘azablangan|Über die kaputte Tür ist der Vermieter wütend.|Uy egasi buzilgan eshikdan g‘azablangan.|
enttäuscht|ɛntˈtɔɪ̯ʃt|hafsalasi pir bo‘lgan|Vom abgesagten Konzert bin ich enttäuscht.|Konsert bekor qilinganidan hafsalam pir bo‘ldi.|
überrascht|yːbɐˈʁaʃt|hayron; ajablangan|Über dein gutes Deutsch bin ich überrascht.|Nemis tilini yaxshi bilishingdan hayronman.|
nervös|nɛʁˈvøːs|hayajonlangan; asabiy|Vor einem wichtigen Gespräch bin ich nervös.|Muhim suhbatdan oldin hayajonlanaman.|
aufgeregt|ˈaʊ̯fɡəˌʁeːkt|hayajonda|Vor meiner ersten Flugreise bin ich sehr aufgeregt.|Birinchi parvozim oldidan juda hayajondaman.|
entspannt|ɛntˈʃpant|xotirjam; bo‘shashgan|Nach dem Spaziergang fühle ich mich entspannt.|Sayrdan keyin o‘zimni xotirjam his qilaman.|
einsam|ˈaɪ̯nzaːm|yolg‘iz; yolg‘izlikni his qiladigan|In der neuen Stadt fühle ich mich manchmal einsam.|Yangi shaharda ba’zan o‘zimni yolg‘iz his qilaman.|
stolz|ʃtɔlts|faxrlanadigan|Auf meinen ersten deutschen Brief bin ich stolz.|Birinchi nemischa xatimdan faxrlanaman.|
neugierig|ˈnɔɪ̯ˌɡiːʁɪç|qiziquvchan|Ich bin neugierig auf deine neue Wohnung.|Yangi uyingni ko‘rishga qiziqyapman.|
geduldig|ɡəˈdʊldɪç|sabrli|Unser Lehrer bleibt auch bei vielen Fragen geduldig.|O‘qituvchimiz ko‘p savollarda ham sabrli bo‘lib qoladi.|
ungeduldig|ˈʊnɡəˌdʊldɪç|sabrsiz|Nach einer Stunde Warten werde ich ungeduldig.|Bir soat kutgach, sabrim tugay boshlaydi.|
mutig|ˈmuːtɪç|jasur|Es ist mutig, in einer neuen Sprache zu sprechen.|Yangi tilda gapirish jasorat talab qiladi.|
schüchtern|ˈʃʏçtɐn|uyatchan|In großen Gruppen ist sie oft schüchtern.|Katta guruhlarda u ko‘pincha tortinadi.|
ehrlich|ˈʔeːɐ̯lɪç|rostgo‘y; samimiy|Bitte sei ehrlich: Ist der Text verständlich?|Iltimos, rostini ayt: matn tushunarlimi?|
unehrlich|ˈʊnˌʔeːɐ̯lɪç|rostgo‘y bo‘lmagan|Seine Ausrede klingt unehrlich.|Uning bahonasi samimiy eshitilmayapti.|
hilfsbereit|ˈhɪlfsbəˌʁaɪ̯t|yordamga tayyor|Meine Nachbarn sind freundlich und hilfsbereit.|Qo‘shnilarim samimiy va yordamga tayyor.|
rücksichtsvoll|ˈʁʏkzɪçtsˌfɔl|boshqalarni o‘ylaydigan|Ein rücksichtsvoller Mitbewohner telefoniert nachts leise.|Boshqalarni o‘ylaydigan uy sherigi tunda past ovozda telefonlashadi.|
rücksichtslos|ˈʁʏkzɪçtsˌloːs|boshqalarni o‘ylamaydigan|Lautes Bohren am frühen Sonntagmorgen ist rücksichtslos.|Yakshanba tongida baland parmalash boshqalarni o‘ylamaslikdir.|
großzügig|ˈɡʁoːsˌtsyːɡɪç|saxiy|Sie ist großzügig und teilt gern mit anderen.|U saxiy va boshqalar bilan bo‘lishishni yoqtiradi.|
geizig|ˈɡaɪ̯tsɪç|ziqna|Er ist nicht geizig, er spart gerade für eine Reise.|U ziqna emas, hozir sayohat uchun pul yig‘yapti.|
sympathisch|zʏmˈpaːtɪʃ|yoqimli; dilkash|Deine neue Kollegin wirkt sehr sympathisch.|Yangi hamkasbing juda dilkash ko‘rinadi.|
unsympathisch|ˈʊnzʏmˌpaːtɪʃ|yoqimsiz|Sein ständiges Prahlen finde ich unsympathisch.|Uning doim maqtanishi menga yoqmaydi.|
verständnisvoll|fɛɐ̯ˈʃtɛntnɪsˌfɔl|tushunadigan; hamdard|Meine Chefin reagiert verständnisvoll auf das Problem.|Rahbarim muammoga tushunish bilan yondashadi.|
dankbar|ˈdaŋkbaːɐ̯|minnatdor|Für deine Hilfe bin ich dir sehr dankbar.|Yordaming uchun sendan juda minnatdorman.|
"""

WEEKS[15] = r"""
das Vergnügen|fɛɐ̯ˈɡnyːɡn̩|zavq; ko‘ngilxushlik|Das Tanzen macht mir großes Vergnügen.|Raqsga tushish menga katta zavq beradi.|die Vergnügen
die Beschäftigung|bəˈʃɛftɪɡʊŋ|mashg‘ulot; bandlik|Für Regentage suche ich eine kreative Beschäftigung.|Yomg‘irli kunlar uchun ijodiy mashg‘ulot qidiraman.|die Beschäftigungen
der Verein|fɛɐ̯ˈʔaɪ̯n|uyushma; klub|Unser Verein organisiert jeden Monat einen Ausflug.|Klubimiz har oy sayohat tashkil qiladi.|die Vereine
das Mitglied|ˈmɪtˌɡliːt|a’zo|Neue Mitglieder sind in unserem Chor willkommen.|Xorimizga yangi a’zolarni mamnuniyat bilan qabul qilamiz.|die Mitglieder
der Mitgliedsbeitrag|ˈmɪtɡliːtsbaɪ̯ˌtʁaːk|a’zolik badali|Der Mitgliedsbeitrag wird einmal im Jahr bezahlt.|A’zolik badali yiliga bir marta to‘lanadi.|die Mitgliedsbeiträge
die Veranstaltung|fɛɐ̯ˈʔanʃtaltʊŋ|tadbir|Wegen des Regens findet die Veranstaltung drinnen statt.|Yomg‘ir sababli tadbir ichkarida bo‘ladi.|die Veranstaltungen
das Festival|ˈfɛstivl̩|festival|Beim Festival spielen Bands aus verschiedenen Ländern.|Festivalda turli mamlakatlardan guruhlar chaladi.|die Festivals
das Konzert|kɔnˈtsɛʁt|konsert|Für das Konzert gibt es nur noch Stehplätze.|Konsertga faqat tik turadigan joylar qolgan.|die Konzerte
die Bühne|ˈbyːnə|sahna|Auf der Bühne steht ein einzelner Stuhl.|Sahnada bittagina stul turibdi.|die Bühnen
das Publikum|ˈpuːblikʊm|tomoshabinlar|Das Publikum lacht an der falschen Stelle.|Tomoshabinlar kulish kerak bo‘lmagan joyda kulishadi.|kein Plural im üblichen Gebrauch
der Applaus|aˈplaʊ̯s|qarsak|Nach dem letzten Lied gibt es langen Applaus.|Oxirgi qo‘shiqdan keyin uzoq qarsak yangraydi.|kein Plural
die Eintrittskarte|ˈaɪ̯ntʁɪtsˌkaʁtə|kirish chiptasi|Meine Eintrittskarte habe ich als Geschenk bekommen.|Kirish chiptamni sovg‘a sifatida olganman.|die Eintrittskarten
die Ermäßigung|ɛɐ̯ˈmɛːsɪɡʊŋ|chegirma|Gibt es eine Ermäßigung für Studierende?|Talabalar uchun chegirma bormi?|die Ermäßigungen
die Ausstellung|ˈaʊ̯sˌʃtɛlʊŋ|ko‘rgazma|Die Ausstellung zeigt Fotos aus dem alten Taschkent.|Ko‘rgazmada eski Toshkent suratlari namoyish etiladi.|die Ausstellungen
das Denkmal|ˈdɛŋkˌmaːl|yodgorlik|Vor dem Denkmal treffen wir unsere Stadtführerin.|Yodgorlik oldida shahar gidimiz bilan uchrashamiz.|die Denkmäler
die Galerie|ɡaləˈʁiː|san’at galereyasi|Die kleine Galerie liegt in einem Hinterhof.|Kichik galereya ichki hovlida joylashgan.|die Galerien
das Gemälde|ɡəˈmɛːldə|rangtasvir asari|Auf dem Gemälde sieht man einen leeren Bahnhof.|Rangtasvir asarida bo‘sh vokzal tasvirlangan.|die Gemälde
die Skulptur|skʊlpˈtuːɐ̯|haykal|Die Skulptur im Park sieht wie ein riesiger Löffel aus.|Bog‘dagi haykal ulkan qoshiqqa o‘xshaydi.|die Skulpturen
die Oper|ˈʔoːpɐ|opera|Diese Oper höre ich heute zum ersten Mal.|Bu operani bugun birinchi marta eshityapman.|die Opern
das Theaterstück|teˈʔaːtɐˌʃtʏk|sahna asari|Das Theaterstück dauert mit Pause zwei Stunden.|Sahna asari tanaffus bilan ikki soat davom etadi.|die Theaterstücke
die Vorstellung|ˈfoːɐ̯ˌʃtɛlʊŋ|tomosha; seans|Die nächste Vorstellung beginnt um zwanzig Uhr.|Keyingi tomosha soat yigirmada boshlanadi.|die Vorstellungen
der Schauspieler|ˈʃaʊ̯ʃpiːlɐ|aktyor|Der Schauspieler spielt heute einen vergesslichen König.|Aktyor bugun unutuvchan qirol rolini o‘ynaydi.|die Schauspieler
die Regie|ʁeˈʒiː|rejissyorlik|Bei diesem Film führt eine junge Frau Regie.|Bu filmga yosh ayol rejissyorlik qiladi.|kein Plural in dieser Bedeutung
die Rolle|ˈʁɔlə|rol|Für diese Rolle muss er tanzen lernen.|Bu rol uchun u raqsga tushishni o‘rganishi kerak.|die Rollen
die Komödie|koˈmøːdi̯ə|komediya|Nach einer schweren Woche sehen wir eine Komödie.|Og‘ir haftadan keyin komediya tomosha qilamiz.|die Komödien
der Krimi|ˈkʁɪmi|detektiv asar|In diesem Krimi verdächtige ich sogar den Erzähler.|Bu detektiv asarda hatto hikoyachidan ham shubhalanaman.|die Krimis
der Roman|ʁoˈmaːn|roman|Den Roman lese ich jeden Abend im Zug.|Romanni har oqshom poyezdda o‘qiyman.|die Romane
das Gedicht|ɡəˈdɪçt|she’r|Dieses Gedicht hat nur sechs Zeilen.|Bu she’r atigi olti misradan iborat.|die Gedichte
die Geschichte|ɡəˈʃɪçtə|hikoya; tarix|Er erzählt eine Geschichte über einen verlorenen Koffer.|U yo‘qolgan chamadon haqida hikoya aytib beradi.|die Geschichten
der Autor|ˈʔaʊ̯toːɐ̯|muallif erkak|Nach der Lesung beantwortet der Autor Fragen.|Asar o‘qish uchrashuvidan keyin muallif savollarga javob beradi.|die Autoren
die Literatur|lɪtəʁaˈtuːɐ̯|adabiyot|Im Lesekreis entdecken wir Literatur aus verschiedenen Ländern.|Kitobxonlar davrasida turli mamlakatlar adabiyoti bilan tanishamiz.|die Literaturen
das Kapitel|kaˈpɪtl̩|bob|Nach diesem Kapitel mache ich eine Pause.|Shu bobdan keyin tanaffus qilaman.|die Kapitel
die Handlung|ˈhandlʊŋ|asar voqealari|Die Handlung spielt in einem kleinen Hotel.|Asar voqealari kichik mehmonxonada kechadi.|die Handlungen
der Untertitel|ˈʊntɐˌtiːtl̩|subtitr|Mit deutschen Untertiteln verstehe ich mehr.|Nemischa subtitrlar bilan ko‘proq tushunaman.|die Untertitel
der Dokumentarfilm|dokumɛnˈtaːɐ̯ˌfɪlm|hujjatli film|Der Dokumentarfilm zeigt den Alltag von Bergsteigern.|Hujjatli film alpinistlarning kundalik hayotini ko‘rsatadi.|die Dokumentarfilme
die Folge|ˈfɔlɡə|serial qismi|Nach einer Folge schalten wir wirklich aus.|Bir qismdan keyin rostdan ham o‘chiramiz.|die Folgen
der Chor|koːɐ̯|xor|Unser Chor probt jeden Mittwoch.|Xorimiz har chorshanba mashq qiladi.|die Chöre
das Instrument|ɪnstʁuˈmɛnt|musiqa asbobi|Welches Instrument möchtest du lernen?|Qaysi musiqa asbobini chalishni o‘rganmoqchisan?|die Instrumente
die Gitarre|ɡiˈtaʁə|gitara|Meine Gitarre nehme ich zum Picknick mit.|Piknikka gitaramni olib boraman.|die Gitarren
das Schlagzeug|ˈʃlaːkˌtsɔɪ̯k|zarbli cholg‘ular to‘plami|Schlagzeug übe ich lieber nicht um Mitternacht.|Yarim tunda baraban chalishni mashq qilmaganim ma’qul.|die Schlagzeuge
die Melodie|meloˈdiː|kuy|Die Melodie bleibt mir den ganzen Tag im Kopf.|Kuy kun bo‘yi xayolimdan ketmaydi.|die Melodien
der Rhythmus|ˈʁʏtmʊs|ritm|Bei diesem Rhythmus wippen alle mit den Füßen.|Bu ritmda hamma oyoqlarini qimirlatib turadi.|die Rhythmen
die Probe|ˈpʁoːbə|repetitsiya|Die Probe dauert heute länger als das Konzert.|Bugun repetitsiya konsertdan uzoqroq davom etadi.|die Proben
der Tanzkurs|ˈtantsˌkʊʁs|raqs kursi|Im Tanzkurs lache ich oft über meine eigenen Füße.|Raqs kursida o‘z oyoqlarimdan tez-tez kulaman.|die Tanzkurse
das Brettspiel|ˈbʁɛtˌʃpiːl|stol usti o‘yini|Dieses Brettspiel können sechs Personen spielen.|Bu stol usti o‘yinini olti kishi o‘ynashi mumkin.|die Brettspiele
das Rätsel|ˈʁɛːtsl̩|topishmoq; boshqotirma|Das Rätsel lösen wir erst beim zweiten Versuch.|Boshqotirmani faqat ikkinchi urinishda yechamiz.|die Rätsel
das Schach|ʃax|shaxmat|Beim Schach denke ich länger als mein Gegner.|Shaxmatda raqibimdan ko‘proq vaqt o‘ylayman.|kein Plural
der Ausflug|ˈaʊ̯sˌfluːk|qisqa sayohat|Unser Ausflug endet mit einem Picknick am See.|Qisqa sayohatimiz ko‘l bo‘yidagi piknik bilan tugaydi.|die Ausflüge
das Picknick|ˈpɪknɪk|piknik|Für das Picknick fehlt uns noch eine Decke.|Piknik uchun bizga hali to‘shama kerak.|die Picknicks
die Wanderung|ˈvandəʁʊŋ|piyoda sayohat|Die Wanderung beginnt an der alten Brücke.|Piyoda sayohat eski ko‘prikdan boshlanadi.|die Wanderungen
das Training|ˈtʁɛːnɪŋ|mashg‘ulot|Nach dem Training trinken wir viel Wasser.|Mashg‘ulotdan keyin ko‘p suv ichamiz.|die Trainings
der Trainer|ˈtʁɛːnɐ|murabbiy erkak|Der Trainer erklärt die Übung noch einmal.|Murabbiy mashqni yana bir bor tushuntiradi.|die Trainer
die Ausdauer|ˈaʊ̯sˌdaʊ̯ɐ|chidamlilik|Durch regelmäßiges Schwimmen verbessert sich meine Ausdauer.|Muntazam suzish orqali chidamliligim oshadi.|kein Plural
die Mannschaft|ˈmanʃaft|sport jamoasi|Unsere Mannschaft trainiert auch bei leichtem Regen.|Jamoamiz mayda yomg‘irda ham mashq qiladi.|die Mannschaften
der Wettbewerb|ˈvɛtbəˌvɛʁp|musobaqa; tanlov|Am Wettbewerb nehmen zwölf Mannschaften teil.|Musobaqada o‘n ikki jamoa qatnashadi.|die Wettbewerbe
das Turnier|tʊʁˈniːɐ̯|turnir|Das Turnier findet in der neuen Sporthalle statt.|Turnir yangi sport zalida o‘tkaziladi.|die Turniere
der Sieg|ziːk|g‘alaba|Nach dem Sieg feiern wir gemeinsam.|G‘alabadan keyin birgalikda bayram qilamiz.|die Siege
die Niederlage|ˈniːdɐˌlaːɡə|mag‘lubiyat|Aus dieser Niederlage haben wir viel gelernt.|Bu mag‘lubiyatdan ko‘p narsa o‘rgandik.|die Niederlagen
der Gegner|ˈɡeːɡnɐ|raqib|Mein Gegner beim Schach ist erst zehn Jahre alt.|Shaxmatdagi raqibim endigina o‘n yoshda.|die Gegner
der Schiedsrichter|ˈʃiːtsˌʁɪçtɐ|sport hakami|Der Schiedsrichter unterbricht das Spiel.|Hakam o‘yinni to‘xtatadi.|die Schiedsrichter
das Tor|toːɐ̯|darvoza; gol|In der letzten Minute schießt sie ein Tor.|Oxirgi daqiqada u gol uradi.|die Tore
der Punkt|pʊŋkt|ochko; nuqta|Uns fehlt nur ein Punkt zum Sieg.|G‘alaba uchun bizga atigi bir ochko yetmayapti.|die Punkte
die Sporthalle|ˈʃpɔʁtˌhalə|sport zali|Vor der Sporthalle ziehen wir saubere Schuhe an.|Sport zaliga kirishdan oldin toza poyabzal kiyamiz.|die Sporthallen
die Umkleidekabine|ˈʊmklaɪ̯dəkaˌbiːnə|kiyim almashtirish xonachasi|In der Umkleidekabine habe ich meine Mütze vergessen.|Kiyim almashtirish xonachasida bosh kiyimimni unutibman.|die Umkleidekabinen
die Kletterwand|ˈklɛtɐˌvant|tirmashish devori|An der Kletterwand trainiere ich meine Kraft.|Tirmashish devorida kuchimni mashq qildiraman.|die Kletterwände
wandern|ˈvandɐn|piyoda sayohat qilmoq|Am Sonntag wandern wir durch den Wald.|Yakshanba kuni o‘rmon bo‘ylab piyoda sayohat qilamiz.|
joggen|ˈdʒɔɡn̩|sekin yugurmoq|Ich jogge lieber morgens als abends.|Men kechqurundan ko‘ra ertalab yugurishni afzal ko‘raman.|
sich aufwärmen|zɪç ˈaʊ̯fˌvɛʁmən|badan qizdirmoq|Vor dem Spiel wärmen wir uns zehn Minuten auf.|O‘yindan oldin o‘n daqiqa badan qizdiramiz.|
klettern|ˈklɛtɐn|tirmashib chiqmoq|Beim Klettern denke ich nur an den nächsten Griff.|Tirmashayotganda faqat keyingi tutqichni o‘ylayman.|
rudern|ˈʁuːdɐn|eshkak eshmoq|Wir rudern langsam zur anderen Seite des Sees.|Ko‘lning boshqa tomoniga sekin eshkak eshib boramiz.|
segeln|ˈzeːɡl̩n|yelkanli qayiqda suzmoq|Bei diesem Wind können wir gut segeln.|Bunday shamolda yelkanli qayiqda yaxshi suzish mumkin.|
tauchen|ˈtaʊ̯xn̩|suvga sho‘ng‘imoq|Im Urlaub möchte sie zum ersten Mal tauchen.|Ta’tilda u birinchi marta suvga sho‘ng‘imoqchi.|
gewinnen|ɡəˈvɪnən|yutmoq|Heute gewinnt endlich unsere Mannschaft.|Bugun nihoyat jamoamiz yutadi.|gewinnt; gewann; hat gewonnen
aufgeben|ˈaʊ̯fˌɡeːbn̩|taslim bo‘lmoq; tashlamoq|Auch nach zwei Niederlagen geben wir nicht auf.|Ikki mag‘lubiyatdan keyin ham taslim bo‘lmaymiz.|gibt auf; gab auf; hat aufgegeben
werfen|ˈvɛʁfn̩|uloqtirmoq|Wirf den Ball bitte nicht gegen das Fenster.|Iltimos, to‘pni derazaga qarab uloqtirma.|wirft; warf; hat geworfen
fangen|ˈfaŋən|tutib olmoq|Den hohen Ball kann ich nicht fangen.|Baland uchgan to‘pni tutib ololmayman.|fängt; fing; hat gefangen
schießen|ˈʃiːsn̩|tepib otmoq; otmoq|Sie schießt den Ball direkt ins Tor.|U to‘pni to‘g‘ri darvozaga tepadi.|schießt; schoss; hat geschossen
zeichnen|ˈtsaɪ̯çnən|rasm chizmoq|Ich zeichne die Brücke mit einem Bleistift.|Ko‘prikni qalam bilan chizaman.|
malen|ˈmaːlən|bo‘yoq bilan rasm chizmoq|Wir malen den Himmel heute grün.|Bugun osmonni yashil rangda chizamiz.|
basteln|ˈbastl̩n|qo‘lda buyum yasamoq|Aus alten Schachteln basteln wir eine kleine Stadt.|Eski qutilardan kichik shahar yasaymiz.|
fotografieren|fotoɡʁaˈfiːʁən|suratga olmoq|Ich fotografiere lieber Türen als Denkmäler.|Men yodgorliklardan ko‘ra eshiklarni suratga olishni yoqtiraman.|
auftreten|ˈaʊ̯fˌtʁeːtn̩|sahnaga chiqmoq|Unser Chor tritt beim Stadtfest auf.|Xorimiz shahar bayramida sahnaga chiqadi.|tritt auf; trat auf; ist aufgetreten
proben|ˈpʁoːbn̩|repetitsiya qilmoq|Wir proben die letzte Szene noch einmal.|Oxirgi sahnani yana bir bor mashq qilamiz.|
klatschen|ˈklatʃn̩|qarsak chalmoq|Das Publikum klatscht im Rhythmus mit.|Tomoshabinlar ritmga mos qarsak chalishadi.|
genießen|ɡəˈniːsn̩|zavqlanmoq|Nach der Arbeit genieße ich die Musik im Park.|Ishdan keyin bog‘dagi musiqadan zavqlanaman.|genießt; genoss; hat genossen
spannend|ˈʃpanənt|hayajonli; qiziqarli|Der Film ist bis zur letzten Minute spannend.|Film oxirgi daqiqagacha qiziqarli.|
eintönig|ˈaɪ̯nˌtøːnɪç|bir xil; zerikarli|Jeden Tag dieselbe Übung wäre mir zu eintönig.|Har kuni ayni mashqni qilish menga juda zerikarli bo‘lardi.|
lustig|ˈlʊstɪç|kulgili|Die lustigste Szene kommt ganz am Ende.|Eng kulgili sahna eng oxirida keladi.|
ernst|ɛʁnst|jiddiy|Trotz des lustigen Titels ist der Film sehr ernst.|Kulgili sarlavhasiga qaramay, film juda jiddiy.|
kreativ|kʁeaˈtiːf|ijodkor; ijodiy|Für das Bühnenbild brauchen wir kreative Ideen.|Sahna bezagi uchun ijodiy g‘oyalar kerak.|
sportlich|ˈʃpɔʁtlɪç|sportga moyil; sportcha|Meine sportliche Nachbarin fährt überall mit dem Rad hin.|Sportga moyil qo‘shnim hamma joyga velosipedda boradi.|
anstrengend|ˈanˌʃtʁɛŋənt|charchatadigan|Die Wanderung war anstrengend, aber wunderschön.|Piyoda sayohat charchatdi, lekin juda chiroyli edi.|
erholsam|ɛɐ̯ˈhoːlzaːm|hordiq chiqaradigan|Ein Nachmittag am See ist für mich erholsam.|Ko‘l bo‘yidagi tushdan keyingi vaqt men uchun yaxshi hordiq.|
beliebt|bəˈliːpt|sevimli; ommabop|Dieser Tanzkurs ist bei Anfängern sehr beliebt.|Bu raqs kursi yangi boshlovchilar orasida juda mashhur.|
berühmt|bəˈʁyːmt|mashhur|Das berühmte Gemälde ist überraschend klein.|Mashhur surat hayratlanarli darajada kichik ekan.|
traditionell|tʁaditsi̯oˈnɛl|an’anaviy|Beim Fest tragen manche Gäste traditionelle Kleidung.|Bayramda ayrim mehmonlar an’anaviy kiyim kiyishadi.|
modern|moˈdɛʁn|zamonaviy|Das moderne Theater hat eine offene Bühne.|Zamonaviy teatrning ochiq sahnasi bor.|
live|laɪ̯f|jonli ijroda yoki efirda|Diese Band habe ich noch nie live gehört.|Bu guruhni hali hech qachon jonli tinglamaganman.|
ausverkauft|ˈaʊ̯sfɛɐ̯ˌkaʊ̯ft|barcha chiptalari yoki tovari sotilgan|Die Abendvorstellung ist leider ausverkauft.|Afsuski, kechki tomoshaning barcha chiptalari sotilgan.|
abwechslungsreich|ˈapvɛkslʊŋsˌʁaɪ̯ç|rang-barang; xilma-xil|Das Festival bietet ein abwechslungsreiches Programm.|Festival rang-barang dastur taklif etadi.|
"""

WEEKS[16] = r"""
die Natur|naˈtuːɐ̯|tabiat|In der Natur vergesse ich oft mein Handy.|Tabiat qo‘ynida telefonimni ko‘pincha unutaman.|kein Plural in dieser Bedeutung
die Landschaft|ˈlantʃaft|tabiiy manzara|Vom Zug aus sehen wir eine grüne Landschaft.|Poyezddan yashil manzarani ko‘ramiz.|die Landschaften
die Umgebung|ʊmˈɡeːbʊŋ|atrof; tevarak|In der Umgebung gibt es viele Wanderwege.|Atrofda piyoda sayohat yo‘llari ko‘p.|die Umgebungen
die Umwelt|ˈʊmˌvɛlt|atrof-muhit|Weniger Müll ist gut für die Umwelt.|Chiqindi kamroq bo‘lishi atrof-muhit uchun yaxshi.|kein Plural im üblichen Gebrauch
der Wald|valt|o‘rmon|Im Wald riecht die Luft nach Regen.|O‘rmonda havodan yomg‘ir hidi keladi.|die Wälder
die Wiese|ˈviːzə|o‘tloq|Auf der Wiese spielen wir ohne Schuhe.|O‘tloqda oyoqyalang o‘ynaymiz.|die Wiesen
das Feld|fɛlt|dala|Hinter dem Dorf liegen weite Felder.|Qishloq orqasida keng dalalar bor.|die Felder
der Hügel|ˈhyːɡl̩|tepalik|Vom Hügel sehen wir den ganzen See.|Tepalikdan butun ko‘lni ko‘ramiz.|die Hügel
das Tal|taːl|vodiy|Im Tal bleibt der Nebel länger.|Vodiyda tuman uzoqroq turadi.|die Täler
der Gipfel|ˈɡɪpfl̩|cho‘qqi|Den Gipfel erreichen wir am Nachmittag.|Cho‘qqiga tushdan keyin yetamiz.|die Gipfel
der Felsen|ˈfɛlzn̩|qoya|Hinter dem Felsen finden wir Schutz vor dem Wind.|Qoya ortida shamoldan pana topamiz.|die Felsen
die Quelle|ˈkvɛlə|buloq; manba|Neben dem Wanderweg liegt eine kleine Quelle.|Sayohat yo‘li yonida kichik buloq bor.|die Quellen
der Bach|bax|jilg‘a|Ein kleiner Bach fließt durch den Garten.|Bog‘dan kichik jilg‘a oqib o‘tadi.|die Bäche
das Ufer|ˈʔuːfɐ|qirg‘oq|Am Ufer stehen alte Bäume.|Qirg‘oqda eski daraxtlar o‘sib turibdi.|die Ufer
die Küste|ˈkʏstə|dengiz sohili|An der Küste weht fast immer Wind.|Dengiz sohilida deyarli doim shamol esadi.|die Küsten
die Insel|ˈʔɪnzl̩|orol|Auf der Insel fahren keine Autos.|Orolda mashinalar yurmaydi.|die Inseln
der Strand|ʃtʁant|plyaj; qumli sohil|Am frühen Morgen ist der Strand noch leer.|Erta tongda plyaj hali bo‘sh bo‘ladi.|die Strände
die Welle|ˈvɛlə|to‘lqin|Eine Welle macht meine Schuhe nass.|Bir to‘lqin poyabzalimni ho‘l qiladi.|die Wellen
der Sand|zant|qum|Nach dem Urlaub finde ich überall Sand.|Ta’tildan keyin hamma joydan qum topaman.|kein Plural im üblichen Gebrauch
die Erde|ˈʔeːɐ̯də|yer; tuproq|Die Erde im Blumentopf ist ganz trocken.|Tuvakdagi tuproq butunlay quruq.|kein Plural in dieser Bedeutung
die Pflanze|ˈpflantsə|o‘simlik|Diese Pflanze braucht wenig Wasser.|Bu o‘simlikka kam suv kerak.|die Pflanzen
das Blatt|blat|barg; varaq|Ein gelbes Blatt liegt auf meinem Buch.|Kitobim ustida sariq barg yotibdi.|die Blätter
der Ast|ast|shox|Auf dem Ast sitzt ein kleiner Vogel.|Shoxda kichik qush o‘tiribdi.|die Äste
die Wurzel|ˈvʊʁtsl̩|ildiz|Über diese Wurzel bin ich fast gestolpert.|Bu ildizga sal bo‘lmasa qoqilib ketdim.|die Wurzeln
die Blüte|ˈblyːtə|o‘simlik guli|Die erste Blüte öffnet sich im April.|Birinchi gul aprel oyida ochiladi.|die Blüten
das Insekt|ɪnˈzɛkt|hasharot|Ein kleines Insekt landet auf meiner Karte.|Xaritam ustiga kichik hasharot qo‘nadi.|die Insekten
die Biene|ˈbiːnə|asalari|Die Biene fliegt von Blüte zu Blüte.|Asalari guldan gulga uchadi.|die Bienen
der Schmetterling|ˈʃmɛtɐlɪŋ|kapalak|Ein blauer Schmetterling sitzt auf dem Zaun.|Panjarada ko‘k kapalak o‘tiribdi.|die Schmetterlinge
der Vogel|ˈfoːɡl̩|qush|Dieser Vogel singt lauter als mein Wecker.|Bu qush uyg‘otkichimdan balandroq sayraydi.|die Vögel
das Wildtier|ˈvɪltˌtiːɐ̯|yovvoyi hayvon|Wildtiere beobachten wir lieber aus der Ferne.|Yovvoyi hayvonlarni uzoqdan kuzatganimiz ma’qul.|die Wildtiere
der Regenbogen|ˈʁeːɡn̩ˌboːɡn̩|kamalak|Nach dem Regen erscheint ein Regenbogen über dem Dorf.|Yomg‘irdan keyin qishloq uzra kamalak paydo bo‘ladi.|die Regenbogen
der Nebel|ˈneːbl̩|tuman|Wegen des Nebels fahren wir langsam.|Tuman sababli sekin haydaymiz.|die Nebel
das Gewitter|ɡəˈvɪtɐ|momaqaldiroqli bo‘ron|Vor dem Gewitter gehen wir nach Hause.|Momaqaldiroqli bo‘rondan oldin uyga qaytamiz.|die Gewitter
der Blitz|blɪts|chaqmoq|Ein heller Blitz leuchtet über den Bergen.|Tog‘lar uzra yorqin chaqmoq chaqnaydi.|die Blitze
der Donner|ˈdɔnɐ|momaqaldiroq|Nach dem Blitz hören wir lauten Donner.|Chaqmoqdan keyin baland momaqaldiroq eshitamiz.|die Donner
der Sturm|ʃtʊʁm|kuchli bo‘ron|Der Sturm hat mehrere Äste abgebrochen.|Bo‘ron bir nechta shoxni sindirgan.|die Stürme
der Hagel|ˈhaːɡl̩|do‘l|Der Hagel trommelt gegen das Fenster.|Do‘l derazaga taqillab urilyapti.|kein Plural
der Frost|fʁɔst|qahraton sovuq; ayoz|Wegen des Frosts bleiben die Pflanzen drinnen.|Ayoz sababli o‘simliklar ichkarida qoladi.|die Fröste
die Hitze|ˈhɪtsə|jazirama|Bei dieser Hitze gehen wir erst abends spazieren.|Bunday jaziramada faqat kechqurun sayrga chiqamiz.|kein Plural
die Kälte|ˈkɛltə|sovuq|Trotz der Kälte warten wir draußen.|Sovuqqa qaramay tashqarida kutamiz.|kein Plural
die Temperatur|tɛmpəʁaˈtuːɐ̯|harorat|Die Temperatur sinkt heute Nacht unter null.|Bugun tunda harorat noldan pastga tushadi.|die Temperaturen
die Wettervorhersage|ˈvɛtɐfoːɐ̯hɛɐ̯ˌzaːɡə|ob-havo bashorati|Laut Wettervorhersage bleibt es morgen trocken.|Ob-havo bashoratiga ko‘ra ertaga yog‘ingarchilik bo‘lmaydi.|die Wettervorhersagen
der Niederschlag|ˈniːdɐˌʃlaːk|yog‘ingarchilik|In dieser Region gibt es im Sommer wenig Niederschlag.|Bu hududda yozda yog‘ingarchilik kam bo‘ladi.|die Niederschläge
der Schatten|ˈʃatn̩|soya|Im Schatten ist es viel angenehmer.|Soyada ancha yoqimli.|die Schatten
der Sonnenschein|ˈzɔnənˌʃaɪ̯n|quyosh nuri; quyoshli havo|Nach drei Regentagen genießen wir den Sonnenschein.|Uch yomg‘irli kundan keyin quyosh nuridan zavqlanamiz.|kein Plural
der Müll|mʏl|chiqindi|Unseren Müll nehmen wir nach dem Picknick wieder mit.|Piknikdan keyin chiqindilarimizni o‘zimiz bilan olib ketamiz.|kein Plural
der Abfall|ˈapˌfal|chiqindi|Organische Abfälle kommen in die braune Tonne.|Organik chiqindilar jigarrang idishga tashlanadi.|die Abfälle
die Mülltonne|ˈmʏlˌtɔnə|chiqindi idishi|Die Mülltonne steht hinter dem Haus.|Chiqindi idishi uy orqasida turibdi.|die Mülltonnen
das Pfand|pfant|qaytariladigan garov puli|Für diese Flasche bekomme ich Pfand zurück.|Bu shishani qaytarib, garov pulini olaman.|die Pfänder
die Energie|enɛʁˈɡiː|energiya; quvvat|Mit einer vollen Waschmaschine sparen wir Energie.|Kir mashinasini to‘ldirib ishlatsak, energiya tejaymiz.|die Energien
blühen|ˈblyːən|gullamoq|Im April blüht dieser Baum besonders schön.|Aprelda bu daraxt ayniqsa chiroyli gullaydi.|
wachsen|ˈvaksn̩|o‘smoq|Auf dem Balkon wachsen meine Pflanzen langsam.|Balkonda o‘simliklarim sekin o‘sadi.|wächst; wuchs; ist gewachsen
pflanzen|ˈpflantsn̩|ekmoq|Wir pflanzen einen Baum vor dem Haus.|Uy oldiga daraxt ekamiz.|
gießen|ˈɡiːsn̩|sug‘ormoq; quymoq|Im Urlaub gießt mein Nachbar die Pflanzen.|Ta’tilimda qo‘shnim o‘simliklarni sug‘oradi.|gießt; goss; hat gegossen
frieren|ˈfʁiːʁən|sovqotmoq; muzlamoq|Ohne Handschuhe friere ich schon nach fünf Minuten.|Qo‘lqopsiz besh daqiqadayoq sovqotaman.|friert; fror; hat gefroren; ist gefroren (zu Eis werden)
schmelzen|ˈʃmɛltsn̩|erimoq|In der Sonne schmilzt der letzte Schnee.|Quyoshda oxirgi qor eriyapti.|schmilzt; schmolz; ist geschmolzen
wehen|ˈveːən|esmoq|Heute weht ein warmer Wind aus Süden.|Bugun janubdan iliq shamol esyapti.|
donnern|ˈdɔnɐn|momaqaldiroq gumburlamoq|In der Ferne donnert es schon.|Uzoqda allaqachon momaqaldiroq gumburlayapti.|
blitzen|ˈblɪtsn̩|chaqmoq chaqmoq|Es blitzt, und wir schließen die Fenster.|Chaqmoq chaqyapti, biz derazalarni yopamiz.|
hageln|ˈhaːɡl̩n|do‘l yog‘moq|Plötzlich hagelt es mitten im Sommer.|Yozning o‘rtasida to‘satdan do‘l yog‘adi.|
nieseln|ˈniːzl̩n|mayda yomg‘ir yog‘moq|Es nieselt nur, deshalb bleiben wir draußen.|Faqat mayda yomg‘ir yog‘yapti, shuning uchun tashqarida qolamiz.|
sinken|ˈzɪŋkn̩|pasaymoq; cho‘kmoq|Nach Sonnenuntergang sinkt die Temperatur schnell.|Quyosh botgach harorat tez pasayadi.|sinkt; sank; ist gesunken
steigen|ˈʃtaɪ̯ɡn̩|ko‘tarilmoq|Im Sommer steigt der Wasserverbrauch.|Yozda suv iste’moli ko‘payadi.|steigt; stieg; ist gestiegen
schützen|ˈʃʏtsn̩|himoya qilmoq|Ein Hut schützt meinen Kopf vor der Sonne.|Shlyapa boshimni quyoshdan himoya qiladi.|
vermeiden|fɛɐ̯ˈmaɪ̯dn̩|oldini olmoq; chetlab o‘tmoq|Mit einer Stofftasche vermeide ich unnötigen Plastikmüll.|Mato sumka bilan ortiqcha plastik chiqindining oldini olaman.|vermeidet; vermied; hat vermieden
sparen|ˈʃpaːʁən|tejamoq; jamg‘armoq|Beim kurzen Duschen spare ich Wasser.|Qisqa dush qabul qilib suv tejayman.|
sammeln|ˈzaml̩n|yig‘moq|Am Strand sammeln wir herumliegenden Müll.|Plyajda sochilib yotgan chiqindilarni yig‘amiz.|
sortieren|zɔʁˈtiːʁən|saralamoq|Zu Hause sortieren wir Papier und Plastik getrennt.|Uyda qog‘oz va plastikni alohida saralaymiz.|
wegwerfen|ˈvɛkˌvɛʁfn̩|tashlab yubormoq|Diese Gläser sind zu schön zum Wegwerfen.|Bu bankalar tashlab yuborish uchun juda chiroyli.|wirft weg; warf weg; hat weggeworfen
wiederverwenden|ˈviːdɐfɛɐ̯ˌvɛndn̩|qayta ishlatmoq|Alte Gläser kann man gut wiederverwenden.|Eski shisha bankalarni qayta ishlatish juda qulay.|verwendet wieder; verwendete wieder; hat wiederverwendet
entfernen|ɛntˈfɛʁnən|olib tashlamoq|Vor dem Waschen entferne ich den groben Schmutz.|Yuvishdan oldin yirik kirlarni olib tashlayman.|
befestigen|bəˈfɛstɪɡn̩|mahkamlamoq|Ich befestige die Lampe an meinem Fahrrad.|Chiroqni velosipedimga mahkamlayman.|
ersetzen|ɛɐ̯ˈzɛtsn̩|o‘rniga boshqasini qo‘ymoq|Wir ersetzen die kaputte Flasche durch eine neue.|Singan shisha o‘rniga yangisini qo‘yamiz.|
aufheben|ˈaʊ̯fˌheːbn̩|yerdan olmoq; saqlab qo‘ymoq|Ich hebe den Schlüssel vom Boden auf.|Kalitni yerdan olaman.|hebt auf; hob auf; hat aufgehoben
einsammeln|ˈaɪ̯nˌzaml̩n|yig‘ib olmoq|Nach dem Ausflug sammeln wir alle Becher ein.|Sayohatdan keyin barcha stakanlarni yig‘ib olamiz.|
ausrutschen|ˈaʊ̯sˌʁʊtʃn̩|sirpanib ketmoq|Auf den nassen Blättern bin ich fast ausgerutscht.|Ho‘l barglarda sal bo‘lmasa sirpanib ketdim.|
stolpern|ˈʃtɔlpɐn|qoqilmoq|Im Dunkeln stolpere ich über meinen eigenen Rucksack.|Qorong‘ida o‘z ryukzagimga qoqilaman.|
sich verlaufen|zɪç fɛɐ̯ˈlaʊ̯fn̩|yo‘ldan adashmoq|Ohne Karte haben wir uns im Wald verlaufen.|Xaritasiz o‘rmonda adashib qoldik.|verläuft sich; verlief sich; hat sich verlaufen
umkehren|ˈʊmˌkeːʁən|ortga qaytmoq|Wegen des Gewitters kehren wir um.|Momaqaldiroqli bo‘ron sababli ortga qaytamiz.|
sich erholen|zɪç ɛɐ̯ˈhoːlən|hordiq chiqarmoq; tiklanmoq|Am Wochenende erhole ich mich im Grünen.|Dam olish kunlari tabiat qo‘ynida hordiq chiqaraman.|
heiter|ˈhaɪ̯tɐ|ochiq havo; xushchaqchaq|Morgen wird das Wetter heiter und mild.|Ertaga havo ochiq va mo‘tadil bo‘ladi.|
wechselhaft|ˈvɛksl̩haft|o‘zgaruvchan|Im April ist das Wetter oft wechselhaft.|Aprelda ob-havo ko‘pincha o‘zgaruvchan bo‘ladi.|
neblig|ˈneːblɪç|tumanli|Am Fluss ist es morgens oft neblig.|Daryo bo‘yida ertalab ko‘pincha tuman bo‘ladi.|
frostig|ˈfʁɔstɪç|ayozli|Nach der frostigen Nacht ist der Weg glatt.|Ayozli tundan keyin yo‘l sirpanchiq.|
stürmisch|ˈʃtʏʁmɪʃ|bo‘ronli|Bei stürmischem Wetter bleiben die Boote im Hafen.|Bo‘ronli havoda qayiqlar bandargohda qoladi.|
schwül|ʃvyːl|dim; issiq va nam|Vor dem Gewitter ist die Luft oft schwül.|Momaqaldiroqli bo‘rondan oldin havo ko‘pincha dim bo‘ladi.|
feucht|fɔɪ̯çt|nam|Nach dem Regen ist die Bank noch feucht.|Yomg‘irdan keyin skameyka hali nam.|
mild|mɪlt|mo‘tadil; yumshoq|Dieser Winter ist ungewöhnlich mild.|Bu qish odatdagidan mo‘tadil.|
rutschig|ˈʁʊtʃɪç|sirpanchiq|Die Steine am Ufer sind rutschig.|Qirg‘oqdagi toshlar sirpanchiq.|
glatt|ɡlat|silliq; muzlab sirpanchiq|Die Straße ist nach dem Frost glatt.|Ayozdan keyin yo‘l sirpanchiq bo‘lib qolgan.|
steil|ʃtaɪ̯l|tik|Der Weg zum Gipfel ist sehr steil.|Cho‘qqiga boradigan yo‘l juda tik.|
flach|flax|tekis; sayoz|Am Ufer ist das Wasser noch flach.|Qirg‘oq yaqinida suv hali sayoz.|
breit|bʁaɪ̯t|keng|Dieser Weg ist breit genug für zwei Fahrräder.|Bu yo‘l ikkita velosiped uchun yetarlicha keng.|
schmal|ʃmaːl|tor; ensiz|Die schmale Brücke führt über den Bach.|Tor ko‘prik jilg‘a ustidan o‘tadi.|
tief|tiːf|chuqur|In der Mitte ist der See sehr tief.|Ko‘l o‘rtasida juda chuqur.|
rein|ʁaɪ̯n|sof; toza|Hier oben genießen wir die reine Bergluft.|Bu balandlikda sof tog‘ havosidan zavqlanamiz.|
trüb|tʁyːp|loyqa; xira|Nach dem starken Regen ist das Wasser im Bach trüb.|Kuchli yomg‘irdan keyin jilg‘a suvi loyqa.|
umweltfreundlich|ˈʊmvɛltˌfʁɔɪ̯ntlɪç|atrof-muhitga zarari kam|Für kurze Wege ist das Fahrrad umweltfreundlich.|Qisqa masofalar uchun velosiped atrof-muhitga zarari kam vositadir.|
schädlich|ˈʃɛːtlɪç|zararli|Plastik im Meer ist für viele Tiere schädlich.|Dengizdagi plastik ko‘p hayvonlar uchun zararli.|
sparsam|ˈʃpaːɐ̯zaːm|tejamkor|Mit Wasser gehen wir im Sommer besonders sparsam um.|Yozda suvdan ayniqsa tejamkorlik bilan foydalanamiz.|
"""

TOPICS = {9: 'Sayohat va turar joy', 10: 'Uchrashuvlar, xizmatlar va rasmiy ishlar', 11: 'Ta’lim va til o‘rganish', 12: 'Ish joyi va ish qidirish', 13: 'Muloqot va texnologiya', 14: 'Munosabatlar va his-tuyg‘ular', 15: 'Bo‘sh vaqt, sport va madaniyat', 16: 'Tabiat, ob-havo va amaliy harakatlar'}


if __name__ == '__main__':
    entries = []
    for week, block in sorted(WEEKS.items()):
        lines = [line for line in block.strip().splitlines() if line.strip()]
        assert len(lines) == 100, (week, len(lines))
        for offset, line in enumerate(lines):
            word, ipa, meaning, example, translation, forms = [part.strip() for part in line.split('|')]
            entries.append(dict(id=(week-1)*100+offset+1, week=week,
                                topic=TOPICS[week], word=word, ipa=ipa,
                                meaning=meaning, example=example,
                                translation=translation, forms=forms))
    assert len(entries) == 800, len(entries)
    assert len({e['word'].casefold() for e in entries}) == 800
    assert [e['id'] for e in entries] == list(range(801, 1601))
    assert all(e['week'] == (e['id'] - 1) // 100 + 1 for e in entries)
    expected_fields = {'id', 'week', 'topic', 'word', 'ipa', 'meaning', 'example', 'translation', 'forms'}
    for entry in entries:
        assert set(entry) == expected_fields
        assert all(isinstance(entry[k], str) for k in expected_fields - {'id', 'week'})
        assert all(entry[k].strip() for k in expected_fields - {'id', 'week', 'forms'})
    target = Path(__file__).resolve().parents[1] / 'src/data/german/vocabulary-2.json'
    part_one = target.with_name('vocabulary-1.json')
    if part_one.exists():
        previous = json.loads(part_one.read_text(encoding='utf-8-sig'))
        previous_words = {e['word'].strip().casefold() for e in previous}
        overlaps = [e['word'] for e in entries if e['word'].casefold() in previous_words]
        assert not overlaps, overlaps
        print('Case-insensitive overlaps with part 1: 0')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(entries, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Count: {len(entries)}; IDs: {entries[0]["id"]}–{entries[-1]["id"]}')
    print('Duplicate words: 0; weeks: 100 entries each')
    print(target)
