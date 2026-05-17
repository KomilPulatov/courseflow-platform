import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyProfile, type StudentProfile } from '../api/profile'

export default function Profile() {
  const [profile, setProfile] = useState<StudentProfile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMyProfile()
      .then(setProfile)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-8 text-gray-500">Loading profile…</div>
  if (!profile) return <div className="p-8 text-red-500">Failed to load profile.</div>

  const ap = profile.academic_profile

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Link to="/student" className="text-sm text-gray-400 hover:text-gray-600 mb-6 block">
          ← Dashboard
        </Link>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">{profile.full_name}</h1>
              <p className="text-sm text-gray-400">{profile.student_number}</p>
            </div>
            <span
              className={`text-xs px-3 py-1 rounded-full font-medium ${
                profile.profile_source === 'ins_verified'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-amber-100 text-amber-700'
              }`}
            >
              {profile.profile_source === 'ins_verified' ? 'INS Verified' : 'Manual'}
            </span>
          </div>

          {ap ? (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Academic profile
              </h2>
              <dl className="grid grid-cols-2 gap-3 text-sm">
                {ap.department_name && (
                  <>
                    <dt className="text-gray-500">Department</dt>
                    <dd className="text-gray-900">{ap.department_name}</dd>
                  </>
                )}
                {ap.major_name && (
                  <>
                    <dt className="text-gray-500">Major</dt>
                    <dd className="text-gray-900">{ap.major_name}</dd>
                  </>
                )}
                {ap.academic_year && (
                  <>
                    <dt className="text-gray-500">Year</dt>
                    <dd className="text-gray-900">Year {ap.academic_year}</dd>
                  </>
                )}
                {ap.current_gpa != null && (
                  <>
                    <dt className="text-gray-500">GPA</dt>
                    <dd className="text-gray-900">
                      {ap.current_gpa.toFixed(2)}
                      {!ap.gpa_is_verified && (
                        <span className="text-xs text-gray-400 ml-1">(not verified)</span>
                      )}
                    </dd>
                  </>
                )}
                {ap.academic_status && (
                  <>
                    <dt className="text-gray-500">Status</dt>
                    <dd className="text-gray-900">{ap.academic_status}</dd>
                  </>
                )}
              </dl>
            </section>
          ) : (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm">
              <p className="text-amber-700">No academic profile yet.</p>
              {profile.profile_source === 'manual' && (
                <Link
                  to="/student/profile/manual"
                  className="mt-1 inline-block font-semibold text-amber-700 hover:underline"
                >
                  Complete manual profile →
                </Link>
              )}
            </div>
          )}

          {profile.completed_courses.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
                Completed courses ({profile.completed_courses.length})
              </h2>
              <ul className="divide-y divide-gray-100">
                {profile.completed_courses.map((c) => (
                  <li key={c.course_code} className="py-2 flex justify-between text-sm">
                    <span>
                      <span className="font-medium text-gray-800">{c.course_code}</span>
                      {c.course_title && (
                        <span className="text-gray-500"> — {c.course_title}</span>
                      )}
                    </span>
                    <span className="text-gray-400">
                      {c.grade ?? '—'} {c.credits != null ? `· ${c.credits} cr` : ''}
                    </span>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {profile.profile_source === 'manual' && (
            <Link
              to="/student/profile/manual"
              className="block text-center text-sm font-semibold text-blue-600 hover:underline"
            >
              Edit profile
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}
