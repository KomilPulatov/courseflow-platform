import { Link } from 'react-router-dom'

export default function NotificationBadge({ count }: { count: number }) {
  return (
    <Link to="/student/notifications" className="relative inline-flex items-center">
      <span className="text-xl">🔔</span>
      {count > 0 && (
        <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs font-bold rounded-full w-4 h-4 flex items-center justify-center">
          {count > 9 ? '9+' : count}
        </span>
      )}
    </Link>
  )
}
