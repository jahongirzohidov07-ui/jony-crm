import { useEffect, useState } from "react";
import { Database, Download, ShieldCheck, Send } from "lucide-react";
import { api, getToken } from "../lib/api";
import { formatDateTime } from "../lib/format";

/**
 * ZAXIRA (2026-08-15, Jahongir: "hammasini ozing qil hamma ruxsatni
 * beraman").
 *
 * Bazaning parolini hech kim hech qayerga ko'chirmaydi — zaxirani
 * JonyOS o'zi oladi. Bir bosishda butun baza .zip bo'lib yuklanadi;
 * ichida tiklash yo'riqnomasi va tiklash skripti ham bor.
 *
 * Faqat asoschiga ko'rinadi: faylda markazning BARCHA ma'lumoti bor.
 */

interface Status {
  tables: number;
  telegram_ready: boolean;
  last: { at?: string | null; by?: string | null; note?: string | null } | null;
}

export default function BackupCard() {
  const [st, setSt] = useState<Status | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const load = () => {
    api
      .fresh<Status>("/backup/status")
      .then(setSt)
      .catch(() => setSt(null));
  };
  useEffect(load, []);

  async function download() {
    setBusy(true);
    setMsg("Zaxira tayyorlanmoqda — bir daqiqacha kuting…");
    try {
      const res = await fetch("/api/backup/download", {
        headers: { Authorization: `Bearer ${getToken() ?? ""}` },
      });
      if (!res.ok) throw new Error(`Xatolik: ${res.status}`);
      const blob = await res.blob();
      const cd = res.headers.get("content-disposition") || "";
      const m = cd.match(/filename="([^"]+)"/);
      const name = m?.[1] || "jonyos_zaxira.zip";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = name;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setMsg(
        `Tayyor: ${name} (${Math.round(blob.size / 1024)} KB) yuklandi. ` +
          "Uni ishonchli joyda saqlang."
      );
      load();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Zaxira olishda xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
          <Database size={18} />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold text-slate-900">
            Baza zaxirasi
          </h3>
          <p className="mt-1 text-sm text-slate-600">
            Butun bazani bitta .zip fayl qilib yuklab oling — o'quvchilar,
            to'lovlar, davomat, xodimlar, hammasi. Ichida tiklash
            yo'riqnomasi (README.txt) va tiklash skripti bor.
          </p>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={download}
              disabled={busy}
              className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
            >
              <Download size={15} />
              {busy ? "Tayyorlanmoqda…" : "Zaxira olish"}
            </button>
            {st && (
              <span className="text-xs text-slate-500">
                {st.tables} ta jadval
              </span>
            )}
          </div>

          {msg && (
            <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700">
              {msg}
            </p>
          )}

          <div className="mt-4 space-y-1.5 border-t border-slate-100 pt-3 text-xs text-slate-500">
            <p className="flex items-start gap-1.5">
              <Send size={13} className="mt-0.5 shrink-0" />
              {st?.telegram_ready ? (
                <span>
                  Har kuni ertalab zaxira asoschining Telegramiga avtomat
                  yuboriladi. Kelmasa — botga <b>/start</b> yozib qo'ying.
                </span>
              ) : (
                <span>
                  Avtomat yuborish uchun Telegram boti sozlanmagan.
                </span>
              )}
            </p>
            <p className="flex items-start gap-1.5">
              <ShieldCheck size={13} className="mt-0.5 shrink-0" />
              Parollar shifrlangan holda saqlanadi — fayldan hech kim asl
              parolni o'qiy olmaydi. Shunga qaramay faylni begonaga
              bermang.
            </p>
            {st?.last?.at && (
              <p className="pt-1">
                Oxirgi zaxira: {formatDateTime(st.last.at)}
                {st.last.by ? ` · ${st.last.by}` : ""}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
