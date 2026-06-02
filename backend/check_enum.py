"""Check what values the PostgreSQL scanstatus enum actually has"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    result = db.execute(text("SELECT unnest(enum_range(NULL::scanstatus))::text AS val"))
    values = [row[0] for row in result]
    print(f"PostgreSQL scanstatus enum has {len(values)} values:")
    for v in values:
        print(f"  • {v}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()
