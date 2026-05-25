"use client";

import { useEffect, useState } from "react";
import { useDatasetStore } from "@/stores/dataset-store";
import { Badge } from "@/components/ui/badge";
import { Plus, Trash2 } from "lucide-react";

export default function DatasetsPage() {
  const { datasets, isLoading, fetchDatasets, createDataset, deleteDataset } =
    useDatasetStore();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

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

  if (isLoading && datasets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-muted-foreground">
        Loading...
      </div>
    );
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
            <button
              onClick={handleCreate}
              className="bg-primary text-white px-3 py-1 rounded text-sm"
            >
              Create
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="border border-border px-3 py-1 rounded text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {datasets.length === 0 ? (
        <p className="text-muted-foreground">
          No datasets yet. Create one to start regression testing.
        </p>
      ) : (
        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="text-left p-3 font-medium">Name</th>
                <th className="text-left p-3 font-medium">Version</th>
                <th className="text-left p-3 font-medium">Created</th>
                <th className="text-right p-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((ds) => (
                <tr key={ds.id} className="border-t border-border hover:bg-muted/50">
                  <td className="p-3 font-medium">{ds.name}</td>
                  <td className="p-3">
                    <Badge variant="default">v{ds.version}</Badge>
                  </td>
                  <td className="p-3 text-muted-foreground text-xs">
                    {new Date(ds.created_at).toLocaleDateString()}
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => deleteDataset(ds.id)}
                      className="text-red-500 hover:text-red-700"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
