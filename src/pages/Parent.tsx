import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { GraduationCap, Snowflake } from "lucide-react";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * OTA-ONA SAHIFASI — loginsiz, faqat maxsus havola bilan ochiladi.
 * Administrator o'quvchi kartasidan havolani oladi va ota-onaga
 * yuboradi. Ota-ona: davomat, uy vazifasi, balans va guruhni ko'radi.
 * Mobilga moslangan — odatda telefonda ochiladi.
 */
const fmt = (n: Any) => Number(n || 0).toLocaleString().replace(/,/g, " ");

export default function Parent() {
  const { token } = useParams();
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    fetch(`/api/parent/${token}`)
      .then(async (r) => {
        if (!r.ok) throw new Error("Havola eskirgan yoki noto'g'ri");
        setD(await r.json());
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [token]);

  if (err)
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <p className="text-sm text-slate-500">{err}</p>
      </div>
    );
  if (!d)
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-400">Yuklanmoqda…</p>
      </div>
    );

  const AT: Record<string, { t: string; cls: string }> = {
    "1": { t: "keldi", cls: "bg-emerald-100 text-emerald-700" },
    "2": { t: "kech keldi", cls: "bg-amber-100 text-amber-700" },
    "0": { t: "kelmadi", cls: "bg-red-100 text-red-600" },
  };
  const HW: Record<string, string> = {
    "2": "vazifa: bajardi ✓", "1": "vazifa: qisman ±",
    "0": "vazifa: qilmadi ✗",
  };

  return (
    <div className="min-h-screen bg-slate-50 pb-10">
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-10">
        <div className="max-w-md mx-auto">
          <div className="flex items-center gap-2 mb-4 opacity-90">
            <GraduationCap size={18} />
            <span className="text-sm font-medium">Jony Academy</span>
          </div>
          <h1 className="text-xl font-semibold">{d.name}</h1>
          <p className="text-sm opacity-90 mt-0.5">
            {d.group || "guruh biriktirilmagan"}
            {d.lesson_time ? ` · ${d.lesson_time}` : ""} · {d.status}
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-xs text-slate-500">Balans</p>
          <p className={`text-2xl font-semibold ${
            d.balance < 0 ? "text-red-600" : "text-emerald-600"}`}>
            {fmt(d.balance)} so'm
          </p>
          {d.balance < 0 && (
            <p className="text-xs text-slate-500 mt-1">
              To'lov qilishingizni so'raymiz. Savol bo'lsa
              administratorga murojaat qiling.
            </p>
          )}
        </div>

        {d.status === "muzlatilgan" && d.frozen_until && (
          <div className="bg-sky-50 border border-sky-200 rounded-xl p-4 flex items-start gap-2.5">
            <Snowflake size={16} className="text-sky-500 mt-0.5" />
            <p className="text-sm text-sky-800">
              O'qish vaqtincha muzlatilgan. Qaytish sanasi:{" "}
              <b>{d.frozen_until}</b>
            </p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-800 mb-3">
            So'nggi darslar
          </p>
          {d.practice && d.practice.done > 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
              <p className="text-xs text-slate-500 mb-1">
                Mashqlar bo'yicha daraja
              </p>
              <p className="text-lg font-semibold text-slate-900">
                {d.practice.level.label}
                <span className="ml-2 text-xs font-normal text-slate-400">
                  IELTS {d.practice.level.ielts} · CEFR {d.practice.level.cefr}
                </span>
              </p>
              <p className="text-xs text-slate-500 mt-0.5">
                {d.practice.done} ta mashq · to'g'ri javoblar{" "}
                {d.practice.percent}%
              </p>
              {d.practice.next && (
                <div className="mt-2">
                  <div className="flex justify-between text-[11px] text-slate-500 mb-0.5">
                    <span>Keyingi: {d.practice.next.label}</span>
                    <span>{d.practice.next.points_left} ball qoldi</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className="h-2 rounded-full bg-emerald-500"
                      style={{ width: `${d.practice.next.progress_percent}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {d.attendance.length === 0 && (
            <p className="text-sm text-slate-400">
              Hozircha dars yozuvi yo'q.
            </p>
          )}
          <div className="space-y-2">
            {d.attendance.map((a: Any, i: number) => {
              const ui = AT[String(a.present)] || AT["0"];
              return (
                <div key={i}
                  className="flex items-center justify-between text-sm">
                  <span className="text-slate-600">{a.date}</span>
                  <span className="flex items-center gap-2">
                    {a.homework !== null && a.homework !== undefined && (
                      <span className="text-[11px] text-slate-400">
                        {HW[String(a.homework)]}
                      </span>
                    )}
                    <span className={`text-[11px] rounded-full px-2 py-0.5 font-medium ${ui.cls}`}>
                      {ui.t}
                    </span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <p className="text-[11px] text-slate-400 text-center px-6">
          Bu sahifa faqat sizga berilgan maxsus havola orqali ochiladi.
          Havolani begonalarga bermang.
        </p>
      </div>
    </div>
  );
}
