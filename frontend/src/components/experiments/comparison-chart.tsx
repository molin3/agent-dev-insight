"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from "recharts";

interface ComparisonData {
  models: string[];
  metrics: { [key: string]: { [model: string]: number } };
}

const MODEL_COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#06b6d4"];

const METRIC_LABELS: Record<string, string> = {
  avg_latency_ms: "Avg Latency (ms)",
  total_tokens: "Total Tokens",
  total_cost: "Total Cost ($)",
  completion_rate: "Completion Rate (%)",
};

function formatMetricValue(key: string, value: number): string {
  if (key === "completion_rate") return `${(value * 100).toFixed(1)}%`;
  if (key === "total_cost") return `$${value.toFixed(4)}`;
  if (key === "avg_latency_ms") return `${value.toFixed(0)}ms`;
  return String(value);
}

export function ComparisonChart({ comparison }: { comparison: ComparisonData }) {
  const { models, metrics } = comparison;

  const metricKeys = Object.keys(metrics).filter(
    (k) => METRIC_LABELS[k]
  );

  return (
    <div className="grid grid-cols-2 gap-4">
      {metricKeys.map((key) => {
        const metricData = metrics[key];
        const chartData = models.map((model) => ({
          name: model,
          value: metricData[model] ?? 0,
        }));

        return (
          <div key={key} className="bg-white border border-border rounded-lg p-3">
            <h5 className="text-xs font-semibold mb-2 text-center">
              {METRIC_LABELS[key] || key}
            </h5>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 10 }}
                  interval={0}
                />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip
                  formatter={(value: number) => formatMetricValue(key, value)}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {chartData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={MODEL_COLORS[index % MODEL_COLORS.length]}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        );
      })}
    </div>
  );
}
