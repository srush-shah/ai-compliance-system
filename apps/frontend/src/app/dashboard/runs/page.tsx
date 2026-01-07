import { apiFetch } from "@/lib/api";

type ADKRunStep = {
  step: string;
  status: string;
  data?: unknown;
  error?: string;
};

type ADKRunSummary = {
  id: number;
  raw_id: number;
  status: string;
  created_at: string;
};

type ADKRun = ADKRunSummary & {
  steps: ADKRunStep[];
};

export default async function ADKRunsPage() {
  // Fetch recent runs
  const runs = await apiFetch<ADKRunSummary[]>("/dashboard/runs?limit=20");

  // For each run, fetch its steps so the UI always has a defined `steps` array
  const runsWithSteps: ADKRun[] = await Promise.all(
    runs.map(async (run) => {
      try {
        const steps = await apiFetch<ADKRunStep[]>(
          `/dashboard/runs/${run.id}/steps`,
        );
        return { ...run, steps: Array.isArray(steps) ? steps : [] };
      } catch {
        // If fetching steps fails, default to empty array
        return { ...run, steps: [] };
      }
    }),
  );

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">ADK Runs</h1>

      {runsWithSteps.length === 0 && (
        <div className="text-gray-500">No runs found.</div>
      )}

      <div className="space-y-4">
        {runsWithSteps.map((run) => (
          <div key={run.id} className="border rounded p-4">
            <div className="font-medium">
              Run #{run.id} (Raw ID: {run.raw_id}) - {run.status}
            </div>
            <div className="text-sm text-gray-500">
              Created: {new Date(run.created_at).toISOString().replace('T', ' ').slice(0, 19)}
            </div>
            {Array.isArray(run.steps) && run.steps.length > 0 ? (
              <div className="mt-2 space-y-1 text-sm">
                {run.steps.map((step, i) => (
                <div key={i}>
                  {step.step}:{" "}
                  <span
                    className={
                      step.status === "success"
                        ? "text-green-600"
                        : step.status === "failed"
                        ? "text-red-600"
                        : step.status === "started"
                        ? "text-blue-600"
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
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
