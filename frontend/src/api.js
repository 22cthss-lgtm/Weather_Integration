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

async function parseJson(response, fallbackMessage) {
  let payload = null;

  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new Error(payload?.error || fallbackMessage);
  }

  return payload;
}

export async function fetchFaqs({ category = "", q = "" } = {}) {
  const params = new URLSearchParams();
  if (category) {
    params.set("category", category);
  }
  if (q) {
    params.set("q", q);
  }

  const queryString = params.toString();
  const response = await fetch(`${API_BASE_URL}/api/faqs${queryString ? `?${queryString}` : ""}`);
  return parseJson(response, "Failed to fetch FAQs");
}

export async function fetchFaq(id) {
  const response = await fetch(`${API_BASE_URL}/api/faqs/${id}`);
  return parseJson(response, `Failed to fetch FAQ ${id}`);
}

export async function fetchFaqCategories() {
  const response = await fetch(`${API_BASE_URL}/api/faqs/categories`);
  return parseJson(response, "Failed to fetch FAQ categories");
}

export async function createFaq(payload) {
  const response = await fetch(`${API_BASE_URL}/api/faqs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseJson(response, "Failed to create FAQ");
}

export async function updateFaq(id, payload) {
  const response = await fetch(`${API_BASE_URL}/api/faqs/${id}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  return parseJson(response, `Failed to update FAQ ${id}`);
}

export async function deleteFaq(id) {
  const response = await fetch(`${API_BASE_URL}/api/faqs/${id}`, {
    method: "DELETE",
  });
  return parseJson(response, `Failed to delete FAQ ${id}`);
}
