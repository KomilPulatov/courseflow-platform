import { request } from "../api.js";
import { bootstrapProfessorPage, renderHtml, showEmpty } from "../layout.js";

function groupByDay(items) {
  return items.reduce((acc, item) => {
    acc[item.day_of_week] ??= [];
    acc[item.day_of_week].push(item);
    return acc;
  }, {});
}

async function loadTimetable() {
  const items = await request("/api/v1/professor/timetable");

  if (!items.length) {
    showEmpty("pageContent", "No timetable entries are available for this professor.");
    return;
  }

  const groups = groupByDay(items);
  renderHtml(
    "pageContent",
    `
      <section class="content-card">
        <div class="content-card__header">
          <div>
            <div class="page-kicker">Professor / Timetable</div>
            <h2 class="content-card__title">Teaching Timetable</h2>
            <p class="content-card__subtitle">Weekly schedule built from professor-assigned section schedules.</p>
          </div>
        </div>
        <div class="stack-lg">
          ${Object.entries(groups)
            .map(
              ([day, entries]) => `
                <div class="panel-box">
                  <div class="panel-box__head">${day}</div>
                  <div class="panel-box__body">
                    <div class="timetable-list">
                      ${entries
                        .map(
                          (entry) => `
                            <article class="schedule-item">
                              <div class="section-item__title">${entry.course_code} · ${entry.course_title}</div>
                              <div class="meta-row">
                                <span>Section ${entry.section_code}</span>
                                <span>${entry.start_time} - ${entry.end_time}</span>
                                <span>${entry.room_label || "Room pending"}</span>
                              </div>
                            </article>
                          `,
                        )
                        .join("")}
                    </div>
                  </div>
                </div>
              `,
            )
            .join("")}
        </div>
      </section>
    `,
  );
}

bootstrapProfessorPage(loadTimetable);
