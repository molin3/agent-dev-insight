"use client";

import { useEffect, useState } from "react";
import { useDatasetStore } from "@/stores/dataset-store";
import { notify } from "@/lib/toast";
import { Badge } from "@/components/ui/badge";
import { SkeletonTable } from "@/components/ui/skeleton";
import { Plus, Trash2, ChevronRight, ChevronDown, FileText } from "lucide-react";

export default function DatasetsPage() {
  const { datasets, currentDataset, isLoading, fetchDatasets, fetchDataset, createDataset, deleteDataset, addItem } =
    useDatasetStore();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [showAddItem, setShowAddItem] = useState(false);
  const [itemInput, setItemInput] = useState("");
  const [itemExpected, setItemExpected] = useState("");

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  const handleCreate = async () => {
    if (!name.trim()) return;
    await createDataset(name, desc || undefined);
    setName("");
    setDesc("");
    setShowCreate(false);
  };

  const handleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);
    await fetchDataset(id);
  };

  const handleAddItem = async () => {
    if (!expandedId || !itemInput.trim()) return;
    try {
      const input = JSON.parse(itemInput);
      await addItem(expandedId, input, itemExpected || undefined);
      setItemInput("");
      setItemExpected("");
      setShowAddItem(false);
    } catch {
      notify.error("Input must be valid JSON, e.g.: {\"query\": \"question\"}");
    }
  };

  if (isLoading && datasets.length === 0) {
    return <SkeletonTable />;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Datasets</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1 bg-primary text-white px-3 py-1.5 rounded-md text-sm"
        >
          <Plus size={14} /> New Dataset
        </button>
      </div>

      {showCreate && (
        <div className="bg-white border border-border rounded-lg p-4 mb-4">
          <input
            type="text"
            placeholder="Dataset name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="border border-border rounded px-3 py-1.5 text-sm w-full mb-2"
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
              Create
            </button>
            <button onClick={() => setShowCreate(false)} className="border border-border px-3 py-1 rounded text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {datasets.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <FileText size={48} className="mx-auto mb-3 opacity-30" />
          <p>No datasets yet.</p>
          <p className="text-sm mt-1">Create a dataset to start regression testing.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {datasets.map((ds) => (
            <div key={ds.id}>
              <div
                className="bg-white border border-border rounded-lg p-4 flex items-center justify-between hover:bg-muted/30 cursor-pointer"
                onClick={() => handleExpand(ds.id)}
              >
                <div className="flex items-center gap-3">
                  {expandedId === ds.id ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                  <div>
                    <p className="font-medium text-sm">{ds.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {ds.description || "No description"} · v{ds.version}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="default">v{ds.version}</Badge>
                  <button
                    onClick={(e) => { e.stopPropagation(); deleteDataset(ds.id); }}
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              {expandedId === ds.id && (
                <div className="bg-muted/30 border border-t-0 border-border rounded-b-lg p-4 ml-6">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-semibold">
                      Test Items ({currentDataset?.items?.length || 0})
                    </h4>
                    <button
                      onClick={() => setShowAddItem(!showAddItem)}
                      className="flex items-center gap-1 text-xs bg-primary text-white px-2 py-1 rounded"
                    >
                      <Plus size={12} /> Add Item
                    </button>
                  </div>

                  {showAddItem && (
                    <div className="bg-white border border-border rounded p-3 mb-3">
                      <textarea
                        placeholder='Input (JSON): {"query": "用户问题"}'
                        value={itemInput}
                        onChange={(e) => setItemInput(e.target.value)}
                        className="border border-border rounded px-3 py-1.5 text-sm w-full mb-2"
                        rows={3}
                      />
                      <input
                        type="text"
                        placeholder="Expected output (optional)"
                        value={itemExpected}
                        onChange={(e) => setItemExpected(e.target.value)}
                        className="border border-border rounded px-3 py-1.5 text-sm w-full mb-2"
                      />
                      <div className="flex gap-2">
                        <button onClick={handleAddItem} className="bg-primary text-white px-3 py-1 rounded text-sm">
                          Save
                        </button>
                        <button onClick={() => setShowAddItem(false)} className="border px-3 py-1 rounded text-sm">
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}

                  {currentDataset?.items && currentDataset.items.length > 0 ? (
                    <div className="space-y-2">
                      {currentDataset.items.map((item, idx) => (
                        <div key={item.id || idx} className="bg-white border border-border rounded p-3 text-sm">
                          <div className="flex gap-2 mb-1">
                            <span className="text-muted-foreground text-xs font-medium">Input:</span>
                            <code className="text-xs bg-muted px-1 rounded">
                              {JSON.stringify(item.input)}
                            </code>
                          </div>
                          {item.expected_output && (
                            <div className="flex gap-2">
                              <span className="text-muted-foreground text-xs font-medium">Expected:</span>
                              <span className="text-xs">{item.expected_output}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      No test items yet. Add one manually or create from a Trace via API.
                    </p>
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
