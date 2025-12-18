import { apiFetch } from "@/lib/api";

type AgentLog = {
  agent: string;
  action: string;
  payload: string;
  created_at: string;
};

export default async function AgentLogsPage() {
  const logs = await apiFetch<AgentLog[]>("/dashboard/agents");

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-4">Agent Logs</h1>

      <div className="space-y-2 text-sm font-mono">
        {logs.map((l, i) => (
          <div key={i} className="border rounded p-2">
            [{new Date(l.created_at).toLocaleTimeString()}] {l.agent} →{" "}
            {l.action}
          </div>
        ))}
      </div>
    </div>
  );
}