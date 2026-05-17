export type Page<T> = {
  items: T[];
  total: number;
  limit: number;
  offset: number;
};

export type Semester = {
  id: number;
  name: string;
  status: "draft" | "active" | "archived";
};

export type Department = {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
};

export type Major = {
  id: number;
  department_id: number;
  code: string;
  name: string;
  is_active: boolean;
};

export type CourseSummary = {
  id: number;
  department_id: number | null;
  department_code: string | null;
  department_name: string | null;
  code: string;
  title: string;
  credits: number;
  course_type: string | null;
  active_offering_count: number;
  active_section_count: number;
  is_active: boolean;
};

export type CourseDetail = {
  id: number;
  department_id: number | null;
  department_code: string | null;
  department_name: string | null;
  code: string;
  title: string;
  credits: number;
  course_type: string | null;
  description: string | null;
  is_repeatable: boolean;
  is_active: boolean;
  prerequisites: Array<{ id: number; code: string; title: string }>;
};

export type EligibilityRule = {
  id: number;
  course_id: number;
  min_academic_year: number | null;
  min_gpa: number | null;
  allowed_department_ids: number[] | null;
  allowed_major_ids: number[] | null;
  rule_metadata: Record<string, unknown> | null;
};

export type Professor = {
  id: number;
  user_id: number;
  email: string | null;
  full_name: string;
  department_name: string | null;
  is_active: boolean;
};

export type Room = {
  id: number;
  building: string | null;
  room_number: string;
  capacity: number;
  room_type: string;
  is_active: boolean;
};

export type Offering = {
  id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  semester_id: number;
  semester_name: string;
  status: "draft" | "active" | "cancelled" | "archived";
  section_count: number;
};

export type Section = {
  id: number;
  course_offering_id: number;
  course_id: number;
  course_code: string;
  course_title: string;
  semester_id: number;
  semester_name: string;
  professor_id: number | null;
  section_code: string;
  capacity: number;
  enrolled_count: number;
  remaining_seats: number;
  waitlist_count: number;
  room_selection_mode: "admin_fixed" | "professor_choice" | "system_recommended";
  status: "draft" | "open" | "closed" | "cancelled";
};

export type RoomAllocation = {
  section_id: number;
  room_id: number;
  building: string | null;
  room_number: string;
  capacity: number;
  room_type: string;
  available: boolean;
};

export type RegistrationPeriod = {
  id: number;
  semester_id: number;
  semester_name: string;
  opens_at: string;
  closes_at: string;
  status: "open" | "closed";
};

export type SuggestionRun = {
  id: number;
  semester_id: number;
  semester_name: string;
  strategy: string;
  status: string;
  created_at: string;
  completed_at: string | null;
  approved_at: string | null;
};

export type SuggestionRunDetail = {
  id: number;
  semester_id: number;
  strategy: string;
  status: string;
  items: Array<{
    id: number;
    section_id: number;
    room_id: number | null;
    time_slot_id: number | null;
    score: number;
    reasons: Record<string, unknown> | null;
    status: string;
  }>;
};

export type AuditLog = {
  id: number;
  actor_student_id: number | null;
  event_type: string;
  entity_type: string;
  entity_id: number | null;
  payload: Record<string, unknown> | null;
  created_at: string;
};

export type Health = {
  status: string;
  checks?: Record<string, string>;
};
