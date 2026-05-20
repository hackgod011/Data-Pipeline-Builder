import { useCallback, useEffect, useRef, useState } from "react";

export interface LogLine {
  type: string;
  timestamp: string;
  step_id?: string;
  message: string;
  status?: string;
  rows_in?: number;
  rows_out?: number;
}

const WS_BASE = (import.meta.env.VITE_WS_BASE_URL as string | undefined) ?? "ws://localhost:8000";
const MAX_RETRIES = 5;

export function useWebSocket(executionId: string | null) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [finalStatus, setFinalStatus] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const finalStatusRef = useRef<string | null>(null);

  const connect = useCallback(() => {
    if (!executionId) return;
    const ws = new WebSocket(`${WS_BASE}/ws/execution/${executionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setIsReconnecting(false);
      retriesRef.current = 0;
    };

    ws.onmessage = (event) => {
      const msg: LogLine = JSON.parse(event.data as string);
      setLogs((prev) => [...prev.slice(-999), msg]);
      if (msg.type === "status" && (msg.status === "success" || msg.status === "failed")) {
        finalStatusRef.current = msg.status;
        setFinalStatus(msg.status);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      if (finalStatusRef.current || retriesRef.current >= MAX_RETRIES) return;
      retriesRef.current += 1;
      const delay = Math.min(1000 * 2 ** retriesRef.current, 30_000);
      setIsReconnecting(true);
      setTimeout(connect, delay);
    };

    ws.onerror = () => ws.close();
  }, [executionId]);

  useEffect(() => {
    if (!executionId) return;
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [executionId, connect]);

  return { logs, isConnected, isReconnecting, finalStatus };
}
