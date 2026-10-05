const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const test=require('node:test');
const assert=require('node:assert/strict');
const ts=require('typescript');
const source=path.resolve(__dirname,'../src/lib/intensive.ts');
const output={};
vm.runInNewContext(ts.transpileModule(fs.readFileSync(source,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,esModuleInterop:true,target:ts.ScriptTarget.ES2023}}).outputText,{exports:output,require:p=>require(path.resolve(path.dirname(source),p))});
test('192 lessons cover every grammar topic and all 4000 planned word slots without skipping or repeating new slots',()=>{
  const ids=new Set(), slots=[];
  for(let no=1;no<=192;no++){
    const p=output.lessonPlan(no); assert.equal(p.no,no); assert.equal(p.day,(no-1)%6+1);
    assert.equal(p.month,Math.ceil(no/24)); assert.ok(p.topics.length>0);
    if(!p.review){p.topics.forEach(t=>ids.add(t.id));for(let i=p.start;i<=p.end;i++)slots.push(i);}
    else {assert.equal(p.end-p.start+1,125);assert.equal(p.day,6);}
    assert.equal(p.wordsReady,p.end<=output.words.length);
  }
  assert.equal(ids.size,output.topics.length);assert.equal(slots.length,4000);assert.equal(new Set(slots).size,4000);assert.equal(Math.min(...slots),1);assert.equal(Math.max(...slots),4000);
});
test('teaching and homework budgets each total 120 minutes',()=>{
  for(const timeline of [output.standardTimeline,output.reviewTimeline,output.homework])assert.equal(timeline.reduce((sum,row)=>sum+row[0],0),120);
});
test('every vocabulary block has complete unique entries and answerable 10/20 word exercises',()=>{
  assert.equal(new Set(output.words.map(w=>w.word.toLowerCase())).size,output.words.length);
  output.words.forEach((w,i)=>{assert.equal(w.id,i+1);for(const value of Object.values(w))assert.ok(value);});
  for(const size of [10,20])for(let start=0;start<output.words.length;start+=size){
    const pool=output.words.slice(start,start+size), before=JSON.stringify(pool), qs=output.vocabularyPractice(pool,size===20);
    assert.equal(qs.length,pool.length);assert.equal(new Set(qs.map(q=>q.id)).size,pool.length);
    for(const q of qs){assert.ok(q.answers[0]);assert.ok(output.isCorrect(q.answers[0].toUpperCase(),q.answers));assert.ok(!output.isCorrect('',q.answers));}
    assert.equal(JSON.stringify(pool),before);
  }
});
test('grammar topics all have model practice and separate explained checks',()=>{
  assert.equal(output.teacherNotes.length,output.grammar.length);
  for(const notes of output.teacherNotes){assert.equal(notes.length,3);assert.ok(notes.every(n=>n.length>20));}
  for(const t of output.topics){const qs=output.topicPractice(t.id);assert.equal(qs.length,1);assert.ok(output.isCorrect(t.example,qs[0].answers));}
  const qs=output.grammarChecks(output.grammar.map((_,i)=>i));assert.equal(qs.length,54);assert.equal(new Set(qs.map(q=>q.id)).size,54);
  for(const q of qs){assert.ok(q.explanation);assert.ok(output.isCorrect(q.answers[0],q.answers));}
  assert.ok(output.isCorrect("  MUSTN'T! ",["mustn’t"]));assert.ok(!output.isCorrect('are',['is']));
});
test('weekly mixed grammar review stays within its taught modules with unique questions',()=>{
  for(let i=0;i<27;i++){
    const qs=output.grammarReview([i]);assert.ok(qs.length>=10&&qs.length<=20);assert.equal(new Set(qs.map(q=>q.id)).size,qs.length);
    assert.ok(qs.every(q=>q.id.startsWith(`g-${i}-`)||q.id.startsWith(`model-${i+1}.`)));
  }
});
test('partial future lessons are explicitly not ready',()=>{
  assert.equal(output.lessonPlan(19).start,376);assert.equal(output.lessonPlan(19).wordsReady,true);
  for(let no=1;no<=24;no++)assert.equal(output.lessonPlan(no).wordsReady,true);
  assert.equal(output.lessonPlan(25).wordsReady,false);assert.equal(output.lessonPlan(192).wordsReady,false);
});
if(process.argv.includes('--export'))fs.writeFileSync(path.resolve(__dirname,'../public/intensive/course-export.json'),JSON.stringify({lessons:Array.from({length:192},(_,i)=>output.lessonPlan(i+1)),timeline:output.standardTimeline,reviewTimeline:output.reviewTimeline,homework:output.homework,grammar:output.grammar,topics:output.topics,words:output.words,checks:output.grammarChecks(output.grammar.map((_,i)=>i))},null,2));
