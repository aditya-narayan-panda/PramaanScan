import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { QrCode, FileUp, Hash, Loader2, AlertTriangle, ShieldCheck, LockKeyhole, CheckCircle2, Info } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { FileDropzone } from "@/components/verification/FileDropzone";
import { QrScanner } from "@/components/qr/QrScanner";
import { verifyFile, resolveCommunication } from "@/api/verification";
import { getApiErrorMessage } from "@/api/client";
import { recordActivity } from "@/hooks/useLocalActivity";

function extractCommunicationId(raw: string): string {
  const trimmed = raw.trim();
  try { const url = new URL(trimmed); const parts = url.pathname.split("/").filter(Boolean); return parts[parts.length - 1] || trimmed; } catch { return trimmed; }
}

export default function VerifyPage() {
  const [searchParams] = useSearchParams();
  const initialTab = searchParams.get("tab") ?? "upload";
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scannerActive, setScannerActive] = useState(initialTab === "qr");

  const handleFileVerify = async () => {
    if (!file) return;
    setError(null); setLoading(true);
    try { const result = await verifyFile(file); recordActivity("VERIFY_FILE", file.name, result.status); navigate("/verify/result", { state: { source: "file", result, filename: file.name } }); }
    catch (err) { setError(getApiErrorMessage(err, "Could not verify this file. Please try again.")); }
    finally { setLoading(false); }
  };

  const handleCodeVerify = async (rawCode: string) => {
    const communicationId = extractCommunicationId(rawCode); if (!communicationId) return;
    setError(null); setLoading(true);
    try { const result = await resolveCommunication(communicationId); recordActivity("VERIFY_CODE", communicationId, "identified"); navigate("/verify/result", { state: { source: "code", result, communicationId } }); }
    catch (err) { setError(getApiErrorMessage(err, "No communication was found for that code.")); }
    finally { setLoading(false); }
  };

  const handleQrDecode = (value: string) => { setScannerActive(false); void handleCodeVerify(value); };

  return <div className="relative min-h-full bg-[radial-gradient(circle_at_50%_0%,hsl(var(--primary)/.08),transparent_35%)]">
    <div className="container max-w-5xl py-12 sm:py-16">
      <div className="mx-auto max-w-3xl text-center"><div className="mx-auto inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/5 px-3.5 py-1.5 text-xs font-bold text-primary"><ShieldCheck className="h-4 w-4"/> Citizen verification service</div><h1 className="mt-5 font-display text-4xl font-extrabold tracking-tight sm:text-5xl">Verify a Document</h1><p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-muted-foreground">Scan a QR code, upload the original file, or enter a verification code. PramaanScan checks cryptographic authenticity first and shows advisory media analysis separately.</p></div>
      <div className="mx-auto mt-10 max-w-3xl">
        <div className="grid gap-3 sm:grid-cols-3">
          {[ ["1","Choose input"],["2","Verify evidence"],["3","Review result"] ].map(([n,t])=><div key={n} className="flex items-center gap-3 rounded-xl border border-border bg-card p-3"><span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-xs font-bold text-primary-foreground">{n}</span><span className="text-xs font-semibold">{t}</span></div>)}
        </div>
        <div className="mt-5 rounded-2xl border border-border bg-card p-4 shadow-card sm:p-6">
          <Tabs defaultValue={initialTab === "qr" || initialTab === "code" ? initialTab : "upload"} onValueChange={(v) => setScannerActive(v === "qr")} className="w-full">
            <TabsList className="mx-auto grid h-12 w-full max-w-lg grid-cols-3 bg-secondary/80 p-1"><TabsTrigger value="qr" className="gap-2"><QrCode className="h-4 w-4"/> Scan QR</TabsTrigger><TabsTrigger value="upload" className="gap-2"><FileUp className="h-4 w-4"/> Upload</TabsTrigger><TabsTrigger value="code" className="gap-2"><Hash className="h-4 w-4"/> Code</TabsTrigger></TabsList>
            {error && <Alert variant="destructive" className="mt-5"><AlertTriangle/><AlertDescription>{error}</AlertDescription></Alert>}
            <TabsContent value="qr" className="mt-6"><QrScanner active={scannerActive} onDecode={handleQrDecode}/>{loading && <div className="mt-4 flex items-center justify-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin"/> Resolving registered communication…</div>}</TabsContent>
            <TabsContent value="upload" className="mt-6"><div className="space-y-5"><FileDropzone file={file} onFileSelected={setFile} onClear={() => setFile(null)} hint="Documents, images, audio and video files are supported"/><Button className="w-full shadow-glow" size="lg" disabled={!file} loading={loading} onClick={handleFileVerify}><ShieldCheck className="h-5 w-5"/> Verify This File</Button></div></TabsContent>
            <TabsContent value="code" className="mt-6"><form className="space-y-5" onSubmit={(e) => { e.preventDefault(); void handleCodeVerify(code); }}><div className="space-y-2"><Label htmlFor="code">Verification Code / Communication ID</Label><Input id="code" placeholder="Paste the code or QR verification link" value={code} onChange={(e) => setCode(e.target.value)} className="h-12 font-mono"/><p className="flex items-center gap-1.5 text-xs text-muted-foreground"><Info className="h-3.5 w-3.5"/> You can paste the full verification URL too.</p></div><Button type="submit" className="w-full shadow-glow" size="lg" disabled={!code.trim()} loading={loading}><SearchIcon/> Verify Code</Button></form></TabsContent>
          </Tabs>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-3"><div className="flex gap-3 rounded-xl border border-border bg-card p-4"><LockKeyhole className="h-5 w-5 shrink-0 text-primary"/><div><p className="text-xs font-bold">Cryptographic first</p><p className="mt-1 text-[11px] leading-5 text-muted-foreground">SHA-256 + digital signature determine authenticity.</p></div></div><div className="flex gap-3 rounded-xl border border-border bg-card p-4"><CheckCircle2 className="h-5 w-5 shrink-0 text-success"/><div><p className="text-xs font-bold">Transparent status</p><p className="mt-1 text-[11px] leading-5 text-muted-foreground">Verified, revoked, modified and unsigned states are explicit.</p></div></div><div className="flex gap-3 rounded-xl border border-border bg-card p-4"><Info className="h-5 w-5 shrink-0 text-primary"/><div><p className="text-xs font-bold">AI is advisory</p><p className="mt-1 text-[11px] leading-5 text-muted-foreground">Manipulation-risk analysis never overrides cryptographic proof.</p></div></div></div>
      </div>
    </div>
  </div>;
}

function SearchIcon() { return <svg viewBox="0 0 24 24" aria-hidden="true" className="h-5 w-5"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" strokeWidth="2"/><path d="m16 16 4.2 4.2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>; }
