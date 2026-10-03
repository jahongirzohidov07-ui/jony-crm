import { StudentLoading, StudentLoadError } from "../../components/StudentLoading";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ChevronRight, Lightbulb, XCircle } from "lucide-react";
import { formatDate } from "../../lib/format";
import { api } from "../../lib/api";

/**
 * JONY STUDENT — IMTIHON NATIJALARIM VA TAHLIL (2026-10-03, Jahongir:
 * "natijalari o'ziga ko'rinib turishi kerak qayerdadir, lekin bosh
 * sahifada alohida bo'lim ochma; tahlil javoblarni yodlab oladigan emas,
 * xatosini tushunadigan bo'lsin, mavzu yuzasidan, aynan savolning o'zi").
 *
 * Profil -> "Imtihon natijalarim". To'g'ri javob ATAYLAB ko'rsatilmaydi:
 * savol, o'z javobi, mavzu va qoida tushuntirishi.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const card = { background: "#0c2258", borderColor: "#35538c" };

function Header({ back, label, title, sub }: {
  back: string; label: string; title: string; sub?: string;
}) {
  return (
    <>
      <div className="flex items-center gap-2.5">
        <Link to={back}
          className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
          style={card}>
          <ArrowLeft size={18} />
        </Link>
        <span className="text-[15px] font-semibold text-brand-300 flex-1">{label}</span>
      </div>
      <h1 className="text-[28px] font-extrabold text-white leading-tight mt-3">{title}</h1>
      {sub && <p className="text-[14px] text-slate-400 mt-1">{sub}</p>}
    </>
  );
}

function scoreText(r: Any): string {
  if (r.absent) return "Kelmadi";
  if (r.band != null) return `Band ${r.band}`;
  if (r.score != null) return `${r.score} / ${r.max_score ?? "—"}`;
  return "—";
}

export default function StudentResults() {
  const { examId } = useParams();
  return examId ? <Review examId={examId} /> : <List />;
}

function List() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<Any>("/student/results").then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);
  if (!d && err) return <StudentLoadError message={err} />;
  if (!d) return <StudentLoading />;
  const rows: Any[] = d.rows || [];

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <Header back="/student/profile" label="Profil" title="Imtihon natijalarim"
        sub="Online topshirganlaringizda xatolar tahlili bor" />
      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 mt-6">Hali e'lon qilingan natija yo'q.</p>
      ) : (
        <div className="space-y-2.5 mt-5">
          {rows.map((r) => {
            const pct = r.percent != null ? Math.round(r.percent) : null;
            const tone = r.absent ? "text-slate-400"
              : pct == null ? "text-white"
              : pct >= 80 ? "text-emerald-300" : pct >= 60 ? "text-amber-300" : "text-rose-300";
            const body = (
              <>
                <div className="min-w-0 flex-1">
                  <p className="text-[15px] font-bold text-white">{r.title}</p>
                  <p className="text-xs text-slate-400">
                    {r.date ? formatDate(r.date) : ""}
                    {r.has_review ? " · Tahlilni ko'rish" : ""}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className={`text-[15px] font-extrabold tabular-nums ${tone}`}>{scoreText(r)}</p>
                  {pct != null && !r.absent && (
                    <p className="text-xs text-slate-400 tabular-nums">{pct}%</p>
                  )}
                </div>
                {r.has_review && <ChevronRight size={17} className="text-slate-500 shrink-0" />}
              </>
            );
            return r.has_review ? (
              <Link key={r.exam_id} to={`/student/results/${r.exam_id}`}
                className="rounded-2xl border p-4 flex items-center gap-3 active:scale-[0.98] transition"
                style={card}>
                {body}
              </Link>
            ) : (
              <div key={r.exam_id} className="rounded-2xl border p-4 flex items-center gap-3" style={card}>
                {body}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Review({ examId }: { examId: string }) {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<Any>(`/student/results/${examId}/review`).then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [examId]);
  if (!d && err) return <StudentLoadError message={err} />;
  if (!d) return <StudentLoading />;
  const mistakes: Any[] = d.mistakes || [];
  const topics: Any[] = d.topics || [];

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <Header back="/student/results" label="Natijalarim" title={d.title}
        sub={`${d.date ? formatDate(d.date) + " · " : ""}Test qismi: ${d.online_correct} / ${d.online_total} to'g'ri`} />

      {topics.length > 0 && (
        <div className="rounded-2xl border p-4 mt-5" style={card}>
          <p className="text-[15px] font-bold text-white mb-2">Mavzular bo'yicha</p>
          <div className="space-y-2">
            {topics.map((t) => {
              const pct = Math.round((t.correct / t.total) * 100);
              return (
                <div key={t.topic}>
                  <div className="flex justify-between text-xs text-slate-300">
                    <span className="truncate pr-2">{t.topic}</span>
                    <span className="tabular-nums shrink-0">{t.correct}/{t.total}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/10 overflow-hidden mt-1">
                    <div className={`h-full rounded-full ${pct >= 80 ? "bg-emerald-400" : pct >= 50 ? "bg-amber-400" : "bg-rose-400"}`}
                      style={{ width: `${Math.max(4, pct)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-[11px] text-slate-400 mt-3">
            Qizil va sariq mavzularni qaytadan takrorlang.
          </p>
        </div>
      )}

      <p className="text-[15px] font-bold text-white mt-6">
        Xatolar tahlili {mistakes.length ? `(${mistakes.length})` : ""}
      </p>
      {mistakes.length === 0 ? (
        <p className="text-sm text-emerald-300 mt-2">Test qismida xato yo'q — barakalla!</p>
      ) : (
        <>
          <p className="text-xs text-slate-400 mt-1">
            To'g'ri javob ataylab ko'rsatilmaydi: qoidani tushunib, o'zingiz toping.
          </p>
          <div className="space-y-3 mt-3">
            {mistakes.map((m, i) => (
              <div key={i} className="rounded-2xl border p-4" style={card}>
                <div className="flex items-center gap-2 text-xs text-slate-400 mb-1.5">
                  <span className="font-semibold text-brand-300">{m.n}-savol</span>
                  {m.topic && <span className="truncate">· {m.topic}</span>}
                </div>
                {m.image && <img src={m.image} alt="" className="rounded-lg mb-2 max-h-48" />}
                <p className="text-[15px] text-white whitespace-pre-line">{m.q}</p>
                {m.options?.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {m.options.map((o: string, oi: number) => (
                      <li key={oi} className="text-sm text-slate-300">
                        <span className="font-semibold text-slate-400 mr-1.5">{"ABCDEFGH"[oi]})</span>{o}
                      </li>
                    ))}
                  </ul>
                )}
                <p className="flex items-start gap-1.5 text-sm text-rose-300 mt-2.5">
                  <XCircle size={15} className="shrink-0 mt-0.5" />
                  <span>Sizning javobingiz: <b>{m.your_answer || "javob berilmagan"}</b></span>
                </p>
                <div className="flex items-start gap-2 rounded-xl bg-white/5 px-3 py-2.5 mt-2.5">
                  <Lightbulb size={16} className="text-amber-300 shrink-0 mt-0.5" />
                  <p className="text-sm text-slate-200 leading-relaxed">{m.explain}</p>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
