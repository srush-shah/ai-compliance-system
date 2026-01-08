import type { ReactNode } from "react";
import Link from "next/link";

export default function DashboardLayout({children}:
    {
        children: ReactNode;
    }
) {
    return (
        <div className="min-h-screen flex">
            <aside className="w-64 border-r p-4">
                <nav className="space-y-2">
                    <Link href="/dashboard" className="block font-medium">Dashboard</Link>
                    <Link href="/dashboard/reports" className="block">Reports</Link>
                    <Link href="/dashboard/violations" className="block">Violations</Link>
                    <Link href="/dashboard/runs" className="block">Runs</Link>
                    <Link href="/dashboard/run_workflow" className="block">Run Workflow</Link>
                </nav>
            </aside>
            <main className="flex-1 p-6">{children}</main>
        </div>
    )
}
