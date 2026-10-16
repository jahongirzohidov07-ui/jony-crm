/* Execute the real TypeScript module in memory: no generated files or project build side effects. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const sourceFiles = [1, 2, 3, 4].flatMap(n => ['part-', 'teacher-ru-'].map(prefix => path.join(root, `src/data/russian/${prefix}${n}.json`)));
const hashes = () => sourceFiles.map(file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'));
const before = hashes();
const cache = new Map();
function load(file) {
  if (!path.extname(file)) file += '.ts';
  if (cache.has(file)) return cache.get(file).exports;
  const module = { exports: {} };
  cache.set(file, module);
  const text = fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, '');
  if (file.endsWith('.json')) module.exports = JSON.parse(text);
  else {
    const result = ts.transpileModule(text, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2023, esModuleInterop: true }, reportDiagnostics: true, fileName: file });
    assert.equal((result.diagnostics ?? []).filter(d => d.category === ts.DiagnosticCategory.Error).length, 0);
    const run = vm.runInThisContext(`(function(require,module,exports){${result.outputText}\n})`, { filename: file });
    run(specifier => {
      assert.ok(specifier.startsWith('.'), `Unexpected runtime dependency: ${specifier}`);
      return load(path.resolve(path.dirname(file), specifier));
    }, module, module.exports);
  }
  return module.exports;
}
const entry = path.join(root, 'src/lib/russianTeaching.ts');
const { russianLessonKind: kind, russianLessonPlan: plan, russianScaffoldedPractice: practice } = load(entry);
const { russianTeacherLessons: lessons } = load(path.join(root, 'src/lib/russianTeacher.ts'));
function freeze(value) { if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); } }
freeze(lessons);
const clean = text => text.normalize('NFC').replace(/\u0301/g, '');
const allIds = new Set();
const counts = { normal: 0, review: 0, monthly: 0, final: 0 };
for (let n = 1; n <= 144; n++) {
  const expected = n === 144 ? 'final' : n % 12 === 0 ? 'monthly' : n % 3 === 0 ? 'review' : 'normal';
  assert.equal(kind(n), expected);
  counts[expected]++;
  for (const size of [1, 8, 12, 16, 17, 33]) {
    const p = plan(n, size);
    assert.equal(p.kind, expected);
    assert.equal(p.timeline.reduce((sum, s) => sum + s.minutes, 0), 120, `Duration lesson ${n}`);
    assert.ok(p.timeline.every(s => Number.isInteger(s.minutes) && s.minutes > 0 && s.title && s.instruction));
    assert.ok(p.label.includes(lessons[n - 1].title));
    assert.ok(p.preparation.some(s => s.includes(lessons[n - 1].grammar.title)));
    assert.ok(p.preparation.some(s => s.includes(lessons[n - 1].roleplay.a)));
    if (expected === 'final' || expected === 'monthly') {
      const capacity = expected === 'final' ? 8 : 16;
      const perStudent = expected === 'final' ? 10 : 5;
      const schedule = p.preparation.find(s => s.startsWith('Один преподаватель:'));
      assert.ok(schedule.includes(`${perStudent} минут на ученика`));
      assert.ok(schedule.includes(`вместимость ${capacity} учеников`));
      assert.ok(schedule.includes(`сегодня оцениваются ${Math.min(size, capacity)}`));
      assert.ok(schedule.includes(`дополнительные сессии по 80 минут: ${Math.ceil(Math.max(0, size - capacity) / capacity)}`));
      assert.ok(p.assessment.join(' ').includes(expected === 'final' ? '40/60' : '14/20'));
    }
  }
  const p = plan(n);
  const listening = p.timeline.find(s => /аудирование|Аудирование|Слушание|Общая работа/.test(s.title));
  assert.ok(listening, `Missing listening ${n}`);
  if (n % 12 === 11) {
    assert.equal(listening.minutes, 25);
    assert.ok(listening.instruction.includes('задание на общий смысл'));
    assert.ok(listening.instruction.includes('вопросы на детали и ответы из этого блока'));
    assert.ok(!listening.instruction.includes(lessons[n - 1].questions[0].prompt));
  } else assert.ok(listening.instruction.includes(`/russian/audio/lesson-${n}.mp3`));
  const result = practice(n);
  assert.deepEqual(result, practice(n), 'Deterministic output');
  assert.equal(result.controlled.length, 11);
  assert.equal(result.controlled.filter(q => q.prompt.startsWith('Грамматика')).length, 7);
  assert.equal(result.controlled.filter(q => q.prompt.startsWith('Фразы')).length, 4);
  assert.equal(new Set(result.controlled.map(q => q.prompt)).size, 11);
  assert.equal(result.mixed.length, 6);
  assert.equal(new Set(result.mixed.map(q => q.prompt)).size, 6);
  for (const q of [...result.controlled, ...result.mixed]) {
    assert.ok(!allIds.has(q.id), `Duplicate id ${q.id}`); allIds.add(q.id);
    assert.ok(q.answers.length && q.answers.every(a => typeof a === 'string' && a.trim()));
    assert.ok(q.explanation && q.hint && !q.prompt.includes('undefined'));
  }
  result.mixed.forEach(q => {
    const source = Number(q.id.match(/source-(\d+)$/)[1]);
    assert.ok(n === 1 ? source === 1 : source >= 1 && source < n, `Future leakage ${q.id}`);
    assert.ok(q.hint.includes(`Источник: урок ${source}`));
    const original = practiceSource(source).find(item => q.prompt.endsWith(item.prompt));
    assert.ok(original, `Mixed content must come from claimed source ${q.id}`);
    assert.deepEqual(q.answers, original.answers);
  });
  // Check actual gap restoration, including last-token and whole-word boundaries.
  const models = lessons[n - 1].grammar.examples.map(e => clean(e.ru));
  const pairs = [
    [result.controlled[4], models[1]], [result.controlled[5], models[0]], [result.controlled[6], models[1]],
    [result.controlled[7], clean(lessons[n - 1].phrases[2].ru)],
    [result.controlled[9], clean(lessons[n - 1].phrases[4].ru)],
  ];
  for (const [q, original] of pairs) {
    const restored = q.prompt.replace('_____', q.answers[0]);
    assert.ok(restored.includes(original), `Gap does not restore full model: ${q.id}`);
  }
  assert.equal(result.production.length, 3);
  result.production.forEach(q => {
    assert.ok(q.prompt && q.sample && q.criteria.length >= 3);
    assert.ok(!('answers' in q), 'Open production must not be automatically marked against a fixed answer');
  });
  assert.ok(result.production[0].prompt.includes(lessons[n - 1].roleplay.a));
  assert.ok(result.production[1].prompt.includes(lessons[n - 1].roleplay.b));
  assert.ok(result.production[2].prompt.includes(lessons[n - 1].roleplay.twist));
}
function practiceSource(n) { return practice(n).controlled; }
for (const n of [0, -1, 145, 1.5, NaN, Infinity]) {
  assert.throws(() => kind(n), RangeError);
  assert.throws(() => plan(n), RangeError);
  assert.throws(() => practice(n), RangeError);
}
for (const size of [0, -1, 2.5, NaN, Infinity]) assert.throws(() => plan(12, size), RangeError);
assert.deepEqual(counts, { normal: 96, review: 36, monthly: 11, final: 1 });
assert.deepEqual(hashes(), before, 'Canonical JSON must remain unchanged');
// Real type-check of the entry and imported modules, without build caches or emitted files.
const program = ts.createProgram([entry], { noEmit: true, target: ts.ScriptTarget.ES2023, module: ts.ModuleKind.ESNext, moduleResolution: ts.ModuleResolutionKind.Bundler, resolveJsonModule: true, esModuleInterop: true, skipLibCheck: true, types: [], noUnusedLocals: true, noUnusedParameters: true });
const diagnostics = ts.getPreEmitDiagnostics(program);
assert.equal(diagnostics.length, 0, ts.formatDiagnosticsWithColorAndContext(diagnostics, { getCanonicalFileName: f => f, getCurrentDirectory: () => root, getNewLine: () => '\n' }));
console.log('OK: 144 lessons, four 120-minute plans, 11 controlled + 6 mixed + 3 manual speaking tasks, audio routing, exam capacity, source integrity and TypeScript.');
