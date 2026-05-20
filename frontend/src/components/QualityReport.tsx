import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { ProfileResult } from "../api/client";

interface Props {
  profile: ProfileResult;
}

function scoreColor(score: number): string {
  if (score >= 90) return "text-green-600";
  if (score >= 70) return "text-yellow-600";
  if (score >= 50) return "text-orange-500";
  return "text-red-600";
}

function scoreLabel(score: number): string {
  if (score >= 90) return "Excellent";
  if (score >= 70) return "Good";
  if (score >= 50) return "Fair";
  return "Poor";
}

function barColor(nullPct: number): string {
  if (nullPct === 0) return "#22c55e";
  if (nullPct < 10) return "#eab308";
  if (nullPct < 30) return "#f97316";
  return "#ef4444";
}

export default function QualityReport({ profile }: Props) {
  const chartData = profile.columns.map((c) => ({
    name: c.name.length > 12 ? c.name.slice(0, 11) + "…" : c.name,
    fullName: c.name,
    nullPct: c.null_pct,
  }));

  return (
    <div className="p-4 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700 uppercase tracking-wide">
          Data Quality Report
        </h2>
        <div className="text-right">
          <span className={`text-3xl font-bold ${scoreColor(profile.quality_score)}`}>
            {profile.quality_score}
          </span>
          <span className="text-xs text-gray-400 ml-1">/ 100</span>
          <p className={`text-xs font-medium ${scoreColor(profile.quality_score)}`}>
            {scoreLabel(profile.quality_score)}
          </p>
        </div>
      </div>

      {/* Summary row */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-gray-800">
            {profile.row_count.toLocaleString()}
          </p>
          <p className="text-xs text-gray-500">Rows</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xl font-bold text-gray-800">{profile.column_count}</p>
          <p className="text-xs text-gray-500">Columns</p>
        </div>
      </div>

      {/* Null % bar chart */}
      {chartData.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
            Null % by Column
          </p>
          <ResponsiveContainer width="100%" height={Math.max(80, chartData.length * 24)}>
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 0, right: 8, left: 0, bottom: 0 }}
            >
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} unit="%" />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fontSize: 10 }}
                width={70}
              />
              <Tooltip formatter={(v) => [`${v}%`, "Null %"]} />
              <Bar dataKey="nullPct" radius={[0, 3, 3, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={barColor(entry.nullPct)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Column detail table */}
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase mb-2">
          Column Details
        </p>
        <div className="overflow-auto border rounded-lg">
          <table className="min-w-full text-xs">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-2 py-1.5 text-left text-gray-500 font-medium">Column</th>
                <th className="px-2 py-1.5 text-left text-gray-500 font-medium">Type</th>
                <th className="px-2 py-1.5 text-right text-gray-500 font-medium">Null%</th>
                <th className="px-2 py-1.5 text-right text-gray-500 font-medium">Unique%</th>
                <th className="px-2 py-1.5 text-right text-gray-500 font-medium">Mean</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {profile.columns.map((col) => (
                <tr key={col.name} className="hover:bg-gray-50">
                  <td className="px-2 py-1.5 font-medium text-gray-800 max-w-[100px] truncate">
                    {col.name}
                  </td>
                  <td className="px-2 py-1.5 text-gray-500">{col.dtype}</td>
                  <td
                    className={`px-2 py-1.5 text-right font-medium ${
                      col.null_pct > 20 ? "text-red-600" : "text-gray-700"
                    }`}
                  >
                    {col.null_pct}%
                  </td>
                  <td className="px-2 py-1.5 text-right text-gray-600">
                    {col.unique_pct}%
                  </td>
                  <td className="px-2 py-1.5 text-right text-gray-600">
                    {col.mean != null ? col.mean : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
