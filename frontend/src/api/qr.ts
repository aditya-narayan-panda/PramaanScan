import { apiClient } from "./client";
import type { QrDataResponse } from "./types";

/** GET /communications/{id}/qr — auth'd QR payload (verification URL) for a communication. */
export async function getQrData(communicationId: string): Promise<QrDataResponse> {
  const { data } = await apiClient.get<QrDataResponse>(
    `/communications/${encodeURIComponent(communicationId)}/qr`
  );
  return data;
}

/** GET /communications/{id}/qr/image — public PNG QR image URL (for <img src>). */
export function getQrImageUrl(communicationId: string): string {
  return `${apiClient.defaults.baseURL}/communications/${encodeURIComponent(communicationId)}/qr/image`;
}
