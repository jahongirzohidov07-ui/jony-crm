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
const MySessions = lazy(() => import("./pages/MySessions"));
const SupportSchedule = lazy(() => import("./pages/SupportSchedule"));
const Plan = lazy(() => import("./pages/Plan"));
const Teachers = lazy(() => import("./pages/Teachers"));
const Moliya = lazy(() => import("./pages/Moliya"));
const Reports = lazy(() => import("./pages/Reports"));
const Analitika = lazy(() => import("./pages/Analitika"));
const Advisor = lazy(() => import("./pages/Advisor"));
const Library = lazy(() => import("./pages/Library"));
const Development = lazy(() => import("./pages/Development"));
const DevelopmentAdmin = lazy(
  () => import("./pages/DevelopmentAdmin"),
);
const Hr = lazy(() => import("./pages/Hr"));
const Marketing = lazy(() => import("./pages/Marketing"));
const Ceo = lazy(() => import("./pages/Ceo"));
const Audit = lazy(() => import("./pages/Audit"));
const Complaints = lazy(() => import("./pages/Complaints"));
const Academic = lazy(() => import("./pages/Academic"));
const TimetableGrid = lazy(() => import("./pages/TimetableGrid"));
const Archive = lazy(() => import("./pages/Archive"));
const Tasks = lazy(() => import("./pages/Tasks"));
const Inventory = lazy(() => import("./pages/Inventory"));
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
const StudentRoadmap = lazy(() => import("./pages/student/StudentRoadmap"));
const StudentSettings = lazy(() => import("./pages/student/StudentSettings"));
const StudentPayments = lazy(() => import("./pages/student/StudentPayments"));
const StudentCertificates = lazy(
  () => import("./pages/student/StudentCertificates"),
);
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
const TeacherLayout = lazy(() => import("./pages/teacher/TeacherLayout"));
const TeacherSalary = lazy(() => import("./pages/teacher/TeacherSalary"));
const TeacherToday = lazy(() => import("./pages/teacher/TeacherToday"));
const TeacherLesson = lazy(() => import("./pages/teacher/TeacherLesson"));
const TeacherWeek = lazy(() => import("./pages/teacher/TeacherWeek"));
const TeacherSession = lazy(() => import("./pages/teacher/TeacherSession"));
const TeacherVocab = lazy(() => import("./pages/teacher/TeacherVocab"));
const TeacherMore = lazy(() => import("./pages/teacher/TeacherMore"));
const TeacherProfile = lazy(() => import("./pages/teacher/TeacherProfile"));
import { GuideProvider } from "./components/guide/GuideProvider";

function PageLoader() {
  return (
    <div className="flex items-center justify-center py-24">
      <p className="text-sm text-slate-400">Yuklanmoqda…</p>
    </div>
  );
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
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "student") return <Navigate to="/student" replace />;
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
          <Route path="grammar/:topic" element={<StudentGrammarPlay />} />
          <Route path="leaderboard" element={<StudentLeaderboard />} />
          <Route path="shop" element={<StudentShop />} />
          <Route path="roadmap" element={<StudentRoadmap />} />
          <Route path="settings" element={<StudentSettings />} />
          <Route path="payments" element={<StudentPayments />} />
          <Route path="certificates" element={<StudentCertificates />} />
          <Route path="profile" element={<StudentProfile />} />
        </Route>
        {/* Jony Teacher — ustoz ilovasi (telefon). Xodimlar paneli
            (Layout) o'chirilmadi: "To'liq panelga o'tish" tugmasi
            orqali ochiladi. */}
        <Route
          path="/teacher"
          element={
            <RequireAuth>
              <TeacherLayout />
            </RequireAuth>
          }
        >
          <Route index element={<TeacherToday />} />
          <Route path="week" element={<TeacherWeek />} />
          <Route path="lesson/:id" element={<TeacherLesson />} />
          <Route path="session" element={<TeacherSession />} />
          <Route path="vocab" element={<TeacherVocab />} />
          <Route path="salary" element={<TeacherSalary />} />
          <Route path="more" element={<TeacherMore />} />
          <Route path="profile" element={<TeacherProfile />} />
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
          <Route index element={<Dashboard />} />
          <Route path="leads" element={<Leads />} />
          <Route path="students" element={<Students />} />
          <Route path="students/:id" element={<StudentDetail />} />
          <Route path="groups" element={<Groups />} />
          <Route path="groups/:id" element={<GroupDetail />} />
          <Route path="my-exams" element={<MyExams />} />
          <Route path="my-sessions" element={<MySessions />} />
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
          <Route path="timetable" element={<TimetableGrid />} />
          <Route path="archive" element={<Archive />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="inventory" element={<Inventory />} />
          <Route path="academic" element={<Academic />} />
          <Route path="hr" element={<Hr />} />
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
