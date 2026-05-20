import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import type { LogLine } from "../hooks/useWebSocket";

interface Props {
  logs: LogLine[];
  isConnected: boolean;
  isReconnecting: boolean;
}

const LEVEL_STYLES: Record<string, string> = {
  error:  "text-red-400",
  status: "text-indigo-400",
  log:    "text-slate-300",
};

export default function LogStream({ logs, isConnected, isReconnecting }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs.length]);

  return (
    <div className="flex flex-col h-full bg-[#0D1117] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-forge-border shrink-0">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Execution Logs</p>
        <span className={`text-xs flex items-center gap-1.5 ${
          isReconnecting ? "text-amber-400"
          : isConnected   ? "text-emerald-400"
          : "text-slate-600"
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full inline-block ${
            isReconnecting ? "bg-amber-400 animate-pulse"
            : isConnected   ? "bg-emerald-400"
            : "bg-slate-600"
          }`} />
          {isReconnecting ? "Reconnecting…" : isConnected ? "Live" : "Disconnected"}
        </span>
      </div>

      {/* Log lines */}
      <div className="flex-1 overflow-y-auto p-3 font-mono text-xs">
        {logs.length === 0 && (
          <p className="text-slate-700 italic">Waiting for execution to start…</p>
        )}
        <AnimatePresence initial={false}>
          {logs.map((log, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -4 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.1 }}
              className={`flex gap-3 py-0.5 ${LEVEL_STYLES[log.type] ?? "text-slate-300"}`}
            >
              <span className="text-slate-600 shrink-0 tabular-nums select-none">
                {log.timestamp
                  ? new Date(log.timestamp).toLocaleTimeString()
                  : "--:--:--"}
              </span>
              <span className="break-all">{log.message}</span>
            </motion.div>
          ))}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
