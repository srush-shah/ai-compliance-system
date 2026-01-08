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
          </div>
        ))}
      </div>
    </div>
  );
}
