/**
 * IMTIHON MATNI — Cambridge IELTS kitoblaridagi ko'rinish (2026-09-27).
 *
 * Jahongir: "men senga cambridge 19-18larni berdim xuddi shunday
 * savollar, instructionslar questionlarni formati, ham yozilishlari
 * farq qilsin tushunishga qiyin bolyabdi hozir, Headline ham bold
 * kattaroq harflarda bolishi kerak readingda".
 *
 * Bazada ko'rsatma bo'lim uchun BITTA matn ("READING PASSAGE 1 ... — — —
 * Questions 1-7 ... Questions 8-13 ..."). Bu fayl uni tuzilmaga ajratadi,
 * chizish esa components/ExamText.tsx da. Faqat ko'rinish — ma'lumot
 * o'zgarmaydi. Cambridge 19 dagi qoidalar:
 *   "Questions 8–13"              — kursiv sarlavha, guruh o'z savollari
 *                                   OLDIDA turadi (hammasi tepada emas);
 *   "Complete the notes below." /
 *   "Write your answers in ..."   — kursiv ko'rsatma;
 *   "Which paragraph contains…?"  — tik (savol o'zagi);
 *   ONE WORD ONLY, TWO, A–G       — qalin;
 *   TRUE / FALSE / NOT GIVEN      — jadval, kalit so'z qalin;
 *   NB                            — qalin;
 *   eslatma / ro'yxat / jadval    — ramkada, sarlavhasi qalin o'rtada.
 * Matn (passage): sarlavha katta qalin, kichik kirish kursiv, paragraf
 * harflari (A, B, C …) qalin chap chetda.
 *
 * Sof TypeScript (JSX yo'q) — node bilan to'g'ridan-to'g'ri sinaladi.
 */

/** Qatordagi bo'lak: oddiy / qalin / bo'sh joy (gap, raqami bilan). */
export type Run = { t: string; b?: boolean; gap?: boolean };

export type InsLine =
  | { k: "heading"; runs: Run[] } //   READING PASSAGE 1 / PART 2
  | { k: "ins"; runs: Run[] } //       kursiv ko'rsatma
  | { k: "stem"; runs: Run[] } //      tik savol o'zagi
  | { k: "key"; key: string; runs: Run[] } // TRUE  if the statement…
  | { k: "nb"; runs: Run[] }; //        NB  You may use…

export type Opt = { letter: string; runs: Run[] };

export type BoxLine =
  | { k: "title"; runs: Run[] }
  | { k: "sub"; runs: Run[] }
  | { k: "bullet"; level: 1 | 2; runs: Run[] }
  | { k: "opt"; opt: Opt }
  | { k: "opts"; opts: Opt[] }
  | { k: "text"; runs: Run[] };

export type Group = {
  /** "Questions 14-19" dagi 14 va 19 (sarlavhasiz kirish qismida null) */
  from: number | null;
  to: number | null;
  /** Ko'rinadigan sarlavha: "Questions 14–19" */
  label: string | null;
  lines: InsLine[];
  /** Ramkadagi qism (eslatma, ro'yxat, jadval) */
  box: BoxLine[];
};

// ------------------------------------------------------------ yordamchi
const DASH = "–";

/** "1-7" -> "1–7", "A-H" -> "A–H" (faqat ko'rinish uchun). */
export function dashRanges(s: string): string {
  return s
    .replace(/(\d)\s*-\s*(\d)/g, `$1${DASH}$2`)
    .replace(/\b([A-Z])\s*-\s*([A-Z])\b/g, `$1${DASH}$2`)
    .replace(/\b([ivx]{1,4})-([ivx]{1,5})\b/g, `$1${DASH}$2`);
}

