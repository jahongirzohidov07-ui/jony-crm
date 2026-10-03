import { lazy, Suspense } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/AuthContext";
import Login from "./pages/Login";
import Layout from "./components/Layout";
import { ToastHost } from "./components/ToastHost";
import { StudentLoading } from "./components/StudentLoading";
import ErrorBoundary from "./components/ErrorBoundary";

/**
 * TEZLIK: har bir sahifa alohida bo'lak (code splitting). Ilgari
 * hammasi bitta ~2 MB faylda kelardi — sekin internetda birinchi
 * ochilish og'ir edi. Endi faqat kerakli sahifa yuklanadi.
 */
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Students = lazy(() => import("./pages/Students"));
const Leads = lazy(() => import("./pages/Leads"));
const StudentDetail = lazy(() => import("./pages/StudentDetail"));
const Groups = lazy(() => import("./pages/Groups"));
const GroupDetail = lazy(() => import("./pages/GroupDetail"));
const MyExams = lazy(() => import("./pages/MyExams"));
// MOCKNI O'ZI SINAB KO'RISH (2026-09-27) — xodimlar uchun
const MockPractice = lazy(() => import("./pages/MockPractice"));
const MockPracticeTake = lazy(() => import("./pages/MockPracticeTake"));
const MySessions = lazy(() => import("./pages/MySessions"));
const MyFinance = lazy(() => import("./pages/MyFinance"));
const SupportSchedule = lazy(() => import("./pages/SupportSchedule"));
const Plan = lazy(() => import("./pages/Plan"));
const Teachers = lazy(() => import("./pages/Teachers"));
const Moliya = lazy(() => import("./pages/Moliya"));
const Reports = lazy(() => import("./pages/Reports"));
const Analitika = lazy(() => import("./pages/Analitika"));
const Advisor = lazy(() => import("./pages/Advisor"));
const ExamsHub = lazy(() => import("./pages/ExamsHub"));
const Library = lazy(() => import("./pages/Library"));
const Development = lazy(() => import("./pages/Development"));
const DevelopmentAdmin = lazy(
  () => import("./pages/DevelopmentAdmin"),
);
const Hr = lazy(() => import("./pages/Hr"));
const Namunali = lazy(() => import("./pages/Namunali"));
const Marketing = lazy(() => import("./pages/Marketing"));
const Ceo = lazy(() => import("./pages/Ceo"));
const Audit = lazy(() => import("./pages/Audit"));
const Complaints = lazy(() => import("./pages/Complaints"));
const Academic = lazy(() => import("./pages/Academic"));
const TimetableGrid = lazy(() => import("./pages/TimetableGrid"));
const Archive = lazy(() => import("./pages/Archive"));
const Drill = lazy(() => import("./pages/Drill"));
const DiscountsPage = lazy(() => import("./pages/DiscountsPage"));
// Dars rejalari + jonli o'yin (Kahoot uslubi), 2026-09-18
const LessonPlans = lazy(() => import("./pages/LessonPlans"));
const LiveHost = lazy(() => import("./pages/LiveHost"));
const Play = lazy(() => import("./pages/Play"));
const Tasks = lazy(() => import("./pages/Tasks"));
const Inventory = lazy(() => import("./pages/Inventory"));
const Events = lazy(() => import("./pages/Events"));
const Permissions = lazy(() => import("./pages/Permissions"));
const MyProfile = lazy(() => import("./pages/MyProfile"));
const MyCoins = lazy(() => import("./pages/MyCoins"));
const MyCareer = lazy(() => import("./pages/MyCareer"));
const Smm = lazy(() => import("./pages/Smm"));
const Gamification = lazy(() => import("./pages/Gamification"));
const Branches = lazy(() => import("./pages/Branches"));
const Users = lazy(() => import("./pages/Users"));
const MyResults = lazy(() => import("./pages/MyResults"));
const MyGroups = lazy(() => import("./pages/MyGroups"));
const MyStudents = lazy(() => import("./pages/MyStudents"));
const MySchedule = lazy(() => import("./pages/MySchedule"));
const MyBooks = lazy(() => import("./pages/MyBooks"));
const Parent = lazy(() => import("./pages/Parent"));
const Apply = lazy(() => import("./pages/Apply"));
const ExamTake = lazy(() => import("./pages/ExamTake"));
// Do'st ko'radigan marketing sahifasi — loginsiz (2026-08-28)
const Referral = lazy(() => import("./pages/Referral"));
// Ochiq ariza sahifasi jonyos.uz/ariza — loginsiz (2026-09-27)
const Ariza = lazy(() => import("./pages/Ariza"));
const ParentHome = lazy(() => import("./pages/ParentHome"));
const ParentPayments = lazy(() => import("./pages/ParentPayments"));
const ParentGamification = lazy(() => import("./pages/ParentGamification"));
const ParentResults = lazy(() => import("./pages/ParentResults"));
const ParentRank = lazy(() => import("./pages/ParentRank"));
const Settings = lazy(() => import("./pages/Settings"));
// Jony Student — o'quvchining O'Z ilovasi (alohida qobiq, pastda tab
// paneli bilan; xodimlar paneliga aralashmaydi).
const StudentLayout = lazy(() => import("./pages/student/StudentLayout"));
const StudentHome = lazy(() => import("./pages/student/StudentHome"));
// Darslar / topshiriqlar (2026-09-18)
const StudentLessons = lazy(() => import("./pages/student/StudentLessons"));
const TeacherCheck = lazy(() => import("./pages/teacher/TeacherCheck"));
const LearningReport = lazy(() => import("./pages/LearningReport"));
const StudentGames = lazy(() => import("./pages/student/StudentGames"));
const StudentIelts = lazy(() => import("./pages/student/StudentIelts"));
const StudentExamSkills = lazy(
  () => import("./pages/student/StudentExamSkills"),
);
const StudentCefrWriting = lazy(
  () => import("./pages/student/StudentCefrWriting"),
);
const StudentCefrWritingGuide = lazy(
  () => import("./pages/student/StudentCefrWritingGuide"),
);
const StudentCefrWritingDrill = lazy(
  () => import("./pages/student/StudentCefrWritingDrill"),
);
const StudentCefrWritingTasks = lazy(
  () => import("./pages/student/StudentCefrWritingTasks"),
);
const StudentCefrWritingExam = lazy(
  () => import("./pages/student/StudentCefrWritingExam"),
);
const StudentCefrSpeaking = lazy(
  () => import("./pages/student/StudentCefrSpeaking"),
);
const StudentCefrSpeakingPart = lazy(
  () => import("./pages/student/StudentCefrSpeakingPart"),
);
const StudentCefrSpeakingMock = lazy(
  () => import("./pages/student/StudentCefrSpeakingMock"),
);
const StudentIeltsListening = lazy(
  () => import("./pages/student/StudentIeltsListening"),
);
const StudentIeltsListeningHome = lazy(
  () => import("./pages/student/StudentIeltsListeningHome"),
);
const StudentIeltsReadingHome = lazy(
  () => import("./pages/student/StudentIeltsReadingHome"),
);
const StudentIeltsReading = lazy(
  () => import("./pages/student/StudentIeltsReading"),
);
const StudentLeagues = lazy(
  () => import("./pages/student/StudentLeagues"),
);
const StudentGamePlay = lazy(() => import("./pages/student/StudentGamePlay"));
const StudentLevelTest = lazy(() => import("./pages/student/StudentLevelTest"));
const StudentLeaderboard = lazy(
  () => import("./pages/student/StudentLeaderboard"),
);
const StudentProfile = lazy(() => import("./pages/student/StudentProfile"));
const StudentShop = lazy(() => import("./pages/student/StudentShop"));
const StudentReferral = lazy(
  () => import("./pages/student/StudentReferral"));
