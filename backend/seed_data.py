import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.models import Category, Supplier

async def main():
    async with AsyncSessionLocal() as db:
        c = (await db.execute(select(Category))).scalars().all()
        s = (await db.execute(select(Supplier))).scalars().all()
        print('Categories:', c)
        print('Suppliers:', s)
        
        # Insert defaults if empty
        if not c:
            db.add(Category(name="Obat Resep", description="Obat keras wajib resep"))
            db.add(Category(name="Obat Bebas", description="Obat yang bisa dibeli bebas"))
            print("Added default categories")
        if not s:
            db.add(Supplier(name="PT Makmur Jaya Abadi", contact_person="Budi", phone="08123456789"))
            db.add(Supplier(name="Kimia Farma Distributor", contact_person="Siti", phone="08987654321"))
            print("Added default suppliers")
            
        if not c or not s:
            await db.commit()

if __name__ == '__main__':
    asyncio.run(main())
