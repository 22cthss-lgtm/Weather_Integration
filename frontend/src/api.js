const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000";

export async function fetchLatestImage(type) {
  const response = await fetch(`${API_BASE_URL}/api/images/latest?type=${encodeURIComponent(type)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch latest image for ${type}`);
  }
  return response.json();
}

export async function fetchImageHistory(type) {
  const response = await fetch(`${API_BASE_URL}/api/images/history?type=${encodeURIComponent(type)}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch history for ${type}`);
  }
  return response.json();
}

export async function fetchDocs() {
  const response = await fetch(`${API_BASE_URL}/api/docs`);
  if (!response.ok) {
    throw new Error("Failed to fetch docs");
  }
  return response.json();
}

export async function fetchDoc(id) {
  const response = await fetch(`${API_BASE_URL}/api/docs/${id}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch doc ${id}`);
  }
  return response.json();
}
