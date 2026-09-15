const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const test = require('node:test');
const ts = require('typescript');

function storage() {
  const values = new Map();
  return { getItem: k => values.get(k) ?? null, setItem: (k,v) => values.set(k,String(v)), removeItem: k => values.delete(k), key: i => [...values.keys()][i] ?? null, get length() { return values.size; } };
}
function environment() {
  const sessionStorage = storage(), localStorage = storage(), pending = [];
  const modules = new Map();
  const window = { location: { href: '' } };
  function load(name) {
    if (modules.has(name)) return modules.get(name);
    const source = readFileSync(join(__dirname, '../src/lib', name + '.ts'), 'utf8');
    const code = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText;
    const exports = {};
    vm.runInNewContext(code, {exports, require: name => name === './toast' ? {pushToast(){}} : load(name.replace('./','')), sessionStorage, localStorage, window, Date, Promise, setTimeout, clearTimeout, fetch: (url, options) => new Promise(resolve => pending.push({url,options,reply:(data,status=200) => resolve({ok:status<400,status,json:async()=>data})}))});
    modules.set(name,exports);
    return exports;
  }
  return { load, pending, sessionStorage, localStorage, window, reload: () => modules.clear() };
}
const tick = () => new Promise(resolve => setImmediate(resolve));

test('a completed write detaches old reads; late reads cannot overwrite new progress', async () => {
  const e=environment(), {api}=e.load('api');
  const old=api.get('/student/home'); await tick();
  const save=api.post('/student/answer',{answer:'test'}); await tick();
  e.pending[1].reply({ok:true}); await save;
  const fresh=api.get('/student/home'); await tick();
  assert.equal(e.pending.length,3);
  e.pending[0].reply({xp:1}); await old;
  const shared=api.get('/student/home'); await tick();
  assert.equal(e.pending.length,3,'late old request must not delete the new in-flight request');
  e.pending[2].reply({xp:2});
  assert.equal((await fresh).xp,2); assert.equal((await shared).xp,2);
  assert.equal((await api.get('/student/home')).xp,2);
});

test('explicit refresh wins even when an older response arrives last', async () => {
  const e=environment(), {api}=e.load('api');
  const old=api.get('/student/profile'); await tick();
  const fresh=api.fresh('/student/profile'); await tick();
  e.pending[1].reply({score:80}); await fresh;
  e.pending[0].reply({score:20}); await old;
  assert.equal((await api.get('/student/profile')).score,80);
});

