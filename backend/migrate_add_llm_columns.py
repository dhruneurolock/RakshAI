"""Drop and recreate vulnerabilities table with new columns."""
import sys, os
sys.path.insert(0, ".")
os.environ.setdefault("DATABASE_URL", "postgresql://rakshaiuser:root@localhost:5432/rakshaidb")

from app.core.database import engine
from app.models.models import Vulnerability, Base
from sqlalchemy import text

def migrate():
    with engine.begin() as conn:
        # Check who owns the table
        result = conn.execute(text(
            "SELECT tableowner FROM pg_tables WHERE tablename='vulnerabilities'"
        ))
        owner = result.scalar()
        print(f"Table owner: {owner}")

        # Try to just drop and recreate
        print("Dropping vulnerabilities table...")
        conn.execute(text("DROP TABLE IF EXISTS vulnerabilities CASCADE"))
        print("Table dropped.")
    
    # Recreate all tables (including new columns)
    Base.metadata.create_all(engine)
    print("All tables recreated with new columns!")
    
    # Verify
    with engine.begin() as conn:
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='vulnerabilities' ORDER BY ordinal_position"
        ))
        cols = [r[0] for r in result]
        print(f"Columns ({len(cols)}): {cols}")

if __name__ == "__main__":
    migrate()
