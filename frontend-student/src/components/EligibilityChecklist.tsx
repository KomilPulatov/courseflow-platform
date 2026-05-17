import type { EligibilityCheck } from '../api/courses'

const RULE_LABELS: Record<string, string> = {
  academic_year: 'Academic year',
  gpa: 'GPA requirement',
  prerequisites: 'Prerequisites',
  department: 'Department restriction',
  major: 'Major restriction',
  credit_limit: 'Credit limit (18 max)',
  timetable_conflict: 'Timetable conflict',
  profile_complete: 'Profile complete',
}

export default function EligibilityChecklist({ checks }: { checks: EligibilityCheck[] }) {
  return (
    <ul className="space-y-2">
      {checks.map((c) => (
        <li key={c.rule} className="flex items-start gap-2 text-sm">
          {c.status === 'passed' && <span className="text-green-600 font-bold mt-0.5">✓</span>}
          {c.status === 'failed' && <span className="text-red-500 font-bold mt-0.5">✗</span>}
          {c.status === 'skipped' && <span className="text-gray-400 mt-0.5">—</span>}
          <span>
            <span className="font-medium text-gray-800">
              {RULE_LABELS[c.rule] ?? c.rule}
            </span>
            {c.message && (
              <span
                className={
                  c.status === 'failed'
                    ? ' text-red-500'
                    : c.status === 'skipped'
                      ? ' text-gray-400'
                      : ' text-gray-500'
                }
              >
                {' '}
                — {c.message}
              </span>
            )}
          </span>
        </li>
      ))}
    </ul>
  )
}
