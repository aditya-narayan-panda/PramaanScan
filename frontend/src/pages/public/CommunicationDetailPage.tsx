import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Building2, History, Loader2, AlertTriangle } from "lucide-react";
import { getCommunication } from "@/api/communications";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Separator } from "@/components/ui/separator";
import { formatDateTime, truncateMiddle } from "@/lib/utils";
import { getApiErrorMessage } from "@/api/client";

export default function CommunicationDetailPage() {
  const { communicationId = "" } = useParams();

  const { data, isLoading, error } = useQuery({
    queryKey: ["communication", communicationId],
    queryFn: () => getCommunication(communicationId),
    enabled: Boolean(communicationId),
  });

  return (
    <div className="container max-w-3xl py-12 sm:py-16">
      <Link
        to="/verify"
        className="mb-6 flex w-fit items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Verify
      </Link>

      {isLoading && (
        <div className="flex items-center justify-center py-24 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(error, "Communication not found.")}</AlertDescription>
        </Alert>
      )}

      {data && (
        <div className="space-y-6">
          <div className="rounded-2xl border border-border bg-card p-6">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="font-display text-xl font-bold">{data.title}</h1>
                <p className="mt-1.5 flex items-center gap-1.5 text-sm text-muted-foreground">
                  <Building2 className="h-3.5 w-3.5" /> {data.issuer.institution_name}
                </p>
              </div>
              <StatusBadge status={data.status} />
            </div>
            {data.description && <p className="mt-4 text-sm text-muted-foreground">{data.description}</p>}
            <Separator className="my-5" />
            <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              <div>
                <dt className="text-xs text-muted-foreground">Communication ID</dt>
                <dd className="mt-0.5 break-all font-mono text-xs font-medium">
                  {truncateMiddle(data.communication_id, 14, 10)}
                </dd>
              </div>
              {data.category && (
                <div>
                  <dt className="text-xs text-muted-foreground">Category</dt>
                  <dd className="mt-0.5 font-medium">{data.category}</dd>
                </div>
              )}
              <div>
                <dt className="text-xs text-muted-foreground">Media Type</dt>
                <dd className="mt-0.5 font-medium">{data.media_type}</dd>
              </div>
              {data.valid_from && (
                <div>
                  <dt className="text-xs text-muted-foreground">Valid From</dt>
                  <dd className="mt-0.5 font-medium">{formatDateTime(data.valid_from)}</dd>
                </div>
              )}
              {data.valid_until && (
                <div>
                  <dt className="text-xs text-muted-foreground">Valid Until</dt>
                  <dd className="mt-0.5 font-medium">{formatDateTime(data.valid_until)}</dd>
                </div>
              )}
            </dl>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6">
            <div className="mb-4 flex items-center gap-2">
              <History className="h-4 w-4 text-primary" />
              <h2 className="font-display text-sm font-semibold">
                Version History ({data.versions.length})
              </h2>
            </div>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Ver</TableHead>
                  <TableHead>SHA-256</TableHead>
                  <TableHead>Key Status</TableHead>
                  <TableHead>Registered</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.versions.map((v) => (
                  <TableRow key={v.version_id} className={v.version_id === data.current_version_id ? "bg-primary/5" : ""}>
                    <TableCell className="font-medium">
                      v{v.version}
                      {v.version_id === data.current_version_id && (
                        <span className="ml-1.5 text-[10px] font-semibold uppercase text-primary">current</span>
                      )}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{truncateMiddle(v.sha256, 8, 6)}</TableCell>
                    <TableCell>
                      <StatusBadge status={v.key_status} />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">{formatDateTime(v.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  );
}
