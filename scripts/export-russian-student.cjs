/* Canonical Russian lessons, exported for the private backend only. */
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const lessons = [1, 2, 3, 4].flatMap(part =>
  JSON.parse(fs.readFileSync(path.join(root, 'src/data/russian', `part-${part}.json`), 'utf8'))
);
if (lessons.length !== 144 || lessons.some((l, i) =>
  l.no !== i + 1 || l.month !== Math.floor(i / 12) + 1)) {
  throw new Error('Expected 144 sequential Russian lessons across 12 months');
}
const fields = ['no', 'month', 'title', 'objective', 'grammar', 'phrases',
  'dialog', 'questions', 'homework', 'exit', 'roleplay'];
const exported = lessons.map(lesson => Object.fromEntries(fields.map(key => {
  if (lesson[key] === undefined) throw new Error(`Lesson ${lesson.no}: missing ${key}`);
  return [key, lesson[key]];
})));
fs.writeFileSync(path.join(root, 'api/student_russian_data.json'),
  JSON.stringify(exported, (key, value) => key === 'teacherTip' ? undefined : value) + '\n');
console.log(`Exported ${exported.length} student Russian lessons.`);
