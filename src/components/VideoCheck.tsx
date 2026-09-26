import { useEffect, useRef, useState } from "react";
import { Film, CheckCircle2, XCircle, HelpCircle } from "lucide-react";
import { api } from "../lib/api";

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

/**
 * VIDEO TEKSHIRUVI (2026-09-26). Jahongir: "videoni yuklaganda tahlil
 * qiladigan funksiya ... oxiridaggi tel raqam qoyilmagan, oxirida logo
 * animation qoshilmagan".
 *
 * Video SERVERGA YUKLANMAYDI: brauzer o'zida ochib davomiylik, o'lcham
 * va 5 ta kichik kadr (boshidan 2, oxirgi 3 soniyadan 3) oladi. Server
 * faqat shu kadrlarni tekshiradi.
 */
function grab(file: File): Promise<Any> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const v = document.createElement("video");
    v.preload = "auto";
    v.muted = true;
    v.playsInline = true;
    v.src = url;
    const frames: Any[] = [];
    const canvas = document.createElement("canvas");
    const done = (x: Any) => { URL.revokeObjectURL(url); resolve(x); };
    v.onerror = () => { URL.revokeObjectURL(url); reject(new Error("Video ochilmadi")); };
    v.onloadedmetadata = async () => {
      const d = v.duration || 0;
      const w = v.videoWidth, h = v.videoHeight;
      const scale = Math.min(1, 480 / Math.max(w, h));
      canvas.width = Math.round(w * scale);
      canvas.height = Math.round(h * scale);
      const ctx = canvas.getContext("2d");
      const times: [number, boolean][] = [
        [Math.min(0.5, d / 4), false], [Math.min(2, d / 2), false],
        [Math.max(0, d - 3), true], [Math.max(0, d - 1.5), true],
        [Math.max(0, d - 0.2), true],
      ];
      for (const [t, end] of times) {
        await new Promise<void>((ok) => {
          const on = () => { v.removeEventListener("seeked", on); ok(); };
          v.addEventListener("seeked", on);
          v.currentTime = t;
        });
        ctx?.drawImage(v, 0, 0, canvas.width, canvas.height);
        frames.push({ t: Math.round(t * 10) / 10, end,
                      data: canvas.toDataURL("image/jpeg", 0.7) });
      }
      done({ duration: Math.round(d * 10) / 10, width: w, height: h, frames });
    };
  });
}

export function VideoCheck({ contentId }: { contentId: number }) {
  const [res, setRes] = useState<Any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const input = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.get<Any>(`/content/${contentId}/video-checks`)
      .then((r) => setRes((r.rows || [])[0] || null)).catch(() => {});
  }, [contentId]);

  const run = async (f: File) => {
    setErr(""); setBusy(true);
    try {
      const meta = await grab(f);
      const r = await api.post<Any>(`/content/${contentId}/video-check`,
        { ...meta, file_name: f.name });
      setRes(r);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally { setBusy(false); }
  };

  return (
    <div className="mt-3 rounded-lg border border-slate-200 p-3">
      <div className="flex flex-wrap items-center gap-2">
        <Film size={14} className="text-slate-400" />
        <span className="text-xs font-medium text-slate-700">Video tekshiruvi</span>
        {res && (
          <span className={`text-[11px] px-2 py-0.5 rounded-full ${
            res.ok ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
            {res.summary}
          </span>
        )}
        <div className="flex-1" />
        <button onClick={() => input.current?.click()} disabled={busy}
          className="px-3 py-1 rounded-lg bg-slate-800 text-white text-xs font-medium disabled:opacity-50">
          {busy ? "Tekshirilmoqda…" : "Videoni tekshirish"}
        </button>
        <input ref={input} type="file" accept="video/*" className="hidden"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) run(f); e.target.value = ""; }} />
      </div>
      {err && <p className="text-xs text-red-600 mt-2">{err}</p>}
      {res && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 mt-2">
          {(res.checks || []).map((c: Any) => (
            <div key={c.key} className="flex items-start gap-1.5 text-[12px]">
              {c.ok === true ? <CheckCircle2 size={13} className="text-emerald-600 mt-0.5 shrink-0" />
                : c.ok === false ? <XCircle size={13} className="text-red-600 mt-0.5 shrink-0" />
                : <HelpCircle size={13} className="text-slate-400 mt-0.5 shrink-0" />}
              <span>
                <span className="text-slate-700">{c.label}</span>
                {c.note && <span className="text-slate-400"> — {c.note}</span>}
              </span>
            </div>
          ))}
          {res.ai_notes && (
            <p className="sm:col-span-2 text-[12px] text-slate-500 mt-1">{res.ai_notes}</p>
          )}
        </div>
      )}
      {!res && !err && (
        <p className="text-[11px] text-slate-400 mt-1">
          Montaj tugagach videoni tanlang: 9:16, sifat, davomiylik, oxirida telefon
          raqam, logo va logo animatsiyasi, subtitr avtomat tekshiriladi. Video
          serverga yuklanmaydi.
        </p>
      )}
    </div>
  );
}
