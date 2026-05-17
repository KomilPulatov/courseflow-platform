import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { manualLogin } from '../api/auth'
import { useAuth } from '../hooks/useAuth'

export default function ManualLogin() {
  const navigate = useNavigate()
  const { saveAuth } = useAuth()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await manualLogin(form.email, form.password)
      saveAuth(res.access_token, res.student_number ?? '')
      navigate('/student')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? 'Login failed. Check your credentials.')
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
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Sign in</h2>
        <p className="text-sm text-gray-500 mb-6">Sign in to your manual profile account.</p>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full bg-blue-600 text-white rounded-lg py-2.5 font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? 'Signing in…' : 'Sign in'}
        </button>

        <p className="mt-4 text-center text-sm text-gray-400">
          New here?{' '}
          <Link to="/student/manual-start" className="text-blue-600 hover:underline">
            Create a profile
          </Link>
        </p>
      </form>
    </div>
  )
}
