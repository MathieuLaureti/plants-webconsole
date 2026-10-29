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

export async function fetchPlugState() {
  const response = await authFetch(`${API_BASE}/plug/state`);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

export async function setPlugPower(on) {
  const path = on ? "on" : "off";
  const response = await authFetch(`${API_BASE}/plug/${path}`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}
