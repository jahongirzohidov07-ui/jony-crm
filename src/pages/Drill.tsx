import { useCallback, useEffect, useRef, useState } from "react";
import { Timer, Play, Check, SkipForward, Square } from "lucide-react";
import { api } from "../lib/api";

/**
 * MASHQ — adminning tayyorgarlik sinovi (2026-09-25).
 *
 * Jahongir: "test filialga kirib mashq degan bo'lim ochiladi faqat
 * adminlarga, start bossa vazifa bersin, vazifalarni bajarib keyingi
 * bosqichga o'taversin".
 *
 * Vazifa TIZIMNING O'ZIDA bajariladi: admin boshqa oynada ishni
 * qiladi, keyin bu yerga qaytib "Bajardim" bosadi. Server haqiqatan
 * bajarilganini tekshiradi (yangi yozuv yoki audit yozuvi), shuning
 * uchun shunchaki tugma bosib o'tib bo'lmaydi.
 */
type Step = {
  id: number;
  order_no: number;
  title: string;
  hint: string | null;
  seconds: number;
  verify_kind: string;
  spent: number | null;
  ok: boolean;
  skipped: boolean;
  in_time: boolean;
};

type Attempt = {
  id: number;
  status: string;
  started_at: string | null;
  finished_at: string | null;
  steps: Step[];
  total: number;
  done: number;
  in_time: number;
  spent: number;
};

type State = {
  can_start: boolean;
  test_branch: boolean;
  branch: string | null;
  tasks: { id: number; title: string; seconds: number; hint: string | null;
           verify_label: string }[];
  attempt: Attempt | null;
  current: Step | null;
  left: number | null;
  history: Attempt[];
  hint: string;
  message?: string;
  ok?: boolean;
};

