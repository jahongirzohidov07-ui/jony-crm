export interface ExamMetric { avg: number | null; results: number; exams: number; students?: number; groups?: number }
export interface ExamSummary extends ExamMetric { key: number; label: string; teacher?: string; branch?: string; level?: string; group?: string; test_ids: number[] }
export interface ExamTest { key: number; label: string; date: string; group_id: number; group: string; teacher_id: number; teacher: string; branch: string; level: string; avg: number | null; results: number; students: number; absent: number; retake: boolean; members: {key: number; label: string; percent: number | null; absent: boolean; counted: boolean}[] }
export interface MonthlyExamReport extends ExamMetric { period: string; scope: string; teacher: string | null; standard: number; by_branch: ExamSummary[]; by_teacher: ExamSummary[]; by_group: ExamSummary[]; by_student: ExamSummary[]; tests: ExamTest[]; history: (ExamMetric & {period: string})[] }
export type ExamReportKind = "by_teacher" | "by_group" | "by_branch" | "by_student";
export const reportTitles: Record<ExamReportKind, string> = { by_teacher: "Ustozlar natijalari", by_group: "Guruhlar natijalari", by_branch: "Filiallar natijalari", by_student: "O'quvchilar natijalari" };
export const percent = (n: number | null) => n == null ? "—" : `${n}%`;
export const monthLabel = (period: string) => { const [y,m]=period.split("-"); return `${["Yanvar","Fevral","Mart","Aprel","May","Iyun","Iyul","Avgust","Sentabr","Oktabr","Noyabr","Dekabr"][Number(m)-1]} ${y}`; };
export function localMonth() { const parts = new Intl.DateTimeFormat("en", {timeZone:"Asia/Tashkent", year:"numeric",month:"2-digit"}).formatToParts(new Date()); return `${parts.find(p=>p.type==="year")!.value}-${parts.find(p=>p.type==="month")!.value}`; }
