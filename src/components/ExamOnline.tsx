import { useEffect, useState } from "react";
import { Copy, Check, Link2, Lock, Unlock, X } from "lucide-react";
import { api } from "../lib/api";
import { levelLabel } from "../lib/subjects";

/**
 * ONLINE TEST — guruh testining linki (2026-09-18).
 *
 * Jahongir: "guruhga test biriktirganda unit midterm yoki end of course
 * link paydo bo'lsin ... ismi familyasi xato yoki yangi o'quvchilar
 * bo'lsa qizil chiziqdan pastdan alohida ko'rinsin examiner uni
 * to'g'irlasa o'z o'rniga tushib qolsin".
 *
 * ExamSheet ichida ikki joyda chiqadi: jadval ustida link kartasi
 * (OnlineLinkCard), jadval ostida Writing/Speaking va qizil chiziqdan
 * pastdagi natijalar (OnlineBelow). Ma'lumot useExamOnline'dan.
 */

export type OnlineSubmission = {
  id: number;
  student_id: number | null;
  student_name: string | null;
  typed_name: string | null;
  status: "placed" | "pending" | "duplicate" | "replaced" | "rejected";
  online_score: number;
  online_max: number;
  paper_score: number | null;
  submitted_at: string | null;
  placed_by: string | null;
  /** Test paytida sahifadan chiqib ketgani (2026-09-23) */
  away_count: number;
  away_sec: number;
  photo: string | null;
  detail: {
    id: string;
    n: number;
    ok: boolean;
    given: string | null;
    part: string | null;
    q: string;
    type: "choice" | "text" | null;
    given_text: string | null;
    correct: string | null;
    image?: string | null;
    has_image?: boolean;
  }[];
};
type TemplateRow = {
  id: number;
  level: string | null;
  kind: string;
  unit_no: number | null;
  title: string;
  q_count: number;
  paper_max: number;
};
export type OnlineData = {
  online: {
    token: string;
    is_open: boolean;
    template_id: number;
    template_title: string | null;
    online_max: number;
    paper_max: number;
    published_at: string | null;
    published_by: string | null;
    state: "waiting" | "countdown" | "running" | "finished";
    server_now: string;
    starts_at: string | null;
    ends_at: string | null;
    duration_min: number | null;
    in_progress: number;
    /** Hozir yechayotganlar va ularning chiqib ketishlari */
    live: { name: string; away_count: number; away_sec: number }[];
  } | null;
  group_level: string | null;
  can_manage: boolean;
  can_publish: boolean;
  /** Ustoz: examiner tasdiqlaguncha natijalar yashirin */
  hidden: boolean;
  templates: TemplateRow[];
  submissions: OnlineSubmission[];
};

