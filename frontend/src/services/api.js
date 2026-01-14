import { getSession } from "../stores/session";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api/v1";

const buildHeaders = () => {
  const { token } = getSession();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

export const apiRequest = async (path, options = {}) => {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...buildHeaders(),
      ...(options.headers || {}),
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload.data;
};
