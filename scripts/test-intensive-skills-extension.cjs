const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const read=name=>JSON.parse(fs.readFileSync(`src/data/${name}.json`,'utf8'));
const packs=read('intensive-skills'),extension=read('intensive-skills-extension');
const normal=s=>s.replace(/\s+/g,' ').trim();
const ids=new Set();
function evidence(task,text){
 assert(!ids.has(task.id),`duplicate ${task.id}`);ids.add(task.id);
 assert(task.prompt&&task.teacher.answer&&task.teacher.guidance);assert(task.teacher.evidence.length);
 for(const quote of task.teacher.evidence)assert(normal(text).includes(normal(quote)),`${task.id}: unsupported evidence ${quote}`);
}
test('all 192 lessons add staged comprehension with source-grounded keys',()=>{
 assert.equal(extension.lessons.length,192);
 extension.lessons.forEach((item,i)=>{assert.equal(item.lesson,i+1);
  for(const mode of ['reading','listening']){
   const extra=item[mode];assert.equal(extra.tasks.length,4);assert(extra.before);
   assert(extra.tasks.some(t=>t.stage==='first-pass'));assert(extra.tasks.some(t=>t.stage==='respond'));
   extra.tasks.forEach(t=>evidence(t,packs[i][mode].text));
  }
 });assert.equal(ids.size,1536);
});
test('32 distinct unseen homework passages increase sustained reading with supported answers',()=>{
 assert.equal(extension.homework.length,32);const originals=new Set(packs.flatMap(p=>[normal(p.reading.text),normal(p.listening.text)]));const unseen=new Set();
 extension.homework.forEach((h,i)=>{assert.equal(h.week,i+1);assert.equal(h.afterLesson,(i+1)*6);assert(h.minutes>=20&&h.minutes<=35);assert(!originals.has(normal(h.text)));assert(!unseen.has(normal(h.text)));unseen.add(normal(h.text));
  assert(h.tasks.length>=4);if(i>=24){assert(h.text.split(/\s+/).length>=350);assert(h.tasks.length>=6);}
  h.tasks.forEach(t=>evidence(t,h.text));
 });
});
