"use client";

import { useState } from "react";
import { ChevronRight, ChevronDown } from "lucide-react";

interface JsonViewerProps {
  data: Record<string, unknown>;
}

export function JsonViewer({ data }: JsonViewerProps) {
  return (
    <div className="text-xs font-mono">
      <JsonNode value={data} depth={0} />
    </div>
  );
}

function JsonNode({ value, depth }: { value: unknown; depth: number }) {
  if (value === null) return <span className="text-gray-400">null</span>;
  if (value === undefined) return <span className="text-gray-400">undefined</span>;

  if (typeof value === "boolean") {
    return <span className="text-orange-600">{String(value)}</span>;
  }
  if (typeof value === "number") {
    return <span className="text-blue-600">{String(value)}</span>;
  }
  if (typeof value === "string") {
    if (value.length > 100) {
      return <CollapsibleString text={value} />;
    }
    return <span className="text-emerald-600">&quot;{value}&quot;</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-gray-400">[]</span>;
    return <CollapsibleArray arr={value} depth={depth} />;
  }

  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    if (entries.length === 0) return <span className="text-gray-400">{"{}"}</span>;
    return <CollapsibleObject entries={entries} depth={depth} />;
  }

  return <span>{String(value)}</span>;
}

function CollapsibleString({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <span>
      <button onClick={() => setOpen(!open)} className="text-gray-400 mr-1">
        {open ? <ChevronDown size={10} className="inline" /> : <ChevronRight size={10} className="inline" />}
      </button>
      <span className="text-emerald-600">
        &quot;{open ? text : text.slice(0, 100) + "..."}&quot;
      </span>
    </span>
  );
}

function CollapsibleArray({ arr, depth }: { arr: unknown[]; depth: number }) {
  const [open, setOpen] = useState(depth < 3);
  if (!open) {
    return (
      <span>
        <button onClick={() => setOpen(true)} className="text-gray-400 mr-1">
          <ChevronRight size={10} className="inline" />
        </button>
        <span className="text-gray-400">[{arr.length} items]</span>
      </span>
    );
  }
  return (
    <div>
      <button onClick={() => setOpen(false)} className="text-gray-400 mr-1">
        <ChevronDown size={10} className="inline" />
      </button>
      [
      <div style={{ paddingLeft: "16px" }}>
        {arr.map((item, i) => (
          <div key={i}>
            <JsonNode value={item} depth={depth + 1} />
            {i < arr.length - 1 && <span className="text-gray-400">,</span>}
          </div>
        ))}
      </div>
      ]
    </div>
  );
}

function CollapsibleObject({
  entries,
  depth,
}: {
  entries: [string, unknown][];
  depth: number;
}) {
  const [open, setOpen] = useState(depth < 3);
  if (!open) {
    return (
      <span>
        <button onClick={() => setOpen(true)} className="text-gray-400 mr-1">
          <ChevronRight size={10} className="inline" />
        </button>
        <span className="text-gray-400">{"{...}"}</span>
      </span>
    );
  }
  return (
    <div>
      <button onClick={() => setOpen(false)} className="text-gray-400 mr-1">
        <ChevronDown size={10} className="inline" />
      </button>
      {"{"}
      <div style={{ paddingLeft: "16px" }}>
        {entries.map(([key, val], i) => (
          <div key={key}>
            <span className="text-gray-600">{key}</span>
            <span className="text-gray-400">: </span>
            <JsonNode value={val} depth={depth + 1} />
            {i < entries.length - 1 && <span className="text-gray-400">,</span>}
          </div>
        ))}
      </div>
      {"}"}
    </div>
  );
}
