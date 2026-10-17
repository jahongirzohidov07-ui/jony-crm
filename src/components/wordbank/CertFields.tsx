import { CERT_EXAM_TYPES, CERT_RULES, type CertExamType } from "../../lib/wordbankApi";
import {
  SUB_LABELS,
  certMinDate,
  examNameLabel,
  levelLabel,
  scoreLabel,
  tashkentToday,
  type CertDraft,
} from "../../lib/wordbankUi";

/**
 * SERTIFIKAT NATIJASI MAYDONLARI (2026-10-17) — o'quvchining yuklash
 * oynasi va xodimning tekshiruv formasi bir xil maydonlardan
 * foydalanadi. Qaysi maydon chiqishi imtihon turiga bog'liq
 * (CERT_RULES — server ham aynan shu qoidani tekshiradi).
 */
const field = "w-full min-h-[44px] rounded-xl border border-slate-300 bg-white px-3 py-2 text-[15px] text-slate-900";
const lab = "block text-[12px] font-semibold text-slate-600 mb-1";

export function CertFields({
  value,
  onChange,
  disabled = false,
  idPrefix = "cert",
}: {
  value: CertDraft;
  onChange: (next: CertDraft) => void;
  disabled?: boolean;
  idPrefix?: string;
}) {
  const rule = CERT_RULES[value.exam_type];
  const set = (patch: Partial<CertDraft>) => onChange({ ...value, ...patch });
  const id = (s: string) => `${idPrefix}-${s}`;

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor={id("type")} className={lab}>Imtihon turi</label>
        <select
          id={id("type")}
          value={value.exam_type}
          disabled={disabled}
          onChange={(e) =>
            // Tur almashsa eski natija maydonlari tozalanadi (boshqa shkala)
            set({
              exam_type: e.target.value as CertExamType,
              exam_name: "",
              score: "",
              level: "",
              subs: {},
            })
          }
          className={field}
        >
          {CERT_EXAM_TYPES.map((t) => (
            <option key={t.key} value={t.key}>{t.label}</option>
          ))}
        </select>
      </div>

      {rule.exam_name && (
        <div>
          <label htmlFor={id("name")} className={lab}>{examNameLabel(value.exam_type)}</label>
          {rule.exam_name.options ? (
            <select
              id={id("name")}
              value={value.exam_name}
              disabled={disabled}
              onChange={(e) => set({ exam_name: e.target.value })}
              className={field}
            >
              <option value="">Tanlang</option>
              {rule.exam_name.options.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          ) : (
            <input
              id={id("name")}
              value={value.exam_name}
              disabled={disabled}
              maxLength={rule.exam_name.maxLen}
              placeholder={value.exam_type === "cefr_other" ? "Masalan: Aptis, LanguageCert" : "Masalan: SAT Subject, HSK"}
              onChange={(e) => set({ exam_name: e.target.value })}
              className={field}
            />
          )}
        </div>
      )}

      {rule.level && (
        <div>
          <label htmlFor={id("level")} className={lab}>{levelLabel(value.exam_type)}</label>
          {rule.level.options ? (
            <select
              id={id("level")}
              value={value.level}
              disabled={disabled}
              onChange={(e) => set({ level: e.target.value })}
              className={field}
            >
              <option value="">Tanlang</option>
              {rule.level.options.map((o) => (
                <option key={o} value={o}>{o}</option>
              ))}
            </select>
          ) : (
            <input
              id={id("level")}
              value={value.level}
              disabled={disabled}
              maxLength={rule.level.maxLen}
              placeholder="Masalan: 5-daraja, 85%"
              onChange={(e) => set({ level: e.target.value })}
              className={field}
            />
          )}
        </div>
      )}

      {rule.score && (
        <div>
          <label htmlFor={id("score")} className={lab}>{scoreLabel(value.exam_type)}</label>
          <input
            id={id("score")}
            type="number"
            inputMode="decimal"
            min={rule.score.min}
            max={rule.score.max}
            step={rule.score.step}
            value={value.score}
            disabled={disabled}
            placeholder={value.exam_type === "ielts" ? "Masalan: 6.5" : `${rule.score.min}–${rule.score.max}`}
            onChange={(e) => set({ score: e.target.value })}
            className={field}
          />
        </div>
      )}

      {rule.sub_scores && (
        <div>
          <p className={lab}>Bo'limlar bo'yicha (ixtiyoriy)</p>
          <div className="grid grid-cols-2 gap-2">
            {rule.sub_scores.map((k) => (
              <label key={k} className="block">
                <span className="block text-[11px] text-slate-500 mb-0.5">{SUB_LABELS[k] || k}</span>
                <input
                  type="number"
                  inputMode="decimal"
                  min={0}
                  max={9}
                  step={0.5}
                  value={value.subs[k] || ""}
                  disabled={disabled}
                  onChange={(e) => set({ subs: { ...value.subs, [k]: e.target.value } })}
                  className={field}
                />
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Sana alohida qatorda: iOS'da date maydoni tor ustunga sig'maydi */}
      <div>
        <label htmlFor={id("date")} className={lab}>Test sanasi</label>
        <input
          id={id("date")}
          type="date"
          value={value.test_date}
          min={certMinDate()}
          max={tashkentToday()}
          disabled={disabled}
          onChange={(e) => set({ test_date: e.target.value })}
          className={`${field} min-w-0`}
        />
      </div>
      <div>
        <label htmlFor={id("no")} className={lab}>Sertifikat raqami (ixtiyoriy)</label>
        <input
          id={id("no")}
          value={value.cert_no}
          maxLength={40}
          disabled={disabled}
          placeholder="TRF / ID raqami"
          onChange={(e) => set({ cert_no: e.target.value })}
          className={field}
        />
      </div>
    </div>
  );
}