const SEP_RE = /^[\s—–\-_*•·=~�]+$/;
// "Questions 1-7", "Question 36", "Questions 26 and 27", shuningdek bir
// qatorda davomi bilan: "Questions 11-13: Choose the correct letter…"
const HEADER_RE = /^Questions?\s+(\d{1,3})(?:\s*(-|–|—|to|and)\s*(\d{1,3}))?\s*(?:[.:]\s*(.*))?$/i;
// Faqat yalang'och sarlavha: "READING PASSAGE 1", "PART 2."
const HEADING_RE = /^(READING PASSAGE|PASSAGE|PART|SECTION|TEXT)\s+\d+[.:]?$/;
// "READING PASSAGE 1. Answer Questions 1-16, …" — ikkiga ajratiladi
const HEADING_REST_RE = /^((?:READING PASSAGE|PASSAGE|PART|SECTION|TEXT)\s+\d+)[.:]\s+(\S.*)$/;
const KEY_RE = /^(NOT GIVEN|TRUE|FALSE|YES|NO)(?:\t+|\s{2,}|\s+(?=if\b|-\s|–\s))\s*(.+)$/;
const NB_RE = /^NB\b[\s:.]*(.*)$/;
const INS_RE =
  /^(Complete|Choose|Write|Label|Match|Look at|In boxes|Answer|Classify|Decide|Mark|Each|For each|For questions?|Using|Use|Read|You should spend|You may|You will|You hear|You are going|You must|There (?:are|is)|Select|Circle|Tick|Fill|Give|Listen|Note|Put|Find|Identify|Number)\b/i;
const STEM_START_RE =
  /^(Do the following|Which|What|When|Where|Who|Whom|Whose|Why|How|Reading Passage \d+ has|The (?:reading )?passage has|The text has|This passage has)\b/i;

const BULLET_RE = /^([•●▪◦·]|-|–|—|\*)\s+(.*)$/;
// "A\tMarta Ilves", "A  Your weekdays…" — bitta harf + tab / 2+ bo'shliq
const OPT_RE = /^([A-Z]|[ivx]{1,4})(?:\t+|\s{2,})(\S.*)$/;
// "A  January     B  March", "A\tdonations\tB  honesty", "A) True   B) False"
const OPTS_SPLIT_RE = /(?:\t+|\s{3,}|\s{2,}(?=[A-Z]\)))(?=[A-Z](?:\t|\s{2,}|\)\s)\S)/;
const OPT_ANY_RE = /^([A-Z])(?:\t+|\s{2,}|\)\s+)(\S.*)$/;
// Bitta bo'shliqli ro'yxat ("A Jerry Siegel", "i Comparing two planets")
// — faqat A, B, C … / i, ii, iii … tartibda kelsa (aks holda artikl "A")
const SOFT_OPT_RE = /^([A-Z]|[ivx]{1,4})[.)]?\s+(\S.*)$/;
const ROMAN_LC = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii"];
const GAP_TEST_RE = /(_{3,}|\.{5,}|…{2,}|…\.{2,}|\.{2,}…)/;

/** Nuqta / "…" ketma-ketligi haqiqiy bo'sh joymi ("..." oddiy ko'p nuqta). */
function isGap(g: string): boolean {
  if (g.includes("_")) return true;
  const ell = (g.match(/…/g) || []).length;
  const dots = (g.match(/\./g) || []).length;
  return ell >= 2 || dots >= 5 || (ell >= 1 && dots >= 2);
}

/** Qatordan bo'sh joylarni (gap) ajratadi: "8 _____", "……", "......",
 *  aralash "…………..". num=false — oldidagi raqam savol raqami emas
 *  ("Address: 27 ____"). */
function withGaps(s: string, inner: (t: string) => Run[], num = true): Run[] {
  const out: Run[] = [];
  const re = num
    ? /(?:\b(\d{1,3})\s*)?(_{3,}|[.…](?:\s?[.…])+)/g
    : /()(_{3,}|[.…](?:\s?[.…])+)/g;
  let pos = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(s))) {
    if (!isGap(m[2])) continue;
    if (m.index > pos) out.push(...inner(s.slice(pos, m.index)));
    out.push({ t: m[1] || "", gap: true });
    pos = m.index + m[0].length;
  }
  if (pos < s.length) out.push(...inner(s.slice(pos)));
  return out;
}

