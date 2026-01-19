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

export default function RunsList() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [loading, setLoading] = useState(true);

  const loadRuns = async () => {
    try {
      const data = await apiFetch<Run[]>("/dashboard/runs?limit=20");
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

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Runs</h1>
        <span className="text-xs text-gray-500">Auto-refreshes every 5s</span>
      </div>

      {loading && <div className="text-gray-500">Loading runs...</div>}

      {!loading && runs.length === 0 && (
        <div className="text-gray-500">No runs found.</div>
      )}

      {runs.length > 0 && (
        <div className="overflow-hidden rounded border">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Run</th>
                <th className="px-4 py-2">Raw ID</th>
                <th className="px-4 py-2">Status</th>
                <th className="px-4 py-2">Created</th>
                <th className="px-4 py-2">Duration</th>
                <th className="px-4 py-2">Notes</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => {
                const reason = failureReason({
                  error: run.error ?? undefined,
                  errorCode: run.error_code ?? undefined,
                });
                return (
                  <tr key={run.id} className="border-t">
                    <td className="px-4 py-3">
                      <Link
                        href={`/dashboard/runs/${run.id}`}
                        className="font-medium text-blue-700"
                      >
                        Run #{run.id}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{run.raw_id}</td>
                    <td className="px-4 py-3">
                      <StatusBadge
                        label={run.status}
                        tone={runStatusTone(run.status)}
                      />
                    </td>
                    <td className="px-4 py-3">
                      {formatIsoDate(run.created_at)}
                    </td>
                    <td className="px-4 py-3">
                      {formatDuration(run.duration_seconds ?? undefined)}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">
                      {run.status === "failed" && reason
                        ? `Failure reason: ${reason}`
                        : "None"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
