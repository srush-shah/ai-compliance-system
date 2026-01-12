"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
  "http://localhost:8000";

type PolicyRule = {
  id: number;
  name: string;
  description?: string | null;
  severity: string;
  category: string;
  pattern_type: string;
  pattern?: string | null;
  scope?: unknown;
  remediation?: string | null;
  version: string;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

export default function PolicyRulesPage() {
  const [rules, setRules] = useState<PolicyRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState({
    name: "",
    description: "",
    severity: "medium",
    category: "general",
    pattern_type: "keyword",
    pattern: "",
    remediation: "",
  });

  const loadRules = async () => {
    try {
      const data = await apiFetch<PolicyRule[]>("/policy-rules");
      setRules(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadRules();
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);

    try {
      await fetch(`${API_BASE}/policy-rules`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ...form,
          is_active: true,
          scope: ["body"],
        }),
      });
      setForm({
        name: "",
        description: "",
        severity: "medium",
        category: "general",
        pattern_type: "keyword",
        pattern: "",
        remediation: "",
      });
      await loadRules();
    } catch (err) {
      setError(String(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Policy rules</h1>
          <p className="text-sm text-gray-600">
            Create structured compliance rules with version tracking.
          </p>
        </div>
      </div>

      <form
        onSubmit={handleSubmit}
        className="rounded border bg-white p-4 space-y-4"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm">
            <span className="font-medium">Rule name</span>
            <input
              type="text"
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.name}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, name: event.target.value }))
              }
              required
            />
          </label>
          <label className="text-sm">
            <span className="font-medium">Severity</span>
            <select
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.severity}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, severity: event.target.value }))
              }
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="font-medium">Category</span>
            <input
              type="text"
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.category}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, category: event.target.value }))
              }
            />
          </label>
          <label className="text-sm">
            <span className="font-medium">Pattern type</span>
            <select
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.pattern_type}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, pattern_type: event.target.value }))
              }
            >
              <option value="keyword">Keyword</option>
              <option value="regex">Regex</option>
              <option value="semantic">Semantic</option>
            </select>
          </label>
          <label className="text-sm">
            <span className="font-medium">Pattern</span>
            <input
              type="text"
              className="mt-1 w-full rounded border px-3 py-2"
              value={form.pattern}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, pattern: event.target.value }))
              }
              placeholder="Keyword, regex, or intent"
            />
          </label>
        </div>
        <label className="text-sm block">
          <span className="font-medium">Description</span>
          <textarea
            className="mt-1 w-full rounded border px-3 py-2"
            value={form.description}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, description: event.target.value }))
            }
          />
        </label>
        <label className="text-sm block">
          <span className="font-medium">Remediation guidance</span>
          <textarea
            className="mt-1 w-full rounded border px-3 py-2"
            value={form.remediation}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, remediation: event.target.value }))
            }
          />
        </label>
        <button
          type="submit"
          className="inline-flex items-center rounded border border-blue-600 bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Add rule
        </button>
      </form>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Active rules</h2>
          {loading && <span className="text-xs text-gray-500">Loading...</span>}
        </div>
        {error && (
          <div className="rounded border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {rules.length === 0 && !loading && (
          <div className="text-sm text-gray-500">No rules available.</div>
        )}
        <div className="grid gap-4 lg:grid-cols-2">
          {rules.map((rule) => (
            <div key={rule.id} className="rounded border bg-white p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">{rule.name}</div>
                  <div className="text-xs text-gray-500">
                    v{rule.version.replace("v", "")} · {rule.category} · {rule.pattern_type}
                  </div>
                </div>
                <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-700">
                  {rule.severity}
                </span>
              </div>
              {rule.pattern && (
                <p className="mt-2 text-xs text-gray-500">Pattern: {rule.pattern}</p>
              )}
              {rule.description && (
                <p className="mt-2 text-sm text-gray-600">{rule.description}</p>
              )}
              {rule.remediation && (
                <p className="mt-2 text-xs text-gray-500">
                  Remediation: {rule.remediation}
                </p>
              )}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
