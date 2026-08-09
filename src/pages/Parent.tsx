import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Download, GraduationCap, Snowflake, X } from "lucide-react";

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
  const [installEvt, setInstallEvt] = useState<Any>(null);
  const [installHidden, setInstallHidden] = useState(false);

  useEffect(() => {
    fetch(`/api/parent/${token}`)
      .then(async (r) => {
        if (!r.ok) throw new Error("Havola eskirgan yoki noto'g'ri");
        setD(await r.json());
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [token]);

  // PWA: shu FARZANDGA xos manifest ulanadi (uy ekraniga qo'shilsa,
  // to'g'ridan-to'g'ri shu sahifaga ochiladi) va servis worker faqat
  // /parent/ doirasida ro'yxatdan o'tadi — xodimlar paneliga tegmaydi.
  useEffect(() => {
    if (!token) return;
    let link = document.querySelector<HTMLLinkElement>(
      'link[rel="manifest"]'
    );
    if (!link) {
      link = document.createElement("link");
      link.rel = "manifest";
      document.head.appendChild(link);
    }
    link.href = `/api/parent/${token}/manifest.webmanifest`;

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js", { scope: "/parent/" })
        .catch(() => {});
    }

    return () => {
      link?.parentNode?.removeChild(link);
    };
  }, [token]);

  // Android/Chrome "uy ekraniga qo'shish mumkin" deb topsa shu
  // hodisani otadi — brauzerning o'zi ko'rsatadigan (ko'zga unча
  // tashlanmaydigan) taklif o'rniga aniq tugma ko'rsatamiz.
  useEffect(() => {
    function onPrompt(e: Any) {
      e.preventDefault();
      setInstallEvt(e);
    }
    window.addEventListener("beforeinstallprompt", onPrompt);
    return () => window.removeEventListener("beforeinstallprompt", onPrompt);
  }, []);

  async function installApp() {
    if (!installEvt) return;
    installEvt.prompt();
    await installEvt.userChoice;
    setInstallEvt(null);
  }

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
        {installEvt && !installHidden && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-3.5 flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-brand-50 flex items-center justify-center shrink-0">
              <Download size={16} className="text-brand-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-800">
                Ilovani telefoningizga o'rnating
              </p>
              <p className="text-xs text-slate-500">
                Uy ekranidan bir bosishda oching
              </p>
            </div>
            <button
              onClick={installApp}
              className="text-xs font-medium px-3 py-1.5 rounded-lg bg-brand-600 text-white shrink-0"
            >
              O'rnatish
            </button>
            <button
              onClick={() => setInstallHidden(true)}
              className="text-slate-400 shrink-0"
              aria-label="Yopish"
            >
              <X size={16} />
            </button>
          </div>
        )}

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

        {d.payments && d.payments.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-3">
              To'lovlar tarixi
            </p>
            <div className="space-y-3">
              {d.payments.map((p: Any, i: number) => (
                <div key={i} className="flex items-start justify-between gap-3 text-sm">
                  <div className="min-w-0">
                    <p className="text-slate-700">
                      {p.kind}
                      {p.method ? ` · ${p.method}` : ""}
                    </p>
                    <p className="text-[11px] text-slate-400 truncate">
                      {(p.date || "").slice(0, 10)}
                      {p.note ? ` · ${p.note}` : ""}
                    </p>
                  </div>
                  <span
                    className={`font-medium shrink-0 ${
                      p.amount < 0 ? "text-red-600" : "text-emerald-600"
                    }`}
                  >
                    {p.amount > 0 ? "+" : ""}
                    {fmt(p.amount)} so'm
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {d.gamification && (
          <div
            className="rounded-xl p-5 text-white relative overflow-hidden"
            style={{
              background: d.gamification.league?.color
                ? `linear-gradient(135deg, ${d.gamification.league.color} 0%, #0f172a 130%)`
                : "linear-gradient(135deg,#334155,#0f172a)",
            }}
          >
            <div className="flex items-start gap-3">
              <div className="text-4xl leading-none">
                {d.gamification.league?.icon || "🌱"}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs opacity-80">
                  {d.gamification.league?.name || "Newcomer"}
                </p>
                <p className="text-2xl font-semibold leading-tight">
                  {fmt(d.gamification.lifetime_xp)}
                  <span className="text-sm font-normal opacity-80"> XP</span>
                </p>
                <p className="text-sm opacity-90 mt-0.5">
                  {d.gamification.level}-daraja · {d.gamification.coins} coin
                </p>
              </div>
            </div>
            {!d.gamification.max_league && (
              <div className="mt-4">
                <div className="flex justify-between text-[11px] opacity-80 mb-1">
                  <span>Keyingi liga: {d.gamification.next_league?.name}</span>
                  <span>{fmt(d.gamification.league_to_next)} XP qoldi</span>
                </div>
                <div className="h-2 rounded-full bg-white/20 overflow-hidden">
                  <div
                    className="h-2 rounded-full bg-white"
                    style={{ width: `${d.gamification.league_percent}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

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

        {((d.daily_grades && d.daily_grades.length > 0) ||
          (d.exam_results && d.exam_results.length > 0)) && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-3">
              O'zlashtirish va test natijalari
            </p>

            {d.exam_results && d.exam_results.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-slate-500 mb-2">Test natijalari</p>
                <div className="space-y-2">
                  {d.exam_results.map((e: Any, i: number) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <div className="min-w-0">
                        <p className="text-slate-700">{e.title}</p>
                        <p className="text-[11px] text-slate-400">
                          {(e.date || "").slice(0, 10)}
                        </p>
                      </div>
                      {e.absent ? (
                        <span className="text-[11px] rounded-full px-2 py-0.5 font-medium bg-red-100 text-red-600 shrink-0">
                          Kelmadi
                        </span>
                      ) : (
                        <span className="text-sm font-medium text-slate-800 shrink-0">
                          {e.band != null
                            ? `Band ${e.band}`
                            : e.max_score
                            ? `${e.score}/${e.max_score}`
                            : e.score}
                          {e.percent != null && (
                            <span className="text-[11px] text-slate-400 font-normal">
                              {" "}
                              ({e.percent}%)
                            </span>
                          )}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {d.daily_grades && d.daily_grades.length > 0 && (
              <div>
                <p className="text-xs text-slate-500 mb-2">
                  Kundalik baholar (har bir dars)
                </p>
                <div className="flex flex-wrap gap-2">
                  {d.daily_grades.map((g: Any, i: number) => (
                    <div
                      key={i}
                      title={(g.date || "").slice(0, 10)}
                      className={`text-xs font-medium rounded-lg px-2 py-1 ${
                        g.score >= 4
                          ? "bg-emerald-100 text-emerald-700"
                          : g.score === 3
                          ? "bg-amber-100 text-amber-700"
                          : "bg-red-100 text-red-600"
                      }`}
                    >
                      {(g.date || "").slice(5, 10)} · {g.score}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <p className="text-[11px] text-slate-400 text-center px-6">
          Bu sahifa faqat sizga berilgan maxsus havola orqali ochiladi.
          Havolani begonalarga bermang.
        </p>
      </div>
    </div>
  );
}
