import { request } from "../api.js";
import { bootstrapProfessorPage, renderHtml } from "../layout.js";
import { sectionIdFromPath } from "../utils.js";

async function saveRoomPreference(sectionId) {
  const roomId = Number(document.getElementById("roomId").value);
  const preferenceRank = Number(document.getElementById("preferenceRank").value);
  const result = await request(`/api/v1/professor/sections/${sectionId}/room-preferences`, {
    method: "POST",
    body: JSON.stringify({
      room_id: roomId,
      preference_rank: preferenceRank,
    }),
  });

  const alert = document.getElementById("pageAlert");
  alert.textContent = result.message;
  alert.className = "inline-alert inline-alert--success";
}

async function loadRoomOptions() {
  const sectionId = sectionIdFromPath();
  const [detail, options] = await Promise.all([
    request(`/api/v1/professor/sections/${sectionId}`),
    request(`/api/v1/professor/sections/${sectionId}/room-options`),
  ]);

  renderHtml(
    "pageContent",
    `
      <div class="stack-lg">
        <section class="content-card">
          <div class="content-card__header">
            <div>
              <div class="page-kicker">Professor / Room Options</div>
              <h2 class="content-card__title">${detail.course_code} · Room Pool</h2>
              <p class="content-card__subtitle">
                Choose a room for section ${detail.section_code}. Only allocated rooms are shown below.
              </p>
            </div>
          </div>
          <div class="meta-row">
            <span>Section ${detail.section_code}</span>
            <span>Capacity ${detail.capacity}</span>
            <span>${detail.room_selection_mode}</span>
            <span>${detail.status}</span>
          </div>
        </section>

        <section class="content-card">
          <div class="content-card__header">
            <div>
              <h3>Available Options</h3>
              <p class="content-card__subtitle">The list below comes from the admin room allocation pool.</p>
            </div>
          </div>
          <div class="option-list">
            ${options.options
              .map(
                (option) => `
                  <article class="option-item">
                    <div class="option-item__title">${option.building || ""}${option.building ? "-" : ""}${option.room_number}</div>
                    <div class="meta-row">
                      <span>Room ID ${option.room_id}</span>
                      <span>Capacity ${option.capacity}</span>
                      <span>${option.room_type}</span>
                    </div>
                  </article>
                `,
              )
              .join("")}
          </div>
        </section>

        <section class="content-card">
          <div class="content-card__header">
            <div>
              <h3>Submit Preference</h3>
              <p class="content-card__subtitle">Save the preferred room for this section.</p>
            </div>
          </div>
          <form id="roomPreferenceForm" class="form-grid">
            <input id="roomId" type="number" min="1" placeholder="Room ID" required />
            <input id="preferenceRank" type="number" min="1" value="1" required />
            <button class="button" type="submit">Save room preference</button>
          </form>
        </section>
      </div>
    `,
  );

  document.getElementById("roomPreferenceForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await saveRoomPreference(sectionId);
    } catch (error) {
      const alert = document.getElementById("pageAlert");
      alert.textContent = error.message;
      alert.className = "inline-alert inline-alert--error";
    }
  });
}

bootstrapProfessorPage(loadRoomOptions);
