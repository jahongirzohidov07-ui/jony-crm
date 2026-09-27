// JonyOS xodim ilovasi: har rol uchun pastki menyu faqat OCHIQ bo'limlarga olib borishini,
// har bandning ikonkasi borligini tekshiradi (2026-09-27, 747 tekshiruv).
// Ishga tushirish: npx esbuild scripts/app_nav_check.ts --bundle --platform=node --outfile=/tmp/c.js --alias:lucide-react=./scripts/lucide_stub.cjs && node /tmp/c.js
import { buildNav } from "../src/components/navItems";
import { buildTabs, appHref, ROUTE_GEM, gemFor } from "../src/pages/app/appNav";
import { GEM } from "../src/pages/app/gemIcons";
import { ALL_ROLES, ADMINISTRATOR, TASK_ACCESS, can } from "../src/lib/roles";
let ok=0, bad=0; const fail=(m:string)=>{bad++;console.log("XATO:",m)}; const pass=()=>ok++;
for (const r of [...ALL_ROLES, ADMINISTRATOR].filter(r=>r!=="student"&&r!=="parent")) for (const t of [false,true]) {
  const nav = buildNav({role:r},{onTestBranch:t});
  const allowed = new Set(nav.map(i=>appHref(i.to)));
  const {tabs, fab} = buildTabs(r, nav, can(r, TASK_ACCESS));
  for (const x of tabs) { if (x.to.startsWith("/app/p") && !allowed.has(x.to)) fail(r+" tab ruxsatsiz: "+x.to); else pass(); }
  if (fab) { if (fab.to.startsWith("/app/p") && !allowed.has(fab.to)) fail(r+" fab ruxsatsiz "+fab.to); else pass(); }
  if (new Set(tabs.map(x=>x.to)).size!==tabs.length) fail(r+" takror tab"); else pass();
  if (fab && tabs.some(x=>x.to===fab.to)) fail(r+" fab tab bilan takror"); else pass();
  if (tabs.length<3||tabs.length>4) fail(r+" tab soni "+tabs.length); else pass();
  for (const i of nav) { if (i.to!=="/" && !ROUTE_GEM[i.to]) fail(r+" ikonkasiz: "+i.to); else pass(); }
  if (t===false) console.log(r.padEnd(18), tabs.map(x=>x.label).join(" | "), "|| FAB:", fab?.label||"-");
}
for (const k of new Set([...Object.values(ROUTE_GEM),"home","task","grid","user","bell","warn","fire","check","lock","open","logout","search","back","chat"])) { if (!GEM[k]) fail("GEM yo'q: "+k); else pass(); }
if (gemFor("/nomalum")!=="grid") fail("gemFor"); else pass();
console.log("OK:",ok,"XATO:",bad);
