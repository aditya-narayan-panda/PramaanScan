import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { KeyRound, Ban, Search, AlertTriangle, CheckCircle2 } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { StatusBadge } from "@/components/common/StatusBadge";
import { revokeKey, getKeyStatus } from "@/api/revocation";
import { getApiErrorMessage } from "@/api/client";
import { formatDateTime } from "@/lib/utils";
import { recordActivity } from "@/hooks/useLocalActivity";
import { toast } from "@/hooks/use-toast";

const revokeSchema = z.object({
  key_id: z.string().min(1, "Key ID is required"),
  reason: z.string().min(1, "Please provide a reason"),
});
type RevokeForm = z.infer<typeof revokeSchema>;

export default function KeyManagementPage() {
  const [statusQuery, setStatusQuery] = useState("");

  const {
    register: registerRevoke,
    handleSubmit: handleRevokeSubmit,
    reset: resetRevoke,
    formState: { errors: revokeErrors },
  } = useForm<RevokeForm>({ resolver: zodResolver(revokeSchema) });

  const revokeMutation = useMutation({
    mutationFn: revokeKey,
    onSuccess: (data) => {
      recordActivity("REVOKE_KEY", data.revocation.key_id, "REVOKED");
      toast({ title: "Signing key revoked", description: data.message, variant: "success" });
      resetRevoke();
    },
    onError: (err) => toast({ title: "Could not revoke key", description: getApiErrorMessage(err), variant: "destructive" }),
  });

  const statusMutation = useMutation({ mutationFn: getKeyStatus });

  return (
    <div>
      <PageHeader title="Key Management" description="Revoke compromised signing keys and check any key's live status." />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Ban className="h-4 w-4 text-destructive" /> Revoke Signing Key
            </CardTitle>
            <CardDescription>
              Immediately invalidates a key. All past and future documents signed with it will report
              REVOKED on verification.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRevokeSubmit((v) => revokeMutation.mutate(v))} className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="key_id">Signing Key ID</Label>
                <Input id="key_id" className="font-mono" placeholder="key_..." {...registerRevoke("key_id")} />
                {revokeErrors.key_id && <p className="text-xs text-destructive">{revokeErrors.key_id.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="reason">Reason</Label>
                <Textarea id="reason" className="font-sans" placeholder="e.g. Suspected key compromise" {...registerRevoke("reason")} />
                {revokeErrors.reason && <p className="text-xs text-destructive">{revokeErrors.reason.message}</p>}
              </div>
              <Button type="submit" variant="destructive" loading={revokeMutation.isPending}>
                <Ban className="h-4 w-4" /> Revoke Key
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <KeyRound className="h-4 w-4 text-primary" /> Check Key Status
            </CardTitle>
            <CardDescription>Look up whether any signing key is currently active or revoked.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (statusQuery.trim()) statusMutation.mutate(statusQuery.trim());
              }}
              className="flex gap-2"
            >
              <Input
                className="font-mono"
                placeholder="key_..."
                value={statusQuery}
                onChange={(e) => setStatusQuery(e.target.value)}
              />
              <Button type="submit" loading={statusMutation.isPending} disabled={!statusQuery.trim()}>
                <Search className="h-4 w-4" />
              </Button>
            </form>

            {statusMutation.isError && (
              <Alert variant="destructive">
                <AlertTriangle />
                <AlertDescription>{getApiErrorMessage(statusMutation.error, "Key not found.")}</AlertDescription>
              </Alert>
            )}

            {statusMutation.data && (
              <div className="rounded-xl border border-border bg-secondary/30 p-4">
                <div className="flex items-center justify-between">
                  <p className="font-mono text-sm font-medium">{statusMutation.data.key_id}</p>
                  <StatusBadge status={statusMutation.data.status} />
                </div>
                <dl className="mt-3 space-y-1.5 text-xs">
                  {statusMutation.data.algorithm && (
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Algorithm</dt>
                      <dd className="font-medium">{statusMutation.data.algorithm}</dd>
                    </div>
                  )}
                  {statusMutation.data.created_at && (
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Created</dt>
                      <dd className="font-medium">{formatDateTime(statusMutation.data.created_at)}</dd>
                    </div>
                  )}
                  {statusMutation.data.revoked_at && (
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Revoked</dt>
                      <dd className="font-medium">{formatDateTime(statusMutation.data.revoked_at)}</dd>
                    </div>
                  )}
                  {statusMutation.data.revoked_reason && (
                    <div className="flex justify-between gap-4">
                      <dt className="shrink-0 text-muted-foreground">Reason</dt>
                      <dd className="text-right font-medium">{statusMutation.data.revoked_reason}</dd>
                    </div>
                  )}
                </dl>
              </div>
            )}

            {!statusMutation.data && !statusMutation.isError && (
              <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
                <CheckCircle2 className="h-8 w-8 opacity-30" />
                <p className="mt-2 text-sm">Enter a key ID to check its status</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
