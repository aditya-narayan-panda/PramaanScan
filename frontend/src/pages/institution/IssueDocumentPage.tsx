import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQuery } from "@tanstack/react-query";
import {
  UploadCloud,
  CheckCircle2,
  KeyRound,
  ArrowRight,
  FileText,
  User,
  Hash,
  Shield,
  ChevronRight,
  ChevronLeft,
  Loader2,
  Info,
  QrCode,
} from "lucide-react";
import { PageHeader } from "@/components/common/PageHeader";
import { FileDropzone } from "@/components/verification/FileDropzone";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { getApiErrorMessage, apiClient } from "@/api/client";
import { useAuth } from "@/context/AuthContext";
import { recordActivity } from "@/hooks/useLocalActivity";
import { cn } from "@/lib/utils";

const STEPS = [
  { id: 1, title: "Upload Document", icon: UploadCloud },
  { id: 2, title: "Document Details", icon: FileText },
  { id: 3, title: "Signing Key", icon: KeyRound },
  { id: 4, title: "Review & Issue", icon: Shield },
];

interface SigningKey {
  id: number;
  key_id: string;
  algorithm: string;
  status: string;
  created_at: string;
}

interface IssueResult {
  success: boolean;
  message: string;
  communication: {
    communication_id: string;
    title: string;
    media_type: string;
    issuer: string;
    issuer_id: number;
  };
  cryptographic_provenance: {
    sha256: string;
    signature_valid: boolean;
    algorithm: string;
    signing_key_id: string;
    key_status: string;
  };
  qr: {
    verification_url: string;
    qr_image_url: string;
  };
}

const step2Schema = z.object({
  title: z.string().min(1, "Title is required").max(500),
  description: z.string().max(5000).optional(),
  category: z.string().max(64).optional(),
  media_type: z.enum(["TEXT", "DOCUMENT", "IMAGE", "AUDIO", "VIDEO"]),
  student_name: z.string().max(255).optional(),
  student_id: z.string().max(64).optional(),
  course: z.string().max(128).optional(),
  department: z.string().max(128).optional(),
  document_type: z.string().max(64).optional(),
});

type Step2Values = z.infer<typeof step2Schema>;

