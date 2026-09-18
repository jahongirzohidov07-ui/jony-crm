import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import QRCode from "qrcode";
import { Users, Play as PlayIcon, ChevronRight, XCircle, ArrowLeft } from "lucide-react";
import { api } from "../lib/api";
import { BrandIcon } from "../components/BrandIcon";
import { OPT, Board } from "./Play";

/**
 * JONLI O'YIN — USTOZ (PROYEKTOR) EKRANI, 2026-09-18.
 *
 * Ustoz dars rejasidan o'yin ochadi, bu sahifani proyektorga chiqaradi:
 * PIN + QR + havola -> o'quvchilar telefondan kiradi -> savollar ->
 * har savoldan keyin to'g'ri javob, kim qancha bosgani va reyting.
 * Server 1.5 soniyada so'raladi; vaqt tugagach natija o'zi ochiladi.
 */

type Top = { id: number; nickname: string; score: number; rank: number };
type Host = {
  id: number; code: string; title: string; mode_label: string;
  status: "lobby" | "question" | "reveal" | "ended";
  q_index: number; total: number; seconds: number; elapsed_ms: number | null;
  question: { index: number; total: number; prompt: string; sub?: string | null; options: string[] } | null;
  correct: number | null; explain: string | null;
  counts: number[]; answered: number; players: Top[];
};

