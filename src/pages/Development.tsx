import { useEffect, useRef, useState, useCallback } from "react";
import {
  GraduationCap, Play, CheckCircle2, X, BarChart3, Lock,
} from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { FOUNDER, HR_MANAGER } from "../lib/roles";

/**
 * Shaxsiy rivojlanish — ustoz uchun video kutubxona.
 *
 * Video JonyOS ichida ochiladi. Pleyer har 5 soniyada "hozir nechanchi
 * soniyadaman" deb serverga yozadi, server esa videoni bo'laklarga
 * bo'lib qaysi bo'lak ko'rilganini belgilaydi. Shuning uchun oxiriga
 * tashlab yuborish foizni oshirmaydi.
 *
 * Ustoz o'z foizini ko'radi, boshqa ustozlarnikini ko'rmaydi.
 */

type Item = {
  id: number;
  title: string;
  description: string;
  topic: string;
  yt_id: string;
  duration: number;
  minutes: number;
  required: boolean;
  percent: number;
  done: boolean;
  resume: number;
};
type MyPd = {
  items: Item[];
  topics: string[];
  total: number;
  done: number;
  percent: number;
  me: { name: string; phone: string };
  watched_label: string;
};

// YouTube iframe API — bir marta yuklanadi
let ytReady: Promise<void> | null = null;
function loadYT(): Promise<void> {
  if (ytReady) return ytReady;
  ytReady = new Promise((resolve) => {
    const w = window as unknown as {
      YT?: { Player: unknown };
      onYouTubeIframeAPIReady?: () => void;
    };
    if (w.YT && w.YT.Player) return resolve();
    const prev = w.onYouTubeIframeAPIReady;
    w.onYouTubeIframeAPIReady = () => {
      prev?.();
      resolve();
    };
    const s = document.createElement("script");
    s.src = "https://www.youtube.com/iframe_api";
    document.head.appendChild(s);
  });
  return ytReady;
}

