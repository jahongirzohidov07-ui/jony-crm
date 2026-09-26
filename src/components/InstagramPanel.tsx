import { useCallback, useEffect, useState } from "react";
import { RefreshCw, ExternalLink, Link2, X } from "lucide-react";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * INSTAGRAM (2026-09-26). Jahongir: "instagramni ulaylik unda avtomat
 * ko'rinishi kerak, telegramdan kora bizga instagram muhim".
 *
 * Tokenni ASOSCHI O'ZI joylaydi — JonyOS uni hech qachon to'liq
 * ko'rsatmaydi. Joylangach har kuni avtomat yangilanadi; har post
 * kontent-plandagi postga bog'lanadi (bo'lmasa rejaga o'zi qo'shiladi).
 */
export function InstagramPanel() {
  const [d, setD] = useState<Any>(null);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    api.get<Any>("/smm/instagram").then(setD).catch(() => setD(null));
  }, []);
  useEffect(load, [load]);

  const connect = async () => {
    setErr(""); setMsg(""); setBusy("connect");
    try {
      const r = await api.post<Any>("/smm/instagram/token", { token });
      setToken("");
      setMsg(`@${r.username} ulandi. ${r.sync?.note || ""}`);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(null); }
  };

  const syncNow = async () => {
    setErr(""); setMsg(""); setBusy("sync");
    try {
      const r = await api.post<Any>("/smm/instagram/sync", {});
      if (r.ok) setMsg(r.note); else setErr(r.note);
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(null); }
  };

  const disconnect = async () => {
    if (!confirm("Instagram uzilsinmi? Yig'ilgan raqamlar o'chmaydi.")) return;
    setBusy("off");
    try {
      await api.post("/smm/instagram/disconnect", {});
      load();
    } finally { setBusy(null); }
  };

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const posts: Any[] = d.posts || [];
  const n = (v: number) => (v || 0).toLocaleString("ru-RU");

  return (
    <div className="space-y-4">
      {msg && (
        <div className="px-3 py-2 rounded-lg bg-emerald-50 border border-emerald-200 text-[13px] text-emerald-800 flex gap-2">
          <span className="flex-1">{msg}</span>
          <button onClick={() => setMsg("")}><X size={14} /></button>
        </div>
      )}
      {err && (
        <div className="px-3 py-2 rounded-lg bg-red-50 border border-red-200 text-[13px] text-red-700 flex gap-2">
          <span className="flex-1">{err}</span>
          <button onClick={() => setErr("")}><X size={14} /></button>
        </div>
      )}

      {!d.connected ? (
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-3">
          <h3 className="font-semibold text-slate-900">Instagram ulanmagan</h3>
          <p className="text-sm text-slate-600">
            Ulangach har bir post va reels bo'yicha ko'rishlar, qamrov, like,
            izoh, saqlash, ulashish, <b>shu postdan kelgan obunachilar</b> va
            profilga o'tishlar har kuni o'zi yig'iladi.
          </p>
          <ol className="text-[13px] text-slate-600 list-decimal pl-5 space-y-1">
            <li>Instagram akkaunt <b>Professional</b> (Business) bo'lsin va
              Facebook sahifaga ulangan bo'lsin.</li>
            <li><b>developers.facebook.com → Tools → Graph API Explorer</b> ni
              oching, ilovangizni tanlang.</li>
            <li>Ruxsatlar: <code>instagram_basic</code>,{" "}
              <code>instagram_manage_insights</code>,{" "}
              <code>pages_show_list</code>,{" "}
              <code>pages_read_engagement</code> → <b>Generate Access Token</b>.</li>
            <li>Tokenni uzoq muddatliga (60 kun) aylantirib, shu yerga
              joylang. Akkaunt raqamini JonyOS o'zi topadi.</li>
          </ol>
          {d.can_set_token ? (
            <div className="flex flex-wrap gap-2">
              <input
                type="password"
                autoComplete="off"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                placeholder="Access token (EAA… yoki IG…)"
                className="flex-1 min-w-[260px] rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <button
                onClick={connect}
                disabled={busy !== null || token.trim().length < 20}
                className="px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-40"
              >
                {busy === "connect" ? "Tekshirilmoqda…" : "Ulash"}
              </button>
            </div>
          ) : (
            <p className="text-[13px] text-amber-700">
              Tokenni asoschi yoki SMM menejer joylaydi.
            </p>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white p-4 flex flex-wrap items-center gap-3">
          <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-xs font-medium">
            Ulangan
          </span>
          <span className="text-sm font-medium text-slate-800">
            @{d.username || d.account_id}
          </span>
          <span className="text-xs text-slate-400">token {d.token}</span>
          <span className="text-xs text-slate-500">
            {d.last_sync
              ? `Oxirgi yangilanish: ${formatDate(d.last_sync.slice(0, 10))} ${d.last_sync.slice(11, 16)}`
              : "Hali yangilanmagan"}
          </span>
          <div className="flex-1" />
          <button onClick={syncNow} disabled={busy !== null}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm font-medium disabled:opacity-40">
            <RefreshCw size={14} className={busy === "sync" ? "animate-spin" : ""} />
            Hozir yangilash
          </button>
          {d.can_set_token && !d.from_env && (
            <button onClick={disconnect} disabled={busy !== null}
              className="px-3 py-1.5 rounded-lg border border-slate-300 text-sm text-slate-600">
              Uzish
            </button>
          )}
          {d.last_note && (
            <p className="w-full text-[12px] text-slate-500">{d.last_note}</p>
          )}
        </div>
      )}

      {posts.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white overflow-x-auto">
          <table className="w-full text-[13px]">
            <thead className="bg-slate-50 text-slate-500 text-[11px] uppercase">
              <tr>
                <th className="text-left px-3 py-2">Sana</th>
                <th className="text-left px-3 py-2">Post</th>
                <th className="text-right px-2 py-2">Ko'rish</th>
                <th className="text-right px-2 py-2">Qamrov</th>
                <th className="text-right px-2 py-2">Like</th>
                <th className="text-right px-2 py-2">Izoh</th>
                <th className="text-right px-2 py-2">Saqlash</th>
                <th className="text-right px-2 py-2">Ulashish</th>
                <th className="text-right px-2 py-2">Obuna</th>
                <th className="text-right px-2 py-2">Profilga</th>
                <th className="text-right px-2 py-2">Lid</th>
                <th className="text-right px-2 py-2">Sotuv</th>
                <th className="text-right px-2 py-2">Tushum</th>
                <th className="text-left px-3 py-2">Rejadagi post</th>
              </tr>
            </thead>
            <tbody>
              {posts.map((p) => (
                <tr key={p.id} className="border-t border-slate-100">
                  <td className="px-3 py-2 whitespace-nowrap text-slate-500">
                    {p.posted_at ? formatDate(p.posted_at.slice(0, 10)) : "—"}
                  </td>
                  <td className="px-3 py-2 max-w-[260px]">
                    <a href={p.permalink} target="_blank" rel="noreferrer"
                      className="inline-flex items-center gap-1 text-slate-800 hover:text-brand-700">
                      <span className="truncate">{p.caption || p.type}</span>
                      <ExternalLink size={11} className="shrink-0" />
                    </a>
                  </td>
                  <td className="px-2 py-2 text-right font-medium">{n(p.views)}</td>
                  <td className="px-2 py-2 text-right">{n(p.reach)}</td>
                  <td className="px-2 py-2 text-right">{n(p.likes)}</td>
                  <td className="px-2 py-2 text-right">{n(p.comments)}</td>
                  <td className="px-2 py-2 text-right">{n(p.saves)}</td>
                  <td className="px-2 py-2 text-right">{n(p.shares)}</td>
                  <td className="px-2 py-2 text-right text-emerald-700 font-medium">
                    {p.follows ? `+${n(p.follows)}` : "0"}
                  </td>
                  <td className="px-2 py-2 text-right">{n(p.profile_visits)}</td>
                  <td className="px-2 py-2 text-right font-medium">{p.leads || "—"}</td>
                  <td className="px-2 py-2 text-right font-semibold text-brand-700">
                    {p.sales || "—"}
                  </td>
                  <td className="px-2 py-2 text-right">
                    {p.revenue ? n(Math.round(p.revenue)) : "—"}
                  </td>
                  <td className="px-3 py-2 text-[12px]">
                    {p.content_title ? (
                      <span className="inline-flex items-center gap-1 text-slate-700">
                        <Link2 size={11} /> {p.content_title}
                        <span className="text-slate-400">({p.link_note})</span>
                      </span>
                    ) : <span className="text-slate-400">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
