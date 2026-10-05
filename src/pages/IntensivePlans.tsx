import { useId, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ArrowLeft, BookOpen, Clock, Download, Eye, RotateCcw, Search, Sparkles } from 'lucide-react';
import brand from '../assets/brand-icon.png';
import { grammar, words, topics, teacherNotes, monthNames, lessonPlan, standardTimeline, reviewTimeline, homework, vocabularyPractice, grammarChecks, grammarReview, topicPractice, isCorrect, shuffled } from '../lib/intensive';
import type { Question, Word } from '../lib/intensive';

const button='inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:border-blue-400 hover:text-blue-700 disabled:opacity-40';
const panel='rounded-2xl border border-slate-200 bg-white p-4 md:p-6';

function Practice({questions,title}:{questions:Question[];title:string}) {
  const instance=useId();
  const [answers,setAnswers]=useState<Record<string,string>>({});
  const [checked,setChecked]=useState(false);
  const [retry,setRetry]=useState<string[]|null>(null);
  const [revealed,setRevealed]=useState(false);
  const active=retry?questions.filter(q=>retry.includes(q.id)):questions;
  const wrong=active.filter(q=>!isCorrect(answers[q.id]??'',q.answers));
  if(!active.length) return <p className="text-sm text-slate-500">Bu to‘plamda mashq yo‘q.</p>;
  return <section className={panel} aria-label={title}>
    <h3 className="font-bold text-slate-900">{title} <span className="text-sm font-normal text-slate-500">· {active.length} savol</span></h3>
    <p className="mt-1 text-xs leading-5 text-slate-500">Natija shu mashg‘ulot uchun; rasmiy bahoga yozilmaydi.</p>
    <form className="mt-4 space-y-4" onSubmit={e=>{e.preventDefault();setChecked(true);}}>
      {active.map((q,i)=><div key={q.id} className="rounded-xl bg-slate-50 p-3">
        <label htmlFor={`${instance}-${q.id}`} className="block text-sm font-medium leading-6 text-slate-800">{i+1}. {q.prompt}</label>
        {q.hint&&<details className="my-1 text-xs text-slate-500"><summary className="cursor-pointer">Yordam</summary><p className="mt-1">{q.hint}</p></details>}
        <input id={`${instance}-${q.id}`} autoComplete="off" spellCheck={false} value={answers[q.id]??''} onChange={e=>{setAnswers({...answers,[q.id]:e.target.value});setChecked(false);}} aria-invalid={checked&&!isCorrect(answers[q.id]??'',q.answers)} className="mt-2 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-base outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100" placeholder="Javobingiz…" />
        {checked&&<p className={`mt-2 text-sm ${isCorrect(answers[q.id]??'',q.answers)?'text-emerald-700':'text-rose-700'}`}>{isCorrect(answers[q.id]??'',q.answers)?'✓ To‘g‘ri':'Qayta mashq qiling'} · {q.answers.join(' / ')}<span className="mt-1 block text-slate-600">{q.explanation}</span></p>}
        {!checked&&revealed&&<p className="mt-2 text-sm text-blue-700">Namuna: {q.answers.join(' / ')} · {q.explanation}</p>}
      </div>)}
      <div className="flex flex-wrap gap-2"><button className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700" type="submit">Tekshirish</button><button type="button" className={button} onClick={()=>setRevealed(!revealed)}><Eye size={16}/>{revealed?'Javoblarni yopish':'Javoblar'}</button>
        <button type="button" className={button} onClick={()=>{setAnswers({});setChecked(false);setRevealed(false);setRetry(null);}}><RotateCcw size={16}/>Qaytadan</button>
        {checked&&wrong.length>0&&<button type="button" className={button} onClick={()=>{setRetry(wrong.map(q=>q.id));setAnswers({});setChecked(false);setRevealed(false);}}>Faqat xatolar ({wrong.length})</button>}
      </div>
      {checked&&<p role="status" className="rounded-xl bg-blue-50 p-3 font-semibold text-blue-800">{active.length-wrong.length}/{active.length} to‘g‘ri · {Math.round((active.length-wrong.length)/active.length*100)}%{revealed?' · Javoblar ko‘rilgan mashq':''}</p>}
    </form>
  </section>;
}

