const appRoot = document.querySelector("#app");
const drawerRoot = document.querySelector("#drawer-root");
const toastRoot = document.querySelector("#toast-root");

const state = {
  token: localStorage.getItem("crspAdminToken") ?? "",
  returnTo: window.location.pathname.startsWith("/admin") ? window.location.pathname : "/admin",
};

const navGroups = [
  {
    title: "Overview",
    items: [
      { label: "Dashboard", path: "/admin" },
      { label: "Observability", path: "/admin/observability" },
      { label: "Audit logs", path: "/admin/audit-logs" },
    ],
  },
  {
    title: "Academic setup",
    items: [
      { label: "Semesters", path: "/admin/semesters" },
      { label: "Departments", path: "/admin/departments" },
      { label: "Majors", path: "/admin/majors" },
      { label: "Courses", path: "/admin/courses" },
      { label: "Offerings", path: "/admin/offerings" },
    ],
  },
  {
    title: "Delivery",
    items: [
      { label: "Professors", path: "/admin/professors" },
      { label: "Rooms", path: "/admin/rooms" },
      { label: "Sections", path: "/admin/sections" },
      { label: "Registration periods", path: "/admin/registration-periods" },
      { label: "Scheduling", path: "/admin/scheduling" },
    ],
  },
];

const api = {
  login: (body) => request("/api/v1/auth/admin/login", { method: "POST", body }),
  departments: () => request("/api/v1/admin/departments"),
  createDepartment: (body) => request("/api/v1/admin/departments", { method: "POST", body }),
  majors: (departmentId) =>
    request(`/api/v1/admin/majors${departmentId ? `?department_id=${departmentId}` : ""}`),
  createMajor: (body) => request("/api/v1/admin/majors", { method: "POST", body }),
  semesters: () => request("/api/v1/admin/semesters"),
  createSemester: (body) => request("/api/v1/admin/semesters", { method: "POST", body }),
  courses: () => request("/api/v1/admin/courses"),
  createCourse: (body) => request("/api/v1/admin/courses", { method: "POST", body }),
  course: (courseId) => request(`/api/v1/courses/${courseId}`),
  replacePrerequisites: (courseId, body) =>
    request(`/api/v1/admin/courses/${courseId}/prerequisites`, { method: "PUT", body }),
  eligibilityRules: (courseId) =>
    request(`/api/v1/admin/courses/${courseId}/eligibility-rules`),
  createEligibilityRule: (courseId, body) =>
    request(`/api/v1/admin/courses/${courseId}/eligibility-rules`, {
      method: "POST",
      body,
    }),
  professors: () => request("/api/v1/admin/professors"),
  createProfessor: (body) => request("/api/v1/admin/professors", { method: "POST", body }),
  rooms: () => request("/api/v1/admin/rooms"),
  createRoom: (body) => request("/api/v1/admin/rooms", { method: "POST", body }),
  offerings: (semesterId) =>
    request(
      `/api/v1/admin/course-offerings${semesterId ? `?semester_id=${semesterId}` : ""}`,
    ),
  createOffering: (body) => request("/api/v1/admin/course-offerings", { method: "POST", body }),
  sections: ({ courseId, semesterId } = {}) => {
    const params = new URLSearchParams();
    if (courseId) params.set("course_id", courseId);
    if (semesterId) params.set("semester_id", semesterId);
    return request(`/api/v1/admin/sections${params.toString() ? `?${params}` : ""}`);
  },
  createSection: (body) => request("/api/v1/admin/sections", { method: "POST", body }),
  section: (sectionId) => request(`/api/v1/sections/${sectionId}`),
  sectionAvailability: (sectionId) => request(`/api/v1/sections/${sectionId}/availability`),
  roomAllocations: (sectionId) => request(`/api/v1/admin/sections/${sectionId}/room-allocations`),
  allocateRooms: (sectionId, body) =>
    request(`/api/v1/admin/sections/${sectionId}/room-allocations`, {
      method: "POST",
      body,
    }),
  registrationPeriods: (semesterId) =>
    request(
      `/api/v1/admin/registration-periods${semesterId ? `?semester_id=${semesterId}` : ""}`,
    ),
  createRegistrationPeriod: (body) =>
    request("/api/v1/admin/registration-periods", { method: "POST", body }),
  schedulingRuns: () => request("/api/v1/admin/scheduling/suggestion-runs"),
  createSchedulingRun: (body) =>
    request("/api/v1/admin/scheduling/suggestion-runs", { method: "POST", body }),
  schedulingRun: (runId) => request(`/api/v1/admin/scheduling/suggestion-runs/${runId}`),
  approveSchedulingRun: (runId) =>
    request(`/api/v1/admin/scheduling/suggestion-runs/${runId}/approve`, {
      method: "POST",
    }),
  auditLogs: () => request("/api/v1/admin/audit-logs"),
  health: () => request("/health"),
  dependencyHealth: () => request("/api/v1/health/dependencies"),
  metrics: () => request("/metrics"),
};

const routes = [
  { pattern: /^\/admin\/?$/, handler: renderDashboard },
  { pattern: /^\/admin\/semesters\/?$/, handler: renderSemesters },
  { pattern: /^\/admin\/departments\/?$/, handler: renderDepartments },
  { pattern: /^\/admin\/majors\/?$/, handler: renderMajors },
  { pattern: /^\/admin\/courses\/?$/, handler: renderCourses },
  { pattern: /^\/admin\/courses\/new\/?$/, handler: renderNewCourse },
  {
    pattern: /^\/admin\/courses\/(?<courseId>\d+)\/prerequisites\/?$/,
    handler: renderCoursePrerequisites,
  },
  {
    pattern: /^\/admin\/courses\/(?<courseId>\d+)\/eligibility-rules\/?$/,
    handler: renderEligibilityRules,
  },
  { pattern: /^\/admin\/courses\/(?<courseId>\d+)\/?$/, handler: renderCourseDetail },
  { pattern: /^\/admin\/professors\/?$/, handler: renderProfessors },
  { pattern: /^\/admin\/rooms\/?$/, handler: renderRooms },
  { pattern: /^\/admin\/offerings\/?$/, handler: renderOfferings },
  { pattern: /^\/admin\/sections\/?$/, handler: renderSections },
  { pattern: /^\/admin\/sections\/(?<sectionId>\d+)\/rooms\/?$/, handler: renderSectionRooms },
  { pattern: /^\/admin\/sections\/(?<sectionId>\d+)\/?$/, handler: renderSectionDetail },
  { pattern: /^\/admin\/registration-periods\/?$/, handler: renderRegistrationPeriods },
  { pattern: /^\/admin\/scheduling\/?$/, handler: renderScheduling },
  { pattern: /^\/admin\/scheduling\/(?<runId>\d+)\/?$/, handler: renderSchedulingRun },
  { pattern: /^\/admin\/audit-logs\/?$/, handler: renderAuditLogs },
  { pattern: /^\/admin\/observability\/?$/, handler: renderObservability },
];

window.addEventListener("popstate", renderCurrentRoute);

document.addEventListener("click", (event) => {
  const link = event.target.closest("[data-link]");
  if (link) {
    event.preventDefault();
    navigate(link.dataset.link);
  }

  if (event.target.matches("[data-close-drawer]") || event.target.closest("[data-close-drawer]")) {
    closeDrawer();
  }
});

renderCurrentRoute();

async function request(path, options = {}) {
  const headers = new Headers(options.headers ?? {});
  const body = options.body ? JSON.stringify(options.body) : undefined;
  if (state.token && !path.includes("/auth/admin/login")) {
    headers.set("Authorization", `Bearer ${state.token}`);
  }
  if (body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers,
    body,
  });
  const contentType = response.headers.get("content-type") ?? "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    if ((response.status === 401 || response.status === 403) && state.token) {
      clearSession();
      state.returnTo = window.location.pathname;
      renderLogin();
    }
    throw new Error(extractErrorMessage(data));
  }
  return data;
}

