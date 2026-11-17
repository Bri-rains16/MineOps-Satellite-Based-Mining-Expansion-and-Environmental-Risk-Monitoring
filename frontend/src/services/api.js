const BASE_URL = import.meta.env.VITE_API_URL || '';

async function fetchJson(endpoint) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url);
  if (!response.ok) {
    let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const errData = await response.json();
      if (errData && errData.error) errorMsg = errData.error;
    } catch (_) {}
    throw new Error(errorMsg);
  }
  return response.json();
}

export const api = {
  getHealth: () => fetchJson('/api/health'),
  getOverview: (year = 2026) => fetchJson(`/api/overview?year=${year}`),
  getRf: (year) => fetchJson(`/api/rf/${year}`),
  getUnet: (year) => fetchJson(`/api/unet/${year}`),
  getProximity: (year) => fetchJson(`/api/proximity/${year}`),
  getDownloadUrl: (relativePath) => `${BASE_URL}/api/download/${relativePath.replace(/\\/g, '/')}`
};

export default api;
