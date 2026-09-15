import { StudentIcon } from "./StudentIcon";

export function StudentLoading() {
  return <div className="student-loading" role="status" aria-live="polite">
    <div className="student-hero student-pattern rounded-3xl p-6">
      <StudentIcon name="level" size={58} />
      <p className="text-white font-bold text-lg mt-3">Yuklanmoqda…</p>
      <p className="text-blue-100 text-sm mt-1">Ma’lumotlaringiz tayyorlanmoqda</p>
      <div className="student-loading-bar mt-5" aria-hidden="true" />
    </div>
  </div>;
}

export function StudentLoadError({ message }: { message: string }) {
  return <div className="student-loading" role="alert"><div className="student-panel p-6">
    <StudentIcon name="settings" size={48} />
    <p className="font-bold text-lg mt-3">Ma’lumot yuklanmadi</p>
    <p className="text-slate-600 text-sm mt-2">{message}</p>
    <button onClick={() => window.location.reload()} className="bg-brand-600 text-white rounded-xl px-5 py-3 font-bold mt-5">Qayta urinish</button>
  </div></div>;
}
