"""
Create database tables from SQLAlchemy models.

This script creates all tables defined in models.py. For existing databases,
you may need to run migrations (e.g., migrate_add_reports_updated_at.py)
to add new columns to existing tables.
"""

from db import engine
from models import Base
from sqlalchemy import inspect, text


def ensure_reports_updated_at_column():
    """Ensure the reports table has the updated_at column."""
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


if __name__ == "__main__":
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created/verified")

    # Ensure reports table has updated_at column (for existing databases)
    try:
        ensure_reports_updated_at_column()
    except Exception as e:
        # If table doesn't exist yet, that's fine - create_all will create it with the column
        if "doesn't exist" not in str(e).lower():
            print(f"Note: Could not check/update reports table: {e}")

    print("Database setup complete.")
