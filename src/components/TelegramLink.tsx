import { useEffect, useState } from "react";
import { Send, Check, Link2Off, Copy } from "lucide-react";
import { api } from "../lib/api";

/**
 * TELEGRAMNI ULASH (2026-08-15).
 *
 * Xodim o'z profilidan botga bir marta ulanadi. Asoschi uchun bu
 * ayniqsa muhim: kunlik baza zaxirasi fayli va server xatosi
 * ogohlantirishi aynan shu chatga keladi.
 */
interface TgState {
  code?: string | null;
  linked: boolean;
  bot?: string | null;
  bot_link?: string | null;
  ready: boolean;
}

export default function TelegramLink() {
  const [st, setSt] = useState<TgState | null>(null);
  const [copied, setCopied] = useState(false);

  const load = () => {
    api
      .fresh<TgState>("/me/telegram")
      .then(setSt)
      .catch(() => setSt(null));
  };
  useEffect(load, []);

  if (!st || !st.ready) return null;

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`/start ${st.code ?? ""}`);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard yopiq */
    }
  };

  const unlink = async () => {
    if (!confirm("Telegram aloqasi uzilsinmi? Xabarlar to'xtaydi.")) return;
    try {
      await api.delete("/me/telegram");
      load();
    } catch {
      /* jim */
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-5 mb-4">
      <div className="flex items-center gap-2 mb-1">
        <Send size={14} className="text-slate-400" />
        <h2 className="text-sm font-semibold text-slate-800">Telegram</h2>
        {st.linked && (
          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
            <Check size={11} /> ulangan
          </span>
        )}
      </div>

      {st.linked ? (
        <>
          <p className="text-sm text-slate-600">
            Tizim xabarlari Telegramingizga kelib turadi.
          </p>
          <button
            onClick={unlink}
            className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            <Link2Off size={13} /> Aloqani uzish
          </button>
        </>
      ) : (
        <>
          <p className="text-sm text-slate-600">
            Ulasangiz muhim xabarlar Telegramingizga keladi: kunlik baza
            zaxirasi va server xatosi haqida ogohlantirish.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            {st.bot_link && (
              <a
                href={st.bot_link}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700"
              >
                <Send size={14} /> Telegramda ochish
              </a>
            )}
            <code className="rounded-lg bg-slate-100 px-3 py-2 text-sm font-mono text-slate-800">
              /start {st.code}
            </code>
            <button
              onClick={copy}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
            >
              <Copy size={13} /> {copied ? "Nusxalandi" : "Nusxalash"}
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-400">
            Tugma ishlamasa: {st.bot ? `@${st.bot}` : "botni"} oching va
            yuqoridagi matnni yuboring.
          </p>
        </>
      )}
    </div>
  );
}
