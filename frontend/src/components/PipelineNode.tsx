import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { motion } from "framer-motion";
import clsx from "clsx";

export interface PipelineNodeData {
  label: string;
  stepType: "extract" | "transform" | "load" | "validate";
  description: string;
  liveStatus?: "pending" | "running" | "success" | "failed";
}

const TYPE_STYLES: Record<string, { bg: string; border: string; badge: string; dot: string }> = {
  extract:   { bg: "bg-indigo-900/60",  border: "border-indigo-600", badge: "bg-indigo-700/60 text-indigo-200",   dot: "bg-indigo-400" },
  transform: { bg: "bg-emerald-900/60", border: "border-emerald-600",badge: "bg-emerald-700/60 text-emerald-200",  dot: "bg-emerald-400" },
  load:      { bg: "bg-amber-900/60",   border: "border-amber-600",  badge: "bg-amber-700/60 text-amber-200",     dot: "bg-amber-400" },
  validate:  { bg: "bg-rose-900/60",    border: "border-rose-600",   badge: "bg-rose-700/60 text-rose-200",       dot: "bg-rose-400" },
};

const STATUS_RING: Record<string, string> = {
  running: "ring-2 ring-amber-400/60 ring-offset-1 ring-offset-forge-bg",
  success: "ring-2 ring-emerald-400/60 ring-offset-1 ring-offset-forge-bg",
  failed:  "ring-2 ring-red-400/60 ring-offset-1 ring-offset-forge-bg",
};

const STATUS_INDICATOR: Record<string, { icon: string; cls: string }> = {
  running: { icon: "⟳", cls: "text-amber-400 animate-spin" },
  success: { icon: "✓", cls: "text-emerald-400" },
  failed:  { icon: "✕", cls: "text-red-400" },
};

function PipelineNode({ data, selected }: NodeProps<PipelineNodeData>) {
  const style = TYPE_STYLES[data.stepType] ?? TYPE_STYLES.extract;
  const ringClass = data.liveStatus ? STATUS_RING[data.liveStatus] ?? "" : "";
  const indicator = data.liveStatus ? STATUS_INDICATOR[data.liveStatus] : null;

  return (
    <motion.div
      initial={{ scale: 0.7, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 350, damping: 25 }}
      className={clsx(
        "px-3.5 py-2.5 rounded-xl border backdrop-blur-sm min-w-[150px] shadow-lg",
        style.bg,
        style.border,
        ringClass,
        selected && "outline outline-2 outline-white/30"
      )}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-forge-border !border-slate-600 !w-2 !h-2"
      />

      {/* Type badge */}
      <div className="flex items-center justify-between gap-2 mb-1.5">
        <span className={clsx("text-[9px] px-1.5 py-0.5 rounded font-semibold uppercase tracking-wider", style.badge)}>
          {data.stepType}
        </span>
        {indicator && (
          <span className={clsx("text-sm font-bold leading-none", indicator.cls)}>
            {indicator.icon}
          </span>
        )}
      </div>

      {/* Operation label */}
      <p className="text-xs font-semibold text-white truncate">{data.label}</p>

      {/* Description */}
      <p className="text-[10px] text-white/50 truncate mt-0.5">{data.description}</p>

      {/* Status bar at bottom */}
      {data.liveStatus && data.liveStatus !== "pending" && (
        <div className={clsx(
          "mt-2 h-0.5 rounded-full",
          data.liveStatus === "running"  ? "bg-amber-400 animate-pulse" :
          data.liveStatus === "success"  ? "bg-emerald-400" :
          data.liveStatus === "failed"   ? "bg-red-400" : "bg-slate-700"
        )} />
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-forge-border !border-slate-600 !w-2 !h-2"
      />
    </motion.div>
  );
}

export default memo(PipelineNode);