/** Qo'shni bir xil bo'laklarni birlashtiradi. */
function merge(runs: Run[]): Run[] {
  const out: Run[] = [];
  for (const r of runs) {
    if (!r.t && !r.gap) continue;
    const last = out[out.length - 1];
    if (last && !last.gap && !r.gap && !!last.b === !!r.b) last.t += r.t;
    else out.push({ ...r });
  }
  return out;
}

// Katta harfli so'zlar ketma-ketligi: "ONE WORD AND/OR A NUMBER", "NOT GIVEN".
// Apostrof faqat katta harflar orasida — "I'm", "O'qing" qalin bo'lmasin.
const CAPS_WORD = "[A-Z](?:['’]?[A-Z])+(?:\\/[A-Z]+)*";
const CAPS_RUN_RE = new RegExp(`\\b${CAPS_WORD}(?:\\s+(?:${CAPS_WORD}|A(?=\\s+[A-Z]{2})))*\\b`, "g");
// Yakka katta so'z faqat shu ro'yxatda bo'lsa qalin (Cambridge javob
// cheklovlari); NREM, CEFR, IELTS, BBC kabi qisqartmalar oddiy qoladi
const KEY_WORDS = new Set([
  "TRUE", "FALSE", "YES", "NO", "NOT", "GIVEN", "NB", "ONLY", "ONCE", "BOTH", "EACH",
  "ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN", "EIGHT", "NINE", "TEN",
  "WORD", "WORDS", "NUMBER", "NUMBERS", "AND/OR", "EXTRA", "MORE", "ALL", "NONE",
]);
const capsBold = (t: string) => /\s/.test(t.trim()) || KEY_WORDS.has(t.trim());
// A–H, A, B or C, A, B, C or D
const LETTERS_RE =
  /\b[A-Z]\s*[–-]\s*[A-Z]\b|\b[A-Z](?:\s*,\s*[A-Z])*,?\s+(?:or|and)\s+[A-Z]\b(?![a-z])|\b[ivx]{1,4}\s*[–-]\s*[ivx]{1,5}\b/g;

/** Ko'rsatma qatoridagi qalin joylar: KATTA HARFLAR va harf oraliqlari. */
export function emphasize(line: string, extra?: RegExp): Run[] {
  const s = dashRanges(line);
  const marks: [number, number][] = [];
  const add = (re: RegExp, keep?: (t: string) => boolean) => {
    const g = new RegExp(re.source, re.flags.includes("g") ? re.flags : re.flags + "g");
    let m: RegExpExecArray | null;
    while ((m = g.exec(s))) {
      if (m[0] && (!keep || keep(m[0]))) marks.push([m.index, m.index + m[0].length]);
      if (g.lastIndex === m.index) g.lastIndex++;
    }
  };
  add(CAPS_RUN_RE, capsBold);
  add(LETTERS_RE);
  if (extra) add(extra);
  marks.sort((a, b) => a[0] - b[0]);
  const plain = (t: string): Run[] => withGaps(t, (x) => [{ t: x }]);
  const runs: Run[] = [];
  let pos = 0;
  for (const [a, b] of marks) {
    if (b <= pos) continue;
    const from = Math.max(a, pos);
    if (from > pos) runs.push(...plain(s.slice(pos, from)));
    runs.push({ t: s.slice(from, b), b: true });
    pos = b;
  }
  if (pos < s.length) runs.push(...plain(s.slice(pos)));
  return merge(runs);
}

/** Qalinsiz (faqat gap va tire). */
export function plainRuns(line: string): Run[] {
  return merge(withGaps(dashRanges(line), (t) => [{ t }]));
}

