import { useEffect, useRef, useState } from "react";
import QRCode from "qrcode";
import { Download, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";

export function QrCodeDisplay({ value, filename = "pramaanscan-qr" }: { value: string; filename?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (!canvasRef.current || !value) return;
    QRCode.toCanvas(canvasRef.current, value, {
      width: 260,
      margin: 2,
      color: { dark: "#0f172a", light: "#ffffff" },
      errorCorrectionLevel: "M",
    }).catch(() => {
      toast({ variant: "destructive", title: "Could not render QR code" });
    });
  }, [value, toast]);

  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const link = document.createElement("a");
    link.download = `${filename}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    toast({ title: "Verification link copied" });
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="rounded-2xl border border-border bg-white p-5 shadow-card">
        <canvas ref={canvasRef} />
      </div>
      <p className="max-w-xs break-all text-center font-mono text-xs text-muted-foreground">{value}</p>
      <div className="flex gap-2">
        <Button type="button" variant="outline" size="sm" onClick={handleCopy}>
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          Copy link
        </Button>
        <Button type="button" size="sm" onClick={handleDownload}>
          <Download className="h-4 w-4" />
          Download PNG
        </Button>
      </div>
    </div>
  );
}
