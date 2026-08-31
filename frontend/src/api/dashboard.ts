import { apiClient } from "./client";
import type { DashboardStats } from "./types";

/** GET /dashboard/stats — role-scoped live stats (Institution sees own issuer, Admin sees all). */
export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/dashboard/stats");
  return data;
}
