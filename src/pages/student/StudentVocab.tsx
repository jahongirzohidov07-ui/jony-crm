import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft, BookA, Check, ChevronRight, Flame, X,
} from "lucide-react";
import { api } from "../../lib/api";
import type { StudentHome, VocabStats } from "../../lib/studentApi";
import { getLang, LANGS } from "../../lib/lang";
import { Flag } from "../../components/Flag";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — LUG'AT: UNIT RO'YXATI (2026-08-11, qayta qurildi).
 *
 * Jahongir: "lug'at mashqiga kirganda unit so'zlar qator bo'lib list
 * ko'rinishida turishi kerak. Har so'zni kamida 3 marta to'g'ri
 * topgan bo'lsa progress bar ko'k, 6 marta bo'lsa yashil, necha foiz
 * o'rganilgani ko'rinib tursin. 99% gacha o'zi practice qiladi,
 * ustoz 'topshirdi' tick qo'ysa 100% bo'ladi. Unitni tanlagach qaysi
 * turdagi practice qilishni so'rasin."
 */
export default function StudentVocab() {
  const nav = useNavigate();
  const lang = getLang();
  const [d, setD] = useState<StudentHome | null>(null);
  const [st, setSt] = useState<VocabStats | null>(null);
  const [units, setUnits] = useState<Any[]>([]);
  const [err, setErr] = useState("");
  const [picker, setPicker] = useState<string | null>(null); // tanlangan unit

  useEffect(() => {
    api.get<StudentHome>("/student/home").then(setD).catch(() => {});
    api.get<VocabStats>("/student/vocab/stats").then(setSt).catch(() => {});
    api
      .get<Any>(`/student/vocab/units?language=${lang}`)
      .then((r) => setUnits(r.units || []))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [lang]);

  const games: Any[] = d?.games || [];
  const langMeta = LANGS.find((l) => l.code === lang) || LANGS[0];

  function openGame(game: string) {
    const q = picker ? `?unit=${encodeURIComponent(picker)}&lang=${lang}` : `?lang=${lang}`;
    nav(`/student/games/${game}${q}`);
  }

  return (
    <>
      <div className="bg-gradient-to-br from-emerald-700 to-emerald-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/student/games"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Mashqlar
          </Link>
          <h1 className="text-xl font-semibold flex items-center gap-2">
            <BookA size={22} />
            Lug'at · <Flag code={lang} size={20} /> {langMeta.label}
          </h1>
          <p className="text-sm opacity-90 mt-0.5">
            Unitni tanlang — mashq turi so'raladi
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-3 pb-8">
        {err && (
          <div className="bg-white rounded-xl border border-red-200 p-4 text-sm text-red-600">
            {err}
          </div>
        )}

        {st && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 flex items-center justify-between">
            <div>
              <p className="text-lg font-semibold text-slate-900 leading-tight">
                {st.correct}{" "}
                <span className="text-sm font-normal text-slate-400">
                  to'g'ri javob
                </span>
              </p>
              <p className="text-xs text-slate-500">
                {st.total} urinishdan · {st.percent}%
              </p>
            </div>
            {st.streak > 0 && (
              <span className="flex items-center gap-1 text-sm font-medium text-orange-600 shrink-0">
                <Flame size={16} />
                {st.streak} kun
              </span>
            )}
          </div>
        )}

        {/* Umumiy mashq (unitsiz) */}
        <button
          onClick={() => setPicker("")}
          className="w-full flex items-center gap-3 bg-white rounded-xl shadow-sm border border-slate-200 p-4 active:scale-[0.99] transition text-left"
        >
          <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shrink-0">
            <BookA size={19} />
          </div>
          <div className="flex-1">
            <p className="text-sm font-semibold text-slate-800">
              Umumiy mashq
            </p>
            <p className="text-[11px] text-slate-400">
              Barcha unitlardan aralash so'zlar
            </p>
          </div>
          <ChevronRight size={18} className="text-slate-300" />
        </button>

        {/* ---- UNIT RO'YXATI ---- */}
        <div className="space-y-2">
          {units.map((u) => {
            const bar =
              u.tone === "gold"
                ? "bg-amber-400"
                : u.tone === "green"
                  ? "bg-emerald-500"
                  : "bg-sky-500";
            return (
              <button
                key={u.key}
                onClick={() => setPicker(u.key)}
                className="w-full bg-white rounded-xl shadow-sm border border-slate-200 p-4 active:scale-[0.99] transition text-left"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-sm font-semibold text-slate-800 flex items-center gap-1.5">
                    {u.key}
                    {u.passed && (
                      <span className="inline-flex items-center gap-0.5 text-[10px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">
                        <Check size={10} />
                        Topshirilgan
                      </span>
                    )}
                  </p>
                  <span
                    className={`text-sm font-bold ${
                      u.passed
                        ? "text-amber-600"
                        : u.tone === "green"
                          ? "text-emerald-600"
                          : "text-sky-600"
                    }`}
                  >
                    {u.percent}%
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${bar}`}
                    style={{ width: `${u.percent}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  {u.n} so'z · 3+ marta: {u.learned3} · 6+ marta:{" "}
                  {u.learned6}
                </p>
              </button>
            );
          })}
        </div>

        <p className="text-[11px] text-slate-400 px-1">
          So'zni 3 marta to'g'ri topsangiz "o'rganilgan" (ko'k), 6 marta
          topsangiz mustahkam (yashil) sanaladi. 99% gacha o'zingiz
          yig'asiz — 100% ustozingiz unitni "topshirildi" deb
          tasdiqlaganda bo'ladi.
        </p>
      </div>

      {/* ---- MASHQ TURI TANLASH ---- */}
      {picker !== null && (
        <div
          className="fixed inset-0 bg-black/40 z-40 flex items-end justify-center"
          onClick={() => setPicker(null)}
        >
          <div
            className="w-full max-w-md bg-white rounded-t-2xl p-4 pb-8 max-h-[75vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-slate-800">
                {picker || "Umumiy mashq"} — qaysi turdagi practice?
              </p>
              <button
                onClick={() => setPicker(null)}
                className="text-slate-400"
                aria-label="Yopish"
              >
                <X size={18} />
              </button>
            </div>
            <div className="space-y-1.5">
              {games.map((gm) => (
                <button
                  key={gm.key}
                  onClick={() => openGame(gm.key)}
                  className="w-full flex items-center gap-3 border border-slate-200 rounded-xl p-3.5 active:scale-[0.99] transition text-left"
                >
                  <div className="w-9 h-9 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 text-sm font-bold">
                    {gm.label.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-800">
                      {gm.label}
                    </p>
                    <p className="text-[11px] text-slate-400 truncate">
                      {gm.hint}
                    </p>
                  </div>
                  <ChevronRight size={16} className="text-slate-300" />
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
