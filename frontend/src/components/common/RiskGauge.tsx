import { RadialBar, RadialBarChart, PolarAngleAxis } from "recharts";
import { cn } from "@/lib/utils";
import type { RiskLabel } from "@/api/types";

const COLORS: Record<RiskLabel, string> = {
  LOW: "#10b981",
  MEDIUM: "#f59e0b",
  HIGH: "#ef4444",
  INCONCLUSIVE: "#94a3b8",
};

export function RiskGauge({
  score,
  label,
  size = 160,
}: {
  score: number | null | undefined;
  label: RiskLabel | string | undefined;
  size?: number;
}) {
  const normalizedLabel = (label as RiskLabel) ?? "INCONCLUSIVE";
  const color = COLORS[normalizedLabel] ?? COLORS.INCONCLUSIVE;
  const pct = score !== null && score !== undefined ? Math.round(score * 100) : 0;
  const data = [{ name: "risk", value: pct, fill: color }];

  return (
    <div className="relative flex flex-col items-center justify-center" style={{ width: size, height: size }}>
      <RadialBarChart
        width={size}
        height={size}
        cx="50%"
        cy="50%"
        innerRadius="72%"
        outerRadius="100%"
        barSize={12}
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar background={{ fill: "hsl(var(--secondary))" }} dataKey="value" cornerRadius={20} angleAxisId={0} />
      </RadialBarChart>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-2xl font-bold" style={{ color }}>
          {score !== null && score !== undefined ? `${pct}%` : "—"}
        </span>
        <span
          className={cn("mt-0.5 text-[11px] font-semibold uppercase tracking-wide")}
          style={{ color }}
        >
          {normalizedLabel}
        </span>
      </div>
    </div>
  );
}
