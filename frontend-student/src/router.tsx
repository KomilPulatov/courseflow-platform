import { createBrowserRouter } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'

import Landing from './pages/Landing'
import StudentLoginChoice from './pages/StudentLoginChoice'
import INSLogin from './pages/INSLogin'
import ManualStart from './pages/ManualStart'
import ManualLogin from './pages/ManualLogin'
import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import ManualProfile from './pages/ManualProfile'
import Catalog from './pages/Catalog'
import CourseDetail from './pages/CourseDetail'
import SectionDetail from './pages/SectionDetail'
import EligibilityPage from './pages/EligibilityPage'
import MyRegistrations from './pages/MyRegistrations'
import Timetable from './pages/Timetable'
import Waitlist from './pages/Waitlist'
import Notifications from './pages/Notifications'

const NotFound = () => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <p className="text-6xl font-bold text-gray-200">404</p>
      <p className="text-gray-500 mt-2">Page not found</p>
    </div>
  </div>
)

const LoginPlaceholder = ({ role }: { role: string }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="text-center">
      <p className="text-gray-400">{role} login — coming soon</p>
    </div>
  </div>
)

export const router = createBrowserRouter([
  { path: '/', element: <Landing /> },
  { path: '/login/student', element: <StudentLoginChoice /> },
  { path: '/login/admin', element: <LoginPlaceholder role="Admin" /> },
  { path: '/login/professor', element: <LoginPlaceholder role="Professor" /> },
  { path: '/student/ins-login', element: <INSLogin /> },
  { path: '/student/manual-login', element: <ManualLogin /> },
  { path: '/student/manual-start', element: <ManualStart /> },

  {
    element: <ProtectedRoute />,
    children: [
      { path: '/student', element: <Dashboard /> },
      { path: '/student/profile', element: <Profile /> },
      { path: '/student/profile/manual', element: <ManualProfile /> },
      { path: '/student/catalog', element: <Catalog /> },
      { path: '/student/courses/:courseId', element: <CourseDetail /> },
      { path: '/student/sections/:sectionId', element: <SectionDetail /> },
      { path: '/student/sections/:sectionId/eligibility', element: <EligibilityPage /> },
      { path: '/student/registration', element: <MyRegistrations /> },
      { path: '/student/registration/timetable', element: <Timetable /> },
      { path: '/student/waitlist', element: <Waitlist /> },
      { path: '/student/notifications', element: <Notifications /> },
    ],
  },

  { path: '*', element: <NotFound /> },
])
