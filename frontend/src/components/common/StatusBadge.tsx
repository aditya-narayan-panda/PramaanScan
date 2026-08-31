import type { ElementType } from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  ShieldQuestion,
  ShieldOff,
  Clock,
} from "lucide-react";

type Status =
  | "VERIFIED"
  | "MODIFIED"
  | "UNSIGNED"
  | "REVOKED"
  | "INVALID"
  | "EXPIRED"
  | "CURRENT"
  | "SUPERSEDED"
  | "ACTIVE"
  | string;

const CONFIG: Record<string, { variant: "success" | "destructive" | "warning" | "secondary" | "outline"; icon: ElementType; label?: string }> = {
  VERIFIED: { variant: "success", icon: ShieldCheck },
  CURRENT: { variant: "success", icon: ShieldCheck },
  ACTIVE: { variant: "success", icon: ShieldCheck },
  MODIFIED: { variant: "destructive", icon: ShieldAlert },
  INVALID: { variant: "destructive", icon: ShieldX },
  REVOKED: { variant: "destructive", icon: ShieldOff },
  UNSIGNED: { variant: "warning", icon: ShieldQuestion },
  EXPIRED: { variant: "secondary", icon: Clock },
  SUPERSEDED: { variant: "secondary", icon: Clock },
  UNKNOWN: { variant: "outline", icon: ShieldQuestion },
};

export function StatusBadge({ status, className }: { status: Status; className?: string }) {
  const config = CONFIG[status] ?? CONFIG.UNKNOWN;
  const Icon = config.icon;
  return (
    <Badge variant={config.variant} className={cn("py-1 px-3 text-[13px]", className)}>
      <Icon className="h-3.5 w-3.5" />
      {config.label ?? status}
    </Badge>
  );
}
