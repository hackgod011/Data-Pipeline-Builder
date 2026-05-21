import { useEffect, useState } from "react";

interface Template {
  id: string;
  name: string;
  category: string;
  description: string;
  nl_prompt: string;
  required_columns: string[];
}

interface Props {
  onSelect: (prompt: string) => void;
  onClose: () => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  Analytics: "bg-blue-900/60 text-blue-300",
  "Data Quality": "bg-green-900/60 text-green-300",
  Transformation: "bg-purple-900/60 text-purple-300",
};

export default function TemplatesModal({ onSelect, onClose }: Props) {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);
  const [filter, setFilter] = useState("All");

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_BASE_URL}/api/v1/templates/`)
      .then((r) => r.json())
      .then((data) => {
        setTemplates(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const categories = ["All", ...Array.from(new Set(templates.map((t) => t.category)))];
  const visible = filter === "All" ? templates : templates.filter((t) => t.category === filter);
  const chosen = templates.find((t) => t.id === selected);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-3xl mx-4 shadow-2xl flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div>
            <h2 className="text-lg font-semibold text-white">Pipeline Templates</h2>
            <p className="text-sm text-gray-400 mt-0.5">Pick a starter — edit the prompt after.</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Category filter */}
        <div className="flex gap-2 px-6 py-3 border-b border-gray-700 overflow-x-auto">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap transition-colors ${
                filter === cat
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Template grid */}
        <div className="flex-1 overflow-y-auto p-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          {loading && (
            <p className="text-gray-500 text-sm col-span-2 text-center py-8">
              Loading templates…
            </p>
          )}
          {!loading &&
            visible.map((t) => (
              <button
                key={t.id}
                onClick={() => setSelected(t.id)}
                className={`text-left p-4 rounded-lg border transition-all ${
                  selected === t.id
                    ? "border-indigo-500 bg-indigo-950"
                    : "border-gray-700 bg-gray-800 hover:border-gray-500"
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <span className="text-white font-medium text-sm">{t.name}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium shrink-0 ${
                      CATEGORY_COLORS[t.category] ?? "bg-gray-700 text-gray-300"
                    }`}
                  >
                    {t.category}
                  </span>
                </div>
                <p className="text-gray-400 text-xs leading-relaxed">{t.description}</p>
                {t.required_columns.length > 0 && (
                  <p className="text-gray-600 text-xs mt-2">
                    Needs: {t.required_columns.join(", ")}
                  </p>
                )}
              </button>
            ))}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-gray-700 flex items-center justify-between gap-4">
          <p className="text-gray-500 text-xs truncate max-w-sm">
            {chosen
              ? chosen.nl_prompt
              : "Select a template to preview its prompt"}
          </p>
          <div className="flex gap-2 shrink-0">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              disabled={!chosen}
              onClick={() => {
                if (chosen) {
                  onSelect(chosen.nl_prompt);
                  onClose();
                }
              }}
              className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Use Template
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
