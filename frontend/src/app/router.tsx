import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "../components/ProtectedRoute";
import { App as AppShellApp } from "../appShell/App";
import { DemoPage } from "../features/demo/DemoPage";
import { App as ProfessorApp } from "../professor/App";
import AdminDashboard from "../pages/AdminDashboard";
import Catalog from "../pages/Catalog";
import CourseDetail from "../pages/CourseDetail";
import Dashboard from "../pages/Dashboard";
import EligibilityPage from "../pages/EligibilityPage";
import INSLogin from "../pages/INSLogin";
import LoginApp from "../pages/LoginApp";
import LoginPlaceholder from "../pages/LoginPlaceholder";
import ManualLogin from "../pages/ManualLogin";
import ManualProfile from "../pages/ManualProfile";
import ManualStart from "../pages/ManualStart";
import MyRegistrations from "../pages/MyRegistrations";
import Notifications from "../pages/Notifications";
import Profile from "../pages/Profile";
import SectionDetail from "../pages/SectionDetail";
import StudentLoginChoice from "../pages/StudentLoginChoice";
import Timetable from "../pages/Timetable";
import Waitlist from "../pages/Waitlist";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginApp />} />
        <Route path="/login/student" element={<StudentLoginChoice />} />
        <Route path="/login/admin" element={<AdminDashboard />} />
        <Route path="/login/professor" element={<LoginPlaceholder role="Professor" />} />
        <Route path="/student/ins-login" element={<INSLogin />} />
        <Route path="/student/manual-login" element={<ManualLogin />} />
        <Route path="/student/manual-start" element={<ManualStart />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/app/*" element={<AppShellApp />} />
        <Route path="/professor/*" element={<ProfessorApp />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/student" element={<Dashboard />} />
          <Route path="/student/profile" element={<Profile />} />
          <Route path="/student/profile/manual" element={<ManualProfile />} />
          <Route path="/student/catalog" element={<Catalog />} />
          <Route path="/student/courses/:courseId" element={<CourseDetail />} />
          <Route path="/student/sections/:sectionId" element={<SectionDetail />} />
          <Route path="/student/sections/:sectionId/eligibility" element={<EligibilityPage />} />
          <Route path="/student/registration" element={<MyRegistrations />} />
          <Route path="/student/registration/timetable" element={<Timetable />} />
          <Route path="/student/waitlist" element={<Waitlist />} />
          <Route path="/student/notifications" element={<Notifications />} />
        </Route>
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
