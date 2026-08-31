import { Link, useLocation, useNavigate } from "react-router-dom";
import { ShieldCheck, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  VerificationResultHeader,
  CommunicationSummaryCard,
} from "@/components/verification/VerificationResultCard";
import { MediaAnalysisPanel } from "@/components/verification/MediaAnalysisPanel";
import type { FileVerificationResponse, QrResolutionResponse } from "@/api/types";

type LocationState =
  | { source: "file"; result: FileVerificationResponse; filename: string }
  | { source: "code"; result: QrResolutionResponse; communicationId: string };

export default function VerificationResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState | null;

  if (!state) {
    return (
      <div className="container max-w-lg py-20 text-center">
        <h1 className="font-display text-2xl font-bold">No result to show</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Verify a document first to see its result here.
        </p>
        <Button className="mt-6" asChild>
          <Link to="/verify">
            <ShieldCheck className="h-4 w-4" /> Go to Verify
          </Link>
        </Button>
      </div>
    );
  }

  const isFile = state.source === "file";
  const result = state.result;

  return (
    <div className="container max-w-2xl py-12 sm:py-16">
      <button
        onClick={() => navigate(-1)}
        className="mb-6 flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </button>

      {isFile ? (
        <FileResultView result={result as FileVerificationResponse} filename={state.filename} />
      ) : (
        <CodeResultView result={result as QrResolutionResponse} />
      )}
    </div>
  );
}

function FileResultView({ result, filename }: { result: FileVerificationResponse; filename: string }) {
  return (
    <div className="space-y-6">
      <VerificationResultHeader
        status={result.status}
        filename={filename}
        sha256={result.sha256}
        communicationId={result.communication_id}
      />

      {result.communication_id && (
        <div className="rounded-2xl border border-border bg-card p-6">
          <h3 className="mb-3 font-display text-sm font-semibold">Signature Details</h3>
          <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
            {result.algorithm && (
              <div>
                <dt className="text-xs text-muted-foreground">Algorithm</dt>
                <dd className="mt-0.5 font-medium">{result.algorithm}</dd>
              </div>
            )}
            {result.version !== undefined && (
              <div>
                <dt className="text-xs text-muted-foreground">Version</dt>
                <dd className="mt-0.5 font-medium">v{result.version}</dd>
              </div>
            )}
            {result.key_status && (
              <div>
                <dt className="text-xs text-muted-foreground">Key Status</dt>
                <dd className="mt-0.5 font-medium">{result.key_status}</dd>
              </div>
            )}
            {result.document_integrity && (
              <div>
                <dt className="text-xs text-muted-foreground">Integrity</dt>
                <dd className="mt-0.5 font-medium">{result.document_integrity}</dd>
              </div>
            )}
          </dl>
          {result.communication_id && (
            <Button variant="outline" size="sm" className="mt-5" asChild>
              <Link to={`/verify/communication/${result.communication_id}`}>View full provenance</Link>
            </Button>
          )}
        </div>
      )}

      <MediaAnalysisPanel analysis={result.media_analysis} />
    </div>
  );
}

function CodeResultView({ result }: { result: QrResolutionResponse }) {
  const status = result.signing.key_status === "REVOKED" ? "REVOKED" : "VERIFIED";
  return (
    <div className="space-y-6">
      <VerificationResultHeader
        status={status}
        sha256={result.current_version.sha256}
        communicationId={result.communication.communication_id}
      />

      <CommunicationSummaryCard
        title={result.communication.title}
        category={result.communication.category}
        createdAt={result.communication.created_at}
        algorithm={result.signing.algorithm}
        keyStatus={result.signing.key_status}
        communicationId={result.communication.communication_id}
      />

      <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-sm text-primary">
        {result.qr_verification.message}
      </div>
    </div>
  );
}
