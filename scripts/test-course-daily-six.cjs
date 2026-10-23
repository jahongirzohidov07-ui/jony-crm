const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'src/components/CourseDailySix.tsx'), 'utf8');
const deferred = () => {let resolve, reject; const promise = new Promise((a,b) => {resolve=a;reject=b;}); return {promise,resolve,reject};};
const tick = async () => {await Promise.resolve(); await Promise.resolve();};
function harness() {
  let slots=[], cursor=0, effects=[], pending=[], day='2026-10-23', reads=[], writes=[], draft=new Map(), listeners={};
  class ApiError extends Error {constructor(message,status) {super(message);this.status=status;}}
  const react={useState(initial) {const i=cursor++; if (!(i in slots)) slots[i]=typeof initial==='function'?initial():initial;return [slots[i],v=>{slots[i]=typeof v==='function'?v(slots[i]):v;}];},useRef(initial) {const i=cursor++;return slots[i]??(slots[i]={current:initial});},useEffect(fn,deps) {const i=cursor++;const prior=effects[i];if(!prior||deps.some((v,j)=>v!==prior.deps[j]))pending.push(()=>{prior?.cleanup?.();effects[i]={deps,cleanup:fn()};});}};
  const window={setInterval:()=>1,addEventListener:(k,fn)=>listeners[k]=fn,removeEventListener:()=>{},speechSynthesis:{cancel(){}}};
  const document={visibilityState:'visible',addEventListener:(k,fn)=>listeners[k]=fn,removeEventListener(){}};
  const api={fresh(url) {const d=deferred();reads.push({url,...d});return d.promise;},post(url,body) {const d=deferred();writes.push({url,body,...d});return d.promise;}};
  const exports={};
  const imports={'react':react,'react/jsx-runtime':{jsx:(type,props)=>({type,props}),jsxs:(type,props)=>({type,props}),Fragment:'fragment'},'react-router-dom':{Link:'a'},'../lib/api':{api,ApiError},'../lib/studentWritingDrafts':{readWritingDraft:(k,id)=>({text:draft.get(k+id)||''}),saveWritingDraft:(k,id,v)=>draft.set(k+id,v.text),removeWritingDraft:(k,id)=>draft.delete(k+id)},'../lib/courseQuestionInteraction':{getCourseQuestionChoices:q=>(q.options||[]).map(value=>({label:value,value}))}};
  const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2022}}).outputText;
  vm.runInNewContext(code,{exports,require:name=>imports[name]||require(name),window,document,Error,Intl:{DateTimeFormat:class {format(){return day;}}},Date,setTimeout:()=>1,clearTimeout(){},clearInterval(){}});
  return {exports,reads,writes,draft,window,ApiError,listeners,setDay(v){day=v;},render(Component=exports.default,props={language:'en',onExit(){}}) {cursor=0; const tree=Component(props);pending.splice(0).forEach(fn=>fn());return tree;},unmount(){effects.forEach(e=>e?.cleanup?.());},reset(){effects.forEach(e=>e?.cleanup?.());slots=[];effects=[];pending=[];}};
}
function nodes(tree,predicate) {if(!tree||typeof tree!=='object')return [];const children=[tree.props?.children].flat(Infinity);return [...(predicate(tree)?[tree]:[]),...children.flatMap(child=>nodes(child,predicate))];}
const text = tree => typeof tree==='string'||typeof tree==='number'?String(tree):tree&&typeof tree==='object'?[tree.props?.children].flat(Infinity).map(text).join(' '):'';
const find = (tree,label) => nodes(tree,n=>n.type==='button'&&text(n).includes(label))[0];
const children = tree => nodes(tree,n=>typeof n.type==='function'&&n.props.question);
function plan(extra={}) {return {id:'daily-six:2026-10-23',student_id:7,day:'2026-10-23',language:'en',lesson:1,title:'Test',completed_steps:0,total_steps:6,completed:false,awarded:false,answers:{},skills:['vocabulary','grammar','reading','listening','writing','speaking'].map(skill=>({skill,target:1,completed_count:0,completed:false,questions:[{id:skill,prompt:'Test '+skill,mode:skill==='speaking'?'audio':skill==='writing'?'writing':'exact'}],...(skill==='listening'?{audio_url:'/intensive/audio/lesson-001.mp3'}:{})})),...extra};}
async function loaded(h,p=plan()) {h.render();h.reads[0].resolve(p);await tick();return h.render();}
test('API progress and first unfinished skill; a filled answer never proves completion',async()=>{const h=harness(),p=plan();p.skills[0].completed=true;p.skills[0].completed_count=1;p.completed_steps=1;let tree=await loaded(h,p);assert.equal(children(tree)[0].props.question.id,'grammar');assert.equal(nodes(tree,n=>n.type==='progress')[0].props.value,1);assert.equal(h.exports.dailySixAccepted(p,'grammar'),false);find(tree,'Gapiriş').props.onClick();tree=h.render();assert.equal(children(tree)[0].props.question.id,'speaking');assert.equal(find(tree,'Gapiriş').props['aria-pressed'],true);});
test('submissions use frozen returned language/day and wait for authoritative response without auto advance',async()=>{const h=harness(),p=plan({language:'de'});let tree=await loaded(h,p);const child=children(tree)[0];const saving=child.props.onSubmit(child.props.question,'gut',false);assert.equal(h.writes[0].body.language,'de');assert.equal(h.writes[0].body.day,p.day);assert.equal(h.writes[0].body.correct,undefined);tree=h.render();assert.equal(children(tree)[0].props.busy,true);h.writes[0].resolve({correct:false,explanation:'Try again',reward:{xp:0,coins:0},plan:{...p,answers:{vocabulary:{answer:'gut',feedback:{correct:false,explanation:'Try again'}}}}});await saving;tree=h.render();assert.equal(children(tree)[0].props.question.id,'vocabulary');assert.equal(nodes(tree,n=>n.type==='progress')[0].props.value,0);});
test('double submit is locked and provider failure preserves progress for retry',async()=>{const h=harness();const tree=await loaded(h);const child=children(tree)[0];const first=child.props.onSubmit(child.props.question,'a',false);await child.props.onSubmit(child.props.question,'b',false);assert.equal(h.writes.length,1);h.writes[0].reject(new h.ApiError('AI unavailable',503));await first;const after=h.render();assert.match(text(after),/AI unavailable/);assert.equal(children(after)[0].props.busy,false);assert.equal(nodes(after,n=>n.type==='progress')[0].props.value,0);});
test('unmount and midnight invalidate outstanding requests; stale completion cannot replace new day',async()=>{const h=harness();const tree=await loaded(h);const child=children(tree)[0];const saving=child.props.onSubmit(child.props.question,'a',false);h.setDay('2026-10-24');h.listeners.focus();h.render();h.writes[0].resolve({reward:{xp:5,coins:1},plan:plan({completed:true,awarded:true,completed_steps:6})});await saving;const after=h.render();assert.equal(children(after).length,0);assert.doesNotMatch(text(after),/Bugungi \+1 tanga berildi/);h.unmount();h.reads[1].resolve(plan());await tick();});
test('409 refreshes authoritative plan without retrying old-day answer',async()=>{const h=harness();const tree=await loaded(h);const child=children(tree)[0];const saving=child.props.onSubmit(child.props.question,'a',false);h.writes[0].reject(new h.ApiError('day changed',409));await saving;h.render();assert.equal(h.reads.length,2);assert.equal(h.writes.length,1);});
test('load failure offers a real retry',async()=>{const h=harness();h.render();h.reads[0].reject(new Error('offline'));await tick();const tree=h.render();find(tree,'Qayta yuklaş').props.onClick();h.render();assert.equal(h.reads.length,2);});
test('draft survives skill unmount and accepted saved answer wins over obsolete draft',async()=>{const h=harness();const p=plan();let tree=await loaded(h,p);const child=children(tree)[0];h.reset();tree=h.render(child.type,child.props);nodes(tree,n=>n.type==='textarea')[0].props.onChange({target:{value:'my draft'}});h.reset();tree=h.render(child.type,child.props);assert.equal(nodes(tree,n=>n.type==='textarea')[0].props.value,'my draft');h.reset();p.answers.vocabulary={answer:'verified',feedback:{correct:true,explanation:'yes'}};tree=h.render(child.type,{...child.props,plan:p});assert.equal(nodes(tree,n=>n.type==='textarea')[0].props.value,'verified');assert.equal(find(tree,'Tekşiriş'),undefined);});
test('speaking is microphone-only with native recognition language, transcript semantics, and caught constructor failures',async()=>{const h=harness();let tree=await loaded(h,plan({language:'de'}));find(tree,'Gapiriş').props.onClick();tree=h.render();const child=children(tree)[0];h.reset();let rec;h.window.SpeechRecognition=class {constructor(){rec=this;}start(){}stop(){}abort(){}};tree=h.render(child.type,child.props);assert.equal(nodes(tree,n=>n.type==='textarea'||n.type==='input').length,0);assert.equal(find(tree,'Savolni tinglaş'),undefined);find(tree,'Mikrofonga').props.onClick();assert.equal(rec.lang,'de-DE');rec.onresult({results:[{isFinal:true,0:{transcript:'Ich bin hier.'}}]});rec.onend();tree=h.render(child.type,child.props);assert.match(text(tree),/Ich bin hier/);assert.match(text(tree),/talaffuz baholanmaydi/);h.reset();h.window.SpeechRecognition=class {constructor(){throw Error('unsupported');}};tree=h.render(child.type,child.props);assert.doesNotThrow(()=>find(tree,'Mikrofonga').props.onClick());assert.match(text(h.render(child.type,child.props)),/Mikrofonni işga tuşirib bölmadi/);});
test('reward update classification includes daily-six; old short session remains and route/card launch real view',()=>{const events=fs.readFileSync(path.join(root,'src/lib/rewardPracticeEvents.ts'),'utf8');const out={};vm.runInNewContext(ts.transpileModule(events,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:out});assert.equal(out.isRewardPracticeWrite('/student/course-practice/daily-six/answer?x=1'),true);assert.equal(out.isRewardPracticeWrite('/student/course-practice/daily-six'),false);const route=fs.readFileSync(path.join(root,'src/pages/student/StudentCoursePractice.tsx'),'utf8');assert.match(route,/if \(view === "daily-six"\) return <CourseDailySix/);assert.match(route,/if \(view === "session"\) return <CourseDailySession/);const card=fs.readFileSync(path.join(root,'src/components/CourseMotivation.tsx'),'utf8');assert.match(card,/view=daily-six/);assert.match(card,/Kunlik 6 qadam/);assert.match(card,/Ustoz coinlari alohida/);});

