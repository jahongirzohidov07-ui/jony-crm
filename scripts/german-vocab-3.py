"""Original B1 vocabulary, weeks 17–24. All linguistic fields are authored below.

Run from any directory to rebuild the owned JSON file and check its invariants.
IPA is broad Standard German; noun articles are transcribed consistently.
"""
import json
from pathlib import Path
from collections import Counter

BLOCKS = []

BLOCKS.append((17, 'Gesellschaft und Zusammenleben', r'''
die Gesellschaft|ɡəˈzɛlʃaft|jamiyat|Eine offene Gesellschaft braucht neugierige Menschen.|Ochiq jamiyatga qiziquvchan odamlar kerak.|die Gesellschaften
zusammenhalten|tsuˈzamənˌhaltn̩|bir-birini qo‘llab-quvvatlamoq|In schwierigen Zeiten halten die Nachbarn zusammen.|Qiyin paytlarda qo‘shnilar bir-birini qo‘llab-quvvatlaydi.|hält zusammen, hielt zusammen, hat zusammengehalten
die Bevölkerung|bəˈfœlkəʁʊŋ|aholi|Die Bevölkerung unserer Stadt wächst langsam.|Shahrimiz aholisi asta-sekin ko‘paymoqda.|die Bevölkerungen
die Herkunft|ˈheːɐ̯kʊnft|kelib chiqish|Nach ihrer Herkunft fragt hier niemand.|Bu yerda hech kim uning kelib chiqishini so‘ramaydi.|odatda birlikda
die Staatsangehörigkeit|ˈʃtaːtsʔanɡəhøːʁɪçkaɪt|fuqarolik|Im Formular steht auch meine Staatsangehörigkeit.|Anketada mening fuqaroligim ham ko‘rsatilgan.|die Staatsangehörigkeiten
der Bürger|ˈbʏʁɡɐ|fuqaro|Jeder Bürger darf eine Frage stellen.|Har bir fuqaro savol berishi mumkin.|die Bürger
die Demokratie|demokʁaˈtiː|demokratiya|In einer Demokratie sind freie Wahlen wichtig.|Demokratiyada erkin saylovlar muhim.|die Demokratien
die Wahl|vaːl|saylov; tanlov|Vor der Wahl vergleichen wir die Programme.|Saylovdan oldin biz dasturlarni solishtiramiz.|die Wahlen
die Stimme|ˈʃtɪmə|ovoz|Bei der Abstimmung zählt jede Stimme.|Ovoz berishda har bir ovoz hisobga olinadi.|die Stimmen
die Mehrheit|ˈmeːɐ̯haɪt|ko‘pchilik|Die Mehrheit möchte einen ruhigeren Innenhof.|Ko‘pchilik tinchroq ichki hovli bo‘lishini istaydi.|die Mehrheiten
die Minderheit|ˈmɪndɐhaɪt|ozchilik|Auch die Meinung der Minderheit wird gehört.|Ozchilikning fikri ham tinglanadi.|die Minderheiten
die Regierung|ʁeˈɡiːʁʊŋ|hukumat|Die Regierung stellt einen neuen Plan vor.|Hukumat yangi rejani taqdim etmoqda.|die Regierungen
das Gesetz|ɡəˈzɛts|qonun|Das neue Gesetz wird im Kurs besprochen.|Yangi qonun kursda muhokama qilinadi.|die Gesetze
das Recht|ʁɛçt|huquq|Jedes Kind hat ein Recht auf Bildung.|Har bir bola ta’lim olish huquqiga ega.|die Rechte
die Pflicht|pflɪçt|majburiyat|Zu meinen Pflichten gehört der Küchendienst.|Mening majburiyatlarimga oshxonada navbatchilik qilish kiradi.|die Pflichten
die Freiheit|ˈfʁaɪhaɪt|erkinlik|Für mich bedeutet Freiheit auch freie Zeit.|Men uchun erkinlik bo‘sh vaqtni ham anglatadi.|die Freiheiten
die Gleichberechtigung|ˈɡlaɪçbəʁɛçtɪɡʊŋ|teng huquqlilik|Über Gleichberechtigung reden wir nicht nur am Frauentag.|Teng huquqlilik haqida faqat Xotin-qizlar kunida gapirmaymiz.|odatda birlikda
Verantwortung tragen|fɛɐ̯ˈʔantvɔʁtʊŋ ˌtʁaːɡn̩|mas’uliyatni zimmasida tutmoq|Für die Sicherheit tragen wir alle Verantwortung.|Xavfsizlik uchun barchamiz mas’ulmiz.|trägt Verantwortung, trug Verantwortung, hat Verantwortung getragen
die Sicherheit|ˈzɪçɐhaɪt|xavfsizlik|Gute Beleuchtung erhöht die Sicherheit am Bahnhof.|Yaxshi yoritish vokzaldagi xavfsizlikni oshiradi.|odatda birlikda
die Öffentlichkeit|ˈœfn̩tlɪçkaɪt|jamoatchilik|Die Öffentlichkeit erfährt morgen von dem Projekt.|Jamoatchilik loyiha haqida ertaga xabar topadi.|odatda birlikda
der Wohnsitz|ˈvoːnzɪts|doimiy yashash joyi|Meinen neuen Wohnsitz muss ich noch anmelden.|Yangi yashash joyimni hali ro‘yxatdan o‘tkazishim kerak.|die Wohnsitze
das Amt|amt|idora|Auf dem Amt fehlt mir noch eine Unterschrift.|Idorada menga hali bitta imzo yetishmayapti.|die Ämter
einen Antrag stellen|aɪnən ˈantʁaːk ˌʃtɛlən|ariza bermoq|Den Antrag kann ich auch online stellen.|Arizani onlayn ham berishim mumkin.|stellt einen Antrag, stellte einen Antrag, hat einen Antrag gestellt
die Genehmigung|ɡəˈneːmɪɡʊŋ|ruxsatnoma|Für das Straßenfest brauchen wir eine Genehmigung.|Ko‘cha bayrami uchun bizga ruxsatnoma kerak.|die Genehmigungen
beglaubigen|bəˈɡlaʊbɪɡn̩|rasmiy tasdiqlamoq|Das Amt beglaubigt die Kopie meines Zeugnisses.|Idora guvohnomam nusxasini rasmiy tasdiqlaydi.|beglaubigt, beglaubigte, hat beglaubigt
der Nachweis|ˈnaːxvaɪs|tasdiqlovchi hujjat, dalil|Als Nachweis reicht eine Kopie des Vertrags.|Tasdiq uchun shartnoma nusxasi yetarli.|die Nachweise
eine Frist verlängern|aɪnə ˈfʁɪst fɛɐ̯ˌlɛŋɐn|muddatni uzaytirmoq|Können Sie die Frist um eine Woche verlängern?|Muddatni bir haftaga uzaytira olasizmi?|verlängert eine Frist, verlängerte eine Frist, hat eine Frist verlängert
die Aufenthaltserlaubnis|ˈaʊfʔɛnthaːltsʔɛɐ̯ˌlaʊpnɪs|yashash ruxsatnomasi|Meine Aufenthaltserlaubnis liegt sicher im Ordner.|Yashash ruxsatnomam papkada xavfsiz turibdi.|die Aufenthaltserlaubnisse
unterschreiben lassen|ʊntɐˈʃʁaɪbn̩ ˌlasn̩|imzolatmoq|Ich lasse das Formular von meiner Chefin unterschreiben.|Blankani rahbarimga imzolataman.|lässt unterschreiben, ließ unterschreiben, hat unterschreiben lassen
die Meldebescheinigung|ˈmɛldəbəˌʃaɪnɪɡʊŋ|yashash joyida ro‘yxatdan o‘tganlik ma’lumotnomasi|Die Bank möchte eine aktuelle Meldebescheinigung sehen.|Bank yangi ro‘yxatdan o‘tganlik ma’lumotnomasini ko‘rmoqchi.|die Meldebescheinigungen
sich niederlassen|zɪç ˈniːdɐˌlasn̩|bir joyga ko‘chib joylashmoq|Nach mehreren Umzügen hat sich die Familie in Bremen niedergelassen.|Bir necha ko‘chishdan keyin oila Bremenga joylashdi.|lässt sich nieder, ließ sich nieder, hat sich niedergelassen
die Integration|ɪntəɡʁaˈtsi̯oːn|jamiyatga qo‘shilish|Gemeinsamer Sport kann die Integration erleichtern.|Birgalikda sport qilish jamiyatga qo‘shilishni yengillashtirishi mumkin.|die Integrationen
die Vielfalt|ˈfiːlfalt|xilma-xillik|Die Vielfalt der Sprachen gefällt mir.|Tillarning xilma-xilligi menga yoqadi.|odatda birlikda
das Vorurteil|ˈfoːɐ̯ʔʊʁtaɪl|asossiz oldindan qarash|Ein Gespräch kann ein Vorurteil verändern.|Bitta suhbat asossiz qarashni o‘zgartirishi mumkin.|die Vorurteile
respektvoll|ʁeˈspɛktfoːl|hurmat bilan, hurmatli|Auch bei Streit bleiben wir respektvoll.|Janjalda ham hurmatni saqlaymiz.|
die Toleranz|toleˈʁants|bag‘rikenglik|Toleranz üben wir schon in unserer WG.|Bag‘rikenglikni umumiy kvartiramizdayoq mashq qilamiz.|odatda birlikda
einen Streit schlichten|aɪnən ˈʃtʁaɪt ˌʃlɪçtn̩|janjalni tinchitmoq|Die Lehrerin schlichtet den Streit um den Ball.|O‘qituvchi to‘p ustidagi janjalni tinchitadi.|schlichtet einen Streit, schlichtete einen Streit, hat einen Streit geschlichtet
nachgeben|ˈnaːxɡeːbn̩|yon bermoq|Diesmal gebe ich nach, nächstes Mal entscheiden wir gemeinsam.|Bu safar yon beraman, keyingi safar birgalikda qaror qilamiz.|gibt nach, gab nach, hat nachgegeben
Rücksicht nehmen auf|ˈʁʏkzɪçt ˌneːmən aʊf|...ni hisobga olib harakat qilmoq|Beim Feiern nehmen wir Rücksicht auf die Nachbarn.|Bayram qilganda qo‘shnilarni hisobga olamiz.|nimmt Rücksicht, nahm Rücksicht, hat Rücksicht genommen; auf + Akkusativ
sich an Regeln halten|zɪç an ˈʁeːɡl̩n ˌhaltn̩|qoidalarga rioya qilmoq|Auch Erwachsene müssen sich an Regeln halten.|Kattalar ham qoidalarga rioya qilishlari kerak.|hält sich an Regeln, hielt sich an Regeln, hat sich an Regeln gehalten
das Verhalten|fɛɐ̯ˈhaltn̩|xulq-atvor|Sein ruhiges Verhalten überrascht mich.|Uning xotirjam xulq-atvori meni hayratlantiradi.|odatda birlikda
die Gewohnheit|ɡəˈvoːnhaɪt|odat|Pünktlichkeit ist eine nützliche Gewohnheit.|Vaqtida kelish foydali odat.|die Gewohnheiten
die Tradition|tʁadiˈtsi̯oːn|an’ana|Zum Neujahr kochen wir nach alter Tradition.|Yangi yilda qadimiy an’anaga ko‘ra taom tayyorlaymiz.|die Traditionen
die Religion|ʁeliˈɡi̯oːn|din|Über Religion sprechen wir respektvoll.|Din haqida hurmat bilan gaplashamiz.|die Religionen
die Generation|ɡenəʁaˈtsi̯oːn|avlod|Drei Generationen sitzen an einem Tisch.|Bir dasturxon atrofida uch avlod o‘tiribdi.|die Generationen
die Armut|ˈaːɐ̯muːt|qashshoqlik|Armut betrifft auch Menschen mit Arbeit.|Qashshoqlik ishlaydigan odamlarga ham ta’sir qiladi.|ko‘plik yo‘q
der Reichtum|ˈʁaɪçtuːm|boylik|Für Oma ist Freundschaft der größte Reichtum.|Buvim uchun do‘stlik eng katta boylik.|die Reichtümer
auf Hilfe angewiesen sein|aʊf ˈhɪlfə ˌanɡəviːzn̩ zaɪn|yordamga muhtoj bo‘lmoq|Nach dem Unfall war ich auf Hilfe angewiesen.|Avariyadan keyin yordamga muhtoj edim.|ist angewiesen, war angewiesen, ist angewiesen gewesen
Kontakte knüpfen|kɔnˈtaktə ˌknʏpfn̩|tanishlar orttirmoq|Im Sprachcafé kann man neue Kontakte knüpfen.|Til kafesida yangi tanishlar orttirish mumkin.|knüpft Kontakte, knüpfte Kontakte, hat Kontakte geknüpft
die Gleichheit|ˈɡlaɪçhaɪt|tenglik|Gleichheit vor dem Gesetz ist ein wichtiges Prinzip.|Qonun oldida tenglik muhim tamoyil.|odatda birlikda
zur Wahl gehen|tsuːɐ̯ ˈvaːl ˌɡeːən|saylovda ovoz berishga bormoq|Am Sonntag gehen viele Nachbarn zur Wahl.|Yakshanba kuni ko‘p qo‘shnilar ovoz berishga boradi.|geht zur Wahl, ging zur Wahl, ist zur Wahl gegangen
abstimmen|ˈapʃtɪmən|ovoz bermoq|Über den Ausflug stimmen wir morgen ab.|Sayohat masalasida ertaga ovoz beramiz.|stimmt ab, stimmte ab, hat abgestimmt
Unterlagen einreichen|ˈʊntɐlaːɡn̩ ˌaɪnʁaɪçn̩|hujjatlarni topshirmoq|Die fehlenden Unterlagen reiche ich morgen ein.|Yetishmayotgan hujjatlarni ertaga topshiraman.|reicht Unterlagen ein, reichte Unterlagen ein, hat Unterlagen eingereicht
genehmigen|ɡəˈneːmɪɡn̩|ruxsat bermoq, tasdiqlamoq|Die Stadt genehmigt unser Straßenfest.|Shahar ma’muriyati ko‘cha bayramimizga ruxsat beradi.|genehmigt, genehmigte, hat genehmigt
gelten|ˈɡɛltn̩|amal qilmoq|Die Hausordnung gilt für alle Bewohner.|Uy tartib-qoidalari barcha yashovchilar uchun amal qiladi.|gilt, galt, hat gegolten
verbieten|fɛɐ̯ˈbiːtn̩|taqiqlamoq|Die Bibliothek verbietet laute Telefongespräche.|Kutubxona baland ovozli telefon suhbatlarini taqiqlaydi.|verbietet, verbot, hat verboten
erlauben|ɛɐ̯ˈlaʊbn̩|ruxsat bermoq|Unser Vermieter erlaubt kleine Haustiere.|Uy egamiz kichik uy hayvonlariga ruxsat beradi.|erlaubt, erlaubte, hat erlaubt
verpflichten|fɛɐ̯ˈpflɪçtn̩|majbur qilmoq|Der Vertrag verpflichtet uns zur pünktlichen Zahlung.|Shartnoma bizni vaqtida to‘lashga majbur qiladi.|verpflichtet, verpflichtete, hat verpflichtet
respektieren|ʁespɛkˈtiːʁən|hurmat qilmoq|Ich respektiere deine Entscheidung.|Men sening qaroringni hurmat qilaman.|respektiert, respektierte, hat respektiert
akzeptieren|aktsɛpˈtiːʁən|qabul qilmoq|Wir akzeptieren unterschiedliche Lebensweisen.|Biz turli turmush tarzlarini qabul qilamiz.|akzeptiert, akzeptierte, hat akzeptiert
sich einsetzen für|zɪç ˈaɪnzɛtsn̩ fyːɐ̯|...uchun faol harakat qilmoq|Wir setzen uns für sichere Radwege ein.|Biz xavfsiz velosiped yo‘llari uchun harakat qilamiz.|setzt sich ein, setzte sich ein, hat sich eingesetzt; für + Akkusativ
sich engagieren|zɪç aŋɡaˈʒiːʁən|faol hissa qo‘shmoq|Ali engagiert sich für ältere Menschen.|Ali keksalarga yordam berishda faol qatnashadi.|engagiert sich, engagierte sich, hat sich engagiert
sich beteiligen|zɪç bəˈtaɪlɪɡn̩|ishtirok etmoq|Auch die Kinder beteiligen sich an der Planung.|Rejalashtirishda bolalar ham qatnashadilar.|beteiligt sich, beteiligte sich, hat sich beteiligt
für jemanden sprechen|fyːɐ̯ ˈjeːmandn̩ ˌʃpʁɛçn̩|kimningdir nomidan gapirmoq|Ich kann nur für mich selbst sprechen.|Men faqat o‘z nomimdan gapira olaman.|spricht für jemanden, sprach für jemanden, hat für jemanden gesprochen
entscheiden|ɛntˈʃaɪdn̩|qaror qilmoq|Darüber entscheidet die ganze Gruppe.|Bu masalada butun guruh qaror qiladi.|entscheidet, entschied, hat entschieden
einhalten|ˈaɪnhaltn̩|rioya qilmoq|Bitte halten Sie die Ruhezeiten ein.|Iltimos, tinchlik vaqtlariga rioya qiling.|hält ein, hielt ein, hat eingehalten
verstoßen|fɛɐ̯ˈʃtoːsn̩|buzmoq, xilof ish qilmoq|Mit dem Lärm verstößt er gegen die Hausordnung.|U shovqini bilan uy tartib-qoidalarini buzmoqda.|verstößt, verstieß, hat verstoßen
sich anpassen|zɪç ˈanpasn̩|moslashmoq|Ich passe mich langsam an den neuen Alltag an.|Yangi kundalik hayotga asta-sekin moslashyapman.|passt sich an, passte sich an, hat sich angepasst
gehören|ɡəˈhøːʁən|tegishli bo‘lmoq|Zum Zusammenleben gehört auch Geduld.|Birga yashash sabr-toqatni ham talab qiladi.|gehört, gehörte, hat gehört
begegnen|bəˈɡeːɡnən|duch kelmoq, uchratmoq|Im Hof begegne ich Menschen aus vielen Ländern.|Hovlida ko‘p mamlakatlardan kelgan odamlarni uchrataman.|begegnet, begegnete, ist begegnet
vermitteln|fɛɐ̯ˈmɪtl̩n|vositachilik qilmoq|Bei Streit vermittelt unsere Hausmeisterin.|Janjal bo‘lsa, uy qarovchimiz vositachilik qiladi.|vermittelt, vermittelte, hat vermittelt
einwandern|ˈaɪnvandɐn|ko‘chib kelmoq|Seine Großeltern sind vor Jahren eingewandert.|Uning bobosi va buvisi ko‘p yillar oldin ko‘chib kelgan.|wandert ein, wanderte ein, ist eingewandert
auswandern|ˈaʊsvandɐn|boshqa mamlakatga ko‘chmoq|Mein Onkel möchte nach Kanada auswandern.|Amakim Kanadaga ko‘chmoqchi.|wandert aus, wanderte aus, ist ausgewandert
integrieren|ɪntəˈɡʁiːʁən|qo‘shmoq, moslashtirmoq|Der Verein integriert neue Mitglieder schnell.|Uyushma yangi a’zolarni tezda jamoaga qo‘shadi.|integriert, integrierte, hat integriert
diskriminieren|dɪskʁimiˈniːʁən|kamsitmoq|Niemand darf andere wegen ihrer Herkunft diskriminieren.|Hech kim boshqalarni kelib chiqishi sababli kamsitishi mumkin emas.|diskriminiert, diskriminierte, hat diskriminiert
die Bürgerversammlung|ˈbʏʁɡɐfɛɐ̯ˌzamlʊŋ|fuqarolar yig‘ilishi|Bei der Bürgerversammlung fragen wir nach dem neuen Spielplatz.|Fuqarolar yig‘ilishida yangi bolalar maydonchasi haqida so‘raymiz.|die Bürgerversammlungen
unter vier Augen|ʊntɐ fiːɐ̯ ˈʔaʊɡn̩|yolg‘iz, yuzma-yuz|Können wir kurz unter vier Augen sprechen?|Bir oz yolg‘iz gaplashsak bo‘ladimi?|
gesetzlich|ɡəˈzɛtslɪç|qonuniy, qonunda belgilangan|Die gesetzliche Frist ist noch nicht vorbei.|Qonunda belgilangan muddat hali tugamadi.|
gleichberechtigt|ˈɡlaɪçbəʁɛçtɪçt|teng huquqli|In unserem Team sind alle gleichberechtigt.|Jamoamizda hamma teng huquqli.|
Verantwortung übernehmen für|fɛɐ̯ˈʔantvɔʁtʊŋ yːbɐˌneːmən fyːɐ̯|...uchun mas’uliyatni o‘z zimmasiga olmoq|Ich übernehme die Verantwortung für die Gästeliste.|Mehmonlar ro‘yxati uchun mas’uliyatni zimmamga olaman.|übernimmt, übernahm, hat übernommen; für + Akkusativ
freiwillig|ˈfʁaɪvɪlɪç|ixtiyoriy|Die Teilnahme am Fest ist freiwillig.|Bayramda qatnashish ixtiyoriy.|
gemeinsam|ɡəˈmaɪnzaːm|birgalikda, umumiy|Gemeinsam streichen wir den alten Zaun.|Eski devorni birgalikda bo‘yaymiz.|
gesellschaftlich|ɡəˈzɛlʃaftlɪç|ijtimoiy|Der Kurs behandelt gesellschaftliche Fragen.|Kursda ijtimoiy masalalar ko‘rib chiqiladi.|
kulturell|kʊltuˈʁɛl|madaniy|Das Viertel bietet viele kulturelle Veranstaltungen.|Mahallada ko‘plab madaniy tadbirlar o‘tkaziladi.|
unabhängig|ˈʊnʔaphɛŋɪç|mustaqil|Der Verein ist politisch unabhängig.|Uyushma siyosiy jihatdan mustaqil.|
abhängig|ˈaphɛŋɪç|bog‘liq, qaram|Ohne Bus bin ich von meinem Bruder abhängig.|Avtobussiz akamga qaram bo‘lib qolaman.|
gerecht|ɡəˈʁɛçt|adolatli|Wir suchen eine gerechte Verteilung der Aufgaben.|Vazifalarni adolatli taqsimlash yo‘lini izlayapmiz.|
friedlich|ˈfʁiːtlɪç|tinch, tinchliksevar|Die Demonstration blieb friedlich.|Namoyish tinch o‘tdi.|
fremd|fʁɛmt|begona, notanish|Am Anfang war mir die Stadt fremd.|Boshida shahar menga begona edi.|
vertraut|fɛɐ̯ˈtʁaʊt|tanish, qadrdon|Inzwischen sind mir die Straßen vertraut.|Endi ko‘chalar menga tanish.|
sich wenden an|zɪç ˈvɛndn̩ an|...ga murojaat qilmoq|Bei Fragen wenden Sie sich bitte an die Beratung.|Savollar bo‘lsa, maslahat bo‘limiga murojaat qiling.|wendet sich, wandte sich, hat sich gewandt; an + Akkusativ
in Kraft treten|ɪn ˈkʁaft ˌtʁeːtn̩|kuchga kirmoq|Die neue Regel tritt im Januar in Kraft.|Yangi qoida yanvarda kuchga kiradi.|tritt in Kraft, trat in Kraft, ist in Kraft getreten
fristgerecht|ˈfʁɪstɡəˌʁɛçt|belgilangan muddatda|Ich habe alle Unterlagen fristgerecht eingereicht.|Barcha hujjatlarni belgilangan muddatda topshirdim.|
innerhalb|ˈɪnɐhalp|ichida, davomida|Sie erhalten innerhalb einer Woche eine Antwort.|Bir hafta ichida javob olasiz.|
außerhalb|ˈaʊsɐhalp|tashqarisida|Außerhalb der Öffnungszeiten erreichen Sie niemanden.|Ish vaqtidan tashqari hech kim bilan bog‘lana olmaysiz.|
laut|laʊt|...ga ko‘ra|Laut Hausordnung dürfen hier keine Fahrräder stehen.|Uy qoidalariga ko‘ra, bu yerga velosiped qo‘yish mumkin emas.|
jeweils|ˈjeːvaɪls|har birida, har safar|Jede Gruppe schickt jeweils zwei Vertreter.|Har bir guruh ikkitadan vakil yuboradi.|
miteinander|mɪtʔaɪˈnandɐ|bir-biri bilan|Wir reden miteinander, bevor wir uns beschweren.|Shikoyat qilishdan oldin bir-birimiz bilan gaplashamiz.|
füreinander|fyːɐ̯ʔaɪˈnandɐ|bir-biri uchun|Gute Nachbarn sind füreinander da.|Yaxshi qo‘shnilar bir-biriga suyanch bo‘ladi.|
aufeinander|aʊfʔaɪˈnandɐ|bir-biriga|Im Haus nehmen wir Rücksicht aufeinander.|Uyda biz bir-birimizni hisobga olamiz.|
'''))

