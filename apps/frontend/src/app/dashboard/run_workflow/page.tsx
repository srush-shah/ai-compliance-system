"use client";
import { useState } from "react";

export default function RunWorkflowPage() {
  const [rawId, setRawId] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  async function handleRun(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("Starting run...");

    const res = await fetch(`/compliance/run/${rawId}`, { method: "POST" });
    const data = await res.json();
    setStatus(JSON.stringify(data, null, 2));
  }

  async function handleRetry(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    setStatus("Retrying run...");

    const res = await fetch(`/compliance/retry/${rawId}`, { method: "POST" });
    const data = await res.json();
    setStatus(JSON.stringify(data, null, 2));
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-semibold">Trigger ADK Workflow</h1>
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
