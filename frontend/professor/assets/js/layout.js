import {
  clearProfessorToken,
  getProfessorToken,
  loginProfessor,
  request,
  setProfessorToken,
} from "./api.js";

function setAlert(message, type = "success") {
  const alert = document.getElementById("pageAlert");
  if (!alert) return;
  if (!message) {
    alert.textContent = "";
    alert.className = "inline-alert is-hidden";
    return;
  }
  alert.textContent = message;
  alert.className = `inline-alert inline-alert--${type}`;
}

function showLoginCard(show) {
  const card = document.getElementById("loginCard");
  if (!card) return;
  card.classList.toggle("is-hidden", !show);
}

function setAuthenticatedShell(isAuthenticated) {
  document.body.classList.toggle("is-authenticated", isAuthenticated);
  document.body.classList.toggle("is-unauthenticated", !isAuthenticated);

  const logoutButton = document.getElementById("logoutButton");
  if (logoutButton) {
    logoutButton.hidden = !isAuthenticated;
  }

  const timetableLink = document.getElementById("headerTimetableLink");
  if (timetableLink) {
    timetableLink.hidden = !isAuthenticated;
  }

  const headerDivider = document.getElementById("headerLinksDivider");
  if (headerDivider) {
    headerDivider.hidden = !isAuthenticated;
  }
}

function setProfessorProfile(profile) {
  const school = document.getElementById("sidebarSchool");
  const name = document.getElementById("sidebarProfessorName");
  const meta = document.getElementById("sidebarProfileMeta");
  const hint = document.getElementById("sidebarSessionHint");

  if (!school || !name || !meta || !hint) return;

  if (!profile) {
    school.textContent = "Professor Portal";
    name.textContent = "Professor Session Required";
    meta.textContent = "";
    hint.textContent =
      "Sign in to load your department, assigned sections, room options, and timetable.";
    return;
  }

  school.textContent = profile.department_name || "Inha University in Tashkent";
  name.textContent = profile.full_name;
  meta.textContent = profile.email || "";
  hint.textContent = "Authenticated professor workspace";
}

function renderSignedOutState() {
  const content = document.getElementById("pageContent");
  const page = document.querySelector(".portal-main");
  if (!content || !page) return;

  const heading = page.getAttribute("data-page-heading") || "Professor workspace";
  const description =
    page.getAttribute("data-page-description") ||
    "Sign in to load professor-specific data and navigation.";

  content.innerHTML = `
    <section class="content-card content-card--hero">
      <div class="content-card__header">
        <div>
          <div class="page-kicker">Inha University in Tashkent</div>
          <h2 class="content-card__title">${heading}</h2>
          <p class="content-card__subtitle">${description}</p>
        </div>
      </div>
      <div class="stat-strip">
        <article class="stat-tile">
          <div class="stat-tile__label">Session</div>
          <div class="stat-tile__value stat-tile__value--compact">Sign in required</div>
        </article>
        <article class="stat-tile">
          <div class="stat-tile__label">Access after sign in</div>
          <div class="stat-tile__value stat-tile__value--compact">Sections and room pool</div>
        </article>
        <article class="stat-tile">
          <div class="stat-tile__label">Data source</div>
          <div class="stat-tile__value stat-tile__value--compact">Assigned professor records</div>
        </article>
      </div>
    </section>
  `;
}

async function authenticateAndLoad(loadPage) {
  const token = getProfessorToken();
  if (!token) {
    setAuthenticatedShell(false);
    showLoginCard(true);
    setProfessorProfile(null);
    renderSignedOutState();
    return;
  }

  try {
    const profile = await request("/api/v1/professor/me");
    setAuthenticatedShell(true);
    showLoginCard(false);
    setProfessorProfile(profile);
    await loadPage(profile);
  } catch (error) {
    clearProfessorToken();
    setAuthenticatedShell(false);
    showLoginCard(true);
    setProfessorProfile(null);
    renderSignedOutState();
    setAlert(error.message, "error");
  }
}

function bindLogin(loadPage) {
  const form = document.getElementById("professorLoginForm");
  if (!form) return;
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(form);
  try {
      const result = await loginProfessor(
        String(formData.get("email") ?? ""),
        String(formData.get("password") ?? ""),
      );
      setProfessorToken(result.access_token);
      setAlert("");
      await authenticateAndLoad(loadPage);
    } catch (error) {
      setAlert(error.message, "error");
    }
  });
}

function bindLogout() {
  const logout = document.getElementById("logoutButton");
  if (!logout) return;
  logout.addEventListener("click", () => {
    clearProfessorToken();
    window.location.href = "/professor";
  });
}

export function renderAsideStatic() {
  const links = document.getElementById("linkSites");
  const help = document.getElementById("helpDesk");
  if (links) {
    links.innerHTML = `
      <ul class="link-list">
        <li><a href="https://inha.uz/" target="_blank" rel="noreferrer">Inha University in Tashkent</a></li>
        <li><a href="https://www.inha.ac.kr/" target="_blank" rel="noreferrer">Inha University in Korea</a></li>
        <li><a href="https://class.inha.uz/" target="_blank" rel="noreferrer">e-Class</a></li>
        <li><a href="mailto:info@iut.uz">e-mail</a></li>
      </ul>
    `;
  }
  if (help) {
    help.innerHTML = `
      <div class="stack-sm">
        <div>Contact</div>
        <div>- +998 71 246-05-73</div>
        <div>- +998 71 238-65-62</div>
        <div>e-mail</div>
        <div>- info@iut.uz</div>
      </div>
    `;
  }
}

export async function bootstrapProfessorPage(loadPage) {
  renderAsideStatic();
  bindLogin(loadPage);
  bindLogout();
  await authenticateAndLoad(loadPage);
}

export function showEmpty(targetId, message) {
  const node = document.getElementById(targetId);
  if (!node) return;
  node.innerHTML = `<div class="empty-state">${message}</div>`;
}

export function renderHtml(targetId, html) {
  const node = document.getElementById(targetId);
  if (!node) return;
  node.innerHTML = html;
}
