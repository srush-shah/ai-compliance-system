from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    adk_tools_test,
    compliance,
    dashboard_reports,
    dashboard_runs,
    dashboard_violations,
    policy_rules,
    reports,
    upload,
    ws_runs,
)
from security import router as auth_router

load_dotenv()

app = FastAPI(title="AI Compliance Platform")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(compliance.router)

app.include_router(dashboard_reports.router)
app.include_router(dashboard_violations.router)
app.include_router(dashboard_runs.router)

app.include_router(adk_tools_test.router)
app.include_router(policy_rules.router)
app.include_router(reports.router)
app.include_router(auth_router)
app.include_router(ws_runs.router)


@app.get("/health")
def health():
    return {"status": "ok"}
