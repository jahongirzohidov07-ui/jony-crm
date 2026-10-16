const assert = require('node:assert/strict');
const fs = require('node:fs');
const { loadTs } = require('./export-german-teaching.cjs');
const teaching = loadTs('src/lib/germanTeaching.ts');
const course = loadTs('src/lib/german.ts');
const exported = JSON.parse(JSON.stringify(teaching.germanTeachingExport));
assert.equal(exported.exercises.length, 432);
assert.equal(new Set(exported.exercises.map(e => e.id)).size, 432);
for (const topic of course.germanGrammar) {
  const added = exported.exercises.filter(e => e.topicId === topic.id);
  assert.deepEqual(added.map(e => e.kind), ['production','correction','transfer']);
  assert.equal(new Set(added.map(e => e.prompt)).size, 3);
  for (const e of added) {
    assert.ok(e.model && e.guidance.length > 80 && e.criteria.length === 3, e.id);
    assert.ok(!topic.questions.some(q => q.prompt === e.prompt), e.id);
  }
}
const seeds = JSON.parse(fs.readFileSync('src/data/german/grammar-teaching.json','utf8'));
assert.equal(new Set(seeds.map(s => s.context)).size, 144);
assert.equal(new Set(seeds.map(s => s.transfer)).size, 144);
for (const s of seeds) assert.notEqual(s.error, s.model, s.topicId);
const allAssigned = [];
for (const kit of exported.lessons) {
  const sum = rows => rows.reduce((n, r) => n + r[0], 0);
  assert.equal(sum(kit.timeline), 120, `lesson ${kit.no}`);
  assert.equal(sum(kit.support), 60, `support ${kit.no}`);
  assert.equal(sum(kit.homework), 75);
  assert.equal(sum(kit.supportDayHomework), 75);
  const v = kit.vocabulary;
  assert.ok(v.activeIds.length >= 10 && v.activeIds.length <= 15);
  const dayIds = course.lessonWords(kit.no).map(w => w.id);
  assert.deepEqual([...v.activeIds, ...v.receptiveIds], Array.from(dayIds));
  allAssigned.push(...v.activeIds, ...v.receptiveIds);
  const pastActive = new Set(exported.lessons.filter(l => l.no < kit.no).flatMap(l => l.vocabulary.activeIds));
  assert.ok(v.reviewIds.every(id => pastActive.has(id)), `untaught review ${kit.no}`);
  assert.ok(kit.support[1][2].includes(`#${v.activeIds[0]}`));
  assert.equal(kit.audioPath, `/german/audio/lesson-${String(kit.no).padStart(3,'0')}.mp3`);
  assert.equal(kit.exercises.length, kit.topicIds.length * 3);
  if (kit.no >= 70) assert.deepEqual(kit.timeline, JSON.parse(JSON.stringify(course.finalWeekTimeline(kit.no))));
  if (kit.checkpoint) {
    const c = kit.checkpoint;
    assert.equal(c.readingQuestions.length, 3); assert.equal(c.listeningQuestions.length, 3);
    assert.equal(c.grammar.length, 4); assert.equal(c.vocabulary.length, 4);
    assert.equal(c.rubric.speaking.length, 3); assert.equal(c.rubric.writing.length, 3);
    assert.ok(c.readingQuestions.every(pair => pair[0] && pair[1]));
    assert.ok(c.listeningQuestions.every(pair => pair[0] && pair[1]));
    const pastTopics = new Set(course.germanLessons.filter(l => l.no < kit.no).flatMap(l => l.topicIds));
    assert.ok(c.grammar.every(e => pastTopics.has(e.topicId)));
    assert.ok(c.vocabulary.every(v => pastActive.has(v.id)));
    assert.ok(c.speakingModel && c.writingModel && c.retest);
    assert.ok(!course.germanSkills.some(s => s.reading.text === c.reading || s.listening.text === c.listening));
  }
}
for (const no of [61,64,67]) {
  const kit=exported.lessons[no-1];
  assert.ok(kit.officialPractice.material.includes('Prüfungstraining 1'));
  assert.ok(kit.timeline.some(r=>r[0]===({61:65,64:40,67:60})[no]));
  assert.ok(kit.support.some(r=>r[0]===20 && kit.topicIds.every(id=>r[2].includes(id))));
}
assert.equal(seeds[1].model, 'wir');
assert.ok(exported.exercises.find(e=>e.id==='g002-transfer').guidance.includes('fe’l va yangi gap talab qilmang'));
assert.deepEqual(allAssigned, Array.from(course.germanWords.map(w => w.id)));
assert.deepEqual(exported.lessons.filter(l => l.checkpoint).map(l => l.no), [12,24,36,48,60]);
assert.notDeepEqual(exported.lessons[1].timeline.map(r => r[0]), exported.lessons[2].timeline.map(r => r[0]));
assert.ok(exported.lessons[48].timeline.some(r => /erta tanishuv/.test(r[1])));
const source = fs.readFileSync('src/pages/GermanPlans.tsx','utf8');
assert.ok(source.includes('CourseLessonAudio course="german" lesson={no}'));
assert.ok(!source.includes('speechSynthesis'));
assert.ok(source.includes('?v=teaching-20261016'));
assert.ok(!source.includes('rows={mainTimeline}'));
assert.ok(source.includes('Mustaqil ish · 75'));
console.log('PASS: 144 topics / 432 new teacher-guided tasks; all 72 daily kits; 2400 vocabulary IDs retained; active-only review; 120/60/75/75 budgets; 5 new keyed checkpoints; final week preserved; audio and PDF links.');

for (const id of ['g005','g013','g017']) assert.ok(exported.exercises.find(e=>e.id===id+'-correction').guidance.includes('asl variantni grammatik xato deb baholamang'));
assert.equal(seeds.find(s=>s.topicId==='g016').model, 'Ich arbeite am Sonntag nicht.');
assert.ok(seeds.find(s=>s.topicId==='g043').transfer.includes('Präsens'));
assert.ok(seeds.find(s=>s.topicId==='g065').context.includes('Yaqinda boshlanadigan'));
