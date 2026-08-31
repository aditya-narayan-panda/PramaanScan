/**
 * Institution Key Management Page
 *
 * Allows authority users to:
 * 1. View all their institution's signing keys (active and revoked)
 * 2. Generate new Ed25519 keypairs (server-side, private key never exposed)
 * 3. Revoke compromised keys with a reason
 */

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  KeyRound,
  Plus,
  Ban,
  ShieldCheck,
  ShieldOff,
  Copy,
  Check,
  Loader2,
  AlertTriangle,
  Info,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { apiClient, getApiErrorMessage } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { formatDateTime } from "@/lib/utils";
import { toast } from "@/hooks/use-toast";
import { recordActivity } from "@/hooks/useLocalActivity";
import { cn } from "@/lib/utils";

interface SigningKey {
  id: number;
  key_id: string;
  issuer_id: number;
  algorithm: string;
  status: "ACTIVE" | "REVOKED";
  public_key?: string;
  created_at: string;
  revoked_at?: string;
  revoked_reason?: string;
}

function CopyButton({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(value).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1800);
        });
      }}
      className="ml-1 inline-flex items-center text-muted-foreground hover:text-foreground transition-colors"
    >
      {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  );
}

export default function InstitutionKeyManagementPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [revokeTarget, setRevokeTarget] = useState<SigningKey | null>(null);
  const [revokeReason, setRevokeReason] = useState("");

  const issuerId = user?.issuer_id;

  const {
    data: keysData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["signing-keys", issuerId],
    queryFn: async () => {
      const { data } = await apiClient.get("/revocation/keys");
      return data as { items: SigningKey[] };
    },
    enabled: !!issuerId,
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append("issuer_id", String(issuerId));
      formData.append("label", "Authority Key");
      const { data } = await apiClient.post("/documents/keys/generate", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data as {
        key: SigningKey & { public_key: string };
        message: string;
      };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["signing-keys"] });
      recordActivity("GENERATE_KEY", data.key.key_id, "ACTIVE");
      toast({
        title: "Signing key generated",
        description: data.message,
        variant: "success",
      });
    },
    onError: (err) =>
      toast({
        title: "Failed to generate key",
        description: getApiErrorMessage(err),
        variant: "destructive",
      }),
  });

  const revokeMutation = useMutation({
    mutationFn: async ({ key_id, reason }: { key_id: string; reason: string }) => {
      const { data } = await apiClient.post("/revocation/key", { key_id, reason });
      return data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["signing-keys"] });
      recordActivity("REVOKE_KEY", variables.key_id, "REVOKED");
      toast({
        title: "Signing key revoked",
        description: "The key has been revoked. All documents signed with it will show REVOKED.",
        variant: "success",
      });
      setRevokeTarget(null);
      setRevokeReason("");
    },
    onError: (err) =>
      toast({
        title: "Could not revoke key",
        description: getApiErrorMessage(err),
        variant: "destructive",
      }),
  });

  const keys = keysData?.items ?? [];
  const activeKeys = keys.filter((k) => k.status === "ACTIVE");
  const revokedKeys = keys.filter((k) => k.status === "REVOKED");

  return (
    <div>
      <PageHeader
        title="Signing Key Management"
        description="Manage your institution's Ed25519 signing keys. Generate new keys or revoke compromised ones."
        action={
          <Button
            loading={generateMutation.isPending}
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
          >
            <Plus className="h-4 w-4" />
            Generate New Key
          </Button>
        }
      />

      <Alert variant="info" className="mb-6">
        <ShieldCheck />
        <AlertDescription>
          Private keys are generated and stored server-side, encrypted at rest. They are{" "}
          <strong>never exposed through the API</strong>. Only the public key is shown here.
        </AlertDescription>
      </Alert>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(error)}</AlertDescription>
        </Alert>
      )}

      {isLoading ? (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading signing keys…
        </div>
      ) : (
        <div className="space-y-8">
          {/* Active Keys */}
          <div>
            <h2 className="mb-4 font-display text-sm font-semibold text-success flex items-center gap-2">
              <ShieldCheck className="h-4 w-4" />
              Active Keys ({activeKeys.length})
            </h2>
            {activeKeys.length === 0 ? (
              <Card>
                <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                  <KeyRound className="h-10 w-10 text-muted-foreground/40" />
                  <p className="mt-3 text-sm text-muted-foreground">
                    No active signing keys. Generate one to start issuing documents.
                  </p>
                  <Button
                    className="mt-4"
                    loading={generateMutation.isPending}
                    onClick={() => generateMutation.mutate()}
                  >
                    <Plus className="h-4 w-4" />
                    Generate Ed25519 Key
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-3">
                {activeKeys.map((key) => (
                  <Card key={key.key_id}>
                    <CardContent className="p-5">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-mono text-sm font-semibold">{key.key_id}</p>
                            <CopyButton value={key.key_id} />
                            <Badge variant="success" className="ml-2">
                              ACTIVE
                            </Badge>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {key.algorithm} · Created {formatDateTime(key.created_at)}
                          </p>
                        </div>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => setRevokeTarget(key)}
                        >
                          <Ban className="h-3.5 w-3.5" />
                          Revoke
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>

          {/* Revoke Confirmation */}
          {revokeTarget && (
            <Card className="border-destructive/30 bg-destructive/5">
              <CardHeader>
                <CardTitle className="text-base text-destructive flex items-center gap-2">
                  <Ban className="h-4 w-4" />
                  Revoke Key: {revokeTarget.key_id}
                </CardTitle>
                <CardDescription>
                  This action is irreversible. All documents signed with this key will show{" "}
                  <strong>REVOKED</strong> on verification.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="revoke-reason">Reason for revocation *</Label>
                  <Textarea
                    id="revoke-reason"
                    placeholder="e.g. Suspected key compromise, staff change, routine rotation"
                    value={revokeReason}
                    onChange={(e) => setRevokeReason(e.target.value)}
                  />
                </div>
                <div className="flex gap-3">
                  <Button
                    variant="destructive"
                    loading={revokeMutation.isPending}
                    disabled={!revokeReason.trim() || revokeMutation.isPending}
                    onClick={() =>
                      revokeMutation.mutate({
                        key_id: revokeTarget.key_id,
                        reason: revokeReason,
                      })
                    }
                  >
                    Confirm Revocation
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setRevokeTarget(null);
                      setRevokeReason("");
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Revoked Keys */}
          {revokedKeys.length > 0 && (
            <div>
              <h2 className="mb-4 font-display text-sm font-semibold text-muted-foreground flex items-center gap-2">
                <ShieldOff className="h-4 w-4" />
                Revoked Keys ({revokedKeys.length})
              </h2>
              <div className="space-y-3">
                {revokedKeys.map((key) => (
                  <Card key={key.key_id} className="opacity-70">
                    <CardContent className="p-5">
                      <div className="flex items-start gap-4">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="font-mono text-sm font-semibold line-through text-muted-foreground">
                              {key.key_id}
                            </p>
                            <Badge variant="destructive">REVOKED</Badge>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {key.algorithm} · Created {formatDateTime(key.created_at)}
                          </p>
                          {key.revoked_at && (
                            <p className="mt-0.5 text-xs text-destructive">
                              Revoked: {formatDateTime(key.revoked_at)}
                            </p>
                          )}
                          {key.revoked_reason && (
                            <p className="mt-1 text-xs text-muted-foreground">
                              Reason: {key.revoked_reason}
                            </p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
