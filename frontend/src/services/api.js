async function request(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed. Please try again later.");
  }
  return payload;
}

export function requestHealth() {
  return request("/api/health");
}

export function requestLogin(formData) {
  return request("/api/auth/login", { method: "POST", body: formData });
}

export function requestProcess(formData) {
  return request("/api/process", { method: "POST", body: formData });
}

export function requestProcessBatch(formData) {
  return request("/api/process-batch", { method: "POST", body: formData });
}

export const requestBatchProcess = requestProcessBatch;

export function requestDemo(formData) {
  return request("/api/demo-chart", { method: "POST", body: formData });
}

export function requestSlidePreview(formData) {
  return request("/api/slide-preview", { method: "POST", body: formData });
}

export function requestSlideOutline(formData) {
  return request("/api/parse-slides", { method: "POST", body: formData });
}

export function requestJobs(limit = 30) {
  return request(`/api/jobs?limit=${limit}`);
}

export function requestJobDetail(requestId) {
  return request(`/api/jobs/${encodeURIComponent(requestId)}`);
}
