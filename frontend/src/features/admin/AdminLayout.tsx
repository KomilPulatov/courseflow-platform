import { Navigate, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import { authStore } from "../../lib/api";

const navGroups = [
  {
    title: "Overview",
    items: [
      { label: "Dashboard", to: "/admin" },
      { label: "Observability", to: "/admin/observability" },
      { label: "Audit logs", to: "/admin/audit-logs" },
    ],
  },
  {
    title: "Academic setup",
    items: [
      { label: "Semesters", to: "/admin/semesters" },
      { label: "Departments", to: "/admin/departments" },
      { label: "Majors", to: "/admin/majors" },
      { label: "Courses", to: "/admin/courses" },
      { label: "Offerings", to: "/admin/offerings" },
    ],
  },
  {
    title: "Delivery",
    items: [
      { label: "Professors", to: "/admin/professors" },
      { label: "Rooms", to: "/admin/rooms" },
      { label: "Sections", to: "/admin/sections" },
      { label: "Registration periods", to: "/admin/registration-periods" },
      { label: "Scheduling", to: "/admin/scheduling" },
    ],
  },
];

export function AdminProtectedRoute() {
  const location = useLocation();
  if (!authStore.admin.get()) {
    return <Navigate to="/admin/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

export function AdminLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const breadcrumbs = location.pathname.split("/").filter(Boolean);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">CR</div>
          <h1>CRSP Admin</h1>
          <p>Modern academy workspace</p>
        </div>
        <nav className="nav-scroll">
          {navGroups.map((group) => (
            <section className="nav-group" key={group.title}>
              <p className="nav-group-title">{group.title}</p>
              {group.items.map((item) => (
                <NavLink
                  end={item.to === "/admin"}
                  className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}
                  to={item.to}
                  key={item.to}
                >
                  {item.label}
                </NavLink>
              ))}
            </section>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="profile-card">
            <strong>Admin session</strong>
            <span>Token stored locally for demo use</span>
            <button
              className="ghost-button"
              type="button"
              onClick={() => {
                authStore.admin.clear();
                navigate("/admin/login");
              }}
            >
              Sign out
            </button>
          </div>
        </div>
      </aside>
      <section className="content">
        <div className="topbar">
          <div className="breadcrumbs">
            {breadcrumbs.map((crumb) => (
              <span key={crumb}>{crumb}</span>
            ))}
          </div>
        </div>
        <Outlet />
      </section>
    </main>
  );
}
