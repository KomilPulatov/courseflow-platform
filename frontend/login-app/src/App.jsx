import { useState } from 'react'
import styles from './App.module.css'

// ─────────────────────────────────────────────────────────────────────────────
// API Helper
// Vite's dev proxy forwards /api/* → http://localhost:8000
// In production, FastAPI serves this on the same origin.
// ─────────────────────────────────────────────────────────────────────────────
async function apiPost(path, body) {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const isJson = res.headers.get('content-type')?.includes('application/json')
  const data = isJson ? await res.json() : await res.text()
  if (!res.ok) {
    let msg = data;
    if (typeof data !== 'string') {
      if (data.detail) {
        msg = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      } else {
        msg = JSON.stringify(data);
      }
    }
    throw new Error(msg);
  }
  return data
}

function storeToken(key, token) {
  localStorage.setItem(key, token)
}

function redirectToDashboard(role) {
  let path = 'student'
  if (role === 'admin') path = 'app/'
  else if (role === 'professor') path = 'professor/'

  if (window.location.port === '5174') {
    // Development: Redirect to the main frontend app's dev server
    window.location.href = `http://localhost:5173/${path}`
  } else {
    // Production/FastAPI: Redirect to the mounted main app
    window.location.href = `/demo/${path}`
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// SVG Icons
// ─────────────────────────────────────────────────────────────────────────────
const IconMonitor = () => (
  <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="3" width="20" height="14" rx="2" />
    <path d="M8 21h8M12 17v4" />
  </svg>
)
const IconMail = () => (
  <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="4" width="20" height="16" rx="2" />
    <path d="M2 7l10 7 10-7" />
  </svg>
)
const IconHome = () => (
  <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" />
    <path d="M9 21V12h6v9" />
  </svg>
)
const IconGlobe = () => (
  <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="9" />
    <path d="M12 3a15 15 0 010 18M3 12h18" />
    <path d="M4.5 7.5a15 15 0 0115 0M4.5 16.5a15 15 0 0115 0" />
  </svg>
)
const IconSeal = () => (
  <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 3L2 8l10 5 10-5-10-5zM2 13l10 5 10-5M2 18l10 5 10-5" stroke="#fff" />
  </svg>
)
const IconVerified = () => (
  <svg viewBox="0 0 24 24" fill="none" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M9 12l2 2 4-4" />
    <path d="M12 2a10 10 0 100 20A10 10 0 0012 2z" />
  </svg>
)

// ─────────────────────────────────────────────────────────────────────────────
// Reusable UI
// ─────────────────────────────────────────────────────────────────────────────
function StatusMessage({ message, type }) {
  if (!message) return null
  return (
    <div
      className={`${styles.status} ${type === 'success' ? styles.statusSuccess : styles.statusError}`}
      role="alert"
      aria-live="polite"
    >
      {message}
    </div>
  )
}

function Field({ id, label, name, type = 'text', placeholder, autoComplete, defaultValue }) {
  return (
    <div className={styles.field}>
      <label htmlFor={id}>{label}</label>
      <input id={id} name={name} type={type} placeholder={placeholder} autoComplete={autoComplete} defaultValue={defaultValue} required />
    </div>
  )
}

function SubmitButton({ loading, label = 'LOGIN', loadingLabel = 'SIGNING IN…' }) {
  return (
    <button
      type="submit"
      className={`${styles.btnLogin} ${loading ? styles.btnLoading : ''}`}
      disabled={loading}
    >
      {loading ? loadingLabel : label}
    </button>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Form hook — reduces boilerplate
// ─────────────────────────────────────────────────────────────────────────────
function useFormSubmit(endpoint, buildPayload, storageKey, options = {}) {
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState({ msg: '', type: '' })

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus({ msg: '', type: '' })

    const fd = new FormData(e.currentTarget)
    const payload = buildPayload(fd)

    // Simple client-side validation — check no required field is empty
    const missing = Object.values(payload).some(v => !String(v ?? '').trim())
    if (missing) {
      setStatus({ msg: 'Please fill in all fields.', type: 'error' })
      return
    }

    setLoading(true)
    try {
      const result = await apiPost(endpoint, payload)
      if (storageKey) storeToken(storageKey, result.access_token)
      const successMsg = options.successMsg ?? 'Success! Redirecting to dashboard…'
      setStatus({ msg: successMsg, type: 'success' })
      setTimeout(() => redirectToDashboard(result.role), 900)
    } catch (err) {
      setStatus({ msg: err.message || 'Request failed. Please try again.', type: 'error' })
      setLoading(false)
    }
  }

  return { loading, status, handleSubmit }
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB 1 — INS Login (Verified academic profile via ins.inha.uz)
// POST /api/v1/auth/student/ins-login
// Body: { student_number, password }
// ─────────────────────────────────────────────────────────────────────────────
function InsLoginForm() {
  const { loading, status, handleSubmit } = useFormSubmit(
    '/api/v1/auth/student/ins-login',
    fd => ({
      student_number: fd.get('student_number')?.trim() ?? '',
      password:       fd.get('password')?.trim() ?? '',
    }),
    'lp_studentToken',
    { successMsg: 'INS login successful! Loading your verified profile…' }
  )

  return (
    <form onSubmit={handleSubmit} className={styles.form} noValidate>
      <div className={styles.insNote}>
        <span className={styles.insNoteIcon}><IconVerified /></span>
        <span>
          Your academic data (GPA, department, courses) will be automatically
          pulled from <strong>ins.inha.uz</strong> and verified.
        </span>
      </div>

      <Field
        id="ins-student-number"
        label="Student Number"
        name="student_number"
        placeholder="e.g. 2310204"
        autoComplete="username"
      />
      <Field
        id="ins-password"
        label="INS Password"
        name="password"
        type="password"
        placeholder="Your ins.inha.uz password"
        autoComplete="current-password"
      />

      <StatusMessage message={status.msg} type={status.type} />
      <SubmitButton loading={loading} />

      <div className={styles.formLinks}>
        <a href="http://ins.inha.uz/" target="_blank" rel="noopener">
          Open INS Portal →
        </a>
      </div>
    </form>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB 2 — Manual Login (existing manual account)
// POST /api/v1/auth/student/manual-login
// Body: { email, password }
// ─────────────────────────────────────────────────────────────────────────────
function ManualLoginForm() {
  const { loading, status, handleSubmit } = useFormSubmit(
    '/api/v1/auth/student/manual-login',
    fd => ({
      email:    fd.get('email')?.trim() ?? '',
      password: fd.get('password')?.trim() ?? '',
    }),
    'lp_studentToken',
    { successMsg: 'Login successful! Redirecting…' }
  )

  return (
    <form onSubmit={handleSubmit} className={styles.form} noValidate>
      <Field
        id="manual-email"
        label="Email Address"
        name="email"
        type="email"
        placeholder="you@example.com"
        autoComplete="username"
        defaultValue="student@crsp.example.com"
      />
      <Field
        id="manual-password"
        label="Password"
        name="password"
        type="password"
        placeholder="Enter your password"
        autoComplete="current-password"
        defaultValue="student12345"
      />

      <StatusMessage message={status.msg} type={status.type} />
      <SubmitButton loading={loading} />

      <div className={styles.formLinks}>
        <a href="https://itislink.inha.ac.kr/passWord/help/" target="_blank" rel="noopener">
          Forgot password?
        </a>
      </div>
    </form>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// TAB 3 — Manual Start (register a new manual student account)
// POST /api/v1/auth/student/manual-start
// Body: { student_number, full_name, email, password }
// ─────────────────────────────────────────────────────────────────────────────
function ManualStartForm() {
  const { loading, status, handleSubmit } = useFormSubmit(
    '/api/v1/auth/student/manual-start',
    fd => ({
      student_number: fd.get('student_number')?.trim() ?? '',
      full_name:      fd.get('full_name')?.trim() ?? '',
      email:          fd.get('email')?.trim() ?? '',
      password:       fd.get('password')?.trim() ?? '',
    }),
    'lp_studentToken',
    { successMsg: 'Account created! Complete your profile to register for courses.' }
  )

  return (
    <form onSubmit={handleSubmit} className={styles.form} noValidate>
      <div className={styles.infoNote}>
        Use this if you are not yet registered in INS. You will need to
        complete your academic profile manually before registering for courses.
      </div>

      <Field
        id="ms-student-number"
        label="Student Number"
        name="student_number"
        placeholder="e.g. 2310204"
        autoComplete="off"
      />
      <Field
        id="ms-full-name"
        label="Full Name"
        name="full_name"
        placeholder="As on your student ID"
        autoComplete="name"
      />
      <Field
        id="ms-email"
        label="Email Address"
        name="email"
        type="email"
        placeholder="you@example.com"
        autoComplete="email"
      />
      <Field
        id="ms-password"
        label="Create Password"
        name="password"
        type="password"
        placeholder="Minimum 8 characters"
        autoComplete="new-password"
      />

      <StatusMessage message={status.msg} type={status.type} />
      <SubmitButton loading={loading} label="CREATE ACCOUNT" loadingLabel="CREATING…" />
    </form>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Professor Login
// POST /api/v1/auth/professor/login
// Body: { email, password }
// ─────────────────────────────────────────────────────────────────────────────
function ProfessorLoginForm() {
  const { loading, status, handleSubmit } = useFormSubmit(
    '/api/v1/auth/professor/login',
    fd => ({
      email:    fd.get('email')?.trim() ?? '',
      password: fd.get('password')?.trim() ?? '',
    }),
    'lp_professorToken',
    { successMsg: 'Professor login successful! Redirecting…' }
  )

  return (
    <form onSubmit={handleSubmit} className={styles.form} noValidate>
      <Field
        id="prof-email"
        label="Professor Email"
        name="email"
        type="email"
        placeholder="professor@crsp.example.com"
        autoComplete="username"
        defaultValue="professor@crsp.example.com"
      />
      <Field
        id="prof-password"
        label="Password"
        name="password"
        type="password"
        placeholder="Enter your password"
        autoComplete="current-password"
        defaultValue="prof12345"
      />

      <StatusMessage message={status.msg} type={status.type} />
      <SubmitButton loading={loading} />

      <div className={styles.formLinks}>
        <a href="mailto:it-support@inha.uz">Contact IT Support</a>
      </div>
    </form>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Admin SSO Login
// POST /api/v1/auth/admin/login
// Body: { email, password }
// ─────────────────────────────────────────────────────────────────────────────
function AdminLoginForm() {
  const { loading, status, handleSubmit } = useFormSubmit(
    '/api/v1/auth/admin/login',
    fd => ({
      email:    fd.get('email')?.trim() ?? '',
      password: fd.get('password')?.trim() ?? '',
    }),
    'lp_adminToken',
    { successMsg: 'Admin login successful! Redirecting…' }
  )

  return (
    <form onSubmit={handleSubmit} className={styles.form} noValidate>
      <Field
        id="admin-email"
        label="Admin Email"
        name="email"
        type="email"
        placeholder="admin@crsp.example.com"
        autoComplete="username"
        defaultValue="admin@crsp.example.com"
      />
      <Field
        id="admin-password"
        label="Password"
        name="password"
        type="password"
        placeholder="Enter admin password"
        autoComplete="current-password"
        defaultValue="admin12345"
      />

      <StatusMessage message={status.msg} type={status.type} />
      <SubmitButton loading={loading} />

      <div className={styles.formLinks}>
        <a href="mailto:admin@crsp.local">Contact IT Support</a>
      </div>
    </form>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick-links panel (right side — INS 2×2 grid)
// ─────────────────────────────────────────────────────────────────────────────
const QUICK_LINKS = [
  { href: 'https://eclass.inha.ac.kr/', icon: <IconMonitor />, label: 'e-Class' },
  { href: 'http://mail.inha.uz/',        icon: <IconMail />,    label: 'e-Mail' },
  { href: 'http://www.inha.uz/',         icon: <IconHome />,    label: <>Inha University<br />In Tashkent</> },
  { href: 'http://www.inha.ac.kr/',      icon: <IconGlobe />,   label: <>Inha University<br />In Korea</> },
]

function QuickLinks() {
  return (
    <section className={styles.linksPanel}>
      <p className={styles.linksHeading}>Quick Access</p>
      <div className={styles.linksGrid}>
        {QUICK_LINKS.map(({ href, icon, label }) => (
          <a key={href} href={href} target="_blank" rel="noopener" className={styles.linkTile}>
            <span className={styles.linkIcon}>{icon}</span>
            <span className={styles.linkLabel}>{label}</span>
          </a>
        ))}
      </div>
      <nav className={styles.navLinks} aria-label="External links">
        <a href="http://ins.inha.uz/"    target="_blank" rel="noopener">IUT Portal</a>
        <a href="http://mail.inha.uz/"   target="_blank" rel="noopener">Webmail</a>
        <a href="http://www.inha.uz/"    target="_blank" rel="noopener">IUT Homepage</a>
        <a href="http://www.inha.ac.kr/" target="_blank" rel="noopener">Inha Korea</a>
      </nav>
    </section>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Header — eClass dark navy bar
// ─────────────────────────────────────────────────────────────────────────────
function Header() {
  return (
    <header className={styles.header}>
      <a href="#" className={styles.logo} aria-label="Inha University in Tashkent — CRSP">
        <div className={styles.logoBadge} aria-hidden="true"><IconSeal /></div>
        <div className={styles.logoText}>
          <span className={styles.uniName}>Inha University in Tashkent</span>
          <span className={styles.iutMark}>IUT</span>
        </div>
        <span className={styles.headerLabel}>CyberCampus</span>
      </a>
      <div className={styles.headerRight}>
        <select
          className={styles.langSelect}
          aria-label="Select language"
          onChange={e => {
            const url = new URL(window.location.href)
            url.searchParams.set('lang', e.target.value)
            window.location.href = url.toString()
          }}
        >
          <option value="en">English (en)</option>
          <option value="uz">O'zbek (uz)</option>
          <option value="ko">한국어 (ko)</option>
        </select>
      </div>
    </header>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Footer — INS contact footer
// ─────────────────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className={styles.footer}>
      Inha University in Tashkent&nbsp;|&nbsp;
      9, Ziyolilar str., M.Ulugbek district, Tashkent&nbsp;|&nbsp;
      +998 71 269-00-58&nbsp;|&nbsp;
      <a href="mailto:info@iut.uz">info@iut.uz</a>&nbsp;|&nbsp;
      <a href="http://www.iut.uz" target="_blank" rel="noopener">www.iut.uz</a>
    </footer>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Unified Login Form Container
// ─────────────────────────────────────────────────────────────────────────────
function UnifiedLoginForm() {
  const [role, setRole] = useState('ins')

  return (
    <div>
      <div className={styles.roleGroup}>
        <label htmlFor="role-select" className={styles.roleLabel}>Select Account Type</label>
        <select
          id="role-select"
          className={styles.roleSelect}
          value={role}
          onChange={e => setRole(e.target.value)}
        >
          <option value="ins">Student (INS Verified)</option>
          <option value="manual">Student (Manual Account)</option>
          <option value="professor">Professor</option>
          <option value="admin">Administrator (SSO)</option>
        </select>
      </div>

      <div style={{ marginTop: '24px' }}>
        {role === 'ins' && (
          <>
            <p className={styles.tabHelp}>Login with your ins.inha.uz credentials to get a verified academic profile.</p>
            <InsLoginForm />
          </>
        )}
        {role === 'manual' && (
          <>
            <p className={styles.tabHelp}>Login to your existing manual account using email + password.</p>
            <ManualLoginForm />
          </>
        )}
        {role === 'professor' && (
          <>
            <p className={styles.tabHelp}>Login with your faculty credentials to access your courses.</p>
            <ProfessorLoginForm />
          </>
        )}
        {role === 'admin' && (
          <>
            <p className={styles.tabHelp}>For system administrators only.</p>
            <AdminLoginForm />
          </>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab definitions — simplified to Login and Register
// ─────────────────────────────────────────────────────────────────────────────
const TABS = [
  {
    id:    'login',
    label: 'Login',
    panel: <UnifiedLoginForm />,
  },
  {
    id:    'register',
    label: 'Register',
    panel: <ManualStartForm />,
    help:  "Don't have an account? Create one manually.",
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Root App
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState('login')

  const currentTab = TABS.find(t => t.id === activeTab)

  return (
    <div className={styles.root}>
      <Header />
      <div className={styles.dividerLine} role="separator" />

      <main className={styles.main}>
        <div className={styles.card}>

          {/* ── LEFT: Login Form Panel ── */}
          <section className={styles.formPanel}>
            <h1 className={styles.portalTitle}>
              <span className={styles.iutBold}>IUT</span>
              <span className={styles.portalRest}>&nbsp;Portal System</span>
            </h1>

            {/* Tab bar */}
            <div className={styles.tabs} role="tablist" aria-label="Login method">
              {TABS.map(tab => (
                <button
                  key={tab.id}
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  aria-controls={`lp-panel-${tab.id}`}
                  onClick={() => setActiveTab(tab.id)}
                  className={`${styles.tab} ${activeTab === tab.id ? styles.tabActive : ''}`}
                >
                  {tab.label}
                  {tab.badge && (
                    <span className={styles.tabBadge}>{tab.badge}</span>
                  )}
                </button>
              ))}
            </div>

            {/* Help text for active tab */}
            {currentTab?.help && (
              <p className={styles.tabHelp}>{currentTab.help}</p>
            )}

            {/* Active panel — unmount/remount on tab switch to reset form state */}
            <div
              id={`lp-panel-${activeTab}`}
              role="tabpanel"
              aria-labelledby={`lp-tab-${activeTab}`}
              key={activeTab}
            >
              {currentTab?.panel}
            </div>
          </section>

          {/* ── RIGHT: Quick Links Panel ── */}
          <QuickLinks />

        </div>
      </main>

      <Footer />
    </div>
  )
}
