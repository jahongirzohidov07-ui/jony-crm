import { useEffect, useMemo, useState } from "react";
import { BrandIcon } from "../components/BrandIcon";
import { ArrowRight, BookOpen, Check, ChevronDown, Gift, Globe2, GraduationCap, Languages, LoaderCircle, MapPin, Phone, ShieldCheck, UserRound } from "lucide-react";
import "./Ariza.css";

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


  async function submit() {
    if (busy) return;
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

  const brand = <a className="ariza-brand" href="/ariza" aria-label="Jony Academy"><BrandIcon size={48} /><span>JONY ACADEMY</span></a>;

  return (
    <div className="ariza-page">
      <div className="ariza-shell">
        <header className="ariza-header">
          {brand}
          <span className="ariza-header-note">Yangi bilim. Yangi imkoniyat.</span>
          <a className="ariza-header-cta" href="#ariza-form">Bepul sinov darsi <ArrowRight size={18} /></a>
        </header>
        {done !== null ? (
          <main className="ariza-success" role="status" aria-live="polite">
            <div className="ariza-success-check"><Check size={38} /></div>
            <p className="ariza-eyebrow">BIRINCHI QADAM QO‘YILDI</p>
            <h1>Rahmat, {first.trim()}!</h1>
            <p>Arizangiz qabul qilindi. {done ? <><strong>{done}</strong> filialimiz </> : "Administratorimiz "}
              tez orada <strong>+998 {fmtPhone(digits)}</strong> raqamiga qo‘ng‘iroq qilib,
              <strong> {lang.toLowerCase()}</strong> bo‘yicha bepul sinov darsiga yozib qo‘yadi.</p>
            <div className="ariza-success-next"><Phone size={20} /> Telefoningizni yoningizda tuting.</div>
          </main>
        ) : (
          <main className="ariza-main">
            <section className="ariza-hero" aria-labelledby="ariza-title">
              <p className="ariza-eyebrow">TIL O‘RGANING. DUNYONI KASHF ETING.</p>
              <h1 id="ariza-title">Kelajagingizga<br /><span>yangi yo‘l oching.</span></h1>
              <p className="ariza-intro">Bepul sinov darsidan boshlang.<br />Sizga mos til va filialni birga tanlaymiz.</p>
              <div className="ariza-scene" aria-hidden="true">
                <div className="ariza-orbit"><i /><i /></div>
                <img className="ariza-globe" src="/ariza/globe.png" alt="" fetchPriority="high" width="640" height="640" />
                <div className="ariza-float ariza-book"><BookOpen /></div>
                <div className="ariza-float ariza-cap"><GraduationCap /></div>
                <div className="ariza-float ariza-language"><Languages /></div>
                <div className="ariza-scene-caption"><span />Yangi bilim.<br />Yangi imkoniyat.<br />Yanada kengroq dunyo.</div>
              </div>
              <div className="ariza-benefits">
                <div><span><MapPin /></span><p><b>Qulay filiallar</b><small>Sizga yaqin manzillar</small></p></div>
                <div><span><Globe2 /></span><p><b>5 ta til</b><small>Dunyo tillarini o‘rganing</small></p></div>
                <div><span><Gift /></span><p><b>Bepul sinov</b><small>Avval sinab ko‘ring</small></p></div>
              </div>
            </section>
            <section className="ariza-card" id="ariza-form" aria-labelledby="ariza-form-title">
              <div className="ariza-form-heading">
                <span className="ariza-cap-badge"><GraduationCap size={30} /></span>
                <div><h2 id="ariza-form-title">Bepul darsga yoziling</h2><p>Ma’lumot qoldiring — siz bilan bog‘lanamiz.</p></div>
              </div>
              <form onSubmit={(e) => { e.preventDefault(); void submit(); }}>
                <fieldset disabled={busy} className="ariza-fields">
                  <legend className="ariza-sr-only">Sinov darsiga ariza</legend>
                  <div className="ariza-name-row">
                    <div><label htmlFor="ariza-first">Ism</label><div className="ariza-input"><UserRound /><input id="ariza-first" name="first_name" autoComplete="given-name" placeholder="Ismingiz" value={first} onChange={(e) => setFirst(e.target.value)} required minLength={2} maxLength={80} /></div></div>
                    <div><label htmlFor="ariza-last">Familiya</label><div className="ariza-input"><UserRound /><input id="ariza-last" name="last_name" autoComplete="family-name" placeholder="Familiyangiz" value={last} onChange={(e) => setLast(e.target.value)} required minLength={2} maxLength={80} /></div></div>
                  </div>
                  <div className="ariza-field">
                    <label htmlFor="ariza-phone">Telefon raqam</label>
                    <div className="ariza-input ariza-phone"><Phone /><span>+998</span>
                      <input id="ariza-phone" name="phone" type="tel" inputMode="numeric" autoComplete="tel-national" placeholder="90 123 45 67" value={fmtPhone(digits)} required
                        onChange={(e) => { let d = e.target.value.replace(/[^0-9]/g, ""); if (d.startsWith("998") && d.length > 9) d = d.slice(3); setDigits(d.slice(0, 9)); }} />
                      {phoneOk && <Check className="ariza-phone-check" />}
                    </div>
                  </div>
                  <div className="ariza-field">
                    <label htmlFor="ariza-branch">Sizga qulay filial</label>
                    <div className="ariza-input ariza-select"><MapPin />
                      <select id="ariza-branch" name="branch_id" value={branchId ?? ""} onChange={(e) => setBranchId(e.target.value ? Number(e.target.value) : null)} required disabled={!branches?.length}>
                        <option value="">{branches === null ? "Filiallar yuklanmoqda…" : !branches.length ? "Filiallar yuklanmadi" : "Filialni tanlang"}</option>
                        {branches?.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
                      </select><ChevronDown className="ariza-chevron" />
                    </div>
                    {branches?.length === 0 && <p className="ariza-load-error" role="alert">Filiallarni yuklab bo‘lmadi. <button type="button" onClick={() => window.location.reload()}>Qayta yuklash</button></p>}
                  </div>
                  <fieldset className="ariza-languages">
                    <legend>Qaysi tilni o‘rganmoqchisiz?</legend>
                    <div className="ariza-language-grid">{TILLAR.map((t, i) => (
                      <label className={"ariza-language-choice" + (lang === t.v ? " is-selected" : "")} key={t.v}>
                        <input type="radio" name="language" value={t.v} checked={lang === t.v} onChange={() => setLang(t.v)} required />
                        <span className={"ariza-flag ariza-flag-" + i} aria-hidden="true">{i === 3 ? "☾" : i === 4 ? "☯" : ""}{i === 3 && <i>★</i>}</span>
                        <span>{t.v}</span>
                        {lang === t.v && <Check className="ariza-choice-check" size={16} />}
                      </label>
                    ))}</div>
                  </fieldset>
                  <input name="website" value={hp} onChange={(e) => setHp(e.target.value)} tabIndex={-1} autoComplete="off" aria-hidden="true" className="ariza-honeypot" />
                  {err && <p className="ariza-error" role="alert">{err}</p>}
                  <button className="ariza-submit" type="submit" disabled={busy || !branches?.length}>
                    {busy ? <><LoaderCircle className="ariza-spinner" size={20} /> Yuborilmoqda…</> : <>Bepul darsga yozilish <ArrowRight size={22} /></>}
                  </button>
                </fieldset>
                <p className="ariza-privacy"><ShieldCheck size={17} /> Raqamingiz faqat bog‘lanish uchun ishlatiladi.</p>
              </form>
              <footer className="ariza-card-footer"><span>Jony Academy</span><span>jonyos.uz</span></footer>
            </section>
          </main>
        )}
      </div>
    </div>
  );
}