/** Savol matni: raqami alohida chiqadi, shuning uchun gap oldidagi raqam
 *  (uy raqami, yil) oddiy matn bo'lib qoladi. */
export function questionRuns(line: string): Run[] {
  return merge(withGaps(line, (t) => [{ t }], false));
}

function looksTitle(s: string): boolean {
  if (/^Questions?\s+\d/i.test(s)) return false;
  if (s.length > 90) return false;
  if (BULLET_RE.test(s) || OPT_RE.test(s)) return false;
  if (GAP_TEST_RE.test(s)) return false;
  if (/[.;,]$/.test(s)) return false;
  return true;
}

function looksSub(s: string, next: string | undefined): boolean {
  if (!next) return false;
  if (s.length > 50) return false;
  if (/[:.;,?!]$/.test(s) || s.includes(":")) return false;
  if (BULLET_RE.test(s) || OPT_RE.test(s)) return false;
  if (GAP_TEST_RE.test(s) || /\d/.test(s)) return false;
  // keyingi qator ro'yxat bo'lsa — bu kichik sarlavha
  return BULLET_RE.test(next);
}

function toOpt(letter: string, rest: string): Opt {
  return { letter, runs: plainRuns(rest.trim()) };
}

function boxLine(s: string, first: boolean, next: string | undefined, soft: Opt | null): BoxLine {
  const b = BULLET_RE.exec(s);
  if (b) {
    const lvl: 1 | 2 = b[1] === "-" || b[1] === "–" || b[1] === "—" ? 2 : 1;
    return { k: "bullet", level: lvl, runs: plainRuns(b[2]) };
  }
  if (/^[A-Z](?:\t|\s{2,}|\)\s)\S/.test(s) && OPTS_SPLIT_RE.test(s)) {
    const opts = s
      .split(OPTS_SPLIT_RE)
      .map((x) => OPT_ANY_RE.exec(x.trim()))
      .filter((m): m is RegExpExecArray => !!m)
      .map((m) => toOpt(m[1], m[2]));
    if (opts.length > 1) return { k: "opts", opts };
  }
  const o = OPT_RE.exec(s);
  if (o) return { k: "opt", opt: toOpt(o[1], o[2]) };
  if (soft) return { k: "opt", opt: soft };
  if (first && looksTitle(s)) return { k: "title", runs: plainRuns(s) };
  // "In England (Questions 9–10)" — eslatmadagi bo'lim nomi
  if (/\(Questions?\s+\d{1,3}(?:\s*[–-]\s*\d{1,3})?\)$/.test(s) && s.length <= 80)
    return { k: "sub", runs: plainRuns(s) };
  if (!first && looksSub(s, next)) return { k: "sub", runs: plainRuns(s) };
  return { k: "text", runs: plainRuns(s) };
}

/** Bitta bo'shliqli ro'yxatni topadi: kamida 2 qator, A, B, C … tartibda. */
function softOpts(rows: string[]): (Opt | null)[] {
  const out: (Opt | null)[] = rows.map(() => null);
  const cand = rows.map((s) => SOFT_OPT_RE.exec(s));
  const nextOf = (ch: string): string | null => {
    if (/^[A-Z]$/.test(ch)) return String.fromCharCode(ch.charCodeAt(0) + 1);
    const i = ROMAN_LC.indexOf(ch);
    return i >= 0 && i + 1 < ROMAN_LC.length ? ROMAN_LC[i + 1] : null;
  };
  let i = 0;
  while (i < rows.length) {
    const m = cand[i];
    if (!m || (m[1] !== "A" && m[1] !== "i")) {
      i++;
      continue;
    }
    let j = i;
    let want: string | null = m[1];
    while (j < rows.length && cand[j] && want && (cand[j] as RegExpExecArray)[1] === want) {
      want = nextOf(want);
      j++;
    }
    if (j - i >= 2) for (let k = i; k < j; k++) {
      const c = cand[k] as RegExpExecArray;
      out[k] = toOpt(c[1], c[2]);
    }
    i = Math.max(j, i + 1);
  }
  return out;
}

