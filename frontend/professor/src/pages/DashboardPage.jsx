import { Link } from "react-router-dom";

import { request } from "../api.js";
import { useAsyncResource } from "../useAsyncResource.js";

export function DashboardPage() {
  const { data, loading, error, reload } = useAsyncResource(async () => {
    const [sections, timetable] = await Promise.all([
      request("/api/v1/professor/sections"),
      request("/api/v1/professor/timetable"),
    ]);
    return { sections, timetable };
  }, []);

  if (loading) {
    return <div className="empty-state">Loading professor workspace...</div>;
  }

  if (error) {
    return (
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor portal</div>
            <h2 className="content-card__title">Professor Dashboard</h2>
          </div>
          <button className="button" type="button" onClick={reload}>
            Retry
          </button>
        </div>
        <div className="empty-state">{error}</div>
      </section>
    );
  }

  const { sections, timetable } = data;

  if (!sections.length) {
    return (
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor portal</div>
            <h2 className="content-card__title">Professor Dashboard</h2>
            <p className="content-card__subtitle">
              No sections are currently assigned to this professor.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <div className="stack-lg">
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor portal</div>
            <h2 className="content-card__title">
              <span className="accent">INS</span> Professor Dashboard
            </h2>
            <p className="content-card__subtitle">
              Direct access to sections, room selection, and teaching timetable.
            </p>
          </div>
        </div>
        <div className="stat-strip">
          <article className="stat-tile">
            <div className="stat-tile__label">Assigned sections</div>
            <div className="stat-tile__value">{sections.length}</div>
          </article>
          <article className="stat-tile">
            <div className="stat-tile__label">Weekly schedule rows</div>
            <div className="stat-tile__value">{timetable.length}</div>
          </article>
          <article className="stat-tile">
            <div className="stat-tile__label">Navigation</div>
            <div className="stat-tile__value stat-tile__value--compact">Sections and timetable</div>
          </article>
        </div>
      </section>

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <h3>Assigned Sections</h3>
            <p className="content-card__subtitle">Open a section to inspect schedule and room pool.</p>
          </div>
        </div>
        <div className="section-list">
          {sections.map((section) => (
            <article key={section.section_id} className="section-item">
              <div className="section-item__title">
                {section.course_code} · {section.course_title}
              </div>
              <div className="meta-row">
                <span>Section {section.section_code}</span>
                <span>Capacity {section.capacity}</span>
                <span>{section.room_selection_mode}</span>
                <span>{section.status}</span>
              </div>
              <div className="section-item__actions">
                <Link className="mini-button" to={`/sections/${section.section_id}`}>
                  Open detail
                </Link>
                <Link className="mini-button" to={`/sections/${section.section_id}/room-options`}>
                  Room options
                </Link>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
