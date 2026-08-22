import { useEffect, useState } from "react";
import {
  GraduationCap, Loader2, Trash2, AlertTriangle, Check, Copy,
} from "lucide-react";
import { api } from "../lib/api";

/**
 * MASHQ FILIALI (2026-08-23, Jahongir: "test deb filial ochganman shu
 * filialga 100 kishilik qilib o'quvchilar va adminlar qoshib qoyginda
 * shundan bosib bosib o'rganvolsin adminlar nimani qanday qilishni").
 *
 * Bir tugma — test filialida to'liq kichik markaz paydo bo'ladi:
 * ustozlar, guruhlar, 100 ta o'quvchi (aktiv/sinov/muzlatilgan/arxiv),
 * darslar va yo'qlamalar, to'lovlar (qarzdorlar bilan), lidlar va
 * xodim akkauntlari. Yangi admin shu yerda hech narsadan qo'rqmay
 * bosib ko'radi. Ikkinchi tugma — hammasini tozalaydi.
 */

interface Br { id: number; name: string }
interface Status {
  students: number; groups: number; teachers: number; users: number;
  password: string;
}
interface SeedRes {
  branch: string;
  created: Record<string, number> | number;
  students_total: number;
  password: string;
  logins?: { login: string; role: string }[];
  note?: string;
}

export default function DemoSeedCard() {
  const [brs, setBrs] = useState<Br[] | null>(null);
  const [hint, setHint] = useState("");
  const [pick, setPick] = useState<number | null>(null);
  const [count, setCount] = useState(100);
  const [st, setSt] = useState<Status | null>(null);
  const [busy, setBusy] = useState<"" | "seed" | "clear">("");
  const [res, setRes] = useState<SeedRes | null>(null);
  const [err, setErr] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.fresh<{ branches: Br[]; hint: string }>("/selftest/branches")
      .then((d) => {
        setBrs(d.branches);
        setHint(d.hint);
        if (d.branches.length) setPick(d.branches[0].id);
      })
      .catch(() => setBrs([]));
  }, []);

  useEffect(() => {
    if (!pick) return;
    api.fresh<Status>(`/demo/status?branch_id=${pick}`)
      .then(setSt).catch(() => setSt(null));
  }, [pick, res]);

  async function seed() {
    if (!pick) return;
    setBusy("seed"); setErr(""); setRes(null);
    try {
      setRes(await api.post<SeedRes>("/demo/seed",
        { branch_id: pick, students: count }));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(""); }
  }

  async function clear() {
    if (!pick) return;
    if (!confirm(
      "Mashq ma'lumoti tozalansinmi?\n\n" +
      "Faqat (DEMO) belgili yozuvlar va demo. login'li xodimlar " +
      "o'chiriladi. Haqiqiy ma'lumotga tegilmaydi."
    )) return;
    setBusy("clear"); setErr(""); setRes(null);
    try {
      await api.delete(`/demo/seed?branch_id=${pick}`);
      const s = await api.fresh<Status>(`/demo/status?branch_id=${pick}`);
      setSt(s);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(""); }
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-emerald-50 text-emerald-600">
          <GraduationCap size={18} />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold text-slate-900">
            Mashq filiali — xodimlar o'rgansin
          </h3>
          <p className="mt-1 text-sm text-slate-600">
            Test filialiga haqiqatga o'xshash ma'lumot to'ldiriladi:
            guruhlar, ustozlar, 100 ta o'quvchi (aktiv, sinovda,
            muzlatilgan, qarzdor — aralash), o'tilgan darslar va
            yo'qlamalar, to'lovlar, lidlar va xodim akkauntlari.
            Yangi admin shu yerda hech narsani buzishdan qo'rqmay
            bosib ko'radi. Haqiqiy filialga <b>tegilmaydi</b>.
          </p>

          {brs && brs.length === 0 && (
            <p className="mt-3 flex items-start gap-2 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">
              <AlertTriangle size={16} className="mt-0.5 shrink-0" />
              {hint}
            </p>
          )}

          {brs && brs.length > 0 && (
            <>
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <select
                  value={pick ?? ""}
                  onChange={(e) => setPick(Number(e.target.value))}
                  className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white"
                >
                  {brs.map((b) => (
                    <option key={b.id} value={b.id}>{b.name}</option>
                  ))}
                </select>
                <select
                  value={count}
                  onChange={(e) => setCount(Number(e.target.value))}
                  className="rounded-lg border border-slate-300 px-2.5 py-2 text-sm bg-white"
                >
                  {[25, 50, 100, 200].map((n) => (
                    <option key={n} value={n}>{n} ta o'quvchi</option>
                  ))}
                </select>
                <button
                  onClick={seed}
                  disabled={!!busy}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                >
                  {busy === "seed" && <Loader2 size={14} className="animate-spin" />}
                  To'ldirish
                </button>
                <button
                  onClick={clear}
                  disabled={!!busy}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-600 hover:border-red-300 hover:text-red-700 disabled:opacity-50"
                >
                  {busy === "clear"
                    ? <Loader2 size={14} className="animate-spin" />
                    : <Trash2 size={14} />}
                  Tozalash
                </button>
              </div>

              {st && (
                <p className="mt-2.5 text-xs text-slate-500">
                  Hozir bu filialda: {st.students} o'quvchi · {st.groups} guruh
                  · {st.teachers} ustoz · {st.users} xodim hisobi
                </p>
              )}
            </>
          )}

          {err && (
            <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {err}
            </p>
          )}

          {res && (
            <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/60 p-4">
              <p className="flex items-center gap-1.5 text-sm font-medium text-emerald-800">
                <Check size={15} />
                {res.branch}: jami {res.students_total} ta o'quvchi tayyor
              </p>
              {typeof res.created === "object" && (
                <p className="mt-1 text-xs text-emerald-700">
                  Yaratildi — {Object.entries(res.created)
                    .filter(([, v]) => v > 0)
                    .map(([k, v]) => `${k}: ${v}`).join(" · ")}
                </p>
              )}

              {res.logins && res.logins.length > 0 && (
                <div className="mt-3">
                  <div className="flex items-center gap-2">
                    <p className="text-xs font-medium text-slate-700">
                      Mashq uchun kirish (parol: <b>{res.password}</b>)
                    </p>
                    <button
                      onClick={() => {
                        const txt = res.logins!
                          .map((l) => `${l.login} — ${l.role}`).join("\n")
                          + `\nParol: ${res.password}`;
                        navigator.clipboard?.writeText(txt);
                        setCopied(true);
                        setTimeout(() => setCopied(false), 2000);
                      }}
                      className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[11px] text-slate-600"
                    >
                      <Copy size={11} /> {copied ? "nusxalandi" : "nusxalash"}
                    </button>
                  </div>
                  <ul className="mt-1.5 space-y-0.5">
                    {res.logins.map((l) => (
                      <li key={l.login} className="text-xs text-slate-600">
                        <span className="font-mono text-slate-800">{l.login}</span>
                        {" — "}{l.role}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {res.note && (
                <p className="mt-2.5 text-xs text-slate-500">{res.note}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
