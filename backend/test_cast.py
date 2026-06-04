import asyncio
from sqlalchemy import select, func, cast, Integer
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.models import AuditLog

async def main():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    stmt = select(func.sum(cast(AuditLog.action == 'LOGIN', Integer)))
    print(stmt)

asyncio.run(main())
