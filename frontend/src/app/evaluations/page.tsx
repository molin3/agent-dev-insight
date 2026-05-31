"use client";

import { useEffect, useState } from "react";
import { BarChart3, Zap } from "lucide-react";
import { useEvaluationStore } from "@/stores/evaluation-store";
import { traceApi } from "@/lib/api-client";
import { notify } from "@/lib/toast";
import { Badge } from "@/components/ui/badge";
import { SkeletonTable } from "@/components/ui/skeleton";

export default function EvaluationsPage() {
  const { evaluations, isLoading, fetchEvaluations } = useEvaluationStore();
  const [evaluatingId, setEvaluatingId] = useState<string | null>(null);

  useEffect(() => {
    fetchEvaluations();
  }, [fetchEvaluations]);

  const handleEvaluate = async (traceId: string) => {
    setEvaluatingId(traceId);
    try {
      await traceApi.evaluate(traceId);
      await fetchEvaluations();
    } catch (e) {
      notify.error(`Evaluation failed: ${(e as Error).message}`);
    } finally {
      setEvaluatingId(null);
    }
  };

  if (isLoading) {
    return <SkeletonTable />;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Evaluations</h2>
      </div>

      {evaluations.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <BarChart3 size={48} className="mx-auto mb-3 opacity-30" />
          <p>No completed traces yet.</p>
          <p className="text-sm mt-1">
            Complete a trace first, then come back to evaluate it.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {evaluations.map((e) => (
            <div
              key={e.traceId}
              className="bg-white border border-border rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <p className="font-medium">{e.traceName}</p>
                  <p className="text-xs text-muted-foreground font-mono">{e.traceId}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant={e.status === "completed" ? "success" : "default"}>
                    {e.status}
                  </Badge>
                  <button
                    onClick={() => handleEvaluate(e.traceId)}
                    disabled={evaluatingId === e.traceId}
                    className="flex items-center gap-1 bg-primary text-white px-3 py-1 rounded-md text-xs hover:bg-primary/90 disabled:opacity-50"
                  >
                    <Zap size={12} />
                    {evaluatingId === e.traceId ? "Evaluating..." : e.scores.length > 0 ? "Re-evaluate" : "Evaluate"}
                  </button>
                </div>
              </div>

              {e.scores.length > 0 ? (
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
              ) : (
                <p className="text-xs text-muted-foreground">
                  No scores yet. Click the Evaluate button to run all 5 built-in evaluators.
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
