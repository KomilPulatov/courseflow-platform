import { request } from "../api.js";
import { bootstrapProfessorPage, renderHtml, showEmpty } from "../layout.js";

async function loadDashboard(profile) {
  const sections = await request("/api/v1/professor/sections");
  const timetable = await request("/api/v1/professor/timetable");

  if (!sections.length) {
    showEmpty("pageContent", "No sections are currently assigned to this professor.");
    return;
  }

  renderHtml(
    "pageContent",
    `
      <div class="stack-lg">
        <section class="content-card">
          <div class="content-card__header">
            <div>
              <div class="page-kicker">Professor portal</div>
              <h2 class="content-card__title"><span class="accent">INS</span> Professor Dashboard</h2>
              <p class="content-card__subtitle">
                Welcome, ${profile.full_name}. This page mirrors the INS-style professor workspace and
                gives direct access to sections, room selection, and teaching timetable.
              </p>
            </div>
          </div>
          <div class="stat-strip">
            <article class="stat-tile">
              <div class="stat-tile__label">Assigned sections</div>
              <div class="stat-tile__value">${sections.length}</div>
            </article>
            <article class="stat-tile">
              <div class="stat-tile__label">Weekly schedule rows</div>
              <div class="stat-tile__value">${timetable.length}</div>
            </article>
            <article class="stat-tile">
              <div class="stat-tile__label">Department</div>
              <div class="stat-tile__value">${profile.department_name || "IUT"}</div>
            </article>
          </div>
        </section>
        <section class="content-card">
          <div class="content-card__header">
            <div>
              <h3>Assigned Sections</h3>
              <p class="content-card__subtitle">Open a section to inspect schedule and room pool.</p>
            </div>
          </div>
          <div class="section-list">
            ${sections
              .map(
                (section) => `
                  <article class="section-item">
                    <div class="section-item__title">${section.course_code} · ${section.course_title}</div>
                    <div class="meta-row">
                      <span>Section ${section.section_code}</span>
                      <span>Capacity ${section.capacity}</span>
                      <span>${section.room_selection_mode}</span>
                      <span>${section.status}</span>
                    </div>
                    <div class="section-item__actions">
                      <a class="mini-button" href="/professor/sections/${section.section_id}">Open detail</a>
                      <a class="mini-button" href="/professor/sections/${section.section_id}/room-options">Room options</a>
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

bootstrapProfessorPage(loadDashboard);
