"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useTraceStore } from "@/stores/trace-store";
import { Badge } from "@/components/ui/badge";
import { WaterfallChart } from "@/components/traces/waterfall-chart";
import { SpanDetail } from "@/components/traces/span-detail";
import { JsonViewer } from "@/components/traces/json-viewer";
import { ConversationReplay } from "@/components/traces/conversation-replay";
import { formatMs, formatTokens, formatCost } from "@/lib/utils";
import type { Span } from "@/types/trace";

export default function TraceDetailPage() {
  const { traceId } = useParams<{ traceId: string }>();
  const { currentTrace, isLoading, fetchTrace } = useTraceStore();
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null);
  const [viewMode, setViewMode] = useState<"waterfall" | "replay" | "json">("waterfall");

  useEffect(() => {
    if (traceId) fetchTrace(traceId);
  }, [traceId, fetchTrace]);

  if (isLoading || !currentTrace) {
    return <p className="text-muted-foreground">Loading...</p>;
  }

  const spans = currentTrace.spans || [];
  const scores = currentTrace.scores || [];

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-xl font-bold">{currentTrace.name}</h2>
        <Badge
          variant={
            currentTrace.status === "completed" ? "success"
            : currentTrace.status === "error" ? "error"
            : "default"
          }
        >
          {currentTrace.status}
        </Badge>
      </div>

      <div className="grid grid-cols-4 gap-4 mb-6">
        <Metric label="Latency" value={currentTrace.total_latency_ms ? formatMs(currentTrace.total_latency_ms) : "-"} />
        <Metric label="Tokens" value={currentTrace.total_tokens ? formatTokens(currentTrace.total_tokens) : "-"} />
        <Metric label="Cost" value={currentTrace.total_cost != null ? formatCost(currentTrace.total_cost) : "-"} />
        <Metric label="Spans" value={String(spans.length)} />
      </div>

      {scores.length > 0 && (
        <div className="mb-4 flex gap-2 flex-wrap">
          {scores.map((s) => (
            <span
              key={s.id}
              className={`px-2 py-0.5 rounded text-xs font-medium ${
                s.value >= 0.8 ? "bg-emerald-50 text-emerald-700"
                : s.value >= 0.5 ? "bg-yellow-50 text-yellow-700"
                : "bg-red-50 text-red-700"
              }`}
              title={s.comment}
            >
              {s.name}: {s.value.toFixed(2)}
            </span>
          ))}
        </div>
      )}

      <div className="flex gap-2 mb-4">
        {(["waterfall", "replay", "json"] as const).map((mode) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            className={`px-3 py-1 rounded text-sm ${
              viewMode === mode
                ? "bg-primary text-white"
                : "bg-muted text-muted-foreground"
            }`}
          >
            {mode === "waterfall" ? "Waterfall" : mode === "replay" ? "Replay" : "JSON"}
          </button>
        ))}
      </div>

      <div className="flex gap-4">
        <div className="flex-1">
          {viewMode === "waterfall" && (
            <WaterfallChart spans={spans} onSpanClick={setSelectedSpan} selectedSpanId={selectedSpan?.id} />
          )}
          {viewMode === "replay" && <ConversationReplay traceId={currentTrace.id} />}
          {viewMode === "json" && <JsonViewer data={currentTrace as unknown as Record<string, unknown>} />}
        </div>

        {selectedSpan && viewMode === "waterfall" && (
          <div className="w-80 flex-shrink-0">
            <SpanDetail span={selectedSpan} onClose={() => setSelectedSpan(null)} />
          </div>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-white border border-border rounded-lg p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-lg font-bold">{value}</p>
    </div>
  );
}
