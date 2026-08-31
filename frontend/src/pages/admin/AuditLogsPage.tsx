import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ClipboardList } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { PaginationBar } from "@/components/common/PaginationBar";
import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { listAuditLogs } from "@/api/logs";
import { getApiErrorMessage } from "@/api/client";
import { formatDateTime } from "@/lib/utils";

export default function AuditLogsPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ["audit-logs", page],
    queryFn: () => listAuditLogs({ page, page_size: 15 }),
  });

  return (
    <div>
      <PageHeader title="Audit Logs" description="A record of administrative and security-relevant actions across the platform." />

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(error)}</AlertDescription>
        </Alert>
      )}

      {isLoading && <Skeleton className="h-64 rounded-xl" />}

      {data && data.items.length === 0 && (
        <EmptyState icon={<ClipboardList className="h-6 w-6" />} title="No audit entries yet" description="Administrative actions like revocations, suspensions, and account changes will appear here." />
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Action</TableHead>
                <TableHead>Resource</TableHead>
                <TableHead>Actor</TableHead>
                <TableHead>When</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((log) => (
                <TableRow key={log.id}>
                  <TableCell>
                    <Badge variant="outline">{log.action}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">
                    <span className="text-muted-foreground">{log.resource_type}</span>
                    {log.resource_id && <span className="ml-1 font-mono text-xs">#{log.resource_id}</span>}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {log.actor_user_id ? `User #${log.actor_user_id}` : "System"}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDateTime(log.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <PaginationBar page={data.page} pages={data.pages} total={data.total} onPageChange={setPage} />
        </div>
      )}
    </div>
  );
}
