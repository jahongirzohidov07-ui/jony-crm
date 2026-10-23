const fs = require("node:fs");
const ts = require("typescript");
const assert = require("node:assert/strict");
const test = require("node:test");
const React = require("react");
function load(path, resolve = require) {
 const exports = {};
 new Function("exports","require",ts.transpileModule(fs.readFileSync(path,"utf8"), {
  compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}
 }).outputText)(exports,resolve);
 return exports;
}
const helper = load("src/lib/studentRewardPractice.ts");
const {rewardPracticePlan:plan,rewardVocabHref:href} = helper;
const source = (id,status="in_progress") => ({id,status});
const unit = (key,extra={}) => ({key,n:20,percent:0,learned3:0,learned6:0,passed:false,...extra});
test("league en/de opens daily session with only canonical source",()=>{
 for(const language of ["en","de"]) {
  const p=plan(source("league:bronze"),language);
  assert.equal(p.href,"/student/course-practice?view=session&reward_source=league%3Abronze");
 }
});
test("paid/untracked/manual sources have no launch in any language",()=>{
 for(const status of ["awarded","untracked","manual_review"])
  for(const lang of ["en","de","ru","ko"])
   for(const id of ["league:bronze","streak:7","wordbank:1"])
    assert.equal(plan(source(id,status),lang),null);
});
test("Russian legacy replacement is honest; Korean uses actual vocabulary",()=>{
 for(const id of ["league:bronze","streak:7"]) {
  assert.equal(plan(source(id),"ru").kind,"unavailable");
  assert.equal(plan(source(id),"ko").kind,"vocab");
 }
 assert.equal(plan(source("other:1"),"en").kind,"unavailable");
 assert.equal(plan(source("streak:7"),"fr").kind,"unavailable");
});
test("wordbank opens adaptive queue without a forged band",()=>{
 const p=plan(source("wordbank:12","eligible"),"en");
 assert.equal(p.href,"/student/words/practice?reward_source=wordbank%3A12");
 assert.equal(plan(source("wordbank:12"),"de").kind,"unavailable");
 assert.ok(!p.label.includes("12"));
});
test("vocab uses exact real unit and prefers started, not mastered",async()=>{
 for(const language of ["en","de","ko"]) {
  let calls=0;
  const url=await href(source("streak:7"),language,async path=>{
   calls++;assert.equal(path,"/student/vocab/units?language="+language);
   return {language,units:[unit("first"),unit("passed",{passed:true,percent:100}),
    unit("solid",{learned6:20,percent:99}),unit("A & B / 2",{learned3:1,percent:5})]};
  });
  const q=new URL(url,"https://test").searchParams;
  assert.equal(q.get("unit"),"A & B / 2");assert.equal(q.get("lang"),language);
  assert.equal(q.get("count"),"10");assert.equal(q.get("reward_source"),"streak:7");
  assert.equal(new URL(url,"https://test").pathname,"/student/games/en_uz");
  assert.equal(calls,1);assert.deepEqual([...q.keys()].sort(),["count","lang","reward_source","unit"]);
 }
});
test("fallback respects API ordering, skips unplayable units, supports virtual mixed bucket",async()=>{
 const url=await href(source("league:gold"),"ko",async()=>({language:"ko",units:[unit("too small",{n:3}),unit("real-first"),unit("real-second")]}));
 assert.equal(new URL(url,"https://test").searchParams.get("unit"),"real-first");
 const mixed=await href(source("streak:7"),"en",async()=>({language:"en",units:[unit("Boshqa")]}));
 assert.equal(new URL(mixed,"https://test").searchParams.has("unit"),false);
 assert.ok(mixed.startsWith("/student/games/en_uz?"));
});
test("lookup errors/empty catalog/wrong language never return a list fallback",async()=>{
 for(const response of [{language:"en",units:[]},{language:"de",units:[unit("A")]},{language:"en",units:[unit("tiny",{n:2})]}])
  await assert.rejects(href(source("streak:7"),"en",async()=>response));
 await assert.rejects(href(source("streak:7"),"en",async()=>{throw Error("offline")}),/offline/);
 await assert.rejects(href(source("streak:7"),"ru",async()=>assert.fail("must not fetch")));
 await assert.rejects(href(source("streak:7","awarded"),"en",async()=>assert.fail("must not fetch")));
});
function walk(node,predicate) {
 if(!node||typeof node!=="object")return null;
 if(predicate(node))return node;
 for(const child of React.Children.toArray(node.props?.children)) {
  const match=walk(child,predicate);if(match)return match;
 }
 return null;
}
test("async launcher disables duplicates, exposes error/retry, and navigates only after success",async()=>{
 let slots=[],index=0,cleanup,navigated=[],calls=0,resolve,reject;
 const mockedReact={...React,
  useState(initial){const i=index++;if(!(i in slots))slots[i]=initial;return [slots[i],v=>slots[i]=v];},
  useRef(initial){const i=index++;return slots[i]??=( {current:initial} );},
  useEffect(fn){if(!cleanup)cleanup=fn();}
 };
 const mod=load("src/components/StudentRewardPath.tsx",name=>{
  if(name==="react")return mockedReact;
  if(name==="../lib/studentRewardPractice")return helper;
  if(name==="../lib/lang")return {useLearningLanguage:()=>"en"};
  if(name==="../lib/api")return {api:{fresh:()=>{calls++;return new Promise((res,rej)=>{resolve=res;reject=rej;});}}};
  if(name==="react-router-dom")return {Link:()=>null,useNavigate:()=>url=>navigated.push(url)};
  return require(name);
 });
 const card=mod.SourceCard({source:{...source("streak:7"),have:0,target:7,unit:"days"},onHistory:()=>{}});
 const launcher=walk(card,n=>typeof n.type==="function"&&n.type.name==="VocabLauncher");
 assert.ok(launcher);
 const render=()=>{index=0;return launcher.type(launcher.props);};
 let tree=render();assert.equal(calls,0);
 const start=walk(tree,n=>n.type==="button").props.onClick;
 const first=start();await start();assert.equal(calls,1);
 tree=render();assert.equal(walk(tree,n=>n.type==="button").props.disabled,true);
 assert.ok(walk(tree,n=>n.props.role==="status"));
 reject(Error("offline"));await first;tree=render();
 assert.ok(walk(tree,n=>n.props.role==="alert"));
 assert.equal(walk(tree,n=>n.type==="button").props.children,"Qayta urinish");
 const retry=walk(tree,n=>n.type==="button").props.onClick();
 resolve({language:"en",units:[unit("Unit 4")]});await retry;
 assert.equal(navigated.length,1);assert.ok(navigated[0].includes("unit=Unit+4"));
 const last=walk(render(),n=>n.type==="button").props.onClick();
 cleanup();resolve({language:"en",units:[unit("Unit 5")]});await last;
 assert.equal(navigated.length,1,"unmounted or language-switched launcher cannot navigate");
});


test("daily six reward opens actual bundle and only supported languages",()=>{
 for(const language of ["en","de"]) {
  const p=plan(source("daily-six:2026-10-23"),language);
  assert.equal(p.href,"/student/course-practice?view=daily-six&reward_source=daily-six%3A2026-10-23");
 }
 for(const language of ["ru","ko"]) assert.equal(plan(source("daily-six:2026-10-23"),language).kind,"unavailable");
 assert.equal(plan(source("daily-six:2026-10-23","awarded"),"en"),null);
});
