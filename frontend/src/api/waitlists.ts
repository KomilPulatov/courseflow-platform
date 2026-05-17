import client from './client'

export interface WaitlistItem {
  waitlist_entry_id: number
  section_id: number
  position: number
  status: string
}

export async function getMyWaitlists(): Promise<WaitlistItem[]> {
  const res = await client.get('/api/v1/waitlists/me')
  return res.data
}

export async function joinWaitlist(section_id: number): Promise<WaitlistItem> {
  const res = await client.post('/api/v1/waitlists', { section_id })
  return res.data
}

export async function cancelWaitlist(
  waitlistEntryId: number,
): Promise<{ status: string; waitlist_entry_id: number }> {
  const res = await client.delete(`/api/v1/waitlists/${waitlistEntryId}`)
  return res.data
}
