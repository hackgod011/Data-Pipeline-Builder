interface Props {
  columns: string[];
  rows: Record<string, unknown>[];
  maxRows?: number;
}

export default function DataTable({ columns, rows, maxRows = 100 }: Props) {
  const displayed = rows.slice(0, maxRows);
  return (
    <div className="overflow-auto max-h-96 border rounded-lg">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {displayed.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col} className="px-3 py-2 whitespace-nowrap text-gray-700">
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > maxRows && (
        <p className="px-3 py-2 text-xs text-gray-400">
          Showing {maxRows} of {rows.length} rows
        </p>
      )}
    </div>
  );
}
