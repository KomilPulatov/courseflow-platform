import { Link } from 'react-router-dom'

const roles = [
  {
    title: 'Student',
    description: 'Browse courses, register for sections, manage your schedule.',
    href: '/login/student',
    color: 'border-blue-300 hover:border-blue-500 hover:bg-blue-50',
    icon: '🎓',
  },
  {
    title: 'Professor',
    description: 'View your sections and choose rooms.',
    href: '/login/professor',
    color: 'border-green-300 hover:border-green-500 hover:bg-green-50',
    icon: '👨‍🏫',
  },
  {
    title: 'Administrator',
    description: 'Manage semesters, courses, rooms, and registration periods.',
    href: '/login/admin',
    color: 'border-purple-300 hover:border-purple-500 hover:bg-purple-50',
    icon: '🛠',
  },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="max-w-xl w-full text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-900">CRSP</h1>
        <p className="mt-2 text-gray-500 text-lg">Course Registration &amp; Scheduling Platform</p>
      </div>
      <div className="max-w-xl w-full space-y-4">
        {roles.map((r) => (
          <Link
            key={r.title}
            to={r.href}
            className={`block border-2 rounded-2xl p-5 bg-white transition-colors ${r.color}`}
          >
            <div className="flex items-center gap-4">
              <span className="text-3xl">{r.icon}</span>
              <div className="text-left">
                <p className="font-semibold text-gray-900 text-lg">{r.title}</p>
                <p className="text-sm text-gray-500">{r.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