function extractErrorMessage(data) {
  if (typeof data === "string") return data || "Request failed.";
  return data.detail ?? data.message ?? JSON.stringify(data);
}

function navigate(path) {
  if (window.location.pathname !== path) {
    history.pushState({}, "", path);
  }
  renderCurrentRoute();
}

function clearSession() {
  state.token = "";
  localStorage.removeItem("crspAdminToken");
}

function renderLogin() {
  closeDrawer();
  appRoot.innerHTML = `
    <main class="login-shell">
      <section class="login-card">
        <div class="login-story">
          <div>
            <div class="brand-mark">CR</div>
            <p class="eyebrow">CRSP Administration</p>
            <h1>Shape the academic term with confidence.</h1>
            <p>
              Manage catalog structure, teaching capacity, scheduling, and system health from one
              calm workspace built for university operations.
            </p>
          </div>
          <div class="login-highlights">
            <article class="login-highlight">
              <strong>Academic setup</strong>
              <p class="muted">Semesters, courses, departments, majors, and offerings.</p>
            </article>
            <article class="login-highlight">
              <strong>Delivery control</strong>
              <p class="muted">Sections, rooms, registration periods, and scheduling runs.</p>
            </article>
          </div>
        </div>
        <div class="login-form-wrap">
          <div>
            <p class="eyebrow">Administrator login</p>
            <h2>Welcome back</h2>
          </div>
          <form id="admin-login-form" class="login-form">
            <label>
              <span>Email</span>
              <input name="email" type="email" value="admin@crsp.local" required />
            </label>
            <label>
              <span>Password</span>
              <input name="password" type="password" value="admin12345" required />
            </label>
            <button class="button" type="submit">Enter admin console</button>
          </form>
          <p class="muted">Seeded demo credentials are prefilled for local development.</p>
        </div>
      </section>
    </main>
  `;

  document.querySelector("#admin-login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    try {
      const result = await api.login({
        email: formData.get("email"),
        password: formData.get("password"),
      });
      state.token = result.access_token;
      localStorage.setItem("crspAdminToken", state.token);
      showToast("Signed in", "Admin session is ready.");
      navigate(state.returnTo || "/admin");
    } catch (error) {
      showToast("Login failed", error.message, "error");
    }
  });
}

async function renderCurrentRoute() {
  if (!state.token) {
    state.returnTo = window.location.pathname;
    renderLogin();
    return;
  }

  const route = matchRoute(window.location.pathname);
  if (!route) {
    renderNotFound();
    return;
  }

  renderLoadingShell();
  try {
    const page = await route.handler(route.params);
    renderShell(page);
    page.afterRender?.();
  } catch (error) {
    if (!state.token) {
      return;
    }
    renderShell({
      title: "Something went wrong",
      eyebrow: "Admin console",
      description: "The page could not be loaded.",
      breadcrumbs: ["Admin", "Error"],
      content: renderErrorState(error.message),
    });
  }
}

function matchRoute(path) {
  for (const route of routes) {
    const match = path.match(route.pattern);
    if (match) {
      return { handler: route.handler, params: match.groups ?? {} };
    }
  }
  return null;
}

function renderLoadingShell() {
  renderShell({
    title: "Loading",
    eyebrow: "CRSP Admin",
    description: "Preparing the next workspace.",
    breadcrumbs: ["Admin"],
    content: `<div class="loading">Loading academic workspace…</div>`,
  });
}

function renderNotFound() {
  renderShell({
    title: "Page not found",
    eyebrow: "Admin console",
    description: "That route is not part of the admin experience.",
    breadcrumbs: ["Admin", "Not found"],
    content: `
      <section class="empty-state">
        <h3>We could not find that page.</h3>
        <p>Return to the dashboard and continue from a known admin workflow.</p>
        <button class="button" data-link="/admin">Back to dashboard</button>
      </section>
    `,
  });
}

function renderShell(page) {
  const activePath = window.location.pathname;
  appRoot.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="brand">
          <div class="brand-mark">CR</div>
          <h1>CRSP Admin</h1>
          <p>Courseflow operations</p>
        </div>
        <div class="nav-scroll">
          ${navGroups
            .map(
              (group) => `
                <nav class="nav-group">
                  <p class="nav-group-title">${escapeHtml(group.title)}</p>
                  ${group.items
                    .map(
                      (item) => `
                        <a
                          class="nav-link ${isActiveNav(activePath, item.path) ? "active" : ""}"
                          href="${item.path}"
                          data-link="${item.path}"
                        >
                          <span>${escapeHtml(item.label)}</span>
                        </a>
                      `,
                    )
                    .join("")}
                </nav>
              `,
            )
            .join("")}
        </div>
        <div class="sidebar-footer">
          <div class="profile-card">
            <strong>Administrator</strong>
            <span>Authenticated session</span>
            <button id="logout-button" class="subtle-button" type="button">Sign out</button>
          </div>
        </div>
      </aside>
      <main class="content">
        <header class="topbar">
          <div class="breadcrumbs">
            ${(page.breadcrumbs ?? ["Admin"]).map((item) => `<span>${escapeHtml(item)}</span>`).join("")}
          </div>
          <div class="topbar-actions">
            ${page.topbarActions ?? ""}
          </div>
        </header>
        <section class="page-hero">
          <div>
            <p class="eyebrow">${escapeHtml(page.eyebrow ?? "CRSP Admin")}</p>
            <h2>${escapeHtml(page.title)}</h2>
            ${page.description ? `<p>${escapeHtml(page.description)}</p>` : ""}
          </div>
          <div class="hero-actions">${page.actions ?? ""}</div>
        </section>
        ${page.content}
      </main>
    </div>
  `;

  document.querySelector("#logout-button")?.addEventListener("click", () => {
    clearSession();
    state.returnTo = "/admin";
    showToast("Signed out", "Admin session cleared.");
    renderLogin();
  });
}

function isActiveNav(activePath, itemPath) {
  if (itemPath === "/admin") return activePath === "/admin";
  return activePath === itemPath || activePath.startsWith(`${itemPath}/`);
}

async function renderDashboard() {
  const [
    semesters,
    departments,
    majors,
    courses,
    professors,
    rooms,
    offerings,
    sections,
    periods,
    auditLogs,
    dependencyHealth,
  ] = await Promise.all([
    api.semesters(),
    api.departments(),
    api.majors(),
    api.courses(),
    api.professors(),
    api.rooms(),
    api.offerings(),
    api.sections(),
    api.registrationPeriods(),
    api.auditLogs(),
    api.dependencyHealth(),
  ]);

  const activeSemesters = semesters.filter((item) => item.status === "active").length;
  const openPeriods = periods.filter((item) => item.status === "open").length;
  const openSections = sections.filter((item) => item.status === "open").length;
  const totalSeats = sections.reduce((sum, item) => sum + item.capacity, 0);

  return {
    title: "Academic operations",
    eyebrow: "Dashboard",
    description:
      "A single view of catalog readiness, teaching capacity, and platform health for the current term.",
    breadcrumbs: ["Admin", "Dashboard"],
    actions: `
      <button class="button" data-link="/admin/courses/new">Create course</button>
      <button class="ghost-button" data-link="/admin/scheduling">Run scheduling</button>
    `,
    content: `
      <section class="grid four">
        ${metricCard("Active semesters", activeSemesters, `${semesters.length} total semesters`)}
        ${metricCard("Courses", courses.length, `${offerings.length} offerings configured`)}
        ${metricCard("Open sections", openSections, `${totalSeats} total seats planned`)}
        ${metricCard("Registration windows", openPeriods, `${periods.length} configured periods`)}
      </section>
      <section class="split" style="margin-top: 18px;">
        <article class="hero-card">
          <div>
            <p class="eyebrow">Quick actions</p>
            <h3>Shape the next academic cycle</h3>
          </div>
          <div class="quick-actions">
            <button class="ghost-button" data-link="/admin/semesters">New semester</button>
            <button class="ghost-button" data-link="/admin/departments">Departments</button>
            <button class="ghost-button" data-link="/admin/offerings">Offerings</button>
            <button class="ghost-button" data-link="/admin/sections">Sections</button>
            <button class="ghost-button" data-link="/admin/registration-periods">Registration</button>
          </div>
          <div class="grid three">
            ${miniStat("Departments", departments.length)}
            ${miniStat("Majors", majors.length)}
            ${miniStat("Professors", professors.length)}
          </div>
        </article>
        <article class="panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">System health</p>
              <h3>${escapeHtml(dependencyHealth.status)}</h3>
            </div>
            ${statusBadge(dependencyHealth.status)}
          </div>
          <div class="timeline">
            ${Object.entries(dependencyHealth.checks)
              .map(
                ([name, value]) => `
                  <div class="timeline-item">
                    <strong>${escapeHtml(name)}</strong>
                    <span>${escapeHtml(String(value))}</span>
                  </div>
                `,
              )
              .join("")}
          </div>
        </article>
      </section>
      <section class="grid two" style="margin-top: 18px;">
        <article class="panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Recent activity</p>
              <h3>Audit trail</h3>
            </div>
            <button class="subtle-button" data-link="/admin/audit-logs">View all</button>
          </div>
          <div class="timeline">
            ${
              auditLogs.length
                ? auditLogs
                    .slice(0, 5)
                    .map(
                      (log) => `
                        <div class="timeline-item">
                          <strong>${escapeHtml(humanizeEvent(log.event_type))}</strong>
                          <span>${escapeHtml(log.entity_type)} #${log.entity_id ?? "—"} · ${formatDateTime(
                            log.created_at,
                          )}</span>
                        </div>
                      `,
                    )
                    .join("")
                : `<p class="muted">No audit activity yet.</p>`
            }
          </div>
        </article>
        <article class="panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Inventory</p>
              <h3>Teaching resources</h3>
            </div>
          </div>
          <div class="detail-grid">
            ${detailItem("Rooms", rooms.length)}
            ${detailItem("Professors", professors.length)}
            ${detailItem("Offerings", offerings.length)}
            ${detailItem("Sections", sections.length)}
          </div>
        </article>
      </section>
    `,
  };
}

async function renderSemesters() {
  const semesters = await api.semesters();
  return {
    title: "Semesters",
    eyebrow: "Academic setup",
    description: "Create and review the academic terms that anchor the rest of the catalog.",
    breadcrumbs: ["Admin", "Semesters"],
    actions: `<button id="create-semester" class="button">New semester</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search semesters",
      columns: ["Name", "Status", "ID"],
      rows: semesters.map((semester) => [
        semester.name,
        statusBadge(semester.status),
        `#${semester.id}`,
      ]),
      emptyTitle: "No semesters yet",
      emptyMessage: "Create the first semester to begin academic setup.",
    }),
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-semester").addEventListener("click", () => {
        openSemesterDrawer();
      });
    },
  };
}

