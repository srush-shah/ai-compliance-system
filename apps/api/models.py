from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True)
    content = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ProcessedData(Base):
    __tablename__ = "processed_data"

    id = Column(Integer, primary_key=True)
    structured = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    severity = Column(String)


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True)
    rule = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    summary = Column(String)
    score = Column(Float)
    content = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True)
    agent_name = Column(String, nullable=False)
    action = Column(String)
    details = Column(JSON)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ADKRun(Base):
    __tablename__ = "adk_runs"

    id = Column(Integer, primary_key=True, index=True)

    raw_id = Column(Integer, nullable=False)
    processed_id = Column(Integer, nullable=True)
    report_id = Column(Integer, nullable=True)

    status = Column(String, nullable=False)  # started | completed | failed
    error = Column(String, nullable=True)
    error_code = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=True)


class ADKRunStep(Base):
    __tablename__ = "adk_run_steps"

    id = Column(Integer, primary_key=True, index=True)

    adk_run_id = Column(
        Integer, ForeignKey("adk_runs.id", ondelete="CASCADE"), nullable=False
    )

    step = Column(String, nullable=False)  # data_engineering, compliance_checking, etc
    status = Column(String, nullable=False)  # success | failed | skipped

    data = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    error_code = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
