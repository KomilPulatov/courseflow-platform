import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyProfile, type StudentProfile } from '../api/profile'
import { getMyRegistrations } from '../api/registrations'
import { getMyWaitlists } from '../api/waitlists'
import { useAuth } from '../hooks/useAuth'
import ProfileSummary from '../components/ProfileSummary'
import NotificationBadge from '../components/NotificationBadge'
import styles from './Dashboard.module.css'

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
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.brandBadge}>CR</span>
          <div className={styles.brandText}>
            <span className={styles.brandTitle}>IUT Portal</span>
            <span className={styles.brandSubtitle}>CourseFlow Dashboard</span>
          </div>
        </div>
        <div className={styles.headerActions}>
          <NotificationBadge count={0} />
          <button onClick={logout} className={styles.logoutButton}>
            Log out
          </button>
        </div>
      </header>
      <div className={styles.divider} role="separator" />

      <main className={styles.main}>
        {profile && <ProfileSummary profile={profile} />}

        {needsProfile && (
          <div className={styles.notice}>
            <p className={styles.noticeTitle}>Complete your profile</p>
            <p className={styles.noticeText}>
              Add your department, major, year, and completed courses to start registering.
            </p>
            <Link to="/student/profile/manual" className={styles.noticeLink}>
              Complete now
            </Link>
          </div>
        )}

        <div className={styles.tileGrid}>
          {[
            { label: 'Enrollments', count: regCount, href: '/student/registration', tone: 'primary' },
            { label: 'Waitlists', count: waitCount, href: '/student/waitlist', tone: 'secondary' },
          ].map(({ label, count, href, tone }) => (
            <Link key={label} to={href} className={styles.tile}>
              <p
                className={`${styles.tileCount} ${tone === 'secondary' ? styles.tileCountAlt : ''}`}
              >
                {count}
              </p>
              <p className={styles.tileLabel}>{label}</p>
            </Link>
          ))}
        </div>

        <nav className={styles.navList}>
          {[
            { label: 'Course catalog', href: '/student/catalog' },
            { label: 'My timetable', href: '/student/registration/timetable' },
            { label: 'My profile', href: '/student/profile' },
            { label: 'Notifications', href: '/student/notifications' },
          ].map(({ label, href }) => (
            <Link key={href} to={href} className={styles.navLink}>
              <span>{label}</span>
              <span className={styles.navArrow}>View</span>
            </Link>
          ))}
        </nav>
      </main>
    </div>
  )
}