test('switching account rejects old 401 without logging out the new account', async () => {
  const e=environment(), a=e.load('api');
  a.setToken('account-a');
  const old=a.api.get('/student/profile'); const rejected=assert.rejects(old,/Hisob o'zgardi/); await tick();
  a.setToken('account-b'); e.pending[0].reply({},401); await rejected;
  assert.equal(a.getToken(),'account-b'); assert.equal(e.window.location.href,'');
});

test('queued requests cannot silently run with another account credentials', async () => {
  const e=environment(), a=e.load('api'); a.setToken('account-a');
  const requests=Array.from({length:5},(_,i)=>a.api.get('/student/test/'+i));
  const results=Promise.allSettled(requests); await tick(); assert.equal(e.pending.length,4);
  a.setToken('account-b'); for(const p of e.pending) p.reply({});
  assert.ok((await results).every(r=>r.status==='rejected')); assert.equal(e.pending.length,4);
});

test('prefix invalidation refreshes only matching in-flight paths', async () => {
  const e=environment(), a=e.load('api');
  const home=a.api.get('/student/home'), ref=a.api.get('/reference'); await tick();
  a.invalidate('/student'); const next=a.api.get('/student/home'), sameRef=a.api.get('/reference'); await tick();
  assert.equal(e.pending.length,3); e.pending[0].reply({v:0}); e.pending[1].reply({v:1}); e.pending[2].reply({v:2});
  await Promise.all([home,ref,next,sameRef]); assert.equal((await a.api.get('/student/home')).v,2);
});

test('writing drafts survive part switches and module reloads without mixing tasks', () => {
  const e=environment(), d=e.load('studentWritingDrafts');
  d.saveWritingDraft('cinema','1.1',{text:'informal draft',deadline:150000});
  d.saveWritingDraft('cinema','1.2',{text:'formal draft',deadline:null});
  d.saveWritingDraft('library','1.1',{text:'different task',deadline:null});
  assert.equal(d.readWritingDraft('cinema','1.1').text,'informal draft');
  assert.equal(d.readWritingDraft('cinema','1.2').text,'formal draft');
  e.reload();
  assert.equal(e.load('studentWritingDrafts').readWritingDraft('cinema','1.1').text,'informal draft');
  d.removeWritingDraft('cinema','1.1');
  assert.equal(d.readWritingDraft('cinema','1.1').text,'');
  assert.equal(d.readWritingDraft('library','1.1').text,'different task');
});

test('writing countdown uses elapsed wall time, including suspended tabs', () => {
  const d=environment().load('studentWritingDrafts');
  assert.equal(d.writingSecondsLeft(120000,30000),90);
  assert.equal(d.writingSecondsLeft(120000,95000),25);
  assert.equal(d.writingSecondsLeft(120000,121000),0);
});

test('writing drafts remain available when browser storage is disabled', () => {
  const e=environment(), d=e.load('studentWritingDrafts');
  e.sessionStorage.setItem=()=>{throw new Error('storage disabled');};
  d.saveWritingDraft('cinema','1.1',{text:'unsent text',deadline:null});
  assert.equal(d.readWritingDraft('cinema','1.1').text,'unsent text');
  d.clearWritingDrafts();
  assert.equal(d.readWritingDraft('cinema','1.1').text,'');
});

test('logout clears saved identity and private writing drafts', () => {
  const e=environment(), a=e.load('api'), d=e.load('studentWritingDrafts');
  a.setToken('a'); e.sessionStorage.setItem('jony_crm_user','old user');
  d.saveWritingDraft('task','1.1',{text:'private text',deadline:null});
  a.clearToken(); assert.equal(a.getToken(),null); assert.equal(e.sessionStorage.getItem('jony_crm_user'),null);
  assert.equal(d.readWritingDraft('task','1.1').text,'');
});


test('unread notifications survive first visit and same-day new arrivals, isolated by student', () => {
  const e=environment(), n=e.load('studentNotifications');
  const feed={student_id:1,items:[{id:'exam:1',date:'2026-09-15'}]};
  assert.equal(n.hasUnreadNotifications(feed),true);
  assert.equal(n.hasUnreadNotifications(feed),true,'reading feed must not mark anything read');
  n.markNotificationsRead(1,feed.items);
  assert.equal(n.hasUnreadNotifications(feed),false);
  assert.equal(n.hasUnreadNotifications({...feed,student_id:2}),true);
  assert.equal(n.hasUnreadNotifications({...feed,items:[...feed.items,{id:'exam:2',date:'2026-09-15'}]}),true);
  e.reload(); assert.equal(e.load('studentNotifications').hasUnreadNotifications(feed),false);
});
test('notification state ignores legacy shared timestamp and tolerates corrupt or unavailable storage', () => {
  const e=environment(), n=e.load('studentNotifications');
  e.localStorage.setItem('jonyos_notif_seen','2099-01-01');
  e.localStorage.setItem('jonyos_notif_read:1','invalid-json');
  const feed={student_id:1,items:[{id:'reward:2'}]};
  assert.equal(n.hasUnreadNotifications(feed),true);
  e.localStorage.getItem=()=>{throw Error('blocked');};
  e.localStorage.setItem=()=>{throw Error('blocked');};
  n.markNotificationsRead(1,feed.items);
  assert.equal(n.hasUnreadNotifications(feed),false);
  assert.equal(n.hasUnreadNotifications({...feed,student_id:2}),true);
});
