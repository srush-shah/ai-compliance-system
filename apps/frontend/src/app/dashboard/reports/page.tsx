import { apiFetch } from "@/lib/api";
import { formatIsoDate } from "@/lib/formatters";

type Report = {
  id: number;
  summary: string;
  risk_score: number;
  risk_tier?: string | null;
  created_at: string;
};

const RISK_TIER_OPTIONS = ["all", "Low", "Medium", "High", "Critical"] as const;

export default async function ReportsPage({
  searchParams,
}: {
  searchParams?: Promise<{ risk_tier?: string; query?: string }>;
}) {
  const resolvedParams = await searchParams;
  const currentRiskTier = resolvedParams?.risk_tier ?? "all";
  const currentQuery = resolvedParams?.query ?? "";
  const params = new URLSearchParams();
  if (currentRiskTier && currentRiskTier !== "all") {
    params.set("risk_tier", currentRiskTier);
  }
  if (currentQuery) {
    params.set("query", currentQuery);
  }
  const querySuffix = params.toString() ? `?${params.toString()}` : "";
  const reports = await apiFetch<Report[]>(`/dashboard/reports${querySuffix}`);
  const apiBase =
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8000";
  const averageScore = reports.length
    ? reports.reduce((acc, report) => acc + (report.risk_score ?? 0), 0) /
      reports.length
    : 0;
  const riskTierCounts = RISK_TIER_OPTIONS.reduce(
    (acc, tier) => {
      if (tier !== "all") {
        acc[tier] = reports.filter(
          (report) => report.risk_tier === tier,
        ).length;
      }
      return acc;
    },
    {} as Record<Exclude<(typeof RISK_TIER_OPTIONS)[number], "all">, number>,
  );
  const maxTierCount = Math.max(1, ...Object.values(riskTierCounts));

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div>
          <h1 className="text-2xl font-semibold">Reports</h1>
          <p className="text-sm text-gray-600">
            Filter and compare risk tiers across compliance reports.
          </p>
        </div>
        <a href="/dashboard/reports" className="text-sm text-blue-600 underline">
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
            placeholder="Search reports by summary or notes"
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          />
        </div>
        <div>
          <label className="text-xs font-semibold text-gray-500">Risk tier</label>
          <select
            name="risk_tier"
            defaultValue={currentRiskTier}
            className="mt-1 w-full rounded border px-3 py-2 text-sm"
          >
            {RISK_TIER_OPTIONS.map((tier) => (
              <option key={tier} value={tier}>
                {tier === "all" ? "All tiers" : tier}
              </option>
            ))}
          </select>
        </div>
        <div className="md:col-span-3 flex flex-wrap gap-2">
          {RISK_TIER_OPTIONS.filter((tier) => tier !== "all").map((tier) => (
            <span
              key={tier}
              className="rounded-full border border-gray-200 bg-gray-50 px-3 py-1 text-xs font-semibold text-gray-600"
            >
              {tier}
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
          <div className="text-xs font-semibold text-gray-500">Total reports</div>
          <div className="text-2xl font-semibold">{reports.length}</div>
        </div>
        <div className="rounded border bg-white p-4">
          <div className="text-xs font-semibold text-gray-500">
            Average risk score
          </div>
          <div className="text-2xl font-semibold">
            {averageScore.toFixed(1)}
          </div>
        </div>
        <div className="rounded border bg-white p-4">
          <div className="text-xs font-semibold text-gray-500">
            High/Critical
          </div>
          <div className="text-2xl font-semibold">
            {(riskTierCounts.High ?? 0) + (riskTierCounts.Critical ?? 0)}
          </div>
        </div>
      </div>

      <div className="rounded border bg-white p-4 mb-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">
          Risk tier distribution
        </h2>
        <div className="space-y-2">
          {Object.entries(riskTierCounts).map(([tier, count]) => (
            <div key={tier} className="flex items-center gap-3">
              <span className="w-20 text-xs font-medium uppercase text-gray-500">
                {tier}
              </span>
              <div className="h-2 flex-1 rounded-full bg-gray-100">
                <div
                  className="h-2 rounded-full bg-indigo-500"
                  style={{ width: `${(count / maxTierCount) * 100}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-gray-600">
                {count}
              </span>
            </div>
          ))}
        </div>
      </div>

      {reports.length === 0 && (
        <div className="text-gray-500">No reports generated yet.</div>
      )}

      <div className="space-y-4">
        {reports.map((r) => (
          <div key={r.id} className="border rounded p-4">
            <div className="font-medium">
              {r.summary || `Report #${r.id}`}
            </div>
            <div className="text-sm text-gray-500">
              Risk: {r.risk_score} · Tier: {r.risk_tier ?? "Unknown"} ·{" "}
              {formatIsoDate(r.created_at)}
            </div>
            <div className="mt-3 flex flex-wrap gap-3 text-sm">
              <a
                href={`${apiBase}/reports/${r.id}.json`}
                className="text-blue-600 underline"
              >
                Export JSON
              </a>
              <a
                href={`${apiBase}/reports/${r.id}/violations.csv`}
                className="text-blue-600 underline"
              >
                Export CSV
              </a>
              <a
                href={`${apiBase}/reports/${r.id}.pdf`}
                className="text-blue-600 underline"
              >
                Export PDF
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
