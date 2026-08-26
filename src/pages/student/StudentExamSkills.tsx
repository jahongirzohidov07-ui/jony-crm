import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ChevronRight, ChevronLeft, Lock } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";
import { findExam } from "./examsConfig";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * IMTIHON ICHI — IKKINCHI QAVAT (2026-08-26).
 *
 * Jahongir: "keyin IELTSga kirganda Reading listening writing
 * speaking, tursin CEFR ga kirganda ham shunaqa".
 *
 * Bitta ekran uch imtihonga ham xizmat qiladi — ro'yxat
 * examsConfig.ts dan olinadi. Yangi imtihon qo'shilsa bu fayl
 * o'zgarmaydi.
 *
 * SONLAR. "12 qism · 340/1200 bajarildi" yozuvi haqiqiy — server
 * /parts?exam= dan olinadi, qo'lda yozilmaydi. Shuning uchun
 * mashq qo'shilsa raqam o'zi o'sadi.
 */
type Stat = { parts: number; total: number; solved: number };

export default function StudentExamSkills() {
  const { exam = "" } = useParams();
  const def = findExam(exam);

  const [gate, setGate] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [stats, setStats] = useState<Record<string, Stat>>({});

  useEffect(() => {
    api
      .get<Any>("/student/learn")
      .then((r) => setGate(r.ielts || { unlocked: false }))
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  // Faqat mashqi bor ko'nikmalar uchun so'rov yuboriladi.
  useEffect(() => {
    if (!gate?.unlocked || !def) return;
    const want = def.skills.filter((s) => s.api);
    want.forEach((s) => {
      api
        .get<Any>(`/student/ielts/${s.api}/parts?exam=${def.key}`)
        .then((r) => {
          const rows: Any[] = r.parts || [];
          setStats((old) => ({
            ...old,
            [s.key]: {
              parts: rows.length,
              total: rows.reduce((a, x) => a + (x.total || 0), 0),
              solved: rows.reduce((a, x) => a + (x.solved || 0), 0),
            },
          }));
        })
        .catch(() => undefined);
    });
  }, [gate?.unlocked, def]);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  if (!def)
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center">
        <p className="text-sm text-slate-400">Bunday imtihon topilmadi.</p>
        <Link
          to="/student/ielts"
          className="inline-block mt-4 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white"
        >
          Imtihonlar ro'yxati
        </Link>
      </div>
    );

  if (err)
    return (
      <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>
    );
  if (!gate)
    return (
      <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>
    );

  if (!gate.unlocked)
    return (
      <div className="max-w-md mx-auto px-4 pt-5 pb-8">
        <div className="rounded-2xl border p-5 mt-5 text-center" style={card}>
          <div
            className="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center"
            style={{ background: "#111C4B" }}
          >
            <Lock size={24} className="text-amber-400" />
          </div>
          <p className="text-white font-bold text-[16px] mt-3">
            Bo'lim hali qulflangan
          </p>
          <p className="text-[13px] text-slate-400 mt-1.5 leading-relaxed">
            {gate.need_label}. Hozirgi darajangiz:{" "}
            <b className="text-slate-200">{gate.level_label || "—"}</b>.
          </p>
          <Link
            to="/student/games"
            className="inline-block mt-4 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white"
          >
            Mashqlarga qaytish
          </Link>
        </div>
      </div>
    );

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <Link
        to="/student/ielts"
        className="inline-flex items-center gap-1 text-[13px] text-slate-400"
      >
        <ChevronLeft size={16} /> Imtihonlar
      </Link>

      <div className="flex items-center gap-3 mt-3">
        <img src={def.icon} alt="" className="w-12 h-12 shrink-0" />
        <div className="min-w-0">
          <h1 className="text-[30px] font-extrabold text-white leading-none">
            {def.title}
          </h1>
          <p className="text-[12px] text-slate-400 mt-1">{def.tag}</p>
        </div>
      </div>
      <p className="text-[13px] text-slate-400 mt-2.5 leading-relaxed">
        {def.desc}
      </p>

      <div className="space-y-2.5 mt-5">
        {def.skills.map((s) => {
          const st = stats[s.key];
          const body = (
            <>
              <img src={s.icon} alt="" className="w-11 h-11 shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-white font-bold text-[15px]">{s.title}</p>
                <p className="text-[12px] text-slate-400 leading-snug mt-0.5">
                  {s.desc}
                </p>
                {s.hint && (
                  <p className="text-[11px] text-brand-300 mt-1">{s.hint}</p>
                )}
                {st && (
                  <p className="text-[11px] text-slate-400 mt-1">
                    {st.parts} qism · {st.total} mashq · {st.solved} bajarildi
                  </p>
                )}
              </div>
            </>
          );
          return s.href ? (
            <Link
              key={s.key}
              to={s.href}
              className="flex items-center gap-3 rounded-2xl border p-4"
              style={card}
            >
              {body}
              <ChevronRight size={18} className="text-slate-500 shrink-0" />
            </Link>
          ) : (
            <div
              key={s.key}
              className="flex items-center gap-3 rounded-2xl border p-4 opacity-80"
              style={card}
            >
              {body}
              <span className="text-[10px] font-bold text-amber-300 bg-amber-400/10 border border-amber-400/30 rounded-full px-2 py-1 shrink-0">
                Tez orada
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
