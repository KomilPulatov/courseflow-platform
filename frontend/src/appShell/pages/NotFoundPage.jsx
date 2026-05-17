import { useMemo } from "react";
import { Link, useLocation } from "react-router-dom";

import { getPreferences } from "../preferences.js";

function useMissingTarget() {
  const location = useLocation();
  return useMemo(() => {
    const params = new URLSearchParams(location.search);
    return params.get("path") || params.get("from") || "Unknown route";
  }, [location.search]);
}

export function NotFoundPage() {
  const target = useMissingTarget();
  const preferences = getPreferences();

  return (
    <div className="stack-lg">
      <section className="content-card content-card--hero">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Shared App Utility</div>
            <h2 className="content-card__title">Route Not Found</h2>
            <p className="content-card__subtitle">
              The requested application page could not be resolved. Use the recovery shortcuts below to continue.
            </p>
          </div>
        </div>
        <div className="stat-strip">
          <article className="stat-tile">
            <div className="stat-tile__label">Missing target</div>
            <div className="stat-tile__value mono">{target}</div>
          </article>
          <article className="stat-tile">
            <div className="stat-tile__label">Recommended landing</div>
            <div className="stat-tile__value mono">{preferences.preferredLanding}</div>
          </article>
          <article className="stat-tile">
            <div className="stat-tile__label">Documentation</div>
            <div className="stat-tile__value mono">/docs</div>
          </article>
        </div>
      </section>

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Recovery actions</div>
            <h3>Choose a Valid Destination</h3>
          </div>
        </div>
        <div className="quick-links">
          <a className="quick-link" href={preferences.preferredLanding}>
            <div className="quick-link__title">Open preferred landing</div>
            <div className="quick-link__hint">Resume from your saved entry point.</div>
          </a>
          <Link className="quick-link" to="/health">
            <div className="quick-link__title">Check application health</div>
            <div className="quick-link__hint">Verify whether the system itself is healthy.</div>
          </Link>
          <a className="quick-link" href="/docs">
            <div className="quick-link__title">Open API docs</div>
            <div className="quick-link__hint">Inspect available backend routes.</div>
          </a>
        </div>
      </section>
    </div>
  );
}
