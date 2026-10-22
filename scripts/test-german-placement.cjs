// 2026-10-22: German placement scoring is server-only (api/german_placement.py,
// covered by scripts/test-german-placement-api.py). The client keeps the 48
// question texts WITHOUT the answer key, only so attempts started before the
// deploy (no server "state") can be finished; they must match the server bank.
const fs=require('node:fs'),vm=require('node:vm'),ts=require('typescript'),assert=require('node:assert/strict');
const out={};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/lib/germanPlacement.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2023}}).outputText,{exports:out});
const {germanPlacementQuestions:qs,placementMonths}=out;
const server=JSON.parse(fs.readFileSync('api/german_placement_bank.json','utf8'));
assert.equal(qs.length,48);assert.equal(new Set(qs.map(q=>q.id)).size,48);assert.equal(placementMonths.length,6);
assert.equal(out.assessGerman,undefined,'no client-side scorer');
assert.ok(qs.every(q=>!('answer' in q)),'no answer key in the client bundle');
assert.doesNotMatch(fs.readFileSync('src/lib/germanPlacement.ts','utf8'),/answer\s*:/);
qs.forEach((q,i)=>{
 const s=server[i];
 assert.equal(q.id,s.id);assert.equal(q.month,s.month);assert.equal(q.skill,s.skill);assert.equal(q.prompt,s.prompt);
 assert.equal(q.text||undefined,s.text||undefined);
 // The server may append a 5th option; existing indexes must not move.
 assert.equal(JSON.stringify(q.options),JSON.stringify(s.options.slice(0,q.options.length)),q.id);
});
for(let m=1;m<=6;m++){const block=qs.filter(q=>q.month===m);assert.equal(block.length,8);assert.equal(block.filter(q=>q.skill==='grammar').length,4);}
console.log('PASS: 48 legacy items aligned with the server bank (ids, prompts, texts, option order), no answer key or scorer on the client.');
