import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { BrandIcon } from "../components/BrandIcon";

/**
 * JONLI O'YIN — O'QUVCHI EKRANI (loginsiz), 2026-09-18.
 *
 * Jahongir: "kahoot korinishidagi oyinlar ... link bilan QR kod bilan
 * live oynasa boladigan qilib hamma togri topgan bilan kim tez bossa
 * shu oldinga chiqadigan achkoni koproq beradigan bolsin".
 *
 * Havola: jonyos.uz/play?code=123456. O'quvchi ismini yozadi, ustoz
 * ekranidagi savolga telefonida 4 rangli tugmadan birini bosadi.
 * Server 1 soniyada so'raladi (Vercel'da websocket yo'q).
 */

type Q = { index: number; total: number; kind: string; prompt: string;
  sub?: string | null; options: string[]; seconds: number };
type Top = { id: number; nickname: string; score: number; rank: number;
  student_id?: number | null; coins?: number; correct?: number };
type Lobby = { title: string; status: string; group: string | null;
  students: { id: number; name: string; taken: boolean }[] };
type State = {
  status: "lobby" | "question" | "reveal" | "ended";
  title: string; nickname: string; score: number; rank: number | null;
  players: number; q_index: number; total: number;
  question?: Q; elapsed_ms?: number; answered?: number | null;
  reveal?: { prompt: string; options: string[]; correct: number; explain?: string | null;
    my_option: number | null; is_correct: boolean; points: number };
  top?: Top[];
  coins?: number; correct?: number; linked?: boolean;
};

const TOKEN_KEY = "jony_live_token";
/** Kahoot'dagi kabi 4 rang + shakl — o'qiy olmaydigan kichkina bola
 * ham rang bo'yicha bosadi. */
export const OPT = [
  { bg: "bg-rose-500", sym: "▲" },
  { bg: "bg-sky-600", sym: "◆" },
  { bg: "bg-amber-500", sym: "●" },
  { bg: "bg-emerald-600", sym: "■" },
];

async function call<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = (data as { detail?: unknown }).detail;
    throw new Error(typeof d === "string" ? d : "Xato");
  }
  return data as T;
}

