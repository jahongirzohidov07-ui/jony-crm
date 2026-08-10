import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ArrowLeft, BookOpenCheck, Check, ChevronDown, ChevronRight,
  Crown, Lock,
} from "lucide-react";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — GRAMMAR A1 DASTURI (2026-08-11, Jahongir bergan
 * tartibda qayta qurildi).
 *
 * Level 1 dan boshlab ketma-ket, orasida BOSS LEVEL sinovlari
 * (toj belgisi bilan). A2 qulf bo'lib turadi - A1 dagi HAMMA mavzu
 * yopilgandagina ochiladi. A1 tugagach yig'ilib turadi, lekin
 * xohlasa ochib eski mavzularni qayta ishlash mumkin.
 */
export default function StudentGrammar() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [showA1, setShowA1] = useState(true);

  useEffect(() => {
    api
      .get<Any>("/student/grammar/topics")
      .then((r) => {
        setD(r);
        if (r?.a1?.completed) setShowA1(false); // tugagan - yig'iq
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const a1 = d?.a1;
  const a2 = d?.a2;

  function TopicRow({ t }: { t: Any }) {
    return (
      <Link
        to={`/student/grammar/${encodeURIComponent(t.topic)}`}
        className={`flex items-center gap-3 rounded-xl shadow-sm border p-3.5 active:scale-[0.99] transition ${
          t.boss
            ? "bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200"
            : "bg-white border-slate-200"
        }`}
      >
        <div
          className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold ${
            t.done
              ? "bg-emerald-100 text-emerald-700"
              : t.boss
                ? "bg-amber-100 text-amber-700"
                : "bg-violet-50 text-violet-600"
          }`}
        >
          {t.done ? (
            <Check size={17} />
          ) : t.boss ? (
            <Crown size={17} />
          ) : (
            `${t.percent}%`
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p
            className={`text-sm font-semibold truncate ${
              t.boss ? "text-amber-800" : "text-slate-800"
            }`}
          >
            {t.topic}
          </p>
          <div className="h-1.5 bg-slate-100 rounded-full mt-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full ${
                t.done
                  ? "bg-emerald-500"
                  : t.boss
                    ? "bg-amber-500"
                    : "bg-violet-500"
              }`}
              style={{ width: `${t.percent}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            {t.solved}/{t.total} savol yechildi
          </p>
        </div>
        <ChevronRight size={17} className="text-slate-300 shrink-0" />
      </Link>
    );
  }

  return (
    <>
      <div className="bg-gradient-to-br from-violet-700 to-violet-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/student/games"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Mashqlar
          </Link>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <BookOpenCheck size={22} />
            Grammar
          </h1>
          {a1 && (
            <p className="text-sm opacity-90 mt-0.5">
              A1: {a1.done}/{a1.total} mavzu
              {a1.completed ? " — tugatildi! 🎉" : ""}
            </p>
          )}
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-3 pb-8">
        {err && (
          <div className="bg-white rounded-xl border border-red-200 p-4 text-sm text-red-600">
            {err}
          </div>
        )}

        {/* ---- A1 ---- */}
        {a1 && (
          <>
            <button
              onClick={() => setShowA1((v) => !v)}
              className={`w-full flex items-center justify-between rounded-xl p-4 border ${
                a1.completed
                  ? "bg-emerald-50 border-emerald-200"
                  : "bg-white border-slate-200"
              }`}
            >
              <div className="text-left">
                <p className="text-sm font-bold text-slate-800">
                  A1 — Beginner
                </p>
                <p className="text-[11px] text-slate-500">
                  {a1.done}/{a1.total} mavzu yopildi
                  {a1.completed ? " · tugatilgan" : ""}
                </p>
              </div>
              <ChevronDown
                size={18}
                className={`text-slate-400 transition ${
                  showA1 ? "rotate-180" : ""
                }`}
              />
            </button>
            {showA1 && (
              <div className="space-y-2">
                {a1.topics.map((t: Any) => (
                  <TopicRow key={t.topic} t={t} />
                ))}
              </div>
            )}
          </>
        )}

        {/* ---- A2 ---- */}
        {d?.a2_locked ? (
          <div className="rounded-xl border-2 border-dashed border-slate-300 p-5 flex items-center gap-3 bg-slate-50">
            <div className="w-10 h-10 rounded-xl bg-slate-200 text-slate-500 flex items-center justify-center shrink-0">
              <Lock size={18} />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-600">
                A2 — Elementary
              </p>
              <p className="text-[11px] text-slate-400">
                A1 dagi barcha mavzularni tugating — A2 ochiladi
              </p>
            </div>
          </div>
        ) : a2?.ready ? (
          <>
            <div className="rounded-xl p-4 bg-white border border-slate-200">
              <p className="text-sm font-bold text-slate-800">
                A2 — Elementary
              </p>
            </div>
            <div className="space-y-2">
              {a2.topics.map((t: Any) => (
                <TopicRow key={t.topic} t={t} />
              ))}
            </div>
          </>
        ) : a1?.completed ? (
          <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm font-semibold text-amber-800">
              A2 ochildi! 🎉
            </p>
            <p className="text-[11px] text-amber-700 mt-0.5">
              A2 mashqlari tez orada yuklanadi.
            </p>
          </div>
        ) : null}
      </div>
    </>
  );
}
