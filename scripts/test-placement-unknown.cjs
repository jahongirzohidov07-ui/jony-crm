const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),ts=require('typescript');
const html=fs.readFileSync('public/placement.html','utf8');
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.attrs={};this.value='';const classes=new Set();this.classList={add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c)};}
 appendChild(e){this.children.push(e);return e;}
 setAttribute(k,v){this.attrs[k]=v;}
 set innerHTML(v){this.children=[];if(v.includes('class="k"'))this.children=[new Element('span'),new Element('span')];}
 get firstChild(){return this.children[0];}
 get lastChild(){return this.children.at(-1);}
}
const body=new Element('div'),document={createElement:t=>new Element(t),createTextNode:t=>({textContent:t})};
const scope={document,$:()=>body,send:p=>scope.sent=p,submit:()=>{},hasTTS:false};
vm.createContext(scope);
// 2026-10-22: "Bilmayman" faqat server idk:true yuborganda, real variantlardan
// keyin OXIRIDA (4 yoki 5 variant), qiymati -1.
const start=html.indexOf('  // ---- Savol turlari'),end=html.indexOf('  function collect(');
vm.runInContext(html.slice(start,end),scope);
for(const kind of ['grammar','listening']){
 scope.renderGrammarLike({kind,opts:['a','b','c','d','e'],qid:1,q:'?',plays:2,idk:true});
 const group=body.children.find(x=>x.className==='opts');
 assert.equal(group.children.length,6);
 assert.equal(group.children[5].lastChild.textContent,'Bilmayman');
 assert.equal(group.children[5].firstChild.textContent,'?');
 assert.equal(group.children[5].className,'opt idk');
 assert.equal(group.children[4].firstChild.textContent,'E');
 assert.equal(group.children.some(x=>x.attrs['aria-pressed']==='true'),false);
 group.children[5].onclick();
 assert.equal(scope.sent.choice,-1);
 assert.equal(group.children[5].attrs['aria-pressed'],'true');
 assert.ok(group.children[5].classList.contains('sel'));
 group.children[4].onclick();assert.equal(scope.sent.choice,4);assert.equal(group.children[5].attrs['aria-pressed'],'false');
 // Eski server (idk yo'q): faqat haqiqiy variantlar.
 scope.renderGrammarLike({kind,opts:['a','b','c','d'],qid:1,q:'?',plays:2});
 const plain=body.children.find(x=>x.className==='opts');
 assert.equal(plain.children.length,4);assert.ok(plain.children.every(x=>x.lastChild.textContent!=='Bilmayman'));
}
scope.renderReading({text:'text',idk:true,qs:[{q:'?',opts:['a','b','c','d','e']}]});
const group=body.children[1].children[1];assert.equal(group.children.length,6);group.children[5].onclick();assert.equal(group.dataset.pick,'-1');
scope.renderReading({text:'text',qs:[{q:'?',opts:['a','b','c','d']}]});
assert.equal(body.children[1].children[1].children.length,4);
scope.renderVocab({words:['a','b','c','d','e','f'],defs:['?'],idk:true});
const select=body.children[2].children[1];
assert.equal(select.children[0].value,'');assert.equal(select.children.at(-1).value,'-1');
assert.equal(select.children.at(-1).textContent,'Bilmayman');
scope.renderVocab({words:['a','b','c','d','e','f'],defs:['?']});
assert.equal(body.children[2].children[1].children.some(o=>o.value==='-1'),false);

