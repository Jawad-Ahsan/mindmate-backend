# recreate_tables.py
# WARNING: This will delete ALL existing data and migration history!
# Only use in development

from .database import engine
from models import Base
from sqlalchemy import text

with engine.connect() as conn:
    # 1) Drop the entire schema (removes all tables, indexes, constraints, *and* alembic_version)
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.commit()

print("Database schema dropped and recreated successfully!")

# 2) Recreate all tables + indexes defined in ORM models
Base.metadata.create_all(bind=engine)
print("All tables recreated successfully!")

# 3) Ensure Alembic version table is also reset (empty)
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL
        )
    """))
    conn.commit()

print("Alembic version table reset successfully! (Empty, ready for migrations)")
