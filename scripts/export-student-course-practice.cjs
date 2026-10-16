// Deterministic server-only bank. Never import this output into the client.
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const read = name => JSON.parse(fs.readFileSync(path.join(root, 'src/data', name + '.json'), 'utf8'));
const extension = read('intensive-skills-extension');
const enSkills = read('intensive-skills');
const deSkills = read('german/skills');
const deLessons = read('german/lessons');
const deGrammar = read('german/grammar');
const deTeaching = read('german/grammar-teaching');
const modules = read('intensive-grammar-map');
const enExercises = {};
for (const source of ['intensive-topic-exercises', 'intensive-exercises-foundation', 'intensive-exercises-advanced']) {
  for (const [id, qs] of Object.entries(read(source))) enExercises[id] = [...(enExercises[id] || []), ...qs];
}
const exact = (id, q, caseSensitive = false) => ({
  id, prompt: q.prompt, mode: 'exact', expected: q.answers,
  explanation: q.explanation || '', caseSensitive: q.caseSensitive ?? caseSensitive,
});
const self = (id, prompt, model, criteria = [], explanation = '') => ({
  id, prompt, mode: 'self', expected: model ? [model] : [], criteria, explanation,
});
const task = (prefix, q) => ({
  ...self(prefix + q.id, q.prompt, q.teacher.answer, q.teacher.evidence, q.teacher.guidance),
  ...(q.options?.length ? { options: q.options } : {}),
  ...(q.options?.includes(q.teacher.answer) ? {mode: "exact"} : {}),
});
function skillSections(language, no, pack) {
  const prefix = language + ':' + no + ':';
  return ['reading', 'listening', 'speaking', 'writing'].map(skill => {
    const source = pack[skill];
    const section = {id: skill, title: source.title || skill, skill, questions: []};
    if (skill === 'reading') section.text = source.text;
    if (skill === 'listening') section.transcript = source.text;
    if (source.questions) section.questions = source.questions.map((q, i) => exact(prefix + skill + ':' + (q.id || i + 1), q));
    else section.questions = [self(prefix + skill, source.prompt || source.task, source.model, source.success || source.criteria)];
    return section;
  });
}
const en = enSkills.map(pack => {
  const no = pack.lesson, prefix = 'en:' + no + ':';
  const sections = skillSections('en', no, pack);
  const extra = extension.lessons.find(row => row.lesson === no);
  if (!extra) throw Error('Missing English extension: ' + no);
  for (const skill of ['reading', 'listening']) {
    sections.find(s => s.id === skill).questions.push(...extra[skill].tasks.map(q => task(prefix, q)));
  }
  const week = Math.ceil(no / 6), day = (no - 1) % 6 + 1;
  const indices = week <= 27 ? [week - 1] : [[0,1,2,3,4,5,6,7],[8,9,10,11,12],[13,14,15,16,17,18],[19,20,21,22,23],[24,25,26]][week - 28];
  const topics = indices.flatMap(mi => modules[mi].items.map((item, ti) => ({id: (mi+1)+'.'+(ti+1), title: item[0]})));
  const assigned = day === 6 ? topics : topics.slice(Math.floor((day-1)*topics.length/5), Math.floor(day*topics.length/5));
  sections.push({id:'grammar', title:'Grammar', skill:'grammar', questions: assigned.flatMap(t => (enExercises[t.id] || []).map((q,i) => exact(prefix+'grammar:'+t.id+':'+i,q)))});
  const homework = extension.homework.find(row => row.afterLesson === no);
  if (homework) sections.push({id:'homework',title:'Week '+homework.week+' · '+homework.title,skill:'reading',text:homework.text,questions:homework.tasks.map(q => task(prefix,q))});
  return {language:'en',lesson:no,title:assigned.map(t=>t.title).join(' · ') || pack.reading.title,level:pack.level,audio_url:'/intensive/audio/lesson-'+String(no).padStart(3,'0')+'.mp3',sections};
});
const de = deLessons.map(lesson => {
  const no = lesson.no, prefix = 'de:'+no+':';
  const pack = deSkills.find(row => row.no === no);
  const sections = skillSections('de', no, pack);
  const questions = [];
  for (const id of lesson.topicIds) {
    const topic = deGrammar.find(t=>t.id === id), seed = deTeaching.find(t=>t.topicId === id);
    if (!topic || !seed) throw Error('Missing German topic '+id);
    questions.push(...topic.questions.map(q=>exact(prefix+q.id,q,true)));
    const criteria = ['Vaziyat va topshiriq mazmuni bajarilgan.', 'Maqsad shakli to‘g‘ri ishlatilgan.', 'Ma’no tushunarli; javob sababi izohlangan.'];
    const rewrite = ['g005','g013','g017'].includes(id);
    questions.push(
      self(prefix+id+'-production',seed.context,seed.model,criteria,topic.rule),
      self(prefix+id+'-correction',rewrite
        ? '«'+seed.error+'» intonatsion savolini fe’l birinchi o‘rindagi neytral ha/yo‘q savoliga qayta yozing. Asl gapni noto‘g‘ri deb belgilamang.'
        : 'Vaziyat: '+seed.context+' «'+seed.error+'» gapini vaziyatga moslab tuzating va sababini tushuntiring.',seed.model,criteria,topic.rule),
      self(prefix+id+'-transfer',seed.transfer,'Tayanch tuzilma: '+seed.model,criteria,(id==='g002'?'Kalit: ich; wir; Sie. ':'')+topic.rule)
    );
  }
  sections.push({id:'grammar',title:'Grammatik',skill:'grammar',questions});
  return {language:'de',lesson:no,title:lesson.title,level:lesson.level,audio_url:'/german/audio/lesson-'+String(no).padStart(3,'0')+'.mp3',sections};
});
for (const [language, lessons, count] of [['en',en,192],['de',de,72]]) {
  if (lessons.length !== count || new Set(lessons.map(l=>l.lesson)).size !== count) throw Error('Invalid lesson coverage '+language);
  for (const lesson of lessons) {
    const qs = lesson.sections.flatMap(s=>s.questions);
    if (new Set(qs.map(q=>q.id)).size !== qs.length) throw Error('Duplicate ids '+language+lesson.lesson);
    for (const q of qs) if (!q.prompt || (q.mode==='exact' && !q.expected?.length)) throw Error('Invalid question '+q.id);
  }
}
const output = {en,de};
fs.writeFileSync(path.join(root,'api/student_course_practice_data.json'),JSON.stringify(output));
for (const [language,lessons] of Object.entries(output)) console.log(language+': '+lessons.length+' lessons, '+lessons.flatMap(l=>l.sections.flatMap(s=>s.questions)).length+' questions');
