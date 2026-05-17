export function formatRoomLabel(option) {
  if (typeof option === "string") {
    return option;
  }
  if (!option) {
    return "Not assigned";
  }
  return option.building ? `${option.building}-${option.room_number}` : option.room_number;
}

export function sectionIdFromPath() {
  const match = window.location.pathname.match(/\/professor\/sections\/(\d+)/);
  return match ? Number(match[1]) : null;
}

export function setText(id, value) {
  const node = document.getElementById(id);
  if (node) {
    node.textContent = value;
  }
}
