import Link from "next/link";
import RunDetailsClient from "./run-details-client";

export default async function RunDetailsPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = await params;
  const numericRunId = Number(runId);

  if (!runId || Number.isNaN(numericRunId)) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Run details unavailable</h1>
        <p className="text-sm text-gray-600">
          The run ID is missing or invalid. Return to the runs list to select a
          valid run.
        </p>
        <Link
          href="/dashboard/runs"
          className="inline-flex items-center rounded border px-4 py-2 text-sm font-medium text-gray-700"
        >
          Back to Runs
        </Link>
      </div>
    );
  }

  return <RunDetailsClient runId={numericRunId} />;
}
