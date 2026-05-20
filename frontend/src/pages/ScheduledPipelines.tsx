import { useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { Clock, Pause, Play, Trash2 } from "lucide-react";
import { schedulesApi, type Schedule } from "../api/client";
import AppNav from "../components/AppNav";
import PageTransition from "../components/PageTransition";

function cronHint(expr: string): string {
  const parts = expr.trim().split(/\s+/);
  if (parts.length !== 5) return expr;
  const [min, hour, dom, month, dow] = parts;
  if (min === "0" && hour === "*" && dom === "*" && month === "*" && dow === "*") return "Every hour";
  if (dom === "*" && month === "*" && dow === "*") return `Daily at ${hour}:${min.padStart(2, "0")} UTC`;
  if (dom === "*" && month === "*") return `Weekly (${dow}) at ${hour}:${min.padStart(2, "0")} UTC`;
  return expr;
}

function NextRunCell({ iso }: { iso: string | null }) {
  if (!iso) return <span className="text-white/20 text-xs">—</span>;
  return <span className="text-xs text-white/50">{new Date(iso).toLocaleString()}</span>;
}

export default function ScheduledPipelines() {
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: schedules, isLoading } = useQuery({
    queryKey: ["schedules"],
    queryFn: () => schedulesApi.list().then((r) => r.data),
  });

  const toggleMut = useMutation({
    mutationFn: (s: Schedule) => schedulesApi.toggle(s.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["schedules"] }),
    onError: () => toast.error("Failed to toggle schedule."),
  });

  const deleteMut = useMutation({
    mutationFn: (s: Schedule) => schedulesApi.remove(s.pipeline_id),
    onSuccess: () => {
      toast.success("Schedule deleted");
      qc.invalidateQueries({ queryKey: ["schedules"] });
    },
    onError: () => toast.error("Failed to delete schedule."),
  });

  return (
    <PageTransition>
      <AppNav />
      <main className="flex-1 max-w-4xl mx-auto w-full px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-lg font-semibold text-white">Scheduled Pipelines</h1>
          <button
            onClick={() => navigate("/history")}
            className="px-4 py-2 text-sm rounded-lg text-white/40 hover:text-white transition-colors"
            style={{ border: "1px solid rgba(255,255,255,0.1)" }}
          >
            + Add schedule
          </button>
        </div>

        {isLoading && (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-20 rounded-xl animate-pulse" style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)" }} />
            ))}
          </div>
        )}

        {!isLoading && (!schedules || schedules.length === 0) && (
          <div className="text-center py-24 rounded-xl" style={{ border: "1px dashed rgba(255,255,255,0.08)" }}>
            <div className="w-11 h-11 mx-auto mb-4 rounded-xl flex items-center justify-center" style={{ background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)" }}>
              <Clock size={18} className="text-white/25" strokeWidth={1.5} />
            </div>
            <p className="text-white/40 font-medium mb-1">No scheduled pipelines</p>
            <p className="text-xs text-white/25">
              Go to Pipeline History and click "Schedule" on any pipeline.
            </p>
          </div>
        )}

        <div className="space-y-3">
          {schedules?.map((s, i) => (
            <motion.div
              key={s.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.06 }}
              className="rounded-xl p-4 flex items-center justify-between gap-4"
              style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.07)" }}
            >
              {/* Left: name + cron */}
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-white/85 truncate">
                  {s.pipeline_name ?? s.pipeline_id.slice(0, 8)}
                </p>
                <p className="text-xs text-white/25 mt-0.5 font-mono">{s.cron_expression}</p>
                <p className="text-xs text-white/20">{cronHint(s.cron_expression)}</p>
              </div>

              {/* Center: next/last run */}
              <div className="text-right shrink-0 hidden sm:block">
                <p className="text-[10px] text-white/25 uppercase tracking-widest mb-0.5">Next run</p>
                <NextRunCell iso={s.next_run_at} />
                {s.last_run_at && (
                  <p className="text-[10px] text-white/20 mt-0.5">
                    Last: {new Date(s.last_run_at).toLocaleString()}
                  </p>
                )}
              </div>

              {/* Right: status + actions */}
              <div className="flex items-center gap-2 shrink-0">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  s.is_active
                    ? "text-emerald-400"
                    : "text-white/30"
                }`} style={{ background: s.is_active ? "rgba(16,185,129,0.1)" : "rgba(255,255,255,0.05)", border: s.is_active ? "1px solid rgba(16,185,129,0.25)" : "1px solid rgba(255,255,255,0.1)" }}>
                  {s.is_active ? "Active" : "Paused"}
                </span>

                <button
                  onClick={() => toggleMut.mutate(s)}
                  disabled={toggleMut.isPending}
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg text-white/35 hover:text-white transition-colors"
                  style={{ border: "1px solid rgba(255,255,255,0.1)" }}
                >
                  {s.is_active ? <Pause size={11} strokeWidth={2} /> : <Play size={11} strokeWidth={2} />}
                  {s.is_active ? "Pause" : "Resume"}
                </button>

                <button
                  onClick={() => { if (confirm("Delete this schedule?")) deleteMut.mutate(s); }}
                  disabled={deleteMut.isPending}
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 text-red-500/70 hover:text-red-400 rounded-lg hover:bg-red-500/08 transition-colors"
                  style={{ border: "1px solid rgba(239,68,68,0.2)" }}
                >
                  <Trash2 size={11} strokeWidth={2} />
                  Delete
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      </main>
    </PageTransition>
  );
}
