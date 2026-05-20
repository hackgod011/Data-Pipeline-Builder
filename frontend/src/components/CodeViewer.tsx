import Editor from "@monaco-editor/react";

interface Props {
  code: string;
  mode: "pandas" | "sql";
  onModeChange: (mode: "pandas" | "sql") => void;
}

export default function CodeViewer({ code, mode, onModeChange }: Props) {
  return (
    <div className="flex flex-col h-full border-l border-forge-border bg-[#0D1117]">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-forge-border shrink-0">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Generated Code</p>
        <div className="flex gap-0.5 bg-forge-border rounded-lg p-0.5">
          {(["pandas", "sql"] as const).map((m) => (
            <button
              key={m}
              onClick={() => onModeChange(m)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                mode === m
                  ? "bg-indigo-600 text-white"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              {m === "pandas" ? "Python" : "SQL"}
            </button>
          ))}
        </div>
      </div>
      {code ? (
        <Editor
          height="100%"
          language={mode === "pandas" ? "python" : "sql"}
          value={code}
          theme="vs-dark"
          options={{
            readOnly: true,
            minimap: { enabled: false },
            fontSize: 12,
            lineNumbers: "on",
            scrollBeyondLastLine: false,
            padding: { top: 12 },
          }}
        />
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center gap-2">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3M3 16v3a2 2 0 002 2h3m8 0h3a2 2 0 002-2v-3" stroke="#3A4563" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <p className="text-xs text-slate-600 text-center">
            Generate a pipeline<br />to see the code here.
          </p>
        </div>
      )}
    </div>
  );
}