BLOCKS.append((18, 'Umwelt und nachhaltiger Alltag', r'''
der Umweltschutz|ˈʊmvɛltˌʃʊts|atrof-muhitni muhofaza qilish|Umweltschutz beginnt für uns vor der Haustür.|Biz uchun atrof-muhitni asrash o‘z eshigimiz oldidan boshlanadi.|ko‘plik yo‘q
das Klima|ˈkliːma|iqlim|Das Klima verändert sich auch bei uns.|Bizda ham iqlim o‘zgarmoqda.|die Klimate
der Klimawandel|ˈkliːmaˌvandl̩|iqlim o‘zgarishi|Im Unterricht diskutieren wir über den Klimawandel.|Darsda iqlim o‘zgarishi haqida bahslashamiz.|odatda birlikda
das Naturschutzgebiet|naˈtuːɐ̯ʃʊtsɡəˌbiːt|tabiatni muhofaza qilish hududi|Im Naturschutzgebiet bleiben wir auf den Wegen.|Tabiatni muhofaza qilish hududida yo‘laklardan chiqmaymiz.|die Naturschutzgebiete
die Grünfläche|ˈɡʁyːnˌflɛçə|ko‘kalamzor hudud|Zwischen den Häusern entsteht eine neue Grünfläche.|Uylar orasida yangi ko‘kalamzor hudud barpo etilmoqda.|die Grünflächen
die Luft|lʊft|havo|Nach dem Regen ist die Luft frisch.|Yomg‘irdan keyin havo toza bo‘ladi.|bu ma’noda ko‘plik yo‘q
das Grundwasser|ˈɡʁʊntˌvasɐ|yerosti suvi|Chemikalien dürfen nicht ins Grundwasser gelangen.|Kimyoviy moddalar yerosti suviga tushmasligi kerak.|ko‘plik yo‘q
der Erdboden|ˈeːɐ̯tˌboːdn̩|yer yuzasi, tuproq|Nach dem Regen ist der Erdboden weich.|Yomg‘irdan keyin tuproq yumshoq.|die Erdböden
abholzen|ˈaphɔltsn̩|daraxtlarni kesib tashlamoq|Für die neue Straße sollen Bäume abgeholzt werden.|Yangi yo‘l uchun daraxtlar kesilishi rejalashtirilgan.|holzt ab, holzte ab, hat abgeholzt
der Kompost|ˈkɔmpɔst|kompost, organik o‘g‘it|Aus Gartenabfällen entsteht wertvoller Kompost.|Bog‘ chiqindilaridan qimmatli kompost hosil bo‘ladi.|die Komposte
die Ernte|ˈɛʁntə|hosil|Unsere erste Ernte besteht aus fünf Tomaten.|Birinchi hosilimiz beshta pomidordan iborat.|die Ernten
die Tierart|ˈtiːɐ̯ʔaːɐ̯t|hayvon turi|Welche Tierarten leben in diesem Wald?|Bu o‘rmonda qanday hayvon turlari yashaydi?|die Tierarten
das Unkraut|ˈʊnkʁaʊt|begona o‘t|Zwischen den Bohnen wächst viel Unkraut.|Loviya orasida ko‘p begona o‘t o‘smoqda.|odatda birlikda
der Dünger|ˈdʏŋɐ|o‘g‘it|Für diese Pflanzen benutzen wir organischen Dünger.|Bu o‘simliklarga organik o‘g‘it ishlatamiz.|die Dünger
der Lebensraum|ˈleːbn̩sˌʁaʊm|yashash muhiti|Der Teich ist ein Lebensraum für Frösche.|Hovuz qurbaqalar uchun yashash muhiti.|die Lebensräume
die Energiequelle|ʔenɛʁˈɡiːˌkvɛlə|energiya manbasi|Die Sonne ist eine wichtige Energiequelle.|Quyosh muhim energiya manbasi.|die Energiequellen
der Strom|ʃtʁoːm|elektr toki|Beim Kochen sparen wir Strom mit einem Deckel.|Ovqat pishirganda qopqoq yordamida elektrni tejaymiz.|bu ma’noda ko‘plik yo‘q
die Wärmepumpe|ˈvɛʁməˌpʊmpə|issiqlik nasosi|Unsere Nachbarn lassen eine Wärmepumpe einbauen.|Qo‘shnilarimiz issiqlik nasosi o‘rnatishyapti.|die Wärmepumpen
der Verbrauch|fɛɐ̯ˈbʁaʊx|sarf, iste’mol|Unser Verbrauch ist diesen Monat gesunken.|Bu oy sarfimiz kamaydi.|odatda birlikda
die Verschmutzung|fɛɐ̯ˈʃmʊtsʊŋ|ifloslanish|Die Verschmutzung des Flusses macht uns Sorgen.|Daryoning ifloslanishi bizni tashvishlantirmoqda.|die Verschmutzungen
Müll vermeiden|ˈmʏl fɛɐ̯ˌmaɪdn̩|chiqindi hosil bo‘lishini kamaytirmoq|Mit eigenen Behältern vermeiden wir Müll beim Einkaufen.|Xaridda o‘z idishlarimizdan foydalanib chiqindini kamaytiramiz.|vermeidet Müll, vermied Müll, hat Müll vermieden
der Sperrmüll|ˈʃpɛʁˌmʏl|yirik maishiy chiqindi|Das alte Sofa wird als Sperrmüll abgeholt.|Eski divan yirik maishiy chiqindi sifatida olib ketiladi.|ko‘plik yo‘q
der Wertstoffhof|ˈveːɐ̯tʃtɔfˌhoːf|qayta ishlanadigan chiqindilarni qabul qilish joyi|Den kaputten Fernseher bringen wir zum Wertstoffhof.|Buzilgan televizorni chiqindi qabul qilish joyiga olib boramiz.|die Wertstoffhöfe
die Verpackung|fɛɐ̯ˈpakʊŋ|qadoq|Die Verpackung ist größer als der Inhalt.|Qadoq ichidagi narsadan kattaroq.|die Verpackungen
das Plastik|ˈplastɪk|plastmassa|Wir kaufen Gemüse möglichst ohne Plastik.|Sabzavotni imkon qadar plastmassasiz sotib olamiz.|ko‘plik yo‘q
der Rohstoff|ˈʁoːʃtɔf|xomashyo|Alte Geräte enthalten oft wertvolle Rohstoffe.|Eski qurilmalarda ko‘pincha qimmatli xomashyo bo‘ladi.|die Rohstoffe
das Metall|meˈtal|metall|Der alte Stuhl besteht fast nur aus Metall.|Eski stul deyarli butunlay metalldan yasalgan.|die Metalle
der Restmüll|ˈʁɛstˌmʏl|qayta ishlanmaydigan maishiy chiqindi|Die kaputte Zahnbürste kommt in den Restmüll.|Singan tish cho‘tkasi qayta ishlanmaydigan chiqindiga tashlanadi.|ko‘plik yo‘q
der Biomüll|ˈbiːoˌmʏl|organik chiqindi|Die Kartoffelschalen gehören in den Biomüll.|Kartoshka po‘choqlari organik chiqindiga tashlanadi.|ko‘plik yo‘q
das Altpapier|ˈaltpaˌpiːɐ̯|makulatura, eski qog‘oz|Wir sammeln Altpapier in einer Kiste.|Eski qog‘ozlarni bir qutiga yig‘amiz.|ko‘plik yo‘q
die Pfandflasche|ˈpfantˌflaʃə|garov puli qaytariladigan idish|Die Pfandflaschen bringe ich beim nächsten Einkauf zurück.|Garovli idishlarni keyingi xaridda qaytaraman.|die Pfandflaschen
der Mehrwegbecher|ˈmeːɐ̯veːkˌbɛçɐ|qayta ishlatiladigan stakan|Mein Mehrwegbecher passt unter die Kaffeemaschine.|Ko‘p marta ishlatiladigan stakanim qahva mashinasi tagiga sig‘adi.|die Mehrwegbecher
die Stofftasche|ˈʃtɔfˌtaʃə|mato sumka|Die Stofftasche begleitet mich seit fünf Jahren.|Mato sumkam besh yildan beri menga xizmat qiladi.|die Stofftaschen
die Solaranlage|zoˈlaːɐ̯ʔanˌlaːɡə|quyosh energiyasi qurilmasi|Auf dem Schuldach steht eine Solaranlage.|Maktab tomida quyosh energiyasi qurilmasi bor.|die Solaranlagen
die Windkraft|ˈvɪntˌkʁaft|shamol energiyasi|Die Region nutzt immer mehr Windkraft.|Hudud shamol energiyasidan tobora ko‘proq foydalanmoqda.|ko‘plik yo‘q
das Kraftwerk|ˈkʁaftvɛʁk|elektr stansiyasi|Das alte Kraftwerk wird nächstes Jahr geschlossen.|Eski elektr stansiyasi kelasi yil yopiladi.|die Kraftwerke
der Nahverkehr|ˈnaːfɛɐ̯ˌkeːɐ̯|mahalliy jamoat transporti|Am Wochenende fährt der Nahverkehr seltener.|Dam olish kunlari mahalliy transport kamroq qatnaydi.|ko‘plik yo‘q
das Verkehrsmittel|fɛɐ̯ˈkeːɐ̯sˌmɪtl̩|transport vositasi|Welches Verkehrsmittel nutzt du am häufigsten?|Qaysi transport vositasidan eng ko‘p foydalanasan?|die Verkehrsmittel
der Radweg|ˈʁaːtveːk|velosiped yo‘lagi|Der neue Radweg führt direkt zur Schule.|Yangi velosiped yo‘lagi to‘g‘ri maktabga olib boradi.|die Radwege
die Fahrgemeinschaft|ˈfaːɐ̯ɡəˌmaɪnʃaft|bir mashinada birga qatnash guruhi|Unsere Fahrgemeinschaft spart Geld und Benzin.|Bir mashinada birga qatnashimiz pul va benzin tejaydi.|die Fahrgemeinschaften
die Abgase|ˈapˌɡaːzə|chiqindi gazlar|An der Kreuzung riecht es nach Abgasen.|Chorrahada chiqindi gazlarning hidi keladi.|ko‘plik; birlik: das Abgas
der Lärm|lɛʁm|shovqin|Der Lärm lässt mich nachts nicht schlafen.|Shovqin tunda uxlashimga yo‘l qo‘ymaydi.|ko‘plik yo‘q
die Hitzewelle|ˈhɪtsəˌvɛlə|jazirama davri|Während der Hitzewelle bleiben die Klassenzimmer morgens offen.|Jazirama davrida sinfxonalar ertalab ochiq turadi.|die Hitzewellen
die Trockenheit|ˈtʁɔkn̩haɪt|qurg‘oqchilik, quruqlik|Unter der Trockenheit leiden auch große Bäume.|Qurg‘oqchilikdan katta daraxtlar ham aziyat chekmoqda.|ko‘plik yo‘q
die Überschwemmung|yːbɐˈʃvɛmʊŋ|suv toshqini|Nach der Überschwemmung helfen viele Freiwillige.|Suv toshqinidan keyin ko‘plab ko‘ngillilar yordam bermoqda.|die Überschwemmungen
das Unwetter|ˈʊnvɛtɐ|kuchli yomon ob-havo|Wegen des Unwetters bleiben wir zu Hause.|Kuchli yomon ob-havo tufayli uyda qolamiz.|die Unwetter
die Dürre|ˈdʏʁə|uzoq qurg‘oqchilik|Die Dürre dauert schon mehrere Monate.|Qurg‘oqchilik bir necha oydan beri davom etmoqda.|die Dürren
der Schaden|ˈʃaːdn̩|zarar|Zum Glück ist der Schaden gering.|Yaxshiyamki, zarar kam.|die Schäden
die Maßnahme|ˈmaːsˌnaːmə|chora-tadbir|Welche Maßnahme hilft gegen den Lärm?|Shovqinga qarshi qaysi chora yordam beradi?|die Maßnahmen
die Nachhaltigkeit|ˈnaːxhaltɪçkaɪt|ekologik barqarorlik|Bei unserer Schulfeier achten wir auf Nachhaltigkeit.|Maktab bayramimizda ekologik barqarorlikka e’tibor beramiz.|ko‘plik yo‘q
unter Schutz stehen|ʊntɐ ˈʃʊts ˌʃteːən|muhofazada bo‘lmoq|Diese seltenen Vögel stehen unter Schutz.|Bu kamyob qushlar muhofazada.|steht unter Schutz, stand unter Schutz, hat unter Schutz gestanden
schonen|ˈʃoːnən|asramoq, avaylamoq|Ich schone die Umwelt und meinen Geldbeutel.|Atrof-muhitni ham, hamyonimni ham asrayman.|schont, schonte, hat geschont
auf etwas achten|aʊf ˈʔɛtvas ˌʔaxtn̩|biror narsaga e’tibor bermoq|Beim Kauf achte ich auf wenig Verpackung.|Xaridda qadoq kam bo‘lishiga e’tibor beraman.|achtet auf etwas, achtete auf etwas, hat auf etwas geachtet
verringern|fɛɐ̯ˈʁɪŋɐn|kamaytirmoq|Wir verringern unseren Wasserverbrauch.|Suv sarfimizni kamaytiryapmiz.|verringert, verringerte, hat verringert
reduzieren|ʁeduˈtsiːʁən|qisqartirmoq|Die Firma reduziert ihre Verpackungen.|Firma qadoqlari miqdorini qisqartiryapti.|reduziert, reduzierte, hat reduziert
trennen|ˈtʁɛnən|ajratmoq|Zu Hause trennen wir Papier und Glas.|Uyda qog‘oz va shishani ajratamiz.|trennt, trennte, hat getrennt
entsorgen|ɛntˈzɔʁɡn̩|chiqindini tegishli joyga topshirmoq|Wo kann ich alte Batterien entsorgen?|Eski batareyalarni qayerga topshirsam bo‘ladi?|entsorgt, entsorgte, hat entsorgt
nachfüllen|ˈnaːxfʏlən|qayta to‘ldirmoq|Die Seifenflasche kann ich im Laden nachfüllen.|Sovun idishini do‘konda qayta to‘ldira olaman.|füllt nach, füllte nach, hat nachgefüllt
recyceln|ʁiˈsaɪkl̩n|qayta ishlamoq|Die Fabrik recycelt alte Kunststoffflaschen.|Zavod eski plastik idishlarni qayta ishlaydi.|recycelt, recycelte, hat recycelt
verschwenden|fɛɐ̯ˈʃvɛndn̩|isrof qilmoq|Lass das Wasser nicht laufen, sonst verschwendest du es.|Suvni oqizib qo‘yma, aks holda isrof qilasan.|verschwendet, verschwendete, hat verschwendet
verbrauchen|fɛɐ̯ˈbʁaʊxn̩|sarflamoq, iste’mol qilmoq|Der neue Kühlschrank verbraucht weniger Strom.|Yangi muzlatkich kamroq elektr sarflaydi.|verbraucht, verbrauchte, hat verbraucht
erzeugen|ɛɐ̯ˈtsɔʏɡn̩|ishlab chiqarmoq, hosil qilmoq|Die Anlage erzeugt Strom für zwanzig Häuser.|Qurilma yigirmata uy uchun elektr ishlab chiqaradi.|erzeugt, erzeugte, hat erzeugt
heizen|ˈhaɪtsn̩|isitmoq|Wir heizen nur die benutzten Zimmer.|Biz faqat foydalanilayotgan xonalarni isitamiz.|heizt, heizte, hat geheizt
lüften|ˈlʏftn̩|shamollatmoq|Nach dem Kochen lüfte ich die Küche.|Ovqat pishirgandan keyin oshxonani shamollataman.|lüftet, lüftete, hat gelüftet
anbauen|ˈanbaʊən|yetishtirmoq|Auf dem Balkon bauen wir Kräuter an.|Balkonda ko‘kat yetishtiramiz.|baut an, baute an, hat angebaut
Regenwasser sammeln|ˈʁeːɡn̩vasɐ ˌzaml̩n|yomg‘ir suvini yig‘moq|Zum Gießen sammeln wir Regenwasser in einer Tonne.|Sug‘orish uchun yomg‘ir suvini bochkaga yig‘amiz.|sammelt Regenwasser, sammelte Regenwasser, hat Regenwasser gesammelt
sich vermehren|zɪç fɛɐ̯ˈmeːʁən|ko‘paymoq|In warmem Wasser vermehren sich manche Insekten schnell.|Iliq suvda ayrim hasharotlar tez ko‘payadi.|vermehrt sich, vermehrte sich, hat sich vermehrt
aussterben|ˈaʊsʃtɛʁbn̩|qirilib ketmoq|Ohne ihren Lebensraum können Tierarten aussterben.|Yashash muhitisiz hayvon turlari qirilib ketishi mumkin.|stirbt aus, starb aus, ist ausgestorben
bedrohen|bəˈdʁoːən|xavf solmoq|Plastik im Meer bedroht viele Tiere.|Dengizdagi plastik ko‘plab hayvonlarga xavf soladi.|bedroht, bedrohte, hat bedroht
zerstören|tsɛɐ̯ˈʃtøːʁən|vayron qilmoq|Das Feuer hat einen Teil des Waldes zerstört.|Yong‘in o‘rmonning bir qismini yo‘q qildi.|zerstört, zerstörte, hat zerstört
verschmutzen|fɛɐ̯ˈʃmʊtsn̩|ifloslantirmoq|Öl kann das Grundwasser verschmutzen.|Neft yerosti suvlarini ifloslantirishi mumkin.|verschmutzt, verschmutzte, hat verschmutzt
verursachen|fɛɐ̯ˈʔuːɐ̯zaxn̩|sabab bo‘lmoq|Der defekte Motor verursacht viel Lärm.|Buzilgan motor ko‘p shovqinga sabab bo‘lmoqda.|verursacht, verursachte, hat verursacht
sich erwärmen|zɪç ɛɐ̯ˈvɛʁmən|isimoq|Der See erwärmt sich im Sommer schnell.|Ko‘l yozda tez isiydi.|erwärmt sich, erwärmte sich, hat sich erwärmt
der Meeresspiegel|ˈmeːʁəsˌʃpiːɡl̩|dengiz sathi|Im Unterricht sprechen wir über den steigenden Meeresspiegel.|Darsda dengiz sathi ko‘tarilishi haqida gaplashamiz.|die Meeresspiegel
ausstoßen|ˈaʊsʃtoːsn̩|chiqarmoq, chiqarib tashlamoq|Alte Motoren stoßen viele Abgase aus.|Eski motorlar ko‘p chiqindi gaz chiqaradi.|stößt aus, stieß aus, hat ausgestoßen
nachhaltig|ˈnaːxhaltɪç|ekologik barqaror|Nachhaltig einkaufen beginnt mit einem guten Plan.|Ekologik mas’uliyatli xarid yaxshi rejadan boshlanadi.|
klimafreundlich|ˈkliːmaˌfʁɔʏntlɪç|iqlimga kam zararli|Wir möchten möglichst klimafreundlich reisen.|Imkon qadar iqlimga kam zarar yetkazib sayohat qilmoqchimiz.|
die Schadstoffe|ˈʃaːtˌʃtɔfə|zararli moddalar|Der Filter hält viele Schadstoffe zurück.|Filtr ko‘plab zararli moddalarni ushlab qoladi.|ko‘plik; birlik: der Schadstoff
erneuerbar|ɛɐ̯ˈnɔʏɐbaːɐ̯|qayta tiklanadigan|Wir informieren uns über erneuerbare Energien.|Qayta tiklanadigan energiya manbalari haqida ma’lumot olyapmiz.|
den Stecker ziehen|deːn ˈʃtɛkɐ ˌtsiːən|vilkani rozetkadan uzmoq|Vor dem Urlaub ziehen wir bei einigen Geräten den Stecker.|Ta’tildan oldin ayrim qurilmalarni rozetkadan uzamiz.|zieht den Stecker, zog den Stecker, hat den Stecker gezogen
regional|ʁeɡi̯oˈnaːl|mahalliy, hududiy|Auf dem Markt kaufen wir regionale Produkte.|Bozordan mahalliy mahsulotlar sotib olamiz.|
saisonal|zɛzoˈnaːl|mavsumiy|Unser Koch verwendet möglichst saisonales Gemüse.|Oshpazimiz imkon qadar mavsumiy sabzavotlardan foydalanadi.|
biologisch|bi̯oˈloːɡɪʃ|biologik, organik|Dieser Hof arbeitet nach biologischen Methoden.|Bu xo‘jalik organik usullar asosida ishlaydi.|
giftig|ˈɡɪftɪç|zaharli|Manche hübschen Pflanzen sind giftig.|Ba’zi chiroyli o‘simliklar zaharli.|
abbaubar|ˈapbaʊbaːɐ̯|parchalanadigan|Laut Verpackung ist diese Tüte biologisch abbaubar.|Qadoqda bu paket biologik parchalanishi aytilgan.|
wassersparend|ˈvasɐˌʃpaːʁənt|suvni tejaydigan|Wir suchen eine wassersparende Waschmaschine.|Suvni tejaydigan kir yuvish mashinasi izlayapmiz.|
wiederaufladbar|ˌviːdɐˈʔaʊflaːtbaːɐ̯|qayta quvvatlanadigan|Diese Batterien sind wiederaufladbar.|Bu batareyalarni qayta quvvatlash mumkin.|
knapp|knap|kam, tanqis|In trockenen Sommern wird Wasser knapp.|Quruq yozlarda suv tanqis bo‘lib qoladi.|
wertvoll|ˈveːɐ̯tfoːl|qimmatli|Trinkwasser ist zu wertvoll zum Verschwenden.|Ichimlik suvi isrof qilish uchun juda qimmatli.|
überflüssig|yːbɐˈflʏsɪç|ortiqcha|Eine zweite Plastiktüte ist überflüssig.|Ikkinchi plastik paket ortiqcha.|
langfristig|ˈlaŋˌfʁɪstɪç|uzoq muddatli|Langfristig spart die neue Heizung Geld.|Yangi isitish tizimi uzoq muddatda pul tejaydi.|
weltweit|ˈvɛltvaɪt|butun dunyoda|Weltweit suchen Menschen nach sauberen Energiequellen.|Butun dunyoda odamlar toza energiya manbalarini izlamoqda.|
insgesamt|ɪnsɡəˈzamt|jami|Insgesamt haben wir zwölf Säcke Müll gesammelt.|Jami o‘n ikki qop axlat yig‘dik.|
statt|ʃtat|o‘rniga|Statt einer Plastiktüte nehme ich meinen Rucksack.|Plastik paket o‘rniga ryukzagimni olaman.|
ohne dass|ˈoːnə das|...masdan, ...magan holda|Das Licht brannte, ohne dass jemand im Zimmer war.|Xonada hech kim bo‘lmasa ham chiroq yonib turardi.|
indem|ɪnˈdeːm|...ish orqali|Wir sparen Energie, indem wir das Licht ausschalten.|Chiroqni o‘chirish orqali energiyani tejaymiz.|
sodass|zoˈdas|natijada, shundayki|Es regnete stark, sodass der Keller voll Wasser lief.|Kuchli yomg‘ir yog‘di, natijada yerto‘la suvga to‘ldi.|
dadurch|daˈdʊʁç|shu orqali, buning natijasida|Ich fahre Rad; dadurch spare ich Fahrgeld.|Velosipedda yuraman; shu orqali yo‘l haqini tejayman.|
immerhin|ɪmɐˈhɪn|har holda, hech bo‘lmaganda|Wir haben immerhin einen Baum gepflanzt.|Har holda, bitta daraxt ekdik.|
möglichst|ˈmøːklɪçst|imkon qadar|Bitte bring möglichst wenig Verpackung mit.|Iltimos, imkon qadar kam qadoq olib kel.|
'''))

