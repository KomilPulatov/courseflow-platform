import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getSectionEligibility, type EligibilityResponse } from '../api/courses'
import EligibilityChecklist from '../components/EligibilityChecklist'

export default function EligibilityPage() {
  const { sectionId } = useParams<{ sectionId: string }>()
  const id = Number(sectionId)
  const [data, setData] = useState<EligibilityResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getSectionEligibility(id)
      .then(setData)
      .catch(() => setError('Could not load eligibility. Are you logged in?'))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="p-8 text-gray-500">Checking eligibility…</div>

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-xl mx-auto px-4 py-8">
        <Link
          to={`/student/sections/${id}`}
          className="text-sm text-gray-400 hover:text-gray-600 mb-6 block"
        >
          ← Section detail
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Eligibility check</h1>

        {error && <p className="text-red-500 text-sm">{error}</p>}

        {data && (
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-6">
              <span
                className={`text-sm font-semibold px-3 py-1 rounded-full ${
                  data.eligible
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-600'
                }`}
              >
                {data.eligible ? 'Eligible' : 'Not eligible'}
              </span>
              {!data.gpa_rules_enabled && (
                <span className="text-xs text-gray-400">GPA rules skipped (manual profile)</span>
              )}
            </div>
            <EligibilityChecklist checks={data.checks} />
          </div>
        )}
      </div>
    </div>
  )
}
