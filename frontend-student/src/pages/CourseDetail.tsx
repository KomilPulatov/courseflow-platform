import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getCourse, getCourseSections, type CourseDetail as CourseDetailType, type SectionSummary } from '../api/courses'
import SectionCard from '../components/SectionCard'

export default function CourseDetail() {
  const { courseId } = useParams<{ courseId: string }>()
  const id = Number(courseId)
  const [course, setCourse] = useState<CourseDetailType | null>(null)
  const [sections, setSections] = useState<SectionSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getCourse(id), getCourseSections(id)])
      .then(([c, s]) => {
        setCourse(c)
        setSections(s)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="p-8 text-gray-500">Loading…</div>
  if (!course) return <div className="p-8 text-red-500">Course not found.</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Link to="/student/catalog" className="text-sm text-gray-400 hover:text-gray-600 mb-6 block">
          ← Catalog
        </Link>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-6">
          <div className="flex items-start justify-between gap-2 mb-2">
            <h1 className="text-xl font-bold text-gray-900">
              {course.code} — {course.title}
            </h1>
            <span className="text-sm text-gray-400 whitespace-nowrap">{course.credits} cr</span>
          </div>
          <p className="text-xs text-gray-400 mb-3">{course.department_name}</p>
          {course.description && (
            <p className="text-sm text-gray-600 mb-4">{course.description}</p>
          )}
          {course.prerequisites.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Prerequisites
              </p>
              <div className="flex flex-wrap gap-2">
                {course.prerequisites.map((p) => (
                  <span
                    key={p.id}
                    className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-lg"
                  >
                    {p.code} — {p.title}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Available sections ({sections.length})
        </h2>
        {sections.length === 0 && (
          <p className="text-gray-400 text-sm">No sections available.</p>
        )}
        <div className="space-y-3">
          {sections.map((s) => (
            <SectionCard key={s.id} section={s} />
          ))}
        </div>
      </div>
    </div>
  )
}
