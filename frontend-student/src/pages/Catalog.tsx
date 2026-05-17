import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listCourses, type CourseSummary } from '../api/courses'

export default function Catalog() {
  const [courses, setCourses] = useState<CourseSummary[]>([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const t = setTimeout(() => {
      setLoading(true)
      listCourses({ search: search || undefined })
        .then(setCourses)
        .catch(() => setError('Failed to load courses.'))
        .finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(t)
  }, [search])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <Link to="/student" className="text-sm text-gray-400 hover:text-gray-600 block mb-1">
              ← Dashboard
            </Link>
            <h1 className="text-2xl font-bold text-gray-900">Course catalog</h1>
          </div>
        </div>

        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by code or title…"
          className="w-full border border-gray-300 rounded-xl px-4 py-2.5 text-sm mb-6 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />

        {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
        {loading && <p className="text-gray-400 text-sm">Loading…</p>}

        {!loading && !error && courses.length === 0 && (
          <p className="text-gray-400 text-sm">No courses found.</p>
        )}

        <div className="space-y-3">
          {courses.map((c) => (
            <Link
              key={c.id}
              to={`/student/courses/${c.id}`}
              className="block bg-white border border-gray-200 rounded-xl p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-gray-900">
                    {c.code} — {c.title}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {c.department_name} · {c.credits} credits
                  </p>
                </div>
                <span className="text-xs text-gray-400 whitespace-nowrap">
                  {c.active_section_count} section{c.active_section_count !== 1 ? 's' : ''}
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
