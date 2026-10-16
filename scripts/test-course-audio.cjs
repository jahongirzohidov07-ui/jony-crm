const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const root = path.resolve(__dirname,'..');
const read = p => JSON.parse(fs.readFileSync(path.join(root,p),'utf8').replace(/^\uFEFF/,''));
const hash = data => createHash('sha256').update(data).digest('hex');
const manifest = read('src/data/course-audio-manifest.json');
for(const [course,count,source,key,lang] of [
 ['intensive',192,'src/data/intensive-skills.json','lesson','en-GB'],
 ['german',72,'src/data/german/skills.json','no','de-DE'],
])test(`${course}: every lesson has a persistent recording matching its current transcript`,()=>{
 const data=read(source),rows=manifest.filter(r=>r.course===course);
 assert.equal(rows.length,count);assert.equal(new Set(rows.map(r=>r.lesson)).size,count);
 for(const item of data){
  const n=item[key],row=rows.find(r=>r.lesson===n);assert.ok(row,`${course}/${n}`);
  assert.equal(row.path,`/${course}/audio/lesson-${String(n).padStart(3,'0')}.mp3`);
  assert.equal(row.source,source);assert.equal(row.language,lang);assert.equal(row.synthesized,true);
  assert.equal(row.sourceSha256,hash(item.listening.text));assert.ok(row.duration>1&&Number.isFinite(row.duration));
  const bytes=fs.readFileSync(path.join(root,'public',row.path));
  assert.equal(bytes.length,row.bytes);assert.ok(bytes.length>512);assert.equal(hash(bytes),row.sha256);
  assert.ok(row.voices.length>0&&row.voices.every(v=>v.startsWith(lang)));
 }
});
test('manifest contains exactly the two supported courses',()=>{
 assert.equal(manifest.length,264);assert.deepEqual([...new Set(manifest.map(r=>r.course))].sort(),['german','intensive']);
});
