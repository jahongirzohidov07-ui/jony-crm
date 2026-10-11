import type { ComponentType } from "react";
import {
  LayoutDashboard, Users, Layers, BookMarked, GraduationCap as TeacherIcon,
  Target, Wallet, BarChart3, PieChart, Trophy, Megaphone, Briefcase, History,
  GraduationCap as AcademicIcon, CalendarDays, Archive as ArchiveIcon,
  ClipboardCheck, Timer, Package, Coins, MessageSquareWarning,
  Settings as SettingsIcon, Sparkles, BookOpen, Clapperboard, PartyPopper,
  Award, UserCog, FlaskConical,
} from "lucide-react";
import {
  SUPPORT_TT_VIEW, SCHEDULE_VIEW, FOUNDER, STAFF_VIEWERS, LEAD_ACCESS,
  FINANCE_ACCESS, TEACHING_STAFF, PLANS_ACCESS, HR_CANDIDATE_VIEW,
  CONDUCT_VIEW, MARKETING_ACCESS, AUDIT_VIEW, ACADEMIC_VIEW, can,
  INVENTORY_VIEW, CASH_ACCESS, STUDENT, PARENT, TEACHER, SUPPORT_TEACHER,
  TEACHER_MENU, SMM_MANAGER, EVENTS_ACCESS, EVENT_MANAGER, EXAM_VIEW,
  EXAMINER, HEAD_EXAMINER,
  MOCK_PRACTICE,
} from "../lib/roles";

/**
 * XODIM MENYUSI — kim qaysi bo'limni ko'radi (2026-09-27).
 *
 * Bu kod ilgari Layout.tsx ichida edi. So'zma-so'z shu yerga
 * ko'chirildi, chunki JonyOS xodim ilovasi (/app) ham AYNAN shu
 * ro'yxatni ishlatishi kerak (Jahongir: "har bir xodim uchun
 * alohida o'zigagina tegishli funksiyalari ochilishi kerak").
 * Ikki joyda ikki xil ro'yxat bo'lsa, vaqt o'tib biri ikkinchisidan
 * farq qilib qoladi — panelda yopiq bo'lim ilovada ochilib qolishi
 * mumkin edi. Endi ruxsat bitta joyda.
 */
export interface NavItem {
  to: string;
  label: string;
  icon: ComponentType<{ size?: number; className?: string }>;
  end?: boolean;
}

const navItems: NavItem[] = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/students", label: "Talabalar", icon: Users },
  { to: "/groups", label: "Guruhlar", icon: Layers },
  { to: "/teachers", label: "O'qituvchilar", icon: TeacherIcon },
];

/**
 * Asoschida menyu qisqaroq: Talabalar va Guruhlar O'quv bo'limi
 * ichida, Xodimlar esa HR ichida turadi. Menyuda 20 ta qator
 * bo'lgandan ko'ra, o'z joyida turgani yaxshi.
 */
const FOUNDER_MOVED = ["/students", "/groups", "/users"];

