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

      {canManage ? (
        <LibraryTab />
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
