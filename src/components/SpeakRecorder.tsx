import { useCallback, useEffect, useRef, useState } from "react";
import { Mic, Square, RotateCcw } from "lucide-react";
import { JSA } from "./Jsa";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * DIKTAFON — MULTILEVEL SPEAKING UCHUN (2026-08-26).
 *
 * Jahongir: "mikrafonni bosgandan keyin shu sekund avtomat ketsin
 * va sekund tugaganda avtomat o'chsin."
 *
 * Shuning uchun:
 *   - tugma bosilishi bilan sanoq BOSHLANADI (qo'lda start yo'q)
 *   - vaqt tugashi bilan yozuv AVTOMAT to'xtaydi
 *   - qolgan vaqt doira bo'lib ko'rinadi, oxirgi 5 soniya qizil
 * Bu imtihon sharoitini aynan takrorlaydi: u yerda ham mikrofon
 * o'zi o'chadi va gapni tugatishga ulgurish kerak.
 *
 * NUTQ MATNGA IKKI YO'L BILAN AYLANADI:
 *   1) Brauzerning o'z moduli (Chrome/Android) — darhol, bepul.
 *   2) Ishlamasa — audio serverga yuboriladi (Gemini o'giradi).
 * Ikkinchi yo'l iOS Safari uchun kerak, u yerda brauzer nutqni
 * tanimaydi.
 */
type Props = {
  seconds: number;
  onDone: (r: { transcript: string; audio?: string; mime?: string;
                used: number }) => void;
  busy?: boolean;
  label?: string;
};

export default function SpeakRecorder({ seconds, onDone, busy,
                                        label }: Props) {
  const [state, setState] = useState<"idle" | "rec" | "done">("idle");
  const [left, setLeft] = useState(seconds);
  const [live, setLive] = useState("");
  const [err, setErr] = useState("");
  const [url, setUrl] = useState("");

  const mediaRef = useRef<Any>(null);
  const recogRef = useRef<Any>(null);
  const chunks = useRef<Blob[]>([]);
  const timer = useRef<number | null>(null);
  const finalTxt = useRef("");
  const started = useRef(0);
  const stopping = useRef(false);

  useEffect(() => {
    setLeft(seconds);
    setState("idle");
    setLive("");
    setUrl("");
    finalTxt.current = "";
  }, [seconds]);

  const cleanup = useCallback(() => {
    if (timer.current) window.clearInterval(timer.current);
    timer.current = null;
    try { recogRef.current?.stop(); } catch { /* yopilgan */ }
    try {
      const m = mediaRef.current;
      if (m && m.state !== "inactive") m.stop();
      m?.stream?.getTracks?.().forEach((t: Any) => t.stop());
    } catch { /* yopilgan */ }
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const finish = useCallback(() => {
    if (stopping.current) return;
    stopping.current = true;
    const used = Math.max(1, Math.round((Date.now() - started.current) / 1000));
    cleanup();
    setState("done");
    // MediaRecorder onstop asinxron — biroz kutamiz
    window.setTimeout(() => {
      const txt = (finalTxt.current + " " + live).trim();
      const blob = chunks.current.length
        ? new Blob(chunks.current, { type: "audio/webm" })
        : null;
      if (blob) setUrl(URL.createObjectURL(blob));
      if (blob && !txt) {
        // Brauzer nutqni tanimadi — audio serverga ketadi
        const fr = new FileReader();
        fr.onloadend = () => onDone({
          transcript: "", audio: String(fr.result || ""),
          mime: "audio/webm", used });
        fr.readAsDataURL(blob);
      } else {
        onDone({ transcript: txt, used });
      }
      stopping.current = false;
    }, 350);
  }, [cleanup, live, onDone]);

  const start = async () => {
    setErr("");
    setLive("");
    finalTxt.current = "";
    chunks.current = [];
    stopping.current = false;

    // 1) Audio yozuv
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      mr.ondataavailable = (e: Any) => {
        if (e.data?.size) chunks.current.push(e.data);
      };
      mr.start();
      mediaRef.current = mr;
    } catch {
      setErr("Mikrofonga ruxsat berilmadi. Brauzer sozlamalaridan "
             + "mikrofonni yoqing.");
      return;
    }

    // 2) Nutqni tanish (bo'lsa)
    const SR = (window as Any).SpeechRecognition
      || (window as Any).webkitSpeechRecognition;
    if (SR) {
      try {
        const r = new SR();
        r.lang = "en-US";
        r.continuous = true;
        r.interimResults = true;
        r.onresult = (e: Any) => {
          let interim = "";
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const t = e.results[i][0].transcript;
            if (e.results[i].isFinal) finalTxt.current += " " + t;
            else interim += t;
          }
          setLive(interim);
        };
        r.onerror = () => undefined;
        r.start();
        recogRef.current = r;
      } catch { /* audio baribir yoziladi */ }
    }

    started.current = Date.now();
    setState("rec");
    setLeft(seconds);
    timer.current = window.setInterval(() => {
      setLeft((s) => {
        if (s <= 1) {
          window.setTimeout(finish, 0);   // VAQT TUGADI -> AVTOMAT
          return 0;
        }
        return s - 1;
      });
    }, 1000);
  };

  const pct = seconds ? (left / seconds) * 100 : 0;
  const danger = left <= 5 && state === "rec";
  const mm = String(Math.floor(left / 60)).padStart(2, "0");
  const ss = String(left % 60).padStart(2, "0");
  const card = { background: JSA.card, borderColor: JSA.cardBorder };

  return (
    <div className="rounded-2xl border p-4" style={card}>
      {state === "idle" && (
        <>
          <button
            onClick={start}
            disabled={busy}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-4 py-4 text-[15px] font-bold text-white disabled:opacity-40"
          >
            <Mic size={20} />
            {label || `Javob berish (${seconds} soniya)`}
          </button>
          <p className="text-[11px] text-slate-500 mt-2 text-center leading-relaxed">
            Tugmani bosishingiz bilan vaqt ketadi va {seconds} soniyadan
            keyin yozuv o'zi to'xtaydi — imtihondagidek.
          </p>
        </>
      )}

      {state === "rec" && (
        <div className="text-center">
          <div className="relative w-28 h-28 mx-auto">
            <svg viewBox="0 0 100 100" className="w-28 h-28 -rotate-90">
              <circle cx="50" cy="50" r="45" fill="none" strokeWidth="7"
                      stroke="rgba(255,255,255,.10)" />
              <circle
                cx="50" cy="50" r="45" fill="none" strokeWidth="7"
                strokeLinecap="round"
                stroke={danger ? "#FB7185" : "#2B49C8"}
                strokeDasharray={2 * Math.PI * 45}
                strokeDashoffset={2 * Math.PI * 45 * (1 - pct / 100)}
                style={{ transition: "stroke-dashoffset 1s linear" }}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span
                className="text-[24px] font-extrabold tabular-nums"
                style={{ color: danger ? "#FB7185" : "#fff" }}
              >
                {mm}:{ss}
              </span>
              <span className="flex items-center gap-1 text-[10px] text-rose-300 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-pulse" />
                yozilmoqda
              </span>
            </div>
          </div>
          {(finalTxt.current || live) && (
            <p className="text-[12px] text-slate-300 leading-relaxed mt-3 text-left max-h-24 overflow-y-auto">
              {finalTxt.current} <span className="text-slate-500">{live}</span>
            </p>
          )}
          <button
            onClick={finish}
            className="mt-3 inline-flex items-center gap-1.5 rounded-xl border px-4 py-2 text-[13px] font-semibold text-slate-300"
            style={card}
          >
            <Square size={13} /> Erta tugatish
          </button>
        </div>
      )}

      {state === "done" && (
        <div className="text-center">
          {url && (
            <audio controls src={url} className="w-full h-9 mb-2" />
          )}
          <button
            onClick={() => { setState("idle"); setLeft(seconds); }}
            disabled={busy}
            className="inline-flex items-center gap-1.5 rounded-xl border px-4 py-2 text-[13px] font-semibold text-slate-300 disabled:opacity-40"
            style={card}
          >
            <RotateCcw size={13} /> Qayta yozish
          </button>
        </div>
      )}

      {err && <p className="text-[12px] text-rose-300 mt-2">{err}</p>}
    </div>
  );
}