async function renderDepartments() {
  const departments = await api.departments();
  return {
    title: "Departments",
    eyebrow: "Academic setup",
    description: "Organize the institution into the academic homes that courses and majors belong to.",
    breadcrumbs: ["Admin", "Departments"],
    actions: `<button id="create-department" class="button">New department</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search departments",
      columns: ["Code", "Name", "ID"],
      rows: departments.map((department) => [
        `<strong>${escapeHtml(department.code)}</strong>`,
        department.name,
        `#${department.id}`,
      ]),
      emptyTitle: "No departments yet",
      emptyMessage: "Create the first academic department.",
    }),
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-department").addEventListener("click", () => {
        openDepartmentDrawer();
      });
    },
  };
}

async function renderMajors() {
  const [majors, departments] = await Promise.all([api.majors(), api.departments()]);
  const departmentById = Object.fromEntries(departments.map((item) => [item.id, item]));
  return {
    title: "Majors",
    eyebrow: "Academic setup",
    description: "Maintain the programs students belong to and connect them to their departments.",
    breadcrumbs: ["Admin", "Majors"],
    actions: `<button id="create-major" class="button">New major</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search majors",
      columns: ["Code", "Name", "Department", "ID"],
      rows: majors.map((major) => [
        `<strong>${escapeHtml(major.code)}</strong>`,
        major.name,
        departmentById[major.department_id]?.name ?? `Department #${major.department_id}`,
        `#${major.id}`,
      ]),
      emptyTitle: "No majors yet",
      emptyMessage: "Create a department first, then add majors.",
    }),
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-major").addEventListener("click", () => {
        openMajorDrawer(departments);
      });
    },
  };
}

