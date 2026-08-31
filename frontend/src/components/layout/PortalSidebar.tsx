import { NavLink } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  UploadCloud,
  QrCode,
  FileStack,
  ScrollText,
  BarChart3,
  UserCog,
  Building2,
  Users,
  KeyRound,
  FileSearch,
  ClipboardList,
  Settings,
} from "lucide-react";
import { Logo } from "./Logo";
import { cn } from "@/lib/utils";

export interface SidebarLink {
  to: string;
  label: string;
  icon: LucideIcon;
  end?: boolean;
}

export const INSTITUTION_LINKS: SidebarLink[] = [
  { to: "/institution/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/institution/issue", label: "Issue Document", icon: UploadCloud },
  { to: "/institution/generate-qr", label: "Generate QR", icon: QrCode },
  { to: "/institution/documents", label: "My Documents", icon: FileStack },
  { to: "/institution/verification-logs", label: "Verification Logs", icon: ScrollText },
  { to: "/institution/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/institution/keys", label: "Signing Keys", icon: KeyRound },
  { to: "/institution/profile", label: "Profile & Settings", icon: UserCog },
];

export const ADMIN_LINKS: SidebarLink[] = [
  { to: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/institutions", label: "Institution Management", icon: Building2 },
  { to: "/admin/users", label: "User Management", icon: Users },
  { to: "/admin/documents", label: "Document Management", icon: FileSearch },
  { to: "/admin/verification-logs", label: "Verification Logs", icon: ScrollText },
  { to: "/admin/keys", label: "Key Management", icon: KeyRound },
  { to: "/admin/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/admin/audit-logs", label: "Audit Logs", icon: ClipboardList },
  { to: "/admin/settings", label: "System Settings", icon: Settings },
];

export function PortalSidebar({
  links,
  portalLabel,
  className,
}: {
  links: SidebarLink[];
  portalLabel: string;
  className?: string;
}) {
  return (
    <aside
      className={cn(
        "flex h-full w-64 flex-col border-r border-border bg-card/60",
        className
      )}
    >
      <div className="flex h-16 items-center border-b border-border px-5">
        <Logo />
      </div>
      <div className="px-5 pb-2 pt-4">
        <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-primary">
          {portalLabel}
        </span>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2 scrollbar-thin">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground",
                isActive && "bg-primary/10 text-primary hover:bg-primary/10 hover:text-primary"
              )
            }
          >
            <link.icon className="h-[18px] w-[18px]" />
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-border p-4 text-[11px] text-muted-foreground">
        PramaanScan v1.0 · Secure Portal
      </div>
    </aside>
  );
}
