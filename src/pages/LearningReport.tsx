import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { BarChart3, Send, ArrowLeft } from "lucide-react";
import { api } from "../lib/api";

/**
 * O'QUV HISOBOTI + O'ZLASHTIRISH XARITASI (2026-09-18, Jahongir,
 * 5- va 8-bandlar). Rahbar: guruh reja bo'yicha qayerda, qiyin mavzular,
 * uy vazifasi, tekshirish kutayotgan ishlar, yordamga muhtoj o'quvchilar,
 * materialning zaif joylari. Ustoz: o'z guruhlari + har o'quvchining
 * xaritasi (o'zlashtirdi / yana mashq kerak / hali tekshirilmagan) va bir
 * bosishda qo'shimcha mashq.
 */

type Group = {
  group_id: number; group: string; teacher: string | null; students: number;
  plan: { course: string; next_lesson_no: number; total: number; carry: string[]; lessons_run: number } | null;
  homework_pct: number | null;
  assignments: { sent: number; expected: number; done: number; done_pct: number | null; pending_checks: number };
  need_help: { student_id: number; name: string; weak: number }[];
};
type Report = { since: string; groups: Group[]; pending_checks: number;
  hard_topics: { course: string; lesson_no: number; skill: string; students: number; title: string }[];
  material_weak: { course: string; lesson_no: number; kind: string; avg_pct: number; n: number }[] };
type Cell = { status: "mastered" | "practice" | "unchecked"; ratio: number | null };
type Mastery = {
  group: string; group_id: number; plan: { course: string; next_lesson_no: number; total: number } | null;
  students: { id: number; name: string }[]; lessons: { no: number; title: string }[]; skills: string[];
  cells: Record<string, Record<string, Cell>>;
  summary: { student_id: number; name: string; mastered: number; practice: number; unchecked: number; text: string;
    weak: { lesson_no: number; skill: string; title: string; ratio: number }[] }[];
  hard_topics: { lesson_no: number; skill: string; count: number; title: string }[];
};

const ST_CLS: Record<string, string> = { mastered: "bg-emerald-500", practice: "bg-amber-400", unchecked: "bg-slate-200" };
const SK_LABEL: Record<string, string> = { vocab: "Lug'at", grammar: "Grammatika", writing: "Writing", speaking: "Speaking" };

export default function LearningReport() {
  const [params, setParams] = useSearchParams();
  const gid = params.get("group");
  if (gid) return <GroupMastery gid={Number(gid)} back={() => setParams({})} />;
  return <ReportHome onOpen={(id) => setParams({ group: String(id) })} />;
}

