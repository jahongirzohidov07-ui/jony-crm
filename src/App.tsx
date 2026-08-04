import { lazy, Suspense } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/AuthContext";
import Login from "./pages/Login";
import Layout from "./components/Layout";

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
const Plan = lazy(() => import("./pages/Plan"));
const Teachers = lazy(() => import("./pages/Teachers"));
const Moliya = lazy(() => import("./pages/Moliya"));
const Reports = lazy(() => import("./pages/Reports"));
const Analitika = lazy(() => import("./pages/Analitika"));
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
const Settings = lazy(() => import("./pages/Settings"));

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

function AppRoutes() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        {/* Ota-ona sahifasi — loginsiz, token havola orqali */}
        <Route path="/parent/:token" element={<Parent />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <Layout />
            </RequireAuth>
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
          <Route path="plan" element={<Plan />} />
          <Route path="teachers" element={<Teachers />} />
          <Route path="finance" element={<Moliya />} />
          <Route path="reports" element={<Reports />} />
          <Route path="analytics" element={<Analitika />} />
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
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
