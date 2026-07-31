import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Layers, Info, Users, Clock, MapPin, BookOpen, ChevronRight,
} from "lucide-react";
import { api, type MyGroupList } from "../lib/api";
import { formatDate } from "../lib/format";

const HW_TONE: Record<string, string> = {
  emerald: "bg-emerald-100 text-emerald-700",
  amber: "bg-amber-100 text-amber-700",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-600",
};

/** Ustozning O'Z guruhlari. Boshqa ustozlarning guruhlari umuman
 *  yuklanmaydi — bu backendda kesiladi, frontendda yashirilmaydi. */
export default function MyGroups() {
  const [d, setD] = useState<MyGroupList | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<MyGroupList>("/me/groups")
      .then(setD)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Layers size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Guruhlarim</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        {d.total_groups} guruh · {d.total_students} o'quvchi
      </p>

      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Sizga hali guruh biriktirilmagan.
        </p>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
          {d.rows.map((g) => (
            <Link
              key={g.id}
              to={`/groups/${g.id}`}
              className="bg-white border border-slate-200 rounded-xl p-4 block hover:border-brand-400 hover:shadow-sm transition"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="font-medium text-slate-900 mb-0.5">{g.name}</p>
                <ChevronRight size={16} className="text-slate-300 shrink-0" />
              </div>
              <p className="text-xs text-slate-500 mb-3">
                {[g.subject_label, g.level].filter(Boolean).join(" · ") || "—"}
              </p>

              <div className="space-y-1.5 text-sm text-slate-600">
                <p className="flex items-center gap-2">
                  <Users size={14} className="text-slate-400 shrink-0" />
                  {g.students} o'quvchi
                </p>
                <p className="flex items-center gap-2">
                  <Clock size={14} className="text-slate-400 shrink-0" />
                  {[g.days, g.time].filter(Boolean).join(" · ") || "—"}
                </p>
                {g.room && (
                  <p className="flex items-center gap-2">
                    <MapPin size={14} className="text-slate-400 shrink-0" />
                    {g.room}
                  </p>
                )}
                {g.homework && g.homework.percent != null && (
                  <p className="flex items-center gap-2">
                    <BookOpen size={14} className="text-slate-400 shrink-0" />
                    Uy vazifasi{" "}
                    <span
                      className={`px-1.5 py-0.5 rounded text-[11px] font-medium ${
                        HW_TONE[g.homework.tone] || HW_TONE.slate
                      }`}
                    >
                      {g.homework.percent}% · {g.homework.label}
                    </span>
                  </p>
                )}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500 space-y-0.5">
                {g.last_lesson && (
                  <p>Oxirgi dars: {formatDate(g.last_lesson)}</p>
                )}
                {g.next_lesson && (
                  <p>Keyingi dars: {formatDate(g.next_lesson)}</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      <p className="text-xs text-slate-500 mt-5 flex items-start gap-1.5">
        <Info size={13} className="text-slate-400 shrink-0 mt-0.5" />
        {d.hint}
      </p>
    </div>
  );
}
