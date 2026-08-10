import { useEffect, useRef, useState } from "react";
import { Camera, Check, LogOut, Pencil } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/AuthContext";
import {
  fmtNum, TONE_BAR, type SkillsCard, type StudentHome,
} from "../../lib/studentApi";

/** JONY STUDENT — profil: barcha ko'nikmalar to'liq ro'yxati va
 * hisobdan chiqish. */
export default function StudentProfile() {
  const { user, logout } = useAuth();
  const [h, setH] = useState<StudentHome | null>(null);
  const [sk, setSk] = useState<SkillsCard | null>(null);
  /* eslint-disable @typescript-eslint/no-explicit-any */
  const [p, setP] = useState<any>(null); // profil ma'lumotlari
  const [edit, setEdit] = useState(false);
  const [f, setF] = useState<any>({});
  const [saving, setSaving] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadProfile = () =>
    api
      .get<any>("/student/profile")
      .then((r) => {
        setP(r);
        setF({
          first_name: r.first_name || "",
          last_name: r.last_name || "",
          middle_name: r.middle_name || "",
          birth_date: r.birth_date || "",
          address: r.address || "",
          school: r.school || "",
          school_grade: r.school_grade || "",
        });
      })
      .catch(() => {});

  useEffect(() => {
    api.get<StudentHome>("/student/home").then(setH).catch(() => {});
    api.get<SkillsCard>("/student/skills").then(setSk).catch(() => {});
    loadProfile();
  }, []);

  // RASM: telefonda tanlangan surat 512px gacha kichraytirilib
  // (kanvas, JPEG 0.82) data URL bo'lib serverga ketadi - katta
  // fayl bazani shishirmasin.
  function pickPhoto(file: File) {
    const img = new Image();
    img.onload = async () => {
      const side = Math.min(img.width, img.height);
      const sx = (img.width - side) / 2;
      const sy = (img.height - side) / 2;
      const c = document.createElement("canvas");
      const size = Math.min(512, side);
      c.width = size;
      c.height = size;
      c.getContext("2d")!.drawImage(img, sx, sy, side, side, 0, 0, size, size);
      const dataUrl = c.toDataURL("image/jpeg", 0.82);
      try {
        await api.put("/student/photo", { photo: dataUrl });
        loadProfile();
        api.get<StudentHome>("/student/home").then(setH).catch(() => {});
      } catch {
        /* toast */
      }
    };
    img.src = URL.createObjectURL(file);
  }

  async function saveProfile() {
    if (saving) return;
    setSaving(true);
    try {
      await api.put("/student/profile", {
        first_name: f.first_name,
        last_name: f.last_name,
        middle_name: f.middle_name || null,
        birth_date: f.birth_date || null,
        address: f.address || null,
        school: f.school || null,
        school_grade: f.school_grade || null,
      });
      setEdit(false);
      loadProfile();
      api.get<StudentHome>("/student/home").then(setH).catch(() => {});
    } catch {
      /* xato toast'da ko'rinadi */
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="bg-gradient-to-br from-brand-700 to-brand-500 text-white px-4 pt-8 pb-12">
        <div className="max-w-md mx-auto flex items-center gap-3">
          <button
            onClick={() => fileRef.current?.click()}
            className="relative w-16 h-16 rounded-full bg-white/20 border-2 border-white/40 overflow-hidden flex items-center justify-center shrink-0"
            aria-label="Rasm qo'yish"
          >
            {p?.photo ? (
              <img src={p.photo} alt="" className="w-full h-full object-cover" />
            ) : (
              <span className="text-2xl font-bold">
                {(h?.name || user?.full_name || "?").charAt(0)}
              </span>
            )}
            <span className="absolute bottom-0 inset-x-0 bg-black/45 py-0.5 flex justify-center">
              <Camera size={11} />
            </span>
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) pickPhoto(file);
              e.target.value = "";
            }}
          />
          <div className="min-w-0">
            <h1 className="text-lg font-semibold truncate">
              {h?.name || user?.full_name}
            </h1>
            <p className="text-sm opacity-90">
              {h?.group || "guruh biriktirilmagan"}
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 space-y-4">
        {/* SHAXSIY MA'LUMOTLAR (2026-08-10): faqat ism, familiya,
            otasining ismi alohida maydonlarda - boshqa narsa yozib
            bo'lmaydi (server ham tekshiradi). To'ldirilgani xodimlar
            bazasida darhol ko'rinadi. */}
        {p && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-slate-800">
                Shaxsiy ma'lumotlar
              </p>
              {!edit && (
                <button
                  onClick={() => setEdit(true)}
                  className="flex items-center gap-1 text-xs font-medium text-brand-600"
                >
                  <Pencil size={12} />
                  O'zgartirish
                </button>
              )}
            </div>

            {!edit ? (
              <>
                <Row label="Familiya" value={p.last_name || "—"} />
                <Row label="Ism" value={p.first_name || "—"} />
                <Row label="Otasining ismi" value={p.middle_name || "—"} />
                <Row label="Tug'ilgan sana" value={p.birth_date || "—"} />
                <Row label="Maktab" value={p.school || "—"} />
                <Row label="Sinf" value={p.school_grade || "—"} />
                <Row label="Manzil" value={p.address || "—"} />
                <Row label="Login (raqam)" value={p.phone || "—"} />
              </>
            ) : (
              <div className="space-y-3">
                {[
                  ["last_name", "Familiya *", "Valiyev"],
                  ["first_name", "Ism *", "Ali"],
                  ["middle_name", "Otasining ismi", "Anvarovich"],
                ].map(([k, lbl, ph]) => (
                  <div key={k}>
                    <label className="block text-[11px] text-slate-500 mb-1">
                      {lbl}
                    </label>
                    <input
                      value={f[k] || ""}
                      onChange={(e) =>
                        setF({ ...f, [k]: e.target.value })
                      }
                      placeholder={ph}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                    />
                  </div>
                ))}
                <p className="text-[11px] text-slate-400 -mt-1">
                  Faqat harflar - bitta so'zdan. Laqab yoki boshqa
                  narsa yozib bo'lmaydi.
                </p>
                <div>
                  <label className="block text-[11px] text-slate-500 mb-1">
                    Tug'ilgan sana
                  </label>
                  <input
                    type="date"
                    value={f.birth_date || ""}
                    onChange={(e) =>
                      setF({ ...f, birth_date: e.target.value })
                    }
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm bg-white"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[11px] text-slate-500 mb-1">
                      Maktab
                    </label>
                    <input
                      value={f.school || ""}
                      onChange={(e) =>
                        setF({ ...f, school: e.target.value })
                      }
                      placeholder="21-maktab"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-slate-500 mb-1">
                      Sinf
                    </label>
                    <input
                      value={f.school_grade || ""}
                      onChange={(e) =>
                        setF({ ...f, school_grade: e.target.value })
                      }
                      placeholder="9-A"
                      className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-[11px] text-slate-500 mb-1">
                    Manzil
                  </label>
                  <input
                    value={f.address || ""}
                    onChange={(e) =>
                      setF({ ...f, address: e.target.value })
                    }
                    placeholder="Bekobod, Zafar MFY"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                  />
                </div>
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={saveProfile}
                    disabled={saving || !f.first_name || !f.last_name}
                    className="flex-1 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-semibold flex items-center justify-center gap-1.5 disabled:opacity-40"
                  >
                    <Check size={15} />
                    {saving ? "Saqlanmoqda…" : "Saqlash"}
                  </button>
                  <button
                    onClick={() => {
                      setEdit(false);
                      loadProfile();
                    }}
                    className="flex-1 py-2.5 rounded-xl border border-slate-200 text-slate-600 text-sm font-semibold"
                  >
                    Bekor qilish
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {sk && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-1">
              Barcha bo'limlar
            </p>
            <p className="text-[11px] text-slate-400 mb-4">
              Har {fmtNum(sk.points_per_level)} ball — keyingi daraja
            </p>
            <div className="space-y-4">
              {sk.skills.map((s) => (
                <div key={s.key}>
                  <div className="flex items-baseline justify-between gap-2 mb-1">
                    <span className="text-sm text-slate-700">{s.label}</span>
                    <span className="text-xs font-medium text-slate-800">
                      {s.level.label}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        TONE_BAR[s.tone] || TONE_BAR.slate
                      }`}
                      style={{
                        width: `${s.next ? s.next.progress_percent : 100}%`,
                      }}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    {fmtNum(s.points)} ball
                    {s.max_level
                      ? " · eng yuqori daraja 🎉"
                      : ` · ${s.next!.label} gacha yana ${fmtNum(
                          s.next!.points_left,
                        )}`}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {h && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm font-semibold text-slate-800 mb-3">
              Hisobim
            </p>
            <Row label="Coin" value={fmtNum(h.gamification.coins)} />
            <Row label="Umumiy XP" value={fmtNum(h.gamification.lifetime_xp)} />
            <Row label="Daraja" value={String(h.gamification.level)} />
            {h.gamification.league && (
              <Row
                label="Liga"
                value={`${h.gamification.league.icon} ${h.gamification.league.name}`}
              />
            )}
            <Row label="Ketma-ket kunlar" value={`${h.streak} kun`} />
            {h.ranks.branch_rank && (
              <Row
                label="Filialdagi o'rin"
                value={`${h.ranks.branch_rank} / ${h.ranks.branch_total}`}
              />
            )}
          </div>
        )}

        <button
          onClick={logout}
          className="w-full flex items-center justify-center gap-2 py-3 rounded-xl border border-slate-200 bg-white text-slate-600 text-sm font-medium"
        >
          <LogOut size={16} />
          Chiqish
        </button>
      </div>
    </>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm font-medium text-slate-800">{value}</span>
    </div>
  );
}
