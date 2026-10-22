const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),test=require('node:test'),assert=require('node:assert/strict'),ts=require('typescript'),React=require('react');
const {renderToStaticMarkup}=require('react-dom/server');
let selected=null; const modules=new Map();
function load(file){
 file=path.resolve(file);if(modules.has(file))return modules.get(file);const exp={};modules.set(file,exp);
 const code=ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText;
 vm.runInNewContext(code,{exports:exp,URLSearchParams,localStorage:{getItem:()=>selected},require:n=>{
  if(n==='react-router-dom')return {Link:({to,children,...props})=>React.createElement('a',{...props,href:to},children)};
  if(n.endsWith('/api'))return {api:{},getToken:()=>null};if(n.endsWith('/lang'))return {useLearningLanguage:()=> 'en'};
  if(n.startsWith('.')){const p=path.resolve(path.dirname(file),n);return load(fs.existsSync(p+'.ts')?p+'.ts':p+'.tsx');}return require(n);
 }});return exp;
}
const c=load('src/components/RewardPracticeContext.tsx');
const source={id:'league:2',title:'Bronze',have:483,target:600,unit:'xp',status:'in_progress'};
const coins={student_id:1,available:60,balance:100,held:40,rewards:[{id:2,name:'Book',cost:150,active:true,in_stock:true}]};
const render=(s=source,base=483)=>renderToStaticMarkup(React.createElement(c.RewardPracticeProgress,{snapshot:{coins,source:s},baseline:base}));
test('reward practice retains goal with spendable coins and canonical source progress',()=>{const html=render();assert.match(html,/60.*150 coin/);assert.match(html,/yana 90 coin kerak/);assert.match(html,/483.*600 XP.*yana 117 XP/);assert.doesNotMatch(html,/100.*150 coin/);});
test('server updated progress is visible without promising a coin',()=>{const html=render({...source,have:493});assert.match(html,/483 →.*493.*600 XP/);assert.match(html,/Har javob coin bermaydi/);assert.doesNotMatch(html,/Coin berilgani hisob tarixida tasdiqlangan/);});
test('threshold eligibility is distinct from ledger payment',()=>{assert.match(render({...source,status:'eligible',have:600}),/hali tasdiqlanmagan/);assert.match(render({...source,status:'awarded',have:600}),/hisob tarixida tasdiqlangan/);});
test('removed earning rule and forged context cannot fabricate a goal',()=>{assert.match(render(null),/endi mavjud emas/);for(const bad of [null,'manual','https://evil.test','league:2&coins=999','<script>'])assert.equal(c.validRewardSource(bad),false);assert.equal(c.validRewardSource('league:2'),true);});

// Minimal hook lifecycle runner: executes the actual private LiveContext returned
// by the public wrapper, with persistent hooks, effect cleanup, and deferred IO.
// No production export or copied identity logic is needed.
function contextHarness() {
  let token = "account-a", cursor = 0, tree, mounted = true;
  const slots = [], pendingEffects = [], timers = new Map(), requests = [];
  let timerId = 0;
  const events = () => {
    const listeners = new Map();
    return {
      addEventListener(name, fn) { if (!listeners.has(name)) listeners.set(name, new Set()); listeners.get(name).add(fn); },
      removeEventListener(name, fn) { listeners.get(name)?.delete(fn); },
      emit(name, event = {}) { for (const fn of [...(listeners.get(name) || [])]) fn(event); },
      count() { return [...listeners.values()].reduce((n, set) => n + set.size, 0); },
    };
  };
  const window = events(), document = { ...events(), visibilityState: "visible" };
  const hooks = {
    ...React,
    useState(initial) {
      const i = cursor++;
      if (!(i in slots)) slots[i] = { value: typeof initial === "function" ? initial() : initial };
      return [slots[i].value, value => { slots[i].value = typeof value === "function" ? value(slots[i].value) : value; }];
    },
    useRef(initial) { const i = cursor++; return slots[i] ??= { current: initial }; },
    useEffect(callback, deps) {
      const i = cursor++, previous = slots[i];
      if (!previous || deps.some((d, n) => !Object.is(d, previous.deps[n]))) {
        pendingEffects.push(() => {
          previous?.cleanup?.();
          slots[i] = { deps, cleanup: callback() };
        });
      }
    },
  };
  const exports = {};
  const code = ts.transpileModule(fs.readFileSync("src/components/RewardPracticeContext.tsx", "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  vm.runInNewContext(code, {
    exports, URLSearchParams, window, document,
    localStorage: { getItem: () => null },
    setTimeout(fn) { const id = ++timerId; timers.set(id, fn); return id; },
    clearTimeout(id) { timers.delete(id); },
    require(name) {
      if (name === "react") return hooks;
      if (name === "react-router-dom") return {
        useLocation: () => ({ pathname: "/student/course-practice", search: "?view=session&reward_source=league%3A2" }),
        Link: ({ to, children, ...props }) => React.createElement("a", { ...props, href: to }, children),
      };
      if (name === "../lib/api") return { getToken: () => token, api: {
        fresh(url) { return new Promise((resolve, reject) => requests.push({ token, url, resolve, reject })); },
      } };
      if (name === "../lib/lang") return { useLearningLanguage: () => "en" };
      if (name === "../lib/studentRewardGoal") return load("src/lib/studentRewardGoal.ts");
      if (name === "../lib/rewardPracticeEvents") return { REWARD_PRACTICE_UPDATED: "jony:reward-practice-updated" };
      if (name === "./StudentRewardPath") return { REWARD_UNITS: { xp: "XP" } };
      return require(name);
    },
  });
  const element = exports.default(); // Keeps the same language/source key for both accounts.
  function renderHook() {
    assert.ok(mounted);
    cursor = 0;
    tree = element.type(element.props);
    while (pendingEffects.length) pendingEffects.shift()();
    return renderToStaticMarkup(tree);
  }
  function walk(node, predicate) {
    if (!node || typeof node !== "object") return null;
    if (predicate(node)) return node;
    for (const child of React.Children.toArray(node.props?.children)) {
      const found = walk(child, predicate); if (found) return found;
    }
    return null;
  }
  return {
    requests, window, document,
    render: renderHook,
    switchAccount() { token = "account-b"; },
    flushTimer() { const current = [...timers.values()]; timers.clear(); for (const fn of current) fn(); },
    refreshEvent() { window.emit("jony:reward-practice-updated"); },
    retry() { renderHook(); const button = walk(tree, n => n.type === "button" && n.props.children === "Qayta yangilash"); assert.ok(button); button.props.onClick(); renderHook(); },
    settle(offset, studentId, have, available) {
      const pair = requests.slice(offset, offset + 2);
      assert.equal(pair.length, 2);
      for (const r of pair) r.resolve(r.url === "/me/coins"
        ? { ...coins, student_id: studentId, full_name: "Same Student Name", available }
        : { student_id: studentId, sources: [{ ...source, have }] });
    },
    unmount() { for (const slot of slots) slot?.cleanup?.(); mounted = false; },
  };
}
const settleHooks = () => new Promise(resolve => setImmediate(resolve));

