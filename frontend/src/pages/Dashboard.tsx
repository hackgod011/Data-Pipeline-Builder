import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Zap } from "lucide-react";
import { sourcesApi } from "../api/client";
import AppNav from "../components/AppNav";
import FileDropzone from "../components/FileDropzone";
import SourcesTable from "../components/SourcesTable";
import PageTransition from "../components/PageTransition";

type UploadTab = "file" | "database";

const INPUT_CLS =
  "w-full rounded-lg px-3 py-2.5 text-sm text-white placeholder-white/20 focus:outline-none transition";

const DB_INPUT_STYLE: React.CSSProperties = {
  background: "rgba(255,255,255,0.04)",
  border: "1px solid rgba(255,255,255,0.08)",
  color: "white",
};

function dbFocus(e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
  e.target.style.border = "1px solid rgba(99,102,241,0.5)";
  e.target.style.boxShadow = "0 0 0 3px rgba(99,102,241,0.08)";
}
function dbBlur(e: React.FocusEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
  e.target.style.border = "1px solid rgba(255,255,255,0.08)";
  e.target.style.boxShadow = "none";
}

export default function Dashboard() {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [tab, setTab] = useState<UploadTab>("file");
  const [dbType, setDbType] = useState<"sqlite" | "postgresql">("sqlite");
  const [connStr, setConnStr] = useState("");
  const [dbQuery, setDbQuery] = useState("SELECT * FROM main_table LIMIT 1000");
  const [dbName, setDbName] = useState("");

  const navigate = useNavigate();
  const qc = useQueryClient();

  const upload = useMutation({
    mutationFn: (files: File[]) => sourcesApi.upload(files),
    onSuccess: () => {
      toast.success("Files uploaded — processing in background");
      qc.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: (err: unknown) => {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      toast.error(detail ?? "Upload failed. Check file type and try again.");
    },
  });

  const connectDb = useMutation({
    mutationFn: () =>
      sourcesApi.connectDb({ db_type: dbType, connection_string: connStr, query: dbQuery, name: dbName || undefined }),
    onSuccess: () => {
      toast.success("Database connected successfully");
      setConnStr("");
      qc.invalidateQueries({ queryKey: ["sources"] });
    },
    onError: (err: unknown) => {
      const detail =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      toast.error(detail ?? "Database connection failed.");
    },
  });

  const toggleId = (id: string) =>
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );

  return (
    <PageTransition>
      <AppNav />

      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-8 space-y-8">
        {/* Upload section */}
        <div className="rounded-xl overflow-hidden" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
          {/* Tab bar */}
          <div className="flex" style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
            {(["file", "database"] as UploadTab[]).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-5 py-3 text-sm font-medium transition-colors relative ${
                  tab === t ? "text-white" : "text-white/30 hover:text-white/60"
                }`}
              >
                {t === "file" ? "Upload File" : "Connect Database"}
                {tab === t && (
                  <motion.div
                    layoutId="tab-underline"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500"
                  />
                )}
              </button>
            ))}
          </div>

          <div className="p-5">
            <AnimatePresence mode="wait">
              {tab === "file" ? (
                <motion.div
                  key="file"
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 8 }}
                  transition={{ duration: 0.15 }}
                >
                  <FileDropzone
                    onFilesAccepted={(files) => upload.mutate(files)}
                    isUploading={upload.isPending}
                  />
                </motion.div>
              ) : (
                <motion.div
                  key="db"
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -8 }}
                  transition={{ duration: 0.15 }}
                  className="space-y-4"
                >
                  <p className="text-sm text-white/40">
                    Connect an external database and import query results as a data source.
                  </p>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[11px] font-medium text-white/40 mb-1.5 tracking-widest uppercase">Database type</label>
                      <select
                        value={dbType}
                        onChange={(e) => setDbType(e.target.value as "sqlite" | "postgresql")}
                        className={INPUT_CLS}
                        style={DB_INPUT_STYLE}
                        onFocus={dbFocus}
                        onBlur={dbBlur}
                      >
                        <option value="sqlite" style={{ background: "#09090F", color: "white" }}>SQLite (file path)</option>
                        <option value="postgresql" style={{ background: "#09090F", color: "white" }}>PostgreSQL (DSN)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-[11px] font-medium text-white/40 mb-1.5 tracking-widest uppercase">Source name (optional)</label>
                      <input
                        value={dbName}
                        onChange={(e) => setDbName(e.target.value)}
                        placeholder="my_database"
                        className={INPUT_CLS}
                        style={DB_INPUT_STYLE}
                        onFocus={dbFocus}
                        onBlur={dbBlur}
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-white/40 mb-1.5 tracking-widest uppercase">
                      {dbType === "sqlite" ? "File path" : "Connection string"}
                    </label>
                    <input
                      value={connStr}
                      onChange={(e) => setConnStr(e.target.value)}
                      placeholder={dbType === "sqlite" ? "/path/to/database.db" : "postgresql://user:pass@host:5432/db"}
                      className={INPUT_CLS + " font-mono"}
                      style={DB_INPUT_STYLE}
                      onFocus={dbFocus}
                      onBlur={dbBlur}
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-white/40 mb-1.5 tracking-widest uppercase">SQL query</label>
                    <textarea
                      rows={3}
                      value={dbQuery}
                      onChange={(e) => setDbQuery(e.target.value)}
                      className={INPUT_CLS + " font-mono resize-none"}
                      style={DB_INPUT_STYLE}
                      onFocus={dbFocus}
                      onBlur={dbBlur}
                    />
                  </div>
                  <button
                    onClick={() => connectDb.mutate()}
                    disabled={!connStr.trim() || connectDb.isPending}
                    className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-500 disabled:opacity-50 transition-colors"
                  >
                    {connectDb.isPending ? "Connecting…" : "Connect & Import"}
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Sources section */}
        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[11px] font-semibold text-white/35 uppercase tracking-widest">Data Sources</h2>
          </div>
          <SourcesTable selectedIds={selectedIds} onToggle={toggleId} />
        </section>

        {/* Build pipeline CTA */}
        <AnimatePresence>
          {selectedIds.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 12 }}
              className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50"
            >
              <button
                onClick={() => navigate(`/build?sources=${selectedIds.join(",")}`)}
                className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-500 font-semibold text-sm shadow-2xl shadow-indigo-900/60 flex items-center gap-2 transition-colors"
                style={{ boxShadow: "0 0 0 1px rgba(99,102,241,0.4), 0 8px 32px rgba(99,102,241,0.3)" }}
              >
                <Zap size={15} strokeWidth={2.5} />
                Build Pipeline with {selectedIds.length} source{selectedIds.length > 1 ? "s" : ""}
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </PageTransition>
  );
}
