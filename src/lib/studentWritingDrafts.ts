const PREFIX = "jony_student_writing:";
export type WritingDraft = { text: string; deadline: number | null };
const empty = (): WritingDraft => ({ text: "", deadline: null });
const key = (task: string, part: string) => `${PREFIX}${encodeURIComponent(task)}:${part}`;
const memory = new Map<string, WritingDraft>();

export function readWritingDraft(task: string, part: string): WritingDraft {
  const cached = memory.get(key(task, part));
  if (cached) return { ...cached };
  try {
    const value = JSON.parse(sessionStorage.getItem(key(task, part)) || "null");
    return value && typeof value.text === "string" ? {
      text: value.text,
      deadline: typeof value.deadline === "number" && Number.isFinite(value.deadline) ? value.deadline : null,
    } : empty();
  } catch { return empty(); }
}
export function saveWritingDraft(task: string, part: string, draft: WritingDraft) {
  memory.set(key(task, part), { ...draft });
  try { sessionStorage.setItem(key(task, part), JSON.stringify(draft)); } catch { /* Keep the React state when browser storage is unavailable. */ }
}
export function removeWritingDraft(task: string, part: string) {
  memory.delete(key(task, part));
  try { sessionStorage.removeItem(key(task, part)); } catch { /* Storage may be disabled. */ }
}
export function clearWritingDrafts() {
  memory.clear();
  try {
    for (let i = sessionStorage.length - 1; i >= 0; i--) {
      const k = sessionStorage.key(i);
      if (k?.startsWith(PREFIX)) sessionStorage.removeItem(k);
    }
  } catch { /* Storage may be disabled. */ }
}
export const writingSecondsLeft = (deadline: number, now = Date.now()) => Math.max(0, Math.ceil((deadline - now) / 1000));
