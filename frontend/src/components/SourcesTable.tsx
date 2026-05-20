import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { sourcesApi, type DataSource, type SchemaColumn } from "../api/client";
import StatusBadge from "./StatusBadge";

interface Props {
  selectedIds: string[];
  onToggle: (id: string) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
}

function SourceSkeleton() {
  return (
    <div className="space-y-2 p-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="h-11 rounded-lg animate-pulse" style={{ background: "rgba(255,255,255,0.04)" }} />
      ))}
    </div>
  );
}

function SchemaPanel({ columns }: { columns: SchemaColumn[] }) {
  return (
    <motion.tr
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
    >
      <td colSpan={7} className="px-5 py-4" style={{ background: "rgba(255,255,255,0.02)", borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <p className="text-[10px] font-semibold text-white/30 uppercase tracking-widest mb-3">
          Schema — {columns.length} columns
        </p>
        <div className="overflow-auto max-h-64">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="text-white/25">
                <th className="text-left pr-6 py-1 font-medium">Column</th>
                <th className="text-left pr-6 py-1 font-medium">Type</th>
                <th className="text-left pr-6 py-1 font-medium">Nulls</th>
                <th className="text-left pr-6 py-1 font-medium">Unique</th>
                <th className="text-left py-1 font-medium">Sample values</th>
              </tr>
            </thead>
            <tbody>
              {columns.map((col) => (
                <tr key={col.name} style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
                  <td className="pr-6 py-1.5 font-mono font-medium text-indigo-300">{col.name}</td>
                  <td className="pr-6 py-1.5 text-white/35">{col.dtype}</td>
                  <td className="pr-6 py-1.5 text-white/35">{col.null_count}</td>
                  <td className="pr-6 py-1.5 text-white/35">{col.unique_count}</td>
                  <td className="py-1.5 text-white/25 truncate max-w-xs font-mono">
                    {col.sample_values.slice(0, 3).map(String).join(", ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </td>
    </motion.tr>
  );
}

export default function SourcesTable({ selectedIds, onToggle }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: sources = [], isLoading } = useQuery({
    queryKey: ["sources"],
    queryFn: () => sourcesApi.list().then((r) => r.data),
    refetchInterval: (query) =>
      (query.state.data ?? []).some(
        (s: DataSource) =>
          s.processing_status === "processing" || s.processing_status === "pending"
      )
        ? 3000
        : false,
  });

  if (isLoading) return <SourceSkeleton />;

  if (sources.length === 0) {
    return (
      <div className="py-16 text-center rounded-xl" style={{ border: "1px dashed rgba(255,255,255,0.08)" }}>
        <p className="text-sm text-white/30">No data sources yet.</p>
        <p className="text-xs text-white/20 mt-1">Upload a file above to get started.</p>
      </div>
    );
  }

  function toggleExpand(id: string) {
    setExpandedId((prev) => (prev === id ? null : id));
  }

  return (
    <div className="overflow-auto rounded-xl" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
      <table className="min-w-full text-sm">
        <thead>
          <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
            <th className="w-10 px-3 py-3" />
            <th className="px-3 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Name</th>
            <th className="px-3 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Type</th>
            <th className="px-3 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Size</th>
            <th className="px-3 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Rows</th>
            <th className="px-3 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Status</th>
            <th className="px-3 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Schema</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((src) => (
            <>
              <motion.tr
                key={src.id}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
                className={`transition-colors ${
                  selectedIds.includes(src.id) ? "bg-indigo-500/05" : "hover:bg-white/[0.02]"
                }`}
              >
                <td className="px-3 py-3">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(src.id)}
                    onChange={() => onToggle(src.id)}
                    disabled={src.processing_status !== "ready"}
                    className="rounded border-forge-border bg-forge-bg cursor-pointer accent-indigo-500"
                  />
                </td>
                <td
                  className="px-3 py-3 font-medium text-white/85 cursor-pointer"
                  onClick={() => src.processing_status === "ready" && onToggle(src.id)}
                >
                  {src.filename}
                </td>
                <td className="px-3 py-3 text-white/35 uppercase text-xs font-mono">{src.file_type}</td>
                <td className="px-3 py-3 text-white/35 font-mono text-xs">{formatBytes(src.file_size_bytes)}</td>
                <td className="px-3 py-3 text-white/35 font-mono text-xs">
                  {src.row_count != null ? src.row_count.toLocaleString() : "—"}
                </td>
                <td className="px-3 py-3">
                  <StatusBadge status={src.processing_status} />
                </td>
                <td className="px-3 py-3">
                  {src.processing_status === "ready" && src.schema_columns && src.schema_columns.length > 0 ? (
                    <button
                      onClick={() => toggleExpand(src.id)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                      {expandedId === src.id ? "Hide" : `View (${src.schema_columns.length} cols)`}
                    </button>
                  ) : (
                    <span className="text-xs text-slate-700">—</span>
                  )}
                </td>
              </motion.tr>
              <AnimatePresence>
                {expandedId === src.id && src.schema_columns && (
                  <SchemaPanel key={`${src.id}-schema`} columns={src.schema_columns} />
                )}
              </AnimatePresence>
            </>
          ))}
        </tbody>
      </table>
    </div>
  );
}