BLOCKS.append((19, 'Medien und Verbraucheralltag', r'''
die Medien|ˈmeːdi̯ən|ommaviy axborot vositalari|Die Medien berichten heute über unser Dorf.|Bugun ommaviy axborot vositalari qishlog‘imiz haqida xabar bermoqda.|ko‘plik; birlik: das Medium
die Schlagzeile|ˈʃlaːkˌtsaɪlə|gazetadagi yirik sarlavha|Die Schlagzeile macht mich neugierig auf den Artikel.|Yirik sarlavha maqolaga qiziqishimni uyg‘otadi.|die Schlagzeilen
der Bericht|bəˈʁɪçt|hisobot, reportaj|Der Bericht erklärt die Ursachen des Unfalls.|Reportaj avariya sabablarini tushuntiradi.|die Berichte
der Artikel|aʁˈtiːkl̩|maqola|Den Artikel lese ich später zu Ende.|Maqolani keyin oxirigacha o‘qiyman.|die Artikel
die Überschrift|ˈyːbɐʃʁɪft|sarlavha|Die Überschrift klingt schlimmer als die Nachricht.|Sarlavha xabarning o‘zidan dahshatliroq tuyuladi.|die Überschriften
aus erster Hand|aʊs ˈeːɐ̯stɐ hant|bevosita manbadan|Die Information kommt aus erster Hand: Meine Schwester war dabei.|Ma’lumot bevosita manbadan: opam u yerda bo‘lgan.|
die Mediathek|medi̯aˈteːk|onlayn ko‘rsatuvlar arxivi|Den Film sehe ich später in der Mediathek.|Filmni keyin onlayn arxivda ko‘raman.|die Mediatheken
der Sender|ˈzɛndɐ|telekanal, radiokanal|Dieser Sender spielt nachts nur Jazz.|Bu radiokanal kechasi faqat jaz qo‘yadi.|die Sender
der Zuschauer|ˈtsuːʃaʊɐ|tomoshabin|Ein Zuschauer stellt eine schwierige Frage.|Bir tomoshabin qiyin savol bermoqda.|die Zuschauer
die Werbung|ˈvɛʁbʊŋ|reklama|Die Werbung verspricht erstaunlich viel.|Reklama hayratlanarli darajada ko‘p narsani va’da qiladi.|die Werbungen; odatda birlikda
die Anzeige|ˈantsaɪɡə|e’lon|In der Anzeige steht leider kein Preis.|Afsuski, e’londa narx ko‘rsatilmagan.|die Anzeigen
die Presse|ˈpʁɛsə|matbuot|Die Presse darf bei der Sitzung dabei sein.|Matbuot vakillari majlisda qatnashishi mumkin.|bu ma’noda ko‘plik yo‘q
der Journalist|ʒʊʁnaˈlɪst|jurnalist|Der Journalist prüft die Zahlen vor dem Schreiben.|Jurnalist yozishdan oldin raqamlarni tekshiradi.|die Journalisten
das Interview|ˈɪntɐvjuː|intervyu|Für das Interview haben wir zehn Minuten.|Intervyu uchun o‘n daqiqamiz bor.|die Interviews
die Umfrage|ˈʊmˌfʁaːɡə|so‘rovnoma|An der Umfrage haben hundert Personen teilgenommen.|So‘rovnomada yuz kishi qatnashdi.|die Umfragen
die Falschmeldung|ˈfalʃˌmɛldʊŋ|yolg‘on xabar|Die Zeitung hat die Falschmeldung korrigiert.|Gazeta yolg‘on xabarni tuzatdi.|die Falschmeldungen
die Meldung|ˈmɛldʊŋ|qisqa xabar, bildirishnoma|Auf dem Bildschirm erscheint eine seltsame Meldung.|Ekranda g‘alati bildirishnoma paydo bo‘lmoqda.|die Meldungen
das Gerücht|ɡəˈʁʏçt|mish-mish|Zum Glück war die Nachricht nur ein Gerücht.|Yaxshiyamki, xabar faqat mish-mish ekan.|die Gerüchte
die Wahrheit|ˈvaːɐ̯haɪt|haqiqat|Ich möchte die Wahrheit erfahren.|Men haqiqatni bilmoqchiman.|die Wahrheiten
die Lüge|ˈlyːɡə|yolg‘on|Eine kleine Lüge macht die Sache kompliziert.|Kichkina yolg‘on ishni murakkablashtiradi.|die Lügen
das Netzwerk|ˈnɛtsvɛʁk|tarmoq|Unser Netzwerk verbindet Menschen aus verschiedenen Berufen.|Tarmog‘imiz turli kasbdagi odamlarni bog‘laydi.|die Netzwerke
der Beitrag|ˈbaɪtʁaːk|post, hissa, maqola|Deinen Beitrag habe ich zweimal gelesen.|Postingni ikki marta o‘qidim.|die Beiträge
der Kommentar|kɔmɛnˈtaːɐ̯|izoh|Unter dem Foto steht ein freundlicher Kommentar.|Surat ostida samimiy izoh bor.|die Kommentare
das Profil|pʁoˈfiːl|profil|In meinem Profil steht kein Geburtsdatum.|Profilimda tug‘ilgan sanam ko‘rsatilmagan.|die Profile
die Zugangsdaten|ˈtsuːɡaŋsˌdaːtn̩|kirish ma’lumotlari|Meine Zugangsdaten bewahre ich sicher auf.|Kirish ma’lumotlarimni xavfsiz saqlayman.|faqat ko‘plik
personenbezogen|pɛʁˈzoːnənbəˌtsoːɡn̩|shaxsga oid|Die Webseite speichert personenbezogene Daten.|Veb-sayt shaxsga oid ma’lumotlarni saqlaydi.|
die Privatsphäre|pʁiˈvaːtˌsfɛːʁə|shaxsiy hayot daxlsizligi|Fotos aus der Wohnung gehören zu meiner Privatsphäre.|Uyim ichidagi suratlar shaxsiy hayotimga tegishli.|die Privatsphären
eine Sicherheitskopie anlegen|aɪnə ˈzɪçɐhaɪtskopiː ˌanleːɡn̩|zaxira nusxa yaratmoq|Vor der Reparatur lege ich eine Sicherheitskopie an.|Ta’mirlashdan oldin zaxira nusxa yarataman.|legt an, legte an, hat angelegt
eine Datei anhängen|aɪnə daˈtaɪ ˌanhɛŋən|fayl ilova qilmoq|Ich hänge die Rechnung als Datei an.|Hisob-fakturani fayl sifatida ilova qilaman.|hängt eine Datei an, hängte eine Datei an, hat eine Datei angehängt
eine Verbindung herstellen|aɪnə fɛɐ̯ˈbɪndʊŋ ˌheːɐ̯ʃtɛlən|ulanishni o‘rnatmoq|Das Gerät stellt automatisch eine Verbindung her.|Qurilma avtomatik ulanishni o‘rnatadi.|stellt her, stellte her, hat hergestellt
der Verbraucher|fɛɐ̯ˈbʁaʊxɐ|iste’molchi|Als Verbraucher möchte ich klare Preisangaben.|Iste’molchi sifatida aniq narxlar ko‘rsatilishini istayman.|die Verbraucher
die Ware|ˈvaːʁə|tovar|Die Ware kam in einem beschädigten Karton.|Tovar shikastlangan qutida keldi.|die Waren
die Bestellung|bəˈʃtɛlʊŋ|buyurtma|Meine Bestellung enthält drei Bücher und eine Tasse.|Buyurtmamda uchta kitob va bitta piyola bor.|die Bestellungen
die Sendungsverfolgung|ˈzɛndʊŋsfɛɐ̯ˌfɔlɡʊŋ|jo‘natmani kuzatish|Laut Sendungsverfolgung liegt mein Paket noch im Lager.|Jo‘natmani kuzatish ma’lumotiga ko‘ra, paketim hali omborda.|die Sendungsverfolgungen
der Versand|fɛɐ̯ˈzant|jo‘natish|Der Versand kostet mehr als das gebrauchte Buch.|Jo‘natish ishlatilgan kitobning o‘zidan qimmatroq.|odatda birlikda
der Ratenkauf|ˈʁaːtn̩ˌkaʊf|bo‘lib-bo‘lib to‘lashga xarid|Beim Ratenkauf prüfe ich zuerst die Gesamtkosten.|Bo‘lib to‘lashga xaridda avval jami xarajatni tekshiraman.|die Ratenkäufe
der Zahlungsnachweis|ˈtsaːlʊŋsˌnaːxvaɪs|to‘lovni tasdiqlovchi hujjat|Den Zahlungsnachweis schicke ich Ihnen per E-Mail.|To‘lovni tasdiqlovchi hujjatni sizga elektron xat bilan yuboraman.|die Zahlungsnachweise
die Gewährleistung|ɡəˈvɛːɐ̯ˌlaɪstʊŋ|tovar nuqsonlari bo‘yicha sotuvchi javobgarligi|Die Beratung erklärt mir den Unterschied zwischen Garantie und Gewährleistung.|Maslahat bo‘limi menga kafolat bilan sotuvchi javobgarligi farqini tushuntiradi.|die Gewährleistungen
der Mangel|ˈmaŋl̩|nuqson, kamchilik|Den Mangel habe ich erst zu Hause bemerkt.|Nuqsonni faqat uyga kelgach payqadim.|die Mängel
sich an den Kundenservice wenden|zɪç an deːn ˈkʊndn̩ˌzøːɐ̯vɪs ˌvɛndn̩|mijozlar xizmatiga murojaat qilmoq|Mit dem Foto wende ich mich an den Kundenservice.|Surat bilan mijozlar xizmatiga murojaat qilaman.|wendet sich, wandte sich, hat sich gewandt
die Reklamation|ʁeklamaˈtsi̯oːn|nuqsonli mahsulot bo‘yicha e’tiroz|Für die Reklamation brauche ich den Kaufbeleg.|Nuqson yuzasidan e’tiroz bildirish uchun xarid cheki kerak.|die Reklamationen
der Rücksendeschein|ˈʁʏkzɛndəˌʃaɪn|qaytarib jo‘natish blankasi|Der Rücksendeschein liegt unten im Paket.|Qaytarish blankasi paketning tagida yotibdi.|die Rücksendescheine
die Rückerstattung|ˈʁʏkʔɛɐ̯ˌʃtatʊŋ|to‘langan pulni qaytarish|Die Rückerstattung erfolgt auf mein Bankkonto.|To‘langan pul bank hisobimga qaytariladi.|die Rückerstattungen
die Gutschrift|ˈɡuːtʃʁɪft|hisobga qaytarib yozilgan mablag‘|Auf der nächsten Rechnung erscheint eine Gutschrift.|Keyingi hisob-fakturada qaytarib yozilgan mablag‘ ko‘rinadi.|die Gutschriften
der Kundenservice|ˈkʊndn̩ˌzøːɐ̯vɪs|mijozlarga xizmat ko‘rsatish|Der Kundenservice hilft mir beim Aufbau.|Mijozlarga xizmat ko‘rsatish bo‘limi yig‘ishda menga yordam beradi.|odatda birlikda
das Abonnement|abɔnəˈmãː|obuna|Das Abonnement verlängert sich nicht automatisch.|Obuna avtomatik uzaymaydi.|die Abonnements
der Vertrag|fɛɐ̯ˈtʁaːk|shartnoma|Ich lese den Vertrag bis zur letzten Zeile.|Shartnomani oxirgi satrigacha o‘qiyman.|die Verträge
die Kündigungsfrist|ˈkʏndɪɡʊŋsˌfʁɪst|shartnomani bekor qilishni bildirish muddati|Die Kündigungsfrist steht auf der zweiten Seite.|Bekor qilishni bildirish muddati ikkinchi betda yozilgan.|die Kündigungsfristen
die Bedingung|bəˈdɪŋʊŋ|shart|Diese Bedingung war im Angebot nicht klar.|Bu shart taklifda aniq emas edi.|die Bedingungen
die Bewertung|bəˈveːɐ̯tʊŋ|baho, sharh|Eine einzelne Bewertung überzeugt mich noch nicht.|Bitta sharhning o‘zi meni hali ishontirmaydi.|die Bewertungen
auf dem neuesten Stand sein|aʊf deːm ˈnɔʏəstn̩ ʃtant zaɪn|eng yangi ma’lumotdan xabardor bo‘lmoq|Dank des Newsletters bin ich auf dem neuesten Stand.|Axborot xati tufayli eng yangi ma’lumotlardan xabardorman.|ist auf dem neuesten Stand, war auf dem neuesten Stand, ist auf dem neuesten Stand gewesen
veröffentlichen|fɛɐ̯ˈʔœfn̩tlɪçn̩|e’lon qilmoq, chop etmoq|Wir veröffentlichen die Fotos nur mit Erlaubnis.|Suratlarni faqat ruxsat bilan e’lon qilamiz.|veröffentlicht, veröffentlichte, hat veröffentlicht
recherchieren|ʁeʃɛʁˈʃiːʁən|ma’lumot izlab o‘rganmoq|Für meinen Vortrag recherchiere ich in der Bibliothek.|Ma’ruzam uchun kutubxonada ma’lumot izlayman.|recherchiert, recherchierte, hat recherchiert
überprüfen|yːbɐˈpʁyːfn̩|tekshirib ko‘rmoq|Überprüfe die Quelle, bevor du den Beitrag teilst.|Postni ulashishdan oldin manbani tekshir.|überprüft, überprüfte, hat überprüft
behaupten|bəˈhaʊptn̩|da’vo qilmoq|Die Anzeige behauptet, der Staubsauger sei lautlos.|E’londa changyutkich ovozsiz ekani da’vo qilinadi.|behauptet, behauptete, hat behauptet
kommentieren|kɔmɛnˈtiːʁən|izoh bermoq|Ich kommentiere lieber sachlich als wütend.|Men jahldan ko‘ra xolislik bilan izoh berishni afzal ko‘raman.|kommentiert, kommentierte, hat kommentiert
teilen|ˈtaɪlən|ulashmoq, bo‘lishmoq|Darf ich deinen Beitrag mit meiner Gruppe teilen?|Postingni guruhim bilan ulashsam maylimi?|teilt, teilte, hat geteilt
auf einen Link klicken|aʊf aɪnən ˈlɪŋk ˌklɪkn̩|havolani bosmoq|Ich klicke nur auf Links aus bekannten Quellen.|Faqat tanish manbalardagi havolalarni bosaman.|klickt, klickte, hat geklickt
eine Nachricht weiterleiten|aɪnə ˈnaːxʁɪçt ˌvaɪtɐlaɪtn̩|xabarni boshqaga yubormoq|Darf ich deine Nachricht an die Gruppe weiterleiten?|Xabaringni guruhga yuborsam maylimi?|leitet weiter, leitete weiter, hat weitergeleitet
Daten sichern|ˈdaːtn̩ ˌzɪçɐn|ma’lumotlarning zaxira nusxasini saqlamoq|Vor dem Update sichere ich meine Daten.|Yangilashdan oldin ma’lumotlarimning zaxirasini saqlayman.|sichert Daten, sicherte Daten, hat Daten gesichert
sich ausloggen|zɪç ˈaʊslɔɡn̩|hisobdan chiqmoq|Am öffentlichen Computer logge ich mich immer aus.|Jamoat kompyuterida hisobimdan doim chiqaman.|loggt sich aus, loggte sich aus, hat sich ausgeloggt
sperren|ˈʃpɛʁən|bloklamoq|Nach dem Diebstahl lasse ich die Karte sperren.|O‘g‘rilikdan keyin kartani bloklataman.|sperrt, sperrte, hat gesperrt
abonnieren|abɔˈniːʁən|obuna bo‘lmoq|Meine Oma abonniert einen Podcast über Technik.|Buvim texnika haqidagi podkastga obuna bo‘ladi.|abonniert, abonnierte, hat abonniert
einen Vertrag abschließen|aɪnən fɛɐ̯ˈtʁaːk ˌapʃliːsn̩|shartnoma tuzmoq|Ich schließe keinen Vertrag ab, den ich nicht verstehe.|Tushunmagan shartnomamni tuzmayman.|schließt ab, schloss ab, hat abgeschlossen
von einem Vertrag zurücktreten|fɔn aɪnəm fɛɐ̯ˈtʁaːk tsuˌʁʏktʁeːtn̩|shartnomadan voz kechmoq|Ich frage nach, ob ich vom Vertrag zurücktreten kann.|Shartnomadan voz kecha olishimni so‘rayman.|tritt zurück, trat zurück, ist zurückgetreten
auf etwas bestehen|aʊf ˈʔɛtvas bəˌʃteːən|biror narsani qat’iy talab qilmoq|Ich bestehe auf einer schriftlichen Antwort.|Yozma javob berilishini qat’iy talab qilaman.|besteht auf, bestand auf, hat auf etwas bestanden; auf + Dativ
eine Bestellung rückgängig machen|aɪnə bəˈʃtɛlʊŋ ˈʁʏkɡɛŋɪç ˌmaxn̩|buyurtmani bekor qilmoq|Kann ich die Bestellung noch rückgängig machen?|Buyurtmani hali bekor qila olamanmi?|macht rückgängig, machte rückgängig, hat rückgängig gemacht
zurücksenden|tsuˈʁʏkˌzɛndn̩|qaytarib jo‘natmoq|Die beschädigte Lampe sende ich morgen zurück.|Shikastlangan chiroqni ertaga qaytarib jo‘nataman.|sendet zurück, sendete zurück, hat zurückgesendet
Geld zurückfordern|ˈɡɛlt tsuˌʁʏkfɔʁdɐn|pulni qaytarishni talab qilmoq|Für die nicht gelieferte Ware fordere ich mein Geld zurück.|Yetkazilmagan tovar uchun pulimni qaytarishni talab qilaman.|fordert zurück, forderte zurück, hat zurückgefordert
berechnen|bəˈʁɛçnən|hisoblamoq, haq olmoq|Für die Beratung berechnet die Werkstatt nichts.|Ustaxona maslahat uchun haq olmaydi.|berechnet, berechnete, hat berechnet
abbuchen|ˈapbuːxn̩|hisobdan yechmoq|Die Bank bucht den Betrag am Montag ab.|Bank summani dushanba kuni hisobdan yechadi.|bucht ab, buchte ab, hat abgebucht
per Lastschrift zahlen|pɛʁ ˈlastʃʁɪft ˌtsaːlən|hisobdan avtomatik yechish orqali to‘lamoq|Die monatliche Gebühr zahle ich per Lastschrift.|Oylik to‘lovni hisobdan avtomatik yechish orqali to‘layman.|zahlt, zahlte, hat gezahlt
liefern|ˈliːfɐn|yetkazib bermoq|Der Laden liefert den Schrank bis zur Wohnungstür.|Do‘kon shkafni kvartira eshigigacha yetkazib beradi.|liefert, lieferte, hat geliefert
das Preis-Leistungs-Verhältnis|ˈpʁaɪsˈlaɪstʊŋs fɛɐ̯ˌhɛltnɪs|narx va sifat nisbati|Bei diesem Gerät stimmt das Preis-Leistungs-Verhältnis.|Bu qurilmada narx va sifat nisbati yaxshi.|die Preis-Leistungs-Verhältnisse
bewerten|bəˈveːɐ̯tn̩|baholamoq|Bewerte bitte auch die Lieferung, nicht nur das Produkt.|Iltimos, faqat mahsulotni emas, yetkazib berishni ham bahola.|bewertet, bewertete, hat bewertet
glaubwürdig|ˈɡlaʊpˌvʏʁdɪç|ishonchli|Der Bericht wirkt durch seine genauen Quellen glaubwürdig.|Aniq manbalari tufayli reportaj ishonchli ko‘rinadi.|
sachlich|ˈzaxlɪç|xolis, ishga oid|Trotz seiner Wut bleibt sein Brief sachlich.|Jahli chiqqaniga qaramay, xati xolis yozilgan.|
kritisch|ˈkʁiːtɪʃ|tanqidiy|Lies die Werbung ruhig etwas kritisch.|Reklamani biroz tanqidiy ko‘z bilan o‘qi.|
aktuell|akˈtu̯ɛl|dolzarb, hozirgi|Ist diese Preisliste noch aktuell?|Bu narxlar ro‘yxati hali amal qiladimi?|
drahtlos|ˈdʁaːtloːs|simsiz|Der Drucker verbindet sich drahtlos mit dem Laptop.|Printer noutbukka simsiz ulanadi.|
die Einwilligung|ˈaɪnvɪlɪɡʊŋ|rozilik|Ohne deine Einwilligung veröffentliche ich das Foto nicht.|Roziligingsiz suratni e’lon qilmayman.|die Einwilligungen
automatisch|aʊtoˈmaːtɪʃ|avtomatik|Die Datei wird automatisch gespeichert.|Fayl avtomatik saqlanadi.|
preisgünstig|ˈpʁaɪsˌɡʏnstɪç|narxi qulay|Ich suche ein preisgünstiges Gerät für einfache Aufgaben.|Oddiy ishlar uchun narxi qulay qurilma izlayapman.|
kostenpflichtig|ˈkɔstn̩ˌpflɪçtɪç|pullik|Nach einem Monat wird der Zugang kostenpflichtig.|Bir oydan keyin kirish pullik bo‘ladi.|
gebraucht|ɡəˈbʁaʊxt|ishlatilgan|Mein gebrauchtes Fahrrad fährt wunderbar.|Ishlatilgan velosipedim ajoyib yuradi.|
mangelhaft|ˈmaŋl̩haft|nuqsonli, qoniqarsiz|Die Verarbeitung der Tasche ist mangelhaft.|Sumkaning ishlanish sifati qoniqarsiz.|
defekt|deˈfɛkt|nosoz|Der Drucker ist defekt, aber die Kaffeemaschine lebt noch.|Printer nosoz, lekin qahva mashinasi hali tirik.|
werbefrei|ˈvɛʁbəˌfʁaɪ|reklamasiz|Diese Sendung kann ich auch werbefrei hören.|Bu eshittirishni reklamasiz ham tinglay olaman.|
auf Lager|aʊf ˈlaːɡɐ|omborda mavjud|Haben Sie dieses Modell noch auf Lager?|Bu model omboringizda hali bormi?|
lieferbar|ˈliːfɐbaːɐ̯|yetkazib berish mumkin bo‘lgan|Das rote Modell ist erst im Mai lieferbar.|Qizil modelni faqat mayda yetkazib berish mumkin.|
unverbindlich|ˈʊnfɛɐ̯ˌbɪntlɪç|majburiyat yuklamaydigan|Ich bitte zunächst um ein unverbindliches Angebot.|Avval majburiyat yuklamaydigan taklif berishingizni so‘rayman.|
ausdrücklich|ˈaʊsˌdʁʏklɪç|aniq ta’kidlab|Ich habe ausdrücklich eine blaue Tasche bestellt.|Men aynan ko‘k sumka buyurtma qilganman.|
angeblich|ˈanɡeːplɪç|aytishlaricha, go‘yoki|Angeblich putzt dieser Roboter sogar die Fenster.|Aytishlaricha, bu robot hatto derazalarni ham tozalaydi.|
tatsächlich|ˈtaːtˌzɛçlɪç|haqiqatan|Das Paket kam tatsächlich schon am nächsten Tag.|Paket haqiqatan ham ertasigayoq keldi.|
offenbar|ˈɔfn̩baːɐ̯|aftidan|Offenbar wurde meine Bestellung vergessen.|Aftidan, buyurtmam unutilgan.|
zumindest|tsuˈmɪndəst|hech bo‘lmaganda|Zumindest funktioniert die Rücksendung problemlos.|Hech bo‘lmaganda, qaytarib jo‘natish muammosiz ishlayapti.|
beziehungsweise|bəˈtsiːʊŋsˌvaɪzə|aniqrog‘i; mos ravishda|Wir treffen uns am Freitag, beziehungsweise am Samstag, falls du arbeiten musst.|Juma kuni uchrashamiz, aniqrog‘i, ishlashing kerak bo‘lsa, shanba kuni.|
sowohl … als auch|zoˈvoːl als aʊx|ham … ham|Ich lese sowohl Zeitungen als auch Blogs.|Men gazetalarni ham, bloglarni ham o‘qiyman.|
weder … noch|ˈveːdɐ nɔx|na … na|Der Drucker druckt weder Texte noch Bilder.|Printer na matnlarni, na rasmlarni chiqaryapti.|
entweder … oder|ˈɛntveːdɐ ˈoːdɐ|yoki … yoki|Entweder wir reparieren das Gerät, oder wir geben es zurück.|Yoki qurilmani tuzatamiz, yoki qaytarib beramiz.|
'''))

