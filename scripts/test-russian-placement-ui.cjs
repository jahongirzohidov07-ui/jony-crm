const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const bank = JSON.parse(fs.readFileSync('api/russian_placement_bank.json', 'utf8'));
function load(file, overrides = {}, globals = {}) {
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2023 },
  }).outputText;
  vm.runInNewContext(code, {
    module, exports: module.exports,
    require: id => Object.hasOwn(overrides, id) ? overrides[id] : require(id), ...globals,
  });
  return module.exports;
}
const lib = load('src/lib/russianPlacement.ts');
assert.equal(lib.placementStages.length, 6);
assert.equal(lib.oralRubric.length, 4);
assert.equal(lib.assessRussian, undefined, 'no client scorer');
const question = Object.fromEntries(Object.entries(bank[0]).filter(([k]) => k !== 'answer'));
const choices = load('src/components/PlacementChoices.tsx');
// 2026-10-22: savollar serverdan bittadan (useSeqPlacement), "Bilmayman"
// faqat savolda idk:true bo'lsa va oxirida; deploydan oldingi urinish
// (legacy) /questions bilan ishlaydi.
const identity = { full_name: 'QA Learner', phone: '901234567', branch_id: 1 };
const attemptId = '12345678-1234-1234-1234-123456789012';
function page(attempt, extra = {}, legacy = []) {
  let hook = 0;
  const hooks = { ...React, useState(initial) {
    const n = hook++;
    if (n === 0) return [legacy, () => {}];   // legacy questions
    return [typeof initial === 'function' ? initial() : initial, () => {}];
  } };
  const state = { attempt, setAttempt() {}, question: null, pick: undefined, setPick() {}, busy: false, stepError: '',
    stateBroken: false, start() {}, answer() {}, recover() {}, reset() {}, saving: false, saveError: '', retrySave() {},
    storageError: false, ...extra };
  const mod = load('src/pages/RussianPlacement.tsx', {
    react: hooks, '../assets/brand-icon.png': 'brand.png', '../lib/russianPlacement': lib,
    '../lib/placementSeq': { useSeqPlacement: () => state }, '../components/PlacementChoices': choices,
  });
  assert.equal(typeof mod.default, 'function');
  return renderToStaticMarkup(React.createElement(mod.default));
}
const seqAttempt = (more = {}) => ({ answers: {}, index: 0, started: true, done: false, mode: 'seq', state: 'S', identity, attemptId, ...more });
// 2026-10-22: bankda endi 5 ta variant; 5-sini taniladigan matn bilan almashtiramiz
const served = { ...question, options: [...question.options.slice(0, 4), 'пятый'], no: 1, total: 48, idk: true };
let html = page(seqAttempt(), { question: served, pick: -1 });
assert.equal((html.match(/type="radio"/g) || []).length, 6, 'five options + Bilmayman');
assert.ok(html.lastIndexOf('Bilmayman') > html.lastIndexOf('пятый'), 'Bilmayman stays last');
assert.match(html, /checked=""[^>]*\/><span[^>]*>\?<\/span><span lang="uz"[^>]*>Bilmayman/);
assert.match(html, /lang="ru"/);
assert.match(html, /og‘zaki tekshiruv/);
assert.doesNotMatch(html, /Oldingi/, 'server-timed questions only go forward');
assert.doesNotMatch(html, /DASTLABKI TAVSIYA/, 'no locally invented score');
html = page(seqAttempt(), { question: { ...served, idk: undefined } });
assert.equal((html.match(/type="radio"/g) || []).length, 5);
assert.doesNotMatch(html, />Bilmayman</, 'no idk flag -> no Bilmayman (old server)');
html = page({ ...seqAttempt(), mode: 'legacy', state: undefined, answers: { 'rp-1': -1 } }, {}, [question]);
// eski (legacy) sahifa: bankdagi hamma variant (endi 5 ta) + oxirida Bilmayman
assert.equal((html.match(/type="radio"/g) || []).length, question.options.length + 1);
assert.equal(question.options.length, 5);
assert.match(html, /Oldingi/);
assert.match(html, /checked=""[^>]*\/><span[^>]*>\?<\/span><span lang="uz"[^>]*>Bilmayman/);
const result = { score: 48, label: 'Yakuniy og‘zaki tekshiruv kerak', allPassed: true, idk: 2,
  month: null, lesson: null, recommendation: { branch_name: 'Chilonzor' }, blocks: [], gaps: [] };
const final = page(seqAttempt({ done: true, result }));
assert.match(final, /48\/48/, 'display uses server result, not local answers');
assert.match(final, /Chilonzor/);
assert.doesNotMatch(final, /null-oy|null-dars/);
assert.doesNotMatch(final, /Juda tez|Taxminan bosilgan/, 'taker never sees speed info');
assert.match(page(seqAttempt({ done: true }), { saveError: 'Natija saqlanmadi. Qayta yuboring.' }), /Qayta|tekshiruv/);
const guess = load('src/components/PlacementGuessStats.tsx', { 'lucide-react': { AlertTriangle: () => null } });
const results = load('src/components/RussianPlacementResults.tsx', {
  '../lib/api': { api: {} }, '../lib/russianPlacement': lib, './PlacementGuessStats': guess,
});
assert.equal(typeof results.default, 'function');
assert.match(renderToStaticMarkup(React.createElement(results.default)), /Rus tili testi natijalari/);
// Staff rows (2026-10-22): "Bilmayman: N · Juda tez: N" per skill + guess warning.
const staffRow = { idk: 3, fast: 20, guess_warning: true, skills: [{ skill: 'grammar', label: 'Grammatika', idk: 2, fast: 12 }] };
const staffHtml = renderToStaticMarkup(React.createElement(guess.GuessStats, { res: staffRow }));
assert.match(staffHtml, /Bilmayman: 3 · Juda tez: 20/);
assert.match(staffHtml, /Grammatika: Bilmayman: 2 · Juda tez: 12/);
assert.match(staffHtml, /Taxminan bosilgan bo(&#x27;|')lishi mumkin/);
assert.doesNotMatch(fs.readFileSync('src/lib/russianPlacement.ts', 'utf8'), /answer:\s*number|russian_placement_bank/);
console.log('PASS: default no-prop exports, server-served question with 5 options + last Bilmayman (-1) only with idk, legacy attempt, Russian language, server-only result without speed info, all-pass null handling, oral rubric');