export default function IssueDocumentPage() {
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [selectedKeyId, setSelectedKeyId] = useState<string>("");
  const [step2Values, setStep2Values] = useState<Step2Values | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [result, setResult] = useState<IssueResult | null>(null);

  const issuerId = user?.issuer_id;

  const { data: keysData, isLoading: keysLoading } = useQuery({
    queryKey: ["signing-keys", issuerId],
    queryFn: async () => {
      const { data } = await apiClient.get("/revocation/keys");
      return data as { items: SigningKey[] };
    },
    enabled: !!issuerId,
  });

  const activeKeys = keysData?.items?.filter((k) => k.status === "ACTIVE") ?? [];

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<Step2Values>({
    resolver: zodResolver(step2Schema),
    defaultValues: { media_type: "DOCUMENT" },
  });

  const currentMediaType = watch("media_type");

  const handleFileSelected = (f: File) => {
    setFile(f);
  };

  const handleStep2Submit = (values: Step2Values) => {
    setStep2Values(values);
    setStep(3);
  };

  const handleIssue = async () => {
    if (!file || !step2Values || !selectedKeyId || !issuerId) return;
    setServerError(null);
    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("issuer_id", String(issuerId));
      formData.append("signing_key_id", selectedKeyId);
      formData.append("title", step2Values.title);
      if (step2Values.description) formData.append("description", step2Values.description);
      if (step2Values.category) formData.append("category", step2Values.category);
      formData.append("media_type", step2Values.media_type);
      if (step2Values.student_name) formData.append("student_name", step2Values.student_name);
      if (step2Values.student_id) formData.append("student_id", step2Values.student_id);
      if (step2Values.course) formData.append("course", step2Values.course);
      if (step2Values.department) formData.append("department", step2Values.department);
      if (step2Values.document_type) formData.append("document_type", step2Values.document_type);

      const { data } = await apiClient.post<IssueResult>("/documents/issue", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      recordActivity("ISSUE_DOCUMENT", step2Values.title, data.communication.communication_id);
      setResult(data);
      setStep(4);
    } catch (err) {
      setServerError(getApiErrorMessage(err, "Failed to issue document."));
    } finally {
      setSubmitting(false);
    }
  };

  if (result) {
    return (
      <div>
        <PageHeader title="Issue Document" />
        <div className="mx-auto max-w-2xl space-y-6">
          <div className="rounded-2xl border border-success/30 bg-success/5 p-8 text-center">
            <CheckCircle2 className="mx-auto h-12 w-12 text-success" />
            <h2 className="mt-4 font-display text-2xl font-bold">Document Issued Successfully</h2>
            <p className="mt-2 text-sm text-muted-foreground">{result.message}</p>
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="h-4 w-4 text-success" />
                Cryptographic Provenance
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-lg bg-secondary/40 p-4 font-mono text-xs">
                <div className="flex justify-between gap-4">
                  <span className="text-muted-foreground shrink-0">SHA-256</span>
                  <span className="break-all text-right">{result.cryptographic_provenance.sha256}</span>
                </div>
                <div className="mt-2 flex justify-between gap-4">
                  <span className="text-muted-foreground shrink-0">Algorithm</span>
                  <span>{result.cryptographic_provenance.algorithm}</span>
                </div>
                <div className="mt-2 flex justify-between gap-4">
                  <span className="text-muted-foreground shrink-0">Signing Key</span>
                  <span>{result.cryptographic_provenance.signing_key_id}</span>
                </div>
                <div className="mt-2 flex justify-between gap-4">
                  <span className="text-muted-foreground shrink-0">Signature Valid</span>
                  <span className="text-success">{result.cryptographic_provenance.signature_valid ? "✓ Yes" : "✗ No"}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <QrCode className="h-4 w-4 text-primary" />
                QR Code & Verification
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-center">
                <img
                  src={result.qr.qr_image_url}
                  alt="QR Code"
                  className="h-48 w-48 rounded-xl border border-border"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              </div>
              <div className="rounded-lg bg-secondary/40 p-3 text-xs">
                <p className="text-muted-foreground mb-1">Verification URL</p>
                <p className="font-mono break-all">{result.qr.verification_url}</p>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => {
                setResult(null);
                setFile(null);
                setStep2Values(null);
                setSelectedKeyId("");
                setStep(1);
              }}
            >
              Issue Another Document
            </Button>
            <Button asChild>
              <Link
                to="/institution/generate-qr"
                state={{ communicationId: result.communication.communication_id }}
              >
                <QrCode className="h-4 w-4" />
                Generate QR Code
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title="Issue Document"
        description="Upload a document, add details, and sign it cryptographically — all in one workflow."
      />

      {/* Step indicator */}
      <div className="mb-8 flex items-center gap-0">
        {STEPS.slice(0, 3).map((s, i) => (
          <div key={s.id} className="flex items-center">
            <button
              onClick={() => step > s.id && setStep(s.id)}
              className={cn(
                "flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium transition-colors",
                step === s.id && "bg-primary/10 text-primary",
                step > s.id && "cursor-pointer text-muted-foreground hover:text-foreground",
                step < s.id && "text-muted-foreground/40"
              )}
            >
              <div
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold",
                  step === s.id && "bg-primary text-primary-foreground",
                  step > s.id && "bg-success text-white",
                  step < s.id && "bg-muted text-muted-foreground"
                )}
              >
                {step > s.id ? "✓" : s.id}
              </div>
              <span className="hidden sm:block">{s.title}</span>
            </button>
            {i < 2 && <ChevronRight className="h-4 w-4 text-muted-foreground/30" />}
          </div>
        ))}
      </div>

      {/* STEP 1: Upload */}
      {step === 1 && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <UploadCloud className="h-4 w-4 text-primary" />
                Upload Document
              </CardTitle>
            </CardHeader>
            <CardContent>
              <FileDropzone
                file={file}
                onFileSelected={handleFileSelected}
                onClear={() => setFile(null)}
                hint="PDF, image, audio, or video file"
              />
              {file && (
                <div className="mt-4 rounded-lg border border-success/30 bg-success/5 px-4 py-3 text-sm">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-success" />
                    <span className="font-medium">{file.name}</span>
                    <span className="text-muted-foreground">
                      ({(file.size / 1024).toFixed(1)} KB)
                    </span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Alert variant="info">
            <Info />
            <AlertTitle>Automatic cryptographic signing</AlertTitle>
            <AlertDescription>
              SHA-256 and Ed25519 signing happen automatically — you never need to handle
              cryptographic values manually.
            </AlertDescription>
          </Alert>

          <Button
            size="lg"
            disabled={!file}
            onClick={() => setStep(2)}
            className="w-full sm:w-auto"
          >
            Continue to Document Details
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* STEP 2: Details */}
      {step === 2 && (
        <form onSubmit={handleSubmit(handleStep2Submit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-4 w-4 text-primary" />
                Document Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="title">Title *</Label>
                  <Input
                    id="title"
                    placeholder="e.g. Bonafide Certificate — 2024"
                    {...register("title")}
                  />
                  {errors.title && (
                    <p className="text-xs text-destructive">{errors.title.message}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    placeholder="e.g. Certificate, Notice, Transcript"
                    {...register("category")}
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  className="font-sans"
                  placeholder="Optional: additional context for this document"
                  {...register("description")}
                />
              </div>

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
                        {["DOCUMENT", "IMAGE", "AUDIO", "VIDEO", "TEXT"].map((t) => (
                          <SelectItem key={t} value={t}>
                            {t}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <User className="h-4 w-4 text-primary" />
                Recipient / Student Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-5 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="student_name">Student Name</Label>
                  <Input id="student_name" placeholder="Full name" {...register("student_name")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="student_id">Student ID / Roll Number</Label>
                  <Input id="student_id" placeholder="e.g. 2024BCS001" {...register("student_id")} />
                </div>
              </div>
              <div className="grid gap-5 sm:grid-cols-3">
                <div className="space-y-1.5">
                  <Label htmlFor="course">Course</Label>
                  <Input id="course" placeholder="e.g. B.Tech CSE" {...register("course")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="department">Department</Label>
                  <Input id="department" placeholder="e.g. Computer Science" {...register("department")} />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="document_type">Document Type</Label>
                  <Input
                    id="document_type"
                    placeholder="e.g. Bonafide, Degree"
                    {...register("document_type")}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex gap-3">
            <Button variant="outline" type="button" onClick={() => setStep(1)}>
              <ChevronLeft className="h-4 w-4" />
              Back
            </Button>
            <Button type="submit" size="lg">
              Continue to Signing Key
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </form>
      )}

      {/* STEP 3: Key selection + review + issue */}
      {step === 3 && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <KeyRound className="h-4 w-4 text-primary" />
                Select Signing Key
              </CardTitle>
            </CardHeader>
            <CardContent>
              {keysLoading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading signing keys…
                </div>
              ) : activeKeys.length === 0 ? (
                <Alert variant="warning">
                  <Info />
                  <AlertTitle>No active signing keys</AlertTitle>
                  <AlertDescription>
                    Your institution has no active signing keys. Ask your administrator to generate one, or{" "}
                    <Link to="/institution/profile" className="underline">
                      generate one from your profile
                    </Link>
                    .
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-2">
                  {activeKeys.map((key) => (
                    <button
                      key={key.key_id}
                      type="button"
                      onClick={() => setSelectedKeyId(key.key_id)}
                      className={cn(
                        "w-full rounded-xl border px-4 py-3 text-left text-sm transition-colors",
                        selectedKeyId === key.key_id
                          ? "border-primary/40 bg-primary/5"
                          : "border-border hover:border-primary/20 hover:bg-secondary/40"
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-mono font-medium">{key.key_id}</p>
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {key.algorithm} · Created{" "}
                            {new Date(key.created_at).toLocaleDateString()}
                          </p>
                        </div>
                        <div
                          className={cn(
                            "rounded-full px-2 py-0.5 text-xs font-medium",
                            key.status === "ACTIVE"
                              ? "bg-success/15 text-success"
                              : "bg-destructive/15 text-destructive"
                          )}
                        >
                          {key.status}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Summary */}
          {step2Values && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Hash className="h-4 w-4 text-primary" />
                  Issue Summary
                </CardTitle>
              </CardHeader>
              <CardContent>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">File</dt>
                    <dd className="font-medium">{file?.name}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Title</dt>
                    <dd className="font-medium">{step2Values.title}</dd>
                  </div>
                  {step2Values.student_name && (
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Student</dt>
                      <dd className="font-medium">{step2Values.student_name}</dd>
                    </div>
                  )}
                  {step2Values.document_type && (
                    <div className="flex justify-between">
                      <dt className="text-muted-foreground">Type</dt>
                      <dd className="font-medium">{step2Values.document_type}</dd>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Signing Key</dt>
                    <dd className="font-mono text-xs">{selectedKeyId || "(not selected)"}</dd>
                  </div>
                </dl>

                <Alert variant="info" className="mt-5">
                  <Shield />
                  <AlertDescription>
                    The SHA-256 fingerprint and Ed25519 signature will be computed automatically.
                    No cryptographic values need to be entered manually.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          )}

          {serverError && (
            <Alert variant="destructive">
              <Info />
              <AlertDescription>{serverError}</AlertDescription>
            </Alert>
          )}

          <div className="flex gap-3">
            <Button variant="outline" type="button" onClick={() => setStep(2)}>
              <ChevronLeft className="h-4 w-4" />
              Back
            </Button>
            <Button
              size="lg"
              loading={submitting}
              disabled={!selectedKeyId || submitting}
              onClick={handleIssue}
            >
              <Shield className="h-4 w-4" />
              Sign & Issue Document
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