BLOCKS.append((20, 'Beruf und Weiterbildung', r'''
eine Bewerbung einreichen|aɪnə bəˈvɛʁbʊŋ ˌaɪnʁaɪçn̩|ishga ariza topshirmoq|Bis Freitag möchte ich meine Bewerbung einreichen.|Jumagacha ishga arizamni topshirmoqchiman.|reicht ein, reichte ein, hat eingereicht
lückenlos|ˈlʏkn̩loːs|bo‘shliqsiz, uzluksiz|Mein Lebenslauf muss nicht perfekt, aber lückenlos sein.|Tarjimayi holim mukammal bo‘lmasa ham, unda bo‘shliqlar bo‘lmasligi kerak.|
sich auf eine Anzeige melden|zɪç aʊf aɪnə ˈantsaɪɡə ˌmɛldn̩|e’lon bo‘yicha murojaat qilmoq|Ich melde mich auf Ihre Anzeige für eine Küchenhilfe.|Oshxona yordamchisi haqidagi e’loningiz bo‘yicha murojaat qilyapman.|meldet sich, meldete sich, hat sich gemeldet
einen guten Eindruck machen|aɪnən ˈɡuːtn̩ ˈaɪndʁʊk ˌmaxn̩|yaxshi taassurot qoldirmoq|Mit ehrlichen Antworten mache ich einen guten Eindruck.|Rost javoblar bilan yaxshi taassurot qoldiraman.|macht, machte, hat gemacht
die Festanstellung|ˈfɛstʔanˌʃtɛlʊŋ|doimiy shtatdagi ish|Nach dem Praktikum bekam sie eine Festanstellung.|Amaliyotdan keyin u doimiy ishga olindi.|die Festanstellungen
der Personalmangel|pɛʁzoˈnaːlˌmaŋl̩|xodimlar yetishmasligi|Wegen Personalmangels schließt der Laden früher.|Xodimlar yetishmagani sababli do‘kon ertaroq yopiladi.|ko‘plik yo‘q
die Arbeitskraft|ˈaʁbaɪtsˌkʁaft|ishchi kuchi; xodim|Der Betrieb sucht zusätzliche Arbeitskräfte.|Korxona qo‘shimcha xodimlar izlamoqda.|die Arbeitskräfte
das Betriebsklima|bəˈtʁiːpsˌkliːma|ishxonadagi muhit|Ein gutes Betriebsklima ist mir wichtiger als ein schickes Büro.|Ishxonadagi yaxshi muhit menga chiroyli ofisdan muhimroq.|ko‘plik kam: die Betriebsklimata
die Zuständigkeit|ˈtsuːʃtɛndɪçkaɪt|vakolat, mas’ullik doirasi|Die Zuständigkeiten im Team sind klar verteilt.|Jamoadagi mas’uliyat doiralari aniq taqsimlangan.|die Zuständigkeiten
die Lohnabrechnung|ˈloːnʔapˌʁɛçnʊŋ|ish haqi hisob-kitob varaqasi|Auf meiner Lohnabrechnung fehlt eine Überstunde.|Ish haqi varaqamda bir qo‘shimcha soat hisobga olinmagan.|die Lohnabrechnungen
die Führungskraft|ˈfyːʁʊŋsˌkʁaft|rahbar xodim|Eine gute Führungskraft hört ihrem Team zu.|Yaxshi rahbar o‘z jamoasini tinglaydi.|die Führungskräfte
der Betriebsrat|bəˈtʁiːpsˌʁaːt|korxona xodimlari kengashi|Bei Problemen kann ich mich an den Betriebsrat wenden.|Muammolarda korxona xodimlari kengashiga murojaat qila olaman.|die Betriebsräte
die Gewerkschaft|ɡəˈvɛʁkʃaft|kasaba uyushmasi|Die Gewerkschaft informiert über Arbeitsrechte.|Kasaba uyushmasi mehnat huquqlari haqida ma’lumot beradi.|die Gewerkschaften
die Gehaltserhöhung|ɡəˈhaltsʔɛɐ̯ˌhøːʊŋ|maosh oshishi|Über eine Gehaltserhöhung sprechen wir im Dezember.|Maoshni oshirish haqida dekabrda gaplashamiz.|die Gehaltserhöhungen
der Mindestlohn|ˈmɪndəstˌloːn|eng kam ish haqi|Im Kurs sprechen wir über den Mindestlohn.|Kursda eng kam ish haqi haqida gaplashamiz.|die Mindestlöhne
der Dienstplan|ˈdiːnstˌplaːn|navbatchilik jadvali|Der neue Dienstplan hängt neben der Küchentür.|Yangi navbatchilik jadvali oshxona eshigi yonida osilgan.|die Dienstpläne
Überstunden abbauen|ˈyːbɐˌʃtʊndn̩ ˈapbaʊən|qo‘shimcha ish soatlari evaziga dam olmoq|Am Freitag baue ich Überstunden ab.|Juma kuni qo‘shimcha ishlagan soatlarim evaziga dam olaman.|baut ab, baute ab, hat abgebaut
die Elternzeit|ˈɛltɐnˌtsaɪt|bola parvarishi ta’tili|Nach der Geburt nimmt auch der Vater Elternzeit.|Bola tug‘ilgach, ota ham parvarish ta’tiliga chiqadi.|die Elternzeiten
die Gleitzeit|ˈɡlaɪtˌtsaɪt|moslashuvchan ish boshlash vaqti|Dank Gleitzeit kann ich mein Kind morgens begleiten.|Moslashuvchan ish vaqti tufayli ertalab bolamga hamroh bo‘la olaman.|ko‘plik yo‘q
sich bewähren|zɪç bəˈvɛːʁən|o‘zini yaxshi ko‘rsatmoq, foydasi bilinmoq|Unser neuer Arbeitsplan hat sich bewährt.|Yangi ish rejamiz o‘zini oqladi.|bewährt sich, bewährte sich, hat sich bewährt
die Befristung|bəˈfʁɪstʊŋ|muddat bilan cheklash|Die Befristung des Vertrags macht mir Sorgen.|Shartnoma muddati cheklangani meni tashvishlantiradi.|die Befristungen
abschalten können|ˈapʃaltn̩ ˌkœnən|ish tashvishidan chalg‘iy olmoq|Nach der Arbeit kann ich beim Schwimmen gut abschalten.|Ishdan keyin suzishda tashvishlardan yaxshi chalg‘iy olaman.|kann abschalten, konnte abschalten, hat abschalten können
eine Sitzung eröffnen|aɪnə ˈzɪtsʊŋ ɛɐ̯ˌʔœfnən|yig‘ilishni ochmoq|Die Teamleiterin eröffnet die Sitzung mit einer Frage.|Jamoa rahbari yig‘ilishni savol bilan ochadi.|eröffnet, eröffnete, hat eröffnet
Protokoll führen|pʁotoˈkɔl ˌfyːʁən|bayonnoma yuritmoq|Bei der heutigen Sitzung führe ich Protokoll.|Bugungi yig‘ilishda bayonnomani men yuritaman.|führt Protokoll, führte Protokoll, hat Protokoll geführt
die Auftragslage|ˈaʊftʁaːksˌlaːɡə|buyurtmalar holati|Wegen der guten Auftragslage stellen wir Personal ein.|Buyurtmalar ko‘pligi tufayli xodimlar yollayapmiz.|ko‘plik kam: die Auftragslagen
die Arbeitsbelastung|ˈaʁbaɪtsbəˌlastʊŋ|ish yuklamasi|Vor Feiertagen ist die Arbeitsbelastung besonders hoch.|Bayramlardan oldin ish yuklamasi ayniqsa yuqori.|die Arbeitsbelastungen
die Teamarbeit|ˈtiːmˌʔaʁbaɪt|jamoaviy ish|Bei diesem Projekt ist Teamarbeit besonders wichtig.|Bu loyihada jamoaviy ish ayniqsa muhim.|odatda birlikda
die Kenntnis|ˈkɛntnɪs|bilim|Für die Stelle brauche ich gute Computerkenntnisse.|Bu ish uchun kompyuterni yaxshi bilishim kerak.|die Kenntnisse
Berufserfahrung sammeln|bəˈʁuːfsʔɛɐ̯ˌfaːʁʊŋ ˈzaml̩n|kasbiy tajriba orttirmoq|Im Hotel sammle ich meine erste Berufserfahrung.|Mehmonxonada ilk kasbiy tajribamni orttiryapman.|sammelt, sammelte, hat gesammelt
die Fachkraft|ˈfaxˌkʁaft|malakali mutaxassis|Für die Reparatur brauchen wir eine Fachkraft.|Ta’mirlash uchun malakali mutaxassis kerak.|die Fachkräfte
die Anforderung|ˈanfɔʁdəʁʊŋ|talab|Eine wichtige Anforderung ist gutes Deutsch.|Muhim talablardan biri nemis tilini yaxshi bilish.|die Anforderungen
belastende Situationen meistern|bəˈlastəndə zitu̯aˌtsi̯oːnən ˈmaɪstɐn|qiyin vaziyatlarni uddalamoq|Mit Ruhe kann ich belastende Situationen besser meistern.|Xotirjamlik bilan qiyin vaziyatlarni yaxshiroq uddalay olaman.|meistert, meisterte, hat gemeistert
an sich arbeiten|an zɪç ˈaʁbaɪtn̩|o‘z ustida ishlamoq|Ich arbeite an mir und nehme Kritik ernst.|O‘z ustimda ishlayman va tanqidga jiddiy qarayman.|arbeitet an sich, arbeitete an sich, hat an sich gearbeitet
eine Lehre machen|aɪnə ˈleːʁə ˌmaxn̩|kasb-hunar ta’limini olmoq|Mein Bruder macht eine Lehre als Elektriker.|Ukam elektriklik kasbini o‘rganmoqda.|macht eine Lehre, machte eine Lehre, hat eine Lehre gemacht
der Ausbildungsplatz|ˈaʊsbɪldʊŋsˌplats|kasb o‘rganish o‘rni|Er sucht einen Ausbildungsplatz als Bäcker.|U novvoylikni o‘rganish uchun o‘rin izlayapti.|die Ausbildungsplätze
der Auszubildende|ˈaʊstsuˌbɪldəndə|kasb o‘rganuvchi|Der Auszubildende zeigt mir die neue Maschine.|Kasb o‘rganuvchi menga yangi mashinani ko‘rsatmoqda.|die Auszubildenden; ein Auszubildender
der Berufseinstieg|bəˈʁuːfsʔaɪnˌʃtiːk|kasbiy faoliyatni boshlash|Ein Praktikum kann den Berufseinstieg erleichtern.|Amaliyot kasbiy faoliyatni boshlashni osonlashtirishi mumkin.|die Berufseinstiege
der Probetag|ˈpʁoːbəˌtaːk|sinov ish kuni|Am Probetag lerne ich das Team kennen.|Sinov ish kunida jamoa bilan tanishaman.|die Probetage
die Umschulung|ˈʊmˌʃuːlʊŋ|boshqa kasbga qayta tayyorlash|Nach der Umschulung arbeitet er als Fahrer.|Qayta tayyorlashdan so‘ng u haydovchi bo‘lib ishlaydi.|die Umschulungen
die Fortbildung|ˈfɔʁtˌbɪldʊŋ|kasbiy malaka oshirish|Unsere Fortbildung behandelt neue Pflegetechniken.|Malaka oshirishimiz yangi parvarish usullariga bag‘ishlangan.|die Fortbildungen
eine Prüfung wiederholen|aɪnə ˈpʁyːfʊŋ viːdɐˌhoːlən|imtihonni qayta topshirmoq|Im Herbst kann ich die Prüfung wiederholen.|Kuzda imtihonni qayta topshira olaman.|wiederholt, wiederholte, hat wiederholt
die Referenz|ʁefeˈʁɛnts|tavsiyanoma, tavsiya beruvchi manba|Meine frühere Chefin darf ich als Referenz angeben.|Oldingi rahbarimni tavsiya beruvchi sifatida ko‘rsatishim mumkin.|die Referenzen
der Bildungsweg|ˈbɪldʊŋsˌveːk|ta’lim yo‘li|Mein Bildungsweg war nicht immer einfach.|Ta’lim yo‘lim doim ham oson bo‘lmagan.|die Bildungswege
die Anerkennung|ˈanʔɛɐ̯ˌkɛnʊŋ|tan olish, e’tirof|Für die Anerkennung brauche ich eine Übersetzung.|Tan olish uchun menga tarjima kerak.|die Anerkennungen
die Nachprüfung|ˈnaːxˌpʁyːfʊŋ|qayta yoki qo‘shimcha imtihon|Die Nachprüfung findet im September statt.|Qayta imtihon sentabrda o‘tkaziladi.|die Nachprüfungen
sich qualifizieren für|zɪç kvalifiˈtsiːʁən fyːɐ̯|...uchun malaka hosil qilmoq|Mit diesem Kurs qualifiziere ich mich für neue Aufgaben.|Bu kurs bilan yangi vazifalar uchun malakamni oshiraman.|qualifiziert sich, qualifizierte sich, hat sich qualifiziert; für + Akkusativ
die Karriere|kaˈʁi̯eːʁə|kasbiy rivojlanish|Für meine Karriere möchte ich nicht alles opfern.|Kasbiy rivojim uchun hamma narsani qurbon qilmoqchi emasman.|die Karrieren
die Arbeitslosigkeit|ˈaʁbaɪtsloːzɪçkaɪt|ishsizlik|Während der Arbeitslosigkeit besuchte er einen Kurs.|Ishsiz paytida u kursga qatnashdi.|ko‘plik yo‘q
die Rente|ˈʁɛntə|pensiya|In der Rente möchte meine Mutter reisen.|Onam pensiyada sayohat qilmoqchi.|die Renten
die Vereinbarkeit|fɛɐ̯ˈʔaɪnbaːɐ̯kaɪt|birga olib borish imkoniyati|Flexible Zeiten verbessern die Vereinbarkeit von Familie und Beruf.|Moslashuvchan vaqtlar oila va ishni birga olib borishni osonlashtiradi.|ko‘plik yo‘q
sich beruflich verändern|zɪç bəˈʁuːflɪç fɛɐ̯ˌʔɛndɐn|kasbiy yo‘nalishini o‘zgartirmoq|Nach zehn Jahren möchte ich mich beruflich verändern.|O‘n yildan keyin kasbiy yo‘nalishimni o‘zgartirmoqchiman.|verändert sich, veränderte sich, hat sich verändert
Personal suchen|pɛʁzoˈnaːl ˌzuːxn̩|xodim izlamoq|Das Café sucht Personal für den Sommer.|Kafe yoz uchun xodimlar izlamoqda.|sucht Personal, suchte Personal, hat Personal gesucht
entlassen|ɛntˈlasn̩|ishdan bo‘shatmoq; chiqarib yubormoq|Der Betrieb musste mehrere Mitarbeiter entlassen.|Korxona bir necha xodimni bo‘shatishga majbur bo‘ldi.|entlässt, entließ, hat entlassen
den Lebensunterhalt verdienen|deːn ˈleːbn̩sʔʊntɐhalt fɛɐ̯ˌdiːnən|tirikchilik uchun pul topmoq|Mit Übersetzungen verdient sie ihren Lebensunterhalt.|U tarjima bilan tirikchilik qiladi.|verdient, verdiente, hat verdient
eine Gehaltsvorstellung nennen|aɪnə ɡəˈhaltsfoːɐ̯ʃtɛlʊŋ ˌnɛnən|kutilayotgan maoshni aytmoq|Im Gespräch soll ich meine Gehaltsvorstellung nennen.|Suhbatda kutayotgan maoshimni aytishim kerak.|nennt, nannte, hat genannt
eine Anleitung geben|aɪnə ˈanlaɪtʊŋ ˌɡeːbn̩|qanday bajarishni ko‘rsatmoq|Der Meister gibt mir eine klare Anleitung.|Usta menga qanday bajarishni aniq ko‘rsatadi.|gibt eine Anleitung, gab eine Anleitung, hat eine Anleitung gegeben
sich weiterbilden|zɪç ˈvaɪtɐˌbɪldn̩|malakasini oshirmoq|Auch mit fünfzig bildet sie sich weiter.|U ellik yoshida ham malakasini oshiradi.|bildet sich weiter, bildete sich weiter, hat sich weitergebildet
anerkennen|ˈanʔɛɐ̯ˌkɛnən|tan olmoq|Die Behörde erkennt mein Zeugnis an.|Idora guvohnomamni tan oladi.|erkennt an, erkannte an, hat anerkannt
eine Prüfung ablegen|aɪnə ˈpʁyːfʊŋ ˌapleːɡn̩|imtihon topshirmoq|Im Juni lege ich die B1-Prüfung ab.|Iyun oyida B1 imtihonini topshiraman.|legt ab, legte ab, hat abgelegt
einen zweiten Anlauf nehmen|aɪnən ˈtsvaɪtn̩ ˈanlaʊf ˌneːmən|ikkinchi bor urinmoq|Nach dem Misserfolg nehme ich einen zweiten Anlauf.|Muvaffaqiyatsizlikdan keyin ikkinchi bor urinaman.|nimmt einen Anlauf, nahm einen Anlauf, hat einen Anlauf genommen
nachholen|ˈnaːxhoːlən|qoldirilganini keyin bajarmoq|Den verpassten Unterricht hole ich am Samstag nach.|Qoldirilgan darsni shanba kuni o‘zlashtiraman.|holt nach, holte nach, hat nachgeholt
sich spezialisieren|zɪç ʃpetsi̯aliˈziːʁən|ixtisoslashmoq|Sie spezialisiert sich auf die Pflege älterer Menschen.|U keksalar parvarishiga ixtisoslashmoqda.|spezialisiert sich, spezialisierte sich, hat sich spezialisiert
etwas in Angriff nehmen|ˈʔɛtvas ɪn ˈanɡʁɪf ˌneːmən|ishga kirishmoq|Nach der Pause nehmen wir die Inventur in Angriff.|Tanaffusdan keyin mol-mulkni hisobdan o‘tkazishga kirishamiz.|nimmt in Angriff, nahm in Angriff, hat in Angriff genommen
für jemanden einspringen|fyːɐ̯ ˈjeːmandn̩ ˌaɪnʃpʁɪŋən|birovning o‘rniga chiqmoq|Am Montag springe ich für meinen Kollegen ein.|Dushanba kuni hamkasbim o‘rniga chiqaman.|springt ein, sprang ein, ist eingesprungen
an einem Strang ziehen|an aɪnəm ˈʃtʁaŋ ˌtsiːən|bir maqsad yo‘lida birlashmoq|Wenn wir an einem Strang ziehen, schaffen wir den Auftrag.|Bir maqsadda birlashsak, buyurtmani bajaramiz.|zieht, zog, hat gezogen
leiten|ˈlaɪtn̩|boshqarmoq|Nächsten Monat leite ich mein erstes Projekt.|Kelasi oy birinchi loyihamni boshqaraman.|leitet, leitete, hat geleitet
sich zurechtfinden|zɪç tsuˈʁɛçtˌfɪndn̩|moslashib yo‘lini topmoq|Im neuen Betrieb finde ich mich langsam zurecht.|Yangi korxonada asta-sekin ishga moslashyapman.|findet sich zurecht, fand sich zurecht, hat sich zurechtgefunden
kündbar|ˈkʏntbaːɐ̯|bekor qilish mumkin bo‘lgan|Der Vertrag ist monatlich kündbar.|Shartnomani har oy bekor qilish mumkin.|
befördern|bəˈfœʁdɐn|lavozimini oshirmoq; tashimoq|Die Firma befördert ihn zum Teamleiter.|Firma uni jamoa rahbari lavozimiga ko‘tarmoqda.|befördert, beförderte, hat befördert
den Überblick behalten|deːn ˈyːbɐblɪk bəˌhaltn̩|vaziyatni nazoratda tutmoq|Mit einer Liste behalte ich den Überblick.|Ro‘yxat yordamida ishlarni nazoratda tutaman.|behält den Überblick, behielt den Überblick, hat den Überblick behalten
eine Vereinbarung treffen|aɪnə fɛɐ̯ˈʔaɪnbaːʁʊŋ ˌtʁɛfn̩|kelishuvga erishmoq|Über die Arbeitszeiten treffen wir eine klare Vereinbarung.|Ish vaqti bo‘yicha aniq kelishuvga erishamiz.|trifft eine Vereinbarung, traf eine Vereinbarung, hat eine Vereinbarung getroffen
etwas nach hinten verschieben|ˈʔɛtvas naːx ˈhɪntn̩ fɛɐ̯ˌʃiːbn̩|biror narsani keyinroqqa surmoq|Wir verschieben den Projektstart um zwei Tage nach hinten.|Loyiha boshlanishini ikki kun keyinga suramiz.|verschiebt, verschob, hat verschoben
eine Absage erhalten|aɪnə ˈapzaːɡə ɛɐ̯ˌhaltn̩|rad javobi olmoq|Leider habe ich auf meine Bewerbung eine Absage erhalten.|Afsuski, ishga arizamga rad javobi oldim.|erhält, erhielt, hat erhalten
eine Stelle antreten|aɪnə ˈʃtɛlə ˌantʁeːtn̩|yangi ishni boshlamoq|Am ersten Oktober trete ich meine neue Stelle an.|Birinchi oktabrda yangi ishimni boshlayman.|tritt an, trat an, hat angetreten
sich eignen|zɪç ˈaɪɡnən|mos kelmoq, yaroqli bo‘lmoq|Der Kurs eignet sich für Berufstätige.|Bu kurs ishlaydigan odamlarga mos keladi.|eignet sich, eignete sich, hat sich geeignet
beruflich|bəˈʁuːflɪç|kasbiy, ishga oid|Beruflich bin ich oft unterwegs.|Ish bilan tez-tez safarda bo‘laman.|
freiberuflich|ˈfʁaɪbəˌʁuːflɪç|mustaqil mutaxassis sifatida|Sie arbeitet freiberuflich als Grafikerin.|U mustaqil grafik dizayner bo‘lib ishlaydi.|
arbeitssuchend|ˈaʁbaɪtsˌzuːxn̩t|ish izlayotgan|Seit seinem Umzug ist er arbeitssuchend.|Ko‘chganidan beri u ish izlayapti.|
auf Dauer|aʊf ˈdaʊɐ|uzoq muddatga, doimiy ravishda|Auf Dauer möchte ich näher an meinem Arbeitsplatz wohnen.|Uzoq muddatda ishxonamga yaqinroq yashamoqchiman.|
ortsunabhängig|ˈɔʁtsʔʊnʔapˌhɛŋɪç|muayyan joyga bog‘liq bo‘lmagan|Manche Aufgaben kann ich ortsunabhängig erledigen.|Ayrim vazifalarni istalgan joyda bajara olaman.|
belastbar|bəˈlastbaːɐ̯|bosimga chidamli|Auch an stressigen Tagen bleibt sie belastbar.|Hatto og‘ir kunlarda ham u bosimga chidamli bo‘lib qoladi.|
teamfähig|ˈtiːmˌfɛːɪç|jamoada ishlay oladigan|Wir suchen eine teamfähige Person für die Küche.|Oshxona uchun jamoada ishlay oladigan odam izlayapmiz.|
sorgfältig|ˈzɔʁkˌfɛltɪç|puxta, sinchkov|Bitte prüfe die Zahlen sorgfältig.|Iltimos, raqamlarni sinchkovlik bilan tekshir.|
der Quereinsteiger|ˈkveːɐ̯ʔaɪnˌʃtaɪɡɐ|boshqa kasbdan o‘tgan xodim|Als Quereinsteiger bringe ich andere Erfahrungen mit.|Boshqa kasbdan o‘tgan xodim sifatida boshqacha tajribam bor.|die Quereinsteiger
sich auskennen mit|zɪç ˈaʊskɛnən mɪt|...ni yaxshi bilmoq|Mit diesem Programm kenne ich mich gut aus.|Bu dasturni yaxshi bilaman.|kennt sich aus, kannte sich aus, hat sich ausgekannt; mit + Dativ
vorgeschrieben|ˈfoːɐ̯ɡəˌʃʁiːbn̩|talab etilgan, majburiy belgilangan|In der Werkstatt sind Sicherheitsschuhe vorgeschrieben.|Ustaxonada himoya oyoq kiyimi kiyish majburiy.|
praktisch|ˈpʁaktɪʃ|amaliy; qulay|Am Freitag üben wir praktische Aufgaben.|Juma kuni amaliy topshiriqlarni mashq qilamiz.|
theoretisch|teoˈʁeːtɪʃ|nazariy|Theoretisch kenne ich die Maschine schon.|Nazariy jihatdan bu mashinani allaqachon bilaman.|
frei sprechen|ˈfʁaɪ ˌʃpʁɛçn̩|matnga qaramay gapirmoq|Im Vortrag versuche ich, möglichst frei zu sprechen.|Ma’ruzada imkon qadar matnga qaramay gapirishga harakat qilaman.|spricht frei, sprach frei, hat frei gesprochen
fachlich|ˈfaxlɪç|mutaxassislikka oid|Fachlich habe ich in diesem Jahr viel gelernt.|Bu yil mutaxassisligim bo‘yicha ko‘p narsa o‘rgandim.|
gründlich|ˈɡʁʏntlɪç|batafsil, puxta|Vor der Übergabe reinigen wir alles gründlich.|Topshirishdan oldin hamma narsani yaxshilab tozalaymiz.|
termingerecht|tɛʁˈmiːnɡəˌʁɛçt|belgilangan vaqtda|Wir haben den Auftrag termingerecht abgeschlossen.|Buyurtmani belgilangan vaqtda tugatdik.|
ausgelastet|ˈaʊsɡəˌlastət|to‘liq band, yuklamasi to‘lgan|Diese Woche ist unser Team völlig ausgelastet.|Bu hafta jamoamiz to‘liq band.|
brutto|ˈbʁʊto|soliqdan oldingi|Im Vertrag steht das Gehalt brutto.|Shartnomada maosh soliqdan oldingi miqdorda ko‘rsatilgan.|
netto|ˈnɛto|soliqdan keyingi|Wie viel bleibt mir davon netto?|Shundan soliqlardan keyin menga qancha qoladi?|
voraus|foˈʁaʊs|oldindan|Wir planen unsere Schichten einen Monat voraus.|Smenalarimizni bir oy oldindan rejalashtiramiz.|
inzwischen|ɪnˈtsvɪʃn̩|shu orada, endilikda|Inzwischen kann ich Kunden selbst beraten.|Endilikda mijozlarga o‘zim maslahat bera olaman.|
zunächst|tsuˈnɛːçst|avvalo, dastlab|Zunächst stellt sich das Team vor.|Dastlab jamoa o‘zini tanishtiradi.|
anschließend|ˈanʃliːsn̩t|undan keyin|Anschließend besichtigen wir die Werkstatt.|Undan keyin ustaxonani ko‘zdan kechiramiz.|
schließlich|ˈʃliːslɪç|nihoyat; axir|Nach drei Gesprächen bekam ich schließlich die Stelle.|Uchta suhbatdan keyin nihoyat ishga kirdim.|
'''))

