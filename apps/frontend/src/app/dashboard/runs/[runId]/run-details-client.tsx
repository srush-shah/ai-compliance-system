"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import StatusBadge from "@/components/status-badge";
import { apiFetch, getAuthToken } from "@/lib/api";
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
  queued_at?: string | null;
  processing_at?: string | null;
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

type RunUpdateMessage = {
  status?: string;
  step?: string | null;
  payload?: {
    run?: Run;
    step?: RunStep;
  };
};

const runStatusTone = (status: string) => {
  switch (status) {
    case "queued":
      return "gray";
    case "processing":
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

const upsertStep = (current: RunStep[], update: RunStep): RunStep[] => {
  const index = current.findIndex((step) => step.id === update.id);
  if (index >= 0) {
    const next = [...current];
    next[index] = { ...current[index], ...update };
    return next;
  }
  return [...current, update].sort((a, b) => a.id - b.id);
};

export default function RunDetailsClient({ runId }: { runId: number }) {
  const [run, setRun] = useState<Run | null>(null);
  const [steps, setSteps] = useState<RunStep[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRun = useCallback(async () => {
    try {
      setError(null);
      const [runData, stepsData] = await Promise.all([
        apiFetch<Run>(`/dashboard/runs/${runId}`),
        apiFetch<RunStep[]>(`/dashboard/runs/${runId}/steps`),
      ]);
      setRun(runData);
      setSteps(stepsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    void fetchRun();
  }, [fetchRun]);

  useEffect(() => {
    let websocket: WebSocket | null = null;
    let pollingTimer: ReturnType<typeof setInterval> | null = null;

    const startPolling = () => {
      if (!pollingTimer) {
        pollingTimer = setInterval(() => {
          void fetchRun();
        }, 5000);
      }
    };

    const stopPolling = () => {
      if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
      }
    };

    if (typeof window === "undefined") {
      return () => undefined;
    }

    const token = getAuthToken();
    if (!token) {
      startPolling();
      return () => {
        stopPolling();
      };
    }

    const apiBase =
      process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
      "http://localhost:8000";
    const wsBase = apiBase.replace(/^http/, "ws");
    const url = new URL(`${wsBase}/ws/runs/${runId}`);
    url.searchParams.set("token", token);

    try {
      websocket = new WebSocket(url.toString());
    } catch (err) {
      startPolling();
      return () => {
        stopPolling();
      };
    }

    websocket.onopen = () => {
      stopPolling();
    };

    websocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as RunUpdateMessage;
        if (message.payload?.run) {
          setRun(message.payload.run);
        }
        if (message.payload?.step) {
          setSteps((current) => upsertStep(current, message.payload!.step!));
        }
      } catch (err) {
        startPolling();
      }
    };

    websocket.onerror = () => {
      startPolling();
    };

    websocket.onclose = () => {
      startPolling();
    };

    return () => {
      stopPolling();
      websocket?.close();
    };
  }, [fetchRun, runId]);

  const failure = useMemo(() => {
    if (!run) {
      return undefined;
    }
    return failureReason({
      error: run.error ?? undefined,
      errorCode: run.error_code ?? undefined,
    });
  }, [run]);

  const fallbackUsed = useMemo(
    () => (Array.isArray(steps) ? hasManualFallback(steps) : false),
    [steps],
  );

  if (loading && !run) {
    return <div className="text-sm text-gray-500">Loading run details...</div>;
  }

  if (!run) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        Unable to load run details. {error}
      </div>
    );
  }

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
          <span>Queued: {formatIsoDate(run.queued_at)}</span>
          <span>Processing: {formatIsoDate(run.processing_at)}</span>
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
