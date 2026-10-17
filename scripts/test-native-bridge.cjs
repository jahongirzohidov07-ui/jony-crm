// Run from any directory: node <repo>/scripts/test-native-bridge.cjs
const assert = require('node:assert/strict');
const { test } = require('node:test');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const filename = path.resolve(__dirname, '../src/lib/nativeBridge.ts');
const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
  fileName: filename,
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
}).outputText;

function setup(overrides = {}) {
  const calls = { start: [], stop: [], speak: [], cancel: 0 };
  // Observe registrations to simulate callbacks for queued (not yet dispatched) IDs.
  const registered = [];
  class ObservedMap extends Map {
    set(id, value) { registered.push(id); return super.set(id, value); }
  }
  const app = {
    isNative: () => true,
    startListening: (...args) => calls.start.push(args),
    stopListening: (...args) => calls.stop.push(args),
    speak: (...args) => calls.speak.push(args),
    stopSpeaking: () => { calls.cancel++; },
    ...overrides,
  };
  const window = { JonyApp: app };
  const exports = {};
  vm.runInNewContext(compiled, {
    window, exports, Map: ObservedMap,
    document: { documentElement: { classList: { add() {} } } },
  }, { filename });
  exports.installNativeBridge();
  return { window, app, calls, registered };
}
function watchRecognition(window) {
  const rec = new window.SpeechRecognition();
  const events = [];
  rec.onstart = () => events.push(['start']);
  rec.onerror = e => events.push(['error', e.error]);
  rec.onend = () => events.push(['end']);
  rec.onresult = e => events.push(['result', e.resultIndex,
    Array.from(e.results, r => [r[0].transcript, r.isFinal])]);
  return { rec, events };
}
function utterance(window, text) {
  const u = new window.SpeechSynthesisUtterance(text);
  const events = [];
  for (const type of ['start', 'end', 'error']) u['on' + type] = () => events.push(type);
  return { u, events };
}

test('recognition start throw emits error/end, detaches old callbacks, and permits retry', () => {
  const h = setup();
  const { rec, events } = watchRecognition(h.window);
  let failedId;
  h.app.startListening = id => { failedId = id; throw new Error('transport unavailable'); };
  rec.start();
  assert.deepEqual(events, [['error', 'not-allowed'], ['end']]);
  h.app.startListening = (...args) => h.calls.start.push(args);
  rec.start();
  const id = h.calls.start[0][0];
  assert.notEqual(id, failedId);
  h.window.__jonySr(failedId, 'final', 'stale');
  h.window.__jonySr(failedId, 'end');
  h.window.__jonySr(id, 'start');
  h.window.__jonySr(id, 'final', 'retry works');
  h.window.__jonySr(id, 'end');
  assert.deepEqual(events, [['error', 'not-allowed'], ['end'], ['start'],
    ['result', 0, [['retry works', true]]], ['end']]);
});

test('recognition stop preserves synchronous final and previously accumulated finals', () => {
  const h = setup();
  const { rec, events } = watchRecognition(h.window);
  rec.lang = 'en-GB'; rec.interimResults = true;
  rec.start();
  const id = h.calls.start[0][0];
  assert.deepEqual(h.calls.start[0].slice(1), ['en-GB', true]);
  h.window.__jonySr(id, 'final', 'first');
  h.app.stopListening = stopped => {
    assert.equal(stopped, id);
    h.window.__jonySr(id, 'final', 'last');
    h.window.__jonySr(id, 'end');
  };
  rec.stop();
  assert.deepEqual(events, [['result', 0, [['first', true]]],
    ['result', 1, [['first', true], ['last', true]]], ['end']]);
});

test('recognition stop keeps asynchronous final alive until native end', () => {
  const h = setup();
  const { rec, events } = watchRecognition(h.window);
  rec.start(); rec.stop();
  const id = h.calls.start[0][0];
  assert.deepEqual(h.calls.stop, [[id]]);
  assert.deepEqual(events, []);
  h.window.__jonySr(id, 'final', 'late final');
  h.window.__jonySr(id, 'end');
  assert.deepEqual(events, [['result', 0, [['late final', true]]], ['end']]);
});

