import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getMyWaitlists, cancelWaitlist, type WaitlistItem } from '../api/waitlists'
import { useRegistrationWS } from '../hooks/useRegistrationWS'

export default function Waitlist() {
  const [entries, setEntries] = useState<WaitlistItem[]>([])
  const [loading, setLoading] = useState(true)
  const [cancelling, setCancelling] = useState<number | null>(null)
  const [toast, setToast] = useState('')

  const userId = localStorage.getItem('crsp_user_id') ?? ''
  const wsEvent = useRegistrationWS(userId)

  const load = useCallback(() => {
    return getMyWaitlists()
      .then(setEntries)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    getMyWaitlists()
      .then(setEntries)
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    if (wsEvent?.type === 'waitlist_promoted') {
      const toastTimer = setTimeout(() => {
        setToast('You have been promoted from the waitlist!')
        load()
      }, 0)
      const clearTimer = setTimeout(() => setToast(''), 5000)
      return () => {
        clearTimeout(toastTimer)
        clearTimeout(clearTimer)
      }
    }
  }, [load, wsEvent])

  async function handleCancel(entryId: number) {
    if (!confirm('Leave this waitlist?')) return
    setCancelling(entryId)
    try {
      await cancelWaitlist(entryId)
      load()
    } catch {
      alert('Could not cancel. Please try again.')
    } finally {
      setCancelling(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 py-8">
        <Link to="/student" className="text-sm text-gray-400 hover:text-gray-600 mb-6 block">
          ← Dashboard
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">My waitlists</h1>

        {toast && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-xl text-sm text-green-700">
            {toast}
          </div>
        )}

        {loading && <p className="text-gray-400 text-sm">Loading…</p>}

        {!loading && entries.length === 0 && (
          <div className="bg-white border border-gray-200 rounded-2xl p-6 text-center text-gray-400 text-sm">
            No waitlist entries.
          </div>
        )}

        <div className="space-y-3">
          {entries.map((e) => (
            <div
              key={e.waitlist_entry_id}
              className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between gap-4"
            >
              <div>
                <p className="font-semibold text-gray-900">Section #{e.section_id}</p>
                <p className="text-sm text-gray-500">
                  Position <span className="font-bold text-amber-600">#{e.position}</span>
                </p>
                <span className="text-xs text-gray-400">{e.status}</span>
              </div>
              <div className="flex gap-3 items-center">
                <Link
                  to={`/student/sections/${e.section_id}`}
                  className="text-sm text-blue-600 hover:underline"
                >
                  View
                </Link>
                <button
                  onClick={() => handleCancel(e.waitlist_entry_id)}
                  disabled={cancelling === e.waitlist_entry_id}
                  className="text-sm text-red-500 hover:text-red-700 font-medium disabled:opacity-50"
                >
                  {cancelling === e.waitlist_entry_id ? 'Cancelling…' : 'Cancel'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