async function renderCourses() {
  const courses = await api.courses();
  return {
    title: "Courses",
    eyebrow: "Academic setup",
    description: "Manage the durable catalog before turning courses into semester offerings.",
    breadcrumbs: ["Admin", "Courses"],
    actions: `<button class="button" data-link="/admin/courses/new">New course</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search by course code or title",
      columns: ["Course", "Department", "Credits", "Offerings", "Sections"],
      rows: courses.map((course) => [
        `<a class="link" href="/admin/courses/${course.id}" data-link="/admin/courses/${course.id}">${escapeHtml(
          course.code,
        )} · ${escapeHtml(course.title)}</a>`,
        course.department_code ?? "—",
        String(course.credits),
        String(course.active_offering_count),
        String(course.active_section_count),
      ]),
      emptyTitle: "No courses yet",
      emptyMessage: "Create the first course to start building the catalog.",
    }),
    afterRender: bindSearch,
  };
}

async function renderNewCourse() {
  const departments = await api.departments();
  return {
    title: "Create course",
    eyebrow: "Courses",
    description: "Add a new course to the durable catalog before creating semester offerings.",
    breadcrumbs: ["Admin", "Courses", "New"],
    content: `
      <section class="panel">
        <form id="course-create-form" class="form-grid">
          <div class="form-grid two">
            ${selectField(
              "Department",
              "department_id",
              departments.map((item) => ({ value: item.id, label: `${item.code} · ${item.name}` })),
              "Optional",
            )}
            ${inputField("Course code", "code", "text", "CSE3010", true)}
          </div>
          <div class="form-grid two">
            ${inputField("Title", "title", "text", "Database Application Design", true)}
            ${inputField("Credits", "credits", "number", "3", true, `min="1" max="12"`)}
          </div>
          <div class="form-grid two">
            ${inputField("Course type", "course_type", "text", "core")}
            <label class="checkbox-row">
              <input name="is_repeatable" type="checkbox" />
              <span>Repeatable course</span>
            </label>
          </div>
          ${textareaField("Description", "description", "Course description")}
          <div>
            <button class="button" type="submit">Create course</button>
          </div>
        </form>
      </section>
    `,
    afterRender: () => {
      document.querySelector("#course-create-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        try {
          const result = await api.createCourse({
            department_id: optionalNumber(data.get("department_id")),
            code: data.get("code"),
            title: data.get("title"),
            credits: Number(data.get("credits")),
            description: optionalText(data.get("description")),
            course_type: optionalText(data.get("course_type")),
            is_repeatable: data.get("is_repeatable") === "on",
          });
          showToast("Course created", `${result.code} is ready for offerings.`);
          navigate(`/admin/courses/${result.id}`);
        } catch (error) {
          showToast("Could not create course", error.message, "error");
        }
      });
    },
  };
}

async function renderCourseDetail({ courseId }) {
  const [course, sections] = await Promise.all([api.course(courseId), api.sections({ courseId })]);
  return {
    title: `${course.code}`,
    eyebrow: "Course detail",
    description: course.title,
    breadcrumbs: ["Admin", "Courses", course.code],
    actions: `
      <button class="ghost-button" data-link="/admin/courses/${course.id}/prerequisites">Prerequisites</button>
      <button class="ghost-button" data-link="/admin/courses/${course.id}/eligibility-rules">Eligibility rules</button>
    `,
    content: `
      <section class="grid two">
        <article class="detail-card">
          <div class="section-head">
            <div>
              <p class="eyebrow">Overview</p>
              <h3>${escapeHtml(course.title)}</h3>
            </div>
            ${course.course_type ? statusBadge(course.course_type) : ""}
          </div>
          <div class="detail-grid">
            ${detailItem("Department", course.department_name ?? "Unassigned")}
            ${detailItem("Credits", course.credits)}
            ${detailItem("Repeatable", course.is_repeatable ? "Yes" : "No")}
            ${detailItem("Prerequisites", course.prerequisites.length)}
          </div>
          ${
            course.description
              ? `<p class="muted" style="margin-top: 16px;">${escapeHtml(course.description)}</p>`
              : ""
          }
        </article>
        <article class="panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Prerequisites</p>
              <h3>Dependency map</h3>
            </div>
          </div>
          ${
            course.prerequisites.length
              ? `<div class="timeline">${course.prerequisites
                  .map(
                    (item) => `
                      <div class="timeline-item">
                        <strong>${escapeHtml(item.code)}</strong>
                        <span>${escapeHtml(item.title)}</span>
                      </div>
                    `,
                  )
                  .join("")}</div>`
              : `<p class="muted">No prerequisites configured.</p>`
          }
        </article>
      </section>
      <section class="panel" style="margin-top: 18px;">
        <div class="section-head">
          <div>
            <p class="eyebrow">Sections</p>
            <h3>Current delivery</h3>
          </div>
        </div>
        ${
          sections.length
            ? renderTable({
                columns: ["Section", "Semester", "Capacity", "Remaining", "Status"],
                rows: sections.map((section) => [
                  `<a class="link" href="/admin/sections/${section.id}" data-link="/admin/sections/${section.id}">${escapeHtml(
                    section.section_code,
                  )}</a>`,
                  section.semester_name,
                  String(section.capacity),
                  String(section.remaining_seats),
                  statusBadge(section.status),
                ]),
              })
            : `<p class="muted">No sections created for this course yet.</p>`
        }
      </section>
    `,
  };
}

async function renderCoursePrerequisites({ courseId }) {
  const [course, courses] = await Promise.all([api.course(courseId), api.courses()]);
  const selectedIds = new Set(course.prerequisites.map((item) => item.id));
  const selectableCourses = courses.filter((item) => item.id !== Number(courseId));
  return {
    title: "Prerequisites",
    eyebrow: course.code,
    description: `Choose the courses students must complete before ${course.code}.`,
    breadcrumbs: ["Admin", "Courses", course.code, "Prerequisites"],
    content: `
      <section class="panel">
        <form id="prerequisite-form" class="form-grid">
          <div class="selection-grid">
            ${selectableCourses
              .map(
                (item) => `
                  <label class="selection-card">
                    <input
                      type="checkbox"
                      name="prerequisite_course_ids"
                      value="${item.id}"
                      ${selectedIds.has(item.id) ? "checked" : ""}
                    />
                    <span>
                      <strong>${escapeHtml(item.code)}</strong>
                      <span>${escapeHtml(item.title)}</span>
                    </span>
                  </label>
                `,
              )
              .join("")}
          </div>
          <div>
            <button class="button" type="submit">Save prerequisites</button>
          </div>
        </form>
      </section>
    `,
    afterRender: () => {
      document.querySelector("#prerequisite-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const ids = [...event.currentTarget.querySelectorAll('input[name="prerequisite_course_ids"]:checked')].map(
          (input) => Number(input.value),
        );
        try {
          await api.replacePrerequisites(courseId, {
            prerequisite_course_ids: ids,
            rule_group: "all",
          });
          showToast("Prerequisites saved", `${course.code} prerequisites updated.`);
          navigate(`/admin/courses/${course.id}`);
        } catch (error) {
          showToast("Could not save prerequisites", error.message, "error");
        }
      });
    },
  };
}

async function renderEligibilityRules({ courseId }) {
  const [course, rules, departments, majors] = await Promise.all([
    api.course(courseId),
    api.eligibilityRules(courseId),
    api.departments(),
    api.majors(),
  ]);
  return {
    title: "Eligibility rules",
    eyebrow: course.code,
    description: `Define who may register for ${course.code}.`,
    breadcrumbs: ["Admin", "Courses", course.code, "Eligibility rules"],
    actions: `<button id="create-rule" class="button">New rule</button>`,
    content: rules.length
      ? renderTablePage({
          searchPlaceholder: "Search rules",
          columns: ["Year", "Minimum GPA", "Departments", "Majors", "ID"],
          rows: rules.map((rule) => [
            rule.min_academic_year ?? "—",
            rule.min_gpa ?? "—",
            readableIds(rule.allowed_department_ids, departments),
            readableIds(rule.allowed_major_ids, majors),
            `#${rule.id}`,
          ]),
          emptyTitle: "",
          emptyMessage: "",
        })
      : `
        <section class="empty-state">
          <h3>No eligibility rules yet</h3>
          <p>Students are currently unconstrained by course-specific rules.</p>
          <button id="create-rule-empty" class="button">Create first rule</button>
        </section>
      `,
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-rule")?.addEventListener("click", () => {
        openEligibilityRuleDrawer(course, departments, majors);
      });
      document.querySelector("#create-rule-empty")?.addEventListener("click", () => {
        openEligibilityRuleDrawer(course, departments, majors);
      });
    },
  };
}

async function renderProfessors() {
  const professors = await api.professors();
  return {
    title: "Professors",
    eyebrow: "Delivery",
    description: "Create teaching accounts and keep instructional ownership visible.",
    breadcrumbs: ["Admin", "Professors"],
    actions: `<button id="create-professor" class="button">New professor</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search professors",
      columns: ["Name", "Email", "Department", "ID"],
      rows: professors.map((professor) => [
        `<strong>${escapeHtml(professor.full_name)}</strong>`,
        professor.email ?? "—",
        professor.department_name ?? "—",
        `#${professor.id}`,
      ]),
      emptyTitle: "No professors yet",
      emptyMessage: "Create the first professor account.",
    }),
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-professor").addEventListener("click", openProfessorDrawer);
    },
  };
}

async function renderRooms() {
  const rooms = await api.rooms();
  return {
    title: "Rooms",
    eyebrow: "Delivery",
    description: "Track the spaces available for teaching, scheduling, and professor choice.",
    breadcrumbs: ["Admin", "Rooms"],
    actions: `<button id="create-room" class="button">New room</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search rooms",
      columns: ["Room", "Capacity", "Type", "Status", "ID"],
      rows: rooms.map((room) => [
        `<strong>${escapeHtml(`${room.building ?? "—"} ${room.room_number}`)}</strong>`,
        String(room.capacity),
        room.room_type,
        room.is_active ? statusBadge("active") : statusBadge("inactive"),
        `#${room.id}`,
      ]),
      emptyTitle: "No rooms yet",
      emptyMessage: "Create rooms before allocating sections.",
    }),
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-room").addEventListener("click", openRoomDrawer);
    },
  };
}

