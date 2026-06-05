import asyncio
import traceback
from app.core.database import AsyncSessionLocal
from app.api.v1.dashboard_routes import _generate_sales_report

async def main():
    try:
        await _generate_sales_report(None, None, 1, 'pdf')
    except Exception as e:
        traceback.print_exc()

asyncio.run(main())
