"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { JsonViewer } from "@/components/traces/json-viewer";
import { formatMs, formatCost } from "@/lib/utils";
import type { Span } from "@/types/trace";

interface SpanDetailProps {
  span: Span;
  onClose: () => void;
}

export function SpanDetail({ span, onClose }: SpanDetailProps) {
  const [tab, setTab] = useState<"info" | "input" | "output" | "json">("info");

  const tabs = ["info", "input", "output", "json"] as const;

  return (
    <div className="bg-white border border-border rounded-lg h-full">
      <div className="flex items-center justify-between p-3 border-b border-border">
        <h4 className="font-semibold text-sm truncate">{span.name}</h4>
        <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
          <X size={14} />
        </button>
      </div>

      <div className="flex border-b border-border">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 text-xs ${
              tab === t
                ? "border-b-2 border-primary text-primary font-medium"
                : "text-muted-foreground"
            }`}
          >
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      <div className="p-3 text-xs overflow-y-auto" style={{ maxHeight: "calc(100vh - 240px)" }}>
        {tab === "info" && (
          <div className="space-y-2">
            <Row label="Type" value={<Badge variant="default">{span.type}</Badge>} />
            <Row label="Status" value={span.status} />
            <Row label="Model" value={span.model || "-"} />
            <Row label="Latency" value={span.latency_ms ? formatMs(span.latency_ms) : "-"} />
            <Row label="Tokens" value={span.usage?.total_tokens ? String(span.usage.total_tokens) : "-"} />
            <Row label="Cost" value={span.cost != null ? formatCost(span.cost) : "-"} />
            <Row label="Level" value={String(span.level ?? 0)} />
            {span.error_message && (
              <div className="text-red-600 bg-red-50 p-2 rounded mt-2">{span.error_message}</div>
            )}
            {span.generations && span.generations.length > 0 && (
              <div className="mt-2">
                <p className="font-medium mb-1">Generations ({span.generations.length})</p>
                {span.generations.map((g, i) => (
                  <div key={g.id || i} className="bg-muted p-2 rounded mb-1">
                    <p>Model: {g.model}</p>
                    {g.completion && <p className="mt-1">Output: {g.completion.slice(0, 200)}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        {tab === "input" && <JsonViewer data={span.input || {}} />}
        {tab === "output" && <JsonViewer data={span.output || {}} />}
        {tab === "json" && <JsonViewer data={span as unknown as Record<string, unknown>} />}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-muted-foreground">{label}</span>
      <span>{value}</span>
    </div>
  );
}