async function renderOfferings() {
  const [offerings, courses, semesters] = await Promise.all([
    api.offerings(),
    api.courses(),
    api.semesters(),
  ]);
  return {
    title: "Offerings",
    eyebrow: "Academic setup",
    description: "Turn catalog courses into term-specific teaching plans.",
    breadcrumbs: ["Admin", "Offerings"],
    actions: `<button id="create-offering" class="button">New offering</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search offerings",
      columns: ["Course", "Semester", "Status", "Sections", "ID"],
      rows: offerings.map((offering) => [
        `${escapeHtml(offering.course_code)} · ${escapeHtml(offering.course_title)}`,
        offering.semester_name,
        statusBadge(offering.status),
        String(offering.section_count),
        `#${offering.id}`,
      ]),
      emptyTitle: "No offerings yet",
      emptyMessage: "Create a course offering for a semester.",
    }),
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-offering").addEventListener("click", () => {
        openOfferingDrawer(courses, semesters);
      });
    },
  };
}

async function renderSections() {
  const [sections, offerings, professors] = await Promise.all([
    api.sections(),
    api.offerings(),
    api.professors(),
  ]);
  return {
    title: "Sections",
    eyebrow: "Delivery",
    description: "Manage the actual class instances students register into.",
    breadcrumbs: ["Admin", "Sections"],
    actions: `<button id="create-section" class="button">New section</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search sections",
      columns: ["Section", "Course", "Semester", "Capacity", "Remaining", "Mode", "Status"],
      rows: sections.map((section) => [
        `<a class="link" href="/admin/sections/${section.id}" data-link="/admin/sections/${section.id}">${escapeHtml(
          section.section_code,
        )}</a>`,
        `${escapeHtml(section.course_code)} · ${escapeHtml(section.course_title)}`,
        section.semester_name,
        String(section.capacity),
        String(section.remaining_seats),
        section.room_selection_mode,
        statusBadge(section.status),
      ]),
      emptyTitle: "No sections yet",
      emptyMessage: "Create offerings first, then add sections.",
    }),
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-section").addEventListener("click", () => {
        openSectionDrawer(offerings, professors);
      });
    },
  };
}

async function renderSectionDetail({ sectionId }) {
  const [section, availability, allocations] = await Promise.all([
    api.section(sectionId),
    api.sectionAvailability(sectionId),
    api.roomAllocations(sectionId),
  ]);
  return {
    title: `${section.course_code} ${section.section_code}`,
    eyebrow: "Section detail",
    description: section.course_title,
    breadcrumbs: ["Admin", "Sections", `${section.course_code} ${section.section_code}`],
    actions: `<button class="button" data-link="/admin/sections/${section.id}/rooms">Manage rooms</button>`,
    content: `
      <section class="grid two">
        <article class="detail-card">
          <div class="section-head">
            <div>
              <p class="eyebrow">Enrollment</p>
              <h3>${escapeHtml(section.semester_name)}</h3>
            </div>
            ${statusBadge(section.status)}
          </div>
          <div class="detail-grid">
            ${detailItem("Capacity", section.capacity)}
            ${detailItem("Enrolled", availability.enrolled_count)}
            ${detailItem("Remaining", availability.remaining_seats)}
            ${detailItem("Waitlist", availability.waitlist_count)}
          </div>
        </article>
        <article class="panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Delivery</p>
              <h3>Room policy</h3>
            </div>
          </div>
          <div class="detail-grid">
            ${detailItem("Mode", section.room_selection_mode)}
            ${detailItem("Professor ID", section.professor_id ?? "Unassigned")}
            ${detailItem("Allocated rooms", allocations.length)}
            ${detailItem("Offering ID", section.course_offering_id)}
          </div>
        </article>
      </section>
      <section class="panel" style="margin-top: 18px;">
        <div class="section-head">
          <div>
            <p class="eyebrow">Allocated rooms</p>
            <h3>Room pool</h3>
          </div>
        </div>
        ${
          allocations.length
            ? renderTable({
                columns: ["Room", "Capacity", "Type", "Available"],
                rows: allocations.map((allocation) => [
                  `${allocation.building ?? "—"} ${allocation.room_number}`,
                  String(allocation.capacity),
                  allocation.room_type,
                  allocation.available ? statusBadge("available") : statusBadge("unavailable"),
                ]),
              })
            : `<p class="muted">No rooms allocated yet.</p>`
        }
      </section>
    `,
  };
}

async function renderSectionRooms({ sectionId }) {
  const [section, allocations, rooms] = await Promise.all([
    api.section(sectionId),
    api.roomAllocations(sectionId),
    api.rooms(),
  ]);
  return {
    title: "Room allocations",
    eyebrow: `${section.course_code} ${section.section_code}`,
    description: "Choose the rooms available to this section and professor flow.",
    breadcrumbs: ["Admin", "Sections", `${section.course_code} ${section.section_code}`, "Rooms"],
    actions: `<button id="allocate-rooms" class="button">Allocate rooms</button>`,
    content: allocations.length
      ? renderTablePage({
          searchPlaceholder: "Search allocated rooms",
          columns: ["Room", "Capacity", "Type", "Available"],
          rows: allocations.map((allocation) => [
            `${allocation.building ?? "—"} ${allocation.room_number}`,
            String(allocation.capacity),
            allocation.room_type,
            allocation.available ? statusBadge("available") : statusBadge("unavailable"),
          ]),
          emptyTitle: "",
          emptyMessage: "",
        })
      : `
        <section class="empty-state">
          <h3>No rooms allocated yet</h3>
          <p>Allocate one or more rooms so professors or scheduling logic have options.</p>
          <button id="allocate-rooms-empty" class="button">Allocate rooms</button>
        </section>
      `,
    afterRender: () => {
      bindSearch();
      document.querySelector("#allocate-rooms")?.addEventListener("click", () => {
        openRoomAllocationDrawer(section, rooms, allocations);
      });
      document.querySelector("#allocate-rooms-empty")?.addEventListener("click", () => {
        openRoomAllocationDrawer(section, rooms, allocations);
      });
    },
  };
}

async function renderRegistrationPeriods() {
  const [periods, semesters] = await Promise.all([api.registrationPeriods(), api.semesters()]);
  return {
    title: "Registration periods",
    eyebrow: "Delivery",
    description: "Open and monitor the enrollment windows that govern student access.",
    breadcrumbs: ["Admin", "Registration periods"],
    actions: `<button id="create-period" class="button">New period</button>`,
    content: renderTablePage({
      searchPlaceholder: "Search registration periods",
      columns: ["Semester", "Opens", "Closes", "Status", "ID"],
      rows: periods.map((period) => [
        period.semester_name,
        formatDateTime(period.opens_at),
        formatDateTime(period.closes_at),
        statusBadge(period.status),
        `#${period.id}`,
      ]),
      emptyTitle: "No registration periods yet",
      emptyMessage: "Create a window before students begin registration.",
    }),
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-period").addEventListener("click", () => {
        openRegistrationPeriodDrawer(semesters);
      });
    },
  };
}

