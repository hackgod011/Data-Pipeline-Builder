import { motion } from "framer-motion";
import clsx from "clsx";

type Status = "pending" | "processing" | "ready" | "error" | "running" | "success" | "failed";

const STATUS_STYLES: Record<Status, string> = {
  pending:    "bg-slate-800/60 text-slate-400 border-slate-700",
  processing: "bg-amber-900/30 text-amber-400 border-amber-700/50",
  ready:      "bg-emerald-900/30 text-emerald-400 border-emerald-700/50",
  error:      "bg-red-900/30 text-red-400 border-red-700/50",
  running:    "bg-indigo-900/30 text-indigo-300 border-indigo-700/50",
  success:    "bg-emerald-900/30 text-emerald-400 border-emerald-700/50",
  failed:     "bg-red-900/30 text-red-400 border-red-700/50",
};

const STATUS_DOT: Record<Status, string> = {
  pending:    "bg-slate-500",
  processing: "bg-amber-400 animate-pulse",
  ready:      "bg-emerald-400",
  error:      "bg-red-400",
  running:    "bg-indigo-400 animate-pulse",
  success:    "bg-emerald-400",
  failed:     "bg-red-400",
};

const STATUS_LABELS: Record<Status, string> = {
  pending:    "Pending",
  processing: "Processing",
  ready:      "Ready",
  error:      "Error",
  running:    "Running",
  success:    "Success",
  failed:     "Failed",
};

interface Props {
  status: Status;
  className?: string;
}

export default function StatusBadge({ status, className }: Props) {
  return (
    <motion.span
      key={status}
      initial={{ scale: 0.85, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.15 }}
      className={clsx(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border",
        STATUS_STYLES[status] ?? "bg-slate-800/60 text-slate-400 border-slate-700",
        className
      )}
    >
      <span className={clsx("w-1.5 h-1.5 rounded-full shrink-0", STATUS_DOT[status] ?? "bg-slate-500")} />
      {STATUS_LABELS[status] ?? status}
    </motion.span>
  );
}
