import importlib
import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

API_ROOT = Path(__file__).resolve().parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


@pytest.fixture()
def app(monkeypatch: pytest.MonkeyPatch, tmp_path) -> Generator[object, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{db_path}")
    monkeypatch.setenv("API_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("DEFAULT_ORG_ID", "1")
    monkeypatch.setenv("DEFAULT_WORKSPACE_ID", "1")

    if "db" in sys.modules:
        importlib.reload(sys.modules["db"])
    else:
        import db  # noqa: F401

    import db as db_module
    from models import Base, Org, Workspace

    Base.metadata.drop_all(db_module.engine)
    Base.metadata.create_all(db_module.engine)

    session = db_module.SessionLocal()
    session.add(Org(id=1, name="Test Org"))
    session.add(Workspace(id=1, org_id=1, name="Test Workspace"))
    session.commit()
    session.close()

    modules_to_reload = [
        "adk.tools.db_tools",
        "adk.tools.tools_registry",
        "security",
        "routers.upload",
        "routers.compliance",
        "routers.reports",
        "routers.dashboard_reports",
        "routers.dashboard_runs",
        "routers.dashboard_violations",
        "routers.adk_tools_test",
        "routers.policy_rules",
        "routers.ws_runs",
        "main",
    ]

    for module_name in modules_to_reload:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)

    import main as main_module

    yield main_module.app


@pytest.fixture()
def client(app: object) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
