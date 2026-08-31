import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ShieldCheck, Calendar, FileDigit, Building2, KeyRound, ArrowRight } from "lucide-react";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { truncateMiddle, formatDateTime } from "@/lib/utils";
import type { VerificationStatus } from "@/api/types";

const STATUS_COPY: Record<string, { title: string; description: string }> = {
  VERIFIED: {
    title: "This document is authentic",
    description: "Its cryptographic fingerprint matches an active, validly-signed record.",
  },
  MODIFIED: {
    title: "This document has been modified",
    description: "The file's fingerprint doesn't match the original registered version.",
  },
  UNSIGNED: {
    title: "No matching signed record found",
    description: "This exact file isn't registered with any institution on PramaanScan.",
  },
  REVOKED: {
    title: "Signing key was revoked",
    description: "This document was signed with a key that has since been revoked. Treat it as untrusted.",
  },
  INVALID: {
    title: "Signature is invalid",
    description: "A record was found, but the cryptographic signature failed validation.",
  },
  EXPIRED: {
    title: "This communication has expired",
    description: "The document was validly signed but is past its validity period.",
  },
};

export function VerificationResultHeader({
  status,
  filename,
  sha256,
  communicationId,
}: {
  status: VerificationStatus | string;
  filename?: string;
  sha256?: string;
  communicationId?: string;
}) {
  const copy = STATUS_COPY[status] ?? {
    title: "Verification result",
    description: "See the details below.",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-border bg-card p-8 text-center shadow-card"
    >
      <div className="flex justify-center">
        <StatusBadge status={status} className="px-4 py-1.5 text-sm" />
      </div>
      <h1 className="mt-4 font-display text-2xl font-bold sm:text-3xl">{copy.title}</h1>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">{copy.description}</p>

      {(filename || sha256 || communicationId) && (
        <>
          <Separator className="my-6" />
          <div className="grid gap-4 text-left sm:grid-cols-2">
            {filename && (
              <div className="flex items-start gap-2.5 text-sm">
                <FileDigit className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">File</p>
                  <p className="font-medium">{filename}</p>
                </div>
              </div>
            )}
            {communicationId && (
              <div className="flex items-start gap-2.5 text-sm">
                <Building2 className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <div>
                  <p className="text-xs text-muted-foreground">Communication ID</p>
                  <p className="font-mono font-medium">{truncateMiddle(communicationId, 12, 8)}</p>
                </div>
              </div>
            )}
            {sha256 && (
              <div className="flex items-start gap-2.5 text-sm sm:col-span-2">
                <KeyRound className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0">
                  <p className="text-xs text-muted-foreground">SHA-256 Fingerprint</p>
                  <p className="break-all font-mono text-xs font-medium">{sha256}</p>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </motion.div>
  );
}

export function CommunicationSummaryCard({
  title,
  institutionName,
  category,
  createdAt,
  algorithm,
  keyStatus,
  communicationId,
}: {
  title: string;
  institutionName?: string;
  category?: string | null;
  createdAt?: string;
  algorithm?: string;
  keyStatus?: string;
  communicationId: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-display text-lg font-semibold">{title}</h2>
          {institutionName && (
            <p className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground">
              <Building2 className="h-3.5 w-3.5" /> {institutionName}
            </p>
          )}
        </div>
        {keyStatus && <StatusBadge status={keyStatus} />}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
        {category && (
          <div>
            <p className="text-xs text-muted-foreground">Category</p>
            <p className="mt-0.5 font-medium">{category}</p>
          </div>
        )}
        {algorithm && (
          <div>
            <p className="text-xs text-muted-foreground">Algorithm</p>
            <p className="mt-0.5 font-medium">{algorithm}</p>
          </div>
        )}
        {createdAt && (
          <div>
            <p className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" /> Registered
            </p>
            <p className="mt-0.5 font-medium">{formatDateTime(createdAt)}</p>
          </div>
        )}
      </div>

      <Separator className="my-5" />

      <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:items-center">
        <p className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <ShieldCheck className="h-3.5 w-3.5 text-primary" />
          Independently signed &amp; publicly verifiable
        </p>
        <Button variant="outline" size="sm" asChild>
          <Link to={`/verify/communication/${communicationId}`}>
            View full provenance <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>
    </div>
  );
}