test('recognition abort ignores synchronous and late callbacks, ends once, and permits retry', () => {
  const h = setup();
  const { rec, events } = watchRecognition(h.window);
  rec.start();
  const old = h.calls.start[0][0];
  h.app.stopListening = id => {
    h.calls.stop.push([id]);
    h.window.__jonySr(id, 'final', 'synchronous stale');
    h.window.__jonySr(id, 'end');
  };
  rec.abort(); rec.abort();
  rec.start();
  for (const type of ['start', 'partial', 'final', 'error', 'end']) h.window.__jonySr(old, type, 'stale');
  const id = h.calls.start[1][0];
  h.window.__jonySr(id, 'final', 'new session');
  h.window.__jonySr(id, 'end');
  assert.deepEqual(h.calls.stop, [[old]]);
  assert.deepEqual(events, [['end'], ['result', 0, [['new session', true]]], ['end']]);
});

test('recognition stop transport throw releases the session for retry', () => {
  const h = setup({ stopListening() { throw new Error('disconnected'); } });
  const { rec, events } = watchRecognition(h.window);
  rec.start(); rec.stop(); rec.start();
  assert.equal(h.calls.start.length, 2);
  assert.deepEqual(events, [['error', 'network'], ['end']]);
});

test('TTS cancel invalidates active and queued callbacks before native stop, then recovers', () => {
  const h = setup();
  const synth = h.window.speechSynthesis;
  const a = utterance(h.window, 'active'), b = utterance(h.window, 'queued');
  synth.speak(a.u); synth.speak(b.u);
  const ids = h.registered.slice();
  assert.equal(ids.length, 2);
  assert.equal(synth.speaking, true); assert.equal(synth.pending, true);
  const stale = () => { for (const id of ids) for (const type of ['start', 'error', 'end']) h.window.__jonyTts(id, type); };
  h.app.stopSpeaking = () => { h.calls.cancel++; stale(); };
  synth.cancel(); stale();
  assert.equal(synth.speaking, false); assert.equal(synth.pending, false);
  assert.deepEqual(a.events, ['end']); assert.deepEqual(b.events, []);
  assert.equal(h.calls.speak.length, 1); assert.equal(h.calls.cancel, 1);
  const c = utterance(h.window, 'fresh'); synth.speak(c.u);
  const id = h.calls.speak[1][0];
  stale(); assert.equal(synth.speaking, true);
  h.window.__jonyTts(id, 'start'); h.window.__jonyTts(id, 'end');
  assert.deepEqual(c.events, ['start', 'end']); assert.equal(synth.speaking, false);
});

test('TTS speak throw reports error, clears busy state, and accepts a later utterance', () => {
  const h = setup({ speak() { throw new Error('unavailable'); } });
  const synth = h.window.speechSynthesis;
  const a = utterance(h.window, 'fails'); synth.speak(a.u);
  const old = h.registered[0];
  assert.deepEqual(a.events, ['error']);
  assert.equal(synth.speaking, false); assert.equal(synth.pending, false);
  h.app.speak = (...args) => h.calls.speak.push(args);
  const b = utterance(h.window, 'works'); synth.speak(b.u);
  h.window.__jonyTts(old, 'end');
  assert.equal(synth.speaking, true);
  h.window.__jonyTts(h.calls.speak[0][0], 'end');
  assert.deepEqual(b.events, ['end']); assert.equal(synth.speaking, false);
});

test('TTS throw handler can cancel and start replacement without losing its busy state or queue', () => {
  const h = setup();
  const synth = h.window.speechSynthesis;
  const a = utterance(h.window, 'fails'), b = utterance(h.window, 'replacement'), c = utterance(h.window, 'next');
  h.app.speak = (...args) => { h.calls.speak.push(args); if (args[1] === 'fails') throw new Error('failure'); };
  a.u.onerror = () => { a.events.push('error'); synth.cancel(); synth.speak(b.u); synth.speak(c.u); };
  synth.speak(a.u);
  assert.deepEqual(h.calls.speak.map(args => args[1]), ['fails', 'replacement']);
  assert.equal(synth.speaking, true); assert.equal(synth.pending, true);
  h.window.__jonyTts(h.calls.speak[1][0], 'end');
  assert.deepEqual(h.calls.speak.map(args => args[1]), ['fails', 'replacement', 'next']);
  assert.equal(synth.speaking, true); assert.equal(synth.pending, false);
  h.window.__jonyTts(h.calls.speak[2][0], 'end');
  assert.deepEqual(a.events, ['error']); assert.deepEqual(b.events, ['end']); assert.deepEqual(c.events, ['end']);
  assert.equal(synth.speaking, false);
});
