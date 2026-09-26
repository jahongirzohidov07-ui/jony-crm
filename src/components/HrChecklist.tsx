import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Check, X, Download, Search, PlayCircle, BookOpen, Link2, FileText, Plus, Pencil,
} from "lucide-react";
import { api } from "../lib/api";
import { exportToExcel } from "../lib/exportXlsx";

/**
 * CHECKLIST — HR uchun bitta katta jadval (2026-09-26).
 *
 * Jahongir: "supportlarga ko'rgan videolari va o'qigan kitobini o'tdi
 * o'tmadi qilib bitta katta jadvalda ko'rib tura olay".
 *
 * Qatorda xodim, ustunda video va kutubxona yozuvi. Videoning "o'tdi"
 * belgisini pleyer qo'yadi (aldab bo'lmaydi) — HR uni bosa olmaydi.
 * Kutubxona (kitob, havola, fayl) katagini HR bosib "o'tdi" qiladi yoki
 * bekor qiladi — kutubxonadagi belgi bilan bitta narsa.
 *
 * SHU YERNING O'ZIDAN QO'SHISH VA TAHRIRLASH (2026-09-26, Jahongir:
 * "shu yerni o'zidan o'zgartirib qo'sha olay"). "+ Qo'shish" yangi
 * ustun ochadi; ustun sarlavhasini bosish — nomi, havolasi,
 * majburiyligi yoki olib tashlash. Yozuvlar o'sha-o'sha kutubxona va
 * video bo'limida turadi, bu yerda faqat qulay kirish.
 */

type Col = {
  key: string; source: "pd" | "lib"; id: number; title: string;
  kind: string; kind_label: string; topic: string; required: boolean;
  targets: string[]; url: string | null;
  can_mark: boolean;
};
type Cell = { passed: boolean; percent: number; at: string | null; by: string | null };
type Row = {
  user_id: number; name: string; role: string; branch: string | null;
  cells: Record<string, Cell>; required: number; passed: number; percent: number;
};
type Data = {
  role: string; role_label: string; columns: Col[]; rows: Row[];
  roles: { key: string; label: string }[];
  summary: { people: number; complete: number; avg_percent: number };
  can_mark: boolean;
  can_edit_lib: boolean;
  can_edit_pd: boolean;
};

const KIND_ICON: Record<string, typeof PlayCircle> = {
  video: PlayCircle, book: BookOpen, link: Link2, file: FileText,
};

