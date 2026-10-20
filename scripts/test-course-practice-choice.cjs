const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const storage = new Map();
let blocked = false;
function load(file, imports = {}) {
  const exports = {};
  const code = ts.transpileModule(fs.readFileSync(path.join(root, file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2023 },
  }).outputText;
  vm.runInNewContext(code, { exports, require: name => imports[name] || require(name), localStorage: {
    getItem(key) { if (blocked) throw Error('blocked'); return storage.get(key); },
    setItem(key, value) { if (blocked) throw Error('blocked'); storage.set(key, value); },
  } });
  return exports;
}
const extended = load('src/lib/coursePracticeVariants.ts');
const audited = JSON.parse(fs.readFileSync(path.join(root, 'src/data/course-practice-audited-prompts.json'), 'utf8'));
const lib = load('src/lib/coursePracticeChoice.ts', { '../lib/coursePracticeVariants': extended, './coursePracticeVariants': extended, '../data/course-practice-audited-prompts.json': audited });
const read = file => JSON.parse(fs.readFileSync(path.join(root, file), 'utf8'));
const bank = read('api/student_course_practice_data.json');
const questions = language => bank[language].flatMap(lesson => lesson.sections.flatMap(section => section.questions.map(question => ({ question, lesson: lesson.lesson }))));
const supported = ['en', 'de'].flatMap(language => questions(language).flatMap(row => {
  const family = lib.getPracticeFamily(row.question, language, row.lesson);
  return family ? [{ ...row, family, language }] : [];
}));
test('actual exported EN and DE questions map by target, prompt, language and lesson', () => {
  assert.ok(supported.length >= 9);
  assert.deepEqual([...new Set(supported.map(r => r.family.id))].sort(), Array.from(lib.practiceFamilies, f => f.id).sort());
  for (const { question, language, lesson, family } of supported) {
    assert.equal(lib.getPracticeFamily({ id: question.id, prompt: question.prompt }, language, lesson).id, family.id);
    assert.equal(lib.getPracticeFamily({ ...question, prompt: question.prompt + ' Explain why.' }, language, lesson), undefined);
    assert.equal(lib.getPracticeFamily(question, language === 'en' ? 'de' : 'en', lesson), undefined);
    assert.equal(lib.getPracticeFamily(question, language, lesson + 1), undefined);
    assert.equal(lib.getPracticeFamily({ ...question, id: 'unknown' }, language, lesson), undefined);
  }
});
test('no broad family conversion for umlauts, person nouns, negation, production or unknown prompts', () => {
  for (const language of ['en', 'de']) {
    const cases = questions(language).filter(({question: q}) => language === 'de'
      ? /g001-q[23]$|g004-q|g003-production$/.test(q.id)
      : q.id.endsWith('grammar:1.1:1'));
    assert.ok(cases.length);
    cases.forEach(({ question, lesson }) => assert.equal(lib.getPracticeFamily(question, language, lesson), undefined));
  }
  assert.equal(lib.getPracticeFamily({id:'ru:1:g001-q1', prompt:'Otni yozing'}, 'ru', 1), undefined);
});
test('all three themes change actual exercise content; local keys never disclose canonical keys', () => {
  for (const { question, family } of supported) {
    assert.equal(new Set(Object.values(family.variants).map(v => v.prompt)).size, 3);
    for (const exercise of Object.values(family.variants)) {
      assert.notEqual(exercise.prompt, question.prompt);
      assert.ok(exercise.scaffold && exercise.explanation);
      assert.ok(lib.checkPracticeAnswer(exercise, exercise.answer));
      assert.ok(lib.checkPracticeAnswer(exercise, ` ${exercise.answer} `));
      assert.equal(lib.checkPracticeAnswer(exercise, 'wrong'), false);
      assert.equal(lib.checkPracticeAnswer(exercise, exercise.answer + ' extra'), false);
      // Grammatical forms may coincide; privacy means never consulting the graded key.
      assert.ok(exercise.prompt && exercise.explanation);
    }
  }
});
test('validated local explanations, German capitalization and sein person agreement', () => {
  const expected = {
    'en-noun': ['cup', 'stadium', 'sensor'], 'en-adjective': ['warm', 'fast', 'shiny'],
    'en-verb': ['cook', 'kick', 'lift'], 'de-capital-noun': ['Tasse', 'Ball', 'Roboter'], 'de-sein': ['bin', 'bin', 'bin'],
  };
  for (const family of lib.practiceFamilies) {
    if (expected[family.id]) assert.deepEqual(Array.from(Object.values(family.variants), v => v.answer), expected[family.id]);
    for (const v of Object.values(family.variants)) {
      assert.ok(v.explanation.toLowerCase().includes(v.answer.toLowerCase()));
      if (family.id === 'de-capital-noun') assert.equal(lib.checkPracticeAnswer(v, v.answer.toLowerCase()), false);
      if (family.id === 'de-sein') {
        assert.match(v.prompt, /^Ich ___/);
        for (const wrong of ['bist', 'ist', 'sind', 'seid']) assert.equal(lib.checkPracticeAnswer(v, wrong), false);
      }
    }
  }
});
test('mapping never reads original expected, answers, hint or explanation', () => {
  const {question, language, lesson} = supported[0];
  const publicQ = {id:question.id, prompt:question.prompt};
  for (const key of ['expected', 'answers', 'hint', 'explanation']) Object.defineProperty(publicQ, key, {get(){ throw Error('canonical leak'); }});
  assert.ok(lib.getPracticeFamily(Object.freeze(publicQ), language, lesson));
});
test('theme preference is language/topic scoped, validated, and survives unavailable storage', () => {
  const [a, b] = lib.practiceFamilies;
  storage.clear();
  lib.savePracticeTheme(a, 'football');
  assert.equal(lib.readPracticeTheme(a), 'football');
  assert.equal(lib.readPracticeTheme(b), 'everyday');
  assert.match(lib.practiceThemeKey(a), /:en:en-noun$/);
  assert.match(lib.practiceThemeKey(lib.practiceFamilies[3]), /:de:/);
  storage.set(lib.practiceThemeKey(a), 'corrupt');
  assert.equal(lib.readPracticeTheme(a), 'everyday');
  blocked = true;
  assert.doesNotThrow(() => lib.savePracticeTheme(a, 'robots'));
  assert.equal(lib.readPracticeTheme(a), 'everyday');
  blocked = false; storage.clear();
});
function nodes(element, type) {
  if (!element || typeof element !== 'object') return [];
  if (Array.isArray(element)) return element.flatMap(e => nodes(e, type));
  return [...(element.type === type ? [element] : []), ...nodes(element.props?.children, type)];
}
function text(element) {
  if (element == null || typeof element === 'boolean') return '';
  if (Array.isArray(element)) return element.map(text).join('');
  if (typeof element !== 'object') return String(element);
  return text(element.props?.children);
}
function harness(row = supported[0]) {
  let states = [], cursor = 0;
  const ref = {current: {focus(){ ref.focused = true; }}};
  const Component = load('src/components/CoursePracticeChoice.tsx', {
    '../lib/coursePracticeChoice': lib,
    react: {useId: () => 'practice-test', useRef: () => ref, useState: initial => {
      const index = cursor++;
      if (!(index in states)) states[index] = typeof initial === 'function' ? initial() : initial;
      return [states[index], value => { states[index] = value; }];
    }},
  }).default;
  const props = {question: {id:row.question.id, prompt:row.question.prompt}, language:row.language, lesson:row.lesson};
  const render = () => { cursor = 0; const child = Component(props); return child.type(child.props); };
  const click = name => { const b = nodes(render(), 'button').find(b => text(b) === name); assert.ok(b, name); b.props.onClick(); };
  return {render, click, Component, props, ref};
}
test('native accessible controls, optional collapsed start, no graded callback and reset identity', () => {
  const h = harness(); const tree = h.render();
  const toggle = nodes(tree, 'button')[0];
  assert.equal(toggle.props['aria-expanded'], false);
  assert.ok(nodes(tree, 'div').find(n => n.props.id === toggle.props['aria-controls']).props.hidden);
  assert.match(text(tree), /Bu tayyorlov mashqi\. Natija kunlik reja va tangalarga qo‘shilmaydi\./);
  assert.doesNotMatch(text(tree), /mastery|XP/);
  assert.match(text(tree), /Asosiy savolga darhol o‘tishingiz mumkin\./);
  assert.ok(nodes(tree, 'button').every(b => b.props.type === 'button' && text(b)));
  assert.equal(nodes(tree, 'legend').length, 2);
  const input = nodes(tree, 'input')[0];
  assert.ok(nodes(tree, 'label').some(l => l.props.htmlFor === input.props.id));
  assert.ok(input.props['aria-describedby']);
  const fallback = h.Component({...h.props, language:'ru'});
  assert.equal(typeof fallback.type, 'function');
  assert.notEqual(h.Component(h.props).key, h.Component({...h.props, question:{...h.props.question, id:h.props.question.id.replace(':1:', ':2:')}, lesson:2})?.key);
});
test('challenge hides scaffold; help reveals it; themes replace exercise and reset answer/result', () => {
  const h = harness();
  h.click('Avval mavzuli mashq qilib ko‘rish (ixtiyoriy)');
  assert.ok(!text(h.render()).includes('Faqat shu qo‘shimcha mashq uchun yordam:'));
  h.click('Tayanch bilan');
  assert.match(text(h.render()), /Faqat shu qo‘shimcha mashq uchun yordam:/);
  h.click('Mustaqil sinov');
  assert.ok(!text(h.render()).includes('Faqat shu qo‘shimcha mashq uchun yordam:'));
  const exercise = supported[0].family.variants.everyday;
  nodes(h.render(), 'input')[0].props.onChange({target:{value:exercise.answer}});
  h.click('Mashq javobini tekshirish');
  assert.match(text(h.render()), /Qo‘shimcha mashq to‘g‘ri/);
  h.click('Futbol');
  assert.equal(nodes(h.render(), 'input')[0].props.value, '');
  assert.ok(!text(h.render()).includes('Qo‘shimcha mashq to‘g‘ri'));
  assert.ok(text(h.render()).includes(supported[0].family.variants.football.prompt));
  h.click('Robotlar');
  assert.ok(text(h.render()).includes(supported[0].family.variants.robots.prompt));
  nodes(h.render(), 'input')[0].props.onChange({target:{value:supported[0].family.variants.robots.answer}});
  h.click('Mashq javobini tekshirish');
  h.click('Mashqni yig‘ish va asosiy savolga o‘tish');
  assert.equal(nodes(h.render(), 'button')[0].props['aria-expanded'], false);
  assert.equal(h.ref.focused, true);
});



