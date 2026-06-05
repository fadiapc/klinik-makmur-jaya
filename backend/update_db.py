import asyncio
from sqlalchemy import select, update
from app.core.database import AsyncSessionLocal
from app.models.models import Product, Category

async def main():
    async with AsyncSessionLocal() as db:
        # Get category ID for 'Obat Resep'
        result = await db.execute(select(Category).where(Category.name == 'Obat Resep'))
        category = result.scalars().first()
        
        if category:
            # Update all products in this category to require prescription
            await db.execute(
                update(Product)
                .where(Product.category_id == category.id)
                .values(requires_prescription=True)
            )
            await db.commit()
            print("Successfully updated all 'Obat Resep' products to require prescription.")
        else:
            print("Category 'Obat Resep' not found.")

if __name__ == "__main__":
    asyncio.run(main())
