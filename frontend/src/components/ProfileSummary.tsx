import type { StudentProfile } from '../api/profile'

export default function ProfileSummary({ profile }: { profile: StudentProfile }) {
  const ap = profile.academic_profile
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-lg">
          {profile.full_name[0]?.toUpperCase()}
        </div>
        <div>
          <p className="font-semibold text-gray-900">{profile.full_name}</p>
          <p className="text-xs text-gray-400">{profile.student_number}</p>
        </div>
        <span
          className={`ml-auto text-xs px-2 py-0.5 rounded-full font-medium ${
            profile.profile_source === 'ins_verified'
              ? 'bg-green-100 text-green-700'
              : 'bg-amber-100 text-amber-700'
          }`}
        >
          {profile.profile_source === 'ins_verified' ? 'INS Verified' : 'Manual'}
        </span>
      </div>
      {ap && (
        <div className="mt-3 grid grid-cols-2 gap-2 text-sm text-gray-600">
          {ap.department_name && <span>{ap.department_name}</span>}
          {ap.major_name && <span>{ap.major_name}</span>}
          {ap.academic_year && <span>Year {ap.academic_year}</span>}
          {ap.current_gpa != null && profile.gpa_rules_enabled && (
            <span>GPA {ap.current_gpa.toFixed(2)}</span>
          )}
        </div>
      )}
    </div>
  )
}
