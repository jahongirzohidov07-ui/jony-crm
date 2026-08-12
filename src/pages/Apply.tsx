import { useState } from "react";
import { BrandIcon } from "../components/BrandIcon";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * OCHIQ ARIZA FORMASI — loginsiz (2026-08-12, Jahongir: "HR
 * nomzodlarga link tashlasa, nomzod to'ldirsa avtomat bazaga
 * yoziladi... to'ldirsa HR bo'limi nomzodlar bo'limiga tushsin").
 * Havola: https://jonyos.uz/apply
 */

const POSITIONS = [
  { key: "sales", label: "Sotuv menejeri" },
  { key: "teacher", label: "Ustoz" },
  { key: "support", label: "Support teacher" },
  { key: "examiner", label: "Examiner" },
  { key: "cleaner", label: "Farrosh" },
  { key: "other", label: "Boshqa ish" },
];
const CERT_NEEDED = ["teacher", "support", "examiner"];

function fileToDataUrl(file: File, maxSide = 900): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith("image/")) {
      // PDF va boshqa hujjatlar — o'z holicha
      const r = new FileReader();
      r.onload = () => resolve(String(r.result));
      r.onerror = reject;
      r.readAsDataURL(file);
      return;
    }
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
      const c = document.createElement("canvas");
      c.width = Math.round(img.width * scale);
      c.height = Math.round(img.height * scale);
      c.getContext("2d")!.drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      resolve(c.toDataURL("image/jpeg", 0.8));
    };
    img.onerror = reject;
    img.src = url;
  });
}

