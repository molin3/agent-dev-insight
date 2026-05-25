"use client";

import { useEffect } from "react";
import { useDashboardStore } from "@/stores/dashboard-store";
import { Activity, CheckCircle2, XCircle, Zap, Coins, Clock } from "lucide-react";
import { formatMs, formatTokens, formatCost } from "@/lib/utils";

function MetricCard({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="bg-white border border-border rounded-lg p-4 flex items-start gap-3">
      <div className="p-2 rounded-md bg-muted">
        <Icon size={18} className="text-primary" />
      </div>
      <div>
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { overview, isLoading, fetchOverview } = useDashboardStore();

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  if (isLoading || !overview) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading...
      </div>
    );
  }

  const errorRate =
    overview.total_traces > 0
      ? ((overview.errors / overview.total_traces) * 100).toFixed(1)
      : "0";

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          icon={Activity}
          label="Total Traces"
          value={String(overview.total_traces)}
          sub={`${overview.completed} completed`}
        />
        <MetricCard
          icon={Clock}
          label="Avg Latency"
          value={formatMs(overview.avg_latency_ms)}
        />
        <MetricCard
          icon={Zap}
          label="Total Tokens"
          value={formatTokens(overview.total_tokens)}
        />
        <MetricCard
          icon={Coins}
          label="Total Cost"
          value={formatCost(overview.total_cost)}
          sub={`${errorRate}% error rate`}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <CheckCircle2 size={16} className="text-emerald-500" />
            Completion Stats
          </h3>
          <div className="flex gap-4 text-sm">
            <div>
              <span className="text-emerald-600 font-bold">{overview.completed}</span>{" "}
              <span className="text-muted-foreground">completed</span>
            </div>
            <div>
              <span className="text-red-600 font-bold">{overview.errors}</span>{" "}
              <span className="text-muted-foreground">errors</span>
            </div>
          </div>
        </div>

        <div className="bg-white border border-border rounded-lg p-4">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <XCircle size={16} className="text-red-500" />
            Alerts
          </h3>
          {overview.errors > 0 ? (
            <p className="text-sm text-red-600">
              {overview.errors} trace(s) failed. Check the Traces page for details.
            </p>
          ) : (
            <p className="text-sm text-muted-foreground">No alerts. All systems normal.</p>
          )}
        </div>
      </div>
    </div>
  );
}
