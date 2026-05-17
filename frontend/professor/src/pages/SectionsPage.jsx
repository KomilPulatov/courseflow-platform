import { Link } from "react-router-dom";

import { request } from "../api.js";
import { useAsyncResource } from "../useAsyncResource.js";

export function SectionsPage() {
  const { data: sections, loading, error, reload } = useAsyncResource(
    () => request("/api/v1/professor/sections"),
    [],
  );

  if (loading) return <div className="empty-state">Loading assigned sections...</div>;
  if (error) {
    return (
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor / Sections</div>
            <h2 className="content-card__title">My Sections</h2>
          </div>
          <button className="button" type="button" onClick={reload}>
            Retry
          </button>
        </div>
        <div className="empty-state">{error}</div>
      </section>
    );
  }
  if (!sections.length) return <div className="empty-state">No assigned sections were found.</div>;

  return (
    <section className="content-card">
      <div className="content-card__header">
        <div>
          <div className="page-kicker">Professor / Sections</div>
          <h2 className="content-card__title">My Sections</h2>
          <p className="content-card__subtitle">
            Select a section to inspect its academic and room context.
          </p>
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
              <span>Mode {section.room_selection_mode}</span>
              <span>Status {section.status}</span>
            </div>
            <div className="section-item__actions">
              <Link className="mini-button" to={`/sections/${section.section_id}`}>
                Section detail
              </Link>
              <Link className="mini-button" to={`/sections/${section.section_id}/room-options`}>
                Room options
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
