import { Link } from "react-router-dom";

export function AppLayout({ title, navItems, currentPath, children }) {
  return (
    <>
      <header className="utility-header">
        <div className="utility-header__inner">
          <div className="logo-wrap">
            <img src="/portal-assets/images/iut-logo.gif" alt="Inha University in Tashkent" />
          </div>
          <div className="header-links">
            <Link to="/app/health">Health</Link>
            <span>|</span>
            <Link to="/app/settings">Settings</Link>
            <span>|</span>
            <a href="/docs">Docs</a>
            <span>|</span>
            <a href="/professor">Professor Portal</a>
          </div>
        </div>
      </header>

      <div className="utility-layout">
        <aside className="utility-sidebar">
          <div className="utility-sidebar__hero">
            <h1>{title}</h1>
            <p>
              Operational status, public-safe runtime metadata, and recovery navigation
              for the platform shell.
            </p>
          </div>
          <nav className="utility-nav">
            {navItems.map((item) => (
              <Link
                key={item.href}
                className={`utility-nav__item${currentPath.startsWith(item.href) ? " is-active" : ""}`}
                to={item.href}
              >
                <span>{item.label}</span>
                <span className="utility-nav__plus">+</span>
              </Link>
            ))}
          </nav>
        </aside>

        <main className="utility-main">
          {children}
        </main>

        <aside className="utility-aside">
          <div className="panel-stack">
            <section className="panel-box">
              <div className="panel-box__head">Link Sites</div>
              <div className="panel-box__body">
                <div className="link-list">
                  <a href="/docs">API documentation</a>
                  <a href="/api/v1/health">Health API</a>
                  <a href="/api/v1/health/dependencies">Dependency health API</a>
                  <a href="/professor">Professor portal</a>
                </div>
              </div>
            </section>
            <section className="panel-box">
              <div className="panel-box__head">Help Desk</div>
              <div className="panel-box__body">
                <div className="helper-list">
                  <div>Support</div>
                  <div>info@iut.uz</div>
                  <div>+998 71 246-05-73</div>
                  <div>Use this shell for operational status, navigation recovery, and safe app preferences.</div>
                </div>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </>
  );
}
