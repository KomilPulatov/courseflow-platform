import client from './client'

export interface AcademicProfile {
  department_id: number | null
  major_id: number | null
  department_name: string | null
  major_name: string | null
  academic_year: number | null
  current_gpa: number | null
  gpa_is_verified: boolean
  academic_status: string | null
}

export interface CompletedCourse {
  course_code: string
  course_title: string | null
  grade: string | null
  credits: number | null
  source: string
}

export interface StudentProfile {
  student_number: string
  full_name: string
  profile_source: 'ins_verified' | 'manual'
  gpa_rules_enabled: boolean
  academic_profile: AcademicProfile | null
  completed_courses: CompletedCourse[]
}

export interface ManualProfileUpdate {
  department_id?: number | null
  major_id?: number | null
  department_name?: string | null
  major_name?: string | null
  academic_year: number
  completed_course_codes: string[]
}

export async function getMyProfile(): Promise<StudentProfile> {
  const res = await client.get('/api/v1/student-profiles/me')
  return res.data
}

export async function updateManualProfile(data: ManualProfileUpdate): Promise<StudentProfile> {
  const res = await client.put('/api/v1/student-profiles/me/manual', data)
  return res.data
}

export async function syncINSProfile(password: string): Promise<StudentProfile> {
  const res = await client.post('/api/v1/student-profiles/me/sync-ins', { password })
  return res.data
}
