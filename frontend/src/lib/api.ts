import type {
  AuditLog,
  CourseDetail,
  CourseSummary,
  Department,
  EligibilityRule,
  Health,
  Major,
  Offering,
  Page,
  Professor,
  RegistrationPeriod,
  Room,
  RoomAllocation,
  Section,
  Semester,
  SuggestionRun,
  SuggestionRunDetail,
} from "./types";

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
  token?: string | null;
};

export const authStore = {
  admin: {
    get: () => localStorage.getItem("crspAdminToken"),
    set: (token: string) => localStorage.setItem("crspAdminToken", token),
    clear: () => localStorage.removeItem("crspAdminToken"),
  },
  professor: {
    get: () => localStorage.getItem("crspProfessorToken"),
    set: (token: string) => localStorage.setItem("crspProfessorToken", token),
    clear: () => localStorage.removeItem("crspProfessorToken"),
  },
  student: {
    get: () => localStorage.getItem("crspStudentToken"),
    set: (token: string) => localStorage.setItem("crspStudentToken", token),
    clear: () => localStorage.removeItem("crspStudentToken"),
  },
};

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, {
    ...options,
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });
  const contentType = response.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const message =
      typeof data === "string" ? data || "Request failed." : data.detail ?? data.message ?? "Request failed.";
    throw new Error(message);
  }
  return data as T;
}

function adminRequest<T>(path: string, options: RequestOptions = {}) {
  return request<T>(path, { ...options, token: authStore.admin.get() });
}

