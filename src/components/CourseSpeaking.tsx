import { useEffect, useRef, useState } from "react";
import { Mic, Volume2 } from "lucide-react";
import { api } from "../lib/api";

type Message = {role: "teacher" | "student"; text: string};
type Recognition = {lang: string; interimResults: boolean; maxAlternatives: number; onresult: ((event: {results: {isFinal?: boolean; 0: {transcript: string}}[]; resultIndex?: number}) => void) | null; onerror: ((event: {error: string}) => void) | null; onend: (() => void) | null; start(): void; stop(): void; abort(): void};
type SpeechWindow = Window & {SpeechRecognition?: new () => Recognition; webkitSpeechRecognition?: new () => Recognition};
export function CourseSpeaking({lesson, questionId, previous, onSaved}: {lesson: number; questionId: string; previous?: string; onSaved: (answer: string, reply: string) => void}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [heard, setHeard] = useState("");
  const [saved, setSaved] = useState(previous || "");
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState<Message[] | null>(null);
  const recognition = useRef<Recognition | null>(null);
  const active = useRef(true);
  const locked = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => { active.current = true; return () => {
    active.current = false;
    if (timer.current) clearTimeout(timer.current);
    const rec = recognition.current;
    if (rec) { rec.onresult = null; rec.onerror = null; rec.onend = null; try {rec.abort();} catch { /* already stopped */ } }
    window.speechSynthesis?.cancel();
  }; }, []);
  function speak(text: string) {
    if (!window.speechSynthesis || !window.SpeechSynthesisUtterance) {setError("Ovozli o‘qish bu qurilmada mavjud emas. Ustoz javobini ekranda o‘qing."); return;}
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text); utterance.lang = "en-US"; utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  }
  async function turn(history: Message[]) {
    if (locked.current) return;
    locked.current = true; setBusy(true); setError(""); setRetry(null);
    try {
      const result = await api.post<{reply: string; saved: boolean}>("/student/course-practice/speaking", {language: "en", lesson, question_id: questionId, messages: history.slice(-20)});
      if (!active.current) return;
      if (!result.reply?.trim()) throw new Error("Ustoz javobi kelmadi. Qayta urinib ko‘ring.");
      setMessages([...history, {role: "teacher", text: result.reply}]);
      const last = history.at(-1);
      if (result.saved && last?.role === "student") {setSaved(last.text); setHeard(""); onSaved(last.text, result.reply);}
    } catch (e) {if (active.current) {setError(e instanceof Error ? e.message : "Suhbat ulanmayapti. Qayta urinib ko‘ring."); setRetry(history);}}
    finally {locked.current = false; if (active.current) setBusy(false);}
  }
  function startMic() {
    if (listening) {recognition.current?.stop(); return;}
    const SR = (window as SpeechWindow).SpeechRecognition || (window as SpeechWindow).webkitSpeechRecognition;
    if (!SR) {setError("Bu qurilmada ovozni aniqlash mavjud emas. Jony Student ilovasini yangilang yoki shu darsni Chrome brauzerida oching."); return;}
    window.speechSynthesis?.cancel(); setError(""); setHeard("");
    const rec = new SR(); recognition.current = rec;
    rec.lang = "en-US"; rec.interimResults = false; rec.maxAlternatives = 1;
    rec.onresult = event => {
      if (!active.current) return;
      const text = Array.from(event.results).filter(r => r.isFinal !== false).map(r => r[0].transcript).join(" ").trim();
      if (text.length > 1000) {setError("Javob juda uzun. Qisqaroq qilib qayta gapiring."); setHeard("");}
      else setHeard(text);
    };
    rec.onerror = event => {if (!active.current) return; setListening(false); const errors: Record<string,string> = {"not-allowed":"Mikrofonga ruxsat berilmagan. Qurilma sozlamalaridan ruxsat bering.","audio-capture":"Mikrofon topilmadi.","no-speech":"Ovoz eshitilmadi. Qayta gapiring.","network":"Ovozni aniqlash xizmati javob bermadi. Internetni tekshiring."}; if(event.error !== "aborted") setError(errors[event.error] || "Ovozni aniqlab bo‘lmadi. Qayta urinib ko‘ring.");};
    rec.onend = () => {if(timer.current) clearTimeout(timer.current); if(active.current) setListening(false);};
    try {setListening(true); rec.start(); timer.current = setTimeout(() => {try {rec.stop();} catch { /* stopped */ }}, 60000);} catch {setListening(false); setError("Mikrofonni ishga tushirib bo‘lmadi.");}
  }
  return <div className="space-y-3 rounded-xl bg-sky-50 p-4">
    <h4 className="font-bold">Jony Teacher bilan shu dars bo‘yicha gaplashing</h4>
    <p className="text-sm">Ustoz suhbatdoshingiz bo‘ladi. Savolni tinglang, mikrofonga inglizcha javob bering, aniqlangan matnni ko‘rib yuboring.</p>
    {saved && <details><summary className="cursor-pointer text-sm font-semibold">Oxirgi saqlangan og‘zaki javob</summary><p lang="en" className="mt-2 break-words text-sm">{saved}</p></details>}
    {!messages.length && !retry && <button disabled={busy} onClick={() => turn([])} className="rounded-xl bg-sky-800 px-4 py-3 font-semibold text-white disabled:opacity-40">{busy ? "Ustoz tayyorlanmoqda…" : "Ovozli suhbatni boshlash"}</button>}
    <div className="space-y-3" aria-live="polite">{messages.map((message,index) => <div key={index} className={`rounded-xl p-3 text-sm ${message.role === "teacher" ? "bg-white" : "bg-sky-100"}`}><p className="mb-1 font-semibold">{message.role === "teacher" ? "Jony Teacher" : "Siz"}</p><p lang="en" className="whitespace-pre-wrap break-words">{message.text}</p>{message.role === "teacher" && <button aria-label="Ustoz javobini tinglash" onClick={() => speak(message.text)} className="mt-2 inline-flex items-center gap-2 text-sky-800"><Volume2 size={18}/>Tinglash</button>}</div>)}</div>
    {!!messages.length && <>
      <button disabled={busy || !!retry} onClick={startMic} aria-label={listening ? "Mikrofonni to‘xtatish" : "Mikrofonni yoqish"} className={`inline-flex items-center gap-2 rounded-xl px-4 py-3 font-semibold text-white disabled:opacity-40 ${listening ? "bg-red-600" : "bg-sky-800"}`}><Mic size={20}/>{listening ? "Tugatish" : "Gapirish"}</button>
      {heard && <div className="rounded-xl border p-3"><p className="text-xs text-slate-600">Ovozdan aniqlangan matn — xato bo‘lsa qayta gapiring:</p><p lang="en" className="my-2 break-words">{heard}</p><button disabled={busy || listening || !!retry} onClick={() => turn([...messages, {role:"student",text:heard}])} className="rounded-lg bg-sky-800 px-4 py-2 text-white disabled:opacity-40">Javobni yuborish</button></div>}
    </>}
    {busy && <p role="status" className="text-sm">Ustoz javob tayyorlayapti…</p>}
    {error && <p role="alert" className="text-sm text-red-700">{error}</p>}
    {retry && <button disabled={busy} className="underline" onClick={() => turn(retry)}>Qayta urinish</button>}
    <p className="text-xs text-slate-600">AI fikri ovozdan aniqlangan matnga asoslanadi; talaffuz bahosi emas. Javobingiz yuborilgach va ustoz javobi kelgach dars hisobiga saqlanadi.</p>
  </div>;
}
