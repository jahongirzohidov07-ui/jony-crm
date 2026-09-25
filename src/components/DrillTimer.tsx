import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { Check, SkipForward, Timer, X } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

/**
 * MASHQ SEKUNDOMERI — butun tizim bo'ylab (2026-09-25).
 *
 * Jahongir: "har safar chiqib ketganda sekundomer o'chib qolyabdi".
 *
 * SABAB. Vazifa boshqa bo'limda bajariladi (lid qo'shish, to'lov
 * kiritish...), Mashq sahifasidan chiqilishi bilan esa sekundomer
 * ko'rinmay qolardi. Vaqtning O'ZI server tomonda sanalardi, ya'ni
 * hisob to'g'ri edi — lekin admin qancha vaqti qolganini ko'rmasdi
 * va har safar orqaga qaytishga majbur edi.
 *
 * ENDI: mashq ketayotgan bo'lsa, ekranning pastki o'ng burchagida
 * kichik oyna osilib turadi — qaysi vazifa, qancha vaqt qolgani va
 * "Bajardim" tugmasi. Ya'ni Mashq sahifasiga qaytish shart emas.
 *
 * Qoldiq vaqt HAR SAFAR serverdan olinadi (10 soniyada bir), oradagi
 * soniyalar esa mahalliy sanaladi — brauzer soati aldasa ham hisob
 * serverniki bo'lib qolaveradi.
 */
type Cur = {
  id: number;
  order_no: number;
  title: string;
  hint: string | null;
  seconds: number;
  verify_kind: string;
};

type State = {
  current: Cur | null;
  left: number | null;
  attempt: { total: number } | null;
  ok?: boolean;
  message?: string;
};

// Mashq topshira oladigan lavozimlar (api/roles.py: DRILL_TAKE).
// Ro'yxatda bo'lmagan xodimga umuman so'rov yuborilmaydi.
const TAKERS = [
  "administrator", "founder", "branch_manager", "sales_head",
  "sales_manager", "academic_head", "hr_manager",
];

// Har sahifa almashganda so'rov yubormaslik uchun: mashq ketmayotgan
// bo'lsa daqiqada bir marta tekshiriladi.
let lastCheck = 0;
let lastRunning = false;

function mmss(sec: number) {
  const s = Math.max(0, Math.round(sec));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export function DrillTimer() {
  const { user } = useAuth();
  const { pathname } = useLocation();
  const [d, setD] = useState<State | null>(null);
  const [left, setLeft] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [closed, setClosed] = useState(false);

  const mayTake = !!user && TAKERS.includes(user.role);

  const load = useCallback((force = false) => {
    if (!mayTake) return;
    const now = Date.now();
    if (!force && !lastRunning && now - lastCheck < 60000) return;
    lastCheck = now;
    api
      .fresh<State>("/drill/state")
      .then((r) => {
        lastRunning = !!r.current;
        setD(r);
        setLeft(r.left);
      })
      .catch(() => setD(null));
  }, [mayTake]);

  useEffect(() => {
    load();
  }, [load, pathname]);

  // Har 10 soniyada server bilan tekislanadi
  useEffect(() => {
    if (!d?.current) return;
    const t = setInterval(() => load(true), 10000);
    return () => clearInterval(t);
  }, [d?.current?.id, load]);

  // Oradagi soniyalar
  useEffect(() => {
    if (left == null || !d?.current) return;
    const t = setInterval(() => setLeft((v) => (v == null ? v : v - 1)), 1000);
    return () => clearInterval(t);
  }, [d?.current?.id, left == null]);

  // Mashq sahifasining o'zida ikkinchi sekundomer kerak emas
  if (!mayTake || closed) return null;
  if (pathname.startsWith("/mashq") || pathname.startsWith("/development"))
    return null;
  if (!d?.current || !d.attempt) return null;

  const act = async (skip: boolean) => {
    setBusy(true);
    setMsg("");
    try {
      const r = await api.post<State>("/drill/done", { skip });
      setD(r);
      setLeft(r.left);
      if (r.ok === false && r.message) setMsg(r.message);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  const over = (left ?? 0) < 0;

  return (
    <div className="fixed bottom-4 right-4 z-50 w-[270px] bg-white border border-slate-200 rounded-xl shadow-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <Timer size={14} className="text-slate-400" />
        <span className="text-xs text-slate-500">
          Mashq · {d.current.order_no}/{d.attempt.total}
        </span>
        <span
          className={`ml-auto text-lg font-semibold tabular-nums ${
            over ? "text-rose-600" : "text-slate-900"
          }`}
        >
          {over ? "+" : ""}
          {mmss(Math.abs(left ?? 0))}
        </span>
        <button
          onClick={() => setClosed(true)}
          title="Yopish (mashq to'xtamaydi)"
          className="text-slate-300 hover:text-slate-500"
        >
          <X size={14} />
        </button>
      </div>

      <p className="text-sm font-medium text-slate-900 leading-snug">
        {d.current.title}
      </p>
      {d.current.hint && (
        <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">
          {d.current.hint}
        </p>
      )}

      {msg && <p className="text-[11px] text-rose-600 mt-1.5">{msg}</p>}

      <div className="flex gap-1.5 mt-2.5">
        <button
          disabled={busy}
          onClick={() => act(false)}
          className="flex items-center gap-1 rounded-lg bg-brand-600 text-white text-xs px-3 py-1.5 disabled:opacity-50"
        >
          <Check size={13} /> Bajardim
        </button>
        <button
          disabled={busy}
          onClick={() => act(true)}
          className="flex items-center gap-1 rounded-lg border border-slate-300 text-slate-600 text-xs px-3 py-1.5 disabled:opacity-50"
        >
          <SkipForward size={13} /> Keyingisi
        </button>
      </div>
    </div>
  );
}
