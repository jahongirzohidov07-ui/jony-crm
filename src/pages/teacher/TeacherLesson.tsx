import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Check, Info, Lock, Star } from "lucide-react";
import { api } from "../../lib/api";
import { pushToast } from "../../lib/toast";
import {
  HOMEWORK_OPTS, PRESENT_OPTS,
  type LessonDetail, type LessonStudent,
} from "../../lib/teacherApi";

/**
 * JONY TEACHER — YO'QLAMA EKRANI (2026-08-10).
 *
 * Ustozning kunlik asosiy ishi. Dizayn qoidasi: bitta o'quvchi = bitta
 * qator, uchta katta tugma (Keldi / Kech / Yo'q) — barmoq bilan
 * aniq bosiladigan o'lchamda. Uy vazifasi va baho ixtiyoriy, ochib
 * qo'yiladi.
 *
 * SAQLASH: mavjud PUT /api/lessons/{id}/attendance va
 * PUT /api/lessons/{id}/grades ishlatiladi — YANGI yo'l yozilmadi.
 * Sababi: o'sha yo'llarda sana qoidalari, muzlatilgan o'quvchi
 * himoyasi, avtomat XP, ota-onaga Telegram xabari va ustoz oyligi
 * hisobi bor. Ikkinchi nusxa yozilsa, shulardan biri esdan chiqib
 * ketishi mumkin edi.
 *
 * "Hammasi keldi" tugmasi ataylab bor: 15 kishilik guruhda odatda
 * 1-2 kishi kelmaydi — ustoz bir bosib hammasini belgilaydi, keyin
 * kelmaganini o'zgartiradi. Bu darsdagi vaqtni tejaydi.
 */
