export default function DashboardLayout({children}:
    {
        children: React.ReactNode;
    }
) {
    return (
        <div className="min-h-screen flex">
            <aside className="w-64 border-r p-4">
                <nav className="space-y-2">
                    <a href="/dashboard" className="block font-medium">Reports</a>
                    <a href="/dashboard/violations" className="block">Violations</a>
                    <a href="/dashboard/runs" className="block">ADK Runs</a>
                    <a href="/dashboard/run_workflow" className="block">Run Workflow</a>
                </nav>
            </aside>
            <main className="flex-1 p-6">{children}</main>
        </div>
    )
}