import { useEffect, useMemo, useState } from "react";
import { BrandIcon } from "../components/BrandIcon";

/**
 * OCHIQ ARIZA SAHIFASI — jonyos.uz/ariza (loginsiz, 2026-09-27).
 *
 * Jahongir: "shunaqa linkimiz bor edi (modme.uz forma), eski CRMda buni
 * o'zgartirib judayam dizaynini ko'zga yoqadigan professional qilib
 * odamga o'zini ma'lumotlarini qoldirish oson — ism familya, tel raqam
 * 998 o'zi turgan bo'lsa qolganini yozish oson bo'lsin, qaysi filial va
 * tilni tanlaydi tamom".
 *
 * Ariza tanlangan filialning Lidlar bo'limiga tushadi (POST
 * /api/public/lead, form=ariza). Instagram bio (?utm_source=ig) yoki
 * Telegramdan kelsa manba avtomat shu tarmoq bo'ladi; ?c=CONTENT-...
 * bo'lsa qaysi postdan kelgani ham yoziladi.
 */

const TILLAR = [
  { v: "Ingliz tili", flag: "🇬🇧" },
  { v: "Rus tili", flag: "🇷🇺" },
  { v: "Nemis tili", flag: "🇩🇪" },
  { v: "Turk tili", flag: "🇹🇷" },
  { v: "Koreys tili", flag: "🇰🇷" },
];

type Branch = { id: number; name: string };

function fmtPhone(d: string) {
  // 901234567 -> "90 123 45 67"
  const p = [d.slice(0, 2), d.slice(2, 5), d.slice(5, 7), d.slice(7, 9)];
  return p.filter(Boolean).join(" ");
}

