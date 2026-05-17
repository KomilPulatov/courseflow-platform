import client from './client'

export interface CourseSummary {
  id: number
  department_id: number
  department_code: string
  department_name: string
  code: string
  title: string
  credits: number
  course_type: string
  active_offering_count: number
  active_section_count: number
}

export interface CourseDetail extends CourseSummary {
  description: string | null
  is_repeatable: boolean
  prerequisites: { id: number; code: string; title: string }[]
}

export interface SectionSummary {
  id: number
  course_offering_id: number
  course_id: number
  course_code: string
  course_title: string
  semester_id: number
  semester_name: string
  professor_id: number | null
  section_code: string
  capacity: number
  enrolled_count: number
  remaining_seats: number
  waitlist_count: number
  room_selection_mode: string
  status: string
}

export interface SectionAvailability {
  section_id: number
  capacity: number
  enrolled_count: number
  remaining_seats: number
  waitlist_count: number
  status: string
}

export interface EligibilityCheck {
  rule: string
  status: 'passed' | 'failed' | 'skipped'
  message: string
}

export interface EligibilityResponse {
  section_id: number
  eligible: boolean
  profile_source: string
  gpa_rules_enabled: boolean
  checks: EligibilityCheck[]
}

export interface CatalogFilters {
  semester_id?: number
  department_id?: number
  major_id?: number
  search?: string
  eligible_only?: boolean
}

export async function listCourses(filters?: CatalogFilters): Promise<CourseSummary[]> {
  const res = await client.get('/api/v1/courses/', { params: filters })
  return res.data
}

export async function getCourse(courseId: number): Promise<CourseDetail> {
  const res = await client.get(`/api/v1/courses/${courseId}`)
  return res.data
}

export async function getCourseSections(
  courseId: number,
  semesterId?: number,
): Promise<SectionSummary[]> {
  const res = await client.get(`/api/v1/courses/${courseId}/sections`, {
    params: semesterId ? { semester_id: semesterId } : undefined,
  })
  return res.data
}

export async function getSection(sectionId: number): Promise<SectionSummary> {
  const res = await client.get(`/api/v1/sections/${sectionId}`)
  return res.data
}

export async function getSectionAvailability(sectionId: number): Promise<SectionAvailability> {
  const res = await client.get(`/api/v1/sections/${sectionId}/availability`)
  return res.data
}

export async function getSectionEligibility(sectionId: number): Promise<EligibilityResponse> {
  const res = await client.get(`/api/v1/sections/${sectionId}/eligibility`)
  return res.data
}
