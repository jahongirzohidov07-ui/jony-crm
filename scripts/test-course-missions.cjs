const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const { renderToStaticMarkup } = require('react-dom/server');
const root = path.resolve(__dirname, '..');
const cache = new Map();
function load(file) {
  const source = path.resolve(root, file);
  if (cache.has(source)) return cache.get(source);
  const exports = {};
  cache.set(source, exports);
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(source, 'utf8'), {compilerOptions: {module: ts.ModuleKind.CommonJS, esModuleInterop: true, target: ts.ScriptTarget.ES2023, jsx: ts.JsxEmit.ReactJSX}}).outputText, {
    exports, require: name => {
      if (!name.startsWith('.')) return require(name);
      const resolved = path.resolve(path.dirname(source), name);
      if (resolved.endsWith('.json')) return require(resolved);
      return load(resolved + (fs.existsSync(resolved + '.ts') ? '.ts' : '.tsx'));
    },
  }, {filename: source});
  return exports;
}
const {getCourseMission} = load('src/lib/courseMissions.ts');
const {CourseJourney} = load('src/components/CourseJourney.tsx');
const {weekModules, lessonPlan} = load('src/lib/intensive.ts');
const data = require('../src/data/course-weekly-missions.json');
const enGrammar = require('../src/data/intensive-grammar-map.json');
const deLessons = require('../src/data/german/lessons.json');
const deGrammar = require('../src/data/german/grammar.json');
const plain = value => JSON.parse(JSON.stringify(value));

test('every EN192 and DE72 lesson resolves to its own week-end portfolio mission', () => {
  for (const [language, weeks, perWeek] of [['en',32,6], ['de',24,3]]) {
    assert.equal(data[language].length, weeks);
    for (let lesson = 1; lesson <= weeks * perWeek; lesson++) {
      const m = getCourseMission(language, lesson), week = Math.ceil(lesson / perWeek);
      assert.equal(m.week, week); assert.equal(m.lesson, week * perWeek);
      assert.equal(m.id, `${language}:${week * perWeek}:weekly-${week}`);
      assert.equal(m.language, language);
    }
    assert.equal(getCourseMission(language, weeks * perWeek + 1), null);
    assert.equal(new Set(data[language].map(m => m.title)).size, weeks);
    assert.equal(new Set(data[language].map(m => m.output)).size, weeks);
    assert.equal(new Set(data[language].map(m => m.criteria.join('|'))).size, weeks);
  }
});

test('unsupported languages and invalid lesson numbers do not leak another curriculum', () => {
  for (const language of ['ru','ko','EN','', 'constructor','__proto__']) assert.equal(getCourseMission(language, 1), null);
  for (const lesson of [0,-1,1.5,NaN,Infinity,'6',null]) assert.equal(getCourseMission('en', lesson), null);
});

test('authored curriculum anchors match actual EN weeks including all five spiral reviews', () => {
  for (const m of data.en) {
    const plan = lessonPlan(m.lesson);
    assert.deepEqual(m.curriculum.moduleIds, plain(weekModules[m.week - 1]));
    assert.deepEqual(m.curriculum.moduleIds, plain(plan.moduleIds));
    assert.deepEqual(m.curriculum.titles, plain(plan.moduleIds.map(i => enGrammar[i].title)));
    assert.ok(m.prompt.length > 30 && m.output.length > 10 && m.criteria.length >= 2);
    assert.ok(!('completed' in m) && !('mastery' in m));
  }
  assert.match(data.en[0].prompt, /To‘liq gap shart emas/);
  assert.match(data.en[31].criteria.join(' '), /Future Perfect/);
});

test('DE missions pin all actual weekly lessons and topic IDs; final week is evidence review', () => {
  const allIds = new Set(deGrammar.map(t => t.id));
  for (const m of data.de) {
    const lessons = deLessons.filter(l => l.week === m.week);
    assert.equal(lessons.at(-1).no, m.lesson);
    assert.deepEqual(m.curriculum.titles, lessons.map(l => l.title));
    assert.deepEqual(m.curriculum.topicIds, [...new Set(lessons.flatMap(l => l.topicIds))]);
    assert.ok(m.curriculum.topicIds.every(id => allIds.has(id)));
    assert.ok(m.prompt.length > 30 && m.output.length > 10 && m.criteria.length >= 2);
  }
  for (const skill of ['Lesen','Hören','Sprechen','Schreiben']) assert.ok(data.de[23].prompt.includes(skill));
  assert.match(data.de[23].criteria.join(' '), /sertifikati deb belgilamang/);
});

function nodes(value) {
  if (Array.isArray(value)) return value.flatMap(nodes);
  if (!value || typeof value !== 'object') return [];
  return [value, ...nodes(value.props?.children)];
}
const base = {language:'en', lessons:[], selected:null, checkpoints:[], onSelect:()=>{}, onCheckpoint:()=>{}};
test('journey leads with mission, keeps full grammar titles and callbacks, opens active month', () => {
  const lessons = Array.from({length:192}, (_,i) => ({lesson:i+1,title:`Original grammar ${i+1}`,question_count:2}));
  const calls = [];
  const tree = CourseJourney({...base, lessons, selected:7, onMission:n=>calls.push(['mission',n]), onSelect:n=>calls.push(['lesson',n]), onCheckpoint:n=>calls.push(['checkpoint',n])});
  const all = nodes(tree);
  const buttons = all.filter(n => n.type === 'button');
  buttons.find(n => n.props.children === 'Ishimni portfolioga yozish →').props.onClick();
  buttons.find(n => n.props['aria-current'] === 'step').props.onClick();
  buttons.filter(n => nodes(n).some(c => c.props?.children === 'Shartlarini ko‘rish →'))[0].props.onClick();
  assert.deepEqual(calls, [['mission',6],['lesson',7],['checkpoint',1]]);
  const html = renderToStaticMarkup(tree);
  assert.equal((html.match(/Ishimni portfolioga yozish/g)||[]).length,32);
  for (const lesson of lessons) assert.ok(html.includes(lesson.title));
  assert.ok(html.indexOf('Tanishuv kartam') < html.indexOf('Original grammar 1'));
  assert.ok(!html.includes('line-clamp'));
  assert.ok(all.some(n => n.type === 'details' && n.props.open));
});

test('sparse shuffled lesson lists preserve week numbers, callback fallback is honest', () => {
  const lessons = [12,7,3].map(lesson=>({lesson,title:`Grammar ${lesson}`,question_count:1}));
  const tree = CourseJourney({...base, language:'de', lessons, selected:7});
  const html = renderToStaticMarkup(tree);
  for (const week of [1,3,4]) assert.ok(html.includes(data.de[week-1].title));
  assert.ok(!html.includes(data.de[1].title));
  assert.ok(!html.includes('Ishimni portfolioga yozish →'));
  assert.ok(html.includes('«Ijodiy ishlarim»'));
  assert.deepEqual(lessons.map(l=>l.lesson), [12,7,3]);
  const empty = renderToStaticMarkup(CourseJourney(base));
  assert.ok(!empty.includes('Ishimni portfolioga yozish'));
});


test('API deployment artifact is byte-for-byte canonical and exporter keeps it bundled', () => {
  assert.equal(fs.readFileSync(path.join(root, 'api/course_weekly_missions.json'), 'utf8'), fs.readFileSync(path.join(root, 'src/data/course-weekly-missions.json'), 'utf8'));
  assert.match(fs.readFileSync(path.join(root, 'scripts/export-student-course-practice.cjs'), 'utf8'), /fs\.copyFileSync.*course-weekly-missions\.json.*course_weekly_missions\.json/);
});
