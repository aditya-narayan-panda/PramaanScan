import { Sparkles, Info } from "lucide-react";
import { RiskGauge } from "@/components/common/RiskGauge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { MediaAnalysisResult } from "@/api/types";
import type { ReactNode } from "react";

const HIDDEN_KEYS = new Set([
  "available",
  "reason",
  "modality",
  "risk_score",
  "risk_label",
  "model_name",
  "is_advisory",
  "evidence_type",
  "disclaimer",
  "filename",
  "models",
  "video",
  "audio",
  "multimodal",
]);

function prettifyKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function renderValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(4);
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}


function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function formatProbability(value: unknown): string {
  if (typeof value !== "number") return "—";
  return `${(value * 100).toFixed(1)}%`;
}

export function MediaAnalysisPanel({ analysis }: { analysis: MediaAnalysisResult | undefined }) {
  if (!analysis) return null;

  if (analysis.available === false) {
    return (
      <Alert>
        <Info />
        <AlertDescription>{analysis.reason ?? "Advisory media analysis is not available for this file."}</AlertDescription>
      </Alert>
    );
  }

  const raw = analysis as Record<string, unknown>;

  const extraEntries = Object.entries(raw).filter(
    ([key, value]) => !HIDDEN_KEYS.has(key) && value !== null && typeof value !== "object"
  );

  const modelMap = isRecord(raw.models) ? raw.models : null;
  const videoDetails = isRecord(raw.video) ? raw.video : null;
  const audioDetails = isRecord(raw.audio) ? raw.audio : null;
  const multimodalDetails = isRecord(raw.multimodal) ? raw.multimodal : null;

  return (
    <div className="rounded-2xl border border-border bg-card p-6 shadow-card">
      <div className="mb-5 flex items-center gap-2">
        <div className="rounded-lg bg-primary/10 p-2 text-primary">
          <Sparkles className="h-4 w-4" />
        </div>
        <div>
          <h3 className="font-display text-sm font-semibold">AI-Assisted Media Analysis</h3>
          <p className="mt-0.5 text-[11px] text-muted-foreground">Secondary forensic signal • cryptographic status remains authoritative</p>
        </div>
        <span className="ml-auto rounded-full bg-secondary px-2.5 py-0.5 text-[11px] font-medium text-muted-foreground">
          Advisory only
        </span>
      </div>

      <div className="flex flex-col items-center gap-6 sm:flex-row sm:items-start">
        <RiskGauge score={analysis.risk_score} label={analysis.risk_label} />

        <div className="flex-1 space-y-3">
          {modelMap && (
            <div className="rounded-xl border border-border/70 bg-secondary/30 p-3">
              <p className="mb-2 text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">
                Model ensemble
              </p>
              <div className="grid gap-2 sm:grid-cols-3">
                {Object.entries(modelMap).map(([name, value]) => {
                  const item = isRecord(value) ? value : {};
                  return (
                    <div key={name} className="rounded-lg bg-background p-3">
                      <p className="truncate text-xs font-semibold">{name}</p>
                      <p className="mt-1 text-sm font-bold">{formatProbability(item.ai_score)}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {String(item.prediction ?? "—")}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {videoDetails && (
            <div className="rounded-xl border border-border/70 bg-secondary/30 p-3">
              <p className="mb-2 text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Video evidence</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {([
                  ["Verdict", videoDetails.verdict],
                  ["AI score", formatProbability(videoDetails.fake_probability)],
                  ["Confidence", videoDetails.confidence],
                  ["Reliable windows", videoDetails.reliable_windows],
                ] as [string, ReactNode][]).map(([label, value]) => (
                  <div key={label} className="rounded-lg bg-background p-2.5">
                    <p className="text-[10px] text-muted-foreground">{label}</p>
                    <p className="mt-0.5 text-xs font-semibold">{String(value ?? "—")}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {audioDetails && (
            <div className="rounded-xl border border-border/70 bg-secondary/30 p-3">
              <p className="mb-2 text-[11px] font-bold uppercase tracking-[.12em] text-muted-foreground">Audio evidence</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {([
                  ["Verdict", audioDetails.final_prediction],
                  ["AI score", formatProbability(audioDetails.average_ai_score)],
                  ["AI votes", audioDetails.ai_votes != null ? `${audioDetails.ai_votes}/${audioDetails.total_models ?? "—"}` : "—"],
                  ["Segments", audioDetails.segments_analyzed],
                ] as [string, ReactNode][]).map(([label, value]) => (
                  <div key={label} className="rounded-lg bg-background p-2.5">
                    <p className="text-[10px] text-muted-foreground">{label}</p>
                    <p className="mt-0.5 text-xs font-semibold">{String(value ?? "—")}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {multimodalDetails && (
            <div className="rounded-xl border border-primary/15 bg-primary/5 p-3">
              <p className="mb-2 text-[11px] font-bold uppercase tracking-[.12em] text-primary">Multimodal fusion</p>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {([
                  ["Final", multimodalDetails.final_verdict],
                  ["Score", formatProbability(multimodalDetails.multimodal_score)],
                  ["Confidence", multimodalDetails.confidence],
                  ["Agreement", multimodalDetails.agreement],
                ] as [string, ReactNode][]).map(([label, value]) => (
                  <div key={label} className="rounded-lg border border-primary/10 bg-background/80 p-2.5">
                    <p className="text-[10px] text-muted-foreground">{label}</p>
                    <p className="mt-0.5 text-xs font-semibold">{String(value ?? "—")}</p>
                  </div>
                ))}
              </div>
              {typeof multimodalDetails.explanation === "string" && (
                <p className="mt-2 text-xs leading-5 text-muted-foreground">{multimodalDetails.explanation}</p>
              )}
            </div>
          )}

          {analysis.model_name && (
            <div className="text-sm">
              <span className="text-muted-foreground">Model:</span>{" "}
              <span className="font-medium">{analysis.model_name}</span>
            </div>
          )}
          {analysis.modality && (
            <div className="text-sm">
              <span className="text-muted-foreground">Modality:</span>{" "}
              <span className="font-medium">{analysis.modality}</span>
            </div>
          )}
          {extraEntries.length > 0 && (
            <dl className="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-2">
              {extraEntries.slice(0, 8).map(([key, value]) => (
                <div key={key} className="flex justify-between gap-2 border-b border-border/60 py-1 text-xs">
                  <dt className="text-muted-foreground">{prettifyKey(key)}</dt>
                  <dd className="font-medium">{renderValue(value)}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </div>

      {analysis.disclaimer && (
        <p className="mt-5 rounded-lg bg-secondary/50 px-3.5 py-2.5 text-xs leading-relaxed text-muted-foreground">
          {analysis.disclaimer}
        </p>
      )}
    </div>
  );
}
