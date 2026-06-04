import asyncio
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/klinik_makmur_jaya')
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT word_similarity('amoxilin', 'Amoxicillin Trihydrate 500mg') > 0.4"))
        print('Is > 0.4 =', res.scalar())

asyncio.run(main())
