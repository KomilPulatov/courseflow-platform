import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyRegistrations, dropRegistration, type RegistrationListItem } from '../api/registrations'

export default function MyRegistrations() {
  const [registrations, setRegistrations] = useState<RegistrationListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [dropping, setDropping] = useState<number | null>(null)

  useEffect(() => {
    getMyRegistrations()
      .then(setRegistrations)
      .finally(() => setLoading(false))
  }, [])

  function refresh() {
    setLoading(true)
    return getMyRegistrations()
      .then(setRegistrations)
      .finally(() => setLoading(false))
  }

  async function handleDrop(enrollmentId: number) {
    if (!confirm('Drop this course?')) return
    setDropping(enrollmentId)
    try {
      await dropRegistration(enrollmentId)
      refresh()
    } catch {
      alert('Could not drop. Please try again.')
    } finally {
      setDropping(null)
    }
  }

  const active = registrations.filter((r) => r.status === 'enrolled')
  const dropped = registrations.filter((r) => r.status === 'dropped')

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Link to="/student" className="text-sm text-gray-400 hover:text-gray-600 mb-1 block">
          ← Dashboard
        </Link>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">My registrations</h1>
          <Link
            to="/student/registration/timetable"
            className="text-sm text-blue-600 hover:underline"
          >
            View timetable →
          </Link>
        </div>

        {loading && <p className="text-gray-400 text-sm">Loading…</p>}

        {!loading && active.length === 0 && (
          <div className="bg-white border border-gray-200 rounded-2xl p-6 text-center text-gray-400 text-sm mb-6">
            No active enrollments.{' '}
            <Link to="/student/catalog" className="text-blue-600 hover:underline">
              Browse catalog →
            </Link>
          </div>
        )}

        <div className="space-y-3 mb-8">
          {active.map((r) => (
            <div
              key={r.enrollment_id}
              className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between gap-4"
            >
              <div>
                <p className="font-semibold text-gray-900">{r.course_code}</p>
                <p className="text-sm text-gray-500">{r.course_title}</p>
                <p className="text-xs text-gray-400">{r.semester_name}</p>
              </div>
              <button
                onClick={() => handleDrop(r.enrollment_id)}
                disabled={dropping === r.enrollment_id}
                className="text-sm text-red-500 hover:text-red-700 font-medium disabled:opacity-50"
              >
                {dropping === r.enrollment_id ? 'Dropping…' : 'Drop'}
              </button>
            </div>
          ))}
        </div>

        {dropped.length > 0 && (
          <>
            <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
              Dropped
            </h2>
            <div className="space-y-2">
              {dropped.map((r) => (
                <div
                  key={r.enrollment_id}
                  className="bg-gray-50 border border-gray-100 rounded-xl p-3 flex items-center justify-between"
                >
                  <p className="text-sm text-gray-500">
                    {r.course_code} — {r.course_title}
                  </p>
                  <span className="text-xs text-gray-400">dropped</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
