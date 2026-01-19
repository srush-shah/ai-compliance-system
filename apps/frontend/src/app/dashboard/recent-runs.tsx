"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import StatusBadge from "@/components/status-badge";
import { apiFetch } from "@/lib/api";
import { failureReason, formatDuration, formatIsoDate } from "@/lib/formatters";

type Run = {
  id: number;
  raw_id: number;
  status: string;
  error?: string | null;
  error_code?: string | null;
  created_at: string;
  duration_seconds?: number | null;
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

export default function RecentRuns() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  const loadRuns = async () => {
    try {
      const data = await apiFetch<Run[]>("/dashboard/runs?limit=10");
      setRuns(Array.isArray(data) ? data : []);
    } catch {
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRuns();
    const interval = setInterval(loadRuns, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="text-sm text-gray-500">Loading runs...</div>;
  }

  if (runs.length === 0) {
    return <div className="text-sm text-gray-500">No runs yet.</div>;
  }

  return (
    <div className="space-y-3 text-sm">
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
  );
}
