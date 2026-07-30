import { AlertTriangle, Ban } from "lucide-react";
import type { CheckProblem } from "../lib/api";

/**
 * Avtomatik tekshiruv natijasi. Ikki xil muammo bor:
 *   block — saqlashga ruxsat berilmaydi (ustoz/xona to'qnashuvi, sig'im);
 *   warn  — saqlash mumkin, lekin odam ko'rib turishi kerak.
 */
export function ScheduleProblems({
  problems,
  canForce,
  saving,
  onForce,
}: {
  problems: CheckProblem[];
  canForce: boolean;
  saving?: boolean;
  onForce: () => void;
}) {
  if (problems.length === 0) return null;

  const blocking = problems.filter((p) => p.severity === "block");
  const warnings = problems.filter((p) => p.severity !== "block");

  return (
    <div
      className={`rounded-lg border p-3 mb-3 ${
        blocking.length
          ? "bg-red-50 border-red-200"
          : "bg-amber-50 border-amber-200"
      }`}
    >
      <div className="flex items-center gap-1.5 mb-2">
        {blocking.length ? (
          <>
            <Ban size={14} className="text-red-600" />
            <p className="text-sm font-medium text-red-900">
              Bunday saqlash mumkin emas
            </p>
          </>
        ) : (
          <>
            <AlertTriangle size={14} className="text-amber-600" />
            <p className="text-sm font-medium text-amber-900">
              E'tibor bering
            </p>
          </>
        )}
      </div>

      <div className="space-y-1.5">
        {[...blocking, ...warnings].map((p, i) => (
          <div key={i} className="flex items-start gap-2">
            <span
              className={`text-xs font-medium shrink-0 px-1.5 py-0.5 rounded ${
                p.severity === "block"
                  ? "bg-red-100 text-red-700"
                  : "bg-amber-100 text-amber-700"
              }`}
            >
              {p.label}
            </span>
            <p
              className={`text-xs ${
                p.severity === "block" ? "text-red-900" : "text-amber-900"
              }`}
            >
              {p.message}
            </p>
          </div>
        ))}
      </div>

      {canForce && blocking.length === 0 && (
        <button
          onClick={onForce}
          disabled={saving}
          className="mt-2.5 px-3 py-1.5 rounded-lg bg-amber-600 text-white text-xs font-medium hover:bg-amber-700 disabled:opacity-50"
        >
          {saving ? "Saqlanmoqda..." : "Baribir saqlash"}
        </button>
      )}
    </div>
  );
}
