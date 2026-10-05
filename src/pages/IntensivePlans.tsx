import { useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowUpRight, BookOpen, ChevronDown, Download, Search } from "lucide-react";
import brandIconSrc from "../assets/brand-icon.png";
import modules from "../data/intensive-grammar-map.json";

const PDF = "/intensive/jony-b2-grammar-map.pdf";
const phases = ["Fundament", "Zamon va ma’no", "Muloqot vositalari", "B2 tomon aniqlik"];
const topicCount = modules.reduce((count, module) => count + module.items.length, 0);

export default function IntensivePlans() {
  const [query, setQuery] = useState("");
  const normalized = query.trim().toLocaleLowerCase();
  const visible = modules.map((module, index) => ({ ...module, index })).filter(module =>
    !normalized || [module.title, module.uz, ...module.items.flat()].some(text => text.toLocaleLowerCase().includes(normalized))
  );

  return (
    <div className="mx-auto max-w-5xl p-4 md:p-8">
      <Link to="/plans" className="mb-3 inline-flex items-center gap-1 text-sm text-slate-500 hover:text-brand-600">
        <ArrowLeft size={15} /> Dars rejalari
      </Link>
      <h1 className="flex items-center gap-2 text-xl font-semibold text-slate-900">
        <BookOpen size={21} className="text-brand-600" /> Dars rejalari
      </h1>
      <nav aria-label="O‘quv yo‘nalishi" className="my-5 flex gap-2 rounded-xl bg-slate-100 p-1">
        <Link to="/plans" className="flex-1 rounded-lg px-4 py-3 text-center text-sm font-semibold text-slate-600 hover:bg-white">Standard English</Link>
        <Link to="/plans/intensive" aria-current="page" className="flex-1 rounded-lg bg-white px-4 py-3 text-center text-sm font-semibold text-brand-700 shadow-sm">Intensive</Link>
      </nav>

      <section aria-labelledby="intensive-title" className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <div className="flex flex-wrap items-start justify-between gap-4 p-5 md:p-7">
          <div>
            <div className="mb-3 flex items-center gap-2 text-xs font-bold tracking-widest text-brand-600">
              <img src={brandIconSrc} alt="Jony Academy" className="h-8 w-8" /> JONY INTENSIVE
            </div>
            <h2 id="intensive-title" className="text-2xl font-bold text-slate-900 md:text-3xl">Noldan B2 sari</h2>
            <p className="mt-2 max-w-xl text-sm leading-6 text-slate-500">8 oylik yo‘l: mustahkam fundamentdan Multilevel milliy sertifikatiga tayyorgarlikkacha.</p>
          </div>
          <div className="rounded-xl bg-brand-50 px-4 py-3 text-sm text-brand-700">
            <b>Haftada 6 kun</b><br />2 soat dars · 2 soat mustaqil mashg‘ulot
          </div>
        </div>
        <div className="h-9 bg-[length:auto_36px] bg-repeat-x" style={{ backgroundImage: "url('/student-design/pattern.png')" }} aria-hidden="true" />
      </section>

      <section aria-labelledby="grammar-map-title" className="mt-6 overflow-hidden rounded-2xl bg-slate-900 text-white">
        <div className="grid gap-6 p-5 md:grid-cols-[1fr_180px] md:p-7">
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-blue-300">01 / Kurs shu yerdan boshlanadi</p>
            <h2 id="grammar-map-title" className="text-2xl font-bold">B2 Grammar Map</h2>
            <p className="mt-3 max-w-xl text-sm leading-6 text-slate-300">{modules.length} bo‘lim · {topicCount} alohida mavzu · 33 sahifa. To be, zamonlar, modallar va murakkab gaplar — misollar hamda o‘zlashtirish kataklari bilan.</p>
            <p className="mt-3 text-sm leading-6 text-slate-300">Positive, negative va questions shakllari alohida mavzularga ajratilgan.</p>
            <div className="mt-5 flex flex-wrap gap-3">
              <a href={PDF} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 rounded-lg bg-white px-4 py-3 text-sm font-semibold text-slate-900 hover:bg-blue-50"><ArrowUpRight size={17} /> PDF’ni ochish</a>
              <a href={PDF} download="Jony-Intensive-B2-Grammar-Map.pdf" className="inline-flex items-center gap-2 rounded-lg border border-slate-600 px-4 py-3 text-sm font-semibold hover:bg-slate-800"><Download size={17} /> Yuklab olish</a>
            </div>
          </div>
          <a href={PDF} target="_blank" rel="noopener noreferrer" aria-label="B2 Grammar Map PDF’ni ochish" className="hidden self-center md:block">
            <img src="/intensive/grammar-map-cover.png" alt="Jony logosi va patterni tushirilgan B2 Grammar Map muqovasi" width={180} height={255} className="rounded-lg shadow-xl" />
          </a>
        </div>
      </section>

      <section aria-labelledby="topics-title" className="mt-7">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 id="topics-title" className="text-lg font-semibold text-slate-900">Grammar mavzulari</h2>
          <label className="flex w-full items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 sm:w-72">
            <Search size={16} className="shrink-0 text-slate-400" />
            <input type="search" value={query} onChange={event => setQuery(event.target.value)} aria-label="Grammar mavzusini qidirish" placeholder="Mavzuni qidirish…" className="min-w-0 w-full bg-transparent text-sm outline-none" />
          </label>
        </div>
        <p className="mb-4 text-sm leading-6 text-slate-500">Bo‘limni ochib mavzular va misollarni ko‘ring. Bitta mavzu alohida o‘rganish qadami; har bir band alohida ikki soatlik dars degani emas.</p>
        <div className="space-y-3">
          {visible.map(module => (
            <details key={`${module.index}-${normalized}`} open={normalized ? true : undefined} className="group overflow-hidden rounded-xl border border-slate-200 bg-white">
              <summary className="flex cursor-pointer list-none items-center gap-3 p-4 [&::-webkit-details-marker]:hidden">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-sm font-bold text-brand-700">{String(module.index + 1).padStart(2, "0")}</span>
                <div className="min-w-0 flex-1"><h3 className="font-semibold text-slate-900">{module.title}</h3><p className="mt-0.5 text-xs text-slate-500">{phases[module.phase]} · {module.items.length} mavzu</p></div>
                <ChevronDown size={18} className="shrink-0 text-slate-400 transition-transform group-open:rotate-180" />
              </summary>
              <div className="border-t border-slate-100">
                <p className="bg-slate-50 px-4 py-3 text-sm leading-6 text-slate-600"><b>Natija:</b> {module.goal}</p>
                <ol className="divide-y divide-slate-100">
                  {module.items.map(([title, example], index) => (
                    <li key={index} className="flex gap-3 px-4 py-3">
                      <span className="pt-0.5 text-xs font-semibold tabular-nums text-brand-600">{String(module.index + 1).padStart(2, "0")}.{String(index + 1).padStart(2, "0")}</span>
                      <div className="min-w-0"><p className="text-sm font-medium text-slate-800">{title}</p><p className="mt-1 text-sm text-slate-500">{example}</p></div>
                    </li>
                  ))}
                </ol>
              </div>
            </details>
          ))}
          {visible.length === 0 && <p role="status" className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">Bu qidiruvga mos mavzu topilmadi.</p>}
        </div>
      </section>

      <section className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">02 / Keyingi bosqich</p>
        <h2 className="mt-1 font-semibold text-slate-700">Vocabulary Map</h2>
        <p className="mt-1 text-sm text-slate-500">Hali tayyorlanmagan. Keyingi xarita so‘z boyligini rivojlantirishga bag‘ishlanadi.</p>
      </section>
      <p className="mt-5 text-xs leading-5 text-slate-500">B2 uchun grammatika bilan birga lug‘at, reading, listening, speaking va writing ham rivojlantiriladi.</p>
    </div>
  );
}
