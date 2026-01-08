import Link from "next/link";
import StatusBadge from "@/components/status-badge";
import { apiFetch } from "@/lib/api";
import { failureReason, formatDuration, formatIsoDate } from "@/lib/formatters";

type Run = {
  id: number;
  raw_id: number;
  status: string;
  error?: string | null;
  error_code?: string | null;
  processed_id?: number | null;
  report_id?: number | null;
  created_at: string;
  updated_at?: string | null;
  completed_at?: string | null;
  duration_seconds?: number | null;
};

type RunStep = {
  id: number;
  step: string;
  status: string;
  data?: unknown;
  error?: string | null;
  error_code?: string | null;
  created_at?: string | null;
  finished_at?: string | null;
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

const stepStatusTone = (status: string) => {
  switch (status) {
    case "started":
      return "blue";
    case "success":
      return "green";
    case "failed":
      return "red";
    case "skipped":
      return "gray";
    default:
      return "gray";
  }
};

const hasManualFallback = (steps: RunStep[]) => {
  const fallbackBySource = steps.some((step) => {
    if (!step.data || typeof step.data !== "object") {
      return false;
    }
    const source = (step.data as { source?: string }).source;
    return source === "manual_fallback" || source === "manual_agents";
  });

  const googleFailedIndex = steps.findIndex(
    (step) => step.step === "google_adk" && step.status === "failed",
  );
  const fallbackAfterFailure =
    googleFailedIndex >= 0 &&
    steps.slice(googleFailedIndex + 1).some((step) => step.step === "fallback");

  return fallbackBySource || fallbackAfterFailure;
};

export default async function RunDetailsPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  const numericRunId = Number(runId);

  if (!runId || Number.isNaN(numericRunId)) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Run details unavailable</h1>
        <p className="text-sm text-gray-600">
          The run ID is missing or invalid. Return to the runs list to select a
          valid run.
        </p>
        <Link
          href="/dashboard/runs"
          className="inline-flex items-center rounded border px-4 py-2 text-sm font-medium text-gray-700"
        >
          Back to Runs
        </Link>
      </div>
    );
  }

  const [run, steps] = await Promise.all([
    apiFetch<Run>(`/dashboard/runs/${numericRunId}`),
    apiFetch<RunStep[]>(`/dashboard/runs/${numericRunId}/steps`),
  ]);

  const failure = failureReason({
    error: run.error ?? undefined,
    errorCode: run.error_code ?? undefined,
  });
  const fallbackUsed = Array.isArray(steps) && hasManualFallback(steps);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Run #{run.id}</h1>
          <p className="text-sm text-gray-600">Raw ID {run.raw_id}</p>
        </div>
        <StatusBadge label={run.status} tone={runStatusTone(run.status)} />
      </div>

      <section className="rounded border p-4 space-y-2">
        <div className="flex flex-wrap gap-2 text-sm text-gray-600">
          <span>Created: {formatIsoDate(run.created_at)}</span>
          <span>Updated: {formatIsoDate(run.updated_at)}</span>
          <span>Completed: {formatIsoDate(run.completed_at)}</span>
          <span>Duration: {formatDuration(run.duration_seconds ?? undefined)}</span>
        </div>
        <div className="grid gap-2 text-sm md:grid-cols-2">
          <div>
            <span className="text-gray-500">Processed ID</span>
            <div className="font-medium">{run.processed_id ?? "N/A"}</div>
          </div>
          <div>
            <span className="text-gray-500">Report ID</span>
            <div className="font-medium">{run.report_id ?? "N/A"}</div>
          </div>
          <div>
            <span className="text-gray-500">Error code</span>
            <div className="font-medium">{run.error_code ?? "None"}</div>
          </div>
          <div>
            <span className="text-gray-500">Failure reason</span>
            <div className="font-medium">{failure ?? "None"}</div>
          </div>
        </div>
        {fallbackUsed && (
          <div className="inline-flex items-center rounded-full border border-yellow-200 bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-700">
            Fallback used: Manual agents
          </div>
        )}
      </section>

      <section className="rounded border p-4">
        <h2 className="text-lg font-semibold mb-3">Steps timeline</h2>
        {steps.length === 0 && (
          <div className="text-sm text-gray-500">No steps recorded.</div>
        )}
        <ol className="space-y-3">
          {steps.map((step) => {
            const stepFailure = failureReason({
              error: step.error ?? undefined,
              errorCode: step.error_code ?? undefined,
            });
            return (
              <li key={step.id} className="rounded border border-gray-100 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-medium">{step.step}</div>
                  <StatusBadge
                    label={step.status}
                    tone={stepStatusTone(step.status)}
                  />
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  Created: {formatIsoDate(step.created_at)} · Finished:{" "}
                  {formatIsoDate(step.finished_at)} · Duration:{" "}
                  {formatDuration(step.duration_seconds ?? undefined)}
                </div>
                {step.status === "failed" && stepFailure && (
                  <div className="mt-2 text-xs text-red-600">
                    Failure reason: {stepFailure}
                  </div>
                )}
                <div className="mt-3 space-y-2 text-xs text-gray-600">
                  {step.data !== undefined && (
                    <details className="rounded border border-gray-200 bg-white p-2">
                      <summary className="cursor-pointer font-medium">
                        Step payload
                      </summary>
                      <pre className="mt-2 whitespace-pre-wrap">
                        {JSON.stringify(step.data, null, 2)}
                      </pre>
                    </details>
                  )}
                  {step.error && (
                    <details className="rounded border border-gray-200 bg-white p-2">
                      <summary className="cursor-pointer font-medium">
                        Error details
                      </summary>
                      <pre className="mt-2 whitespace-pre-wrap">
                        {JSON.stringify(step.error, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      </section>
    </div>
  );
}
