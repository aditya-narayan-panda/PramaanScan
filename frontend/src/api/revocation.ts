import { apiClient } from "./client";
import type { KeyStatusResponse, RevokeKeyRequest, RevokeKeyResponse } from "./types";

/** POST /revocation/key — revoke a signing key (Admin: Key Management). */
export async function revokeKey(payload: RevokeKeyRequest): Promise<RevokeKeyResponse> {
  const { data } = await apiClient.post<RevokeKeyResponse>("/revocation/key", payload);
  return data;
}

/** GET /revocation/key/{key_id} — check whether a signing key is active or revoked. */
export async function getKeyStatus(keyId: string): Promise<KeyStatusResponse> {
  const { data } = await apiClient.get<KeyStatusResponse>(
    `/revocation/key/${encodeURIComponent(keyId)}`
  );
  return data;
}
