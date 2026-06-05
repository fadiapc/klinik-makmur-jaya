import asyncio
import traceback
from app.core.database import AsyncSessionLocal
from app.services.order_service import OrderService
from app.schemas.order import CheckoutRequest, CheckoutItemRequest
from app.models.models import User, Role, OrderType, PaymentMethod
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        try:
            # get any patient user
            user = (await db.execute(select(User).where(User.email == 'andi@example.com'))).scalar_one()
            # get products for testing
            from app.models.models import Product
            products = (await db.execute(select(Product).limit(2))).scalars().all()
            
            service = OrderService(db)
            req = CheckoutRequest(
                items=[
                    CheckoutItemRequest(product_id=products[0].id, quantity=1),
                    CheckoutItemRequest(product_id=products[1].id, quantity=1)
                ],
                payment_method=PaymentMethod.TRANSFER,
                notes="test"
            )
            
            res = await service.checkout(req, user, None)
            print("Success:", res)
        except Exception as e:
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
