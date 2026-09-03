import axios from "axios";

export function errorMessage(err: unknown, fallback = "Request failed"): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail)) {
      const parts = detail
        .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : null))
        .filter((item): item is string => Boolean(item));
      if (parts.length) {
        return parts.join(" ");
      }
    }
    const errors = err.response?.data?.errors;
    if (Array.isArray(errors)) {
      const parts = errors
        .map((item) => (typeof item === "object" && item && "msg" in item ? String(item.msg) : null))
        .filter((item): item is string => Boolean(item));
      if (parts.length) {
        return parts.join(" ");
      }
    }
    if (err.response?.status === 409) {
      return "That record already exists.";
    }
    if (err.response?.status === 403) {
      return "You do not have access to this resource.";
    }
    if (!err.response) {
      return "Could not reach the API.";
    }
  }
  return fallback;
}

export async function swallowForbidden<T>(loader: () => Promise<T>, fallback: T): Promise<T> {
  try {
    return await loader();
  } catch (err) {
    if (axios.isAxiosError(err) && err.response?.status === 403) {
      return fallback;
    }
    throw err;
  }
}
