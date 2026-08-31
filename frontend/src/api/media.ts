import { apiClient } from "./client";
import type { MediaAnalyzeResponse } from "./types";

/** POST /media/analyze — run advisory AI manipulation-risk analysis independently of registration. */
export async function analyzeMedia(file: File, versionId?: number): Promise<MediaAnalyzeResponse> {
  const formData = new FormData();
  formData.append("file", file);
  if (versionId !== undefined) formData.append("version_id", String(versionId));
  const { data } = await apiClient.post<MediaAnalyzeResponse>("/media/analyze", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
