import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    adk_tools_test,
    compliance,
    dashboard_reports,
    dashboard_runs,
    dashboard_violations,
    demo,
    policy_rules,
    reports,
    upload,
    ws_runs,
)

load_dotenv()

app = FastAPI(title="AI Compliance Platform")

# Configure CORS - support both local and production origins
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

# Add production frontend URL from environment variable if set
if frontend_url := os.getenv("FRONTEND_URL"):
    allowed_origins.append(frontend_url)

# Allow all origins in development (can be restricted in production)
if os.getenv("ALLOW_ALL_ORIGINS", "false").lower() == "true":
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
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
app.include_router(ws_runs.router)
app.include_router(demo.router)


@app.get("/health")
def health():
    return {"status": "ok"}