export function ChecklistTab() {
  const [role, setRole] = useState("support_teacher");
  const [d, setD] = useState<Data | null>(null);
  const [err, setErr] = useState("");
  const [q, setQ] = useState("");
  const [onlyLeft, setOnlyLeft] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  // null — yopiq, "new" — yangi qo'shish, Col — shu ustunni tahrirlash
  const [dialog, setDialog] = useState<Col | "new" | null>(null);

  const load = useCallback(() => {
    setErr("");
    api.get<Data>(`/hr/checklist?role=${encodeURIComponent(role)}`)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, [role]);
  useEffect(load, [load]);

  const rows = useMemo(() => {
    if (!d) return [];
    const needle = q.trim().toLowerCase();
    return d.rows.filter((r) =>
      (!needle || r.name.toLowerCase().includes(needle))
      && (!onlyLeft || r.passed < r.required));
  }, [d, q, onlyLeft]);

  async function toggle(r: Row, c: Col) {
    if (!c.can_mark || !d?.can_mark) return;
    const cell = r.cells[c.key];
    const next = !cell?.passed;
    const k = `${r.user_id}:${c.key}`;
    setBusy(k);
    try {
      await api.put(`/library/${c.id}/people/${r.user_id}`, { passed: next });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(null);
    }
  }

  function exportXlsx() {
    if (!d) return;
    exportToExcel(`checklist-${d.role}`, "Checklist", rows.map((r) => {
      const o: Record<string, unknown> = {
        "Xodim": r.name, "Filial": r.branch ?? "",
        "O'tdi": `${r.passed}/${r.required}`, "Foiz": `${r.percent}%`,
      };
      for (const c of d.columns) {
        const cell = r.cells[c.key];
        o[`${c.kind_label}: ${c.title}`] = cell?.passed
          ? "o'tdi" : `o'tmadi${cell && cell.percent ? ` (${cell.percent}%)` : ""}`;
      }
      return o;
    }));
  }

  if (err && !d) return <p className="text-sm text-red-600 py-6">{err}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-6">Yuklanmoqda…</p>;

  const pd = d.columns.filter((c) => c.source === "pd");
  const lib = d.columns.filter((c) => c.source === "lib");
  const canAdd = d.can_edit_lib || d.can_edit_pd;

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Checklist</h2>
          <p className="text-sm text-slate-500">
            Kim qaysi videoni ko'rdi, qaysi kitobni o'qidi — o'tdi / o'tmadi.
            Video belgisini pleyer o'zi qo'yadi; kitob va boshqa
            materiallarni katakni bosib belgilaysiz. Ustun nomini bosib
            tahrirlaysiz.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <select value={role} onChange={(e) => setRole(e.target.value)}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm bg-white">
            {d.roles.map((r) => (
              <option key={r.key} value={r.key}>{r.label}</option>
            ))}
          </select>
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={q} onChange={(e) => setQ(e.target.value)}
                   placeholder="Ism bo'yicha"
                   className="rounded-lg border border-slate-200 pl-8 pr-3 py-2 text-sm w-44" />
          </div>
          <label className="flex items-center gap-1.5 text-sm text-slate-600 cursor-pointer">
            <input type="checkbox" checked={onlyLeft}
                   onChange={(e) => setOnlyLeft(e.target.checked)} />
            Faqat tugatmaganlar
          </label>
          {canAdd && (
            <button onClick={() => setDialog("new")}
                    className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-3 py-2 text-sm font-medium">
              <Plus size={14} /> Qo'shish
            </button>
          )}
          <button onClick={exportXlsx}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50">
            <Download size={14} /> Excel
          </button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4 max-w-xl">
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <p className="text-xs text-slate-500">{d.role_label}</p>
          <p className="text-lg font-semibold text-slate-900">{d.summary.people}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <p className="text-xs text-slate-500">Hammasidan o'tgan</p>
          <p className="text-lg font-semibold text-emerald-600">{d.summary.complete}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3">
          <p className="text-xs text-slate-500">O'rtacha</p>
          <p className="text-lg font-semibold text-slate-900">{d.summary.avg_percent}%</p>
        </div>
      </div>

      {err && <p className="text-sm text-red-600 mb-2">{err}</p>}

      {d.columns.length === 0 ? (
        <div className="text-sm text-slate-500 bg-white rounded-xl border border-slate-200 p-6 text-center">
          <p>Bu lavozimga hali video yoki kitob biriktirilmagan.</p>
          {canAdd && (
            <button onClick={() => setDialog("new")}
                    className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white px-3 py-2 text-sm font-medium">
              <Plus size={14} /> Birinchisini qo'shish
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-auto max-h-[70vh]">
          <table className="text-sm border-separate border-spacing-0">
            <thead>
              <tr className="text-[11px] uppercase text-slate-500">
                <th className="sticky left-0 top-0 z-30 bg-slate-50 border-b border-r border-slate-200 px-3 py-2 text-left min-w-[200px]" rowSpan={2}>
                  Xodim
                </th>
                <th className="sticky top-0 z-20 bg-slate-50 border-b border-r border-slate-200 px-2 py-2" rowSpan={2}>
                  O'tdi
                </th>
                {pd.length > 0 && (
                  <th colSpan={pd.length} className="sticky top-0 z-20 bg-indigo-50 text-indigo-700 border-b border-r border-slate-200 px-2 py-1.5">
                    Videolar (avtomat)
                  </th>
                )}
                {lib.length > 0 && (
                  <th colSpan={lib.length} className="sticky top-0 z-20 bg-amber-50 text-amber-800 border-b border-slate-200 px-2 py-1.5">
                    Kutubxona (HR belgilaydi)
                  </th>
                )}
              </tr>
              <tr>
                {d.columns.map((c) => {
                  const Icon = KIND_ICON[c.kind] ?? FileText;
                  const editable = c.source === "pd" ? d.can_edit_pd : d.can_edit_lib;
                  return (
                    <th key={c.key}
                        title={`${c.kind_label}: ${c.title}${c.required ? "" : " (ixtiyoriy)"}${editable ? "\nBosing — tahrirlash" : ""}`}
                        className="sticky top-[29px] z-20 bg-white border-b border-r border-slate-200 p-0 align-bottom font-medium text-slate-700 min-w-[112px] max-w-[140px]">
                      <button type="button" disabled={!editable}
                              onClick={() => setDialog(c)}
                              className={`group w-full px-2 py-2 flex flex-col items-center gap-1 text-center ${
                                editable ? "hover:bg-slate-50 cursor-pointer" : "cursor-default"}`}>
                        <Icon size={14} className={c.source === "pd" ? "text-indigo-500" : "text-amber-600"} />
                        <span className="text-[11px] leading-tight line-clamp-3 normal-case">{c.title}</span>
                        {!c.required && <span className="text-[10px] text-slate-400">ixtiyoriy</span>}
                        {editable && (
                          <Pencil size={11} className="text-slate-300 group-hover:text-slate-500" />
                        )}
                      </button>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.user_id} className="hover:bg-slate-50/60">
                  <td className="sticky left-0 z-10 bg-white border-b border-r border-slate-100 px-3 py-2">
                    <p className="font-medium text-slate-800">{r.name}</p>
                    <p className="text-[11px] text-slate-400">{[r.role, r.branch].filter(Boolean).join(" · ")}</p>
                  </td>
                  <td className="border-b border-r border-slate-100 px-2 py-2 text-center whitespace-nowrap">
                    <span className={`font-semibold ${r.required && r.passed === r.required ? "text-emerald-600" : "text-slate-700"}`}>
                      {r.passed}/{r.required}
                    </span>
                    <div className="h-1.5 w-14 mx-auto mt-1 rounded bg-slate-100 overflow-hidden">
                      <div className="h-full bg-emerald-500" style={{ width: `${r.percent}%` }} />
                    </div>
                  </td>
                  {d.columns.map((c) => {
                    const cell = r.cells[c.key];
                    const ok = !!cell?.passed;
                    const k = `${r.user_id}:${c.key}`;
                    const markable = c.can_mark && d.can_mark;
                    const tip = ok
                      ? `O'tdi${cell?.at ? ` — ${cell.at}` : ""}${cell?.by ? ` (${cell.by})` : ""}`
                        + (markable ? "\nBosing — bekor qilish" : "")
                      : `O'tmadi${cell?.percent ? ` — ${cell.percent}%` : ""}`
                        + (markable ? "\nBosing — o'tdi deb belgilash" : "\nVideo ko'rilganda o'zi belgilanadi");
                    return (
                      <td key={c.key} className="border-b border-r border-slate-100 p-1 text-center">
                        <button
                          type="button"
                          disabled={!markable || busy === k}
                          onClick={() => toggle(r, c)}
                          title={tip}
                          className={`w-full rounded-md py-1.5 inline-flex flex-col items-center justify-center ${
                            ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-600"
                          } ${markable ? "hover:ring-2 hover:ring-slate-300 cursor-pointer" : "cursor-default"} ${
                            busy === k ? "opacity-50" : ""}`}
                        >
                          {ok ? <Check size={16} strokeWidth={3} /> : <X size={16} strokeWidth={3} />}
                          <span className="text-[10px] leading-none mt-0.5">
                            {ok ? "o'tdi" : cell?.percent ? `${cell.percent}%` : "o'tmadi"}
                          </span>
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={d.columns.length + 2} className="px-3 py-6 text-center text-slate-400">
                    Hech kim topilmadi
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {dialog && (
        <ItemDialog
          col={dialog === "new" ? null : dialog}
          role={d.role}
          roleLabel={d.role_label}
          allRoles={d.roles.map((r) => r.key)}
          canPd={d.can_edit_pd}
          canLib={d.can_edit_lib}
          onClose={() => setDialog(null)}
          onSaved={() => { setDialog(null); load(); }}
        />
      )}
    </div>
  );
}

type Kind = "book" | "link" | "pd";

/** Ustun qo'shish / tahrirlash: kitob, havola yoki YouTube video.
 *  YouTube video pleyer bilan kuzatiladi ("o'tdi"ni o'zi qo'yadi);
 *  kitob va havolani HR jadvalda bosib belgilaydi. */
function ItemDialog({ col, role, roleLabel, allRoles, canPd, canLib, onClose, onSaved }: {
  col: Col | null; role: string; roleLabel: string; allRoles: string[];
  canPd: boolean; canLib: boolean; onClose: () => void; onSaved: () => void;
}) {
  const initKind: Kind = col
    ? (col.source === "pd" ? "pd" : col.kind === "book" ? "book" : "link")
    : canLib ? "book" : "pd";
  const [kind, setKind] = useState<Kind>(initKind);
  const [title, setTitle] = useState(col?.title ?? "");
  const [url, setUrl] = useState(col?.url ?? "");
  const [required, setRequired] = useState(col?.required ?? true);
  const [err, setErr] = useState("");
  const [saving, setSaving] = useState(false);
  // Bir nechta lavozimga (yoki hammaga) berilgan yozuv — olib
  // tashlaganda faqat shu lavozim ro'yxatidan chiqadi.
  const shared = !!col && (col.targets.length === 0 || col.targets.length > 1);

  async function save() {
    setErr("");
    if (!title.trim()) { setErr("Nomini yozing"); return; }
    if ((kind === "pd" || kind === "link") && !url.trim()) {
      setErr(kind === "pd" ? "YouTube havolasini qo'ying" : "Havolani qo'ying");
      return;
    }
    setSaving(true);
    try {
      if (!col) {
        if (kind === "pd") {
          await api.post("/pd/videos", {
            title: title.trim(), yt: url.trim(), target_roles: [role], required,
          });
        } else {
          await api.post("/library", {
            title: title.trim(), kind, url: url.trim() || null,
            target_roles: [role], required,
          });
        }
      } else if (col.source === "pd") {
        const body: Record<string, unknown> = { title: title.trim(), required };
        if (url.trim() !== (col.url ?? "")) body.yt = url.trim();
        await api.put(`/pd/videos/${col.id}`, body);
      } else {
        await api.put(`/library/${col.id}`, {
          title: title.trim(), url: url.trim() || null, required,
        });
      }
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setSaving(false);
    }
  }

  /** Faqat SHU lavozim ro'yxatidan olib tashlaydi. Boshqa lavozimlarga
   *  ham berilgan bo'lsa — ularda qoladi; faqat shu lavozimga bo'lsa —
   *  yozuv yashiriladi (o'chirilmaydi, kim o'tgani tarixda qoladi). */
  async function remove() {
    if (!col) return;
    const msg = shared
      ? `"${col.title}" ${roleLabel} ro'yxatidan olib tashlanadi. Boshqa lavozimlarda qoladi.`
      : `"${col.title}" yashiriladi. Kim o'tgani saqlanib qoladi.`;
    if (!window.confirm(msg)) return;
    setSaving(true);
    try {
      const path = col.source === "pd" ? `/pd/videos/${col.id}` : `/library/${col.id}`;
      if (shared) {
        const base = col.targets.length === 0 ? allRoles : col.targets;
        await api.put(path, { target_roles: base.filter((r) => r !== role) });
      } else {
        await api.put(path, { active: false });
      }
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      setSaving(false);
    }
  }

  const kinds: { key: Kind; label: string; hint: string; ok: boolean }[] = [
    { key: "book", label: "Kitob", hint: "HR jadvalda bosib belgilaydi. Havola ixtiyoriy.", ok: canLib },
    { key: "link", label: "Havola", hint: "Maqola, kurs, hujjat. HR jadvalda bosib belgilaydi.", ok: canLib },
    { key: "pd", label: "YouTube video", hint: "JonyOS ichida ochiladi, kim qancha ko'rgani o'zi belgilanadi.", ok: canPd },
  ];

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-16 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-md p-5 shadow-xl">
        <div className="flex items-center justify-between mb-1">
          <h3 className="font-semibold text-slate-800">
            {col ? "Tahrirlash" : "Checklistga qo'shish"}
          </h3>
          <button onClick={onClose} className="text-slate-400"><X size={18} /></button>
        </div>
        <p className="text-xs text-slate-500 mb-4">
          {col
            ? `${col.kind_label} · ${shared ? "bir nechta lavozimda" : roleLabel}`
            : `${roleLabel} uchun yangi ustun`}
        </p>
        {err && <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-3">{err}</p>}
        <div className="space-y-3">
          {!col && (
            <div>
              <label className="block text-xs text-slate-500 mb-1">Turi</label>
              <div className="grid grid-cols-3 gap-2">
                {kinds.filter((k) => k.ok).map((k) => (
                  <button key={k.key} type="button" onClick={() => setKind(k.key)}
                          className={`rounded-lg border px-2 py-2 text-sm ${
                            kind === k.key ? "border-brand-600 bg-brand-50 text-brand-700 font-medium"
                              : "border-slate-200 text-slate-600"}`}>
                    {k.label}
                  </button>
                ))}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {kinds.find((k) => k.key === kind)?.hint}
              </p>
            </div>
          )}
          <div>
            <label className="block text-xs text-slate-500 mb-1">Nomi</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)}
                   placeholder={kind === "book" ? "Teach Like a Champion" : "Nomi"}
                   className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
          </div>
          <div>
            <label className="block text-xs text-slate-500 mb-1">
              {kind === "pd" ? "YouTube havolasi" : kind === "book" ? "Havola (ixtiyoriy)" : "Havola"}
            </label>
            <input value={url} onChange={(e) => setUrl(e.target.value)}
                   placeholder={kind === "pd" ? "https://youtu.be/..." : "https://..."}
                   className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm" />
          </div>
          <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
            <input type="checkbox" checked={required} onChange={(e) => setRequired(e.target.checked)} />
            Majburiy — "O'tdi" hisobiga kiradi
          </label>
        </div>
        <div className="flex items-center justify-between mt-5">
          {col ? (
            <button type="button" onClick={remove} disabled={saving}
                    className="text-sm text-rose-600 hover:underline disabled:opacity-50">
              {shared ? `${roleLabel} ro'yxatidan olib tashlash` : "Olib tashlash"}
            </button>
          ) : <span />}
          <button type="button" onClick={save} disabled={saving}
                  className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60">
            {saving ? "Saqlanmoqda..." : "Saqlash"}
          </button>
        </div>
      </div>
    </div>
  );
}
