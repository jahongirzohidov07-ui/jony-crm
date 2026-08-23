/**
 * O'RGATUVCHI MO'LJALLARI TEKSHIRUVI (2026-08-23).
 *
 * Har bir dars qadami ekrandagi bitta joyni ko'rsatadi — o'sha joy
 * `data-guide="..."` bilan belgilangan bo'lishi kerak. Agar belgi
 * bo'lmasa, xodim dars o'rtasida "bu joy ko'rinmayapti" degan sariq
 * ogohlantirishga duch keladi. Buni QO'LDA sezish qiyin, shuning
 * uchun shu tekshiruv bor.
 *
 * Ishga tushirish:  node src/lib/guide/anchors.check.mjs
 */
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

function walk(dir, out = []) {
  for (const f of readdirSync(dir)) {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p, out);
    else if (p.endsWith(".tsx")) out.push(p);
  }
  return out;
}

const src = readFileSync("src/lib/guide/lessons.ts", "utf8");
const targets = [...src.matchAll(/target:\s*"([^"]+)"/g)].map((m) => m[1]);

// Barcha belgilar: to'g'ridan-to'g'ri yozilganlari va prefiksli
// dinamiklari (masalan data-guide={"stab-" + t.key}).
const literal = new Set();
const prefixes = [];
for (const file of walk("src")) {
  const t = readFileSync(file, "utf8");
  for (const m of t.matchAll(/data-guide=\{?"([^"]+)"/g)) literal.add(m[1]);
  for (const m of t.matchAll(/data-guide=\{"([^"]+)"\s*\+/g)) prefixes.push(m[1]);
  for (const m of t.matchAll(/data-guide=\{\w+\s*===\s*0\s*\?\s*"([^"]+)"/g))
    literal.add(m[1]);
}

const missing = [...new Set(targets)].filter(
  (t) => !literal.has(t) && !prefixes.some((p) => t.startsWith(p))
);

if (missing.length) {
  console.log("XATO — bu mo'ljallar ekranda yo'q:", missing.join(", "));
  process.exit(1);
}
console.log(`OK — ${new Set(targets).size} ta mo'ljalning hammasi topildi`);
