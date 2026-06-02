from app.core.database import SessionLocal
from app.api.v1.endpoints.dashboard import get_dashboard_stats
from app.models.schemas import DashboardStats
import asyncio

async def main():
    db = SessionLocal()
    try:
        stats = await get_dashboard_stats(db)
        print(stats)
        
        # Test validation
        validated = DashboardStats(**stats)
        print("Validation successful!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
