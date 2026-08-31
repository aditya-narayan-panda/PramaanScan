import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ScrollText } from "lucide-react";
import { listVerificationLogs } from "@/api/logs";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PaginationBar } from "@/components/common/PaginationBar";
import { EmptyState } from "@/components/common/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatDateTime, truncateMiddle } from "@/lib/utils";
import { getApiErrorMessage } from "@/api/client";

export function VerificationLogsTable() {
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ["verification-logs", page],
    queryFn: () => listVerificationLogs({ page, page_size: 15 }),
  });

  return (
    <div className="space-y-4">
      {error && (
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(error)}</AlertDescription>
        </Alert>
      )}

      {isLoading && <Skeleton className="h-64 rounded-xl" />}

      {data && data.items.length === 0 && (
        <EmptyState
          icon={<ScrollText className="h-6 w-6" />}
          title="No verification attempts yet"
          description="Every time someone verifies one of your documents — via QR, code, or file upload — it will be logged here."
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Result</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Communication</TableHead>
                <TableHead>SHA-256</TableHead>
                <TableHead>When</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>
                    <StatusBadge status={log.result} />
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">{log.source.replace("_", " ")}</Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {log.communication_id ? truncateMiddle(log.communication_id, 8, 6) : "—"}
                  </TableCell>
                  <TableCell className="font-mono text-xs text-muted-foreground">
                    {truncateMiddle(log.sha256, 8, 6)}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDateTime(log.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <PaginationBar page={data.page} pages={data.pages} total={data.total} onPageChange={setPage} />
        </>
      )}
    </div>
  );
}
