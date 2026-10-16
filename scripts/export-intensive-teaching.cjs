// Evaluate the UI's pure TypeScript data module without maintaining a second schedule.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const cache = new Map();
function load(file) {
  file = path.resolve(file);
  if (cache.has(file)) return cache.get(file);
  if (file.endsWith('.json')) return JSON.parse(fs.readFileSync(file, 'utf8'));
  const exports = {}; cache.set(file, exports);
  const js = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2023, esModuleInterop: true },
  }).outputText;
  vm.runInNewContext(js, { exports, require: name => {
    if (!name.startsWith('.')) throw Error('Unexpected dependency: '+name);
    const target = path.resolve(path.dirname(file), name);
    return load(path.extname(target) ? target : target+'.ts');
  } }, {filename:file});
  return exports;
}
const teaching = () => load(path.join(root,'src/lib/intensiveTeaching.ts'));
module.exports = { teaching, load };
if (require.main === module) {
  const course = teaching().intensiveTeachingCourse();
  const target = path.join(root,'_inbox/intensive-teacher-kits.json');
  fs.mkdirSync(path.dirname(target), {recursive:true});
  fs.writeFileSync(target, JSON.stringify(course));
  console.log(`Exported ${course.length} teacher kits from the UI source to ${target}`);
}