export default function Play() {
  const [params] = useSearchParams();
  const [code, setCode] = useState(params.get("code") ?? "");
  const [nick, setNick] = useState("");
  const [token, setToken] = useState<string | null>(
    () => sessionStorage.getItem(TOKEN_KEY));
  const [st, setSt] = useState<State | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [picked, setPicked] = useState<number | null>(null);
  const [gone, setGone] = useState(0); // savol boshidan o'tgan ms
  const [lobby, setLobby] = useState<Lobby | null>(null); // ro'yxat (ism tanlash)
  const [other, setOther] = useState(false);              // "Boshqa ism" rejimi
  const seenQ = useRef<number>(-1);
  const startedAt = useRef<number>(0);

  const poll = useCallback(async () => {
    if (!token) return;
    try {
      const s = await call<State>(`/live/p/${token}`);
      setSt(s);
      if (s.status === "question" && s.question && s.q_index !== seenQ.current) {
        seenQ.current = s.q_index;
        setPicked(s.answered ?? null);
        startedAt.current = Date.now() - (s.elapsed_ms ?? 0);
      }
    } catch (e) {
      const m = (e as Error).message;
      if (/topilmadi/.test(m)) { sessionStorage.removeItem(TOKEN_KEY); setToken(null); setSt(null); }
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    poll();
    const t = setInterval(poll, 1000);
    return () => clearInterval(t);
  }, [token, poll]);

  // Vaqt chizig'i (100 ms da yangilanadi)
  useEffect(() => {
    if (st?.status !== "question") return;
    const t = setInterval(() => setGone(Date.now() - startedAt.current), 100);
    return () => clearInterval(t);
  }, [st?.status, st?.q_index]);

  // 1-qadam: PIN -> guruh o'quvchilari ro'yxati (2026-09-18, Jahongir:
  // "o'quvchilar royxatidagi ism familyalardan birini tanlashsin agar
  // yoq bolsa boshqa yozadigan bolishi kerak").
  async function lookup() {
    setErr(""); setBusy(true);
    try {
      const l = await call<Lobby>(`/live/lobby/${code}`);
      if (l.status !== "lobby") throw new Error("O'yin allaqachon boshlangan");
      setLobby(l); setOther(l.students.length === 0);
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

  async function join(studentId?: number) {
    setErr(""); setBusy(true);
    try {
      const r = await call<{ token: string }>("/live/join",
        studentId ? { code, student_id: studentId } : { code, nickname: nick });
      sessionStorage.setItem(TOKEN_KEY, r.token);
      seenQ.current = -1;
      setToken(r.token);
    } catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  }

  async function answer(i: number) {
    if (!token || !st?.question || picked !== null) return;
    setPicked(i);
    try {
      await call(`/live/p/${token}/answer`, { q_index: st.q_index, option: i });
    } catch (e) { setErr((e as Error).message); }
  }

  function leave() {
    sessionStorage.removeItem(TOKEN_KEY); setToken(null); setSt(null); seenQ.current = -1;
  }

  // ---------- Kirish ekrani ----------
  if (!token) {
    return (
      <Shell>
        <div className="w-full max-w-sm mx-auto bg-white rounded-2xl shadow-xl p-6 mt-8">
          <div className="flex items-center gap-2 mb-4">
            <BrandIcon size={34} />
            <div>
              <div className="font-bold text-slate-900 leading-tight">Jony Academy</div>
              <div className="text-xs text-slate-500">Jonli o'yin</div>
            </div>
          </div>
          <label className="block text-xs font-medium text-slate-600 mb-1">O'yin PIN kodi</label>
          <input value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                 inputMode="numeric" placeholder="123456"
                 className="w-full text-center text-3xl tracking-[0.3em] font-bold border-2 border-slate-200 rounded-xl px-3 py-3 mb-3 focus:border-brand-500 outline-none" />
          {!lobby ? (
            <>
              {err && <div className="text-sm text-rose-600 mb-2">{err}</div>}
              <button onClick={lookup} disabled={busy || code.length < 6}
                      className="w-full bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white font-semibold rounded-xl py-3 text-lg">
                Davom etish
              </button>
            </>
          ) : (
            <>
              <div className="text-xs text-slate-500 mb-2">{lobby.title}{lobby.group ? ` · ${lobby.group}` : ""}</div>
              {!other && (
                <>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Ro'yxatdan ismingizni tanlang</label>
                  <div className="max-h-64 overflow-y-auto border border-slate-200 rounded-xl divide-y divide-slate-100 mb-2">
                    {lobby.students.map((s) => (
                      <button key={s.id} disabled={s.taken || busy} onClick={() => join(s.id)}
                              className="w-full text-left px-3 py-2.5 text-sm hover:bg-brand-50 disabled:opacity-40 disabled:line-through">
                        {s.name}
                      </button>
                    ))}
                  </div>
                  <button onClick={() => setOther(true)} className="text-xs text-brand-600 underline mb-2">Ismim ro'yxatda yo'q — boshqa ism yozaman</button>
                </>
              )}
              {other && (
                <>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Ismingiz</label>
                  <input value={nick} onChange={(e) => setNick(e.target.value)} maxLength={24}
                         placeholder="Masalan: Aziz" onKeyDown={(e) => e.key === "Enter" && join()}
                         className="w-full text-lg border-2 border-slate-200 rounded-xl px-3 py-2.5 mb-2 focus:border-brand-500 outline-none" />
                  <div className="text-[11px] text-slate-400 mb-2">Eslatma: ro'yxatdan tanlanmagan ishtirokchiga coin yozilmaydi.</div>
                  {lobby.students.length > 0 && <button onClick={() => setOther(false)} className="text-xs text-brand-600 underline mb-2">Ro'yxatga qaytish</button>}
                </>
              )}
              {err && <div className="text-sm text-rose-600 mb-2">{err}</div>}
              {other && (
                <button onClick={() => join()} disabled={busy || nick.trim().length < 2}
                        className="w-full bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white font-semibold rounded-xl py-3 text-lg">
                  Kirish
                </button>
              )}
            </>
          )}
        </div>
      </Shell>
    );
  }

  if (!st) return <Shell><p className="text-white/80 text-center mt-16">Ulanmoqda…</p></Shell>;

  // ---------- Kutish ----------
  if (st.status === "lobby") {
    return (
      <Shell>
        <Card>
          <div className="text-xs text-slate-500 mb-1">{st.title}</div>
          <div className="text-2xl font-bold text-slate-900 mb-2">Salom, {st.nickname}! 👋</div>
          <p className="text-slate-600">Siz o'yindasiz. Ustoz boshlashini kuting…</p>
          <div className="mt-4 text-sm text-slate-500">O'yinchilar: <b>{st.players}</b></div>
          <div className="mt-6 flex justify-center"><Spinner /></div>
          <button onClick={leave} className="mt-6 text-xs text-slate-400 underline">Chiqish</button>
        </Card>
      </Shell>
    );
  }

  // ---------- Savol ----------
  if (st.status === "question" && st.question) {
    const q = st.question;
    const total = q.seconds * 1000;
    const left = Math.max(0, total - gone);
    const pct = Math.round((left / total) * 100);
    return (
      <Shell>
        <div className="w-full max-w-md mx-auto">
          <div className="flex items-center justify-between text-white/90 text-sm mb-2">
            <span>{q.index + 1} / {q.total}</span>
            <span className="font-semibold">{st.nickname} · {st.score} ball</span>
          </div>
          <div className="h-2 bg-white/20 rounded-full overflow-hidden mb-3">
            <div className="h-full bg-white transition-[width] duration-100" style={{ width: pct + "%" }} />
          </div>
          <div className="bg-white rounded-2xl shadow-xl p-4 mb-3">
            <div className="text-lg font-semibold text-slate-900 leading-snug">{q.prompt}</div>
            {q.sub && <div className="text-xs text-slate-500 mt-1">{q.sub}</div>}
          </div>
          {picked === null ? (
            <div className="grid grid-cols-1 gap-2">
              {q.options.map((o, i) => (
                <button key={i} onClick={() => answer(i)}
                        className={`${OPT[i % 4].bg} text-white rounded-2xl px-4 py-4 text-left text-lg font-semibold shadow-lg active:scale-[0.98] flex items-center gap-3`}>
                  <span className="text-2xl opacity-90">{OPT[i % 4].sym}</span>
                  <span>{o}</span>
                </button>
              ))}
            </div>
          ) : (
            <Card>
              <div className="text-3xl mb-2">✅</div>
              <div className="font-semibold text-slate-900">Javob qabul qilindi!</div>
              <p className="text-sm text-slate-500 mt-1">Natijani ustoz ekranida kuting…</p>
              <div className="mt-4 flex justify-center"><Spinner /></div>
            </Card>
          )}
          {err && <div className="text-sm text-white bg-rose-600/80 rounded-lg px-3 py-2 mt-2">{err}</div>}
        </div>
      </Shell>
    );
  }

  // ---------- Natija (reveal) ----------
  if (st.status === "reveal" && st.reveal) {
    const r = st.reveal;
    return (
      <Shell>
        <div className="w-full max-w-md mx-auto">
          <Card tone={r.is_correct ? "good" : "bad"}>
            <div className="text-4xl mb-1">{r.is_correct ? "🎉" : "😕"}</div>
            <div className="text-2xl font-bold">{r.is_correct ? "To'g'ri!" : (r.my_option === null ? "Javob berilmadi" : "Noto'g'ri")}</div>
            <div className="text-lg mt-1">+{r.points} ball</div>
            <div className="text-sm mt-3 opacity-90">
              To'g'ri javob: <b>{r.options[r.correct]}</b>
            </div>
            {r.explain && <div className="text-xs mt-1 opacity-80">{r.explain}</div>}
          </Card>
          <Card>
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Sizning o'rningiz</span>
              <span className="text-2xl font-bold text-slate-900">#{st.rank ?? "–"}</span>
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-slate-600">Jami ball</span>
              <span className="text-xl font-semibold text-brand-600">{st.score}</span>
            </div>
          </Card>
          <Board rows={st.top ?? []} me={st.nickname} />
        </div>
      </Shell>
    );
  }

  // ---------- Yakun ----------
  return (
    <Shell>
      <div className="w-full max-w-md mx-auto">
        <Card>
          <div className="text-4xl mb-1">🏆</div>
          <div className="text-2xl font-bold text-slate-900">O'yin tugadi</div>
          <div className="text-slate-600 mt-1">{st.nickname}, siz <b>#{st.rank ?? "–"}</b> o'rindasiz — {st.score} ball · {st.correct ?? 0}/{st.total} to'g'ri</div>
          {st.linked ? (
            <div className="mt-2 text-lg font-semibold text-amber-600">🪙 +{st.coins ?? 0} coin{(st.coins ?? 0) ? " hisobingizga qo'shildi" : ""}</div>
          ) : (
            <div className="mt-2 text-xs text-slate-400">Coin faqat ro'yxatdan tanlangan o'quvchilarga beriladi.</div>
          )}
        </Card>
        <Board rows={st.top ?? []} me={st.nickname} />
        <button onClick={leave} className="mt-4 w-full bg-white/90 text-slate-800 font-semibold rounded-xl py-3">
          Yangi o'yinga kirish
        </button>
      </div>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-brand-600 to-indigo-700 px-4 py-5">
      {children}
      <div className="text-center text-white/60 text-xs mt-8">Jony Academy · jonyos.uz</div>
    </div>
  );
}

function Card({ children, tone }: { children: React.ReactNode; tone?: "good" | "bad" }) {
  const cls = tone === "good" ? "bg-emerald-500 text-white" : tone === "bad" ? "bg-rose-500 text-white" : "bg-white text-slate-800";
  return <div className={`${cls} rounded-2xl shadow-xl p-5 text-center mb-3 max-w-md mx-auto w-full`}>{children}</div>;
}

function Spinner() {
  return <div className="w-8 h-8 border-4 border-brand-100 border-t-brand-600 rounded-full animate-spin" />;
}

export function Board({ rows, me, showCoins }: { rows: Top[]; me?: string; showCoins?: boolean }) {
  if (!rows.length) return null;
  const medal = ["🥇", "🥈", "🥉"];
  return (
    <div className="bg-white rounded-2xl shadow-xl p-4">
      <div className="text-xs font-semibold text-slate-500 uppercase mb-2">Reyting</div>
      {rows.map((r) => (
        <div key={r.id} className={`flex items-center justify-between py-1.5 border-b border-slate-100 last:border-0 ${r.nickname === me ? "font-bold text-brand-600" : "text-slate-800"}`}>
          <span className="flex items-center gap-2">
            <span className="w-7 text-center">{medal[r.rank - 1] ?? r.rank}</span>
            {r.nickname}
          </span>
          <span className="tabular-nums">{r.score}{showCoins && r.coins ? <span className="text-amber-600 text-xs ml-2">🪙 +{r.coins}</span> : null}</span>
        </div>
      ))}
    </div>
  );
}
