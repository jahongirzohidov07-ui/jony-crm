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
function page(answers = {}, done = false, result = null) {
  let hook = 0;
  const attempt = { answers, index: 0, done, identity: { full_name: 'QA Learner', phone: '901234567', branch_id: 1 }, attemptId: '12345678-1234-1234-1234-123456789012' };
  const hooks = { ...React, useState(initial) {
    const n = hook++;
    if (n === 1) return [[question], () => {}];
    // State order: attempt/questions/branches/name/phone/branch/loading/loadError/reload/storageError/result.
    if (n === 10) return [result, () => {}];
    return [typeof initial === 'function' ? initial() : initial, () => {}];
  } };
  const mod = load('src/pages/RussianPlacement.tsx', {
    react: hooks, '../assets/brand-icon.png': 'brand.png', '../lib/russianPlacement': lib,
  }, { sessionStorage: { getItem: () => JSON.stringify(attempt) } });
  assert.equal(typeof mod.default, 'function');
  return renderToStaticMarkup(React.createElement(mod.default));
}
const html = page({ 'rp-1': -1 });
assert.equal((html.match(/type="radio"/g) || []).length, 4);
assert.match(html, /aria-pressed="true"[^>]*>Bilmayman<\/button>/);
assert.ok(html.indexOf('Bilmayman</button>') > html.lastIndexOf('type="radio"'), 'fifth choice stays visible');
assert.match(html, /lang="ru"/);
assert.match(html, /og‘zaki tekshiruv/);
assert.doesNotMatch(html, /DASTLABKI TAVSIYA/, 'no locally invented score');
const result = { score: 48, label: 'Yakuniy og‘zaki tekshiruv kerak', allPassed: true,
  month: null, lesson: null, recommendation: { branch_name: 'Chilonzor' }, blocks: [], gaps: [] };
const final = page(Object.fromEntries(bank.map(q => [q.id, -1])), true, result);
assert.match(final, /48\/48/, 'display uses server result, not local answers');
assert.match(final, /Chilonzor/);
assert.doesNotMatch(final, /null-oy|null-dars/);
assert.match(page({}, true), /Qayta|tekshiruv/);
const results = load('src/components/RussianPlacementResults.tsx', {
  '../lib/api': { api: {} }, '../lib/russianPlacement': lib,
});
assert.equal(typeof results.default, 'function');
assert.match(renderToStaticMarkup(React.createElement(results.default)), /Rus tili testi natijalari/);
assert.doesNotMatch(fs.readFileSync('src/lib/russianPlacement.ts', 'utf8'), /answer:\s*number|russian_placement_bank/);
console.log('PASS: default no-prop exports, four choices + explicit -1 button, Russian language, server-only result, all-pass null handling, oral rubric');
