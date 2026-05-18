import { FormEvent, ReactNode, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { authStore, request } from "../../lib/api";

type Role = "student-ins" | "student-manual" | "professor" | "admin";
type Mode = "login" | "register";
type TokenResponse = { access_token: string; role?: string; student_number?: string };

const roleLabels: Record<Role, string> = {
  "student-ins": "Student (INS verified)",
  "student-manual": "Student (manual account)",
  professor: "Professor",
  admin: "Administrator",
};

function dashboardPath(role: Role) {
  if (role === "admin") return "/admin";
  if (role === "professor") return "/professor";
  return "/demo";
}

function tokenStore(role: Role) {
  if (role === "admin") return authStore.admin;
  if (role === "professor") return authStore.professor;
  return authStore.student;
}

function fieldValue(data: FormData, name: string) {
  return String(data.get(name) ?? "").trim();
}

export function UnifiedLoginPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("login");
  const [role, setRole] = useState<Role>("student-ins");
  const [status, setStatus] = useState<{ tone: "error" | "success"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setStatus(null);

    const data = new FormData(event.currentTarget);
    const endpoint =
      mode === "register"
        ? "/api/v1/auth/student/manual-start"
        : role === "student-ins"
          ? "/api/v1/auth/student/ins-login"
          : role === "student-manual"
            ? "/api/v1/auth/student/manual-login"
            : role === "professor"
              ? "/api/v1/auth/professor/login"
              : "/api/v1/auth/admin/login";

    const body =
      mode === "register"
        ? {
            student_number: fieldValue(data, "student_number"),
            full_name: fieldValue(data, "full_name"),
            email: fieldValue(data, "email"),
            password: fieldValue(data, "password"),
          }
        : role === "student-ins"
          ? {
              student_number: fieldValue(data, "student_number"),
              password: fieldValue(data, "password"),
            }
          : {
              email: fieldValue(data, "email"),
              password: fieldValue(data, "password"),
            };

    try {
      const result = await request<TokenResponse>(endpoint, { method: "POST", body });
      const activeRole = mode === "register" ? "student-manual" : role;
      tokenStore(activeRole).set(result.access_token);
      setStatus({ tone: "success", message: "Signed in. Opening your workspace..." });
      window.setTimeout(() => navigate(dashboardPath(activeRole), { replace: true }), 450);
    } catch (error) {
      setStatus({
        tone: "error",
        message: error instanceof Error ? error.message : "Sign-in failed. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="portal-login-shell">
      <header className="portal-login-header">
        <Link to="/demo" className="portal-login-brand" aria-label="CourseFlow demo">
          <span className="brand-mark">CF</span>
          <span>
            <strong>CourseFlow</strong>
            <small>IUT registration platform</small>
          </span>
        </Link>
        <Link to="/demo" className="subtle-button">Demo console</Link>
      </header>

      <section className="portal-login-layout">
        <div className="portal-login-copy">
          <p className="eyebrow">Unified access</p>
          <h1>IUT Portal System</h1>
          <p className="muted">
            Sign in as a student, professor, or administrator from the same CourseFlow frontend.
          </p>
          <div className="portal-login-links" aria-label="External resources">
            <a href="http://ins.inha.uz/" target="_blank" rel="noreferrer">INS Portal</a>
            <a href="https://eclass.inha.ac.kr/" target="_blank" rel="noreferrer">e-Class</a>
            <a href="http://mail.inha.uz/" target="_blank" rel="noreferrer">Webmail</a>
            <a href="http://www.inha.uz/" target="_blank" rel="noreferrer">IUT Homepage</a>
          </div>
        </div>

        <form className="portal-login-card" onSubmit={submit}>
          <div className="portal-login-tabs" role="tablist" aria-label="Login mode">
            <button type="button" className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>
              Login
            </button>
            <button type="button" className={mode === "register" ? "active" : ""} onClick={() => setMode("register")}>
              Register
            </button>
          </div>

          {mode === "login" ? (
            <>
              <label>
                Account type
                <select value={role} onChange={(event) => setRole(event.target.value as Role)}>
                  {Object.entries(roleLabels).map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </label>
              {role === "student-ins" ? (
                <StudentInsFields />
              ) : (
                <EmailPasswordFields role={role} />
              )}
            </>
          ) : (
            <RegisterFields />
          )}

          {status ? <p className={`portal-login-status ${status.tone}`}>{status.message}</p> : null}
          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : mode === "register" ? "Create account" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

function Field({
  name,
  label,
  type = "text",
  defaultValue,
  placeholder,
  autoComplete,
}: {
  name: string;
  label: ReactNode;
  type?: string;
  defaultValue?: string;
  placeholder?: string;
  autoComplete?: string;
}) {
  return (
    <label>
      {label}
      <input
        name={name}
        type={type}
        defaultValue={defaultValue}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required
      />
    </label>
  );
}

function StudentInsFields() {
  return (
    <>
      <p className="portal-login-note">Your academic profile is synced from ins.inha.uz.</p>
      <Field name="student_number" label="Student number" placeholder="2310204" autoComplete="username" />
      <Field name="password" label="INS password" type="password" autoComplete="current-password" />
    </>
  );
}

function EmailPasswordFields({ role }: { role: Role }) {
  const defaults =
    role === "admin"
      ? { email: "admin@crsp.example.com", password: "admin12345" }
      : role === "professor"
        ? { email: "professor@crsp.example.com", password: "prof12345" }
        : { email: "student@crsp.example.com", password: "student12345" };

  return (
    <>
      <Field name="email" label="Email" type="email" defaultValue={defaults.email} autoComplete="username" />
      <Field
        name="password"
        label="Password"
        type="password"
        defaultValue={defaults.password}
        autoComplete="current-password"
      />
    </>
  );
}

function RegisterFields() {
  return (
    <>
      <p className="portal-login-note">Manual student profiles skip GPA-based eligibility rules until verified.</p>
      <Field name="student_number" label="Student number" placeholder="2310204" />
      <Field name="full_name" label="Full name" placeholder="As shown on your student ID" autoComplete="name" />
      <Field name="email" label="Email" type="email" placeholder="you@example.com" autoComplete="email" />
      <Field name="password" label="Password" type="password" autoComplete="new-password" />
    </>
  );
}
