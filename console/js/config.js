/** API base path: local nginx uses /api; production may use /plants/api */
export function getApiBase() {
  const path = window.location.pathname || "";
  if (path.startsWith("/plants")) {
    return "/plants/api";
  }
  return "/api";
}

export const API_BASE = getApiBase();
