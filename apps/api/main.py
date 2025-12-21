from dotenv import load_dotenv
from fastapi import FastAPI
from routers import (
    adk_tools_test,
    compliance,
    dashboard_agents,
    dashboard_reports,
    dashboard_violations,
    ingest,
    report,
    risk,
    upload,
)

load_dotenv()

app = FastAPI(title="AI Compliance Platform")

app.include_router(upload.router)
app.include_router(ingest.router)
app.include_router(compliance.router)
app.include_router(risk.router)
app.include_router(report.router)

app.include_router(dashboard_reports.router)
app.include_router(dashboard_violations.router)
app.include_router(dashboard_agents.router)

app.include_router(adk_tools_test.router)


@app.get("/health")
def health():
    return {"status": "ok"}
