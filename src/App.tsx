import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/AuthContext";
import Login from "./pages/Login";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Students from "./pages/Students";
import Leads from "./pages/Leads";
import StudentDetail from "./pages/StudentDetail";
import Groups from "./pages/Groups";
import GroupDetail from "./pages/GroupDetail";
import Teachers from "./pages/Teachers";
import Moliya from "./pages/Moliya";
import Reports from "./pages/Reports";
import Analitika from "./pages/Analitika";
import Hr from "./pages/Hr";
import Marketing from "./pages/Marketing";
import Ceo from "./pages/Ceo";
import Audit from "./pages/Audit";
import Complaints from "./pages/Complaints";
import Academic from "./pages/Academic";
import Timetable from "./pages/Timetable";
import Archive from "./pages/Archive";
import Tasks from "./pages/Tasks";
import Inventory from "./pages/Inventory";
import Gamification from "./pages/Gamification";
import Branches from "./pages/Branches";
import Users from "./pages/Users";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
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
        <Route path="teachers" element={<Teachers />} />
        <Route path="finance" element={<Moliya />} />
        <Route path="reports" element={<Reports />} />
        <Route path="analytics" element={<Analitika />} />
        <Route path="ceo" element={<Ceo />} />
        <Route path="complaints" element={<Complaints />} />
        <Route path="audit" element={<Audit />} />
        <Route path="timetable" element={<Timetable />} />
        <Route path="archive" element={<Archive />} />
        <Route path="tasks" element={<Tasks />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="academic" element={<Academic />} />
        <Route path="hr" element={<Hr />} />
        <Route path="marketing" element={<Marketing />} />
        <Route path="gamification" element={<Gamification />} />
        <Route path="branches" element={<Branches />} />
        <Route path="users" element={<Users />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
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
