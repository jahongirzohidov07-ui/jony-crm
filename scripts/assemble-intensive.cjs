/** Assemble authored source packs; fail rather than publish gaps or duplicates. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const dir = path.join(root, 'src/data');
const read = name => JSON.parse(fs.readFileSync(path.join(dir, name), 'utf8').replace(/^\uFEFF/, ''));
const write = (name, data) => fs.writeFileSync(path.join(dir, name), JSON.stringify(data, null, 2) + '\n');
const normalize = s => s.normalize('NFKC').toLowerCase().replace(/[’‘]/g, "'").trim();
const base = read('intensive-vocabulary.json').slice(0, 500);
const vocabulary = [...base];
const seen = new Set(base.map(w => normalize(w.word)));
const problems = [];
for (let month = 2; month <= 8; month++) {
  const name = `intensive/words-month${month}.json`;
  if (!fs.existsSync(path.join(dir, name))) { problems.push(`${name}: missing`); continue; }
  const entries = read(name);
  if (entries.length !== 500) problems.push(`${name}: ${entries.length}/500 words`);
  for (const w of entries) {
    const key = normalize(w.word);
    if (seen.has(key)) problems.push(`${name}: duplicate ${w.word}`);
    seen.add(key);
    for (const field of ['word', 'ipa', 'meaning', 'example', 'translation', 'topic']) {
      assert.equal(typeof w[field], 'string', `${name}: ${w.word}/${field}`);
      assert.ok(w[field].trim(), `${name}: ${w.word}/${field} empty`);
      assert.ok(!w[field].includes('\uFFFD'), `${name}: broken encoding`);
    }
    assert.match(w.ipa, /^\/.+\/$/, `${w.word}: IPA slashes`);
    vocabulary.push({ id: vocabulary.length + 1, ...w });
  }
}
const skills = [];
for (const [from, to] of [[1,48],[49,96],[97,144],[145,168],[169,192]]) {
  const name = `intensive/skills-${from}-${to}.json`;
  if (!fs.existsSync(path.join(dir, name))) { problems.push(`${name}: missing`); continue; }
  const packs = read(name);
  if (packs.length !== to - from + 1) problems.push(`${name}: ${packs.length}/${to-from+1} lessons`);
  packs.forEach((pack, i) => {
    assert.equal(pack.lesson, from + i, `${name}: lesson order`);
    for (const mode of ['reading', 'listening']) {
      assert.ok(pack[mode].text.length >= 100, `${pack.lesson}: empty ${mode}`);
      assert.equal(pack[mode].questions.length, 3, `${pack.lesson}: ${mode} question count`);
      for (const q of pack[mode].questions) {
        assert.ok(q.prompt && q.explanation && q.answers.length && q.answers.every(a => a.trim()));
      }
    }
    for (const mode of ['speaking', 'writing']) {
      assert.ok(pack[mode].prompt && pack[mode].success.length >= 3);
    }
    assert.ok(pack.writing.model && pack.teacherNote && pack.objective && pack.level);
  });
  skills.push(...packs);
}
const grammarMap = read('intensive-grammar-map.json');
const grammarExercises = {};
for (const name of ['intensive/grammar-1-3.json', 'intensive/grammar-4-15.json', 'intensive/grammar-16-21.json', 'intensive/grammar-22-27.json']) {
  if (!fs.existsSync(path.join(dir, name))) { problems.push(`${name}: missing`); continue; }
  for (const [id, questions] of Object.entries(read(name))) {
    assert.ok(!grammarExercises[id], `Repeated topic ${id}`);
    assert.equal(questions.length, 2, `${id} must have two authored questions`);
    questions.forEach(q => assert.ok(q.prompt && q.explanation && q.answers.length && q.answers.every(a => a.trim())));
    grammarExercises[id] = questions;
  }
}
const topicIds = grammarMap.flatMap((m,mi) => m.items.map((_,ti) => `${mi+1}.${ti+1}`));
for (const id of topicIds) if (!grammarExercises[id]) problems.push(`Missing authored grammar questions: ${id}`);
if (problems.length) {
  console.error(problems.join('\n'));
  process.exitCode = 1;
} else {
  assert.equal(vocabulary.length, 4000);
  assert.equal(seen.size, 4000);
  assert.equal(skills.length, 192);
  assert.equal(new Set(skills.flatMap(p => [p.reading.text, p.listening.text])).size, 384, 'Repeated skill text');
  write('intensive-vocabulary.json', vocabulary);
  write('intensive-skills.json', skills);
  write('intensive-topic-exercises.json', grammarExercises);
  console.log('Assembled 4000 unique vocabulary entries, 192 skill packs and 822 authored grammar questions.');
}
