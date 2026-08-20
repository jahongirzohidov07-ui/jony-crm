import { useEffect, useRef, useState } from "react";
import { Bot, Send, Sparkles, User as UserIcon } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FOUNDER } from "../lib/roles";

/**
 * BIZNES MASLAHATCHI AI — faqat asoschi (2026-08-20).
 *
 * Jahongir: "menga asoschi uchun Biznes maslahatchi AI qoshib ber
 * ichiga mendagi bor malumotlar platformadan kelib chiqib men bilan
 * biznes tahlil qila olsin, chuqur tahlillarga asoslanib menga
 * tavsiyalar bera olsin".
 *
 * Har savolda server platformaning YANGI raqamlarini (tushum,
 * xarajat, o'quvchi oqimi, qarz, lidlar...) AI kontekstiga qo'shadi
 * — maslahatchi taxmin emas, sening haqiqiy raqamlaring bilan
 * gaplashadi. Suhbat tarixi brauzerda turadi, serverda saqlanmaydi.
 */

type Msg = { role: "user" | "assistant"; content: string };

const STARTERS = [
  "Bu oy biznes qanday ketyapti? Qisqa xulosa ber",
  "Qaysi filialga e'tibor berishim kerak?",
  "Qarzdorlikni qanday kamaytiraman?",
  "Kelasi oyga 3 ta ustuvor ishni ayt",
];

export default function Advisor() {
  const { user } = useAuth();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs, busy]);

  if (user?.role !== FOUNDER)
    return (
      <div className="p-8">
        <p className="text-slate-400 text-sm">
          Bu bo'lim faqat asoschi uchun.
        </p>
      </div>
    );

  async function send(q?: string) {
    const t = (q ?? text).trim();
    if (!t || busy) return;
    setErr("");
    setText("");
    const history = msgs;
    setMsgs((m) => [...m, { role: "user", content: t }]);
    setBusy(true);
    try {
      const r = await api.post<{ reply: string }>("/founder/advisor", {
        text: t,
        history,
      });
      setMsgs((m) => [...m, { role: "assistant", content: r.reply }]);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
      // savol yozuvda qolsin - qayta yuborish oson bo'ladi
      setText(t);
      setMsgs((m) => m.slice(0, -1));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="p-8 max-w-3xl flex flex-col" style={{ height: "calc(100vh - 0px)" }}>
      <div className="flex items-center gap-3 mb-1">
        <span className="w-10 h-10 rounded-xl bg-brand-600 text-white flex items-center justify-center">
          <Sparkles size={20} />
        </span>
        <div>
          <h1 className="text-xl font-semibold text-slate-900">
            Biznes maslahatchi
          </h1>
          <p className="text-sm text-slate-500">
            Platformangizdagi jonli raqamlar asosida tahlil va tavsiyalar
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto mt-5 space-y-4 pr-1">
        {msgs.length === 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-5">
            <p className="text-sm text-slate-600 leading-relaxed">
              Salom, Jahongir! Men platformadagi barcha raqamlarni —
              tushum, xarajat, o'quvchilar oqimi, qarzdorlik, lidlar,
              guruhlar to'lganligini ko'rib turaman. Nimani tahlil
              qilamiz?
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              {STARTERS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="text-xs px-3 py-2 rounded-lg border border-brand-200 bg-brand-50 text-brand-700 hover:bg-brand-100 text-left"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {msgs.map((m, i) => (
          <div key={i} className={`flex gap-2.5 ${m.role === "user" ? "justify-end" : ""}`}>
            {m.role === "assistant" && (
              <span className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center shrink-0 mt-0.5">
                <Bot size={15} />
              </span>
            )}
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                m.role === "user"
                  ? "bg-brand-600 text-white"
                  : "bg-white border border-slate-200 text-slate-800"
              }`}
            >
              {m.content}
            </div>
            {m.role === "user" && (
              <span className="w-8 h-8 rounded-full bg-slate-200 text-slate-500 flex items-center justify-center shrink-0 mt-0.5">
                <UserIcon size={15} />
              </span>
            )}
          </div>
        ))}

        {busy && (
          <div className="flex gap-2.5">
            <span className="w-8 h-8 rounded-full bg-brand-600 text-white flex items-center justify-center shrink-0">
              <Bot size={15} />
            </span>
            <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 text-sm text-slate-400">
              Raqamlarni tahlil qilyapman…
            </div>
          </div>
        )}
        {err && <p className="text-sm text-red-600">{err}</p>}
        <div ref={endRef} />
      </div>

      <div className="mt-4 flex gap-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Savolingizni yozing…"
          className="flex-1 rounded-xl border border-slate-300 px-4 py-3 text-sm bg-white"
        />
        <button
          onClick={() => send()}
          disabled={busy || !text.trim()}
          className="bg-brand-600 hover:bg-brand-700 text-white rounded-xl px-4 disabled:opacity-40"
        >
          <Send size={17} />
        </button>
      </div>
      <p className="text-[11px] text-slate-400 mt-2">
        Maslahatchi javoblari tavsiya xarakterida — yakuniy qaror sizniki.
      </p>
    </div>
  );
}
