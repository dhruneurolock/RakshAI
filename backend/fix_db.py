"""
Fix PostgreSQL scanstatus enum — add missing values.
ALTER TYPE requires less privilege than ALTER TABLE.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from sqlalchemy import text

def fix_enum():
    db = SessionLocal()
    
    # These are the values that the Python ScanStatus enum defines
    # but PostgreSQL's scanstatus type is missing
    missing_values = [
        "planning", "discovering", "testing", "validating",
        "poc_generation", "aggregating", "reporting",
        "initializing", "cancelled"
    ]
    
    for val in missing_values:
        try:
            db.execute(text(f"ALTER TYPE scanstatus ADD VALUE IF NOT EXISTS '{val}'"))
            db.commit()
            print(f"  ✅ Added '{val}' to scanstatus enum")
        except Exception as e:
            db.rollback()
            err = str(e)
            if "already exists" in err.lower() or "duplicate" in err.lower():
                print(f"  ⏭️  '{val}' already exists")
            else:
                print(f"  ❌ Failed to add '{val}': {err}")
    
    db.close()
    print("\nDone!")

if __name__ == "__main__":
    fix_enum()
