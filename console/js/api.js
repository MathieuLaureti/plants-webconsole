import { API_BASE } from "./config.js";
import { authFetch } from "./auth.js";

export async function fetchSensorHistory() {
  const response = await authFetch(`${API_BASE}/get_THs`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchLastImage(offset, cameraId) {
  const response = await authFetch(
    `${API_BASE}/get_last_image/${offset}/${cameraId}`
  );
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

export async function fetchTimelapse(cameraId, limit) {
  const response = await authFetch(
    `${API_BASE}/generate-timelapse/${cameraId}/${limit}`
  );
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.blob();
}

async function parseError(response) {
  const detail = await response.json().catch(() => ({}));
  const msg = detail.detail;
  if (typeof msg === "string") {
    return msg;
  }
  if (Array.isArray(msg)) {
    return msg.map((e) => e.msg || String(e)).join("; ");
  }
  return `HTTP ${response.status}`;
}

export async function listPlugs() {
  const response = await authFetch(`${API_BASE}/plugs`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function createPlug(payload) {
  const response = await authFetch(`${API_BASE}/plugs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function updatePlug(id, payload) {
  const response = await authFetch(`${API_BASE}/plugs/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function setPlugScheduleEnabled(id, enabled) {
  const response = await authFetch(`${API_BASE}/plugs/${id}/schedule/enabled`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}

export async function fetchPlugRuntime(id) {
  const response = await authFetch(`${API_BASE}/plugs/${id}/runtime`);
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return response.json();
}