async function renderScheduling() {
  const [runs, semesters] = await Promise.all([api.schedulingRuns(), api.semesters()]);
  return {
    title: "Scheduling",
    eyebrow: "Delivery",
    description: "Generate timetable suggestions and approve the strongest room assignments.",
    breadcrumbs: ["Admin", "Scheduling"],
    actions: `<button id="create-run" class="button">New suggestion run</button>`,
    content: runs.length
      ? renderTablePage({
          searchPlaceholder: "Search scheduling runs",
          columns: ["Run", "Semester", "Strategy", "Status", "Created"],
          rows: runs.map((run) => [
            `<a class="link" href="/admin/scheduling/${run.id}" data-link="/admin/scheduling/${run.id}">#${run.id}</a>`,
            `#${run.semester_id}`,
            run.strategy,
            statusBadge(run.status),
            formatDateTime(run.created_at),
          ]),
          emptyTitle: "",
          emptyMessage: "",
        })
      : `
        <section class="empty-state">
          <h3>No scheduling runs yet</h3>
          <p>Start the first suggestion run to review generated room assignments.</p>
          <button id="create-run-empty" class="button">Start a run</button>
        </section>
      `,
    afterRender: () => {
      bindSearch();
      document.querySelector("#create-run")?.addEventListener("click", () => {
        openSchedulingDrawer(semesters);
      });
      document.querySelector("#create-run-empty")?.addEventListener("click", () => {
        openSchedulingDrawer(semesters);
      });
    },
  };
}

async function renderSchedulingRun({ runId }) {
  const [run, sections, rooms] = await Promise.all([
    api.schedulingRun(runId),
    api.sections(),
    api.rooms(),
  ]);
  const sectionById = Object.fromEntries(sections.map((item) => [item.id, item]));
  const roomById = Object.fromEntries(rooms.map((item) => [item.id, item]));
  return {
    title: `Suggestion run #${run.id}`,
    eyebrow: "Scheduling",
    description: `Strategy: ${run.strategy}`,
    breadcrumbs: ["Admin", "Scheduling", `Run #${run.id}`],
    actions:
      run.status === "approved"
        ? statusBadge("approved")
        : `<button id="approve-run" class="button">Approve run</button>`,
    content: `
      <section class="grid three">
        ${metricCard("Semester", run.semester_id, "Run target")}
        ${metricCard("Items", run.items.length, "Suggested assignments")}
        ${metricCard("Status", run.status, "Current lifecycle")}
      </section>
      <section class="panel" style="margin-top: 18px;">
        <div class="section-head">
          <div>
            <p class="eyebrow">Suggestions</p>
            <h3>Generated items</h3>
          </div>
        </div>
        ${
          run.items.length
            ? renderTable({
                columns: ["Section", "Room", "Score", "Status", "Reasons"],
                rows: run.items.map((item) => {
                  const section = sectionById[item.section_id];
                  const room = item.room_id ? roomById[item.room_id] : null;
                  return [
                    section
                      ? `${section.course_code} ${section.section_code}`
                      : `Section #${item.section_id}`,
                    room ? `${room.building ?? "—"} ${room.room_number}` : "No room",
                    String(item.score),
                    statusBadge(item.status),
                    item.reasons
                      ? `<details><summary>View</summary><pre class="pre">${escapeHtml(
                          JSON.stringify(item.reasons, null, 2),
                        )}</pre></details>`
                      : "—",
                  ];
                }),
              })
            : `<p class="muted">No scheduling items were generated.</p>`
        }
      </section>
    `,
    afterRender: () => {
      document.querySelector("#approve-run")?.addEventListener("click", async () => {
        try {
          const result = await api.approveSchedulingRun(run.id);
          showToast("Run approved", `${result.approved_items} items approved.`);
          renderCurrentRoute();
        } catch (error) {
          showToast("Could not approve run", error.message, "error");
        }
      });
    },
  };
}

async function renderAuditLogs() {
  const logs = await api.auditLogs();
  return {
    title: "Audit logs",
    eyebrow: "Governance",
    description: "Review recent administrative changes and registration-side effects.",
    breadcrumbs: ["Admin", "Audit logs"],
    content: renderTablePage({
      searchPlaceholder: "Search event type or entity",
      columns: ["Event", "Entity", "Entity ID", "Created", "Payload"],
      rows: logs.map((log) => [
        `<strong>${escapeHtml(humanizeEvent(log.event_type))}</strong>`,
        log.entity_type,
        log.entity_id ?? "—",
        formatDateTime(log.created_at),
        log.payload
          ? `<details><summary>View</summary><pre class="pre">${escapeHtml(
              JSON.stringify(log.payload, null, 2),
            )}</pre></details>`
          : "—",
      ]),
      emptyTitle: "No audit logs yet",
      emptyMessage: "Administrative changes will appear here.",
    }),
    afterRender: bindSearch,
  };
}

async function renderObservability() {
  const [health, dependencyHealth, metrics] = await Promise.all([
    api.health(),
    api.dependencyHealth(),
    api.metrics(),
  ]);
  const metricPreview = metrics.split("\n").filter(Boolean).slice(0, 18).join("\n");
  return {
    title: "Observability",
    eyebrow: "Platform health",
    description: "A concise operating view of the backend and its supporting services.",
    breadcrumbs: ["Admin", "Observability"],
    content: `
      <section class="grid three">
        ${metricCard("API health", health.status, "Root health endpoint")}
        ${metricCard("Dependencies", dependencyHealth.status, "Required service check")}
        ${metricCard("Metrics lines", metrics.split("\n").filter(Boolean).length, "Prometheus output")}
      </section>
      <section class="grid two" style="margin-top: 18px;">
        <article class="panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Dependencies</p>
              <h3>Service checks</h3>
            </div>
            ${statusBadge(dependencyHealth.status)}
          </div>
          <div class="timeline">
            ${Object.entries(dependencyHealth.checks)
              .map(
                ([name, value]) => `
                  <div class="timeline-item">
                    <strong>${escapeHtml(name)}</strong>
                    <span>${escapeHtml(String(value))}</span>
                  </div>
                `,
              )
              .join("")}
          </div>
        </article>
        <article class="panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">External tools</p>
              <h3>Continue in the stack</h3>
            </div>
          </div>
          <div class="timeline">
            <div class="timeline-item">
              <strong>Grafana</strong>
              <span>Default local URL: http://localhost:3000</span>
            </div>
            <div class="timeline-item">
              <strong>Prometheus</strong>
              <span>Default local URL: http://localhost:9090</span>
            </div>
            <div class="timeline-item">
              <strong>Tempo / Loki</strong>
              <span>Inspect traces and logs through the provisioned Grafana datasources.</span>
            </div>
          </div>
        </article>
      </section>
      <section class="panel" style="margin-top: 18px;">
        <div class="section-head">
          <div>
            <p class="eyebrow">Metrics preview</p>
            <h3>Prometheus sample</h3>
          </div>
        </div>
        <pre class="pre">${escapeHtml(metricPreview)}</pre>
      </section>
    `,
  };
}

function renderTablePage({ searchPlaceholder, columns, rows, emptyTitle, emptyMessage }) {
  if (!rows.length) {
    return `
      <section class="empty-state">
        <h3>${escapeHtml(emptyTitle)}</h3>
        <p>${escapeHtml(emptyMessage)}</p>
      </section>
    `;
  }
  return `
    <section class="table-card">
      <div style="padding: 16px 16px 0;">
        <div class="searchbar">
          <input id="table-search" type="search" placeholder="${escapeHtml(searchPlaceholder)}" />
        </div>
      </div>
      ${renderTable({ columns, rows })}
    </section>
  `;
}

function renderTable({ columns, rows }) {
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows
            .map(
              (row) => `
                <tr data-searchable="${escapeHtml(stripHtml(row.join(" ")))}">
                  ${row.map((cell) => `<td>${cell}</td>`).join("")}
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function bindSearch() {
  const input = document.querySelector("#table-search");
  if (!input) return;
  input.addEventListener("input", () => {
    const needle = input.value.trim().toLowerCase();
    document.querySelectorAll("tbody tr").forEach((row) => {
      row.hidden = !row.dataset.searchable.toLowerCase().includes(needle);
    });
  });
}

function renderErrorState(message) {
  return `
    <section class="empty-state">
      <h3>Could not load this page</h3>
      <p>${escapeHtml(message)}</p>
      <button class="button" data-link="/admin">Return to dashboard</button>
    </section>
  `;
}

