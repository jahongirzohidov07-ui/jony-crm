"""Original A1 German–Uzbek vocabulary, weeks 1–8. Regenerates only vocabulary-1.json."""
import json
from pathlib import Path

# word | standard German broad IPA (lexical head) | Uzbek | example | translation | forms
DATA = r"""
@1|Tanishuv va olmoshlar
ich|ɪç|men|Ich heiße Ali.|Mening ismim Ali.|
du|duː|sen|Du bist nett.|Sen mehribonsan.|
er|eːɐ̯|u (erkak)|Er kommt aus Berlin.|U Berlindan kelgan.|
sie|ziː|u (ayol); ular|Sie ist meine Schwester.|U mening opam.|
es|ɛs|u (o‘rta jins)|Das Baby lacht. Es ist glücklich.|Chaqaloq kulyapti. U xursand.|
wir|viːɐ̯|biz|Wir lernen zusammen.|Biz birga o‘rganamiz.|
ihr|iːɐ̯|sizlar|Ihr seid heute leise.|Sizlar bugun jimsizlar.|
man|man|odam; kishilar (umumiy shaxs)|Hier spricht man Deutsch.|Bu yerda nemischa gaplashishadi.|
mein|maɪ̯n|mening|Das ist mein Stift.|Bu mening ruchkam.|
dein|daɪ̯n|sening|Dein Kaffee ist kalt.|Sening qahvang sovuq.|
@1|Asosiy fe’llar
sein|zaɪ̯n|bo‘lmoq|Ich bin müde.|Men charchaganman.|ist; war; ist gewesen
haben|ˈhaːbən|bor bo‘lmoq; ega bo‘lmoq|Wir haben Zeit.|Bizning vaqtimiz bor.|hat; hatte; hat gehabt
heißen|ˈhaɪ̯sən|deb atalmoq|Wie heißt dein Bruder?|Akangning ismi nima?|heißt; hieß; hat geheißen
kommen|ˈkɔmən|kelmoq|Komm bitte rein!|Iltimos, ichkariga kir!|kommt; kam; ist gekommen
wohnen|ˈvoːnən|yashamoq|Ich wohne in Taschkent.|Men Toshkentda yashayman.|
lernen|ˈlɛʁnən|o‘rganmoq|Wir lernen Deutsch.|Biz nemis tilini o‘rganyapmiz.|
sprechen|ˈʃpʁɛçən|gapirmoq|Sprich bitte langsam!|Iltimos, sekin gapir!|spricht; sprach; hat gesprochen
verstehen|fɛɐ̯ˈʃteːən|tushunmoq|Ich verstehe die Frage.|Men savolni tushunyapman.|versteht; verstand; hat verstanden
fragen|ˈfʁaːɡən|so‘ramoq|Frag bitte den Lehrer.|Iltimos, o‘qituvchidan so‘ra.|
antworten|ˈantvɔʁtən|javob bermoq|Anna antwortet sofort.|Anna darhol javob beradi.|
lesen|ˈleːzən|o‘qimoq|Ich lese ein Buch.|Men kitob o‘qiyapman.|liest; las; hat gelesen
schreiben|ˈʃʁaɪ̯bən|yozmoq|Schreib deinen Namen hier.|Ismingni shu yerga yoz.|schreibt; schrieb; hat geschrieben
hören|ˈhøːʁən|eshitmoq; tinglamoq|Wir hören Musik.|Biz musiqa tinglayapmiz.|
sehen|ˈzeːən|ko‘rmoq|Ich sehe deinen Hund.|Men sening itingni ko‘ryapman.|sieht; sah; hat gesehen
machen|ˈmaxən|qilmoq|Was machst du heute?|Bugun nima qilasan?|
gehen|ˈɡeːən|bormoq; yurmoq|Wir gehen nach Hause.|Biz uyga ketyapmiz.|geht; ging; ist gegangen
bleiben|ˈblaɪ̯bən|qolmoq|Bleib bitte hier.|Iltimos, shu yerda qol.|bleibt; blieb; ist geblieben
arbeiten|ˈaʁbaɪ̯tən|ishlamoq|Mein Vater arbeitet heute.|Dadam bugun ishlaydi.|
brauchen|ˈbʁaʊ̯xən|kerak bo‘lmoq|Ich brauche einen Stift.|Menga ruchka kerak.|
möchten|ˈmœçtən|xohlamoq (muloyim)|Ich möchte einen Tee.|Men bir piyola choy istayman.|möchte; möchten (Konjunktiv II von mögen)
@1|Salomlashish va qisqa so‘zlar
hallo|haˈloː|salom|Hallo, ich bin Lola!|Salom, men Lolaman!|
tschüss|tʃʏs|xayr|Tschüss, bis morgen!|Xayr, ertagacha!|
bitte|ˈbɪtə|iltimos; marhamat|Ein Wasser, bitte.|Bir stakan suv, iltimos.|
danke|ˈdaŋkə|rahmat|Danke für den Tee.|Choy uchun rahmat.|
ja|jaː|ha|Ja, das bin ich.|Ha, bu menman.|
nein|naɪ̯n|yo‘q|Nein, ich habe keine Katze.|Yo‘q, mening mushugim yo‘q.|
gut|ɡuːt|yaxshi|Dein Deutsch ist gut.|Nemis tiling yaxshi.|
schlecht|ʃlɛçt|yomon|Der Kaffee ist schlecht.|Qahva yomon.|
auch|aʊ̯x|ham|Ich lerne auch Deutsch.|Men ham nemis tilini o‘rganyapman.|
nicht|nɪçt|emas; -ma (inkor)|Ich komme heute nicht.|Men bugun kelmayman.|
und|ʊnt|va|Ali und Anna lernen.|Ali va Anna o‘rganishyapti.|
oder|ˈoːdɐ|yoki|Tee oder Kaffee?|Choymi yoki qahvami?|
aber|ˈaːbɐ|lekin|Ich bin müde, aber glücklich.|Men charchaganman, lekin baxtliman.|
hier|hiːɐ̯|shu yerda|Hier ist dein Buch.|Mana sening kitobing.|
dort|dɔʁt|u yerda|Anna wohnt dort.|Anna u yerda yashaydi.|
wer|veːɐ̯|kim|Wer ist das?|Bu kim?|
was|vas|nima|Was liest du?|Nima o‘qiyapsan?|
wie|viː|qanday|Wie geht es dir?|Ahvoling qanday?|
wo|voː|qayerda|Wo wohnst du?|Qayerda yashaysan?|
woher|voˈheːɐ̯|qayerdan|Woher kommt ihr?|Sizlar qayerdansizlar?|
@1|Tanishuv va dars
der Name|ˈnaːmə|ism|Mein Name ist Karim.|Mening ismim Karim.|die Namen
der Vorname|ˈfoːɐ̯naːmə|ism (familiyadan farqli)|Mein Vorname ist Aziz.|Mening ismim Aziz.|die Vornamen
der Nachname|ˈnaːxnaːmə|familiya|Ist Müller dein Nachname?|Müller sening familiyangmi?|die Nachnamen
das Land|lant|mamlakat|Mein Land ist schön.|Mening mamlakatim chiroyli.|die Länder
die Stadt|ʃtat|shahar|Die Stadt ist groß.|Shahar katta.|die Städte
die Sprache|ˈʃpʁaːxə|til|Welche Sprache sprichst du?|Qaysi tilda gapirasan?|die Sprachen
Deutsch|dɔɪ̯tʃ|nemis tili|Deutsch macht mir Spaß.|Nemis tili menga yoqadi.|
Usbekisch|ʊsˈbeːkɪʃ|o‘zbek tili|Zu Hause sprechen wir Usbekisch.|Uyda biz o‘zbekcha gaplashamiz.|
der Mann|man|erkak; er|Der Mann heißt Paul.|Bu erkakning ismi Paul.|die Männer
die Frau|fʁaʊ̯|ayol; xotin|Die Frau spricht Deutsch.|Ayol nemischa gapiradi.|die Frauen
das Kind|kɪnt|bola|Das Kind malt ein Haus.|Bola uy rasmini chizyapti.|die Kinder
der Freund|fʁɔɪ̯nt|do‘st (erkak)|Mein Freund wohnt hier.|Do‘stim shu yerda yashaydi.|die Freunde
die Freundin|ˈfʁɔɪ̯ndɪn|dugona; do‘st (ayol)|Meine Freundin heißt Malika.|Dugonamning ismi Malika.|die Freundinnen
der Lehrer|ˈleːʁɐ|o‘qituvchi (erkak)|Der Lehrer hört zu.|O‘qituvchi tinglayapti.|die Lehrer
die Lehrerin|ˈleːʁəʁɪn|o‘qituvchi (ayol)|Die Lehrerin lacht.|O‘qituvchi kulyapti.|die Lehrerinnen
der Kurs|kʊʁs|kurs|Unser Kurs beginnt morgen.|Bizning kursimiz ertaga boshlanadi.|die Kurse
das Buch|buːx|kitob|Das Buch ist neu.|Kitob yangi.|die Bücher
der Stift|ʃtɪft|yozuv quroli; ruchka|Mein Stift schreibt blau.|Ruchkam ko‘k rangda yozadi.|die Stifte
die Frage|ˈfʁaːɡə|savol|Ich habe eine Frage.|Menda bir savol bor.|die Fragen
die Antwort|ˈantvɔʁt|javob|Deine Antwort ist richtig.|Javobing to‘g‘ri.|die Antworten
@1|Asosiy sonlar
null|nʊl|nol|Heute sind es null Grad.|Bugun havo nol daraja.|
eins|aɪ̯ns|bir|Die Nummer eins fehlt.|Birinchi raqam yo‘q.|
zwei|tsvaɪ̯|ikki|Ich habe zwei Brüder.|Mening ikkita akam bor.|
drei|dʁaɪ̯|uch|Drei Kinder spielen hier.|Bu yerda uch bola o‘ynayapti.|
vier|fiːɐ̯|to‘rt|Der Tisch hat vier Beine.|Stolning to‘rtta oyog‘i bor.|
fünf|fʏnf|besh|Wir brauchen fünf Stühle.|Bizga beshta stul kerak.|
sechs|zɛks|olti|Sechs Eier sind genug.|Oltita tuxum yetadi.|
sieben|ˈziːbən|yetti|Eine Woche hat sieben Tage.|Bir hafta yetti kundan iborat.|
acht|axt|sakkiz|Der Bus kommt um acht.|Avtobus soat sakkizda keladi.|
neun|nɔɪ̯n|to‘qqiz|Meine Tochter ist neun.|Qizim to‘qqiz yoshda.|
zehn|tseːn|o‘n|Ich warte zehn Minuten.|Men o‘n daqiqa kutaman.|
elf|ɛlf|o‘n bir|Wir sind elf Personen.|Biz o‘n bir kishimiz.|
zwölf|tsvœlf|o‘n ikki|Es ist zwölf Uhr.|Soat o‘n ikki.|
zwanzig|ˈtsvantsɪç|yigirma|Das kostet zwanzig Euro.|Bu yigirma yevro turadi.|
hundert|ˈhʊndɐt|yuz|Hier arbeiten hundert Menschen.|Bu yerda yuz kishi ishlaydi.|
die Zahl|tsaːl|son|Schreib die Zahl bitte auf.|Iltimos, sonni yozib ol.|die Zahlen
die Nummer|ˈnʊmɐ|raqam|Welche Nummer hat dein Zimmer?|Xonangning raqami nechchi?|die Nummern
alt|alt|qari; eski; yoshda|Wie alt bist du?|Yoshing nechada?|
jung|jʊŋ|yosh|Unsere Lehrerin ist jung.|O‘qituvchimiz yosh.|
neu|nɔɪ̯|yangi|Mein Handy ist neu.|Telefonim yangi.|
@1|Oddiy ta’riflar
groß|ɡʁoːs|katta|Deine Tasche ist groß.|Sumkang katta.|
klein|klaɪ̯n|kichik|Mein Zimmer ist klein.|Xonam kichkina.|
schön|ʃøːn|chiroyli|Das Bild ist schön.|Rasm chiroyli.|
nett|nɛt|mehribon; yoqimli|Unsere Nachbarn sind nett.|Qo‘shnilarimiz mehribon.|
langsam|ˈlaŋzaːm|sekin|Bitte lies langsam.|Iltimos, sekin o‘qi.|
schnell|ʃnɛl|tez|Der Hund läuft schnell.|It tez yuguradi.|
richtig|ˈʁɪçtɪç|to‘g‘ri|Die Nummer ist richtig.|Raqam to‘g‘ri.|
falsch|falʃ|noto‘g‘ri|Die Adresse ist falsch.|Manzil noto‘g‘ri.|
einfach|ˈaɪ̯nfax|oson; oddiy|Die Aufgabe ist einfach.|Topshiriq oson.|
schwer|ʃveːɐ̯|qiyin; og‘ir|Mein Koffer ist schwer.|Jomadonim og‘ir.|
@2|Oila
die Familie|faˈmiːli̯ə|oila|Meine Familie wohnt in Samarkand.|Oilam Samarqandda yashaydi.|die Familien
die Mutter|ˈmʊtɐ|ona|Meine Mutter kocht gern.|Onam ovqat pishirishni yaxshi ko‘radi.|die Mütter
der Vater|ˈfaːtɐ|ota|Mein Vater liest abends.|Otam kechqurun kitob o‘qiydi.|die Väter
die Eltern|ˈɛltɐn|ota-ona|Meine Eltern besuchen uns.|Ota-onam biznikiga kelishyapti.|nur Plural
die Schwester|ˈʃvɛstɐ|opa; singil|Meine Schwester ist vier Jahre alt.|Singlim to‘rt yoshda.|die Schwestern
der Bruder|ˈbʁuːdɐ|aka; uka|Mein Bruder spielt Fußball.|Akam futbol o‘ynaydi.|die Brüder
die Tochter|ˈtɔxtɐ|qiz farzand|Ihre Tochter lernt schwimmen.|Uning qizi suzishni o‘rganyapti.|die Töchter
der Sohn|zoːn|o‘g‘il farzand|Unser Sohn schläft schon.|O‘g‘limiz allaqachon uxlayapti.|die Söhne
die Großmutter|ˈɡʁoːsmʊtɐ|buvi|Meine Großmutter hat ein Fahrrad.|Buvimning velosipedi bor.|die Großmütter
der Großvater|ˈɡʁoːsfaːtɐ|bobo|Mein Großvater trinkt Tee.|Bobom choy ichyapti.|die Großväter
die Großeltern|ˈɡʁoːsʔɛltɐn|buvi va bobo|Am Sonntag kommen die Großeltern.|Yakshanba kuni buvi bilan bobo kelishadi.|nur Plural
die Oma|ˈoːma|buvi (og‘zaki)|Oma, dein Kuchen schmeckt gut!|Buvijon, pirogingiz mazali!|die Omas
der Opa|ˈoːpa|bobo (og‘zaki)|Opa erzählt eine Geschichte.|Bobom hikoya aytib beryapti.|die Opas
die Tante|ˈtantə|xola; amma|Meine Tante wohnt nebenan.|Xolam yonimizda yashaydi.|die Tanten
der Onkel|ˈɔŋkl̩|tog‘a; amaki|Mein Onkel fährt Bus.|Tog‘am avtobusda yuradi.|die Onkel
die Cousine|kuˈziːnə|amakivachcha va boshqa qarindosh qiz|Meine Cousine heißt Saida.|Amakivachchamning ismi Saida.|die Cousinen
der Cousin|kuˈzɛ̃ː|amakivachcha va boshqa qarindosh o‘g‘il|Mein Cousin ist zwölf.|Amakivachcham o‘n ikki yoshda.|die Cousins
das Baby|ˈbeːbi|chaqaloq|Das Baby hat Hunger.|Chaqaloq och qoldi.|die Babys
die Geschwister|ɡəˈʃvɪstɐ|aka-uka va opa-singillar|Hast du Geschwister?|Aka-ukang yoki opa-singling bormi?|nur Plural
das Mädchen|ˈmɛːtçən|qiz bola|Das Mädchen spielt im Garten.|Qizcha bog‘da o‘ynayapti.|die Mädchen
der Junge|ˈjʊŋə|o‘g‘il bola|Der Junge trägt eine Brille.|Bola ko‘zoynak taqadi.|die Jungen
der Ehemann|ˈeːəman|er|Ihr Ehemann ist Koch.|Uning eri oshpaz.|die Ehemänner
die Ehefrau|ˈeːəfʁaʊ̯|xotin|Seine Ehefrau arbeitet hier.|Uning xotini shu yerda ishlaydi.|die Ehefrauen
der Nachbar|ˈnaːxbaːɐ̯|qo‘shni (erkak)|Der Nachbar hilft uns.|Qo‘shnimiz bizga yordam beradi.|die Nachbarn
die Nachbarin|ˈnaːxbaːʁɪn|qo‘shni (ayol)|Unsere Nachbarin hat drei Katzen.|Qo‘shni ayolning uchta mushugi bor.|die Nachbarinnen
verheiratet|fɛɐ̯ˈhaɪ̯ʁaːtət|turmush qurgan|Meine Schwester ist verheiratet.|Opam turmushga chiqqan.|
ledig|ˈleːdɪç|turmush qurmagan|Paul ist ledig.|Paul uylanmagan.|
geschieden|ɡəˈʃiːdən|ajrashgan|Meine Tante ist geschieden.|Xolam ajrashgan.|
zusammen|tsuˈzamən|birga|Wir essen zusammen.|Biz birga ovqatlanamiz.|
allein|aˈlaɪ̯n|yolg‘iz|Opa wohnt nicht allein.|Bobom yolg‘iz yashamaydi.|
@2|Bog‘lovchi va yordamchi so‘zlar
unser|ˈʊnzɐ|bizning|Unser Haus ist gelb.|Uyimiz sariq.|
euer|ˈɔɪ̯ɐ|sizlarning|Ist das euer Auto?|Bu sizlarning mashinangizmi?|
mit|mɪt|bilan|Ich komme mit meiner Mutter.|Men onam bilan kelaman.|
ohne|ˈoːnə|siz; -siz|Ich trinke Tee ohne Zucker.|Men choyni shakarsiz ichaman.|
für|fyːɐ̯|uchun|Das Geschenk ist für dich.|Sovg‘a sen uchun.|
von|fɔn|dan; -ning|Das ist ein Foto von Oma.|Bu buvimning surati.|
aus|aʊ̯s|dan (ichidan, kelib chiqish)|Sie kommt aus Usbekistan.|U O‘zbekistondan.|
bei|baɪ̯|huzurida; yonida|Wir sind bei unseren Eltern.|Biz ota-onamiznikidamiz.|
zu|tsuː|ga (tomon)|Ich gehe zu meiner Tante.|Men xolamnikiga ketyapman.|
nach|naːx|ga; keyin|Nach dem Kurs esse ich.|Kursdan keyin ovqatlanaman.|
@2|Vaqt
die Zeit|tsaɪ̯t|vaqt|Hast du heute Zeit?|Bugun vaqting bormi?|die Zeiten
die Uhr|uːɐ̯|soat (asbob)|Meine Uhr geht falsch.|Soatim noto‘g‘ri yuradi.|die Uhren
die Stunde|ˈʃtʊndə|soat (davomiylik)|Der Film dauert eine Stunde.|Film bir soat davom etadi.|die Stunden
die Minute|miˈnuːtə|daqiqa|Eine Minute, bitte!|Bir daqiqa, iltimos!|die Minuten
die Sekunde|zeˈkʊndə|soniya|Warte zehn Sekunden.|O‘n soniya kut.|die Sekunden
der Tag|taːk|kun|Heute ist ein schöner Tag.|Bugun chiroyli kun.|die Tage
die Woche|ˈvɔxə|hafta|Diese Woche habe ich frei.|Bu hafta ishdan bo‘shman.|die Wochen
der Monat|ˈmoːnat|oy|Ein Monat ist schon vorbei.|Bir oy allaqachon o‘tib ketdi.|die Monate
das Jahr|jaːɐ̯|yil|Ein Jahr hat zwölf Monate.|Bir yilda o‘n ikki oy bor.|die Jahre
der Geburtstag|ɡəˈbuːɐ̯tstaːk|tug‘ilgan kun|Wann hast du Geburtstag?|Tug‘ilgan kuning qachon?|die Geburtstage
der Morgen|ˈmɔʁɡən|ertalab; tong|Am Morgen trinke ich Wasser.|Ertalab suv ichaman.|die Morgen
der Vormittag|ˈfoːɐ̯mɪtaːk|tushgacha bo‘lgan vaqt|Am Vormittag habe ich Unterricht.|Tushgacha darsim bor.|die Vormittage
der Mittag|ˈmɪtaːk|tush payti|Zu Mittag gibt es Suppe.|Tushlikka sho‘rva bor.|die Mittage
der Nachmittag|ˈnaːxmɪtaːk|tushdan keyingi vaqt|Am Nachmittag besuchen wir Oma.|Tushdan keyin buvimnikiga boramiz.|die Nachmittage
der Abend|ˈaːbənt|kechqurun|Am Abend bin ich zu Hause.|Kechqurun uyda bo‘laman.|die Abende
die Nacht|naxt|tun|In der Nacht ist es still.|Tunda jimjit bo‘ladi.|die Nächte
heute|ˈhɔɪ̯tə|bugun|Heute kocht mein Bruder.|Bugun akam ovqat pishiradi.|
morgen|ˈmɔʁɡən|ertaga|Morgen beginnt mein Kurs.|Ertaga kursim boshlanadi.|
gestern|ˈɡɛstɐn|kecha|Gestern war ich bei Oma.|Kecha buvimnikida edim.|
jetzt|jɛtst|hozir|Jetzt brauche ich eine Pause.|Hozir menga tanaffus kerak.|
@2|Hafta kunlari
der Montag|ˈmoːntaːk|dushanba|Am Montag arbeiten wir.|Dushanba kuni ishlaymiz.|die Montage
der Dienstag|ˈdiːnstaːk|seshanba|Dienstag habe ich Deutsch.|Seshanba kuni nemis tili darsim bor.|die Dienstage
der Mittwoch|ˈmɪtvɔx|chorshanba|Am Mittwoch kommt mein Onkel.|Chorshanba kuni amakim keladi.|die Mittwoche
der Donnerstag|ˈdɔnɐstaːk|payshanba|Donnerstag spielen wir zusammen.|Payshanba kuni birga o‘ynaymiz.|die Donnerstage
der Freitag|ˈfʁaɪ̯taːk|juma|Am Freitag endet der Kurs.|Juma kuni kurs tugaydi.|die Freitage
der Samstag|ˈzamstaːk|shanba|Samstag schlafen wir lange.|Shanba kuni uzoq uxlaymiz.|die Samstage
der Sonntag|ˈzɔntaːk|yakshanba|Am Sonntag essen alle bei uns.|Yakshanba kuni hamma biznikida ovqatlanadi.|die Sonntage
das Wochenende|ˈvɔxn̩ʔɛndə|hafta oxiri|Am Wochenende fahre ich nach Hause.|Hafta oxirida uyga ketaman.|die Wochenenden
wann|van|qachon|Wann kommt deine Schwester?|Opang qachon keladi?|
um|ʊm|soat … da; atrofida|Der Kurs beginnt um neun.|Kurs soat to‘qqizda boshlanadi.|
@2|Oylar va oilaviy faoliyat
der Januar|ˈjanuaːɐ̯|yanvar|Im Januar ist es kalt.|Yanvarda sovuq bo‘ladi.|die Januare
der Februar|ˈfeːbʁuaːɐ̯|fevral|Im Februar hat Papa Geburtstag.|Dadamning tug‘ilgan kuni fevralda.|die Februare
der März|mɛʁts|mart|Im März kommen die Blumen.|Martda gullar ochila boshlaydi.|die Märze
der April|aˈpʁɪl|aprel|Im April regnet es oft.|Aprelda tez-tez yomg‘ir yog‘adi.|die Aprile
der Mai|maɪ̯|may|Im Mai sitzen wir draußen.|Mayda tashqarida o‘tiramiz.|die Maie
der Juni|ˈjuːni|iyun|Im Juni endet die Schule.|Iyunda maktabdagi o‘qish tugaydi.|die Junis
der Juli|ˈjuːli|iyul|Im Juli fahren wir ans Meer.|Iyulda dengizga boramiz.|die Julis
der August|aʊ̯ˈɡʊst|avgust|Im August ist es heiß.|Avgustda issiq bo‘ladi.|die Auguste
der September|zɛpˈtɛmbɐ|sentabr|Im September beginnt mein neuer Kurs.|Sentabrda yangi kursim boshlanadi.|die September
der Oktober|ɔkˈtoːbɐ|oktabr|Im Oktober tragen wir Jacken.|Oktabrda kurtka kiyamiz.|die Oktober
der November|noˈvɛmbɐ|noyabr|Im November bleiben wir oft drinnen.|Noyabrda ko‘pincha ichkarida qolamiz.|die November
der Dezember|deˈtsɛmbɐ|dekabr|Im Dezember besuchen wir unsere Großeltern.|Dekabrda buvi va bobomiznikiga boramiz.|die Dezember
lieben|ˈliːbən|sevmoq|Ich liebe meine Familie.|Men oilamni sevaman.|
besuchen|bəˈzuːxən|borib ko‘rmoq; tashrif buyurmoq|Wir besuchen morgen unsere Tante.|Ertaga xolamiznikiga boramiz.|
leben|ˈleːbən|yashamoq; hayot kechirmoq|Meine Großeltern leben auf dem Land.|Buvi va bobom qishloqda yashashadi.|
spielen|ˈʃpiːlən|o‘ynamoq|Die Kinder spielen im Haus.|Bolalar uyda o‘ynashyapti.|
lachen|ˈlaxən|kulmoq|Das Baby lacht laut.|Chaqaloq ovoz chiqarib kulyapti.|
feiern|ˈfaɪ̯ɐn|nishonlamoq|Wir feiern heute meinen Geburtstag.|Bugun tug‘ilgan kunimni nishonlaymiz.|
schenken|ˈʃɛŋkən|sovg‘a qilmoq|Ich schenke Oma Blumen.|Buvimga gullar sovg‘a qilaman.|
heiraten|ˈhaɪ̯ʁaːtən|turmush qurmoq|Meine Schwester heiratet im Mai.|Opam mayda turmushga chiqadi.|
@2|Vaqtni aniqlashtirish
früh|fʁyː|erta|Oma steht sehr früh auf.|Buvim juda erta turadi.|
spät|ʃpɛːt|kech|Heute komme ich spät nach Hause.|Bugun uyga kech kelaman.|
immer|ˈɪmɐ|har doim|Mein Bruder hat immer Hunger.|Akamning har doim qorni och.|
oft|ɔft|tez-tez|Wir telefonieren oft mit Oma.|Buvim bilan tez-tez telefonda gaplashamiz.|
manchmal|ˈmançmaːl|ba’zan|Manchmal frühstücken wir im Garten.|Ba’zan bog‘da nonushta qilamiz.|
nie|niː|hech qachon|Ich trinke nie kalten Tee.|Men hech qachon sovuq choy ichmayman.|
bald|balt|tez orada|Bald kommt meine Schwester.|Tez orada opam keladi.|
später|ˈʃpɛːtɐ|keyinroq|Ich rufe dich später an.|Men senga keyinroq qo‘ng‘iroq qilaman.|
halb|halp|yarim|Es ist halb acht.|Soat yetti yarim.|
das Viertel|ˈfɪʁtl̩|chorak|Ein Viertel der Pizza ist noch da.|Pitsaning choragi hali bor.|die Viertel
@3|Sinf va o‘qish
die Schule|ˈʃuːlə|maktab|Die Schule ist neben dem Park.|Maktab bog‘ yonida.|die Schulen
die Klasse|ˈklasə|sinf|Unsere Klasse ist sehr nett.|Sinfimiz juda ahil.|die Klassen
der Unterricht|ˈʊntɐʁɪçt|dars; o‘qitish|Der Unterricht beginnt gleich.|Dars hozir boshlanadi.|kein Plural
die Lektion|lɛkˈtsi̯oːn|dars (kitob bo‘limi)|Lektion drei ist kurz.|Uchinchi dars qisqa.|die Lektionen
die Aufgabe|ˈaʊ̯fɡaːbə|topshiriq|Diese Aufgabe mache ich zuerst.|Bu topshiriqni avval bajaraman.|die Aufgaben
die Hausaufgabe|ˈhaʊ̯sʔaʊ̯fɡaːbə|uy vazifasi|Meine Hausaufgabe liegt noch zu Hause.|Uy vazifam hali ham uyda qolibdi.|die Hausaufgaben
das Heft|hɛft|daftar|Mein Heft hat einen roten Umschlag.|Daftarimning muqovasi qizil.|die Hefte
das Papier|paˈpiːɐ̯|qog‘oz|Wir brauchen noch Papier.|Bizga yana qog‘oz kerak.|die Papiere (Dokumente); als Material kein Plural
der Bleistift|ˈblaɪ̯ʃtɪft|qalam|Der Bleistift ist zu kurz.|Qalam juda kalta.|die Bleistifte
der Kugelschreiber|ˈkuːɡl̩ʃʁaɪ̯bɐ|sharikli ruchka|Dein Kugelschreiber liegt unter dem Buch.|Ruchkang kitob ostida turibdi.|die Kugelschreiber
der Radiergummi|ʁaˈdiːɐ̯ɡʊmi|o‘chirg‘ich|Kann ich deinen Radiergummi haben?|O‘chirg‘ichingni olsam bo‘ladimi?|die Radiergummis
das Lineal|lineˈaːl|chizg‘ich|Das Lineal ist dreißig Zentimeter lang.|Chizg‘ich o‘ttiz santimetr uzunlikda.|die Lineale
die Schere|ˈʃeːʁə|qaychi|Die Schere liegt im Schrank.|Qaychi shkafda turibdi.|die Scheren
die Tafel|ˈtaːfl̩|doska|An der Tafel steht mein Name.|Doskada mening ismim yozilgan.|die Tafeln
das Wort|vɔʁt|so‘z|Dieses Wort kenne ich schon.|Bu so‘zni allaqachon bilaman.|die Wörter (einzeln); die Worte (Äußerung)
der Satz|zats|gap|Lies bitte den ganzen Satz.|Iltimos, gapni to‘liq o‘qi.|die Sätze
der Buchstabe|ˈbuːxʃtaːbə|harf|Mein Name hat vier Buchstaben.|Ismim to‘rtta harfdan iborat.|die Buchstaben
der Text|tɛkst|matn|Der Text ist leicht zu lesen.|Matnni o‘qish oson.|die Texte
die Seite|ˈzaɪ̯tə|sahifa; tomon|Öffnet das Buch auf Seite zehn.|Kitobning o‘ninchi sahifasini oching.|die Seiten
das Wörterbuch|ˈvœʁtɐbuːx|lug‘at|Das Wörterbuch hilft mir oft.|Lug‘at menga tez-tez yordam beradi.|die Wörterbücher
die Übung|ˈyːbʊŋ|mashq|Die nächste Übung machen wir mündlich.|Keyingi mashqni og‘zaki bajaramiz.|die Übungen
der Fehler|ˈfeːlɐ|xato|Ein Fehler ist kein Problem.|Bitta xato muammo emas.|die Fehler
die Prüfung|ˈpʁyːfʊŋ|imtihon|Die Prüfung ist am Freitag.|Imtihon juma kuni.|die Prüfungen
die Pause|ˈpaʊ̯zə|tanaffus|In der Pause essen wir Äpfel.|Tanaffusda olma yeymiz.|die Pausen
der Schüler|ˈʃyːlɐ|o‘quvchi (o‘g‘il)|Der Schüler hebt die Hand.|O‘quvchi qo‘lini ko‘taryapti.|die Schüler
die Schülerin|ˈʃyːləʁɪn|o‘quvchi (qiz)|Die Schülerin liest sehr gut.|O‘quvchi qiz juda yaxshi o‘qiydi.|die Schülerinnen
üben|ˈyːbən|mashq qilmoq|Wir üben jeden Tag zehn Minuten.|Har kuni o‘n daqiqa mashq qilamiz.|
wiederholen|viːdɐˈhoːlən|takrorlamoq|Wiederhole bitte den letzten Satz.|Iltimos, oxirgi gapni takrorla.|
buchstabieren|buːxʃtaˈbiːʁən|harflab aytmoq|Buchstabieren Sie bitte Ihren Nachnamen.|Iltimos, familiyangizni harflab ayting.|
erklären|ɛɐ̯ˈklɛːʁən|tushuntirmoq|Die Lehrerin erklärt das Wort.|O‘qituvchi so‘zni tushuntiryapti.|
@3|Ish va kasb
die Arbeit|ˈaʁbaɪ̯t|ish|Meine Arbeit beginnt um acht.|Ishim soat sakkizda boshlanadi.|die Arbeiten
der Beruf|bəˈʁuːf|kasb|Was bist du von Beruf?|Kasbing nima?|die Berufe
das Büro|byˈʁoː|idora; ofis|Im Büro ist es warm.|Ofisda issiq.|die Büros
die Firma|ˈfɪʁma|firma; korxona|Die Firma sucht einen Fahrer.|Firma haydovchi qidiryapti.|die Firmen
der Chef|ʃɛf|boshliq (erkak)|Unser Chef fährt Fahrrad.|Boshlig‘imiz velosipedda yuradi.|die Chefs
die Chefin|ˈʃɛfɪn|boshliq (ayol)|Die Chefin kommt um neun.|Boshlig‘imiz soat to‘qqizda keladi.|die Chefinnen
der Kollege|kɔˈleːɡə|hamkasb (erkak)|Mein Kollege spricht Usbekisch.|Hamkasbim o‘zbekcha gapiradi.|die Kollegen
die Kollegin|kɔˈleːɡɪn|hamkasb (ayol)|Meine Kollegin bringt Kuchen mit.|Hamkasbim pirog olib keladi.|die Kolleginnen
der Arzt|aːɐ̯tst|shifokor (erkak)|Der Arzt fragt nach meinem Namen.|Shifokor ismimni so‘rayapti.|die Ärzte
die Ärztin|ˈɛːɐ̯tstɪn|shifokor (ayol)|Die Ärztin arbeitet heute lange.|Shifokor bugun uzoq ishlaydi.|die Ärztinnen
der Verkäufer|fɛɐ̯ˈkɔɪ̯fɐ|sotuvchi (erkak)|Der Verkäufer zeigt mir Schuhe.|Sotuvchi menga oyoq kiyim ko‘rsatyapti.|die Verkäufer
die Verkäuferin|fɛɐ̯ˈkɔɪ̯fəʁɪn|sotuvchi (ayol)|Die Verkäuferin ist freundlich.|Sotuvchi xushmuomala.|die Verkäuferinnen
der Koch|kɔx|oshpaz (erkak)|Der Koch probiert die Suppe.|Oshpaz sho‘rvani tatib ko‘ryapti.|die Köche
die Köchin|ˈkœçɪn|oshpaz (ayol)|Die Köchin schneidet Gemüse.|Oshpaz sabzavot to‘g‘rayapti.|die Köchinnen
der Fahrer|ˈfaːʁɐ|haydovchi|Der Fahrer kennt die Straße.|Haydovchi bu ko‘chani biladi.|die Fahrer
der Student|ʃtuˈdɛnt|talaba (yigit)|Der Student lernt in der Bibliothek.|Talaba kutubxonada o‘qiyapti.|die Studenten
die Studentin|ʃtuˈdɛntɪn|talaba (qiz)|Die Studentin sucht ein Zimmer.|Talaba qiz xona qidiryapti.|die Studentinnen
der Computer|kɔmˈpjuːtɐ|kompyuter|Mein Computer ist heute langsam.|Kompyuterim bugun sekin ishlayapti.|die Computer
das Telefon|teleˈfoːn|telefon|Das Telefon klingelt schon wieder.|Telefon yana jiringlayapti.|die Telefone
die E-Mail|ˈiːmeːl|elektron xat|Ich schreibe meiner Chefin eine E-Mail.|Boshlig‘imga elektron xat yozyapman.|die E-Mails
@3|Uy va jihozlar
das Haus|haʊ̯s|uy (bino)|Unser Haus hat einen Garten.|Uyimizning bog‘i bor.|die Häuser
die Wohnung|ˈvoːnʊŋ|xonadon; kvartira|Die Wohnung hat drei Zimmer.|Xonadon uch xonali.|die Wohnungen
das Zimmer|ˈtsɪmɐ|xona|Mein Zimmer ist oben.|Xonam yuqori qavatda.|die Zimmer
die Küche|ˈkʏçə|oshxona|In der Küche riecht es gut.|Oshxonadan yoqimli hid kelyapti.|die Küchen
das Bad|baːt|hammom|Das Bad ist neben der Küche.|Hammom oshxona yonida.|die Bäder
das Schlafzimmer|ˈʃlaːftsɪmɐ|yotoqxona|Im Schlafzimmer steht ein großes Bett.|Yotoqxonada katta karavot bor.|die Schlafzimmer
das Wohnzimmer|ˈvoːntsɪmɐ|mehmonxona (uyda)|Wir sitzen im Wohnzimmer.|Biz mehmonxonada o‘tiribmiz.|die Wohnzimmer
der Flur|fluːɐ̯|yo‘lak (uy ichida)|Deine Schuhe stehen im Flur.|Oyoq kiyiming yo‘lakda turibdi.|die Flure
der Balkon|balˈkɔŋ|balkon|Auf dem Balkon wachsen Blumen.|Balkonda gullar o‘sadi.|die Balkone
der Garten|ˈɡaʁtn̩|bog‘|Opa arbeitet gern im Garten.|Bobom bog‘da ishlashni yoqtiradi.|die Gärten
die Tür|tyːɐ̯|eshik|Mach bitte die Tür zu.|Iltimos, eshikni yop.|die Türen
das Fenster|ˈfɛnstɐ|deraza|Das Fenster ist offen.|Deraza ochiq.|die Fenster
die Wand|vant|devor|An der Wand hängt ein Foto.|Devorda surat osilgan.|die Wände
der Boden|ˈboːdən|pol; yer|Auf dem Boden liegt ein Stift.|Polda ruchka yotibdi.|die Böden
die Treppe|ˈtʁɛpə|zinapoya|Die Treppe ist sehr schmal.|Zinapoya juda tor.|die Treppen
der Tisch|tɪʃ|stol|Das Essen steht auf dem Tisch.|Ovqat stolda turibdi.|die Tische
der Stuhl|ʃtuːl|stul|Dieser Stuhl ist frei.|Bu stul bo‘sh.|die Stühle
das Bett|bɛt|karavot|Die Katze schläft im Bett.|Mushuk karavotda uxlayapti.|die Betten
der Schrank|ʃʁaŋk|shkaf|Meine Jacke hängt im Schrank.|Kurtkam shkafda osilgan.|die Schränke
das Sofa|ˈzoːfa|divan|Auf dem Sofa sitzt mein Bruder.|Divanda akam o‘tiribdi.|die Sofas
die Lampe|ˈlampə|chiroq|Die Lampe ist kaputt.|Chiroq buzilgan.|die Lampen
der Teppich|ˈtɛpɪç|gilam|Der Teppich ist weich.|Gilam yumshoq.|die Teppiche
der Spiegel|ˈʃpiːɡl̩|oyna (ko‘zgu)|Im Spiegel sehe ich Zahnpasta.|Ko‘zguda tish pastasini ko‘ryapman.|die Spiegel
das Regal|ʁeˈɡaːl|tokcha; javon|Meine Bücher stehen im Regal.|Kitoblarim javonda turibdi.|die Regale
der Kühlschrank|ˈkyːlʃʁaŋk|muzlatkich|Im Kühlschrank ist nur Milch.|Muzlatkichda faqat sut bor.|die Kühlschränke
die Waschmaschine|ˈvaʃmaʃiːnə|kir yuvish mashinasi|Die Waschmaschine ist sehr laut.|Kir yuvish mashinasi juda shovqinli.|die Waschmaschinen
der Schlüssel|ˈʃlʏsl̩|kalit|Mein Schlüssel ist in der Tasche.|Kalitim sumkada.|die Schlüssel
die Miete|ˈmiːtə|ijara haqi|Die Miete ist leider hoch.|Afsuski, ijara haqi baland.|die Mieten
die Adresse|aˈdʁɛsə|manzil|Schreib mir bitte deine Adresse.|Iltimos, manzilingni menga yoz.|die Adressen
der Stock|ʃtɔk|qavat|Wir wohnen im zweiten Stock.|Biz ikkinchi qavatda yashaymiz.|die Stockwerke (Etagen); die Stöcke (Stäbe)
@3|Uy va darsdagi harakatlar
sitzen|ˈzɪtsən|o‘tirmoq|Ich sitze neben dem Fenster.|Men deraza yonida o‘tiribman.|sitzt; saß; hat gesessen
stehen|ˈʃteːən|turmoq|Warum steht dein Schuh auf dem Tisch?|Nega oyoq kiyiming stol ustida turibdi?|steht; stand; hat gestanden
liegen|ˈliːɡən|yotmoq|Meine Brille liegt auf dem Sofa.|Ko‘zoynagim divanda yotibdi.|liegt; lag; hat gelegen
öffnen|ˈœfnən|ochmoq|Öffne bitte das Fenster.|Iltimos, derazani och.|
schließen|ˈʃliːsən|yopmoq|Das Geschäft schließt um sechs.|Do‘kon soat oltida yopiladi.|schließt; schloss; hat geschlossen
suchen|ˈzuːxən|qidirmoq|Ich suche schon wieder meinen Schlüssel.|Men yana kalitimni qidiryapman.|
finden|ˈfɪndən|topmoq|Ich finde meine Tasche nicht.|Sumkamni topolmayapman.|findet; fand; hat gefunden
zeigen|ˈtsaɪ̯ɡən|ko‘rsatmoq|Zeig mir bitte dein Zimmer.|Iltimos, xonangni menga ko‘rsat.|
helfen|ˈhɛlfən|yordam bermoq|Mein Sohn hilft beim Kochen.|O‘g‘lim ovqat pishirishda yordam beradi.|hilft; half; hat geholfen
putzen|ˈpʊtsən|tozalamoq|Heute putzen wir die Fenster.|Bugun derazalarni tozalaymiz.|
@3|Joylashuv
in|ɪn|ichida; -da|Die Milch steht in der Küche.|Sut oshxonada turibdi.|
auf|aʊ̯f|ustida; ustiga|Die Katze springt auf den Tisch.|Mushuk stolga sakrayapti.|
unter|ˈʊntɐ|ostida|Unter dem Bett ist ein Ball.|Karavot ostida to‘p bor.|
neben|ˈneːbən|yonida|Neben mir sitzt Anna.|Yonimda Anna o‘tiribdi.|
vor|foːɐ̯|oldida; oldin|Vor dem Haus steht ein Baum.|Uy oldida daraxt bor.|
hinter|ˈhɪntɐ|orqasida|Der Hund ist hinter der Tür.|It eshik orqasida.|
zwischen|ˈtsvɪʃən|orasida|Der Tisch steht zwischen zwei Fenstern.|Stol ikkita deraza orasida turibdi.|
oben|ˈoːbən|yuqorida|Meine Eltern wohnen oben.|Ota-onam yuqori qavatda yashaydi.|
unten|ˈʊntən|pastda|Unten wartet ein Taxi.|Pastda taksi kutyapti.|
an|an|yonida; ustida (tik yuzada)|Die Uhr hängt an der Wand.|Soat devorda osilgan.|
@4|Ovqat va ichimlik
das Essen|ˈɛsn̩|ovqat|Das Essen ist gleich fertig.|Ovqat hozir tayyor bo‘ladi.|die Essen (Mahlzeiten)
das Frühstück|ˈfʁyːʃtʏk|nonushta|Zum Frühstück esse ich Brot.|Nonushtaga non yeyman.|die Frühstücke
das Mittagessen|ˈmɪtaːkˌʔɛsn̩|tushlik|Das Mittagessen schmeckt allen.|Tushlik hammaga yoqyapti.|die Mittagessen
das Abendessen|ˈaːbn̩tˌʔɛsn̩|kechki ovqat|Nach dem Abendessen gehen wir spazieren.|Kechki ovqatdan keyin sayr qilamiz.|die Abendessen
das Brot|bʁoːt|non|Das Brot ist noch warm.|Non hali issiq.|die Brote
das Brötchen|ˈbʁøːtçən|kichik dumaloq non|Ich nehme zwei Brötchen.|Men ikkita kichik non olaman.|die Brötchen
die Butter|ˈbʊtɐ|sariyog‘|Die Butter ist im Kühlschrank.|Sariyog‘ muzlatkichda.|kein Plural
der Käse|ˈkɛːzə|pishloq|Dieser Käse riecht stark.|Bu pishloqning hidi o‘tkir.|die Käse (Sorten)
das Ei|aɪ̯|tuxum|Mein Ei ist zu weich.|Tuxumim juda yumshoq pishibdi.|die Eier
die Marmelade|maʁməˈlaːdə|murabbo|Oma macht Marmelade selbst.|Buvim murabboni o‘zi tayyorlaydi.|die Marmeladen
die Milch|mɪlç|sut|Trinkst du Kaffee mit Milch?|Qahvani sut bilan ichasanmi?|kein Plural
der Joghurt|ˈjoːɡʊʁt|yogurt|Im Joghurt sind Erdbeeren.|Yogurt ichida qulupnay bor.|die Joghurts
das Wasser|ˈvasɐ|suv|Bitte bring mir ein Glas Wasser.|Iltimos, menga bir stakan suv olib kel.|die Wässer (Sorten); meist ohne Plural
der Tee|teː|choy|Der Tee ist noch zu heiß.|Choy hali juda issiq.|die Tees
der Kaffee|ˈkafe|qahva|Ohne Kaffee bin ich morgens langsam.|Qahvasiz ertalab sust bo‘laman.|die Kaffees
der Saft|zaft|sharbat|Der Saft ist aus frischen Äpfeln.|Sharbat yangi olmalardan tayyorlangan.|die Säfte
die Limonade|limoˈnaːdə|limonad|Die Limonade ist mir zu süß.|Limonad menga juda shirinlik qilyapti.|die Limonaden
das Mineralwasser|mineˈʁaːlvasɐ|mineral suv|Ich möchte Mineralwasser ohne Kohlensäure.|Men gazsiz mineral suv istayman.|die Mineralwässer
das Bier|biːɐ̯|pivo|Er bestellt ein alkoholfreies Bier.|U alkogolsiz pivo buyurtma qiladi.|die Biere
der Wein|vaɪ̯n|vino; sharob|Für mich bitte keinen Wein.|Menga sharob bermang, iltimos.|die Weine
@4|Meva va sabzavot
das Obst|oːpst|meva (umumiy)|Ich esse jeden Tag Obst.|Men har kuni meva yeyman.|kein Plural
der Apfel|ˈapfl̩|olma|Dieser Apfel ist knackig.|Bu olma qarsillaydi.|die Äpfel
die Banane|baˈnaːnə|banan|Die Banane kommt in meine Tasche.|Bananni sumkamga solaman.|die Bananen
die Orange|oˈʁaŋʒə|apelsin|Die Orange hat viele Kerne.|Apelsinning urug‘i ko‘p.|die Orangen
die Zitrone|tsiˈtʁoːnə|limon|Eine Zitrone reicht für den Tee.|Choy uchun bitta limon yetadi.|die Zitronen
die Birne|ˈbɪʁnə|nok|Die Birne ist schon reif.|Nok allaqachon pishgan.|die Birnen
die Erdbeere|ˈeːɐ̯tbeːʁə|qulupnay|Diese Erdbeeren schmecken nach Sommer.|Bu qulupnaylarning ta’mi yozni eslatadi.|die Erdbeeren
die Traube|ˈtʁaʊ̯bə|uzum donasi|Die Trauben sind sehr süß.|Uzum juda shirin.|die Trauben
die Melone|meˈloːnə|qovun; poliz mevasi|Wir teilen eine große Melone.|Biz katta qovunni bo‘lishib yeymiz.|die Melonen
der Pfirsich|ˈpfɪʁzɪç|shaftoli|Der Pfirsich ist weich und saftig.|Shaftoli yumshoq va sersuv.|die Pfirsiche
das Gemüse|ɡəˈmyːzə|sabzavot|Zum Reis gibt es Gemüse.|Guruch yoniga sabzavot beriladi.|die Gemüse (Sorten); meist ohne Plural
die Kartoffel|kaʁˈtɔfl̩|kartoshka|Die Kartoffeln kochen schon.|Kartoshkalar allaqachon qaynayapti.|die Kartoffeln
die Tomate|toˈmaːtə|pomidor|Ich schneide die Tomate klein.|Pomidorni mayda to‘g‘rayapman.|die Tomaten
die Gurke|ˈɡʊʁkə|bodring|Die Gurke kommt in den Salat.|Bodring salatga solinadi.|die Gurken
die Zwiebel|ˈtsviːbl̩|piyoz|Diese Zwiebel bringt mich zum Weinen.|Bu piyoz meni yig‘latyapti.|die Zwiebeln
die Karotte|kaˈʁɔtə|sabzi|Das Kind isst eine rohe Karotte.|Bola xom sabzi yeyapti.|die Karotten
die Paprika|ˈpaːpʁika|bulg‘or qalampiri|Wir brauchen eine rote Paprika.|Bizga qizil bulg‘or qalampiri kerak.|die Paprikas
der Knoblauch|ˈknoːplaʊ̯x|sarimsoq|In die Suppe kommt wenig Knoblauch.|Sho‘rvaga ozgina sarimsoq solinadi.|kein Plural
die Bohne|ˈboːnə|loviya|Die Bohnen brauchen noch Zeit.|Loviya yana biroz pishishi kerak.|die Bohnen
der Pilz|pɪlts|qo‘ziqorin|Wir kaufen Pilze im Supermarkt.|Qo‘ziqorinni supermarketdan sotib olamiz.|die Pilze
@4|Taomlar va mahsulotlar
der Reis|ʁaɪ̯s|guruch|Heute kocht Papa Reis.|Bugun dadam guruch pishiradi.|kein Plural
die Nudel|ˈnuːdl̩|makaron|Die Nudeln sind in fünf Minuten fertig.|Makaron besh daqiqada tayyor bo‘ladi.|die Nudeln
das Fleisch|flaɪ̯ʃ|go‘sht|Ich esse heute kein Fleisch.|Bugun go‘sht yemayman.|kein Plural
das Hähnchen|ˈhɛːnçən|jo‘ja; tovuq go‘shti|Das Hähnchen ist im Ofen.|Tovuq go‘shti duxovkada.|die Hähnchen
der Fisch|fɪʃ|baliq|Zum Fisch essen wir Kartoffeln.|Baliq bilan kartoshka yeymiz.|die Fische
die Wurst|vʊʁst|kolbasa|Ist diese Wurst aus Rindfleisch?|Bu kolbasa mol go‘shtidanmi?|die Würste
die Suppe|ˈzʊpə|sho‘rva|Die Suppe wärmt meine Hände.|Sho‘rva qo‘llarimni isityapti.|die Suppen
der Salat|zaˈlaːt|salat|Im Salat fehlt noch Salz.|Salatga hali tuz yetishmayapti.|die Salate
die Pizza|ˈpɪtsa|pitsa|Unsere Pizza ist riesig.|Pitsamiz juda katta.|die Pizzen
der Kuchen|ˈkuːxən|pirog; keks|Der Kuchen ist für meine Mutter.|Pirog onam uchun.|die Kuchen
der Keks|keːks|pechenye|Der letzte Keks gehört dir.|Oxirgi pechenye seniki.|die Kekse
die Schokolade|ʃokoˈlaːdə|shokolad|Die Schokolade schmilzt in meiner Tasche.|Shokolad sumkamda eriyapti.|die Schokoladen
das Eis|aɪ̯s|muz; muzqaymoq|Im Sommer essen wir gern Eis.|Yozda muzqaymoqni sevib yeymiz.|kein Plural
der Zucker|ˈtsʊkɐ|shakar|Ein Löffel Zucker ist genug.|Bir qoshiq shakar yetadi.|kein Plural
das Salz|zalts|tuz|Gib mir bitte das Salz.|Iltimos, tuzni uzat.|die Salze (Sorten)
der Pfeffer|ˈpfɛfɐ|murch|In der Suppe ist viel Pfeffer.|Sho‘rvada murch ko‘p.|kein Plural
das Öl|øːl|yog‘ (suyuq)|Wir braten das Gemüse in Öl.|Sabzavotni yog‘da qovuramiz.|die Öle
das Mehl|meːl|un|Auf meiner Nase ist Mehl.|Burnimga un tegibdi.|die Mehle (Sorten)
der Honig|ˈhoːnɪç|asal|Ich esse Brot mit Honig.|Men nonni asal bilan yeyman.|die Honige (Sorten)
die Soße|ˈzoːsə|qayla; sous|Die Soße passt gut zum Reis.|Qayla guruchga juda mos keladi.|die Soßen
@4|Idishlar va ovqatlanish joyi
der Teller|ˈtɛlɐ|likopcha|Mein Teller ist schon leer.|Likopcham allaqachon bo‘sh.|die Teller
die Tasse|ˈtasə|piyola; chashka|Die Tasse hat einen kleinen Riss.|Piyolada kichik yoriq bor.|die Tassen
das Glas|ɡlaːs|stakan; shisha|Mein Glas steht neben deinem.|Stakanim senikining yonida.|die Gläser
die Flasche|ˈflaʃə|shisha idish; butilka|Die Flasche ist noch halb voll.|Shishada hali yarimigacha ichimlik bor.|die Flaschen
der Löffel|ˈlœfl̩|qoshiq|Für die Suppe brauche ich einen Löffel.|Sho‘rva uchun qoshiq kerak.|die Löffel
die Gabel|ˈɡaːbl̩|sanchqi|Meine Gabel ist auf den Boden gefallen.|Sanchqim polga tushib ketdi.|die Gabeln
das Messer|ˈmɛsɐ|pichoq|Dieses Messer schneidet sehr gut.|Bu pichoq juda yaxshi kesadi.|die Messer
der Topf|tɔpf|qozon|Der Topf ist zu klein.|Qozon juda kichik.|die Töpfe
die Pfanne|ˈpfanə|tova|Die Eier sind in der Pfanne.|Tuxumlar tovada.|die Pfannen
die Schüssel|ˈʃʏsl̩|kosa; tog‘ora|Der Salat ist in der blauen Schüssel.|Salat ko‘k kosada.|die Schüsseln
der Herd|heːɐ̯t|plita|Mach bitte den Herd aus.|Iltimos, plitani o‘chir.|die Herde
der Ofen|ˈoːfn̩|pech; duxovka|Der Kuchen bleibt noch im Ofen.|Pirog hali duxovkada turadi.|die Öfen
das Restaurant|ʁɛstoˈʁãː|restoran|Das Restaurant ist heute voll.|Bugun restoran to‘la.|die Restaurants
das Café|kaˈfeː|kafe|Wir treffen uns im Café.|Kafeda uchrashamiz.|die Cafés
die Speisekarte|ˈʃpaɪ̯zəkaʁtə|taomnoma|Die Speisekarte liegt auf dem Tisch.|Taomnoma stolda turibdi.|die Speisekarten
die Rechnung|ˈʁɛçnʊŋ|hisob; to‘lov qog‘ozi|Die Rechnung bitte, wir möchten gehen.|Hisobni bering, iltimos, ketmoqchimiz.|die Rechnungen
der Kellner|ˈkɛlnɐ|ofitsiant (erkak)|Der Kellner bringt frisches Wasser.|Ofitsiant toza suv olib kelyapti.|die Kellner
die Kellnerin|ˈkɛlnəʁɪn|ofitsiant (ayol)|Die Kellnerin empfiehlt den Fisch.|Ofitsiant baliqni tavsiya qilyapti.|die Kellnerinnen
der Hunger|ˈhʊŋɐ|ochlik; qorin ochishi|Nach dem Sport habe ich Hunger.|Sportdan keyin qornim ochadi.|kein Plural
der Durst|dʊʁst|chanqoq|Bei dieser Hitze habe ich Durst.|Bunday issiqda chanqayman.|kein Plural
@4|Ovqatlanish va ta’m
essen|ˈɛsn̩|yemoq; ovqatlanmoq|Was esst ihr zum Frühstück?|Nonushtaga nima yeysizlar?|isst; aß; hat gegessen
trinken|ˈtʁɪŋkən|ichmoq|Trink bitte genug Wasser.|Iltimos, yetarlicha suv ich.|trinkt; trank; hat getrunken
kochen|ˈkɔxən|pishirmoq; qaynatmoq|Heute koche ich für sechs Personen.|Bugun olti kishiga ovqat pishiraman.|
backen|ˈbakən|yopmoq; pechda pishirmoq|Am Samstag backen wir Brot.|Shanba kuni non yopamiz.|backt/bäckt; backte; hat gebacken
braten|ˈbʁaːtən|qovurmoq|Brate die Zwiebeln zuerst.|Avval piyozni qovur.|brät; briet; hat gebraten
schneiden|ˈʃnaɪ̯dən|kesmoq; to‘g‘ramoq|Ich schneide Brot für alle.|Men hammaga non kesyapman.|schneidet; schnitt; hat geschnitten
bestellen|bəˈʃtɛlən|buyurtma bermoq|Wir bestellen zwei Suppen.|Biz ikki kosa sho‘rva buyurtma qilamiz.|
bezahlen|bəˈtsaːlən|to‘lamoq|Heute bezahle ich das Essen.|Bugun ovqatga men to‘layman.|
schmecken|ˈʃmɛkən|ta’mi bo‘lmoq; yoqmoq|Schmeckt dir mein Kuchen?|Pirogim senga yoqdimi?|
probieren|pʁoˈbiːʁən|tatib ko‘rmoq; sinamoq|Probier mal diese Suppe!|Bu sho‘rvani bir tatib ko‘r!|
süß|zyːs|shirin|Der Honig ist sehr süß.|Asal juda shirin.|
sauer|ˈzaʊ̯ɐ|nordon|Die Zitrone ist mir zu sauer.|Limon menga juda nordonlik qilyapti.|
salzig|ˈzaltsɪç|sho‘r|Die Suppe ist etwas salzig.|Sho‘rva biroz sho‘r.|
scharf|ʃaʁf|achchiq; o‘tkir|Die Soße ist scharf, aber lecker.|Qayla achchiq, lekin mazali.|
lecker|ˈlɛkɐ|mazali|Dein Brot ist wirklich lecker.|Noning juda mazali ekan.|
frisch|fʁɪʃ|yangi; barra|Die Tomaten sind frisch.|Pomidorlar barra.|
heiß|haɪ̯s|issiq; qaynoq|Vorsicht, die Pfanne ist heiß!|Ehtiyot bo‘l, tova issiq!|
kalt|kalt|sovuq|Mein Tee ist schon kalt.|Choyim allaqachon sovibdi.|
satt|zat|to‘q|Danke, ich bin schon satt.|Rahmat, qornim to‘ydi.|
vegetarisch|veɡeˈtaːʁɪʃ|go‘shtsiz; vegetariancha|Gibt es ein vegetarisches Gericht?|Go‘shtsiz taom bormi?|
@5|Do‘kon va pul
der Laden|ˈlaːdn̩|do‘kon|Der Laden öffnet um zehn.|Do‘kon soat o‘nda ochiladi.|die Läden
das Geschäft|ɡəˈʃɛft|do‘kon; savdo joyi|Dieses Geschäft verkauft Kinderschuhe.|Bu do‘kon bolalar oyoq kiyimini sotadi.|die Geschäfte
der Supermarkt|ˈzuːpɐmaʁkt|supermarket|Im Supermarkt ist heute viel los.|Supermarket bugun juda gavjum.|die Supermärkte
der Markt|maʁkt|bozor|Auf dem Markt kaufen wir Obst.|Bozordan meva sotib olamiz.|die Märkte
die Bäckerei|bɛkəˈʁaɪ̯|nonvoyxona|Vor der Bäckerei riecht es gut.|Nonvoyxona oldidan yoqimli hid keladi.|die Bäckereien
die Metzgerei|mɛtsɡəˈʁaɪ̯|go‘sht do‘koni|Die Metzgerei hat heute geschlossen.|Go‘sht do‘koni bugun yopiq.|die Metzgereien
die Kasse|ˈkasə|kassa|An der Kasse warten drei Leute.|Kassada uch kishi kutyapti.|die Kassen
der Preis|pʁaɪ̯s|narx|Der Preis steht auf dem Schild.|Narx lavhada yozilgan.|die Preise
das Geld|ɡɛlt|pul|Mein Geld ist in der Jacke.|Pulim kurtkamda.|die Gelder (Geldbeträge); meist ohne Plural
der Euro|ˈɔɪ̯ʁo|yevro|Das Brot kostet einen Euro.|Non bir yevro turadi.|die Euros; nach Zahlen Euro
der Cent|tsɛnt|sent|Mir fehlen zehn Cent.|Menga o‘n sent yetmayapti.|die Cents; nach Zahlen Cent
die Münze|ˈmʏntsə|tanga|Eine Münze liegt unter der Kasse.|Kassa ostida tanga yotibdi.|die Münzen
der Geldschein|ˈɡɛltʃaɪ̯n|pul kupyurasi|Dieser Geldschein ist ganz neu.|Bu kupyura yap-yangi.|die Geldscheine
die Karte|ˈkaʁtə|karta; xarita|Kann ich mit Karte bezahlen?|Karta bilan to‘lasam bo‘ladimi?|die Karten
das Angebot|ˈanɡəboːt|taklif; chegirmali mahsulot|Die Äpfel sind heute im Angebot.|Bugun olmalarga chegirma bor.|die Angebote
der Rabatt|ʁaˈbat|chegirma|Gibt es einen Rabatt für Studenten?|Talabalarga chegirma bormi?|die Rabatte
der Kunde|ˈkʊndə|xaridor (erkak)|Der Kunde sucht eine Jacke.|Xaridor kurtka qidiryapti.|die Kunden
die Kundin|ˈkʊndɪn|xaridor (ayol)|Die Kundin bezahlt bar.|Xaridor naqd pul bilan to‘layapti.|die Kundinnen
der Kassenbon|ˈkasn̩bɔŋ|kassa cheki|Bitte geben Sie mir den Kassenbon.|Iltimos, kassa chekini bering.|die Kassenbons
das Wechselgeld|ˈvɛksl̩ɡɛlt|qaytim|Ihr Wechselgeld liegt hier.|Qaytimingiz mana bu yerda.|kein Plural
@5|Kiyimlar
die Kleidung|ˈklaɪ̯dʊŋ|kiyim-kechak|Warme Kleidung ist heute wichtig.|Bugun issiq kiyim kerak.|kein Plural
die Hose|ˈhoːzə|shim|Diese Hose ist zu lang.|Bu shim juda uzun.|die Hosen
die Jeans|dʒiːns|jinsi shim|Meine Jeans ist noch nass.|Jinsi shimim hali ho‘l.|die Jeans
das Hemd|hɛmt|erkaklar ko‘ylagi|Papa trägt ein weißes Hemd.|Dadam oq ko‘ylak kiygan.|die Hemden
die Bluse|ˈbluːzə|ayollar koftasi|Die Bluse passt zum Rock.|Kofta yubkaga mos keladi.|die Blusen
das T-Shirt|ˈtiːʃœːɐ̯t|futbolka|Auf meinem T-Shirt ist eine Katze.|Futbolkamda mushuk rasmi bor.|die T-Shirts
der Pullover|pʊˈloːvɐ|sviter|Oma strickt mir einen Pullover.|Buvim menga sviter to‘qiyapti.|die Pullover
die Jacke|ˈjakə|kurtka|Nimm deine Jacke mit!|Kurtkangni olib ket!|die Jacken
der Mantel|ˈmantl̩|palto|Der Mantel hängt an der Tür.|Palto eshikda osilgan.|die Mäntel
das Kleid|klaɪ̯t|ayollar ko‘ylagi|Sie trägt ein grünes Kleid.|U yashil ko‘ylak kiygan.|die Kleider
der Rock|ʁɔk|yubka|Der Rock hat zwei Taschen.|Yubkaning ikkita cho‘ntagi bor.|die Röcke
der Anzug|ˈantsuːk|kostyum|Zum Fest trägt er einen Anzug.|Bayramga u kostyum kiyadi.|die Anzüge
der Schuh|ʃuː|oyoq kiyim|In meinem Schuh ist ein Stein.|Oyoq kiyimim ichida tosh bor.|die Schuhe
der Stiefel|ˈʃtiːfl̩|etik|Meine Stiefel sind warm.|Etiklarim issiq.|die Stiefel
die Sandale|zanˈdaːlə|sandal|Im Sommer trage ich Sandalen.|Yozda sandal kiyaman.|die Sandalen
die Socke|ˈzɔkə|paypoq|Eine Socke fehlt schon wieder.|Yana bitta paypoq yo‘q.|die Socken
die Mütze|ˈmʏtsə|qalpoq|Die rote Mütze gehört meinem Sohn.|Qizil qalpoq o‘g‘limniki.|die Mützen
der Hut|huːt|shlyapa|Dein Hut fliegt weg!|Shlyapang uchib ketyapti!|die Hüte
der Schal|ʃaːl|sharf|Mein Schal ist zwei Meter lang.|Sharfim ikki metr uzunlikda.|die Schals
der Handschuh|ˈhantʃuː|qo‘lqop|Ich finde nur einen Handschuh.|Faqat bitta qo‘lqopni topyapman.|die Handschuhe
@5|Aksessuarlar va ranglar
die Tasche|ˈtaʃə|sumka; cho‘ntak|Meine Tasche ist voller Bücher.|Sumkam kitobga to‘la.|die Taschen
der Rucksack|ˈʁʊkzak|ryukzak|Im Rucksack ist mein Mittagessen.|Tushligim ryukzakda.|die Rucksäcke
der Gürtel|ˈɡʏʁtl̩|kamar|Der Gürtel ist zu eng.|Kamar juda tor.|die Gürtel
die Brille|ˈbʁɪlə|ko‘zoynak|Ohne Brille sehe ich wenig.|Ko‘zoynaksiz yaxshi ko‘rmayman.|die Brillen
die Sonnenbrille|ˈzɔnənbʁɪlə|quyosh ko‘zoynagi|Wo ist meine Sonnenbrille?|Quyosh ko‘zoynagim qayerda?|die Sonnenbrillen
der Ring|ʁɪŋ|uzuk|Der Ring passt nicht mehr.|Uzuk endi sig‘mayapti.|die Ringe
die Kette|ˈkɛtə|zanjir; marjon|Meine Mutter trägt eine silberne Kette.|Onam kumush marjon taqadi.|die Ketten
die Größe|ˈɡʁøːsə|o‘lcham; kattalik|Haben Sie diese Größe noch?|Sizda bu o‘lcham hali bormi?|die Größen
die Farbe|ˈfaʁbə|rang|Welche Farbe magst du?|Qaysi rangni yoqtirasan?|die Farben
rot|ʁoːt|qizil|Deine Nase ist ganz rot.|Burning qip-qizil bo‘libdi.|
blau|blaʊ̯|ko‘k|Der Himmel ist heute blau.|Bugun osmon ko‘m-ko‘k.|
grün|ɡʁyːn|yashil|Mein Fahrrad ist grün.|Velosipedim yashil.|
gelb|ɡɛlp|sariq|Die gelben Blumen sind für dich.|Sariq gullar sen uchun.|
weiß|vaɪ̯s|oq|Das weiße Hemd ist sauber.|Oq ko‘ylak toza.|
schwarz|ʃvaʁts|qora|Ich suche eine schwarze Hose.|Qora shim qidiryapman.|
grau|ɡʁaʊ̯|kulrang|Opas Haare sind grau.|Bobomning sochlari oqargan.|
braun|bʁaʊ̯n|jigarrang|Unsere Tür ist braun.|Eshigimiz jigarrang.|
rosa|ˈʁoːza|pushti|Meine Tochter möchte rosa Schuhe.|Qizim pushti oyoq kiyim istaydi.|
lila|ˈliːla|binafsharang|Die lila Jacke gefällt mir.|Binafsharang kurtka menga yoqdi.|
orange|oˈʁãːʒə|to‘q sariq|Sein Rucksack ist orange.|Uning ryukzagi to‘q sariq.|
@5|Xarid qilish
kaufen|ˈkaʊ̯fən|sotib olmoq|Ich kaufe nur das Nötige.|Men faqat kerakli narsalarni sotib olaman.|
verkaufen|fɛɐ̯ˈkaʊ̯fən|sotmoq|Verkaufen Sie auch Briefmarken?|Siz pochta markalarini ham sotasizmi?|
einkaufen|ˈaɪ̯nkaʊ̯fən|bozorlik qilmoq|Wir kaufen am Samstag ein.|Biz shanba kuni bozorlik qilamiz.|kauft ein; hat eingekauft
kosten|ˈkɔstən|narxi … bo‘lmoq|Was kosten diese Schuhe?|Bu oyoq kiyim qancha turadi?|
zahlen|ˈtsaːlən|to‘lamoq|Wir zahlen zusammen.|Biz birga to‘laymiz.|
nehmen|ˈneːmən|olmoq|Ich nehme die blaue Jacke.|Men ko‘k kurtkani olaman.|nimmt; nahm; hat genommen
geben|ˈɡeːbən|bermoq|Gib mir bitte die kleine Tasche.|Iltimos, kichik sumkani menga ber.|gibt; gab; hat gegeben
tragen|ˈtʁaːɡən|kiymoq; ko‘tarmoq|Heute trage ich meine neuen Schuhe.|Bugun yangi oyoq kiyimimni kiydim.|trägt; trug; hat getragen
passen|ˈpasən|mos kelmoq; sig‘moq|Die Hose passt perfekt.|Shim juda mos tushdi.|
gefallen|ɡəˈfalən|yoqmoq|Gefällt dir dieser Mantel?|Bu palto senga yoqdimi?|gefällt; gefiel; hat gefallen
anprobieren|ˈanpʁobiːʁən|kiyib ko‘rmoq|Darf ich das Kleid anprobieren?|Ko‘ylakni kiyib ko‘rsam bo‘ladimi?|probiert an; hat anprobiert
anziehen|ˈantsiːən|kiymoq|Zieh bitte eine warme Jacke an.|Iltimos, issiq kurtka kiy.|zieht an; zog an; hat angezogen
ausziehen|ˈaʊ̯stsiːən|yechmoq|Zieh die nassen Schuhe aus.|Ho‘l oyoq kiyimingni yech.|zieht aus; zog aus; hat ausgezogen
umtauschen|ˈʊmtaʊ̯ʃən|almashtirib olmoq|Kann ich die Hose umtauschen?|Shimni almashtirib olsam bo‘ladimi?|tauscht um; hat umgetauscht
zurückgeben|tsuˈʁʏkɡeːbən|qaytarib bermoq|Ich möchte den Pullover zurückgeben.|Men sviterni qaytarib bermoqchiman.|gibt zurück; gab zurück; hat zurückgegeben
billig|ˈbɪlɪç|arzon|Die Bananen sind heute billig.|Bugun bananlar arzon.|
teuer|ˈtɔɪ̯ɐ|qimmat|Diese Schuhe sind mir zu teuer.|Bu oyoq kiyim men uchun juda qimmat.|
günstig|ˈɡʏnstɪç|hamyonbop; qulay|Hier gibt es günstige Jacken.|Bu yerda hamyonbop kurtkalar bor.|
bar|baːɐ̯|naqd|Ich zahle lieber bar.|Men naqd to‘lashni afzal ko‘raman.|
kostenlos|ˈkɔstənloːs|bepul|Die Lieferung ist kostenlos.|Yetkazib berish bepul.|
@5|O‘lcham va miqdor
lang|laŋ|uzun|Die Ärmel sind zu lang.|Yenglari juda uzun.|
kurz|kʊʁts|qisqa; kalta|Im Sommer trage ich kurze Hosen.|Yozda kalta shim kiyaman.|
eng|ɛŋ|tor|Die Schuhe sind vorn zu eng.|Oyoq kiyimning oldi juda tor.|
weit|vaɪ̯t|keng; uzoq|Das Hemd ist mir zu weit.|Ko‘ylak menga juda keng.|
bequem|bəˈkveːm|qulay|Meine alten Schuhe sind bequem.|Eski oyoq kiyimim qulay.|
weich|vaɪ̯ç|yumshoq|Dieser Schal ist besonders weich.|Bu sharf juda yumshoq.|
sauber|ˈzaʊ̯bɐ|toza|Ist mein weißes Hemd sauber?|Oq ko‘ylagim tozami?|
schmutzig|ˈʃmʊtsɪç|kir; iflos|Nach dem Spielen sind die Socken schmutzig.|O‘yindan keyin paypoqlar kir bo‘lgan.|
trocken|ˈtʁɔkən|quruq|Die Wäsche ist endlich trocken.|Kirlar nihoyat quridi.|
nass|nas|ho‘l|Meine Jacke ist vom Regen nass.|Kurtkam yomg‘irda ho‘l bo‘ldi.|
viel|fiːl|ko‘p|Ich habe heute viel eingekauft.|Bugun ko‘p narsa sotib oldim.|
wenig|ˈveːnɪç|oz; kam|Wir haben noch wenig Milch.|Bizda ozgina sut qoldi.|
mehr|meːɐ̯|ko‘proq; yana|Ich brauche mehr Platz.|Menga ko‘proq joy kerak.|
genug|ɡəˈnuːk|yetarli|Wir haben genug Brot.|Bizda non yetarli.|
alles|ˈaləs|hammasi|Ist das alles für heute?|Bugun uchun shu hammasimi?|
etwas|ˈɛtvas|biror narsa; biroz|Ich möchte etwas Süßes.|Men shirin narsa istayman.|
das Stück|ʃtʏk|dona; bo‘lak|Ein Stück Kuchen reicht mir.|Menga bir bo‘lak pirog yetadi.|die Stücke
das Kilo|ˈkiːlo|kilo|Ein Kilo Äpfel kostet zwei Euro.|Bir kilo olma ikki yevro turadi.|die Kilos; nach Zahlen Kilo
das Gramm|ɡʁam|gramm|Ich brauche zweihundert Gramm Käse.|Menga ikki yuz gramm pishloq kerak.|die Gramme; nach Zahlen Gramm
der Liter|ˈliːtɐ|litr|Wir kaufen einen Liter Milch.|Biz bir litr sut sotib olamiz.|die Liter
@6|Tana a’zolari
der Körper|ˈkœʁpɐ|tana|Mein Körper braucht eine Pause.|Tanamga dam kerak.|die Körper
der Kopf|kɔpf|bosh|Mein Kopf tut heute weh.|Bugun boshim og‘riyapti.|die Köpfe
das Gesicht|ɡəˈzɪçt|yuz|Wasch bitte dein Gesicht.|Iltimos, yuzingni yuv.|die Gesichter
das Auge|ˈaʊ̯ɡə|ko‘z|Meine Augen sind braun.|Ko‘zlarim jigarrang.|die Augen
das Ohr|oːɐ̯|quloq|Mein linkes Ohr tut weh.|Chap qulog‘im og‘riyapti.|die Ohren
die Nase|ˈnaːzə|burun|Meine Nase ist kalt.|Burnim sovuq.|die Nasen
der Mund|mʊnt|og‘iz|Mach bitte den Mund auf.|Iltimos, og‘zingni och.|die Münder
der Zahn|tsaːn|tish|Der erste Zahn ist schon da.|Birinchi tish allaqachon chiqqan.|die Zähne
die Zunge|ˈtsʊŋə|til (a’zo)|Nach dem Eis ist meine Zunge blau.|Muzqaymoqdan keyin tilim ko‘k bo‘lib qoldi.|die Zungen
das Haar|haːɐ̯|soch tolasi|In der Suppe ist ein Haar.|Sho‘rvada soch tolasi bor.|die Haare
der Hals|hals|bo‘yin; tomoq|Mein Schal hält den Hals warm.|Sharfim bo‘ynimni issiq tutadi.|die Hälse
die Schulter|ˈʃʊltɐ|yelka|Die Tasche hängt an meiner Schulter.|Sumka yelkamda osilib turibdi.|die Schultern
der Arm|aʁm|qo‘l (yelka–panja)|Mein rechter Arm ist müde.|O‘ng qo‘lim charchagan.|die Arme
die Hand|hant|qo‘l; kaft|Deine Hände sind eiskalt.|Qo‘llaring muzdek.|die Hände
der Finger|ˈfɪŋɐ|qo‘l barmog‘i|Der Ring sitzt am falschen Finger.|Uzuk boshqa barmoqqa taqilgan.|die Finger
der Bauch|baʊ̯x|qorin|Mein Bauch macht laute Geräusche.|Qornim baland ovozda quldirayapti.|die Bäuche
der Rücken|ˈʁʏkən|orqa; bel|Nach der Arbeit tut mein Rücken weh.|Ishdan keyin belim og‘riydi.|die Rücken
das Bein|baɪ̯n|oyoq (sondan past)|Meine Beine sind vom Laufen müde.|Yugurganimdan oyoqlarim charchagan.|die Beine
das Knie|kniː|tizza|Mein Knie tut beim Gehen weh.|Yurganimda tizzam og‘riydi.|die Knie
der Fuß|fuːs|oyoq panjasi|Meine Füße brauchen größere Schuhe.|Oyoqlarimga kattaroq oyoq kiyim kerak.|die Füße
@6|Sog‘liq
die Zehe|ˈtseːə|oyoq barmog‘i|Die kleine Zehe tut weh.|Oyoqning kichik barmog‘i og‘riyapti.|die Zehen
die Haut|haʊ̯t|teri|Meine Haut ist im Winter trocken.|Qishda terim quruq bo‘ladi.|die Häute
das Herz|hɛʁts|yurak|Mein Herz schlägt schnell.|Yuragim tez uryapti.|die Herzen
der Schmerz|ʃmɛʁts|og‘riq|Der Schmerz ist jetzt schwächer.|Og‘riq hozir pasaydi.|die Schmerzen
die Kopfschmerzen|ˈkɔpfʃmɛʁtsən|bosh og‘rig‘i|Wegen der Kopfschmerzen bleibe ich daheim.|Bosh og‘rig‘i sababli uyda qolaman.|Plural; Singular: der Kopfschmerz
die Bauchschmerzen|ˈbaʊ̯xʃmɛʁtsən|qorin og‘rig‘i|Das Kind hat Bauchschmerzen.|Bolaning qorni og‘riyapti.|Plural; Singular: der Bauchschmerz
das Fieber|ˈfiːbɐ|isitma|Heute habe ich kein Fieber mehr.|Bugun endi isitmam yo‘q.|kein Plural
der Husten|ˈhuːstən|yo‘tal|Der Husten stört mich nachts.|Yo‘tal meni tunda bezovta qiladi.|kein Plural
der Schnupfen|ˈʃnʊpfn̩|tumov|Mit Schnupfen rieche ich wenig.|Tumov bo‘lganda hidni yaxshi sezmayman.|kein Plural
die Erkältung|ɛɐ̯ˈkɛltʊŋ|shamollash|Meine Erkältung ist schon besser.|Shamollashim ancha yengillashdi.|die Erkältungen
die Krankheit|ˈkʁaŋkhaɪ̯t|kasallik|Die Ärztin erklärt mir die Krankheit.|Shifokor kasallikni menga tushuntiryapti.|die Krankheiten
die Gesundheit|ɡəˈzʊnthaɪ̯t|sog‘liq|Gesundheit ist mir wichtig.|Sog‘liq men uchun muhim.|kein Plural
die Apotheke|apoˈteːkə|dorixona|Die Apotheke ist noch offen.|Dorixona hali ochiq.|die Apotheken
das Medikament|medikaˈmɛnt|dori|Wie heißt dieses Medikament?|Bu dorining nomi nima?|die Medikamente
die Tablette|taˈblɛtə|tabletka|Die Tabletten liegen im Schrank.|Tabletkalar shkafda turibdi.|die Tabletten
das Rezept|ʁeˈtsɛpt|retsept|Für dieses Medikament brauche ich ein Rezept.|Bu doriga menga retsept kerak.|die Rezepte
das Pflaster|ˈpflastɐ|yopishqoq plastir|Hast du ein Pflaster für mich?|Menga plastiring bormi?|die Pflaster
das Krankenhaus|ˈkʁaŋkənhaʊ̯s|kasalxona|Meine Schwester arbeitet im Krankenhaus.|Opam kasalxonada ishlaydi.|die Krankenhäuser
die Praxis|ˈpʁaksɪs|shifokor qabulxonasi|Die Praxis öffnet um acht Uhr.|Shifokor qabulxonasi soat sakkizda ochiladi.|die Praxen
der Termin|tɛʁˈmiːn|belgilangan uchrashuv vaqti|Ich habe morgen einen Termin beim Arzt.|Ertaga shifokor qabuliga yozilganman.|die Termine
@6|Shifokor bilan muloqot
der Patient|paˈtsi̯ɛnt|bemor (erkak)|Der Patient wartet im Flur.|Bemor yo‘lakda kutyapti.|die Patienten
die Patientin|paˈtsi̯ɛntɪn|bemor (ayol)|Die Patientin spricht mit der Ärztin.|Bemor shifokor bilan gaplashyapti.|die Patientinnen
der Zahnarzt|ˈtsaːnʔaːɐ̯tst|tish shifokori (erkak)|Der Zahnarzt schaut meine Zähne an.|Tish shifokori tishlarimni ko‘ryapti.|die Zahnärzte
die Zahnärztin|ˈtsaːnʔɛːɐ̯tstɪn|tish shifokori (ayol)|Meine Zahnärztin erklärt alles ruhig.|Tish shifokorim hammasini xotirjam tushuntiradi.|die Zahnärztinnen
krank|kʁaŋk|kasal|Ich bin krank und bleibe im Bett.|Men kasalman, yotoqda qolaman.|
gesund|ɡəˈzʊnt|sog‘lom|Zum Glück sind alle wieder gesund.|Yaxshiyamki, hamma yana sog‘aygan.|
müde|ˈmyːdə|charchagan; uyqusi kelgan|Nach dem Kurs bin ich müde.|Kursdan keyin charchayman.|
wach|vax|uyg‘oq|Das Baby ist schon wieder wach.|Chaqaloq yana uyg‘oq.|
fit|fɪt|tetik; yaxshi jismoniy holatda|Nach dem Urlaub fühle ich mich fit.|Ta’tildan keyin o‘zimni tetik his qilyapman.|
schwach|ʃvax|kuchsiz; holsiz|Heute fühle ich mich noch schwach.|Bugun hali o‘zimni holsiz his qilyapman.|
stark|ʃtaʁk|kuchli|Mein Bruder ist ziemlich stark.|Akam ancha kuchli.|
besser|ˈbɛsɐ|yaxshiroq|Geht es dir heute besser?|Bugun ahvoling yaxshiroqmi?|
schlimm|ʃlɪm|yomon; og‘ir|Ist der Schmerz sehr schlimm?|Og‘riq juda kuchlimi?|
weh tun|ˈveː tuːn|og‘rimoq|Wo tut es dir weh?|Qayering og‘riyapti?|tut weh; tat weh; hat wehgetan
sich fühlen|zɪç ˈfyːlən|o‘zini his qilmoq|Ich fühle mich heute gut.|Bugun o‘zimni yaxshi his qilyapman.|fühlt sich; hat sich gefühlt
schlafen|ˈʃlaːfn̩|uxlamoq|Mein Bruder schläft wie ein Stein.|Akam toshdek qotib uxlayapti.|schläft; schlief; hat geschlafen
sich ausruhen|zɪç ˈaʊ̯sʁuːən|dam olmoq|Nach dem Essen ruhe ich mich aus.|Ovqatdan keyin dam olaman.|ruht sich aus; hat sich ausgeruht
husten|ˈhuːstən|yo‘talmoq|Ich muss nachts oft husten.|Men tunda tez-tez yo‘talaman.|
niesen|ˈniːzən|aksirmoq|Meine Schwester niest dreimal.|Singlim uch marta aksiradi.|
atmen|ˈaːtmən|nafas olmoq|Bitte atmen Sie ruhig.|Iltimos, xotirjam nafas oling.|
@6|Gigiyena
waschen|ˈvaʃən|yuvmoq|Ich wasche vor dem Essen die Hände.|Ovqatdan oldin qo‘limni yuvaman.|wäscht; wusch; hat gewaschen
duschen|ˈduːʃən|dush qabul qilmoq|Nach dem Sport dusche ich.|Sportdan keyin dush qabul qilaman.|
baden|ˈbaːdən|cho‘milmoq; vanna qabul qilmoq|Das Baby badet gern.|Chaqaloq cho‘milishni yoqtiradi.|
kämmen|ˈkɛmən|taramoq|Ich kämme morgens meine Haare.|Ertalab sochimni tarayman.|
sich rasieren|zɪç ʁaˈziːʁən|soqolini olmoq|Papa rasiert sich jeden Morgen.|Dadam har kuni ertalab soqolini oladi.|rasiert sich; hat sich rasiert
die Seife|ˈzaɪ̯fə|sovun|Die Seife riecht nach Zitrone.|Sovundan limon hidi keladi.|die Seifen
das Shampoo|ˈʃampuː|shampun|Mein Shampoo ist fast leer.|Shampunim deyarli tugagan.|die Shampoos
die Zahnbürste|ˈtsaːnbyʁstə|tish cho‘tkasi|Die blaue Zahnbürste gehört mir.|Ko‘k tish cho‘tkasi meniki.|die Zahnbürsten
die Zahnpasta|ˈtsaːnpasta|tish pastasi|Die Zahnpasta liegt neben dem Waschbecken.|Tish pastasi qo‘lyuvgich yonida.|die Zahnpasten
das Handtuch|ˈhanttuːx|sochiq|Dein Handtuch hängt an der Tür.|Sochig‘ing eshikda osilgan.|die Handtücher
der Kamm|kam|taroq|Mein Kamm ist in der kleinen Tasche.|Tarog‘im kichik sumkada.|die Kämme
die Bürste|ˈbʏʁstə|cho‘tka|Diese Bürste ist für die Haare.|Bu cho‘tka soch uchun.|die Bürsten
die Dusche|ˈduːʃə|dush|Die Dusche ist leider besetzt.|Afsuski, dush band.|die Duschen
die Badewanne|ˈbaːdəvanə|vanna|Die Badewanne ist voller Wasser.|Vanna suvga to‘la.|die Badewannen
das Waschbecken|ˈvaʃbɛkən|qo‘lyuvgich|Im Waschbecken liegt ein Spielzeug.|Qo‘lyuvgichda o‘yinchoq yotibdi.|die Waschbecken
die Toilette|to̯aˈlɛtə|hojatxona|Wo ist bitte die Toilette?|Kechirasiz, hojatxona qayerda?|die Toiletten
das Toilettenpapier|to̯aˈlɛtn̩papiːɐ̯|hojatxona qog‘ozi|Wir müssen Toilettenpapier kaufen.|Hojatxona qog‘ozi sotib olishimiz kerak.|die Toilettenpapiere (Sorten)
das Taschentuch|ˈtaʃn̩tuːx|dastro‘mol; qog‘oz ro‘molcha|Hast du ein sauberes Taschentuch?|Toza ro‘molchang bormi?|die Taschentücher
die Creme|kʁeːm|krem|Diese Creme ist für trockene Hände.|Bu krem quruq qo‘llar uchun.|die Cremes
der Schlaf|ʃlaːf|uyqu|Nach wenig Schlaf bin ich langsam.|Kam uxlasam, sust bo‘laman.|kein Plural
@6|Harakat va holat
der Sport|ʃpɔʁt|sport|Sport macht mir Spaß.|Sport menga yoqadi.|kein Plural
der Fußball|ˈfuːsbal|futbol; futbol to‘pi|Am Freitag spielen wir Fußball.|Juma kuni futbol o‘ynaymiz.|die Fußbälle (Bälle)
der Ball|bal|to‘p|Der Ball rollt unter das Auto.|To‘p mashina tagiga dumalab ketyapti.|die Bälle
das Schwimmbad|ˈʃvɪmbaːt|basseyn; suzish havzasi|Das Schwimmbad ist sonntags offen.|Basseyn yakshanba kunlari ochiq.|die Schwimmbäder
schwimmen|ˈʃvɪmən|suzmoq|Ich schwimme lieber im Schwimmbad.|Men basseynda suzishni afzal ko‘raman.|schwimmt; schwamm; ist/hat geschwommen
laufen|ˈlaʊ̯fən|yugurmoq; piyoda yurmoq|Wir laufen langsam durch den Park.|Biz bog‘ bo‘ylab sekin yuguryapmiz.|läuft; lief; ist gelaufen
rennen|ˈʁɛnən|chopmoq|Renn nicht auf der Treppe!|Zinapoyada chopma!|rennt; rannte; ist gerannt
tanzen|ˈtantsən|raqsga tushmoq|Oma tanzt besser als ich.|Buvim mendan yaxshiroq raqsga tushadi.|
springen|ˈʃpʁɪŋən|sakramoq|Der Hund springt über die Tasche.|It sumka ustidan sakrayapti.|springt; sprang; ist gesprungen
spazieren gehen|ʃpaˈtsiːʁən ˌɡeːən|sayr qilmoq|Abends gehen wir gern spazieren.|Kechqurun sayr qilishni yoqtiramiz.|geht spazieren; ging spazieren; ist spazieren gegangen
sich bewegen|zɪç bəˈveːɡən|harakat qilmoq|Im Büro bewege ich mich wenig.|Ofisda kam harakat qilaman.|bewegt sich; hat sich bewegt
trainieren|tʁɛˈniːʁən|mashq qilmoq; shug‘ullanmoq|Wir trainieren jeden Dienstag.|Biz har seshanba mashq qilamiz.|
der Spaziergang|ˈʃpaːtsiːɐ̯ɡaŋ|sayr|Ein kurzer Spaziergang tut mir gut.|Qisqa sayr menga yaxshi ta’sir qiladi.|die Spaziergänge
die Hilfe|ˈhɪlfə|yordam|Danke für deine schnelle Hilfe.|Tez yordam berganing uchun rahmat.|die Hilfen
der Notfall|ˈnoːtfal|favqulodda holat|Ist das ein Notfall?|Bu favqulodda holatmi?|die Notfälle
der Unfall|ˈʊnfal|baxtsiz hodisa; avariya|Vor der Schule war ein Unfall.|Maktab oldida avariya bo‘ldi.|die Unfälle
vorsichtig|ˈfoːɐ̯zɪçtɪç|ehtiyotkor|Sei auf der Treppe vorsichtig.|Zinapoyada ehtiyot bo‘l.|
ruhig|ˈʁuːɪç|tinch; xotirjam|Hier kann ich ruhig schlafen.|Bu yerda tinch uxlay olaman.|
warm|vaʁm|iliq; issiq|Heute bleiben meine Füße warm.|Bugun oyoqlarim issiq turadi.|
regelmäßig|ˈʁeːɡl̩mɛːsɪç|muntazam|Ich gehe regelmäßig schwimmen.|Men muntazam ravishda suzishga boraman.|
@7|Shahar joylari
die Straße|ˈʃtʁaːsə|ko‘cha|Unsere Straße ist abends ruhig.|Ko‘chamiz kechqurun tinch bo‘ladi.|die Straßen
der Platz|plats|maydon; joy|Auf dem Platz spielen Kinder.|Maydonda bolalar o‘ynayapti.|die Plätze
der Park|paʁk|istirohat bog‘i|Im Park gibt es einen kleinen See.|Bog‘da kichik ko‘l bor.|die Parks
die Brücke|ˈbʁʏkə|ko‘prik|Wir gehen über die alte Brücke.|Biz eski ko‘prikdan o‘tyapmiz.|die Brücken
der Fluss|flʊs|daryo|Der Fluss fließt durch die Stadt.|Daryo shahar ichidan oqib o‘tadi.|die Flüsse
der See|zeː|ko‘l|Am See essen wir unser Brot.|Ko‘l bo‘yida nonimizni yeymiz.|die Seen
das Zentrum|ˈtsɛntʁʊm|markaz|Im Zentrum gibt es viele Cafés.|Markazda kafelar ko‘p.|die Zentren
die Innenstadt|ˈɪnənʃtat|shaharning markaziy qismi|Die Innenstadt ist heute voll.|Bugun shahar markazi gavjum.|die Innenstädte
das Dorf|dɔʁf|qishloq|Meine Tante lebt in einem Dorf.|Xolam qishloqda yashaydi.|die Dörfer
die Post|pɔst|pochta|Die Post ist neben der Bank.|Pochta bank yonida.|kein Plural
die Bank|baŋk|bank; skameyka|Ich hole Geld bei der Bank.|Bankdan pul olaman.|die Banken (Geldinstitut); die Bänke (Sitzmöbel)
der Geldautomat|ˈɡɛltʔaʊ̯tomaːt|bankomat|Der Geldautomat funktioniert nicht.|Bankomat ishlamayapti.|die Geldautomaten
die Polizei|poliˈtsaɪ̯|politsiya|Die Polizei hilft den Kindern.|Politsiya bolalarga yordam beryapti.|kein Plural
das Rathaus|ˈʁaːthaʊ̯s|shahar hokimiyati binosi|Das Rathaus steht am Marktplatz.|Hokimiyat binosi bozor maydonida.|die Rathäuser
die Bibliothek|biblioˈteːk|kutubxona|In der Bibliothek ist es leise.|Kutubxonada jimjit.|die Bibliotheken
das Museum|muˈzeːʊm|muzey|Das Museum zeigt alte Fahrräder.|Muzeyda eski velosipedlar namoyish etiladi.|die Museen
das Kino|ˈkiːno|kinoteatr|Heute gehen wir ins Kino.|Bugun kinoga boramiz.|die Kinos
das Theater|teˈaːtɐ|teatr|Vor dem Theater wartet meine Freundin.|Teatr oldida dugonam kutyapti.|die Theater
die Kirche|ˈkɪʁçə|cherkov|Die alte Kirche hat einen hohen Turm.|Eski cherkovning baland minorasi bor.|die Kirchen
die Moschee|moˈʃeː|masjid|Die Moschee ist in dieser Straße.|Masjid shu ko‘chada.|die Moscheen
das Hotel|hoˈtɛl|mehmonxona|Unser Hotel liegt am Bahnhof.|Mehmonxonamiz vokzal yonida.|die Hotels
die Haltestelle|ˈhaltəʃtɛlə|bekat|An der Haltestelle stehen viele Leute.|Bekatda ko‘p odam turibdi.|die Haltestellen
der Bahnhof|ˈbaːnhoːf|vokzal|Der Bahnhof ist zehn Minuten entfernt.|Vokzal o‘n daqiqalik masofada.|die Bahnhöfe
der Flughafen|ˈfluːkhaːfn̩|aeroport|Zum Flughafen nehmen wir ein Taxi.|Aeroportga taksida boramiz.|die Flughäfen
die Kreuzung|ˈkʁɔɪ̯tsʊŋ|chorraha|An der Kreuzung gehen wir links.|Chorrahada chapga burilamiz.|die Kreuzungen
die Ampel|ˈampl̩|svetofor|Die Ampel ist noch rot.|Svetofor hali qizil.|die Ampeln
der Weg|veːk|yo‘l|Kennst du den Weg zur Schule?|Maktabga boradigan yo‘lni bilasanmi?|die Wege
der Eingang|ˈaɪ̯nɡaŋ|kirish joyi|Der Eingang ist auf der anderen Seite.|Kirish joyi boshqa tomonda.|die Eingänge
der Ausgang|ˈaʊ̯sɡaŋ|chiqish joyi|Wir treffen uns am Ausgang.|Chiqish joyida uchrashamiz.|die Ausgänge
der Parkplatz|ˈpaʁkplats|avtoturargoh|Auf dem Parkplatz ist noch Platz.|Avtoturargohda hali joy bor.|die Parkplätze
@7|Transport
das Auto|ˈaʊ̯to|avtomobil|Unser Auto steht vor dem Haus.|Mashinamiz uy oldida turibdi.|die Autos
der Bus|bʊs|avtobus|Dieser Bus fährt zum Bahnhof.|Bu avtobus vokzalga boradi.|die Busse
der Zug|tsuːk|poyezd|Der Zug kommt fünf Minuten später.|Poyezd besh daqiqa kechroq keladi.|die Züge
die Straßenbahn|ˈʃtʁaːsn̩baːn|tramvay|Mit der Straßenbahn bin ich schneller.|Tramvayda tezroq yetib boraman.|die Straßenbahnen
die U-Bahn|ˈuːbaːn|metro|Die U-Bahn fährt alle fünf Minuten.|Metro har besh daqiqada qatnaydi.|die U-Bahnen
die S-Bahn|ˈɛsbaːn|shahar va shahar atrofi poyezdi|Wir fahren mit der S-Bahn ins Zentrum.|Markazga shahar poyezdida boramiz.|die S-Bahnen
das Taxi|ˈtaksi|taksi|Das Taxi wartet vor dem Hotel.|Taksi mehmonxona oldida kutyapti.|die Taxis
das Fahrrad|ˈfaːɐ̯ʁaːt|velosiped|Mein Fahrrad hat einen platten Reifen.|Velosipedimning shinasi damini yo‘qotgan.|die Fahrräder
das Motorrad|ˈmoːtoːɐ̯ʁaːt|mototsikl|Sein Motorrad ist sehr laut.|Uning mototsikli juda shovqinli.|die Motorräder
das Flugzeug|ˈfluːktsɔɪ̯k|samolyot|Das Flugzeug fliegt über unser Haus.|Samolyot uyimiz ustidan uchib o‘tyapti.|die Flugzeuge
das Schiff|ʃɪf|kema|Vom Ufer sehen wir ein Schiff.|Qirg‘oqdan kema ko‘ryapmiz.|die Schiffe
die Fahrkarte|ˈfaːɐ̯kaʁtə|yo‘l chiptasi|Ich kaufe eine Fahrkarte nach Berlin.|Berlinga chipta sotib olaman.|die Fahrkarten
das Ticket|ˈtɪkət|chipta|Mein Ticket ist auf dem Handy.|Chiptam telefonimda.|die Tickets
der Fahrplan|ˈfaːɐ̯plaːn|qatnov jadvali|Der Fahrplan hängt an der Haltestelle.|Qatnov jadvali bekatda osilgan.|die Fahrpläne
das Gleis|ɡlaɪ̯s|temiryo‘l izi; poyezd yo‘li|Unser Zug fährt von Gleis drei.|Poyezdimiz uchinchi yo‘ldan jo‘naydi.|die Gleise
der Bahnsteig|ˈbaːnʃtaɪ̯k|perron|Auf dem Bahnsteig ist es kalt.|Perronda sovuq.|die Bahnsteige
die Fahrt|faːɐ̯t|yo‘l safari; qatnov|Die Fahrt dauert eine halbe Stunde.|Yo‘l yarim soat davom etadi.|die Fahrten
die Verspätung|fɛɐ̯ˈʃpɛːtʊŋ|kechikish|Unser Bus hat heute Verspätung.|Avtobusimiz bugun kechikyapti.|die Verspätungen
der Verkehr|fɛɐ̯ˈkeːɐ̯|yo‘l harakati|Morgens gibt es hier viel Verkehr.|Ertalab bu yerda transport ko‘p bo‘ladi.|kein Plural
der Stau|ʃtaʊ̯|tirbandlik|Wir stehen seit zehn Minuten im Stau.|O‘n daqiqadan beri tirbandlikda turibmiz.|die Staus
@7|Yo‘l harakatlari
fahren|ˈfaːʁən|transportda bormoq; haydamoq|Fährst du mit dem Bus zur Arbeit?|Ishga avtobusda borasanmi?|fährt; fuhr; ist/hat gefahren
fliegen|ˈfliːɡən|uchmoq|Im Juni fliegen wir nach Taschkent.|Iyunda Toshkentga uchamiz.|fliegt; flog; ist geflogen
reisen|ˈʁaɪ̯zən|sayohat qilmoq|Wir reisen gern mit dem Zug.|Poyezdda sayohat qilishni yoqtiramiz.|
einsteigen|ˈaɪ̯nʃtaɪ̯ɡən|transportga chiqmoq|Bitte steigen Sie vorn ein.|Iltimos, old tomondan chiqing.|steigt ein; stieg ein; ist eingestiegen
aussteigen|ˈaʊ̯sʃtaɪ̯ɡən|transportdan tushmoq|Wir steigen an der nächsten Haltestelle aus.|Keyingi bekatda tushamiz.|steigt aus; stieg aus; ist ausgestiegen
umsteigen|ˈʊmʃtaɪ̯ɡən|boshqa transportga o‘tmoq|Am Bahnhof musst du umsteigen.|Vokzalda boshqa transportga o‘tishing kerak.|steigt um; stieg um; ist umgestiegen
ankommen|ˈankɔmən|yetib kelmoq|Wann kommt dein Zug an?|Poyezding qachon yetib keladi?|kommt an; kam an; ist angekommen
abfahren|ˈapfaːʁən|jo‘nab ketmoq|Der letzte Bus fährt bald ab.|Oxirgi avtobus tez orada jo‘naydi.|fährt ab; fuhr ab; ist abgefahren
warten|ˈvaʁtən|kutmoq|Ich warte vor dem Eingang auf dich.|Seni kirish joyi oldida kutaman.|
halten|ˈhaltn̩|to‘xtamoq; ushlamoq|Hält dieser Zug in Potsdam?|Bu poyezd Potsdamda to‘xtaydimi?|hält; hielt; hat gehalten
parken|ˈpaʁkən|mashinani qo‘yib turmoq|Hier darfst du nicht parken.|Bu yerga mashina qo‘yish mumkin emas.|
abbiegen|ˈapbiːɡən|burilmoq|Bieg an der Ampel rechts ab.|Svetoforda o‘ngga buril.|biegt ab; bog ab; ist abgebogen
überqueren|yːbɐˈkveːʁən|kesib o‘tmoq|Wir überqueren die Straße bei Grün.|Ko‘chani yashil chiroqda kesib o‘tamiz.|
bringen|ˈbʁɪŋən|olib kelmoq; eltmoq|Papa bringt mich zum Bahnhof.|Dadam meni vokzalga olib boradi.|bringt; brachte; hat gebracht
holen|ˈhoːlən|borib olib kelmoq|Ich hole schnell mein Fahrrad.|Tezda velosipedimni olib kelaman.|
abholen|ˈaphoːlən|borib olib ketmoq; kutib olmoq|Meine Schwester holt mich am Flughafen ab.|Opam meni aeroportda kutib oladi.|holt ab; hat abgeholt
links|lɪŋks|chapda; chapga|Die Post ist links.|Pochta chapda.|
rechts|ʁɛçts|o‘ngda; o‘ngga|Rechts sehen Sie das Rathaus.|O‘ng tomonda hokimiyat binosini ko‘rasiz.|
geradeaus|ɡəˈʁaːdəʔaʊ̯s|to‘g‘riga|Gehen Sie noch hundert Meter geradeaus.|Yana yuz metr to‘g‘riga yuring.|
zurück|tsuˈʁʏk|orqaga; qaytib|Ich gehe kurz nach Hause zurück.|Men qisqa vaqtga uyga qaytaman.|
@7|Safar
die Reise|ˈʁaɪ̯zə|sayohat|Unsere Reise beginnt am Montag.|Sayohatimiz dushanba kuni boshlanadi.|die Reisen
der Urlaub|ˈuːɐ̯laʊ̯p|ta’til|Im Urlaub schlafe ich länger.|Ta’tilda uzoqroq uxlayman.|die Urlaube
der Koffer|ˈkɔfɐ|jomadon|Mein Koffer ist leider zu schwer.|Afsuski, jomadonim juda og‘ir.|die Koffer
das Gepäck|ɡəˈpɛk|yuk; bagaj|Unser Gepäck ist schon im Taxi.|Yukimiz allaqachon taksida.|kein Plural
der Pass|pas|pasport|Zeigen Sie bitte Ihren Pass.|Iltimos, pasportingizni ko‘rsating.|die Pässe
der Ausweis|ˈaʊ̯svaɪ̯s|shaxsni tasdiqlovchi hujjat|Mein Ausweis ist in der Geldbörse.|Hujjatim hamyonimda.|die Ausweise
die Rezeption|ʁetsɛpˈtsi̯oːn|qabul bo‘limi (mehmonxonada)|An der Rezeption bekomme ich den Schlüssel.|Kalitni qabul bo‘limidan olaman.|die Rezeptionen
das Einzelzimmer|ˈaɪ̯ntsl̩tsɪmɐ|bir kishilik xona|Ein Einzelzimmer ist noch frei.|Bitta bir kishilik xona hali bo‘sh.|die Einzelzimmer
das Doppelzimmer|ˈdɔpl̩tsɪmɐ|ikki kishilik xona|Wir möchten ein Doppelzimmer mit Bad.|Hammomli ikki kishilik xona istaymiz.|die Doppelzimmer
die Reservierung|ʁezɛʁˈviːʁʊŋ|band qilish; bron|Ich habe eine Reservierung für zwei Nächte.|Ikki kechaga xona band qilganman.|die Reservierungen
buchen|ˈbuːxən|band qilmoq; bron qilmoq|Wir buchen das Hotel im Internet.|Mehmonxonani internet orqali band qilamiz.|
reservieren|ʁezɛʁˈviːʁən|band qilib qo‘ymoq|Ich reserviere einen Tisch für vier.|To‘rt kishilik stol band qilaman.|
übernachten|yːbɐˈnaxtən|tunab qolmoq|Wir übernachten bei Freunden.|Do‘stlarimiznikida tunab qolamiz.|
packen|ˈpakən|joylamoq; yig‘moq|Ich packe meinen Koffer heute Abend.|Jomadonimni bugun kechqurun yig‘aman.|
vergessen|fɛɐ̯ˈɡɛsn̩|unutmoq|Vergiss bitte deinen Pass nicht.|Iltimos, pasportingni unutma.|vergisst; vergaß; hat vergessen
verlieren|fɛɐ̯ˈliːʁən|yo‘qotmoq|Ich verliere oft meine Fahrkarte.|Men yo‘l chiptamni tez-tez yo‘qotaman.|verliert; verlor; hat verloren
mitnehmen|ˈmɪtneːmən|o‘zi bilan olmoq|Nimm bitte genug Wasser mit.|Iltimos, o‘zing bilan yetarli suv ol.|nimmt mit; nahm mit; hat mitgenommen
zurückkommen|tsuˈʁʏkkɔmən|qaytib kelmoq|Wir kommen am Sonntag zurück.|Biz yakshanba kuni qaytib kelamiz.|kommt zurück; kam zurück; ist zurückgekommen
der Stadtplan|ˈʃtatplaːn|shahar xaritasi|Auf dem Stadtplan finde ich unser Hotel.|Shahar xaritasidan mehmonxonamizni topaman.|die Stadtpläne
die Information|ɪnfɔʁmaˈtsi̯oːn|ma’lumot|Diese Information ist sehr hilfreich.|Bu ma’lumot juda foydali.|die Informationen
@7|Yo‘lni aniqlashtirish
nah|naː|yaqin|Die Schule ist ganz nah.|Maktab juda yaqin.|
gegenüber|ɡeːɡn̩ˈʔyːbɐ|ro‘parasida|Die Bank ist gegenüber der Post.|Bank pochta ro‘parasida.|
über|ˈyːbɐ|ustida; ustidan|Über der Stadt fliegt ein Flugzeug.|Shahar ustida samolyot uchyapti.|
durch|dʊʁç|orqali; ichidan|Wir gehen durch den Park.|Biz bog‘ ichidan o‘tyapmiz.|
bis|bɪs|gacha|Fahren Sie bis zum Bahnhof.|Vokzalgacha boring.|
ab|ap|dan boshlab|Ab morgen fährt der Bus früher.|Ertadan avtobus ertaroq qatnaydi.|
wohin|voˈhɪn|qayerga|Wohin fährt dieser Zug?|Bu poyezd qayerga boradi?|
entfernt|ɛntˈfɛʁnt|uzoqda; masofada|Der See ist zwei Kilometer entfernt.|Ko‘l ikki kilometr uzoqlikda.|
zu Fuß|tsuː ˈfuːs|piyoda|Ich gehe jeden Tag zu Fuß.|Men har kuni piyoda yuraman.|
pünktlich|ˈpʏŋktlɪç|vaqtida|Heute ist der Zug pünktlich.|Bugun poyezd vaqtida keldi.|
@8|Kundalik odatlar
aufstehen|ˈaʊ̯fʃteːən|o‘rnidan turmoq|Ich stehe jeden Morgen um sieben auf.|Har kuni ertalab soat yettida turaman.|steht auf; stand auf; ist aufgestanden
aufwachen|ˈaʊ̯fvaxən|uyg‘onmoq|Sonntags wache ich ohne Wecker auf.|Yakshanba kunlari budilniksiz uyg‘onaman.|wacht auf; ist aufgewacht
einschlafen|ˈaɪ̯nʃlaːfn̩|uxlab qolmoq|Beim Film schläft Papa oft ein.|Kino ko‘rayotganda dadam tez-tez uxlab qoladi.|schläft ein; schlief ein; ist eingeschlafen
frühstücken|ˈfʁyːʃtʏkən|nonushta qilmoq|Wir frühstücken heute auf dem Balkon.|Bugun balkonda nonushta qilamiz.|
aufräumen|ˈaʊ̯fʁɔɪ̯mən|yig‘ishtirmoq|Vor dem Besuch räume ich auf.|Mehmonlar kelishidan oldin uy yig‘ishtiraman.|räumt auf; hat aufgeräumt
aufhören|ˈaʊ̯fhøːʁən|to‘xtatmoq; tugamoq|Der Regen hört endlich auf.|Yomg‘ir nihoyat to‘xtayapti.|hört auf; hat aufgehört
anfangen|ˈanfaŋən|boshlamoq; boshlanmoq|Wann fängt dein Unterricht an?|Darsing qachon boshlanadi?|fängt an; fing an; hat angefangen
fernsehen|ˈfɛʁnzeːən|televizor ko‘rmoq|Abends sehe ich selten fern.|Kechqurun kamdan-kam televizor ko‘raman.|sieht fern; sah fern; hat ferngesehen
anrufen|ˈanʁuːfn̩|qo‘ng‘iroq qilmoq|Ruf mich nach der Arbeit an.|Ishdan keyin menga qo‘ng‘iroq qil.|ruft an; rief an; hat angerufen
telefonieren|telefoˈniːʁən|telefonda gaplashmoq|Lola telefoniert mit ihrer Schwester.|Lola opasi bilan telefonda gaplashyapti.|
zuhören|ˈtsuːhøːʁən|diqqat bilan tinglamoq|Die Kinder hören der Oma zu.|Bolalar buvini diqqat bilan tinglashyapti.|hört zu; hat zugehört
mitbringen|ˈmɪtbʁɪŋən|o‘zi bilan olib kelmoq|Bring bitte dein Heft mit.|Iltimos, daftaringni olib kel.|bringt mit; brachte mit; hat mitgebracht
aufmachen|ˈaʊ̯fmaxən|ochmoq (og‘zaki)|Mach bitte das Fenster auf!|Iltimos, derazani ochib yubor!|macht auf; hat aufgemacht
zumachen|ˈtsuːmaxən|yopmoq (og‘zaki)|Mach die Tasche gut zu.|Sumkani yaxshilab yop.|macht zu; hat zugemacht
einschalten|ˈaɪ̯nʃaltn̩|yoqmoq (qurilmani)|Ich schalte morgens das Radio ein.|Ertalab radioni yoqaman.|schaltet ein; hat eingeschaltet
ausschalten|ˈaʊ̯sʃaltn̩|o‘chirmoq (qurilmani)|Schalte bitte das Licht aus.|Iltimos, chiroqni o‘chir.|schaltet aus; hat ausgeschaltet
benutzen|bəˈnʊtsən|foydalanmoq|Darf ich deinen Computer benutzen?|Kompyuteringdan foydalansam bo‘ladimi?|
planen|ˈplaːnən|rejalashtirmoq|Wir planen unser Wochenende zusammen.|Hafta oxirini birga rejalashtiramiz.|
treffen|ˈtʁɛfən|uchratmoq; uchrashmoq|Ich treffe meine Freundin im Park.|Dugonam bilan bog‘da uchrashaman.|trifft; traf; hat getroffen
einladen|ˈaɪ̯nlaːdn̩|taklif qilmoq (mehmonga)|Wir laden unsere Nachbarn zum Essen ein.|Qo‘shnilarimizni ovqatga taklif qilamiz.|lädt ein; lud ein; hat eingeladen
@8|Kundalik hayot va bo‘sh vaqt
der Alltag|ˈaltaːk|kundalik hayot|Im Alltag spreche ich viel Usbekisch.|Kundalik hayotda ko‘p o‘zbekcha gapiraman.|kein Plural
die Routine|ʁuˈtiːnə|odatiy tartib|Ein kurzer Spaziergang gehört zu meiner Routine.|Qisqa sayr kundalik odatimga kiradi.|die Routinen
der Wecker|ˈvɛkɐ|budilnik|Mein Wecker klingelt viel zu früh.|Budilnigim juda erta jiringlaydi.|die Wecker
das Handy|ˈhɛndi|mobil telefon|Mein Handy hat keinen Akku mehr.|Telefonimning quvvati tugagan.|die Handys
das Internet|ˈɪntɐnɛt|internet|Im Zug funktioniert das Internet nicht.|Poyezdda internet ishlamayapti.|kein Plural
die Nachricht|ˈnaːxʁɪçt|xabar|Ich schreibe dir eine kurze Nachricht.|Senga qisqa xabar yozyapman.|die Nachrichten
der Brief|bʁiːf|xat|Oma freut sich über meinen Brief.|Buvim xatimdan xursand.|die Briefe
die Briefmarke|ˈbʁiːfmaʁkə|pochta markasi|Auf dem Brief fehlt die Briefmarke.|Xatga pochta markasi yopishtirilmagan.|die Briefmarken
das Foto|ˈfoːto|fotosurat|Auf dem Foto lachen wir alle.|Suratda hammamiz kulyapmiz.|die Fotos
das Bild|bɪlt|rasm; tasvir|Mein Sohn malt ein Bild für Oma.|O‘g‘lim buvisi uchun rasm chizyapti.|die Bilder
die Musik|muˈziːk|musiqa|Beim Kochen höre ich Musik.|Ovqat pishirayotganda musiqa tinglayman.|kein Plural
das Lied|liːt|qo‘shiq|Dieses Lied singen wir im Kurs.|Bu qo‘shiqni kursda kuylaymiz.|die Lieder
der Film|fɪlm|film|Der Film beginnt in zehn Minuten.|Film o‘n daqiqadan keyin boshlanadi.|die Filme
die Serie|ˈzeːʁi̯ə|serial; turkum|Wir schauen eine deutsche Serie.|Nemischa serial tomosha qilyapmiz.|die Serien
das Hobby|ˈhɔbi|sevimli mashg‘ulot|Kochen ist mein liebstes Hobby.|Ovqat pishirish eng sevimli mashg‘ulotim.|die Hobbys
die Freizeit|ˈfʁaɪ̯tsaɪ̯t|bo‘sh vaqt|In meiner Freizeit male ich gern.|Bo‘sh vaqtimda rasm chizishni yoqtiraman.|kein Plural
das Spiel|ʃpiːl|o‘yin|Dieses Spiel kennt die ganze Familie.|Bu o‘yinni butun oilamiz biladi.|die Spiele
das Haustier|ˈhaʊ̯stiːɐ̯|uyda boqiladigan jonivor|Habt ihr ein Haustier?|Uyda jonivor boqasizlarmi?|die Haustiere
der Hund|hʊnt|it|Unser Hund wartet neben der Tür.|Itimiz eshik yonida kutyapti.|die Hunde
die Katze|ˈkatsə|mushuk|Die Katze schläft auf meinen Hausaufgaben.|Mushuk uy vazifalarim ustida uxlayapti.|die Katzen
@8|Istak, imkon va fikr
können|ˈkœnən|qila olmoq|Ich kann schon etwas Deutsch sprechen.|Men allaqachon biroz nemischa gapira olaman.|kann; konnte; hat gekonnt
müssen|ˈmʏsən|majbur bo‘lmoq; kerak bo‘lmoq|Morgen muss ich früh arbeiten.|Ertaga erta ishlashim kerak.|muss; musste; hat gemusst
dürfen|ˈdʏʁfən|ruxsat bo‘lmoq|Dürfen wir hier sitzen?|Bu yerda o‘tirsak bo‘ladimi?|darf; durfte; hat gedurft
sollen|ˈzɔlən|kerak bo‘lmoq (topshiriq, maslahat)|Ich soll meine Mutter anrufen.|Onamga qo‘ng‘iroq qilishim kerak.|soll; sollte; hat gesollt
wollen|ˈvɔlən|xohlamoq; niyat qilmoq|Wir wollen am Sonntag wandern.|Yakshanba kuni tabiat qo‘ynida piyoda sayr qilmoqchimiz.|will; wollte; hat gewollt
mögen|ˈmøːɡən|yoqtirmoq|Ich mag Tee mit Zitrone.|Men limonli choyni yoqtiraman.|mag; mochte; hat gemocht
wissen|ˈvɪsn̩|bilmoq (ma’lumotni)|Weißt du ihre Telefonnummer?|Uning telefon raqamini bilasanmi?|weiß; wusste; hat gewusst
kennen|ˈkɛnən|tanimoq; tanish bo‘lmoq|Kennst du unseren neuen Nachbarn?|Yangi qo‘shnimizni taniysanmi?|kennt; kannte; hat gekannt
denken|ˈdɛŋkən|o‘ylamoq|Ich denke oft an meine Familie.|Men oilam haqida tez-tez o‘ylayman.|denkt; dachte; hat gedacht
glauben|ˈɡlaʊ̯bən|ishonmoq; deb o‘ylamoq|Ich glaube, der Bus kommt gleich.|Menimcha, avtobus hozir keladi.|
hoffen|ˈhɔfən|umid qilmoq|Ich hoffe auf gutes Wetter.|Havo yaxshi bo‘lishiga umid qilaman.|
zählen|ˈtsɛːlən|sanamoq|Mein Sohn zählt bis zwanzig.|O‘g‘lim yigirmagacha sanaydi.|
dauern|ˈdaʊ̯ɐn|davom etmoq|Wie lange dauert die Pause?|Tanaffus qancha davom etadi?|
fehlen|ˈfeːlən|yetishmaslik; yo‘q bo‘lmoq|In meinem Heft fehlt eine Seite.|Daftarimda bir sahifa yo‘q.|
bekommen|bəˈkɔmən|olmoq; qo‘lga kiritmoq|Zum Geburtstag bekomme ich ein Buch.|Tug‘ilgan kunimga kitob olaman.|bekommt; bekam; hat bekommen
schicken|ˈʃɪkən|yubormoq|Schick mir bitte das Foto.|Iltimos, suratni menga yubor.|
kein|kaɪ̯n|hech qanday; … yo‘q|Heute habe ich keinen Unterricht.|Bugun darsim yo‘q.|
jeder|ˈjeːdɐ|har bir; har kim|Jeder Tag beginnt mit Tee.|Har kun choy bilan boshlanadi.|
wünschen|ˈvʏnʃən|tilamoq; istamoq|Ich wünsche dir einen schönen Tag.|Senga yaxshi kun tilayman.|
sich freuen|zɪç ˈfʁɔɪ̯ən|xursand bo‘lmoq|Ich freue mich auf das Wochenende.|Hafta oxirini xursand bo‘lib kutyapman.|freut sich; hat sich gefreut
@8|Ob-havo va tabiat
das Wetter|ˈvɛtɐ|ob-havo|Heute haben wir schönes Wetter.|Bugun havo yaxshi.|kein Plural
die Sonne|ˈzɔnə|quyosh|Die Sonne scheint durch das Fenster.|Quyosh derazadan nur sochyapti.|die Sonnen
der Regen|ˈʁeːɡən|yomg‘ir|Nach dem Regen riecht der Garten frisch.|Yomg‘irdan keyin bog‘dan yoqimli yangi hid keladi.|kein Plural
der Schnee|ʃneː|qor|Die Kinder spielen im Schnee.|Bolalar qorda o‘ynashyapti.|kein Plural
der Wind|vɪnt|shamol|Der Wind macht die Tür zu.|Shamol eshikni yopib yuboryapti.|die Winde
die Wolke|ˈvɔlkə|bulut|Diese Wolke sieht wie ein Hund aus.|Bu bulut itga o‘xshaydi.|die Wolken
der Himmel|ˈhɪml̩|osmon|Am Abend ist der Himmel rosa.|Kechqurun osmon pushti tusda.|die Himmel
der Frühling|ˈfʁyːlɪŋ|bahor|Im Frühling blüht unser Garten.|Bahorda bog‘imiz gullaydi.|die Frühlinge
der Sommer|ˈzɔmɐ|yoz|Im Sommer essen wir draußen.|Yozda tashqarida ovqatlanamiz.|die Sommer
der Herbst|hɛʁpst|kuz|Im Herbst sind die Blätter bunt.|Kuzda barglar rang-barang bo‘ladi.|die Herbste
der Winter|ˈvɪntɐ|qish|Im Winter brauche ich warme Socken.|Qishda menga issiq paypoq kerak.|die Winter
regnen|ˈʁeːɡnən|yomg‘ir yog‘moq|Es regnet, nimm einen Schirm mit.|Yomg‘ir yog‘yapti, soyabon ol.|
schneien|ˈʃnaɪ̯ən|qor yog‘moq|Heute Nacht soll es schneien.|Aytishlaricha, bugun kechasi qor yog‘adi.|
sonnig|ˈzɔnɪç|quyoshli|Morgen wird es sonnig.|Ertaga havo quyoshli bo‘ladi.|
windig|ˈvɪndɪç|shamolli|Am Meer ist es oft windig.|Dengiz bo‘yida tez-tez shamol bo‘ladi.|
bewölkt|bəˈvœlkt|bulutli|Der Himmel ist heute stark bewölkt.|Bugun osmonni qalin bulut qoplagan.|
der Baum|baʊ̯m|daraxt|Unter dem Baum ist es kühl.|Daraxt tagida salqin.|die Bäume
die Blume|ˈbluːmə|gul|Diese Blume braucht viel Wasser.|Bu gulga ko‘p suv kerak.|die Blumen
das Meer|meːɐ̯|dengiz|Ich möchte einmal das Meer sehen.|Men bir marta dengizni ko‘rishni istayman.|die Meere
der Berg|bɛʁk|tog‘|Auf dem Berg liegt noch Schnee.|Tog‘da hali qor yotibdi.|die Berge
@8|Kundalik gaplarni bog‘lash
gern|ɡɛʁn|bajonidil; yoqtirib|Ich lerne gern neue Wörter.|Men yangi so‘zlarni bajonidil o‘rganaman.|
sehr|zeːɐ̯|juda|Deine Nachricht freut mich sehr.|Xabaring meni juda xursand qildi.|
nur|nuːɐ̯|faqat|Ich brauche nur fünf Minuten.|Menga faqat besh daqiqa kerak.|
noch|nɔx|hali; yana|Möchtest du noch eine Tasse Tee?|Yana bir piyola choy xohlaysanmi?|
schon|ʃoːn|allaqachon|Meine Hausaufgaben sind schon fertig.|Uy vazifalarim allaqachon tayyor.|
wieder|ˈviːdɐ|yana; qayta|Mein Schlüssel ist wieder weg.|Kalitim yana yo‘qolibdi.|
deshalb|ˈdɛshalp|shuning uchun|Es regnet, deshalb bleibe ich drinnen.|Yomg‘ir yog‘yapti, shuning uchun ichkarida qolaman.|
weil|vaɪ̯l|chunki; …gani uchun|Ich lerne Deutsch, weil ich reisen möchte.|Men sayohat qilmoqchi bo‘lganim uchun nemis tilini o‘rganyapman.|
dass|das|…ligini; … deb|Ich hoffe, dass du morgen kommst.|Ertaga kelishingga umid qilaman.|
wenn|vɛn|agar; …ganda|Wenn es warm ist, essen wir draußen.|Havo issiq bo‘lsa, tashqarida ovqatlanamiz.|
dann|dan|keyin; unda|Erst frühstücke ich, dann gehe ich los.|Avval nonushta qilaman, keyin yo‘lga chiqaman.|
zuerst|tsuˈeːɐ̯st|avval; birinchi bo‘lib|Zuerst wasche ich meine Hände.|Avval qo‘llarimni yuvaman.|
danach|daˈnaːx|undan keyin|Wir kochen, danach essen wir zusammen.|Ovqat pishiramiz, undan keyin birga yeymiz.|
vorher|ˈfoːɐ̯heːɐ̯|undan oldin|Der Film beginnt um acht; vorher essen wir.|Film soat sakkizda boshlanadi; undan oldin ovqatlanamiz.|
glücklich|ˈɡlʏklɪç|baxtli; xursand|Mit meiner Familie bin ich glücklich.|Oilam bilan baxtliman.|
traurig|ˈtʁaʊ̯ʁɪç|xafa; g‘amgin|Ohne meine Freunde bin ich traurig.|Do‘stlarimsiz xafa bo‘laman.|
freundlich|ˈfʁɔɪ̯ntlɪç|xushmuomala; do‘stona|Die neue Nachbarin grüßt immer freundlich.|Yangi qo‘shni ayol doim xushmuomalalik bilan salom beradi.|
interessant|ɪntəʁɛˈsant|qiziqarli|Der Film über Berlin ist interessant.|Berlin haqidagi film qiziqarli.|
langweilig|ˈlaŋvaɪ̯lɪç|zerikarli|Allein warten ist langweilig.|Yolg‘iz kutish zerikarli.|
wichtig|ˈvɪçtɪç|muhim|Für mich ist tägliches Üben wichtig.|Men uchun har kuni mashq qilish muhim.|
"""

