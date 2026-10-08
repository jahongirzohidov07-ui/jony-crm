import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";

/**
 * AVTOMUZLATISHDA YO'QOLGAN YO'QLAMALAR (2026-10-08, Jahongir: "avval
 * ro'yxatni ko'rsat"). Faqat ko'rish — hech narsa o'zgarmaydi. Audit
 * jurnalidan: ustoz nima belgilagan, kim, qachon; va muzlatilgan payt
 * umuman belgilab bo'lmagan darslar.
 */
type Lost = { group: string; date: string; value: string; by?: string; at?: string };
type Row = {
  student_id: number; full_name: string; status: string;
  group?: string | null; branch?: string | null;
  events: { at: string; kind: string; note?: string }[];
  lost: Lost[]; lost_present: number; blank: string[];
};
type Data = { rows: Row[]; students: number; lost: number; lost_present: number; blank: number };

const TONE: Record<string, string> = {
  keldi: "bg-emerald-100 text-emerald-700",
  "kech keldi": "bg-amber-100 text-amber-700",
  kelmadi: "bg-red-100 text-red-700",
};
const STATUS: Record<string, string> = {
  active: "Faol", frozen: "Muzlatilgan", archived: "Arxiv", left: "Ketgan", trial: "Sinovda",
};

export default function FreezeLosses() {
  const [d, setD] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<Data>("/attendance/freeze-losses?since=2026-08-01").then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);
  if (err) return <p className="text-sm text-red-600">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400">Yuklanmoqda...</p>;

  return (
    <div>
      <p className="text-sm text-slate-600 mb-4">
        Avtomuzlatish (yoki sinovdan chiqish) paytida yo'qolgan yo'qlamalar —
        audit jurnalidan. <b>Hech narsa o'zgartirilmagan</b>, faqat ro'yxat.
      </p>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-5">
        {[
          ["O'quvchi", d.students],
          ["Yo'qolgan belgi", d.lost],
          ["Shundan «keldi»", d.lost_present],
          ["Muzlatilgan payt belgisiz dars", d.blank],
        ].map(([l, v]) => (
          <div key={l as string} className="bg-white rounded-xl border border-slate-200 p-3">
            <p className="text-xs text-slate-500">{l}</p>
            <p className="text-lg font-semibold text-slate-900">{v}</p>
          </div>
        ))}
      </div>
      {d.rows.length === 0 ? (
        <p className="text-sm text-slate-400 py-8 text-center">Yo'qolgan yo'qlama topilmadi.</p>
      ) : (
        <div className="space-y-2">
          {d.rows.map((r) => (
            <div key={r.student_id} className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex flex-wrap items-center gap-2">
                <Link to={`/students/${r.student_id}`}
                  className="text-sm font-medium text-slate-900 hover:text-brand-700">
                  {r.full_name}
                </Link>
                <span className="text-xs text-slate-500">
                  {[r.group, r.branch, STATUS[r.status] || r.status].filter(Boolean).join(" · ")}
                </span>
              </div>
              {r.events.map((e, i) => (
                <p key={i} className="text-xs text-slate-500 mt-1">
                  {e.at} — {e.kind === "auto_freeze" ? "Avtomuzlatildi"
                    : e.kind === "trial_dropout" ? "Sinovdan chiqarildi" : "Tozalash"}
                </p>
              ))}
              {r.lost.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-slate-700 mb-1">
                    Yo'qolgan belgilar (ustoz qo'ygani):
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {r.lost.map((x) => (
                      <span key={x.group + x.date}
                        title={`${x.group} · ${x.by || ""} · ${x.at || ""}`}
                        className={`px-2 py-0.5 rounded text-xs ${TONE[x.value] || "bg-slate-100"}`}>
                        {formatDate(x.date)}: {x.value}
                        {x.by ? ` (${x.by})` : ""}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {r.blank.length > 0 && (
                <p className="text-xs text-slate-500 mt-2">
                  Muzlatilgan payt belgilab bo'lmagan darslar:{" "}
                  {r.blank.map((x) => formatDate(x)).join(", ")}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