test("same-name cross-tab switch clears immediately and delayed old response cannot replace new account", async () => {
  const h = contextHarness();
  h.render(); h.settle(0, 1, 483, 60); await settleHooks();
  assert.match(h.render(), /483.*600 XP/);
  h.refreshEvent(); h.flushTimer(); // Account A's second request remains delayed.
  assert.equal(h.requests[2].token, "account-a");
  h.switchAccount();
  h.window.emit("storage", { key: "jony_crm_token", newValue: "account-b" });
  let html = h.render();
  assert.doesNotMatch(html, /483|Book|60.*150 coin/);
  assert.match(html, /Maqsadingiz yuklanmoqda/);
  h.flushTimer();
  assert.equal(h.requests[4].token, "account-b");
  h.settle(4, 2, 20, 7); await settleHooks();
  html = h.render();
  assert.match(html, /20.*600 XP/); assert.match(html, /7.*150 coin/);
  assert.doesNotMatch(html, /483|→/); // Baseline must belong to B, despite identical full_name.
  h.settle(2, 1, 590, 99); await settleHooks();
  html = h.render();
  assert.doesNotMatch(html, /590|99.*150 coin|483/);
  assert.match(html, /20.*600 XP/);
  assert.doesNotMatch(html, /disabled=""|Hisob yangilanmoqda/);
  h.refreshEvent(); h.flushTimer(); h.settle(6, 2, 30, 8); await settleHooks();
  assert.match(h.render(), /20 →.*30.*600 XP/);
  h.unmount(); assert.equal(h.window.count(), 0); assert.equal(h.document.count(), 0);
});

test("focus catches a missed account storage event and invalidates pending responses", async () => {
  const h = contextHarness();
  h.render(); h.settle(0, 1, 483, 60); await settleHooks(); h.render();
  h.refreshEvent(); h.flushTimer();
  h.switchAccount(); h.window.emit("focus");
  assert.doesNotMatch(h.render(), /483|Book/);
  h.settle(2, 1, 590, 99); await settleHooks();
  assert.doesNotMatch(h.render(), /590|Book/);
  h.flushTimer(); h.settle(4, 2, 20, 7); await settleHooks();
  assert.match(h.render(), /20.*600 XP/);
  h.unmount();
});

test("midflight token change without an event produces a retryable error and resets baseline", async () => {
  const h = contextHarness();
  h.render(); h.settle(0, 1, 483, 60); await settleHooks(); h.render();
  h.refreshEvent(); h.flushTimer(); h.switchAccount();
  h.settle(2, 1, 590, 99); await settleHooks();
  const html = h.render();
  assert.match(html, /role="alert"/); assert.doesNotMatch(html, /483|590|disabled=""/);
  h.retry(); h.settle(4, 2, 20, 7); await settleHooks();
  assert.doesNotMatch(h.render(), /483|→/);
  h.unmount();
});

test("account-change API rejection also clears the old baseline before retry", async () => {
  const h = contextHarness();
  h.render(); h.settle(0, 1, 483, 60); await settleHooks(); h.render();
  h.refreshEvent(); h.flushTimer(); h.switchAccount();
  // api.ts rejects responses when the request token differs from getToken().
  for (const r of h.requests.slice(2, 4)) r.reject(Error("Hisob o'zgardi, so'rov bekor qilindi"));
  await settleHooks();
  assert.match(h.render(), /role="alert"/);
  h.retry(); h.settle(4, 2, 20, 7); await settleHooks();
  const html = h.render();
  h.unmount();
  assert.doesNotMatch(html, /483|→/, "Account A baseline must not be shown as B's progress");
  assert.match(html, /20.*600 XP/);
});
