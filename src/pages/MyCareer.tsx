import { useEffect, useState } from "react";
import {
  GraduationCap, TrendingUp, AlertTriangle, BookOpen, Headphones,
  Check, Info,
} from "lucide-react";
import { api, type TeacherCareer } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";

const TONE: Record<string, string> = {
  slate: "bg-slate-100 text-slate-700",
  sky: "bg-sky-100 text-sky-700",
  teal: "bg-teal-100 text-teal-700",
  violet: "bg-violet-100 text-violet-700",
  amber: "bg-amber-100 text-amber-700",
  rose: "bg-rose-100 text-rose-700",
  emerald: "bg-emerald-100 text-emerald-700",
  red: "bg-red-100 text-red-700",
};

/**
 * Ustozning O'Z karyera xaritasi.
 *
 * Maqsad — ustoz "keyingi darajaga nima qilishim kerak" degan savolga
 * bir qarashda javob topsin: hozir qaysi darajada, bir o'quvchidan
 * qancha olyapti, keyingisida qancha bo'ladi va nima yetishmayapti.
 */
export default function MyCareer() {
  const [d, setD] = useState<TeacherCareer | null>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const [tab, setTab] = useState<"yol" | "oqish" | "tarix">("yol");

  function load() {
    api
      .get<TeacherCareer>("/me/career")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }
  useEffect(load, []);

  async function toggle(id: number, done: boolean) {
    if (!d) return;
    setBusy(id);
    try {
      await api.post(`/teachers/${d.state.teacher_id}/study/${id}`, { done });
      load();
    } finally {
      setBusy(null);
    }
  }

  if (err)
    return <p className="text-sm text-slate-500 py-10 text-center">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const s = d.state;
  const idx = d.grades.findIndex((g) => g.key === s.grade);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <GraduationCap size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Mening yo'lim</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Daraja, stavka va keyingi bosqichgacha nima qolgani
      </p>

      {/* Katta karta */}
      <div className="rounded-2xl bg-gradient-to-br from-brand-600 to-brand-800 text-white p-6 mb-5">
        <p className="text-sm opacity-80">Hozirgi darajangiz</p>
        <p className="text-3xl font-semibold mt-1">{s.grade_label}</p>
        <p className="text-lg mt-1">
          {formatSom(s.rate_per_student)}
          <span className="text-sm opacity-80"> — har bir o'quvchidan</span>
        </p>
        <div className="flex flex-wrap gap-5 mt-4 text-sm">
          <div>
            <p className="opacity-70 text-xs">Tajriba</p>
            <p>{Math.round(s.months)} oy</p>
          </div>
          <div>
            <p className="opacity-70 text-xs">Guruhlarim</p>
            <p>
              {s.groups}
              {s.max_groups ? ` / ${s.max_groups}` : ""}
            </p>
          </div>
          <div>
            <p className="opacity-70 text-xs">Bosqichdan o'tganlar</p>
            <p>
              {s.pass_rate !== null && s.pass_rate !== undefined
                ? `${s.pass_rate}%`
                : "—"}
            </p>
          </div>
          <div>
            <p className="opacity-70 text-xs">Oylik test o'rtachasi</p>
            <p>
              {s.test_avg !== null && s.test_avg !== undefined
                ? `${s.test_avg}%`
                : "—"}
            </p>
          </div>
        </div>
      </div>

      {s.in_remediation && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 mb-5">
          <div className="flex items-center gap-1.5 mb-1">
            <AlertTriangle size={13} className="text-amber-600" />
            <p className="text-sm font-medium text-amber-800">
              Qayta tayyorlash bosqichi
            </p>
          </div>
          <p className="text-xs text-amber-700">{s.remediation_reason}</p>
          <p className="text-xs text-amber-600 mt-1">
            {s.remediation_until} da qayta test. Shu vaqtgacha yangi guruh
            ochilmaydi — o'ta olmagan o'quvchilar bilan ishlashga vaqt
            beriladi.
          </p>
        </div>
      )}

      <div className="flex gap-1 border-b border-slate-200 mb-5">
        {(
          [
            ["yol", "Daraja yo'li"],
            ["oqish", "O'qish rejasi"],
            ["tarix", "Tarix"],
          ] as const
        ).map(([k, l]) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px ${
              tab === k
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {l}
          </button>
        ))}
      </div>

      {tab === "yol" && (
        <div>
          <div className="space-y-2 mb-5">
            {d.grades.map((g, i) => {
              const cur = i === idx;
              const passed = i < idx;
              return (
                <div
                  key={g.key}
                  className={`rounded-xl border p-4 flex flex-wrap items-center gap-3 ${
                    cur
                      ? "border-brand-400 bg-brand-50"
                      : passed
                        ? "border-emerald-200 bg-emerald-50/50"
                        : "border-slate-200 bg-white"
                  }`}
                >
                  <span
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-medium shrink-0 ${
                      passed
                        ? "bg-emerald-500 text-white"
                        : cur
                          ? "bg-brand-600 text-white"
                          : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    {passed ? <Check size={13} /> : i + 1}
                  </span>
                  <div className="flex-1 min-w-[140px]">
                    <p
                      className={`text-sm font-medium ${
                        cur ? "text-brand-800" : "text-slate-800"
                      }`}
                    >
                      {g.label}
                      {cur && (
                        <span className="text-xs font-normal text-brand-600">
                          {" "}
                          — hozir shu yerdasiz
                        </span>
                      )}
                    </p>
                    <p className="text-xs text-slate-400">
                      {g.min_months} oy tajriba · {g.cert_label || "—"} ·{" "}
                      {g.min_groups === g.max_groups
                        ? `${g.max_groups} ta guruh`
                        : `${g.min_groups}-${g.max_groups} ta guruh`}
                    </p>
                  </div>
                  <span
                    className={`text-sm font-medium ${
                      cur ? "text-brand-800" : "text-slate-600"
                    }`}
                  >
                    {formatSom(g.rate_per_student)}
                  </span>
                  {g.promote_pass_rate && (
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs ${
                        TONE[g.tone] || TONE.slate
                      }`}
                    >
                      {g.promote_pass_rate}% o'tsa keyingisi
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          {s.next_label ? (
            <div
              className={`rounded-xl border p-5 ${
                s.ready
                  ? "border-emerald-300 bg-emerald-50"
                  : "border-slate-200 bg-white"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp
                  size={15}
                  className={s.ready ? "text-emerald-600" : "text-brand-500"}
                />
                <p className="text-sm font-medium text-slate-800">
                  {s.next_label} bo'lish uchun
                </p>
                <span className="text-xs text-slate-500">
                  {formatSom(s.next_rate || 0)} / o'quvchi
                </span>
              </div>
              {s.ready ? (
                <p className="text-sm text-emerald-700">
                  Hamma shart bajarilgan. Tizim darajani o'zi ko'taradi —
                  hech kimdan so'rash shart emas.
                </p>
              ) : (
                <ul className="space-y-2 mt-2">
                  {s.missing.map((m) => (
                    <li
                      key={m.key}
                      className="flex items-start gap-2 text-sm text-slate-600"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-2 shrink-0" />
                      {m.text}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <div className="rounded-xl border border-brand-200 bg-brand-50 p-5">
              <p className="text-sm text-brand-800">
                Eng yuqori darajadasiz. Rahmat!
              </p>
            </div>
          )}

          <p className="text-xs text-slate-500 mt-4 flex items-start gap-1.5">
            <Info size={11} className="mt-0.5 shrink-0" />
            Daraja o'zgarsa stavka ham o'zi o'zgaradi. O'tgan oylarning
            oyligi qayta hisoblanmaydi — u eski stavkada qoladi.
          </p>
        </div>
      )}

      {tab === "oqish" && (
        <div className="space-y-5">
          {d.study.map((st) => (
            <div key={st.key}>
              <div className="flex items-center gap-2 mb-2">
                <p className="text-sm font-medium text-slate-700">
                  {st.label}
                </p>
                <span
                  className={`text-xs ${
                    st.done === st.total
                      ? "text-emerald-600"
                      : "text-slate-400"
                  }`}
                >
                  {st.done}/{st.total}
                </span>
                <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden max-w-[220px]">
                  <div
                    className={`h-full rounded-full ${
                      st.done === st.total ? "bg-emerald-500" : "bg-brand-400"
                    }`}
                    style={{
                      width: `${st.total ? (st.done / st.total) * 100 : 0}%`,
                    }}
                  />
                </div>
              </div>
              <div className="space-y-1">
                {st.items.map((i) => (
                  <label
                    key={i.id}
                    className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg border cursor-pointer transition ${
                      i.done
                        ? "border-emerald-200 bg-emerald-50"
                        : "border-slate-100 bg-white hover:border-slate-300"
                    } ${busy === i.id ? "opacity-50" : ""}`}
                  >
                    <input
                      type="checkbox"
                      checked={i.done}
                      disabled={busy === i.id}
                      onChange={(e) => toggle(i.id, e.target.checked)}
                    />
                    {i.kind === "book" ? (
                      <BookOpen size={14} className="text-slate-400 shrink-0" />
                    ) : (
                      <Headphones
                        size={14}
                        className="text-slate-400 shrink-0"
                      />
                    )}
                    <span
                      className={`text-sm flex-1 ${
                        i.done ? "text-emerald-800" : "text-slate-700"
                      }`}
                    >
                      {i.title}
                    </span>
                    {i.done_at && (
                      <span className="text-xs text-slate-400">
                        {formatDate(i.done_at)}
                      </span>
                    )}
                  </label>
                ))}
              </div>
            </div>
          ))}
          <p className="text-xs text-slate-500">
            97/3 qoidasi: sohangiz bo'yicha 3 ta kitob o'qisangiz, 97%
            odamdan oldinda bo'lasiz. Ro'yxatni o'zingiz belgilaysiz.
          </p>
        </div>
      )}

      {tab === "tarix" && (
        <div className="space-y-2">
          {d.history.length === 0 ? (
            <p className="text-sm text-slate-400 py-6">Hali o'zgarish yo'q.</p>
          ) : (
            d.history.map((h) => (
              <div
                key={h.id}
                className="rounded-lg border border-slate-100 bg-white p-3 flex flex-wrap items-start gap-2"
              >
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                    TONE[h.tone] || TONE.slate
                  }`}
                >
                  {h.kind_label}
                </span>
                <div className="flex-1 min-w-[180px]">
                  <p className="text-sm text-slate-800">
                    {h.from_label && h.from_label !== h.to_label
                      ? `${h.from_label} → ${h.to_label}`
                      : h.to_label}
                  </p>
                  <p className="text-xs text-slate-500">{h.reason}</p>
                </div>
                <p className="text-xs text-slate-400">
                  {h.date ? formatDate(h.date) : "—"}
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
