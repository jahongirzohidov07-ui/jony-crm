import { formatDate } from "./format";
/**
 * X-Printer (80mm termal) uchun chek. Yangi oynada ochiladi va avtomat
 * print dialogi chiqadi — printer tanlangach chek chiqadi.
 * Termal printerlar uchun: 72mm kenglik, oq-qora, katta raqamlar.
 */
export function printXReceipt(o: {
  org?: string;
  branch?: string | null;
  student: string;
  publicId?: string | null;
  amount: number;
  method?: string | null;
  note?: string | null;
  balance?: number | null;
  cashier?: string | null;
  paymentId?: number | string | null;
}) {
  const now = new Date();
  // Chekda ham sana OY NOMI bilan — "12-Avg 2026 17:41" (Jahongir,
  // 2026-08-12: "qayerda sana bolsa oy nomi bolsin").
  const dt =
    formatDate(now.toISOString().slice(0, 10)) +
    " " +
    now.toLocaleTimeString("uz-UZ", { hour: "2-digit", minute: "2-digit" });
  const som = (n: number) =>
    Math.round(n).toLocaleString("ru-RU").replace(/,/g, " ") + " so'm";
  const METHODS: Record<string, string> = {
    cash: "Naqd",
    card: "Karta",
    transfer: "O'tkazma",
    click: "Click",
    payme: "Payme",
  };
  const w = window.open("", "_blank", "width=380,height=600");
  if (!w) {
    alert("Brauzer oynani bloklab qo'ydi — popupga ruxsat bering");
    return;
  }
  w.document.write(`<!doctype html><html><head><meta charset="utf-8">
<title>Chek</title>
<style>
  @page { size: 80mm auto; margin: 0; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { width: 72mm; margin: 0 auto; padding: 4mm 2mm 8mm;
         font-family: "Courier New", monospace; color: #000;
         font-size: 12px; line-height: 1.45; }
  .c { text-align: center; }
  .b { font-weight: bold; }
  .xl { font-size: 20px; }
  .lg { font-size: 15px; }
  .hr { border-top: 1px dashed #000; margin: 6px 0; }
  .row { display: flex; justify-content: space-between; gap: 6px; }
  .row span:last-child { text-align: right; }
</style></head><body>
  <div class="c b xl">JONY ACADEMY</div>
  ${o.branch ? `<div class="c">${o.branch} filiali</div>` : ""}
  <div class="c">To'lov cheki</div>
  <div class="hr"></div>
  <div class="row"><span>Sana:</span><span>${dt}</span></div>
  ${o.paymentId ? `<div class="row"><span>Chek №:</span><span>${o.paymentId}</span></div>` : ""}
  <div class="row"><span>O'quvchi:</span><span class="b">${o.student}</span></div>
  ${o.publicId ? `<div class="row"><span>ID:</span><span>${o.publicId}</span></div>` : ""}
  <div class="hr"></div>
  <div class="row lg b"><span>TO'LOV:</span><span>${som(o.amount)}</span></div>
  <div class="row"><span>Usul:</span><span>${METHODS[o.method || ""] || o.method || "Naqd"}</span></div>
  ${o.note ? `<div class="row"><span>Izoh:</span><span>${o.note}</span></div>` : ""}
  ${o.balance != null ? `<div class="hr"></div>
  <div class="row"><span>Balans:</span><span class="b">${som(o.balance)}</span></div>` : ""}
  ${o.cashier ? `<div class="row"><span>Qabul qildi:</span><span>${o.cashier}</span></div>` : ""}
  <div class="hr"></div>
  <div class="c">To'lovingiz uchun rahmat!</div>
  <div class="c">JonyOS · jonyos.uz</div>
</body></html>`);
  w.document.close();
  w.focus();
  setTimeout(() => {
    w.print();
    setTimeout(() => w.close(), 400);
  }, 250);
}


/**
 * Daraja tugatganlik SERTIFIKATI — A4 landshaft, JONY SCHOOL logotipi
 * bilan. Yangi oynada ochiladi: chop etish yoki "Save as PDF" orqali
 * yuklab olinadi.
 */