export default function Apply() {
  const [f, setF] = useState<any>({
    full_name: "", address: "", birth_date: "", phone: "",
    workplaces: "", socials: "", education: "", marital: "",
    position: "", other_position: "", subject: "",
    experience_years: "",
  });
  const [photo, setPhoto] = useState("");
  const [cert, setCert] = useState("");
  const [certName, setCertName] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  const set = (k: string, v: any) => setF((p: any) => ({ ...p, [k]: v }));
  const needCert = CERT_NEEDED.includes(f.position);
  const isTeacher = f.position === "teacher";

  async function submit() {
    setErr("");
    if (f.full_name.trim().length < 5) return setErr("F.I.Sh ni to'liq yozing");
    if (f.phone.trim().length < 7) return setErr("Telefon raqamingizni yozing");
    if (!f.position) return setErr("Qaysi lavozimga qiziqayotganingizni tanlang");
    if (!photo) return setErr("Shaxsiy fotosuratingizni yuklang");
    if (needCert && !cert) return setErr("Bu lavozim uchun sertifikat yuklash shart");
    setBusy(true);
    try {
      const res = await fetch("/api/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...f, photo, certificate: cert }),
      });
      const j = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(j.detail || "Xatolik yuz berdi");
      setDone(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Xatolik yuz berdi");
    } finally {
      setBusy(false);
    }
  }

  if (done)
    return (
      <div className="min-h-screen bg-gradient-to-br from-brand-700 to-brand-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <p className="text-4xl mb-3">✅</p>
          <h1 className="text-xl font-bold text-slate-900 mb-2">
            Arizangiz qabul qilindi!
          </h1>
          <p className="text-sm text-slate-600">
            HR bo'limimiz arizangizni ko'rib chiqib, tez orada siz bilan
            bog'lanadi. Rahmat!
          </p>
        </div>
      </div>
    );

  const inp = "w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm";
  const lbl = "block text-xs font-medium text-slate-600 mb-1 mt-3";

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-700 to-brand-500 py-8 px-4">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center gap-2 justify-center mb-4 text-white">
          <BrandIcon size={22} className="rounded-md" />
          <span className="font-semibold">JONY ACADEMY</span>
        </div>
        <div className="bg-white rounded-2xl shadow-xl p-6">
          <h1 className="text-lg font-bold text-slate-900">
            Ishga ariza topshirish
          </h1>
          <p className="text-xs text-slate-500 mb-2">
            Barcha maydonlarni to'ldiring — arizangiz to'g'ridan-to'g'ri
            HR bo'limiga tushadi.
          </p>

          <label className={lbl}>F.I.Sh *</label>
          <input className={inp} value={f.full_name}
                 onChange={(e) => set("full_name", e.target.value)}
                 placeholder="Familiya Ism Sharif" />

          <label className={lbl}>Yashash manzilingiz</label>
          <input className={inp} value={f.address}
                 onChange={(e) => set("address", e.target.value)} />

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={lbl}>Tug'ilgan sanangiz</label>
              <input type="date" className={inp} value={f.birth_date}
                     onChange={(e) => set("birth_date", e.target.value)} />
            </div>
            <div>
              <label className={lbl}>Telefon raqamingiz *</label>
              <input className={inp} value={f.phone}
                     onChange={(e) => set("phone", e.target.value)}
                     placeholder="+998 90 123 45 67" />
            </div>
          </div>

          <label className={lbl}>
            Avvalgi ishlagan joylaringiz (lavozim, qancha vaqt)
          </label>
          <textarea className={inp} rows={3} value={f.workplaces}
                    onChange={(e) => set("workplaces", e.target.value)} />

          <label className={lbl}>Ijtimoiy tarmoqlardagi akkauntlaringiz</label>
          <input className={inp} value={f.socials}
                 onChange={(e) => set("socials", e.target.value)}
                 placeholder="Instagram, Telegram..." />

          <label className={lbl}>
            Ma'lumotingiz (maktab raqami yoki bitirgan joy nomi)
          </label>
          <input className={inp} value={f.education}
                 onChange={(e) => set("education", e.target.value)} />

          <label className={lbl}>Oilaviy holatingiz</label>
          <select className={inp} value={f.marital}
                  onChange={(e) => set("marital", e.target.value)}>
            <option value="">— tanlang —</option>
            <option value="single">Turmush qurmagan</option>
            <option value="married">Oilali</option>
            <option value="divorced">Ajrashgan</option>
          </select>

          <label className={lbl}>Shaxsiy fotosuratingiz *</label>
          <input type="file" accept="image/*" className={inp}
                 onChange={async (e) => {
                   const file = e.target.files?.[0];
                   if (file) setPhoto(await fileToDataUrl(file));
                 }} />
          {photo && (
            <img src={photo} alt="" className="mt-2 w-20 h-20 rounded-xl object-cover border" />
          )}

          <label className={lbl}>Qaysi lavozimga qiziqyapsiz? *</label>
          <select className={inp} value={f.position}
                  onChange={(e) => set("position", e.target.value)}>
            <option value="">— tanlang —</option>
            {POSITIONS.map((p) => (
              <option key={p.key} value={p.key}>{p.label}</option>
            ))}
          </select>
          {f.position === "other" && (
            <input className={inp + " mt-2"} value={f.other_position}
                   onChange={(e) => set("other_position", e.target.value)}
                   placeholder="Qanday ish?" />
          )}

          {isTeacher && (
            <>
              <label className={lbl}>Qancha vaqt ustoz bo'lib ishlagansiz? (yil)</label>
              <input type="number" min="0" step="0.5" className={inp}
                     value={f.experience_years}
                     onChange={(e) => set("experience_years", e.target.value)} />
              <label className={lbl}>Qaysi fandan dars berasiz?</label>
              <input className={inp} value={f.subject}
                     onChange={(e) => set("subject", e.target.value)}
                     placeholder="Ingliz tili, matematika..." />
            </>
          )}

          {needCert && (
            <>
              <label className={lbl}>
                Sertifikatingizni yuklang (IELTS, CEFR va h.k.) *
              </label>
              <input type="file" accept="image/*,.pdf" className={inp}
                     onChange={async (e) => {
                       const file = e.target.files?.[0];
                       if (file) {
                         setCert(await fileToDataUrl(file, 1400));
                         setCertName(file.name);
                       }
                     }} />
              {certName && (
                <p className="text-xs text-emerald-600 mt-1">✓ {certName}</p>
              )}
            </>
          )}

          {err && (
            <p className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 mt-4">
              {err}
            </p>
          )}

          <button disabled={busy} onClick={submit}
                  className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-xl py-3 text-sm font-semibold mt-4 disabled:opacity-50">
            {busy ? "Yuborilmoqda..." : "Arizani yuborish"}
          </button>
        </div>
        <p className="text-center text-xs text-white/70 mt-3">
          JonyOS · Jony Academy
        </p>
      </div>
    </div>
  );
}