export default function Ariza() {
  const qs = useMemo(() => new URLSearchParams(window.location.search), []);
  const [branches, setBranches] = useState<Branch[] | null>(null);
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [digits, setDigits] = useState("");
  const [branchId, setBranchId] = useState<number | null>(null);
  const [lang, setLang] = useState("");
  const [hp, setHp] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/public/branches")
      .then((r) => r.json())
      .then((b) => setBranches(Array.isArray(b) ? b : []))
      .catch(() => setBranches([]));
  }, []);

  const phoneOk = digits.length === 9;
  const ready = first.trim().length >= 2 && last.trim().length >= 2
    && phoneOk && !!branchId && !!lang;

  async function submit() {
    setErr("");
    if (first.trim().length < 2) return setErr("Ismingizni yozing");
    if (last.trim().length < 2) return setErr("Familiyangizni yozing");
    if (!phoneOk) return setErr("Telefon raqamini to'liq kiriting (9 ta raqam)");
    if (!branchId) return setErr("Filialni tanlang");
    if (!lang) return setErr("Qaysi tilni o'rganmoqchisiz — tanlang");
    setBusy(true);
    try {
      const page = window.location.origin + window.location.pathname;
      const res = await fetch("/api/public/lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          form: "ariza",
          first_name: first.trim(),
          last_name: last.trim(),
          phone: "+998 " + fmtPhone(digits),
          branch_id: branchId,
          language: lang,
          utm_source: qs.get("utm_source") || "",
          utm_medium: qs.get("utm_medium") || "",
          utm_content: qs.get("utm_content") || "",
          c: qs.get("c") || "",
          page,
          hp,
        }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || "Xatolik yuz berdi, qayta urinib ko'ring");
      setDone(branches?.find((b) => b.id === branchId)?.name || "");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik yuz berdi");
    } finally {
      setBusy(false);
    }
  }

  const shell = "min-h-screen bg-gradient-to-br from-brand-800 via-brand-600 to-indigo-500";

  if (done !== null)
    return (
      <div className={`${shell} flex items-center justify-center p-4`}>
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-md w-full text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-3xl">
            ✓
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900">Rahmat, {first.trim()}!</h1>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            Arizangiz qabul qilindi. {done ? <><b>{done}</b> filialimiz </> : "Administratorimiz "}
            tez orada <b>+998 {fmtPhone(digits)}</b> raqamiga qo'ng'iroq qilib,
            <b> {lang.toLowerCase()}</b> bo'yicha bepul sinov darsiga yozib qo'yadi.
          </p>
          <p className="mt-5 text-xs text-slate-400">Telefoningizni yoningizda tuting 📞</p>
        </div>
      </div>
    );

  const inp = "w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3.5 text-[15px] "
    + "text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:bg-white "
    + "focus:outline-none focus:ring-4 focus:ring-brand-100 transition";
  const lbl = "block text-[13px] font-semibold text-slate-700 mb-1.5";

  return (
    <div className={shell}>
      <div className="mx-auto max-w-lg px-4 pt-8 pb-10">
        <div className="flex flex-col items-center text-center">
          <div className="rounded-2xl bg-white p-2.5 shadow-lg">
            <BrandIcon size={44} className="rounded-xl" />
          </div>
          <p className="mt-3 text-sm font-bold tracking-[0.2em] text-white/90">JONY ACADEMY</p>
          <h1 className="mt-3 text-[28px] leading-tight font-extrabold text-white">
            Til o'rganishni bugun boshlang
          </h1>
          <p className="mt-2 text-[15px] text-white/85">
            Ma'lumotingizni qoldiring — o'zimiz qo'ng'iroq qilib,
            <b className="text-white"> bepul sinov darsiga</b> yozib qo'yamiz.
          </p>
        </div>

        <div className="mt-6 rounded-3xl bg-white p-5 sm:p-6 shadow-2xl">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={lbl}>Ism</label>
              <input className={inp} value={first} autoComplete="given-name"
                placeholder="Ismingiz" onChange={(e) => setFirst(e.target.value)} />
            </div>
            <div>
              <label className={lbl}>Familiya</label>
              <input className={inp} value={last} autoComplete="family-name"
                placeholder="Familiyangiz" onChange={(e) => setLast(e.target.value)} />
            </div>
          </div>

          <label className={`${lbl} mt-4`}>Telefon raqam</label>
          <div className={`flex items-center rounded-2xl border bg-slate-50 transition focus-within:bg-white focus-within:ring-4 focus-within:ring-brand-100 ${
            digits && !phoneOk ? "border-amber-300" : "border-slate-200 focus-within:border-brand-500"}`}>
            <span className="flex items-center gap-1.5 pl-4 pr-3 text-[15px] font-semibold text-slate-700 border-r border-slate-200 py-3.5">
              🇺🇿 +998
            </span>
            <input
              className="w-full bg-transparent px-3 py-3.5 text-[15px] tracking-wide text-slate-900 placeholder:text-slate-400 focus:outline-none"
              inputMode="numeric" autoComplete="tel-national"
              placeholder="90 123 45 67"
              value={fmtPhone(digits)}
              onChange={(e) => {
                let d = e.target.value.replace(/\D/g, "");
                if (d.startsWith("998") && d.length > 9) d = d.slice(3);
                setDigits(d.slice(0, 9));
              }}
            />
            {phoneOk && <span className="pr-4 text-emerald-600 font-bold">✓</span>}
          </div>

          <label className={`${lbl} mt-5`}>Qaysi filialimizga qatnaysiz?</label>
          {branches === null ? (
            <p className="text-sm text-slate-400">Yuklanmoqda…</p>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {branches.map((b) => {
                const on = branchId === b.id;
                return (
                  <button key={b.id} type="button" onClick={() => setBranchId(b.id)}
                    className={`rounded-2xl border-2 px-3 py-3 text-left text-[14px] font-semibold transition ${
                      on ? "border-brand-600 bg-brand-50 text-brand-800 shadow-sm"
                        : "border-slate-200 text-slate-700 hover:border-brand-300"}`}>
                    <span className="mr-1.5">📍</span>{b.name}
                  </button>
                );
              })}
            </div>
          )}

          <label className={`${lbl} mt-5`}>Qaysi tilni o'rganmoqchisiz?</label>
          <div className="flex flex-wrap gap-2">
            {TILLAR.map((t) => {
              const on = lang === t.v;
              return (
                <button key={t.v} type="button" onClick={() => setLang(t.v)}
                  className={`rounded-full border-2 px-4 py-2.5 text-[14px] font-semibold transition ${
                    on ? "border-brand-600 bg-brand-600 text-white shadow"
                      : "border-slate-200 text-slate-700 hover:border-brand-300"}`}>
                  <span className="mr-1">{t.flag}</span>{t.v}
                </button>
              );
            })}
          </div>

          {/* bot tuzog'i — odam ko'rmaydi */}
          <input value={hp} onChange={(e) => setHp(e.target.value)} tabIndex={-1}
            autoComplete="off" aria-hidden="true"
            className="absolute -left-[9999px] h-0 w-0 opacity-0" />

          {err && (
            <p className="mt-4 rounded-xl bg-red-50 px-3 py-2.5 text-sm text-red-700">{err}</p>
          )}

          <button type="button" onClick={submit} disabled={busy}
            className={`mt-5 w-full rounded-2xl py-4 text-[16px] font-extrabold text-white shadow-lg transition ${
              ready ? "bg-gradient-to-r from-brand-600 to-indigo-600 hover:brightness-110"
                : "bg-slate-300"} disabled:opacity-60`}>
            {busy ? "Yuborilmoqda…" : "Ariza qoldirish"}
          </button>
          <p className="mt-3 text-center text-[12px] text-slate-400">
            Sinov darsi bepul. Raqamingiz faqat siz bilan bog'lanish uchun ishlatiladi.
          </p>
        </div>

        <div className="mt-6 grid grid-cols-3 gap-2 text-center">
          {[
            [String(branches?.length || 5), "filial"],
            [String(TILLAR.length), "til"],
            ["1-dars", "bepul"],
          ].map(([a, b]) => (
            <div key={b} className="rounded-2xl bg-white/10 py-3 backdrop-blur border border-white/15">
              <p className="text-lg font-extrabold text-white">{a}</p>
              <p className="text-[12px] text-white/75">{b}</p>
            </div>
          ))}
        </div>
        <p className="mt-6 text-center text-[11px] text-white/60">Jony Academy · jonyos.uz</p>
      </div>
    </div>
  );
}