test('draft keys isolate accounts, days and languages',()=>{const h=harness(),p=plan();const key=h.exports.dailySixDraftKey(p);assert.notEqual(key,h.exports.dailySixDraftKey({...p,student_id:8}));assert.notEqual(key,h.exports.dailySixDraftKey({...p,day:'2026-10-24'}));assert.notEqual(key,h.exports.dailySixDraftKey({...p,language:'de'}));});
test('demo completion never promises a pending coin',async()=>{const h=harness();const tree=await loaded(h,plan({completed:true,completed_steps:6,reward_eligible:false,reward_note:'Demo mode: no coin'}));assert.match(text(tree),/Demo mode: no coin/);assert.doesNotMatch(text(tree),/Tanga hali tasdiqlanmagan/);});

// Render the real Course closure obtained through StudentCoursePractice's public
// wrapper. Only its children, network, and router are mocked; hook slots survive
// URL changes, as they do for navigation within the same mounted route.
function courseRouteHarness(language) {
  let params = new URLSearchParams('view=daily-six&reward_source=daily-six:2026-10-23');
  const slots = [], effects = [], reads = [];
  let cursor = 0, pending = [], dirty = false;
  const react = {
    useState(initial) {
      const i = cursor++;
      if (!(i in slots)) {
        const slot = {value: typeof initial === 'function' ? initial() : initial};
        slot.set = value => {
          const next = typeof value === 'function' ? value(slot.value) : value;
          if (!Object.is(next, slot.value)) {slot.value = next; dirty = true;}
        };
        slots[i] = slot;
      }
      return [slots[i].value, slots[i].set];
    },
    useRef(initial) {const i = cursor++; return slots[i] ?? (slots[i] = {current: initial});},
    useEffect(fn, deps) {
      const i = cursor++, prior = effects[i];
      if (!prior || deps.some((value, index) => !Object.is(value, prior.deps[index]))) {
        pending.push(() => {prior?.cleanup?.(); effects[i] = {deps, cleanup: fn()};});
      }
    },
  };
  const DailySix = () => null, ShortSession = () => null, Motivation = () => null;
  const unused = () => null;
  const imports = {
    react,
    'react/jsx-runtime': {jsx: (type, props) => ({type, props}), jsxs: (type, props) => ({type, props})},
    'react-router-dom': {Link: 'a', useSearchParams: () => [params, next => {params = new URLSearchParams(next);}]},
    'lucide-react': {ArrowLeft: unused, BookOpen: unused},
    '../../lib/lang': {useLearningLanguage: () => language},
    '../../lib/api': {api: {fresh: url => {reads.push(url); return new Promise(() => {});}, post: () => Promise.resolve({})}},
    '../../components/CourseDailySix': {__esModule: true, default: DailySix},
    '../../components/CourseDailySession': {__esModule: true, default: ShortSession},
    '../../components/CourseMotivation': {CourseMotivation: Motivation, CourseCheckpoint: unused},
    '../../components/CourseJourney': {CourseJourney: unused},
    '../../components/CourseSpeaking': {CourseSpeaking: unused},
  };
  for (const name of ['CourseCollaboration', 'CourseAnswer', 'CoursePortfolio', 'CourseLessonAudio']) {
    imports[`../../components/${name}`] = {__esModule: true, default: unused};
  }
  const exports = {};
  const file = fs.readFileSync(path.join(root, 'src/pages/student/StudentCoursePractice.tsx'), 'utf8');
  const code = ts.transpileModule(file, {compilerOptions: {
    module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2022,
  }}).outputText;
  vm.runInNewContext(code, {exports, require(name) {
    assert.ok(imports[name], `Unexpected Course dependency: ${name}`);
    return imports[name];
  }});
  const mounted = exports.default();
  function render() {
    let tree;
    for (let pass = 0; pass < 10; pass++) {
      cursor = 0; dirty = false;
      tree = mounted.type(mounted.props);
      pending.splice(0).forEach(effect => effect());
      if (!dirty) return tree;
    }
    throw Error('Course effects did not settle');
  }
  return {
    DailySix, ShortSession, Motivation, reads, render,
    navigate(href) {params = new URL(href, 'https://student.test').searchParams; return render();},
    query: () => params,
    close() {effects.forEach(effect => effect?.cleanup?.());},
  };
}

