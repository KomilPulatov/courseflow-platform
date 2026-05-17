import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  BookOpen,
  CheckCircle2,
  GraduationCap,
  LogIn,
  RefreshCw,
  Server,
  Shield,
  Trash2,
  Wifi,
} from "lucide-react";
import "./styles.css";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "";

const tokenKeys = {
  admin: "courseflowAdminToken",
  professor: "courseflowProfessorToken",
  student: "courseflowStudentToken",
};

const defaultCredentials = {
  admin: { email: "admin@crsp.local", password: "admin12345" },
  professor: { email: "professor@crsp.local", password: "prof12345" },
};

function App() {
  const [tokens, setTokens] = useState(() => ({
    admin: localStorage.getItem(tokenKeys.admin) ?? "",
    professor: localStorage.getItem(tokenKeys.professor) ?? "",
    student: localStorage.getItem(tokenKeys.student) ?? "",
  }));
  const [courses, setCourses] = useState([]);
  const [search, setSearch] = useState("");
  const [semesterId, setSemesterId] = useState("");
  const [sectionId, setSectionId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [socketState, setSocketState] = useState("Disconnected");
  const socketRef = useRef(null);
  const [events, setEvents] = useState([]);
  const [busy, setBusy] = useState(false);

  const signedInCount = useMemo(
    () => Object.values(tokens).filter(Boolean).length,
    [tokens],
  );

  const pushEvent = useCallback((title, payload) => {
    setEvents((current) => [
      {
        id: crypto.randomUUID(),
        at: new Date().toLocaleTimeString(),
        title,
        payload:
          typeof payload === "string" ? payload : JSON.stringify(payload, null, 2),
      },
      ...current,
    ]);
  }, []);

  const request = useCallback(async (path, options = {}) => {
    const headers = new Headers(options.headers ?? {});
    const token = tokens[options.role ?? "admin"];
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (options.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${apiBaseUrl}${path}`, {
      ...options,
      headers,
    });
    const isJson = response.headers
      .get("content-type")
      ?.includes("application/json");
    const data = isJson ? await response.json() : await response.text();
    if (!response.ok) {
      const message =
        typeof data === "string" ? data : data.detail ?? JSON.stringify(data);
      throw new Error(message);
    }
    return data;
  }, [tokens]);

  const loadCourses = useCallback(async (event) => {
    event?.preventDefault();
    setBusy(true);
    try {
      const params = new URLSearchParams();
      if (search.trim()) params.set("search", search.trim());
      if (semesterId) params.set("semester_id", semesterId);
      const query = params.toString();
      const data = await request(`/api/v1/courses${query ? `?${query}` : ""}`, {
        role: "student",
      });
      setCourses(data);
      pushEvent("Catalog loaded", { count: data.length });
    } catch (error) {
      pushEvent("Catalog failed", error.message);
    } finally {
      setBusy(false);
    }
  }, [pushEvent, request, search, semesterId]);

  async function login(role, formData) {
    setBusy(true);
    try {
      const result = await request(`/api/v1/auth/${role}/login`, {
        method: "POST",
        role,
        body: JSON.stringify({
          email: formData.get("email"),
          password: formData.get("password"),
        }),
      });
      localStorage.setItem(tokenKeys[role], result.access_token);
      setTokens((current) => ({ ...current, [role]: result.access_token }));
      pushEvent(`${role} login`, { token_type: result.token_type ?? "bearer" });
    } catch (error) {
      pushEvent(`${role} login failed`, error.message);
    } finally {
      setBusy(false);
    }
  }

  function clearTokens() {
    Object.values(tokenKeys).forEach((key) => localStorage.removeItem(key));
    setTokens({ admin: "", professor: "", student: "" });
    pushEvent("Session cleared", "Browser tokens removed.");
  }

  async function createStudent(formData) {
    setBusy(true);
    try {
      const result = await request("/api/v1/auth/student/manual-start", {
        method: "POST",
        role: "student",
        body: JSON.stringify({
          student_number: formData.get("studentNumber"),
          full_name: formData.get("fullName"),
          email: formData.get("email"),
          password: formData.get("password"),
        }),
      });
      localStorage.setItem(tokenKeys.student, result.access_token);
      setTokens((current) => ({ ...current, student: result.access_token }));
      pushEvent("Student created", result);
    } catch (error) {
      pushEvent("Student creation failed", error.message);
    } finally {
      setBusy(false);
    }
  }

  async function lookupSection(kind) {
    if (!sectionId) return;
    setBusy(true);
    try {
      const path =
        kind === "eligibility"
          ? `/api/v1/sections/${sectionId}/eligibility`
          : `/api/v1/sections/${sectionId}/availability`;
      const headers =
        kind === "eligibility" && studentId
          ? { "X-Student-Id": String(studentId) }
          : {};
      pushEvent(kind, await request(path, { headers, role: "student" }));
    } catch (error) {
      pushEvent(`${kind} failed`, error.message);
    } finally {
      setBusy(false);
    }
  }

  async function health(path, title) {
    setBusy(true);
    try {
      const result = await request(path, { role: "admin" });
      pushEvent(title, typeof result === "string" ? result.slice(0, 1200) : result);
    } catch (error) {
      pushEvent(`${title} failed`, error.message);
    } finally {
      setBusy(false);
    }
  }

  function connectSocket() {
    if (!sectionId) return;
    socketRef.current?.close();
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const host = apiBaseUrl
      ? new URL(apiBaseUrl, window.location.href).host
      : window.location.host;
    const nextSocket = new WebSocket(
      `${protocol}://${host}/ws/sections/${sectionId}`,
    );
    setSocketState(`Connecting ${sectionId}`);
    nextSocket.addEventListener("open", () => {
      setSocketState(`Live: section ${sectionId}`);
      pushEvent("WebSocket connected", { section_id: Number(sectionId) });
    });
    nextSocket.addEventListener("message", (message) => {
      try {
        pushEvent("WebSocket message", JSON.parse(message.data));
      } catch {
        pushEvent("WebSocket message", message.data);
      }
    });
    nextSocket.addEventListener("close", () => setSocketState("Disconnected"));
    nextSocket.addEventListener("error", () =>
      pushEvent("WebSocket error", { section_id: Number(sectionId) }),
    );
    socketRef.current = nextSocket;
  }

  useEffect(() => {
    let ignore = false;

    async function loadInitialCourses() {
      setBusy(true);
      try {
        const data = await request("/api/v1/courses", { role: "student" });
        if (!ignore) {
          setCourses(data);
          pushEvent("Catalog loaded", { count: data.length });
        }
      } catch (error) {
        if (!ignore) pushEvent("Catalog failed", error.message);
      } finally {
        if (!ignore) setBusy(false);
      }
    }

    loadInitialCourses();
    return () => {
      ignore = true;
    };
  }, [pushEvent, request]);

  useEffect(() => () => socketRef.current?.close(), []);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">CourseFlow Platform</p>
          <h1>Registration operations console</h1>
        </div>
        <div className="status-strip">
          <Status label="Sessions" value={signedInCount} icon={Shield} />
          <Status label="Realtime" value={socketState} icon={Wifi} />
        </div>
      </header>

      <section className="workspace">
        <div className="main-column">
          <Panel title="Catalog" icon={BookOpen}>
            <form className="toolbar" onSubmit={loadCourses}>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search code or title"
              />
              <input
                value={semesterId}
                onChange={(event) => setSemesterId(event.target.value)}
                type="number"
                min="1"
                placeholder="Semester ID"
              />
              <button disabled={busy} type="submit" title="Refresh catalog">
                <RefreshCw size={18} />
                Refresh
              </button>
            </form>
            <div className="course-grid">
              {courses.map((course) => (
                <article className="course-card" key={course.id}>
                  <div>
                    <strong>{course.code}</strong>
                    <h3>{course.title}</h3>
                  </div>
                  <dl>
                    <div>
                      <dt>Credits</dt>
                      <dd>{course.credits}</dd>
                    </div>
                    <div>
                      <dt>Offerings</dt>
                      <dd>{course.active_offering_count ?? 0}</dd>
                    </div>
                    <div>
                      <dt>Sections</dt>
                      <dd>{course.active_section_count ?? 0}</dd>
                    </div>
                  </dl>
                </article>
              ))}
              {!courses.length && (
                <p className="empty">No courses returned by the API yet.</p>
              )}
            </div>
          </Panel>

          <Panel title="Section Checks" icon={CheckCircle2}>
            <div className="toolbar">
              <input
                value={sectionId}
                onChange={(event) => setSectionId(event.target.value)}
                type="number"
                min="1"
                placeholder="Section ID"
              />
              <input
                value={studentId}
                onChange={(event) => setStudentId(event.target.value)}
                type="number"
                min="1"
                placeholder="Student ID"
              />
              <button onClick={() => lookupSection("availability")} type="button">
                Availability
              </button>
              <button onClick={() => lookupSection("eligibility")} type="button">
                Eligibility
              </button>
              <button onClick={connectSocket} type="button">
                <Wifi size={18} />
                Live
              </button>
            </div>
          </Panel>

          <Panel title="Platform Health" icon={Server}>
            <div className="action-grid">
              <button onClick={() => health("/health", "Health")} type="button">
                Health
              </button>
              <button
                onClick={() =>
                  health("/api/v1/health/dependencies", "Dependency health")
                }
                type="button"
              >
                Dependencies
              </button>
              <button onClick={() => health("/metrics", "Metrics")} type="button">
                <Activity size={18} />
                Metrics
              </button>
            </div>
          </Panel>
        </div>

        <aside className="side-column">
          <Panel title="Sessions" icon={LogIn}>
            <LoginForm
              title="Admin"
              defaults={defaultCredentials.admin}
              token={tokens.admin}
              onSubmit={(formData) => login("admin", formData)}
            />
            <LoginForm
              title="Professor"
              defaults={defaultCredentials.professor}
              token={tokens.professor}
              onSubmit={(formData) => login("professor", formData)}
            />
            <StudentForm token={tokens.student} onSubmit={createStudent} />
            <button className="ghost-button" onClick={clearTokens} type="button">
              <Trash2 size={18} />
              Clear sessions
            </button>
          </Panel>

          <Panel title="Event Log" icon={Activity}>
            <button
              className="ghost-button"
              onClick={() => setEvents([])}
              type="button"
            >
              <Trash2 size={18} />
              Clear log
            </button>
            <div className="event-log">
              {events.map((event) => (
                <article key={event.id}>
                  <span>{event.at}</span>
                  <strong>{event.title}</strong>
                  <pre>{event.payload}</pre>
                </article>
              ))}
              {!events.length && <p className="empty">No events yet.</p>}
            </div>
          </Panel>
        </aside>
      </section>
    </main>
  );
}

function Panel({ title, icon, children }) {
  return (
    <section className="panel">
      <div className="panel-title">
        {React.createElement(icon, { size: 20 })}
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}

function Status({ label, value, icon }) {
  return (
    <div className="status">
      {React.createElement(icon, { size: 18 })}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function LoginForm({ title, defaults, token, onSubmit }) {
  return (
    <form
      className="form-stack"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(new FormData(event.currentTarget));
      }}
    >
      <div className="form-heading">
        <h3>{title}</h3>
        <span className={token ? "pill live" : "pill"}>{token ? "Ready" : "Out"}</span>
      </div>
      <input name="email" type="email" defaultValue={defaults.email} required />
      <input
        name="password"
        type="password"
        defaultValue={defaults.password}
        required
      />
      <button type="submit">
        <LogIn size={18} />
        Sign in
      </button>
    </form>
  );
}

function StudentForm({ token, onSubmit }) {
  return (
    <form
      className="form-stack"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(new FormData(event.currentTarget));
      }}
    >
      <div className="form-heading">
        <h3>Student</h3>
        <span className={token ? "pill live" : "pill"}>{token ? "Ready" : "Out"}</span>
      </div>
      <input name="studentNumber" placeholder="Student number" required />
      <input name="fullName" placeholder="Full name" required />
      <input name="email" type="email" placeholder="student@example.com" required />
      <input name="password" type="password" defaultValue="student12345" required />
      <button type="submit">
        <GraduationCap size={18} />
        Create student
      </button>
    </form>
  );
}

export default App;
