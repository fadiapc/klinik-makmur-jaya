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
        existing_categories = {cat.name for cat in c}
        desired_categories = [
            ("Obat Resep", "Obat keras wajib resep"),
            ("Obat Bebas", "Obat yang bisa dibeli bebas"),
            ("Suplemen", "Vitamin dan suplemen kesehatan"),
            ("Alat Kesehatan", "Peralatan medis dan kesehatan")
        ]
        
        for name, desc in desired_categories:
            if name not in existing_categories:
                db.add(Category(name=name, description=desc))
                print(f"Added category: {name}")

        if not s:
            db.add(Supplier(name="PT Makmur Jaya Abadi", contact_person="Budi", phone="08123456789"))
            db.add(Supplier(name="Kimia Farma Distributor", contact_person="Siti", phone="08987654321"))
            print("Added default suppliers")
            
        await db.commit()

if __name__ == '__main__':
    asyncio.run(main())
