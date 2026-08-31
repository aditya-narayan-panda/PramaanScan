import { apiClient } from "./client";
import type { AnalyticsOverview, MediaAnalytics, VerificationAnalytics } from "./types";

export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  const { data } = await apiClient.get<AnalyticsOverview>("/analytics/overview");
  return data;
}

export async function getVerificationAnalytics(): Promise<VerificationAnalytics> {
  const { data } = await apiClient.get<VerificationAnalytics>("/analytics/verifications");
  return data;
}

export async function getMediaAnalytics(): Promise<MediaAnalytics> {
  const { data } = await apiClient.get<MediaAnalytics>("/analytics/media");
  return data;
}
