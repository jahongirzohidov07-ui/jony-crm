type Accuracy = {total: number; correct: number; eligible: boolean; accuracy_percent: number | null};
type DifficultyPeriod = {first_attempt: Accuracy; last7: Accuracy; prior7: Accuracy; change_percentage_points: number | null};
const skillLabels: Record<string, string> = {reading: "O‘qish", listening: "Tinglash", grammar: "Grammatika", homework: "Mustahkamlash", writing: "Yozish", speaking: "Gapirish"};
function accuracyLabel(value: Accuracy) {
  return `${value.correct}/${value.total}${value.eligible ? ` (${value.accuracy_percent}%)` : " — foiz uchun kamida 5 savol kerak"}`;
}
function DifficultyRow({value, label}: {value: DifficultyPeriod; label: string}) {
  return <li className="rounded-lg border p-3"><h4 className="font-semibold">{label}</h4><p>Birinchi javob: {accuracyLabel(value.first_attempt)}</p><p>Oxirgi 7 kun: {accuracyLabel(value.last7)}</p><p>Oldingi 7 kun: {accuracyLabel(value.prior7)}</p><p className="text-xs text-slate-600">{value.change_percentage_points === null ? "Taqqoslash uchun har ikki davrda kamida 5 turli savol kerak." : `Farq: ${value.change_percentage_points > 0 ? "+" : ""}${value.change_percentage_points} foiz punkti. Savollar qiyinligi farq qilishi mumkin; bu sababiy o‘sish dalili emas.`}</p></li>;
}
export type LearningMeasurement = {
  difficulty?: {minimum_samples: number; overall: DifficultyPeriod; skills: (DifficultyPeriod & {skill: string})[]};
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
      {m.difficulty && <section aria-label="Birinchi aniq javoblar" className="space-y-3 rounded-xl bg-white p-3"><h3 className="font-semibold">Qaysi ko‘nikmada savollar qiyinroq bo‘lyapti?</h3><p className="text-xs text-slate-600">Har bir savolning faqat birinchi avtomatik tekshirilgan javobi. Qayta urinish va o‘zini baholash qo‘shilmaydi. Tezlik bilim darajasini bildirmaydi.</p><ul className="space-y-2"><DifficultyRow value={m.difficulty.overall} label="Jami"/>{m.difficulty.skills.map(item => <DifficultyRow key={item.skill} value={item} label={skillLabels[item.skill] || item.skill}/>)}</ul></section>}
      <p className="text-xs text-slate-600">2–4 hafta kuzating. Bu raqamlar gamifikatsiya natijani yaxshilaganini o‘z-o‘zidan isbotlamaydi.</p>
    </div>
  </details>;
}