function openSemesterDrawer() {
  openDrawer({
    title: "New semester",
    body: `
      <form id="drawer-form" class="form-grid">
        ${inputField("Name", "name", "text", "Spring 2026", true)}
        ${selectField("Status", "status", statusOptions(["active", "draft", "archived"]))}
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      await api.createSemester({ name: data.get("name"), status: data.get("status") });
      showToast("Semester created", `${data.get("name")} is ready.`);
    },
  });
}

function openDepartmentDrawer() {
  openDrawer({
    title: "New department",
    body: `
      <form id="drawer-form" class="form-grid">
        ${inputField("Code", "code", "text", "CSE", true)}
        ${inputField("Name", "name", "text", "Computer Science", true)}
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      await api.createDepartment({ code: data.get("code"), name: data.get("name") });
      showToast("Department created", `${data.get("name")} added.`);
    },
  });
}

function openMajorDrawer(departments) {
  openDrawer({
    title: "New major",
    body: `
      <form id="drawer-form" class="form-grid">
        ${selectField(
          "Department",
          "department_id",
          departments.map((item) => ({ value: item.id, label: `${item.code} · ${item.name}` })),
          null,
          true,
        )}
        ${inputField("Code", "code", "text", "SE", true)}
        ${inputField("Name", "name", "text", "Software Engineering", true)}
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      await api.createMajor({
        department_id: Number(data.get("department_id")),
        code: data.get("code"),
        name: data.get("name"),
      });
      showToast("Major created", `${data.get("name")} added.`);
    },
  });
}

function openEligibilityRuleDrawer(course, departments, majors) {
  openDrawer({
    title: `New eligibility rule · ${course.code}`,
    body: `
      <form id="drawer-form" class="form-grid">
        ${inputField("Minimum academic year", "min_academic_year", "number", "3", false, `min="1" max="6"`)}
        ${inputField("Minimum GPA", "min_gpa", "number", "3.5", false, `min="0" max="5" step="0.01"`)}
        ${selectField(
          "Allowed departments",
          "allowed_department_ids",
          departments.map((item) => ({ value: item.id, label: `${item.code} · ${item.name}` })),
          "Any department",
          false,
          "multiple",
        )}
        ${selectField(
          "Allowed majors",
          "allowed_major_ids",
          majors.map((item) => ({ value: item.id, label: `${item.code} · ${item.name}` })),
          "Any major",
          false,
          "multiple",
        )}
      </form>
    `,
    onSubmit: async () => {
      const form = document.querySelector("#drawer-form");
      const data = new FormData(form);
      await api.createEligibilityRule(course.id, {
        min_academic_year: optionalNumber(data.get("min_academic_year")),
        min_gpa: optionalNumber(data.get("min_gpa")),
        allowed_department_ids: selectedNumbers(form, "allowed_department_ids"),
        allowed_major_ids: selectedNumbers(form, "allowed_major_ids"),
        rule_metadata: null,
      });
      showToast("Eligibility rule created", `${course.code} has a new rule.`);
    },
  });
}

function openProfessorDrawer() {
  openDrawer({
    title: "New professor",
    body: `
      <form id="drawer-form" class="form-grid">
        ${inputField("Email", "email", "email", "professor@crsp.local", true)}
        ${inputField("Full name", "full_name", "text", "Professor Name", true)}
        ${inputField("Department name", "department_name", "text", "Computer Science")}
        ${inputField("Password", "password", "password", "prof12345", true)}
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      await api.createProfessor({
        email: data.get("email"),
        full_name: data.get("full_name"),
        department_name: optionalText(data.get("department_name")),
        password: data.get("password"),
      });
      showToast("Professor created", `${data.get("full_name")} can now sign in.`);
    },
  });
}

function openRoomDrawer() {
  openDrawer({
    title: "New room",
    body: `
      <form id="drawer-form" class="form-grid">
        <div class="form-grid two">
          ${inputField("Building", "building", "text", "B")}
          ${inputField("Room number", "room_number", "text", "305", true)}
        </div>
        <div class="form-grid two">
          ${inputField("Capacity", "capacity", "number", "30", true, `min="1"`)}
          ${inputField("Room type", "room_type", "text", "lecture", true)}
        </div>
        <label class="checkbox-row">
          <input name="is_active" type="checkbox" checked />
          <span>Room is active</span>
        </label>
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      await api.createRoom({
        building: optionalText(data.get("building")),
        room_number: data.get("room_number"),
        capacity: Number(data.get("capacity")),
        room_type: data.get("room_type"),
        is_active: data.get("is_active") === "on",
      });
      showToast("Room created", `${data.get("room_number")} added.`);
    },
  });
}

function openOfferingDrawer(courses, semesters) {
  openDrawer({
    title: "New offering",
    body: `
      <form id="drawer-form" class="form-grid">
        ${selectField(
          "Course",
          "course_id",
          courses.map((item) => ({ value: item.id, label: `${item.code} · ${item.title}` })),
          null,
          true,
        )}
        ${selectField(
          "Semester",
          "semester_id",
          semesters.map((item) => ({ value: item.id, label: item.name })),
          null,
          true,
        )}
        ${selectField("Status", "status", statusOptions(["active", "draft", "cancelled", "archived"]))}
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      await api.createOffering({
        course_id: Number(data.get("course_id")),
        semester_id: Number(data.get("semester_id")),
        status: data.get("status"),
      });
      showToast("Offering created", "Semester delivery plan updated.");
    },
  });
}

function openSectionDrawer(offerings, professors) {
  openDrawer({
    title: "New section",
    body: `
      <form id="drawer-form" class="form-grid">
        ${selectField(
          "Offering",
          "course_offering_id",
          offerings.map((item) => ({
            value: item.id,
            label: `${item.course_code} · ${item.semester_name}`,
          })),
          null,
          true,
        )}
        ${selectField(
          "Professor",
          "professor_id",
          professors.map((item) => ({ value: item.id, label: item.full_name })),
          "Unassigned",
        )}
        <div class="form-grid two">
          ${inputField("Section code", "section_code", "text", "001", true)}
          ${inputField("Capacity", "capacity", "number", "30", true, `min="1" max="500"`)}
        </div>
        ${selectField(
          "Room selection mode",
          "room_selection_mode",
          statusOptions(["admin_fixed", "professor_choice", "system_recommended"]),
        )}
        ${selectField("Status", "status", statusOptions(["open", "draft", "closed", "cancelled"]))}
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      await api.createSection({
        course_offering_id: Number(data.get("course_offering_id")),
        professor_id: optionalNumber(data.get("professor_id")),
        section_code: data.get("section_code"),
        capacity: Number(data.get("capacity")),
        room_selection_mode: data.get("room_selection_mode"),
        status: data.get("status"),
      });
      showToast("Section created", "Delivery inventory updated.");
    },
  });
}

function openRoomAllocationDrawer(section, rooms, allocations) {
  const allocatedIds = new Set(allocations.map((item) => item.room_id));
  const availableRooms = rooms.filter((room) => !allocatedIds.has(room.id));
  openDrawer({
    title: `Allocate rooms · ${section.course_code} ${section.section_code}`,
    body: `
      <form id="drawer-form" class="form-grid">
        ${
          allocations.length
            ? `<p class="muted">Already allocated: ${escapeHtml(
                allocations
                  .map((item) => `${item.building ?? "—"} ${item.room_number}`)
                  .join(", "),
              )}</p>`
            : ""
        }
        <div class="selection-grid">
          ${
            availableRooms.length
              ? availableRooms
                  .map(
                    (room) => `
                      <label class="selection-card">
                        <input type="checkbox" name="room_ids" value="${room.id}" />
                        <span>
                          <strong>${escapeHtml(`${room.building ?? "—"} ${room.room_number}`)}</strong>
                          <span>${room.capacity} seats · ${escapeHtml(room.room_type)}</span>
                        </span>
                      </label>
                    `,
                  )
                  .join("")
              : `<p class="muted">Every active room is already allocated to this section.</p>`
          }
        </div>
        ${textareaField("Notes", "notes", "Optional allocation notes")}
      </form>
    `,
    onSubmit: async () => {
      const form = document.querySelector("#drawer-form");
      const roomIds = [...form.querySelectorAll('input[name="room_ids"]:checked')].map((input) =>
        Number(input.value),
      );
      if (!roomIds.length) {
        throw new Error("Select at least one new room to allocate.");
      }
      await api.allocateRooms(section.id, {
        room_ids: roomIds,
        notes: optionalText(new FormData(form).get("notes")),
      });
      showToast("Rooms allocated", `${roomIds.length} room option(s) saved.`);
    },
  });
}

function openRegistrationPeriodDrawer(semesters) {
  openDrawer({
    title: "New registration period",
    body: `
      <form id="drawer-form" class="form-grid">
        ${selectField(
          "Semester",
          "semester_id",
          semesters.map((item) => ({ value: item.id, label: item.name })),
          null,
          true,
        )}
        ${inputField("Opens at", "opens_at", "datetime-local", "", true)}
        ${inputField("Closes at", "closes_at", "datetime-local", "", true)}
        ${selectField("Status", "status", statusOptions(["open", "closed"]))}
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      await api.createRegistrationPeriod({
        semester_id: Number(data.get("semester_id")),
        opens_at: new Date(data.get("opens_at")).toISOString(),
        closes_at: new Date(data.get("closes_at")).toISOString(),
        status: data.get("status"),
      });
      showToast("Registration period created", "Enrollment window configured.");
    },
  });
}