BLOCKS.append((21, 'Gesundheit und medizinische Versorgung', r'''
die Krankenversicherung|ˈkʁaŋkn̩fɛɐ̯ˌzɪçəʁʊŋ|tibbiy sug‘urta|Meine Krankenversicherung schickt mir eine neue Karte.|Tibbiy sug‘urtam menga yangi karta yuboradi.|die Krankenversicherungen
der Eigenanteil|ˈaɪɡn̩ʔanˌtaɪl|o‘zi to‘laydigan ulush|Wie hoch ist mein Eigenanteil für diese Leistung?|Bu xizmat uchun o‘zim to‘laydigan ulush qancha?|die Eigenanteile
die Zuzahlung|ˈtsuːˌtsaːlʊŋ|qo‘shimcha to‘lov|Die Apothekerin erklärt mir die Zuzahlung.|Dorixonachi qo‘shimcha to‘lovni tushuntiradi.|die Zuzahlungen
einen Termin wahrnehmen|aɪnən tɛʁˈmiːn ˌvaːɐ̯neːmən|belgilangan uchrashuvga bora olmoq|Wegen der Reise kann ich den Arzttermin nicht wahrnehmen.|Safar sababli shifokor qabuliga bora olmayman.|nimmt wahr, nahm wahr, hat wahrgenommen
der Bereitschaftsdienst|bəˈʁaɪtʃaftsˌdiːnst|navbatchilik xizmati|Auf der Praxistür steht die Nummer des Bereitschaftsdienstes.|Qabulxona eshigida navbatchilik xizmati raqami yozilgan.|die Bereitschaftsdienste
der Befund|bəˈfʊnt|tekshiruv xulosasi|Den Befund bespricht die Ärztin morgen mit mir.|Tekshiruv xulosasini shifokor ertaga men bilan muhokama qiladi.|die Befunde
sich krankmelden|zɪç ˈkʁaŋkˌmɛldn̩|kasalligi haqida ishga xabar bermoq|Heute musste ich mich bei meinem Arbeitgeber krankmelden.|Bugun ish beruvchimga kasalligim haqida xabar berishga majbur bo‘ldim.|meldet sich krank, meldete sich krank, hat sich krankgemeldet
Blut abnehmen|ˈbluːt ˌapneːmən|qon namunasini olmoq|Für den Test nimmt die Pflegekraft etwas Blut ab.|Tahlil uchun hamshira biroz qon oladi.|nimmt Blut ab, nahm Blut ab, hat Blut abgenommen
die Sprechstundenhilfe|ˈʃpʁɛçʃtʊndn̩ˌhɪlfə|shifokor qabulxonasi yordamchisi|Die Sprechstundenhilfe gibt mir einen neuen Termin.|Qabulxona yordamchisi menga yangi vaqt belgilaydi.|die Sprechstundenhilfen
die Diagnose|diaˈɡnoːzə|tashxis|Die Diagnose bespricht der Arzt mit mir persönlich.|Shifokor tashxisni men bilan shaxsan muhokama qiladi.|die Diagnosen
das Symptom|zʏmpˈtoːm|alomat|Seit wann haben Sie diese Symptome?|Bu alomatlar sizda qachondan beri bor?|die Symptome
die Ursache|ˈuːɐ̯zaxə|sabab|Die Ursache der Schmerzen ist noch unklar.|Og‘riq sababi hali aniq emas.|die Ursachen
die Erkrankung|ɛɐ̯ˈkʁaŋkʊŋ|kasallik|Wegen einer Erkrankung fällt der Kurs aus.|Kasallik sababli dars bo‘lmaydi.|die Erkrankungen
die Entzündung|ɛntˈtsʏndʊŋ|yallig‘lanish|Die Ärztin untersucht die Entzündung am Ohr.|Shifokor quloqdagi yallig‘lanishni tekshirmoqda.|die Entzündungen
die Verletzung|fɛɐ̯ˈlɛtsʊŋ|jarohat|Nach der Verletzung musste er das Training unterbrechen.|Jarohatdan keyin u mashg‘ulotni to‘xtatishga majbur bo‘ldi.|die Verletzungen
die Wunde|ˈvʊndə|yara|Die Pflegekraft versorgt die Wunde vorsichtig.|Hamshira yaraga ehtiyotkorlik bilan ishlov beradi.|die Wunden
der Verband|fɛɐ̯ˈbant|bog‘lam|Der Verband darf heute nicht nass werden.|Bog‘lam bugun ho‘l bo‘lmasligi kerak.|die Verbände
die Narbe|ˈnaʁbə|chandiq|Die kleine Narbe erinnert mich an meinen Fahrradsturz.|Kichkina chandiq velosipeddan yiqilganimni eslatadi.|die Narben
die Allergie|alɛʁˈɡiː|allergiya|Bitte erwähnen Sie Ihre Allergie vor der Behandlung.|Iltimos, davolashdan oldin allergiyangiz haqida ayting.|die Allergien
die Nebenwirkung|ˈneːbn̩ˌvɪʁkʊŋ|nojo‘ya ta’sir|Über mögliche Nebenwirkungen frage ich die Apothekerin.|Mumkin bo‘lgan nojo‘ya ta’sirlar haqida dorixonachidan so‘rayman.|die Nebenwirkungen
die Dosierung|doˈziːʁʊŋ|dozalash, qabul miqdori|Die Dosierung steht auf dem Etikett.|Qabul qilish miqdori yorliqda yozilgan.|die Dosierungen
die Packungsbeilage|ˈpakʊŋsˌbaɪlaːɡə|dori yo‘riqnomasi|Die Packungsbeilage ist klein gedruckt.|Dori yo‘riqnomasi mayda harflarda bosilgan.|die Packungsbeilagen
die Einnahme|ˈaɪnˌnaːmə|dori qabul qilish|Die Apothekerin erklärt mir die Einnahme.|Dorixonachi menga dorini qanday qabul qilishni tushuntiradi.|bu ma’noda odatda birlikda
die Spritze|ˈʃpʁɪtsə|ukol, shprits|Vor der Spritze schaue ich lieber aus dem Fenster.|Ukoldan oldin derazadan qarab turganim ma’qul.|die Spritzen
die Impfung|ˈɪmpfʊŋ|emlash|Meinen Termin zur Impfung habe ich notiert.|Emlashga belgilangan vaqtni yozib qo‘ydim.|die Impfungen
die Vorsorge|ˈfoːɐ̯ˌzɔʁɡə|profilaktika, oldindan g‘amxo‘rlik|Bei der Vorsorge stellt die Ärztin viele Fragen.|Profilaktik ko‘rikda shifokor ko‘p savol beradi.|ko‘plik yo‘q
die Pflege|ˈpfleːɡə|parvarish|Nach der Operation braucht er tägliche Pflege.|Operatsiyadan keyin unga har kuni parvarish kerak.|ko‘plik yo‘q
die Pflegekraft|ˈpfleːɡəˌkʁaft|parvarish xodimi, hamshira|Die Pflegekraft zeigt mir den Weg zur Station.|Hamshira menga bo‘limga boradigan yo‘lni ko‘rsatadi.|die Pflegekräfte
der Angehörige|ˈanɡəˌhøːʁɪɡə|yaqin qarindosh|Ein Angehöriger begleitet den Patienten nach Hause.|Yaqin qarindosh bemorni uyiga kuzatadi.|die Angehörigen; ein Angehöriger
die Station|ʃtaˈtsi̯oːn|kasalxona bo‘limi|Auf dieser Station dürfen Angehörige bis acht bleiben.|Bu bo‘limda yaqinlar soat sakkizgacha qolishi mumkin.|die Stationen
die Aufnahme|ˈaʊfˌnaːmə|qabul qilish, ro‘yxatga olish|Bei der Aufnahme werden meine Daten geprüft.|Qabul qilishda ma’lumotlarim tekshiriladi.|die Aufnahmen
die Entlassung|ɛntˈlasʊŋ|kasalxonadan chiqarish; bo‘shatish|Vor der Entlassung bekomme ich einen Arztbrief.|Kasalxonadan chiqishdan oldin shifokor xulosasini olaman.|die Entlassungen
Erste Hilfe leisten|ˈeːɐ̯stə ˈhɪlfə ˌlaɪstn̩|birinchi yordam ko‘rsatmoq|Eine Passantin leistet Erste Hilfe.|Yo‘ldan o‘tayotgan ayol birinchi yordam ko‘rsatmoqda.|leistet Erste Hilfe, leistete Erste Hilfe, hat Erste Hilfe geleistet
die Notaufnahme|ˈnoːtʔaʊfˌnaːmə|shoshilinch yordam bo‘limi|In der Notaufnahme schildert er seine Beschwerden.|Shoshilinch yordam bo‘limida u shikoyatlarini aytadi.|die Notaufnahmen
der Rettungswagen|ˈʁɛtʊŋsˌvaːɡn̩|tez yordam mashinasi|Wir machen dem Rettungswagen sofort Platz.|Tez yordam mashinasiga darhol yo‘l beramiz.|die Rettungswagen
die Operation|opəʁaˈtsi̯oːn|operatsiya|Vor der Operation erklärt der Chirurg den Ablauf.|Operatsiyadan oldin jarroh jarayonni tushuntiradi.|die Operationen
der Eingriff|ˈaɪnɡʁɪf|tibbiy aralashuv, muolaja|Der Eingriff ist für Dienstag geplant.|Muolaja seshanbaga rejalashtirilgan.|die Eingriffe
die Therapie|teʁaˈpiː|davolash usuli, terapiya|Die Therapie findet zweimal pro Woche statt.|Terapiya haftada ikki marta bo‘ladi.|die Therapien
die Genesung|ɡəˈneːzʊŋ|sog‘ayish|Wir wünschen dir eine schnelle Genesung.|Senga tez sog‘ayishni tilaymiz.|ko‘plik yo‘q
die Krankschreibung|ˈkʁaŋkˌʃʁaɪbʊŋ|kasallik tufayli mehnatga layoqatsizlik hujjati|Die Krankschreibung gilt bis Donnerstag.|Kasallik varaqasi payshanbagacha amal qiladi.|die Krankschreibungen
die Ernährung|ɛɐ̯ˈnɛːʁʊŋ|ovqatlanish|Über meine Ernährung führe ich eine Woche lang Tagebuch.|Ovqatlanishim haqida bir hafta kundalik yuritaman.|ko‘plik yo‘q
die Bewegung|bəˈveːɡʊŋ|harakat|Nach langem Sitzen freue ich mich auf Bewegung.|Uzoq o‘tirgandan keyin harakat qilishdan xursand bo‘laman.|die Bewegungen
die Erholung|ɛɐ̯ˈhoːlʊŋ|dam olish, tiklanish|Am Wochenende brauche ich vor allem Erholung.|Dam olish kunlari menga eng avvalo hordiq kerak.|die Erholungen; odatda birlikda
unter Druck stehen|ʊntɐ ˈdʁʊk ˌʃteːən|bosim ostida bo‘lmoq|Vor dem Abgabetermin stehe ich unter Druck.|Topshirish muddati oldidan bosim ostida bo‘laman.|steht unter Druck, stand unter Druck, hat unter Druck gestanden
die Belastung|bəˈlastʊŋ|yuklama, zo‘riqish|Die doppelte Schicht war eine große Belastung.|Ikki smenada ishlash katta zo‘riqish bo‘ldi.|die Belastungen
die Sucht|zʊxt|qaramlik, ruju qo‘yish|Über Sucht sprechen wir ohne Vorwürfe.|Qaramlik haqida ayblovlarsiz gaplashamiz.|die Süchte
das Wohlbefinden|ˈvoːlbəˌfɪndn̩|o‘zini yaxshi his qilish|Ein ruhiger Spaziergang verbessert mein Wohlbefinden.|Tinch sayr o‘zimni yaxshiroq his qilishimga yordam beradi.|ko‘plik yo‘q
der Blutdruck|ˈbluːtˌdʁʊk|qon bosimi|Die Ärztin misst meinen Blutdruck.|Shifokor qon bosimimni o‘lchaydi.|odatda birlikda
der Kreislauf|ˈkʁaɪslaʊf|qon aylanishi|Bei Hitze macht mein Kreislauf manchmal Probleme.|Issiqda qon aylanishim ba’zan muammo tug‘diradi.|die Kreisläufe
die Flüssigkeit|ˈflʏsɪçkaɪt|suyuqlik|Wie viel Flüssigkeit passt in diese Flasche?|Bu idishga qancha suyuqlik sig‘adi?|die Flüssigkeiten
untersuchen|ʊntɐˈzuːxn̩|tekshirmoq, ko‘rikdan o‘tkazmoq|Die Ärztin untersucht mein Knie.|Shifokor tizzamni tekshiradi.|untersucht, untersuchte, hat untersucht
behandeln|bəˈhandl̩n|davolamoq; muomala qilmoq|In dieser Praxis werden auch Kinder behandelt.|Bu qabulxonada bolalar ham davolanadi.|behandelt, behandelte, hat behandelt
verschreiben|fɛɐ̯ˈʃʁaɪbn̩|retsept yozib bermoq|Der Arzt verschreibt mir eine Salbe.|Shifokor menga surtma yozib beradi.|verschreibt, verschrieb, hat verschrieben
einnehmen|ˈaɪnneːmən|dori ichmoq, qabul qilmoq|Wann soll ich das Medikament einnehmen?|Dorini qachon qabul qilishim kerak?|nimmt ein, nahm ein, hat eingenommen
vertragen|fɛɐ̯ˈtʁaːɡn̩|ko‘tara olmoq, mos tushmoq|Ich vertrage dieses Medikament nicht gut.|Bu dori menga yaxshi to‘g‘ri kelmaydi.|verträgt, vertrug, hat vertragen
leiden|ˈlaɪdn̩|azob chekmoq|Er leidet seit Jahren unter Rückenschmerzen.|U yillardan beri bel og‘rig‘idan aziyat chekadi.|leidet, litt, hat gelitten
wieder zu Kräften kommen|ˈviːdɐ tsuː ˈkʁɛftn̩ ˌkɔmən|yana kuchga kirmoq|Nach der Krankheit komme ich langsam wieder zu Kräften.|Kasallikdan keyin asta-sekin yana kuchga kiryapman.|kommt, kam, ist gekommen
heilen|ˈhaɪlən|bitmoq, sog‘aytirmoq|Die Wunde heilt langsam.|Yara asta-sekin bitmoqda.|heilt, heilte, ist geheilt (bitmoq); hat geheilt (davolamoq)
pflegen|ˈpfleːɡn̩|parvarish qilmoq|Er pflegt seinen Vater zu Hause.|U otasini uyda parvarish qiladi.|pflegt, pflegte, hat gepflegt
versorgen|fɛɐ̯ˈzɔʁɡn̩|ta’minlamoq, parvarish qilmoq|Die Ärztin versorgt die kleine Verletzung.|Shifokor kichik jarohatga ishlov beradi.|versorgt, versorgte, hat versorgt
messen|ˈmɛsn̩|o‘lchamoq|Ich messe meine Temperatur noch einmal.|Haroratimni yana bir marta o‘lchayman.|misst, maß, hat gemessen
abhören|ˈaphøːʁən|tibbiy asbob bilan eshitib tekshirmoq|Der Arzt hört meine Lunge ab.|Shifokor o‘pkamni eshitib tekshiradi.|hört ab, hörte ab, hat abgehört
schlucken|ˈʃlʊkn̩|yutmoq|Beim Schlucken tut mir der Hals weh.|Yutganda tomog‘im og‘riydi.|schluckt, schluckte, hat geschluckt
bluten|ˈbluːtn̩|qonamoq|Mein Finger blutet nach dem kleinen Schnitt.|Kichik kesikdan keyin barmog‘im qonayapti.|blutet, blutete, hat geblutet
anschwellen|ˈanˌʃvɛlən|shishmoq|Nach dem Sturz ist mein Knöchel angeschwollen.|Yiqilgandan keyin to‘pig‘im shishdi.|schwillt an, schwoll an, ist angeschwollen
sich anstecken|zɪç ˈanʃtɛkn̩|kasallik yuqtirmoq|Im Büro haben sich mehrere Kollegen angesteckt.|Ofisda bir nechta hamkasb kasallik yuqtirdi.|steckt sich an, steckte sich an, hat sich angesteckt
impfen|ˈɪmpfn̩|emlamoq|Die Ärztin impft heute in der Schule.|Shifokor bugun maktabda emlash o‘tkazadi.|impft, impfte, hat geimpft
operieren|opəˈʁiːʁən|operatsiya qilmoq|Das Team operiert meinen Onkel am Mittwoch.|Jamoa amakimni chorshanba kuni operatsiya qiladi.|operiert, operierte, hat operiert
aufnehmen|ˈaʊfneːmən|qabul qilmoq; yozib olmoq|Das Krankenhaus nimmt sie zur Beobachtung auf.|Kasalxona uni kuzatuv uchun qabul qiladi.|nimmt auf, nahm auf, hat aufgenommen
krankschreiben|ˈkʁaŋkˌʃʁaɪbn̩|kasallik varaqasi bermoq|Der Arzt schreibt mich bis Freitag krank.|Shifokor menga jumagacha kasallik varaqasi beradi.|schreibt krank, schrieb krank, hat krankgeschrieben
sich entspannen|zɪç ɛntˈʃpanən|bo‘shashmoq, hordiq chiqarmoq|Beim Zeichnen kann ich mich gut entspannen.|Rasm chizishda yaxshi hordiq chiqaraman.|entspannt sich, entspannte sich, hat sich entspannt
verzichten|fɛɐ̯ˈtsɪçtn̩|voz kechmoq|Heute verzichte ich auf den dritten Kaffee.|Bugun uchinchi qahvadan voz kechaman.|verzichtet, verzichtete, hat verzichtet
zunehmen|ˈtsuːneːmən|semirmoq; ko‘paymoq|Im Winter habe ich etwas zugenommen.|Qishda biroz vazn qo‘shdim.|nimmt zu, nahm zu, hat zugenommen
abnehmen|ˈapneːmən|ozmoq; kamaymoq|Seit dem Umzug hat mein Stress abgenommen.|Ko‘chganimdan beri stressim kamaydi.|nimmt ab, nahm ab, hat abgenommen
vorbeugen|ˈfoːɐ̯bɔʏɡn̩|oldini olmoq|Wie kann ich solchen Beschwerden vorbeugen?|Bunday bezovtaliklarning oldini qanday olsam bo‘ladi?|beugt vor, beugte vor, hat vorgebeugt
akut|aˈkuːt|o‘tkir, to‘satdan boshlangan|Wegen akuter Schmerzen rufe ich die Praxis an.|O‘tkir og‘riq sababli qabulxonaga qo‘ng‘iroq qilaman.|
chronisch|ˈkʁoːnɪʃ|surunkali|Er lebt seit Jahren mit einer chronischen Erkrankung.|U yillardan beri surunkali kasallik bilan yashaydi.|
ansteckend|ˈanʃtɛkn̩t|yuqumli|Die Ärztin erklärt, ob die Krankheit ansteckend ist.|Shifokor kasallik yuqumlimi, yo‘qmi, tushuntiradi.|
allergisch|aˈlɛʁɡɪʃ|allergiyasi bor, allergik|Auf Katzen reagiere ich allergisch.|Menda mushuklarga allergiya bor.|
schmerzhaft|ˈʃmɛʁtsˌhaft|og‘riqli|Das Auftreten mit dem rechten Fuß ist schmerzhaft.|O‘ng oyoqqa bosish og‘riqli.|
harmlos|ˈhaːɐ̯mloːs|zararsiz, xavfsiz|Laut Ärztin ist der kleine Fleck harmlos.|Shifokorning aytishicha, kichik dog‘ xavfsiz.|
ernsthaft|ˈɛʁnsthaft|jiddiy|Zum Glück wurde niemand ernsthaft verletzt.|Yaxshiyamki, hech kim jiddiy jarohatlanmadi.|
erschöpft|ɛɐ̯ˈʃœpft|holdan toygan|Nach der langen Schicht bin ich erschöpft.|Uzoq smenadan keyin holdan toyganman.|
schwindelig|ˈʃvɪndəlɪç|boshi aylanayotgan|Beim Aufstehen wird mir schwindelig.|Turganimda boshim aylanadi.|
übel|ˈyːbl̩|ko‘ngli aynigan; yomon|Im Bus wird mir manchmal übel.|Avtobusda ba’zan ko‘nglim ayniydi.|
bewusstlos|bəˈvʊstloːs|hushsiz|Der Patient war kurz bewusstlos.|Bemor qisqa vaqt hushsiz edi.|
übergewichtig|ˈyːbɐɡəˌvɪçtɪç|ortiqcha vaznli|Als Kind war ich übergewichtig.|Bolaligimda ortiqcha vaznli edim.|
ausgewogen|ˈaʊsɡəˌvoːɡn̩|muvozanatli|Unsere Kantine bietet ausgewogene Mahlzeiten an.|Oshxonamiz muvozanatli taomlar taklif qiladi.|
körperlich|ˈkœʁpɐlɪç|jismoniy|Meine Arbeit ist körperlich anstrengend.|Ishim jismonan mashaqqatli.|
seelisch|ˈzeːlɪʃ|ruhiy|Nach dem Unfall braucht sie auch seelische Unterstützung.|Avariyadan keyin unga ruhiy qo‘llab-quvvatlash ham kerak.|
vorbeugend|ˈfoːɐ̯bɔʏɡn̩t|oldini oluvchi, profilaktik|Die Ärztin erklärt mir vorbeugende Maßnahmen.|Shifokor menga profilaktik choralarni tushuntiradi.|
lebensgefährlich|ˈleːbn̩sɡəˌfɛːɐ̯lɪç|hayot uchun xavfli|Der Unfall war schwer, aber niemand wurde lebensgefährlich verletzt.|Avariya og‘ir edi, ammo hech kim hayoti xavf ostida qoladigan darajada jarohatlanmadi.|
vorübergehend|foˈʁyːbɐˌɡeːənt|vaqtincha|Die Praxis ist vorübergehend geschlossen.|Qabulxona vaqtincha yopiq.|
dauerhaft|ˈdaʊɐhaft|doimiy, uzoq muddatli|Wir suchen eine dauerhafte Lösung für die Pflege.|Parvarish uchun doimiy yechim izlayapmiz.|
ambulant|ambʊˈlant|yotib qolmasdan davolanadigan|Der Eingriff wird ambulant durchgeführt.|Muolaja kasalxonada yotib qolmasdan o‘tkaziladi.|
stationär|ʃtatsi̯oˈnɛːɐ̯|kasalxonada yotib davolanadigan|Mein Vater wird stationär behandelt.|Otam kasalxonada yotib davolanyapti.|
nüchtern|ˈnʏçtɐn|och qoringa; hushyor|Soll ich zur Untersuchung nüchtern kommen?|Tekshiruvga och qoringa kelishim kerakmi?|
empfindlich|ɛmˈpfɪntlɪç|sezgir|Meine Haut ist empfindlich gegen manche Seifen.|Terim ayrim sovunlarga sezgir.|
solange|zoˈlaŋə|...guncha, ...davomida|Solange ich krank bin, bleibe ich zu Hause.|Kasal ekanman, uyda qolaman.|
sobald|zoˈbalt|...ishi bilanoq|Sobald der Befund da ist, ruft die Praxis an.|Tekshiruv xulosasi kelishi bilanoq qabulxonadan qo‘ng‘iroq qilishadi.|
'''))

