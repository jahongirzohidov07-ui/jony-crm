import { useEffect, useState } from 'react';

// KETMA-KET KIRISH TESTI — nemis va rus (2026-10-22).
//
// Egasi: "diagnostik testda hech narsani bilmay taxminan bosib
// tashlaydiganlarning darajasi baland chiqyapti". Shuning uchun savollar
// endi SERVERDAN bittadan beriladi va faqat oldinga yuriladi: har javob
// kelgan vaqtni server o'zi o'lchaydi (savolni o'qishga yetmaydigan
// darajada tez bosilgan to'g'ri javob ham xato). Mijoz hech qanday vaqt
// yubormaydi va javob kalitini ko'rmaydi.
//
// Server shartnomasi (api/placement_guard.py, SeqTest):
//   POST {base}/start   {attempt_id}                     -> Step
//   POST {base}/answer  {attempt_id, state, qid, choice} -> Step
//   POST {base}/current {attempt_id, state}              -> Step (vaqt qayta boshlanmaydi)
//   POST {base}         {full_name, phone, branch_id, attempt_id, state}
//                                                        -> {saved, result}
//   (legacy: state o'rniga answers {qid: choice} — 48 ta)
//   Step = {state, question | null, done, answered, total, stale?}
//   choice: haqiqiy variant indeksi yoki -1 = "Bilmayman" (xato hisoblanadi).
//   "state" — server shifrlagan va imzolagan holat; sahifa uni o'qimaydi,
//   faqat qaytarib yuboradi.
//
// Deploydan oldin boshlangan urinishlar (sessionStorage'da state yo'q) va
// /start bo'lmagan eski server — "legacy": bugungidek javoblar oxirida
// birdan yuboriladi; serverda vaqt yo'q, "juda tez" qoidasi qo'llanmaydi.
// Server bu yo'lni faqat roles.PLACEMENT_LEGACY_SUBMIT_UNTIL gacha qabul
// qiladi, keyin 409 "Sahifani yangilang" — "Yangi o'quvchi uchun test"
// tugmasi bilan qaytadan (seq rejimida) boshlanadi.

export type Identity = { full_name: string; phone: string; branch_id: number };
export type SeqSkill = 'grammar' | 'vocabulary' | 'reading';
export type SeqQuestion = {
  id: string; prompt: string; options: string[]; text?: string; skill: SeqSkill; topic?: string;
  month?: number; stage?: number; index?: number; no?: number; total?: number; idk?: boolean;
};
export type SeqStep = {
  state: string; question: SeqQuestion | null; done: boolean; answered?: number; total?: number; stale?: boolean;
};
export type SeqMode = 'seq' | 'legacy';
export type SeqAttempt<R> = {
  answers: Record<string, number>; index: number; started: boolean; done: boolean;
  identity?: Identity; attemptId?: string; mode?: SeqMode; state?: string; result?: R;
};

export class PlacementHttpError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

export async function placementRequest<T>(base: string, path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...(body !== undefined ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}), signal,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new PlacementHttpError(typeof data?.detail === 'string' ? data.detail : "Ma'lumotlarni tekshirib qayta urinib ko'ring.", response.status);
  }
  return data as T;
}

/** Yo'l serverda umuman yo'q (FastAPI standart javobi) — eski server. */
export function isRouteMissing(e: unknown): boolean {
  return e instanceof PlacementHttpError && (e.status === 404 || e.status === 405)
    && (e.message === 'Not Found' || e.message === 'Method Not Allowed');
}

export function errorText(e: unknown, fallback = "Xatolik. Qayta urinib ko'ring."): string {
  if (e instanceof TypeError || (e instanceof Error && e.name === 'AbortError')) return "Internet bilan aloqa uzildi. Qayta urinib ko'ring.";
  return e instanceof Error && e.message ? e.message : fallback;
}

export const seqStart = (base: string, attemptId: string, signal?: AbortSignal) =>
  placementRequest<SeqStep>(base, '/start', { attempt_id: attemptId }, signal);
