// 2026-10-22 — nemis/rus kirish testlari: savollar serverdan bittadan
// (src/lib/placementSeq.ts), "Bilmayman" tanlovi (PlacementChoices) va
// xodim hisoboti "Bilmayman: N · Juda tez: N" (PlacementGuessStats).
// Ishga tushirish: node scripts/test-placement-seq-client.cjs
const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict'), ts = require('typescript');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

function load(file, overrides = {}, globals = {}) {
  const module = { exports: {} };
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2023 },
  }).outputText;
  vm.runInNewContext(code, { module, exports: module.exports, console,
    require: id => Object.hasOwn(overrides, id) ? overrides[id] : require(id), ...globals });
  return module.exports;
}
const tick = () => new Promise(r => setTimeout(r, 0));

// ---- Kichik hook "renderer": useState/useEffect, effektlar render'dan keyin.
function harness() {
  const states = [], effects = [];
  let pending = [], dirty = false, cursor = 0, ec = 0, out, hook, args;
  const react = {
    useState(init) {
      const i = cursor++;
      if (!(i in states)) states[i] = typeof init === 'function' ? init() : init;
      return [states[i], v => { const nv = typeof v === 'function' ? v(states[i]) : v; if (!Object.is(nv, states[i])) { states[i] = nv; dirty = true; } }];
    },
    useEffect(fn, deps) {
      const i = ec++, prev = effects[i];
      if (prev && deps && deps.every((d, k) => Object.is(d, prev.deps[k]))) return;
      effects[i] = { deps, cleanup: prev && prev.cleanup };
      pending.push(() => { if (effects[i].cleanup) effects[i].cleanup(); effects[i].cleanup = fn(); });
    },
  };
  function render() { cursor = 0; ec = 0; dirty = false; out = hook(args); const p = pending; pending = []; p.forEach(f => f()); }
  async function settle() {
    for (let n = 0; n < 100; n++) { render(); await tick(); await tick(); if (!dirty && !pending.length) return out; }
    throw new Error('hook did not settle');
  }
  return { react, settle, mount(h, a) { hook = h; args = a; return settle(); }, get out() { return out; } };
}

// ---- Server soxtasi: chaqiruvlarni yozib boradi.
function server(routes) {
  const calls = [];
  const fetch = async (url, opts = {}) => {
    const body = opts.body ? JSON.parse(opts.body) : undefined;
    calls.push({ url, body });
    const [status, data] = routes(url, body);
    return { ok: status < 400, status, json: async () => data };
  };
  return { calls, fetch };
}
function storage(init = {}) {
  const m = new Map(Object.entries(init));
  return { getItem: k => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, String(v)), map: m };
}
const BASE = '/api/public/german-placement';
const AID = '11111111-1111-4111-8111-111111111111';
const ID = { full_name: 'QA Learner', phone: '901234567', branch_id: 1 };
const q = (id, no, extra = {}) => ({ id, no, total: 3, month: 1, skill: 'grammar', prompt: 'P' + no,
  options: ['a', 'b', 'c', 'd', 'e'], idk: true, ...extra });

function seqModule(h, store, srv) {
  return load('src/lib/placementSeq.ts', { react: h.react }, {
    fetch: srv.fetch, sessionStorage: store, setTimeout, clearTimeout, AbortController,
    crypto: { randomUUID: () => AID },
  });
}

