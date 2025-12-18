import { apiFetch } from "@/lib/api";

type Report = {
    id: number;
    summary: string;
    risk_score: number;
    created_at: string;
}

export default async function ReportsPage() {
    const reports = await apiFetch<Report[]>("/dashboard/reports");

    return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Reports</h1>

            <div className="space-y-4">
                {reports.map((r) => (
                    <div key={r.id} className="border rounded p-4">
                        <div className="font-medium">{r.summary}</div>
                        <div className="text-sm text-gray-500">
                            Risk: {r.risk_score} ᐧ {r.created_at ? new Date(r.created_at).toLocaleString() : 'N/A'}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}