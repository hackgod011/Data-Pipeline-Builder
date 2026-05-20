import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { ArrowLeft, Play, Loader2 } from "lucide-react";
import { sourcesApi, pipelinesApi, executionsApi } from "../api/client";
import { usePipelineStore } from "../stores/pipelineStore";
import NLInputPanel from "../components/NLInputPanel";
import CodeViewer from "../components/CodeViewer";
import DAGCanvas from "../components/DAGCanvas";

function extractErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (err as { response?: { data?: { detail?: string } } }).response;
    if (res?.data?.detail) return res.data.detail;
  }
  return fallback;
}

export default function PipelineBuilder() {
  const [searchParams] = useSearchParams();
  const initialSourceIds = searchParams.get("sources")?.split(",").filter(Boolean) ?? [];
  const [selectedSourceIds, setSelectedSourceIds] = useState<string[]>(initialSourceIds);
  const [clarifyingQuestions, setClarifyingQuestions] = useState<string[]>([]);

  const navigate = useNavigate();

  const {
    plan,
    generatedCode,
    codeMode,
    liveNodeStatus,
    setPlan,
    setGeneratedCode,
    setCodeMode,
    setSelectedNodeId,
    resetExecution,
  } = usePipelineStore();

  const { data: sources = [] } = useQuery({
    queryKey: ["sources"],
    queryFn: () => sourcesApi.list().then((r) => r.data),
  });

  const generate = useMutation({
    mutationFn: (prompt: string) =>
      pipelinesApi
        .generate({ nl_prompt: prompt, source_ids: selectedSourceIds, code_mode: codeMode })
        .then((r) => r.data),
    onSuccess: (data) => {
      setClarifyingQuestions(data.clarifying_questions ?? []);
      if (data.plan) {
        setPlan(data.plan);
        setGeneratedCode(data.generated_code ?? "");
        toast.success("Pipeline generated");
      }
    },
    onError: (err) => {
      toast.error(extractErrorMessage(err, "Failed to generate pipeline. Try again."));
    },
  });

  const switchMode = useMutation({
    mutationFn: (newMode: "pandas" | "sql") => {
      if (!plan) throw new Error("No pipeline loaded");
      return pipelinesApi.update(plan.pipeline_id, { plan, code_mode: newMode }).then((r) => r.data);
    },
    onSuccess: (data, newMode) => {
      setCodeMode(newMode);
      setGeneratedCode(data.generated_code ?? "");
    },
  });

  const runPipeline = useMutation({
    mutationFn: () => executionsApi.execute(plan!.pipeline_id).then((r) => r.data),
    onSuccess: (data) => {
      resetExecution();
      toast.success("Execution started");
      navigate(`/executions/${data.execution_id}`);
    },
    onError: (err) => {
      toast.error(extractErrorMessage(err, "Failed to start execution."));
    },
  });

  const toggleSource = (id: string) =>
    setSelectedSourceIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );

  function handleModeChange(newMode: "pandas" | "sql") {
    if (newMode === codeMode) return;
    if (plan) switchMode.mutate(newMode);
    else setCodeMode(newMode);
  }

  return (
    <div className="h-screen bg-black flex flex-col overflow-hidden">
      {/* Header */}
      <header className="h-14 flex items-center justify-between px-5 shrink-0" style={{ background: "rgba(0,0,0,0.85)", backdropFilter: "blur(20px)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-1.5 text-sm text-white/40 hover:text-white transition-colors"
          >
            <ArrowLeft size={14} strokeWidth={2} />
            Dashboard
          </button>
          <span className="text-white/15">·</span>
          <h1 className="text-sm font-semibold text-white/80">Pipeline Builder</h1>
          <AnimatePresence>
            {switchMode.isPending && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-xs text-slate-500"
              >
                Switching mode…
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        <div className="flex items-center gap-2">
          {plan && (
            <a
              href={pipelinesApi.exportUrl(plan.pipeline_id)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-forge-border rounded-lg text-slate-400 hover:text-white hover:border-forge-border-hover transition-colors"
            >
              <ArrowLeft size={11} strokeWidth={2} style={{ transform: "rotate(-90deg)" }} />
              Export .py
            </a>
          )}
          <motion.button
            onClick={() => runPipeline.mutate()}
            disabled={!plan || runPipeline.isPending}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="px-4 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 disabled:opacity-40 transition-colors flex items-center gap-2"
          >
            {runPipeline.isPending ? (
              <><Loader2 size={13} className="animate-spin" /> Starting…</>
            ) : (
              <><Play size={13} fill="white" strokeWidth={0} /> Run</>
            )}
          </motion.button>
        </div>
      </header>

      {/* 3-column layout */}
      <div className="flex-1 grid grid-cols-[280px_1fr_320px] overflow-hidden">
        <NLInputPanel
          sources={sources}
          selectedSourceIds={selectedSourceIds}
          onToggleSource={toggleSource}
          onGenerate={(prompt) => generate.mutate(prompt)}
          isGenerating={generate.isPending}
          clarifyingQuestions={clarifyingQuestions}
          generateError={generate.isError ? extractErrorMessage(generate.error, "Generation failed") : null}
        />

        <DAGCanvas
          plan={plan}
          liveStatus={liveNodeStatus}
          onNodeClick={(stepId) => setSelectedNodeId(stepId)}
        />

        <CodeViewer
          code={generatedCode}
          mode={codeMode}
          onModeChange={handleModeChange}
        />
      </div>
    </div>
  );
}