export const adminApi = {
  login: (body: { email: string; password: string }) =>
    request<{ access_token: string; role: string }>("/api/v1/auth/admin/login", {
      method: "POST",
      body,
    }),
  departments: () => adminRequest<Department[]>("/api/v1/admin/departments"),
  createDepartment: (body: unknown) =>
    adminRequest<Department>("/api/v1/admin/departments", { method: "POST", body }),
  updateDepartment: (id: number, body: unknown) =>
    adminRequest<Department>(`/api/v1/admin/departments/${id}`, { method: "PATCH", body }),
  majors: (departmentId?: number) =>
    adminRequest<Major[]>(
      `/api/v1/admin/majors${departmentId ? `?department_id=${departmentId}` : ""}`,
    ),
  createMajor: (body: unknown) =>
    adminRequest<Major>("/api/v1/admin/majors", { method: "POST", body }),
  updateMajor: (id: number, body: unknown) =>
    adminRequest<Major>(`/api/v1/admin/majors/${id}`, { method: "PATCH", body }),
  semesters: () => adminRequest<Semester[]>("/api/v1/admin/semesters"),
  createSemester: (body: unknown) =>
    adminRequest<Semester>("/api/v1/admin/semesters", { method: "POST", body }),
  updateSemester: (id: number, body: unknown) =>
    adminRequest<Semester>(`/api/v1/admin/semesters/${id}`, { method: "PATCH", body }),
  courses: (params: URLSearchParams) =>
    adminRequest<Page<CourseSummary>>(`/api/v1/admin/courses?${params.toString()}`),
  createCourse: (body: unknown) =>
    adminRequest<CourseDetail>("/api/v1/admin/courses", { method: "POST", body }),
  course: (id: number) => adminRequest<CourseDetail>(`/api/v1/admin/courses/${id}`),
  updateCourse: (id: number, body: unknown) =>
    adminRequest<CourseDetail>(`/api/v1/admin/courses/${id}`, { method: "PATCH", body }),
  replacePrerequisites: (id: number, body: unknown) =>
    adminRequest(`/api/v1/admin/courses/${id}/prerequisites`, { method: "PUT", body }),
  eligibilityRules: (id: number) =>
    adminRequest<EligibilityRule[]>(`/api/v1/admin/courses/${id}/eligibility-rules`),
  createEligibilityRule: (id: number, body: unknown) =>
    adminRequest<EligibilityRule>(`/api/v1/admin/courses/${id}/eligibility-rules`, {
      method: "POST",
      body,
    }),
  updateEligibilityRule: (courseId: number, ruleId: number, body: unknown) =>
    adminRequest<EligibilityRule>(
      `/api/v1/admin/courses/${courseId}/eligibility-rules/${ruleId}`,
      { method: "PATCH", body },
    ),
  deleteEligibilityRule: (courseId: number, ruleId: number) =>
    adminRequest<void>(`/api/v1/admin/courses/${courseId}/eligibility-rules/${ruleId}`, {
      method: "DELETE",
    }),
  professors: () => adminRequest<Professor[]>("/api/v1/admin/professors"),
  createProfessor: (body: unknown) =>
    adminRequest<Professor>("/api/v1/admin/professors", { method: "POST", body }),
  updateProfessor: (id: number, body: unknown) =>
    adminRequest<Professor>(`/api/v1/admin/professors/${id}`, { method: "PATCH", body }),
  rooms: () => adminRequest<Room[]>("/api/v1/admin/rooms"),
  createRoom: (body: unknown) => adminRequest<Room>("/api/v1/admin/rooms", { method: "POST", body }),
  updateRoom: (id: number, body: unknown) =>
    adminRequest<Room>(`/api/v1/admin/rooms/${id}`, { method: "PATCH", body }),
  offerings: (semesterId?: number) =>
    adminRequest<Offering[]>(
      `/api/v1/admin/course-offerings${semesterId ? `?semester_id=${semesterId}` : ""}`,
    ),
  createOffering: (body: unknown) =>
    adminRequest<Offering>("/api/v1/admin/course-offerings", { method: "POST", body }),
  updateOffering: (id: number, body: unknown) =>
    adminRequest<Offering>(`/api/v1/admin/course-offerings/${id}`, { method: "PATCH", body }),
  sections: (params: URLSearchParams) =>
    adminRequest<Page<Section>>(`/api/v1/admin/sections?${params.toString()}`),
  createSection: (body: unknown) =>
    adminRequest<Section>("/api/v1/admin/sections", { method: "POST", body }),
  updateSection: (id: number, body: unknown) =>
    adminRequest<Section>(`/api/v1/admin/sections/${id}`, { method: "PATCH", body }),
  section: (id: number) => request<Section>(`/api/v1/sections/${id}`),
  roomAllocations: (sectionId: number) =>
    adminRequest<RoomAllocation[]>(`/api/v1/admin/sections/${sectionId}/room-allocations`),
  allocateRooms: (sectionId: number, body: unknown) =>
    adminRequest<RoomAllocation[]>(`/api/v1/admin/sections/${sectionId}/room-allocations`, {
      method: "POST",
      body,
    }),
  removeRoomAllocation: (sectionId: number, roomId: number) =>
    adminRequest<void>(`/api/v1/admin/sections/${sectionId}/room-allocations/${roomId}`, {
      method: "DELETE",
    }),
  registrationPeriods: (semesterId?: number) =>
    adminRequest<RegistrationPeriod[]>(
      `/api/v1/admin/registration-periods${semesterId ? `?semester_id=${semesterId}` : ""}`,
    ),
  createRegistrationPeriod: (body: unknown) =>
    adminRequest<RegistrationPeriod>("/api/v1/admin/registration-periods", {
      method: "POST",
      body,
    }),
  updateRegistrationPeriod: (id: number, body: unknown) =>
    adminRequest<RegistrationPeriod>(`/api/v1/admin/registration-periods/${id}`, {
      method: "PATCH",
      body,
    }),
  schedulingRuns: (params: URLSearchParams) =>
    adminRequest<Page<SuggestionRun>>(`/api/v1/admin/scheduling/suggestion-runs?${params.toString()}`),
  createSchedulingRun: (body: unknown) =>
    adminRequest<{ run_id: number; status: string }>("/api/v1/admin/scheduling/suggestion-runs", {
      method: "POST",
      body,
    }),
  schedulingRun: (id: number) =>
    adminRequest<SuggestionRunDetail>(`/api/v1/admin/scheduling/suggestion-runs/${id}`),
  approveSchedulingRun: (id: number) =>
    adminRequest<{ run_id: number; status: string; approved_items: number }>(
      `/api/v1/admin/scheduling/suggestion-runs/${id}/approve`,
      { method: "POST" },
    ),
  auditLogs: (params: URLSearchParams) =>
    adminRequest<Page<AuditLog>>(`/api/v1/admin/audit-logs?${params.toString()}`),
  health: () => request<Health>("/health"),
  dependencyHealth: () => request<Health>("/api/v1/health/dependencies"),
  metrics: () => request<string>("/metrics"),
};

export const publicApi = {
  courses: (params: URLSearchParams) =>
    request<CourseSummary[]>(`/api/v1/courses${params.toString() ? `?${params.toString()}` : ""}`),
  course: (id: number) => request<CourseDetail>(`/api/v1/courses/${id}`),
  courseSections: (id: number) => request<Section[]>(`/api/v1/courses/${id}/sections`),
  section: (id: number) => request<Section>(`/api/v1/sections/${id}`),
  sectionAvailability: (id: number) => request(`/api/v1/sections/${id}/availability`),
};
