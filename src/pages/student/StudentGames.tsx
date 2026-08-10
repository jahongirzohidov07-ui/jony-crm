import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BookA, BookOpenCheck, ChevronRight, Ear, Mic, PenLine, Text,
} from "lucide-react";
import { api } from "../../lib/api";
import type { VocabStats } from "../../lib/studentApi";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY STUDENT — MASHQ BO'LIMLARI (2026-08-10, qayta qurildi).
 *
 * Jahongir: "grammar mashqi turibdi, pastida hammasi lug'at mashqi
 * turibdi — hammasini bitta bo'lim qilib, grammar tagiga lug'at
 * mashqi qilib yashil rang bilan qo'ygin."
 *
 * Endi sahifa ikkita katta bo'limdan iborat: Grammar (binafsha) va
 * Lug'at (yashil). Har birining o'z ichki sahifasi bor — 7 ta
 * lug'at o'yini endi shu yerda sochilib yotmaydi.
 */
export default function StudentGames() {
  const [st, setSt] = useState<VocabStats | null>(null);
  const [gr, setGr] = useState<Any>(null);
  const [sk, setSk] = useState<Any>(null);

  useEffect(() => {
    api.get<VocabStats>("/student/vocab/stats").then(setSt).catch(() => {});
    api.get<Any>("/student/grammar/topics").then(setGr).catch(() => {});
    api.get<Any>("/student/skills").then(setSk).catch(() => {});
  }, []);

  const pts = (key: string) =>
    sk?.skills?.find((x: Any) => x.key === key)?.points ?? null;

  const grTopics: Any[] = (gr?.levels || []).flatMap((l: Any) => l.topics);
  const grDone = grTopics.filter((t: Any) => t.done).length;

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-10">
        <div className="max-w-md mx-auto">
          <h1 className="text-xl font-semibold">Mashq</h1>
          <p className="text-sm opacity-90 mt-0.5">
            Har to'g'ri javob — ball va XP
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-3 pb-8">
        <Link
          to="/student/grammar"
          className="flex items-center gap-3.5 bg-gradient-to-r from-violet-600 to-violet-500 rounded-2xl shadow-sm p-5 active:scale-[0.99] transition text-white"
        >
          <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center shrink-0">
            <BookOpenCheck size={24} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-base font-semibold">Grammar mashqlari</p>
            <p className="text-xs opacity-85 mt-0.5">
              Har mavzuga xilma-xil mashqlar: A1 dan B1 gacha
            </p>
            {gr && grTopics.length > 0 && (
              <p className="text-[11px] opacity-75 mt-1">
                {grDone}/{grTopics.length} mavzu yopildi ·{" "}
                {gr.total_correct || 0} savol yechildi
              </p>
            )}
          </div>
          <ChevronRight size={20} className="opacity-70 shrink-0" />
        </Link>

        <Link
          to="/student/vocab"
          className="flex items-center gap-3.5 bg-gradient-to-r from-emerald-600 to-emerald-500 rounded-2xl shadow-sm p-5 active:scale-[0.99] transition text-white"
        >
          <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center shrink-0">
            <BookA size={24} />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-base font-semibold">Lug'at mashqi</p>
            <p className="text-xs opacity-85 mt-0.5">
              7 xil o'yin: tanlov, yozish, juftlash va boshqalar
            </p>
            {st && (
              <p className="text-[11px] opacity-75 mt-1">
                {st.correct} to'g'ri javob · {st.percent}%
                {st.streak > 0 && ` · ${st.streak} kun ketma-ket`}
              </p>
            )}
          </div>
          <ChevronRight size={20} className="opacity-70 shrink-0" />
        </Link>

        {/* 4 KO'NIKMA (2026-08-10, Jahongir: "listening, reading,
            writing, speaking mashqlari ham qo'shaylik") */}
        {[
          {
            skill: "listening",
            label: "Listening",
            hint: "Eshiting: diktant va tanlov",
            grad: "from-amber-600 to-amber-500",
            Icon: Ear,
          },
          {
            skill: "reading",
            label: "Reading",
            hint: "Matn o'qib, savollarga javob bering",
            grad: "from-sky-700 to-sky-500",
            Icon: Text,
          },
          {
            skill: "writing",
            label: "Writing",
            hint: "Jumlalarni inglizcha yozib tarjima qiling",
            grad: "from-rose-600 to-rose-500",
            Icon: PenLine,
          },
          {
            skill: "speaking",
            label: "Speaking",
            hint: "Mikrofonga o'qing — talaffuz tekshiriladi",
            grad: "from-teal-600 to-teal-500",
            Icon: Mic,
          },
        ].map(({ skill, label, hint, grad, Icon }) => (
          <Link
            key={skill}
            to={`/student/practice/${skill}`}
            className={`flex items-center gap-3.5 bg-gradient-to-r ${grad} rounded-2xl shadow-sm p-5 active:scale-[0.99] transition text-white`}
          >
            <div className="w-12 h-12 rounded-2xl bg-white/20 flex items-center justify-center shrink-0">
              <Icon size={24} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-base font-semibold">{label}</p>
              <p className="text-xs opacity-85 mt-0.5">{hint}</p>
              {pts(skill) !== null && (
                <p className="text-[11px] opacity-75 mt-1">
                  {pts(skill)} ball to'plangan
                </p>
              )}
            </div>
            <ChevronRight size={20} className="opacity-70 shrink-0" />
          </Link>
        ))}
      </div>
    </>
  );
}
