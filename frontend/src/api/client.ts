import axios, { AxiosError } from "axios";
import type { ApiErrorPayload } from "./types";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

export const TOKEN_STORAGE_KEY = "pramaanscan.access_token";
export const REFRESH_TOKEN_STORAGE_KEY = "pramaanscan.refresh_token";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 180_000, // 3 minutes — audio/video ML inference can be slow on constrained hosting
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/** Fired by the interceptor when a 401 is received so AuthContext can log out. */
export const AUTH_EXPIRED_EVENT = "pramaanscan:auth-expired";

let refreshPromise: Promise<string | null> | null = null;

async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_STORAGE_KEY);
  if (!refreshToken) return null;
  if (!refreshPromise) {
    refreshPromise = axios
      .post(`${API_BASE_URL}/auth/refresh`, { refresh_token: refreshToken })
      .then((res) => {
        const { access_token, refresh_token } = res.data;
        localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
        localStorage.setItem(REFRESH_TOKEN_STORAGE_KEY, refresh_token);
        return access_token as string;
      })
      .catch(() => null)
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorPayload>) => {
    const original = error.config as (typeof error.config & { _retried?: boolean }) | undefined;
    const isAuthEndpoint =
      typeof original?.url === "string" &&
      (original.url.includes("/auth/logout") || original.url.includes("/auth/refresh") || original.url.includes("/auth/login"));
    if (error.response?.status === 401 && original && !original._retried && !isAuthEndpoint) {
      original._retried = true;
      const newToken = await tryRefreshToken();
      if (newToken) {
        original.headers = original.headers ?? {};
        original.headers.Authorization = `Bearer ${newToken}`;
        return apiClient.request(original);
      }
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }
    return Promise.reject(error);
  }
);

/** Extract a human-readable error message from any Axios/FastAPI error. */
export function getApiErrorMessage(error: unknown, fallback = "Something went wrong. Please try again."): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as ApiErrorPayload | undefined;
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail) && data.detail.length > 0) {
      return data.detail.map((d) => d.msg).join(", ");
    }
    if (error.code === "ECONNABORTED") return "The request timed out. Please try again.";
    if (error.message === "Network Error") {
      return `Could not reach the PramaanScan API at ${API_BASE_URL}. Is the backend running?`;
    }
    return error.message || fallback;
  }
  if (error instanceof Error) return error.message;
  return fallback;
}
