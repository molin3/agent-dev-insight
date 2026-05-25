"use client";

import { useEffect, useState } from "react";
import { useExperimentStore } from "@/stores/experiment-store";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2, FlaskConical, Play, RefreshCw } from "lucide-react";
import { formatMs, formatTokens, formatCost } from "@/lib/utils";

export default function ExperimentsPage() {
  const {
    experiments,
    isLoading,
    fetchExperiments,
    createExperiment,
    runExperiment,
    deleteExperiment,
  } = useExperimentStore();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [taskDesc, setTaskDesc] = useState("");
  const [desc, setDesc] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchExperiments();
  }, [fetchExperiments]);

  const handleCreate = async () => {
    if (!name.trim() || !taskDesc.trim()) return;
    await createExperiment(name, taskDesc, desc || undefined);
    setName("");
    setTaskDesc("");
    setDesc("");
    setShowCreate(false);
  };

  if (isLoading && experiments.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading...
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Experiments</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1 bg-primary text-white px-3 py-1.5 rounded-md text-sm"
        >
          <Plus size={14} /> New Experiment
        </button>
      </div>

      {showCreate && (
        <div className="bg-white border border-border rounded-lg p-4 mb-4">
          <input
            type="text"
            placeholder="Experiment name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="border border-border rounded px-3 py-1.5 text-sm w-full mb-2"
          />
          <textarea
            placeholder="Task description"
            value={taskDesc}
            onChange={(e) => setTaskDesc(e.target.value)}
            className="border border-border rounded px-3 py-1.5 text-sm w-full mb-2"
            rows={3}
          />
          <input
            type="text"
            placeholder="Description (optional)"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            className="border border-border rounded px-3 py-1.5 text-sm w-full mb-2"
          />
          <div className="flex gap-2">
            <button onClick={handleCreate} className="bg-primary text-white px-3 py-1 rounded text-sm">
              Create & Run
            </button>
            <button onClick={() => setShowCreate(false)} className="border border-border px-3 py-1 rounded text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {experiments.length === 0 ? (
        <p className="text-muted-foreground">No experiments yet.</p>
      ) : (
        <div className="space-y-3">
          {experiments.map((exp) => (
            <div key={exp.id}>
              <div className="bg-white border border-border rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-md bg-purple-50">
                    <FlaskConical size={18} className="text-purple-500" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{exp.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {exp.task_description.slice(0, 80)}
                      {exp.task_description.length > 80 ? "..." : ""}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      exp.status === "completed" ? "success"
                      : exp.status === "running" ? "default"
                      : exp.status === "failed" ? "error"
                      : "warning"
                    }
                  >
                    {exp.status}
                  </Badge>
                  {exp.status === "completed" && (
                    <button
                      onClick={() => runExperiment(exp.id)}
                      className="text-blue-500 hover:text-blue-700"
                      title="Re-run"
                    >
                      <RefreshCw size={14} />
                    </button>
                  )}
                  {exp.status === "pending" && (
                    <button
                      onClick={() => runExperiment(exp.id)}
                      className="text-emerald-500 hover:text-emerald-700"
                      title="Run now"
                    >
                      <Play size={14} />
                    </button>
                  )}
                  <button
                    onClick={() => deleteExperiment(exp.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
