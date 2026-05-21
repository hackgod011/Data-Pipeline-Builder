import { useState } from "react";
import { Link } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { type DataSource } from "../api/client";
import TemplatesModal from "./TemplatesModal";

interface Props {
  sources: DataSource[];
  selectedSourceIds: string[];
  onToggleSource: (id: string) => void;
  onGenerate: (prompt: string) => void;
  isGenerating: boolean;
  clarifyingQuestions: string[];
  generateError?: string | null;
}

export default function NLInputPanel({
  sources,
  selectedSourceIds,
  onToggleSource,
  onGenerate,
  isGenerating,
  clarifyingQuestions,
  generateError,
}: Props) {
  const [prompt, setPrompt] = useState("");
  const [showTemplates, setShowTemplates] = useState(false);

  const readySources = sources.filter((s) => s.processing_status === "ready");

  return (
    <div className="flex flex-col h-full border-r border-forge-border bg-forge-surface overflow-hidden">
      {showTemplates && (
        <TemplatesModal
          onSelect={(p) => { setPrompt(p); setShowTemplates(false); }}
          onClose={() => setShowTemplates(false)}
        />
      )}
      {/* Sources section */}
      <div className="p-4 border-b border-forge-border">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Data Sources</p>
          <Link
            to="/dashboard"
            className="text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            + Upload more
          </Link>
        </div>

        {readySources.length === 0 ? (
          <div className="py-3 text-center">
            <p className="text-xs text-slate-600">No ready sources.</p>
            <Link to="/dashboard" className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
              Upload files →
            </Link>
          </div>
        ) : (
          <div className="space-y-1">
            {readySources.map((src) => (
              <label
                key={src.id}
                className={`flex items-center gap-2.5 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
                  selectedSourceIds.includes(src.id)
                    ? "bg-indigo-900/30 border border-indigo-700/50"
                    : "hover:bg-forge-surface2 border border-transparent"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedSourceIds.includes(src.id)}
                  onChange={() => onToggleSource(src.id)}
                  className="rounded border-forge-border bg-forge-bg accent-indigo-500"
                />
                <span className="text-xs text-slate-300 truncate">{src.filename}</span>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Prompt section */}
      <div className="flex flex-col flex-1 p-4 gap-3 overflow-hidden">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Describe your pipeline</p>
          <button
            onClick={() => setShowTemplates(true)}
            className="text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            Use Template
          </button>
        </div>
        <textarea
          className="flex-1 min-h-0 p-3 text-sm bg-forge-bg border border-forge-border rounded-lg resize-none text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
          placeholder="e.g. Join sales with customers on customer_id, filter North region, sum revenue by product category"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={isGenerating}
        />

        <motion.button
          onClick={() => prompt.trim() && onGenerate(prompt.trim())}
          disabled={isGenerating || !prompt.trim() || selectedSourceIds.length === 0}
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          className="px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium
                     hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors
                     flex items-center justify-center gap-2"
        >
          {isGenerating ? (
            <>
              <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Generating…
            </>
          ) : (
            <>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M13 10V3L4 14h7v7l9-11h-7z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Generate Pipeline
            </>
          )}
        </motion.button>

        {selectedSourceIds.length === 0 && prompt.trim() && (
          <p className="text-xs text-slate-600 text-center">Select at least one source above</p>
        )}
      </div>

      {/* Feedback messages */}
      <AnimatePresence>
        {generateError && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="mx-4 mb-4 p-3 bg-red-900/20 border border-red-700/50 rounded-lg"
          >
            <p className="text-xs font-semibold text-red-400 mb-1">Generation failed</p>
            <p className="text-xs text-red-300">{generateError}</p>
          </motion.div>
        )}
        {clarifyingQuestions.length > 0 && !generateError && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="mx-4 mb-4 p-3 bg-amber-900/20 border border-amber-700/50 rounded-lg"
          >
            <p className="text-xs font-semibold text-amber-400 mb-1.5">Needs clarification</p>
            {clarifyingQuestions.map((q, i) => (
              <p key={i} className="text-xs text-amber-300">• {q}</p>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
