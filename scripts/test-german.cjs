const fs = require('node:fs');
const assert = require('node:assert/strict');
const read = name => JSON.parse(fs.readFileSync(`src/data/german/${name}.json`, 'utf8'));
const words = [1,2,3].flatMap(n => read(`vocabulary-${n}`));
const topics = read('grammar'), lessons = read('lessons'), skills = read('skills');
assert.equal(words.length,2400);
assert.equal(lessons.length,72); assert.equal(skills.length,72);
const norm = text => text.normalize('NFKC').toLocaleLowerCase('de').trim().replace(/\s+/g,' ');
assert.equal(new Set(words.map(w=>norm(w.word))).size,2400,'Duplicate vocabulary entries');
words.forEach((w,i) => {assert.equal(w.id,i+1);assert.equal(w.week,Math.ceil(w.id/100));for(const key of ['word','ipa','meaning','example','translation','topic']) assert.ok(typeof w[key]==='string'&&w[key].trim(),`${w.id} missing ${key}`);assert.equal(typeof w.forms,'string');});
const topicIds=new Set(topics.map(t=>t.id));assert.equal(topicIds.size,topics.length);assert.ok(topics.length>=144);
let questions=0; const questionIds=new Set();
function checkQuestions(qs,where,min=3){assert.ok(qs.length>=min,where);qs.forEach(q=>{assert.ok(q.id&&q.prompt&&q.explanation,where);assert.ok(q.answers.length&&q.answers.every(a=>a.trim()),where);assert.ok(!questionIds.has(q.id),`Duplicate question ID ${q.id}`);questionIds.add(q.id);questions++;});}
topics.forEach(t=>{assert.ok(t.rule&&t.example&&t.translation,t.id);checkQuestions(t.questions,t.id);});
const assigned=new Set();let wordAssignment=[];
lessons.forEach((l,i)=>{assert.equal(l.no,i+1);assert.equal(l.week,Math.ceil(l.no/3));assert.equal(l.month,Math.ceil(l.week/4));assert.ok(l.objective&&l.teacherTip&&l.supportTask&&l.homework.length);assert.ok(l.topicIds.length);l.topicIds.forEach(id=>{assert.ok(topicIds.has(id),`Unknown ${id}`);assigned.add(id);});const day=i%3;wordAssignment.push(...words.filter(w=>w.week===l.week).slice(Math.floor(day*100/3),Math.floor((day+1)*100/3)).map(w=>w.id));});
assert.equal(assigned.size,topics.length,'Unassigned grammar topics');assert.deepEqual(wordAssignment,words.map(w=>w.id));
const texts=new Set();skills.forEach((s,i)=>{assert.equal(s.no,i+1);for(const kind of ['reading','listening']){assert.ok(s[kind].text&&s[kind].title);assert.ok(!texts.has(norm(s[kind].text)),`Duplicate text ${s.no}/${kind}`);texts.add(norm(s[kind].text));checkQuestions(s[kind].questions,`${s.no}/${kind}`);}for(const kind of ['speaking','writing'])assert.ok(s[kind].task&&s[kind].model&&s[kind].criteria.length>=3);});
console.log(`PASS: ${words.length} unique entries, ${topics.length} topics, ${lessons.length} lessons + support, ${skills.length*2} distinct texts, ${questions} exercises; complete ID and schedule coverage.`);
const path=require('node:path'), vm=require('node:vm'), ts=require('typescript');
function loadTs(file){const full=path.resolve(file),out={};vm.runInNewContext(ts.transpileModule(fs.readFileSync(full,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,esModuleInterop:true,target:ts.ScriptTarget.ES2023}}).outputText,{exports:out,require:p=>p.endsWith('/intensive')?loadTs('src/lib/intensive.ts'):require(path.resolve(path.dirname(full),p))});return out;}
const course=loadTs('src/lib/german.ts'), english=loadTs('src/lib/intensive.ts');
for(let no=1;no<=72;no++){const pool=course.lessonWords(no),review=course.supportWords(no);assert.ok(pool.length>=33&&pool.length<=34);assert.equal(review.length,20);assert.ok(review.every(w=>w.id<=pool.at(-1).id&&w.week>=Math.max(1,Math.ceil(no/3)-1)),`Future vocabulary in support ${no}`);}
for(const size of [10,20])for(let i=0;i<words.length;i+=size){const pool=words.slice(i,i+size),before=JSON.stringify(pool),qs=course.germanWordPractice(pool,size===20);assert.equal(qs.length,pool.length);assert.equal(new Set(qs.map(q=>q.id)).size,qs.length);for(const q of qs){assert.ok(english.isCorrect(q.answers[0],q.answers,q.caseSensitive));assert.ok(!english.isCorrect('',q.answers,q.caseSensitive));assert.ok(!q.prompt.includes('Inglizcha'));}assert.equal(JSON.stringify(pool),before);}
for(const [key,budget] of [['mainTimeline',120],['orientationTimeline',120],['supportTimeline',60],['independentWork',75]])assert.equal(course[key].reduce((sum,row)=>sum+row[0],0),budget);
assert.ok(!english.isCorrect('der mann',['der Mann'],true));assert.ok(!english.isCorrect('schon',['schön'],true));
console.log('PASS: all 10/20 blocks answerable, noun capitalization and umlauts retained, support only reviews taught words, timing budgets 120/60/75.');

for(const no of [70,71,72])assert.equal(course.finalWeekTimeline(no).reduce((sum,row)=>sum+row[0],0),120);
