const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export async function postJson(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
}

export async function getJson(path) {
  const response = await fetch(`${API_BASE}${path}`);
  return handleResponse(response);
}

export async function postFile(path, file, extra = {}) {
  const formData = new FormData();
  formData.append("file", file);
  const query = new URLSearchParams(extra).toString();
  const endpoint = query ? `${API_BASE}${path}?${query}` : `${API_BASE}${path}`;
  const response = await fetch(endpoint, { method: "POST", body: formData });
  return handleResponse(response);
}

async function handleResponse(response) {
  const text = await response.text();
  const data = text ? JSON.parse(text) : null;
  if (!response.ok) {
    const detail = data?.detail || "Request failed";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