BLOCKS.append((22, 'Ehrenamt und gemeinsame Planung', r'''
das Ehrenamt|ˈeːʁənˌʔamt|ko‘ngilli jamoat ishi|Durch mein Ehrenamt habe ich neue Freunde gefunden.|Ko‘ngilli jamoat ishim orqali yangi do‘stlar topdim.|die Ehrenämter
einem Verein beitreten|aɪnəm fɛɐ̯ˈʔaɪn ˌbaɪtʁeːtn̩|uyushmaga a’zo bo‘lmoq|Ich bin dem Sportverein erst im Mai beigetreten.|Sport uyushmasiga faqat may oyida a’zo bo‘ldim.|tritt bei, trat bei, ist beigetreten
die Mitgliedschaft|ˈmɪtɡliːtʃaft|a’zolik|Für die Mitgliedschaft fülle ich ein kurzes Formular aus.|A’zolik uchun qisqa blankani to‘ldiraman.|die Mitgliedschaften
der Vorstand|ˈfoːɐ̯ʃtant|boshqaruv hay’ati|Der Vorstand trifft sich einmal im Monat.|Boshqaruv hay’ati oyiga bir marta yig‘iladi.|die Vorstände
die Spende|ˈʃpɛndə|xayriya, ehson|Mit Ihrer Spende kaufen wir neue Schulbücher.|Ehsoningizga yangi darsliklar sotib olamiz.|die Spenden
die Sammlung|ˈzamlʊŋ|yig‘ish; to‘plam|Bei der Sammlung kamen viele warme Jacken zusammen.|Yig‘im paytida ko‘plab issiq kurtkalar to‘plandi.|die Sammlungen
die Hilfsorganisation|ˈhɪlfsʔɔʁɡanizaˌtsi̯oːn|yordam tashkiloti|Die Hilfsorganisation sucht Fahrer für das Wochenende.|Yordam tashkiloti dam olish kunlari uchun haydovchilar izlayapti.|die Hilfsorganisationen
das Tierheim|ˈtiːɐ̯haɪm|hayvonlar boshpanasi|Im Tierheim gehe ich mit Hunden spazieren.|Hayvonlar boshpanasida itlarni sayrga olib chiqaman.|die Tierheime
das Seniorenheim|zeˈni̯oːʁənˌhaɪm|keksalar uyi|Im Seniorenheim veranstalten wir einen Spielenachmittag.|Keksalar uyida tushdan keyingi o‘yin tadbirini tashkil qilamiz.|die Seniorenheime
das Jugendzentrum|ˈjuːɡn̩tˌtsɛntʁʊm|yoshlar markazi|Das Jugendzentrum bekommt einen neuen Musikraum.|Yoshlar markazida yangi musiqa xonasi ochiladi.|die Jugendzentren
die Notunterkunft|ˈnoːtʔʊntɐˌkʊnft|favqulodda vaqtinchalik boshpana|Nach dem Brand wohnt die Familie in einer Notunterkunft.|Yong‘indan keyin oila vaqtinchalik boshpanada yashayapti.|die Notunterkünfte
die Betreuung|bəˈtʁɔʏʊŋ|qarov, g‘amxo‘rlik|Während des Kurses gibt es Betreuung für die Kinder.|Kurs paytida bolalarga qarab turiladi.|die Betreuungen
die Begleitung|bəˈɡlaɪtʊŋ|hamrohlik|Für den Arztbesuch wünscht sie sich eine Begleitung.|Shifokorga borishda u hamroh bo‘lishini istaydi.|die Begleitungen
Rat einholen|ˈʁaːt ˌaɪnhoːlən|maslahat olmoq|Vor dem Projekt holen wir bei erfahrenen Helfern Rat ein.|Loyihadan oldin tajribali yordamchilardan maslahat olamiz.|holt Rat ein, holte Rat ein, hat Rat eingeholt
die Begegnung|bəˈɡeːɡnʊŋ|uchrashuv|Die Begegnung mit den Nachbarn hat mir Mut gemacht.|Qo‘shnilar bilan uchrashuv menga dalda berdi.|die Begegnungen
die Teilnahme|ˈtaɪlˌnaːmə|qatnashish|Die Teilnahme ist auch ohne Mitgliedschaft möglich.|A’zo bo‘lmasdan ham qatnashish mumkin.|odatda birlikda
der Einsatz|ˈaɪnzats|faol xizmat, sa’y-harakat|Vielen Dank für euren Einsatz am Wochenende.|Dam olish kunlaridagi sa’y-harakatlaringiz uchun katta rahmat.|die Einsätze
die Nachbarschaftshilfe|ˈnaːxbaːɐ̯ʃaftsˌhɪlfə|qo‘shnichilik yordami|Die Nachbarschaftshilfe bringt älteren Menschen Einkäufe.|Qo‘shnichilik yordami keksalarga xaridlarini olib keladi.|ko‘plik yo‘q
der Begegnungsort|bəˈɡeːɡnʊŋsˌʔɔʁt|uchrashish joyi|Die Bibliothek ist auch ein Begegnungsort.|Kutubxona uchrashish joyi hamdir.|die Begegnungsorte
die Aktion|akˈtsi̯oːn|tashabbus, aksiya|Unsere Aktion beginnt mit einem gemeinsamen Frühstück.|Aksiyamiz birgalikdagi nonushta bilan boshlanadi.|die Aktionen
etwas auf die Beine stellen|ˈʔɛtvas aʊf diː ˈbaɪnə ˌʃtɛlən|biror ishni tashkil qilib yo‘lga qo‘ymoq|Zusammen stellen wir ein kleines Festival auf die Beine.|Birgalikda kichik festival tashkil qilamiz.|stellt, stellte, hat gestellt
das Ziel|tsiːl|maqsad|Unser Ziel ist ein Garten für alle.|Maqsadimiz — hamma uchun bog‘ yaratish.|die Ziele
die Planung|ˈplaːnʊŋ|rejalashtirish|Bei der Planung haben wir die Buszeiten vergessen.|Rejalashtirishda avtobus vaqtlarini unutibmiz.|die Planungen
der Ablauf|ˈaplaʊf|jarayon tartibi|Den genauen Ablauf besprechen wir morgen.|Aniq o‘tkazish tartibini ertaga muhokama qilamiz.|die Abläufe
der Zeitplan|ˈtsaɪtplaːn|vaqt jadvali|Unser Zeitplan enthält auch längere Pausen.|Vaqt jadvalimizda uzoqroq tanaffuslar ham bor.|die Zeitpläne
Vorbereitungen treffen|ˈfoːɐ̯bəʁaɪtʊŋən ˌtʁɛfn̩|tayyorgarlik ko‘rmoq|Schon am Freitag treffen wir die letzten Vorbereitungen.|Jumadayoq oxirgi tayyorgarliklarni ko‘ramiz.|trifft Vorbereitungen, traf Vorbereitungen, hat Vorbereitungen getroffen
die Durchführung|ˈdʊʁçˌfyːʁʊŋ|amalga oshirish, o‘tkazish|Für die Durchführung brauchen wir zehn Helfer.|O‘tkazish uchun o‘nta yordamchi kerak.|die Durchführungen
die Nachbereitung|ˈnaːxbəˌʁaɪtʊŋ|yakundan keyingi tahlil|Bei der Nachbereitung sammeln wir Ideen fürs nächste Mal.|Yakuniy tahlilda keyingi safar uchun g‘oyalar yig‘amiz.|die Nachbereitungen
sich zurückmelden|zɪç tsuˈʁʏkˌmɛldn̩|qayta xabar bermoq|Bitte meldet euch bis morgen zurück.|Iltimos, ertagacha javob xabarini beringlar.|meldet sich zurück, meldete sich zurück, hat sich zurückgemeldet
das Budget|byˈdʒeː|budjet|Unser Budget reicht für Getränke und Brot.|Budjetimiz ichimliklar va nonga yetadi.|die Budgets
die Kosten|ˈkɔstn̩|xarajatlar|Die Kosten teilen wir unter allen Teilnehmern auf.|Xarajatlarni barcha qatnashchilar o‘rtasida bo‘lamiz.|faqat ko‘plik
die Finanzierung|finanˈtsiːʁʊŋ|moliyalashtirish|Die Finanzierung des Projekts ist noch offen.|Loyihani moliyalashtirish masalasi hali ochiq.|die Finanzierungen
das Material|matəˈʁi̯aːl|material|Das Material für die Plakate liegt im Schrank.|Plakatlar uchun material shkafda turibdi.|die Materialien
die Ausstattung|ˈaʊsˌʃtatʊŋ|jihozlar, jihozlanish|Die technische Ausstattung prüfen wir vorher.|Texnik jihozlarni oldindan tekshiramiz.|die Ausstattungen
die Ausrüstung|ˈaʊsˌʁʏstʊŋ|anjomlar|Für die Wanderung fehlt uns noch etwas Ausrüstung.|Piyoda sayohat uchun bizga hali ayrim anjomlar yetishmayapti.|die Ausrüstungen
mit anpacken|mɪt ˈanpakn̩|ishga qo‘shilib yordam bermoq|Beim Aufräumen packen alle mit an.|Yig‘ishtirishda hamma birga yordam beradi.|packt mit an, packte mit an, hat mit angepackt
der Raum|ʁaʊm|xona; joy|Für den Workshop brauchen wir einen hellen Raum.|Amaliy mashg‘ulot uchun yorug‘ xona kerak.|die Räume
die Lautsprecheranlage|ˈlaʊtʃpʁɛçɐʔanˌlaːɡə|ovoz kuchaytirish tizimi|Vor dem Fest testen wir die Lautsprecheranlage.|Bayramdan oldin ovoz kuchaytirish tizimini tekshiramiz.|die Lautsprecheranlagen
der Stand|ʃtant|rasta, stend|An unserem Stand gibt es selbst gemachte Marmelade.|Rastamizda uyda tayyorlangan murabbo bor.|die Stände
das Plakat|plaˈkaːt|plakat|Auf dem Plakat fehlt noch die Uhrzeit.|Plakatda hali vaqt ko‘rsatilmagan.|die Plakate
jemanden willkommen heißen|ˈjeːmandn̩ vɪlˈkɔmən ˌhaɪsn̩|kimnidir xush kelibsiz deb kutib olmoq|Am Eingang heißen wir die Gäste willkommen.|Kirishda mehmonlarni xush kelibsiz deb kutib olamiz.|heißt willkommen, hieß willkommen, hat willkommen geheißen
sich in eine Liste eintragen|zɪç ɪn aɪnə ˈlɪstə ˌaɪntʁaːɡn̩|ro‘yxatga o‘zini yozmoq|Wer helfen möchte, trägt sich in die Liste ein.|Yordam bermoqchi bo‘lgan kishi o‘zini ro‘yxatga yozadi.|trägt sich ein, trug sich ein, hat sich eingetragen
die Warteliste|ˈvaʁtəˌlɪstə|kutish ro‘yxati|Zwei Personen stehen noch auf der Warteliste.|Yana ikki kishi kutish ro‘yxatida turibdi.|die Wartelisten
die Absprache|ˈapˌʃpʁaːxə|kelishuv|Nach Absprache kannst du früher gehen.|Kelishuvga ko‘ra, ertaroq ketishing mumkin.|die Absprachen
jemanden ablösen|ˈjeːmandn̩ ˌapløːzn̩|navbatchilikda birovni almashtirmoq|Um drei löse ich dich am Getränkestand ab.|Soat uchda ichimlik rastasida seni almashtiraman.|löst ab, löste ab, hat abgelöst
die Reserve|ʁeˈzɛʁvə|zaxira|Als Reserve halten wir zehn Stühle bereit.|Zaxira sifatida o‘nta stulni tayyor tutamiz.|die Reserven
die Alternative|altɛʁnaˈtiːvə|muqobil yo‘l|Bei schlechtem Wetter brauchen wir eine Alternative.|Yomon ob-havoda bizga muqobil variant kerak.|die Alternativen
die Priorität|pʁi̯oʁiˈtɛːt|ustuvorlik|Die Sicherheit der Kinder hat Priorität.|Bolalar xavfsizligi ustuvor o‘rinda.|die Prioritäten
das Hindernis|ˈhɪndɐnɪs|to‘siq|Die steile Treppe ist für Rollstühle ein Hindernis.|Tik zina nogironlar aravachalari uchun to‘siq.|die Hindernisse
die Gelegenheit|ɡəˈleːɡn̩haɪt|imkoniyat, qulay fursat|Das Fest bietet eine gute Gelegenheit zum Kennenlernen.|Bayram tanishish uchun yaxshi imkoniyat beradi.|die Gelegenheiten
spenden|ˈʃpɛndn̩|ehson qilmoq|Die Bäckerei spendet Brot für unser Frühstück.|Nonvoyxona nonushtamiz uchun non ehson qiladi.|spendet, spendete, hat gespendet
die Sammelstelle|ˈzaml̩ˌʃtɛlə|yig‘ish punkti|Die Sammelstelle für Kleidung ist im Gemeindehaus.|Kiyim yig‘ish punkti jamoat binosida.|die Sammelstellen
betreuen|bəˈtʁɔʏən|qaramoq, g‘amxo‘rlik qilmoq|Zwei Helfer betreuen die Kinder beim Basteln.|Qo‘l mehnati paytida ikki yordamchi bolalarga qaraydi.|betreut, betreute, hat betreut
jemandem Gesellschaft leisten|ˈjeːmandəm ɡəˈzɛlʃaft ˌlaɪstn̩|kimningdir yonida bo‘lib suhbatlashmoq|Einmal pro Woche leiste ich meinem Nachbarn Gesellschaft.|Haftada bir marta qo‘shnimning yonida bo‘lib suhbatlashaman.|leistet Gesellschaft, leistete Gesellschaft, hat Gesellschaft geleistet
ein offenes Ohr haben|aɪn ˈɔfnəs ˈʔoːɐ̯ ˌhaːbn̩|tinglashga tayyor bo‘lmoq|Unsere Gruppenleiterin hat immer ein offenes Ohr.|Guruh rahbarimiz doim tinglashga tayyor.|hat ein offenes Ohr, hatte ein offenes Ohr, hat ein offenes Ohr gehabt
ermutigen|ɛɐ̯ˈmuːtɪɡn̩|ruhlantirmoq|Die Kursleiterin ermutigt uns, selbst zu sprechen.|Kurs rahbari bizni mustaqil gapirishga ruhlantiradi.|ermutigt, ermutigte, hat ermutigt
mitwirken|ˈmɪtvɪʁkn̩|hissa qo‘shib qatnashmoq|Bei unserem Theaterstück wirken auch Eltern mit.|Teatr sahnamizda ota-onalar ham qatnashadi.|wirkt mit, wirkte mit, hat mitgewirkt
beitragen|ˈbaɪtʁaːɡn̩|hissa qo‘shmoq|Jeder kann etwas zum gemeinsamen Essen beitragen.|Har kim umumiy taomga biror narsa bilan hissa qo‘sha oladi.|trägt bei, trug bei, hat beigetragen
vorbereiten|ˈfoːɐ̯bəˌʁaɪtn̩|tayyorlamoq|Am Freitag bereiten wir den Saal vor.|Juma kuni zalni tayyorlaymiz.|bereitet vor, bereitete vor, hat vorbereitet
durchführen|ˈdʊʁçfyːʁən|o‘tkazmoq, amalga oshirmoq|Wir führen die Aktion auch bei leichtem Regen durch.|Aksiyani yengil yomg‘irda ham o‘tkazamiz.|führt durch, führte durch, hat durchgeführt
auswerten|ˈaʊsveːɐ̯tn̩|natijalarni tahlil qilmoq|Nach dem Fest werten wir die Fragebögen aus.|Bayramdan keyin so‘rovnomalarni tahlil qilamiz.|wertet aus, wertete aus, hat ausgewertet
aufteilen|ˈaʊftaɪlən|taqsimlamoq|Wir teilen die Arbeit gerecht auf.|Ishni adolatli taqsimlaymiz.|teilt auf, teilte auf, hat aufgeteilt
die Aufgabenverteilung|ˈaʊfɡaːbn̩fɛɐ̯ˌtaɪlʊŋ|vazifalar taqsimoti|Die Aufgabenverteilung hängt an der Tür.|Vazifalar taqsimoti eshikda osilgan.|die Aufgabenverteilungen
einplanen|ˈaɪnplaːnən|rejaga kiritmoq|Für den Aufbau planen wir eine Stunde ein.|O‘rnatish uchun rejada bir soat ajratamiz.|plant ein, plante ein, hat eingeplant
festlegen|ˈfɛstleːɡn̩|belgilab qo‘ymoq|Heute legen wir das Datum endgültig fest.|Bugun sanani uzil-kesil belgilaymiz.|legt fest, legte fest, hat festgelegt
absprechen|ˈapʃpʁɛçn̩|kelishib olmoq|Die Details sprechen wir mit der Schule ab.|Tafsilotlarni maktab bilan kelishib olamiz.|spricht ab, sprach ab, hat abgesprochen
sich abstimmen mit|zɪç ˈapʃtɪmən mɪt|...bilan ishni kelishmoq|Vor der Buchung stimmen wir uns mit dem Verein ab.|Band qilishdan oldin uyushma bilan kelishib olamiz.|stimmt sich ab, stimmte sich ab, hat sich abgestimmt; mit + Dativ
ausrichten|ˈaʊsʁɪçtn̩|tadbir uyushtirmoq; xabar yetkazmoq|Dieses Jahr richten wir das Sommerfest aus.|Bu yil yozgi bayramni biz uyushtiramiz.|richtet aus, richtete aus, hat ausgerichtet
besorgen|bəˈzɔʁɡn̩|topib olib kelmoq|Kannst du noch Klebeband besorgen?|Yana yopishqoq lenta topib kela olasanmi?|besorgt, besorgte, hat besorgt
aufbauen|ˈaʊfbaʊən|o‘rnatmoq, qurmoq|Wir bauen die Tische im Schatten auf.|Stollarni soyaga o‘rnatamiz.|baut auf, baute auf, hat aufgebaut
abbauen|ˈapbaʊən|yig‘ishtirib yechmoq|Nach dem Konzert bauen wir die Bühne ab.|Konsertdan keyin sahnani yechib yig‘ishtiramiz.|baut ab, baute ab, hat abgebaut
verteilen|fɛɐ̯ˈtaɪlən|tarqatmoq|Die Kinder verteilen Einladungen in der Nachbarschaft.|Bolalar mahallada taklifnomalar tarqatadi.|verteilt, verteilte, hat verteilt
einspringen|ˈaɪnʃpʁɪŋən|birovning o‘rniga ishga chiqmoq|Wenn du krank wirst, springe ich ein.|Kasal bo‘lib qolsang, o‘rningga men chiqaman.|springt ein, sprang ein, ist eingesprungen
verschönern|fɛɐ̯ˈʃøːnɐn|chiroyli qilmoq|Mit Blumen verschönern wir den Innenhof.|Gullar bilan ichki hovlini chiroyli qilamiz.|verschönert, verschönerte, hat verschönert
sich lohnen|zɪç ˈloːnən|arzigulik bo‘lmoq|Die Mühe hat sich wirklich gelohnt.|Qilgan mehnatimiz haqiqatan ham arzigulik bo‘ldi.|lohnt sich, lohnte sich, hat sich gelohnt
ehrenamtlich|ˈeːʁənˌʔamtlɪç|ko‘ngilli ravishda, haq olmasdan|Sie arbeitet ehrenamtlich in der Bibliothek.|U kutubxonada ko‘ngilli bo‘lib ishlaydi.|
gemeinnützig|ɡəˈmaɪnˌnʏtsɪç|jamoat manfaatiga xizmat qiluvchi|Unser gemeinnütziger Verein bietet Sprachhilfe an.|Jamoat manfaatiga xizmat qiladigan uyushmamiz til bo‘yicha yordam taklif qiladi.|
entgegenkommend|ɛntˈɡeːɡn̩ˌkɔmənt|yon berishga tayyor, iltifotli|Die Vermieterin des Saals war sehr entgegenkommend.|Zalni ijaraga beruvchi ayol juda iltifotli bo‘ldi.|
einfühlsam|ˈaɪnfyːlzaːm|boshqalarning hislarini tushunadigan|Mit traurigen Kindern spricht sie besonders einfühlsam.|Xafa bolalar bilan u ayniqsa mehr va tushunish bilan gaplashadi.|
aktiv|akˈtiːf|faol|Auch nach der Rente bleibt er im Verein aktiv.|Pensiyadan keyin ham u uyushmada faol.|
in Verbindung bleiben|ɪn fɛɐ̯ˈbɪndʊŋ ˌblaɪbn̩|aloqada bo‘lib turmoq|Auch nach dem Projekt bleiben wir in Verbindung.|Loyihadan keyin ham aloqada bo‘lib turamiz.|bleibt in Verbindung, blieb in Verbindung, ist in Verbindung geblieben
barrierefrei|baˈʁi̯eːʁəˌfʁaɪ|to‘siqlarsiz, hamma uchun qulay|Der Eingang ist barrierefrei und breit genug.|Kirish joyi to‘siqlarsiz va yetarlicha keng.|
übersichtlich|ˈyːbɐˌzɪçtlɪç|tushunarli tuzilgan, ko‘rib chiqish oson|Der neue Zeitplan ist viel übersichtlicher.|Yangi vaqt jadvali ancha tushunarli tuzilgan.|
realistisch|ʁeˈalɪstɪʃ|haqiqatga mos, amalga oshadigan|Mit fünf Helfern ist dieser Plan realistisch.|Besh yordamchi bilan bu rejani amalga oshirish mumkin.|
machbar|ˈmaxbaːɐ̯|bajarish mumkin bo‘lgan|Bis Freitag ist die Reparatur machbar.|Ta’mirlashni jumagacha bajarish mumkin.|
aufwendig|ˈaʊfˌvɛndɪç|ko‘p mehnat yoki xarajat talab qiladigan|Die Dekoration war aufwendig, aber wunderschön.|Bezak ko‘p mehnat talab qildi, ammo juda chiroyli chiqdi.|
knifflig|ˈknɪflɪç|biroz murakkab, bosh qotiradigan|Der Aufbau des Zeltes ist ziemlich knifflig.|Chodirni o‘rnatish ancha bosh qotiradigan ish.|
kurzfristig|ˈkʊʁtsˌfʁɪstɪç|qisqa muddat ichida, kutilmaganda|Zwei Helfer haben kurzfristig abgesagt.|Ikki yordamchi oxirgi paytda qatnasha olmasligini aytdi.|
voraussichtlich|foˈʁaʊsˌzɪçtlɪç|taxminan, kutilishicha|Voraussichtlich kommen ungefähr vierzig Gäste.|Taxminan qirqta mehmon kelishi kutilmoqda.|
notfalls|ˈnoːtfals|zarurat bo‘lsa|Notfalls bringen wir unsere eigenen Stühle mit.|Zarurat bo‘lsa, o‘z stullarimizni olib kelamiz.|
vorsichtshalber|ˈfoːɐ̯zɪçtsˌhalbɐ|ehtiyot shart|Vorsichtshalber nehmen wir einen zweiten Schlüssel mit.|Ehtiyot shart ikkinchi kalitni olib ketamiz.|
recht|ʁɛçt|ancha, durustgina|Der Saal ist recht groß.|Zal ancha katta.|
übrig|ˈyːbʁɪç|ortib qolgan|Nach dem Fest ist noch viel Brot übrig.|Bayramdan keyin hali ko‘p non ortib qoldi.|
zusätzlich|ˈtsuːˌzɛtslɪç|qo‘shimcha|Wir brauchen zusätzlich zwei große Töpfe.|Bizga qo‘shimcha ikkita katta qozon kerak.|
gegenseitig|ˈɡeːɡn̩ˌzaɪtɪç|o‘zaro, bir-biriga|Wir helfen uns gegenseitig beim Tragen.|Ko‘tarishda bir-birimizga yordam beramiz.|
vorab|foˈʁap|oldindan|Die wichtigsten Informationen schicken wir vorab.|Eng muhim ma’lumotlarni oldindan yuboramiz.|
nachher|ˈnaːxheːɐ̯|keyin|Nachher räumen wir gemeinsam auf.|Keyin birgalikda yig‘ishtiramiz.|
währenddessen|vɛːʁəntˈdɛsn̩|shu paytda|Ich koche Tee; währenddessen deckt Ali den Tisch.|Men choy damlayman; shu paytda Ali dasturxon yozadi.|
falls|fals|agar, mabodo|Falls es regnet, feiern wir im Saal.|Agar yomg‘ir yog‘sa, zalda bayram qilamiz.|
damit|daˈmɪt|...ishi uchun|Wir sprechen langsam, damit alle uns verstehen.|Hamma tushunishi uchun sekin gapiramiz.|
'''))

