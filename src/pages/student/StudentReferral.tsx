import { JsaLogo } from "../../components/Jsa";
import { StudentIcon } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import {
  Copy, Check, Share2, Users, Clock, TrendingUp, Info,
} from "lucide-react";
import { api } from "../../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * JONY STUDENT — "DO'STINGNI OLIB KEL" (2026-08-28).
 *
 * Jahongir: "referallar holati ko'rinib turishi kerak".
 *
 * Ekran to'rt qismdan iborat, tepadan pastga — bola nima qilishi
 * kerakligini bilib olsin:
 *   1. HOZIRGI HOLAT — nechta do'st to'lagan, qancha chegirma
 *   2. HAVOLA — bir bosishda nusxa / ulashish
 *   3. PILLAPOYA — 10 -> 30 -> 50 -> 75 -> 100%, qayerdaligi ko'rinib
 *   4. DO'STLAR — kim qaysi bosqichda
 *
 * QO'SHILMASLIK ochiq yozilgan: bola "10+30=40 bo'ladi" deb
 * o'ylab, keyin xafa bo'lmasin.
 */

const som = (n: number) =>
  (Math.round(n) || 0).toLocaleString("ru-RU").replace(/,/g, " ");

const STAGE: Record<string, { t: string; c: string }> = {
  invited: { t: "Ro'yxatdan o'tdi", c: "bg-slate-100 text-slate-600" },
  processing: { t: "Admin bog'lanmoqda", c: "bg-amber-100 text-amber-700" },
  enrolled: { t: "Guruhga qo'shildi", c: "bg-sky-100 text-sky-700" },
  paid: { t: "To'lov qildi ✓", c: "bg-emerald-100 text-emerald-700" },
};

