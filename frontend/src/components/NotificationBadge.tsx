import { Link } from 'react-router-dom'
import styles from './NotificationBadge.module.css'

export default function NotificationBadge({ count }: { count: number }) {
  return (
    <Link to="/student/notifications" className={styles.badge} aria-label="Notifications">
      <svg className={styles.icon} viewBox="0 0 24 24" aria-hidden="true">
        <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 0 0-5-5.9V4a1 1 0 1 0-2 0v1.1A6 6 0 0 0 6 11v3.2c0 .5-.2 1-.6 1.4L4 17h5" />
        <path d="M9 17a3 3 0 0 0 6 0" />
      </svg>
      {count > 0 && (
        <span className={styles.count}>{count > 9 ? '9+' : count}</span>
      )}
    </Link>
  )
}