// Render the real React components with a minimal hook host; exercise their handlers.
function host(file,initial,extra={}){
 let states=initial,cursor=0;
 const exports={};
 const react={useState:init=>{const i=cursor++;if(!(i in states))states[i]=typeof init==='function'?init():init;return [states[i],v=>states[i]=typeof v==='function'?v(states[i]):v];},useEffect(){},useCallback:f=>f};
 const jsx=(type,props)=>({type,props:props||{}});
 const context={exports,require:n=>n==='react'?react:n==='react/jsx-runtime'?{jsx,jsxs:jsx}:n.includes('useAutoNext')?{autoNextDelay:()=>100}:n.includes('germanPlacement')?extra.bank:n.includes('/api')?{api:{post:async(url,p)=>{context.sent=p;return {correct:false,expected:'a'};}}}:n.includes('/Jsa')?{JSA:{},JsaLogo:'logo'}:{},sessionStorage:{getItem:()=>null},window:{},setTimeout(){},...extra};
 vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX}}).outputText,context);
 return {render:()=>{cursor=0;return exports.default();},context,states};
}
function nodes(tree){if(!tree||typeof tree!=='object')return [];if(Array.isArray(tree))return tree.flatMap(nodes);return [tree,...nodes(tree.props?.children)];}
(async()=>{
 const h=host('src/pages/student/StudentLevelTest.tsx',['quiz',null,{question:{options:['a','b','c','d'],kind:'fill'},section:'grammar'},null,null,null,false,'']);
 let buttons=nodes(h.render()).filter(n=>n.type==='button'&&n.props['aria-pressed']!==undefined);
 assert.equal(buttons.length,5);assert.ok(buttons.every(b=>!b.props['aria-pressed']));
 await buttons[4].props.onClick();assert.equal(h.context.sent.answer,-1);
 buttons=nodes(h.render()).filter(n=>n.type==='button'&&n.props['aria-pressed']!==undefined);
 assert.equal(buttons[4].props['aria-pressed'],true);assert.ok(buttons[4].props.className.includes('border-red'));
 // Nemis sahifasi (2026-10-22): savol serverdan (seq), "Bilmayman" faqat idk:true
 // bo'lsa va oxirida; deploydan oldingi urinish (legacy) — mahalliy savollar.
 const React=require('react'),{renderToStaticMarkup}=require('react-dom/server');
 function loadTs(file,overrides={}){const m={exports:{}};vm.runInNewContext(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2023}}).outputText,{module:m,exports:m.exports,require:id=>Object.hasOwn(overrides,id)?overrides[id]:require(id)});return m.exports;}
 const bank=loadTs('src/lib/germanPlacement.ts');
 assert.equal(bank.assessGerman,undefined,'no client answer key');
 const choices=loadTs('src/components/PlacementChoices.tsx');
 const icons=new Proxy({},{get:()=>()=>null});
 function germanPage(hookState){
  const mod=loadTs('src/pages/GermanPlacement.tsx',{'react-router-dom':{Link:p=>React.createElement('a',{href:p.to},p.children)},'lucide-react':icons,'../assets/brand-icon.png':'brand.png',
   '../lib/germanPlacement':bank,'../components/PlacementChoices':choices,'../lib/placementSeq':{useSeqPlacement:()=>hookState}});
  return renderToStaticMarkup(React.createElement(mod.default));
 }
 const hook=(attempt,extra={})=>({attempt,setAttempt(){},question:null,pick:undefined,setPick(){},busy:false,stepError:'',stateBroken:false,start(){},answer(){},recover(){},reset(){},saving:false,saveError:'',retrySave(){},storageError:false,...extra});
 const sq={id:'gp-1',no:1,total:48,month:1,skill:'grammar',prompt:'Ich ___ Student.',options:['bist','bin','ist','sind','seid'],idk:true};
 let page=germanPage(hook({answers:{},index:0,started:true,done:false,mode:'seq',state:'S'},{question:sq,pick:-1}));
 assert.equal((page.match(/type="radio"/g)||[]).length,6);
 assert.ok(page.lastIndexOf('Bilmayman')>page.lastIndexOf('seid'),'Bilmayman is last');
 assert.match(page,/checked=""[^>]*\/><span[^>]*>\?<\/span><span lang="uz"[^>]*>Bilmayman/);
 assert.doesNotMatch(page,/Oldingi/,'seq: no going back');
 page=germanPage(hook({answers:{},index:0,started:true,done:false,mode:'seq',state:'S'},{question:{...sq,idk:undefined}}));
 assert.equal((page.match(/type="radio"/g)||[]).length,5);assert.doesNotMatch(page,/>Bilmayman</);
 page=germanPage(hook({answers:{'gp-1':-1},index:0,started:true,done:false,mode:'legacy'}));
 assert.equal((page.match(/type="radio"/g)||[]).length,5);assert.match(page,/Oldingi/);assert.match(page,/>Bilmayman</);
 const result={score:30,month:4,lesson:37,label:'A2 yakuni',gaps:[],allPassed:false,idk:3,blocks:[{month:1,label:'A1 poydevor',correct:8,total:8,passed:true}],skills:[{skill:'grammar',correct:15,total:24}]};
 page=germanPage(hook({answers:{},index:0,started:true,done:true,mode:'seq',state:'S',identity:{full_name:'QA',phone:'901234567',branch_id:1},attemptId:'x',result}));
 assert.match(page,/30\/48/);assert.match(page,/37-dars/);assert.doesNotMatch(page,/Juda tez|Taxminan bosilgan/,'taker never sees speed info');
 console.log('PASS: public grammar/listening/reading/vocabulary: 5 options + last Bilmayman only with idk; student fifth choice and payload; German server-served question, legacy attempt, server result without speed info.');
})().catch(e=>{console.error(e);process.exitCode=1;});
