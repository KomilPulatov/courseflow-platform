const KEY = "crspAppPreferences";

const defaults = {
  preferredLanding: "/professor",
  healthAutoRefreshSeconds: 30,
  showStatusHints: true,
};

export function getPreferences() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return { ...defaults };
    return { ...defaults, ...JSON.parse(raw) };
  } catch {
    return { ...defaults };
  }
}

export function savePreferences(next) {
  const merged = { ...defaults, ...next };
  localStorage.setItem(KEY, JSON.stringify(merged));
  return merged;
}