function ReportHome({ onOpen }: { onOpen: (id: number) => void }) {
  const [d, setD] = useState<Report | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => { api.fresh<Report>("/reports/learning").then(setD).catch((e) => setErr(e.message)); }, []);
  if (err) return <div className="p-8 text-rose-600">{err}</div>;
  if (!d) return <div className="p-8 text-slate-500">Yuklanmoqda…</div>;
  return (
    <div className="p-6 md:p-8 max-w-6xl">
      <h1 className="text-xl font-semibold text-slate-900 flex items-center gap-2 mb-1"><BarChart3 size={20} className="text-brand-600" /> O'quv hisoboti</h1>
      <p className="text-sm text-slate-500 mb-4">O'quvchi o'sishi va ishlarning o'z vaqtida bajarilishi bo'yicha (oxirgi 28 kun, {d.since} dan). Ustoz "necha marta kirdi" bilan baholanmaydi.</p>

      <div className="grid sm:grid-cols-3 gap-3 mb-5">
        <div className="bg-white rounded-xl border border-slate-200 p-4"><div className="text-xs text-slate-500">Tekshirishni kutayotgan ishlar</div><div className="text-2xl font-bold text-violet-700">{d.pending_checks}</div></div>
        <div className="bg-white rounded-xl border border-slate-200 p-4"><div className="text-xs text-slate-500">Qo'shimcha yordamga muhtoj</div><div className="text-2xl font-bold text-rose-600">{d.groups.reduce((a, g) => a + g.need_help.length, 0)}</div></div>
        <div className="bg-white rounded-xl border border-slate-200 p-4"><div className="text-xs text-slate-500">Guruhlar</div><div className="text-2xl font-bold text-slate-900">{d.groups.length}</div></div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto mb-5">
        <table className="w-full text-sm">
          <thead><tr className="bg-slate-50 text-slate-600 text-left">
            <th className="px-3 py-2">Guruh</th><th className="px-3 py-2">Reja bo'yicha</th><th className="px-3 py-2">Ko'chgan qismlar</th>
            <th className="px-3 py-2">Uy vazifasi</th><th className="px-3 py-2">Topshiriqlar</th><th className="px-3 py-2">Kutayotgan</th><th className="px-3 py-2">Yordam kerak</th><th></th>
          </tr></thead>
          <tbody>
            {d.groups.map((g) => (
              <tr key={g.group_id} className="border-t border-slate-100">
                <td className="px-3 py-2"><div className="font-medium text-slate-900">{g.group}</div><div className="text-xs text-slate-500">{g.teacher ?? "—"} · {g.students} o'quvchi</div></td>
                <td className="px-3 py-2">{g.plan ? (
                  <div><div className="font-medium">{g.plan.next_lesson_no - 1}/{g.plan.total} dars</div>
                    <div className="h-1.5 bg-slate-100 rounded mt-1 w-28"><div className="h-full bg-brand-600 rounded" style={{ width: `${Math.round(100 * (g.plan.next_lesson_no - 1) / g.plan.total)}%` }} /></div></div>
                ) : <span className="text-amber-600 text-xs">reja bog'lanmagan</span>}</td>
                <td className="px-3 py-2 text-xs text-amber-700">{g.plan?.carry.length ? g.plan.carry.join("; ") : "—"}</td>
                <td className="px-3 py-2">{g.homework_pct == null ? "—" : <span className={g.homework_pct < 60 ? "text-rose-600 font-medium" : ""}>{g.homework_pct}%</span>}</td>
                <td className="px-3 py-2">{g.assignments.sent ? `${g.assignments.done}/${g.assignments.expected} (${g.assignments.done_pct ?? 0}%)` : "—"}</td>
                <td className="px-3 py-2">{g.assignments.pending_checks ? <span className="text-violet-700 font-medium">{g.assignments.pending_checks}</span> : "0"}</td>
                <td className="px-3 py-2 text-xs">{g.need_help.length ? g.need_help.map((h) => h.name).join(", ") : "—"}</td>
                <td className="px-3 py-2"><button onClick={() => onOpen(g.group_id)} className="text-xs text-brand-600">Xarita →</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="font-semibold text-slate-800 mb-2">Ko'pchilik qiynalayotgan mavzular</h3>
          {d.hard_topics.length === 0 ? <p className="text-sm text-slate-500">Hali ma'lumot yo'q (topshiriqlar bajarilgach chiqadi).</p> : (
            <ul className="text-sm space-y-1">{d.hard_topics.map((t, i) => <li key={i}><b>{t.lesson_no}-dars</b> {SK_LABEL[t.skill] ?? t.skill} — {t.students} o'quvchi <span className="text-slate-400">· {t.title}</span></li>)}</ul>
          )}
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <h3 className="font-semibold text-slate-800 mb-2">Materialning yaxshilash kerak joylari</h3>
          {d.material_weak.length === 0 ? <p className="text-sm text-slate-500">Kamida 3 ta natija bo'lgan topshiriqlar bo'yicha chiqadi.</p> : (
            <ul className="text-sm space-y-1">{d.material_weak.map((m, i) => <li key={i}><b>{m.lesson_no}-dars</b> {m.kind} — o'rtacha {m.avg_pct}% ({m.n} ish)</li>)}</ul>
          )}
        </div>
      </div>
    </div>
  );
}

function GroupMastery({ gid, back }: { gid: number; back: () => void }) {
  const [d, setD] = useState<Mastery | null>(null);
  const [err, setErr] = useState("");
  const [sel, setSel] = useState<Record<number, boolean>>({});
  const [lessonNo, setLessonNo] = useState<number>(0);
  const [skill, setSkill] = useState("vocab");
  const [msg, setMsg] = useState("");
  useEffect(() => {
    api.fresh<Mastery>(`/groups/${gid}/mastery`)
      .then((m) => { setD(m); if (m.plan) setLessonNo(Math.max(1, m.plan.next_lesson_no - 1)); })
      .catch((e) => setErr(e.message));
  }, [gid]);

  async function practice() {
    const ids = Object.keys(sel).filter((k) => sel[Number(k)]).map(Number);
    if (!ids.length || !lessonNo) return;
    try {
      const r = await api.post<{ sent: number }>(`/groups/${gid}/mastery/practice`, { student_ids: ids, lesson_no: lessonNo, skill });
      setMsg(`${r.sent} ta qo'shimcha mashq yuborildi (${lessonNo}-dars, ${SK_LABEL[skill]}).`); setSel({});
    } catch (e) { setMsg((e as Error).message); }
  }

  if (err) return <div className="p-8 text-rose-600">{err}</div>;
  if (!d) return <div className="p-8 text-slate-500">Yuklanmoqda…</div>;
  return (
    <div className="p-6 md:p-8 max-w-7xl">
      <button onClick={back} className="text-sm text-slate-500 flex items-center gap-1 mb-1"><ArrowLeft size={14} /> Hisobot</button>
      <h1 className="text-xl font-semibold text-slate-900 mb-1">{d.group} — o'zlashtirish xaritasi</h1>
      {!d.plan && <p className="text-sm text-amber-600">Guruh rejaga bog'lanmagan — ustoz "Bugun" oynasida bog'laydi.</p>}
      <div className="flex gap-3 text-xs text-slate-600 mb-3">
        <span className="flex items-center gap-1"><i className="w-3 h-3 rounded bg-emerald-500 inline-block" /> o'zlashtirdi (≥80%)</span>
        <span className="flex items-center gap-1"><i className="w-3 h-3 rounded bg-amber-400 inline-block" /> yana mashq kerak</span>
        <span className="flex items-center gap-1"><i className="w-3 h-3 rounded bg-slate-200 inline-block" /> hali tekshirilmagan</span>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <Send size={14} className="text-brand-600" />
          <span className="text-sm text-slate-700">Tanlanganlarga qo'shimcha mashq:</span>
          <select value={lessonNo} onChange={(e) => setLessonNo(Number(e.target.value))} className="text-sm border border-slate-200 rounded-lg px-2 py-1">
            {d.lessons.map((l) => <option key={l.no} value={l.no}>{l.no}-dars</option>)}
          </select>
          <select value={skill} onChange={(e) => setSkill(e.target.value)} className="text-sm border border-slate-200 rounded-lg px-2 py-1">
            <option value="vocab">Lug'at testi</option><option value="grammar">Grammatika testi</option>
          </select>
          <button onClick={practice} disabled={!Object.values(sel).some(Boolean)} className="text-sm bg-brand-600 text-white rounded-lg px-3 py-1.5 disabled:opacity-40">Bir bosishda yuborish</button>
          {msg && <span className="text-xs text-emerald-700">{msg}</span>}
        </div>
        <div className="space-y-1">
          {d.summary.map((s) => (
            <label key={s.student_id} className="flex items-start gap-2 text-sm">
              <input type="checkbox" checked={!!sel[s.student_id]} onChange={(e) => setSel({ ...sel, [s.student_id]: e.target.checked })} className="mt-1" />
              <span><b>{s.name}</b>: {s.text} <span className="text-xs text-slate-400">· ✓{s.mastered} · ⚠{s.practice} · ?{s.unchecked}</span></span>
            </label>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
        <table className="text-xs">
          <thead><tr className="bg-slate-50">
            <th className="px-2 py-2 text-left sticky left-0 bg-slate-50">O'quvchi</th>
            {d.lessons.map((l) => <th key={l.no} className="px-1 py-2 text-center" title={l.title}>{l.no}</th>)}
          </tr></thead>
          <tbody>
            {d.students.map((st) => (
              <tr key={st.id} className="border-t border-slate-100">
                <td className="px-2 py-1.5 whitespace-nowrap sticky left-0 bg-white">{st.name}</td>
                {d.lessons.map((l) => {
                  const c = d.cells[`${st.id}:${l.no}`] || {};
                  return (
                    <td key={l.no} className="px-1 py-1.5">
                      <div className="grid grid-cols-2 gap-0.5" title={d.skills.map((k) => `${SK_LABEL[k]}: ${c[k]?.status ?? "-"}${c[k]?.ratio != null ? ` ${c[k].ratio}%` : ""}`).join("\n")}>
                        {d.skills.map((k) => <i key={k} className={`w-2.5 h-2.5 rounded-sm inline-block ${ST_CLS[c[k]?.status ?? "unchecked"]}`} />)}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <div className="text-[11px] text-slate-400 px-2 py-1">Har katak: ▪ lug'at ▪ grammatika / ▪ writing ▪ speaking</div>
      </div>
      {d.hard_topics.length > 0 && (
        <div className="mt-4 text-sm text-slate-700">Guruhda qiyin: {d.hard_topics.map((t) => `${t.lesson_no}-dars ${SK_LABEL[t.skill]} (${t.count})`).join(", ")}</div>
      )}
      <div className="mt-3"><Link to="/plans" className="text-xs text-brand-600">Dars rejalari →</Link></div>
    </div>
  );
}
