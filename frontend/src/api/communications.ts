import { apiClient } from "./client";
import type {
  CommunicationDetail,
  CommunicationListItem,
  PaginatedResponse,
  RegisterCommunicationRequest,
  RegisterCommunicationResponse,
  VersionHistoryResponse,
  CommunicationVersionSerialized,
} from "./types";

export interface ListCommunicationsParams {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  media_type?: string;
  category?: string;
}

/** GET /communications — role-scoped, paginated list (Institution: own docs, Admin: all). */
export async function listCommunications(
  params: ListCommunicationsParams = {}
): Promise<PaginatedResponse<CommunicationListItem>> {
  const { data } = await apiClient.get<PaginatedResponse<CommunicationListItem>>("/communications", { params });
  return data;
}

/** PUT /communications/{id} — update title/description/category/status/validity. */
export async function updateCommunication(
  communicationId: string,
  payload: Partial<{
    title: string;
    description: string | null;
    category: string | null;
    status: string;
    valid_from: string | null;
    valid_until: string | null;
  }>
) {
  const { data } = await apiClient.put(`/communications/${encodeURIComponent(communicationId)}`, payload);
  return data as { success: boolean; communication_id: string; status: string };
}

/** DELETE /communications/{id} — archives/revokes the communication. */
export async function deleteCommunication(communicationId: string) {
  const { data } = await apiClient.delete(`/communications/${encodeURIComponent(communicationId)}`);
  return data as { success: boolean; message: string; communication_id: string };
}

/** POST /communications — register an already-signed communication (first version). */
export async function registerCommunication(
  payload: RegisterCommunicationRequest
): Promise<RegisterCommunicationResponse> {
  const { data } = await apiClient.post<RegisterCommunicationResponse>("/communications", payload);
  return data;
}

/** GET /communications/{communication_id} — full public provenance lookup. */
export async function getCommunication(communicationId: string): Promise<CommunicationDetail> {
  const { data } = await apiClient.get<CommunicationDetail>(
    `/communications/${encodeURIComponent(communicationId)}`
  );
  return data;
}

/** GET /communications/{communication_id}/versions — full immutable version history. */
export async function getCommunicationVersions(
  communicationId: string
): Promise<VersionHistoryResponse> {
  const { data } = await apiClient.get<VersionHistoryResponse>(
    `/communications/${encodeURIComponent(communicationId)}/versions`
  );
  return data;
}

/** GET /communications/{communication_id}/current — the currently active version. */
export async function getCommunicationCurrentVersion(
  communicationId: string
): Promise<CommunicationVersionSerialized> {
  const { data } = await apiClient.get<CommunicationVersionSerialized>(
    `/communications/${encodeURIComponent(communicationId)}/current`
  );
  return data;
}
