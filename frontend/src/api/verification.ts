import { apiClient } from "./client";
import type { FileVerificationResponse, QrResolutionResponse } from "./types";

/** POST /verify/file — authoritative cryptographic + advisory ML verification of an uploaded file. */
export async function verifyFile(file: File): Promise<FileVerificationResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await apiClient.post<FileVerificationResponse>("/verify/file", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/** GET /verify/communication/{communication_id} — resolves a QR / Communication ID. */
export async function resolveCommunication(communicationId: string): Promise<QrResolutionResponse> {
  const { data } = await apiClient.get<QrResolutionResponse>(
    `/verify/communication/${encodeURIComponent(communicationId)}`
  );
  return data;
}
