import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Bot, CheckCircle2, Circle, ExternalLink, RefreshCw, X } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * JONY ACADEMY BOTI (2026-10-13). Railway trial tugab bot o'chdi —
 * endi bot JonyOS ichida (bepul). Asoschi BotFather tokenini shu yerga
 * O'ZI joylaydi; JonyOS uni hech qachon qayta ko'rsatmaydi.
 * Sotuv guruhi va adminlar ID yozmasdan — bitta havolani bosish bilan.
 */
export function AcademyBotPanel() {
  const [d, setD] = useState<Any>(null);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const load = useCallback(() => {
    api.get<Any>("/tg/academy-bot-status").then(setD).catch(() => setD({}));
  }, []);
  useEffect(load, [load]);

  const run = async (key: string, fn: () => Promise<Any>, ok: string) => {
    setErr(""); setMsg(""); setBusy(key);
    try {
      const r = await fn();
      if (r) setD(r);
      setMsg(ok);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(null); }
  };

  const connect = () => run("connect", async () => {
    const r = await api.post<Any>("/tg/academy-bot-connect", { token: token.trim() });
    setToken("");
    return r;
  }, "Bot ulandi va ishlayapti. Endi pastdagi 2 ta havolani bosing.");

  const reconnect = () => run("setup",
    () => api.post<Any>("/tg/academy-bot-setup", {}), "Qayta ulandi.");
  const newCode = () => {
    if (!confirm("Eski havolalar ishlamay qoladi. Davom etilsinmi?")) return;
    run("code", () => api.post<Any>("/tg/academy-bot-new-code", {}),
      "Yangi havolalar tayyor.");
  };

  if (!d) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda…</p>;

  const Step = ({ done, title, children }: { done: boolean; title: string; children?: ReactNode }) => (
    <div className="flex gap-3">
      {done
        ? <CheckCircle2 size={20} className="text-emerald-600 shrink-0 mt-0.5" />
        : <Circle size={20} className="text-slate-300 shrink-0 mt-0.5" />}
      <div className="flex-1 space-y-2">
        <p className={`text-sm font-semibold ${done ? "text-emerald-800" : "text-slate-800"}`}>{title}</p>
        {children}
      </div>
    </div>
  );

  const LinkBtn = ({ href, label }: { href?: string; label: string }) => href ? (
    <a href={href} target="_blank" rel="noreferrer"
      className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#229ED9] text-white text-sm font-semibold">
      <ExternalLink size={14} /> {label}
    </a>
  ) : null;

  return (
    <div className="max-w-2xl space-y-4">
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

      <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5">
        <div className="flex items-center gap-2">
          <Bot size={18} className="text-brand-600" />
          <h3 className="font-semibold text-slate-900 flex-1">
            Jony Academy boti {d.bot ? <span className="text-slate-500 font-normal">@{d.bot}</span> : null}
          </h3>
          {d.enabled && (
            <span className={`text-[12px] px-2 py-0.5 rounded-full ${d.webhook_ok ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>
              {d.webhook_ok ? "Ishlayapti" : "Ulanmagan"}
            </span>
          )}
        </div>

        <Step done={!!d.enabled && !!d.webhook_ok} title="1. Bot tokenini joylang">
          {!d.enabled || !d.webhook_ok ? (
            <>
              <p className="text-[13px] text-slate-600">
                Telegram'da <b>@BotFather</b> → <b>/mybots</b> → botingiz →{" "}
                <b>API Token</b> — chiqqan matnni nusxalab shu yerga qo'ying.
              </p>
              <div className="flex flex-wrap gap-2">
                <input type="password" autoComplete="off" value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="123456789:AAH…"
                  className="flex-1 min-w-[240px] rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                <button onClick={connect} disabled={busy !== null || token.trim().length < 40}
                  className="px-4 py-2 rounded-lg bg-slate-900 text-white text-sm font-medium disabled:opacity-40">
                  {busy === "connect" ? "Ulanmoqda…" : "Ulash"}
                </button>
              </div>
              {d.enabled && (
                <button onClick={reconnect} disabled={busy !== null}
                  className="text-[12px] text-brand-700 inline-flex items-center gap-1">
                  <RefreshCw size={12} /> Token bor — qayta ulash
                </button>
              )}
            </>
          ) : (
            <p className="text-[13px] text-slate-500">
              Ulangan. Jami murojaatlar: <b>{d.regs_total ?? 0}</b>
              {d.pending ? ` · navbatda: ${d.pending}` : ""}
              {d.last_error ? ` · oxirgi xato: ${d.last_error}` : ""}
            </p>
          )}
        </Step>

        <Step done={!!d.sales_group} title="2. Sotuv guruhiga qo'shing">
          {d.group_link ? (
            <>
              <p className="text-[13px] text-slate-600">
                Bosing → arizalar keladigan guruhni tanlang. Bot o'zi
                «guruh ulandi» deb yozadi.
              </p>
              <LinkBtn href={d.group_link} label={d.sales_group ? "Boshqa guruhga ulash" : "Guruhni tanlash"} />
            </>
          ) : <p className="text-[13px] text-slate-400">Avval 1-qadam.</p>}
        </Step>

        <Step done={!!d.sales_group || (d.admins || 0) > 0} title="3. Adminlar">
          {d.admin_link ? (
            <>
              <p className="text-[13px] text-slate-600">
                Sotuv guruhidagi <b>hamma a'zo avtomat admin</b> — botga
                shaxsiy yozib /stat, /royxat, /broadcast ishlata oladi.
                Guruhdan chiqsa huquqi o'zi yo'qoladi. Guruhda bo'lmagan
                odamni admin qilish uchun unga shu havolani yuboring.
              </p>
              <LinkBtn href={d.admin_link} label="Qo'shimcha admin havolasi" />
            </>
          ) : <p className="text-[13px] text-slate-400">Avval 1-qadam.</p>}
        </Step>

        <div className="flex gap-3 pt-1 border-t border-slate-100">
          <button onClick={load} className="text-[12px] text-slate-500 inline-flex items-center gap-1 pt-3">
            <RefreshCw size={12} /> Yangilash
          </button>
          {d.group_link && (
            <button onClick={newCode} disabled={busy !== null}
              className="text-[12px] text-slate-500 pt-3">
              Havolalarni yangilash
            </button>
          )}
        </div>
      </div>
      <p className="text-[12px] text-slate-500">
        Har bir ro'yxatdan o'tgan o'quvchi Lidlarda «telegram» manbasi bilan
        avtomat paydo bo'ladi. Har kuni 20:00 da guruhga hisobot boradi.
      </p>
    </div>
  );
}
