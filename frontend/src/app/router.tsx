import { Navigate, Route, Routes } from "react-router-dom";
import { BrowserRouter } from "react-router-dom";

import ProtectedRoute from "../components/ProtectedRoute";
import { AdminLayout, AdminProtectedRoute } from "../features/admin/AdminLayout";
import { LoginPage } from "../features/admin/LoginPage";
import {
  CourseDetailPage,
  CourseEligibilityRulesPage,
  CourseListPage,
  CoursePrerequisitesPage,
  NewCoursePage,
} from "../features/admin/catalog-pages";
import {
  DepartmentPage,
  MajorPage,
  OfferingPage,
  ProfessorPage,
  RegistrationPeriodPage,
  RoomPage,
  SectionDetailPage,
  SectionListPage,
  SectionRoomsPage,
  SemesterPage,
} from "../features/admin/delivery-pages";
import {
  AuditLogsPage,
  DashboardPage,
  ObservabilityPage,
  SchedulingPage,
  SchedulingRunPage,
} from "../features/admin/ops-pages";
import { DemoPage } from "../features/demo/DemoPage";
import { UnifiedLoginPage } from "../features/login/UnifiedLoginPage";
import { App as AppShellApp } from "../appShell/App";
import { App as ProfessorApp } from "../professor/App";
import Catalog from "../pages/Catalog";
import CourseDetail from "../pages/CourseDetail";
import Dashboard from "../pages/Dashboard";
import EligibilityPage from "../pages/EligibilityPage";
import ManualProfile from "../pages/ManualProfile";
import MyRegistrations from "../pages/MyRegistrations";
import Notifications from "../pages/Notifications";
import Profile from "../pages/Profile";
import SectionDetail from "../pages/SectionDetail";
import Timetable from "../pages/Timetable";
import Waitlist from "../pages/Waitlist";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<UnifiedLoginPage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/app/*" element={<AppShellApp />} />
        <Route path="/professor/*" element={<ProfessorApp />} />
        <Route path="/admin/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
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
        <Route element={<AdminProtectedRoute />}>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="semesters" element={<SemesterPage />} />
            <Route path="departments" element={<DepartmentPage />} />
            <Route path="majors" element={<MajorPage />} />
            <Route path="courses" element={<CourseListPage />} />
            <Route path="courses/new" element={<NewCoursePage />} />
            <Route path="courses/:courseId" element={<CourseDetailPage />} />
            <Route path="courses/:courseId/prerequisites" element={<CoursePrerequisitesPage />} />
            <Route
              path="courses/:courseId/eligibility-rules"
              element={<CourseEligibilityRulesPage />}
            />
            <Route path="professors" element={<ProfessorPage />} />
            <Route path="rooms" element={<RoomPage />} />
            <Route path="offerings" element={<OfferingPage />} />
            <Route path="sections" element={<SectionListPage />} />
            <Route path="sections/:sectionId" element={<SectionDetailPage />} />
            <Route path="sections/:sectionId/rooms" element={<SectionRoomsPage />} />
            <Route path="registration-periods" element={<RegistrationPeriodPage />} />
            <Route path="scheduling" element={<SchedulingPage />} />
            <Route path="scheduling/:runId" element={<SchedulingRunPage />} />
            <Route path="audit-logs" element={<AuditLogsPage />} />
            <Route path="observability" element={<ObservabilityPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/app/not-found" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
