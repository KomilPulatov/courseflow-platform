import { useEffect, useState } from "react";

import { request } from "../api.js";
import { Alert } from "../components/Alert.jsx";
import { getPreferences, savePreferences } from "../preferences.js";

export function SettingsPage() {
  const [appSettings, setAppSettings] = useState(null);
  const [preferences, setPreferences] = useState(getPreferences());
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    request("/api/v1/app/settings")
      .then(setAppSettings)
      .catch((loadError) => setError(loadError.message));
  }, []);

  function onSubmit(event) {
    event.preventDefault();
    const next = savePreferences(preferences);
    setPreferences(next);
    setError("");
    setMessage(`Preferences saved. Preferred landing is now ${next.preferredLanding}.`);
  }

  return (
    <div className="stack-lg">
      <Alert message={message} type="success" />
      <Alert message={error} type="error" />

      <section className="content-card content-card--hero">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Shared App Utility</div>
            <h2 className="content-card__title">Application Settings</h2>
            <p className="content-card__subtitle">
              Safe public runtime metadata plus client-side utility preferences for the local portal shell.
            </p>
          </div>
        </div>
        <div className="stat-strip">
          <article className="stat-tile">
            <div className="stat-tile__label">Application</div>
            <div className="stat-tile__value">{appSettings?.app_name ?? "Loading"}</div>
          </article>
          <article className="stat-tile">
            <div className="stat-tile__label">Version</div>
            <div className="stat-tile__value">{appSettings?.version ?? "Loading"}</div>
          </article>
          <article className="stat-tile">
            <div className="stat-tile__label">Environment</div>
            <div className="stat-tile__value">{appSettings?.environment ?? "Loading"}</div>
          </article>
        </div>
      </section>

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Public backend settings</div>
            <h3>Runtime Metadata</h3>
          </div>
        </div>
        <div className="settings-grid">
          <article className="detail-card">
            <div className="detail-card__label">Docs URL</div>
            <div className="detail-card__value mono">{appSettings?.docs_url ?? "Loading"}</div>
            <div className="detail-card__hint">Primary operator-facing API reference.</div>
          </article>
          <article className="detail-card">
            <div className="detail-card__label">OpenAPI URL</div>
            <div className="detail-card__value mono">{appSettings?.openapi_url ?? "Loading"}</div>
            <div className="detail-card__hint">Machine-readable contract surface.</div>
          </article>
          <article className="detail-card">
            <div className="detail-card__label">Default professor landing</div>
            <div className="detail-card__value mono">
              {appSettings?.default_professor_landing ?? "Loading"}
            </div>
            <div className="detail-card__hint">Role-specific portal entry point.</div>
          </article>
          <article className="detail-card">
            <div className="detail-card__label">Support</div>
            <div className="detail-card__value">{appSettings?.support_phone ?? "Loading"}</div>
            <div className="detail-card__hint">{appSettings?.support_email ?? "Loading"}</div>
          </article>
        </div>
      </section>

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Client preferences</div>
            <h3>Local Utility Preferences</h3>
            <p className="content-card__subtitle">
              Stored in your browser only. These do not change backend configuration.
            </p>
          </div>
        </div>
        <form className="form-grid" onSubmit={onSubmit}>
          <div className="field">
            <label htmlFor="preferredLanding">Preferred landing page</label>
            <select
              id="preferredLanding"
              value={preferences.preferredLanding}
              onChange={(event) =>
                setPreferences((current) => ({ ...current, preferredLanding: event.target.value }))
              }
            >
              <option value="/professor">Professor portal</option>
              <option value="/app/health">App health</option>
              <option value="/app/settings">App settings</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="healthAutoRefreshSeconds">Health auto-refresh interval</label>
            <select
              id="healthAutoRefreshSeconds"
              value={String(preferences.healthAutoRefreshSeconds)}
              onChange={(event) =>
                setPreferences((current) => ({
                  ...current,
                  healthAutoRefreshSeconds: Number(event.target.value),
                }))
              }
            >
              <option value="0">Off</option>
              <option value="15">15 seconds</option>
              <option value="30">30 seconds</option>
              <option value="60">60 seconds</option>
            </select>
          </div>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={preferences.showStatusHints}
              onChange={(event) =>
                setPreferences((current) => ({ ...current, showStatusHints: event.target.checked }))
              }
            />
            <span>Show explanatory hints on status pages</span>
          </label>
          <div className="toolbar">
            <button className="button" type="submit">
              Save preferences
            </button>
            <a className="secondary-button" href={preferences.preferredLanding}>
              Open preferred landing
            </a>
          </div>
        </form>
      </section>
    </div>
  );
}
