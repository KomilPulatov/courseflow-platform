import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { apiErrorMessage } from '../api/errors'
import { getMyProfile, updateManualProfile } from '../api/profile'

export default function ManualProfile() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    department_name: '',
    major_name: '',
    academic_year: 1,
    completed_course_codes: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getMyProfile().then((p) => {
      const ap = p.academic_profile
      if (ap) {
        setForm({
          department_name: ap.department_name ?? '',
          major_name: ap.major_name ?? '',
          academic_year: ap.academic_year ?? 1,
          completed_course_codes: '',
        })
      }
    }).catch(() => {
      console.warn('Could not preload profile.')
    })
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    const codes = form.completed_course_codes
      .split(',')
      .map((c) => c.trim())
      .filter(Boolean)
    try {
      await updateManualProfile({
        department_name: form.department_name || null,
        major_name: form.major_name || null,
        academic_year: form.academic_year,
        completed_course_codes: codes,
      })
      navigate('/student')
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Failed to save profile.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="max-w-sm w-full bg-white rounded-2xl border border-gray-200 p-8">
        <Link to="/student/profile" className="text-sm text-gray-400 hover:text-gray-600 mb-6 block">
          ← Back
        </Link>
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Academic profile</h2>
        <p className="text-sm text-gray-500 mb-6">
          Enter your academic details. GPA rules are skipped for manual profiles.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Department name</label>
            <input
              type="text"
              value={form.department_name}
              onChange={(e) => setForm({ ...form, department_name: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="e.g. SOCIE"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Major name</label>
            <input
              type="text"
              value={form.major_name}
              onChange={(e) => setForm({ ...form, major_name: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="e.g. CSE"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Academic year (1–6)
            </label>
            <select
              required
              value={form.academic_year}
              onChange={(e) => setForm({ ...form, academic_year: Number(e.target.value) })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            >
              {[1, 2, 3, 4, 5, 6].map((y) => (
                <option key={y} value={y}>
                  Year {y}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Completed course codes
            </label>
            <textarea
              value={form.completed_course_codes}
              onChange={(e) => setForm({ ...form, completed_course_codes: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              rows={3}
              placeholder="e.g. MSC1051, MSC1052, SOC3020"
            />
            <p className="text-xs text-gray-400 mt-1">Comma-separated course codes.</p>
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full bg-blue-600 text-white rounded-lg py-2.5 font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Saving…' : 'Save profile'}
        </button>
      </form>
    </div>
  )
}