type Kind = "sep" | "heading" | "key" | "nb" | "ins" | "stem" | "other";

function kindOf(s: string): Kind {
  if (!s.trim() || SEP_RE.test(s)) return "sep";
  if (HEADING_RE.test(s)) return "heading";
  if (KEY_RE.test(s)) return "key";
  if (NB_RE.test(s)) return "nb";
  if (STEM_START_RE.test(s)) return "stem";
  if (INS_RE.test(s)) return "ins";
  if (s.endsWith("?") && s.length < 220) return "stem";
  return "other";
}

const QRANGE_RE = /Questions?\s+\d{1,3}\s*(?:[–-]|and)\s*\d{1,3}/;

function insLine(s: string, k: Kind): InsLine {
  if (k === "heading") return { k: "heading", runs: [{ t: dashRanges(s) }] };
  if (k === "key") {
    const m = KEY_RE.exec(s) as RegExpExecArray;
    return { k: "key", key: m[1], runs: plainRuns(m[2]) };
  }
  if (k === "nb") {
    const m = NB_RE.exec(s) as RegExpExecArray;
    return { k: "nb", runs: emphasize(m[1]) };
  }
  if (k === "stem") return { k: "stem", runs: emphasize(s) };
  // "You should spend about 20 minutes on Questions 1–13, …" — oraliq qalin
  return { k: "ins", runs: emphasize(s, /^You should spend/i.test(s) ? QRANGE_RE : undefined) };
}

// Ko'rsatma ramkadagi narsani nazarda tutadi: "Complete the notes below",
// "Label the map", "the list of researchers below"
const BOX_HINT_RE = /\b(notes?|form|table|summary|flow-?chart|diagram|list|timetable|plan|map|below)\b/i;

function finishGroup(from: number | null, to: number | null, label: string | null, body: string[]): Group {
  const rows = body.filter((s) => kindOf(s) !== "sep");
  const firstOther = rows.findIndex((s) => kindOf(s) === "other");
  const head = firstOther < 0 ? rows : rows.slice(0, firstOther);
  const content = firstOther < 0 ? [] : rows.slice(firstOther);
  // Ramka faqat haqiqiy belgisi bo'lsa: gap, ro'yxat, harfli variantlar
  // yoki ko'rsatmada "notes / table / list … below". Aks holda (CEFR
  // Speaking, o'zbekcha ko'rsatma) qatorlar tartibda oddiy chiqadi.
  const soft = softOpts(content);
  const boxy =
    content.length > 0 &&
    (content.some(
      (s) =>
        BULLET_RE.test(s) || OPT_RE.test(s) || GAP_TEST_RE.test(s) ||
        (/^[A-Z](?:\t|\s{2,}|\)\s)\S/.test(s) && OPTS_SPLIT_RE.test(s))
    ) ||
      soft.some(Boolean) ||
      /^List of\b/i.test(content[0]) ||
      head.some((s) => kindOf(s) === "ins" && BOX_HINT_RE.test(s)));
  if (!boxy) {
    const lines = rows.map((s) => {
      const k = kindOf(s);
      return k === "other" ? ({ k: "stem", runs: emphasize(s) } as InsLine) : insLine(s, k);
    });
    return { from, to, label, lines, box: [] };
  }
  const lines = head.map((s) => insLine(s, kindOf(s)));
  const box = content.map((s, i) => boxLine(s, i === 0, content[i + 1], soft[i]));
  return { from, to, label, lines, box };
}

/**
 * Bo'lim ko'rsatmasini guruhlarga ajratadi. Birinchi element — sarlavhasiz
 * kirish qismi (bo'sh bo'lsa ham qaytadi, from = null).
 */