const StudentRoadmap = lazy(() => import("./pages/student/StudentRoadmap"));
const StudentSettings = lazy(() => import("./pages/student/StudentSettings"));
const StudentPayments = lazy(() => import("./pages/student/StudentPayments"));
const StudentCertificates = lazy(
  () => import("./pages/student/StudentCertificates"),
);
const StudentResults = lazy(() => import("./pages/student/StudentResults"));
const StudentGrammar = lazy(() => import("./pages/student/StudentGrammar"));
const StudentVocab = lazy(() => import("./pages/student/StudentVocab"));
const StudentPractice = lazy(
  () => import("./pages/student/StudentPractice"),
);
const StudentSpeaking = lazy(
  () => import("./pages/student/StudentSpeaking"),
);
const StudentNotifications = lazy(
  () => import("./pages/student/StudentNotifications"),
);
const StudentGrammarPlay = lazy(
  () => import("./pages/student/StudentGrammarPlay"),
);
// Jony Teacher — ustozning O'Z ilovasi (telefon uchun: yo'qlama,
// jadval, barcha bo'limlar).
const TeacherSalary = lazy(() => import("./pages/teacher/TeacherSalary"));
const TeacherFinancePage = lazy(() => import("./pages/teacher/TeacherFinance"));
const TeacherToday = lazy(() => import("./pages/teacher/TeacherToday"));
const TeacherLesson = lazy(() => import("./pages/teacher/TeacherLesson"));
// Dars rejimi — "Darsni boshlash" (2026-09-18), to'liq ekran (pastki menyusiz)
const TeacherRun = lazy(() => import("./pages/teacher/TeacherRun"));
const TeacherWeek = lazy(() => import("./pages/teacher/TeacherWeek"));
const TeacherSession = lazy(() => import("./pages/teacher/TeacherSession"));
const TeacherVocab = lazy(() => import("./pages/teacher/TeacherVocab"));
import { GuideProvider } from "./components/guide/GuideProvider";
// JonyOS — XODIM ILOVASI (2026-09-27): rolga qarab, telefon uchun
const AppLayout = lazy(() => import("./pages/app/AppLayout"));
const AppHome = lazy(() => import("./pages/app/AppHome"));
const AppTasks = lazy(() => import("./pages/app/AppTasks"));
const AppMenu = lazy(() => import("./pages/app/AppMenu"));
const AppProfile = lazy(() => import("./pages/app/AppProfile"));
const AppAlerts = lazy(() => import("./pages/app/AppAlerts"));
const AppEmbed = lazy(() => import("./pages/app/AppEmbed"));
const AppTeacher = lazy(() => import("./pages/app/AppTeacher"));