BLOCKS.append((23, 'Meinungen und Argumente', r'''
Stellung nehmen zu|ˈʃtɛlʊŋ ˌneːmən tsuː|...haqida o‘z munosabatini bildirmoq|Zum Vorschlag möchte ich kurz Stellung nehmen.|Taklif haqida qisqacha munosabatimni bildirmoqchiman.|nimmt Stellung, nahm Stellung, hat Stellung genommen; zu + Dativ
die Ansicht|ˈanˌzɪçt|qarash, fikr|Meiner Ansicht nach fehlt hier ein Spielplatz.|Mening fikrimcha, bu yerda bolalar maydonchasi yetishmaydi.|die Ansichten
der Standpunkt|ˈʃtantˌpʊŋkt|nuqtayi nazar|Kannst du deinen Standpunkt genauer erklären?|Nuqtayi nazaringni aniqroq tushuntira olasanmi?|die Standpunkte
das Argument|aʁɡuˈmɛnt|dalil, asos|Für deinen Vorschlag spricht ein starkes Argument.|Taklifingni qo‘llab-quvvatlaydigan kuchli dalil bor.|die Argumente
die Begründung|bəˈɡʁʏndʊŋ|asoslash, sababini tushuntirish|Ohne Begründung überzeugt mich diese Entscheidung nicht.|Sababi tushuntirilmasa, bu qaror meni ishontirmaydi.|die Begründungen
der Beweis|bəˈvaɪs|isbot|Ein einzelnes Foto ist noch kein Beweis.|Bitta suratning o‘zi hali isbot emas.|die Beweise
ein Beispiel anführen|aɪn ˈbaɪʃpiːl ˌanfyːʁən|misol keltirmoq|Dazu möchte ich ein Beispiel aus meinem Alltag anführen.|Bunga kundalik hayotimdan bir misol keltirmoqchiman.|führt an, führte an, hat angeführt
die Tatsache|ˈtaːtˌzaxə|fakt, haqiqat|Wir sollten Meinungen und Tatsachen unterscheiden.|Fikrlar bilan faktlarni farqlashimiz kerak.|die Tatsachen
die Vermutung|fɛɐ̯ˈmuːtʊŋ|taxmin|Meine Vermutung hat sich später bestätigt.|Taxminim keyinchalik tasdiqlandi.|die Vermutungen
der Zweifel|ˈtsvaɪfl̩|shubha|An dieser Erklärung habe ich Zweifel.|Bu tushuntirishga shubham bor.|die Zweifel
die Überzeugung|yːbɐˈtsɔʏɡʊŋ|ishonch, qat’iy qarash|Sie spricht mit großer Überzeugung über Bildung.|U ta’lim haqida katta ishonch bilan gapiradi.|die Überzeugungen
die Zustimmung|ˈtsuːˌʃtɪmʊŋ|rozilik, ma’qullash|Dein Vorschlag findet im Team viel Zustimmung.|Taklifingni jamoada ko‘pchilik ma’qullayapti.|odatda birlikda
die Ablehnung|ˈapˌleːnʊŋ|rad etish|Die Ablehnung meines Antrags war enttäuschend.|Arizamning rad etilishi ko‘nglimni cho‘ktirdi.|die Ablehnungen
der Einwand|ˈaɪnvant|e’tiroz|Gegen den Termin habe ich einen Einwand.|Belgilangan vaqtga bitta e’tirozim bor.|die Einwände
die Kritik|kʁiˈtiːk|tanqid|Sachliche Kritik hilft mir beim Lernen.|Xolis tanqid o‘rganishimga yordam beradi.|die Kritiken
das Lob|loːp|maqtov|Über das Lob meiner Lehrerin habe ich mich gefreut.|O‘qituvchimning maqtovidan xursand bo‘ldim.|odatda birlikda
die Diskussion|dɪskʊˈsi̯oːn|muhokama|Die Diskussion dauert länger als geplant.|Muhokama rejalashtirilganidan uzoqroq davom etyapti.|die Diskussionen
die Debatte|deˈbatə|bahs-munozara|In der Debatte geht es um günstigen Wohnraum.|Bahs-munozara arzon turar joy haqida ketyapti.|die Debatten
das Thema|ˈteːma|mavzu|Beim Thema Verkehr haben alle etwas zu sagen.|Transport mavzusida hammaning aytadigan gapi bor.|die Themen
der Zusammenhang|tsuˈzamənhaŋ|bog‘liqlik|Zwischen Schlaf und Konzentration besteht ein Zusammenhang.|Uyqu bilan diqqatni jamlash o‘rtasida bog‘liqlik bor.|die Zusammenhänge
der Unterschied|ˈʊntɐʃiːt|farq|Der Unterschied liegt vor allem im Preis.|Farq asosan narxda.|die Unterschiede
die Gemeinsamkeit|ɡəˈmaɪnzaːmkaɪt|umumiy jihat|Trotz unserer Unterschiede haben wir viele Gemeinsamkeiten.|Farqlarimizga qaramay, umumiy jihatlarimiz ko‘p.|die Gemeinsamkeiten
der Vorteil|ˈfoːɐ̯taɪl|afzallik|Ein Vorteil des Fahrrads ist die einfache Parkplatzsuche.|Velosipedning bir afzalligi — qo‘yish uchun joy topish osonligi.|die Vorteile
der Nachteil|ˈnaːxtaɪl|kamchilik, salbiy tomon|Der lange Arbeitsweg ist ein Nachteil.|Ishga boradigan yo‘lning uzoqligi bir kamchilik.|die Nachteile
sich auswirken auf|zɪç ˈaʊsvɪʁkn̩ aʊf|...ga ta’sir ko‘rsatmoq|Lange Arbeitswege wirken sich auf die Freizeit aus.|Ishga uzoq qatnash bo‘sh vaqtga ta’sir qiladi.|wirkt sich aus, wirkte sich aus, hat sich ausgewirkt; auf + Akkusativ
die Wirkung|ˈvɪʁkʊŋ|ta’sir|Seine ruhige Stimme hat eine beruhigende Wirkung.|Uning sokin ovozi tinchlantiruvchi ta’sirga ega.|die Wirkungen
der Einfluss|ˈaɪnflʊs|ta’sir, ta’sir kuchi|Werbung hat Einfluss auf unsere Entscheidungen.|Reklama qarorlarimizga ta’sir qiladi.|die Einflüsse
die Bedeutung|bəˈdɔʏtʊŋ|ma’no; ahamiyat|Dieses Treffen hat für mich große Bedeutung.|Bu uchrashuv men uchun katta ahamiyatga ega.|die Bedeutungen
der Zweck|tsvɛk|maqsad, vazifa|Welchen Zweck hat diese Regel?|Bu qoidadan maqsad nima?|die Zwecke
die Absicht|ˈapˌzɪçt|niyat|Es war nicht meine Absicht, dich zu unterbrechen.|Sening gapingni bo‘lish niyatim yo‘q edi.|die Absichten
der Grund|ɡʁʊnt|sabab, asos|Für meine Entscheidung gibt es einen einfachen Grund.|Qarorimning oddiy bir sababi bor.|die Gründe
anders gesagt|ˈandɐs ɡəˈzaːkt|boshqacha aytganda|Wir brauchen mehr Zeit, anders gesagt: Der Termin ist zu früh.|Bizga ko‘proq vaqt kerak, boshqacha aytganda, belgilangan muddat juda erta.|
die Behauptung|bəˈhaʊptʊŋ|da’vo|Für diese Behauptung fehlen noch Zahlen.|Bu da’voni tasdiqlash uchun hali raqamlar yetishmayapti.|die Behauptungen
die Haltung|ˈhaltʊŋ|munosabat, pozitsiya|Seine Haltung zum Thema hat sich geändert.|Uning bu mavzuga munosabati o‘zgardi.|die Haltungen
die Perspektive|pɛʁspɛkˈtiːvə|nuqtayi nazar, istiqbol|Versuch, die Situation aus ihrer Perspektive zu sehen.|Vaziyatga uning nuqtayi nazaridan qarashga harakat qil.|die Perspektiven
die Erfahrungssache|ɛɐ̯ˈfaːʁʊŋsˌzaxə|tajribaga bog‘liq narsa|Gute Zeiteinteilung ist auch eine Erfahrungssache.|Vaqtni yaxshi taqsimlash tajribaga ham bog‘liq.|die Erfahrungssachen; odatda birlikda
aneinander vorbeireden|anʔaɪˈnandɐ foːɐ̯ˈbaɪˌʁeːdn̩|bir-birining gapini tushunmay gaplashmoq|Ich glaube, wir reden gerade aneinander vorbei.|Menimcha, hozir bir-birimizning gapimizni tushunmayapmiz.|redet aneinander vorbei, redete aneinander vorbei, hat aneinander vorbeigeredet
die Sicht|zɪçt|qarash; ko‘rish|Aus meiner Sicht ist der Plan zu teuer.|Mening nazarimda, reja juda qimmatga tushadi.|bu ma’noda odatda birlikda
Grenzen setzen|ˈɡʁɛntsn̩ ˌzɛtsn̩|chegara qo‘ymoq|Auch bei freiwilliger Hilfe muss man Grenzen setzen.|Ixtiyoriy yordamda ham chegara qo‘yish kerak.|setzt Grenzen, setzte Grenzen, hat Grenzen gesetzt
der Wert|veːɐ̯t|qadriyat; qiymat|Ehrlichkeit ist für mich ein wichtiger Wert.|Halollik men uchun muhim qadriyat.|die Werte
sich verlassen auf|zɪç fɛɐ̯ˈlasn̩ aʊf|...ga ishonib suyanmoq|Auf ihre Zusage kann ich mich verlassen.|Uning bergan roziligiga ishona olaman.|verlässt sich, verließ sich, hat sich verlassen; auf + Akkusativ
zuversichtlich|ˈtsuːfɛɐ̯ˌzɪçtlɪç|yaxshilikka ishonadigan, umidvor|Trotz der Schwierigkeiten bleiben wir zuversichtlich.|Qiyinchiliklarga qaramay, umidvormiz.|
Bedenken äußern|bəˈdɛŋkn̩ ˌʔɔʏsɐn|xavotir yoki e’tirozini bildirmoq|Einige Eltern äußern Bedenken wegen des langen Weges.|Ba’zi ota-onalar yo‘lning uzoqligi haqida xavotir bildirmoqda.|äußert Bedenken, äußerte Bedenken, hat Bedenken geäußert
bedauerlich|bəˈdaʊɐlɪç|afsuslanarli|Es ist bedauerlich, dass die Beratung geschlossen wird.|Maslahat bo‘limining yopilishi afsuslanarli.|
die Begeisterung|bəˈɡaɪstəʁʊŋ|ishtiyoq, zavq|Ihre Begeisterung für das Projekt steckt uns an.|Uning loyihaga ishtiyoqi bizga ham yuqadi.|odatda birlikda
sich Zeit lassen|zɪç ˈtsaɪt ˌlasn̩|shoshmasdan vaqt ajratmoq|Bei wichtigen Entscheidungen lasse ich mir Zeit.|Muhim qarorlarda shoshmayman.|lässt sich Zeit, ließ sich Zeit, hat sich Zeit gelassen
sich trauen|zɪç ˈtʁaʊən|jur’at etmoq|Inzwischen traue ich mich, vor der Gruppe zu sprechen.|Endi guruh oldida gapirishga jur’at eta olaman.|traut sich, traute sich, hat sich getraut
die Ehrlichkeit|ˈeːɐ̯lɪçkaɪt|halollik, rostgo‘ylik|Deine Ehrlichkeit schätze ich sehr.|Rostgo‘yligingni juda qadrlayman.|ko‘plik yo‘q
die Fairness|ˈfɛːɐ̯nɛs|adolatli munosabat|Fairness ist wichtiger als ein schneller Sieg.|Adolatli o‘yin tez g‘alabadan muhimroq.|ko‘plik yo‘q
einen Ausweg finden|aɪnən ˈaʊsveːk ˌfɪndn̩|chiqish yo‘lini topmoq|Gemeinsam finden wir sicher einen Ausweg.|Birgalikda albatta chiqish yo‘lini topamiz.|findet einen Ausweg, fand einen Ausweg, hat einen Ausweg gefunden
derselben Meinung sein|deːɐ̯ˈzɛlbn̩ ˈmaɪnʊŋ zaɪn|bir xil fikrda bo‘lmoq|In dieser Frage sind wir derselben Meinung.|Bu masalada bir xil fikrdamiz.|ist derselben Meinung, war derselben Meinung, ist derselben Meinung gewesen
anderer Meinung sein|ˈandəʁɐ ˈmaɪnʊŋ zaɪn|boshqa fikrda bo‘lmoq|Ich verstehe dich, bin aber anderer Meinung.|Seni tushunaman, ammo fikrim boshqacha.|ist anderer Meinung, war anderer Meinung, ist anderer Meinung gewesen
für etwas sprechen|fyːɐ̯ ˈʔɛtvas ˌʃpʁɛçn̩|biror narsaning foydasiga dalil bo‘lmoq|Für den Zug sprechen der Komfort und die kurze Fahrzeit.|Poyezd foydasiga qulaylik va yo‘lning qisqaligi dalil bo‘ladi.|spricht dafür, sprach dafür, hat dafür gesprochen
überzeugen|yːbɐˈtsɔʏɡn̩|ishontirmoq|Dein persönliches Beispiel hat mich überzeugt.|Shaxsiy misoling meni ishontirdi.|überzeugt, überzeugte, hat überzeugt
vermuten|fɛɐ̯ˈmuːtn̩|taxmin qilmoq|Ich vermute, dass der Bus im Stau steht.|Menimcha, avtobus tirbandlikda turibdi.|vermutet, vermutete, hat vermutet
bezweifeln|bəˈtsvaɪfl̩n|shubha qilmoq|Ich bezweifle, dass wir heute fertig werden.|Bugun tugatishimizga shubha qilaman.|bezweifelt, bezweifelte, hat bezweifelt
beweisen|bəˈvaɪzn̩|isbotlamoq|Kannst du diese Aussage beweisen?|Bu fikrni isbotlay olasanmi?|beweist, bewies, hat bewiesen
zugeben|ˈtsuːɡeːbn̩|tan olmoq|Ich gebe zu, dass ich mich geirrt habe.|Adashganimni tan olaman.|gibt zu, gab zu, hat zugegeben
betonen|bəˈtoːnən|ta’kidlamoq|Sie betont, wie wichtig die Zusammenarbeit ist.|U hamkorlik qanchalik muhimligini ta’kidlaydi.|betont, betonte, hat betont
erwähnen|ɛɐ̯ˈvɛːnən|tilga olmoq|Den Preis hast du noch nicht erwähnt.|Narxni hali tilga olmading.|erwähnt, erwähnte, hat erwähnt
hinzufügen|hɪnˈtsuːfyːɡn̩|qo‘shimcha qilmoq|Zu deiner Erklärung möchte ich noch etwas hinzufügen.|Tushuntirishingga yana bir narsa qo‘shmoqchiman.|fügt hinzu, fügte hinzu, hat hinzugefügt
auf den Punkt kommen|aʊf deːn ˈpʊŋkt ˌkɔmən|asosiy gapga o‘tmoq|Wir haben wenig Zeit; komm bitte auf den Punkt.|Vaqtimiz oz; iltimos, asosiy gapga o‘t.|kommt auf den Punkt, kam auf den Punkt, ist auf den Punkt gekommen
beurteilen|bəˈʔʊʁtaɪlən|baho bermoq|Ohne weitere Informationen kann ich das nicht beurteilen.|Qo‘shimcha ma’lumotsiz bunga baho bera olmayman.|beurteilt, beurteilte, hat beurteilt
unterscheiden|ʊntɐˈʃaɪdn̩|farqlamoq|Wir müssen zwischen Wunsch und Wirklichkeit unterscheiden.|Istak bilan haqiqatni farqlashimiz kerak.|unterscheidet, unterschied, hat unterschieden
berücksichtigen|bəˈʁʏkˌzɪçtɪɡn̩|hisobga olmoq|Bitte berücksichtige auch die Fahrtzeit.|Iltimos, yo‘lga ketadigan vaqtni ham hisobga ol.|berücksichtigt, berücksichtigte, hat berücksichtigt
dagegen sein|daˈɡeːɡn̩ zaɪn|qarshi bo‘lmoq|Die Eintrittspreise sollen steigen, aber ich bin dagegen.|Kirish narxlarini oshirishmoqchi, ammo men bunga qarshiman.|ist dagegen, war dagegen, ist dagegen gewesen
befürchten|bəˈfʏʁçtn̩|xavotir olmoq|Ich befürchte, dass der Saal zu klein ist.|Zal juda kichik bo‘lishidan xavotirdaman.|befürchtet, befürchtete, hat befürchtet
davon ausgehen|daˈfɔn ˌaʊsɡeːən|shunday deb hisoblamoq, faraz qilmoq|Ich gehe davon aus, dass alle pünktlich kommen.|Hamma vaqtida keladi deb hisoblayman.|geht davon aus, ging davon aus, ist davon ausgegangen
schätzen|ˈʃɛtsn̩|qadrlamoq; chamalamoq|Ich schätze deine ruhige Art.|Sening xotirjamligingni qadrlayman.|schätzt, schätzte, hat geschätzt
abhängen|ˈaphɛŋən|bog‘liq bo‘lmoq|Unsere Entscheidung hängt vom Preis ab.|Qarorimiz narxga bog‘liq.|hängt ab, hing ab, hat abgehangen
beeinflussen|bəˈʔaɪnflʊsn̩|ta’sir ko‘rsatmoq|Müde zu sein beeinflusst meine Stimmung.|Charchagan bo‘lish kayfiyatimga ta’sir qiladi.|beeinflusst, beeinflusste, hat beeinflusst
ausdrücken|ˈaʊsdʁʏkn̩|ifoda etmoq|Auf Deutsch kann ich meine Gefühle immer besser ausdrücken.|Nemis tilida hislarimni tobora yaxshiroq ifodalay olaman.|drückt aus, drückte aus, hat ausgedrückt
formulieren|fɔʁmuˈliːʁən|so‘z bilan ifodalamoq|Formuliere deine Bitte möglichst klar.|Iltimosingni imkon qadar aniq ifodala.|formuliert, formulierte, hat formuliert
sich einigen|zɪç ˈaɪnɪɡn̩|kelishmoq|Wir einigen uns auf einen früheren Termin.|Ertaroq vaqtga kelishamiz.|einigt sich, einigte sich, hat sich geeinigt
Wie meinen Sie das?|viː ˈmaɪnən ziː das|Bu bilan nimani nazarda tutyapsiz?|Entschuldigung, wie meinen Sie das genau?|Kechirasiz, bu bilan aynan nimani nazarda tutyapsiz?|
überzeugend|yːbɐˈtsɔʏɡn̩t|ishonarli|Deine Begründung klingt überzeugend.|Asoslashing ishonarli eshitilyapti.|
nachvollziehbar|ˈnaːxfɔlˌtsiːbaːɐ̯|tushunsa bo‘ladigan, asosli|Deine Entscheidung ist für mich nachvollziehbar.|Qaroringni tushunsa bo‘ladi deb hisoblayman.|
eindeutig|ˈaɪnˌdɔʏtɪç|aniq, bir ma’noli|Das Ergebnis ist eindeutig.|Natija aniq.|
fraglich|ˈfʁaːklɪç|shubhali, noma’lum|Ob der Plan bezahlbar ist, bleibt fraglich.|Rejaga pul yetishi hali noma’lum.|
sinnvoll|ˈzɪnfoːl|maqsadga muvofiq, foydali|Eine Pause wäre jetzt sinnvoll.|Hozir tanaffus qilish maqsadga muvofiq bo‘lardi.|
wesentlich|ˈveːzn̩tlɪç|muhim, asosiy; ancha|Der neue Vorschlag ist wesentlich günstiger.|Yangi taklif ancha arzonroq.|
entscheidend|ɛntˈʃaɪdn̩t|hal qiluvchi|Für mich ist die Lage der Wohnung entscheidend.|Men uchun kvartiraning joylashuvi hal qiluvchi ahamiyatga ega.|
umstritten|ʊmˈʃtʁɪtn̩|bahsli|Die neue Parkregel ist im Viertel umstritten.|Yangi mashina qo‘yish qoidasi mahallada bahsli.|
einerseits … andererseits|ˈaɪnɐzaɪts ˈandəʁɐzaɪts|bir tomondan … boshqa tomondan|Einerseits möchte ich sparen, andererseits brauche ich ein Fahrrad.|Bir tomondan pul tejamoqchiman, boshqa tomondan menga velosiped kerak.|
zwar … aber|tsvaːɐ̯ ˈaːbɐ|garchi … lekin|Der Kurs ist zwar teuer, aber sehr hilfreich.|Kurs garchi qimmat bo‘lsa-da, juda foydali.|
obwohl|ɔpˈvoːl|...ga qaramay|Obwohl ich dir zuhöre, bin ich anderer Meinung.|Seni tinglayotgan bo‘lsam ham, fikrim boshqacha.|
trotzdem|ˈtʁɔtsdeːm|shunga qaramay|Es gibt Risiken; trotzdem möchte ich es versuchen.|Xavflar bor; shunga qaramay urinib ko‘rmoqchiman.|
dennoch|ˈdɛnɔx|shunday bo‘lsa ham|Der Plan ist schwierig, dennoch halte ich ihn für machbar.|Reja qiyin, shunday bo‘lsa ham uni bajarish mumkin deb hisoblayman.|
allerdings|alɐˈdɪŋs|biroq, lekin|Ich komme gern, allerdings erst nach sechs.|Bajonidil kelaman, biroq faqat oltidan keyin.|
hingegen|hɪnˈɡeːɡn̩|esa, aksincha|Ich fahre gern Zug, mein Bruder hingegen fliegt lieber.|Men poyezdda yurishni yoqtiraman, akam esa uchishni afzal ko‘radi.|
außerdem|ˈaʊsɐdeːm|bundan tashqari|Der Weg ist kurz; außerdem ist er gut beleuchtet.|Yo‘l qisqa; bundan tashqari yaxshi yoritilgan.|
daher|ˈdaːheːɐ̯|shuning uchun|Der Raum ist klein; daher begrenzen wir die Teilnehmerzahl.|Xona kichik; shuning uchun qatnashchilar sonini cheklaymiz.|
folglich|ˈfɔlklɪç|demak, natijada|Alle Plätze sind besetzt; folglich brauchen wir weitere Stühle.|Hamma joy band; demak, yana stullar kerak.|
nämlich|ˈnɛːmlɪç|chunki, ya’ni|Ich muss früher gehen; mein Zug fährt nämlich um sechs.|Ertaroq ketishim kerak; chunki poyezdim oltida jo‘naydi.|
beispielsweise|ˈbaɪʃpiːlsˌvaɪzə|masalan|Wir könnten beispielsweise einen Flohmarkt organisieren.|Masalan, eski buyumlar bozorini tashkil qilishimiz mumkin.|
insbesondere|ɪnsbəˈzɔndəʁə|ayniqsa, xususan|Der Kurs hilft insbesondere beim freien Sprechen.|Kurs ayniqsa erkin gapirishga yordam beradi.|
grundsätzlich|ˈɡʁʊntˌzɛtslɪç|umuman olganda, tamoyil jihatidan|Grundsätzlich bin ich mit dem Vorschlag einverstanden.|Umuman olganda, taklifga roziman.|
eher|ˈeːɐ̯|ko‘proq, yaxshisi|Ich wäre eher für einen Termin am Vormittag.|Men ko‘proq ertalabki vaqt tarafdori bo‘lardim.|
keineswegs|ˈkaɪnəsˌveːks|aslo, hech ham|Damit bin ich keineswegs einverstanden.|Men bunga aslo rozi emasman.|
im Gegensatz zu|ɪm ˈɡeːɡn̩zats tsuː|...dan farqli ravishda|Im Gegensatz zu mir steht Lea gern früh auf.|Mendan farqli ravishda Lea erta turishni yoqtiradi.|
'''))

