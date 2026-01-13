import { apiFetch } from "@/lib/api";
import { formatIsoDate } from "@/lib/formatters";

type Report = {
  id: number;
  summary: string;
  risk_score: number;
  created_at: string;
};

export default async function ReportsPage() {
  const reports = await apiFetch<Report[]>("/dashboard/reports");
  const apiBase =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8000";

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Reports</h1>

      {reports.length === 0 && (
        <div className="text-gray-500">No reports generated yet.</div>
      )}

      <div className="space-y-4">
        {reports.map((r) => (
          <div key={r.id} className="border rounded p-4">
            <div className="font-medium">
              {r.summary || `Report #${r.id}`}
            </div>
            <div className="text-sm text-gray-500">
              Risk: {r.risk_score} · {formatIsoDate(r.created_at)}
            </div>
            <div className="mt-3 flex flex-wrap gap-3 text-sm">
              <a
                href={`${apiBase}/reports/${r.id}.json`}
                className="text-blue-600 underline"
              >
                Export JSON
              </a>
              <a
                href={`${apiBase}/reports/${r.id}/violations.csv`}
                className="text-blue-600 underline"
              >
                Export CSV
              </a>
              <a
                href={`${apiBase}/reports/${r.id}.pdf`}
                className="text-blue-600 underline"
              >
                Export PDF
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
