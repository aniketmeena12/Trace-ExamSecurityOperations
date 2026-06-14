// Thin fetch wrapper around the REAL Trace backend. No mock data anywhere.
// In dev, Vite proxies /api -> http://127.0.0.1:8000 (see vite.config.js).
// In production, VITE_API_URL is set to the Railway backend URL.

const BASE = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE || "/api";

class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function parse(res) {
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const detail = (data && data.detail) || res.statusText;
    throw new ApiError(
      typeof detail === "string" ? detail : JSON.stringify(detail),
      res.status,
      detail
    );
  }
  return data;
}

function authHeaders(token) {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export const api = {
  BASE,

  // OAuth2 password login (form-encoded) -> { access_token, role, username }
  async login(username, password) {
    const body = new URLSearchParams({ username, password });
    const res = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    return parse(res);
  },

  async get(path, token) {
    const res = await fetch(`${BASE}${path}`, { headers: authHeaders(token) });
    return parse(res);
  },

  async post(path, token, json) {
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders(token) },
      body: json === undefined ? undefined : JSON.stringify(json),
    });
    return parse(res);
  },

  // Returns an object URL for an image endpoint (e.g. watermarked paper PNG)
  // plus any response headers we care about (the trace fingerprint).
  async getImage(path, token) {
    const res = await fetch(`${BASE}${path}`, { headers: authHeaders(token) });
    if (!res.ok) return parse(res); // throws ApiError with detail
    const blob = await res.blob();
    return {
      url: URL.createObjectURL(blob),
      blob,
      fingerprint: res.headers.get("X-Trace-Fingerprint"),
    };
  },

  // Multipart upload (investigator trace)
  async uploadImage(path, token, file) {
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers: authHeaders(token),
      body: form,
    });
    return parse(res);
  },
};

export { ApiError };
