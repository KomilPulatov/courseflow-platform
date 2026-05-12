const state = {
  token: localStorage.getItem("crspAdminToken") ?? "",
  professorToken: localStorage.getItem("crspProfessorToken") ?? "",
  studentToken: localStorage.getItem("crspStudentToken") ?? "",
};

const authState = document.querySelector("#authState");
const professorAuthState = document.querySelector("#professorAuthState");
const studentAuthState = document.querySelector("#studentAuthState");
const eventLog = document.querySelector("#eventLog");
const catalogResults = document.querySelector("#catalogResults");
const sectionResults = document.querySelector("#sectionResults");

function setAuthState() {
  authState.textContent = state.token ? "Admin token loaded" : "Signed out";
  authState.className = `badge ${state.token ? "warm" : "muted"}`;
  professorAuthState.textContent = state.professorToken ? "Professor token loaded" : "Signed out";
  professorAuthState.className = `badge ${state.professorToken ? "warm" : "muted"}`;
  studentAuthState.textContent = state.studentToken ? "Student token loaded" : "Signed out";
  studentAuthState.className = `badge ${state.studentToken ? "warm" : "muted"}`;
}

function tokenForRole(role) {
  if (role === "professor") return state.professorToken;
  if (role === "student") return state.studentToken;
  return state.token;
}

function log(title, payload) {
  const time = new Date().toLocaleTimeString();
  const block = `[${time}] ${title}\n${typeof payload === "string" ? payload : JSON.stringify(payload, null, 2)}\n\n`;
  eventLog.textContent = block + eventLog.textContent;
}

async function request(path, options = {}) {
  const { role, ...fetchOptions } = options;
  const headers = new Headers(options.headers ?? {});
  const token = tokenForRole(role);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...fetchOptions, headers });
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof data === "string" ? data : data.detail ?? JSON.stringify(data);
    throw new Error(message);
  }

  return data;
}

function renderCourseCard(course) {
  return `
    <article class="result-card">
      <h3>${course.code} · ${course.title}</h3>
      <p>Department: ${course.department_code ?? "N/A"} · Credits: ${course.credits}</p>
      <p>Offerings: ${course.active_offering_count} · Sections: ${course.active_section_count}</p>
      <button data-course-id="${course.id}" class="view-course-button">View Course Detail</button>
    </article>
  `;
}

function renderJsonCard(title, data) {
  return `
    <article class="result-card">
      <h3>${title}</h3>
      <pre>${JSON.stringify(data, null, 2)}</pre>
    </article>
  `;
}

async function loadCatalog(params = {}) {
  const searchParams = new URLSearchParams();
  if (params.search) searchParams.set("search", params.search);
  if (params.semesterId) searchParams.set("semester_id", params.semesterId);

  const query = searchParams.toString();
  const courses = await request(`/api/v1/courses${query ? `?${query}` : ""}`);
  catalogResults.innerHTML = courses.length
    ? courses.map(renderCourseCard).join("")
    : `<article class="result-card"><p>No courses matched the current filter.</p></article>`;

  document.querySelectorAll(".view-course-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const courseId = button.dataset.courseId;
      try {
        const detail = await request(`/api/v1/courses/${courseId}`);
        const sections = await request(`/api/v1/courses/${courseId}/sections`);
        catalogResults.innerHTML = [
          renderJsonCard("Course Detail", detail),
          renderJsonCard("Sections", sections),
        ].join("");
        log("Loaded course detail", { courseId, detail, sections });
      } catch (error) {
        log("Course detail failed", error.message);
      }
    });
  });
}

function readCsvIds(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .map((item) => Number(item));
}

function toIsoFromLocal(value) {
  return value ? new Date(value).toISOString() : "";
}

function bindJsonForm(selector, { path, buildPayload, onSuccess }) {
  const form = document.querySelector(selector);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
    try {
      const payload = buildPayload(formData);
      const result = await request(path(payload), {
        method: "POST",
        body: JSON.stringify(payload),
      });
      log(`POST ${path(payload)}`, result);
      if (onSuccess) {
        await onSuccess(result);
      }
      form.reset();
    } catch (error) {
      log(`POST ${path({})} failed`, error.message);
    }
  });
}

document.querySelector("#loginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  try {
    const result = await request("/api/v1/auth/admin/login", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });
    state.token = result.access_token;
    localStorage.setItem("crspAdminToken", state.token);
    setAuthState();
    log("Admin login", result);
  } catch (error) {
    log("Admin login failed", error.message);
  }
});

document.querySelector("#logoutButton").addEventListener("click", () => {
  state.token = "";
  state.professorToken = "";
  state.studentToken = "";
  localStorage.removeItem("crspAdminToken");
  localStorage.removeItem("crspProfessorToken");
  localStorage.removeItem("crspStudentToken");
  setAuthState();
  log("Tokens cleared", "Tokens removed from browser storage.");
});

