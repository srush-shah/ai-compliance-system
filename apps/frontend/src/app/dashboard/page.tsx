import Link from "next/link";
import StatusBadge from "@/components/status-badge";
import { apiFetch } from "@/lib/api";
import { failureReason, formatDuration, formatIsoDate } from "@/lib/formatters";

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

type Run = {
  id: number;
  raw_id: number;
  status: string;
  error?: string | null;
  error_code?: string | null;
  report_id?: number | null;
  processed_id?: number | null;
  created_at: string;
  duration_seconds?: number | null;
};

const runStatusTone = (status: string) => {
  switch (status) {
    case "started":
      return "blue";
    case "completed":
      return "green";
    case "failed":
      return "red";
    default:
      return "gray";
  }
};

export default async function DashboardHomePage() {
  const [runs, reports, violations] = await Promise.all([
    apiFetch<Run[]>("/dashboard/runs?limit=10"),
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
          <div className="space-y-3 text-sm">
            {runs.length === 0 && (
              <div className="text-gray-500">No runs yet.</div>
            )}
            {runs.map((run) => {
              const reason = failureReason({
                error: run.error ?? undefined,
                errorCode: run.error_code ?? undefined,
              });
              return (
                <div
                  key={run.id}
                  className="rounded border border-gray-100 bg-gray-50 p-3"
                >
                  <div className="flex items-center justify-between">
                    <Link
                      href={`/dashboard/runs/${run.id}`}
                      className="font-medium text-blue-700"
                    >
                      Run #{run.id}
                    </Link>
                    <StatusBadge
                      label={run.status}
                      tone={runStatusTone(run.status)}
                    />
                  </div>
                  <div className="mt-1 text-xs text-gray-500">
                    Raw ID {run.raw_id} · {formatIsoDate(run.created_at)} ·{" "}
                    {formatDuration(run.duration_seconds ?? undefined)}
                  </div>
                  {run.status === "failed" && reason && (
                    <div className="mt-2 text-xs text-red-600">
                      Failure reason: {reason}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
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
