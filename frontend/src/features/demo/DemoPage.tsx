import { FormEvent, ReactNode, useMemo, useRef, useState } from "react";

import { Badge } from "../../components/ui";
import { authStore, publicApi, request } from "../../lib/api";
import type { CourseSummary, Section } from "../../lib/types";

type Role = "admin" | "professor" | "student";

function tokenFor(role: Role) {
  return authStore[role].get();
}

function csvNumbers(value: FormDataEntryValue | null) {
  return String(value ?? "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .map(Number);
}

function csvStrings(value: FormDataEntryValue | null) {
  return String(value ?? "")
    .split(",")
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
}

export function DemoPage() {
  const [adminToken, setAdminToken] = useState(authStore.admin.get());
  const [professorToken, setProfessorToken] = useState(authStore.professor.get());
  const [studentToken, setStudentToken] = useState(authStore.student.get());
  const [courses, setCourses] = useState<CourseSummary[]>([]);
  const [sections, setSections] = useState<Section[]>([]);
  const [log, setLog] = useState("");
  const [socketStatus, setSocketStatus] = useState("Disconnected");
  const socketRef = useRef<WebSocket | null>(null);

  const logEvent = (title: string, payload: unknown) => {
    const block = `[${new Date().toLocaleTimeString()}] ${title}\n${
      typeof payload === "string" ? payload : JSON.stringify(payload, null, 2)
    }\n\n`;
    setLog((current) => block + current);
  };

  const withRequest = async <T,>(title: string, fn: () => Promise<T>) => {
    try {
      const result = await fn();
      logEvent(title, result);
      return result;
    } catch (error) {
      logEvent(`${title} failed`, error instanceof Error ? error.message : String(error));
      throw error;
    }
  };

  const onForm = (handler: (data: FormData) => Promise<unknown>) => async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    await handler(new FormData(form));
    form.reset();
  };

  const courseCards = useMemo(
    () =>
      courses.map((course) => (
        <article className="demo-result-card" key={course.id}>
          <h3>{course.code} · {course.title}</h3>
          <p className="muted">{course.department_code ?? "N/A"} · {course.credits} credits</p>
          <button
            type="button"
            onClick={() =>
              withRequest("Loaded course detail", async () => ({
                detail: await publicApi.course(course.id),
                sections: await publicApi.courseSections(course.id),
              }))
            }
          >
            View detail
          </button>
        </article>
      )),
    [courses],
  );

  return (
    <main className="demo-shell">
      <section className="demo-hero">
        <p className="eyebrow">CRSP Demo Console</p>
        <h1>Exercise the full academic flow from one React workspace.</h1>
        <p className="muted">
          The demo console preserves the original feature set while sharing the same typed API layer as the admin app.
        </p>
      </section>

      <section className="demo-grid">
        <section className="demo-panel">
          <div className="demo-panel-head">
            <h2>Sessions</h2>
            <div className="demo-pill-row">
              <Badge tone={adminToken ? "warm" : "muted"}>Admin</Badge>
              <Badge tone={professorToken ? "warm" : "muted"}>Professor</Badge>
              <Badge tone={studentToken ? "warm" : "muted"}>Student</Badge>
            </div>
          </div>
          <div className="demo-forms-grid">
            <DemoForm title="Admin login" onSubmit={onForm(async (data) => {
              const result = await withRequest("Admin login", () =>
                request<{ access_token: string }>("/api/v1/auth/admin/login", {
                  method: "POST",
                  body: { email: data.get("email"), password: data.get("password") },
                }),
              );
              authStore.admin.set(result.access_token);
              setAdminToken(result.access_token);
            })}>
              <input name="email" defaultValue="admin@crsp.example.com" />
              <input name="password" type="password" defaultValue="admin12345" />
            </DemoForm>
            <DemoForm title="Professor login" onSubmit={onForm(async (data) => {
              const result = await withRequest("Professor login", () =>
                request<{ access_token: string }>("/api/v1/auth/professor/login", {
                  method: "POST",
                  body: { email: data.get("email"), password: data.get("password") },
                }),
              );
              authStore.professor.set(result.access_token);
              setProfessorToken(result.access_token);
            })}>
              <input name="email" placeholder="professor email" />
              <input name="password" type="password" placeholder="password" />
            </DemoForm>
            <DemoForm title="Manual student start" onSubmit={onForm(async (data) => {
              const result = await withRequest("Manual student start", () =>
                request<{ access_token: string }>("/api/v1/auth/student/manual-start", {
                  method: "POST",
                  body: Object.fromEntries(data.entries()),
                }),
              );
              authStore.student.set(result.access_token);
              setStudentToken(result.access_token);
            })}>
              <input name="student_number" placeholder="student number" />
              <input name="full_name" placeholder="full name" />
              <input name="email" placeholder="email" />
              <input name="password" type="password" placeholder="password" />
            </DemoForm>
            <button
              className="ghost-button"
              type="button"
              onClick={() => {
                authStore.admin.clear();
                authStore.professor.clear();
                authStore.student.clear();
                setAdminToken(null);
                setProfessorToken(null);
                setStudentToken(null);
                logEvent("Tokens cleared", "All browser tokens removed.");
              }}
            >
              Clear tokens
            </button>
          </div>
        </section>

        <section className="demo-panel">
          <div className="demo-panel-head">
            <h2>Catalog browse</h2>
          </div>
          <form className="demo-inline-form" onSubmit={onForm(async (data) => {
            const params = new URLSearchParams();
            if (data.get("search")) params.set("search", String(data.get("search")));
            if (data.get("semester_id")) params.set("semester_id", String(data.get("semester_id")));
            const result = await withRequest("Catalog search", () => publicApi.courses(params));
            setCourses(result);
          })}>
            <input name="search" placeholder="code or title" />
            <input name="semester_id" placeholder="semester ID" />
            <button>Load</button>
          </form>
          <div className="demo-results">{courseCards}</div>
        </section>
      </section>

      <section className="demo-grid">
        <section className="demo-panel">
          <h2>Admin setup flow</h2>
          <div className="demo-forms-grid">
            <DemoForm title="Department" onSubmit={onForm((data) => withRequest("Create department", () => adminRequest("/api/v1/admin/departments", { code: data.get("code"), name: data.get("name") })))}>
              <input name="code" placeholder="CSE" />
              <input name="name" placeholder="Computer Science" />
            </DemoForm>
            <DemoForm title="Major" onSubmit={onForm((data) => withRequest("Create major", () => adminRequest("/api/v1/admin/majors", { department_id: Number(data.get("department_id")), code: data.get("code"), name: data.get("name") })))}>
              <input name="department_id" placeholder="department ID" />
              <input name="code" placeholder="SE" />
              <input name="name" placeholder="Software Engineering" />
            </DemoForm>
            <DemoForm title="Semester" onSubmit={onForm((data) => withRequest("Create semester", () => adminRequest("/api/v1/admin/semesters", { name: data.get("name"), status: data.get("status") })))}>
              <input name="name" placeholder="Spring 2026" />
              <select name="status" defaultValue="active"><option>active</option><option>draft</option><option>archived</option></select>
            </DemoForm>
            <DemoForm title="Course" onSubmit={onForm((data) => withRequest("Create course", () => adminRequest("/api/v1/admin/courses", { department_id: data.get("department_id") ? Number(data.get("department_id")) : null, code: data.get("code"), title: data.get("title"), credits: Number(data.get("credits")), course_type: data.get("course_type") || null })))}>
              <input name="department_id" placeholder="department ID" />
              <input name="code" placeholder="CSE3010" />
              <input name="title" placeholder="Databases" />
              <input name="credits" defaultValue="3" />
              <input name="course_type" placeholder="lecture" />
            </DemoForm>
            <DemoForm title="Prerequisites" onSubmit={onForm((data) => withRequest("Replace prerequisites", () => adminRequest(`/api/v1/admin/courses/${data.get("course_id")}/prerequisites`, { prerequisite_course_ids: csvNumbers(data.get("prerequisite_course_ids")), rule_group: "all" }, "PUT")))}>
              <input name="course_id" placeholder="course ID" />
              <input name="prerequisite_course_ids" placeholder="1, 2" />
            </DemoForm>
            <DemoForm title="Eligibility rule" onSubmit={onForm((data) => withRequest("Create eligibility rule", () => adminRequest(`/api/v1/admin/courses/${data.get("course_id")}/eligibility-rules`, { min_academic_year: data.get("min_academic_year") ? Number(data.get("min_academic_year")) : null, min_gpa: data.get("min_gpa") ? Number(data.get("min_gpa")) : null, allowed_department_ids: csvNumbers(data.get("department_ids")) || null, allowed_major_ids: csvNumbers(data.get("major_ids")) || null })))}>
              <input name="course_id" placeholder="course ID" />
              <input name="min_academic_year" placeholder="minimum year" />
              <input name="min_gpa" placeholder="minimum GPA" />
              <input name="department_ids" placeholder="department IDs" />
              <input name="major_ids" placeholder="major IDs" />
            </DemoForm>
            <DemoForm title="Offering" onSubmit={onForm((data) => withRequest("Create offering", () => adminRequest("/api/v1/admin/course-offerings", { course_id: Number(data.get("course_id")), semester_id: Number(data.get("semester_id")), status: "active" })))}>
              <input name="course_id" placeholder="course ID" />
              <input name="semester_id" placeholder="semester ID" />
            </DemoForm>
            <DemoForm title="Section" onSubmit={onForm((data) => withRequest("Create section", () => adminRequest("/api/v1/admin/sections", { course_offering_id: Number(data.get("course_offering_id")), professor_id: data.get("professor_id") ? Number(data.get("professor_id")) : null, section_code: data.get("section_code"), capacity: Number(data.get("capacity")), room_selection_mode: data.get("room_selection_mode"), status: "open" })))}>
              <input name="course_offering_id" placeholder="offering ID" />
              <input name="professor_id" placeholder="professor ID" />
              <input name="section_code" placeholder="001" />
              <input name="capacity" defaultValue="30" />
              <select name="room_selection_mode" defaultValue="professor_choice"><option>admin_fixed</option><option>professor_choice</option><option>system_recommended</option></select>
            </DemoForm>
            <DemoForm title="Professor" onSubmit={onForm((data) => withRequest("Create professor", () => adminRequest("/api/v1/admin/professors", Object.fromEntries(data.entries()))))}>
              <input name="email" placeholder="email" />
              <input name="full_name" placeholder="name" />
              <input name="department_name" placeholder="department" />
              <input name="password" defaultValue="prof12345" />
            </DemoForm>
            <DemoForm title="Room" onSubmit={onForm((data) => withRequest("Create room", () => adminRequest("/api/v1/admin/rooms", { building: data.get("building") || null, room_number: data.get("room_number"), capacity: Number(data.get("capacity")), room_type: data.get("room_type") || "lecture" })))}>
              <input name="building" placeholder="B" />
              <input name="room_number" placeholder="305" />
              <input name="capacity" defaultValue="40" />
              <input name="room_type" defaultValue="lecture" />
            </DemoForm>
            <DemoForm title="Room allocation" onSubmit={onForm((data) => withRequest("Allocate rooms", () => adminRequest(`/api/v1/admin/sections/${data.get("section_id")}/room-allocations`, { room_ids: csvNumbers(data.get("room_ids")), notes: data.get("notes") || null })))}>
              <input name="section_id" placeholder="section ID" />
              <input name="room_ids" placeholder="1, 2" />
              <input name="notes" placeholder="notes" />
            </DemoForm>
            <DemoForm title="Registration period" onSubmit={onForm((data) => withRequest("Create registration period", () => adminRequest("/api/v1/admin/registration-periods", { semester_id: Number(data.get("semester_id")), opens_at: new Date(String(data.get("opens_at"))).toISOString(), closes_at: new Date(String(data.get("closes_at"))).toISOString(), status: "open" })))}>
              <input name="semester_id" placeholder="semester ID" />
              <input name="opens_at" type="datetime-local" />
              <input name="closes_at" type="datetime-local" />
            </DemoForm>
            <DemoForm title="Scheduling run" onSubmit={onForm((data) => withRequest("Create scheduling run", () => adminRequest("/api/v1/admin/scheduling/suggestion-runs", { semester_id: Number(data.get("semester_id")), strategy: "balanced_heuristic" })))}>
              <input name="semester_id" placeholder="semester ID" />
            </DemoForm>
          </div>
        </section>

        <section className="demo-panel">
          <h2>Professor, student, and diagnostics</h2>
          <div className="demo-forms-grid">
            <DemoForm title="Room options" onSubmit={onForm((data) => withRequest("Room options", () => roleRequest("professor", `/api/v1/professor/sections/${data.get("section_id")}/room-options`)))}>
              <input name="section_id" placeholder="section ID" />
            </DemoForm>
            <DemoForm title="Choose room" onSubmit={onForm((data) => withRequest("Choose room", () => roleRequest("professor", `/api/v1/professor/sections/${data.get("section_id")}/room-preferences`, { room_id: Number(data.get("room_id")), preference_rank: 1 })))}>
              <input name="section_id" placeholder="section ID" />
              <input name="room_id" placeholder="room ID" />
            </DemoForm>
            <DemoForm title="Manual profile" onSubmit={onForm((data) => withRequest("Update manual profile", () => roleRequest("student", "/api/v1/student-profiles/me/manual", { department_id: Number(data.get("department_id")), major_id: Number(data.get("major_id")), academic_year: Number(data.get("academic_year")), completed_course_codes: csvStrings(data.get("completed_course_codes")) }, "PUT")))}>
              <input name="department_id" placeholder="department ID" />
              <input name="major_id" placeholder="major ID" />
              <input name="academic_year" placeholder="year" />
              <input name="completed_course_codes" placeholder="MSC1010, CSE2010" />
            </DemoForm>
            <DemoForm title="Eligibility" onSubmit={onForm((data) => withRequest("Eligibility", () => roleRequest("student", `/api/v1/sections/${data.get("section_id")}/eligibility`)))}>
              <input name="section_id" placeholder="section ID" />
            </DemoForm>
            <DemoForm title="Register" onSubmit={onForm((data) => withRequest("Register", () => roleRequest("student", "/api/v1/registrations", { section_id: Number(data.get("section_id")), idempotency_key: crypto.randomUUID() })))}>
              <input name="section_id" placeholder="section ID" />
            </DemoForm>
            <DemoForm title="Drop" onSubmit={onForm((data) => withRequest("Drop", () => roleRequest("student", `/api/v1/registrations/${data.get("enrollment_id")}`, undefined, "DELETE")))}>
              <input name="enrollment_id" placeholder="enrollment ID" />
            </DemoForm>
            <DemoForm title="Waitlist" onSubmit={onForm((data) => withRequest("Join waitlist", () => roleRequest("student", "/api/v1/waitlists", { section_id: Number(data.get("section_id")) })))}>
              <input name="section_id" placeholder="section ID" />
            </DemoForm>
            <DemoForm title="Section lookup" onSubmit={onForm(async (data) => {
              const section = await withRequest("Section detail", () => publicApi.section(Number(data.get("section_id"))));
              setSections([section]);
            })}>
              <input name="section_id" placeholder="section ID" />
            </DemoForm>
          </div>
          <div className="demo-pill-row">
            <button type="button" className="ghost-button" onClick={() => withRequest("My registrations", () => roleRequest("student", "/api/v1/registrations/me"))}>My registrations</button>
            <button type="button" className="ghost-button" onClick={() => withRequest("My waitlists", () => roleRequest("student", "/api/v1/waitlists/me"))}>My waitlists</button>
            <button type="button" className="ghost-button" onClick={() => withRequest("Notifications", () => roleRequest("student", "/api/v1/notifications/me"))}>Notifications</button>
            <button type="button" className="ghost-button" onClick={() => withRequest("Health", () => request("/health"))}>Health</button>
            <button type="button" className="ghost-button" onClick={() => withRequest("Dependencies", () => request("/api/v1/health/dependencies"))}>Dependencies</button>
            <button type="button" className="ghost-button" onClick={() => withRequest("Audit logs", () => adminRequest("/api/v1/admin/audit-logs?limit=10&offset=0"))}>Audit logs</button>
          </div>
          <div className="demo-results">
            {sections.map((section) => <article className="demo-result-card" key={section.id}>{section.course_code} · {section.section_code}</article>)}
          </div>
        </section>
      </section>

      <section className="demo-grid">
        <section className="demo-panel">
          <div className="demo-panel-head">
            <h2>WebSocket</h2>
            <Badge tone={socketRef.current ? "cool" : "muted"}>{socketStatus}</Badge>
          </div>
          <DemoForm title="Connect to section" onSubmit={onForm(async (data) => {
            socketRef.current?.close();
            const sectionId = data.get("section_id");
            const socket = new WebSocket(`${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/sections/${sectionId}`);
            socket.onopen = () => setSocketStatus("Connected");
            socket.onmessage = (event) => logEvent("WebSocket message", JSON.parse(event.data));
            socket.onclose = () => setSocketStatus("Disconnected");
            socketRef.current = socket;
          })}>
            <input name="section_id" placeholder="section ID" />
          </DemoForm>
          <button type="button" className="ghost-button" onClick={() => socketRef.current?.close()}>Disconnect</button>
        </section>
        <section className="demo-panel">
          <div className="demo-panel-head">
            <h2>Event log</h2>
            <button type="button" className="ghost-button" onClick={() => setLog("")}>Clear</button>
          </div>
          <pre className="demo-log">{log}</pre>
        </section>
      </section>
    </main>
  );
}

function DemoForm({
  title,
  children,
  onSubmit,
}: {
  title: string;
  children: ReactNode;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <form className="demo-card demo-stack" onSubmit={onSubmit}>
      <h3>{title}</h3>
      {children}
      <button>Submit</button>
    </form>
  );
}

function adminRequest(path: string, body?: unknown, method = body === undefined ? "GET" : "POST") {
  return request(path, { method, body, token: tokenFor("admin") });
}

function roleRequest(
  role: Role,
  path: string,
  body?: unknown,
  method = body === undefined ? "GET" : "POST",
) {
  return request(path, { method, body, token: tokenFor(role) });
}
