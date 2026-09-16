import { useEffect, useState } from "react";
import { Ban, Search, X, UserX, AlertTriangle } from "lucide-react";
import { api, type BlacklistHit } from "../lib/api";
import { formatDate } from "../lib/format";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * HR QORA RO'YXATI (2026-09-16, Jahongir: "o'quv markaz qora ro'yxatini
 * shakllantir hr bo'limi uchun, bu bo'limga tushgan nomzodlar boshqa
 * ishga olinmasin").
 *
 * Odam telefon raqami va ism-familiyasi bo'yicha tanib olinadi. Server
 * uni ishga olishning HAMMA yo'lida to'xtatadi (api/blacklist.py) — bu
 * yerda faqat ro'yxat, qo'shish va chiqarish.
 */

const CATEGORIES = [
  { key: "discipline", label: "Intizom buzilishi" },
  { key: "theft", label: "O'g'irlik / moddiy zarar" },
  { key: "fraud", label: "Aldov / soxta hujjat" },
  { key: "conflict", label: "Janjal / hurmatsizlik" },
  { key: "left_bad", label: "Yomon sharoitda ishdan ketgan" },
  { key: "other", label: "Boshqa" },
];

/** Nomzod/xodim yonidagi qizil belgi. */
export function BlacklistBadge({ hit }: { hit?: BlacklistHit | null }) {
  if (!hit) return null;
  return (
    <span
      title={`Qora ro'yxat: ${hit.category_label} — ${hit.reason}`}
      className="ml-1.5 inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-red-600 text-white text-[10px] font-semibold align-middle"
    >
      <Ban size={10} /> Qora ro'yxat
    </span>
  );
}

/** Nomzod kartasidagi ogohlantirish. */
export function BlacklistBanner({ hit }: { hit?: BlacklistHit | null }) {
  if (!hit) return null;
  return (
    <div className="rounded-lg border border-red-300 bg-red-50 px-3 py-2.5 flex gap-2">
      <AlertTriangle size={16} className="text-red-600 shrink-0 mt-0.5" />
      <div className="text-sm">
        <p className="font-semibold text-red-700">
          Qora ro'yxatda — ishga olib bo'lmaydi
        </p>
        <p className="text-red-700">
          {hit.category_label}: {hit.reason}
        </p>
        <p className="text-xs text-red-500 mt-0.5">
          {[hit.added_at && formatDate(hit.added_at), hit.added_by]
            .filter(Boolean).join(" · ")}
        </p>
      </div>
    </div>
  );
}

