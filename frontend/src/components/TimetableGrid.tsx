import type { TimetableItem } from '../api/registrations'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

function timeToMinutes(t: string) {
  const [h, m] = t.split(':').map(Number)
  return h * 60 + m
}

function formatTime(t: string) {
  const [h, m] = t.split(':').map(Number)
  const ampm = h >= 12 ? 'PM' : 'AM'
  const hour = h % 12 || 12
  return `${hour}:${m.toString().padStart(2, '0')} ${ampm}`
}

export default function TimetableGrid({ items }: { items: TimetableItem[] }) {
  if (items.length === 0) {
    return <p className="text-gray-500 text-sm">No scheduled classes yet.</p>
  }

  const byDay: Record<string, TimetableItem[]> = {}
  for (const item of items) {
    const day = item.day_of_week
    if (!byDay[day]) byDay[day] = []
    byDay[day].push(item)
  }

  const activeDays = DAYS.filter((d) => byDay[d]?.length)

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm border-collapse">
        <thead>
          <tr>
            {activeDays.map((day) => (
              <th
                key={day}
                className="border border-gray-200 bg-gray-50 px-3 py-2 text-left font-semibold text-gray-700"
              >
                {day}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <tr>
            {activeDays.map((day) => (
              <td key={day} className="border border-gray-200 px-3 py-2 align-top">
                {(byDay[day] ?? [])
                  .sort(
                    (a, b) =>
                      timeToMinutes(a.start_time) - timeToMinutes(b.start_time),
                  )
                  .map((item) => (
                    <div
                      key={item.enrollment_id}
                      className="mb-2 p-2 bg-blue-50 border border-blue-200 rounded-lg"
                    >
                      <p className="font-semibold text-blue-800">{item.course_code}</p>
                      <p className="text-xs text-blue-600 truncate">{item.course_title}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatTime(item.start_time)} – {formatTime(item.end_time)}
                      </p>
                    </div>
                  ))}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  )
}
