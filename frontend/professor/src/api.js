const TOKEN_KEY = "crspProfessorToken";

export function getProfessorToken() {
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

export function setProfessorToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearProfessorToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function request(path, options = {}) {
  const headers = new Headers(options.headers ?? {});
  const token = getProfessorToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(path, { ...options, headers });
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    const message =
      typeof data === "string" ? data : data.detail ?? data.message ?? JSON.stringify(data);
    throw new Error(message);
  }

  return data;
}

export function loginProfessor(email, password) {
  return request("/api/v1/auth/professor/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}
