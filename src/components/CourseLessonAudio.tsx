import { useRef, useState } from 'react';

type Props = { course: 'intensive' | 'german'; lesson: number; title: string };

/** Persistent course recording; does not depend on operating-system speech voices. */
export default function CourseLessonAudio({ course, lesson, title }: Props) {
  const player = useRef<HTMLAudioElement>(null);
  const [failed, setFailed] = useState(false);
  const [rate, setRate] = useState(1);
  const path = `/${course}/audio/lesson-${String(lesson).padStart(3, '0')}.mp3`;
  return <div className="my-4 rounded-xl border border-blue-100 bg-blue-50 p-4">
    <p className="font-semibold text-blue-950">{title} · tayyor audio</p>
    <p className="my-2 text-sm leading-6 text-slate-600">Kurs uchun tayyorlangan sun’iy ovozli yozuv. 1-tinglash: umumiy mazmun; 2-tinglash: savollar. Transkript va javoblarni tekshiruvdan keyin oching.</p>
    <audio ref={player} className="my-3 w-full print:hidden" controls preload="none" src={path}
      aria-label={`${lesson}-dars ${course === 'german' ? 'nemischa' : 'inglizcha'} tinglash yozuvi`}
      onError={() => setFailed(true)} onCanPlay={() => setFailed(false)} />
    <div className="flex flex-wrap items-center gap-4 text-sm print:hidden">
      <label>Tezlik <select className="ml-2 rounded-lg border border-blue-200 bg-white p-2" value={rate} onChange={event => { const next = Number(event.target.value); setRate(next); if (player.current) player.current.playbackRate = next; }}>
        <option value={0.8}>0.8× · yordam bilan</option><option value={1}>1× · asl tezlik</option><option value={1.1}>1.1× · qo‘shimcha</option>
      </select></label>
      <a className="font-semibold text-blue-700 underline" href={path} download>MP3 yuklab olish</a>
    </div>
    {failed && <p role="alert" className="mt-3 text-sm leading-6 text-amber-900">Audio yuklanmadi. Internetni tekshirib qayta oching yoki MP3 havolasidan foydalaning. Vaqtincha ustoz transkriptni ikki marta o‘qib berishi mumkin.</p>}
    <p className="mt-2 text-xs leading-5 text-slate-500">Nazoratda asl tezlikni saqlang. Ushbu mashq rasmiy imtihon audiosi emas.</p>
  </div>;
}
