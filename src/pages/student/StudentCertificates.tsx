import { StudentImage } from "../../components/StudentIcon";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Award, Lock } from "lucide-react";
import { formatDate } from "../../lib/format";
import { api } from "../../lib/api";
import { BrandIcon } from "../../components/BrandIcon";

/**
 * JONY STUDENT — SERTIFIKATLAR.
 *
 * 2026-08-21: "Sertifikatlar.png" dizayni bo'yicha to'q temada
 * qayta terildi. Ma'lumot o'zgarmadi: /student/certificates
 * (imtihon natijasi 70%+ bo'lsa chiqadi).
 */

/* eslint-disable @typescript-eslint/no-explicit-any */
type Any = any;

export default function StudentCertificates() {
  const [d, setD] = useState<Any>(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    api
      .get<Any>("/student/certificates")
      .then(setD)
      .catch((e) => setErr(e instanceof Error ? e.message : "Xatolik"));
  }, []);

  const rows: Any[] = d?.rows || [];
  const card = { background: "#0c2258", borderColor: "#35538c" };

  return (
    <div className="max-w-md mx-auto px-4 pt-5 pb-8">
      <div className="flex items-center gap-2.5">
        <Link to="/student/profile"
          className="w-10 h-10 rounded-xl border flex items-center justify-center text-white shrink-0"
          style={card}>
          <ArrowLeft size={18} />
        </Link>
        <span className="text-[15px] font-semibold text-brand-300 flex-1">
          Profil
        </span>
        <StudentImage src="/jsicons/learn-certificate.png" alt="" className="w-12 h-12" />
      </div>

      <h1 className="text-[34px] font-extrabold text-white leading-none mt-3">
        Sertifikatlar
      </h1>
      <p className="text-[15px] text-slate-400 mt-2">
        Yutuqlaringizni tasdiqlang
      </p>

      {err && <p className="text-sm text-red-400 mt-4">{err}</p>}

      {/* ------------------------------------ birinchi sertifikat */}
      {d && rows.length === 0 && (
        <div className="student-panel bg-white rounded-3xl p-5 mt-4 text-center">
          <div className="mx-auto max-w-[300px] rounded-2xl border-[6px] border-slate-200 bg-slate-50 p-5 relative">
            <div className="flex items-center justify-center gap-1.5">
              <BrandIcon size={22} />
              <p className="text-[11px] font-extrabold text-slate-700 leading-tight text-left">
                JONY<br />STUDENT APP
              </p>
            </div>
            <p className="text-[19px] font-extrabold text-slate-800 tracking-[0.18em] mt-2">
              SERTIFIKAT
            </p>
            <p className="text-[11px] font-bold text-slate-500 tracking-wide">
              KELAJAKDAGI DARAJANGIZ
            </p>
            <span className="mx-auto mt-3 w-14 h-14 rounded-full bg-slate-200 flex items-center justify-center">
              <Lock size={22} className="text-slate-400" />
            </span>
            <p className="text-[10px] text-slate-400 mt-3">
              Sana _ _ / _ _ / 20 _ _ · Direktor
            </p>
          </div>
          <p className="text-[19px] font-extrabold text-slate-900 mt-4">
            Birinchi sertifikatingizni oling!
          </p>
          <p className="text-sm text-slate-500 mt-1 leading-relaxed">
            Imtihondan 70% yoki yuqori natija olsangiz sertifikat shu
            yerda ochiladi.
          </p>
          <Link to="/student/games"
            className="inline-block mt-4 px-6 py-3 rounded-2xl bg-brand-600 text-white text-sm font-bold">
            Imtihonga tayyorlanish →
          </Link>
        </div>
      )}

      {/* --------------------------------------------- mavjudlari */}
      <div className="space-y-3 mt-4">
        {rows.map((r) => (
          <div key={r.id} className="bg-white rounded-3xl p-4 flex items-center gap-3">
            <span className="w-14 h-14 rounded-2xl bg-violet-100 flex items-center justify-center shrink-0">
              <Award size={26} className="text-violet-600" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-[16px] font-extrabold text-slate-900 truncate">
                {r.title}
              </p>
              {r.date && (
                <p className="text-xs text-slate-500 mt-0.5">
                  {formatDate(r.date)}
                </p>
              )}
            </div>
            <span className="text-[19px] font-extrabold text-violet-700 shrink-0">
              {r.band != null ? `band ${r.band}` : `${r.percent}%`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
