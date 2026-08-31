// ============================================================
// These types mirror the actual PramaanScan FastAPI response
// shapes exactly as returned by the backend (see /app/api/routes
// and /app/schemas in the analyzed backend). No field is invented.
// ============================================================

export type UserRole = "ADMIN" | "AUTHORITY";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  issuer_id: number | null;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}

export interface DashboardStats {
  total_documents: number;
  revoked_documents: number;
  total_verifications: number;
  verified_verifications: number;
  unsigned_verifications: number;
  high_risk_media: number;
  users: number;
  institutions: number;
}

export interface CommunicationListItem {
  id: number;
  communication_id: string;
  issuer_id: number;
  title: string;
  description: string | null;
  category: string | null;
  media_type: MediaType;
  status: CommunicationStatus;
  current_version_id: number | null;
  valid_from: string | null;
  valid_until: string | null;
  created_at: string;
}

export interface InstitutionListItem {
  id: number;
  institution_name: string;
  email: string;
  contact_phone: string | null;
  status: "ACTIVE" | "SUSPENDED";
  created_at: string;
}

export interface InstitutionDetail extends InstitutionListItem {
  users: { id: number; email: string; full_name: string; role: UserRole; is_active: boolean }[];
}

export interface UserListItem {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  issuer_id: number | null;
  is_active: boolean;
  created_at: string;
  last_login_at: string | null;
}

export interface AuditLogItem {
  id: number;
  actor_user_id: number | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown>;
  created_at: string;
}

export interface VerificationLogItem {
  id: number;
  communication_id: string | null;
  sha256: string;
  result: VerificationStatus;
  source: "QR" | "COMMUNICATION_ID" | "FILE_UPLOAD";
  created_at: string;
}

export interface AnalyticsOverview {
  total_verifications: number;
  results: Record<string, number>;
  documents: number;
}

export interface VerificationAnalytics {
  by_source: Record<string, number>;
  by_result: Record<string, number>;
  total: number;
}

export interface MediaAnalytics {
  total_analyses: number;
  risk_labels: Record<string, number>;
  average_risk_score: number;
}

export interface UserSettingsResponse {
  language: string;
  theme: "system" | "light" | "dark";
  notifications_enabled: boolean;
  email_notifications: boolean;
}

export interface QrDataResponse {
  communication_id: string;
  verification_url: string;
  [key: string]: unknown;
}

export type MediaType = "TEXT" | "DOCUMENT" | "IMAGE" | "AUDIO" | "VIDEO";

export type CommunicationStatus =
  | "CURRENT"
  | "SUPERSEDED"
  | "REVOKED"
  | "EXPIRED";

export type KeyStatus = "ACTIVE" | "REVOKED";

export type VerificationStatus =
  | "VERIFIED"
  | "MODIFIED"
  | "UNSIGNED"
  | "REVOKED"
  | "INVALID"
  | "EXPIRED";

export interface CommunicationVersionSerialized {
  version_id: number;
  communication_id: string;
  version: number;
  title: string;
  description: string | null;
  category: string | null;
  media_type: MediaType;
  communication_status: CommunicationStatus;
  sha256: string;
  signature: string;
  signing_key_id: string;
  algorithm: string;
  key_status: KeyStatus;
  file_name: string | null;
  mime_type: string | null;
  file_size_bytes: number | null;
  valid_from: string | null;
  valid_until: string | null;
  created_at: string;
}

export interface CommunicationDetail {
  communication_id: string;
  issuer: {
    issuer_id: number;
    institution_name: string;
    email: string;
  };
  title: string;
  description: string | null;
  category: string | null;
  media_type: MediaType;
  status: CommunicationStatus;
  current_version_id: number | null;
  valid_from: string | null;
  valid_until: string | null;
  versions: CommunicationVersionSerialized[];
}

export interface VersionHistoryResponse {
  communication_id: string;
  current_version_id: number | null;
  current_status: CommunicationStatus;
  total_versions: number;
  versions: CommunicationVersionSerialized[];
}

