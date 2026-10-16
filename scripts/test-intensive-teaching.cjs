const test=require('node:test'), assert=require('node:assert/strict');
const {teaching,load}=require('./export-intensive-teaching.cjs');
const path=require('node:path');
const api=teaching(), course=api.intensiveTeachingCourse();
const lib=load(path.resolve(__dirname,'../src/lib/intensive.ts'));
test('192 serializable kits retain 32 weeks and 8 months with continuous 120 minute budgets',()=>{
  assert.equal(course.length,192); assert.equal(new Set(course.map(k=>k.week)).size,32);assert.equal(new Set(course.map(k=>k.month)).size,8);
  for(const [i,k] of course.entries()) {assert.equal(k.lesson,i+1);assert.equal(k.totalMinutes,120);assert.equal(k.homeworkMinutes,120);let t=0;for(const s of k.stages){assert.equal(s.start,t);assert.ok(s.minutes>0);t=s.end;}assert.equal(t,120);assert.equal(JSON.parse(JSON.stringify(k)).lesson,i+1);assert.equal(k.homeworkMinutes,k.homework.reduce((n,h)=>n+h.minutes,0));}
  assert.equal(new Set(course.map(k=>k.profile)).size,6);
});
test('every internal exercise ref resolves to original questions and unchanged answer keys',()=>{
  for(const k of course){const available=new Map(k.questions.map(q=>[q.id,q]));assert.equal(available.size,k.questions.length);
    for(const id of [...k.mandatoryExerciseIds,...k.extensionExerciseIds,...k.homework.flatMap(h=>h.exerciseIds)])assert.ok(available.has(id)||/^(speaking-|writing-|exam:)/.test(id),`${k.lesson}: ${id}`);
    const plan=lib.lessonPlan(k.lesson);const source=new Map([...lib.lessonGrammarPractice(k.lesson),...(k.profile.startsWith('mock-') ? lib.lessonGrammarPractice(k.lesson-1):[]),...plan.topics.flatMap(t=>lib.topicPractice(t.id))].map(q=>[q.id,q]));
    for(const q of k.questions){assert.ok(q.answers.length&&q.explanation);if(q.id.startsWith('topic-')||q.id.startsWith('g-'))assert.deepEqual(q,source.get(q.id));}
    if(!plan.review&&!plan.spiral&&k.lesson<169)for(const t of plan.topics)assert.ok(k.mandatoryExerciseIds.some(id=>id.startsWith(`topic-${t.id}-`)),`${k.lesson} omits ${t.id}`);
  }
});
test('foundation boundaries, final handoff, and finite input handling',()=>{
 for(const k of course.slice(0,6))assert.match(k.boundary,/erkin gap.*talab qilinmaydi/);
 assert.equal(course[191].handoff.nextLesson,null);assert.equal(api.intensiveTeachingKit(Infinity).lesson,1);assert.equal(api.intensiveTeachingKit(-1).lesson,1);assert.equal(api.intensiveTeachingKit(300).lesson,192);
 assert.equal(api.intensiveTeachingKit(1,NaN).groupSize,16);
});
test('split mock sessions honor the existing component budgets and are confined to month 8',()=>{
 assert.equal(course[167].exam,null);assert.ok(course[168].exam);
 for(const no of [181,187]){const k=course[no-1];assert.equal(k.stages.find(s=>s.exerciseIds.includes('exam:listening')).minutes,45);assert.equal(k.stages.find(s=>s.exerciseIds.includes('exam:reading')).minutes,60);assert.equal(k.exam.cycle,course[no].exam.cycle);}
 for(const no of [182,188]){const k=course[no-1];assert.equal(k.stages.find(s=>s.exerciseIds.includes('exam:writing')).minutes,60);assert.equal(k.stages.find(s=>s.exerciseIds.includes('exam:speaking')).minutes,30);}
});

test('audio paths and group logistics cover solo, pairs and triads',()=>{
 for(const k of course)assert.equal(k.materials.audioUrl,`/intensive/audio/lesson-${String(k.lesson).padStart(3,'0')}.mp3`);
 assert.match(api.intensiveTeachingKit(1,1).stages.find(s=>s.title.startsWith('Speaking')).instruction,/1 o‘quvchi: ustoz sherik/);
 assert.match(api.intensiveTeachingKit(1,3).stages.find(s=>s.title.startsWith('Speaking')).instruction,/0 juft va 1 uchlik/);
 assert.match(api.intensiveTeachingKit(1,16).stages.find(s=>s.title.startsWith('Speaking')).instruction,/8 juft/);
});

test('mock homework preserves all 100 assigned new words and avoids upcoming papers',()=>{
 const slots=[];
 for(const no of [181,182,187,188]){const k=course[no-1];assert.equal(k.homeworkMinutes,120);assert.equal(k.homework[0].minutes,25);const p=lib.lessonPlan(no);assert.ok(k.homework[0].task.includes(`${p.start}–${p.end}`));assert.equal(p.spiral,true);slots.push(...k.materials.vocabulary.map(w=>w.id));assert.match(k.homework[2].task,/oldindan ishlamang/);}
 assert.equal(new Set(slots).size,100);
});

test('teacher UI uses Uzbek labels and keeps answer/transcript/model sections closed',()=>{
 const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript');
 const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
 const file=path.resolve(__dirname,'../src/components/IntensiveTeachingKit.tsx'),out={};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2023,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText,{exports:out,require:n=>n==='../lib/intensiveTeaching'?api:require(n)});
 const html=renderToStaticMarkup(React.createElement(out.default,{lesson:1}));
 assert.ok(html.includes('Boshlang‘ich tayanch'));assert.ok(html.includes('Asosiy mashqlar'));assert.ok(html.includes('Javob kalitlari'));assert.ok(html.includes('120 daqiqa'));
 assert.equal(/<details[^>]*\bopen/.test(html),false);assert.equal(html.includes('Majburiy IDlar'),false);
});