document.querySelector("#clearLogButton").addEventListener("click", () => {
  eventLog.textContent = "";
});

document.querySelector("#refreshCatalogButton").addEventListener("click", () => {
  loadCatalog().catch((error) => log("Catalog refresh failed", error.message));
});

document.querySelector("#catalogSearchForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  try {
    await loadCatalog({
      search: String(formData.get("search") ?? "").trim(),
      semesterId: String(formData.get("semesterId") ?? "").trim(),
    });
    log("Catalog search", Object.fromEntries(formData.entries()));
  } catch (error) {
    log("Catalog search failed", error.message);
  }
});

bindJsonForm("#departmentForm", {
  path: () => "/api/v1/admin/departments",
  buildPayload: (formData) => ({
    code: formData.get("code"),
    name: formData.get("name"),
  }),
  onSuccess: loadCatalog,
});

bindJsonForm("#majorForm", {
  path: () => "/api/v1/admin/majors",
  buildPayload: (formData) => ({
    department_id: Number(formData.get("departmentId")),
    code: formData.get("code"),
    name: formData.get("name"),
  }),
});

bindJsonForm("#semesterForm", {
  path: () => "/api/v1/admin/semesters",
  buildPayload: (formData) => ({
    name: formData.get("name"),
    status: formData.get("status"),
  }),
});

bindJsonForm("#courseForm", {
  path: () => "/api/v1/admin/courses",
  buildPayload: (formData) => ({
    department_id: formData.get("departmentId")
      ? Number(formData.get("departmentId"))
      : null,
    code: formData.get("code"),
    title: formData.get("title"),
    credits: Number(formData.get("credits")),
    description: formData.get("description") || null,
    course_type: formData.get("courseType") || null,
    is_repeatable: false,
  }),
  onSuccess: loadCatalog,
});

document.querySelector("#prerequisiteForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const courseId = Number(formData.get("courseId"));
  try {
    const payload = {
      prerequisite_course_ids: readCsvIds(String(formData.get("prereqIds") ?? "")),
      rule_group: "all",
    };
    const result = await request(`/api/v1/admin/courses/${courseId}/prerequisites`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    log("Updated prerequisites", result);
  } catch (error) {
    log("Prerequisite update failed", error.message);
  }
});

document.querySelector("#eligibilityRuleForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const courseId = Number(formData.get("courseId"));
  try {
    const payload = {
      min_academic_year: formData.get("minAcademicYear")
        ? Number(formData.get("minAcademicYear"))
        : null,
      min_gpa: formData.get("minGpa") ? Number(formData.get("minGpa")) : null,
      allowed_department_ids: readCsvIds(String(formData.get("departmentIds") ?? "")) || null,
      allowed_major_ids: readCsvIds(String(formData.get("majorIds") ?? "")) || null,
      rule_metadata: null,
    };
    const result = await request(`/api/v1/admin/courses/${courseId}/eligibility-rules`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    log("Created eligibility rule", result);
  } catch (error) {
    log("Eligibility rule failed", error.message);
  }
});

bindJsonForm("#offeringForm", {
  path: () => "/api/v1/admin/course-offerings",
  buildPayload: (formData) => ({
    course_id: Number(formData.get("courseId")),
    semester_id: Number(formData.get("semesterId")),
    status: formData.get("status"),
  }),
});

bindJsonForm("#sectionForm", {
  path: () => "/api/v1/admin/sections",
  buildPayload: (formData) => ({
    course_offering_id: Number(formData.get("courseOfferingId")),
    professor_id: formData.get("professorId")
      ? Number(formData.get("professorId"))
      : null,
    section_code: formData.get("sectionCode"),
    capacity: Number(formData.get("capacity")),
    room_selection_mode: formData.get("roomSelectionMode"),
    status: formData.get("status"),
  }),
});

bindJsonForm("#professorForm", {
  path: () => "/api/v1/admin/professors",
  buildPayload: (formData) => ({
    email: formData.get("email"),
    full_name: formData.get("fullName"),
    department_name: formData.get("departmentName") || null,
    password: formData.get("password"),
  }),
});

bindJsonForm("#roomForm", {
  path: () => "/api/v1/admin/rooms",
  buildPayload: (formData) => ({
    building: formData.get("building") || null,
    room_number: formData.get("roomNumber"),
    capacity: Number(formData.get("capacity")),
    room_type: formData.get("roomType") || "lecture",
    is_active: true,
  }),
});

document.querySelector("#roomAllocationForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const sectionId = Number(formData.get("sectionId"));
  try {
    const result = await request(`/api/v1/admin/sections/${sectionId}/room-allocations`, {
      method: "POST",
      body: JSON.stringify({
        room_ids: readCsvIds(String(formData.get("roomIds") ?? "")),
        notes: formData.get("notes") || null,
      }),
    });
    log("Allocated rooms", result);
  } catch (error) {
    log("Room allocation failed", error.message);
  }
});