export const seqAnswer = (base: string, attemptId: string, state: string, qid: string, choice: number, signal?: AbortSignal) =>
  placementRequest<SeqStep>(base, '/answer', { attempt_id: attemptId, state, qid, choice }, signal);
export const seqCurrent = (base: string, attemptId: string, state: string, signal?: AbortSignal) =>
  placementRequest<SeqStep>(base, '/current', { attempt_id: attemptId, state }, signal);

const UUID = /^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i;
export const emptyAttempt = <R,>(): SeqAttempt<R> => ({ answers: {}, index: 0, started: false, done: false });

/** sessionStorage'dagi urinishni tekshirib tiklaydi. Javob -1 ("Bilmayman")
 *  yoki 0..9 (4–5 variant) bo'lishi mumkin. */
export function restoreAttempt<R>(storageKey: string, total: number, ids?: string[]): SeqAttempt<R> {
  try {
    const v = JSON.parse(sessionStorage.getItem(storageKey) || 'null');
    if (!v || typeof v !== 'object' || !v.answers || typeof v.answers !== 'object') return emptyAttempt();
    const answers: Record<string, number> = {};
    for (const [id, value] of Object.entries(v.answers as Record<string, unknown>)) {
      if ((!ids || ids.includes(id)) && Number.isInteger(value) && (value as number) >= -1 && (value as number) <= 9) answers[id] = value as number;
    }
    const id = v.identity;
    const identity = id && typeof id.full_name === 'string' && typeof id.phone === 'string' && Number.isInteger(id.branch_id) ? id as Identity : undefined;
    const attemptId = typeof v.attemptId === 'string' && UUID.test(v.attemptId) ? v.attemptId : undefined;
    const seq = v.mode === 'seq' && typeof v.state === 'string' && !!v.state && !!attemptId && !!identity;
    const index = Number.isInteger(v.index) && v.index >= 0 && v.index < total ? v.index : 0;
    const result = v.result && typeof v.result === 'object' ? v.result as R : undefined;
    if (seq) return { answers, index: 0, started: true, done: v.done === true, identity, attemptId, mode: 'seq', state: v.state, result };
    // Legacy: deploydan oldingi urinishlar (mode yo'q) ham shu yerda davom etadi.
    return { answers, index, started: !!v.started || !!identity, identity, attemptId, mode: 'legacy',
      done: v.done === true && Object.keys(answers).length === total, result };
  } catch { return emptyAttempt(); }
}

/** Nemis va rus sahifalari uchun umumiy holat: ro'yxatdan o'tish, savolni
 *  serverdan olish, javob yuborish, sahifa yangilanganda davom etish va
 *  yakunda CRMga saqlash. */
