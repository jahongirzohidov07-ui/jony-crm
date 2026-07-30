import { useEffect, useState } from "react";
import { Cake, Award, Copy, Check, Info, AlertTriangle } from "lucide-react";
import { api, type StaffDates, type StaffDateRow } from "../lib/api";
import { StaffCard } from "./StaffCard";

const TONE: Record<string, string> = {
  violet: "bg-violet-100 text-violet-700",
  sky: "bg-sky-100 text-sky-700",
};

/** Tabrik matni — HR o'ylab o'tirmaydi, ko'chiradi va yuboradi. */
function greeting(r: StaffDateRow): string {
  if (r.kind === "birthday") {
    return (
      `${r.full_name}, tug'ilgan kuningiz muborak bo'lsin! ` +
      "Jony Academy jamoasi sizga sog'lik, tinchlik va katta yutuqlar tilaydi."
    );
  }
  return (
    `${r.full_name}, jamoamizda ${r.years} yil bo'ldingiz! ` +
    "Mehnatingiz va sabringiz uchun rahmat — shu muhitni siz ham qurdingiz."
  );
}

function whenText(r: StaffDateRow): string {
  if (r.today) return "Bugun!";
  if (r.days_left === 1) return "Ertaga";
  return `${r.days_left} kundan keyin`;
}

/**
 * Tug'ilgan kunlar va ish yubileylari.
 *
 * Odam esdan chiqaradi, tizim chiqarmaydi: sanaga bir necha kun
 * qolganda HR'ga vazifa o'zi tushadi. Bu yerda esa butun yil oldindan
 * ko'rinib turadi.
 */
export function StaffDatesTab() {
  const [d, setD] = useState<StaffDates | null>(null);
  const [days, setDays] = useState(60);
  const [kind, setKind] = useState<string>("");
  const [copied, setCopied] = useState<string | null>(null);
  const [card, setCard] = useState<number | null>(null);

  useEffect(() => {
    api.get<StaffDates>(`/hr/dates?days=${days}`).then(setD);
  }, [days]);

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;

  const rows = kind ? d.rows.filter((r) => r.kind === kind) : d.rows;
  const missing = [
    ...new Set([...d.missing_birth_date, ...d.missing_hired_date]),
  ];

  async function copy(r: StaffDateRow) {
    const key = `${r.user_id}-${r.kind}`;
    try {
      await navigator.clipboard.writeText(greeting(r));
      setCopied(key);
      setTimeout(() => setCopied(null), 1800);
    } catch {
      /* clipboard yopiq bo'lsa — jim o'tamiz */
    }
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2 mb-4">
        <div className="flex gap-1">
          {[30, 60, 180, 366].map((n) => (
            <button
              key={n}
              onClick={() => setDays(n)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                days === n
                  ? "bg-brand-50 border-brand-400 text-brand-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {n === 366 ? "Bir yil" : `${n} kun`}
            </button>
          ))}
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => setKind("")}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
              kind === ""
                ? "bg-slate-100 border-slate-300 text-slate-700"
                : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
            }`}
          >
            Hammasi
          </button>
          {d.kinds.map((k) => (
            <button
              key={k.key}
              onClick={() => setKind(k.key)}
              className={`px-2.5 py-1 rounded-lg text-xs font-medium border transition ${
                kind === k.key
                  ? "bg-slate-100 border-slate-300 text-slate-700"
                  : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
              }`}
            >
              {k.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-3 mb-5">
        <Box
          label={`Yaqin ${d.lead_days} kunda`}
          value={String(d.soon.length)}
          hint="vazifa allaqachon HR'da"
          tone={d.soon.length ? "warn" : "plain"}
        />
        <Box label="Tug'ilgan kunlar" value={String(d.birthdays)} />
        <Box label="Ish yubileylari" value={String(d.anniversaries)} />
      </div>

      {rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Bu davrda sana yo'q.
        </p>
      ) : (
        <div className="space-y-2">
          {rows.map((r) => {
            const key = `${r.user_id}-${r.kind}`;
            return (
              <div
                key={key}
                className={`bg-white rounded-xl border p-4 flex flex-wrap items-center gap-3 ${
                  r.today
                    ? "border-amber-300 bg-amber-50"
                    : r.soon
                      ? "border-amber-200"
                      : "border-slate-200"
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 ${
                    TONE[r.tone] || "bg-slate-100 text-slate-600"
                  }`}
                >
                  {r.kind === "birthday" ? (
                    <Cake size={16} />
                  ) : (
                    <Award size={16} />
                  )}
                </div>

                <div className="min-w-[180px] flex-1">
                  <button
                    onClick={() => setCard(r.user_id)}
                    className="text-sm font-medium text-slate-800 hover:text-brand-700"
                  >
                    {r.full_name}
                  </button>
                  <p className="text-xs text-slate-400">
                    {r.role_label}
                    {r.branch ? ` · ${r.branch}` : ""}
                    {` · ${r.tenure} ishlayapti`}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-sm text-slate-800">{r.date_label}</p>
                  <p
                    className={`text-xs ${
                      r.today
                        ? "text-amber-700 font-medium"
                        : r.soon
                          ? "text-amber-600"
                          : "text-slate-400"
                    }`}
                  >
                    {whenText(r)}
                  </p>
                </div>

                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-medium shrink-0 ${
                    TONE[r.tone] || "bg-slate-100 text-slate-600"
                  }`}
                >
                  {r.kind === "birthday"
                    ? `${r.years} yosh`
                    : `${r.years} yil`}
                </span>

                <button
                  onClick={() => copy(r)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-brand-300 hover:text-brand-700 shrink-0"
                >
                  {copied === key ? (
                    <>
                      <Check size={12} /> Ko'chirildi
                    </>
                  ) : (
                    <>
                      <Copy size={12} /> Tabrik
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {missing.length > 0 && (
        <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
          <div className="flex items-center gap-1.5 mb-1">
            <AlertTriangle size={13} className="text-amber-600" />
            <p className="text-sm font-medium text-amber-800">
              {missing.length} xodimning sanasi kiritilmagan
            </p>
          </div>
          <p className="text-xs text-amber-700">
            {missing.slice(0, 12).join(", ")}
            {missing.length > 12 ? ` va yana ${missing.length - 12} ta` : ""}
          </p>
          <p className="text-xs text-amber-600 mt-1.5">
            Xodimlar bo'limidan tahrirlab tug'ilgan sana va ishga kirgan
            sanani qo'ying — shundan keyin eslatma o'zi ishlaydi.
          </p>
        </div>
      )}

      <p className="text-xs text-slate-500 mt-3 flex items-start gap-1.5">
        <Info size={11} className="mt-0.5 shrink-0" />
        {d.hint}
      </p>

      {card !== null && (
        <StaffCard userId={card} canEdit onClose={() => setCard(null)} />
      )}
    </div>
  );
}

function Box({
  label,
  value,
  hint,
  tone = "plain",
}: {
  label: string;
  value: string;
  hint?: string;
  tone?: "plain" | "warn";
}) {
  const cls = {
    plain: "bg-white border-slate-200 text-slate-900",
    warn: "bg-amber-50 border-amber-200 text-amber-800",
  }[tone];
  return (
    <div className={`rounded-xl border p-4 ${cls}`}>
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className="text-lg font-semibold">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}
