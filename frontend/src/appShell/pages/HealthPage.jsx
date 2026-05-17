import { useEffect, useMemo, useState } from "react";

import { request } from "../api.js";
import { Alert } from "../components/Alert.jsx";
import { StatusPill } from "../components/StatusPill.jsx";
import { getPreferences } from "../preferences.js";

export function HealthPage() {
  const [appSettings, setAppSettings] = useState(null);
  const [health, setHealth] = useState(null);
  const [dependencyHealth, setDependencyHealth] = useState(null);
  const [error, setError] = useState("");
  const [checkedAt, setCheckedAt] = useState(null);

  const prefs = useMemo(() => getPreferences(), []);

  async function loadData() {
    try {
      setError("");
      const [settings, healthData, dependencyData] = await Promise.all([
        request("/api/v1/app/settings"),
        request("/api/v1/health"),
        request("/api/v1/health/dependencies"),
      ]);
      setAppSettings(settings);
      setHealth(healthData);
      setDependencyHealth(dependencyData);
      setCheckedAt(new Date());
    } catch (loadError) {
      setError(loadError.message);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (prefs.healthAutoRefreshSeconds <= 0) return undefined;
    const interval = window.setInterval(loadData, prefs.healthAutoRefreshSeconds * 1000);
    return () => window.clearInterval(interval);
  }, [prefs.healthAutoRefreshSeconds]);

  const checks = dependencyHealth?.checks ?? {};

  return (
    <div className="stack-lg">
      <Alert message={error} type="error" />

      <section className="content-card content-card--hero">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Shared App Utility</div>
            <h2 className="content-card__title">Application Health</h2>
            <p className="content-card__subtitle">
              Real-time status surface for backend availability, dependency checks, and operational quick links.
            </p>
          </div>
          <div className="toolbar">
            <button className="button" type="button" onClick={loadData}>
              Refresh
            </button>
            <a className="ghost-button" href="/docs">
              Open Docs
            </a>
          </div>
        </div>
        <div className="stat-strip">
          <article className="stat-tile">
            <div className="stat-tile__label">Overall API</div>
            <div className="stat-tile__value">{health?.status ?? "Loading"}</div>
          </article>
          <article className="stat-tile">
            <div className="stat-tile__label">Dependency state</div>
            <div className="stat-tile__value">{dependencyHealth?.status ?? "Loading"}</div>
          </article>
          <article className="stat-tile">
            <div className="stat-tile__label">Last checked</div>
            <div className="stat-tile__value">
              {checkedAt ? checkedAt.toLocaleTimeString() : "Pending"}
            </div>
          </article>
        </div>
      </section>

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Backend checks</div>
            <h3>Dependency Status</h3>
            <p className="content-card__subtitle">
              Source endpoints: <span className="mono">{appSettings?.health_url ?? "/api/v1/health"}</span> and{" "}
              <span className="mono">
                {appSettings?.dependency_health_url ?? "/api/v1/health/dependencies"}
              </span>.
            </p>
          </div>
        </div>
        <div className="status-grid">
          <article className="status-tile">
            <div className="status-tile__label">API status</div>
            <div><StatusPill value={health?.status ?? "unknown"} /></div>
            {prefs.showStatusHints ? (
              <div className="status-tile__hint">Simple readiness check for the application service.</div>
            ) : null}
          </article>
          {Object.entries(checks).map(([name, value]) => (
            <article key={name} className="status-tile">
              <div className="status-tile__label">{name}</div>
              <div><StatusPill value={String(value)} /></div>
              {prefs.showStatusHints ? (
                <div className="status-tile__hint">{name} dependency status reported by the backend.</div>
              ) : null}
            </article>
          ))}
        </div>
      </section>

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Operational context</div>
            <h3>Environment Summary</h3>
          </div>
        </div>
        <div className="detail-grid">
          <article className="detail-card">
            <div className="detail-card__label">Environment</div>
            <div className="detail-card__value">{appSettings?.environment ?? "Loading"}</div>
            <div className="detail-card__hint">Public-safe environment identifier exposed by the backend.</div>
          </article>
          <article className="detail-card">
            <div className="detail-card__label">Database backend</div>
            <div className="detail-card__value">{appSettings?.database_backend ?? "Loading"}</div>
            <div className="detail-card__hint">Useful for local debugging and deployment validation.</div>
          </article>
          <article className="detail-card">
            <div className="detail-card__label">Observability</div>
            <div className="detail-card__value">
              {appSettings ? (appSettings.observability_enabled ? "Enabled" : "Disabled") : "Loading"}
            </div>
            <div className="detail-card__hint">Shows whether OTEL export is configured, not the endpoint secret itself.</div>
          </article>
          <article className="detail-card">
            <div className="detail-card__label">Portal origin</div>
            <div className="detail-card__value mono">{appSettings?.portal_origin ?? "Loading"}</div>
            <div className="detail-card__hint">The public INS connector origin used by sync flows.</div>
          </article>
        </div>
      </section>
    </div>
  );
}