/** Nomzod yoki xodimni qora ro'yxatga qo'shish oynasi. */
export function AddToBlacklist({
  candidateId, userId, name, onClose, onDone,
}: {
  candidateId?: number;
  userId?: number;
  name: string;
  onClose: () => void;
  onDone: () => void;
}) {
  const [category, setCategory] = useState("discipline");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  async function save() {
    setBusy(true);
    setErr("");
    try {
      await api.post("/hr/blacklist", {
        candidate_id: candidateId, user_id: userId, category,
        reason: reason.trim(),
      });
      onDone();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 bg-slate-900/40 flex items-center justify-center z-[60] px-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-sm p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-900">Qora ro'yxatga qo'shish</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-slate-700 mb-3">
          <b>{name}</b> endi ishga olinmaydi: nomzod sifatida ham, xodim
          sifatida ham.
        </p>
        <label className="block text-xs font-medium text-slate-500 mb-1">Toifa</label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white mb-3"
        >
          {CATEGORIES.map((c) => (
            <option key={c.key} value={c.key}>{c.label}</option>
          ))}
        </select>
        <label className="block text-xs font-medium text-slate-500 mb-1">
          Sabab (majburiy)
        </label>
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          rows={3}
          className="w-full rounded-lg border border-slate-300 px-2.5 py-2 text-sm"
          placeholder="Nima bo'lgani, qachon"
        />
        {err && <p className="text-sm text-red-600 mt-2">{err}</p>}
        <button
          onClick={save}
          disabled={busy || reason.trim().length < 5}
          className="w-full mt-3 bg-red-600 hover:bg-red-700 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-40"
        >
          {busy ? "Saqlanmoqda..." : "Qora ro'yxatga qo'shish"}
        </button>
      </div>
    </div>
  );
}

export function HrBlacklistTab() {
  const [status, setStatus] = useState("active");
  const [q, setQ] = useState("");
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");
  const [f, setF] = useState({
    full_name: "", phone: "", category: "discipline", reason: "",
  });
  const [busy, setBusy] = useState(false);
  const [formErr, setFormErr] = useState("");

  const load = () => {
    setErr("");
    api
      .get<Any>(`/hr/blacklist?status=${status}`, true)
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  };
  useEffect(load, [status]);

  async function add() {
    setBusy(true);
    setFormErr("");
    try {
      await api.post("/hr/blacklist", {
        full_name: f.full_name.trim(),
        phone: f.phone.trim() || null,
        category: f.category,
        reason: f.reason.trim(),
      });
      setF({ full_name: "", phone: "", category: f.category, reason: "" });
      load();
    } catch (e) {
      setFormErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  async function remove(r: Any) {
    const why = prompt(
      `${r.full_name} qora ro'yxatdan chiqarilsinmi?\n\n` +
        "Nega chiqarilayotganini yozing (majburiy):");
    if (why === null) return;
    try {
      await api.post(`/hr/blacklist/${r.id}/remove`, { reason: why.trim() });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  }

  const t = q.trim().toLowerCase();
  const digits = t.replace(/\D/g, "");
  const rows: Any[] = (d?.rows || []).filter((r: Any) =>
    !t ||
    r.full_name.toLowerCase().includes(t) ||
    (digits.length >= 3 && (r.phone || "").replace(/\D/g, "").includes(digits)));

  return (
    <div>
      <div className="flex items-start gap-2 mb-4">
        <UserX size={18} className="text-red-600 mt-0.5" />
        <p className="text-sm text-slate-600">
          Qora ro'yxatdagi odamni ishga olib bo'lmaydi: nomzodni "ishga
          olindi"ga o'tkazish, taklif berish, xodim hisobi yoki ustoz
          akkaunti ochish va bo'shatilgan xodimni qaytarish to'xtatiladi.
          Odam telefon raqami va ism-familiyasi bo'yicha tanib olinadi.
        </p>
      </div>

      {d?.can_manage && (
        <div className="bg-white border border-slate-200 rounded-xl p-4 mb-4">
          <p className="text-sm font-medium text-slate-700 mb-3">Qo'shish</p>
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              value={f.full_name}
              onChange={(e) => setF({ ...f, full_name: e.target.value })}
              placeholder="Familiya Ism"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <input
              value={f.phone}
              onChange={(e) => setF({ ...f, phone: e.target.value })}
              placeholder="Telefon (+998 ...)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <select
              value={f.category}
              onChange={(e) => setF({ ...f, category: e.target.value })}
              className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white"
            >
              {(d.categories || CATEGORIES).map((c: Any) => (
                <option key={c.key} value={c.key}>{c.label}</option>
              ))}
            </select>
            <input
              value={f.reason}
              onChange={(e) => setF({ ...f, reason: e.target.value })}
              placeholder="Sabab (majburiy)"
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          {formErr && <p className="text-sm text-red-600 mt-2">{formErr}</p>}
          <div className="flex flex-wrap items-center gap-3 mt-3">
            <button
              onClick={add}
              disabled={busy || f.full_name.trim().length < 3
                || f.reason.trim().length < 5}
              className="bg-red-600 hover:bg-red-700 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-40"
            >
              Qora ro'yxatga qo'shish
            </button>
            <p className="text-xs text-slate-400">
              Nomzod yoki bo'shatilgan xodimni uning kartasidan ham qo'shish
              mumkin.
            </p>
          </div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <div className="relative">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Ism yoki telefon"
            className="pl-8 pr-3 py-1.5 rounded-lg border border-slate-300 text-sm w-56"
          />
        </div>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm bg-white"
        >
          <option value="active">Qora ro'yxatdagilar</option>
          <option value="removed">Chiqarilganlar</option>
          <option value="all">Hammasi</option>
        </select>
        <span className="text-sm text-slate-500">{rows.length} ta</span>
      </div>

      {err && <p className="text-sm text-red-600 py-4">{err}</p>}
      {!d && !err && <p className="text-sm text-slate-400 py-4">Yuklanmoqda…</p>}

      {d && (
        <div className="bg-white border border-slate-200 rounded-xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-500 text-xs">
              <tr>
                <th className="text-left px-4 py-2.5 font-medium">F.I.Sh.</th>
                <th className="text-left px-3 py-2.5 font-medium">Telefon</th>
                <th className="text-left px-3 py-2.5 font-medium">Sabab</th>
                <th className="text-left px-3 py-2.5 font-medium">Kim, qachon</th>
                <th className="text-left px-3 py-2.5 font-medium">Qayta ariza</th>
                <th className="px-3 py-2.5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {rows.map((r) => (
                <tr key={r.id} className={r.is_active ? "" : "bg-slate-50/60"}>
                  <td className="px-4 py-2.5 font-medium text-slate-900 whitespace-nowrap">
                    {r.full_name}
                    {!r.is_active && (
                      <span className="ml-1.5 text-[10px] font-medium bg-slate-200 text-slate-600 px-1.5 py-0.5 rounded">
                        chiqarilgan
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-slate-600 whitespace-nowrap">
                    {r.phone || "—"}
                  </td>
                  <td className="px-3 py-2.5 text-slate-700 min-w-[200px]">
                    <span className="text-xs font-medium text-red-700">
                      {r.category_label}
                    </span>
                    <p>{r.reason}</p>
                    {!r.is_active && (
                      <p className="text-xs text-slate-500 mt-1">
                        Chiqarildi: {r.remove_reason} ({r.removed_by},{" "}
                        {r.removed_at && formatDate(r.removed_at.slice(0, 10))})
                      </p>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-xs text-slate-500 whitespace-nowrap">
                    {r.added_by || "—"}
                    <br />
                    {r.created_at && formatDate(r.created_at.slice(0, 10))}
                  </td>
                  <td className="px-3 py-2.5 text-xs">
                    {r.applied_again.length ? (
                      <span className="text-amber-700 font-medium">
                        {r.applied_again.length} marta:{" "}
                        {r.applied_again
                          .map((a: Any) => a.created_at
                            ? formatDate(a.created_at.slice(0, 10)) : a.full_name)
                          .join(", ")}
                      </span>
                    ) : (
                      <span className="text-slate-300">—</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right">
                    {d.can_manage && r.is_active && (
                      <button
                        onClick={() => remove(r)}
                        className="text-xs text-slate-500 hover:text-brand-700 underline whitespace-nowrap"
                      >
                        Ro'yxatdan chiqarish
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.length === 0 && (
            <p className="text-sm text-slate-400 py-8 text-center">
              {status === "active" ? "Qora ro'yxat bo'sh." : "Yozuv yo'q."}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
