import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { UploadCloud, Info, CheckCircle2, KeyRound, ArrowRight } from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { FileDropzone } from "@/components/verification/FileDropzone";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { registerCommunication } from "@/api/communications";
import { getApiErrorMessage } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { sha256File, truncateMiddle } from "@/lib/utils";
import { recordActivity } from "@/hooks/useLocalActivity";
import type { MediaType, RegisterCommunicationResponse } from "@/api/types";

const schema = z.object({
  title: z.string().min(1, "Title is required").max(500),
  description: z.string().max(5000).optional(),
  category: z.string().max(64).optional(),
  media_type: z.enum(["TEXT", "DOCUMENT", "IMAGE", "AUDIO", "VIDEO"]),
  signing_key_id: z.string().min(1, "Signing key ID is required"),
  signature: z.string().min(1, "Signature is required"),
  issuer_id: z.coerce.number().int().positive("Issuer ID is required"),
});

type FormValues = z.infer<typeof schema>;

export default function UploadSignPage() {
  const { user } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [computedHash, setComputedHash] = useState<string | null>(null);
  const [hashing, setHashing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [result, setResult] = useState<RegisterCommunicationResponse | null>(null);

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { media_type: "DOCUMENT", issuer_id: user?.issuer_id ?? undefined },
  });

  const handleFileSelected = async (selected: File) => {
    setFile(selected);
    setHashing(true);
    setComputedHash(null);
    try {
      const hash = await sha256File(selected);
      setComputedHash(hash);
    } finally {
      setHashing(false);
    }
  };

  const onSubmit = async (values: FormValues) => {
    if (!computedHash) {
      setServerError("Select a file first so its SHA-256 fingerprint can be computed.");
      return;
    }
    setServerError(null);
    setSubmitting(true);
    try {
      const response = await registerCommunication({
        issuer_id: values.issuer_id,
        title: values.title,
        description: values.description || null,
        category: values.category || null,
        media_type: values.media_type as MediaType,
        sha256: computedHash,
        signature: values.signature,
        signing_key_id: values.signing_key_id,
        file_name: file?.name ?? null,
        mime_type: file?.type || null,
        file_size_bytes: file?.size ?? null,
      });
      recordActivity("REGISTER_COMMUNICATION", values.title, response.communication.communication_id);
      setResult(response);
    } catch (err) {
      setServerError(getApiErrorMessage(err, "Could not register this communication."));
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <div>
        <PageHeader title="Upload & Sign Documents" />
        <div className="mx-auto max-w-lg rounded-2xl border border-success/30 bg-success/5 p-8 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-success" />
          <h2 className="mt-4 font-display text-xl font-bold">Communication registered</h2>
          <p className="mt-2 text-sm text-muted-foreground">{result.message}</p>
          <div className="mt-5 rounded-xl bg-background p-4 text-left">
            <p className="text-xs text-muted-foreground">Communication ID</p>
            <p className="mt-1 break-all font-mono text-sm font-medium">{result.communication.communication_id}</p>
          </div>
          <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
            <Button variant="outline" onClick={() => setResult(null)}>
              Register Another
            </Button>
            <Button asChild>
              <Link to="/institution/generate-qr" state={{ communicationId: result.communication.communication_id }}>
                Generate QR Code <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Upload & Sign Documents" description="Register a communication that has already been cryptographically signed." />

      <Alert variant="info" className="mb-6">
        <Info />
        <AlertTitle>How signing works on PramaanScan</AlertTitle>
        <AlertDescription>
          Private signing keys never touch this API — signing happens through your institution's
          secure offline process. Select the file below to compute its real SHA-256 fingerprint
          in your browser, then paste in the Ed25519 signature and signing key ID your process
          produced.
        </AlertDescription>
      </Alert>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardContent className="space-y-5 p-6">
            <div>
              <Label className="mb-2 block">Document File</Label>
              <FileDropzone file={file} onFileSelected={handleFileSelected} onClear={() => { setFile(null); setComputedHash(null); }} />
            </div>

            {file && (
              <div className="flex items-center gap-2.5 rounded-lg bg-secondary/50 px-3.5 py-2.5 text-xs">
                <KeyRound className="h-3.5 w-3.5 shrink-0 text-primary" />
                {hashing ? (
                  <span className="text-muted-foreground">Computing SHA-256 fingerprint…</span>
                ) : (
                  <span className="font-mono">{computedHash ? truncateMiddle(computedHash, 16, 12) : "—"}</span>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-5 p-6">
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="title">Title</Label>
                <Input id="title" placeholder="e.g. Public Notice — Admission Results 2026" {...register("title")} />
                {errors.title && <p className="text-xs text-destructive">{errors.title.message}</p>}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="category">Category</Label>
                <Input id="category" placeholder="e.g. Notice, Certificate, Press Release" {...register("category")} />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" className="font-sans" placeholder="Optional context for this communication" {...register("description")} />
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Media Type</Label>
                <Controller
                  control={control}
                  name="media_type"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {["TEXT", "DOCUMENT", "IMAGE", "AUDIO", "VIDEO"].map((t) => (
                          <SelectItem key={t} value={t}>
                            {t}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="issuer_id">Issuer ID</Label>
                <Input id="issuer_id" type="number" {...register("issuer_id")} />
                {errors.issuer_id && <p className="text-xs text-destructive">{errors.issuer_id.message}</p>}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="space-y-5 p-6">
            <h3 className="font-display text-sm font-semibold">Cryptographic Provenance</h3>
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="signing_key_id">Signing Key ID</Label>
                <Input id="signing_key_id" className="font-mono" placeholder="key_..." {...register("signing_key_id")} />
                {errors.signing_key_id && <p className="text-xs text-destructive">{errors.signing_key_id.message}</p>}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="signature">Ed25519 Signature (base64)</Label>
              <Textarea id="signature" placeholder="Signature produced offline over the SHA-256 fingerprint" {...register("signature")} />
              {errors.signature && <p className="text-xs text-destructive">{errors.signature.message}</p>}
            </div>
          </CardContent>
        </Card>

        {serverError && (
          <Alert variant="destructive">
            <Info />
            <AlertDescription>{serverError}</AlertDescription>
          </Alert>
        )}

        <Button type="submit" size="lg" loading={submitting} disabled={!computedHash}>
          <UploadCloud className="h-4 w-4" />
          Register Signed Communication
        </Button>
      </form>
    </div>
  );
}
