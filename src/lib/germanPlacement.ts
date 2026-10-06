export type PlacementQuestion = { id: string; month: number; skill: 'grammar' | 'vocabulary' | 'reading'; topic: string; prompt: string; options: string[]; answer: number; text?: string };
export const placementMonths = ['A1 poydevor', 'A1 yakuni', 'A2 poydevor', 'A2 yakuni', 'B1 poydevor', 'B1 yakuni'];
// Original diagnostic items, separate from the course practice bank.
const rows: [number, PlacementQuestion['skill'], string, string, string[], number, string?][] = [
 [1,'grammar','sein','Ich ___ Student.',['bist','bin','ist','sind'],1],
 [1,'grammar','Savol tartibi','Qaysi savol to‘g‘ri?',['Wo du wohnst?','Du wo wohnst?','Wo wohnst du?','Wohnst wo du?'],2],
 [1,'grammar','Inkor va artikl','Das ist ___ Auto. Das ist ein Fahrrad.',['kein','keine','keinen','keinem'],0],
 [1,'grammar','Akkuzativ','Ich kaufe ___ Apfel.',['einem','eines','ein','einen'],3],
 [1,'vocabulary','Vaqt','Eine Woche hat sieben ___.',['Monate','Jahre','Tage','Stunden'],2],
 [1,'vocabulary','Kasb','Eine Lehrerin arbeitet normalerweise in einer ___.',['Schule','Bäckerei','Apotheke','Bank'],0],
 [1,'reading','Asosiy ma’lumot','Wo wohnt Nina?',['In Berlin','In Taschkent','In Wien','In Bonn'],1,'Ich heiße Nina und komme aus Berlin. Jetzt wohne ich in Taschkent. Ich lerne Deutsch am Montag und Mittwoch.'],
 [1,'reading','Jadval','Wann lernt Nina Deutsch?',['Jeden Tag','Am Wochenende','Dienstags und donnerstags','Montags und mittwochs'],3,'Ich heiße Nina und komme aus Berlin. Jetzt wohne ich in Taschkent. Ich lerne Deutsch am Montag und Mittwoch.'],
 [2,'grammar','Ajraladigan fe’l','Ich ___ jeden Morgen um sieben Uhr ___.',['stehe … auf','auf … stehe','steht … auf','stehe … an'],0],
 [2,'grammar','Modal fe’l','Wir müssen heute lange ___.',['arbeitet','arbeiten','gearbeitet','arbeitet haben'],1],
 [2,'grammar','Taqiq','Hier darf man nicht rauchen. Das bedeutet:',['Rauchen ist unnötig.','Rauchen ist erlaubt.','Rauchen ist verboten.','Man raucht später.'],2],
 [2,'grammar','Dativ','Ich fahre mit ___ Bus.',['den','der','des','dem'],3],
 [2,'vocabulary','Soat','Es ist halb neun.',['09:30','08:30','09:00','08:00'],1],
 [2,'vocabulary','Oila','Die Schwester meiner Mutter ist meine ___.',['Tante','Tochter','Oma','Cousine'],0],
 [2,'reading','E’lon','Wann kann man am Samstag Brot kaufen?',['Um 07:00','Um 14:00','Um 18:00','Um 10:00'],3,'Bäckerei Weber: Montag bis Freitag 7–18 Uhr, Samstag 8–12 Uhr. Sonntags geschlossen.'],
 [2,'reading','Yo‘l-yo‘riq','Was soll der Besucher tun?',['Im Erdgeschoss warten.','Zum zweiten Stock gehen.','Draußen bleiben.','Morgen kommen.'],1,'Die Praxis ist heute nicht im Erdgeschoss. Bitte gehen Sie in den zweiten Stock und melden Sie sich dort am Empfang.'],
 [3,'grammar','Perfekt: sein','Gestern ___ wir nach Samarkand gefahren.',['haben','werden','sind','waren'],2],
 [3,'grammar','Partizip II','Ich habe die Aufgabe schon ___.',['machen','gemacht','machte','mache'],1],
 [3,'grammar','Präteritum','Als Kind ___ ich jeden Tag früh aufstehen.',['muss','gemusst','müssen','musste'],3],
 [3,'grammar','Reflexiv','Er interessiert ___ für Musik.',['sich','mich','dich','uns'],0],
 [3,'vocabulary','Safar','Der Zug kommt später als geplant. Er hat ___.',['Urlaub','Verspätung','Erfolg','Besuch'],1],
 [3,'vocabulary','Ro‘yxatdan o‘tish','Für den Kurs muss ich ein Formular ___.',['abfahren','einschlafen','ausfüllen','anziehen'],2],
 [3,'reading','O‘tgan voqea','Warum nahm Lea den Bus?',['Ihr Fahrrad war kaputt.','Es regnete.','Der Bus war kostenlos.','Sie hatte kein Fahrrad.'],0,'Lea wollte gestern mit dem Fahrrad zur Arbeit fahren. Doch der Reifen war kaputt. Deshalb nahm sie den Bus und kam zehn Minuten zu spät.'],
 [3,'reading','Reja o‘zgarishi','Wann findet das Treffen statt?',['Heute um 16 Uhr','Morgen um 15 Uhr','Heute um 15 Uhr','Morgen um 16 Uhr'],3,'Hallo Tom, unser Treffen heute um 15 Uhr fällt aus. Können wir uns stattdessen morgen um 16 Uhr treffen? – Ja, das passt.'],
 [4,'grammar','Sifat turlanishi','Ich suche einen ___ Mantel.',['warme','warmen','warmes','warmem'],1],
 [4,'grammar','Taqqoslash','Dieser Zug ist ___ als der Bus.',['schneller','schnellste','schnellsten','schnelles'],0],
 [4,'grammar','weil','Ich bleibe zu Hause, weil ___.',['ich bin krank','bin ich krank','krank ich bin','ich krank bin'],3],
 [4,'grammar','Bilvosita savol','Wissen Sie, ___ der nächste Zug abfährt?',['denn','dass','wann','weil'],2],
 [4,'vocabulary','Uy-joy','Zusätzlich zur Miete bezahlt man oft ___.',['Hausaufgaben','Nebenkosten','Zeugnisse','Fahrkarten'],1],
 [4,'vocabulary','Taqqoslash','Dieser Preis ist sehr günstig. Das bedeutet:',['besonders hoch','noch unbekannt','relativ niedrig','immer gleich'],2],
 [4,'reading','Shart','Wer bekommt den günstigeren Eintritt?',['Alle Besucher','Nur Kinder','Nur Erwachsene','Personen mit Studentenausweis'],3,'Der Eintritt kostet 12 Euro. Studierende zahlen mit gültigem Studentenausweis nur 8 Euro. Ohne Ausweis gilt der normale Preis.'],
 [4,'reading','Sabab va yechim','Was bietet das Geschäft an?',['Das Geld sofort zurückzugeben.','Die Lieferung kostenlos zu bringen.','Die Ware teurer zu verkaufen.','Nur eine Abholung im Laden.'],1,'Ihre Bestellung kommt leider zwei Tage später, weil unser Lieferwagen ausgefallen ist. Als Entschuldigung berechnen wir Ihnen keine Versandkosten.'],
 [5,'grammar','obwohl','___ es regnet, gehen wir spazieren.',['Obwohl','Deshalb','Trotzdem','Wegen'],0],
 [5,'grammar','Maqsad','Ich lerne Deutsch, ___ in Deutschland zu studieren.',['damit','weil','um','dass'],2],
 [5,'grammar','Relativsatz','Das ist die Kollegin, ___ ich gestern geholfen habe.',['die','der','den','deren'],1],
 [5,'grammar','Plusquamperfekt','Nachdem er gegessen ___, ging er zur Arbeit.',['hat','ist','war','hatte'],3],
 [5,'vocabulary','Dalillash','Ein Vorteil ist eine ___ Seite einer Sache.',['positive','unbekannte','negative','unwichtige'],0],
 [5,'vocabulary','Mas’uliyat','Wer Verantwortung übernimmt, ___.',['vermeidet jede Aufgabe','kümmert sich um die Folgen seines Handelns','gibt immer anderen die Schuld','macht grundsätzlich nichts'],1],
 [5,'reading','Qarama-qarshi fikr','Was findet der Autor problematisch?',['Die tägliche Fahrt.','Die freie Zeiteinteilung.','Die fehlenden spontanen Gespräche.','Die kurzen Pausen.'],2,'Im Homeoffice spare ich täglich eine Stunde Fahrt. Trotzdem möchte ich nicht immer zu Hause arbeiten: Mir fehlen die spontanen Gespräche mit Kollegen. Zwei Bürotage pro Woche wären für mich ideal.'],
 [5,'reading','Taklif maqsadi','Warum soll die Bibliothek länger öffnen?',['Damit mehr Bücher verkauft werden.','Damit Angestellte früher gehen.','Damit Kinder dort schlafen können.','Damit Berufstätige sie nach der Arbeit nutzen können.'],3,'Viele Beschäftigte können die Bibliothek vor 18 Uhr nicht erreichen. Der Verein schlägt deshalb vor, sie donnerstags bis 21 Uhr zu öffnen. An den übrigen Tagen sollen die bisherigen Zeiten gelten.'],
 [6,'grammar','Konjunktiv II','Wenn ich mehr Zeit hätte, ___ ich öfter lesen.',['würde','werde','wurde','hatte'],0],
 [6,'grammar','Passiv','Die Briefe ___ jeden Morgen sortiert.',['haben','sind gewesen','werden','hätten'],2],
 [6,'grammar','Fe’l va predlog','Ich freue mich ___ den Urlaub nächste Woche.',['über','mit','bei','auf'],3],
 [6,'grammar','O‘zaro bog‘lanish','Je mehr ich übe, ___ sicherer werde ich.',['weil','desto','obwohl','damit'],1],
 [6,'vocabulary','Kelishuv','Einen Kompromiss finden bedeutet:',['Eine Lösung finden, bei der beide Seiten etwas nachgeben.','Eine Seite entscheidet alles.','Das Gespräch sofort abbrechen.','Jede Änderung ablehnen.'],0],
 [6,'vocabulary','Ish va hujjat','In einer Bewerbung beschreibt man vor allem ___.',['das Wetter','seine Berufserfahrung und Qualifikationen','die Speisekarte','die Öffnungszeiten'],1],
 [6,'reading','Muallif munosabati','Welche Aussage entspricht dem Text?',['Autos sollen überall verboten werden.','Busse sind immer leer.','Veränderungen müssen verschiedene Bedürfnisse berücksichtigen.','Nur Radfahrer brauchen sichere Wege.'],2,'Weniger Autos könnten die Innenstadt ruhiger machen. Ein vollständiges Verbot halte ich jedoch erst dann für sinnvoll, wenn Busse zuverlässig fahren und Menschen mit eingeschränkter Mobilität weiterhin ihre Ziele erreichen können.'],
 [6,'reading','Shartli qaror','Unter welcher Bedingung beginnt das Projekt?',['Wenn alle im Urlaub sind.','Sobald ein Raum gefunden ist.','Auch ohne Geld.','Wenn die Finanzierung bis Freitag bestätigt wird.'],3,'Das Team hat einen Raum gefunden und die Aufgaben verteilt. Der Start am Montag bleibt allerdings vorläufig: Nur wenn die Finanzierung bis Freitag bestätigt wird, kann das Projekt wie geplant beginnen.'],
];
export const germanPlacementQuestions: PlacementQuestion[] = rows.map(([month,skill,topic,prompt,options,answer,text], i) => ({id:`gp-${i+1}`,month,skill,topic,prompt,options,answer,text}));
export function assessGerman(answers: Record<string, number>) {
 const blocks = placementMonths.map((label,i) => {
  const questions = germanPlacementQuestions.filter(q=>q.month===i+1);
  const correct = questions.filter(q=>answers[q.id]===q.answer).length;
  const reading = questions.filter(q=>q.skill==='reading' && answers[q.id]===q.answer).length;
  const grammar = questions.filter(q=>q.skill==='grammar' && answers[q.id]===q.answer).length;
  return {month:i+1,label,correct,total:8,passed:correct>=6 && reading>=1 && grammar>=3};
 });
 // Never skip an unmastered prerequisite just because later guesses were right.
 const firstGap = blocks.findIndex(b=>!b.passed);
 const month = firstGap===-1 ? 6 : firstGap+1;
 const lesson = firstGap===-1 ? 70 : (month-1)*12+1;
 const skills = (['grammar','vocabulary','reading'] as const).map(skill=>({skill,total:germanPlacementQuestions.filter(q=>q.skill===skill).length,correct:germanPlacementQuestions.filter(q=>q.skill===skill&&answers[q.id]===q.answer).length}));
 return {blocks,skills,month,lesson,score:blocks.reduce((s,b)=>s+b.correct,0),allPassed:firstGap===-1,
  label:firstGap===-1?'B1 bilimlari: to‘rt ko‘nikma sinovi kerak':`${placementMonths[month-1]} bosqichidan boshlash`,
  gaps:germanPlacementQuestions.filter(q=>q.month<=month&&answers[q.id]!==q.answer).map(q=>q.topic)};
}
