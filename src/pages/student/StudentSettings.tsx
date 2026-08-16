import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, Save, X } from "lucide-react";
import { api } from "../../lib/api";

/**
 * JONY STUDENT — SOZLAMALAR (2026-08-16).
 *
 * Profil sahifasi dizayn bo'yicha qayta yozilganda undagi TAHRIRLASH
 * formasi yo'qolib qolmasin uchun shu yerga ko'chirildi (profildagi
 * tishli g'ildirak orqali ochiladi). Maydonlar va manzil o'sha-o'sha:
 * PUT /api/student/profile.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

const FIELDS: [string, string, string][] = [
  ["last_name", "Familiya", "Nazarov"],
  ["first_name", "Ism", "Doniyor"],
  ["middle_name", "Otasining ismi", "Aziz o'g'li"],
  ["birth_date", "Tug'ilgan sana", "2010-05-14"],
  ["school", "Maktab", "21-maktab"],
  ["school_grade", "Sinf", "9-A"],
  ["address", "Manzil", "Bekobod, Zafar MFY"],
];

export default function StudentSettings() {
  const [p, setP] = useState<Any>(null);
  const [form, setForm] = useState<Any>({});
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

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
      setMsg("Saqlandi");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  if (!p && !err)
    return (
      <p className="text-sm text-slate-400 text-center py-20">Yuklanmoqda…</p>
    );

  return (
    <>
      <div className="bg-brand-600 text-white px-4 pt-6 pb-12">
        <div className="max-w-md mx-auto">
          <Link
            to="/student/profile"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Profil
          </Link>
          <h1 className="text-xl font-bold">Sozlamalar</h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 pb-8 space-y-3">
        {msg && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 flex gap-2 items-center">
            <Check size={16} className="text-emerald-600" />
            <p className="text-sm text-emerald-800 flex-1">{msg}</p>
            <button onClick={() => setMsg("")} className="text-emerald-500">
              <X size={15} />
            </button>
          </div>
        )}
        {err && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-3">
            <p className="text-sm text-red-700">{err}</p>
          </div>
        )}

        <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
          {FIELDS.map(([k, label, ph]) => (
            <div key={k}>
              <label className="block text-[11px] text-slate-500 mb-1">
                {label}
              </label>
              <input
                value={form[k] || ""}
                onChange={(e) => setForm({ ...form, [k]: e.target.value })}
                placeholder={ph}
                className="w-full rounded-xl border border-slate-200 px-3.5 py-2.5 text-sm focus:border-brand-400 outline-none"
              />
            </div>
          ))}

          <div>
            <label className="block text-[11px] text-slate-500 mb-1">
              Login (raqam)
            </label>
            <input
              value={p?.phone || ""}
              disabled
              className="w-full rounded-xl border border-slate-100 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-400"
            />
            <p className="text-[11px] text-slate-400 mt-1">
              Login va parolni administrator o'zgartiradi.
            </p>
          </div>
        </div>

        <button
          onClick={save}
          disabled={busy}
          className="w-full py-3.5 rounded-xl bg-brand-600 text-white font-semibold flex items-center justify-center gap-2 disabled:opacity-60"
        >
          <Save size={17} />
          {busy ? "Saqlanmoqda…" : "Saqlash"}
        </button>
      </div>
    </>
  );
}
