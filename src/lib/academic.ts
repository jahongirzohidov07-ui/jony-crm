// Akademik risk - backend/roles.py'dagi RISK_SIGNALS/RISK_LEVELS bilan bir xil.

export const RISK_LEVELS = [
  { key: "normal", label: "Normal", dot: "bg-emerald-500",
    box: "bg-emerald-50 border-emerald-200", text: "text-emerald-700" },
  { key: "watch", label: "E'tibor kerak", dot: "bg-amber-400",
    box: "bg-amber-50 border-amber-200", text: "text-amber-700" },
  { key: "high", label: "Yuqori xavf", dot: "bg-orange-500",
    box: "bg-orange-50 border-orange-200", text: "text-orange-700" },
  { key: "critical", label: "Ketib qolish xavfi", dot: "bg-red-500",
    box: "bg-red-50 border-red-200", text: "text-red-700" },
];

export function riskLevel(key?: string | null) {
  return RISK_LEVELS.find((l) => l.key === key) || RISK_LEVELS[0];
}

/** Qo'lda qo'yiladigan signallar. Qolganlari avtomat hisoblanadi. */
export const MANUAL_SIGNALS = [
  { key: "no_homework", label: "Uy vazifasini bajarmayapti" },
  { key: "teacher_negative", label: "Ustoz salbiy izoh berdi" },
  { key: "no_progress", label: "O'sish yo'q" },
  { key: "score_drop", label: "Natijasi tushdi" },
];

/** Guruh to'lishi darajalari. */
export const FILL_BANDS = [
  { key: "good", label: "Yaxshi", text: "text-emerald-600", bar: "bg-emerald-500" },
  { key: "ok", label: "Qoniqarli", text: "text-sky-600", bar: "bg-sky-500" },
  { key: "problem", label: "Muammoli", text: "text-amber-600", bar: "bg-amber-500" },
  { key: "critical", label: "Birlashtirish yoki yopish", text: "text-red-600", bar: "bg-red-500" },
];

export function fillBand(key?: string | null) {
  return FILL_BANDS.find((b) => b.key === key) || FILL_BANDS[3];
}

export const CERTIFICATE_KINDS = [
  { key: "ielts", label: "IELTS" },
  { key: "cefr", label: "CEFR" },
  { key: "internal", label: "Ichki sertifikat" },
  { key: "course", label: "Kurs tugatdi" },
  { key: "olympiad", label: "Olimpiada" },
  { key: "other", label: "Boshqa" },
];

export const TALK_CHANNELS = [
  { key: "phone", label: "Telefon" },
  { key: "visit", label: "Tashrif" },
  { key: "telegram", label: "Telegram" },
  { key: "meeting", label: "Yig'ilish" },
];

/** O'quvchi tarixidagi voqea turlari. */
export const HISTORY_KINDS: Record<string, { label: string; dot: string }> = {
  group: { label: "Guruh", dot: "bg-sky-500" },
  complaint: { label: "Shikoyat", dot: "bg-red-500" },
  talk: { label: "Ota-ona suhbati", dot: "bg-violet-500" },
  certificate: { label: "Sertifikat", dot: "bg-emerald-500" },
  freeze: { label: "Muzlatish", dot: "bg-amber-500" },
  leave: { label: "Chiqish", dot: "bg-slate-500" },
  return: { label: "Qaytish", dot: "bg-emerald-500" },
  trial: { label: "Sinov", dot: "bg-slate-400" },
};
