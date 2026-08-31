import { useEffect, useRef, useState, type ChangeEvent } from "react";
import QrScannerLib from "qr-scanner";
import { Camera, CameraOff, ImageUp, AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface QrScannerProps {
  onDecode: (rawValue: string) => void;
  active: boolean;
}

export function QrScanner({ onDecode, active }: QrScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const scannerRef = useRef<QrScannerLib | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [hasCamera, setHasCamera] = useState<boolean | null>(null);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);

  useEffect(() => {
    if (!active || !videoRef.current) return;

    let cancelled = false;

    QrScannerLib.hasCamera().then((result) => {
      if (!cancelled) setHasCamera(result);
    });

    const scanner = new QrScannerLib(
      videoRef.current,
      (result) => onDecode(result.data),
      {
        highlightScanRegion: true,
        highlightCodeOutline: true,
        maxScansPerSecond: 5,
      }
    );
    scannerRef.current = scanner;

    scanner.start().catch((err: unknown) => {
      setCameraError(
        err instanceof Error ? err.message : "Could not access the camera. Check browser permissions."
      );
    });

    return () => {
      cancelled = true;
      scanner.stop();
      scanner.destroy();
      scannerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  const handleFileUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageError(null);
    try {
      const result = await QrScannerLib.scanImage(file, { returnDetailedScanResult: true });
      onDecode(result.data);
    } catch {
      setImageError("No QR code could be detected in that image. Try a clearer photo.");
    } finally {
      e.target.value = "";
    }
  };

  return (
    <div className="space-y-4">
      <div className="relative mx-auto aspect-square w-full max-w-sm overflow-hidden rounded-2xl border border-border bg-slate-950 shadow-card">
        <video ref={videoRef} className="h-full w-full object-cover" muted playsInline />
        {!cameraError && (
          <div className="pointer-events-none absolute inset-8 rounded-xl border-2 border-white/40">
            <div className="absolute left-0 top-0 h-6 w-6 rounded-tl-xl border-l-[3px] border-t-[3px] border-primary-400" />
            <div className="absolute right-0 top-0 h-6 w-6 rounded-tr-xl border-r-[3px] border-t-[3px] border-primary-400" />
            <div className="absolute bottom-0 left-0 h-6 w-6 rounded-bl-xl border-b-[3px] border-l-[3px] border-primary-400" />
            <div className="absolute bottom-0 right-0 h-6 w-6 rounded-br-xl border-b-[3px] border-r-[3px] border-primary-400" />
            <div className="absolute inset-x-0 top-0 h-0.5 animate-scan-line bg-primary-400 shadow-[0_0_12px_2px_rgba(59,102,245,0.8)]" />
          </div>
        )}
        {cameraError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-950/95 px-6 text-center text-white">
            <CameraOff className="h-8 w-8 text-slate-400" />
            <p className="text-sm text-slate-300">{cameraError}</p>
          </div>
        )}
        {hasCamera === false && !cameraError && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-950/95 px-6 text-center text-white">
            <Camera className="h-8 w-8 text-slate-400" />
            <p className="text-sm text-slate-300">No camera was detected on this device.</p>
          </div>
        )}
      </div>

      {imageError && (
        <Alert variant="destructive">
          <AlertTriangle />
          <AlertDescription>{imageError}</AlertDescription>
        </Alert>
      )}

      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-border" />
        <span className="text-xs font-medium text-muted-foreground">or</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileUpload}
      />
      <Button type="button" variant="outline" className="w-full" onClick={() => fileInputRef.current?.click()}>
        <ImageUp className="h-4 w-4" />
        Upload a QR code image
      </Button>
    </div>
  );
}
