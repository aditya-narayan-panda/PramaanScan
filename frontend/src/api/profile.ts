import { apiClient } from "./client";
import type { User, UserSettingsResponse } from "./types";

export async function getProfile(): Promise<User & { created_at: string; last_login_at: string | null }> {
  const { data } = await apiClient.get("/profile");
  return data;
}

export async function updateProfile(full_name: string) {
  const { data } = await apiClient.put("/profile", { full_name });
  return data as { success: boolean; full_name: string };
}

export async function changePassword(current_password: string, new_password: string) {
  const { data } = await apiClient.post("/profile/password", { current_password, new_password });
  return data as { success: boolean; message: string };
}

export async function getUserSettings(): Promise<UserSettingsResponse> {
  const { data } = await apiClient.get<UserSettingsResponse>("/settings");
  return data;
}

export async function updateUserSettings(payload: Partial<UserSettingsResponse>): Promise<UserSettingsResponse> {
  const { data } = await apiClient.put<UserSettingsResponse>("/settings", payload);
  return data;
}
