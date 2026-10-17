export type LearningMeasurement = {
  window_days: number; started_on: string | null; active_days: number;
  plan_days: number; completed_plan_days: number;
  return_day7: {eligible: boolean; returned: boolean | null};
  retention7: {total: number; before_correct: number; after_correct: number};
  speaking_days: number; speaking_attempts: number;
};
export default function CourseMeasurement({data:m}: {data:LearningMeasurement}) {
  return <details className="rounded-xl border border-sky-200 bg-sky-50 p-4">
    <summary className="cursor-pointer text-sm font-semibold text-sky-950">28 kunlik natijalar</summary>
    <div className="mt-4 space-y-4 text-sm text-slate-800">
      <p>Oxirgi {m.window_days} kun. Mashq odati va esda qolgan bilim alohida hisoblanadi.</p>
      {!m.started_on ? <p className="rounded-lg bg-white p-3">Birinchi mashqingizdan keyin kuzatuv boshlanadi.</p> : <p className="text-xs text-slate-600">Birinchi mashq: {m.started_on}</p>}
      <dl className="grid grid-cols-2 gap-3">
        <div className="rounded-xl bg-white p-3"><dt>Mashq qilingan kun</dt><dd className="mt-1 text-xl font-bold">{m.active_days}</dd></div>
        <div className="rounded-xl bg-white p-3"><dt>Bajarilgan kunlik reja</dt><dd className="mt-1 text-xl font-bold">{m.completed_plan_days} / {m.plan_days}</dd></div>
      </dl>
      <p className="text-xs text-slate-600">Hisobotda mashq boshlangandagi reja hisoblanadi. Keyin vaqtni qisqartirish bu hisobni o‘zgartirmaydi; bir kun bir marta sanaladi.</p>
      <section aria-label="Yettinchi kun qaytishi" className="rounded-xl bg-white p-3"><h3 className="font-semibold">7-kuni yana mashq qildimmi?</h3><p className="mt-1">{!m.return_day7.eligible ? 'Hali 7-kun yakunlanmagan — xulosa qilishga erta.' : m.return_day7.returned ? 'Ha, birinchi mashqdan 7 kun keyin ham mashq qilgansiz.' : 'O‘sha kuni mashq qayd etilmagan. Bugun davom etishingiz mumkin.'}</p></section>
      <section aria-label="Yetti kunlik eslab qolish" className="rounded-xl bg-white p-3"><h3 className="font-semibold">Bir haftadan keyin esda qoldimi?</h3>{m.retention7.total ? <><p className="mt-1">Bir xil {m.retention7.total} savol: boshida {m.retention7.before_correct}/{m.retention7.total}, kamida 7 kun o‘tib {m.retention7.after_correct}/{m.retention7.total} to‘g‘ri.</p><p className="mt-1 text-xs text-slate-600">Faqat shu savollar natijasi; umumiy til darajasi emas.</p></> : <p className="mt-1">Hali kamida 7 kun o‘tib qayta tekshirilgan savollar yo‘q.</p>}</section>
      <section className="rounded-xl bg-white p-3"><h3 className="font-semibold">Gapirish mashqi</h3><p className="mt-1">{m.speaking_days} kun · {m.speaking_attempts} alohida topshiriq urinishlari.</p><p className="mt-1 text-xs text-slate-600">Bu mashq miqdori. Ravonlik va talaffuz o‘sishini ustoz bir xil mezon bilan tekshirishi kerak.</p></section>
      <p className="text-xs text-slate-600">2–4 hafta kuzating. Bu raqamlar gamifikatsiya natijani yaxshilaganini o‘z-o‘zidan isbotlamaydi.</p>
    </div>
  </details>;
}
