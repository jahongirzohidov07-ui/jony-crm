import { createServer } from 'vite';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const server=await createServer({root,server:{middlewareMode:true},appType:'custom'});
try {
 const {russianLessonPlan,russianScaffoldedPractice}=await server.ssrLoadModule('/src/lib/russianTeaching.ts');
 const data=Array.from({length:144},(_,i)=>({no:i+1,plan:russianLessonPlan(i+1,12),practice:russianScaffoldedPractice(i+1)}));
 await mkdir(path.join(root,'_inbox'),{recursive:true});
 await writeFile(path.join(root,'_inbox/russian-teaching-export.json'),JSON.stringify(data,null,2));
 console.log('Exported 144 teacher plans and practice sets for PDFs.');
} finally { await server.close(); }