for (const language of ['en', 'de']) {
  test(`mounted Course follows daily-six -> session -> today and browser back (${language})`, async () => {
    // Use the actual link emitted by DailySix, rather than inventing its route.
    const daily = harness();
    const dailyTree = await loaded(daily, plan({language}));
    const shortLink = nodes(dailyTree, node => node.type === 'a' && text(node).includes('Qisqa seans'))[0];
    assert.ok(shortLink, 'DailySix must offer a short-session link');
    const course = courseRouteHarness(language);
    try {
      assert.equal(course.render().type, course.DailySix);
      assert.equal(course.navigate(shortLink.props.to).type, course.ShortSession,
        'Following the link must switch the mounted Course, not just its URL');
      let tree = course.navigate('/student/course-practice?view=today');
      assert.equal(tree.type, 'main');
      assert.equal(find(tree, 'Bugungi rejam').props['aria-pressed'], true);
      assert.equal(nodes(tree, node => node.type === 'div' && node.props.hidden === false &&
        nodes(node, child => child.type === course.Motivation).length > 0).length, 1);
      // Back then back again: the component is deliberately never remounted.
      assert.equal(course.navigate(shortLink.props.to).type, course.ShortSession);
      assert.equal(course.navigate('/student/course-practice?view=daily-six').type, course.DailySix);
      assert.equal(course.reads.length, 1, 'Route changes must preserve the existing Course mount');
      // Also exercise the actual short-session exit callback with reward context.
      tree = course.navigate('/student/course-practice?view=session&reward_source=daily-six:2026-10-23');
      tree.props.onExit();
      tree = course.render();
      assert.equal(tree.type, 'main');
      assert.equal(find(tree, 'Bugungi rejam').props['aria-pressed'], true);
      assert.equal(course.query().get('view'), 'today');
      assert.equal(course.query().get('reward_source'), 'daily-six:2026-10-23');
    } finally {course.close(); daily.unmount();}
  });
}
