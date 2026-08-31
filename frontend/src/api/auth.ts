import { apiClient } from "./client";
import type { LoginRequest, TokenResponse, User } from "./types";

/** POST /auth/admin/login — role-locked admin login. */
export async function adminLogin(payload: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/admin/login", payload);
  return data;
}

/** POST /auth/institution/login — role-locked institution (AUTHORITY) login. */
export async function institutionLogin(payload: LoginRequest): Promise<TokenResponse> {
  const { data } = await apiClient.post<TokenResponse>("/auth/institution/login", payload);
  return data;
}

/** POST /auth/logout */
export async function logoutRequest(): Promise<void> {
  await apiClient.post("/auth/logout");
}

/** GET /auth/me — returns the authenticated user, including role + issuer_id. */
export async function getMe(): Promise<User> {
  const { data } = await apiClient.get<User>("/auth/me");
  return data;
}
