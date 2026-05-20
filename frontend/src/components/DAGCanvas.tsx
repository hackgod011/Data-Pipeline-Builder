import { useEffect } from "react";
import { motion } from "framer-motion";
import ReactFlow, {
  type Node,
  type Edge,
  Controls,
  Background,
  BackgroundVariant,
  MiniMap,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";
import PipelineNode, { type PipelineNodeData } from "./PipelineNode";
import type { PipelinePlan } from "../api/client";

const NODE_TYPES = { pipeline: PipelineNode };

const MINIMAP_NODE_COLORS: Record<string, string> = {
  extract:   "#6366F1",
  transform: "#10B981",
  load:      "#F59E0B",
  validate:  "#F43F5E",
};

function planToNodes(
  plan: PipelinePlan,
  liveStatus: Record<string, string>
): Node<PipelineNodeData>[] {
  return plan.steps.map((step, i) => ({
    id: step.step_id,
    type: "pipeline",
    position: {
      x: 220 * (i % 3),
      y: 140 * Math.floor(i / 3) + (i % 2) * 20,
    },
    data: {
      label: step.operation,
      stepType: step.type,
      description: step.description,
      liveStatus: (liveStatus[step.step_id] as PipelineNodeData["liveStatus"]) ?? "pending",
    },
  }));
}

function planToEdges(plan: PipelinePlan): Edge[] {
  const edges: Edge[] = [];
  for (const step of plan.steps) {
    for (const dep of step.depends_on) {
      edges.push({
        id: `${dep}->${step.step_id}`,
        source: dep,
        target: step.step_id,
        animated: false,
        style: { stroke: "#3A4563", strokeWidth: 1.5 },
      });
    }
  }
  return edges;
}

interface Props {
  plan: PipelinePlan | null;
  liveStatus: Record<string, string>;
  onNodeClick?: (stepId: string) => void;
}

export default function DAGCanvas({ plan, liveStatus, onNodeClick }: Props) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!plan) return;
    setNodes(planToNodes(plan, liveStatus));
    setEdges(planToEdges(plan));
  }, [plan, liveStatus, setNodes, setEdges]);

  if (!plan) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-4 bg-forge-bg"
        style={{
          backgroundImage: `radial-gradient(circle, #252E45 1px, transparent 1px)`,
          backgroundSize: "24px 24px",
        }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="text-center"
        >
          <div className="w-14 h-14 mx-auto mb-4 rounded-2xl bg-forge-surface border border-forge-border flex items-center justify-center">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="3" width="7" height="5" rx="1.5" stroke="#3A4563" strokeWidth="1.5"/>
              <rect x="14" y="3" width="7" height="5" rx="1.5" stroke="#3A4563" strokeWidth="1.5"/>
              <rect x="8" y="16" width="8" height="5" rx="1.5" stroke="#3A4563" strokeWidth="1.5"/>
              <path d="M6.5 8v3h11V8" stroke="#3A4563" strokeWidth="1.5" strokeLinecap="round"/>
              <path d="M12 11v5" stroke="#3A4563" strokeWidth="1.5" strokeLinecap="round"/>
            </svg>
          </div>
          <p className="text-sm text-slate-600">Describe a pipeline to see the DAG</p>
          <p className="text-xs text-slate-700 mt-1">Steps will appear as connected nodes</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-forge-bg">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={NODE_TYPES}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={(_, node) => onNodeClick?.(node.id)}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        attributionPosition="bottom-right"
      >
        <Background
          variant={BackgroundVariant.Dots}
          color="#252E45"
          gap={24}
          size={1}
        />
        <Controls
          className="!bg-forge-surface !border-forge-border"
          showInteractive={false}
        />
        <MiniMap
          className="!bg-forge-surface !border-forge-border"
          nodeColor={(n) => MINIMAP_NODE_COLORS[(n.data as PipelineNodeData).stepType] ?? "#6366F1"}
          maskColor="rgba(11,15,26,0.7)"
        />
      </ReactFlow>
    </div>
  );
}
