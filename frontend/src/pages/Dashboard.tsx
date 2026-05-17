import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyProfile, type StudentProfile } from '../api/profile'
import { getMyRegistrations } from '../api/registrations'
import { getMyWaitlists } from '../api/waitlists'
import { useAuth } from '../hooks/useAuth'
import ProfileSummary from '../components/ProfileSummary'
import NotificationBadge from '../components/NotificationBadge'

export default function Dashboard() {
  const { logout } = useAuth()
  const [profile, setProfile] = useState<StudentProfile | null>(null)
  const [regCount, setRegCount] = useState(0)
  const [waitCount, setWaitCount] = useState(0)

  useEffect(() => {
    getMyProfile().then(setProfile).catch(() => {})
    getMyRegistrations()
      .then((r) => setRegCount(r.filter((e) => e.status === 'enrolled').length))
      .catch(() => {})
    getMyWaitlists().then((w) => setWaitCount(w.length)).catch(() => {})
  }, [])

  const needsProfile =
    profile && !profile.academic_profile && profile.profile_source === 'manual'

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <span className="font-bold text-gray-900">CRSP</span>
        <div className="flex items-center gap-4">
          <NotificationBadge count={0} />
          <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-700">
            Log out
          </button>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
        {profile && <ProfileSummary profile={profile} />}

        {needsProfile && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm">
            <p className="font-medium text-amber-800">Complete your profile</p>
            <p className="text-amber-600 mt-1">
              Add your department, major, year, and completed courses to start registering.
            </p>
            <Link
              to="/student/profile/manual"
              className="mt-2 inline-block text-amber-700 font-semibold hover:underline"
            >
              Complete now →
            </Link>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          {[
            { label: 'Enrollments', count: regCount, href: '/student/registration', color: 'text-blue-600' },
            { label: 'Waitlists', count: waitCount, href: '/student/waitlist', color: 'text-amber-600' },
          ].map(({ label, count, href, color }) => (
            <Link
              key={label}
              to={href}
              className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-sm transition-shadow"
            >
              <p className={`text-3xl font-bold ${color}`}>{count}</p>
              <p className="text-sm text-gray-500 mt-1">{label}</p>
            </Link>
          ))}
        </div>

        <nav className="space-y-2">
          {[
            { label: '📚 Course catalog', href: '/student/catalog' },
            { label: '📅 My timetable', href: '/student/registration/timetable' },
            { label: '👤 My profile', href: '/student/profile' },
            { label: '🔔 Notifications', href: '/student/notifications' },
          ].map(({ label, href }) => (
            <Link
              key={href}
              to={href}
              className="block bg-white border border-gray-200 rounded-xl px-5 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
            >
              {label}
            </Link>
          ))}
        </nav>
      </main>
    </div>
  )
}
