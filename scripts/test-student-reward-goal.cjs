const fs=require('node:fs');
const vm=require('node:vm');
const test=require('node:test');
const assert=require('node:assert/strict');
const ts=require('typescript');
const mod={exports:{}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('src/lib/studentRewardGoal.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,{exports:mod.exports});
const {readRewardGoal,writeRewardGoal,resolveRewardGoal}=mod.exports;
const rewards=[{id:1,name:'Book',cost:50,active:true,in_stock:true},{id:2,name:'Cap',cost:100,active:true,in_stock:true},{id:3,name:'Old',cost:10,active:false,in_stock:true},{id:4,name:'Gone',cost:30,active:true,in_stock:false}];
test('chosen reward survives reload without leaking across student accounts',()=>{
 const values=new Map();const storage={getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,v)};
 assert.equal(writeRewardGoal(storage,7,2),true);assert.equal(readRewardGoal(storage,7),2);assert.equal(readRewardGoal(storage,8),null);
 assert.equal(resolveRewardGoal(rewards,readRewardGoal(storage,7),6).reward.id,2);
});
test('selected goal remains selected when affordable; held coin excluded via available balance',()=>{
 const x=resolveRewardGoal(rewards,2,105);assert.equal(x.reward.id,2);assert.equal(x.left,0);assert.equal(x.percent,100);
 const held=resolveRewardGoal(rewards,2,6);assert.equal(held.left,94);assert.equal(held.percent,6);
});
test('sold out selection remains visible but removed reward gets honest fallback',()=>{
 assert.equal(resolveRewardGoal(rewards,4,6).reward.in_stock,false);
 const removed=resolveRewardGoal(rewards,3,6);assert.equal(removed.unavailableSelection,true);assert.equal(removed.reward.id,1);
});
test('empty catalog is not all rewards affordable',()=>{
 const x=resolveRewardGoal([],null,999);assert.equal(x.reward,null);assert.equal(x.percent,0);
});
test('corrupt or blocked storage is safe; invalid writes rejected',()=>{
 for(const value of ['NaN','-1','0','1.2','Infinity','9007199254740992']) assert.equal(readRewardGoal({getItem:()=>value},1),null);
 assert.equal(readRewardGoal({getItem:()=>{throw Error('blocked')}},1),null);
 assert.equal(writeRewardGoal({setItem:()=>{throw Error('blocked')}},1,2),false);
 assert.equal(writeRewardGoal({setItem:()=>assert.fail()},1,0),false);
});
test('negative or invalid balance never creates negative progress',()=>{
 for(const value of [-10,NaN,Infinity]) {const x=resolveRewardGoal(rewards,1,value);assert.equal(x.percent,0);assert.equal(x.left,50);}
});
