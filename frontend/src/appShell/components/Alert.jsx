export function Alert({ message, type = "success" }) {
  if (!message) return null;
  return <div className={`inline-alert inline-alert--${type}`}>{message}</div>;
}
