import asyncio
import logging
logging.basicConfig(level=logging.ERROR)
from app.core.database import AsyncSessionLocal
from app.api.v1.dashboard_routes import _generate_sales_report

async def main():
    await _generate_sales_report(None, None, 1, 'pdf')

asyncio.run(main())
