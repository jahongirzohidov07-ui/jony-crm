import { GraduationCap, Check, Play, RotateCcw } from "lucide-react";
import { useGuide } from "./GuideProvider";

/**
 * "MENING FUNKSIYALARIM" — profildagi bo'lim (2026-08-23).
 *
 * Jahongir: "profil bolimida mening funksiyalarim bolimi bolsa,
 * shu funksiyalarni qaysini qilishni bilmasa shuni bosadi,
 * programma avtomat test rejimida... shu yerni bosasan deb
 * strelkalar turib hammasini korsatib turishi kerak".
 *
 * Xodim o'z lavozimi uchun MAVJUD ishlarning ro'yxatini ko'radi.
 * Qaysinisini qilishni bilmasa — ustiga bosadi va tizim uni
 * qadam-baqadam olib boradi (mashq test filialida ketadi).
 */
export default function MyFunctions() {
  const { lessons, done, start, running } = useGuide();

  if (!lessons.length) return null;

  const left = lessons.filter((l) => !done.includes(l.id));
  const pct = Math.round((done.length / lessons.length) * 100);

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-50 text-brand-600">
          <GraduationCap size={18} />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900">
              Mening funksiyalarim
            </h3>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600">
              {done.length}/{lessons.length} o'rganildi
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600">
            Lavozimingizda qila oladigan ishlar. Qaysinisini qilishni
            bilmasangiz — ustiga bosing, tizim <b>strelka bilan
            ko'rsatib</b> boshidan oxirigacha olib boradi. Mashq{" "}
            <b>test filialida</b> ketadi, haqiqiy ma'lumotga tegmaydi.
          </p>

          <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-brand-500 transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>

          <ul className="mt-4 space-y-2">
            {lessons.map((l) => {
              const ok = done.includes(l.id);
              return (
                <li
                  key={l.id}
                  className="flex items-start gap-3 rounded-xl border border-slate-100 p-3"
                >
                  <span
                    className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] ${
                      ok
                        ? "bg-emerald-100 text-emerald-700"
                        : "bg-slate-100 text-slate-500"
                    }`}
                  >
                    {ok ? <Check size={13} /> : l.minutes}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-800">
                      {l.title}
                    </p>
                    <p className="mt-0.5 text-xs leading-relaxed text-slate-500">
                      {l.why}
                    </p>
                  </div>
                  <button
                    onClick={() => start(l.id)}
                    disabled={!!running}
                    className={`inline-flex shrink-0 items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium disabled:opacity-40 ${
                      ok
                        ? "border border-slate-200 text-slate-600 hover:border-slate-300"
                        : "bg-brand-600 text-white hover:bg-brand-700"
                    }`}
                  >
                    {ok ? <RotateCcw size={12} /> : <Play size={12} />}
                    {ok ? "Takrorlash" : "O'rgat"}
                  </button>
                </li>
              );
            })}
          </ul>

          {left.length === 0 && (
            <p className="mt-3 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              Barcha darslarni o'tdingiz. Istagan paytda takrorlashingiz
              mumkin.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
