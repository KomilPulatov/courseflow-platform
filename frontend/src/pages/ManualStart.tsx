import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { manualStart } from '../api/auth'
import { apiErrorMessage } from '../api/errors'
import { useAuth } from '../hooks/useAuth'

export default function ManualStart() {
  const navigate = useNavigate()
  const { saveAuth } = useAuth()
  const [form, setForm] = useState({
    student_number: '',
    full_name: '',
    email: '',
    password: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await manualStart(form)
      saveAuth(res.access_token, res.student_number ?? '')
      if (res.requires_profile_completion) {
        navigate('/student/profile/manual')
      } else {
        navigate('/student')
      }
    } catch (err: unknown) {
      setError(apiErrorMessage(err, 'Registration failed.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <form onSubmit={handleSubmit} className="max-w-sm w-full bg-white rounded-2xl border border-gray-200 p-8">
        <Link to="/login/student" className="text-sm text-gray-400 hover:text-gray-600 mb-6 block">
          ← Back
        </Link>
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Create profile</h2>
        <p className="text-sm text-gray-500 mb-6">
          Manual profiles skip GPA rules. You'll complete your academic info next.
        </p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        <div className="space-y-4">
          {(
            [
              { key: 'student_number', label: 'Student number', type: 'text', placeholder: 'e.g. 210065' },
              { key: 'full_name', label: 'Full name', type: 'text', placeholder: 'e.g. Iftikhor Mominov' },
              { key: 'email', label: 'Email', type: 'email', placeholder: 'you@example.com' },
              { key: 'password', label: 'Password', type: 'password', placeholder: '' },
            ] as const
          ).map(({ key, label, type, placeholder }) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
              <input
                type={type}
                required
                value={form[key]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                placeholder={placeholder}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
          ))}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full bg-blue-600 text-white rounded-lg py-2.5 font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Creating…' : 'Create profile'}
        </button>
      </form>
    </div>
  )
}
