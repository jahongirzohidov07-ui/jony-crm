import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Check, Clock, Trash2 } from "lucide-react";
import { api } from "../../lib/api";
import { pushToast } from "../../lib/toast";
import { Time24Input } from "../../components/Time24Input";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY TEACHER — SUPPORT TEACHER SOAT BELGILASH (2026-08-10).
 *
 * Jahongir: "Supportlar soat belgilashi yo'q bo'lib qolibdi."
 *
 * Support teacherning kunlik ishi ustozникidan BOSHQA: u yo'qlama
 * qo'ymaydi (bu ustozning ishi), balki O'Z SEANSINI — qaysi guruh
 * bilan, soat nechadan nechagacha, nechta o'quvchi bilan ishlaganini
 * yozadi. Oyligi aynan shundan hisoblanadi.
 *
 * Yozish mavjud POST /api/me/support-sessions orqali ketadi (yangi
 * yo'l yozilmadi) — u yerda sana qoidalari, takror kiritishdan
 * himoya va oylik hisobi allaqachon bor.
 */
export default function TeacherSession() {
  const [d, setD] = useState<Any>(null);
  const [opts, setOpts] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [f, setF] = useState({
    group_id: "",
    start_time: "",
    hours: 0,
    students_count: "",
  });

  const load = () => {
    setErr("");
    api
      .get<Any>("/me/support-sessions")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };

  useEffect(() => {
    load();
    // Guruhlar VA ruxsat etilgan soatlar backend'dan (chegara ikki
    // joyda yozilib qolmasin).
    api
      .get<Any>("/teacher/support-options")
      .then(setOpts)
      .catch(() => setOpts(null));
  }, []);

  const groups: Any[] = opts?.groups || [];
  const steps: number[] = opts?.hour_steps || [1, 1.5, 2, 2.5, 3];
  const valid =
    !!f.group_id && !!f.start_time && f.hours > 0 &&
    Number(f.students_count) > 0;

  async function add() {
    if (!valid || busy) return;
    setBusy(true);
    try {
      await api.post("/me/support-sessions", {
        group_id: Number(f.group_id),
        start_time: f.start_time,
        // Tugash vaqti EMAS — necha soat dars o'tgani. Server
        // tugash vaqtini o'zi hisoblaydi.
        hours: f.hours,
        students_count: Number(f.students_count),
      });
      setF({ group_id: "", start_time: "", hours: 0, students_count: "" });
      pushToast("Seans yozildi", "success", 2500);
      load();
    } catch {
      // xato toast'da ko'rinadi
    } finally {
      setBusy(false);
    }
  }

  async function del(id: number) {
    try {
      await api.delete(`/me/support-sessions/${id}`);
      load();
    } catch {
      /* toast */
    }
  }

  const rows: Any[] = d?.rows || d?.sessions || [];

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/teacher"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Bugun
          </Link>
          <h1 className="text-lg font-semibold">Soat belgilash</h1>
          <p className="text-sm opacity-90">
            {d?.period || "Bugungi seansingizni yozing"}
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-4 pb-8">
        {/* ---- Yangi seans ---- */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-3">
          <p className="text-sm font-semibold text-slate-800">Yangi seans</p>

          <div>
            <label className="block text-[11px] text-slate-500 mb-1">
              Guruh
            </label>
            <select
              value={f.group_id}
              onChange={(e) => setF({ ...f, group_id: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm bg-white"
            >
              <option value="">Guruhni tanlang</option>
              {groups.map((g) => (
                <option key={g.id} value={g.id}>
                  {g.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-500 mb-1">
              Boshlandi
            </label>
            <Time24Input
              value={f.start_time}
              onChange={(e) => setF({ ...f, start_time: e.target.value })}
              className="w-full rounded-lg border border-slate-300 px-2 py-2.5 text-sm"
            />
          </div>

          {/* SOATNI SUPPORTNING O'ZI TANLAYDI (Jahongir, 2026-08-10):
              kamida 1, ko'pi bilan 3 soat. Tugash vaqtini hisoblab
              o'tirmaydi — server o'zi chiqaradi. */}
          <div>
            <label className="block text-[11px] text-slate-500 mb-1.5">
              Necha soat dars o'tdingiz
            </label>
            <div className="grid grid-cols-5 gap-1.5">
              {steps.map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => setF({ ...f, hours: h })}
                  className={`py-2.5 rounded-lg border text-sm font-semibold transition ${
                    f.hours === h
                      ? "bg-brand-600 text-white border-transparent"
                      : "bg-white text-slate-600 border-slate-200"
                  }`}
                >
                  {h}
                </button>
              ))}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">
              {opts?.min_hours ?? 1}–{opts?.max_hours ?? 3} soat oralig'ida
            </p>
          </div>

          <div>
            <label className="block text-[11px] text-slate-500 mb-1">
              Nechta o'quvchi bilan ishladingiz
            </label>
            <input
              type="number"
              inputMode="numeric"
              min={1}
              value={f.students_count}
              onChange={(e) =>
                setF({ ...f, students_count: e.target.value })
              }
              className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
              placeholder="masalan 6"
            />
          </div>

          <button
            onClick={add}
            disabled={!valid || busy}
            className="w-full py-3 rounded-xl bg-brand-600 text-white text-sm font-semibold flex items-center justify-center gap-2 disabled:opacity-40"
          >
            <Check size={16} />
            {busy ? "Saqlanmoqda…" : "Seansni yozish"}
          </button>
        </div>

        {/* ---- Bu oydagi seanslar ---- */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
          <p className="text-sm font-semibold text-slate-800 mb-3">
            Bu oydagi seanslarim
          </p>
          {err && <p className="text-sm text-red-600 mb-2">{err}</p>}
          {rows.length === 0 && !err && (
            <p className="text-sm text-slate-400 text-center py-6">
              Hali seans yozilmagan.
            </p>
          )}
          <div className="space-y-2">
            {rows.map((r: Any) => (
              <div
                key={r.id}
                className="flex items-center gap-2.5 text-sm border-b border-slate-50 last:border-0 pb-2 last:pb-0"
              >
                <Clock size={14} className="text-slate-300 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-slate-800 truncate">
                    {r.group || r.group_name || "—"}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {(r.date || "").slice(8, 10)}.{(r.date || "").slice(5, 7)} ·{" "}
                    {r.start_time}–{r.end_time}
                    {r.students_count ? ` · ${r.students_count} o'quvchi` : ""}
                  </p>
                </div>
                <button
                  onClick={() => del(r.id)}
                  className="text-slate-300 hover:text-red-500 shrink-0"
                  aria-label="O'chirish"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <p className="text-[11px] text-slate-400 text-center px-6">
          Oyligingiz shu seanslardan hisoblanadi — darsni o'sha kuni
          yozib qo'ying.
        </p>
      </div>
    </>
  );
}