bindJsonForm("#periodForm", {
  path: () => "/api/v1/admin/registration-periods",
  buildPayload: (formData) => ({
    semester_id: Number(formData.get("semesterId")),
    opens_at: toIsoFromLocal(String(formData.get("opensAt") ?? "")),
    closes_at: toIsoFromLocal(String(formData.get("closesAt") ?? "")),
    status: formData.get("status"),
  }),
});

bindJsonForm("#schedulingForm", {
  path: () => "/api/v1/admin/scheduling/suggestion-runs",
  buildPayload: (formData) => ({
    semester_id: Number(formData.get("semesterId")),
    strategy: formData.get("strategy"),
  }),
});

document.querySelector("#approveSchedulingForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const runId = Number(formData.get("runId"));
  try {
    const result = await request(`/api/v1/admin/scheduling/suggestion-runs/${runId}/approve`, {
      method: "POST",
    });
    log("Approved scheduling run", result);
  } catch (error) {
    log("Approve scheduling run failed", error.message);
  }
});

document.querySelector("#professorLoginForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  try {
    const result = await request("/api/v1/auth/professor/login", {
      method: "POST",
      body: JSON.stringify({
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });
    state.professorToken = result.access_token;
    localStorage.setItem("crspProfessorToken", state.professorToken);
    setAuthState();
    log("Professor login", result);
  } catch (error) {
    log("Professor login failed", error.message);
  }
});

document.querySelector("#roomOptionsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const sectionId = Number(new FormData(event.currentTarget).get("sectionId"));
  try {
    const result = await request(`/api/v1/professor/sections/${sectionId}/room-options`, {
      role: "professor",
    });
    log("Loaded room options", result);
  } catch (error) {
    log("Room options failed", error.message);
  }
});

document.querySelector("#roomPreferenceForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const sectionId = Number(formData.get("sectionId"));
  try {
    const result = await request(`/api/v1/professor/sections/${sectionId}/room-preferences`, {
      method: "POST",
      role: "professor",
      body: JSON.stringify({
        room_id: Number(formData.get("roomId")),
        preference_rank: Number(formData.get("preferenceRank")),
      }),
    });
    log("Saved room preference", result);
  } catch (error) {
    log("Room preference failed", error.message);
  }
});

document.querySelector("#manualStudentForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  try {
    const result = await request("/api/v1/auth/student/manual-start", {
      method: "POST",
      body: JSON.stringify({
        student_number: formData.get("studentNumber"),
        full_name: formData.get("fullName"),
        email: formData.get("email"),
        password: formData.get("password"),
      }),
    });
    state.studentToken = result.access_token;
    localStorage.setItem("crspStudentToken", state.studentToken);
    setAuthState();
    log("Manual student created", result);
  } catch (error) {
    log("Manual student failed", error.message);
  }
});

document.querySelector("#registerForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  try {
    const result = await request("/api/v1/registrations", {
      method: "POST",
      role: "student",
      body: JSON.stringify({
        section_id: Number(formData.get("sectionId")),
        idempotency_key: formData.get("idempotencyKey"),
      }),
    });
    log("Registration result", result);
  } catch (error) {
    log("Registration failed", error.message);
  }
});

document.querySelector("#waitlistForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const sectionId = Number(new FormData(event.currentTarget).get("sectionId"));
  try {
    const result = await request("/api/v1/waitlists", {
      method: "POST",
      role: "student",
      body: JSON.stringify({ section_id: sectionId }),
    });
    log("Waitlist result", result);
  } catch (error) {
    log("Waitlist failed", error.message);
  }
});

document.querySelector("#sectionLookupForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const sectionId = Number(formData.get("sectionId"));
  try {
    const availability = await request(`/api/v1/sections/${sectionId}/availability`);
    sectionResults.innerHTML = renderJsonCard("Availability", availability);
    log("Loaded section availability", availability);
  } catch (error) {
    log("Section availability failed", error.message);
  }
});

document.querySelector("#eligibilityForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.currentTarget);
  const sectionId = Number(formData.get("sectionId"));
  const studentId = Number(formData.get("studentId"));
  try {
    const eligibility = await request(`/api/v1/sections/${sectionId}/eligibility`, {
      headers: { "X-Student-Id": String(studentId) },
    });
    sectionResults.innerHTML = renderJsonCard("Eligibility", eligibility);
    log("Loaded eligibility preview", eligibility);
  } catch (error) {
    log("Eligibility preview failed", error.message);
  }
});

setAuthState();
loadCatalog().catch((error) => log("Initial catalog load failed", error.message));
