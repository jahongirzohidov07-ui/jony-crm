import { useEffect, useState } from "react";
import { Shield, RotateCcw, Check, Lock, Info } from "lucide-react";
import { api, type PermMatrix } from "../lib/api";
import { useAuth } from "../lib/AuthContext";
import { PERMISSION_ADMIN, can } from "../lib/roles";

const ACTION_TONE: Record<string, string> = {
  view: "bg-slate-500",
  create: "bg-sky-500",
  edit: "bg-teal-500",
  delete: "bg-red-500",
  approve: "bg-violet-500",
  export: "bg-amber-500",
  secret: "bg-rose-600",
};

/**
 * Ruxsatlar matritsasi. Har bir ROL uchun har bir BO'LIMDA nima qila
 * olishi shu yerda belgilanadi. Faqat asoschi o'zgartira oladi.
 */
export default function Permissions() {
  const { user } = useAuth();
  const [data, setData] = useState<PermMatrix | null>(null);
  const [role, setRole] = useState<string>("");
  const [saving, setSaving] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(true);

  function load() {
    setLoading(true);
    api
      .get<PermMatrix>("/permissions")
      .then((d) => {
        setData(d);
        if (!role) setRole(d.roles.find((r) => !r.locked)?.key ?? "");
      })
      .finally(() => setLoading(false));
  }
  useEffect(load, []);

  if (!can(user?.role, PERMISSION_ADMIN)) {
    return (
      <p className="text-sm text-slate-500 py-10 text-center">
        Ruxsatlarni faqat asoschi o'zgartira oladi.
      </p>
    );
  }

  if (loading) return <p className="text-sm text-slate-400 py-8">Yuklanmoqda...</p>;
  if (!data) return null;

  const current = data.roles.find((r) => r.key === role);
  const perms = data.matrix[role] ?? {};
  const changed = data.changed[role] ?? {};

  // Bo'limlarni guruhlab ko'rsatamiz
  const groups: { name: string; rows: typeof data.resources }[] = [];
  for (const r of data.resources) {
    let g = groups.find((x) => x.name === r.group);
    if (!g) {
      g = { name: r.group, rows: [] };
      groups.push(g);
    }
    g.rows.push(r);
  }

  async function toggle(resource: string, action: string, on: boolean) {
    setSaving(`${resource}:${action}`);
    setErr("");
    try {
      await api.put("/permissions", {
        role,
        resource,
        action,
        allowed: on,
      });
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik");
    } finally {
      setSaving("");
    }
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <Shield size={18} className="text-slate-400" />
        <h1 className="text-xl font-semibold text-slate-900">Ruxsatlar</h1>
      </div>
      <p className="text-sm text-slate-500 mb-5">
        Har bir rol qaysi bo'limda nima qila olishini siz belgilaysiz
      </p>

      <TelegramCard />

      {err && (
        <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mb-4">
          {err}
        </p>
      )}

      {/* --- Rol tanlash --- */}
      <div className="space-y-3 mb-5">
        {data.role_groups.map((g) => (
          <div key={g.key}>
            <p className="text-xs text-slate-400 mb-1.5">{g.label}</p>
            <div className="flex flex-wrap gap-1.5">
              {g.roles.map((k) => {
                const r = data.roles.find((x) => x.key === k);
                if (!r) return null;
                const n = Object.keys(data.changed[k] ?? {}).length;
                return (
                  <button
                    key={k}
                    onClick={() => !r.locked && setRole(k)}
                    disabled={r.locked}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                      r.locked
                        ? "bg-slate-50 border-slate-200 text-slate-400 cursor-default"
                        : role === k
                          ? "bg-brand-50 border-brand-400 text-brand-700"
                          : "bg-white border-slate-200 text-slate-600 hover:border-slate-300"
                    }`}
                  >
                    {r.locked && <Lock size={11} />}
                    {r.label}
                    {n > 0 && (
                      <span className="px-1 rounded bg-amber-100 text-amber-700">
                        {n}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {current?.locked && (
        <p className="text-sm text-slate-500 bg-slate-50 rounded-lg px-3 py-2 mb-4">
          Asoschida hamma narsa ochiq va uni o'zgartirib bo'lmaydi — aks
          holda tizimga kirish yo'li yopilib qolardi.
        </p>
      )}

      {current && !current.locked && (
        <>
          <div className="flex items-center gap-2 mb-3">
            <p className="text-sm font-medium text-slate-800">
              {current.label}
            </p>
            {current.external && (
              <span className="px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-500">
                tashqi foydalanuvchi — faqat o'ziga tegishlini ko'radi
              </span>
            )}
            <div className="flex-1" />
            {Object.keys(changed).length > 0 && (
              <button
                onClick={async () => {
                  if (!confirm(`${current.label} standart holatga qaytsinmi?`))
                    return;
                  await api.post("/permissions/reset", { role });
                  load();
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-600 hover:border-slate-300"
              >
                <RotateCcw size={12} /> Standartga qaytarish
              </button>
            )}
          </div>

          <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 sticky top-0">
                <tr className="text-xs text-slate-500">
                  <th className="text-left px-4 py-2.5 min-w-48">Bo'lim</th>
                  {data.actions.map((a) => (
                    <th key={a.key} className="w-24 py-2.5">
                      <div className="flex flex-col items-center gap-1">
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            ACTION_TONE[a.key] || "bg-slate-400"
                          }`}
                        />
                        {a.label}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {groups.map((g) => (
                  <>
                    <tr key={g.name} className="bg-slate-50/60">
                      <td
                        colSpan={data.actions.length + 1}
                        className="px-4 py-1.5 text-xs font-medium text-slate-500"
                      >
                        {g.name}
                      </td>
                    </tr>
                    {g.rows.map((res) => {
                      const has = perms[res.key] ?? [];
                      const edited = changed[res.key] ?? [];
                      return (
                        <tr
                          key={res.key}
                          className="border-t border-slate-100 hover:bg-slate-50/50"
                        >
                          <td className="px-4 py-2">
                            <span className="text-slate-800">{res.label}</span>
                            {edited.length > 0 && (
                              <span className="ml-1.5 text-xs text-amber-600">
                                o'zgartirilgan
                              </span>
                            )}
                          </td>
                          {data.actions.map((a) => {
                            const on = has.includes(a.key);
                            const busy = saving === `${res.key}:${a.key}`;
                            const hint =
                              a.key === "secret" ? res.secret_hint : null;
                            return (
                              <td key={a.key} className="text-center py-2">
                                <button
                                  onClick={() => toggle(res.key, a.key, !on)}
                                  disabled={busy}
                                  title={hint || undefined}
                                  className={`w-7 h-7 rounded-lg border transition inline-flex items-center justify-center ${
                                    on
                                      ? `${
                                          ACTION_TONE[a.key] || "bg-slate-500"
                                        } border-transparent text-white`
                                      : "bg-white border-slate-200 text-transparent hover:border-slate-400"
                                  } ${busy ? "opacity-40" : ""}`}
                                >
                                  <Check size={14} />
                                </button>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-start gap-1.5 mt-3">
            <Info size={13} className="text-slate-400 mt-0.5 shrink-0" />
            <p className="text-xs text-slate-500">
              "Ko'rish"ni yopsangiz — o'sha bo'limdagi qolgan hamma amal ham
              yopiladi. Boshqa amalni bersangiz — "Ko'rish" o'zi ochiladi.
              "Maxfiy maydonlar" — maosh, sof foyda va shunga o'xshash
              narsalar.
            </p>
          </div>
        </>
      )}
    </div>
  );
}

/** Telegram bot holati: sozlangan bo'lsa — @username va nechta
 *  ota-ona ulangani; webhook'ni bir marta shu yerdan ulanadi. */
function TelegramCard() {
  const [d, setD] = useState<{
    enabled: boolean; bot?: string | null; linked?: number; hint?: string;
  } | null>(null);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get<typeof d>("/telegram/status").then((r) => setD(r))
      .catch(() => {});
  }, []);

  const setup = async () => {
    try {
      await api.post("/telegram/setup-webhook", {});
      setMsg("Webhook ulandi ✓ — endi ota-onalar botga yozsa bog'lanadi");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Xatolik");
    }
  };

  if (!d) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 mb-5 max-w-xl">
      <p className="text-sm font-semibold text-slate-800 mb-1">
        Telegram xabarnomalar
      </p>
      {d.enabled ? (
        <>
          <p className="text-sm text-slate-600">
            Bot: <b>@{d.bot || "—"}</b> · ulangan ota-onalar:{" "}
            <b>{d.linked ?? 0}</b>
          </p>
          <p className="text-xs text-slate-400 mt-1">
            O'quvchi kartasidagi kod bilan ota-ona botga /start KOD deb
            yozadi — keyin davomat va to'lov xabarlari boradi.
          </p>
          <button onClick={setup}
            className="mt-2 text-xs px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:border-brand-300">
            Webhook'ni ulash / yangilash
          </button>
        </>
      ) : (
        <p className="text-sm text-slate-500">
          Hozircha o'chiq. Yoqish uchun Vercel'da{" "}
          <code className="bg-slate-100 px-1 rounded">TELEGRAM_BOT_TOKEN</code>{" "}
          o'rnatiladi (@BotFather'dan olinadi) — keyin bu yerda webhook
          ulanadi.
        </p>
      )}
      {msg && <p className="text-xs text-emerald-600 mt-2">{msg}</p>}
    </div>
  );
}
