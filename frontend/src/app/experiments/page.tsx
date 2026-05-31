"use client";

import { useEffect, useState } from "react";
import { useExperimentStore } from "@/stores/experiment-store";
import { ComparisonChart } from "@/components/experiments/comparison-chart";
import { Badge } from "@/components/ui/badge";
import { SkeletonTable } from "@/components/ui/skeleton";
import { Plus, Trash2, FlaskConical, Play, RefreshCw, ChevronRight, ChevronDown } from "lucide-react";
import { formatMs, formatTokens, formatCost } from "@/lib/utils";

export default function ExperimentsPage() {
  const {
    experiments,
    currentExperiment,
    isLoading,
    fetchExperiments,
    fetchExperiment,
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

  const handleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    await fetchExperiment(id);
  };

  const handleRerun = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await runExperiment(id);
    await fetchExperiment(id);
  };

  if (isLoading && experiments.length === 0) {
    return <SkeletonTable />;
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
            placeholder="Task description (e.g. 'Compare model performance on customer service Q&A')"
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
        <div className="text-center py-16 text-muted-foreground">
          <FlaskConical size={48} className="mx-auto mb-3 opacity-30" />
          <p>No experiments yet.</p>
          <p className="text-sm mt-1">Create an experiment to compare models on the same task.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {experiments.map((exp) => (
            <div key={exp.id}>
              <div
                className="bg-white border border-border rounded-lg p-4 flex items-center justify-between hover:bg-muted/30 cursor-pointer"
                onClick={() => handleExpand(exp.id)}
              >
                <div className="flex items-center gap-3">
                  {expandedId === exp.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  <div className="p-2 rounded-md bg-purple-50">
                    <FlaskConical size={18} className="text-purple-500" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{exp.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {exp.task_description?.slice(0, 80)}
                      {exp.task_description?.length > 80 ? "..." : ""}
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
                  <button
                    onClick={(e) => handleRerun(e, exp.id)}
                    className="text-blue-500 hover:text-blue-700"
                    title={exp.status === "completed" ? "Re-run" : "Run now"}
                  >
                    {exp.status === "completed" ? <RefreshCw size={14} /> : <Play size={14} />}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteExperiment(exp.id); }}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {expandedId === exp.id && currentExperiment && (
                <div className="bg-muted/30 border border-t-0 border-border rounded-b-lg p-4 ml-6">
                  {currentExperiment.runs && currentExperiment.runs.length > 0 ? (
                    <>
                      <h4 className="text-sm font-semibold mb-3">
                        Runs ({currentExperiment.runs.length})
                      </h4>
                      <div className="space-y-3">
                        {currentExperiment.runs.map((run, idx) => (
                          <div key={run.id || idx} className="bg-white border border-border rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium bg-purple-100 text-purple-700 px-2 py-0.5 rounded">
                                  {run.model_name || `Run ${idx + 1}`}
                                </span>
                                <Badge variant={run.status === "completed" ? "success" : "default"}>
                                  {run.status}
                                </Badge>
                              </div>
                            </div>
                            <div className="grid grid-cols-4 gap-3 text-xs">
                              <div>
                                <span className="text-muted-foreground">Latency</span>
                                <p className="font-medium">{run.avg_latency_ms ? formatMs(run.avg_latency_ms) : "-"}</p>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Tokens</span>
                                <p className="font-medium">{run.total_tokens ? formatTokens(run.total_tokens) : "-"}</p>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Cost</span>
                                <p className="font-medium">{run.total_cost != null ? formatCost(run.total_cost) : "-"}</p>
                              </div>
                              <div>
                                <span className="text-muted-foreground">Completion</span>
                                <p className="font-medium">
                                  {run.completion_rate != null ? `${(run.completion_rate * 100).toFixed(0)}%` : "-"}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {currentExperiment.comparison && (
                        <div className="mt-4 bg-white border border-border rounded-lg p-3">
                          <h4 className="text-sm font-semibold mb-2">Comparison</h4>
                          <ComparisonChart comparison={currentExperiment.comparison as { models: string[]; metrics: { [key: string]: { [model: string]: number } } }} />
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-4 text-muted-foreground text-sm">
                      <p>No runs yet. Click the play button to execute this experiment.</p>
                      <p className="text-xs mt-1">
                        Add runs via API: POST /api/experiments/{exp.id}/run
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
