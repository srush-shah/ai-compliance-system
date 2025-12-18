import { apiFetch } from "@/lib/api";

type Violation = {
    id: number;
    rule: string;
    severity: string;
    details: string | object;
    created_at: string;
}
export default async function ViolationsPage() {
    const violations = await apiFetch<Violation[]>("/dashboard/violations")

    return (
        <div>
            <h1 className="text-2xl font-semibold mb-4">Violations</h1>

            {
                violations.length === 0 && (
                    <div className="text-gray-500">No violations detected.</div>
                )
            }
            
            <div className="space-y-3">
                {violations.map((v) => (
                    <div key={v.id} className="border rounded p-3">
                        <div className="font-medium">{v.rule}</div>
                        <div className="text-sm">
                            Severity: <span className="font-mono">{v.severity}</span>
                        </div>
                        <div className="text-sm text-gray-600">
                            {typeof v.details === 'string' 
                                ? v.details 
                                : JSON.stringify(v.details, null, 2)}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}