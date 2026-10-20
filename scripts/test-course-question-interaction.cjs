const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
function load(relative, imports = {}) {
  const exports = {};
  const code = ts.transpileModule(fs.readFileSync(path.join(root, relative), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2023 },
  }).outputText;
  vm.runInNewContext(code, { exports, require: name => imports[name] || require(name) });
  return exports;
}
const lib = load('src/lib/courseQuestionInteraction.ts');
const values = question => Array.from(lib.getCourseQuestionChoices(question), c => c.value);
const question = (prompt, extra = {}) => ({ id: 'q1', mode: 'exact', prompt, ...extra });
test('observed lesson prompts yield only their literal choices', () => {
  assert.deepEqual(values(question('Tanlang: The children ___ in the pool. (swim / happy)')), ['swim', 'happy']);
  assert.deepEqual(values(question('Harakat fe’lini yozing: chair / dance / red.')), ['chair', 'dance', 'red']);
  assert.deepEqual(values(question('chair / dance / red')), ['chair', 'dance', 'red']);
  assert.deepEqual(values(question('Tanlang: ot / fe’l.')), ['ot', 'fe’l']);
});
test('actual foundation and topic bank prompts are supported deterministically', () => {
  for (const [file, snippet, expected] of [
    ['intensive-exercises-foundation', '(swim / happy)', ['swim', 'happy']],
    ['intensive-topic-exercises', 'chair / dance / red', ['chair', 'dance', 'red']],
  ]) {
    const bank = JSON.parse(fs.readFileSync(path.join(root, `src/data/${file}.json`), 'utf8'));
    const source = Object.values(bank).flat().find(item => item.prompt.includes(snippet));
    assert.ok(source, `fixture exists: ${snippet}`);
    const publicQuestion = Object.freeze(question(source.prompt));
    assert.deepEqual(values(publicQuestion), expected);
    assert.deepEqual(values(publicQuestion), expected);
  }
});
test('labelled choices submit the letter and explicit options take priority', () => {
  assert.deepEqual(values(question('Choose:\nA) swim\nB) happy')), ['A', 'B']);
  assert.deepEqual(values(question('Choose: A. swim B. happy')), ['A', 'B']);
  assert.deepEqual(values(question('chair / dance / red', { options: ['A) red', 'B) blue'] })), ['A', 'B']);
  assert.deepEqual(values(question('(swim / happy)', { options: ['Yes, I can.', 'No, I cannot.'] })), ['Yes, I can.', 'No, I cannot.']);
});
test('ambiguous slash notation and nonlists remain free writing', () => {
  for (const prompt of [
    '20/10/2026', '20 / 10 / 2026', '1 / 2', 'https://example.com/path',
    'he/she', 'and / or', '(he / she)', '(subject / verb)', '(singular / plural)',
    'Grammar: S / V / O', 'V1 / V2', 'Write am/is/are', 'Compare reading / writing in two sentences.',
    '(swim / happy) and (red / blue)', 'Choose (red / blue). Explain why.',
    'Go to https://school.test: red / blue', 'red / red', 'A) red\nC) blue',
    'Word building: a / b / c / d / e / f / g',
  ]) assert.deepEqual(values(question(prompt)), [], prompt);
});
test('self, partial labels, duplicate options and empty explicit lists stay as writing', () => {
  for (const options of [[], ['red'], ['red', 'red'], ['A) red', 'blue'], ['A) red', 'C) blue'], ['', 'blue']]) {
    assert.deepEqual(values(question('(swim / happy)', { options })), []);
  }
  assert.deepEqual(values(question('(swim / happy)', { mode: 'self' })), []);
  assert.deepEqual(values(question('Select all that apply', { mode: 'self', options: ['red', 'blue'] })), []);
});
test('selection matches only literal submitted values and never reads answer keys', () => {
  const q = question('(swim / happy)');
  Object.defineProperty(q, 'expected', { get() { throw Error('answer leak'); } });
  Object.defineProperty(q, 'answers', { get() { throw Error('answer leak'); } });
  const choices = lib.getCourseQuestionChoices(q);
  assert.equal(lib.selectedCourseChoice(choices, 'swim'), 0);
  for (const draft of ['Swim', ' swim ', 'My own\nanswer', '']) assert.equal(lib.selectedCourseChoice(choices, draft), -1);
});
// Inspect real React elements and invoke handlers with a controlled parent value.
// Native radio inputs supply browser Tab/arrow/Space behavior, without custom key traps.
let instance = 0;
const Component = load('src/components/CourseQuestionInput.tsx', {
  react: { useId: () => `test-${++instance}` },
  '../lib/courseQuestionInteraction': lib,
}).default;
function nodes(element, type) {
  if (!element || typeof element !== 'object') return [];
  const children = [element.props?.children].flat(Infinity);
  return [...(element.type === type ? [element] : []), ...children.flatMap(child => nodes(child, type))];
}
test('card selection changes the answer; editing and question changes preserve drafts', () => {
  let value = 'My original\nwriting';
  const q = question('Choose', { options: ['A) red', 'B) blue'] });
  const render = (extra = {}) => Component({ question: q, value, onChange: next => { value = next; }, ...extra });
  let tree = render();
  assert.equal(nodes(tree, 'textarea')[0].props.value, value);
  assert.ok(nodes(tree, 'input').every(input => !input.props.checked));
  nodes(tree, 'input')[1].props.onChange();
  assert.equal(value, 'B');
  tree = render();
  assert.deepEqual(nodes(tree, 'input').map(input => input.props.checked), [false, true]);
  nodes(tree, 'textarea')[0].props.onChange({ target: { value: 'B, because\nI think so.' } });
  tree = render();
  assert.ok(nodes(tree, 'input').every(input => !input.props.checked));
  assert.equal(nodes(tree, 'textarea')[0].props.value, 'B, because\nI think so.');
  tree = render({ question: question('Write freely', { id: 'q2', mode: 'self' }) });
  assert.equal(nodes(tree, 'input').length, 0);
  assert.equal(nodes(tree, 'textarea')[0].props.value, value);
});
test('accessible native groups, unique names, labels, and disabled handlers', () => {
  const props = { question: question('(swim / happy)'), value: '', onChange() { throw Error('disabled change'); }, disabled: true, 'aria-label': '3-savol javobi' };
  const tree = Component(props);
  const radios = nodes(tree, 'input');
  assert.equal(nodes(tree, 'fieldset').length, 1);
  assert.equal(nodes(tree, 'legend').length, 1);
  assert.ok(radios.every(r => r.props.type === 'radio' && r.props.disabled && r.props.name === radios[0].props.name));
  assert.notEqual(nodes(Component(props), 'input')[0].props.name, radios[0].props.name);
  radios.forEach(r => r.props.onChange());
  const textarea = nodes(tree, 'textarea')[0];
  assert.equal(textarea.props.maxLength, 6000);
  assert.equal(textarea.props['aria-label'], '3-savol javobi');
  assert.ok(textarea.props.disabled);
  assert.ok(nodes(tree, 'label').some(label => label.props.htmlFor === textarea.props.id));
  textarea.props.onChange({ target: { value: 'ignored' } });
});
const orderingQuestion = question('Voqealar qaysi tartibda yuz berdi?', { mode: 'self', options: ['A. Start', 'B. Middle', 'C. End'] });
test('ordering requires explicit self ordering wording and sequential letter options', () => {
  assert.equal(lib.getCourseQuestionOrdering(orderingQuestion).length, 3);
  assert.equal(lib.getCourseQuestionOrdering({ ...orderingQuestion, prompt: 'Voqealar tartibini yozing.' }).length, 3);
  for (const overrides of [
    { mode: 'exact' }, { prompt: 'Choose any matching events' }, { options: undefined },
    { options: ['Start', 'Middle', 'End'] }, { options: ['A. Start', 'C. End'] },
    { options: ['A. Start'] },
  ]) assert.equal(lib.getCourseQuestionOrdering({ ...orderingQuestion, ...overrides }).length, 0);
});
test('lesson 2 public sequence task enables ordering without reading teacher answers', () => {
  const bank = JSON.parse(fs.readFileSync(path.join(root, 'src/data/intensive-skills-extension.json'), 'utf8'));
  const lesson = bank.lessons.find(item => item.lesson === 2);
  assert.ok(lesson);
  const task = lesson.reading.tasks.find(item => item.type === 'sequence');
  assert.ok(task);
  const publicQuestion = Object.freeze({ id: task.id, prompt: task.prompt, mode: 'self', options: task.options });
  assert.deepEqual(Array.from(lib.getCourseQuestionOrdering(publicQuestion), choice => choice.value), ['A', 'B', 'C']);
});
test('ordered selection serializes letters, removes, undoes, resets, and protects arbitrary drafts', () => {
  const choices = lib.getCourseQuestionOrdering(orderingQuestion);
  let value = '';
  for (const letter of ['B', 'A', 'C']) value = lib.changeCourseQuestionOrder(choices, value, { type: 'toggle', value: letter });
  assert.equal(value, 'B, A, C');
  assert.equal(lib.changeCourseQuestionOrder(choices, value, { type: 'toggle', value: 'A' }), 'B, C');
  assert.equal(lib.changeCourseQuestionOrder(choices, value, { type: 'undo' }), 'B, A');
  assert.equal(lib.changeCourseQuestionOrder(choices, value, { type: 'reset' }), '');
  assert.equal(lib.changeCourseQuestionOrder(choices, value, { type: 'toggle', value: 'D' }), value);
  for (const draft of ['My written explanation', 'A, A', 'B, D', 'B A C', '']) {
    assert.equal(lib.parseCourseQuestionOrder(choices, draft).length, 0);
    assert.equal(lib.changeCourseQuestionOrder(choices, draft, { type: 'undo' }), draft);
  }
  assert.deepEqual(Array.from(lib.parseCourseQuestionOrder(choices, 'B,A, C')), ['B', 'A', 'C']);
});
test('ordering cards update controlled drafts and expose accessible selection state', () => {
  let value = '';
  const render = (extra = {}) => Component({ question: orderingQuestion, value, onChange: next => { value = next; }, ...extra });
  nodes(render(), 'button')[1].props.onClick();
  nodes(render(), 'button')[0].props.onClick();
  nodes(render(), 'button')[2].props.onClick();
  assert.equal(value, 'B, A, C');
  assert.ok(nodes(render(), 'button').slice(0, 3).every(button => button.props['aria-pressed']));
  assert.match(nodes(render(), 'button')[1].props['aria-label'], /1-o‘rinda/);
  nodes(render(), 'button')[0].props.onClick();
  assert.equal(value, 'B, C');
  nodes(render(), 'button')[3].props.onClick();
  assert.equal(value, 'B');
  nodes(render(), 'textarea')[0].props.onChange({ target: { value: 'My explanation\nB then A' } });
  assert.equal(nodes(render(), 'textarea')[0].props.value, value);
  nodes(render({ disabled: true }), 'button').forEach(button => button.props.onClick());
  assert.equal(value, 'My explanation\nB then A');
  nodes(render(), 'button')[4].props.onClick();
  assert.equal(value, '');
});
test('multi-blank, multi-answer, word-order and grammar hints never become radios', () => {
  for (const prompt of [
    'Gapni tartiblang: English / study / We.',
    'So‘zlarni odatiy tartibda joylang: a / Italian / beautiful / old / painting.',
    'Ikki bo‘shliqni vergul bilan to‘ldiring: I saw ___ dog. ___ dog was brown. (a / the)',
    'Ikki javobni vergul bilan yozing: ___ Monday; ___ three days. (for / since)',
    'Complete: ___ dog and ___ cat. (a / the)',
    'Future Perfect inkor shaklini yozing: By Monday, the paint ___ completely. (not / dry)',
  ]) {
    assert.deepEqual(values(question(prompt)), [], prompt);
    assert.deepEqual(values(question(prompt, { options: ['a', 'the'] })), [], prompt);
  }
});
test('explicit word order serializes spaces and keeps repeated token occurrences', () => {
  const words = lib.getCourseWordOrder(question('Gapni tartiblang: English / study / We.'));
  assert.equal(words.length, 3);
  let value = '';
  for (const id of ['2', '1', '0']) value = lib.changeCourseWordOrder(words, value, { type: 'toggle', value: id });
  assert.equal(value, 'We study English');
  assert.equal(lib.changeCourseWordOrder(words, value, { type: 'undo' }), 'We study');
  assert.equal(lib.changeCourseWordOrder(words, value, { type: 'toggle', value: '1' }), 'We English');
  assert.equal(lib.changeCourseWordOrder(words, value, { type: 'reset' }), '');
  const repeated = lib.getCourseWordOrder(question('Gapni tartiblang: we / think / we / can.'));
  for (const id of ['0', '1', '2', '3']) {
    if (id === '0') value = '';
    value = lib.changeCourseWordOrder(repeated, value, { type: 'toggle', value: id });
  }
  assert.equal(value, 'we think we can');
  assert.equal(lib.parseCourseWordOrder(repeated, value).length, 4);
  assert.equal(lib.parseCourseWordOrder(repeated, 'we we we').length, 0);
  assert.equal(lib.getCourseWordOrder(question('Consider: English / study / We.')).length, 0);
});
test('word-order cards remain editable and serialize token text instead of IDs', () => {
  let value = '';
  const render = () => Component({ question: question('Gapni tartiblang: English / study / We.'), value, onChange: next => { value = next; } });
  for (const index of [2, 1, 0]) nodes(render(), 'button')[index].props.onClick();
  assert.equal(value, 'We study English');
  assert.equal(nodes(render(), 'input').length, 0);
  nodes(render(), 'textarea')[0].props.onChange({ target: { value: 'My freely edited sentence.' } });
  assert.equal(nodes(render(), 'textarea')[0].props.value, 'My freely edited sentence.');
  assert.ok(nodes(render(), 'button').slice(0, 3).every(button => !button.props['aria-pressed']));
});
test('every converted question in the freshly generated bank has a compatible accepted answer', () => {
  // Run the real exporter without writing its server-only output to disk.
  // Answer keys exist only in this test; the parser receives a public projection.
  let bank;
  const exporter = path.join(root, 'scripts/export-student-course-practice.cjs');
  vm.runInNewContext(fs.readFileSync(exporter, 'utf8'), {
    __dirname: path.dirname(exporter),
    console: { log() {} },
    require: name => name === 'node:fs' ? { ...fs, writeFileSync(file, content) {
      assert.equal(path.resolve(file), path.join(root, 'api/student_course_practice_data.json'));
      bank = JSON.parse(content);
    } } : require(name),
  });
  assert.ok(bank);
  const normalize = (value, sensitive) => {
    const normalized = value.normalize('NFKC').replace(/[’‘`]/gu, "'").replace(/[.!?,;:]/gu, '').trim().replace(/\s+/gu, ' ');
    return sensitive ? normalized : normalized.toLowerCase().replace(/ß/gu, 'ss');
  };
  const failures = [];
  let checked = 0, choicesCount = 0, wordsCount = 0;
  for (const lessons of Object.values(bank)) for (const lesson of lessons) for (const section of lesson.sections) for (const q of section.questions) {
    checked++;
    const publicQuestion = { id: q.id, prompt: q.prompt, mode: q.mode, ...(q.options !== undefined ? { options: q.options } : {}) };
    const choices = lib.getCourseQuestionChoices(publicQuestion);
    if (choices.length) {
      choicesCount++;
      if (!choices.some(c => q.expected.some(answer => normalize(answer, q.caseSensitive) === normalize(c.value, q.caseSensitive)))) failures.push(`${q.id}: ${q.prompt}`);
    }
    const words = lib.getCourseWordOrder(publicQuestion);
    if (words.length) {
      wordsCount++;
      const signature = text => normalize(text, q.caseSensitive).split(' ').sort().join('|');
      if (!q.expected.some(answer => signature(answer) === signature(words.map(word => word.label).join(' ')))) failures.push(`word-order ${q.id}: ${q.prompt}`);
    }
  }
  assert.ok(checked > 10000);
  assert.ok(choicesCount > 1000);
  assert.ok(wordsCount > 0);
  assert.deepEqual(failures, []);
  console.log(`Bank audit: ${checked} questions, ${choicesCount} choice inputs, ${wordsCount} word-order inputs, ${failures.length} incompatible conversions.`);
});
