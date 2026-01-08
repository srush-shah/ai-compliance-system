"use client";
import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function RunWorkflowPage() {
  const [rawId, setRawId] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  async function handleRun(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("Starting run...");

    try {
      const data = await apiFetch(`/compliance/run/${rawId}`, {
        method: "POST",
      });
      setStatus(JSON.stringify(data, null, 2));
    } catch (err) {
      setStatus(`Error starting run: ${String(err)}`);
    }
  }

  async function handleRetry(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    setStatus("Retrying run...");

    try {
      const data = await apiFetch(`/compliance/retry/${rawId}`, {
        method: "POST",
      });
      setStatus(JSON.stringify(data, null, 2));
    } catch (err) {
      setStatus(`Error retrying run: ${String(err)}`);
    }
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">Trigger ADK Workflow</h1>
      <p className="text-sm text-gray-600">
        If Google ADK fails or runs out of quota, the system uses manual agents
        and logs a fallback step.
      </p>
      <form onSubmit={handleRun} className="space-x-2">
        <input
          type="number"
          value={rawId}
          onChange={(e) => setRawId(e.target.value)}
          placeholder="Raw ID"
          className="border px-2 py-1"
          required
        />
        <button type="submit" className="border px-4 py-1">Run</button>
        <button onClick={handleRetry} className="border px-4 py-1 ml-2">Retry</button>
      </form>
      {status && (
        <pre className="bg-gray-100 p-2 rounded font-mono text-sm">{status}</pre>
      )}
    </div>
  );
}
