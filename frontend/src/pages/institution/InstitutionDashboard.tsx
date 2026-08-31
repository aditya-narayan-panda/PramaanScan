import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  FileStack,
  ShieldCheck,
  ShieldOff,
  ShieldQuestion,
  AlertTriangle,
  UploadCloud,
  QrCode,
  FileSearch,
} from "lucide-react";
import { getDashboardStats } from "@/api/dashboard";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { getApiErrorMessage } from "@/api/client";

const QUICK_ACTIONS = [
  { to: "/institution/issue", label: "Issue a Document", icon: UploadCloud },
  { to: "/institution/generate-qr", label: "Generate a QR Code", icon: QrCode },
  { to: "/institution/documents", label: "Browse My Documents", icon: FileSearch },
];

export default function InstitutionDashboard() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: getDashboardStats,
  });

  return (
    <div>
      <PageHeader title="Dashboard" description="A live snapshot of your institution's documents and verifications." />

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(error)}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {isLoading || !data
          ? Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[84px] rounded-2xl" />)
          : (
            <>
              <StatCard icon={FileStack} label="Total Documents" value={data.total_documents} />
              <StatCard icon={ShieldCheck} label="Verified Checks" value={data.verified_verifications} tone="success" />
              <StatCard icon={ShieldQuestion} label="Unsigned Checks" value={data.unsigned_verifications} tone="warning" />
              <StatCard icon={ShieldOff} label="Revoked Documents" value={data.revoked_documents} tone="destructive" />
            </>
          )}
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardContent className="p-6">
            <h3 className="font-display text-sm font-semibold">Verification Activity</h3>
            <p className="mt-1 text-xs text-muted-foreground">
              Total checks performed against your institution's registered documents.
            </p>
            {isLoading || !data ? (
              <Skeleton className="mt-4 h-32 rounded-xl" />
            ) : (
              <div className="mt-5 grid grid-cols-3 gap-4 text-center">
                <div className="rounded-xl bg-secondary/50 py-5">
                  <p className="font-display text-2xl font-bold">{data.total_verifications}</p>
                  <p className="mt-1 text-xs text-muted-foreground">Total Checks</p>
                </div>
                <div className="rounded-xl bg-success/10 py-5">
                  <p className="font-display text-2xl font-bold text-success">{data.verified_verifications}</p>
                  <p className="mt-1 text-xs text-muted-foreground">Verified</p>
                </div>
                <div className="rounded-xl bg-destructive/10 py-5">
                  <p className="font-display text-2xl font-bold text-destructive">{data.high_risk_media}</p>
                  <p className="mt-1 text-xs text-muted-foreground">High-Risk Media</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <h3 className="font-display text-sm font-semibold">Quick Actions</h3>
            <div className="mt-4 space-y-2">
              {QUICK_ACTIONS.map((action) => (
                <Link
                  key={action.to}
                  to={action.to}
                  className="flex items-center gap-3 rounded-lg border border-border px-3.5 py-3 text-sm font-medium transition-colors hover:border-primary/40 hover:bg-primary/5"
                >
                  <action.icon className="h-4 w-4 text-primary" />
                  {action.label}
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