export default function Development() {
  const { user } = useAuth();
  const [d, setD] = useState<MyPd | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<Item | null>(null);

  const load = useCallback(() => {
    api
      .get<MyPd>("/pd/my")
      .then(setD)
      .catch((e) => setError(e instanceof Error ? e.message : "Xatolik"));
  }, []);
  useEffect(load, [load]);

  const canManage = user?.role === FOUNDER || user?.role === HR_MANAGER;

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!d) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  const byTopic = d.topics
    .map((t) => ({
      topic: t,
      rows: d.items.filter((x) => (x.topic || "Umumiy") === t),
    }))
    .filter((g) => g.rows.length > 0);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <GraduationCap size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          Shaxsiy rivojlanish
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Videolarni shu yerda ko'rasiz — ko'rgan qismingiz o'zi belgilanadi
      </p>

      {/* Umumiy holat */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-5">
        <div className="flex items-end justify-between mb-2">
          <div>
            <p className="text-2xl font-semibold text-slate-900">
              {d.done}
              <span className="text-base font-normal text-slate-400">
                {" "}/ {d.total}
              </span>
            </p>
            <p className="text-xs text-slate-500">ko'rib bo'lingan video</p>
          </div>
          <div className="text-right">
            <p className="text-lg font-semibold text-brand-700">
              {d.percent}%
            </p>
            <p className="text-xs text-slate-400">{d.watched_label}</p>
          </div>
        </div>
        <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-brand-500 rounded-full transition-all"
            style={{ width: `${d.percent}%` }}
          />
        </div>
      </div>

      {canManage && (
        <Link
          to="/development/stats"
          className="mb-5 flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 hover:border-brand-300"
        >
          <BarChart3 size={16} className="text-brand-600" />
          Video qo'shish va ko'rish statistikasi
          <span className="ml-auto text-slate-300">→</span>
        </Link>
      )}

      {d.items.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-10 text-center">
          <p className="text-sm text-slate-600">Hozircha video yo'q</p>
          <p className="text-xs text-slate-400 mt-1">
            Video qo'shilganda shu yerda paydo bo'ladi
          </p>
        </div>
      )}

      {byTopic.map((g) => (
        <div key={g.topic} className="mb-6">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">
            {g.topic}
          </p>
          <div className="space-y-2">
            {g.rows.map((it) => (
              <button
                key={it.id}
                onClick={() => setOpen(it)}
                className="w-full text-left bg-white rounded-xl border border-slate-200 p-3 flex items-center gap-3 hover:border-brand-300"
              >
                <div
                  className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                    it.done
                      ? "bg-emerald-50 text-emerald-600"
                      : "bg-brand-50 text-brand-600"
                  }`}
                >
                  {it.done ? <CheckCircle2 size={18} /> : <Play size={16} />}
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {it.title}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="h-1.5 flex-1 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          it.done ? "bg-emerald-500" : "bg-brand-500"
                        }`}
                        style={{ width: `${it.percent}%` }}
                      />
                    </div>
                    <span className="text-[11px] text-slate-400 w-16 text-right">
                      {it.percent}% · {it.minutes} daq
                    </span>
                  </div>
                </div>
                {!it.required && (
                  <span className="text-[10px] text-slate-400 shrink-0">
                    ixtiyoriy
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      ))}

      {open && (
        <PlayerModal
          item={open}
          watermark={`${d.me.name} · ${d.me.phone}`}
          onClose={() => {
            setOpen(null);
            load();
          }}
        />
      )}
    </div>
  );
}

/** Video oynasi: pleyer + suv belgisi + har 5 soniyada holat yozish. */
function PlayerModal({
  item,
  watermark,
  onClose,
}: {
  item: Item;
  watermark: string;
  onClose: () => void;
}) {
  const boxRef = useRef<HTMLDivElement | null>(null);
  const playerRef = useRef<{
    getCurrentTime: () => number;
    getDuration: () => number;
    destroy: () => void;
    seekTo: (s: number) => void;
  } | null>(null);
  const [pct, setPct] = useState(item.percent);
  const [done, setDone] = useState(item.done);
  // Suv belgisi joyi — o'rnini o'zgartirib turadi, kesib tashlab
  // bo'lmasin
  const [wmPos, setWmPos] = useState({ top: "12%", left: "8%" });

  useEffect(() => {
    let timer: number | undefined;
    let mover: number | undefined;
    let alive = true;

    api.post(`/pd/${item.id}/open`, {}).catch(() => {});

    loadYT().then(() => {
      if (!alive || !boxRef.current) return;
      const w = window as unknown as {
        YT: {
          Player: new (
            el: HTMLElement,
            o: Record<string, unknown>,
          ) => typeof playerRef.current;
        };
      };
      playerRef.current = new w.YT.Player(boxRef.current, {
        videoId: item.yt_id,
        playerVars: {
          rel: 0,
          modestbranding: 1,
          disablekb: 1,
          playsinline: 1,
          start: item.resume > 5 ? item.resume - 3 : 0,
        },
      });
    });

    // Har 5 soniyada — qayerdaligini yozamiz
    timer = window.setInterval(() => {
      const p = playerRef.current;
      if (!p || typeof p.getCurrentTime !== "function") return;
      const pos = Math.floor(p.getCurrentTime() || 0);
      const dur = Math.floor(p.getDuration() || 0);
      if (!dur) return;
      api
        .post<{ percent: number; done: boolean }>(`/pd/${item.id}/beat`, {
          pos,
          duration: dur,
        })
        .then((r) => {
          if (!alive) return;
          setPct(r.percent);
          setDone(r.done);
        })
        .catch(() => {});
    }, 5000);

    mover = window.setInterval(() => {
      setWmPos({
        top: `${8 + Math.random() * 70}%`,
        left: `${5 + Math.random() * 60}%`,
      });
    }, 9000);

    const noMenu = (e: Event) => e.preventDefault();
    document.addEventListener("contextmenu", noMenu);

    return () => {
      alive = false;
      if (timer) window.clearInterval(timer);
      if (mover) window.clearInterval(mover);
      document.removeEventListener("contextmenu", noMenu);
      try {
        playerRef.current?.destroy();
      } catch {
        /* pleyer allaqachon yopilgan */
      }
    };
  }, [item.id, item.yt_id, item.resume]);

  return (
    <div className="fixed inset-0 bg-slate-900/70 z-50 flex items-center justify-center p-3">
      <div className="bg-white rounded-xl w-full max-w-3xl overflow-hidden">
        <div className="flex items-start gap-3 p-4 border-b border-slate-100">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-slate-900">
              {item.title}
            </p>
            {item.description && (
              <p className="text-xs text-slate-500 mt-0.5">
                {item.description}
              </p>
            )}
          </div>
          <button onClick={onClose} className="text-slate-400 shrink-0">
            <X size={20} />
          </button>
        </div>

        <div className="relative bg-black" style={{ aspectRatio: "16 / 9" }}>
          <div ref={boxRef} className="w-full h-full" />
          {/* Suv belgisi — bosib bo'lmaydi, faqat ko'rinadi */}
          <div
            className="absolute text-white/35 text-xs font-medium select-none"
            style={{
              ...wmPos,
              pointerEvents: "none",
              textShadow: "0 1px 3px rgba(0,0,0,.6)",
              transition: "top .8s, left .8s",
            }}
          >
            {watermark}
          </div>
        </div>

        <div className="p-4">
          <div className="flex items-center gap-3 mb-2">
            <div className="h-2 flex-1 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  done ? "bg-emerald-500" : "bg-brand-500"
                }`}
                style={{ width: `${pct}%` }}
              />
            </div>
            <span className="text-xs text-slate-500 w-10 text-right">
              {pct}%
            </span>
          </div>
          <p className="text-[11px] text-slate-400 flex items-center gap-1.5">
            <Lock size={11} />
            Ko'rgan qismingiz o'zi belgilanadi. Oldinga tashlab yuborsangiz
            o'sha joy ko'rilgan hisoblanmaydi.
          </p>
        </div>
      </div>
    </div>
  );
}
