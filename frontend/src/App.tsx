import { Routes, Route } from "react-router-dom";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { ProtectedRoute } from "@/components/common/ProtectedRoute";
import { PublicLayout } from "@/components/layout/PublicLayout";
import { InstitutionLayout } from "@/components/layout/InstitutionLayout";
import { AdminLayout } from "@/components/layout/AdminLayout";

// Public
import LandingPage from "@/pages/public/LandingPage";
import VerifyPage from "@/pages/public/VerifyPage";
import VerificationResultPage from "@/pages/public/VerificationResultPage";
import CommunicationDetailPage from "@/pages/public/CommunicationDetailPage";
import AboutPage from "@/pages/public/AboutPage";
import ContactPage from "@/pages/public/ContactPage";
import FaqPage from "@/pages/public/FaqPage";

// Auth
import AdminLoginPage from "@/pages/auth/AdminLoginPage";
import InstitutionLoginPage from "@/pages/auth/InstitutionLoginPage";

// Institution
import InstitutionDashboard from "@/pages/institution/InstitutionDashboard";
import IssueDocumentPage from "@/pages/institution/IssueDocumentPage";
import UploadSignPage from "@/pages/institution/UploadSignPage";
import GenerateQrPage from "@/pages/institution/GenerateQrPage";
import MyDocumentsPage from "@/pages/institution/MyDocumentsPage";
import VerificationLogsPage from "@/pages/institution/VerificationLogsPage";
import AnalyticsPage from "@/pages/institution/AnalyticsPage";
import ProfileSettingsPage from "@/pages/institution/ProfileSettingsPage";
import InstitutionKeyManagementPage from "@/pages/institution/InstitutionKeyManagementPage";

// Admin
import AdminDashboard from "@/pages/admin/AdminDashboard";
import InstitutionManagementPage from "@/pages/admin/InstitutionManagementPage";
import UserManagementPage from "@/pages/admin/UserManagementPage";
import DocumentManagementPage from "@/pages/admin/DocumentManagementPage";
import AdminVerificationLogsPage from "@/pages/admin/AdminVerificationLogsPage";
import KeyManagementPage from "@/pages/admin/KeyManagementPage";
import AdminAnalyticsPage from "@/pages/admin/AdminAnalyticsPage";
import AuditLogsPage from "@/pages/admin/AuditLogsPage";
import SystemSettingsPage from "@/pages/admin/SystemSettingsPage";

// Errors
import NotFoundPage from "@/pages/errors/NotFoundPage";
import ForbiddenPage from "@/pages/errors/ForbiddenPage";
import ServerErrorPage from "@/pages/errors/ServerErrorPage";

export default function App() {
  return (
    <ErrorBoundary>
      <Routes>
        {/* Public site */}
        <Route element={<PublicLayout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/verify" element={<VerifyPage />} />
          <Route path="/verify/result" element={<VerificationResultPage />} />
          <Route path="/verify/communication/:communicationId" element={<CommunicationDetailPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/faq" element={<FaqPage />} />
        </Route>

        {/* Auth (no shared layout — full-bleed) */}
        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route path="/institution/login" element={<InstitutionLoginPage />} />

        {/* Institution portal */}
        <Route element={<ProtectedRoute allowedRoles={["AUTHORITY"]} />}>
          <Route element={<InstitutionLayout />}>
            <Route path="/institution/dashboard" element={<InstitutionDashboard />} />
            {/* Primary document issuance — server-side signing wizard */}
            <Route path="/institution/issue" element={<IssueDocumentPage />} />
            {/* Legacy manual sign page — kept for advanced users who sign externally */}
            <Route path="/institution/upload-sign" element={<UploadSignPage />} />
            <Route path="/institution/generate-qr" element={<GenerateQrPage />} />
            <Route path="/institution/documents" element={<MyDocumentsPage />} />
            <Route path="/institution/documents/:communicationId" element={<CommunicationDetailPage />} />
            <Route path="/institution/verification-logs" element={<VerificationLogsPage />} />
            <Route path="/institution/analytics" element={<AnalyticsPage />} />
            <Route path="/institution/keys" element={<InstitutionKeyManagementPage />} />
            <Route path="/institution/profile" element={<ProfileSettingsPage />} />
          </Route>
        </Route>

        {/* Admin portal */}
        <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
          <Route element={<AdminLayout />}>
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/institutions" element={<InstitutionManagementPage />} />
            <Route path="/admin/users" element={<UserManagementPage />} />
            <Route path="/admin/documents" element={<DocumentManagementPage />} />
            <Route path="/admin/documents/:communicationId" element={<CommunicationDetailPage />} />
            <Route path="/admin/verification-logs" element={<AdminVerificationLogsPage />} />
            <Route path="/admin/keys" element={<KeyManagementPage />} />
            <Route path="/admin/analytics" element={<AdminAnalyticsPage />} />
            <Route path="/admin/audit-logs" element={<AuditLogsPage />} />
            <Route path="/admin/settings" element={<SystemSettingsPage />} />
          </Route>
        </Route>

        {/* Errors */}
        <Route path="/403" element={<ForbiddenPage />} />
        <Route path="/500" element={<ServerErrorPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </ErrorBoundary>
  );
}
