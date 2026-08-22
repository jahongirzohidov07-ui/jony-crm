import { useEffect, useState, useCallback } from "react";
import {
  BarChart3, Plus, Trash2, Pencil, X, Users, ArrowLeft, Eye,
} from "lucide-react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

/**
 * Shaxsiy rivojlanish — boshqaruv va statistika.
 *
 * Faqat asoschi va HR menejer ko'radi (backendda ham shunday
 * cheklangan). Ustoz o'z foizini ko'radi, bu sahifani ko'rmaydi.
 */

type Video = {
  id: number;
  title: string;
  description: string;
  topic: string;
  yt_id: string;
  minutes: number;
  required: boolean;
  active: boolean;
  target_roles: string[];
  watchers: number;
  done_count: number;
  avg_percent: number;
};
type VideoList = {
  items: Video[];
  roles: { key: string; label: string }[];
};
type PersonRow = {
  user_id: number;
  name: string;
  role: string;
  total: number;
  done: number;
  avg_percent: number;
  watched: string;
  last_at: string | null;
};
type People = {
  rows: PersonRow[];
  videos: number;
  avg_percent: number;
  watched_total: string;
};
type WatcherRow = {
  user_id: number;
  name: string;
  role: string;
  percent: number;
  done: boolean;
  opens: number;
  watched: string;
  last_at: string | null;
  started: boolean;
};

const bar = (p: number) =>
  p >= 90 ? "bg-emerald-500" : p >= 40 ? "bg-amber-500" : "bg-slate-300";

