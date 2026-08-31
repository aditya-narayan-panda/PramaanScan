import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { AlertTriangle, FileStack, ShieldCheck, Sparkles } from "lucide-react";
import { getAnalyticsOverview, getMediaAnalytics, getVerificationAnalytics } from "@/api/analytics";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { getApiErrorMessage } from "@/api/client";

const RESULT_COLORS: Record<string, string> = {
  VERIFIED: "#10b981",
  MODIFIED: "#ef4444",
  UNSIGNED: "#f59e0b",
  REVOKED: "#dc2626",
  INVALID: "#ef4444",
  EXPIRED: "#94a3b8",
};

function toChartData(record: Record<string, number>) {
  return Object.entries(record).map(([name, value]) => ({ name, value }));
}

export function AnalyticsView({ title, description }: { title: string; description: string }) {
  const overview = useQuery({ queryKey: ["analytics-overview"], queryFn: getAnalyticsOverview });
  const verifications = useQuery({ queryKey: ["analytics-verifications"], queryFn: getVerificationAnalytics });
  const media = useQuery({ queryKey: ["analytics-media"], queryFn: getMediaAnalytics });

  const loading = overview.isLoading || verifications.isLoading || media.isLoading;
  const anyError = overview.error || verifications.error || media.error;

  return (
    <div>
      <PageHeader title={title} description={description} />

      {anyError && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle />
          <AlertDescription>{getApiErrorMessage(anyError)}</AlertDescription>
        </Alert>
      )}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-[84px] rounded-2xl" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          <StatCard icon={FileStack} label="Documents" value={overview.data?.documents ?? 0} />
          <StatCard icon={ShieldCheck} label="Total Verifications" value={overview.data?.total_verifications ?? 0} tone="success" />
          <StatCard
            icon={Sparkles}
            label="Avg. Media Risk Score"
            value={`${Math.round((media.data?.average_risk_score ?? 0) * 100)}%`}
            tone="warning"
          />
        </div>
      )}

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Results by Outcome</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {verifications.data && Object.keys(verifications.data.by_result).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={toChartData(verifications.data.by_result)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                  <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))" }} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {toChartData(verifications.data.by_result).map((entry) => (
                      <Cell key={entry.name} fill={RESULT_COLORS[entry.name] ?? "#3b66f5"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-sm text-muted-foreground">No verification data yet.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Verification Source</CardTitle>
          </CardHeader>
          <CardContent className="h-72">
            {verifications.data && Object.keys(verifications.data.by_source).length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={toChartData(verifications.data.by_source)}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={55}
                    outerRadius={90}
                    paddingAngle={3}
                  >
                    {toChartData(verifications.data.by_source).map((entry, i) => (
                      <Cell key={entry.name} fill={["#1d4ed8", "#3b66f5", "#93b4fd"][i % 3]} />
                    ))}
                  </Pie>
                  <Legend />
                  <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))" }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="flex h-full items-center justify-center text-sm text-muted-foreground">No verification data yet.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Media Risk Labels</CardTitle>
        </CardHeader>
        <CardContent className="h-64">
          {media.data && Object.keys(media.data.risk_labels).length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={toChartData(media.data.risk_labels)} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis type="number" allowDecimals={false} tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={90} stroke="hsl(var(--muted-foreground))" />
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid hsl(var(--border))" }} />
                <Bar dataKey="value" radius={[0, 6, 6, 0]} fill="#f59e0b" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="flex h-full items-center justify-center text-sm text-muted-foreground">No media analyses yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
