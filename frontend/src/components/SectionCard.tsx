import { Link } from 'react-router-dom'
import type { SectionSummary } from '../api/courses'

interface Props {
  section: SectionSummary
  showCourse?: boolean
}

export default function SectionCard({ section, showCourse = false }: Props) {
  const isFull = section.remaining_seats === 0
  const statusColor =
    section.status === 'open'
      ? 'bg-green-100 text-green-700'
      : section.status === 'closed'
        ? 'bg-red-100 text-red-600'
        : 'bg-gray-100 text-gray-500'

  return (
    <div className="border border-gray-200 rounded-xl p-4 bg-white hover:shadow-sm transition-shadow">
      <div className="flex items-start justify-between gap-2">
        <div>
          {showCourse && (
            <p className="text-sm font-semibold text-gray-800">
              {section.course_code} — {section.course_title}
            </p>
          )}
          <p className="text-sm text-gray-600">Section {section.section_code}</p>
          {section.semester_name && (
            <p className="text-xs text-gray-400">{section.semester_name}</p>
          )}
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${statusColor}`}>
          {section.status}
        </span>
      </div>

      <div className="mt-3 flex gap-4 text-sm text-gray-600">
        <span>
          <span className="font-medium">{section.enrolled_count}</span>/{section.capacity} enrolled
        </span>
        {isFull ? (
          <span className="text-amber-600 font-medium">
            Full · {section.waitlist_count} waiting
          </span>
        ) : (
          <span className="text-green-600 font-medium">
            {section.remaining_seats} seats left
          </span>
        )}
      </div>

      <Link
        to={`/student/sections/${section.id}`}
        className="mt-3 inline-block text-sm text-blue-600 hover:underline"
      >
        View details →
      </Link>
    </div>
  )
}
