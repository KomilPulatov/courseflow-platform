import client from './client'

export interface RegistrationCreate {
  section_id: number
  idempotency_key: string
}

export interface EnrolledResponse {
  status: 'enrolled'
  enrollment_id: number
  section_id: number
  remaining_seats: number
}

export interface WaitlistedResponse {
  status: 'waitlisted'
  waitlist_entry_id: number
  position: number
}

export interface ErrorResponse {
  status: 'error'
  error_code: string
  message: string
}

export type RegistrationResult = EnrolledResponse | WaitlistedResponse | ErrorResponse

export interface RegistrationListItem {
  enrollment_id: number
  section_id: number
  course_id: number
  course_code: string
  course_title: string
  semester_id: number
  semester_name: string
  status: string
}

export interface TimetableItem {
  enrollment_id: number
  section_id: number
  course_code: string
  course_title: string
  day_of_week: string
  start_time: string
  end_time: string
}

export async function register(data: RegistrationCreate): Promise<RegistrationResult> {
  const res = await client.post('/api/v1/registrations', data)
  return res.data
}

export async function dropRegistration(
  enrollmentId: number,
): Promise<{ status: string; enrollment_id: number; section_id: number }> {
  const res = await client.delete(`/api/v1/registrations/${enrollmentId}`)
  return res.data
}

export async function getMyRegistrations(): Promise<RegistrationListItem[]> {
  const res = await client.get('/api/v1/registrations/me')
  return res.data
}

export async function getMyTimetable(): Promise<TimetableItem[]> {
  const res = await client.get('/api/v1/registrations/me/timetable')
  return res.data
}
