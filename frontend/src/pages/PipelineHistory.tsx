import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { Plus, RotateCcw, CalendarPlus, FileCode2, Loader2 } from "lucide-react";
import { pipelinesApi, executionsApi, schedulesApi, type Pipeline } from "../api/client";
import { usePipelineStore } from "../stores/pipelineStore";
import AppNav from "../components/AppNav";
import PageTransition from "../components/PageTransition";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const INPUT_CLS =
  "w-full bg-forge-bg border border-forge-border rounded-lg px-3 py-2.5 text-sm text-white placeholder-slate-600 font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition";

function RerunButton({ pipeline }: { pipeline: Pipeline }) {
  const navigate = useNavigate();
  const { resetExecution } = usePipelineStore();
  const qc = useQueryClient();

  const rerun = useMutation({
    mutationFn: () => executionsApi.execute(pipeline.id).then((r) => r.data),
    onSuccess: (data) => {
      resetExecution();
      qc.invalidateQueries({ queryKey: ["pipelines"] });
      toast.success("Re-running pipeline");
      navigate(`/executions/${data.execution_id}`);
    },
    onError: () => toast.error("Failed to start re-run"),
  });

  return (
    <button
      onClick={() => rerun.mutate()}
      disabled={rerun.isPending}
      className="flex items-center gap-1.5 px-2.5 py-1 text-xs bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 disabled:opacity-50 transition-colors"
    >
      {rerun.isPending ? <Loader2 size={11} className="animate-spin" /> : <RotateCcw size={11} strokeWidth={2.5} />}
      {rerun.isPending ? "Starting…" : "Re-run"}
    </button>
  );
}

function ScheduleButton({ pipeline }: { pipeline: Pipeline }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [cron, setCron] = useState("0 9 * * 1-5");

  const upsert = useMutation({
    mutationFn: () => schedulesApi.upsert(pipeline.id, cron),
    onSuccess: () => {
      setOpen(false);
      toast.success("Schedule saved");
      qc.invalidateQueries({ queryKey: ["schedules"] });
    },
    onError: () => toast.error("Invalid cron expression or server error."),
  });

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center gap-1.5 px-2.5 py-1 text-xs border border-forge-border rounded-lg text-slate-400 hover:text-white hover:border-forge-border-hover transition-colors"
      >
        <CalendarPlus size={11} strokeWidth={2} />
        Schedule
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={(e) => e.target === e.currentTarget && setOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0, y: 8 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.9, opacity: 0, y: 8 }}
              transition={{ duration: 0.2 }}
              className="rounded-2xl shadow-2xl w-full max-w-sm p-6 space-y-4"
              style={{ background: "#09090F", border: "1px solid rgba(255,255,255,0.1)" }}
            >
              <div>
                <h2 className="text-base font-semibold text-white">Schedule Pipeline</h2>
                <p className="text-xs text-slate-500 mt-0.5 truncate">{pipeline.name}</p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">
                  Cron expression (UTC)
                </label>
                <input
                  value={cron}
                  onChange={(e) => setCron(e.target.value)}
                  className={INPUT_CLS}
                  placeholder="0 9 * * 1-5"
                />
                <p className="text-xs text-slate-600 mt-1.5">
                  e.g. <code className="text-indigo-400">0 9 * * 1-5</code> = weekdays at 9am UTC
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-1">
                <button
                  onClick={() => setOpen(false)}
                  className="px-3 py-1.5 text-sm border border-forge-border rounded-lg text-slate-400 hover:text-white transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => upsert.mutate()}
                  disabled={upsert.isPending}
                  className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 disabled:opacity-50 transition-colors"
                >
                  {upsert.isPending ? "Saving…" : "Save schedule"}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default function PipelineHistory() {
  const navigate = useNavigate();

  const { data: pipelines = [], isLoading } = useQuery({
    queryKey: ["pipelines"],
    queryFn: () => pipelinesApi.list().then((r) => r.data),
  });

  return (
    <PageTransition>
      <AppNav />
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-lg font-semibold text-white">Pipeline History</h1>
          <button
            onClick={() => navigate("/build")}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-500 transition-colors flex items-center gap-2"
          >
            <Plus size={14} strokeWidth={2.5} />
            New Pipeline
          </button>
        </div>

        {isLoading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-14 rounded-xl animate-pulse" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }} />
            ))}
          </div>
        )}

        {!isLoading && pipelines.length === 0 && (
          <div className="text-center py-24 rounded-xl" style={{ border: "1px dashed rgba(255,255,255,0.08)" }}>
            <p className="text-white/35 text-sm mb-4">No pipelines yet.</p>
            <button
              onClick={() => navigate("/build")}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-500 transition-colors"
            >
              Build your first pipeline
            </button>
          </div>
        )}

        {pipelines.length > 0 && (
          <div className="rounded-xl overflow-hidden" style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}>
            <table className="min-w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                  <th className="px-4 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Name</th>
                  <th className="px-4 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Prompt</th>
                  <th className="px-4 py-3 text-center text-[10px] font-medium text-white/30 uppercase tracking-widest">Version</th>
                  <th className="px-4 py-3 text-left text-[10px] font-medium text-white/30 uppercase tracking-widest">Created</th>
                  <th className="px-4 py-3 text-right text-[10px] font-medium text-white/30 uppercase tracking-widest">Actions</th>
                </tr>
              </thead>
              <tbody>
                {pipelines.map((p, i) => (
                  <motion.tr
                    key={p.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                    style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
                    className="hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-4 py-3 font-medium text-white/85 max-w-[160px] truncate">{p.name}</td>
                    <td className="px-4 py-3 text-white/35 max-w-[240px] truncate text-xs">{p.nl_prompt}</td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-xs text-white/35 font-mono px-1.5 py-0.5 rounded" style={{ background: "rgba(255,255,255,0.06)" }}>
                        v{p.version}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-white/35 text-xs whitespace-nowrap">{formatDate(p.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <RerunButton pipeline={p} />
                        <ScheduleButton pipeline={p} />
                        <a
                          href={`${API_BASE}/api/v1/pipelines/${p.id}/export`}
                          className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-lg text-white/35 hover:text-white transition-colors"
                          style={{ border: "1px solid rgba(255,255,255,0.1)" }}
                        >
                          <FileCode2 size={11} strokeWidth={2} />
                          Export .py
                        </a>
                      </div>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </PageTransition>
  );
}
