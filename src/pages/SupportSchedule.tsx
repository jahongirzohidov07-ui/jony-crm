import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CalendarDays, Users2 } from "lucide-react";
import { api, type Branch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { SUPPORT_TT_VIEW, can } from "../lib/roles";

const DAYS: { key: string; label: string }[] = [
  { key: "mon", label: "Dushanba" },
  { key: "tue", label: "Seshanba" },
  { key: "wed", label: "Chorshanba" },
  { key: "thu", label: "Payshanba" },
  { key: "fri", label: "Juma" },
  { key: "sat", label: "Shanba" },
  { key: "sun", label: "Yakshanba" },
];

type Block = {
  kind: "group" | "busy";
  label: string;
  group_id?: number | null;
  time: string;
  room?: string | null;
};
type Row = {
  teacher_id: number;
  name: string;
  branch?: string | null;
  blocks: Block[];
};

/** Supportlar bo'yicha ALOHIDA jadval: kim qachon qaysi guruhda band,
 *  qaysi vaqtni o'zi "dars qo'yilmasin" deb belgilagan. Support
 *  manager kimdan so'ramasdan darsni qo'yaveradi. */
export default function SupportSchedule() {
  const { user } = useAuth();
  const nav = useNavigate();
  const today = new Date().getDay(); // 0=yak
  const defDay = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"][today];
  const [day, setDay] = useState(defDay === "sun" ? "mon" : defDay);
  const [rows, setRows] = useState<Row[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [branchF, setBranchF] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<Branch[]>("/branches").then(setBranches).catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    api
      .get<{ rows: Row[] }>(
        `/support-timetable?day=${day}${branchF ? `&branch_id=${branchF}` : ""}`
      )
      .then((r) => setRows(r.rows))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [day, branchF]);

  if (!can(user?.role, SUPPORT_TT_VIEW)) {
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">
          Bu sahifani ko'rish uchun ruxsatingiz yo'q.
        </p>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-8">
      <h1 className="text-xl font-semibold text-slate-900 mb-1 flex items-center gap-2">
        <Users2 size={20} className="text-brand-600" /> Supportlar jadvali
      </h1>
      <p className="text-sm text-slate-500 mb-5">
        Qaysi support qachon band — guruhlari va o'zi belgilagan vaqtlari
        bir qarashda
      </p>

      <div className="flex flex-wrap items-center gap-2 mb-5">
        {DAYS.map((d) => (
          <button
            key={d.key}
            onClick={() => setDay(d.key)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              day === d.key
                ? "bg-brand-600 text-white"
                : "bg-white border border-slate-200 text-slate-600 hover:border-slate-300"
            }`}
          >
            {d.label}
          </button>
        ))}
        <div className="flex-1" />
        <select
          value={branchF}
          onChange={(e) => setBranchF(e.target.value)}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm bg-white"
        >
          <option value="">Barcha filiallar</option>
          {branches.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>
      ) : rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-10 text-center">
          Support teacher topilmadi
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-xs text-slate-500 uppercase">
              <tr>
                <th className="text-left px-4 py-3 font-medium w-56">
                  Support
                </th>
                <th className="text-left px-4 py-3 font-medium">
                  <span className="inline-flex items-center gap-1.5">
                    <CalendarDays size={13} />
                    Bandligi ({DAYS.find((d) => d.key === day)?.label})
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.teacher_id} className="border-t border-slate-100 align-top">
                  <td className="px-4 py-3">
                    <p className="font-medium text-slate-800">{r.name}</p>
                    {r.branch && (
                      <p className="text-xs text-slate-400">{r.branch}</p>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {r.blocks.length === 0 ? (
                      <span className="text-xs text-emerald-600 bg-emerald-50 rounded-md px-2 py-1">
                        Bo'sh — dars qo'ysa bo'ladi
                      </span>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {r.blocks.map((b, i) => (
                          <span
                            key={i}
                            onClick={() => {
                              if (b.kind === "group" && b.group_id)
                                nav(`/groups/${b.group_id}`);
                            }}
                            title={b.kind === "busy" ? "O'zi belgilagan band vaqt" : "Guruhga kirish uchun bosing"}
                            className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs border ${
                              b.kind === "busy"
                                ? "bg-red-50 border-red-200 text-red-700"
                                : "bg-teal-50 border-teal-200 text-teal-800 cursor-pointer hover:bg-teal-100 hover:border-teal-300"
                            }`}
                          >
                            <span className="font-semibold">{b.time}</span>
                            {b.label}
                            {b.room ? ` · ${b.room}` : ""}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-slate-400 mt-3">
        Yashil — bo'sh; ko'k — support darsi (biriktirishda belgilangan
        vaqt); qizil — support o'zi "dars qo'yilmasin" degan vaqt.
        Vaqti belgilanmagan biriktirishlar jadvalda ko'rinmaydi.
      </p>
    </div>
  );
}
