import { Link, useParams } from "react-router-dom";

import { request } from "../api.js";
import { useAsyncResource } from "../useAsyncResource.js";

export function SectionDetailPage() {
  const { sectionId } = useParams();
  const { data: detail, loading, error, reload } = useAsyncResource(
    () => request(`/api/v1/professor/sections/${sectionId}`),
    [sectionId],
  );

  if (loading) return <div className="empty-state">Loading section detail...</div>;
  if (error) {
    return (
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor / Sections / {sectionId}</div>
            <h2 className="content-card__title">Section Detail</h2>
          </div>
          <button className="button" type="button" onClick={reload}>
            Retry
          </button>
        </div>
        <div className="empty-state">{error}</div>
      </section>
    );
  }

  return (
    <div className="stack-lg">
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor / Sections / {detail.section_id}</div>
            <h2 className="content-card__title">
              {detail.course_code} · {detail.course_title}
            </h2>
            <p className="content-card__subtitle">
              Section {detail.section_code} for {detail.semester_name || "current semester"}.
            </p>
          </div>
        </div>
        <div className="detail-grid">
          <div className="panel-box">
            <div className="panel-box__head">Section Summary</div>
            <div className="panel-box__body">
              <div className="detail-list">
                <div className="detail-list__row"><span className="detail-list__label">Section ID</span><span className="detail-list__value">{detail.section_id}</span></div>
                <div className="detail-list__row"><span className="detail-list__label">Offering ID</span><span className="detail-list__value">{detail.course_offering_id}</span></div>
                <div className="detail-list__row"><span className="detail-list__label">Capacity</span><span className="detail-list__value">{detail.capacity}</span></div>
                <div className="detail-list__row"><span className="detail-list__label">Room mode</span><span className="detail-list__value">{detail.room_selection_mode}</span></div>
                <div className="detail-list__row"><span className="detail-list__label">Current room</span><span className="detail-list__value">{detail.current_room || "Not assigned"}</span></div>
                <div className="detail-list__row"><span className="detail-list__label">Status</span><span className="detail-list__value">{detail.status}</span></div>
              </div>
            </div>
          </div>
          <div className="panel-box">
            <div className="panel-box__head">Actions</div>
            <div className="panel-box__body stack-md">
              <Link className="mini-button" to={`/sections/${detail.section_id}/room-options`}>
                Open room options
              </Link>
              <Link className="mini-button" to="/sections">
                Back to my sections
              </Link>
            </div>
          </div>
        </div>
      </section>
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <h3>Schedule</h3>
            <p className="content-card__subtitle">Current day and time allocations for this section.</p>
          </div>
        </div>
        <div className="timetable-list">
          {detail.schedules.map((slot, index) => (
            <article key={`${slot.day_of_week}-${slot.start_time}-${index}`} className="schedule-item">
              <div className="section-item__title">{slot.day_of_week}</div>
              <div className="meta-row">
                <span>
                  {slot.start_time} - {slot.end_time}
                </span>
                <span>{slot.room_label || "Room pending"}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