export function parseInstructions(raw: string | null | undefined): Group[] {
  const text = String(raw || "").replace(/\r\n?/g, "\n");
  const groups: Group[] = [];
  let cur = { from: null as number | null, to: null as number | null, label: null as string | null, body: [] as string[] };
  for (const r of text.split("\n")) {
    const s = r.trim() ? r.replace(/^\s+/, "").replace(/\s+$/, "") : "";
    const h = HEADER_RE.exec(s);
    if (h) {
      groups.push(finishGroup(cur.from, cur.to, cur.label, cur.body));
      const a = Number(h[1]);
      const b = h[3] ? Number(h[3]) : a;
      const and = h[2] && /and/i.test(h[2]);
      cur = {
        from: a,
        to: b,
        label: h[3] ? `Questions ${a}${and ? " and " : DASH}${b}` : `Question ${a}`,
        // "Questions 11-13: Choose …" — davomi shu guruhning birinchi qatori
        body: h[4] && h[4].trim() ? [h[4].trim()] : [],
      };
      continue;
    }
    const hr = HEADING_REST_RE.exec(s);
    if (hr) {
      cur.body.push(hr[1], hr[2]);
      continue;
    }
    cur.body.push(s);
  }
  groups.push(finishGroup(cur.from, cur.to, cur.label, cur.body));
  return groups;
}

/** Guruhda ko'rinadigan narsa bormi. */
export function groupHasContent(g: Group): boolean {
  return !!g.label || g.lines.length > 0 || g.box.length > 0;
}

const runsText = (runs: Run[]) => runs.map((r) => r.t).join("");

/** Guruhning butun matni (qidiruv uchun: "map", "plan", "below" …). */
export function groupText(g: Group): string {
  const box = g.box.map((b) =>
    b.k === "opt" ? runsText(b.opt.runs) : b.k === "opts" ? b.opts.map((o) => runsText(o.runs)).join(" ") : runsText(b.runs)
  );
  return [g.label || "", ...g.lines.map((l) => runsText(l.runs)), ...box].join("\n");
}

export type PlaceQ = { n: number; type?: string; pick?: number | null };

/**
 * Guruhlarni savollarga bog'laydi: at.get(q.n) — shu savol OLDIDAN
 * chiqadigan guruhlar. Faqat raqamlar TO'LIQ mos kelsa: guruhlar uzluksiz
 * (14–19, 20–23, 24–26), birinchisi bo'limning birinchi savolida,
 * oxirgisi oxirgisida tugaydi. Bosma raqamlar q.n dan farq qilishi mumkin
 * (bitta "Choose THREE" savoli 3 ta raqam oladi) — shuning uchun avval
 * har savol = 1 raqam, keyin multi = pick raqam deb uriniladi. Mos
 * kelmasa hammasi avvalgidek bo'lim boshida, asl tartibda (2026-09-27
 * ko'rigi: Challenge 25 da guruh noto'g'ri savol oldiga tushardi).
 */
export function placeGroups(groups: Group[], qs: PlaceQ[]): { intro: Group[]; at: Map<number, Group[]> } {
  const shown = groups.filter(groupHasContent);
  const labelled = shown.filter((g) => g.from !== null);
  const fallback = { intro: shown, at: new Map<number, Group[]>() };
  if (!labelled.length || !qs.length) return fallback;
  // sarlavhasiz qism faqat boshida bo'lishi kerak
  const firstLab = shown.indexOf(labelled[0]);
  if (shown.slice(firstLab).some((g) => g.from === null)) return fallback;
  for (let i = 1; i < labelled.length; i++)
    if ((labelled[i].from as number) !== (labelled[i - 1].to as number) + 1) return fallback;

  const tryMap = (span: (q: PlaceQ) => number): Map<number, Group[]> | null => {
    const start = labelled[0].from as number;
    const byPrinted = new Map<number, number>();
    let p = start;
    for (const q of qs) {
      byPrinted.set(p, q.n);
      p += span(q);
    }
    if ((labelled[labelled.length - 1].to as number) !== p - 1) return null;
    const at = new Map<number, Group[]>();
    for (const g of labelled) {
      const n = byPrinted.get(g.from as number);
      if (n === undefined) return null;
      at.set(n, [...(at.get(n) || []), g]);
    }
    return at;
  };
  const at =
    tryMap(() => 1) ||
    tryMap((q) => (q.type === "multi" ? Math.max(1, Number(q.pick) || 1) : 1));
  return at ? { intro: shown.slice(0, firstLab), at } : fallback;
}

