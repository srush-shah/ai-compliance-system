from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Org(Base):
    __tablename__ = "orgs"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)
    org_id = Column(
        Integer, ForeignKey("orgs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True)
    org_id = Column(
        Integer, ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    content = Column(JSON, nullable=False)
    file_name = Column(String, nullable=True)
    file_type = Column(String, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ProcessedData(Base):
    __tablename__ = "processed_data"

    id = Column(Integer, primary_key=True)
    org_id = Column(
        Integer, ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    structured = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(Integer, primary_key=True)
    org_id = Column(
        Integer, ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name = Column(String, nullable=False)
    description = Column(String)
    severity = Column(String)
    category = Column(String, nullable=False, default="general")
    pattern_type = Column(String, nullable=False, default="keyword")
    pattern = Column(String, nullable=True)
    scope = Column(JSON, nullable=True)
    remediation = Column(String, nullable=True)
    version = Column(String, nullable=False, default="v1")
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)


class PolicyRuleVersion(Base):
    __tablename__ = "policy_rule_versions"

    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("policy_rules.id", ondelete="CASCADE"))
    version = Column(String, nullable=False)
    content_snapshot = Column(JSON, nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class PolicyRuleAudit(Base):
    __tablename__ = "policy_rule_audit"

    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("policy_rules.id", ondelete="CASCADE"))
    action = Column(String, nullable=False)
    actor = Column(String, nullable=True)
    changes = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True)
    org_id = Column(
        Integer, ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    rule = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    details = Column(JSON)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True)
    org_id = Column(
        Integer, ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    summary = Column(String)
    score = Column(Float)
    content = Column(JSON)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    # Optional timestamp for later updates via `update_report`
    updated_at = Column(DateTime(timezone=True), nullable=True)


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True)
    agent_name = Column(String, nullable=False)
    action = Column(String)
    details = Column(JSON)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class ADKRun(Base):
    __tablename__ = "adk_runs"

    id = Column(Integer, primary_key=True, index=True)

    raw_id = Column(Integer, nullable=False)
    processed_id = Column(Integer, nullable=True)
    report_id = Column(Integer, nullable=True)
    org_id = Column(
        Integer, ForeignKey("orgs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    workspace_id = Column(
        Integer,
        ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status = Column(String, nullable=False)  # started | completed | failed
    error = Column(String, nullable=True)
    error_code = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class ADKRunStep(Base):
    __tablename__ = "adk_run_steps"

    id = Column(Integer, primary_key=True, index=True)

    adk_run_id = Column(
        Integer, ForeignKey("adk_runs.id", ondelete="CASCADE"), nullable=False
    )

    step = Column(String, nullable=False)  # data_engineering, compliance_checking, etc
    status = Column(String, nullable=False)  # started | success | failed | skipped

    data = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    error_code = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    finished_at = Column(DateTime(timezone=True), nullable=True)
