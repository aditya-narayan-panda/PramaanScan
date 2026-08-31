import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Users, AlertTriangle, UserX } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { PaginationBar } from "@/components/common/PaginationBar";
import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { listUsers, createUser, deactivateUser } from "@/api/admin";
import { getApiErrorMessage } from "@/api/client";
import { formatDate } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";

const schema = z
  .object({
    email: z.string().email("Enter a valid email"),
    password: z.string().min(8, "At least 8 characters"),
    full_name: z.string().min(1, "Required"),
    role: z.enum(["ADMIN", "AUTHORITY"]),
    issuer_id: z.coerce.number().int().positive().optional(),
  })
  .refine((data) => data.role !== "AUTHORITY" || data.issuer_id, {
    message: "Issuer ID is required for AUTHORITY users",
    path: ["issuer_id"],
  });
type FormValues = z.infer<typeof schema>;

export default function UserManagementPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["users", page, search],
    queryFn: () => listUsers({ page, page_size: 10, search: search || undefined }),
  });

  const { register, handleSubmit, reset, control, watch, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { role: "AUTHORITY" },
  });
  const role = watch("role");

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      toast({ title: "User created", variant: "success" });
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setDialogOpen(false);
      reset();
    },
    onError: (err) => toast({ title: "Could not create user", description: getApiErrorMessage(err), variant: "destructive" }),
  });

  const deactivateMutation = useMutation({
    mutationFn: deactivateUser,
    onSuccess: () => {
      toast({ title: "User deactivated" });
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => toast({ title: "Could not deactivate user", description: getApiErrorMessage(err), variant: "destructive" }),
  });

  return (
    <div>
      <PageHeader
        title="User Management"
        description="Manage platform users across institutions."
        action={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4" /> New User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add User</DialogTitle>
                <DialogDescription>Create a new Admin or Institution user account.</DialogDescription>
              </DialogHeader>
              <form onSubmit={handleSubmit((v) => createMutation.mutate(v))} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="full_name">Full Name</Label>
                  <Input id="full_name" {...register("full_name")} />
                  {errors.full_name && <p className="text-xs text-destructive">{errors.full_name.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" type="email" {...register("email")} />
                  {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="password">Password</Label>
                  <Input id="password" type="password" {...register("password")} />
                  {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
                </div>
                <div className="space-y-1.5">
                  <Label>Role</Label>
                  <Controller
                    control={control}
                    name="role"
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="AUTHORITY">Institution (AUTHORITY)</SelectItem>
                          <SelectItem value="ADMIN">Administrator</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
                {role === "AUTHORITY" && (
                  <div className="space-y-1.5">
                    <Label htmlFor="issuer_id">Issuer ID</Label>
                    <Input id="issuer_id" type="number" {...register("issuer_id")} />
                    {errors.issuer_id && <p className="text-xs text-destructive">{errors.issuer_id.message}</p>}
                  </div>
                )}
                <DialogFooter>
                  <Button type="submit" loading={createMutation.isPending}>
                    Create User
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      <div className="relative mb-4 max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search users…" className="pl-9" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(error)}</AlertDescription>
        </Alert>
      )}

      {isLoading && <Skeleton className="h-64 rounded-xl" />}

      {data && data.items.length === 0 && (
        <EmptyState icon={<Users className="h-6 w-6" />} title="No users yet" description="Create the first admin or institution user account." />
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-4">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.full_name}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{u.email}</TableCell>
                  <TableCell>
                    <Badge variant={u.role === "ADMIN" ? "accent" : "secondary"}>{u.role}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={u.is_active ? "success" : "destructive"}>{u.is_active ? "Active" : "Inactive"}</Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDate(u.created_at)}</TableCell>
                  <TableCell className="text-right">
                    {u.is_active && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        onClick={() => deactivateMutation.mutate(u.id)}
                        disabled={deactivateMutation.isPending}
                      >
                        <UserX className="h-3.5 w-3.5" /> Deactivate
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