function WordCards({pool}:{pool:Word[]}) {
  const [hide,setHide]=useState(false);
  return <div><button type="button" className={`${button} mb-3`} onClick={()=>setHide(!hide)}><Eye size={16}/>{hide?'Tarjimalarni ko‘rsatish':'Tarjimalarni yopish'}</button>
    <div className="grid gap-3 lg:grid-cols-2">{pool.map(w=><article key={w.id} className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="flex flex-wrap items-baseline gap-2"><span className="text-xs text-slate-400">{String(w.id).padStart(3,'0')}</span><h3 className="text-lg font-bold text-slate-900">{w.word}</h3><span className="text-sm text-blue-600">{w.ipa}</span></div>
      {!hide&&<p className="mt-1 text-sm font-medium text-slate-600">{w.meaning}</p>}
      <p className="mt-3 border-l-2 border-lime-300 pl-3 text-sm leading-6 text-slate-800">{w.example}</p>{!hide&&<p className="mt-1 pl-3 text-sm leading-5 text-slate-500">{w.translation}</p>}
    </article>)}</div></div>;
}

function TopicCard({id}:{id:string}) {
  const topic=topics.find(t=>t.id===id)!;
  return <details className="rounded-xl border border-slate-200 bg-white">
    <summary className="cursor-pointer p-4 text-sm font-semibold text-slate-800">{id} · {topic.title}</summary>
    <div className="space-y-4 border-t border-slate-100 p-4">
      <p className="rounded-xl bg-blue-50 p-4 text-sm leading-6 text-blue-900">{topic.example}</p>
      <div className="rounded-xl bg-amber-50 p-4 text-sm leading-6 text-slate-700"><p><b>Ustozga qoida:</b> {teacherNotes[topic.module][0]}</p><p className="mt-2"><b>Tushunganini so‘rang:</b> {teacherNotes[topic.module][1]}</p><p className="mt-2"><b>Ko‘p uchraydigan xato:</b> {teacherNotes[topic.module][2]}</p></div>
      <ol className="list-decimal space-y-2 pl-5 text-sm leading-6 text-slate-600"><li><b>Tahlil:</b> namunadagi mavzuga tegishli so‘z yoki shaklni toping. U qanday ma’no berishini tushuntiring.</li><li><b>Birga:</b> ustoz bilan namunani o‘qing, tartibini ayting. So‘ng namunani yopib pastdagi mashqni bajaring.</li><li><b>Mustaqil:</b> shu shaklda ikki yangi gap yoki birikma yozing; bittasida bugungi lug‘atdan foydalaning. Juftingiz tekshirsin.</li></ol>
      <details><summary className="cursor-pointer text-sm font-semibold text-blue-700">Namuna tiklash mashqi</summary><div className="mt-3"><Practice key={id} title={topic.title} questions={topicPractice(id)}/></div></details>
      <p className="text-xs leading-5 text-slate-500"><b>Ustoz tekshiruvi:</b> mavzuning shakli, ma’nosi va so‘z tartibi to‘g‘rimi? Erkin gaplar avtomatik baholanmaydi; bir nechta to‘g‘ri javob bo‘lishi mumkin.</p>
    </div>
  </details>;
}

const orientation = [
  [15,'Kurs bilan tanishuv','8 oy maqsadi, 6 kunlik dars va 2 soatlik uy ishini tushuntiring. Grammar, vocabulary va 4 ko‘nikma birga rivojlanishini ayting.'],
  [15,'Xarita va tartib','Xaritalarni oching. Eslash → mashq → tekshirish → xatoni qaytarish tartibini ko‘rsating. Kechikish, daftar, uy vazifasi va savol berish tartibini kelishib oling.'],
  [15,'Noun va adjective','Bugungi kartalardan ot va sifatni misollarda ajrating. Ikki o‘quvchi yangi misol keltirsin.'],
  [15,'Dastlabki 10 so‘z','Ovoz, ma’no va kulgili misolni ayting. Tarjimani yopib qaytartiring.'],
  [5,'Tanaffus','So‘zni mimika bilan ifodalash o‘yini.'],
  [15,'Keyingi so‘zlar','11–20 so‘zlarni o‘rgating; 21–25 bilan tanishtiring. Birinchi kunda tezlikdan ko‘ra tushunishni tekshiring.'],
  [15,'Mashqni birga bajarish','10 so‘zli mashqning birinchi savolini ustoz yechadi, qolganini juftlar bajaradi.'],
  [15,'Tinglash va gapirish','Quyidagi uch misolni o‘qing. So‘zlarni topishsin va o‘zlari sodda misol aytishsin.'],
  [10,'Uy ishini namoyish qilish','Bitta so‘zni qaytarish, gap yozish va xato daftarini yuritishni ko‘rsating.'],
] as const;

