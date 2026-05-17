import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyTimetable, type TimetableItem } from '../api/registrations'
import TimetableGrid from '../components/TimetableGrid'

export default function Timetable() {
  const [items, setItems] = useState<TimetableItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMyTimetable()
      .then(setItems)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <Link
          to="/student/registration"
          className="text-sm text-gray-400 hover:text-gray-600 mb-6 block"
        >
          ← My registrations
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">My timetable</h1>

        {loading ? (
          <p className="text-gray-400 text-sm">Loading…</p>
        ) : (
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <TimetableGrid items={items} />
          </div>
        )}
      </div>
    </div>
  )
}
