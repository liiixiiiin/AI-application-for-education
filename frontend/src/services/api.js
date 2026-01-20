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
  const isFormData = options.body instanceof FormData;
  const headers = buildHeaders();
  if (isFormData) {
    delete headers["Content-Type"];
  }
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers || {}),
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload.data ?? payload;
};

const parseSseEvents = (buffer) => {
  const events = [];
  const parts = buffer.split("\n\n");
  const remaining = parts.pop() || "";
  parts.forEach((part) => {
    if (!part.trim()) return;
    let event = "message";
    const dataLines = [];
    part.split("\n").forEach((line) => {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      }
    });
    if (!dataLines.length) return;
    const raw = dataLines.join("\n");
    let data = raw;
    try {
      data = JSON.parse(raw);
    } catch (error) {
      data = raw;
    }
    events.push({ event, data });
  });
  return { events, remaining };
};

export const apiStream = async (path, options = {}, onEvent) => {
  const headers = buildHeaders();
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...headers,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch (error) {
      message = message;
    }
    throw new Error(message);
  }

  if (!response.body) {
    throw new Error("Streaming not supported by browser");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSseEvents(buffer);
    buffer = parsed.remaining;
    parsed.events.forEach(({ event, data }) => {
      if (onEvent) {
        onEvent(event, data);
      }
    });
  }

  if (buffer.trim()) {
    const parsed = parseSseEvents(buffer + "\n\n");
    parsed.events.forEach(({ event, data }) => {
      if (onEvent) {
        onEvent(event, data);
      }
    });
  }
};
