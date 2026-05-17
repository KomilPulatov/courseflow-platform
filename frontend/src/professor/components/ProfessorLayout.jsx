import { NavLink, useNavigate } from "react-router-dom";

import { signOutProfessor } from "../session.js";

const navItems = [
  { href: "/professor", label: "Professor Home", exact: true },
  { href: "/professor/sections", label: "My Sections" },
  { href: "/professor/timetable", label: "Timetable" },
];

export function ProfessorLayout({
  profile,
  alert,
  children,
  onDismissAlert,
  onLogout,
}) {
  const navigate = useNavigate();

  function logout() {
    signOutProfessor();
    onLogout?.();
    navigate("/professor");
  }

  return (
    <>
      <header className="portal-header">
        <div className="portal-header__inner">
          <div className="logo-wrap">
            <img src="/portal-assets/images/iut-logo.gif" alt="Inha University in Tashkent" />
          </div>
          <div className="header-links">
            {profile ? <NavLink to="/professor/timetable">Timetable</NavLink> : null}
            {profile ? <span className="header-links__divider">|</span> : null}
            <a href="https://class.inha.uz/" target="_blank" rel="noreferrer">
              e-Class
            </a>
            {profile ? (
              <button className="logout-button" type="button" onClick={logout}>
                Logout
              </button>
            ) : null}
          </div>
        </div>
      </header>

      <div className="portal-layout">
        <aside className="portal-sidebar">
          <div className="sidebar-profile">
            <div className="sidebar-profile__school">
              {profile?.department_name || "Professor Portal"}
            </div>
            <div className="sidebar-profile__name">
              {profile?.full_name || "Professor Session Required"}
            </div>
            <div className="sidebar-profile__meta">{profile?.email || ""}</div>
            <div className="sidebar-profile__hint">
              {profile
                ? "Authenticated professor workspace"
                : "Sign in to load your department, assigned sections, room options, and timetable."}
            </div>
          </div>
          {profile ? (
            <nav className="sidebar-nav">
              {navItems.map((item) => (
                <NavLink
                  key={item.href}
                  to={item.href}
                  end={item.exact}
                  className={({ isActive }) =>
                    `sidebar-nav__item${isActive ? " is-active" : ""}`
                  }
                >
                  <span>{item.label}</span>
                  <span className="sidebar-nav__plus">+</span>
                </NavLink>
              ))}
            </nav>
          ) : null}
        </aside>

        <main className="portal-main">
          {alert?.message ? (
            <div className={`inline-alert inline-alert--${alert.type}`}>
              {alert.message}
              {onDismissAlert ? (
                <button className="inline-alert__dismiss" type="button" onClick={onDismissAlert}>
                  ×
                </button>
              ) : null}
            </div>
          ) : null}
          {children}
        </main>

        <aside className="portal-aside">
          <div className="stack-lg">
            <section className="panel-box">
              <div className="panel-box__head">Link Sites</div>
              <div className="panel-box__body">
                <ul className="link-list">
                  <li>
                    <a href="https://inha.uz/" target="_blank" rel="noreferrer">
                      Inha University in Tashkent
                    </a>
                  </li>
                  <li>
                    <a href="https://www.inha.ac.kr/" target="_blank" rel="noreferrer">
                      Inha University in Korea
                    </a>
                  </li>
                  <li>
                    <a href="https://class.inha.uz/" target="_blank" rel="noreferrer">
                      e-Class
                    </a>
                  </li>
                  <li>
                    <a href="mailto:info@iut.uz">e-mail</a>
                  </li>
                </ul>
              </div>
            </section>
            <section className="panel-box">
              <div className="panel-box__head">Help Desk</div>
              <div className="panel-box__body">
                <div className="stack-sm">
                  <div>Contact</div>
                  <div>- +998 71 246-05-73</div>
                  <div>- +998 71 238-65-62</div>
                  <div>e-mail</div>
                  <div>- info@iut.uz</div>
                </div>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </>
  );
}
