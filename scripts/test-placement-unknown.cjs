const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),ts=require('typescript');
const html=fs.readFileSync('public/placement.html','utf8');
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.dataset={};this.attrs={};this.value='';const classes=new Set();this.classList={add:c=>classes.add(c),remove:c=>classes.delete(c),contains:c=>classes.has(c)};}
 appendChild(e){this.children.push(e);return e;}
 setAttribute(k,v){this.attrs[k]=v;}
 set innerHTML(v){this.children=[];if(v.includes('class="k"'))this.children=[new Element('span'),new Element('span')];}
 get lastChild(){return this.children.at(-1);}
}
const body=new Element('div'),document={createElement:t=>new Element(t),createTextNode:t=>({textContent:t})};
const scope={document,$:()=>body,send:p=>scope.sent=p,submit:()=>{},hasTTS:false};
vm.createContext(scope);
const start=html.indexOf('  function optButtons('),end=html.indexOf('  function collect(');
vm.runInContext(html.slice(start,end),scope);
for(const kind of ['grammar','listening']){
 scope.renderGrammarLike({kind,opts:['a','b','c','d'],qid:1,q:'?',plays:2});
 const group=body.children.find(x=>x.className==='opts');
 assert.equal(group.children.length,5);
 assert.equal(group.children[4].lastChild.textContent,'Bilmayman');
 assert.equal(group.children.some(x=>x.attrs['aria-pressed']==='true'),false);
 group.children[4].onclick();
 assert.equal(scope.sent.choice,-1);
 assert.equal(group.children[4].attrs['aria-pressed'],'true');
 assert.ok(group.children[4].classList.contains('sel'));
 group.children[0].onclick();assert.equal(scope.sent.choice,0);assert.equal(group.children[4].attrs['aria-pressed'],'false');
}
scope.renderReading({text:'text',qs:[{q:'?',opts:['a','b','c','d']}]});
const group=body.children[1].children[1];group.children[4].onclick();assert.equal(group.dataset.pick,'-1');
scope.renderVocab({words:['a','b','c','d','e','f'],defs:['?']});
const select=body.children[2].children[1];
assert.equal(select.children[0].value,'');assert.equal(select.children.at(-1).value,'-1');
assert.equal(select.children.at(-1).textContent,'Bilmayman');

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
 const bank={};vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/lib/germanPlacement.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,{exports:bank});
 const g=host('src/pages/GermanPlacement.tsx',[{answers:{},index:0,started:true,done:false}],{bank});
 let radios=nodes(g.render()).filter(n=>n.type==='input'&&n.props.type==='radio');assert.equal(radios.length,5);assert.ok(radios.every(n=>!n.props.checked));
 radios[4].props.onChange();assert.equal(g.states[0].answers['gp-1'],-1);
 radios=nodes(g.render()).filter(n=>n.type==='input'&&n.props.type==='radio');assert.equal(radios[4].props.checked,true);
 const next=nodes(g.render()).find(n=>n.type==='button'&&Array.isArray(n.props.children)&&n.props.children[0]==='Keyingi');assert.equal(next.props.disabled,false);
 next.props.onClick();assert.equal(g.states[0].index,1);
 assert.equal(bank.assessGerman(g.states[0].answers).score,0);
 console.log('PASS: public grammar/listening/reading/vocabulary unknown selection; student fifth choice and payload; German answered state and navigation.');
})().catch(e=>{console.error(e);process.exitCode=1;});
