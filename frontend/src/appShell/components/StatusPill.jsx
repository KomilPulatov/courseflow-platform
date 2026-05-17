function modifierFor(value) {
  const normalized = String(value || "unknown").toLowerCase();
  if (normalized === "ok") return "ok";
  if (normalized.includes("not_configured")) return "not-configured";
  if (normalized.includes("error")) return "error";
  if (normalized === "degraded") return "degraded";
  return "unknown";
}

export function StatusPill({ value }) {
  return <span className={`status-pill status-pill--${modifierFor(value)}`}>{value}</span>;
}
