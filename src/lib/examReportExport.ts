import { type MonthlyExamReport, type ExamReportKind, reportTitles, monthLabel, percent } from "./examReport";
export const REPORT_PAGE_SIZE = 20;
export function reportCanvas(d: MonthlyExamReport, kind: ExamReportKind, page: number) {
  const canvas = document.createElement("canvas"); canvas.width=1200; canvas.height=1697;
  const c=canvas.getContext("2d")!;
  const text=(s:string,x:number,y:number,size=20,color="#172b4d",bold=false) => { c.fillStyle=color; c.font=`${bold?700:400} ${size}px Arial, sans-serif`; c.fillText(s,x,y); };
  const box=(x:number,y:number,w:number,h:number,color:string) => {c.fillStyle=color;c.fillRect(x,y,w,h);};
  const wrap=(s:string,x:number,y:number,w:number,size=18) => {
    c.font=`${size}px Arial, sans-serif`; let line="", lines:string[]=[];
    for(const word of s.split(/\s+/)) {const next=line?`${line} ${word}`:word;if(c.measureText(next).width>w && line){lines.push(line);line=word;}else line=next;}lines.push(line);
    if(lines.length>2) {lines=lines.slice(0,2);while(c.measureText(lines[1]+"…").width>w)lines[1]=lines[1].slice(0,-1);lines[1]+="…";}
    lines.forEach((l,i)=>text(l,x,y+i*(size+5),size));
  };
  box(0,0,1200,1697,"#f5f7fb");box(0,0,1200,275,"#102747");box(60,55,7,42,"#4b9cff");
  text("JonyOS",84,87,36,"#ffffff",true);text("JONY ACADEMY  /  IMTIHON HISOBOTI",60,141,17,"#b5c9e5");
  text(reportTitles[kind],60,195,42,"#ffffff",true);text(`${monthLabel(d.period)} · ${d.teacher || d.scope}`,60,235,21,"#d4e2f3");
  const summary=[["O'RTACHA NATIJA",percent(d.avg)],["TESTLAR",String(d.exams)],["O'QUVCHILAR",String(d.students??0)]];
  summary.forEach(([label,value],i)=>{box(60+i*365,310,350,110,"#ffffff");text(label,82+i*365,344,15,"#667a96");text(value,82+i*365,391,35,i===0?"#1267d6":"#172b4d",true);});
  const rows=d[kind], totalPages=Math.max(1,Math.ceil(rows.length/REPORT_PAGE_SIZE));
  const group=kind==="by_group", student=kind==="by_student";
  const cols=group?[60,115,355,625,805,940,1040]:[60,120,560,925,1040];
  const heads=group?["#","GURUH","USTOZ","FILIAL","DARAJA","TEST","NATIJA"]:["#",student?"O'QUVCHI":kind==="by_branch"?"FILIAL":"USTOZ",student?"GURUH":"FILIAL","TEST","NATIJA"];
  box(60,450,1080,52,"#e6edf7");heads.forEach((h,i)=>text(h,cols[i]+10,483,15,"#516984",true));
  rows.slice(page*REPORT_PAGE_SIZE,(page+1)*REPORT_PAGE_SIZE).forEach((r,i)=>{
    const y=502+i*50, rank=page*REPORT_PAGE_SIZE+i+1;
    box(60,y,1080,49,rank===1?"#fff4d4":i%2?"#f0f4fa":"#ffffff");
    text(String(rank),cols[0]+12,y+31,18,rank<=3?"#ab7612":"#8190a5",true);
    if(group){wrap(r.label,125,y+20,220,16);wrap(r.teacher||"—",365,y+20,245,16);wrap(r.branch||"—",635,y+20,150,16);wrap(r.level||"—",815,y+20,110,16);}
    else{wrap(r.label,130,y+20,410,18);wrap(student?(r.group||"—"):(r.branch||"—"),570,y+20,330,17);}
    text(String(r.exams),group?950:935,y+31,18);text(percent(r.avg),1050,y+31,20,(r.avg??0)>=d.standard?"#078364":"#b94b42",true);
  });
  if(!rows.length)text("Bu oyda imtihon natijalari yo'q",85,555,24,"#667a96");
  box(60,1530,1080,64,"#102747");text("UMUMIY TA'LIM NATIJASI",82,1570,19,"#d4e2f3",true);text(percent(d.avg),1015,1573,28,"#ffffff",true);
  text("O'rtacha: hisobga olingan natijalar yig'indisi / natijalar soni.",60,1628,16,"#667a96");
  text("Kelmagan va hisobga olinmagan natijalar o'rtachaga kirmaydi.",60,1655,16,"#667a96");
  text(`${page+1} / ${totalPages}`,1080,1655,17,"#667a96");return canvas;
}
// A4 PDF with one high-resolution report image per page; Unicode remains intact.
export function reportPdf(d: MonthlyExamReport, kind: ExamReportKind): Blob {
  const n=Math.max(1,Math.ceil(d[kind].length/REPORT_PAGE_SIZE));const enc=new TextEncoder();const objects:Uint8Array[]=[];
  const bytes=(s:string)=>enc.encode(s);const combine=(parts:Uint8Array[])=>{const out=new Uint8Array(parts.reduce((s,b)=>s+b.length,0));let at=0;for(const b of parts){out.set(b,at);at+=b.length;}return out;};
  objects.push(bytes("<< /Type /Catalog /Pages 2 0 R >>"));
  objects.push(bytes(`<< /Type /Pages /Count ${n} /Kids [${Array.from({length:n},(_,i)=>`${3+i*3} 0 R`).join(" ")}] >>`));
  for(let i=0;i<n;i++) {const id=3+i*3;const canvas=reportCanvas(d,kind,i);const raw=atob(canvas.toDataURL("image/jpeg",0.94).split(",")[1]);const jpg=Uint8Array.from(raw,ch=>ch.charCodeAt(0));
    objects.push(bytes(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.28 841.89] /Resources << /XObject << /Im ${id+1} 0 R >> >> /Contents ${id+2} 0 R >>`));
    objects.push(combine([bytes(`<< /Type /XObject /Subtype /Image /Width 1200 /Height 1697 /ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length ${jpg.length} >>\nstream\n`),jpg,bytes("\nendstream")]));
    const content="q 595.28 0 0 841.89 0 0 cm /Im Do Q";objects.push(bytes(`<< /Length ${content.length} >>\nstream\n${content}\nendstream`));
  }
  const parts=[bytes("%PDF-1.4\n")],offsets=[0];let offset=parts[0].length;
  objects.forEach((obj,i)=>{offsets.push(offset);const part=combine([bytes(`${i+1} 0 obj\n`),obj,bytes("\nendobj\n")]);parts.push(part);offset+=part.length;});
  parts.push(bytes(`xref\n0 ${objects.length+1}\n0000000000 65535 f \n${offsets.slice(1).map(o=>`${String(o).padStart(10,"0")} 00000 n \n`).join("")}trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${offset}\n%%EOF`));
  return new Blob([combine(parts)],{type:"application/pdf"});
}
