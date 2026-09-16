import { useEffect, useState } from "react";
import { formatPhone } from "./PhoneInput";
import { X, Save, FileText, Plus } from "lucide-react";
import { api, type CandidateCard as Card } from "../lib/api";
import { formatSom, formatDate } from "../lib/format";
import { candidateSourceLabel } from "../lib/hr";
import { Attachments } from "./Attachments";
import { ObservationList } from "./LessonRubric";
import { CandidateGrowth } from "./CandidateGrowth";
import { AddToBlacklist, BlacklistBanner } from "./HrBlacklist";
import { CandidateHistoryList } from "./CandidateHistory";
import { useAuth } from "../lib/AuthContext";
import { BLACKLIST_MANAGE, can } from "../lib/roles";

/**
 * Nomzod kartasi. Qaror qabul qilish uchun kerak bo'lgan hammasi bitta
 * ekranda: CV, tajriba, ballar, kuchli va zaif tomonlari, tavsiyanoma.
 */
export function CandidateCard({
  id,
  canEdit,
  onClose,
  onSaved,
}: {
  id: number;
  canEdit: boolean;
  onClose: () => void;
  onSaved?: () => void;
}) {
  const { user } = useAuth();
  const canBlacklist = can(user?.role, BLACKLIST_MANAGE);
  const [blAdd, setBlAdd] = useState(false);
  // "Avvalgi arizalari"dan boshqa kartaga shu oynaning o'zida o'tiladi
  const [curId, setCurId] = useState(id);
  const [c, setC] = useState<Card | null>(null);
  const [f, setF] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [ok, setOk] = useState(false);

  function load() {
    api.get<Card>(`/candidates/${curId}`, true).then((d) => {
      setC(d);
      setF({
        cv: d.cv ?? "",
        experience_years: d.experience_years?.toString() ?? "",
        workplaces: d.workplaces ?? "",
        certificates: d.certificates ?? "",
        language_level: d.language_level ?? "",
        native_language: d.native_language ?? "",
        expected_salary: d.expected_salary?.toString() ?? "",
        trial_score: d.trial_score?.toString() ?? "",
        interview_score: d.interview_score?.toString() ?? "",
        strengths: d.strengths ?? "",
        weaknesses: d.weaknesses ?? "",
        reference_note: d.reference_note ?? "",
        decision: d.decision ?? "pending",
      });
    });
  }
  useEffect(load, [curId]);

  async function merge(row: { id: number; created_at?: string | null;
                              full_name: string }) {
    if (!c) return;
    if (!confirm(
      `${row.full_name} (${row.created_at?.slice(0, 10) || "?"}) arizasi ` +
      `shu kartaga qo'shilsinmi?\n\nArizalari, suhbatlari, baholari va ` +
      `fayllari shu yerga ko'chadi, bo'sh maydonlar to'ldiriladi, ikkinchi ` +
      `yozuv o'chadi. Buni ortga qaytarib bo'lmaydi.`)) return;
    try {
      await api.post(`/candidates/${c.id}/merge`, { source_id: row.id });
      load();
      onSaved?.();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Xatolik");
    }
  }

  function set(k: string, v: string) {
    setF({ ...f, [k]: v });
    setOk(false);
  }

  /**
   * Til darajasi ro'yxatiga YANGI variant qo'shish (2026-08-16).
   *
   * Jahongir: "tagidan qo'shadigan qilish kerak til darajasini
   * nomzodlarda hr bo'limida, ona tili yo boshqa sertifikatlar
   * kiritib bo'lmayabdi".
   *
   * Qo'shilgan variant BAZAGA yoziladi — keyingi safar hamma
   * uchun ro'yxatda turadi, har safar qaytadan yozish shart emas.
   */
  async function addLanguageOption() {
    const label = prompt(
      "Yangi variant nomi\n\nMasalan: TOEFL 90+, Rus tili C1, " +
      "CEFR sertifikati, Ona tili"
    );
    if (!label || !label.trim()) return;
    try {
      const row = await api.post<{ key: string; label: string }>(
        "/hr/options/language_level",
        { label: label.trim() }
      );
      await api.put(`/candidates/${curId}`, { language_level: row.key });
      load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Qo'shib bo'lmadi");
    }
  }

  async function save() {
    setSaving(true);
    await api.put(`/candidates/${curId}`, {
      cv: f.cv || null,
      experience_years: f.experience_years ? Number(f.experience_years) : null,
      workplaces: f.workplaces || null,
      certificates: f.certificates || null,
      language_level: f.language_level || null,
      native_language: f.native_language || null,
      expected_salary: f.expected_salary ? Number(f.expected_salary) : null,
      trial_score: f.trial_score ? Number(f.trial_score) : null,
      interview_score: f.interview_score ? Number(f.interview_score) : null,
      strengths: f.strengths || null,
      weaknesses: f.weaknesses || null,
      reference_note: f.reference_note || null,
      decision: f.decision || "pending",
    });
    setSaving(false);
    setOk(true);
    load();
    onSaved?.();
  }

  const overall =
    f.trial_score || f.interview_score
      ? (
          ([f.trial_score, f.interview_score]
            .filter(Boolean)
            .reduce((a, b) => a + Number(b), 0) as number) /
          [f.trial_score, f.interview_score].filter(Boolean).length
        ).toFixed(1)
      : null;

  return (
    <div className="fixed inset-0 bg-black/30 flex items-start justify-center z-50 p-4 pt-12 overflow-y-auto">
      <div className="bg-white rounded-xl w-full max-w-3xl shadow-xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div>
            <h3 className="font-semibold text-slate-900">
              {c?.full_name ?? "Nomzod"}
            </h3>
            <p className="text-xs text-slate-500">
              {[c?.vacancy, c?.branch, formatPhone(c?.phone)].filter(Boolean).join(" · ")}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {c && !c.blacklist && canBlacklist && (
              <button
                onClick={() => setBlAdd(true)}
                className="text-xs px-2.5 py-1.5 rounded-lg bg-red-50 text-red-700 hover:bg-red-100"
              >
                Qora ro'yxatga
              </button>
            )}
            <button onClick={onClose} className="text-slate-400">
              <X size={18} />
            </button>
          </div>
        </div>
        {blAdd && c && (
          <AddToBlacklist
            candidateId={c.id}
            name={c.full_name}
            onClose={() => setBlAdd(false)}
            onDone={() => {
              setBlAdd(false);
              load();
              onSaved?.();
            }}
          />
        )}

        {!c ? (
          <p className="text-sm text-slate-400 p-8">Yuklanmoqda...</p>
        ) : (
          <div className="p-5 space-y-5">
            <BlacklistBanner hit={c.blacklist} />

            {/* TAKRORIY NOMZOD (2026-09-16) */}
            {!!c.history?.length && (
              <div className="rounded-xl border border-amber-300 bg-amber-50/60 p-4">
                <p className="text-sm font-semibold text-amber-800 mb-1">
                  Avval ham ariza bergan — {c.history.length} marta
                </p>
                <CandidateHistoryList
                  rows={c.history}
                  onOpen={(hid) => setCurId(hid)}
                  onMerge={canEdit ? merge : undefined}
                />
              </div>
            )}

            {/* ARIZA MA'LUMOTLARI (2026-09-16, Jahongir: "nomzod haqidagi
                to'liq ma'lumotlarni ruchka editni bosmasa bilib bo'lmayabdi,
                ismi ustiga bosganda ham chiqsin"). */}
            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-xs font-medium text-slate-700 mb-2">
                Ariza ma'lumotlari
              </p>
              <div className="grid gap-x-6 sm:grid-cols-2">
                <Info
                  label="Lavozim"
                  value={[c.role_label, c.subject].filter(Boolean).join(" · ")}
                />
                <Info label="Vakansiya" value={c.vacancy} />
                <Info label="Telefon" value={formatPhone(c.phone)} />
                <Info label="Filial" value={c.branch} />
                <Info label="Bosqich" value={c.stage_label} />
                <Info label="Manba" value={candidateSourceLabel(c.source)} />
                <Info
                  label="Ariza sanasi"
                  value={c.created_at ? formatDate(c.created_at) : null}
                />
                <Info label="Tug'ilgan sana" value={c.birth_date_text} />
                <Info label="Oilaviy holati" value={c.marital_label} />
                <Info label="Yashash manzili" value={c.address} />
                <Info label="Ma'lumoti" value={c.education} />
                <Info label="Ijtimoiy tarmoqlar" value={c.socials} />
                <Info label="Qancha vaqt ishlamoqchi" value={c.work_duration} />
                <Info
                  label="Tajriba"
                  value={c.experience_years != null
                    ? `${c.experience_years} yil` : null}
                />
                {c.reject_reason && (
                  <Info label="Rad etish sababi" value={c.reject_reason} />
                )}
              </div>
              {c.workplaces && (
                <Info label="Avvalgi ish joylari" value={c.workplaces} block />
              )}
              {c.note && <Info label="Izoh" value={c.note} block />}
            </div>

            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-xs font-medium text-slate-700 mb-2">
                Rasm va hujjatlar
              </p>
              <Attachments
                entity="candidate"
                entityId={c.id}
                compact
                kinds={[
                  { key: "photo", label: "Rasm" },
                  { key: "certificate", label: "Sertifikat" },
                  { key: "resume", label: "Rezyume" },
                  { key: "document", label: "Hujjat" },
                ]}
              />
            </div>
            {/* Ballar - eng muhimi tepada */}
            <div className="grid grid-cols-3 gap-3">
              <Score
                label="Probniy dars"
                value={f.trial_score}
                onChange={(v) => set("trial_score", v)}
                canEdit={canEdit}
              />
              <Score
                label="Intervyu"
                value={f.interview_score}
                onChange={(v) => set("interview_score", v)}
                canEdit={canEdit}
              />
              <div className="bg-brand-50 rounded-xl border border-brand-200 p-3 text-center">
                <p className="text-xs text-brand-700 mb-1">Umumiy</p>
                <p className="text-2xl font-semibold text-brand-800">
                  {overall ?? "—"}
                </p>
              </div>
            </div>

            {/* Sinov darsini mezon bo'yicha baholash — natija
                "Probniy dars" balliga o'zi tushadi */}
            <div>
              <p className="text-xs font-medium text-slate-700 mb-2">
                Sinov darsi baholashi
              </p>
              <CandidateGrowth key={curId} candidateId={curId} />
              <div className="h-4" />
              <ObservationList key={curId} candidateId={curId} canAdd={canEdit} />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <Text
                label="Tajriba (yil)"
                value={f.experience_years}
                onChange={(v) => set("experience_years", v)}
                canEdit={canEdit}
                type="number"
              />
              <div>
                <label className="block text-xs text-slate-500 mb-1">
                  Til darajasi / sertifikat
                </label>
                {canEdit ? (
                  <>
                    <select
                      value={f.language_level}
                      onChange={(e) => set("language_level", e.target.value)}
                      className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white"
                    >
                      <option value="">— tanlang —</option>
                      {c.language_levels.map((l) => (
                        <option key={l.key} value={l.key}>
                          {l.label}
                        </option>
                      ))}
                      {/* Ro'yxatda yo'q eski qiymat ham yo'qolmasin */}
                      {f.language_level &&
                        !c.language_levels.some(
                          (l) => l.key === f.language_level
                        ) && (
                          <option value={f.language_level}>
                            {c.language_level_label || f.language_level}
                          </option>
                        )}
                    </select>
                    <button
                      type="button"
                      onClick={addLanguageOption}
                      className="mt-1.5 inline-flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700"
                    >
                      <Plus size={13} />
                      Ro'yxatga yangi variant qo'shish
                    </button>
                  </>
                ) : (
                  <p className="text-sm text-slate-800 py-2">
                    {c.language_level_label || "—"}
                  </p>
                )}
              </div>
              <Text
                label="Ona tili"
                value={f.native_language}
                onChange={(v) => set("native_language", v)}
                canEdit={canEdit}
                placeholder="O'zbek / Rus / Qoraqalpoq"
              />
              <Text
                label="Kutilayotgan maosh"
                value={f.expected_salary}
                onChange={(v) => set("expected_salary", v)}
                canEdit={canEdit}
                type="number"
                hint={
                  f.expected_salary
                    ? formatSom(Number(f.expected_salary))
                    : undefined
                }
              />
              <div>
                <label className="block text-xs text-slate-500 mb-1">
                  Yakuniy qaror
                </label>
                {canEdit ? (
                  <select
                    value={f.decision}
                    onChange={(e) => set("decision", e.target.value)}
                    className={`w-full px-3 py-2 rounded-lg border text-sm font-medium ${
                      f.decision === "hire"
                        ? "bg-emerald-50 border-emerald-300 text-emerald-800"
                        : f.decision === "reject"
                          ? "bg-red-50 border-red-300 text-red-800"
                          : "bg-white border-slate-200 text-slate-700"
                    }`}
                  >
                    {c.decisions.map((d) => (
                      <option key={d.key} value={d.key}>
                        {d.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <p className="text-sm text-slate-800 py-2">
                    {c.decision_label}
                  </p>
                )}
              </div>
            </div>

            <Area
              label="CV"
              value={f.cv}
              onChange={(v) => set("cv", v)}
              canEdit={canEdit}
              rows={3}
            />
            <Area
              label="Ish joylari"
              value={f.workplaces}
              onChange={(v) => set("workplaces", v)}
              canEdit={canEdit}
              rows={2}
              placeholder="Bright School (2021-2023), Free English (2023-2026)"
            />
            <Area
              label="Sertifikatlar"
              value={f.certificates}
              onChange={(v) => set("certificates", v)}
              canEdit={canEdit}
              rows={2}
              placeholder="CELTA, IELTS 7.5"
            />

            <div className="grid gap-4 md:grid-cols-2">
              <Area
                label="Kuchli tomonlari"
                value={f.strengths}
                onChange={(v) => set("strengths", v)}
                canEdit={canEdit}
                rows={3}
              />
              <Area
                label="Zaif tomonlari"
                value={f.weaknesses}
                onChange={(v) => set("weaknesses", v)}
                canEdit={canEdit}
                rows={3}
              />
            </div>

            <Area
              label="Tavsiyanoma"
              value={f.reference_note}
              onChange={(v) => set("reference_note", v)}
              canEdit={canEdit}
              rows={2}
              placeholder="Oldingi rahbari nima dedi"
            />

            <div>
              <p className="text-xs font-medium text-slate-700 mb-2 flex items-center gap-1.5">
                <FileText size={13} /> Fayllar — rasm, sertifikat, CV
              </p>
              <Attachments key={curId} entity="candidate" entityId={curId} />
            </div>

            {canEdit && (
              <div className="flex items-center gap-3">
                <button
                  onClick={save}
                  disabled={saving}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-brand-600 text-white text-sm font-medium hover:bg-brand-700 disabled:opacity-50"
                >
                  <Save size={15} />
                  {saving ? "Saqlanmoqda..." : "Saqlash"}
                </button>
                {ok && (
                  <span className="text-sm text-emerald-600">Saqlandi</span>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function Score({
  label,
  value,
  onChange,
  canEdit,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  canEdit: boolean;
}) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-3 text-center">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      {canEdit ? (
        <input
          type="number"
          step="0.5"
          min="0"
          max="10"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="—"
          className="w-full text-2xl font-semibold text-slate-900 text-center outline-none"
        />
      ) : (
        <p className="text-2xl font-semibold text-slate-900">{value || "—"}</p>
      )}
    </div>
  );
}

function Text({
  label,
  value,
  onChange,
  canEdit,
  type = "text",
  hint,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  canEdit: boolean;
  type?: string;
  hint?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1">{label}</label>
      {canEdit ? (
        <input
          type={type}
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
        />
      ) : (
        <p className="text-sm text-slate-800 py-2">{value || "—"}</p>
      )}
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

function Area({
  label,
  value,
  onChange,
  canEdit,
  rows = 2,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  canEdit: boolean;
  rows?: number;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs text-slate-500 mb-1">{label}</label>
      {canEdit ? (
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={rows}
          placeholder={placeholder}
          className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm"
        />
      ) : (
        <p className="text-sm text-slate-700 whitespace-pre-wrap">
          {value || "—"}
        </p>
      )}
    </div>
  );
}

/** Kartadagi faqat o'qiladigan qator: savol tepada, javob ostida. */
function Info({ label, value, block = false }: {
  label: string;
  value?: string | null;
  block?: boolean;
}) {
  return (
    <div className={`py-1.5 border-b border-slate-50 ${block ? "mt-1" : ""}`}>
      <p className="text-[11px] text-slate-400">{label}</p>
      <p className="text-sm text-slate-800 whitespace-pre-line break-words">
        {value && String(value).trim() ? value : "—"}
      </p>
    </div>
  );
}