export default function LiveHost() {
  const { id } = useParams();
  const [st, setSt] = useState<Host | null>(null);
  const [qr, setQr] = useState("");
  const [gone, setGone] = useState(0);
  const [err, setErr] = useState("");
  const startedAt = useRef(0);
  const seenQ = useRef(-1);
  const autoRef = useRef(false);

  const joinUrl = `${window.location.origin}/play?code=${st?.code ?? ""}`;

  const poll = useCallback(async () => {
    try {
      const s = await api.fresh<Host>(`/live/games/${id}/host`);
      setSt(s);
      if (s.status === "question" && s.q_index !== seenQ.current) {
        seenQ.current = s.q_index;
        autoRef.current = false;
        startedAt.current = Date.now() - (s.elapsed_ms ?? 0);
      }
    } catch (e) { setErr((e as Error).message); }
  }, [id]);

  useEffect(() => {
    poll();
    const t = setInterval(poll, 1500);
    return () => clearInterval(t);
  }, [poll]);

  useEffect(() => {
    if (!st?.code) return;
    QRCode.toDataURL(joinUrl, { width: 320, margin: 1, color: { dark: "#0f172a" } })
      .then(setQr).catch(() => setQr(""));
  }, [st?.code, joinUrl]);

  async function step(path: "next" | "end") {
    try {
      const s = await api.post<Host>(`/live/games/${id}/${path}`);
      setSt(s);
      if (s.status === "question") {
        seenQ.current = s.q_index;
        autoRef.current = false;
        startedAt.current = Date.now();
      }
    } catch (e) { setErr((e as Error).message); }
  }

  // Sanoq va vaqt tugaganda (yoki hamma bosganda) avtomatik natija
  useEffect(() => {
    if (st?.status !== "question") return;
    const t = setInterval(() => {
      const g = Date.now() - startedAt.current;
      setGone(g);
      const allIn = st.players.length > 0 && st.answered >= st.players.length;
      if (!autoRef.current && (g > st.seconds * 1000 + 1500 || allIn)) {
        autoRef.current = true;
        step("next");
      }
    }, 200);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [st?.status, st?.q_index, st?.answered, st?.players.length]);

  if (!st) {
    return <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">{err || "Yuklanmoqda…"}</div>;
  }

  const leftMs = Math.max(0, st.seconds * 1000 - gone);
  const leftS = Math.ceil(leftMs / 1000);

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-600 via-indigo-700 to-slate-900 text-white">
      <header className="flex items-center justify-between px-6 py-3 bg-black/20">
        <div className="flex items-center gap-3">
          <BrandIcon size={30} />
          <div>
            <div className="font-bold leading-tight">{st.title}</div>
            <div className="text-xs text-white/70">{st.mode_label} · {st.total} savol · {st.seconds} soniya</div>
          </div>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="flex items-center gap-1"><Users size={16} /> {st.players.length}</span>
          <span className="font-mono text-lg tracking-widest bg-white/15 px-3 py-1 rounded-lg">PIN {st.code}</span>
          {st.status !== "ended" && (
            <button onClick={() => step("end")} className="text-white/70 hover:text-white flex items-center gap-1">
              <XCircle size={16} /> Tugatish
            </button>
          )}
          <Link to="/plans" className="text-white/70 hover:text-white flex items-center gap-1"><ArrowLeft size={16} /> Rejalar</Link>
        </div>
      </header>

      {err && <div className="mx-6 mt-3 bg-rose-500/80 rounded-lg px-3 py-2 text-sm">{err}</div>}

      {/* ---------- LOBBY ---------- */}
      {st.status === "lobby" && (
        <div className="grid md:grid-cols-2 gap-8 p-8 items-center max-w-6xl mx-auto">
          <div className="bg-white text-slate-900 rounded-3xl p-6 text-center shadow-2xl">
            <div className="text-sm text-slate-500">Telefondan kiring</div>
            <div className="text-2xl font-bold text-brand-600 break-all">{window.location.host}/play</div>
            <div className="text-sm text-slate-500 mt-4">O'yin PIN kodi</div>
            <div className="text-7xl font-black tracking-[0.15em] my-2">{st.code}</div>
            {qr && <img src={qr} alt="QR" className="mx-auto w-56 h-56 rounded-xl" />}
            <div className="text-xs text-slate-400 mt-2">QR kodni skanerlang yoki havolani oching</div>
          </div>
          <div>
            <div className="text-white/70 text-sm mb-2">O'yinchilar ({st.players.length})</div>
            <div className="flex flex-wrap gap-2 min-h-[8rem]">
              {st.players.map((p) => (
                <span key={p.id} className="bg-white/15 rounded-full px-4 py-2 text-lg font-semibold">{p.nickname}</span>
              ))}
              {!st.players.length && <span className="text-white/50">Hali hech kim kirmadi…</span>}
            </div>
            <button onClick={() => step("next")} disabled={!st.players.length}
                    className="mt-8 bg-white text-brand-700 disabled:opacity-40 font-bold text-xl rounded-2xl px-8 py-4 flex items-center gap-2 shadow-xl">
              <PlayIcon size={22} /> Boshlash
            </button>
          </div>
        </div>
      )}

      {/* ---------- SAVOL ---------- */}
      {st.status === "question" && st.question && (
        <div className="p-8 max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-3 text-white/80">
            <span className="text-lg">Savol {st.question.index + 1} / {st.total}</span>
            <span className="text-lg">Javob berdi: <b className="text-white">{st.answered}</b> / {st.players.length}</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex-1 bg-white text-slate-900 rounded-3xl p-8 shadow-2xl min-h-[9rem] flex flex-col justify-center">
              <div className="text-3xl md:text-4xl font-bold leading-snug">{st.question.prompt}</div>
              {st.question.sub && <div className="text-lg text-slate-500 mt-2">{st.question.sub}</div>}
            </div>
            <div className="w-28 h-28 rounded-full bg-white/15 flex items-center justify-center text-5xl font-black shrink-0">{leftS}</div>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-6">
            {st.question.options.map((o, i) => (
              <div key={i} className={`${OPT[i % 4].bg} rounded-2xl px-6 py-6 text-2xl font-semibold flex items-center gap-4 shadow-lg`}>
                <span className="text-3xl opacity-90">{OPT[i % 4].sym}</span>{o}
              </div>
            ))}
          </div>
          <button onClick={() => step("next")} className="mt-6 bg-white/15 hover:bg-white/25 rounded-xl px-5 py-2 flex items-center gap-1">
            Javoblarni ko'rsatish <ChevronRight size={18} />
          </button>
        </div>
      )}

      {/* ---------- NATIJA ---------- */}
      {st.status === "reveal" && st.question && (
        <div className="p-8 max-w-6xl mx-auto">
          <div className="bg-white text-slate-900 rounded-3xl p-6 shadow-2xl">
            <div className="text-2xl md:text-3xl font-bold">{st.question.prompt}</div>
            {st.explain && <div className="text-slate-500 mt-1">{st.explain}</div>}
          </div>
          <div className="grid grid-cols-2 gap-4 mt-5">
            {st.question.options.map((o, i) => {
              const ok = i === st.correct;
              const max = Math.max(1, ...st.counts);
              return (
                <div key={i} className={`${OPT[i % 4].bg} ${ok ? "ring-4 ring-white" : "opacity-60"} rounded-2xl px-6 py-4 shadow-lg`}>
                  <div className="flex items-center justify-between text-xl font-semibold">
                    <span className="flex items-center gap-3"><span className="text-2xl">{OPT[i % 4].sym}</span>{o}{ok && " ✓"}</span>
                    <span className="text-2xl font-black">{st.counts[i] ?? 0}</span>
                  </div>
                  <div className="h-2 bg-black/20 rounded-full mt-2 overflow-hidden">
                    <div className="h-full bg-white/90" style={{ width: `${Math.round(((st.counts[i] ?? 0) / max) * 100)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="grid md:grid-cols-[1fr_auto] gap-6 mt-6 items-start">
            <div className="text-slate-900"><Board rows={st.players.slice(0, 5)} /></div>
            <button onClick={() => step("next")} className="bg-white text-brand-700 font-bold text-xl rounded-2xl px-8 py-4 flex items-center gap-2 shadow-xl">
              {st.q_index + 1 >= st.total ? "Yakuniy natija" : "Keyingi savol"} <ChevronRight size={22} />
            </button>
          </div>
        </div>
      )}

      {/* ---------- YAKUN ---------- */}
      {st.status === "ended" && (
        <div className="p-8 max-w-4xl mx-auto">
          <div className="text-center text-4xl font-black mb-6">🏆 G'oliblar</div>
          <div className="grid grid-cols-3 gap-4 items-end mb-8">
            {[st.players[1], st.players[0], st.players[2]].map((p, i) => p ? (
              <div key={p.id} className={`bg-white text-slate-900 rounded-2xl text-center p-4 shadow-2xl ${i === 1 ? "py-8" : ""}`}>
                <div className="text-4xl">{["🥈", "🥇", "🥉"][i]}</div>
                <div className="font-bold text-xl mt-1">{p.nickname}</div>
                <div className="text-brand-600 font-semibold">{p.score} ball</div>
              </div>
            ) : <div key={i} />)}
          </div>
          <div className="text-slate-900"><Board rows={st.players} /></div>
          <div className="text-center mt-6">
            <Link to="/plans" className="bg-white text-brand-700 font-semibold rounded-xl px-6 py-3 inline-block">Dars rejalariga qaytish</Link>
          </div>
        </div>
      )}
    </div>
  );
}