BLOCKS.append((24, 'Probleme lösen und sicher kommunizieren', r'''
die Panne|ˈpanə|yo‘ldagi nosozlik, kutilmagan xato|Mitten auf der Fahrt hatten wir eine Panne.|Yo‘lning o‘rtasida mashinamiz buzilib qoldi.|die Pannen
die Störung|ˈʃtøːʁʊŋ|nosozlik, uzilish|Wegen einer Störung fährt die U-Bahn unregelmäßig.|Nosozlik sababli metro tartibsiz qatnayapti.|die Störungen
außer Betrieb sein|ˈaʊsɐ bəˈtʁiːp zaɪn|ishlamayotgan bo‘lmoq|Der Aufzug ist vorübergehend außer Betrieb.|Lift vaqtincha ishlamayapti.|ist außer Betrieb, war außer Betrieb, ist außer Betrieb gewesen
die Unterbrechung|ʊntɐˈbʁɛçʊŋ|uzilish, to‘xtatib turish|Nach einer kurzen Unterbrechung setzen wir das Gespräch fort.|Qisqa uzilishdan so‘ng suhbatni davom ettiramiz.|die Unterbrechungen
sich irren|zɪç ˈɪʁən|adashmoq|Ich habe mich im Datum geirrt.|Sanada adashibman.|irrt sich, irrte sich, hat sich geirrt
das Versehen|fɛɐ̯ˈzeːən|bexosdan qilingan xato|Ich habe die E-Mail aus Versehen gelöscht.|Elektron xatni adashib o‘chirib yubordim.|die Versehen
die Schwierigkeit|ˈʃviːʁɪçkaɪt|qiyinchilik|Bei Schwierigkeiten kannst du mich jederzeit fragen.|Qiyinchilik tug‘ilsa, istalgan payt mendan so‘rashing mumkin.|die Schwierigkeiten
sich einer Aufgabe stellen|zɪç aɪnɐ ˈaʊfɡaːbə ˌʃtɛlən|vazifani bajarishga bel bog‘lamoq|Trotz meiner Zweifel stelle ich mich der Aufgabe.|Shubhalarimga qaramay, vazifani bajarishga bel bog‘layman.|stellt sich, stellte sich, hat sich gestellt; Dativ
die Notlösung|ˈnoːtˌløːzʊŋ|vaqtinchalik majburiy yechim|Die Luftmatratze ist nur eine Notlösung.|Havo to‘shagi faqat vaqtinchalik yechim.|die Notlösungen
die Fehlerquelle|ˈfeːlɐˌkvɛlə|xato kelib chiqish manbasi|Ein lockeres Kabel war die Fehlerquelle.|Bo‘shashgan sim nosozlik manbasi ekan.|die Fehlerquellen
der Ersatz|ɛɐ̯ˈzats|o‘rnini bosuvchi narsa, almashtirish|Für die kaputte Lampe bekommen wir Ersatz.|Buzilgan chiroq o‘rniga yangisini olamiz.|odatda birlikda
das Ersatzteil|ɛɐ̯ˈzatsˌtaɪl|ehtiyot qism|Das passende Ersatzteil kommt erst am Montag.|Mos ehtiyot qism faqat dushanba kuni keladi.|die Ersatzteile
die Anleitung|ˈanˌlaɪtʊŋ|yo‘riqnoma|Ohne Anleitung sieht mein Regal wie moderne Kunst aus.|Yo‘riqnomasiz tokcham zamonaviy san’at asariga o‘xshaydi.|die Anleitungen
auf etwas hinweisen|aʊf ˈʔɛtvas ˌhɪnvaɪzn̩|biror narsaga e’tibor qaratmoq|Ich möchte auf einen Fehler im Formular hinweisen.|Blankadagi xatoga e’tibor qaratmoqchiman.|weist hin, wies hin, hat hingewiesen; auf + Akkusativ
die Warnung|ˈvaʁnʊŋ|ogohlantirish|Die Warnung vor dem Sturm kam rechtzeitig.|Bo‘ron haqidagi ogohlantirish vaqtida keldi.|die Warnungen
die Gefahr|ɡəˈfaːɐ̯|xavf|Auf der vereisten Treppe besteht große Gefahr.|Muzlagan zinada katta xavf bor.|die Gefahren
das Risiko|ˈʁiːziko|tavakkal, xavf ehtimoli|Dieses Risiko möchte ich nicht eingehen.|Bunday tavakkal qilmoqchi emasman.|die Risiken
der Zufall|ˈtsuːfal|tasodif|Dass wir uns hier treffen, ist ein schöner Zufall.|Bu yerda uchrashganimiz yoqimli tasodif.|die Zufälle
das Pech|pɛç|omadsizlik|Heute habe ich Pech: Erst fällt der Bus aus, dann regnet es.|Bugun omadsizman: avval avtobus bekor bo‘ldi, keyin yomg‘ir yog‘di.|bu ma’noda ko‘plik yo‘q
das Glück|ɡlʏk|omad, baxt|Zum Glück hatte ich den Schlüssel in der Jacke.|Yaxshiyamki, kalit kurtkamda ekan.|ko‘plik yo‘q
der Versuch|fɛɐ̯ˈzuːx|urinish|Beim dritten Versuch ging die Tür endlich auf.|Uchinchi urinishda eshik nihoyat ochildi.|die Versuche
vorankommen|foˈʁankɔmən|olg‘a siljimoq|Mit täglichen Übungen komme ich beim Deutschlernen voran.|Kundalik mashqlar bilan nemis tilida olg‘a siljiyapman.|kommt voran, kam voran, ist vorangekommen
der Erfolg|ɛɐ̯ˈfɔlk|muvaffaqiyat|Unser erster gemeinsamer Auftritt war ein Erfolg.|Birinchi birgalikdagi chiqishimiz muvaffaqiyatli bo‘ldi.|die Erfolge
der Misserfolg|ˈmɪsʔɛɐ̯ˌfɔlk|muvaffaqiyatsizlik|Ein Misserfolg bedeutet nicht das Ende.|Bir muvaffaqiyatsizlik hammasi tugadi degani emas.|die Misserfolge
die Mühe|ˈmyːə|mehnat, zahmat|Vielen Dank für Ihre Mühe und Geduld.|Zahmatingiz va sabringiz uchun katta rahmat.|die Mühen
der Aufwand|ˈaʊfvant|sarflanadigan vaqt, mehnat yoki mablag‘|Der Aufwand für die Anmeldung ist gering.|Ro‘yxatdan o‘tish ko‘p mehnat talab qilmaydi.|die Aufwände
die Möglichkeit|ˈmøːklɪçkaɪt|imkoniyat|Gibt es eine Möglichkeit, den Termin zu tauschen?|Belgilangan vaqtni almashtirish imkoniyati bormi?|die Möglichkeiten
die Entscheidung|ɛntˈʃaɪdʊŋ|qaror|Für diese Entscheidung brauche ich noch einen Tag.|Bu qaror uchun menga yana bir kun kerak.|die Entscheidungen
die Veränderung|fɛɐ̯ˈʔɛndəʁʊŋ|o‘zgarish|Eine kleine Veränderung macht den Alltag leichter.|Kichik bir o‘zgarish kundalik hayotni osonlashtiradi.|die Veränderungen
die Entwicklung|ɛntˈvɪklʊŋ|rivojlanish|Die Entwicklung des Projekts freut uns.|Loyihaning rivojlanishi bizni xursand qiladi.|die Entwicklungen
die Verbesserung|fɛɐ̯ˈbɛsəʁʊŋ|yaxshilanish|Nach dem Gespräch gab es eine deutliche Verbesserung.|Suhbatdan keyin sezilarli yaxshilanish bo‘ldi.|die Verbesserungen
die Rücksicht|ˈʁʏkzɪçt|boshqalarni hisobga olish|Aus Rücksicht auf das Baby sprechen wir leise.|Chaqaloqni hisobga olib, past ovozda gaplashamiz.|odatda birlikda
das Verständnis|fɛɐ̯ˈʃtɛntnɪs|tushunish, hamdardlik|Vielen Dank für Ihr Verständnis bei der Verspätung.|Kechikishni tushunganingiz uchun katta rahmat.|odatda birlikda
etwas wiedergutmachen|ˈʔɛtvas ˌviːdɐˈɡuːtmaxn̩|qilgan xatosini tuzatmoq|Den Fehler möchte ich mit meiner Hilfe wiedergutmachen.|Xatomni yordamim bilan tuzatmoqchiman.|macht wieder gut, machte wieder gut, hat wiedergutgemacht
das Versprechen|fɛɐ̯ˈʃpʁɛçn̩|va’da|Dieses Versprechen werde ich halten.|Bu va’damda turaman.|die Versprechen
die Erinnerung|ɛɐ̯ˈʔɪnəʁʊŋ|xotira, eslatma|Ich stelle mir eine Erinnerung für den Termin ein.|Uchrashuv uchun eslatma o‘rnataman.|die Erinnerungen
der Eindruck|ˈaɪndʁʊk|taassurot|Beim Gespräch hatte ich einen guten Eindruck von der Firma.|Suhbatda firma haqida yaxshi taassurot oldim.|die Eindrücke
mit etwas rechnen|mɪt ˈʔɛtvas ˌʁɛçnən|biror narsani kutmoq, hisobga olmoq|Mit einer so schnellen Antwort habe ich nicht gerechnet.|Bunchalik tez javobni kutmagandim.|rechnet mit, rechnete mit, hat mit etwas gerechnet; mit + Dativ
in Betracht ziehen|ɪn bəˈtʁaxt ˌtsiːən|variant sifatida ko‘rib chiqmoq|Wir ziehen auch einen späteren Termin in Betracht.|Kechroq sanani ham variant sifatida ko‘rib chiqyapmiz.|zieht in Betracht, zog in Betracht, hat in Betracht gezogen
die Empfehlung|ɛmˈpfeːlʊŋ|tavsiya|Auf deine Empfehlung habe ich den Kurs gewählt.|Sening tavsiyang bilan kursni tanladim.|die Empfehlungen
jemandem einen Gefallen tun|ˈjeːmandəm aɪnən ɡəˈfalən ˌtuːn|kimga yaxshilik qilmoq|Könntest du mir einen Gefallen tun und das Paket annehmen?|Paketni qabul qilib, menga bir yaxshilik qila olasanmi?|tut einen Gefallen, tat einen Gefallen, hat einen Gefallen getan
die Forderung|ˈfɔʁdəʁʊŋ|talab|Unsere wichtigste Forderung sind sichere Schulwege.|Eng muhim talabimiz — maktabga xavfsiz yo‘llar.|die Forderungen
entgegenkommen|ɛntˈɡeːɡn̩ˌkɔmən|yon bermoq, kelishuvga borish|Beim Preis kommt uns der Händler etwas entgegen.|Sotuvchi narxda bizga biroz yon beryapti.|kommt entgegen, kam entgegen, ist entgegengekommen
die Nachfrage|ˈnaːxˌfʁaːɡə|talab; qo‘shimcha so‘rov|Wegen der großen Nachfrage gibt es einen zweiten Kurs.|Talab yuqoriligi sababli ikkinchi kurs ham ochiladi.|die Nachfragen; bozor talabi ma’nosida birlikda
der Bedarf|bəˈdaʁf|ehtiyoj|An günstigen Wohnungen besteht großer Bedarf.|Arzon kvartiralarga katta ehtiyoj bor.|die Bedarfe
der Umgang|ˈʊmɡaŋ|muomala, foydalanish|Den Umgang mit der neuen Maschine üben wir gemeinsam.|Yangi mashinadan foydalanishni birgalikda mashq qilamiz.|bu ma’noda ko‘plik yo‘q
die Übersicht|ˈyːbɐˌzɪçt|umumiy ko‘rinish, jamlanma|Eine Übersicht über die Kosten hilft uns beim Planen.|Xarajatlar jamlanmasi rejalashtirishga yordam beradi.|die Übersichten
die Einzelheit|ˈaɪntsl̩haɪt|tafsilot|Die Einzelheiten klären wir nach der Pause.|Tafsilotlarni tanaffusdan keyin aniqlashtiramiz.|die Einzelheiten
die Reihenfolge|ˈʁaɪənˌfɔlɡə|ketma-ketlik|In welcher Reihenfolge sollen wir die Aufgaben erledigen?|Vazifalarni qaysi ketma-ketlikda bajarishimiz kerak?|die Reihenfolgen
der Schritt|ʃʁɪt|qadam, bosqich|Der erste Schritt ist oft der schwerste.|Birinchi qadam ko‘pincha eng qiyini bo‘ladi.|die Schritte
Abhilfe schaffen|ˈapˌhɪlfə ˌʃafn̩|muammoni bartaraf etmoq|Ein neuer Router könnte hier Abhilfe schaffen.|Yangi router bu muammoni bartaraf etishi mumkin.|schafft Abhilfe, schuf Abhilfe, hat Abhilfe geschaffen
klären|ˈklɛːʁən|aniqlashtirmoq|Wir sollten zuerst die Zuständigkeit klären.|Avval kim mas’ulligini aniqlashtirishimiz kerak.|klärt, klärte, hat geklärt
feststellen|ˈfɛstʃtɛlən|aniqlamoq, qayd etmoq|Zu Hause stellte ich fest, dass ein Teil fehlte.|Uyda bir qism yetishmayotganini aniqladim.|stellt fest, stellte fest, hat festgestellt
herausfinden|hɛˈʁaʊsfɪndn̩|bilib olmoq, aniqlamoq|Wir müssen herausfinden, wo der Fehler liegt.|Xato qayerdaligini aniqlashimiz kerak.|findet heraus, fand heraus, hat herausgefunden
beheben|bəˈheːbn̩|bartaraf etmoq|Der Techniker hat die Störung schnell behoben.|Texnik nosozlikni tez bartaraf etdi.|behebt, behob, hat behoben
austauschen|ˈaʊstaʊʃn̩|almashtirmoq; fikr almashmoq|Wir tauschen das defekte Teil aus.|Nosoz qismni almashtiramiz.|tauscht aus, tauschte aus, hat ausgetauscht
in Ordnung bringen|ɪn ˈʔɔʁdnʊŋ ˌbʁɪŋən|tuzatib, tartibga keltirmoq|Bis morgen bringe ich den Fehler in der Rechnung in Ordnung.|Hisob-fakturadagi xatoni ertagacha tuzataman.|bringt in Ordnung, brachte in Ordnung, hat in Ordnung gebracht
scheitern|ˈʃaɪtɐn|muvaffaqiyatsizlikka uchramoq|Unser erster Plan ist am Geld gescheitert.|Birinchi rejamiz pul yetishmagani sababli amalga oshmadi.|scheitert, scheiterte, ist gescheitert
gelingen|ɡəˈlɪŋən|uddalanmoq, muvaffaqiyatli chiqmoq|Beim zweiten Versuch ist mir der Kuchen gelungen.|Ikkinchi urinishda pirogim yaxshi chiqdi.|gelingt, gelang, ist gelungen
schaffen|ˈʃafn̩|uddalamoq|Mit deiner Hilfe schaffe ich das bis morgen.|Sening yordaming bilan buni ertagacha uddalayman.|schafft, schaffte, hat geschafft
bewältigen|bəˈvɛltɪɡn̩|uddasidan chiqmoq|So viel Arbeit kann ich allein nicht bewältigen.|Buncha ishning uddasidan yolg‘iz chiqa olmayman.|bewältigt, bewältigte, hat bewältigt
auf Nummer sicher gehen|aʊf ˈnʊmɐ ˈzɪçɐ ˌɡeːən|ishonch hosil qilish uchun ehtiyot chorasi ko‘rmoq|Ich rufe noch einmal an, um auf Nummer sicher zu gehen.|Ishonch hosil qilish uchun yana bir bor qo‘ng‘iroq qilaman.|geht auf Nummer sicher, ging auf Nummer sicher, ist auf Nummer sicher gegangen
nachdenken|ˈnaːxdɛŋkn̩|o‘ylab ko‘rmoq|Über dein Angebot möchte ich noch nachdenken.|Taklifing haqida yana o‘ylab ko‘rmoqchiman.|denkt nach, dachte nach, hat nachgedacht
überlegen|yːbɐˈleːɡn̩|mulohaza qilmoq|Wir überlegen, ob wir den Termin verschieben.|Uchrashuvni boshqa vaqtga ko‘chirish haqida o‘ylayapmiz.|überlegt, überlegte, hat überlegt
einen Vorschlag aufgreifen|aɪnən ˈfoːɐ̯ʃlaːk ˌaʊfɡʁaɪfn̩|taklifni qabul qilib rivojlantirmoq|Die Chefin greift meinen Vorschlag auf.|Rahbarim taklifimni qabul qilib rivojlantirmoqda.|greift auf, griff auf, hat aufgegriffen
empfehlen|ɛmˈpfeːlən|tavsiya qilmoq|Welche Werkstatt kannst du mir empfehlen?|Menga qaysi ustaxonani tavsiya qila olasan?|empfiehlt, empfahl, hat empfohlen
bitten|ˈbɪtn̩|iltimos qilmoq|Ich bitte Sie um eine kurze Bestätigung.|Sizdan qisqa tasdiq berishingizni so‘rayman.|bittet, bat, hat gebeten
fordern|ˈfɔʁdɐn|talab qilmoq|Die Mieter fordern eine schnelle Reparatur.|Ijarachilar tez ta’mirlashni talab qilmoqda.|fordert, forderte, hat gefordert
zur Wahl stehen|tsuːɐ̯ ˈvaːl ˌʃteːən|tanlash uchun mavjud bo‘lmoq|Zwei Termine stehen zur Wahl.|Tanlash uchun ikkita vaqt bor.|steht zur Wahl, stand zur Wahl, hat zur Wahl gestanden
annehmen|ˈanneːmən|qabul qilmoq; faraz qilmoq|Deine Hilfe nehme ich gern an.|Yordamingni bajonidil qabul qilaman.|nimmt an, nahm an, hat angenommen
sein Wort halten|zaɪn ˈvɔʁt ˌhaltn̩|so‘zida turmoq|Auf ihn ist Verlass, denn er hält sein Wort.|Unga ishonish mumkin, chunki u so‘zida turadi.|hält sein Wort, hielt sein Wort, hat sein Wort gehalten
um Verzeihung bitten|ʊm fɛɐ̯ˈtsaɪʊŋ ˌbɪtn̩|kechirim so‘ramoq|Für meine unfreundliche Antwort bitte ich um Verzeihung.|Qo‘pol javobim uchun kechirim so‘rayman.|bittet um Verzeihung, bat um Verzeihung, hat um Verzeihung gebeten
eine Beschwerde einreichen|aɪnə bəˈʃveːɐ̯də ˌaɪnʁaɪçn̩|shikoyat topshirmoq|Wegen der doppelten Abbuchung reiche ich eine Beschwerde ein.|Pul ikki marta yechilgani sababli shikoyat topshiraman.|reicht ein, reichte ein, hat eingereicht
auf Kritik eingehen|aʊf kʁiˈtiːk ˌaɪnɡeːən|tanqidga javoban fikr bildirmoq|Im Gespräch geht die Leiterin auf unsere Kritik ein.|Suhbatda rahbar bizning tanqidimizga javoban fikr bildiradi.|geht ein, ging ein, ist eingegangen
umgehen mit|ˈʊmɡeːən mɪt|...bilan muomala qilmoq, ...ni eplamoq|Mit Zeitdruck kann sie gut umgehen.|U vaqt tig‘izligini yaxshi eplaydi.|geht um, ging um, ist umgegangen; mit + Dativ
hilfreich|ˈhɪlfʁaɪç|foydali, yordam beradigan|Dein Hinweis war wirklich hilfreich.|Ko‘rsatmang haqiqatan foydali bo‘ldi.|
vergeblich|fɛɐ̯ˈɡeːplɪç|behuda|Ich habe vergeblich auf eine Antwort gewartet.|Javobni behuda kutdim.|
zufällig|ˈtsuːˌfɛlɪç|tasodifan|Hast du zufällig einen Schraubenzieher dabei?|Tasodifan yoningda otvyortka bormi?|
unangenehm|ˈʊnʔanɡəˌneːm|yoqimsiz|Das Gespräch war unangenehm, aber notwendig.|Suhbat yoqimsiz, ammo zarur edi.|
peinlich|ˈpaɪnlɪç|uyatli, xijolatli|Mein lauter Klingelton war mir in der Sitzung peinlich.|Yig‘ilishda telefonimning baland jiringlashidan xijolat bo‘ldim.|
umständlich|ˈʊmˌʃtɛntlɪç|ortiqcha murakkab, noqulay|Die Anmeldung ist leider ziemlich umständlich.|Afsuski, ro‘yxatdan o‘tish ancha murakkab.|
umsichtig|ˈʊmˌzɪçtɪç|ehtiyotkor va vaziyatni hisobga oladigan|Die Fahrerin reagiert ruhig und umsichtig.|Haydovchi ayol xotirjam va vaziyatni hisobga olib harakat qiladi.|
ratlos|ˈʁaːtloːs|nima qilishni bilmay qolgan|Vor den vielen Kabeln stand ich ratlos.|Ko‘plab simlar oldida nima qilishni bilmay qoldim.|
offen|ˈɔfn̩|ochiq; hal etilmagan|Zwei Fragen sind noch offen.|Ikki savol hali ochiq qolmoqda.|
bereit|bəˈʁaɪt|tayyor|Ich bin bereit, einen neuen Versuch zu machen.|Yana urinib ko‘rishga tayyorman.|
Bescheid geben|bəˈʃaɪt ˈɡeːbn̩|xabar bermoq|Gib mir bitte Bescheid, sobald du etwas weißt.|Biror narsa bilishing bilanoq menga xabar ber.|gibt Bescheid, gab Bescheid, hat Bescheid gegeben
in Frage kommen|ɪn ˈfʁaːɡə ˌkɔmən|mos variant bo‘la olmoq|Ein Termin am Montag kommt für mich nicht in Frage.|Dushanbadagi uchrashuv men uchun to‘g‘ri kelmaydi.|kommt in Frage, kam in Frage, ist in Frage gekommen
zur Verfügung stehen|tsuːɐ̯ fɛɐ̯ˈfyːɡʊŋ ˌʃteːən|ixtiyorda bo‘lmoq|Für Fragen stehe ich Ihnen gern zur Verfügung.|Savollaringizga bajonidil javob berishga tayyorman.|steht zur Verfügung, stand zur Verfügung, hat zur Verfügung gestanden
in Anspruch nehmen|ɪn ˈanʃpʁʊx ˌneːmən|foydalanmoq; vaqt talab qilmoq|Die Reparatur nimmt zwei Tage in Anspruch.|Ta’mirlash ikki kun vaqt oladi.|nimmt in Anspruch, nahm in Anspruch, hat in Anspruch genommen
in Kauf nehmen|ɪn ˈkaʊf ˌneːmən|salbiy oqibatga ko‘nmoq|Für die günstigere Wohnung nehme ich einen längeren Weg in Kauf.|Arzonroq kvartira uchun uzoqroq yo‘lga ko‘naman.|nimmt in Kauf, nahm in Kauf, hat in Kauf genommen
sich Mühe geben|zɪç ˈmyːə ˌɡeːbn̩|astoydil harakat qilmoq|Ich gebe mir Mühe, jeden Tag Deutsch zu sprechen.|Har kuni nemischa gapirishga astoydil harakat qilaman.|gibt sich Mühe, gab sich Mühe, hat sich Mühe gegeben
Wert legen auf|ˈveːɐ̯t ˌleːɡn̩ aʊf|...ga ahamiyat bermoq|Bei einer Zusammenarbeit lege ich Wert auf Ehrlichkeit.|Hamkorlikda halollikka ahamiyat beraman.|legt Wert auf, legte Wert auf, hat Wert auf etwas gelegt; auf + Akkusativ
zur Sprache bringen|tsuːɐ̯ ˈʃpʁaːxə ˌbʁɪŋən|gap ochmoq, muhokamaga qo‘ymoq|Beim Treffen bringe ich das Problem zur Sprache.|Uchrashuvda muammo haqida gap ochaman.|bringt zur Sprache, brachte zur Sprache, hat zur Sprache gebracht
auf dem Laufenden bleiben|aʊf deːm ˈlaʊfn̩dn̩ ˌblaɪbn̩|xabardor bo‘lib turmoq|Über die Gruppe bleibe ich auf dem Laufenden.|Guruh orqali xabardor bo‘lib turaman.|bleibt auf dem Laufenden, blieb auf dem Laufenden, ist auf dem Laufenden geblieben
im Voraus|ɪm foˈʁaʊs|oldindan|Vielen Dank im Voraus für Ihre Unterstützung.|Qo‘llab-quvvatlashingiz uchun oldindan rahmat.|
auf jeden Fall|aʊf ˈjeːdn̩ fal|albatta, har qanday holatda|Auf jeden Fall sollten wir vorher anrufen.|Har qanday holatda oldindan qo‘ng‘iroq qilishimiz kerak.|
auf keinen Fall|aʊf ˈkaɪnən fal|hech qachon, aslo|Das Original möchte ich auf keinen Fall verlieren.|Asl nusxani aslo yo‘qotmoqchi emasman.|
im Großen und Ganzen|ɪm ˈɡʁoːsn̩ ʊnt ˈɡantsn̩|umuman olganda|Im Großen und Ganzen bin ich mit dem Kurs zufrieden.|Umuman olganda, kursdan mamnunman.|
Schritt für Schritt|ˈʃʁɪt fyːɐ̯ ˈʃʁɪt|bosqichma-bosqich|Wir lösen das Problem Schritt für Schritt.|Muammoni bosqichma-bosqich hal qilamiz.|
so bald wie möglich|zoː ˈbalt viː ˈmøːklɪç|imkon qadar tez|Bitte antworten Sie so bald wie möglich.|Iltimos, imkon qadar tez javob bering.|
'''))



def build():
    entries = []
    articles = {'der': 'deːɐ̯', 'die': 'diː', 'das': 'das'}
    for week, topic, block in BLOCKS:
        rows = [line.split('|') for line in block.strip().splitlines()]
        assert len(rows) == 100, (week, len(rows))
        for offset, row in enumerate(rows):
            assert len(row) == 6, (week, offset, row)
            word, ipa, meaning, example, translation, forms = row
            article = word.split(' ')[0]
            if article in articles:
                ipa = articles[article] + ' ' + ipa
                assert forms, word
            entries.append(dict(id=(week-1)*100+offset+1, week=week,
                topic=topic, word=word, ipa='['+ipa+']', meaning=meaning,
                example=example, translation=translation, forms=forms))
    words = Counter(e['word'].casefold() for e in entries)
    duplicates = [word for word, count in words.items() if count > 1]
    assert not duplicates, duplicates
    assert len(entries) == 800, len(entries)
    assert [e['id'] for e in entries] == list(range(1601, 2401))
    assert all(e['week'] == (e['id']+99)//100 for e in entries)
    string_fields = ('topic', 'word', 'ipa', 'meaning', 'example', 'translation', 'forms')
    assert all(isinstance(e[k], str) for e in entries for k in string_fields)
    assert all(e[k].strip() for e in entries for k in string_fields if k != 'forms')
    assert len({e['example'] for e in entries}) == len(entries)
    target = Path(__file__).resolve().parents[1] / 'src/data/german/vocabulary-3.json'
    # Other contributors' files are only read; rerunning also checks integration.
    for part in (1, 2):
        other_path = target.with_name(f'vocabulary-{part}.json')
        if other_path.exists():
            other = json.loads(other_path.read_text(encoding='utf-8-sig'))
            other_words = {e['word'].casefold() for e in other}
            overlap = [e['word'] for e in entries if e['word'].casefold() in other_words]
            assert not overlap, (f'Part {part} overlap', overlap)
            print(f'Cross-part {part} duplicate headwords: 0')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(entries, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Count:', len(entries))
    print('Per week:', dict(Counter(e['week'] for e in entries)))
    print('Duplicate words:', duplicates)
    print('Duplicate examples:', [x for x,n in Counter(e['example'] for e in entries).items() if n>1])
    print('IDs: 1601–2400; contiguous; week=ceil(id/100): OK')
    print('Changed paths: scripts/german-vocab-3.py; src/data/german/vocabulary-3.json')

if __name__ == '__main__':
    build()
