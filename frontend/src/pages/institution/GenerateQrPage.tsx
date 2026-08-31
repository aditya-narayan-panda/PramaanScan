import { useState } from "react";
import { useLocation } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { QrCode, Search, AlertTriangle } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { QrCodeDisplay } from "@/components/qr/QrCodeDisplay";
import { getQrData } from "@/api/qr";
import { getApiErrorMessage } from "@/api/client";
import { recordActivity } from "@/hooks/useLocalActivity";

export default function GenerateQrPage() {
  const location = useLocation();
  const prefill = (location.state as { communicationId?: string } | null)?.communicationId ?? "";
  const [communicationId, setCommunicationId] = useState(prefill);

  const mutation = useMutation({
    mutationFn: (id: string) => getQrData(id),
    onSuccess: (data, id) => recordActivity("LOOKUP_COMMUNICATION", id, "qr-generated"),
  });

  return (
    <div>
      <PageHeader title="Generate QR" description="Create a scannable QR code for one of your registered communications." />

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardContent className="p-6">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (communicationId.trim()) mutation.mutate(communicationId.trim());
              }}
              className="space-y-4"
            >
              <div className="space-y-1.5">
                <Label htmlFor="comm-id">Communication ID</Label>
                <Input
                  id="comm-id"
                  className="font-mono"
                  placeholder="Paste a Communication ID"
                  value={communicationId}
                  onChange={(e) => setCommunicationId(e.target.value)}
                />
              </div>
              <Button type="submit" loading={mutation.isPending} disabled={!communicationId.trim()}>
                <Search className="h-4 w-4" />
                Generate QR Code
              </Button>
            </form>

            {mutation.isError && (
              <Alert variant="destructive" className="mt-5">
                <AlertTriangle />
                <AlertDescription>{getApiErrorMessage(mutation.error, "Communication not found.")}</AlertDescription>
              </Alert>
            )}

            <p className="mt-6 text-xs leading-relaxed text-muted-foreground">
              The QR code encodes a public verification link. Anyone who scans it lands directly
              on this communication's verification result — no login required.
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="flex min-h-[320px] items-center justify-center p-6">
            {mutation.data ? (
              <QrCodeDisplay
                value={mutation.data.verification_url}
                filename={`pramaanscan-${mutation.data.communication_id}`}
              />
            ) : (
              <div className="flex flex-col items-center text-center text-muted-foreground">
                <QrCode className="h-10 w-10 opacity-30" />
                <p className="mt-3 text-sm">Your QR code will appear here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