export function printCertificate(o: {
  student: string;
  level: string;
  score?: number | null;
  date?: string | null;
  publicId?: string | null;
}) {
  const d = formatDate(
    o.date ? o.date : new Date().toISOString().slice(0, 10));
  const w = window.open("", "_blank", "width=1100,height=800");
  if (!w) {
    alert("Brauzer oynani bloklab qo'ydi — popupga ruxsat bering");
    return;
  }
  w.document.write(`<!doctype html><html><head><meta charset="utf-8">
<title>Sertifikat — ${o.student}</title>
<style>
  @page { size: A4 landscape; margin: 0; }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: Georgia, "Times New Roman", serif; }
  .page { width: 297mm; height: 210mm; padding: 14mm;
          background: #fdfcf8; position: relative; overflow: hidden; }
  .frame { position: absolute; inset: 8mm; border: 3px solid #0f766e;
           border-radius: 6px; }
  .frame2 { position: absolute; inset: 11mm; border: 1px solid #d4af37; }
  .inner { position: relative; height: 100%; display: flex;
           flex-direction: column; align-items: center;
           justify-content: center; text-align: center; z-index: 2; }
  .logo { display: flex; align-items: center; gap: 14px;
          margin-bottom: 6mm; }
  .crest { width: 64px; height: 64px; }
  .brand { text-align: left; }
  .brand .n { font-size: 26px; font-weight: bold; letter-spacing: 4px;
              color: #0f766e; }
  .brand .s { font-size: 11px; letter-spacing: 6px; color: #b45309;
              text-transform: uppercase; }
  h1 { font-size: 42px; letter-spacing: 10px; color: #1e293b;
       text-transform: uppercase; }
  .sub { font-size: 14px; color: #64748b; letter-spacing: 3px;
         text-transform: uppercase; margin-top: 2mm; }
  .name { font-size: 40px; color: #0f766e; margin: 8mm 0 3mm;
          font-style: italic; border-bottom: 2px solid #d4af37;
          padding: 0 18mm 2mm; }
  .txt { font-size: 16px; color: #334155; max-width: 200mm;
         line-height: 1.7; }
  .lvl { font-size: 24px; font-weight: bold; color: #b45309;
         margin-top: 2mm; }
  .meta { display: flex; gap: 40mm; margin-top: 10mm; font-size: 13px;
          color: #475569; }
  .meta div { border-top: 1px solid #94a3b8; padding: 2mm 8mm 0;
              min-width: 45mm; }
  .wm { position: absolute; right: -20mm; bottom: -20mm; width: 120mm;
        height: 120mm; opacity: 0.06; z-index: 1; }
</style></head><body>
<div class="page">
  <div class="frame"></div><div class="frame2"></div>
  <svg class="wm" viewBox="0 0 100 100"><circle cx="50" cy="50" r="48"
    fill="none" stroke="#0f766e" stroke-width="2"/>
    <text x="50" y="58" text-anchor="middle" font-size="30"
      fill="#0f766e" font-family="Georgia">JS</text></svg>
  <div class="inner">
    <div class="logo">
      <svg class="crest" viewBox="0 0 100 100">
        <path d="M50 4 L92 20 V52 C92 76 74 90 50 97 C26 90 8 76 8 52 V20 Z"
          fill="#0f766e"/>
        <path d="M50 12 L84 25 V52 C84 70 70 82 50 89 C30 82 16 70 16 52 V25 Z"
          fill="#fdfcf8"/>
        <text x="50" y="63" text-anchor="middle" font-size="34"
          font-weight="bold" fill="#0f766e"
          font-family="Georgia">JS</text>
        <path d="M30 70 H70" stroke="#d4af37" stroke-width="3"/>
      </svg>
      <div class="brand">
        <div class="n">JONY SCHOOL</div>
        <div class="s">Jony Academy oilasi</div>
      </div>
    </div>
    <h1>Sertifikat</h1>
    <div class="sub">Darajani muvaffaqiyatli tugatganlik uchun</div>
    <div class="name">${o.student}</div>
    <div class="txt">
      yakuniy testdan muvaffaqiyatli o'tib, quyidagi darajani
      tugatganligi bilan taqdirlanadi:
    </div>
    <div class="lvl">${o.level}${o.score != null ? ` — ${o.score}%` : ""}</div>
    <div class="meta">
      <div>Sana: ${d}</div>
      <div>${o.publicId ? "ID: " + o.publicId : "JonyOS"}</div>
    </div>
  </div>
</div>
<script>setTimeout(function(){window.print();},300);</script>
</body></html>`);
  w.document.close();
  w.focus();
}
