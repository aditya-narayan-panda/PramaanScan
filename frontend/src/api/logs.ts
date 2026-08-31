import { apiClient } from "./client";
import type { AuditLogItem, PaginatedResponse, VerificationLogItem } from "./types";

export async function listAuditLogs(
  params: { page?: number; page_size?: number; action?: string; resource_type?: string } = {}
): Promise<PaginatedResponse<AuditLogItem>> {
  const { data } = await apiClient.get<PaginatedResponse<AuditLogItem>>("/admin/audit-logs", { params });
  return data;
}

export async function listVerificationLogs(
  params: { page?: number; page_size?: number; result?: string; source?: string; communication_id?: string } = {}
): Promise<PaginatedResponse<VerificationLogItem>> {
  const { data } = await apiClient.get<PaginatedResponse<VerificationLogItem>>("/verification/logs", { params });
  return data;
}