export default function DevelopmentAdmin() {
  const [tab, setTab] = useState<"videos" | "people">("videos");
  const [v, setV] = useState<VideoList | null>(null);
  const [p, setP] = useState<People | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [edit, setEdit] = useState<Video | "new" | null>(null);
  const [seeVideo, setSeeVideo] = useState<Video | null>(null);

  const load = useCallback(() => {
    api.get<VideoList>("/pd/videos").then(setV).catch((e) =>
      setError(e instanceof Error ? e.message : "Xatolik"),
    );
    api.get<People>("/pd/people").then(setP).catch(() => {});
  }, []);
  useEffect(load, [load]);

  if (error)
    return <p className="text-sm text-slate-500 py-10 text-center">{error}</p>;
  if (!v) return <p className="text-sm text-slate-400 py-10">Yuklanmoqda…</p>;

  return (
    <div>
      <Link
        to="/development"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 mb-3"
      >
        <ArrowLeft size={15} /> Shaxsiy rivojlanish
      </Link>
      <div className="flex items-center gap-2 mb-1">
        <BarChart3 size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">
          Videolar va ko'rish statistikasi
        </h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Bu sahifani faqat siz va HR menejer ko'radi
      </p>

      {p && (
        <div className="grid grid-cols-3 gap-3 mb-5">
          <Card label="Video" value={String(p.videos)} />
          <Card label="O'rtacha ko'rilgan" value={`${p.avg_percent}%`} />
          <Card label="Jami vaqt" value={p.watched_total} small />
        </div>
      )}

      <div className="flex gap-2 mb-4">
        {(["videos", "people"] as const).map((k) => (
          <button
            key={k}
            onClick={() => setTab(k)}
            className={`px-3 py-1.5 rounded-lg text-sm ${
              tab === k
                ? "bg-brand-600 text-white"
                : "bg-white border border-slate-200 text-slate-600"
            }`}
          >
            {k === "videos" ? "Videolar" : "Xodimlar kesimi"}
          </button>
        ))}
        <button
          onClick={() => setEdit("new")}
          className="ml-auto inline-flex items-center gap-1.5 bg-brand-600 text-white rounded-lg px-3 py-1.5 text-sm font-medium"
        >
          <Plus size={15} /> Video qo'shish
        </button>
      </div>

      {tab === "videos" && (
        <div className="space-y-2">
          {v.items.length === 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-10 text-center">
              <p className="text-sm text-slate-600">Hali video qo'shilmagan</p>
              <p className="text-xs text-slate-400 mt-1">
                YouTube'ga videoni "Yashirin" (Unlisted) qilib yuklang,
                havolasini shu yerga qo'ying
              </p>
            </div>
          )}
          {v.items.map((it) => (
            <div
              key={it.id}
              className="bg-white rounded-xl border border-slate-200 p-3"
            >
              <div className="flex items-start gap-3">
                <img
                  src={`https://i.ytimg.com/vi/${it.yt_id}/mqdefault.jpg`}
                  alt=""
                  className="w-24 h-14 object-cover rounded-lg bg-slate-100 shrink-0"
                />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {it.title}
                    {!it.active && (
                      <span className="ml-2 text-[10px] text-slate-400">
                        o'chirilgan
                      </span>
                    )}
                  </p>
                  <p className="text-xs text-slate-500">
                    {it.topic || "Umumiy"} · {it.minutes} daq
                    {it.required ? " · majburiy" : " · ixtiyoriy"}
                  </p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <div className="h-1.5 flex-1 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${bar(it.avg_percent)}`}
                        style={{ width: `${it.avg_percent}%` }}
                      />
                    </div>
                    <span className="text-[11px] text-slate-500 whitespace-nowrap">
                      o'rtacha {it.avg_percent}% · {it.done_count} kishi
                      ko'rib bo'lgan
                    </span>
                  </div>
                </div>
                <div className="flex flex-col gap-1 shrink-0">
                  <button
                    onClick={() => setSeeVideo(it)}
                    title="Kim ko'rgan"
                    className="p-1.5 text-slate-400 hover:text-brand-600"
                  >
                    <Users size={15} />
                  </button>
                  <button
                    onClick={() => setEdit(it)}
                    className="p-1.5 text-slate-400 hover:text-brand-600"
                  >
                    <Pencil size={15} />
                  </button>
                  <button
                    onClick={async () => {
                      if (!confirm(`"${it.title}" o'chirilsinmi?`)) return;
                      await api.delete(`/pd/videos/${it.id}`);
                      load();
                    }}
                    className="p-1.5 text-slate-400 hover:text-red-600"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "people" && p && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          {p.rows.length === 0 && (
            <p className="p-8 text-center text-sm text-slate-500">
              Hozircha ma'lumot yo'q
            </p>
          )}
          {p.rows.map((r) => (
            <PersonLine key={r.user_id} r={r} />
          ))}
        </div>
      )}

      {edit && (
        <VideoForm
          item={edit === "new" ? null : edit}
          roles={v.roles}
          onClose={() => setEdit(null)}
          onSaved={() => {
            setEdit(null);
            load();
          }}
        />
      )}
      {seeVideo && (
        <WatchersModal video={seeVideo} onClose={() => setSeeVideo(null)} />
      )}
    </div>
  );
}

function Card({
  label,
  value,
  small,
}: {
  label: string;
  value: string;
  small?: boolean;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3">
      <p
        className={`font-semibold text-slate-900 ${
          small ? "text-sm" : "text-xl"
        }`}
      >
        {value}
      </p>
      <p className="text-[11px] text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}

function PersonLine({ r }: { r: PersonRow }) {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState<
    { title: string; percent: number; done: boolean; watched: string }[] | null
  >(null);

  const toggle = () => {
    setOpen(!open);
    if (!rows)
      api
        .get<{
          rows: { title: string; percent: number; done: boolean;
                  watched: string }[];
        }>(`/pd/person/${r.user_id}`)
        .then((d) => setRows(d.rows))
        .catch(() => setRows([]));
  };

  return (
    <div className="border-b border-slate-100 last:border-0">
      <button
        onClick={toggle}
        className="w-full text-left px-4 py-3 flex items-center gap-3"
      >
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-slate-900 truncate">
            {r.name}
          </p>
          <p className="text-xs text-slate-500">
            {r.role} · {r.done}/{r.total} video · {r.watched}
          </p>
        </div>
        <div className="w-24 shrink-0">
          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${bar(r.avg_percent)}`}
              style={{ width: `${r.avg_percent}%` }}
            />
          </div>
          <p className="text-[10px] text-slate-400 text-right mt-0.5">
            {r.avg_percent}%
          </p>
        </div>
      </button>
      {open && (
        <div className="px-4 pb-3 space-y-1.5">
          {rows === null && (
            <p className="text-xs text-slate-400">Yuklanmoqda…</p>
          )}
          {rows?.map((x, i) => (
            <div key={i} className="flex items-center gap-2">
              <span className="text-xs text-slate-600 flex-1 truncate">
                {x.title}
              </span>
              <span className="text-[11px] text-slate-400">{x.watched}</span>
              <span
                className={`text-[11px] w-9 text-right ${
                  x.done ? "text-emerald-600" : "text-slate-500"
                }`}
              >
                {x.percent}%
              </span>
            </div>
          ))}
          {rows?.length === 0 && (
            <p className="text-xs text-slate-400">Video biriktirilmagan</p>
          )}
        </div>
      )}
    </div>
  );
}

function WatchersModal({
  video,
  onClose,
}: {
  video: Video;
  onClose: () => void;
}) {
  const [d, setD] = useState<{
    rows: WatcherRow[];
    started: number;
    done: number;
    total: number;
  } | null>(null);

  useEffect(() => {
    api
      .get<{
        rows: WatcherRow[]; started: number; done: number; total: number;
      }>(`/pd/videos/${video.id}/people`)
      .then(setD)
      .catch(() => setD(null));
  }, [video.id]);

  return (
    <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-end sm:items-center justify-center">
      <div className="bg-white rounded-t-2xl sm:rounded-xl w-full sm:max-w-lg max-h-[85vh] overflow-y-auto">
        <div className="flex items-start gap-3 p-4 border-b border-slate-100 sticky top-0 bg-white">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-slate-900 truncate">
              {video.title}
            </p>
            {d && (
              <p className="text-xs text-slate-500">
                {d.done} kishi ko'rib bo'lgan · {d.started} kishi boshlagan ·
                jami {d.total}
              </p>
            )}
          </div>
          <button onClick={onClose} className="text-slate-400 shrink-0">
            <X size={20} />
          </button>
        </div>
        <div className="p-2">
          {!d && <p className="p-6 text-sm text-slate-400">Yuklanmoqda…</p>}
          {d?.rows.map((r) => (
            <div
              key={r.user_id}
              className="flex items-center gap-3 px-2 py-2.5 border-b border-slate-50 last:border-0"
            >
              <div className="min-w-0 flex-1">
                <p className="text-sm text-slate-900 truncate">{r.name}</p>
                <p className="text-[11px] text-slate-400">
                  {r.role}
                  {r.started
                    ? ` · ${r.watched} · ${r.opens} marta ochgan`
                    : " · boshlamagan"}
                  {r.last_at ? ` · ${r.last_at}` : ""}
                </p>
              </div>
              <div className="w-20 shrink-0">
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${bar(r.percent)}`}
                    style={{ width: `${r.percent}%` }}
                  />
                </div>
                <p className="text-[10px] text-slate-400 text-right mt-0.5">
                  {r.percent}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function VideoForm({
  item,
  roles: roleList,
  onClose,
  onSaved,
}: {
  item: Video | null;
  roles: { key: string; label: string }[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState(item?.title || "");
  const [yt, setYt] = useState(item ? `https://youtu.be/${item.yt_id}` : "");
  const [topic, setTopic] = useState(item?.topic || "");
  const [description, setDescription] = useState(item?.description || "");
  const [required, setRequired] = useState(item?.required ?? true);
  const [target, setTarget] = useState<string[]>(item?.target_roles || []);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const save = async () => {
    setBusy(true);
    setErr(null);
    try {
      const body = {
        title, yt, topic, description, required, target_roles: target,
      };
      if (item) await api.put(`/pd/videos/${item.id}`, body);
      else await api.post("/pd/videos", body);
      onSaved();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/50 z-50 flex items-end sm:items-center justify-center">
      <div className="bg-white rounded-t-2xl sm:rounded-xl w-full sm:max-w-lg max-h-[90vh] overflow-y-auto p-4">
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm font-semibold text-slate-900">
            {item ? "Videoni tahrirlash" : "Yangi video"}
          </p>
          <button onClick={onClose} className="text-slate-400">
            <X size={20} />
          </button>
        </div>

        <label className="block text-xs text-slate-500 mb-1">Nomi</label>
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Masalan: Darsni qanday boshlash kerak"
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-3"
        />

        <label className="block text-xs text-slate-500 mb-1">
          YouTube havolasi
        </label>
        <input
          value={yt}
          onChange={(e) => setYt(e.target.value)}
          placeholder="https://youtu.be/..."
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm"
        />
        <p className="text-[11px] text-slate-400 mt-1 mb-3 flex items-start gap-1">
          <Eye size={12} className="mt-0.5 shrink-0" />
          YouTube'da videoni "Yashirin" (Unlisted) qilib yuklang — qidiruvda
          chiqmaydi, faqat havolasi borlar ko'radi
        </p>

        <label className="block text-xs text-slate-500 mb-1">
          Bo'lim (ixtiyoriy)
        </label>
        <input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Dars metodikasi"
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-3"
        />

        <label className="block text-xs text-slate-500 mb-1">
          Izoh (ixtiyoriy)
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={2}
          className="w-full border border-slate-200 rounded-lg px-3 py-2 text-sm mb-3"
        />

        <label className="block text-xs text-slate-500 mb-1">
          Kimlar uchun (bo'sh qoldirsangiz — hamma xodimga)
        </label>
        <div className="flex flex-wrap gap-1.5 mb-3">
          {roleList.map((r) => {
            const on = target.includes(r.key);
            return (
              <button
                key={r.key}
                onClick={() =>
                  setTarget(
                    on
                      ? target.filter((x) => x !== r.key)
                      : [...target, r.key],
                  )
                }
                className={`px-2 py-1 rounded-md text-[11px] border ${
                  on
                    ? "bg-brand-600 text-white border-brand-600"
                    : "bg-white text-slate-600 border-slate-200"
                }`}
              >
                {r.label}
              </button>
            );
          })}
        </div>

        <label className="flex items-center gap-2 mb-4 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={required}
            onChange={(e) => setRequired(e.target.checked)}
          />
          Majburiy — ko'rish shart
        </label>

        {err && <p className="text-xs text-red-600 mb-2">{err}</p>}
        <button
          disabled={busy || !title.trim() || !yt.trim()}
          onClick={save}
          className="w-full bg-brand-600 text-white rounded-lg py-2.5 text-sm font-medium disabled:opacity-50"
        >
          {busy ? "Saqlanmoqda…" : "Saqlash"}
        </button>
      </div>
    </div>
  );
}
