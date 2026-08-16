import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, Award } from "lucide-react";
import { formatDate } from "../../lib/format";
import { api } from "../../lib/api";

/**
 * JONY STUDENT — SERTIFIKATLAR (2026-08-16).
 *
 * Alohida "sertifikat" jadvali ochilmadi: markazda sertifikat
 * imtihon natijasi asosida beriladi, ya'ni ma'lumot allaqachon
 * bazada. Bu yerda faqat kuchli natijalar ko'rsatiladi (band bor
 * yoki 70% dan yuqori) — har unit testi sertifikat emas.
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

  return (
    <>
      <div className="bg-brand-600 text-white px-4 pt-6 pb-12">
        <div className="max-w-md mx-auto">
          <Link
            to="/student/profile"
            className="inline-flex items-center gap-1.5 text-sm text-white/85 mb-3"
          >
            <ArrowLeft size={16} />
            Profil
          </Link>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Award size={20} />
            Sertifikatlar
          </h1>
        </div>
      </div>

      <div className="max-w-md mx-auto px-4 -mt-7 pb-8 space-y-2.5">
        {err && <p className="text-sm text-red-600 py-4">{err}</p>}

        {d && rows.length === 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
            <Award size={30} className="mx-auto text-slate-300 mb-2" />
            <p className="text-sm text-slate-500 leading-relaxed">
              Hali sertifikat yo'q. Imtihonda 70% dan yuqori natija
              olsangiz shu yerda paydo bo'ladi.
            </p>
            <Link
              to="/student/games"
              className="inline-block mt-4 px-5 py-2.5 rounded-xl bg-brand-600 text-white text-sm font-semibold"
            >
              Tayyorlanish
            </Link>
          </div>
        )}

        {rows.map((r) => (
          <div
            key={r.id}
            className="bg-gradient-to-br from-violet-50 to-white rounded-xl border border-violet-200 p-4 flex items-center gap-3"
          >
            <span className="w-12 h-12 rounded-xl bg-violet-100 flex items-center justify-center shrink-0">
              <Award size={22} className="text-violet-600" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-bold text-slate-900 truncate">
                {r.title}
              </p>
              {r.date && (
                <p className="text-xs text-slate-500 mt-0.5">
                  {formatDate(r.date)}
                </p>
              )}
            </div>
            <span className="text-lg font-extrabold text-violet-700 shrink-0">
              {r.band != null ? `band ${r.band}` : `${r.percent}%`}
            </span>
          </div>
        ))}
      </div>
    </>
  );
}