export function useExamOnline(examId: number, enabled: boolean) {
  const [data, setData] = useState<OnlineData | null>(null);
  function reload() {
    if (!enabled) return;
    api.fresh<OnlineData>(`/exams/${examId}/online`).then(setData).catch(() => {});
  }
  useEffect(reload, [examId, enabled]);
  // Link ochiq turganda o'quvchilar topshirib turadi — 15 soniyada
  // bir yangilanadi (examiner sahifani qayta ochmasin)
  const isOpen = !!data?.online?.is_open;
  useEffect(() => {
    if (!enabled || !isOpen) return;
    const t = setInterval(reload, 10000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [examId, enabled, isOpen]);
  return { data, setData, reload };
}

function when(iso: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("uz-UZ", {
    day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
  });
}

export function Photo({ src, size = 32 }: { src: string | null; size?: number }) {
  const [big, setBig] = useState(false);
  if (!src) return null;
  return (
    <>
      <img
        src={src}
        alt=""
        onClick={(e) => {
          e.stopPropagation();
          setBig(true);
        }}
        style={{ width: size, height: size }}
        className="rounded-lg object-cover cursor-zoom-in inline-block"
      />
      {big && (
        <div
          className="fixed inset-0 bg-slate-900/70 z-50 flex items-center justify-center p-4"
          onClick={() => setBig(false)}
        >
          <img src={src} alt="" className="max-h-[80vh] max-w-full rounded-xl" />
        </div>
      )}
    </>
  );
}

/** JAVOB VARAG'I (2026-09-18, Jahongir: "ustiga bossa javoblari ham
 *  ko'rinsin aynan nimada xato qilganini examiner isbotlay olsin").
 *  Har savol: o'quvchi javobi, to'g'ri javob, to'g'ri/xato. */
export function AnswerSheetButton({
  s,
  className,
  children,
}: {
  s: OnlineSubmission;
  className?: string;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const [onlyWrong, setOnlyWrong] = useState(false);
  const wrong = s.detail.filter((d) => !d.ok).length;
  const rows = onlyWrong ? s.detail.filter((d) => !d.ok) : s.detail;
  let lastPart: string | null = null;
  return (
    <>
      <button
        type="button"
        title="Javoblarni ko'rish"
        onClick={(e) => {
          e.stopPropagation();
          setOpen(true);
        }}
        className={className}
      >
        {children}
      </button>
      {open && (
        <div
          className="fixed inset-0 bg-slate-900/40 z-50 overflow-y-auto"
          onClick={() => setOpen(false)}
        >
          <div
            className="bg-white max-w-2xl mx-auto my-6 rounded-xl shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 p-4 border-b border-slate-100 sticky top-0 bg-white rounded-t-xl">
              <Photo src={s.photo} size={44} />
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-slate-900 truncate">
                  {s.student_name || s.typed_name || "—"}
                </p>
                <p className="text-xs text-slate-500">
                  {s.online_score} / {s.online_max} · {wrong} ta xato ·{" "}
                  {when(s.submitted_at)}
                  {s.away_count ? (
                    <>
                      {" · "}
                      <AwayBadge n={s.away_count} sec={s.away_sec} />
                    </>
                  ) : null}
                  {s.typed_name && s.student_name && s.typed_name !== s.student_name
                    ? ` · o'zi yozgan ism: ${s.typed_name}`
                    : ""}
                </p>
              </div>
              <label className="text-xs text-slate-600 flex items-center gap-1.5 whitespace-nowrap">
                <input
                  type="checkbox"
                  checked={onlyWrong}
                  onChange={(e) => setOnlyWrong(e.target.checked)}
                />
                Faqat xatolar
              </label>
              <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            <div className="p-4 space-y-2">
              {rows.map((d) => {
                const head = d.part && d.part !== lastPart ? d.part : null;
                lastPart = d.part;
                return (
                  <div key={d.id}>
                    {head && (
                      <p className="text-xs font-semibold text-slate-500 uppercase mt-3 mb-1">
                        {head}
                      </p>
                    )}
                    <div
                      className={`rounded-lg border px-3 py-2 text-sm ${
                        d.ok ? "border-emerald-200 bg-emerald-50/40" : "border-rose-200 bg-rose-50/50"
                      }`}
                    >
                      <p className="text-slate-800 whitespace-pre-line">
                        <span className={`font-semibold mr-1.5 ${d.ok ? "text-emerald-600" : "text-rose-600"}`}>
                          {d.ok ? "✓" : "✗"} {d.n}.
                        </span>
                        {d.image && (
                          <img src={d.image} alt="" className="inline-block h-10 rounded mr-2 align-middle" />
                        )}
                        {d.q ||
                          (d.has_image ? (
                            !d.image && <span className="text-slate-400">(rasmli savol)</span>
                          ) : (
                            <span className="text-slate-400">(audio / matndagi bo'sh joy)</span>
                          ))}
                      </p>
                      <p className="mt-1 text-xs">
                        <span className="text-slate-500">Javobi: </span>
                        <span className={d.ok ? "text-emerald-700 font-medium" : "text-rose-700 font-medium"}>
                          {d.given_text ?? <i className="text-slate-400 font-normal">javob bermagan</i>}
                        </span>
                        {!d.ok && (
                          <>
                            <span className="text-slate-400 mx-1.5">·</span>
                            <span className="text-slate-500">To'g'risi: </span>
                            <span className="text-emerald-700 font-medium">{d.correct}</span>
                          </>
                        )}
                      </p>
                    </div>
                  </div>
                );
              })}
              {rows.length === 0 && (
                <p className="text-sm text-slate-400 text-center py-6">Xato yo'q</p>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

/** "2 marta chiqdi · 1:20" — test paytida boshqa ilovaga o'tgani. */
export function AwayBadge({ n, sec, className = "" }: { n: number; sec: number; className?: string }) {
  if (!n) return null;
  return (
    <span
      title="Test paytida sahifadan chiqib ketgan (boshqa ilova yoki ekran). Skrinshotning o'zi sezilmaydi."
      className={`text-[11px] font-medium bg-amber-50 text-amber-700 px-1.5 py-0.5 rounded ${className}`}
    >
      ⚠ {n} marta chiqdi{sec ? ` · ${mmss(sec)}` : ""}
    </span>
  );
}

function mmss(sec: number) {
  const s = Math.max(0, Math.ceil(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** VAQTLI TEST (2026-09-18, Jahongir: "examiner vaqt belgilab start
 *  bosganda sekund teskari sanab test ochilsin ... vaqt tugagach
 *  testlar yopilib qolsin"). O'quvchilar link orqali kirib kutadi. */
function TimerControls({
  examId,
  data,
  canManage,
  run,
  busy,
}: {
  examId: number;
  data: NonNullable<OnlineData["online"]>;
  canManage: boolean;
  run: (fn: () => Promise<OnlineData>) => void;
  busy: boolean;
}) {
  const [minutes, setMinutes] = useState(String(data.duration_min || 40));
  const [now, setNow] = useState(Date.now());
  const offset = Date.parse(data.server_now) - Date.now();
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  const serverNow = now + offset;
  const startsIn = data.starts_at ? (Date.parse(data.starts_at) - serverNow) / 1000 : 0;
  const endsIn = data.ends_at ? (Date.parse(data.ends_at) - serverNow) / 1000 : 0;
  let state = data.state;
  if (state === "countdown" && startsIn <= 0) state = "running";
  if (state === "running" && endsIn <= 0) state = "finished";

  if (state === "countdown" || state === "running")
    return (
      <div className="flex flex-wrap items-center gap-3 rounded-lg bg-sky-50 text-sky-900 px-3 py-2 mb-3">
        <span className="text-sm">
          {state === "countdown" ? "Test boshlanmoqda:" : "Test ketyapti — qolgan vaqt:"}
        </span>
        <span className="text-xl font-bold tabular-nums">
          {mmss(state === "countdown" ? startsIn : endsIn)}
        </span>
        {data.in_progress ? (
          <span className="text-xs text-sky-700">yechmoqda: {data.in_progress}</span>
        ) : null}
        {data.live?.some((x) => x.away_count) ? (
          <span className="w-full text-xs text-amber-700">
            Sahifadan chiqqanlar:{" "}
            {data.live
              .filter((x) => x.away_count)
              .map((x) => `${x.name} (${x.away_count})`)
              .join(", ")}
          </span>
        ) : null}
        {canManage && (
          <button
            disabled={busy}
            onClick={() => {
              if (confirm("Test hozir hamma uchun tugatilsinmi? Javoblar avtomatik topshiriladi."))
                run(() => api.post<OnlineData>(`/exams/${examId}/online/stop`, {}));
            }}
            className="ml-auto border border-sky-300 rounded-lg px-3 py-1.5 text-sm hover:bg-sky-100"
          >
            Tugatish
          </button>
        )}
      </div>
    );

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 mb-3">
      <span className="text-sm text-slate-700">
        {state === "finished"
          ? "Test vaqti tugadi."
          : `Kutmoqda: ${data.in_progress} o'quvchi — savollar Start bosilgach ochiladi.`}
      </span>
      {canManage && (
        <span className="ml-auto flex items-center gap-2">
          <input
            type="number"
            min={1}
            max={300}
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            className="w-20 rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
            title="Test vaqti, daqiqa"
          />
          <span className="text-xs text-slate-500">daqiqa</span>
          <button
            disabled={busy || !Number(minutes)}
            onClick={() => {
              if (
                state === "finished" &&
                !confirm("Test qayta ochilsinmi? Hali topshirmaganlar yana kira oladi.")
              )
                return;
              run(() =>
                api.post<OnlineData>(`/exams/${examId}/online/start`, {
                  minutes: Number(minutes),
                })
              );
            }}
            className="bg-sky-600 hover:bg-sky-700 text-white rounded-lg px-4 py-1.5 text-sm font-medium disabled:opacity-60"
          >
            {state === "finished" ? "Qayta start" : "Start"}
          </button>
        </span>
      )}
    </div>
  );
}

/** Link kartasi: yaratish, nusxa olish, ochish/yopish. */
export function OnlineLinkCard({
  examId,
  kind,
  data,
  setData,
  onChanged,
}: {
  examId: number;
  kind: string;
  data: OnlineData | null;
  setData: (d: OnlineData) => void;
  onChanged: () => void;
}) {
  const [tplId, setTplId] = useState<number | "">("");
  const [paper, setPaper] = useState("");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (data && !data.online && data.templates.length && tplId === "") {
      const t = data.templates[0];
      setTplId(t.id);
      setPaper(String(t.paper_max || 0));
    }
  }, [data, tplId]);

  if (kind === "mock" || !data) return null;
  const o = data.online;
  const url = o ? `${window.location.origin}/t/${o.token}` : "";

  async function run(fn: () => Promise<OnlineData>) {
    setBusy(true);
    setError(null);
    try {
      setData(await fn());
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  if (!o) {
    if (!data.can_manage) return null;
    return (
      <div className="border border-dashed border-slate-300 rounded-xl p-4 mb-4 bg-white">
        <p className="text-sm font-medium text-slate-800 flex items-center gap-2 mb-2">
          <Link2 size={15} className="text-brand-600" /> Online test linki
        </p>
        {data.templates.length === 0 ? (
          <p className="text-xs text-slate-500">
            Test bazasida bu tur/unit uchun test yo'q. Examinerlar boshlig'i
            Audit → Test bazasi bo'limida qo'shadi.
          </p>
        ) : (
          <div className="flex flex-wrap items-end gap-2">
            <label className="text-xs text-slate-500">
              Test
              <select
                className="block mt-1 rounded-lg border border-slate-300 px-2 py-1.5 text-sm bg-white max-w-[280px]"
                value={tplId}
                onChange={(e) => {
                  const t = data.templates.find((x) => x.id === Number(e.target.value));
                  setTplId(Number(e.target.value));
                  if (t) setPaper(String(t.paper_max || 0));
                }}
              >
                {data.templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.title} ({t.q_count} savol
                    {t.level ? `, ${levelLabel(t.level)}` : ""}
                    {t.level && data.group_level && t.level !== data.group_level
                      ? " — boshqa daraja"
                      : ""}
                    )
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs text-slate-500">
              Writing + Speaking (qog'oz), max
              <input
                type="number"
                min={0}
                className="block mt-1 w-28 rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
                value={paper}
                onChange={(e) => setPaper(e.target.value)}
              />
            </label>
            <button
              disabled={busy || tplId === ""}
              onClick={() =>
                run(() =>
                  api.post<OnlineData>(`/exams/${examId}/online`, {
                    template_id: tplId,
                    paper_max: Number(paper || 0),
                  })
                )
              }
              className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60"
            >
              Link yaratish
            </button>
          </div>
        )}
        {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
      </div>
    );
  }

  const placed = data.submissions.filter((s) => s.status === "placed").length;
  const waiting = data.submissions.filter(
    (s) => s.status === "pending" || s.status === "duplicate"
  ).length;
  return (
    <div className="border border-slate-200 rounded-xl p-4 mb-4 bg-white">
      {o.is_open && (
        <TimerControls
          examId={examId}
          data={o}
          canManage={data.can_manage}
          run={run}
          busy={busy}
        />
      )}
      {/* TASDIQLASH (2026-09-18): examiner tasdiqlaguncha natija guruh
          testiga yozilmaydi — ustoz, o'quvchi va ota-ona ko'rmaydi */}
      <div
        className={`flex flex-wrap items-center gap-2 rounded-lg px-3 py-2 mb-3 text-sm ${
          o.published_at
            ? "bg-emerald-50 text-emerald-800"
            : "bg-amber-50 text-amber-800"
        }`}
      >
        {o.published_at ? (
          <span>
            Natijalar tasdiqlangan — {when(o.published_at)}
            {o.published_by ? `, ${o.published_by}` : ""}. O'quvchi va ustozlarga
            ko'rinadi.
          </span>
        ) : data.hidden ? (
          <span>Natijalar examiner tasdiqlagandan keyin ko'rinadi.</span>
        ) : (
          <>
            <span className="flex-1 min-w-[200px]">
              Natijalar hali tasdiqlanmagan — o'quvchi va ustozlarga
              ko'rinmaydi. Topshirgan: {placed}
              {waiting ? `, aniqlanmagan: ${waiting}` : ""}.
            </span>
            {data.can_publish && (
              <button
                disabled={busy}
                onClick={() => {
                  if (
                    confirm(
                      `${placed} ta natija tasdiqlansinmi? Shundan keyin o'quvchi, ustoz va ota-onaga ko'rinadi, coin beriladi.` +
                        (waiting ? `\n\nDiqqat: ${waiting} ta aniqlanmagan natija hali biriktirilmagan.` : "")
                    )
                  )
                    run(() => api.post<OnlineData>(`/exams/${examId}/online/publish`, {}));
                }}
                className="bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-60"
              >
                Natijalarni tasdiqlash
              </button>
            )}
          </>
        )}
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Link2 size={15} className="text-brand-600" />
        <span className="text-sm font-medium text-slate-800">
          Online test: {o.template_title}
        </span>
        <span
          className={`text-[11px] font-medium px-2 py-0.5 rounded ${
            o.is_open ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"
          }`}
        >
          {o.is_open ? "ochiq" : "yopiq"}
        </span>
        <span className="text-xs text-slate-500">
          {o.online_max} savol
          {o.paper_max > 0 ? ` + qog'oz ${o.paper_max} ball` : ""} · topshirgan: {placed}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-2 mt-3">
        <input
          readOnly
          value={url}
          onFocus={(e) => e.target.select()}
          className="flex-1 min-w-[200px] rounded-lg border border-slate-300 px-3 py-2 text-sm bg-slate-50 text-slate-700"
        />
        <button
          onClick={() => {
            navigator.clipboard?.writeText(url).then(() => {
              setCopied(true);
              setTimeout(() => setCopied(false), 1500);
            });
          }}
          className="inline-flex items-center gap-1.5 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
        >
          {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
          {copied ? "Nusxalandi" : "Nusxa olish"}
        </button>
        {data.can_manage && (
          <button
            disabled={busy}
            onClick={() =>
              run(() => api.put<OnlineData>(`/exams/${examId}/online`, { is_open: !o.is_open }))
            }
            className="inline-flex items-center gap-1.5 border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
          >
            {o.is_open ? <Lock size={14} /> : <Unlock size={14} />}
            {o.is_open ? "Yopish" : "Ochish"}
          </button>
        )}
        {data.can_manage && data.submissions.length === 0 && (
          <button
            disabled={busy}
            title="Linkni o'chirish"
            onClick={() => {
              if (confirm("Link o'chirilsinmi?"))
                run(() => api.delete<OnlineData>(`/exams/${examId}/online`));
            }}
            className="text-slate-300 hover:text-red-500 px-1"
          >
            <X size={16} />
          </button>
        )}
      </div>
      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
    </div>
  );
}

/** Jadval ostida: Writing/Speaking kiritish va qizil chiziqdan
 *  pastdagi (aniqlanmagan) natijalar. */
export function OnlineBelow({
  examId,
  data,
  setData,
  students,
  onChanged,
}: {
  examId: number;
  data: OnlineData | null;
  setData: (d: OnlineData) => void;
  students: { id: number; full_name: string }[];
  onChanged: () => void;
}) {
  const [paper, setPaper] = useState<Record<number, string>>({});
  const [pick, setPick] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!data) return;
    const next: Record<number, string> = {};
    for (const s of data.submissions)
      if (s.status === "placed" && s.student_id)
        next[s.student_id] = s.paper_score != null ? String(s.paper_score) : "";
    setPaper(next);
  }, [data]);

  if (!data || !data.online) return null;
  const o = data.online;
  const placed = data.submissions.filter((s) => s.status === "placed");
  const below = data.submissions.filter(
    (s) => s.status === "pending" || s.status === "duplicate"
  );

  async function run(fn: () => Promise<OnlineData>) {
    setBusy(true);
    setError(null);
    try {
      setData(await fn());
      onChanged();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }


  return (
    <div className="mt-4 space-y-4">
      {error && <p className="text-sm text-red-600">{error}</p>}

      {o.paper_max > 0 && placed.length > 0 && (
        <div className="border border-slate-200 rounded-xl bg-white overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-slate-50">
            <p className="text-sm font-medium text-slate-700">
              Writing + Speaking (qog'oz, max {o.paper_max})
            </p>
            {data.can_manage && (
              <button
                disabled={busy}
                onClick={() =>
                  run(() =>
                    api.put<OnlineData>(`/exams/${examId}/paper`, {
                      marks: placed.map((s) => ({
                        student_id: s.student_id,
                        paper:
                          (paper[s.student_id!] ?? "").trim() === ""
                            ? null
                            : Number(paper[s.student_id!]),
                      })),
                    })
                  )
                }
                className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-60"
              >
                Saqlash
              </button>
            )}
          </div>
          <table className="w-full text-sm">
            <tbody>
              {placed.map((s) => {
                const p = paper[s.student_id!] ?? "";
                const total = p.trim() === "" ? null : s.online_score + Number(p);
                return (
                  <tr key={s.id} className="border-t border-slate-100">
                    <td className="px-4 py-2 text-slate-800">
                      <span className="inline-flex items-center gap-2">
                        <Photo src={s.photo} size={28} />
                        {s.student_name}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-500 whitespace-nowrap">
                      <AnswerSheetButton s={s} className="underline decoration-dotted hover:text-brand-700">
                        online {s.online_score}/{s.online_max}
                      </AnswerSheetButton>
                    </td>
                    <td className="px-4 py-2">
                      <input
                        type="number"
                        min={0}
                        max={o.paper_max}
                        disabled={!data.can_manage}
                        className="w-20 rounded-lg border border-slate-300 px-2 py-1 text-sm"
                        value={p}
                        placeholder="—"
                        onChange={(e) =>
                          setPaper({ ...paper, [s.student_id!]: e.target.value })
                        }
                      />
                    </td>
                    <td className="px-4 py-2 text-right font-medium text-slate-800 whitespace-nowrap">
                      {total != null ? (
                        `${total} / ${o.online_max + o.paper_max}`
                      ) : (
                        <span className="text-amber-600 text-xs font-normal">
                          qog'oz kutilmoqda
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {below.length > 0 && (
        <div>
          <div className="border-t-2 border-red-500 mb-2" />
          <p className="text-sm font-semibold text-red-600 mb-2">
            Aniqlanmagan natijalar ({below.length}) — o'quvchiga biriktiring
          </p>
          <div className="space-y-2">
            {below.map((s) => (
              <div
                key={s.id}
                className="border border-red-200 bg-red-50/40 rounded-xl px-3 py-2.5"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <Photo src={s.photo} size={44} />
                  <div className="min-w-[140px]">
                    <p className="text-sm font-medium text-slate-800">
                      {s.typed_name || s.student_name || "—"}
                    </p>
                    <AwayBadge n={s.away_count} sec={s.away_sec} className="mb-0.5 inline-block" />
                    <p className="text-xs text-slate-500">
                      {s.status === "duplicate"
                        ? `${s.student_name} qayta topshirgan`
                        : "Ro'yxatda yo'q / ism boshqacha"}
                      {" · "}
                      {when(s.submitted_at)}
                    </p>
                  </div>
                  <AnswerSheetButton
                    s={s}
                    className="text-sm font-semibold text-slate-800 underline decoration-dotted"
                  >
                    {s.online_score}/{s.online_max}
                  </AnswerSheetButton>
                  {data.can_manage && (
                    <div className="flex flex-wrap items-center gap-2 ml-auto">
                      <select
                        className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm bg-white max-w-[200px]"
                        value={pick[s.id] ?? (s.student_id ? String(s.student_id) : "")}
                        onChange={(e) => setPick({ ...pick, [s.id]: e.target.value })}
                      >
                        <option value="">O'quvchini tanlang</option>
                        {students.map((st) => (
                          <option key={st.id} value={st.id}>
                            {st.full_name}
                          </option>
                        ))}
                      </select>
                      <button
                        disabled={busy || !(pick[s.id] ?? s.student_id)}
                        onClick={() => {
                          const sid = Number(pick[s.id] ?? s.student_id);
                          const has = placed.find((x) => x.student_id === sid);
                          if (
                            has &&
                            !confirm(
                              `${has.student_name}ning avvalgi natijasi (${has.online_score}/${has.online_max}) shu natija bilan almashtirilsinmi?`
                            )
                          )
                            return;
                          run(() =>
                            api.post<OnlineData>(`/exam-submissions/${s.id}/assign`, {
                              student_id: sid,
                            })
                          );
                        }}
                        className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-3 py-1.5 text-sm font-medium disabled:opacity-50"
                      >
                        Biriktirish
                      </button>
                      <button
                        disabled={busy}
                        onClick={() => {
                          if (confirm("Bu natija rad etilsinmi?"))
                            run(() =>
                              api.post<OnlineData>(`/exam-submissions/${s.id}/reject`, {})
                            );
                        }}
                        className="text-xs text-slate-400 hover:text-red-600"
                      >
                        Rad etish
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