(async () => {
  // 1) sessionStorage'dan tiklash: deploydan oldingi urinish -> legacy.
  {
    const h = harness();
    const lib = seqModule(h, storage(), server(() => [404, {}]));
    const ids = ['gp-1', 'gp-2', 'gp-3'];
    const old = { answers: { 'gp-1': 1, 'gp-2': -1, 'gp-3': 4, x: 2 }, index: 2, started: true, done: false, identity: ID, attemptId: AID };
    const a = load('src/lib/placementSeq.ts', {}, { sessionStorage: storage({ k: JSON.stringify(old) }) }).restoreAttempt('k', 3, ids);
    assert.equal(a.mode, 'legacy'); assert.equal(a.index, 2); assert.equal(a.started, true);
    assert.deepEqual({ ...a.answers }, { 'gp-1': 1, 'gp-2': -1, 'gp-3': 4 }, '5-variant (4) va -1 saqlanadi, begona kalit tashlanadi');
    const bad = load('src/lib/placementSeq.ts', {}, { sessionStorage: storage({ k: JSON.stringify({ answers: { 'gp-1': 12, 'gp-2': -2 } }) }) }).restoreAttempt('k', 3, ids);
    assert.deepEqual({ ...bad.answers }, {});
    const seq = load('src/lib/placementSeq.ts', {}, { sessionStorage: storage({ k: JSON.stringify({ answers: {}, mode: 'seq', state: 'S1', started: true, identity: ID, attemptId: AID }) }) }).restoreAttempt('k', 3, ids);
    assert.equal(seq.mode, 'seq'); assert.equal(seq.state, 'S1');
    const noId = load('src/lib/placementSeq.ts', {}, { sessionStorage: storage({ k: JSON.stringify({ answers: {}, mode: 'seq', state: 'S1', attemptId: AID }) }) }).restoreAttempt('k', 3, ids);
    assert.equal(noId.mode, 'legacy', 'identity yo\'q seq holati ishlatilmaydi');
    assert.equal(lib.isRouteMissing(new lib.PlacementHttpError('Not Found', 404)), true);
    assert.equal(lib.isRouteMissing(new lib.PlacementHttpError('Test holati buzilgan', 400)), false);
    assert.equal(lib.isRouteMissing(new lib.PlacementHttpError('Filial topilmadi', 404)), false);
  }

  // 2) Ketma-ket test: start -> "Bilmayman" (-1) -> eski javob (stale) -> oxirgi -> saqlash FAQAT state bilan.
  {
    const h = harness(), store = storage();
    let n = 0;
    const srv = server((url, body) => {
      if (url === BASE + '/start') return [200, { state: 'S0', question: q('q1', 1), done: false }];
      if (url === BASE + '/answer') {
        n++;
        if (n === 1) return [200, { state: 'S1', question: q('q2', 2), done: false }];
        if (n === 2) return [200, { state: 'S1', question: q('q2', 2), done: false, stale: true }];
        if (n === 3) return [200, { state: 'S2', question: q('q3', 3), done: false }];
        return [200, { state: 'S3', question: null, done: true }];
      }
      if (url === BASE) return [200, { saved: true, result: { score: 1, idk: 1 } }];
      return [404, { detail: 'Not Found' }];
    });
    const lib = seqModule(h, store, srv);
    await h.mount(lib.useSeqPlacement, { base: BASE, storageKey: 'k', total: 3 });
    assert.equal(h.out.attempt.started, false);
    await h.out.start(ID); await h.settle();
    assert.deepEqual(srv.calls[0], { url: BASE + '/start', body: { attempt_id: AID } });
    assert.equal(h.out.attempt.mode, 'seq'); assert.equal(h.out.question.id, 'q1'); assert.equal(h.out.question.idk, true);
    h.out.setPick(-1); await h.settle();
    await h.out.answer(); await h.settle();
    assert.deepEqual(srv.calls.at(-1), { url: BASE + '/answer', body: { attempt_id: AID, state: 'S0', qid: 'q1', choice: -1 } });
    assert.equal(h.out.attempt.answers.q1, -1); assert.equal(h.out.question.id, 'q2'); assert.equal(h.out.pick, undefined);
    h.out.setPick(4); await h.settle();
    await h.out.answer(); await h.settle();
    assert.equal(h.out.attempt.answers.q2, undefined, 'stale javob yozilmaydi');
    h.out.setPick(4); await h.settle(); await h.out.answer(); await h.settle();
    assert.equal(h.out.attempt.answers.q2, 4, '5-variant (indeks 4) yuboriladi');
    h.out.setPick(0); await h.settle(); await h.out.answer(); await h.settle();
    assert.equal(h.out.attempt.done, true);
    const save = srv.calls.find(c => c.url === BASE);
    assert.deepEqual(save.body, { ...ID, attempt_id: AID, state: 'S3' }, 'seq saqlash: answers YUBORILMAYDI, faqat state');
    assert.deepEqual({ ...h.out.attempt.result }, { score: 1, idk: 1 });
    assert.equal(srv.calls.some(c => 'choice' in (c.body || {}) && typeof c.body.choice !== 'number'), false);
    assert.equal(JSON.stringify(srv.calls).includes('elapsed'), false, 'mijoz vaqt yubormaydi');
    const saved = JSON.parse(store.getItem('k'));
    assert.equal(saved.mode, 'seq'); assert.equal(saved.state, 'S3');
  }

  // 3) Eski server (/start yo'q) -> legacy: javoblar oxirida answers bilan.
  {
    const h = harness();
    const srv = server(url => url === BASE ? [200, { saved: true, result: { score: 0 } }] : [404, { detail: 'Not Found' }]);
    const lib = seqModule(h, storage(), srv);
    await h.mount(lib.useSeqPlacement, { base: BASE, storageKey: 'k', total: 1 });
    await h.out.start(ID); await h.settle();
    assert.equal(h.out.attempt.mode, 'legacy'); assert.equal(h.out.attempt.started, true); assert.equal(h.out.stepError, '');
    h.out.setAttempt(a => ({ ...a, answers: { 'gp-1': -1 }, done: true })); await h.settle();
    const save = srv.calls.find(c => c.url === BASE);
    assert.deepEqual(save.body, { ...ID, attempt_id: AID, answers: { 'gp-1': -1 } });
  }

  // 4) Sahifa yangilandi: /current bilan davom etadi; holat buzilsa — qaytadan boshlash.
  {
    const h = harness();
    let broken = true;
    const srv = server(url => {
      if (url === BASE + '/current') return broken ? [400, { detail: 'Test holati buzilgan' }] : [200, { state: 'S5', question: q('q5', 2), done: false }];
      if (url === BASE + '/start') return [200, { state: 'N0', question: q('q1', 1), done: false }];
      return [404, { detail: 'Not Found' }];
    });
    const st = storage({ k: JSON.stringify({ answers: { q1: 0 }, mode: 'seq', state: 'S5', started: true, done: false, identity: ID, attemptId: AID }) });
    const lib = seqModule(h, st, srv);
    await h.mount(lib.useSeqPlacement, { base: BASE, storageKey: 'k', total: 3 });
    assert.deepEqual(srv.calls[0], { url: BASE + '/current', body: { attempt_id: AID, state: 'S5' } });
    assert.equal(h.out.stepError, 'Test holati buzilgan'); assert.equal(h.out.stateBroken, true);
    h.out.recover(); await h.settle();
    assert.equal(srv.calls.at(-1).url, BASE + '/start'); assert.equal(h.out.question.id, 'q1'); assert.equal(h.out.attempt.state, 'N0');
    broken = false;
    const h2 = harness(), lib2 = seqModule(h2, st, srv);
    st.setItem('k', JSON.stringify({ answers: { q1: 0 }, mode: 'seq', state: 'S5', started: true, done: false, identity: ID, attemptId: AID }));
    await h2.mount(lib2.useSeqPlacement, { base: BASE, storageKey: 'k', total: 3 });
    assert.equal(h2.out.question.id, 'q5');
  }

  // 5) Variantlar: haqiqiy variantlar + oxirida "Bilmayman" (-1), faqat idk:true bo'lsa.
  {
    const { default: Choices } = load('src/components/PlacementChoices.tsx');
    const inputs = el => { const out = []; const walk = n => { if (!n || typeof n !== 'object') return; if (Array.isArray(n)) return n.forEach(walk); if (n.type === 'input') out.push(n); walk(n.props && n.props.children); }; walk(el); return out; };
    let got;
    const five = Choices({ name: 'q', options: ['a', 'b', 'c', 'd', 'e'], value: undefined, onChange: v => { got = v; }, idk: true, lang: 'de' });
    const ins = inputs(five);
    assert.equal(ins.length, 6);
    ins[5].props.onChange(); assert.equal(got, -1);
    ins[4].props.onChange(); assert.equal(got, 4);
    assert.equal(inputs(Choices({ name: 'q', options: ['a', 'b', 'c', 'd'], value: undefined, onChange() {}, idk: false, lang: 'de' })).length, 4);
    const html = renderToStaticMarkup(React.createElement(Choices, { name: 'q', options: ['a', 'b', 'c', 'd', 'e'], value: -1, onChange() {}, idk: true, lang: 'ru' }));
    assert.ok(html.lastIndexOf('Bilmayman') > html.lastIndexOf('>e<'), '"Bilmayman" eng oxirida');
    assert.match(html, /checked=""[^>]*\/><span[^>]*>\?<\/span><span lang="uz"[^>]*>Bilmayman/);
    assert.match(html, /border-dashed/);
  }

  // 6) Xodim hisoboti.
  {
    const lucide = { AlertTriangle: () => null };
    const g = load('src/components/PlacementGuessStats.tsx', { 'lucide-react': lucide });
    const en = { idk: 4, fast: 11, guess_warning: true, skills: [
      { key: 'grammar', label: 'Grammatika', idk: 2, fast: 9 }, { key: 'vocab', label: "Lug'at", idk: 1, fast: 1 },
      { key: 'reading', label: 'Reading', idk: 1, fast: 1 }, { key: 'listening', label: 'Listening', idk: 0, fast: 0 }] };
    const s = g.guessSummary(en);
    assert.equal(s.idk, 4); assert.equal(s.fast, 11); assert.equal(s.warning, true); assert.equal(s.sections.length, 4);
    let html = renderToStaticMarkup(React.createElement(g.GuessStats, { res: en }));
    assert.match(html, /Bilmayman: 4 · Juda tez: 11/);
    assert.match(html, /Grammatika: Bilmayman: 2 · Juda tez: 9/);
    assert.match(html, /Taxminan bosilgan bo(&#x27;|')lishi mumkin/);
    assert.match(renderToStaticMarkup(React.createElement(g.GuessWarningChip, { res: en })), /Taxminan bosilgan/);
    // Eski sessiya — maydonlar yo'q: hech narsa.
    assert.equal(g.guessSummary({ score: 3, skills: [{ key: 'grammar', label: 'Grammatika' }] }), null);
    assert.equal(renderToStaticMarkup(React.createElement(g.GuessStats, { res: { score: 3 } })), '');
    assert.equal(renderToStaticMarkup(React.createElement(g.GuessWarningChip, { res: { score: 3 } })), '');
    // Nemis/rus: skills[].skill; deploydan oldingi yozuv timed=false -> "Juda tez: —".
    const de = { idk: 2, fast: 0, guess_warning: false, timed: false, skills: [{ skill: 'grammar', label: 'Grammatika', idk: 2, fast: 0 }] };
    html = renderToStaticMarkup(React.createElement(g.GuessStats, { res: de }));
    assert.match(html, /Bilmayman: 2 · Juda tez: —/); assert.match(html, /o(&#x27;|')lchanmagan/);
    assert.doesNotMatch(html, /Taxminan bosilgan/);
    // Ingliz: deploydan oldin tugagan sessiya — idk/fast null, timed=false:
    // "0" emas, "—" va "eski test" izohi (toza sessiyadek ko'rinmasin).
    const enOld = { idk: null, fast: null, guess_warning: false, timed: false, skills: [
      { key: 'grammar', label: 'Grammatika', idk: null, fast: null }, { key: 'vocab', label: "Lug'at", idk: null, fast: null }] };
    html = renderToStaticMarkup(React.createElement(g.GuessStats, { res: enOld }));
    assert.match(html, /Bilmayman: — · Juda tez: —/); assert.match(html, /o(&#x27;|')lchanmagan/);
    assert.doesNotMatch(html, /Bilmayman: 0/);
    assert.equal(renderToStaticMarkup(React.createElement(g.GuessWarningChip, { res: enOld })), '');
    // Obyekt ko'rinishi {total, bo'lim: n}.
    const obj = g.guessSummary({ idk: { total: 3, grammar: 2, reading: 1 }, fast: { grammar: 5 } });
    assert.equal(obj.idk, 3); assert.equal(obj.fast, 5);
    assert.equal(JSON.stringify(obj.sections.map(x => [x.key, x.idk, x.fast])), JSON.stringify([['grammar', 2, 5], ['reading', 1, 0]]));
  }
  console.log('PASS: seq start/answer(-1, 5th option)/stale/save state-only, legacy fallback + answers, resume via /current, broken state restart, choices with last Bilmayman, staff Bilmayman/Juda tez counts + warning, old sessions hidden.');
})().catch(e => { console.error(e); process.exitCode = 1; });
