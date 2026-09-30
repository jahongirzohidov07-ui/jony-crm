
const {readFileSync} = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const test = require('node:test');
const assert = require('node:assert/strict');
const ts = require('typescript');
const source = readFileSync(path.join(__dirname,'../src/lib/examOrderDates.ts'),'utf8');
const code = ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const output = {};
vm.runInNewContext(code,{exports:output,Date,Intl});
const dates = output.examOrderDates;
test('October 2 is explicit and submitted as ISO, not February 10',()=>{
  const rows=dates({min_date:'2026-10-01',max_date:'2026-11-29',min_notice_days:1,max_ahead_days:60},new Date('2030-01-01'));
  assert.equal(rows.length,60);
  assert.equal(rows[1].label,'2-oktabr 2026');
  assert.equal(rows[1].value,'2026-10-02');
  assert.equal(rows.some(r=>r.value==='2026-02-10'),false);
  assert.equal(rows.at(-1).value,'2026-11-29');
});
test('cached response fallback uses Tashkent at UTC midnight boundary',()=>{
  const rows=dates({min_notice_days:1,max_ahead_days:60},new Date('2026-09-30T20:00:00Z'));
  assert.equal(rows[0].value,'2026-10-02');
});
test('year and leap-month boundaries stay valid',()=>{
  const rows=dates({min_date:'2026-12-31',max_date:'2027-01-01',min_notice_days:1,max_ahead_days:60});
  assert.equal(rows[1].label,'1-yanvar 2027');
  const leap=dates({min_date:'2028-02-28',max_date:'2028-03-01',min_notice_days:1,max_ahead_days:60});
  assert.equal(leap.length,3);
  assert.equal(leap[1].label,'29-fevral 2028');
});