export function buildNav(
  user: { role: string } | null | undefined,
  { onTestBranch }: { onTestBranch: boolean },
): NavItem[] {
  let items: NavItem[] = navItems;
  // Asoschida bu bo'limlar o'z bo'limi ichiga ko'chirilgan
  if (user?.role === FOUNDER) {
    items = items.filter((i) => !FOUNDER_MOVED.includes(i.to));
  }
  // "Bugungi holat" endi Dashboard ICHIDA alohida bo'lim - menyuda
  // takrorlanmaydi.
  // Dars jadvali va Lidlar - administratorning kuni shulardan boshlanadi,
  // shuning uchun eng tepada turadi.
  if (can(user?.role, SCHEDULE_VIEW)) {
    items = [
      items[0],
      { to: "/timetable", label: "Dars jadvali", icon: CalendarDays },
      ...items.slice(1),
    ];
  }
  // Supportlar bo'yicha ALOHIDA jadval — support manager, o'quv
  // bo'limi rahbari va HR kimning qachon bandligini shu yerdan biladi.
  if (can(user?.role, SUPPORT_TT_VIEW)) {
    const ti = items.findIndex((i) => i.to === "/timetable");
    const item = { to: "/support-schedule", label: "Supportlar jadvali",
                   icon: CalendarDays };
    items = ti >= 0
      ? [...items.slice(0, ti + 1), item, ...items.slice(ti + 1)]
      : [...items, item];
  }
  if (can(user?.role, LEAD_ACCESS)) {
    items = [
      items[0],
      { to: "/leads", label: "Lidlar", icon: Target },
      ...items.slice(1),
    ];
  }
  // Coin tizimi o'quv jarayoniga tegishli - ustozlar ham ko'radi.
  if (can(user?.role, TEACHING_STAFF)) {
    items = [...items, { to: "/gamification", label: "Gamification", icon: Trophy }];
  }
  // Ustoz o'z karyera yo'lini ko'radi: daraja, stavka, keyingi bosqich.
  if (user?.role === TEACHER || user?.role === SUPPORT_TEACHER) {
    items = [
      ...items,
      { to: "/my-career", label: "Mening yo'lim", icon: TeacherIcon },
    ];
  }
  // O'quvchi va ota-ona uchun - o'z coin kabineti
  if (user?.role === STUDENT || user?.role === PARENT) {
    items = [
      ...items,
      { to: "/my-coins", label: "Mening coinlarim", icon: Coins },
    ];
  }
  // Moliya - administratorda ham bor, lekin ichida faqat qarzdorlar
  // va oylik hisob-kitob turadi (foyda-zarar unga ko'rinmaydi).
  if (can(user?.role, CASH_ACCESS)) {
    items = [...items, { to: "/finance", label: "Moliya", icon: Wallet }];
  }
  if (user?.role === SMM_MANAGER) {
    items = [...items, { to: "/my-finance", label: "Moliya", icon: Wallet }];
  }
  // 2026-08-27, Jahongir: "Smm mutaxasisi uchun hisobotlardan va
  // analitikadan qismida unga kerakli foydali boladiganlari
  // korsatilsin." Marketologda bu ikki band umuman yo'q edi.
  // Sahifalar ichida u faqat marketingga tegishli bo'limlarni
  // ko'radi (Reports.tsx / Analitika.tsx dagi tab filtri).
  if (can(user?.role, FINANCE_ACCESS) || user?.role === SMM_MANAGER) {
    items = [
      ...items,
      { to: "/reports", label: "Hisobotlar", icon: BarChart3 },
      { to: "/analytics", label: "Analitika", icon: PieChart },
    ];
  }
  if (!items.some(i => i.to === "/reports") && can(user?.role, EXAM_VIEW)) {
    items = [...items, { to: "/reports", label: "Hisobotlar", icon: BarChart3 }];
  }
  // KUTUBXONA - barcha xodimga (2026-08-20, Jahongir: "kutubxona
  // bo'liimi ham supportlarda ochilmadi"). Ilgari faqat HR sahifasi
  // ichida edi - supportlar va boshqa xodimlar yo'l topolmasdi.
  //
  // 2026-08-22, Jahongir: "Kutubxona bo'limini o'quv bo'limi ichiga
  // qoshib ber" — endi u O'quv bo'limi ichida TAB. Menyuda ikki marta
  // turmasligi uchun bandni faqat O'quv bo'limiga KIRA OLMAYDIGANLARGA
  // qoldiramiz (HR, buxgalter, administrator, examiner, SMM...) —
  // ular uchun kutubxonaga boshqa yo'l yo'q.
  const seesAcademic = can(user?.role, ACADEMIC_VIEW)
    && user?.role !== "sales_manager";
  if (!seesAcademic) {
    items = [...items, { to: "/library", label: "Kutubxona", icon: BookOpen }];
  }
  // BIZNES MASLAHATCHI AI - faqat asoschi (2026-08-20, Jahongir:
  // "menga asoschi uchun Biznes maslahatchi AI qoshib ber").
  // 2026-09-26, Jahongir: "maslahatchi AIni korinmaydigan qilib
  // turgin ... chunki u ishlagani yoq hozir API ulanmgan". Sahifa va
  // yo'nalish joyida turibdi — API ulangach shu shartni qaytarish
  // kifoya: if (user?.role === FOUNDER) { ... }
  const ADVISOR_READY = false;
  if (ADVISOR_READY && user?.role === FOUNDER) {
    items = [...items,
      { to: "/advisor", label: "Maslahatchi AI", icon: Sparkles }];
  }
  // O'quv bo'limi - ta'lim sifati. Guruhlardan keyin turadi.
  // Sotuv menejerining ishi sotuv — bu bo'lim unga ko'rinmaydi.
  if (can(user?.role, ACADEMIC_VIEW) && user?.role !== "sales_manager") {
    items = [...items, { to: "/academic", label: "O'quv bo'limi", icon: AcademicIcon }];
    // O'quvchilar o'zlashtirishi (sobiq "O'quv hisoboti"; 2026-09-18,
    // Jahongir: "oquvchilar o'zlashtirishi nomi bilan barcha ustozlarga").
    items = [...items, { to: "/learning", label: "O'quvchilar o'zlashtirishi", icon: BarChart3 }];
  }
  // DARS REJALARI + jonli o'yin (2026-09-18, Jahongir: "saytgayam
  // qoy ... kahoot korinishidagi oyinlar ... har bir unitda").
  // Faqat ingliz tili ustozlariga (boshqa til ustozlariga — o'z rejasi
  // tuzilganda). Rahbariyatga har doim. Ro'yxat backend'dagi
  // TEACHING_ACCESS bilan bir xil (examiner, administrator ham) —
  // ilgari ACADEMIC_VIEW ichida turgani uchun ba'zi ustozlarga
  // chiqmasdi (2026-09-18, "Shirinabonu ko'rinmayabdi deyabdi").
  // 2026-09-18: fan bo'yicha cheklov olib tashlandi — barcha ustozlarga.
  if (can(user?.role, PLANS_ACCESS)) {
    items = [...items, { to: "/plans", label: "Dars rejalari", icon: BookOpen }];
  }
  // IMTIHONLAR (2026-09-26, Jahongir: "audit bolimidagi umumiy
  // imthonlar exam bo'limi qilib bosh sahifaga qosh"). Audit ichida
  // turgani uchun topish qiyin edi. Ustozda o'z oqimi bor
  // ("Imtihon buyurtma"), shuning uchun unga bu band chiqmaydi.
  if (can(user?.role, EXAM_VIEW) && user?.role !== TEACHER) {
    const examItem = { to: "/exam", label: "Imtihonlar", icon: ClipboardCheck };
    // EXAMINERDA ENG TEPADA (2026-09-28, Jahongir: "imtixonlar ko'rinmay
    // qoldi examinerlarga ... alohida bo'limdan ko'rinadigan qilib ber
    // yon menuda"). Bu ularning asosiy ishi — ro'yxat oxirida
    // yo'qolib qolmasin, Dashboard'dan keyin darrov tursin.
    items = user?.role === EXAMINER || user?.role === HEAD_EXAMINER
      ? [items[0], examItem, ...items.slice(1)]
      : [...items, examItem];
  }
  // MOCKNI O'ZI SINAB KO'RISH (2026-09-27, Jahongir: "faqat guruhda
  // emas, boshqalar ham o'zi kirib ishlaydigan bo'lsa yaxshi bo'lardi
  // mock testni xodimlargayam koproq ustozlarga ular ham experience
  // qilib xatolarni aytadida"; administratorlarga kerak emas). Ustoz
  // va support menyusi pastda qayta yig'iladi — band o'sha ikki
  // ro'yxatda ham bor.
  const mockItem = { to: "/mock-practice", label: "Mock sinab ko'rish", icon: FlaskConical };
  // 2026-09-27, Jahongir: "mock testni sinab ko'rish bu asosiyda
  // turmasin imtihonlar bo'limida bor yetadi". Imtihonlar bo'limini
  // ko'radiganlarga (asoschi, filial/o'quv rahbari, examinerlar...)
  // yon menyuda alohida band chiqmaydi — Imtihonlar ichidagi "O'zim
  // sinab ko'raman" tugmasi orqali kiradi. Imtihonlarga kira olmaydigan
  // ustoz va supportda esa bu yagona yo'l, shuning uchun ularda qoladi.
  const seesExams = can(user?.role, EXAM_VIEW) && user?.role !== TEACHER;
  if (can(user?.role, MOCK_PRACTICE) && !seesExams) {
    items = [...items, mockItem];
  }
  // SMM - kontent quvuri: g'oyadan natijagacha. HR menejeriga bu
  // bo'lim kerak emas — uning ishi odamlar, kontent emas.
  // SMM endi Marketing ICHIDA (tab). Marketingga kirolmaydigan, lekin
  // kontent so'rovi/g'oya beradigan rollargagina alohida band qoladi.
  // SMM bo'limi: faqat marketing/SMM va sotuv rahbari (+ asoschi).
  if (
    user?.role === "founder" ||
    user?.role === "smm_manager" ||
    user?.role === "sales_head"
  ) {
    items = [...items, { to: "/smm", label: "SMM", icon: Megaphone }];
  }
  // Marketing - reklama va voronka analitikasi.
  if (can(user?.role, MARKETING_ACCESS)) {
    items = [...items, { to: "/marketing", label: "Marketing", icon: Megaphone }];
  }
  // Asoschida Xodimlar HR ichida turadi — menyuda takrorlanmaydi.
  if (can(user?.role, STAFF_VIEWERS) && user?.role !== FOUNDER) {
    items = [...items, { to: "/users", label: "Xodimlar", icon: UserCog }];
  }
  // HR - xodimlar ro'yxatidan keyin, chunki u kadr ishining davomi.
  // O'quv bo'limi rahbari ham kiradi — unga faqat "Nomzodlar" va
  // "Dars baholash" tablari ochiladi (Hr.tsx ichida cheklangan).
  if (can(user?.role, HR_CANDIDATE_VIEW)) {
    items = [...items, { to: "/hr", label: "HR", icon: Briefcase }];
  }
  // 2026-09-16, Jahongir: "Na'munali xodim" — intizom balli (100 dan)
  if (can(user?.role, CONDUCT_VIEW)) {
    items = [...items, { to: "/namunali", label: "Na'munali xodim", icon: Award }];
  }
  // SHIKOYATLAR - 2026-08-22, Jahongir: "Shikoyatlar bo'limini audit
  // bo'limi ichiga qo'shib ber". Endi u Audit ichida TAB. Menyuda
  // takrorlanmasin deb, bandni faqat Auditga kirolmaydiganlarga
  // qoldiramiz (ustoz, support, administrator, examiner...).
  if (can(user?.role, TEACHING_STAFF) && !can(user?.role, AUDIT_VIEW)) {
    items = [...items,
             { to: "/complaints", label: "Shikoyatlar", icon: MessageSquareWarning }];
  }
  // O'zgarishlar tarixi - eng oxirida, kamdan-kam ochiladi.
  // Audit - nazorat bo'limi: o'zgarishlar tarixi va imtihonlar.
  // Examiner ham shu yerga kiradi (u asoschiga bo'ysunadi).
  if (can(user?.role, AUDIT_VIEW)) {
    items = [...items, { to: "/audit", label: "Audit", icon: History }];
  }
  // Vazifalar endi tepada, qo'ng'iroqcha yonida turadi — menyuda emas.
  if (can(user?.role, INVENTORY_VIEW)) {
    items = [...items, { to: "/inventory", label: "Ombor", icon: Package }];
  }
  // CHEGIRMALAR (2026-09-17) 2026-09-26 da Hisobotlar ichiga ko'chdi
  // (Jahongir: "bosh sahifadagi chegirmalarni hisobotlar bolimiga
  // otkaz") — menyuda alohida band yo'q, Hisobotlar > Chegirmalar.
  if (can(user?.role, TEACHING_STAFF)) {
    items = [...items, { to: "/archive", label: "Arxiv", icon: ArchiveIcon }];
  }
  // MASHQ (2026-09-25, Jahongir: "faqat adminlarga") — administrator
  // tizimni qanchalik tez boshqarishini sinov filialida o'lchaydi.
  // 2026-09-26: "mashq bolimi faqat test filialda qolsin qolgan
  // filialga kerak emas" — endi tepadagi tanlagichda sinov filiali
  // (Branch.is_test) turgandagina ko'rinadi.
  if ((user?.role === "administrator" || user?.role === "founder")
      && onTestBranch) {
    items = [...items, { to: "/mashq", label: "Mashq", icon: Timer }];
  }
  // TADBIRLAR (2026-09-14): tug'ilgan kunlar va tadbirlar.
  if (can(user?.role, EVENTS_ACCESS)) {
    items = [...items, { to: "/events", label: "Tadbirlar", icon: PartyPopper }];
  }
  // Event menejerga o'quv va moliya bo'limlari kerak emas — ochsa ham
  // ruxsat xatosi chiqardi. Menyuda faqat o'z ishi qoladi.
  if (user?.role === EVENT_MANAGER) {
    items = items.filter((i) => i.to === "/events");
  }
  if (user?.role === FOUNDER) {
    items = [
      ...items,
      { to: "/settings", label: "Sozlamalar", icon: SettingsIcon },
    ];
  }
  // Ustozda menyu ochiq ro'yxat bo'yicha kesiladi: dars berishga
  // aloqasi yo'q bo'lim ko'rinmaydi.
  // Shaxsiy rivojlanish — har bir xodimning o'z videolari. Ko'rgan
  // qismi o'zi belgilanadi, statistikani esa faqat asoschi va HR
  // ko'radi (u alohida sahifada).
  items = [...items,
           { to: "/development", label: "Shaxsiy rivojlanish",
             icon: Clapperboard }];

  if (user?.role === TEACHER) {
    // Ustozda "Guruhlar" va "Talabalar" o'rniga o'ziniki: butun
    // markazning ro'yxati ustozning ishiga aloqador emas
    items = [
      ...items,
      { to: "/my-groups", label: "Guruhlarim", icon: Layers },
      { to: "/my-students", label: "O'quvchilarim", icon: AcademicIcon },
      { to: "/my-schedule", label: "Darslarim", icon: CalendarDays },
      { to: "/my-books", label: "Kitob buyurtma", icon: BookMarked },
      { to: "/my-exams", label: "Imtihon buyurtma", icon: ClipboardCheck },
      mockItem,
      // MOLIYA (2026-09-05, Jahongir: "ustozlarda moliya bo'limi
      // qo'shilib ... oyliklar tarixi bo'lsin") — oylar bo'yicha tarix
      { to: "/my-finance", label: "Moliya", icon: Wallet },
      { to: "/my-results", label: "Mening natijalarim", icon: PieChart },
      // HR kutubxonasi (2026-10-11) — ustoz O'quv bo'limiga kira oladi,
      // shuning uchun yuqoridagi umumiy "Kutubxona" bandi unga qo'shilmagan
      { to: "/library", label: "Kutubxona", icon: BookOpen },
    ];
    items = TEACHER_MENU
      .map((to) => items.find((i) => i.to === to))
      .filter((i): i is (typeof items)[number] => !!i);
  }
  // Support teacher: qisqa menyu — coin, imtihon va kitob buyurtma YO'Q.
  // Jadvali biriktirilgan guruhlardan chiqadi.
  if (user?.role === SUPPORT_TEACHER) {
    items = [
      items[0],
      { to: "/my-schedule", label: "Dars jadvalim", icon: CalendarDays },
      { to: "/my-groups", label: "Guruhlarim", icon: Layers },
      { to: "/my-students", label: "O'quvchilarim", icon: AcademicIcon },
      { to: "/my-sessions", label: "Darslarim va oyligim", icon: Timer },
      { to: "/my-finance", label: "Moliya", icon: Wallet },
      { to: "/my-results", label: "Mening natijalarim", icon: PieChart },
      mockItem,
      // O'SISH UCHUN VIDEOLAR VA KUTUBXONA (2026-10-11, Jahongir:
      // "supportlarda o'sish uchun hr belgilagan videolar ko'radigan
      // bo'lim yo'q mobil versiyada"). Qisqa menyu qayta tuzilganda
      // ikkalasi tushib qolgan edi — HR checklistdagi video va kitoblar
      // aynan shu ikki sahifada ochiladi.
      { to: "/development", label: "Shaxsiy rivojlanish", icon: Clapperboard },
      { to: "/library", label: "Kutubxona", icon: BookOpen },
    ];
  }
  return items;
}
