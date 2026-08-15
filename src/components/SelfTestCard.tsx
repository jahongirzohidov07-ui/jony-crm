import { useEffect, useState } from "react";
import { Stethoscope, Check, X, Loader2, AlertTriangle } from "lucide-react";
import { api } from "../lib/api";

/**
 * TIZIM TEKSHIRUVI (2026-08-15, Jahongir: "men test deb bitta filial
 * ochganman shunda qilib ko'rsa bo'ladi hamma testlarni").
 *
 * Deploy'dan keyin bir bosishda: markazning kundalik zanjiri jonli
 * saytda, TEST FILIALIDA boshdan oxirigacha bosib chiqiladi va
 * tekshiruv o'zidan keyin hamma narsani tozalab ketadi.
 */

interface Check {
  name: string;
  ok: boolean;
  detail?: string;
}
interface Result {
  branch: string;
  passed: number;
  total: number;
  all_ok: boolean;
  seconds: number;
  checks: Check[];
  cleanup: { removed: number; stuck: string[] };
  crash?: string | null;
}
interface Br {
  id: number;
  name: string;
}

export default function SelfTestCard() {
  const [brs, setBrs] = useState<Br[] | null>(null);
  const [hint, setHint] = useState("");
  const [pick, setPick] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [res, setRes] = useState<Result | null>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .fresh<{ branches: Br[]; hint: string }>("/selftest/branches")
      .then((d) => {
        setBrs(d.branches);
        setHint(d.hint);
        if (d.branches.length) setPick(d.branches[0].id);
      })
      .catch(() => setBrs([]));
  }, []);

  async function run() {
    if (!pick) return;
    setBusy(true);
    setErr("");
    setRes(null);
    try {
      setRes(await api.post<Result>(`/selftest?branch_id=${pick}`));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-sky-50 text-sky-600">
          <Stethoscope size={18} />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold text-slate-900">
            Tizim tekshiruvi
          </h3>
          <p className="mt-1 text-sm text-slate-600">
            Markazning kundalik zanjiri — guruh ochish, lid, o'quvchiga
            aylantirish, yo'qlama, to'lov, chegirma, oylik hisob,
            arxiv, muzlatish — jonli saytda bosib chiqiladi. Tekshiruv{" "}
            <b>faqat test filialida</b> ishlaydi va o'zidan keyin
            hamma narsani <b>tozalab ketadi</b>.
          </p>

          {brs && brs.length === 0 ? (
            <p className="mt-3 flex items-start gap-1.5 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
              <AlertTriangle size={13} className="mt-0.5 shrink-0" />
              {hint}
            </p>
          ) : (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <select
                value={pick ?? ""}
                onChange={(e) => setPick(Number(e.target.value))}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
              >
                {(brs ?? []).map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name}
                  </option>
                ))}
              </select>
              <button
                onClick={run}
                disabled={busy || !pick}
                className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
              >
                {busy && <Loader2 size={14} className="animate-spin" />}
                {busy ? "Tekshirilmoqda…" : "Tekshiruvni boshlash"}
              </button>
            </div>
          )}

          {err && (
            <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
              {err}
            </p>
          )}

          {res && (
            <div className="mt-4">
              <div
                className={`rounded-lg px-3 py-2 text-sm font-medium ${
                  res.all_ok
                    ? "bg-emerald-50 text-emerald-800"
                    : "bg-rose-50 text-rose-800"
                }`}
              >
                {res.all_ok
                  ? `Hammasi joyida — ${res.passed}/${res.total} tekshiruv o'tdi (${res.seconds} s)`
                  : `Diqqat: ${res.total - res.passed} ta muammo topildi (${res.passed}/${res.total})`}
              </div>

              <ul className="mt-3 space-y-1">
                {res.checks.map((ch, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-sm text-slate-700"
                  >
                    {ch.ok ? (
                      <Check
                        size={15}
                        className="mt-0.5 shrink-0 text-emerald-600"
                      />
                    ) : (
                      <X size={15} className="mt-0.5 shrink-0 text-rose-600" />
                    )}
                    <span>
                      {ch.name}
                      {ch.detail && (
                        <span className="text-xs text-rose-600">
                          {" "}
                          — {ch.detail}
                        </span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>

              <p className="mt-3 border-t border-slate-100 pt-2 text-xs text-slate-500">
                Tozalash: {res.cleanup.removed} ta sinov yozuvi o'chirildi
                {res.cleanup.stuck.length > 0 && (
                  <span className="text-amber-700">
                    {" "}
                    · qolib ketgani: {res.cleanup.stuck.join(", ")}
                  </span>
                )}
                . Boshqa filiallarga tegilmadi.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