export interface QrResolutionResponse {
  communication: {
    communication_id: string;
    title: string;
    description: string | null;
    category: string | null;
    media_type: MediaType;
    status: CommunicationStatus;
    valid_from: string | null;
    valid_until: string | null;
    created_at: string;
  };
  current_version: {
    version: number;
    sha256: string;
    filename: string | null;
    mime_type: string | null;
    file_size_bytes: number | null;
    created_at: string;
  };
  signing: {
    key_id: string;
    algorithm: string;
    key_status: KeyStatus;
  };
  qr_verification: {
    identified: boolean;
    message: string;
  };
}

export interface RegisterCommunicationRequest {
  issuer_id: number;
  title: string;
  description?: string | null;
  category?: string | null;
  media_type: MediaType;
  sha256: string;
  signature: string;
  signing_key_id: string;
  file_name?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  valid_from?: string | null;
  valid_until?: string | null;
}

export interface RegisterCommunicationResponse {
  success: boolean;
  message: string;
  communication: {
    communication_id: string;
    issuer_id: number;
    institution_name: string;
    title: string;
    media_type: MediaType;
    status: CommunicationStatus;
    current_version: number;
  };
  cryptographic_provenance: {
    sha256: string;
    signature_valid: boolean;
    algorithm: string;
    signing_key_id: string;
    key_status: KeyStatus;
  };
  version: {
    version_id: number;
    version_number: number;
    file_name: string | null;
    mime_type: string | null;
    file_size_bytes: number | null;
  };
}

// ------------------------------------------------------------
// Media / AI-assisted advisory analysis (secondary, non-authoritative)
// ------------------------------------------------------------

export type RiskLabel = "LOW" | "MEDIUM" | "HIGH" | "INCONCLUSIVE";

export interface MediaAnalysisResult {
  available?: boolean;
  reason?: string;
  modality?: "IMAGE" | "AUDIO" | "VIDEO" | "DOCUMENT" | "UNKNOWN";
  risk_score?: number | null;
  risk_label?: RiskLabel;
  model_name?: string;
  is_advisory?: boolean;
  evidence_type?: string;
  disclaimer?: string;
  filename?: string;
  [key: string]: unknown;
}

export interface DatabaseStoreResult {
  stored: boolean;
  media_analysis_id?: number;
  risk_label?: RiskLabel;
  risk_score?: number | null;
  model_name?: string;
  model_version?: string;
  is_advisory?: boolean;
  reason?: string;
  error?: string;
}

// ------------------------------------------------------------
// POST /verify/file response — the authoritative verification result
// ------------------------------------------------------------

export interface FileVerificationResponse {
  status: VerificationStatus;
  reason: string;
  sha256: string;
  filename: string;

  communication_id?: string;
  version?: number;
  key_id?: string;
  algorithm?: string;
  key_status?: KeyStatus;
  document_integrity?: "MATCH";
  signature_valid?: boolean;

  cryptographic_verification: {
    verified: boolean;
    status?: VerificationStatus;
    sha256?: string;
    algorithm?: string;
    key_status?: KeyStatus;
  };

  media_analysis: MediaAnalysisResult;
  database: DatabaseStoreResult;
}

export interface MediaAnalyzeResponse {
  success: boolean;
  filename: string;
  analysis: MediaAnalysisResult;
  database: DatabaseStoreResult;
}

// ------------------------------------------------------------
// Revocation
// ------------------------------------------------------------

export interface RevokeKeyRequest {
  key_id: string;
  reason: string;
  revoked_by?: number | null;
}

export interface RevokeKeyResult {
  key_id: string;
  status: KeyStatus;
  revoked_at: string | null;
  reason: string;
  revocation_id: number;
}

export interface RevokeKeyResponse {
  success: boolean;
  message: string;
  revocation: RevokeKeyResult;
}

export interface KeyStatusResponse {
  key_id: string;
  found: boolean;
  status: "ACTIVE" | "REVOKED" | "UNKNOWN";
  revoked: boolean;
  algorithm?: string;
  created_at?: string | null;
  revoked_at?: string | null;
  revoked_reason?: string | null;
}

// ------------------------------------------------------------
// Generic API error shape (FastAPI HTTPException)
// ------------------------------------------------------------

export interface ApiErrorPayload {
  detail?: string | { msg: string }[];
}