export function useSeqPlacement<R>({ base, storageKey, total, ids }: {
  base: string; storageKey: string; total: number; ids?: string[];
}) {
  const [attempt, setAttempt] = useState<SeqAttempt<R>>(() => restoreAttempt<R>(storageKey, total, ids));
  const [question, setQuestion] = useState<SeqQuestion | null>(null);
  const [pick, setPick] = useState<number | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [stepError, setStepError] = useState('');
  const [stateBroken, setStateBroken] = useState(false);
  const [resume, setResume] = useState(0);
  const [saving, setSaving] = useState(false), [saveError, setSaveError] = useState(''), [retry, setRetry] = useState(0);
  const [storageError, setStorageError] = useState(false);

  useEffect(() => {
    try { sessionStorage.setItem(storageKey, JSON.stringify(attempt)); } catch { setStorageError(true); }
  }, [attempt, storageKey]);

  function apply(step: SeqStep, answered?: { qid: string; choice: number }) {
    const finished = !!step.done || !step.question;
    setAttempt(a => ({
      ...a, state: step.state, done: finished,
      answers: answered && !step.stale ? { ...a.answers, [answered.qid]: answered.choice } : a.answers,
    }));
    setQuestion(finished ? null : step.question);
    setPick(undefined);
  }

  function fail(e: unknown) {
    // 400 — holat buzilgan, 409 — boshqa urinishniki: qaytadan boshlash kerak.
    setStateBroken(e instanceof PlacementHttpError && (e.status === 400 || e.status === 409));
    setStepError(errorText(e));
  }

  // Sahifa yangilangan: joriy savolni qayta so'raymiz (soat qayta boshlanmaydi).
  useEffect(() => {
    if (attempt.mode !== 'seq' || !attempt.started || attempt.done || !attempt.state || !attempt.attemptId || question) return;
    let active = true;
    const controller = new AbortController();
    setBusy(true); setStepError('');
    seqCurrent(base, attempt.attemptId, attempt.state, controller.signal)
      .then(step => { if (active) apply(step); })
      .catch(e => { if (active) fail(e); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; controller.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt.mode, attempt.started, attempt.done, attempt.state, attempt.attemptId, question, resume, base]);

  // Yakunda natija CRMga saqlanadi. Seq rejimida FAQAT "state" yuboriladi:
  // javoblar va "juda tez" belgilari server tokenidan olinadi (answers
  // yuborilsa server uni 48 ta deb tekshiradi). Legacy — answers bilan.
  useEffect(() => {
    if (!attempt.done || !attempt.identity || !attempt.attemptId || attempt.result) return;
    let active = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    setSaving(true); setSaveError('');
    const body: Record<string, unknown> = { ...attempt.identity, attempt_id: attempt.attemptId };
    if (attempt.mode === 'seq' && attempt.state) body.state = attempt.state;
    else body.answers = attempt.answers;
    placementRequest<{ saved: boolean; result: R }>(base, '', body, controller.signal)
      .then(d => { if (active) setAttempt(a => ({ ...a, result: d.result })); })
      .catch(e => { if (active) setSaveError(errorText(e, "Natija saqlanmadi. Qayta yuboring.")); })
      .finally(() => { clearTimeout(timeout); if (active) setSaving(false); });
    return () => { active = false; clearTimeout(timeout); controller.abort(); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt.done, attempt.identity, attempt.attemptId, attempt.result, retry, base]);

  /** Ro'yxatdan o'tgach: server 1-savolni beradi. /start yo'q bo'lsa — legacy. */
  async function start(identity: Identity) {
    if (busy) return;
    const attemptId = crypto.randomUUID();
    setBusy(true); setStepError(''); setStateBroken(false); setSaveError('');
    try {
      const step = await seqStart(base, attemptId);
      setAttempt({ ...emptyAttempt<R>(), started: true, identity, attemptId, mode: 'seq', state: step.state });
      apply(step);
    } catch (e) {
      if (isRouteMissing(e)) {
        setAttempt({ ...emptyAttempt<R>(), started: true, identity, attemptId, mode: 'legacy' });
        setQuestion(null);
      } else fail(e);
    } finally { setBusy(false); }
  }

  /** Tanlangan javobni yuboradi ("Keyingi"). */
  async function answer() {
    if (busy || !question || pick === undefined || !attempt.state || !attempt.attemptId) return;
    const sent = { qid: question.id, choice: pick };
    setBusy(true); setStepError('');
    try { apply(await seqAnswer(base, attempt.attemptId, attempt.state, sent.qid, sent.choice), sent); }
    catch (e) { fail(e); }
    finally { setBusy(false); }
  }

  /** Xatodan keyin: holat buzilgan bo'lsa test qaytadan, aks holda savolni qayta so'raymiz. */
  function recover() {
    if (stateBroken && attempt.identity) { void start(attempt.identity); return; }
    setStepError(''); setQuestion(null); setResume(n => n + 1);
  }

  function reset() {
    setAttempt(emptyAttempt<R>()); setQuestion(null); setPick(undefined);
    setStepError(''); setStateBroken(false); setSaveError(''); setSaving(false);
  }

  return { attempt, setAttempt, question, pick, setPick, busy, stepError, stateBroken, start, answer, recover, reset,
    saving, saveError, retrySave: () => setRetry(n => n + 1), storageError };
}
