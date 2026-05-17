import { request } from "../api.js";
import { bootstrapProfessorPage, renderHtml } from "../layout.js";
import { sectionIdFromPath } from "../utils.js";

async function loadSectionDetail() {
  const sectionId = sectionIdFromPath();
  const detail = await request(`/api/v1/professor/sections/${sectionId}`);

  renderHtml(
    "pageContent",
    `
      <div class="stack-lg">
        <section class="content-card">
          <div class="content-card__header">
            <div>
              <div class="page-kicker">Professor / Sections / ${detail.section_id}</div>
              <h2 class="content-card__title">${detail.course_code} · ${detail.course_title}</h2>
              <p class="content-card__subtitle">
                Section ${detail.section_code} for ${detail.semester_name || "current semester"}.
              </p>
            </div>
          </div>
          <div class="detail-grid">
            <div class="panel-box">
              <div class="panel-box__head">Section Summary</div>
              <div class="panel-box__body">
                <div class="detail-list">
                  <div class="detail-list__row"><span class="detail-list__label">Section ID</span><span class="detail-list__value">${detail.section_id}</span></div>
                  <div class="detail-list__row"><span class="detail-list__label">Offering ID</span><span class="detail-list__value">${detail.course_offering_id}</span></div>
                  <div class="detail-list__row"><span class="detail-list__label">Capacity</span><span class="detail-list__value">${detail.capacity}</span></div>
                  <div class="detail-list__row"><span class="detail-list__label">Room mode</span><span class="detail-list__value">${detail.room_selection_mode}</span></div>
                  <div class="detail-list__row"><span class="detail-list__label">Current room</span><span class="detail-list__value">${detail.current_room || "Not assigned"}</span></div>
                  <div class="detail-list__row"><span class="detail-list__label">Status</span><span class="detail-list__value">${detail.status}</span></div>
                </div>
              </div>
            </div>
            <div class="panel-box">
              <div class="panel-box__head">Actions</div>
              <div class="panel-box__body stack-md">
                <a class="mini-button" href="/professor/sections/${detail.section_id}/room-options">Open room options</a>
                <a class="mini-button" href="/professor/sections">Back to my sections</a>
              </div>
            </div>
          </div>
        </section>
        <section class="content-card">
          <div class="content-card__header">
            <div>
              <h3>Schedule</h3>
              <p class="content-card__subtitle">Current day and time allocations for this section.</p>
            </div>
          </div>
          <div class="timetable-list">
            ${detail.schedules
              .map(
                (slot) => `
                  <article class="schedule-item">
                    <div class="section-item__title">${slot.day_of_week}</div>
                    <div class="meta-row">
                      <span>${slot.start_time} - ${slot.end_time}</span>
                      <span>${slot.room_label || "Room pending"}</span>
                    </div>
                  </article>
                `,
              )
              .join("")}
          </div>
        </section>
      </div>
    `,
  );
}

bootstrapProfessorPage(loadSectionDetail);
