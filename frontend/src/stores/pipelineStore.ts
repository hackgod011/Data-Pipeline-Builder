import { create } from "zustand";

export interface PipelineStep {
  step_id: string;
  type: "extract" | "transform" | "load" | "validate";
  operation: string;
  params: Record<string, unknown>;
  output_alias: string;
  description: string;
  depends_on: string[];
}

export interface PipelinePlan {
  pipeline_id: string;
  name: string;
  nl_prompt: string;
  version: number;
  steps: PipelineStep[];
}

interface PipelineStore {
  plan: PipelinePlan | null;
  generatedCode: string;
  codeMode: "pandas" | "sql";
  selectedNodeId: string | null;
  liveNodeStatus: Record<string, "pending" | "running" | "success" | "failed">;
  setPlan: (plan: PipelinePlan) => void;
  setGeneratedCode: (code: string) => void;
  setCodeMode: (mode: "pandas" | "sql") => void;
  setSelectedNodeId: (id: string | null) => void;
  setLiveNodeStatus: (stepId: string, status: "pending" | "running" | "success" | "failed") => void;
  resetExecution: () => void;
}

export const usePipelineStore = create<PipelineStore>((set) => ({
  plan: null,
  generatedCode: "",
  codeMode: "pandas",
  selectedNodeId: null,
  liveNodeStatus: {},
  setPlan: (plan) => set({ plan }),
  setGeneratedCode: (code) => set({ generatedCode: code }),
  setCodeMode: (mode) => set({ codeMode: mode }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  setLiveNodeStatus: (stepId, status) =>
    set((s) => ({ liveNodeStatus: { ...s.liveNodeStatus, [stepId]: status } })),
  resetExecution: () => set({ liveNodeStatus: {} }),
}));
