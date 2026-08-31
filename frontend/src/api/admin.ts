import { apiClient } from "./client";
import type { InstitutionDetail, InstitutionListItem, PaginatedResponse, UserListItem } from "./types";

export interface ListParams {
  page?: number;
  page_size?: number;
  search?: string;
}

export async function listInstitutions(
  params: ListParams & { status?: string } = {}
): Promise<PaginatedResponse<InstitutionListItem>> {
  const { data } = await apiClient.get<PaginatedResponse<InstitutionListItem>>("/admin/institutions", { params });
  return data;
}

export async function createInstitution(payload: {
  institution_name: string;
  email: string;
  contact_phone?: string | null;
}) {
  const { data } = await apiClient.post("/admin/institutions", payload);
  return data as { success: boolean; institution: InstitutionListItem };
}

export async function getInstitution(id: number): Promise<InstitutionDetail> {
  const { data } = await apiClient.get<InstitutionDetail>(`/admin/institutions/${id}`);
  return data;
}

export async function updateInstitution(
  id: number,
  payload: Partial<{ institution_name: string; email: string; contact_phone: string | null; status: string }>
) {
  const { data } = await apiClient.put(`/admin/institutions/${id}`, payload);
  return data as { success: boolean; id: number; status: string };
}

export async function suspendInstitution(id: number) {
  const { data } = await apiClient.delete(`/admin/institutions/${id}`);
  return data as { success: boolean; message: string; id: number };
}

export async function listUsers(
  params: ListParams & { role?: string; issuer_id?: number } = {}
): Promise<PaginatedResponse<UserListItem>> {
  const { data } = await apiClient.get<PaginatedResponse<UserListItem>>("/admin/users", { params });
  return data;
}

export async function createUser(payload: {
  email: string;
  password: string;
  full_name: string;
  role: "ADMIN" | "AUTHORITY";
  issuer_id?: number | null;
}) {
  const { data } = await apiClient.post("/admin/users", payload);
  return data as { success: boolean; user: UserListItem };
}

export async function updateUser(
  id: number,
  payload: Partial<{ full_name: string; password: string; role: string; issuer_id: number | null; is_active: boolean }>
) {
  const { data } = await apiClient.put(`/admin/users/${id}`, payload);
  return data;
}

export async function deactivateUser(id: number) {
  const { data } = await apiClient.delete(`/admin/users/${id}`);
  return data as { success: boolean; message: string; id: number };
}
