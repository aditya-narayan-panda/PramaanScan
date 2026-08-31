import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Eye, AlertTriangle } from "lucide-react";
import { listCommunications, type ListCommunicationsParams } from "@/api/communications";
import { StatusBadge } from "@/components/common/StatusBadge";
import { PaginationBar } from "@/components/common/PaginationBar";
import { EmptyState } from "@/components/common/EmptyState";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { formatDate, truncateMiddle } from "@/lib/utils";
import { getApiErrorMessage } from "@/api/client";
import { FileStack } from "lucide-react";

export function DocumentsTable({ detailBasePath }: { detailBasePath: string }) {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const params: ListCommunicationsParams = { page, page_size: 10, search: search || undefined };

  const { data, isLoading, error } = useQuery({
    queryKey: ["communications", params],
    queryFn: () => listCommunications(params),
  });

  return (
    <div className="space-y-4">
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search by title…"
          className="pl-9"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(error)}</AlertDescription>
        </Alert>
      )}

      {isLoading && <Skeleton className="h-64 rounded-xl" />}

      {data && data.items.length === 0 && (
        <EmptyState
          icon={<FileStack className="h-6 w-6" />}
          title="No documents yet"
          description="Registered communications will appear here once signed documents are uploaded."
        />
      )}

      {data && data.items.length > 0 && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Registered</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <p className="font-medium">{item.title}</p>
                    <p className="font-mono text-xs text-muted-foreground">{truncateMiddle(item.communication_id, 10, 6)}</p>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{item.category ?? "—"}</TableCell>
                  <TableCell>
                    <StatusBadge status={item.status} />
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDate(item.created_at)}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm" asChild>
                      <Link to={`${detailBasePath}/${item.communication_id}`}>
                        <Eye className="h-3.5 w-3.5" /> View
                      </Link>
                    </Button>
                  </TableCell>
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
