import { apiFetch } from "@/lib/api";

type ADKRunStep = {
  step: string;
  status: string;
  data?: unknown;
  error?: string;
};

type ADKRun = {
  id: number;
  raw_id: number;
  status: string;
  processed_id?: number;
  report_id?: number;
  created_at: string;
  steps: ADKRunStep[];
};

export default async function ADKRunsPage() {
  const runs = await apiFetch<ADKRun[]>("/compliance/runs?limit=20");

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">ADK Runs</h1>

      {runs.length === 0 && <div className="text-gray-500">No runs found.</div>}

      <div className="space-y-4">
        {runs.map((run) => (
          <div key={run.id} className="border rounded p-4">
            <div className="font-medium">
              Run #{run.id} (Raw ID: {run.raw_id}) - {run.status}
            </div>
            <div className="text-sm text-gray-500">
              Created: {new Date(run.created_at).toLocaleString()}
            </div>
            <div className="mt-2 space-y-1 text-sm">
              {run.steps?.map((step, i) => (
                <div key={i}>
                  {step.step}:{" "}
                  <span
                    className={
                      step.status === "success"
                        ? "text-green-600"
                        : step.status === "failed"
                        ? "text-red-600"
                        : "text-gray-600"
                    }
                  >
                    {step.status}
                  </span>
                  {step.error && (
                    <div className="text-red-600 font-mono">{step.error}</div>
                  )}
                  {step.data != null && (
                    <pre className="text-gray-700 font-mono text-xs">
                      {JSON.stringify(step.data, null, 2)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