export default function TeacherLesson() {
  const { id } = useParams();
  const [d, setD] = useState<LessonDetail | null>(null);
  const [err, setErr] = useState("");
  const [rows, setRows] = useState<LessonStudent[]>([]);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [openExtra, setOpenExtra] = useState<number | null>(null);

  const load = useCallback(() => {
    api
      .get<LessonDetail>(`/teacher/lesson/${id}`)
      .then((r) => {
        setD(r);
        setRows(r.students);
        setDirty(false);
      })
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [id]);

  useEffect(load, [load]);

  function setField(sid: number, patch: Partial<LessonStudent>) {
    if (!d?.editable) return;
    setRows((rs) =>
      rs.map((r) => {
        if (r.id !== sid) return r;
        const next = { ...r, ...patch };
        // KELMAGAN O'QUVCHIGA BAHO YO'Q (2026-08-10, Jahongir).
        // "Yo'q" bosilishi bilan bahosi va uy vazifasi tozalanadi —
        // server ham buni rad etadi, lekin ekranda ham darhol
        // ko'rinib tursin (ustoz keyin "nega saqlanmadi" deb
        // o'ylamasin).
        if (patch.present === 0) {
          next.grade = null;
          next.homework = null;
        }
        return next;
      }),
    );
    setDirty(true);
  }

  function markAll(v: number) {
    if (!d?.editable) return;
    setRows((rs) => rs.map((r) => ({ ...r, present: v })));
    setDirty(true);
  }

  async function save() {
    if (!d || saving) return;
    setSaving(true);
    try {
      // 1) Yo'qlama — belgilanmaganlar (null) umuman yuborilmaydi,
      //    ular "belgilanmagan" bo'lib qolaveradi.
      const marks = rows
        .filter((r) => r.present !== null)
        .map((r) => ({
          student_id: r.id,
          present: r.present !== 0,
          late: r.present === 2,
          homework: r.homework ?? undefined,
        }));
      if (marks.length > 0) {
        await api.put(`/lessons/${d.lesson_id}/attendance`, { marks });
      }

      // 2) Baholar — faqat qo'yilganlari
      const grades = rows
        .filter((r) => r.grade !== null && r.grade !== undefined)
        .map((r) => ({ student_id: r.id, score: r.grade }));
      if (grades.length > 0) {
        await api.put(`/lessons/${d.lesson_id}/grades`, { marks: grades });
      }

      pushToast("Saqlandi", "success", 2500);
      load();
    } catch {
      // xato toast'da ko'rinadi (api.ts)
    } finally {
      setSaving(false);
    }
  }

  if (err)
    return (
      <Shell title="Yo'qlama">
        <p className="text-sm text-slate-500 text-center py-16 px-6">{err}</p>
      </Shell>
    );
  if (!d)
    return (
      <Shell title="Yo'qlama">
        <p className="text-sm text-slate-400 text-center py-16">Yuklanmoqda…</p>
      </Shell>
    );

  const marked = rows.filter((r) => r.present !== null).length;

  return (
    <Shell title={d.group} subtitle={`${d.date.slice(8, 10)}.${d.date.slice(5, 7)}${d.time ? ` · ${d.time}` : ""}`}>
      {!d.editable && d.readonly_reason && (
        <div className="bg-slate-100 border border-slate-200 rounded-xl p-3.5 flex items-start gap-2.5 mb-4">
          <Lock size={16} className="text-slate-500 mt-0.5 shrink-0" />
          <p className="text-xs text-slate-600">{d.readonly_reason}</p>
        </div>
      )}

      {d.editable && (
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={() => markAll(1)}
            className="flex-1 py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-medium active:bg-emerald-700"
          >
            Hammasi keldi
          </button>
          <span className="text-xs text-slate-400 shrink-0 px-1">
            {marked}/{rows.length}
          </span>
        </div>
      )}

      <div className="space-y-2">
        {rows.length === 0 && (
          <p className="text-sm text-slate-400 text-center py-10">
            Bu guruhda faol o'quvchi yo'q.
          </p>
        )}
        {rows.map((s, i) => (
          <div
            key={s.id}
            className="bg-white rounded-xl shadow-sm border border-slate-200 p-3"
          >
            <div className="flex items-center gap-2.5">
              <span className="w-5 text-xs text-slate-300 shrink-0 text-right">
                {i + 1}
              </span>
              <p className="flex-1 text-sm font-medium text-slate-800 truncate">
                {s.full_name}
                {s.status === "trial" && (
                  <span className="ml-1.5 text-[10px] font-normal text-amber-600">
                    sinov
                  </span>
                )}
              </p>
            </div>

            <div className="flex gap-1.5 mt-2.5">
              {PRESENT_OPTS.map((o) => (
                <button
                  key={o.v}
                  disabled={!d.editable}
                  onClick={() =>
                    setField(s.id, { present: s.present === o.v ? null : o.v })
                  }
                  className={`flex-1 py-2.5 rounded-lg text-xs font-semibold border transition disabled:opacity-50 ${
                    s.present === o.v
                      ? o.cls + " border-transparent"
                      : "bg-white text-slate-500 border-slate-200"
                  }`}
                >
                  {o.label}
                </button>
              ))}
              <button
                disabled={s.present === 0}
                onClick={() =>
                  setOpenExtra(openExtra === s.id ? null : s.id)
                }
                className={`w-11 rounded-lg border text-xs transition disabled:opacity-30 ${
                  s.homework !== null || s.grade !== null
                    ? "border-brand-300 bg-brand-50 text-brand-600"
                    : "border-slate-200 text-slate-400"
                }`}
                aria-label="Uy vazifasi va baho"
                title={
                  s.present === 0
                    ? "Kelmagan o'quvchiga baho qo'yilmaydi"
                    : "Uy vazifasi va baho"
                }
              >
                {s.grade !== null ? (
                  <span className="font-bold">{s.grade}</span>
                ) : (
                  <Star size={15} className="mx-auto" />
                )}
              </button>
            </div>

            {openExtra === s.id && s.present !== 0 && (
              <div className="mt-3 pt-3 border-t border-slate-100 space-y-3">
                <div>
                  <p className="text-[11px] text-slate-500 mb-1.5">
                    Uy vazifasi
                  </p>
                  <div className="flex gap-1.5">
                    {HOMEWORK_OPTS.map((o) => (
                      <button
                        key={o.v}
                        disabled={!d.editable}
                        onClick={() =>
                          setField(s.id, {
                            homework: s.homework === o.v ? null : o.v,
                          })
                        }
                        className={`flex-1 py-2 rounded-lg text-xs font-medium border transition disabled:opacity-50 ${
                          s.homework === o.v
                            ? "bg-slate-900 text-white border-transparent"
                            : "bg-white text-slate-500 border-slate-200"
                        }`}
                      >
                        {o.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[11px] text-slate-500 mb-1.5">
                    Dars bahosi (coin beriladi)
                  </p>
                  <div className="flex gap-1.5">
                    {[1, 2, 3, 4, 5].map((n) => (
                      <button
                        key={n}
                        disabled={!d.editable}
                        onClick={() =>
                          setField(s.id, { grade: s.grade === n ? null : n })
                        }
                        className={`flex-1 py-2 rounded-lg text-sm font-bold border transition disabled:opacity-50 ${
                          s.grade === n
                            ? n >= 4
                              ? "bg-emerald-600 text-white border-transparent"
                              : n === 3
                                ? "bg-amber-500 text-white border-transparent"
                                : "bg-red-600 text-white border-transparent"
                            : "bg-white text-slate-500 border-slate-200"
                        }`}
                      >
                        {n}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {rows.length > 0 && (
        <p className="text-[11px] text-slate-400 flex items-start gap-1.5 mt-4 px-1">
          <Info size={11} className="mt-0.5 shrink-0" />
          Belgilanmagan o'quvchi oylik hisobiga kirmaydi. Kech kelgan
          ham "kelgan" hisoblanadi. Kelmagan o'quvchiga baho va coin
          qo'yilmaydi.
        </p>
      )}

      {/* Saqlash paneli pastdagi TAB PANELI USTIDA turadi (2026-08-10,
          Jahongir: "saqlash tugmasi juda pastda"). Ilgari ikkalasi ham
          bottom-0 edi va tab paneli (z-40) tugmani berkitib qo'yardi. */}
      {d.editable && rows.length > 0 && (
        <div className="fixed bottom-[60px] inset-x-0 px-4 pt-6 pb-3 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent z-30">
          <div className="max-w-md mx-auto">
            <button
              onClick={save}
              disabled={saving || !dirty}
              className="w-full py-3.5 rounded-xl bg-brand-600 text-white text-sm font-semibold shadow-lg flex items-center justify-center gap-2 disabled:opacity-40"
            >
              <Check size={17} />
              {saving ? "Saqlanmoqda…" : dirty ? "Saqlash" : "Saqlangan"}
            </button>
          </div>
        </div>
      )}
    </Shell>
  );
}

function Shell({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-6 pb-8">
        <div className="max-w-md mx-auto">
          <Link
            to="/teacher"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Bugun
          </Link>
          <h1 className="text-lg font-semibold">{title}</h1>
          {subtitle && <p className="text-sm opacity-90">{subtitle}</p>}
        </div>
      </div>
      <div className="max-w-md mx-auto px-4 -mt-4 pb-44">{children}</div>
    </>
  );
}
