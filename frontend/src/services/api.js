async function request(url, options = {}) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "请求失败，请稍后再试。");
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