function mmss(sec: number) {
  const s = Math.max(0, Math.round(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function Drill() {
  const [d, setD] = useState<State | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [left, setLeft] = useState<number | null>(null);
  const tick = useRef<number | null>(null);

  const load = useCallback(() => {
    api
      .fresh<State>("/drill/state")
      .then((r) => {
        setD(r);
        setLeft(r.left);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);
  useEffect(load, [load]);

  // Sekundomer: server bergan qoldiqdan boshlab sanaydi
  useEffect(() => {
    if (left == null) return;
    tick.current = window.setInterval(
      () => setLeft((v) => (v == null ? v : v - 1)),
      1000
    );
    return () => {
      if (tick.current) window.clearInterval(tick.current);
    };
  }, [d?.current?.id]);

  const act = async (path: string, body?: unknown) => {
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<State>(path, body ?? {});
      setD(r);
      setLeft(r.left);
      if (r.ok === false && r.message) setErr(r.message);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  const card = "bg-white border border-slate-200 rounded-xl p-5";

  return (
    <div className="max-w-3xl">
      <div className="flex items-center gap-2 mb-1">
        <Timer size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Mashq</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Tizimni qanchalik tez boshqarishingizni tekshiramiz
        {d.branch ? ` · ${d.branch}` : ""}
      </p>

      {!d.test_branch && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-4">
          <p className="text-sm text-amber-900">
            Mashq faqat <b>sinov filialida</b> ishlaydi — haqiqiy filialda
            soxta o'quvchi va to'lov paydo bo'lmasligi uchun. Tepadagi
            tanlagichdan sinov filialiga o'ting.
          </p>
        </div>
      )}

      {err && (
        <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 mb-4">
          <p className="text-sm text-rose-700">{err}</p>
        </div>
      )}

      {/* ---------- Ketayotgan mashq ---------- */}
      {d.current && d.attempt ? (
        <div className={card}>
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs text-slate-500">
              {d.current.order_no} / {d.attempt.total}
            </span>
            <span
              className={`text-2xl font-semibold tabular-nums ${
                (left ?? 0) < 0 ? "text-rose-600" : "text-slate-900"
              }`}
            >
              {(left ?? 0) < 0 ? "+" : ""}
              {mmss(Math.abs(left ?? 0))}
            </span>
          </div>

          <p className="text-lg font-medium text-slate-900">
            {d.current.title}
          </p>
          {d.current.hint && (
            <p className="text-sm text-slate-500 mt-1">{d.current.hint}</p>
          )}
          <p className="text-xs text-slate-400 mt-2">
            {d.current.verify_kind === "view"
              ? "Ko'rish vazifasi — bo'limni oching va tasdiqlang"
              : "Tizimda bajaring — server tekshiradi"}
          </p>

          <div className="h-1.5 bg-slate-100 rounded-full my-4">
            <div
              className="h-1.5 bg-brand-600 rounded-full transition-all"
              style={{
                width: `${((d.current.order_no - 1) / d.attempt.total) * 100}%`,
              }}
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              disabled={busy}
              onClick={() => act("/drill/done")}
              className="flex items-center gap-1.5 rounded-lg bg-brand-600 text-white text-sm px-4 py-2 disabled:opacity-50"
            >
              <Check size={15} /> Bajardim
            </button>
            <button
              disabled={busy}
              onClick={() => act("/drill/done", { skip: true })}
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 text-slate-600 text-sm px-4 py-2 disabled:opacity-50"
            >
              <SkipForward size={15} /> O'tkazib yuborish
            </button>
            <button
              disabled={busy}
              onClick={() => {
                if (confirm("Mashq to'xtatilsinmi?")) act("/drill/stop");
              }}
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 text-slate-500 text-sm px-4 py-2 ml-auto disabled:opacity-50"
            >
              <Square size={14} /> To'xtatish
            </button>
          </div>

          {d.attempt.steps.some((s) => s.spent != null) && (
            <div className="mt-5 border-t border-slate-100 pt-3 space-y-1">
              {d.attempt.steps
                .filter((s) => s.spent != null)
                .map((s) => (
                  <div key={s.id} className="flex items-center gap-2 text-xs">
                    <span
                      className={
                        s.skipped
                          ? "text-slate-400"
                          : s.in_time
                          ? "text-emerald-600"
                          : "text-amber-600"
                      }
                    >
                      {s.skipped ? "—" : s.in_time ? "✓" : "!"}
                    </span>
                    <span className="text-slate-600 truncate">{s.title}</span>
                    <span className="ml-auto text-slate-400 tabular-nums">
                      {s.spent}s / {s.seconds}s
                    </span>
                  </div>
                ))}
            </div>
          )}
        </div>
      ) : (
        <div className={card}>
          <p className="text-sm text-slate-600 mb-3">{d.hint}</p>
          <p className="text-sm text-slate-500 mb-4">
            Jami {d.tasks.length} ta vazifa ·{" "}
            {Math.round(
              d.tasks.reduce((a, t) => a + t.seconds, 0) / 60
            )}{" "}
            daqiqagacha
          </p>
          <button
            disabled={busy || !d.can_start}
            onClick={() => act("/drill/start")}
            className="flex items-center gap-1.5 rounded-lg bg-brand-600 text-white text-sm px-5 py-2.5 disabled:opacity-40"
          >
            <Play size={15} /> Boshlash
          </button>
        </div>
      )}

      {/* ---------- O'tgan urinishlar ---------- */}
      {d.history.length > 0 && (
        <div className="mt-6">
          <p className="text-sm font-medium text-slate-700 mb-2">
            Oldingi urinishlar
          </p>
          <div className="space-y-2">
            {d.history.map((a) => (
              <div
                key={a.id}
                className="bg-white border border-slate-200 rounded-xl p-3 flex items-center gap-3 text-sm"
              >
                <span className="text-slate-500">
                  {a.started_at?.slice(0, 16).replace("T", " ")}
                </span>
                <span className="text-slate-700">
                  {a.in_time} / {a.total} vazifa vaqtida
                </span>
                <span className="ml-auto text-slate-400">
                  {Math.round(a.spent / 60)} daqiqa
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
