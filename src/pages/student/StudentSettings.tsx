import { StudentImage } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, ChevronRight, Save, X } from "lucide-react";
import { api } from "../../lib/api";
import { BrandIcon } from "../../components/BrandIcon";

/**
 * JONY STUDENT — SOZLAMALAR.
 *
 * 2026-08-21: "sozlamalar.png" dizayni bo'yicha to'q temada qayta
 * terildi (Jahongir: "hammasini 1ga 1 qilib ber"). Maydonlar va
 * manzil o'sha-o'sha: PUT /api/student/profile. Til va parol
 * bo'limlari ma'lumot sifatida ko'rsatiladi (parolni administrator
 * o'zgartiradi).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const FIELDS: [string, string, string, string][] = [
  ["first_name", "Ism", "Doniyor", "👤"],
  ["last_name", "Familiya", "Nazarov", "👥"],
  ["middle_name", "Otasining ismi", "Aziz o'g'li", "👤"],
  ["birth_date", "Tug'ilgan sana", "2010-05-14", "📅"],
  ["school", "Maktab", "21-maktab", "🎓"],
  ["school_grade", "Sinf", "9-A", "🏫"],
  ["address", "Manzil", "Bekobod, Zafar MFY", "📍"],
];

export default function StudentSettings() {
  const [p, setP] = useState<Any>(null);
  const [form, setForm] = useState<Any>({});
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [edit, setEdit] = useState<string | null>(null);

  useEffect(() => {
    api
      .fresh<Any>("/student/profile")
      .then((r) => {
        setP(r);
        const f: Any = {};
        FIELDS.forEach(([k]) => (f[k] = r[k] || ""));
        setForm(f);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  async function save() {
    setBusy(true);
    setErr("");
    try {
      await api.put("/student/profile", form);
      setMsg("O'zgarishlar saqlandi");
      setEdit(null);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  if (!p && !err)
    return <p className="text-sm text-slate-500 text-center py-20">Yuklanmoqda…</p>;

  const Section = ({ icon, title, children }: any) => (
    <div className="student-panel bg-white rounded-3xl p-4">
      <p className="flex items-center gap-2.5 text-[19px] font-extrabold text-slate-900 mb-1">
        <span className="w-9 h-9 rounded-full bg-brand-600 text-white flex items-center justify-center text-[16px]">
          {icon}
        </span>
        {title}
      </p>
      <div className="divide-y divide-slate-100">{children}</div>
    </div>
  );

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8 space-y-4">
      <div className="flex items-center gap-2.5">
        <Link to="/student/profile"
          className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
          style={{ background: "#0c2258", borderColor: "#35538c" }}>
          <ArrowLeft size={18} />
        </Link>
        <div className="flex-1 flex items-center justify-center gap-2.5">
          <BrandIcon size={36} />
          <div className="leading-none">
            <p className="text-[14px] font-extrabold text-white">JONY</p>
            <p className="text-[14px] font-extrabold text-white">STUDENT APP</p>
          </div>
        </div>
        <span className="w-10" />
      </div>

      <h1 className="text-[34px] font-extrabold text-white leading-none">
        Sozlamalar
      </h1>

      {msg && (
        <div className="bg-emerald-500/10 border border-emerald-500/40 rounded-xl p-3 flex gap-2 items-center">
          <Check size={16} className="text-emerald-400" />
          <p className="text-sm text-emerald-300 flex-1">{msg}</p>
          <button onClick={() => setMsg("")} className="text-emerald-400">
            <X size={15} />
          </button>
        </div>
      )}
      {err && (
        <div className="bg-red-500/10 border border-red-500/40 rounded-xl p-3">
          <p className="text-sm text-red-300">{err}</p>
        </div>
      )}

      {/* ---------------------------------------- foydalanuvchi */}
      <div className="student-hero student-pattern rounded-3xl p-4 flex items-center gap-4"
           style={{ background:
             "linear-gradient(110deg,#14257C,#1D2F8E 70%)" }}>
        <div className="w-[74px] h-[74px] rounded-full bg-brand-600 border-4 border-brand-400/70 overflow-hidden flex items-center justify-center shrink-0">
          {p?.photo ? (
            <StudentImage src={p.photo} alt="" className="w-full h-full object-cover" />
          ) : (
            <span className="text-[28px] font-extrabold text-white">
              {(p?.first_name || p?.full_name || "?").charAt(0)}
            </span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[24px] font-extrabold text-white truncate">
            {p?.first_name || p?.full_name}
          </p>
          <p className="text-[13px] text-white/70 mt-0.5">
            Jony Student App foydalanuvchisi
          </p>
        </div>
      </div>

      {/* ------------------------------------- shaxsiy ma'lumotlar */}
      <Section icon="👤" title="Shaxsiy ma'lumotlar">
        {FIELDS.map(([k, label, ph, emoji]) => (
          <div key={k} className="py-1">
            <button
              onClick={() => setEdit(edit === k ? null : k)}
              className="w-full flex items-center gap-3 py-2 text-left"
            >
              <span className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center text-[15px] shrink-0">
                {emoji}
              </span>
              <span className="text-[15px] font-semibold text-slate-800 flex-1">
                {label}
              </span>
              <span className="text-[15px] text-slate-500 truncate max-w-[150px]">
                {form[k] || "—"}
              </span>
              <ChevronRight size={16} className="text-slate-300 shrink-0" />
            </button>
            {edit === k && (
              <input
                autoFocus
                value={form[k] || ""}
                onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                placeholder={ph}
                className="w-full rounded-xl border border-brand-300 px-3.5 py-2.5 text-sm outline-none mb-2"
              />
            )}
          </div>
        ))}
      </Section>

      {/* ------------------------------------------------ xavfsizlik */}
      <Section icon="🛡" title="Xavfsizlik">
        <div className="flex items-center gap-3 py-3">
          <span className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center text-[15px] shrink-0">
            🔒
          </span>
          <span className="text-[15px] font-semibold text-slate-800 flex-1">
            Parolni o'zgartirish
          </span>
          <span className="text-[13px] text-slate-400">administrator orqali</span>
        </div>
        <div className="flex items-center gap-3 py-3">
          <span className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center text-[15px] shrink-0">
            👤
          </span>
          <span className="text-[15px] font-semibold text-slate-800 flex-1">
            Login
          </span>
          <span className="text-[15px] text-slate-500">{p?.phone || "—"}</span>
        </div>
      </Section>

      <button
        onClick={save}
        disabled={busy}
        className="w-full py-4 rounded-2xl bg-brand-600 text-white text-[17px] font-bold flex items-center justify-center gap-2.5 disabled:opacity-60"
      >
        <Save size={18} />
        {busy ? "Saqlanmoqda…" : "O'zgarishlarni saqlash"}
      </button>
    </div>
  );
}
