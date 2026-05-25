"use client";

import { useEffect, useState } from "react";
import { traceApi } from "@/lib/api-client";
import type { ReplayEvent } from "@/types/trace";
import { Badge } from "@/components/ui/badge";

interface ConversationReplayProps {
  traceId: string;
}

export function ConversationReplay({ traceId }: ConversationReplayProps) {
  const [events, setEvents] = useState<ReplayEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    traceApi
      .replay(traceId)
      .then((data) => setEvents(data.events))
      .catch(() => setEvents([]))
      .finally(() => setLoading(false));
  }, [traceId]);

  if (loading) return <p className="text-muted-foreground text-sm">Loading replay...</p>;
  if (events.length === 0) return <p className="text-muted-foreground text-sm">No events to replay.</p>;

  const displayedEvents = events.slice(0, currentStep + 1);

  return (
    <div className="bg-white border border-border rounded-lg">
      <div className="flex items-center gap-3 p-3 border-b border-border">
        <button
          onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
          disabled={currentStep === 0}
          className="px-3 py-1 text-sm border rounded disabled:opacity-50"
        >
          Prev
        </button>
        <span className="text-sm text-muted-foreground">
          Step {currentStep + 1} / {events.length}
        </span>
        <button
          onClick={() => setCurrentStep(Math.min(events.length - 1, currentStep + 1))}
          disabled={currentStep >= events.length - 1}
          className="px-3 py-1 text-sm bg-primary text-white rounded disabled:opacity-50"
        >
          Next
        </button>
        <button
          onClick={() => setCurrentStep(events.length - 1)}
          className="px-3 py-1 text-sm border rounded"
        >
          All
        </button>
      </div>

      <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
        {displayedEvents.map((event, i) => (
          <div
            key={i}
            className={`p-3 rounded-lg text-sm ${
              event.type === "generation"
                ? "bg-blue-50 border border-blue-100"
                : event.type.includes("llm")
                ? "bg-purple-50 border border-purple-100"
                : event.type.includes("tool")
                ? "bg-emerald-50 border border-emerald-100"
                : "bg-gray-50 border border-gray-200"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <Badge
                variant={
                  event.type.includes("error") ? "error"
                  : event.type === "generation" ? "default"
                  : "success"
                }
              >
                {event.type}
              </Badge>
              {event.name && <span className="font-medium">{event.name}</span>}
              {event.model && (
                <span className="text-muted-foreground text-xs">{event.model}</span>
              )}
            </div>
            {event.completion && (
              <p className="text-xs mt-1 whitespace-pre-wrap">{event.completion}</p>
            )}
            {event.input && !event.completion && (
              <p className="text-xs text-muted-foreground mt-1">
                Input: {JSON.stringify(event.input).slice(0, 200)}
              </p>
            )}
            {event.output && (
              <p className="text-xs text-muted-foreground mt-1">
                Output: {JSON.stringify(event.output).slice(0, 200)}
              </p>
            )}
            {event.latency_ms && (
              <p className="text-xs text-muted-foreground mt-1">
                {event.latency_ms.toFixed(0)}ms
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
