import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { formatIsoDate } from "@/lib/formatters";
import RecentRuns from "./recent-runs";

type Report = {
  id: number;
  summary: string;
  risk_score: number;
  created_at: string;
};

type Violation = {
  id: number;
  rule: string;
  severity: string;
  created_at: string;
};

export default async function DashboardHomePage() {
  const [reports, violations] = await Promise.all([
    apiFetch<Report[]>("/dashboard/reports?limit=5"),
    apiFetch<Violation[]>("/dashboard/violations?limit=5"),
  ]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm text-gray-600">
            Runs fall back to manual agents when Google ADK is unavailable.
          </p>
        </div>
        <Link
          href="/dashboard/run_workflow"
          className="inline-flex items-center justify-center rounded border px-4 py-2 text-sm font-medium"
        >
          Trigger run by Raw ID
        </Link>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <section className="rounded border p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent runs</h2>
            <Link href="/dashboard/runs" className="text-sm text-blue-600">
              View all
            </Link>
          </div>
          <RecentRuns />
        </section>

        <section className="rounded border p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent reports</h2>
            <Link href="/dashboard/reports" className="text-sm text-blue-600">
              View all
            </Link>
          </div>
          <div className="space-y-3 text-sm">
            {reports.length === 0 && (
              <div className="text-gray-500">No reports yet.</div>
            )}
            {reports.map((report) => (
              <div
                key={report.id}
                className="rounded border border-gray-100 bg-gray-50 p-3"
              >
                <div className="font-medium">
                  {report.summary || `Report #${report.id}`}
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  Risk score {report.risk_score} ·{" "}
                  {formatIsoDate(report.created_at)}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded border p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Recent violations</h2>
            <Link href="/dashboard/violations" className="text-sm text-blue-600">
              View all
            </Link>
          </div>
          <div className="space-y-3 text-sm">
            {violations.length === 0 && (
              <div className="text-gray-500">No violations yet.</div>
            )}
            {violations.map((violation) => (
              <div
                key={violation.id}
                className="rounded border border-gray-100 bg-gray-50 p-3"
              >
                <div className="font-medium">{violation.rule}</div>
                <div className="mt-1 text-xs text-gray-500">
                  Severity {violation.severity} ·{" "}
                  {formatIsoDate(violation.created_at)}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
