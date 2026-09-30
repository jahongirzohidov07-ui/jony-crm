import { useEffect, useState } from "react";
import { BookOpen } from "lucide-react";
import { api, type LibraryList } from "../lib/api";
import { MyLibrary } from "./MyProfile";
import { LibraryTab } from "./Hr";

/**
 * KUTUBXONA — alohida sahifa (2026-08-20).
 *
 * Jahongir: "kutubxona bo'liimi ham supportlarda ochilmadi
 * adashmasam". Sabab: kutubxona faqat HR sahifasining ichida tab
 * edi, HR sahifasini esa support rahbari ocholmasdi; oddiy xodim
 * uchun esa profil ichida material bo'lsagina ko'rinardi.
 *
 * Endi yon menyuda BARCHA xodimga "Kutubxona" bor:
 *   - har kim o'z ro'yxatini ko'radi va ko'rgan foizini belgilaydi;
 *   - boshqara oladiganlar (HR, rahbariyat, o'quv/examiner/support
 *     rahbarlari) shu yerning o'zida material qo'shadi-o'zgartiradi.
 */
export default function Library() {
  const [canManage, setCanManage] = useState(false);
  const [empty, setEmpty] = useState(false);
  const [version, setVersion] = useState(0);
  const [importOpen, setImportOpen] = useState(false);
  const [bookText, setBookText] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [importError, setImportError] = useState("");
  const parsedBooks = bookText.split(/\r?\n/).filter(x => x.trim()).map(line => {
    const [title, ...note] = line.split("\t");
    return { title: title.trim(), description: note.join(" · ").trim() };
  });
  async function importBooks() {
    if (busy || !parsedBooks.length) return;
    setBusy(true); setImportError(""); setMessage("");
    try {
      const result = await api.post<{added: number; skipped: number}>("/library/import", {items: parsedBooks});
      setMessage(result.added + " ta kitob qo'shildi. " + result.skipped + " ta oldindan mavjud.");
      setVersion(v => v + 1); setBookText(""); setImportOpen(false);
    } catch (e) { setImportError(e instanceof Error ? e.message : "Saqlab bo'lmadi"); }
    finally { setBusy(false); }
  }

  const [archiveSource, setArchiveSource] = useState("");
  async function archiveImport() {
    if (busy || !archiveSource.trim()) return;
    if (!confirm("Shu fayldan import qilingan kitoblar yashirilsinmi? Yozuvlar saqlanadi va qayta faollashtirish mumkin.")) return;
    setBusy(true); setMessage(""); setImportError("");
    try {
      const r = await api.post<{archived: number}>("/library/import/archive", {source: archiveSource.trim()});
      setMessage(`${r.archived} ta kitob yashirildi. Ma'lumotlari saqlangan.`);
      setVersion(v => v + 1); setArchiveSource("");
    } catch (e) { setImportError(e instanceof Error ? e.message : "Xatolik"); }
    finally { setBusy(false); }
  }

  useEffect(() => {
    api.get<LibraryList>("/library")
      .then((d) => { setCanManage(d.can_manage); setEmpty(d.items.length === 0); })
      .catch(() => {});
  }, []);

  return (
    <div className="p-8 max-w-5xl">
      <h1 className="text-xl font-semibold text-slate-900 mb-1 flex items-center gap-2">
        <BookOpen size={20} className="text-brand-600" />
        Kutubxona
      </h1>
      <p className="text-sm text-slate-500 mb-5">
        Onboarding va o'sish uchun majburiy kitob-videolar. Ko'rgan
        foizingizni o'zingiz belgilaysiz, "topshirdi"ni rahbar qo'yadi.
      </p>

      {canManage && <div className="mb-5">
        <button className="rounded-lg border border-slate-300 px-4 py-2 text-sm"
                onClick={() => setImportOpen(v => !v)} disabled={busy}>
          Ro'yxatdan kitob qo'shish
        </button>
        <details className="mt-3 text-sm">
          <summary className="cursor-pointer">Importni bekor qilish</summary>
          <p className="my-2 text-slate-500">Faqat tanlangan manbadan import qilingan kitoblar yashiriladi. Yashirilgan materiallar ro'yxatidan tiklash mumkin.</p>
          <input aria-label="Import manbasi" placeholder="Excel faylining to'liq nomi" value={archiveSource} onChange={e => setArchiveSource(e.target.value)} className="border rounded-lg p-2 mr-2" />
          <button onClick={archiveImport} disabled={busy || !archiveSource.trim()} className="border rounded-lg p-2">Import kitoblarini yashirish</button>
          {importError && <p role="alert" className="text-red-600 mt-2">{importError}</p>}
        </details>
        {message && <p role="status" className="mt-2 text-sm text-emerald-700">{message}</p>}
        {importOpen && <div className="mt-3 rounded-xl border border-slate-200 bg-white p-4 space-y-3">
          <label htmlFor="library-book-list" className="block text-sm font-medium">Kitoblar ro'yxati</label>
          <p className="text-sm text-slate-500">Har bir qatorda kitob nomi. Excel'dan ikki ustun — nom va izohni ko'chirib qo'yish mumkin. Mavjud nomlar takrorlanmaydi. Kitoblar ixtiyoriy o'qish uchun qo'shiladi.</p>
          <textarea id="library-book-list" value={bookText} onChange={e => setBookText(e.target.value)}
                    disabled={busy} rows={10} className="w-full border border-slate-300 rounded-lg p-3 text-sm" />
          <p className="text-sm">{parsedBooks.length} ta kitob tayyor</p>
          {importError && <p role="alert" className="text-sm text-red-600">{importError}</p>}
          <button onClick={importBooks} disabled={busy || !parsedBooks.length || parsedBooks.length > 500}
                  className="rounded-lg bg-brand-600 text-white px-4 py-2 text-sm disabled:opacity-50">
            {busy ? "Qo'shilmoqda…" : "Kitoblarni qo'shish"}
          </button>
        </div>}
      </div>}
      {canManage ? (
        <LibraryTab key={version} />
      ) : empty ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <BookOpen size={26} className="mx-auto text-slate-300 mb-2" />
          <p className="text-sm text-slate-500">
            Sizning rolingiz uchun hozircha material qo'shilmagan.
          </p>
        </div>
      ) : (
        <MyLibrary />
      )}
    </div>
  );
}
