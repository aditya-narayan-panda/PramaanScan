import { ServerOff } from "lucide-react";
import { EmptyState } from "./EmptyState";

/**
 * Used on pages the product spec calls for but which the current PramaanScan
 * API does not yet support (no list/aggregate endpoint exists). We show this
 * honestly instead of inventing data, per the "no dummy data" requirement.
 */
export function BackendUnavailableNotice({
  feature,
  missingEndpoints,
}: {
  feature: string;
  missingEndpoints: string[];
}) {
  return (
    <EmptyState
      icon={<ServerOff className="h-6 w-6" />}
      title={`${feature} needs a backend endpoint`}
      description={`The PramaanScan API doesn't expose this yet. Once it's added, this screen will connect automatically — no frontend changes needed.`}
      action={
        <div className="w-full max-w-md rounded-xl border border-border bg-card px-4 py-3 text-left">
          <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Expected endpoint{missingEndpoints.length > 1 ? "s" : ""}
          </p>
          <ul className="space-y-1">
            {missingEndpoints.map((ep) => (
              <li key={ep} className="font-mono text-xs text-primary">
                {ep}
              </li>
            ))}
          </ul>
        </div>
      }
    />
  );
}
