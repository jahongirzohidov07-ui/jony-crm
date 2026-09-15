import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { formatDateTime } from "../lib/format";

/* IZOHLAR TARIXI (2026-09-15, Jahongir: "lc updaqa yozganlari
   oldingilari bilan saqlanib turadigan qilib bering raqamlar bilan
   ketma ket korinib tursin"). Har izoh alohida saqlanadi, ustidan
   yozilmaydi. O'quvchida muzlatish/faollashtirish ham kim qilgani
   bilan shu ro'yxatda chiqadi. */

export interface CommentRow {
  n: number;
  kind: "comment" | "legacy" | "status";
  source: "student" | "lead";
  id: number | null;
  text: string;
  title?: string;
  action?: string;
  by: string | null;
  date: string | null;
}

export interface CommentList {
  rows: CommentRow[];
  can_write: boolean;
  last_status: { title: string; by: string; date: string | null } | null;
}

const STATUS_TONE: Record<string, string> = {
  freeze: "bg-sky-50 text-sky-700 border-sky-200",
  auto_freeze: "bg-sky-50 text-sky-700 border-sky-200",
  activate: "bg-emerald-50 text-emerald-700 border-emerald-200",
  restore: "bg-emerald-50 text-emerald-700 border-emerald-200",
};

export function CommentThread({
  path,
  canWrite = true,
  placeholder = "Yangi izoh yozing...",
  onAdded,
}: {
  path: string;
  canWrite?: boolean;
  placeholder?: string;
  onAdded?: () => void;
}) {
  const [data, setData] = useState<CommentList | null>(null);
  const [text, setText] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function load() {
    api
      .get<CommentList>(path)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  }
  useEffect(load, [path]);

  async function add() {
    if (!text.trim() || saving) return;
    setSaving(true);
    setError(null);
    try {
      await api.post(path, { text: text.trim() });
      setText("");
      load();
      onAdded?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving(false);
    }
  }

  const rows = data?.rows ?? [];
  const writable = canWrite && (data?.can_write ?? true);

  return (
    <div>
      {!data && !error && <p className="text-sm text-slate-400 py-3">Yuklanmoqda...</p>}
      {data && rows.length === 0 && (
        <p className="text-sm text-slate-400 py-3">Hali izoh yo'q</p>
      )}
      {rows.length > 0 && (
        <ol className="space-y-2 mb-3">
          {rows.map((r) => (
            <li
              key={r.n}
              className={`flex gap-3 rounded-lg border px-3 py-2 ${
                r.kind === "status"
                  ? STATUS_TONE[r.action || ""] || "bg-amber-50 text-amber-800 border-amber-200"
                  : "bg-white border-slate-200"
              }`}
            >
              <span className="shrink-0 w-6 h-6 rounded-full bg-slate-100 text-slate-600 text-xs font-semibold flex items-center justify-center">
                {r.n}
              </span>
              <div className="flex-1 min-w-0">
                {r.kind === "status" && (
                  <p className="text-sm font-medium">{r.title}</p>
                )}
                {r.text && (
                  <p className={`text-sm whitespace-pre-line break-words ${
                    r.kind === "status" ? "opacity-80" : "text-slate-800"
                  }`}>
                    {r.text}
                  </p>
                )}
                <p className="text-xs text-slate-400 mt-0.5">
                  {r.by || (r.kind === "legacy" ? "Oldingi izoh" : "—")}
                  {r.date ? ` · ${formatDateTime(r.date, false)}` : ""}
                  {r.source === "lead" && path.startsWith("/students")
                    ? " · lid paytida" : ""}
                </p>
              </div>
            </li>
          ))}
        </ol>
      )}
      {writable && (
        <div>
          <textarea
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm min-h-[80px]"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) add();
            }}
            placeholder={placeholder}
          />
          <div className="flex items-center gap-3 mt-2">
            <button
              type="button"
              onClick={add}
              disabled={saving || !text.trim()}
              className="bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-60"
            >
              {saving ? "Saqlanmoqda..." : "Izoh qo'shish"}
            </button>
            <span className="text-xs text-slate-400">Oldingi izohlar o'chmaydi</span>
          </div>
        </div>
      )}
      {error && <p className="text-sm text-red-600 mt-2">{error}</p>}
    </div>
  );
}
