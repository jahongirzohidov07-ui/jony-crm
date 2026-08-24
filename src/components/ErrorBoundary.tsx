import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";

/**
 * YANGI VERSIYA XATOSI (2026-08-24, Jahongir: "oxirgi paytlar
 * shunaqa holatlar kop uchrayabdi").
 *
 * Deploy bo'lgach ochiq turgan sahifa eski JS bo'laklarini
 * qidiradi va topolmaydi. Bu DASTUR XATOSI EMAS — shunchaki
 * versiya yangilangan. Uni ajratib olamiz: foydalanuvchiga
 * qo'rqinchli "xatolik" o'rniga "yangilanmoqda" deymiz va
 * sahifani o'zimiz yangilaymiz.
 */
function isVersionError(e: Error | null): boolean {
  const m = ((e?.message || "") + " " + (e?.name || "")).toLowerCase();
  return (
    m.includes("dynamically imported module") ||
    m.includes("failed to fetch dynamically") ||
    m.includes("importing a module script failed") ||
    m.includes("loading chunk") ||
    m.includes("loading css chunk") ||
    m.includes("chunkloaderror")
  );
}

const RELOAD_KEY = "jonyos_chunk_reload";

/**
 * OQ EKRANNI TO'XTATADI (2026-08-14, Jahongir: "bitta JS xatosi
 * butun ekranni oq qilib qo'yadi, xodim nima qilishni bilmaydi.
 * togrla").
 *
 * React'da hech qayerda ushlanmagan xato butun daraxtni o'chirib
 * yuboradi — foydalanuvchi bo'm-bo'sh oq sahifani ko'radi. Bu qobiq
 * xatoni ushlaydi va:
 *   - o'zbekcha tushunarli xabar ko'rsatadi;
 *   - "Qayta urinish" va "Sahifani yangilash" tugmalarini beradi;
 *   - texnik matnni yopiq "Texnik ma'lumot" ichida saqlaydi — xodim
 *     uni nusxalab yuborsa, sabab darrov topiladi.
 *
 * Ikki qatlamda ishlatiladi: butun ilova ustida va har bir sahifa
 * ustida — shunda bitta sahifa yiqilsa ham menyu va boshqa bo'limlar
 * ishlab turaveradi.
 */

interface Props {
  children: ReactNode;
  /** Qaysi joyda yiqilgani (xabarda ko'rsatiladi). */
  where?: string;
  /** Sahifa qobig'i: ixchamroq ko'rinish. */
  compact?: boolean;
}

interface State {
  error: Error | null;
  info: string;
  /** Qayta urinishda bolalarni "yangidan" yaratish uchun. */
  seed: number;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, info: "", seed: 0 };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[JonyOS] ushlangan xato:", error, info);
    this.setState({ info: (info?.componentStack || "").slice(0, 2000) });
    // Versiya yangilangan bo'lsa — o'zimiz yangilaymiz (bir marta,
    // aylanib qolmasligi uchun bayroq bilan).
    if (isVersionError(error)) {
      try {
        if (!sessionStorage.getItem(RELOAD_KEY)) {
          sessionStorage.setItem(RELOAD_KEY, "1");
          setTimeout(() => window.location.reload(), 600);
        }
      } catch {
        /* sessionStorage yopiq bo'lsa - jim o'tamiz */
      }
    }
  }

  private retry = () => {
    this.setState((s) => ({ error: null, info: "", seed: s.seed + 1 }));
  };

  private reload = () => {
    window.location.reload();
  };

  private copy = async () => {
    const { error, info } = this.state;
    const text = [
      `JonyOS xatosi - ${new Date().toLocaleString("uz-UZ")}`,
      `Manzil: ${window.location.pathname}${window.location.search}`,
      `Joy: ${this.props.where || "-"}`,
      `Xabar: ${error?.message || "-"}`,
      "",
      (error?.stack || "").slice(0, 1500),
      "",
      info,
    ].join("\n");
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      /* clipboard yopiq bo'lsa - jim o'tamiz */
    }
  };

  render() {
    const { error } = this.state;
    if (!error) {
      return (
        <div key={this.state.seed} className="contents">
          {this.props.children}
        </div>
      );
    }

    return (
      <div
        className={
          this.props.compact
            ? "m-4 rounded-2xl border border-rose-200 bg-rose-50/60 p-5"
            : "flex min-h-screen items-center justify-center bg-slate-50 p-6"
        }
      >
        <div
          className={
            this.props.compact
              ? "w-full"
              : "w-full max-w-lg rounded-2xl border border-rose-200 bg-white p-6 shadow-sm"
          }
        >
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-rose-100 text-xl">
              !
            </div>
            <div className="min-w-0">
              <h2 className="text-base font-semibold text-slate-900">
                {isVersionError(error)
                  ? "Dastur yangilandi"
                  : "Bu bo'limni ochishda xatolik yuz berdi"}
              </h2>
              <p className="mt-1 text-sm text-slate-600">
                {isVersionError(error)
                  ? "Yangi versiya chiqdi — sahifa o'zi yangilanmoqda. "
                    + "Bir necha soniya kuting yoki \"Sahifani "
                    + "yangilash\"ni bosing. Ma'lumotlaringizga hech "
                    + "narsa bo'lmadi."
                  : "Ma'lumotlaringizga hech narsa bo'lmadi - hech nima "
                    + "o'chmadi va o'zgarmadi. Quyidagi tugmani bosib "
                    + "qayta urinib ko'ring."}
              </p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <button
              onClick={this.retry}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            >
              Qayta urinish
            </button>
            <button
              onClick={this.reload}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Sahifani yangilash
            </button>
            <a
              href="/"
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Bosh sahifa
            </a>
            <button
              onClick={this.copy}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Xatoni nusxalash
            </button>
          </div>

          <details className="mt-4">
            <summary className="cursor-pointer text-xs text-slate-500">
              Texnik ma'lumot (dasturchi uchun)
            </summary>
            <pre className="mt-2 max-h-48 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-900 p-3 text-[11px] leading-relaxed text-slate-100">
              {(this.props.where ? `Joy: ${this.props.where}\n` : "") +
                (error.message || "") +
                "\n\n" +
                (error.stack || "").slice(0, 1200)}
            </pre>
          </details>
        </div>
      </div>
    );
  }
}
