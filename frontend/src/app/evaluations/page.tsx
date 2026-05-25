"use client";

import { useEffect, useState } from "react";
import { BarChart3 } from "lucide-react";
import { traceApi } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";

interface EvalSummary {
  traceName: string;
  traceId: string;
  status: string;
  scores: { name: string; value: number }[];
}

export default function EvaluationsPage() {
  const [evals, setEvals] = useState<EvalSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const result = await traceApi.list({ page_size: "50" });
        const items = result.items || [];
        const summaries: EvalSummary[] = [];

        for (const t of items) {
          try {
            const scoresData = await traceApi.scores(t.id);
            if (scoresData.scores?.length > 0) {
              summaries.push({
                traceName: t.name,
                traceId: t.id,
                status: t.status,
                scores: scoresData.scores.map((s) => ({
                  name: s.name,
                  value: s.value,
                })),
              });
            }
          } catch {
            // trace might not have scores
          }
        }
        setEvals(summaries);
      } catch {
        // API not available
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading evaluations...
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Evaluations</h2>

      {evals.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <BarChart3 size={48} className="mx-auto mb-3 opacity-30" />
          <p>No evaluations yet.</p>
          <p className="text-sm mt-1">
            Complete a trace and run evaluation to see scores here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {evals.map((e) => (
            <div
              key={e.traceId}
              className="bg-white border border-border rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="font-medium">{e.traceName}</p>
                  <p className="text-xs text-muted-foreground">{e.traceId}</p>
                </div>
                <Badge
                  variant={e.status === "completed" ? "success" : "default"}
                >
                  {e.status}
                </Badge>
              </div>
              <div className="flex gap-2 flex-wrap">
                {e.scores.map((s) => (
                  <span
                    key={s.name}
                    className={`px-2 py-0.5 rounded text-xs font-medium ${
                      s.value >= 0.8
                        ? "bg-emerald-50 text-emerald-700"
                        : s.value >= 0.5
                        ? "bg-yellow-50 text-yellow-700"
                        : "bg-red-50 text-red-700"
                    }`}
                  >
                    {s.name}: {s.value.toFixed(2)}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
