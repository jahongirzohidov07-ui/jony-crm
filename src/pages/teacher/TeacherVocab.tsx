import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, BookA, Check } from "lucide-react";
import { api } from "../../lib/api";
import { pushToast } from "../../lib/toast";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY TEACHER — LUG'AT UNITLARINI TASDIQLASH (2026-08-11).
 *
 * Jahongir: "ustoz 1-unitni topshirdi degan tick qo'ysa unit avtomat
 * 100% bo'lishi kerak." O'quvchi practice bilan 99% gacha yig'adi -
 * yakuniy 100% faqat shu yerdan.
 */
export default function TeacherVocab() {
  const [groups, setGroups] = useState<Any[]>([]);
  const [gid, setGid] = useState<number | null>(null);
  const [students, setStudents] = useState<Any[]>([]);
  const [sid, setSid] = useState<number | null>(null);
  const [prog, setProg] = useState<Any>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Any>("/me/groups")
      .then((r) => {
        const gs = r.rows || [];
        setGroups(gs);
        if (gs.length === 1) setGid(gs[0].id);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!gid) return;
    setStudents([]);
    setSid(null);
    setProg(null);
    api
      .get<Any>(`/teacher/vocab-students?group_id=${gid}`)
      .then((r) => setStudents(r.students || []))
      .catch(() => {});
  }, [gid]);

  const loadProg = (studentId: number) => {
    setSid(studentId);
    setProg(null);
    api
      .get<Any>(`/teacher/vocab/${studentId}`)
      .then(setProg)
      .catch(() => {});
  };

  async function toggle(unit: string, passed: boolean) {
    if (!sid || busy) return;
    setBusy(unit);
    try {
      await api.post("/teacher/vocab-pass", {
        student_id: sid,
        unit,
        passed,
      });
      pushToast(
        passed ? `${unit} topshirildi ✓` : `${unit} bekor qilindi`,
        "success",
        2000,
      );
      loadProg(sid);
    } catch {
      /* toast */
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-6 pb-10">
        <div className="max-w-md mx-auto">
          <Link
            to="/teacher/more"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Bo'limlar
          </Link>
          <h1 className="text-lg font-semibold flex items-center gap-2">
            <BookA size={20} />
            Lug'at unitlari
          </h1>
          <p className="text-sm opacity-90 mt-0.5">
            O'quvchi unitni topshirsa — tick qo'ying, 100% bo'ladi
          </p>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-5 space-y-3 pb-8">
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4 space-y-3">
          <div>
            <label className="block text-[11px] text-slate-500 mb-1">
              Guruh
            </label>
            <select
              value={gid ?? ""}
              onChange={(e) => setGid(Number(e.target.value) || null)}
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
          {students.length > 0 && (
            <div>
              <label className="block text-[11px] text-slate-500 mb-1">
                O'quvchi
              </label>
              <select
                value={sid ?? ""}
                onChange={(e) => loadProg(Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm bg-white"
              >
                <option value="">O'quvchini tanlang</option>
                {students.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.full_name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {prog && (
          <div className="space-y-2">
            {(prog.units || []).map((u: Any) => (
              <div
                key={u.key}
                className="bg-white rounded-xl shadow-sm border border-slate-200 p-3.5 flex items-center gap-3"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-800">
                    {u.key}
                  </p>
                  <div className="h-1.5 bg-slate-100 rounded-full mt-1.5 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        u.passed ? "bg-amber-400" : "bg-sky-500"
                      }`}
                      style={{ width: `${u.percent}%` }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {u.percent}% · {u.learned3}/{u.n} so'z o'rganilgan
                  </p>
                </div>
                <button
                  disabled={busy === u.key}
                  onClick={() => toggle(u.key, !u.passed)}
                  className={`w-11 h-11 rounded-xl border-2 flex items-center justify-center shrink-0 transition ${
                    u.passed
                      ? "bg-amber-400 border-amber-400 text-white"
                      : "border-slate-300 text-slate-300"
                  }`}
                  aria-label={
                    u.passed ? "Tasdiqni bekor qilish" : "Topshirdi"
                  }
                >
                  <Check size={20} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