function PageLoader() {
  const { pathname } = useLocation();
  if (pathname === "/student" || pathname.startsWith("/student/")) {
    return <div className="student-app"><StudentLoading /></div>;
  }
  return (
    <div className="flex items-center justify-center py-24">
      <p className="text-sm text-slate-400">Yuklanmoqda…</p>
    </div>
  );
}

/** Eski Jony Teacher manzillari -> JonyOS ichidagi o'rni (2026-09-27). */
function TeacherRedirect() {
  const { pathname, search } = useLocation();
  const rest = pathname.replace(/^\/teacher/, "");
  const to = rest === "/more" ? "/app/menu"
    : rest === "/profile" ? "/app/profile"
    : "/app/t" + rest;
  return <Navigate to={to + search} replace />;
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/** Xodimlar paneli. O'quvchi bu yerga tushib qolsa (masalan eski
 * xatcho'p yoki noma'lum manzil orqali) — O'Z ilovasiga qaytariladi,
 * chunki xodim vositalari unga ko'rinmasligi kerak. */
function RequireStaff({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const { pathname } = useLocation();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "student") return <Navigate to="/student" replace />;
  // Event menejerning bosh sahifasi — Tadbirlar (Dashboard unga yopiq).
  if (user.role === "event_manager" && pathname === "/")
    return <Navigate to="/events" replace />;
  return <>{children}</>;
}

/** Manzil o'zgarganda xato qobig'ini yangilaydi - boshqa bo'limga
 * o'tilganda eski xato ekrani qolib ketmasin. */
function RouteBoundary({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation();
  return (
    <ErrorBoundary key={pathname} where={pathname} compact>
      {children}
    </ErrorBoundary>
  );
}

/** XODIM SAHIFALARI — bir ro'yxat, ikki qobiq (2026-09-27): xodimlar
 * paneli ("/", yon menyu bilan) va JonyOS xodim ilovasi ("/app/p/...",
 * telefon sarlavhasi bilan). Ro'yxat ikki joyda takrorlanmasin deb
 * bitta bo'lakka chiqarildi. */
const staffRoutes = (
  <>
    <Route index element={<Dashboard />} />
    <Route path="leads" element={<Leads />} />
    <Route path="students" element={<Students />} />
    <Route path="students/:id" element={<StudentDetail />} />
    <Route path="groups" element={<Groups />} />
    <Route path="groups/:id" element={<GroupDetail />} />
    <Route path="my-exams" element={<MyExams />} />
    {/* MOCK SINAB KO'RISH (2026-09-27) — xodim va ustozlar o'zi */}
    <Route path="mock-practice" element={<MockPractice />} />
    <Route path="mock-practice/:id" element={<MockPracticeTake />} />
    <Route path="my-sessions" element={<MySessions />} />
    <Route path="my-finance" element={<MyFinance />} />
    <Route path="support-schedule" element={<SupportSchedule />} />
    <Route path="plan" element={<Plan />} />
    <Route path="teachers" element={<Teachers />} />
    <Route path="finance" element={<Moliya />} />
    <Route path="reports" element={<Reports />} />
    <Route path="analytics" element={<Analitika />} />
    <Route path="advisor" element={<Advisor />} />
    <Route path="library" element={<Library />} />
    <Route path="development" element={<Development />} />
    <Route
      path="development/stats"
      element={<DevelopmentAdmin />}
    />
    <Route path="ceo" element={<Ceo />} />
    <Route path="complaints" element={<Complaints />} />
    <Route path="audit" element={<Audit />} />
    {/* IMTIHONLAR — Audit ichidan alohida bo'limga chiqdi (2026-09-26) */}
    <Route path="exam" element={<ExamsHub />} />
    <Route path="timetable" element={<TimetableGrid />} />
    <Route path="archive" element={<Archive />} />
    {/* Adminlar mashqi (2026-09-25) */}
    <Route path="mashq" element={<Drill />} />
    <Route path="discounts" element={<DiscountsPage />} />
    <Route path="plans" element={<LessonPlans />} />
    <Route path="learning" element={<LearningReport />} />
    <Route path="plans/:course" element={<LessonPlans />} />
    <Route path="plans/:course/:no" element={<LessonPlans />} />
    <Route path="tasks" element={<Tasks />} />
    <Route path="inventory" element={<Inventory />} />
    <Route path="events" element={<Events />} />
    <Route path="academic" element={<Academic />} />
    <Route path="hr" element={<Hr />} />
    <Route path="namunali" element={<Namunali />} />
    <Route path="marketing" element={<Marketing />} />
    <Route path="gamification" element={<Gamification />} />
    <Route path="branches" element={<Branches />} />
    <Route path="users" element={<Users />} />
    <Route path="my-results" element={<MyResults />} />
    <Route path="my-groups" element={<MyGroups />} />
    <Route path="my-students" element={<MyStudents />} />
    <Route path="my-schedule" element={<MySchedule />} />
    <Route path="my-books" element={<MyBooks />} />
    <Route path="permissions" element={<Permissions />} />
    <Route path="settings" element={<Settings />} />
    <Route path="profile" element={<MyProfile />} />
    <Route path="my-coins" element={<MyCoins />} />
    <Route path="my-career" element={<MyCareer />} />
    <Route path="smm" element={<Smm />} />
  </>
);

function AppRoutes() {
  return (
    // SAHIFA QATLAMI: bitta sahifa yiqilsa ham qolgan bo'limlar
    // ishlab turaveradi. Manzil o'zgarganda qobiq o'zini tozalaydi
    // (key={pathname}) - aks holda xato ekrani yopishib qolardi.
    <RouteBoundary>
      <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        {/* Ota-ona sahifasi — loginsiz, token havola orqali. Ichki
            bo'limlar (to'lovlar, coin/XP, natijalar, reyting) endi
            har biri o'z sahifasida (2026-08-09) — Parent.tsx faqat
            ma'lumotni bir marta yuklab, Outlet orqali beradi. */}
        {/* Ochiq ariza formasi — loginsiz (2026-08-12) */}
        <Route path="/apply" element={<Apply />} />
        {/* Jonli o'yin — o'quvchi telefondan PIN/QR bilan, LOGINSIZ (2026-09-18) */}
        <Route path="/play" element={<Play />} />
        {/* Jonli o'yin — ustoz/proyektor ekrani (to'liq ekran, yon menyusiz) */}
        <Route path="/live/:id" element={<RequireStaff><LiveHost /></RequireStaff>} />
        <Route path="/teacher-run/:lessonId" element={<RequireStaff><TeacherRun /></RequireStaff>} />
        {/* Online test — havola orqali (2026-09-18). 2026-09-25: o'quvchi
            kirgan bo'lsa ilovadagi sahifaga yo'naltiradi; kirmagan bo'lsa
            login (keyin shu imtihonga qaytadi) yoki mehmon tartibi. */}
        <Route path="/t/:token" element={<ExamTake />} />
        {/* Imtihon JONY STUDENT ILOVASI ICHIDA (2026-09-25, Jahongir:
            "cherer Student app qiladigan qilish kerak"). Student
            qobig'idan TASHQARIDA — pastki menyu taymer/topshirish
            panelini to'sib qo'ymasin, o'quvchi chalg'imasin. */}
        <Route
          path="/student/exam/:token"
          element={
            <RequireAuth>
              <ExamTake inApp />
            </RequireAuth>
          }
        />
        {/* Referal havolasi: jonyos.uz/r/JONY-XXXXX — loginsiz */}
        <Route path="/r/:code" element={<Referral />} />
        {/* Ochiq ariza: jonyos.uz/ariza — tanlangan filial lidlariga */}
        <Route path="/ariza" element={<Ariza />} />
        <Route path="/parent/:token" element={<Parent />}>
          <Route index element={<ParentHome />} />
          <Route path="payments" element={<ParentPayments />} />
          <Route path="coins" element={<ParentGamification />} />
          <Route path="results" element={<ParentResults />} />
          <Route path="rank" element={<ParentRank />} />
        </Route>
        {/* Jony Student — o'quvchi ilovasi. Alohida qobiq: xodimlar
            paneli (Layout) bilan aralashmaydi, PWA nomi ham boshqa
            ("Jony Student"). */}
        <Route
          path="/student"
          element={
            <RequireAuth>
              <StudentLayout />
            </RequireAuth>
          }
        >
          <Route index element={<StudentHome />} />
          <Route path="games" element={<StudentGames />} />
          <Route path="lessons" element={<StudentLessons />} />
          <Route path="lessons/:aid" element={<StudentLessons />} />
          <Route path="ielts" element={<StudentIelts />} />
          {/* 2026-08-26: har imtihon o'z ichiga kiradi */}
          <Route path="ielts/exam/:exam"
                 element={<StudentExamSkills />} />
          {/* CEFR Writing — o'rganish / mashq / imtihon */}
          <Route path="cefr/writing"
                 element={<StudentCefrWriting />} />
          <Route path="cefr/writing/guide/:key"
                 element={<StudentCefrWritingGuide />} />
          <Route path="cefr/writing/drill/:kind"
                 element={<StudentCefrWritingDrill />} />
          <Route path="cefr/writing/tasks/:part"
                 element={<StudentCefrWritingTasks />} />
          <Route path="cefr/writing/task/:tid"
                 element={<StudentCefrWritingExam />} />
          {/* Multilevel Speaking — mashq va Free Mock */}
          <Route path="cefr/speaking"
                 element={<StudentCefrSpeaking />} />
          <Route path="cefr/speaking/part/:key"
                 element={<StudentCefrSpeakingPart />} />
          <Route path="cefr/speaking/mock"
                 element={<StudentCefrSpeakingMock />} />
          <Route path="ielts/listening"
                 element={<StudentIeltsListeningHome />} />
          <Route path="ielts/listening/:kind"
                 element={<StudentIeltsListening />} />
          <Route path="ielts/reading"
                 element={<StudentIeltsReadingHome />} />
          <Route path="ielts/reading/:kind"
                 element={<StudentIeltsReading />} />
          <Route path="leagues" element={<StudentLeagues />} />
          <Route path="games/:game" element={<StudentGamePlay />} />
          <Route path="level-test" element={<StudentLevelTest />} />
          <Route path="vocab" element={<StudentVocab />} />
          <Route path="practice/:skill" element={<StudentPractice />} />
          <Route path="speaking" element={<StudentSpeaking />} />
          <Route
            path="notifications"
            element={<StudentNotifications />}
          />
          <Route path="grammar" element={<StudentGrammar />} />
          {/* Aralash mashq (2026-09-25) — statik yo'l dinamik :topic dan
              oldin turadi */}
          <Route path="grammar/mix" element={<StudentGrammarPlay mix />} />
          <Route path="grammar/:topic" element={<StudentGrammarPlay />} />
          <Route path="leaderboard" element={<StudentLeaderboard />} />
          <Route path="shop" element={<StudentShop />} />
          <Route path="referral" element={<StudentReferral />} />
          <Route path="roadmap" element={<StudentRoadmap />} />
          <Route path="settings" element={<StudentSettings />} />
          <Route path="payments" element={<StudentPayments />} />
          <Route path="certificates" element={<StudentCertificates />} />
          <Route path="results" element={<StudentResults />} />
          <Route path="results/:examId" element={<StudentResults />} />
          <Route path="profile" element={<StudentProfile />} />
        </Route>
        {/* JONY TEACHER endi JonyOS ichida (2026-09-27, Jahongir: "Jony
            Teacher va JonyOS xodimlar uchun bitta programma bo'laversin").
            Eski manzil (o'rnatilgan ilova, xatcho'p, Telegram havolasi)
            yangisiga olib boradi: /teacher/lesson/5 -> /app/t/lesson/5. */}
        <Route path="/teacher/*" element={<TeacherRedirect />} />
        {/* JonyOS xodim ilovasi — har xodim faqat o'z bo'limlarini ko'radi
            (ro'yxat paneldagi menyu bilan bir manbadan: navItems.ts) */}
        <Route
          path="/app"
          element={
            <RequireAuth>
              <AppLayout />
            </RequireAuth>
          }
        >
          <Route index element={<AppHome />} />
          <Route path="tasks" element={<AppTasks />} />
          <Route path="menu" element={<AppMenu />} />
          <Route path="profile" element={<AppProfile />} />
          <Route path="alerts" element={<AppAlerts />} />
          {/* Ustoz va support ishi — sobiq Jony Teacher (2026-09-27) */}
          <Route path="t" element={<AppTeacher />}>
            <Route index element={<TeacherToday />} />
            <Route path="week" element={<TeacherWeek />} />
            <Route path="lesson/:id" element={<TeacherLesson />} />
            <Route path="check" element={<TeacherCheck />} />
            <Route path="check/:sid" element={<TeacherCheck />} />
            <Route path="session" element={<TeacherSession />} />
            <Route path="vocab" element={<TeacherVocab />} />
            <Route path="salary" element={<TeacherSalary />} />
            <Route path="finance" element={<TeacherFinancePage />} />
          </Route>
          <Route path="p" element={<AppEmbed />}>
            {staffRoutes}
          </Route>
        </Route>
        <Route
          path="/"
          element={
            <RequireStaff>
              {/* O'RGATUVCHI (2026-08-23): xodimlar panelining ustidan
                  ishlaydi — strelka, matn va mashq rejimi shu yerdan
                  boshqariladi. O'quvchi/ustoz ilovasiga tegmaydi. */}
              <GuideProvider>
                <Layout />
              </GuideProvider>
            </RequireStaff>
          }
        >
          {staffRoutes}
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </Suspense>
    </RouteBoundary>
  );
}

function App() {
  return (
    // ENG TASHQI QATLAM: hatto login yoki umumiy qobiq yiqilsa ham
    // oq ekran emas, tushunarli xabar chiqadi.
    <ErrorBoundary where="Ilova">
      <BrowserRouter>
        <AuthProvider>
          <AppRoutes />
          <ToastHost />
        </AuthProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
