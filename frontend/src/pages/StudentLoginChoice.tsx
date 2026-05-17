import { Link } from 'react-router-dom'

export default function StudentLoginChoice() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="max-w-sm w-full">
        <Link to="/" className="text-sm text-gray-400 hover:text-gray-600 mb-6 block">
          ← Back
        </Link>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Student login</h2>
        <p className="text-gray-500 mb-8">Choose how to continue.</p>
        <div className="space-y-4">
          <Link
            to="/student/ins-login"
            className="block border-2 border-blue-300 hover:border-blue-500 hover:bg-blue-50 rounded-2xl p-5 bg-white transition-colors"
          >
            <p className="font-semibold text-gray-900">Continue with INS</p>
            <p className="text-sm text-gray-500 mt-1">
              Use your IUT INS credentials. Your academic data is synced automatically.
            </p>
          </Link>
          <Link
            to="/student/manual-login"
            className="block border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-50 rounded-2xl p-5 bg-white transition-colors"
          >
            <p className="font-semibold text-gray-900">Sign in with email</p>
            <p className="text-sm text-gray-500 mt-1">
              Already have a manual profile? Sign in with your email and password.
            </p>
          </Link>
          <Link
            to="/student/manual-start"
            className="block border-2 border-gray-200 hover:border-gray-400 hover:bg-gray-50 rounded-2xl p-5 bg-white transition-colors"
          >
            <p className="font-semibold text-gray-900">Create manual profile</p>
            <p className="text-sm text-gray-500 mt-1">
              New here? Enter your academic information manually. GPA rules will be skipped.
            </p>
          </Link>
        </div>
      </div>
    </div>
  )
}
