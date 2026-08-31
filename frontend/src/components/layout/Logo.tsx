import { Link } from "react-router-dom";
import { cn } from "@/lib/utils";

/**
 * Official PramaanScan logo mark. Renders the real brand asset
 * (public/brand/pramaanscan-logo.png — background keyed transparent,
 * artwork otherwise untouched) rather than a placeholder icon.
 * Aspect ratio is preserved via h-full/w-auto on a fixed-height box.
 */
export function Logo({ className, iconOnly = false }: { className?: string; iconOnly?: boolean }) {
  return (
    <Link to="/" className={cn("flex items-center gap-2.5 select-none", className)}>
      <span className="flex h-9 w-9 shrink-0 items-center justify-center">
        <img
          src="/brand/pramaanscan-logo.png"
          alt="PramaanScan"
          className="h-full w-full object-contain"
          draggable={false}
        />
      </span>
      {!iconOnly && (
        <span className="font-display text-[19px] font-bold tracking-tight">
          Pramaan<span className="text-primary">Scan</span>
        </span>
      )}
    </Link>
  );
}
