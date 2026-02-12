import { apiFetch } from "@/lib/api";
import { formatIsoDate } from "@/lib/formatters";

type Violation = {
  id: number;
  rule: string;
  severity: string;
  details: string | object;
  created_at: string;
};
const SEVERITY_OPTIONS = ["all", "low", "medium", "high", "critical"] as const;

export default async function ViolationsPage({
  searchParams,
}: {
  searchParams?: Promise<{ severity?: string; query?: string }>;
}) {
  const resolvedParams = await searchParams;
  const currentSeverity = resolvedParams?.severity ?? "all";
  const currentQuery = resolvedParams?.query ?? "";
  const params = new URLSearchParams();
  if (currentSeverity && currentSeverity !== "all") {
    params.set("severity", currentSeverity);
  }
  if (currentQuery) {
    params.set("query", currentQuery);
  }
  const querySuffix = params.toString() ? `?${params.toString()}` : "";
  const violations = await apiFetch<Violation[]>(
    `/dashboard/violations${querySuffix}`,
  );
  const severityCounts = SEVERITY_OPTIONS.reduce(
    (acc, severity) => {
      if (severity !== "all") {
        acc[severity] = violations.filter(
          (violation) => violation.severity === severity,
        ).length;
      }
      return acc;
    },
    {} as Record<Exclude<(typeof SEVERITY_OPTIONS)[number], "all">, number>,
  );
  const maxSeverityCount = Math.max(
    1,
    ...Object.values(severityCounts),
  );
  const latestViolation = violations[0];

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h1 className="text-2xl font-semibold">Violations</h1>
          <p className="text-sm text-gray-600">
            Filter by severity, search rule names, and review distribution.
          </p>
        </div>
        <a
          href="/dashboard/violations"
          className="text-sm text-blue-600 underline"
        >
          Clear filters
        </a>
      </div>

      <form className="mb-6 grid gap-3 rounded border bg-white p-4 md:grid-cols-3">
        <div className="md:col-span-2">
          <label className="text-xs font-semibold text-gray-500">Search</label>
          <input
            type="search"
            name="query"
            defaultValue={currentQuery}
            placeholder="Search violations by rule or details"
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="text-xs font-semibold text-gray-500">Severity</label>
          <select
            name="severity"
            defaultValue={currentSeverity}
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          >
            {SEVERITY_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {option === "all"
                  ? "All severities"
                  : option.charAt(0).toUpperCase() + option.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div className="md:col-span-3 flex flex-wrap gap-2">
          {SEVERITY_OPTIONS.filter((option) => option !== "all").map((option) => (
            <span
              key={option}
              className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-semibold text-gray-600"
            >
              {option.toUpperCase()}
            </span>
          ))}
        </div>
        <div className="md:col-span-3">
          <button
            type="submit"
            className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
          >
            Apply filters
          </button>
        </div>
      </form>

      <div className="grid gap-4 md:grid-cols-3 mb-6">
        <div className="rounded border bg-white p-4">
          <div className="text-xs font-semibold text-gray-500">
            Total violations
          </div>
          <div className="text-2xl font-semibold">{violations.length}</div>
        </div>
        <div className="rounded border bg-white p-4">
          <div className="text-xs font-semibold text-gray-500">
            High/Critical
          </div>
          <div className="text-2xl font-semibold">
            {(severityCounts.high ?? 0) + (severityCounts.critical ?? 0)}
          </div>
        </div>
        <div className="rounded border bg-white p-4">
          <div className="text-xs font-semibold text-gray-500">
            Latest detection
          </div>
          <div className="text-sm font-medium">
            {latestViolation?.created_at
              ? formatIsoDate(latestViolation.created_at)
              : "No data"}
          </div>
        </div>
      </div>

      <div className="rounded border bg-white p-4 mb-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">
          Severity distribution
        </h2>
        <div className="space-y-2">
          {Object.entries(severityCounts).map(([severity, count]) => (
            <div key={severity} className="flex items-center gap-3">
              <span className="w-20 text-xs font-medium uppercase text-gray-500">
                {severity}
              </span>
              <div className="h-2 flex-1 rounded-full bg-gray-100">
                <div
                  className="h-2 rounded-full bg-blue-500"
                  style={{ width: `${(count / maxSeverityCount) * 100}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-gray-600">
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>

      {violations.length === 0 && (
        <div className="text-gray-500">No violations detected.</div>
      )}

      <div className="space-y-3">
        {violations.map((v) => (
          <div key={v.id} className="border rounded p-3">
            <div className="font-medium">{v.rule}</div>
            <div className="text-sm text-gray-600">
              Severity: <span className="font-mono">{v.severity}</span> ·{" "}
              {formatIsoDate(v.created_at)}
            </div>
            <div className="text-sm text-gray-600">
              {typeof v.details === "string"
                ? v.details
                : JSON.stringify(v.details, null, 2)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