function Timeline({review,first}:{review:boolean;first:boolean}) {
  const stages=first?orientation:review?reviewTimeline:standardTimeline; let minute=0;
  return <ol className="space-y-3">{stages.map(([duration,title,instruction])=>{const start=minute;minute+=duration;return <li key={title} className="flex gap-3 rounded-xl bg-slate-50 p-3"><span className="w-16 shrink-0 pt-1 text-xs font-bold tabular-nums text-blue-600">{start}–{minute}<span className="block font-normal text-slate-400">daqiqa</span></span><div><h4 className="text-sm font-semibold text-slate-900">{title}</h4><p className="mt-1 text-sm leading-6 text-slate-600">{instruction}</p></div></li>;})}</ol>;
}

function Lesson({no,go}:{no:number;go:(no:number)=>void}) {
  const plan=lessonPlan(no);
  const [mode,setMode]=useState('plan'); const [vocabSize,setVocabSize]=useState(10); const [offset,setOffset]=useState(0);
  const pool=plan.review?shuffled(plan.words,plan.week).slice(0,20):plan.words.slice(offset,offset+vocabSize);
  return <section className="mt-5 space-y-4">
    <div className="rounded-2xl bg-slate-900 p-5 text-white md:p-7"><div className="flex items-center justify-between gap-3"><p className="text-xs font-semibold uppercase tracking-wider text-blue-300">{plan.month}-oy / {plan.week}-hafta / {plan.day}-kun</p><span className="flex items-center gap-1 text-sm"><Clock size={15}/>120 daqiqa</span></div><h2 className="mt-3 text-xl font-bold">{plan.no}-dars · {plan.review?'Takrorlash va nazorat':plan.topics[0]?.title}</h2><p className="mt-2 text-sm leading-6 text-slate-300">{plan.topics.length} grammar qadami · lug‘at {plan.start}–{plan.end} · uyda 120 daqiqa</p><div className="mt-4 flex gap-2"><button disabled={no===1} className="rounded-lg border border-slate-600 px-3 py-2 text-sm disabled:opacity-40" onClick={()=>go(no-1)}>← Oldingi dars</button><button disabled={no===192} className="rounded-lg border border-slate-600 px-3 py-2 text-sm disabled:opacity-40" onClick={()=>go(no+1)}>Keyingi dars →</button></div></div>
    {!plan.wordsReady&&<p role="status" className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900"><b>Material to‘liq emas.</b> Lug‘at oralig‘i {plan.start}–{plan.end}; hozir {plan.words.length} ta so‘z tayyor. Yetishmagan so‘zlar va mashqlar kiritilmaguncha darsni to‘liq tayyor deb olmang. Reja va grammar ochiq.</p>}
    <nav aria-label="Dars ichidagi bo‘limlar" className="grid grid-cols-2 gap-2 sm:grid-cols-4">{[['plan','Dars ssenariysi'],['grammar','Grammar va mashqlar'],['words','Vocabulary va mashqlar'],['homework','Uy vazifasi']].map(([key,label])=><button key={key} onClick={()=>setMode(key)} aria-pressed={mode===key} className={`${button} ${mode===key?'!border-blue-500 !bg-blue-50 !text-blue-700':''}`}>{label}</button>)}</nav>
    {mode==='plan'&&<><div className={panel}><h3 className="mb-3 font-bold">Darsdan oldin — 5 daqiqa</h3><ul className="list-disc space-y-2 pl-5 text-sm leading-6 text-slate-600"><li>Bugungi mavzu va javoblarni oching. Doska, daftar va taymerni tayyorlang.</li><li>Lug‘at oralig‘ini tekshiring; tayyor bo‘lmagan materialni topshiriq qilib bermang.</li><li>Kecha qiyin bo‘lgan 3 xatoni kirish mashqiga oling.</li></ul></div><div className={panel}><h3 className="mb-4 font-bold">Qachon, nima va qanday o‘tiladi?</h3><Timeline review={plan.review} first={no===1}/></div><div className={panel}><h3 className="font-bold">Reading / listening mikromatni</h3><p className="mt-2 text-sm leading-6 text-slate-500">Ustoz matnni yopib ikki marta o‘qiydi. Bu qisqa diktant va tushunish mashqi; alohida darajaviy reading yoki sertifikat mock testi emas.</p><div className="mt-3 space-y-2">{(plan.words.length?plan.words.slice(0,3).map(w=>w.example):plan.topics.slice(0,3).map(t=>t.example)).map((line,i)=><p key={i} className="rounded-lg bg-blue-50 p-3 text-sm text-blue-900">{i+1}. {line}</p>)}</div><p className="mt-3 text-sm text-slate-600">Kim yoki nima haqida? Qaysi so‘zlarni eshitdingiz? Ma’nosini ayting; matn bilan tekshiring.</p></div></>}
    {mode==='grammar'&&<><div className="space-y-2">{plan.topics.map(t=><TopicCard key={t.id} id={t.id}/>)}</div><Practice key={`g-${no}`} title="Bo‘lim yakunida — nazorat savollari" questions={plan.review?grammarReview(plan.moduleIds):grammarChecks(plan.moduleIds)}/><p className="text-xs leading-5 text-slate-500">Bo‘lim savollarini shu qoidalar o‘tilgandan keyin bering; oldindan baholamang.</p></>}
    {mode==='words'&&<>{plan.words.length?<><WordCards pool={plan.words}/><div className="flex flex-wrap gap-2">{[10,20].map(n=><button key={n} className={`${button} ${vocabSize===n?'!bg-blue-50':''}`} onClick={()=>{setVocabSize(n);setOffset(0);}}>{n} so‘z{n===20?' · aralash':''}</button>)}{!plan.review&&plan.words.length>vocabSize&&<button className={button} onClick={()=>setOffset(offset+vocabSize>=plan.words.length?0:offset+vocabSize)}>Keyingi to‘plam</button>}</div><Practice key={`v-${no}-${vocabSize}-${offset}`} title={`Lug‘at mashqi · ${pool[0]?.id}–${pool.at(-1)?.id}`} questions={vocabularyPractice(pool,vocabSize===20||plan.review)}/></>:<p className={panel}>Bu oraliqning lug‘ati hali kiritilmagan. Vocabulary bo‘limida mavjud so‘zlar bilan mashq qiling.</p>}</>}
    {mode==='homework'&&<><div className={panel}><h3 className="mb-4 font-bold">Uy vazifasi — 120 daqiqa</h3><ol className="space-y-4">{homework.map(([minutes,title,task])=><li key={title} className="border-l-2 border-blue-200 pl-4"><p className="text-sm font-bold">{title} · {minutes} daqiqa</p><p className="mt-1 text-sm leading-6 text-slate-600">{task}</p></li>)}</ol>{!plan.wordsReady&&<p className="mt-4 text-sm text-amber-800">Lug‘atga oid bandlarni faqat tayyor va o‘tilgan so‘zlar uchun bering.</p>}</div><div className={panel}><h3 className="font-bold">Keyingi darsdagi tekshiruv</h3><p className="mt-2 text-sm leading-6 text-slate-600">5 so‘zni xotiradan so‘rang; 2 yangi gapni izohlatib tekshiring. 80% dan kam bo‘lsa, aynan xato bandlarini qaytartiring. Erkin gaplarda shakl, ma’no va mustaqil ishlatishni alohida tekshiring.</p></div></>}
  </section>;
}

export default function IntensivePlans() {
  const [params,setParams]=useSearchParams();
  const tab=['course','grammar','vocabulary'].includes(params.get('tab')??'')?params.get('tab')!:'course';
  const rawNo=Number(params.get('lesson')); const no=Number.isFinite(rawNo)&&rawNo>=1&&rawNo<=192?Math.trunc(rawNo):1; const month=Math.ceil(no/24);
  const [query,setQuery]=useState(''); const [group,setGroup]=useState(0); const [size,setSize]=useState(10);
  const setTab=(next:string)=>{const p=new URLSearchParams(params);p.set('tab',next);setParams(p);setQuery('');};
  const go=(next:number)=>{const p=new URLSearchParams(params);p.set('lesson',String(next));p.set('tab','course');setParams(p);};
  const q=query.toLocaleLowerCase().trim(); const vocabPool=words.slice(group*size,group*size+size);
  const filtered=words.filter(w=>`${w.word} ${w.meaning} ${w.topic}`.toLocaleLowerCase().includes(q));
  const visibleModules=grammar.map((m,mi)=>({m,mi,items:topics.filter(t=>t.module===mi&&(!q||`${t.title} ${t.example} ${m.title} ${m.uz}`.toLocaleLowerCase().includes(q)))})).filter(x=>x.items.length);
  return <div className="mx-auto max-w-6xl p-4 md:p-8">
    <Link to="/plans" className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500"><ArrowLeft size={16}/>Dars rejalari / Standard English</Link>
    <header className="overflow-hidden rounded-2xl border border-slate-200 bg-white"><div className="p-5 md:p-7"><div className="flex items-center gap-2 text-xs font-bold tracking-widest text-blue-600"><img src={brand} alt="Jony" className="h-9 w-9"/>JONY INTENSIVE</div><h1 className="mt-4 text-3xl font-bold text-slate-900">Bitta yo‘l. Har dars aniq.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-slate-500">Ustoz uchun 8 oylik yo‘l: nimani o‘tish, qanday mashq qilish va uyga nima berish — bir joyda.</p><div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">{[['8 oy','32 o‘quv haftasi'],['192 dars','120 daqiqadan'],[`${topics.length} mavzu`,'Grammar xaritasi'],[`${words.length} / 4 000`,'Tayyor lug‘at / reja']].map(([value,label])=><div key={label} className="rounded-xl bg-slate-50 p-3"><b className="text-lg text-slate-900">{value}</b><p className="mt-1 text-xs text-slate-500">{label}</p></div>)}</div></div><div aria-hidden="true" className="h-8 bg-repeat-x bg-[length:auto_32px]" style={{backgroundImage:"url('/student-design/pattern.png')"}}/></header>
    <nav aria-label="Intensive bo‘limlari" className="my-5 grid grid-cols-3 gap-2">{[['course','Darslar'],['grammar','Grammar'],['vocabulary','Vocabulary']].map(([key,label])=><button key={key} aria-pressed={tab===key} onClick={()=>setTab(key)} className={`${button} ${tab===key?'!border-blue-600 !bg-blue-600 !text-white':''}`}>{label}</button>)}</nav>
    {tab==='course'&&<><p className="mb-4 text-sm leading-6 text-slate-500">32 o‘quv haftasi; qolgan kalendar kunlari bayram va qayta o‘tish uchun zaxira. Har 6-dars — takrorlash. Lug‘atning qolgan qismi va to‘liq ko‘nikma materiallari hali tayyorlanmoqda.</p><div className="grid grid-cols-4 gap-2 md:grid-cols-8">{monthNames.map((name,i)=><button key={name} title={name} aria-pressed={month===i+1} onClick={()=>go(i*24+1)} className={`${button} ${month===i+1?'!bg-blue-50 !text-blue-700 !border-blue-400':''}`}>{i+1}-oy</button>)}</div><h2 className="mb-3 mt-5 font-bold text-slate-900">{monthNames[month-1]}</h2><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{Array.from({length:4},(_,i)=>(month-1)*4+i+1).map(week=><div key={week} className="rounded-xl border border-slate-200 bg-white p-3"><p className="mb-2 text-xs font-bold text-slate-500">{week}-hafta · so‘zlar {(week-1)*125+1}–{week*125}</p><div className="grid grid-cols-3 gap-2">{Array.from({length:6},(_,i)=>(week-1)*6+i+1).map(n=><button key={n} onClick={()=>go(n)} aria-current={no===n?'step':undefined} className={`rounded-lg px-2 py-3 text-xs font-semibold ${no===n?'bg-blue-600 text-white':n%6===0?'bg-lime-50 text-lime-800':'bg-slate-50 text-slate-600'}`}>{n}-dars{n%6===0&&<span className="block text-[10px] font-normal">Takrorlash</span>}</button>)}</div></div>)}</div><Lesson key={no} no={no} go={go}/></>}
    {tab==='grammar'&&<><div className="mb-5 flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-bold">Grammar xaritasi va mashqlar</h2><a className={button} href="/intensive/jony-b2-grammar-map.pdf" download><Download size={16}/>Grammar PDF</a></div><SearchBox value={query} onChange={setQuery} label="Grammar mavzusini qidirish"/><div className="mt-4 space-y-3">{visibleModules.map(({m,mi,items})=><details key={`${mi}-${q}`} open={q?true:undefined} className="rounded-2xl border border-slate-200 bg-white"><summary className="cursor-pointer p-4"><BookOpen size={17} className="mr-2 inline text-blue-600"/><b>{mi+1}. {m.title}</b><span className="ml-2 text-xs text-slate-500">{items.length} mavzu</span></summary><div className="space-y-3 border-t border-slate-100 p-4"><p className="text-sm leading-6 text-slate-600">Natija: {m.goal}</p>{items.map(t=><TopicCard key={t.id} id={t.id}/>)}<Practice key={`module-${mi}`} title="Bo‘lim nazorati" questions={grammarChecks([mi])}/></div></details>)}{!visibleModules.length&&<p role="status" className={panel}>Mavzu topilmadi.</p>}</div><details className={`${panel} mt-5`}><summary className="cursor-pointer font-bold">Barcha bo‘limlardan aralash mashq</summary><div className="mt-4"><Practice title="Aralash grammatika · 27 bo‘lim" questions={grammarChecks(grammar.map((_,i)=>i))}/></div></details></>}
    {tab==='vocabulary'&&<><div className="mb-5 flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-xl font-bold">Vocabulary Map</h2><p className="mt-1 text-sm text-slate-500">Kulgili misol → eslash → 10 so‘z → 20 so‘zli takrorlash.</p></div><a className={button} href="/intensive/jony-vocabulary-001-500.pdf" download><Download size={16}/>500 so‘z PDF</a></div><div className="mb-4 rounded-xl bg-lime-50 p-4 text-sm leading-6 text-lime-900"><Sparkles size={17} className="mr-2 inline"/>So‘zni ayting, kulgili holatni tasavvur qiling, tarjimani yoping va o‘z gapingizni tuzing.</div><SearchBox value={query} onChange={setQuery} label="So‘z, tarjima yoki mavzu qidirish"/>{q?<div className="mt-4"><WordCards pool={filtered}/>{!filtered.length&&<p role="status" className={panel}>So‘z topilmadi.</p>}</div>:<><div className="my-4 flex flex-wrap gap-2">{[10,20].map(n=><button key={n} aria-pressed={size===n} className={`${button} ${size===n?'!bg-blue-50 !border-blue-400':''}`} onClick={()=>{setGroup(Math.floor(group*size/n));setSize(n);}}>{n} so‘z{n===20?' · aralash':''}</button>)}<label className="flex items-center gap-2 text-sm">To‘plam<select className="max-w-64 rounded-xl border border-slate-200 bg-white p-3" value={group} onChange={e=>setGroup(Number(e.target.value))}>{Array.from({length:Math.ceil(words.length/size)},(_,i)=><option key={i} value={i}>{i*size+1}–{Math.min((i+1)*size,words.length)} · {words[i*size].topic.split(' • ')[1]}</option>)}</select></label></div><WordCards key={`cards-${group}-${size}`} pool={vocabPool}/><div className="mt-5"><Practice key={`vp-${group}-${size}`} title={`${group*size+1}–${Math.min((group+1)*size,words.length)} so‘zlar mashqi`} questions={vocabularyPractice(vocabPool,size===20)}/></div></>}
    </>}
    <footer className="mt-8 border-t border-slate-200 pt-5 text-xs leading-5 text-slate-500">Qaytarish: ertasi kuni → 3-kuni → 7-kuni → oy yakunida. <a className="ml-2 text-blue-600 underline" href="/intensive/jony-intensive-teacher-guide.pdf" download>Ustoz qo‘llanmasi PDF</a> <a className="ml-2 text-blue-600 underline" href="/intensive/jony-intensive-vocabulary-workbook.pdf" download>Vocabulary mashqlari PDF</a> <a className="ml-2 text-blue-600 underline" href="/intensive/jony-intensive-grammar-workbook.pdf" download>Grammar mashqlari PDF</a></footer>
  </div>;
}
function SearchBox({value,onChange,label}:{value:string;onChange:(value:string)=>void;label:string}) {return <label className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3"><Search size={17} className="text-slate-400"/><input type="search" value={value} onChange={e=>onChange(e.target.value)} aria-label={label} placeholder={label} className="w-full min-w-0 bg-transparent text-sm outline-none"/></label>;}
