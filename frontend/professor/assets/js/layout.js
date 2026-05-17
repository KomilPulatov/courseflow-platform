import {
  clearProfessorToken,
  getProfessorToken,
  loginProfessor,
  request,
  setProfessorToken,
} from "./api.js";
import { setText } from "./utils.js";

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

function setProfessorProfile(profile) {
  setText(
    "sidebarSchool",
    profile?.department_name || "School of Computer and Information Engineering",
  );
  setText("sidebarProfessorName", profile?.full_name || "Professor session required");
}

async function authenticateAndLoad(loadPage) {
  const token = getProfessorToken();
  if (!token) {
    showLoginCard(true);
    setProfessorProfile(null);
    return;
  }

  try {
    const profile = await request("/api/v1/professor/me");
    showLoginCard(false);
    setProfessorProfile(profile);
    await loadPage(profile);
  } catch (error) {
    clearProfessorToken();
    showLoginCard(true);
    setProfessorProfile(null);
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
      setAlert("Professor session started.");
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
