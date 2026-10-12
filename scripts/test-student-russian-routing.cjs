const {readFileSync}=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const ts=require('typescript');
const root=path.resolve(__dirname,'..');
const read=p=>readFileSync(path.join(root,p),'utf8');
const values=new Map(), events=new EventTarget();
let subscribe;
const react={useSyncExternalStore:(s,g)=>{subscribe=s;return g();}};
const box={exports:{},require:n=>{assert.equal(n,'react');return react;},
 localStorage:{getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)},window:events,Event};
vm.runInNewContext(ts.transpileModule(read('src/lib/lang.ts'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,box);
const lang=box.exports;
assert.equal(lang.useLearningLanguage(),'en');
let calls=0;const unsubscribe=subscribe(()=>calls++);
lang.setLang('ru');assert.equal(lang.getLang(),'ru');assert.equal(calls,1);
lang.setLang('invalid');assert.equal(lang.getLang(),'ru');assert.equal(calls,1);
for(const code of ['de','ko','en','ru']) {lang.setLang(code);assert.equal(lang.useLearningLanguage(),code);}
const external=new Event('storage');external.key='jonyos_lang';values.set('jonyos_lang','de');events.dispatchEvent(external);assert.equal(lang.useLearningLanguage(),'de');assert.equal(calls,6);
unsubscribe();lang.setLang('en');assert.equal(calls,6);
const app=read('src/App.tsx');
for(const component of ['StudentGames','StudentVocab','StudentGrammar','StudentGrammarPlay','StudentGamePlay','StudentPractice','StudentSpeaking']) {
 assert.ok(new RegExp('<StudentLanguageRoute[^>]*><'+component+'(?: mix)? /></StudentLanguageRoute>').test(app),component+' must select language before fetching legacy exercises');
}
assert.ok(app.includes('path="russian" element={<StudentRussianCourse />}'));
const wrapper=read('src/components/StudentLanguageRoute.tsx');assert.ok(wrapper.includes('language === "ru"'));assert.ok(wrapper.includes('skill || section'));
console.log('PASS: Russian entry points, all learning languages, same-page and cross-tab selection, invalid selections and subscription cleanup');
