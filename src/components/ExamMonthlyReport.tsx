import { useEffect, useState } from "react";
import { ChevronDown, Download, FileImage, FileText, X } from "lucide-react";
import { api } from "../lib/api";
import { BranchPicker, branchParam } from "./BranchPicker";
import { type MonthlyExamReport, type ExamSummary, type ExamTest, type ExamReportKind, reportTitles, percent, monthLabel, localMonth } from "../lib/examReport";
import { reportCanvas, reportPdf, REPORT_PAGE_SIZE } from "../lib/examReportExport";

export default function ExamMonthlyReport({ branchId, own=false }: { branchId?: number | null; own?: boolean }) {
  const [period,setPeriod]=useState(localMonth);const [localBranch,setLocalBranch]=useState<number|null>(null);
  const branch=branchId===undefined?localBranch:branchId;
  const [data,setData]=useState<MonthlyExamReport|null>(null),[error,setError]=useState("");
  const [loading,setLoading]=useState(true),[retry,setRetry]=useState(0);
  const [preview,setPreview]=useState<ExamReportKind|null>(null);
  const [search,setSearch]=useState(""),[limit,setLimit]=useState(50);
  useEffect(()=>{let live=true;setLoading(true);setError("");setPreview(null);setLimit(50);
    api.get<MonthlyExamReport>(`${own?"/teacher/exam-history":"/reports/exams-monthly"}?period=${period}${own?"":branchParam(branch)}`)
      .then(d=>{if(live)setData(d);}).catch(e=>{if(live)setError(e instanceof Error?e.message:"Hisobot yuklanmadi");}).finally(()=>{if(live)setLoading(false);});
    return()=>{live=false;};
  },[period,branch,own,retry]);
  return <section className="space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><h2 className="font-semibold text-slate-900">{own?"Imtihonlarim — oylik tarix":"Oylik imtihon hisoboti"}</h2><p className="text-xs text-slate-500 mt-1">Ustoz yoki guruhni bosib, test natijalarini oching.</p></div>
      <div className="flex flex-wrap gap-2"><label className="text-xs text-slate-500">Hisobot oyi<input aria-label="Hisobot oyi" type="month" value={period} onChange={e=>{if(e.target.value)setPeriod(e.target.value);}} className="block rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800" /></label>{!own&&branchId===undefined&&<BranchPicker value={localBranch} onChange={setLocalBranch}/>}</div>
    </div>
    {loading?<p className="py-8 text-sm text-slate-400">Hisobot tayyorlanmoqda…</p>:error?<div role="alert" className="p-4 bg-red-50 rounded-xl text-red-700">{error}<button className="ml-3 underline" onClick={()=>setRetry(v=>v+1)}>Qayta urinish</button></div>:data&&<>
      {own&&data.history.length>0&&<div className="flex gap-2 overflow-x-auto pb-2" aria-label="Oylik natijalar tarixi">{data.history.map(h=><button key={h.period} onClick={()=>setPeriod(h.period)} className={`min-w-36 text-left rounded-xl border p-3 ${period===h.period?"border-blue-400 bg-blue-50":"border-slate-200 bg-white"}`}><span className="block text-xs text-slate-500">{monthLabel(h.period)}</span><strong className="text-lg text-slate-900">{percent(h.avg)}</strong><span className="block text-xs text-slate-500">{h.groups} guruh · {h.exams} test</span></button>)}</div>}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{[["O'rtacha natija",percent(data.avg)],["Testlar",data.exams],["Guruhlar",data.groups??0],["O'quvchilar",data.students??0]].map(([label,value])=><div key={label} className="rounded-xl border border-slate-200 bg-white p-4"><p className="text-xs text-slate-500">{label}</p><strong className="block text-2xl text-slate-900 mt-1">{value}</strong></div>)}</div>
      <p className="text-xs text-slate-500">{monthLabel(period)} · {data.results} ta hisobga olingan natija. O'rtacha har bir natija bo'yicha hisoblanadi; kelmagan va hisobga olinmagan ballar qo'shilmaydi.</p>
      {!data.exams&&<p className="rounded-xl border border-dashed p-8 text-center text-slate-500">Bu oyda yakunlangan test natijasi yo'q. Boshqa oyni tanlashingiz mumkin.</p>}
      <div className={`grid gap-4 ${own?"":"xl:grid-cols-3"}`}>
        {!own&&<Ranking kind="by_teacher" data={data} onExport={setPreview}/>}
        <Ranking kind="by_group" data={data} onExport={setPreview}/>
        {!own&&<Ranking kind="by_branch" data={data} onExport={setPreview}/>}
      </div>
      <details className="rounded-xl border border-slate-200 bg-white p-4"><summary className="cursor-pointer font-semibold text-slate-800">O'quvchilar kesimida ({data.by_student.length})</summary>
        <div className="flex flex-wrap justify-between gap-2 my-3"><input aria-label="O'quvchi qidirish" placeholder="O'quvchi ismi…" value={search} onChange={e=>{setSearch(e.target.value);setLimit(50);}} className="border rounded-lg px-3 py-2 text-sm"/><button onClick={()=>setPreview("by_student")} className="text-sm text-blue-700 flex items-center gap-1"><Download size={15}/> PDF / Rasm</button></div>
        {data.by_student.filter(s=>s.label.toLocaleLowerCase().includes(search.toLocaleLowerCase())).slice(0,limit).map(s=><details key={s.key} className="border-t py-2"><summary className="cursor-pointer text-sm flex justify-between gap-2"><span>{s.label}<small className="block text-slate-400">{s.group} · {s.exams} test</small></span><strong>{percent(s.avg)}</strong></summary><div className="bg-slate-50 rounded-lg p-3 mt-2 space-y-2">{data.tests.filter(t=>s.test_ids.includes(t.key)).map(t=>{const m=t.members.find(m=>m.key===s.key)!;return <div key={t.key} className="text-xs flex justify-between gap-2"><span>{t.date} · {t.label}</span><span>{m.absent?"Kelmadi":percent(m.percent)}{!m.absent&&!m.counted?" · hisobga olinmagan":""}</span></div>;})}</div></details>)}
        {data.by_student.filter(s=>s.label.toLocaleLowerCase().includes(search.toLocaleLowerCase())).length>limit&&<button onClick={()=>setLimit(v=>v+50)} className="text-sm text-blue-700 mt-3">Yana ko'rsatish</button>}
      </details>
      {preview&&<ExportPreview data={data} kind={preview} onClose={()=>setPreview(null)}/>}
    </>}
  </section>;
}
function Ranking({kind,data,onExport}:{kind:ExamReportKind;data:MonthlyExamReport;onExport:(k:ExamReportKind)=>void}) {
  return <div className="rounded-xl border border-slate-200 bg-white p-4 min-w-0"><div className="flex items-start justify-between gap-2 mb-3"><div><h3 className="font-semibold text-slate-800">{reportTitles[kind]}</h3><p className="text-xs text-slate-400">{monthLabel(data.period)}</p></div><button title="PDF yoki rasm yuklash" aria-label={`${reportTitles[kind]} — PDF yoki rasm`} onClick={()=>onExport(kind)} className="p-2 rounded-lg bg-blue-50 text-blue-700"><Download size={17}/></button></div>
    {!data[kind].length&&<p className="py-5 text-sm text-slate-400">Natija yo'q</p>}
    {data[kind].map((r,i)=><details key={r.key??"unset"} className="group border-t border-slate-100"><summary className="cursor-pointer flex items-center gap-2 py-3 list-none"><span className="text-xs text-slate-400 w-5">{i+1}</span><span className="flex-1 min-w-0 text-sm text-slate-700">{r.label}<span className="block text-xs text-slate-400 mt-1">{r.exams} test · {r.results} natija{kind!=="by_group"?` · ${r.groups} guruh`:""}</span></span><strong className={`text-sm ${(r.avg??0)>=data.standard?"text-emerald-600":"text-red-600"}`}>{percent(r.avg)}</strong><ChevronDown size={14} className="text-slate-400 shrink-0"/></summary><div className="bg-slate-50 rounded-lg px-3 pb-3 mb-3"><Breakdown kind={kind} row={r} data={data}/></div></details>)}
  </div>;
}
function Breakdown({kind,row,data}:{kind:ExamReportKind;row:ExamSummary;data:MonthlyExamReport}) {
  const tests=data.tests.filter(t=>row.test_ids.includes(t.key));
  if(kind==="by_group")return <Tests tests={tests}/>;
  const groups=[...new Set(tests.map(t=>t.group_id))];
  return <>{groups.map(id=>{const tt=tests.filter(t=>t.group_id===id);const vals=tt.flatMap(t=>t.members.filter(m=>m.counted).map(m=>m.percent!));const avg=vals.length?Math.round(vals.reduce((a,b)=>a+b,0)/vals.length*10)/10:null;return <details key={id} className="border-b border-slate-200 last:border-0 py-2"><summary className="text-xs cursor-pointer"><strong>{tt[0].group}</strong><span className="block text-slate-500 mt-1">{tt.length} test · {percent(avg)}</span></summary><Tests tests={tt}/></details>;})}</>;
}
function Tests({tests}:{tests:ExamTest[]}) {return <>{tests.map(t=><details key={t.key} className="py-2 border-b border-slate-200 last:border-0"><summary className="cursor-pointer text-xs"><span className="font-medium text-slate-800">{t.label}{t.retake?" · qayta topshirish":""}</span><span className="block text-slate-500 mt-1">{t.date} · {percent(t.avg)} · {t.results} natija · {t.absent} kelmagan</span></summary><div className="mt-2 space-y-2">{t.members.map(m=><div key={m.key} className="flex justify-between gap-2 text-xs"><span>{m.label}</span><span>{m.absent?"Kelmadi":percent(m.percent)}{!m.absent&&!m.counted?" *":""}</span></div>)}<p className="text-[10px] text-slate-400">* O'rtachaga kiritilmagan</p></div></details>)}</>;}
function ExportPreview({data,kind,onClose}:{data:MonthlyExamReport;kind:ExamReportKind;onClose:()=>void}) {
  const [page,setPage]=useState(0),[image,setImage]=useState(""),[pdfUrl,setPdfUrl]=useState(""),[error,setError]=useState("");
  const pages=Math.max(1,Math.ceil(data[kind].length/REPORT_PAGE_SIZE));
  const name=`JonyOS-${data.period}-${kind}`;
  useEffect(()=>{setImage(reportCanvas(data,kind,page).toDataURL("image/png"));},[data,kind,page]);
  useEffect(()=>{
    let url="";setPdfUrl("");setError("");
    const timer=setTimeout(()=>{try {url=URL.createObjectURL(reportPdf(data,kind));setPdfUrl(url);}catch(e){setError(e instanceof Error?e.message:"PDF tayyorlanmadi");}},20);
    return()=>{clearTimeout(timer);if(url)URL.revokeObjectURL(url);};
  },[data,kind]);
  useEffect(()=>{const close=(e:KeyboardEvent)=>{if(e.key==="Escape")onClose();};window.addEventListener("keydown",close);return()=>window.removeEventListener("keydown",close);},[onClose]);
  return <div role="dialog" aria-modal="true" aria-label="Hisobotni yuklash" className="fixed inset-0 z-[100] bg-slate-900/70 overflow-y-auto p-3 md:p-6"><div className="max-w-4xl mx-auto rounded-2xl bg-white p-4"><div className="flex flex-wrap justify-between items-center gap-2 mb-4"><h3 className="font-semibold">{reportTitles[kind]}</h3><button autoFocus aria-label="Yopish" onClick={onClose} className="p-2"><X size={20}/></button></div><div className="flex flex-wrap gap-2 mb-4"><a href={pdfUrl||undefined} download={`${name}.pdf`} aria-disabled={!pdfUrl} className={`bg-blue-600 text-white rounded-lg px-4 py-2 text-sm flex items-center gap-2 ${pdfUrl?"":"opacity-50 pointer-events-none"}`}><FileText size={16}/> PDF — barcha {pages} bet</a><a href={image||undefined} download={`${name}-${page+1}.png`} className="border rounded-lg px-4 py-2 text-sm flex items-center gap-2"><FileImage size={16}/> Rasm — {page+1}-bet</a><select aria-label="Hisobot beti" value={page} onChange={e=>setPage(Number(e.target.value))} className="border rounded-lg px-3 text-sm">{Array.from({length:pages},(_,i)=><option value={i} key={i}>{i+1} / {pages}-bet</option>)}</select></div>{error&&<p role="alert" className="text-red-600">{error}</p>}{!pdfUrl&&!error&&<p className="text-sm text-slate-500 mb-2">PDF tayyorlanmoqda…</p>}<img src={image||undefined} alt={`${reportTitles[kind]} — ${monthLabel(data.period)}, ${page+1}-bet`} className="w-full rounded-lg border"/></div></div>;
}
