import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  getSection,
  getSectionEligibility,
  type SectionSummary,
  type EligibilityResponse,
} from '../api/courses'
import { register } from '../api/registrations'
import { apiErrorMessage } from '../api/errors'
import { joinWaitlist } from '../api/waitlists'
import { useSectionWS } from '../hooks/useSectionWS'
import EligibilityChecklist from '../components/EligibilityChecklist'

const ERROR_MESSAGES: Record<string, string> = {
  duplicate_registration: 'Already registered for this course this semester.',
  prerequisites_failed: 'Missing prerequisites.',
  gpa_below_minimum: 'GPA is below the required minimum.',
  credit_limit_exceeded: 'Would exceed the 18-credit semester limit.',
  timetable_conflict: 'Conflicts with an existing class in your schedule.',
  registration_period_closed: 'Registration is not currently open.',
  section_full: 'Section is full — you may join the waitlist instead.',
  profile_incomplete: 'Complete your academic profile first.',
}

export default function SectionDetail() {
  const { sectionId } = useParams<{ sectionId: string }>()
  const id = Number(sectionId)

  const [section, setSection] = useState<SectionSummary | null>(null)
  const [eligibility, setEligibility] = useState<EligibilityResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [result, setResult] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const [idemKey] = useState(() => crypto.randomUUID())
  const liveAvail = useSectionWS(id)

  useEffect(() => {
    Promise.all([
      getSection(id),
      getSectionEligibility(id).catch(() => null),
    ])
      .then(([s, e]) => {
        setSection(s)
        setEligibility(e)
      })
      .finally(() => setLoading(false))
  }, [id])

  const seats = liveAvail ?? {
    remaining_seats: section?.remaining_seats ?? 0,
    enrolled_count: section?.enrolled_count ?? 0,
    waitlist_count: section?.waitlist_count ?? 0,
    capacity: section?.capacity ?? 0,
  }

  async function handleRegister() {
    setActionLoading(true)
    setResult(null)
    try {
      const res = await register({ section_id: id, idempotency_key: idemKey })
      if (res.status === 'enrolled') {
        setResult({ type: 'success', message: 'Enrolled successfully!' })
      } else if (res.status === 'waitlisted') {
        setResult({ type: 'success', message: `Added to waitlist at position ${res.position}.` })
      } else {
        setResult({ type: 'error', message: ERROR_MESSAGES[res.error_code] ?? res.message ?? 'Registration failed.' })
      }
    } catch (err: unknown) {
      setResult({ type: 'error', message: apiErrorMessage(err, 'Something went wrong.') })
    } finally {
      setActionLoading(false)
    }
  }

  async function handleJoinWaitlist() {
    setActionLoading(true)
    setResult(null)
    try {
      const res = await joinWaitlist(id)
      setResult({ type: 'success', message: `Joined waitlist at position ${res.position}.` })
    } catch (err: unknown) {
      setResult({ type: 'error', message: apiErrorMessage(err, 'Could not join waitlist.') })
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) return <div className="p-8 text-gray-500">Loading…</div>
  if (!section) return <div className="p-8 text-red-500">Section not found.</div>

  const isFull = seats.remaining_seats === 0
  const canRegister = eligibility?.eligible ?? false

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Link
          to={`/student/courses/${section.course_id}`}
          className="text-sm text-gray-400 hover:text-gray-600 mb-6 block"
        >
          ← {section.course_code}
        </Link>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 mb-6">
          <div className="flex items-start justify-between gap-2 mb-1">
            <h1 className="text-xl font-bold text-gray-900">
              {section.course_code} · Section {section.section_code}
            </h1>
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                section.status === 'open'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-500'
              }`}
            >
              {section.status}
            </span>
          </div>
          <p className="text-sm text-gray-500 mb-4">{section.course_title}</p>

          <div className="grid grid-cols-3 gap-3 text-center mb-4">
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-2xl font-bold text-gray-900">{seats.capacity}</p>
              <p className="text-xs text-gray-400">Capacity</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-3">
              <p className={`text-2xl font-bold ${isFull ? 'text-red-500' : 'text-green-600'}`}>
                {seats.remaining_seats}
              </p>
              <p className="text-xs text-gray-400">Seats left</p>
            </div>
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-2xl font-bold text-amber-500">{seats.waitlist_count}</p>
              <p className="text-xs text-gray-400">Waitlist</p>
            </div>
          </div>

          {result && (
            <div
              className={`mb-4 p-3 rounded-xl text-sm ${
                result.type === 'success'
                  ? 'bg-green-50 border border-green-200 text-green-700'
                  : 'bg-red-50 border border-red-200 text-red-600'
              }`}
            >
              {result.message}
            </div>
          )}

          <div className="flex gap-3">
            {!isFull && (
              <button
                onClick={handleRegister}
                disabled={actionLoading || !canRegister}
                className="flex-1 bg-blue-600 text-white rounded-xl py-2.5 font-semibold text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {actionLoading ? 'Processing…' : 'Register'}
              </button>
            )}
            {isFull && (
              <button
                onClick={handleJoinWaitlist}
                disabled={actionLoading}
                className="flex-1 bg-amber-500 text-white rounded-xl py-2.5 font-semibold text-sm hover:bg-amber-600 disabled:opacity-50 transition-colors"
              >
                {actionLoading ? 'Processing…' : 'Join waitlist'}
              </button>
            )}
            <Link
              to={`/student/sections/${id}/eligibility`}
              className="px-4 py-2.5 border border-gray-200 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Eligibility
            </Link>
          </div>

          {!canRegister && eligibility && (
            <p className="mt-3 text-xs text-red-500">
              You are not eligible for this section. See eligibility details.
            </p>
          )}
        </div>

        {eligibility && (
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
              Eligibility
            </h2>
            <EligibilityChecklist checks={eligibility.checks} />
          </div>
        )}
      </div>
    </div>
  )
}