function openSchedulingDrawer(semesters) {
  openDrawer({
    title: "New suggestion run",
    body: `
      <form id="drawer-form" class="form-grid">
        ${selectField(
          "Semester",
          "semester_id",
          semesters.map((item) => ({ value: item.id, label: item.name })),
          null,
          true,
        )}
        ${inputField("Strategy", "strategy", "text", "balanced_heuristic", true)}
      </form>
    `,
    onSubmit: async () => {
      const data = getDrawerFormData();
      const result = await api.createSchedulingRun({
        semester_id: Number(data.get("semester_id")),
        strategy: data.get("strategy"),
      });
      showToast("Suggestion run created", `Run #${result.run_id} completed.`);
      navigate(`/admin/scheduling/${result.run_id}`);
    },
    rerenderAfterSubmit: false,
  });
}

function openDrawer({ title, body, onSubmit, rerenderAfterSubmit = true }) {
  drawerRoot.innerHTML = `
    <div class="drawer-backdrop">
      <aside class="drawer" role="dialog" aria-modal="true">
        <div class="drawer-head">
          <div>
            <p class="eyebrow">Admin action</p>
            <h3>${escapeHtml(title)}</h3>
          </div>
          <button class="icon-button" data-close-drawer aria-label="Close drawer">×</button>
        </div>
        <div class="drawer-body">${body}</div>
        <div class="drawer-foot">
          <button class="ghost-button" data-close-drawer type="button">Cancel</button>
          <button id="drawer-submit" class="button" type="button">Save</button>
        </div>
      </aside>
    </div>
  `;

  const submitDrawer = async () => {
    try {
      await onSubmit();
      closeDrawer();
      if (rerenderAfterSubmit) {
        renderCurrentRoute();
      }
    } catch (error) {
      showToast("Could not save", error.message, "error");
    }
  };

  document.querySelector("#drawer-submit").addEventListener("click", submitDrawer);
  document.querySelector("#drawer-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitDrawer();
  });
}

function closeDrawer() {
  drawerRoot.innerHTML = "";
}

function getDrawerFormData() {
  return new FormData(document.querySelector("#drawer-form"));
}

function showToast(title, message, type = "success") {
  const toast = document.createElement("article");
  toast.className = `toast ${type === "error" ? "error" : ""}`;
  toast.innerHTML = `
    <strong>${escapeHtml(title)}</strong>
    <span>${escapeHtml(message)}</span>
  `;
  toastRoot.appendChild(toast);
  window.setTimeout(() => toast.remove(), 3800);
}

function metricCard(label, value, hint) {
  return `
    <article class="metric-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value))}</strong>
      <em>${escapeHtml(hint)}</em>
    </article>
  `;
}

function miniStat(label, value) {
  return `
    <article class="metric-card">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value))}</strong>
    </article>
  `;
}

function detailItem(label, value) {
  return `
    <div class="detail-item">
      <span>${escapeHtml(label)}</span>
      <strong>${escapeHtml(String(value))}</strong>
    </div>
  `;
}

function statusBadge(status) {
  const normalized = String(status).toLowerCase();
  const kind = ["active", "open", "approved", "available", "ok", "completed"].includes(normalized)
    ? "success"
    : ["draft", "running", "queued"].includes(normalized)
      ? "info"
      : ["archived", "closed"].includes(normalized)
        ? "neutral"
        : ["cancelled", "failed", "degraded", "inactive", "unavailable"].includes(normalized)
          ? "danger"
          : "warning";
  return `<span class="badge ${kind}">${escapeHtml(normalized.replaceAll("_", " "))}</span>`;
}

function statusOptions(values) {
  return values.map((value) => ({ value, label: value.replaceAll("_", " ") }));
}

function inputField(label, name, type, placeholder = "", required = false, attrs = "") {
  return `
    <label>
      <span>${escapeHtml(label)}</span>
      <input
        name="${escapeHtml(name)}"
        type="${escapeHtml(type)}"
        placeholder="${escapeHtml(placeholder)}"
        ${required ? "required" : ""}
        ${attrs}
      />
    </label>
  `;
}

function textareaField(label, name, placeholder = "") {
  return `
    <label>
      <span>${escapeHtml(label)}</span>
      <textarea name="${escapeHtml(name)}" placeholder="${escapeHtml(placeholder)}"></textarea>
    </label>
  `;
}

function selectField(label, name, options, placeholder = null, required = false, extraAttr = "") {
  return `
    <label>
      <span>${escapeHtml(label)}</span>
      <select name="${escapeHtml(name)}" ${required ? "required" : ""} ${extraAttr}>
        ${
          placeholder !== null
            ? `<option value="">${escapeHtml(placeholder)}</option>`
            : ""
        }
        ${options
          .map(
            (option) =>
              `<option value="${escapeHtml(String(option.value))}">${escapeHtml(option.label)}</option>`,
          )
          .join("")}
      </select>
    </label>
  `;
}

function optionalNumber(value) {
  return value === null || value === undefined || value === "" ? null : Number(value);
}

function optionalText(value) {
  const text = String(value ?? "").trim();
  return text || null;
}

function selectedNumbers(form, fieldName) {
  const select = form.elements[fieldName];
  const values = [...select.selectedOptions].map((option) => Number(option.value));
  return values.length ? values : null;
}

function readableIds(ids, items) {
  if (!ids?.length) return "Any";
  const itemById = Object.fromEntries(items.map((item) => [item.id, item]));
  return ids
    .map((id) => itemById[id]?.code ?? itemById[id]?.name ?? `#${id}`)
    .join(", ");
}

function formatDateTime(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function humanizeEvent(value) {
  return value
    .replace(/^admin_/, "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function stripHtml(value) {
  const temp = document.createElement("div");
  temp.innerHTML = value;
  return temp.textContent ?? temp.innerText ?? "";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