test('every audited topic entry exists in the exported bank and only public fields are shipped', () => {
  for (const rule of audited) {
    assert.deepEqual(Object.keys(rule).sort(), ['family', 'language', 'prompts', 'topic']);
    assert.ok(lib.practiceFamilies.some(f => f.id === rule.family && f.language === rule.language));
    for (const [index, prompt] of Object.entries(rule.prompts)) {
      const suffix = rule.language === 'en' ? `grammar:${rule.topic}:${index}` : `${rule.topic}-${index}`;
      const matches = questions(rule.language).filter(row => row.question.id.endsWith(':' + suffix));
      assert.ok(matches.length, suffix);
      for (const {question, lesson} of matches) {
        assert.equal(question.prompt, prompt, `bank drift: ${question.id}`);
        assert.equal(lib.getPracticeFamily(question, rule.language, lesson).id, rule.family);
        const publicQ = {id: question.id, prompt: question.prompt};
        for (const key of ['expected','answers','hint','explanation']) Object.defineProperty(publicQ, key, {get(){throw Error('canonical key accessed');}});
        assert.equal(lib.getPracticeFamily(publicQ, rule.language, lesson).id, rule.family);
      }
    }
  }
});
test('prompt-specific exclusions do not convert helper-only, infinitive, meaning or conjunction questions', () => {
  for (const [language, suffix] of [
    ['en','grammar:7.1:4'], ['en','grammar:18.4:5'], ['en','grammar:15.1:5'],
    ['de','g033-q2'], ['de','g036-q3'], ['de','g127-q2'], ['de','g089-q1'], ['de','g090-q2'],
  ]) {
    const matches = questions(language).filter(row => row.question.id.endsWith(':' + suffix));
    assert.ok(matches.length, suffix);
    for (const {question,lesson} of matches) assert.equal(lib.getPracticeFamily(question,language,lesson),undefined,question.id);
  }
});
test('later-course local checks reject incorrect tense, modality, spelling and German word order', () => {
  const wrong = {
    'en-present-base': 'packs', 'en-present-third': 'carrys', 'en-present-continuous': 'making',
    'en-past-regular': 'wash', 'en-past-irregular': 'breaked', 'en-modal-bare': 'to cook',
    'en-should': 'should to drink', 'en-zero': 'will beep', 'en-first': 'would relax', 'en-second': 'will plant',
    'de-present': 'kauft', 'de-v2': 'ich kaufe Brot', 'de-can': 'könne', 'de-must': 'müsst',
    'de-past-sein': 'bin', 'de-past-regular': 'koche', 'de-wuerde': 'werde', 'de-conditional': 'hat',
    'de-verb-final': 'ich habe Hunger',
  };
  for (const [id, answer] of Object.entries(wrong)) {
    const family = lib.practiceFamilies.find(f => f.id === id);
    assert.ok(family, id);
    assert.equal(lib.checkPracticeAnswer(family.variants.everyday, answer), false, id);
  }
});
test('unsupported question offers optional study strategies without fake themes or answer hints', () => {
  const row = questions('de').find(r => r.question.id.endsWith(':g001-q2'));
  const h = harness({...row, language:'de'});
  const tree = h.render();
  assert.equal(tree.type, 'details');
  assert.equal(tree.props.open, undefined);
  assert.match(text(tree), /tekshirilgan mavzuli variant yo‘q/);
  assert.doesNotMatch(text(tree), /Futbol|Robotlar|mastery|XP/);
  assert.equal(nodes(tree, 'input').length, 0);
  assert.match(text(tree), /bitta so‘z, bo‘shliqdagi qism yoki butun gap/);
  h.click('Javobni tekshirish rejasi');
  assert.match(text(h.render()), /Bu usul javobning to‘g‘riligini baholamaydi/);
  assert.equal(nodes(h.render(),'button')[1].props['aria-pressed'], true);
  h.click('Topshiriqni ajratish');
  assert.equal(nodes(h.render(),'button')[0].props['aria-pressed'], true);
});
test('bounded coverage report across actual grammar questions, not universal coverage', t => {
  for (const language of ['en','de']) {
    const all = bank[language].flatMap(l => l.sections.filter(s => s.skill === 'grammar').flatMap(s => s.questions));
    const rows = supported.filter(r => r.language === language);
    const prompts = new Set(rows.map(r => r.question.prompt));
    const lessons = new Set(rows.map(r => r.lesson));
    const families = new Set(rows.map(r => r.family.id));
    assert.equal(prompts.size, language === 'en' ? 69 : 27);
    assert.ok(rows.length < all.length);
    t.diagnostic(`${language}: ${rows.length}/${all.length} grammar question placements; ${prompts.size} distinct public prompts; ${families.size} families; ${lessons.size}/${bank[language].length} lessons; lesson range ${Math.min(...lessons)}–${Math.max(...lessons)}`);
  }
  assert.equal(lib.practiceFamilies.length, 24);
  t.diagnostic(`${lib.practiceFamilies.length * 3} curated supplemental theme exercises`);
});
