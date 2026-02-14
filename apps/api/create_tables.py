"""
Create database tables from SQLAlchemy models.

This script creates all tables defined in models.py. For existing databases,
you may need to run migrations (e.g., migrate_add_reports_updated_at.py)
to add new columns to existing tables.
"""

from db import engine
from models import Base
from sqlalchemy import inspect, text


def table_exists(table_name: str) -> bool:
    """Return True if the table exists in the current database/schema."""
    inspector = inspect(engine)
    try:
        return inspector.has_table(table_name)
    except Exception:
        # Some DB backends can raise on has_table; fall back to trying get_columns
        try:
            inspector.get_columns(table_name)
            return True
        except Exception:
            return False


def ensure_reports_updated_at_column():
    """Ensure the reports table has the updated_at column."""
    if not table_exists("reports"):
        return

    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("reports")]

    if "updated_at" not in columns:
        print("Adding missing 'updated_at' column to 'reports' table...")
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                ALTER TABLE reports 
                ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE NULL
            """
                )
            )
        print("✓ Added 'updated_at' column to 'reports' table.")


def ensure_raw_data_columns():
    """Ensure raw_data table has metadata columns."""
    if not table_exists("raw_data"):
        return

    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("raw_data")]
    alterations = []

    if "file_name" not in columns:
        alterations.append("ADD COLUMN file_name VARCHAR NULL")
    if "file_type" not in columns:
        alterations.append("ADD COLUMN file_type VARCHAR NULL")
    if "source" not in columns:
        alterations.append("ADD COLUMN source VARCHAR NULL")

    if alterations:
        print("Adding missing metadata columns to 'raw_data' table...")
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE raw_data {', '.join(alterations)}"))
        print("✓ Added raw_data metadata columns.")


def ensure_policy_rule_columns():
    """Ensure policy_rules table has pattern column."""
    if not table_exists("policy_rules"):
        return

    inspector = inspect(engine)
    columns = [col["name"] for col in inspector.get_columns("policy_rules")]
    if "pattern" not in columns:
        print("Adding missing 'pattern' column to 'policy_rules' table...")
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                ALTER TABLE policy_rules
                ADD COLUMN pattern VARCHAR NULL
            """
                )
            )
        print("✓ Added 'pattern' column to 'policy_rules' table.")


def ensure_org_workspace_tables():
    """Ensure orgs and workspaces tables exist for multi-tenant data."""
    with engine.begin() as conn:
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS orgs (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """
            )
        )
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS workspaces (
                id SERIAL PRIMARY KEY,
                org_id INTEGER NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_workspaces_org_id ON workspaces (org_id)")
        )


def ensure_dashboard_indexes():
    with engine.begin() as conn:
        if table_exists("violations"):
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_violations_severity ON violations (severity)"
                )
            )
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_violations_created_at ON violations (created_at)"
                )
            )

        if table_exists("reports"):
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_reports_created_at ON reports (created_at)"
                )
            )


def ensure_multi_tenant_columns():
    """Ensure org/workspace columns, indexes, and constraints exist."""
    inspector = inspect(engine)
    tables = [
        "raw_data",
        "processed_data",
        "policy_rules",
        "violations",
        "reports",
        "adk_runs",
    ]

    for table in tables:
        if not table_exists(table):
            continue

        columns = [col["name"] for col in inspector.get_columns(table)]
        alterations = []
        if "org_id" not in columns:
            alterations.append("ADD COLUMN org_id INTEGER NULL")
        if "workspace_id" not in columns:
            alterations.append("ADD COLUMN workspace_id INTEGER NULL")

        if alterations:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} {', '.join(alterations)}"))

        with engine.begin() as conn:
            conn.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_{table}_org_id ON {table} (org_id)"
                )
            )
            conn.execute(
                text(
                    f"CREATE INDEX IF NOT EXISTS ix_{table}_workspace_id ON {table} (workspace_id)"
                )
            )

    foreign_keys = {
        "raw_data": [
            ("fk_raw_data_org_id_orgs", "org_id", "orgs", "id"),
            ("fk_raw_data_workspace_id_workspaces", "workspace_id", "workspaces", "id"),
        ],
        "processed_data": [
            ("fk_processed_data_org_id_orgs", "org_id", "orgs", "id"),
            (
                "fk_processed_data_workspace_id_workspaces",
                "workspace_id",
                "workspaces",
                "id",
            ),
        ],
        "policy_rules": [
            ("fk_policy_rules_org_id_orgs", "org_id", "orgs", "id"),
            (
                "fk_policy_rules_workspace_id_workspaces",
                "workspace_id",
                "workspaces",
                "id",
            ),
        ],
        "violations": [
            ("fk_violations_org_id_orgs", "org_id", "orgs", "id"),
            (
                "fk_violations_workspace_id_workspaces",
                "workspace_id",
                "workspaces",
                "id",
            ),
        ],
        "reports": [
            ("fk_reports_org_id_orgs", "org_id", "orgs", "id"),
            ("fk_reports_workspace_id_workspaces", "workspace_id", "workspaces", "id"),
        ],
        "adk_runs": [
            ("fk_adk_runs_org_id_orgs", "org_id", "orgs", "id"),
            (
                "fk_adk_runs_workspace_id_workspaces",
                "workspace_id",
                "workspaces",
                "id",
            ),
        ],
    }

    for table, constraints in foreign_keys.items():
        if not table_exists(table):
            continue
        existing = {fk["name"] for fk in inspector.get_foreign_keys(table)}
        for name, column, ref_table, ref_col in constraints:
            if name in existing:
                continue
            with engine.begin() as conn:
                conn.execute(
                    text(
                        f"""
                    ALTER TABLE {table}
                    ADD CONSTRAINT {name}
                    FOREIGN KEY ({column})
                    REFERENCES {ref_table}({ref_col})
                """
                    )
                )


if __name__ == "__main__":
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created/verified")

    # Ensure reports table has updated_at column (for existing databases)
    try:
        ensure_reports_updated_at_column()
        ensure_raw_data_columns()
        ensure_policy_rule_columns()
        ensure_org_workspace_tables()
        ensure_dashboard_indexes()
        ensure_multi_tenant_columns()
    except Exception as e:
        # If table doesn't exist yet, that's fine - create_all will create it with the column
        msg = str(e).lower()
        if ("doesn't exist" not in msg) and ("does not exist" not in msg) and ("undefinedtable" not in msg):
            print(f"Note: Could not check/update schema: {e}")

    print("Database setup complete.")
