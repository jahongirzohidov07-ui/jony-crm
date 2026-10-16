// Evaluate the UI's pure teaching module; print exact serializable data for PDFs.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
const cache = new Map();
function loadTs(file) {
  const full = path.resolve(root, file);
  if (cache.has(full)) return cache.get(full);
  const exports = {};
  cache.set(full, exports);
  const output = ts.transpileModule(fs.readFileSync(full, 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2023, esModuleInterop: true } }).outputText;
  vm.runInNewContext(output, { exports, require: name => {
    const resolved = path.resolve(path.dirname(full), name);
    return fs.existsSync(resolved + '.ts') ? loadTs(resolved + '.ts') : require(resolved);
  } }, { filename: full });
  return exports;
}
module.exports = { loadTs };
if (require.main === module) process.stdout.write(JSON.stringify(loadTs('src/lib/germanTeaching.ts').germanTeachingExport));
