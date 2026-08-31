import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Building2, AlertTriangle, Ban } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { PaginationBar } from "@/components/common/PaginationBar";
import { EmptyState } from "@/components/common/EmptyState";
import { StatusBadge } from "@/components/common/StatusBadge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { listInstitutions, createInstitution, suspendInstitution } from "@/api/admin";
import { getApiErrorMessage } from "@/api/client";
import { formatDate } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

const schema = z.object({
  institution_name: z.string().min(1, "Required").max(255),
  email: z.string().email("Enter a valid email"),
  contact_phone: z.string().max(32).optional(),
});
type FormValues = z.infer<typeof schema>;

export default function InstitutionManagementPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["institutions", page, search],
    queryFn: () => listInstitutions({ page, page_size: 10, search: search || undefined }),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const createMutation = useMutation({
    mutationFn: createInstitution,
    onSuccess: () => {
      toast({ title: "Institution created", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["institutions"] });
      setDialogOpen(false);
      reset();
    },
    onError: (err) => toast({ title: "Could not create institution", description: getApiErrorMessage(err), variant: "destructive" }),
  });

  const suspendMutation = useMutation({
    mutationFn: suspendInstitution,
    onSuccess: () => {
      toast({ title: "Institution suspended" });
      queryClient.invalidateQueries({ queryKey: ["institutions"] });
    },
    onError: (err) => toast({ title: "Could not suspend institution", description: getApiErrorMessage(err), variant: "destructive" }),
  });

  return (
    <div>
      <PageHeader
        title="Institution Management"
        description="Onboard and manage issuing institutions on the platform."
        action={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4" /> New Institution
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Institution</DialogTitle>
                <DialogDescription>Register a new issuing authority on PramaanScan.</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit((v) => createMutation.mutate(v))} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="institution_name">Institution Name</Label>
                  <Input id="institution_name" {...register("institution_name")} />
                  {errors.institution_name && <p className="text-xs text-destructive">{errors.institution_name.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" {...register("email")} />
                  {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="contact_phone">Contact Phone (optional)</Label>
                  <Input id="contact_phone" {...register("contact_phone")} />
                </div>
                <DialogFooter>
                  <Button type="submit" loading={createMutation.isPending}>
                    Create Institution
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="relative mb-4 max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search institutions…" className="pl-9" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(error)}</AlertDescription>
        </Alert>
      )}

      {isLoading && <Skeleton className="h-64 rounded-xl" />}

      {data && data.items.length === 0 && (
        <EmptyState icon={<Building2 className="h-6 w-6" />} title="No institutions yet" description="Add your first institution to start issuing signed communications." />
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Institution</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Onboarded</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((inst) => (
                <TableRow key={inst.id}>
                  <TableCell className="font-medium">{inst.institution_name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{inst.email}</TableCell>
                  <TableCell>
                    <StatusBadge status={inst.status === "ACTIVE" ? "ACTIVE" : "REVOKED"} />
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDate(inst.created_at)}</TableCell>
                  <TableCell className="text-right">
                    {inst.status === "ACTIVE" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => suspendMutation.mutate(inst.id)}
                        disabled={suspendMutation.isPending}
                      >
                        <Ban className="h-3.5 w-3.5" /> Suspend
                      </Button>
                    )}
                  </TableCell>
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
