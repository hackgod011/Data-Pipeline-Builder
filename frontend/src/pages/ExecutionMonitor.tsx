import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowLeft, Download } from "lucide-react";
import { executionsApi, pipelinesApi } from "../api/client";
import { usePipelineStore } from "../stores/pipelineStore";
import { useWebSocket } from "../hooks/useWebSocket";
import DAGCanvas from "../components/DAGCanvas";
import LogStream from "../components/LogStream";
import QualityReport from "../components/QualityReport";
import StatusBadge from "../components/StatusBadge";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000";

type RightPanel = "logs" | "profile";

export default function ExecutionMonitor() {
  const { executionId } = useParams<{ executionId: string }>();
  const navigate = useNavigate();
  const { plan, liveNodeStatus, setLiveNodeStatus, setPlan } = usePipelineStore();
  // null = not explicitly chosen; auto-derive from data
  const [userSelectedPanel, setUserSelectedPanel] = useState<RightPanel | null>(null);

  const { data: execution } = useQuery({
    queryKey: ["execution", executionId],
    queryFn: () => executionsApi.get(executionId!).then((r) => r.data),
    enabled: !!executionId,
    refetchInterval: (query) => {
      const s = query.state.data?.status;
      return s === "running" || s === "pending" ? 2000 : false;
    },
  });

  const { data: fetchedPipeline } = useQuery({
    queryKey: ["pipeline-for-execution", execution?.pipeline_id],
    queryFn: () => pipelinesApi.get(execution!.pipeline_id).then((r) => r.data),
    enabled: !!execution?.pipeline_id && !plan,
  });

  useEffect(() => {
    if (fetchedPipeline && !plan) setPlan(fetchedPipeline.plan);
  }, [fetchedPipeline, plan, setPlan]);

  const { logs, isConnected, isReconnecting, finalStatus } = useWebSocket(executionId ?? null);

  useEffect(() => {
    const last = logs[logs.length - 1];
    if (last?.type === "step_status" && last.step_id && last.status) {
      setLiveNodeStatus(last.step_id, last.status as "pending" | "running" | "success" | "failed");
    }
  }, [logs.length, setLiveNodeStatus]);

  // Derive active panel: auto-switch to profile when results arrive unless user picked logs
  const rightPanel: RightPanel =
    userSelectedPanel ?? (execution?.output_profile ? "profile" : "logs");

  const status = (finalStatus ?? execution?.status ?? "pending") as "pending" | "running" | "success" | "failed";
  const outputFilename = execution?.output_file_path
    ? execution.output_file_path.split(/[\\/]/).pop()
    : null;

  const qScore = execution?.output_profile?.quality_score;

  return (
    <div className="h-screen bg-black flex flex-col overflow-hidden">
      {/* Header */}
      <header className="h-14 flex items-center justify-between px-5 shrink-0" style={{ background: "rgba(0,0,0,0.85)", backdropFilter: "blur(20px)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white transition-colors"
          >
            <ArrowLeft size={14} strokeWidth={2} />
            Back
          </button>
          <span className="text-white/15">·</span>
          <h1 className="text-sm font-semibold text-white/80">Execution Monitor</h1>
          <StatusBadge status={status} />
        </div>
        {outputFilename && (
          <motion.a
            href={`${API_BASE}/api/v1/outputs/${outputFilename}`}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="px-4 py-1.5 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 transition-colors flex items-center gap-2"
          >
            <Download size={14} strokeWidth={2} />
            Download Output
          </motion.a>
        )}
      </header>

      {/* Error banner */}
      {status === "failed" && execution?.error_message && (
        <div className="mx-5 mt-3 p-3 bg-red-900/20 border border-red-700/50 rounded-lg text-sm text-red-300">
          <span className="font-semibold text-red-400">Error: </span>
          {execution.error_message}
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 grid grid-cols-[1fr_400px] overflow-hidden">
        <DAGCanvas plan={plan} liveStatus={liveNodeStatus} />

        <div className="flex flex-col overflow-hidden" style={{ borderLeft: "1px solid rgba(255,255,255,0.06)" }}>
          {/* Tab bar */}
          <div className="flex shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)", background: "rgba(0,0,0,0.6)" }}>
            {(["logs", "profile"] as RightPanel[]).map((panel) => (
              <button
                key={panel}
                onClick={() => setUserSelectedPanel(panel)}
                disabled={panel === "profile" && !execution?.output_profile}
                className={`px-4 py-2.5 text-xs font-medium transition-colors relative disabled:opacity-30 ${
                  rightPanel === panel ? "text-white" : "text-white/30 hover:text-white/60"
                }`}
              >
                {panel === "logs" ? "Logs" : "Quality Report"}
                {panel === "profile" && qScore != null && (
                  <span className={`ml-1.5 text-[10px] px-1 py-0.5 rounded font-bold ${
                    qScore >= 90 ? "bg-emerald-900/50 text-emerald-400"
                    : qScore >= 70 ? "bg-amber-900/50 text-amber-400"
                    : "bg-red-900/50 text-red-400"
                  }`}>
                    {qScore}
                  </span>
                )}
                {rightPanel === panel && (
                  <motion.div
                    layoutId="exec-tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-indigo-500"
                  />
                )}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-hidden">
            {rightPanel === "logs" ? (
              <LogStream logs={logs} isConnected={isConnected} isReconnecting={isReconnecting} />
            ) : execution?.output_profile ? (
              <QualityReport profile={execution.output_profile} />
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
