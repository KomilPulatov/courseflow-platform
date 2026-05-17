import { request } from "../api.js";
import { useAsyncResource } from "../useAsyncResource.js";

function groupByDay(items) {
  return items.reduce((acc, item) => {
    acc[item.day_of_week] ??= [];
    acc[item.day_of_week].push(item);
    return acc;
  }, {});
}

export function TimetablePage() {
  const { data: items, loading, error, reload } = useAsyncResource(
    () => request("/api/v1/professor/timetable"),
    [],
  );

  if (loading) return <div className="empty-state">Loading timetable...</div>;
  if (error) {
    return (
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor / Timetable</div>
            <h2 className="content-card__title">Teaching Timetable</h2>
          </div>
          <button className="button" type="button" onClick={reload}>
            Retry
          </button>
        </div>
        <div className="empty-state">{error}</div>
      </section>
    );
  }
  if (!items.length) {
    return <div className="empty-state">No timetable entries are available for this professor.</div>;
  }

  const groups = groupByDay(items);

  return (
    <section className="content-card">
      <div className="content-card__header">
        <div>
          <div className="page-kicker">Professor / Timetable</div>
          <h2 className="content-card__title">Teaching Timetable</h2>
          <p className="content-card__subtitle">
            Weekly schedule built from professor-assigned section schedules.
          </p>
        </div>
      </div>
      <div className="stack-lg">
        {Object.entries(groups).map(([day, entries]) => (
          <div key={day} className="panel-box">
            <div className="panel-box__head">{day}</div>
            <div className="panel-box__body">
              <div className="timetable-list">
                {entries.map((entry) => (
                  <article
                    key={`${entry.section_id}-${entry.start_time}-${entry.end_time}`}
                    className="schedule-item"
                  >
                    <div className="section-item__title">
                      {entry.course_code} · {entry.course_title}
                    </div>
                    <div className="meta-row">
                      <span>Section {entry.section_code}</span>
                      <span>
                        {entry.start_time} - {entry.end_time}
                      </span>
                      <span>{entry.room_label || "Room pending"}</span>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
