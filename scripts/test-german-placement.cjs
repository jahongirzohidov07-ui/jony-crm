const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript'),assert=require('node:assert/strict');
const out={};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/lib/germanPlacement.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2023}}).outputText,{exports:out});
const {germanPlacementQuestions:qs,assessGerman:score}=out;
assert.equal(qs.length,48);assert.equal(new Set(qs.map(q=>q.id)).size,48);
const all=Object.fromEntries(qs.map(q=>[q.id,q.answer]));
assert.equal(score(all).lesson,70);assert.equal(score(all).score,48);assert.equal(score({}).lesson,1);
for(let m=1;m<=6;m++){
 const block=qs.filter(q=>q.month===m);assert.equal(block.length,8);assert.equal(block.filter(q=>q.skill==='grammar').length,4);
 block.forEach(q=>{assert.equal(new Set(q.options).size,4);assert.ok(q.answer>=0&&q.answer<4);});
 const a={...all};block.slice(0,3).forEach(q=>a[q.id]=-1);assert.equal(score(a).lesson,(m-1)*12+1,'earliest gap must control placement');
 const b={...all};block.filter(q=>q.skill==='reading').forEach(q=>b[q.id]=-1);assert.equal(score(b).month,m,'reading floor');
 const c={...all};block.slice(0,2).forEach(q=>c[q.id]=-1);assert.equal(score(c).month,m,'grammar floor');
 const d={...all};block.filter(q=>q.skill==='vocabulary').forEach(q=>d[q.id]=-1);assert.equal(score(d).lesson,70,'6/8 plus section floors passes');
}
assert.equal(score(Object.fromEntries(qs.map(q=>[q.id,-1]))).score,0);
console.log('PASS: 48 items, all six entry points, prerequisite gating, section floors, pass boundary, unknown and blank answers.');