def build():
    entries = []
    week = topic = None
    for raw in DATA.strip().splitlines():
        if not raw.strip() or raw.startswith('#'):
            continue
        if raw.startswith('@'):
            w, topic = raw[1:].split('|', 1)
            week = int(w)
            continue
        parts = raw.split('|')
        assert len(parts) == 6, raw
        word, ipa, meaning, example, translation, forms = parts
        entries.append(dict(id=len(entries)+1, week=week, topic=topic,
                            word=word, ipa=ipa, meaning=meaning,
                            example=example, translation=translation, forms=forms))
    assert len(entries) == 800, len(entries)
    assert all(e['week'] == (e['id']-1)//100+1 for e in entries)
    words = [e['word'] for e in entries]
    assert len({w.casefold() for w in words}) == 800, 'Duplicate headwords'
    assert len(set(e['example'] for e in entries)) == 800, 'Duplicate examples'
    assert all(all(e[k] for k in ('word','ipa','meaning','example','translation')) for e in entries)
    assert all(isinstance(e['forms'], str) for e in entries)
    for e in entries:
        if e['word'].startswith(('der ', 'die ', 'das ')):
            assert e['word'].split(' ', 1)[1][0].isupper(), e['word']
            assert e['forms'], e['word']
    target = Path(__file__).resolve().parents[1] / 'src/data/german/vocabulary-1.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(entries, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Count:', len(entries))
    print('Per week:', {w: sum(e['week']==w for e in entries) for w in range(1,9)})
    print('Duplicate headwords: 0; duplicate examples: 0')
    print('Changed paths: src/data/german/vocabulary-1.json; scripts/german-vocab-1.py')

if __name__ == '__main__':
    build()
