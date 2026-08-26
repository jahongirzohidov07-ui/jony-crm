import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ChevronRight, PenLine } from "lucide-react";
import { JSA } from "../../components/Jsa";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * CEFR WRITING — BOSH EKRAN (2026-08-26).
 *
 * Jahongir: "shu narsalarni shunday mukammal qilib joylashtirginki
 * CEFR writing yozishni o'rganish uchun bu qism mukammal bo'lsin
 * va skillarni improve qilish eng samarali bo'lsin."
 *
 * METODIKA — UCH QATLAM. Yozuv ko'nikmasi faqat "yoz va yubor"
 * bilan o'smaydi, chunki o'quvchi xatosini ko'rmaydi. Shuning
 * uchun ekran uch bosqichga ajratilgan:
 *
 *   1. O'RGANISH — qaysi abzatsda nima yoziladi, tayyor iboralar,
 *      izohlangan namuna xat.
 *   2. MASHQ — mayda ko'nikmalar (register, ochilish-yopilish,
 *      band qamrovi). Bular AVTOMAT tekshiriladi, ya'ni o'quvchi
 *      javobni darrov oladi.
 *   3. IMTIHON — vaqt hisoblagichi, so'z sanagichi, avtomat
 *      tekshiruv va AI ekspert bahosi.
 *
 * Bu tartib tasodifiy emas: mayda ko'nikma mustahkam bo'lmasa,
 * to'liq matn yozish paytida u baribir buziladi.
 */
