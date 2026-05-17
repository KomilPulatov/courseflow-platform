import { request } from "../api.js";
import { bootstrapProfessorPage, renderHtml, showEmpty } from "../layout.js";

async function loadSections() {
  const sections = await request("/api/v1/professor/sections");

  if (!sections.length) {
    showEmpty("pageContent", "No assigned sections were found.");
    return;
  }

  renderHtml(
    "pageContent",
    `
      <section class="content-card">
        <div class="content-card__header">
          <div>
            <div class="page-kicker">Professor / Sections</div>
            <h2 class="content-card__title">My Sections</h2>
            <p class="content-card__subtitle">Select a section to inspect its academic and room context.</p>
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
                    <span>Mode ${section.room_selection_mode}</span>
                    <span>Status ${section.status}</span>
                  </div>
                  <div class="section-item__actions">
                    <a class="mini-button" href="/professor/sections/${section.section_id}">Section detail</a>
                    <a class="mini-button" href="/professor/sections/${section.section_id}/room-options">Room options</a>
                  </div>
                </article>
              `,
            )
            .join("")}
        </div>
      </section>
    `,
  );
}

bootstrapProfessorPage(loadSections);
