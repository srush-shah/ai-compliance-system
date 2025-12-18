from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, Integer, String
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