export default function StudentCefrWriting() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/cefr/writing/home")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  if (err)
    return <p className="text-sm text-slate-400 text-center py-20 px-6">{err}</p>;
  if (!d)
    return <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>;

  const g1 = (d.guide || []).filter((g: Any) => g.part === "1.1");
  const g2 = (d.guide || []).filter((g: Any) => g.part === "1.2");
  const g3 = (d.guide || []).filter((g: Any) => g.part === "2");
  const drillTotal = (d.drills || []).reduce(
    (a: number, x: Any) => a + x.total, 0);
  const drillDone = (d.drills || []).reduce(
    (a: number, x: Any) => a + x.solved, 0);

  const Group = ({ title, rows }: { title: string; rows: Any[] }) => (
    <>
      <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-4 mb-1.5">
        {title}
      </p>
      <div className="space-y-2">
        {rows.map((g: Any) => (
          <Link
            key={g.key}
            to={`/student/cefr/writing/guide/${g.key}`}
            className="flex items-center gap-3 rounded-2xl border p-3.5"
            style={card}
          >
            <div className="flex-1 min-w-0">
              <p className="text-white font-bold text-[14px]">{g.title}</p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                {g.level} · {g.words[0]}-{g.words[1]} so'z · {g.minutes} daq ·{" "}
                {g.steps} qadam
              </p>
            </div>
            <ChevronRight size={16} className="text-slate-500 shrink-0" />
          </Link>
        ))}
      </div>
    </>
  );

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5 text-white">
        <Link
          to="/student/ielts/exam/cefr"
          className="w-10 h-10 rounded-xl border flex items-center justify-center shrink-0"
          style={card}
        >
          <ArrowLeft size={18} />
        </Link>
        <p className="text-[15px] font-extrabold tracking-wide flex-1">
          CEFR Multilevel
        </p>
        <img src="/jsicons/learn-writing.png" alt=""
             className="w-10 h-10 shrink-0" />
      </div>

      <h1 className="text-[30px] font-extrabold text-white leading-none mt-3">
        Writing
      </h1>

      {/* --- imtihon formati ------------------------------- */}
      <div className="rounded-2xl border p-3.5 mt-4" style={card}>
        <p className="text-[12px] font-bold text-white mb-2">
          Imtihon formati
        </p>
        <div className="space-y-1.5">
          {(d.format || []).map((f: Any) => (
            <div key={f.part} className="flex items-center gap-2 text-[11px]">
              <span className="w-9 shrink-0 font-bold text-brand-300">
                {f.part}
              </span>
              <span className="w-7 shrink-0 text-slate-500">{f.level}</span>
              <span className="flex-1 min-w-0 text-slate-300 truncate">
                {f.kind}
              </span>
              <span className="shrink-0 text-slate-400">{f.words} so'z</span>
              <span className="w-11 shrink-0 text-right text-slate-500">
                {f.minutes} daq
              </span>
            </div>
          ))}
        </div>
        <p className="text-[10.5px] text-slate-500 mt-2.5 leading-relaxed">
          Part 1 da bitta xabar keladi va siz SHU vaziyat bo'yicha ikki
          xat yozasiz: avval do'stingizga (norasmiy), keyin
          rahbariyatga (rasmiy). Imtihon aynan uslub almashtira
          olishingizni tekshiradi.
        </p>
      </div>

      {/* --- 3-qatlam: imtihon ----------------------------- */}
      <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-5 mb-1.5">
        To'liq yozish
      </p>
      <div className="space-y-2">
        <Link to="/student/cefr/writing/tasks/1"
              className="flex items-center gap-3 rounded-2xl border p-4"
              style={card}>
          <PenLine size={20} className="text-brand-300 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-white font-bold text-[15px]">
              Part 1 — ikki xat
            </p>
            <p className="text-[11.5px] text-slate-400 leading-snug mt-0.5">
              Bitta vaziyat, ikki xat. Vaqt hisoblagichi, so'z
              sanagichi va topshirgandan keyin namuna javob.
            </p>
            <p className="text-[11px] text-brand-300 mt-1">
              {d.tasks?.part1} ta vaziyat · {d.tasks?.written || 0} ta yozilgan
            </p>
          </div>
          <ChevronRight size={16} className="text-slate-500 shrink-0" />
        </Link>
        <Link to="/student/cefr/writing/tasks/2"
              className="flex items-center gap-3 rounded-2xl border p-4"
              style={card}>
          <PenLine size={20} className="text-brand-300 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-white font-bold text-[15px]">
              Part 2 — blog / forum / maqola
            </p>
            <p className="text-[11.5px] text-slate-400 leading-snug mt-0.5">
              C1 daraja, 180-200 so'z, 30 daqiqa.
            </p>
            <p className="text-[11px] text-brand-300 mt-1">
              {d.tasks?.part2} ta mavzu
            </p>
          </div>
          <ChevronRight size={16} className="text-slate-500 shrink-0" />
        </Link>
      </div>

      {/* --- 2-qatlam: mashqlar ---------------------------- */}
      <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-5 mb-1.5">
        Mashqlar · {drillDone}/{drillTotal}
      </p>
      <div className="space-y-2">
        {(d.drills || []).map((m: Any) => (
          <Link
            key={m.kind}
            to={`/student/cefr/writing/drill/${m.kind}`}
            className="flex items-center gap-3 rounded-2xl border p-3.5"
            style={card}
          >
            <div className="flex-1 min-w-0">
              <p className="text-white font-bold text-[14px]">{m.title}</p>
              <p className="text-[11px] text-slate-400 leading-snug mt-0.5">
                {m.desc}
              </p>
              <div className="h-1 rounded-full bg-white/10 mt-2 overflow-hidden">
                <div
                  className="h-full rounded-full bg-brand-500"
                  style={{
                    width: `${Math.round(100 * m.solved / Math.max(1, m.total))}%`,
                  }}
                />
              </div>
              <p className="text-[10.5px] text-slate-500 mt-1">
                {m.solved}/{m.total}
              </p>
            </div>
            <ChevronRight size={16} className="text-slate-500 shrink-0" />
          </Link>
        ))}
      </div>

      {/* --- 1-qatlam: qo'llanma --------------------------- */}
      <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wide mt-5">
        Qo'llanma — qaysi xatni qanday yozish kerak
      </p>
      <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
        Har turda: abzatslar tuzilmasi, tayyor iboralar va namuna
        xat — har abzatsi nima ish qilayotgani izohi bilan.
      </p>
      <Group title="Part 1.1 — norasmiy" rows={g1} />
      <Group title="Part 1.2 — rasmiy" rows={g2} />
      <Group title="Part 2 — C1" rows={g3} />
    </div>
  );
}
