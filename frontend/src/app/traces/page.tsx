"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useTraceStore } from "@/stores/trace-store";
import { Badge } from "@/components/ui/badge";
import { formatMs, formatTokens, formatCost } from "@/lib/utils";
import { Search } from "lucide-react";

export default function TracesPage() {
  const { traces, total, isLoading, fetchTraces, page, setPage } = useTraceStore();
  const [keyword, setKeyword] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    fetchTraces({ keyword: keyword || undefined, status: status || undefined });
  }, [fetchTraces, page]);

  const handleSearch = () => {
    setPage(1);
    fetchTraces({ keyword: keyword || undefined, status: status || undefined });
  };

  const totalPages = Math.ceil(total / 20);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Traces</h2>

      <div className="flex gap-2 mb-4">
        <div className="flex items-center border border-border rounded-md px-3 py-1.5 flex-1 max-w-xs">
          <Search size={14} className="text-muted-foreground mr-2" />
          <input
            type="text"
            placeholder="Search traces..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="outline-none text-sm flex-1 bg-transparent"
          />
        </div>
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="border border-border rounded-md px-3 py-1.5 text-sm bg-white"
        >
          <option value="">All Status</option>
          <option value="completed">Completed</option>
          <option value="in_progress">In Progress</option>
          <option value="error">Error</option>
        </select>
        <button
          onClick={handleSearch}
          className="bg-primary text-white px-4 py-1.5 rounded-md text-sm"
        >
          Search
        </button>
      </div>

      {isLoading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : (
        <>
          <div className="border border-border rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted">
                <tr>
                  <th className="text-left p-3 font-medium">Name</th>
                  <th className="text-left p-3 font-medium">Status</th>
                  <th className="text-left p-3 font-medium">Time</th>
                  <th className="text-left p-3 font-medium">Latency</th>
                  <th className="text-left p-3 font-medium">Tokens</th>
                  <th className="text-left p-3 font-medium">Cost</th>
                </tr>
              </thead>
              <tbody>
                {traces.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-6 text-center text-muted-foreground">
                      No traces found. Start by sending traces from your agent.
                    </td>
                  </tr>
                ) : (
                  traces.map((t) => (
                    <tr key={t.id} className="border-t border-border hover:bg-muted/50">
                      <td className="p-3">
                        <Link href={`/traces/${t.id}`} className="text-primary hover:underline font-medium">
                          {t.name}
                        </Link>
                      </td>
                      <td className="p-3">
                        <Badge
                          variant={
                            t.status === "completed" ? "success"
                            : t.status === "error" ? "error"
                            : "default"
                          }
                        >
                          {t.status}
                        </Badge>
                      </td>
                      <td className="p-3 text-muted-foreground text-xs">
                        {t.started_at ? new Date(t.started_at).toLocaleString() : "-"}
                      </td>
                      <td className="p-3">
                        {t.total_latency_ms ? formatMs(t.total_latency_ms) : "-"}
                      </td>
                      <td className="p-3">
                        {t.total_tokens ? formatTokens(t.total_tokens) : "-"}
                      </td>
                      <td className="p-3">
                        {t.total_cost != null ? formatCost(t.total_cost) : "-"}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center gap-2 mt-4 justify-center">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="px-3 py-1 border rounded text-sm disabled:opacity-50"
              >
                Prev
              </button>
              <span className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="px-3 py-1 border rounded text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
