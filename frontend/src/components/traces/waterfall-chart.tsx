"use client";

import { useMemo } from "react";
import type { Span } from "@/types/trace";
import { formatMs } from "@/lib/utils";

interface WaterfallChartProps {
  spans: Span[];
  onSpanClick: (span: Span) => void;
  selectedSpanId?: string;
}

const typeColors: Record<string, string> = {
  llm: "bg-blue-500",
  tool: "bg-emerald-500",
  retriever: "bg-purple-500",
  embedding: "bg-orange-500",
  agent: "bg-indigo-500",
  span: "bg-gray-400",
};

function getSpanColor(type: string): string {
  return typeColors[type] || typeColors.span;
}

function buildSpanTree(spans: Span[]): Span[] {
  const map = new Map<string, Span & { children: Span[] }>();
  const roots: (Span & { children: Span[] })[] = [];

  for (const s of spans) {
    map.set(s.id, { ...s, children: [] });
  }
  for (const s of map.values()) {
    if (s.parent_span_id && map.has(s.parent_span_id)) {
      map.get(s.parent_span_id)!.children.push(s);
    } else {
      roots.push(s);
    }
  }
  return roots;
}

export function WaterfallChart({ spans, onSpanClick, selectedSpanId }: WaterfallChartProps) {
  const roots = useMemo(() => buildSpanTree(spans), [spans]);

  if (spans.length === 0) {
    return <p className="text-muted-foreground text-sm p-4">No spans recorded.</p>;
  }

  const minTime = Math.min(...spans.map((s) => new Date(s.started_at || 0).getTime()));
  const maxTime = Math.max(
    ...spans.map((s) => {
      const start = new Date(s.started_at || 0).getTime();
      return start + (s.latency_ms || 0);
    })
  );
  const totalDuration = maxTime - minTime || 1;

  const renderSpanRow = (span: Span & { children?: Span[] }, depth: number): React.ReactNode => {
    const startMs = new Date(span.started_at || 0).getTime();
    const leftPct = ((startMs - minTime) / totalDuration) * 100;
    const widthPct = Math.max(((span.latency_ms || 0) / totalDuration) * 100, 0.5);
    const isSelected = span.id === selectedSpanId;

    return (
      <div key={span.id}>
        <div
          className={`flex items-center cursor-pointer hover:opacity-80 py-0.5 ${
            isSelected ? "bg-blue-50" : ""
          }`}
          style={{ paddingLeft: `${depth * 20 + 8}px` }}
          onClick={() => onSpanClick(span)}
        >
          <div className="w-40 flex-shrink-0 text-xs truncate pr-2" title={span.name}>
            {span.name}
          </div>
          <div className="flex-1 relative h-5">
            <div
              className={`absolute top-0.5 h-4 rounded ${getSpanColor(span.type)}`}
              style={{ left: `${leftPct}%`, width: `${widthPct}%`, minWidth: "4px" }}
            />
          </div>
          <div className="w-16 text-right text-xs text-muted-foreground flex-shrink-0">
            {span.latency_ms ? formatMs(span.latency_ms) : ""}
          </div>
        </div>
        {span.children?.map((child) => renderSpanRow(child, depth + 1))}
      </div>
    );
  };

  return (
    <div className="bg-white border border-border rounded-lg p-4 overflow-x-auto">
      <div className="flex items-center text-xs text-muted-foreground mb-2">
        <div className="w-40 flex-shrink-0 pr-2">Name</div>
        <div className="flex-1">Timeline</div>
        <div className="w-16 text-right flex-shrink-0">Duration</div>
      </div>
      {roots.map((root) => renderSpanRow(root, 0))}
      <div className="flex gap-2 mt-3 pt-3 border-t border-border text-xs">
        {Object.entries(typeColors).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1">
            <div className={`w-3 h-3 rounded ${color}`} />
            <span className="text-muted-foreground">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