// ------------------------------------------------------------ passage
export type PBlock =
  | { k: "sep"; s: number; e: number }
  | { k: "title"; s: number; e: number }
  | { k: "sub"; s: number; e: number }
  /** l: harf / rim raqami tugaydigan joy; b: matn boshlanadigan joy */
  | { k: "label"; s: number; e: number; l: number; b: number }
  | { k: "para"; s: number; e: number };

const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"];

/**
 * Matnni bo'laklarga ajratadi. Bo'laklar matnni TO'LIQ va uzluksiz qoplaydi
 * (s..e) — belgilash (highlight) belgi o'rinlari o'zgarmaydi.
 */
export function passageBlocks(text: string): PBlock[] {
  const raw: { s: number; e: number; sep: boolean }[] = [];
  const lead = /^\s*/.exec(text);
  let pos = lead ? lead[0].length : 0;
  if (pos) raw.push({ s: 0, e: pos, sep: true });
  // Bo'sh qator: Windows (\r\n) va Word/PDF dan ko'chirilgan NBSP ham
  const re = /\r?\n[ \t\r ]*\r?\n\s*/g;
  re.lastIndex = pos;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    if (m.index > pos) raw.push({ s: pos, e: m.index, sep: false });
    raw.push({ s: m.index, e: m.index + m[0].length, sep: true });
    pos = m.index + m[0].length;
  }
  if (pos < text.length) {
    const tail = /\s*$/.exec(text.slice(pos));
    const end = text.length - (tail ? tail[0].length : 0);
    if (end > pos) raw.push({ s: pos, e: end, sep: false });
    if (end < text.length) raw.push({ s: Math.max(end, pos), e: text.length, sep: true });
  }
  const paras = raw.filter((r) => !r.sep);
  const str = (r: { s: number; e: number }) => text.slice(r.s, r.e);

  // Paragraf harfi: kuchli — "A\t", "A  ", "A." , "A)", "A\n";
  // kuchsiz — "A According…" (bitta bo'shliq: artikl "A" bo'lishi mumkin)
  type Lab = { len: number; ch: string; strong: boolean; roman: boolean };
  const labelOf = (s: string): Lab | null => {
    const rm = /^([IVX]{1,4})[ \t\r]*\n/.exec(s);
    if (rm && ROMAN.includes(rm[1])) return { len: rm[1].length, ch: rm[1], strong: true, roman: true };
    const lm = /^([A-J])(?:\t+| {2,}|[ \t]*\r?\n|[.)][ \t]+)/.exec(s);
    if (lm) return { len: 1, ch: lm[1], strong: true, roman: false };
    if (/^[A-J] (?=\S)/.test(s)) return { len: 1, ch: s[0], strong: false, roman: false };
    return null;
  };
  const lab = paras.map((p) => labelOf(str(p)));

  /** Eng uzun A, B, C … ketma-ketligi. Bitta harf tushib qolsa ham davom
   *  etadi (A, B, D); yangi "A" kelsa — yangi ketma-ketlik boshlanadi. */
  const longest = (cands: { i: number; ch: string }[]): number[] => {
    let best: number[] = [];
    let cur: number[] = [];
    let last = "";
    for (const c of cands) {
      if (c.ch === "A") {
        if (cur.length > best.length) best = cur;
        cur = [c.i];
        last = "A";
        continue;
      }
      const d = last ? c.ch.charCodeAt(0) - last.charCodeAt(0) : 0;
      if (cur.length && d >= 1 && d <= 2) {
        cur.push(c.i);
        last = c.ch;
      }
    }
    return cur.length > best.length ? cur : best;
  };
  const letters = lab
    .map((x, i) => (x && !x.roman ? { i, ch: x.ch, strong: x.strong } : null))
    .filter((x): x is { i: number; ch: string; strong: boolean } => !!x);
  const ok = new Set<number>();
  // Kuchli harflar yetarli bo'lsa — faqat ular (sarlavhadagi "A" artikli
  // harf bo'lib qolmasin); aks holda kuchsizlari ham, lekin kamida 3 ta
  const strongSeq = longest(letters.filter((x) => x.strong));
  if (strongSeq.length >= 2) strongSeq.forEach((i) => ok.add(i));
  else {
    const all = longest(letters);
    if (all.length >= 3) all.forEach((i) => ok.add(i));
  }
  lab.forEach((x, i) => {
    if (x && x.roman) ok.add(i);
  });

  let titleIdx = -1;
  // "Saturn Spectacular\nSolving the puzzles…" — sarlavha va kirish bitta
  // bo'lakda: birinchi qator sarlavha, ikkinchisi kursiv kirish
  let splitAt = -1;
  if (paras.length >= 2) {
    const t = str(paras[0]);
    // Xat salomi / sarlavha qatorlari ("Dear Anna", "From: Susan") sarlavha emas
    const okTitle = (x: string) =>
      x.length > 0 &&
      x.length <= 140 &&
      !/[.;,:]$/.test(x) &&
      !/^(Dear|Hi|Hello|To|From|Subject|Date|Re)\b/i.test(x) &&
      !/^[A-Z][a-z]+:\s/.test(x);
    if (!/\r?\n/.test(t) && okTitle(t) && !ok.has(0)) titleIdx = 0;
    else if (!ok.has(0)) {
      const ls = t.split(/\r?\n/);
      if (ls.length === 2 && okTitle(ls[0]) && ls[1].trim().length > 0 && ls[1].trim().length <= 220) {
        titleIdx = 0;
        splitAt = paras[0].s + ls[0].length;
      }
    }
  }
  let subIdx = -1;
  if (titleIdx === 0 && splitAt < 0 && paras.length >= 3) {
    const t = str(paras[1]);
    // Gap bor paragraf ("… (1) ________ …") — savol matni, kirish emas
    const gap = /(_{3,}|\.{5,}|…{2,}|\(\d{1,3}\))/.test(t);
    if (!/\r?\n/.test(t) && t.length <= 220 && !ok.has(1) && !gap) subIdx = 1;
  }

  const out: PBlock[] = [];
  let pi = 0;
  for (const r of raw) {
    if (r.sep) {
      out.push({ k: "sep", s: r.s, e: r.e });
      continue;
    }
    const i = pi++;
    const L = lab[i];
    if (i === titleIdx && splitAt > 0) {
      const nl = /^\s*/.exec(text.slice(splitAt, r.e));
      const b2 = splitAt + (nl ? nl[0].length : 0);
      out.push({ k: "title", s: r.s, e: splitAt });
      out.push({ k: "sep", s: splitAt, e: b2 });
      if (b2 < r.e) out.push({ k: "sub", s: b2, e: r.e });
    } else if (i === titleIdx) out.push({ k: "title", s: r.s, e: r.e });
    else if (i === subIdx) out.push({ k: "sub", s: r.s, e: r.e });
    else if (ok.has(i) && L) {
      const l = r.s + L.len;
      // harfdan keyingi "." / ")" va bo'shliqlar chap chetda, ko'rinmaydi
      const after = /^[.)]?[\t \r\n ]*/.exec(text.slice(l, r.e));
      out.push({ k: "label", s: r.s, e: r.e, l, b: l + (after ? after[0].length : 0) });
    } else out.push({ k: "para", s: r.s, e: r.e });
  }
  return out;
}