export default function StudentReferral() {
  const [d, setD] = useState<any>(null);
  const [err, setErr] = useState("");
  const [copied, setCopied] = useState("");

  useEffect(() => {
    // 2026-09-06: manzil "/api/student/referral" yozilgan edi, api.get
    // esa o'zi "/api" qo'shadi -> "/api/api/..." -> 404. Sahifa hech
    // qachon ochilmagan.
    api.get<any>("/student/referral")
      .then(setD)
      .catch((e) => setErr(e?.message || "Yuklab bo'lmadi"));
  }, []);

  async function copy(what: string, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(what);
      setTimeout(() => setCopied(""), 1800);
    } catch {
      setErr("Nusxa olinmadi — matnni qo'lda belgilab oling");
    }
  }

  async function share() {
    const nav: any = navigator;
    if (nav.share) {
      try {
        await nav.share({ title: "Jony Academy", text: d.share_text });
        return;
      } catch { /* foydalanuvchi bekor qildi */ }
    }
    copy("share", d.share_text);
  }

  if (err)
    return (
      <div className="p-4">
        <div className="rounded-2xl bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {err}
        </div>
      </div>
    );
  if (!d) return <div className="p-4 text-sm text-slate-400">Yuklanmoqda...</div>;

  const lvl = d.level as number;

  return (
    <div className="max-w-md mx-auto p-4 pb-8 space-y-4">
      <JsaLogo />
      {/* ---- 1. HOLAT ---- */}
      <div className="student-hero student-pattern rounded-3xl bg-gradient-to-br from-violet-600 to-brand-600 p-5 text-white shadow-lg">
        <div className="flex items-center gap-2 mb-3">
          <StudentIcon name="gift" size={46} />
          <h1 className="text-xl font-bold">Do'stingni olib kel</h1>
        </div>
        <p className="text-4xl font-extrabold leading-none">
          {d.percent}%
        </p>
        <p className="text-white/85 text-sm mt-1">
          {lvl > 0
            ? `${d.paid_this_month} ta do'sting to'lov qildi — chegirmang tayyor`
            : "Hali chegirma yo'q — birinchi do'stingni taklif qil"}
        </p>
        {lvl > 0 ? (
          <div className="mt-3 rounded-2xl bg-white/15 p-3">
            <p className="text-xs text-white/80">Chegirma summasi</p>
            <p className="text-xl font-bold">{som(d.amount)} so'm</p>
            <p className="text-[11px] text-white/70 mt-0.5">
              {d.target_period} oyiga · to'laydigan summangdan hisoblangan
            </p>
          </div>
        ) : null}
        <p className="text-xs text-white/85 mt-3 flex items-start gap-1.5">
          <TrendingUp size={14} className="mt-0.5 shrink-0" />
          {d.next_hint}
        </p>
      </div>

      {/* ---- 2. HAVOLA ---- */}
      <div className="student-panel rounded-2xl bg-white border border-slate-200 p-4">
        <p className="text-sm font-bold text-slate-900 mb-1">Sening havolang</p>
        <p className="text-xs text-slate-500 mb-3">
          Shu havolani do'stingga yubor. U ariza qoldirsa, sen bilan
          bog'lanishi avtomat ko'rinadi.
        </p>
        <div className="flex items-center gap-2 rounded-xl bg-slate-50 border border-slate-200 px-3 py-2.5">
          <span className="text-xs text-slate-700 truncate flex-1">{d.link}</span>
          <button
            className="shrink-0 rounded-lg bg-slate-900 px-2.5 py-1.5 text-white"
            onClick={() => copy("link", d.link)}
            title="Nusxa olish"
          >
            {copied === "link" ? <Check size={14} /> : <Copy size={14} />}
          </button>
        </div>
        <button
          className="mt-3 w-full rounded-xl bg-brand-600 py-3 text-white text-sm font-bold
                     hover:bg-brand-700 flex items-center justify-center gap-2"
          onClick={share}
        >
          <Share2 size={16} />
          {copied === "share" ? "Matn nusxalandi!" : "Tayyor matn bilan ulashish"}
        </button>
        <details className="mt-3">
          <summary className="text-xs text-slate-500 cursor-pointer">
            Yuboriladigan matnni ko'rish
          </summary>
          <p className="mt-2 text-xs text-slate-600 whitespace-pre-line
                        rounded-xl bg-slate-50 p-3 leading-relaxed">
            {d.share_text}
          </p>
        </details>
      </div>

      {/* ---- 3. PILLAPOYA ---- */}
      <div className="student-panel rounded-2xl bg-white border border-slate-200 p-4">
        <p className="text-sm font-bold text-slate-900 mb-3">Chegirma pillapoyasi</p>
        <div className="space-y-2">
          {d.ladder.map((s: any) => {
            const done = lvl >= s.n;
            const now = lvl === s.n;
            return (
              <div
                key={s.n}
                className={"flex items-center gap-3 rounded-xl px-3 py-2.5 border "
                  + (now
                    ? "bg-violet-50 border-violet-300"
                    : done
                      ? "bg-emerald-50 border-emerald-200"
                      : "bg-slate-50 border-slate-200")}
              >
                <span className={"w-7 h-7 rounded-full grid place-items-center text-xs font-bold "
                  + (done ? "bg-emerald-500 text-white" : "bg-white text-slate-500 border border-slate-300")}>
                  {done ? <Check size={14} /> : s.n}
                </span>
                <span className="text-sm text-slate-700 flex-1">
                  {s.n}-do'st to'lov qilsa
                </span>
                <span className={"text-sm font-extrabold "
                  + (done ? "text-emerald-700" : "text-slate-400")}>
                  {s.percent}%
                </span>
              </div>
            );
          })}
        </div>
        <div className="mt-3 rounded-xl bg-amber-50 border border-amber-200 p-3 flex gap-2">
          <Info size={15} className="text-amber-600 shrink-0 mt-0.5" />
          <p className="text-xs text-amber-800 leading-relaxed">
            Foizlar <b>qo'shilmaydi</b>. 2 ta do'st olib kelsang 30% bo'ladi
            (10+30=40% emas) — har bir daraja oldingisini almashtiradi.
          </p>
        </div>
      </div>

      {/* ---- 4. DO'STLAR ---- */}
      <div className="student-panel rounded-2xl bg-white border border-slate-200 p-4">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
            <Users size={16} /> Taklif qilganlaring
          </p>
          <span className="text-xs text-slate-500">{d.total_invited} ta</span>
        </div>
        {d.friends.length === 0 ? (
          <p className="text-xs text-slate-400 py-3 text-center">
            Hali hech kim yo'q. Havolangni yuborishdan boshla!
          </p>
        ) : (
          <div className="space-y-2">
            {d.friends.map((f: any) => {
              const st = STAGE[f.stage] || STAGE.invited;
              const thisMonth = f.period === d.period;
              return (
                <div
                  key={`${f.kind}-${f.id}`}
                  className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2.5"
                >
                  <span className="text-sm text-slate-800 flex-1 truncate">
                    {f.name}
                  </span>
                  {f.stage === "paid" && !thisMonth ? (
                    <span className="text-[10px] text-slate-400">
                      {f.period}
                    </span>
                  ) : null}
                  <span className={"text-[11px] px-2 py-1 rounded-full font-medium " + st.c}>
                    {st.t}
                  </span>
                </div>
              );
            })}
          </div>
        )}
        {d.paid_other_months > 0 ? (
          <p className="mt-3 text-[11px] text-slate-500 flex items-start gap-1.5">
            <Clock size={13} className="mt-0.5 shrink-0" />
            {d.paid_other_months} ta do'sting boshqa oyda to'lagan — chegirma
            har oy qaytadan hisoblanadi, shuning uchun ular bu oyga
            qo'shilmaydi.
          </p>
        ) : null}
      </div>

      {/* ---- QOIDALAR ---- */}
      <div className="rounded-2xl bg-slate-900 p-4">
        <p className="text-sm font-bold text-white mb-2">Qoidalar</p>
        <ul className="space-y-1.5">
          {d.rules.map((r: string, i: number) => (
            <li key={i} className="text-xs text-white/75 flex gap-2 leading-relaxed">
              <span className="text-white/40">{i + 1}.</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* ---- TARIX ---- */}
      {d.history.length > 0 ? (
        <div className="student-panel rounded-2xl bg-white border border-slate-200 p-4">
          <p className="text-sm font-bold text-slate-900 mb-2">
            Olgan chegirmalaring
          </p>
          <div className="space-y-2">
            {d.history.map((h: any, i: number) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="text-slate-500 w-16">{h.period}</span>
                <span className="font-semibold text-slate-800 flex-1">
                  {som(h.amount)} so'm
                </span>
                <span className={"px-2 py-0.5 rounded-full text-[11px] "
                  + (h.status === "active"
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-slate-100 text-slate-500")}>
                  {h.status === "active"
                    ? (h.applied ? "Balansga tushdi" : "Kutilmoqda")
                    : "Bekor qilingan"}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
