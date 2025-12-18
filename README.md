# AI Compliance & Risk Review System

Enterprise-grade multi-agent system for compliance analysis, risk scoring, and automated reporting.

## Overview

The AI Compliance & Risk Review System is a monorepo application that processes uploaded data through a multi-agent pipeline to detect compliance violations, assess risk, and generate comprehensive reports. The system consists of a FastAPI backend with specialized AI agents and a Next.js dashboard for visualization and monitoring.

**Current Status:** Backend APIs and Next.js dashboard implemented. Core workflow functional with basic agent implementations.

## Tech Stack

### Backend
- **Python 3.13** with FastAPI
- **SQLAlchemy 2.0+** for ORM
- **Alembic** for database migrations
- **PostgreSQL 15** (via Docker)
- **psycopg** (v3) for PostgreSQL connectivity
- **ChromaDB** (optional, for vector embeddings)
- **Pydantic v2** for data validation

### Frontend
- **Next.js 16** (App Router)
- **React 19**
- **TypeScript 5**
- **Tailwind CSS 4**
- **Server-side rendering** for dashboard pages

## Monorepo Structure

```
ai-compliance-system/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── agents/             # Multi-agent system
│   │   │   ├── base.py
│   │   │   ├── data_engineer.py
│   │   │   ├── compliance_checker.py
│   │   │   ├── risk_assessor.py
│   │   │   └── report_writer.py
│   │   ├── routers/            # API route handlers
│   │   │   ├── upload.py
│   │   │   ├── ingest.py
│   │   │   ├── compliance.py
│   │   │   ├── risk.py
│   │   │   ├── report.py
│   │   │   ├── dashboard_agents.py
│   │   │   ├── dashboard_reports.py
│   │   │   └── dashboard_violations.py
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── db.py               # Database connection
│   │   ├── main.py             # FastAPI app entry
│   │   ├── create_tables.py    # Table initialization
│   │   └── requirements.txt
│   └── frontend/               # Next.js application
│       ├── src/
│       │   ├── app/
│       │   │   ├── page.tsx              # Upload page
│       │   │   ├── dashboard/
│       │   │   │   ├── page.tsx          # Reports dashboard
│       │   │   │   ├── layout.tsx        # Dashboard layout
│       │   │   │   ├── violations/
│       │   │   │   │   └── page.tsx      # Violations view
│       │   │   │   └── agents/
│       │   │   │       └── page.tsx      # Agent logs view
│       │   │   └── layout.tsx
│       │   └── lib/
│       │       └── api.ts                # API client utilities
│       └── package.json
├── docker-compose.yml          # PostgreSQL service
└── README.md
```

## Architecture

### Multi-Agent System

The backend implements a four-agent pipeline for processing compliance data:

1. **DataEngineer Agent** (`agents/data_engineer.py`)
   - Processes raw uploaded data
   - Structures and cleans input
   - Stores processed data in `processed_data` table
   - Logs processing actions

2. **ComplianceChecker Agent** (`agents/compliance_checker.py`)
   - Evaluates processed data against policy rules
   - Detects compliance violations
   - Creates violation records in `violations` table
   - Returns list of detected violations

3. **RiskAssessor Agent** (`agents/risk_assessor.py`)
   - Calculates risk scores based on violations
   - Creates initial report entries
   - Risk scoring: 10 points per violation (max 100)
   - Returns risk score and report ID

4. **ReportWriter Agent** (`agents/report_writer.py`)
   - Generates comprehensive compliance reports
   - Aggregates violations, risk scores, and data snapshots
   - Updates report content with structured output

All agents extend `BaseAgent` which provides logging functionality to the `agent_logs` table.

## Database Schema

The system uses PostgreSQL with the following tables:

