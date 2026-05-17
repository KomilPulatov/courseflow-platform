import { clearProfessorToken, getProfessorToken, loginProfessor, request, setProfessorToken } from "./api.js";

export async function restoreProfessorSession() {
  const token = getProfessorToken();
  if (!token) return null;

  try {
    return await request("/api/v1/professor/me");
  } catch {
    clearProfessorToken();
    return null;
  }
}

export async function signInProfessor(email, password) {
  const result = await loginProfessor(email, password);
  setProfessorToken(result.access_token);
  return request("/api/v1/professor/me");
}

export function signOutProfessor() {
  clearProfessorToken();
}