- **`raw_data`**: Stores uploaded files/content (JSON)
- **`processed_data`**: Structured data after processing (JSON)
- **`policy_rules`**: Compliance policy definitions (name, description, severity)
- **`violations`**: Detected compliance violations (rule, severity, details JSON)
- **`reports`**: Generated compliance reports (summary, score, content JSON)
- **`agent_logs`**: Agent activity tracking (agent_name, action, details JSON)

All tables include `created_at` timestamps (UTC).

## API Endpoints

### Core Workflow
- `POST /upload` - Upload a file (JSON or text)
- `POST /ingest` - Process raw data (requires `raw_id`)
- `POST /check_compliance` - Run compliance checks (requires `processed_id`)
- `POST /risk_assessment` - Assess risk (requires `processed_id`)
- `POST /generate-report` - Generate final report (requires `report_id`)

### Dashboard APIs
- `GET /dashboard/reports` - List reports (limit query param, default 20)
- `GET /dashboard/violations` - List violations (limit query param, default 50)
- `GET /dashboard/agents` - List agent logs (limit query param, default 100)

### Health Check
- `GET /health` - Service health status

## Frontend Pages

- **`/`** - File upload interface
- **`/dashboard`** - Reports overview (risk scores, summaries)
- **`/dashboard/violations`** - Compliance violations list
- **`/dashboard/agents`** - Agent activity logs

All dashboard pages use server-side rendering and fetch data from the FastAPI backend.

## Setup Instructions

### Prerequisites
- Python 3.13
- Node.js 18+ and npm
- Docker and Docker Compose

### Backend Setup

1. **Start PostgreSQL:**
   ```bash
   docker-compose up -d
   ```

2. **Create virtual environment:**
   ```bash
   cd apps/api
   python3.13 -m venv ai-compliance
   source ai-compliance/bin/activate  # On Windows: ai-compliance\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database:**
   ```bash
   python create_tables.py
   ```

5. **Set environment variables:**
   Create a `.env` file in `apps/api/`:
   ```env
   DATABASE_URL=postgresql+psycopg://admin:admin@localhost:5432/compliance
   ```

6. **Run the API server:**
   ```bash
   uvicorn main:app --reload
   ```
   API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd apps/frontend
   npm install
   ```

2. **Set environment variables:**
   Create a `.env.local` file in `apps/frontend/`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run the development server:**
   ```bash
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`

## Environment Variables

### Backend (`apps/api/.env`)
- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql+psycopg://admin:admin@localhost:5432/compliance`)

### Frontend (`apps/frontend/.env.local`)
- `NEXT_PUBLIC_API_URL` - Backend API base URL (default: `http://localhost:8000`)

## Current Limitations & Stubbed Features

The following features are implemented with basic functionality and may be enhanced in future phases:

1. **Policy Rules**: The `policy_rules` table exists but may be empty. Compliance checking uses simple text matching against rule names.

2. **Data Processing**: The DataEngineer agent performs basic structuring (text length, raw content preservation). Advanced parsing, extraction, and normalization are not yet implemented.

3. **Compliance Logic**: Violation detection uses simple substring matching. Production-grade rule engines, pattern matching, and ML-based detection are not implemented.

4. **Risk Scoring**: Current algorithm is basic (10 points per violation, capped at 100). Sophisticated risk models are not yet implemented.

5. **Authentication**: No authentication or authorization is implemented. All endpoints are publicly accessible.

6. **Error Handling**: Basic error handling is in place. Comprehensive error responses and validation are not fully implemented.

7. **Vector Search**: ChromaDB is included in dependencies but not actively used in the current workflow.

## Next Steps

- Implement authentication and authorization (JWT, OAuth, or API keys)
- Enhance policy rule engine with advanced matching and validation
- Integrate vector embeddings for semantic compliance checking
- Add comprehensive test coverage (unit, integration, E2E)
- Implement real-time updates via WebSockets
- Add data export capabilities (PDF, CSV)
- Enhance UI with charts, filters, and advanced visualizations
- Implement audit logging and compliance tracking
- Add support for multiple file formats and data sources

